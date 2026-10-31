"""Dark Cave: pack both maps (assemble.py) onto one tileset pair of their own.

    python3 tools/gba/maps/dark_cave/pack.py ENGINE_CHECKOUT

The native art is assemble.py's: HGSS's floor, water, stairs and exits as rendered, its rock
redrawn on the Gen 3 grid in its own cave textures, 1:1 at 16 px per cell. A Gen 3 tileset pair
holds 1,008 tiles in 13 banks of 15; when the two maps hold more distinct 8x8 tiles (flip-deduped)
or colours, two lossy steps fit them, both recorded in evidence/pack.json:

1. Palette banks. Every distinct tile is assigned one of 13 banks; each bank's 15 colours are
   fitted to its tiles (weighted k-means over the tiles' own colours, alternating with the
   assignment), and each tile takes its bank's nearest colours.
2. Tile reuse. Representatives are always real HGSS tiles. Starting from every distinct tile,
   the representative whose removal costs least (its users' extra error, weighted by how often
   each is drawn) is dropped and its users take their nearest remaining representative under
   any flip, until the patterns fit. Distance is the RGB555 error plus a penalty for every pixel
   whose HGSS material class (floor, wall, cliff top, water, stairs, rock, exit, void) differs,
   so a wall edge is only ever drawn by a tile with the same wall edge. Pixel figures in
pack.json compare the native maps with assemble.py's art.

Every cell is a single bottom layer under the player (Gen 3 caves draw nothing above the
player). Traversal comes from the HGSS permission grid (traversal()).
"""
from __future__ import annotations
import json, re, sys
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/dark-cave'
SRC, EV = ART / 'source', ART / 'evidence'
SIDES = ('route45-side', 'route31-side')
W = H = 64
BANKS, PRIMARY_TILES, SECONDARY_TILES = 13, 512, 496
TILE_TARGET = PRIMARY_TILES + SECONDARY_TILES - 1          # tile 0 stays the transparent tile
LAMBDA = 300.0                                             # per pixel whose material class differs
CH_W = np.array([3.0, 4.0, 2.0])                           # channel weights for colour error

# HGSS material (hgss-ground-materials.npz names) -> class: 0 void, 1 floor, 2 wall face, 3 cliff
# top, 4 rock rim, 5 boulder, 6 stairs, 7 water, 8 exit light/hole
CLASS = {'droad01': 1, 'droad01_r': 1, 'droad01_r2': 1, 'droad01_sub': 1, 'droad01_sub2': 1,
         'dwall_s': 2, 'dwall_n': 2, 'dwall_e': 2, 'dwall_w': 2, 'dwall_es': 2, 'dwall_ne': 2, 'dwall_sw': 2, 'dwall_wn': 2,
         'dcliff01': 3, 'dcliff01_r': 3, 'dallpeak': 3, 'dallpeak_p': 3, 'd_ro': 4, 'd_rock01': 5, 'd_rock01s': 5,
         'dslope': 6, 'driver': 7, 'driver_r': 7, 'dpond_line': 7, 'chole_in': 8, 'chole_out': 8, 'chole_light': 8, 'light': 8}
NCLASS = 9
FL = (lambda t: t, lambda t: t[:, ::-1], lambda t: t[::-1], lambda t: t[::-1, ::-1])   # flip codes: bit0 h, bit1 v

# Exits. HGSS marks each walk-off exit with an exit cell (0x6F) and an arrow cell south of it
# (0x65); Gen 3 puts MB_SOUTH_ARROW_WARP on the exit cell itself. The hole into the Route 45
# side (0x6E, walked into northward) is a Gen 3 MB_NON_ANIMATED_DOOR: arriving, the player
# steps out south onto the floor. Route 31's exit stays solid: Route 31 and Dark Cave's
# entrance there are another agent's maps.
UNWIRED = {('route31-side', (5, 26)): "HGSS's exit to Route 31: Route 31 and the Dark Cave entrance beside it are "
                                      "another agent's maps, so this exit stays solid until they are joined"}

def rgb5(a):
    return (np.asarray(a, np.int32) >> 3).astype(np.int16)

def behaviors(engine):
    names = re.findall(r'^\s+(MB_[A-Z0-9_]+),', (engine / 'include/constants/metatile_behaviors.h').read_text(), re.M)
    return {n: i for i, n in enumerate(names)}

