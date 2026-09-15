"""Cherrygrove City layout: my reading of the HGSS town, ten years on.

Coordinates are metatiles (16 px). West is open sea under a sandstone cliff,
a concave beach runs down the west side of town, Route 30 leaves north beside
the shops and Route 29 leaves east past the player's home. The blossom park and
the faded fishing pier are the two Apocrypha additions the design bible asks for.

Building footprints follow the HGSS models: homes are five cells wide and five
tall (roof top to doorstep), the Pokemon Center six by six, the Mart five by four.
"""
W, H = 60, 34

# Route exits: north gap columns and east gap rows.
NORTH_EXIT = (31, 34)   # x range [31,34)
EAST_EXIT = (12, 15)    # y range [12,15)

# Beach: for each row, the sea ends at shore(y) and sand ends at sand_end(y) (exclusive).
_SHORE = {5: 20, 6: 19, 8: 17, 10: 16, 12: 15, 14: 15, 16: 15, 18: 15, 20: 16, 22: 17, 24: 18, 26: 19, 28: 20, 29: 21}
_SAND_END = {5: 25, 6: 24, 7: 24, 8: 23, 9: 23, 10: 23, 11: 22, 12: 22, 13: 22, 14: 22, 15: 22, 16: 22, 17: 23,
             18: 23, 19: 24, 20: 24, 21: 25, 22: 26, 23: 27, 24: 28, 25: 29, 26: 29, 27: 30, 28: 30, 29: 30}

def _interp(table, y):
    if y in table: return table[y]
    lo = max(k for k in table if k < y) if any(k < y for k in table) else min(table)
    hi = min(k for k in table if k > y) if any(k > y for k in table) else max(table)
    if lo == hi: return table[lo]
    return round(table[lo] + (table[hi] - table[lo]) * (y - lo) / (hi - lo))

def shore(y):
    """First non-sea column on row y (the shoreline cell)."""
    return _interp(_SHORE, min(max(y, 5), 29))

def sand_end(y):
    """First grass column east of the beach on row y."""
    return _interp(_SAND_END, min(max(y, 5), 29))

SEA_TOP = 5                  # first open-sea row below the cliff foot
CLIFF_ROWS = (1, 4)          # crest row .. foot row (the HGSS cliff is four cells tall)
CLIFF_X = (0, 28)            # spans the whole north-west, ends under the town's trees

# Buildings: name, style, top-left cell. Door cell derives from the style.
BUILDINGS = [
    dict(name='Mart', style='mart', x=35, y=4),
    dict(name='PokemonCenter', style='center', x=42, y=2),
    dict(name='NeighborHouse', style='house_l', x=26, y=9),
    dict(name='GoldHouse', style='gable', x=38, y=10),
    dict(name='PlayerHouse', style='house', x=48, y=9),
    dict(name='TransplantHouse', style='house2', x=31, y=21),
]
DOOR_COLUMN = dict(house=1, house_l=1, house2=1, gable=2, center=2, mart=1)
SIZE = dict(house=(5, 5), house_l=(5, 5), house2=(5, 5), gable=(5, 5), center=(6, 6), mart=(5, 4))

def door_of(b):
    w, h = SIZE[b['style']]
    return (b['x'] + DOOR_COLUMN[b['style']], b['y'] + h - 1)

# Sand lanes (rectangles) - the path network, in walking order around the town.
LANES = [
    (31, 0, 3, 9),     # from Route 30 down to the shop front
    (31, 8, 17, 2),    # shop front, west to east (Mart and Center doorsteps)
    (35, 10, 2, 6),    # down between the neighbour's plot and Gold's house
    (33, 15, 21, 2),   # main east-west lane through the middle of town
    (53, 12, 7, 3),    # to Route 29 (matches the east exit rows)
    (49, 14, 2, 1),    # player's doorstep
    (44, 17, 2, 2),    # down to the park
    (38, 19, 8, 2),    # park promenade
    (36, 17, 2, 10),   # west lane to the transplant home and the waterfront
    (30, 26, 8, 2),    # waterfront lane
]

# Scattered trees (top-left cells of 2x3 crowns) placed by hand, plus the bands.
TREES = [
    (25, 6), (23, 15), (30, 17), (27, 22), (33, 11),
    (55, 9), (55, 17), (55, 21), (52, 24), (49, 27),
    (37, 27), (33, 28), (43, 27), (36, 1), (39, 1),
]
BLOSSOMS = [(38, 22), (47, 21), (41, 24), (46, 24), (43, 22)]
# Forest bands: (x0, y0, x1, y1) inclusive cell ranges filled with the HGSS lattice
# (32 px rows, 32 px columns, odd rows offset one cell).
FOREST = [
    (28, -3, 30, 0), (34, -3, 59, 0),   # north wall, split at the Route 30 gap
    (56, 3, 59, 9), (56, 16, 59, 33),   # east wall, split at the Route 29 gap
    (31, 29, 59, 33),                   # south wall
    (0, -3, 27, -1),                    # cliff-top wood
]

# Fenced gardens: (x, y, w, h) with tulip beds inside a picket fence.
GARDENS = [
    (49, 5, 6, 2),    # east of the Pokemon Center
    (47, 18, 4, 2),   # beside the park
    (26, 16, 3, 3),   # neighbour's plot by the beach
]
BATTLE_YARD = (43, 11, 4, 4)   # worn sand ring east of Gold's house
PETALS = (38, 21, 12, 8)       # park lawn area (daisy patches)
PARK_PROPS = dict(bench=[(40, 27), (45, 27)], lamp=[(37, 21), (45, 22)])

PIER = dict(x0=14, x1=22, y=26)          # deck cells x0..x1-1 on rows y, y+1
BOATS = [(9, 23), (15, 29)]
NETS = [(24, 28)]
LOOKOUT = dict(x=17, y=5, w=4, h=2)     # timber deck over the water below the cliff
SEA_ROCKS = [(2, 7), (9, 30), (20, 31), (6, 12), (11, 20)]      # 2x2 grey boulders in the bay
SEA_ROCKS_SMALL = [(6, 9), (12, 13), (8, 19), (3, 26), (24, 32), (5, 15)]
ROCKS = [(23, 30), (21, 10)]             # brown boulders on the sand
SIGNS = [
    ('TownSign', 34, 17), ('NorthSign', 34, 3), ('EastSign', 54, 11), ('GoldSign', 43, 10), ('WaterfrontSign', 29, 28),
    ('ParkSign', 38, 21), ('LookoutSign', 21, 8),
]
MAILBOXES = [(25, 13), (37, 14), (47, 13), (30, 25)]
BUSHES = [(34, 14), (53, 10), (55, 15), (24, 22)]
PLANTERS = []   # planters are part of the house sprites

SPAWN = (49, 14)    # new game start: outside the player's front door
