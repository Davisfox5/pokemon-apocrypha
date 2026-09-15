#!/usr/bin/env python3
"""Adult Silver overworld walker — recolor of the GSRIVEL (teen Silver) model.

Matches battle direction B: charcoal-indigo longcoat, crimson shoulder
mantle, red hair kept from the vanilla walker. Palette-driven where
possible; the mantle is painted per frame on the top rows of the torso.

Vanilla GSRIVEL palette (mmodel 58):
  1-4,9 hair reds | 5 black | 6,11 skin | 7 shine | 8 jacket purple accent
  10 eye white | 12 jacket shadow | 13 jacket lit | 14 jacket outline
  15 unused
"""
from PIL import Image
import os, sys

S = os.path.dirname(os.path.abspath(__file__))
SRC = S + "/ow_src/mmodel_058.png"

JACKET = {12, 13, 14}   # 8 is dual-used in the hair - leave it
CRIMSON_I = 15   # 15 was unused in vanilla

NEWPAL = {
    12: (41, 36, 66),    # coat shadow
    13: (66, 57, 107),   # coat lit
    14: (16, 12, 28),    # coat outline
    15: (140, 24, 49),   # crimson mantle (was unused)
}

def main():
    im = Image.open(SRC)
    w, h = im.size
    nf = w // 32
    px = im.load()
    # per-frame mantle: jacket pixels in the top 3 torso rows -> crimson
    for f in range(nf):
        x0 = f * 32
        rows = [y for y in range(32)
                if any(px[x0+x, y] in JACKET for x in range(32))]
        if not rows:
            continue
        top = min(rows)
        for y in range(top, min(top+3, 32)):
            for x in range(32):
                v = px[x0+x, y]
                if v in (12, 13):
                    px[x0+x, y] = CRIMSON_I
                # 14 outline stays outline
        # front frames (2+ eye-white px): white shirt sliver under the mantle
        eyes = sum(1 for y in range(32) for x in range(32) if px[x0+x, y] == 10)
        if eyes >= 2:
            xs = [x for y in range(32) for x in range(32) if px[x0+x, y] == 10]
            cx = sum(xs) // len(xs)
            for y in range(top+3, min(top+5, 32)):
                for x in range(max(0, cx-1), min(32, cx+3)):
                    if px[x0+x, y] in (12, 13):
                        px[x0+x, y] = 10
    pal = im.getpalette()
    for i, c in NEWPAL.items():
        pal[i*3:i*3+3] = list(c)
    im.putpalette(pal)
    im.save(S + "/silver_ow.png")

    # preview at 4x on neutral ground
    rgba = im.convert("RGBA"); rp = rgba.load(); q = im.load()
    for y in range(h):
        for x in range(w):
            if q[x, y] == 0:
                rp[x, y] = (0, 0, 0, 0)
    bg = Image.new("RGBA", (w, h), (52, 52, 60, 255))
    bg.paste(rgba, (0, 0), rgba)
    bg.resize((w*4, h*4), Image.NEAREST).save(S + "/silver_ow_prev.png")
    print(f"ok: {nf} frames")

if __name__ == "__main__":
    main()
