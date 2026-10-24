"""Review images for Saffron City ten years on (v2): HGSS's Saffron versus the installed map.

    python3 tools/gba/maps/saffron/review.py [ENGINE_CHECKOUT]   # with the engine, the interiors too

Run check.py first (it confirms evidence/native.png is what the engine files decode to).
Writes evidence/review/*.png: each area the story changed and the city's plan around it,
HGSS (its own map data, decoded) beside the native map, at 2x with cell numbers along the
edges; and the two new interiors beside the FireRed rooms they are built from.
"""
from __future__ import annotations
import sys
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
import frlg                                         # noqa: E402

ART = ROOT / 'gba/art/saffron-kanto'
EV = ART / 'evidence'
REGIONS = {  # cells x0, y0, x1, y1 (exclusive)
    'dojo': (35, 4, 56, 19), 'silph-and-lab': (19, 20, 45, 44), 'station': (0, 6, 20, 22),
    'center-mart': (8, 18, 46, 54), 'east-gate': (48, 38, 64, 58), 'north-gate': (12, 0, 30, 10),
}

def labelled(img, b, scale):
    """Cells b of img at scale, with cell numbers along the top and left edges."""
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

def side_by_side(a, b, ta, tb, out):
    o = Image.new('RGB', (a.width + b.width + 12, max(a.height, b.height) + 20), (28, 32, 38)); d = ImageDraw.Draw(o)
    o.paste(a, (0, 20)); o.paste(b, (a.width + 12, 20))
    d.text((4, 4), ta, fill='white'); d.text((a.width + 16, 4), tb, fill='white')
    o.save(out)

def main(engine=None):
    hgss = Image.open(ART / 'source/hgss/hgss-render.png').convert('RGB')
    after = Image.open(EV / 'native.png').convert('RGB')
    (EV / 'review').mkdir(exist_ok=True)
    for name, b in REGIONS.items():
        side_by_side(labelled(hgss, b, 2), labelled(after, b, 2), f'HGSS (header 59, decoded)   cells x{b[0]}-{b[2] - 1}, y{b[1]}-{b[3] - 1}',
                     'Ten years on, as installed', EV / 'review' / f'{name}.png')
    if engine:
        import interiors as I
        src = I.sources(engine)
        for key, name, room in (('D', 'dojo-hall', 'interiors/dojo.png'), ('G', 'dojo-hall-gym', 'interiors/dojo.png'),
                                ('L', 'silph-lab', 'interiors/lab.png')):
            pair, grid = src[key]
            before = Image.fromarray(frlg.flat(*frlg.render(pair, grid)))
            before = before.resize((before.width * 2, before.height * 2), Image.Resampling.NEAREST)
            side_by_side(before, Image.open(EV / room).convert('RGB'), f'FireRed ({I.SOURCES[key][0]})', 'Ten years on, as installed',
                         EV / 'review' / f'{name}.png')
    print('review images written')

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None)
