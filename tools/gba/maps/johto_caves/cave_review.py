"""Coordinate-labelled review sheets for a Johto cave, and its gameplay gallery.

    python3 tools/gba/maps/<cave>/review.py ENGINE_CHECKOUT RUNTIME_DIR

Whole floors: HGSS's render beside the installed native decode (cave_check's decode, equal to the
packer and to Porymap's export), numbered by cell, with and without the grid. Detail sheets at 2x over
each floor's cave, in pieces of at most 34 cells a side. The town's mouth (decoded from the checkout,
the mouth cell outlined). Every door, hole and ladder, and every stair flight, HGSS beside native.
Gallery: runtime.py's captures. Writes evidence/review/.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
import cave                                         # noqa: E402
import cave_pack as P                               # noqa: E402
import cave_install as I                            # noqa: E402
import cave_check as C                              # noqa: E402
sys.path.insert(1, str(HERE.parent / 'route46'))
from trace import numbered                          # noqa: E402  (route46/trace.py: numbered cell grid)

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art' / cave.ART
SRC, EV = ART / 'source', ART / 'evidence'
OUT = EV / 'review'
PIECE = 34

def pair(a, b, gap=12):
    out = Image.new('RGB', (a.width + b.width + gap, max(a.height, b.height)), (24, 26, 30))
    out.paste(a, (0, 0)); out.paste(b, (a.width + gap, 0))
    return out

def sheet(tiles, cols):
    cw, chh = max(t.width for t in tiles), max(t.height for t in tiles)
    s = Image.new('RGB', (cols * (cw + 8), ((len(tiles) + cols - 1) // cols) * (chh + 8)), (24, 26, 30))
    for i, t in enumerate(tiles):
        s.paste(t, ((i % cols) * (cw + 8), (i // cols) * (chh + 8)))
    return s

def labelled(a, b, text):
    t = Image.new('RGB', (a.width * 2 + 6, a.height + 14), (24, 26, 30))
    t.paste(a, (0, 14)); t.paste(b, (a.width + 6, 14))
    ImageDraw.Draw(t).text((2, 1), text, fill='white')
    return t

def main(engine, runtime):
    OUT.mkdir(parents=True, exist_ok=True)
    doors, flights = [], []
    from scipy import ndimage
    for side, name in I.MAPS.items():
        w, h = P.SIZE[side]
        ref = np.array(Image.open(SRC / f'hgss/{side}/hgss-render.png').convert('RGB'))
        nat = C.floor(engine, name, side)['img']
        pair(numbered(ref, 0, 0, w, h, 1, title=f'HGSS {side} (decoded land_data, area bank {cave.AREA_BANK})'),
             numbered(nat, 0, 0, w, h, 1, title=f'Native {name} (installed decode)')).save(OUT / f'{side}-whole.png')
        pair(Image.fromarray(ref), Image.fromarray(nat)).save(OUT / f'{side}-hgss-beside-native.png')
        led = json.loads((SRC / f'assemble/{side}-ledger.json').read_text())['cells']
        cells = [(c['x'], c['y']) for c in led if not c['void']]
        xs, ys = [x for x, _ in cells], [y for _, y in cells]
        x0, y0, x1, y1 = max(0, min(xs) - 1), max(0, min(ys) - 1), min(w, max(xs) + 2), min(h, max(ys) + 2)
        nx, ny = -(-(x1 - x0) // PIECE), -(-(y1 - y0) // PIECE)
        for j in range(ny):
            for i in range(nx):
                a0, b0 = x0 + i * (x1 - x0) // nx, y0 + j * (y1 - y0) // ny
                a1, b1 = x0 + (i + 1) * (x1 - x0) // nx, y0 + (j + 1) * (y1 - y0) // ny
                part = '' if nx * ny == 1 else f'-row{j + 1}-col{i + 1}'
                pair(numbered(ref, a0, b0, a1, b1, 2, title=f'HGSS {side} ({a0}-{a1 - 1}, {b0}-{b1 - 1})'),
                     numbered(nat, a0, b0, a1, b1, 2, title=f'Native {name}')).save(OUT / f'{side}-2x{part}.png')
        for c in led:
            if c['kind'] in ('exit', 'hole', 'ladder') or c.get('piece') == 'ladder_top':
                x, y = c['x'], c['y']
                box = np.s_[max(0, y - 3) * 16:min(h, y + 3) * 16, max(0, x - 3) * 16:min(w, x + 4) * 16]
                a, b = Image.fromarray(ref[box]), Image.fromarray(nat[box])
                doors.append(labelled(a.resize((a.width * 2, a.height * 2), Image.NEAREST), b.resize((b.width * 2, b.height * 2), Image.NEAREST),
                                      f'{side} ({x},{y}) {c["kind"]}{" " + c["piece"] if c.get("piece") else ""}'))
        cls = np.load(SRC / f'assemble/{side}-class.npy')
        st = (cls.reshape(h, 16, w, 16) == 6).any((1, 3))
        lab, n = ndimage.label(st)
        for i in range(1, n + 1):
            ys_, xs_ = np.nonzero(lab == i)
            a0, b0, a1, b1 = max(0, xs_.min() - 2), max(0, ys_.min() - 2), min(w, xs_.max() + 3), min(h, ys_.max() + 3)
            box = np.s_[b0 * 16:b1 * 16, a0 * 16:a1 * 16]
            flights.append(labelled(Image.fromarray(ref[box]), Image.fromarray(nat[box]),
                                    f'{side} ({xs_.min()}-{xs_.max()},{ys_.min()}-{ys_.max()})'))
    if doors:
        sheet(doors, 3).save(OUT / 'doors-and-ladders.png')
    if flights:
        sheet(flights, 4).save(OUT / 'stairs.png')
    r, pf, sf, ww, hh = C.ROUTE
    d = C.decode(engine, r, pf, sf, ww, hh)
    cx, cy = cave.TOWN['cell']
    x0, y0 = max(0, cx - 7), max(0, cy - 5)
    im = numbered(d['img'], x0, y0, min(ww, cx + 8), min(hh, cy + 6), 2, title=f'{r}: {cave.NAME} mouth at ({cx},{cy}), now a door')
    dr = ImageDraw.Draw(im)
    px, py = 28 + (cx - x0) * 32, 40 + (cy - y0) * 32
    dr.rectangle((px, py, px + 31, py + 31), outline=(255, 220, 0), width=2)
    im.save(OUT / 'town-mouth.png')
    names = sorted(p.stem for p in runtime.glob('*.png') if not p.stem.startswith('bg-'))
    cols = 4
    g = Image.new('RGB', (cols * 248, ((len(names) + cols - 1) // cols) * 180), (24, 26, 30))
    dr = ImageDraw.Draw(g)
    for i, n in enumerate(names):
        x, y = (i % cols) * 248 + 4, (i // cols) * 180 + 16
        g.paste(Image.open(runtime / f'{n}.png').convert('RGB'), (x, y)); dr.text((x, y - 13), n, fill='white')
    g.save(OUT / 'gameplay-gallery.png')
    print('review sheets:', sorted(p.name for p in OUT.glob('*.png')))
