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
    side = s[46:80, 0:8]; roof = (side[..., 0].astype(int) > 150) & (side[..., 0].astype(int) > side[..., 1].astype(int) + 40)
    side[..., 3] = np.where(roof, side[..., 3], 0)      # the model's shadowed side wall read as a stray block; the roof's corner stays
    # (the wall now starts 8 px into the footprint, on the tile grid, so a letterbox can stand against it)
    narrow(s, 18, 56, 18, 24, 16)                        # door 18 -> 16 px, now at sprite x 18..34
    return shift_rect(s, 18, 56, 16, 24, -2)             # centre it in cell column 1 (x 16..32)

def house_b():
    """Gable house (Gold's). 96x80: the whole roof survives; 16 px door in cell column 2."""
    win = cutout(680, 132, 104, 96, erase=[(0, 54, 31, 42), (0, 80, 104, 16), (0, 0, 26, 56)])   # mailbox, shadow, daisies
    s = blank(96, 80); paste(s, win[0:80, 8:104], 0, 0)
    s[40:80, 83:96] = 0; s[0:56, 0:6] = 0              # the neighbour's rose sliver and a stray daisy
    s[56:80, 0:24] = 0                                  # the wall starts 24 px in, on the tile grid, for the letterbox
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
    """The Mart's flag sign on its pole, 32x64: board and pole only. The board's top edge slopes from (0,5) to
    (28,1); the Mart's roof corner above that line and its wall beside the pole are cleared."""
    a = px(648 + 72, 4 + 26, 32, 64)
    keep = np.zeros(a.shape[:2], bool); keep[0:27, :] = True; keep[27:58, 10:18] = True
    bgm = _near(a, GROUND_COLORS + TREE_COLORS + SHADOW_COLORS + [(56, 72, 152), (40, 48, 120), (24, 96, 216)], 14)
    ys, xs = np.mgrid[0:64, 0:32]
    keep &= ~((xs < 12) & (ys < 5.5 - xs * 4 / 28))
    a[..., 3] = (keep & ~bgm) * 255
    pole = a[27:58, 10:18]; greyish = (np.abs(pole[..., 0].astype(int) - pole[..., 1].astype(int)) < 24) & (np.abs(pole[..., 1].astype(int) - pole[..., 2].astype(int)) < 30)
    pole[..., 3] = np.where(greyish, pole[..., 3], 0)
    lab, sizes = _components(a[..., 3] > 0); best = max(sizes, key=sizes.get); a[..., 3] = (lab == best) * 255
    return a

def planter(side='right'):
    """Flower box hung on a house wall, 16x32."""
    a = cutout(520 + 76, 116 + 36, 20, 36, keep_colors_tol=14)
    s = blank(16, 32); paste(s, a[:, 0:16], 0, 0)
    return s[:, ::-1] if side == 'left' else s

def mailbox():
    """The red letterbox on its post, 16x32, right-aligned so it can stand against a house wall.
    Cut tight from the render (box 12x19, post 4x5) so none of the wall behind it comes along."""
    a = px(695, 191, 12, 24)
    keep = np.zeros(a.shape[:2], bool); keep[0:19, :] = True; keep[19:24, 4:8] = True
    a[..., 3] = (keep & ~_near(a, GROUND_COLORS + SHADOW_COLORS + [(64, 136, 104)], 12)) * 255
    s = blank(16, 32); paste(s, a, 4, 8)
    return s

def signpost():
    """Wooden signpost, 32x32 with the board centred on the left cell."""
    a = cutout(662, 130, 32, 32)
    return a

# ------------------------------------------------------------------ vegetation

TREE_TIP = (0, 0)          # sprite offset of the crown's tip: a tree is placed at (cx*16, cy*16) so the tip sits on the cell's top
TREE_PITCH = (32, 24)      # the HGSS lattice: straight columns two cells apart, rows 24 px apart (crowns overlap the row behind)

