"""Fuchsia City: trace decoded HGSS Fuchsia square by square (steps 1 and 2 of docs/GBA_MAP_RECONSTRUCTION.md).

    python3 tools/gba/maps/fuchsia_city/hgss_render.py PHG gba/art/kanto-fuchsia/source/hgss
    python3 tools/gba/maps/fuchsia_city/hgss_events.py PHG gba/art/kanto-fuchsia/source/hgss-events.json
    python3 tools/gba/maps/fuchsia_city/reference.py PHG

The authority is HGSS Fuchsia's own map data (EVERYWHERE matrix cells (37..38, 12..13), land_data
permissions, terrain mesh, building placements and zone events T08), decoded and rendered 1:1 at 16 px
per tile by hgss_render.py: the Route 29/30 catalog process, as Route 32's reference.py.

Native frame: HGSS tile (hx, hz) is native cell (hx, hz), 16 px, no scaling, no padding. 64 x 64.
Route 18 lies west of rows 32-63, Route 15 east of rows 32-63 (through its gatehouse), Route 19 south
of columns 0-31 (through its gatehouse). None is built, so no seam rows are borrowed.

Each cell gets two independent records:
  * material and structure (material-grid.txt, ledger.json): what stands there and on what ground
  * traversal (traversal.json): HGSS's foot access from the permission bytes

Writes gba/art/kanto-fuchsia/source/trace/{ledger.json, material-grid.txt, traversal.json, trees.json,
objects.json} and evidence/trace/ numbered sheets of the HGSS render with the grid.
"""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'route32_native')]
import hgss_render as R                              # noqa: E402
import reference as R32                              # noqa: E402  (numbered(): the sheet drawer)

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/kanto-fuchsia'
SRC, EV = ART / 'source', ART / 'evidence'
OUT, OEV = SRC / 'trace', EV / 'trace'
HW = HH = W = H = 64
PX = 16
LIGHT = ('grass02', 'grass02_r', 'grass02_a')
ROAD = ('sek_fe03', 'sek_fe03_r')
FLOWERS = ('flower01', 'flower02')
WALLS = ('wall01_g', 'wall01_d', 'cliff01gs')
LEDGE_MATERIALS = ('allpeakgs', 'allpeak_pgs')
WATER = ('pond_un', 'pond_on', 'pond_edge', 'pond_line')
HEDGE = ('sek_teien',)
BED = ('sek_flower', 'f_dodai', 'f_dodai_a', 'flower_sp1')
BUILDINGS = {295: 'pal_park_hall', 39: 'mart', 300: 'gym', 297: 'house_red', 298: 'house_pink', 40: 'pokemon_center',
             299: 'warden_house', 247: 'route15_gatehouse'}
DOOR_MODELS = {15: 'sliding door (Mart, Center)', 16: 'Gym door', 306: "Warden's door", 307: 'house door'}
SIGN_MODELS = {29: 'city sign', 30: 'house sign', 31: 'notice board', 33: 'Gym sign'}
LAMP_MODEL = 333

def topdown(phg):
    """HGSS terrain drawn flat from straight above: per-pixel height, material and colour."""
    R.AREA_BANK, R.HEADER_ID = 16, 56
    land, tex0, models, chunks, meta = R.load(phg)
    cv = R.Canvas(HW * PX, HH * PX)
    for c in chunks:
        ch = R.hgss_map.MapChunk.parse(land[c['land']])
        ox, oz = c['cx'] * 32, c['cz'] * 32
        R.draw_model(cv, R.mdlview.Model(ch.model), tex0, lambda x, y, z, ox=ox, oz=oz: (x + 16 + ox, y, z + 16 + oz), -1, None, flat=True)
    h = np.nan_to_num(cv.height, nan=float(np.nanmin(cv.height)))
    return h, cv.mat, list(R.MATERIAL_NAMES), cv.rgb.astype(np.uint8)

GATE19 = {(x, y) for x in range(17, 23) for y in (62, 63)}   # the Route 19 gatehouse's north end (its model is on Route 19's chunk)
PEN_FRONT_ROW = 26                    # the white picket rail across the front of the four north pens

def floor_of(frac):
    tot = lambda g: sum(frac.get(n, 0) for n in g)
    return 'road' if tot(ROAD) > 128 else 'light' if tot(LIGHT) > 128 else 'grass'

