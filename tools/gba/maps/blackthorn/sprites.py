"""Blackthorn's buildings and props as Gen 3 sprites.

    python3 tools/gba/maps/blackthorn/sprites.py PATH/TO/pokeheartgold

The houses (model 132 with door 133) and the Gym (139 with door 16) are HGSS's own models
and textures rendered at C06's angle (hgss_camera.view: 38 degrees, 16 px per tile up the
screen, each squeezed across to fit its footprint as C06 is), so roof pitch and doors
match the Center beside them, then finished as Gen 3 art: the house in its own 14 colours
(k-means) with HGSS's straw lifted toward the golden straw of Blackthorn's first houses,
the Gym in 14 picked by family from its render (roof wood, purple bands, hall, beams,
emblem, glass), C06's outline colour round the silhouette, each roof mirrored on an 8 px
axis so its halves share tiles, the Gym's roof seams and the door's planks drawn back where
14 colours swallow them, and tiles that differ only by a one-pixel edge shift folded
together. The gate posts and the standing stone are drawn at native resolution.

Writes source/elements/sprites/*.png (what elements.py places) and the contact sheet
source/elements/sprites.png. Each sprite's bottom edge is the bottom of its object's base
row.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = ROOT / 'gba/art/blackthorn-city/source/elements'
SPRITES = OUT / 'sprites'

def canvas(w, h):
    return np.zeros((h, w, 4), np.uint8)

def outline(img, c):
    """One-pixel outline along the inside edge of the opaque area."""
    a = img[..., 3] > 0
    pad = np.pad(a, 1)
    edge = a & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    img[edge] = tuple(c) + (255,)

def snap(img, palette):
    """Snap every opaque pixel to its nearest palette colour (keeps a sprite's ramp small)."""
    a = img[..., 3] > 0
    p = np.array(palette, float)
    c = img[a][:, :3].astype(float)
    img[a, :3] = p[((c[:, None] - p[None]) ** 2).sum(-1).argmin(1)].astype(np.uint8)

# Stone grey: the grey ramp of Cherrygrove's Center palette (bank 8, loaded for the shared
# Center), so stone tiles need no learned palette.
GREY = [(56, 56, 72), (96, 104, 96), (120, 120, 112), (168, 168, 160), (216, 216, 208)]

# --------------------------------------------------------------------------- buildings
C06_LINE = (41, 41, 49)                  # the owner-locked C06 Center's outline
DOOR = (0.15625, 0, 0.75)                # each door's offset from its building in HGSS's placements
# name: (model parts, width px, roof mirror (rows, axis, cols))
RENDERS = {
    'house': ([(132, (0, 0, 0)), (133, DOOR)], 64, (51, 32, 64)),
    'gym': ([(139, (0, 0, 0)), (16, (0, 0, 1.3125))], 112, (999, 56, 112)),
}
# The Gym in 14 colours picked by family from its own render's colour clusters (the rest
# fold into the nearest): roof wood light, mid, dark; the purple bands; the hall's two
# greys; the beams' light, lit face and orange; one rust for the beams' shadow side and the
# emblem's face; the emblem's lit top and dark underside; the door glass.
GYM_PALETTE = [(176, 136, 104), (152, 112, 72), (120, 88, 56), (136, 96, 192), (112, 72, 168),
               (200, 184, 184), (168, 152, 152), (248, 192, 144), (232, 152, 88), (240, 112, 24),
               (184, 88, 40), (208, 112, 104), (112, 32, 0), (88, 160, 208)]

def sprite_palette(rgba, n=14):
    """A sprite's own colours: weighted k-means over its 5-bit colours with farthest-first
    seeds, so a small accent (a door's knob, a window) keeps its own colour."""
    import build as B
    px = rgba[rgba[..., 3] > 0][:, :3] >> 3
    uc, cnt = np.unique(px, axis=0, return_counts=True)
    return [tuple(int(v) << 3 | int(v) >> 2 for v in c) for c in B.kmeans_colors(uc, np.sqrt(cnt).astype(float), n)]

def finish(rgba, pal, mirror=None):
    """Mirror the roof's left half onto its right, map to the sprite's palette, then outline
    the silhouette in C06's outline colour."""
    img = rgba.copy()
    if mirror:
        rows, axis, cols = mirror
        left = img[:rows, axis - (cols - axis):axis]
        img[:rows, axis:cols] = left[:, ::-1]
    a = img[..., 3] > 0
    p = np.array(pal, int)
    img[..., :3] = p[((img[..., :3][..., None, :].astype(int) - p[None, None]) ** 2).sum(-1).argmin(-1)]
    img[~a] = 0
    outline(img, C06_LINE)
    return img

# Fine lines the render loses at 14 colours, drawn back one pixel wide, each pixel one step
# darker on its surface's own ramp: the Gym's en_gyma planks carry two dark seams (texture
# rows 7-8 and 23-24) that arc across each roof shell; the house door's fu_door1 is green
# planks, a dark 2-texel stripe every 4 texels. A marker render at 4x finds where they fall.
# name: (texture, surface (rows, cols), stripes, 'rows' for horizontal stripes given as row
# ranges or 'cols' for vertical ones given as column ranges)
SEAMS = {'gym': ('en_gyma', ((0, 32), (14, 60)), ((7, 9), (23, 25)), 'rows'),
         'house': ('fu_door1', ((0, 26), (0, 24)), tuple((a, a + 2) for a in range(2, 24, 4)), 'cols')}
# The thatch keeps HGSS's own straw (fu_h01's left block) lifted toward the golden straw of
# Blackthorn's first Gen 3 houses: the DS texture is a muted tan that reads grey on the GBA.
# name: (texture, (rows, cols), per-channel gain)
LIFT = {'house': ('fu_h01', ((0, 48), (0, 24)), (1.16, 1.13, 1.0))}

def marked(C, models, parts, width, height, name, paint, z=4):
    """Per sprite pixel, the share of it that shows each marker colour (green, magenta) of a
    render where paint(texture) recolours the named texture's regions."""
    big, _ = C.view(models, parts, width * z, sy=C.C06_SCALE * z, retex={name: paint})
    h = height * z
    big = big[-h:] if big.shape[0] >= h else np.pad(big, ((h - big.shape[0], 0), (0, 0), (0, 0)))
    rgb = big[..., :3].astype(int)
    cover = lambda m: m.reshape(height, z, width, z).mean(axis=(1, 3))
    green = cover((rgb[..., 0] < 60) & (rgb[..., 1] > 200) & (rgb[..., 2] < 60))
    magenta = cover((rgb[..., 0] > 200) & (rgb[..., 1] < 60) & (rgb[..., 2] > 200))
    return green, magenta

def seam_mask(C, models, parts, width, height, name, surface, stripes, axis):
    """(seam, surface): per sprite pixel, the seam line (one pixel per stripe crossing, along
    the stripe's run) and the surface it lies on."""
    (r0, r1), (c0, c1) = surface
    def mark(t):
        t = t.copy()
        t[r0:r1, c0:c1, :3] = (0, 255, 0)
        for a, b in stripes:
            if axis == 'rows':
                t[a:b, c0:c1, :3] = (255, 0, 255)
            else:
                t[r0:r1, a:b, :3] = (255, 0, 255)
        return t
    green, seam = marked(C, models, parts, width, height, name, mark)
    s = seam if axis == 'rows' else seam.T                 # thin each band to its strongest pixel
    line = np.zeros(s.shape, bool)
    for x in range(s.shape[1]):
        y = 0
        while y < s.shape[0]:
            if s[y, x] > 0.25:
                y1 = y
                while y1 < s.shape[0] and s[y1, x] > 0.25:
                    y1 += 1
                line[y + int(np.argmax(s[y:y1, x])), x] = True
                y = y1
            else:
                y += 1
    return (line if axis == 'rows' else line.T), (green + seam) > 0.5

def lift(C, models, parts, width, rgba, name, region, gain):
    """Scale the colours of the pixels that show the region of the named texture."""
    (r0, r1), (c0, c1) = region
    def mark(t):
        t = t.copy()
        t[r0:r1, c0:c1, :3] = (0, 255, 0)
        return t
    green, _ = marked(C, models, parts, width, rgba.shape[0], name, mark)
    img = rgba.copy()
    m = (green > 0.5) & (img[..., 3] > 0)
    img[m, :3] = np.clip(img[m, :3].astype(float) * np.array(gain), 0, 255).astype(np.uint8)
    return img

def draw_seams(img, mask, floor=None):
    """Each seam pixel one step darker on the surface's ramp (the colours covering at least a
    twentieth of it, light to dark); on the darkest, `floor` when given (a door's plank gaps
    go to the outline colour), else unchanged."""
    line, plank = mask
    img = img.copy()
    on = plank & (img[..., 3] > 0)
    cols, cnt = np.unique(img[on][:, :3], axis=0, return_counts=True)
    ramp = sorted((tuple(int(v) for v in c) for c, k in zip(cols, cnt) if k >= 0.05 * on.sum()), key=sum)
    ramp = ([tuple(floor)] if floor else []) + ramp
    step = {c: ramp[max(i - 1, 0)] for i, c in enumerate(ramp)}
    for y, x in zip(*np.nonzero(line & on)):
        c = tuple(int(v) for v in img[y, x, :3])
        if c in step:
            img[y, x, :3] = step[c]
    return img

# Tile reuse, the way a Gen 3 artist trims a tileset: a building tile that differs from a
# more common tile of its sprite (any flip) only where an edge sits a pixel over or a render
# speck sits (at most REUSE pixels, each taking a colour its own 4-neighbour already had,
# same silhouette) becomes that tile. Drawn detail (the Gym's roof seams) is kept: a fold
# may not touch it. Sprites are bottom-aligned on cells, so the 8 px grid runs up from the
# bottom edge.
REUSE = 12
FLIPS = [(False, False), (True, False), (False, True), (True, True)]

def flip(t, f):
    t = t[:, ::-1] if f[0] else t
    return t[::-1] if f[1] else t

def edge_shift(old, new, diff):
    o, n, oa = old[..., :3].astype(int), new[..., :3].astype(int), old[..., 3] > 0
    for y, x in zip(*np.nonzero(diff)):
        if not any(0 <= y + dy < 8 and 0 <= x + dx < 8 and oa[y + dy, x + dx] and (o[y + dy, x + dx] == n[y, x]).all()
                   for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1))):
            return False
    return True

