"""Saffron's Gen 3 building and prop sprites, from HGSS's own models and textures.

    python3 tools/gba/maps/saffron/art.py PATH/TO/pokeheartgold

Saffron ten years on follows HGSS's city (the owner's call, 2026-10-24), so every building
HGSS places in Saffron is HGSS's model rendered at C06's angle (Olivine's method,
olivine_elements/sprites.py), and the story's new buildings are made from HGSS's own
parts (newbuildings.py):

    station    the Magnet Train station (256, door 260), squeezed to HGSS's footprint
    silph      Silph Co. (257, door 261), two floors taller ("dominates the skyline")
    lab        Silph's research lab wing, with its own entrance (newbuildings.lab_wing)
    dojo       the Saffron Dojo: the Fighting and Psychic Dojos in one building, an
               entrance each (newbuildings.saffron_dojo)
    apt_a/b/c  the apartment blocks (252, 253, 254)
    copycat    the Copycat's house (258, door 259)
    mrpsychic  Mr. Psychic's house (251, door 259)
    gate_n/e   the north and east gatehouses (246, 247)
    citysign, board, dojosign, lamp   HGSS's signs (29, 31, 33 without the League's
               emblem) and street lamps (330)

Buildings keep HGSS's own colours (v1's Kanto grade, concrete walls and slate roofs, gave
way to HGSS's yellow and green blocks with the city plan). Each palette group takes its own colours
in 5-bit colour (14 a building), C06's outline round the silhouette; symmetric buildings
mirror on an 8 px axis so their halves share tiles; one-pixel edge shifts fold together.
The Dojo has two groups, Fighting and Psychic, split on a tile column in its hall, that
share one ramp for the roof over both, so the roof shows no seam.

Writes gba/art/saffron-kanto/source/sprites/*.png, origins.json and sprites.png.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
import olivine                          # noqa: E402
import modelkit as K                    # noqa: E402
import newbuildings as NB               # noqa: E402
OS = olivine.mod('sprites')             # Olivine's: palette fit, finish, outline, tile folding

K.R.HEADER_ID, K.R.AREA_BANK = 59, 12   # MAP_SAFFRON (MAP_T11), area data bank 12
ART = ROOT / 'gba/art/saffron-kanto'
OUT = ART / 'source/sprites'
PLACES = ART / 'source/hgss/hgss-render.json'

def no_board_emblem(t):
    """board_ef (the Gym sign) without the League emblem on its head: its grey and white
    marks there take the head's own colour."""
    t = t.copy()
    rgb = t[..., :3].astype(int)
    head = np.zeros(t.shape[:2], bool)
    head[: t.shape[0] // 2] = True
    mark = head & (rgb.min(-1) > 150) & (t[..., 3] > 0)
    if mark.any() and (head & ~mark & (t[..., 3] > 0)).any():
        t[mark, :3] = np.median(rgb[head & ~mark & (t[..., 3] > 0)], 0).astype(np.uint8)
    return t

# --------------------------------------------------------------------------- renders
def placements():
    return json.loads(PLACES.read_text())['buildings']

def offset(model, door):
    """A door's offset from its building, as HGSS's placements put them."""
    B = placements()
    b = next(p for p in B if p['model'] == model)
    d = min((p for p in B if p['model'] == door), key=lambda p: sum((p['pos'][k] - b['pos'][k]) ** 2 for k in (0, 2)))
    return tuple(round(d['pos'][k] - b['pos'][k], 4) for k in range(3))

# name: (parts, px per unit across, mirror spec, texture replacements)
def spec():
    return {
        'apt_a': ([(252, (0, 0, 0))], 17, ('rows', 999, 32), {}),
        'apt_b': ([(253, (0, 0, 0))], 17, ('rows', 999, 32), {}),
        'apt_c': ([(254, (0, 0, 0))], 80 / 4.6, ('rows', 999, 40), {}),
        'copycat': ([(258, (0, 0, 0)), (259, offset(258, 259))], 17, None, {}),
        'mrpsychic': ([(251, (0, 0, 0)), (259, offset(251, 259))], 17, None, {}),
        'gate_n': ([(246, (0, 0, 0))], 96 / 5.5, ('rows', 999, 48), {}),
        'gate_e': ([(247, (0, 0, 0))], 16, ('rows', 999, 60), {}),
        'citysign': ([(29, (0, 0, 0))], 16, None, {}),
        'board': ([(31, (0, 0, 0))], 16, None, {}),
        'dojosign': ([(33, (0, 0, 0))], 16, None, {'board_ef': no_board_emblem}),
        'lamp': ([(330, (0, 3.0, 0))], 16, None, {}),           # HGSS places it 3 units up, on its own post
    }

def hgss_renders(models):
    out, origin = {}, {}
    for name, (parts, sx, _, retex) in spec().items():
        faces = sum((K.load(models, m, off, retex=retex or None) for m, off in parts), [])
        rgba, to_px = K.render(faces, sx)
        out[name] = rgba
        origin[name] = dict(model_px=[round(float(v), 2) for v in to_px(0, 0, 0)])
        door = next((off for m, off in parts if m == 259), None)
        if door:
            origin[name]['door_px'] = [round(float(v), 2) for v in to_px(door[0] - 0.6, 0, door[2] + 0.1)]
    return out, origin

def station(phg):
    """Saffron's Magnet Train station (v1's sprite, HGSS's own placement)."""
    _, _, models, _, _ = K.R.load(phg)
    door = offset(256, 260)
    rgba, to_px = K.C.view(models, [(256, (0, 0, 0)), (260, door)], 168)
    a = STATION_ANNEX // 2                      # the platform annex: its east half the mirror of its west
    rgba[:, a:2 * a] = rgba[:, :a][:, ::-1]
    return rgba, dict(model_px=[round(float(v), 2) for v in to_px(0, 0, 0)],
                      door_px=[round(float(v), 2) for v in to_px(*door)])

# The station's hall mirrors on its centre (x 112); its front at street level (the door, the
# ticket windows west of it) keeps its own pixels. The platform annex west of the hall (x 0-56)
# mirrors on its own centre, a tile's middle, so its three bays share tiles.
STATION_MIRROR = ('keep', 112, (80, 144, 108, 135))
STATION_ANNEX = 56

# Colours per palette group (a bank each); small props ride in a host's colours.
GROUPS = [(('station',), 14), (('silph', 'lab'), 14), (('apt_a', 'apt_b', 'apt_c'), 14), (('copycat', 'mrpsychic'), 14),
          (('gate_n', 'gate_e'), 14)]
HOSTS = dict(citysign='copycat', board='silph', dojosign='silph', lamp='silph')
REUSE_GROUPS = [('station',), ('silph', 'lab'), ('apt_a', 'apt_b', 'apt_c'), ('copycat', 'mrpsychic'), ('gate_n', 'gate_e'),
                ('dojo',), ('citysign',), ('board',), ('dojosign',), ('lamp',)]

FIXED = {('silph', 'lab'): [NB.LAB_LAMP]}       # colours a group keeps whatever k-means finds

def group_palettes(renders):
    pals = {}
    for names, n in GROUPS:
        both = np.concatenate([renders[k][renders[k][..., 3] > 0] for k in names])[None]
        fixed = [tuple(v & 0xF8 for v in c) for c in FIXED.get(names, [])]
        p = [tuple(v << 3 | v >> 2 for v in c) for c in OS.sprite_palette(both, n - len(fixed))]
        p += [tuple(v | v >> 5 for v in c) for c in fixed]
        for k in names:
            pals[k] = p
    for k, host in HOSTS.items():
        pals[k] = pals[host]
    return pals

def dojo_sprite(models):
    """The Dojo in two palette groups split at a tile column in the hall (the first column
    west of the Psychic walls), a shared five-colour ramp for the roof over both."""
    rgba, to_px, doors = NB.saffron_dojo(models)
    mats = K.render.materials
    a = rgba[..., 3] > 0
    roof = a & np.isin(mats, NB.ROOF)
    split = int(to_px(NB.PSYCHIC_X - NB.GYM_WALLS_X, 0, 0)[0]) // 8 * 8
    west = np.zeros(a.shape, bool); west[:, :split] = True
    ramp = [tuple(c) for c in OS.sprite_palette(rgba * roof[..., None], 5)]
    out = rgba.copy()
    near = lambda px, pal: pal[((px[:, None] - pal[None]) ** 2).sum(-1).argmin(-1)]
    to8 = lambda cs: np.array([tuple(v << 3 | v >> 2 for v in c) for c in cs], int)
    out[roof, :3] = near(rgba[roof][:, :3].astype(int), to8(ramp))         # one roof over both halves
    for side in (west, ~west):
        m = a & side & ~roof
        own = [tuple(c) for c in OS.sprite_palette(rgba * m[..., None], 8)]
        out[m, :3] = near(rgba[m][:, :3].astype(int), to8(ramp + own))
    out[~a] = 0
    OS.outline(out, OS.C06_LINE)
    return out, dict(split_px=split, doors={k: [round(float(v[0]), 2), round(float(v[1]), 2)] for k, v in doors.items()},
                     model_px=[round(float(v), 2) for v in to_px(NB.FIGHT_X, 0, 0)])

def build(phg):
    _, _, models, _, _ = K.R.load(phg)
    renders, origin = hgss_renders(models)
    silph, to_px, d = NB.silph_tower(models)
    renders['silph'] = silph
    origin['silph'] = dict(model_px=[round(float(v), 2) for v in to_px(0, 0, 0)], door_px=[round(float(v), 2) for v in d['silph']])
    lab, to_px, d = NB.lab_wing(models)
    renders['lab'] = lab
    origin['lab'] = dict(model_px=[round(float(v), 2) for v in to_px(0, 0, 0)], door_px=[round(float(v), 2) for v in d['lab']])
    renders['station'], origin['station'] = station(phg)
    pals = group_palettes(renders)
    mirror = {k: v[2] for k, v in spec().items()}
    mirror.update(silph=('rows', 999, 80), lab=('rows', 999, 40), station=STATION_MIRROR)
    out = {name: OS.finish(r, pals[name], mirror.get(name)) for name, r in renders.items()}
    out['dojo'], origin['dojo'] = dojo_sprite(models)
    before = {n: OS.unique_tiles(v) for n, v in out.items()}
    for names in REUSE_GROUPS:
        OS.reuse_tiles(out, names)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, img in out.items():
        Image.fromarray(img, 'RGBA').save(OUT / f'{name}.png')
        origin[name]['size'] = [img.shape[1], img.shape[0]]
    (OUT / 'origins.json').write_text(json.dumps(origin, indent=1) + '\n')
    sheet(out)
    total = 0
    for n, v in out.items():
        cols = len({tuple(c) for c in v[v[..., 3] > 0][:, :3].tolist()})
        total += OS.unique_tiles(v)
        print(f'{n:10} {v.shape[1]:3}x{v.shape[0]:3}  tiles {before[n]:3} -> {OS.unique_tiles(v):3}  colours {cols}')
    print('tiles', total)
    return out

def sheet(parts):
    parts = list(parts.values())
    w = sum(p.shape[1] * 2 + 12 for p in parts); h = max(p.shape[0] for p in parts) * 2 + 12
    out = Image.new('RGBA', (w, h), (200, 160, 96, 255))
    x = 6
    for p in parts:
        out.alpha_composite(Image.fromarray(p, 'RGBA').resize((p.shape[1] * 2, p.shape[0] * 2), Image.Resampling.NEAREST),
                            (x, h - 6 - p.shape[0] * 2))
        x += p.shape[1] * 2 + 12
    out.save(ART / 'source/sprites.png')

def load(name):
    return np.array(Image.open(OUT / f'{name}.png').convert('RGBA'))

if __name__ == '__main__':
    build(Path(sys.argv[1]).resolve())
