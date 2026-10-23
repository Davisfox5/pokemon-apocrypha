"""Olivine's Gen 3 sprites, made from HGSS's own models and textures.

    python3 tools/gba/maps/olivine_elements/sprites.py PATH/TO/pokeheartgold

Every building and prop HGSS places in Olivine (bm_field models; doors offset from their
buildings as HGSS's placements put them) is rendered with its own textures at C06's angle
(hgss_camera.view: 38 degrees, 16 px per tile up the screen, squeezed across to its
footprint as C06 is), then finished as Gen 3 art: each palette group's own colours in
5-bit colour (14 for a building, fitted by weighted k-means seeded farthest-first),
merged across groups where they agree within two levels, C06's own outline colour round
the silhouette, symmetric parts mirrored on an 8 px axis so their halves share tiles,
and tiles that differ only by a one-pixel edge shift or a render speck folded together.

    gym         the Gym (111, door 16) as a civic hall: canon has no Olivine Gym, so the
                emblem decal on its plaque (as_gym_w) is left out
    cafe        the Olivine Cafe (118, door 120)
    house       the three houses (109, door 114), one sprite
    lighthouse  the Glitter Lighthouse (110); its tower is lit from the left, so it
                keeps both sides and everything round it mirrors
    terminal    the ferry terminal (167): its body mirrors about the door, the canopy
                over the west platform does not; the red mat on that platform lies on
                the floor, so it is left out with the other painted floor faces
    bench       the parasol benches (115)
    yacht       the sailboats (119) with their wake
    bunting     the flag lines (121): the two poles mirror, the flags do not
    citysign    the city sign (29, board_ab)
    board       the pier and Lighthouse notice boards (31, board_cd)

Writes source/elements/sprites/*.png (what elements.py places) and the contact sheet
source/elements/sprites.png. Each sprite's bottom edge is the bottom of its base row.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = ROOT / 'gba/art/olivine-elements/source/elements'
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

# --------------------------------------------------------------------------- HGSS renders
def placements():
    return json.loads((ROOT / 'gba/art/olivine-elements/source/hgss/hgss-render.json').read_text())['buildings']

def door(b, d):
    """A door's offset from its building, as HGSS's placements put them."""
    B = placements()
    return tuple(round(B[d]['pos'][k] - B[b]['pos'][k], 4) for k in range(3))

def no_emblem(t):
    """as_gym_w with the Gym emblem decal (the white arcs in its lower-left quarter) cut
    out, so the plaque over the door stays plain."""
    t = t.copy()
    rgb = t[..., :3].astype(int)
    glyph = (rgb.min(-1) > 200) & (np.arange(32)[:, None] >= 18) & (np.arange(32)[None, :] < 18)
    t[glyph, 3] = 0
    return t

# name: (model parts, footprint width px, mirror, texture replacements, skipped textures).
# The width is HGSS's blocked footprint (C06's own fit); the flag line is 8 cells (HGSS's 8.8),
# so the one between the Center and the Mart fits between them.
# mirror: ('rows', last mirrored row, axis) mirrors those rows' left half onto the right;
# ('keep', axis, (x0, x1, y0, y1)) mirrors everything outside that box; ('right', axis,
# first column) mirrors the right half onto the left from that column on.
def renders_spec():
    return {
        'gym': ([(111, (0, 0, 0)), (16, door(15, 16))], 112, ('rows', 999, 56), {'as_gym_w': no_emblem}, ()),
        'cafe': ([(118, (0, 0, 0)), (120, door(6, 7))], 64, None, {}, ()),
        'house': ([(109, (0, 0, 0)), (114, door(11, 12))], 64, ('rows', 48, 32), {}, ()),
        'lighthouse': ([(110, (0, 0, 0))], 112, ('keep', 56, (32, 80, 61, 133)), {}, ()),
        'terminal': ([(167, (0, 0, 0))], 144, ('right', 80, 16), {}, ('d_mat01',)),
        'bench': ([(115, (0, 0, 0))], 64, ('rows', 999, 32), {}, ()),
        'yacht': ([(119, (0, 0, 0))], 80, None, {}, ()),
        'bunting': ([(121, (0, 0, 0))], 128, ('poles', 64), {}, ('as_kage',)),
        'citysign': ([(29, (0, 0, 0))], 16, ('rows', 999, 8), {}, ()),
        'board': ([(31, (0, 0, 0))], 16, ('rows', 999, 8), {}, ()),
    }

def hgss_renders(phg):
    import hgss_camera as C
    R = C.R
    _, _, models, _, _ = R.load(phg)
    out, origin = {}, {}
    for name, (parts, width, mirror, retex, skip) in renders_spec().items():
        rgba, to_px = C.view(models, parts, width, retex=retex or None, skip=('h_kage',) + tuple(skip))
        out[name] = rgba
        origin[name] = [round(float(v), 2) for v in to_px(0, 0, 0)]
    return out, origin

def sprite_palette(rgba, n=14):
    """A sprite's own colours: weighted k-means over its 5-bit colours with farthest-first
    seeds, so a small accent (a door's wood, a lifebuoy's red) keeps its own colour."""
    import build as B
    px = rgba[rgba[..., 3] > 0][:, :3] >> 3
    uc, cnt = np.unique(px, axis=0, return_counts=True)
    return [tuple(int(v) for v in c) for c in B.kmeans_colors(uc, np.sqrt(cnt).astype(float), n)]

# Colours per palette group. The Lighthouse and the terminal are one harbour family (blue
# roofs, white walls, glass) and share fifteen colours a bank each; the benches, yachts
# and flags take small ramps that merge into the others where they agree.
GROUPS = [(('gym',), 14), (('cafe',), 14), (('house',), 14), (('lighthouse',), 14), (('terminal',), 14), (('bunting',), 7)]
# Small props draw in a ramp already loaded (no bank of their own): the benches and their
# parasols in the Lighthouse's blues and whites, the yachts in the Gym's whites, greys,
# wood and orange, the city sign in the cafe's wood, the notice boards in the terminal's greys.
HOSTS = dict(bench='lighthouse', yacht='gym', citysign='cafe', board='terminal')

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
    for k, host in HOSTS.items():
        if k in renders:
            pals[k] = pals[host]
    return pals

FLIPS = [(False, False), (True, False), (False, True), (True, True)]

def flip(t, f):
    t = t[:, ::-1] if f[0] else t
    return t[::-1] if f[1] else t

def mirror(img, spec):
    """Mirror the left half onto the right on an 8 px axis (spec from renders_spec)."""
    if not spec:
        return img
    img = img.copy()
    kind = spec[0]
    if kind == 'rows':
        rows, axis = spec[1], spec[2]
        left = img[:rows, :axis]
        img[:rows, axis:axis * 2] = left[:, ::-1][:, :img.shape[1] - axis]
    elif kind == 'poles':
        # the flag line's two poles: columns outside the flags, every row
        axis = spec[1]
        a = img[..., 3] > 0
        cols = [x for x in range(axis) if a[:, x].any()]
        pole = [x for x in cols if x < 24]
        for x in pole:
            img[:, img.shape[1] - 1 - x] = img[:, x]
    elif kind == 'keep':
        axis, (x0, x1, y0, y1) = spec[1], spec[2]
        h = img.shape[0]
        out = img.copy()
        out[:, axis:axis * 2] = img[:, :axis][:, ::-1][:, :img.shape[1] - axis]
        box = np.s_[y0:y1, x0:x1]
        out[box] = img[box]
        img = out
    elif kind == 'right':
        axis, x0 = spec[1], spec[2]
        img[:, x0:axis] = img[:, axis:axis * 2 - x0][:, ::-1]
    return img

def finish(rgba, pal, spec=None):
    """Mirror, map to the sprite's palette, then outline the silhouette in C06's outline."""
    img = mirror(rgba, spec)
    a = img[..., 3] > 0
    p = np.array(pal, int)
    img[..., :3] = p[((img[..., :3][..., None, :].astype(int) - p[None, None]) ** 2).sum(-1).argmin(-1)]
    img[~a] = 0
    outline(img, C06_LINE)
    return img

# Tile reuse, the way a Gen 3 artist trims a tileset: a building tile that differs from a
# more common tile of its group (any flip) only where an edge sits a pixel over or a render
# speck sits (at most REUSE pixels, each taking a colour its own 4-neighbour already had,
# same silhouette) becomes that tile. Sprites are bottom-aligned on cells, so the 8 px
# grid runs up from the bottom edge.
REUSE = 12
REUSE_GROUPS = [('gym',), ('cafe',), ('house',), ('lighthouse',), ('terminal',), ('bench',), ('yacht',), ('bunting',),
               ('citysign',), ('board',)]

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
    for t, where, held in sorted(seen.values(), key=lambda v: (-len(v[1]), v[0].tobytes())):
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

def unique_tiles(img):
    pad = (-img.shape[0]) % 8
    g = np.concatenate([np.zeros((pad,) + img.shape[1:], np.uint8), img], 0)
    seen = set()
    for ty in range(g.shape[0] // 8):
        for tx in range(g.shape[1] // 8):
            t = g[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].copy()
            if t[..., 3].any():
                t[t[..., 3] == 0] = 0
                seen.add(min(flip(t, f).tobytes() for f in FLIPS))
    return len(seen)

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
    outline), laid flat as HGSS draws it: 16 x 8, one tile row."""
    return to_ramp(resample(tex[16:32, 0:16], 16, 8), STONE)

