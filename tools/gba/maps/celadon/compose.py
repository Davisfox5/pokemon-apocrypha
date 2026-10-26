"""Celadon City ten years on: FireRed's own Celadon, rebuilt for Apocrypha's story.

    python3 tools/gba/maps/celadon/compose.py ENGINE_CHECKOUT

FireRed's map (CeladonCity_Frlg: 60x40 on General_Frlg + CeladonCity) is the base, cell for
cell; HGSS's Celadon is the plan reference (letters A-G in evidence/plan.png). The owner's
approved plan (gba/art/celadon-kanto/README.md):

    1 market      Slateport's market tents (parts.tent_*) round the fountain lawn, which grows
                  a row north toward the store (HGSS B), one in the pocket west of the store,
                  produce baskets and crates on the east walk
    2 services    the Dept Store stands as FireRed draws it; its sign names the services
    3 gardens     on the gym's site: the gym's walls under a glass roof (parts.glass, the
                  porch's crest a leaf), a paved forecourt (HGSS F), Cerulean's hedges for the
                  gym's ledges, a north gate from the market where the west house stood
    4 hotel       the south row's last two houses made one hotel a floor taller (parts.hotel),
                  under one roof, with balconies and one shop entrance in the middle
    5 café        the house between the market and the gardens gains FireRed's house door
                  and the Bike Shop's striped awning (HGSS G)
    6 Game Corner kept as FireRed draws it
    7 bike lane   painted on the road from Route 7 to Route 16 in Celadon's teal
    8 canal       FireRed's pond carried south to the treeline as a canal (HGSS A), the Bond
                  Bridge's planks (parts.bridge) where the street crosses it

Every unchanged cell keeps its FireRed metatile. A cell any part draws in, or the lane paints,
is an art cell, packed from its pixels (pack.py).
Writes source/compose.npz and evidence/terrain.png, compare.png.
"""
from __future__ import annotations
import colorsys, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.append(str(HERE.parent / 'saffron'))
import frlg                                     # noqa: E402

ART = ROOT / 'gba/art/celadon-kanto'
SRC, EV = ART / 'source', ART / 'evidence'
PRIMARY, SECONDARY, LAYOUT = 'general_frlg', 'celadon_city_frlg', 'CeladonCity_Frlg'
W, H = 60, 40
PAVING = 0x16E                                  # FireRed's plain Celadon paving
GRASS = (0x008, 0x009, 0x010, 0x011)            # Celadon's lawn: plain, and with tufts
FLOWERS = 0x004
WOOD_SIGN = 0x003                               # FireRed's wooden signpost (General)
SIGNPOST = 0x002                                # its plain city signpost
OPEN, BLOCKED = (0, 3), (1, 0)                  # (collision, elevation) as FireRed's grid has them
POND = dict(left=0x1AD, water=0x1AE, right=0x1AF, bottom=(0x2CB, 0x2DD, 0x2CC))

# Lots cleared before the new pieces stand on them (x0, y0, x1, y1 inclusive): to paving, then
# lawns over what becomes green.
CLEARED = [(4, 25, 7, 29),                      # the house west of the gym: the gardens' north gate
           (44, 25, 51, 29)]                    # the south row's last two houses: the hotel
LAWNS = [(10, 17, 16, 17),                      # the fountain lawn a row taller, toward the store (HGSS B)
         (4, 25, 7, 30),                        # the gardens' gate lawn either side of its path
         (4, 33, 9, 33), (12, 33, 19, 33)]      # the gym's ledges, under the hedges
PATHS = [(5, 25, 6, 31),                        # the gate path, from the market road into the gardens
         (5, 31, 15, 31),                       # along the beds to the glasshouse
         (8, 31, 14, 32),                       # the glasshouse's forecourt (HGSS F)
         (10, 33, 11, 35)]                      # through the hedges to the south lawn
FLOWER_BEDS = [(4, 26), (7, 26), (4, 28), (7, 28), (4, 30), (7, 30), (10, 17), (16, 17),
               (16, 32), (18, 32), (8, 34), (13, 34), (17, 34), (14, 36), (19, 36)]
