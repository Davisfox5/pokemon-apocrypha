"""Route 45: native art assembled under docs/GBA_MAP_RECONSTRUCTION.md, by the process the
owner accepted for Mahogany Town, Route 43, Lake of Rage, Route 44 and Route 42.

    python3 tools/gba/maps/route45/assemble.py PHG_CHECKOUT CATALOG_CHECKOUT ENGINE_CHECKOUT

1. Reference: trace.py registers decoded HGSS land_data chunks 108-112 to native cells 1:1
   (numbered sheets, material grid, traversal ledger); elements.ledger decodes them flat, cell
   by cell, and labels the stairs, the Dark Cave mouth and the bridge decks.
2. Rock, as Blackthorn's installed rock: every HGSS height layer is one terrace
   (source/assemble/terrace-grid.txt), drawn with FRLG General's mountain nine-slice,
   over-rock pieces and inner corners in the Johto rock ramp, one face per metatile, as a
   top-layer overlay on plain ground (elements.rock_frlg). The Dark Cave mouth is FRLG
   General's cave mouth, as Blackthorn's Dragon's Den is; the boulders are FRLG General's
   boulder (AGENTS.md: reuse rock art).
3. Shared art, copied unchanged with hashes into source/shared-art/ from the Johto catalog
   (CATALOG_CHECKOUT is a checkout of branch codex/violet-city):
     ground      the accepted Cherrygrove/Route 36 painter (claude_cherrygrove/ground.py), run on
                 an 8 px lawn/road grid read from HGSS's own flat ground colours
     tall grass  G15, the whole-cell tall grass piece, on every HGSS tall-grass cell
     stairs      S01-S03, the catalog's straight flight (west end, middle, east end), on HGSS's
                 flights down a south face; S04 and S05, its diagonal flights descending west
                 and east, on HGSS's flights down a west or east face
     trees       T01 on one regular lattice of 2x2 roots per woods block (elements.tree_footprints)
     signs       P14 green rounded sign (HGSS model 32), P13 grey plaque (model 31)
4. Blackthorn's own art: the river and pond are CherrygrovePrimary's animated sea, Blackthorn's
   lake water, inside the natural bank the owner approved on Route 43 (water()); the bridges
   are Blackthorn's plank bridge in CherrygrovePrimary's wood ramp, turned to run east-west
   (bridges()).
5. Local assets, HGSS's own pixels lifted from the decoded true-heights render: the flower
   patches (flower01-03, every pixel that is not lawn green), Route 46's red dirt at the west
   edge (road05) and the three cascades (cascades(); Gen 3 has no short drop, and Emerald's
   waterfall reads as flat bands without its animation).
6. The Blackthorn seam: Route 45 joins Blackthorn City by a map connection, and a Gen 3
   connection draws the neighbour with the current map's tilesets. The part of Route 45
   Blackthorn's tilesets ever draw (views()) is built from Blackthorn's own metatiles where it
   can be (pack_fixed.py proves it).

Writes source/assemble/layers.npz (ground RGB with water, bridges, stairs and the dirt, rock
RGBA with the boulders and the cave mouth, objects RGBA, object owner, terrace levels),
placements.json, terrace-grid.txt, evidence/assemble/*.png.
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
ART = ROOT / 'gba/art/route-45'
SRC, EV = ART / 'source', ART / 'evidence'
TRACE, SHARED, LOCAL = SRC / 'trace', SRC / 'shared-art', SRC / 'local-art'
OUT, OEV = SRC / 'assemble', EV / 'assemble'
W, H = 32, 160
PX = 16

CATALOG = {  # local name -> catalog path (branch codex/violet-city)
    'T01.png': 'gba/art/johto-common/trees/source/T01.png',
    'P13.png': 'gba/art/johto-common/scenery/source/P13.png',
    'P14.png': 'gba/art/johto-common/scenery/source/P14.png',
    'G15.png': 'gba/art/johto-common/scenery/source/G15.png',
    **{f'S0{i}.png': f'gba/art/johto-common/scenery/source/S0{i}.png' for i in range(1, 6)},
}
# The approved painter's rim wave (claude_cherrygrove/ground.WAVE, +-2 px over 32 px) taken every
# other pixel, so it runs over 16 px; with the lawn and road each one 16 px quarter of Cherrygrove's
# 32 px block, every lawn edge repeats from cell to cell. Route 45 is five times Route 42's height,
# and its secondary metatiles run out otherwise.
WAVE16 = [0, 1, 1, 2, 2, 1, 1, 0, 0, -1, -1, -2, -2, -1, -1, 0]
QUARTER = dict(grass=(16, 16), sand=(0, 0))   # the quarter of each Cherrygrove block: the lawn's has no tuft

def quarter(name):
    oy, ox = QUARTER[name]
    return np.tile(TEX[name][oy:oy + 16, ox:ox + 16], (2, 2, 1))

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p): return np.array(Image.open(p).convert('RGBA'))

def stage_shared(catalog):
    """Copy every catalog master used here, unchanged, with its hash and the catalog commit."""
    commit = subprocess.run(['git', '-C', str(catalog), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    prov = dict(catalog=dict(branch='codex/violet-city', commit=commit,
                             rule='Masters copied byte for byte; native tile ids and palette slots may differ, visible colours do not.'))
    for name, rel in CATALOG.items():
        dst = SHARED / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(catalog / rel, dst)
        prov[name] = dict(source=rel, sha256=sha(dst))
    (SHARED / 'provenance.json').write_text(json.dumps(prov, indent=2) + '\n')

# --------------------------------------------------------------------------- ledger
DIRT = ('road05', 'road05_sub')             # Route 46's red dirt, where it reaches Route 45's west edge
ROCK_BASE = 2                               # HGSS height of Route 45's lowest ground (by the river's mouth)
CASCADE_ROWS = E.CASCADE_ROWS

is_water = E.is_river

def boulder_cells():
    """The cells HGSS's boulders (rock01) stand on: a quarter of a cell's pixels or more."""
    z = np.load(SRC / 'hgss/hgss-ground-materials.npz')
    m = z['material'] == list(z['names']).index('rock01')
    return m.reshape(H, PX, W, PX).sum(axis=(1, 3)) >= 32

def unboulder(cells):
    """HGSS reads each boulder's 2x2 footprint as a little cliff. Here a boulder is one object
    (compose), so its cells take the ground round it: the rock top it sits on, at that rock's
    height, or the lawn or road about it. Collision stays HGSS's (pack.traversal)."""
    bc = boulder_cells()
    out = [list(row) for row in cells]
    for y, x in zip(*np.nonzero(bc)):
        near = [cells[ny][nx] for ny in range(y - 1, y + 2) for nx in range(x - 1, x + 2)
                if 0 <= ny < H and 0 <= nx < W and not bc[ny, nx]]
        rock = [c for c in near if c['lab'] in E.ROCK]
        water = [c for c in near if is_water(c)]
        ground = [c for c in near if c not in rock and c not in water]
        kind = max((len(rock), 'rock'), (len(water), 'water'), (len(ground), 'ground'))[1]
        c = cells[y][x]
        if kind == 'rock':
            row = [cells[y][nx] for nx in range(x - 3, x + 4) if 0 <= nx < W and not bc[y, nx] and cells[y][nx]['lab'] in E.ROCK]
            out[y][x] = dict(c, lab='T', peak=float(np.median([n['peak'] for n in (row or rock)])), boulder=True)
        else:
            pool = water if kind == 'water' else ground
            floors = [n['floor'] for n in pool]
            out[y][x] = dict(c, lab='.', floor=max(set(floors), key=floors.count), boulder=True)
    return out

