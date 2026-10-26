"""Celadon City ten years on: HGSS's Celadon, rebuilt in Gen 3 (second round).

    python3 tools/gba/maps/celadon/compose.py ENGINE_CHECKOUT

The owner, 2026-10-26: "start with HGSS and work backward". HGSS's Celadon (pokeheartgold
T07, source/hgss/) is the plan, cell for cell in HGSS's own coordinates (a 60x50 cut of its
64x64 block): its north row of buildings on a paved terrace, the main road east to Route 7,
the west avenue down to the road west to Route 16, the fountain plaza, the Game Corner block,
the canal and its footbridge, the paved loop round the south-east houses, the gym on its
forecourt above the ledges, the forests round the town. Every cell is then drawn in Gen 3:

    ground      FireRed Celadon's own metatiles: its paving with its lawn edges (the edge
                piece chosen from the paving's grass neighbours), its grass and flowers, its
                trees (each forest's edges, tops and trunks chosen from the forest's shape),
                its pond's rims and water for the canal, FireRed's fence and signposts
    buildings   FireRed's Celadon buildings on HGSS's lots (parts.py): the Dept Store (the
                market's services), the Mansion as the Pokemon Hotel on HGSS's Condominiums
                lot, the Center, the Game Corner and prize room, FireRed's houses for HGSS's
                houses, the gym under glass as the Botanical Gardens' glasshouse
    story       the market's tents and produce round the fountain, the café (a house with
                the Bike Shop's awning beside the market), the gardens (hedges for the
                ledges, beds and trees for the gym's flanking houses, a forecourt), the
                Bond Bridge's planks over the canal, the bike lane painted from Route 7 to
                Route 16

A cell any part draws in, or the lane paints, is an art cell, packed from its pixels (pack.py).
Writes source/compose.npz and evidence/terrain.png, compare.png (HGSS beside the build).
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
W, H = 60, 50
OPEN, BLOCKED = (0, 3), (1, 0)                  # (collision, elevation) as FireRed's grids have them

# --------------------------------------------------------------------------- FireRed's pieces
GRASS = (0x008, 0x009, 0x010, 0x011)
FLOWERS = 0x004
SIGNPOST, WOOD_SIGN = 0x002, 0x003
FENCE = (0x0E7, 0x0E7)                          # FireRed Celadon's railing on grass (its 0x0D6/0x0D7 is the fence over a forest's top)
# FireRed Celadon's paving, by which of its sides (N, S, W, E) meet grass; the inner corners
# by the one diagonal that does.
PAVE = {(): 0x16E, ('N',): 0x166, ('S',): 0x176, ('W',): 0x16D, ('E',): 0x16F,
        ('N', 'W'): 0x165, ('N', 'E'): 0x167, ('S', 'W'): 0x175, ('S', 'E'): 0x177}
PAVE_INNER = {'NE': 0x196, 'NW': 0x195, 'SE': 0x19E, 'SW': 0x19D}
# FireRed's trees, two cells wide: a forest's top row, its second row, its fill (even rows,
# odd rows) and its trunks; its left edge (even x) and right edge (odd x).
TREE = dict(top=(0x00E, 0x00F), second=(0x01E, 0x01F), fill_even=(0x01C, 0x01D), fill_odd=(0x014, 0x015),
            trunk=(0x024, 0x025), trunk_left=0x026, trunk_right=0x027,
            left_even=0x01E, left_odd=0x016, right_even=0x01F, right_odd=0x017)
POND = dict(top=(0x1A5, 0x1A6, 0x1A7), mid=(0x1AD, 0x1AE, 0x1AF), bottom=(0x2CB, 0x2DD, 0x2CC))

# --------------------------------------------------------------------------- HGSS's plan
# Rectangles x0, y0, x1, y1 inclusive, in HGSS's cells.
FOREST = [(0, 0, 59, 1),                        # the north treeline
          (0, 0, 7, 29), (0, 37, 7, 49),        # the west woods, either side of the road to Route 16
          (54, 0, 59, 11), (54, 19, 59, 49),    # the east woods, either side of the road to Route 7
          (0, 47, 59, 49),                      # the south woods
          (32, 43, 53, 49), (26, 45, 31, 49),   # HGSS's trees below the south-east loop and the canal's end
          (10, 3, 13, 5), (24, 3, 27, 5), (36, 3, 43, 5), (50, 3, 51, 5),   # HGSS's trees behind the north row
          (10, 37, 11, 39), (10, 41, 11, 43)]   # the gardens' trees, where the gym's west house stood
PAVING = [(10, 8, 53, 17),                      # the north row's terrace and the main road
          (54, 14, 59, 17),                     # on to Route 7
          (10, 14, 12, 35),                     # the west avenue
          (13, 18, 24, 18), (23, 18, 24, 32), (10, 31, 24, 32),   # round the plaza
          (0, 33, 30, 35),                      # the road to Route 16, over the canal
          (31, 29, 53, 31), (31, 29, 32, 41), (31, 39, 53, 41), (52, 29, 53, 41),   # the south-east loop
          (12, 42, 23, 44), (12, 36, 13, 41), (22, 36, 23, 41),   # the gardens' forecourt and its paths
          (13, 19, 13, 19), (22, 19, 22, 19), (13, 30, 13, 30), (22, 30, 22, 30)]   # the plaza lawn's corners
CANAL = dict(x=(25, 30), top=29, bottom=43, bridge=(33, 35))
FENCES = [(30, 28, 41, 28), (44, 28, 53, 28)]
FLOWER_BEDS = [(14, 23), (21, 23), (14, 26), (21, 26), (15, 20), (20, 20), (15, 29), (20, 29),
               (16, 2), (21, 2), (30, 2), (33, 3), (46, 2), (48, 3),
               (25, 19), (25, 23), (28, 27), (43, 19), (52, 19), (43, 26), (52, 26),
               (33, 32), (34, 38), (38, 38), (46, 38), (50, 38), (51, 32),
               (10, 36), (11, 40), (10, 44), (11, 44), (24, 36), (24, 38), (24, 40), (24, 42), (24, 44),
               (8, 31), (9, 32), (8, 36), (55, 13), (57, 12), (55, 18)]
SIGNS = {(17, 22): SIGNPOST, (18, 14): SIGNPOST, (35, 13): SIGNPOST, (35, 28): SIGNPOST, (38, 28): SIGNPOST,
         (45, 28): SIGNPOST, (21, 44): WOOD_SIGN, (29, 26): WOOD_SIGN}
DOORS = {'center': (47, 13), 'services_w': (16, 13), 'services_e': (20, 13), 'hotel': (31, 13),
         'game_corner': (34, 25), 'prize_room': (39, 24), 'cafe': (27, 25), 'gardens': (17, 41), 'residence': (40, 37)}

# Parts: name, sprite, left edge (px), foot row. BUILDINGS block what they cover (their back
# row aside); SOLID parts block every cell they draw in; GROUND parts lie under the player and
# keep the grid's collision.
PLACED = [('house_nw', 'house', 160, 13), ('dept', 'dept', 224, 13), ('house_n2', 'house_chimney', 368, 13),
          ('hotel', 'hotel', 448, 13), ('house_n3', 'house', 576, 13), ('house_n4', 'house_chimney', 640, 13),
          ('center', 'center', 720, 13),
          ('game_corner', 'game_corner', 496, 26), ('cafe', 'house_door', 416, 25), ('awning', 'awning', 416, 25),
          ('house_e1', 'house', 704, 25), ('house_e2', 'house_chimney', 768, 25),
          ('house_se1', 'house', 560, 37), ('residence', 'house_door', 624, 37), ('house_se3', 'house_chimney', 688, 37),
          ('house_se4', 'house', 752, 37),
          ('glasshouse', 'glasshouse', 224, 41), ('fountain', 'fountain', 256, 25),
          ('tent_nw', 'tent_a', 208, 21), ('tent_ne', 'tent_b', 304, 21), ('tent_sw', 'tent_c', 208, 30), ('tent_se', 'tent_e', 304, 30),
          ('produce_1', 'produce_crate', 384, 20), ('produce_2', 'produce_orange', 384, 22),
          ('produce_3', 'produce_green', 384, 26), ('produce_4', 'produce_pot', 384, 28),
          ('hedge_w', 'hedge8', 160, 45), ('hedge_e', 'hedge6', 320, 45),
          ('bridge', 'bridge', 400, 36)]
# FireRed's own cells behind each building sprite (parts.py cuts them from CeladonCity_Frlg):
# where a sprite's cell is whole and as FireRed draws it, the cell takes FireRed's metatile
# itself (both layers in FireRed's own banks, its collision and behaviour); only the cells a
# building's outline crosses, or the story edits, are packed from pixels.
FRLG_SOURCE = {'dept': (9, 4), 'center': (46, 6), 'game_corner': (31, 17), 'house': (32, 25), 'house_door': (36, 25),
               'house_chimney': (40, 25), 'hotel': (27, 4), 'glasshouse': (8, 25)}
BUILDINGS = ('house_nw', 'dept', 'house_n2', 'hotel', 'house_n3', 'house_n4', 'center', 'game_corner', 'cafe', 'awning',
             'house_e1', 'house_e2', 'house_se1', 'residence', 'house_se3', 'house_se4', 'glasshouse')
SOLID = ('fountain', 'tent_nw', 'tent_ne', 'tent_sw', 'tent_se', 'produce_1', 'produce_2', 'produce_3', 'produce_4',
         'hedge_w', 'hedge_e')
GROUND = ('bridge',)
BACK_ROWS = {}
TENT_SHADE = (8, 30, 48, 16)                    # the shade under a tent's table (x, y, w, h in the sprite)
PAD = {'bridge': 8}                             # transparent rows under a part (its foot row)

# Colours: a canvas's ramp laid onto one of Celadon's own; every other colour to its nearest
# Celadon colour (5-bit), so the map adds none.
RAMPS = dict(purple=[(238, 230, 255), (222, 197, 255), (180, 148, 222), (131, 106, 172), (82, 82, 106)],
             red=[(255, 205, 139), (238, 148, 115), (222, 106, 98), (205, 82, 74), (172, 32, 41)],
             gold=[(238, 230, 139), (222, 197, 139), (213, 189, 106), (197, 172, 106), (172, 148, 74)],
             teal=[(189, 230, 222), (148, 205, 180), (115, 172, 148), (106, 148, 139), (74, 115, 106)],
             blue=[(156, 213, 255), (115, 189, 246), (98, 164, 222), (74, 131, 197), (49, 98, 164)])
CANVAS = {'tent_nw': 'purple', 'tent_sw': 'gold', 'tent_ne': 'red', 'tent_se': 'teal'}
CANVAS_SRC = [(238, 246, 230), (189, 197, 246), (123, 148, 246), (82, 123, 180)]

# The bike lane (DESIGN.md: "the revitalized bike corridor"), Route 7 to Route 16, down the
# middle of the main road, the west avenue and the road west.
LANE = [(11, 16, 59, 16), (11, 16, 11, 34), (0, 34, 11, 34)]
LANE_MARK = 9
BIKE = ["..o...o..",
        ".o.o.ooo.",
        "o...o.o.o",
        ".o.o...o.",
        "..o...o.."]
WHITE = (246, 246, 255)

def rects(rs):
    for x0, y0, x1, y1 in rs:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                yield x, y

def cell(mid, cv):
    return np.uint16(mid | (cv[0] << 10) | (cv[1] << 12))

def plan():
    """Each cell's ground kind, from HGSS's plan."""
    kind = np.full((H, W), 'grass', '<U8')
    for x, y in rects(FOREST):
        kind[y, x] = 'forest'
    for x, y in rects(PAVING):
        kind[y, x] = 'pave'
    x0, x1 = CANAL['x']
    for y in range(CANAL['top'], CANAL['bottom'] + 1):
        for x in range(x0, x1 + 1):
            kind[y, x] = 'pave' if CANAL['bridge'][0] <= y <= CANAL['bridge'][1] else 'canal'
    for x, y in rects(FENCES):
        kind[y, x] = 'fence'
    for x, y in FLOWER_BEDS:
        assert kind[y, x] == 'grass', ('flowers off the grass', x, y, kind[y, x])
        kind[y, x] = 'flower'
    for (x, y), _ in SIGNS.items():
        kind[y, x] = 'sign'
    return kind

def build_grid(kind):
    g = np.zeros((H, W), np.uint16)
    at = lambda x, y, default: kind[y, x] if 0 <= x < W and 0 <= y < H else default
    for y in range(H):
        for x in range(W):
            k = kind[y, x]
            if k in ('grass', 'flower'):
                g[y, x] = cell(FLOWERS if k == 'flower' else GRASS[(x + y) % 2 + 2 * ((x * 7 + y * 3) % 5 == 0)], OPEN)
            elif k == 'pave':
                green = lambda dx, dy: at(x + dx, y + dy, 'pave') in ('grass', 'flower', 'forest', 'fence', 'sign')
                sides = tuple(s for s, (dx, dy) in (('N', (0, -1)), ('S', (0, 1)), ('W', (-1, 0)), ('E', (1, 0))) if green(dx, dy))
                assert sides in PAVE, ('paving with grass on opposite sides', x, y, sides)
                mid = PAVE[sides]
                if not sides:
                    diag = [d for d, (dx, dy) in (('NE', (1, -1)), ('NW', (-1, -1)), ('SE', (1, 1)), ('SW', (-1, 1))) if green(dx, dy)]
                    if diag:
                        mid = PAVE_INNER[diag[0]]
                g[y, x] = cell(mid, OPEN)
            elif k == 'forest':
                f = lambda dx, dy: at(x + dx, y + dy, 'forest') == 'forest'
                if not f(0, 1):                                  # its trunks
                    mid = TREE['trunk_left'] if not f(-1, 0) else TREE['trunk_right'] if not f(1, 0) else TREE['trunk'][x % 2]
                    coll = BLOCKED
                elif not f(0, -1):                               # its top: the crowns, walked behind
                    mid, coll = TREE['top'][x % 2], OPEN
                elif not f(0, -2):
                    mid, coll = TREE['second'][x % 2], BLOCKED
                else:
                    even = y % 2 == 0
                    mid = (TREE['fill_even'] if even else TREE['fill_odd'])[x % 2]
                    if not f(-1, 0):
                        mid = TREE['left_even'] if even else TREE['left_odd']
                    elif not f(1, 0):
                        mid = TREE['right_even'] if even else TREE['right_odd']
                    coll = BLOCKED
                g[y, x] = cell(mid, coll)
            elif k == 'canal':
                x0, x1 = CANAL['x']
                col = 0 if x == x0 else 2 if x == x1 else 1
                row = 'top' if y == CANAL['top'] else 'bottom' if y == CANAL['bottom'] else 'mid'
                water = row == 'mid' and col == 1
                g[y, x] = cell(POND[row][col], OPEN if water else BLOCKED)
            elif k == 'fence':
                g[y, x] = cell(FENCE[x % 2], BLOCKED)
            elif k == 'sign':
                g[y, x] = cell(SIGNS[(x, y)], BLOCKED)
    return g

def check_plan(kind):
    """HGSS's plan fits FireRed's tree pieces: every forest run starts on an even column and
    ends on an odd one, every forest's top and trunk rows are odd."""
    bad = []
    for y in range(H):
        for x in range(W):
            if kind[y, x] != 'forest':
                continue
            if x > 0 and kind[y, x - 1] != 'forest' and x % 2:
                bad.append(('left edge on an odd column', x, y))
            if x < W - 1 and kind[y, x + 1] != 'forest' and not x % 2:
                bad.append(('right edge on an even column', x, y))
            if y < H - 1 and kind[y + 1, x] != 'forest' and not y % 2:
                bad.append(('trunks on an even row', x, y))
            if y > 0 and kind[y - 1, x] != 'forest' and not y % 2:
                bad.append(('top on an even row', x, y))
    assert not bad, bad[:10]

