"""Concept render of the fourth-round plan (plan.py) with its real art, for the owner's call.

    python3 tools/gba/maps/celadon_elements/concept.py PATH/TO/pokeheartgold

Ground from HGSS's textures (ground.py's pieces), the canal with stone quays drawn from the
water's own shape, the cycleway painted along its banks, gravel walks and meadows in the
Arboretum, trees (Celadon's round tree, a conifer and a blossom tree for the Arboretum),
the buildings as Gen 3 art (gen3_art.py) at their new size, the custom props
(custom_art.py), the C06 Center. Writes evidence/v4/concept.png, plot.png.
"""
from __future__ import annotations
import hashlib, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

import common as C
import ground as G
import props as Pr
import custom_art as A
import gen3_art as G3
import buildings as Bd
import plan as PL

W, H = PL.W, PL.H
G.W, G.H = W, H                     # ground.py's helpers work on the plan's size
OUT = C.EV / 'v4'
GRASSY = ('forest', 'meadow', 'lawn', 'grass')

def h(*a):
    return int(hashlib.md5(' '.join(map(str, a)).encode()).hexdigest(), 16)

# --------------------------------------------------------------------------- ground
QUAY = [(232, 224, 200), (200, 192, 168), (152, 144, 128), (104, 100, 96)]
CYCLE = [(96, 184, 176), (72, 160, 152), (56, 128, 128)]
LINE = (248, 248, 232)
GRAVEL = [(240, 224, 184), (224, 204, 160), (200, 176, 136), (168, 144, 112)]

