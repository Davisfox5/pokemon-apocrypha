"""Johto's and Sinnoh's Pokemon Centers and Johto's Mart, built from Gen 3's own pieces on the original games'
floor plans (owner, November 8, after rejecting straight DS renders: follow AGENTS.md; compare the original
square by square with native Gen 3 tiles, matching material, structure and traversal).

Every square of the HGSS (or Platinum) room is matched to the native Gen 3 element of the same material and
role, taken whole from Emerald's own rooms with its collision and behaviour (a counter is a counter, a PC a PC,
an escalator an escalator):

    Emerald PokemonCenter_1F  the nurse's counter block (healing machine, nurse's floor, desk, Poke Ball
                              ornaments), the PC, the potted palm, the stools and glass table, the up
                              escalator, the floor's Poke Ball emblem, the exit mat, the side walls
    Emerald PokemonCenter_2F  the plain back wall, its glass doors (as HGSS's windows and shut doors), the
                              attendants' counters (ends, middles, gap blocks), the white pillars, the down
                              escalator, the floor rings, the potted plants
    Emerald Mart              the register counter with its clerk's floor, the glass coolers, the wall shelves
                              of goods, the floor shelves, the clock, the potted plant, the exit mat

Pieces on the room's east side that face west in the original are Emerald's mirrored (Gen 3 metatiles flip).
Colours: each room takes its original's by material (the floor and wall ramps of HGSS's or Platinum's room,
lightest to lightest); furniture keeps Emerald's colours.

Original designs: Game Freak / Nintendo / Creatures (read-only derivation from the games' data).
"""
from __future__ import annotations
import sys
from collections import Counter
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE)]
import native as N                        # noqa: E402

PX = 16
C1, C2, MT = 'PokemonCenter_1F', 'PokemonCenter_2F', 'Mart'

class NRoom:
    """A room of whole native cells: lower and upper layers, collision, native behaviour, a plan label per cell."""
    def __init__(self, name, W, H):
        self.name, self.W, self.H = name, W, H
        self.lower = np.zeros((H * PX, W * PX, 3), np.uint8)
        self.upper = np.zeros((H * PX, W * PX, 4), np.uint8)
        self.blocked = np.ones((H, W), bool)
        self.behaviors, self.notes, self.rect = {}, [], (0, 0, W, H)
        self.beh = {}
        self.plan = {}
        self.deferred = []                # furniture drawn by its own pixels: after the room's colours are set
        self.rugs = []
    def inside(self, x, y):
        return True
    def layers(self):
        return self.lower.copy(), self.upper.copy()
    def image(self):
        out = self.lower.copy(); a = self.upper[..., 3] > 0; out[a] = self.upper[..., :3][a]
        return out
    def sl(self, x, y):
        return np.s_[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX]
    def cell(self, src, sx, sy, x, y, whole=True, flip=False, label=None, block=None, beh='keep', drop=(), tint=None):
        """Native cell (sx, sy) of room src onto (x, y): whole (both layers, collision, behaviour) or, with
        whole=False, only its object pixels over what is there (native.Source.object), less any of the source
        room's own wall or floor colours named in `drop`, its colours changed by `tint`."""
        if not (0 <= x < self.W and 0 <= y < self.H):
            return
        s = N.Source(src); c = s.cell(sx, sy)
        f = (lambda a: a[:, ::-1]) if flip else (lambda a: a)
        if whole:
            self.lower[self.sl(x, y)] = f(c['bot'])
            if c['layer'] == 1:
                top = f(c['top']); a = top[..., 3] > 0
                self.lower[self.sl(x, y)][a] = top[..., :3][a]
                self.upper[self.sl(x, y)] = 0
            else:
                self.upper[self.sl(x, y)] = f(c['top'])
        else:
            m = f(s.object(sx, sy)); fl = f(s.flat(sx, sy)).copy()
            for a, b in (tint or {}).items():
                fl[(fl == a).all(-1)] = b
            for col in drop:
                m = m & ~(fl == col).all(-1)
            self.deferred.append((x, y, m, fl, label))
        self.blocked[y, x] = c['blocked'] if block is None else block
        b = c['behavior'] if beh == 'keep' else beh
        if b:
            self.beh[(x, y)] = b
        else:
            self.beh.pop((x, y), None)
        if label:
            self.plan[(x, y)] = label
    def piece(self, src, sx, sy, w, h, x, y, flip=False, **kw):
        """A w x h block of native cells; flipped, its columns mirrored too."""
        for j in range(h):
            for i in range(w):
                self.cell(src, sx + (w - 1 - i if flip else i), sy + j, x + i, y + j, flip=flip, **kw)
    def black(self, x, y):
        self.lower[self.sl(x, y)] = 0; self.upper[self.sl(x, y)] = 0; self.blocked[y, x] = True
        self.beh.pop((x, y), None)