def tree():
    """One HGSS Johto tree as rendered, 40x40: the bottom tree of the column beside the Mart, whose crown,
    trunk and shadow are all unobscured. The crown is 38 px wide and 27 tall (tip on row 0); trunk and shadow
    reach row 35. Kept on the 8 px tile grid so a tree costs 25 tiles rather than 36."""
    a = px(624, 58, 40, 40)
    bgm = _near(a, GROUND_COLORS + SHADOW_COLORS, 12) | (a[..., 2].astype(int) > a[..., 0].astype(int) + 40)   # grass, and the Mart's blue roof corner
    m = ~bgm; lab, sizes = _components(m); best = max(sizes, key=sizes.get)
    a[..., 3] = _fill_holes(lab == best) * 255
    return a

def _trim_shadow(a):
    return a

def bush():
    """Rose hedge cell (16x32) beside the eastern house."""
    a = px(916, 220, 16, 32); bgm = _near(a, GROUND_COLORS + SHADOW_COLORS, 12); a[..., 3] = (~bgm) * 255
    return a

def tulips():
    """One flower-bed cell, 16x16, cut on the render's cell grid: a pink tulip over an orange one with the leaves
    that join it to its neighbours. The bed repeats this cell exactly, so any bed size tiles without seams."""
    return cell(55, 7)

def tulips_top():
    """The 2 px of tulip heads that rise above a bed's back row, as a 16x16 overlay on the cell behind."""
    a = cell(55, 6); a[..., 3] = (~_near(a, GROUND_COLORS + SHADOW_COLORS, 12)) * 255; a[0:12, :, 3] = 0
    return a

def daisies():
    """A patch of white daisies and one orange bloom on grass, 48x32 ground overlay (whole flowers this time)."""
    a = px(560, 238, 48, 32); bgm = _near(a, GROUND_COLORS + SHADOW_COLORS + TREE_COLORS, 10); a[..., 3] = (~bgm) * 255
    lab, sizes = _components(a[..., 3] > 0)
    for k, n in sizes.items():
        if n < 6: a[..., 3][lab == k] = 0
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

def _rocky(a):
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    return (r > g + 12) & (r > b + 20)

def _rock_columns(a, top=0, min_count=6, tail=3, gap=6):
    """Opaque along every column's run of rock pixels (small crevices and highlights bridged, gaps wider than
    `gap` px end a run, runs shorter than `min_count` dropped), plus up to `tail` rows of the foam or shadow
    line the render draws under the rock. Rows above `top` never count."""
    rocky = _rocky(a); rocky[:top] = False
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int); lum = 0.3 * r + 0.6 * g + 0.1 * b
    foam = (b > r + 10) & (lum > 170); shade = (g > r + 20) & (g > b + 10) & (lum < 150)
    keep = np.zeros(a.shape[:2], bool)
    for x in range(a.shape[1]):
        ys = np.nonzero(rocky[:, x])[0]
        if len(ys) == 0: continue
        runs = [[ys[0], ys[0]]]
        for y in ys[1:]:
            if y - runs[-1][1] <= gap: runs[-1][1] = y
            else: runs.append([y, y])
        for y0, y1 in runs:
            if y1 - y0 + 1 < min_count: continue
            keep[y0:y1 + 1, x] = True
            for y in range(y1 + 1, min(y1 + 1 + tail, a.shape[0])):
                if foam[y, x] or shade[y, x]: keep[y, x] = True
                else: break
    a[..., 3] = keep * 255
    return a

def _patch_green(a):
    """Green pixels inside the rock (a tree crown drawn over the face) take the colour four columns to the right."""
    r, g = a[..., 0].astype(int), a[..., 1].astype(int); m = (a[..., 3] > 0) & (g > r + 8)
    for y, x in zip(*np.nonzero(m)):
        src = min(x + 4, a.shape[1] - 1); a[y, x, :3] = a[y, src, :3]
    return a

def cliff():
    """32x64 cliff band over the sea: lip, two courses and the foot with its foam line (repeats every 32 px).
    Rows above the lip (grass, tree shadows and trunks in the render) are cleared; the map paints its own ground."""
    return _rock_columns(px(OX + 13 * 16, 44, 32, 64), top=5)

def cliff_sand():
    """The same band where its foot stands on the beach: the sea band's body over the beach stretch's plain foot,
    so the two share every tile above the foot row."""
    a = cliff(); foot = _rock_columns(px(OX + 27 * 16, 44, 32, 64), top=5)
    a[48:] = foot[48:]; return a

