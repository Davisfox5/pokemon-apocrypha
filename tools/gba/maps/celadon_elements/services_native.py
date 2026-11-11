"""The market's services building (HGSS's Celadon Dept Store), designed from scratch in Gen 3's own
pieces with HGSS's colours (owner, 2026-11-11: "Build it from scratch using as much gen 3 stuff
with gen 4 style and color as you can, just like you did the apartments").

    python3 tools/gba/maps/celadon_elements/services_native.py

What the building holds is the story's (DESIGN.md "The Market", KANTO_ITEMS.md "Celadon
services"): the old store "does services now", no shelves of stock (the stalls outside sell
the items). Four floors, HGSS's directory read as services:

    1F  the service counter: the lobby round FireRed's own Celadon store service-counter island,
        a directory board, a drinks corner, a lounge
    2F  Daisy Oak's salon: reception, grooming tables with stools, a wash station, product
        shelves, a waiting sofa
    3F  the move tutor: a classroom (Rustboro's Pokemon School: blackboard on its stage, the
        tutor's desk, desks in rows, windows), a bookcase
    4F  EV training: a training hall on Saffron Dojo mats, Trainer Tower's terminal, a stats
        screen on the wall, water machines, benches

    shell   the apartments' (apartments_native.py): Lilycove Museum's cream walls and pillars,
            FireRed's Celadon store's orange tile (HGSS's store floor) in every floor's hall
    core    a hall along the west of every floor: the elevator (Lilycove's) between the two
            flights' spots, the flights alternating floor to floor as in the apartments
            (1F up west; 2F down west, up east; 3F down east, up west; 4F down west)

Writes gba/art/celadon-elements/evidence/services/native-*.png and native.png.
"""
from __future__ import annotations
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import apartments_native as A

EV = A.C.ROOT / 'gba/art/celadon-elements/evidence/services'
W, H = 28, 16
P, LIFT, Q = 1, 6, 11                         # the west flight, the elevator, the east flight (each 3 wide)
CORE = 13                                     # the hall's east edge; the services' wall at x 14
STAIRS = {1: (None, P), 2: (P, Q), 3: (Q, P), 4: (P, None)}

for k, n in dict(C1='CeladonCity_DepartmentStore_1F', C2='CeladonCity_DepartmentStore_2F', C3='CeladonCity_DepartmentStore_3F',
                 SC='RustboroCity_PokemonSchool', DJ='SaffronCity_Dojo', TT='TrainerTower_Lobby',
                 D5='LilycoveCity_DepartmentStore_5F').items():
    if k not in A.SRC:
        A.source(k, n)
A.WALL_ROWS.update(C1=(0, 1, 4), C2=(0, 1, 4), C3=(0, 1, 4), SC=(0, 1), DJ=(1, 2), TT=(7, 8), D5=(0, 1))
A.FLOORS.update(
    orange=[('C2', 4, 6), ('C2', 5, 6), ('C2', 4, 7), ('C2', 5, 7)],         # FireRed's Celadon store tile
    school=[('SC', 6, 6), ('SC', 7, 6), ('SC', 6, 7), ('SC', 7, 7)],         # Rustboro's Pokemon School
    dojo=[('DJ', 2, 8), ('DJ', 3, 8), ('DJ', 2, 9), ('DJ', 3, 9)],           # Saffron Dojo's boards
    polka=[('D5', 12, 4), ('D5', 13, 4), ('D5', 12, 5), ('D5', 13, 5)])      # Lilycove store 5F
