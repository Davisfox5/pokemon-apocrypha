"""Route 7 from HGSS's own route (hgss_source.py), element by element (AGENTS.md: "Converting a
Gen 4 map", "Kanto towns: HGSS's Kanto, the Olivine way"), on the plan the owner approved
(README.md, change list; 2026-10-30).

    python3 tools/gba/maps/route7/compose.py

The cell ledger is HGSS's: its collision (128 blocks; HGSS's other values are walkable
flags), its behaviours (tall grass 0x02, ledges 0x38 east and 0x3b south, the corner 0x3e),
its materials and heights. Each element becomes its Gen 3 piece:

    grass       FireRed's grass and its tufted cells, as Celadon (nature.grass), in the
                world's phase so the pattern runs on across the seam
    road        HGSS's road01 at 1:1 in the world's phase, meeting the grass through FireRed's
                path edge pieces (nature.grass_edges); HGSS's pebble decals (road01_sub) on
                the 8 px grid; widened by a row so Celadon's road comes on at its own width
    Celadon     the city's hexagon paving (x 0-4, HGSS's Celadon level and its slope) and the
                two-lane cycleway (rows 18-19) painted exactly as Celadon paints it, the
                lane's lines carried into the gate
    tall grass  the whole-cell piece G15 on every HGSS tall-grass cell (owner, Route 43)
    rock        FRLG General's mountain set recoloured to HGSS's cliff ramp (cliff01gs tops,
                wall01_g faces), one terrace: the step down from Celadon (x 4) and the two
                outcrops; FireRed's own shadow pixels on FireRed's grass
    ledges      FRLG's ledges in the same ramp where HGSS has its ledges, jumping as HGSS's
                behaviours say
    woods       Cherrygrove's standard tree on Celadon's staggered lattice in world cells, so
                the border woods run on from the city's
    gate        HGSS's Kanto gatehouse (model 247) at 45 degrees on its lot; the road's
                five cells in front of its west face are east arrow warps into the gate room
    Underground the entrance (model 339) on its lot, its door solid until its inside is built
    Path        (owner: unsealed, the inside to come later); HGSS's notice board with
                FireRed's Underground Path sign

Writes gba/art/route7/source/route7.npz (ground, cell kinds, foot, objects) and
evidence/compose.png.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'celadon_elements'))
import common as C             # noqa: E402
import ground as G             # noqa: E402
import nature as N             # noqa: E402
import plan as PL              # noqa: E402
import concept as K            # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route7'
SRC, EV = ART / 'source', ART / 'evidence'
ENGINE = ROOT.parent / 'pokeemerald-expansion'
MW, MH = 33, 32                     # the map: HGSS's block and a column for the gate's east wall
OX, OY = PL.W, 1                    # where the route sits beside Celadon (Route 7 row = Celadon row - 1)
W, H = MW, PL.H                     # the canvas: the map's columns, Celadon's rows (woods above and below)
ROAD, LANE, PAVE_X = (15, 19), (18, 20), 5       # HGSS's road rows; Celadon's lane rows; the paving and lane end at x 5
ROAD_END = 26.5                     # the road runs in under the gate's west wing and step
GATE_X, GATE_BASE = 25.25, 19       # the gatehouse: HGSS's west wall, base row
ARROWS = [(24, y) for y in range(ROAD[0], ROAD[1])]  # the road's four cells in front of the gate's west face, pressing east
UNDERGROUND = (12.0, 23)            # left edge, base row; its door (13, 23)
UNDERGROUND_DOOR = (13, 23)
NOTICE = (12, 25)                   # HGSS's (12, 24) a row south: there its top would cover the entrance's foot
PEBBLES = [(8, 17), (16, 16)]       # HGSS's road01_sub (its third is on Celadon's paving now)
NORTH = (4, 14)                     # the north barrier's west arm: its west column, the row it stops above

def h(*a):
    return int(hashlib.md5(' '.join(map(str, a)).encode()).hexdigest(), 16)

def hgss():
    """HGSS's behaviours, collision and dominant material per cell, on the canvas (map row y
    is canvas row y + OY; the canvas past the map is HGSS-less woods)."""
    p = np.load(SRC / 'hgss/hgss-permissions.npz')
    m = np.load(SRC / 'hgss/hgss-ground-materials.npz')
    names = list(m['names'])
    mat = np.full((H, W), '', '<U12')
    for y in range(32):
        for x in range(32):
            v = np.bincount(m['material'][y * 16:y * 16 + 16, x * 16:x * 16 + 16].ravel() + 1).argmax() - 1
            mat[y + OY, x] = names[v] if v >= 0 else ''
    types = np.zeros((H, W), np.uint8); coll = np.full((H, W), 128, np.uint8)
    types[OY:OY + 32, :32], coll[OY:OY + 32, :32] = p['types'], p['collision']
    return types, coll, mat

def on_map(x, y):
    """Canvas cell (x, y) lies on Route 7's map."""
    return 0 <= x < MW and OY <= y < OY + MH

