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
    def inside(self, x, y):
        return True
    def layers(self):
        return self.lower.copy(), self.upper.copy()
    def image(self):
        out = self.lower.copy(); a = self.upper[..., 3] > 0; out[a] = self.upper[..., :3][a]
        return out
    def sl(self, x, y):
        return np.s_[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX]
    def cell(self, src, sx, sy, x, y, whole=True, flip=False, label=None, block=None, beh='keep'):
        """Native cell (sx, sy) of room src onto (x, y): whole (both layers, collision, behaviour) or, with
        whole=False, only its object pixels over what is there (native.Source.object)."""
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
            m = f(s.object(sx, sy)); fl = f(s.flat(sx, sy))
            self.deferred.append((x, y, m, fl))
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

def counter(r, x0, x1, y, src=C2):
    """An attendants' counter from 2F's pieces: its left end, middles and right end (top row y, its front y + 1)."""
    for x in range(x0, x1 + 1):
        sx = 6 if x == x0 else (7 if x == x1 else 1)
        fx = 6 if x == x0 else (7 if x == x1 else 1)
        r.cell(src, sx, 3, x, y, label='counter'); r.cell(src, fx, 4, x, y + 1, label='counter front')

def plant(r, x, y):
    """2F's potted plant (two squares), on the floor that is there."""
    r.cell(C2, 5, 8, x, y, whole=False, label='plant'); r.cell(C2, 5, 9, x, y + 1, whole=False, label='plant', block=True)

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
    for x in (7, 12):                                            # HGSS's two windows: 2F's glass doors, shut
        r.piece(C2, 5, 0, 1, 2, x, 0, label='window', beh=0, block=True)
    plant(r, 15, 3)
    # the raised back with its three counters (HGSS row 5; attendants at (2, 4), (6, 4), (11, 4))
    counter(r, 1, 6, 5); counter(r, 8, 11, 5); counter(r, 13, 14, 5)
    for x in (7, 12):                                            # HGSS's openings between the counters: 2F's gap blocks
        r.cell(C2, 5, 3, x, 5, label='counter gap'); r.cell(C2, 5, 4, x, 6, label='counter gap')
    # the nurse's partition (HGSS rows 7-8, its posts) and counter (nurse (8, 11), counter row 12): Emerald 1F's
    # counter block with its healing machine and desk (its x 4-9, rows 0-3), the PC west of it (1F x 10, rows
    # 0-2), 2F's white pillars as the partition's ends; the machine stands in the partition as Emerald has it
    r.piece(C1, 4, 0, 6, 4, 5, 9, label='nurse counter')
    r.piece(C1, 10, 0, 1, 3, 4, 9, label='PC')
    r.cell(C1, 2, 4, 4, 12, label='floor')
    r.piece(C2, 1, 0, 1, 2, 11, 9, label='partition')
    r.cell(C1, 11, 2, 11, 11, label='floor'); r.cell(C1, 2, 4, 11, 12, label='floor')
    for x in (3, 12):
        r.piece(C2, 3, 1, 1, 2, x, 9, label='post')
        r.cell(C1, 2, 4, x, 11, label='floor')
    # HGSS's glass divider west of the lobby (x 3, rows 11-14): potted plants
    plant(r, 3, 11); plant(r, 3, 13)
    # HGSS's benches: the glass table with stools
    table(r, 1, 12); stool(r, 1, 14, red=True); stool(r, 2, 14)
    table(r, 13, 8); stool(r, 15, 8); stool(r, 15, 9, red=True)
    plant(r, 14, 13); plant(r, 15, 13)
    # the Poke Ball on the floor (Emerald 1F's, x 5-8, rows 4-7)
    r.piece(C1, 5, 4, 4, 4, 7, 13, label='emblem')
    # the escalator down (HGSS x 14-15, rows 16-19, its warp (14, 17)): 2F's down escalator, mirrored onto
    # the east wall; its warp square (15, 17)
    r.piece(C2, 0, 5, 2, 3, 15, 16, flip=True, label='escalator')
    # the exit (HGSS (8, 19)): Emerald's mat
    r.piece(C1, 6, 8, 2, 1, 8, 19, label='exit mat')
    r.rect = (0, 0, 17, 20)
    r.behaviors[(8, 19)] = 'exit'; r.behaviors[(9, 19)] = 'exit'
    r.notes.append("HGSS's Pokemon Center 1F square by square in Emerald's own Center pieces")
    return r

def johto_center_b1():
    """HGSS's B1F, 17 x 13."""
    r = NRoom('JohtoPokemonCenterB1F', 17, 14)
    center_shell(r, 0, 12)
    for x in (5, 9):                                             # HGSS's two doors at the back: 2F's glass doors, shut
        r.piece(C2, 5, 0, 1, 2, x, 0, label='door (shut)', beh=0, block=True)
    for x in (3, 13):
        r.piece(C2, 3, 1, 1, 2, x, 1, label='pillar')
    # three counters (HGSS row 5; attendants (4, 4), (8, 4), (12, 4)), 2F's card machines beside them
    counter(r, 2, 4, 5); counter(r, 6, 8, 5); counter(r, 10, 15, 5)
    for x in (5, 9):
        r.cell(C2, 5, 3, x, 5, label='counter gap'); r.cell(C2, 5, 4, x, 6, label='counter gap')
    r.piece(C2, 3, 3, 1, 2, 1, 5, label='terminal')
    # the lounge: the glass table and stools (HGSS x 2-4, rows 7-9), the floor rings (HGSS's emblem x 7-10)
    table(r, 2, 8); stool(r, 4, 8, red=True); stool(r, 4, 9)
    r.piece(C2, 4, 5, 4, 2, 7, 8, label='emblem')
    plant(r, 4, 11); plant(r, 12, 11)
    for x, red in ((5, False), (6, True), (7, False), (9, True), (10, False), (11, True)):
        stool(r, x, 12, red)
    # the escalator up (HGSS x 14-15, rows 7-11, warp (14, 10)): Emerald 1F's, mirrored onto the east wall
    r.piece(C1, 0, 5, 2, 3, 15, 9, flip=True, label='escalator')
    r.rect = (0, 0, 17, 13)
    r.notes.append("HGSS's Pokemon Center B1F square by square in Emerald's own Center pieces")
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
    r.piece(C1, 0, 5, 2, 3, 0, 7, label='escalator')             # up; Platinum's warp (2, 10): here (1, 8)
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
    r.piece(C2, 0, 5, 2, 3, 0, 7, label='escalator')             # down; Platinum's warp (2, 10): here (1, 8)
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

def finished(make):
    def run():
        r = retone(make())
        for x, y, m, fl in r.deferred:                          # furniture keeps Emerald's own colours
            r.lower[r.sl(x, y)][m] = fl[m]
        return r
    run.__name__ = make.__name__
    return run

ROOMS = {'JohtoPokemonCenter1F': johto_center_1f, 'JohtoPokemonCenterB1F': johto_center_b1, 'JohtoMart': johto_mart,
         'SinnohPokemonCenter1F': sinnoh_center_1f, 'SinnohPokemonCenter2F': sinnoh_center_2f}
ROOMS = {n: finished(f) for n, f in ROOMS.items()}
