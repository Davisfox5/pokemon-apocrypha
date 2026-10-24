"""Review images for Saffron City ten years on: FireRed's Saffron versus the installed map.

    python3 tools/gba/maps/saffron/review.py ENGINE_CHECKOUT

Run check.py first (it confirms evidence/native.png is what the engine files decode to).
Writes evidence/review/*.png: each changed area, FireRed (as FireRed draws it) beside the
native map, at 2x with cell numbers along the edges.
"""
from __future__ import annotations
import sys
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import frlg                                         # noqa: E402
import compose as C                                 # noqa: E402

EV = C.EV
REGIONS = {  # cells x0, y0, x1, y1 (exclusive)
    'station': (12, 4, 32, 18), 'silph-tower-wings': (18, 12, 48, 36), 'dojos-plaza': (36, 8, 54, 18),
    'copycat-house': (14, 15, 26, 24), 'league-office': (42, 15, 54, 25), 'south-center-grade': (14, 32, 52, 46),
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

def main(engine):
    pair = frlg.Pair(engine, C.PRIMARY, C.SECONDARY)
    grid, _ = frlg.layout(engine, C.LAYOUT)
    before = Image.fromarray(frlg.flat(*frlg.render(pair, grid)))
    after = Image.open(EV / 'native.png').convert('RGB')
    (EV / 'review').mkdir(exist_ok=True)
    for name, b in REGIONS.items():
        w, h = (b[2] - b[0]) * 32, (b[3] - b[1]) * 32
        o = Image.new('RGB', (w * 2 + 12, h + 20), (28, 32, 38)); d = ImageDraw.Draw(o)
        o.paste(labelled(before, b, 2), (0, 20)); o.paste(labelled(after, b, 2), (w + 12, 20))
        d.text((4, 4), f'FireRed (SaffronCity_Frlg)   cells x{b[0]}-{b[2] - 1}, y{b[1]}-{b[3] - 1}', fill='white')
        d.text((w + 16, 4), 'Ten years on, as installed', fill='white')
        o.save(EV / 'review' / f'{name}.png')
    print('review images written')

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
