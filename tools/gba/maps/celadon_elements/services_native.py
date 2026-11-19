"""The market's services building (HGSS's Celadon Dept Store), designed from scratch in Gen 3's own
pieces with HGSS's colours (owner, 2026-11-11: "Build it from scratch using as much gen 3 stuff
with gen 4 style and color as you can, just like you did the apartments"; round 2, 2026-11-11:
too bare, pieces placed at random or off the floor's vibe, a heart on the wall nobody knows,
the chalkboard broken: map out a real floor plan, think about what each floor holds, more going
on).

    python3 tools/gba/maps/celadon_elements/services_native.py

What the building holds is the story's (DESIGN.md "The Market", KANTO_ITEMS.md "Celadon
services"): the old store does services now, the stalls outside sell the items. HGSS's store is
the colour: its orange tile on the lower floors, its cream tile up top. Every floor keeps the
same core on its north wall (the elevator, the two flights' spots, the flights alternating floor
to floor as in the apartments). Each service room wears the Gen 3 room it comes from, walls and
floor, so its wall pieces sit in their own wall whole (the school's blackboard is the school's
own wall).

    1F  Front desk and lounge (open floor, the store's orange tile)
        the service counter island in the middle (FireRed's Celadon store), the directory board
        by the elevator; west, the waiting lounge (Saffron fan club's sofa set on its rug, fish
        tanks, a magazine shelf); east, the drinks corner (vending machines, Pokemon Center
        cafe tables and stools); the storage PC on the wall; plants by the street door
    2F  Daisy Oak's salon
        west, the front of house in the store's tile: reception desk with its register (Pretty
        Petal's counter), the retail shelf and display cases of grooming goods, the Pokeblock
        bar (Lilycove contest lobby's berry blenders: condition is what the salon sells), the
        waiting area (Vermilion fan club's sofa set on its rug); east, the grooming room in
        Pretty Petal's walls and floor: five grooming tables (Pokemon Center's), shampoo racks
        and flowers along the wall, fish tanks
    3F  Move tutor
        west, the study hall: move reference terminals (Cinnabar lab's desks), the reading table
        on its rug (Cinnabar lab's lounge), Oak's lab's shelves; east, the classroom: Rustboro's
        Pokemon School as it is, its wall with the blackboard, the stage and the tutor's desk,
        four rows of desks
    4F  EV training
        west, the stats lab in HGSS's upper-floor cream (Pokemon Center tile): front desk, the
        stat scanner (Cinnabar lab's capsule), stat readers (the Frontier Ranking Hall's
        consoles), a lab desk, benches, water machines; east, the gym in Saffron Dojo's walls
        and floor: two sparring mats, a tire stack and an agility lane of jump and spin mats
        (secret base decorations), bleachers

    people  the preview draws the floors' people and Pokemon (overworld sprites) where their
            object events will stand; they are not part of the tiles

Writes gba/art/celadon-elements/evidence/services/native-*.png, native.png and
native-pieces.png (every piece cut on its own).
"""
from __future__ import annotations
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import apartments_native as A

EV = A.C.ROOT / 'gba/art/celadon-elements/evidence/services'
GFX = A.ENG / 'graphics'
W, H = 28, 16
P, LIFT, Q = 1, 6, 11                         # the west flight, the elevator, the east flight (each 3 wide)
CORE = 13                                     # the hall's east edge; the service room's wall at x 14
ROOM = 15                                     # the service room's first column
STAIRS = {1: (None, P), 2: (P, Q), 3: (Q, P), 4: (P, None)}

for k, n in dict(C1='CeladonCity_DepartmentStore_1F', C2='CeladonCity_DepartmentStore_2F', C3='CeladonCity_DepartmentStore_3F',
                 SC='RustboroCity_PokemonSchool', DJ='SaffronCity_Dojo', PC1='PokemonCenter_1F', PC2='PokemonCenter_2F',
                 FS='Route104_PrettyPetalFlowerShop', VF='VermilionCity_PokemonFanClub', SF='SaffronCity_PokemonTrainerFanClub',
                 CL='LilycoveCity_ContestLobby', LG='CinnabarIsland_PokemonLab_Lounge', EX='CinnabarIsland_PokemonLab_ExperimentRoom',
                 OK='PalletTown_ProfessorOaksLab', RH='BattleFrontier_RankingHall').items():
    if k not in A.SRC:
        A.source(k, n)

