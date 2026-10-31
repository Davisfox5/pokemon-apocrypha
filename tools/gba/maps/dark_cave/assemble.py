"""Dark Cave: built from the Johto routes' own tiles, recoloured to HGSS's cave.

    python3 tools/gba/maps/dark_cave/assemble.py PATH/TO/pokeheartgold ENGINE_CHECKOUT

Owner direction (October 31): no HGSS render pixels and no blended tiles. The cave is mapped out
cell by cell from HGSS's own data (ledger(): floors and their heights, rock and its tier heights,
stairs, jump ledges, water, boulders, exits), then drawn with exactly the pieces the routes use:

    ground   the routes' road (Cherrygrove's sand, its 16 px quarter) and sea, with the accepted
             painter's shore between them (route46/assemble.py paint_ground)
    rock     FRLG General's mountain nine-slice, over-rock pieces and inner corners, laid out as
             on the routes (route46/elements.py rock_frlg, route46/assemble.py terraces, topped,
             south_faces): every HGSS height is a terrace, ground included, and a wall has a face
             only toward ground that is really lower
    ledges   FRLG's jump ledge (elements.ledges_frlg)
    stairs   the catalog flights S01-S05 (route46/assemble.py flights, stairs)
    boulders FRLG General's boulder (elements.frlg_boulder)

The cave's surroundings (HGSS's black void) are rock, as a Gen 3 cave's are. Then the whole image
is recoloured, colour for colour (recolour()): the Johto rock ramp to the cave rock ramp taken from
HGSS's cave textures, the road and shore tones to HGSS's cave floor tones, the sea to its cave
water, the cast shadow to the floor's darkest. The exit glows and the hole are HGSS's own exit art
over the floor.

Writes source/assemble/<side>-{bottom,top}.png (layers), <side>.png (composited), <side>-class.npy,
<side>-terrace-grid.txt (the mapped shapes), evidence/assemble/<side>-before-after.png.
"""
from __future__ import annotations
import importlib.util, sys
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
MAPS = HERE.parent
sys.path.insert(0, str(HERE))
import pack as P                                      # noqa: E402

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

E = _load('route46_elements', MAPS / 'route46/elements.py')            # the routes' rock pieces and layout
sys.path.insert(0, str(MAPS))
from claude_cherrygrove import ground as G             # noqa: E402  (the accepted ground painter)

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/dark-cave'
SRC, EV = ART / 'source', ART / 'evidence'
STAIR_ART = ROOT / 'gba/art/route-46/source/shared-art'               # catalog S01-S05, as the routes stage them
W = H = 64
PX = 16
E.W, E.H = W, H                                          # rock_frlg reads its module's map size
VOID, FLOOR, FACE, TOP, RIM, BOULDER, STAIRS, WATER, EXIT = range(9)  # pack.CLASS numbers
WAVE16 = [0, 1, 1, 2, 2, 1, 1, 0, 0, -1, -1, -2, -2, -1, -1, 0]      # route46/assemble.py's painter wave

# Cave colours, from HGSS's Dark Cave textures (dwall_s, dcliff01, dallpeak_p; droad01; driver).
CAVE_RAMP = [(66, 57, 41), (173, 165, 148), (156, 148, 132), (140, 132, 115), (115, 107, 90), (99, 90, 74), (82, 74, 57)]

