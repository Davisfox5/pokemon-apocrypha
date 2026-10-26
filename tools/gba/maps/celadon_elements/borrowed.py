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