def build(phg):
    renders, origin = hgss_renders(phg)
    (OUT / 'sprites').mkdir(parents=True, exist_ok=True)
    (OUT / 'sprites/origins.json').write_text(json.dumps(origin, indent=1) + '\n')
    pals = town_palettes(renders)
    spec = {k: v[2] for k, v in renders_spec().items()}
    out = {name: finish(r, pals[name], spec[name]) for name, r in renders.items()}
    before = {n: unique_tiles(v) for n, v in out.items()}
    for names in REUSE_GROUPS:
        reuse_tiles(out, names)
    SPRITES.mkdir(parents=True, exist_ok=True)
    for name, img in out.items():
        Image.fromarray(img, 'RGBA').save(SPRITES / f'{name}.png')
    sheet(out)
    for n, v in out.items():
        print(f'{n:11} {v.shape[1]:3}x{v.shape[0]:3}  tiles {before[n]:3} -> {unique_tiles(v):3}  colours {len(pals[n])}')
    return out

def load(name):
    return np.array(Image.open(SPRITES / f'{name}.png').convert('RGBA'))

def sheet(parts):
    parts = list(parts.values())
    w = sum(p.shape[1] * 3 + 16 for p in parts); h = max(p.shape[0] for p in parts) * 3 + 16
    out = Image.new('RGBA', (w, h), (232, 232, 192, 255))
    x = 8
    for p in parts:
        out.alpha_composite(Image.fromarray(p, 'RGBA').resize((p.shape[1] * 3, p.shape[0] * 3), Image.Resampling.NEAREST),
                            (x, h - 8 - p.shape[0] * 3))
        x += p.shape[1] * 3 + 16
    out.save(OUT / 'sprites.png')

if __name__ == '__main__':
    build(Path(sys.argv[1]).resolve())