# --------------------------------------------------------------------------- the mapped shapes
def ledger(side):
    """One record per cell from HGSS's permissions, heights and materials: lab ('T' rock, '.'
    ground, 's' stairs, 'L' south ledge, 'Q' west ledge), floor ('sand' ground, 'water'), peak
    (rock), ground (floor height), plus void / boulder / exit flags."""
    hg = SRC / f'hgss/{side}'
    m = np.load(hg / 'hgss-ground-materials.npz')
    names = [str(v) for v in m['names']]
    hcls = np.array([P.CLASS[n] for n in names] + [VOID], np.int16)[m['material']]
    major = np.array([[Counter(hcls[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX].ravel().tolist()).most_common(1)[0][0]
                       for x in range(W)] for y in range(H)])
    perm = np.load(hg / 'hgss-permissions.npz')
    types, coll = perm['types'], perm['collision']
    height = np.nan_to_num(np.load(hg / 'hgss-cell-peak.npy'))            # top-down: a tier's top, a floor's level
    void = (types == 0) & (coll == 0)
    top = float(height.max()) + 1
    cells = []
    for y in range(H):
        row = []
        for x in range(W):
            t, k, h = int(types[y, x]), int(coll[y, x]), float(height[y, x])
            c = dict(x=x, y=y, lab='.', floor='sand', ground=h, peak=h, level=h, material=major[y, x])
            if void[y, x]:
                c.update(lab='T', peak=top, void=True)
            elif t == 0x3B:
                c.update(lab='L')
            elif t == 0x39:
                c.update(lab='Q')
            elif t == 0x15:
                c.update(floor='water')
            elif k & 0x80:
                if major[y, x] == BOULDER:
                    c.update(boulder=True)                       # FRLG boulder on the floor
                elif major[y, x] in (FLOOR, WATER):
                    # HGSS's small moss rocks (d_rock01s, too small to be the cell's main material):
                    # blocked, so drawn as the routes' boulder, on the water where HGSS has them in it
                    c.update(boulder=True, floor='water' if major[y, x] == WATER else 'sand')
                else:
                    c.update(lab='T')                            # rock (walls, pillars, exit rims)
            elif major[y, x] == STAIRS:
                c.update(lab='s')
            if t in (0x6F, 0x6E):
                c.update(exit=True)
            row.append(c)
        cells.append(row)
    # A blocked floor cell or boulder stands on the floor beside it: the height of its lowest open neighbour.
    for row in cells:
        for c in row:
            if c.get('boulder') or c['lab'] in 'LQ':
                near = [cells[c['y'] + dy][c['x'] + dx]['ground'] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                        if 0 <= c['x'] + dx < W and 0 <= c['y'] + dy < H and cells[c['y'] + dy][c['x'] + dx]['lab'] == '.']
                if near:
                    c['ground'] = min(near)
    return cells, hcls, major

def flights(cells):
    """HGSS's stair cells as the routes' flights: a run along a row is a straight flight down a
    south face (S01-S03); a run down a column is a diagonal flight down the face either side of
    it, descending toward its lower side (S04 west, S05 east). Returns [(kind, x, y, n, face)]."""
    s = np.array([[c['lab'] == 's' for c in row] for row in cells])
    seen, out = np.zeros_like(s), []
    g = lambda x, y: cells[y][x]['ground'] if 0 <= x < W and 0 <= y < H and cells[y][x]['lab'] == '.' else None
    for y in range(H):
        for x in range(W):
            if not s[y, x] or seen[y, x]:
                continue
            n = 0
            while x + n < W and s[y, x + n]:
                n += 1
            m = 0
            while y + m < H and s[y + m, x]:
                m += 1
            if n >= m and n > 1 or (n == m == 1 and g(x, y - 1) is not None and g(x, y + 1) is not None):
                seen[y, x:x + n] = True
                out.append(('row', x, y, n, 'S'))
                continue
            seen[y:y + m, x] = True
            west = [g(x - 1, y + k) for k in range(m) if g(x - 1, y + k) is not None]
            east = [g(x + 1, y + k) for k in range(m) if g(x + 1, y + k) is not None]
            face = 'W' if (min(west) if west else 99) < (min(east) if east else 99) else 'E'
            out.append(('column', x, y, m, face))
    return out

def rock_cells(cells, fl):
    """The ledger for the rock pass: every stair cell is part of the cliff it cuts through, at the
    height of the rock either side of it across its run, so the cliff runs on unbroken and the
    flight goes over it (route46/assemble.py rock_cells, river_stairs). Boulders and blocked floor
    are ground."""
    out = [[dict(c) for c in row] for row in cells]
    for kind, x0, y0, n, face in fl:
        for k in range(n):
            x, y = (x0 + k, y0) if kind == 'row' else (x0, y0 + k)
            steps = [(1, 0)] if kind == 'row' else [(0, 1)]
            near = []
            for sx, sy in steps:
                for s_ in range(1, W):
                    for sgn in (-1, 1):
                        nx, ny = x + sx * s_ * sgn, y + sy * s_ * sgn
                        if 0 <= nx < W and 0 <= ny < H and cells[ny][nx]['lab'] == 'T' and not cells[ny][nx].get('void'):
                            near.append((s_, cells[ny][nx]['peak']))
                if near:
                    break
            peak = min(near)[1] if near else cells[y][x]['ground'] + 1
            out[y][x] = dict(out[y][x], lab='S' if kind == 'row' else face, peak=peak, stair=True)
    return out

