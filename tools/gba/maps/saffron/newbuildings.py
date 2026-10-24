"""Saffron's new buildings, made from HGSS's own models (modelkit) at C06's angle.

    saffron_dojo   one original building for both dojos (the owner's brief, 2026-10-24):
                   the Fighting Dojo's west end, gabled porch, open doorway and banners
                   (HGSS model 255), a long hall under the same shingled roof, and the
                   Gym's purple porch, glass door, walls and windows (250, door 16) for
                   the Psychic Dojo, each porch an entrance of its own on HGSS's door
                   (41, 12) and (48, 12). Canon has no Saffron Gym: the League emblems
                   come off, and each porch carries its discipline's mark (a fist on the
                   Fighting plaque, an eye on the Psychic gable), painted at Gen 3 scale.

Every part keeps HGSS's own textures and lighting; parts are sliced from the models with
modelkit.clip, so the hall repeats a uniform slice of the Fighting Dojo (roof, eave beam,
windows, walls) exactly as the model draws it. Rendered at 16 px per model unit across,
the C06 scale of HGSS's own Saffron footprints.
"""
from __future__ import annotations
import math
import numpy as np

import modelkit as K

SX = 16                                         # px per model unit across

# --------------------------------------------------------------------------- the Dojo
FIGHT_X, PSYCHIC_X = 41.5, 48.5                 # HGSS's Fighting Dojo and Gym (their doors' centres)
DOJO_X0 = 38.0                                  # the sprite's west edge (cells): both doors' centres on 8 px columns
SLICE = (1.45, 2.45)                            # a uniform slice of the Fighting Dojo, one model unit
ROOF = ('ybcfg_02', 'ybcfg_04')                 # its shingles and eave beam
GYM_WALLS_X = 3.39                              # the Gym's walls run to +-3.39
PORCH_X = 1.32                                  # the Gym's porch box: |x| <= 1.32, in front of z 0.4
BANNER = [(120, 66, 41), (189, 123, 74), (222, 132, 66), (247, 148, 74), (255, 189, 115)]   # ybcfg_07's oranges, dark to light

def plain_plaque(t):
    """The Fighting porch's plaque (ybcfg_01's front, x 0-22): the banners' orange in place
    of the League's lilac, by lightness, its emblem field one flat orange."""
    t = t.copy()
    rgb = t[0:15, 0:23, :3].astype(int)
    lum = rgb.sum(-1)
    q = np.searchsorted(np.quantile(lum, [0.2, 0.45, 0.7, 0.9]), lum)
    t[0:15, 0:23, :3] = np.array(BANNER)[q]
    t[2:13, 2:21, :3] = BANNER[1]
    return t

def no_gym_emblem(t):
    """ya_gym_b without its League emblem decal (rows 17-34, the porch gable's front)."""
    t = t.copy()
    t[17:35, 0:32, 3] = 0
    return t

# Marks painted on the rendered sprite (8 px tall at most, Gen 3 scale): key colour, outline.
FIST = ["..ooooooooo.",
        ".oWWoWWoWWoo",
        "oWWWoWWoWWWo",
        "oWWWWWWWWWWo",
        "oWoooooWWWWo",
        "oWWWWWWoWWWo",
        ".oWWWWWWWWo.",
        "..oWWWWWWo..",
        "...oooooo..."]
EYE = ["....ooooooo....",
       "..ooWWWWWWWoo..",
       ".oWWWoooooWWWo.",
       "oWWWoPPPPPoWWWo",
       ".oWWWoooooWWWo.",
       "..ooWWWWWWWoo..",
       "....ooooooo...."]

def paint(img, art, cx, cy, cols):
    h, w = len(art), len(art[0])
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    for j, row in enumerate(art):
        for i, ch in enumerate(row):
            if ch in cols:
                img[y0 + j, x0 + i] = tuple(cols[ch]) + (255,)

