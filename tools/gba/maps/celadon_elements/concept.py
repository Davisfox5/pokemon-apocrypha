"""Concept render of the plan (plan.py) with its real art, for the owner's call (round 6).

    python3 tools/gba/maps/celadon_elements/concept.py

The ground is Kanto's own (nature.py): FireRed's grass, Viridian Forest's dirt for the walks,
and wherever grass meets anything else (dirt, paving, brick, the cycleway, the pond's coping)
FireRed's path edge laid over it quadrant by quadrant; HGSS's hexagon paving and terrace brick
for the streets; the straight canal and its pond with stone quays; the cycleway. Trees are the
games' own (Hoenn's round tree, Kanto's cone tree, Viridian Forest's great tree, Fortree's
palm), flowers Gen 3's own in their colours. Buildings are HGSS's Celadon models brought down
to Gen 3 at 45 degrees (hgss_gen3.py); the Game Corner is round 5's drawing without its
lettering; the C06 Center; the stalls drawn at the same pitch (custom_art.stall3d); Olivine's
lamps and Hoenn's secret base plants (borrowed.py). Writes evidence/v6/concept.png,
concept-2x.png, plot.png and art.png.
"""
from __future__ import annotations
import hashlib, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

import common as C
import ground as G
import props as Pr
import custom_art as A
import gen3_kit as K
import borrowed as B
import plan as PL
import nature as N
import hgss_gen3 as H6

W, H = PL.W, PL.H
G.W, G.H = W, H                     # ground.py's helpers work on the plan's size
OUT = C.EV / 'v6'

def h(*a):
    return int(hashlib.md5(' '.join(map(str, a)).encode()).hexdigest(), 16)

def put(dst, img, X, Y):
    C.put(dst, img, int(X), int(Y))

# --------------------------------------------------------------------------- ground
QUAY = [(240, 236, 216), (208, 200, 176), (160, 152, 136), (112, 108, 104), (80, 80, 88)]
CYCLE = [(112, 200, 192), (80, 168, 160), (56, 136, 136), (40, 104, 112)]
LINE = (248, 248, 232)
KERB = [(216, 216, 208), (168, 168, 160), (120, 120, 120)]
GRAVEL = [(240, 224, 184), (224, 204, 160), (200, 176, 136), (168, 144, 112)]
MEADOW = (99, 189, 140)

def px_mask(cells):
    return cells.repeat(16, 0).repeat(16, 1)

def water_mask(cell):
    wat = px_mask(cell == 'water') | px_mask(cell == 'bridge')
    # the pond's corners rounded a little (Gen 3 ponds turn their corners in a cell's quarter)
    x0, y0, x1, y1 = (v * 16 for v in PL.POND)
    r = 10
    ys, xs = np.mgrid[0:H * 16, 0:W * 16]
    for cx, cy in ((x0 + r, y1 - r), (x1 - r, y1 - r)):
        corner = ((xs < x0 + r) if cx == x0 + r else (xs >= x1 - r)) & (ys >= y1 - r) & (ys < y1)
        wat &= ~(corner & ((xs + 0.5 - cx) ** 2 + (ys + 0.5 - cy) ** 2 > r * r))
    for cx, cy in ((x0 + r, y0 + r),):
        corner = (xs < x0 + r) & (ys >= y0) & (ys < y0 + r)
        wat &= ~(corner & ((xs + 0.5 - cx) ** 2 + (ys + 0.5 - cy) ** 2 > r * r))
    corner = (xs >= x1 - r) & (ys >= y0) & (ys < y0 + r)
    wat &= ~(corner & ((xs + 0.5 - (x1 - r)) ** 2 + (ys + 0.5 - (y0 + r)) ** 2 > r * r))
    return wat

