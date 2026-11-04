"""The apartment block from its floor plans in Gen 3's own pieces (owner, 2026-11-04: "splice
gen 4 conversions and gen 3 native tiles into the same map"; native or existing elements in
place of every custom or converted one).

    python3 tools/gba/maps/celadon_elements/apartments_native.py

Every element is a whole metatile piece from an Emerald or FireRed room in the engine, checked
whole against its own room (cut(): an object whose pixels run past its box is flagged), laid on
by its own pixels over this room's floor and walls. HGSS conversions stay only where neither game
has the element (NATIVE_GAPS; none so far). The plans are here (Plan): the floor plans of
apartments_floorplans.py redrawn 36 squares wide so the core's north wall holds both flights and
the elevator apart (owner, 2026-11-04), and with the museum's own wall depths.

    shell      Lilycove Museum (Emerald): its cream walls and pink skirting, the north wall, the
               inner walls seen from above and face on, its marble floor for the lobby and core
    homes      Brendan's house (Emerald): the kitchen run, the TV, the dining set, the bed, the
               PC desk, the clock, the wood floor; Lorelei's house (FireRed): its carpet, its
               drawers and bookcase, its dining set, its bed
    upscale    Devon Corp 3F (Emerald): its carpet, the black leather sofa, the armchairs, the
               glass tables and display cases; Slateport's Fan Club (Emerald): the sofa set on
               its rug; the museum's paintings, sculptures and bench
    service    Lilycove Dept Store (Emerald): the elevator doors, the counter, the planters and
               plants; its rooftop for the terrace (paving, railings, planters, benches)
    stairs     the museum's flights set into the north wall: up (1F) and down (2F), alternating
               spots floor to floor as a stairwell would (STAIRS)

Writes gba/art/celadon-elements/evidence/apartments/native-*.png (each floor, and
native-pieces.png: every piece on its own with its check).
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parent / 'saffron'))
import common as C                                  # noqa: E402
import frlg                                         # noqa: E402
import tiles as T                                   # noqa: E402

ENG = C.ROOT.parent / 'pokeemerald-expansion'
EV = C.ROOT / 'gba/art/celadon-elements/evidence/apartments'
LAYOUTS = {l['name']: l for l in json.loads((ENG / 'data/layouts/layouts.json').read_text())['layouts'] if l}
GFX = (ENG / 'src/data/tilesets/graphics.h').read_text()
HDR = (ENG / 'src/data/tilesets/headers.h').read_text()
NATIVE_GAPS = {}                                    # element -> why no Gen 3 piece serves (an HGSS conversion stands in)

def folder(sym):
    name = sym.replace('gTileset_', '')
    m = re.search(rf'gTileset_{name} =\s*\{{(.*?)\}};', HDR, re.S)
    t = re.search(r'\.tiles = gTilesetTiles_(\w+)', m.group(1)).group(1)
    return re.search(rf'gTilesetTiles_{t}\[\] = INCGFX_U32\("data/tilesets/(?:primary|secondary)/([^/]+)/', GFX).group(1)

class EPair:
    """An Emerald tileset pair, drawn per metatile as (bottom RGB, top RGBA) like frlg.Pair."""
    def __init__(self, primary, secondary):
        self.t = T.Tileset(ENG, secondary, primary)
    def quad(self, e):
        tid = e & 1023; bank = e >> 12
        tiles = self.t.tiles[tid >= 512]; idx = tid - 512 if tid >= 512 else tid
        out = np.zeros((8, 8, 4), np.uint8)
        if idx >= len(tiles):
            return out
        cols = self.t.pals[bank >= 6][bank]
        v = np.array(tiles[idx], int).reshape(8, 8) % 16
        if e & 1024: v = v[:, ::-1]
        if e & 2048: v = v[::-1]
        for y in range(8):
            for x in range(8):
                if v[y, x]:
                    out[y, x, :3] = cols[v[y, x]]; out[y, x, 3] = 255
        return out
    def cell(self, mid):
        entries = self.t.blocks[mid >= 512][mid - 512 if mid >= 512 else mid]
        bot = np.zeros((16, 16, 3), np.uint8); bot[...] = self.t.pals[0][0][0]
        top = np.zeros((16, 16, 4), np.uint8)
        for li in range(8):
            q = self.quad(entries[li]); sl = np.s_[(li % 4 // 2) * 8:(li % 4 // 2) * 8 + 8, (li % 2) * 8:(li % 2) * 8 + 8]
            a = q[..., 3] > 0
            if li < 4:
                bot[sl][a] = q[..., :3][a]
            else:
                top[sl][a] = q[a]
        return bot, top

SRC = {}
def source(key, layout):
    l = LAYOUTS[layout + '_Layout']
    g = np.frombuffer((ENG / l['blockdata_filepath']).read_bytes(), '<u2').reshape(l['height'], l['width']).astype(int) & 0x3FF
    p, s = folder(l['primary_tileset']), folder(l['secondary_tileset'])
    pair = frlg.Pair(ENG, p, s) if l.get('layout_version') == 'frlg' else EPair(p, s)
    SRC[key] = (pair, g, layout)

for k, n in dict(MU='LilycoveCity_LilycoveMuseum_1F', B1='LittlerootTown_BrendansHouse_1F', B2='LittlerootTown_BrendansHouse_2F',
                 DV='RustboroCity_DevonCorp_3F', DS='LilycoveCity_DepartmentStore_1F', RT='LilycoveCity_DepartmentStoreRooftop',
                 FC='SlateportCity_PokemonFanClub', LO='FourIsland_LoreleisHouse', K1='CeladonCity_Condominiums_1F',
                 K2='CeladonCity_Condominiums_2F', K3='CeladonCity_Condominiums_3F',
                 EL='LilycoveCity_DepartmentStoreElevator', M2='LilycoveCity_LilycoveMuseum_2F').items():
    source(k, n)

_flat = {}
def flat(src, x, y):
    pair, g, _ = SRC[src]
    m = int(g[y, x])
    if (src, m) not in _flat:
        b, t = pair.cell(m)
        out = b.astype(np.int16).copy(); a = t[..., 3] > 0; out[a] = t[..., :3][a]
        _flat[(src, m)] = out
    return _flat[(src, m)]

_modes = {}
def mode(src, cells):
    a = np.stack([flat(src, x, y) for x, y in cells])
    key = (a[..., 0].astype(np.int64) << 20) | (a[..., 1].astype(np.int64) << 10) | a[..., 2]
    out = np.zeros((16, 16, 3), np.int16)
    for yy in range(16):
        for xx in range(16):
            v, n = np.unique(key[:, yy, xx], return_counts=True)
            k = int(v[n.argmax()]); out[yy, xx] = (k >> 20, (k >> 10) & 1023, k & 1023)
    return out

# the rows of each source that are wall (its north wall, and the condos' inner walls)
WALL_ROWS = dict(K1=(0, 1, 5, 6, 15, 16), K2=(0, 1, 5, 6, 15, 16), K3=(0, 1, 5, 6, 15, 16))

def modes(src):
    """A room's plain background: its floor (per pixel, the colour most floor cells have there),
    the shade down its first column, and per wall row its plain wall."""
    if src not in _modes:
        _, g, _ = SRC[src]
        H, W = g.shape
        # the room's floor is the metatile it repeats most; with it the shade under the north wall
        # (row 2's commonest) and down the left wall (the first column's commonest)
        from collections import Counter
        body = [int(v) for v in g[3:H - 1].ravel() if int(v) != 0x8]
        x0 = next((x for x in range(W) if int(g[3, x]) != 0x8), 0)
        ids = {Counter(body).most_common(1)[0][0], Counter(int(v) for v in g[2]).most_common(1)[0][0],
               Counter(int(g[y, x0]) for y in range(3, H - 1)).most_common(1)[0][0]}
        cell_of = {int(g[y, x]): (x, y) for y in range(H) for x in range(W)}
        floor = [flat(src, *cell_of[m]) for m in ids]
        left = []
        rows = {}
        for y in WALL_ROWS.get(src, (0, 1)):
            cells = [(x, y) for x in range(W) if flat(src, x, y).sum(-1).mean() > 8]   # not the void around the room
            m = mode(src, cells)
            if max((m == f).all(-1).mean() for f in floor) < 0.3:
                rows[y] = m
        _modes[src] = (rows, floor, left)
    return _modes[src]

def object_mask(src, x, y):
    _, g, _ = SRC[src]
    if int(g[y, x]) == 0x8:
        return np.zeros((16, 16), bool)
    c = flat(src, x, y)
    rows, floor, left = modes(src)
    same = np.zeros((16, 16), bool)
    for f in floor + left:
        same |= (c == f).all(-1)
    if y in rows:
        same |= (c == rows[y]).all(-1)
    pair = SRC[src][0]
    top = pair.cell(int(g[y, x]))[1][..., 3] > 0          # the top layer is always the object (Emerald lays furniture there)
    return ~same | top

# --------------------------------------------------------------------------- the pieces
# name: (source, x, y, w, h, kind) — 'wall' pieces stand against a north wall (their top two
# rows on its two rows), 'floor' pieces stand free, 'cells' are copied whole (walls, floors).
PIECES = {
    # Lilycove Museum: the shell
    'painting_a':   ('MU', 1, 0, 2, 2, 'wall'), 'painting_b': ('MU', 5, 0, 2, 2, 'wall'),
    'painting_c':   ('MU', 9, 0, 1, 1, 'wall'), 'painting_d': ('MU', 19, 0, 2, 2, 'wall'),
    'bench':        ('MU', 15, 7, 5, 3, 'floor'), 'statue_a': ('MU', 15, 11, 1, 2, 'floor'), 'statue_b': ('MU', 18, 11, 1, 2, 'floor'),
    # Brendan's house
    'kitchen':      ('B1', 0, 0, 5, 3, 'wall'), 'tv': ('B1', 4, 4, 1, 2, 'floor'), 'table_w': ('B1', 2, 4, 2, 2, 'floor', (0, 7)),
    'kitchen_in':   ('B1', 0, 0, 5, 3, 'wall', 17),
    'dining_b1':    ('B1', 1, 5, 6, 4, 'floor', 9),
    'window':       ('K1', 4, 0, 1, 2, 'wall'), 'mat': ('B1', 8, 8, 2, 1, 'floor'),
    'pc':           ('B2', 0, 0, 2, 3, 'wall'), 'console': ('B2', 3, 1, 1, 2, 'wall'), 'tv_wall': ('B2', 4, 0, 1, 3, 'wall'),
    'clock':        ('B2', 5, 0, 1, 2, 'wall'), 'picture': ('B2', 2, 0, 1, 2, 'wall'), 'bed': ('B2', 0, 4, 3, 2, 'floor'),
    'rug_blue':     ('B2', 4, 3, 4, 4, 'floor'),
    # Devon Corp 3F
    'sofa_black':   ('DV', 8, 0, 3, 3, 'wall'), 'armchair_l': ('DV', 5, 4, 1, 3, 'floor'), 'armchair_r': ('DV', 17, 4, 1, 3, 'floor'),
    'glass_table':  ('DV', 7, 4, 5, 4, 'floor'), 'side_table': ('DV', 15, 4, 2, 4, 'floor'), 'glass_case': ('DV', 1, 4, 1, 2, 'floor'),
    # Slateport Fan Club
    'lounge':       ('FC', 2, 4, 10, 5, 'floor'), 'books_fc': ('FC', 0, 1, 2, 2, 'wall'), 'plant_fc': ('FC', 0, 9, 1, 2, 'floor'),
    # Lorelei's house
    'bed_lo':       ('LO', 0, 2, 3, 2, 'floor'), 'drawers': ('LO', 8, 0, 1, 3, 'wall'), 'books_lo': ('LO', 9, 0, 2, 3, 'wall'),
    'dining_lo':    ('LO', 3, 3, 6, 4, 'floor'), 'cupboard_lo': ('LO', 3, 0, 2, 3, 'wall'), 'table_lo': ('LO', 9, 3, 2, 3, 'floor'),
    # Lilycove Dept Store
    'elevator':     ('DS', 1, 0, 3, 2, 'wall'), 'counter': ('DS', 6, 1, 6, 3, 'wall'),
    'planter':      ('DS', 0, 4, 2, 2, 'floor'), 'plant': ('DS', 14, 6, 1, 2, 'floor'),
    # the rooftop
    'r_planter':    ('RT', 1, 2, 2, 2, 'floor'), 'r_bench': ('RT', 5, 5, 2, 1, 'floor'), 'r_chair': ('RT', 16, 4, 1, 1, 'floor'),
    'r_vending':    ('RT', 9, 0, 2, 2, 'wall'),
    # FireRed's Condominiums
    # the museum's flights, set into the north wall: up (1F, to 2F) and down (2F, to 1F)
    'stairs_up':    ('MU', 15, 0, 3, 2, 'wall'), 'stairs_down': ('M2', 12, 0, 3, 2, 'wall'),
    'sofa_fr':      ('K2', 1, 6, 4, 2, 'floor', 9), 'sofa_side': ('K2', 6, 9, 1, 3, 'floor'), 'table_fr': ('K2', 1, 8, 4, 4, 'floor'),
    'tv_fr':        ('K2', 5, 5, 2, 3, 'wall'), 'sofa_fr2': ('K2', 4, 16, 3, 2, 'floor'), 'picture_fr': ('K2', 2, 15, 2, 2, 'wall'),
}

def piece_pixels(name):
    src, sx, sy, w, h = PIECES[name][:5]
    return np.concatenate([np.concatenate([flat(src, sx + xx, sy + yy) for xx in range(w)], 1) for yy in range(h)], 0)

def piece_mask(name):
    from scipy import ndimage
    src, sx, sy, w, h = PIECES[name][:5]
    # pixel rows at its top (and bottom) that belong to the pieces above or below it
    trim = PIECES[name][6] if len(PIECES[name]) > 6 else 0
    top, bot = trim if isinstance(trim, tuple) else (trim, 0)
    raw = np.concatenate([np.concatenate([object_mask(src, sx + xx, sy + yy) for xx in range(w)], 1) for yy in range(h)], 0)
    raw[:top] = False
    if bot:
        raw[-bot:] = False
    m = ndimage.binary_closing(np.pad(raw, 2), np.ones((3, 3)), iterations=2)[2:-2, 2:-2] | raw
    m[:top] = False
    if bot:
        m[-bot:] = False
    m = ndimage.binary_fill_holes(m)
    # on the source's wall rows only the object's own pixels: the wall between them stays wall
    rows = modes(src)[0]
    for yy in range(h):
        if sy + yy in rows:
            m[yy * 16:(yy + 1) * 16] = raw[yy * 16:(yy + 1) * 16]
    return m

def cut(name):
    src, x0, y0, w, h = PIECES[name][:5]
    _, g, _ = SRC[src]
    H, W = g.shape
    big = np.zeros(((H + 2) * 16, (W + 2) * 16), bool)
    for y in range(max(0, y0 - 1), min(H, y0 + h + 1)):
        for x in range(max(0, x0 - 1), min(W, x0 + w + 1)):
            big[(y + 1) * 16:(y + 2) * 16, (x + 1) * 16:(x + 2) * 16] = object_mask(src, x, y)
    X0, Y0, X1, Y1 = (x0 + 1) * 16, (y0 + 1) * 16, (x0 + w + 1) * 16, (y0 + h + 1) * 16
    out = dict(left=int((big[Y0:Y1, X0] & big[Y0:Y1, X0 - 1]).sum()), right=int((big[Y0:Y1, X1 - 1] & big[Y0:Y1, X1]).sum()),
               top=int((big[Y0, X0:X1] & big[Y0 - 1, X0:X1]).sum()), bottom=int((big[Y1 - 1, X0:X1] & big[Y1, X0:X1]).sum()))
    return {k: v for k, v in out.items() if v}

# --------------------------------------------------------------------------- the shell
# The museum's walls by its own rule (Lilycove Museum 1F):
#   north wall   two rows, its top (MU x, 0) and its face with the skirting (MU x, 1)
#   east-west    three rows: its cap, whose top half is the floor beyond it (MU x, 4), its face
#                (MU x, 5) and its face with the skirting (MU x, 6); at a doorway the wall ends in
#                a pillar: its cap corner (MU 9, 4), the pillar (MU 9, 5), its foot (MU 9, 8)
#   north-south  a pillar one square wide: over the north wall (MU 13, 0-1), down its length
#                banded and plain by turns (MU 13, 2 / 13, 3), its foot with the skirting (MU 13, 4)
# The marble's shade is the museum's: under a wall (MU x, 2 / x, 7) and east of a pillar
# (MU 10, 6-7). The other floors are their own rooms' plain floor.
FLOORS = dict(
    marble=[('MU', 10, 10), ('MU', 11, 10), ('MU', 10, 11), ('MU', 11, 11)],
    wood=[('B1', 7, 5), ('B1', 8, 5), ('B1', 7, 6), ('B1', 8, 6)],
    carpet=[('LO', 9, 6), ('LO', 10, 6), ('LO', 9, 7), ('LO', 10, 7)],
    red=[('DV', 13, 5), ('DV', 14, 5), ('DV', 13, 6), ('DV', 14, 6)])
BLACK = ('K1', 0, 19)

def floor_cell(style, x, y):
    src, sx, sy = FLOORS[style][(y % 2) * 2 + (x % 2)]
    return flat(src, sx, sy)

W = 36                                        # every floor 36 squares wide
CORE = (11, 21)                               # the core's floor; its walls at x 10 and 22
P, LIFT, Q = 11, 15, 19                       # the north wall's three spots: stairs, the elevator, stairs

class Plan:
    """A floor's geometry: floor style per square, north-south walls (x, y0, y1), east-west walls
    (x0, x1, cap row) three rows deep, doorways (squares cut from the walls, with their floor)."""
    def __init__(self, H=16):
        self.W, self.H = W, H
        self.floor = np.full((H, W), '', '<U8')
        self.ns, self.ew, self.doors, self.sills = [], [], {}, set()
    def room(self, x0, y0, x1, y1, style):
        self.floor[y0:y1 + 1, x0:x1 + 1] = style
    def door_ns(self, x, y, style):
        self.doors[(x, y)] = style
    def door_ew(self, x, cap, style):
        for yy in range(cap, cap + 3):
            self.doors[(x, yy)] = style
        self.sills.add((x, cap))                 # the doorway's sill: the room beyond up to the cap's line

class Room:
    def __init__(self, plan):
        self.p = plan
        W, H = plan.W, plan.H
        self.W, self.H = W, H
        self.img = np.zeros((H * 16, W * 16, 3), np.int16)
        self.solid = np.zeros((H, W), bool)
        self.used = []
        ns, ew = set(), {}
        for x, y0, y1 in plan.ns:
            for y in range(y0, y1 + 1):
                ns.add((x, y))
        for x0, x1, cap in plan.ew:
            for x in range(x0, x1 + 1):
                for r in range(3):
                    ew[(x, cap + r)] = r
        for c in plan.doors:
            ns.discard(c); ew.pop(c, None)
        style = plan.floor.copy()
        for (x, y), st in plan.doors.items():
            style[y, x] = st
        wall = np.zeros((H, W), bool); wall[0:2] = True
        for x, y in ns | set(ew):
            wall[y, x] = True
        self.ns, self.ew, self.wall, self.style = ns, ew, wall, style
        for y in range(H):
            for x in range(W):
                sl = np.s_[y * 16:(y + 1) * 16, x * 16:(x + 1) * 16]
                if wall[y, x]:
                    self.img[sl] = self.wall_cell(x, y); self.solid[y, x] = True
                elif style[y, x]:
                    self.img[sl] = self.floor_at(x, y)
                    if (x, y) in plan.sills and style[y - 1, x] and style[y - 1, x] != style[y, x]:
                        self.img[sl][:8] = self.floor_at(x, y - 1)[:8] if style[y - 1, x] != 'marble' else floor_cell('marble', x, y)[:8]
                else:
                    self.img[sl] = flat(*BLACK); self.solid[y, x] = True
    def is_wall(self, x, y):
        return not (0 <= x < self.W and 0 <= y < self.H) or self.wall[y, x]
    def floor_at(self, x, y):
        st = self.style[y, x] if 0 <= y < self.H and 0 <= x < self.W else ''
        if not st:
            return floor_cell('marble', x, y)
        if st != 'marble':
            return floor_cell(st, x, y)
        under = self.wall[y - 1, x] and ((x, y - 1) not in self.ns or y - 1 <= 1)
        beside = x > 0 and (x - 1, y) in self.ns
        if under and beside:
            return mu(14, 2)
        if under:
            return mu(4 + x % 2, 2 if y - 1 <= 1 else 7)
        if beside:
            return mu(10, 6 + y % 2)
        return floor_cell('marble', x, y)
    def with_floor(self, cell, x, fy, rows):
        """A wall square whose part `rows` is the floor of square (x, fy)."""
        out = cell.copy()
        if 0 <= fy < self.H and self.style[fy, x] and self.style[fy, x] != 'marble':
            out[rows] = floor_cell(self.style[fy, x], x, fy)[rows]
        return out
    def wall_cell(self, x, y):
        H = self.H
        if (x, y) in self.ns:
            if y <= 1:
                return mu(13, y)
            if not self.is_wall(x, y + 1):
                return self.with_floor(mu(13, 4), x, y + 1, np.s_[8:])
            return mu(13, 2 + y % 2)
        if y <= 1:
            return mu(3 + x % 2, y)
        r = self.ew[(x, y)]
        cap = y - r
        left_open = not self.is_wall(x - 1, y)
        right_open = not self.is_wall(x + 1, y)
        if left_open or right_open:                    # the wall's end at a doorway: its pillar
            c = [mu(9, 4), mu(9, 5), mu(9, 8)][r]
            if left_open and not right_open:
                c = c[:, ::-1]
            if r == 0:
                return self.with_floor(c, x, cap - 1, np.s_[:8])
            if r == 2:
                return self.with_floor(c, x, cap + 3, np.s_[8:])
            return c
        if r == 0:
            return self.with_floor(mu(4 + x % 2, 4), x, cap - 1, np.s_[:8])
        return mu(4 + x % 2, 4 + r)
    def piece(self, name, x, y, solid=True):
        """A whole piece by its own pixels, its top-left cell at (x, y) ('cells' pieces whole
        below the wall rows)."""
        src, sx, sy, w, h, kind = PIECES[name][:6]
        self.used.append((name, x, y))
        m = piece_mask(name); px = piece_pixels(name)
        if kind == 'cells':
            m = m.copy(); m[max(0, (2 - sy)) * 16:] = True
        dst = self.img[y * 16:(y + h) * 16, x * 16:(x + w) * 16]
        dst[m] = px[m]
        if solid:
            for yy in range(h):
                for xx in range(w):
                    if m[yy * 16:(yy + 1) * 16, xx * 16:(xx + 1) * 16].any():
                        self.solid[y + yy, x + xx] = True
    def png(self):
        return np.clip(self.img, 0, 255).astype(np.uint8)

def mu(x, y):
    return flat('MU', x, y)

# --------------------------------------------------------------------------- the floors
# The stairs alternate as a real stairwell would: the flight up from a floor lands where the
# next floor's flight down is, so the spots swap floor to floor (owner, 2026-11-04):
#   1F up P;  2F, 4F down P, up Q;  3F, 5F down Q, up P;  6F down P, up Q;  roof down Q
STAIRS = {1: (None, P), 2: (P, Q), 3: (Q, P), 4: (P, Q), 5: (Q, P), 6: (P, Q)}

def core(p, r, floor, plants=True):
    down, up = STAIRS[floor]
    r.piece('elevator', LIFT, 0)
    if down is not None:
        r.piece('stairs_down', down, 0)
    r.piece('stairs_up', up, 0)
    if plants:
        r.piece('plant', CORE[0], p.H - 3); r.piece('plant', CORE[1], p.H - 3)

def core_plan(p):
    p.room(CORE[0], 2, CORE[1], p.H - 2, 'marble')
    p.ns += [(10, 0, p.H - 2), (22, 0, p.H - 2)]

def lobby():
    p = Plan()
    p.room(0, 2, W - 1, 14, 'marble')
    p.room(0, 2, 5, 5, 'wood')                                   # the concierge office
    p.ns += [(6, 0, 8)]; p.ew += [(0, 5, 6)]
    p.door_ew(3, 6, 'marble')
    r = Room(p)
    core(p, r, 1, plants=False)
    r.piece('painting_a', 0, 0); r.piece('books_fc', 2, 0); r.piece('pc', 4, 0)          # the office: shelves, a desk
    r.piece('counter', 7, 10)                                                         # the concierge desk by the door
    r.piece('painting_b', 24, 0); r.piece('painting_d', 28, 0); r.piece('painting_a', 32, 0)
    r.piece('lounge', 25, 7)                                                          # the lounge
    r.piece('statue_a', 13, 12); r.piece('statue_b', 19, 12)                          # either side of the way in
    r.piece('planter', 0, 12); r.piece('planter', 34, 12); r.piece('glass_case', 35, 3); r.piece('glass_case', 35, 5)
    r.piece('plant', 23, 2); r.piece('plant', 9, 2)
    r.piece('mat', 16, 14, solid=False)                                               # the street door
    return r

def typical(floor):
    p = Plan()
    core_plan(p)
    p.room(0, 2, 9, 14, 'wood')                                  # the studio, one open room
    p.door_ns(10, 10, 'wood')
    p.room(23, 2, 28, 5, 'carpet'); p.room(30, 2, 35, 5, 'carpet')   # the two-bedroom's bedrooms
    p.room(23, 9, 35, 14, 'wood')                                # its living room
    p.ns += [(29, 0, 6)]; p.ew += [(23, 35, 6)]
    p.door_ew(24, 6, 'wood'); p.door_ew(34, 6, 'wood')
    p.door_ns(22, 10, 'wood')
    r = Room(p)
    core(p, r, floor)
    # the studio: the kitchen and the TV along the window wall, the dining set below the kitchen,
    # the end-on sofa and a low table by the TV, the bed on its rug in the far corner
    r.piece('kitchen', 0, 0); r.piece('window', 5, 0); r.piece('clock', 6, 0); r.piece('tv_wall', 7, 0)
    r.piece('dining_b1', 0, 4)
    r.piece('table_w', 7, 4); r.piece('sofa_side', 9, 3)
    r.piece('rug_blue', 0, 10, solid=False); r.piece('bed', 0, 10)
    r.piece('plant', 9, 13); r.piece('plant', 0, 8)
    # the bedrooms: a bed and a desk or shelves in each
    r.piece('pc', 23, 0); r.piece('picture', 25, 0); r.piece('bed', 26, 2)
    r.piece('books_lo', 30, 0); r.piece('drawers', 32, 0); r.piece('bed', 33, 2)
    # the open room: the kitchen on the bedrooms' wall, the dining set under it, the sofas
    r.piece('kitchen_in', 27, 7)
    r.piece('dining_b1', 23, 10)
    r.piece('sofa_fr', 30, 10); r.piece('sofa_side', 34, 11); r.piece('table_w', 31, 12)
    return r

def penthouse():
    p = Plan(H=20)
    core_plan(p)
    p.room(0, 2, 9, 18, 'red')                                   # the great room
    p.door_ns(10, 10, 'red')
    p.room(23, 2, 28, 6, 'wood'); p.room(30, 2, 35, 6, 'red')    # the study, the master bedroom
    p.room(23, 10, 35, 11, 'marble')                             # the hall
    p.room(23, 15, 28, 18, 'red'); p.room(30, 15, 35, 18, 'wood')   # the guest room, the walk-in closet
    p.ns += [(29, 0, 7), (29, 12, 18)]; p.ew += [(23, 35, 7), (23, 35, 12)]
    p.door_ew(26, 7, 'marble'); p.door_ew(32, 7, 'marble'); p.door_ew(26, 12, 'red'); p.door_ew(32, 12, 'wood')
    p.door_ns(22, 10, 'marble')
    r = Room(p)
    core(p, r, 6)
    # the great room: the kitchen and the black sofa on the window wall, the glass table and an
    # armchair before the sofa, the dining set below, a reading corner, the display cases
    r.piece('kitchen', 0, 0); r.piece('sofa_black', 6, 0)
    r.piece('glass_table', 5, 3); r.piece('armchair_l', 4, 3)
    r.piece('dining_lo', 0, 8)
    r.piece('armchair_l', 1, 13); r.piece('side_table', 2, 13); r.piece('armchair_r', 4, 13)
    r.piece('glass_case', 9, 8); r.piece('glass_case', 9, 12); r.piece('plant', 0, 17); r.piece('plant', 9, 17)
    # the study, the master bedroom
    r.piece('books_fc', 23, 0); r.piece('pc', 25, 0); r.piece('plant', 28, 2)
    r.piece('painting_d', 30, 0); r.piece('books_lo', 32, 0); r.piece('bed', 33, 2)
    # the guest room, the closet
    r.piece('cupboard_lo', 23, 13); r.piece('bed', 23, 15)
    r.piece('drawers', 30, 13); r.piece('cupboard_lo', 33, 13); r.piece('glass_case', 30, 16); r.piece('glass_case', 35, 16)
    r.piece('plant', 35, 10)
    return r

def rt_layers(sx, sy, flip=False):
    pair, g, _ = SRC['RT']
    bot, top = pair.cell(int(g[sy, sx]))
    if flip:
        bot, top = bot[:, ::-1], top[:, ::-1]
    return bot.astype(np.int16), top

def roof():
    """Lilycove Dept Store's rooftop at the terrace's size, built as Emerald builds it: its paving,
    shade and parapet from the bottom layer, the railing over them from the top layer, the east
    side the west side flipped (Gen 3 flips tiles). The stair house (over the 6F flight up, Q),
    vending machines, planters, benches and chairs are the rooftop's own."""
    H = 16
    p = Plan(H)
    r = Room(p)
    def col(x):
        if x == 0: return 0, False
        if x == W - 1: return 0, True
        if x == 1: return 1, False
        return 3 + (x % 2), False
    def row(y):
        if y <= 1: return y
        if y >= H - 4: return y - (H - 4) + 6
        return 3 + (y % 2)
    for y in range(H):
        for x in range(W):
            sx, flip = col(x); sy = row(y)
            if sy == 9:
                sx = 4
            bot, top = rt_layers(sx, sy, flip)
            a = top[..., 3] > 0
            if sx == 1 and 2 <= sy <= 5:
                a[:] = False                            # the rooftop's planters stand there: its paving only
            bot[a] = top[..., :3][a]
            r.img[y * 16:(y + 1) * 16, x * 16:(x + 1) * 16] = bot
            r.solid[y, x] = x in (0, W - 1) or y <= 1 or y >= H - 4
    def put(sx, sy, w, h, x, y, cells=False):
        for yy in range(h):
            for xx in range(w):
                bot, top = rt_layers(sx + xx, sy + yy)
                dst = r.img[(y + yy) * 16:(y + yy + 1) * 16, (x + xx) * 16:(x + xx + 1) * 16]
                if cells:
                    dst[...] = bot
                a = top[..., 3] > 0
                dst[a] = top[..., :3][a]
                r.solid[y + yy, x + xx] = True
    put(12, 1, 3, 3, Q, 1, cells=True)                  # the stair house over the flight up from 6F
    r.solid[3, Q + 1] = False
    put(9, 0, 2, 2, 25, 0, cells=True)                  # vending machines in the railing
    for x, y in ((2, 3), (2, 7), (32, 3), (32, 7)):
        put(1, 2, 2, 2, x, y)                           # planters
    for x, y in ((7, 6), (7, 9), (26, 6), (26, 9)):
        put(5, 5, 2, 1, x, y)                           # benches
    for x, y in ((10, 6), (10, 9), (29, 6), (29, 9)):
        put(16, 4, 1, 1, x, y)                          # chairs
    r.used = [('rooftop', 0, 0)]
    return r

