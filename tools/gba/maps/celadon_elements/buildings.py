"""Celadon's buildings and props: HGSS's own models and textures at C06's angle.

    python3 tools/gba/maps/celadon_elements/buildings.py PATH/TO/pokeheartgold

Every building HGSS places in Celadon, and the props the story adds, are rendered with
their own textures by Olivine's camera (hgss_camera.view: 38 degrees, 16 px per tile up the
screen, squeezed across to the building's lot as C06 is), then finished as Gen 3 art by
Olivine's sprite tools: their own colours in 5-bit colour, merged across buildings where
they agree within two levels, C06's outline round the silhouette, symmetric buildings
mirrored on an 8 px axis, near-duplicate tiles folded together.

    services    the Dept Store (242, door 15), the market's services building
    tower       the beige apartment tower beside it (238)
    hotel       the Condominiums (244, door 15), the Pokemon Hotel
    gamecorner  the Game Corner (241, door 15)
    prize       the prize corner (240, door 24)
    house       HGSS's teal house (237), eleven of them
    flat        the teal house with the flower box by the plaza (236)
    cafe        the restaurant (243, door 133), the cafe
    gardens     the Gym (245, door 16) as the Botanical Gardens: its two roof panels
                (kn_gym_c) glazed with the Gym's own window glass with leaves behind it,
                the Gym emblem on its canopy left out and a leaf drawn there
    fountain    the plaza fountain (78)
    stall       the market stalls: HGSS's parasol bench (115, Olivine's) with its blue
                cloth panels in Celadon's rainbow, red to violet west to east
    lamp        Goldenrod's street lamp (95)
    citysign, board, board_ef   HGSS's signs (29, 31, 33)

Writes source/elements/sprites/*.png, origins.json, the sheet sprites.png and
evidence/sprites-vs-hgss.png (each render, unquantized, beside its sprite).
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

import common as C

OUT = C.SRC / 'elements'
SPRITES = OUT / 'sprites'
C06_LINE = (41, 41, 49)

def placements():
    return json.loads((C.SRC / 'hgss/hgss-render.json').read_text())['buildings']

def door(b, d):
    B = placements()
    return tuple(round(B[d]['pos'][k] - B[b]['pos'][k], 4) for k in range(3))

# --------------------------------------------------------------------------- retextures
def glass_with_leaves(gym_b):
    """kn_gym_c (the Gym's grey roof panel, 16 x 16) as glass: the Gym's own window pane
    from ta_gym_b (its blue pane, beside the canopy's greens) with leaves showing through
    it in the canopy's greens."""
    pane = gym_b[0:16, 16:32].copy()
    greens = [tuple(int(v) for v in c) for c in gym_b[0:16, 0:16][..., :3].reshape(-1, 3)]
    greens = sorted(set(greens), key=sum)
    leaf = ["................", "................", "..ll......d.....", ".lLLl....dDd....", ".lLLLl..dDDd....",
            "..lLl...dDd..l..", "...l.....d..lLl.", ".........ll.lLl.", "....d...lLl..l..", "...dDd..lLLl....",
            "...dDDd..ll.....", "....dd..........", ".........lll....", "........lLLLl...", "................",
            "................"]
    pal = dict(l=greens[1], L=greens[-1], d=greens[0], D=greens[len(greens) // 2])
    inner = (pane[..., :3].astype(int).sum(-1) > 300)            # the pane, inside its frame
    for y, row in enumerate(leaf):
        for x, ch in enumerate(row):
            if ch in pal and inner[y, x]:
                pane[y, x, :3] = pal[ch]
    return lambda t: pane if t.shape[:2] == (16, 16) else t

def no_emblem(t):
    """ta_gym_b with the Gym emblem (the white arcs in its lower half) cut out, so the
    canopy over the door is plain; the Gardens' leaf is drawn on afterwards (leaf())."""
    t = t.copy()
    rgb = t[..., :3].astype(int)
    grey = (rgb.max(-1) - rgb.min(-1) < 48) & (rgb.max(-1) > 110)          # the emblem and its soft edge
    glyph = grey & (np.arange(t.shape[0])[:, None] >= 16) & (np.arange(t.shape[1])[None] < 32)
    t[glyph, 3] = 0
    return t

# The Gardens' leaf crest, drawn on the canopy's face where the Gym emblem was.
LEAF = ["......wwww....", "....wwwwwwww..", "..wwwwwwwvww..", ".wwwwwwvwwww..", "wwwwwvwwwww...",
        ".wwwvwwwww....", "..wvwwww......", ".v............", "v............."]

def leaf(img):
    """Draw the leaf centred on the canopy's face (the run of its lightest green above the
    door), in white with the canopy's darkest green for the vein."""
    rgb = img[..., :3].astype(int)
    green = (rgb[..., 1] > rgb[..., 0] + 40) & (rgb[..., 1] > rgb[..., 2] + 20) & (img[..., 3] > 0)
    ys, xs = np.nonzero(green)
    mid = img.shape[1] // 2
    sel = np.abs(xs - mid) < 16
    ys, xs = ys[sel], xs[sel]
    cols = img[ys, xs, :3]
    dark = tuple(int(v) for v in cols[cols.astype(int).sum(-1).argmin()])
    cy = int(np.median(ys))
    y0, x0 = cy - len(LEAF) // 2, mid - len(LEAF[0]) // 2
    for y, row in enumerate(LEAF):
        for x, ch in enumerate(row):
            if ch != '.' and img[y0 + y, x0 + x, 3]:
                img[y0 + y, x0 + x, :3] = (255, 255, 255) if ch == 'w' else dark
    return img

RAINBOW = dict(red=[(255, 115, 115), (214, 66, 74)], orange=[(255, 189, 99), (231, 140, 41)],
               green=[(140, 222, 99), (66, 165, 74)], violet=[(206, 148, 255), (140, 90, 206)])

def rainbow(img):
    """The parasol's blue cloth panels in Celadon's rainbow: each blue pixel takes the
    colour of its panel's place across the parasol (red, orange, green, violet from west
    to east), lit or shaded as the blue it replaces."""
    img = img.copy()
    rgb = img[..., :3].astype(int)
    blue = (rgb[..., 2] > rgb[..., 0] + 40) & (img[..., 3] > 0)
    ys, xs = np.nonzero(blue)
    x0, x1 = xs.min(), xs.max() + 1
    lum = rgb.sum(-1)
    mid = np.median(lum[blue])
    names = list(RAINBOW)
    for y, x in zip(ys, xs):
        light, dark = RAINBOW[names[min(3, (x - x0) * 4 // (x1 - x0))]]
        img[y, x, :3] = light if lum[y, x] >= mid else dark
    return img

# --------------------------------------------------------------------------- spec
# name: (model parts, width px, mirror, texture replacements, skipped textures). Width is the
# building's lot in whole cells (its model's width, rounded, as C06's five cells hold the
# Center's 5.25 units). mirror as Olivine's sprites.mirror: ('rows', last row, axis).
def spec(models_tex=None):
    s = {
        'services': ([(242, (0, 0, 0)), (15, door(4, 5))], 112, ('keep', 56, (66, 84, 36, 100)), {}, ()),
        'tower': ([(238, (0, 0, 0))], 80, None, {}, ()),
        'hotel': ([(244, (0, 0, 0)), (15, door(1, 2))], 96, None, {}, ()),
        'gamecorner': ([(241, (0, 0, 0)), (15, door(6, 7))], 112, ('rows', 999, 56), {}, ()),
        'prize': ([(240, (0, 0, 0)), (24, door(24, 25))], 72, None, {}, ()),
        'house': ([(237, (0, 0, 0))], 64, ('rows', 999, 32), {}, ()),
        'flat': ([(236, (0, 0, 0))], 64, None, {}, ()),
        'cafe': ([(243, (0, 0, 0)), (133, door(36, 37))], 64, None, {}, ()),
        'gardens': ([(245, (0, 0, 0)), (16, door(31, 32))], 112, ('rows', 999, 56), {}, ()),
        'fountain': ([(78, (0, 0, 0))], 48, ('rows', 999, 24), {}, ()),
        'lamp': ([(95, (0, 0, 0))], 16, None, {}, ()),
        'citysign': ([(29, (0, 0, 0))], 16, ('rows', 999, 8), {}, ()),
        'board': ([(31, (0, 0, 0))], 16, ('rows', 999, 8), {}, ()),
        'board_ef': ([(33, (0, 0, 0))], 16, ('rows', 999, 8), {}, ()),
    }
    s['stall'] = ([(115, (0, 0, 0))], 48, None, {}, ())
    return s

def model_texture(models, mid, name):
    r = C.R()
    m = r.mdlview.Model(models[mid])
    for matid, _ in m.faces():
        mat = r.Material(m, matid, m.tex)
        if mat.name == name:
            return mat.tex
    raise KeyError(name)

def renders(phg):
    import hgss_camera as HC
    _, _, models, _, _ = C.load(str(phg))
    gym_b = model_texture(models, 245, 'ta_gym_b')
    sp = spec()
    sp['gardens'][3].update(kn_gym_c=glass_with_leaves(gym_b), ta_gym_b=no_emblem)
    out, origin = {}, {}
    for name, (parts, width, mirror, retex, skip) in sp.items():
        rgba, to_px = HC.view(models, parts, width, retex=retex or None, skip=('h_kage',) + tuple(skip))
        out[name] = rainbow(rgba) if name == 'stall' else rgba
        origin[name] = [round(float(v), 2) for v in to_px(0, 0, 0)]
    return out, origin, sp

# Palette groups: each group's own colours (weighted k-means, farthest-first seeds), at most
# n, merged into a colour another group already uses where they agree within two 5-bit
# levels, so the town shares exact colours. Small props ride in a group already loaded.
# Six groups, one palette bank each (pack.py): the four ground banks, the trees and the
# Center's two take the other seven of the map's thirteen.
GROUPS = [(('services',), 14), (('tower', 'hotel'), 14), (('gamecorner', 'prize'), 14), (('house', 'flat'), 14),
          (('cafe', 'gardens'), 13),
          (('stall', 'fountain', 'lamp', 'citysign', 'board', 'board_ef'), 14)]

def c06_colours():
    img = np.array(Image.open(C.SRC / 'shared-art/pokemon-center.png').convert('RGBA'))
    return sorted({tuple(int(v) for v in c) for c in (img[img[..., 3] > 0][:, :3] >> 3).tolist()})

def palettes(rend):
    """C06's colours come first in the shared list, so a building colour within two levels
    of one of them takes it exactly."""
    import build as B
    pals, shared = {}, list(c06_colours())
    for names, n in GROUPS:
        px = np.concatenate([rend[k][rend[k][..., 3] > 0][:, :3] >> 3 for k in names])
        uc, cnt = np.unique(px, axis=0, return_counts=True)
        own = []
        for c in (tuple(int(v) for v in c) for c in B.kmeans_colors(uc, np.sqrt(cnt).astype(float), n)):
            near = [q for q in shared if max(abs(a - b) for a, b in zip(q, c)) <= 2]
            c = near[0] if near else c
            if not near:
                shared.append(c)
            if c not in own:
                own.append(c)
        for k in names:
            pals[k] = [tuple(v << 3 | v >> 2 for v in c) for c in own]
    return pals

def build(phg):
    import sprites as OS                                  # Olivine's sprite finishing tools
    rend, origin, sp = renders(phg)
    pals = palettes(rend)
    out = {name: OS.finish(r, pals[name], sp[name][2]) for name, r in rend.items()}
    out['gardens'] = leaf(out['gardens'])
    before = {n: OS.unique_tiles(v) for n, v in out.items()}
    for n in out:
        OS.reuse_tiles(out, (n,))
    SPRITES.mkdir(parents=True, exist_ok=True)
    for p in SPRITES.glob('*.png'):
        p.unlink()
    for name, img in out.items():
        Image.fromarray(img, 'RGBA').save(SPRITES / f'{name}.png')
    (SPRITES / 'origins.json').write_text(json.dumps(origin, indent=1) + '\n')
    sheet(out)
    against(rend, out)
    total = set()
    for n, v in out.items():
        cols = {tuple(c) for c in v[v[..., 3] > 0][:, :3].tolist()}
        total |= cols
        print(f'{n:14} {v.shape[1]:3}x{v.shape[0]:3}  tiles {before[n]:3} -> {OS.unique_tiles(v):3}  colours {len(cols)}')
    print('distinct building colours', len(total))
    return out

def against(rend, out):
    """evidence/sprites-vs-hgss.png: each building's HGSS render at C06's angle, unquantized
    (left), beside its finished sprite (right), at 3x."""
    names = [n for n in out if n not in ('citysign', 'board', 'board_ef', 'lamp')]
    z, gap = 3, 12
    w = sum(rend[n].shape[1] * z * 2 + gap * 3 for n in names); h = max(out[n].shape[0] for n in names) * z + 16
    img = Image.new('RGBA', (w, h), (115, 222, 173, 255))
    x = gap
    for n in names:
        for pic in (rend[n], out[n]):
            img.alpha_composite(Image.fromarray(pic, 'RGBA').resize((pic.shape[1] * z, pic.shape[0] * z), Image.Resampling.NEAREST),
                                (x, h - 8 - pic.shape[0] * z))
            x += pic.shape[1] * z + gap
        x += gap
    C.EV.mkdir(parents=True, exist_ok=True)
    img.convert('RGB').save(C.EV / 'sprites-vs-hgss.png')

def load(name):
    return np.array(Image.open(SPRITES / f'{name}.png').convert('RGBA'))

def origins():
    return json.loads((SPRITES / 'origins.json').read_text())

def sheet(parts):
    parts = list(parts.values())
    w = sum(p.shape[1] * 3 + 16 for p in parts); h = max(p.shape[0] for p in parts) * 3 + 16
    out = Image.new('RGBA', (w, h), (115, 222, 173, 255))
    x = 8
    for p in parts:
        out.alpha_composite(Image.fromarray(p, 'RGBA').resize((p.shape[1] * 3, p.shape[0] * 3), Image.Resampling.NEAREST),
                            (x, h - 8 - p.shape[0] * 3))
        x += p.shape[1] * 3 + 16
    out.save(OUT / 'sprites.png')

if __name__ == '__main__':
    build(Path(sys.argv[1]).resolve())