# the secret base's decorations (Emerald): no room lays them out, so a strip of their metatiles
# on the secret base's ground stands in as their source room
SB_GROUND = 0x20A
SB_GRID = [
    [0x280, 0x281, SB_GROUND, 0x261, 0x262, 0x260, SB_GROUND, 0x26A, 0x26B, 0x26C, 0x26D, SB_GROUND],
    [0x288, 0x289, SB_GROUND, SB_GROUND, SB_GROUND, SB_GROUND, SB_GROUND, 0x272, 0x273, 0x274, 0x275, SB_GROUND],
    [SB_GROUND] * 12,
    [0x330, 0x331, 0x333, 0x334, 0x31E, 0x31F, SB_GROUND, SB_GROUND, SB_GROUND, SB_GROUND, SB_GROUND, SB_GROUND],
    [SB_GROUND] * 12]

def _sb():
    import os
    d = A.C.ROOT.parent / 'pokeemerald-expansion/data/tilesets/secondary/secret_base'
    import tempfile
    from pathlib import Path
    tmp = Path(tempfile.gettempdir()) / 'apoc_secret_base_red_cave'   # the red cave's tiles and palettes with the shared metatiles
    tmp.mkdir(parents=True, exist_ok=True)
    for name, src in (('tiles.png', d / 'red_cave/tiles.png'), ('palettes', d / 'red_cave/palettes'),
                      ('metatiles.bin', d / 'metatiles.bin'), ('metatile_attributes.bin', d / 'metatile_attributes.bin')):
        if not (tmp / name).exists():
            os.symlink(src, tmp / name)
    pair = A.EPair(A.folder('gTileset_SecretBase'), str(tmp))
    A.SRC['SB'] = (pair, np.array(SB_GRID), 'SecretBase_Decorations')
if 'SB' not in A.SRC:
    _sb()

A.WALL_ROWS.update(C1=(0, 1, 4), C2=(0, 1, 4), C3=(0, 1, 4), SC=(0, 1), DJ=(1, 2), PC1=(0, 1), PC2=(0, 1), FS=(0, 1),
                   VF=(0, 1, 2), SF=(0, 1, 2), CL=(0, 1), LG=(0, 1, 2), EX=(0, 1, 2), OK=(0, 1), RH=(), SB=())
A.FLOORS.update(
    orange=[('C2', 4, 6), ('C2', 5, 6), ('C2', 4, 7), ('C2', 5, 7)],         # FireRed's Celadon store tile (HGSS 1F-3F)
    cream=[('PC1', 2, 5), ('PC1', 3, 5), ('PC1', 2, 6), ('PC1', 3, 6)],      # the Pokemon Center's tile (HGSS 4F-5F)
    school=[('SC', 6, 6), ('SC', 7, 6), ('SC', 6, 7), ('SC', 7, 7)],         # Rustboro's Pokemon School
    dojo=[('DJ', 2, 8), ('DJ', 3, 8), ('DJ', 2, 9), ('DJ', 3, 9)],           # Saffron Dojo's boards
    petal=[('FS', 3, 5), ('FS', 4, 5), ('FS', 3, 6), ('FS', 4, 6)])          # Pretty Petal's tile

# each service room's own north wall: (source, its rows for the wall's two rows, its plain columns)
WALLS = dict(petal=('FS', (0, 1), (3, 4)), school=('SC', (0, 1), None), dojo=('DJ', (1, 2), (2, 3)))

