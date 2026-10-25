"""Saffron's new buildings and street furniture, cut from Gen 3's own maps.

Every part is real Gen 3 pixel art: the cells of a FireRed or Emerald map, as the game
draws them, cut out and put together into a building of Saffron's own. Ground pixels round
a part (water, grass, paving) are made transparent, so a part stands on Saffron's ground.

    dojo()        The Saffron Dojo, both dojos in one building (the owner's brief): the
                  Battle Palace's hall (Emerald, Battle Frontier) widened to fourteen cells
                  under one dark tiled roof, its second roof tier over the centre bay with
                  the shared crest (half the Fighting red, half the Psychic purple), an
                  entrance each, (40, 12) and (45, 12), its noren curtain in its
                  discipline's colour: a fist on the Fighting red, an eye on the Psychic
                  purple.
    silph()       Silph Co. ten years on: FireRed's own Silph in its own materials, two
                  floors taller, its roof atrium's glass carried down the front as one spine
                  to the entrance canopy.
    lab()         Silph's research lab, built onto the tower's east side with its own glass
                  door: Mossdeep's Space Center (the observatory dome and the dish on its
                  roof deck, the glass stair column), in Silph's lavender.
    fountain(), lamp()   street furniture: Celadon's fountain (FireRed), Rustboro's street
                  lamps (Emerald).

    python3 tools/gba/maps/saffron/parts.py ENGINE_CHECKOUT    # writes source/sprites/*.png
"""
from __future__ import annotations
import json, re, sys
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(HERE), str(HERE.parent)]
import frlg                                         # noqa: E402
from tiles import Tileset                           # noqa: E402

OUT = ROOT / 'gba/art/saffron-kanto/source/sprites'
OUTLINE = (41, 49, 90)
FIGHT = [(148, 41, 41), (222, 74, 49), (255, 140, 99)]      # dark, base, light
PSYCHIC = [(98, 41, 139), (164, 82, 205), (213, 156, 246)]
WHITE = (255, 255, 255)

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

def paint(img, art, x0, y0, cols):
    for j, row in enumerate(art):
        for i, ch in enumerate(row):
            if ch in cols:
                img[y0 + j, x0 + i] = tuple(cols[ch]) + (255,)

# --------------------------------------------------------------------------- the Dojo
FIST = ["..oooooo.",
        ".owowowoo",
        "owwwwwwwo",
        "owwwwwwwo",
        ".owwwwwo.",
        "..ooooo.."]
EYE = ["...ooo...",
       ".oowwwoo.",
       "owwwppwwo",
       ".oowwwoo.",
       "...ooo..."]
DOJO_W = 224                                        # fourteen cells (36-49)
DOJO_DOORS = (72, 152)                              # the doors' centres (px in the sprite): cells 40 and 45

