"""Route 32: native art assembled by the Route 29/30 catalog process (Mahogany Town / Route 43).

    python3 tools/gba/maps/route32_catalog/assemble.py PHG_CHECKOUT CATALOG_CHECKOUT ENGINE_CHECKOUT

CATALOG_CHECKOUT is a checkout of the Johto catalog commit (pokemon-apocrypha codex/violet-city
de5d8cfb). Shared art is copied byte for byte into source/shared-art/ with its hash:

  ground      the approved Cherrygrove/Route 36 painter (claude_cherrygrove/ground.py) on an 8 px
              lawn/road grid read from HGSS's own flat ground colours; lawn and road are Cherrygrove's
              own textures (its road block at the engine's base revision)
  rock        Blackthorn's FRLG terraces in the Johto rock ramp (rock.py, Route 30's): every HGSS height
              layer one terrace, the soft grass fringe where a rock top meets grass at its height
  trees       the Cherrygrove tree (T01 with the town's contact shadow, Route 30's local cut) on
              non-overlapping 2x2 roots
  tall grass  G15 on every HGSS tall-grass cell
  ledges      L11/L12/L13 on the jump-south runs, turned a quarter for the jump-east run (Route 29's)
  stairs      the Johto stair pieces (Route 30's stair_pieces.py output), in HGSS's own direction (its decoded
              height slope): grey treads on north-south flights, Route 36's plank flight on east-west ones
  gatehouse   G02, the owner-approved HGSS side gate (Route 31's), its stairs on HGSS's gate warps
  Center      C06, the owner-approved Johto Center, its door on HGSS's Center door
  signs       P14 on HGSS's three route signs (model 32)
Local assets from HGSS's own data (source/local-art/):
  sea         HGSS's sea (sea_un, sea_on, and its shore rim pond_line) from the flat decode: every water cell takes the HGSS water cell
              that has the same water/land neighbours (open water: and texture phase), so the shore keeps
              HGSS's foam and the open sea its texture; one exemplar per configuration keeps the tile count small
  pier        HGSS's wooden pier (bridge_b, bridge_c) the same way: one exemplar per pier-neighbour pattern
  boulders    HGSS's sea boulders (sea_rock) and land boulders (rock01) from HGSS's own render, as sprites at
              HGSS's positions (16 px grid), one exemplar each, in the upper tile
  cave        HGSS's Union Cave mouth (cavehole) and its rock surround, from HGSS's own render
  islets      HGSS's three small rock islands in the sea: Johto's FRLG rock at one terrace above the sea
  flowers, light lawn  HGSS's ground textures, every pixel that is not plain lawn (Route 29's), cell by cell
              from one exemplar per 32 px phase
  viaduct     the Magnet Train viaduct deck on HGSS's shadow footprint, drawn above the player in HGSS's
              own Magnet Train textures (a/2/3/3 senro_base, senro_line): land_data has only its shadow
The north padding (reference.py) is Violet City's own lawn and road: rows 0-4 by id (pack.py), row 5 drawn.

Writes source/assemble/layers.npz, placements.json and evidence/assemble/*.png.
"""
from __future__ import annotations
import hashlib, json, shutil, struct, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import reference as Rf                               # noqa: E402
from reference import W, H, PX, COL0, ROW0, HW, HH   # noqa: E402
import rock as Rk                                    # noqa: E402
from claude_cherrygrove import ground as G           # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route32-catalog'
SRC, EV = ART / 'source', ART / 'evidence'
TRACE, SHARED, LOCAL = SRC / 'trace', SRC / 'shared-art', SRC / 'local-art'
OUT, OEV = SRC / 'assemble', EV / 'assemble'

CATALOG = {n + '.png': f'gba/art/johto-common/scenery/source/{n}.png' for n in ('P14', 'L11', 'L12', 'L13', 'G15')}
CATALOG['T01.png'] = 'gba/art/johto-common/trees/source/T01.png'
CATALOG['G02.png'] = 'gba/art/johto-common-review/gates/refinement-4/G02.png'
CATALOG['C06.png'] = 'gba/art/johto-center/source/building.png'
# Already cut on the hub's main branch (Route 30's catalog work).
HUB = {'cherrygrove-tree-with-shadow.png': 'gba/art/route30-catalog/source/local-art/cherrygrove-tree-with-shadow.png',
       **{f'stairs/{k}.png': f'gba/art/route30-catalog/source/shared-art/stairs/{k}.png'
          for k in ('ns-left', 'ns-mid', 'ns-right', 'ew-top', 'ew-mid', 'ew-bottom')}}
BASE_REV = '2722eaf7601ec02dc5a684fa8cdef9206c0dc377'   # the engine's apocrypha base: Cherrygrove before the town rework
FLOOR = 1                           # HGSS height of Route 32's low walkable floor (the coast, the pier, the cave forecourt)
GATE_ORIGIN = (0, 1 + ROW0)         # G02 is 7x7 cells; its stairs (column 6, rows 4-5) stand on HGSS's gate warps (6,5)/(6,6)
CENTER_DOOR = (2, 4)                # C06's door inside its 5x5 cells (Violet's and Cherrygrove's placements)
VIADUCT_PX = (round((Rf.VIADUCT[0] + ROW0) * PX), round((Rf.VIADUCT[1] + ROW0) * PX))

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p): return np.array(Image.open(p).convert('RGBA'))

def stage_shared(catalog):
    commit = subprocess.run(['git', '-C', str(catalog), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    hub = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'origin/main'], capture_output=True, text=True).stdout.strip()
    prov = dict(catalog=dict(repository='pokemon-apocrypha', branch='codex/violet-city', commit=commit,
                             rule='Masters copied byte for byte; native tile ids and palette slots may differ, visible colours do not.'))
    for name, rel in CATALOG.items():
        dst = SHARED / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(catalog / rel, dst)
        prov[name] = dict(source=rel, sha256=sha(dst))
    for name, rel in HUB.items():
        dst = SHARED / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(subprocess.check_output(['git', '-C', str(ROOT), 'show', f'{hub}:{rel}']))
        prov[name] = dict(source=rel, branch='main', commit=hub, sha256=sha(dst))
    (SHARED / 'provenance.json').write_text(json.dumps(prov, indent=2) + '\n')

# --------------------------------------------------------------------------- town art
def base_snapshot(engine):
    """Cherrygrove's tilesets and map at the engine's base revision, in a temporary engine-shaped folder."""
    tmp = Path(tempfile.mkdtemp(prefix='r32-base-'))
    files = subprocess.check_output(['git', '-C', str(engine), 'ls-tree', '-r', '--name-only', BASE_REV,
                                     'data/tilesets/primary/cherrygrove', 'data/tilesets/secondary/cherrygrove',
                                     'data/layouts/CherrygroveCity']).decode().split()
    for f in files:
        (tmp / f).parent.mkdir(parents=True, exist_ok=True)
        (tmp / f).write_bytes(subprocess.check_output(['git', '-C', str(engine), 'show', f'{BASE_REV}:{f}']))
    return tmp

