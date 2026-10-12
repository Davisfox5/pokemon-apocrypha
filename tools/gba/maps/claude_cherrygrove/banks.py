"""Reduce RGBA scenery to 15-colour GBA palette banks.

A `Bank` collects the RGBA assets that must share one palette, computes a 15-colour
palette (exact when the assets use 15 colours or fewer, otherwise median-cut snapped
back to real source colours) and returns indexed `Canvas` objects for the map compiler.
"""
from __future__ import annotations
import numpy as np
from PIL import Image
from .pixel import Palette, Canvas

class Bank:
    def __init__(self, bank: int, name: str, pool: str):
        assert pool in ('primary', 'secondary')
        self.bank, self.name, self.pool = bank, name, pool
        self.assets: dict[str, np.ndarray] = {}
        self.palette: Palette | None = None
        self.fixed: list[tuple[int, int, int]] = []   # colours that must survive quantisation

    def add(self, name, rgba):
        self.assets[name] = np.asarray(rgba, dtype=np.uint8); return self

    def keep(self, *colors):
        self.fixed += [tuple(int(v) for v in c) for c in colors]; return self

    def _colors(self):
        px = np.concatenate([a[a[..., 3] > 0][:, :3] for a in self.assets.values()]) if self.assets else np.zeros((0, 3), np.uint8)
        u, n = np.unique(px, axis=0, return_counts=True)
        return [tuple(int(v) for v in c) for c in u], n

    def build(self):
        colors, counts = self._colors()
        if len(colors) <= 15:
            pal = colors
        else:
            fixed = [c for c in self.fixed if c in colors]
            budget = 15 - len(fixed)
            rest = [c for c in colors if c not in fixed]
            # median-cut on the actual pixel population, then snap each entry to the nearest real colour
            pxs = np.concatenate([np.repeat(np.array([c], np.uint8), int(n), axis=0) for c, n in zip(colors, counts) if c not in fixed])
            im = Image.fromarray(pxs.reshape(1, -1, 3)).quantize(colors=budget, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
            q = np.array(im.getpalette()[:budget * 3]).reshape(-1, 3)
            snapped = []
            arr = np.array(rest, dtype=np.int32)
            for c in q:
                i = int(((arr - c) ** 2).sum(1).argmin()); s = rest[i]
                if s not in snapped and s not in fixed: snapped.append(s)
            pal = fixed + snapped
        pal = pal[:15]
        self.palette = Palette(self.bank, pal, [f'c{i}' for i in range(len(pal))])
        arr = np.array(pal, dtype=np.int32)
        out = {}
        for name, a in self.assets.items():
            c = Canvas(a.shape[1], a.shape[0], self.palette)
            m = a[..., 3] > 0
            if m.any():
                flat = a[m][:, :3].astype(np.int32)
                idx = ((flat[:, None, :] - arr[None, :, :]) ** 2).sum(-1).argmin(1) + 1
                c.px[m] = idx
            c.pool = self.pool
            out[name] = c
        return out

def recolor(pal: Palette, bank: int, fn) -> Palette:
    """A new bank with every colour passed through fn(rgb) -> rgb (same slots, so tiles are shared)."""
    return Palette(bank, [fn(c) for c in pal.colors], [f'c{i}' for i in range(len(pal.colors))], slots=pal.slots)

def hue_shift(rgb, hue_deg, sat=1.0, val=1.0):
    import colorsys
    r, g, b = [v / 255 for v in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    h = (h + hue_deg / 360.0) % 1.0
    r, g, b = colorsys.hsv_to_rgb(h, min(1, s * sat), min(1, v * val))
    return (int(r * 255), int(g * 255), int(b * 255))
