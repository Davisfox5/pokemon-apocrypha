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
        self.behaviors[EXIT] = 'exit'
        self.blocked[EXIT[1], EXIT[0]] = False
        return self

# --------------------------------------------------------------------------- the plans
def sage():
    """A retired sage's home, nearest the tower: the dojo's wall, a tatami room, the Bellsprout statue he
    kept from the tower, a potted plant; nothing else (proposal)."""
    h = House('VioletHouse1', 'dojo')
    h.tatami(3, 3, 5, 3)
    h.statue(9, 3)
    h.place('dj_plant', 1, 1)
    h.place('dj_mat', 3, 8)
    h.notes.append("a retired sage's home: the Fighting Dojo's wall, planks and tatami, a Bellsprout statue (proposal)")
    return h.finish()

def boarding_a():
    """Students' boarding house: two beds, a PC desk and its console, a bookshelf, a window, a table to
    study at, a plant (proposal)."""
    h = House('VioletHouse2')
    h.place('pc', 1, 0); h.place('desk', 2, 0 + 1)
    h.place('window', 4, 0)
    h.place('shelf', 8, 0)
    h.place('bed', 1, 3, whole=False); h.place('bed', 7, 3, whole=False)
    h.place('table4', 4, 6, whole=False)
    h.place('plant', 9, 6)
    h.place('mat', 3, 8)
    h.notes.append("students' boarding house: two beds, a PC desk, a bookshelf, a study table (proposal)")
    return h.finish()

def boarding_b():
    """A second boarding house: a shared kitchen and TV, the dining table, two beds by the east wall (proposal)."""
    h = House('VioletHouse3')
    h.place('kitchen', 1, 0); h.place('tv', 6, 0); h.place('window', 8, 0)
    h.place('dining', 0, 3)
    h.place('bed', 8, 3, whole=False)
    h.place('plant', 9, 7)
    h.place('mat', 3, 8)
    h.notes.append("a second boarding house: shared kitchen and TV, the dining table, beds (proposal)")
    return h.finish()

def professor():
    """A professor's home with a study: a wall of bookshelves, the PC and desk, a reading table on its rug (proposal)."""
    h = House('VioletHouse4')
    h.place('shelf', 1, 0); h.place('shelf', 3, 0); h.place('shelf', 5, 0)
    h.place('pc', 8, 0); h.place('desk', 9, 1)
    h.place('reading', 3, 3)
    h.place('plant', 9, 6)
    h.place('plant', 0, 6)
    h.place('mat', 3, 8)
    h.notes.append("a professor's home with a study: a wall of bookshelves, PC and desk, a reading table (proposal)")
    return h.finish()

def family():
    """The map-card kid's family home, with their gran: kitchen, TV, the town map on the wall, the family's
    dining table, plants (proposal)."""
    h = House('VioletHouse5')
    h.place('kitchen', 1, 0); h.place('tv', 6, 0); h.place('notice', 8, 0); h.place('window', 9, 0)
    h.place('dining', 3, 3)
    h.place('plant', 0, 6); h.place('plant', 10, 6)
    h.place('mat', 3, 8)
    h.notes.append("the map-card kid's family home: kitchen, TV, town map, dining table (proposal)")
    return h.finish()

HOUSES = dict(VioletHouse1=sage, VioletHouse2=boarding_a, VioletHouse3=boarding_b, VioletHouse4=professor, VioletHouse5=family)