def flights(cells):
    """HGSS's stair flights (ledger label s): runs along a row are straight flights down a
    south face (S01-S03), runs down a column are diagonal flights down the face either side
    of them (S04 descending west, S05 east). Returns [(kind, x, y, length, face)]."""
    s = np.array([[c['lab'] == 's' for c in row] for row in cells])
    seen, out = np.zeros_like(s), []
    for y in range(H):
        for x in range(W):
            if not s[y, x] or seen[y, x]:
                continue
            n = 0
            while x + n < W and s[y, x + n]:
                n += 1
            if n > 1:
                seen[y, x:x + n] = True
                out.append(('row', x, y, n, 'S'))
                continue
            m = 0
            while y + m < H and s[y + m, x]:
                m += 1
            seen[y:y + m, x] = True
            above = cells[y - 1][x]['lab'] if y else ''
            below = cells[y + m][x]['lab'] if y + m < H else ''
            face = above if above in 'WE' else below if below in 'WE' else 'W'
            if (x, y) in E.RIVER_STAIRS:
                face = 'W'                                  # the landing's flight, down the bank's west face
            out.append(('column', x, y, m, face))
    return out

def rock_cells(cells):
    """The ledger for the rock pass: the Dark Cave mouth is a face cell of the cliff it is cut
    into (FRLG's cave mouth goes over the face), and every stair cell is part of the cliff it
    cuts through, so the cliff runs on unbroken and the flight goes over it (stairs()). The
    signs' cells, which HGSS blocks for their models, are ground under the sign. The cells the
    owner review made ground (elements.OWNER_GROUND) are that ground (owner_ground).
    Floors: water for the river, the pond and the blocked river cells by the bridges, bridge
    for the decks, dirt for Route 46's red dirt."""
    fl = {(x + (k if kind == 'row' else 0), y + (0 if kind == 'row' else k)): face
          for kind, x, y, n, face in flights(cells) for k in range(n)}
    out = []
    for row in unboulder(cells):
        r = []
        for c in row:
            if c['lab'] == 'D':
                c = dict(c, lab='S')
            elif (c['x'], c['y']) in SIGNS and c['lab'] in E.ROCK:
                c = dict(c, lab='.')                  # a sign's own cell: HGSS blocks it for the model, it is road
            elif c['lab'] == 's':
                c = dict(c, lab=fl[(c['x'], c['y'])], stair=True)
            if (c['x'], c['y']) in E.OWNER_GROUND:
                c = owner_ground(cells, c)
            if is_water(c):
                c = dict(c, floor='water')
            elif c['lab'] == 'b':
                c = dict(c, floor='bridge')
            elif c['material'] in DIRT and c['lab'] not in E.ROCK:
                c = dict(c, floor='dirt')
            r.append(c)
        out.append(r)
    return out

def owner_ground(cells, c):
    """An HGSS cliff cell the owner review made walkable ground (elements.OWNER_GROUND): road
    beside the row 47 ledge's east end, the lawn shore at the river's foot, the road where the
    Surf route lands below Blackthorn. It takes the height of the nearest walkable ground."""
    x, y = c['x'], c['y']
    near = sorted((abs(dx) + abs(dy), cells[y + dy][x + dx]['ground']) for dx in range(-2, 3) for dy in range(-2, 3)
                  if 0 <= x + dx < W and 0 <= y + dy < H and cells[y + dy][x + dx]['lab'] == '.')
    return dict(c, lab='.', floor=E.OWNER_GROUND[(x, y)], ground=near[0][1], owner_ground=True)

def south_faces(cells, d, rock, north):
    """Rock cells whose slope falls north (to a lower rock step) with walkable ground south of
    them, off the river: drawn as a face looking south onto that ground (elements.rock_frlg),
    so no strip of rock floor lies beside a road (owner review, 2026-10-26). The river's own
    south banks face the river instead (north_faces)."""
    out = set()
    for y in range(1, H - 1):
        for x in range(W):
            s_ = cells[y + 1][x]
            if (rock[y, x] and (x, y) not in north and not cells[y][x].get('stair') and d[y - 1, x] < d[y, x]
                    and not rock[y + 1, x] and s_['floor'] in ('grass', 'sand', 'dirt') and s_['lab'] not in 'LJQ'):
                out.add((x, y))
    return out