A.PIECES.update({
    # FireRed's Celadon Dept Store
    'fr_island':  ('C1', 2, 7, 9, 6, 'floor'),     # the service counter on its yellow carpet
    'fr_board':   ('C1', 8, 0, 2, 2, 'wall'),      # the directory board
    'fr_vending': ('C1', 11, 4, 2, 2, 'floor'),
    'fr_plant':   ('C1', 0, 6, 1, 2, 'floor'),
    'fr_shelf':   ('C2', 10, 4, 3, 2, 'floor', 6), # a shelf of bottles
    'fr_tvdesk':  ('C3', 1, 7, 3, 2, 'floor'),     # a counter with a computer and a screen
    # the Pokemon Centers (Emerald)
    'pc_pc':      ('PC1', 10, 0, 1, 3, 'wall'),    # the storage PC
    'pc_shelf':   ('PC1', 2, 1, 2, 2, 'wall'),     # the magazine shelf
    'pc_table':   ('PC1', 11, 6, 2, 2, 'floor'),   # the round glass table
    'pc_stool_r': ('PC1', 1, 3, 1, 1, 'floor'), 'pc_stool_y': ('PC1', 2, 3, 1, 1, 'floor'),
    'pc_stool_p': ('PC2', 8, 9, 1, 1, 'floor'),
    # Pretty Petal (Emerald)
    'fs_counter': ('FS', 1, 2, 2, 3, 'floor'),     # the shop counter with its register
    'fs_rack':    ('FS', 6, 1, 3, 2, 'wall'),      # the wire rack of pots and bottles
    'fs_vase':    ('FS', 2, 1, 1, 2, 'wall'),      # flowers in a vase against the wall
    'fs_box':     ('FS', 5, 5, 1, 3, 'floor'),     # a flower box
    'fs_beds':    ('FS', 10, 1, 4, 2, 'wall'),     # flower beds along the wall
    # the fan clubs (FireRed)
    'sf_lounge':  ('SF', 2, 3, 7, 5, 'floor'),     # the sofa set on its rug
    'sf_tank':    ('SF', 10, 4, 1, 2, 'floor'),    # a fish tank
    'vf_lounge':  ('VF', 2, 3, 8, 6, 'floor'),     # the armchair set on its rug
    'vf_books':   ('VF', 4, 0, 2, 3, 'wall'),
    # Lilycove contest lobby (Emerald): the berry blender
    'cl_blender': ('CL', 23, 4, 1, 2, 'floor'),
    # Cinnabar lab (FireRed)
    'lg_table':   ('LG', 4, 3, 7, 6, 'floor'),     # the reading table and its chairs on the rug
    'lg_case':    ('LG', 1, 0, 2, 3, 'wall'),      # the glass-fronted case
    'lg_books':   ('LG', 3, 0, 2, 3, 'wall'),
    'ex_desk':    ('EX', 2, 3, 3, 2, 'floor'),     # a lab desk with its computer
    'ex_stool':   ('EX', 3, 5, 1, 1, 'floor'),
    'ex_capsule': ('EX', 12, 0, 2, 3, 'wall'),     # the capsule machine
    'ex_shelf':   ('EX', 3, 0, 2, 3, 'wall'),
    # Oak's lab (FireRed)
    'ok_shelf':   ('OK', 1, 8, 2, 2, 'floor'),     # a free-standing shelf
    'ok_books':   ('OK', 9, 0, 2, 3, 'wall'),
    # the Frontier's Ranking Hall (Emerald)
    'rh_console': ('RH', 8, 6, 1, 2, 'floor'),     # a reader console
    'rh_chair':   ('RH', 3, 7, 1, 2, 'floor'),
    # the classroom: Rustboro's Pokemon School
    'sc_stage':   ('SC', 4, 2, 4, 1, 'floor'),     # the stage under the blackboard
    'sc_desk':    ('SC', 1, 5, 1, 2, 'floor'),     # a desk and its chair
    'sc_teacher': ('SC', 5, 4, 2, 1, 'floor'),
    # Saffron Dojo
    'dj_mat':     ('DJ', 4, 7, 5, 5, 'floor'),
    # the secret base's decorations
    'sb_tire':    ('SB', 0, 0, 2, 2, 'floor'),
    'sb_jump':    ('SB', 3, 0, 1, 1, 'floor'), 'sb_spin': ('SB', 4, 0, 1, 1, 'floor'),
    'sb_stand':   ('SB', 7, 0, 4, 2, 'floor'),     # bleachers
    'sb_ball':    ('SB', 0, 3, 1, 1, 'floor'), 'sb_green': ('SB', 1, 3, 1, 1, 'floor'),
    'sb_blue':    ('SB', 2, 3, 1, 1, 'floor'), 'sb_cute': ('SB', 3, 3, 1, 1, 'floor'),
    'sb_long':    ('SB', 4, 3, 2, 1, 'floor'),
})
A.RUGS.update({'fr_island', 'sf_lounge', 'vf_lounge', 'lg_table'})
# pixel boxes (y0, y1, x0, x1) of the source rooms behind the pieces
A.CLEAR.update(pc_pc=[(34, 48, 0, 16)], pc_shelf=[(25, 32, 0, 32)], fs_counter=[(0, 14, 16, 32)])

