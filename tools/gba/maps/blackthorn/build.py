"""Prior three-section draft, kept for reference; superseded by the element build (elements.py, pack.py,
install_elements.py). Its evidence lives in evidence/sections-draft/.

Blackthorn City exterior: HGSS land_data render -> native Gen 3 tiles, palettes and cells.

First authoring only. install.py refuses to overwrite an existing Blackthorn map.

Inputs (gba/art/blackthorn-city/source/):
    hgss/          the HGSS render layers from hgss_render.py (terrain, foreground, permissions)
    shared-art/    the approved shared Pokemon Center and Pokemart, copied byte for byte

Method:
    ground   HGSS terrain at 1:1, cliff and ledge fronts stretched to whole 8 px rows
    top      HGSS buildings and props (transparent RGBA), plus the shared Center and Mart
             placed so their doors sit on the HGSS warp cells
    banks    Center keeps Cherrygrove bank 8 exactly, the Mart its own palette, and the five
             tiles where the two buildings touch a junction bank of their exact colours; ten
             banks are fitted to the HGSS art (terrain and buildings separately)
    tiles    exact duplicates (with flips, across banks) are shared; nothing else is merged
    sections the 64x64 city is three native Porymap maps (rows 0-23, 24-43, 44-63), each with
             a private tileset pair inside the 1008-tile / 1024-metatile hardware limits and
             all sharing the same 13 palettes; the city view streams native tiles so the
             camera crosses section lines without seams

    python3 tools/gba/maps/blackthorn/build.py ENGINE_CHECKOUT
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/blackthorn-city'
SRC, EV = ART / 'source', ART / 'evidence/sections-draft'
W = H = 64
PX = 16
TILE_LIMIT = 1008                       # NUM_TILES_TOTAL minus the 16 door-animation slots
SECTIONS = [('BlackthornCity01', 0, 24), ('BlackthornCity02', 24, 44), ('BlackthornCity03', 44, 64)]
CENTER_ORIGIN, CENTER_DOOR = (31, 43), (3, 5)      # door lands on HGSS warp (34, 48)
MART_ORIGIN, MART_DOOR = (25, 43), (2, 5)          # door lands on HGSS warp (27, 48)
CENTER_BANK, MART_BANK, JUNCTION_BANK = 8, 9, 10
GROUND_BANKS = [0, 1, 2, 3, 4]          # HGSS terrain
FG_BANKS = [5, 6, 7, 11, 12]            # HGSS buildings and props (top layer only)
NORMAL, COVERED = 0, 1                  # metatile layer types
GROUND_LAYER = __import__('os').environ.get('BLACKTHORN_GROUND', 'hgss-ground.png')   # terrain with HGSS contact shadows
CH_W = np.array([3.0, 4.0, 2.0])        # channel weights for colour error

# ----------------------------------------------------------------------------- helpers
def rgb5(a):
    return np.asarray(a, np.int32) >> 3

def read_pal(path):
    return [tuple(map(int, l.split())) for l in path.read_text().replace('\r', '').splitlines()[3:19]]

def behaviors(game):
    names = re.findall(r'^\s+(MB_[A-Z0-9_]+),', (game / 'include/constants/metatile_behaviors.h').read_text(), re.M)
    return {n: i for i, n in enumerate(names)}

def flips(t):
    """The four orientations of an 8x8 array, in (hflip, vflip) order 00, 10, 01, 11."""
    return [t, t[:, ::-1], t[::-1], t[::-1, ::-1]]

# ----------------------------------------------------------------------------- composition
def compose():
    hg, sa = SRC / 'hgss', SRC / 'shared-art'
    ground = np.array(Image.open(hg / GROUND_LAYER).convert('RGB'))
    fg = np.array(Image.open(hg / 'hgss-foreground.png').convert('RGBA'))
    # Shared buildings: exact pixels and palette indices. HGSS's own Center and
    # Mart were never rendered into either layer; the ground beneath is terrain.
    top = fg.copy()
    source = np.where(fg[..., 3] > 0, 1, 0).astype(np.uint8)    # 1 HGSS, 2 Mart, 3 Center
    index = np.zeros(fg.shape[:2], np.uint8)
    center = np.array(Image.open(sa / 'pokemon-center.png').convert('RGBA'))
    center_pal = read_pal(sa / 'pokemon-center.pal')
    mart = np.array(Image.open(sa / 'poke-mart.png').convert('RGBA'))
    mart_idx = np.array(Image.open(sa / 'poke-mart.indexed.png'))
    mart_pal = read_pal(sa / 'poke-mart.pal')
    for art, idx, pal, (cx, cy), tag in ((mart, mart_idx, mart_pal, MART_ORIGIN, 2), (center, None, center_pal, CENTER_ORIGIN, 3)):
        ox, oy = cx * PX, cy * PX
        m = art[..., 3] > 0
        reg = np.s_[oy:oy + art.shape[0], ox:ox + art.shape[1]]
        assert not source[reg][m].any(), 'shared building overlaps HGSS art'
        if idx is None:
            lut = {c: i for i, c in enumerate(pal) if i}
            idx = np.zeros(m.shape, np.uint8)
            for y, x in zip(*np.nonzero(m)):
                idx[y, x] = lut[tuple(int(v) for v in art[y, x, :3])]
        for y, x in zip(*np.nonzero(m)):
            assert tuple(pal[idx[y, x]]) == tuple(int(v) for v in art[y, x, :3]), (tag, x, y)
        top[reg][m] = art[m]
        source[reg][m] = tag
        index[reg][m] = idx[m]
    material = np.load(hg / 'hgss-ground-materials.npz')['material'].astype(np.int32)
    owner = np.load(hg / 'hgss-foreground-owner.npz')['owner'].astype(np.int32)
    return dict(ground=ground, top=top, source=source, index=index, center=center, mart=mart,
                center_pal=center_pal, mart_pal=mart_pal, material=material, owner=owner)

# ----------------------------------------------------------------------------- traversal
def traversal(c, MB):
    perm = np.load(SRC / 'hgss/hgss-permissions.npz')
    types, coll = perm['types'], perm['collision']
    doors = {(CENTER_ORIGIN[0] + CENTER_DOOR[0], CENTER_ORIGIN[1] + CENTER_DOOR[1]): 'pokemon_center',
             (MART_ORIGIN[0] + MART_DOOR[0], MART_ORIGIN[1] + MART_DOOR[1]): 'poke_mart'}
    # Shared building bodies are blocked wherever a canvas row 1-5 cell is at least
    # 40% covered; HGSS's narrower Mart left walkable cells the shared Mart now fills,
    # and a part-covered alcove would draw wall fragments over the player.
    body = np.zeros((H, W), bool)
    for art, (ox, oy) in ((c['mart'], MART_ORIGIN), (c['center'], CENTER_ORIGIN)):
        a = art[..., 3] > 0
        for cy in range(1, a.shape[0] // PX):
            for cx in range(a.shape[1] // PX):
                if a[cy * PX:cy * PX + PX, cx * PX:cx * PX + PX].mean() >= 0.4:
                    body[oy + cy, ox + cx] = True
    cells = []
    for y in range(H):
        for x in range(W):
            t, k = int(types[y, x]), int(coll[y, x])
            assert t in (0, 0x10, 0x15, 0x3B, 0x69, 0x6E), (x, y, t)
            cell = dict(x=x, y=y, hgss_type=t, hgss_collision=k)
            if (x, y) in doors:
                cell.update(foot='door', behavior='MB_ANIMATED_DOOR', collision=0, elevation=3, door=doors[(x, y)])
            elif t == 0x10:
                cell.update(foot='water', behavior='MB_POND_WATER', collision=0, elevation=1)
            elif t == 0x15:
                cell.update(foot='water', behavior='MB_OCEAN_WATER', collision=0, elevation=1)
            elif t == 0x3B:
                cell.update(foot='ledge_south', behavior='MB_JUMP_SOUTH', collision=1, elevation=0)
            elif t == 0x69:
                cell.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3,
                            adaptation='HGSS door; interior not built, so solid')
            elif t == 0x6E:
                cell.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3,
                            adaptation='HGSS cave mouth; destination map not built, so solid')
            elif k & 0x80:
                cell.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3)
            else:
                cell.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3)
            if body[y, x] and cell['foot'] == 'open':
                cell.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3,
                            adaptation='open in HGSS; inside the shared building footprint')
            cell['behavior_id'] = MB[cell['behavior']]
            cells.append(cell)
    return cells

# ----------------------------------------------------------------------------- palettes
def kmeans_colors(colors, weights, k, init=None, iters=40):
    """Weighted k-means over unique RGB5 colours."""
    colors = colors.astype(float)
    if len(colors) <= k:
        return np.array(list(colors) + [colors[0]] * (k - len(colors))).astype(int)
    if init is None:
        cent = [colors[int(np.argmax(weights))]]
        for _ in range(k - 1):
            d = np.min([((colors - c) ** 2 * CH_W).sum(1) for c in cent], 0) * weights
            cent.append(colors[int(np.argmax(d))])
        cent = np.array(cent)
    else:
        cent = np.array(init, float)
    for _ in range(iters):
        lab = (((colors[:, None] - cent[None]) ** 2) * CH_W).sum(-1).argmin(1)
        new = cent.copy()
        for j in range(k):
            m = lab == j
            if m.any():
                new[j] = (colors[m] * weights[m, None]).sum(0) / weights[m].sum()
        if np.allclose(new, cent):
            break
        cent = new
    return np.clip(np.rint(cent), 0, 31).astype(int)

def tile_error(px, mask, pal):
    d = ((px[:, :, None, :] - pal[None, None]) ** 2 * CH_W).sum(-1).min(-1)
    return (d * mask).sum(1)

def fit_banks(jobs, nbanks, seed, scheme, rounds=25):
    """Assign tiles to banks and fit 15 colours per bank (alternating, k-means style)."""
    px = np.stack([j['px'] for j in jobs]).astype(float)
    mask = np.stack([j['mask'] for j in jobs]).astype(float)
    # How much a tile's usage counts: 'flat' (every distinct tile once, so a small
    # material is not outvoted by the mountain mass), 'sqrt' or 'log' (damped usage).
    use = np.array([j['weight'] for j in jobs], float)
    w = {'flat': np.ones(len(jobs)), 'sqrt': np.sqrt(use), 'log': 1 + np.log2(use)}[scheme]
    uc, inv = np.unique(px[mask > 0].astype(int), axis=0, return_inverse=True)
    glob = kmeans_colors(uc, np.bincount(inv.ravel()).astype(float), 48)
    lab = ((px[:, :, None, :] - glob[None, None]) ** 2 * CH_W).sum(-1).argmin(-1)
    hist = np.zeros((len(jobs), len(glob)))
    for i in range(len(jobs)):
        np.add.at(hist[i], lab[i], mask[i])
    hist /= np.maximum(hist.sum(1, keepdims=True), 1)
    rng = np.random.default_rng(seed)
    cent = hist[rng.choice(len(jobs), nbanks, replace=False, p=w / w.sum())]
    for _ in range(25):
        assign = ((hist[:, None] - cent[None]) ** 2).sum(-1).argmin(1)
        for k in range(nbanks):
            if (assign == k).any():
                cent[k] = np.average(hist[assign == k], 0, w[assign == k])
    pals = [None] * nbanks
    for _ in range(rounds):
        for k in range(nbanks):
            m = assign == k
            if not m.any():
                continue
            sel = mask[m] > 0
            cols = px[m][sel].astype(int)
            ww = np.repeat(w[m], 64).reshape(-1, 64)[sel]
            uc, inv = np.unique(cols, axis=0, return_inverse=True)
            pals[k] = kmeans_colors(uc, np.bincount(inv.ravel(), ww).astype(float), 15, init=pals[k])
        errs = np.stack([tile_error(px, mask, np.array(p, float)) if p is not None else np.full(len(jobs), np.inf)
                         for p in pals], 1)
        new = errs.argmin(1)
        if (new == assign).all():
            break
        assign = new
    total = float((errs.min(1) * w).sum() / (mask.sum(1) * w).sum())
    return pals, assign, total

def visible_loss(jobs, pals, assign):
    """Share of each material's map area whose colour moves by two or more 5-bit
    levels: the mean over materials plus the worst one, so a fit that keeps the
    mountain exact but flattens the pond glints or the bridge grain loses."""
    px = np.stack([j['px'] for j in jobs]).astype(float)
    mask = np.stack([j['mask'] for j in jobs]) > 0
    use = np.array([j['weight'] for j in jobs], float)
    mat = np.stack([j['material'] for j in jobs])
    pal = np.stack([np.array(p, float) for p in pals])[assign]                  # n,15,3
    q = np.take_along_axis(pal, (((px[:, :, None, :] - pal[:, None]) ** 2 * CH_W).sum(-1).argmin(-1))[..., None], 1)
    bad = (np.abs(q - px).max(-1) >= 2) & mask
    shares = []
    for m in np.unique(mat):
        area = ((mat == m) & mask) * use[:, None]
        if area.sum() >= 500:
            shares.append(float((area * bad).sum() / area.sum()))
    return float(np.mean(shares)) + max(shares)

def best_banks(jobs, nbanks, schemes, seeds=range(8)):
    fits = [fit_banks(jobs, nbanks, s, scheme) for scheme in schemes for s in seeds]
    return min(fits, key=lambda r: visible_loss(jobs, r[0], r[1]))

# ----------------------------------------------------------------------------- build
def main(game):
    MB = behaviors(game)
    c = compose()
    cells = traversal(c, MB)
    ground, top, source, index = c['ground'], c['top'], c['source'], c['index']
    g5, t5 = rgb5(ground), rgb5(top[..., :3])
    opaque = top[..., 3] > 0
    walkable = np.array([[cells[y * W + x]['foot'] in ('open', 'door', 'water') for x in range(W)] for y in range(H)])

    # Tile jobs: one per distinct 8x8 content and layer.
    bottom_jobs, top_jobs, pos_bottom, pos_top = {}, {}, {}, {}
    for ty in range(H * 2):
        for tx in range(W * 2):
            sl = np.s_[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            om = opaque[sl]
            if om.any():
                src = set(source[sl][om].ravel().tolist())
                kind = {frozenset({1}): ('learned', None), frozenset({2}): ('fixed', MART_BANK),
                        frozenset({3}): ('fixed', CENTER_BANK), frozenset({2, 3}): ('fixed', JUNCTION_BANK)}.get(frozenset(src))
                assert kind is not None, (tx, ty, src)
                key = (t5[sl].tobytes(), om.tobytes(), kind, index[sl].tobytes())
                j = top_jobs.setdefault(key, dict(px=t5[sl].reshape(64, 3), mask=om.ravel().astype(np.uint8), weight=0,
                                                   kind=kind, index=index[sl].copy(), layer='top', material=c['owner'][sl].ravel()))
                j['weight'] += 1
                pos_top[(tx, ty)] = key
            if om.all():
                pos_bottom[(tx, ty)] = None             # hidden under an opaque building tile
                continue
            key = (g5[sl].tobytes(),)
            j = bottom_jobs.setdefault(key, dict(px=g5[sl].reshape(64, 3), mask=np.ones(64, np.uint8), weight=0,
                                                  kind=('learned', None), layer='bottom', material=c['material'][sl].ravel()))
            j['weight'] += 1
            pos_bottom[(tx, ty)] = key

    # Fixed banks.
    banks = {CENTER_BANK: [tuple(rgb5(v)) for v in c['center_pal'][1:16]],
             MART_BANK: [tuple(rgb5(v)) for v in c['mart_pal'][1:16]]}
    jcols = []
    for j in top_jobs.values():
        if j['kind'][1] == JUNCTION_BANK:
            for p in np.nonzero(j['mask'])[0]:
                col = tuple(int(v) for v in j['px'][p])
                if col not in jcols:
                    jcols.append(col)
    assert len(jcols) <= 15, len(jcols)
    banks[JUNCTION_BANK] = jcols + [jcols[-1]] * (15 - len(jcols))

    # Learned banks: terrain and buildings never share a tile, so each gets its
    # own bank set and building colours are not crowded out by terrain.
    mean_err = {}
    for name, ids, jobs, schemes in (('ground', GROUND_BANKS, list(bottom_jobs.values()), ('flat', 'sqrt', 'log')),
                                     ('foreground', FG_BANKS, [j for j in top_jobs.values() if j['kind'][0] == 'learned'], ('log',))):
        pals, assign, mean_err[name] = best_banks(jobs, len(ids), schemes)
        for j, a in zip(jobs, assign):
            j['bank'] = ids[a]
        for k, p in zip(ids, pals):
            banks[k] = [tuple(int(v) for v in col) for col in p]
    for j in top_jobs.values():
        if j['kind'][0] == 'fixed':
            j['bank'] = j['kind'][1]
    print('learned banks fitted; mean weighted error per pixel', mean_err, flush=True)

    def quantize(j):
        if j['kind'][0] == 'fixed' and j['bank'] in (CENTER_BANK, MART_BANK):
            ix = j['index'].ravel().astype(np.uint8)
        elif j['kind'][1] == JUNCTION_BANK:
            ix = np.array([banks[JUNCTION_BANK].index(tuple(int(v) for v in j['px'][p])) + 1 if j['mask'][p] else 0
                           for p in range(64)], np.uint8)
        else:
            pal = np.array(banks[j['bank']], float)
            ix = (((j['px'][:, None, :].astype(float) - pal[None]) ** 2 * CH_W).sum(-1).argmin(-1) + 1).astype(np.uint8)
        if j['layer'] == 'top':
            ix = np.where(j['mask'] > 0, ix, 0).astype(np.uint8)
        return ix.reshape(8, 8)

    # Patterns: index arrays shared across banks and flips; pattern 0 is blank.
    patterns = {np.zeros((8, 8), np.uint8).tobytes(): 0}
    def entry(ix, bank):
        vs = flips(ix)
        o = min(range(4), key=lambda i: vs[i].tobytes())
        k = vs[o].tobytes()
        if k not in patterns:
            patterns[k] = len(patterns)
        # City-wide pattern ids exceed 10 bits; install.py assigns real tile ids per section.
        return patterns[k] | (o << 16) | (bank << 20)
    for j in list(bottom_jobs.values()) + list(top_jobs.values()):
        j['entry'] = entry(quantize(j), j['bank'])

    entries = np.zeros((H, W, 8), np.uint32)                   # pattern | flip << 16 | bank << 20
    attr = np.zeros((H, W), np.uint16)
    for y in range(H):
        for x in range(W):
            q = [(2 * x, 2 * y), (2 * x + 1, 2 * y), (2 * x, 2 * y + 1), (2 * x + 1, 2 * y + 1)]
            entries[y, x, :4] = [bottom_jobs[pos_bottom[p]]['entry'] if pos_bottom[p] is not None else 0 for p in q]
            entries[y, x, 4:] = [top_jobs[pos_top[p]]['entry'] if p in pos_top else 0 for p in q]
            cell = cells[y * W + x]
            has_top = any(p in pos_top for p in q)
            # Roofs and props over a cell the player can occupy draw above the
            # player; everything else, including building walls, draws below.
            layer = NORMAL if has_top and walkable[y, x] else COVERED
            cell['layer'] = 'normal' if layer == NORMAL else 'covered'
            attr[y, x] = cell['behavior_id'] | (layer << 12)
    pat = np.zeros((len(patterns), 8, 8), np.uint8)
    for k, i in patterns.items():
        pat[i] = np.frombuffer(k, np.uint8).reshape(8, 8)
    pal_rgb = np.zeros((16, 16, 3), np.uint8)
    for k, cols in banks.items():
        for i, col in enumerate(cols[:15]):
            pal_rgb[k, i + 1] = [(v << 3) | (v >> 2) for v in col]

    # Per-section budgets.
    sections = []
    for name, y0, y1 in SECTIONS:
        sub = entries[y0:y1]
        used = sorted(set((sub & 0xFFFF).ravel().tolist()) | {0})
        combos = {(sub[y, x].tobytes(), int(attr[y0 + y, x])) for y in range(y1 - y0) for x in range(W)}
        assert len(used) <= TILE_LIMIT and len(combos) <= 1024, (name, len(used), len(combos))
        sections.append(dict(name=name, rows=[y0, y1], tiles=len(used), metatiles=len(combos)))

    # Decoded native image, for review against the HGSS render.
    native = np.zeros((H * PX, W * PX, 3), np.uint8)
    for y in range(H):
        for x in range(W):
            for li in range(8):
                e = int(entries[y, x, li]); t = pat[e & 0xFFFF]
                if e & 0x10000: t = t[:, ::-1]
                if e & 0x20000: t = t[::-1]
                qi = li % 4
                oy, ox = y * PX + (qi // 2) * 8, x * PX + (qi % 2) * 8
                m = t > 0
                native[oy:oy + 8, ox:ox + 8][m] = pal_rgb[e >> 20][t[m]]
    EV.mkdir(parents=True, exist_ok=True)
    Image.fromarray(native).save(EV / 'native-decoded.png')
    comp = ground.copy(); comp[opaque] = top[..., :3][opaque]
    # Compare in the GBA's own 5-bit colour space.
    d5 = np.abs(rgb5(native) - rgb5(comp)).max(-1)
    shared = source >= 2
    np.savez_compressed(EV / 'packing-work.npz', entries=entries, attr=attr, patterns=pat, palettes=pal_rgb,
                        collision=np.array([[cells[y * W + x]['collision'] for x in range(W)] for y in range(H)], np.uint8),
                        elevation=np.array([[cells[y * W + x]['elevation'] for x in range(W)] for y in range(H)], np.uint8))
    ledger = dict(registration=dict(source='HGSS land_data chunks 104-107 (map matrix cells x 20-21, z 4-5)', origin=[0, 0],
                                    scale=1, cells=[W, H], px_per_cell=PX,
                                    note='Collision, behaviour and doors are decoded HGSS permissions, not an overview trace.'),
                  sections=sections, cells=cells)
    (EV / 'material-traversal-ledger.json').write_text(json.dumps(ledger, indent=1) + '\n')
    stats = dict(patterns_city=len(patterns), sections=sections, tile_limit=TILE_LIMIT, metatile_limit=1024,
                 palette_banks=dict(center=CENTER_BANK, mart=MART_BANK, junction=JUNCTION_BANK, ground=GROUND_BANKS,
                                    foreground=FG_BANKS),
                 junction_colors=len(jcols), learned_bank_mean_error=mean_err, merged_tiles=0,
                 colour_rgb5=dict(exact_pixels=int((d5 == 0).sum()), within_1=int((d5 <= 1).sum()),
                                  within_2=int((d5 <= 2).sum()), total=int(d5.size), worst=int(d5.max()),
                                  shared_building_pixels_exact=bool((d5[shared] == 0).all())),
                 hidden_bottom_tiles=sum(1 for v in pos_bottom.values() if v is None))
    (EV / 'build-report.json').write_text(json.dumps(stats, indent=2) + '\n')
    Image.fromarray(comp).save(EV / 'composed-source.png')
    print(json.dumps(stats))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