def ground(fl, t):
    t = G.textures(t)
    ys, xs = np.mgrid[0:H * 16, 0:W * 16]
    cell = np.array(fl)
    gr = N.grass()
    out = np.zeros((H * 16, W * 16, 3), np.uint8)
    for y in range(H):
        for x in range(W):
            k = h('grass', x, y) % 10
            out[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = gr[0 if k < 8 else k - 7]
    grass_px = out.copy()
    for k, tex in (('pave', 'tama_yuka'), ('bridge', 'tama_yuka'), ('cycle', 'tama_yuka'), ('brick', 'tama_yuka2')):
        m = px_mask(cell == k)
        out[m] = G.tile(t[tex], ys, xs)[m]
    kc, _ = G.kerb_cell(t, False)
    for y, x in zip(*np.nonzero(cell == 'kerb')):
        c = kc.copy(); c[:3] = G.tile(t['tama_yuka2'], ys, xs)[y * 16:y * 16 + 3, x * 16:x * 16 + 16]
        out[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = c
    gm = px_mask(cell == 'gravel')
    out[gm] = N.dirt_texture(H, W)[gm]
    cycleway(out)
    pre = out.copy()
    water(out, cell)
    deck = px_mask(cell == 'bridge')
    out[deck] = pre[deck]                                   # the streets run on over their bridges
    grassy = np.isin(cell, ('forest', 'meadow', 'lawn', 'grass', 'garden'))
    N.grass_edges(out, ~grassy, grass_px)
    fl_ = list(N.flowers().values())
    for y in range(H):
        for x in range(W):
            if (cell[y, x] == 'garden' and h('bed', x, y) % 10 < 7) or (cell[y, x] == 'meadow' and h('flower', x, y) % 7 == 0):
                put(out, fl_[h('kind', x, y) % len(fl_)], x * 16, y * 16)
    return out

def cycleway(out):
    """Two lanes in teal between white edge lines, a grey kerb on the road side, a dashed
    centre line, a bicycle painted every ten cells; the runs meet square at the corners."""
    m = np.zeros((H * 16, W * 16), bool)
    for x0, y0, x1, y1 in PL.CYCLE:
        m[y0 * 16:y1 * 16, x0 * 16:x1 * 16] = True
    pad = 40                                                # the map's own edge is not a kerb: the lanes run on
    d = ndimage.distance_transform_cdt(np.pad(m, pad, mode='edge'), metric='chessboard')[pad:-pad, pad:-pad]
    ys, xs = np.mgrid[0:H * 16, 0:W * 16]
    out[m] = CYCLE[1]
    out[m & (d <= 2)] = KERB[1]
    out[m & (d == 1)] = KERB[2]
    out[m & (d == 2) & ((xs + ys) % 8 == 0)] = KERB[0]
    out[m & ((d == 4) | (d == 5))] = LINE
    out[m & (d == 6)] = CYCLE[2]
    out[m & ((d == 3))] = CYCLE[3]
    out[m & (d >= 15) & ((((xs + ys) // 8) % 2) == 0)] = LINE
    # texture: a fine speckle in the surface
    rnd = (np.sin(xs * 7.13 + ys * 91.7) * 43758.5453) % 1
    out[m & (d > 6) & (d < 15) & (rnd > 0.96)] = CYCLE[0]
    bike = bike_icon()
    for x0, y0, x1, y1 in PL.CYCLE:
        horiz = (x1 - x0) > (y1 - y0)
        if horiz:
            for X in range(x0 * 16 + 40, x1 * 16 - 24, 160):
                put(out, bike, X, y0 * 16 + 4); put(out, bike, X + 64, y0 * 16 + 20)
        else:
            for Y in range(y0 * 16 + 48, y1 * 16 - 40, 160):
                put(out, bike, x0 * 16 + 8, Y)

def bike_icon():
    rows = ["..........ww....", "....w.....w.....", "...www...www....", ".wwww.www..w....",
            "w...ww.....ww...", "w..w.w....w..w..", "w...w....w....w.", ".www.....w....w.",
            "..........wwww.."]
    rows = [r[:15] for r in rows]
    return C.art(rows, dict(w=LINE))

def water(out, cell):
    """The canal and pond: HGSS's water, the north quay's wall face, coping round every edge,
    the deep shade along the west and north walls."""
    t = C.textures()
    wat = water_mask(cell)
    ys, xs = np.mgrid[0:H * 16, 0:W * 16]
    tex = G.tile(t['pond_on'][0:16, 0:16], ys, xs)
    out[wat] = tex[wat]
    land = ~wat
    def dist(dy, dx, n):
        """1 + how many pixels this water pixel lies from land in direction (dy, dx), up to n."""
        r = np.full(wat.shape, n + 1)
        P = n + 1
        padded = np.pad(land, P, mode='edge')               # past the map's edge the water runs on
        for k in range(n, 0, -1):
            sh = padded[P - dy * k:P - dy * k + land.shape[0], P - dx * k:P - dx * k + land.shape[1]]
            r[wat & sh] = k
        return r
    top, left, right, bot = dist(1, 0, 10), dist(0, 1, 6), dist(0, -1, 6), dist(-1, 0, 6)
    side = np.minimum(left, right)
    out[wat & (left <= 6)] = G.WATER[4]
    out[wat & (top <= 10)] = G.WATER[4]
    face = wat & (top <= 8) & (side > 3)
    out[face] = QUAY[3]
    out[face & ((top == 1) | (top == 2))] = QUAY[1]
    out[face & (top == 8)] = QUAY[4]
    out[face & ((xs // 8 + (top > 4)) % 2 == 0) & ((xs % 8) == 0)] = QUAY[4]          # the wall's blocks
    out[face & (top == 5)] = QUAY[4]
    cope = wat & (side <= 3) & (top > 0)
    out[cope] = QUAY[1]
    out[wat & (side == 1)] = QUAY[0]
    out[wat & (side == 3)] = QUAY[3]
    low = wat & (bot <= 3)
    out[low] = QUAY[1]; out[wat & (bot == 1)] = QUAY[2]; out[wat & (bot == 3) & (side > 3)] = QUAY[0]
    out[cope & (((ys // 12) % 2 == 0) & ((ys % 12) == 0))] = QUAY[3]

def bridge_art(name):
    """A Gen 3 stone bridge over the canal: the street's deck runs on over it (already in the
    ground), balustrades along its north and south edges over the water, the south face below
    the deck with its arch down to the water. The Arboretum's is a timber footbridge."""
    (bx0, by0, bx1, by1), way = PL.BRIDGES[name]
    x0, x1 = PL.CANAL[0] * 16 - 3, PL.CANAL[2] * 16 + 3
    w = x1 - x0
    dh = (by1 - by0) * 16
    img = np.zeros((dh + 14, w, 4), np.uint8)
    S = QUAY
    timber = name == 'arboretum'
    if timber:
        WD = A.WOOD
        img[:dh, :, :3] = WD[1]; img[:dh, :, 3] = 255
        for X in range(0, w, 6):
            img[:dh, X, :3] = WD[3]
            img[:dh, X + 1, :3] = WD[0]
    for Y in (0, dh - 6):
        R = A.WOOD if timber else S
        img[Y:Y + 6, :, :3] = R[1]; img[Y:Y + 6, :, 3] = 255
        img[Y:Y + 2, :, :3] = R[0]
        img[Y + 5, :, :3] = R[3]
        for xx in range(3, w - 2, 7):
            img[Y + 2:Y + 5, xx:xx + 3, :3] = R[2]
            img[Y + 2:Y + 5, xx, :3] = R[0]
    face = img[dh:dh + 14]
    face[..., :3] = (A.WOOD if timber else S)[2]; face[..., 3] = 255
    face[0:2, :, :3] = (A.WOOD if timber else S)[3]
    if not timber:
        for xx in range(0, w, 8):
            face[2:, xx, :3] = S[3]
        cx, rx = w / 2, w / 2 - 9
        for yy in range(2, 14):
            for xx in range(w):
                if ((xx + 0.5 - cx) / rx) ** 2 + ((14 - yy) / 11) ** 2 <= 1:
                    face[yy, xx, :3] = (40, 72, 136)
                    if ((xx + 0.5 - cx) / (rx - 2)) ** 2 + ((14 - yy) / 9) ** 2 > 1:
                        face[yy, xx, :3] = S[3]
    else:
        face[2:, :, :3] = (40, 72, 136)
        for xx in (2, w // 2 - 1, w - 4):
            face[:, xx:xx + 3, :3] = A.WOOD[3]
    A.outline(img)
    return img, x0, by0 * 16

# --------------------------------------------------------------------------- trees
def trees(fl, taken):
    """The forest round the town in Hoenn's and Kanto's trees; the Arboretum's groves in all
    four, Viridian Forest's great trees and Fortree's palms among them."""
    cell = np.array(fl)
    T = N.trees()
    items = []
    def free(x, y, w, hh, kinds):
        return all(0 <= xx < W and 0 <= yy < H and cell[yy, xx] in kinds and not taken[yy, xx]
                   for xx in range(x, x + w) for yy in range(y, y + hh))
    def place(x, y, img):
        w, hh = img.shape[1] // 16, img.shape[0] // 16
        items.append((x * 16, (y + hh) * 16 - img.shape[0], img))
        taken[y:y + hh, x:x + w] = True
    for y in range(36, H - 1):                             # the Arboretum: its great trees and palms first,
        for x in range(4, W - 1):                          # then the round and cone trees between them
            k = h('grove', x, y) % 9
            img = T['viridian'] if k < 2 else T['palm'] if k == 2 else None
            if img is not None and free(x, y, img.shape[1] // 16, img.shape[0] // 16, ('meadow',)):
                place(x, y, img)
    for y in range(36, H - 1):
        for x in range(4, W - 1):
            k = h('small', x, y) % 10
            img = T['hoenn'] if k < 5 else T['kanto'] if k < 9 else None
            if img is not None and free(x, y, 2, 2, ('meadow',)):
                place(x, y, img)
    for y in range(0, H - 1, 2):
        for x in range(0, W - 1, 2):
            if free(x, y, 2, 2, ('forest',)):
                place(x, y, T['hoenn'] if h('wood', x, y) % 3 else T['kanto'])
    return items

# --------------------------------------------------------------------------- the picture
def sprites():
    c06 = np.array(Image.open(C.SRC / 'shared-art/pokemon-center.png').convert('RGBA'))
    m = H6.models()
    s = dict(dept_store=H6.dept_store(m), apartments=H6.apartments(m), hotel=H6.hotel(m), prize_corner=H6.prize_corner(m),
             cafe=H6.cafe(m), flat=H6.flat(m), game_corner=K.game_corner(), center=c06, fountain=A.fountain(),
             blossom_pool=A.blossom_pool())
    base = H6.convert(m, 'house', H6.HOUSE_SCALE)
    for colour in H6.HUES:
        s['house_' + colour] = H6.house(m, colour, base)
    return s

def compose():
    t = C.textures()
    fl = PL.floors()
    out = ground(fl, t)
    taken = np.zeros((H, W), bool)
    items = []
    cell = np.array(fl)
    taken |= cell == 'water'
    for name in PL.BRIDGES:
        b, X, Y = bridge_art(name)
        items.append((X, Y, b, -1))
    sp = sprites()
    for name, kind, x, base in PL.PLACES:
        img = sp[kind]
        X, Y = int(round(x * 16)), int((base + 1) * 16) - img.shape[0]
        items.append((X, Y, img))
        taken[max(0, int(base) - 3):int(base) + 2, max(0, int(x)):int(x) + (img.shape[1] + 15) // 16] = True   # trees may stand behind
    for x, base, colour, facing in PL.STALLS:
        s = A.stall3d(colour, facing)
        items.append((int(x * 16), (base + 1) * 16 - s.shape[0], s))
    lamp = B.olivine_lamp()
    for x, base in PL.LAMPS:
        items.append((x * 16 + (16 - lamp.shape[1]) // 2, (base + 1) * 16 - lamp.shape[0], lamp))
        taken[max(0, base - 2):base + 1, x] = True
    bench = A.plant_bench()
    for x, base in PL.BENCHES:
        items.append((x * 16 - 8, (base + 1) * 16 - bench.shape[0], bench))
        taken[base - 1:base + 1, x - 1:x + 3] = True
    plants = B.plants()
    for kind, x, base in PL.PLANTS:
        p = plants[kind]
        items.append((x * 16, (base + 1) * 16 - p.shape[0], p))
        taken[base - 1:base + 1, x:x + p.shape[1] // 16] = True
    items += trees(fl, taken)
    items = [it if len(it) == 4 else it + (0,) for it in items]
    items.sort(key=lambda it: (it[3], it[1] + it[2].shape[0], it[0]))
    for X, Y, img, _ in items:
        put(out, img, X, Y)
    return out

LABELS = [('Dept Store', 5, 3), ('Apartments', 25, 3), ('Pokemon Hotel', 33, 3), ('Center', 43, 8), ('Canal', 20, 1),
          ('Houses', 50, 9), ('Market square', 9, 26), ('Game Corner', 27, 23), ('Prize corner', 39, 24),
          ('Houses (terrace)', 45, 22), ('Cafe', 45, 30), ('Houses', 51, 30), ('Arboretum', 4, 43), ('Arboretum', 48, 46),
          ('Blossom pool', 37, 46), ('Pond', 16, 45), ('Promenade', 26, 40), ('Cycleway', 40, 19), ('Cycleway', 4, 26),
          ('to Route 16 / Cycling Road', 0, 36), ('to Route 7 / Saffron', 52, 17), ('Bridge', 20, 16), ('Bridge', 20, 34),
          ('Footbridge', 20, 42)]

def art_sheet():
    """Every new piece at 1:1 on one sheet, for review."""
    sp = sprites()
    T, F, P = N.trees(), N.flowers(), B.plants()
    rows = [[sp[k] for k in ('dept_store', 'apartments', 'hotel', 'center', 'game_corner')],
            [sp[k] for k in ('prize_corner', 'cafe', 'flat')] + [sp['house_' + c] for c in H6.HUES],
            [A.stall3d('red'), A.stall3d('blue'), A.stall3d('green', 'east'), A.stall3d('violet', 'west'), sp['fountain'],
             sp['blossom_pool'], A.plant_bench(), B.olivine_lamp()] + list(T.values()),
            list(F.values()) + list(P.values())]
    W_ = max(sum(p.shape[1] + 8 for p in r) + 8 for r in rows)
    H_ = sum(max(p.shape[0] for p in r) + 12 for r in rows) + 8
    s = np.zeros((H_, W_, 4), np.uint8); s[..., :3] = N.grass()[0][0, 0]; s[..., 3] = 255
    y = 8
    for r in rows:
        rh = max(p.shape[0] for p in r)
        x = 8
        for p in r:
            put(s, p, x, y + rh - p.shape[0])
            x += p.shape[1] + 8
        y += rh + 12
    return s

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pic = compose()
    Image.fromarray(pic).save(OUT / 'concept.png')
    Image.fromarray(pic).resize((W * 32, H * 32), Image.Resampling.NEAREST).save(OUT / 'concept-2x.png')
    plot = Image.fromarray(pic).convert('RGBA')
    d = ImageDraw.Draw(plot)
    for txt, x, y in LABELS:
        tw = 6 * len(txt) + 4
        d.rectangle((x * 16, y * 16, x * 16 + tw, y * 16 + 12), fill=(0, 0, 0, 200))
        d.text((x * 16 + 2, y * 16), txt, fill=(255, 255, 120))
    plot.save(OUT / 'plot.png')
    a = art_sheet()
    Image.fromarray(a).resize((a.shape[1] * 2, a.shape[0] * 2), Image.Resampling.NEAREST).save(OUT / 'art.png')
    print('concept written', pic.shape)

if __name__ == '__main__':
    main()
