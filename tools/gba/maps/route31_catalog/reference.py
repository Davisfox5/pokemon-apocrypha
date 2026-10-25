"""Route 31: trace decoded HGSS Route 31 square by square (step 1 of docs/GBA_MAP_RECONSTRUCTION.md).

    python3 tools/gba/maps/route31_catalog/reference.py PHG_CHECKOUT

The authority is HGSS Route 31's own map data (EVERYWHERE matrix cells (16..17, 8), land_data
permissions, terrain mesh and zone events R31), decoded and rendered 1:1 at 16 px per tile by
hgss_render.py: the Route 29 catalog process (Mahogany / Route 43), as Route 30.

Native frame: HGSS tile (hx, hz) is native cell (hx, hz), 16 px, no scaling. Route 30 joins its south
edge with its column 0 at Route 31's column 27 (Route 30 is HGSS Route 30 + (5, 2); HGSS Route 30's
column 0 is HGSS Route 31's column 32). The Violet gate is a building (warps), not a connection.

Writes gba/art/route31-catalog/source/trace/{ledger.json, material-grid.txt, traversal.json,
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
ART = ROOT / 'gba/art/route31-catalog'
SRC, EV = ART / 'source', ART / 'evidence'
OUT, OEV = SRC / 'trace', EV / 'trace'
HW, HH = 64, 32                       # HGSS Route 31
COL0, ROW0 = 0, 0
W, H = HW, HH
PAD0 = H                              # no padding rows
PX = 16
R30_OFFSET = -27                      # Route 30's "up" connection: Route 31 column 0 is Route 30 column -27
CG_OFFSET = 35
# Lawn and road textures are Cherrygrove's 32 px blocks in Cherrygrove's own pixel frame: Route 31 column x
# is Cherrygrove column x + 28 + 35 - 4... resolved through Route 30: Route 31 x = Route 30 x + 28, Route 30
# x = Cherrygrove x - 35; Route 31's rows sit 32 + 104 rows above Cherrygrove's.
XPHASE, YPHASE = ((CG_OFFSET - R30_OFFSET) * PX) % 32, (-(H + 104) * PX) % 32
TREES = ('tree01gs', 'tree01_un', 'tree01_re')
LIGHT = ('grass02', 'grass02_r', 'grass02_a')
FLOWERS = ('flower01', 'flower02', 'flower03')
WALLS = ('wall01_g', 'wall01_d', 'cliff01gs')
LEDGE_MATERIALS = ('allpeakgs', 'allpeak_pgs')
GATE_MODEL = 36                       # HGSS's Route 31 / Violet gatehouse
SIGN_MODELS = {32: 'P14', 31: 'P13'}  # green route sign, gray plaque (Dark Cave)

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
    F woods (0x06), G tall grass (0x02), ~ water (0x10), L/Q/E jump south/west/east (0x3B/0x39/0x38),
    J blocked ledge corner (0x3E), W gate warp (0x6D), V cave warp (0x6E), ^ stairs (collision 6, 'slope'),
    B gatehouse, C cave mouth, s sign, R rock (face: T top, E/S/W/N by downhill direction, Route 43's
    decode), X other blocked, . open."""
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
        if b['model'] == GATE_MODEL:
            x0, z0, x1, z1 = b['footprint']
            for hz in range(max(0, int(np.floor(z0))), min(HH, int(np.ceil(z1)))):
                for hx in range(max(0, int(np.floor(x0))), min(HW, int(np.ceil(x1)))):
                    house[hz, hx] = 'gate'
    signs = {tuple(s['cell']) for s in events['signs'] if s['bg_type'] == 1}
    labels = {0x06: 'F', 0x02: 'G', 0x10: '~', 0x3B: 'L', 0x39: 'Q', 0x38: 'E', 0x3E: 'J', 0x6D: 'W', 0x6E: 'V'}
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
                lab = 'B'
            elif blocked and frac.get('cavehole', 0) > 32:
                lab = 'C'
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
def woods_mask(cells):
    """Native cells that are woods: HGSS woods."""
    m = np.zeros((H, W), bool)
    for hz in range(HH):
        for hx in range(HW):
            x, y = to_map(hx, hz)
            m[y, x] = cells[hz][hx]['lab'] == 'F'
    return m

