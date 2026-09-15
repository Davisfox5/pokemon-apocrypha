"""Render every asset on a grass ground at 3x for inspection."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from .art import build_all

def render(out, scale=3, ground=(120, 200, 136)):
    assets = build_all()
    x = 4; y = 4; row_h = 0; tiles = []
    W = 4
    for name, c in assets.items():
        rgba = c.to_rgba()
        if x + c.w + 4 > 640: x = 4; y += row_h + 12; row_h = 0
        tiles.append((name, x, y, rgba)); x += c.w + 8; row_h = max(row_h, c.h)
    H = y + row_h + 12
    img = np.zeros((H, 640, 3), dtype=np.uint8); img[:] = ground
    for name, x, y, rgba in tiles:
        h, w = rgba.shape[:2]; m = rgba[..., 3] > 0
        img[y:y+h, x:x+w][m] = rgba[..., :3][m]
    im = Image.fromarray(img).resize((640 * scale, H * scale), Image.Resampling.NEAREST)
    im.save(out); print(out, im.size)

if __name__ == '__main__':
    render(sys.argv[1])