def north_faces(cells, d, rock):
    """The river's south banks (owner review, 2026-10-27: the east-west walls along the river
    face the water): rock cells whose slope falls north to the river, straight or down a lower
    bank cell that does, drawn as a face looking north onto the water (elements.rock_frlg, FRLG's
    south face turned to look north), so the valley's walls face the river from both sides; and
    the cells where such a wall turns into a side wall (only a diagonal neighbour north of them
    lower, and on the bank), drawn with the inner corner turned the same way."""
    wet = lambda x, y: 0 <= x < W and 0 <= y < H and cells[y][x]['floor'] == 'water'
    out = set()
    for y in range(1, H):
        for x in range(W):
            if not rock[y, x] or cells[y][x].get('stair'):
                continue
            on_bank = lambda nx: wet(nx, y - 1) or (nx, y - 1) in out
            if d[y - 1, x] < d[y, x]:
                if on_bank(x):
                    out.add((x, y))
            elif not any(0 <= x + dx < W and 0 <= y + dy < H and d[y + dy, x + dx] < d[y, x]
                         for dx, dy in ((1, 0), (0, 1), (-1, 0))):
                if any(0 <= x + dx < W and d[y - 1, x + dx] < d[y, x] and on_bank(x + dx) for dx in (-1, 1)):
                    out.add((x, y))
    return out

def with_xy(cells):
    return [[dict(c, x=x, y=y) for x, c in enumerate(row)] for y, row in enumerate(cells)]

def level(v):
    """An HGSS height as a terrace level above Route 45's lowest ground (half-up rounding)."""
    return int(np.floor(v + 0.5)) - ROCK_BASE

def terraces(cells):
    """Every HGSS height layer is one Gen 3 terrace, the ground's as well as the rock's. A rock
    cell (ledger label T, E, S, W or N: HGSS's cliff cells, decoded flat) stands at its rock
    peak, every other cell at its own ground height (a bridge deck at its deck, water at its
    surface, rounded down), all counted from Route 45's lowest ground (ROCK_BASE). So every HGSS
    step is a wall of its own (AGENTS.md: count the original's wall levels), and a wall has a
    face only toward ground that is really lower: a river bank faces the river, not the road
    level with its top (owner review: the banks read as raised spikes)."""
    lab = np.array([[c['lab'] for c in row] for row in cells])
    rock = np.isin(lab, list(E.ROCK))
    d = np.zeros((H, W), int)
    for y in range(H):
        for x in range(W):
            c = cells[y][x]
            if rock[y, x]:
                d[y, x] = level(c['peak'])
            elif c['floor'] == 'water':
                d[y, x] = int(np.floor(c['level'])) - ROCK_BASE
            else:
                d[y, x] = level(c['ground'])
    d = np.maximum(d, 0)
    pad = np.pad(d, 1, mode='edge')
    lower = np.zeros((H, W), bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                lower |= pad[1 + dy:1 + dy + H, 1 + dx:1 + dx + W] < d
    return d, rock & lower, rock

def topped(cells, d, rock, north=()):
    """Wall cells whose top is the ground beside them: a rock cell showing a face (a lower
    neighbour south, alone or with one east or west), not on the river (a bank stays rock), with a lawn, road or
    dirt neighbour (north, east, south or west) at its own level or above. Returns {cell: that
    ground's class}, the highest such neighbour's, lawn or road as the painter drew that cell
    (compose sets each floor from GROUND_CLASS), so a wall by tall grass is topped with lawn
    (elements.rock_frlg draws the wall's top as it). A stair's cliff keeps its whole face, as on Route 42 (owner review there:
    the flight stands on an unbroken cliff)."""
    out = {}
    for y in range(H):
        for x in range(W):
            if not rock[y, x] or cells[y][x].get('stair') or (x, y) in north:
                continue
            # a river bank stays rock, a regular face down to the water (owner review, 2026-10-26)
            if any(0 <= x + dx < W and 0 <= y + dy < H and cells[y + dy][x + dx]['floor'] == 'water'
                   for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0))):
                continue
            # only a wall that shows a face (lower ground south, or a corner of one); a slope
            # falling north is a back edge in Gen 3, and HGSS shows it as rock, so it keeps its
            # rock top; a side wall (lower ground east or west only) is FRLG's side piece whole,
            # its face band and rock top (owner review, 2026-10-27: a side wall topped with the
            # road read as rock mixed with sand)
            low = {k for k, (dx, dy) in dict(e=(1, 0), s=(0, 1), w=(-1, 0)).items()
                   if 0 <= x + dx < W and 0 <= y + dy < H and d[y + dy, x + dx] < d[y, x]}
            if not low or low in ({'e'}, {'w'}):
                continue
            best = None
            for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < W and 0 <= ny < H) or rock[ny, nx]:
                    continue
                f = cells[ny][nx]['floor']
                if f in ('grass', 'sand', 'dirt') and d[ny, nx] >= d[y, x] and (best is None or d[ny, nx] > best[0]):
                    best = (d[ny, nx], f)
            if best:
                out[(x, y)] = best[1]
    return out

CAVE = (10, 6)                              # HGSS warp 0 into Dark Cave

def frlg_rock(rc, ground, dirt):
    """Blackthorn's installed rock (elements.rock_frlg): FRLG General's mountain nine-slice, its
    over-rock version where an edge drops to a lower terrace, and its four inner corners,
    recoloured to the Johto rock ramp, one face per metatile. The rock is a top-layer overlay;
    under its clear pixels the bottom carries the plainest 8x8 block of the ground beyond the
    edge (Cherrygrove's sea where it is the river), and its cast shadow is Cherrygrove's border
    grey. The jump ledges are FRLG's, in the same ramp (elements.ledges_frlg), and the Dark Cave
    mouth is FRLG's cave mouth on its face, as Blackthorn's Dragon's Den is."""
    d, face, isrock = terraces(rc)
    E.layers = lambda _cells: (d, face, isrock)
    pieces = E.frlg_pieces(ENGINE)
    north = north_faces(rc, d, isrock)
    out, over, _, piece = E.rock_frlg(rc, ground, pieces, TEX, dict(dirt=dirt), topped(rc, d, isrock, north),
                                       south_faces(rc, d, isrock, north), north)
    ledge = E.ledges_frlg(rc, pieces)
    a = ledge[..., 3] > 0
    over[a] = ledge[a]
    x, y = CAVE
    sl = over[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX]
    for (yy, xx), k in np.ndenumerate(pieces['cave']):
        sl[yy, xx] = (E.ROCK_RAMP[k] if k >= 0 else CAVE_DARK if k == E.CAVE_DARK else E.ROCK_RAMP[0] if k == E.CAVE_SILL
                      else E.BORDER_GRAY) + (255,)
    return out, over, d, isrock, piece

