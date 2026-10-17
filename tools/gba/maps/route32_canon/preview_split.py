#!/usr/bin/env python3
"""Original / native sheets for the two-map Route 32 build. Usage: preview_split.py ENGINE RIP_DIR OUT_DIR LABEL"""
import sys, struct
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parent/'route32_native_cleanup'))
from native import Part, PRIMARY_GLYPHS, SECONDARY_GLYPHS
eng, rip, out, label = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]; out.mkdir(parents=True, exist_ok=True)
F = ImageFont.load_default(); SPLIT = 78
prim = Part(eng/'data/tilesets/primary/route32', PRIMARY_GLYPHS, 0)
def render(sec, grid):
    parts = [prim, sec]; cache = {}; img = np.zeros((grid.shape[0]*16, grid.shape[1]*16, 3), np.uint8)
    def mt(m):
        if m in cache: return cache[m]
        out_ = np.zeros((16, 16, 3), np.uint8); out_[:] = prim.pals[0][0]
        e = parts[m >= 512].blocks[m-512 if m >= 512 else m]
        for layer in range(2):
            for q in range(4):
                v = e[layer*4+q]; t = v & 1023; b = v >> 12
                g = parts[t >= 512].glyphs[t-512 if t >= 512 else t]
                if v & 1024: g = g[:, ::-1]
                if v & 2048: g = g[::-1]
                cols = np.array(parts[b >= 6].pals[b], np.uint8); ys, xs = np.nonzero(g)
                out_[(q//2)*8+ys, (q % 2)*8+xs] = cols[g[ys, xs]]
        cache[m] = out_; return out_
    for y in range(grid.shape[0]):
        for x in range(grid.shape[1]): img[y*16:y*16+16, x*16:x*16+16] = mt(int(grid[y, x] & 1023))
    return img
gN = np.fromfile(eng/'data/layouts/JohtoRoute32/map.bin', '<u2').reshape(-1, 32); gS = np.fromfile(eng/'data/layouts/JohtoRoute32South/map.bin', '<u2').reshape(-1, 32)
nat = np.concatenate([render(Part(eng/'data/tilesets/secondary/route32', SECONDARY_GLYPHS, 512), gN), render(Part(eng/'data/tilesets/secondary/route32_south', SECONDARY_GLYPHS, 512), gS)], 0)
var = Image.fromarray(nat); var.save(out/'native-1x.png')
orig = Image.open(rip/'rectified.png').convert('RGB')
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