def reuse_tiles(img, keep=None):
    """keep: pixel mask a fold may not change."""
    pad = (-img.shape[0]) % 8
    g = np.concatenate([np.zeros((pad, img.shape[1], 4), np.uint8), img], 0)
    k = keep if keep is not None else np.zeros(img.shape[:2], bool)
    hold = np.concatenate([np.zeros((pad, k.shape[1]), bool), k], 0)
    seen = {}
    for ty in range(g.shape[0] // 8):
        for tx in range(g.shape[1] // 8):
            t = g[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].copy()
            if not t[..., 3].any():
                continue
            t[t[..., 3] == 0] = 0
            f = min(FLIPS, key=lambda f: flip(t, f).tobytes())
            c = flip(t, f)
            e = seen.setdefault(c.tobytes(), [c, [], np.zeros((8, 8), bool)])
            e[1].append((ty, tx, f))
            e[2] |= flip(hold[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8], f)
    kept = []
    for t, where, held in sorted(seen.values(), key=lambda v: -len(v[1])):
        a, best = t[..., 3] > 0, None
        for r in kept:
            for f in FLIPS:
                fr = flip(r, f)
                if ((fr[..., 3] > 0) != a).any():
                    continue
                diff = (fr[..., :3] != t[..., :3]).any(-1) & a
                d = int(diff.sum())
                if d <= REUSE and (best is None or d < best[0]) and not (diff & held).any() and edge_shift(t, fr, diff):
                    best = (d, fr)
        if best is None:
            kept.append(t)
            continue
        for ty, tx, f in where:
            g[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8] = flip(best[1], f)
    return g[pad:]

def buildings(phg):
    """The house and the Gym, finished."""
    sys.path.insert(0, str(HERE))
    import hgss_camera as C
    _, _, models, _, _ = C.R.load(phg)
    out = {}
    for name, (parts, width, mirror) in RENDERS.items():
        rgba, _ = C.view(models, parts, width)
        if name in LIFT:
            rgba = lift(C, models, parts, width, rgba, *LIFT[name])
        pal = GYM_PALETTE if name == 'gym' else sprite_palette(rgba)
        img = finish(rgba, pal, mirror)
        keep = None
        if name in SEAMS:
            mask = seam_mask(C, models, parts, width, rgba.shape[0], *SEAMS[name])
            img, keep = draw_seams(img, mask, C06_LINE if SEAMS[name][3] == 'cols' else None), mask[0]
        out[name] = reuse_tiles(img, keep)
    return out

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
    lower left, lit from the upper left in four bands of grey, a few etched cracks;
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

def build(phg):
    out = buildings(phg)
    out.update(gate_post=gate_post(), standing_stone=standing_stone())
    SPRITES.mkdir(parents=True, exist_ok=True)
    for name, img in out.items():
        Image.fromarray(img, 'RGBA').save(SPRITES / f'{name}.png')
    sheet(out)
    return out

def load(name):
    return np.array(Image.open(SPRITES / f'{name}.png').convert('RGBA'))

def sheet(parts):
    parts = list(parts.values())
    w = sum(p.shape[1] * 4 + 16 for p in parts); h = max(p.shape[0] for p in parts) * 4 + 16
    out = Image.new('RGBA', (w, h), (226, 200, 140, 255))
    x = 8
    for p in parts:
        out.alpha_composite(Image.fromarray(p, 'RGBA').resize((p.shape[1] * 4, p.shape[0] * 4), Image.Resampling.NEAREST), (x, 8))
        x += p.shape[1] * 4 + 16
    out.save(OUT / 'sprites.png')

if __name__ == '__main__':
    build(Path(sys.argv[1]).resolve())
