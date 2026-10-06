"""Route 29 and Route 30 cell plans, read off the 1:1 HGSS renders.

Coordinates are metatiles on each render's own grid (art.ORIGIN), which is also the map grid:
Route 29 is 98 x 34 with Cherrygrove to the west and New Bark to the east; Route 30 is 35 x 74
with Cherrygrove below and the Route 31 stairs at the top. Each plan starts as forest and
carves the HGSS layout out of it with rectangles (x, y, w, h), in order:

    T forest (lattice trees)   . lawn   P sand path   G tall grass   W water
    _ ledge, jump south        | ledge wall   ^ ledge wall top
    a ledge corner, wall from the north turning east   b ... turning west   c ledge turning south
    # rock wall (Route 30)    = wooden steps    F railing (Route 29 lookout)

Where the HGSS path stops a few cells short of the town edge, it is extended so it meets the
town's lane. Apocrypha additions from the design bible (Chapter 1 world design) are marked.
"""
from __future__ import annotations
import numpy as np

def plan(w, h, ops):
    g = np.full((h, w), 'T', dtype='<U1')
    for ch, x, y, ww, hh in ops:
        g[max(y, 0):y + hh, max(x, 0):x + ww] = ch
    return g

# ----------------------------------------------------------------- Route 29 (Cherrygrove -> New Bark)

