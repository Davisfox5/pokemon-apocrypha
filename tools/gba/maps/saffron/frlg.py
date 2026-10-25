"""Read a FireRed/LeafGreen map and its tileset pair from the expansion's own FRLG data.

FRLG layouts use the FRLG split: a 640-tile, 640-metatile primary with palette banks 0-6,
a secondary from tile and metatile 640 with banks 7-12, and 32-bit metatile attributes
(behaviour in bits 0-8, layer type in bits 29-30). The expansion's FRLG behaviour values
are the shared MB_* numbering, so a behaviour carries over to an Emerald-format map as it
is.

    pair = Pair(engine, 'general_frlg', 'saffron_city_frlg')
    grid, border = layout(engine, 'SaffronCity_Frlg')
"""
from __future__ import annotations
import colorsys, json
from pathlib import Path
import numpy as np
from PIL import Image

NT, NB = 640, 7                          # FRLG primary: tiles (and metatiles), palette banks

def _tiles(d):
    a = np.array(Image.open(d / 'tiles.png')) & 15
    return [a[y:y + 8, x:x + 8].copy() for y in range(0, a.shape[0], 8) for x in range(0, a.shape[1], 8)]

def read_pal(p):
    v = list(map(int, p.read_text().split()[3:51]))
    return [tuple(v[i * 3:i * 3 + 3]) for i in range(16)]

