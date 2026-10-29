"""Violet City's elements, cleaned up to AGENTS.md's native visual rules on the town's two whole-map layers.

The canvas holds every cell's lower and upper layer as the base draws them (base.py); each element redraws
pixels of one kind and marks its cells. Pixels an element does not own (buildings, signs, lanterns, trees,
fences) keep their colours exactly.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent)]
import base as B                                     # noqa: E402
from claude_cherrygrove import ground as G           # noqa: E402

W, H = B.W, B.H

class Canvas:
    def __init__(self, v):
        self.v = v
        self.lower = np.zeros((H * 16, W * 16, 3), np.uint8)
        self.upper = np.zeros((H * 16, W * 16, 4), np.uint8)
        self.attr = np.zeros((H, W), np.int64)
        self.bits = np.zeros((H, W), np.int64)
        self.prefer = {}
        for r in range(H):
            for x in range(W):
                w = int(v.words[r, x]); m = w & 1023
                low, up = v.layers(m)
                self.lower[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16] = low
                self.upper[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16] = up
                self.attr[r, x] = v.attr(m); self.bits[r, x] = w & 0xFC00
                self.prefer[(x, r)] = [[e >> 12] for e in v.block(m)]
        self.changed = set()
        self.notes = []
    def sl(self, x, r):
        return np.s_[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16]
    def image(self):
        out = self.lower.copy(); a = self.upper[..., 3] > 0; out[a] = self.upper[..., :3][a]
        return out
    def cells(self):
        out = {}
        for r in range(H):
            for x in range(W):
                sl = self.sl(x, r)
                prefer = self.prefer[(x, r)] if (x, r) not in self.changed else [[]] * 8
                out[(x, r)] = (self.lower[sl], self.upper[sl], int(self.attr[r, x]), int(self.bits[r, x]), prefer)
        return out

def keyset(a):
    return {tuple(int(v) for v in c) for c in np.asarray(a).reshape(-1, 3)}

def tonemask(img, tones):
    """Pixels whose colour is one of tones."""
    t = np.array(sorted(tones), np.int64)
    k = (img[..., 0].astype(np.int64) << 16) | (img[..., 1].astype(np.int64) << 8) | img[..., 2]
    return np.isin(k, (t[:, 0] << 16) | (t[:, 1] << 8) | t[:, 2])

def disk(r):
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    return xx * xx + yy * yy <= r * r

# --------------------------------------------------------------------------- the cobbled streets
# Violet's streets are cobble (its own 32 px texture) cut square against the lawn with a 1 px tan line.
# HGSS runs a dirt verge between cobble and lawn and rounds every corner. Here the verge is the Johto port's
# own dirt tones (the ground painter's sand and its rim, as Cherrygrove's and Routes 30-31's roads), flat,
# in the street's outer VERGE px, so a straight run is one tile in any flip and the tile budget holds; the
# corners round off. Against buildings, bridges, signs and lanterns the cobble runs right up to them.
COBBLE_CELL = (20, 44)                               # a cell of pure cobble: the texture's source
VERGE = 8                                            # px of sand between the cobble and the lawn
VERGE_PROFILE = [(128, 136, 120), (184, 168, 128), (216, 184, 128), (216, 184, 128), (224, 200, 128),
                 (216, 184, 128), (184, 168, 128), (152, 144, 112)]   # from the lawn in: its shade line, the sand, the dark line on the cobble
ROUND = 3                                            # corner radius, px
LAWN_FLAT = (104, 208, 152)                          # the lawn's main tone

def cobble_texture(img):
    x, r = COBBLE_CELL
    tex = np.zeros((32, 32, 3), np.uint8)
    y0, x0 = (r * 16) - (r * 16) % 32, (x * 16) - (x * 16) % 32
    tex[:] = img[y0:y0 + 32, x0:x0 + 32]
    return tex

def paths(cv):
    from scipy.ndimage import binary_closing, binary_opening, distance_transform_edt
    img = cv.image()
    cob = cobble_texture(img)
    lawn, sand = G.textures()[G.GRASS], G.textures()[G.PATH].copy()
    sand[(sand == (216, 168, 128)).all(-1)] = (216, 184, 128)   # as Cherrygrove: the darkest pebbles are the next tone
    h, w = img.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w]
    is_cob = (img == cob[ys % 32, xs % 32]).all(-1) & tonemask(img, keyset(cob))
    is_lawn = (img == lawn[ys % 32, xs % 32]).all(-1)
    # the old outline: non-cobble, non-lawn pixels squeezed between the two
    near_cob = distance_transform_edt(~is_cob) <= 2
    near_lawn = distance_transform_edt(~is_lawn) <= 2
    outline = ~is_cob & ~is_lawn & near_cob & near_lawn & ~tonemask(img, keyset(cob)) & tonemask(img, edge_tones(img, is_cob, is_lawn))
    ground = is_cob | is_lawn | outline
    street_px = is_cob | outline
    # the street's shape by cells (a building's footprint must not cut it up): a cell is street where its
    # ground is mostly cobble; a cell its art covers whole goes with the street when one touches it
    cob_n = street_px.reshape(H, 16, W, 16).sum((1, 3)); lawn_n = is_lawn.reshape(H, 16, W, 16).sum((1, 3))
    street = cob_n > lawn_n
    covered = (cob_n + lawn_n) == 0
    touch = np.zeros_like(street)
    touch[1:] |= street[:-1]; touch[:-1] |= street[1:]; touch[:, 1:] |= street[:, :-1]; touch[:, :-1] |= street[:, 1:]
    street |= covered & touch
    p = np.repeat(np.repeat(street, 16, 0), 16, 1)
    pad = 2 * ROUND
    p = np.pad(p, pad, mode='edge')
    p = binary_opening(binary_closing(p, disk(ROUND)), disk(ROUND))[pad:-pad, pad:-pad]
    lawn_px = ground & ~p
    d_lawn = distance_transform_edt(~(lawn_px & (is_lawn | outline)))   # into the street from the lawn
    # the verge: flat tones by depth, inside the street's outer quadrant, so a straight run draws one tile
    new = np.where(lawn_px[..., None], lawn[ys % 32, xs % 32], img)
    cut = lawn_px & np.repeat(np.repeat(street, 16, 0), 16, 1)   # a street cell's corner the rounding gave back to the lawn
    new[cut] = LAWN_FLAT                             # in the lawn's own flat tone: one corner tile at any position
    inner = p & (d_lawn > VERGE)
    new[inner] = cob[ys % 32, xs % 32][inner]
    depth = np.clip(np.ceil(d_lawn).astype(int) - 1, 0, VERGE - 1)
    prof = np.array(VERGE_PROFILE, np.uint8)
    verge = p & ~inner
    new[verge] = prof[depth[verge]]
    change = ground & (new != img).any(-1)
    cells = {(int(x) // 16, int(y) // 16) for y, x in zip(*np.nonzero(change))}
    cellmask = np.zeros((H, W), bool)
    for x, r in cells:
        cellmask[r, x] = True
    own = ground & np.repeat(np.repeat(cellmask, 16, 0), 16, 1)
    cv.lower[own] = new[own]
    cv.upper[own, 3] = 0                             # every ground pixel of a redrawn cell draws below (the street was partly an upper layer)
    cv.changed |= cells
    cv.notes.append(f'paths: cobble with a {VERGE} px sand verge in {len(cells)} cells, corners rounded {ROUND} px')

def edge_tones(img, is_cob, is_lawn):
    """The old outline's tones: colours drawn only right between cobble and lawn."""
    from scipy.ndimage import distance_transform_edt
    between = (distance_transform_edt(~is_cob) <= 2) & (distance_transform_edt(~is_lawn) <= 2) & ~is_cob & ~is_lawn
    import collections
    inside = collections.Counter(tuple(int(v) for v in c) for c in img[between])
    everywhere = collections.Counter(tuple(int(v) for v in c) for c in img[~is_cob & ~is_lawn])
    return {c for c, n in inside.items() if n >= 0.8 * everywhere[c]}

