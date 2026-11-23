"""Fuchsia's buildings and props: HGSS's own models brought down to Gen 3 (source art for the plan).

    python3 tools/gba/maps/fuchsia_city/sprites.py PATH/TO/pokeheartgold

Every building and prop HGSS places in Fuchsia (hgss-render.json, area bank 16, building texture set 15)
is rendered from its own model and textures by Celadon round 6's method (AGENTS.md on hub branch
claude/celadon-city, "The HGSS model is the base, always"; gen3_art.convert): orthographic at 45 degrees,
unsqueezed, SCALE px per model unit, each material on its own k-means ramp, Gen 3 light, crease lines, the
Gen 3 finish and C06's outline. Each door model rides at HGSS's own offset from its building.

Writes gba/art/kanto-fuchsia/source/local-art/buildings/{name}.png, buildings.json, and
evidence/buildings/sprites-vs-hgss.png: each model's plain HGSS render at the same angle (left) beside
its Gen 3 sprite (right), at 3x, for the owner's check before anything is placed.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'route32_native'), str(HERE)]
import hgss_render as R                              # noqa: E402
import gen3_art as G3                                # noqa: E402
B30 = G3._B                                          # route30_catalog/buildings.py (view(): the plain render)

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/kanto-fuchsia'
OUT, EV = ART / 'source/local-art/buildings', ART / 'evidence/buildings'
PITCH, SCALE = 45.0, 16.0

# name: (building model, door model or None, colours per material)
SPEC = dict(hall=(295, None, 14), mart=(39, 15, 14), gym=(300, 16, 14), house_red=(297, 307, 8), house_pink=(298, None, 8),
            warden_house=(299, 306, 8), center_hgss=(40, 15, 10), route15_gate=(247, None, 10),
            city_sign=(29, None, 8), house_sign=(30, None, 8), notice_board=(31, None, 8), gym_sign=(33, None, 8),
            lamp=(333, None, 8))

# Self-check against the source (2026-11-23): the Gen 3 light step turned the Gym's brown roof rim orange and the
# Mart's slate roof panel bright blue. These two keep their HGSS texel colours; creases and the finish still apply.
UNLIT = ('gym', 'mart')

def parts(placed, model, door):
    pos = {}
    for e in placed:
        pos.setdefault(e['model'], []).append(np.array(e['pos']))
    p = pos[model][0]
    out = [(model, (0.0, 0.0, 0.0))]
    if door:
        d = min(pos[door], key=lambda q: np.linalg.norm(q - p))
        out.append((door, tuple(float(v) for v in d - p)))
    return out

def build(phg):
    R.AREA_BANK, R.HEADER_ID = 16, 56
    _, _, models, _, _ = R.load(phg)
    placed = json.loads((ART / 'source/hgss/hgss-render.json').read_text())['buildings']
    OUT.mkdir(parents=True, exist_ok=True); EV.mkdir(parents=True, exist_ok=True)
    info, pairs = {}, []
    for name, (model, door, n) in SPEC.items():
        pp = parts(placed, model, door)
        skip = ('h_kage',)
        sprite, _ = G3.convert(models, pp, scale=SCALE, pitch=PITCH, finish=True, n=n, skip=skip, light=name not in UNLIT)
        width = B30.visible_width(models, pp)
        plain, _ = B30.view(models, pp, max(8, int(round(width * SCALE))), pitch=PITCH, sy=SCALE)
        Image.fromarray(sprite, 'RGBA').save(OUT / f'{name}.png')
        info[name] = dict(model=model, door_model=door, model_width_units=round(float(width), 2), size=[sprite.shape[1], sprite.shape[0]],
                          cells=[round(sprite.shape[1] / 16, 2), round(sprite.shape[0] / 16, 2)],
                          colours=len({tuple(c) for c in sprite[sprite[..., 3] > 0][:, :3].tolist()}))
        pairs.append((name, plain, sprite))
    (OUT / 'buildings.json').write_text(json.dumps(dict(
        note='HGSS models at 45 degrees, unsqueezed, 16 px per unit, Gen 3 finish (Celadon round 6 method). '
             'center_hgss is for comparison only: the map uses the owner-locked C06 Center.', sprites=info), indent=1) + '\n')
    z, gap = 3, 14
    rows, row, rw = [], [], 0
    for item in pairs:
        w = (item[1].shape[1] + item[2].shape[1]) * z + gap * 3
        if row and rw + w > 1900:
            rows.append(row); row, rw = [], 0
        row.append(item); rw += w
    rows.append(row)
    heights = [max(max(p.shape[0], s.shape[0]) for _, p, s in r) * z + 34 for r in rows]
    sheet = Image.new('RGBA', (1920, sum(heights)), (115, 222, 173, 255)); d = ImageDraw.Draw(sheet); y = 0
    for r, h in zip(rows, heights):
        x = gap
        for name, plain, sprite in r:
            d.text((x, y + 4), f"{name} ({SPEC[name][0]})", fill="black")
            for pic in (plain, sprite):
                sheet.alpha_composite(Image.fromarray(pic, 'RGBA').resize((pic.shape[1] * z, pic.shape[0] * z), Image.Resampling.NEAREST),
                                      (x, y + h - 8 - pic.shape[0] * z))
                x += pic.shape[1] * z + gap
            x += gap
        y += h
    sheet.convert('RGB').save(EV / 'sprites-vs-hgss.png')
    print(json.dumps(info, indent=0))

if __name__ == '__main__':
    build(Path(sys.argv[1]).resolve())
