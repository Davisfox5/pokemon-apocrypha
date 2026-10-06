"""Render every asset on a grass ground for inspection."""
import sys
import numpy as np
from PIL import Image

def render(out, assets=None, scale=3, ground=(104, 208, 152)):
    if assets is None:
        from .build import build_assets
        assets, _ = build_assets()
    x = 4; y = 4; row_h = 0; tiles = []
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