def inner_edge(inner, verge):
    p = np.pad(inner, 1)
    n = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    return verge & n

# --------------------------------------------------------------------------- the lake's north bank
# HGSS's Violet lake drops from the lawn to the water by an earth bank on its north sides: a light face
# with toothed streaks over a darker foot, a deeper blue just below it. Violet's lake had a 1 px line. The
# bank is HGSS's own (source/hgss/lake-bank.png, 16 px repeat, cut from the HGSS render): its light rows
# on the lawn's last pixels, its dark rows over the water's first, then the deeper blue.
BANK_TEX = B.ART / 'source/hgss/lake-bank.png'
BANK_LIGHT = 6                                       # the bank's rows on the lawn side
WATER_MB = 0x10
DEEP = (40, 152, 208)                                # the shadowed water under the bank
DEEP_ROWS = 2

def lake_bank(cv):
    from PIL import Image
    tex = np.array(Image.open(BANK_TEX).convert('RGB'))
    rows = tex.shape[0]
    img = cv.image()
    water_cell = (cv.attr & 0xFF) == WATER_MB
    water_t = {tuple(int(v) for v in c) for c in img[np.repeat(np.repeat(water_cell, 16, 0), 16, 1)]}
    water_t = {c for c in water_t if c[2] > 180 and c[2] > c[0] + 80}       # the lake's blues
    is_water = tonemask(img, water_t) & np.repeat(np.repeat(water_cell, 16, 0), 16, 1)
    lawn = G.textures()[G.GRASS]
    ys, xs = np.mgrid[0:H * 16, 0:W * 16]
    is_lawn = (img == lawn[ys % 32, xs % 32]).all(-1)
    tex[(tex == (57, 154, 243)).all(-1)] = DEEP       # the strip's last row is HGSS's water: the deep blue here
    painted = 0
    cells = set()
    for xp in range(W * 16):
        col = is_water[:, xp]
        for y in range(1, H * 16):
            if not (col[y] and not col[y - 1]):
                continue
            if not is_lawn[max(0, y - 5):y, xp].any():
                continue                             # only where the lawn is above the water (not the landing, the islet)
            for k in range(rows + DEEP_ROWS):
                yy = y - BANK_LIGHT + k
                if not 0 <= yy < H * 16:
                    continue
                if k < BANK_LIGHT and is_water[yy, xp]:
                    continue
                if k >= BANK_LIGHT and not is_water[yy, xp]:
                    break
                if cv.upper[yy, xp, 3]:
                    continue                         # an object above the lawn's edge stays
                c = tex[k, xp % 16] if k < rows else DEEP
                cv.upper[yy, xp, :3] = c; cv.upper[yy, xp, 3] = 255   # on the upper layer (drawn below the player), the ground below kept
                cells.add((xp // 16, yy // 16)); painted += 1
    cv.changed |= cells
    cv.notes.append(f'lake: HGSS earth bank on the north edges, {painted} pixels in {len(cells)} cells')

# --------------------------------------------------------------------------- the lake's landing
# Violet's central landing is HGSS's own size and place (x31-42, rows 23-28). It was a flat grey slab with a
# 1 px outline. It takes HGSS's: a 12 px border of stone blocks round a dotted floor (source/hgss/landing.png,
# HGSS's ground layer with 8 px of lake round it, every part repeating every 16 px), and the deeper blue
# ring HGSS draws in the water round it. The walkways stay open where the bridges land; the lanterns stay.
LANDING_TEX = B.ART / 'source/hgss/landing.png'
LANDING = (31, 23, 12, 6)                            # x, row, width, height in cells
RING = 8                                             # px of lake round it in the texture
LANDING_TONES = {(144, 144, 160), (136, 136, 144), (152, 160, 168), (112, 112, 144)}
WALKWAY = (38, 41)                                   # the bridges' walkable columns (x38-40)
HGSS_RING = {(57, 154, 243), (57, 144, 240), (57, 167, 247)}
LANTERNS = [(37, 24), (37, 25), (40, 24), (40, 25)]
# HGSS's greys onto the grey ramp Violet's landing, bridges and street already draw in (bank 11), in rank
# order, HGSS's floor tone on Violet's: the shapes are HGSS's, the colours the town's
LANDING_SNAP = {(107, 107, 123): (96, 104, 120), (115, 115, 132): (104, 104, 136), (123, 123, 140): (112, 112, 144),
                (140, 140, 156): (120, 120, 152), (148, 148, 165): (136, 136, 144), (156, 156, 173): (144, 144, 160),
                (165, 165, 181): (152, 160, 168), (82, 148, 214): (96, 104, 120), (90, 140, 189): (96, 104, 120),
                (107, 123, 156): (96, 104, 120)}

def landing_art():
    from PIL import Image
    t = np.array(Image.open(LANDING_TEX).convert('RGB'))
    L = t[RING:-RING, RING:-RING]                    # 96 x 192
    h, w = L.shape[:2]
    out = np.zeros_like(L)
    for v in range(h):
        for u in range(w):
            top, bot, lef, rig = v < 16, v >= h - 16, u < 16, u >= w - 16
            if (top or bot) and (lef or rig):
                out[v, u] = L[v, u]                  # the corners as HGSS has them
            elif top or bot:
                out[v, u] = L[v, 16 + (u - 16) % 16]
            elif lef or rig:
                out[v, u] = L[16 + (v - 16) % 16, u]
            else:
                out[v, u] = L[16 + (v - 16) % 16, 16 + (u - 16) % 16]
    hw, hh = w // 2, h // 2                          # mirrored from its north-west quarter: its tiles serve all four in a flip
    out[:, hw:] = out[:, :hw][:, ::-1]
    out[hh:] = out[:hh][::-1]
    x0, r0, cw, ch = LANDING
    for u in range((WALKWAY[0] - x0) * 16, (WALKWAY[1] - x0) * 16):   # the walkways open onto the floor
        for v in list(range(16)) + list(range(h - 16, h)):
            out[v, u] = L[16 + (v - 16) % 16, 16 + (u - 16) % 16]
    ring = np.array([[tuple(int(c) for c in p) in HGSS_RING for p in row] for row in t])
    rh, rw = ring.shape[0] // 2, ring.shape[1] // 2
    ring[:, rw:] = ring[:, :rw][:, ::-1]
    ring[rh:] = ring[:rh][::-1]
    for c, to in LANDING_SNAP.items():
        out[(out == c).all(-1)] = to
    return out, ring

def landing(cv):
    art, ring = landing_art()
    x0, r0, cw, ch = LANDING
    X, Y = x0 * 16, r0 * 16
    img = cv.image()
    up = cv.upper[Y:Y + ch * 16, X:X + cw * 16]
    lantern = np.zeros(up.shape[:2], bool)
    for x, r in LANTERNS:
        lantern[(r - r0) * 16:(r - r0 + 1) * 16, (x - x0) * 16:(x - x0 + 1) * 16] = True
    keep = (up[..., 3] > 0) & lantern & ~tonemask(up[..., :3], LANDING_TONES)   # the lanterns (the bridge deck's run across goes)
    low = cv.lower[Y:Y + ch * 16, X:X + cw * 16]
    low[~keep] = art[~keep]
    up[~keep, 3] = 0
    # the deeper blue round it, on the lake's own water pixels
    water_cell = (cv.attr & 0xFF) == WATER_MB
    Ye, Xe = Y - RING, X - RING
    sub = cv.lower[Ye:Ye + ring.shape[0], Xe:Xe + ring.shape[1]]
    subu = cv.upper[Ye:Ye + ring.shape[0], Xe:Xe + ring.shape[1]]
    comp = img[Ye:Ye + ring.shape[0], Xe:Xe + ring.shape[1]]
    wc = np.repeat(np.repeat(water_cell, 16, 0), 16, 1)[Ye:Ye + ring.shape[0], Xe:Xe + ring.shape[1]]
    blue = (comp[..., 2] > 180) & (comp[..., 2] > comp[..., 0].astype(int) + 80)
    put = ring & wc & blue & (subu[..., 3] == 0)
    subu[put, :3] = DEEP; subu[put, 3] = 255          # over the water, which keeps its tiles
    cells = {(x, r) for r in range(r0 - 1, r0 + ch + 1) for x in range(x0 - 1, x0 + cw + 1)}
    cv.changed |= cells
    cv.notes.append(f'landing: HGSS stone border and floor, the deeper ring round it ({int(put.sum())} px)')

# --------------------------------------------------------------------------- the lake's islet
# The islet east of the landing (x47-50, rows 22-26) carried its tree on a teal top that read as a pool of
# water inside it. Its top is grass: each teal tone takes the green of its own depth from the islet's own
# palette (bank 2, which the west gatehouse's teal shares, so the slots stay), the earth sides and the tree
# stay.
ISLET = (range(47, 51), range(22, 27))
ISLET_TOP = {(120, 208, 176): (120, 168, 40), (72, 176, 168): (120, 168, 40), (48, 160, 152): (96, 128, 32),
             (40, 144, 136): (96, 128, 32), (40, 112, 104): (80, 96, 48)}

def islet(cv):
    n = 0
    for r in ISLET[1]:
        for x in ISLET[0]:
            sl = cv.sl(x, r)
            for layer in (cv.lower[sl], cv.upper[sl]):
                for a, b in ISLET_TOP.items():
                    m = (layer[..., :3] == a).all(-1)
                    if layer.shape[-1] == 4:
                        m &= layer[..., 3] > 0
                    if m.any():
                        layer[..., :3][m] = b; n += int(m.sum()); cv.changed.add((x, r))
    cv.notes.append(f'islet: its teal top grass ({n} px)')

# --------------------------------------------------------------------------- one layer where two are not needed
def flatten(cv):
    """In cells whose two layers both draw below the player (layer type covered), a quadrant whose picture one
    bank can draw takes one tile on the lower layer instead of two: the same pixels, fewer tiles."""
    b5 = [{tuple(int(x) >> 3 for x in c) for c in b[1:]} for b in cv.v.banks]
    n = 0
    for r in range(H):
        for x in range(W):
            if (int(cv.attr[r, x]) >> 12) & 3 != B.COVERED:
                continue
            for q in range(4):
                y0, x0 = r * 16 + (q // 2) * 8, x * 16 + (q % 2) * 8
                up = cv.upper[y0:y0 + 8, x0:x0 + 8]
                a = up[..., 3] > 0
                if not a.any():
                    continue
                low = cv.lower[y0:y0 + 8, x0:x0 + 8]
                comp = low.copy(); comp[a] = up[..., :3][a]
                cols = {tuple(int(v) >> 3 for v in c) for c in comp.reshape(-1, 3)} - {tuple(int(v) >> 3 for v in cv.v.backdrop)}
                if any(cols <= b for b in b5):
                    low[:] = comp; up[..., 3] = 0; n += 1
    cv.notes.append(f'{n} two-layer quadrants drawn as one')
