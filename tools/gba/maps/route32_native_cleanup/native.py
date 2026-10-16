"""Direct native Route 32 source editing: indexed glyphs, metatiles, attributes and layout.

Edits the committed Porymap source in place (tiles.png, metatiles.bin,
metatile_attributes.bin, map.bin).  No generator is replayed; every change is a
small, listed local edit that Porymap could also make by hand.
"""
import hashlib, json, struct
from pathlib import Path
import numpy as np
from PIL import Image

PRIMARY_GLYPHS = 512
SECONDARY_GLYPHS = 496
ANIMATED_PRIMARY = set(range(1, 93))   # Cherrygrove sea animation overwrites VRAM tiles 1..92
LAYOUT_W, LAYOUT_H = 32, 128

def palette(path):
    return [tuple(map(int, line.split())) for line in Path(path).read_text().splitlines()[3:19]]

class Part:
    def __init__(self, folder, count, base):
        self.folder = Path(folder); self.base = base; self.count = count
        self.png = Image.open(self.folder/'tiles.png')
        assert self.png.mode == 'P', self.png.mode
        arr = np.array(self.png)
        h, w = arr.shape
        self.cols = w//8
        self.glyphs = [arr[(i//self.cols)*8:(i//self.cols)*8+8, (i%self.cols)*8:(i%self.cols)*8+8].copy()%16 for i in range(count)]
        self.pals = [palette(self.folder/'palettes'/f'{n:02}.pal') for n in range(16)]
        data = (self.folder/'metatiles.bin').read_bytes()
        self.blocks = [list(e) for e in struct.iter_unpack('<8H', data)]
        self.attrs = list(struct.unpack('<'+'H'*(len(data)//16), (self.folder/'metatile_attributes.bin').read_bytes()))

    def save(self):
        arr = np.array(self.png)
        for i, g in enumerate(self.glyphs):
            arr[(i//self.cols)*8:(i//self.cols)*8+8, (i%self.cols)*8:(i%self.cols)*8+8] = g
        out = Image.fromarray(arr.astype(np.uint8), 'P'); out.putpalette(self.png.getpalette())
        out.save(self.folder/'tiles.png')
        (self.folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H', *b) for b in self.blocks))
        (self.folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(self.attrs), *self.attrs))

class Native:
    def __init__(self, game, primary='route32', secondary='route32', layout='JohtoRoute32'):
        self.game = Path(game)
        self.parts = [Part(self.game/'data/tilesets/primary'/primary, PRIMARY_GLYPHS, 0),
                      Part(self.game/'data/tilesets/secondary'/secondary, SECONDARY_GLYPHS, 512)]
        self.layout_dir = self.game/'data/layouts'/layout
        self.grid = np.fromfile(self.layout_dir/'map.bin', '<u2').reshape(LAYOUT_H, LAYOUT_W).copy()
        self.log = []

    # ---- glyphs -------------------------------------------------------
    def glyph(self, tid):
        p = self.parts[tid >= 512]; return p.glyphs[tid - p.base]
    def set_glyph(self, tid, arr):
        p = self.parts[tid >= 512]; p.glyphs[tid - p.base] = np.array(arr, np.uint8) % 16
    def bank_colors(self, bank):
        return self.parts[bank >= 6].pals[bank]
    def referenced_glyphs(self):
        used = set()
        for p in self.parts:
            for b in p.blocks:
                for v in b: used.add(v & 1023)
        return used
    def free_static_glyphs(self):
        used = self.referenced_glyphs()
        free = [i for i in range(1, PRIMARY_GLYPHS) if i not in used and i not in ANIMATED_PRIMARY]
        free += [512 + i for i in range(SECONDARY_GLYPHS) if 512 + i not in used]
        return free
    def alloc_glyph(self, arr, bank=None, note=''):
        """Reuse an identical glyph (with flips) when one exists, else take a free static slot."""
        arr = np.array(arr, np.uint8) % 16
        for tid in self.referenced_glyphs():
            g = self.glyph(tid)
            for h in (0, 1):
                for v in (0, 1):
                    c = g[:, ::-1] if h else g
                    c = c[::-1, :] if v else c
                    if np.array_equal(c, arr): return tid, h, v
        free = self.free_static_glyphs()
        if not free: raise RuntimeError('no free static glyph')
        tid = free[0]; self.set_glyph(tid, arr)
        # mark as referenced by a placeholder so successive allocs do not collide
        self._reserved = getattr(self, '_reserved', set()); self._reserved.add(tid)
        self.log.append({'glyph': tid, 'bank': bank, 'note': note})
        return tid, 0, 0
    def referenced_glyphs(self):
        used = set(getattr(self, '_reserved', set()))
        for p in self.parts:
            for b in p.blocks:
                for v in b: used.add(v & 1023)
        return used

    # ---- metatiles ----------------------------------------------------
    def entries(self, mid):
        p = self.parts[mid >= 512]; return p.blocks[mid - p.base]
    def attr(self, mid):
        p = self.parts[mid >= 512]; return p.attrs[mid - p.base]
    def set_entries(self, mid, entries, attr=None):
        p = self.parts[mid >= 512]; p.blocks[mid - p.base] = [int(v) & 0xffff for v in entries]
        if attr is not None: p.attrs[mid - p.base] = int(attr)
    def used_metatiles(self):
        return set(int(v) for v in np.unique(self.grid & 1023))
    def free_primary_metatiles(self):
        """Blank (all-zero) primary catalogue entries that no layout cell uses; existing pieces are never recycled."""
        used = self.used_metatiles() | set(getattr(self, '_reserved_m', set()))
        return [m for m in range(1, PRIMARY_GLYPHS) if m not in used and not any(self.parts[0].blocks[m])]
    def alloc_metatile(self, entries, attr, note=''):
        mid = self.free_primary_metatiles()[0]
        self._reserved_m = getattr(self, '_reserved_m', set()); self._reserved_m.add(mid)
        self.set_entries(mid, entries, attr); self.log.append({'metatile': mid, 'note': note})
        return mid
    @staticmethod
    def entry(tid, bank, h=0, v=0):
        return (tid & 1023) | (h << 10) | (v << 11) | (bank << 12)
    @staticmethod
    def hflip_entries(entries):
        """Mirror a metatile horizontally: swap quadrant columns and toggle hflip."""
        order = [1, 0, 3, 2, 5, 4, 7, 6]
        return [entries[i] ^ 1024 if entries[i] & 1023 else entries[i] for i in order]

    # ---- layout -------------------------------------------------------
    def mid(self, x, y): return int(self.grid[y, x] & 1023)
    def coll(self, x, y): return int((self.grid[y, x] >> 10) & 3)
    def elev(self, x, y): return int(self.grid[y, x] >> 12)
    def put(self, x, y, mid, coll=None, elev=None, note=''):
        old = int(self.grid[y, x])
        c = old >> 10 & 3 if coll is None else coll
        e = old >> 12 if elev is None else elev
        self.grid[y, x] = (mid & 1023) | (c << 10) | (e << 12)
        self.log.append({'cell': [x, y], 'from': f'{old & 1023:03x}/{old >> 10 & 3}.{old >> 12}', 'to': f'{mid:03x}/{c}.{e}', 'note': note})

    # ---- color --------------------------------------------------------
    def quantize(self, rgb, bank, mask=None):
        """Map an 8x8 RGB block to bank indices (1..15).  mask False -> index 0 (transparent)."""
        cols = np.array(self.bank_colors(bank)[1:], float)
        shape = np.array(rgb).shape[:2]
        px = np.array(rgb, float).reshape(-1, 3)
        d = ((px[:, None, :] - cols[None]) ** 2).sum(2)
        idx = d.argmin(1) + 1; err = np.sqrt(d.min(1))
        idx = idx.reshape(shape); err = err.reshape(shape)
        if mask is not None:
            idx = np.where(mask, idx, 0); err = np.where(mask, err, 0)
        return idx.astype(np.uint8), float(err.mean()), float(err.max())
    def best_bank(self, rgb, banks, mask=None):
        best = None
        for b in banks:
            idx, mean, mx = self.quantize(rgb, b, mask)
            if best is None or mean < best[1]: best = (b, mean, mx, idx)
        return best

    # ---- rendering (static, both layers) --------------------------------
    def render_metatile(self, mid):
        out = np.zeros((16, 16, 3), np.uint8); out[:] = self.bank_colors(0)[0]
        e = self.entries(mid)
        for layer in range(2):
            for q in range(4):
                v = e[layer*4+q]; tid = v & 1023; bank = v >> 12
                g = self.glyph(tid) if (tid < 512 and tid < PRIMARY_GLYPHS) or (tid >= 512 and tid-512 < SECONDARY_GLYPHS) else None
                if g is None: continue
                if v & 1024: g = g[:, ::-1]
                if v & 2048: g = g[::-1, :]
                cols = np.array(self.bank_colors(bank), np.uint8)
                ys, xs = np.nonzero(g)
                out[(q//2)*8+ys, (q%2)*8+xs] = cols[g[ys, xs]]
        return out
    def render(self):
        cache = {}; img = np.zeros((LAYOUT_H*16, LAYOUT_W*16, 3), np.uint8)
        for y in range(LAYOUT_H):
            for x in range(LAYOUT_W):
                m = self.mid(x, y)
                if m not in cache: cache[m] = self.render_metatile(m)
                img[y*16:y*16+16, x*16:x*16+16] = cache[m]
        return Image.fromarray(img)

    # ---- persistence --------------------------------------------------
    def save(self):
        for p in self.parts: p.save()
        self.grid.astype('<u2').tofile(self.layout_dir/'map.bin')
    def source_hashes(self):
        files = ['data/layouts/JohtoRoute32/map.bin']
        for part in ('primary', 'secondary'):
            for f in ('tiles.png', 'metatiles.bin', 'metatile_attributes.bin'):
                files.append(f'data/tilesets/{part}/route32/{f}')
        return {f: hashlib.sha256((self.game/f).read_bytes()).hexdigest() for f in files}
