"""Celadon's buildings, round 6: HGSS's own Celadon models brought down to Gen 3.

The owner, on round 5's drawn buildings: "take actual houses from Gen 4, move them down to Gen
3 ... the actual Kanto houses that are in Celadon. Take those, modify them slightly ... use
those as your one source of truth"; for the Dept Store "start with the Gen 4 department store
and just add to that"; and of every building, "the pitch ... is very flat, very 2D".

So each building is its HGSS model (pokeheartgold Celadon, area bank 15) rendered by
gen3_art.convert at 45 degrees (between C06's 38 and a top-down view: the roofs open up
without crushing the fronts), unsqueezed, at the scale its role asks, then given the Gen 3
finish (gen3_art.gen3_finish: shade under eaves, lit upper and left edges, lone texels
merged) and C06's outline. The changes the story asks are made on the model's own textures
or on the converted art, never by redrawing the building:

    dept_store      242 with its door (15), 27 px per unit: its two banners repainted with
                    Gen 3 kana (painted at 1:1 on the converted art), the yellow タマムシ ("Tamamushi", Celadon's Japanese name) and
                    the red デパート ("department store"); its roof glass (station_c) given
                    crisp Gen 3 panes in the texture's own four blues
    hotel           244 with its door (15), 24 px: the Pokemon Hotel
    apartments      238, 24 px
    prize_corner    240 with its door (24), 17 px
    cafe            243 with its door (133), 16 px
    house(colour)   237, HGSS Celadon's teal house, 15 px (60 x 78), both its storeys as HGSS has them
                    (a one-storey cut left the barrel roof swamping the house): a door put in
                    its ground floor under the window's left pane, and its teal turned to one
                    of Celadon's colours (teal, coral, blue, amber, plum, green)
    flat            236, the teal house with the flower box, 16 px

No building carries English text (AGENTS.md); the Dept Store's kana are its only lettering.
"""
from __future__ import annotations
import colorsys
import numpy as np

import common as C
import gen3_art as G3
import buildings as Bd

PITCH = 45.0

KANA = {   # 8 x 8 Gen 3 kana, drawn for the banners (vertical writing: the long vowel is a stroke down)
    'ta': ["..#.....", ".######.", ".#....#.", "#.#..#..", "...##...", "..##....", ".#......", "#......."],
    'ma': ["########", "......#.", ".....#..", "..#.#...", "...#....", "....#...", ".....#..", "........"],
    'mu': ["...#....", "...#....", "..#.....", "..#..#..", ".#....#.", ".#.....#", "########", "......#."],
    'shi': ["##......", "..#...#.", "......#.", "##...#..", "..#.#...", "...#....", ".##.....", "........"],
    'de': ["......##", ".#####..", "........", "########", "...#....", "...#....", "..#.....", ".#......"],
    'pa': ["......#.", "..#..#.#", "..#...#.", ".#.....#", ".#.....#", "#.......", "#.......", "........"],
    '-': ["...#....", "...#....", "...#....", "...#....", "...#....", "...#....", "...#....", "........"],
    'to': ["..#.....", "..#.....", "..###...", "..#..#..", "..#.....", "..#.....", "..#.....", "........"],
}
BANNERS = ((0, ('ta', 'ma', 'mu', 'shi')), (16, ('de', 'pa', '-', 'to')))

def banners(t):
    """ta_depart2 with its two banners cleared of HGSS's lettering (each to its cloth's light
    shade); paint_kana letters them again on the converted art at 1:1."""
    t = t.copy()
    for x0, _ in BANNERS:
        reg = t[5:64, x0:x0 + 16, :3]
        cols = sorted({tuple(int(v) for v in c) for c in reg.reshape(-1, 3)}, key=sum)
        reg[...] = cols[-1]
    return t

