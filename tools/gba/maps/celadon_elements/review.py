"""Review images for Celadon City: HGSS's Celadon beside the installed map.

    python3 tools/gba/maps/celadon_elements/review.py

Run check.py first (it confirms evidence/native.png is what the engine files decode to).
Writes evidence/review/*.png: each area, HGSS's render beside the native map at the same cells,
at 2x with cell numbers along the edges.
"""
from __future__ import annotations
import sys
from pathlib import Path
from PIL import Image, ImageDraw

import common as C

EV, SRC = C.EV, C.SRC
REGIONS = {  # cells x0, y0, x1, y1 (exclusive)
    'north-row': (8, 1, 54, 19), 'market': (8, 13, 27, 37), 'game-corner': (22, 16, 56, 30),
    'canal-and-bridge': (20, 26, 36, 46), 'gardens': (6, 32, 28, 48), 'south-east-and-cafe': (28, 26, 58, 46),
}

def labelled(img, b, scale):
    x0, y0, x1, y1 = b
    big = img.crop((x0 * 16, y0 * 16, x1 * 16, y1 * 16)).resize(((x1 - x0) * 16 * scale, (y1 - y0) * 16 * scale),
                                                               Image.Resampling.NEAREST)
    d = ImageDraw.Draw(big)
    n = 16 * scale
    for i in range(x1 - x0):
        d.text((i * n + 2, 2), str(x0 + i), fill='white', stroke_width=1, stroke_fill='black')
    for i in range(y1 - y0):
        d.text((2, i * n + 3), str(y0 + i), fill='white', stroke_width=1, stroke_fill='black')
    return big

def main():
    before = Image.open(SRC / 'hgss/hgss-render.png').convert('RGB')
    after = Image.open(EV / 'native.png').convert('RGB')
    out = EV / 'review'
    out.mkdir(exist_ok=True)
    for p in out.glob('*.png'):
        p.unlink()
    for name, b in REGIONS.items():
        w, h = (b[2] - b[0]) * 32, (b[3] - b[1]) * 32
        o = Image.new('RGB', (w * 2 + 12, h + 20), (28, 32, 38)); d = ImageDraw.Draw(o)
        o.paste(labelled(before, b, 2), (0, 20)); o.paste(labelled(after, b, 2), (w + 12, 20))
        d.text((4, 4), f'HGSS (pokeheartgold T07)   cells x{b[0]}-{b[2] - 1}, y{b[1]}-{b[3] - 1}', fill='white')
        d.text((w + 16, 4), 'Celadon in Gen 3, as installed', fill='white')
        o.save(out / f'{name}.png')
    print('review images written')

if __name__ == '__main__':
    main()