GYM_SIGN = (16, 31)                             # the gym's red signpost (its top in the cell above) becomes the gardens' wooden sign
NEW_SIGNS = {(45, 30): SIGNPOST,                # the hotel's, by its entrance
             (19, 30): WOOD_SIGN}               # the café's, at its awning
CAFE_DOOR_FROM = (36, 28)                       # FireRed's house door front (2 x 2 cells: the frame's top, the door) ...
CAFE_DOOR_TO = (16, 28)                         # ... onto the house at cols 16-19, its door at (17, 29)
CANAL = (24, 29, 23, 32)                        # x0, x1, first row carried on (FireRed's pond bottom), last water row
CANAL_BOTTOM = 33
BRIDGE_ROWS = (24, 25)                          # the street over the canal
DOORS = {'center': (48, 11), 'services_w': (11, 14), 'services_e': (15, 14), 'condominiums': (30, 11),
         'game_corner': (34, 21), 'prize_room': (39, 20), 'gardens': (11, 30), 'cafe': (17, 29), 'hotel': (48, 29)}

# Parts: name, sprite, left edge (px), foot row. Buildings block what they stand on (back row
# aside); SOLID parts block every cell they cover; GROUND parts lie under the player and keep the
# grid's collision.
PLACED = [('glass', 'glass', 128, 28), ('porch', 'porch', 128, 30), ('awning', 'awning', 256, 29),
          ('hotel', 'hotel', 704, 29), ('bridge', 'bridge', 384, 26),
          ('tent_nw', 'tent_a', 96, 19), ('tent_sw', 'tent_c', 96, 22), ('tent_ne', 'tent_b', 272, 19),
          ('tent_se', 'tent_e', 272, 22), ('tent_pocket', 'tent_d', 80, 14),
          ('hedge_w', 'hedge6', 64, 33), ('hedge_e', 'hedge6', 192, 33),
          ('produce_1', 'produce_crate', 336, 17), ('produce_2', 'produce_orange', 336, 18),
          ('produce_3', 'produce_green', 336, 20), ('produce_4', 'produce_pot', 336, 22),
          ('produce_5', 'produce_flowers', 144, 14)]
BUILDINGS = ('glass', 'porch', 'hotel')
SOLID = ('tent_nw', 'tent_sw', 'tent_ne', 'tent_se', 'tent_pocket', 'hedge_w', 'hedge_e',
         'produce_1', 'produce_2', 'produce_3', 'produce_4', 'produce_5')
GROUND = ('bridge',)
BACK_ROWS = {}
TENT_SHADE = (8, 30, 48, 16)                    # the shade under a tent's table (x, y, w, h in the sprite)
PAD = {'bridge': 8}                              # transparent rows under a part (its foot row)

# Colours. A part takes FireRed Celadon's own colours: a canvas's ramp (its colours by
# lightness) is laid onto one of Celadon's ramps; every other colour goes to its nearest
# Celadon colour (5-bit), so the map adds none.
RAMPS = dict(purple=[(238, 230, 255), (222, 197, 255), (180, 148, 222), (131, 106, 172), (82, 82, 106)],
             red=[(255, 205, 139), (238, 148, 115), (222, 106, 98), (205, 82, 74), (172, 32, 41)],
             gold=[(238, 230, 139), (222, 197, 139), (213, 189, 106), (197, 172, 106), (172, 148, 74)],
             teal=[(189, 230, 222), (148, 205, 180), (115, 172, 148), (106, 148, 139), (74, 115, 106)],
             blue=[(156, 213, 255), (115, 189, 246), (98, 164, 222), (74, 131, 197), (49, 98, 164)])
CANVAS = {'tent_nw': 'purple', 'tent_sw': 'gold', 'tent_ne': 'red', 'tent_se': 'teal', 'tent_pocket': 'blue'}
CANVAS_SRC = {'tent': [(238, 246, 230), (189, 197, 246), (123, 148, 246), (82, 123, 180)]}