class Pair:
    """An FRLG primary and secondary: tiles (4-bit index arrays), 13 palette banks,
    metatiles (8 tile entries each, layer 0 then layer 1) and attributes."""
    def __init__(self, engine, primary, secondary):
        pd, sd = engine / 'data/tilesets/primary' / primary, engine / 'data/tilesets/secondary' / secondary
        self.tiles = _tiles(pd)[:NT] + _tiles(sd)
        self.n_primary_tiles = NT
        self.pals = {b: read_pal(pd / f'palettes/{b:02}.pal') for b in range(NB)}
        self.pals.update({b: read_pal(sd / f'palettes/{b:02}.pal') for b in range(NB, 13)})
        pm = np.frombuffer((pd / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
        sm = np.frombuffer((sd / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
        pa = np.frombuffer((pd / 'metatile_attributes.bin').read_bytes(), '<u4')
        sa = np.frombuffer((sd / 'metatile_attributes.bin').read_bytes(), '<u4')
        self.meta = {i: [int(v) for v in pm[i]] for i in range(len(pm))}
        self.meta.update({NT + i: [int(v) for v in sm[i]] for i in range(len(sm))})
        self.attr = {i: int(pa[i]) for i in range(len(pa))}
        self.attr.update({NT + i: int(sa[i]) for i in range(len(sa))})

    def tile(self, e):
        t = self.tiles[e & 1023]
        if e & 0x400: t = t[:, ::-1]
        if e & 0x800: t = t[::-1]
        return t

    def behavior(self, mid):
        return self.attr[mid] & 0x1FF

    def layer_type(self, mid):
        return (self.attr[mid] >> 29) & 3

    def cell(self, mid, pals=None):
        """One metatile as (bottom RGB 16x16, top RGBA 16x16): layer 0 as the screen shows
        it (see under()), layer 1 by its non-zero pixels."""
        pals = pals or self.pals
        bot = np.zeros((16, 16, 3), np.uint8)
        top = np.zeros((16, 16, 4), np.uint8)
        fill = under(self.tiles[FILL_TILE], self.layer_type(mid), pals)
        for li, e in enumerate(self.meta[mid]):
            t = self.tile(e)
            q = li % 4
            sl = np.s_[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            c = np.array(pals[e >> 12], np.uint8)[t]
            if li < 4:
                bot[sl] = np.where((t == 0)[..., None], fill, c)
            else:
                m = t != 0
                top[sl][m] = np.concatenate([c[m], np.full((int(m.sum()), 1), 255, np.uint8)], 1)
        return bot, top

# What shows through a bottom-layer pixel of colour 0. A normal-layer metatile draws its
# bottom layer on BG2 over BG3, which the engine fills with tile 0x14 in bank 3
# (field_camera.c, DrawMetatile: 0x3014, in FireRed as in Emerald); a covered or split one
# draws it on BG3 itself, over the backdrop (bank 0's colour 0).
FILL_TILE, FILL_BANK = 0x14, 3

def under(fill_tile, layer_type, pals):
    """The 8x8 RGB a bottom-layer pixel of colour 0 shows, for a metatile of this layer type."""
    back = np.array(pals[0][0], np.uint8)
    if layer_type != 0:
        return np.broadcast_to(back, (8, 8, 3))
    c = np.array(pals[FILL_BANK], np.uint8)[fill_tile]
    return np.where((fill_tile == 0)[..., None], back, c)

def layout(engine, name):
    """(grid, border): uint16 arrays of map blocks (metatile id | collision << 10 | elevation << 12)."""
    L = json.loads((engine / 'data/layouts/layouts.json').read_text())
    lay = next(l for l in L['layouts'] if l.get('name') == name.replace('_Frlg', '') + '_Layout'
               and l.get('blockdata_filepath', '').startswith(f'data/layouts/{name}/'))
    w, h = lay['width'], lay['height']
    grid = np.frombuffer((engine / lay['blockdata_filepath']).read_bytes(), '<u2').reshape(h, w).copy()
    border = np.frombuffer((engine / lay['border_filepath']).read_bytes(), '<u2').reshape(lay['border_height'], lay['border_width']).copy()
    return grid, border

def render(pair, grid, pals=None):
    """The whole map as the game draws it: (bottom RGB, top RGBA)."""
    h, w = grid.shape
    bot = np.zeros((h * 16, w * 16, 3), np.uint8)
    top = np.zeros((h * 16, w * 16, 4), np.uint8)
    for y in range(h):
        for x in range(w):
            b, t = pair.cell(int(grid[y, x]) & 0x3FF, pals)
            bot[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = b
            top[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = t
    return bot, top

def flat(bot, top):
    out = bot.copy()
    a = top[..., 3] > 0
    out[a] = top[..., :3][a]
    return out

# --------------------------------------------------------------------------- the Kanto grade
# DESIGN.md (Visual Identity): Kanto is "cooler institutional steel and glass; restrained,
# corporate". Per bank, every warm or green colour (hue 25-170 degrees, saturation over
# 0.08) takes the bank's steel hue, keeping its lightness, its saturation scaled and
# capped; greys, purples, reds and blues stay. Applied to the town's walls and roofs only:
# the paving, the trees, the Center and Mart, Silph's purple and the dojos' and gates'
# wood keep FRLG's colours.
GRADE = {12: (215, 0.30, 0.10),           # apartment and house walls: concrete, faintly cool
         11: (205, 0.60, 0.26)}           # house roofs: slate

def grade_colour(c, hue, scale, cap):
    r, g, b = [v / 255 for v in c]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    if not (s > 0.08 and 25 <= h * 360 <= 170):
        return tuple(c)
    h, s = hue / 360, min(s * scale, cap)
    return tuple(int(round(v * 255)) & 0xF8 for v in colorsys.hls_to_rgb(h, l, s))

def graded(pals, grade=GRADE):
    """A graded colour that lands on another colour of its bank (in 5-bit) steps one level
    lighter or darker, whichever its original sat on, so no two colours merge."""
    five = lambda c: tuple(v >> 3 for v in c)
    out = dict(pals)
    for b, (hue, scale, cap) in grade.items():
        cols = [pals[b][0]]
        for c in pals[b][1:]:
            g = grade_colour(c, hue, scale, cap)
            step = 8 if sum(c) >= sum(g) else -8
            while five(g) in {five(o) for o in cols[1:]}:
                g = tuple(min(248, max(0, v + step)) for v in g)
            cols.append(g)
        out[b] = cols
    return out
