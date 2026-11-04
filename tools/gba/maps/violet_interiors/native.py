"""Gen 3's own rooms as a source of pieces for Violet's interiors (the Celadon apartments' method:
tools/gba/maps/celadon_elements/apartments_native.py on claude/celadon-city).

A Source is an Emerald or FireRed room in the engine, read from its own layout and tileset pair: per
cell its bottom layer (RGB), top layer (RGBA), behaviour and collision. A piece is a rectangle of its
cells; it goes onto a new room either whole (walls, floors, stairs, anything on the floor it was drawn
on) or as an object laid over the new room's floor by its own pixels (object(): the pixels that are not
the source room's plain floor, and everything on the top layer).
"""
from __future__ import annotations
import json, re, struct, sys
from collections import Counter
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]
import frlg                               # noqa: E402
import tiles as T                         # noqa: E402

ENG = Path('/home/user/engine-r3031')
_L = None

def layouts():
    global _L
    if _L is None:
        _L = {l['name']: l for l in json.loads((ENG / 'data/layouts/layouts.json').read_text())['layouts'] if l}
    return _L

def folder(sym):
    hdr = (ENG / 'src/data/tilesets/headers.h').read_text()
    gfx = (ENG / 'src/data/tilesets/graphics.h').read_text()
    name = sym.replace('gTileset_', '')
    m = re.search(rf'gTileset_{name} =\s*\{{(.*?)\}};', hdr, re.S)
    t = re.search(r'\.tiles = gTilesetTiles_(\w+)', m.group(1)).group(1)
    return re.search(rf'gTilesetTiles_{t}\[\] = INCGFX_U32\("data/tilesets/(?:primary|secondary)/([^/]+)/', gfx).group(1)

class EPair:
    """An Emerald tileset pair, per metatile (bottom RGB, top RGBA) and its attribute."""
    def __init__(self, primary, secondary):
        self.t = T.Tileset(ENG, secondary, primary)
    def quad(self, e):
        tid = e & 1023; bank = e >> 12
        tiles = self.t.tiles[tid >= 512]; idx = tid - 512 if tid >= 512 else tid
        out = np.zeros((8, 8, 4), np.uint8)
        if idx >= len(tiles):
            return out
        cols = np.array(self.t.pals[bank >= 6][bank], np.uint8)
        v = np.array(tiles[idx], int).reshape(8, 8) % 16
        if e & 1024: v = v[:, ::-1]
        if e & 2048: v = v[::-1]
        m = v > 0
        out[m, :3] = cols[v[m]]; out[m, 3] = 255
        return out
    def cell(self, mid):
        part = mid >= 512
        entries = self.t.blocks[part][mid - 512 if part else mid]
        attr = self.t.attrs[part][mid - 512 if part else mid]
        bot = np.zeros((16, 16, 3), np.uint8); bot[...] = self.t.pals[0][0][0]
        top = np.zeros((16, 16, 4), np.uint8)
        for li in range(8):
            q = self.quad(entries[li]); sl = np.s_[(li % 4 // 2) * 8:(li % 4 // 2) * 8 + 8, (li % 2) * 8:(li % 2) * 8 + 8]
            a = q[..., 3] > 0
            if li < 4:
                bot[sl][a] = q[..., :3][a]
            else:
                top[sl][a] = q[a]
        return bot, top, attr & 0xFF, (attr >> 12) & 0xF

class FPair:
    """A FireRed pair through frlg.Pair, with the same cell() as EPair."""
    def __init__(self, primary, secondary):
        self.p = frlg.Pair(ENG, primary, secondary)
    def cell(self, mid):
        b, t = self.p.cell(mid)
        a = self.p.attr.get(mid, 0)
        return np.asarray(b, np.uint8), np.asarray(t, np.uint8), a & 0x1FF, (a >> 29) & 3

class Source:
    """One room: its grid of (bottom, top, behaviour, layer, collision) cells."""
    _all = {}
    def __new__(cls, name):
        if name not in cls._all:
            o = super().__new__(cls); o._load(name); cls._all[name] = o
        return cls._all[name]
    def _load(self, name):
        l = layouts()[name + '_Layout']
        self.name = name
        self.W, self.H = l['width'], l['height']
        self.words = np.frombuffer((ENG / l['blockdata_filepath']).read_bytes(), '<u2').reshape(self.H, self.W).astype(int)
        p, s = folder(l['primary_tileset']), folder(l['secondary_tileset'])
        self.pair = FPair(p, s) if l.get('layout_version') == 'frlg' else EPair(p, s)
        self.frlg = l.get('layout_version') == 'frlg'
        self._cells = {}
    def cell(self, x, y):
        if (x, y) not in self._cells:
            w = int(self.words[y, x])
            b, t, beh, lay = self.pair.cell(w & 0x3FF)
            self._cells[(x, y)] = dict(bot=b, top=t, behavior=beh, layer=lay, blocked=bool(w & 0x0C00), mid=w & 0x3FF)
        return self._cells[(x, y)]
    def flat(self, x, y):
        c = self.cell(x, y)
        out = c['bot'].copy(); a = c['top'][..., 3] > 0; out[a] = c['top'][..., :3][a]
        return out
    def image(self):
        return np.concatenate([np.concatenate([self.flat(x, y) for x in range(self.W)], 1) for y in range(self.H)], 0)
    def floor(self):
        """The room's plain floor: its most repeated metatile below its north wall."""
        ids = Counter(int(self.words[y, x]) & 0x3FF for y in range(2, self.H) for x in range(self.W))
        mid = ids.most_common(1)[0][0]
        at = next((x, y) for y in range(2, self.H) for x in range(self.W) if int(self.words[y, x]) & 0x3FF == mid)
        return self.flat(*at)
    def floors(self):
        """The plain floor and its shaded variants (the most used metatiles in the room's first floor row
        and first floor column): what is not an object."""
        ids = Counter(int(self.words[y, x]) & 0x3FF for y in range(2, self.H) for x in range(self.W))
        out = [self.floor()]
        for cells in ([(x, 2) for x in range(self.W)], [(1, y) for y in range(2, self.H)]):
            c = Counter(int(self.words[y, x]) & 0x3FF for x, y in cells)
            mid = c.most_common(1)[0][0]
            at = next((x, y) for x, y in cells if int(self.words[y, x]) & 0x3FF == mid)
            out.append(self.flat(*at))
        return out
    def object(self, x, y):
        """This cell's object pixels: everything on its top layer, and bottom pixels unlike the plain floor
        and its shades."""
        c = self.cell(x, y)
        same = np.zeros((16, 16), bool)
        for f in self.floors():
            same |= (c['bot'] == f).all(-1)
        return ~same | (c['top'][..., 3] > 0)

def sheet(name, k=2):
    from PIL import Image, ImageDraw
    s = Source(name)
    img = Image.fromarray(s.image()).resize((s.W * 16 * k, s.H * 16 * k), Image.NEAREST)
    d = ImageDraw.Draw(img)
    for y in range(s.H):
        for x in range(s.W):
            d.text((x * 16 * k + 1, y * 16 * k), f'{x},{y}', fill=(255, 255, 0))
            if s.cell(x, y)['blocked']:
                d.rectangle([x * 16 * k + 12 * k, y * 16 * k + 12 * k, x * 16 * k + 15 * k, y * 16 * k + 15 * k], fill=(255, 0, 0))
    return img