def crisp_glass(t):
    """station_c (the roof glass, 16 x 16, soft rounded panes) as Gen 3 glass: a frame in its
    darkest blue, the pane in its mid blues lit at the top, a diagonal glint in its lightest."""
    t = t.copy()
    cols = sorted({tuple(int(v) for v in c) for c in t[..., :3].reshape(-1, 3)}, key=lambda c: 3 * c[0] + 4 * c[1] + 2 * c[2])
    d, m1, m2, l = cols[0], cols[len(cols) // 3], cols[2 * len(cols) // 3], cols[-1]
    h, w = t.shape[:2]
    t[..., :3] = m1
    t[0, :, :3] = d; t[:, 0, :3] = d
    t[1:4, 1:, :3] = m2
    for k in range(3, w - 3):
        t[h - 1 - k, k, :3] = l
        if k + 1 < w:
            t[h - 1 - k, k + 1, :3] = l
    return t

def models():
    _, _, m, _, _ = C.load(str(C.ROOT.parent / 'pokeheartgold'))
    return m

def convert(mods, name, scale, retex=None, n=8):
    img, _ = G3.convert(mods, Bd.spec()[name][0], scale=scale, pitch=PITCH, retex=retex, finish=True, n=n)
    return img

def dept_store(mods):
    img = convert(mods, 'services', 27.0, retex={'ta_depart2': banners, 'station_c': crisp_glass}, n=14)
    return paint_kana(img)

def paint_kana(img):
    """The kana again on the converted banners at 1:1, bold, in a step darker than HGSS's
    lettering so they read at Gen 3 size: the yellow banner's タマムシ, the red's デパート."""
    img = img.copy()
    rgb = img[..., :3].astype(int)
    a = img[..., 3] > 0
    yellow = a & (rgb[..., 0] > 200) & (rgb[..., 1] > 150) & (rgb[..., 2] < 110)
    red = a & (rgb[..., 0] > 190) & (rgb[..., 1] < 90) & (rgb[..., 2] < 60)
    for mask, word, ink in ((yellow, BANNERS[0][1], (156, 99, 16)), (red, BANNERS[1][1], (115, 16, 8))):
        ys, xs = np.nonzero(mask)
        if not len(ys):
            continue
        cols = np.bincount(xs)
        x0, x1 = xs.min(), xs.max()
        body = [y for y in range(ys.min(), ys.max() + 1) if mask[y, x0:x1 + 1].mean() > 0.8]
        y0, y1 = body[0], body[-1]
        cx = (x0 + x1) // 2
        step = max(10, (y1 - y0 - 8) // len(word))
        for k, g in enumerate(word):
            gy0 = y0 + 4 + k * step
            for gy, row in enumerate(KANA[g]):
                for gx, ch in enumerate(row):
                    if ch == '#':
                        for dx in (0, 1):                      # bold: each stroke two pixels across
                            X, Y = cx - 4 + gx + dx, gy0 + gy
                            if mask[Y, X]:
                                img[Y, X, :3] = ink
    return img

def hotel(mods):
    return convert(mods, 'hotel', 24.0)

def apartments(mods):
    return convert(mods, 'tower', 24.0)

def prize_corner(mods):
    return convert(mods, 'prize', 17.0)

def cafe(mods):
    return convert(mods, 'cafe', 16.0)

def flat(mods):
    return convert(mods, 'flat', 16.0)

# --------------------------------------------------------------------------- the teal house
HUES = dict(teal=None, coral=0.02, blue=0.60, amber=0.10, plum=0.83, green=0.30)

def recolour(img, hue):
    """Turn the house's teal (its roof, frames and balconies) to another of Celadon's colours,
    keeping each pixel's lightness and the greys, whites and the lime balconies as they are."""
    if hue is None:
        return img
    out = img.copy()
    for y, x in zip(*np.nonzero(img[..., 3])):
        r, g, b = (img[y, x, :3] / 255.0)
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        if s > 0.15 and 0.38 < h < 0.55:                       # the teals (the lime and the greys stay)
            nr, ng, nb = colorsys.hls_to_rgb(hue, l, min(1.0, s * 1.05))
            out[y, x, :3] = [int(round(v * 31)) * 255 // 31 for v in (nr, ng, nb)]
    return out

def one_storey(img, cut=(36, 56)):
    """The teal house with its upper storey (the upper window and its balcony) taken out:
    the roof sits on the ground floor."""
    return np.concatenate([img[:cut[0]], img[cut[1]:]], 0)

def add_door(img):
    """A door in the ground floor beside the window, in the house's own darkest teal for the
    frame and its mid teal for the leaf, lit at the top like the window over it; the window
    keeps its right-hand pane and the balcony its right-hand half."""
    out = img.copy()
    h, w = out.shape[:2]
    rgb = out[..., :3].astype(int)
    lum = rgb @ [3, 4, 2]
    a = out[..., 3] > 0
    teal = a & (rgb[..., 1] > rgb[..., 0] + 20) & (rgb[..., 2] > rgb[..., 0])
    darkest = tuple(rgb[teal][np.argmin(lum[teal])])
    mids = sorted({tuple(c) for c in rgb[teal]}, key=lambda c: 3 * c[0] + 4 * c[1] + 2 * c[2])
    mid, light = mids[len(mids) // 2], mids[-2]
    x0 = int(round(w * 0.33)); x1 = x0 + 11                  # under the window's left pane
    y1 = h - 3
    y0 = y1 - 21
    out[y0:y1, x0:x1, :3] = darkest
    out[y0 + 1:y1, x0 + 1:x1 - 1, :3] = mid
    out[y0 + 1:y0 + 3, x0 + 1:x1 - 1, :3] = light
    out[y0 + 10, x1 - 3, :3] = (247, 222, 99)                  # the knob
    out[y0 + 4:y1, x0 + (x1 - x0) // 2, :3] = darkest           # the door's two leaves
    out[y0:y1, x0:x1, 3] = 255
    return out

HOUSE_SCALE = 15.0                                             # 60 x 78: under the Center's 80, four to a 15-cell terrace

def house(mods, colour='teal', base=None):
    base = convert(mods, 'house', HOUSE_SCALE) if base is None else base
    return recolour(add_door(base), HUES[colour])
