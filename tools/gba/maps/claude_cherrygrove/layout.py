"""Cherrygrove City layout: my reading of the HGSS town, ten years on.

Coordinates are metatiles (16 px). West is open sea under a sandstone cliff,
a concave beach runs down the west side of town, Route 30 leaves north beside
the shops and Route 29 leaves east past the player's home. The blossom park and
the faded fishing pier are the two Apocrypha additions the design bible asks for.
"""
W, H = 60, 34

# Route exits: north gap columns and east gap rows.
NORTH_EXIT = (31, 34)   # x range [31,34)
EAST_EXIT = (12, 15)    # y range [12,15)

# Beach: for each row, the sea ends at shore(y) and sand ends at sand_end(y) (exclusive).
_SHORE = {4: 20, 6: 19, 8: 17, 10: 16, 12: 15, 14: 15, 16: 15, 18: 15, 20: 16, 22: 17, 24: 18, 26: 19, 28: 20, 29: 21}
_SAND_END = {4: 25, 5: 25, 6: 24, 7: 24, 8: 23, 9: 23, 10: 23, 11: 22, 12: 22, 13: 22, 14: 22, 15: 22, 16: 22, 17: 23,
             18: 23, 19: 24, 20: 24, 21: 25, 22: 26, 23: 27, 24: 28, 25: 29, 26: 29, 27: 30, 28: 30, 29: 30}

def _interp(table, y):
    if y in table: return table[y]
    lo = max(k for k in table if k < y) if any(k < y for k in table) else min(table)
    hi = min(k for k in table if k > y) if any(k > y for k in table) else max(table)
    if lo == hi: return table[lo]
    return round(table[lo] + (table[hi] - table[lo]) * (y - lo) / (hi - lo))

def shore(y):
    """First non-sea column on row y (the shoreline cell)."""
    return _interp(_SHORE, min(max(y, 4), 29))

def sand_end(y):
    """First grass column east of the beach on row y."""
    return _interp(_SAND_END, min(max(y, 4), 29))

CLIFF_ROWS = (2, 3)          # rim row, face row
CLIFF_X = (0, 28)            # spans the whole north-west, ends where the town's trees begin

# Buildings: name, style, top-left cell. Door cell derives from the style.
BUILDINGS = [
    dict(name='Mart', style='mart', x=35, y=5),
    dict(name='PokemonCenter', style='center', x=42, y=4),
    dict(name='NeighborHouse', style='house', x=28, y=8),
    dict(name='GoldHouse', style='house', x=38, y=11),
    dict(name='PlayerHouse', style='house', x=49, y=14),
    dict(name='TransplantHouse', style='house2', x=31, y=21),
]
DOOR_COLUMN = dict(house=1, house2=1, center=2, mart=1)
SIZE = dict(house=(4, 4), house2=(4, 4), center=(5, 4), mart=(4, 3))

def door_of(b):
    w, h = SIZE[b['style']]
    return (b['x'] + DOOR_COLUMN[b['style']], b['y'] + h - 1)

# Sand lanes (rectangles) – the path network, in walking order around the town.
LANES = [
    (31, 0, 3, 9),     # from Route 30 down to the shop front
    (31, 8, 17, 2),    # shop front, west to east
    (35, 9, 2, 7),     # down between neighbour and Gold's house
    (33, 15, 21, 2),   # main east–west lane through the middle of town
    (52, 12, 8, 3),    # to Route 29 (matches the east exit rows)
    (52, 12, 2, 4),    # join lane to the exit
    (45, 17, 2, 4),    # down to the park
    (40, 20, 9, 2),    # park promenade
    (36, 17, 2, 5),    # west lane to the transplant home and the waterfront
    (30, 25, 8, 2),    # waterfront lane
]

# Scattered trees (top-left cells of 2x3 crowns) placed by hand, plus the bands.
TREES = [
    (26, 4), (25, 12), (30, 18), (33, 18), (27, 22),
    (48, 10), (52, 9), (54, 10), (56, 8),  (55, 18), (56, 21), (54, 23), (51, 25),
    (37, 27), (33, 27), (43, 27), (50, 27), (36, 3), (39, 2),
]
BLOSSOMS = [(38, 22), (48, 21), (41, 24), (46, 24), (43, 22)]
# Forest bands: (x0, y0, x1, y1) inclusive cell ranges filled with a staggered crown lattice.
FOREST = [
    (28, -2, 30, 2), (34, -2, 59, 2),   # north wall, split at the Route 30 gap
    (56, 4, 59, 11), (56, 15, 59, 33),  # east wall, split at the Route 29 gap
    (31, 29, 59, 33),                   # south wall
    (0, -2, 27, 0),                     # cliff-top wood
]

# Fenced gardens: (x, y, w, h) with beds inside a picket fence.
GARDENS = [
    (48, 6, 7, 2),    # east of the Pokemon Center
    (43, 17, 5, 2),   # below the battle yard
    (26, 16, 3, 3),   # neighbour's plot by the beach
]
BATTLE_YARD = (43, 12, 5, 4)   # worn sand ring east of Gold's house
PETALS = (38, 21, 12, 8)       # park lawn area
PARK_PROPS = dict(bench=[(42, 26), (47, 26)], lamp=[(40, 19), (49, 19)])

PIER = dict(x0=14, x1=22, y=26)          # deck cells x0..x1-1 on rows y, y+1
BOATS = [(9, 23), (15, 28)]
NETS = [(24, 28)]
LOOKOUT = dict(x=17, y=5, w=4, h=2)     # timber deck over the water below the cliff
ROCKS1 = [(6, 8), (11, 12), (8, 19), (3, 26), (12, 31), (24, 32), (5, 14)]
ROCKS2 = [(2, 6), (9, 30), (20, 31)]
SIGNS = [
    ('TownSign', 37, 17), ('NorthSign', 34, 4), ('EastSign', 53, 11), ('GoldSign', 42, 15), ('WaterfrontSign', 31, 27),
    ('ParkSign', 39, 20), ('LookoutSign', 21, 7),
]
MAILBOXES = [(31, 12), (41, 15), (52, 18), (34, 25)]
BUSHES = [(32, 12), (42, 13), (53, 17), (27, 10)]

SPAWN = (50, 18)    # new game start: outside the player's front door
