"""Pixel-level ground painter in the HGSS render's colours.

The map composer hands over a cell grid of materials (grass, path, sand, sea). Each
material is filled with its rendered texture (sampled by absolute pixel position so
tiles repeat and dedupe), then every boundary between two materials is softened with
the colour profile measured on the HGSS render: the mossy shadow rim where grass
meets a sand path, the pale wet rim where the beach meets grass, and the foam and
shallow-blue gradient where sand or cliff meets the sea. Boundaries wobble with a
32 px wave so straight runs still pack into a handful of tiles.
"""
from __future__ import annotations
import numpy as np
from . import hgss

GRASS, PATH, SAND, SEA, ROCK = 0, 1, 2, 3, 4   # ROCK = cliff foot / rock base, no rim of its own

# Rim profiles: (material A, material B) -> (A-side colours from the boundary outward, B-side colours).
PROFILES = {
    (GRASS, PATH): ([(128, 136, 120), (88, 176, 136), (88, 176, 136), (88, 176, 136), (96, 192, 144)],
                    [(152, 144, 112), (184, 168, 128), (184, 168, 128), (216, 184, 128)]),
    (GRASS, SAND): ([(168, 216, 152)],
                    [(208, 208, 168), (208, 208, 168), (208, 208, 168), (208, 208, 168), (216, 216, 176)]),
    (SAND, SEA): ([(200, 192, 144), (200, 192, 144), (208, 208, 168), (216, 216, 176), (216, 216, 176), (216, 216, 176)],
                  [(200, 232, 224), (200, 232, 224), (200, 232, 224), (200, 232, 224), (152, 224, 224), (104, 192, 224), (72, 160, 224), (40, 128, 224)]),
    (ROCK, SEA): ([], [(192, 216, 224), (192, 216, 224), (192, 216, 224)]),
    (GRASS, SEA): ([(88, 176, 136), (88, 176, 136)], [(192, 216, 224), (192, 216, 224), (152, 224, 224), (104, 192, 224)]),
    (PATH, SAND): ([], []),
    (PATH, SEA): ([(200, 192, 144), (200, 192, 144)], [(200, 232, 224), (200, 232, 224), (200, 232, 224), (152, 224, 224), (104, 192, 224), (72, 160, 224)]),
}

WAVE = [0, 0, 1, 1, 1, 2, 2, 2, 2, 2, 1, 1, 1, 0, 0, 0, 0, -1, -1, -1, -2, -2, -2, -2, -2, -1, -1, -1, 0, 0, 0, 0]   # 32 px

def textures():
    """Base textures per material, as RGB arrays sampled by absolute pixel position."""
    grass = np.zeros((32, 32, 3), np.uint8); grass[...] = hgss.GRASS
    for (x, y) in ((3, 2), (19, 6), (11, 13), (27, 17), (6, 24), (22, 28), (14, 21), (30, 9)): grass[y, x] = hgss.GRASS_SPECK
    path = np.zeros((32, 32, 3), np.uint8); path[...] = hgss.PATH
    for (x, y, c) in ((2, 3, hgss.PATH_SPECK), (9, 1, hgss.PATH_SPECK2), (13, 8, hgss.PATH_SPECK), (5, 12, hgss.PATH_SPECK2), (11, 14, hgss.PATH_SPECK),
                      (20, 19, hgss.PATH_SPECK), (27, 24, hgss.PATH_SPECK2), (17, 29, hgss.PATH_SPECK), (24, 6, hgss.PATH_SPECK2), (30, 15, hgss.PATH_SPECK)): path[y, x] = c
    sand = hgss.px(392, 148, 32, 32)[..., :3]
    sea = hgss.sea()[..., :3]
    rock = np.zeros((32, 32, 3), np.uint8); rock[...] = (152, 104, 88)
    return {GRASS: grass, PATH: path, SAND: sand, SEA: sea, ROCK: rock}

def _chamfer(mask, limit=9):
    """Distance (in pixels, 4-connected) from every pixel to the nearest True pixel, capped at limit."""
    d = np.where(mask, 0, limit).astype(np.int16)
    for _ in range(limit):
        n = d.copy()
        n[1:, :] = np.minimum(n[1:, :], d[:-1, :] + 1); n[:-1, :] = np.minimum(n[:-1, :], d[1:, :] + 1)
        n[:, 1:] = np.minimum(n[:, 1:], d[:, :-1] + 1); n[:, :-1] = np.minimum(n[:, :-1], d[:, 1:] + 1)
        if (n == d).all(): break
        d = n
    return d

def paint(cells, wobble=True):
    """cells: (H, W) int8 material grid -> (H*16, W*16, 4) RGBA ground image."""
    H, W = cells.shape; h, w = H * 16, W * 16
    tex = textures()
    # Per-pixel material with a wobbling boundary: sample the cell grid at a displaced position.
    ys, xs = np.mgrid[0:h, 0:w]
    if wobble:
        dx = np.array(WAVE)[ys % 32]; dy = np.array(WAVE)[(xs + 11) % 32]
    else:
        dx = dy = 0
    sx = np.clip(xs + dx, 0, w - 1) // 16; sy = np.clip(ys + dy, 0, h - 1) // 16
    mat = cells[sy, sx]
    # Sea and rock keep hard, unwobbled cell shapes where they meet each other (cliff foot is straight).
    out = np.zeros((h, w, 4), np.uint8); out[..., 3] = 255
    for m, t in tex.items():
        mm = mat == m
        out[..., :3][mm] = t[ys[mm] % t.shape[0], xs[mm] % t.shape[1]]
    # Rims.
    dist = {m: _chamfer(mat == m) for m in tex}
    order = [(GRASS, PATH), (GRASS, SAND), (PATH, SAND), (PATH, SEA), (GRASS, SEA), (SAND, SEA), (ROCK, SEA)]
    for (a, b) in order:
        pa, pb = PROFILES[(a, b)]
        if not (mat == a).any() or not (mat == b).any(): continue
        # A-side pixels near B
        for i, c in enumerate(pa):
            sel = (mat == a) & (dist[b] == i + 1); out[..., :3][sel] = c
        for i, c in enumerate(pb):
            sel = (mat == b) & (dist[a] == i + 1); out[..., :3][sel] = c
    return out, mat