def ground(fl, t, m):
    """The ground at pixel level: cell materials from the plan, the canal, lake and cycleway
    from its masks."""
    from scipy import ndimage
    t = G.textures(t)
    ys, xs = np.mgrid[0:H * 16, 0:W * 16]
    cell = np.array(fl)
    px = lambda k: k.repeat(16, 0).repeat(16, 1)
    out = G.tile(t['grass'], ys, xs).copy()
    out[px(cell == 'pave')] = G.tile(t['tama_yuka'], ys, xs)[px(cell == 'pave')]
    out[px(cell == 'brick')] = G.tile(t['tama_yuka2'], ys, xs)[px(cell == 'brick')]
    kc, _ = G.kerb_cell(t, False)
    for y, x in zip(*np.nonzero(cell == 'kerb')):
        c = kc.copy(); c[:3] = G.tile(t['tama_yuka2'], ys, xs)[y * 16:y * 16 + 3, x * 16:x * 16 + 16]
        out[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = c
    rnd = (np.sin(xs * 12.9898 + ys * 78.233) * 43758.5453) % 1
    gm = px(cell == 'gravel')
    g = np.full((H * 16, W * 16, 3), GRAVEL[1], np.uint8)
    g[rnd > 0.93] = GRAVEL[0]; g[(rnd > 0.88) & (rnd < 0.9)] = GRAVEL[2]; g[(rnd > 0.86) & (rnd < 0.865)] = GRAVEL[3]
    out[gm] = g[gm]
    lawnfloor = np.where(np.isin(cell, GRASSY + ('garden',)), 'grass', np.where(cell == 'water', 'water', 'pave'))
    G.lawn_edges(out, lawnfloor)
    # The cycleway: teal surface, white edge lines, a dashed centre line along the curve.
    cyc = m['cycle'] & ~px(cell == 'bridge')
    lo, hi = PL.CYCLE_OFFSET
    out[cyc] = CYCLE[1]
    d = m['dist']
    out[cyc & ((d < lo + 2) | (d > hi - 2))] = LINE
    out[cyc & (((d >= lo + 2) & (d < lo + 4)) | ((d <= hi - 2) & (d > hi - 4)))] = CYCLE[2]
    mid = (lo + hi) / 2
    out[cyc & (np.abs(d - mid) < 1) & ((m['along'] // 6) % 2 == 0)] = LINE
    # The canal and lake: water from their shape, a stone quay round them.
    wat = m['water']
    dd = ndimage.distance_transform_cdt(wat, metric='chessboard')
    water = G.tile(t['pond_on'][0:16, 0:16], ys, xs)
    out[wat] = water[wat]
    out[wat & (dd <= 6) & (dd > 3)] = G.WATER[4]
    out[wat & (dd == 3)] = QUAY[3]
    out[wat & (dd == 2)] = QUAY[2]
    out[wat & (dd == 1)] = QUAY[0]
    out[wat & (dd == 1) & (((xs + ys) % 12) == 0)] = QUAY[2]
    # Painted bicycles every 12 cells along the cycleway.
    bike = bike_icon()
    line = PL.spline(PL.CANAL, 0.01) * 16
    run = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(line, axis=0).T))])
    for k in range(len(line) - 1):
        if int(run[k] // (16 * 12)) != int(run[k + 1] // (16 * 12)):
            (x0, y0), (x1, y1) = line[k], line[k + 1]
            tx, ty = (x1 - x0), (y1 - y0)
            n = np.hypot(tx, ty) or 1
            nx, ny = -ty / n * PL.CYCLE_SIDE, tx / n * PL.CYCLE_SIDE
            X, Y = int(x0 + nx * mid) - 8, int(y0 + ny * mid) - 4
            if 0 <= Y < H * 16 - 9 and 0 <= X < W * 16 - 16 and cyc[Y + 4, X + 8]:
                put(out, bike, X, Y)
    for y in range(H):
        for x in range(W):
            if cell[y, x] in ('meadow', 'garden') and h('flower', x, y) % (2 if cell[y, x] == 'garden' else 7) == 0:
                put(out, t[('flower01', 'flower02', 'flower03')[h('kind', x, y) % 3]], x * 16, y * 16)
    return out

def put(dst, img, X, Y):
    C.put(dst, img, X, Y)

def bike_icon():
    rows = ["..........ww....", "....w.....w.....", "...www...www....", ".wwww.www..w....",
            "w...ww.....ww...", "w..w.w....w..w..", "w...w....w....w.", ".www.....w....w.",
            "..........wwww.."]
    return C.art(rows, dict(w=LINE))

# --------------------------------------------------------------------------- trees
def trees(fl, t, taken):
    cell = np.array(fl)
    round_ = Pr.tree(t)
    blossom = round_.copy()
    a = blossom[..., 3] > 0
    crown = a & (np.arange(48)[:, None] < 38) & (blossom[..., 1].astype(int) > blossom[..., 0].astype(int) + 10)
    lum = blossom[..., :3].astype(int).sum(-1)
    pink = np.array([(255, 208, 224), (248, 168, 200), (224, 120, 168), (176, 80, 128)], np.uint8)
    q = np.digitize(lum, [180, 280, 380])
    blossom[crown, :3] = pink[3 - q[crown]]
    conifer = cherrygrove_tree()
    items = []
    free = lambda x, y: all(0 <= xx < W and 0 <= yy < H and cell[yy, xx] in ('forest',) and not taken[yy, xx]
                            for xx in (x, x + 1) for yy in (y, y + 1))
    for y in range(0, H - 1, 2):
        for x in range(0, W - 1, 2):
            if free(x, y):
                items.append((x * 16, (y + 2) * 16 - 48, round_))
    # Arboretum groves: on meadow 2x2 blocks off the walks and the water, a mix of kinds
    meadow = lambda x, y: all(0 <= xx < W and 0 <= yy < H and cell[yy, xx] == 'meadow' and not taken[yy, xx]
                              for xx in (x, x + 1) for yy in (y - 1, y, y + 1))
    for y in range(40, H - 1, 2):
        for x in range(0, W - 1, 2):
            if meadow(x, y) and h('grove', x, y) % 5 < 3:
                kind = (round_, conifer, blossom)[h('kind', x, y) % 3]
                items.append((x * 16, (y + 2) * 16 - 48, kind))
    return items

def cherrygrove_tree():
    import importlib.util
    spec = importlib.util.spec_from_file_location('olv_el', C.OLIVINE / 'elements.py')
    m = importlib.util.module_from_spec(spec)
    sys.modules['olv_el'] = m
    try:
        spec.loader.exec_module(m)
        return m.cherrygrove_tree(Path('/home/user/pokeemerald-expansion'))
    except Exception:
        return Pr.tree(C.textures())

# --------------------------------------------------------------------------- buildings
SCALES = dict(services=23.0, gamecorner=22.0)
COTTAGES = dict(cottage_red=297, cottage_green=316, cottage_orange=298, cottage_teal=41)

def buildings(models):
    sp = Bd.spec()
    out = {}
    for n in ('services', 'tower', 'hotel', 'gamecorner', 'prize', 'cafe'):
        retex = None
        out[n], _ = G3.convert(models, sp[n][0], scale=SCALES.get(n, G3.SCALE))
    out['gamecorner'] = A.casino_lights(out['gamecorner'])
    for n, mid in COTTAGES.items():
        out[n], _ = G3.convert(models, [(mid, (0, 0, 0))])
    return out

BRIDGE_ROADS = dict(main_west=('ew', 17, 22), main_east=('ew', 17, 22), cross=('ew', 36, 40), east=('ew', 30, 33),
                    arboretum=('ns', 44, 46), island=('ns', 40, 42))

def bridge_span(m, name):
    """Where a street crosses the water: the street's band, and the water's extent along it
    near the plan's bridge, widened a cell for the abutments."""
    (x0, y0, x1, y1), _ = PL.BRIDGES[name]
    way, a, b = BRIDGE_ROADS[name]
    wat = m['water'].reshape(H, 16, W, 16).mean(axis=(1, 3)) > 0.05
    if way == 'ew':
        cols = [x for x in range(x0 - 2, x1 + 2) if wat[a:b, x].any()]
        return (min(cols) - 1, a, max(cols) + 2, b), way
    rows = [y for y in range(y0 - 2, y1 + 2) if wat[y, a:b].any()]
    return (a, min(rows) - 1, b, max(rows) + 2), way

def bridge_art(x0, y0, x1, y1, way, deck_tex):
    """A Gen 3 stone bridge. The deck carries the street's own paving; balustrades (a lit rail
    on stout posts) run along both sides the water passes; on an east-west bridge the south
    side shows its face, an arch over the water, down to the waterline."""
    w, hgt = (x1 - x0) * 16, (y1 - y0) * 16
    S = A.STONE
    if way == 'ew':
        img = np.zeros((hgt + 14, w, 4), np.uint8)
        img[:hgt, :, :3] = deck_tex[y0 * 16:y1 * 16, x0 * 16:x1 * 16]; img[:hgt, :, 3] = 255
        for Y in (0, hgt - 6):                                     # balustrades
            img[Y:Y + 6, :, :3] = S[1]; img[Y:Y + 6, :, 3] = 255
            img[Y:Y + 2, :, :3] = S[0]
            img[Y + 5, :, :3] = S[3]
            for xx in range(4, w - 2, 8):
                img[Y + 2:Y + 5, xx:xx + 3, :3] = S[2]
                img[Y + 2:Y + 5, xx, :3] = S[0]
        face = img[hgt:hgt + 14]                                  # the south face with its arch
        face[..., :3] = S[2]; face[..., 3] = 255
        face[0:2, :, :3] = S[3]
        for xx in range(0, w, 8):
            face[2:, xx, :3] = S[3]
        cx, rx = w / 2, max(16.0, w / 2 - 14)
        for yy in range(2, 14):
            for xx in range(w):
                if ((xx + 0.5 - cx) / rx) ** 2 + ((14 - yy) / 11) ** 2 <= 1:
                    face[yy, xx, :3] = (40, 72, 136)
                    if ((xx + 0.5 - cx) / (rx - 2)) ** 2 + ((14 - yy) / 9) ** 2 > 1:
                        face[yy, xx, :3] = S[3]
        A.outline(img)
        return img, 0
    img = np.zeros((hgt, w, 4), np.uint8)
    img[..., :3] = S[1]; img[..., 3] = 255
    for yy in range(0, hgt, 4):
        img[yy, :, :3] = S[2]                                     # planks of a footbridge
    for X in (0, w - 6):
        img[:, X:X + 6, :3] = S[1]
        img[:, X:X + 2, :3] = S[0]
        img[:, X + 5, :3] = S[3]
        for yy in range(2, hgt - 2, 8):
            img[yy:yy + 3, X + 2:X + 5, :3] = S[2]
    A.outline(img)
    return img, 0

def compose(phg):
    t = C.textures()
    m = PL.masks()
    fl = PL.floors(m)
    out = ground(fl, t, m)
    _, _, models, _, _ = C.load(str(phg))
    art = buildings(models)
    taken = np.zeros((H, W), bool)
    items = []
    paving = G.tile(G.textures(t)['tama_yuka'], *np.mgrid[0:H * 16, 0:W * 16])
    for name in PL.BRIDGES:
        (x0, y0, x1, y1), way = bridge_span(m, name)
        b, _ = bridge_art(x0, y0, x1, y1, way, paving)
        items.append((x0 * 16, y0 * 16, b, -1))                   # drawn flat, before anything that stands
    c06 = np.array(Image.open(C.SRC / 'shared-art/pokemon-center.png').convert('RGBA'))
    sprites = dict(art, center=c06, fountain=A.fountain(), conservatory=A.conservatory())
    for name, kind, x, base in PL.PLACES:
        img = sprites[kind]
        items.append((x * 16, (base + 1) * 16 - img.shape[0], img))
        y0 = max(0, (base + 1) - img.shape[0] // 16 - 1)
        taken[y0:base + 2, max(0, x - 1):x + img.shape[1] // 16 + 1] = True
        if kind == 'gamecorner':
            m = A.marquee()
            items.append((x * 16 + (img.shape[1] - m.shape[1]) // 2, (base + 1) * 16 - img.shape[0] - 14, m))
    for x, base, colour in PL.STALLS:
        s = A.stall(colour)
        items.append((x * 16, (base + 1) * 16 - s.shape[0], s))
    lamp = A.lamp()
    for x, base in LAMPS:
        items.append((x * 16, (base + 1) * 16 - lamp.shape[0], lamp))
    bench, planter = A.bench(), A.planter(Pr.tree(t))
    for x, base in BENCHES:
        items.append((x * 16 + 4, (base + 1) * 16 - bench.shape[0], bench))
    for x, base in PLANTERS:
        items.append((x * 16, (base + 1) * 16 - planter.shape[0], planter))
        taken[base - 2:base + 1, x:x + 2] = True
    items += trees(fl, t, taken)
    items = [it if len(it) == 4 else it + (0,) for it in items]
    items.sort(key=lambda it: (it[3], it[1] + it[2].shape[0], it[0]))
    for X, Y, img, _ in items:
        put(out, img, X, Y)
    return out

BENCHES = [(12, 29), (19, 29), (33, 34), (40, 34), (47, 34), (8, 45), (16, 45), (30, 53), (50, 53), (60, 56), (74, 56)]
PLANTERS = [(32, 25), (42, 25), (50, 25), (54, 25), (52, 34), (36, 34)]
LAMPS = [(11, 29), (22, 29), (11, 23), (22, 23)] + [(23, y) for y in (26, 33, 44)] + [(63, y) for y in (26, 40)] + \
        [(x, 21) for x in (8, 30, 50, 66, 76)] + [(x, 52) for x in (30, 46, 56)] + [(9, 48), (16, 52)]

LABELS = [('Market Services (Dept Store)', 12, 6), ('Apartments', 29, 6), ('Pokemon Hotel', 35, 6), ('Center', 44, 10),
          ('Canal', 24, 1), ('Market', 10, 23), ('Game Corner', 31, 22), ('Prize', 46, 25), ('Cafe', 31, 39),
          ('Cottages', 64, 24), ('Cottages', 36, 39), ('Arboretum', 6, 44), ('Conservatory', 6, 53),
          ('Arboretum', 44, 53), ('Cycleway', 4, 40), ('to Route 16 (Cycling Road)', 0, 37), ('to Route 7', 76, 18),
          ('Bridge', 24, 22), ('Bridge', 58, 22), ('Bridge', 24, 40), ('Bridge', 44, 46), ('Bridge', 58, 34), ('Pond', 31, 58)]

def main(phg):
    OUT.mkdir(parents=True, exist_ok=True)
    pic = compose(phg)
    Image.fromarray(pic).save(OUT / 'concept.png')
    big = Image.fromarray(pic).resize((W * 32, H * 32), Image.Resampling.NEAREST)
    big.save(OUT / 'concept-2x.png')
    plot = Image.fromarray(pic).convert('RGBA')
    d = ImageDraw.Draw(plot)
    for txt, x, y in LABELS:
        tw = 6 * len(txt) + 4
        d.rectangle((x * 16, y * 16, x * 16 + tw, y * 16 + 12), fill=(0, 0, 0, 200))
        d.text((x * 16 + 2, y * 16), txt, fill=(255, 255, 120))
    plot.save(OUT / 'plot.png')
    print('concept written', pic.shape)

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
