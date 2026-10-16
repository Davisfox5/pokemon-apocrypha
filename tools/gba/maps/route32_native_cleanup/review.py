#!/usr/bin/env python3
"""Coordinate-labelled original / before / after review sheets for the Route 32 cleanup.

Usage: review.py ENGINE  (before = the Codex baseline files from git HEAD~ of the work branch,
or an explicit --before-dir containing the same relative files)
"""
import argparse, subprocess, tempfile, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import sys; HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
from native import Native
ROOT = HERE.parents[3]; HUB = ROOT/'gba/art/route32-native-cleanup'; E = HUB/'evidence'
REF = ROOT/'gba/art/route32-hgss-blocks/source/hgss-reference.png'
FONT = ImageFont.load_default()
FILES = ['data/layouts/JohtoRoute32/map.bin'] + [f'data/tilesets/{p}/route32/{f}' for p in ('primary', 'secondary') for f in ('tiles.png', 'metatiles.bin', 'metatile_attributes.bin')] + [f'data/tilesets/{p}/route32/palettes/{i:02}.pal' for p in ('primary', 'secondary') for i in range(16)]

def baseline_checkout(game, rev):
    tmp = Path(tempfile.mkdtemp(prefix='r32-before-'))
    for f in FILES:
        (tmp/f).parent.mkdir(parents=True, exist_ok=True)
        (tmp/f).write_bytes(subprocess.check_output(['git', '-C', str(game), 'show', f'{rev}:{f}']))
    return tmp

def original():
    ref = Image.open(REF).convert('RGB'); img = Image.new('RGB', (512, 2048), (40, 40, 40)); img.paste(ref.crop((0, 0, 480, 2000)), (16, 16)); return img

def panel(img, x0, y0, w, h, label, Z):
    c = img.crop((x0*16, y0*16, (x0+w)*16, (y0+h)*16)).resize((w*16*Z, h*16*Z), Image.NEAREST)
    p = Image.new('RGB', (c.width+36, c.height+22), (25, 25, 25)); p.paste(c, (36, 22)); d = ImageDraw.Draw(p)
    for i in range(w+1):
        X = 36+i*16*Z; d.line([(X, 22), (X, 22+c.height)], fill=(255, 255, 0) if (x0+i) % 4 == 0 else (255, 255, 255), width=1)
        if i < w: d.text((X+2, 10), str(x0+i), fill=(255, 255, 255), font=FONT)
    for j in range(h+1):
        Y = 22+j*16*Z; d.line([(36, Y), (36+c.width, Y)], fill=(255, 255, 0) if (y0+j) % 4 == 0 else (255, 255, 255), width=1)
        if j < h: d.text((2, Y+2), str(y0+j), fill=(255, 255, 255), font=FONT)
    d.text((40, 0), label, fill=(255, 255, 0), font=FONT); return p

def triptych(imgs, labels, x0, y0, w, h, Z, out):
    ps = [panel(i, x0, y0, w, h, l, Z) for i, l in zip(imgs, labels)]
    s = Image.new('RGB', (sum(p.width for p in ps)+8*(len(ps)-1), ps[0].height), (25, 25, 25)); X = 0
    for p in ps: s.paste(p, (X, 0)); X += p.width+8
    s.save(out)

REGIONS = {  # name: (x0, y0, w, h, zoom)
    'gate-shadow': (0, 9, 9, 7, 6), 'cave-mouth': (11, 114, 8, 6, 6), 'rock-column-end': (22, 59, 6, 7, 6),
    'north-south-stairs': (3, 84, 9, 9, 6), 'pier-arm-junction': (11, 69, 11, 12, 5), 'west-pillar': (7, 68, 7, 12, 6),
    'pylon': (21, 68, 9, 9, 6), 'railway-posts': (5, 64, 14, 7, 5), 'flowers': (11, 4, 9, 11, 5), 'lower-pier': (15, 77, 10, 12, 5),
    'upper-dock': (14, 61, 8, 6, 6),
}

def main():
    p = argparse.ArgumentParser(); p.add_argument('game', type=Path); p.add_argument('--before-rev', default='HEAD'); a = p.parse_args()
    E.mkdir(parents=True, exist_ok=True)
    after = Native(a.game); before_dir = baseline_checkout(a.game, a.before_rev); before = Native(before_dir)
    imgs = [original(), before.render(), after.render()]
    imgs[1].save(E/'native-before-1x.png'); imgs[2].save(E/'native-after-1x.png'); imgs[0].save(E/'original-registered-1x.png')
    labels = ['Original HGSS (registered +1,+1)', 'Before (Codex 7049fd5d)', 'After']
    # whole map at 1x in three columns plus 16-row strips at 2x
    whole = Image.new('RGB', (512*3+40, 2048+20), (25, 25, 25)); d = ImageDraw.Draw(whole)
    for i, (im, l) in enumerate(zip(imgs, labels)): whole.paste(im, (i*(512+20), 20)); d.text((i*(512+20), 4), l, fill=(255, 255, 0), font=FONT)
    whole.save(E/'whole-map-original-before-after.png')
    for y0 in range(0, 128, 16): triptych(imgs, labels, 0, y0, 32, 16, 2, E/f'strip-{y0:03d}.png')
    for name, (x0, y0, w, h, Z) in REGIONS.items(): triptych(imgs, labels, x0, y0, w, h, Z, E/f'detail-{name}.png')
    # changed cells
    diff = [(x, y, f'{before.mid(x,y):03x}/{before.coll(x,y)}.{before.elev(x,y)}', f'{after.mid(x,y):03x}/{after.coll(x,y)}.{after.elev(x,y)}') for y in range(128) for x in range(32) if int(before.grid[y, x]) != int(after.grid[y, x])]
    coll = [(x, y, b, c) for x, y, b, c in diff if b.split('/')[1] != c.split('/')[1]]
    # pixel diff of the renders
    pd = (np.array(imgs[1]).astype(int) != np.array(imgs[2]).astype(int)).any(2)
    cells = sorted({(int(x)//16, int(y)//16) for y, x in zip(*np.nonzero(pd))})
    json.dump({'changed_layout_cells': len(diff), 'collision_or_elevation_changes': coll, 'cells_with_pixel_changes': len(cells), 'pixel_changed_cells': cells, 'layout_changes': diff}, open(E/'cell-diff.json', 'w'), indent=1)
    print('layout cells changed', len(diff), 'collision/elevation changes', len(coll), 'cells with pixel changes', len(cells))

if __name__ == '__main__': main()
