"""Coordinate-labelled review sheets for a room."""
from PIL import Image, ImageDraw
import numpy as np

def grid(img, blocked=None, k=3, x0=0, y0=0, marks=()):
    a = Image.fromarray(img).resize((img.shape[1] * k, img.shape[0] * k), Image.NEAREST)
    d = ImageDraw.Draw(a)
    W, H = img.shape[1] // 16, img.shape[0] // 16
    for x in range(W + 1): d.line([(x * 16 * k, 0), (x * 16 * k, a.height)], fill=(255, 255, 255))
    for y in range(H + 1): d.line([(0, y * 16 * k), (a.width, y * 16 * k)], fill=(255, 255, 255))
    for y in range(H):
        for x in range(W):
            d.text((x * 16 * k + 2, y * 16 * k + 1), f'{x + x0},{y + y0}', fill=(255, 255, 0))
            if blocked is not None and blocked[y, x]:
                d.rectangle([x * 16 * k + 6 * k, y * 16 * k + 6 * k, x * 16 * k + 10 * k, y * 16 * k + 10 * k], outline=(255, 0, 0))
    for (x, y, t) in marks:
        d.text((x * 16 * k + 2, y * 16 * k + 8 * k), t, fill=(0, 255, 255))
    return a