def road_texture(engine):
    """Cherrygrove's own 32 px road block (the commonest pure-road block of the town at the base revision)."""
    from tiles import Tileset
    base = base_snapshot(engine)
    t = Tileset(base, 'cherrygrove', 'cherrygrove')
    b = (base / 'data/layouts/CherrygroveCity/map.bin').read_bytes()
    words = np.array(struct.unpack('<%dH' % (len(b) // 2), b))
    img = np.array(t.map_image(words.tolist(), 80))
    shutil.rmtree(base)
    core = np.array([(216, 184, 128), (224, 200, 128)])
    sand = (img[..., None, :] == core).all(-1).any(-1)
    blocks = Counter()
    for y in range(0, img.shape[0] - 31, 32):
        for x in range(0, img.shape[1] - 31, 32):
            if sand[y:y + 32, x:x + 32].all():
                blocks[img[y:y + 32, x:x + 32].tobytes()] += 1
    return np.frombuffer(blocks.most_common(1)[0][0], np.uint8).reshape(32, 32, 3)

def violet(engine):
    from tiles import Tileset
    t = Tileset(engine, 'violet_city', 'violet_city')
    b = (engine / 'data/layouts/VioletCity/map.bin').read_bytes()
    return t, np.array(struct.unpack('<%dH' % (len(b) // 2), b)).reshape(-1, 80)

# --------------------------------------------------------------------------- ground
def native_cells(cells, grid):
    """The ledger in the native frame. The north padding is Violet's lawn (and road) at HGSS row 0's floor."""
    out = []
    for y in range(H):
        row = []
        for x in range(W):
            hx, hz = Rf.to_hgss(x, y)
            if hz < 0:
                c = dict(cells[0][hx])
                c.update(lab='P', floor='sand' if x in Rf.VIOLET_ROAD else 'grass', ground=c['level'], peak=c['level'], blocked=False)
            else:
                c = dict(cells[hz][hx])
                if grid[y][x] in '~X' and c['type'] in (0x15, 0x10, 0) and c['material'].startswith('sea'):
                    c['floor'] = 'water'
                if grid[y][x] in '~B' or c['material'].startswith('sea'):
                    c['floor'] = 'water'                  # a land boulder (rock01) keeps HGSS's own floor
                if c['floor'] == 'water' and grid[y][x] != 'B':
                    c.update(ground=0.0, peak=0.0)       # the sea is one level, below every rock face beside it
            row.append(c)
        out.append(row)
    for y in range(H):
        for x in range(W):
            c = out[y][x]
            if c['lab'] == 'X' and c['floor'] != 'water':
                nb = [out[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= x + dx < W and 0 <= y + dy < H]
                rk = [n for n in nb if n['lab'] == 'R']
                if rk:
                    c.update(lab='R', peak=max(n['peak'] for n in rk))
    return out

def ground_quadrants(phg, ncells):
    """Lawn or road per 8 px quadrant from HGSS's own flat ground colours (Route 43's rule); woods, tall
    grass, water and rock stand on their cell's floor. Ledge stones are read past."""
    _, _, _, rgb = Rf.topdown(phg)
    rgb = rgb.astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    rock = np.array([[c['lab'] == 'R' for c in row] for row in ncells])
    rockpx = np.repeat(np.repeat(rock[ROW0:ROW0 + HH, COL0:COL0 + HW], PX, 0), PX, 1)
    water = (b > g + 30) & (b > 150)
    lawn = (g > r + 20) & ~rockpx & ~water
    sand = (r >= g) & (r > 180) & (b < 175) & ~rockpx
    q = np.repeat(np.repeat(np.array([[G.PATH if c['floor'] == 'sand' else G.GRASS for c in row] for row in ncells]), 2, 0), 2, 1).astype(np.int8)
    for qy in range(H * 2):
        for qx in range(W * 2):
            x, y = qx // 2, qy // 2
            lab = ncells[y][x]['lab']
            if y < ROW0:
                continue
            if lab in 'FG~B' or ncells[y][x]['floor'] == 'water':
                q[qy, qx] = G.GRASS
                continue
            hqx, hqy = qx - COL0 * 2, qy - ROW0 * 2
            sl = np.s_[hqy * 8:hqy * 8 + 8, hqx * 8:hqx * 8 + 8]
            nl, ns = int(lawn[sl].sum()), int(sand[sl].sum())
            if ns >= 32 and ns > nl:
                q[qy, qx] = G.PATH
            elif nl >= 8:
                q[qy, qx] = G.GRASS
    for y in range(H):
        for x in range(W):
            if ncells[y][x]['lab'] in 'LJ':
                q[2 * y + 1, 2 * x:2 * x + 2] = q[2 * y, 2 * x:2 * x + 2]
    from scipy.ndimage import label
    for val, other, small in ((G.PATH, G.GRASS, 6), (G.GRASS, G.PATH, 3)):
        lab, n = label(q == val)
        sizes = np.bincount(lab.ravel())
        for i in range(1, n + 1):
            if sizes[i] < small:
                q[lab == i] = other
    flats = stair_landings(q, ncells)
    return q, flats

STAIR_LANDING = 2                    # cells above and below a north-south flight whose road takes the flight's columns

def stair_landings(q, ncells):
    """Route 30's: the road meets each north-south flight edge to edge (the flight's own columns)."""
    lab = lambda x, y: ncells[y][x]['lab'] if 0 <= x < W and 0 <= y < H else '#'
    flats, seen = [], set()
    for y in range(H):
        for x in range(W):
            if lab(x, y) != '^' or (x, y) in seen or lab(x - 1, y) == '^' or lab(x, y - 1) == '^':
                continue
            x1 = x
            while lab(x1 + 1, y) == '^':
                x1 += 1
            if x1 == x:
                continue
            y1 = y
            while all(lab(c, y1 + 1) == '^' for c in range(x, x1 + 1)):
                y1 += 1
            seen |= {(c, r) for c in range(x, x1 + 1) for r in range(y, y1 + 1)}
            for r in list(range(y - STAIR_LANDING, y)) + list(range(y1 + 1, y1 + 1 + STAIR_LANDING)):
                if not (0 <= r < H) or not any(q[2 * r + k, c] == G.PATH for k in (0, 1) for c in range(2 * x - 1, 2 * x1 + 3)):
                    continue
                q[2 * r:2 * r + 2, 2 * x:2 * x1 + 2] = G.PATH
                for c in (2 * x - 1, 2 * x1 + 2):
                    if 0 <= c < q.shape[1] and lab(c // 2, r) not in 'R^':
                        q[2 * r:2 * r + 2, c] = G.GRASS
            flats.append((x * PX - 8, (y - STAIR_LANDING) * PX, (x1 + 1) * PX + 8, (y1 + 1 + STAIR_LANDING) * PX))
    return flats

FLAT_RUN = 2 * PX

def paint_ground(q, road, flats=()):
    """The approved painter on an 8 px material grid (Route 30's paint_ground without the town runs)."""
    U = 8
    hq, wq = q.shape
    h, w = hq * U, wq * U
    tex = G.textures()
    tex[G.PATH] = road
    ys, xs = np.mgrid[0:h, 0:w]
    wave = np.array(G.WAVE)
    near = np.zeros((h, w))
    for x0, y0, x1, y1 in flats:
        dx_ = np.maximum(np.maximum(x0 - xs, xs - (x1 - 1)), 0); dy_ = np.maximum(np.maximum(y0 - ys, ys - (y1 - 1)), 0)
        near = np.maximum(near, np.clip(1 - np.maximum(dx_, dy_) / FLAT_RUN, 0, 1))
    fade = 1 - near
    dx = np.rint(wave[ys % 32] * fade).astype(int); dyy = np.rint(wave[(xs + 11) % 32] * fade).astype(int)
    sx = np.clip(xs + dx, 0, w - 1) // U; sy = np.clip(ys + dyy, 0, h - 1) // U
    mat = q[sy, sx]
    out = np.zeros((h, w, 3), np.uint8)
    for m, t in tex.items():
        mm = mat == m
        out[mm] = t[ys[mm] % t.shape[0], xs[mm] % t.shape[1]]
    dist = {m: G._chamfer(mat == m) for m in tex}
    pa, pb = G.PROFILES[(G.GRASS, G.PATH)]
    for k, c in enumerate(pa):
        out[(mat == G.GRASS) & (dist[G.PATH] == k + 1)] = c
    for k, c in enumerate(pb):
        out[(mat == G.PATH) & (dist[G.GRASS] == k + 1)] = c
    return out, mat, tex

# --------------------------------------------------------------------------- HGSS-derived details
def lift(phg, names, keep):
    """HGSS ground-texture pixels of the named materials, in the native frame."""
    h, mat, nm, rgb = Rf.topdown(phg)
    ids = [nm.index(n) for n in names if n in nm]
    m = np.isin(mat, ids) & keep(rgb.astype(int))
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    a = art[ROW0 * PX:ROW0 * PX + HH * PX, COL0 * PX:COL0 * PX + HW * PX]
    a[m, :3] = rgb[m]; a[m, 3] = 255
    return art

def hgss_lawn_colours(phg):
    h, mat, nm, rgb = Rf.topdown(phg)
    return {tuple(int(v) for v in c) for c in np.unique(rgb[mat == nm.index('grass01gs')], axis=0)}

def cell_aligned(art, cover=0.5, kind=None):
    """HGSS's flower and light-lawn textures repeat every 32 px, so each patch is drawn cell by cell from one
    exemplar per 32 px phase (the phase's fullest cell): a cell at least `cover` covered takes it whole, a cell
    less covered drops its spill (tile budget)."""
    out = np.zeros_like(art)
    a = art[..., 3] > 0
    share = a.reshape(H, PX, W, PX).mean(axis=(1, 3))
    best = {}
    for y in range(H):
        for x in range(W):
            k = (x % 2, y % 2, None if kind is None else kind[y, x])
            if share[y, x] >= cover and share[y, x] > best.get(k, (0, None))[0]:
                best[k] = (share[y, x], (x, y))
    for y in range(H):
        for x in range(W):
            if share[y, x] >= cover:
                ex, ey = best[(x % 2, y % 2, None if kind is None else kind[y, x])][1]
                out[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX] = art[ey * PX:(ey + 1) * PX, ex * PX:(ex + 1) * PX]
    return out

def flowers(phg):
    plain = np.array(sorted(hgss_lawn_colours(phg)))
    h, mat, nm, rgb = Rf.topdown(phg)
    ids = np.array([nm.index(n) if n in nm else -9 for n in Rf.FLOWERS])
    kind = np.full((H, W), -1)
    cnt = np.stack([(mat == i).reshape(HH, PX, HW, PX).sum(axis=(1, 3)) for i in ids], -1)
    kind[ROW0:, COL0:] = np.where(cnt.max(-1) > 0, cnt.argmax(-1), -1)
    art = cell_aligned(lift(phg, Rf.FLOWERS, lambda c: ~(c[..., None, :] == plain[None, None]).all(-1).any(-1)), kind=kind)
    Image.fromarray(art).save(LOCAL / 'flowers.png')
    return art

def light_lawn(phg):
    plain = np.array(sorted(hgss_lawn_colours(phg)))
    art = lift(phg, Rf.LIGHT, lambda c: ~(c[..., None, :] == plain[None, None]).all(-1).any(-1))
    from scipy.ndimage import label
    lab, n = label(art[..., 3] > 0, structure=np.ones((3, 3)))
    sizes = np.bincount(lab.ravel())
    art[(sizes[lab] < 24) & (lab > 0)] = 0
    art = cell_aligned(art)
    Image.fromarray(art).save(LOCAL / 'light-lawn.png')
    return art

NB8 = ((0, -1), (1, 0), (0, 1), (-1, 0), (1, -1), (1, 1), (-1, 1), (-1, -1))

def exemplars(grid, src, cellset, alike, phase=True):
    """Every cell in cellset takes the pixels of the first HGSS cell (raster order) with the same pattern
    of `alike` neighbours (8 directions) and, with phase, the same 32 px texture phase: one exemplar per
    configuration. src is an HGSS-frame image. Returns (native-frame RGB image, cell mask, table)."""
    g = lambda x, y: grid[y][x] if 0 <= x < W and 0 <= y < H else '#'
    art = np.zeros((H * PX, W * PX, 3), np.uint8)
    mask = np.zeros((H, W), bool)
    pick, table = {}, {}
    for y in range(ROW0, H):
        for x in range(W):
            if g(x, y) not in cellset:
                continue
            k = tuple(int(g(x + dx, y + dy) in alike or (y + dy >= H and g(x, y) in alike)) for dx, dy in NB8)
            if phase and all(k):                        # open water keeps the 32 px texture phase; shore cells share one
                k += (x % 2, y % 2)
            if k not in pick:
                pick[k] = (x, y)
            ex, ey = pick[k]
            hx, hz = Rf.to_hgss(ex, ey)
            art[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX] = src[hz * PX:(hz + 1) * PX, hx * PX:(hx + 1) * PX]
            mask[y, x] = True
            table[f'{x},{y}'] = [ex, ey]
    return art, mask, dict(exemplars={','.join(map(str, k)): list(v) for k, v in pick.items()}, cells=table)

def sea_and_pier(phg, grid):
    """HGSS's sea and pier, one exemplar per neighbour configuration (flat decode, HGSS's own pixels).
    Water cells: '~', the blocked sea under the viaduct ('X' on the sea) and the water under boulders 'O'."""
    _, mat, nm, rgb = Rf.topdown(phg)
    # The sea's source keeps only HGSS's water and foam: land pixels at a shore cell's edge (rock bases, grass) take
    # the open sea's texture at the same place, so no land is copied into the water.
    water_ids = [nm.index(n) for n in nm if n.startswith('sea') or n == 'pond_line']   # pond_line: HGSS's shore rim and foam
    wet = np.isin(mat, water_ids)
    hy, hx = np.argwhere(wet.reshape(HH, PX, HW, PX).all(axis=(1, 3)))[0]
    block = rgb[hy * PX:hy * PX + 32, hx * PX:hx * PX + 32]
    yy, xx = np.mgrid[0:rgb.shape[0], 0:rgb.shape[1]]
    sea_src = np.where(wet[..., None], rgb, block[(yy - hy * PX) % 32, (xx - hx * PX) % 32])
    cells = json.loads((TRACE / 'ledger.json').read_text())['cells']
    sea_x = {(x, y) for y in range(ROW0, H) for x in range(W)
             if grid[y][x] in 'XO' and cells[y - ROW0][x]['material'].startswith('sea')}
    g2 = [row[:] for row in grid]
    for x, y in sea_x:
        g2[y][x] = '~'
    sea, smask, stab = exemplars(g2, sea_src, '~', '~B')
    bridge = np.isin(mat, [nm.index(n) for n in Rf.PIER if n in nm])
    pier, pmask, ptab = exemplars(g2, np.where(bridge[..., None], rgb, sea_src), 'B', 'B', phase=False)
    Image.fromarray(sea).save(LOCAL / 'sea.png'); Image.fromarray(pier).save(LOCAL / 'pier.png')
    (LOCAL / 'sea-pier-exemplars.json').write_text(json.dumps(dict(sea=stab, pier=ptab)) + '\n')
    return sea, smask, pier, pmask, sea_x

FULL_SEA_BOULDERS = True             # the whole sprite, over both columns HGSS blocks for it

def boulders(grid, sea_x):
    """HGSS's boulders as sprites at HGSS's own positions (they stand at half-cell offsets, so a per-cell cut
    breaks them): each connected boulder in HGSS's projected render (sea_rock in the sea, rock01 on land) with
    its white foam ring. Every sea boulder takes the most common-sized one (one exemplar); the two land boulders
    take the first. A sea boulder is its 16x16 core round the rock, on the cell nearest HGSS's position (tile budget); a land
    boulder (2x2 cells) is whole, on the 16 px grid. A flat overlay drawn into the ground."""
    from scipy.ndimage import label, find_objects
    gnd = np.array(Image.open(SRC / 'hgss/hgss-ground.png').convert('RGB')).astype(int)
    mz = np.load(SRC / 'hgss/hgss-ground-materials.npz')
    names = [str(n) for n in mz['names']]
    def comps(mats):
        m = np.isin(mz['material'], [names.index(n) for n in mats if n in names])
        lab, n = label(m)
        out = []
        for i, sl in enumerate(find_objects(lab), 1):
            if (lab[sl] == i).sum() < 24:
                continue
            ys, xs = sl
            y0, y1, x0, x1 = max(0, ys.start - 2), ys.stop + 2, max(0, xs.start - 2), xs.stop + 2
            win = gnd[y0:y1, x0:x1]
            k = (lab[y0:y1, x0:x1] == i) | ((win.min(-1) > 200) & ~(lab[y0:y1, x0:x1] > 0))
            spr = np.zeros(win.shape[:2] + (4,), np.uint8)
            spr[k, :3] = win[k]; spr[k, 3] = 255
            out.append(dict(xy=(x0, y0), art=spr, size=int((lab[sl] == i).sum())))
        return out
    sea = comps(('sea_rock', 'sea_rock_m'))
    land = comps(('rock01',))
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    placed = []
    def core(spr):
        """The sprite's 16x16 core round the rock's centre (the foam beyond it is left off)."""
        ys, xs = np.nonzero(spr[..., 3] > 0)
        cy, cx = int(round(ys.mean())), int(round(xs.mean()))
        out = np.zeros((PX, PX, 4), np.uint8)
        y0, x0 = max(0, cy - PX // 2), max(0, cx - PX // 2)
        part = spr[y0:y0 + PX, x0:x0 + PX]
        out[:part.shape[0], :part.shape[1]] = part
        return out, (x0, y0)
    def put(spr, x0, y0, kind):
        spr, (dx, dy) = (spr, (0, 0)) if kind == 'land' or FULL_SEA_BOULDERS else core(spr)
        x, y = int(round((x0 + dx) / 16)) * 16 + COL0 * PX, int(round((y0 + dy) / 16)) * 16 + ROW0 * PX
        h, w = spr.shape[:2]
        reg = art[y:y + h, x:x + w]; m = spr[:reg.shape[0], :reg.shape[1], 3] > 0
        reg[m] = spr[:reg.shape[0], :reg.shape[1]][m]
        placed.append(dict(kind=kind, xy=[x, y], hgss_xy=[int(x0), int(y0)]))
    if sea:
        sizes = Counter(c['art'].shape[:2] for c in sea)
        ex = next(c for c in sea if c['art'].shape[:2] == sizes.most_common(1)[0][0])
        for c in sea:
            put(ex['art'], *c['xy'], 'sea')
    for c in land:
        put(land[0]['art'], *c['xy'], 'land')
    Image.fromarray(art).save(LOCAL / 'boulders.png')
    return art, placed

ISLET_MAX = 40                      # a rock component this small with only water round it is a sea islet

def islets(grid):
    """HGSS's small rock islands in the sea: rock components under ISLET_MAX cells with only sea round them.
    Returns HGSS's own art for them (evidence: local-art/islets.png; lifting it costs about 120 tiles) and their
    cells, which take one terrace (HGSS's mixed heights broke the FRLG faces into fragments)."""
    from scipy.ndimage import label
    R = np.array([[c == 'R' for c in row] for row in grid])
    lab, n = label(R)
    gnd = np.array(Image.open(SRC / 'hgss/hgss-ground.png').convert('RGB')).astype(int)
    mz = np.load(SRC / 'hgss/hgss-ground-materials.npz')
    names = [str(nm) for nm in mz['names']]
    rockpx = np.isin(mz['material'], [names.index(nm) for nm in Rf.WALLS + ('sea_rock', 'sea_rock_m', 'pond_line') if nm in names])
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    cells = set()
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if len(ys) >= ISLET_MAX:
            continue
        around = {grid[y + dy][x + dx] for y, x in zip(ys, xs) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                  if 0 <= x + dx < W and 0 <= y + dy < H and lab[y + dy, x + dx] != i}
        if not around <= set('~XO'):
            continue
        cells |= set(zip(xs.tolist(), ys.tolist()))
        hy0, hy1 = (ys.min() - ROW0 - 2) * PX, (ys.max() - ROW0 + 1) * PX + 4
        hx0, hx1 = (xs.min() - COL0) * PX - 4, (xs.max() - COL0 + 1) * PX + 4
        hy0, hx0 = max(hy0, 0), max(hx0, 0)
        win = gnd[hy0:hy1, hx0:hx1]
        # Only the rock that belongs to this islet: the pixel regions of rock (and its white rim) touching its cells.
        part = rockpx[hy0:hy1, hx0:hx1] | (win.min(-1) > 200)
        pl, _ = label(part)
        own = np.zeros(part.shape, bool)
        for y, x in zip(ys, xs):
            cy0, cx0 = (y - ROW0) * PX - hy0, (x - COL0) * PX - hx0
            own[max(cy0, 0):cy0 + PX, max(cx0, 0):cx0 + PX] = True
        keep = set(np.unique(pl[own & part]).tolist()) - {0}
        m = np.isin(pl, list(keep))
        a = art[hy0 + ROW0 * PX:hy1 + ROW0 * PX, hx0 + COL0 * PX:hx1 + COL0 * PX]
        a[m, :3] = win[m]; a[m, 3] = 255
    Image.fromarray(art).save(LOCAL / 'islets.png')
    return art, cells

def cave_mouth():
    """HGSS's Union Cave mouth: the cavehole texture's pixels from HGSS's own projected render."""
    gnd = np.array(Image.open(SRC / 'hgss/hgss-ground.png').convert('RGB'))
    mz = np.load(SRC / 'hgss/hgss-ground-materials.npz')
    names = [str(n) for n in mz['names']]
    m = mz['material'] == names.index('cavehole')
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    a = art[ROW0 * PX:, COL0 * PX:]
    a[m, :3] = gnd[m]; a[m, 3] = 255
    Image.fromarray(art).save(LOCAL / 'cave-mouth.png')
    return art

# --------------------------------------------------------------------------- viaduct
VIADUCT_RAIL = 8                     # px of guard rail along each edge of the deck

def viaduct_art(phg):
    """The Magnet Train viaduct deck over HGSS's shadow footprint, above the player: HGSS's own Magnet Train
    track textures (a/2/3/3 model 0: senro_base, the concrete bed; senro_line, the rails) tiled across the
    route, a guard rail in the bed's lightest and darkest tones along both edges. Its shape is a proposal
    from the shadow; HGSS's viaduct model is not in Route 32's map data."""
    import hgss_render as R
    ms = R.narc.load(phg / 'files/a/2/3/3')
    m = R.mdlview.Model(ms[0])
    tex = {}
    for e in m.tex.textures:
        if e.name in ('senro_base', 'senro_line'):
            pal = m.tex.pal_for(e)
            tex[e.name] = R.decode(m.tex, e, pal.name if pal else None)[..., :3]
    base, line = tex['senro_base'], tex['senro_line']
    y0, y1 = VIADUCT_PX
    h, w = y1 - y0, W * PX
    deck = np.zeros((h, w, 3), np.uint8)
    yy, xx = np.mgrid[0:h, 0:w]
    deck[:] = base[yy % base.shape[0], xx % 16]           # the bed's left 16 px, repeated (tile budget)
    for rail in (h // 2 - 12, h // 2 + 4):                      # two rails, senro_line's 8 px band
        deck[rail:rail + line.shape[0]] = line[np.arange(line.shape[0])[:, None], xx[:line.shape[0]] % 16]
    tones = sorted({tuple(int(v) for v in c) for c in base.reshape(-1, 3)}, key=sum)
    light, dark = tones[-1], tones[0]
    for edge in (slice(0, VIADUCT_RAIL), slice(h - VIADUCT_RAIL, h)):
        deck[edge] = light
        deck[edge.start] = dark if edge.start == 0 else light
        deck[edge.stop - 1] = dark
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    art[y0:y1, :, :3] = deck; art[y0:y1, :, 3] = 255
    Image.fromarray(art[y0:y1]).save(LOCAL / 'viaduct.png')
    return art

# --------------------------------------------------------------------------- stairs, ledges
EW_PLANK_TONES = 3
EW_ROCK_SNAP = 14.0                  # Lab distance within which a Route 36 rock colour takes the Johto rock ramp

def fit_ew(pieces):
    """Route 30's: Route 36's plank flight sits in this route's wall, its rock cheeks in the wall's FRLG rock ramp,
    its planks reduced to EW_PLANK_TONES."""
    ramp = [tuple(int(v) for v in c) for c in Rk.ROCK_RAMP]
    lab_r = _lab(np.array(ramp))
    snap = {}
    cols = sorted({tuple(c) for p in pieces.values() for c in p[..., :3].reshape(-1, 3).tolist()})
    for c in cols:
        d = np.linalg.norm(lab_r - _lab(np.array([c]))[0], axis=1)
        if d.min() < EW_ROCK_SNAP:
            snap[c] = ramp[int(d.argmin())]
    planks = {k: apply_tones(v, snap) for k, v in pieces.items()}
    m = reduce_tones(list(planks.values()), keep=set(ramp), n=EW_PLANK_TONES)
    return {k: apply_tones(v, m) for k, v in planks.items()}

def stairs(phg, grid):
    """Route 30's stair pieces flight by flight on HGSS's stair cells. Each flight's direction is HGSS's own: the
    decoded height falls along x (east-west) or along y (north-south) across it. An east-west flight takes Route
    36's plank flight in each of its columns (its top cell with the dark cheek, plank cells, the bottom cell with
    the brown cheek); a north-south flight takes the grey treads in each of its rows (left end, middle, right end)."""
    p = {k: rgba(SHARED / f'stairs/{k}.png') for k in ('ns-left', 'ns-mid', 'ns-right', 'ew-top', 'ew-mid', 'ew-bottom')}
    p.update(fit_ew({k: v for k, v in p.items() if k.startswith('ew')}))
    h, _, _, _ = Rf.topdown(phg)
    gy, gx = np.gradient(h)
    g = lambda x, y: grid[y][x] if 0 <= x < W and 0 <= y < H else '#'
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    placed, seen = [], set()
    for y0 in range(H):
        for x0 in range(W):
            if g(x0, y0) != '^' or (x0, y0) in seen:
                continue
            comp, todo = set(), [(x0, y0)]
            while todo:
                c = todo.pop()
                if c in comp or g(*c) != '^':
                    continue
                comp.add(c); todo += [(c[0] + dx, c[1] + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            seen |= comp
            xs, ys = sorted({c[0] for c in comp}), sorted({c[1] for c in comp})
            sl = np.s_[(ys[0] - ROW0) * PX:(ys[-1] - ROW0 + 1) * PX, (xs[0] - COL0) * PX:(xs[-1] - COL0 + 1) * PX]
            ew = abs(float(gx[sl].mean())) > abs(float(gy[sl].mean()))
            for (x, y) in sorted(comp):
                if ew:
                    k = 'ew-top' if y == ys[0] else 'ew-bottom' if y == ys[-1] else 'ew-mid'
                else:
                    k = 'ns-left' if x == xs[0] else 'ns-right' if x == xs[-1] else 'ns-mid'
                art[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX] = p[k]
                placed.append(dict(cell=[x, y], art=k, flight='east-west' if ew else 'north-south',
                                   hgss_slope=[round(float(gx[sl].mean()), 3), round(float(gy[sl].mean()), 3)]))
    return art, placed

def ledge_pieces():
    l11, l12, l13 = (rgba(SHARED / f'{n}.png') for n in ('L11', 'L12', 'L13'))
    south = dict(left=l11, mid=l12, right=l13, single=np.concatenate([l11[:, :8], l13[:, 8:]], 1))
    ccw = lambda a: np.rot90(a, 1).copy()
    cw = lambda a: np.rot90(a, -1).copy()
    east = dict(top=ccw(l13), mid=ccw(l12), bottom=ccw(l11))
    west = dict(top=cw(l11), mid=cw(l12), bottom=cw(l13))
    return south, east, west

def ledges(grid):
    """Route 29's ledges(): south runs, east/west runs, corners joining both."""
    south, east, west = ledge_pieces()
    g = lambda x, y: grid[y][x] if 0 <= x < W and 0 <= y < H else '#'
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    placed = []
    def put(x, y, piece, name):
        sl = np.s_[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX]
        m = piece[..., 3] > 0
        art[sl][m] = piece[m]
        placed.append(dict(cell=[x, y], art=name))
    for y in range(H):
        for x in range(W):
            ch = g(x, y)
            if ch == 'L':
                left, right = g(x - 1, y) in 'LXJ', g(x + 1, y) in 'LXJ'
                k = 'mid' if left and right else 'left' if right else 'right' if left else 'single'
                put(x, y, south[k], f'L-{k}')
            elif ch in 'EQ':
                d = east if ch == 'E' else west
                up, down = g(x, y - 1) == ch, g(x, y + 1) in (ch + 'XJ')
                k = 'mid' if up and down else 'top' if down else 'bottom' if up else 'mid'
                put(x, y, d[k], f'{ch}-{k}')
            elif ch in 'XJ' and any(g(x + dx, y) == 'L' for dx in (-1, 1)):
                side = 'E' if g(x, y - 1) == 'E' else 'Q' if g(x, y - 1) == 'Q' else None
                run_west, run_east = g(x - 1, y) == 'L', g(x + 1, y) == 'L'
                k = 'mid' if run_west and run_east else 'right' if run_west else 'left'
                base = south[k].copy()
                if side:
                    vert = (east if side == 'E' else west)['mid']
                    lip = int(np.nonzero((base[..., 3] > 0).any(1))[0].min())
                    top = vert.copy(); top[lip:] = 0
                    m = top[..., 3] > 0
                    base[m] = top[m]
                put(x, y, base, f'corner-{side or "none"}-{k}')
    return art, placed

# --------------------------------------------------------------------------- tones (Route 30's)
LOCAL_TONES = 15
FLOWER_TONES, LIGHT_TONES = 3, 3

def _lab(c):
    c = np.asarray(c, float) / 255
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    xyz = c @ np.array([[0.4124, 0.2126, 0.0193], [0.3576, 0.7152, 0.1192], [0.1805, 0.0722, 0.9505]])
    xyz /= np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)

def reduce_tones(arts, keep, n=LOCAL_TONES):
    """Mahogany's reduction: kept tones farthest-first in Lab from the most common; every other tone joins
    its nearest kept tone; each group takes its most common member. Returns {old: new}."""
    cnt = Counter()
    for a in arts:
        m = a[..., 3] > 0 if a.shape[-1] == 4 else np.ones(a.shape[:2], bool)
        cnt.update(c for c in map(tuple, a[m][:, :3].tolist()) if c not in keep)
    cols = sorted(cnt, key=lambda c: -cnt[c])
    if len(cols) <= n:
        return {c: c for c in cols}
    lab = _lab(np.array(cols))
    chosen = [0]
    dmin = np.linalg.norm(lab - lab[0], axis=1)
    while len(chosen) < n:
        i = int(np.argmax(dmin))
        chosen.append(i)
        dmin = np.minimum(dmin, np.linalg.norm(lab - lab[i], axis=1))
    for _ in range(4):
        cent = lab[chosen]
        own = np.argmin(np.linalg.norm(lab[:, None] - cent[None], axis=2), 1)
        chosen = [max((i for i in range(len(cols)) if own[i] == g), key=lambda i: cnt[cols[i]]) for g in range(len(chosen)) if (own == g).any()]
    cent = lab[chosen]
    own = np.argmin(np.linalg.norm(lab[:, None] - cent[None], axis=2), 1)
    return {cols[i]: cols[chosen[own[i]]] for i in range(len(cols))}

def apply_tones(a, mapping):
    out = a.copy()
    if out.shape[-1] == 3:
        flat = out.reshape(-1, 3)
        new = np.array([mapping.get(tuple(c), tuple(c)) for c in flat.tolist()], np.uint8)
        return new.reshape(out.shape)
    m = out[..., 3] > 0
    px = out[m][:, :3]
    new = np.array([mapping.get(tuple(c), tuple(c)) for c in px.tolist()], np.uint8).reshape(-1, 3)
    sub = out[m]; sub[:, :3] = new; out[m] = sub
    return out

SEA_TONES, PIER_TONES, BOULDER_TONES, CAVE_TONES, ISLET_TONES = 6, 5, 4, 2, 8
LAND_BOULDER_TONES = 3
RIM_ON_LAND = False                  # the rim in land cells joined the sea's and land's palettes: 13 no longer fit

# --------------------------------------------------------------------------- compose
def over(dst, src, x, y, owner=None, name=''):
    h, w = src.shape[:2]
    sy0, sx0 = max(0, -y), max(0, -x)
    sy1, sx1 = min(h, dst.shape[0] - y), min(w, dst.shape[1] - x)
    s = src[sy0:sy1, sx0:sx1]
    a = s[..., 3] > 0
    d = dst[y + sy0:y + sy1, x + sx0:x + sx1]
    d[a] = s[a]
    if owner is not None:
        owner[y + sy0:y + sy1, x + sx0:x + sx1][a] = name

def read_grid():
    lines = [l for l in (TRACE / 'material-grid.txt').read_text().splitlines() if l[:3].isdigit()]
    return [list(l.split()[1]) for l in lines]

def padding(engine, bottom):
    """North padding: rows 0-5 drawn from Violet's own row 71 (lawn, road) at Violet's columns."""
    t, words = violet(engine)
    ids = {}
    for y in range(ROW0):
        for x in range(W):
            vx, vy = Rf.pad_source(x, y)
            m = int(words[vy, vx]) & 1023
            bottom[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX] = np.array(t.render(m).convert('RGB'))
            ids[(x, y)] = m
    return ids

def compose(phg, engine):
    grid = read_grid()
    cells = json.loads((TRACE / 'ledger.json').read_text())['cells']
    ncells = native_cells(cells, grid)
    events = json.loads((SRC / 'hgss-events.json').read_text())
    rinfo = json.loads((SRC / 'hgss/hgss-render.json').read_text())
    roots = [tuple(r) for r in json.loads((TRACE / 'trees.json').read_text())['roots']]
    road = road_texture(engine)
    def local(art, n, keep=()):
        # Each local family keeps its own n tones (Mahogany's reduction), so a tile of it never pulls in another
        # family's colours; `keep` colours (the rock ramp, for the cave mouth) are left as they are.
        return apply_tones(art, reduce_tones([art], keep=set(keep), n=n))
    q, flats = ground_quadrants(phg, ncells)
    bottom, mat, tex = paint_ground(q, road, flats)
    pad_ids = padding(engine, bottom)
    # The sea and the pier (HGSS's pixels, one exemplar per configuration), into the ground.
    sea, smask, pier, pmask, sea_x = sea_and_pier(phg, grid)
    seamask = np.repeat(np.repeat(smask, PX, 0), PX, 1)
    piermask = np.repeat(np.repeat(pmask, PX, 0), PX, 1)
    sea = np.dstack([sea, np.full(sea.shape[:2], 255, np.uint8)]); pier = np.dstack([pier, np.full(pier.shape[:2], 255, np.uint8)])
    # The sea first; the water at a pier cell's edges is the same sea and takes the same tones; then the planks
    # keep PIER_TONES of their own.
    m_sea = reduce_tones([sea[seamask][None]], keep=set(), n=SEA_TONES)
    sea, pier = apply_tones(sea, m_sea)[..., :3], apply_tones(pier, m_sea)
    sea_cols = {tuple(c) for c in sea[seamask][:, :3].tolist()}
    pier = apply_tones(pier, reduce_tones([pier[piermask][None]], keep=sea_cols, n=PIER_TONES))[..., :3]
    bottom[seamask] = sea[seamask]
    bottom[piermask] = pier[piermask]
    water_block = sea[np.nonzero(smask)[0][0] * PX:np.nonzero(smask)[0][0] * PX + PX, np.nonzero(smask)[1][0] * PX:np.nonzero(smask)[1][0] * PX + PX]
    # HGSS's shore rim (pond_line) where it reaches into land cells beside the sea, into the ground (rock cells
    # take their FRLG faces instead).
    _, tmat, tnm, trgb = Rf.topdown(phg)
    rim = tmat == tnm.index('pond_line')
    # On land the rim takes the land's own vocabulary: the rock ramp, the cast-shadow grey, the lawn rim and the
    # road (so a land tile never pulls the sea's palette in).
    sea_tones = np.array(sorted({tuple(int(v) for v in c) for c in Rk.ROCK_RAMP + [Rk.BORDER_GRAY, Rk.FRINGE_RIM]}
                                | {tuple(c) for c in road.reshape(-1, 3).tolist()}), int)
    for y in range(ROW0, H):
        for x in range(W):
            if grid[y][x] in '~XOBR^tko' or (x, y) in sea_x:      # woods: under the crowns, slivers only
                continue
            hsl = np.s_[(y - ROW0) * PX:(y - ROW0 + 1) * PX, (x - COL0) * PX:(x - COL0 + 1) * PX]
            if RIM_ON_LAND and rim[hsl].any():
                cell = bottom[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX]
                px = trgb[hsl][rim[hsl]]                   # each rim pixel the nearest land tone
                cell[rim[hsl]] = sea_tones[np.argmin(((px[:, None, :].astype(int) - sea_tones[None]) ** 2).sum(-1), 1)]
    # Rock terraces over the ground (bottom keeps the plain block beyond each edge; the sea beyond a sea cliff).
    ia, islet_cells = islets(grid)
    for x, y in islet_cells:                           # one terrace above the sea: HGSS's mixed heights broke them up
        ncells[y][x] = dict(ncells[y][x], lab='R', ground=float(FLOOR + 1), peak=float(FLOOR + 1))
    d, isrock = Rk.terraces(ncells, FLOOR)
    plain_tex = dict(grass=tex[G.GRASS], sand=tex[G.PATH], water=water_block)
    bottom, rock_over, piece = Rk.rock_frlg(ncells, d, isrock, bottom, Rk.frlg_pieces(engine), plain_tex, soft=True)
    flat = np.zeros((H * PX, W * PX, 4), np.uint8)
    flat_owner = np.full((H * PX, W * PX), '', object)
    def lay(art, name):
        a = art[..., 3] > 0
        flat[a] = art[a]; flat_owner[a] = name
    light, flw = light_lawn(phg), flowers(phg)
    flw, light = local(flw, FLOWER_TONES), local(light, LIGHT_TONES)
    g15 = rgba(SHARED / 'G15.png')
    tg = np.zeros_like(flat); n_g15 = 0
    for y in range(H):
        for x in range(W):
            if grid[y][x] == 'G':
                tg[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX] = g15; n_g15 += 1
    la, ledge_list = ledges(grid)
    sa, stair_list = stairs(phg, grid)
    # The plank flight is wood like the pier: its plank tones take the nearest pier tone (palette budget).
    keep_s = {tuple(c) for k in ('ns-left', 'ns-mid', 'ns-right') for c in rgba(SHARED / f'stairs/{k}.png')[..., :3].reshape(-1, 3).tolist()}
    keep_s |= {tuple(int(v) for v in c) for c in Rk.ROCK_RAMP}
    wood = np.array(sorted({tuple(c) for c in pier[piermask].tolist()} - {tuple(c) for c in sea[seamask].tolist()}), int)
    scol = sorted({tuple(c) for c in sa[sa[..., 3] > 0][:, :3].tolist()} - keep_s)
    if len(wood) and scol:
        lab_w = _lab(wood)
        sa = apply_tones(sa, {c: tuple(int(v) for v in wood[int(np.argmin(np.linalg.norm(lab_w - _lab(np.array([c]))[0], axis=1)))]) for c in scol})
    ba, boulder_list = boulders(grid, sea_x)
    # Every sea boulder stands on the same open-water cell (HGSS's sea at one texture phase), so all of them are
    # one native cell (tile budget).
    ox, oy = next((x, y) for y in range(ROW0, H) for x in range(W) if smask[y, x] and x % 2 == 0 and y % 2 == 0
                  and all(0 <= x + dx < W and 0 <= y + dy < H and smask[y + dy, x + dx] and grid[y + dy][x + dx] == '~' for dx in (-1, 0, 1) for dy in (-1, 0, 1)))
    open_sea = bottom[oy * PX:(oy + 1) * PX, ox * PX:(ox + 1) * PX].copy()
    for y in range(ROW0, H):
        for x in range(W):
            if grid[y][x] == 'O' and (x, y) in sea_x:
                bottom[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX] = open_sea
    land_px = np.zeros(ba.shape[:2], bool)              # the land boulders keep their own tones
    for b_ in boulder_list:
        if b_['kind'] == 'land':
            x, y = b_['xy']; land_px[y:y + 2 * PX + 8, x:x + 2 * PX + 8] = True
    sea_b, land_b = ba.copy(), ba.copy()
    sea_b[land_px] = 0; land_b[~land_px] = 0
    ba = local(sea_b, BOULDER_TONES)
    lb = local(land_b, LAND_BOULDER_TONES)
    ba[lb[..., 3] > 0] = lb[lb[..., 3] > 0]
    ca = local(cave_mouth(), CAVE_TONES, keep=[tuple(c) for c in Rk.ROCK_RAMP])
    # Terrain belongs to the bottom layer: rock faces, stairs and the cave mouth are drawn into the
    # ground, so whatever stands on top (crowns, roofs, signs) never shares a tile with them.
    for art in (rock_over, sa, ca):
        a = art[..., 3] > 0
        bottom[a] = art[a][:, :3]
    # Boulders sit in the upper tile over the water (still under the player): their tiles then depend only on
    # the sprite, not on the water texture beneath (tile budget).
    lay(light, 'light_lawn'); lay(flw, 'flowers'); lay(tg, 'tall_grass'); lay(la, 'ledge'); lay(ba, 'boulders')
    top = np.zeros((H * PX, W * PX, 4), np.uint8)
    owner = np.full((H * PX, W * PX), '', object)
    tree = rgba(SHARED / 'cherrygrove-tree-with-shadow.png')
    objs = [dict(name=f'tree_{i}', master='shared-art/cherrygrove-tree-with-shadow.png (T01 + shadow)', xy=[x * PX, (y - 1) * PX], art=tree, root=[x, y])
            for i, (x, y) in enumerate(roots)]
    gx, gy = GATE_ORIGIN
    objs.append(dict(name='gate_alph', master='shared-art/G02.png', xy=[gx * PX, gy * PX], art=rgba(SHARED / 'G02.png')))
    door = next((x, y) for y, row in enumerate(grid) for x, ch in enumerate(row) if ch == 'D')
    cx, cy = door[0] - CENTER_DOOR[0], door[1] - CENTER_DOOR[1]
    objs.append(dict(name='pokemon_center', master='shared-art/C06.png', xy=[cx * PX, cy * PX], art=rgba(SHARED / 'C06.png'), door=list(door)))
    p14 = rgba(SHARED / 'P14.png')
    for s in events['signs']:
        if s['bg_type'] != 1:
            continue
        x, y = Rf.to_map(*s['cell'])
        objs.append(dict(name=f'sign_{x}_{y}', master='shared-art/P14.png', xy=[x * PX - 8, (y + 1) * PX - p14.shape[0]], art=p14, cell=[x, y]))
    for o in objs:
        al = o['art'][..., 3] > 0
        o['base'] = o['xy'][1] + int(np.nonzero(al.any(1))[0].max())
    objs.sort(key=lambda o: (o['base'], o['xy'][0]))
    for o in objs:
        over(top, o['art'], o['xy'][0], o['xy'][1], owner, o['name'])
    # The viaduct stands over everything on its rows.
    va = viaduct_art(phg)
    # The viaduct takes Violet's palette 11 (its greys), which Route 32 carries for the seam anyway: each of its
    # tones becomes the nearest of those greys in Lab, so the deck's tiles need no palette of their own.
    from tiles import Tileset
    v11 = [tuple(int(v) for v in c) for c in Tileset(engine, 'violet_city', 'violet_city').pals[1][11][1:]]
    lab11 = _lab(np.array(v11))
    vcols = sorted({tuple(c) for c in va[va[..., 3] > 0][:, :3].tolist()})
    va = apply_tones(va, {c: v11[int(np.argmin(np.linalg.norm(lab11 - _lab(np.array([c]))[0], axis=1)))] for c in vcols})
    over(top, va, 0, 0, owner, 'viaduct')
    (LOCAL / 'reductions.json').write_text(json.dumps(dict(
        rule=('Local HGSS art, reduced by medoids in Lab (the most distinct original tones kept farthest-first, every '
              'other tone joining its nearest), each family within its own tones: sea 7 (the shore rim in land cells takes the '
              'nearest rock, rim or road tone), pier 5, sea boulders 4, land boulders 4, cave mouth 2 (with the rock ramp), east-west stair planks the nearest pier tone, '
              'flowers 4, light lawn 3. The viaduct takes the nearest of Violet palette 11\'s greys.')), indent=1) + '\n')
    fam = lambda a: sorted({tuple(int(v) for v in c) for c in (a[a[..., 3] > 0][:, :3] if a.shape[-1] == 4 else a.reshape(-1, 3)).tolist()})
    families = dict(sea=fam(sea[seamask]), pier=fam(pier[piermask]), rock=fam(rock_over), boulders=fam(ba), cave=fam(ca), viaduct=fam(va),
                    flowers=fam(flw), light=fam(light), stairs=fam(sa), ledges=fam(la), tall_grass=fam(g15), lawn=fam(tex[G.GRASS]),
                    road=fam(road), tree=fam(tree), gate=fam(rgba(SHARED / 'G02.png')), center=fam(rgba(SHARED / 'C06.png')), sign=fam(p14),
                    padding=fam(bottom[:ROW0 * PX]))
    (OUT / 'families.json').write_text(json.dumps(families) + '\n')
    return dict(bottom=bottom, flat=flat, flat_owner=flat_owner, top=top, owner=owner, objs=objs, ledges=ledge_list,
                stairs=stair_list, boulders=boulder_list, n_g15=n_g15, q=q, padding=pad_ids, terrace=d, rock_piece=piece)

def main(phg, catalog, engine):
    for d in (OUT, OEV, LOCAL, SHARED):
        d.mkdir(parents=True, exist_ok=True)
    stage_shared(catalog)
    r = compose(phg, engine)
    view = r['bottom'].copy()
    for layer in (r['flat'], r['top']):
        a = layer[..., 3] > 0
        view[a] = layer[a, :3]
    Image.fromarray(view).save(OEV / 'composed.png')
    np.savez_compressed(OUT / 'layers.npz', ground=r['bottom'], flat=r['flat'], flat_owner=r['flat_owner'].astype(str), objects=r['top'],
                        owner=r['owner'].astype(str), quadrants=r['q'], terrace=r['terrace'])
    (OUT / 'placements.json').write_text(json.dumps(dict(
        note='Every placed object: master, top-left pixel, base row. Trees on the 2x2 roots of reference.py, crown one row behind.',
        objects=[{k: v for k, v in o.items() if k not in ('art',)} for o in r['objs']], ledges=r['ledges'], stairs=r['stairs'],
        boulders=r['boulders'], tall_grass_cells=r['n_g15'],
        padding={f'{x},{y}': f'{m:#05x}' for (x, y), m in sorted(r['padding'].items())}), indent=1, default=int) + '\n')
    print('objects', len(r['objs']), 'ledges', len(r['ledges']), 'stairs', len(r['stairs']), 'tall grass', r['n_g15'])

if __name__ == '__main__':
    main(*(Path(a).resolve() for a in sys.argv[1:4]))
