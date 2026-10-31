"""Coordinate-labelled review sheets for Dark Cave, and the gameplay gallery.

    python3 tools/gba/maps/dark_cave/review.py ENGINE_CHECKOUT RUNTIME_DIR

Whole maps: HGSS's render beside the installed native decode (check.decode, equal to the packer
and to Porymap's export). Detail sheets: the same pair at 2x, numbered by cell, for REGIONS; and
the two outdoor doors (Routes 45 and 46, decoded from the checkout, with the new warp cells
outlined). Gallery: runtime.py's captures. Writes evidence/review/.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(1, str(HERE.parent / 'route46'))
import check as C                                   # noqa: E402
import install as I                                 # noqa: E402
from trace import numbered                          # noqa: E402  (route46/trace.py: numbered cell grid)

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/dark-cave'
SRC, EV = ART / 'source', ART / 'evidence'
OUT = EV / 'review'
REGIONS = {  # side: {name: (x0, y0, x1, y1) in cells}
    'route45-side': {'north-halls': (22, 0, 64, 20), 'west-ledges': (0, 8, 24, 48), 'lake': (22, 14, 60, 46),
                     'south-and-hole': (0, 40, 40, 64)},
    'route31-side': {'west-cavern-and-pools': (0, 0, 34, 32), 'hole-and-north': (16, 0, 64, 22), 'east-halls': (34, 16, 64, 48),
                     'south-and-route46-exit': (34, 40, 64, 64)},
}
GALLERY = ['dark-route45-side-entrance', 'route45-side-entrance', 'route45-side-north-hall', 'route45-side-plateaus',
           'route45-side-lake', 'route45-side-west-ledges', 'route45-side-south', 'route45-side-hole-exit',
           'route31-side-west-cavern', 'route31-side-hole', 'route31-side-north', 'route31-side-east-hall',
           'route31-side-south-hall', 'route31-side-route46-exit', 'route31-side-route31-exit', 'dark-route31-side-pool',
           'arrive-from-route45', 'back-on-route45', 'arrive-from-route45-side', 'back-on-route45-side',
           'arrive-on-route46', 'back-in-route31-side', 'ledge-jumped-south', 'surfing-route45-side-lake',
           'surfing-route31-side-pool', 'rock-smash-rock', 'strength-boulder', 'route31-exit-solid',
           'save-on-route', 'cold-flash-reload', 'continue-menu', 'ordinary-continue']

def pair(a, b, gap=12):
    out = Image.new('RGB', (a.width + b.width + gap, max(a.height, b.height)), (24, 26, 30))
    out.paste(a, (0, 0)); out.paste(b, (a.width + gap, 0))
    return out

def main(engine, runtime):
    OUT.mkdir(parents=True, exist_ok=True)
    for side, name in C.SIDES.items():
        ref = np.array(Image.open(SRC / f'hgss/{side}/hgss-render.png').convert('RGB'))
        nat = C.decode(engine, name, 'dark_cave', 'dark_cave', C.W, C.H)['img']
        a = numbered(ref, 0, 0, C.W, C.H, 1, title=f'HGSS {side} (decoded land_data, area bank 87)')
        b = numbered(nat, 0, 0, C.W, C.H, 1, title=f'Native {name} (installed decode)')
        pair(a, b).save(OUT / f'{side}-whole.png')
        for rn, (x0, y0, x1, y1) in REGIONS[side].items():
            pair(numbered(ref, x0, y0, x1, y1, 2, title=f'HGSS: {rn}'),
                 numbered(nat, x0, y0, x1, y1, 2, title=f'Native: {rn}')).save(OUT / f'{side}-{rn}.png')
    doors = []
    for r, ((cx, cy), mid, _) in I.MOUTHS.items():
        d = C.decode(engine, r, *C.ROUTES[r])
        x0, y0 = max(0, cx - 7), max(0, cy - 5)
        im = numbered(d['img'], x0, y0, min(C.ROUTES[r][2], cx + 8), cy + 6, 2, title=f'{r}: Dark Cave door at ({cx},{cy}), now a warp')
        dr = ImageDraw.Draw(im)
        px, py = 28 + (cx - x0) * 32, 40 + (cy - y0) * 32
        dr.rectangle((px, py, px + 31, py + 31), outline=(255, 220, 0), width=2)
        doors.append(im)
    pair(*doors).save(OUT / 'route-doors.png')
    shots = [Image.open(runtime / f'{n}.png').convert('RGB') for n in GALLERY if (runtime / f'{n}.png').exists()]
    cols = 4
    g = Image.new('RGB', (cols * 248, ((len(shots) + cols - 1) // cols) * 180), (24, 26, 30))
    dr = ImageDraw.Draw(g)
    for i, (n, s) in enumerate(zip([n for n in GALLERY if (runtime / f'{n}.png').exists()], shots)):
        x, y = (i % cols) * 248 + 4, (i // cols) * 180 + 16
        g.paste(s, (x, y)); dr.text((x, y - 13), n, fill='white')
    g.save(OUT / 'gameplay-gallery.png')
    print('review sheets:', sorted(p.name for p in OUT.glob('*.png')))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
