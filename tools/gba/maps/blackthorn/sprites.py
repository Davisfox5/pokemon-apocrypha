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

GREY = [(56, 54, 52), (96, 92, 86), (128, 124, 116), (160, 156, 146), (192, 188, 176)]   # warm stone grey; Gym frames

# --------------------------------------------------------------------------- thatched hut
STRAW = [(240, 212, 140), (224, 192, 120), (204, 168, 100), (180, 144, 84), (150, 114, 64), (116, 84, 48)]
STRAW_LINE = (84, 58, 32)
HUT_PALETTE = STRAW + [STRAW_LINE, (36, 30, 32), (200, 150, 72), (132, 92, 48), (8, 90, 41), (16, 120, 60),
                       (206, 206, 231), (255, 255, 255)]                      # 15 colours: one bank

def snap(img, palette):
    """Snap every opaque pixel to its nearest palette colour (keeps a sprite's ramp small)."""
    a = img[..., 3] > 0
    p = np.array(palette, float)
    c = img[a][:, :3].astype(float)
    img[a, :3] = p[((c[:, None] - p[None]) ** 2).sum(-1).argmin(1)].astype(np.uint8)

def hut():
    """Blackthorn house, shaped from HGSS's own house model seen through Blackthorn's field
    camera (camera type 0, 48.7 degrees): a small rounded crown sitting on a wide,
    low-pitched thatch skirt that overhangs the walls, straw strands running down the
    slope, a dormer on the skirt below the crown, a ragged eave; under it a plank front
    with dark corner posts, a green door and a window. 64 x 80 (four cells); the crown
    rises into the row above the footprint. Mirror-symmetric above the eave, so the two
    roof halves share tiles."""
    img = canvas(64, 80)
    ys, xs = np.mgrid[0:80, 0:64]
    dx = np.abs(xs - 31.5)
    # silhouettes: the crown is a rounded cap; the skirt's shoulder curves out from under
    # it to the full width, then falls almost straight to a low eave that bows forward
    shoulder = 13 + 16 * (1 - np.sqrt(np.clip(1 - ((dx - 16) / 16.5) ** 2, 0, 1)))
    skirt_top = np.where(dx <= 16, 13, shoulder)
    eave = 54 + np.floor(2.5 * np.sqrt(np.clip(1 - (dx / 32) ** 2, 0, 1)))
    half = np.where(ys < 44, 32.0, 32 - (ys - 44) * 0.3)
    skirt = (ys >= skirt_top) & (ys <= eave) & (dx <= half)
    crown = ((dx / 18) ** 2 + ((ys - 14) / 13) ** 2 <= 1) & (ys <= 22)
    # straw: strands run down the slope, two pixels wide, broken into uneven lengths
    ang = np.arctan2(xs - 31.5, ys + 30)
    strand = np.floor(np.abs(ang) * 34).astype(int)
    phase = (strand * 7) % 11
    brk = ((ys + phase) % 11 < 2)
    tone = (strand % 2) + brk
    roof = skirt | crown
    k = np.zeros(ys.shape, int)
    k[skirt] = 1 + tone[skirt] + (ys[skirt] > 34) + (ys[skirt] > eave[skirt] - 5)
    k[skirt & (dx >= 27)] += 1                                  # rounding away at the sides
    k[crown] = tone[crown] + (ys[crown] > 9)
    k[crown & (dx >= 14)] += 1
    k = np.clip(k, 0, 5)
    for i, c in enumerate(STRAW):
        img[roof & (k == i)] = c + (255,)
    # the crown's ragged lip where it overhangs the skirt
    rim = crown & ~((dx / 18) ** 2 + ((ys - 13) / 13) ** 2 <= 1)
    img[rim] = STRAW[4] + (255,)
    for x in range(14, 50):
        r = int(np.ceil(14 + 13 * np.sqrt(max(0.0, 1 - ((x - 31.5) / 18) ** 2))))
        if r <= 22 and (x * 5) % 3 == 0:
            img[min(r, 23), x] = STRAW[5] + (255,)
    # dormer on the skirt, just under the crown's lip
    rect(img, 24, 24, 40, 37, (96, 64, 38)); rect(img, 26, 26, 38, 37, (36, 32, 44))
    rect(img, 26, 26, 38, 28, (140, 96, 52)); rect(img, 23, 36, 41, 38, (96, 64, 38))
    # ragged eave: straw tips hanging below the skirt's edge
    for x in range(1, 63):
        e = int(eave[0, x])
        if dx[0, x] <= half[e, x]:
            for t in range(1 + (x * 7 % 5 == 0) + (x % 3 == 0)):
                img[e + 1 + t, x] = (STRAW[4] if t == 0 else STRAW[5]) + (255,)
    img[:56, 32:] = img[:56, :32][:, ::-1]                    # mirror the roof
    # front wall: golden planks between dark corner posts, shadowed under the eave
    top = 55
    rect(img, 5, top, 59, 77, (200, 150, 72))
    for y in range(top + 4, 77, 4):
        rect(img, 5, y, 59, y + 1, (164, 118, 58))
    rect(img, 5, top, 59, top + 3, (132, 92, 48))
    for x0 in (3, 55):
        rect(img, x0, top - 1, x0 + 6, 77, (78, 52, 32)); rect(img, x0 + 1, top + 2, x0 + 2, 77, (128, 88, 50))
    door = tex('fu_door1')[0:25, 0:24]            # the green leaf only; HGSS's dark threshold rows dropped
    dimg = np.array(Image.fromarray(door).resize((14, 76 - (top + 3)), Image.Resampling.NEAREST))
    rect(img, 15, top + 2, 31, 77, (40, 30, 24)); paste(img, dimg, 16, top + 3)   # one dark sill row left
    win = tex('h_mado')
    rect(img, 35, top + 3, 51, top + 13, (78, 52, 32))
    paste(img, np.array(Image.fromarray(win).resize((14, 8), Image.Resampling.NEAREST)), 36, top + 4)
    rect(img, 42, top + 4, 43, top + 12, (110, 74, 44)); rect(img, 36, top + 8, 50, top + 9, (110, 74, 44))
    rect(img, 34, top + 14, 52, top + 17, (132, 92, 48)); rect(img, 34, top + 16, 52, top + 17, STRAW_LINE)   # window box
    rect(img, 3, 77, 61, 78, (96, 72, 44))                      # sill along the ground
    outline(img, STRAW_LINE)
    img[78:] = 0
    snap(img, HUT_PALETTE)
    return img

