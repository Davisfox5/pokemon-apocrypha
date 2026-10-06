"""Route scenery cut from the 1:1 HGSS renders of Route 29 and Route 30.

The renders (`gba/art/claude-routes/references/`) are native scale: one 16 px cell per
movement tile, the same scale as the Cherrygrove render the town was built from. Each has
its own grid origin (measured on tall-grass and ledge edges). Pieces are cut on that grid
and their ground made transparent, so the route's own painted ground (the town's grass and
path, for seamless map connections) shows through.

Tall grass repeats exactly every cell in HGSS, so a block is assembled per 8x8 quadrant
from a six-cell nine-slice; ledges, ledge walls and their corners are single cells; the
Route 46 gate, Mr. Pokemon's house, the berry house, stairs and cliff walls are cut out
whole. Everything returns RGBA arrays for `banks.Bank`.

Original designs and art: Game Freak / Nintendo / Creatures (read-only derivation).
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
REFS = ROOT / 'gba/art/claude-routes/references'
ORIGIN = {29: (4, 5), 30: (6, 4)}
_cache = {}

def ref(route):
    if route not in _cache:
        _cache[route] = np.asarray(Image.open(REFS / f'route{route}-hgss.png').convert('RGB')).astype(np.int16)
    return _cache[route]

def cells(route, cx, cy, w=1, h=1, dx=0, dy=0, pw=None, ph=None):
    """RGBA crop of w x h cells at cell (cx, cy), optionally shifted by (dx, dy) px or sized pw x ph px."""
    ox, oy = ORIGIN[route]; a = ref(route)
    x0, y0 = ox + cx * 16 + dx, oy + cy * 16 + dy
    pw = w * 16 if pw is None else pw; ph = h * 16 if ph is None else ph
    sub = a[y0:y0 + ph, x0:x0 + pw]
    return np.dstack([sub, np.full(sub.shape[:2], 255, np.int16)]).astype(np.uint8)

# Ground colours of each render (lawn and its speckles, path and its rim), made transparent.
GRASS29 = [(104, 208, 160), (104, 200, 160), (96, 200, 152), (96, 192, 144), (88, 184, 144), (88, 176, 136), (72, 168, 136), (104, 216, 160), (112, 208, 160)]
GRASS30 = [(104, 208, 152), (104, 200, 152), (96, 192, 144), (88, 176, 136), (96, 200, 152), (112, 208, 160), (104, 216, 152)]
PATH = [(224, 200, 128), (224, 200, 136), (216, 184, 128), (216, 184, 136), (184, 168, 128), (216, 168, 128), (216, 168, 136), (152, 144, 112), (128, 136, 120)]
TREE = [(64, 56, 40), (64, 64, 40), (72, 72, 48), (80, 88, 40), (88, 104, 32), (88, 112, 32), (96, 120, 32), (112, 144, 32), (120, 152, 32), (136, 168, 40),
        (80, 96, 48), (72, 80, 56), (64, 72, 48), (48, 128, 104), (72, 168, 136), (64, 136, 104), (56, 128, 96)]
TALL = [(56, 152, 88), (40, 136, 80), (64, 168, 112), (32, 112, 80), (80, 192, 120), (32, 120, 88)]

def near(a, colors, tol):
    flat = a[..., :3].reshape(-1, 3).astype(np.int32); cs = np.array(colors, dtype=np.int32)
    d = ((flat[:, None, :] - cs[None]) ** 2).sum(-1).min(1)
    return (d <= tol * tol).reshape(a.shape[:2])

def clear(a, colors, tol=10):
    a = a.copy(); a[..., 3] = np.where(near(a, colors, tol), 0, 255); return a

def components(m):
    from collections import deque
    lab = np.zeros(m.shape, np.int32); n = 0; sizes = {}
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

def fill_holes(keep):
    from collections import deque
    h, w = keep.shape; outside = np.zeros(keep.shape, bool); q = deque()
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

def cutout(a, background, tol=12, keep_largest=1, min_size=0):
    """Drop background colours, keep the largest solid components, fill their holes."""
    a = a.copy(); m = ~near(a, background, tol)
    lab, sizes = components(m)
    best = sorted(sizes, key=sizes.get, reverse=True)[:keep_largest]
    keep = np.zeros(m.shape, bool)
    for b in best:
        if sizes[b] >= min_size: keep |= lab == b
    a[..., 3] = fill_holes(keep) * 255
    return a

# ------------------------------------------------------------------ tall grass (Route 29 block at x 17-30, rows 15-17)

def tall_slices():
    """Nine-slice of the tall grass: top-left, top, left, centre, bottom-left, bottom (right side = mirror)."""
    bg = GRASS29 + PATH
    s = {k: clear(cells(29, *xy), bg, 8) for k, xy in dict(tl=(17, 15), t=(18, 15), l=(17, 16), c=(18, 16), bl=(17, 17), b=(18, 17)).items()}
    return s

def tall_cell(sl, n, s, w, e):
    """Compose one tall-grass cell from the slices by its four neighbours (True = tall grass there)."""
    out = np.zeros((16, 16, 4), np.uint8)
    def pick(top, left):
        if top and left: return sl['tl']
        if top: return sl['t']
        if left: return sl['l']
        return sl['c']
    def pickb(bottom, left):
        if bottom and left: return sl['bl']
        if bottom: return sl['b']
        if left: return sl['l']
        return sl['c']
    # quadrant sources: left half from the left-hand slices, right half from mirrored left-hand slices
    tlq = pick(not n, not w)[0:8, 0:8]
    trq = pick(not n, not e)[:, ::-1][0:8, 8:16]
    blq = pickb(not s, not w)[8:16, 0:8]
    brq = pickb(not s, not e)[:, ::-1][8:16, 8:16]
    out[0:8, 0:8] = tlq; out[0:8, 8:16] = trq; out[8:16, 0:8] = blq; out[8:16, 8:16] = brq
    return out

# ------------------------------------------------------------------ ledges and ledge walls (Route 29)

def ledges():
    bg = GRASS29 + PATH + TALL
    pick = dict(ledge_l=(15, 14), ledge_a=(16, 14), ledge_b=(17, 14), ledge_r=(18, 14),
                wall_top=(13, 16), wall=(13, 17), corner_se=(13, 18), corner_sw=(28, 14), corner_ne=(52, 18))
    out = {}
    for k, xy in pick.items():
        a = clear(cells(29, *xy), bg, 10)
        lab, sizes = components(a[..., 3] > 0)
        for i, n in sizes.items():
            if n < 6: a[..., 3][lab == i] = 0
        out[k] = a
    return out

# ------------------------------------------------------------------ Route 46 gate (Route 29, x 49-55, rows 2-9)

def gate():
    a = cells(29, 48, 1, 9, 9)
    return cutout(a, GRASS29 + PATH + TREE + [(48, 128, 104), (56, 144, 112)], tol=14)

def apricorn():
    """The small Apricorn tree on Route 29's upper lawn (cell 21, rows 10-11)."""
    a = cells(29, 20, 9, 3, 3)
    a = cutout(a, GRASS29 + PATH + [(120, 216, 176), (128, 216, 176), (136, 224, 184), (112, 208, 168), (120, 208, 168)], tol=14)
    return a