def piece_sheet():
    F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
    tiles = []
    for name, (src, sx, sy, w, h, kind, *_) in PIECES.items():
        c = cut(name)
        im = Image.fromarray(np.clip(piece_pixels(name), 0, 255).astype(np.uint8)).convert('RGBA')
        m = piece_mask(name); a = np.array(im); a[..., 3] = m * 255; im = Image.fromarray(a)
        im = im.resize((w * 32, h * 32), Image.NEAREST)
        t = Image.new('RGB', (max(im.width, 130) + 8, im.height + 34), (40, 46, 60)); d = ImageDraw.Draw(t)
        t.paste(im, (4, 30), im)
        d.text((4, 2), f'{name} ({SRC[src][2].split("_")[0]})', font=F, fill=(255, 255, 255))
        d.text((4, 15), 'whole' if not c else 'touches ' + ','.join(c), font=F, fill=(140, 230, 140) if not c else (255, 200, 90))
        tiles.append(t)
    W = 2000; rows, row, x = [], [], 0
    for t in tiles:
        if x + t.width > W:
            rows.append(row); row, x = [], 0
        row.append(t); x += t.width + 8
    rows.append(row)
    o = Image.new('RGB', (W, sum(max(t.height for t in rw) + 8 for rw in rows)), (16, 18, 24)); y = 0
    for rw in rows:
        x = 0
        for t in rw:
            o.paste(t, (x, y)); x += t.width + 8
        y += max(t.height for t in rw) + 8
    o.save(EV / 'native-pieces.png')

