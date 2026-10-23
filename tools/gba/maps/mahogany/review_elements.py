"""Review images for the element-built Mahogany: HGSS reference versus the installed map.

    python3 tools/gba/maps/mahogany/review_elements.py [STYLE]   # STYLE C by default

Run check_elements.py first (it confirms native-STYLE.png is what the engine files decode
to). Writes into gba/art/mahogany-town/evidence/elements/:
    original-native.png   whole town: HGSS land_data render (true heights) | native Gen 3
    review/*.png          region pairs at 2x with cell numbers, for close inspection
"""
from __future__ import annotations
import sys
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/mahogany-town'
EV, SRC = ART / 'evidence/elements', ART / 'source'
REGIONS = {'north-west': (0, 0, 272, 272), 'north-east': (240, 0, 512, 272), 'south-west': (0, 240, 272, 512),
           'south-east': (240, 240, 512, 512), 'town-centre': (128, 128, 432, 400)}

def labelled(img, b, scale):
    """Crop b of img at scale, with cell numbers along the top and left edges."""
    w, h = b[2] - b[0], b[3] - b[1]
    big = img.crop(b).resize((w * scale, h * scale), Image.Resampling.NEAREST)
    d = ImageDraw.Draw(big)
    n = 16 * scale
    for i in range(w // 16):
        d.text((i * n + 2, 2), str(b[0] // 16 + i), fill='white', stroke_width=1, stroke_fill='black')
    for i in range(h // 16):
        d.text((2, i * n + 3), str(b[1] // 16 + i), fill='white', stroke_width=1, stroke_fill='black')
    return big

def main(style):
    ref = Image.open(SRC / 'hgss/hgss-reference-true-heights.png').convert('RGB')
    nat = Image.open(EV / f'native-{style}.png').convert('RGB')
    out = Image.new('RGB', (ref.width * 2 + 16, ref.height + 28), (28, 32, 38)); d = ImageDraw.Draw(out)
    out.paste(ref, (0, 28)); out.paste(nat, (ref.width + 16, 28))
    d.text((6, 8), 'HGSS land_data 85, true heights', fill='white')
    d.text((ref.width + 22, 8), 'Native Gen 3, as installed', fill='white')
    out.save(EV / 'original-native.png')
    (EV / 'review').mkdir(exist_ok=True)
    for name, b in REGIONS.items():
        w, h = b[2] - b[0], b[3] - b[1]
        o = Image.new('RGB', (w * 4 + 12, h * 2 + 20), (28, 32, 38)); d = ImageDraw.Draw(o)
        o.paste(labelled(ref, b, 2), (0, 20)); o.paste(labelled(nat, b, 2), (w * 2 + 12, 20))
        d.text((4, 4), f'HGSS (true heights)   cells x{b[0] // 16}-{b[2] // 16 - 1}, y{b[1] // 16}-{b[3] // 16 - 1}', fill='white')
        d.text((w * 2 + 16, 4), f'Native Gen 3, style {style}, as installed', fill='white')
        o.save(EV / 'review' / f'{name}.png')
    print('review images written')

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'C')
