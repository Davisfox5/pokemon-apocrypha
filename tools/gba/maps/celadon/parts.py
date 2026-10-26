"""Celadon's buildings and street furniture, cut from Gen 3's own maps.

Celadon stands on HGSS's plan (compose.py); every piece drawn on it is real Gen 3 pixel art:
cells of a FireRed or Emerald map as the game draws them, cut out and, where the story needs
it, put together into a piece of Celadon's own (AGENTS.md, Kanto towns). Ground pixels round
a part are made transparent, so it stands on the new ground. compose.py brings each part's
colours into FireRed Celadon's palette.

FireRed's Celadon, each building on the HGSS lot it now stands on:
    dept          the Dept Store, now the market's services
    hotel         FireRed's Celadon Mansion as the Pokemon Hotel (the spec: Condominiums ->
                  Pokemon Hotel), on HGSS's Condominiums lot, balconies under its upper windows
    center        the Pokemon Center
    game_corner   the Game Corner and its prize room
    house, house_door, house_chimney   FireRed's Celadon houses, for HGSS's houses
    glasshouse    the Botanical Gardens on HGSS's gym lot: FireRed's Celadon Gym under
                  Cerulean's Bike Shop glass (FireRed), Celadon's tree crowns showing through
                  the panes in Celadon's teal, its Poke Ball crest a leaf, its GYM plate gone
    fountain      FireRed's Celadon fountain, for HGSS's plaza fountain
New pieces:
    awning        the café's striped awning on its posts: the Bike Shop's (FireRed)
    tent_*        market stalls: Slateport Market's tents with their goods (Emerald); compose.py
                  lays each canvas onto one of Celadon's colour ramps
    produce_*     Slateport Market's baskets and crates, one cell each
    bridge        the canal's footbridge: Three Island's Bond Bridge planks (FireRed), six
                  cells wide, three rows of deck for the three-row street
    hedge*        a clipped hedge, Cerulean's (FireRed), for HGSS's ledges below the gym

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

def cells(img, x0, y0, x1, y1):
    return img[y0 * 16:y1 * 16, x0 * 16:x1 * 16].copy()

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

_ground = {}
def celadon_ground(engine):
    """FireRed Celadon's grass, paving and lawn-edge colours, from their own metatiles."""
    if not _ground:
        pair = frlg.Pair(engine, 'general_frlg', 'celadon_city_frlg')
        mt = lambda ids: set().union(*[colours(frlg.flat(*frlg.render(pair, np.array([[m]], np.uint16)))) for m in ids])
        _ground['g'] = mt([0x008, 0x009, 0x010, 0x011]) | mt([0x16E, 0x166, 0x317]) | \
            mt([0x166, 0x176, 0x16D, 0x16F, 0x165, 0x167, 0x175, 0x177, 0x19D, 0x19E, 0x195, 0x196])
    return _ground['g']

def frlg_cut(engine, x0, y0, x1, y1, edges='tb', top_px=0):
    """FireRed Celadon's cells (x1, y1 exclusive) with their ground cleared from the given
    edges; top_px rows of the first cell left out (a fence behind a roof)."""
    cel = source(engine, 'CeladonCity')
    t = rgba(cells(cel, x0, y0, x1, y1))
    if top_px:
        t[:top_px, :, 3] = 0
    return clear_from_edges(t, celadon_ground(engine), edges)

# Celadon's own greens (FireRed's General and Celadon banks), light to dark
TEAL = [(189, 230, 222), (148, 205, 180), (115, 172, 148), (106, 148, 139), (74, 115, 106)]
LEAF = [(189, 255, 139), (131, 213, 98), (57, 148, 49), (57, 90, 16)]
BALCONY = [(222, 222, 230), (172, 189, 205), (123, 123, 131), (82, 82, 106)]   # Celadon's railing greys, light to dark

# --------------------------------------------------------------------------- FireRed's buildings
def dept(engine):
    return frlg_cut(engine, 9, 4, 18, 15)

def center(engine):
    return frlg_cut(engine, 46, 6, 51, 12, 'tlrb')

def game_corner(engine):
    """The Game Corner and its prize room (cols 31-41, rows 17-22), the fence behind their
    roofs left out."""
    return frlg_cut(engine, 31, 17, 42, 23, 'tb', top_px=9)

