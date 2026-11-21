"""The approved Johto tall grass and pond borders (2026-11-21) as layer art for the route assemblers.

johto_tall_grass.restyle() and johto_pond.restyle() restyle an installed map's flattened image. A map that is
assembled from layers (route30_catalog, route31_catalog, route32_native, cherrygrove_town, violet_city) draws
the same art here instead, before it packs, so the packer builds the tiles and palettes:

  grass_art(cells)              RGBA over the whole map: the hand-drawn G3 tile in the tall-grass cells, the
                                patch corners rounded (opening, radius 7), a wavy 1-2 px dark edge on the sides
                                and bottom, blade tips on the top rows. Carved pixels are transparent, so the
                                ground the assembler already drew under the grass shows there (sand stays sand).
  pond_art(water, texture)      RGBA over the whole map for the pond cells (johto_pond.ponds() picks them):
                                Emerald's general-tileset pond set (b0 b1 b2 b8 ba c0 c2 a1) with its light water
                                replaced by the map's water texture and its shadow band by that water at 72%.
  pond_lip(water, ground, lawn) RGBA: the top two rows of Emerald metatile 0x2 on the land cell under each pond
                                cell, only over lawn-coloured ground pixels.

Both are the same pixels restyle() makes. AGENTS.md "Never draw over what is already there": the assembler
lays these in place of its old grass and water art, not on top of it.
"""
from __future__ import annotations
import os
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
PX = 16

def _tile():
    import johto_tall_grass as TG
    return TG.parse(TG.TILE).astype(np.uint8), np.array(TG.P['.']), np.array(TG.P['L'])

def _morph(m, r, op):
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dy * dy + dx * dx <= r * r + r * 0.5:
                sh = np.roll(np.roll(m, dy, 0), dx, 1)
                out = (out & sh) if op == 'erode' else (out | sh)
    return out

def grass_art(cells, R=7):
    """cells: H x W bool (tall-grass cells). Returns (H*16, W*16, 4) uint8."""
    tile, DARK, LIGHT = _tile()
    M = np.kron(cells.astype(bool), np.ones((PX, PX), bool))
    pad = 8
    Mp = np.pad(M, pad)
    Mr = _morph(_morph(Mp, R, 'erode'), R, 'dilate')[pad:-pad, pad:-pad]
    H, W = M.shape
    yy, xx = np.mgrid[0:H, 0:W]
    wave = ((xx // 4 + yy // 4) % 2).astype(bool)
    inner1 = _morph(np.pad(Mr, pad), 1, 'erode')[pad:-pad, pad:-pad]
    keep = np.where(wave, inner1, Mr)
    top = np.zeros((H, W), int); run = np.zeros(W, int)
    for y in range(H):
        run = np.where(M[y], run + 1, 0); top[y] = run
    tex = np.tile(tile, (H // PX, W // PX, 1))
    art = np.zeros((H, W, 4), np.uint8)
    art[keep, :3] = tex[keep]; art[keep, 3] = 255
    tips = (top <= 4) & (tex == DARK).all(-1)
    art[tips, 3] = 0
    ol = keep & ~inner1 & ~(top <= 4) & ~(tex == LIGHT).all(-1)
    art[ol, :3] = DARK; art[ol, 3] = 255
    art[~M] = 0
    return art

ENGINE = None          # the engine checkout the assembler runs on (its primary/general is Emerald's own)
_PIECES = None

def ponds(w, max_cells=400):
    """johto_pond.ponds(): water components that do not touch the map edge and have at most max_cells."""
    from scipy.ndimage import label
    lab, n = label(w)
    keep = np.zeros(w.shape, bool)
    H, W = w.shape
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if ys.min() > 0 and xs.min() > 0 and ys.max() < H - 1 and xs.max() < W - 1 and len(ys) <= max_cells:
            keep[ys, xs] = True
    return keep
def _pieces():
    global _PIECES
    if _PIECES is None:
        import map_gate as G
        b = Path(os.environ.get('EMERALD_ENGINE') or ENGINE) / 'data/tilesets'
        em = G._load_tileset(b / 'primary/general', b / 'secondary/petalburg')
        r = lambda i: np.asarray(em.render(i).convert('RGB')).astype(int)
        _PIECES = ({k: r(v) for k, v in dict(a1=0xa1, b0=0xb0, b1=0xb1, b2=0xb2, b8=0xb8, ba=0xba, c0=0xc0, c2=0xc2).items()},
                   r(0x2)[:2])
    return _PIECES

LIGHT_WATER, SHADOW = np.array((115, 189, 246)), np.array((74, 115, 172))

def piece_at(w, y, x):
    Hh, Ww = w.shape
    W_ = lambda yy, xx: (not (0 <= yy < Hh and 0 <= xx < Ww)) or w[yy, xx]
    n, wst, est = W_(y - 1, x), W_(y, x - 1), W_(y, x + 1)
    if not n:
        return 'b0' if not wst else 'b2' if not est else 'b1'
    if not wst: return 'b8'
    if not est: return 'ba'
    if not W_(y - 1, x - 1): return 'c0'
    if not W_(y - 1, x + 1): return 'c2'
    return 'a1'

def pond_art(w, texture, shade=0.72, shade_tones=None):
    """w: H x W bool pond cells; texture: (H*16, W*16, 3) the map's water at map phase. shade_tones: at most
    this many shadow-band tones (the darkest water tones' shades join their nearest kept one), for a map whose
    pond shares one bank with its lawn."""
    P, _ = _pieces()
    if shade_tones:
        cols = sorted({tuple(int(v) >> 3 for v in c) for c in texture.reshape(-1, 3)}, key=sum)
        keep = cols[len(cols) - shade_tones:]
        near = {c: min(keep, key=lambda k: sum(abs(a - b) for a, b in zip(c, k))) for c in cols}
        texture_sh = np.array([[[v << 3 for v in near[tuple(int(v) >> 3 for v in p)]] for p in row] for row in texture])
    else:
        texture_sh = texture
    Hh, Ww = w.shape
    art = np.zeros((Hh * PX, Ww * PX, 4), np.uint8)
    for y, x in zip(*np.nonzero(w)):
        sl = np.s_[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX]
        p = P[piece_at(w, y, x)]; wt = texture[sl][..., :3].astype(int)
        out = p.copy()
        mh = (p == LIGHT_WATER).all(-1); mg = (p == SHADOW).all(-1)
        ws = texture_sh[sl][..., :3].astype(int)
        out[mh] = wt[mh]; out[mg] = (ws[mg] * shade).astype(int)
        art[sl][..., :3] = np.clip(out, 0, 255); art[sl][..., 3] = 255
    return art

def pond_lip(w, ground, lawn):
    """The 2 px lip on each land cell under a pond cell, over the lawn colours `lawn` (a set of RGB) only."""
    _, LIP = _pieces()
    Hh, Ww = w.shape
    art = np.zeros((Hh * PX, Ww * PX, 4), np.uint8)
    for y, x in zip(*np.nonzero(w)):
        if y + 1 < Hh and not w[y + 1, x]:
            Y = (y + 1) * PX
            g = ground[Y:Y + 2, x * PX:(x + 1) * PX, :3]
            ok = np.array([[tuple(int(v) for v in p) in lawn for p in row] for row in g])
            seg = art[Y:Y + 2, x * PX:(x + 1) * PX]
            seg[ok, :3] = LIP[ok]; seg[ok, 3] = 255
    return art
