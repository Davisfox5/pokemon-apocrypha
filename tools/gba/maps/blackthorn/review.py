"""Review images for Blackthorn: HGSS reference versus installed native art.

    python3 tools/gba/maps/blackthorn/review.py ENGINE_CHECKOUT

Writes into gba/art/blackthorn-city/evidence/:
    original-native.png   whole city, HGSS land_data render (true heights) | decoded native sections
    reference-grid.png    HGSS render at 2x, numbered cells, decoded HGSS permissions overlaid
    camera-margin.png     native city with the city view's camera margin, as the camera can see it
    review/*.png          region pairs at 2x for close inspection
Run check.py first: it writes evidence/native.png from the engine files.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/blackthorn-city'
EV, SRC = ART / 'evidence', ART / 'source'
REGIONS = {'north-den-pond': (288, 0, 672, 256), 'gym': (288, 192, 672, 448), 'northeast-ice-path': (640, 160, 1024, 416),
           'northwest-cliffs': (0, 160, 384, 416), 'west-town': (96, 416, 480, 672), 'central-town': (320, 560, 704, 816),
           'east-terraces': (640, 416, 1024, 672), 'southwest-bridge': (96, 736, 480, 992), 'southeast-river': (608, 640, 992, 896)}

def grid(img, scale, sections=()):
    big = img.resize((img.width * scale, img.height * scale), Image.Resampling.NEAREST)
    d = ImageDraw.Draw(big)
    n = 16 * scale
    for i in range(img.width // 16):
        d.line((i * n, 0, i * n, big.height), fill=(60, 60, 70))
        d.text((i * n + 2, 2), str(i), fill='white', stroke_width=1, stroke_fill='black')
    for i in range(img.height // 16):
        d.line((0, i * n, big.width, i * n), fill=(60, 60, 70))
        d.text((2, i * n + 3), str(i), fill='white', stroke_width=1, stroke_fill='black')
    for y in sections:
        d.line((0, y * n, big.width, y * n), fill=(255, 220, 0), width=2)
    return big

def main(g):
    ref = Image.open(SRC / 'hgss/hgss-reference-true-heights.png').convert('RGB')
    nat = Image.open(EV / 'native.png').convert('RGB')
    # Whole city side by side.
    out = Image.new('RGB', (ref.width * 2 + 16, ref.height + 28), (28, 32, 38)); d = ImageDraw.Draw(out)
    out.paste(ref, (0, 28)); out.paste(nat, (ref.width + 16, 28))
    d.text((6, 8), 'HGSS land_data chunks 104-107, rendered 1:1 at true heights (HGSS Center and Mart)', fill='white')
    d.text((ref.width + 22, 8), 'Native Gen 3, decoded from the three installed sections (shared Center and Mart)', fill='white')
    out.save(EV / 'original-native.png')
    # Reference grid with the decoded permissions.
    perm = np.load(SRC / 'hgss/hgss-permissions.npz')
    types, coll = perm['types'], perm['collision']
    ov = Image.new('RGBA', ref.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for y in range(64):
        for x in range(64):
            box = (x * 16, y * 16, x * 16 + 15, y * 16 + 15)
            t = int(types[y, x])
            if t in (0x10, 0x15):
                od.rectangle(box, fill=(0, 80, 255, 70))
            elif t == 0x3B:
                od.rectangle(box, fill=(255, 160, 0, 110))
            elif t in (0x69, 0x6E):
                od.rectangle(box, outline=(0, 255, 0, 255), width=2)
            elif coll[y, x] & 0x80:
                od.rectangle(box, fill=(255, 0, 0, 60))
    ri = Image.alpha_composite(ref.convert('RGBA'), ov).convert('RGB')
    gi = grid(ri, 2); d = ImageDraw.Draw(gi)
    d.rectangle((4, gi.height - 30, 620, gi.height - 4), fill=(0, 0, 0))
    d.text((10, gi.height - 24), 'red: blocked   blue: water (Surf)   orange: jump-south ledge   green: door / cave warp', fill='white')
    gi.save(EV / 'reference-grid.png')
    # Camera margin, using the engine's own margin tables.
    t = {k: np.frombuffer((g / f'data/city_views/blackthorn/margin-{k}.bin').read_bytes(), np.uint8) for k in ('north', 'south', 'west', 'east')}
    rock = tuple(int(v) for v in re.search(r'\.rockX = (\d+), \.rockY = (\d+)', (g / 'src/data/city_views/blackthorn.h').read_text()).groups())
    a = np.array(nat); P = 8
    def cell(x, y):
        ix, iy = 0 <= x < 64, 0 <= y < 64
        if ix and iy: return x, y
        s = 255 if not ix and not iy else int(t['west'][y] if x < 0 else t['east'][y] if x >= 64 else t['north'][x] if y < 0 else t['south'][x])
        if s == 255: return rock[0] + (x & 1), rock[1] + (y & 1)
        return (s + (x & 1), y) if not ix else (x, s + (y & 1))
    m = np.zeros(((64 + 2 * P) * 16, (64 + 2 * P) * 16, 3), np.uint8)
    for py in range(64 + 2 * P):
        for px in range(64 + 2 * P):
            x, y = cell(px - P, py - P)
            m[py * 16:py * 16 + 16, px * 16:px * 16 + 16] = a[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
    mi = Image.fromarray(m); d = ImageDraw.Draw(mi)
    d.rectangle((P * 16 - 1, P * 16 - 1, (64 + P) * 16, (64 + P) * 16), outline=(255, 220, 0))
    mi.save(EV / 'camera-margin.png')
    # Region pairs.
    (EV / 'review').mkdir(exist_ok=True)
    for n, b in REGIONS.items():
        w, h = b[2] - b[0], b[3] - b[1]
        o = Image.new('RGB', (w * 4 + 12, h * 2 + 20), (28, 32, 38)); d = ImageDraw.Draw(o)
        o.paste(ref.crop(b).resize((w * 2, h * 2), Image.Resampling.NEAREST), (0, 20))
        o.paste(nat.crop(b).resize((w * 2, h * 2), Image.Resampling.NEAREST), (w * 2 + 12, 20))
        d.text((4, 4), f'HGSS (true heights)   cells x{b[0] // 16}-{b[2] // 16 - 1}, y{b[1] // 16}-{b[3] // 16 - 1}', fill='white')
        d.text((w * 2 + 16, 4), 'Native Gen 3, decoded from the installed sections', fill='white')
        o.save(EV / 'review' / f'{n}.png')
    print('review images written')

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