class Plan(A.Plan):
    def __init__(self, h=H):
        self.W, self.H = W, h
        self.floor = np.full((h, W), '', '<U8')
        self.ns, self.ew, self.doors, self.sills = [], [], {}, set()

def wall_from(r, style, x0, x1):
    """The north wall over x0..x1 in a service room's own wall (WALLS): its plain columns
    repeated, or (no plain columns) the source's wall itself from its first column."""
    src, rows, plain = WALLS[style]
    for x in range(x0, x1 + 1):
        sx = (plain[(x - x0) % len(plain)] if plain else x - x0)
        for y, sy in enumerate(rows):
            r.img[y * 16:(y + 1) * 16, x * 16:(x + 1) * 16] = A.flat(src, sx, sy)
    r.base = r.img.copy()

def whole(r, src, sx, sy, w, h, x, y):
    """Cells copied whole from their own room (a wall piece in its own wall)."""
    for yy in range(h):
        for xx in range(w):
            r.img[(y + yy) * 16:(y + yy + 1) * 16, (x + xx) * 16:(x + xx + 1) * 16] = A.flat(src, sx + xx, sy + yy)
    r.base = r.img.copy()

def core(r, floor, spare=None):
    down, up = STAIRS[floor]
    r.piece('elevator', LIFT, 0)
    for x, kind, where in ((down, 'stairs_down', 'down'), (up, 'stairs_up', 'up')):
        if x is not None:
            r.piece(kind, x, 0)
            r.warp(x + 1, 1, 'MB_NON_ANIMATED_DOOR', where)
    r.warp(LIFT + 1, 1, 'MB_NON_ANIMATED_DOOR', 'lift'); r.warp(LIFT + 2, 1, 'MB_NON_ANIMATED_DOOR', 'lift')

def hall(p, style, door_y, hall_style='orange'):
    """The west hall in the store's tile, the service room on the east behind its wall."""
    p.room(0, 2, CORE, H - 2, hall_style)
    p.room(ROOM, 2, W - 1, H - 2, style)
    p.ns += [(CORE + 1, 2, H - 2)]
    p.door_ns(CORE + 1, door_y, style)

# --------------------------------------------------------------------------- people
PEOPLE = GFX / 'object_events/pics/people'
MONS = GFX / 'pokemon'
FACING = dict(down=0, up=1, left=2, right=2)
MON_FACING = dict(down=0, up=2, left=4, right=4)

def sprite(name, facing='down'):
    """An overworld sprite's standing frame as RGBA (index 0 clear)."""
    if (PEOPLE / f'{name}.png').exists():
        im = Image.open(PEOPLE / f'{name}.png'); fw = 32 if im.width >= 288 else 16
        f = FACING[facing]
    else:
        im = Image.open(MONS / name / 'overworld.png'); fw = im.height
        f = MON_FACING[facing]
    idx = np.array(im)[:, f * fw:(f + 1) * fw]
    raw = (im.getpalette() or []) + [0] * 48
    pal = np.array(raw[:48], np.uint8).reshape(16, 3)
    palf = MONS / name / 'overworld_normal.pal'
    if palf.exists():                                       # a Pokemon's own overworld palette
        pal = np.array([list(map(int, l.split())) for l in palf.read_text().splitlines()[3:19]], np.uint8)
    out = np.zeros(idx.shape + (4,), np.uint8)
    out[..., :3] = pal[idx % 16]; out[..., 3] = np.where(idx % 16 == 0, 0, 255)
    if facing == 'right':
        out = out[:, ::-1]
    return out
