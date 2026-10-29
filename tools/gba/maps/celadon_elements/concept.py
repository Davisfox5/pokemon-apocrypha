"""Concept render of the plan (plan.py) with its real art, for the owner's call (round 6).

    python3 tools/gba/maps/celadon_elements/concept.py

The ground is Kanto's own (nature.py): FireRed's grass, Viridian Forest's dirt for the walks,
and wherever grass meets anything else (dirt, paving, brick, the cycleway, the pond's coping)
FireRed's path edge laid over it quadrant by quadrant; HGSS's hexagon paving and terrace brick
for the streets; the straight canal and its pond with stone quays; the cycleway. Trees are the
repo's own cut-outs (nature.TREE_ART: whole crowns, clear backgrounds), flowers Gen 3's own in
their colours; the bridges Route 104's boardwalk. Buildings are HGSS's Celadon models brought down
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

def px_rect(r):
    x0, y0, x1, y1 = r
    m = np.zeros((H * 16, W * 16), bool)
    m[y0 * 16:y1 * 16, x0 * 16:x1 * 16] = True
    return m

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
    wet = out.copy()
    grassy = np.isin(cell, ('forest', 'meadow', 'lawn', 'grass', 'garden'))
    N.grass_edges(out, ~grassy, grass_px)
    canal = water_mask(cell) & px_rect(PL.CANAL)
    out[canal] = wet[canal]                                 # the canal's seawall runs unbroken past the grass banks
    return out

def flowers(out, cell, covered):
    """Gen 3's flowers on the beds and here and there in the Arboretum's grass, only on cells
    no object stands over (covered: H x W, any object's pixel in the cell)."""
    fl_ = list(N.flowers().values())
    for y in range(H):
        for x in range(W):
            if covered[y, x]:
                continue
            if (cell[y, x] == 'garden' and h('bed', x, y) % 10 < 7) or (cell[y, x] == 'meadow' and h('flower', x, y) % 7 == 0):
                put(out, fl_[h('kind', x, y) % len(fl_)], x * 16, y * 16)

def cycleway(out):
    """Two lanes in teal between white edge lines, a grey kerb on the road side, a dashed
    centre line, and a few bicycles painted in the middle of the lanes (BIKE_MARKS); the runs
    meet square at the corners."""
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
    for (cx, cy) in BIKE_MARKS:                                # a few painted bicycles in the middle of the lanes
        stamp_bike(out, cx, cy)

BIKE_MARKS = [(13 * 16, 20 * 16), (34 * 16, 20 * 16), (50 * 16, 20 * 16), (5 * 16, 28 * 16)]

def bike_emblem():
    """The cycleway's bicycle, 32 x 18: painted white in two-pixel strokes (two wheels, the
    frame, the seat and the bars), its outline a step darker than the lane, so it reads on the
    ground from across the street without shouting."""
    w, h = 30, 16
    a = np.zeros((h, w), bool)
    yy, xx = np.mgrid[0:h, 0:w]
    for cx in (6.5, 23.5):                                   # the wheels
        d = np.hypot(xx + 0.5 - cx, yy + 0.5 - 10.0)
        a |= (d <= 6.0) & (d >= 4.0)
    def line(x0, y0, x1, y1, t=1.0):
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 3) + 1
        for k in range(n + 1):
            x = x0 + (x1 - x0) * k / n; y = y0 + (y1 - y0) * k / n
            a[(np.hypot(xx + 0.5 - x, yy + 0.5 - y) <= t)] = True
    line(6.5, 10, 13, 10)                                    # chain stay
    line(13, 10, 10, 4)                                      # seat tube
    line(10, 4, 20, 4)                                       # top tube
    line(20, 4, 13, 10)                                      # down tube
    line(20, 4, 23.5, 10)                                    # fork
    line(18.5, 1.5, 21.5, 1.5, 0.8); line(20, 1.5, 20, 4, 0.8)   # the bars
    line(8, 2.5, 12, 2.5, 0.8)                               # the seat
    img = np.zeros((h + 2, w + 2, 4), np.uint8)
    A = np.pad(a, 1)
    p = np.pad(A, 1)
    ring = ~A & (p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:])
    img[ring, :3] = CYCLE[3]; img[ring, 3] = 255
    img[A, :3] = LINE; img[A, 3] = 255
    return img

