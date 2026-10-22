"""Blackthorn's buildings and props, drawn as Gen 3 pixel art.

Each function returns an RGBA array whose bottom edge sits on the bottom of the
object's lowest blocked cell. Geometry is drawn fresh at native resolution (flat
front walls, banded domes, one-pixel dark outlines). The houses and the standing
stone fill their shapes with HGSS's own texture for that object, reduced to a few
shades (source/elements/hgss-building-textures/); the Gym and the gate posts are
drawn in explicit Gen 3 ramps taken from those textures' colours.

    python3 tools/gba/maps/blackthorn/sprites.py   # writes source/elements/sprites.png
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = ROOT / 'gba/art/blackthorn-city/source/elements'
TEX = OUT / 'hgss-building-textures'

def tex(name):
    return np.array(Image.open(TEX / f'{name}.png').convert('RGBA'))

def canvas(w, h):
    return np.zeros((h, w, 4), np.uint8)

def rect(img, x0, y0, x1, y1, c):
    img[max(0, y0):y1, max(0, x0):x1] = tuple(c[:3]) + (255,)

def paste(img, src, x, y):
    h, w = src.shape[:2]
    a = src[..., 3] > 0
    img[y:y + h, x:x + w][a] = src[a]

def outline(img, c):
    """One-pixel outline along the inside edge of the opaque area."""
    a = img[..., 3] > 0
    pad = np.pad(a, 1)
    edge = a & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    img[edge] = tuple(c) + (255,)

def shade(img, mask, cx, cy, rx, ry, strength=0.35):
    """Darken a dome away from an upper-left light."""
    ys, xs = np.nonzero(mask)
    nx, ny = (xs - cx) / rx, (ys - cy) / ry
    f = 1 + strength * (-0.6 * nx - 0.8 * ny) * 0.9
    img[ys, xs, :3] = np.clip(img[ys, xs, :3] * f[:, None], 0, 255).astype(np.uint8)

def shade_sym(img, mask, cx, cy, rx, ry, strength=0.35):
    """Gen 3 dome shading: horizontal bands that darken toward the base, plus a darker
    rim along the outline. Rows repeat across the dome and the halves mirror, so the
    dome packs into few tiles."""
    ys, xs = np.nonzero(mask)
    ny = (ys - cy) / ry
    f = 1 + strength * (-0.8 * ny) * 0.9
    pad = np.pad(mask, 3)
    inner = np.ones_like(mask)
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            if abs(dx) + abs(dy) <= 3:
                inner &= pad[3 + dy:3 + dy + mask.shape[0], 3 + dx:3 + dx + mask.shape[1]]
    rim = ~inner[ys, xs]
    f = np.where(rim, f * 0.82, f)
    img[ys, xs, :3] = np.clip(img[ys, xs, :3] * f[:, None], 0, 255).astype(np.uint8)

def posterize(img, mask, n):
    """Reduce the colours under mask to n representative shades (by luminance bins)."""
    ys, xs = np.nonzero(mask)
    c = img[ys, xs, :3].astype(float)
    lum = c @ np.array([0.3, 0.59, 0.11])
    edges = np.quantile(lum, np.linspace(0, 1, n + 1))
    k = np.clip(np.searchsorted(edges[1:-1], lum), 0, n - 1)
    for i in range(n):
        if (k == i).any():
            img[ys[k == i], xs[k == i], :3] = np.median(c[k == i], 0).astype(np.uint8)

def tiled(src, w, h, ox=0, oy=0):
    ys, xs = np.mgrid[0:h, 0:w]
    return src[(ys + oy) % src.shape[0], (xs + ox) % src.shape[1]]

# --------------------------------------------------------------------------- thatched hut
def hut():
    """Blackthorn house: straw dome with a dormer over a plank front, green door, window.
    64 x 80 (four cells); the dome's crown rises into the row above the footprint."""
    t = tex('fu_h01')
    straw = t[0:45, 0:24]                       # one wrap of straw: light crown to dark eave
    img = canvas(64, 80)
    ys, xs = np.mgrid[0:80, 0:64]
    cx, cy, rx, ry, eave = 31.5, 42.0, 31.0, 41.0, 55
    dome = (((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2 <= 1.0) & (ys <= eave)
    v = np.clip(((ys - 1) / (eave - 1) * 41).astype(int), 0, 41)          # straw courses by height
    u = xs % 8                                   # the straw repeats every 8 px
    fill = straw[v, u]
    img[dome] = fill[dome]
    shade_sym(img, dome, cx, 30, 32, 40, 0.35)
    posterize(img, dome, 5)
    # ragged eave: the strip's own scalloped fringe
    fringe = straw[41:45]
    for x in range(1, 63):
        for k in range(4):
            if fringe[k, x % 24, 3] and dome[eave, x]:
                img[eave + 1 + k - 1, x] = fringe[k, x % 24]
    # dormer
    rect(img, 23, 17, 41, 34, (96, 64, 38))
    rect(img, 25, 19, 39, 34, (36, 32, 44))
    rect(img, 25, 19, 39, 21, (140, 96, 52))
    rect(img, 22, 33, 42, 35, (96, 64, 38))
    # front wall: golden planks between dark corner posts
    rect(img, 6, 58, 58, 78, (200, 150, 72))
    for y in range(61, 78, 4):
        rect(img, 6, y, 58, y + 1, (164, 118, 58))
    rect(img, 6, 58, 58, 59, (228, 182, 98))
    for x0 in (4, 54):
        rect(img, x0, 54, x0 + 6, 78, (78, 52, 32)); rect(img, x0 + 1, 54, x0 + 2, 78, (128, 88, 50))
    # door (second cell) from fu_door1, window (third cell) from h_mado
    door = tex('fu_door1')[0:28, 0:24]
    dimg = np.array(Image.fromarray(door).resize((14, 18), Image.Resampling.NEAREST))
    rect(img, 15, 59, 31, 78, (40, 30, 24)); paste(img, dimg, 16, 60)
    win = tex('h_mado')
    rect(img, 35, 60, 51, 71, (78, 52, 32))
    paste(img, np.array(Image.fromarray(win).resize((14, 9), Image.Resampling.NEAREST)), 36, 61)
    rect(img, 42, 61, 43, 70, (110, 74, 44)); rect(img, 36, 65, 50, 66, (110, 74, 44))
    rect(img, 34, 72, 52, 75, (128, 128, 136)); rect(img, 34, 74, 52, 75, (92, 92, 100))
    outline(img, (64, 44, 26))
    img[78:] = 0
    # the dome, dormer and eave are mirror-symmetric (shared tiles through flips)
    img[:56, 32:] = img[:56, :32][:, ::-1]
    return img

# --------------------------------------------------------------------------- gate post
POST = {'o': (56, 40, 24), 'd': (104, 76, 48), 'm': (148, 112, 72), 'l': (188, 152, 104), 'h': (216, 184, 128),
        'p': (120, 108, 48), 's': (88, 76, 32)}
POST_ART = [            # 16 x 40: a dead trunk with a split crown, two stubs and a root flare
    '..oo.....oo.....',
    '.ohdo...oldo....',
    '.ohmdo.odmdo....',
    '..ohmdodmmdo..oo',
    '..ohlmddmmdo.old',
    '...ohlmdmmddold.',
    '...ohlmmdmmdddo.',
    '...ohlmmdmmdo...',
    '...ohllmdmmdo...',
    '...ohllmdmmdo...',
    '...ohllmdmmdo...',
    'oo.ohllmdmmdo...',
    'ldoohllmdmmdo...',
    'olddhllmdmmdo...',
    '.oodlhlmdmmdo...',
    '...ohllmdmmdo...',
    '...ohllmdmmdo...',
    '...ohhllmdmdo...',
    '...ohhllmdmdo...',
    '...ohlhlmmddo...',
    '...ohlhlmmddo...',
    '...ohlhhlmddo...',
    '...ohlhhlmddo...',
    '...ohlhhlmddo...',
    '...ohllhlmddo...',
    '...ohllhlmddo...',
    '...ohlllmmddo...',
    '...ohlmlmmddo...',
    '...ohlmmmmddo...',
    '...ohlmmdmddo...',
    '..ohlmmmdmmddo..',
    '..ohlmmdddmmmdo.',
    '.ohlmmddsddmmmdo',
    '.ohmmddsssddmmdo',
    '.odddossssssoddo',
    '.oppssssssssppo.',
    '..opppsssssppo..',
    '...oopppppppoo..',
    '.....ooooooo....',
    '................',
]

def gate_post(mirror=False):
    """The billboard gate post south of the Mart: a dead trunk drawn in Gen 3 terms,
    16 x 40 so it stays inside its own cell column (a player beside it is never
    overlapped); its ground patch sits under the trunk's blocked cell."""
    img = canvas(16, 40)
    for y, row in enumerate(POST_ART):
        for x, ch in enumerate(row):
            if ch != '.':
                img[y, x] = POST[ch] + (255,)
    return img[:, ::-1].copy() if mirror else img

# --------------------------------------------------------------------------- standing stone
def standing_stone():
    """The grey stone beside the west house (fu_rock texture), 32 x 56, jagged crown."""
    rock = tex('fu_rock')
    img = canvas(32, 56)
    ys, xs = np.mgrid[0:56, 0:32]
    half = np.clip((ys - 1) * 0.62, 0, 14.5)
    body = (np.abs(xs - 15.5 + (ys < 20) * (20 - ys) * 0.15) <= half) & (ys >= 1)
    body &= ~((ys < 14) & (xs > 20))
    body &= ~((ys > 44) & (np.abs(xs - 15.5) > 13 - (ys - 44) * 0.2))
    img[body] = tiled(rock, 32, 56)[body]
    shade(img, body, 14, 30, 16, 28, 0.5)
    posterize(img, body, 4)
    for (x0, y0, dx) in ((12, 16, 1), (19, 28, -1), (9, 38, 1)):
        for i in range(8):
            yy, xx = y0 + i, x0 + (i * dx) // 2
            if body[yy, xx]:
                img[yy, xx] = (70, 70, 78, 255)
    outline(img, (52, 52, 60))
    return img

# --------------------------------------------------------------------------- gym
GYM = dict(line=(56, 40, 48), wood=[(208, 168, 120), (176, 136, 96), (144, 104, 72), (112, 80, 56)],
           beam=[(248, 184, 104), (232, 128, 48), (192, 88, 32), (144, 56, 24)],
           hall=[(236, 228, 244), (204, 196, 222), (170, 162, 196)], band=[(168, 128, 216), (124, 84, 180)],
           red=[(208, 72, 56), (160, 44, 36), (112, 28, 28)], glass=[(176, 220, 248), (104, 164, 220)],
           frame=(112, 112, 128))

def gym():
    """Blackthorn Gym, redrawn in Gen 3 terms: a plank barrel roof (planks running front
    to back, a dark spine down the middle) on a round lavender hall with two purple
    bands, two orange beams that rise above the roof and splay out to the hall's foot,
    orange corner posts, red emblem panel over glass doors. 112 x 128: seven cells
    wide, the six blocked rows plus two rows of roof over the pond. Shading runs across
    the roof in 8 px plank columns and the halves mirror, so it packs into few tiles."""
    C = GYM
    img = canvas(112, 128)
    ys, xs = np.mgrid[0:128, 0:112]
    dx = np.abs(xs - 55.5)
    put = lambda m, c: img.__setitem__(m, tuple(c) + (255,))
    # hall: a drum; its foot and bands bow toward the viewer at the middle
    bow = lambda k: k + np.floor(3.5 * np.sqrt(np.clip(1 - (dx / 52) ** 2, 0, 1)))
    hall = (dx <= 52) & (ys >= 72) & (ys <= bow(115))
    put(hall, C['hall'][1])
    put(hall & (ys <= bow(80)), C['hall'][0])
    put(hall & (ys >= bow(111)), C['hall'][2])
    for b in (95, 103):
        put(hall & (ys >= bow(b)) & (ys < bow(b + 2)), C['band'][0])
        put(hall & (ys >= bow(b + 2)) & (ys < bow(b + 4)), C['band'][1])
    put(hall & (dx >= 48), C['hall'][2])
    # barrel roof: rounded back, straight sides, front edge bowed over the hall
    top = 12 + np.round(28 * (1 - np.sqrt(np.clip(1 - (dx / 47) ** 2, 0, 1))))
    roof = (dx <= 47) & (ys >= top) & (ys <= bow(74))
    col = np.minimum(3, (dx // 12).astype(int))               # plank columns lighter at the crown
    for k in range(4):
        put(roof & (col == k), C['wood'][k])
    put(roof & (xs % 8 == 0), C['wood'][3])                     # plank seams every 8 px
    put(roof & (col < 3) & (xs % 8 == 1), C['wood'][max(0, 0)])
    spine = roof & (dx < 6)
    put(spine, C['wood'][2]); put(spine & (ys % 4 == 0), C['wood'][3])
    put(roof & (ys >= bow(71)), C['wood'][3])                   # eave
    # beams: rise above the roof, run down its front, then splay to the hall's foot
    for y in range(4, 117):
        t = 0.0 if y < 66 else ((y - 66) / 50) ** 1.4
        x0 = int(np.floor(55.5 - (19 + 17 * t))) - 3
        for k in range(7):
            img[y, x0 + k] = tuple(C['beam'][0 if k < 2 else 1 if k < 5 else 2]) + (255,)
        if y == 4:                                              # rounded horn tips
            img[y, x0] = img[y, x0 + 6] = 0
        if y < 12:
            img[y, x0 + 3] = tuple(C['beam'][2]) + (255,)
    # corner posts
    for x0 in (2,):
        rect(img, x0, 66, x0 + 9, 117, C['beam'][1]); rect(img, x0 + 1, 66, x0 + 3, 117, C['beam'][0])
        rect(img, x0 + 7, 66, x0 + 9, 117, C['beam'][2]); rect(img, x0, 64, x0 + 9, 67, C['beam'][3])
    # windows
    for x0 in (16, 26):
        rect(img, x0 - 1, 83, x0 + 8, 93, C['frame'])
        rect(img, x0, 84, x0 + 7, 92, C['glass'][1]); rect(img, x0 + 1, 85, x0 + 3, 91, C['glass'][0])
        rect(img, x0 + 3, 84, x0 + 4, 92, C['frame'])
    # red emblem panel with the Gym emblem
    rect(img, 42, 62, 56, 86, C['red'][1]); rect(img, 42, 62, 56, 64, C['red'][0]); rect(img, 42, 84, 56, 86, C['red'][2])
    emblem = tex('fu_gym_w')[19:30, 0:16]
    e = emblem[..., 3] > 0
    for (yy, xx) in zip(*np.nonzero(e[:, :8])):
        lum = int(emblem[yy, xx, :3].astype(int).sum())
        img[67 + yy, 48 + xx] = (248, 248, 248, 255) if lum > 500 else tuple(C['red'][2]) + (255,)
    # glass doors
    rect(img, 45, 92, 56, 118, C['frame'])
    rect(img, 47, 94, 56, 118, C['glass'][1]); rect(img, 48, 95, 51, 117, C['glass'][0])
    rect(img, 55, 94, 56, 118, C['frame'])
    img[:, 56:] = img[:, :56][:, ::-1]                          # mirror-symmetric facade
    outline(img, C['line'])
    return img

def sheet():
    parts = [hut(), gate_post(), gate_post(True), standing_stone(), gym()]
    w = sum(p.shape[1] * 4 + 16 for p in parts); h = max(p.shape[0] for p in parts) * 4 + 16
    out = Image.new('RGBA', (w, h), (226, 200, 140, 255))
    x = 8
    for p in parts:
        out.alpha_composite(Image.fromarray(p, 'RGBA').resize((p.shape[1] * 4, p.shape[0] * 4), Image.Resampling.NEAREST), (x, 8))
        x += p.shape[1] * 4 + 16
    out.save(OUT / 'sprites.png')

if __name__ == '__main__':
    sheet()
