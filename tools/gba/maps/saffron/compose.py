"""Saffron City ten years on: FireRed's own Saffron, rebuilt for Apocrypha's story (v3).

    python3 tools/gba/maps/saffron/compose.py ENGINE_CHECKOUT

FireRed's map (SaffronCity_Frlg: 66x55 on General_Frlg + SaffronCity) is the base, cell for
cell (the owner, 2026-10-24: FireRed's Gen 3 Saffron, not HGSS's, is the base). New
buildings are real Gen 3 art put together into buildings of Saffron's own (parts.py):

    dojo         One Saffron Dojo for both dojos, an entrance each into one hall, on
                 FireRed's Fighting Dojo's and Gym's lots: the Fighting door (40, 12), the
                 Psychic door (45, 12). Canon has no Saffron Gym.
    silph        Silph Co. "dominates the skyline": FireRed's crown on a new glass tower,
                 a floor taller; the street behind it four cells deep, the back two behind its roof.
    lab          Silph's research lab, built onto the tower's east side on the east inner
                 block's lot, its own door (42, 30).
    station      The Magnet Train station, the player's way into Kanto (Chapter 4's end),
                 in the north-west block where HGSS puts it (sprites.py).
    fountain, lamps   a fountain on the south avenue's plaza; street lamps at Silph's and
                 the lab's doors.
    green        lawns, flower beds and trees in FireRed's own General pieces (Celadon's
                 grass, flowers and trees, no new colours): a fountain garden out to the
                 south gate's grass, lawns before Silph and the lab, the east fence's green,
                 two corner groves; Celadon's lawn edge drawn in Saffron's colours (kerbs).
    rail         the Magnet Train's elevated deck to match Johto's (Goldenrod's), west from the
                 station to the map's edge, the west walkway under it.
    signs        The Gym's red signposts are plain city signposts (install.py writes the
                 dojos' signs); the city sign moves north of Silph's crown.
    copycat      The Copycat's house, whose lot the station takes, moves to the house at
                 (18, 17), which gains FireRed's own door front.

Every unchanged cell keeps its FireRed metatile. A cell any part draws in is an art cell,
packed from its pixels (pack.py): FireRed's picture there, both layers flattened, under the
part's own pixels on the top layer.
Writes source/compose.npz and evidence/terrain.png, compare.png.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
import frlg                                     # noqa: E402

ART = ROOT / 'gba/art/saffron-kanto'
SRC, EV = ART / 'source', ART / 'evidence'
PRIMARY, SECONDARY, LAYOUT = 'general_frlg', 'saffron_city_frlg', 'SaffronCity_Frlg'
W, H = 66, 55
PAVING = 0x2E9                                  # FireRed's plain Saffron paving
SIGNPOST = 0x002                                # its plain signpost (General)
OLIVE = 0x2EC                                   # the darker paving round its buildings
OPEN, BLOCKED = (0, 3), (1, 0)                  # (collision, elevation) as FireRed's grid has them

NW_BLOCK = (17, 10, 28, 14)                     # the three houses the station replaces
STATION_X, STATION_BASE_ROW = 288, 14           # the station: sprite left edge (px), its foot row
STATION_DOOR = (25, 14)
# Lots cleared to paving before the new buildings stand on them (x0, y0, x1, y1 inclusive).
CLEARED = [(37, 8, 49, 13),                     # FireRed's Fighting Dojo and Gym
           (29, 14, 37, 30),                    # FireRed's Silph, and the railings and old city sign behind it, under the taller roof's back
           (38, 22, 47, 31)]                    # the east inner block's apartments, their fence and Silph's east railing
GYM_SIGNS = [(42, 13), (50, 13)]                # red Gym signposts (top cell; the post is the row below)
COPYCAT_HOUSE = (18, 20)                        # its front's top-left: two rows take the door front
CITY_SIGN = (30, 12)                            # moved from (29, 14), which Silph's crown covers
SILPH_RAIL_END = (38, 14)                       # the railing east of Silph now starts here (its end post was at (37, 14))
# Parts: name, sprite, left edge (px), foot row. Buildings block what they stand on; props
# block their foot cell.
PLACED = [('rail', 'rail', 0, 14), ('dojo', 'dojo', 36 * 16, 12), ('silph', 'silph', 29 * 16, 30), ('lab', 'lab', 38 * 16, 30),
          ('station', 'station', STATION_X, STATION_BASE_ROW), ('fountain', 'fountain', 33 * 16, 42),
          ('lamp_silph_w', 'lamp', 31 * 16, 31), ('lamp_silph_e', 'lamp', 35 * 16, 31),
          ('lamp_lab_w', 'lamp', 40 * 16, 31), ('lamp_lab_e', 'lamp', 44 * 16, 31)]
BUILDINGS = ('dojo', 'silph', 'lab', 'station', 'fountain')
# The Magnet Train's deck runs from the station's west platform (x 288) to the map's west
# edge at the platform's height, over the forest, the city fence and the west walkway
# (cols 15-16), which stays open under it, the deck drawn over the player. Goldenrod's
# deck casts a 40 px shadow on the street below it; so does Saffron's.
RAIL_SHADOW = (14 * 16, 14 * 16, 4 * 16, 40)   # x, y, width, height (px): the fence, the walkway and the street west of the station; the forest's crowns stay as they are
# Saffron's 13 banks are full, so the deck's colours come from two sides: the station it meets
# takes FireRed's nearest colours throughout (it is a soft render; 2-4 5-bit steps), which
# frees its own; the deck keeps Goldenrod's twelve main colours exactly (93% of its pixels),
# its rare specks taking the nearest of those twelve.
SNAPS = {'rail': None}         # a part's snap distance; None: every colour to its palette's nearest
RAIL_COLOURS = 6
def rail_palette():
    d = np.array(Image.open(SRC / 'goldenrod-deck.png').convert('RGB')).astype(int) >> 3
    cs, n = np.unique(d.reshape(-1, 3), axis=0, return_counts=True)
    return cs[np.argsort(-n, kind='stable')[:RAIL_COLOURS]]
PALETTES = {'rail': rail_palette}
# Rows at a building's back (from the top row its pixels reach) that keep their ground's
# collision and draw above the player, who walks behind the roof: a tall building is not
# deep, so Silph's roof hides two rows of the street behind it.
BACK_ROWS = {'silph': 2}
DOORS = {'dojo_fighting': (40, 12), 'dojo_psychic': (45, 12), 'lab': (42, 30), 'silph': (33, 30), 'station': STATION_DOOR}

# Green spaces, all in FireRed's own General pieces (Celadon's grass, flowers and trees), so
# they cost no new colours: lawns (x0, y0, x1, y1 inclusive) laid first, then flowers, then
# trees (top-left of FireRed's 2x3 tree: crown, canopy, trunk).
GRASS = (0x008, 0x009, 0x010, 0x011)            # Celadon's lawn: plain, and two with tufts
FLOWERS = 0x004
TREE = ((0x00E, 0x00F), (0x01E, 0x01F), (0x024, 0x025))
LAWNS = [(31, 39, 37, 43), (32, 44, 37, 44),    # the fountain garden on the south avenue, out to the south gate's grass ((31, 44) holds a tree's crown)
         (30, 31, 32, 32), (34, 31, 41, 32), (43, 31, 47, 32),   # Silph's and the lab's front lawns, paths kept to both doors
         (50, 15, 52, 21),                      # the east fence's green, north of the east gate (east of the League office)
         (48, 30, 52, 33),                      # and south of it
         (15, 39, 18, 42),                      # the south-west corner by the Center, inside its fence
         (15, 10, 16, 16)]                      # the strip west of the station
REPAVED = [(30, 31, 47, 33)]                    # FireRed's olive patch before Silph, cleared under the lawns (its sign at (29, 31) stays)
FLOWER_BEDS = [(31, 39), (37, 39), (31, 41), (37, 41), (31, 43), (37, 43), (32, 44), (36, 44),
               (30, 32), (32, 31), (34, 32), (36, 31), (38, 32), (39, 31), (41, 32),
               (43, 32), (45, 31), (46, 32), (47, 31),
               (50, 17), (52, 16), (50, 20), (52, 21), (50, 31), (52, 30), (48, 33), (52, 33), (15, 39), (18, 39),
               (15, 16)]
# Trees only off the walkways: check.py fails if one makes any route between doors, gates and signs longer.
TREES = [(15, 40), (17, 40)]                    # the fenced corner by the Center

def edit_grid(grid):
    g = grid.copy()
    cell = lambda mid, cv: np.uint16(mid | (cv[0] << 10) | (cv[1] << 12))
    notes = {}
    for x0, y0, x1, y1 in [NW_BLOCK] + CLEARED + REPAVED:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                g[y, x] = cell(PAVING, OPEN)
    for x0, y0, x1, y1 in LAWNS:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                g[y, x] = cell(GRASS[(x + y) % 2 + 2 * ((x * 7 + y * 3) % 5 == 0)], OPEN)
    for x, y in FLOWER_BEDS:
        g[y, x] = cell(FLOWERS, OPEN)
    for x, y in TREES:
        for j, row in enumerate(TREE):
            for i, mid in enumerate(row):
                g[y + j, x + i] = cell(mid, OPEN if j == 0 else BLOCKED)
    for x, y in GYM_SIGNS:
        g[y, x] = cell(OLIVE, OPEN)
        g[y + 1, x] = cell(SIGNPOST, BLOCKED)
    g[CITY_SIGN[1], CITY_SIGN[0]] = cell(SIGNPOST, BLOCKED)
    g[SILPH_RAIL_END[1], SILPH_RAIL_END[0]] = grid[SILPH_RAIL_END[1], SILPH_RAIL_END[0] - 1]   # the east railing's end post, one cell east
    hx, hy = COPYCAT_HOUSE
    for j in range(2):
        for i in range(3):
            g[hy + j, hx + i] = (g[hy + j, hx + i] & 0xFC00) | (grid[13 + j, 21 + i] & 0x3FF)
    notes['copycat_door'] = (hx + 1, hy + 1)
    return g, notes

SNAP = 2.5                                      # 5-bit colour distance a part's colour moves to FireRed's own

def sprite(name, frlg_colours=None, snap=SNAP):
    """A part, each colour within snap of a colour FireRed's Saffron already draws taking that
    colour (an invisible shift that lets the part share FireRed's palette banks); snap None
    takes every colour to its nearest (the Magnet Train deck: at most three 5-bit steps)."""
    img = np.array(Image.open(SRC / f'sprites/{name}.png').convert('RGBA'))
    if frlg_colours is not None:
        a = img[..., 3] > 0
        px = img[a][:, :3].astype(int)
        q = px >> 3
        d = np.sqrt(((q[:, None, :] - frlg_colours[None, :, :]) ** 2).sum(-1))
        near = d.min(1) <= snap if snap is not None else np.ones(len(q), bool)
        snapped = px.copy()
        snapped[near] = (frlg_colours[d.argmin(1)][near] << 3) | (frlg_colours[d.argmin(1)][near] >> 2)
        img[a, :3] = snapped
    return img

def frlg_colours(pair):
    return np.array(sorted({tuple(v >> 3 for v in c) for b in (0, 1, 2, 3, 5, 8, 10, 11, 12) for c in pair.pals[b][1:]}))

def merge_near(layers):
    """Colours one 5-bit step apart in every channel (an invisible difference; FireRed's own
    banks hold such pairs) become one, the more used of each pair, so the whole map fits
    thirteen banks exactly. layers: RGB or RGBA arrays, changed in place."""
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

GRASS_FILL, GRASS_RIM = (115, 205, 164), (65, 180, 139)   # FireRed's lawn and its tufts' darker green

def kerbs(images, full):
    """Celadon's lawn edge in Saffron's own colours: where a lawn meets paving, the lawn's
    outer pixel row turns its tufts' darker green and the paving gets a kerb (its mortar
    colour against the grass, its lightest colour behind). images: arrays changed in place."""
    lawn = np.zeros((H, W), bool)
    for x0, y0, x1, y1 in LAWNS:
        lawn[y0:y1 + 1, x0:x1 + 1] = True
    cellpx = lambda x, y: full[y * 16:y * 16 + 16, x * 16:x * 16 + 16].reshape(-1, 3)
    pave = {tuple(c) for x, y in ((38, 33), (49, 28)) for c in cellpx(x, y).tolist()}   # plain and olive paving
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
            # the lawn's rim, its paving's kerb (outermost row first), as (cell x, y, pixel row/col)
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
    """Every lawn cell replaces paving or grass, never part of a building: its FireRed
    picture (lots cleared, no lawns yet) holds only paving and grass colours."""
    kept = LAWNS, FLOWER_BEDS, TREES
    globals().update(LAWNS=[], FLOWER_BEDS=[], TREES=[])
    try:
        g, _ = edit_grid(grid)
    finally:
        globals().update(LAWNS=kept[0], FLOWER_BEDS=kept[1], TREES=kept[2])
    full = frlg.flat(*frlg.render(pair, g))
    cellc = lambda x, y: {tuple(c) for c in full[y * 16:y * 16 + 16, x * 16:x * 16 + 16].reshape(-1, 3).tolist()}
    ground = cellc(38, 33) | cellc(49, 28) | cellc(32, 45) | {tuple(c) for m in GRASS for c in
                                                             frlg.flat(*frlg.render(pair, np.array([[m]], np.uint16))).reshape(-1, 3).tolist()}
    bad = [(x, y) for x0, y0, x1, y1 in LAWNS for y in range(y0, y1 + 1) for x in range(x0, x1 + 1) if not cellc(x, y) <= ground]
    assert not bad, ('lawn over a building', bad)

def shade(bottom, top, full, fc, x, y, w, h):
    """A shadow on the ground: every pixel of the rectangle takes the FireRed colour nearest
    its own at 72% brightness (so it adds no colour), on whichever layer shows it."""
    def dark(px):
        q = (px[..., :3].astype(int) >> 3) * 0.72
        d = ((q[..., None, :] - fc[None, None, :, :]) ** 2).sum(-1)
        n = fc[d.argmin(-1)]
        return (n << 3) | (n >> 2)
    sl = np.s_[y:y + h, x:x + w]
    shown = top[sl][..., 3] > 0
    b, t, f = bottom[sl], top[sl], full[sl]
    db, dt = dark(b), dark(t)
    b[~shown] = db[~shown]
    t[..., :3][shown] = dt[shown]
    f[...] = np.where(shown[..., None], t[..., :3], b)
    return int(w * h)

def compose(engine):
    pair = frlg.Pair(engine, PRIMARY, SECONDARY)
    grid, border = frlg.layout(engine, LAYOUT)
    lawn_ground(pair, grid)
    g, notes = edit_grid(grid)
    bottom, top = frlg.render(pair, g)
    full = frlg.flat(bottom, top)
    notes['kerb_edges'] = kerbs([bottom, full], full.copy())
    fc = frlg_colours(pair)
    notes['rail_shadow_px'] = shade(bottom, top, full, fc, *RAIL_SHADOW)
    # every part on one layer, in painter's order (foot row, then left edge)
    layer = np.zeros(bottom.shape[:2] + (4,), np.uint8)
    who = np.full(bottom.shape[:2], '', '<U16')
    feet = {}
    for name, spr, X, row in sorted(PLACED, key=lambda p: (p[3], p[2])):
        img = sprite(spr, PALETTES[spr]() if spr in PALETTES else fc, SNAPS.get(spr, SNAP))
        Y = (row + 1) * 16 - img.shape[0]
        a = img[..., 3] > 0
        layer[Y:Y + img.shape[0], X:X + img.shape[1]][a] = img[a]
        who[Y:Y + img.shape[0], X:X + img.shape[1]][a] = name
        feet[name] = row
    hit = layer[..., 3] > 0
    art = hit.reshape(H, 16, W, 16).any(axis=(1, 3))
    cover = hit.reshape(H, 16, W, 16).mean(axis=(1, 3))
    owner = np.full((H, W), '', '<U16')
    for y, x in zip(*np.nonzero(art)):
        names, counts = np.unique(who[y * 16:y * 16 + 16, x * 16:x * 16 + 16][hit[y * 16:y * 16 + 16, x * 16:x * 16 + 16]],
                                  return_counts=True)
        owner[y, x] = names[counts.argmax()]
        sl = np.s_[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
        bottom[sl] = full[sl]
        top[sl] = layer[sl]
    border_bottom, border_top = frlg.render(pair, border)
    notes['merged_colours'] = len(merge_near([bottom, top, border_bottom, border_top]))
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
    for i, (im, t) in enumerate(((before, 'FireRed (SaffronCity_Frlg)'), (after, 'Ten years on'))):
        sheet.paste(Image.fromarray(im), (i * (W * 16 + 12), 24)); d.text((i * (W * 16 + 12) + 4, 6), t, fill='white')
    sheet.save(EV / 'compare.png')
    print('art cells', int(r['art'].sum()), r['notes'])

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
