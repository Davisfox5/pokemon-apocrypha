"""Sprout Tower 1F-3F as a Gen 3 conversion (owner, November 4: "follow the conversion guide ... use the
elements and tiles that we have available to us, both native and ... converted").

The plan is HGSS's own: each floor's collision and props (hgss_interior.py), square by square, so every
walkway, the railing ring, the pillar, the ladders and the statues stand where HGSS has them. The art is
Gen 3's:

    north wall   FireRed's Pokemon Tower: the white cap and the purple slatted panel (PokemonTower_2F
                 x 9-13, rows 0-2), HGSS's purple walls in Gen 3's own drawing
    wall scrolls FireRed's Fighting Dojo: its hanging scrolls (SaffronCity_Dojo 5/7, 1-2), at HGSS's lanterns
    floor        FireRed's Fighting Dojo planks, shaded under the wall (SaffronCity_Dojo 2, 3-4)
    pillar       Fortree's tree trunk (FortreeCity_House1 x 3-4), floor to ceiling, its flared foot on the
                 pillar's base: the Bellsprout-swayed column as Gen 3's own trunk
    exit mat     Fortree's (FortreeCity_House1 x 3-4, row 5)

Neither game has a wooden railing, an indoor wooden ladder or a Bellsprout statue, so those three are
drawn here in Gen 3's manner (flat ramps, one-pixel outlines) from the Fortree trunk's own browns:
railings by their neighbours (runs, corners, ends), ladders up and holes down, and HGSS's Bellsprout
statue reduced to the trunk's five browns with a dark outline (CONVERTED).
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE)]
import native as N                        # noqa: E402
import room as RM                         # noqa: E402

PX = 16
X0, Y0 = 4, 5                             # HGSS cell (X0, Y0) is this map's (0, 0)
W, H = 23, 25                             # HGSS x 4-26; rows 5-7 the wall, 8-28 the floor, then black
CONVERTED = ['railings', 'ladders', 'Bellsprout statues']
EXITS = {'sprout1': [(15 - 4, 28 - 5)]}               # the exit mat's west cell (map coords)

def hx(x): return x - X0
def hy(y): return y - Y0

def ramp():
    """The trunk's browns, dark to light (Fortree's own colours)."""
    t = N.Source('FortreeCity_House1')
    px = np.concatenate([t.flat(3, 1).reshape(-1, 3), t.flat(4, 1).reshape(-1, 3), t.flat(3, 3).reshape(-1, 3)])
    u = np.unique(px, axis=0)
    lum = u @ np.array([0.3, 0.59, 0.11])
    u = u[np.argsort(lum)]
    u = u[(u.max(1) - u.min(1)) > 20] if len(u) > 5 else u          # the browns, not the outline greys
    idx = np.linspace(0, len(u) - 1, 5).round().astype(int)
    return [tuple(int(v) for v in u[i]) for i in idx]

class Floor:
    def __init__(self, name):
        self.name = name
        self.h = RM.hgss_room(name)
        self.W, self.H = W, H
        self.lower = np.zeros((H * PX, W * PX, 3), np.uint8)
        self.upper = np.zeros((H * PX, W * PX, 4), np.uint8)
        self.blocked = np.ones((H, W), bool)
        self.behaviors = {}
        self.rect = (0, 0, W, H)
        self.notes = []
        self.R = ramp()
    # the Room interface build.py uses
    def inside(self, x, y):
        return True
    def layers(self):
        return self.lower.copy(), self.upper.copy()
    def image(self):
        out = self.lower.copy(); a = self.upper[..., 3] > 0; out[a] = self.upper[..., :3][a]
        return out
    def sl(self, x, y, w=1, h=1):
        return np.s_[y * PX:(y + h) * PX, x * PX:(x + w) * PX]
    def put(self, x, y, img, upper=False):
        """img at map cell (x, y) (pixel offsets allowed: x, y floats), RGBA or RGB."""
        px, py = int(round(x * PX)), int(round(y * PX))
        h, w = img.shape[:2]
        a = img[..., 3] > 0 if img.shape[2] == 4 else np.ones((h, w), bool)
        tgt = self.upper if upper else self.lower
        ys, xs = np.nonzero(a)
        ty, tx = ys + py, xs + px
        ok = (ty >= 0) & (ty < tgt.shape[0]) & (tx >= 0) & (tx < tgt.shape[1])
        if upper:
            tgt[ty[ok], tx[ok], :3] = img[ys[ok], xs[ok], :3]; tgt[ty[ok], tx[ok], 3] = 255
        else:
            tgt[ty[ok], tx[ok]] = img[ys[ok], xs[ok], :3]

def cells(src, x, y, w, h):
    s = N.Source(src)
    return np.concatenate([np.concatenate([s.flat(x + i, y + j) for i in range(w)], 1) for j in range(h)], 0)

def build(name):
    f = Floor(name)
    coll = f.h['collision']
    walk = np.zeros((H, W), bool)
    for y in range(H):
        for x in range(W):
            X, Y = x + X0, y + Y0
            walk[y, x] = 5 <= X <= 25 and 8 <= Y <= 28 and coll[Y, X] != 128
    props = f.h['props']
    anchor = lambda p: (int(np.floor(p.pos[0])) - X0, int(np.floor(p.pos[2])) - Y0)
    # 1. floor everywhere inside the tower, Fortree's planks
    plank = cells('SaffronCity_Dojo', 2, 4, 1, 1)               # the dojo's plain planks
    shadow = cells('SaffronCity_Dojo', 2, 3, 1, 1)              # and the same planks in the wall's shadow
    for y in range(hy(8), hy(29)):
        for x in range(hx(5), hx(26)):
            f.lower[f.sl(x, y)] = shadow if y == hy(8) else plank
    # the floor beyond the walkways on a top floor that narrows (3F's open sides): black
    inside = np.zeros((H, W), bool)
    for y in range(hy(8), hy(29)):
        for x in range(hx(5), hx(26)):
            inside[y, x] = True
    near = np.zeros_like(walk)
    from scipy.ndimage import binary_dilation
    near = binary_dilation(walk, np.ones((3, 3), bool))
    void = inside & ~near if name == 'sprout3' else np.zeros_like(inside)   # 3F's open sides
    for y, x in zip(*np.nonzero(void)):
        f.lower[f.sl(x, y)] = 0
    # 2. the north wall: Pokemon Tower's cap and purple panel
    cap, face = (cells('PokemonTower_2F', 10, r, 1, 1) for r in (0, 1))
    for x in range(hx(5), hx(26)):
        for y, c in ((1, cap), (2, face)):                      # the tower's wall is two rows; above it black
            f.lower[f.sl(x, y)] = c
    # the dojo's hanging scrolls at HGSS's wall lanterns
    dojo = N.Source('SaffronCity_Dojo')
    scroll = np.concatenate([dojo.flat(5, 1), dojo.flat(5, 2)], 0)
    plain = np.concatenate([dojo.flat(3, 1), dojo.flat(3, 2)], 0)
    mask = (scroll != plain).any(-1)
    sc = np.zeros(scroll.shape[:2] + (4,), np.uint8); sc[..., :3] = scroll; sc[mask, 3] = 255
    for p in props:
        if p.model == 68:                                      # HGSS's wall lanterns
            x, _ = anchor(p)
            f.put(x, 1.4, sc)
    # 3. railings: HGSS's blocked squares on the floor that are not a prop or the pillar
    taken = set()
    for p in props:
        x, y = anchor(p)
        if p.model == 65:                                      # the pillar: its base 3 wide, rows 17-21
            for yy in range(y - 1, y + 4):
                for xx in range(x - 1, x + 2):
                    taken.add((xx, yy))
        elif p.model == 64:
            taken.add((x, y)); taken.add((x, y - 1))
        else:
            taken.add((x, y)); taken.add((x, y - 1))
    rail = np.zeros((H, W), bool)
    for y in range(hy(8), hy(29)):
        for x in range(hx(5), hx(26)):
            if not walk[y, x] and not void[y, x] and (x, y) not in taken:
                rail[y, x] = True
    draw_rails(f, rail, walk)
    # 4. the pillar: Fortree's trunk from the wall to its base, its foot flared on the base row
    for p in props:
        if p.model == 65:
            x, y = anchor(p)
            trunk = cells('FortreeCity_House1', 3, 1, 2, 1)       # one trunk row
            base = cells('FortreeCity_House1', 3, 3, 2, 1)
            tm = np.ones(trunk.shape[:2], bool)
            bottom = y + 3                                          # HGSS's base runs to row 21
            for yy in range(hy(8) - 3, bottom):
                rgba = np.dstack([trunk, np.full(trunk.shape[:2], 255, np.uint8)])
                f.put(x - 0.5, yy, rgba, upper=yy < bottom - 4)
            fb = base.copy()
            bm = (fb != plank[:, :1].repeat(1, 1).mean((0, 1)).astype(np.uint8)).any(-1)
            rgba = np.dstack([fb, np.full(fb.shape[:2], 255, np.uint8)])
            rgba[..., 3] = np.where(trunk_mask(base), 255, 0)
            f.put(x - 0.5, bottom, rgba)
    # 5. statues and ladders
    stat = statue(f.R)
    for p in props:
        x, y = anchor(p)
        if p.model == 64:
            f.put(x, y - 1, stat[:16], upper=True); f.put(x, y, stat[16:])
        elif p.model == 66:
            lad = ladder(f.R, 3)
            f.put(x, y - 2, lad[:16], upper=walk[y - 2, x] if y - 2 >= 0 else False)
            f.put(x, y - 1, lad[16:])
        elif p.model == 67:
            f.put(x, y, hole(f.R))
    mat = cells('FortreeCity_House1', 3, 5, 2, 1)
    for (wx, wy) in EXITS.get(name, []):
        f.lower[f.sl(wx, wy, 2, 1)] = mat
    # 6. traversal: HGSS's walkable squares; the exit, ladders and holes from HGSS's warps
    f.blocked = ~walk
    return f, walk

def trunk_mask(base):
    """The trunk foot's own pixels (not Fortree's floor around it)."""
    t = N.Source('FortreeCity_House1')
    floor = t.flat(1, 4)                                        # Fortree's own floor round the foot
    a = np.concatenate([(t.flat(3, 3) != floor).any(-1), (t.flat(4, 3) != floor).any(-1)], 1)
    return a

def draw_rails(f, rail, walk):
    """A low wooden railing in Gen 3's manner, by which neighbours are railing. An east-west run seen
    face on: a top rail (light edge, dark outline), posts 16 px apart, a lower rail, a contact shadow; where
    HGSS's run is two squares deep it is one tall railing over both. A north-south run seen from above: a
    bar down the middle with its shadow."""
    D, d, m, l, L = f.R
    def shade(c, rows, cols):
        c[rows, cols] = np.clip(c[rows, cols].astype(int) * 0.72, 0, 255).astype(np.uint8)
    for y, x in zip(*np.nonzero(rail)):
        n = lambda dx, dy: 0 <= y + dy < f.H and 0 <= x + dx < f.W and rail[y + dy, x + dx]
        c = f.lower[f.sl(x, y)].copy()
        E, Wn, S, Nn = n(1, 0), n(-1, 0), n(0, 1), n(0, -1)
        horiz = E or Wn
        if horiz:
            x0 = 0 if Wn else 2; x1 = 16 if E else 14
            top = S and (n(1, 1) or n(-1, 1))                 # the upper square of a two-deep run
            low = Nn and (n(1, -1) or n(-1, -1))              # the lower square of one
            if top and not low:
                c[9, x0:x1] = D; c[10, x0:x1] = L; c[11, x0:x1] = l; c[12, x0:x1] = d; c[13, x0:x1] = D
                for px in (7,):
                    c[12:16, px - 1] = D; c[12:16, px] = l; c[12:16, px + 1] = d; c[12:16, px + 2] = D
                if not Wn: c[9:16, x0] = D
                if not E: c[9:16, x1 - 1] = D
            elif low:
                for px in (7,):
                    c[0:11, px - 1] = D; c[0:11, px] = m; c[0:11, px + 1] = d; c[0:11, px + 2] = D
                c[5, x0:x1] = D; c[6, x0:x1] = l; c[7, x0:x1] = d; c[8, x0:x1] = D
                if not Wn: c[0:11, x0] = D
                if not E: c[0:11, x1 - 1] = D
                shade(c, slice(11, 13), slice(x0, x1))
            else:
                c[3, x0:x1] = D; c[4, x0:x1] = L; c[5, x0:x1] = l; c[6, x0:x1] = d; c[7, x0:x1] = D
                c[4:12, 6] = D; c[4:12, 7] = l; c[4:12, 8] = d; c[4:12, 9] = D
                shade(c, slice(12, 14), slice(x0, x1))
        else:
            y0 = 0 if Nn else 3; y1 = 16 if S else 13
            c[y0:y1, 5] = D; c[y0:y1, 6] = L; c[y0:y1, 7] = l; c[y0:y1, 8] = d; c[y0:y1, 9] = D
            shade(c, slice(y0, y1), slice(10, 12))
            if not Nn: c[y0, 5:10] = D
            if not S: c[y1 - 1, 5:10] = D; shade(c, slice(y1, min(16, y1 + 2)), slice(5, 12))
        f.lower[f.sl(x, y)] = c

def ladder(R, rows):
    """A wooden ladder leaning up: two rails, rungs every 4 px, outlined; rows cells tall, 16 px wide."""
    D, d, m, l, L = R
    h = rows * 16
    a = np.zeros((h, 16, 4), np.uint8)
    for x0 in (3, 11):
        a[:, x0 - 1, :3] = D; a[:, x0, :3] = l; a[:, x0 + 1, :3] = d; a[:, x0 + 2, :3] = D
        a[:, x0 - 1:x0 + 3, 3] = 255
    for y in range(3, h - 1, 5):
        a[y, 4:11, :3] = D; a[y + 1, 4:11, :3] = L; a[y + 2, 4:11, :3] = m; a[y + 3, 4:11, :3] = D
        a[y:y + 4, 4:11, 3] = 255
    return a[-32:] if rows > 2 else a

def hole(R):
    """A hatch in the floor with the ladder's top rungs going down: a wooden frame round black."""
    D, d, m, l, L = R
    a = np.zeros((16, 16, 4), np.uint8)
    a[1:15, 1:15, :3] = D; a[1:15, 1:15, 3] = 255
    a[2:14, 2:14, :3] = (24, 16, 16)
    a[2, 2:14, :3] = l; a[13, 2:14, :3] = d; a[2:14, 2, :3] = l; a[2:14, 13, :3] = d
    for y in (5, 9):
        a[y, 4:12, :3] = m; a[y + 1, 4:12, :3] = D
    a[3:13, 4, :3] = m; a[3:13, 11, :3] = m
    return a