# --------------------------------------------------------------------------- gate post
POST = {'o': (88, 64, 64), 'd': (104, 72, 48), 'm': (136, 96, 72), 'l': (184, 136, 104), 'h': (200, 168, 112),
        'p': (96, 88, 72), 's': (104, 88, 88)}            # CherrygrovePrimary's wood ramp (bank 2)
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
    """The standing stone beside the west house, from HGSS's stone model (235) seen through
    Blackthorn's field camera: a tall rounded stone leaning slightly, a smaller lobe at its
    lower left, lit from the upper left in four bands of warm grey, a few etched cracks;
    sized against the house by that same camera view (about 0.6 of its height).
    32 x 56, its base on the bottom of its lowest blocked cell."""
    img = canvas(32, 56)
    ys, xs = np.mgrid[0:56, 0:32].astype(float)
    def lobe(cx, cy, rx, ry, taper=0.0):
        """Height field of an upright egg (narrower toward the top by taper)."""
        w = rx * (1 - taper * np.clip((cy - ys) / ry, 0, 1))
        return np.sqrt(np.clip(1 - ((xs - cx) / w) ** 2 - ((ys - cy) / ry) ** 2, 0, None))
    main = lobe(18.5, 38, 13, 29, taper=0.6)                      # a broad cone with a rounded peak
    head = lobe(18.5, 21, 8.5, 12) * 0.92                        # the upper lump, blended into it
    side = lobe(9.5, 47, 8.5, 8.5) * 0.85                        # the lobe at the lower left
    hip = lobe(24.5, 45, 6.5, 9.5) * 0.9                         # and a bulge at the lower right
    shoulder = lobe(12.5, 30, 6, 8) * 0.85                       # a lump on the left flank
    h = np.maximum.reduce([main, head, side, hip, shoulder])
    body = (h > 0) & (ys <= 54)
    gy, gx = np.gradient(h)
    n = np.stack([-gx * 6, -gy * 6, np.ones_like(h)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    light = n @ np.array([-0.55, -0.6, 0.58]) / np.linalg.norm([-0.55, -0.6, 0.58])
    band = np.digitize(light, [0.35, 0.6, 0.82])               # 0 darkest .. 3 lightest
    ridge = xs > 17 + (ys - 10) * 0.12                           # a facet edge down the stone: the right face turns away
    band = np.where(ridge & (np.maximum(main, head) >= np.maximum.reduce([side, hip, shoulder])), np.minimum(band, 2) - (band > 0), band)
    band = np.clip(band, 0, 3)
    for k in range(4):
        img[body & (band == k)] = GREY[k + 1] + (255,)
    # shadowed creases where one lump tucks under another
    for a, b, y0 in ((side, main, 40), (hip, main, 40), (shoulder, main, 28)):
        crease = body & (a > 0) & (np.abs(a - b) < 0.07) & (ys > y0)
        img[crease] = GREY[1] + (255,)
    for pts in (((15, 17), (17, 20), (16, 23)), ((22, 29), (20, 32), (22, 36)), ((13, 41), (15, 45))):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):           # etched cracks
            for t in np.linspace(0, 1, 2 * max(abs(x1 - x0), abs(y1 - y0)) + 1):
                x, y = int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t))
                if body[y, x]:
                    img[y, x] = GREY[1] + (255,)
    outline(img, GREY[0])
    snap(img, GREY)
    return img

# --------------------------------------------------------------------------- gym
GYM = dict(line=(56, 40, 48), wood=[(208, 168, 120), (176, 136, 96), (144, 104, 72), (112, 80, 56)],
           beam=[(248, 184, 104), (232, 128, 48), (192, 88, 32), (144, 56, 24)],
           hall=[(236, 228, 244), (204, 196, 222), (170, 162, 196)], band=[(168, 128, 216), (124, 84, 180)],
           red=[(208, 72, 56), (160, 44, 36), (112, 28, 28)], glass=[(176, 220, 248), (104, 164, 220)],
           frame=GREY[2])

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