# --------------------------------------------------------------------------- the ledger
def ledger():
    """Per cell: kind (grass, tall, road, pave, forest, rock, ledge_s, ledge_e, ledge_se)."""
    types, coll, mat = hgss()
    open_ = coll != 128
    kind = np.where(open_, 'grass', 'forest').astype('<U9')
    kind[open_ & (types == 0x02)] = 'tall'
    kind[types == 0x3b] = 'ledge_s'
    kind[types == 0x38] = 'ledge_e'
    kind[types == 0x3e] = 'ledge_se'
    rock = np.zeros((H, W), bool)
    Y = OY
    rock[Y + 0:Y + 4, 21:24] = True; rock[Y + 0:Y + 6, 24:28] = True        # the north-east outcrop
    rock[Y + 20:Y + 32, 4:8] = True; rock[Y + 28:Y + 32, 8:12] = True       # the south-west outcrop
    # The north barrier (owner, 2026-10-31): the step down from Celadon made an outcrop as wide as
    # the south-west one, up to the map's top edge where it ends on its own rim, then four rows
    # deep along the top of the map east to the north-east outcrop, through the woods and the
    # meadow's top rows: the route's north edge is rock the player cannot leave by.
    rock[Y + 0:Y + NORTH[1], NORTH[0]:NORTH[0] + 4] = True
    rock[Y + 0:Y + 4, NORTH[0]:24] = True
    kind[rock] = 'rock'
    kind[Y + ROAD[0]:Y + ROAD[1], 0:W] = 'road'
    kind[Y + 14:Y + 21, 27:W] = 'forest'                    # behind the gate: HGSS's woods (no road beyond it)
    kind[Y + ROAD[0]:Y + LANE[0], 0:PAVE_X] = 'pave'
    kind[Y + LANE[0]:Y + LANE[1], 0:PAVE_X] = 'lane'        # Celadon's lane, ending where the paving meets the dirt road (owner)
    kind[Y + 14, 0:4] = 'forest'                            # Celadon's woods at x 60-63 run on
    return kind, types, coll, mat

def levels(kind):
    """Terrace level per cell: Celadon's level (x 0-4 off the road) and the rock are 1."""
    return (kind == 'rock').astype(int)

# --------------------------------------------------------------------------- Gen 3 pieces
RAMP = [(82, 58, 52), (239, 189, 140), (222, 173, 123), (198, 148, 115), (156, 115, 90), (123, 82, 66), (99, 74, 57)]
FRLG_RAMP = {9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 6}
NINE = {('N', 'W'): 0x68, ('N', 'M'): 0x69, ('N', 'E'): 0x6A, ('M', 'W'): 0x70, ('M', 'M'): 0x71,
        ('M', 'E'): 0x72, ('S', 'W'): 0x78, ('S', 'M'): 0x79, ('S', 'E'): 0x7A}
INNER = dict(se=0xB2, sw=0xB3, ne=0xBA, nw=0xBB)
LEDGE = dict(s=0x87, s_left=0xB0, s_right=0xB1, e_top=0x84, e_mid=0x8C, corner=0x8E)   # FRLG's ledge set
DIRS = dict(n=(0, -1), ne=(1, -1), e=(1, 0), se=(1, 1), s=(0, 1), sw=(-1, 1), w=(-1, 0), nw=(-1, -1))

