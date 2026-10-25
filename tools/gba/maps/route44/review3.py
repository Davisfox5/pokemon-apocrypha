"""Coordinate-labelled review sheets for Route 44.

    python3 tools/gba/maps/route44/review3.py

Whole map: decoded HGSS reference over the native decode. Detail sheets: the same pair,
numbered by native cell, at 2x for the regions listed in REGIONS. The seam sheet joins
Mahogany Town's east half to Route 44's west end, HGSS above native, as a player crossing sees
them. Native is evidence/pack3/native.png (decoded, equal to the installed map and to
Porymap's export, see check3.py and porymap.py). Writes evidence/review3/.
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
ART = ROOT / 'gba/art/route-44'
MAH = ROOT / 'gba/art/mahogany-town'
EV = ART / 'evidence'
OUT = EV / 'review3'
REGIONS = {  # name: (x0, y0, x1, y1) in cells
    'west-end-pond': (0, 6, 28, 32), 'river-bridge': (16, 4, 44, 32), 'big-pond-tall-grass': (36, 0, 66, 26),
    'east-woods-road': (56, 0, 84, 32), 'ice-path': (70, 2, 96, 24),
}

def pair(ref, nat, box, scale, title, vertical=False):
    x0, y0, x1, y1 = box
    a = T.numbered(ref, x0, y0, x1, y1, scale, title=f'HGSS (decoded land_data 101-103): {title}')
    b = T.numbered(nat, x0, y0, x1, y1, scale, title=f'Native (installed decode): {title}')
    if vertical:
        out = Image.new('RGB', (max(a.width, b.width), a.height + b.height + 12), (24, 26, 30))
        out.paste(a, (0, 0)); out.paste(b, (0, a.height + 12))
    else:
        out = Image.new('RGB', (a.width + b.width + 12, max(a.height, b.height)), (24, 26, 30))
        out.paste(a, (0, 0)); out.paste(b, (a.width + 12, 0))
    return out

def seam(ref, nat):
    """Mahogany x 16-31 beside Route 44 x 0-15, HGSS above native, cells numbered in Route 44's
    frame (Mahogany x 16-31 is Route 44 x -16..-1)."""
    mref = np.array(Image.open(MAH / 'source/hgss/hgss-reference-true-heights.png').convert('RGB'))
    mnat = np.array(Image.open(MAH / 'evidence/pack3/native.png').convert('RGB'))
    rows = []
    for m, r, label in ((mref, ref, 'HGSS (decoded land_data 85 | 101)'), (mnat, nat, 'Native: Mahogany as accepted | Route 44')):
        joined = np.concatenate([m[:, 256:512], r[:, :256]], 1)
        img = Image.fromarray(joined).resize((joined.shape[1] * 2, joined.shape[0] * 2), Image.Resampling.NEAREST)
        d = ImageDraw.Draw(img)
        for i in range(32):
            d.line((i * 32, 0, i * 32, img.height), fill=(60, 60, 70))
            d.text((i * 32 + 2, 2), str(i - 16), fill='white', stroke_width=1, stroke_fill='black')
        for j in range(32):
            d.line((0, j * 32, img.width, j * 32), fill=(60, 60, 70))
            d.text((2, j * 32 + 3), str(j), fill='white', stroke_width=1, stroke_fill='black')
        d.line((512, 0, 512, img.height), fill=(255, 0, 255), width=2)
        head = Image.new('RGB', (img.width, 22), (24, 26, 30))
        ImageDraw.Draw(head).text((4, 4), f'{label}; the magenta line is the seam (Mahogany x 32 = Route 44 x 0)', fill='white')
        rows += [head, img]
    out = Image.new('RGB', (rows[1].width, sum(r.height for r in rows) + 12), (24, 26, 30))
    y = 0
    for i, r in enumerate(rows):
        out.paste(r, (0, y)); y += r.height + (12 if i == 1 else 0)
    return out

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ref = np.array(Image.open(ART / 'source/hgss/hgss-reference-true-heights.png').convert('RGB'))
    nat = np.array(Image.open(EV / 'pack3/native.png').convert('RGB'))
    pair(ref, nat, (0, 0, 96, 32), 1, 'whole route, cells x0-95 y0-31', vertical=True).save(OUT / 'whole.png')
    seam(ref, nat).save(OUT / 'mahogany-seam.png')
    for name, box in REGIONS.items():
        pair(ref, nat, box, 2, f'{name}, cells x{box[0]}-{box[2] - 1} y{box[1]}-{box[3] - 1}').save(OUT / f'{name}.png')
    print('review sheets in', OUT)

if __name__ == '__main__':
    main()
