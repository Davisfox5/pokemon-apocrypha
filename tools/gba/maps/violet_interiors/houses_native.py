"""Violet's five campus homes from floor plans, built from Gen 3's own pieces (owner, November 4: "create a
floor plan that makes sense for the type of building ... that a Pokemon game can actually accommodate.
And then ... put the tiles and elements that we have available to us in the places that they need to go").

The game's rules for a house: one room per map, 11 x 9 squares like HGSS's Violet house; the north wall
two rows deep, its furniture standing against it; the exit mat at the foot of the room (4, 8) where the
town's door leads in; one-square gaps between furniture so every piece can be reached.

Every piece is a whole rectangle of metatiles from a FireRed room in the engine, with its own collision
and behaviour (a TV is a TV, a bookshelf a bookshelf): Pallet Town's two houses for the kitchen, TV,
dining set, beds, PC, bookshelves, plants, walls, floor and mat; Lavender's volunteer house for its table;
Fuchsia's house for its rug and reading table; the Fighting Dojo for the sage's home (its green wall with
round windows and scrolls, planks, tatami, potted plant, mat). Pieces from a room with another floor go
on by their own pixels (native.Source.object). The sage's Bellsprout statue is Sprout Tower's
(sprout_native.statue), the one element no Gen 3 room has.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE)]
import native as N                        # noqa: E402

PX = 16
W, H = 11, 10                             # the room 11 x 9, a black row below
EXIT = (4, 8)

P1, P2 = 'PalletTown_PlayersHouse_1F', 'PalletTown_PlayersHouse_2F_FRLG'
LV, F2, DJ = 'LavenderTown_VolunteerPokemonHouse', 'FuchsiaCity_House2', 'SaffronCity_Dojo'

# name: (source room, x, y, w, h) -- the piece's rectangle in its room
PIECES = {
    'kitchen':   (P1, 1, 0, 4, 3),        # sink, worktop, stove, its hood on the wall
    'tv':        (P1, 6, 0, 1, 3),
    'window':    (P1, 7, 0, 2, 2),
    'dining':    (P1, 4, 3, 6, 4),        # the table and four chairs on the green rug
    'plant':     (P1, 12, 6, 1, 2),
    'mat':       (P1, 3, 8, 3, 1),
    'pc':        (P2, 1, 0, 1, 3),
    'desk':      (P2, 2, 1, 1, 2),
    'shelf':     (P2, 4, 0, 2, 3),        # the bookshelf, two wide
    'bed':       (P2, 1, 4, 3, 3),
    'notice':    (P2, 11, 0, 1, 2),       # the town map on the wall
    'table4':    (LV, 4, 4, 4, 2),        # Lavender's table with its chairs
    'reading':   (F2, 5, 4, 5, 4),        # Fuchsia's rug with a table and stool
    'dj_plant':  (DJ, 6, 2, 1, 2),
    'dj_mat':    (DJ, 5, 14, 3, 1),
    'tatami':    None,                    # built below from the dojo's tatami edges
}

class House:
    def __init__(self, name, kit='frlg'):
        self.name, self.W, self.H = name, W, H
        self.lower = np.zeros((H * PX, W * PX, 3), np.uint8)
        self.upper = np.zeros((H * PX, W * PX, 4), np.uint8)
        self.blocked = np.ones((H, W), bool)
        self.behaviors, self.notes, self.rect = {}, [], (0, 0, W, H)
        self.beh = {}                     # (x, y): native behaviour value
        self.plan = {}                    # (x, y): piece name, for the floor plan sheet
        self.kit = kit
        self.shell()
    def inside(self, x, y):
        return True
    def layers(self):
        return self.lower.copy(), self.upper.copy()
    def image(self):
        out = self.lower.copy(); a = self.upper[..., 3] > 0; out[a] = self.upper[..., :3][a]
        return out
    def sl(self, x, y):
        return np.s_[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX]
    def cell_from(self, src, sx, sy, x, y, whole=True):
        s = N.Source(src); c = s.cell(sx, sy)
        if whole:
            self.lower[self.sl(x, y)] = c['bot']
            if c['layer'] == 1:                    # covered: both layers under the player
                a = c['top'][..., 3] > 0
                self.lower[self.sl(x, y)][a] = c['top'][..., :3][a]
                self.upper[self.sl(x, y)] = 0
            else:
                self.upper[self.sl(x, y)] = c['top']
        else:
            m = s.object(sx, sy)
            f = s.flat(sx, sy)
            self.lower[self.sl(x, y)][m] = f[m]
        self.blocked[y, x] = c['blocked']
        if c['behavior']:
            self.beh[(x, y)] = c['behavior']
    def shell(self):
        if self.kit == 'dojo':
            # the dojo's wall: round windows and scrolls on its green, planks, the wall's shade
            row0 = [3, 3, 2, 3, 5, 3, 5, 3, 2, 3, 3]                 # dojo columns: 3 plain, 2 window, 5 scroll
            for x, sx in enumerate(row0):
                self.cell_from(DJ, sx, 1, x, 0); self.cell_from(DJ, sx, 2, x, 1)
            for y in range(2, 9):
                for x in range(W):
                    self.cell_from(DJ, 2, 3 if y == 2 else 4, x, y)
        else:
            for x in range(W):
                self.cell_from(P1, 9, 0, x, 0); self.cell_from(P1, 9, 1, x, 1)
            for y in range(2, 9):
                for x in range(W):
                    self.cell_from(P1, 9 if y == 2 else 2, 2 if y == 2 else 4, x, y)
        for x in range(W):                          # the black row below the room
            self.lower[self.sl(x, 9)] = 0; self.blocked[9, x] = True
    def place(self, name, x, y, whole=True):
        src, sx, sy, w, h = PIECES[name]
        for j in range(h):
            for i in range(w):
                self.cell_from(src, sx + i, sy + j, x + i, y + j, whole)
                self.plan[(x + i, y + j)] = name
    def tatami(self, x, y, w, h):
        """The dojo's tatami, its edges and middle (SaffronCity_Dojo x 4-8, rows 7-11)."""
        for j in range(h):
            sy = 7 if j == 0 else (11 if j == h - 1 else 8)
            for i in range(w):
                sx = 4 if i == 0 else (8 if i == w - 1 else 5)
                self.cell_from(DJ, sx, sy, x + i, y + j)
                self.plan[(x + i, y + j)] = 'tatami'
    def statue(self, x, y):
        import sprout_native as SN
        st = SN.statue(SN.ramp())
        top, bot = st[:16], st[16:]
        for img, yy, upper in ((top, y - 1, True), (bot, y, False)):
            a = img[..., 3] > 0
            if upper:
                self.upper[self.sl(x, yy)][a] = img[a]
            else:
                self.lower[self.sl(x, yy)][a] = img[..., :3][a]
        self.blocked[y, x] = True
        self.plan[(x, y)] = self.plan[(x, y - 1)] = 'statue'
    def finish(self):
        retone(self)
        self.behaviors[EXIT] = 'exit'
        self.blocked[EXIT[1], EXIT[0]] = False
        return self