def house(engine):
    return frlg_cut(engine, 32, 25, 36, 30)

def house_door(engine):
    return frlg_cut(engine, 36, 25, 40, 30)

def house_chimney(engine):
    return frlg_cut(engine, 40, 25, 44, 30)

def hotel(engine):
    """FireRed's Celadon Mansion (cols 27-33, rows 4-11) as the Pokemon Hotel: a balcony slab
    and railing in Celadon's railing greys under each window row above the ground floor."""
    t = frlg_cut(engine, 27, 4, 34, 12, 'tlrb', top_px=9)       # the trees and roof exit behind its roof's top edge left out
    glass = (t[..., 2].astype(int) > 200) & (t[..., 0].astype(int) < 180) & (t[..., 3] > 0)
    rows = [y for y in range(t.shape[0]) if glass[y].sum() >= 8]
    bands = [r for i, r in enumerate(rows) if i == 0 or r != rows[i - 1] + 1]        # each window row's first glass line
    ends = [r for i, r in enumerate(rows) if i == len(rows) - 1 or rows[i + 1] != r + 1]
    for top, bot in list(zip(bands, ends))[:-1]:          # every window row but the ground floor's
        yb = bot + 3
        for x in range(4, t.shape[1] - 4):
            if t[yb, x, 3] == 0:
                continue
            t[yb, x, :3] = BALCONY[0]
            t[yb + 1, x, :3] = BALCONY[2]
            t[yb - 4, x, :3] = BALCONY[1]
            if x % 4 == 2:
                t[yb - 3:yb, x, :3] = BALCONY[3]
    return t

def fountain(engine):
    c = source(engine, 'CeladonCity')
    t = rgba(cells(c, 12, 19, 15, 22))
    clear_from_edges(t, colours(cells(c, 11, 19, 12, 22)) | colours(cells(c, 15, 19, 16, 22)), 'tlrb')
    g = t[..., :3].astype(int)
    t[(g[..., 1] > g[..., 0] + 30) & (g[..., 1] > g[..., 2] + 10), 3] = 0        # the lawn's grass tufts
    return t

# --------------------------------------------------------------------------- the gardens
GLASS_W = 128                                       # eight cells, the gym's roof
GLASS_LIGHT, GLASS_DARK, GLASS_EDGE = (172, 222, 238), (139, 189, 213), (115, 164, 189)
LEAF_MARK = ["..g..",
             ".gLg.",
             "gLLLg",
             "gLdLg",
             ".gdg.",
             "..d.."]