def cliff_end():
    """64x104 corner where the HGSS cliff turns north: the band's east end and the vertical face that runs from the
    corner to the top of the render (and so off the top of the map). Cut from y = 0, placed 44 px above the crest row."""
    a = px(472, 0, 64, 104)
    a[0:47, 0:31] = 0                                    # trees on the plateau, left of the face
    a = _rock_columns(a, top=0, min_count=8)
    return _patch_green(a)

def dominant(rgba, rect, n=1):
    """The n most common opaque colours inside rect=(x, y, w, h) of a sprite."""
    x, y, w, h = rect; sub = rgba[y:y + h, x:x + w]; m = sub[..., 3] > 0
    if not m.any(): return []
    u, c = np.unique(sub[m][:, :3], axis=0, return_counts=True)
    return [tuple(int(v) for v in u[i]) for i in np.argsort(-c)[:n]]

def sea_rock():
    """One grey boulder in the bay with its pale wet rim, 32x32 (the neighbouring rock's corner is dropped)."""
    a = px(72, 112, 36, 36); bgm = _near(a, SEA_COLORS + [(24, 104, 224), (32, 112, 224)], 20)
    lab, sizes = _components(~bgm); best = max(sizes, key=sizes.get); a[..., 3] = _fill_holes(lab == best) * 255
    return centered(a, 32, 32)

def sea_rock_small():
    return blank(16, 16)

def rock():
    """Brown boulder, 32x48 (it is taller than two cells); footprint is the lower two cells."""
    a = cutout(190, 224, 48, 48, keep_colors_tol=12, bg=SEA_COLORS + [SAND, SAND2, SAND3, (216, 216, 176), (208, 208, 168), (200, 192, 144), (200, 232, 224), (152, 224, 224), (104, 192, 224), (72, 160, 224)])
    return centered(a, 32, 48)

def grass_texture():
    """32x32 of open lawn from the render (cells 29-30, rows 7-8: nothing but grass and its speckle clusters).
    32 px so shoreline and path rims, which wobble on a 32 px wave, repeat with it."""
    return cell(29, 7, 2, 2)

def path_texture():
    """32x32 of the sand path from the render (cells 35-36, rows 3-4), which repeats every 32 px."""
    return cell(35, 3, 2, 2)

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