def regularise(rc, d, isrock):
    """Clean-up on the mapped shapes, so every cell is one the routes' pieces draw cleanly with the
    cells round it (owner review: go tile by tile). Repeats until nothing changes:

    wall rock   a moss rock HGSS sets into a wall's edge (two or more sides rock) is that wall,
                at the lowest of those rocks' heights, not a boulder notched into it
    floor       a floor cell whose height matches none of the floor beside it (HGSS's height noise:
                a cell one level up or down in an even corridor) takes the height most of them have
    spine       a one-cell ridge of higher rock along the top of a lower rock mass is that mass's top
    bump        a small raised patch (up to BUMP cells) with lower rock all round it is that rock's top
    nub         a rock cell standing proud of its wall with three or four sides lower has no FRLG
                piece: it becomes the routes' boulder on the floor beside it, still blocked

    deep rock   outer rock (joined to HGSS's void) more than DEEP cells from any floor, water, ledge
                or boulder (Chebyshev) is the rock top all round the cave, at the void's height: HGSS shows at most three tiers of a
                wall before its dark, and the far tiers of the big outer masses otherwise draw as
                stacks of rounded columns
    island      a rock formation standing free inside the cave is one block at its full height

    Returns {kind: [cells changed]}."""
    changed = dict(wall_rock=[], floor=[], nub=[], deep_rock=[], island=[], spine=[], bump=[])
    open_ = np.array([[not isrock[y, x] for x in range(W)] for y in range(H)])
    from scipy.ndimage import distance_transform_cdt
    from scipy.ndimage import label
    comp, _ = label(~open_, structure=np.ones((3, 3), bool))
    voids = np.array([[bool(c.get('void')) for c in row] for row in rc])
    outer = np.isin(comp, np.unique(comp[voids & (comp > 0)]))         # rock joined to the dark round the cave
    far = (distance_transform_cdt(~open_, metric='chessboard') > DEEP) & outer
    top = max(c['peak'] for row in rc for c in row)
    for y, x in zip(*np.nonzero(far & isrock)):
        if not rc[y][x].get('void') and not rc[y][x].get('stair'):
            rc[y][x] = dict(rc[y][x], peak=top, regularised='deep_rock')
            changed['deep_rock'].append([int(x), int(y)])
    # island: a rock formation standing free inside the cave (not joined to its outer walls) is one block
    # at its full height, so its inside tier steps (HGSS's 45-degree slopes) do not draw as rounded bumps
    for k in np.unique(comp[(comp > 0) & ~outer]):
        m = comp == k
        peak = max(rc[y][x]['peak'] for y, x in zip(*np.nonzero(m)))
        for y, x in zip(*np.nonzero(m)):
            if rc[y][x]['peak'] != peak:
                rc[y][x] = dict(rc[y][x], peak=peak, regularised='island')
                changed['island'].append([int(x), int(y)])
    d[:], _, isrock[:] = terraces(rc)
    orth = ((0, -1), (1, 0), (0, 1), (-1, 0))
    inside = lambda x, y: 0 <= x < W and 0 <= y < H
    is_floor = lambda c: c['lab'] == '.' and c['floor'] == 'sand' and not c.get('boulder')
    for _ in range(20):
        moved = False
        for y in range(H):
            for x in range(W):
                c = rc[y][x]
                if c.get('boulder') and c['floor'] == 'sand':
                    rocks = [rc[y + dy][x + dx] for dx, dy in orth if inside(x + dx, y + dy) and isrock[y + dy, x + dx]
                             and not rc[y + dy][x + dx].get('void')]
                    if len(rocks) >= 2:
                        rc[y][x] = dict(c, lab='T', boulder=False, peak=min(r['peak'] for r in rocks), regularised='wall_rock')
                        changed['wall_rock'].append([x, y]); moved = True
                elif is_floor(c) and not c.get('exit'):
                    lv = [level(rc[y + dy][x + dx]['ground']) for dx, dy in orth if inside(x + dx, y + dy) and is_floor(rc[y + dy][x + dx])]
                    if lv and level(c['ground']) not in lv:
                        g = Counter(lv).most_common(1)[0][0] + ROCK_BASE
                        rc[y][x] = dict(c, ground=float(g), regularised='floor')
                        changed['floor'].append([x, y]); moved = True
        d[:], _, isrock[:] = terraces(rc)
        # spine: a one-cell ridge of higher rock along the top of a lower rock mass (lower rock on two
        # opposite sides) draws as a pointed spike; it is that mass's top
        for y in range(1, H - 1):
            for x in range(1, W - 1):
                c = rc[y][x]
                if not isrock[y, x] or c.get('void') or c.get('stair'):
                    continue
                for (ax, ay), (bx, by) in (((-1, 0), (1, 0)), ((0, -1), (0, 1))):
                    A, B = (x + ax, y + ay), (x + bx, y + by)
                    if all(isrock[q[1], q[0]] and not rc[q[1]][q[0]].get('void') and d[q[1], q[0]] < d[y, x] for q in (A, B)):
                        peak = max(rc[A[1]][A[0]]['peak'], rc[B[1]][B[0]]['peak'])
                        rc[y][x] = dict(c, peak=peak, regularised='spine')
                        changed['spine'].append([x, y]); moved = True
                        break
        d[:], _, isrock[:] = terraces(rc)
        # bump: a small raised patch (up to BUMP cells) sitting on a rock top, lower rock all round it,
        # draws as a lone knob; it is that top
        from scipy.ndimage import label as _label
        for lv in sorted(set(d[isrock].tolist()), reverse=True):
            lab_, n = _label(isrock & (d == lv), structure=np.ones((3, 3), bool))
            for k in range(1, n + 1):
                m = lab_ == k
                if m.sum() > BUMP:
                    continue
                ys, xs = np.nonzero(m)
                ring = {(x + dx, y + dy) for y, x in zip(ys, xs) for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - set(zip(xs, ys))
                if not all(inside(*q) and isrock[q[1], q[0]] and not rc[q[1]][q[0]].get('void') and d[q[1], q[0]] < lv for q in ring):
                    continue
                if any(rc[y][x].get('stair') or rc[y][x].get('void') for y, x in zip(ys, xs)):
                    continue
                peak = max(rc[q[1]][q[0]]['peak'] for q in ring)
                for y, x in zip(ys, xs):
                    rc[y][x] = dict(rc[y][x], peak=peak, regularised='bump')
                    changed['bump'].append([int(x), int(y)]); moved = True
            d[:], _, isrock[:] = terraces(rc)
        for y in range(H):
            for x in range(W):
                c = rc[y][x]
                if not isrock[y, x] or c.get('void') or c.get('stair'):
                    continue
                low = [(dx, dy) for dx, dy in orth if inside(x + dx, y + dy) and d[y + dy, x + dx] < d[y, x]]
                if len(low) >= 3:
                    floors = [rc[y + dy][x + dx] for dx, dy in low if is_floor(rc[y + dy][x + dx])]
                    g = min((f['ground'] for f in floors), default=c['ground'])
                    rc[y][x] = dict(c, lab='.', floor='sand', ground=g, boulder=True, regularised='nub')
                    changed['nub'].append([x, y]); moved = True
        d[:], _, isrock[:] = terraces(rc)
        if not moved:
            break
    return changed

ROCK_BASE = None
DEEP = 3
BUMP = 6
def level(v):
    return int(np.floor(v + 0.5)) - ROCK_BASE

def terraces(cells):
    """route46/assemble.py terraces: every HGSS height is a Gen 3 terrace, the ground's as well as
    the rock's, so a wall has a face only toward ground that is really lower."""
    lab = np.array([[c['lab'] for c in row] for row in cells])
    rock = np.isin(lab, list(E.ROCK))
    d = np.zeros((H, W), int)
    for y in range(H):
        for x in range(W):
            c = cells[y][x]
            d[y, x] = level(c['peak']) if rock[y, x] else (int(np.floor(c['level'])) - ROCK_BASE if c['floor'] == 'water'
                                                           else level(c['ground']))
    d = np.maximum(d, 0)
    pad = np.pad(d, 1, mode='edge')
    lower = np.zeros((H, W), bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                lower |= pad[1 + dy:1 + dy + H, 1 + dx:1 + dx + W] < d
    return d, rock & lower, rock

def south_faces(cells, d, rock):
    """route46/assemble.py south_faces: rock whose slope falls north with ground south of it is a
    face looking south onto that ground, so no strip of rock floor lies beside the floor."""
    out = set()
    for y in range(1, H - 1):
        for x in range(W):
            s_ = cells[y + 1][x]
            if (rock[y, x] and not cells[y][x].get('stair') and d[y - 1, x] < d[y, x] and not rock[y + 1, x]
                    and s_['floor'] == 'sand' and s_['lab'] not in 'LJQ'):
                out.add((x, y))
    return out

def topped(cells, d, rock):
    """route46/assemble.py topped: a wall showing a face whose top is level with the floor beside
    it reads as that floor, its face, then the lower side (not a raised ridge); a side wall keeps
    FRLG's side piece whole."""
    out = {}
    for y in range(H):
        for x in range(W):
            if not rock[y, x] or cells[y][x].get('stair') or cells[y][x].get('void'):
                continue
            if any(0 <= x + dx < W and 0 <= y + dy < H and cells[y + dy][x + dx]['floor'] == 'water'
                   for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0))):
                continue
            low = {k for k, (dx, dy) in dict(e=(1, 0), s=(0, 1), w=(-1, 0)).items()
                   if 0 <= x + dx < W and 0 <= y + dy < H and d[y + dy, x + dx] < d[y, x]}
            if not low or low in ({'e'}, {'w'}):
                continue
            if any(0 <= x + dx < W and 0 <= y + dy < H and not rock[y + dy, x + dx] and cells[y + dy][x + dx]['floor'] == 'sand'
                   and d[y + dy, x + dx] >= d[y, x] for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0))):
                out[(x, y)] = 'sand'
    return out

