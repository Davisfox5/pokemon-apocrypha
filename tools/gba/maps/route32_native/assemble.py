"""Route 32: native art assembled by the Route 29/30 catalog process (Mahogany Town / Route 43).

    python3 tools/gba/maps/route32_native/assemble.py PHG_CHECKOUT CATALOG_CHECKOUT ENGINE_CHECKOUT

CATALOG_CHECKOUT is a checkout of the Johto catalog commit (pokemon-apocrypha codex/violet-city
de5d8cfb). Shared art is copied byte for byte into source/shared-art/ with its hash:

  ground      the approved Cherrygrove/Route 36 painter (claude_cherrygrove/ground.py) on an 8 px
              lawn/road grid read from HGSS's own flat ground colours; lawn and road are Cherrygrove's
              own textures (its road block at the engine's base revision)
  rock        Blackthorn's FRLG terraces in the Johto rock ramp (rock.py, Route 30's): every HGSS height
              layer one terrace, the soft grass fringe where a rock top meets grass at its height
  trees       the Cherrygrove tree (T01 with the town's contact shadow, Route 30's local cut) on
              non-overlapping 2x2 roots
  tall grass  the catalog set G00-G15 by neighbour mask on every HGSS tall-grass cell (round patch edges)
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
ART = ROOT / 'gba/art/route32-native'
SRC, EV = ART / 'source', ART / 'evidence'
TRACE, SHARED, LOCAL = SRC / 'trace', SRC / 'shared-art', SRC / 'local-art'
OUT, OEV = SRC / 'assemble', EV / 'assemble'

CATALOG = {n + '.png': f'gba/art/johto-common/scenery/source/{n}.png' for n in ('P14', 'L11', 'L12', 'L13')}
CATALOG.update({f'stairs/S0{i}.png': f'gba/art/johto-common/scenery/source/S0{i}.png' for i in range(1, 6)})
CATALOG.update({f'tall-grass/G{m:02d}.png': f'gba/art/johto-common/scenery/source/G{m:02d}.png' for m in range(16)})
CATALOG['T01.png'] = 'gba/art/johto-common/trees/source/T01.png'
CATALOG['G02.png'] = 'gba/art/johto-common-review/gates/refinement-4/G02.png'
CATALOG['C06.png'] = 'gba/art/johto-center/source/building.png'
# Already cut on the hub's main branch (Route 30's catalog work).
HUB = {'cherrygrove-tree-with-shadow.png': 'gba/art/route30-catalog/source/local-art/cherrygrove-tree-with-shadow.png'}
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
                if grid[y][x] in 'R~' and c['lab'] in 'R~':
                    c['lab'] = grid[y][x]                 # the grid's rock and sea (it straightens the islet's column)
                if grid[y][x] in '~X' and c['type'] in (0x15, 0x10, 0) and c['material'].startswith('sea'):
                    c['floor'] = 'water'
                if grid[y][x] in '~B' or c['material'].startswith('sea'):
                    c['floor'] = 'water'                  # a land boulder (rock01) keeps HGSS's own floor
                if c['floor'] == 'water' and grid[y][x] != 'B':
                    c.update(ground=0.0, peak=0.0)       # the sea is one level, below every rock face beside it
            c['code'] = grid[y][x]
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
            if y < ROW0:                                  # the padding is drawn from Violet; lawn for the painter
                q[qy, qx] = G.GRASS
                continue
            if lab in 'FG~B' or ncells[y][x]['floor'] == 'water':
                q[qy, qx] = G.GRASS
                continue
            hqx, hqy = qx - COL0 * 2, qy - ROW0 * 2
            sl = np.s_[hqy * 8:hqy * 8 + 8, hqx * 8:hqx * 8 + 8]
            nl, ns = int(lawn[sl].sum()), int(sand[sl].sum())
            if ns >= 32 and ns > nl:
                q[qy, qx] = G.PATH
            elif nl >= (40 if ncells[y][x]['floor'] == 'sand' or ncells[y][x].get('code') == 'd' else 8):   # a road cell needs real lawn, not wall-foot specks
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
    for y in range(H):                                 # stairs stand on the path that runs through them
        for x in range(W):
            if ncells[y][x]['lab'] == '^':
                q[2 * y:2 * y + 2, 2 * x:2 * x + 2] = G.PATH
    # Under rock the ground runs on as the nearest open ground's material (lawn or road), so the clear pixels
    # of a cliff piece show the ground actually beside it on each side, not one plain block.
    from scipy.ndimage import distance_transform_edt
    rockq = np.repeat(np.repeat(np.array([[c['lab'] in 'RX' for c in row] for row in ncells]), 2, 0), 2, 1)
    if rockq.any():
        _, (iy, ix) = distance_transform_edt(rockq, return_indices=True)
        q[rockq] = q[iy[rockq], ix[rockq]]
    # specks again, now that the ground under the rock is known (lawn left in a road strip beside a wall)
    lab_, n_ = label((q == G.GRASS) & ~rockq)
    sizes = np.bincount(lab_.ravel())
    for i in range(1, n_ + 1):
        if sizes[i] < 8:
            q[lab_ == i] = G.PATH
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
            if y1 - y + 1 >= x1 - x + 1:
                seen |= {(c, r) for c in range(x, x1 + 1) for r in range(y, y1 + 1)}
                continue                                   # taller than wide: an east-west flight through a wall
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

# --------------------------------------------------------------------------- straight paths
PATH_ROUND = 6                       # corner radius, px (Cherrygrove's accepted town paths)
PATH_SNAP = {(216, 168, 128): (216, 184, 128)}       # the texture's darkest pebbles, never drawn on Cherrygrove's paths

def _disk(r):
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    return xx * xx + yy * yy <= r * r

def paint_paths(grid, ncells, q):
    """Cherrygrove's own path finish (cherrygrove_town/elements.py, accepted for the town): the dirt road is the
    cell grid of HGSS's road cells ('d', the stairs and the Center door), opened and closed with a disk so the
    convex and concave corners round off, every run straight; the painter's lawn and sand by absolute pixel,
    and its grass/path rim profile either side of the edge. The road never runs under a tree, a wall or the
    water: those cells are not road cells."""
    from scipy.ndimage import binary_closing, binary_opening
    cells = np.array([[ch in 'dD' for ch in row] for row in grid])
    # a flight is road only where a road reaches it (the road runs up to the treads); a flight between lawns
    # stands in the lawn, with no sand rim round it
    from scipy.ndimage import label as _label, binary_dilation as _dil
    fl, fn = _label(np.array([[ch == '^' for ch in row] for row in grid]))
    for i in range(1, fn + 1):
        if (_dil(fl == i) & cells).any():
            cells |= fl == i
    # ledges, boulders and signs stand on the ground around them: on the road where most of their neighbours are
    for _ in range(2):
        for y in range(len(grid)):
            for x in range(len(grid[0])):
                if grid[y][x] in 'LQEJOs' and not cells[y, x]:
                    nb = [cells[b, a] for a, b in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
                          if 0 <= a < cells.shape[1] and 0 <= b < cells.shape[0] and grid[b][a] not in 'RXtk~LQEJOs']
                    if nb and sum(nb) * 2 > len(nb):
                        cells[y, x] = True
    # the road runs straight onto the pier: a pier cell the road meets counts as road here (the planks cover it),
    # so the road's corners stay square at the landing instead of rounding off into lawn notches
    road0 = cells.copy()
    for y in range(len(grid)):
        for x in range(len(grid[0])):
            if grid[y][x] == 'B' and any(0 <= a < cells.shape[1] and 0 <= b < cells.shape[0] and road0[b, a]
                                         for a, b in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                cells[y, x] = True
    path = np.repeat(np.repeat(cells, PX, 0), PX, 1)
    pad = 2 * PATH_ROUND
    pp = np.pad(path, pad, mode='edge')
    pp = binary_opening(binary_closing(pp, _disk(PATH_ROUND)), _disk(PATH_ROUND))
    path = pp[pad:-pad, pad:-pad]
    tex = G.textures()
    sand = tex[G.PATH].copy()
    for c, to in PATH_SNAP.items():
        sand[(sand == c).all(-1)] = to
    tex[G.PATH] = sand
    h, w = path.shape
    ys, xs = np.mgrid[0:h, 0:w]
    out = np.where(path[..., None], sand[ys % 32, xs % 32], tex[G.GRASS][ys % 32, xs % 32]).astype(np.uint8)
    pa, pb = G.PROFILES[(G.GRASS, G.PATH)]
    to_path, to_lawn = G._chamfer(path), G._chamfer(~path)
    for i, c in enumerate(pa):
        out[~path & (to_path == i + 1)] = c
    for i, c in enumerate(pb):
        out[path & (to_lawn == i + 1)] = c
    mat = np.where(path, G.PATH, G.GRASS).astype(np.int8)
    return out, mat, tex

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

CG_SEA = ((58, 59), (75, 76))       # Cherrygrove's open sea, a 2x2 block of its metatiles
CG_SEA_ROCK = 151                   # Cherrygrove's grey sea rock (and its foam), as the town draws it
FOAM, SAND_RIM = (200, 232, 224), (208, 208, 168)   # Cherrygrove's beach foam and the sand's waterline rim
PIER_ROUND, PIER_FOAM = 6, 2              # px: the pier's rounded outside corners and the foam line along it
BANK, BANK_PX = (198, 148, 115), 3        # HGSS's brown bank where grass meets water (189,140,99), as the rock ramp's tone
PIER_TEX = ROOT / 'gba/art/cherrygrove-town/source/hgss/pier.png'   # HGSS Route 32's pier repeat (hgss_pier.py), as Cherrygrove's dock
PIER_RAIL = 8                             # px: the rail each side of the repeat's 32 px of boards
PIER_BEAM = (165, 132, 90)                # Cherrygrove's end beam: the wood's darkest tone

def cherrygrove_tiles(engine):
    from tiles import Tileset
    return Tileset(engine, 'cherrygrove', 'cherrygrove_town')

def sea_and_pier(phg, grid, engine):
    """Cherrygrove's sea and dock (the town's accepted water vocabulary) on HGSS's water and pier cells.
    Water cells: '~', the blocked sea under the viaduct ('X' on the sea) and the water under boulders 'O'.
    Where the sea meets lawn or road, the town's beach edge: foam over the sea, the sand's waterline rim
    (rock edges take their FRLG faces instead). The pier is Cherrygrove's dock (HGSS Route 32's own pier
    repeat), with a foam line along it and its outside corners rounded where it meets open water."""
    t = cherrygrove_tiles(engine)
    block = np.zeros((32, 32, 3), np.uint8)
    for r in (0, 1):
        for c in (0, 1):
            block[r * 16:(r + 1) * 16, c * 16:(c + 1) * 16] = np.array(t.render(CG_SEA[r][c]).convert('RGB'))
    cells = json.loads((TRACE / 'ledger.json').read_text())['cells']
    sea_x = {(x, y) for y in range(ROW0, H) for x in range(W)
             if grid[y][x] in 'XO' and cells[y - ROW0][x - COL0]['material'].startswith('sea')}
    smask = np.array([[grid[y][x] == '~' or (x, y) in sea_x for x in range(W)] for y in range(H)])
    pmask = np.array([[grid[y][x] == 'B' for x in range(W)] for y in range(H)])
    yy, xx = np.mgrid[0:H * PX, 0:W * PX]
    sea = block[yy % 32, xx % 32]
    land = lambda x, y: 0 <= x < W and 0 <= y < H and not smask[y, x] and not pmask[y, x] and grid[y][x] not in 'ROX'
    for y in range(H):
        for x in range(W):
            if not smask[y, x]:
                continue
            for side, (dx, dy) in dict(n=(0, -1), s=(0, 1), w=(-1, 0), e=(1, 0)).items():
                if not land(x + dx, y + dy):
                    continue
                # a grass shore has HGSS's brown bank between the grass and the foam; a sand shore the sand's rim
                grassy = grid[y + dy][x + dx] not in 'dD^'
                for k in range(PX):
                    wob = G.WAVE[((y * PX + k) if side in 'we' else (x * PX + k)) % 32] // 4
                    for depth in range(4 + wob + (BANK_PX - 1 if grassy else 0)):
                        px_ = dict(n=(x * PX + k, y * PX + depth), s=(x * PX + k, (y + 1) * PX - 1 - depth),
                                   w=(x * PX + depth, y * PX + k), e=((x + 1) * PX - 1 - depth, y * PX + k))[side]
                        if grassy:
                            sea[px_[1], px_[0]] = BANK if depth < BANK_PX else FOAM
                        else:
                            sea[px_[1], px_[0]] = SAND_RIM if depth == 0 else FOAM
    # The dock is Cherrygrove's: HGSS Route 32's own pier repeat (8 px rail, 32 px of cross boards, 8 px rail,
    # 32 px down), laid along each run with its rails at the run's two long edges and all 32 px of boards between
    # (the boards repeat every 32 px across a wider run), turned a quarter for an east-west run, a beam across
    # each end of a run that stands in the water.
    tex = np.array(Image.open(PIER_TEX).convert('RGB'))
    pier = np.zeros_like(sea)
    for y in range(H):
        for x in range(W):
            if not pmask[y, x]:
                continue
            vert = (y > 0 and pmask[y - 1, x]) or (y < H - 1 and pmask[y + 1, x])
            horiz = (x > 0 and pmask[y, x - 1]) or (x < W - 1 and pmask[y, x + 1])
            along_y = vert or not horiz
            if along_y:
                lo = hi = x
                while lo - 1 >= 0 and pmask[y, lo - 1]: lo -= 1
                while hi + 1 < W and pmask[y, hi + 1]: hi += 1
            else:
                lo = hi = y
                while lo - 1 >= 0 and pmask[lo - 1, x]: lo -= 1
                while hi + 1 < H and pmask[hi + 1, x]: hi += 1
            w_ = (hi - lo + 1) * PX
            for py in range(PX):
                for px_ in range(PX):
                    X, Y = x * PX + px_, y * PX + py
                    across, along = (X - lo * PX, Y) if along_y else (Y - lo * PX, X)
                    if across < PIER_RAIL:
                        col = across
                    elif across >= w_ - PIER_RAIL:
                        col = tex.shape[1] - (w_ - across)
                    else:
                        col = PIER_RAIL + (across - PIER_RAIL) % (tex.shape[1] - 2 * PIER_RAIL)
                    pier[Y, X] = tex[along % tex.shape[0], col]
    for y in range(H):
        for x in range(W):
            if not pmask[y, x]:
                continue
            vert = (y > 0 and pmask[y - 1, x]) or (y < H - 1 and pmask[y + 1, x])
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                if (dx == 0) == bool(vert) and 0 <= x + dx < W and 0 <= y + dy < H and smask[y + dy, x + dx]:
                    sl = {(0, -1): np.s_[y * PX:y * PX + 2, x * PX:(x + 1) * PX], (0, 1): np.s_[(y + 1) * PX - 2:(y + 1) * PX, x * PX:(x + 1) * PX],
                          (-1, 0): np.s_[y * PX:(y + 1) * PX, x * PX:x * PX + 2], (1, 0): np.s_[y * PX:(y + 1) * PX, (x + 1) * PX - 2:(x + 1) * PX]}[(dx, dy)]
                    pier[sl] = PIER_BEAM
    # Where the planks meet open water: a thin foam line along the pier (HGSS's), and each outside corner rounded
    # off (the deck stops PIER_ROUND px short of a square corner and the foam follows the curve).
    wet = lambda x, y: 0 <= x < W and 0 <= y < H and smask[y, x]
    clean = sea.copy()
    for y in range(H):
        for x in range(W):
            if not smask[y, x]:
                continue
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                if 0 <= x + dx < W and 0 <= y + dy < H and pmask[y + dy, x + dx]:
                    for d in range(PIER_FOAM):
                        if dx:
                            X = (x + 1) * PX - 1 - d if dx > 0 else x * PX + d
                            sea[y * PX:(y + 1) * PX, X] = FOAM
                        else:
                            Y = (y + 1) * PX - 1 - d if dy > 0 else y * PX + d
                            sea[Y, x * PX:(x + 1) * PX] = FOAM
    r, f = PIER_ROUND, PIER_FOAM
    from collections import Counter as _C
    base = np.array(_C(map(tuple, clean[np.repeat(np.repeat(smask, PX, 0), PX, 1)].tolist())).most_common(1)[0][0], np.uint8)
    for y in range(H):
        for x in range(W):
            if not pmask[y, x]:
                continue
            for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                if not (wet(x + sx, y) and wet(x, y + sy) and wet(x + sx, y + sy)):
                    continue
                cx = x * PX + r if sx < 0 else (x + 1) * PX - r       # the curve's centre, r inside the corner
                cy = y * PX + r if sy < 0 else (y + 1) * PX - r
                xs = range(x * PX - f, x * PX + r) if sx < 0 else range((x + 1) * PX - r, (x + 1) * PX + f)
                ys = range(y * PX - f, y * PX + r) if sy < 0 else range((y + 1) * PX - r, (y + 1) * PX + f)
                for Y in ys:
                    for X in xs:
                        dist = np.hypot(X + 0.5 - cx, Y + 0.5 - cy)
                        if dist <= r or not (0 <= X < W * PX and 0 <= Y < H * PX):
                            continue
                        if pmask[Y // PX, X // PX]:
                            # inside a pier cell: foam, then the sea's main tone (a pier tile keeps few sea colours)
                            c = FOAM if dist <= r + f else base
                            pier[Y, X] = c; sea[Y, X] = c
                        else:
                            sea[Y, X] = FOAM if dist <= r + f else clean[Y, X]
    Image.fromarray(sea).save(LOCAL / 'sea.png'); Image.fromarray(pier).save(LOCAL / 'pier.png')
    return sea, smask, pier, pmask, sea_x

FULL_SEA_BOULDERS = True             # the whole sprite, over both columns HGSS blocks for it

def boulders(grid, sea_x, engine):
    """Cherrygrove's grey sea rock (metatile 151, the town's own) on each HGSS boulder: one per connected run
    of boulder cells, on its first cell. In the sea with the town's foam; on land the rock alone (its
    sea-coloured pixels clear), on HGSS's land boulder cells."""
    from scipy.ndimage import label
    t = cherrygrove_tiles(engine)
    rock = np.array(t.render(CG_SEA_ROCK).convert('RGB'))
    seab = np.zeros((32, 32, 3), np.uint8)
    for r in (0, 1):
        for c in (0, 1):
            seab[r * 16:(r + 1) * 16, c * 16:(c + 1) * 16] = np.array(t.render(CG_SEA[r][c]).convert('RGB'))
    sea_cols = {tuple(int(v) for v in c) for c in seab.reshape(-1, 3)}
    rock_land = np.zeros((PX, PX, 4), np.uint8)
    keep = np.array([[tuple(int(v) for v in p) not in sea_cols and tuple(int(v) for v in p) != FOAM for p in row] for row in rock])
    rock_land[keep, :3] = rock[keep]; rock_land[keep, 3] = 255
    # the town's sea behind the rock is clear: the rock and its foam stand on the route's own sea
    rock_sea = np.zeros((PX, PX, 4), np.uint8)
    keep_s = np.array([[tuple(int(v) for v in p) not in sea_cols for p in row] for row in rock])
    rock_sea[keep_s, :3] = rock[keep_s]; rock_sea[keep_s, 3] = 255
    # One rock per HGSS sea boulder, on the cell nearest the boulder's own centre (HGSS's sea_rock pieces).
    from scipy.ndimage import label as _lb, center_of_mass
    mz = np.load(SRC / 'hgss/hgss-ground-materials.npz')
    names = [str(n) for n in mz['names']]
    m = np.isin(mz['material'], [names.index(n) for n in ('sea_rock', 'sea_rock_m') if n in names])
    lab, n = _lb(m)
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    placed, used = [], set()
    for i in range(1, n + 1):
        if (lab == i).sum() < 24:
            continue
        cy, cx = center_of_mass(lab == i)
        x, y = int(cx // PX) + COL0, int(cy // PX) + ROW0
        if grid[y][x] not in 'O~' or (x, y) in used:
            cand = [(abs(a - x) + abs(b - y), a, b) for b in range(y - 1, y + 2) for a in range(x - 1, x + 2)
                    if 0 <= a < W and 0 <= b < H and grid[b][a] == 'O' and (a, b) not in used]
            if not cand:
                continue
            _, x, y = min(cand)
        used.add((x, y))
        reg = art[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX]
        mm = rock_sea[..., 3] > 0
        reg[mm] = rock_sea[mm]
        placed.append(dict(kind='sea', xy=[x * PX, y * PX], hgss_centre=[round(float(cx), 1), round(float(cy), 1)]))
    for b in land_boulders():
        art[b['xy'][1]:b['xy'][1] + b['art'].shape[0], b['xy'][0]:b['xy'][0] + b['art'].shape[1]][b['art'][..., 3] > 0] = b['art'][b['art'][..., 3] > 0]
        placed.append(dict(kind='land', xy=b['xy']))
    Image.fromarray(art).save(LOCAL / 'boulders.png')
    return art, placed

def land_boulders():
    """HGSS's two land boulders (rock01), cut from its render at their own place, on the 16 px grid."""
    from scipy.ndimage import label, find_objects
    gnd = np.array(Image.open(SRC / 'hgss/hgss-ground.png').convert('RGB'))
    mz = np.load(SRC / 'hgss/hgss-ground-materials.npz')
    names = [str(n) for n in mz['names']]
    m = mz['material'] == names.index('rock01')
    lab, n = label(m)
    out = []
    for i, sl in enumerate(find_objects(lab), 1):
        k = lab[sl] == i
        if k.sum() < 24:
            continue
        spr = np.zeros(k.shape + (4,), np.uint8)
        spr[k, :3] = gnd[sl][k]; spr[k, 3] = 255
        y0, x0 = sl[0].start, sl[1].start
        out.append(dict(xy=[int(round(x0 / 16)) * 16 + COL0 * PX, int(round(y0 / 16)) * 16 + ROW0 * PX], art=spr))
    return out

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
    m &= gnd.astype(int).sum(-1) < 240                   # the opening itself, not the texture's rock rim
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    a = art[ROW0 * PX:, COL0 * PX:]
    a[m, :3] = gnd[m]; a[m, 3] = 255
    Image.fromarray(art).save(LOCAL / 'cave-mouth.png')
    return art

# --------------------------------------------------------------------------- viaduct
VIADUCT_RAIL = 8                     # px of guard rail along each edge of the deck

CYCLING_ROAD = dict(layout='Route110', col=21, rows=range(29, 34))   # Emerald's elevated Cycling Road, east-west

def viaduct_art(phg, engine):
    """The Magnet Train viaduct: Emerald's own elevated Cycling Road (Route 110, its straight east-west section,
    cell column 21, rows 29-33: guard rail, deck, deck, guard rail, the blue side face), run east-west across
    the route on the footprint of HGSS's viaduct shadow, above the player. Route 110's water around it is
    clear, so Route 32's own ground shows."""
    from tiles import Tileset
    t = Tileset(engine, 'mauville', 'general')
    b = (engine / f"data/layouts/{CYCLING_ROAD['layout']}/map.bin").read_bytes()
    words = np.array(struct.unpack('<%dH' % (len(b) // 2), b)).reshape(-1, 40)
    strip = np.concatenate([np.array(t.render(int(words[r, CYCLING_ROAD['col']]) & 1023).convert('RGB')) for r in CYCLING_ROAD['rows']])
    water = {tuple(int(v) for v in c) for c in np.array(t.render(int(words[27, CYCLING_ROAD['col']]) & 1023).convert('RGB')).reshape(-1, 3)}
    y0, y1 = VIADUCT_PX
    h = y1 - y0
    assert strip.shape[0] == 80 and h == 80, (strip.shape, h)
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    for x in range(W * PX):
        col = strip[:, x % PX]
        clear = np.array([tuple(int(v) for v in c) in water for c in col])
        art[y0:y1, x, :3] = col
        art[y0:y1, x, 3] = np.where(clear, 0, 255)
    Image.fromarray(art[y0:y1]).save(LOCAL / 'viaduct.png')
    return art

# --------------------------------------------------------------------------- tall grass
TALL_MARGIN = 1                      # px of lawn left on an open side of a tall-grass cell (the catalog's is 4)

def tall_grass_set():
    """The catalog's 16 tall-grass pieces (mask 8 north, 4 south, 2 west, 1 east), made to fill their cell: on
    each open side the piece's own blades and rounded outline are drawn out from its 4 px margin to
    TALL_MARGIN px of the edge (nearest-pixel resample of that half of the piece), and every other clear pixel
    takes the blade pixel beside it, so lawn shows only round the outside of a patch, never inside it."""
    src = [rgba(SHARED / f'tall-grass/G{m:02d}.png') for m in range(16)]
    out = []
    for m, a in enumerate(src):
        n_open, s_open, w_open, e_open = not m & 8, not m & 4, not m & 2, not m & 1
        ys0, ys1 = np.nonzero(a[..., 3].any(1))[0][[0, -1]]
        xs0, xs1 = np.nonzero(a[..., 3].any(0))[0][[0, -1]]
        def remap(i, lo_open, hi_open, c0, c1):
            # destination index -> source index along one axis
            if i < 8 and lo_open:
                if i < TALL_MARGIN:
                    return None
                return int(round(c0 + (i - TALL_MARGIN) * (8 - c0) / (8 - TALL_MARGIN)))
            if i >= 8 and hi_open:
                if i > 15 - TALL_MARGIN:
                    return None
                return int(round(8 + (i - 8) * (c1 - 8) / (7 - TALL_MARGIN)))
            return i
        b = np.zeros_like(a)
        for y in range(16):
            sy = remap(y, n_open, s_open, ys0, ys1)
            if sy is None:
                continue
            for x in range(16):
                sx = remap(x, w_open, e_open, xs0, xs1)
                if sx is not None:
                    b[y, x] = a[min(sy, 15), min(sx, 15)]
        # Only the margin outside the outline on an open side stays clear; every other clear pixel (the gaps
        # between blade bases, which on a joined side would show lawn between two cells) takes the grass beside it.
        al = b[..., 3] > 0
        keep_clear = np.zeros((16, 16), bool)
        for x in range(16):
            col = np.nonzero(al[:, x])[0]
            if n_open:
                keep_clear[:col[0] if len(col) else 16, x] = True
            if s_open:
                keep_clear[(col[-1] + 1) if len(col) else 0:, x] = True
        for y in range(16):
            row = np.nonzero(al[y])[0]
            if w_open:
                keep_clear[y, :row[0] if len(row) else 16] = True
            if e_open:
                keep_clear[y, (row[-1] + 1) if len(row) else 0:] = True
        for _ in range(16):
            al = b[..., 3] > 0
            todo = ~al & ~keep_clear
            if not todo.any():
                break
            for y, x in zip(*np.nonzero(todo)):
                for dy, dx in ((1, 0), (0, -1), (0, 1), (-1, 0)):
                    if 0 <= y + dy < 16 and 0 <= x + dx < 16 and al[y + dy, x + dx]:
                        b[y, x] = b[y + dy, x + dx]; break
        out.append(b)
    sheet = np.zeros((16, 16 * 18, 4), np.uint8)
    for m, b in enumerate(out):
        sheet[:, m * 18:m * 18 + 16] = b
    Image.fromarray(sheet).save(LOCAL / 'tall-grass-set.png')
    return out

# --------------------------------------------------------------------------- stairs, ledges
def stair_flights(grid):
    """HGSS's stair cells as flights. A run along a row (the flight down a south face) is a straight flight; a
    flight across a wall (rock above and below it) is one diagonal flight per column, each column's own rows
    (reference.py stacks a wide one, each lower column a row further south). Returns
    [(kind, x, y, length, falls)] with kind 'row' or 'column' and falls 'E'/'W' for a column."""
    g = lambda x, y: grid[y][x] if 0 <= x < W and 0 <= y < H else '#'
    rock = lambda x, y: g(x, y) in 'RX'
    out, seen = [], set()
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
            xs = sorted({c[0] for c in comp})
            cols = {x: sorted(y for cx, y in comp if cx == x) for x in xs}
            if all(rock(x, cols[x][0] - 1) and rock(x, cols[x][-1] + 1) for x in xs):
                tops = [cols[x][0] for x in xs]
                falls = 'E' if tops[-1] > tops[0] or (tops[-1] == tops[0] and g(xs[0] - 1, cols[xs[0]][0]) in 'dD') else 'W'
                out += [('column', x, cols[x][0], len(cols[x]), falls) for x in xs]
            else:
                ys = sorted({c[1] for c in comp})
                out += [('row', xs[0], y, len(xs), 'S') for y in ys]
    return out

# HGSS Route 32's flight in the route's palette (sampled from it converted): its plank stripes across a column,
# the treads' dark top edge, and its rails top to bottom (outline, light edge, body, shade, outline).
TREAD_STRIPES = [(152, 144, 120), (168, 168, 144), (168, 168, 144), (152, 144, 120), (88, 80, 48)]
TREAD_EDGE, TREAD_PX = (88, 80, 48), 30
TOP_RAIL = [(82, 58, 52), (198, 148, 115), (165, 115, 99), (165, 115, 99), (99, 70, 66), (82, 58, 52)]
BOTTOM_RAIL = [(82, 58, 52), (165, 115, 99), (198, 148, 115), (165, 115, 99), (99, 70, 66), (82, 58, 52)]

def stairs(grid):
    """A straight flight (down a south face) is the catalog's S01, S02 ... S02, S03 across its row, opaque, as
    Route 45 draws it. A flight across a wall is HGSS's, drawn on its diagonal over the cliff it cuts through
    (upper layer): rails and treads as straight parallel bands, a wider flight stacked one row per column so the
    bands run on unbroken. Returns (straight bottom art, diagonal upper art, placements)."""
    straight = np.zeros((H * PX, W * PX, 4), np.uint8)
    diagonal = np.zeros((H * PX, W * PX, 4), np.uint8)
    placed = []
    fl = stair_flights(grid)
    columns = [f for f in fl if f[0] == 'column']
    for kind, x, y, n, face in fl:
        if kind == 'row':
            for k in range(n):
                name = 'S01' if k == 0 else 'S03' if k == n - 1 else 'S02'
                straight[y * PX:(y + 1) * PX, (x + k) * PX:(x + k + 1) * PX] = rgba(SHARED / f'stairs/{name}.png')
                placed.append(dict(cell=[x + k, y], art=name, flight='north-south'))
    # Each flight across a wall: HGSS's flight, drawn as one clean unit over every column it crosses: a top rail,
    # the treads and a bottom rail, straight parallel bands on HGSS's diagonal (one pixel down per pixel toward
    # the low side, so a stacked column one row lower continues the same lines), each the full width of its
    # column. Colours: HGSS's plank stripes (the lifted flight's own, per pixel across) and its rails in the rock
    # ramp. Above the top rail and below the bottom rail the cliff shows, behind each rail's dark outline.
    for kind, x, y, n, face in columns:
        for xx in range(PX):
            dy = xx if face == 'E' else PX - 1 - xx
            top = y * PX + dy                               # first tread row in this pixel column
            bands = [(top - len(TOP_RAIL) + k, c) for k, c in enumerate(TOP_RAIL)]
            bands += [(top + k, TREAD_EDGE if k == 0 else TREAD_STRIPES[(x * PX + xx) % len(TREAD_STRIPES)]) for k in range(TREAD_PX)]
            bands += [(top + TREAD_PX + k, c) for k, c in enumerate(BOTTOM_RAIL)]
            for Y, c in bands:
                if 0 <= Y < H * PX:
                    diagonal[Y, x * PX + xx, :3] = c; diagonal[Y, x * PX + xx, 3] = 255
        placed.append(dict(cell=[x, y], rows=n, art='HGSS flight, rails and treads on the diagonal', flight='east-west'))
    Image.fromarray(np.maximum(straight, diagonal)).save(LOCAL / 'stairs.png')
    return straight, diagonal, placed

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

SEA_TONES, PIER_TONES, BOULDER_TONES, CAVE_TONES, ISLET_TONES = 15, 6, 4, 2, 8
LAND_BOULDER_TONES = 4
VIADUCT_TONES = 4
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
    road_cap(bottom)
    return ids

CAP = [(0x80, 0x88, 0x78), (0xd8, 0xb8, 0x80), (0xe0, 0xc8, 0x80), (0xb8, 0xa8, 0x80)]   # Violet's verge, outside in

def road_cap(bottom):
    """Row 5 (route art, not Violet's ids): Violet's cobble road ends in a rounded cap of its own verge tones,
    lawn below, instead of stopping square at HGSS row 0."""
    y0 = (ROW0 - 1) * PX
    cell = bottom[y0:y0 + PX].astype(int)
    lawn_c = np.array((104, 208, 152))
    lawn = np.abs(cell - lawn_c).sum(-1) < 24
    cols = np.nonzero(~lawn[0])[0]
    L, R = int(cols.min()), int(cols.max()) + 1
    out = cell.copy()
    bot, rad = 11, 4
    for yy in range(PX):
        for xx in range(L, R):
            cx = min(max(xx + 0.5, L + rad), R - rad)
            if yy + 0.5 <= bot + 1 - rad:
                continue                                  # straight part: Violet's own road and verge
            dist = rad - np.hypot(xx + 0.5 - cx, yy + 0.5 - (bot + 1 - rad))
            if dist < 0:
                out[yy, xx] = lawn_c if lawn[min(yy, PX - 1), max(L - 2, 0)] else cell[yy, max(L - 2, 0)]
            elif dist < len(CAP):
                out[yy, xx] = CAP[int(dist)]
    bottom[y0:y0 + PX] = out.astype(np.uint8)

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
    bottom, mat, tex = paint_paths(grid, ncells, q)
    pad_ids = padding(engine, bottom)
    # The sea and the pier (HGSS's pixels, one exemplar per configuration), into the ground.
    sea, smask, pier, pmask, sea_x = sea_and_pier(phg, grid, engine)
    seamask = np.repeat(np.repeat(smask, PX, 0), PX, 1)
    piermask = np.repeat(np.repeat(pmask, PX, 0), PX, 1)
    sea = np.dstack([sea, np.full(sea.shape[:2], 255, np.uint8)]); pier = np.dstack([pier, np.full(pier.shape[:2], 255, np.uint8)])
    # The sea first; the water at a pier cell's edges is the same sea and takes the same tones; then the planks
    # keep PIER_TONES of their own.
    m_sea = reduce_tones([sea[seamask][None]], keep=set(), n=SEA_TONES)
    sea, pier = apply_tones(sea, m_sea)[..., :3], apply_tones(pier, m_sea)
    sea_cols = {tuple(c) for c in sea[seamask][:, :3].tolist()}
    # water inside a pier cell (the rounded corners) keeps two tones: the foam and the sea's main tone; the wood
    # keeps PIER_TONES of the pier repeat's own (Cherrygrove's six)
    pcols = {tuple(c) for c in pier[piermask][:, :3].tolist()} - sea_cols
    from collections import Counter as _C
    main = _C(map(tuple, sea[seamask][:, :3].tolist())).most_common(1)[0][0]
    foam_n = min(sea_cols, key=lambda c: sum((a - b) ** 2 for a, b in zip(c, FOAM)))
    sea_arr = np.array([main, foam_n], int); lab_s = _lab(sea_arr)
    wet_map = {c: tuple(int(v) for v in sea_arr[int(np.argmin(np.linalg.norm(lab_s - _lab(np.array([c]))[0], axis=1)))])
               for c in pcols if c[2] > c[0] + 20 and c[2] >= c[1] - 10}
    pier = apply_tones(pier, wet_map)
    keep_p = sea_cols | {tuple(int(v) for v in c) for c in Rk.ROCK_RAMP}
    pier = apply_tones(pier, reduce_tones([pier[piermask][None]], keep=keep_p, n=PIER_TONES))[..., :3]
    bottom[seamask] = sea[seamask]
    bottom[piermask] = pier[piermask]
    # the plain water under a rock piece's clear pixels: the sea's own pattern at that spot (the full canvas, so
    # the 2x2 block keeps its phase and no beach foam comes with it)
    water_block = sea
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
    pillar_cells = set(islet_cells)                   # the islets' own rock cells; boulders stay sea rocks
    for x, y in pillar_cells:                          # an islet is rock standing out of the sea
        ncells[y][x] = dict(ncells[y][x], lab='R', ground=1.0, peak=3.0, top=3.0, floor='water')
    for y in range(H):                                 # the cave mouth is cut into the rock face: it terraces as rock
        for x in range(W):
            if grid[y][x] == 'C':
                ncells[y][x] = dict(ncells[y][x], lab='R')
    # Levels counted from HGSS's own heights, one per height unit, contiguous round every mass (levels.py).
    import levels as Lv
    d, isrock = Lv.levels(Rf.topdown(phg), grid, cells, ROW0, Rf.WALLS + ('slope',))
    for y in range(H):
        for x in range(W):
            if isrock[y, x]:
                ncells[y][x] = dict(ncells[y][x], lab='R')
            elif ncells[y][x]['lab'] == 'R':
                ncells[y][x] = dict(ncells[y][x], lab='X')
    (OUT / 'levels.json').write_text(json.dumps(dict(levels=d.tolist(), audit=Lv.audit(d, isrock))) + '\n')
    # A diagonal flight's cells are part of the cliff it cuts through: the cliff is drawn on under it, unbroken,
    # at the flight's levels (the wall's own, levels.py), and the flight lies over it (Route 45).
    draw_rock = isrock.copy()
    for kind, x, y, n, face in stair_flights(grid):
        if kind == 'column':
            for k in range(n):
                draw_rock[y + k, x] = True
                ncells[y + k][x] = dict(ncells[y + k][x], lab='R')
    plain_tex = dict(grass=tex[G.GRASS], sand=tex[G.PATH], water=water_block)
    bottom, rock_over, piece = Rk.rock_frlg(ncells, d, draw_rock, bottom, Rk.frlg_pieces(engine), plain_tex, soft=True)
    flat = np.zeros((H * PX, W * PX, 4), np.uint8)
    flat_owner = np.full((H * PX, W * PX), '', object)
    def lay(art, name):
        a = art[..., 3] > 0
        flat[a] = art[a]; flat_owner[a] = name
    light, flw = light_lawn(phg), flowers(phg)
    flw, light = local(flw, FLOWER_TONES), local(light, LIGHT_TONES)
    # Tall grass: the catalog's 16-piece set by neighbour mask (8 north, 4 south, 2 west, 1 east), so each patch
    # rounds off on every side that is not tall grass and the lawn (or the beach edge at the water) shows round it.
    gset = tall_grass_set()
    g15 = gset[15]
    tall = lambda x, y: not (0 <= x < W and 0 <= y < H) or grid[y][x] == 'G'
    tg = np.zeros_like(flat); n_g15 = 0
    for y in range(H):
        for x in range(W):
            if grid[y][x] == 'G':
                m = 8 * tall(x, y - 1) + 4 * tall(x, y + 1) + 2 * tall(x - 1, y) + tall(x + 1, y)
                tg[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX] = gset[m]; n_g15 += 1
    la, ledge_list = ledges(grid)
    # Stairs: S01-S03 straight (Route 45's); a flight across a wall HGSS's own, stacked, in the route's palette.
    sa, sdiag, stair_list = stairs(grid)
    ba, boulder_list = boulders([[('~' if (x, y) in pillar_cells else ch) for x, ch in enumerate(row)] for y, row in enumerate(grid)], sea_x, engine)
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
    lb = land_b.copy()                                  # land boulders are rock: each tone the nearest of the Johto rock ramp
    ramp = np.array(Rk.ROCK_RAMP, int); lr = _lab(ramp)
    m_ = lb[..., 3] > 0
    if m_.any():
        px_ = lb[m_][:, :3].astype(int)
        lb_new = ramp[np.argmin(((_lab(px_)[:, None] - lr[None]) ** 2).sum(-1), 1)]
        sub = lb[m_]; sub[:, :3] = lb_new; lb[m_] = sub
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
    lay(sdiag, 'stairs')                                 # the diagonal flights over their cliff
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
    va = viaduct_art(phg, engine)
    va = local(va, VIADUCT_TONES)                      # the Cycling Road deck in its six most distinct tones (bank budget)
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

GROUND_SNAP = 1                      # px: a ground 8x8 tile this close to one already drawn becomes that tile

def snap_ground_tiles(bottom, flat, top):
    """Tile budget: palette reduction and texture phases leave many ground 8x8 tiles one pixel apart from
    another; each costs a tile. Every ground-only tile (nothing of the upper layers over it; Violet's padding
    rows untouched) that differs from an earlier one, flips included, in at most GROUND_SNAP pixels becomes
    that tile."""
    out = bottom.copy()
    over = (flat[..., 3] > 0) | (top[..., 3] > 0)
    book, keys, n = [], {}, 0
    for ty in range(ROW0 * 2, out.shape[0] // 8):
        for tx in range(out.shape[1] // 8):
            sl = np.s_[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            if over[sl].any():
                continue
            t = out[sl]
            k = (t >> 3).tobytes()
            if k in keys:
                continue
            f5 = [(v >> 3).astype(np.int16) for v in (t, t[:, ::-1], t[::-1], t[::-1, ::-1])]
            hit = None
            if book:
                B = np.stack([b for b, _ in book])
                for fi, v in enumerate(f5):
                    d = (B != v[None]).any(-1).sum((1, 2))
                    j = int(np.argmin(d))
                    if 0 < d[j] <= GROUND_SNAP:
                        hit = (j, fi); break
            if hit is None:
                book.append(((t >> 3).astype(np.int16), t.copy())); keys[k] = True
            else:
                j, fi = hit
                src = book[j][1]
                out[sl] = (src, src[:, ::-1], src[::-1], src[::-1, ::-1])[fi]
                n += 1
    return out, n

def main(phg, catalog, engine):
    for d in (OUT, OEV, LOCAL, SHARED):
        d.mkdir(parents=True, exist_ok=True)
    stage_shared(catalog)
    r = compose(phg, engine)
    r['bottom'], n_snapped = snap_ground_tiles(r['bottom'], r['flat'], r['top'])
    print('ground tiles snapped', n_snapped)
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
