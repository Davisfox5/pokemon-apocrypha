"""Celadon's grass, trees, flowers and grass edges, round 6: taken as they are from the games.

The owner on round 5's trees and flowers: "you've kind of custom designed some trees, and I
don't think that they work ... it's fine to use all the trees from those regions ... a
collection of the different regions' nature"; the flowers "look so two-dimensional. Try to use
flowers that are actually in these games"; and the joins between grass, flowers, dirt, stone
and street must be smooth, not hard lines.

    grass           FireRed's grass (general_frlg 0x001) and its two tufted cells (0x008,
                    0x009), Kanto's own ground
    edge pieces     FireRed's dirt path (general_frlg 0x0D0-0x0E2 and its inner corners 0x106,
                    0x107, as Viridian Forest lays them): every cell that is not grass but
                    touches grass takes, quadrant by quadrant, the path piece's grass and its
                    light rim over its own ground, so dirt, paving, brick and the pond's
                    coping all meet the grass the way Viridian Forest's paths do
    trees           the repo's own cut-out trees (TREE_ART): Cherrygrove's, the lighter Johto
                    crown, Sandgem's cone tree, Floccesy's great trees in sun and shade; whole
                    crowns on clear backgrounds (round 6's tileset cuts lost leaves to the key)
    flowers         Kanto's red flowers (FireRed 0x004) and Hoenn's (Emerald 0x004), each also
                    in Gen 3's other flower colours (yellow, white, blue, pink: the same art,
                    the petals' ramp swapped); HGSS's flat flower textures stay out
"""
from __future__ import annotations
import functools
from pathlib import Path
import numpy as np

import common as C
import metatiles as MT

E = Path('/home/user/pokeemerald-expansion/data/tilesets')

@functools.lru_cache(maxsize=None)
def tileset(prim, sec, frlg):
    return MT.Tileset(E / prim, E / sec, None, *((640, 7, 640) if frlg else (512, 6, 512)))

FR = ('primary/general_frlg', 'secondary/pallet_town_frlg', True)
VF = ('primary/general_frlg', 'secondary/viridian_forest_frlg', True)
EM = ('primary/general', 'secondary/petalburg', False)
FO = ('primary/general', 'secondary/fortree', False)

def meta(ts, m):
    return tileset(*ts).meta(m)

def block(ts, grid):
    return np.concatenate([np.concatenate([meta(ts, m) for m in row], 1) for row in grid], 0)

def keyed(ts, grid, ground):
    """The block with every pixel of its ground's colours made clear."""
    img = block(ts, grid)
    cols = set()
    for g in ground:
        cols |= {tuple(int(v) for v in c) for c in meta(ts, g)[..., :3].reshape(-1, 3)}
    key = np.array([tuple(int(v) for v in c) in cols for c in img[..., :3].reshape(-1, 3)]).reshape(img.shape[:2])
    img[key, 3] = 0
    return img

# --------------------------------------------------------------------------- grass
def grass():
    return [meta(FR, 0x001)[..., :3], meta(FR, 0x008)[..., :3], meta(FR, 0x009)[..., :3]]

# --------------------------------------------------------------------------- edges
PATH = dict(tl=0xD0, t=0xD1, tr=0xD2, l=0xD8, c=0xD9, r=0xDA, bl=0xE0, b=0xE1, br=0xE2, in_br=0x107, in_bl=0x106)

@functools.lru_cache(maxsize=None)
def path_pieces():
    p = {k: meta(FR, m)[..., :3] for k, m in PATH.items()}
    p['in_tr'] = p['in_br'][::-1].copy()                     # FireRed has the lower inner corners; the upper are their mirror
    p['in_tl'] = p['in_bl'][::-1].copy()
    return p

@functools.lru_cache(maxsize=None)
def classes():
    """Per piece: 0 its own ground (dirt), 1 grass, 2 the grass's rim (the light and dark
    pixels where the grass laps over the ground)."""
    p = path_pieces()
    dirt = {tuple(int(v) for v in c) for c in p['c'].reshape(-1, 3)}
    gr = set()
    for g in grass():
        gr |= {tuple(int(v) for v in c) for c in g.reshape(-1, 3)}
    out = {}
    for k, img in p.items():
        cl = np.full(img.shape[:2], 2, np.uint8)
        for y in range(16):
            for x in range(16):
                c = tuple(int(v) for v in img[y, x])
                cl[y, x] = 0 if c in dirt and c not in gr else 1 if c in gr else 2
        out[k] = cl
    return out

