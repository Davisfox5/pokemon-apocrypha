"""Pack Cianwood's composed elements into one native map on CherrygrovePrimary.

    python3 tools/gba/maps/cianwood_elements/pack.py ENGINE_CHECKOUT [STYLE]   # STYLE C by default

Input is elements.py's compose-STYLE.npz (bottom layer, top layer, shared Center layer).
Every 8x8 tile that equals a CherrygrovePrimary tile under one of its palettes (banks 0-5)
references that tile, so the accepted Johto ground and sea (with its animation) cost
nothing. Everything else goes into a Cianwood secondary tileset: 496 tiles (16
door-animation slots reserved), 512 metatiles and seven learned banks (6-12). The banks are
one exact fit: the owner-locked C06 Center's 21 colours split exactly over banks 8 and 9,
then every other tile fits the seven banks, filling the slots the Center leaves.

Traversal is the decoded HGSS permissions in Gen 3 behaviours: beach sand, the walkable
surf strip, the sea, east and south ledges. The Center's body is solid and its top row a
walkable roof overhang (gba/art/johto-center). A cell HGSS blocks only because its taller
building model stands there, with nothing of the Gen 3 sprite in it, is open ground.
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
ART = ROOT / 'gba/art/cianwood-elements'
SRC, EV = ART / 'source', ART / 'evidence'
W, H = 32, 64
PRIMARY_BANKS = [0, 1, 2, 3, 4, 5]
SECONDARY_BANKS = [6, 7, 8, 9, 10, 11, 12]
CENTER_BANKS = [8, 9]
SECONDARY_TILES = 496
NORMAL, COVERED = 0, 1
CENTER_ORIGIN, CENTER_DOOR = (25, 45), (2, 4)                 # C06 door on the HGSS Center door (27, 49)
CENTER = 2                                                    # shared_src id of the Center
CLEAR = -1                                                    # transparent pixel marker in keys
FLAT = ('stone_', 'tuft_')                                    # ground details: never above the player
EVENTS = json.loads((SRC / 'hgss-events.json').read_text())
SIGNS = {tuple(e['cell']) for e in EVENTS['signs'] if e['bg_type'] == 1}

def read_pal(p):
    v = list(map(int, p.read_text().split()[3:51]))
    return [tuple(v[i * 3:i * 3 + 3]) for i in range(16)]

def exact_banks(jobs, nbanks, size=15, tries=9000, init=None):
    """Give tiles their exact 5-bit colours where the banks allow it. Only the maximal
    colour sets are packed (every other tile's set lies inside one of them and rides
    along), largest first. Tries take turns between three choices of bank (fewest new
    colours, most colours already shared, fewest colours held), later tries jitter the
    order, and the packing that leaves the fewest tile uses unplaced wins.
    Tiles that fit nowhere are quantized into the bank that suits them, so their loss
    stays local. init gives colours the banks already hold (the Center's)."""
    sets = [frozenset(map(tuple, j['px'][j['mask'] > 0].astype(int).tolist())) for j in jobs]
    distinct = sorted(set(sets), key=lambda c: sorted(c))
    maximal = [c for c in distinct if not any(c < d for d in distinct)]
    rng = np.random.default_rng(0)
    best = None
    for t in range(tries):
        order = sorted(maximal, key=lambda c: -len(c) * (1 + (rng.random() * 0.8 if t else 0)))
        banks = [set(init[k]) if init else set() for k in range(nbanks)]
        rule = t % 3
        for c in order:
            fits = [((len(c - b), -len(c & b)) if rule == 0 else (-len(c & b), len(c - b)) if rule == 1 else (len(c - b), len(b)))
                    + (k,) for k, b in enumerate(banks) if len(b | c) <= size]
            if fits:
                banks[min(fits)[-1]] |= c
        lost = sum(j['weight'] for j, c in zip(jobs, sets) if not any(c <= b for b in banks))
        if best is None or lost < best[0]:
            best = (lost, [set(b) for b in banks])
        if not lost:
            break
    banks = best[1]
    pals = []
    for b in banks:
        cols = sorted(b) or [(0, 0, 0)]
        pals.append(cols + [cols[-1]] * (size - len(cols)))
    px = np.stack([j['px'] for j in jobs]).astype(float)
    mask = np.stack([j['mask'] for j in jobs]).astype(float)
    errs = np.stack([B.tile_error(px, mask, np.array(p, float)) for p in pals], 1)
    assign = np.array([next((k for k, b in enumerate(banks) if c <= b), int(errs[i].argmin())) for i, c in enumerate(sets)])
    w = np.array([j['weight'] for j in jobs], float)
    err = errs[np.arange(len(jobs)), assign]
    return pals, assign, float((err * w).sum() / (mask.sum(1) * w).sum())

def primary(engine):
    d = engine / 'data/tilesets/primary/cherrygrove'
    a = np.array(Image.open(d / 'tiles.png')) & 15
    tiles = [a[y:y + 8, x:x + 8] for y in range(0, a.shape[0], 8) for x in range(0, a.shape[1], 8)][:512]
    pals = {b: read_pal(d / f'palettes/{b:02}.pal') for b in PRIMARY_BANKS}
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

def traversal(engine, cells, art):
    """Gen 3 behaviour, collision and elevation per cell from the HGSS permissions. art is
    the per-cell 'has object art' grid (top and shared layers, plus the sign cells)."""
    MB = B.behaviors(engine)
    perm = np.load(SRC / 'hgss/hgss-permissions.npz')
    types, coll = perm['types'], perm['collision']
    door = (CENTER_ORIGIN[0] + CENTER_DOOR[0], CENTER_ORIGIN[1] + CENTER_DOOR[1])
    ox, oy = CENTER_ORIGIN
    body = {(x, y) for y in range(oy + 1, oy + 5) for x in range(ox, ox + 5)}      # C06 rows 1-4
    overhang = {(x, oy) for x in range(ox, ox + 5)}                                # C06 row 0
    out = []
    for y in range(H):
        for x in range(W):
            t, k = int(types[y, x]), int(coll[y, x])
            lab = cells[y][x]['lab']
            c = dict(x=x, y=y, hgss_type=t, hgss_collision=k, element=lab + cells[y][x]['floor'][0])
            if (x, y) == door:
                c.update(foot='door', behavior='MB_ANIMATED_DOOR', collision=0, elevation=3, door='pokemon_center')
            elif (x, y) in body:
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3)
            elif (x, y) in overhang:
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3,
                         adaptation="C06's top row: a walkable roof overhang (HGSS's taller Center blocks it)")
            elif t == 0x15:
                c.update(foot='water', behavior='MB_OCEAN_WATER', collision=0, elevation=1)
            elif t == 0x17:
                c.update(foot='open', behavior='MB_SHALLOW_WATER', collision=0, elevation=3)
            elif t == 0x38:
                c.update(foot='ledge_east', behavior='MB_JUMP_EAST', collision=1, elevation=0)
            elif t == 0x3B:
                c.update(foot='ledge_south', behavior='MB_JUMP_SOUTH', collision=1, elevation=0)
            elif t == 0x3E:
                c.update(foot='ledge_south', behavior='MB_JUMP_SOUTH', collision=1, elevation=0,
                         adaptation="HGSS's south-east jump where both ledges meet; Gen 3 jumps only straight, so the south ledge's end")
            elif t == 0x63:
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3, adaptation='HGSS cave mouth (Cliff Edge Gate); destination not built, so solid')
            elif t == 0x6D:
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3, adaptation="HGSS warp step into Cliff Edge Gate; destination not built, so plain ground")
            elif t == 0x69:
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3, adaptation='HGSS door; interior not built, so solid')
            elif k & 0x80 and lab == 'X' and not art[y, x]:
                c.update(foot='open', behavior='MB_SAND' if t == 0x21 else 'MB_NORMAL', collision=0, elevation=3,
                         adaptation="HGSS's taller building model blocks it; the Gen 3 sprite does not reach this cell")
            elif k & 0x80:
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3)
            elif t == 0x21:
                c.update(foot='open', behavior='MB_SAND', collision=0, elevation=3)
            else:
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3)
            c['behavior_id'] = MB[c['behavior']]
            out.append(c)
    return out

