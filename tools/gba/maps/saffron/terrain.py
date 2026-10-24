"""Saffron City ten years on as Gen 3 elements: ledger and terrain composer.

    python3 tools/gba/maps/saffron/terrain.py ENGINE_CHECKOUT PHG_CHECKOUT

Saffron follows HGSS's city plan (the owner's call, 2026-10-24): its blocks of paving, the
asphalt road rings round them, its apartment blocks, Silph Co. at the centre. Every cell
gets a material and structure label from HGSS's own map data (map header 59, zone T11:
top-down materials, permissions, building placements), and each element takes the Gen 3
piece that does its job, in HGSS's colours (Olivine's method, olivine_elements/elements.py):

    road        FRLG Saffron's paving bricks (General_Frlg/SaffronCity 0x2E9) in HGSS's
                asphalt mauves (ymb_fe01)
    sidewalk    Slateport's paving nine-slice in HGSS's orange paving (ymb_fe02): its
                scalloped rim onto the lawns is HGSS's paving edge (ymb_fe02_r)
    kerb        HGSS's kerb (ymb_fe01_r) the Gen 3 way: a band of small bricks on the road's
                side wherever the road meets the sidewalk, in the kerb's browns
    grass       Cherrygrove's (CherrygrovePrimary)
    trees       Cherrygrove's tree (HGSS's tree01_re at 1:1), one per HGSS tree on its 2x2
                grid, its crown rising a row over its block; one standing on a building's
                front is left out (clear_fronts)
    manholes    HGSS's manhole cover (ymb_hole) at 1:1, flat on the road
    hydrants    HGSS's fire hydrant (ymb_shouka) at 1:1, standing in its cell
    railings    HGSS's blue hoop railing (ymb_fence_a) and its posts (ymb_fence_c), at 1:1
    lamps       HGSS's street lamps (330), art.py

Buildings are art.py's (HGSS's models at C06's angle, the Dojo and Silph's lab wing
made from HGSS's parts), a few moved a tile column clear of a neighbour (NUDGE); the Center
is the owner-locked C06 and the Mart the shared Johto Mart, on HGSS's Center and Mart doors.
Everything that stands is drawn in painter's order
with no background of its own; where two kinds of art meet in one 8x8 tile, one takes the
top layer and the other is drawn into the bottom layer over its ground (split).

    source/ledger.json, ledger.png, compose.npz
    evidence/terrain.png, compare.png
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
import olivine                                  # noqa: E402
import hgss_render as R                         # noqa: E402
R.HEADER_ID, R.AREA_BANK = 59, 12               # MAP_SAFFRON, area data bank 12
OE = olivine.mod('elements')                    # Olivine's: trees, Cherrygrove ground, Slateport paving
import modelkit as K                            # noqa: E402

ART = ROOT / 'gba/art/saffron-kanto'
SRC, EV = ART / 'source', ART / 'evidence'
W, H = 64, 64
DIRS = OE.DIRS
TREES = ('tree01_re', 'tree01_un', 'tree01gs')
FENCES = ('ymb_fence_a', 'ymb_fence_b', 'ymb_fence_c', 'ymb_fence_cx', 'ymb_fence_d', 'ymb_fence_ax', 'ymb_fence_dx')
FLOORS = dict(ymb_fe01='road', ymb_fe01_r='road', ymb_fe02='walk', ymb_fe02_r='walk', ymb_hole='road', ymb_shouka='walk',
              grass01gs='grass')

# --------------------------------------------------------------------------- ledger
def topdown(phg):
    return OE.topdown(phg)

def ledger(phg, td):
    h, mat, names, rgb = td
    perm = np.load(SRC / 'hgss/hgss-permissions.npz')
    types, coll = perm['types'], perm['collision']
    nm = np.array(names + ['none'])
    m = np.where(mat >= 0, mat, len(names)).reshape(H, 16, W, 16).transpose(0, 2, 1, 3).reshape(H, W, 256)
    blds = json.loads((SRC / 'hgss/hgss-render.json').read_text())['buildings']
    owner = np.full((H, W), -1, int)
    for i, b in enumerate(blds):
        if b['model'] in (330,):                                  # street lamps stand on the sidewalk
            continue
        x0, z0, x1, z1 = b['footprint']
        owner[max(0, int(np.floor(z0))):int(np.ceil(z1)), max(0, int(np.floor(x0))):int(np.ceil(x1))] = i
    trees = OE.tree_grid(mat, names, rgb)
    # fences, manholes and hydrants from the lifted render, where their faces show
    lift = np.load(SRC / 'hgss/hgss-ground-materials.npz')
    lnames = list(lift['names'])
    def count(*ks):
        sel = np.isin(lift['material'], [lnames.index(k) for k in ks if k in lnames])
        return sel.reshape(H, 16, W, 16).sum(axis=(1, 3))
    fence = count(*FENCES)
    cells = []
    for y in range(H):
        row = []
        for x in range(W):
            u, cnt = np.unique(nm[m[y, x]], return_counts=True)
            frac = {str(k): int(v) for k, v in zip(u, cnt)}
            blocked = bool(coll[y, x] & 0x80)
            treepx = sum(frac.get(k, 0) for k in TREES)
            ground = {k: v for k, v in frac.items() if k in FLOORS}
            floor = FLOORS[max(ground, key=ground.get)] if ground else 'grass'
            if blocked and treepx >= 128:
                lab = 'F'
            elif blocked and fence[y, x] > 24:
                lab = 'f'
            elif blocked and owner[y, x] >= 0:
                lab = 'X'
            elif blocked:
                lab = 'B'
            else:
                lab = '.'
            row.append(dict(lab=lab, floor=floor, type=int(types[y, x]), blocked=blocked, owner=int(owner[y, x]),
                            fence=int(fence[y, x]), frac=frac))
        cells.append(row)
    tree_at = {}
    for x0, y0 in trees:
        for yy in (y0, y0 + 1):
            for xx in (x0, x0 + 1):
                if 0 <= xx < W and 0 <= yy < H:
                    tree_at[(xx, yy)] = (x0, y0)
    for (x, y), t in tree_at.items():
        c = cells[y][x]
        c['tree'] = list(t)
        if c['lab'] in ('F', '.', 'B'):
            c['lab'] = 'F'
        c['floor'] = 'grass'
    x, y0, y1 = LAB_RAIL
    for y in range(y0, y1 + 1):
        if cells[y][x]['lab'] == 'f':
            cells[y][x]['lab'] = 'B'
    return cells, trees

def save_ledger(cells):
    slim = [[{k: v for k, v in c.items() if k != 'frac'} for c in row] for row in cells]
    (SRC / 'ledger.json').write_text(json.dumps(dict(
        note='Per-cell element ledger from HGSS land_data (map header 59). lab: F tree, X building or prop, f railing, '
             'B blocked plain ground, . open. floor: road (asphalt), walk (sidewalk paving), grass.',
        cells=[[c['lab'] + c['floor'][0] for c in row] for row in cells], detail=slim)) + '\n')
    img = Image.new('RGB', (W * 12, H * 12), (20, 20, 24)); d = ImageDraw.Draw(img)
    col = dict(F=(40, 110, 50), X=(90, 90, 90), f=(70, 110, 230), B=(60, 60, 70))
    fl = dict(road=(140, 120, 140), walk=(230, 170, 70), grass=(110, 210, 160))
    for y in range(H):
        for x in range(W):
            c = cells[y][x]
            d.rectangle((x * 12, y * 12, x * 12 + 11, y * 12 + 11), fill=col.get(c['lab']) or fl[c['floor']])
    img.save(SRC / 'ledger.png')

# --------------------------------------------------------------------------- ground
ROAD = {166: (140, 123, 132), 167: (132, 115, 123), 168: (123, 107, 115)}   # FRLG 0x2E9's three shades -> ymb_fe01's
ROAD_MID = 0x2E9
WALK = {6 * 16 + 2: (214, 165, 66), 6 * 16 + 3: (181, 132, 41)}            # Slateport's stone, joint -> ymb_fe02's
KERB = dict(l=(173, 140, 115), m=(148, 115, 99), d=(123, 107, 115))         # ymb_fe01_r's browns; its shadow the road's dark
FENCE = [(99, 132, 173), (57, 90, 148), (41, 66, 107)]                      # ymb_fence's blues, light to dark
HYDRANT = [(231, 132, 0), (198, 90, 0), (140, 49, 0), (123, 107, 115)]      # ymb_shouka's reds; its outline the road's dark
PAVED = ('road', 'walk')

def road_block(engine):
    rgb, key = OE.gen3_meta(engine, 'general_frlg', 'saffron_city_frlg', ROAD_MID)
    return np.array([[ROAD[int(k)] for k in row] for row in key], np.uint8)

def ground(cells, tex, engine):
    """Bottom layer: Cherrygrove's grass; the road FRLG Saffron's bricks in HGSS's mauves; the
    sidewalk Slateport's paving per 8x8 quadrant, each quadrant facing a lawn taking the
    nine-slice piece its two edges call for (its rim on the paving side, the lawn beyond it
    the plainest grass block), a quadrant facing the road or a building plain paving."""
    ys, xs = np.mgrid[0:H * 16, 0:W * 16]
    out = tex['grass'][ys % 32, xs % 32].copy()
    floor = np.array([[c['floor'] for c in row] for row in cells])
    road, pave, green = road_block(engine), OE.paving(engine), OE.plain(tex, 'grass')
    lawn = lambda x, y: 0 <= x < W and 0 <= y < H and floor[y, x] == 'grass'
    for y in range(H):
        for x in range(W):
            cell = np.s_[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
            if floor[y, x] == 'road':
                out[cell] = road
            elif floor[y, x] == 'walk':
                lo = {k: lawn(x + dx, y + dy) for k, (dx, dy) in DIRS.items()}
                blk = np.zeros((16, 16, 3), np.uint8)
                for qy in (0, 1):
                    v = ('N', 'S')[qy] if lo['n'] and lo['s'] else 'N' if lo['n'] else 'S' if lo['s'] else 'M'
                    for qx in (0, 1):
                        h = ('W', 'E')[qx] if lo['w'] and lo['e'] else 'W' if lo['w'] else 'E' if lo['e'] else 'M'
                        sl = np.s_[qy * 8:qy * 8 + 8, qx * 8:qx * 8 + 8]
                        key = pave[(v, h)][sl]
                        blk[sl] = np.where((key == OE.LAWN)[..., None], green[sl],
                                           np.array([WALK.get(int(k), WALK[6 * 16 + 2]) for k in key.ravel()], np.uint8).reshape(8, 8, 3))
                out[cell] = blk
    return out

# HGSS's kerb (ymb_fe01_r) the Gen 3 way: on the road's side of every road-sidewalk edge, a
# 5 px band: a lit lip, three rows of 8 px bricks, a shadow onto the road.
BAND = ['l', 'm', 'm', 'm', 'd']

def kerbs(out, cells):
    fl = lambda x, y: cells[y][x]['floor'] if 0 <= x < W and 0 <= y < H else ''
    col = lambda k: np.array(KERB[k], np.uint8)
    for y in range(H):
        for x in range(W):
            if fl(x, y) != 'road':
                continue
            X0, Y0 = x * 16, y * 16
            cell = out[Y0:Y0 + 16, X0:X0 + 16]
            side = {k: fl(x + dx, y + dy) == 'walk' for k, (dx, dy) in DIRS.items()}
            for k, rows in (('n', range(5)), ('s', range(15, 10, -1)), ('w', range(5)), ('e', range(15, 10, -1))):
                if not side[k]:
                    continue
                for i, r in enumerate(rows):
                    if k in 'ns':
                        cell[r, :] = col(BAND[i])
                        if 1 <= i <= 3:
                            cell[r, ::8] = col('d')
                    else:
                        cell[:, r] = col(BAND[i])
                        if 1 <= i <= 3:
                            cell[::8, r] = col('d')
            for k, (ry, rx) in dict(ne=(range(5), range(15, 10, -1)), nw=(range(5), range(5)),
                                   se=(range(15, 10, -1), range(15, 10, -1)), sw=(range(15, 10, -1), range(5))).items():
                if side[k] and not side[k[0]] and not side[k[1]]:            # an inner corner: a square of kerb
                    for i, r in enumerate(ry):
                        for j, c in enumerate(rx):
                            cell[r, c] = col(BAND[max(i, j)] if min(i, j) == 0 or max(i, j) == 4 else 'm')

def blobs(td, name):
    from scipy import ndimage
    h, mat, names, rgb = td
    if name not in names:
        return []
    lab, n = ndimage.label(mat == names.index(name))
    out = []
    for sl in ndimage.find_objects(lab):
        out.append(((sl[1].start + sl[1].stop) / 2 / 16, (sl[0].start + sl[0].stop) / 2 / 16, sl))
    return out

def manholes(out, td, phg):
    """HGSS's manhole cover (ymb_hole) at 1:1 on the road, in the road's three mauves, its
    centre on an 8 px grid point."""
    t = OE.hgss_texture(phg, 'ymb_hole', 'ymb_hole_pl')
    pal = np.array(list(ROAD.values()), int)
    a = t[..., 3] > 0
    ys, xs = np.nonzero(a)
    t = t[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    a = t[..., 3] > 0
    img = pal[((t[..., :3][..., None, :].astype(int) - pal[None, None]) ** 2).sum(-1).argmin(-1)].astype(np.uint8)
    placed = []
    for cx, cy, _ in blobs(td, 'ymb_hole'):
        X, Y = int(round(cx * 2)) * 8 - img.shape[1] // 2, int(round(cy * 2)) * 8 - img.shape[0] // 2
        out[Y:Y + img.shape[0], X:X + img.shape[1]][a] = img[a]
        placed.append([X, Y])
    return placed

def hgss_prop(phg, name, pal):
    t = OE.hgss_texture(phg, name, name + '_pl')
    a = t[..., 3] > 0
    ys, xs = np.nonzero(a)
    t = t[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()
    a = t[..., 3] > 0
    p = np.array(pal, int)
    t[..., :3] = p[((t[..., :3][..., None, :].astype(int) - p[None, None]) ** 2).sum(-1).argmin(-1)]
    t[~a] = 0
    return t

def hydrants(td, phg):
    """HGSS's fire hydrant (ymb_shouka) at 1:1, standing on the cell HGSS puts it in."""
    img = hgss_prop(phg, 'ymb_shouka', HYDRANT)
    out = []
    for cx, cy, sl in blobs(td, 'ymb_shouka'):
        x, y = int(cx), int(sl[0].stop - 1) // 16
        out.append(dict(name=f'hydrant_{x}_{y}', fam='street', img=img, X=x * 16 + (16 - img.shape[1]) // 2,
                        Y=(y + 1) * 16 - img.shape[0]))
    return out