# --------------------------------------------------------------------------- shells
def center_shell(r, top, bottom):
    """Side walls (Emerald 1F's columns 0 and 13), the plain back wall (2F's), the floor-under-wall row, the
    floor, the bottom corners; rows above `top` and below `bottom` black."""
    W = r.W
    for y in range(r.H):
        for x in range(W):
            r.black(x, y)
    for x in range(1, W - 1):
        r.cell(C2, 1, 0, x, top, label='wall'); r.cell(C2, 1, 1, x, top + 1, label='wall')
        r.cell(C2, 1, 2, x, top + 2, label='floor')
        for y in range(top + 3, bottom + 1):
            r.cell(C1, 2, 4, x, y, label='floor')
    for (x, col) in ((0, 0), (W - 1, 13)):
        r.cell(C1, col, 0, x, top, label='wall'); r.cell(C1, col, 1, x, top + 1, label='wall')
        r.cell(C1, col, 2, x, top + 2, label='wall')
        for y in range(top + 3, bottom):
            r.cell(C1, col, 3 if col == 0 else 4, x, y, label='wall')
        r.cell(C1, col, 8, x, bottom, label='wall')
        for y in range(r.H):                                     # Emerald marks its wall edges walkable: here they block
            r.blocked[y, x] = True

def escalator(r, src, x, y, flip=False, **kw):
    """Emerald's escalator (its x 0-1, rows 5-7) with only its warp square open; its rails and wall block."""
    r.piece(src, 0, 5, 2, 3, x, y, flip=flip, label=kw.pop('label', 'escalator'), **kw)
    for j in range(3):
        for i in range(2):
            if r.beh.get((x + i, y + j)) not in (0x6A, 0x6B):
                r.blocked[y + j, x + i] = True

def counter(r, x0, x1, y, src=C2):
    """An attendants' counter from 2F's pieces: its left end, middles and right end (top row y, its front y + 1)."""
    for x in range(x0, x1 + 1):
        sx = 6 if x == x0 else (7 if x == x1 else 1)
        fx = 6 if x == x0 else (7 if x == x1 else 1)
        r.cell(src, sx, 3, x, y, label='counter'); r.cell(src, fx, 4, x, y + 1, label='counter front')

def plant(r, x, y):
    """2F's potted plant (two squares), on the floor that is there."""
    r.cell(C2, 5, 8, x, y, whole=False, label='plant', block=True); r.cell(C2, 5, 9, x, y + 1, whole=False, label='plant', block=True)

def planter(r, x, y):
    """Lilycove's wooden planter box of shrubs (its x 0-1, rows 4-5), two squares wide."""
    r.piece('LilycoveCity_DepartmentStore_1F', 0, 4, 2, 2, x, y, whole=False, label='planter', block=True)

def bookshelf(r, x, y):
    """FireRed's Center bookshelf of coloured books (its x 2-3, rows 1-2), against the back wall, framed in wood."""
    r.piece('PokemonCenter_1F_FRLG', 2, 1, 2, 2, x, y, whole=False, label='bookshelf', block=True,
            drop=((164, 255, 180), (255, 255, 255), (180, 180, 164), (230, 222, 156), (213, 205, 156), (197, 180, 139)),
            tint={(106, 197, 106): (172, 115, 65)})    # less FireRed's green wall and floor; its green frame in wood
    for i in range(2):
        r.beh[(x + i, y)] = 0xE1

def picture(r, x, y):
    """Emerald's framed map of the region (its x 11-12, rows 0-1)."""
    r.piece(C1, 11, 0, 2, 2, x, y, whole=False, label='picture', block=True,
            drop=((246, 180, 115), (222, 123, 49), (148, 148, 148)))                     # Emerald's orange wall below it

def rug(r, x, y, w, h, kind='lounge'):
    """A rug, drawn under the furniture in Gen 3's manner (outline, border, a field with a small repeat)."""
    r.rugs.append((x, y, w, h, kind))
    for j in range(h):
        for i in range(w):
            r.plan.setdefault((x + i, y + j), 'rug')

def stool(r, x, y, red=False):
    r.cell(C2, 8 if red else 3, 9, x, y, whole=False, label='stool', block=False)

def table(r, x, y):
    """1F's glass table (2 x 2)."""
    r.piece(C1, 11, 6, 2, 2, x, y, whole=False, label='table')
    for j in range(2):
        for i in range(2):
            r.blocked[y + j, x + i] = True