def glass(engine):
    """The Bike Shop's glass roof (Cerulean, FireRed) widened to the gym's eight cells, the
    planting under it showing through the panes: Celadon's tree crowns in Celadon's teal, the
    checker one step lighter on its light squares."""
    c = source(engine, 'CeruleanCity')
    roof = widen(px(c, 192, 375, 256, 424), 24, 24, GLASS_W, 8)
    t = rgba(roof)
    clear_from_edges(t, colours(px(c, 176, 370, 192, 424)) | colours(px(c, 256, 370, 272, 424)), 'tlr')
    cel = source(engine, 'CeladonCity')
    crowns = px(cel, 0, 176, 64, 336)
    lum = crowns.astype(int).sum(-1)
    ramp = np.digitize(lum, np.quantile(lum, [0.2, 0.45, 0.7, 0.9]))
    rgb = t[..., :3]
    glassy = np.zeros(rgb.shape[:2], bool)
    for col in (GLASS_LIGHT, GLASS_DARK, GLASS_EDGE):
        glassy |= (rgb == col).all(-1)
    light = (rgb == GLASS_LIGHT).all(-1)
    for y, x in zip(*np.nonzero(glassy)):
        k = int(ramp[(y + 7) % crowns.shape[0], (x * 3 + y // 16 * 13) % crowns.shape[1]])
        k = min(4, k + (1 if light[y, x] else 0))
        rgb[y, x] = TEAL[4 - k]
    t[(t[..., :3] == (255, 255, 255)).all(-1), :3] = (205, 205, 222)
    return t

def glasshouse(engine):
    """FireRed's Celadon Gym (cols 8-15, rows 25-30) under the glass roof, its porch's Poke
    Ball crest painted out in the porch's gold for a leaf, its GYM plate painted out in the
    wall's own column."""
    cel = source(engine, 'CeladonCity')
    t = frlg_cut(engine, 8, 25, 16, 31, 'tb')        # 128 x 96, y0 = 400
    g = glass(engine)
    m = g[..., 3] > 0
    t[16:16 + g.shape[0]][m] = g[m]                  # the roof, y 416-465
    gold = tuple(int(v) for v in cel[470, 176])
    for y in range(465, 479):
        for x in range(172, 197):
            v = tuple(int(c) for c in cel[y, x])
            if v in {(255, 255, 255), (222, 222, 230), (246, 246, 255), (197, 197, 205), (189, 148, 139), (123, 74, 74)} \
                    or sum(v) > sum(gold) + 40:
                t[y - 400, x - 128, :3] = gold
    paint(t, LEAF_MARK, 184 - 128 - 2, 466 - 400, dict(g=LEAF[2], L=LEAF[1], d=LEAF[3]))
    for y in range(472, 486):
        for x in range(146, 168):
            t[y - 400, x - 128, :3] = cel[y, 145]
    return t

def hedge(engine, n):
    """Cerulean's clipped hedge (FireRed), n cells long: its rounded ends and the middle repeated."""
    c = source(engine, 'CeruleanCity')
    out = widen(px(c, 112, 512, 272, 528), 16, 16, n * 16, 16)
    t = rgba(out)
    return clear_from_edges(t, colours(px(c, 96, 512, 112, 528)) | colours(px(c, 112, 528, 272, 544)), 'tlrb')

# --------------------------------------------------------------------------- the café
def awning(engine):
    """The Bike Shop's striped awning and its two posts (Cerulean, FireRed), four cells."""
    c = source(engine, 'CeruleanCity')
    t = rgba(px(c, 192, 438, 256, 470))
    keep = np.zeros(t.shape[:2], bool)
    keep[:18] = True
    g = t[..., :3].astype(int)
    post = g[..., 2] > g[..., 0] + 20
    cols = np.zeros(t.shape[1], bool)
    cols[3:10] = cols[54:61] = True
    keep |= post & cols[None, :]
    t[~keep, 3] = 0
    return t

# --------------------------------------------------------------------------- the market
TENTS = {'tent_a': (40, 656), 'tent_b': (168, 656), 'tent_c': (40, 720), 'tent_d': (168, 720), 'tent_e': (40, 784)}
TENT_W, TENT_H = 64, 48

def slateport_ground(s):
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

# --------------------------------------------------------------------------- the canal
def bridge(engine):
    """The Bond Bridge's planks (Three Island, FireRed), six cells wide: its west end, two
    middle cells and its east end; three rows of deck (its second plank row repeated) and its
    south side."""
    b = source(engine, 'ThreeIsland_BondBridge')
    deck = px(b, 544, 144, 704, 184)
    deck = np.concatenate([deck[:, :32], deck[:, 32:64], deck[:, 128:160]], 1)    # 96 px
    deck = np.concatenate([deck[:32], deck[16:32], deck[32:]], 0)                 # 56 px: three plank rows and the side
    t = rgba(deck)
    water = colours(px(b, 544, 128, 704, 144)) | colours(px(b, 544, 186, 704, 200))
    clear_from_edges(t, water, 'tlrb')
    g = t[..., :3].astype(int)
    t[g[..., 2] > g[..., 0] + 60, 3] = 0            # the sea showing under the side
    return t

PARTS = {'dept': dept, 'center': center, 'game_corner': game_corner, 'house': house, 'house_door': house_door,
         'house_chimney': house_chimney, 'hotel': hotel, 'fountain': fountain, 'glasshouse': glasshouse,
         'awning': awning, 'bridge': bridge,
         **{n: (lambda e, a=a: tent(e, a)) for n, a in TENTS.items()},
         **{n: (lambda e, a=a: produce(e, a)) for n, a in PRODUCE.items()},
         **{f'hedge{n}': (lambda e, n=n: hedge(e, n)) for n in (2, 4, 6, 8)}}

def main(engine):
    OUT.mkdir(parents=True, exist_ok=True)
    for p in OUT.glob('*.png'):
        p.unlink()
    for name, fn in PARTS.items():
        img = fn(engine)
        Image.fromarray(img).save(OUT / f'{name}.png')
        print(name, img.shape[1], 'x', img.shape[0])

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