def railings(cells, phg):
    """HGSS's blue railing at 1:1: a hoop (ymb_fence_a) per cell along an east-west run, a
    post (ymb_fence_c) per cell along a north-south run."""
    hoop, post = hgss_prop(phg, 'ymb_fence_a', FENCE), hgss_prop(phg, 'ymb_fence_c', FENCE)
    f = lambda x, y: 0 <= x < W and 0 <= y < H and cells[y][x]['lab'] == 'f'
    out = []
    for y in range(H):
        for x in range(W):
            if not f(x, y):
                continue
            img = post if (f(x, y - 1) or f(x, y + 1)) and not (f(x - 1, y) or f(x + 1, y)) else hoop
            out.append(dict(name=f'fence_{x}_{y}', fam='street', img=img, X=x * 16 + (16 - img.shape[1]) // 2,
                            Y=(y + 1) * 16 - img.shape[0]))
    return out

# --------------------------------------------------------------------------- objects
# HGSS's placements, model -> sprite (art.py). Doors belong to their buildings' sprites; the
# Fighting Dojo and the Gym are one sprite (the Dojo); HGSS's Center and Mart are the shared
# Gen 3 ones (below). Silph's lab wing stands on the lot of the apartment block east of
# Silph (254 at 37.3, 40).
MODEL_SPRITE = {252: 'apt_a', 253: 'apt_b', 254: 'apt_c', 258: 'copycat', 251: 'mrpsychic', 246: 'gate_n', 247: 'gate_e',
                256: 'station', 257: 'silph', 29: 'citysign', 31: 'board', 33: 'dojosign', 330: 'lamp'}
