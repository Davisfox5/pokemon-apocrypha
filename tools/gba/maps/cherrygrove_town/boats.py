"""The town's two small boats, redrawn clean on their own silhouettes in their own palette (bank 11).

The base town's fishing boat (x27-28, rows 14-17) and motorboat (x28-31, rows 23-25) were resampled art:
their decks were speckle. Each is drawn here part by part from the base boat's layout: outline, gunwale
(lit to the west and north, shaded to the east and south), a flat deck with its hatch and crates, the
cabin with its window band, posts and door, the transom or hull side. The large boat west of the pier
keeps its base pixels.
"""
from __future__ import annotations
import math
import numpy as np
from scipy.ndimage import binary_fill_holes, binary_opening

OUT, DK, SL = (41, 32, 32), (41, 41, 49), (65, 82, 90)
R1, R2, R3, R4 = (222, 82, 32), (156, 65, 49), (139, 32, 16), (106, 16, 16)
WH, CR, CR2 = (246, 238, 222), (222, 213, 180), (205, 189, 164)
TN, TN2 = (172, 156, 123), (131, 123, 98)
GL, GL2 = (49, 131, 164), (98, 189, 205)
PALETTE = (OUT, DK, SL, R1, R2, R3, R4, WH, CR, CR2, TN, TN2, GL, GL2)

def _half(y):
    """The fishing boat's half width by row: a round bow, straight sides, a stepped stern."""
    if y < 3:
        return 1
    if y <= 25:
        return max(2, int(round(1.5 + 7.5 * math.sqrt((y - 3) / 22))))
    if y <= 51:
        return 9
    return {58: 7, 59: 7, 60: 7, 61: 7, 62: 6, 63: 4}.get(y, 8)

def fishing():
    """32x64 RGBA, bow north: the bow post, the fore deck's hold, the white cabin and its window band, the
    rear wall's door and windows, the aft deck, the transom; fenders on both sides."""
    h, w = 64, 32
    art = np.zeros((h, w, 4), np.uint8)
    for y in range(h):
        k = _half(y); l, r = 16 - k, 15 + k
        art[y, l:r + 1, 3] = 255
        if y <= 2:
            art[y, l:r + 1, :3] = OUT if y == 0 else (TN if y == 1 else CR)
            continue
        for x in range(l, r + 1):
            c = SL
            if y == 31:
                c = CR
            elif 32 <= y <= 41:
                c = CR2 if x >= r - 3 else (TN2 if 15 <= x <= 16 and 35 <= y <= 36 else WH)   # the roof, its mast foot
            elif 42 <= y <= 44:
                c = CR if (x <= l + 3 or x >= r - 3 or y == 44) else (GL2 if y == 42 else GL)
            elif 45 <= y <= 50:
                c = CR2 if y == 45 else (DK if 14 <= x <= 17 and y >= 47 else (GL if x in (11, 12, 19, 20) and 47 <= y <= 48 else CR))
            elif 58 <= y <= 62:
                c = WH if y >= 60 else R1
            elif 13 <= y <= 25 and 12 <= x <= 19:
                c = TN if y == 13 else (TN2 if x in (12, 19) or y == 25 else (SL if y == 14 else DK))   # the hold
            elif y in (8, 9) and 15 <= x <= 16:
                c = TN
            art[y, x, :3] = c
        art[y, l, :3] = art[y, r, :3] = OUT
        if r - l + 1 >= 6:
            art[y, l + 1, :3], art[y, r - 1, :3] = R1, R2
        if r - l + 1 >= 10 and not 58 <= y <= 62:
            art[y, l + 2, :3], art[y, r - 2, :3] = R3, R4
        if y == h - 1:
            art[y, l:r + 1, :3] = OUT
    for y in range(3, h):                            # where the bow widens the outline steps out with it
        for d in range(_half(y - 1) + 1, _half(y) + 1):
            art[y, 16 - d, :3] = art[y, 15 + d, :3] = OUT
    for y in (27, 28, 42, 43):                       # fenders
        for x in (6, 25):
            art[y, x] = OUT + (255,)
    return art

def motorboat(base_mask):
    """64x48 RGBA, bow west, seen from the south as the town's buildings are: the red top rail round the
    bow, the deck's two crates and its hatch, the white cabin with its window, door and two posts, the
    stern deck, the lower rail, the white hull side above its dark bottom. base_mask: the base boat's
    pixels, its silhouette."""
    mask = binary_fill_holes(base_mask)
    mask = binary_opening(mask, np.ones((2, 2), bool)) | (mask & binary_opening(mask, np.ones((1, 3), bool)))
    h, w = mask.shape
    art = np.zeros((h, w, 4), np.uint8)
    p = np.pad(mask, 1)
    edge = mask & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
    for y, x in zip(*np.nonzero(mask)):
        cab = 38 <= x <= 54
        c = SL
        if y <= 12:                                  # above the deck: the cabin roof and its posts
            if 40 <= x <= 41 and y <= 9:
                c = TN if y == 7 else WH
            elif 50 <= x <= 53 and y <= 9:
                c = TN2 if y == 7 else DK
            else:
                c = CR if y <= 11 else CR2
        elif y <= 14 and not cab:
            c = R1
        elif y <= 24:
            if cab:
                c = CR if y == 13 else (CR2 if x >= 53 else WH)
                if 41 <= x <= 47 and 18 <= y <= 21:
                    c = GL2 if y == 18 else GL
                if 49 <= x <= 51 and y >= 19:
                    c = DK
            elif x >= 55:
                c = R1 if y == 15 else (R2 if y == 16 else SL)
            elif 32 <= x <= 36 and 18 <= y <= 22:
                c = TN2 if x in (32, 36) or y in (18, 22) else DK   # the hatch
        elif y <= 26:
            c = R2 if y == 25 else R3
        elif y <= 28:
            c = WH
        elif y == 29:
            c = CR2
        art[y, x, :3] = c
    art[edge, :3] = OUT
    pe = np.pad(edge, 1)
    near = mask & ~edge & (pe[:-2, 1:-1] | pe[2:, 1:-1] | pe[1:-1, :-2] | pe[1:-1, 2:])
    for y, x in zip(*np.nonzero(near)):              # the gunwale just inside the outline, round bow and stern
        if 13 <= y <= 26 and not 38 <= x <= 54:
            art[y, x, :3] = R1 if y <= 19 else R2
    for a, b, c, d in ((11, 16, 19, 21), (22, 17, 30, 22)):   # the crates: a dark edge, a lit top
        for y in range(b, d + 1):
            for x in range(a, c + 1):
                art[y, x, :3] = DK if x in (a, c) or y in (b, d) else (CR if y == b + 1 else (TN2 if x == c - 1 else TN))
    art[mask, 3] = 255
    return art