def elevator_car():
    """The car is Lilycove Dept Store's elevator as it stands (the floor menu is its own script)."""
    _, g, _ = SRC['EL']
    H, W = g.shape
    return np.concatenate([np.concatenate([flat('EL', x, y) for x in range(W)], 1) for y in range(H)], 0)

def sheet(images):
    F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)
    z = 2
    tiles = []
    for title, a in images:
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
        im = im.resize((im.width * z, im.height * z), Image.NEAREST)
        t = Image.new('RGB', (max(im.width + 24, 720), im.height + 52), (24, 27, 36))
        ImageDraw.Draw(t).text((12, 12), title, font=F, fill=(255, 255, 255)); t.paste(im, (12, 42))
        tiles.append(t)
    W = max(t.width for t in tiles)
    o = Image.new('RGB', (W, sum(t.height for t in tiles)), (24, 27, 36)); y = 0
    for t in tiles:
        o.paste(t, (0, y)); y += t.height
    o.save(EV / 'native.png')

def main():
    EV.mkdir(parents=True, exist_ok=True)
    piece_sheet()
    out = []
    for k, title, fn in (('lobby', '1F  Lobby', lobby),
                         ('typical', '2F and 4F  Studio (west), two-bedroom (east): down at the west flight, up at the east', lambda: typical(2)),
                         ('typical_b', '3F and 5F  the same, the flights swapped: down at the east, up at the west', lambda: typical(3)),
                         ('penthouse', '6F  Penthouse', penthouse), ('roof', 'Roof terrace', roof)):
        r = fn()
        Image.fromarray(r.png()).save(EV / f'native-{k}.png')
        out.append((title, r.png()))
        print(k, 'pieces', len(r.used))
    car = elevator_car()
    Image.fromarray(np.clip(car, 0, 255).astype(np.uint8)).save(EV / 'native-elevator.png')
    out.append(('Elevator car  (Lilycove Dept Store elevator)', car))
    sheet(out)

if __name__ == '__main__':
    main()