# --------------------------------------------------------------------------- HGSS's palette (owner, November 5)
# The pieces stay FireRed's; their colours take HGSS's Violet house (T22R0401) by material, lightest to
# lightest: the floor's olive parquet becomes HGSS's wood (its five browns), the wall's cream and blue stripe
# HGSS's cream wall and brown trim, Lavender's tiles HGSS's grey kitchen stone, the dojo's pale planks HGSS's
# wood and its green wall HGSS's cream.
HGSS_WOOD = [(148, 99, 33), (173, 132, 90), (181, 140, 99), (189, 148, 99), (198, 156, 107)]
HGSS_WALL = {'cream': (247, 239, 214), 'shade': (231, 214, 173), 'light': (255, 251, 239),
             'trim': (214, 156, 90), 'dark': (148, 99, 33), 'outline': (99, 66, 33)}
HGSS_STONE = [(148, 140, 123), (156, 156, 140), (181, 181, 165), (206, 206, 189)]

def _colours(src, cells):
    s = N.Source(src)
    from collections import Counter
    c = Counter()
    for x, y in cells:
        c.update(map(tuple, s.flat(x, y).reshape(-1, 3)))
    return c

def _by_light(cols):
    return sorted(cols, key=lambda c: 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2])

def ramp_map(cols, target):
    """Each colour onto the target ramp by its lightness rank."""
    cols = _by_light(cols)
    n, m = len(cols), len(target)
    return {c: target[min(m - 1, round(i * (m - 1) / max(1, n - 1)))] for i, c in enumerate(cols)}

def retone_map(kit):
    out = {}
    if kit == 'dojo':
        out.update(ramp_map(list(_colours(DJ, [(2, 4), (2, 3)])), HGSS_WOOD[1:]))
        wall = _colours(DJ, [(3, 1), (3, 2)])
        for c in _by_light(wall):
            pass
        light = _by_light(list(wall))
        out.update(ramp_map(light, [HGSS_WALL['dark'], HGSS_WALL['trim'], HGSS_WALL['shade'], HGSS_WALL['cream'], HGSS_WALL['light']]))
        out.update(ramp_map(list(_colours(LV, [(2, 6), (1, 3)])), HGSS_STONE))
    else:
        floor = [c for c in _colours(P1, [(2, 4), (9, 2)]) if c != (123, 123, 123)]
        out.update(ramp_map(floor, HGSS_WOOD))
        out[(123, 123, 123)] = (156, 115, 74)                    # the parquet's grey studs: a darker wood
        out.update({(213, 213, 172): HGSS_WALL['cream'], (197, 197, 148): HGSS_WALL['shade'],
                    (255, 255, 255): HGSS_WALL['light'], (139, 180, 222): HGSS_WALL['trim'],
                    (82, 82, 106): HGSS_WALL['outline']})
        out.update(ramp_map(list(_colours(LV, [(2, 6), (1, 3)])), HGSS_STONE))
    return out