# --------------------------------------------------------------------------- ground
def quarter(tex, name):
    oy, ox = dict(grass=(16, 16), sand=(0, 0))[name]
    return np.tile(tex[name][oy:oy + 16, ox:ox + 16], (2, 2, 1))

def paint_ground(q, tex):
    """route46/assemble.py paint_ground: the accepted painter on an 8 px material grid, road and sea."""
    U = 8
    hq, wq = q.shape
    h, w = hq * U, wq * U
    t = G.textures()
    t[G.PATH] = quarter(tex, 'sand'); t[G.SEA] = tex['water']
    t = {k: v for k, v in t.items() if k in (G.PATH, G.SEA)}
    ys, xs = np.mgrid[0:h, 0:w]
    wave = np.array(WAVE16)
    sx = np.clip(xs + wave[ys % 16], 0, w - 1) // U; sy = np.clip(ys + wave[(xs + 5) % 16], 0, h - 1) // U
    mat = q[sy, sx]
    out = np.zeros((h, w, 3), np.uint8)
    for k, tt in t.items():
        mm = mat == k
        out[mm] = tt[ys[mm] % tt.shape[0], xs[mm] % tt.shape[1]]
    if (mat == G.PATH).any() and (mat == G.SEA).any():
        dist = {k: G._chamfer(mat == k) for k in t}
        pa, pb = G.PROFILES[(G.PATH, G.SEA)]
        for k, c in enumerate(pa):
            out[(mat == G.PATH) & (dist[G.SEA] == k + 1)] = c
        for k, c in enumerate(pb):
            out[(mat == G.SEA) & (dist[G.PATH] == k + 1)] = c
    return out

