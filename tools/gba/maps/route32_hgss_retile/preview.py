#!/usr/bin/env python3
"""Preview sheets for a retile variant: original HGSS / current cleanup / variant, whole map and 4x regions.
Usage: preview.py VARIANT_ENGINE CLEANUP_ENGINE OUT_DIR LABEL"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'route32_native_cleanup'))
from native import Native
ROOT = Path(__file__).resolve().parents[4]
ve, ce, out, label = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]; out.mkdir(parents=True, exist_ok=True)
F = ImageFont.load_default()
ref = Image.open(ROOT/'gba/art/route32-hgss-blocks/source/hgss-reference.png').convert('RGB')
orig = Image.new('RGB', (512, 2048), (40, 40, 40)); orig.paste(ref.crop((0, 0, 480, 2000)), (16, 16))
cur = Native(ce).render(); var = Native(ve).render(); var.save(out/f'native-{label}-1x.png')
imgs = [orig, cur, var]; labels = ['Original HGSS', 'Current (cleanup 48cefd3d)', label]
def panel(img, x0, y0, w, h, Z, text):
    c = img.crop((x0*16, y0*16, (x0+w)*16, (y0+h)*16)).resize((w*16*Z, h*16*Z), Image.NEAREST)
    p = Image.new('RGB', (c.width+36, c.height+22), (25, 25, 25)); p.paste(c, (36, 22)); d = ImageDraw.Draw(p)
    for i in range(w+1):
        X = 36+i*16*Z; d.line([(X, 22), (X, 22+c.height)], fill=(255, 255, 0) if (x0+i) % 4 == 0 else (90, 90, 90))
        if i < w: d.text((X+2, 10), str(x0+i), fill=(255, 255, 255), font=F)
    for j in range(h+1):
        Y = 22+j*16*Z; d.line([(36, Y), (36+c.width, Y)], fill=(255, 255, 0) if (y0+j) % 4 == 0 else (90, 90, 90))
        if j < h: d.text((2, Y+2), str(y0+j), fill=(255, 255, 255), font=F)
    d.text((40, 0), text, fill=(255, 255, 0), font=F); return p
def sheet(x0, y0, w, h, Z, name):
    ps = [panel(i, x0, y0, w, h, Z, l) for i, l in zip(imgs, labels)]
    s = Image.new('RGB', (sum(p.width for p in ps)+16, ps[0].height), (25, 25, 25)); X = 0
    for p in ps: s.paste(p, (X, 0)); X += p.width+8
    s.save(out/f'{name}.png')
whole = Image.new('RGB', (512*3+40, 2068), (25, 25, 25)); d = ImageDraw.Draw(whole)
for i, (im, l) in enumerate(zip(imgs, labels)): whole.paste(im, (i*532, 20)); d.text((i*532, 4), l, fill=(255, 255, 0), font=F)
whole.save(out/'whole-map.png')
for name, (x0, y0, w, h) in {'north-gate-terraces': (0, 4, 32, 24), 'cliffs-and-stairs': (4, 44, 28, 20), 'railway-docks-pylon': (8, 60, 24, 22), 'lower-pier-center': (10, 82, 22, 30), 'cave': (6, 108, 24, 20)}.items():
    sheet(x0, y0, w, h, 3, f'detail-{name}')
print('ok', out)
