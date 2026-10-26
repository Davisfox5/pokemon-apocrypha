"""Cherrygrove's houses as Gen 3 sprites by Blackthorn's method (route30_catalog/buildings.py): HGSS
Cherrygrove's own house models at the owner-locked C06 Center's angle, each with HGSS's door (model 50) at
the offset HGSS Cherrygrove places it.

    python3 tools/gba/maps/cherrygrove_town/houses.py PATH/TO/pokeheartgold

skylight  HGSS model 37 (the two west houses of HGSS Cherrygrove; Route 30's Apricorn house)
gable     HGSS model 38 (HGSS Cherrygrove's middle house)
teal      the skylight house with its roof and door turned to the town's teal (the owner's transplant
          colour), the same tiles in another palette

The skylight and gable houses share 13 colours (buildings.py's weighted k-means over both) plus C06's
outline, one bank as the town's pink and red houses had; each bank keeps one slot for the lawn the door
animation draws beside the door. Writes gba/art/cherrygrove-town/source/
houses/{name}.png, houses.json and a contact sheet.
"""
from __future__ import annotations
import colorsys, json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / 'route30_catalog')]
import buildings as Bd                               # noqa: E402
import hgss_render as R                              # noqa: E402

ROOT = HERE.parents[3]
OUT = ROOT / 'gba/art/cherrygrove-town/source/houses'
HGSS_CHERRYGROVE = 67                                # pokeheartgold MAP_CHERRYGROVE (T21)
MODELS = dict(skylight=37, gable=38)
DOOR_MODEL = 50
TONES = 13                                           # + C06's outline + the lawn beside the door = 15
TEAL_HUE = 168 / 360                                 # the owner's teal roofs (hue of the old roof ramp)

def placements(phg):
    """Each house model with its door at HGSS Cherrygrove's own offset."""
    R.HEADER_ID = HGSS_CHERRYGROVE
    land, _, models, chunks, _ = R.load(phg)
    pos = {}
    for c in chunks:
        ch = R.hgss_map.MapChunk.parse(land[c['land']])
        for i in range(len(ch.buildings) // 48):
            e = ch.buildings[i * 48:i * 48 + 48]
            mid, = struct.unpack_from('<I', e, 0)
            p = np.array([struct.unpack_from('<i', e, 4 + 4 * k)[0] / 65536 for k in range(3)]) + (16 + c['cx'] * 32, 0, 16 + c['cz'] * 32)
            pos.setdefault(mid, []).append(p)
    def door_of(p):
        d = min(pos[DOOR_MODEL], key=lambda q: np.linalg.norm(q - p))
        return tuple(float(v) for v in d - p)
    return models, {n: [(m, (0.0, 0.0, 0.0)), (DOOR_MODEL, door_of(pos[m][0]))] for n, m in MODELS.items()}

def door_box(models, parts, width):
    """The door's columns and rows in the sprite (a marker render of its texture)."""
    paint = lambda t: np.where(t[..., 3:] > 0, np.array([0, 255, 0, 255], np.uint8), t)
    img, _ = Bd.view(models, parts, width, retex={'yo_door1': paint})
    g = (img[..., 0] < 60) & (img[..., 1] > 200) & (img[..., 2] < 60)
    ys, xs = np.nonzero(g)
    return [int(xs.min()), int(xs.max()) + 1], [int(ys.min()), int(ys.max()) + 1]

def teal(pal):
    """The skylight house's palette with its warm roof and door tones turned to the town's teal."""
    out = []
    for c in pal:
        h, s, v = colorsys.rgb_to_hsv(*[x / 255 for x in c])
        if (h < 25 / 360 or h > 340 / 360) and s > 0.2:
            c = tuple(int(round(x * 255)) for x in colorsys.hsv_to_rgb(TEAL_HUE, s * 0.6, min(1.0, v * 1.02)))
            c = tuple((x >> 3) << 3 for x in c)
        out.append(c)
    return out

def build(phg):
    models, parts = placements(phg)
    OUT.mkdir(parents=True, exist_ok=True)
    info, sheet = {}, []
    renders = {}
    for name, pr in parts.items():
        width = int(round(Bd.visible_width(models, pr) * 16 / 8)) * 8
        renders[name] = (pr, width, Bd.view(models, pr, width)[0])
    # The skylight and gable houses share one palette (one bank), as the town's pink and red houses do.
    pal = Bd.sprite_palette(np.concatenate([r[2].reshape(-1, 4) for r in renders.values()])[None], TONES)
    for name, (pr, width, rgba) in renders.items():
        img = Bd.reuse_tiles(Bd.finish(rgba, pal))
        cols, rows = door_box(models, pr, width)
        Image.fromarray(img, 'RGBA').save(OUT / f'{name}.png')
        used = sorted({tuple(int(v) for v in c) for c in img[img[..., 3] > 0][:, :3].tolist()})
        info[name] = dict(models=[m for m, _ in pr], offsets=[list(o) for _, o in pr], size=[img.shape[1], img.shape[0]],
                          door_columns=cols, door_rows=rows, palette=used)
        sheet.append(img)
        if name == 'skylight':
            tp = teal(used)
            lut = {a: b for a, b in zip(used, tp)}
            t = img.copy()
            a = t[..., 3] > 0
            t[a, :3] = np.array([lut[tuple(int(v) for v in c)] for c in t[a, :3]], np.uint8)
            Image.fromarray(t, 'RGBA').save(OUT / 'teal.png')
            info['teal'] = dict(info[name], palette=tp, recolour_of='skylight')
            sheet.append(t)
    (OUT / 'houses.json').write_text(json.dumps(dict(
        note="Blackthorn's method (route30_catalog/buildings.py): HGSS Cherrygrove's models at C06's angle, door model 50 at "
             "HGSS's offsets, 13 colours by k-means plus C06's outline; teal is the skylight house's tiles in the town's teal.",
        sprites=info), indent=1) + '\n')
    w = sum(p.shape[1] * 3 + 12 for p in sheet); h = max(p.shape[0] for p in sheet) * 3 + 12
    im = Image.new('RGBA', (w, h), (104, 208, 152, 255)); x = 6
    for p in sheet:
        im.alpha_composite(Image.fromarray(p, 'RGBA').resize((p.shape[1] * 3, p.shape[0] * 3), Image.Resampling.NEAREST), (x, 6))
        x += p.shape[1] * 3 + 12
    (OUT.parents[1] / 'evidence').mkdir(parents=True, exist_ok=True)
    im.save(OUT.parents[1] / 'evidence/houses.png')
    print(json.dumps({k: dict(size=v['size'], door_columns=v['door_columns'], door_rows=v['door_rows'], colours=len(v['palette'])) for k, v in info.items()}))

if __name__ == '__main__':
    build(Path(sys.argv[1]).resolve())
