"""Pieces Celadon borrows as they are from other maps (round 5; the owner: "don't be afraid to
borrow stuff from other maps, even if it's from Johto or even if it's from Hoenn").

    olivine_lamp()      Olivine's flag-line post (gba/art/olivine-elements, bunting.png): the
                        grey post with its gold lantern and gold foot, cut out of the flag
                        line and its shaft shortened to a street lamp's height
    plants()            Hoenn's secret base plants, from Emerald's secret base tilesets (the
                        decorations' top layer, without the base's floor): the Red Plant, the
                        Tropical Plant, Pretty Flowers (1 x 2 cells), the Colorful Plant, the
                        Big Plant, the Gorgeous Plant (2 x 2)
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
from PIL import Image

import common as C

ENGINE = Path('/home/user/pokeemerald-expansion')
OLIVINE_ART = C.ROOT / 'gba/art/olivine-elements/source/elements/sprites'

def olivine_lamp(height=48):
    b = np.array(Image.open(OLIVINE_ART / 'bunting.png').convert('RGBA'))
    a = b[..., 3] > 0
    # the left post: the opaque columns from the left edge up to the first gap
    cols = a.any(0)
    x1 = 0
    while x1 < b.shape[1] and cols[x1]:
        x1 += 1
    # the flags hang from the post; keep the post's own columns (its widest run in the foot)
    foot = a[-8:].any(0)
    fx1 = 0
    while fx1 < b.shape[1] and foot[fx1]:
        fx1 += 1
    post = b[:, :fx1].copy()
    # clear the flag line where it leaves the post: anything right of the shaft above the foot
    shaft = a[b.shape[0] // 2, :fx1]
    sx0 = int(np.argmax(shaft)); sx1 = sx0 + int(shaft[sx0:].argmin() or shaft[sx0:].size)
    lantern_rows = np.nonzero(a[:, :fx1].sum(1) > (sx1 - sx0))[0]
    top_end = next((y for y in range(len(lantern_rows) - 1) if lantern_rows[y + 1] - lantern_rows[y] > 1), 0)
    for y in range(lantern_rows[top_end] + 1 if len(lantern_rows) else 0, b.shape[0] - 12):
        post[y, :sx0, 3] = 0
        post[y, sx1:, 3] = 0
    ys = np.nonzero(post[..., 3].any(1))[0]
    post = post[ys.min():ys.max() + 1]
    # shorten the shaft
    cut = post.shape[0] - height
    if cut > 0:
        mid = post.shape[0] // 2
        post = np.concatenate([post[:mid - cut // 2], post[mid - cut // 2 + cut:]])
    return post

PLANTS = dict(red_plant=((0x2D0,), (0x2D8,)), tropical_plant=((0x2D2,), (0x2DA,)), pretty_flowers=((0x2D4,), (0x2DC,)),
              colorful_plant=((0x2E0, 0x2E2), (0x2E8, 0x2E9)), big_plant=((0x2E4, 0x2E6), (0x2EC, 0x2ED)),
              gorgeous_plant=((0x2F0, 0x2F2), (0x2F8, 0x2F9)))

def plants():
    import metatiles as MT
    ts = MT.Tileset(ENGINE / 'data/tilesets/primary/secret_base', ENGINE / 'data/tilesets/secondary/secret_base/tree',
                   ENGINE / 'data/tilesets/secondary/secret_base')
    out = {}
    for name, rows in PLANTS.items():
        img = np.zeros((16 * len(rows), 16 * len(rows[0]), 4), np.uint8)
        for r, row in enumerate(rows):
            for c, mt in enumerate(row):
                img[r * 16:r * 16 + 16, c * 16:c * 16 + 16] = ts.meta(mt, layers=(1,))
        out[name] = img
    return out

def boardwalk(rows):
    """Route 104's boardwalk (Emerald, Rustboro's tileset): planks laid north-south across an
    east-west crossing, nailed, each plank lit on its left; 0x344 its top row, 0x34C the rows
    under it, 0x34D the dark line along its south edge. Its top layer only (the water under it
    is the canal's own); five cells across, a cell of water plus half a quay each side."""
    import metatiles as MT
    ts = MT.Tileset(ENGINE / 'data/tilesets/primary/general', ENGINE / 'data/tilesets/secondary/rustboro')
    row = lambda m: np.concatenate([ts.meta(m, layers=(1,))] * 5, 1)
    parts = [row(0x344)] + [row(0x34C)] * (rows - 1) + [row(0x34D)[:4]]
    return np.concatenate(parts, 0)

def log_bridge(rows, tiles=5):
    """Fortree's log bridge (Emerald Route 120, Fortree's tileset 0x297 over 0x29F): dark logs
    laid north-south across an east-west crossing, two to a cell, each capped at both ends.
    Built to any depth: the top tile's capped upper half, then the log's body repeated, then
    the bottom tile's capped lower half, so each log runs whole from the street's north edge to
    its south edge and the bridge reads as one deck over the full crossing. Top layer only;
    `tiles` cells across (the canal and half a quay each side)."""
    import metatiles as MT
    ts = MT.Tileset(ENGINE / 'data/tilesets/primary/general', ENGINE / 'data/tilesets/secondary/fortree')
    top, bot = ts.meta(0x297, layers=(1,)), ts.meta(0x29F, layers=(1,))
    body = top[8:12]
    h = rows * 16
    col = np.concatenate([top[:8]] + [body] * ((h - 16) // 4) + [bot[8:]], 0)
    return np.concatenate([col] * tiles, 1)
