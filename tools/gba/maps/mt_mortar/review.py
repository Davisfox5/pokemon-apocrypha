"""Coordinate-labelled review sheets for Mt. Mortar, and the gameplay gallery.

    python3 tools/gba/maps/mt_mortar/review.py ENGINE_CHECKOUT RUNTIME_DIR

Whole floors: HGSS's render beside the installed native decode (check.py's decode, equal to the
packer and to Porymap's export), numbered by native cell (1F back: HGSS's matrix cropped, its
render cut to the same window). Detail sheets at 2x for REGIONS. Route 42's four mouths (decoded
from the checkout, each mouth cell outlined). Gallery: runtime.py's captures. Writes evidence/review/.
"""
from __future__ import annotations
import importlib.util, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent

def _load(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(sp); sys.modules[name] = mod; sp.loader.exec_module(mod)
    return mod

sys.path.insert(0, str(HERE))
P = _load('pack', HERE / 'pack.py')
I = _load('install', HERE / 'install.py')
C = _load('mt_mortar_check', HERE / 'check.py')
sys.path.insert(1, str(HERE.parent / 'route46'))
from trace import numbered                          # noqa: E402  (route46/trace.py: numbered cell grid)

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/mt-mortar'
SRC, EV = ART / 'source', ART / 'evidence'
OUT = EV / 'review'
REGIONS = {   # native cells (x0, y0, x1, y1)
    '1f-entrance': {'falls-and-upper-pool': (30, 0, 62, 30), 'west-halls-and-mouths': (8, 12, 40, 50),
                    'east-halls-and-rock-climb': (56, 12, 90, 52)},
    '1f-back': {'north-maze': (0, 0, 40, 34), 'brown-hall': (16, 26, 58, 62), 'south-exits': (0, 56, 75, 88),
                'east-rock-climb-and-ledges': (40, 20, 75, 60)},
    '2f': {'west': (0, 0, 34, 64), 'east': (30, 0, 64, 64)},
    'b1f': {'north-terraces': (6, 2, 40, 40), 'lake-and-ladders': (2, 36, 58, 82)},
}
GALLERY = ['view-1f-entrance', 'view-1f-back', 'view-2f', 'view-b1f', 'mouth-20-11', 'mouth-48-15', 'mouth-50-4', 'mouth-77-11',
           'falls-crest', 'falls-foot', 'waterfall-offered', 'rock-climb-1f-entrance', 'rock-climb-1f-back', 'ledge-east', 'ledge-west',
           'save-on-route', 'cold-flash-reload', 'continue-menu', 'ordinary-continue']

def pair(a, b, gap=12):
    out = Image.new('RGB', (a.width + b.width + gap, max(a.height, b.height)), (24, 26, 30))
    out.paste(a, (0, 0)); out.paste(b, (a.width + gap, 0))
    return out

def main(engine, runtime):
    OUT.mkdir(parents=True, exist_ok=True)
    for side, name in I.MAPS.items():
        w, h = P.SIZE[side]
        ox, oy = P.OFFSET[side]
        ref = np.array(Image.open(SRC / f'hgss/{side}/hgss-render.png').convert('RGB'))[oy * 16:(oy + h) * 16, ox * 16:(ox + w) * 16]
        nat = C.decode(engine, name, 'mt_mortar', 'mt_mortar', w, h)['img']
        crop = f', cropped at HGSS ({ox},{oy})' if (ox, oy) != (0, 0) else ''
        pair(numbered(ref, 0, 0, w, h, 1, title=f'HGSS {side} (decoded land_data, area bank 79{crop})'),
             numbered(nat, 0, 0, w, h, 1, title=f'Native {name} (installed decode)')).save(OUT / f'{side}-whole.png')
        for rn, (x0, y0, x1, y1) in REGIONS[side].items():
            x1, y1 = min(x1, w), min(y1, h)
            pair(numbered(ref, x0, y0, x1, y1, 2, title=f'HGSS: {rn}'),
                 numbered(nat, x0, y0, x1, y1, 2, title=f'Native: {rn}')).save(OUT / f'{side}-{rn}.png')
    r, pf, sf, ww, hh = C.ROUTE
    d = C.decode(engine, r, pf, sf, ww, hh)
    mouths = []
    for (cx, cy) in sorted(I.MOUTHS):
        x0, y0 = max(0, cx - 6), max(0, cy - 4)
        im = numbered(d['img'], x0, y0, min(ww, cx + 7), min(hh, cy + 5), 2, title=f'Route 42: Mt. Mortar mouth at ({cx},{cy}), now a door')
        dr = ImageDraw.Draw(im)
        px, py = 28 + (cx - x0) * 32, 40 + (cy - y0) * 32
        dr.rectangle((px, py, px + 31, py + 31), outline=(255, 220, 0), width=2)
        mouths.append(im)
    pair(pair(mouths[0], mouths[1]), pair(mouths[2], mouths[3])).save(OUT / 'route42-mouths.png')
    names = [n for n in GALLERY if (runtime / f'{n}.png').exists()]
    names += sorted(p.stem for p in runtime.glob('warp-*.png'))
    cols = 4
    g = Image.new('RGB', (cols * 248, ((len(names) + cols - 1) // cols) * 180), (24, 26, 30))
    dr = ImageDraw.Draw(g)
    for i, n in enumerate(names):
        x, y = (i % cols) * 248 + 4, (i // cols) * 180 + 16
        g.paste(Image.open(runtime / f'{n}.png').convert('RGB'), (x, y)); dr.text((x, y - 13), n, fill='white')
    g.save(OUT / 'gameplay-gallery.png')
    print('review sheets:', sorted(p.name for p in OUT.glob('*.png')))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
