"""Coordinate-labelled review sheets for Route 43.

    python3 tools/gba/maps/route43/review3.py

Whole map: decoded HGSS reference | native decode. Detail sheets: the same pair, numbered by
native cell, at 3x for the regions listed in REGIONS. Native is evidence/pack3/native.png (decoded, equal to the installed map
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
ART = ROOT / 'gba/art/route-43'
EV = ART / 'evidence'
OUT = EV / 'review3'
REGIONS = {  # name: (x0, y0, x1, y1) in cells
    'north-woods-sign': (0, 0, 32, 12), 'ponds-tall-grass': (0, 10, 32, 24), 'big-pond-east-lawn': (0, 22, 32, 36),
    'massif-ledge-toll-gate': (0, 34, 32, 50), 'south-road-mahogany-gate': (0, 46, 32, 64),
}

def pair(ref, nat, box, scale, title):
    x0, y0, x1, y1 = box
    a = T.numbered(ref, x0, y0, x1, y1, scale, title=f'HGSS (decoded land_data 87-88): {title}')
    b = T.numbered(nat, x0, y0, x1, y1, scale, title=f'Native (installed decode): {title}')
    out = Image.new('RGB', (a.width + b.width + 12, max(a.height, b.height)), (24, 26, 30))
    out.paste(a, (0, 0)); out.paste(b, (a.width + 12, 0))
    return out

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ref = np.array(Image.open(ART / 'source/hgss/hgss-reference-true-heights.png').convert('RGB'))
    nat = np.array(Image.open(EV / 'pack3/native.png').convert('RGB'))
    pair(ref, nat, (0, 0, 32, 64), 1, 'whole route, cells x0-31 y0-63').save(OUT / 'whole.png')
    for name, box in REGIONS.items():
        pair(ref, nat, box, 3, f'{name}, cells x{box[0]}-{box[2] - 1} y{box[1]}-{box[3] - 1}').save(OUT / f'{name}.png')
    print('review sheets in', OUT)

if __name__ == '__main__':
    main()
