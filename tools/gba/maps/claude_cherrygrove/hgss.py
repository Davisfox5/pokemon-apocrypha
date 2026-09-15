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
    """Skylight house (the two western homes). 80x80: door in cell column 1, rows 3-4."""
    win = cutout(520, 116, 96, 80, erase=[(75, 36, 21, 44), (0, 74, 96, 6)])   # planter, ground shadow
    s = blank(80, 80); paste(s, win[:, 10:90], 0, 6)   # wall base lands on y=80
    return shift_rect(s, 18, 56, 18, 24, -3)           # door 28..46 in window -> 15..33 in sprite

def house_b():
    """Gable house (Gold's). 80x80: door in cell column 2."""
    win = cutout(680, 132, 96, 96, erase=[(0, 54, 31, 42), (0, 80, 96, 16), (88, 40, 8, 56), (0, 0, 26, 56)])   # mailbox, shadow, rose sliver, daisies
    s = blank(80, 80); paste(s, win[0:80, 13:93], 0, 0)
    return shift_rect(s, 27, 56, 18, 24, 4)

def center():
    """Pokemon Center. 96x96: door in cell column 2, rows 4-5."""
    win = cutout(776, 4, 96, 96, erase=[(0, 60, 12, 36), (92, 60, 4, 36), (0, 92, 96, 4)])
    s = blank(96, 96); paste(s, win[:, 9:105] if win.shape[1] >= 105 else np.pad(win, ((0, 0), (0, 9), (0, 0)))[:, 9:105], 0, 4)
    return s

def mart():
    """Poke Mart body without its sign. 80x64: door in cell column 1, rows 2-3."""
    win = cutout(648, 4, 112, 96, erase=[(78, 0, 34, 96), (0, 80, 112, 16)])
    win[18:50, 72:78] = win[18:50, 12:18][:, ::-1]      # the sign board overlapped the roof corner; the roof is symmetric
    s = blank(80, 64); paste(s, win[16:80, 10:90], 0, 0)
    return s

def mart_sign():
    """The Mart's flag sign on its pole, 32x64, drawn over the Mart's right edge."""
    a = px(648 + 72, 4 + 26, 32, 64)
    keep = np.zeros(a.shape[:2], bool); keep[0:32, :] = True; keep[32:60, 14:20] = True
    bgm = _near(a, GROUND_COLORS + TREE_COLORS + SHADOW_COLORS + [(56, 72, 152), (40, 48, 120), (24, 96, 216)], 14)
    a[..., 3] = (keep & ~bgm) * 255
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
    """One HGSS Johto tree, 32x48: the tree01 texture at its rendered size, in the render's tones, over its shadow."""
    import sys; sys.path.insert(0, str(ROOT / 'tools/hoennconv'))
    import narc; from nsbtx import Tex0
    t = Tex0(narc.load(ROOT / 'disasm/pokeheartgold/files/a/0/4/4')[2]); orig = t.pal_for
    t.pal_for = lambda e: next(p for p in t.palettes if p.name == 'tree01') if e.name == 'tree01gs' else orig(e)
    e = next(e for e in t.textures if e.name == 'tree01gs'); tex = np.asarray(t.render(e).convert('RGBA')).astype(np.int16)
    ys, xs = np.nonzero(tex[..., 3]); tex = tex[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    im = Image.fromarray(tex.astype(np.uint8)).resize((32, 42), Image.NEAREST); a = np.asarray(im).astype(np.int16)
    # colour map: texture tones -> rendered tones by luminance rank
    src = sorted({tuple(c[:3]) for c in a[a[..., 3] > 0]}, key=lambda c: 0.3 * c[0] + 0.6 * c[1] + 0.1 * c[2])
    dst = sorted(TREE_COLORS, key=lambda c: 0.3 * c[0] + 0.6 * c[1] + 0.1 * c[2])
    out = blank(32, 48)
    for i, c in enumerate(src):
        j = round(i * (len(dst) - 1) / max(len(src) - 1, 1)); m = (a[..., :3] == c).all(-1) & (a[..., 3] > 0)
        out[0:42, :, :3][m] = dst[j]; out[0:42, :, 3][m] = 255
    # ground shadow ellipse under the trunk
    for y in range(40, 48):
        for x in range(32):
            if ((x - 15.5) / 12.0) ** 2 + ((y - 43.5) / 3.5) ** 2 <= 1 and out[y, x, 3] == 0: out[y, x] = (*TREE_SHADOW, 255)
    return out

def _trim_shadow(a):
    return a

def bush():
    """Rose hedge cell (16x32) beside the eastern house."""
    a = px(916, 220, 16, 32); bgm = _near(a, GROUND_COLORS + SHADOW_COLORS, 12); a[..., 3] = (~bgm) * 255
    return a

def tulips(row):
    """One 16x16 flower-bed cell; the render alternates two tulip colourways by row."""
    return px(880, 116 + 16 * (row % 2), 16, 16)

def daisies():
    """Scattered daisies and one orange bloom on grass, 32x16 ground overlay."""
    a = px(564, 244, 32, 16); bgm = _near(a, [GRASS, GRASS_SPECK, GRASS_SHADE, GRASS_SHADE2], 8); a[..., 3] = (~bgm) * 255
    return a

def fence_h():
    a = px(880, 146, 16, 16); bgm = _near(a, GROUND_COLORS + SHADOW_COLORS, 10); a[..., 3] = (~bgm) * 255
    return a

def fence_v():
    a = px(862, 116, 16, 16); bgm = _near(a, GROUND_COLORS + SHADOW_COLORS, 10); a[..., 3] = (~bgm) * 255; a[:, 11:, 3] = 0
    return a

def fence_corner():
    a = px(864, 146, 16, 16); bgm = _near(a, GROUND_COLORS + SHADOW_COLORS, 10); a[..., 3] = (~bgm) * 255
    return a

# ------------------------------------------------------------------ terrain

def sea():
    """32x32 sea block (the texture repeats every 32 px)."""
    return cell(13, 10, 2, 2)

def cliff():
    """32x64 cliff band: crest, upper course, lower course, foot with lapping water (repeats every 32 px)."""
    return px(OX + 13 * 16, 44, 32, 64)

def cliff_sand():
    """32x64 cliff band whose foot stands on the beach instead of the sea."""
    return px(OX + 24 * 16, 44, 32, 64)

def dominant(rgba, rect, n=1):
    """The n most common opaque colours inside rect=(x, y, w, h) of a sprite."""
    x, y, w, h = rect; sub = rgba[y:y + h, x:x + w]; m = sub[..., 3] > 0
    if not m.any(): return []
    u, c = np.unique(sub[m][:, :3], axis=0, return_counts=True)
    return [tuple(int(v) for v in u[i]) for i in np.argsort(-c)[:n]]

def sea_rock():
    a = cutout(OX + 9 * 16 - 4, OY + 8 * 16 - 8, 40, 40, keep_colors_tol=16)
    s = blank(32, 32); paste(s, a[4:36, 4:36], 0, 0)
    return s

def sea_rock_small():
    a = cutout(OX + 6 * 16 - 2, OY + 8 * 16 + 2, 20, 20, keep_colors_tol=16)
    s = blank(16, 16); paste(s, a[2:18, 2:18], 0, 0)
    return s

def rock():
    a = cutout(190, 226, 48, 48, keep_colors_tol=12, bg=SEA_COLORS + [SAND, SAND2, SAND3, (216, 216, 176), (208, 208, 168), (200, 192, 144), (200, 232, 224), (152, 224, 224), (104, 192, 224), (72, 160, 224)])
    return centered(a, 32, 32)

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
