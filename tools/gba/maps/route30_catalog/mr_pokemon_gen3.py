#!/usr/bin/env python3
"""Mr. Pokemon's house in Gen 3 style (owner review of #39: the HGSS model render read as a bubbly Gen 4 paste).

    python3 tools/gba/maps/route30_catalog/mr_pokemon_gen3.py

Built on Cherrygrove's own house sprite (gba/art/claude-cherrygrove/source/house.png), so the roof pitch, the
camera angle and the cell grid match the houses already accepted in Cherrygrove. Recoloured to HGSS Mr.
Pokemon's house: a slate roof, tan plank walls and a red door, and given his stone chimney on the roof's
top face. Colours stay one-for-one with the master (14), plus nothing new: the chimney reuses the roof's tones.

Writes gba/art/route30-catalog/source/local-art/buildings/mr_pokemon_gen3.png.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
MASTER = ROOT / 'gba/art/claude-cherrygrove/source/house.png'
OUT = ROOT / 'gba/art/route30-catalog/source/local-art/buildings/mr_pokemon_gen3.png'

ROOF_ROWS = 51                  # the roof and its eave end above this row; the door's reds below it stay apart
ROOF = {                        # Cherrygrove's red roof ramp -> HGSS Mr. Pokemon's slate, light to dark
    (232, 152, 144): (160, 152, 152),
    (208, 128, 112): (136, 128, 128),
    (200, 104, 104): (128, 112, 112),
    (184, 88, 88): (112, 100, 100),
    (168, 72, 72): (96, 88, 88),
    (112, 48, 48): (72, 64, 64),
}
WALLS = {                       # brown planks -> his tan planks
    (144, 120, 96): (208, 160, 112),
    (128, 112, 88): (184, 136, 96),
    (112, 88, 64): (160, 112, 72),
}
DOOR = {(120, 32, 40): (160, 72, 48)}  # his red door, one tone; the old roof reds below the eave go to it too
OUTLINE = (40, 32, 48)

def build():
    a = np.array(Image.open(MASTER).convert('RGBA'))
    out = a.copy()
    rgb = a[..., :3]
    ys = np.arange(a.shape[0])[:, None].repeat(a.shape[1], 1)
    for table, rows in ((ROOF, ys < ROOF_ROWS), (WALLS, ys >= 0), (DOOR, ys >= 0)):
        for src, dst in table.items():
            m = (rgb == src).all(-1) & rows & (a[..., 3] > 0)
            out[m, :3] = dst
    # Below the eave the old roof reds are the door's panel and its shading: the panel takes the door red,
    # the shading the darkest slate.
    for src in ROOF:
        m = (rgb == src).all(-1) & (ys >= ROOF_ROWS) & (a[..., 3] > 0)
        out[m, :3] = ROOF[(112, 48, 48)] if src == (112, 48, 48) else DOOR[(120, 32, 40)]
    # His stone chimney on the roof's top face, toward the back.
    x0, x1, y0 = 47, 58, 0
    roof_top = {x: int(np.nonzero(a[:, x, 3])[0].min()) for x in range(x0, x1 + 1)}
    for x in range(x0, x1 + 1):
        for y in range(y0, roof_top[x] + 3):
            edge = x in (x0, x1) or y == y0
            if edge:
                c = OUTLINE
            elif y <= y0 + 2:
                c = ROOF[(232, 152, 144)]                   # the cap
            elif y == y0 + 3:
                c = ROOF[(112, 48, 48)]                     # the cap's shadow
            elif x == x0 + 1:
                c = ROOF[(208, 128, 112)]                   # lit west side
            else:
                c = ROOF[(168, 72, 72)] if (x + y // 3) % 3 else ROOF[(184, 88, 88)]   # stone courses
            out[y, x, :3] = c; out[y, x, 3] = 255
    cols = {tuple(p[:3]) for p in out.reshape(-1, 4) if p[3]}
    assert len(cols) <= 15, len(cols)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out).save(OUT)
    return out

if __name__ == '__main__':
    o = build()
    print(OUT.relative_to(ROOT), o.shape, len({tuple(p[:3]) for p in o.reshape(-1, 4) if p[3]}), 'colours')
