"""Lake of Rage: native art assembled under docs/GBA_MAP_RECONSTRUCTION.md, by the process the
owner accepted for Mahogany and Route 43 (tools/gba/maps/route43/assemble.py).

    python3 tools/gba/maps/lake_of_rage/assemble.py PHG_CHECKOUT CATALOG_CHECKOUT ENGINE_CHECKOUT

1. Reference: trace.py registers decoded HGSS land_data chunks 89-94 (3 x 2) to native cells
   1:1; elements.ledger decodes them flat, cell by cell (lake water '~', flooded-tree crown
   cells 'C', the lake's blocked bank ring 'X').
2. Rock, as Blackthorn's, Mahogany's and Route 43's: every HGSS height layer is one terrace
   (the floor and the lake 0, the south-east cliffs 1-2; source/assemble/terrace-grid.txt), FRLG
   General's mountain nine-slice in the Johto rock ramp, one face per metatile.
3. Shared art, copied unchanged with hashes into source/shared-art/:
     ground      the accepted Cherrygrove/Route 36 painter (claude_cherrygrove/ground.py) on an
                 8 px lawn/road grid read from HGSS's flat ground colours
     water       Route 30's installed HGSS freshwater texture (route30-hgss-blocks pond-15)
     ledges      L11/L12/L13
     trees       T01 on non-overlapping 2x2 roots on HGSS's woods cells (elements.tree_footprints)
     signs       P13 grey information plaque (HGSS model 31), as in Mahogany
     houses      Mahogany's owner-accepted house (gba/art/mahogany-town/source/local-art/house.png,
                 HGSS model 134 with its door 135, reduced to 15 tones), on HGSS's two houses
4. Local assets (source/local-art/), only what the catalog lacks:
     lake banks       the natural bank owner-approved on Route 43's ponds (owner review: water
                      meets grass with a rough bank, not a park rim), on the lake's edge
     flooded trees    HGSS's own crowns (tree_water and tree_w textures, lifted from the flat
                      top-down decode) on each flooded tree, and HGSS's own shadow blobs (the
                      tree_kage models, cut from the decoded reference) at HGSS's positions
     driftwood        HGSS's floating sticks and leaves (ki_obj1-3, etc_a), exact pixels, on the
                      top layer

Writes source/assemble/layers.npz, placements.json, terrace-grid.txt, evidence/assemble/*.png.
"""
from __future__ import annotations
import hashlib, json, shutil, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import elements as E                                 # noqa: E402
from claude_cherrygrove import ground as G           # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/lake-of-rage'
SRC, EV = ART / 'source', ART / 'evidence'
TRACE, SHARED, LOCAL = SRC / 'trace', SRC / 'shared-art', SRC / 'local-art'
OUT, OEV = SRC / 'assemble', EV / 'assemble'
MAHOGANY = ROOT / 'gba/art/mahogany-town'
ROUTE43_TREES = lambda: json.loads((ROOT / 'gba/art/route-43/source/trace/trees.json').read_text())['trees']
W, H = 96, 64
PX = 16

CATALOG = {  # local name -> catalog path (branch codex/violet-city)
    'T01.png': 'gba/art/johto-common/trees/source/T01.png',
    'P13.png': 'gba/art/johto-common/scenery/source/P13.png',
    'L11.png': 'gba/art/johto-common/scenery/source/L11.png',
    'L12.png': 'gba/art/johto-common/scenery/source/L12.png',
    'L13.png': 'gba/art/johto-common/scenery/source/L13.png',
    # Route 30's installed HGSS freshwater (tools/gba/maps/route30_hgss_blocks/assets.py): pond-15-<phase>
    # is open water, phase (y % 2) * 2 + x % 2 of its 32 px water texture.
    **{f'pond/pond-15-{f}.png': f'gba/art/route30-hgss-blocks/source/materials/pond-15-{f}.png' for f in range(4)},
}
HOUSE = MAHOGANY / 'source/local-art/house.png'                 # owner-accepted with Mahogany
HOUSE_HGSS = MAHOGANY / 'source/local-art/house-hgss.png'
WAVE = True
PATH_CORE = 32
FLOOR = 4

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p): return np.array(Image.open(p).convert('RGBA'))