LAB_LOT = (37.3125, 40.0)
LAB_X, LAB_ROW = 37.5, 41                       # its centre (cells): on the block's own footprint
LAB_RAIL = (34, 30, 41)                         # HGSS's railing east of Silph (column, rows) gives way to the wing
LAB_LAMP_AT = (37.5, 34.0)                      # and the street lamp on its lot
DOJO = dict(x0=38.0, row=12)                    # art.py renders it from x 38 (cells)
# A building with a door stands with its door on HGSS's door row.
DOOR_ROW = dict(station=16, copycat=26, silph=37, mrpsychic=50, dojo=12, lab=41)
# Gen 3 sprites a few pixels wider than HGSS's footprints would overlap a neighbour; these
# move a tile column (px) so they stand clear. The station's door comes nearer HGSS's
# (10, 16), and the apartments either side of the Mart, which is wider than HGSS's, clear it
# (the one east of it tucks behind its own neighbour, as the blocks along Silph's north do).
NUDGE = dict(station_10_14=-8, apt_b_34_25=-8, apt_a_43_25=16)
SHARED = dict(pokemon_center=('pokemon-center.png', (12, 46)), poke_mart=('poke-mart.png', (36, 21)))   # C06 door (14, 50); Mart door (38, 26)
SHARED_ART = ROOT / 'gba/art/olivine-elements/source/shared-art'
SHARED_FAMILY = dict(pokemon_center='center', poke_mart='mart')
FAMILY = dict(apt_a='apt', apt_b='apt', apt_c='apt', copycat='house', mrpsychic='house', gate_n='gate', gate_e='gate',
              station='station', silph='silph', lab='silph', citysign='house', board='silph', dojosign='silph', lamp='silph')