def reach(cells, start=(30, 25)):
    """Cells a player on foot reaches from the main road (HGSS permissions; ledges count one way)."""
    seen, todo = set(), [start]
    while todo:
        x, y = todo.pop()
        if (x, y) in seen or not (0 <= x < HW and 0 <= y < HH):
            continue
        c = cells[y][x]
        if c['blocked'] and c['type'] not in (0x38, 0x39, 0x3B) or c['type'] == 0x10:
            continue
        seen.add((x, y))
        todo += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return seen

def footprint_cells(b):
    x0, z0, x1, z1 = b['footprint']
    return [(hx, hz) for hz in range(max(0, int(np.floor(z0))), min(HH, int(np.ceil(z1))))
            for hx in range(max(0, int(np.floor(x0))), min(HW, int(np.ceil(x1))))]

def ledger(td, rinfo, events):
    """One label per HGSS cell from the decoded permissions, its flat materials and heights.
    F woods (0x06), ~ pond (0x10, Surf), L/Q/E jump south/west/east (0x3B/0x39/0x38), D door (0x69),
    C the hall's entrance steps (0x6E), w gatehouse doorway (0x6C/0x6F), H building, s sign, i lamp,
    h hedge, b pen bed or planter, x fence, R rock (face: T top, E/S/W/N by downhill direction),
    J ledge end, X other blocked, . open."""
    h, mat, names, rgb = td
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
    level, low = np.median(hc, -1), hc.min(-1)
    wallpx = np.isin(nm[m], WALLS)
    peak = np.where(wallpx.any(-1), np.where(wallpx, hc, -1e9).max(-1), hc.max(-1))
    # the lifted render's materials: fences and hedges are thin from above, their faces show in it
    lz = np.load(SRC / 'hgss/hgss-ground-materials.npz')
    ln = [str(n) for n in lz['names']]
    lifted = lambda group: np.isin(lz['material'], [ln.index(n) for n in group if n in ln]).reshape(HH, PX, HW, PX).sum((1, 3))
    fence_px, hedge_px = lifted(('fence_a', 'fence_b')), lifted(HEDGE)
    house = np.full((HH, HW), '', object)
    lamp = set()
    for b in rinfo['buildings']:
        if b['model'] in BUILDINGS:
            for hx, hz in footprint_cells(b):
                house[hz, hx] = BUILDINGS[b['model']]
        elif b['model'] == LAMP_MODEL:
            x0, z0, x1, z1 = b['footprint']
            lamp.add((int((x0 + x1) / 2), int(z0)))
    signs = {tuple(s['cell']) for s in events['signs'] if s['bg_type'] == 1}
    labels = {0x06: 'F', 0x10: '~', 0x3B: 'L', 0x39: 'Q', 0x38: 'E', 0x69: 'D', 0x6E: 'C', 0x6C: 'w', 0x6F: 'w'}
    cells = []
    for hz in range(HH):
        row = []
        for hx in range(HW):
            u, cnt = np.unique(nm[m[hz, hx]], return_counts=True)
            frac = {str(k): int(v) for k, v in zip(u, cnt)}
            dominant = str(u[np.argmax(cnt)])
            t, k = int(types[hz, hx]), int(coll[hz, hx])
            blocked = bool(k & 0x80)
            tot = lambda g: sum(frac.get(n, 0) for n in g)
            if t in labels:
                lab = labels[t]
            elif (hx, hz) in signs:
                lab = 's'
            elif (hx, hz) in lamp and blocked:
                lab = 'i'
            elif blocked and (house[hz, hx] or (hx, hz) in GATE19):
                lab = 'H'
            elif blocked and dominant in LEDGE_MATERIALS:
                lab = 'J'
            elif blocked and tot(WALLS) > 64:
                lab = 'R'
            elif blocked and tot(WATER) > 96:
                lab = '~'
            elif blocked and (tot(HEDGE) > 48 or hedge_px[hz, hx] > 96):
                lab = 'h'
            elif blocked and tot(BED) > 48:
                lab = 'b'
            elif blocked and fence_px[hz, hx] > 12:
                lab = 'x'
            elif blocked and floor_of(frac) == 'light' and hz == PEN_FRONT_ROW and types[hz - 1, hx] != 0x06:
                lab = 'p'
            elif blocked:
                lab = 'X'
            else:
                lab = '.'
            face = ''
            if lab == 'R':
                a = np.degrees(np.arctan2(ddy[hz, hx], ddx[hz, hx])) % 360
                face = 'ESWN'[int(((a + 45) % 360) // 90)] if share[hz, hx] > 0.25 else 'T'
            floor = floor_of(frac)
            row.append(dict(lab=lab, face=face, type=t, collision=k, blocked=blocked, floor=floor, material=dominant,
                            level=round(float(level[hz, hx]), 2), ground=round(float(low[hz, hx] if t == 0x06 else level[hz, hx]), 2),
                            peak=round(float(peak[hz, hx]), 2), house=house[hz, hx], flowers=tot(FLOWERS), road=tot(ROAD),
                            light=tot(LIGHT), water=tot(WATER), fence=int(fence_px[hz, hx]), hedge=int(hedge_px[hz, hx])))
        cells.append(row)
    return cells

def tree_roots(td, woods):
    """HGSS's own trees: each is a 2x2 block of woods cells whose lower row carries the trunk's under-shade
    (tree01_un, decoded flat), read left to right along each trunk row (Route 32's method)."""
    h, mat, names, rgb = td
    un = (mat == names.index('tree01_un')).reshape(HH, PX, HW, PX).mean((1, 3)) > 0.3
    used = np.zeros((H, W), bool)
    roots = []
    for y in range(1, H):
        x = 0
        while x < W - 1:
            if un[y, x] and all(woods[y - dy, x + dx] and not used[y - dy, x + dx] for dx in (0, 1) for dy in (0, 1)):
                roots.append((x, y - 1)); used[y - 1:y + 1, x:x + 2] = True; x += 2
            else:
                x += 1
    return sorted(roots, key=lambda t: (t[1], t[0]))

CODES = {'g': 'lawn (grass01gs)', 'l': 'pale pen lawn (grass02)', 'd': 'maroon stone road (sek_fe03)',
         'f': 'lawn with flowers (flower01/02)', 't': 'tree root (2x2)', 'k': 'woods cell under the crown of the tree south of it',
         'o': 'woods cell no root fits: blocked lawn under the woods edge', '~': 'pond (Surf)', 'h': 'pen hedge (sek_teien)',
         'b': "a pen's inside: flower bed, soil bed or planter (sek_flower, f_dodai, flower_sp1)", 'x': 'fence (fence_a)', 'i': 'street lamp (model 333)',
         's': 'sign', 'R': 'rock (terrace, one level)', 'L': 'jump ledge south', 'Q': 'jump ledge west', 'E': 'jump ledge east',
         'J': 'ledge end (blocked)', 'H': 'building', 'D': 'door', 'C': "the hall's entrance steps (warp)",
         'w': 'gatehouse doorway (warp)', 'c': 'cuttable tree (object)', 'a': 'Apricorn tree (object)', 'p': 'pen front rail (white pickets between planter posts)',
         'u': 'lawn no one reaches on foot (north of the hall; the fenced pond yard, Surf only)', 'X': 'other blocked'}

def material_grid(cells, woods, roots, events):
    rooted = {(x + dx, y + dy) for x, y in roots for dx in (0, 1) for dy in (0, 1)}
    crowns = {(x + dx, y - 1) for x, y in roots for dx in (0, 1)} - rooted
    obj = {tuple(o['cell']): {'SPRITE_TREE': 'c', 'SPRITE_BONGURI': 'a'}[o['sprite']] for o in events['objects']
           if o['sprite'] in ('SPRITE_TREE', 'SPRITE_BONGURI')}
    walk = reach(cells)
    grid = [['?'] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            c = cells[y][x]
            if c['lab'] == '.' and (x, y) not in walk:
                # open in HGSS's permissions but walled in: inside a building's outline, inside a pen, or cut off
                near = [cells[b][a]['lab'] for a, b in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)) if 0 <= a < W and 0 <= b < H]
                c['enclosed'] = True
                grid[y][x] = 'H' if c['house'] else 'b' if PEN_ROWS[0] <= y <= PEN_ROWS[1] else 'u'
                continue
            if (x, y) in obj:
                ch = obj[(x, y)]
            elif woods[y, x]:
                ch = 't' if (x, y) in rooted else 'k' if (x, y) in crowns else 'o'
            elif c['lab'] != '.':
                ch = c['lab']
            elif c['floor'] == 'road':
                ch = 'd'
            elif c['floor'] == 'light':
                ch = 'l'
            elif c['flowers'] > 24:
                ch = 'f'
            else:
                ch = 'g'
            grid[y][x] = ch
    return grid

PEN_ROWS = (23, 31)                   # rows holding the pens' insides

SHEETS = [(0, 0, 32, 32), (32, 0, 64, 32), (0, 32, 32, 64), (32, 32, 64, 64)]

def main(phg):
    OUT.mkdir(parents=True, exist_ok=True); OEV.mkdir(parents=True, exist_ok=True)
    events = json.loads((SRC / 'hgss-events.json').read_text())
    rinfo = json.loads((SRC / 'hgss/hgss-render.json').read_text())
    td = topdown(phg)
    cells = ledger(td, rinfo, events)
    woods = np.array([[c['lab'] == 'F' for c in row] for row in cells])
    roots = tree_roots(td, woods)
    grid = material_grid(cells, woods, roots, events)
    (OUT / 'ledger.json').write_text(json.dumps(dict(
        note='Per HGSS cell (row hz, column hx): permission type/collision, label, ground. Native cell = HGSS cell.',
        cells=cells)) + '\n')
    (OUT / 'trees.json').write_text(json.dumps(dict(
        note='2x2 tree roots (top-left cell; crown row, trunk row), each on an HGSS tree.', roots=roots), indent=0) + '\n')
    (OUT / 'material-grid.txt').write_text(
        f'# Fuchsia City material grid ({W}x{H}), one code per 16x16 cell. Native = HGSS + (0, 0).\n' +
        ''.join(f'#   {k}  {v}\n' for k, v in CODES.items()) +
        '#   x: ' + ''.join(str(x % 10) for x in range(W)) + '\n' +
        ''.join(f'{y:03d}   ' + ''.join(row) + '\n' for y, row in enumerate(grid)))
    perm = np.load(SRC / 'hgss/hgss-permissions.npz')
    foot = {0x3B: 'ledge_south', 0x39: 'ledge_west', 0x38: 'ledge_east', 0x69: 'door', 0x6C: 'gate_warp', 0x6F: 'gate_warp',
            0x6E: 'stair_warp', 0x10: 'surf'}
    (OUT / 'traversal.json').write_text(json.dumps(dict(
        note='Decoded HGSS foot access per HGSS cell: type byte and collision bit 0x80 (land_data permissions).',
        cells=[dict(hx=hx, hz=hz, type=int(perm['types'][hz, hx]), collision=int(perm['collision'][hz, hx]),
                    foot=foot.get(int(perm['types'][hz, hx]), 'blocked' if perm['collision'][hz, hx] & 0x80 else 'open'))
               for hz in range(HH) for hx in range(HW)])) + '\n')
    placed = [dict(model=b['model'], kind=BUILDINGS.get(b['model']) or DOOR_MODELS.get(b['model']) or SIGN_MODELS.get(b['model'])
                   or ('street lamp' if b['model'] == LAMP_MODEL else 'unlisted'), footprint=[round(v, 2) for v in b['footprint']])
              for b in rinfo['buildings']]
    (OUT / 'objects.json').write_text(json.dumps(dict(
        note="HGSS's building placements (model id, kind, footprint in cells) and zone events.", models=placed,
        warps=events['warps'], signs=events['signs'], objects=events['objects']), indent=1) + '\n')
    ref = np.array(Image.open(SRC / 'hgss/hgss-reference-true-heights.png').convert('RGB'))
    for i, (x0, y0, x1, y1) in enumerate(SHEETS, 1):
        R32.numbered(ref, x0, y0, x1, y1, 2, title=f'HGSS Fuchsia City (decoded), cells x{x0}-{x1 - 1}, y{y0}-{y1 - 1}').save(OEV / f'hgss-numbered-{i}.png')
        R32.numbered(ref, x0, y0, x1, y1, 2, grid=grid, title=f'Material grid over HGSS, cells x{x0}-{x1 - 1}, y{y0}-{y1 - 1}').save(OEV / f'grid-over-hgss-{i}.png')
    print('codes', dict(Counter(ch for r in grid for ch in r)), 'roots', len(roots))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
