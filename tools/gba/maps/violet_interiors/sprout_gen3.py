"""Sprout Tower 1F-3F as a custom Gen 3 tileset converted from HGSS (owner, November 5: "you need a pretty
much entirely custom tile set ... go through the grid making for the Gen 4 game, identifying the tile, and
converting it to the Gen 3 game to fit in a grid ... For the ladders, you can use just regular Gen 3
ladders").

Every square of HGSS's floor plan is identified from HGSS's own terrain (which texture covers it, its
collision, its props) and gets the Gen 3 tile for that element. Each element is HGSS's own texture, decoded
from the DS data (Sprout Tower's map texture set and its field models), which HGSS draws at 16 texels a
tile, Gen 3's own density. The conversion keeps each texture's pixels and hues, lifts its contrast to Gen 3's
ramps, adds Gen 3's one-pixel outlines, and redraws the solid things at Gen 3's pitch (a vertical face one
pixel per pixel of height, a top face foreshortened):

    floor        d15_yuka01 planks, one board a row; the row under the north wall in the wall's shadow
    north wall   four rows: a top trim and frieze, then HGSS's niches every three squares (d15_wall01, 2 x 2), lit
                 niches with the lamp where HGSS hangs one (d15_light_b, d15_light_a), piers between
    side walls   the wall's top seen from above (d15_wall01a), an inner edge and outline
    railings     d15_wall02 balusters under d15_wall02a's rail and posts; an east-west run is the railing's
                 face on its first row and the kerb below it on the second; a north-south run is the rail
                 seen from above with the kerb's shade on its east side
    lattice      d15_yuka03 over the drop, framed by d15_yuka03a's inner face on its north side
    plinth       d15_yuka02's tan slab round the pillar's foot
    pillar       d15_pillar01's wood and d15_pillar02's iron band, a post two squares wide as tall as the
                 north wall (the ceiling), its cut top a light end grain (FireRed's Hall of Fame and Lorelei's
                 columns: Gen 3 draws a floor-to-ceiling column at the wall's height with a lit top). HGSS's
                 model runs on 12 tiles high into a black cap (d15_pillar03) that the DS camera never shows.
    statues      d15_obj02's Bellsprout on d15_obj01's pedestal
    exit         d15_genkan's stone
    ladders      Gen 3's own: FireRed's ladder (Mt. Moon B1F 3, 2-3) up, its hole with the ladder down
                 (Mt. Moon 1F 5, 6) rimmed in the floor's wood

Original designs and textures: Game Freak / Nintendo / Creatures (read-only derivation from the games' data).
"""
from __future__ import annotations
import struct, sys
from functools import lru_cache
from pathlib import Path
import numpy as np
from scipy.ndimage import binary_dilation, binary_erosion, label

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / 'route29_catalog')]
import hgss_render as R                 # noqa: E402
import hgss_interior as HI              # noqa: E402
import room as RM                       # noqa: E402
import native as N                      # noqa: E402

PX = 16
X0, Y0 = 4, 4                             # HGSS cell (X0, Y0) is this map's (0, 0)
W, H = 23, 26                             # HGSS x 4-26 (side walls 4 and 26); map rows 0-3 the wall, 4-24 HGSS 8-28, 25 black
WALL = 4                                  # the north wall's height in rows, and so the ceiling's
EXITS = {'sprout1': [(15 - X0, 28 - Y0), (16 - X0, 28 - Y0)]}
CONTRAST = 1.3

def hx(x): return x - X0
def hy(y): return y - Y0

# --------------------------------------------------------------------------- HGSS's own data
@lru_cache(None)
def textures():
    """Sprout Tower's textures by name: the map's set and the field models' own (RGBA)."""
    a = RM.PHG / 'files/a'
    area = R.narc.load(a / '0/4/2')[77]
    _, ms = struct.unpack_from('<HH', area, 0)
    t = R.Tex0(R.narc.load(a / '0/4/4')[ms])
    out = {e.name: R.decode(t, e, None) for e in t.textures}
    fm = RM.models(1)
    for mi in (64, 65, 68):
        m = R.mdlview.Model(fm[mi])
        out.update({e.name: R.decode(m.tex, e, None) for e in m.tex.textures})
    return out

