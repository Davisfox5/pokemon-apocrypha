"""Mahogany Town: register the decoded HGSS reference and trace it square by square.

    python3 tools/gba/maps/mahogany/trace.py PHG_CHECKOUT

Step 1 of docs/GBA_MAP_RECONSTRUCTION.md. The geographic authority is HGSS Mahogany's own
map data, decoded from pret/pokeheartgold's packed archives (land_data chunk 85: terrain
mesh, 32x32 permission grid, building placements; zone events T28), not a screenshot.
Registration is exact: HGSS tile (x, z) of the chunk is native cell (x, y), 16 px per
cell, origin (0, 0), no crop or expansion.

Outputs (gba/art/mahogany-town/source/trace/):
    roles.npz        per pixel, from HGSS's terrain mesh rendered at its own heights
                     (trees left out so the rock and ground behind them are complete):
                     role 0 ground, 1 rock plateau top (and flat mountain wall caps), 2 front face (facing south),
                     3 side face facing east, 4 side face facing west, 5 rear face
                     (facing north); top material (lawn or rock) above each face;
                     ground material (lawn / dirt / flowers) from the flat top-down view
    material-grid.txt  editable 32x32 material and structure grid (one code per cell)
    traversal.json   per-cell foot access from the decoded permissions
    trees.json       HGSS tree footprints (2x2, top-left cell)
and evidence/trace/: numbered reference sheets of the decoded HGSS render, the role map
and the material grid over the reference.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hgss_render as R                              # noqa: E402
import elements as E                                 # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/mahogany-town'
SRC, EV = ART / 'source', ART / 'evidence'
OUT, OEV = SRC / 'trace', EV / 'trace'
W = H = 32
PX = 16
TREES = ('tree01gs', 'tree01_un', 'tree01_re')
FACES = ('wall01_d', 'wall01_g')
WALLS = ('wall01_d', 'wall01_g', 'wall01_h')
GROUND, TOP, FRONT, EAST, WEST, REAR = range(6)
ROLE_NAMES = ['ground', 'rock top', 'front face (south)', 'side face (east)', 'side face (west)', 'rear face (north)']

# --------------------------------------------------------------------------- roles
def face_role(world):
    """Outward horizontal direction of a steep triangle (the mesh winds every face outward)."""
    p = np.array(world, float)
    n = np.cross(p[1] - p[0], p[2] - p[0])
    nx, nz = n[0], n[2]
    if abs(nz) >= abs(nx):
        return FRONT if nz > 0 else REAR
    return EAST if nx > 0 else WEST

def render_roles(phg):
    """HGSS's terrain at its own heights (hgss_render's projection, fronts snapped to whole
    8 px rows), trees left out, each pixel tagged with its role."""
    R.SNAP = True
    land, tex0, models, chunks, meta = R.load(phg)
    cv = R.Canvas(W * PX, H * PX)
    role = np.zeros((H * PX, W * PX), np.uint8)
    drawn = np.zeros((H * PX, W * PX), bool)
    for c in chunks:
        ch = R.hgss_map.MapChunk.parse(land[c['land']])
        model = R.mdlview.Model(ch.model)
        ox, oz = c['cx'] * 32, c['cz'] * 32
        place = lambda x, y, z: (x + 16 + ox, y, z + 16 + oz)
        mats = {}
        for mid, verts in model.faces():
            mat = mats.setdefault(mid, R.Material(model, mid, tex0))
            if mat.name in TREES or mat.tex is None:
                continue
            world = [place(*v[0]) for v in verts]
            ref = R.reference_height(world, None)
            steep = any(r < w[1] - 1e-6 for r, w in zip(ref, world))
            pw = np.array(world, float)
            nrm = np.cross(pw[1] - pw[0], pw[2] - pw[0])
            ny = abs(nrm[1]) / (np.linalg.norm(nrm) + 1e-9)
            if mat.name in WALLS and ny < 0.95:
                code = face_role(world)            # every sloped wall triangle, bevels included
            elif mat.name in WALLS:
                code = TOP if mat.name == 'wall01_d' else GROUND   # flat wall caps: mountain rim / lawn rim
            else:
                code = face_role(world) if steep else (TOP if mat.name == 'cliff01gs' else GROUND)
            scr = [(X * PX, (Z - (Y - r)) * PX) for (X, Y, Z), r in zip(world, ref)]
            dep = [Z + (Y - r) + 0.01 * Y for (X, Y, Z), r in zip(world, ref)]
            uv = [v[1] for v in verts]
            before = cv.depth.copy()
            for a, b, d in ([(0, 1, 2)] if len(verts) == 3 else [(0, 1, 2), (0, 2, 3)]):
                cv.tri([scr[a], scr[b], scr[d]], [uv[a], uv[b], uv[d]], [dep[a], dep[b], dep[d]], mat, code,
                       hgt=(world[a][1], world[b][1], world[d][1]), steep=steep)
            changed = cv.depth != before
            role[changed] = code
            drawn |= changed
    names = list(R.MATERIAL_NAMES)
    return role, cv.rgb.astype(np.uint8), cv.mat, names, drawn

def ground_material(phg):
    """Flat top-down HGSS ground per pixel: 0 lawn, 1 dirt road, 2 flowers."""
    h, mat, names, rgb = E.topdown(phg)
    nm = np.array(names + ['none'])
    m = nm[np.where(mat >= 0, mat, len(names))]
    out = np.zeros(m.shape, np.uint8)
    out[np.char.startswith(m, 'road')] = 1
    out[m == 'flower03'] = 2
    return out, h

def top_material(role, ground):
    """For each face pixel, what lies on top of the wall: lawn (a grass-topped wall) or the
    rock plateau. A face's top edge lies away from the direction it faces: a front (facing
    south) has its top up the screen, a rear (facing north) down the screen, a side facing
    west has its top to the east and a side facing east to the west. Read from the face
    across its run to the first non-face pixel in that direction."""
    out = np.zeros(role.shape, np.uint8)            # 0 n/a, 1 lawn, 2 rock
    h, w = role.shape
    step = {FRONT: (-1, 0), REAR: (1, 0), WEST: (0, 1), EAST: (0, -1)}
    for k, (dy, dx) in step.items():
        ys, xs = np.nonzero(role == k)
        for y, x in zip(ys, xs):
            yy, xx = y, x
            while 0 <= yy < h and 0 <= xx < w and role[yy, xx] == k:
                yy += dy; xx += dx
            above = role[yy, xx] if 0 <= yy < h and 0 <= xx < w else TOP
            out[y, x] = 2 if above == TOP else 1
    return out

# --------------------------------------------------------------------------- cell grid
CODES = {
    'g': 'lawn', 'd': 'dirt road', 'f': 'lawn with white flowers', 'r': 'rock plateau top',
    'F': 'rock front face (mountain)', 'E': 'rock side facing east', 'W': 'rock side facing west', 'N': 'rock rear rim',
    'w': 'low wall, front (grass-topped)', 'e': 'low wall side facing east', 'x': 'low wall side facing west',
    'n': 'low wall rear rim', 'L': 'jump ledge south', 'Q': 'jump ledge west', 'J': 'ledge corner (blocked)',
    't': 'tree root (T01)', 'B': 'building / prop footprint', 'C': 'Pokemon Center (C06)', 'G': 'Route 43 gatehouse',
    's': 'sign',
}

def cell_grid(role, topmat, gmat, perm, trees, events, buildings):
    types, coll = perm['types'], perm['collision']
    grid = [['?'] * W for _ in range(H)]
    tree_cells = {(tx + dx, ty + dy) for tx, ty in trees for dx in (0, 1) for dy in (0, 1)}
    signs = {tuple(s['cell']) for s in events['signs']}
    for y in range(H):
        for x in range(W):
            sl = np.s_[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX]
            r, tm, gm = role[sl], topmat[sl], gmat[sl]
            share = np.bincount(r.ravel(), minlength=6) / 256.0
            t = int(types[y, x])
            if (x, y) in signs:
                c = 's'
            elif t == 0x3B:
                c = 'L'
            elif t == 0x39:
                c = 'Q'
            elif (x, y) in tree_cells:
                c = 't'
            elif share[FRONT:].sum() >= 0.25:
                k = int(np.argmax(share[FRONT:])) + FRONT
                lawn_top = (tm[r >= FRONT] == 1).mean() > 0.5
                c = {FRONT: 'wF', EAST: 'eE', WEST: 'xW', REAR: 'nN'}[k][0 if lawn_top else 1]
            elif share[TOP] >= 0.5:
                c = 'r'
            else:
                frac = np.bincount(gm.ravel(), minlength=3) / 256.0
                c = 'f' if frac[2] > 0.15 else 'd' if frac[1] > frac[0] else 'g'
            grid[y][x] = c
    # Buildings, the gate and the Center from the decoded placements' blocked footprints.
    for b in buildings:
        kind = b['kind']
        if kind in ('sign',):
            continue
        for (x, y) in b['cells']:
            if grid[y][x] not in 'gdf':           # rock, walls, ledges, trees and signs keep their own code
                continue
            grid[y][x] = {'center': 'C', 'gate': 'G'}.get(kind, 'B')
    # The blocked corner where the west and south ledge runs meet.
    for y in range(H):
        for x in range(W):
            if coll[y, x] & 0x80 and grid[y][x] in 'gd' and (
                    (y + 1 < H and grid[y + 1][x] == 'Q') or (y > 0 and grid[y - 1][x] == 'Q')) and (
                    (x + 1 < W and grid[y][x + 1] == 'L')):
                grid[y][x] = 'J'
    return grid

def building_cells(perm, rinfo, events):
    """Blocked cells inside each decoded building footprint (model bounds), by kind."""
    coll = perm['collision']
    out = []
    kinds = {35: 'gate', 40: 'center', 134: 'house', 138: 'gym', 249: 'tower', 136: 'antenna_tree',
             29: 'sign', 31: 'sign', 33: 'sign'}
    for b in rinfo['buildings']:
        k = kinds.get(b['model'])
        if k is None:
            continue
        x0, z0, x1, z1 = b['footprint']
        cells = [(x, y) for y in range(max(0, int(np.floor(z0))), min(H, int(np.ceil(z1))))
                 for x in range(max(0, int(np.floor(x0))), min(W, int(np.ceil(x1)))) if coll[y, x] & 0x80]
        out.append(dict(kind=k, model=b['model'], pos=b['pos'], footprint=b['footprint'], cells=cells))
    return out

# --------------------------------------------------------------------------- sheets
def numbered(img, x0, y0, x1, y1, scale, grid=None, title=''):
    w, h = (x1 - x0) * PX * scale, (y1 - y0) * PX * scale
    big = Image.fromarray(img[y0 * PX:y1 * PX, x0 * PX:x1 * PX]).resize((w, h), Image.Resampling.NEAREST).convert('RGB')
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

ROLE_COLOURS = np.array([(0, 0, 0, 0), (200, 160, 120, 255), (220, 60, 60, 255), (60, 140, 230, 255), (240, 200, 40, 255),
                         (150, 70, 200, 255)], np.uint8)

def main(phg):
    OUT.mkdir(parents=True, exist_ok=True); OEV.mkdir(parents=True, exist_ok=True)
    perm = np.load(SRC / 'hgss/hgss-permissions.npz')
    events = json.loads((SRC / 'hgss-events.json').read_text())
    rinfo = json.loads((SRC / 'hgss/hgss-render.json').read_text())
    role, rgb, mat, names, drawn = render_roles(phg)
    gmat, height = ground_material(phg)
    topmat = top_material(role, gmat)
    cells = E.ledger(phg)
    trees = E.tree_footprints(cells)
    blds = building_cells(perm, rinfo, events)
    grid = cell_grid(role, topmat, gmat, perm, trees, events, blds)
    np.savez_compressed(OUT / 'roles.npz', role=role, top_material=topmat, ground_material=gmat, drawn=drawn)
    (OUT / 'material-grid.txt').write_text(
        '# Mahogany Town material and structure grid, one code per native 16x16 cell (x across, y down).\n'
        '# Traced from decoded HGSS land_data chunk 85 (trace.py), then reviewed. Codes:\n' +
        ''.join(f'#   {k}  {v}\n' for k, v in CODES.items()) +
        '#   x: ' + ''.join(str(x % 10) for x in range(W)) + '\n' +
        ''.join(f'{y:02d}    ' + ''.join(row) + '\n' for y, row in enumerate(grid)))
    (OUT / 'trees.json').write_text(json.dumps(dict(note='HGSS tree footprints, 2x2 cells, top-left cell (crown row, trunk row).',
                                                    trees=trees), indent=1) + '\n')
    (OUT / 'buildings.json').write_text(json.dumps(blds, indent=1) + '\n')
    types, coll = perm['types'], perm['collision']
    trav = [dict(x=x, y=y, hgss_type=int(types[y, x]), hgss_collision=int(coll[y, x]),
                 foot=('ledge_south' if types[y, x] == 0x3B else 'ledge_west' if types[y, x] == 0x39 else
                       'blocked' if coll[y, x] & 0x80 else 'warp' if types[y, x] in (0x69, 0x6E) else 'open'))
            for y in range(H) for x in range(W)]
    (OUT / 'traversal.json').write_text(json.dumps(dict(
        note='Foot access per cell from the decoded HGSS permissions (land_data chunk 85): type byte and collision bit '
             '0x80. Doors (0x69) and the gate warps (0x6E) are listed as warps. This is decoded original collision.',
        cells=trav)) + '\n')
    # Reference sheets: decoded HGSS render at true heights, numbered; role map; grid over the reference.
    ref = np.array(Image.open(SRC / 'hgss/hgss-reference-true-heights.png').convert('RGB'))
    for i, (x0, y0, x1, y1) in enumerate([(0, 0, 16, 16), (16, 0, 32, 16), (0, 16, 16, 32), (16, 16, 32, 32)], 1):
        numbered(ref, x0, y0, x1, y1, 3, title=f'HGSS Mahogany, decoded land_data 85 at true heights; cells x{x0}-{x1 - 1}, y{y0}-{y1 - 1}').save(OEV / f'hgss-numbered-{i}.png')
        numbered(ref, x0, y0, x1, y1, 3, grid=grid, title=f'Material grid over HGSS; cells x{x0}-{x1 - 1}, y{y0}-{y1 - 1}').save(OEV / f'grid-over-hgss-{i}.png')
    rv = rgb.copy()
    rc = ROLE_COLOURS[role]
    a = rc[..., 3] > 0
    rv[a] = (rv[a].astype(int) * 0.35 + rc[a][:, :3].astype(int) * 0.65).astype(np.uint8)
    numbered(rv, 0, 0, 32, 32, 2, title='Rock roles: tan top, red front, blue east side, yellow west side, purple rear').save(OEV / 'roles.png')
    print('cells', {k: sum(r.count(k) for r in grid) for k in CODES}, 'trees', len(trees))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
