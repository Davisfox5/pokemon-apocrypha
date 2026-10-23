"""Cianwood's buildings and props, drawn as Gen 3 pixel art from HGSS's own models.

Each shape and proportion is read from the model drawn through Cianwood's field camera
(camera type 0, 48.7 degrees; hgss_camera.py, evidence/elements/*-reference.png) and
redrawn at native resolution with one-pixel dark outlines and small ramps. Each sprite's
bottom edge sits on the bottom of its object's lowest blocked cell, and every building's
door is in its second cell from the left, as in HGSS.

    python3 tools/gba/maps/cianwood_elements/sprites.py   # writes source/elements/sprites.png

Models: houses 102 + door 103 (scaled 0.89 so the 74 px model fits four cells), the
pharmacy 104, Cameron's photo studio 105 with its poster board, the Gym 108 + door 16
(Blackthorn's Gym model with Cianwood's red bands and grey emblem slab, scaled 0.95),
the herb drying racks 106, Cameron's camera 90, and the sea rocks (terrain), drawn in
Cherrygrove's accepted sea-rock colours.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = ROOT / 'gba/art/cianwood-elements/source/elements'

def canvas(w, h):
    return np.zeros((h, w, 4), np.uint8)

def rect(img, x0, y0, x1, y1, c):
    img[max(0, y0):y1, max(0, x0):x1] = tuple(c[:3]) + (255,)

def outline(img, c):
    """One-pixel outline along the inside edge of the opaque area."""
    a = img[..., 3] > 0
    pad = np.pad(a, 1)
    edge = a & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    img[edge] = tuple(c) + (255,)

def snap(img, palette):
    """Snap every opaque pixel to its nearest palette colour (keeps a sprite's ramp small)."""
    a = img[..., 3] > 0
    p = np.array(palette, float)
    c = img[a][:, :3].astype(float)
    img[a, :3] = p[((c[:, None] - p[None]) ** 2).sum(-1).argmin(1)].astype(np.uint8)

# Neutral greys shared by every building, so one palette bank's worth serves them all.
LINE = (56, 56, 72)
WHITE, PALE, GREY, MID, DARK = (248, 248, 240), (224, 224, 216), (200, 200, 192), (168, 168, 160), (120, 120, 112)
WALL = (88, 100, 80)                                       # the dark green-grey upper wall and corner posts
# Houses and the pharmacy: glass roofs, wood (15 colours with the neutrals: one bank)
GLASS = [(184, 216, 224), (136, 176, 224), (88, 148, 224), (64, 104, 208), (24, 80, 168)]
WOOD = [(248, 192, 120), (216, 160, 96), (148, 108, 88)]
HOUSE_PALETTE = [LINE, WHITE, PALE, GREY, MID, DARK, WALL] + GLASS + WOOD
# The studio: slate roof, awning, poster board (15 with the neutrals). Its teal is the
# herb racks', its board the camera's peach and its frame brown the houses' wood, so the
# town shares palette slots.
SLATE = [(120, 144, 216), (100, 128, 208), (84, 108, 192), (64, 88, 168)]
STUDIO_PALETTE = [LINE, WHITE, PALE, GREY, MID, DARK, WALL] + SLATE + [(128, 232, 200), (248, 224, 120), (248, 184, 144), WOOD[2]]

# --------------------------------------------------------------------------- glass-roof houses
def glass_roof(img, light=False):
    """The houses' gable roof seen from the camera: ridge running front to back, a glass
    plane either side in a grid of panes, white eaves, the grey front gable under the
    ridge's end. Drawn for the left half and mirrored."""
    h, w = img.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w]
    dx = np.abs(xs - 31.5)
    top = 1 + 0.5 * dx
    roof = (dx <= 31.5) & (ys >= top) & (ys <= 42)
    gable = (dx <= 22) & (ys >= 28 + 0.68 * dx) & (ys <= 42)
    plane = roof & ~gable & (dx >= 3)
    put = lambda m, c: img.__setitem__(m, tuple(c) + (255,))
    # panes: 6 px grid from the ridge outward, lighter toward the ridge and the top
    u = np.floor((dx - 3) / 6).astype(int)
    v = np.floor((ys - top) / 6).astype(int)
    shade = np.clip(u // 2 + (v >= 4) + (0 if light else 1), 0, 3)
    for k in range(4):
        put(plane & (shade == k), GLASS[k] if light else GLASS[min(3, k + 0)] if k < 3 else GLASS[3])
    frame = plane & ((((dx - 3) % 6) < 1) | (((ys - top) % 6) < 1))
    put(frame, GLASS[3] if light else GLASS[4])
    glint = plane & (((dx - 3) % 6) >= 1) & (((dx - 3) % 6) < 3) & (((ys - top) % 6) == 1)
    put(glint, GLASS[0])
    # ridge cap
    ridge = roof & (dx < 3) & (ys < 30)
    put(ridge, WHITE); put(ridge & (dx >= 2), PALE)
    for y in range(4, 28, 4):
        img[y, 30:34] = tuple(GREY) + (255,)
    # white eaves along the slopes and down the sides, grey eave under the planes
    put(plane & (ys < top + 2), WHITE)
    put(plane & (ys >= top + 2) & (ys < top + 3), PALE)
    put(plane & (dx > 29.5), WHITE)
    put(plane & (ys >= 40), PALE)
    # front gable: grey siding, white bargeboards, a dark vent
    put(gable, GREY)
    put(gable & ((ys % 3) == 0), MID)
    put(gable & (ys < 30 + 0.68 * dx), WHITE)
    rect(img, 29, 35, 35, 37, LINE)
    img[:, 32:] = img[:, :32][:, ::-1]

def house_front(img, door_dark=True):
    """Wall under the eaves: dark band, white wall, corner posts, door in the second cell,
    window to the right, foundation, blue pots at both corners."""
    rect(img, 3, 43, 61, 72, (255, 255, 255))
    rect(img, 3, 43, 61, 49, WALL); rect(img, 3, 43, 61, 44, DARK)
    rect(img, 3, 49, 61, 68, WHITE); rect(img, 3, 64, 61, 68, GREY)
    rect(img, 3, 43, 8, 72, WALL); rect(img, 56, 43, 61, 72, WALL)
    rect(img, 3, 68, 61, 72, MID); rect(img, 3, 71, 61, 72, DARK)
    # door, cell 1 (x 16-31)
    rect(img, 17, 50, 31, 72, WHITE)
    rect(img, 18, 51, 30, 72, LINE)
    rect(img, 18, 51, 30, 56, WOOD[1])
    for x in range(18, 30, 3):
        img[51:56, x] = tuple(WOOD[0]) + (255,)
    rect(img, 18, 56, 30, 57, WOOD[2])
    rect(img, 18, 64, 30, 72, DARK)
    return img

def window(img, x0, y0, x1, y1):
    rect(img, x0, y0, x1, y1, WOOD[2])
    rect(img, x0 + 1, y0 + 1, x1 - 1, y1 - 1, WHITE)
    mid = (x0 + x1) // 2
    rect(img, x0 + 2, y0 + 2, mid - 1, y1 - 2, GLASS[0]); rect(img, mid + 1, y0 + 2, x1 - 2, y1 - 2, GLASS[0])
    img[y0 + 2, x0 + 2:x0 + 5] = tuple(WHITE) + (255,); img[y0 + 2, mid + 1:mid + 4] = tuple(WHITE) + (255,)

def house():
    """A Cianwood house (models 102 + 103): 64 x 72, the four-cell footprint."""
    img = canvas(64, 72)
    glass_roof(img)
    house_front(img)
    window(img, 35, 51, 53, 61)
    rect(img, 34, 61, 54, 62, WOOD[1])
    rect(img, 37, 63, 51, 68, WOOD[1]); rect(img, 37, 63, 51, 64, WOOD[0])       # bench under the window
    for x in (41, 46):
        img[63:68, x] = tuple(WOOD[2]) + (255,)
    for x0 in (1, 57):                                                          # blue pots
        rect(img, x0, 64, x0 + 6, 71, GLASS[3]); rect(img, x0, 64, x0 + 6, 65, GLASS[2]); rect(img, x0 + 4, 65, x0 + 6, 71, GLASS[4])
    outline(img, LINE)
    snap(img, HOUSE_PALETTE)
    return img

def pharmacy():
    """Cianwood Pharmacy (104): the house roof in a lighter glass, a shop sign across the
    front, a wide display window and a wooden counter base."""
    img = canvas(64, 72)
    glass_roof(img, light=True)
    house_front(img)
    rect(img, 8, 44, 56, 50, WOOD[2]); rect(img, 9, 45, 55, 49, WOOD[0])           # the sign board
    for x0 in (12, 20, 28, 36, 44):                                             # characters, abstract strokes
        rect(img, x0, 46, x0 + 5, 47, WOOD[2]); img[45:49, x0 + 2] = tuple(WOOD[2]) + (255,)
    rect(img, 33, 51, 55, 62, WOOD[2]); rect(img, 34, 52, 54, 61, WHITE)
    rect(img, 35, 53, 53, 60, GLASS[0]); img[53, 35:39] = tuple(WHITE) + (255,)
    rect(img, 33, 62, 55, 68, WOOD[1]); rect(img, 33, 62, 55, 63, WOOD[0])           # counter base, gold trim
    for x in (36, 42, 48, 54):
        img[63:68, x] = tuple(WOOD[2]) + (255,)
    outline(img, LINE)
    snap(img, HOUSE_PALETTE)
    return img

# --------------------------------------------------------------------------- photo studio
def studio():
    """Cameron's photo studio (105 + door 116): 64 x 64. A slate hipped roof whose hips run
    up to a central ridge, a skylight on its front slope, grey eaves; a dark wall band, a
    scalloped teal-and-yellow awning, white walls, the door in the second cell, a window."""
    img = canvas(64, 64)
    ys, xs = np.mgrid[0:64, 0:64]
    dx = np.abs(xs - 31.5)
    put = lambda m, c: img.__setitem__(m, tuple(c) + (255,))
    roof = (xs >= 1) & (xs <= 62) & (ys >= 2) & (ys <= 33)
    put(roof, SLATE[1])
    front = roof & (ys >= 2 + 30 * (dx / 30.5) * 0 + (dx * 0.9))               # the front slope between the hips
    put(roof & (ys < 2 + dx * 0.9), SLATE[2])                                    # side slopes, a shade darker
    put(roof & (ys < 2 + dx * 0.9) & (xs > 31.5), SLATE[0])                     # the lit right side
    put(front & (ys > 26), SLATE[3])
    hip = roof & (np.abs(ys - (2 + dx * 0.9)) < 1.2) & (dx > 2)
    put(hip, GREY)
    put(roof & (dx < 3) & (ys < 5), GREY)
    put(roof & ((xs <= 2) | (xs >= 61) | (ys <= 3)), GREY)                      # eaves
    rect(img, 1, 30, 63, 34, GREY); rect(img, 1, 33, 63, 34, MID)
    rect(img, 23, 14, 41, 26, MID); rect(img, 24, 15, 40, 25, PALE)            # skylight
    rect(img, 25, 16, 39, 24, WHITE); rect(img, 26, 17, 32, 21, SLATE[0]); rect(img, 33, 19, 38, 23, SLATE[0])
    rect(img, 1, 34, 63, 64, (255, 255, 255))
    rect(img, 1, 34, 63, 39, WALL)
    for x0 in range(4, 60, 8):                                                   # awning scallops
        c = STUDIO_PALETTE[11] if (x0 // 8) % 2 == 0 else STUDIO_PALETTE[12]
        rect(img, x0, 39, x0 + 8, 43, c)
        img[43, x0 + 1:x0 + 7] = tuple(c) + (255,); img[44, x0 + 2:x0 + 6] = tuple(c) + (255,)
    rect(img, 1, 39, 4, 64, MID); rect(img, 60, 39, 63, 64, MID)
    rect(img, 4, 45, 60, 58, WHITE)
    rect(img, 4, 39, 60, 40, LINE)
    rect(img, 17, 45, 31, 64, LINE); rect(img, 17, 58, 31, 64, DARK)           # door, cell 1
    rect(img, 37, 46, 53, 57, STUDIO_PALETTE[14]); rect(img, 38, 47, 52, 56, WHITE)
    rect(img, 39, 48, 51, 55, PALE); img[48, 39:43] = tuple(WHITE) + (255,)
    rect(img, 4, 58, 60, 61, STUDIO_PALETTE[12]); rect(img, 4, 61, 60, 64, MID)
    rect(img, 17, 58, 31, 64, DARK)
    outline(img, LINE)
    snap(img, STUDIO_PALETTE)
    return img

def studio_board():
    """The studio's poster board on two posts, 16 x 26."""
    img = canvas(16, 26)
    for x in (2, 12):
        rect(img, x, 6, x + 2, 26, MID); img[6:26, x + 1] = tuple(DARK) + (255,)
    rect(img, 1, 1, 15, 20, STUDIO_PALETTE[14])
    rect(img, 2, 2, 14, 19, STUDIO_PALETTE[13])
    rect(img, 3, 3, 13, 9, STUDIO_PALETTE[12]); rect(img, 4, 11, 12, 18, WHITE)
    rect(img, 5, 12, 8, 15, STUDIO_PALETTE[11]); rect(img, 8, 14, 11, 17, MID)
    outline(img, LINE)
    snap(img, STUDIO_PALETTE)
    return img

# --------------------------------------------------------------------------- props
RACK_PALETTE = [LINE, (248, 240, 200), (232, 216, 152), (200, 176, 104), (160, 136, 72), (128, 232, 200),
                (64, 184, 152), (32, 120, 104), (112, 112, 120), (248, 184, 144), (184, 80, 8), (72, 80, 80)]

def rack():
    """A herb drying rack (106): two pale wooden posts and a crossbar, four bundles of green
    herbs hanging in two rows. 32 x 32, two cells wide on its blocked base row."""
    img = canvas(32, 32)
    P = RACK_PALETTE
    for x0 in (1, 27):
        rect(img, x0, 3, x0 + 4, 31, P[2]); rect(img, x0, 3, x0 + 1, 31, P[1]); rect(img, x0 + 3, 3, x0 + 4, 31, P[3])
        rect(img, x0 - 1, 29, x0 + 5, 32, P[3])
    rect(img, 1, 2, 31, 6, P[2]); rect(img, 1, 2, 31, 3, P[1]); rect(img, 1, 5, 31, 6, P[3])
    rect(img, 5, 16, 27, 17, P[3])
    for cx, cy in ((10, 7), (21, 7), (10, 18), (21, 18)):
        img[cy:cy + 2, cx] = tuple(P[8]) + (255,)
        ys, xs = np.mgrid[0:32, 0:32]
        leaf = ((xs - cx) / 4.6) ** 2 + ((ys - cy - 6) / 4.2) ** 2 <= 1
        img[leaf] = tuple(P[6]) + (255,)
        img[leaf & (ys < cy + 5)] = tuple(P[5]) + (255,)
        img[leaf & (ys > cy + 8)] = tuple(P[7]) + (255,)
        img[leaf & (np.abs(xs - cx) < 1) & (ys > cy + 3)] = tuple(P[7]) + (255,)
    outline(img, LINE)
    snap(img, RACK_PALETTE)
    return img

def camera_prop():
    """Cameron's camera on its tripod (90): 16 x 24."""
    img = canvas(16, 24)
    P = RACK_PALETTE
    for (x0, x1) in ((7, 2), (8, 13), (7, 7)):
        for y in range(10, 24):
            x = int(round(x0 + (x1 - x0) * (y - 10) / 13))
            img[y, x] = tuple(P[11]) + (255,)
    rect(img, 2, 2, 14, 10, P[10]); rect(img, 2, 2, 14, 4, P[9]); rect(img, 3, 8, 13, 10, P[11])
    rect(img, 6, 4, 10, 8, P[11]); img[5, 7:9] = tuple(P[1]) + (255,)
    rect(img, 6, 0, 10, 2, P[11])
    outline(img, LINE)
    snap(img, RACK_PALETTE)
    return img

# Cherrygrove's accepted sea rock: foam ring, teal-lit top, slate shadow.
SEA_ROCK = [(208, 216, 216), (136, 184, 184), (112, 168, 184), (128, 128, 128), (72, 96, 112), (56, 72, 96)]

def sea_rock(w=32, h=24):
    """A rock standing in the sea, HGSS's two-cell size, in Cherrygrove's sea-rock colours:
    a rounded stone lit from the upper left with two facet creases, its foot ringed with
    foam where it meets the water. Mirrored facets keep it to few tiles."""
    img = canvas(w, h)
    ys, xs = np.mgrid[0:h, 0:w]
    cx, cy, rx, ry = (w - 1) / 2, h * 0.42, w * 0.41, h * 0.38
    body = ((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2 <= 1
    foam = (((xs - cx) / (rx + 2)) ** 2 + ((ys - cy - 1) / (ry + 2)) ** 2 <= 1) & ~body & (ys > cy)
    img[foam] = SEA_ROCK[0] + (255,)
    nx, ny = (xs - cx) / rx, (ys - cy) / ry
    light = -0.6 * nx - 0.8 * ny
    k = np.select([light > 0.45, light > 0.05, light > -0.35, light > -0.7], [1, 2, 3, 4], 5)
    for i in range(1, 6):
        img[body & (k == i)] = SEA_ROCK[i] + (255,)
    crease = body & ((np.abs(xs - cx + (ys - cy) * 0.6) < 0.6) | (np.abs(xs - cx - 5 - (ys - cy) * 0.4) < 0.6)) & (ys > cy - ry * 0.4)
    img[crease] = SEA_ROCK[4] + (255,)
    edge = body & ~(np.pad(body, 1)[:-2, 1:-1] & np.pad(body, 1)[2:, 1:-1] & np.pad(body, 1)[1:-1, :-2] & np.pad(body, 1)[1:-1, 2:])
    img[edge] = SEA_ROCK[5] + (255,)
    return img

def pebble():
    """HGSS's lone pebble north of the rock line, a small sea rock."""
    return sea_rock(16, 12)

# --------------------------------------------------------------------------- ground details
# HGSS's small stones (etc_a: the brown stone of its prop atlas, a flat 15 x 8 decal) in
# the cliff's own ramp, and its sand tufts (beach_sub) in Cherrygrove's grass greens.
STONE = [(239, 189, 140), (222, 173, 123), (198, 148, 115), (165, 115, 99), (132, 90, 74), (82, 58, 52)]
TUFT = [(104, 208, 152), (96, 192, 144), (88, 176, 136), (208, 208, 168)]

def stone():
    """A small brown stone lying flat, 16 x 8: lit from the upper left, dark rim, its
    shadow along the bottom row."""
    img = canvas(16, 8)
    ys, xs = np.mgrid[0:8, 0:16]
    cx, cy, rx, ry = 7.5, 3.2, 7.0, 3.4
    body = ((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2 <= 1
    nx, ny = (xs - cx) / rx, (ys - cy) / ry
    light = -0.6 * nx - 0.8 * ny
    k = np.select([light > 0.5, light > 0.1, light > -0.3], [0, 1, 2], 3)
    for i in range(4):
        img[body & (k == i)] = STONE[i] + (255,)
    edge = body & ~(np.pad(body, 1)[:-2, 1:-1] & np.pad(body, 1)[2:, 1:-1] & np.pad(body, 1)[1:-1, :-2] & np.pad(body, 1)[1:-1, 2:])
    img[edge] = STONE[4] + (255,)
    img[edge & (ys >= cy)] = STONE[5] + (255,)
    shadow = ~body & (np.pad(body, ((1, 0), (0, 0)))[:-1]) & (ys >= 5)
    img[shadow] = STONE[5] + (255,)
    return img

def tuft():
    """A tuft of beach grass, 16 x 16: five blades fanning up from a point, a soft
    shadow on the sand under it."""
    img = canvas(16, 16)
    rect(img, 4, 13, 12, 15, TUFT[3]); rect(img, 6, 15, 10, 16, TUFT[3])
    blades = [((7.5, 14), (7.5, 2), 1), ((7, 14), (3, 5), 2), ((8, 14), (12, 5), 2), ((7, 14), (1, 10), 1), ((8, 14), (14, 10), 1)]
    for (x0, y0), (x1, y1), shade in blades:
        n = int(max(abs(x1 - x0), abs(y1 - y0))) * 2 + 1
        for t in np.linspace(0, 1, n):
            x, y = int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t))
            img[y, x] = TUFT[shade if t < 0.7 else 0] + (255,)
    return img

# --------------------------------------------------------------------------- gym
# Blackthorn's Gym model (108 in Cianwood) through the same camera, Cianwood's colours:
# red bands and flank, a grey emblem slab. 15 colours in all.
GYM = dict(line=LINE, wood=[(184, 144, 104), (160, 112, 72), (120, 88, 56)],
           beam=[(248, 200, 144), (248, 112, 24), (208, 88, 24)],
           hall=[(224, 208, 208), (176, 160, 160)], band=[(208, 72, 64), (168, 32, 24)],
           red=[(168, 168, 168), (136, 136, 136), (80, 80, 80)], glass=(96, 184, 232))
GYM_PALETTE = [GYM['line'], *GYM['wood'], *GYM['beam'], *GYM['hall'], *GYM['band'], *GYM['red'], GYM['glass']]

def gym():
    """Cianwood Gym, from HGSS's Gym model (108, door 16) through the field camera, scaled
    by 0.95 so its 118 px width fits seven cells: a low oval drum with two red bands, two
    curved plank roof shells split by a recessed spine with three slats, orange beams that
    run up the spine's edges, bend out over the hall and drop to its foot as posts, a grey
    emblem slab over glass doors, two short beam ends at each side. 112 x 80: the foot on
    the bottom of the door row. Mirror-symmetric, so the halves share tiles."""
    C = GYM
    img = canvas(112, 96)
    ys, xs = np.mgrid[0:96, 0:112]
    dx = np.abs(xs - 55.5)
    put = lambda m, c: img.__setitem__(m, tuple(c) + (255,))
    ell = lambda r: np.sqrt(np.clip(1 - (dx / r) ** 2, 0, 1))
    e = ell(50)
    foot = 82 + 13 * e
    drum = (dx <= 50) & (ys >= 44 - 13 * e) & (ys <= foot)
    put(drum, C['hall'][0])
    put(drum & (dx > 45.5) & (ys >= 42), C['band'][0])
    band = 66 + 11 * e
    put(drum & (ys >= band) & (ys < band + 3), C['band'][1])
    put(drum & (ys >= band + 3) & (ys < band + 9), C['hall'][1])
    put(drum & (ys >= band + 9), C['band'][0])
    put(drum & (ys >= foot - 2), C['band'][1])
    er = ell(47)
    roof = (dx <= 45) & (ys >= 44 - 29 * er) & (ys <= 49 + 16 * er) & ~((dx < 14) & (ys < 22))
    put(drum & ~roof & (ys <= 51 + 16 * er) & (dx <= 46), C['hall'][1])
    shell = roof & (dx >= 19)
    put(shell, C['wood'][0])
    put(shell & ((ys > 40) | (dx > 39)), C['wood'][1])
    put(shell & (ys > 47 + 16 * er), C['wood'][2])
    for ang in (0.55, 1.0):
        t = np.linspace(0, 1, 120)
        sx = 19 + t * 30 * np.cos(ang); sy = 58 - t * 44 * np.sin(ang)
        for x_, y_ in zip(np.round(55.5 - sx).astype(int), np.round(sy).astype(int)):
            if 0 <= x_ < 56 and shell[y_, x_]:
                img[y_, x_] = tuple(C['wood'][2]) + (255,)
    put(shell & (ys < 44 - 29 * er + 1.5) & (dx < 43), C['beam'][0])
    spine = roof & (dx < 14)
    put(spine, C['wood'][1])
    put(spine & (ys < 24), C['wood'][2])
    put(spine & (dx >= 11.5), C['wood'][2])
    for y0 in (27, 35, 43):
        put(spine & (dx < 9.5) & (ys >= y0) & (ys < y0 + 3), C['wood'][2])
    put(spine & (ys >= 52), C['wood'][2])
    for x0 in (25, 32):
        rect(img, x0, 66, x0 + 6, 74, C['hall'][1])
        rect(img, x0 + 1, 67, x0 + 5, 73, C['glass'])
        img[67, x0 + 1:x0 + 3] = tuple(C['hall'][0]) + (255,); img[68, x0 + 1] = tuple(C['hall'][0]) + (255,)
    for y in range(17, 59):
        for k, t in enumerate([1, 0, 0, 1, 2]):
            img[y, 36 + k] = tuple(C['beam'][t]) + (255,)
    for y in range(64, 95):
        for k, t in enumerate([0, 1, 1, 1, 2]):
            img[y, 18 + k] = tuple(C['beam'][t]) + (255,)
    (ax, ay), (bx, by) = (38.0, 57.0), (20.0, 65.0)
    vx, vy = bx - ax, by - ay
    tt = np.clip(((xs - ax) * vx + (ys - ay) * vy) / (vx * vx + vy * vy), 0, 1)
    px_, py_ = ax + tt * vx - xs, ay + tt * vy - ys
    side = (px_ * vy - py_ * vx) / np.hypot(vx, vy)
    bend = (np.hypot(px_, py_) <= 2.6) & (xs < 56)
    put(bend, C['beam'][1]); put(bend & (side > 1.0), C['beam'][0]); put(bend & (side < -1.3), C['beam'][2])
    img[17, 36] = img[17, 40] = 0
    rect(img, 41, 59, 56, 80, C['red'][1])
    rect(img, 43, 59, 56, 60, C['red'][0]); rect(img, 41, 61, 56, 64, C['red'][0]); rect(img, 42, 60, 56, 61, C['red'][0])
    img[59, 41:43] = 0; img[60, 41] = 0
    rect(img, 41, 74, 56, 80, C['red'][2]); rect(img, 41, 61, 42, 80, C['red'][2])
    r2 = (xs - 55.5) ** 2 + (ys - 73.5) ** 2
    arch = (r2 <= 8.4 ** 2) & (r2 > 4.6 ** 2) & (ys <= 73) & (ys >= 65)
    put(arch & (xs < 56), C['hall'][0])
    put((dx < 2) & (ys >= 70) & (ys <= 73), C['hall'][0])
    rect(img, 41, 80, 45, 95, C['beam'][1]); rect(img, 41, 80, 42, 95, C['beam'][0]); rect(img, 44, 80, 45, 95, C['beam'][2])
    rect(img, 45, 80, 56, 95, C['hall'][1])
    rect(img, 46, 81, 55, 95, C['glass'])
    rect(img, 47, 82, 49, 94, C['hall'][0])
    img[80:95, 55] = tuple(C['hall'][1]) + (255,)
    for y0 in (57, 65):
        rect(img, 0, y0, 7, y0 + 6, C['beam'][1]); rect(img, 0, y0, 7, y0 + 2, C['beam'][0]); rect(img, 0, y0 + 5, 7, y0 + 6, C['beam'][2])
    img[:, 56:] = img[:, :56][:, ::-1]
    outline(img, C['line'])
    snap(img, GYM_PALETTE)
    assert not img[:16, :, 3].any()
    return img[16:]

def sheet():
    parts = [house(), pharmacy(), studio(), studio_board(), gym(), rack(), camera_prop(), sea_rock(), pebble(), stone(), tuft()]
    w = sum(p.shape[1] * 4 + 16 for p in parts); h = max(p.shape[0] for p in parts) * 4 + 16
    out = Image.new('RGBA', (w, h), (240, 240, 200, 255))
    x = 8
    for p in parts:
        out.alpha_composite(Image.fromarray(p, 'RGBA').resize((p.shape[1] * 4, p.shape[0] * 4), Image.Resampling.NEAREST), (x, 8))
        x += p.shape[1] * 4 + 16
    OUT.mkdir(parents=True, exist_ok=True)
    out.save(OUT / 'sprites.png')

if __name__ == '__main__':
    sheet()