# --------------------------------------------------------------------------- water
# FRLG General's rock-edged pond (Icefall Cave's and Berry Forest's): still water with a brown rock lip
# inside the water cell along every edge that meets land, so it never depends on the floor beside it.
# The lip is on FRLG's mountain bank (the rock ramp), the water on bank 3.
POND_NINE = {('N', 'W'): 419, ('N', 'M'): 422, ('N', 'E'): 420, ('M', 'W'): 429, ('M', 'M'): 430, ('M', 'E'): 431,
             ('S', 'W'): 548, ('S', 'M'): 549, ('S', 'E'): 550}
POND_INNER = dict(nw=436, ne=435)                       # only a diagonal is land; the south pair are these turned over

def pond_pieces(engine):
    """{key: (water rgb 16x16x3, lip index map 16x16 into the rock ramp, -1 clear)} from general_frlg."""
    d = engine / 'data/tilesets/primary/general_frlg'
    a = np.array(Image.open(d / 'tiles.png')) & 15
    tiles = [a[y:y + 8, x:x + 8] for y in range(0, a.shape[0], 8) for x in range(0, a.shape[1], 8)]
    blocks = np.frombuffer((d / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
    pal = lambda b: np.array([tuple(map(int, l.split())) for l in (d / 'palettes' / f'{b:02}.pal').read_text().replace('\r', '').splitlines()[3:19]], np.uint8)
    def piece(m):
        water = np.zeros((16, 16, 3), np.uint8); lip = np.full((16, 16), E.CLEAR, int)
        for li in range(8):
            e = int(blocks[m][li]); b = e >> 12
            t = tiles[e & 1023]
            if e & 0x400: t = t[:, ::-1]
            if e & 0x800: t = t[::-1]
            q = li % 4
            sl = np.s_[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            if li < 4:
                water[sl] = pal(b)[t]
            elif e:
                assert b == 1, (m, hex(e))
                sub = lip[sl]
                for (yy, xx), v in np.ndenumerate(t):
                    if v:
                        sub[yy, xx] = E.FRLG_RAMP.get(int(v), E.SHADOW)
        return water, lip
    out = {k: piece(v) for k, v in POND_NINE.items()}
    for k, v in POND_INNER.items():
        out[k] = piece(v)
    out['sw'] = tuple(x[::-1] for x in out['nw'])                # turned over: the lip's corner at the bottom
    out['se'] = tuple(x[::-1] for x in out['ne'])
    return out

def ponds(cells, pieces):
    """Every water cell from the pond pieces, per 8x8 quadrant as the rock nine-slice is composed:
    a land neighbour (anything not water) north, south, east or west puts the lip on that side; a
    land diagonal alone puts the inner corner there. Returns RGBA (lip pixels in the rock ramp)."""
    out = np.zeros((H * PX, W * PX, 4), np.uint8)
    wet = lambda x, y: not (0 <= x < W and 0 <= y < H) or cells[y][x]['floor'] == 'water'
    for y in range(H):
        for x in range(W):
            if cells[y][x]['floor'] != 'water':
                continue
            land = {k: not wet(x + dx, y + dy) for k, (dx, dy) in E.DIRS.items()}
            cell = np.zeros((16, 16, 4), np.uint8); cell[..., 3] = 255
            for qy in (0, 1):
                v = ('N', 'S')[qy] if land['n'] and land['s'] else 'N' if land['n'] else 'S' if land['s'] else 'M'
                for qx in (0, 1):
                    h = ('W', 'E')[qx] if land['w'] and land['e'] else 'W' if land['w'] else 'E' if land['e'] else 'M'
                    q = np.s_[qy * 8:qy * 8 + 8, qx * 8:qx * 8 + 8]
                    vk, hk = 'ns'[qy], 'we'[qx]
                    key = vk + hk if land[vk + hk] and not land[vk] and not land[hk] else (v, h)
                    water, lip = pieces[key]
                    cell[q][..., :3] = water[q]
                    for (yy, xx), k in np.ndenumerate(lip[q]):
                        if k >= 0:
                            cell[q][yy, xx, :3] = E.ROCK_RAMP[k]
            out[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX] = cell
    return out

# --------------------------------------------------------------------------- recolour
def recolour(img, tex):
    """Colour for colour: the Johto rock ramp to CAVE_RAMP, the routes' road and shore tones to
    HGSS's cave floor tones and the sea to its cave water (each by brightness rank), the cast
    shadow to the floor's darkest. Returns the image and the mapping."""
    lum = lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
    def ranked(src, dst):
        src = sorted(set(src), key=lum); dst = sorted(set(dst), key=lum)
        return {s: dst[min(len(dst) - 1, round(i * (len(dst) - 1) / max(1, len(src) - 1)))] for i, s in enumerate(src)}
    hg_floor = [tuple(int(v) for v in c) for c in np.unique(FLOOR_TEX.reshape(-1, 3), axis=0)]
    hg_water = [tuple(int(v) for v in c) for c in np.unique(WATER_TEX.reshape(-1, 3), axis=0)]
    road = [tuple(int(v) for v in c) for c in np.unique(quarter(tex, 'sand').reshape(-1, 3), axis=0)]
    sea = sorted({tuple(int(v) for v in c) for w, _ in POND.values() for c in w.reshape(-1, 3)})
    cmap = {tuple(s): tuple(d) for s, d in zip(E.ROCK_RAMP, CAVE_RAMP)}
    cmap.update(ranked(road, hg_floor))
    cmap.update(ranked(sea, hg_water))
    cmap[tuple(E.BORDER_GRAY)] = min(hg_floor, key=lum)
    cols = {tuple(int(v) for v in c) for c in np.unique(img.reshape(-1, 3), axis=0)}
    rest = [c for c in cols if c not in cmap]           # the catalog stairs' grey stone, by brightness rank
    cmap.update(ranked([c for c in rest if c in STAIR_STRAIGHT], CAVE_RAMP))
    cmap.update(ranked([c for c in rest if c not in STAIR_STRAIGHT], CAVE_RAMP))
    out = img.copy()
    flat = img.reshape(-1, 3)
    keys = flat[:, 0].astype(np.int32) << 16 | flat[:, 1].astype(np.int32) << 8 | flat[:, 2]
    res = out.reshape(-1, 3)
    for s, d in cmap.items():
        res[keys == (s[0] << 16 | s[1] << 8 | s[2])] = d
    return out, {f'{s}': d for s, d in cmap.items() if s in cols}

FLOOR_TEX = WATER_TEX = None
POND = None
PIECES = {}
STAIR_STRAIGHT = {(131, 131, 139), (164, 164, 164), (189, 189, 189), (213, 213, 213), (255, 255, 255)}   # S01-S03's tones

def main(phg, engine):
    global ROCK_BASE, FLOOR_TEX, WATER_TEX
    import hgss_render as R
    _, tex0, _, _, _ = R.load(phg)
    dec = {e.name: e for e in tex0.textures}
    FLOOR_TEX = R.decode(tex0, dec['droad01'], 'droad01_pl')[..., :3]
    WATER_TEX = R.decode(tex0, dec['driver'], 'driver_pl')[..., :3]
    exit_names = {'chole_in', 'chole_light', 'light'}                  # the glow and the hole, not chole_out's rubble rim
    out_dir = SRC / 'assemble'; out_dir.mkdir(parents=True, exist_ok=True)
    (EV / 'assemble').mkdir(parents=True, exist_ok=True)
    tex = E.cherry_textures()
    global POND
    POND = pond_pieces(engine)
    tex['water'] = quarter(tex, 'sand')                      # past a rock edge toward a pond: floor, then the pond's own lip
    pieces = E.frlg_pieces(engine)
    boulder = E.frlg_boulder(engine)
    report = {}
    for side in P.SIDES:
        cells, hcls, major = ledger(side)
        ROCK_BASE = int(np.floor(min(c['ground'] for row in cells for c in row if c['lab'] == '.') + 0.5))
        fl = flights(cells)
        rc = rock_cells(cells, fl)
        d, face, isrock = terraces(rc)
        nubs = regularise(rc, d, isrock)
        d, face, isrock = terraces(rc)
        E.layers = lambda _cells, _d=d, _f=face, _r=isrock: (_d, _f, _r)
        # ground: road everywhere but the water
        q = np.full((H * 2, W * 2), G.PATH, np.int8)            # the floor is road edge to edge; the ponds go over it
        ground = paint_ground(q, tex)
        pond = ponds(rc, POND)
        a = pond[..., 3] > 0
        ground[a] = pond[a, :3]
        main.piece = None
        bottom, over, _, piece = E.rock_frlg(rc, ground, pieces, tex, None, topped(rc, d, isrock), south_faces(rc, d, isrock), ())
        ledge = E.ledges_frlg(rc, pieces)
        PIECES[side] = (piece, d, isrock, rc)
        a = ledge[..., 3] > 0
        over[a] = ledge[a]
        top = np.zeros((H * PX, W * PX, 4), np.uint8)
        # stairs (route46/assemble.py stairs)
        for kind, x, y, n, f in fl:
            if kind == 'row':
                for k in range(n):
                    name = 'S01.png' if k == 0 else 'S03.png' if k == n - 1 else 'S02.png'
                    sl = np.s_[y * PX:(y + 1) * PX, (x + k) * PX:(x + k + 1) * PX]
                    bottom[sl] = np.array(Image.open(STAIR_ART / name).convert('RGBA'))[..., :3]
                    over[sl] = 0
                continue
            art = np.array(Image.open(STAIR_ART / ('S04.png' if f == 'W' else 'S05.png')).convert('RGBA'))
            sl = np.s_[y * PX:y * PX + art.shape[0], x * PX:(x + 1) * PX]
            aa = over[sl][..., 3] > 0
            bottom[sl][aa] = over[sl][aa, :3]
            over[sl] = 0
            m = art[..., 3] > 0
            top[sl][m] = art[m]
        for row in rc:
            for c in row:
                if c.get('boulder'):
                    sl = np.s_[c['y'] * PX:(c['y'] + 1) * PX, c['x'] * PX:(c['x'] + 1) * PX]
                    m = boulder[..., 3] > 0
                    top[sl][m] = boulder[m]
        comp = bottom[..., :3].copy()
        for layer in (over, top):
            a = layer[..., 3] > 0
            comp[a] = layer[a, :3]
        comp, cmap = recolour(comp, tex)
        # HGSS's exit art (the glows, the hole) over the floor, on the exit cells and their rims
        ref = np.array(Image.open(SRC / f'hgss/{side}/hgss-render.png').convert('RGB'))
        m = np.load(SRC / f'hgss/{side}/hgss-ground-materials.npz')
        names = [str(v) for v in m['names']]
        ex = np.isin(m['material'], [names.index(n) for n in exit_names if n in names])
        comp[ex] = ref[ex]
        cls = np.full((H * PX, W * PX), FLOOR, np.int16)
        rk = over[..., 3] > 0
        cls[rk] = FACE
        cls[np.repeat(np.repeat(np.array([[c['floor'] == 'water' for c in row] for row in rc]), PX, 0), PX, 1) & ~rk] = WATER
        cls[ex] = EXIT
        Image.fromarray(comp).save(out_dir / f'{side}.png')
        np.save(out_dir / f'{side}-class.npy', cls.astype(np.int8))
        (out_dir / f'{side}-terrace-grid.txt').write_text(
            f'# Dark Cave {side}: one line per cell row. Ground and water: their terrace level (0-9, HGSS height above\n'
            f'# the lowest floor); rock: a letter (A = level 0, B = 1 ...); stairs s, jump ledges L (south) / Q (west),\n'
            f'# boulders o, void (HGSS black, drawn as rock) #. Decoded from HGSS land_data (assemble.ledger).\n' +
            ''.join(f'{y:02d}  ' + ''.join(
                '#' if cells[y][x].get('void') else 's' if cells[y][x]['lab'] == 's' else cells[y][x]['lab'] if cells[y][x]['lab'] in 'LQ'
                else 'o' if cells[y][x].get('boulder') else chr(65 + d[y, x]) if isrock[y, x] else str(min(9, d[y, x]))
                for x in range(W)) + '\n' for y in range(H)))
        both = Image.new('RGB', (W * 32 + 12, H * 16), (24, 26, 30))
        both.paste(Image.fromarray(ref), (0, 0)); both.paste(Image.fromarray(comp), (W * 16 + 12, 0))
        both.save(EV / f'assemble/{side}-before-after.png')
        report[side] = dict(flights=len(fl), rock_cells=int(isrock.sum()), regularised=nubs, colour_map=cmap)
        print(side, len(fl), 'flights', int(isrock.sum()), 'rock cells', {k: len(v) for k, v in nubs.items()})
    return report

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