def dojo(engine):
    bf = source(engine, 'BattleFrontier_OutsideEast')
    hall = cells(bf, 35, 22, 44, 30)                # the Battle Palace's hall, rows 22-29, cols 35-43
    water = colours(cells(bf, 35, 22, 44, 23))
    hc = lambda *spans: np.concatenate(spans, 1)
    mid = lambda rows, n: np.tile(hall[rows, 48:56], (1, n, 1))
    R, F = slice(0, 80), slice(80, 128)             # roof (rows 22-26) and facade (27-29)
    roof = rgba(hc(hall[R, 0:48], mid(R, (DOJO_W - 96) // 8), hall[R, 96:144]))
    # the facade: its end bays, a door bay, a centre bay of shoji between two pillars, a
    # second door bay, the other end
    fac = rgba(hc(hall[F, 0:48], hall[F, 48:96], hall[F, 48:56], hall[F, 32:48], hall[F, 88:96],
                  hall[F, 48:96], hall[F, 96:144]))
    fac[:, :8, 3] = 0                               # the palace's deck planks at either end
    fac[:, -8:, 3] = 0
    body = np.concatenate([clear_from_edges(roof, water, 'tlr'), fac], 0)
    # the upper tier, eight cells, over the centre bay: a hip roof of the same tiles over a
    # band of shoji under the eave
    TW = 128
    troof = rgba(np.concatenate([hc(hall[16:44, 0:16], mid(slice(16, 44), (TW - 32) // 8), hall[16:44, 128:144]),
                                 hc(hall[66:80, 0:16], mid(slice(66, 80), (TW - 32) // 8), hall[66:80, 128:144])], 0))
    B = slice(80, 104)
    band = rgba(hc(hall[B, 8:48], hall[B, 32:48], hall[B, 96:112], hall[B, 96:136]))
    tier = np.zeros((troof.shape[0] + 24, TW, 4), np.uint8)
    tier[:troof.shape[0]] = clear_from_edges(troof, water, 'tlr')
    tier[troof.shape[0]:, 8:8 + band.shape[1]] = band
    UP = 40
    out = np.zeros((body.shape[0] + UP, DOJO_W, 4), np.uint8)
    out[UP:] = body
    x0, ty = (DOJO_W - TW) // 2, UP + 56 - tier.shape[0]
    m = tier[..., 3] > 0
    out[ty:ty + tier.shape[0], x0:x0 + TW][m] = tier[m]
    # a noren over each door, and the shared crest on the tier's band
    fy = UP + 96
    for cx, (dark, base, light), mark in ((DOJO_DOORS[0], FIGHT, FIST), (DOJO_DOORS[1], PSYCHIC, EYE)):
        for x in range(cx - 16, cx + 16):
            panel = (x - (cx - 16)) // 11
            edge = (x - (cx - 16)) % 11 in (0, 9) or x == cx + 15
            gap = (x - (cx - 16)) % 11 == 10
            for y in range(fy, fy + 13):
                if gap and y > fy:
                    continue
                out[y, x] = (light if y == fy else dark if edge or y == fy + 12 else base) + (255,)
        paint(out, mark, cx - len(mark[0]) // 2, fy + 3, dict(o=dark, w=WHITE, p=base))
    cx, cy, r = DOJO_W // 2, ty + troof.shape[0] + 11, 6
    for y in range(cy - r - 1, cy + r + 2):
        for x in range(cx - r - 1, cx + r + 2):
            d = ((x - cx + .5) ** 2 + (y - cy + .5) ** 2) ** .5
            if d <= r + 1:
                out[y, x] = OUTLINE + (255,)
            if d <= r:
                out[y, x] = (FIGHT[1] if x < cx else PSYCHIC[1]) + (255,)
            if d <= 2.2:
                out[y, x] = WHITE + (255,)
    return out

# --------------------------------------------------------------------------- Silph Co.
SILPH_EXTRA_FLOORS = 1                          # floors added to FireRed's nine (a second left too little street behind it)
FLOOR = 16                                      # FireRed's Silph: one floor every 16 px
FIRST_FLOOR, CANOPY_FROM_FOOT = 85, 35          # its first floor's top row; its entrance canopy's top, from the sprite's foot
ATRIUM = (48, 96)                               # the roof atrium's columns, which the entrance canopy shares
ATRIUM_BAND, ATRIUM_MULLION = 41, 12            # a 16-row band of the atrium's glass and its mullion within it

def silph(engine):
    """FireRed's own Silph Co., in its own materials throughout (purple roof panels, white
    rounded sides, pale teal glass, a floor line every 16 px), a floor taller; the roof
    atrium's glass carried down the whole front as one spine to the entrance canopy, which is
    the atrium's width, its mullions on the floor lines."""
    s = source(engine, 'SaffronCity')
    fr = cells(s, 29, 16, 38, 31)                   # the building and the street row under it
    floor = fr[FIRST_FLOOR + FLOOR:FIRST_FLOOR + 2 * FLOOR]
    t = np.concatenate([fr[:FIRST_FLOOR + FLOOR]] + [floor] * SILPH_EXTRA_FLOORS + [fr[FIRST_FLOOR + FLOOR:]], 0).copy()
    h = t.shape[0]
    x0, x1 = ATRIUM
    for y in range(FIRST_FLOOR, h - CANOPY_FROM_FOOT):
        t[y, x0:x1] = fr[ATRIUM_BAND + (y - (FIRST_FLOOR - 1) % FLOOR + ATRIUM_MULLION) % FLOOR, x0:x1]
    t = rgba(t)
    ground = (colours(cells(s, 28, 15, 39, 16)) | colours(cells(s, 28, 30, 29, 31)) | colours(cells(s, 38, 30, 39, 31))
              | colours(cells(s, 31, 31, 36, 32)))
    return clear_from_edges(t, ground, 'tlrb')

def lab(engine):
    ms = source(engine, 'MossdeepCity')
    t = rgba(np.concatenate([cells(ms, 60, 7, 69, 14), cells(ms, 60, 15, 69, 16)], 0))   # the Space Center, one ledge band out
    t[:15, :, 3] = 0                                # the launch towers' feet behind its roof
    top = t[:24]
    for c in ((205, 65, 82), (222, 106, 98), (115, 197, 164), (65, 180, 131), (164, 213, 197)):
        top[(top[..., :3] == c).all(-1), 3] = 0
    ground = colours(cells(ms, 59, 9, 60, 16)) | colours(cells(ms, 69, 9, 70, 16)) | colours(cells(ms, 63, 16, 66, 17))
    clear_from_edges(t, ground, 'lrb')
    remap = {(205, 213, 131): (205, 180, 246), (148, 148, 74): (164, 131, 205), (90, 82, 8): (98, 74, 139)}
    for src, dst in remap.items():
        sel = (t[..., :3] == src).all(-1)
        t[sel, :3] = dst
    return t

# --------------------------------------------------------------------------- street furniture
def fountain(engine):
    c = source(engine, 'CeladonCity')
    t = rgba(cells(c, 12, 19, 15, 22))
    clear_from_edges(t, colours(cells(c, 11, 19, 12, 22)) | colours(cells(c, 15, 19, 16, 22)), 'tlrb')
    g = t[..., :3].astype(int)
    t[(g[..., 1] > g[..., 0] + 30) & (g[..., 1] > g[..., 2] + 10), 3] = 0        # the lawn's grass tufts
    return t

def lamp(engine):
    """Rustboro's street lamp, one cell by two, without Rustboro's paving: its warm stones,
    pale speckles and grey cast shadow are left behind, so it stands on grass or paving."""
    r = source(engine, 'RustboroCity')
    t = rgba(cells(r, 19, 15, 20, 17))
    g = t[..., :3].astype(int)
    t[(g[..., 0] > g[..., 2] + 8) & (g[..., 1] > g[..., 2] + 8), 3] = 0     # the warm paving and its shadow
    t[(g == (205, 213, 230)).all(-1), 3] = 0                                # the paving's pale speckles
    shadow = (g == (131, 131, 139)).all(-1)                                 # the cast shadow, grey on paving, east and south of the post's foot
    shadow[:27] = False
    shadow[27:, :10] = False
    shadow[30:] = (g[30:] == (131, 131, 139)).all(-1)
    t[shadow, 3] = 0
    return t

PARTS = dict(dojo=dojo, silph=silph, lab=lab, fountain=fountain, lamp=lamp)

def main(engine):
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in PARTS.items():
        img = fn(engine)
        Image.fromarray(img).save(OUT / f'{name}.png')
        print(name, img.shape[1], 'x', img.shape[0], 'colours', len(colours(img[img[..., 3] > 0][:, :3][None])))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
