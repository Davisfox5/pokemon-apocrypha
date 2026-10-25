"""Coordinate-labelled review sheets for Route 45.

    python3 tools/gba/maps/route45/review3.py ENGINE_CHECKOUT

Whole map: decoded HGSS reference beside the native decode. Detail sheets: the same pair,
numbered by native cell, at 2x for the regions listed in REGIONS. The seam sheet joins
Blackthorn City's south end to Route 45's north end, HGSS beside native, as a player crossing
sees them (Blackthorn's HGSS reference from its own branch, its native decoded from the
checkout, equal to its committed decode, see check3.py). Native is evidence/pack3/native.png
(decoded, equal to the installed map and to Porymap's export, see check3.py and porymap.py).
Writes evidence/review3/.
"""
from __future__ import annotations
import io, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import trace as T                                   # noqa: E402
import check3 as C                                  # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route-45'
EV = ART / 'evidence'
OUT = EV / 'review3'
NB_REF = 'origin/claude/blackthorn-city:gba/art/blackthorn-city/source/hgss/hgss-reference-true-heights.png'
REGIONS = {  # name: (x0, y0, x1, y1) in cells
    'dark-cave-first-bridges': (0, 0, 32, 24), 'tall-grass-third-bridge': (0, 20, 32, 48),
    'first-cascade-fourth-bridge': (0, 46, 32, 72), 'middle-ledges-fifth-bridge': (0, 70, 32, 96),
    'second-cascade-island': (0, 92, 32, 120), 'third-cascade-pond': (0, 116, 32, 142), 'woods-river-mouth': (0, 136, 32, 160),
}

def pair(ref, nat, box, scale, title):
    x0, y0, x1, y1 = box
    a = T.numbered(ref, x0, y0, x1, y1, scale, title=f'HGSS (decoded land_data 108-112): {title}')
    b = T.numbered(nat, x0, y0, x1, y1, scale, title=f'Native (installed decode): {title}')
    out = Image.new('RGB', (a.width + b.width + 12, max(a.height, b.height)), (24, 26, 30))
    out.paste(a, (0, 0)); out.paste(b, (a.width + 12, 0))
    return out

def seam(ref, nat, engine):
    """Blackthorn rows 48-63 above Route 45 rows 0-15, HGSS beside native, cells numbered in
    Route 45's frame (Blackthorn y 48-63 is Route 45 y -16 to -1)."""
    nref = np.array(Image.open(io.BytesIO(subprocess.check_output(['git', '-C', str(ROOT), 'show', NB_REF]))).convert('RGB'))
    nnat = C.decode(engine, *C.LAYOUTS['blackthorn'])[0]
    cols = []
    for m, r, label in ((nref, ref, 'HGSS: Blackthorn | Route 45'), (nnat, nat, 'Native: Blackthorn as committed | Route 45')):
        joined = np.concatenate([m[48 * 16:64 * 16, :512], r[:256]], 0)
        img = Image.fromarray(joined).resize((joined.shape[1] * 2, joined.shape[0] * 2), Image.Resampling.NEAREST)
        d = ImageDraw.Draw(img)
        for i in range(32):
            d.line((i * 32, 0, i * 32, img.height), fill=(60, 60, 70))
            d.text((i * 32 + 2, 2), str(i), fill='white', stroke_width=1, stroke_fill='black')
        for j in range(32):
            d.line((0, j * 32, img.width, j * 32), fill=(60, 60, 70))
            d.text((2, j * 32 + 3), str(j - 16), fill='white', stroke_width=1, stroke_fill='black')
        d.line((0, 512, img.width, 512), fill=(255, 0, 255), width=2)
        head = Image.new('RGB', (img.width, 22), (24, 26, 30))
        ImageDraw.Draw(head).text((4, 4), f'{label}; the magenta line is the seam (Route 45 y 0 = Blackthorn y 64)', fill='white')
        col = Image.new('RGB', (img.width, img.height + 22), (24, 26, 30))
        col.paste(head, (0, 0)); col.paste(img, (0, 22))
        cols.append(col)
    out = Image.new('RGB', (cols[0].width * 2 + 12, cols[0].height), (24, 26, 30))
    out.paste(cols[0], (0, 0)); out.paste(cols[1], (cols[0].width + 12, 0))
    return out

def main(engine):
    OUT.mkdir(parents=True, exist_ok=True)
    ref = np.array(Image.open(ART / 'source/hgss/hgss-reference-true-heights.png').convert('RGB'))
    nat = np.array(Image.open(EV / 'pack3/native.png').convert('RGB'))
    pair(ref, nat, (0, 0, 32, 160), 1, 'whole route, cells x0-31 y0-159').save(OUT / 'whole.png')
    seam(ref, nat, engine).save(OUT / 'blackthorn-seam.png')
    for name, box in REGIONS.items():
        pair(ref, nat, box, 2, f'{name}, cells x{box[0]}-{box[2] - 1} y{box[1]}-{box[3] - 1}').save(OUT / f'{name}.png')
    print('review sheets in', OUT)

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