def tex(name):
    return textures()[name].copy()

@lru_cache(None)
def hgss(name):
    """HGSS's floor: terrain, per-pixel texture name, collision, types and props."""
    hdr, bank, matrix = HI.ROOMS[name]
    R.load = HI.loader(bank, matrix, {0: RM.models(0), 1: RM.models(1)})
    R.SNAP = True
    r = R.render(RM.PHG)
    names = np.array(list(r['materials']) + [''], object)
    mat = names[np.where(r['ground_mat'] < 0, len(names) - 1, r['ground_mat'])]
    props = [(b['model'], tuple(b['pos'])) for b in r['buildings']]
    return dict(terrain=np.array(r['terrain']), mat=mat, coll=r['collision'], types=r['types'], props=props)

def cellmat(h, x, y):
    """The texture covering most of HGSS cell (x, y)."""
    from collections import Counter
    m = h['mat'][y * PX:(y + 1) * PX, x * PX:(x + 1) * PX].ravel()
    return Counter(m).most_common(1)[0][0].replace('d15_', '')

# --------------------------------------------------------------------------- Gen 3 colour
def snap(c):
    v = np.round(np.clip(np.asarray(c, float), 0, 255) / 255 * 31).astype(int)
    return ((v << 3) | (v >> 2)).astype(np.uint8)

def g3(img, k=CONTRAST, lift=0.0):
    """HGSS's texture with its own hues, its value spread k times wider round its mean (Gen 3's stronger
    ramps), in 5-bit colour."""
    out = img.copy()
    rgb = img[..., :3].astype(float)
    on = img[..., 3] > 0 if img.shape[-1] == 4 else np.ones(img.shape[:2], bool)
    if not on.any():
        return out
    lum = rgb @ [0.3, 0.59, 0.11]
    mu = lum[on].mean()
    nl = mu + (lum - mu) * k + lift
    scale = np.where(lum > 1, nl / np.maximum(lum, 1), 1.0)[..., None]
    res = np.where(lum[..., None] > 1, rgb * scale, rgb + (nl - lum)[..., None])
    out[..., :3] = snap(res)
    return out

def shade(c, f):
    return snap(np.asarray(c, float) * f)

def rgba(rgb, a=255):
    out = np.zeros(rgb.shape[:2] + (4,), np.uint8); out[..., :3] = rgb; out[..., 3] = a
    return out

def outline(a, col, inner=False):
    """Gen 3's one-pixel outline round an RGBA sprite's opaque pixels (outside them, or on their edge)."""
    on = a[..., 3] > 0
    if inner:
        e = on & ~binary_erosion(on)
    else:
        big = np.zeros((a.shape[0] + 2, a.shape[1] + 2, 4), np.uint8); big[1:-1, 1:-1] = a; a = big
        on = a[..., 3] > 0
        e = binary_dilation(on, np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)) & ~on
    a = a.copy(); a[e, :3] = col; a[e, 3] = 255
    return a

# --------------------------------------------------------------------------- the elements
@lru_cache(None)
def palette():
    fl = g3(tex('d15_yuka01'))
    cols = sorted({tuple(int(v) for v in c) for c in fl[..., :3].reshape(-1, 3)}, key=lambda c: sum(c))
    wall = g3(tex('d15_wall01'))
    purp = sorted({tuple(int(v) for v in c) for c in wall[..., :3].reshape(-1, 3) if c[2] > c[1] + 8}, key=lambda c: sum(c))
    return dict(floor=cols, purple=purp, outline=(41, 24, 24), wood_dark=tuple(int(v) for v in shade(cols[0], 0.62)))