BIG = set()

def people(r, who):
    """Draws (name, x, y, facing) on the room's preview: feet on the square's bottom edge."""
    img = r.img
    for name, x, y, facing in sorted(who, key=lambda t: t[2]):
        s = sprite(name, facing)
        h, w = s.shape[:2]
        y1 = (y + 1) * 16; x0 = x * 16 + 8 - w // 2
        y0 = y1 - h
        sy0 = max(0, -y0); y0 = max(0, y0)
        sx0 = max(0, -x0); x0 = max(0, x0); x1 = min(img.shape[1], x * 16 + 8 - w // 2 + w)
        dst = img[y0:y1, x0:x1]; src = s[sy0:, sx0:sx0 + (x1 - x0)]
        a = src[..., 3] > 0
        dst[a] = src[..., :3][a]

# --------------------------------------------------------------------------- the floors
def lobby():
    p = Plan()
    p.room(0, 2, W - 1, H - 2, 'orange')
    r = A.Room(p)
    core(r, 1)
    r.piece('fr_board', 4, 0)                                     # the directory, by the elevator
    r.piece('pc_pc', 9, 0)                                        # the storage PC
    r.piece('lg_case', Q, 0); r.piece('fr_plant', Q + 2, 2)       # no flight here: a display case
    # the street door, plants either side
    r.piece('mat', 13, 14, solid=False)
    r.warp(13, 14, 'MB_SOUTH_ARROW_WARP', 'street'); r.warp(14, 14, 'MB_SOUTH_ARROW_WARP', 'street')
    r.warps = r.warps[-2:] + r.warps[:-2]
    r.piece('fr_plant', 11, 12); r.piece('fr_plant', 16, 12)
    # the service counter in the middle of the floor
    r.piece('fr_island', 9, 4)
    # west: the waiting lounge (the sofa set on its rug), fish tanks, the magazine shelf
    r.piece('pc_shelf', 0, 1)
    r.piece('sf_lounge', 1, 8)
    r.piece('sf_tank', 0, 4); r.piece('sf_tank', 0, 6)
    r.piece('fr_plant', 0, 12); r.piece('fr_plant', 7, 3)
    # east: the drinks corner (machines on the wall, cafe tables with stools), paintings
    r.piece('painting_b', 15, 0); r.piece('painting_d', 18, 0)
    r.piece('r_vending', 22, 0); r.piece('fr_vending', 24, 1); r.piece('fr_plant', 27, 2)
    for x, y in ((20, 6), (24, 6), (22, 10)):
        r.piece('pc_table', x, y); r.piece('pc_stool_r', x - 1, y + 1); r.piece('pc_stool_y', x + 2, y + 1)
    r.piece('fr_plant', 27, 12); r.piece('planter', 18, 12)
    people(r, [('mart_employee', 13, 7, 'down'), ('woman_2', 13, 10, 'up'), ('meowth', 12, 11, 'up'),
               ('old_man', 3, 9, 'down'), ('lass', 6, 10, 'left'), ('pikachu', 5, 12, 'up'),
               ('man_1', 19, 7, 'right'), ('woman_5', 26, 7, 'left'), ('boy_1', 24, 3, 'up'),
               ('gentleman', 10, 2, 'up'), ('twin', 15, 13, 'up')])
    return r

def salon():
    p = Plan()
    hall(p, 'petal', 8)
    r = A.Room(p)
    wall_from(r, 'petal', ROOM, W - 1)
    core(r, 2)
    r.piece('sb_cute', 4, 1); r.piece('sb_cute', 9, 1)
    # front of house: reception with its register by the stairs, the retail shelves and cases
    # of grooming goods on the west wall, the Pokeblock bar, the waiting area on its rug
    r.piece('fs_counter', 3, 3); r.piece('pc_stool_p', 2, 4)
    r.piece('fr_shelf', 0, 7); r.piece('glass_case', 0, 10); r.piece('glass_case', 1, 10)
    r.piece('cl_blender', 9, 3); r.piece('cl_blender', 11, 3); r.piece('pc_stool_p', 9, 6); r.piece('pc_stool_p', 11, 6)
    r.piece('vf_lounge', 4, 8)
    r.piece('fr_plant', 0, 12); r.piece('fr_plant', CORE, 12)
    # the grooming room: racks of shampoos and flower beds along the wall, fish tanks, five
    # grooming tables, flowers by the door
    r.piece('fs_rack', 16, 0); r.piece('fs_beds', 20, 0); r.piece('fs_rack', 24, 0)
    r.piece('sf_tank', 27, 4); r.piece('sf_tank', 27, 6)
    for x, y in ((16, 4), (20, 4), (24, 4), (18, 9), (22, 9)):
        r.piece('pc_table', x, y)
    r.piece('fs_box', ROOM, 10); r.piece('fs_box', 27, 10); r.piece('fs_vase', 27, 12)
    people(r, [('nurse', 2, 3, 'down'), ('daisy', 21, 6, 'up'), ('eevee', 21, 5, 'down'),
               ('woman_3', 17, 6, 'up'), ('skitty', 17, 5, 'down'), ('woman_1', 25, 6, 'up'), ('poochyena', 25, 5, 'down'),
               ('worker_f', 19, 11, 'up'), ('azurill', 19, 10, 'down'),
               ('beauty', 6, 10, 'right'), ('clefairy', 6, 13, 'up'), ('girl_2', 10, 7, 'up'), ('rich_boy', 1, 9, 'left')])
    return r

def tutor():
    p = Plan()
    hall(p, 'school', 9)
    r = A.Room(p)
    wall_from(r, 'school', ROOM + 1, ROOM + 12)                   # the school's wall, its blackboard in the middle
    whole(r, 'SC', 0, 0, 1, 2, ROOM, 0)
    core(r, 3)
    r.piece('ok_books', 4, 0); r.piece('ok_books', 9, 0)
    # the study hall: move reference terminals, the reading table on its rug, shelves
    r.piece('ex_desk', 0, 4); r.piece('ex_stool', 1, 6)
    r.piece('ex_desk', 0, 8); r.piece('ex_stool', 1, 10)
    r.piece('lg_table', 5, 4)
    r.piece('ok_shelf', 5, 12); r.piece('ok_shelf', 8, 12)
    r.piece('fr_plant', 0, 12); r.piece('fr_plant', CORE, 12)
    # the classroom: the stage under the blackboard, the tutor's desk, four rows of desks
    S0 = ROOM + 1                                                 # the school's own column 0
    r.piece('sc_stage', S0 + 4, 2)
    r.piece('sc_teacher', S0 + 5, 4)
    for y in (6, 9, 12):
        for x in (S0 + 1, S0 + 3, S0 + 8, S0 + 10):
            r.piece('sc_desk', x, y)
    r.piece('fr_plant', ROOM, 12); r.piece('fr_plant', W - 1, 12)
    people(r, [('expert_m', S0 + 6, 3, 'down'), ('school_kid_m', S0 + 1, 8, 'up'), ('lass', S0 + 3, 8, 'up'),
               ('youngster', S0 + 8, 8, 'up'), ('picnicker', S0 + 10, 11, 'up'), ('psyduck', S0 + 11, 11, 'up'),
               ('scientist', 1, 5, 'up'), ('hex_maniac', 1, 9, 'up'), ('camper', 5, 6, 'right'),
               ('cooltrainer_f', 11, 7, 'left'), ('clerk', 12, 10, 'down')])
    return r

def training():
    p = Plan()
    hall(p, 'dojo', 8, 'cream')
    r = A.Room(p)
    wall_from(r, 'dojo', ROOM, W - 1)
    core(r, 4)
    # the stats lab: the front desk by the stairs, the stat scanner in the spare flight's spot,
    # reader consoles beside it, a lab desk, the water machines, benches
    r.piece('r_vending', 4, 0)
    r.piece('ex_capsule', Q, 0)
    r.piece('fr_tvdesk', 2, 4)
    r.piece('rh_console', 9, 4); r.piece('rh_console', 11, 4)
    r.piece('ex_desk', 9, 8); r.piece('ex_stool', 10, 10)
    r.piece('r_bench', 2, 9); r.piece('r_bench', 2, 12); r.piece('rh_chair', 6, 9); r.piece('rh_chair', 6, 12)
    r.piece('fr_plant', 0, 3); r.piece('fr_plant', CORE, 12)
    # the gym: two sparring mats, the tire stack, an agility lane of jump and spin mats, bleachers
    r.piece('dj_mat', ROOM + 1, 3); r.piece('dj_mat', ROOM + 7, 3)
    r.piece('sb_tire', ROOM + 1, 10); r.piece('sb_tire', ROOM + 3, 10)
    for i, x in enumerate(range(ROOM + 6, ROOM + 12)):
        r.piece('sb_jump' if i % 2 == 0 else 'sb_spin', x, 12, solid=False)
    r.piece('sb_stand', ROOM + 7, 9)
    r.piece('r_vending', W - 2, 0)
    people(r, [('cooltrainer_m', 3, 3, 'down'), ('scientist', 12, 4, 'down'), ('trainer_tower_dude', 11, 3, 'down'),
               ('youngster', 10, 7, 'up'), ('black_belt', ROOM + 2, 5, 'right'), ('machop', ROOM + 4, 5, 'left'),
               ('cooltrainer_f', ROOM + 8, 6, 'right'), ('growlithe', ROOM + 10, 6, 'left'),
               ('rocker', ROOM + 2, 12, 'up'), ('ponyta', ROOM + 8, 12, 'right'), ('camper', ROOM + 6, 13, 'right'),
               ('man_2', 3, 11, 'down')])
    return r

def piece_sheet(names):
    F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
    tiles = []
    for name in names:
        src, sx, sy, w, h = A.PIECES[name][:5]
        im = Image.fromarray(np.clip(A.piece_pixels(name), 0, 255).astype(np.uint8)).convert('RGBA')
        m = A.piece_mask(name); a = np.array(im); a[..., 3] = m * 255; im = Image.fromarray(a)
        im = im.resize((w * 32, h * 32), Image.NEAREST)
        t = Image.new('RGB', (max(im.width, 110) + 8, im.height + 22), (70, 80, 100)); d = ImageDraw.Draw(t)
        t.paste(im, (4, 18), im); d.text((4, 2), f'{name} ({src})', font=F, fill=(255, 255, 255))
        tiles.append(t)
    Wd = 1800; rows, row, x = [], [], 0
    for t in tiles:
        if x + t.width > Wd:
            rows.append(row); row, x = [], 0
        row.append(t); x += t.width + 6
    rows.append(row)
    o = Image.new('RGB', (Wd, sum(max(t.height for t in rw) + 6 for rw in rows)), (16, 18, 24)); y = 0
    for rw in rows:
        x = 0
        for t in rw:
            o.paste(t, (x, y)); x += t.width + 6
        y += max(t.height for t in rw) + 6
    o.save(EV / 'native-pieces.png')

NEW = [k for k in A.PIECES if k.split('_')[0] in ('fr', 'pc', 'fs', 'sf', 'vf', 'cl', 'lg', 'ex', 'ok', 'rh', 'sc', 'dj', 'sb')]

def main():
    EV.mkdir(parents=True, exist_ok=True)
    piece_sheet(NEW)
    out = []
    F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)
    for key, title, fn in (('1f', '1F  Front desk and lounge', lobby), ('2f', "2F  Daisy Oak's salon", salon),
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
