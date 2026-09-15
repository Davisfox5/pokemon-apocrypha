"""Tiny indexed-colour pixel authoring kit for Gen 3 style scenery.

Every asset is painted with one 15-colour bank (index 0 is transparent) so the
result drops straight into an Emerald secondary tileset without quantisation.
"""
from __future__ import annotations
import numpy as np

class Palette:
    def __init__(self, bank, colors, names, slots=None):
        assert len(colors) <= 15 and len(colors) == len(names)
        self.bank = bank
        self.colors = [tuple(int(v) for v in c) for c in colors]
        self.slots = list(slots) if slots else list(range(1, len(colors) + 1))
        assert len(self.slots) == len(colors) and 0 not in self.slots
        self.index = {n: self.slots[i] for i, n in enumerate(names)}
        self.by_slot = {self.slots[i]: i for i in range(len(colors))}
    def rgb(self, i):
        return (0, 0, 0) if i not in self.by_slot else self.colors[self.by_slot[i]]
    def gba(self):
        """16 entries; unused slots (including transparent 0) stay black."""
        return [self.rgb(i) for i in range(16)]

class Canvas:
    """(bank, index) pixels; -1 bank means transparent."""
    def __init__(self, w, h, pal: Palette):
        self.w, self.h, self.pal = w, h, pal
        self.px = np.zeros((h, w), dtype=np.int16)  # 0 transparent, else index
    def c(self, name):
        return self.pal.index[name]
    def put(self, x, y, name):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y, x] = self.c(name)
    def rect(self, x, y, w, h, name):
        x0, y0 = max(x, 0), max(y, 0); x1, y1 = min(x + w, self.w), min(y + h, self.h)
        if x1 > x0 and y1 > y0: self.px[y0:y1, x0:x1] = self.c(name)
    def hline(self, x, y, w, name): self.rect(x, y, w, 1, name)
    def vline(self, x, y, h, name): self.rect(x, y, 1, h, name)
    def box(self, x, y, w, h, name):
        self.hline(x, y, w, name); self.hline(x, y + h - 1, w, name)
        self.vline(x, y, h, name); self.vline(x + w - 1, y, h, name)
    def rows(self, x, y, lines, key):
        """Paint an ASCII art block; key maps chars to colour names, '.' transparent, ' ' skip."""
        for dy, line in enumerate(lines):
            for dx, ch in enumerate(line):
                if ch == ' ': continue
                if ch == '.':
                    if 0 <= x + dx < self.w and 0 <= y + dy < self.h: self.px[y + dy, x + dx] = 0
                    continue
                self.put(x + dx, y + dy, key[ch])
    def ellipse(self, cx, cy, rx, ry, name, fill=True):
        for yy in range(int(cy - ry), int(cy + ry) + 1):
            for xx in range(int(cx - rx), int(cx + rx) + 1):
                if ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0:
                    self.put(xx, yy, name)
    def outline(self, name, mask=None):
        """Draw a 1px outline around every opaque region (inside the region border)."""
        src = self.px.copy() if mask is None else mask
        opaque = src != 0
        pad = np.pad(opaque, 1)
        edge = opaque & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
        self.px[edge] = self.c(name)
    def blit(self, other: 'Canvas', x, y):
        h, w = other.px.shape
        for yy in range(h):
            for xx in range(w):
                v = other.px[yy, xx]
                if v: self.put(x + xx, y + yy, other.pal.colors and list(other.pal.index)[v - 1])
    def flip(self):
        c = Canvas(self.w, self.h, self.pal); c.px = self.px[:, ::-1].copy(); return c
    def to_rgba(self):
        out = np.zeros((self.h, self.w, 4), dtype=np.uint8)
        for i in range(1, 16):
            m = self.px == i
            if m.any():
                out[m, :3] = self.pal.rgb(i); out[m, 3] = 255
        return out
    def c(self, name):
        return self.pal.index[name]

def dither(canvas, x, y, w, h, a, b, phase=0):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            canvas.put(xx, yy, a if (xx + yy + phase) % 2 == 0 else b)