# --------------------------------------------------------------------------- Johto (HGSS T21PC0101, T27PC0105)
def johto_center_1f():
    """HGSS's 1F, 17 x 20, square by square (map coordinates are HGSS's)."""
    r = NRoom('JohtoPokemonCenter1F', 17, 21)
    center_shell(r, 0, 19)
    for x in (7, 12):                                            # HGSS's two windows (the styling's wall displays)
        r.piece(C2, 5, 0, 1, 2, x, 0, label='window', beh=0, block=True)
    # the staff side of the back counters: a bookshelf and the region's map on the back wall, a plant in its corner
    bookshelf(r, 2, 1); picture(r, 9, 0); plant(r, 15, 3)
    # the raised back with its three counters (HGSS row 5; attendants at (2, 4), (6, 4), (11, 4)); the third
    # runs to the east wall so the staff side is closed (HGSS's raised back is the attendants' side)
    counter(r, 1, 6, 5); counter(r, 8, 11, 5); counter(r, 13, 15, 5)
    for x in (7, 12):                                            # HGSS's openings between the counters: 2F's gap blocks
        r.cell(C2, 5, 3, x, 5, label='counter gap'); r.cell(C2, 5, 4, x, 6, label='counter gap')
    # the nurse's station: Emerald 1F's counter block with its healing machine and desk (its x 4-9, rows 0-3) in a
    # partition (HGSS's, rows 9-10), the PC at its west end (1F x 10, rows 0-2), finished posts at both ends
    # (the styling draws them), the notice board east of the TV
    r.piece(C1, 4, 0, 6, 4, 5, 9, label='nurse counter')
    r.piece(C1, 10, 0, 1, 3, 4, 9, label='PC')
    r.cell(C1, 2, 4, 4, 12, label='floor')
    r.piece(C2, 1, 0, 1, 2, 11, 9, label='notice board')
    r.cell(C1, 11, 2, 11, 11, label='floor'); r.cell(C1, 2, 4, 11, 12, label='floor')
    for x in (3, 12):
        r.piece(C2, 1, 0, 1, 2, x, 9, label='post')
        r.cell(C1, 2, 4, x, 11, label='floor')
    # HGSS's glass divider west of the lobby (x 3, rows 11-14): potted plants, a barrier as HGSS's is
    plant(r, 3, 11); plant(r, 3, 13)
    # the lounges (HGSS's benches): glass tables and stools on rugs
    rug(r, 1, 12, 2, 4); table(r, 1, 12); stool(r, 1, 14, red=True); stool(r, 2, 14)
    rug(r, 13, 8, 3, 3); table(r, 13, 8); stool(r, 15, 8); stool(r, 15, 9, red=True)
    plant(r, 14, 13); plant(r, 15, 13)
    # the Poke Ball on the floor (Emerald 1F's, x 5-8, rows 4-7), a runner from the door up to it
    r.piece(C1, 5, 4, 4, 4, 7, 13, label='emblem')
    rug(r, 8, 17, 2, 2, kind='runner')
    # planters either side of the door
    planter(r, 4, 17); planter(r, 12, 17)
    # the escalator down (HGSS x 14-15, rows 16-19, its warp (14, 17)): 2F's down escalator, mirrored onto the
    # east wall; its warp square (15, 17)
    escalator(r, C2, 15, 16, flip=True)
    r.piece(C1, 6, 8, 2, 1, 8, 19, label='exit mat')
    r.rect = (0, 0, 17, 20)
    r.behaviors[(8, 19)] = 'exit'; r.behaviors[(9, 19)] = 'exit'
    r.notes.append("HGSS's Pokemon Center 1F square by square in Emerald's own Center pieces, styled a decade on")
    return r

def johto_center_b1():
    """HGSS's B1F, 17 x 13."""
    r = NRoom('JohtoPokemonCenterB1F', 17, 14)
    center_shell(r, 0, 12)
    for x in (5, 9):                                             # HGSS's two doors at the back (the styling's displays)
        r.piece(C2, 5, 0, 1, 2, x, 0, label='door (shut)', beh=0, block=True)
    bookshelf(r, 1, 1); picture(r, 11, 0); bookshelf(r, 14, 1)
    # three counters (HGSS row 5; attendants (4, 4), (8, 4), (12, 4)), the terminal at the west end
    counter(r, 2, 4, 5); counter(r, 6, 8, 5); counter(r, 10, 15, 5)
    for x in (5, 9):
        r.cell(C2, 5, 3, x, 5, label='counter gap'); r.cell(C2, 5, 4, x, 6, label='counter gap')
    r.piece(C2, 3, 3, 1, 2, 1, 5, label='terminal')
    # the lounge: the glass table and stools on a rug (HGSS x 2-4, rows 7-9), the floor rings (HGSS's emblem x 7-10)
    rug(r, 1, 8, 4, 3); table(r, 2, 8); stool(r, 4, 8, red=True); stool(r, 4, 9); stool(r, 1, 9)
    r.piece(C2, 4, 5, 4, 2, 7, 8, label='emblem')
    planter(r, 1, 11); plant(r, 3, 11); planter(r, 11, 11)       # the floor before the escalator stays open
    for x, red in ((5, False), (6, True), (7, False), (9, True), (10, False)):
        stool(r, x, 12, red)
    # the escalator up (HGSS x 14-15, rows 7-11, warp (14, 10)): Emerald 1F's, mirrored onto the east wall, its
    # foot on the bottom row (no square left behind it); its warp square (15, 11)
    escalator(r, C1, 15, 10, flip=True)
    r.rect = (0, 0, 17, 13)
    r.notes.append("HGSS's Pokemon Center B1F square by square in Emerald's own Center pieces, styled a decade on")
    return r

