"""Celadon City, fifth and sixth rounds: the revised plan (owner, 2026-10-26).

Round 4's winding canal and its curving cycleway went back: "curved objects don't really work
with the Gen 3 games". This plan is drawn on the cell grid, every edge straight, and pressed
together the way HGSS and FireRed pack their Celadon (64 x 52 cells against round 4's 84 x 64):

    canal       one straight canal down from the north woods beside the Dept Store, past the
                market square and the Game Corner, into a small pond in the Arboretum;
                three bridges (the main road, the cross street, the Arboretum footbridge)
    cycleway    two lanes from Route 7 (east, to Saffron) along the main road, down the west
                avenue and out west on the road to Route 16 and the Cycling Road; nothing to
                the north
    market      the square framed by its stalls: two along the north edge facing south, two
                down each side facing in, the fountain in the middle, open to the cross
                street
    north row   the big buildings at full size on the brick terrace: the Dept Store (12 x 10
                cells), the apartments (7 x 10), the Pokemon Hotel (9 x 10), the Center
    Game Corner 12 x 8.5 with its marquee, against the canal's east quay, the prize counter
                inside it; two terrace houses beside it
    houses      timber cottages, the cafe's family, lower than the Center; the cafe on the
                cross street facing the Arboretum
    Arboretum   the whole south of the town from the Gym's old block east: groves of three
                kinds of tree round the pond, a gravel promenade with a footbridge over the
                canal, walks, benches between planters, Hoenn's secret base plants, flower
                beds along the cross street, and in a gravel plaza the blossom pool (a stone
                blossom for what Erika made of the Gym); no building
    lamps       HGSS's city lamp, few and in pattern, never on the road or the cycleway
    bridges     the flat wood bridge (Cherrygrove's pier deck), the cycleway painted on

Round 6 (the owner on round 5): the market's fountain in the middle of the square, the blossom
pool three cells up and one right in a gravel plaza the promenade runs through, and the houses
(HGSS's own Celadon houses) sandwiched together in terraces, no yard each, a cell back from the
road they face.

Cells: forest, brick, kerb, pave, cycle, lawn, grass, garden, gravel, meadow, water, bridge.
"""
from __future__ import annotations

W, H = 64, 52

def rect(g, x0, y0, x1, y1, v):
    for y in range(max(0, y0), min(H, y1)):
        for x in range(max(0, x0), min(W, x1)):
            g[y][x] = v

CANAL = (20, 0, 24, 42)             # x0, y0, x1, y1 (cells): the canal's water
POND = (15, 42, 28, 48)             # the pond it ends in
BRIDGES = dict(main=((19, 16, 25, 21), 'ew'), cross=((19, 34, 25, 37), 'ew'), arboretum=((19, 40, 25, 42), 'ew'))
CYCLE = [(4, 19, W, 21), (4, 19, 6, 38), (0, 36, 6, 38)]           # the cycleway's three straight runs
WALKS = [(4, 40, 60, 42),                                          # the promenade
         (11, 37, 13, 50), (4, 48, 13, 50), (52, 37, 54, 50), (29, 48, 60, 50), (40, 46, 42, 50),
         (36, 38, 47, 46)]                                         # the blossom plaza

def floors():
    g = [['forest'] * W for _ in range(H)]
    rect(g, 4, 9, 60, 15, 'brick')                       # the terrace under the north row
    rect(g, 4, 15, 60, 16, 'kerb')
    rect(g, 4, 16, W, 19, 'pave')                        # the main road east to Route 7
    rect(g, 6, 16, 8, 37, 'pave')                        # the west avenue
    rect(g, 0, 34, 6, 36, 'pave')                        # the road west to Route 16
    rect(g, 8, 21, W - 4, 22, 'lawn')                    # the verge between the cycleway and the blocks
    rect(g, 8, 22, 19, 34, 'brick')                      # the market square, in the terrace's brick
    rect(g, 24, 22, 45, 34, 'pave')                      # the Game Corner's block
    rect(g, 25, 31, 29, 33, 'lawn')                      # lawn beds either side of its entrance walk
    rect(g, 32, 31, 44, 33, 'lawn')
    rect(g, 45, 22, 60, 34, 'pave')                      # the east terraces: two rows of houses, a lane between
    rect(g, 6, 34, 59, 37, 'pave')                       # the cross street
    rect(g, 4, 37, 60, 50, 'meadow')                     # the Arboretum
    for x0, x1 in ((6, 11), (13, 19), (25, 36), (47, 52), (54, 59)):
        rect(g, x0, 37, x1, 40, 'garden')                # flower beds along the cross street
    for r in WALKS:
        rect(g, *r, 'gravel')
    for r in CYCLE:
        rect(g, *r, 'cycle')
    rect(g, *CANAL, 'water')
    rect(g, *POND, 'water')
    rect(g, 19, 22, 20, 34, 'pave')                      # quay walks either side of the canal
    rect(g, 24, 22, 25, 34, 'pave')
    for (x0, y0, x1, y1), _ in BRIDGES.values():
        for y in range(y0, y1):
            for x in range(x0, x1):
                if CANAL[0] <= x < CANAL[2]:
                    g[y][x] = 'bridge'
    return g

