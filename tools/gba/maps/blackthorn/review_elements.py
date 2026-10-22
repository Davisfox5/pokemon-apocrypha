"""Review images for the element-built Blackthorn: HGSS reference versus the installed map.

    python3 tools/gba/maps/blackthorn/review_elements.py [STYLE]   # STYLE C by default

Run check_elements.py first (it confirms native-STYLE.png is what the engine files decode
to). Writes into gba/art/blackthorn-city/evidence/elements/:
    original-native.png   whole city: HGSS land_data render (true heights) | native Gen 3
    styles.png            whole city in the three rock styles (A, B, C), native C installed
    review/*.png          region pairs at 2x with cell numbers, for close inspection
"""
from __future__ import annotations
import sys
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/blackthorn-city'
EV, SRC = ART / 'evidence/elements', ART / 'source'
REGIONS = {'north-den-pond': (288, 0, 672, 256), 'gym': (288, 192, 672, 448), 'northeast-ice-path': (640, 160, 1024, 416),
           'northwest-cliffs': (0, 160, 384, 416), 'west-town': (96, 416, 480, 672), 'central-town': (320, 560, 704, 816),
           'east-terraces': (640, 416, 1024, 672), 'southwest-bridge': (96, 736, 480, 992), 'southeast-river': (608, 640, 992, 896)}

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
    d.text((6, 8), 'HGSS land_data chunks 104-107, rendered 1:1 at true heights', fill='white')
    d.text((ref.width + 22, 8), f'Native Gen 3, style {style}, as installed (one map, CherrygrovePrimary + BlackthornCity)', fill='white')
    out.save(EV / 'original-native.png')
    views = [('A: HGSS pieces, one layer per metatile (render only, over budget)', EV / 'terrain-A.png'),
             ('B: Emerald rock recoloured', EV / 'terrain-B.png'),
             (f'C: FRLG mountain set recoloured (installed)', EV / f'native-{style}.png')]
    s = Image.new('RGB', (1024 * 3 + 32, 1024 + 28), (28, 32, 38)); d = ImageDraw.Draw(s)
    for i, (t, p) in enumerate(views):
        s.paste(Image.open(p).convert('RGB'), (i * 1040, 28)); d.text((i * 1040 + 6, 8), t, fill='white')
    s.save(EV / 'styles.png')
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