def stage_shared(catalog):
    """Copy every master used here, unchanged, with its hash and source."""
    commit = subprocess.run(['git', '-C', str(catalog), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    prov = dict(catalog=dict(branch='codex/violet-city', commit=commit,
                             rule='Masters copied byte for byte; native tile ids and palette slots may differ, visible colours do not.'))
    for name, rel in CATALOG.items():
        dst = SHARED / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(catalog / rel, dst)
        prov[name] = dict(source=rel, sha256=sha(dst))
    shutil.copyfile(HOUSE, SHARED / 'house.png')
    prov['house.png'] = dict(source='gba/art/mahogany-town/source/local-art/house.png (owner-accepted with Mahogany)',
                             sha256=sha(SHARED / 'house.png'))
    (SHARED / 'provenance.json').write_text(json.dumps(prov, indent=2) + '\n')

# --------------------------------------------------------------------------- rock
def terraces(cells):
    """Blackthorn's rock structure: every HGSS height layer is one Gen 3 terrace."""
    lab = np.array([[c['lab'] for c in row] for row in cells])
    rock = np.isin(lab, list(E.ROCK))
    d = np.zeros((H, W), int)
    for y in range(H):
        for x in range(W):
            c = cells[y][x]
            d[y, x] = max(1, round(c['peak']) - FLOOR) if rock[y, x] else max(0, round(c['ground']) - FLOOR)
    pad = np.pad(d, 1, mode='edge')
    lower = np.zeros((H, W), bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                lower |= pad[1 + dy:1 + dy + H, 1 + dx:1 + dx + W] < d
    return d, rock & lower, rock

def frlg_rock(cells, ground):
    """Blackthorn's installed rock (elements.rock_frlg) on the terraces."""
    d, face, isrock = terraces(cells)
    E.layers = lambda _cells: (d, face, isrock)
    plain_cells = [[dict(c, lab='.' if c['lab'] in E.LEDGES else c['lab']) for c in row] for row in cells]
    out, over, _, piece = E.rock_frlg(plain_cells, ground, E.frlg_pieces(ENGINE), E.cherry_textures())
    return out, over, d, isrock, piece

# --------------------------------------------------------------------------- ground
def paint_ground(q):
    """The accepted Cherrygrove/Route 36 painter on an 8 px material grid (as Route 43)."""
    U = 8
    hq, wq = q.shape
    h, w = hq * U, wq * U
    tex = G.textures()
    tex[G.PATH] = np.tile(tex[G.PATH][:PATH_CORE, :PATH_CORE], (32 // PATH_CORE, 32 // PATH_CORE, 1))
    ys, xs = np.mgrid[0:h, 0:w]
    wave = np.array(G.WAVE) if WAVE else np.zeros(32, int)
    dx = wave[ys % 32]; dy = wave[(xs + 11) % 32]
    sx = np.clip(xs + dx, 0, w - 1) // U; sy = np.clip(ys + dy, 0, h - 1) // U
    mat = q[sy, sx]
    out = np.zeros((h, w, 4), np.uint8); out[..., 3] = 255
    for m, t in tex.items():
        mm = mat == m
        out[..., :3][mm] = t[ys[mm] % t.shape[0], xs[mm] % t.shape[1]]
    dist = {m: G._chamfer(mat == m) for m in tex}
    for (a, b) in [(G.GRASS, G.PATH), (G.GRASS, G.SAND), (G.PATH, G.SAND), (G.PATH, G.SEA), (G.GRASS, G.SEA), (G.SAND, G.SEA), (G.ROCK, G.SEA)]:
        pa, pb = G.PROFILES[(a, b)]
        if not (mat == a).any() or not (mat == b).any():
            continue
        for k, c in enumerate(pa):
            out[..., :3][(mat == a) & (dist[b] == k + 1)] = c
        for k, c in enumerate(pb):
            out[..., :3][(mat == b) & (dist[a] == k + 1)] = c
    return out, mat

def ground_quadrants(cells, rock):
    """Lawn or road per 8 px quadrant from HGSS's flat ground colours (as Route 43); the lake,
    its flooded trees, its bank ring, woods and ledges stand on lawn."""
    _, _, _, rgb = E.topdown(PHG)
    rgb = rgb.astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    rockpx = np.repeat(np.repeat(rock, PX, 0), PX, 1)
    water = (b > g + 30) & (b > 150)
    lawn = (g > r + 20) & ~rockpx & ~water
    sand = (r >= g) & (r > 180) & (b < 175) & ~rockpx
    q = np.repeat(np.repeat(np.array([[G.PATH if c['floor'] == 'sand' else G.GRASS for c in row] for row in cells]), 2, 0), 2, 1).astype(np.int8)
    for qy in range(H * 2):
        for qx in range(W * 2):
            lab = cells[qy // 2][qx // 2]['lab']
            if lab in 'F~CX' or cells[qy // 2][qx // 2]['material'] == 'slope':
                q[qy, qx] = G.GRASS
                continue
            sl = np.s_[qy * 8:qy * 8 + 8, qx * 8:qx * 8 + 8]
            nl, ns = int(lawn[sl].sum()), int(sand[sl].sum())
            if ns >= 32 and ns > nl:
                q[qy, qx] = G.PATH
            elif nl >= 8:
                q[qy, qx] = G.GRASS
    for y in range(H):
        for x in range(W):
            if cells[y][x]['lab'] in 'LJ':
                q[2 * y + 1, 2 * x:2 * x + 2] = q[2 * y, 2 * x:2 * x + 2]
    return q

# --------------------------------------------------------------------------- water
POND_SEED = 29
GRASS_EDGE, GRASS_DARK = (104, 208, 152), (88, 176, 136)       # Cherrygrove lawn tones
MUD, BANK, SHALLOW = (160, 144, 104), (88, 112, 80), (72, 200, 224)   # Route 30's HGSS pond rim tones

def smooth_noise(h, w, step, rng):
    """Value noise in [-1, 1]: a random grid every `step` px, bilinear between grid points."""
    gh, gw = h // step + 2, w // step + 2
    g = rng.uniform(-1, 1, (gh, gw))
    ys, xs = np.mgrid[0:h, 0:w] / step
    y0, x0 = ys.astype(int), xs.astype(int)
    fy, fx = ys - y0, xs - x0
    top = g[y0, x0] * (1 - fx) + g[y0, x0 + 1] * fx
    bot = g[y0 + 1, x0] * (1 - fx) + g[y0 + 1, x0 + 1] * fx
    return top * (1 - fy) + bot * fy

def periodic_noise1(n, period, step, rng):
    """1D value noise in [-1, 1] that repeats every `period` px (grid every `step` px, wrapped)."""
    g = rng.uniform(-1, 1, period // step)
    t = np.arange(n) / step
    i0 = np.floor(t).astype(int) % len(g)
    f = t - np.floor(t)
    return g[i0] * (1 - f) + g[(i0 + 1) % len(g)] * f

def periodic_noise2(h, w, period, step, rng):
    """2D value noise in [-1, 1] that repeats every `period` px both ways."""
    k = period // step
    g = rng.uniform(-1, 1, (k, k))
    ys, xs = np.mgrid[0:h, 0:w] / step
    y0, x0 = np.floor(ys).astype(int), np.floor(xs).astype(int)
    fy, fx = ys - y0, xs - x0
    a, b = g[y0 % k, x0 % k], g[y0 % k, (x0 + 1) % k]
    c, d = g[(y0 + 1) % k, x0 % k], g[(y0 + 1) % k, (x0 + 1) % k]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy

def water_texture():
    return np.concatenate([np.concatenate([rgba(SHARED / f'pond/pond-15-{r * 2 + c}.png')[..., :3] for c in (0, 1)], 1)
                           for r in (0, 1)], 0)

def lake(cells, ground):
    """The lake as Route 43's owner-approved natural ponds (route43/assemble.pond): Route 30's
    HGSS freshwater texture inside a rough bank in Route 30's rim tones (mud, dark bank line,
    shallow water), rounded corners, three octaves of seeded value noise along each edge
    (repeating every 64 px, for the tile budget), lawn tufts breaking into the mud. The water is HGSS's water cells and its flooded trees' cells; the mean shore
    sits two pixels inside them and open water reaches at least 4 px round every water cell's
    centre, so the Surf boundary is the cell edge."""
    from scipy.ndimage import distance_transform_edt, gaussian_filter
    rng = np.random.default_rng(POND_SEED)
    water = np.repeat(np.repeat(np.array([[c['lab'] in '~C' for c in row] for row in cells]), PX, 0), PX, 1)
    h, w = water.shape
    soft = gaussian_filter(water.astype(float), 5) > 0.5
    d = distance_transform_edt(soft) - distance_transform_edt(~soft)
    # The shore wanders along each edge with noise of the coordinate along that edge, repeating
    # every 64 px, so straight runs of shore reuse their tiles (the lake's shore is long; a
    # noise that never repeats cost 450 tiles). Edge direction comes from the distance field.
    gy, gx = np.gradient(d)
    along_x = gy ** 2 / np.maximum(gx ** 2 + gy ** 2, 1e-9)        # 1 on a horizontal edge
    nx = sum(a * periodic_noise1(w, 64, st, rng) for a, st in ((2.6, 16), (1.2, 8), (0.5, 4)))
    ny = sum(a * periodic_noise1(h, 64, st, rng) for a, st in ((2.6, 16), (1.2, 8), (0.5, 4)))
    shore = d - 2 + along_x * nx[None, :] + (1 - along_x) * ny[:, None]
    # Every water cell keeps open water around its centre (the lake's corners and one-cell
    # channels would otherwise go to bank): within 4 px of a cell centre the shore rises.
    ys, xs = np.mgrid[0:h, 0:w]
    r = np.hypot(ys % PX - (PX - 1) / 2, xs % PX - (PX - 1) / 2)
    shore = np.where(water, np.maximum(shore, 4.5 + (4 - r) * 1.5), shore)
    tuft = periodic_noise2(h, w, 32, 4, rng) + 0.5 * periodic_noise2(h, w, 32, 1, rng)
    broken = periodic_noise2(h, w, 32, 8, rng)
    tex = water_texture()
    art = np.zeros((h, w, 4), np.uint8)
    def put(m, col):
        art[m, :3] = col; art[m, 3] = 255
    near = d > -6
    open_ = near & (shore >= 4.5)
    put(open_, tex[ys % 32, xs % 32][open_])
    band = near & (shore >= 3.2) & (shore < 4.5)
    put(band & (broken > -0.35), SHALLOW)
    put(band & (broken <= -0.35), tex[ys % 32, xs % 32][band & (broken <= -0.35)])
    put(near & (shore >= 2.2) & (shore < 3.2), BANK)
    mud = near & (shore >= 0.3) & (shore < 2.2)
    put(mud, MUD)
    put(mud & (tuft > 0.75), GRASS_EDGE)
    put(mud & (tuft < -0.95), BANK)
    put(near & (shore >= -0.6) & (shore < 0.3), GRASS_DARK)
    art[(art[..., 3] > 0) & (art[..., :3] == ground[..., :3]).all(-1), 3] = 0
    centre = water & (ys % PX == PX // 2) & (xs % PX == PX // 2)
    assert (shore[centre] >= 3.2).all(), 'a water cell centre is not open water'
    Image.fromarray(art).save(LOCAL / 'lake-banks.png')
    return art, open_ | (band & (broken <= -0.35))

SHADOW_CORE = (8, 74, 132)                                  # the darkest HGSS shadow tone, only in shadow centres

def shadows():
    """HGSS's flooded-tree shadows (the tree_kage models): 248 dark blobs in HGSS's own shadow
    tones, two sizes, at their own positions (many are not under a crown). Each blob is found
    by its core, the one tone no other art uses. A size's master is cut from the decoded
    reference: every shadow-tone pixel within 6 px of a core's box that is nearer that core
    than any other (blobs on a 32 px pitch touch), from the instance of that size with the
    most such pixels. Every blob takes its size's master with its top-left on the nearest 8 px
    corner (at most 4 px); compose() keeps shadow pixels to the lake's open water."""
    from scipy import ndimage
    ref = np.array(Image.open(SRC / 'hgss/hgss-reference-true-heights.png').convert('RGBA'))
    r, g, b = (ref[..., i].astype(int) for i in range(3))
    sm = (b > r + 80) & (g < 130) & (b < 240)
    core = (ref[..., :3] == SHADOW_CORE).all(-1)
    lab, n = ndimage.label(core)
    cobj = ndimage.find_objects(lab)
    cent = np.array([((o[1].start + o[1].stop - 1) / 2, (o[0].start + o[0].stop - 1) / 2) for o in cobj])
    size = lambda o: 'large' if o[1].stop - o[1].start > 20 else 'small'
    def cut(i):
        o = cobj[i]
        y0, y1, x0, x1 = max(0, o[0].start - 6), o[0].stop + 6, max(0, o[1].start - 6), o[1].stop + 6
        ys, xs = np.mgrid[y0:y1, x0:x1]
        d = np.hypot(xs[..., None] - cent[:, 0], ys[..., None] - cent[:, 1])
        mine = (d.argmin(-1) == i) & sm[y0:y1, x0:x1]
        art = ref[y0:y1, x0:x1].copy(); art[~mine] = 0
        return art, cent[i][0] - x0, cent[i][1] - y0, int(mine.sum())
    masters = {}
    for kind in ('small', 'large'):
        best = max((cut(i) for i, o in enumerate(cobj) if size(o) == kind), key=lambda t: t[3])
        masters[kind] = best[:3]
        Image.fromarray(best[0]).save(LOCAL / f'flooded-tree-shadow-{kind}.png')
    out = []
    for i, o in enumerate(cobj):
        art, mx, my = masters[size(o)]
        x0, y0 = cent[i][0] - mx, cent[i][1] - my
        out.append(dict(kind=size(o), hgss_xy=[round(float(x0), 1), round(float(y0), 1)],
                        xy=[int(round(x0 / 8.0)) * 8, int(round(y0 / 8.0)) * 8]))
    return masters, out

def flooded_trees(phg):
    """HGSS's flooded-tree crowns (tree_water1/2 and tree_w12/22 textures) lifted exactly from
    the flat top-down decode, one master per crown kind (the first instance; every instance
    of a kind is the same texture), each placed with its centre on the nearest (16n, 16m + 8)
    (at most 2 px from HGSS's)."""
    from scipy import ndimage
    h, mat, names, rgb = E.topdown(phg)
    nm = np.array(names + ['none'])
    m = nm[np.where(mat >= 0, mat, len(names))]
    kinds = {'tree_water': ('tree_water1', 'tree_water2'), 'tree_w': ('tree_w12', 'tree_w22')}
    masters, placed = {}, []
    for kind, mats in kinds.items():
        cm = np.isin(m, mats)
        lab, n = ndimage.label(cm)
        for i, s_ in enumerate(ndimage.find_objects(lab), 1):
            mask = lab[s_] == i
            if mask.sum() < 100:
                continue
            ys, xs = np.nonzero(mask)
            cy, cx = s_[0].start + ys.mean(), s_[1].start + xs.mean()
            if kind not in masters:
                a = np.zeros(mask.shape + (4,), np.uint8)
                a[mask, :3] = rgb[s_][mask]; a[mask, 3] = 255
                masters[kind] = (a, cy - s_[0].start, cx - s_[1].start)
                Image.fromarray(a).save(LOCAL / f'flooded-tree-{kind.replace("_", "-")}.png')
            a, my, mx = masters[kind]
            gx, gy = int(round(cx / PX)) * PX, int(round((cy - 8) / PX)) * PX + 8
            placed.append(dict(kind=kind, centre=[gx, gy], hgss_centre=[round(float(cx), 1), round(float(cy), 1)],
                               xy=[int(round(gx - mx)), int(round(gy - my))], art=a))
    return placed

def driftwood(phg):
    """HGSS's floating sticks and leaves (ki_obj1-3, etc_a), exact pixels."""
    h, mat, names, rgb = E.topdown(phg)
    nm = np.array(names + ['none'])
    m = np.isin(nm[np.where(mat >= 0, mat, len(names))], ('ki_obj1', 'ki_obj2', 'ki_obj3', 'etc_a'))
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    art[m, :3] = rgb[m]; art[m, 3] = 255
    Image.fromarray(art).save(LOCAL / 'driftwood.png')
    return art

def houses(phg):
    """HGSS's two houses (model 134 with door 135), cut from the true-heights render exactly as
    Mahogany's were; each cut must equal Mahogany's house-hgss.png, so Mahogany's accepted
    house.png stands in its place, its top-left on the nearest 8 px corner."""
    import hgss_render as R
    R.SNAP = True
    r = R.render(phg)
    fg, own = np.array(r['fg']), r['fg_owner']
    want = rgba(HOUSE_HGSS)
    out = []
    for i, b in enumerate(r['buildings']):
        if b['model'] != 134:
            continue
        parts = [i] + [j for j, o in enumerate(r['buildings']) if o['model'] == 135
                       and abs(o['pos'][0] - b['pos'][0]) < 2 and abs(o['pos'][2] - b['pos'][2]) < 3]
        mm = np.isin(own, parts) & (fg[..., 3] > 0)
        ys, xs = np.nonzero(mm)
        x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
        a = fg[y0:y1, x0:x1].copy(); a[~mm[y0:y1, x0:x1]] = 0
        same = a.shape == want.shape and (a == want).all()
        assert same, ('Lake of Rage house differs from Mahogany\'s', a.shape, want.shape)
        out.append(dict(pos=[float(v) for v in b['pos']], hgss_xy=[x0, y0], xy=[int(round(x0 / 8.0)) * 8, int(round(y0 / 8.0)) * 8]))
    return out

# --------------------------------------------------------------------------- colour reduction
def tile_sets(arts, offs):
    out = []
    for a, (x, y) in zip(arts, offs):
        ox, oy = x % 8, y % 8
        h, w = a.shape[:2]
        c = np.zeros((oy + h + 8, ox + w + 8, 4), np.uint8); c[oy:oy + h, ox:ox + w] = a
        for ty in range(0, c.shape[0] - 7, 8):
            for tx in range(0, c.shape[1] - 7, 8):
                t = c[ty:ty + 8, tx:tx + 8]
                m = t[..., 3] > 0
                if m.any():
                    out.append(frozenset(map(tuple, (t[m][:, :3] >> 3).tolist())))
    return out

def reduce_colours(arts, n, offs=None, banks=None):
    """Merge the closest pair of RGB555 tones, the rarer into the commoner, until n remain
    across all the given masters together (and, with banks, until the masters' tiles as
    placed fit that many exact 15-colour banks)."""
    from pack_lossless import pack_sets
    flat = np.concatenate([a.reshape(-1, 4) for a in arts])
    m = flat[:, 3] > 0
    c5 = flat[:, :3].astype(int) >> 3
    cols, inv, cnt = np.unique(c5[m], axis=0, return_inverse=True, return_counts=True)
    inv = inv.ravel()
    w = cnt.astype(float)
    alive = list(range(len(cols)))
    target = list(range(len(cols)))
    merged = []
    cw = np.array([3.0, 4.0, 2.0])

    def apply(target):
        first8 = {k: flat[m][inv == k][0, :3] for k in range(len(cols))}      # each tone keeps its HGSS 8-bit value
        out = flat.copy()
        out[m, :3] = np.array([first8[target[k]] for k in inv], np.uint8)
        res, o = [], 0
        for a in arts:
            k = a.shape[0] * a.shape[1]
            res.append(out[o:o + k].reshape(a.shape)); o += k
        return res

    def fits(target):
        return banks is None or pack_sets(tile_sets(apply(target), offs), banks, tries=40) is not None
    while len(alive) > n or not fits(target):
        best = None
        for ii, i in enumerate(alive):
            for j in alive[ii + 1:]:
                d = float((((cols[i] - cols[j]) ** 2) * cw).sum()) * np.sqrt(min(w[i], w[j]))
                if (cols[i][2] > cols[i][0]) != (cols[j][2] > cols[j][0]):
                    d *= 20                                   # keep cool tones (window glass) apart from warm ones
                if best is None or d < best[0]:
                    best = (d, i, j)
        _, i, j = best
        keep, drop = (i, j) if w[i] >= w[j] else (j, i)
        w[keep] += w[drop]
        alive.remove(drop)
        target = [keep if t == drop else t for t in target]
        merged.append([[int(v) << 3 for v in cols[drop]], [int(v) << 3 for v in cols[keep]], int(cnt[drop])])
    return apply(target), merged

# Local art tone limits (closest pairs merge, as Mahogany's buildings did; shapes untouched).
REDUCE = {'shadow': 6, 'crown': 15, 'driftwood': 15}

def reduce_layer(art, n):
    """reduce_colours on one RGBA layer (as a single master)."""
    (out,), merged = reduce_colours([art], n)
    return out, merged

# --------------------------------------------------------------------------- compose
def over(dst, src, x, y, owner=None, name=''):
    h, w = src.shape[:2]
    sy0, sx0 = max(0, -y), max(0, -x)
    sy1, sx1 = min(h, dst.shape[0] - y), min(w, dst.shape[1] - x)
    s = src[sy0:sy1, sx0:sx1]
    a = s[..., 3] > 0
    d = dst[y + sy0:y + sy1, x + sx0:x + sx1]
    d[a] = s[a][:, :dst.shape[-1]]
    if owner is not None:
        owner[y + sy0:y + sy1, x + sx0:x + sx1][a] = name

def read_grid():
    lines = [l for l in (TRACE / 'material-grid.txt').read_text().splitlines() if l[:2].isdigit()]
    return [list(l.split()[1]) for l in lines]

# P13 on HGSS's model 31 signs, as Mahogany placed it: art top-left (x * 16 - 8, (y - 1.5) * 16).
SIGNS = [(48, 50), (54, 57)]

def compose(phg):
    global PHG
    PHG = phg
    cells = E.ledger(phg)
    trees = json.loads((TRACE / 'trees.json').read_text())['trees']
    lab = np.array([[c['lab'] for c in row] for row in cells])
    ground, _ = paint_ground(ground_quadrants(cells, np.isin(lab, list(E.ROCK))))
    bottom, rock, d, isrock, piece = frlg_rock(cells, ground[..., :3].copy())
    owner = np.full((H * PX, W * PX), '', object)
    (OUT / 'terrace-grid.txt').write_text(
        '# Lake of Rage rock terraces (assemble.terraces), one line per cell row: level 0-3, rock cells upper-case A/B/C\n'
        '# (the first, second and third terrace), from HGSS land_data 89-94 decoded flat (elements.ledger).\n' +
        ''.join(f'{y:02d}    ' + ''.join(('ABC'[min(d[y, x], 3) - 1] if isrock[y, x] else str(d[y, x])) for x in range(W)) + '\n'
                for y in range(H)))
    # Lake, flooded-tree shadows and driftwood, then ledges, on the ground layer.
    lk, wet = lake(cells, bottom)
    a = lk[..., 3] > 0
    bottom[a] = lk[a, :3]; owner[a] = 'lake'
    masters, blobs = shadows()
    both, merged_s = reduce_colours([masters['small'][0], masters['large'][0]], REDUCE['shadow'])
    masters = {k: (a,) + masters[k][1:] for k, a in zip(('small', 'large'), both)}
    for k in masters:
        Image.fromarray(masters[k][0]).save(LOCAL / f'flooded-tree-shadow-{k}.png')
    shade = np.zeros((H * PX, W * PX, 4), np.uint8)
    for sh in blobs:
        over(shade, masters[sh['kind']][0], sh['xy'][0], sh['xy'][1])
    a = (shade[..., 3] > 0) & wet
    bottom[a] = shade[a, :3]; owner[a] = 'shadow'
    crowns = flooded_trees(phg)
    kinds = sorted({c['kind'] for c in crowns})
    firsts = [next(c['art'] for c in crowns if c['kind'] == k) for k in kinds]
    reduced, merged_c = reduce_colours(firsts, REDUCE['crown'])
    for k, art in zip(kinds, reduced):
        Image.fromarray(art).save(LOCAL / f'flooded-tree-{k.replace("_", "-")}.png')
        for c in crowns:
            if c['kind'] == k:
                c['art'] = art
    dw, merged_d = reduce_layer(driftwood(phg), REDUCE['driftwood'])
    Image.fromarray(dw).save(LOCAL / 'driftwood.png')
    (LOCAL / 'reductions.json').write_text(json.dumps(dict(
        note='Local lake art: closest RGB555 tones merge (the rarer into the commoner) until the limit; shapes untouched. '
             'Entries: [dropped tone, kept tone, pixels].', limits=REDUCE,
        shadow=merged_s, crown=merged_c, driftwood=merged_d), indent=1) + '\n')
    l11, l12, l13 = (rgba(SHARED / f'{n}.png') for n in ('L11', 'L12', 'L13'))
    single = np.concatenate([l11[:, :8], l13[:, 8:]], axis=1)
    ledges = []
    for y in range(H):
        for x in range(W):
            if lab[y, x] != 'L':
                continue
            left = x > 0 and lab[y, x - 1] == 'L'
            right = x + 1 < W and lab[y, x + 1] == 'L'
            art, kind = (l12, 'L12') if left and right else (l11, 'L11') if right else (l13, 'L13') if left else (single, 'L11+L13')
            sl = np.s_[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX]
            m = art[..., 3] > 0
            bottom[sl][m] = art[m, :3]; owner[sl][m] = 'ledge'
            ledges.append(dict(cell=[x, y], art=kind))
    # Objects, painted north to south by their base row so the nearer one covers.
    top = np.zeros((H * PX, W * PX, 4), np.uint8)
    objs = []
    t01 = rgba(SHARED / 'T01.png')
    for i, (tx, ty) in enumerate(trees):
        objs.append(dict(name=f'tree_{i}', master='shared-art/T01.png', xy=[tx * PX, ty * PX - PX], art=t01, root=[tx, ty]))
    # Route 43's trees rooted on its top row reach across the seam: their crowns stand in the
    # Lake's bottom row (Lake x = Route 43 x + 32), as HGSS draws them.
    for i, (tx, ty) in enumerate(ROUTE43_TREES()):
        if ty == 0:
            objs.append(dict(name=f'tree_r43_{i}', master='shared-art/T01.png', xy=[(tx + 32) * PX, (H + ty) * PX - PX], art=t01,
                             route43_root=[tx, ty]))
    for i, c in enumerate(crowns):
        objs.append(dict(name=f'crown_{i}', master=f"local-art/flooded-tree-{c['kind'].replace('_', '-')}.png", xy=c['xy'],
                         art=c['art'], centre=c['centre'], hgss_centre=c['hgss_centre']))
    house = rgba(SHARED / 'house.png')
    for i, hs in enumerate(houses(phg)):
        objs.append(dict(name=f'house_{i}', master='shared-art/house.png', xy=hs['xy'], art=house, hgss_xy=hs['hgss_xy'], pos=hs['pos']))
    p13 = rgba(SHARED / 'P13.png')
    for sx, sy in SIGNS:
        objs.append(dict(name=f'sign_{sx}_{sy}', master='shared-art/P13.png', xy=[sx * PX - 8, int((sy - 1.5) * PX)], art=p13, cell=[sx, sy]))
    for o in objs:
        a = o['art'][..., 3] > 0
        o['base'] = o['xy'][1] + int(np.nonzero(a.any(1))[0].max())
    objs.sort(key=lambda o: (o['base'], o['xy'][0]))
    # Driftwood floats on the water, on the top layer (its tones with a shadow's and the
    # water's would pass 15 colours in one tile); only water cells hold it, so it stays under
    # a surfing player. Objects nearer the camera cover it.
    a = dw[..., 3] > 0
    top[a] = dw[a]; owner[a] = 'flat_driftwood'
    for o in objs:
        over(top, o['art'], o['xy'][0], o['xy'][1], owner, o['name'])
    return bottom, rock, top, owner, d, objs, ledges, crowns, blobs

ENGINE = None
PHG = None

def main(phg, catalog, engine):
    global ENGINE
    ENGINE = engine
    for d in (OUT, OEV, LOCAL, SHARED):
        d.mkdir(parents=True, exist_ok=True)
    stage_shared(catalog)
    ground, rock, top, owner, levels, objs, ledges, crowns, blobs = compose(phg)
    view = ground.copy()
    for layer in (rock, top):
        a = layer[..., 3] > 0
        view[a] = layer[a, :3]
    Image.fromarray(view).save(OEV / 'composed.png')
    Image.fromarray(ground).save(OEV / 'ground.png')
    Image.fromarray(rock).save(OEV / 'rock.png')
    Image.fromarray(top).save(OEV / 'objects.png')
    np.savez_compressed(OUT / 'layers.npz', ground=ground, rock=rock, objects=top, owner=owner.astype(str), levels=levels)
    (OUT / 'placements.json').write_text(json.dumps(dict(
        note='Every placed object: master file, top-left pixel, base row. Trees sit on non-overlapping 2x2 roots on '
             'HGSS woods cells; flooded-tree crowns on the cell grid nearest HGSS\'s centre, each over a shadow blob; '
             'houses and signs on HGSS\'s own.',
        objects=[{k: v for k, v in o.items() if k != 'art'} for o in objs], ledges=ledges, shadows=blobs), indent=1, default=int) + '\n')
    print('objects', len(objs), 'flooded trees', len(crowns), 'shadows', len(blobs), 'ledges', len(ledges))

if __name__ == '__main__':
    main(*(Path(a).resolve() for a in sys.argv[1:4]))