# --------------------------------------------------------------------------- the Mart (HGSS T21FS0101, 18 wide)
def mart_shell(r):
    W = r.W
    for y in range(r.H):
        for x in range(W):
            r.black(x, y)
    for x in range(W):
        sx = 0 if x == 0 else (10 if x == W - 1 else 2)
        r.cell(MT, sx, 0, x, 1, label='wall'); r.cell(MT, sx, 1, x, 2, label='wall')
        for y in range(3, 11):
            r.cell(MT, 4, 3, x, y, label='floor')
        r.cell(MT, 0 if x == 0 else (10 if x == W - 1 else 5), 7, x, 11, label='floor')

def johto_mart():
    """HGSS's Mart, 18 x 11 squares for M01's 7-square front: the standard counter on the west wall (Emerald's,
    its clerk at (1, 4)), a second counter mirrored on the east wall (clerk (16, 4)); HGSS's coolers, wall
    shelves, floor shelves, cafe table and plants between; the exit mat at (4, 11)."""
    r = NRoom('JohtoMart', 18, 13)
    mart_shell(r)
    W = r.W
    r.piece(MT, 0, 2, 3, 3, 0, 3, label='counter')               # the standard counter and its clerk's floor
    r.piece(MT, 0, 2, 3, 3, W - 3, 3, flip=True, label='second counter')
    r.piece(MT, 1, 0, 1, 2, 1, 1, label='clock')
    r.piece(MT, 1, 0, 1, 2, W - 2, 1, flip=True, label='clock')
    r.piece(MT, 6, 0, 4, 2, 4, 1, label='wall shelves')          # HGSS's shelves on the wall (x 4-7)
    r.piece(MT, 3, 0, 3, 2, 8, 1, label='coolers')               # HGSS's drinks coolers (x 8-11), and four more
    r.piece(MT, 3, 0, 3, 2, 11, 1, label='coolers')
    for x in (6, 9, 12):                                         # HGSS's floor shelves (x 6-7, 9-10), one more
        r.piece(MT, 6, 4, 2, 3, x, 5, label='floor shelves')
    table(r, 9, 9)
    r.cell(C1, 1, 3, 8, 9, whole=False, label='stool', block=False)
    r.cell(C1, 2, 3, 11, 10, whole=False, label='stool', block=False)
    r.piece(MT, 10, 2, 1, 2, 1, 9, whole=False, label='plant')
    r.piece(MT, 10, 2, 1, 2, W - 2, 9, whole=False, flip=True, label='plant')
    for x in (1, W - 2):
        r.blocked[10, x] = True
    r.piece(MT, 3, 7, 2, 1, 4, 11, label='exit mat')
    r.rect = (0, 0, W, 12)
    r.behaviors[(4, 11)] = 'exit'; r.behaviors[(5, 11)] = 'exit'
    r.notes.append("HGSS's Mart square by square in Emerald's own Mart pieces, four columns wider, a second counter (proposal)")
    return r

# --------------------------------------------------------------------------- Sinnoh (Platinum PokemonCenter_1F/2F)
# Platinum's wall is three rows and its nurse's alcove two; Gen 3's are two and one (Emerald's 1F, Platinum's
# predecessor square for square). Platinum's rows from the nurse down stand two rows higher here (its row r is
# row r - 2); its columns are its own (Emerald's x + 1).
def sinnoh_center_1f():
    """Platinum's 1F, 17 x 11."""
    r = NRoom('SinnohPokemonCenter1F', 17, 12)
    center_shell(r, 0, 10)
    r.piece(C1, 1, 0, 3, 3, 2, 0, label='plant, bookshelf')       # Platinum's plant (2, 1), bookshelf (3-4, 1-2)
    r.piece(C1, 4, 0, 6, 4, 5, 0, label='nurse counter')         # nurse (8, 2), counter row 3 (Platinum (8, 4), row 5)
    r.piece(C1, 10, 0, 3, 3, 12, 0, label='PC, picture')         # Platinum's PC (12, 2-3), picture (13-14, 1)
    r.cell(C1, 1, 3, 1, 3, whole=False, label='stool', block=False)
    r.cell(C1, 2, 3, 1, 4, whole=False, label='stool', block=False)
    r.piece(C1, 5, 4, 4, 4, 7, 6, label='emblem')                # Platinum's emblem (7-10, 8-11)
    unshadow(r, 7, 10, 6)
    escalator(r, C1, 0, 7)                                       # up; Platinum's warp (2, 10): here (1, 8)
    r.piece(C2, 0, 5, 2, 3, 15, 7, flip=True, label='escalator (shut)', beh=0, block=True)
    for x, red in ((3, False), (4, True), (12, True), (13, False)):
        stool(r, x, 10, red)
    r.piece(C1, 6, 8, 2, 1, 8, 10, label='exit mat')             # Platinum's exit (8, 12)
    r.rect = (0, 0, 17, 11)
    r.behaviors[(8, 10)] = 'exit'; r.behaviors[(9, 10)] = 'exit'
    r.notes.append("Platinum's Pokemon Center 1F square by square in Emerald's own Center pieces")
    return r

