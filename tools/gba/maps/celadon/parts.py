"""Celadon's new buildings and street furniture, cut from Gen 3's own maps.

Every part is real Gen 3 pixel art: cells of a FireRed or Emerald map as the game draws
them, cut out and put together into a piece of Celadon's own (AGENTS.md, Kanto towns). Ground
pixels round a part are made transparent, so it stands on Celadon's ground. Colours are
brought into FireRed Celadon's own palette in compose.py (snapped, or a part's ramp laid onto
one of Celadon's ramps), so the map keeps FireRed's colours.

    glass()       the Botanical Gardens' glasshouse roof, on FireRed's Celadon Gym (the
                  gardens take the gym's site, DESIGN.md): Cerulean's Bike Shop glass (FireRed)
                  widened to the gym's eight cells, the planting under it showing through the
                  panes in Celadon's own greens
    porch()       the gym's porch over the door with its Poke Ball crest painted out for a
                  leaf, and the GYM plate on its wall painted out
    awning()      the café's striped awning on its posts: the Bike Shop's (FireRed)
    tent_*()      market stalls: Slateport Market's tents with their goods (Emerald), one per
                  stall, the canvas laid onto one of Celadon's colour ramps in compose.py
    produce_*()   Slateport Market's baskets and crates, one cell each
    hotel()       the Pokemon Hotel: two of FireRed's Celadon houses made one building eight
                  cells wide under one roof, a floor taller, balconies on the upper floors and
                  one entrance in the middle
    bridge()      the canal's footbridge: Three Island's Bond Bridge (FireRed), six cells
    hedge()       a clipped hedge, Cerulean's (FireRed), any length

    python3 tools/gba/maps/celadon/parts.py ENGINE_CHECKOUT    # writes source/sprites/*.png
"""
from __future__ import annotations
import json, re, sys
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path += [str(HERE.parent / 'saffron'), str(HERE.parent)]
import frlg                                         # noqa: E402
from tiles import Tileset                           # noqa: E402

OUT = ROOT / 'gba/art/celadon-kanto/source/sprites'

# --------------------------------------------------------------------------- sources
def _folder(engine, sym):
    h = (engine / 'src/data/tilesets/headers.h').read_text()
    g = (engine / 'src/data/tilesets/graphics.h').read_text() + (engine / 'src/graphics.c').read_text()
    t = re.search(r'\.tiles = (\w+)', h.split(f'const struct Tileset {sym} =')[1].split(';')[0]).group(1)
    return re.search(t + r'\[\] = INCGFX_U32\("data/tilesets/\w+/(\w+)/tiles.png"', g).group(1)

_maps = {}
def source(engine, name):
    """A map as the game draws it (RGB), by layout name."""
    if name not in _maps:
        lays = {l['name'].replace('_Layout', ''): l for l in json.loads((engine / 'data/layouts/layouts.json').read_text())['layouts']
                if 'name' in l}
        l = lays[name]
        w, h = l['width'], l['height']
        grid = np.frombuffer((engine / l['blockdata_filepath']).read_bytes(), '<u2').reshape(h, w)
        p, s = _folder(engine, l['primary_tileset']), _folder(engine, l['secondary_tileset'])
        if l['primary_tileset'].endswith('_Frlg'):
            img = frlg.flat(*frlg.render(frlg.Pair(engine, p, s), grid))
        else:
            img = np.array(Tileset(engine, s, p).map_image(grid.ravel().tolist(), w).convert('RGB'))
        _maps[name] = img
    return _maps[name]

def px(img, x0, y0, x1, y1):
    """A pixel rectangle (x1, y1 exclusive)."""
    return img[y0:y1, x0:x1].copy()

def rgba(a):
    return np.concatenate([a, np.full(a.shape[:2] + (1,), 255, np.uint8)], 2)

def colours(img):
    return {tuple(c) for c in img.reshape(-1, 3).tolist()}

def clear_from_edges(t, ground, edges='tlrb'):
    """Pixels of the ground's colours reachable from the given edges become transparent."""
    h, w = t.shape[:2]
    seeds = ([(0, x) for x in range(w)] if 't' in edges else []) + ([(h - 1, x) for x in range(w)] if 'b' in edges else []) \
        + ([(y, 0) for y in range(h)] if 'l' in edges else []) + ([(y, w - 1) for y in range(h)] if 'r' in edges else [])
    seen = np.zeros((h, w), bool)
    q = deque(seeds)
    while q:
        y, x = q.popleft()
        if not (0 <= y < h and 0 <= x < w) or seen[y, x] or tuple(t[y, x, :3]) not in ground:
            continue
        seen[y, x] = True
        q.extend(((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)))
    t[seen, 3] = 0
    return t