def piece_for(inside, x, y, qx, qy):
    """Which path piece's quadrant a cell's quadrant takes. inside(x, y): the cell is ground
    (not grass); out of the map counts as ground."""
    dx, dy = (-1 if qx == 0 else 1), (-1 if qy == 0 else 1)
    h, v, d = inside(x + dx, y), inside(x, y + dy), inside(x + dx, y + dy)
    if h and v and d:
        return 'c'
    if h and v:
        return {(-1, -1): 'in_tl', (1, -1): 'in_tr', (-1, 1): 'in_bl', (1, 1): 'in_br'}[(dx, dy)]
    if h:
        return 't' if dy < 0 else 'b'
    if v:
        return 'l' if dx < 0 else 'r'
    return {(-1, -1): 'tl', (1, -1): 'tr', (-1, 1): 'bl', (1, 1): 'br'}[(dx, dy)]

def grass_edges(out, ground, grass_px, texture=None):
    """Lay the grass over the edge of every ground cell (ground: H x W bool) that touches
    grass, quadrant by quadrant from FireRed's path pieces: their grass pixels from grass_px
    (the map's grass picture), their rim pixels as FireRed draws them. With texture (a picture
    the size of the map) the ground pixels take it (the dirt path itself)."""
    H, W = ground.shape
    inside = lambda x, y: (not (0 <= x < W and 0 <= y < H)) or ground[y, x]
    pieces, cls = path_pieces(), classes()
    for y in range(H):
        for x in range(W):
            if not ground[y, x]:
                continue
            for qy in (0, 1):
                for qx in (0, 1):
                    k = piece_for(inside, x, y, qx, qy)
                    sl = (slice(y * 16 + qy * 8, y * 16 + qy * 8 + 8), slice(x * 16 + qx * 8, x * 16 + qx * 8 + 8))
                    ps = (slice(qy * 8, qy * 8 + 8), slice(qx * 8, qx * 8 + 8))
                    cl = cls[k][ps]
                    if texture is not None:
                        out[sl][cl == 0] = texture[sl][cl == 0]
                    if k == 'c':
                        continue
                    out[sl][cl == 1] = grass_px[sl][cl == 1]
                    out[sl][cl == 2] = pieces[k][ps][cl == 2]

def dirt_texture(H, W):
    """FireRed's dirt (the path's centre piece) over the whole map."""
    c = path_pieces()['c']
    return np.tile(c, (H, W, 1))

# --------------------------------------------------------------------------- trees
# The owner, round 6: "so many trees are either cut off or cut off something ... There are
# already trees with transparent backgrounds in the repo, so use those." Trees cut from a
# tileset by keying out its grass lose every leaf that shares a grass colour and keep the
# shadow squares of the cells round them, so Celadon's trees are the repo's own cut-outs:
# whole crowns on clear backgrounds, already shown to the owner in other towns.
TREE_ART = dict(
    johto=('gba/art/cherrygrove-synthesis/refined/tree.png', "Cherrygrove's tree (HGSS's own, cropped whole from its render)"),
    johto_light=('gba/art/johto-restart/native/tree.png', 'the Johto restart tree, a lighter crown'),
    sinnoh=('gba/art/sandgem-v1/native/tree.png', "Sandgem's cone tree"),
    grove_sun=('gba/art/floccesy-v4/native/tree-sun.png', "Floccesy's great tree in sunlit greens"),
    grove_shade=('gba/art/floccesy-v4/native/tree-shade.png', "Floccesy's great tree in shaded greens"),
)

def trees():
    from PIL import Image
    out = {}
    for k, (path, _) in TREE_ART.items():
        a = np.array(Image.open(C.ROOT / path).convert('RGBA'))
        a[..., 3] = np.where(a[..., 3] >= 128, 255, 0)
        out[k] = a
    return out

# --------------------------------------------------------------------------- flowers
PETALS = dict(yellow=[(255, 247, 140), (247, 214, 57), (206, 165, 16)], white=[(255, 255, 255), (231, 231, 239), (181, 181, 198)],
              blue=[(165, 206, 255), (99, 156, 247), (66, 99, 206)], pink=[(255, 206, 231), (247, 140, 198), (214, 82, 156)])

def petal_swap(img, ramp):
    """The flower with its petals (its reds and oranges) put on another Gen 3 flower ramp,
    shade for shade."""
    out = img.copy()
    rgb = img[..., :3].astype(int)
    a = img[..., 3] > 0
    petal = a & (rgb[..., 0] > rgb[..., 1] + 40) & (rgb[..., 0] > 120)
    cols = sorted({tuple(c) for c in rgb[petal]}, key=lambda c: -(3 * c[0] + 4 * c[1] + 2 * c[2]))
    for i, c in enumerate(cols):
        m = petal & np.all(rgb == c, -1)
        out[m, :3] = ramp[min(i * len(ramp) // max(1, len(cols)), len(ramp) - 1)]
    return out

def flowers():
    fr = keyed(FR, [[0x004]], [0x001])
    em = keyed(EM, [[0x004]], [0x001])
    out = dict(kanto_red=fr, hoenn_red=em)
    for name, ramp in PETALS.items():
        out['kanto_' + name] = petal_swap(fr, ramp)
        out['hoenn_' + name] = petal_swap(em, ramp)
    return out