def above_player(walkable, top, shared, owner):
    """Cells whose art draws above the player (layer type normal). A Gen 3 player is two
    cells tall: feet in its own cell, head in the cell north of it. Object art in a walkable
    cell draws above the player only when the object's base (the lowest row holding its
    pixels) lies further south, so the object stands in front: a roof or crown the player
    walks behind. A door, or any cell on an object's base row, is behind a player standing
    on it or south of it and stays below the player (covered), like every blocked cell.
    Top-layer art that belongs to no object keeps the plain rule (walkable means above).
    Flat ground details (HGSS draws its stones and sand tufts into the terrain mesh) lie
    under the player wherever they are."""
    art = (top[..., 3] > 0) | (shared[..., 3] > 0)
    base = {}
    for name in set(owner[art].ravel().tolist()) - {''}:
        base[name] = int(np.nonzero((owner == name).any(1))[0].max()) // 16
    out = np.zeros((H, W), bool)
    for y in range(H):
        for x in range(W):
            sl = np.s_[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
            a = art[sl]
            if not (walkable[y, x] and a.any()):
                continue
            names = set(owner[sl][a].ravel().tolist())
            out[y, x] = ('' in names and (top[sl][..., 3] > 0).any()) or \
                any(base[n] > y for n in names - {''} if not n.startswith(FLAT))
    return out

def object_art(top, shared):
    art = ((top[..., 3] > 0) | (shared[..., 3] > 0)).reshape(H, 16, W, 16).any(axis=(1, 3))
    for x, y in SIGNS:
        art[y, x] = True
    return art

def main(engine, style):
    comp = np.load(SRC / 'elements' / f'compose-{style}.npz', allow_pickle=True)
    bottom, top, shared, shared_src = comp['bottom'], comp['top'], comp['shared'], comp['shared_src']
    cells = json.loads((SRC / 'elements/ledger.json').read_text())['detail']
    tiles, pals, metas, attrs = primary(engine)
    opaque_idx, masked_idx = primary_index(tiles, pals)
    trav = traversal(engine, cells, object_art(top, shared))
    walkable = np.array([[trav[y * W + x]['foot'] in ('open', 'door', 'water') for x in range(W)] for y in range(H)])
    above = above_player(walkable, top, shared, comp['owner'])

    # Decide each 8x8 position's bottom and top content.
    lay = {}                                                  # (tx, ty, layer) -> dict(px, mask, fixed)
    for ty in range(H * 2):
        for tx in range(W * 2):
            sl = np.s_[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            sh = shared[sl][..., 3] > 0
            fixed = CENTER if sh.any() else None
            tp = top[sl][..., 3] > 0
            if sh.all() and not above[ty // 2, tx // 2]:
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

    # Primary matches first. C06's tiles split exactly over banks 8 and 9; every other
    # tile then goes into one exact fit over the seven secondary banks, starting from the
    # Center's colours, so the town's tiles use the slots the Center leaves.
    banks = {b: [tuple(v >> 3 for v in c) for c in p[1:16]] for b, p in pals.items()}
    fixed_sets = {b: set(p) for b, p in banks.items()}
    jobs = {}
    stats = dict(primary=0, primary_bank=0, center=0, secondary=0)
    for pos, L in lay.items():
        layer = pos[2]
        k = key5(L['px'], None if layer == 0 else L['mask'])
        hit = (opaque_idx if layer == 0 else masked_idx).get(k)
        if hit and L['fixed'] is None:
            L['entry'] = ('primary',) + hit; stats['primary'] += 1
            continue
        cols = {tuple(int(v) for v in c) for c in B.rgb5(L['px'])[L['mask']]}
        bank = None if L['fixed'] == CENTER else next((b for b in PRIMARY_BANKS if cols <= fixed_sets[b]), None)
        jk = (k, layer, bank, L['fixed'])
        j = jobs.setdefault(jk, dict(px=B.rgb5(L['px']).reshape(64, 3), mask=L['mask'].ravel().astype(np.uint8), weight=0,
                                     bank=bank, layer=layer, center=L['fixed'] == CENTER, material=np.zeros(64, int)))
        j['weight'] += 1
        L['entry'] = ('job', jk)
    center = [j for j in jobs.values() if j['center']]
    town = [j for j in jobs.values() if j['bank'] is None and not j['center']]
    stats.update(primary_bank=len(jobs) - len(center) - len(town), center=len(center), secondary=len(town))
    cpals, cassign, cerr = exact_banks(center, len(CENTER_BANKS))
    assert cerr == 0, ('C06 does not split exactly over two banks', cerr)
    init = {b: set() for b in SECONDARY_BANKS}
    for j, a in zip(center, cassign):
        j['bank'] = CENTER_BANKS[a]
        init[j['bank']] |= {tuple(int(v) for v in c) for c in j['px'][j['mask'] > 0]}
    pals_l, assign, err = exact_banks(town, len(SECONDARY_BANKS), init=[init[b] for b in SECONDARY_BANKS])
    for j, a in zip(town, assign):
        j['bank'] = SECONDARY_BANKS[a]
    for b, p in zip(SECONDARY_BANKS, pals_l):
        banks[b] = [tuple(int(v) for v in c) for c in p]
    for j in center:
        assert {tuple(int(v) for v in c) for c in j['px'][j['mask'] > 0]} <= set(banks[j['bank']]), 'C06 colour lost'

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
    sec_meta, grid = {}, np.zeros((H, W), np.uint16)
    blank_top = [0, 0, 0, 0]
    for y in range(H):
        for x in range(W):
            q = [(2 * x, 2 * y), (2 * x + 1, 2 * y), (2 * x, 2 * y + 1), (2 * x + 1, 2 * y + 1)]
            bot = [entry(lay[(a, b, 0)]) for a, b in q]
            tp = [entry(lay.get((a, b, 1))) for a, b in q]
            has_top = any((a, b, 1) in lay for a, b in q)
            c = trav[y * W + x]
            layer = NORMAL if above[y, x] else COVERED                 # walk-behind art: see above_player()
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
    for b in PRIMARY_BANKS:
        pal_rgb[b] = np.array(pals[b], np.uint8)
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
    assert shared_exact, 'C06 pixels changed'
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
                  tile_positions=stats, secondary_bank_error=err,
                  colour_rgb5=dict(exact=int((d5 == 0).sum()), within_1=int((d5 <= 1).sum()), within_2=int((d5 <= 2).sum()),
                                   total=int(d5.size), worst=int(d5.max())),
                  shared_building_pixels_exact=shared_exact,
                  adaptations={f"{c['x']},{c['y']}": c['adaptation'] for c in trav if 'adaptation' in c})
    (EV / 'elements' / f'pack-{style}.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'adaptations'}), len(report['adaptations']), 'adapted cells')

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), sys.argv[2] if len(sys.argv) > 2 else 'C')
