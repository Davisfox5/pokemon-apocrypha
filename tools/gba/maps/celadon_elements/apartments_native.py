"""The apartment block from its floor plans in Gen 3's own pieces (owner, 2026-11-04: "splice
gen 4 conversions and gen 3 native tiles into the same map"; native or existing elements in
place of every custom or converted one).

    python3 tools/gba/maps/celadon_elements/apartments_native.py

Every element is a whole metatile piece from an Emerald or FireRed room in the engine, checked
whole against its own room (cut(): an object whose pixels run past its box is flagged), laid on
by its own pixels over this room's floor and walls. HGSS conversions stay only where neither game
has the element (NATIVE_GAPS; none so far). The floor plans' geometry (apartments_floorplans.py)
is kept: rooms, walls, doorways, the core.

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
    stairs     FireRed's Condominiums stairs up and down, its doorway, its call panel

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
import apartments_floorplans as FP                  # noqa: E402

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
                 EL='LilycoveCity_DepartmentStoreElevator').items():
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
    'window':       ('K1', 4, 0, 1, 2, 'wall'), 'stairs_mu': ('MU', 15, 0, 3, 2, 'wall'),
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
    'stairs_up':    ('K1', 5, 0, 2, 4, 'wall'), 'stairs_down': ('K3', 0, 0, 2, 4, 'cells'), 'doorway': ('K1', 1, 0, 3, 2, 'wall'),
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

# --------------------------------------------------------------------------- the shell's cells
# (source, x, y) of each background cell: floors repeat with their own 2 x 2 period
SHELL = dict(
    wall_top=[('MU', 3, 0), ('MU', 4, 0)], wall_face=[('MU', 3, 1), ('MU', 4, 1)],
    ew_cap=[('MU', 4, 4), ('MU', 5, 4)], ew_face=[('MU', 4, 6), ('MU', 5, 6)],
    ns_cap=[('MU', 9, 7)], ns_end=[('MU', 9, 8)],
    marble=[('MU', 10, 10), ('MU', 11, 10), ('MU', 10, 11), ('MU', 11, 11)],
    wood=[('B1', 7, 5), ('B1', 8, 5), ('B1', 7, 6), ('B1', 8, 6)],
    carpet=[('LO', 9, 6), ('LO', 10, 6), ('LO', 9, 7), ('LO', 10, 7)],
    red=[('DV', 13, 5), ('DV', 14, 5), ('DV', 13, 6), ('DV', 14, 6)],
    paving=[('RT', 3, 3), ('RT', 4, 3), ('RT', 3, 4), ('RT', 4, 4)],
    black=[('K1', 0, 19)])
FLOOR_OF = dict(lobby='marble', core='marble', living='wood', kitchen='wood', bed='carpet', closet='wood', study='wood',
                terrace='paving', red='red')

def shell_cell(name, x, y):
    cells = SHELL[name]
    if len(cells) == 4:
        src, sx, sy = cells[(y % 2) * 2 + (x % 2)]
    else:
        src, sx, sy = cells[x % len(cells)]
    return flat(src, sx, sy)

class Room:
    def __init__(self, plan, floor_over=None):
        W, H = FP.W, FP.H
        self.W, self.H = W, H
        self.img = np.zeros((H * 16, W * 16, 3), np.int16)
        self.solid = np.zeros((H, W), bool)
        self.used = []
        kind = np.full((H, W), 'void', '<U8'); style = np.full((H, W), 'core', '<U8')
        for (x0, y0, x1, y1), k, _ in plan['rooms']:
            kind[y0:y1 + 1, x0:x1 + 1] = 'floor'; style[y0:y1 + 1, x0:x1 + 1] = k
        if floor_over:
            for k, v in floor_over.items():
                style[style == k] = v
        wall = np.zeros((H, W), bool); wall[0:2, :] = True
        for (x0, y0, x1, y1) in plan['walls']:
            wall[y0:y1 + 1, x0:x1 + 1] = True
        doors = set(plan['doors'])
        for x, y in doors:
            wall[y, x] = False; kind[y, x] = 'floor'
            yy = y
            while (x, yy) in doors and yy < H - 1:
                yy += 1
            style[y, x] = style[yy, x] if kind[yy, x] == 'floor' else style[max(0, y - 1), x]
        wall[H - 1, :] = False
        kind[wall] = 'wall'; kind[H - 1, :] = 'void'
        self.kind, self.style, self.wall = kind, style, wall
        for y in range(H):
            for x in range(W):
                sl = np.s_[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
                if kind[y, x] == 'floor':
                    self.img[sl] = shell_cell(FLOOR_OF.get(style[y, x], 'wood'), x, y)
                elif kind[y, x] == 'void':
                    self.img[sl] = shell_cell('black', x, y); self.solid[y, x] = True
                else:
                    self.solid[y, x] = True
                    self.img[sl] = shell_cell(self.wall_kind(x, y), x, y)
    def wall_kind(self, x, y):
        """The museum's walls by the game's rule: the north wall its top and face; an east-west
        wall (a wall cell with wall east or west of it) its cap over its face; a north-south
        wall its cap down its length and its face at its foot."""
        H, W, wall = self.H, self.W, self.wall
        if y <= 1:
            return 'wall_top' if y == 0 else 'wall_face'
        floor_below = y + 1 < H and not wall[y + 1, x]
        ew = (x > 0 and wall[y, x - 1]) or (x + 1 < W and wall[y, x + 1])
        if ew and not (y + 1 < H and wall[y + 1, x] and not ((x > 0 and wall[y + 1, x - 1]) or (x + 1 < W and wall[y + 1, x + 1]))):
            return 'ew_face' if floor_below else 'ew_cap'
        return 'ns_end' if floor_below else 'ns_cap'
    def piece(self, name, x, y, solid=True):
        """A whole piece by its own pixels, its top-left cell at (x, y) ('cells' pieces whole
        below the wall rows: a stairwell's own dark is the piece)."""
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

# --------------------------------------------------------------------------- the floors
def core(r, up=True, down=True):
    r.piece('elevator', 11, 0)
    if down:
        r.piece('stairs_down', 13, 0)
    if up:
        r.piece('stairs_up', 15, 0)
    r.piece('plant', 11, 12); r.piece('plant', 16, 12)

def lobby():
    p = FP.lobby()
    r = Room(p)
    core(r, down=False)
    r.piece('painting_a', 0, 0); r.piece('books_fc', 2, 0); r.piece('pc', 4, 0)  # the office: shelves and a desk
    r.piece('counter', 7, 7)                                                      # the concierge desk facing the door
    r.piece('painting_b', 18, 0); r.piece('painting_d', 22, 0); r.piece('painting_a', 26, 0)
    r.piece('lounge', 20, 7)                                                      # the lounge: sofa, armchairs, table
    r.piece('statue_a', 9, 12); r.piece('statue_b', 18, 12)
    r.piece('planter', 0, 12); r.piece('planter', 29, 12); r.piece('glass_case', 30, 3); r.piece('glass_case', 30, 5)
    return r

def typical():
    p = FP.typical()
    r = Room(p)
    core(r)
    # the studio: the kitchen and the TV along the window wall, the dining set below the kitchen,
    # FireRed's end-on sofa and a low table by the TV; the bed and a rug in the sleeping half
    r.piece('kitchen', 0, 0); r.piece('window', 5, 0); r.piece('clock', 6, 0); r.piece('tv_wall', 7, 0)
    r.piece('dining_b1', 0, 4)
    r.piece('table_w', 7, 4); r.piece('sofa_side', 9, 3)
    r.piece('bed', 0, 11); r.piece('rug_blue', 4, 10); r.piece('plant', 9, 13); r.piece('plant', 0, 8)
    # the two-bedroom: a bed and a desk or shelves in each bedroom
    r.piece('pc', 18, 0); r.piece('picture', 20, 0); r.piece('bed', 21, 2)
    r.piece('books_lo', 25, 0); r.piece('drawers', 30, 0); r.piece('bed', 28, 2)
    # its open room: the kitchen on the bedrooms' wall between their doors, the dining set below it,
    # FireRed's sofas round a low table on the left
    r.piece('kitchen_in', 22, 6)
    r.piece('dining_b1', 24, 10)
    r.piece('sofa_fr', 18, 10); r.piece('sofa_side', 22, 11); r.piece('table_w', 19, 12)
    r.piece('plant', 30, 8)
    return r

def penthouse():
    p = FP.penthouse()
    r = Room(p, floor_over=dict(living='red', bed='red'))
    core(r)
    # the great room: the kitchen and Devon's black sofa on the window wall, its glass table and an
    # armchair before the sofa, Lorelei's dining set below the kitchen, a display corner
    r.piece('kitchen', 0, 0); r.piece('sofa_black', 6, 0)
    r.piece('glass_table', 5, 3); r.piece('armchair_l', 4, 3)
    r.piece('dining_lo', 0, 8)
    r.piece('glass_case', 9, 9); r.piece('glass_case', 9, 11); r.piece('plant', 0, 13); r.piece('plant', 9, 13)
    # the study: shelves and the desk
    r.piece('books_fc', 18, 0); r.piece('pc', 20, 0); r.piece('plant', 22, 4)
    # the master bedroom: a painting, shelves and the bed
    r.piece('painting_d', 24, 0); r.piece('books_lo', 26, 0); r.piece('drawers', 30, 0); r.piece('bed', 27, 2)
    # the guest room and the walk-in closet
    r.piece('cupboard_lo', 18, 9); r.piece('bed', 20, 11)
    r.piece('drawers', 25, 9); r.piece('cupboard_lo', 28, 9); r.piece('glass_case', 24, 12); r.piece('glass_case', 30, 12)
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
    side the west side flipped (Gen 3 flips tiles). The stair house, vending machines, planters,
    benches and chairs are the rooftop's own."""
    p = FP.roof()
    W, H = FP.W, FP.H
    r = Room(p)
    r.solid[:] = False
    def col(x):
        if x == 0: return 0, False
        if x == W - 1: return 0, True
        if x == 1: return 1, False
        return 3 + (x % 2), False
    def row(y):
        if y <= 1: return y
        if y >= H - 4: return y - (H - 4) + 6          # the south railing, the edge, the parapet, the wall below
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
    r.kind[:] = 'floor'
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
    put(12, 1, 3, 3, 14, 1, cells=True)                 # the stair house (its door the stairs down)
    r.solid[3, 15] = False
    put(9, 0, 2, 2, 11, 0, cells=True)                  # vending machines in the railing
    for x, y in ((2, 3), (2, 7), (27, 3), (27, 7)):
        put(1, 2, 2, 2, x, y)                           # planters
    for x, y in ((6, 6), (6, 9), (21, 6), (21, 9)):
        put(5, 5, 2, 1, x, y)                           # benches
    for x, y in ((9, 6), (9, 9), (24, 6), (24, 9)):
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
    for k, title in dict(lobby='1F  Lobby', typical='2F-5F  Studio (west) and two-bedroom (east)',
                         penthouse='6F  Penthouse', roof='Roof terrace').items():
        r = globals()[k]()
        Image.fromarray(r.png()).save(EV / f'native-{k}.png')
        out.append((title, r.png()))
        print(k, 'pieces', len(r.used))
    car = elevator_car()
    Image.fromarray(np.clip(car, 0, 255).astype(np.uint8)).save(EV / 'native-elevator.png')
    out.append(('Elevator car  (Lilycove Dept Store elevator)', car))
    sheet(out)

if __name__ == '__main__':
    main()