def sinnoh_center_2f():
    """Platinum's 2F, 17 x 11: counters row 3 (Platinum's row 5), the escalator down (1, 8)."""
    r = NRoom('SinnohPokemonCenter2F', 17, 12)
    center_shell(r, 0, 10)
    r.piece(C2, 5, 0, 1, 2, 8, 0, label='Union Room door (shut)', beh=0, block=True)
    for x in (4, 13):
        r.piece(C2, 3, 1, 1, 2, x, 1, label='pillar')
    counter(r, 1, 7, 3); counter(r, 9, 12, 3); counter(r, 14, 15, 3)
    for x in (8, 13):
        r.cell(C2, 5, 3, x, 3, label='counter gap'); r.cell(C2, 5, 4, x, 4, label='counter gap')
    r.piece(C2, 8, 3, 1, 2, 5, 3, label='card machine'); r.piece(C2, 12, 3, 1, 2, 11, 3, label='card machine')
    r.piece(C2, 4, 5, 4, 2, 6, 6, label='emblem')
    plant(r, 5, 9); plant(r, 13, 9)
    for x, red in ((7, False), (8, True), (10, False), (11, True)):
        stool(r, x, 10, red)
    escalator(r, C2, 0, 7)                                       # down; Platinum's warp (2, 10): here (1, 8)
    r.rect = (0, 0, 17, 11)
    r.notes.append("Platinum's Pokemon Center 2F square by square in Emerald's own Center pieces")
    return r

# --------------------------------------------------------------------------- the originals' colours
# Each room's floor and wall ramps, lightest to lightest, sampled from the original room's own floor and wall
# (HGSS's T21PC0101, T27PC0105, T21FS0101; Platinum's PokemonCenter_1F/2F): Emerald's cream floor and orange
# wall become HGSS's warmer floor and orange, its blue basement, its teal-tiled Mart, Platinum's red-orange.
TONES = {
    'JohtoPokemonCenter1F': ([(222, 181, 115), (255, 214, 140), (255, 222, 148), (255, 231, 156), (255, 239, 181)],
                             [(181, 74, 49), (198, 90, 66), (222, 123, 33), (255, 156, 66), (255, 206, 107)]),
    'JohtoPokemonCenterB1F': ([(115, 181, 214), (156, 214, 239), (170, 224, 250), (181, 231, 255), (206, 239, 255)],
                              [(24, 132, 148), (33, 140, 156), (57, 165, 181), (74, 181, 198), (132, 222, 247)]),
    'JohtoMart': ([(66, 148, 181), (90, 173, 198), (107, 189, 214), (132, 206, 222), (156, 214, 231)],
                  [(66, 123, 198), (82, 156, 231), (255, 222, 140), (255, 239, 181)]),
    'SinnohPokemonCenter1F': ([(222, 189, 115), (247, 214, 132), (255, 222, 140), (255, 231, 156), (255, 239, 181)],
                              [(165, 49, 57), (198, 82, 57), (239, 99, 57), (255, 156, 66), (255, 189, 90)]),
}
TONES['SinnohPokemonCenter2F'] = TONES['SinnohPokemonCenter1F']
TONES['JohtoPokemonCenterB1F'] = TONES['JohtoPokemonCenter1F']       # the styling (below) runs through both floors
KEEP = {(255, 255, 255), (82, 82, 106), (148, 148, 148), (0, 0, 0)}     # white, outline, grey: Gen 3's own

def _cols(src, cells):
    s = N.Source(src)
    out = set()
    for x, y in cells:
        out |= {tuple(int(v) for v in c) for c in s.flat(x, y).reshape(-1, 3)}
    return out

def _light(c):
    return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]

def _ramp(cols, target):
    cols = sorted(cols, key=_light)
    n, m = len(cols), len(target)
    return {c: target[min(m - 1, round(i * (m - 1) / max(1, n - 1)))] for i, c in enumerate(cols)}

def retone(r):
    """Emerald's floor and wall colours onto the original room's ramps; furniture's own colours stay."""
    floor_t, wall_t = TONES[r.name]
    if r.name == 'JohtoMart':
        floor = _cols(MT, [(4, 3), (5, 5), (3, 2), (4, 2), (5, 7)]) - KEEP
        wall = _cols(MT, [(2, 0), (2, 1)]) - KEEP - floor
    else:
        floor = _cols(C1, [(2, 4), (3, 5), (4, 4), (11, 2)]) | _cols(C2, [(1, 2), (1, 7), (2, 8)])
        floor -= KEEP
        wall = (_cols(C2, [(1, 0), (1, 1)]) | _cols(C1, [(0, 3), (0, 1), (13, 4), (13, 1)])) - KEEP - floor
    m = {**_ramp(floor, floor_t), **_ramp(wall, wall_t)}
    for arr in (r.lower, r.upper):
        rgb = arr[..., :3]
        key = (rgb[..., 0].astype(np.int64) << 16) | (rgb[..., 1].astype(np.int64) << 8) | rgb[..., 2]
        sel_all = arr[..., 3] > 0 if arr.shape[-1] == 4 else np.ones(key.shape, bool)
        for a, b in m.items():
            sel = (key == ((a[0] << 16) | (a[1] << 8) | a[2])) & sel_all
            rgb[sel] = b
    return r