def traversal(engine, side):
    """Gen 3 behaviour, collision and elevation per cell from the HGSS permission grid."""
    MB = behaviors(engine)
    perm = np.load(SRC / f'hgss/{side}/hgss-permissions.npz')
    types, coll = perm['types'], perm['collision']
    out = []
    for y in range(H):
        for x in range(W):
            t, k = int(types[y, x]), int(coll[y, x])
            c = dict(x=x, y=y, hgss_type=t, hgss_collision=k)
            if (side, (x, y)) in UNWIRED:
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3, adaptation=UNWIRED[(side, (x, y))])
            elif t == 0x6F:
                c.update(foot='exit', behavior='MB_SOUTH_ARROW_WARP', collision=0, elevation=3,
                         adaptation='HGSS exit cell (0x6F, arrow 0x65 south of it): a Gen 3 south arrow warp on the exit cell')
            elif t == 0x6E:
                c.update(foot='door', behavior='MB_NON_ANIMATED_DOOR', collision=0, elevation=3,
                         adaptation='HGSS hole (0x6E) into the Route 45 side: walked into northward; arriving, the player steps out south')
            elif t == 0x3B:
                c.update(foot='ledge_south', behavior='MB_JUMP_SOUTH', collision=1, elevation=0)
            elif t == 0x39:
                c.update(foot='ledge_west', behavior='MB_JUMP_WEST', collision=1, elevation=0)
            elif t == 0x15:
                c.update(foot='surf', behavior='MB_POND_WATER', collision=0, elevation=1)
            elif k & 0x80 or (t == 0 and k == 0):
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3, void=not k & 0x80)
            elif t == 0x08:
                c.update(foot='open', behavior='MB_CAVE', collision=0, elevation=3)
            else:
                raise SystemExit(f'unhandled HGSS permission {side} {(x, y)} type {t:#x} collision {k:#x}')
            c['behavior_id'] = MB[c['behavior']]
            out.append(c)
    return out

# ----------------------------------------------------------------------------- palettes
def kmeans_colors(colors, weights, k, init=None, iters=40):
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

def fit_banks(px, w, nbanks, seed, rounds=30):
    """px: (n, 64, 3) distinct tiles; w: draw counts. Banks are seeded by clustering the
    tiles' colour histograms, then palettes and assignment alternate."""
    n = len(px)
    uc, inv = np.unique(px.reshape(-1, 3), axis=0, return_inverse=True)
    inv = inv.reshape(n, 64)
    hist = np.zeros((n, len(uc)))
    for i in range(n):
        np.add.at(hist[i], inv[i], 1)
    hist /= 64
    ws = np.sqrt(w)
    rng = np.random.default_rng(seed)
    cent = hist[rng.choice(n, nbanks, replace=False, p=ws / ws.sum())]
    for _ in range(25):
        assign = ((hist[:, None] - cent[None]) ** 2).sum(-1).argmin(1)
        for k in range(nbanks):
            if (assign == k).any():
                cent[k] = np.average(hist[assign == k], 0, ws[assign == k])
    pals = [None] * nbanks
    pxf = px.astype(float)
    for _ in range(rounds):
        for k in range(nbanks):
            m = assign == k
            if not m.any():
                continue
            cols = px[m].reshape(-1, 3)
            cw = np.repeat(ws[m], 64)
            u, iv = np.unique(cols, axis=0, return_inverse=True)
            pals[k] = kmeans_colors(u, np.bincount(iv.ravel(), cw).astype(float), 15, init=pals[k])
        errs = np.stack([(((pxf[:, :, None] - np.array(p, float)[None, None]) ** 2 * CH_W).sum(-1).min(-1)).sum(1)
                         if p is not None else np.full(n, np.inf) for p in pals], 1)
        new = errs.argmin(1)
        if (new == assign).all():
            break
        assign = new
    return [np.array(p if p is not None else [[0, 0, 0]] * 15) for p in pals], assign, float((errs.min(1) * w).sum())

def quantize(px, pal):
    d = (((px[:, None, :].astype(float) - pal[None].astype(float)) ** 2) * CH_W).sum(-1)
    ix = d.argmin(1)
    return ix + 1, pal[ix]