# The bike lane (DESIGN.md: "the revitalized bike corridor"), Route 7 to Route 16: its cells,
# as (x0, y0, x1, y1) runs; each paving pixel in them takes Celadon's teal, white lines on its
# long edges, and a bicycle every LANE_MARK cells.
LANE = [(18, 13, 59, 13), (18, 13, 18, 16), (5, 16, 18, 16), (5, 16, 5, 23), (0, 23, 5, 23)]
LANE_MARK = 9
BIKE = ["..o...o..",
        ".o.o.ooo.",
        "o...o.o.o",
        ".o.o...o.",
        "..o...o.."]
WHITE = (246, 246, 255)

def cell(mid, cv):
    return np.uint16(mid | (cv[0] << 10) | (cv[1] << 12))

def rects(rs):
    for x0, y0, x1, y1 in rs:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                yield x, y

def edit_grid(grid):
    g = grid.copy()
    for x, y in rects(CLEARED):
        g[y, x] = cell(PAVING, OPEN)
    for x, y in rects(LAWNS):
        g[y, x] = cell(GRASS[(x + y) % 2 + 2 * ((x * 7 + y * 3) % 5 == 0)], OPEN)
    for x, y in rects(PATHS):
        g[y, x] = cell(PAVING, OPEN)
    for x, y in FLOWER_BEDS:
        g[y, x] = cell(FLOWERS, OPEN)
    x, y = GYM_SIGN
    g[y - 1, x] = cell(GRASS[0], OPEN)
    g[y, x] = cell(WOOD_SIGN, BLOCKED)
    for (x, y), mid in NEW_SIGNS.items():
        g[y, x] = cell(mid, BLOCKED)
    sx, sy = CAFE_DOOR_FROM
    tx, ty = CAFE_DOOR_TO
    for j in range(2):
        for i in range(2):
            g[ty + j, tx + i] = grid[sy + j, sx + i]
    # the canal: FireRed's pond's middle row carried south, its bottom rim at the treeline
    x0, x1, r0, r1 = CANAL
    for y in range(r0, r1 + 1):
        for x in range(x0, x1 + 1):
            if y in BRIDGE_ROWS:                # the street, under the footbridge's deck
                g[y, x] = cell(PAVING, OPEN)
                continue
            mid = POND['left'] if x == x0 else POND['right'] if x == x1 else POND['water']
            g[y, x] = cell(mid, OPEN if mid == POND['water'] else BLOCKED)
    for x in range(x0, x1 + 1):
        mid = POND['bottom'][0] if x == x0 else POND['bottom'][2] if x == x1 else POND['bottom'][1]
        g[CANAL_BOTTOM, x] = cell(mid, BLOCKED)
    return g

def rgb5(c):
    return np.asarray(c, int) >> 3

def nearest(px, fc):
    q = px.astype(int) >> 3
    d = ((q[:, None, :] - fc[None, :, :]) ** 2).sum(-1)
    n = fc[d.argmin(1)]
    return ((n << 3) | (n >> 2)).astype(np.uint8)

