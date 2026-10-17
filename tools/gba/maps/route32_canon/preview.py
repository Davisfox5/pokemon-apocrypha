#!/usr/bin/env python3
"""Original (rectified HGSS) / native comparison sheets for a 32x160 Route 32 build.
Usage: preview.py ENGINE RIP_DIR OUT_DIR LABEL"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parent/'route32_native_cleanup'))
import native as nat; nat.LAYOUT_H = 160
from native import Native
eng, rip, out, label = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]; out.mkdir(parents=True, exist_ok=True)
F = ImageFont.load_default()
orig = Image.open(rip/'rectified.png').convert('RGB'); var = Native(eng).render(); var.save(out/'native-1x.png')
imgs = [orig, var]; labels = ['Original HGSS (rectified, sprites removed)', label]
def panel(img, x0, y0, w, h, Z, text):
    c = img.crop((x0*16, y0*16, (x0+w)*16, (y0+h)*16)).resize((w*16*Z, h*16*Z), Image.NEAREST)
    p = Image.new('RGB', (c.width+36, c.height+22), (25, 25, 25)); p.paste(c, (36, 22)); d = ImageDraw.Draw(p)
    for i in range(w+1):
        X = 36+i*16*Z; d.line([(X, 22), (X, 22+c.height)], fill=(255, 255, 0) if (x0+i) % 4 == 0 else (80, 80, 80))
        if i < w: d.text((X+2, 10), str(x0+i), fill=(255, 255, 255), font=F)
    for j in range(h+1):
        Y = 22+j*16*Z; d.line([(36, Y), (36+c.width, Y)], fill=(255, 255, 0) if (y0+j) % 4 == 0 else (80, 80, 80))
        if j < h: d.text((2, Y+2), str(y0+j), fill=(255, 255, 255), font=F)
    d.text((40, 0), text, fill=(255, 255, 0), font=F); return p
def sheet(x0, y0, w, h, Z, name):
    ps = [panel(i, x0, y0, w, h, Z, l) for i, l in zip(imgs, labels)]
    s = Image.new('RGB', (sum(p.width for p in ps)+8, ps[0].height), (25, 25, 25)); X = 0
    for p in ps: s.paste(p, (X, 0)); X += p.width+8
    s.save(out/f'{name}.png')
whole = Image.new('RGB', (512*2+20, 2560+20), (25, 25, 25)); d = ImageDraw.Draw(whole)
for i, (im, l) in enumerate(zip(imgs, labels)): whole.paste(im, (i*532, 20)); d.text((i*532, 4), l, fill=(255, 255, 0), font=F)
whole.save(out/'whole-map.png')
for y0 in range(0, 160, 32): sheet(0, y0, 32, 32, 3, f'strip-{y0:03d}')
print('ok', out)