# ----------------------------------------------------------------------------- tiles
def distinct_tiles(images, classes):
    """Flip-canonical distinct tiles over every map: rgb (n,8,8,3), class (n,8,8), draw counts,
    and per map the (tile, flip) at every 8x8 position."""
    keys, rgb, cls, w, pos = {}, [], [], [], []
    for im, cl in zip(images, classes):
        p = np.zeros((H * 2, W * 2, 2), np.int32)
        for ty in range(H * 2):
            for tx in range(W * 2):
                t = im[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
                f = min(range(4), key=lambda i: FL[i](t).tobytes())
                k = FL[f](t).tobytes()
                if k not in keys:
                    keys[k] = len(rgb)
                    rgb.append(FL[f](t)); cls.append(FL[f](cl[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8])); w.append(0)
                w[keys[k]] += 1
                p[ty, tx] = keys[k], f
        pos.append(p)
    return np.array(rgb), np.array(cls), np.array(w, float), pos

def reduce_tiles(q, cls, w, pattern_of, target):
    """Medoid removal (see the module docstring). q: (n,8,8,3) quantized RGB of the distinct
    tiles; pattern_of: (n,) canonical pattern key per tile. Returns each tile's representative
    and the flip that maps the representative onto it."""
    n = len(q)
    R = q.reshape(n, -1).astype(np.float32)
    C = np.zeros((n, 64 * NCLASS), np.float32)
    C[np.arange(n)[:, None], np.arange(64)[None] * NCLASS + cls.reshape(n, 64)] = 1
    D = np.full((n, n), np.inf, np.float32)
    Fb = np.zeros((n, n), np.int8)
    for f in range(4):
        Rf = np.stack([FL[f](t) for t in q]).reshape(n, -1).astype(np.float32)
        Cf = np.stack([FL[f](c.reshape(8, 8, NCLASS)) for c in C.reshape(n, 8, 8, NCLASS)]).reshape(n, -1)
        d = (R ** 2).sum(1)[:, None] + (Rf ** 2).sum(1)[None] - 2 * R @ Rf.T + LAMBDA * (64 - C @ Cf.T)
        better = d < D
        D[better] = d[better]; Fb[better] = f
    np.fill_diagonal(D, 0); np.fill_diagonal(Fb, 0)
    D = np.maximum(D, 0)
    rep = np.ones(n, bool)
    a1, d1 = np.arange(n), np.zeros(n)
    a2, d2 = np.zeros(n, int), np.zeros(n)

    def second(t):
        row = np.where(rep, D[t], np.inf)
        row[a1[t]] = np.inf
        j = int(row.argmin())
        return j, float(row[j])
    for t in range(n):
        a2[t], d2[t] = second(t)
    npat = lambda: len({pattern_of[i] for i in np.nonzero(rep)[0]})
    count = npat()
    while count > target:
        for _ in range(max(1, min(50, (count - target) // 2))):
            cost = np.bincount(a1, weights=w * (d2 - d1), minlength=n)
            cost[~rep] = np.inf
            r = int(cost.argmin())
            rep[r] = False
            for t in np.nonzero(a1 == r)[0]:
                a1[t], d1[t] = a2[t], d2[t]
                a2[t], d2[t] = second(t)
            for t in np.nonzero(a2 == r)[0]:
                a2[t], d2[t] = second(t)
        count = npat()
    return a1, Fb[np.arange(n), a1].astype(int), int(rep.sum())

def main(engine):
    (SRC / 'pack').mkdir(parents=True, exist_ok=True); EV.mkdir(parents=True, exist_ok=True)
    images, classes = [], []
    for side in SIDES:                                     # assemble.py: HGSS's rock on the Gen 3 grid
        images.append(rgb5(np.array(Image.open(SRC / f'assemble/{side}.png').convert('RGB'))))
        classes.append(np.load(SRC / f'assemble/{side}-class.npy').astype(np.int16))
    rgb, cls, w, pos = distinct_tiles(images, classes)
    n = len(rgb)
    # 1. palette banks (best of a few seeds)
    px = rgb.reshape(n, 64, 3)
    fits = [fit_banks(px, w, BANKS, s) for s in range(6)]
    pals, assign, _ = min(fits, key=lambda f: f[2])
    ix = np.zeros((n, 64), np.uint8)
    q = np.zeros_like(px)
    for i in range(n):
        ix[i], q[i] = quantize(px[i], pals[assign[i]])
    ix, q = ix.reshape(n, 8, 8), q.reshape(n, 8, 8, 3)
    canon = []
    for i in range(n):
        canon.append(min(FL[f](ix[i]).tobytes() for f in range(4)))
    # 2. tile reuse
    rep, rflip, nrep = reduce_tiles(q, cls, w, canon, TILE_TARGET)
    # patterns: the representatives' index arrays, flip-deduped; tile 0 transparent
    patterns = {np.zeros((8, 8), np.uint8).tobytes(): 0}
    pat_of, pflip = {}, {}
    use = Counter()
    for r in sorted(set(rep.tolist())):
        vs = [FL[f](ix[r]) for f in range(4)]
        o = min(range(4), key=lambda f: vs[f].tobytes())
        k = vs[o].tobytes()
        patterns.setdefault(k, len(patterns))
        pat_of[r], pflip[r] = patterns[k], o                      # FL[o](ix[r]) is the stored pattern
    assert len(patterns) <= PRIMARY_TILES + SECONDARY_TILES, len(patterns)

    def entry(tile, f):
        """Tile `tile` drawn with flip f at a position (the map shows FL[f](canonical tile))."""
        r = rep[tile]
        # canonical tile ~ FL[rflip](rep); rep = FL[pflip](pattern) (flips are involutions and commute)
        fl = f ^ rflip[tile] ^ pflip[r]
        return pat_of[r] | ((fl & 1) << 10) | ((fl >> 1) << 11) | (int(assign[r]) << 12)

    metas, grids, travs = {}, [], []
    for si, side in enumerate(SIDES):
        trav = traversal(engine, side)
        travs.append(trav)
        g = np.zeros((H, W), np.int32)
        for y in range(H):
            for x in range(W):
                ents = tuple(entry(*pos[si][2 * y + dy, 2 * x + dx]) for dy in (0, 1) for dx in (0, 1)) + (0, 0, 0, 0)
                attr = trav[y * W + x]['behavior_id'] | (1 << 12)          # METATILE_LAYER_TYPE_COVERED
                k = (ents, attr)
                metas.setdefault(k, len(metas))
                g[y, x] = metas[k]
                use[k] += 1
        grids.append(g)
    nm = len(metas)
    assert nm <= 1024, ('metatiles over budget', nm)
    # Most-used metatiles and patterns go to the primary tileset (both maps load both halves).
    order = sorted(metas, key=lambda k: -use[k])
    ids = {k: (i if i < 512 else 512 + (i - 512)) for i, k in enumerate(order)}
    remap = np.zeros(nm, np.int32)
    for k, i in metas.items():
        remap[i] = ids[k]
    grids = [remap[g] for g in grids]
    pat = np.zeros((len(patterns), 8, 8), np.uint8)
    for k, i in patterns.items():
        pat[i] = np.frombuffer(k, np.uint8).reshape(8, 8)
    pal_rgb = np.zeros((16, 16, 3), np.uint8)
    for b in range(BANKS):
        for i, c in enumerate(pals[b][:15]):
            pal_rgb[b, i + 1] = [(int(v) << 3) | (int(v) >> 2) for v in c]
    meta_rows = np.zeros((nm, 9), np.uint16)
    for k, i in ids.items():
        meta_rows[i] = list(k[0]) + [k[1]]
    # Decode the native result and measure it against the HGSS render.
    report = dict(method='assemble.py art (the routes\' FRLG rock in HGSS cave colours), 13 fitted palette banks, medoid tile reuse under a material-class penalty '
                         f'(lambda {LAMBDA}), one bottom layer per cell',
                  distinct_tiles=n, representatives=nrep, patterns=len(patterns),
                  primary_tiles=min(len(patterns), PRIMARY_TILES), secondary_tiles=max(0, len(patterns) - PRIMARY_TILES),
                  metatiles=nm, primary_metatiles=min(nm, 512), secondary_metatiles=max(0, nm - 512),
                  colours_per_bank=[len({tuple(c) for c in p}) for p in pals], sides={})
    for si, side in enumerate(SIDES):
        native = np.zeros((H * 16, W * 16, 3), np.uint8)
        for y in range(H):
            for x in range(W):
                ents = meta_rows[grids[si][y, x]][:4]
                for qi, e in enumerate(ents):
                    t = pat[e & 1023]
                    if e & 0x400: t = t[:, ::-1]
                    if e & 0x800: t = t[::-1]
                    native[y * 16 + (qi // 2) * 8:y * 16 + (qi // 2) * 8 + 8, x * 16 + (qi % 2) * 8:x * 16 + (qi % 2) * 8 + 8] = pal_rgb[e >> 12][t]
        Image.fromarray(native).save(EV / f'{side}-native.png')
        d = np.abs(rgb5(native) - images[si]).max(-1)
        walk = np.kron(np.array([[c['foot'] != 'blocked' or not c.get('void') for c in travs[si][y * W:(y + 1) * W]] for y in range(H)]),
                       np.ones((16, 16), bool))
        report['sides'][side] = dict(pixels=int(walk.sum()), exact=round(float((d[walk] == 0).mean()), 4),
                                     within_1=round(float((d[walk] <= 1).mean()), 4), within_2=round(float((d[walk] <= 2).mean()), 4),
                                     max_level_diff=int(d[walk].max()), metatiles_used=int(len(np.unique(grids[si]))))
    np.savez_compressed(SRC / 'pack/pack.npz', patterns=pat, palettes=pal_rgb, metatiles=meta_rows,
                        **{f'grid_{s.replace("-", "_")}': g.astype(np.uint16) for s, g in zip(SIDES, grids)},
                        **{f'collision_{s.replace("-", "_")}': np.array([[c['collision'] for c in t[y * W:(y + 1) * W]] for y in range(H)], np.uint8)
                           for s, t in zip(SIDES, travs)},
                        **{f'elevation_{s.replace("-", "_")}': np.array([[c['elevation'] for c in t[y * W:(y + 1) * W]] for y in range(H)], np.uint8)
                           for s, t in zip(SIDES, travs)})
    for s, t in zip(SIDES, travs):
        (SRC / f'pack/traversal-{s}.json').write_text(json.dumps(t) + '\n')
    (EV / 'pack.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    return report

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
