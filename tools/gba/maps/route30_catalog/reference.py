"""Route 30: trace decoded HGSS Route 30 square by square (step 1 of docs/GBA_MAP_RECONSTRUCTION.md).

    python3 tools/gba/maps/route30_catalog/reference.py PHG_CHECKOUT

The authority is HGSS Route 30's own map data (EVERYWHERE matrix cells (17, 9..11), land_data
permissions, terrain mesh and zone events R30), decoded and rendered 1:1 at 16 px per tile by
hgss_render.py: the Route 29 catalog process (Mahogany / Route 43), with Route 43's rock decode.

Native frame: HGSS tile (hx, hz) is native cell (hx + COL0, hz + ROW0), 16 px, no scaling.
  * COL0 = 5 puts HGSS's south road (columns 3-6, native 8-11) on Cherrygrove's north road (Cherrygrove
    columns 43-45, native 8-10, and its rim; connection offset 35, unchanged), and HGSS's woods east of the
    road (columns 8-21, native 13-26) on the column pairs of Cherrygrove's forest band (trees on odd
    columns there), so the route's trees stand in the band's columns.
  * SOUTH_PAD = 6 rows below HGSS row 95 carry Cherrygrove's own north forest band (its rows 0-2, twice,
    as Cherrygrove's primary metatile ids) with its road: from Cherrygrove's road and lawn the camera sees
    five rows into Route 30, which would otherwise show HGSS's west wall and south pond in Cherrygrove's
    tileset. The band continues the town's forest across the seam; its two blossom trees take the
    green tree beside them (the blossom's palette would cost a whole secondary bank). The route's west
    wall (native columns 5-6) runs on through the band into Cherrygrove, where the town's east-west cliff
    turns north to meet it (WALL_COLS, cherrygrove_wall.py).
  * NORTH_PAD = 2 rows above HGSS row 0 continue its north edge: the rock at Route 31's plateau height with
    the road on through it from the top of the stairs (HGSS row 0 with its stairs as road). Route 31's
    camera sees five rows into Route 30, and each map draws the other's visible cells with its own
    tilesets; without the pad that view takes in Mr. Pokemon's roof, whose colours Route 31's banks cannot
    hold beside its own art (pair_pack.py).

Writes gba/art/route30-catalog/source/trace/{ledger.json, material-grid.txt, traversal.json,
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
ART = ROOT / 'gba/art/route30-catalog'
SRC, EV = ART / 'source', ART / 'evidence'
OUT, OEV = SRC / 'trace', EV / 'trace'
HW, HH = 32, 96                       # HGSS Route 30
NORTH_PAD = 2
COL0, ROW0 = 5, NORTH_PAD
SOUTH_PAD = 6
W, H = HW + COL0, HH + ROW0 + SOUTH_PAD   # 37 x 104
WINDOW = 8                            # seam window: drawn by the neighbouring map with its own tilesets
PX = 16
CG_OFFSET = 35                        # Cherrygrove's "up" connection: Route 30 column 0 is Cherrygrove column 35
# Lawn and road textures are Cherrygrove's 32 px blocks in Cherrygrove's own pixel frame, so Route 30
# samples them at Cherrygrove's phase: x + 35 cells, y - H cells.
XPHASE, YPHASE = (CG_OFFSET * PX) % 32, (-H * PX) % 32
TREES = ('tree01gs', 'tree01_un', 'tree01_re')
LIGHT = ('grass02', 'grass02_r', 'grass02_a')
FLOWERS = ('flower01', 'flower02', 'flower03')
WALLS = ('wall01_g', 'wall01_d', 'cliff01gs')
LEDGE_MATERIALS = ('allpeakgs', 'allpeak_pgs')
HOUSES = {53: 'mr_pokemon_house', 37: 'apricorn_house'}   # HGSS building models
SIGN_MODELS = {30: 'P12', 32: 'P14', 34: 'P16'}           # wooden signpost, green route sign, blue board

def to_map(hx, hz): return hx + COL0, hz + ROW0
def to_hgss(x, y): return x - COL0, y - ROW0
def in_window(y): return y < WINDOW or y >= H - WINDOW

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
    F woods (0x06), G tall grass (0x02), ~ water (0x10), L/Q/E jump south/west/east (0x3B/0x39/0x38),
    J blocked ledge end, D door (0x69), ^ stairs (collision 6, 'slope'), H house, n fence, s sign,
    R rock (face: T top, E/S/W/N by downhill direction, Route 43's decode), X other blocked, . open."""
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
        if b['model'] in HOUSES:
            x0, z0, x1, z1 = b['footprint']
            for hz in range(max(0, int(np.floor(z0))), min(HH, int(np.ceil(z1)))):
                for hx in range(max(0, int(np.floor(x0))), min(HW, int(np.ceil(x1)))):
                    house[hz, hx] = HOUSES[b['model']]
    signs = {tuple(s['cell']) for s in events['signs'] if s['bg_type'] == 1}
    labels = {0x06: 'F', 0x02: 'G', 0x10: '~', 0x3B: 'L', 0x39: 'Q', 0x38: 'E', 0x3E: 'J', 0x69: 'D'}
    cells = []
    for hz in range(HH):
        row = []
        for hx in range(HW):
            u, cnt = np.unique(nm[m[hz, hx]], return_counts=True)
            frac = {str(k): int(v) for k, v in zip(u, cnt)}
            dominant = str(u[np.argmax(cnt)])
            t, k = int(types[hz, hx]), int(coll[hz, hx])
            blocked = bool(k & 0x80)
            if t in labels:
                lab = labels[t]
            elif k == 6 or frac.get('slope', 0) > 96:
                lab = '^'
            elif (hx, hz) in signs:
                lab = 's'
            elif blocked and house[hz, hx]:
                lab = 'H'
            elif blocked and frac.get('fence_b', 0) > 64:
                lab = 'n'
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
                            flowers=sum(frac.get(n, 0) for n in FLOWERS), light=sum(frac.get(n, 0) for n in LIGHT)))
        cells.append(row)
    return cells