def frlg_piece(m):
    """FRLG General metatile m: RGBA with its rock-bank pixels in HGSS's ramp, its other
    rock-bank pixels (cast shadow on grass) in FireRed's own colours, its grass clear."""
    d = ENGINE / 'data/tilesets/primary/general_frlg'
    tiles = np.array(Image.open(d / 'tiles.png')) & 15
    tl = lambda i: tiles[(i // 16) * 8:(i // 16) * 8 + 8, (i % 16) * 8:(i % 16) * 8 + 8]
    pals = [[tuple(c & 0xF8 for c in map(int, (d / f'palettes/{b:02}.pal').read_text().split()[3 + i * 3:6 + i * 3]))
             for i in range(16)] for b in range(16)]
    blocks = np.frombuffer((d / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
    out = np.zeros((16, 16, 4), np.uint8)
    for li in range(8):
        e = int(blocks[m][li])
        if e >> 12 != 1:
            continue
        t = tl(e & 1023)
        if e & 0x400: t = t[:, ::-1]
        if e & 0x800: t = t[::-1]
        q = li % 4
        sub = out[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
        for (yy, xx), v in np.ndenumerate(t):
            if v:
                c = RAMP[FRLG_RAMP[int(v)]] if int(v) in FRLG_RAMP else pals[1][int(v)]
                sub[yy, xx] = c + (255,)
    return out

def rock(out, kind):
    """FRLG's mountain pieces per 8x8 quadrant from the terrace levels (Blackthorn's
    rock_frlg, one terrace): side and face pieces where a quadrant faces lower ground, the
    whole inner-corner piece where the only lower neighbour is diagonal. Off the map the
    rock runs on (north, west), except the south, where the outcrop shows its face."""
    lv = levels(kind)
    def lvl(x, y):
        if y >= H:
            return 0
        return lv[min(max(y, 0), H - 1), min(max(x, 0), W - 1)]
    nine = {k: frlg_piece(v) for k, v in NINE.items()}
    inner = {k: frlg_piece(v) for k, v in INNER.items()}
    for y in range(H):
        for x in range(W):
            if kind[y, x] != 'rock':
                continue
            lo = {k: lvl(x + dx, y + dy) < 1 for k, (dx, dy) in DIRS.items()}
            whole = None
            diag = [k for k in ('ne', 'se', 'sw', 'nw') if lo[k]]
            if not any(lo[k] for k in 'nesw') and len(diag) == 1:
                whole = inner[diag[0]]
            cell = out[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
            for qy in (0, 1):
                v = ('N', 'S')[qy] if lo['n'] and lo['s'] else 'N' if lo['n'] else 'S' if lo['s'] else 'M'
                for qx in (0, 1):
                    hh = ('W', 'E')[qx] if lo['w'] and lo['e'] else 'W' if lo['w'] else 'E' if lo['e'] else 'M'
                    vk, hk = 'ns'[qy], 'we'[qx]
                    sl = np.s_[qy * 8:qy * 8 + 8, qx * 8:qx * 8 + 8]
                    if whole is not None:
                        p = whole[sl]
                    elif lo[vk + hk] and not lo[vk] and not lo[hk]:
                        p = inner[vk + hk][sl]
                    else:
                        p = nine[(v, hh)][sl]
                    a = p[..., 3] > 0
                    cell[sl][a] = p[..., :3][a]

def ledges(out, kind):
    """FRLG's ledges: south ledges with rounded ends where they stop on open ground; the east
    ledge as FireRed lays one down a column (its top piece, then middle pieces) turning into the
    south ledge through FireRed's own corner piece, so the two read as one ledge."""
    P = {k: frlg_piece(v) for k, v in LEDGE.items()}
    K_ = lambda x, y: kind[y, x] if 0 <= x < W and 0 <= y < H else 'forest'
    south = lambda x, y: K_(x, y) in ('ledge_s', 'ledge_se')
    east = lambda x, y: K_(x, y) in ('ledge_e', 'ledge_se')
    for y in range(H):
        for x in range(W):
            k = kind[y, x]
            if k not in ('ledge_s', 'ledge_e', 'ledge_se'):
                continue
            if k == 'ledge_se':
                piece = P['corner']
            elif k == 'ledge_e':
                piece = P['e_mid'] if east(x, y - 1) else P['e_top']
            else:
                piece = P['s'].copy()
                if not south(x - 1, y):
                    piece[:, :8] = P['s_left'][:, :8]
                if not south(x + 1, y):
                    piece[:, 8:] = P['s_right'][:, 8:]
            a = piece[..., 3] > 0
            cell = out[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
            cell[a] = piece[..., :3][a]

def tall_grass():
    return np.array(Image.open(SRC / 'shared-art/G15.png').convert('RGBA'))

# --------------------------------------------------------------------------- the ground
def world_grid():
    ys, xs = np.mgrid[0:H * 16, 0:W * 16]
    return ys, xs + OX * 16

def lane(out):
    """Celadon's cycleway (concept.cycleway) painted on: the same distance-from-edge bands over
    the city's lanes and the route's as one mask, so the kerbs, white lines and dashes run on
    across the seam; the lane runs under the gate, which takes it in at its west face."""
    WW, HH = OX + W, PL.H
    m = np.zeros((HH * 16, WW * 16), bool)
    for x0, y0, x1, y1 in PL.CYCLE:
        m[y0 * 16:y1 * 16, x0 * 16:x1 * 16] = True
    m[(OY + LANE[0]) * 16:(OY + LANE[1]) * 16, OX * 16:(OX + PAVE_X) * 16] = True
    pad = 40
    d = ndimage.distance_transform_cdt(np.pad(m, pad, mode='edge'), metric='chessboard')[pad:-pad, pad:-pad]
    sl = np.s_[0:H * 16, OX * 16:WW * 16]
    m, d = m[sl], d[sl]
    ys, xs = world_grid()
    out[m] = K.CYCLE[1]
    out[m & (d <= 2)] = K.KERB[1]
    out[m & (d == 1)] = K.KERB[2]
    out[m & (d == 2) & ((xs + ys) % 8 == 0)] = K.KERB[0]
    out[m & ((d == 4) | (d == 5))] = K.LINE
    out[m & (d == 6)] = K.CYCLE[2]
    out[m & (d == 3)] = K.CYCLE[3]
    out[m & (d >= 15) & ((((xs + ys) // 8) % 2) == 0)] = K.LINE
    rnd = (np.sin(xs * 7.13 + ys * 91.7) * 43758.5453) % 1
    out[m & (d > 6) & (d < 15) & (rnd > 0.96)] = K.CYCLE[0]

def ground(kind):
    t = G.textures(C.textures())
    tex = np.load(SRC / 'hgss/textures.npz')
    gr = N.grass()
    out = np.zeros((H * 16, W * 16, 3), np.uint8)
    for y in range(H):
        for x in range(W):
            k = h('grass', x + OX, y) % 10                   # Celadon's tufts, in world cells
            out[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = gr[0 if k < 8 else k - 7]
    grass_px = out.copy()
    ys, xs = world_grid()
    pave = (kind == 'pave').repeat(16, 0).repeat(16, 1)
    out[pave] = G.tile(t['tama_yuka'], ys, xs)[pave]
    lane(out)
    gtall = tall_grass()
    for y, x in zip(*np.nonzero(kind == 'tall')):
        out[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = gtall[..., :3]
    grassy = np.isin(kind, ('grass', 'forest', 'rock', 'ledge_s', 'ledge_e', 'ledge_se', 'tall'))
    N.grass_edges(out, ~grassy, grass_px)
    rough_road(out, kind, grass_px, tex, t)
    rock(out, kind)
    ledges(out, kind)
    return out

# --------------------------------------------------------------------------- the rough road
WEAR = [(231, 198, 148), (231, 181, 148)]      # road01's two darker shades, for worn patches

def hgss_edges(out, road, grass_px, tex):
    """The road's top and bottom edges feathered with HGSS's own road edge (road01_r, the texture
    HGSS lays along this road's edge rows): its vertical edge strip (texels 0-15 across, grass
    to the west) turned to run along the road, at 1:1 in the world's phase, mirrored for the south
    edge; its grass texels take the map's grass, its sand the road's own texture, its feathered
    grey-brown band kept as HGSS draws it (owner, 2026-10-31: feathered, from tiles that exist)."""
    t = tex['road01_r'][..., :3].astype(int)
    strip = t[:, 0:16].transpose(1, 0, 2)                          # 16 rows (grass at the top) x 32 along
    sand = {tuple(c) for c in tex['road01'][..., :3].reshape(-1, 3).tolist()}
    green = (strip[..., 1] > strip[..., 0] + 20)
    sandy = np.array([[tuple(c) in sand for c in row] for row in strip.tolist()])
    Hh, Ww = road.shape
    for y, x in zip(*np.nonzero(road)):
        for south in (False, True):
            ny = y + (1 if south else -1)
            if 0 <= ny < Hh and road[ny, x]:
                continue
            st, g, sd = (strip[::-1], green[::-1], sandy[::-1]) if south else (strip, green, sandy)
            cols = (np.arange(16) + (x + OX) * 16) % 32
            sl = np.s_[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
            cell, gp = out[sl], grass_px[sl]
            gm, sm = g[:, cols], sd[:, cols]
            rim = ~gm & ~sm
            cell[gm] = gp[gm]
            cell[rim] = st[:, cols][rim].astype(np.uint8)

def rough_road(out, kind, grass_px, tex, t):
    """The dirt road as a rough country road (owner, 2026-10-31): HGSS's road01 at 1:1 on HGSS's
    rows, its edges feathered with HGSS's own road edge texture (not jagged: the owner's second
    note), worn patches in road01's own darker shades, HGSS's pebbles scattered, and Celadon's
    paving breaking up into the dirt at its end instead of stopping on a straight kerb."""
    H8, W8 = H * 2, W * 2
    road = np.zeros((H8, W8), bool)
    r0, r1 = (OY + ROAD[0]) * 2, (OY + ROAD[1]) * 2
    x0, x1 = PAVE_X * 2, int(ROAD_END * 2)
    road[r0:r1, x0:x1] = True
    # the paving's last column breaks up into the dirt (its lane rows stay whole)
    pave_end = np.zeros((H8, W8), bool)
    for sy in range((OY + ROAD[0]) * 2 + 1, (OY + LANE[0]) * 2):      # its top row stays whole, under the grass's edge
        for sx in (x0 - 2, x0 - 1):
            if h('slab', sy, sx) % 3 == 0 or (sx == x0 - 1 and h('slab', sy, sx) % 3 == 1):
                pave_end[sy, sx] = True
    ys, xs = world_grid()
    big = lambda m: m.repeat(8, 0).repeat(8, 1)
    region = np.zeros((H8, W8), bool)
    region[r0 - 2:r1 + 2, x0:x1] = True
    rg = big(region) & ~big(np.isin(kind, ('forest', 'rock', 'ledge_s', 'ledge_e', 'ledge_se', 'tall')).repeat(2, 0).repeat(2, 1))
    out[rg] = grass_px[rg]                                        # the verges, repainted as plain grass first
    dirt = big(road | pave_end)
    out[dirt] = G.tile(tex['road01'], ys, xs)[dirt]
    # the broken slabs' edges: a dark crack where paving meets the dirt that took its place
    paved = (kind == 'pave').repeat(16, 0).repeat(16, 1) & ~dirt
    crack = paved & (np.roll(dirt, 1, 1) | np.roll(dirt, -1, 1) | np.roll(dirt, 1, 0) | np.roll(dirt, -1, 0))
    out[crack] = K.KERB[2]
    # worn patches: small irregular blots of the road's darker shades, dithered at their rims
    ry0, ry1 = r0 * 8, r1 * 8
    for i in range(int((x1 - x0) * 1.2)):
        cx = x0 * 8 + h('wear x', i) % ((x1 - x0) * 8)
        cy = ry0 + 6 + h('wear y', i) % max(1, ry1 - ry0 - 12)
        rx, rh = 3 + h('wear w', i) % 6, 1 + h('wear h', i) % 3
        shade = WEAR[h('wear c', i) % len(WEAR)]
        for yy in range(cy - rh, cy + rh + 1):
            for xx in range(cx - rx, cx + rx + 1):
                if not (0 <= yy < H * 16 and 0 <= xx < W * 16) or not road[yy // 8, xx // 8]:
                    continue
                d = ((xx - cx) / rx) ** 2 + ((yy - cy) / (rh + 0.5)) ** 2
                if d <= 0.55 or (d <= 1.0 and (xx + yy) % 2 == 0):
                    out[yy, xx] = shade
    # HGSS's pebbles, scattered on the 8 px grid off the edges
    p = tex['road01_sub']; pa = p[..., 3] > 0
    for sy in range(r0 + 1, r1 - 2):
        for sx in range(x0 + 2, x1 - 3):
            if h('pebble', sx + OX * 2, sy) % 23 == 0 and road[sy:sy + 2, sx:sx + 2].all():
                cell = out[sy * 8:sy * 8 + 16, sx * 8:sx * 8 + 16]
                cell[pa] = p[..., :3][pa]
    hgss_edges(out, road[::2, ::2], grass_px, tex)

# --------------------------------------------------------------------------- objects
def sprites():
    a = lambda n: np.array(Image.open(SRC / f'art/{n}.png').convert('RGBA'))
    return dict(gate=a('gate-b'), underground=a('underground'), notice=a('notice'))   # the Kanto gate (owner: B)

def objects(kind):
    """The buildings and the notice board, then Cherrygrove's trees on Celadon's lattice in
    world cells (concept.trees: staggered rows two cells apart, the foot two cells, no tree
    over a prop or in front of a building)."""
    sp = sprites()
    objs = []
    g = sp['gate']
    objs.append(dict(X=int(round(GATE_X * 16)), Y=(OY + GATE_BASE + 1) * 16 - g.shape[0], img=g, fam='gate', name='gate'))
    u = sp['underground']
    objs.append(dict(X=int(UNDERGROUND[0] * 16), Y=(OY + UNDERGROUND[1] + 1) * 16 - u.shape[0], img=u, fam='underground', name='underground'))
    n = sp['notice']
    objs.append(dict(X=NOTICE[0] * 16, Y=(OY + NOTICE[1] + 1) * 16 - n.shape[0], img=n, fam='notice', name='notice'))
    tree = N.trees()['johto']
    taken = np.zeros((H, W), bool)
    props = np.zeros((H * 16, W * 16), bool)
    fronts = np.full((H * 16, W * 16), -1, int)
    for o in objs:
        m = np.zeros_like(props); K.stamp(m, o['img'], o['X'], o['Y'])
        if o['fam'] == 'notice':
            props |= m
        else:
            fronts[m] = np.maximum(fronts[m], o['Y'] + o['img'].shape[0])
            props |= m & False
        x0, x1 = o['X'] // 16, (o['X'] + o['img'].shape[1] + 15) // 16
        base = (o['Y'] + o['img'].shape[0]) // 16 - 1
        taken[max(0, base - 1):base + 1, max(0, x0):min(W, x1)] = True
    wood = kind == 'forest'
    for wy in range(0, H - 1, 2):                              # Celadon's rows: world rows even, shifted a cell each row
        for wx in range((wy // 2) % 2 - 1, OX + W + 2, 2):
            x, y = wx - OX, wy
            if x < 0:                                          # a tree whose foot starts in Celadon is the city's
                continue
            w = (tree.shape[1] + 15) // 16
            foot = [(xx, yy) for xx in range(x, x + w) for yy in range(y, y + 2)]
            ok = all((not (0 <= xx < W and 0 <= yy < H)) or (wood[yy, xx] and not taken[yy, xx]) for xx, yy in foot)
            if not ok or not any(0 <= xx < W and 0 <= yy < H for xx, yy in foot):
                continue
            X, Y = x * 16 + (w * 16 - tree.shape[1]) // 2, (y + 2) * 16 - tree.shape[0]
            m = np.zeros_like(props); K.stamp(m, tree, X, Y)
            if (m & props).any() or (m & (fronts >= 0) & (fronts <= (y + 2) * 16)).any():
                continue
            objs.append(dict(X=X, Y=Y, img=tree, fam='tree', name=f'tree_{wx}_{wy}'))
            for xx, yy in foot:
                if 0 <= xx < W and 0 <= yy < H:
                    taken[yy, xx] = True
    for o in objs:
        a = o['img'][..., 3] > 0
        o['base'] = (o['Y'] + int(np.nonzero(a.any(1))[0].max())) // 16
    objs.sort(key=lambda o: (o['Y'] + o['img'].shape[0], o['X']))
    return objs

def overlaps(objs):
    """AGENTS.md "Layering": no standing object covers another, but trees behind a building or
    behind each other."""
    bad = []
    masks = []
    for o in objs:
        m = np.zeros((H * 16 + 64, W * 16 + 64), bool)
        K.stamp(m, o['img'], o['X'] + 32, o['Y'] + 32)
        masks.append(m)
    for i, a in enumerate(objs):
        for j, b in enumerate(objs):
            if j <= i or not (masks[i] & masks[j]).any():
                continue
            fi, fj = a['fam'], b['fam']
            if fi == 'tree' and fj == 'tree':
                continue
            if 'tree' in (fi, fj):
                t, o = (a, b) if fi == 'tree' else (b, a)
                if o['fam'] in ('gate', 'underground') and t['base'] < o['base']:
                    continue                                  # a tree behind a building
            bad.append((a['name'], b['name']))
    return bad

# --------------------------------------------------------------------------- the picture
def picture(ground_, objs):
    out = ground_.copy()
    for o in objs:
        C.put(out, o['img'], o['X'], o['Y'])
    return out

def main():
    kind, types, coll, mat = ledger()
    gr = ground(kind)
    objs = objects(kind)
    bad = overlaps(objs)
    pic = picture(gr, objs)
    EV.mkdir(parents=True, exist_ok=True)
    Image.fromarray(pic).save(EV / 'compose-canvas.png')
    m = pic[OY * 16:(OY + MH) * 16]
    Image.fromarray(m).save(EV / 'compose.png')
    Image.fromarray(m).resize((MW * 32, MH * 32), Image.NEAREST).save(EV / 'compose-2x.png')
    np.savez_compressed(SRC / 'route7.npz', ground=gr, kind=kind,
                        objects=np.array([json.dumps(dict(X=o['X'], Y=o['Y'], fam=o['fam'], name=o['name'])) for o in objs]))
    print('objects', len(objs), 'trees', sum(o['fam'] == 'tree' for o in objs), 'overlaps', bad[:10])
    return kind, gr, objs

if __name__ == '__main__':
    main()

# --------------------------------------------------------------------------- traversal
BASE_ONLY = ('notice',)

def traversal(kind, objs):
    """Per canvas cell: foot ('open', 'blocked', 'tall', 'jump_s', 'jump_e', 'arrow_e') and why.
    Off the map is blocked. Trees block their two foot rows, the buildings every cell their art
    covers but a top edge alone (stream6's rule), the notice board its base row; the cells in
    front of the gate's west face are east arrow warps; the Underground Path's door stays solid
    until its inside is built."""
    foot = np.full((H, W), 'blocked', '<U8')
    why = np.full((H, W), 'off the map', '<U24')
    for y in range(OY, OY + MH):
        for x in range(MW):
            k = kind[y, x]
            f = dict(grass='open', road='open', pave='open', lane='open', tall='tall', ledge_s='jump_s', ledge_se='jump_s',
                     ledge_e='jump_e').get(k, 'blocked')
            foot[y, x] = f; why[y, x] = k
    for o in objs:
        m = np.zeros((H * 16, W * 16), bool); K.stamp(m, o['img'], o['X'], o['Y'])
        m = m.reshape(H, 16, W, 16)
        art, upper = m.any(axis=(1, 3)), m[:, :8].any(axis=(1, 3))
        for y, x in zip(*np.nonzero(art)):
            if not on_map(x, y):
                continue
            if o['fam'] == 'tree':
                hit = y >= o['base'] - 1
            elif o['fam'] in BASE_ONLY:
                hit = y == o['base']
            else:
                hit = y <= o['base'] and (upper[y, x] or y == o['base'])
            if hit:
                foot[y, x] = 'blocked'; why[y, x] = o['name'][:24]
    for x, y in ARROWS:
        assert foot[OY + y, x] == 'open', (x, y, why[OY + y, x])
        foot[OY + y, x] = 'arrow_e'; why[OY + y, x] = 'to the gate room'
    dx, dy = UNDERGROUND_DOOR
    foot[OY + dy, dx] = 'blocked'; why[OY + dy, dx] = 'door to nothing: underground'
    return foot, why
