"""Coordinate-labelled review sheets for Lake of Rage.

    python3 tools/gba/maps/lake_of_rage/review3.py

Whole map: decoded HGSS reference | native decode. Detail sheets: the same pair, numbered by
native cell, at 2x for the regions listed in REGIONS. Native is evidence/pair/lake-native.png (decoded, equal to the installed map
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
ART = ROOT / 'gba/art/lake-of-rage'
EV = ART / 'evidence'
OUT = EV / 'review3'
REGIONS = {  # name: (x0, y0, x1, y1) in cells
    'north-west-house-pond': (0, 0, 32, 24), 'north-lake': (24, 0, 72, 24), 'east-shore-clearing': (56, 12, 96, 48),
    'west-lake': (0, 20, 40, 48), 'south-lake-outlet': (24, 36, 72, 64), 'south-west-ledges': (0, 40, 40, 64),
    'guru-house-cliffs': (48, 44, 96, 64),
}

def pair(ref, nat, box, scale, title):
    x0, y0, x1, y1 = box
    a = T.numbered(ref, x0, y0, x1, y1, scale, title=f'HGSS (decoded land_data 89-94): {title}')
    b = T.numbered(nat, x0, y0, x1, y1, scale, title=f'Native (installed decode): {title}')
    out = Image.new('RGB', (a.width + b.width + 12, max(a.height, b.height)), (24, 26, 30))
    out.paste(a, (0, 0)); out.paste(b, (a.width + 12, 0))
    return out

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ref = np.array(Image.open(ART / 'source/hgss/hgss-reference-true-heights.png').convert('RGB'))
    nat = np.array(Image.open(EV / 'pair/lake-native.png').convert('RGB'))
    pair(ref, nat, (0, 0, 96, 64), 1, 'whole lake, cells x0-95 y0-63').save(OUT / 'whole.png')
    for name, box in REGIONS.items():
        pair(ref, nat, box, 2, f'{name}, cells x{box[0]}-{box[2] - 1} y{box[1]}-{box[3] - 1}').save(OUT / f'{name}.png')
    print('review sheets in', OUT)

if __name__ == '__main__':
    main()