def nearest(px, fc):
    q = px.astype(int) >> 3
    d = ((q[:, None, :] - fc[None, :, :]) ** 2).sum(-1)
    n = fc[d.argmin(1)]
    return ((n << 3) | (n >> 2)).astype(np.uint8)

def lay_ramp(img, src, dst):
    a = img[..., 3] > 0
    src = sorted(src, key=lambda c: -sum(c))
    for i, c in enumerate(src):
        k = round(i * (len(dst) - 1) / max(1, len(src) - 1))
        sel = a & (img[..., :3] == c).all(-1)
        img[sel, :3] = dst[k]

def sprite(name, part, fc):
    img = np.array(Image.open(SRC / f'sprites/{name}.png').convert('RGBA'))
    if part in CANVAS:
        lay_ramp(img, CANVAS_SRC, RAMPS[CANVAS[part]])
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

def shade(bottom, full, fc, x, y, w, h):
    """A shadow on the ground: each pixel takes the Celadon colour nearest its own at 72%."""
    sl = np.s_[y:y + h, x:x + w]
    q = (bottom[sl].astype(int) >> 3) * 0.72
    d = ((q[..., None, :] - fc[None, None, :, :]) ** 2).sum(-1)
    n = fc[d.argmin(-1)]
    bottom[sl] = (n << 3) | (n >> 2)
    full[sl] = bottom[sl]