A.PIECES.update({
    # FireRed's Celadon Dept Store
    'fr_island':  ('C1', 2, 7, 9, 6, 'floor'),     # the service counter on its yellow carpet
    'fr_board':   ('C1', 8, 0, 2, 2, 'wall'),      # the notice board
    'fr_vending': ('C1', 11, 4, 2, 2, 'floor'),
    'fr_plant':   ('C1', 0, 6, 1, 2, 'floor'),
    'fr_counter': ('C2', 0, 4, 3, 6, 'floor', 9),  # the L-shaped service counter with its register
    'fr_shelf':   ('C2', 10, 4, 3, 2, 'floor', 6), # wall shelves of bottles
    'fr_glass':   ('C2', 1, 10, 3, 2, 'floor'),    # a glass-topped table
    'fr_tvdesk':  ('C3', 1, 7, 3, 2, 'floor'),     # a counter with a computer and a screen
    'fr_stool':   ('C3', 1, 9, 1, 1, 'floor'),
    # Rustboro's Pokemon School
    'sc_board':   ('SC', 4, 0, 4, 3, 'wall'),      # the blackboard on its stage
    'sc_window':  ('SC', 1, 0, 2, 2, 'wall'),
    'sc_desk':    ('SC', 1, 5, 1, 2, 'floor'),     # a desk and its chair
    'sc_teacher': ('SC', 5, 4, 2, 1, 'floor'),
    # Saffron Dojo, Trainer Tower, Lilycove store 5F, Brendan's house
    'dj_mat':     ('DJ', 4, 7, 5, 5, 'floor'),
    'dj_scroll':  ('DJ', 5, 1, 1, 2, 'wall'),
    'tt_monitor': ('TT', 4, 7, 2, 2, 'wall'),
    'tt_terminal': ('TT', 8, 9, 1, 2, 'floor'),
    'd5_heart':   ('D5', 8, 0, 2, 2, 'wall'),
    'sink':       ('B1', 1, 0, 2, 3, 'wall', 17),
})
A.RUGS.update({'fr_island'})
# pixel boxes (y0, y1, x0, x1) of FireRed's store and Trainer Tower behind the pieces: the store's
# raised carpet behind its counter, the tower's red counter under its terminal
A.CLEAR.update(fr_counter=[(0, 24, 0, 32), (0, 11, 32, 48)], tt_terminal=[(0, 11, 0, 16), (30, 32, 0, 16)])

class Plan(A.Plan):
    def __init__(self, h=H):
        self.W, self.H = W, h
        self.floor = np.full((h, W), '', '<U8')
        self.ns, self.ew, self.doors, self.sills = [], [], {}, set()

def core(r, floor):
    down, up = STAIRS[floor]
    r.piece('elevator', LIFT, 0)
    for x, kind, where in ((down, 'stairs_down', 'down'), (up, 'stairs_up', 'up')):
        if x is not None:
            r.piece(kind, x, 0)
            r.warp(x + 1, 1, 'MB_NON_ANIMATED_DOOR', where)
    r.warp(LIFT + 1, 1, 'MB_NON_ANIMATED_DOOR', 'lift'); r.warp(LIFT + 2, 1, 'MB_NON_ANIMATED_DOOR', 'lift')
    spare = [x for x in (P, Q) if x not in (down, up)]
    for x in spare:                                     # the flight a floor does not have: its notice board
        r.piece('fr_board', x, 0)

def hall(p, style):
    """The west hall in the store's tile, the service on the east behind its wall."""
    p.room(0, 2, CORE, H - 2, 'orange')
    p.room(CORE + 2, 2, W - 1, H - 2, style)
    p.ns += [(CORE + 1, 2, H - 2)]

def lobby():
    p = Plan()
    p.room(0, 2, W - 1, H - 2, 'orange')
    r = A.Room(p)
    core(r, 1)
    # the service counter in the middle of the hall, the street door below it
    r.piece('fr_island', 10, 5)
    r.piece('mat', 14, 14, solid=False)
    r.warp(14, 14, 'MB_SOUTH_ARROW_WARP', 'street'); r.warp(15, 14, 'MB_SOUTH_ARROW_WARP', 'street')
    r.warps = r.warps[-2:] + r.warps[:-2]
    # the east wall: paintings, the drinks corner; a lounge before them
    r.piece('painting_b', 17, 0); r.piece('painting_d', 21, 0)
    r.piece('fr_vending', 25, 1)
    r.piece('sofa_fr', 21, 7); r.piece('table_w', 22, 10)
    r.piece('armchair_l', 20, 9); r.piece('armchair_r', 25, 9)
    r.piece('fr_plant', 27, 7); r.piece('fr_plant', 27, 12)
    # the west side: the museum's bench on its rug between planters
    r.piece('bench', 2, 9)
    r.piece('planter', 0, 4); r.piece('planter', 0, 12)
    # plants either side of the door
    r.piece('fr_plant', 12, 12); r.piece('fr_plant', 17, 12)
    return r

