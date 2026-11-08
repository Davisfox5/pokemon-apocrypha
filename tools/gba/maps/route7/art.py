"""Route 7's buildings and props: HGSS's own Route 7 models brought down to Gen 3 (AGENTS.md,
"The HGSS model is the base, always"), the Celadon round 6 way (celadon_elements/hgss_gen3.py):
rendered at 45 degrees, unsqueezed, with the Gen 3 finish and C06's outline.

    python3 tools/gba/maps/route7/art.py

    gate        247, HGSS's Kanto east-west gatehouse (the Saffron gate), 16 px per unit: HGSS's
                own footprint on the Gen 3 grid
    underground 339, the Underground Path entrance, its door (r39_door1) in the model, 16 px
    notice      31, the notice board (board_cd) in front of it

Writes gba/art/route7/source/art/*.png and evidence/art.png (each sprite beside its model at the
same angle, unquantized, 5x; AGENTS.md "Check against the source").
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'celadon_elements'))
import common as C            # noqa: E402
import gen3_art as G3         # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route7'
PITCH = 45.0
SPEC = dict(gate=([(247, (0, 0, 0))], 16.0, 14), underground=([(339, (0, 0, 0))], 16.0, 14),
            notice=([(31, (0, 0, 0))], 16.0, 8))

def models():
    _, _, m, _, _ = C.load(str(ROOT.parent / 'pokeheartgold'))
    return m

def raw(mods, parts, scale):
    """The model at the same angle, unquantized (the reference the sprite is checked against)."""
    cv, faces, normals, to_px = G3.raster(mods, parts, scale=scale * 4, pitch=PITCH)
    return cv

def build():
    mods = models()
    out = ART / 'source/art'
    out.mkdir(parents=True, exist_ok=True)
    sheet = []
    for name, (parts, scale, n) in SPEC.items():
        img, _ = G3.convert(mods, parts, scale=scale, pitch=PITCH, finish=True, n=n)
        Image.fromarray(img).save(out / f'{name}.png')
        print(name, img.shape, len({tuple(p) for p in img[img[..., 3] > 0][:, :3]}), 'colours')
        sheet.append(img)
    return sheet

if __name__ == '__main__':
    build()
