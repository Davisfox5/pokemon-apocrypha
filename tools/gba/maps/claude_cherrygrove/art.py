"""Cherrygrove scenery: Gen 3 (RSE) pixel conventions, HGSS Johto shapes and colours.

Conventions copied from Emerald's own tiles: a single dark navy outline for
built things and dark green for foliage, three or four tones per material,
light from the top-left, hatched roof courses, a pale bevelled cornice between
roof and wall, blue glass with a white frame, red pixel lettering on white.
Shapes and palette come from HGSS Cherrygrove: rose hip roofs with a front
gable, timber-framed cream walls, orange rounded Pokemon Center, blue Mart,
round broccoli-crown trees, sandstone sea cliff, pale beach.
"""
from __future__ import annotations
import numpy as np
from .pixel import Palette, Canvas

NAVY = (58, 58, 92)

WATER = dict(light=(130, 196, 240), mid=(106, 172, 232), deep=(82, 140, 214))

PALETTES = {
    'TREE': Palette(6, [(30, 66, 44), (40, 106, 60), (64, 146, 76), (110, 190, 96), (160, 224, 120), (210, 246, 160),
                        (76, 48, 30), (122, 82, 46), (170, 124, 72), (52, 122, 66)],
                    ['ol', 'g0', 'g1', 'g2', 'g3', 'g4', 't0', 't1', 't2', 'gs']),
    'BLOSSOM': Palette(7, [(84, 42, 70), (154, 74, 122), (196, 108, 158), (228, 150, 190), (246, 190, 216), (255, 226, 238),
                           (76, 48, 30), (122, 82, 46), (170, 124, 72), (176, 92, 140)],
                       ['ol', 'g0', 'g1', 'g2', 'g3', 'g4', 't0', 't1', 't2', 'gs']),
    'TERRAIN': Palette(8, [NAVY, (106, 66, 44), (156, 106, 66), (198, 150, 100), (230, 194, 140), (246, 222, 172),
                           (70, 74, 90), (116, 122, 140), (164, 170, 186), (206, 210, 222), (238, 240, 246), (128, 150, 90)],
                       ['ol', 'r0', 'r1', 'r2', 'r3', 'r4', 'k0', 'k1', 'k2', 'k3', 'k4', 'moss']),
    'HOUSE': Palette(9, [NAVY, (156, 48, 74), (214, 84, 100), (240, 130, 138), (255, 186, 182),
                         (194, 154, 104), (232, 200, 148), (252, 236, 196), (104, 64, 40), (148, 100, 56),
                         (56, 110, 190), (108, 182, 240), (184, 226, 255), (206, 60, 56), (255, 255, 255)],
                     ['ol', 'r0', 'r1', 'r2', 'r3', 'w0', 'w1', 'w2', 'b0', 'b1', 'gl0', 'gl1', 'gl2', 'door', 'white']),
    'HOUSE2': Palette(10, [NAVY, (60, 82, 118), (94, 126, 162), (140, 172, 200), (196, 218, 236),
                           (170, 166, 150), (216, 212, 196), (244, 242, 228), (96, 70, 48), (140, 106, 68),
                           (56, 110, 190), (108, 182, 240), (184, 226, 255), (76, 122, 96), (255, 255, 255)],
                      ['ol', 'r0', 'r1', 'r2', 'r3', 'w0', 'w1', 'w2', 'b0', 'b1', 'gl0', 'gl1', 'gl2', 'door', 'white']),
    # Pokemon Center and Mart share one bank: orange ramp, blue ramp, grey walls, glass, red.
    'SHOPS': Palette(11, [NAVY, (186, 74, 30), (236, 118, 44), (252, 172, 96), (34, 84, 156), (58, 126, 208), (112, 180, 244),
                          (140, 148, 172), (196, 204, 220), (232, 236, 244), (255, 255, 255),
                          (48, 82, 156), (98, 160, 230), (170, 214, 250), (222, 48, 56)],
                     ['ol', 'o0', 'o1', 'o2', 'b0', 'b1', 'b2', 'w0', 'w1', 'w2', 'white', 'gl0', 'gl1', 'gl2', 'red']),
    'WOOD': Palette(12, [NAVY, (96, 60, 36), (146, 100, 58), (196, 148, 92), (230, 196, 140),
                         (255, 255, 255), (206, 210, 222), (150, 154, 172), (64, 110, 180), (128, 176, 232),
                         (104, 120, 96), (156, 172, 136), (216, 56, 56), (232, 200, 120)],
                    ['ol', 'd0', 'd1', 'd2', 'd3', 'white', 'grey', 'dgrey', 'blue', 'blue2', 'net', 'net2', 'red', 'rope']),
    # Flowers live in the free slots of the primary grass bank (2); beach in the primary path bank (5).
    'FLOWER': Palette(2, [(30, 66, 44), (60, 140, 76), (110, 190, 100), (222, 44, 60), (252, 116, 108),
                          (246, 202, 44), (255, 240, 150), (232, 116, 176), (255, 186, 218), (118, 84, 50)],
                      ['ol', 'l1', 'l2', 'red', 'red2', 'yel', 'yel2', 'pink', 'pink2', 'soil'], slots=[1, 2, 3, 5, 6, 7, 8, 9, 10, 11]),
    'SHORE': Palette(5, [(242, 228, 184), (252, 244, 212), (220, 198, 150), (188, 166, 126),
                         (255, 255, 255), (210, 236, 252), WATER['light'], WATER['mid'], WATER['deep'], (150, 132, 100)],
                     ['sand', 'sand2', 'sand0', 'wet', 'foam', 'foam2', 'wl', 'wm', 'wd', 'wet0'], slots=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
}

def canvas(w, h, bank):
    if bank in ('CENTER', 'MART'): bank = 'SHOPS'
    return Canvas(w, h, PALETTES[bank])

def paint(c, x, y, rows, key):
    c.rows(x, y, rows, key)

def mirror_rows(rows):
    return [r[::-1] for r in rows]

# ---------------------------------------------------------------- house

HOUSE_KEY = dict(O='ol', R='r0', r='r1', p='r2', P='r3', s='w0', w='w1', W='w2', B='b0', b='b1', d='gl0', g='gl1', G='gl2', D='door', F='white')

def roof_course(c, x0, x1, y, phase):
    """One 4-row course of rose roof tiles across [x0,x1]: highlight edge, seams, dark underside."""
    c.hline(x0, y, x1 - x0 + 1, 'r2')
    c.rect(x0, y + 1, x1 - x0 + 1, 2, 'r1')
    c.hline(x0, y + 3, x1 - x0 + 1, 'r0')
    for x in range(x0 + 3 + phase * 4, x1, 8):
        c.vline(x, y + 1, 2, 'r0')
        if x + 1 <= x1: c.put(x + 1, y + 1, 'r3')

def house(bank='HOUSE'):
    """64x64, 4x4 metatiles. A front-gabled wing on the left holds the door (column x 16..31)."""
    c = canvas(64, 64, bank)
    K = HOUSE_KEY
    # Main hip roof: ridge y=2, right slope to the eave at y=30.
    ridge_y, eave_y, top_l, top_r = 2, 30, 20, 47
    for y in range(ridge_y + 1, eave_y):
        t = (y - ridge_y) / (eave_y - ridge_y)
        x0 = round(top_l - top_l * t); x1 = round(top_r + (63 - top_r) * t)
        c.hline(x0, y, x1 - x0 + 1, 'r1')
    for y in range(ridge_y + 1, eave_y - 2, 4):
        xs = np.nonzero(c.px[y])[0]
        roof_course(c, int(xs[0]), int(xs[-1]), y, (y // 4) % 2)
    c.hline(top_l, ridge_y, top_r - top_l + 1, 'r3'); c.hline(top_l - 1, ridge_y + 1, top_r - top_l + 3, 'r2')
    c.hline(0, eave_y, 64, 'ol'); c.rect(1, eave_y + 1, 62, 2, 'w0')
    # Front gable wing, x 0..31: 45-degree fascia, timber truss, cream boards, attic window.
    apex = 5
    for y in range(apex, apex + 16):
        h = y - apex
        x0, x1 = 15 - h, 16 + h
        c.hline(x0, y, x1 - x0 + 1, 'w1')
        c.put(x0, y, 'r2'); c.put(x1, y, 'r2'); c.put(x0 + 1, y, 'r3'); c.put(x1 - 1, y, 'r3')
        if x0 - 1 >= 0: c.put(x0 - 1, y, 'ol')
        if x1 + 1 <= 31: c.put(x1 + 1, y, 'ol')
    c.hline(0, apex + 16, 32, 'r3'); c.hline(0, apex + 17, 32, 'r2'); c.hline(0, apex + 18, 32, 'r0'); c.hline(0, apex + 19, 32, 'ol')
    c.put(15, apex, 'r2'); c.put(16, apex, 'r2'); c.put(15, apex - 1, 'ol'); c.put(16, apex - 1, 'ol')
    for y in range(apex + 4, apex + 15):  # truss lines inside the gable
        h = y - apex
        c.put(15 - h + 3, y, 'b1'); c.put(16 + h - 3, y, 'b1')
    paint(c, 12, apex + 5, ['.FFFFFF.', 'FggGGggF', 'FgGGGggF', 'FggggggF', 'FddddddF', '.FFFFFF.'], K)
    c.rect(0, apex + 20, 32, 6, 'w1'); c.rect(0, apex + 20, 32, 1, 'w0')
    # Walls: shadow under the eaves, beam, horizontal boards, corner posts.
    c.rect(32, eave_y + 3, 31, 28, 'w1'); c.rect(0, apex + 21, 32, 41, 'w1')
    c.hline(32, eave_y + 3, 31, 'b1'); c.hline(32, eave_y + 4, 31, 'b0')
    c.hline(1, apex + 20, 31, 'b1'); c.hline(1, apex + 21, 31, 'b0')
    for y in range(eave_y + 8, 61, 4): c.hline(33, y, 29, 'w0'); c.hline(33, y + 1, 29, 'w2')
    for y in range(apex + 24, 61, 4): c.hline(1, y, 30, 'w0'); c.hline(1, y + 1, 30, 'w2')
    c.rect(61, eave_y + 5, 2, 26, 'b1'); c.vline(62, eave_y + 5, 26, 'b0')
    c.rect(0, apex + 22, 2, 40, 'b1'); c.vline(0, apex + 22, 40, 'b0')
    c.rect(31, apex + 22, 2, 40, 'b1'); c.vline(32, apex + 22, 40, 'b0'); c.vline(31, apex + 22, 40, 'b0')
    # Right window with a sill.
    paint(c, 44, 41, ['FFFFFFFFFFFFFF', 'FggGGGgFggggdF', 'FgGGGGgFggggdF', 'FgGGGggFggggdF', 'FggggggFggggdF', 'FFFFFFFFFFFFFF',
                      'FggggggFggggdF', 'FggggggFggggdF', 'FggggggFggggdF', 'FddddddFdddddF', 'FFFFFFFFFFFFFF', 'bbbbbbbbbbbbbb', 'BBBBBBBBBBBBBB'], K)
    # Door in the wing: timber frame, red panelled door, pane, knob, stone step.
    paint(c, 17, 41, ['BBBBBBBBBBBBBB', 'BDDDDDDDDDDDDB', 'BDFFFFFFFFFFDB', 'BDFgggGGgggFDB', 'BDFgggGgggdFDB', 'BDFggggggddFDB', 'BDFFFFFFFFFFDB',
                      'BDDDDDDDDDDDDB', 'BDOOOOOOOOOODB', 'BDDDDDDDDDDDDB', 'BDDDDDDDDDDDDB', 'BDDDDDDDDDFDDB', 'BDDDDDDDDDDDDB', 'BDDDDDDDDDDDDB',
                      'BDOOOOOOOOOODB', 'BDDDDDDDDDDDDB', 'BDDDDDDDDDDDDB', 'BDDDDDDDDDDDDB', 'BDDDDDDDDDDDDB', 'BBBBBBBBBBBBBB'], K)
    c.rect(16, 61, 16, 2, 'w2'); c.hline(16, 62, 16, 'w0')
    c.hline(1, 62, 62, 'w0'); c.hline(0, 63, 64, 'ol'); c.vline(63, eave_y, 34, 'ol')
    c.outline('ol')
    return c

CENTER_KEY = dict(O='ol', o='o0', a='o1', A='o2', h='o2', s='w0', w='w1', W='w2', F='white', d='gl0', g='gl1', G='gl2', R='red', f='w0')

def center():
    """80x64, 5x4 metatiles. Door column x 32..47."""
    c = canvas(80, 64, 'CENTER')
    # Rounded orange roof slab: highlight cap, ribbed body, dark underside.
    for y in range(2, 30):
        r = {2: 7, 3: 5, 4: 3, 5: 2, 6: 1, 7: 1, 26: 1, 27: 1, 28: 2, 29: 3}.get(y, 0)
        c.hline(3 + r, y, 74 - 2 * r, 'o1')
    c.hline(10, 2, 60, 'o2'); c.rect(8, 3, 64, 2, 'o2'); c.hline(6, 5, 68, 'o2'); c.hline(4, 6, 72, 'o2')
    for x in range(7, 74, 8):
        c.vline(x, 6, 20, 'o0'); c.vline(x + 1, 6, 20, 'o2')
    c.rect(4, 24, 72, 2, 'o0'); c.hline(4, 23, 72, 'o2')
    # Emblem: Poke Ball on the roof front.
    paint(c, 34, 9, ['    OOOO    ', '  OORRRROO  ', ' ORRRRRRRRO ', 'ORRRRRRRRRRO', 'ORRRRRRRRRRO', 'OOOOOOOOOOOO', 'OFFFFOOFFFFO', 'OFFFOFFFOFFO',
                     ' OFFFOOOFFO ', '  OOFFFFOO  ', '    OOOO    '], CENTER_KEY)
    c.put(38, 16, 'white'); c.put(39, 16, 'white'); c.put(40, 16, 'white'); c.put(41, 16, 'white')
    # Pale bevelled cornice, then grey walls.
    c.rect(2, 26, 76, 6, 'w2'); c.hline(2, 26, 76, 'white'); c.hline(2, 31, 76, 'w0')
    c.rect(2, 32, 76, 30, 'w1'); c.hline(2, 32, 76, 'w0')
    for x in (2, 76): c.rect(x, 32, 2, 30, 'w0')
    # Blue window bands each side, framed white.
    for wx in (8, 56):
        paint(c, wx, 40, ['FFFFFFFFFFFFFFFF', 'FggGGGgggggggggF', 'FgGGGGgggggggggF', 'FgGGGggggggggggF', 'FggggggggggggggF', 'FggggggggggggggF',
                          'FggggggggggggggF', 'FggggggggggggggF', 'FddddddddddddddF', 'FFFFFFFFFFFFFFFF', 'ssssssssssssssss'], CENTER_KEY)
    # Sliding glass door.
    paint(c, 31, 40, ['OOOOOOOOOOOOOOOOOO', 'OFFFFFFFFOFFFFFFFO', 'OFggGGggFOFggGGggO', 'OFgGGGggFOFgGGGggO', 'OFgGGgggFOFgGGgggO', 'OFggggggFOFggggggO',
                      'OFggggggFOFggggggO', 'OFggggggFOFggggggO', 'OFFFFFFFFOFFFFFFFO', 'OFggggggFOFggggggO', 'OFggggggFOFggggggO', 'OFggggggFOFggggggO',
                      'OFggggggFOFggggggO', 'OFggggggFOFggggggO', 'OFggggggFOFggggggO', 'OFggggggFOFggggggO', 'OFggggggFOFggggggO', 'OFggggggFOFggggggO',
                      'OFddddddFOFddddddO', 'OFFFFFFFFOFFFFFFFO', 'OOOOOOOOOOOOOOOOOO', 'ffffffffffffffffff'], CENTER_KEY)
    c.hline(2, 62, 76, 'w0'); c.hline(1, 63, 78, 'ol')
    c.outline('ol')
    return c

# ---------------------------------------------------------------- mart

FONT = {
    'M': ['#...#', '##.##', '#.#.#', '#...#', '#...#', '#...#', '#...#'],
    'A': ['.###.', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'],
    'R': ['####.', '#...#', '#...#', '####.', '#.#..', '#..#.', '#...#'],
    'T': ['#####', '..#..', '..#..', '..#..', '..#..', '..#..', '..#..'],
}
MART_KEY = CENTER_KEY | dict(o='b0', a='b1', A='b2', h='b2')

def mart():
    """64x48, 4x3 metatiles. Door column x 16..31."""
    c = canvas(64, 48, 'MART')
    for y in range(2, 22):
        r = {2: 5, 3: 3, 4: 2, 5: 1, 19: 1, 20: 2, 21: 3}.get(y, 0)
        c.hline(2 + r, y, 60 - 2 * r, 'b1')
    c.hline(8, 2, 48, 'b2'); c.rect(6, 3, 52, 2, 'b2'); c.hline(4, 5, 56, 'b2')
    for x in range(6, 58, 8):
        c.vline(x, 6, 12, 'b0'); c.vline(x + 1, 6, 12, 'b2')
    c.rect(3, 18, 58, 2, 'b0'); c.hline(3, 17, 58, 'b2')
    c.rect(2, 20, 60, 5, 'w2'); c.hline(2, 20, 60, 'white'); c.hline(2, 24, 60, 'w0')
    c.rect(2, 25, 60, 21, 'w1'); c.hline(2, 25, 60, 'w0')
    for x in (2, 60): c.rect(x, 25, 2, 21, 'w0')
    # Red MART lettering on a white sign, right of the door.
    c.rect(35, 28, 25, 12, 'white'); c.box(35, 28, 25, 12, 'w0')
    x = 37
    for ch in 'MART':
        for dy, line in enumerate(FONT[ch]):
            for dx, v in enumerate(line):
                if v == '#': c.put(x + dx, 30 + dy, 'red')
        x += 6
    c.hline(37, 38, 22, 'red')
    # Sliding door and a side window.
    paint(c, 15, 27, ['OOOOOOOOOOOOOOOOOO', 'OFFFFFFFFOFFFFFFFO', 'OFggGGggFOFggGGggO', 'OFgGGGggFOFgGGGggO', 'OFgGGgggFOFgGGgggO', 'OFggggggFOFggggggO',
                      'OFggggggFOFggggggO', 'OFFFFFFFFOFFFFFFFO', 'OFggggggFOFggggggO', 'OFggggggFOFggggggO', 'OFggggggFOFggggggO', 'OFggggggFOFggggggO',
                      'OFggggggFOFggggggO', 'OFggggggFOFggggggO', 'OFggggggFOFggggggO', 'OFddddddFOFddddddO', 'OFFFFFFFFOFFFFFFFO', 'OOOOOOOOOOOOOOOOOO',
                      'ffffffffffffffffff'], MART_KEY)
    paint(c, 4, 30, ['FFFFFFFFFF', 'FggGGggggF', 'FgGGGggggF', 'FgGGgggggF', 'FggggggggF', 'FggggggggF', 'FggggggggF', 'FddddddddF', 'FFFFFFFFFF', 'ssssssssss'], MART_KEY)
    c.hline(2, 46, 60, 'w0'); c.hline(1, 47, 62, 'ol')
    c.outline('ol')
    return c

# ---------------------------------------------------------------- trees

TREE_ROWS = [
    '...........OOOOOOOOO............',
    '.........OO333333333OO..........',
    '........O33344444433322O........',
    '.......O3334444444333322O.......',
    '......O33344444443333322O.......',
    '.....O333344444333333222O.......',
    '....O3333333333333333322OO......',
    '...O33333333333333322222O2O.....',
    '...O3O333O3333O3333O2222O22O....',
    '..O33OO33OO33OO333OO222OO222O...',
    '..O3333333333333333322222222O...',
    '.O33334433333333322222222222O...',
    '.O33344433333333222222222221O...',
    '.O3333333333333222222222221O1O..',
    'O3O3333O33333O33322O2222O2221O..',
    'O33OO33OO333OO333OO222OOO22O11O.',
    'O2223333333333333322222222211O..',
    'O22233333333333222222222211111O.',
    'O2222222222222222222222211111O..',
    '.O222O2222O22222O2222O21111111O.',
    '.O22OO222OO2222OO222OO1111111O..',
    '.O2222222222222222221111111100O.',
    '..O1222222222222221111111110O...',
    '..O11111111111111111111000000O..',
    '...O111111O111111O1111O00000O...',
    '....OO1111OOO111OOOO000000OO....',
    '......OOOO..OTuO...OOOOOOO......',
    '...........SOTuOS...............',
    '..........SSOTuOSS..............',
    '..........SSOTuOSS..............',
    '...........SOTuOS...............',
    '............OOOO................',
]
def tree(bank='TREE'):
    """32x32 (2x2 metatiles): round Johto crown in scalloped tiers, slim trunk, ground shadow."""
    c = canvas(32, 32, bank)
    paint(c, 0, 0, TREE_ROWS, dict(O='ol', **{'0': 'g0', '1': 'g1', '2': 'g2', '3': 'g3', '4': 'g4'}, T='t0', u='t2', S='gs'))
    return c

# ---------------------------------------------------------------- terrain

CLIFF_KEY = dict(O='ol', **{'0': 'r0', '1': 'r1', '2': 'r2', '3': 'r3', '4': 'r4'}, m='moss')
CLIFF_ROWS = [
    '................................',
    '................................',
    '..OOOOOOOOOOOOOOOOOOOOOOOOOOOO..',
    '.O4444444444444444444444444444O.',
    'O444443333333344444443333333344O',
    'O333333333333333333333333333333O',
    'O322222233333322222223333332223O',
    'O322222222222222222222222222223O',
    'O32222222222222O2222222222O2223O',
    'O3O222222O22222O222222O2222222O3',
    'O33O2222O222222O22222O22222222O3',
    'O2333322222222O333333222222O2223',
    'O2222222222222O222222222222O2222',
    'O2O11122222O111222222O222222O111',
    'O2O11111111O111111111O11111111O1',
    'O11111111111111111111111111111O1',
    'O11122222222111112222222221111O1',
    'O11222222O221111122222222O21111O',
    'O1222222O2221111O2222222O222111O',
    'O122222O22221111O222222O2222111O',
    'O1222222222211112222222222222110',
    'O1111111111111111111111111111110',
    'O11O1111111O1111111O11111111O110',
    'O11O1111111O1111111O11111111O110',
    'O111111111111111111111111111110O',
    'O000111000011110000111100001100O',
    'O0000000000000000000000000000000',
    'O0000000000000000000000000000000',
    'OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO',
    '................................',
    '................................',
    '................................',
]

def cliff_face():
    """32x32 sandstone cliff: lit rim, staggered rock pillows with soft joins, dark base."""
    c = canvas(32, 32, 'TERRAIN')
    c.hline(0, 2, 32, 'ol'); c.hline(0, 3, 32, 'r4'); c.hline(0, 4, 32, 'r3')
    tiers = [(5, [(0, 12), (12, 12), (24, 8)]), (12, [(-6, 12), (6, 12), (18, 12), (30, 12)]), (19, [(0, 12), (12, 12), (24, 8)]), (26, [(-6, 12), (6, 12), (18, 12), (30, 12)])]
    for y, pillows in tiers:
        for x0, w in pillows:
            for dy in range(6):
                if y + dy > 27: break
                inset = 1 if dy in (0, 5) else 0
                tone = ['r3', 'r2', 'r2', 'r2', 'r1', 'r0'][dy]
                for x in range(x0 + inset, x0 + w - inset):
                    if 0 <= x < 32: c.put(x, y + dy, tone)
                for x in (x0, x0 + w - 1):
                    if 0 <= x < 32 and 1 <= dy <= 4: c.put(x, y + dy, 'r1' if dy < 4 else 'r0')
            for x in (x0 - 1,):
                if 0 <= x < 32:
                    for dy in range(6):
                        if y + dy <= 27: c.put(x, y + dy, 'r0')
            if 0 <= x0 + 2 < 32: c.put(x0 + 2, y + 1, 'r4'); c.put(x0 + 3, y + 1, 'r4')
        for x in range(32):
            if y + 6 <= 27 and c.px[y + 6, x] == 0: c.put(x, y + 6, 'r0')
    c.rect(0, 28, 32, 2, 'r0'); c.hline(0, 30, 32, 'ol')
    for x, y in [(3, 3), (18, 3), (27, 3)]: c.put(x, y, 'moss'); c.put(x + 1, y, 'moss')
    return c

def cliff_end(side):
    c = cliff_face()
    for y in range(2, 29):
        t = (y - 2) / 26
        cut = int(9 * (1 - t) ** 1.5) + 1
        for x in range(cut):
            xx = x if side == 'left' else 31 - x
            c.px[y, xx] = 0
        xx = cut if side == 'left' else 31 - cut
        if c.px[y, xx]: c.px[y, xx] = c.c('ol')
    return c

ROCK1 = [
    '................', '......OOOO......', '....OO4433OO....', '...O44433322O...', '..O4443333222O..', '..O3333332222O..',
    '.O33333322222O..', '.O33332222221O..', '.O22222222111O..', '..O2222211111O..', '..O2221111110O..', '...O11111100O...',
    '....OOOO0000O...', '.......OOOOO....', '................', '................',
]
def rock(size):
    """Shore boulder: 16x16 or 32x24 grey stone with a lit crown."""
    key = dict(O='ol', **{'0': 'k0', '1': 'k1', '2': 'k2', '3': 'k3', '4': 'k4'})
    if size == 1:
        c = canvas(16, 16, 'TERRAIN'); paint(c, 0, 0, ROCK1, key); return c
    c = canvas(32, 24, 'TERRAIN')
    c.ellipse(15.5, 13, 14.5, 9.5, 'k1'); c.ellipse(13, 10, 11.5, 7, 'k2'); c.ellipse(9, 7.5, 6, 3.6, 'k3'); c.ellipse(7.5, 6.5, 2.6, 1.4, 'k4')
    c.ellipse(21, 6, 4.5, 3, 'k2'); c.ellipse(20, 5, 2.2, 1.2, 'k3')
    for y in range(15, 23):
        for x in range(32):
            if c.px[y, x] and x > 4 + (y - 15) * 2: c.px[y, x] = c.c('k0') if y > 19 else c.c('k1')
    c.hline(9, 16, 6, 'k0'); c.put(13, 12, 'k0'); c.put(22, 11, 'k0'); c.put(23, 12, 'k0')
    c.outline('ol'); return c

def sand_tile(kind):
    c = canvas(16, 16, 'SHORE')
    if kind == 'dry':
        c.rect(0, 0, 16, 16, 'sand')
        for x, y in [(2, 3), (9, 1), (13, 6), (5, 9), (11, 12), (1, 14), (7, 6), (14, 13)]: c.put(x, y, 'sand2')
        for x, y in [(4, 5), (12, 9), (8, 14), (0, 8)]: c.put(x, y, 'sand2'); c.put(x + 1, y, 'sand2')
        for x, y in [(6, 2), (10, 11), (15, 3), (3, 12)]: c.put(x, y, 'sand0')
    else:
        c.rect(0, 0, 16, 16, 'wet')
        for x, y in [(3, 2), (9, 5), (13, 10), (5, 12), (11, 14)]: c.put(x, y, 'wet0')
        for x, y in [(1, 7), (7, 9), (14, 1)]: c.put(x, y, 'sand0')
    return c

# ---------------------------------------------------------------- props (WOOD bank)

WOOD_KEY = dict(O='ol', **{'0': 'd0', '1': 'd1', '2': 'd2', '3': 'd3'}, F='white', g='grey', G='dgrey', b='blue', B='blue2', n='net', N='net2', R='red', r='rope')

def pier_deck():
    c = canvas(16, 16, 'WOOD')
    paint(c, 0, 0, ['3333333333333333', '2222222222222222', '2222222222222222', '2222122222221222', '1111111111111111', '3333333333333333',
                    '2222222222222222', '2221222222222222', '2222222222222122', '1111111111111111', '3333333333333333', '2222222222222222',
                    '2222222122222222', '2222222222212222', '1111111111111111', '0000000000000000'], WOOD_KEY)
    return c

def pier_side(side):
    c = pier_deck()
    if side == 'south':
        paint(c, 0, 10, ['3333333333333333', '1111111111111111', '0000000000000000', 'OOOOOOOOOOOOOOOO', '.O1O........O1O.', '.O0O........O0O.'], WOOD_KEY)
        paint(c, 0, 9, ['.O3O........O3O.', ], WOOD_KEY)
    elif side == 'north':
        paint(c, 0, 0, ['OOOOOOOOOOOOOOOO', '3333333333333333'], WOOD_KEY)
        paint(c, 1, 0, ['O3O', 'O2O', 'O1O', 'OOO'], WOOD_KEY); paint(c, 12, 0, ['O3O', 'O2O', 'O1O', 'OOO'], WOOD_KEY)
    elif side == 'west':
        c.vline(0, 0, 16, 'ol'); c.vline(1, 0, 16, 'd1')
        paint(c, 0, 4, ['O3O', 'O2O', 'O1O', 'OOO'], WOOD_KEY); paint(c, 0, 11, ['O3O', 'O2O', 'O1O', 'OOO'], WOOD_KEY)
    elif side == 'east':
        c.vline(15, 0, 16, 'ol'); c.vline(14, 0, 16, 'd1')
        paint(c, 13, 4, ['O3O', 'O2O', 'O1O', 'OOO'], WOOD_KEY); paint(c, 13, 11, ['O3O', 'O2O', 'O1O', 'OOO'], WOOD_KEY)
    return c

def rail(side):
    c = pier_deck()
    if side == 'h':
        paint(c, 0, 0, ['O..............O', 'O3O..........O3O', 'O2OOOOOOOOOOOO2O', 'O23333333333332O', 'O21111111111112O', 'O2OOOOOOOOOOOO2O',
                        'O2O..........O2O', 'O2OOOOOOOOOOOO2O', 'O23333333333332O', 'O21111111111112O', 'O2OOOOOOOOOOOO2O', 'O2O..........O2O',
                        'O1O..........O1O', 'OOO..........OOO'], WOOD_KEY)
    else:
        paint(c, 3, 0, ['OOOOOOOOOO', 'O33333333O', 'O22222222O', 'O11111111O', 'OOOOOOOOOO', '...O2O....', '...O2O....', 'OOOOOOOOOO',
                        'O33333333O', 'O22222222O', 'O11111111O', 'OOOOOOOOOO', '...O2O....', '...O2O....', '...O1O....', '...OOO....'], WOOD_KEY)
    return c

BOAT_ROWS = [
    '................................',
    '................................',
    '..........OOOOOOOOOOOOOOOOOOO...',
    '.......OOOFFFFFFFFFFFFFFFFFFFOO.',
    '.....OOFFFFFFFFFFFFFFFFFFFFFFFFO',
    '...OOFFFFOOOOOOOOOOOOOOOOFFFFFFO',
    '..OFFFFFO3333333333333330FFFFFFO',
    '.OFFFFFO33222222222222220FFFFFFO',
    'OFFFFFFO32221111111111120FFFFFFO',
    'OFFFFFFO32211111111111120FFFFFFO',
    'OFFFFFFO32221111111111120FFFFFFO',
    'OFFFFFFO33222222222222220FFFFFFO',
    '.OFFFFFFOOOOOOOOOOOOOOOOFFFFFFFO',
    '..OggFFFFFFFFFFFFFFFFFFFFFFFFggO',
    '...OObbbbbbbbbbbbbbbbbbbbbbbbbbO',
    '.....OOBBBBBBBBBBBBBBBBBBBBBBBBO',
    '.......OOOBBBBBBBBBBBBBBBBBBBBOO',
    '..........OOOOOOOOOOOOOOOOOOOO..',
    '................................',
]
def boat():
    c = canvas(32, 32, 'WOOD'); paint(c, 0, 4, BOAT_ROWS, WOOD_KEY)
    paint(c, 20, 7, ['OOOOOOOO', 'O333333O', 'O222222O', 'OOOOOOOO'], WOOD_KEY)
    for i in range(5): c.put(4 - i, 16 + i, 'rope')
    return c

def net_rack():
    c = canvas(32, 16, 'WOOD')
    paint(c, 0, 0, ['O3333333333333333333333333333330', 'O2222222222222222222222222222220', 'O1O.........................O1O.'], WOOD_KEY)
    for x in range(3, 27, 8):
        for y in range(3, 13):
            for xx in range(x, x + 6): c.put(xx, y, 'net' if (xx + y) % 2 else 'net2')
        c.hline(x, 13, 6, 'ol'); c.vline(x - 1, 3, 11, 'ol'); c.vline(x + 6, 3, 11, 'ol')
    for y in range(3, 16): c.put(1, y, 'd1'); c.put(2, y, 'd0'); c.put(29, y, 'd1'); c.put(30, y, 'd0')
    c.vline(0, 2, 14, 'ol'); c.vline(3, 2, 14, 'ol'); c.vline(28, 2, 14, 'ol'); c.vline(31, 2, 14, 'ol')
    return c

def fence(kind):
    c = canvas(16, 16, 'WOOD')
    if kind == 'h':
        paint(c, 0, 2, ['..O....O....O...', '.OFO..OFO..OFO..', '.OFgO.OFgO.OFgO.', 'OOFgOOOFgOOOFgOO', 'OFFFFFFFFFFFFFFO', 'OggggggggggggggO',
                        'OOFgOOOFgOOOFgOO', '.OFgO.OFgO.OFgO.', 'OOFgOOOFgOOOFgOO', 'OFFFFFFFFFFFFFFO', 'OggggggggggggggO', 'OOFgOOOFgOOOFgOO',
                        '.OFgO.OFgO.OFgO.', '.OOO..OOO..OOO..'], WOOD_KEY)
    elif kind == 'v':
        paint(c, 4, 0, ['..OFgO..', '..OFgO..', 'OOOFgOOO', 'OFFFFFFO', 'OggggggO', 'OOOFgOOO', '..OFgO..', '..OFgO..', 'OOOFgOOO', 'OFFFFFFO',
                        'OggggggO', 'OOOFgOOO', '..OFgO..', '..OFgO..', '..OFgO..', '..OOOO..'], WOOD_KEY)
    elif kind == 'post':
        paint(c, 5, 1, ['..O...', '.OFO..', 'OFFgO.', 'OFFgO.', 'OFFgO.', 'OFFgO.', 'OFFgO.', 'OFFgO.', 'OFFgO.', 'OFFgO.', 'OFFgO.', 'OFFgO.', 'OGGGO.', '.OOO..'], WOOD_KEY)
    return c

def signpost():
    c = canvas(16, 16, 'WOOD')
    paint(c, 1, 1, ['OOOOOOOOOOOOOO', 'O333333333333O', 'O322222222223O', 'O32O2O2O2O223O', 'O322222222223O', 'O32O2O2O22223O', 'O322222222223O',
                    'O311111111113O', 'OOOOOOOOOOOOOO', '.....O11O.....', '.....O11O.....', '.....O11O.....', '.....O11O.....', '....OO00OO....'], WOOD_KEY)
    return c

def mailbox():
    c = canvas(16, 16, 'WOOD')
    paint(c, 3, 1, ['...OOOOO..', '..ORRRRRO.', '.ORRRRRRRO', '.ORFFFRRRO', '.ORRRRRRRO', '.OOOOOOOOO', '.ORRRRRRRO', '.OOOOOOOOO',
                    '....OGO...', '....OGO...', '....OGO...', '....OGO...', '...OOOOO..'], WOOD_KEY)
    return c

def bench():
    c = canvas(16, 16, 'WOOD')
    paint(c, 0, 3, ['.OOOOOOOOOOOOOO.', '.O333333333333O.', '.O222222222222O.', '.OOOOOOOOOOOOOO.', '.O333333333333O.', '.O111111111111O.',
                    '.OOOOOOOOOOOOOO.', '..O1O......O1O..', '..O1O......O1O..', '..O0O......O0O..', '..OOO......OOO..'], WOOD_KEY)
    return c

def lamp():
    c = canvas(16, 32, 'WOOD')
    paint(c, 4, 0, ['..OOOO..', '.O3333O.', 'O333333O', 'O3rrrr3O', 'O3rrrr3O', 'O222222O', '.OOOOOO.', '...OO...', '..O11O..', '..O11O..',
                    '..O11O..', '..O11O..', '..O11O..', '..O11O..', '..O11O..', '..O11O..', '..O11O..', '..O11O..', '..O11O..', '..O11O..',
                    '..O11O..', '..O11O..', '.OO00OO.', 'O000000O', 'OOOOOOOO'], WOOD_KEY)
    return c

# ---------------------------------------------------------------- flowers (FLOWER bank)

FLOWER_KEY = dict(O='ol', l='ol', L='l1', M='l2', R='red', r='red2', Y='yel', y='yel2', P='pink', p='pink2', s='soil', S='soil')

def flowerbed(color):
    """16x16 HGSS style flower bed: two rows of tulips over tilled soil."""
    c = canvas(16, 16, 'FLOWER')
    for y in range(16):
        for x in range(16): c.put(x, y, 'soil' if (x + y) % 2 else 'ol')
    A, B = {'red': ('R', 'r'), 'yel': ('Y', 'y'), 'pink': ('P', 'p')}[color]
    tulip = ['.AB.', 'ABBA', '.AA.', 'lLLl', '.Ll.', '.lL.']
    tulip = [row.replace('A', A).replace('B', B) for row in tulip]
    for (x, y) in [(1, 0), (9, 1), (5, 8), (13, 8)]:
        paint(c, x, y, tulip, FLOWER_KEY)
    return c

def petals():
    c = canvas(16, 16, 'BLOSSOM')
    for x, y in [(2, 3), (11, 2), (6, 8), (13, 10), (3, 13), (9, 14)]: c.put(x, y, 'g3'); c.put(x + 1, y, 'g4')
    for x, y in [(8, 5), (1, 9), (14, 5)]: c.put(x, y, 'g4')
    return c

def bush():
    c = canvas(16, 16, 'TREE')
    paint(c, 0, 1, ['.....OOOOO......', '...OOMMMMLOO....', '..OMMMMMMLLLO...', '.OMMMLMMMLLLLO..', 'OMMLLLLLLLLLLLO.', 'OMLLLLLLLLLLLLO.',
                    'OLLLLLLLlLLLLlO.', 'OLLLLlLLLLLlLLO.', 'OLLlLLLLlLLLLlO.', '.OLLLlLLLLLlLO..', '.OllLLLllLLllO..', '..OOllllllllOO..',
                    '....OOOOOOOO....'], dict(O='ol', l='g1', L='g2', M='g3'))
    return c

ASSETS = dict(house=lambda: house('HOUSE'), house2=lambda: house('HOUSE2'), center=center, mart=mart,
              tree=lambda: tree('TREE'), blossom=lambda: tree('BLOSSOM'), cliff=cliff_face,
              cliff_l=lambda: cliff_end('left'), cliff_r=lambda: cliff_end('right'), rock1=lambda: rock(1), rock2=lambda: rock(2),
              sand=lambda: sand_tile('dry'), sand_wet=lambda: sand_tile('wet'), deck=pier_deck,
              deck_s=lambda: pier_side('south'), deck_n=lambda: pier_side('north'), deck_w=lambda: pier_side('west'), deck_e=lambda: pier_side('east'),
              rail_h=lambda: rail('h'), rail_v=lambda: rail('v'), boat=boat, nets=net_rack,
              fence_h=lambda: fence('h'), fence_v=lambda: fence('v'), fence_post=lambda: fence('post'),
              sign=signpost, mailbox=mailbox, bench=bench, bed_red=lambda: flowerbed('red'), bed_yel=lambda: flowerbed('yel'),
              bed_pink=lambda: flowerbed('pink'), petals=petals, bush=bush, lamp=lamp)

def build_all():
    return {k: f() for k, f in ASSETS.items()}