def statue(R):
    """HGSS's Bellsprout statue (field model 64), reduced to the trunk's five browns by lightness, with a
    one-pixel dark outline: 16 x 32."""
    p = RM.Prop(64, (1.0, 0.0, 2.9), kind=1).draw(32, 48)
    a = p.rgba
    ys, xs = np.nonzero(a[..., 3])
    cx = int(round(xs.mean()))
    crop = np.zeros((32, 16, 4), np.uint8)
    y1 = ys.max() + 1
    src = a[max(0, y1 - 32):y1, max(0, cx - 8):cx + 8]
    crop[32 - src.shape[0]:, :src.shape[1]] = src
    on = crop[..., 3] > 0
    lum = crop[..., :3].astype(float) @ np.array([0.3, 0.59, 0.11])
    if on.any():
        lo, hi = np.percentile(lum[on], 5), np.percentile(lum[on], 95)
        k = np.clip(((lum - lo) / max(1, hi - lo) * 3.99).astype(int) + 1, 1, 4)
        out = np.zeros_like(crop)
        for i in range(1, 5):
            out[on & (k == i), :3] = R[i]
        out[on, 3] = 255
        from scipy.ndimage import binary_erosion
        edge = on & ~binary_erosion(on)
        out[edge, :3] = R[0]
        return out
    return crop