def retone(h):
    m = retone_map(h.kit)
    for arr in (h.lower, h.upper):
        rgb = arr[..., :3]
        key = (rgb[..., 0].astype(np.int64) << 16) | (rgb[..., 1].astype(np.int64) << 8) | rgb[..., 2]
        for a, b in m.items():
            a = tuple(int(v) for v in a)                          # numpy uint8 would overflow the shifts
            k = (a[0] << 16) | (a[1] << 8) | a[2]
            sel = key == k
            if arr.shape[-1] == 4:
                sel &= arr[..., 3] > 0
            rgb[sel] = b

# --------------------------------------------------------------------------- the plans
# Beds as Gen 3 lays two in one room (Emerald's S.S. Tidal cabins, SSTidalRooms): headboards against the
# north wall, in its corners or side by side. Every house has a kitchen on the north wall over its own tiled
# corner, as HGSS's Violet house has (its stone floor under the sink and fridge).

def kitchen_floor(h, x0, x1, y1):
    for y in range(2, y1 + 1):
        for x in range(x0, x1 + 1):
            h.cell_from(LV, 2, 6 if y > 2 else 6, x, y)
            h.plan[(x, y)] = 'kitchen floor'

def sage():
    """A retired sage's home, nearest the tower: the dojo's wall with its scrolls, a small kitchen on its own
    stone, a tatami room, the Bellsprout statue he kept from the tower, a plant (proposal)."""
    h = House('VioletHouse1', 'dojo')
    for x, sx in enumerate([3, 3, 3, 3, 3, 3, 5, 3, 5, 2, 3]):   # scrolls and a window east of the kitchen
        h.cell_from(DJ, sx, 1, x, 0); h.cell_from(DJ, sx, 2, x, 1)
    kitchen_floor(h, 0, 3, 5)
    h.place('kitchen', 0, 0, whole=False)
    h.tatami(5, 3, 5, 3)
    h.statue(10, 3)
    h.place('plant', 0, 6, whole=False)
    h.place('dj_mat', 3, 8)
    h.notes.append("a retired sage's home: the dojo's wall and tatami, a kitchen on its stone, a Bellsprout statue (proposal)")
    return h.finish()

def boarding_a():
    """Students' boarding house: a bed in each corner of the north wall with the kitchen between them, a
    study table in the middle of the room, a plant (proposal)."""
    h = House('VioletHouse2')
    kitchen_floor(h, 3, 6, 5)
    h.place('kitchen', 3, 0, whole=False)
    h.place('window', 7, 0)
    h.place('bed', 0, 1, whole=False); h.place('bed', 8, 1, whole=False)
    h.place('table4', 4, 6, whole=False)
    h.place('plant', 10, 6)
    h.place('mat', 3, 8)
    h.notes.append("students' boarding house: beds in the north wall's corners, the kitchen between, a study table (proposal)")
    return h.finish()

def boarding_b():
    """A second boarding house: the kitchen and TV at the west of the north wall, two beds side by side at
    its east, the dining table (proposal)."""
    h = House('VioletHouse3')
    kitchen_floor(h, 0, 3, 5)
    h.place('kitchen', 0, 0, whole=False); h.place('tv', 4, 0); h.place('window', 5, 0)
    h.place('bed', 6, 1, whole=False); h.place('bed', 8, 1, whole=False)
    h.place('dining', 1, 4)
    h.place('plant', 10, 6)
    h.place('mat', 3, 8)
    h.notes.append("a second boarding house: kitchen and TV, two beds side by side on the north wall, dining table (proposal)")
    return h.finish()

def professor():
    """A professor's home with a study: the kitchen at the west, two bookshelves, the PC and desk, a reading
    table on its rug (proposal)."""
    h = House('VioletHouse4')
    kitchen_floor(h, 0, 3, 5)
    h.place('kitchen', 0, 0, whole=False)
    h.place('shelf', 4, 0); h.place('shelf', 6, 0)
    h.place('pc', 8, 0); h.place('desk', 9, 1)
    h.place('reading', 4, 4)
    h.place('plant', 10, 6); h.place('plant', 0, 6)
    h.place('mat', 3, 8)
    h.notes.append("a professor's home with a study: kitchen, bookshelves, PC and desk, a reading table (proposal)")
    return h.finish()

def family():
    """The map-card kid's family home, with their gran: kitchen on its stone, TV, the town map on the wall,
    the family's dining table, plants (proposal)."""
    h = House('VioletHouse5')
    kitchen_floor(h, 1, 4, 5)
    h.place('kitchen', 1, 0, whole=False); h.place('tv', 6, 0); h.place('notice', 8, 0); h.place('window', 9, 0)
    h.place('dining', 3, 4)
    h.place('plant', 0, 6); h.place('plant', 10, 6)
    h.place('mat', 3, 8)
    h.notes.append("the map-card kid's family home: kitchen, TV, town map, dining table (proposal)")
    return h.finish()

HOUSES = dict(VioletHouse1=sage, VioletHouse2=boarding_a, VioletHouse3=boarding_b, VioletHouse4=professor, VioletHouse5=family)