R29_W, R29_H = 98, 34
R29_OPS = [
    # north of the Route 46 gate (behind the closed gate)
    ('P', 50, 0, 5, 2),
    # west end: the entry from Cherrygrove (path extended to the town edge), sign nook
    ('.', 0, 14, 13, 5), ('.', 5, 12, 5, 2),
    ('P', 0, 16, 13, 2), ('P', 0, 18, 3, 1), ('P', 9, 18, 4, 1), ('P', 10, 19, 17, 2),   # three rows at the seam, like the town's lane
    ('G', 9, 19, 1, 2), ('G', 9, 21, 5, 6),    # HGSS starts this block at x 7; columns 0-8 are in the seam window (seams.py)
    # the pocket below the first ledge and the upper lawn with the Apricorn tree
    ('.', 15, 15, 2, 1), ('.', 13, 16, 4, 3), ('.', 17, 10, 12, 4), ('.', 19, 14, 3, 1), ('.', 19, 18, 3, 1),
    ('G', 17, 15, 14, 3),
    # centre: open lawn, the tall-grass block under the north woods, tree clumps, the southern ledge
    ('.', 27, 19, 2, 2), ('.', 29, 10, 20, 15), ('.', 36, 9, 2, 1), ('.', 45, 9, 3, 1),
    ('G', 29, 11, 7, 3), ('G', 29, 14, 2, 1), ('G', 36, 13, 1, 1),
    ('T', 38, 8, 7, 5), ('T', 37, 13, 3, 1), ('T', 31, 14, 8, 4), ('T', 39, 14, 6, 3), ('T', 42, 17, 3, 1),
    ('T', 45, 16, 4, 4), ('T', 46, 20, 3, 2), ('T', 36, 19, 6, 4), ('T', 41, 20, 5, 3), ('T', 24, 21, 7, 7),
    # the Route 46 gate clearing and the east-centre lawns
    ('.', 48, 10, 26, 15), ('.', 65, 6, 9, 4), ('.', 48, 25, 15, 2),
    ('T', 55, 9, 4, 5), ('T', 51, 16, 2, 2), ('T', 55, 16, 8, 3), ('T', 66, 11, 4, 7), ('T', 63, 19, 5, 7),
    ('G', 59, 10, 5, 4), ('G', 55, 14, 10, 2), ('G', 63, 16, 3, 3), ('G', 65, 6, 9, 5), ('G', 70, 11, 4, 1),
    ('G', 69, 16, 5, 5),
    ('P', 57, 24, 4, 3),
    # east end: open lawn to New Bark, the sand path, tall grass and the last ledge
    ('.', 72, 15, 26, 4), ('.', 82, 13, 16, 2), ('.', 72, 12, 1, 3), ('.', 72, 19, 5, 3), ('.', 78, 19, 13, 1),
    ('.', 68, 23, 14, 3),
    ('G', 72, 16, 2, 6), ('G', 78, 17, 7, 5), ('G', 85, 20, 6, 2), ('G', 68, 23, 5, 3), ('G', 78, 22, 4, 4),
    ('P', 86, 16, 12, 2), ('P', 74, 23, 5, 2),
    ('T', 91, 19, 7, 3),
    # ledges and ledge walls
    ('_', 15, 14, 4, 1), ('_', 22, 14, 6, 1), ('b', 28, 14, 1, 1), ('|', 28, 10, 1, 4), ('^', 28, 10, 1, 1),
    ('^', 13, 16, 1, 1), ('|', 13, 17, 1, 1), ('a', 13, 18, 1, 1), ('_', 14, 18, 5, 1), ('_', 22, 18, 9, 1),
    ('_', 31, 22, 5, 1),
    ('_', 49, 18, 3, 1), ('c', 52, 18, 1, 1), ('|', 52, 19, 1, 3), ('a', 52, 22, 1, 1), ('_', 53, 22, 4, 1),
    ('_', 59, 22, 4, 1),
    ('_', 68, 22, 9, 1), ('b', 77, 22, 1, 1), ('|', 77, 17, 1, 5), ('^', 77, 16, 1, 1),
    # Apocrypha: the sea-view lookout (design bible, Route 29 "ridge overlooking the sea"): a lawn pocket
    # beside the sand nook, railed at the cliff edge, with the coast running under the whole route
    ('.', 54, 25, 9, 2), ('F', 54, 27, 9, 1),
]
R29_COAST = (28, 31)          # cliff crest row .. foot row; open sea below the foot
R29_SIGNS = [('WestSign', 6, 14), ('EastSign', 87, 14)]
R29_GATE = (48, 1)            # top-left cell of the 9 x 9 cut; building solid, steps walkable
R29_APRICORN = (20, 9)        # top-left cell of the 3 x 3 cut; the trunk stands on (21, 11)
R29_BENCHES = [(56, 26), (60, 26)]
R29_HIDDEN_POTION = (62, 25)  # design bible: Route 29's one optional hidden item, a Potion, off the main path
R29_ORANGE = [(45, 10), (46, 10), (47, 10), (48, 10), (45, 11), (46, 11), (49, 10), (43, 23), (44, 23), (72, 13), (73, 13), (85, 13), (88, 13), (89, 13)]
R29_DAISIES = [(36, 10), (43, 13), (60, 19), (82, 14), (6, 12)]   # 3 x 2 patches (the town's own daisy overlay)
R29_BLOSSOM_MAX_X = 6         # design bible: the westmost front-row trees are blossom trees spilling from Cherrygrove
R29_LATTICE = (0, 16)         # x parity, y phase (px mod 24): continues Cherrygrove's east woods across the seam
R29_TOWN_OFFSET = -4          # Route 29 row 16 meets Cherrygrove row 12

def route29():
    return plan(R29_W, R29_H, R29_OPS)

# ----------------------------------------------------------------- Route 30 (Cherrygrove -> Route 31)