def stamp_bike(out, cx, cy):
    """A bicycle centred at (cx, cy) on the lane, the dashes cleared round it."""
    e = bike_emblem()
    h_, w_ = e.shape[:2]
    clear = out[cy - 3:cy + 3, cx - w_ // 2 - 10:cx + w_ // 2 + 10]
    clear[np.all(clear == LINE, -1)] = CYCLE[1]
    put(out, e, cx - w_ // 2, cy - h_ // 2)

def paint_cycleway(deck, X, Y):
    """The cycleway painted across a bridge's planks: where its band crosses the deck, a flat
    coat of the lane's teal (lit a shade at its top edge, a shade darker at its foot), the
    boards' seams showing through it as fine darker lines the way paint lies on planks, and
    the white edge lines and dashed centre painted solid over it."""
    for x0, y0, x1, y1 in PL.CYCLE:
        if not (x1 - x0 > y1 - y0) or x1 * 16 <= X or x0 * 16 >= X + deck.shape[1]:
            continue                                         # an east-west run that crosses this deck
        r0, r1 = y0 * 16 - Y, y1 * 16 - Y
        if r1 <= 0 or r0 >= deck.shape[0]:
            continue
        band = deck[max(r0, 0):min(r1, deck.shape[0])]
        a = band[..., 3] > 0
        lum = band[..., :3].astype(int) @ [3, 4, 2]
        seam = a & (lum <= np.percentile(lum[a], 15))        # the boards' joints and grain, darkest in the wood
        band[a, :3] = CYCLE[1]
        band[seam, :3] = CYCLE[2]
        band[0, a[0], :3] = CYCLE[0]; band[-1, a[-1], :3] = CYCLE[3]
        for rr in (3, 4, band.shape[0] - 5, band.shape[0] - 4):
            band[rr, a[rr], :3] = LINE
        xs = np.arange(band.shape[1]) + X
        mid = band.shape[0] // 2
        for rr in (mid - 1, mid):
            m = a[rr] & (((xs + (y0 * 16 + rr)) // 8) % 2 == 0)
            band[rr, m, :3] = LINE

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

def ledge(xs):
    """The pond's stone ledge (RAIL rows of the wall face water() draws under land's south
    edge: its lit top, its block joints, its dark foot) for the columns xs, so a piece laid
    across the pond's edge carries the ledge on unbroken."""
    t = np.arange(1, B.RAIL + 1)[:, None]
    X = np.asarray(xs)[None]
    img = np.zeros((B.RAIL, X.shape[1], 3), np.uint8)
    img[...] = QUAY[3]
    img[np.broadcast_to((t == 1) | (t == 2), img.shape[:2])] = QUAY[1]
    img[np.broadcast_to(t == 8, img.shape[:2])] = QUAY[4]
    img[(((X // 8 + (t > 4)) % 2 == 0) & ((X % 8) == 0))] = QUAY[4]
    img[np.broadcast_to(t == 5, img.shape[:2])] = QUAY[4]
    return img

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
def trees(fl, taken, objects):
    """Whole trees (nature.trees) round the town and through the Arboretum.

    A tree's foot is its bottom two cells (trunk and lower crown); its crown rises over the
    cells above. The forest round the town stands in staggered rows two cells apart, each row
    shifted a cell from the one above, so every crown is whole and overlaps only the trunks
    behind it, all Cherrygrove's standard Kanto/Johto tree. The Arboretum's groves mix
    Floccesy's great trees, Cherrygrove's and Sandgem's cone tree. No tree is placed where its pixels would cover a
    lamp, bench, plant, stall, sign or fountain, or stand in front of a building."""
    cell = np.array(fl)
    T = N.trees()
    props = np.zeros((H * 16, W * 16), bool)
    fronts = np.full((H * 16, W * 16), -1, int)              # each building pixel: the building's foot row (px)
    for X, Y, img, layer in objects:
        if layer < 0:
            continue
        if img.shape[0] >= 64 and img.shape[1] >= 60:        # a building
            m = np.zeros_like(props); stamp(m, img, X, Y)
            fronts[m] = np.maximum(fronts[m], Y + img.shape[0])
        else:
            stamp(props, img, X, Y)
    items = []
    def fits(x, y, img, kinds):
        w = (img.shape[1] + 15) // 16
        edge_ok = 'forest' in kinds                          # the border runs on off the map's edges
        if not all(((0 <= xx < W and 0 <= yy < H) and cell[yy, xx] in kinds and not taken[yy, xx]) or
                   (edge_ok and not (0 <= xx < W and 0 <= yy < H))
                   for xx in range(x, x + w) for yy in range(y, y + 2)):
            return False
        X, Y = x * 16 + (w * 16 - img.shape[1]) // 2, (y + 2) * 16 - img.shape[0]
        m = np.zeros_like(props); stamp(m, img, X, Y)
        if (m & props).any():
            return False
        foot = (y + 2) * 16
        if (m & (fronts >= 0) & (fronts <= foot)).any():     # in front of a building: no
            return False
        return X, Y
    def place(x, y, img, kinds):
        at = fits(x, y, img, kinds)
        if not at:
            return False
        items.append((at[0], at[1], img))
        w = (img.shape[1] + 15) // 16
        taken[max(y, 0):y + 2, max(x, 0):x + w] = True
        return True
    grove = [T['grove_sun'], T['grove_shade'], T['johto'], T['johto'], T['sinnoh']]
    for y in range(36, H - 1):                             # the Arboretum: great trees first, then the rest
        for x in range(4, W - 2):
            if h('grove', x, y) % 7 < 2:
                place(x, y, grove[h('g', x, y) % 2], ('meadow',))
    for y in range(36, H - 1):
        for x in range(4, W - 1):
            if h('small', x, y) % 10 < 8:
                place(x, y, grove[2 + h('kind', x, y) % 3], ('meadow',))
    for y in range(0, H - 1, 2):                           # the forest, rows staggered
        for x in range((y // 2) % 2 - 1, W + 1, 2):
            place(x, y, T['johto'], ('forest',))   # the border: the standard Kanto/Johto tree only
    return items

# --------------------------------------------------------------------------- the picture
def sprites():
    c06 = np.array(Image.open(C.SRC / 'shared-art/pokemon-center.png').convert('RGBA'))
    m = H6.models()
    s = dict(dept_store=H6.dept_store(m), apartments=H6.apartments(m), hotel=H6.hotel(m), prize_corner=H6.prize_corner(m),
             cafe=H6.cafe(m), flat=H6.flat(m), game_corner=H6.game_corner(m), center=c06, fountain=A.fountain(),
             blossom_pool=A.blossom_pool())
    base = H6.convert(m, 'house', H6.HOUSE_SCALE)
    for colour in H6.HUES:
        s['house_' + colour] = H6.house(m, colour, base)
    return s

def compose(layers=False):
    """The concept picture; with layers, the ground (bridges, flowers and painted lanes in it)
    and every standing object as (X, Y, img, family, name), for the engine's packer."""
    t = C.textures()
    fl = PL.floors()
    out = ground(fl, t)
    taken = np.zeros((H, W), bool)
    items = []
    cell = np.array(fl)
    taken |= cell == 'water'
    for name, ((bx0, by0, bx1, by1), _) in PL.BRIDGES.items():
        X, Y = PL.CANAL[0] * 16, by0 * 16
        footpath = name == 'arboretum'                       # the promenade's footbridge: the pond's stone ledge for edging
        b = B.boardwalk27(by1 - by0, (PL.CANAL[2] - PL.CANAL[0]) * 16, north=not footpath, south=not footpath)
        if footpath:
            xs = np.arange(X, X + b.shape[1])
            b = np.concatenate([b, np.zeros((B.RAIL,) + b.shape[1:], np.uint8)])
            b[:B.RAIL, :, :3] = ledge(xs)                      # along its top, in place of the wood edging
            b[-B.RAIL:, :, :3] = ledge(xs)                     # along its foot, the pond's ledge carried across
            b[..., 3] = 255
        bare = b.copy()
        paint_cycleway(b, X, Y)
        painted = np.nonzero((b != bare).any((1, 2)))[0]
        if len(painted) and painted[-1] >= b.shape[0] - B.RAIL and not footpath:
            foot = painted[-1] - 2                               # the lane's lower white line ends 3 rows above the foot
            b[foot:] = bare[foot:]                               # the wood edging below the lane's white line
        items.append((X, Y, b, -1, 'bridge', 'bridge_' + name))
        if not footpath:
            sh = out[by1 * 16:by1 * 16 + 4, PL.CANAL[0] * 16:PL.CANAL[2] * 16]
            sh[(sh[..., 2] > 150) & (sh[..., 0] < 150)] = G.WATER[4]         # the bridge's shade on the water
    sp = sprites()
    for name, kind, x, base in PL.PLACES:
        img = sp[kind]
        X, Y = int(round(x * 16)), int((base + 1) * 16) - img.shape[0]
        items.append((X, Y, img, 0, kind if not kind.startswith('house_') else 'house', name))
        taken[max(0, int(base) - 3):int(base) + 2, max(0, int(x)):int(x) + (img.shape[1] + 15) // 16] = True   # trees may stand behind
    for x, base, colour, facing in PL.STALLS:
        s = A.stall3d(colour, facing)
        items.append((int(x * 16), (base + 1) * 16 - s.shape[0], s, 0, 'stall', f'stall_{int(x)}_{base}'))
    lamp = A.street_lamp()
    for x, base in PL.LAMPS:
        items.append((x * 16 + (16 - lamp.shape[1]) // 2, (base + 1) * 16 - lamp.shape[0], lamp, 0, 'lamp', f'lamp_{x}_{base}'))
        taken[max(0, base - 2):base + 1, x] = True
    bench = A.plant_bench()
    for x, base in PL.BENCHES:
        items.append((x * 16 - 8, (base + 1) * 16 - bench.shape[0], bench, 0, 'bench', f'bench_{x}_{base}'))
        taken[base - 1:base + 1, x - 1:x + 3] = True
    plants = B.plants()
    for kind, x, base in PL.PLANTS:
        p = plants[kind]
        items.append((x * 16, (base + 1) * 16 - p.shape[0], p, 0, 'plant', f'plant_{x}_{base}'))
        taken[base - 1:base + 1, x:x + p.shape[1] // 16] = True
    tagged = [it[:4] for it in items]
    names = [it[4:] for it in items]
    for X, Y, img in trees(fl, taken, tagged):                # layer 1: trees, for the checks only
        tagged.append((X, Y, img, 1)); names.append(('tree', f'tree_{X}_{Y}'))
    covered = np.zeros((H * 16, W * 16), bool)
    for X, Y, img, layer in tagged:
        if layer >= 0:
            stamp(covered, img, X, Y)
    flowers(out, cell, covered.reshape(H, 16, W, 16).any(axis=(1, 3)))
    overlaps(tagged)
    order = sorted(range(len(tagged)), key=lambda i: (tagged[i][3] < 0 and -1 or 0, tagged[i][1] + tagged[i][2].shape[0], tagged[i][0]))
    if layers:
        for i in order:
            if tagged[i][3] < 0:
                put(out, tagged[i][2], tagged[i][0], tagged[i][1])
        return dict(ground=out, cells=cell, objects=[tagged[i][:3] + names[i] for i in order if tagged[i][3] >= 0])
    for i in order:
        X, Y, img, _ = tagged[i]
        put(out, img, X, Y)
    return out

def stamp(mask, img, X, Y):
    h_, w_ = img.shape[:2]
    y0, x0, y1, x1 = max(Y, 0), max(X, 0), min(Y + h_, mask.shape[0]), min(X + w_, mask.shape[1])
    if y1 > y0 and x1 > x0:
        mask[y0:y1, x0:x1] |= img[y0 - Y:y1 - Y, x0 - X:x1 - X, 3] > 0

def overlaps(tagged):
    """Every pair of standing objects whose pixels overlap, but a tree behind a building or
    another tree (Gen 3's forests overlap; a building stands in front of the woods)."""
    objs = [(X, Y, img, layer) for X, Y, img, layer in tagged if layer >= 0]
    bad = []
    for i in range(len(objs)):
        for j in range(i + 1, len(objs)):
            (X1, Y1, a, l1), (X2, Y2, b, l2) = objs[i], objs[j]
            if l1 == 1 and l2 == 1:
                continue
            x0, y0 = max(X1, X2), max(Y1, Y2)
            x1, y1 = min(X1 + a.shape[1], X2 + b.shape[1]), min(Y1 + a.shape[0], Y2 + b.shape[0])
            if x1 <= x0 or y1 <= y0:
                continue
            ov = (a[y0 - Y1:y1 - Y1, x0 - X1:x1 - X1, 3] > 0) & (b[y0 - Y2:y1 - Y2, x0 - X2:x1 - X2, 3] > 0)
            if ov.any():
                foot1, foot2 = Y1 + a.shape[0], Y2 + b.shape[0]
                tree_behind = (l1 == 1 and foot1 <= foot2 and a.shape[0] <= b.shape[0] * 4) or (l2 == 1 and foot2 <= foot1)
                if (l1 == 1) != (l2 == 1) and tree_behind:
                    continue
                bad.append(((X1 // 16, foot1 // 16 - 1, a.shape), (X2 // 16, foot2 // 16 - 1, b.shape), int(ov.sum())))
    for b in bad:
        print('overlap', b)
    return bad

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
             sp['blossom_pool'], A.plant_bench(), A.street_lamp(), bike_emblem(), B.boardwalk27(3, 64)] + list(T.values()),
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
    frames = []                                              # the fountains' four frames, as the engine will cycle them
    for f in range(4):
        fr = np.zeros((80, 176, 4), np.uint8); fr[..., :3] = N.grass()[0][0, 0]; fr[..., 3] = 255
        put(fr, A.fountain(f), 4, 4); put(fr, A.blossom_pool(f), 92, 4)
        frames.append(Image.fromarray(fr).resize((176 * 4, 80 * 4), Image.Resampling.NEAREST))
    frames[0].save(OUT / 'fountains.gif', save_all=True, append_images=frames[1:], duration=160, loop=0)
    a = art_sheet()
    Image.fromarray(a).resize((a.shape[1] * 2, a.shape[0] * 2), Image.Resampling.NEAREST).save(OUT / 'art.png')
    print('concept written', pic.shape)

if __name__ == '__main__':
    main()