def salon():
    p = Plan()
    hall(p, 'polka')
    p.door_ns(CORE + 1, 8, 'polka')
    r = A.Room(p)
    core(r, 2)
    # the hall is the salon's front: reception under the heart, product cases, the waiting sofa
    r.piece('d5_heart', 4, 0)
    r.piece('fr_counter', 2, 5)
    r.piece('glass_case', 12, 3); r.piece('glass_case', 12, 5)
    r.piece('sofa_fr', 6, 10); r.piece('table_w', 7, 13)
    r.piece('fr_plant', 0, 12); r.piece('fr_plant', CORE, 12)
    # the salon: wash stations and shelves on the wall, two rows of grooming tables with stools
    r.piece('sink', 16, 0); r.piece('fr_shelf', 20, 1); r.piece('sink', 25, 0); r.piece('fr_plant', 27, 2)
    for y in (5, 10):
        for x in (17, 21, 25):
            r.piece('table_w', x, y); r.piece('fr_stool', x + 1, y + 2)
    return r

def tutor():
    p = Plan()
    hall(p, 'school')
    p.door_ns(CORE + 1, 10, 'school')
    r = A.Room(p)
    core(r, 3)
    # the hall: bookcases between the flights and the elevator, benches to wait on
    r.piece('books_fc', 4, 0); r.piece('books_fc', 9, 0)
    r.piece('r_bench', 2, 6); r.piece('r_bench', 2, 9); r.piece('r_bench', 8, 6); r.piece('r_bench', 8, 9)
    r.piece('fr_plant', 0, 12); r.piece('fr_plant', CORE, 12)
    # the classroom: windows either side of the blackboard, the tutor's desk before it, desks in rows
    r.piece('sc_window', 16, 0); r.piece('sc_board', 19, 0); r.piece('sc_window', 24, 0)
    r.piece('books_lo', 26, 0)
    r.piece('sc_teacher', 20, 4)
    for y in (7, 10):
        for x in (17, 20, 23):
            r.piece('sc_desk', x, y)
    return r

def training():
    p = Plan()
    hall(p, 'dojo')
    p.door_ns(CORE + 1, 8, 'dojo')
    r = A.Room(p)
    core(r, 4)
    # the hall: the front desk under the stats screen, the terminal, benches
    r.piece('tt_monitor', 4, 0)
    r.piece('fr_tvdesk', 3, 4); r.piece('tt_terminal', 9, 4)
    r.piece('r_bench', 3, 9); r.piece('r_bench', 8, 9)
    r.piece('fr_plant', 0, 12); r.piece('fr_plant', CORE, 12)
    # the training hall: two mats, scrolls and the water machines on the wall, benches
    r.piece('dj_scroll', 18, 0); r.piece('dj_scroll', 21, 0); r.piece('dj_scroll', 24, 0); r.piece('r_vending', 26, 0)
    r.piece('dj_mat', 16, 5); r.piece('dj_mat', 22, 5)
    r.piece('r_bench', 17, 12); r.piece('r_bench', 23, 12)
    return r

def main():
    EV.mkdir(parents=True, exist_ok=True)
    out = []
    F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)
    for key, title, fn in (('1f', '1F  Service counter', lobby), ('2f', "2F  Daisy Oak's salon", salon),
                           ('3f', '3F  Move tutor', tutor), ('4f', '4F  EV training', training)):
        r = fn()
        img = r.png()
        Image.fromarray(img).save(EV / f'native-{key}.png')
        out.append((title, img))
    tiles = []
    for title, a in out:
        im = Image.fromarray(a).resize((a.shape[1] * 2, a.shape[0] * 2), Image.NEAREST)
        t = Image.new('RGB', (im.width + 24, im.height + 52), (24, 27, 36))
        ImageDraw.Draw(t).text((12, 12), title, font=F, fill=(255, 255, 255)); t.paste(im, (12, 42))
        tiles.append(t)
    sheet = Image.new('RGB', (max(t.width for t in tiles), sum(t.height for t in tiles)), (24, 27, 36)); y = 0
    for t in tiles:
        sheet.paste(t, (0, y)); y += t.height
    sheet.save(EV / 'native.png')

if __name__ == '__main__':
    main()