def tree_roots(woods, cells):
    """The largest set of non-overlapping 2x2 roots on woods cells (Route 43's integer program).
    Ties prefer HGSS's own trunk-detected roots."""
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
        inner = all(not (0 <= x + dx < W and 0 <= y + dy < H) or woods[y + dy, x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        return 1.25 if inner else 1.0
    weight = np.concatenate([np.array([-0.01 * ((x, y) in detected) for x, y in cand]), -np.array([cw(*c) for c in cells_used])])
    res = milp(weight, constraints=LinearConstraint(A.tocsr(), lo, hi), integrality=np.ones(nr + nc), bounds=Bounds(0, 1),
               options=dict(time_limit=600))
    assert res.x is not None, res.message
    return sorted((cand[j] for j in range(len(cand)) if res.x[j] > 0.5), key=lambda t: (t[1], t[0])), sorted(detected)

# --------------------------------------------------------------------------- grid
CODES = {'g': 'lawn', 'd': 'dirt road', 'f': 'lawn with flowers', 'l': 'light lawn patch', 'G': 'tall grass (G15)',
         't': 'tree root (T01)', 'o': 'woods cell no root fits: blocked lawn under the woods edge',
         'k': 'woods cell under the crown of the tree south of it (blocked)',
         'L': 'jump ledge south', 'Q': 'jump ledge west', 'E': 'jump ledge east', 'J': 'ledge end (blocked)',
         '~': 'pond water (Surf)', '^': 'stairs', 'R': 'rock (terrace, FRLG faces)', 'B': 'Violet gatehouse (G02)',
         'W': 'gatehouse doorway (warp)', 'C': 'cave mouth', 'V': 'Dark Cave entrance (warp)',
         's': 'sign', 'c': 'cuttable tree (object)', 'X': 'other blocked'}

def material_grid(cells, woods, roots, events):
    rooted = {(x + dx, y + dy) for x, y in roots for dx in (0, 1) for dy in (0, 1)}
    crowns = {(x + dx, y - 1) for x, y in roots for dx in (0, 1)} - rooted
    cut = {to_map(*o['cell']) for o in events['objects'] if o['sprite'] == 'SPRITE_TREE'}
    grid = [['?'] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            hx, hz = to_hgss(x, y)
            c = cells[hz][hx] if 0 <= hz < HH and 0 <= hx < HW else None
            if (x, y) in cut:
                ch = 'c'
            elif woods[y, x]:
                ch = 't' if (x, y) in rooted else 'k' if (x, y) in crowns else 'o'
            elif c['lab'] in 'GLQEJ~^RBCWVsX':
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

SHEETS = [(0, 0, 22, H), (21, 0, 43, H), (42, 0, W, H)]

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
        f'# Route 31 native material grid ({W}x{H}), one code per 16x16 cell. Native = HGSS.\n' +
        ''.join(f'#   {k}  {v}\n' for k, v in CODES.items()) +
        '#   x: ' + ''.join(str(x % 10) for x in range(W)) + '\n' +
        ''.join(f'{y:03d}   ' + ''.join(row) + '\n' for y, row in enumerate(grid)))
    perm = np.load(SRC / 'hgss/hgss-permissions.npz')
    (OUT / 'traversal.json').write_text(json.dumps(dict(
        note='Decoded HGSS foot access per HGSS cell: type byte and collision bit 0x80 (land_data permissions).',
        cells=[dict(hx=hx, hz=hz, type=int(perm['types'][hz, hx]), collision=int(perm['collision'][hz, hx]),
                    foot={0x3B: 'ledge_south', 0x39: 'ledge_west', 0x38: 'ledge_east', 0x3E: 'ledge_corner', 0x6D: 'gate warp', 0x6E: 'cave warp'}.get(
                        int(perm['types'][hz, hx]), 'blocked' if perm['collision'][hz, hx] & 0x80 else 'open'))
               for hz in range(HH) for hx in range(HW)])) + '\n')
    ref = np.array(Image.open(SRC / 'hgss/hgss-reference-true-heights.png').convert('RGB'))
    for i, (x0, y0, x1, y1) in enumerate(SHEETS, 1):
        numbered(ref, x0, y0, x1, y1, 2, title=f'HGSS Route 31 (decoded), native cells x{x0}-{x1 - 1}, y{y0}-{y1 - 1}',
                 origin=(COL0, ROW0)).save(OEV / f'hgss-numbered-{i}.png')
        numbered(ref, x0, y0, x1, y1, 2, grid=grid, title=f'Material grid over HGSS, native cells x{x0}-{x1 - 1}, y{y0}-{y1 - 1}',
                 origin=(COL0, ROW0)).save(OEV / f'grid-over-hgss-{i}.png')
    from collections import Counter
    print('codes', dict(Counter(ch for r in grid for ch in r)), 'roots', len(roots))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