# What stands where: name, kind, left cell (fractional: the HGSS houses are 60 px, 3.75 cells,
# and stand wall to wall), base row (the art's foot).
HOUSE = 3.75
PLACES = [
    ('dept_store', 'dept_store', 4.5, 14), ('apartments', 'apartments', 25, 14), ('hotel', 'hotel', 33, 14),
    ('center', 'center', 43, 14),
    ('house_n0', 'house_coral', 49, 14), ('house_n1', 'house_teal', 49 + HOUSE, 14), ('house_n2', 'house_amber', 49 + 2 * HOUSE, 14),
    ('gamecorner', 'game_corner', 24, 29),                # against the canal's east quay; the prize counter is inside
    ('house_g0', 'house_plum', 37.5, 29), ('house_g1', 'house_amber', 37.5 + HOUSE, 29),
    ('house_a0', 'house_blue', 45, 25), ('house_a1', 'house_plum', 45 + HOUSE, 25),
    ('house_a2', 'house_teal', 45 + 2 * HOUSE, 25), ('house_a3', 'house_green', 45 + 3 * HOUSE, 25),
    ('cafe', 'cafe', 45, 32), ('flat', 'flat', 49.9, 32), ('house_b0', 'house_coral', 55.1, 32),
    ('fountain', 'fountain', 11, 30), ('blossom', 'blossom_pool', 39, 42.5),
]
# Stalls framing the square: (left cell, base row, colour, facing).
STALLS = [(9.5, 24, 'red', 'south'), (14.5, 24, 'orange', 'south'),
          (8, 28, 'green', 'east'), (8, 32, 'blue', 'east'),
          (16, 28, 'violet', 'west'), (16, 32, 'red', 'west')]
DOORS = dict(dept_store=(11, 14), apartments=(28, 14), hotel=(38, 14), center=(45, 14), gamecorner=(30, 29), house_g0=(39, 29), cafe=(47, 32))
# The street lamps (custom_art.street_lamp, HGSS's city lamp): either side of the main road
# bridge's north end, a lamp at each corner of the cross street's bridge, four along the
# promenade; none over the cycleway, none in front of a building or a stall
# (concept.overlaps checks).
LAMPS = [(18, 15), (24, 15),                                # the main road's bridge, either side of its north end
         (19, 33), (24, 33), (19, 37), (24, 37),             # the cross street's bridge, a lamp at each corner
         (5, 42), (29, 42), (47, 42), (55, 42)]              # the promenade, between its benches
BENCHES = [(11, 33), (15, 33), (7, 42), (32, 42), (49, 42), (57, 42), (37, 45), (45, 45)]
PLANTS = [('big_plant', 25, 32), ('big_plant', 27, 32), ('big_plant', 33, 32), ('gorgeous_plant', 36, 32), ('big_plant', 42, 32),
          ('gorgeous_plant', 36, 39), ('gorgeous_plant', 45, 39), ('colorful_plant', 37, 43), ('colorful_plant', 44, 43),
          ('red_plant', 10, 39), ('red_plant', 13, 39), ('tropical_plant', 51, 39), ('tropical_plant', 54, 39),
          ('pretty_flowers', 13, 44), ('pretty_flowers', 10, 47), ('pretty_flowers', 54, 45), ('red_plant', 51, 46)]