def clear_colours(t, cols):
    sel = np.zeros(t.shape[:2], bool)
    for c in cols:
        sel |= (t[..., :3] == c).all(-1)
    t[sel, 3] = 0
    return t

def widen(a, left, right, width, period):
    """a's columns [left, w - right) repeated (whole periods from `left`) to `width` pixels."""
    mid = a[:, left:left + period]
    n = width - left - right
    reps = np.concatenate([mid] * (n // period + 1), 1)[:, :n]
    return np.concatenate([a[:, :left], reps, a[:, a.shape[1] - right:]], 1)

def paint(img, art, x0, y0, cols):
    for j, row in enumerate(art):
        for i, ch in enumerate(row):
            if ch in cols:
                img[y0 + j, x0 + i] = tuple(cols[ch]) + (255,)

# Celadon's own greens (FireRed's General and Celadon banks), light to dark
TEAL = [(189, 230, 222), (148, 205, 180), (115, 172, 148), (106, 148, 139), (74, 115, 106)]
LEAF = [(189, 255, 139), (131, 213, 98), (57, 148, 49), (57, 90, 16)]

# --------------------------------------------------------------------------- the gardens
GLASS_W = 128                                       # eight cells, the gym's roof
GLASS_LIGHT, GLASS_DARK, GLASS_EDGE = (172, 222, 238), (139, 189, 213), (115, 164, 189)

def glass(engine):
    """The Bike Shop's glass roof (Cerulean, FireRed) widened to the gym's eight cells. The
    panes show the planting under them: the Celadon trees' crowns (FireRed's own, from the
    city's west edge) behind the glass, in Celadon's teal greens, the panes' checker one
    step lighter on its light squares, so the roof reads as glass over a garden."""
    c = source(engine, 'CeruleanCity')
    roof = px(c, 192, 375, 256, 424)                # the frame and its glass, 64 x 49
    roof = widen(roof, 24, 24, GLASS_W, 8)
    t = rgba(roof)
    clear_from_edges(t, colours(px(c, 176, 370, 192, 424)) | colours(px(c, 256, 370, 272, 424)), 'tlr')
    cel = source(engine, 'CeladonCity')
    crowns = px(cel, 0, 176, 64, 336)               # the west edge's trees, cols 0-3, rows 11-20
    lum = crowns.astype(int).sum(-1)
    ramp = np.digitize(lum, np.quantile(lum, [0.2, 0.45, 0.7, 0.9]))      # 0 darkest .. 4 lightest
    rgb = t[..., :3]
    glassy = np.zeros(rgb.shape[:2], bool)
    for col in (GLASS_LIGHT, GLASS_DARK, GLASS_EDGE):
        glassy |= (rgb == col).all(-1)
    light = (rgb == GLASS_LIGHT).all(-1)
    for y, x in zip(*np.nonzero(glassy)):
        k = int(ramp[(y + 7) % crowns.shape[0], (x * 3 + y // 16 * 13) % crowns.shape[1]])   # 0 dark .. 4 light
        k = min(4, k + (1 if light[y, x] else 0))
        rgb[y, x] = TEAL[4 - k]
    t[(t[..., :3] == (255, 255, 255)).all(-1), :3] = (205, 205, 222)     # a glint on the frame, in the frame's own light grey
    return t

LEAF_MARK = ["..g..",
             ".gLg.",
             "gLLLg",
             "gLdLg",
             ".gdg.",
             "..d.."]

def porch(engine):
    """The gym's porch and wall row (FireRed, rows 29-30 of the gym, cols 8-15) with its
    Poke Ball crest painted out in the porch's gold for a leaf, and the GYM plate on the wall
    painted out in the wall's own rows."""
    cel = source(engine, 'CeladonCity')
    t = rgba(px(cel, 128, 462, 256, 496))           # under the roof: walls, porch and door, 128 x 34
    gold = tuple(int(v) for v in cel[470, 176])     # the porch's face
    # the crest: the porch face between its trim, x 172-196, y 465-479
    for y in range(465, 479):
        for x in range(172, 197):
            v = tuple(int(c) for c in cel[y, x])
            if v in {(255, 255, 255), (222, 222, 230), (246, 246, 255), (197, 197, 205), (189, 148, 139), (123, 74, 74)} \
                    or sum(v) > sum(gold) + 40:
                t[y - 462, x - 128, :3] = gold
    paint(t, LEAF_MARK, 184 - 128 - 2, 466 - 462, dict(g=LEAF[2], L=LEAF[1], d=LEAF[3]))
    # the plate: the plain wall column just west of it, carried across
    for y in range(472, 486):
        for x in range(146, 168):
            t[y - 462, x - 128, :3] = cel[y, 145]
    clear_from_edges(t, colours(px(cel, 144, 496, 240, 512)), 'lrb')        # the lawn in front (row 31)
    return t

def hedge(engine, cells):
    """Cerulean's clipped hedge (FireRed), `cells` long: its rounded ends and the middle repeated."""
    c = source(engine, 'CeruleanCity')
    h = px(c, 112, 512, 272, 528)                   # cols 7-16, row 32
    out = widen(h, 16, 16, cells * 16, 16)
    t = rgba(out)
    return clear_from_edges(t, colours(px(c, 96, 512, 112, 528)) | colours(px(c, 112, 528, 272, 544)), 'tlrb')

# --------------------------------------------------------------------------- the café
def awning(engine):
    """The Bike Shop's striped awning and its two posts (Cerulean, FireRed), four cells."""
    c = source(engine, 'CeruleanCity')
    t = rgba(px(c, 192, 438, 256, 470))             # the awning (y 440-455) and posts to the ground
    keep = np.zeros(t.shape[:2], bool)
    keep[:18] = True                                # the canvas and its valance
    g = t[..., :3].astype(int)
    post = g[..., 2] > g[..., 0] + 20               # the posts' blue-grey
    cols = np.zeros(t.shape[1], bool)
    cols[3:10] = cols[54:61] = True                 # the posts, at either end
    keep |= post & cols[None, :]
    t[~keep, 3] = 0
    return t

# --------------------------------------------------------------------------- the market
TENTS = {'tent_a': (40, 656), 'tent_b': (168, 656), 'tent_c': (40, 720), 'tent_d': (168, 720), 'tent_e': (40, 784)}
TENT_W, TENT_H = 64, 48

def slateport_ground(s):
    """Slateport's paving and the tents' shade on it (all left behind)."""
    g = colours(px(s, 32, 640, 240, 656))            # row 40, bare paving
    shade = colours(px(s, 80, 688, 96, 704)) - g      # cell (5, 43): only the shade on the paving
    return g, shade

def tent(engine, at):
    s = source(engine, 'SlateportCity')
    x, y = at
    t = rgba(px(s, x, y, x + TENT_W, y + TENT_H))
    ground, shade = slateport_ground(s)
    clear_from_edges(t, ground | shade, 'tlrb')
    clear_colours(t, shade)
    return t

PRODUCE = {'produce_orange': (112, 656), 'produce_crate': (112, 672), 'produce_green': (112, 688), 'produce_pot': (48, 704),
           'produce_flowers': (96, 576)}

def produce(engine, at):
    s = source(engine, 'SlateportCity')
    x, y = at
    t = rgba(px(s, x, y, x + 16, y + 16))
    ground, shade = slateport_ground(s)
    return clear_from_edges(t, ground | shade, 'tlrb')

# --------------------------------------------------------------------------- the hotel
HOTEL_W = 128                                       # eight cells, two houses' lots
HOUSE = (704, 400, 768, 480)                        # FireRed's Celadon house at cols 44-47, rows 25-29 (px, x1/y1 exclusive)
ROOF_ROWS = (8, 40)                                 # the roof's rows within the house picture
WINDOW_BAND = (48, 64)                              # one storey of the wall: a window row, 16 px
BALCONY = [(222, 222, 230), (172, 189, 205), (123, 123, 131), (82, 82, 106)]   # Celadon's railing greys, light to dark

def hotel(engine):
    """Two of FireRed's Celadon houses (cols 44-51) made one building: one roof eight cells
    wide (the house roof's ends, its middle repeated, one chimney at the centre), the wall a
    storey taller (the house's own window band repeated), a balcony slab and railing under each
    upper window row in Celadon's railing greys, and one entrance in the middle: FireRed's
    house door, the door itself in col 48."""
    cel = source(engine, 'CeladonCity')
    x0, y0, x1, y1 = HOUSE
    house = px(cel, x0, y0, x1, y1)                 # 64 x 80: roof rows 8-39, wall 40-79
    chimney_house = px(cel, 768, y0, 832, y1)       # the next house, whose roof has the chimney
    roof = widen(house[:ROOF_ROWS[1]], 16, 16, HOTEL_W, 16)
    cx = HOTEL_W // 2 - 16
    roof[:, cx:cx + 32] = chimney_house[:ROOF_ROWS[1], 28:60]      # the chimney, mid-roof
    wall = house[ROOF_ROWS[1]:]                     # 40 rows: top trim, window rows at 48 and 64, base
    # its windows every 32 px from x 9: the left edge, three window bays, the last bay and edge
    wall = np.concatenate([wall[:, :9], wall[:, 9:41], wall[:, 9:41], wall[:, 9:41], wall[:, 41:64]], 1)
    band = wall[WINDOW_BAND[0] - ROOF_ROWS[1]:WINDOW_BAND[1] - ROOF_ROWS[1]]
    body = np.concatenate([wall[:WINDOW_BAND[0] - ROOF_ROWS[1]], band, wall[WINDOW_BAND[0] - ROOF_ROWS[1]:]], 0)
    # the ground floor: its two middle windows walled up for the entrance in the middle
    gy = body.shape[0] - 24
    plain = body[gy:gy + 16, 26:27]                 # a window-free wall column of the same rows
    body[gy:gy + 16, 41:87] = np.repeat(plain, 46, 1)
    # the entrance: FireRed's house door front (the house at cols 36-39), the door itself in col 48
    door = px(cel, 584, 456, 608, 480)              # 24 x 24, the frame and door
    dx = 56
    body[body.shape[0] - 24:, dx:dx + 24] = door
    t = rgba(np.concatenate([roof, body], 0))
    # balconies under the two upper window rows (not the ground floor)
    top = ROOF_ROWS[1] + (WINDOW_BAND[0] - ROOF_ROWS[1])
    for row in (top, top + 16):
        yb = row + 13
        for x in range(6, HOTEL_W - 6):
            t[yb, x, :3] = BALCONY[0]                   # the slab's lit edge
            t[yb + 1, x, :3] = BALCONY[2]
            t[yb - 5, x, :3] = BALCONY[1]               # the rail
            if x % 4 == 2:
                t[yb - 4:yb, x, :3] = BALCONY[3]        # the balusters
    ground = colours(px(cel, 688, 480, 704, 496)) | colours(px(cel, 832, 480, 848, 496)) | colours(px(cel, 704, 384, 832, 400))
    return clear_from_edges(t, ground, 'tlrb')

# --------------------------------------------------------------------------- the canal
def bridge(engine):
    """The Bond Bridge's planks (Three Island, FireRed), six cells: its west end, three
    middle cells and its east end, the deck two rows and its side under it."""
    b = source(engine, 'ThreeIsland_BondBridge')
    deck = px(b, 544, 144, 704, 184)                # cols 34-43, rows 9-11: the deck and its south side
    deck = np.concatenate([deck[:, :32], deck[:, 32:64], deck[:, 128:160]], 1)    # 96 px
    t = rgba(deck)
    water = colours(px(b, 544, 128, 704, 144)) | colours(px(b, 544, 186, 704, 200))
    clear_from_edges(t, water, 'tlrb')
    g = t[..., :3].astype(int)
    t[g[..., 2] > g[..., 0] + 60, 3] = 0            # the sea showing under the side
    return t

PARTS = {'glass': glass, 'porch': porch, 'awning': awning, 'hotel': hotel, 'bridge': bridge,
         **{n: (lambda e, a=a: tent(e, a)) for n, a in TENTS.items()},
         **{n: (lambda e, a=a: produce(e, a)) for n, a in PRODUCE.items()},
         **{f'hedge{n}': (lambda e, n=n: hedge(e, n)) for n in (3, 4, 5, 6)}}

def main(engine):
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in PARTS.items():
        img = fn(engine)
        Image.fromarray(img).save(OUT / f'{name}.png')
        print(name, img.shape[1], 'x', img.shape[0], 'colours', len(colours(img[img[..., 3] > 0][:, :3][None])))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
