"""Fuchsia's terrain elements as Gen 3 pieces on HGSS's cells.

Every element here is placed from the cell ledger (source/trace/material-grid.txt), one piece to a cell or
to an 8 px quadrant of it, and no pixel comes from an HGSS render. The pieces are FireRed's own (the
General and Fuchsia tilesets in the engine checkout), read as palette indices so that their background
(FireRed's lawn) is left out and their ramps can take HGSS's colours:

    rock      the General mountain set (nine-slice 0x068-0x07A, inner corners 0x0B2-0x0BB) in the ramp of
              HGSS's cliff01gs / wall01_d, autotiled per quadrant; the terrace is one level
    ledges    the General jump ledges (south 0x087 and its ends 0x0B0/0x0B1, west 0x083/0x085/0x08D,
              east 0x084/0x086/0x08E), same ramp
    ponds     FireRed's pond nine-slice (0x1A5-0x1AF, 0x333-0x335): its rim in the rock ramp, its water
              HGSS's pond_on texture in the world's phase, its deep band pond_edge's blue
    hedges    Fuchsia's pen hedge (0x290-0x295, 0x29B, 0x29C) in sek_teien's greens, composed per quadrant
              so the back hedge is one cell deep, as HGSS's is
    fences    FireRed's grey fence (0x336 runs, 0x0F4/0x0F5 columns, corners) in fence_a's greys
    pen beds  HGSS's soil (f_dodai_a) in a frame of its planks (f_dodai), or its dark bed; a flower to a cell
"""
from __future__ import annotations
import numpy as np

W = H = 64
GROUND, TREE, PEN, ROCK, FENCE = 0, 1, 2, 3, 4

ROCK_RAMP = {9: (239, 189, 140), 10: (222, 173, 123), 11: (198, 148, 115), 12: (165, 115, 99), 13: (132, 90, 74), 14: (99, 74, 57)}
HEDGE_RAMP = {14: (123, 231, 99), 13: (99, 214, 66), 12: (41, 181, 66), 11: (24, 115, 82), 10: (24, 90, 49)}
FENCE_RAMP = {1: (239, 247, 255), 2: (206, 214, 239), 3: (156, 165, 173), 4: (156, 165, 173), 5: (132, 140, 148), 6: (107, 107, 123), 7: (74, 66, 74)}
DEEP = (57, 140, 239)
BED = (70, 116, 91)
SHADOW, WATER = 1, 2                                       # values of a piece's 'special' plane