def lay_ramp(img, src, dst):
    """Each pixel of a canvas colour (src, light to dark; None: the part's colours whose hue is
    the canvas's, ranked by lightness) takes the colour of the same rank on dst."""
    a = img[..., 3] > 0
    cols = sorted({tuple(c) for c in img[a][:, :3].tolist()}, key=lambda c: -sum(c))
    if src is None:
        h0 = colorsys.rgb_to_hsv(*[v / 255 for v in cols[len(cols) // 2]])[0]
        src = [c for c in cols if abs(colorsys.rgb_to_hsv(*[v / 255 for v in c])[0] - h0) < 0.08
               and colorsys.rgb_to_hsv(*[v / 255 for v in c])[1] > 0.12]
    src = sorted(src, key=lambda c: -sum(c))
    for i, c in enumerate(src):
        k = round(i * (len(dst) - 1) / max(1, len(src) - 1))
        sel = a & (img[..., :3] == c).all(-1)
        img[sel, :3] = dst[k]

def sprite(name, part, fc):
    img = np.array(Image.open(SRC / f'sprites/{name}.png').convert('RGBA'))
    if part in CANVAS:
        lay_ramp(img, CANVAS_SRC['tent'], RAMPS[CANVAS[part]])
    if PAD.get(part):
        img = np.concatenate([img, np.zeros((PAD[part], img.shape[1], 4), np.uint8)], 0)
    a = img[..., 3] > 0
    img[a, :3] = nearest(img[a][:, :3], fc)
    return img

def frlg_colours(pair):
    return np.array(sorted({tuple(v >> 3 for v in c) for b in (0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12) for c in pair.pals[b][1:]}))

def merge_near(layers):
    """Colours one 5-bit step apart in every channel become one, the more used of each pair."""
    use = {}
    for a in layers:
        px = a[..., :3][a[..., 3] > 0] if a.shape[-1] == 4 else a.reshape(-1, 3)
        cs, n = np.unique(px.astype(np.int32) >> 3, axis=0, return_counts=True)
        for c, k in zip(map(tuple, cs.tolist()), n.tolist()):
            use[c] = use.get(c, 0) + k
    rep = {}
    for c in sorted(use, key=lambda c: (-use[c], c)):
        if c in rep:
            continue
        rep[c] = c
        for d in use:
            if d not in rep and max(abs(x - y) for x, y in zip(c, d)) <= 1:
                rep[d] = c
    moved = {c: r for c, r in rep.items() if c != r}
    for a in layers:
        q = a[..., :3].astype(np.int32) >> 3
        for c, r in moved.items():
            sel = (q == c).all(-1)
            a[..., :3][sel] = [(v << 3) | (v >> 2) for v in r]
    return moved

GRASS_FILL, GRASS_RIM = (115, 205, 164), (65, 180, 139)

def kerbs(images, full, lawns):
    """Celadon's lawn edge on the new lawns: where a lawn meets paving, the lawn's outer pixel
    row turns its tufts' darker green and the paving gets a kerb (its darkest colour against
    the grass, its lightest behind)."""
    lawn = np.zeros((H, W), bool)
    for x, y in rects(lawns):
        lawn[y, x] = True
    cellpx = lambda x, y: full[y * 16:y * 16 + 16, x * 16:x * 16 + 16].reshape(-1, 3)
    pave = {tuple(c) for x, y in ((6, 16), (20, 24)) for c in cellpx(x, y).tolist()}
    paving = lambda x, y: 0 <= x < W and 0 <= y < H and not lawn[y, x] and all(tuple(c) in pave for c in cellpx(x, y).tolist())
    n = 0
    for y, x in zip(*np.nonzero(lawn)):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if not paving(x + dx, y + dy):
                continue
            n += 1
            nb = cellpx(x + dx, y + dy)
            lum = nb.astype(int).sum(1)
            dark, light = nb[lum.argmin()], nb[lum.argmax()]
            if dx:
                rim = np.s_[y * 16:y * 16 + 16, x * 16 + (15 if dx > 0 else 0)]
                kerb = [np.s_[y * 16:y * 16 + 16, (x + dx) * 16 + (0 if dx > 0 else 15) + i * dx] for i in (0, 1)]
            else:
                rim = np.s_[y * 16 + (15 if dy > 0 else 0), x * 16:x * 16 + 16]
                kerb = [np.s_[(y + dy) * 16 + (0 if dy > 0 else 15) + i * dy, x * 16:x * 16 + 16] for i in (0, 1)]
            for im in images:
                r = im[rim]
                r[(r[..., :3] == GRASS_FILL).all(-1), :3] = GRASS_RIM
                im[kerb[0]][..., :3] = dark
                im[kerb[1]][..., :3] = light
    return n

def lawn_ground(pair, grid):
    """Every new lawn cell replaces paving or grass (or a cleared lot), never part of a
    building left standing."""
    g = grid.copy()
    for x, y in rects(CLEARED):
        g[y, x] = cell(PAVING, OPEN)
    full = frlg.flat(*frlg.render(pair, g))
    cellc = lambda x, y: {tuple(c) for c in full[y * 16:y * 16 + 16, x * 16:x * 16 + 16].reshape(-1, 3).tolist()}
    ground = cellc(6, 16) | cellc(20, 24) | cellc(10, 23) | cellc(9, 20) | cellc(9, 31) | cellc(5, 33) | cellc(12, 33) | {
        tuple(c) for m in GRASS + (FLOWERS, 0x0B0, 0x0B1, 0x087) for c in frlg.flat(*frlg.render(pair, np.array([[m]], np.uint16))).reshape(-1, 3).tolist()}
    bad = [(x, y) for x, y in rects(LAWNS) if not cellc(x, y) <= ground]
    assert not bad, ('lawn over a building', bad)

def shade(bottom, full, fc, x, y, w, h):
    """A shadow on the ground: each pixel takes the Celadon colour nearest its own at 72%."""
    sl = np.s_[y:y + h, x:x + w]
    q = (bottom[sl].astype(int) >> 3) * 0.72
    d = ((q[..., None, :] - fc[None, None, :, :]) ** 2).sum(-1)
    n = fc[d.argmin(-1)]
    bottom[sl] = (n << 3) | (n >> 2)
    full[sl] = bottom[sl]

ROADS = (0x16E, 0x166, 0x317)                   # FireRed's Celadon road paving

def lane(bottom, full, fc, painted, pair):
    """Paint the bike lane: paving pixels in the lane's cells take Celadon's teal by their
    lightness (its middle three greens); the lane's two long edges a white line; a white
    bicycle every LANE_MARK cells. Pixels that are not paving (a kerb, a lawn's edge) stay."""
    pave = sorted({tuple(c) for m in ROADS for c in frlg.flat(*frlg.render(pair, np.array([[m]], np.uint16))).reshape(-1, 3).tolist()},
                  key=lambda c: -sum(c))
    teal = RAMPS["teal"][2:5]
    tmap = {c: teal[min(len(teal) - 1, i * len(teal) // len(pave))] for i, c in enumerate(pave)}
    cells = []
    for x0, y0, x1, y1 in LANE:
        horizontal = y0 == y1
        for x, y in rects([(x0, y0, x1, y1)]):
            cells.append((x, y, horizontal))
    seen = set()
    for i, (x, y, horizontal) in enumerate(cells):
        if (x, y) in seen:
            continue
        seen.add((x, y))
        sl = np.s_[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
        b = bottom[sl]
        isp = np.array([[tuple(int(v) for v in b[yy, xx]) in tmap for xx in range(16)] for yy in range(16)])
        if not isp.all():
            continue                            # a kerb, a lawn's edge or a sign in the cell: the lane breaks there
        for yy, xx in zip(*np.nonzero(isp)):
            b[yy, xx] = tmap[tuple(int(v) for v in b[yy, xx])]
        if horizontal:
            b[1, :] = WHITE
            b[14, :] = WHITE
        else:
            b[:, 1] = WHITE
            b[:, 14] = WHITE
        if i % LANE_MARK == LANE_MARK // 2:
            for j, row in enumerate(BIKE):
                for k, ch in enumerate(row):
                    if ch == 'o':
                        b[5 + j, 3 + k] = WHITE
        full[sl] = b
        painted[y, x] = True

def hide_ground(bottom, top, art):
    """A part's opaque pixels hide the ground under them, whatever the layer type, so in an
    art cell each 8x8 bottom tile's hidden pixels take the commonest colour it still shows (a
    tile wholly hidden takes one colour): what the screen shows is unchanged, and the tile
    needs no colour it does not show."""
    n = 0
    for y, x in zip(*np.nonzero(art)):
        for q in range(4):
            sl = np.s_[y * 16 + (q // 2) * 8:y * 16 + (q // 2) * 8 + 8, x * 16 + (q % 2) * 8:x * 16 + (q % 2) * 8 + 8]
            cov = top[sl][..., 3] > 0
            if not cov.any():
                continue
            b = bottom[sl]
            seen = b[~cov]
            if len(seen):
                cs, k = np.unique(seen.reshape(-1, 3), axis=0, return_counts=True)
                fill = cs[k.argmax()]
            else:
                fill = b[0, 0].copy()
            n += int((cov & (b != fill).any(-1)).sum())
            b[cov] = fill
    return n

def compose(engine):
    pair = frlg.Pair(engine, PRIMARY, SECONDARY)
    grid, border = frlg.layout(engine, LAYOUT)
    lawn_ground(pair, grid)
    g = edit_grid(grid)
    bottom, top = frlg.render(pair, g)
    full = frlg.flat(bottom, top)
    notes = dict(kerb_edges=kerbs([bottom, full], full.copy(), LAWNS + PATHS))
    fc = frlg_colours(pair)
    painted = np.zeros((H, W), bool)
    lane(bottom, full, fc, painted, pair)
    # the shade under each tent's table, on the ground
    sprites = {}
    for name, spr, X, row in PLACED:
        sprites[name] = sprite(spr, name, fc)
    for name, spr, X, row in PLACED:
        if name.startswith('tent'):
            img = sprites[name]
            Y = (row + 1) * 16 - img.shape[0]
            sx, sy, sw, sh = TENT_SHADE
            shade(bottom, full, fc, X + sx, Y + sy, sw, sh)
            painted[(Y + sy) // 16, (X + sx) // 16:(X + sx + sw - 1) // 16 + 1] = True
    layer = np.zeros(bottom.shape[:2] + (4,), np.uint8)
    who = np.full(bottom.shape[:2], '', '<U16')
    feet = {}
    for name, spr, X, row in sorted(PLACED, key=lambda p: (p[3], p[2])):
        img = sprites[name]
        Y = (row + 1) * 16 - img.shape[0]
        a = img[..., 3] > 0
        layer[Y:Y + img.shape[0], X:X + img.shape[1]][a] = img[a]
        who[Y:Y + img.shape[0], X:X + img.shape[1]][a] = name
        feet[name] = row
    hit = layer[..., 3] > 0
    art = hit.reshape(H, 16, W, 16).any(axis=(1, 3)) | painted
    cover = hit.reshape(H, 16, W, 16).mean(axis=(1, 3))
    owner = np.full((H, W), '', '<U16')
    for y, x in zip(*np.nonzero(art)):
        sl = np.s_[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
        h = hit[sl]
        if h.any():
            names, counts = np.unique(who[sl][h], return_counts=True)
            owner[y, x] = names[counts.argmax()]
        bottom[sl] = full[sl]
        top[sl] = layer[sl]
    notes['hidden_ground_px'] = hide_ground(bottom, top, art)
    border_bottom, border_top = frlg.render(pair, border)
    notes['merged_colours'] = len(merge_near([bottom, top, border_bottom, border_top]))
    notes['painted_cells'] = int(painted.sum())
    return dict(pair=pair, grid=grid, border=border, edited=g, bottom=bottom, top=top, art=art, owner=owner, cover=cover,
                feet=feet, notes=notes, border_bottom=border_bottom, border_top=border_top)

def main(engine):
    r = compose(engine)
    SRC.mkdir(parents=True, exist_ok=True); EV.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(SRC / 'compose.npz', grid=r['grid'], border=r['border'], edited=r['edited'], bottom=r['bottom'],
                        top=r['top'], art=r['art'], owner=r['owner'], cover=r['cover'],
                        border_bottom=r['border_bottom'], border_top=r['border_top'],
                        feet_names=np.array(list(r['feet']), '<U16'), feet_rows=np.array(list(r['feet'].values())),
                        pals=np.array([r['pair'].pals[b] for b in range(13)], np.uint8))
    after = frlg.flat(r['bottom'], r['top'])
    Image.fromarray(after).save(EV / 'terrain.png')
    before = frlg.flat(*frlg.render(r['pair'], r['grid']))
    sheet = Image.new('RGB', (W * 16 * 2 + 12, H * 16 + 24), (28, 32, 38)); d = ImageDraw.Draw(sheet)
    for i, (im, t) in enumerate(((before, 'FireRed (CeladonCity_Frlg)'), (after, 'Ten years on'))):
        sheet.paste(Image.fromarray(im), (i * (W * 16 + 12), 24)); d.text((i * (W * 16 + 12) + 4, 6), t, fill='white')
    sheet.save(EV / 'compare.png')
    print('art cells', int(r['art'].sum()), r['notes'])

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
