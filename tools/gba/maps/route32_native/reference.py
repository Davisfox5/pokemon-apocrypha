"""Route 32: trace decoded HGSS Route 32 square by square (step 1 of docs/GBA_MAP_RECONSTRUCTION.md).

    python3 tools/gba/maps/route32_native/reference.py PHG_CHECKOUT

The authority is HGSS Route 32's own map data (EVERYWHERE matrix cells (14, 9..13), land_data
permissions, terrain mesh and zone events R32), decoded and rendered 1:1 at 16 px per tile by
hgss_render.py: the Route 29/30 catalog process (Mahogany / Route 43).

Native frame: HGSS tile (hx, hz) is native cell (hx + COL0, hz + ROW0), 16 px, no scaling.
Route 32 is HGSS's own 32 x 160 plus NORTH_PAD rows. Violet City lies north (HGSS matrix (14, 8)), Route 33
south (matrix (14, 14)), the open sea east (EVERYWHERE).
  * NORTH_PAD = 6 rows above HGSS row 0 continue Violet City's south edge: the lawn below its last tree
    row with its cobble road (Violet row 71). From Violet's road the camera sees five rows into Route 32,
    and each map draws the other's visible cells with its own tilesets, so rows 0-4 are Violet's own
    metatiles placed by id (Route 32's tilesets define them with Violet's art, pack.py), and row 5 is the
    same lawn drawn as route art, under the crowns of HGSS's first row of trees. Violet column x is Route
    32 column x - VIOLET_SHIFT: Violet's road (its columns 22-24) comes down onto columns 18-20, inside
    HGSS's open north edge (columns 14-25).

Labels beyond Route 30's: '~' is the sea (type 0x15), 'B' the wooden pier (HGSS's bridge_b/bridge_c
planks, walkable; HGSS gives its cells collision 6/13, the plank footstep, which Route 30's tracer reads
as stairs), 'O' a boulder (HGSS's sea_rock in the water, rock01 on land), 'C' the Union Cave mouth
(type 0x6e), 'w' the Ruins of Alph gatehouse doorway (type 0x6d, the gate's warps).
The Magnet Train viaduct crosses the route at HGSS rows 82.5-87.5: land_data carries only its shadow
(a translucent band in the terrain mesh); the deck is drawn above the player on those rows (assemble.py).

Writes gba/art/route32-native/source/trace/{ledger.json, material-grid.txt, traversal.json,
trees.json} and evidence/trace/ numbered sheets of the HGSS render with the grid.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hgss_render as R                              # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route32-native'
SRC, EV = ART / 'source', ART / 'evidence'
OUT, OEV = SRC / 'trace', EV / 'trace'
HW, HH = 32, 160                      # HGSS Route 32
NORTH_PAD = 6
COL0, ROW0 = 0, NORTH_PAD
W, H = HW + COL0, HH + ROW0           # 32 x 166
VIOLET_SHIFT = 4                      # Route 32 column x is Violet column x + 4 (connection offset -4)
VIOLET_ROAD = range(22 - VIOLET_SHIFT, 25 - VIOLET_SHIFT)   # native 18-20: Violet's cobble road in the padding
VIOLET_ROW = 71                       # the Violet row the padding repeats: lawn below its forest, the road
VIOLET_ID_ROWS = 5                    # padding rows 0-4: Violet's metatiles by id; row 5: the same, as route art
WINDOW = 8                            # seam window: drawn by the neighbouring map with its own tilesets
PX = 16
VIADUCT = (82.5, 87.5)                # HGSS rows of the viaduct's shadow (its footprint)
TREES = ('tree01gs', 'tree01_un', 'tree01_re')
LIGHT = ('grass02', 'grass02_r', 'grass02_a')
FLOWERS = ('flower01', 'flower02', 'flower03')
WALLS = ('wall01_g', 'wall01_d', 'cliff01gs')
LEDGE_MATERIALS = ('allpeakgs', 'allpeak_pgs')
PIER = ('bridge_b', 'bridge_c')
BOULDERS = ('sea_rock', 'sea_rock_m', 'rock01')
BUILDINGS = {36: 'alph_gatehouse', 40: 'pokemon_center'}   # HGSS building models
SIGN_MODELS = {32: 'P14'}                                  # green route sign

def to_map(hx, hz): return hx + COL0, hz + ROW0
def to_hgss(x, y): return x - COL0, y - ROW0

# --------------------------------------------------------------------------- flat decode
_TD = {}
def topdown(phg):
    """HGSS terrain drawn flat from straight above: per-pixel height, material and colour."""
    if 'v' not in _TD:
        land, tex0, models, chunks, meta = R.load(phg)
        cv = R.Canvas(HW * PX, HH * PX)
        for c in chunks:
            ch = R.hgss_map.MapChunk.parse(land[c['land']])
            ox, oz = c['cx'] * 32, c['cz'] * 32
            R.draw_model(cv, R.mdlview.Model(ch.model), tex0, lambda x, y, z, ox=ox, oz=oz: (x + 16 + ox, y, z + 16 + oz), -1, None, flat=True)
        h = np.nan_to_num(cv.height, nan=float(np.nanmin(cv.height)))
        _TD['v'] = (h, cv.mat, list(R.MATERIAL_NAMES), cv.rgb.astype(np.uint8))
    return _TD['v']

def ledger(phg, rinfo, events):
    """One label per HGSS cell from the decoded permissions, its flat materials and heights.
    F woods (0x06), G tall grass (0x02), ~ sea (0x15) or fresh water (0x10), L/Q/E jump south/west/east
    (0x3B/0x39/0x38), J blocked ledge end (0x3E), D door (0x69), w gatehouse doorway (0x6D), C cave mouth
    (0x6E), B pier, O boulder, ^ stairs (collision 6, 'slope'), H building, s sign, R rock (face: T top,
    E/S/W/N by downhill direction, Route 43's decode), X other blocked, . open."""
    h, mat, names, rgb = topdown(phg)
    perm = np.load(SRC / 'hgss/hgss-permissions.npz')
    types, coll = perm['types'], perm['collision']
    nm = np.array(names + ['none'])
    m = np.where(mat >= 0, mat, len(names)).reshape(HH, PX, HW, PX).transpose(0, 2, 1, 3).reshape(HH, HW, PX * PX)
    gy, gx = np.gradient(h)
    slope = np.hypot(gx, gy) > 0.05
    share = slope.reshape(HH, PX, HW, PX).mean(axis=(1, 3))
    ddx = -(gx * slope).reshape(HH, PX, HW, PX).sum(axis=(1, 3))
    ddy = -(gy * slope).reshape(HH, PX, HW, PX).sum(axis=(1, 3))
    hc = h.reshape(HH, PX, HW, PX).transpose(0, 2, 1, 3).reshape(HH, HW, PX * PX)
    level = np.median(hc, -1)
    low = hc.min(-1)
    wallpx = np.isin(nm[m], WALLS)
    peak = np.where(wallpx.any(-1), np.where(wallpx, hc, -1e9).max(-1), hc.max(-1))
    house = np.full((HH, HW), '', object)
    for b in rinfo['buildings']:
        if b['model'] in BUILDINGS:
            x0, z0, x1, z1 = b['footprint']
            for hz in range(max(0, int(np.floor(z0))), min(HH, int(np.ceil(z1)))):
                for hx in range(max(0, int(np.floor(x0))), min(HW, int(np.ceil(x1)))):
                    house[hz, hx] = BUILDINGS[b['model']]
    signs = {tuple(s['cell']) for s in events['signs'] if s['bg_type'] == 1}
    labels = {0x06: 'F', 0x02: 'G', 0x15: '~', 0x10: '~', 0x3B: 'L', 0x39: 'Q', 0x38: 'E', 0x3E: 'J',
              0x69: 'D', 0x6D: 'w', 0x6E: 'C'}
    cells = []
    for hz in range(HH):
        row = []
        for hx in range(HW):
            u, cnt = np.unique(nm[m[hz, hx]], return_counts=True)
            frac = {str(k): int(v) for k, v in zip(u, cnt)}
            dominant = str(u[np.argmax(cnt)])
            t, k = int(types[hz, hx]), int(coll[hz, hx])
            blocked = bool(k & 0x80)
            pier = sum(frac.get(n, 0) for n in PIER)
            boulder = sum(frac.get(n, 0) for n in BOULDERS)
            if pier > 96 and not blocked:
                lab = 'B'
            elif t in labels and not (t == 0x15 and blocked):
                lab = labels[t]
            elif blocked and boulder > 64:
                lab = 'O'
            elif k == 6 or frac.get('slope', 0) > 96:
                lab = '^'
            elif (hx, hz) in signs:
                lab = 's'
            elif blocked and house[hz, hx]:
                lab = 'H'
            elif blocked and dominant in LEDGE_MATERIALS:
                lab = 'J'
            elif blocked and sum(frac.get(w, 0) for w in WALLS) > 64:
                lab = 'R'
            elif blocked:
                lab = 'X'
            else:
                lab = '.'
            sand = sum(v for n, v in frac.items() if n.startswith('road'))
            face = ''
            if lab == 'R':
                a = np.degrees(np.arctan2(ddy[hz, hx], ddx[hz, hx])) % 360
                face = 'ESWN'[int(((a + 45) % 360) // 90)] if share[hz, hx] > 0.25 else 'T'
            row.append(dict(lab=lab, face=face, type=t, collision=k, blocked=blocked,
                            floor='sand' if sand > 128 else 'grass', material=dominant,
                            level=round(float(level[hz, hx]), 2), ground=round(float(low[hz, hx] if t == 0x06 else level[hz, hx]), 2),
                            peak=round(float(peak[hz, hx]), 2), house=house[hz, hx],
                            flowers=sum(frac.get(n, 0) for n in FLOWERS), light=sum(frac.get(n, 0) for n in LIGHT),
                            pier=pier, boulder=boulder))
        cells.append(row)
    return cells

# --------------------------------------------------------------------------- trees
def woods_mask(cells):
    m = np.zeros((H, W), bool)
    for hz in range(HH):
        for hx in range(HW):
            x, y = to_map(hx, hz)
            m[y, x] = cells[hz][hx]['lab'] == 'F'
    return m

def tree_roots(woods, cells, phg=None):
    """HGSS's own trees: each is a 2x2 block of woods cells whose lower row carries the trunk's under-shade
    (tree01_un, decoded flat). Blocks are read left to right along each trunk row, so every native tree
    stands on the footprint of an HGSS tree. Woods cells left over are the crown rows above each forest
    band, which the native crowns cover (material grid 'k')."""
    h, mat, names, rgb = topdown(phg)
    un = (mat == names.index('tree01_un')).reshape(HH, PX, HW, PX).mean((1, 3)) > 0.3
    used = np.zeros((H, W), bool)
    roots = []
    for hz in range(1, HH):
        y = hz + ROW0
        x = 0
        while x < W - 1:
            hx = x - COL0
            ok = (0 <= hx < HW - 1 and un[hz, hx] and all(woods[y - dy, x + dx] and not used[y - dy, x + dx]
                                                        for dx in (0, 1) for dy in (0, 1)))
            if ok:
                roots.append((x, y - 1)); used[y - 1:y + 1, x:x + 2] = True; x += 2
            else:
                x += 1
    return sorted(roots, key=lambda t: (t[1], t[0])), []

# --------------------------------------------------------------------------- grid
CODES = {'g': 'lawn', 'd': 'dirt road', 'f': 'lawn with flowers', 'l': 'light lawn patch', 'G': 'tall grass (G15)',
         't': 'tree root (T01)', 'o': 'woods cell no root fits: blocked lawn under the woods edge',
         'k': 'woods cell under the crown of the tree south of it (blocked)',
         'L': 'jump ledge south', 'Q': 'jump ledge west', 'E': 'jump ledge east', 'J': 'ledge end (blocked)',
         '~': 'sea (Surf)', 'B': 'wooden pier', 'O': 'boulder', '^': 'stairs', 'R': 'rock (terrace, FRLG faces)',
         'H': 'building', 'D': 'Center door', 'w': 'gatehouse doorway', 'C': 'Union Cave mouth', 's': 'sign',
         'c': 'cuttable tree (object)', 'X': 'other blocked',
         'P': "Violet City's lawn (its metatiles, north padding)", 'p': "Violet City's cobble road (north padding)",
         'v': "Violet City's lawn drawn as route art (north padding row 5, under the first tree row's crowns)"}

def pad_source(x, y):
    """Violet cell (column, row) a north padding cell repeats."""
    return x + VIOLET_SHIFT, VIOLET_ROW

def material_grid(cells, woods, roots, events):
    rooted = {(x + dx, y + dy) for x, y in roots for dx in (0, 1) for dy in (0, 1)}
    crowns = {(x + dx, y - 1) for x, y in roots for dx in (0, 1)} - rooted
    cut = {to_map(*o['cell']) for o in events['objects'] if o['sprite'] == 'SPRITE_TREE'}
    grid = [['?'] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            hx, hz = to_hgss(x, y)
            if y < ROW0:
                grid[y][x] = 'p' if x in VIOLET_ROAD else 'P' if y < VIOLET_ID_ROWS else 'v'
                continue
            c = cells[hz][hx]
            if (x, y) in cut:
                ch = 'c'
            elif woods[y, x]:
                ch = 't' if (x, y) in rooted else 'k' if (x, y) in crowns else 'o'
            elif c['lab'] in 'GLQEJ~B^ORHDwCsX':
                ch = c['lab']
            elif c['floor'] == 'sand':
                ch = 'd'
            elif c['light'] > 96:
                ch = 'l'
            elif c['flowers'] > 24:
                ch = 'f'
            else:
                ch = 'g'
            grid[y][x] = ch
    # A flight across a wall (rock above and below it) more than one column wide is one diagonal flight per
    # column, one level each, and the columns stack: each lower column stands one row further south than the
    # column above it (Route 45's owner-accepted river flights), so the flight runs down the wall's levels in
    # steps. HGSS's ground heights say which side is high; the vacated cell is the wall, the cell gained below
    # was the wall.
    seen = set()
    for y0 in range(ROW0, H):
        for x0 in range(W):
            if grid[y0][x0] != '^' or (x0, y0) in seen:
                continue
            comp, todo = set(), [(x0, y0)]
            while todo:
                c = todo.pop()
                if c in comp or not (0 <= c[0] < W and ROW0 <= c[1] < H) or grid[c[1]][c[0]] != '^':
                    continue
                comp.add(c); todo += [(c[0] + dx, c[1] + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            seen |= comp
            xs, ys = sorted({c[0] for c in comp}), sorted({c[1] for c in comp})
            rk = lambda x, y: ROW0 <= y < H and grid[y][x] in 'RX'
            if len(xs) < 2 or not all(rk(x, ys[0] - 1) and rk(x, ys[-1] + 1) for x in xs):
                continue
            lv = lambda x: np.mean([cells[y - ROW0][x - COL0]['ground'] for y in ys])
            order = xs if lv(xs[0]) > lv(xs[-1]) else xs[::-1]          # high side first
            for k, x in enumerate(order):
                for y in ys:
                    grid[y][x] = 'R'
                for y in ys:
                    grid[y + k][x] = '^'
            seen |= {(x, y + k) for k, x in enumerate(order) for y in ys}
    # Rock out in the sea takes HGSS's rock art, not its collision: HGSS blocks its islets only in patches (the big
    # islet at x27-31, rows 94-97, is mostly surfable) and steps the pillar under the big wall a column west of its
    # art. A sea or rock cell whose eight neighbours are all sea, rock, boulder, pier or viaduct is rock where HGSS's
    # rock pixels cover at least half of it, sea otherwise.
    mz = np.load(SRC / 'hgss/hgss-ground-materials.npz')
    names = [str(nm) for nm in mz['names']]
    rockpx = np.isin(mz['material'], [names.index(nm) for nm in WALLS if nm in names])
    cover = rockpx.reshape(HH, PX, HW, PX).mean((1, 3))
    base = [row[:] for row in grid]
    for y in range(ROW0, H):
        for x in range(W):
            if base[y][x] not in '~R':
                continue
            nb = [base[b][a] for a in range(x - 1, x + 2) for b in range(y - 1, y + 2)
                  if 0 <= a < W and ROW0 <= b < H and (a, b) != (x, y)]
            if all(c in '~ROXB' for c in nb):
                hx, hz = to_hgss(x, y)
                grid[y][x] = 'R' if cover[hz, hx] >= 0.5 else '~'
    return grid

# --------------------------------------------------------------------------- sheets
def numbered(img, x0, y0, x1, y1, scale, grid=None, title='', origin=(0, 0)):
    """Crop native-frame cells x0..x1, y0..y1 of an image whose pixel (0,0) is native cell origin."""
    ox, oy = origin
    w, h = (x1 - x0) * PX * scale, (y1 - y0) * PX * scale
    crop = np.zeros(((y1 - y0) * PX, (x1 - x0) * PX, 3), np.uint8) + 24
    sy0, sx0 = (y0 - oy) * PX, (x0 - ox) * PX
    for yy in range(crop.shape[0]):
        sy = sy0 + yy
        if 0 <= sy < img.shape[0]:
            a, b = max(0, -sx0), min(crop.shape[1], img.shape[1] - sx0)
            if b > a:
                crop[yy, a:b] = img[sy, sx0 + a:sx0 + b]
    big = Image.fromarray(crop).resize((w, h), Image.Resampling.NEAREST)
    out = Image.new('RGB', (w + 28, h + 40), (24, 26, 30)); out.paste(big, (28, 40))
    d = ImageDraw.Draw(out)
    n = PX * scale
    for i in range(x1 - x0 + 1):
        d.line((28 + i * n, 40, 28 + i * n, 40 + h), fill=(255, 0, 255) if (x0 + i) % 5 == 0 else (90, 90, 100))
        if i < x1 - x0:
            d.text((28 + i * n + 2, 26), str(x0 + i), fill='white')
    for i in range(y1 - y0 + 1):
        d.line((28, 40 + i * n, 28 + w, 40 + i * n), fill=(255, 0, 255) if (y0 + i) % 5 == 0 else (90, 90, 100))
        if i < y1 - y0:
            d.text((2, 40 + i * n + 2), str(y0 + i), fill='white')
    if grid is not None:
        for y in range(y0, y1):
            for x in range(x0, x1):
                d.text((28 + (x - x0) * n + 3, 40 + (y - y0) * n + 2), grid[y][x], fill='black', stroke_width=2, stroke_fill='white')
    d.text((4, 4), title, fill='white')
    return out

SHEETS = [(0, y, W, min(y + 33, H)) for y in range(0, H, 32)]

def main(phg):
    OUT.mkdir(parents=True, exist_ok=True); OEV.mkdir(parents=True, exist_ok=True)
    events = json.loads((SRC / 'hgss-events.json').read_text())
    rinfo = json.loads((SRC / 'hgss/hgss-render.json').read_text())
    cells = ledger(phg, rinfo, events)
    woods = woods_mask(cells)
    roots, detected = tree_roots(woods, cells, phg)
    grid = material_grid(cells, woods, roots, events)
    (OUT / 'ledger.json').write_text(json.dumps(dict(
        note=f'Per HGSS cell (row hz, column hx): permission type/collision, label, ground. Native cell = (hx+{COL0}, hz+{ROW0}).',
        cells=cells)) + '\n')
    (OUT / 'trees.json').write_text(json.dumps(dict(
        note='Native 2x2 tree roots (top-left cell; crown row, trunk row). T01 draws its crown one row north of the root.',
        roots=roots, hgss_trunk_detected=detected), indent=0) + '\n')
    (OUT / 'material-grid.txt').write_text(
        f'# Route 32 native material grid ({W}x{H}), one code per 16x16 cell. Native = HGSS + ({COL0}, {ROW0}); {NORTH_PAD} rows north continue Violet City.\n' +
        ''.join(f'#   {k}  {v}\n' for k, v in CODES.items()) +
        '#   x: ' + ''.join(str(x % 10) for x in range(W)) + '\n' +
        ''.join(f'{y:03d}   ' + ''.join(row) + '\n' for y, row in enumerate(grid)))
    perm = np.load(SRC / 'hgss/hgss-permissions.npz')
    (OUT / 'traversal.json').write_text(json.dumps(dict(
        note='Decoded HGSS foot access per HGSS cell: type byte and collision bit 0x80 (land_data permissions).',
        cells=[dict(hx=hx, hz=hz, type=int(perm['types'][hz, hx]), collision=int(perm['collision'][hz, hx]),
                    foot={0x3B: 'ledge_south', 0x39: 'ledge_west', 0x38: 'ledge_east', 0x3E: 'ledge_corner', 0x69: 'door',
                          0x6D: 'gate_warp', 0x6E: 'cave_warp', 0x15: 'surf', 0x10: 'surf'}.get(
                        int(perm['types'][hz, hx]), 'blocked' if perm['collision'][hz, hx] & 0x80 else 'open'))
               for hz in range(HH) for hx in range(HW)])) + '\n')
    ref = np.array(Image.open(SRC / 'hgss/hgss-reference-true-heights.png').convert('RGB'))
    for i, (x0, y0, x1, y1) in enumerate(SHEETS, 1):
        numbered(ref, x0, y0, x1, y1, 2, title=f'HGSS Route 32 (decoded), native cells x{x0}-{x1 - 1}, y{y0}-{y1 - 1}',
                 origin=(COL0, ROW0)).save(OEV / f'hgss-numbered-{i}.png')
        numbered(ref, x0, y0, x1, y1, 2, grid=grid, title=f'Material grid over HGSS, native cells x{x0}-{x1 - 1}, y{y0}-{y1 - 1}',
                 origin=(COL0, ROW0)).save(OEV / f'grid-over-hgss-{i}.png')
    from collections import Counter
    print('codes', dict(Counter(ch for r in grid for ch in r)), 'roots', len(roots))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
