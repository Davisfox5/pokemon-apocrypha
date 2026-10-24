"""Coordinate-labelled review sheets for the third-draft Mahogany Town.

    python3 tools/gba/maps/mahogany/review3.py [GAMEPLAY_FRAMES_DIR]

Whole map: decoded HGSS reference | native decode. Detail sheets: the same pair, numbered by
native cell, at 3x for each quarter and for the rock structures, buildings and ledges
listed in REGIONS. Native is evidence/pack3/native.png (decoded, equal to the installed map
and to Porymap's export, see check3.py and porymap.py). Writes evidence/review3/.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import trace as T                                   # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/mahogany-town'
EV = ART / 'evidence'
OUT = EV / 'review3'
REGIONS = {  # name: (x0, y0, x1, y1) in cells
    'nw-mountain-gate': (0, 0, 16, 11), 'ne-woods-tower': (16, 0, 32, 12), 'west-lawns-ledges': (0, 9, 16, 22),
    'houses-antenna': (12, 10, 32, 17), 'gym-terraces': (0, 15, 16, 27), 'center-east-wall': (16, 16, 32, 27),
    'south-terraces': (0, 24, 32, 32),
}

def pair(ref, nat, box, scale, title):
    x0, y0, x1, y1 = box
    a = T.numbered(ref, x0, y0, x1, y1, scale, title=f'HGSS (decoded land_data 85): {title}')
    b = T.numbered(nat, x0, y0, x1, y1, scale, title=f'Native (installed decode): {title}')
    out = Image.new('RGB', (a.width + b.width + 12, max(a.height, b.height)), (24, 26, 30))
    out.paste(a, (0, 0)); out.paste(b, (a.width + 12, 0))
    return out

def main(frames=None):
    OUT.mkdir(parents=True, exist_ok=True)
    ref = np.array(Image.open(ART / 'source/hgss/hgss-reference-true-heights.png').convert('RGB'))
    nat = np.array(Image.open(EV / 'pack3/native.png').convert('RGB'))
    pair(ref, nat, (0, 0, 32, 32), 2, 'whole town, cells 0-31').save(OUT / 'whole.png')
    for name, box in REGIONS.items():
        pair(ref, nat, box, 3, f'{name}, cells x{box[0]}-{box[2] - 1} y{box[1]}-{box[3] - 1}').save(OUT / f'{name}.png')
    print('review sheets in', OUT)

if __name__ == '__main__':
    main(*sys.argv[1:])