def front_row(models, mid, z):
    m = K.R.mdlview.Model(models[mid])
    zs = [v[0][2] for matid, f in m.faces() for v in f if v[0][1] < 0.6 and K.R.Material(m, matid, m.tex).name != 'h_kage']
    return int(np.floor(z + max(zs) - 1e-6)) if zs else int(np.floor(z))

def buildings(phg):
    import art
    _, _, models, _, _ = K.R.load(phg)
    origin = json.loads((SRC / 'sprites/origins.json').read_text())
    out = []
    for b in json.loads((SRC / 'hgss/hgss-render.json').read_text())['buildings']:
        name = MODEL_SPRITE.get(b['model'])
        if not name:
            continue
        x, y, z = b['pos']
        if name == 'apt_c' and abs(x - LAB_LOT[0]) < 0.1 and abs(z - LAB_LOT[1]) < 0.1:
            continue
        if name == 'lamp' and abs(x - LAB_LAMP_AT[0]) < 0.1 and abs(z - LAB_LAMP_AT[1]) < 0.1:
            continue
        img = art.load(name)
        mx = origin[name]['model_px'][0]
        key = f'{name}_{int(x)}_{int(z)}'
        X = int(round((x * 16 - mx) / 8)) * 8 + NUDGE.get(key, 0)
        row = DOOR_ROW.get(name, front_row(models, b['model'], z))
        out.append(dict(name=key, fam=FAMILY[name], img=img, X=X, Y=(row + 1) * 16 - img.shape[0]))
    lab = art.load('lab')
    out.append(dict(name='lab', fam='silph', img=lab, X=int(LAB_X * 16) - lab.shape[1] // 2, Y=(LAB_ROW + 1) * 16 - lab.shape[0]))
    dojo = art.load('dojo')
    split = origin['dojo']['split_px']
    X, Y = int(DOJO['x0'] * 16), (DOJO['row'] + 1) * 16 - dojo.shape[0]
    west, east = dojo.copy(), dojo.copy()
    west[:, split:] = 0
    east[:, :split] = 0
    out.append(dict(name='dojo_fighting', fam='dojo_w', img=west, X=X, Y=Y))
    out.append(dict(name='dojo_psychic', fam='dojo_e', img=east, X=X, Y=Y))
    for name, (f, (ox, oy)) in SHARED.items():
        out.append(dict(name=name, fam=SHARED_FAMILY[name],
                        img=np.array(Image.open(SHARED_ART / f).convert('RGBA')), X=ox * 16, Y=oy * 16))
    return out

def standing(cells, engine, td, phg):
    built = buildings(phg)
    return clear_fronts(OE.trees(cells, engine), built) + railings(cells, phg) + hydrants(td, phg) + built

GROUND_LEVEL = ('tree', 'street')

def overlap(a, b):
    """Opaque pixels item a draws over item b's."""
    (ah, aw), (bh, bw) = a['img'].shape[:2], b['img'].shape[:2]
    y0, x0 = max(a['Y'], b['Y']), max(a['X'], b['X'])
    y1, x1 = min(a['Y'] + ah, b['Y'] + bh), min(a['X'] + aw, b['X'] + bw)
    if y1 <= y0 or x1 <= x0:
        return 0
    return int((a['img'][y0 - a['Y']:y1 - a['Y'], x0 - a['X']:x1 - a['X'], 3] > 0).__and__(
        b['img'][y0 - b['Y']:y1 - b['Y'], x0 - b['X']:x1 - b['X'], 3] > 0).sum())

def clear_fronts(trees, built):
    """A tree standing in front of a building with its canopy on the building is left out: a
    Gen 3 tree stands clear of a building's front, and the tile where the two meet would need
    the tree's greens, the building's colours and the ground's in one bank. (HGSS's row of
    trees south of the east gate stands on the plinth the Gen 3 gate is drawn with.)"""
    return [t for t in trees if not any(foot(t) // 16 > foot(b) // 16 and overlap(t, b) for b in built)]

def foot(it):
    return it['Y'] + int(np.nonzero(it['img'][..., 3].any(1))[0].max())

def stack(bottom, items, leave_out=None):
    """The finished picture: the ground, then everything standing in painter's order (by the
    row its foot stands on, north first; in one row trees and street furniture before
    buildings), each item by its own opaque pixels only. Returns the picture and, per pixel,
    the family and owner of what shows there ('' for the ground)."""
    want = bottom.copy()
    fam = np.full(bottom.shape[:2], '', '<U12')
    own = np.full(bottom.shape[:2], '', '<U24')
    order = lambda it: (foot(it) // 16, it['fam'] not in GROUND_LEVEL, foot(it), it['X'])
    for it in sorted((it for it in items if it['fam'] != leave_out), key=order):
        img, X, Y = it['img'], it['X'], it['Y']
        y0, x0 = max(Y, 0), max(X, 0)
        y1, x1 = min(Y + img.shape[0], H * 16), min(X + img.shape[1], W * 16)
        if y1 <= y0 or x1 <= x0:
            continue
        part = img[y0 - Y:y1 - Y, x0 - X:x1 - X]
        m = part[..., 3] > 0
        sl = np.s_[y0:y1, x0:x1]
        want[sl][m] = part[..., :3][m]
        fam[sl][m] = it['fam']
        own[sl][m] = it['name']
    return want, fam, own

# Where two families show in one 8x8 tile, the first here takes the top layer; the bottom
# layer there is the picture with that family left out (Olivine's split).
TOP_FIRST = ('center', 'mart', 'station', 'silph', 'dojo_w', 'dojo_e', 'apt', 'house', 'gate', 'tree', 'street')
SHARED_SRC = dict(mart=1, center=2)

def split(bottom, want, fam, tex, behind):
    out = bottom.copy()
    top = np.zeros(bottom.shape[:2] + (4,), np.uint8)
    shared = np.zeros(bottom.shape[:2] + (4,), np.uint8)
    shared_src = np.zeros(bottom.shape[:2], np.uint8)
    green = OE.plain(tex, 'grass')
    grass = np.array(sorted({tuple(c) for c in tex['grass'].reshape(-1, 3).tolist()}), np.uint8)
    mixed = {}
    for ty in range(H * 2):
        for tx in range(W * 2):
            ts = np.s_[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            f = fam[ts]
            kinds = set(np.unique(f).tolist()) - {''}
            if not kinds:
                continue
            first = min(kinds, key=TOP_FIRST.index)
            m = f == first
            dst = shared if first in SHARED_SRC else top
            dst[ts][m] = np.concatenate([want[ts][m], np.full((int(m.sum()), 1), 255, np.uint8)], 1)
            if first in SHARED_SRC:
                shared_src[ts][m] = SHARED_SRC[first]
            if ((f != '') & ~m).any():
                pic, pfam = behind(first)
                q = out[ts]
                q[:] = pic[ts]
                is_grass = (q[:, :, None, :] == grass[None, None]).all(-1).any(-1) & (pfam[ts] == '')
                q[is_grass] = green[(ty % 2) * 8:(ty % 2) * 8 + 8, (tx % 2) * 8:(tx % 2) * 8 + 8][is_grass]
                mixed[(tx, ty)] = [first] + sorted(kinds - {first})
    return out, top, shared, shared_src, mixed

def compose(engine, phg, cells, td):
    tex = OE.cherry_textures()
    bottom = ground(cells, tex, engine)
    kerbs(bottom, cells)
    holes = manholes(bottom, td, phg)
    items = standing(cells, engine, td, phg)
    want, fam, owner = stack(bottom, items)
    cache = {}
    def behind(f):
        if f not in cache:
            cache[f] = stack(bottom, items, leave_out=f)[:2]
        return cache[f]
    bottom, top, shared, shared_src, mixed = split(bottom, want, fam, tex, behind)
    return dict(bottom=bottom, top=top, shared=shared, shared_src=shared_src, owner=owner, family=fam, mixed=mixed,
                items=items, manholes=holes)

def preview(bottom, top, shared=None):
    out = bottom.copy()
    for layer in (top, shared):
        if layer is not None:
            a = layer[..., 3] > 0
            out[a] = layer[..., :3][a]
    return out

def main(engine, phg):
    td = topdown(phg)
    cells, trees = ledger(phg, td)
    save_ledger(cells)
    r = compose(engine, phg, cells, td)
    EV.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(SRC / 'compose.npz', bottom=r['bottom'], top=r['top'], shared=r['shared'], shared_src=r['shared_src'],
                        owner=r['owner'], family=r['family'])
    v = preview(r['bottom'], r['top'], r['shared'])
    Image.fromarray(v).save(EV / 'terrain.png')
    ref = np.array(Image.open(SRC / 'hgss/hgss-render.png').convert('RGB'))
    sheet = Image.new('RGB', (W * 16 * 2 + 12, H * 16 + 24), (28, 32, 38)); d = ImageDraw.Draw(sheet)
    for i, (img, t) in enumerate(((ref, 'HGSS reference (decoded map data)'), (v, 'Ten years on, Gen 3 elements'))):
        sheet.paste(Image.fromarray(img), (i * (W * 16 + 12), 24)); d.text((i * (W * 16 + 12) + 4, 6), t, fill='white')
    sheet.save(EV / 'compare.png')
    pairs = {}
    for k in r['mixed'].values():
        pairs['/'.join(k)] = pairs.get('/'.join(k), 0) + 1
    print('trees', len(trees), 'items', len(r['items']), 'manholes', len(r['manholes']), 'mixed tiles', len(r['mixed']))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