def mirror_porches(rgba, mats, to_px):
    """Each half mirrored about its door's centre (an 8 px column), so its two sides share
    tiles. Fighting: the west part, past the end's first tile column, is the mirror of the
    porch's east side and the hall (the model is symmetric). Psychic: the Gym's walls and
    porch west of the door are the mirror of those east of it; the hall roof keeps its own
    pixels there (its shingles run one way, and it repeats as it is)."""
    f, p = (int(round(to_px(x, 0, 0)[0])) for x in (FIGHT_X, PSYCHIC_X))
    assert f % 8 == 0 and p % 8 == 0, (f, p)
    src, sm = rgba.copy(), mats.copy()
    rgba[:, 8:f] = src[:, f:2 * f - 8][:, ::-1]
    mats[:, 8:f] = sm[:, f:2 * f - 8][:, ::-1]
    w = p - (int(to_px(PSYCHIC_X - GYM_WALLS_X, 0, 0)[0]) // 8 + 1) * 8
    s, m = src[:, p:p + w][:, ::-1], sm[:, p:p + w][:, ::-1]
    take = ~np.isin(m, ROOF) & (s[..., 3] > 0)
    rgba[:, p - w:p][take] = s[take]
    mats[:, p - w:p][take] = m[take]

def saffron_dojo(models):
    D = K.load(models, 255, retex={'ybcfg_01': plain_plaque})
    G = K.load(models, 250, retex={'ya_gym_b': no_gym_emblem})
    door = K.load(models, 16, (0, 0, 1.4))                       # HGSS: 1.4 in front of the Gym
    w = SLICE[1] - SLICE[0]
    end = 3.3 - SLICE[1]                                          # the Fighting Dojo's east end past the slice
    right = PSYCHIC_X + GYM_WALLS_X + 0.06                        # the roof's east end, just past the Psychic walls
    mid = PSYCHIC_X - GYM_WALLS_X                                 # where the Psychic walls begin
    parts = K.move(K.clip(D, 'x', hi=SLICE[0]), FIGHT_X)          # west end and the Fighting porch
    x = FIGHT_X + SLICE[0]
    while x < right - end - 1e-6:                                 # the hall: the slice, repeated
        n = min(w, right - end - x)
        sl = K.clip(D, 'x', SLICE[0], SLICE[0] + n)
        walls = K.clip(K.without(sl, *ROOF), 'x', hi=SLICE[0] + max(0.0, min(n, mid - x)))
        parts += K.move(K.named(sl, *ROOF) + walls, x - SLICE[0])
        x += n
    east = K.clip(D, 'x', SLICE[1])
    parts += K.move(K.named(east, *ROOF) + K.where(east, lambda v: v[:, 1].min() >= 3.2), x - SLICE[1])
    porch = K.where(G, lambda v: np.abs(v[:, 0]).max() <= PORCH_X and v[:, 2].min() >= 0.4)
    walls = [f for f in K.clip(K.where(G, lambda v: v[:, 1].max() < 2.6), 'x', lo=-GYM_WALLS_X - 0.01) if f not in porch]
    parts += K.move(walls + porch + door, PSYCHIC_X)
    rgba, to_px = K.render(parts, SX, x_range=(DOJO_X0, math.ceil(K.extent(parts, 'x')[1] * 2) / 2))
    mirror_porches(rgba, K.render.materials, to_px)
    # The marks: the fist in the Fighting plaque's field, the eye on the Psychic gable.
    fx, fy = to_px(FIGHT_X, 3.46, 1.70)
    paint(rgba, FIST, fx, fy, dict(W=(255, 247, 231), o=BANNER[0]))
    px_, py_ = to_px(PSYCHIC_X, 3.36, 1.55)
    paint(rgba, EYE, px_, py_, dict(W=(255, 255, 255), o=(99, 33, 148), P=(189, 115, 231)))
    doors = {'fighting': to_px(FIGHT_X, 0, 1.6), 'psychic': to_px(PSYCHIC_X, 0, 1.6)}
    return rgba, to_px, doors

# --------------------------------------------------------------------------- Silph Co.
# HGSS's Silph Co. (257, door 261) has a floor every 0.875 model units (window bands at y
# 0.625, 1.5, ... 8.5, the roof's parapet at 9.23). Ten years on it rises RISE floors more:
# the band from 4.125 to 5.0 repeats and everything above it moves up. Drawn 16 px per unit
# across (its 10 units on 10 of HGSS's 11 footprint cells, so its one-unit window bays fall
# on the 8 px grid and repeat as tiles) and SILPH_SY px per unit up the screen, which puts
# a floor at 12 px, so the tower's tiles repeat every two floors.
SILPH_X = 29.0                                  # HGSS's placement (door 28-29, 37)
SILPH_SX = 16
SILPH_SY = 12 / (0.875 * float(np.cos(np.radians(K.C.C06_PITCH))))
FLOOR, BAND = 0.875, (4.125, 5.0)
RISE = 2
SILPH_DOOR_Z = 37.5625 - 34.375                 # door 261's offset in front of 257 (HGSS)
SILPH_ANCHOR = (0, 0, SILPH_DOOR_Z)             # the tower and the lab wing draw their floors on the same rows

def silph_faces(models):
    return K.load(models, 257) + K.load(models, 261, (0, 0, SILPH_DOOR_Z))

def taller(faces, rise=RISE):
    lo, hi = BAND
    parts = K.clip(faces, 'y', hi=lo)
    for k in range(rise + 1):
        parts += K.move(K.clip(faces, 'y', lo, hi), dy=k * FLOOR)
    return parts + K.move(K.clip(faces, 'y', lo=hi), dy=rise * FLOOR)

def silph_tower(models):
    rgba, to_px = K.render(taller(silph_faces(models)), SILPH_SX, sy=SILPH_SY, anchor=SILPH_ANCHOR)
    return rgba, to_px, {'silph': to_px(0, 0, SILPH_DOOR_Z + 0.1)}

# The research lab wing (the owner's brief): a low wing built from the tower's own parts,
# its lobby floor and three floors over it, its own canopy and glass door centred on it, the
# canopy lamps in the lab's green. Its roof is the tower's parapet and roof panels without
# the glass atrium: the two panel sides (|x| 2.02-4.88) close up to meet in the middle,
# and the body's chamfered corners (|x| 4.2-4.88) close in on the canopy to the same width.
LAB_TOP = BAND[1]                               # the wing stops over its third floor
LAB_HALF = 40 / SILPH_SX                        # 80 px wide (the lot's apartment block's width), mirrored on an 8 px axis
ATRIUM = 5.0 - LAB_HALF                         # the roof kept each side, out to the parapet (past the atrium's 2.02)
LAB_LAMP = (99, 222, 140)

def lab_wing(models):
    S = silph_faces(models)
    roof = K.without(K.clip(S, 'y', lo=9.1), 'ybc_wd03.1', 'ybc_sl07')
    roof = K.move(K.where(roof, lambda v: np.abs(v[:, 0]).min() >= ATRIUM - 1e-6 or v[:, 1].max() <= 9.38), dy=LAB_TOP - 9.23)
    half = LAB_HALF                                               # each side of the wing's roof
    parts = K.move(K.clip(roof, 'x', hi=-ATRIUM), dx=ATRIUM) + K.move(K.clip(roof, 'x', lo=ATRIUM), dx=-ATRIUM)
    body = K.clip(S, 'y', hi=LAB_TOP)
    core = half - (5.0 - 4.2)                                     # the corners take the rest
    parts += K.clip(body, 'x', -core, core)
    parts += K.move(K.clip(body, 'x', hi=-4.2), dx=4.2 - core) + K.move(K.clip(body, 'x', lo=4.2), dx=core - 4.2)
    rgba, to_px = K.render(parts, SILPH_SX, sy=SILPH_SY, anchor=SILPH_ANCHOR)
    # the canopy's lamps (the tower's warm yellow) in green; the gold trim on the corners stays
    x0, y0 = to_px(-2.25, 2.0, SILPH_DOOR_Z - 0.5)
    x1, y1 = to_px(2.25, 1.2, SILPH_DOOR_Z + 0.5)
    box = np.zeros(rgba.shape[:2], bool)
    box[int(y0):int(y1) + 1, int(x0):int(x1) + 1] = True
    rgb = rgba[..., :3].astype(int)
    lamp = box & (rgb[..., 0] > 200) & (rgb[..., 1] > 180) & (rgb[..., 2] < 140) & (rgba[..., 3] > 0)
    rgba[lamp, :3] = LAB_LAMP
    return rgba, to_px, {'lab': to_px(0, 0, SILPH_DOOR_Z + 0.1)}