class Pieces:
    def __init__(self, ts, tex):
        self.ts, self.tex = ts, tex
        self.cache = {}

    def idx(self, m):
        ts = self.ts
        ent = ts.pm[m] if m < ts.n_meta else ts.sm[m - ts.n_meta]
        out = np.zeros((16, 16), int)
        for layer in (0, 1):
            for q in range(4):
                e = int(ent[layer * 4 + q])
                t = ts.tile(e & 0x3FF)
                if t is None:
                    continue
                if e & 0x400: t = t[:, ::-1]
                if e & 0x800: t = t[::-1]
                b = out[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
                b[t > 0] = ((e >> 12) * 16 + t)[t > 0]
        return out

    def piece(self, m, kind):
        """(rgba, special): the metatile with its lawn left out and its ramps in HGSS's colours."""
        if (m, kind) in self.cache:
            return self.cache[(m, kind)]
        ix = self.idx(m)
        rgba = np.zeros((16, 16, 4), np.uint8)
        sp = np.zeros((16, 16), np.uint8)
        pal9 = self.ts.sp[9]
        for (y, x), v in np.ndenumerate(ix):
            b, i = divmod(int(v), 16)
            c = None
            if kind in ('rock', 'pond') and b == 1 and i in ROCK_RAMP:
                c = ROCK_RAMP[i]
            elif kind == 'rock' and b == 1 and i == 4:
                sp[y, x] = SHADOW
            elif kind == 'pond' and b == 3 and i == 12:
                sp[y, x] = WATER
            elif kind == 'pond' and b == 3 and i == 14:
                c = DEEP
            elif kind == 'hedge' and b == 9 and i in HEDGE_RAMP:
                c = HEDGE_RAMP[i]
            elif kind == 'hedge' and b == 9 and i == 2:
                sp[y, x] = SHADOW
            elif kind == 'hedge' and b == 9 and i:
                c = pal9[i]
            elif kind == 'fence' and b in (2, 3) and i in FENCE_RAMP:
                c = FENCE_RAMP[i]
            if c is not None:
                rgba[y, x] = (*c, 255)
        self.cache[(m, kind)] = (rgba, sp)
        return rgba, sp

LAWN_DARK = {(115, 205, 164): (65, 180, 139), (139, 222, 189): (115, 205, 164), (164, 230, 197): (139, 222, 189), (65, 180, 139): (49, 156, 123)}

def paint(out, fam, P, x, y, m, kind, family, sl=np.s_[0:16, 0:16], src=None):
    """Lay a piece (or the part sl of it, taken from src of the piece) on cell (x, y)."""
    rgba, sp = P.piece(m, kind)
    src = sl if src is None else src
    part, s = rgba[src], sp[src]
    Y0, X0 = y * 16 + (sl[0].start or 0), x * 16 + (sl[1].start or 0)
    h, w = part.shape[:2]
    d, f = out[Y0:Y0 + h, X0:X0 + w], fam[Y0:Y0 + h, X0:X0 + w]
    a = part[..., 3] > 0
    d[a] = part[..., :3][a]
    f[a] = family
    for yy, xx in zip(*np.nonzero(s == SHADOW)):
        d[yy, xx] = LAWN_DARK.get(tuple(d[yy, xx].tolist()), tuple(int(v * 0.8) for v in d[yy, xx]))
    wm = s == WATER
    if wm.any():
        t = P.tex['pond_on'][..., :3]
        ys, xs = (np.arange(h) + Y0) % t.shape[0], (np.arange(w) + X0) % t.shape[1]
        d[wm] = t[ys][:, xs][wm]
        f[wm] = family

Q = [(qy, qx, np.s_[qy * 8:qy * 8 + 8, qx * 8:qx * 8 + 8]) for qy in (0, 1) for qx in (0, 1)]

# ------------------------------------------------------------------ rock and ledges
NINE = {('N', 'W'): 0x68, ('N', 'M'): 0x69, ('N', 'E'): 0x6A, ('M', 'W'): 0x70, ('M', 'M'): 0x71, ('M', 'E'): 0x72,
        ('S', 'W'): 0x78, ('S', 'M'): 0x79, ('S', 'E'): 0x7A}
INNER = dict(se=0xB2, sw=0xB3, ne=0xBA, nw=0xBB)

def rock_mask(g):
    r = np.array([[c == 'R' for c in row] for row in g])
    r[51, 8:24] = True                                     # the terrace's south face runs on behind the south row
    return r

def rock(out, fam, P, g):
    r = rock_mask(g)
    isr = lambda x, y: True if not (0 <= x < W and 0 <= y < H) else bool(r[y, x])
    for y in range(H):
        for x in range(W):
            if not r[y, x]:
                continue
            lo = {k: not isr(x + dx, y + dy) for k, (dx, dy) in
                  dict(n=(0, -1), e=(1, 0), s=(0, 1), w=(-1, 0), ne=(1, -1), se=(1, 1), sw=(-1, 1), nw=(-1, -1)).items()}
            diag = [k for k in ('ne', 'se', 'sw', 'nw') if lo[k]]
            if not any(lo[k] for k in 'nesw') and len(diag) == 1:
                paint(out, fam, P, x, y, INNER[diag[0]], 'rock', ROCK)      # an inner corner is placed whole
                continue
            for qy, qx, sl in Q:
                v = ('N', 'S')[qy] if lo['n'] and lo['s'] else 'N' if lo['n'] else 'S' if lo['s'] else 'M'
                h = ('W', 'E')[qx] if lo['w'] and lo['e'] else 'W' if lo['w'] else 'E' if lo['e'] else 'M'
                vk, hk = 'ns'[qy], 'we'[qx]
                m = INNER[vk + hk] if lo[vk + hk] and not lo[vk] and not lo[hk] else NINE[(v, h)]
                paint(out, fam, P, x, y, m, 'rock', ROCK, sl)

def ledges(out, fam, P, g):
    at = lambda x, y: g[y][x] if 0 <= x < W and 0 <= y < H else ' '
    for y in range(H):
        for x in range(W):
            c = g[y][x]
            if c == 'Q':
                m = 0x83 if at(x, y - 1) != 'Q' else 0x85
            elif c == 'E':
                m = 0x84 if at(x, y - 1) != 'E' else 0x86
            elif c == 'J':
                m = 0x8D if at(x + 1, y) == 'L' else 0x8E   # the corner where a side ledge turns into the south one
            elif c == 'L':
                m = 0xB1 if at(x + 1, y) not in 'LJ' else 0xB0 if at(x - 1, y) not in 'LJ' else 0x87
            else:
                continue
            paint(out, fam, P, x, y, m, 'rock', ROCK)

# ------------------------------------------------------------------ ponds
POND = {('N', 'W'): 0x1A5, ('N', 'M'): 0x1A6, ('N', 'E'): 0x1A7, ('M', 'W'): 0x1AD, ('M', 'M'): 0x1AE, ('M', 'E'): 0x1AF,
        ('S', 'W'): 0x333, ('S', 'M'): 0x334, ('S', 'E'): 0x335}

def ponds(out, fam, P, g):
    wat = lambda x, y: 0 <= x < W and 0 <= y < H and g[y][x] == '~'
    for y in range(H):
        for x in range(W):
            if not wat(x, y):
                continue
            for qy, qx, sl in Q:
                dy, dx = (-1, 1)[qy], (-1, 1)[qx]
                v = 'M' if wat(x, y + dy) else 'NS'[qy]
                h = 'M' if wat(x + dx, y) else 'WE'[qx]
                paint(out, fam, P, x, y, POND[(v, h)], 'pond', PEN, sl)
                if v == h == 'M' and not wat(x + dx, y + dy):
                    # an inner corner: the rim turns here, so the corner quadrant takes the rim's own corner
                    # pixels (the 3 px where the two rims meet), from the opposite outer corner piece
                    rgba, _ = P.piece(POND[('NS'[1 - qy], 'WE'[1 - qx])], 'pond')
                    Y0, X0 = y * 16 + (13 if qy else 0), x * 16 + (13 if qx else 0)
                    part = rgba[(0 if qy else 13):(3 if qy else 16), (0 if qx else 13):(3 if qx else 16)]
                    a = part[..., 3] > 0
                    out[Y0:Y0 + 3, X0:X0 + 3][a] = part[..., :3][a]

# ------------------------------------------------------------------ pen hedges
def hedges(out, fam, P, g):
    hd = lambda x, y: 0 <= x < W and 0 <= y < H and g[y][x] == 'h'
    top, bot = np.s_[0:8, 0:16], np.s_[8:16, 0:16]
    for y in range(H):
        for x in range(W):
            if not hd(x, y):
                continue
            n, s, e, w = hd(x, y - 1), hd(x, y + 1), hd(x + 1, y), hd(x - 1, y)
            if s and n:
                paint(out, fam, P, x, y, 0x29B, 'hedge', PEN)                 # a side, mid run
            elif n:
                paint(out, fam, P, x, y, 0x29C, 'hedge', PEN)                 # a side's south end
            elif s:
                # the back's corner: the top's rounded end over the side's start, one cell deep
                a, b = (0x290, 0x293) if e or not w else (0x292, 0x295)
                paint(out, fam, P, x, y, a, 'hedge', PEN, top, bot)
                paint(out, fam, P, x, y, b, 'hedge', PEN, bot, bot)
            else:
                a = 0x291 if (w or not hd(x - 1, y)) and e else 0x291
                paint(out, fam, P, x, y, a, 'hedge', PEN, top, bot)           # the back: the hedge's top
                paint(out, fam, P, x, y, 0x294, 'hedge', PEN, bot, bot)       # over its front face

# ------------------------------------------------------------------ fences
def fences(out, fam, P, g):
    fx = lambda x, y: 0 <= x < W and 0 <= y < H and g[y][x] in 'xp' or (0 <= x < W and 0 <= y < H and g[y][x] == 'i' and
                                                                       (at(x - 1, y) == 'x' or at(x + 1, y) == 'x'))
    at = lambda x, y: g[y][x] if 0 <= x < W and 0 <= y < H else ' '
    side = {}
    for x in range(W):                                     # a column's rail stands on the side its enclosure is on
        y = 0
        while y < H:
            if at(x, y) == 'x' and at(x, y + 1) in ('x', 'i') and at(x, y - 1) not in ('x', 'i'):
                y1 = y
                while at(x, y1 + 1) in ('x', 'i'):
                    y1 += 1
                east = any(at(x + 1, yy) == 'x' for yy in (y, y1))
                west = any(at(x - 1, yy) == 'x' for yy in (y, y1))
                s = 'L' if east and not west else 'R'
                for yy in range(y, y1 + 1):
                    side[(x, yy)] = s
                y = y1
            y += 1
    for y in range(H):
        for x in range(W):
            if not fx(x, y):
                continue
            n, s = (x, y - 1) in side and (x, y) in side, (x, y + 1) in side and (x, y) in side
            e, w = fx(x + 1, y) and at(x + 1, y) != 'p' or at(x + 1, y) == 'p' == at(x, y), fx(x - 1, y)
            if (x, y) in side and not (n and s) and (e or w) and (n or s) and not (e and w):
                m = {(False, True, True): 0xEC, (False, True, False): 0x337, (True, False, True): 0xFC, (True, False, False): 0xFD}[(n, s, e)]
            elif (x, y) in side and not (e or w):
                m = 0xF4 if side[(x, y)] == 'L' else 0xF5
            else:
                m = 0x336
            paint(out, fam, P, x, y, m, 'fence', FENCE)

# ------------------------------------------------------------------ pen beds
SOIL_PENS = ((36, 39, 23, 25), (40, 44, 29, 30))            # x0, x1, y0, y1: the planted beds in their plank frame
FLOWER_PENS = ((22, 25, 23, 25), (44, 48, 23, 25))          # the dark beds of orange and white flowers

def beds(out, fam, P, g, flowers, pick):
    tex = P.tex
    plank, soil = tex['f_dodai'][..., :3], tex['f_dodai_a'][..., :3]
    for x0, x1, y0, y1 in SOIL_PENS:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                d = out[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
                d[:] = soil[(np.arange(16) + y * 16) % soil.shape[0]][:, (np.arange(16) + x * 16) % soil.shape[1]]
                if x == x0: d[:, :4] = plank[:, :4]
                if x == x1: d[:, 12:] = plank[:, 12:]
                if y == y0: d[:4, :] = plank[:, :4].transpose(1, 0, 2)
                if y == y1: d[12:, :] = plank[:, 12:].transpose(1, 0, 2)
                f = flowers[2]
                a = f[..., 3] > 0
                d[a] = f[..., :3][a]
                fam[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = FENCE     # soil, planks and pink petals sit with the signs' browns and the lamps' pinks
    for x0, x1, y0, y1 in FLOWER_PENS:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                d = out[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
                d[:] = BED
                f = flowers[pick(x, y)]
                a = f[..., 3] > 0
                d[a] = f[..., :3][a]
                fam[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = GROUND    # the lawn's own flowers

def terrain(out, fam, P, g, flowers, pick):
    g = [list(r) for r in g]
    for x in range(40, 45):                                # the short pen's third row is its front rail in HGSS
        g[31][x] = 'p'
    g = [''.join(r) for r in g]
    beds(out, fam, P, g, flowers, pick)
    ponds(out, fam, P, g)
    rock(out, fam, P, g)
    ledges(out, fam, P, g)
    hedges(out, fam, P, g)
    fences(out, fam, P, g)
