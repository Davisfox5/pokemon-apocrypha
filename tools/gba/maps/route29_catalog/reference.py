"""Route 29: trace decoded HGSS Route 29 square by square (step 1 of docs/GBA_MAP_RECONSTRUCTION.md).

    python3 tools/gba/maps/route29_catalog/reference.py PHG_CHECKOUT

The authority is HGSS Route 29's own map data (EVERYWHERE matrix cells (18..20, 12), land_data
permissions, terrain mesh and zone events R29), decoded and rendered 1:1 at 16 px per tile by
hgss_render.py. This is the process the owner accepted for Mahogany Town and Route 43.

Native frame: HGSS tile (hx, hz) is native cell (hx + COL0, hz + ROW0), 16 px, no scaling.
  * ROW0 = 3 keeps Cherrygrove's connection offset 0 and New Bark's offset 6 on their roads.
  * COL0 = 4 puts every HGSS sign and tall-grass cell outside the 8-column seam windows and keeps
    HGSS's two-column tree pairs on the windows' pairs; the four added west columns continue
    HGSS column 0 toward Cherrygrove.
  * HGSS rows 29-31 are the solid forest border; the accepted Cherrygrove coast (cliff and sea)
    replaces them from native row 32 down. Nothing walkable changes there.

Writes gba/art/route29-catalog/source/trace/{ledger.json, material-grid.txt, traversal.json,
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
ART = ROOT / 'gba/art/route29-catalog'
SRC, EV = ART / 'source', ART / 'evidence'
OUT, OEV = SRC / 'trace', EV / 'trace'
HW, HH = 96, 32                       # HGSS Route 29
COL0, ROW0 = 4, 3
EAST_PAD = 2                          # two columns east of HGSS column 95 keep HGSS's east grass outside the window
W, H = HW + COL0 + EAST_PAD, 51       # native map
COAST_ROW = HH - 3 + ROW0             # native row 32: the coast replaces HGSS rows 29-31 (forest border)
WINDOW = 8                            # seam window: drawn by the neighbouring town with its own tilesets
PX = 16
TREES = ('tree01gs', 'tree01_un', 'tree01_re')
LIGHT = ('grass02', 'grass02_r', 'grass02_a')
FLOWERS = ('flower01', 'flower02', 'flower03')

def to_map(hx, hz): return hx + COL0, hz + ROW0
def to_hgss(x, y): return x - COL0, y - ROW0
def in_window(x): return x < WINDOW or x >= W - WINDOW

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

def ledger(phg):
    """One label per HGSS cell from the decoded permissions, plus its flat ground material.
    F woods (0x06), G tall grass (0x02), L jump south (0x3B), Q jump west (0x39), E jump east
    (0x38), J the blocked ledge corner (0x3E), X other blocked, . open."""
    h, mat, names, rgb = topdown(phg)
    perm = np.load(SRC / 'hgss/hgss-permissions.npz')
    types, coll = perm['types'], perm['collision']
    nm = np.array(names + ['none'])
    m = np.where(mat >= 0, mat, len(names)).reshape(HH, PX, HW, PX).transpose(0, 2, 1, 3).reshape(HH, HW, PX * PX)
    labels = {0x06: 'F', 0x02: 'G', 0x3B: 'L', 0x39: 'Q', 0x38: 'E', 0x3E: 'J'}
    cells = []
    for hz in range(HH):
        row = []
        for hx in range(HW):
            u, cnt = np.unique(nm[m[hz, hx]], return_counts=True)
            frac = {str(k): int(v) for k, v in zip(u, cnt)}
            t, k = int(types[hz, hx]), int(coll[hz, hx])
            lab = labels.get(t) or ('X' if k & 0x80 else '.')
            sand = sum(v for n, v in frac.items() if n.startswith('road'))
            row.append(dict(lab=lab, type=t, collision=k, blocked=bool(k & 0x80),
                            floor='sand' if sand > 128 else 'grass', material=str(u[np.argmax(cnt)]),
                            flowers=sum(frac.get(n, 0) for n in FLOWERS), light=sum(frac.get(n, 0) for n in LIGHT)))
        cells.append(row)
    return cells

# --------------------------------------------------------------------------- trees
def woods_mask(cells):
    """Native cells that are woods: HGSS woods above the coast, and the three padding rows above
    HGSS row 0 and the padding columns west of HGSS column 0 wherever their neighbour is woods."""
    m = np.zeros((H, W), bool)
    for hz in range(HH):
        for hx in range(HW):
            x, y = to_map(hx, hz)
            if y < COAST_ROW:
                m[y, x] = cells[hz][hx]['lab'] == 'F'
    for y in range(ROW0):
        m[y, COL0:] = True
    for x in range(COL0):
        m[:COAST_ROW, x] = m[:COAST_ROW, COL0]
    for x in range(W - EAST_PAD, W):
        m[:COAST_ROW, x] = m[:COAST_ROW, W - EAST_PAD - 1]
    m[:ROW0, :COL0] = True
    # The HGSS gatehouse is wider than G01a: its footprint column east of G01a closes with trees.
    for x, y in GATE_EXTRA:
        m[y, x] = True
    gx, gy = GATE_ORIGIN
    m[gy:gy + 8, gx:gx + 6] = False                 # G01a itself, its roof included
    return m

# G01a is 6x8 cells; its doorway (2,7)-(3,7) stands on HGSS's gate warps (50,5)/(51,5), so its origin
# is HGSS (48,-2) and it spans HGSS columns 48-53. HGSS's model spans 48.0-54.25, which leaves its
# footprint column 54 (rows 0-6) outside G01a: trees close it.
GATE_ORIGIN = (48 + COL0, -2 + ROW0)
GATE_EXTRA = [(54 + COL0, hz + ROW0) for hz in range(0, 7)]

def tree_roots(woods, cells):
    """The largest set of non-overlapping 2x2 roots on woods cells (Route 43's integer program),
    outside the seam windows. Ties prefer HGSS's own trunk-detected roots."""
    from scipy.optimize import milp, LinearConstraint, Bounds
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
    # Row -1 (above the map) counts as woods, so the top padding rows fill with whole trees.
    wd = lambda x, y: y < 0 or (y < COAST_ROW and woods[y, x])
    def allowed(x, y):
        if not all(wd(x + dx, y + dy) for dx in (0, 1) for dy in (0, 1)):
            return False
        west, east = x < WINDOW, x + 1 >= W - WINDOW
        if west or east:
            # Seam windows hold primary metatiles only, which a town also draws with its own tileset:
            # a pair never straddles the map edge, and the crown row above a root is woods (the primary's
            # crown tiles draw under the player, so a crown may not hang over a walkable cell there).
            if (west and x % 2) or (east and (W - 1 - (x + 1)) % 2):
                return False
            if not (wd(x, y - 1) and wd(x + 1, y - 1)):
                return False
        return True
    cand = [(x, y) for y in range(-1, COAST_ROW - 1) for x in range(W - 1) if allowed(x, y)]
    # Integer program: roots x_j (binary), covered cells c_i (binary). Footprints never overlap. A woods cell
    # counts as covered when a root's footprint holds it, or, inside a seam window, when it is the blocked
    # crown row of a root (the towns' own forest edges: a crown over a solid cell).
    from scipy.sparse import lil_matrix
    foot = lambda x, y: [(x + dx, y + dy) for dx in (0, 1) for dy in (0, 1)]
    crown = lambda x, y: [(x + dx, y - 1) for dx in (0, 1)] if (x < WINDOW or x + 1 >= W - WINDOW) else []
    cells_used = sorted({c for x, y in cand for c in foot(x, y) + crown(x, y) if c[1] >= 0 and wd(*c)})
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
        hi[i] = 1; lo[i] = 0                             # footprints never overlap
        A[nc + i, nr + i] = 1; hi[nc + i] = 0            # covered only if something covers it
    def solid(x, y):
        # never walked on: woods, the gatehouse, the coast, beyond the map
        if not (0 <= x < W) or y < 0 or y >= COAST_ROW:
            return True
        gx, gy = GATE_ORIGIN
        return wd(x, y) or (gx <= x < gx + 6 and gy <= y < gy + 8)
    def cw(x, y):
        # Cover interior woods first: a cell left without a root then lies on a lawn-facing edge, where HGSS
        # itself shows crown overhang, never as a lawn gap inside the forest.
        inner = all(solid(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        return 1.25 if inner else 1.0
    weight = np.concatenate([np.array([-0.01 * ((x, y) in detected) for x, y in cand]), -np.array([cw(*c) for c in cells_used])])
    res = milp(weight, constraints=LinearConstraint(A.tocsr(), lo, hi), integrality=np.ones(nr + nc), bounds=Bounds(0, 1),
               options=dict(time_limit=600))
    assert res.x is not None, res.message
    return sorted((cand[j] for j in range(len(cand)) if res.x[j] > 0.5), key=lambda t: (t[1], t[0])), sorted(detected)

# --------------------------------------------------------------------------- grid
CODES = {'g': 'lawn', 'd': 'dirt road', 'f': 'lawn with flowers', 'l': 'light lawn patch', 'G': 'tall grass (G15)',
         't': 'tree root (T01)', 'o': 'woods cell no root fits (crown overhang): open lawn', 'k': 'woods cell under the crown of the tree south of it (blocked)',
         'L': 'jump ledge south', 'Q': 'jump ledge west', 'E': 'jump ledge east', 'J': 'ledge corner (blocked)',
         'B': 'Route 46 gatehouse (G01a)', 'D': 'gatehouse door', 's': 'route sign (P14)', 'c': 'cuttable tree (object)',
         'X': 'other blocked', '~': 'coast (carried)'}

def material_grid(cells, woods, roots, events, gate_cells):
    rooted = {(x + dx, y + dy) for x, y in roots for dx in (0, 1) for dy in (0, 1)}
    crowns = {(x + dx, y - 1) for x, y in roots for dx in (0, 1)} - rooted
    signs = {to_map(*s['cell']) for s in events['signs'] if s['bg_type'] == 1}
    cut = {to_map(*o['cell']) for o in events['objects'] if o['sprite'] == 'SPRITE_TREE'}
    doors = {to_map(*w['cell']) for w in events['warps']}
    grid = [['?'] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            hx, hz = to_hgss(x, y)
            c = cells[hz][min(max(0, hx), HW - 1)] if 0 <= hz < HH else None
            if y >= COAST_ROW:
                ch = '~'
            elif (x, y) in doors:
                ch = 'D'
            elif ((x, y) in gate_cells and (x, y) not in GATE_EXTRA) or (
                    GATE_ORIGIN[0] <= x < GATE_ORIGIN[0] + 6 and GATE_ORIGIN[1] <= y < GATE_ORIGIN[1] + 8):
                ch = 'B'
            elif (x, y) in signs:
                ch = 's'
            elif (x, y) in cut:
                ch = 'c'
            elif woods[y, x]:
                ch = 't' if (x, y) in rooted else 'k' if (x, y) in crowns else 'o'
            elif c['lab'] in 'GLQEJX':
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

def gate_footprint(rinfo, cells):
    """Blocked HGSS cells inside the decoded gatehouse model footprint (model 35)."""
    out = set()
    for b in rinfo['buildings']:
        if b['model'] != 35:
            continue
        x0, z0, x1, z1 = b['footprint']
        for hz in range(max(0, int(np.floor(z0))), min(HH, int(np.ceil(z1)))):
            for hx in range(max(0, int(np.floor(x0))), min(HW, int(np.ceil(x1)))):
                if cells[hz][hx]['blocked']:
                    out.add(to_map(hx, hz))
    return out

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

SHEETS = [(0, 0, 26, 35), (25, 0, 51, 35), (50, 0, 77, 35), (76, 0, 102, 35)]

def main(phg):
    OUT.mkdir(parents=True, exist_ok=True); OEV.mkdir(parents=True, exist_ok=True)
    events = json.loads((SRC / 'hgss-events.json').read_text())
    rinfo = json.loads((SRC / 'hgss/hgss-render.json').read_text())
    cells = ledger(phg)
    woods = woods_mask(cells)
    roots, detected = tree_roots(woods, cells)
    gate = gate_footprint(rinfo, cells)
    grid = material_grid(cells, woods, roots, events, gate)
    (OUT / 'ledger.json').write_text(json.dumps(dict(
        note='Per HGSS cell (row hz, column hx): permission type/collision, label, ground. Native cell = (hx+4, hz+3).',
        cells=cells)) + '\n')
    (OUT / 'trees.json').write_text(json.dumps(dict(
        note='Native 2x2 tree roots (top-left cell; crown row, trunk row). T01 draws its crown one row north of the root.',
        roots=roots, hgss_trunk_detected=detected), indent=0) + '\n')
    (OUT / 'material-grid.txt').write_text(
        '# Route 29 native material grid (102x51), one code per 16x16 cell. Native = HGSS + (4, 3); two padding columns east.\n' +
        ''.join(f'#   {k}  {v}\n' for k, v in CODES.items()) +
        '#   x: ' + ''.join(str(x % 10) for x in range(W)) + '\n' +
        ''.join(f'{y:02d}    ' + ''.join(row) + '\n' for y, row in enumerate(grid)))
    perm = np.load(SRC / 'hgss/hgss-permissions.npz')
    (OUT / 'traversal.json').write_text(json.dumps(dict(
        note='Decoded HGSS foot access per HGSS cell: type byte and collision bit 0x80 (land_data permissions).',
        cells=[dict(hx=hx, hz=hz, type=int(perm['types'][hz, hx]), collision=int(perm['collision'][hz, hx]),
                    foot={0x3B: 'ledge_south', 0x39: 'ledge_west', 0x38: 'ledge_east', 0x3E: 'ledge_corner', 0x6E: 'warp'}.get(
                        int(perm['types'][hz, hx]), 'blocked' if perm['collision'][hz, hx] & 0x80 else 'open'))
               for hz in range(HH) for hx in range(HW)])) + '\n')
    ref = np.array(Image.open(SRC / 'hgss/hgss-reference-true-heights.png').convert('RGB'))
    for i, (x0, y0, x1, y1) in enumerate(SHEETS, 1):
        numbered(ref, x0, y0, x1, y1, 3, title=f'HGSS Route 29 (decoded), native cells x{x0}-{x1 - 1}, y{y0}-{y1 - 1}',
                 origin=(COL0, ROW0)).save(OEV / f'hgss-numbered-{i}.png')
        numbered(ref, x0, y0, x1, y1, 3, grid=grid, title=f'Material grid over HGSS, native cells x{x0}-{x1 - 1}, y{y0}-{y1 - 1}',
                 origin=(COL0, ROW0)).save(OEV / f'grid-over-hgss-{i}.png')
    from collections import Counter
    print('codes', dict(Counter(ch for r in grid for ch in r)), 'roots', len(roots))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
