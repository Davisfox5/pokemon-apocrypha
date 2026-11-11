"""Celadon's trees and fence posts, from HGSS's own textures.

Tree: Celadon's tree is HGSS's tree01gs crown (a round olive crown, 42 x 41 px in its
texture) area-averaged to 32 px across and snapped back onto its own colours, so it fills
the two cells of HGSS's 2x2 tree block as Cherrygrove's tree does, with a dark outline
kept round it; under it HGSS's tree01_un (the trunk and its ring of shade seen from above)
squeezed into a 32 x 12 shadow, its lawn cleared, and the trunk's foot showing below the
crown. 32 x 48, the crown rising a row above the block. Its colours: nine for the crown (a k-means
of its own, the darkest its outline), two shades and three trunk browns.

Fence post: tama_f's grey post (its first 9 x 16 px, the post and its shadow), one to a
fence cell, standing at the cell's foot.
"""
from __future__ import annotations
import numpy as np
from PIL import Image

import common as C

TREE_W, TREE_H, CROWN_H, CROWN_Y = 32, 48, 32, 6
SHADOW_Y, SHADOW_H = 35, 13
OUTLINE = (74, 66, 57)              # the crown texture's own darkest brown
OUTLINE_SET = [OUTLINE]
TRUNK = [(148, 115, 74), (123, 99, 74), (82, 74, 66)]

def resample(a, w, h, pal, alpha=110):
    pm = (a[..., :3].astype(float) * (a[..., 3:] / 255)).astype(np.uint8)
    col = np.array(Image.fromarray(pm).resize((w, h), Image.Resampling.BOX)).astype(float)
    al = np.array(Image.fromarray(a[..., 3]).resize((w, h), Image.Resampling.BOX)).astype(float)
    rgb = col / np.maximum(al[..., None], 1) * 255
    p = np.array(pal, float)
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = np.array(pal, np.uint8)[((rgb[..., None, :] - p[None, None]) ** 2).sum(-1).argmin(-1)]
    out[..., 3] = np.where(al >= alpha, 255, 0)
    out[out[..., 3] == 0] = 0
    return out

def outline(img, c):
    a = img[..., 3] > 0
    pad = np.pad(a, 1)
    edge = a & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    img[edge, :3] = c

CROWN_COLOURS = 9
SHADE = [(57, 140, 115), (82, 181, 148)]                     # tree01_un's ring of shade, two of its shades

def tree(t):
    import build as B
    src = t['tree01gs'][16:57, 11:53]
    uc, cnt = np.unique(src[src[..., 3] > 0][:, :3] >> 3, axis=0, return_counts=True)
    pal = [tuple(int(v) << 3 | int(v) >> 2 for v in c) for c in B.kmeans_colors(uc, np.sqrt(cnt).astype(float), CROWN_COLOURS)]
    pal = [min(OUTLINE_SET, key=lambda o: sum((a - b) ** 2 for a, b in zip(o, c))) if sum(c) < 200 else c for c in pal]
    crown = resample(src, TREE_W, CROWN_H, pal)
    outline(crown, OUTLINE)
    un = t['tree01_un'].copy()
    lawn = np.abs(un[..., :3].astype(int) - [115, 222, 173]).sum(-1) < 24
    un[lawn] = 0
    spal = [tuple(int(v) for v in c) for c in np.unique(un[un[..., 3] > 0][:, :3], axis=0)]
    shadow = resample(un, TREE_W, SHADOW_H, spal, alpha=128)
    a = shadow[..., 3] > 0
    p = np.array(SHADE + TRUNK, int)
    shadow[a, :3] = p[((shadow[a, :3][:, None, :].astype(int) - p[None]) ** 2).sum(-1).argmin(-1)]
    img = np.zeros((TREE_H, TREE_W, 4), np.uint8)
    C.put(img, shadow, 0, SHADOW_Y)
    # the trunk's foot below the crown: 6 px across, lit on the left, outlined
    for yy in range(CROWN_Y + CROWN_H - 3, SHADOW_Y + 6):
        img[yy, 13:19, :3] = TRUNK[0]; img[yy, 13:19, 3] = 255
        img[yy, 17:19, :3] = TRUNK[1]
        img[yy, 12, :3] = img[yy, 19, :3] = TRUNK[2]; img[yy, 12, 3] = img[yy, 19, 3] = 255
    img[SHADOW_Y + 6, 12:20, :3] = TRUNK[2]; img[SHADOW_Y + 6, 12:20, 3] = 255
    C.put(img, crown, 0, CROWN_Y)
    return img

def post(t):
    import ground as G
    return G.snap(t['tama_f'][0:16, 0:9], G.GREYS)
