"""The apartment block as a plan for the owner (2026-11-03: a full, upscale apartment complex;
1F a lobby with an elevator and stairs; four floors, each with a studio and a two-bedroom
apartment; the penthouse on top; owner's second note: every piece whole, the furniture where it
would stand in a real home).

    python3 tools/gba/maps/celadon_elements/apartments_plan.py

Every piece is a whole FireRed object cut from the room it stands in (PIECES: source room and
cell box), checked against that room: cut() fails if the object's pixels run on past its box.
A piece set in a room of another tileset keeps its own pixels and takes this room's floor or wall
where its source had floor or wall (each source cell is matched pixel for pixel against that
room's own background cells), so a bed on Pallet's olive floor stands on Copycat's cream floor.

    1F            the lobby: HGSS's Condominiums 1F as built (interiors.apartments_grid), with
                  FireRed Condominiums 2F's octagon table and sofa as a seating area, a painting
    2F-5F hall    one hall on every floor: stairs down and up at the two ends, the studio's door,
                  the elevator and its call panel, the two-bedroom's door
    studio        one room in Copycat's house's own pieces (FireRed's Saffron home): kitchen
                  along the back wall, a dining table, the TV on its rug, a bed with a wardrobe
                  and a desk in the far corner
    two-bedroom   FireRed's Condominiums 1F floor plan (FireRed's own Celadon apartment): the
                  long room a living room (sofa, TV on its rug, plants), the middle room the
                  kitchen and dining room, the two side rooms the bedrooms
    6F penthouse  FireRed's Condominiums 2F floor plan: a foyer with the stairs and elevator, a
                  lounge, a dining room and kitchen, a study, the master bedroom, a door to its
                  roof terrace (HGSS's Condominiums roof and its planters)
    elevator      one car (FireRed's Dept Store elevator)

Writes gba/art/celadon-elements/evidence/apartments/*.png (each room, and pieces.png: every
piece on its own) and evidence/apartments-plan.png.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as C                                  # noqa: E402
sys.path.append(str(C.HERE.parent / 'saffron'))
import frlg                                         # noqa: E402
import interiors as I                               # noqa: E402

ENG = C.ROOT.parent / 'pokeemerald-expansion'
OUT = C.EV / 'apartments'
LAYOUTS = {l['name']: l for l in json.loads((ENG / 'data/layouts/layouts.json').read_text())['layouts'] if l}
PAIRS = dict(K=frlg.Pair(ENG, 'building_frlg', 'condominiums_frlg'), G=frlg.Pair(ENG, 'building_frlg', 'generic_building_1_frlg'))

def grid(name):
    l = LAYOUTS[name]
    return np.frombuffer((ENG / l['blockdata_filepath']).read_bytes(), '<u2').reshape(l['height'], l['width']).astype(int) & 0x3FF

SRC = dict(K1=('K', 'CeladonCity_Condominiums_1F_Layout'), K2=('K', 'CeladonCity_Condominiums_2F_Layout'),
           K3=('K', 'CeladonCity_Condominiums_3F_Layout'), KR=('K', 'CeladonCity_Condominiums_Roof_Layout'),
           C1=('G', 'SaffronCity_CopycatsHouse_1F_Layout'), C2=('G', 'SaffronCity_CopycatsHouse_2F_Layout'),
           P1=('G', 'PalletTown_PlayersHouse_1F_Layout'), P2=('G', 'PalletTown_PlayersHouse_2F_FRLG_Layout'))
SRC = {k: (p, grid(n)) for k, (p, n) in SRC.items()}

_flat = {}
def flat(pair, m):
    if (pair, m) not in _flat:
        b, t = PAIRS[pair].cell(m)
        out = b.copy(); a = t[..., 3] > 0; out[a] = t[..., :3][a]
        _flat[(pair, m)] = out.astype(np.int16)
    return _flat[(pair, m)]

def background(src):
    """A source room's black: the one repeated cell always background (rugs, plants and
    furniture repeat too, so repetition alone does not make a cell background)."""
    return SRC[src][0], {0x8}

_modes = {}
def modes(src):
    """A source room's plain background, per row: at every pixel of a cell the colour most of
    that row's cells have there (so a row of wall gives the plain wall, a row of floor the
    floor), and the same down its first floor column (the shade along the left wall)."""
    if src not in _modes:
        pair, g = SRC[src]
        H, W = g.shape
        def mode(cells):
            a = np.stack([flat(pair, int(g[y, x])) for x, y in cells])          # n x 16 x 16 x 3
            key = (a[..., 0].astype(np.int64) << 20) | (a[..., 1].astype(np.int64) << 10) | a[..., 2]
            out = np.zeros((16, 16, 3), np.int16)
            for yy in range(16):
                for xx in range(16):
                    v, n = np.unique(key[:, yy, xx], return_counts=True)
                    k = int(v[n.argmax()]); out[yy, xx] = (k >> 20, (k >> 10) & 1023, k & 1023)
            return out
        floor = mode([(x, y) for y in range(3, H - 1) for x in range(W)])
        # a row's own plain background only where the row is wall (its common colours mostly not
        # the floor's): in a row of floor a big rug can outvote the floor and would vanish
        rows = {}
        for y in range(H):
            m = mode([(x, y) for x in range(W)])
            if (m == floor).all(-1).mean() < 0.3:
                rows[y] = m
        x0 = next(x for x in range(W) if int(g[3, x]) != 0x8)       # the first column inside the room
        left = mode([(x0, y) for y in range(3, H - 1)])
        _modes[src] = (rows, floor, left)
    return _modes[src]

def object_mask(src, x, y):
    """The pixels of source cell (x, y) that are not the room's background: not its row's plain
    background, its floor, the shade along its left wall, nor any cell it repeats."""
    pair, g = SRC[src]
    _, bg = background(src)
    c = flat(pair, int(g[y, x]))
    if int(g[y, x]) in bg:
        return np.zeros((16, 16), bool)
    rows, floor, left = modes(src)
    same = (c == floor).all(-1) | (c == left).all(-1)
    if y in rows:
        same |= (c == rows[y]).all(-1)
    for m in bg:
        same |= (flat(pair, m) == c).all(-1)
    return ~same

# --------------------------------------------------------------------------- the pieces
# name: (source room, x, y, w, h, where it stands) — 'wall' pieces stand against a back wall,
# their top row on the wall top, their second on the wall face; 'floor' pieces stand free.
PIECES = {
    # Copycat's house (Saffron) and the Pallet houses: FireRed's homes. Pieces that touch in
    # their own room (the fridge, sink and cupboard; the desk, shelf and wardrobe) are one piece.
    'kitchen':       ('C1', 1, 0, 5, 3, 'wall'),     # fridge, sink, cupboard and the rice cooker on the floor
    'fridge_sink':   ('C1', 1, 0, 3, 3, 'wall'),
    'cupboard':      ('C1', 4, 0, 2, 3, 'wall'),
    'tv_stand':      ('C1', 7, 0, 1, 3, 'wall'),
    'window_c':      ('C1', 6, 0, 1, 2, 'wall'),
    'dining_rug':    ('C1', 4, 3, 6, 4, 'floor'),     # the rug, its table and four chairs
    'plant_c':       ('C1', 1, 4, 1, 2, 'floor'),
    'mat_c':         ('C1', 3, 8, 3, 2, 'floor'),     # the exit mat and the black under it
    'study':         ('C2', 1, 0, 4, 3, 'wall'),     # the PC on its desk with its chair, a tall shelf, a wardrobe
    'picture_s':     ('C2', 5, 0, 1, 2, 'wall'),
    'picture_w':     ('C2', 6, 0, 2, 2, 'wall'),
    'tv_rug':        ('C2', 2, 3, 5, 5, 'floor'),     # the orange rug, the TV and its console
    'bed':           ('P2', 1, 4, 3, 3, 'floor'),
    'bookcase_g':    ('P2', 4, 0, 2, 3, 'wall'),
    'pc_corner':     ('P2', 1, 0, 3, 3, 'wall'),     # the PC on its desk with its chair, the nightstand
    'calendar':      ('P2', 11, 0, 1, 2, 'wall'),
    # FireRed's Celadon Condominiums
    'sofa':          ('K2', 1, 5, 4, 3, 'wall'),     # the long sofa against a wall
    'sofa_short':    ('K2', 4, 15, 3, 3, 'wall'),
    'sofa_side':     ('K2', 6, 9, 1, 3, 'floor'),     # the sofa end-on, beside a table
    'octagon_table': ('K2', 1, 8, 4, 4, 'floor'),
    'bookcase_k':    ('K2', 5, 5, 2, 3, 'wall'),
    'lobby_table':   ('K1', 1, 9, 4, 5, 'floor'),     # the round table with its two stools
    'cabinet':       ('K1', 2, 15, 2, 3, 'wall'),     # the glass display cabinet
    'painting':      ('K1', 5, 5, 2, 2, 'wall'),
    'phone':         ('K1', 3, 5, 1, 2, 'wall'),
    'window_k':      ('K1', 4, 0, 1, 2, 'wall'),
    'doorway':       ('K1', 1, 0, 3, 2, 'wall'),
    'stairs_up':     ('K1', 4, 0, 3, 4, 'wall'),     # its left column's window is wall here (stairs_up())
    'stairs_down':   ('K3', 0, 0, 2, 4, 'wall'),     # its rail's last pixel is in the next cell, under the wall
    'desk':          ('K3', 0, 8, 3, 3, 'floor'),     # the desk with its PC
    'bookcase_k2':   ('K3', 0, 5, 2, 3, 'wall'),
    'boxes':         ('K3', 3, 12, 1, 2, 'floor'),
    'plant_k':       ('K2', 9, 5, 1, 2, 'floor'),
    'wall_plant_k':  ('K1', 0, 5, 1, 3, 'wall'),
    'mat_k':         ('K1', 11, 18, 3, 2, 'floor'),
    'planter':       ('KR', 11, 4, 2, 2, 'floor'),
}

def cut(name):
    """Where a piece's object runs on past its box in its own room: per side, the number of
    pixel rows or columns along that edge where the object touches both sides of the edge."""
    src, x0, y0, w, h, _ = PIECES[name]
    pair, g = SRC[src]
    H, W = g.shape
    big = np.zeros(((H + 2) * 16, (W + 2) * 16), bool)
    for y in range(max(0, y0 - 1), min(H, y0 + h + 1)):
        for x in range(max(0, x0 - 1), min(W, x0 + w + 1)):
            big[(y + 1) * 16:(y + 2) * 16, (x + 1) * 16:(x + 2) * 16] = object_mask(src, x, y)
    X0, Y0, X1, Y1 = (x0 + 1) * 16, (y0 + 1) * 16, (x0 + w + 1) * 16, (y0 + h + 1) * 16
    out = dict(left=int((big[Y0:Y1, X0] & big[Y0:Y1, X0 - 1]).sum()), right=int((big[Y0:Y1, X1 - 1] & big[Y0:Y1, X1]).sum()),
               top=int((big[Y0, X0:X1] & big[Y0 - 1, X0:X1]).sum()), bottom=int((big[Y1 - 1, X0:X1] & big[Y1, X0:X1]).sum()))
    return {k: v for k, v in out.items() if v}

def piece_pixels(name):
    src, sx, sy, w, h, _ = PIECES[name]
    pair, g = SRC[src]
    return np.concatenate([np.concatenate([flat(pair, int(g[sy + yy, sx + xx])) for xx in range(w)], 1) for yy in range(h)], 0)

def piece_mask(name):
    from scipy import ndimage
    src, sx, sy, w, h, _ = PIECES[name]
    m = np.concatenate([np.concatenate([object_mask(src, sx + xx, sy + yy) for xx in range(w)], 1) for yy in range(h)], 0)
    m = ndimage.binary_closing(np.pad(m, 2), np.ones((3, 3)), iterations=2)[2:-2, 2:-2] | m
    return ndimage.binary_fill_holes(m)

# --------------------------------------------------------------------------- rooms
class Room:
    """A room drawn cell by cell from FireRed metatiles in its own tileset ('K' Condominiums,
    'G' FireRed's homes), pieces from either set laid on with this room's background."""
    def __init__(self, pair, w, h):
        self.pair, self.w, self.h = pair, w, h
        self.img = np.zeros((h * 16, w * 16, 3), np.int16)
        self.bg = np.zeros((h, w), int)                       # each cell's background metatile
        self.solid = np.zeros((h, w), bool)
        self.used = []
    def cell(self, x, y, m, solid=None):
        self.img[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = flat(self.pair, m)
        self.bg[y, x] = m
        if solid is not None:
            self.solid[y, x] = solid
    def piece(self, name, x, y, solid_rows=None):
        """A piece's own pixels laid on (its mask over the whole piece, closed and its holes
        filled, so a pixel inside the object that happens to match the floor stays)."""
        src, sx, sy, w, h, _ = PIECES[name]
        pair, g = SRC[src]
        self.used.append((name, x, y))
        img = piece_pixels(name)
        m = piece_mask(name)
        dst = self.img[y * 16:(y + h) * 16, x * 16:(x + w) * 16]
        dst[m] = img[m]
        for yy in range(h):
            for xx in range(w):
                if m[yy * 16:(yy + 1) * 16, xx * 16:(xx + 1) * 16].any() and (solid_rows is None or yy in solid_rows):
                    self.solid[y + yy, x + xx] = True
    def png(self):
        return np.clip(self.img, 0, 255).astype(np.uint8)

# backgrounds per tileset: (wall top, wall face, floor under the wall, floor, floor's left shade, black)
BG = dict(K=dict(top=0x289, face=0x291, under=0x282, floor=0x281, left=0x282, black=0x8),
          G=dict(top=int(SRC['C1'][1][0, 10]), face=int(SRC['C1'][1][1, 10]), under=int(SRC['C1'][1][2, 9]),
                 floor=0xA9, left=int(SRC['C1'][1][3, 1]), black=0x8))

def shell(pair, w, h, black_left=False):
    """Walls along the back (two rows), floor, the shaded column along the left wall, black
    along the bottom (and down the left, as FireRed's homes have it)."""
    b = BG[pair]
    r = Room(pair, w, h)
    for y in range(h):
        for x in range(w):
            r.cell(x, y, b['floor'])
    x0 = 1 if black_left else 0
    for x in range(x0, w):
        r.cell(x, 0, b['top'], True); r.cell(x, 1, b['face'], True); r.cell(x, 2, b['under'])
    for y in range(3, h - 1):
        r.cell(x0, y, b['left'])
    for x in range(w):
        r.cell(x, h - 1, b['black'], True)
    if black_left:
        for y in range(h):
            r.cell(0, y, b['black'], True)
    return r

def stairs_up(r, x):
    r.piece('stairs_up', x, 0)
    r.cell(x, 0, BG[r.pair]['top']); r.cell(x, 1, BG[r.pair]['face'])
    r.piece('stairs_up', x, 0) if False else None
    src, sx, sy, w, h, _ = PIECES['stairs_up']
    pair, g = SRC[src]
    for yy in range(h):
        for xx in range(1, w):
            r.img[yy * 16:(yy + 1) * 16, (x + xx) * 16:(x + xx + 1) * 16] = flat(pair, int(g[sy + yy, sx + xx]))
    for yy in (2, 3):
        r.img[yy * 16:(yy + 1) * 16, x * 16:(x + 1) * 16] = flat(pair, int(g[sy + yy, sx]))

def stairs_down(r, x):
    src, sx, sy, w, h, _ = PIECES['stairs_down']
    pair, g = SRC[src]
    for yy in range(h):
        for xx in range(w):
            r.img[yy * 16:(yy + 1) * 16, (x + xx) * 16:(x + xx + 1) * 16] = flat(pair, int(g[sy + yy, sx + xx]))
    r.used.append(('stairs_down', x, 0))

def blit(r, src, sx, sy, w, h, x, y):
    """Cells copied whole (walls, a floor plan), the same tileset as the room."""
    pair, g = SRC[src]
    for yy in range(h):
        for xx in range(w):
            r.cell(x + xx, y + yy, int(g[sy + yy, sx + xx]))

# ---- 1F lobby
def lobby():
    r = Room('K', 15, 14)
    g = I.apartments_grid().astype(int)
    for y in range(14):
        for x in range(15):
            r.cell(x, y, int(g[y, x]) & 0x3FF, bool((int(g[y, x]) >> 10) & 3))
    r.piece('painting', 6, 0)
    r.piece('octagon_table', 1, 5)                            # FireRed 2F's seating: the table, the sofa end-on beside it
    r.piece('sofa_side', 6, 6)
    return r

# ---- 2F-5F hall
def hall():
    r = shell('K', 17, 9)
    stairs_down(r, 0)
    r.piece('doorway', 4, 0)                                  # the studio's door
    r.piece('doorway', 7, 0)                                  # the elevator
    r.piece('phone', 10, 0)                                   # its call panel
    r.piece('doorway', 11, 0)                                 # the two-bedroom's door
    stairs_up(r, 14)
    r.piece('plant_k', 3, 6); r.piece('plant_k', 13, 6)
    return r

def fill(r, xs, ys, m):
    for y in ys:
        for x in xs:
            r.cell(x, y, m)

def wall_band(r, xs, top, pair='K'):
    """A run of back wall: its top, its face, and the shaded floor under it."""
    b = BG[pair]
    fill(r, xs, [top], b['top']); fill(r, xs, [top + 1], b['face']); fill(r, xs, [top + 2], b['under'])

# ---- the studio: one room in Copycat's house's own pieces
def studio():
    r = shell('G', 13, 10, black_left=True)
    r.piece('kitchen', 1, 0)                                  # kitchenette along the back wall, left
    r.piece('study', 6, 0)                                    # desk and PC, shelf and wardrobe in the middle
    r.piece('bed', 10, 1)                                     # the bed, its head to the back wall, in the far corner
    r.piece('dining_rug', 1, 3)                               # the dining table in front of the kitchen
    r.piece('tv_stand', 9, 4) if False else None
    r.piece('plant_c', 12, 5); r.piece('plant_c', 9, 6)
    r.piece('mat_c', 4, 8)
    return r

# ---- the two-bedroom: FireRed's Condominiums 1F floor plan, its four rooms
def two_bed():
    pair, g = SRC['K1']
    H, W = g.shape
    K = BG['K']
    r = Room('K', W, H)
    for y in range(H):
        for x in range(W):
            r.cell(x, y, int(g[y, x]))
    cap_top, cap_face = int(g[15, 8]), int(g[16, 8])          # FireRed's end of a run of wall
    # bedroom 2, top left (x 0-6, rows 0-4): FireRed's stairs out; a doorway at x 6 down into the kitchen
    wall_band(r, range(0, 7), 0); fill(r, range(1, 7), [3], K['floor']); r.cell(0, 3, K['left'])
    r.cell(6, 4, K['floor']); r.cell(6, 5, K['floor']); r.cell(6, 6, K['floor'])
    r.cell(5, 5, cap_top); r.cell(5, 6, cap_face)
    # the kitchen and dining room, middle left (x 0-6, rows 5-13): FireRed's plants, table, phone out
    fill(r, range(0, 5), [5], K['top']); fill(r, range(0, 5), [6], K['face']); fill(r, range(0, 6), [7], K['under'])
    fill(r, range(1, 7), range(8, 14), K['floor']); fill(r, [0], range(8, 14), K['left']); r.cell(6, 7, K['floor'])
    # bedroom 1, bottom left (x 0-8, rows 15-18): FireRed's plant and cabinet out
    fill(r, range(0, 8), [15], K['top']); fill(r, range(0, 8), [16], K['face'])
    fill(r, range(0, 9), [17], K['under']); fill(r, range(1, 9), [18], K['floor']); r.cell(0, 18, K['left'])
    # the living room, the long room (x 9-14): FireRed's plants and painting out
    wall_band(r, range(9, 15), 0); fill(r, range(10, 15), range(3, 18), K['floor']); fill(r, [9], range(3, 18), K['left'])
    fill(r, range(9, 11), [18], K['floor']); r.cell(14, 18, K['floor'])
    # furniture
    r.piece('bed', 0, 1)                                      # bedroom 2: the bed's head to the wall,
    r.piece('pc_corner', 3, 0)                                # a desk and nightstand beside it
    r.piece('kitchen', 0, 5)                                  # the kitchen along its wall,
    r.piece('lobby_table', 1, 9)                              # the dining table with its stools in front
    r.piece('plant_k', 5, 12)
    r.piece('bed', 0, 16)                                     # bedroom 1: the bed's head to the wall,
    r.piece('study', 4, 15)                                   # desk, shelf and wardrobe along it
    r.piece('sofa', 10, 0)                                    # the living room as FireRed's lounge: the sofa
    r.piece('tv_stand', 14, 0)                                # against the back wall, the TV on its stand beside it,
    r.piece('octagon_table', 10, 4)                           # the coffee table in front of the sofa
    r.piece('bookcase_k', 13, 9) if False else None
    r.piece('plant_k', 14, 5); r.piece('plant_k', 14, 10); r.piece('plant_k', 10, 12); r.piece('plant_k', 14, 15)
    return r

# ---- the penthouse: FireRed's Condominiums 2F floor plan
def penthouse():
    pair, g = SRC['K2']
    H, W = g.shape
    K = BG['K']
    r = Room('K', W, H)
    for y in range(H):
        for x in range(W):
            r.cell(x, y, int(g[y, x]))
    # the foyer, top left: FireRed's stairs (left) stay, its right stairs out for the elevator;
    # the foyer opens east into the long room through the wall between them (rows 2-3)
    wall_band(r, range(0, 7), 0); fill(r, range(1, 7), [3], K['floor']); r.cell(0, 3, K['left'])
    stairs_down(r, 0)                                         # down to 5F
    r.piece('doorway', 3, 0); r.piece('phone', 6, 0)
    fill(r, [7, 8], [2, 3], K['floor'])
    r.cell(7, 4, int(g[0, 7])); r.cell(8, 4, int(g[0, 8]))    # the wall between them starts again (its top end)
    # the lounge, middle left: FireRed 2F's own sofa, bookcase, table, side sofa and plant stay
    # the master bedroom, bottom left: FireRed's sofa out for the bed
    fill(r, range(1, 8), [15], K['top']); fill(r, range(1, 8), [16], K['face']); fill(r, range(1, 9), [17], K['under'])
    fill(r, range(1, 9), [18], K['floor'])
    r.piece('bed', 1, 16)                                     # the bed, its head to the wall,
    r.piece('pc_corner', 4, 15)                               # desk and nightstand beside it
    r.piece('painting', 6, 15) if False else None
    # the long room (x 9-14): FireRed's stairs and plants out; kitchen, dining, study
    wall_band(r, range(9, 15), 0); fill(r, range(10, 15), range(3, 18), K['floor']); fill(r, [9], range(3, 18), K['left'])
    fill(r, range(9, 11), [18], K['floor']); r.cell(14, 18, K['floor'])
    r.piece('kitchen', 9, 0); r.piece('window_k', 14, 0)
    r.piece('lobby_table', 10, 4)                             # the dining table
    r.piece('desk', 11, 12)                                   # the study
    r.piece('plant_k', 14, 4); r.piece('plant_k', 9, 11); r.piece('plant_k', 14, 16)
    blit(r, 'K1', 11, 18, 3, 2, 11, 18)                       # the mat out to the roof terrace
    return r

def terrace():
    W, H = 17, 12
    r = Room('K', W, H)
    for y in range(H):
        for x in range(W):
            r.cell(x, y, 0x306)
    for x in range(W):
        r.cell(x, 0, 0x328); r.cell(x, 1, 0x320); r.cell(x, H - 1, 0x320)
    for y in range(2, H - 1):
        r.cell(0, y, 0x321); r.cell(W - 1, y, 0x322)
    r.cell(0, 1, 0x319); r.cell(W - 1, 1, 0x31a); r.cell(0, H - 1, 0x329); r.cell(W - 1, H - 1, 0x32a)
    for x in range(6, 11):
        r.cell(x, 2, 0x289); r.cell(x, 3, 0x291)
    src, sx, sy, w, h, _ = PIECES['doorway']
    for xx in range(3):
        for yy in range(2):
            r.img[(2 + yy) * 16:(3 + yy) * 16, (7 + xx) * 16:(8 + xx) * 16] = flat('K', int(SRC['K1'][1][sy + yy, sx + xx]))
    for x, y in ((2, 5), (2, 8), (13, 5), (13, 8), (7, 8)):
        r.piece('planter', x, y)
    return r

def elevator():
    sp = frlg.Pair(ENG, 'building_frlg', 'condominiums_frlg')
    sd = ENG / 'data/tilesets/secondary/silph_co_frlg'
    sm = np.frombuffer((sd / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
    sp.meta.update({frlg.NT + i: [int(v) for v in sm[i]] for i in range(len(sm))})
    PAIRS['S'] = sp
    g = grid('CeladonCity_DepartmentStore_Elevator_Layout')
    r = Room('S', g.shape[1], g.shape[0])
    for y in range(g.shape[0]):
        for x in range(g.shape[1]):
            r.cell(x, y, int(g[y, x]))
    return r

# --------------------------------------------------------------------------- review and sheet
def piece_sheet():
    """Every piece on its own, on its own tileset's floor (wall pieces against a wall), with its
    cut check."""
    F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
    tiles, report = [], {}
    for name, (src, sx, sy, w, h, kind) in PIECES.items():
        pair = SRC[src][0]
        r = shell(pair, w + 2, h + 2) if kind == 'wall' else Room(pair, w + 2, h + 2)
        if kind != 'wall':
            for y in range(h + 2):
                for x in range(w + 2):
                    r.cell(x, y, BG[pair]['floor'])
        if name.startswith('stairs'):
            (stairs_up if name == 'stairs_up' else stairs_down)(r, 1)
        else:
            r.piece(name, 1, 0 if kind == 'wall' else 1)
        report[name] = cut(name)
        im = Image.fromarray(r.png()).resize(((w + 2) * 32, (h + 2) * 32), Image.NEAREST)
        t = Image.new('RGB', (max(im.width, 150), im.height + 30), (24, 28, 36)); d = ImageDraw.Draw(t)
        t.paste(im, (0, 28)); d.text((2, 2), name, font=F, fill=(255, 255, 255))
        d.text((2, 14), 'whole' if not report[name] else 'CUT ' + str(report[name]), font=F,
               fill=(140, 230, 140) if not report[name] else (255, 90, 90))
        tiles.append(t)
    W = 2200
    rows, row, x = [], [], 0
    for t in tiles:
        if x + t.width > W:
            rows.append(row); row, x = [], 0
        row.append(t); x += t.width + 10
    rows.append(row)
    H = sum(max(t.height for t in rw) + 10 for rw in rows)
    o = Image.new('RGB', (W, H), (16, 18, 24)); y = 0
    for rw in rows:
        x = 0
        for t in rw:
            o.paste(t, (x, y)); x += t.width + 10
        y += max(t.height for t in rw) + 10
    o.save(OUT / 'pieces.png')
    return report

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob('*.png'):
        f.unlink()
    report = piece_sheet()
    rooms = dict(lobby=lobby(), hall=hall(), studio=studio(), two_bed=two_bed(), penthouse=penthouse(), terrace=terrace(),
                 elevator=elevator())
    for k, r in rooms.items():
        Image.fromarray(r.png()).save(OUT / f'{k}.png')
    (OUT / 'pieces.json').write_text(json.dumps(dict(cut={k: v for k, v in report.items() if v},
                                                     used={k: r.used for k, r in rooms.items()}), indent=1) + '\n')
    print('cut pieces:', {k: v for k, v in report.items() if v})
    sheet(rooms)

def sheet(rooms):
    F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 16)
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
    big = lambda k, z=2: Image.fromarray(rooms[k].png()).resize((rooms[k].w * 16 * z, rooms[k].h * 16 * z), Image.NEAREST)
    stack = [('Roof', 'Penthouse terrace (private)', ''), ('6F', 'Penthouse', 'stairs down'),
             ('5F', 'Studio 5A, two-bedroom 5B', 'stairs down, up'), ('4F', 'Studio 4A, two-bedroom 4B', 'stairs down, up'),
             ('3F', 'Studio 3A, two-bedroom 3B', 'stairs down, up'), ('2F', 'Studio 2A, two-bedroom 2B', 'stairs down, up'),
             ('1F', 'Lobby; the door to Celadon (28, 14)', 'stairs up')]
    bw, bh = 360, 46
    st = Image.new('RGB', (bw + 240, len(stack) * (bh + 8) + 40), (16, 18, 24)); d = ImageDraw.Draw(st)
    d.text((10, 6), 'The building', font=F, fill=(255, 230, 120))
    for i, (fl, what, how) in enumerate(stack):
        y = 34 + i * (bh + 8)
        d.rectangle((10, y, 10 + bw, y + bh), outline=(200, 200, 200), fill=(40, 46, 60))
        d.text((20, y + 6), fl, font=F, fill=(255, 255, 255)); d.text((70, y + 8), what, font=f, fill=(230, 230, 230))
        d.text((70, y + 26), how, font=f, fill=(150, 200, 255))
        if fl != 'Roof':
            d.rectangle((bw + 30, y, bw + 80, y + bh), outline=(255, 200, 120), fill=(70, 56, 40))
            d.text((bw + 38, y + 14), 'lift', font=f, fill=(255, 220, 160))
    d.text((bw + 90, 40), 'One elevator,\nevery floor\n1F-6F. The\nterrace is\nthrough the\npenthouse.', font=f, fill=(220, 220, 220))
    panels = [
        ('1F  Lobby', 'lobby', ["HGSS's Condominiums 1F (built): elevator, directory", "board, display cabinet, stairs up. Added: a painting,", "FireRed's octagon table with its side sofa"]),
        ('2F-5F  Hall (every floor)', 'hall', ["Stairs down (left) and up (right); the studio's door,", "the elevator with its call panel, the two-bedroom's door"]),
        ('Studio (2A-5A)', 'studio', ["One room in Copycat's house's own pieces: kitchen", "along the back wall with the dining table in front,", "a desk, shelf and wardrobe, the bed in the far corner"]),
        ('Two-bedroom (2B-5B)', 'two_bed', ["FireRed's own Celadon Condominiums floor plan:", "living room (sofa, coffee table, TV), kitchen and", "dining room, bedroom 2 (top left, through a doorway", "from the kitchen), bedroom 1 (bottom left)"]),
        ('6F  Penthouse', 'penthouse', ["FireRed's Condominiums 2F floor plan: foyer with the", "stairs down and the elevator; lounge; kitchen, dining", "table and study; master bedroom; the mat at the", "bottom right leads out to the terrace"]),
        ('Roof  Penthouse terrace', 'terrace', ["HGSS's Condominiums roof: planters, the", "penthouse's door; reached only through it"]),
        ('Elevator', 'elevator', ["One car (FireRed's Dept Store elevator),", "a floor menu for 1F-6F"]),
    ]
    blocks = []
    for title, k, notes in panels:
        im = big(k)
        b = Image.new('RGB', (im.width + 440, im.height + 34), (24, 28, 36)); dd = ImageDraw.Draw(b)
        dd.text((6, 4), title, font=F, fill=(255, 230, 120)); b.paste(im, (6, 28))
        for i, n in enumerate(notes):
            dd.text((im.width + 20, 34 + i * 19), n, font=f, fill=(235, 235, 235))
        blocks.append(b)
    cols = [[blocks[0], blocks[1], blocks[6]], [blocks[2], blocks[3]], [blocks[4], blocks[5]]]
    colw = [max(b.width for b in c) for c in cols]
    H = max(st.height, max(sum(b.height + 12 for b in c) for c in cols)) + 60
    W = st.width + sum(colw) + 20 * (len(cols) + 2)
    o = Image.new('RGB', (W, H), (16, 18, 24)); d = ImageDraw.Draw(o)
    d.text((12, 10), "Celadon apartments: an upscale apartment block (plan; only the lobby's room is built).  Every piece: evidence/apartments/pieces.png",
           font=F, fill=(255, 255, 255))
    o.paste(st, (12, 40))
    x = st.width + 30
    for c, cw in zip(cols, colw):
        y = 40
        for b in c:
            o.paste(b, (x, y)); y += b.height + 12
        x += cw + 20
    o.save(C.EV / 'apartments-plan.png')
    print(o.size)

if __name__ == '__main__':
    main()
