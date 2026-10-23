"""Pack Blackthorn's composed elements into one native map on CherrygrovePrimary.

    python3 tools/gba/maps/blackthorn/pack.py ENGINE_CHECKOUT STYLE        # STYLE: A, B or C

Input is elements.py's compose-STYLE.npz (bottom layer, top layer, shared Center and
Mart layer). Every 8x8 tile that equals a CherrygrovePrimary tile under one of its
palettes (banks 0-5, or bank 8, Cherrygrove's Pokemon Center palette, which Blackthorn's
secondary carries unchanged) references that tile, so the accepted Johto ground, water
(with its animation) and the shared Center cost nothing. Everything else goes into a
Blackthorn secondary tileset: 496 tiles (16 door-animation slots reserved), 512
metatiles, the shared Mart's exact palette in bank 9, the tiles where Center and Mart
touch in a junction bank of their exact colours, and learned palettes for the rest.

Traversal is the decoded HGSS permissions; the shared buildings' bodies are solid.
Writes evidence/elements/pack-STYLE.json, native-STYLE.png and source/elements/pack-STYLE.npz.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build as B                                             # palette fitting helpers  # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/blackthorn-city'
SRC, EV = ART / 'source', ART / 'evidence'
W = H = 64
PRIMARY_BANKS = [0, 1, 2, 3, 4, 5]
CENTER_BANK, MART_BANK, JUNCTION_BANK = 8, 9, 10
LEARNED_BANKS = [6, 7, 11, 12]
SECONDARY_TILES = 496
NORMAL, COVERED = 0, 1
CENTER_ORIGIN, CENTER_DOOR = (31, 43), (3, 5)
MART_ORIGIN, MART_DOOR = (25, 43), (2, 5)
CLEAR = -1                                                    # transparent pixel marker in keys

def read_pal(p):
    v = list(map(int, p.read_text().split()[3:51]))
    return [tuple(v[i * 3:i * 3 + 3]) for i in range(16)]

def exact_banks(jobs, nbanks, size=15, tries=400):
    """Give tiles their exact 5-bit colours where the banks allow it. Colour sets go in
    most-used first, each into the bank needing the fewest new colours; sets that found
    no room go first on the next try, and the packing that leaves the fewest tile uses
    unplaced wins. Tiles that fit nowhere (rare mixes) are quantized into the bank that
    suits them, so their loss stays local instead of shifting a shared colour across the
    map. pack.py keeps this fit or the k-means one, whichever loses less visibly."""
    sets = [frozenset(map(tuple, j['px'][j['mask'] > 0].astype(int).tolist())) for j in jobs]
    use = [j['weight'] * len(c) for j, c in zip(jobs, sets)]
    rng = np.random.default_rng(0)
    first = set()                     # sets that failed before go first next time
    best = None
    for t in range(tries):
        jitter = (lambda i: rng.random() * 0.6) if t else (lambda i: 0.0)
        order = sorted(range(len(jobs)), key=lambda i: (i not in first, -use[i] * (1 + jitter(i)), -len(sets[i])))
        banks, assign, left = [set() for _ in range(nbanks)], [0] * len(jobs), []
        for i in order:
            c = sets[i]
            fits = [(len(c - b), -len(c & b), k) for k, b in enumerate(banks) if len(b | c) <= size]
            if not fits:
                left.append(i)
                continue
            k = min(fits)[2]
            banks[k] |= c
            assign[i] = k
        first |= set(left)
        lost = sum(jobs[i]['weight'] for i in left)
        if best is None or lost < best[0]:
            best = (lost, [set(b) for b in banks], assign[:], left[:])
        if not lost:
            break
    _, banks, assign, left = best
    pals = []
    for b in banks:
        cols = sorted(b) or [(0, 0, 0)]
        pals.append(cols + [cols[-1]] * (size - len(cols)))
    px = np.stack([j['px'] for j in jobs]).astype(float)
    mask = np.stack([j['mask'] for j in jobs]).astype(float)
    errs = np.stack([B.tile_error(px, mask, np.array(p, float)) for p in pals], 1)
    for i in left:
        assign[i] = int(errs[i].argmin())
    w = np.array([j['weight'] for j in jobs], float)
    err = errs[np.arange(len(jobs)), assign]
    return pals, np.array(assign), float((err * w).sum() / (mask.sum(1) * w).sum())

def primary(engine):
    d = engine / 'data/tilesets/primary/cherrygrove'
    a = np.array(Image.open(d / 'tiles.png')) & 15
    tiles = [a[y:y + 8, x:x + 8] for y in range(0, a.shape[0], 8) for x in range(0, a.shape[1], 8)][:512]
    pals = {b: read_pal(d / f'palettes/{b:02}.pal') for b in PRIMARY_BANKS}
    pals[CENTER_BANK] = read_pal(engine / 'data/tilesets/secondary/cherrygrove/palettes/08.pal')
    metas = np.frombuffer((d / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
    attrs = np.frombuffer((d / 'metatile_attributes.bin').read_bytes(), '<u2')
    return tiles, pals, metas, attrs

def key5(px, mask=None):
    k = B.rgb5(px).astype(np.int16)
    if mask is not None:
        k[~mask] = CLEAR
    return k.tobytes()

def primary_index(tiles, pals):
    """rgb5 content -> (tile, bank, flip) for every primary tile under every usable bank."""
    opaque, masked = {}, {}
    for t, ix in enumerate(tiles):
        for b, pal in pals.items():
            p = np.array(pal, np.int32)
            for f, v in enumerate(B.flips(ix)):
                rgb = p[v]
                m = v != 0
                masked.setdefault(key5(rgb, m), (t, b, f))
                if m.all():
                    opaque.setdefault(key5(rgb), (t, b, f))
    return opaque, masked

def traversal(engine, cells, shared_src):
    MB = B.behaviors(engine)
    perm = np.load(SRC / 'hgss/hgss-permissions.npz')
    types, coll = perm['types'], perm['collision']
    doors = {(CENTER_ORIGIN[0] + CENTER_DOOR[0], CENTER_ORIGIN[1] + CENTER_DOOR[1]): 'pokemon_center',
             (MART_ORIGIN[0] + MART_DOOR[0], MART_ORIGIN[1] + MART_DOOR[1]): 'poke_mart'}
    # Shared buildings: the Mart's manifest (gba/art/johto-mart) makes its wall rows 1-5
    # solid across the width it covers; the Center is solid where 40%+ covered.
    body = np.zeros((H, W), bool)
    for src, (ox, oy), need in ((1, MART_ORIGIN, 0.0), (2, CENTER_ORIGIN, 0.4)):
        for cy in range(oy + 1, oy + 6):
            for cx in range(ox, ox + 7):
                cover = (shared_src[cy * 16:cy * 16 + 16, cx * 16:cx * 16 + 16] == src).mean()
                if cover > 0 and cover >= need:
                    body[cy, cx] = True
    out = []
    for y in range(H):
        for x in range(W):
            t, k = int(types[y, x]), int(coll[y, x])
            c = dict(x=x, y=y, hgss_type=t, hgss_collision=k, element=cells[y][x]['lab'] + cells[y][x]['floor'][0])
            if (x, y) in doors:
                c.update(foot='door', behavior='MB_ANIMATED_DOOR', collision=0, elevation=3, door=doors[(x, y)])
            elif t == 0x10:
                c.update(foot='water', behavior='MB_POND_WATER', collision=0, elevation=1)
            elif t == 0x15:
                c.update(foot='water', behavior='MB_OCEAN_WATER', collision=0, elevation=1)
            elif t == 0x3B:
                c.update(foot='ledge_south', behavior='MB_JUMP_SOUTH', collision=1, elevation=0)
            elif t == 0x69:
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3, adaptation='HGSS door; interior not built, so solid')
            elif t == 0x6E:
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3, adaptation='HGSS cave mouth; destination not built, so solid')
            elif k & 0x80:
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3)
            else:
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3)
            if body[y, x] and c['foot'] == 'open':
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3, adaptation='open in HGSS; inside the shared building')
            c['behavior_id'] = MB[c['behavior']]
            out.append(c)
    return out

def main(engine, style):
    comp = np.load(SRC / 'elements' / f'compose-{style}.npz', allow_pickle=True)
    bottom, top, shared, shared_src = comp['bottom'], comp['top'], comp['shared'], comp['shared_src']
    cells = json.loads((SRC / 'elements/ledger.json').read_text())['detail']
    tiles, pals, metas, attrs = primary(engine)
    opaque_idx, masked_idx = primary_index(tiles, pals)
    mart_pal = read_pal(SRC / 'shared-art/poke-mart.pal')
    trav = traversal(engine, cells, shared_src)
    walkable = np.array([[trav[y * W + x]['foot'] in ('open', 'door', 'water') for x in range(W)] for y in range(H)])

    # Decide each 8x8 position's bottom and top content.
    lay = {}                                                  # (tx, ty, layer) -> dict(px, mask, fixed)
    for ty in range(H * 2):
        for tx in range(W * 2):
            sl = np.s_[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            sh = shared[sl][..., 3] > 0
            src = set(shared_src[sl][sh].ravel().tolist())
            fixed = {frozenset({1}): MART_BANK, frozenset({2}): CENTER_BANK, frozenset({1, 2}): JUNCTION_BANK}.get(frozenset(src))
            tp = top[sl][..., 3] > 0
            if sh.all():
                lay[(tx, ty, 0)] = dict(px=shared[sl][..., :3], mask=np.ones((8, 8), bool), fixed=fixed)
                if tp.any():
                    lay[(tx, ty, 1)] = dict(px=top[sl][..., :3], mask=tp, fixed=None)
                continue
            lay[(tx, ty, 0)] = dict(px=bottom[sl], mask=np.ones((8, 8), bool), fixed=None)
            if sh.any():
                assert not tp.any(), ('shared building over top-layer art', tx, ty)
                lay[(tx, ty, 1)] = dict(px=shared[sl][..., :3], mask=sh, fixed=fixed)
            elif tp.any():
                lay[(tx, ty, 1)] = dict(px=top[sl][..., :3], mask=tp, fixed=None)

    # Primary matches first; tiles whose colours sit inside a fixed bank keep them exactly.
    fixed_pals = dict(pals); fixed_pals[MART_BANK] = mart_pal
    fixed_sets = {b: {tuple(v >> 3 for v in c) for c in p[1:]} for b, p in fixed_pals.items()}
    jobs = {}
    stats = dict(primary=0, fixed_exact=0, learned=0)
    for pos, L in lay.items():
        layer = pos[2]
        k = key5(L['px'], None if layer == 0 else L['mask'])
        hit = (opaque_idx if layer == 0 else masked_idx).get(k)
        if hit and (L['fixed'] in (None, hit[1])):
            L['entry'] = ('primary',) + hit; stats['primary'] += 1
            continue
        cols = {tuple(int(v) for v in c) for c in B.rgb5(L['px'])[L['mask']]}
        bank = L['fixed']
        if bank is None:
            bank = next((b for b in (MART_BANK, CENTER_BANK) + tuple(PRIMARY_BANKS) if cols <= fixed_sets[b]), None)
        jk = (k, layer, bank)
        j = jobs.setdefault(jk, dict(px=B.rgb5(L['px']).reshape(64, 3), mask=L['mask'].ravel().astype(np.uint8), weight=0,
                                     bank=bank, layer=layer, material=np.zeros(64, int)))
        j['weight'] += 1
        L['entry'] = ('job', jk)
    junction = [j for j in jobs.values() if j['bank'] == JUNCTION_BANK]
    jcols = []
    for j in junction:
        for p in np.nonzero(j['mask'])[0]:
            c = tuple(int(v) for v in j['px'][p])
            if c not in jcols:
                jcols.append(c)
    assert len(jcols) <= 15, len(jcols)
    banks = {b: [tuple(v >> 3 for v in c) for c in p[1:16]] for b, p in fixed_pals.items()}
    banks[JUNCTION_BANK] = jcols + [jcols[-1] if jcols else (0, 0, 0)] * (15 - len(jcols))
    learned = [j for j in jobs.values() if j['bank'] is None]
    stats['fixed_exact'] = sum(1 for j in jobs.values() if j['bank'] is not None)
    stats['learned'] = len(learned)
    fits = [exact_banks(learned, len(LEARNED_BANKS)),
            B.best_banks(learned, len(LEARNED_BANKS), ('flat', 'sqrt', 'log'), seeds=range(6))]
    loss = [B.visible_loss(learned, f[0], f[1]) for f in fits]
    pals_l, assign, err = fits[int(np.argmin(loss))]
    stats['learned_fit'] = ('exact where possible', 'k-means')[int(np.argmin(loss))]
    for j, a in zip(learned, assign):
        j['bank'] = LEARNED_BANKS[a]
    for b, p in zip(LEARNED_BANKS, pals_l):
        banks[b] = [tuple(int(v) for v in c) for c in p]

    # Quantize and share patterns across flips.
    patterns = {np.zeros((8, 8), np.uint8).tobytes(): 0}
    for j in jobs.values():
        pal = np.array(banks[j['bank']], float)
        ix = (((j['px'][:, None, :].astype(float) - pal[None]) ** 2 * B.CH_W).sum(-1).argmin(-1) + 1).astype(np.uint8)
        if j['layer'] == 1:
            ix = np.where(j['mask'] > 0, ix, 0).astype(np.uint8)
        ix = ix.reshape(8, 8)
        vs = B.flips(ix)
        o = min(range(4), key=lambda i: vs[i].tobytes())
        kk = vs[o].tobytes()
        if kk not in patterns:
            patterns[kk] = len(patterns)
        j['pattern'], j['flip'] = patterns[kk], o
    n_sec = len(patterns)
    assert n_sec <= SECONDARY_TILES, ('secondary tiles over budget', n_sec)

    def entry(L):
        if L is None:
            return 0
        e = L['entry']
        if e[0] == 'primary':
            t, b, f = e[1:]
        else:
            j = jobs[e[1]]; t, b, f = 512 + j['pattern'], j['bank'], j['flip']
        return t | ((f & 1) << 10) | ((f >> 1) << 11) | (b << 12)

    # Metatiles: reuse a primary metatile when identical, else a new secondary one.
    prim_meta = {(tuple(int(v) for v in metas[i]), int(attrs[i])): i for i in range(len(metas))}
    sec_meta, grid, layer_of = {}, np.zeros((H, W), np.uint16), {}
    blank_top = [0, 0, 0, 0]
    for y in range(H):
        for x in range(W):
            q = [(2 * x, 2 * y), (2 * x + 1, 2 * y), (2 * x, 2 * y + 1), (2 * x + 1, 2 * y + 1)]
            bot = [entry(lay[(a, b, 0)]) for a, b in q]
            tp = [entry(lay.get((a, b, 1))) for a, b in q]
            has_top = any((a, b, 1) in lay for a, b in q)
            c = trav[y * W + x]
            layer = NORMAL if has_top and walkable[y, x] else COVERED
            c['layer'] = 'normal' if layer == NORMAL else 'covered'
            attr = c['behavior_id'] | (layer << 12)
            k = (tuple(bot + (tp if has_top else blank_top)), attr)
            if k in prim_meta:
                mid = prim_meta[k]
            else:
                mid = sec_meta.setdefault(k, 512 + len(sec_meta))
            grid[y, x] = mid
    assert len(sec_meta) <= 512, ('secondary metatiles over budget', len(sec_meta))

    # Decode the result back to pixels (what the GBA will draw).
    pat = np.zeros((n_sec, 8, 8), np.uint8)
    for kk, i in patterns.items():
        pat[i] = np.frombuffer(kk, np.uint8).reshape(8, 8)
    pal_rgb = np.zeros((16, 16, 3), np.uint8)
    for b in range(16):
        if b in banks:
            for i, c in enumerate(banks[b][:15]):
                pal_rgb[b, i + 1] = [(v << 3) | (v >> 2) for v in c]
    for b in PRIMARY_BANKS + [CENTER_BANK]:
        pal_rgb[b] = np.array(pals[b], np.uint8)
    pal_rgb[MART_BANK] = np.array(mart_pal, np.uint8)
    allmeta = {}
    for i in range(len(metas)):
        allmeta[i] = (tuple(int(v) for v in metas[i]), int(attrs[i]))
    for k, i in sec_meta.items():
        allmeta[i] = k
    native = np.zeros((H * 16, W * 16, 3), np.uint8)
    for y in range(H):
        for x in range(W):
            ents, _ = allmeta[int(grid[y, x])]
            for li, e in enumerate(ents):
                t = e & 1023
                ix = tiles[t] if t < 512 else pat[t - 512]
                if e & 0x400: ix = ix[:, ::-1]
                if e & 0x800: ix = ix[::-1]
                qi = li % 4
                oy, ox = y * 16 + (qi // 2) * 8, x * 16 + (qi % 2) * 8
                m = ix > 0 if li >= 4 else np.ones((8, 8), bool)
                native[oy:oy + 8, ox:ox + 8][m] = pal_rgb[e >> 12][ix[m]]
    want = bottom.copy()
    a = top[..., 3] > 0; want[a] = top[..., :3][a]
    a = shared[..., 3] > 0; want[a] = shared[..., :3][a]
    d5 = np.abs(B.rgb5(native) - B.rgb5(want)).max(-1)
    shared_exact = bool((d5[shared[..., 3] > 0] == 0).all())
    (EV / 'elements').mkdir(parents=True, exist_ok=True)
    Image.fromarray(native).save(EV / 'elements' / f'native-{style}.png')
    np.savez_compressed(SRC / 'elements' / f'pack-{style}.npz', grid=grid, patterns=pat, palettes=pal_rgb,
                        sec_meta=np.array([list(k[0]) + [k[1]] for k, _ in sorted(sec_meta.items(), key=lambda kv: kv[1])], np.uint16).reshape(-1, 9),
                        collision=np.array([[trav[y * W + x]['collision'] for x in range(W)] for y in range(H)], np.uint8),
                        elevation=np.array([[trav[y * W + x]['elevation'] for x in range(W)] for y in range(H)], np.uint8))
    (SRC / 'elements' / f'traversal-{style}.json').write_text(json.dumps(trav) + '\n')
    report = dict(style=style, secondary_tiles=n_sec, secondary_tile_limit=SECONDARY_TILES,
                  secondary_metatiles=len(sec_meta), metatile_limit=512,
                  primary_metatiles_reused=int(sum(1 for v in grid.ravel() if v < 512)),
                  tile_positions=stats, junction_colours=len(jcols), learned_bank_error=err,
                  colour_rgb5=dict(exact=int((d5 == 0).sum()), within_1=int((d5 <= 1).sum()), within_2=int((d5 <= 2).sum()),
                                   total=int(d5.size), worst=int(d5.max())),
                  shared_building_pixels_exact=shared_exact)
    (EV / 'elements' / f'pack-{style}.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), sys.argv[2])