def pier(cells, rail_px=None, piles_px=None):
    """A clean boardwalk pier, `cells` wide, as a (cells*16) x 48 sprite placed 8 px above its two deck rows:
    rows 0-7 a rope rail on short posts (over the sea cell behind), rows 8-37 the plank deck with a dark rim and
    a lit top edge, rows 38-47 the piles under the seaward edge and the deck's shadow on the water. Rail, piles
    and shadow stop at rail_px / piles_px, where the deck reaches the beach."""
    w = cells * 16; s = blank(w, 48); rail_px = w if rail_px is None else rail_px; piles_px = w if piles_px is None else piles_px
    OUT, LIT, SEAM = (56, 36, 24, 255), (216, 176, 120, 255), (120, 84, 52, 255)
    PLANK = [((184, 140, 92), (200, 156, 104), (168, 124, 80)), ((176, 132, 84), (192, 148, 96), (160, 116, 72))]
    d0, d1 = 8, 38
    s[d0:d1, :] = OUT
    for i, y in enumerate(range(d0 + 2, d1 - 2, 4)):
        base, hi, lo = PLANK[i % 2]
        s[y, :] = (*hi, 255); s[y + 1:y + 3, :] = (*base, 255); s[y + 3, :] = (*lo, 255)
        for x in range((i * 24 + 10) % 32, w, 32):        # staggered board ends
            if 2 <= x < w - 2: s[y:y + 4, x] = SEAM; s[y:y + 4, x + 1] = (*hi, 255)
    s[d0 + 1, :] = LIT; s[d1 - 2, :] = SEAM
    s[d0:d1, 0] = OUT; s[d0:d1, w - 1] = OUT; s[d0 + 1:d1 - 1, 1] = LIT
    # shadow on the water and piles under the seaward edge
    s[d1, 1:w - 1] = (24, 56, 120, 255); s[d1 + 1, 2:w - 2] = (32, 72, 144, 255)
    def pile(x, y0, y1, w_=6):
        s[y0:y1, x:x + w_] = (104, 68, 40, 255); s[y0:y1, x + 1] = (152, 108, 68, 255); s[y0:y1, x + w_ - 1] = (56, 36, 24, 255)
        s[y1 - 1, x:x + w_] = (40, 24, 16, 255); s[y1, x + 1:x + w_ - 1] = (24, 56, 120, 255)
    for x in [x for x in range(3, w - 8, 32) if x + 6 <= piles_px] + [piles_px - 9]: pile(x, d1 - 4, 47)
    s[d1:d1 + 2, piles_px:] = 0
    # rope rail along the north edge
    for x in [x for x in range(2, w - 4, 32) if x + 4 <= rail_px] + [rail_px - 6]:
        s[0:d0 + 2, x:x + 4] = (120, 84, 52, 255); s[0:d0 + 2, x + 1] = (176, 132, 84, 255); s[0:d0 + 2, x + 3] = OUT; s[0, x:x + 4] = OUT
    for x in range(0, rail_px):
        if s[3, x, 3] == 0: s[3 + ((x // 4) % 2), x] = (216, 192, 144, 255)
    return s

def boat():
    """A modern motorboat from above, 48x32 (three cells by two), bow to the left: white hull with a blue stripe,
    grey deck, a windshield ahead of the cockpit, an outboard motor on the transom and its shadow on the water."""
    s = blank(48, 32); cy = 15
    OUT, WHITE, CREAM, STRIPE = (40, 44, 56), (240, 240, 236), (216, 216, 208), (40, 112, 208)
    DECK, DECK2, SEAT, SEATHI, GLASS, GLASSHI, MOTOR, MOTOR2 = (184, 188, 192), (160, 164, 172), (72, 80, 96), (112, 120, 136), (152, 208, 240), (216, 240, 248), (72, 76, 84), (112, 116, 124)
    def half(x):
        if x < 22: return 1 + (x - 4) * 0.42
        return 8.6 - max(0, x - 38) * 0.2
    for x in range(4, 44):
        h = half(x)
        for y in range(0, 32):
            d = h - abs(y - cy)
            if d < 0: continue
            if d < 1: c = OUT
            elif d < 3: c = WHITE if y <= cy else CREAM
            elif d < 4: c = STRIPE
            else: c = DECK if (x + y) % 2 else DECK2
            s[y, x] = (*c, 255)
    s[cy, 5:8] = (*OUT, 255)
    # cockpit and seats
    for y in range(cy - 4, cy + 5):
        for x in range(26, 41): s[y, x] = (*SEAT, 255)
    for x0 in (27, 33):
        s[cy - 3:cy - 1, x0:x0 + 4] = (*SEATHI, 255); s[cy + 2:cy + 4, x0:x0 + 4] = (*SEATHI, 255)
    s[cy - 4, 26:41] = (*OUT, 255); s[cy + 4, 26:41] = (*OUT, 255); s[cy - 4:cy + 5, 40] = (*OUT, 255)
    # windshield
    for y in range(cy - 5, cy + 6):
        s[y, 22] = (*OUT, 255); s[y, 23:26] = (*GLASS, 255)
    s[cy - 4:cy - 1, 23] = (*GLASSHI, 255); s[cy - 5, 22:26] = (*OUT, 255); s[cy + 5, 22:26] = (*OUT, 255)
    # outboard motor on the transom
    s[cy - 3:cy + 4, 43:47] = (*MOTOR, 255); s[cy - 3, 43:47] = (*OUT, 255); s[cy + 3, 43:47] = (*OUT, 255); s[cy - 2:cy + 3, 46] = (*OUT, 255)
    s[cy - 2:cy, 44] = (*MOTOR2, 255); s[cy - 1:cy + 2, 47] = (*OUT, 255)
    # bow cleat and shadow on the water
    s[cy - 1:cy + 2, 12] = (*OUT, 255)
    for x in range(5, 46):
        h = half(min(x, 43)); y = int(cy + h) + 1
        if y < 32 and s[y, x, 3] == 0: s[y, x] = (24, 56, 120, 255)
    return s