# --------------------------------------------------------------------------- frame
# The south padding is Cherrygrove's rows 0-2 (its north forest band and road), repeated: native row
# y >= PAD0 shows Cherrygrove cell (x + CG_OFFSET, (y - PAD0) % 3).
PAD0 = HH + ROW0
ROAD_COLS = range(43 - CG_OFFSET, 46 - CG_OFFSET)     # native 8-10: Cherrygrove's road; 7 and 11 hold its rims
BLOSSOM = {48: 50, 49: 51, 62: 64, 63: 65}   # Cherrygrove's two blossom trees in the band take the green pair beside them
# Route 30's west wall runs on south through the band into Cherrygrove, where Cherrygrove's east-west cliff
# (its rows 7-9) turns north to meet it (cherrygrove_wall.py): native columns 5-6 (Cherrygrove 40-41) are
# rock at 2 and 1 terrace levels above the floor, as on the route. Beside the wall, the band's columns 4 and 7
# (Cherrygrove 39 and 42, its rows 0-5) are Cherrygrove's blocked lawn and its road's left rim: (even-row,
# odd-row) metatile, collision.
WALL_COLS = {5: 2, 6: 1}
BAND_KIT = {4: ((0x033, 0x027), 3), 7: ((0x04F, 0x060), 0)}
CG_WALL_ROWS = range(0, 10)           # Cherrygrove rows the wall takes at columns 40-41 (its cliff's rows 7-9 included)
CG_WALL_ID0 = 596                     # first metatile id after Cherrygrove's secondary's own 84 (512-595)
# The seam forest: the route's tree lattice (2x2 roots every two columns and rows, crown one row north, so
# the crowns overlap) runs on through the band and Cherrygrove's north forest on both sides of the road,
# in place of the band's copies of Cherrygrove's three-row tree rows. Band roots (native frame) and
# Cherrygrove's (its own frame); the ground under them is Cherrygrove's lawn, or its road's right rim in
# Cherrygrove column 46.
BAND_ROOTS = [(x, y) for y in (98, 100, 102) for x in (0, 2) + tuple(range(11, 36, 2))]
CG_ROOTS = [(x, y) for y in (0, 2, 4) for x in range(-1, 38, 2)] + [(x, 0) for x in range(46, 70, 2)]
CG_RIGHT_RIM = 46
def band_woods(x):
    return x < min(BAND_KIT) or x >= 11
def forest_ground(cx, cy):
    """Cherrygrove metatile under the seam forest at Cherrygrove cell (cx, cy) (cy < 0: the band)."""
    if cx == CG_RIGHT_RIM:
        return (0x032, 0x026)[cy % 2]
    return ((0x034, 0x033), (0x028, 0x027))[cy % 2][cx % 2]
def pad_source(x, y):
    cx = x + CG_OFFSET
    return BLOSSOM.get(cx, cx), (y - PAD0) % 3