def orange_flowers(route=29):
    xy = (45, 10) if route == 29 else (12, 24)
    a = clear(cells(route, *xy), (GRASS29 if route == 29 else GRASS30) + PATH, 12)
    lab, sizes = components(a[..., 3] > 0)
    for i, n in sizes.items():
        if n < 5: a[..., 3][lab == i] = 0
    return a

# ------------------------------------------------------------------ Route 30 cliffs, stairs and houses

def cliff_pieces():
    """Rock wall cells: the two-row top wall, the two-column east wall, the one-row cross wall and the one-column west wall."""
    p = {}
    p['top0'] = cells(30, 20, 0); p['top1'] = cells(30, 20, 1)
    p['east0'] = cells(30, 32, 20); p['east1'] = cells(30, 33, 20)
    p['corner00'] = cells(30, 32, 0); p['corner01'] = cells(30, 33, 0); p['corner10'] = cells(30, 32, 1); p['corner11'] = cells(30, 33, 1)
    p['cross'] = cells(30, 13, 63)
    p['west'] = cells(30, 3, 45, dx=8)
    bg = GRASS30 + PATH + TREE + TALL
    for k in list(p):
        a = p[k].copy(); m = near(a, bg, 10); a[..., 3] = np.where(m, 0, 255); p[k] = a
    return p

def stairs(kind):
    """Wooden steps: 'top' (x 9-11, rows 0-1), 'mid' (x 9-11, rows 27-28), 'low' (x 6-9, row 63, drawn 8 px down).
    The path, lawn and tree pixels around the boards are cleared so the route's own ground shows."""
    if kind == 'top': a = cells(30, 9, 0, 3, 2); a[:, 0:3] = 0
    elif kind == 'mid': a = cells(30, 9, 27, 3, 2)
    else: a = cells(30, 6, 62, 4, 2, dy=8)
    return clear(a, GRASS30 + PATH + TREE + TALL + [(200, 184, 136), (208, 192, 136), (192, 176, 128)], 10)

def mr_pokemon_house():
    """Mr. Pokemon's house with its chimney, mailbox and log fence, 9 x 6 cells from row 2 (the chimney's cap
    rises 4 px into row 1; the rock wall behind it is excluded)."""
    a = cells(30, 23, 2, 9, 6, dy=-4, ph=6 * 16 + 4)
    a = cutout(a, GRASS30 + PATH + TREE + TALL + [(80, 160, 120), (72, 152, 112)], tol=14)
    a[0:26, 0:46, 3] = 0; a[0:14, 110:, 3] = 0      # the plateau's rock wall behind the house
    return a

def berry_house():
    a = cells(30, 10, 48, 9, 7)
    return cutout(a, GRASS30 + PATH + TREE + TALL + [(80, 160, 120), (72, 152, 112)], tol=14)

def berry_tree():
    """The pink-fruited berry tree on the upper lawn (cell 21, rows 4-5)."""
    a = cells(30, 20, 4, 3, 2)
    return cutout(a, GRASS30 + PATH + [(80, 160, 120), (72, 152, 112), (120, 216, 168), (128, 216, 176)], tol=14)
