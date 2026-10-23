"""Cianwood's Gen 3 sprites, made from HGSS's own models and textures.

    python3 tools/gba/maps/cianwood_elements/sprites.py PATH/TO/pokeheartgold

Buildings and props (the houses 102 + door 103, the Pharmacy 104 and the photo studio 105
with its poster board, both with door 116, the Gym 108 + door 16, the herb racks 106 and
Cameron's camera 90) are
rendered with their own textures at C06's angle (hgss_camera.view: 38 degrees, 16 px per
tile up the screen, each squeezed across to fit its footprint as C06 is), then finished
as Gen 3 art: each group's own colours in 5-bit colour (14 for a building, the houses and
the Pharmacy sharing one palette), merged across groups where they agree within two levels,
C06's own outline colour round the silhouette, each roof mirrored on an 8 px axis so its
halves share tiles, and tiles that differ only by a one-pixel edge shift folded together. The sea rocks and small stones are HGSS's own textures
resampled; the sand tuft is drawn by hand in Cherrygrove's grass greens, the way Gen 3
draws plants (dark outline, light blade edges).

Writes source/elements/sprites/*.png (what elements.py places) and the contact sheet
source/elements/sprites.png. Each sprite's bottom edge is the bottom of its object's base
row.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = ROOT / 'gba/art/cianwood-elements/source/elements'
SPRITES = OUT / 'sprites'
sys.path.insert(0, str(HERE))

def canvas(w, h):
    return np.zeros((h, w, 4), np.uint8)

def outline(img, c):
    """One-pixel outline along the inside edge of the opaque area."""
    a = img[..., 3] > 0
    pad = np.pad(a, 1)
    edge = a & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    img[edge] = tuple(c) + (255,)

C06_LINE = (41, 41, 49)                 # C06's outline: every building and prop drawn from HGSS
FOAM = (200, 232, 224)                  # Cherrygrove's foam lip
rgb5 = lambda c: tuple((v >> 3 << 3) | (v >> 5) for v in c)

# --------------------------------------------------------------------------- HGSS renders
D = (0.1195526, 0.1649017, 0.7194366)   # each door's offset from its building in HGSS's placements
# name: (model parts, footprint width px, mirror (rows, axis x, columns) or None)
RENDERS = {
    'house': ([(102, (0, 0, 0)), (103, D)], 64, (57, 32, 64)),
    'pharmacy': ([(104, (0, 0, 0)), (116, D)], 64, (56, 32, 64)),
    'studio': ([(105, (0, 0, 0)), (116, D)], 80, (47, 32, 64)),
    'rack': ([(106, (0, 0, 0))], 32, (999, 16, 32)),
    'camera': ([(90, (0, 0, 0))], 16, None),
    'gym': ([(108, (0, 0, 0)), (16, (0, 0, 1.3125))], 112, (999, 56, 112)),
}

def hgss_renders(phg):
    import hgss_camera as C
    R = C.R
    _, _, models, _, _ = R.load(phg)
    tex = {}
    for mid in (102, 104):
        m = R.mdlview.Model(models[mid])
        for matid, _ in m.faces():
            mat = R.Material(m, matid, m.tex)
            if mat.tex is not None:
                tex.setdefault(mat.name, mat.tex[..., :3])
    out, seams = {}, {}
    for name, (parts, width, mirror) in RENDERS.items():
        rgba, _ = C.view(models, parts, width)
        if name in PANES:
            t, py, px = PANES[name]
            rgba = glaze(rgba, tex[t][py:py + 8, px:px + 8], mirror[0], mirror[1])
        out[name] = rgba
        if name in SEAMS:
            seams[name] = seam_mask(C, models, parts, width, rgba.shape[0], *SEAMS[name])
    return out, seams

# The Gym's side roofs are HGSS's en_gyma planks: light panels with two dark seams (texture
# rows 7-8 and 23-24) that arc across each roof plane. At 14 colours the render's shading
# swallows them, so a marker render at 4x finds where they fall and they are drawn back one
# pixel wide, each pixel one step darker on the roof's own ramp. name: (texture, seam
# rows, plank columns)
SEAMS = {'gym': ('en_gyma', ((7, 9), (23, 25)), (14, 60))}

def seam_mask(C, models, parts, width, height, name, rows, cols, z=4):
    """(seam, plank): per sprite pixel, the seam line (one pixel per column per seam) and
    the plank surface it lies on."""
    def mark(t):
        t = t.copy()
        t[:32, cols[0]:cols[1], :3] = (0, 255, 0)
        for a, b in rows:
            t[a:b, cols[0]:cols[1], :3] = (255, 0, 255)
        return t
    big, _ = C.view(models, parts, width * z, sy=C.C06_SCALE * z, retex={name: mark})
    h = height * z
    big = big[-h:] if big.shape[0] >= h else np.pad(big, ((h - big.shape[0], 0), (0, 0), (0, 0)))
    rgb = big[..., :3].astype(int)
    cover = lambda m: m.reshape(height, z, width, z).mean(axis=(1, 3))
    seam = cover((rgb[..., 0] > 200) & (rgb[..., 1] < 60) & (rgb[..., 2] > 200))
    plank = cover((rgb[..., 0] < 60) & (rgb[..., 1] > 200) & (rgb[..., 2] < 60)) + seam
    line = np.zeros((height, width), bool)
    for x in range(width):                                  # thin each band to its strongest pixel
        y = 0
        while y < height:
            if seam[y, x] > 0.25:
                y1 = y
                while y1 < height and seam[y1, x] > 0.25:
                    y1 += 1
                line[y + int(np.argmax(seam[y:y1, x])), x] = True
                y = y1
            else:
                y += 1
    return line, plank > 0.5

def keep_ramp(pal, rgba, region, k=4, extra=1, n=14):
    """The plank surface's own shades in the palette: of its k-means colours, the `extra`
    farthest from every palette colour join, and the colours whose loss costs the sprite
    least make room (a 14-colour fit alone flattens the roof to one brown)."""
    own = [tuple(v << 3 | v >> 2 for v in c) for c in sprite_palette(np.where(region[..., None], rgba, 0).astype(np.uint8), k)]
    pal = list(pal)
    gap = lambda c: min(max(abs((a >> 3) - (b >> 3)) for a, b in zip(c, q)) for q in pal)
    new = [c for c in sorted(own, key=gap, reverse=True)[:extra] if gap(c) > 1]
    px = rgba[rgba[..., 3] > 0][:, :3].astype(float)
    pal += new
    while len(pal) > n:
        P = np.array(pal, float)
        d = ((px[:, None] - P[None]) ** 2).sum(-1)
        base = d.min(1).sum()
        cost = [np.inf if c in new else np.delete(d, i, 1).min(1).sum() - base for i, c in enumerate(pal)]
        pal.pop(int(np.argmin(cost)))
    return pal

def draw_seams(img, mask):
    """Each seam pixel one step darker on the plank surface's ramp (the colours covering at
    least a twentieth of it, light to dark)."""
    line, plank = mask
    img = img.copy()
    on = plank & (img[..., 3] > 0)
    cols, cnt = np.unique(img[on][:, :3], axis=0, return_counts=True)
    ramp = sorted((tuple(int(v) for v in c) for c, k in zip(cols, cnt) if k >= 0.05 * on.sum()), key=sum)
    step = {c: ramp[max(i - 1, 0)] for i, c in enumerate(ramp)}
    for y, x in zip(*np.nonzero(line & on)):
        c = tuple(int(v) for v in img[y, x, :3])
        if c in step:
            img[y, x, :3] = step[c]
    return img

def sprite_palette(rgba, n=14):
    """A sprite's own colours: weighted k-means over its 5-bit colours with farthest-first
    seeds, so a small accent (a door's wood, a poster) keeps its own colour."""
    import build as B
    px = rgba[rgba[..., 3] > 0][:, :3] >> 3
    uc, cnt = np.unique(px, axis=0, return_counts=True)
    return [tuple(int(v) for v in c) for c in B.kmeans_colors(uc, np.sqrt(cnt).astype(float), n)]

# Colours per palette group: the houses and the Pharmacy are one model with the same
# walls, frames and glass, so they share one palette; small props keep small ramps.
GROUPS = [(('house', 'pharmacy'), 14), (('gym',), 14), (('studio',), 14), (('rack',), 8), (('camera',), 6)]

def town_palettes(renders):
    """A palette per group, then colours within two 5-bit levels of a colour another group
    already uses are merged into it, so the town shares exact colours."""
    pals, shared = {}, []
    for names, n in GROUPS:
        both = np.concatenate([renders[k][renders[k][..., 3] > 0] for k in names])[None]
        own = []
        for c in sprite_palette(both, n):
            near = [q for q in shared if max(abs(a - b) for a, b in zip(q, c)) <= 2]
            c = near[0] if near else c
            if not near:
                shared.append(c)
            if c not in own:
                own.append(c)
        for k in names:
            pals[k] = [tuple(v << 3 | v >> 2 for v in c) for c in own]
    return pals

# Glass roofs: HGSS's own roof textures hold their glass as an 8 px lattice of panes. The
# render shears and resamples it, so nearly every roof tile comes out different; laying
# one pane of the texture back over the plane on an 8 px lattice that steps 4 px per pane
# (the roof's slope) keeps HGSS's glass and makes the plane repeat every two tiles, the
# way Gen 3 builds a roof. name: (texture, pane cell y, x)
PANES = {'house': ('tn_h01_02', 32, 0), 'pharmacy': ('tn_pharmacy02', 34, 6)}

def glaze(rgba, pane, rows, axis):
    """Re-lay the glass of the left roof plane (blue pixels left of axis, above rows)."""
    img = rgba.copy()
    ys, xs = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    c = img[..., :3].astype(int)
    glass = (img[..., 3] > 0) & (c[..., 2] > c[..., 0] + 40) & (c[..., 2] > 120) & (ys < rows) & (xs < axis)
    img[glass, :3] = pane[(ys + xs // 2) % 8, xs % 8][glass]
    return img

def finish(rgba, pal, mirror=None):
    """Mirror the roof's left half onto its right, map to the sprite's palette, then outline
    the silhouette in C06's outline colour."""
    img = rgba.copy()
    if mirror:
        rows, axis, cols = mirror
        left = img[:rows, axis - (cols - axis):axis]
        img[:rows, axis:cols] = left[:, ::-1]
    a = img[..., 3] > 0
    p = np.array(pal, int)
    img[..., :3] = p[((img[..., :3][..., None, :].astype(int) - p[None, None]) ** 2).sum(-1).argmin(-1)]
    img[~a] = 0
    outline(img, C06_LINE)
    return img

# Tile reuse, the way a Gen 3 artist trims a tileset: a building tile that differs from a
# more common tile of its group (any flip) only where an edge sits a pixel over or a render
# speck sits (at most REUSE pixels, each taking a colour its own 4-neighbour already had,
# same silhouette) becomes that tile. Drawn detail (the Gym's roof seams) is kept: a fold
# may not touch it. Sprites are bottom-aligned on cells, so the 8 px grid runs up from the
# bottom edge.
REUSE = 12
REUSE_GROUPS = [('gym',), ('studio',), ('house', 'pharmacy')]
FLIPS = [(False, False), (True, False), (False, True), (True, True)]

def flip(t, f):
    t = t[:, ::-1] if f[0] else t
    return t[::-1] if f[1] else t

def edge_shift(old, new, diff):
    o, n, oa = old[..., :3].astype(int), new[..., :3].astype(int), old[..., 3] > 0
    for y, x in zip(*np.nonzero(diff)):
        if not any(0 <= y + dy < 8 and 0 <= x + dx < 8 and oa[y + dy, x + dx] and (o[y + dy, x + dx] == n[y, x]).all()
                   for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1))):
            return False
    return True

def reuse_tiles(parts, names, keep=None):
    """keep: name -> pixel mask a fold may not change."""
    grids, hold = {}, {}
    for n in names:
        pad = (-parts[n].shape[0]) % 8
        grids[n] = (pad, np.concatenate([np.zeros((pad, parts[n].shape[1], 4), np.uint8), parts[n]], 0))
        k = (keep or {}).get(n, np.zeros(parts[n].shape[:2], bool))
        hold[n] = np.concatenate([np.zeros((pad, k.shape[1]), bool), k], 0)
    seen = {}
    for n, (_, g) in grids.items():
        for ty in range(g.shape[0] // 8):
            for tx in range(g.shape[1] // 8):
                t = g[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].copy()
                if not t[..., 3].any():
                    continue
                t[t[..., 3] == 0] = 0
                f = min(FLIPS, key=lambda f: flip(t, f).tobytes())
                c = flip(t, f)
                e = seen.setdefault(c.tobytes(), [c, [], np.zeros((8, 8), bool)])
                e[1].append((n, ty, tx, f))
                e[2] |= flip(hold[n][ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8], f)
    kept = []
    for t, where, held in sorted(seen.values(), key=lambda v: -len(v[1])):
        a, best = t[..., 3] > 0, None
        for r in kept:
            for f in FLIPS:
                fr = flip(r, f)
                if ((fr[..., 3] > 0) != a).any():
                    continue
                diff = (fr[..., :3] != t[..., :3]).any(-1) & a
                d = int(diff.sum())
                if d <= REUSE and (best is None or d < best[0]) and not (diff & held).any() and edge_shift(t, fr, diff):
                    best = (d, fr)
        if best is None:
            kept.append(t)
            continue
        for n, ty, tx, f in where:
            grids[n][1][ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8] = flip(best[1], f)
    for n, (pad, g) in grids.items():
        parts[n] = g[pad:]

# --------------------------------------------------------------------------- textures
def resample(t, w, h):
    """Area-average an RGBA texture to w x h; alpha thresholded."""
    a = t.astype(float)
    pm = np.clip(a[..., :3] * (a[..., 3:] / 255), 0, 255).astype(np.uint8)
    col = np.array(Image.fromarray(pm).resize((w, h), Image.Resampling.BOX)).astype(float)
    al = np.array(Image.fromarray(t[..., 3]).resize((w, h), Image.Resampling.BOX)).astype(float)
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = np.clip(np.where(al[..., None] > 0, col / np.maximum(al[..., None], 1) * 255, 0), 0, 255)
    out[..., 3] = np.where(al >= 128, 255, 0)
    return out

def to_ramp(img, ramp):
    p = np.array(ramp, int)
    a = img[..., 3] > 0
    out = img.copy()
    out[..., :3] = p[((img[..., :3][..., None, :].astype(int) - p[None, None]) ** 2).sum(-1).argmin(-1)]
    out[~a] = 0
    return out

SEA_ROCK = [(198, 206, 214), (173, 181, 189), (148, 148, 156), (123, 132, 132), (107, 107, 107), (90, 90, 99)]
SEA_ROCK_LINE = (56, 72, 96)            # Cherrygrove's sea-rock slate

def sea_rock(tex, w=32, h=24):
    """HGSS's sea rock texture (sea_rock): the grey rock lit from the upper left and the foam
    ring where it meets the water, the water itself cleared; foam in Cherrygrove's lip
    colour, the rock outlined in Cherrygrove's sea-rock slate."""
    rgb = tex[..., :3].astype(int)
    blue = rgb[..., 2] > rgb[..., 0] + 40
    foam = blue & (rgb[..., 0] > 150)
    t = tex.copy()
    t[..., 3] = np.where(~blue | foam, 255, 0)
    t[foam, :3] = FOAM
    ys, xs = np.nonzero(t[..., 3])
    t = t[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    img = to_ramp(resample(t, w, h), SEA_ROCK + [FOAM])
    body = (img[..., 3] > 0) & ~(img[..., :3] == FOAM).all(-1)
    pad = np.pad(body, 1)
    img[body & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:]), :3] = SEA_ROCK_LINE
    return img

# The cliffs' rock ramp (elements.BLACKTHORN_RAMP), light to dark, then its outline, so a
# stone shares the rock's bank and costs no colours of its own.
STONE = [(239, 189, 140), (198, 148, 115), (165, 115, 99), (132, 90, 74), (99, 70, 66), (82, 58, 52)]

def stone(tex):
    """HGSS's small brown stone (the lower-left quarter of etc_a, its shadow as the rock's
    outline), laid flat as HGSS draws it: 16 x 8, one tile row, so every stone is the same
    two tiles."""
    return to_ramp(resample(tex[16:32, 0:16], 16, 8), STONE)

# Cherrygrove's grass greens and the dark green of its trees (CherrygrovePrimary banks 0 and 3)
TUFT = {'o': (64, 136, 104), 'd': (88, 176, 136), 'm': (104, 208, 152), 'l': (168, 216, 152)}
TUFT_ART = [
    "........o.......",
    "...o...olo......",
    "..olo..olo...o..",
    "..olo..olo..olo.",
    "...olo.olo.olo..",
    "o..olo.olo.olo..",
    "lo..olooloolo.o.",
    "olo.olmlmlolo.lo",
    ".olooldlmlo.olo.",
    "..olmldmdmlolo..",
    "...odmdmdmdmo...",
    "....oddddddo....",
    ".....oooooo.....",
]

def art(rows, pal):
    img = canvas(max(len(r) for r in rows), len(rows))
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in pal:
                img[y, x] = pal[ch] + (255,)
    return img

def tuft():
    """A tuft of beach grass, 16 x 13: blades fanning from one root, light edges, the dark
    tree green as outline."""
    return art(TUFT_ART, TUFT)

def build(phg):
    sys.path.insert(0, str(HERE))
    import elements as E
    renders, seams = hgss_renders(phg)
    pals = town_palettes(renders)
    for name, (_, plank) in seams.items():
        pals[name] = keep_ramp(pals[name], renders[name], plank)
    out = {name: finish(r, pals[name], RENDERS[name][2]) for name, r in renders.items()}
    for name, mask in seams.items():
        out[name] = draw_seams(out[name], mask)
    for names in REUSE_GROUPS:
        reuse_tiles(out, names, keep={n: seams[n][0] for n in names if n in seams})
    rock = sea_rock(E.hgss_texture(phg, 'sea_rock', 'sea_rock'))
    out.update(sea_rock=rock, pebble=sea_rock(E.hgss_texture(phg, 'sea_rock', 'sea_rock'), 16, 13),
               stone=stone(E.hgss_texture(phg, 'etc_a', 'etc_a')), tuft=tuft())
    SPRITES.mkdir(parents=True, exist_ok=True)
    for name, img in out.items():
        Image.fromarray(img, 'RGBA').save(SPRITES / f'{name}.png')
    sheet(out)
    return out

def load(name):
    return np.array(Image.open(SPRITES / f'{name}.png').convert('RGBA'))

def sheet(parts):
    parts = list(parts.values())
    w = sum(p.shape[1] * 4 + 16 for p in parts); h = max(p.shape[0] for p in parts) * 4 + 16
    out = Image.new('RGBA', (w, h), (232, 232, 192, 255))
    x = 8
    for p in parts:
        out.alpha_composite(Image.fromarray(p, 'RGBA').resize((p.shape[1] * 4, p.shape[0] * 4), Image.Resampling.NEAREST), (x, 8))
        x += p.shape[1] * 4 + 16
    out.save(OUT / 'sprites.png')

if __name__ == '__main__':
    build(Path(sys.argv[1]).resolve())