def woods_mask(cells):
    """Native cells that are woods: HGSS woods, and the columns west of HGSS column 0 (the far side of
    its west wall). The south padding is Cherrygrove's band, not traced."""
    m = np.zeros((H, W), bool)
    for hz in range(HH):
        for hx in range(HW):
            x, y = to_map(hx, hz)
            m[y, x] = cells[hz][hx]['lab'] == 'F'
    for x in range(COL0):                            # columns west of HGSS column 0: rock's outer side, woods
        m[:HH + ROW0, x] = True
    return m

def tree_roots(woods, cells):
    """The largest set of non-overlapping 2x2 roots on woods cells (Route 43's integer program).
    Roots end above the south padding. Ties prefer HGSS's own trunk-detected roots."""
    from scipy.optimize import milp, LinearConstraint, Bounds
    from scipy.sparse import lil_matrix
    detected = set()
    for hz in range(1, HH):
        hx = 0
        while hx < HW:
            if cells[hz][hx]['lab'] == 'F' and cells[hz][hx]['material'] == 'tree01_un':
                x1 = hx
                while x1 < HW and cells[hz][x1]['lab'] == 'F' and cells[hz][x1]['material'] == 'tree01_un':
                    x1 += 1
                detected |= {to_map(tx, hz - 1) for tx in range(hx, x1 - 1, 2)}
                hx = x1
            else:
                hx += 1
    wd = lambda x, y: 0 <= x < W and 0 <= y < H and woods[y, x]
    def allowed(x, y):
        return y + 1 < PAD0 and all(wd(x + dx, y + dy) for dx in (0, 1) for dy in (0, 1))
    cand = [(x, y) for y in range(0, H - 1) for x in range(W - 1) if allowed(x, y)]
    foot = lambda x, y: [(x + dx, y + dy) for dx in (0, 1) for dy in (0, 1)]
    crown = lambda x, y: []
    cells_used = sorted({c for x, y in cand for c in foot(x, y) + crown(x, y) if wd(*c)})
    index = {p: i for i, p in enumerate(cells_used)}
    nr, nc = len(cand), len(cells_used)
    A = lil_matrix((2 * nc, nr + nc)); lo = np.full(2 * nc, -np.inf); hi = np.zeros(2 * nc)
    for j, (x, y) in enumerate(cand):
        for c in foot(x, y):
            if c in index:
                A[index[c], j] = 1
        for c in foot(x, y) + crown(x, y):
            if c in index:
                A[nc + index[c], j] = -1
    for i in range(nc):
        hi[i] = 1; lo[i] = 0
        A[nc + i, nr + i] = 1; hi[nc + i] = 0
    def cw(x, y):
        if x < COL0 and y < HH + ROW0:
            return 0.5                                   # west of HGSS column 0: never seen, leftovers go here
        inner = all(not (0 <= x + dx < W and 0 <= y + dy < H) or woods[y + dy, x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        return 1.25 if inner else 1.0
    # Ties: HGSS's own trunk-detected roots; west of HGSS column 0, even columns, the column pairs of
    # Cherrygrove's forest band below.
    pref = lambda x, y: 0.01 * ((x, y) in detected) + 0.005 * (x < COL0 and x % 2 == 0)
    weight = np.concatenate([np.array([-pref(x, y) for x, y in cand]), -np.array([cw(*c) for c in cells_used])])
    res = milp(weight, constraints=LinearConstraint(A.tocsr(), lo, hi), integrality=np.ones(nr + nc), bounds=Bounds(0, 1),
               options=dict(time_limit=600))
    assert res.x is not None, res.message
    return sorted((cand[j] for j in range(len(cand)) if res.x[j] > 0.5), key=lambda t: (t[1], t[0])), sorted(detected)

# --------------------------------------------------------------------------- grid
CODES = {'g': 'lawn', 'd': 'dirt road', 'f': 'lawn with flowers', 'l': 'light lawn patch', 'G': 'tall grass (G15)',
         't': 'tree root (T01)', 'o': 'woods cell no root fits: blocked lawn under the woods edge',
         'k': 'woods cell under the crown of the tree south of it (blocked)',
         'L': 'jump ledge south', 'Q': 'jump ledge west', 'E': 'jump ledge east', 'J': 'ledge end (blocked)',
         '~': 'pond water (Surf)', '^': 'stairs', 'R': 'rock (terrace, FRLG faces)', 'H': 'house', 'D': 'house door',
         'n': 'fence', 's': 'sign', 'c': 'cuttable tree (object)', 'X': 'other blocked',
         'P': "Cherrygrove's north forest band (its metatiles, south padding)", 'p': "Cherrygrove's road in the band"}
# Rows 0-1 (north padding) repeat HGSS row 0, its stairs as road.

def material_grid(cells, woods, roots, events):
    rooted = {(x + dx, y + dy) for x, y in roots for dx in (0, 1) for dy in (0, 1)}
    crowns = {(x + dx, y - 1) for x, y in roots for dx in (0, 1)} - rooted
    cut = {to_map(*o['cell']) for o in events['objects'] if o['sprite'] == 'SPRITE_TREE'}
    grid = [['?'] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            hx, hz = to_hgss(x, y)
            c = cells[hz][hx] if 0 <= hz < HH and 0 <= hx < HW else None
            if y >= PAD0:
                ch = 'R' if x in WALL_COLS else 'p' if x in ROAD_COLS else 't' if band_woods(x) else 'P'
            elif y < ROW0 and not woods[y, x]:
                top = cells[0][hx]['lab']
                ch = 'd' if top == '^' else top
            elif (x, y) in cut:
                ch = 'c'
            elif woods[y, x]:
                ch = 't' if (x, y) in rooted else 'k' if (x, y) in crowns else 'o'
            elif c['lab'] in 'GLQEJ~^RHDnsX':
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

SHEETS = [(0, 0, W, 26), (0, 25, W, 51), (0, 50, W, 77), (0, 76, W, H)]

def main(phg):
    OUT.mkdir(parents=True, exist_ok=True); OEV.mkdir(parents=True, exist_ok=True)
    events = json.loads((SRC / 'hgss-events.json').read_text())
    rinfo = json.loads((SRC / 'hgss/hgss-render.json').read_text())
    cells = ledger(phg, rinfo, events)
    woods = woods_mask(cells)
    roots, detected = tree_roots(woods, cells)
    grid = material_grid(cells, woods, roots, events)
    (OUT / 'ledger.json').write_text(json.dumps(dict(
        note=f'Per HGSS cell (row hz, column hx): permission type/collision, label, ground. Native cell = (hx+{COL0}, hz+{ROW0}).',
        cells=cells)) + '\n')
    (OUT / 'trees.json').write_text(json.dumps(dict(
        note='Native 2x2 tree roots (top-left cell; crown row, trunk row). T01 draws its crown one row north of the root.',
        roots=roots, hgss_trunk_detected=detected), indent=0) + '\n')
    (OUT / 'material-grid.txt').write_text(
        f'# Route 30 native material grid ({W}x{H}), one code per 16x16 cell. Native = HGSS + ({COL0}, {ROW0}); '
        f'{COL0} rock-side columns west, {NORTH_PAD} padding rows north (HGSS row 0, its stairs as road), {SOUTH_PAD} padding rows south.\n' +
        ''.join(f'#   {k}  {v}\n' for k, v in CODES.items()) +
        '#   x: ' + ''.join(str(x % 10) for x in range(W)) + '\n' +
        ''.join(f'{y:03d}   ' + ''.join(row) + '\n' for y, row in enumerate(grid)))
    perm = np.load(SRC / 'hgss/hgss-permissions.npz')
    (OUT / 'traversal.json').write_text(json.dumps(dict(
        note='Decoded HGSS foot access per HGSS cell: type byte and collision bit 0x80 (land_data permissions).',
        cells=[dict(hx=hx, hz=hz, type=int(perm['types'][hz, hx]), collision=int(perm['collision'][hz, hx]),
                    foot={0x3B: 'ledge_south', 0x39: 'ledge_west', 0x38: 'ledge_east', 0x3E: 'ledge_corner', 0x69: 'door'}.get(
                        int(perm['types'][hz, hx]), 'blocked' if perm['collision'][hz, hx] & 0x80 else 'open'))
               for hz in range(HH) for hx in range(HW)])) + '\n')
    ref = np.array(Image.open(SRC / 'hgss/hgss-reference-true-heights.png').convert('RGB'))
    for i, (x0, y0, x1, y1) in enumerate(SHEETS, 1):
        numbered(ref, x0, y0, x1, y1, 2, title=f'HGSS Route 30 (decoded), native cells x{x0}-{x1 - 1}, y{y0}-{y1 - 1}',
                 origin=(COL0, ROW0)).save(OEV / f'hgss-numbered-{i}.png')
        numbered(ref, x0, y0, x1, y1, 2, grid=grid, title=f'Material grid over HGSS, native cells x{x0}-{x1 - 1}, y{y0}-{y1 - 1}',
                 origin=(COL0, ROW0)).save(OEV / f'grid-over-hgss-{i}.png')
    from collections import Counter
    print('codes', dict(Counter(ch for r in grid for ch in r)), 'roots', len(roots))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