ROADS = (0x16E,)

def lane(bottom, full, painted, pair):
    """Paint the bike lane: the paving's pixels in its cells take Celadon's teal by their
    lightness, white lines on its long edges, a white bicycle every LANE_MARK cells. A cell
    holding anything but plain paving (a kerb, a door's step) breaks the lane there."""
    pave = sorted({tuple(c) for m in ROADS for c in frlg.flat(*frlg.render(pair, np.array([[m]], np.uint16))).reshape(-1, 3).tolist()},
                  key=lambda c: -sum(c))
    teal = RAMPS['teal'][2:5]
    tmap = {c: teal[min(len(teal) - 1, i * len(teal) // len(pave))] for i, c in enumerate(pave)}
    seen = set()
    i = 0
    for x0, y0, x1, y1 in LANE:
        horizontal = y0 == y1
        for x, y in rects([(x0, y0, x1, y1)]):
            if (x, y) in seen:
                continue
            seen.add((x, y))
            i += 1
            sl = np.s_[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
            b = bottom[sl]
            isp = np.array([[tuple(int(v) for v in b[yy, xx]) in tmap for xx in range(16)] for yy in range(16)])
            if not isp.all():
                continue
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

def hide_ground(bottom, top, art, keep):
    """A part's opaque pixels hide the ground under them, so in an art cell each 8x8 bottom
    tile's hidden pixels take the commonest colour it still shows: what the screen shows is
    unchanged, and the tile needs no colour it does not show. Door cells (keep) are left
    whole: their door is flattened onto the bottom layer, where the door animation draws."""
    n = 0
    for y, x in zip(*np.nonzero(art)):
        if (x, y) in keep:
            continue
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

def frlg_cells(engine, pair, g, sprites):
    """Each building sprite's whole, unedited cells become FireRed's own metatiles in the grid
    (and leave the sprite); returns how many."""
    fgrid, _ = frlg.layout(engine, LAYOUT)
    fpic = frlg.flat(*frlg.render(pair, fgrid))
    n = 0
    for name, spr, X, row in PLACED:
        if spr not in FRLG_SOURCE:
            continue
        img = sprites[name]
        sx, sy = FRLG_SOURCE[spr]
        Y = (row + 1) * 16 - img.shape[0]
        assert X % 16 == 0 and Y % 16 == 0, name
        for j in range(img.shape[0] // 16):
            for i in range(img.shape[1] // 16):
                c = img[j * 16:j * 16 + 16, i * 16:i * 16 + 16]
                ref = fpic[(sy + j) * 16:(sy + j) * 16 + 16, (sx + i) * 16:(sx + i) * 16 + 16]
                if (c[..., 3] == 255).all() and ((c[..., :3] >> 3) == (ref >> 3)).all():
                    g[Y // 16 + j, X // 16 + i] = fgrid[sy + j, sx + i]
                    c[..., 3] = 0
                    n += 1
    return n

def compose(engine):
    pair = frlg.Pair(engine, PRIMARY, SECONDARY)
    _, border = frlg.layout(engine, LAYOUT)
    kind = plan()
    check_plan(kind)
    g = build_grid(kind)
    fc = frlg_colours(pair)
    sprites = {name: sprite(spr, name, fc) for name, spr, X, row in PLACED}
    frlg_kept = frlg_cells(engine, pair, g, sprites)
    bottom, top = frlg.render(pair, g)
    full = frlg.flat(bottom, top)
    painted = np.zeros((H, W), bool)
    lane(bottom, full, painted, pair)
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
    doors = set(DOORS.values())
    for y, x in zip(*np.nonzero(art)):
        sl = np.s_[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
        h = hit[sl]
        if h.any():
            names, counts = np.unique(who[sl][h], return_counts=True)
            owner[y, x] = names[counts.argmax()]
        bottom[sl] = full[sl]
        top[sl] = layer[sl]
        if (x, y) in doors:                     # the door on the bottom layer, as FireRed draws its doors
            m = top[sl][..., 3] > 0
            bottom[sl][m] = top[sl][..., :3][m]
            top[sl] = 0
    notes = dict(frlg_building_cells=frlg_kept, hidden_ground_px=hide_ground(bottom, top, art, doors))
    border_bottom, border_top = frlg.render(pair, border)
    notes['merged_colours'] = len(merge_near([bottom, top, border_bottom, border_top]))
    notes['painted_cells'] = int(painted.sum())
    return dict(pair=pair, grid=g, border=border, edited=g, kind=kind, bottom=bottom, top=top, art=art, owner=owner,
                cover=cover, feet=feet, notes=notes, border_bottom=border_bottom, border_top=border_top)

def main(engine):
    r = compose(engine)
    SRC.mkdir(parents=True, exist_ok=True); EV.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(SRC / 'compose.npz', grid=r['grid'], border=r['border'], edited=r['edited'], bottom=r['bottom'],
                        top=r['top'], art=r['art'], owner=r['owner'], cover=r['cover'], kind=r['kind'],
                        border_bottom=r['border_bottom'], border_top=r['border_top'],
                        feet_names=np.array(list(r['feet']), '<U16'), feet_rows=np.array(list(r['feet'].values())),
                        pals=np.array([r['pair'].pals[b] for b in range(13)], np.uint8))
    after = frlg.flat(r['bottom'], r['top'])
    Image.fromarray(after).save(EV / 'terrain.png')
    hgss = np.array(Image.open(SRC / 'hgss/hgss-render.png').convert('RGB'))[:H * 16, :W * 16]
    sheet = Image.new('RGB', (W * 16 * 2 + 12, H * 16 + 24), (28, 32, 38)); d = ImageDraw.Draw(sheet)
    for i, (im, t) in enumerate(((hgss, 'HGSS Celadon (the plan)'), (after, 'Ten years on, in Gen 3'))):
        sheet.paste(Image.fromarray(im), (i * (W * 16 + 12), 24)); d.text((i * (W * 16 + 12) + 4, 6), t, fill='white')
    sheet.save(EV / 'compare.png')
    print('art cells', int(r['art'].sum()), r['notes'])

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
