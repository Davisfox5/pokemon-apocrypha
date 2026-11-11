"""Draw an engine tileset's metatiles to RGBA (Emerald's format: a primary of 512 tiles, 512
metatiles and 6 palettes, a secondary after it). Used to borrow other maps' pieces."""
from __future__ import annotations
from pathlib import Path
import numpy as np
from PIL import Image

def jasc(p):
    lines = Path(p).read_text().splitlines()
    return [tuple(int(v) for v in line.split()) for line in lines[3:3 + int(lines[2])]]

def tiles(d):
    d = Path(d)
    if not (d / 'tiles.png').exists():
        d = next(s for s in sorted(d.iterdir()) if s.is_dir() and (s / 'tiles.png').exists())
    a = np.array(Image.open(d / 'tiles.png'))
    return [a[y:y + 8, x:x + 8] % 16 for y in range(0, a.shape[0], 8) for x in range(0, a.shape[1], 8)], d

def palettes(d):
    return {int(p.stem): jasc(p) for p in sorted((Path(d) / 'palettes').glob('*.pal'))}

class Tileset:
    def __init__(self, primary, secondary, secondary_meta=None, n_tiles=512, n_pals=6, n_meta=512):
        self.pt, pd = tiles(primary)
        self.st, sd = tiles(secondary)
        self.pp, self.sp = palettes(pd), palettes(sd)
        self.n_tiles, self.n_pals, self.n_meta = n_tiles, n_pals, n_meta
        sm = Path(secondary_meta or secondary)
        self.pm = np.fromfile(Path(primary) / 'metatiles.bin', '<u2').reshape(-1, 8)
        self.sm = np.fromfile(sm / 'metatiles.bin', '<u2').reshape(-1, 8)

    def tile(self, t):
        if t < self.n_tiles:
            return self.pt[t] if t < len(self.pt) else None
        t -= self.n_tiles
        return self.st[t] if t < len(self.st) else None

    def meta(self, m, layers=(0, 1)):
        ent = self.pm[m] if m < self.n_meta else self.sm[m - self.n_meta]
        out = np.zeros((16, 16, 4), np.uint8)
        for layer in layers:
            for q in range(4):
                e = int(ent[layer * 4 + q])
                t = self.tile(e & 0x3FF)
                pal = (self.pp if (e >> 12) < self.n_pals else self.sp).get(e >> 12)
                if t is None or pal is None:
                    continue
                if e & 0x400:
                    t = t[:, ::-1]
                if e & 0x800:
                    t = t[::-1]
                oy, ox = (q // 2) * 8, (q % 2) * 8
                cols = np.array([(*pal[c], 255) if c < len(pal) else (0, 0, 0, 0) for c in range(16)], np.uint8)
                blk = out[oy:oy + 8, ox:ox + 8]
                blk[t > 0] = cols[t][t > 0]
        return out