@lru_cache(None)
def floor_tex():
    return g3(tex('d15_yuka01'))[..., :3]

def floor_cell(x, y, shadow=0):
    """The plank floor at map cell (x, y): HGSS's 64 x 64 texture is four boards by four squares."""
    t = floor_tex()
    c = t[(y % 4) * PX:(y % 4 + 1) * PX, (x % 4) * PX:(x % 4 + 1) * PX].copy()
    if shadow:
        c[:shadow] = shade(c[:shadow], 0.72)
    return c

def wall_strip(lit, windows=()):
    """The north wall, W x WALL squares: a top trim, then HGSS's niches (2 x 2) centred every three squares
    from 2.5, lit ones with the lamp; piers between. Side walls take columns 0 and W - 1."""
    P = palette()['purple']
    dk, d, m, l = P[0], P[1], P[len(P) // 2], P[-1]
    out = np.zeros((WALL * PX, W * PX, 3), np.uint8)
    out[:] = m
    out[0:2] = dk; out[2:4] = d; out[4:6] = l; out[6:7] = d          # the trim where the wall meets the ceiling
    out[7:30] = m; out[27:29] = l; out[29:31] = d                    # the frieze, a lit moulding over the niches
    # piers: a light edge each side of every niche, the slatted skirting along the foot
    base = g3(tex('d15_wall01'))[..., :3]
    skirt = base[24:32, 4:12]                                       # the niche texture's own slats
    for x in range(0, W * PX, 8):
        out[56:64, x:x + 8] = skirt[:, :min(8, W * PX - x)]
    niche = base
    lamp = g3(tex('d15_light_b.1'))[..., :3]
    flame = small_flame()
    for k in range(7):
        cx = 2.5 + 3 * k
        x0 = int((cx - 1) * PX)
        if x0 < PX or x0 + 32 > (W - 1) * PX:
            continue
        art = lamp.copy() if cx in lit else niche.copy()
        if cx in lit:
            fa = flame
            fy, fx = 9, 16 - fa.shape[1] // 2
            on = fa[..., 3] > 0
            sub = art[fy:fy + fa.shape[0], fx:fx + fa.shape[1]]
            sub[on] = fa[..., :3][on]
        out[32:64, x0:x0 + 32] = art
        out[31:64, x0 - 1] = l; out[31:64, x0 + 32] = dk
    for cx in windows:
        w = g3(tex('d15_win'))
        x0 = int((cx - 1) * PX)
        on = w[..., 3] > 0
        sub = out[32:64, x0:x0 + 32]
        sub[on] = w[..., :3][on]
    return out

def small_flame():
    """d15_light_a's flame on its bracket at two thirds (the lamp niche is drawn 2 squares wide, not HGSS's 3)."""
    f = tex('d15_light_a.1')
    on = f[..., 3] > 0
    ys, xs = np.nonzero(on)
    f = f[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = f.shape[:2]
    nh, nw = max(1, round(h * 2 / 3)), max(1, round(w * 2 / 3))
    yi = (np.arange(nh) * h / nh).astype(int); xi = (np.arange(nw) * w / nw).astype(int)
    return g3(f[yi][:, xi], 1.1)

def side_wall(rows, east):
    """A side wall seen from above: the wall's top purple, its inner edge lit, an outline at the floor."""
    P = palette()['purple']
    c = np.zeros((rows * PX, PX, 3), np.uint8); c[:] = P[1]
    c[:, 3:13] = P[len(P) // 2]
    edge = (slice(None), 0) if east else (slice(None), PX - 1)
    lite = (slice(None), 1) if east else (slice(None), PX - 2)
    c[lite] = P[-1]; c[edge] = palette()['outline']
    return c

def rail_parts():
    """d15_wall02's balusters (32 x 32: the rail across its top 6 rows) and d15_wall02a's posts."""
    b = g3(tex('d15_wall02'))[..., :3]
    a = g3(tex('d15_wall02a'))[..., :3]
    return b, a

def railing_face(c, x0, x1, post_at, end_l, end_r):
    """An east-west railing seen face on in a 16 px row: rail 4 px, balusters 9, foot rail 2, outlined."""
    b, a = rail_parts()
    O = palette()['outline']
    rail, bal = b[0:6], b[6:32]
    red = rail[2, 2]; redl = shade(red, 1.25); redd = shade(red, 0.7)
    c[1, x0:x1] = O; c[2, x0:x1] = redl; c[3:5, x0:x1] = red; c[5, x0:x1] = redd
    for x in range(x0, x1):
        c[6:13, x] = bal[4:11, x % 32]
    c[13, x0:x1] = redd; c[14, x0:x1] = red; c[15, x0:x1] = O
    for px in post_at:
        post(c, px)
    if end_l: c[1:16, x0] = O
    if end_r: c[1:16, x1 - 1] = O

def post(c, px, top=0):
    """A railing post 4 px wide: d15_wall02a's red with its tan foot band, outlined."""
    b, a = rail_parts()
    O = palette()['outline']
    red = b[2, 2]
    c[top:16, px - 2] = O; c[top:16, px + 3] = O
    c[top:16, px - 1:px + 3] = red
    c[top:16, px - 1] = shade(red, 1.25)
    c[top:16, px + 2] = shade(red, 0.7)
    c[top, px - 1:px + 3] = O
    tan = a[1, 1]
    c[12:14, px - 1:px + 3] = tan

def kerb(c, x0, x1):
    """The railing's kerb below its face: its top (2 px, nailed) and its dark front (the HGSS shade band)."""
    fl = palette()['floor']
    O = palette()['outline']
    top, face = shade(fl[1], 0.8), shade(fl[0], 0.62)
    c[0:4, x0:x1] = top
    c[4:12, x0:x1] = face
    c[12, x0:x1] = O
    c[13:16, x0:x1] = shade(c[13:16, x0:x1], 0.8)
    for x in range(x0 + 3, x1, 6):
        c[1, x] = shade(fl[0], 0.5)

def rail_ns(c, y0, y1, posts):
    """A north-south railing seen from above: the rail (6 px, outlined) and the kerb's shade east of it."""
    b, a = rail_parts()
    O = palette()['outline']
    red = b[2, 2]
    c[y0:y1, 3] = O; c[y0:y1, 4] = shade(red, 1.25); c[y0:y1, 5:8] = red; c[y0:y1, 8] = shade(red, 0.7); c[y0:y1, 9] = O
    c[y0:y1, 10:13] = shade(c[y0:y1, 10:13], 0.62)
    c[y0:y1, 13] = shade(c[y0:y1, 13], 0.8)
    for py in posts:
        c[py:py + 5, 3:10] = O
        c[py + 1:py + 4, 4:9] = shade(red, 1.25)
        c[py + 2:py + 4, 5:8] = a[1, 1]

def lattice_cell(x, y):
    t = g3(tex('d15_yuka03'))[..., :3]
    return t[(y % 2) * PX:(y % 2 + 1) * PX, (x % 2) * PX:(x % 2 + 1) * PX].copy()

def plinth_slab(w, h):
    """d15_yuka02's tan slab, w x h px: the top lit, the front its own three bands, outlined."""
    t = g3(tex('d15_yuka02'))[..., :3]
    O = palette()['outline']
    top, f1, f2, f3 = t[2, 2], t[8, 2], t[11, 2], t[14, 2]
    s = np.zeros((h, w, 3), np.uint8); s[:] = top
    s[h - 7:h - 5] = f1; s[h - 5:h - 3] = f2; s[h - 3:h - 1] = f3
    s[1, 1:-1] = shade(top, 1.12); s[1:h - 7, 1] = shade(top, 1.12)
    s[0] = O; s[-1] = O; s[:, 0] = O; s[:, -1] = O
    return s

def pillar_art():
    """The swaying pillar at Gen 3's pitch: a post 2 squares wide and WALL rows tall (floor to ceiling, as tall
    as the north wall), d15_pillar01's grain lit from the west, HGSS's two d15_pillar02 iron bands where they sit
    on HGSS's 12-tile post (a quarter and three quarters up), and its top cut by the ceiling shown as the post's
    own end grain (Gen 3's lit column top) in place of HGSS's black cap."""
    wood = g3(tex('d15_pillar01'))[..., :3]
    band = g3(tex('d15_pillar02'))[..., :3]
    O = palette()['outline']
    hgt, top = WALL * PX, 8
    a = np.zeros((hgt + top, 32, 4), np.uint8)
    face = wood[:hgt, 16:48].copy()
    face[:, 0:2] = shade(face[:, 0:2], 1.18); face[:, 2:4] = shade(face[:, 2:4], 1.08)
    face[:, 24:28] = shade(face[:, 24:28], 0.88); face[:, 28:32] = shade(face[:, 28:32], 0.74)
    for frac in (0.25, 0.75):
        by = hgt - round(hgt * frac) - 5
        b = band[11:21].copy()
        b[:, 28:32] = shade(b[:, 28:32], 0.8)
        face[by:by + 10] = b
        face[by - 1] = O; face[by + 10] = shade(O, 1.4)
    a[top:, :, :3] = face; a[top:, :, 3] = 255
    # the end grain where the ceiling cuts it: the wood's own tones in rings round the pith
    fl = sorted({tuple(int(v) for v in c) for c in wood.reshape(-1, 3)}, key=sum)
    t = np.zeros((top, 32, 3), np.uint8); t[:] = shade(fl[-1], 1.1)
    t[1:top - 1, 3:29] = shade(fl[-2], 1.08)
    t[2:top - 2, 7:25] = shade(fl[-1], 1.1)
    t[3:top - 3, 12:20] = shade(fl[-3], 1.0)
    a[:top, :, :3] = t; a[:top, :, 3] = 255
    a[top - 1, :, :3] = shade(fl[0], 0.75)
    return outline(a, O)

def plinth_art():
    """d15_yuka02's tan base round the post's foot: 12 px of slab each side, 24 px of top behind the foot line
    and 4 in front, then the slab's own three-band front."""
    s = plinth_slab(56, 24 + 4 + 7)
    return rgba(s)

def statue_art():
    """d15_obj02's Bellsprout standing on d15_obj01's pedestal: the pedestal 18 px wide, its top 6 px, its
    front 8 px (0.5 tiles), the Bellsprout 32 px square above it as HGSS draws it at 16 texels a tile."""
    bs = g3(tex('d15_obj02'), 1.15)
    ped = g3(tex('d15_obj01'))[..., :3]
    O = palette()['outline']
    on = bs[..., 3] > 0
    ys, xs = np.nonzero(on)
    bs = bs[ys.min():ys.max() + 1]
    hb = bs.shape[0]
    a = np.zeros((hb + 12, 32, 4), np.uint8)
    p = np.zeros((14, 18, 4), np.uint8)
    p[:, :, :3] = ped[1, 8]; p[..., 3] = 255
    p[0:6, :, :3] = ped[1, 2]
    p[6:, :, :3] = ped[13, 8]
    p[6:, 0:2, :3] = shade(ped[13, 8], 1.1)
    p[0, :, :3] = O; p[-1, :, :3] = O; p[:, 0, :3] = O; p[:, -1, :3] = O; p[6, :, :3] = shade(ped[13, 8], 0.75)
    a[hb - 2:hb + 12, 7:25] = p
    on = bs[..., 3] > 0
    sub = a[:hb]
    sub[on] = bs[on]
    return a

# --------------------------------------------------------------------------- Gen 3 ladders
@lru_cache(None)
def gen3_ladder():
    """FireRed's ladder up: Mt. Moon B1F (3, 2) and (3, 3), its top layer (the ladder's own pixels), 16 x 32."""
    s = N.Source('MtMoon_B1F')
    return np.concatenate([s.cell(3, 2)['top'], s.cell(3, 3)['top']], 0)

@lru_cache(None)
def gen3_hole():
    """FireRed's hole with the ladder going down: Mt. Moon 1F (5, 6); its cave rim recoloured in the floor's
    wood (the ladder and the dark kept), 16 x 16 RGBA."""
    s = N.Source('MtMoon_1F')
    c = s.flat(5, 6)
    near = np.concatenate([s.flat(4, 6), s.flat(6, 6), s.flat(5, 7)]).reshape(-1, 3)
    floor = {tuple(v) for v in near}
    lad = {tuple(v) for v in gen3_ladder()[..., :3][gen3_ladder()[..., 3] > 0]}
    a = np.zeros((16, 16, 4), np.uint8)
    fl = palette()['floor']
    lum = c.astype(float) @ [0.3, 0.59, 0.11]
    for y in range(16):
        for x in range(16):
            v = tuple(c[y, x])
            if v in lad:
                a[y, x, :3] = c[y, x]; a[y, x, 3] = 255
            elif lum[y, x] < 40:
                a[y, x, :3] = (16, 8, 8); a[y, x, 3] = 255
            elif v not in floor:
                a[y, x, :3] = shade(fl[0], 0.55 if lum[y, x] < 90 else 0.75); a[y, x, 3] = 255
    return a

# --------------------------------------------------------------------------- the floor
class Floor:
    def __init__(self, name):
        self.name = name
        self.W, self.H = W, H
        self.lower = np.zeros((H * PX, W * PX, 3), np.uint8)
        self.upper = np.zeros((H * PX, W * PX, 4), np.uint8)
        self.blocked = np.ones((H, W), bool)
        self.behaviors = {}
        self.rect = (0, 0, W, H)
        self.notes = []
    def inside(self, x, y):
        return True
    def layers(self):
        return self.lower.copy(), self.upper.copy()
    def image(self):
        out = self.lower.copy(); a = self.upper[..., 3] > 0; out[a] = self.upper[..., :3][a]
        return out
    def sl(self, x, y, w=1, h=1):
        return np.s_[y * PX:(y + h) * PX, x * PX:(x + w) * PX]
    def put(self, px, py, img, upper_from=None):
        """img with its top-left at pixel (px, py); RGBA pixels above pixel row upper_from go on the top layer."""
        h, w = img.shape[:2]
        a = img[..., 3] > 0 if img.shape[2] == 4 else np.ones((h, w), bool)
        ys, xs = np.nonzero(a)
        ty, tx = ys + py, xs + px
        ok = (ty >= 0) & (ty < self.lower.shape[0]) & (tx >= 0) & (tx < self.lower.shape[1])
        ys, xs, ty, tx = ys[ok], xs[ok], ty[ok], tx[ok]
        up = (ty < upper_from) if upper_from is not None else np.zeros(len(ty), bool)
        self.lower[ty[~up], tx[~up]] = img[ys[~up], xs[~up], :3]
        self.upper[ty[up], tx[up], :3] = img[ys[up], xs[up], :3]; self.upper[ty[up], tx[up], 3] = 255

def build(name):
    h = hgss(name)
    f = Floor(name)
    coll = h['coll']
    walk = np.zeros((H, W), bool)
    for y in range(H):
        for x in range(W):
            X, Y = x + X0, y + Y0
            walk[y, x] = 5 <= X <= 25 and 8 <= Y <= 28 and coll[Y, X] != 128
    props = h['props']
    anchor = lambda p: (p[1][0] - X0, p[1][2] - Y0)          # map coordinates, fractional (cell centres at .5)
    mats = {(x, y): cellmat(h, x + X0, y + Y0) for y in range(H) for x in range(W)}
    lat = np.array([[mats[(x, y)].startswith('yuka03') and 1 <= x < W - 1 and y >= WALL for x in range(W)] for y in range(H)])
    # 1. floor, the row under the wall in its shadow
    for y in range(WALL, H - 1):
        for x in range(1, W - 1):
            f.lower[f.sl(x, y)] = floor_cell(x, y, 4 if y == WALL else 0)
    # 2. the lattice over the drops, its north side the opening's inner face (d15_yuka03a)
    face = g3(tex('d15_yuka03a'))[..., :3]
    for y, x in zip(*np.nonzero(lat)):
        c = lattice_cell(x, y)
        if not lat[y - 1, x]:
            c[0:3] = face[0:3, :16] if face.shape[0] >= 3 else c[0:3]
            c[0] = palette()['outline']; c[1:4] = shade(palette()['floor'][0], 0.62)
        if not lat[y, x - 1]: c[:, 0] = palette()['outline']
        if not lat[y, x + 1]: c[:, -1] = palette()['outline']
        if y + 1 < H and not lat[y + 1, x]: c[-1] = shade(palette()['floor'][-1], 1.0)
        f.lower[f.sl(x, y)] = c
    # 3. the north wall and side walls, the south edge
    lamps = [p[1][0] - X0 for p in props if p[0] == 68]
    wins = []
    if name == 'sprout3':
        wm = h['mat'] == 'd15_win'
        ys, xs = np.nonzero(wm)
        if len(xs):
            lab, n = label(wm)
            for i in range(1, n + 1):
                yy, xx = np.nonzero(lab == i)
                if yy.mean() < 8 * PX:
                    wins.append(round((xx.mean() / PX - X0) * 2) / 2)
    f.lower[0:WALL * PX] = wall_strip(set(lamps), [w for w in wins if any(abs(w - (2.5 + 3 * k)) < 0.6 for k in range(7))])
    for x, east in ((0, False), (W - 1, True)):
        f.lower[:, x * PX:(x + 1) * PX] = side_wall(H, east)
    f.lower[(H - 1) * PX:] = 0                                      # south of the last floor row: Gen 3's black
    # 4. what stands on the floor: the props' squares, then railings in the rest of HGSS's blocked squares
    taken = set()
    for m, pos in props:
        cx, cz = pos[0] - X0, pos[2] - Y0
        if m == 65:
            for yy in range(int(cz) - 1, int(cz) + 2):
                for xx in range(int(cx) - 1, int(cx) + 2):
                    taken.add((xx, yy))
        elif m in (64, 66, 67):
            taken.add((int(cx), int(cz))); taken.add((int(cx), int(cz) - 1))
    plinth = (h['mat'] == 'd15_yuka02')
    rail = np.zeros((H, W), bool)
    for y in range(WALL, H - 1):
        for x in range(1, W - 1):
            if not walk[y, x] and not lat[y, x] and (x, y) not in taken:
                rail[y, x] = True
    draw_rails(f, rail, walk)
    # 5. the plinth round the pillar's foot and the pillar
    for m, pos in props:
        if m != 65:
            continue
        cx, cz = pos[0] - X0, pos[2] - Y0
        foot = int((cz + 1) * PX)                       # the pillar's front face meets the floor here
        f.put(int((cx - 1) * PX) - 12, foot - 24, plinth_art())
        pa = pillar_art()
        f.put(int((cx - 1) * PX) - 1, foot - pa.shape[0] + 1, pa, upper_from=foot - PX)
    # 6. statues, Gen 3 ladders and holes
    st = statue_art()
    for m, pos in props:
        cx, cz = pos[0] - X0, pos[2] - Y0
        if m == 64:
            foot = int((cz + 0.5) * PX) + 2
            f.put(int(cx * PX) - 16, foot - st.shape[0], st, upper_from=foot - PX - 2)
        elif m == 66:
            lad = gen3_ladder()
            x, y = int(cx), int(cz)
            on = lad[..., 3] > 0
            sh = np.zeros_like(on); sh[2:, 2:] = on[:-2, :-2]; sh &= ~on       # its contact shadow, down and east
            sl = f.lower[(y - 1) * PX:(y + 1) * PX, x * PX:(x + 1) * PX]
            sl[sh] = shade(sl[sh], 0.62)
            f.put(x * PX, (y - 1) * PX, lad)
        elif m == 67:
            x, y = int(cx), int(cz)
            f.put(x * PX, y * PX, gen3_hole())
    # 7. the exit: d15_genkan's stone, two squares
    for (wx, wy) in EXITS.get(name, []):
        g = g3(tex('d15_genkan'))[..., :3].copy()
        g[0] = palette()['outline']; g[1] = shade(g[4, 4], 1.15)
        f.lower[f.sl(wx, wy)] = g
    # 8. traversal: HGSS's own
    f.blocked = ~walk
    f.lat = lat
    return f, walk

def draw_rails(f, rail, walk):
    """Railings by their neighbours, in HGSS's textures. A run longer east-west than north-south is the
    railing's face on its first row and its kerb on the second (rows behind those stay floor); a north-south
    run is the rail seen from above, in the square of the strip next to the walkway. Posts at a run's ends
    and every third square."""
    Hh, Ww = rail.shape
    n = lambda x, y: 0 <= y < Hh and 0 <= x < Ww and rail[y, x]
    def run(x, y, dx, dy):
        k = 1
        for sgn in (1, -1):
            xx, yy = x + sgn * dx, y + sgn * dy
            while n(xx, yy):
                k += 1; xx += sgn * dx; yy += sgn * dy
        return k
    ew = np.zeros_like(rail)
    for y, x in zip(*np.nonzero(rail)):
        ew[y, x] = run(x, y, 1, 0) >= run(x, y, 0, 1)
    w = lambda x, y: 0 <= y < Hh and 0 <= x < Ww and walk[y, x]
    for y, x in zip(*np.nonzero(rail)):
        c = f.lower[f.sl(x, y)].copy()
        if ew[y, x]:
            k = 0
            while n(x, y - k - 1) and ew[y - k - 1, x]:
                k += 1
            E, Wn = n(x + 1, y) and ew[y, x + 1], n(x - 1, y) and ew[y, x - 1]
            if k == 0:
                xs = x
                while n(xs - 1, y) and ew[y, xs - 1]: xs -= 1
                posts = [2] if (x - xs) % 3 == 0 else []
                if not E: posts.append(11)
                railing_face(c, 0, 16, posts, not Wn, not E)
            elif k == 1:
                kerb(c, 0, 16)
            else:
                continue
        else:
            # the strip's square next to the walkway carries the rail (its west square when both or neither do)
            wide = [xx for xx in (x - 1, x + 1) if n(xx, y) and not ew[y, xx]]
            if wide:
                mine = w(x - 1, y) or w(x + 1, y)
                other = wide[0]
                theirs = w(other - 1, y) or w(other + 1, y)
                if theirs and not mine:
                    continue
                if mine == theirs and other < x:
                    continue
            Nn = n(x, y - 1)
            posts = [1] if not Nn else ([6] if (y % 3 == 0) else [])
            rail_ns(c, 0, 16, posts)
        f.lower[f.sl(x, y)] = c

def catalog():
    """The tile families, for the evidence sheet."""
    out = {}
    out['floor (4 x 4)'] = floor_tex()
    out['north wall'] = wall_strip({5.5, 11.5, 17.5})[:, :10 * PX]
    out['lattice'] = np.concatenate([np.concatenate([lattice_cell(x, y) for x in range(2)], 1) for y in range(2)], 0)
    out['pillar'] = pillar_art()
    out['statue'] = statue_art()
    out['ladder up (FireRed)'] = gen3_ladder()
    out['hole down (FireRed)'] = gen3_hole()
    out['plinth'] = plinth_slab(64, 40)
    return out