CAVE_DARK = (36, 30, 32)                    # Blackthorn's Dragon's Den opening

# --------------------------------------------------------------------------- ground
def paint_ground(q):
    """The accepted Cherrygrove/Route 36 painter (claude_cherrygrove/ground.paint) on an 8 px
    material grid: its own textures, rim profiles, 32 px wobble wave and order, with each
    material square 8 px (ground_quadrants fills it a whole cell at a time), its wave and
    textures repeating every 16 px (WAVE16, QUARTER); its road is Cherrygrove's sand (Blackthorn's)."""
    U = 8
    hq, wq = q.shape
    h, w = hq * U, wq * U
    tex = G.textures()
    # The road is Cherrygrove's own sand, as Blackthorn's is (elements.cherry_textures): the
    # painter's road differs by 14 pixels in a tone CherrygrovePrimary's palettes lack, and the
    # road runs on across the seam into Blackthorn. Lawn and road repeat every 16 px (QUARTER).
    tex[G.GRASS], tex[G.PATH] = quarter('grass'), quarter('sand')
    ys, xs = np.mgrid[0:h, 0:w]
    wave = np.array(WAVE16)
    dx = wave[ys % 16]; dy = wave[(xs + 5) % 16]
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
    """Lawn or road per cell, read per 8 px quadrant from HGSS's own flat ground colours (lawn
    greens against road sand); quadrants HGSS shows too little open ground in keep their cell's
    material. HGSS's woods, tall grass, water and bridge cells are lawn here (the water and
    the decks go over them). Ledge stones are read past: a south ledge cell's lower quadrants
    take the ground above them."""
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
            c = cells[qy // 2][qx // 2]
            if c['lab'] in 'FGb' or is_water(c):
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
    # One material per cell, the painter's own 16 px grid (Cherrygrove, Route 36): a cell is road
    # where most of its quadrants are, lawn where most are lawn, and its own floor on a tie. Route
    # 45 is five times Route 42's height, and lawn edges mid-cell cost more tiles than its
    # secondary tileset holds.
    for y in range(H):
        for x in range(W):
            n = int((q[2 * y:2 * y + 2, 2 * x:2 * x + 2] == G.PATH).sum())
            road = n > 2 or (n == 2 and cells[y][x]['floor'] == 'sand')
            q[2 * y:2 * y + 2, 2 * x:2 * x + 2] = G.PATH if road else G.GRASS
    return q

def plain_lawn(ground, cells, phg):
    """Under G15 (every tall-grass cell) and under a flower patch whose cell and neighbours are
    all lawn, the ground is plain lawn, the same in every such cell: the painter's rim on a
    lawn cell's side of an edge gives way to it (G15 covers all but the odd pixel)."""
    block = quarter('grass')[:16, :16]
    lawn = (ground.reshape(H, PX, W, PX, 3)[..., None, :] == np.array(E.CHERRY['grass'], np.uint8)).all(-1).any(-1).all(axis=(1, 3))
    fl = flowers(phg)[1]
    for y in range(H):
        for x in range(W):
            whole = all(lawn[ny, nx] for ny in range(max(0, y - 1), min(H, y + 2)) for nx in range(max(0, x - 1), min(W, x + 2)))
            if cells[y][x]['lab'] == 'G' or ((x, y) in fl and whole and cells[y][x]['lab'] == '.'):
                ground[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX] = block

def tall_grass(cells):
    """Catalog tall grass on every HGSS tall-grass cell: G15, the whole-cell piece (AGENTS.md)."""
    grass = np.array([[c['lab'] == 'G' for c in row] for row in cells])
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    g15 = rgba(SHARED / 'G15.png')
    for y, x in zip(*np.nonzero(grass)):
        art[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX] = g15
    return art, {'G15': int(grass.sum())}

# --------------------------------------------------------------------------- water
POND_SEED = 45
GRASS_EDGE, GRASS_DARK = (104, 208, 152), (88, 176, 136)       # Cherrygrove lawn tones
MUD, BANK, SHALLOW = (160, 144, 104), (88, 112, 80), (72, 200, 224)   # Route 30's HGSS pond rim tones

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

def water(cells, ground):
    """HGSS's water cells in Blackthorn's lake water (CherrygrovePrimary's animated sea, on its
    32 px phase, which Blackthorn's shares across the seam) inside the natural bank the owner
    approved on Route 43: a rough bank in Route 30's rim tones (mud, dark bank line, shallow
    water), rounded corners, three octaves of seeded value noise along each edge (repeating
    every 64 px), lawn tufts breaking into the mud. The mean shore sits two pixels inside the
    water cells and open water reaches at least 4 px round every water cell's centre, so the
    Surf boundary is the cell edge. Rock standing in the water, and a bridge deck over it, has
    water at its foot (no bank); the rock cells themselves keep the rock pass's plain sea block
    under the rock's clear pixels, as Blackthorn's do."""
    from scipy.ndimage import distance_transform_edt, gaussian_filter
    rng = np.random.default_rng(POND_SEED)
    cellmask = lambda f: np.repeat(np.repeat(np.array([[f(c) for c in row] for row in cells]), PX, 0), PX, 1)
    water_px = cellmask(is_water)
    solid = cellmask(lambda c: c['lab'] in 'TESWNb')
    _, (iy, ix) = distance_transform_edt(solid, return_indices=True)
    wet = water_px | (solid & water_px[iy, ix])
    h, w = wet.shape
    soft = gaussian_filter(wet.astype(float), 5) > 0.5
    d = distance_transform_edt(soft) - distance_transform_edt(~soft)
    gy, gx = np.gradient(d)
    along_x = gy ** 2 / np.maximum(gx ** 2 + gy ** 2, 1e-9)
    nx = sum(a * periodic_noise1(w, 64, st, rng) for a, st in ((2.6, 16), (1.2, 8), (0.5, 4)))
    ny = sum(a * periodic_noise1(h, 64, st, rng) for a, st in ((2.6, 16), (1.2, 8), (0.5, 4)))
    shore = d - 2 + along_x * nx[None, :] + (1 - along_x) * ny[:, None]
    ys, xs = np.mgrid[0:h, 0:w]
    r = np.hypot(ys % PX - (PX - 1) / 2, xs % PX - (PX - 1) / 2)
    shore = np.where(water_px, np.maximum(shore, 4.5 + (4 - r) * 1.5), shore)
    tuft = periodic_noise2(h, w, 32, 4, rng) + 0.5 * periodic_noise2(h, w, 32, 1, rng)
    broken = periodic_noise2(h, w, 32, 8, rng)
    tex = TEX['water']
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
    art[solid] = 0
    art[(art[..., 3] > 0) & (art[..., :3] == ground[..., :3]).all(-1), 3] = 0
    centre = water_px & (ys % PX == PX // 2) & (xs % PX == PX // 2)
    assert (shore[centre] >= 3.2).all(), 'a water cell centre is not open water'
    Image.fromarray(art).save(LOCAL / 'water-banks.png')
    return art

LIP = ((148, 222, 255), (99, 181, 255))     # HGSS's foam blues, lightest first

def cascades(cells, bottom):
    """HGSS's three cascades, its own pixels from the decoded true-heights render (HGSS stands a
    model on the drop row, with no land mesh under it), over the river's cells from half a row
    above the drop row to the foot of the row below: every pixel that is not one of HGSS's river
    texture colours (the falling sheet, its dark lip and the foam), and the light blue foam
    pixels joined to them that share a colour with the texture's sparkle, so the foam runs the
    river's full width as in HGSS. The sheet's top two rows take HGSS's foam blues (LIP), a
    bright lip where the river tips over (owner review). They go over the river's own water. The tones
    merge toward Blackthorn's palettes as the other local pieces do (REDUCE). Surf as HGSS: the
    cells stay river."""
    from scipy.ndimage import label
    ref = np.array(Image.open(SRC / 'hgss/hgss-reference-true-heights.png').convert('RGB'))
    z = np.load(SRC / 'hgss/hgss-ground-materials.npz')
    river = np.isin(z['material'], [list(z['names']).index(n) for n in ('river', 'river_r')])
    for y in CASCADE_ROWS:                                   # the texture away from the cascades
        river[(y - 2) * PX:(y + 3) * PX] = False
    texture = {tuple(c) for c in np.unique(ref[river], axis=0)}
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    out = []
    for y in CASCADE_ROWS:
        xs = [x for x in range(W) if is_water(cells[y][x])]
        x0, x1 = xs[0] * PX, (xs[-1] + 1) * PX
        y0, y1 = y * PX - PX // 2, (y + 2) * PX
        box = ref[y0:y1, x0:x1]
        c = box.astype(int)
        fall = ~np.array([[tuple(v) in texture for v in row] for row in box])
        foam = (c[..., 2] >= 230) & (c[..., 1] >= 170)
        lb, _ = label(fall | foam)
        fall = np.isin(lb, np.unique(lb[fall])) & (lb > 0)
        sub = art[y0:y1, x0:x1]
        sub[fall, :3] = box[fall]; sub[fall, 3] = 255
        # The lip where the river tips over: the sheet's top two rows in HGSS's own foam blues,
        # so the drop starts at a bright edge, not a hard stripe across the water (owner review).
        top = int(np.argmax(fall.any(1)))
        for k, tone in enumerate(LIP):
            row = fall[top + k]
            sub[top + k][row, :3] = tone
        out.append(dict(row=y, cells=[xs[0], xs[-1]]))
    art, merged = reduce_local(art, *(REDUCE['cascades'][0], neighbour_tones(REDUCE['cascades'][1])))
    a = art[..., 3] > 0
    bottom[a] = art[a, :3]
    Image.fromarray(art).save(LOCAL / 'cascades.png')
    return out, merged

# --------------------------------------------------------------------------- bridges
WOOD = [(88, 64, 64), (120, 80, 56), (136, 96, 64), (160, 120, 88), (184, 136, 96), (200, 168, 112)]   # CherrygrovePrimary bank 2

def decks(cells):
    """Each HGSS bridge deck (ledger label b) as its cell box (x0, y0, x1, y1), exclusive."""
    b = np.array([[c['lab'] == 'b' for c in row] for row in cells])
    from scipy.ndimage import label, find_objects
    lb, _ = label(b)
    return [(sl[1].start, sl[0].start, sl[1].stop, sl[0].stop) for sl in find_objects(lb)]

def bridges(bottom, boxes):
    """Blackthorn's plank bridge (blackthorn/elements.bridge) turned to run east-west: boards
    along the river, a beam down each side with a post every 32 px, nail heads by the beams."""
    for cx0, cy0, cx1, cy1 in boxes:
        x0, y0, x1, y1 = cx0 * PX, cy0 * PX, cx1 * PX, cy1 * PX
        for px in range(x0, x1):
            r = (px - x0) % 8
            col = WOOD[4] if r in (0, 1) else WOOD[3] if r in (2, 3, 4) else WOOD[2] if r in (5, 6) else WOOD[1]
            bottom[y0:y1, px] = col
            if r == 3:
                bottom[y0 + 5, px] = WOOD[1]; bottom[y1 - 6, px] = WOOD[1]
            bottom[y0:y0 + 3, px] = (WOOD[0], WOOD[1], WOOD[2])
            bottom[y1 - 3:y1, px] = (WOOD[2], WOOD[1], WOOD[0])
            if (px - x0) % 32 in (0, 1, 2):
                bottom[y0:y0 + 3, px] = WOOD[1]; bottom[y1 - 3:y1, px] = WOOD[1]

# --------------------------------------------------------------------------- HGSS local pieces
def hgss_material(names):
    """HGSS's own pixels of the given materials, from the decoded true-heights render, where no
    HGSS model (a sign) stands over them."""
    z = np.load(SRC / 'hgss/hgss-ground-materials.npz')
    nm = list(z['names'])
    ref = np.array(Image.open(SRC / 'hgss/hgss-reference-true-heights.png').convert('RGB'))
    m = np.isin(z['material'], [nm.index(n) for n in names if n in nm])
    m &= np.load(SRC / 'hgss/hgss-foreground-owner.npz')['owner'] < 0
    art = np.zeros(ref.shape[:2] + (4,), np.uint8)
    art[m, :3] = ref[m]; art[m, 3] = 255
    return art

def snap_pieces(art, step=8):
    """Each separate piece of a lifted HGSS layer moved to the nearest step-px corner (at most
    step / 2 px), so identical pieces share their tiles. Returns the moved layer and the moves."""
    from scipy.ndimage import label, find_objects
    lb, n = label(art[..., 3] > 0)
    out = np.zeros_like(art)
    moves = []
    for i, sl in enumerate(find_objects(lb), 1):
        y0, x0 = sl[0].start, sl[1].start
        sub = art[sl].copy(); sub[lb[sl] != i] = 0
        ny, nx = int(round(y0 / step)) * step, int(round(x0 / step)) * step
        over(out, sub, nx, ny)
        moves.append(dict(hgss_xy=[int(x0), int(y0)], xy=[nx, ny]))
    return out, moves

def flowers(phg):
    """HGSS's flower cells (flower01-03): the flower heads lifted from the decoded ground
    texture, every pixel that is not one of the texture's lawn greens (green over red by 40)."""
    h, mat, names, rgb = E.topdown(phg)
    fm = np.isin(mat, [names.index(n) for n in ('flower01', 'flower02', 'flower03') if n in names])
    cells = sorted({(int(x) // PX, int(y) // PX) for y, x in zip(*np.nonzero(fm))})
    c = rgb.astype(int)
    m = fm & ~(c[..., 1] - c[..., 0] >= 40)
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    art[m, :3] = rgb[m]; art[m, 3] = 255
    return art, cells

# --------------------------------------------------------------------------- colour reduction
# Local HGSS pieces: at most this many tones that Blackthorn's palettes lack. Each piece's tones
# merge toward the CherrygrovePrimary banks its surroundings are drawn in: the flower heads on
# the lawn (bank 0), Route 46's dirt on the road (bank 1), the cascades on the sea (any primary bank).
REDUCE = {'flowers': (2, [0]), 'dirt': (1, [1]), 'cascades': (4, [0, 1, 2, 3, 4, 5])}

def neighbour_tones(banks):
    """The colours in the given banks of Blackthorn's installed palettes (CherrygrovePrimary
    banks 0-5, Blackthorn's secondary 6-12), RGB555."""
    out = set()
    for b in banks:
        d = 'primary/cherrygrove' if b < 6 else 'secondary/blackthorn_city'
        lines = (ENGINE / 'data/tilesets' / d / 'palettes' / f'{b:02}.pal').read_text().splitlines()[3:19]
        out |= {tuple(int(v) >> 3 for v in l.split()) for l in lines}
    return out

def reduce_local(art, n, anchors):
    """Merge the closest pair of RGB555 tones (the rarer into the commoner; a tone Blackthorn's
    palettes hold is never dropped) until at most n of the piece's tones are ones Blackthorn's
    palettes lack. Shapes untouched; each kept tone keeps its HGSS 8-bit value, or takes
    Blackthorn's when it merges into one of Blackthorn's."""
    m = art[..., 3] > 0
    c5 = art[..., :3].astype(int) >> 3
    cols, inv, cnt = np.unique(c5[m], axis=0, return_inverse=True, return_counts=True)
    inv = inv.ravel()
    w = cnt.astype(float)
    tones = [tuple(c) for c in cols]
    anchor = [t in anchors for t in tones]
    target = list(range(len(cols)))
    near = sorted(anchors)
    merged = []
    cw = np.array([3.0, 4.0, 2.0])
    while sum(1 for i in range(len(tones)) if target[i] == i and not anchor[i]) > n:
        best = None
        alive = [i for i in range(len(tones)) if target[i] == i]
        for i in alive:
            if anchor[i]:
                continue
            for j in alive:
                if j == i:
                    continue
                d = float((((np.array(tones[i]) - np.array(tones[j])) ** 2) * cw).sum()) * np.sqrt(min(w[i], w[j]))
                if best is None or d < best[0]:
                    best = (d, i, j)
            a = np.array(near)
            dd = (((a - np.array(tones[i])) ** 2) * cw).sum(1)
            k = int(dd.argmin())
            d = float(dd[k]) * np.sqrt(w[i])
            if best is None or d < best[0]:
                best = (d, i, ('anchor', tuple(near[k])))
        _, i, j = best
        if isinstance(j, tuple):
            tones.append(j[1]); anchor.append(True); w = np.append(w, 0.0); target.append(len(tones) - 1)
            j = len(tones) - 1
        keep, drop = (j, i) if anchor[j] or w[j] >= w[i] else (i, j)
        w[keep] += w[drop]
        target = [keep if t == drop else t for t in target]
        merged.append([[int(v) << 3 for v in tones[drop]], [int(v) << 3 for v in tones[keep]], int(w[drop])])
    first8 = {}
    flat = art[m]
    for k in range(len(cols)):
        first8[k] = flat[inv == k][0, :3]
    def colour(k):
        t = target[k]
        if t < len(cols) and not anchor[t]:
            return first8[t]
        return np.array([(v << 3) | (v >> 2) for v in tones[t]], np.uint8)
    out = art.copy()
    lut = np.array([colour(k) for k in range(len(cols))], np.uint8)
    out[m, :3] = lut[inv]
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

# Signs on their HGSS models, as Route 43, the Lake and Route 42 placed them: P14 (model 32)
# top-left (x * 16 - 8, (y - 1) * 16), P13 (model 31) top-left (x * 16 - 8, (y - 1.5) * 16).
SIGNS = {(24, 7): ('P14.png', 24 * PX - 8, 6 * PX), (12, 7): ('P13.png', 12 * PX - 8, int(5.5 * PX))}

def stairs(bottom, rock, top, owner, fl):
    """HGSS's flights over the cliff they cut through (rock_cells). A straight flight is
    S01, S02 ... S02, S03 across its row, opaque, so the cell is the flight alone (the rock comes
    off it). A diagonal flight is S04 or S05 over its column: there the cliff comes down to
    the ground layer and the flight goes over it on the top layer as a flat ground detail, so a
    player on the stairs stands on them (pack.FLAT)."""
    for kind, x, y, n, face in fl:
        if kind == 'row':
            for k in range(n):
                name = 'S01.png' if k == 0 else 'S03.png' if k == n - 1 else 'S02.png'
                sl = np.s_[y * PX:(y + 1) * PX, (x + k) * PX:(x + k + 1) * PX]
                bottom[sl] = rgba(SHARED / name)[..., :3]
                rock[sl] = 0
            continue
        art = rgba(SHARED / ('S04.png' if face == 'W' else 'S05.png'))
        sl = np.s_[y * PX:y * PX + art.shape[0], x * PX:(x + 1) * PX]
        a = rock[sl][..., 3] > 0
        bottom[sl][a] = rock[sl][a, :3]
        rock[sl] = 0
        over(top, art, x * PX, y * PX, owner, 'flat_stairs')

NB_DY = 64                                 # Blackthorn y = Route 45 y + 64 (Blackthorn is north of the route)
NB_W, NB_H = 64, 64
NB_BASE = 'origin/claude/blackthorn-city'

def neighbour_walk():
    """Blackthorn's walkable cells (collision 0, Surf water included), as installed at NB_BASE."""
    raw = subprocess.run(['git', '-C', str(ENGINE), 'show', f'{NB_BASE}:data/layouts/BlackthornCity/map.bin'],
                         capture_output=True, check=True).stdout
    grid = np.frombuffer(raw, '<u2').reshape(NB_H, NB_W)
    return {(x, y) for y in range(NB_H) for x in range(NB_W) if not (grid[y, x] >> 10) & 3}

def views():
    """What each map's camera shows of the other while the other's secondary tileset is loaded.
    The player's cell is drawn at screen (112, 72), so a standing view spans x * 16 - 112 to
    x * 16 + 128 and y * 16 - 72 to y * 16 + 88. Crossing a connection swaps the secondary
    tileset at the start of the step (fieldmap.c CameraMove), while the old view is still on
    screen and scrolls out over the step. So Route 45 pixels drawn under Blackthorn's tilesets
    are those in view from every walkable Blackthorn cell, and from every Route 45 cell on the
    seam that steps into Blackthorn; Blackthorn pixels drawn under Route 45's tilesets likewise.
    Returns (route45_px, blackthorn_px) masks, in each map's own pixels."""
    walk_n = neighbour_walk()
    cells = E.ledger(PHG)
    walk_r = {(x, y) for y in range(H) for x in range(W) if not cells[y][x]['blocked'] or is_water(cells[y][x])}
    seam_cols = {x for x in range(W) if (x, NB_H - 1) in walk_n and (x, 0) in walk_r}
    r45 = np.zeros((H * PX, W * PX), bool)
    nb = np.zeros((NB_H * PX, NB_W * PX), bool)
    def show(mask, x, y):
        """Mark the standing view centred on cell (x, y) of mask's map (y may lie outside it)."""
        x0, x1 = x * PX - 112, x * PX + 128
        y0, y1 = y * PX - 72, y * PX + 88
        mask[max(0, y0):max(0, min(mask.shape[0], y1)), max(0, x0):max(0, min(mask.shape[1], x1))] = True
    for x, y in walk_n:
        show(r45, x, y - NB_DY)
    for x in seam_cols:
        show(r45, x, 0)                        # stepping into Blackthorn from Route 45's top row
    for x, y in walk_r:
        show(nb, x, y + NB_DY)
    for x in seam_cols:
        show(nb, x, NB_H - 1)                  # stepping into Route 45 from Blackthorn's bottom row
    return r45, nb

def compose(phg):
    global PHG, TEX
    PHG = phg
    TEX = E.cherry_textures()
    cells = with_xy(E.ledger(phg))
    for x, y in E.RIVER_STAIRS:                       # the landing's flight (owner review, 2026-10-27)
        cells[y][x] = dict(cells[y][x], lab='s')
    trees = json.loads((TRACE / 'trees.json').read_text())['trees']
    rc = rock_cells(cells)
    rclab = np.array([[c['lab'] for c in row] for row in rc])
    global GROUND_CLASS
    q = ground_quadrants(rc, np.isin(rclab, list(E.ROCK)))
    GROUND_CLASS = np.where(q[::2, ::2] == G.PATH, 'sand', 'grass')        # one material per cell (ground_quadrants)
    ground, _ = paint_ground(q)
    # The rock pass reads each cell's ground as painted (tall grass is lawn, whatever HGSS's
    # material count called its floor).
    rc = [[dict(c, floor=str(GROUND_CLASS[y, x])) if c['floor'] in ('grass', 'sand') else c for x, c in enumerate(row)]
          for y, row in enumerate(rc)]
    ground = ground[..., :3].copy()
    reductions = {}
    lim = lambda k: (REDUCE[k][0], neighbour_tones(REDUCE[k][1]))
    # Route 46's red dirt at the west edge, in its commonest HGSS tone, edge to edge on its cells.
    dirt_art, reductions['dirt'] = reduce_local(hgss_material(list(DIRT)), *lim('dirt'))
    cols, cnt = np.unique(dirt_art[dirt_art[..., 3] > 0, :3], axis=0, return_counts=True)
    dirt = np.tile(cols[np.argmax(cnt)], (16, 16, 1)).astype(np.uint8)
    for y, x in zip(*np.nonzero(np.array([[c['floor'] == 'dirt' for c in row] for row in rc]))):
        ground[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX] = dirt
    plain_lawn(ground, rc, phg)
    boxes = decks(rc)
    bridges(ground, boxes)
    owner = np.full((H * PX, W * PX), '', object)
    wa = water(rc, ground)
    a = wa[..., 3] > 0
    ground[a] = wa[a, :3]; owner[a] = 'water'
    falls, reductions['cascades'] = cascades(rc, ground)
    bottom, rock, d, isrock, piece = frlg_rock(rc, ground, dirt)
    (OUT / 'terrace-grid.txt').write_text(
        '# Route 45 terraces (assemble.terraces), one line per cell row: ground and water levels 0-9 as digits, rock cells\n'
        '# as letters (A = level 0, B = 1 and so on), from HGSS land_data 108-112 decoded flat (elements.ledger).\n' +
        ''.join(f'{y:03d}    ' + ''.join((chr(65 + d[y, x]) if isrock[y, x] else str(d[y, x])) for x in range(W)) + '\n'
                for y in range(H)))
    view, nb_view = views()
    top = np.zeros((H * PX, W * PX, 4), np.uint8)
    fl = flights(cells)
    stairs(bottom, rock, top, owner, fl)
    fla, fcells = flowers(phg)
    fla, reductions['flowers'] = reduce_local(fla, *lim('flowers'))
    Image.fromarray(fla).save(LOCAL / 'flowers.png')
    tg, tg_used = tall_grass(cells)
    # HGSS's boulders become FRLG General's boulder (metatile 0x9F's top layer) in the Johto rock
    # ramp, the rock the map is built of: one on the middle of each HGSS boulder's footprint.
    _, boulder_moves = snap_pieces(hgss_material(['rock01']), 16)
    stones = np.zeros((H * PX, W * PX, 4), np.uint8)
    frlg_boulder = E.frlg_boulder(ENGINE)
    for b in boulder_moves:
        b['frlg_xy'] = [b['xy'][0] + 8, b['xy'][1] + 8]
        over(stones, frlg_boulder, *b['frlg_xy'])
    (LOCAL / 'reductions.json').write_text(json.dumps(dict(
        note='Local HGSS pieces: closest RGB555 tones merge (the rarer into the commoner, or onto the nearest tone '
             'Blackthorn\'s palettes hold) until at most the limit of tones Blackthorn lacks remain; shapes untouched. '
             'Entries: [dropped tone, kept tone, pixels].', limits={k: dict(new_tones=v[0], blackthorn_banks=v[1]) for k, v in REDUCE.items()}, **reductions), indent=1) + '\n')
    Image.fromarray(stones).save(LOCAL / 'boulders.png')
    a = stones[..., 3] > 0
    rock[a] = stones[a]; owner[a] = 'boulder'
    # Tall grass and flower heads are flat ground details on the top layer, never above the
    # player (pack.FLAT), as the Lake's driftwood.
    for art, name in ((tg, 'flat_tall_grass'), (fla, 'flat_flowers')):
        a = (art[..., 3] > 0) & (top[..., 3] == 0)
        top[a] = art[a]; owner[a] = name
    # Objects, painted north to south by their base row so the nearer one covers.
    objs = []
    t01 = rgba(SHARED / 'T01.png')
    for i, (tx, ty) in enumerate(trees):
        objs.append(dict(name=f'tree_{i}', master='shared-art/T01.png', xy=[tx * PX, ty * PX - PX], art=t01, root=[tx, ty]))
    for (sx, sy), (f, x, y) in SIGNS.items():
        objs.append(dict(name=f'sign_{sx}_{sy}', master=f'shared-art/{f}', xy=[x, y], art=rgba(SHARED / f), cell=[sx, sy]))
    for o in objs:
        a = o['art'][..., 3] > 0
        o['base'] = o['xy'][1] + int(np.nonzero(a.any(1))[0].max())
    objs.sort(key=lambda o: (o['base'], o['xy'][0]))
    for o in objs:
        over(top, o['art'], o['xy'][0], o['xy'][1], owner, o['name'])
    compose.boulders, compose.falls, compose.decks, compose.flights = boulder_moves, falls, boxes, fl
    # The trees alone, whole: where trees share a tile, the packer keeps the hidden one whole
    # under the other, so those tiles repeat.
    compose.trees = np.zeros_like(top)
    for o in objs:
        if o['name'].startswith('tree_'):
            over(compose.trees, o['art'], o['xy'][0], o['xy'][1])
    return bottom, rock, top, owner, d, objs, fcells, tg_used, view, nb_view

ENGINE = None
PHG = None
TEX = None
GROUND_CLASS = None

def main(phg, catalog, engine):
    global ENGINE
    ENGINE = engine
    for d in (OUT, OEV, LOCAL, SHARED):
        d.mkdir(parents=True, exist_ok=True)
    stage_shared(catalog)
    ground, rock, top, owner, levels, objs, fcells, tg_used, view, nb_view = compose(phg)
    view_img = ground.copy()
    for layer in (rock, top):
        a = layer[..., 3] > 0
        view_img[a] = layer[a, :3]
    Image.fromarray(view_img).save(OEV / 'composed.png')
    Image.fromarray(ground).save(OEV / 'ground.png')
    Image.fromarray(rock).save(OEV / 'rock.png')
    Image.fromarray(top).save(OEV / 'objects.png')
    np.savez_compressed(OUT / 'layers.npz', ground=ground, rock=rock, objects=top, owner=owner.astype(str), levels=levels,
                        trees=compose.trees, gate=np.zeros_like(top), blackthorn_view=view, route_view_of_blackthorn=nb_view)
    (OUT / 'placements.json').write_text(json.dumps(dict(
        note='Every placed object: master file, top-left pixel, base row. Trees sit on their decoded HGSS 2x2 roots '
             '(T01 bottom on the root bottom, crown one row behind); the signs stand on HGSS\'s own.',
        objects=[{k: v for k, v in o.items() if k != 'art'} for o in objs], flower_cells=fcells,
        tall_grass_pieces=tg_used, stairs=[dict(kind=k, cell=[x, y], length=n, face=f) for k, x, y, n, f in compose.flights],
        cave_mouth=CAVE, bridges=[list(b) for b in compose.decks], cascades=compose.falls, boulders=compose.boulders),
        indent=1, default=int) + '\n')
    print('objects', len(objs), 'flower cells', len(fcells), 'tall grass', tg_used, 'bridges', len(compose.decks))

if __name__ == '__main__':
    main(*(Path(a).resolve() for a in sys.argv[1:4]))
