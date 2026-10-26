"""Celadon City, fifth round: the revised plan (owner, 2026-10-26).

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
    Game Corner 12 x 8.5 with its marquee, the prize corner beside it
    houses      timber cottages, the cafe's family, lower than the Center; the cafe on the
                cross street facing the Arboretum
    Arboretum   the whole south of the town from the Gym's old block east: groves of three
                kinds of tree round the pond, a gravel promenade with a footbridge over the
                canal, walks, benches between planters, Hoenn's secret base plants, flower
                beds along the cross street, and in a gravel plaza the blossom pool (a stone
                blossom for what Erika made of the Gym); no building
    lamps       Olivine's posts, along the kerbs and verges, never on the road or the
                cycleway

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
         (35, 42, 46, 46)]                                         # the blossom plaza
def floors():
    g = [['forest'] * W for _ in range(H)]
    rect(g, 4, 9, 60, 15, 'brick')                       # the terrace under the north row
    rect(g, 4, 15, 60, 16, 'kerb')
    rect(g, 4, 16, W, 19, 'pave')                        # the main road east to Route 7
    rect(g, 6, 16, 9, 37, 'pave')                        # the west avenue
    rect(g, 0, 34, 6, 36, 'pave')                        # the road west to Route 16
    rect(g, 9, 21, W - 4, 22, 'lawn')                    # the verge between the cycleway and the blocks
    rect(g, 9, 22, 19, 34, 'brick')                      # the market square, in the terrace's brick
    rect(g, 24, 22, 45, 34, 'pave')                      # the Game Corner's block
    rect(g, 25, 31, 31, 33, 'lawn')                      # lawn beds either side of its entrance walk
    rect(g, 34, 31, 44, 33, 'lawn')
    rect(g, 45, 22, 60, 34, 'grass')                     # cottages east, the cafe on the cross street
    rect(g, 45, 27, 60, 29, 'pave')                      # their lane
    rect(g, 6, 34, 59, 37, 'pave')                       # the cross street
    rect(g, 4, 37, 60, 50, 'meadow')                     # the Arboretum
    rect(g, 6, 37, 11, 40, 'garden')                     # flower beds along the cross street
    rect(g, 13, 37, 19, 40, 'garden')
    rect(g, 25, 37, 52, 40, 'garden')
    rect(g, 54, 37, 59, 40, 'garden')
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

# What stands where: name, kind, left cell (may be fractional), base row (the art's foot).
PLACES = [
    ('dept_store', 'dept_store', 5, 14), ('apartments', 'apartments', 26, 14), ('hotel', 'hotel', 34, 14),
    ('center', 'center', 44, 14), ('house_n0', 'cottage_red', 50, 14), ('house_n1', 'cottage_teal', 55, 14),
    ('gamecorner', 'game_corner', 26, 29), ('prize', 'prize_corner', 39, 29),
    ('house_e0', 'cottage_orange', 45, 26), ('house_e1', 'cottage_green', 50, 26), ('house_e2', 'cottage_red', 55, 26),
    ('cafe', 'cafe', 45, 33), ('house_e3', 'cottage_teal', 51, 33), ('house_e4', 'cottage_orange', 56, 33),
    ('fountain', 'fountain', 11.5, 31), ('blossom', 'blossom_pool', 38, 45.5),
]
# Stalls framing the square: (left cell, base row, colour, facing).
STALLS = [(10, 24, 'red', 'south'), (16, 24, 'orange', 'south'),
          (9, 28, 'green', 'east'), (9, 32, 'blue', 'east'),
          (18, 28, 'violet', 'west'), (18, 32, 'red', 'west')]
DOORS = dict(dept_store=(11, 14), apartments=(28, 14), hotel=(38, 14), center=(46, 14), gamecorner=(32, 29),
             prize=(42, 29), cafe=(48, 33))
# Olivine's lamps: on the terrace kerb, the verge, the quays, the square's corners, the
# Game Corner's forecourt and along the promenade's south edge.
LAMPS = [(x, 15) for x in (18, 25, 33, 43, 49, 59)] + [(x, 21) for x in (9, 25, 31, 37, 43, 49, 55, 61)] + \
        [(19, 27), (24, 27), (9, 33), (18, 33)] + [(x, 33) for x in (31, 33)] + \
        [(x, 42) for x in (5, 10, 13, 30, 34, 47, 51, 55)]
BENCHES = [(12, 33), (15, 33), (7, 42), (32, 42), (49, 42), (57, 42), (36, 45), (44, 45), (6, 49)]
PLANTS = [('big_plant', 26, 32), ('big_plant', 29, 32), ('big_plant', 35, 32), ('gorgeous_plant', 38, 32), ('big_plant', 42, 32),
          ('gorgeous_plant', 35, 43), ('gorgeous_plant', 44, 43), ('colorful_plant', 37, 47), ('colorful_plant', 42, 47),
          ('red_plant', 10, 39), ('red_plant', 13, 39), ('tropical_plant', 51, 39), ('tropical_plant', 54, 39),
          ('pretty_flowers', 13, 44), ('pretty_flowers', 10, 47), ('pretty_flowers', 54, 45), ('red_plant', 51, 46)]
