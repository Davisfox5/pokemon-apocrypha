"""Violet City as the engine's port commit has it (BASE_REV): its map words and its two private tilesets,
decoded into each cell's two layers.

A cell is (lower, upper, layer type, behaviour): lower the RGB of the metatile's first four entries (its
transparent pixels the backdrop colour, as the hardware draws them), upper the RGBA of the last four,
layer type and behaviour its attribute word. The map word's bits 10-15 (collision, elevation) are the
cell's own.
"""
from __future__ import annotations
import io, struct, subprocess, tarfile, tempfile
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/violet-city-review'
BASE_REV = '42cd9d1a53'                              # the engine commit that ported Violet from codex/johto-editor-consolidation
W, H = 80, 72
LAYOUT = 'data/layouts/VioletCity'
PRIMARY, SECONDARY = 'data/tilesets/primary/violet_city', 'data/tilesets/secondary/violet_city'
NORMAL, COVERED, SPLIT = 0, 1, 2

def read_pal(path):
    return [tuple(map(int, l.split())) for l in path.read_text().splitlines()[3:19]]

def jasc(cols):
    return '\r\n'.join(['JASC-PAL', '0100', '16'] + [f'{c[0]} {c[1]} {c[2]}' for c in cols]) + '\r\n'

def gba(c):
    return tuple((int(v) >> 3) << 3 for v in c)

def base_checkout(engine):
    """The layout and both tilesets at BASE_REV, unpacked in the engine's layout under a temp dir."""
    out = Path(tempfile.mkdtemp(prefix='violet-base-'))
    tar = subprocess.check_output(['git', '-C', str(engine), 'archive', BASE_REV, LAYOUT, PRIMARY, SECONDARY])
    tarfile.open(fileobj=io.BytesIO(tar)).extractall(out)
    return out

def tiles_of(d):
    from PIL import Image
    a = np.array(Image.open(d / 'tiles.png'))
    return [a[y:y + 8, x:x + 8] & 15 for y in range(0, a.shape[0], 8) for x in range(0, a.shape[1], 8)]

class Violet:
    def __init__(self, engine):
        self.engine = Path(engine)
        self.base = base_checkout(self.engine)
        b = (self.base / LAYOUT / 'map.bin').read_bytes()
        self.words = np.array(struct.unpack('<%dH' % (len(b) // 2), b), np.int64).reshape(H, W)
        self.border = list(struct.unpack('<4H', (self.base / LAYOUT / 'border.bin').read_bytes()))
        self.tiles, self.pals, self.blocks, self.attrs = [], [], [], []
        for d in (self.base / PRIMARY, self.base / SECONDARY):
            self.tiles.append(tiles_of(d))
            self.pals.append([read_pal(d / f'palettes/{i:02d}.pal') for i in range(16)])
            self.blocks.append(list(struct.iter_unpack('<8H', (d / 'metatiles.bin').read_bytes())))
            a = (d / 'metatile_attributes.bin').read_bytes()
            self.attrs.append(list(struct.unpack('<%dH' % (len(a) // 2), a)))
        self.banks = [self.pals[0][b] for b in range(6)] + [self.pals[1][b] for b in range(6, 13)]
        self.backdrop = tuple(self.pals[0][0][0])
        self._cells = {}

    def block(self, m):
        return self.blocks[int(m >= 512)][m - 512 if m >= 512 else m]

    def attr(self, m):
        return self.attrs[int(m >= 512)][m - 512 if m >= 512 else m]

    def tile(self, i):
        t = self.tiles[int(i >= 512)]
        j = i - 512 if i >= 512 else i
        return t[j] if j < len(t) else np.zeros((8, 8), np.uint8)

    def layers(self, m):
        """(lower RGB, upper RGBA) of metatile m."""
        if m in self._cells:
            return self._cells[m]
        low = np.zeros((16, 16, 3), np.uint8); low[...] = self.backdrop
        up = np.zeros((16, 16, 4), np.uint8)
        for layer in (0, 1):
            for q in range(4):
                e = self.block(m)[layer * 4 + q]
                t = self.tile(e & 1023)
                if e & 0x400: t = t[:, ::-1]
                if e & 0x800: t = t[::-1]
                pal = np.array(self.banks[e >> 12], np.uint8)
                sl = np.s_[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
                op = t > 0
                if layer == 0:
                    low[sl][op] = pal[t[op]]
                else:
                    up[sl][op, :3] = pal[t[op]]; up[sl][op, 3] = 255
        self._cells[m] = (low, up)
        return low, up

    def image(self, words=None):
        """The map as the game draws it (upper over lower)."""
        words = self.words if words is None else words
        out = np.zeros((H * 16, W * 16, 3), np.uint8)
        for r in range(H):
            for x in range(W):
                low, up = self.layers(int(words[r, x]) & 1023)
                px = low.copy(); a = up[..., 3] > 0; px[a] = up[..., :3][a]
                out[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16] = px
        return out