def unshadow(r, x0, x1, y):
    """Emerald's emblem lies under its counter; its top row carries the counter's shadow. Away from a counter
    those shaded floor pixels take the plain floor's (the floor's pattern is the same in every square)."""
    s = N.Source(C1)
    plain = s.flat(2, 4)
    pc = {tuple(int(v) for v in c) for c in plain.reshape(-1, 3)}
    shade = {tuple(int(v) for v in c) for c in s.flat(4, 4).reshape(-1, 3)} - pc
    for x in range(x0, x1 + 1):
        c = r.lower[r.sl(x, y)]
        m = np.array([[tuple(int(v) for v in px) in shade for px in row] for row in c])
        c[m] = plain[m]

# --------------------------------------------------------------------------- rugs
def q(c):
    """A colour on the GBA's 5-bit grid."""
    return tuple(((v * 31 + 127) // 255) * 255 // 31 for v in c)

RUG = dict(lounge=[q(c) for c in ((98, 49, 41), (164, 65, 57), (213, 123, 90), (238, 189, 139))],
           runner=[q(c) for c in ((98, 49, 41), (164, 49, 57), (197, 74, 65), (238, 189, 139))])

def draw_rug(r, x, y, w, h, kind):
    """Gen 3's rug: a dark outline, a two-pixel border, a field with a small diamond repeat (a runner: a stripe
    down each side), inset two pixels from the squares' edges so the floor shows round it."""
    o, b, f, p = RUG[kind]
    H, W = h * PX - 4, w * PX - 4
    a = np.empty((H, W, 3), np.uint8)
    a[:] = o; a[1:-1, 1:-1] = b; a[3:-3, 3:-3] = f
    yy, xx = np.mgrid[:H, :W]
    if kind == 'runner':
        a[3:-3, 5:7] = p; a[3:-3, W - 7:W - 5] = p
    else:
        d = (abs(((yy - 4) % 8) - 4) + abs(((xx - 4) % 8) - 4)) == 1
        inner = (yy >= 5) & (yy < H - 5) & (xx >= 5) & (xx < W - 5)
        a[d & inner] = p
    r.lower[y * PX + 2:y * PX + 2 + H, x * PX + 2:x * PX + 2 + W] = a
    r.upper[y * PX + 2:y * PX + 2 + H, x * PX + 2:x * PX + 2 + W] = 0

# --------------------------------------------------------------------------- the Johto Center, a decade on
# Owner, November 10, approving the mockup: "the updated color palette is solid ... run with the styling". The
# same native pieces in new materials, by colour (a cool polished floor, white panels with the Center's red band,
# slate counters with cyan light strips), and Gen 3-drawn details (wall displays, a welcome display in the old TV's
# place, self-service terminals on the back counters, finished posts at the station's ends, a notice board).
FLOOR = {(255, 239, 181): (239, 243, 247), (255, 231, 156): (222, 230, 239), (255, 222, 148): (197, 206, 222),
         (255, 214, 140): (189, 197, 214), (222, 181, 115): (156, 165, 189), (238, 222, 164): (222, 230, 239),
         (205, 197, 139): (180, 189, 205), (230, 230, 180): (214, 222, 230)}
WALL = {(255, 156, 66): (230, 235, 243), (198, 90, 66): (206, 49, 66), (181, 74, 49): (156, 33, 57),
        (255, 206, 107): (255, 255, 255)}
SLATE = {(180, 172, 222): (74, 82, 106), (148, 131, 164): (49, 57, 82), (222, 156, 98): (115, 123, 148)}
SEAT = {(255, 172, 123): (90, 206, 214), (213, 115, 98): (49, 156, 173), (255, 222, 65): (238, 242, 246),
        (197, 164, 24): (165, 174, 189), (255, 213, 172): (148, 230, 238), (255, 238, 156): (255, 255, 255)}
PLANTER = {(238, 222, 164): (247, 247, 247), (205, 197, 139): (189, 197, 214), (156, 115, 90): (115, 123, 148),
           (189, 148, 49): (148, 156, 173)}
CYAN, CYAN_D, NAVY, NAVY_L, RED, RED_D = (74, 222, 247), (41, 156, 198), (24, 33, 57), (41, 57, 99), (206, 49, 66), (156, 33, 57)
O, SL, SL_M, SL_L, PALE = (49, 57, 82), (74, 82, 106), (115, 123, 148), (148, 156, 173), (238, 242, 246)
MODERN = {'JohtoPokemonCenter1F': dict(kiosks=(3, 10, 14), tv=(152, 168, 129, 152), nurse_row=(12, 5, 10), posts=(3, 12), board=11),
          'JohtoPokemonCenterB1F': dict(kiosks=(3, 7, 12))}

def modern(r, protect):
    cfg = MODERN[r.name]
    def remap(region, table, guard=True):
        for arr in (r.lower, r.upper):
            sub = arr[region]; rgb = sub[..., :3]
            ok = sub[..., 3] > 0 if arr.shape[-1] == 4 else np.ones(rgb.shape[:2], bool)
            if guard:
                ok = ok & ~protect[region]
            for a, b in table.items():
                m = (rgb == a).all(-1) & ok
                rgb[m] = q(b)
    def cells(*labels):
        return [(x, y) for (x, y), l in r.plan.items() if l in labels]
    def put(y0, y1, x0, x1, c):                    # Gen 3-drawn pixels: on the lower layer, nothing over them
        r.lower[y0:y1, x0:x1] = q(c); r.upper[y0:y1, x0:x1] = 0
    for x, y in cells('emblem'):
        remap(r.sl(x, y), {(255, 156, 66): RED, (255, 206, 107): RED})
    for x, y in cells('exit mat'):
        remap(r.sl(x, y), {(198, 90, 66): (115, 123, 148), (255, 156, 66): (148, 156, 173), (148, 148, 148): (82, 90, 115)})
    for x, y in cells('counter', 'nurse counter', 'terminal'):
        remap(r.sl(x, y), SLATE)
    for x, y in cells('stool'):
        remap(r.sl(x, y), SEAT)
    for x, y in cells('plant'):
        remap(r.sl(x, y), PLANTER)
    for x, y in cells('PC'):
        remap(r.sl(x, y), {(139, 148, 82): CYAN_D, (98, 98, 123): NAVY_L})
    remap(np.s_[:, :], {**WALL, **FLOOR})

    def screen(x0, y0, w, h):
        """A wall display: slate bezel, navy glass, a cyan glow line, the Poke Ball in cyan, red and white."""
        put(y0, y0 + h, x0, x0 + w, O); put(y0 + 1, y0 + h - 1, x0 + 1, x0 + w - 1, NAVY)
        put(y0 + 1, y0 + 2, x0 + 1, x0 + w - 1, CYAN_D); put(y0 + h - 2, y0 + h - 1, x0 + 1, x0 + w - 1, NAVY_L)
        a = r.lower[y0:y0 + h, x0:x0 + w]
        cy, cx, R = h // 2, w // 2, min(w, h) // 2 - 4
        yy, xx = np.mgrid[:h, :w]
        d = (yy - cy) ** 2 + (xx - cx) ** 2
        a[(d <= R * R) & (d >= (R - 1) ** 2)] = q(CYAN)
        a[(d < (R - 1) ** 2) & (yy < cy)] = q(RED)
        a[(d < (R - 1) ** 2) & (yy > cy)] = q(PALE)
        a[(yy == cy) & (d < R * R)] = q(O)
        a[d <= 4] = q(PALE); a[(d <= 4) & (d >= 2)] = q(O)
    for x in sorted({x for x, y in cells('window', 'door (shut)') if y == 0}):
        screen(x * PX - 4, 2, 24, 26)

    if 'tv' in cfg:                                # the old TV becomes a wider welcome display
        y0, y1, x0, x1 = cfg['tv']
        r.lower[y0:y1, x0:x1] = r.lower[9 * PX + 12, 8 * PX + 1]; r.upper[y0:y1, x0 - 2:x1 + 2] = 0
        put(y0 + 1, y1, x0 - 2, x1 + 2, O); put(y0 + 2, y1 - 1, x0 - 1, x1 + 1, NAVY)
        put(y0 + 2, y0 + 3, x0 - 1, x1 + 1, CYAN_D)
        put(y0 + 5, y0 + 6, x0 + 2, x1 - 2, CYAN); put(y0 + 8, y0 + 9, x0 + 2, x0 + 14, CYAN_D); put(y0 + 8, y0 + 9, x0 + 17, x1 - 2, RED)

    # cyan light strips: the foot of the back wall (not across the furniture), the counters' fronts
    row = ~protect[31, PX:(r.W - 1) * PX]
    r.lower[31, PX:(r.W - 1) * PX][row] = q(CYAN); r.upper[31, PX:(r.W - 1) * PX][row] = 0
    strip = cells('counter')
    if 'nurse_row' in cfg:
        y, a, b = cfg['nurse_row']; strip += [(x, y) for x in range(a, b + 1)]
    for x, y in strip:
        col = r.lower[y * PX:(y + 1) * PX, x * PX + 8]
        dark = [i for i in range(PX) if tuple(col[i]) == q(SLATE[(180, 172, 222)])]
        if dark:
            put(y * PX + max(dark), y * PX + max(dark) + 1, x * PX, (x + 1) * PX, CYAN)

    def kiosk(x, y):                               # a self-service terminal standing on the counter top
        y0, x0 = y * PX - 22, x * PX
        put(y0 + 6, y0 + 28, x0 + 4, x0 + 12, O); put(y0 + 7, y0 + 16, x0 + 5, x0 + 11, NAVY)
        put(y0 + 8, y0 + 10, x0 + 6, x0 + 10, CYAN); put(y0 + 11, y0 + 12, x0 + 6, x0 + 9, CYAN_D)
        put(y0 + 13, y0 + 14, x0 + 6, x0 + 10, CYAN_D); put(y0 + 16, y0 + 27, x0 + 6, x0 + 10, SL_M)
        put(y0 + 26, y0 + 28, x0 + 3, x0 + 13, O)
    for x in cfg['kiosks']:
        kiosk(x, 5)

    for x in cfg.get('posts', ()):                 # the station's ends: slate posts, capped, banded, on a plinth
        y0, x0 = 9 * PX, x * PX
        put(y0, y0 + 32, x0, x0 + 16, O)
        put(y0 + 1, y0 + 3, x0 + 1, x0 + 15, SL_L)            # the cap
        put(y0 + 3, y0 + 4, x0 + 1, x0 + 15, SL)
        put(y0 + 4, y0 + 27, x0 + 2, x0 + 14, SL_M)            # the shaft: lit on the left, shaded on the right
        put(y0 + 4, y0 + 27, x0 + 2, x0 + 4, SL_L); put(y0 + 4, y0 + 27, x0 + 11, x0 + 14, SL)
        put(y0 + 4, y0 + 27, x0 + 1, x0 + 2, O); put(y0 + 4, y0 + 27, x0 + 14, x0 + 15, O)
        put(y0 + 13, y0 + 16, x0 + 2, x0 + 14, RED); put(y0 + 16, y0 + 17, x0 + 2, x0 + 14, RED_D)   # the Center's band
        put(y0 + 8, y0 + 10, x0 + 7, x0 + 9, CYAN)                                                # a status light
        put(y0 + 27, y0 + 28, x0, x0 + 16, O)                    # the plinth
        put(y0 + 28, y0 + 31, x0 + 1, x0 + 15, SL); put(y0 + 28, y0 + 29, x0 + 1, x0 + 15, SL_M)
        below = r.plan.get((x, 11))
        if below == 'floor':                                     # its shadow on the floor
            put(11 * PX, 11 * PX + 2, x0 + 1, x0 + 15, (180, 189, 205))

    if 'board' in cfg:                             # a cork notice board on the station's partition, pinned notices
        x0, y0 = cfg['board'] * PX, 9 * PX
        put(y0 + 3, y0 + 22, x0 + 1, x0 + 15, (90, 57, 41)); put(y0 + 4, y0 + 21, x0 + 2, x0 + 14, (164, 106, 65))
        put(y0 + 5, y0 + 20, x0 + 3, x0 + 13, (213, 164, 106))
        put(y0 + 6, y0 + 12, x0 + 4, x0 + 8, (255, 255, 255)); put(y0 + 7, y0 + 8, x0 + 5, x0 + 7, (148, 156, 173))
        put(y0 + 9, y0 + 10, x0 + 5, x0 + 7, (148, 156, 173))
        put(y0 + 8, y0 + 13, x0 + 9, x0 + 12, (255, 238, 156)); put(y0 + 10, y0 + 11, x0 + 9, x0 + 11, (197, 164, 24))
        put(y0 + 14, y0 + 19, x0 + 5, x0 + 11, (148, 230, 238)); put(y0 + 16, y0 + 17, x0 + 6, x0 + 10, (49, 156, 173))
        for px_, py_ in ((x0 + 6, y0 + 6), (x0 + 10, y0 + 8), (x0 + 8, y0 + 14)):
            put(py_, py_ + 1, px_, px_ + 1, RED)

DECOR = {'bookshelf', 'picture', 'planter'}        # drawn decor keeps its own colours through the styling

def finished(make):
    def run():
        r = retone(make())
        for x, y, w, h, kind in r.rugs:
            draw_rug(r, x, y, w, h, kind)
        protect = np.zeros(r.lower.shape[:2], bool)
        for x, y, m, fl, label in r.deferred:                   # furniture keeps Emerald's own colours
            r.lower[r.sl(x, y)][m] = fl[m]
            if label in DECOR:
                protect[r.sl(x, y)] |= m
        if r.name in MODERN:
            modern(r, protect)
        return r
    run.__name__ = make.__name__
    return run

ROOMS = {'JohtoPokemonCenter1F': johto_center_1f, 'JohtoPokemonCenterB1F': johto_center_b1, 'JohtoMart': johto_mart,
         'SinnohPokemonCenter1F': sinnoh_center_1f, 'SinnohPokemonCenter2F': sinnoh_center_2f}
ROOMS = {n: finished(f) for n, f in ROOMS.items()}
