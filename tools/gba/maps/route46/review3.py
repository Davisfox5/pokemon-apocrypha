"""Coordinate-labelled review sheets for Route 46.

    python3 tools/gba/maps/route46/review3.py ENGINE_CHECKOUT

Whole map: decoded HGSS reference beside the native decode. Detail sheets: the same pair,
numbered by native cell, at 2x for the regions listed in REGIONS. The seam sheet joins Route
46's east end to Route 45's west columns by its foot, HGSS beside native, as a player crossing
sees them (Route 45's HGSS reference and its native decode from the checkout, equal to its
committed decode, see check3.py). Native is evidence/pack3/native.png (decoded, equal to the
installed map and to Porymap's export, see check3.py and porymap.py). Writes evidence/review3/.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import trace as T                                   # noqa: E402
import check3 as C                                  # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route-46'
EV = ART / 'evidence'
OUT = EV / 'review3'
NB_REF = ROOT / 'gba/art/route-45/source/hgss/hgss-reference-true-heights.png'
REGIONS = {  # name: (x0, y0, x1, y1) in cells
    'dark-cave-north-lawn': (0, 0, 32, 24), 'terraces-rock-climb': (0, 16, 32, 42), 'tall-grass-road-gate': (0, 38, 32, 64),
}

def pair(ref, nat, box, scale, title):
    x0, y0, x1, y1 = box
    a = T.numbered(ref, x0, y0, x1, y1, scale, title=f'HGSS (decoded land_data 113-114): {title}')
    b = T.numbered(nat, x0, y0, x1, y1, scale, title=f'Native (installed decode): {title}')
    out = Image.new('RGB', (a.width + b.width + 12, max(a.height, b.height)), (24, 26, 30))
    out.paste(a, (0, 0)); out.paste(b, (a.width + 12, 0))
    return out

def seam(ref, nat, engine):
    """Route 46's columns 16-31 beside Route 45's columns 0-15, rows 0-31 of Route 46 (Route 45's
    128-159), HGSS above native, cells numbered in Route 46's frame (Route 45's x 0-15 is Route 46's
    32-47)."""
    nref = np.array(Image.open(NB_REF).convert('RGB'))
    nnat = C.decode(engine, *C.LAYOUTS['route45'])[0]
    rows = []
    for m, r, label in ((nref, ref, 'HGSS: Route 46 | Route 45'), (nnat, nat, 'Native: Route 46 | Route 45 as committed')):
        joined = np.concatenate([r[:512, 256:512], m[128 * 16:160 * 16, :256]], 1)
        img = Image.fromarray(joined).resize((joined.shape[1] * 2, joined.shape[0] * 2), Image.Resampling.NEAREST)
        d = ImageDraw.Draw(img)
        for i in range(32):
            d.line((i * 32, 0, i * 32, img.height), fill=(60, 60, 70))
            d.text((i * 32 + 2, 2), str(16 + i), fill='white', stroke_width=1, stroke_fill='black')
        for j in range(32):
            d.line((0, j * 32, img.width, j * 32), fill=(60, 60, 70))
            d.text((2, j * 32 + 3), str(j), fill='white', stroke_width=1, stroke_fill='black')
        d.line((512, 0, 512, img.height), fill=(255, 0, 255), width=2)
        head = Image.new('RGB', (img.width, 22), (24, 26, 30))
        ImageDraw.Draw(head).text((4, 4), f'{label}; the magenta line is the seam (Route 46 (x, y) = Route 45 (x - 32, y + 128))', fill='white')
        col = Image.new('RGB', (img.width, img.height + 22), (24, 26, 30))
        col.paste(head, (0, 0)); col.paste(img, (0, 22))
        rows.append(col)
    out = Image.new('RGB', (rows[0].width * 2 + 12, rows[0].height), (24, 26, 30))
    out.paste(rows[0], (0, 0)); out.paste(rows[1], (rows[0].width + 12, 0))
    return out

def main(engine):
    OUT.mkdir(parents=True, exist_ok=True)
    ref = np.array(Image.open(ART / 'source/hgss/hgss-reference-true-heights.png').convert('RGB'))
    nat = np.array(Image.open(EV / 'pack3/native.png').convert('RGB'))
    pair(ref, nat, (0, 0, 32, 64), 1, 'whole route, cells x0-31 y0-63').save(OUT / 'whole.png')
    seam(ref, nat, engine).save(OUT / 'route45-seam.png')
    for name, box in REGIONS.items():
        pair(ref, nat, box, 2, f'{name}, cells x{box[0]}-{box[2] - 1} y{box[1]}-{box[3] - 1}').save(OUT / f'{name}.png')
    print('review sheets in', OUT)

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
