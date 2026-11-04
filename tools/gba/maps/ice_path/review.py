"""Coordinate-labelled review sheets for Ice Path, and the gameplay gallery.

    python3 tools/gba/maps/ice_path/review.py ENGINE_CHECKOUT RUNTIME_DIR

Whole floors: HGSS's render beside the installed native decode (check.py's decode, equal to the
packer and to Porymap's export), numbered by cell. Detail sheets at 2x for REGIONS. The two doors
(Route 44's and Blackthorn's, decoded from the checkout, the warp cell outlined). Gallery:
runtime.py's captures. Writes evidence/review/.
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
C = _load('ice_path_check', HERE / 'check.py')
sys.path.insert(1, str(HERE.parent / 'route46'))
from trace import numbered                          # noqa: E402  (route46/trace.py: numbered cell grid)

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/ice-path'
SRC, EV = ART / 'source', ART / 'evidence'
OUT = EV / 'review'
REGIONS = {
    '1f': {'west-ice-and-halls': (14, 2, 46, 24), 'east-ladders': (36, 2, 60, 42), 'route44-door-and-ice': (6, 30, 30, 62)},
    'b1f': {'crystal-field-and-holes': (2, 2, 30, 24), 'lower-room': (2, 32, 30, 52)},
    'b2f': {'west-ice-and-fallen-boulders': (0, 0, 32, 32), 'east': (32, 0, 64, 32)},
    'b3f': {'whole-2x': (0, 0, 32, 32)},
}
GALLERY = ['view-1f', 'arrive-from-route44', 'back-on-route44', 'arrive-from-blackthorn', 'back-in-blackthorn',
           'ladder-1f-55-7', 'ladder-1f-55-20', 'ladder-b1f-6-20', 'ladder-b1f-25-8', 'ladder-b1f-27-40', 'ladder-b1f-6-41',
           'ladder-b2f-26-10', 'ladder-b2f-16-17', 'ladder-b2f-50-5', 'ladder-b2f-43-21', 'ladder-b3f-5-10', 'ladder-b3f-24-11',
           'stairs-1f-31-9', 'stairs-1f-32-32', 'stairs-1f-38-19', 'stairs-1f-49-8', 'stairs-1f-52-18', 'stairs-b2f-49-17',
           'stairs-b2f-55-11', 'stairs-b3f-12-10', 'stairs-b3f-20-10', 'dropped-to-b2f', 'slid-1f', 'slid-b2f', 'boulder-in-hole', 'b1f-boulder-gone', 'rock-smash-rock', 'view-b1f', 'view-b2f',
           'view-b3f', 'save-on-route', 'cold-flash-reload', 'continue-menu', 'ordinary-continue']

def pair(a, b, gap=12):
    out = Image.new('RGB', (a.width + b.width + gap, max(a.height, b.height)), (24, 26, 30))
    out.paste(a, (0, 0)); out.paste(b, (a.width + gap, 0))
    return out

def main(engine, runtime):
    OUT.mkdir(parents=True, exist_ok=True)
    for side, name in I.MAPS.items():
        w, h = P.SIZE[side]
        ref = np.array(Image.open(SRC / f'hgss/{side}/hgss-render.png').convert('RGB'))
        nat = C.decode(engine, name, 'ice_path', 'ice_path', w, h)['img']
        pair(numbered(ref, 0, 0, w, h, 1, title=f'HGSS {side} (decoded land_data, area bank 76)'),
             numbered(nat, 0, 0, w, h, 1, title=f'Native {name} (installed decode)')).save(OUT / f'{side}-whole.png')
        for rn, (x0, y0, x1, y1) in REGIONS[side].items():
            pair(numbered(ref, x0, y0, x1, y1, 2, title=f'HGSS: {rn}'),
                 numbered(nat, x0, y0, x1, y1, 2, title=f'Native: {rn}')).save(OUT / f'{side}-{rn}.png')
    doors = []
    for r, ((cx, cy), mid, _, _) in I.MOUTHS.items():
        d = C.decode(engine, r, *C.ROUTES[r])
        x0, y0 = max(0, cx - 7), max(0, cy - 5)
        im = numbered(d['img'], x0, y0, min(C.ROUTES[r][2], cx + 8), cy + 6, 2, title=f'{r}: Ice Path door at ({cx},{cy}), now a warp')
        dr = ImageDraw.Draw(im)
        px, py = 28 + (cx - x0) * 32, 40 + (cy - y0) * 32
        dr.rectangle((px, py, px + 31, py + 31), outline=(255, 220, 0), width=2)
        doors.append(im)
    pair(*doors).save(OUT / 'doors.png')
    # HGSS's stairs beside native, every flight (owner review: the stairs were left out)
    spots = [(side, c['x'], c['y']) for side in I.MAPS for c in __import__('json').loads((SRC / f'assemble/{side}-ledger.json').read_text())['cells']
             if c.get('piece') == 'stairs' and c['x'] % 1 == 0]
    firsts = [(s_, x, y) for s_, x, y in spots if (s_, x - 1, y) not in set(spots)]
    sheet = Image.new('RGB', (3 * 404, ((len(firsts) + 2) // 3) * 200), (24, 26, 30))
    dr = ImageDraw.Draw(sheet)
    for i, (side, x, y) in enumerate(firsts):
        w, h = P.SIZE[side]
        ref = np.array(Image.open(SRC / f'hgss/{side}/hgss-render.png').convert('RGB'))
        nat = C.decode(engine, I.MAPS[side], 'ice_path', 'ice_path', w, h)['img']
        box = (max(0, x - 2) * 16, max(0, y - 2) * 16, min(w, x + 4) * 16, min(h, y + 3) * 16)
        X, Y = (i % 3) * 404, (i // 3) * 200
        for k, im in enumerate((ref, nat)):
            sheet.paste(Image.fromarray(im[box[1]:box[3], box[0]:box[2]]).resize(((box[2] - box[0]) * 2, (box[3] - box[1]) * 2), 0), (X + k * 200, Y + 18))
        dr.text((X + 2, Y + 3), f'{side} ({x},{y})-({x + 1},{y}): HGSS | native', fill='white')
    sheet.save(OUT / 'stairs.png')
    names = [n for n in GALLERY if (runtime / f'{n}.png').exists()]
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