R30_W, R30_H = 35, 74
R30_OPS = [
    # top: the Route 31 steps and the plateau's rock rim; the east cliff
    ('#', 12, 0, 22, 2), ('=', 9, 0, 3, 2), ('#', 32, 2, 2, 44),
    # the northern corridor and the plateau with Mr. Pokemon's house
    ('P', 9, 2, 3, 25), ('.', 12, 2, 1, 25), ('.', 16, 2, 16, 25), ('.', 5, 7, 4, 18), ('.', 12, 22, 3, 5),
    ('T', 16, 2, 5, 3), ('T', 16, 7, 5, 5), ('.', 13, 5, 3, 2), ('T', 30, 2, 2, 9), ('T', 22, 13, 8, 6), ('T', 20, 19, 6, 6), ('T', 5, 18, 2, 7),
    ('G', 5, 7, 4, 5), ('.', 7, 11, 2, 1), ('G', 5, 12, 2, 1), ('G', 5, 13, 4, 5),
    ('G', 18, 13, 4, 2), ('G', 26, 11, 6, 3), ('G', 30, 14, 2, 5), ('G', 26, 19, 6, 3), ('G', 16, 19, 4, 6),
    ('_', 9, 3, 3, 1), ('_', 7, 12, 6, 1), ('_', 8, 20, 5, 1),
    ('|', 15, 21, 1, 6),
    ('T', 28, 25, 4, 21), ('.', 12, 27, 16, 1), ('G', 20, 26, 8, 2), ('P', 9, 27, 3, 1),
    # the middle steps through the rock and the path down to the junction
    ('=', 9, 28, 3, 1), ('#', 7, 28, 2, 1), ('#', 12, 28, 2, 1), ('#', 7, 29, 1, 7), ('#', 4, 35, 5, 1),
    ('.', 8, 29, 1, 6), ('P', 9, 29, 3, 8), ('.', 12, 29, 1, 4), ('_', 8, 31, 4, 1),
    ('.', 12, 33, 16, 8), ('G', 12, 33, 3, 3), ('T', 15, 32, 3, 4),
    ('P', 7, 37, 14, 2), ('P', 18, 36, 9, 1), ('P', 25, 33, 2, 3),
    ('.', 10, 39, 11, 3), ('T', 10, 40, 3, 10), ('T', 13, 44, 4, 6), ('T', 26, 38, 2, 9),
    ('G', 21, 38, 5, 4), ('G', 17, 42, 9, 6), ('G', 14, 42, 3, 2), ('G', 18, 48, 3, 3),
    ('P', 7, 39, 3, 24), ('#', 4, 36, 1, 27),
    # the pond and the berry house
    ('W', 21, 47, 6, 11),
    ('.', 10, 49, 11, 13), ('T', 10, 48, 3, 3), ('_', 7, 49, 3, 1),
    ('P', 7, 54, 10, 2), ('P', 15, 56, 2, 4), ('P', 7, 60, 10, 2), ('.', 10, 62, 11, 1),
    # the low rock band with two flights of steps, and the grass above Cherrygrove
    ('#', 5, 63, 21, 1), ('=', 6, 63, 4, 1), ('=', 17, 63, 4, 1),
    ('.', 5, 64, 20, 6), ('.', 5, 70, 2, 4), ('.', 10, 64, 1, 10), ('P', 7, 64, 3, 10),
    ('G', 15, 64, 7, 2), ('_', 5, 65, 10, 1), ('T', 11, 68, 11, 2), ('T', 22, 64, 3, 6), ('#', 4, 64, 1, 2),
    # Rows 66-73 sit in the seam window at the Cherrygrove crossing (seams.py): only terrain both maps draw the same.
    # HGSS runs the ledge a row lower and the tall grass four rows further down; woods from x 11 keep the Pokemon
    # Center out of this route's view, so only the Mart and a signpost are copied from the town.
    ('W', 30, 70, 5, 4),      # the pond that continues into Cherrygrove's north-east corner
]
R30_SIGNS = [('JunctionSign', 20, 34), ('RouteSign', 13, 58)]
R30_MR_POKEMON = (23, 2)      # top-left cell of the 9 x 6 cut (drawn 4 px higher for the chimney)
R30_BERRY_HOUSE = (10, 48)    # top-left cell of the 9 x 7 cut
R30_BERRY_TREES = [(20, 4)]   # top-left cell of the 3 x 2 cut; the trunk stands on (21, 5)
R30_STAIRS = [('top', 9, 0, 0), ('mid', 9, 27, 0), ('low', 6, 62, 8), ('low', 17, 62, 8)]
R30_ORANGE = [(12, 23), (13, 23), (14, 23), (12, 24), (13, 24), (14, 24), (13, 25), (11, 56), (12, 57), (13, 56)]
R30_DAISIES = [(21, 33), (16, 36), (17, 53), (28, 8)]
R30_LATTICE = (0, 8)          # continues Cherrygrove's north woods across the seam (74 rows = 1184 px = 8 mod 24)
R30_TOWN_OFFSET = 24          # Route 30 column 0 sits over Cherrygrove column 24: the path x 7-9 meets the town's x 31-33

def route30():
    return plan(R30_W, R30_H, R30_OPS)
