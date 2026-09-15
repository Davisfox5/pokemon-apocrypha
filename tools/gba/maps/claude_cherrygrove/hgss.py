"""HGSS-faithful scenery: cut from the 1:1 top-down HGSS Cherrygrove render.

The reference (`gba/art/johto-v1/references/cherrygrove-hgss.png`) is a native-scale
render of the DS town: one 16 px cell per movement tile, so every scenery piece can be
lifted at exact pixel size. Buildings are 3D models in HGSS and do not sit on the
16 px grid, so each one is cropped, cleaned of its neighbours and ground shadow, and
its door is nudged a few pixels so it lands in one movement cell. Ground colours are
sampled from the render (the DS renderer darkens the raw textures), and tileable
ground/edge tiles are synthesised from those samples so the look stays seamless.

Everything here returns RGBA numpy arrays; `banks.py` reduces them to palette banks.
Original designs and art: Game Freak / Nintendo / Creatures (read-only derivation).
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
REF = ROOT / 'gba/art/johto-v1/references/cherrygrove-hgss.png'
OX, OY = 8, 4   # pixel origin of the 16 px cell grid inside the render

_ref = None
def ref():
    global _ref
    if _ref is None: _ref = np.asarray(Image.open(REF).convert('RGB')).astype(np.int16)
    return _ref

def px(x, y, w, h):
    """RGBA crop in render pixel coordinates."""
    a = ref()[y:y + h, x:x + w]
    return np.dstack([a, np.full(a.shape[:2], 255, dtype=np.int16)]).astype(np.uint8)

def cell(cx, cy, w=1, h=1):
    return px(OX + cx * 16, OY + cy * 16, w * 16, h * 16)

# Reference colours (as rendered).
GRASS = (104, 208, 152); GRASS_SPECK = (104, 200, 152); GRASS_SHADE = (88, 176, 136); GRASS_SHADE2 = (96, 192, 144)
PATH = (224, 200, 128); PATH_SPECK = (216, 184, 128); PATH_SPECK2 = (184, 168, 128)
SAND = (240, 240, 200); SAND2 = (232, 232, 192); SAND3 = (224, 224, 184)
EDGE_DARK = (128, 136, 120)   # the dark rim where sand meets grass shadow

def _near(a, colors, tol):
    flat = a[..., :3].reshape(-1, 3).astype(np.int32); cs = np.array(colors, dtype=np.int32)
    d = ((flat[:, None, :] - cs[None, :, :]) ** 2).sum(-1).min(1)
    return (d <= tol * tol).reshape(a.shape[:2])

GROUND_COLORS = [GRASS, GRASS_SPECK, GRASS_SHADE, GRASS_SHADE2, PATH, PATH_SPECK, PATH_SPECK2, SAND, SAND2, SAND3, EDGE_DARK,
                 (104, 152, 120), (152, 144, 112), (168, 216, 152), (208, 208, 168), (216, 216, 176), (192, 152, 104), (208, 168, 112), (208, 184, 112), (216, 168, 128)]
TREE_COLORS = [(64, 56, 40), (64, 64, 40), (72, 72, 48), (80, 88, 40), (88, 104, 32), (88, 112, 32), (96, 120, 32), (112, 144, 32), (120, 152, 32), (136, 168, 40)]
SEA_COLORS = [(24, 96, 216), (24, 104, 224), (32, 112, 224), (32, 120, 224), (40, 128, 224), (40, 136, 224), (48, 152, 224), (56, 176, 224), (64, 192, 224)]
TREE_SHADOW = (64, 136, 104)
SHADOW_COLORS = [(72, 152, 112), (64, 144, 104), (80, 160, 120), (56, 136, 96), (72, 144, 112), (80, 152, 112)]   # building drop shadow on grass

def _components(m):
    lab = np.zeros(m.shape, np.int32); n = 0; sizes = {}
    from collections import deque
    for sy, sx in zip(*np.nonzero(m)):
        if lab[sy, sx]: continue
        n += 1; q = deque([(sy, sx)]); lab[sy, sx] = n; c = 0
        while q:
            y, x = q.popleft(); c += 1
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < m.shape[0] and 0 <= xx < m.shape[1] and m[yy, xx] and not lab[yy, xx]: lab[yy, xx] = n; q.append((yy, xx))
        sizes[n] = c
    return lab, sizes

def _fill_holes(keep):
    from collections import deque
    outside = np.zeros(keep.shape, bool); q = deque()
    h, w = keep.shape
    for y in range(h):
        for x in (0, w - 1):
            if not keep[y, x] and not outside[y, x]: outside[y, x] = True; q.append((y, x))
    for x in range(w):
        for y in (0, h - 1):
            if not keep[y, x] and not outside[y, x]: outside[y, x] = True; q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w and not keep[yy, xx] and not outside[yy, xx]: outside[yy, xx] = True; q.append((yy, xx))
    return ~outside

def cutout(x, y, w, h, erase=(), keep_colors_tol=14, extra_bg=(), bg=None):
    """Crop a window, drop ground/tree/sea/shadow colours, keep the largest solid, fill its holes."""
    a = px(x, y, w, h)
    bgm = _near(a, (GROUND_COLORS + TREE_COLORS + SEA_COLORS + SHADOW_COLORS if bg is None else list(bg)) + list(extra_bg), keep_colors_tol)
    m = ~bgm
    for (ex, ey, ew, eh) in erase: m[ey:ey + eh, ex:ex + ew] = False
    lab, sizes = _components(m)
    best = max(sizes, key=sizes.get)
    keep = _fill_holes(lab == best)
    a[..., 3] = keep * 255
    return a

def centered(a, w, h):
    """Place the opaque bbox of `a` centred in a w x h sprite (bottom-aligned when taller)."""
    ys, xs = np.nonzero(a[..., 3]); sub = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    s = blank(w, h); paste(s, sub, (w - sub.shape[1]) // 2, h - sub.shape[0])
    return s

def blank(w, h):
    return np.zeros((h, w, 4), dtype=np.uint8)

def paste(dst, src, x, y):
    h, w = src.shape[:2]
    x0, y0 = max(x, 0), max(y, 0); x1, y1 = min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
    if x1 <= x0 or y1 <= y0: return dst
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]; m = s[..., 3] > 0
    dst[y0:y1, x0:x1][m] = s[m]
    return dst

def narrow(a, x0, y0, w, h, target):
    """Shrink a rectangle (a door with its frame) to `target` px wide by dropping interior columns; the
    outline columns at both edges survive. The freed columns on the right are refilled from the wall beyond."""
    block = a[y0:y0 + h, x0:x0 + w].copy()
    inner = block[:, 1:w - 1]; keep = target - 2
    cols = np.linspace(0, inner.shape[1] - 1, keep).round().astype(int)
    out = np.concatenate([block[:, :1], inner[:, cols], block[:, w - 1:w]], axis=1)
    fill = a[y0:y0 + h, x0 + w:x0 + w + 1]
    a[y0:y0 + h, x0:x0 + w] = np.repeat(fill, w, axis=1)
    a[y0:y0 + h, x0:x0 + target] = out
    return a

def shift_rect(a, x0, y0, w, h, dx):
    """Slide a rectangle horizontally by dx; the vacated strip is refilled from the neighbouring wall columns."""
    block = a[y0:y0 + h, x0:x0 + w].copy()
    if dx < 0:
        fill = a[y0:y0 + h, x0 + w:x0 + w + 1]
        a[y0:y0 + h, x0 + w + dx:x0 + w] = np.repeat(fill, -dx, axis=1)
    else:
        fill = a[y0:y0 + h, x0 - 1:x0]
        a[y0:y0 + h, x0:x0 + dx] = np.repeat(fill, dx, axis=1)
    a[y0:y0 + h, x0 + dx:x0 + dx + w] = block
    return a

# ------------------------------------------------------------------ buildings
# Window origins in render pixels; crops measured on the masked cutouts.

def house_a():
    """Skylight house (the two western homes). 80x80: 16 px door in cell column 1, rows 3-4."""
    win = cutout(520, 116, 96, 80, erase=[(75, 36, 21, 44), (0, 74, 96, 6)])   # planter, ground shadow
    s = blank(80, 80); paste(s, win[:, 10:90], 0, 6)
    s[46:80, 0:6] = 0                                   # the model's shadowed side wall, which read as a stray block
    narrow(s, 18, 56, 18, 24, 16)                        # door 18 -> 16 px, now at sprite x 18..34
    return shift_rect(s, 18, 56, 16, 24, -2)             # centre it in cell column 1 (x 16..32)

def house_b():
    """Gable house (Gold's). 96x80: the whole roof survives; 16 px door in cell column 2."""
    win = cutout(680, 132, 104, 96, erase=[(0, 54, 31, 42), (0, 80, 104, 16), (0, 0, 26, 56)])   # mailbox, shadow, daisies
    s = blank(96, 80); paste(s, win[0:80, 8:104], 0, 0)
    s[40:80, 83:96] = 0; s[0:56, 0:6] = 0              # the neighbour's rose sliver and a stray daisy
    narrow(s, 32, 56, 18, 24, 16)                        # door 40..58 in window -> 32..50 here -> 32..48
    return s

def center():
    """Pokemon Center. 96x96: 16 px door in cell column 2, rows 4-5."""
    win = cutout(776, 4, 96, 96, erase=[(0, 60, 12, 36), (92, 60, 4, 36), (0, 92, 96, 4)])
    s = blank(96, 96); paste(s, win[:, 9:105] if win.shape[1] >= 105 else np.pad(win, ((0, 0), (0, 9), (0, 0)))[:, 9:105], 0, 4)
    narrow(s, 31, 78, 18, 14, 16)                        # blue door 40..58 in window -> 31..49 here -> 31..47
    return shift_rect(s, 31, 78, 16, 14, 1)

def mart():
    """Poke Mart body without its sign. 80x64: 16 px door in cell column 1, rows 2-3."""
    win = cutout(648, 4, 112, 96, erase=[(78, 0, 34, 96), (0, 80, 112, 16)])
    win[18:50, 72:78] = win[18:50, 12:18][:, ::-1]      # the sign board overlapped the roof corner; the roof is symmetric
    s = blank(80, 64); paste(s, win[16:80, 10:90], 0, 0)
    narrow(s, 14, 46, 20, 18, 16)                        # sliding door 24..44 in window -> 14..34 here -> 14..30
    return shift_rect(s, 14, 46, 16, 18, 2)

def mart_sign():
    """The Mart's flag sign on its pole, 32x64: board and pole only."""
    a = px(648 + 72, 4 + 26, 32, 64)
    keep = np.zeros(a.shape[:2], bool); keep[0:32, :] = True; keep[32:58, 14:20] = True
    bgm = _near(a, GROUND_COLORS + TREE_COLORS + SHADOW_COLORS + [(56, 72, 152), (40, 48, 120), (24, 96, 216)], 14)
    a[..., 3] = (keep & ~bgm) * 255
    pole = a[32:58, 14:20]; greyish = (np.abs(pole[..., 0].astype(int) - pole[..., 1].astype(int)) < 24) & (np.abs(pole[..., 1].astype(int) - pole[..., 2].astype(int)) < 30)
    pole[..., 3] = np.where(greyish, pole[..., 3], 0)
    return a

def planter(side='right'):
    """Flower box hung on a house wall, 16x32."""
    a = cutout(520 + 76, 116 + 36, 20, 36, keep_colors_tol=14)
    s = blank(16, 32); paste(s, a[:, 0:16], 0, 0)
    return s[:, ::-1] if side == 'left' else s

def mailbox():
    a = cutout(680 + 14, 132 + 54, 18, 34)
    s = blank(16, 32); paste(s, a[:, 1:17], 0, 0)
    return s

def signpost():
    """Wooden signpost, 32x32 with the board centred on the left cell."""
    a = cutout(662, 130, 32, 32)
    return a

# ------------------------------------------------------------------ vegetation

def tree():
    """One HGSS Johto tree, 32x48: the tree01 texture at its rendered size, in the render's tones, over a trunk and shadow."""
    import sys; sys.path.insert(0, str(ROOT / 'tools/hoennconv'))
    import narc; from nsbtx import Tex0
    t = Tex0(narc.load(ROOT / 'disasm/pokeheartgold/files/a/0/4/4')[2]); orig = t.pal_for
    t.pal_for = lambda e: next(p for p in t.palettes if p.name == 'tree01') if e.name == 'tree01gs' else orig(e)
    e = next(e for e in t.textures if e.name == 'tree01gs'); tex = np.asarray(t.render(e).convert('RGBA')).astype(np.int16)
    ys, xs = np.nonzero(tex[..., 3]); tex = tex[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    im = Image.fromarray(tex.astype(np.uint8)).resize((32, 38), Image.NEAREST); a = np.asarray(im).astype(np.int16)
    src = sorted({tuple(c[:3]) for c in a[a[..., 3] > 0]}, key=lambda c: 0.3 * c[0] + 0.6 * c[1] + 0.1 * c[2])
    dst = sorted(TREE_COLORS, key=lambda c: 0.3 * c[0] + 0.6 * c[1] + 0.1 * c[2])
    out = blank(32, 48)
    # shadow, then trunk, then crown (the render shows a short trunk with a dark shadow ellipse)
    for y in range(38, 48):
        for x in range(32):
            if ((x - 15.5) / 13.0) ** 2 + ((y - 43.0) / 4.0) ** 2 <= 1: out[y, x] = (*TREE_SHADOW, 255)
    out[36:44, 12:20] = (136, 96, 72, 255); out[36:44, 12:14] = (104, 72, 56, 255); out[36:44, 18:20] = (104, 72, 56, 255); out[43, 12:20] = (88, 64, 48, 255)
    for i, c in enumerate(src):
        j = round(i * (len(dst) - 1) / max(len(src) - 1, 1)); m = (a[..., :3] == c).all(-1) & (a[..., 3] > 0)
        out[0:38, :, :3][m] = dst[j]; out[0:38, :, 3][m] = 255
    return out

def _trim_shadow(a):
    return a

def bush():
    """Rose hedge cell (16x32) beside the eastern house."""
    a = px(916, 220, 16, 32); bgm = _near(a, GROUND_COLORS + SHADOW_COLORS, 12); a[..., 3] = (~bgm) * 255
    return a

def tulips(row=0):
    """One flower-bed cell as a 16x24 sprite (the heads rise 8 px above the cell)."""
    return px(876, 108, 16, 24)

def daisies():
    """Scattered daisies and one orange bloom on grass, 32x16 ground overlay."""
    a = px(564, 244, 32, 16); bgm = _near(a, [GRASS, GRASS_SPECK, GRASS_SHADE, GRASS_SHADE2], 8); a[..., 3] = (~bgm) * 255
    return a

def fence_h():
    a = px(880, 146, 16, 16); bgm = _near(a, GROUND_COLORS + SHADOW_COLORS, 10); a[..., 3] = (~bgm) * 255
    return a

def fence_v():
    a = px(864, 116, 16, 16); bgm = _near(a, GROUND_COLORS + SHADOW_COLORS, 10); a[..., 3] = (~bgm) * 255; a[:, 11:, 3] = 0
    return a

def fence_corner():
    a = px(864, 146, 16, 16); bgm = _near(a, GROUND_COLORS + SHADOW_COLORS, 10); a[..., 3] = (~bgm) * 255
    return a

# ------------------------------------------------------------------ terrain

def sea():
    """32x32 sea block (the texture repeats every 32 px)."""
    return cell(13, 10, 2, 2)

def cliff():
    """32x64 cliff band: crest lip, upper course, lower course, foot with lapping water (repeats every 32 px).
    The grass and tree shadows above the lip are cleared so the map's own ground and trees show."""
    a = px(OX + 13 * 16, 44, 32, 64); return _clear_crest(a)

def _clear_crest(a):
    """Keep only rock and lip pixels in the crest row (warm tones); grass and tree shadows become transparent."""
    top = a[0:16]; r, g, b = top[..., 0].astype(int), top[..., 1].astype(int), top[..., 2].astype(int)
    rocky = (r >= g) & (r > b); top[..., 3] = np.where(rocky, top[..., 3], 0); return a

def cliff_end():
    """80x104 corner where the HGSS cliff turns south and ends on the beach (placed 8 px above the crest row).
    Everything that is not rock is cleared: grass and tree tones, beach sand, the path and the roof beyond."""
    a = px(472, 36, 80, 104)
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    green = g > r + 8
    sand = (r > 222) & (g > 222) & (b > 165)
    path = _near(a, [PATH, PATH_SPECK, PATH_SPECK2, (208, 168, 112), (192, 152, 104), (208, 184, 112), (216, 168, 128), EDGE_DARK, (152, 144, 112), (104, 152, 120)], 10)
    roof = (r > 150) & (g < 130) & (b < 130) & (r - g > 60)
    a[..., 3] = np.where(green | sand | path | roof, 0, 255)
    a[60:, 60:, 3] = 0; a[88:, 44:, 3] = 0; a[0:8, 0:30, 3] = 0; a[0:10, 64:80, 3] = 0; a[56:, 0:16, 3] = 0
    a[..., 3] = _fill_holes(a[..., 3] > 0) * 255
    return a

def cliff_sand():
    """32x64 cliff band whose foot stands on the beach (a clean stretch without foot rocks)."""
    a = px(OX + 27 * 16, 44, 32, 64); return _clear_crest(a)

def dominant(rgba, rect, n=1):
    """The n most common opaque colours inside rect=(x, y, w, h) of a sprite."""
    x, y, w, h = rect; sub = rgba[y:y + h, x:x + w]; m = sub[..., 3] > 0
    if not m.any(): return []
    u, c = np.unique(sub[m][:, :3], axis=0, return_counts=True)
    return [tuple(int(v) for v in u[i]) for i in np.argsort(-c)[:n]]

def sea_rock():
    a = px(72, 112, 36, 36); bgm = _near(a, SEA_COLORS + [(24, 104, 224), (32, 112, 224)], 20); a[..., 3] = (~bgm) * 255
    return centered(a, 32, 32)

def sea_rock_small():
    return blank(16, 16)

def rock():
    """Brown boulder, 32x48 (it is taller than two cells); footprint is the lower two cells."""
    a = cutout(190, 224, 48, 48, keep_colors_tol=12, bg=SEA_COLORS + [SAND, SAND2, SAND3, (216, 216, 176), (208, 208, 168), (200, 192, 144), (200, 232, 224), (152, 224, 224), (104, 192, 224), (72, 160, 224)])
    return centered(a, 32, 48)

def grass_tile():
    s = blank(16, 16); s[..., :3] = GRASS; s[..., 3] = 255
    for (x, y) in ((3, 2), (11, 6), (6, 12), (14, 13)): s[y, x, :3] = GRASS_SPECK
    return s

def path_tile():
    s = blank(16, 16); s[..., :3] = PATH; s[..., 3] = 255
    for (x, y, c) in ((2, 3, PATH_SPECK), (9, 1, PATH_SPECK2), (13, 8, PATH_SPECK), (5, 12, PATH_SPECK2), (11, 14, PATH_SPECK)): s[y, x, :3] = c
    return s

def sand_tile():
    """Beach sand with the soft diagonal ripple of the render."""
    return cell(25, 9)

# ------------------------------------------------------------------ waterfront (HGSS bridge textures + original boat)

def _texture(name, alias=None):
    import sys; sys.path.insert(0, str(ROOT / 'tools/hoennconv'))
    import narc; from nsbtx import Tex0
    t = Tex0(narc.load(ROOT / 'disasm/pokeheartgold/files/a/0/4/4')[2]); orig = t.pal_for
    if alias: t.pal_for = lambda e: next(p for p in t.palettes if p.name == alias) if e.name == name else orig(e)
    e = next(e for e in t.textures if e.name == name); return np.asarray(t.render(e).convert('RGBA')).astype(np.int16)

def _tone(a, k=0.82):
    """The DS renderer draws textures darker than their raw pixels; match the render."""
    out = a.copy(); out[..., :3] = np.clip(a[..., :3] * k, 0, 255); return out.astype(np.uint8)

def pier(cells):
    """A plank pier `cells` wide and two cells tall from the HGSS bridge planks: a dark rim, a lit top edge,
    a water shadow under the seaward side and round log posts along it."""
    planks = _tone(_texture('bridge_c'))
    w = cells * 16; s = blank(w, 32)
    for x in range(0, w, 32): paste(s, planks[:, :min(32, w - x)], x, 0)
    rim = (72, 48, 32, 255)
    s[0, :] = rim; s[29, :] = rim; s[:, 0] = rim; s[:30, w - 1] = rim
    s[1, :, :3] = (176, 136, 96); s[28, :, :3] = (112, 76, 48)
    s[30, 1:w - 1] = (40, 64, 112, 255); s[31, 2:w - 2] = (24, 56, 120, 255)   # shadow on the water
    def post(x, y):
        s[y:y + 12, x:x + 6] = (120, 80, 48, 255); s[y:y + 12, x + 1:x + 2] = (168, 120, 80, 255); s[y:y + 12, x + 5:x + 6] = (72, 48, 32, 255)
        s[y, x:x + 6] = (184, 136, 88, 255); s[y + 1, x + 1:x + 5] = (200, 152, 104, 255); s[y + 11, x:x + 6] = (56, 40, 24, 255)
    for x in range(2, w - 6, 16): post(x, 20)
    post(1, 2); post(w - 7, 2)
    return s

BOAT_ROWS = [
    '.......OOOOOOOOOOOOOOOOOO.......',
    '....OOOwwwwwwwwwwwwwwwwwwOOO....',
    '..OOwwwddddddddddddddddddwwwOO..',
    '.OwwwddOOOOOOOOOOOOOOOOOOddwwwO.',
    'OwwddOllllllllOppOllllllllOddwwO',
    'OwwddOllllllllOppOllllllllOddwwO',
    'OwwddOlllOOOOOOppOOOOOOlllOddwwO',
    'OwwddOllllllllOppOllllllllOddwwO',
    '.OwwwddOOOOOOOOOOOOOOOOOOddwwwO.',
    '..OOwwwddddddddddddddddddwwwOO..',
    '....OOOwwwwwwwwwwwwwwwwwwOOO....',
    '.......OOOOOOOOOOOOOOOOOO.......',
]
BOAT_KEY = dict(O=(64, 40, 28), w=(232, 232, 216), d=(200, 144, 96), l=(152, 104, 64), p=(120, 80, 48))

def boat():
    """A wooden rowboat seen from above, 32x16 (two cells wide, one tall): pale hull, plank floor, a thwart."""
    s = blank(32, 16)
    for dy, row in enumerate(BOAT_ROWS):
        for dx, ch in enumerate(row):
            if ch != '.': s[2 + dy, dx] = (*BOAT_KEY[ch], 255)
    s[14, 2:30] = (24, 56, 120, 255)   # water shadow
    return s
