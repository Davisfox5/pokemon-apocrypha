"""Render FireRed/LeafGreen-format layouts and metatiles from the expansion checkout.

    python3 tools/gba/maps/fuchsia_city/frlg_render.py ENGINE LayoutDir OUT.png
    python3 tools/gba/maps/fuchsia_city/frlg_render.py ENGINE --sheet PRIMARY SECONDARY OUT.png

tiles.py assumes Emerald's 512/512/6 primary split; FRLG layouts (isFrlg, layout_version "frlg")
use 640 tiles, 640 metatiles and 7 palettes in the primary.
"""
import json, re, struct, sys
from pathlib import Path
from PIL import Image, ImageDraw

NT, NM, NP = 640, 640, 7

def palette(path):
    return [tuple(map(int, l.split())) for l in path.read_text().splitlines()[3:19]]

def load(folder):
    img = Image.open(folder / 'tiles.png')
    raw = img.tobytes() if img.mode == 'P' else img.convert('P').tobytes()
    W = img.width
    tiles = []
    for ty in range(img.height // 8):
        for tx in range(W // 8):
            tiles.append([raw[(ty * 8 + y) * W + tx * 8 + x] for y in range(8) for x in range(8)])
    pals = [palette(folder / 'palettes' / f'{n:02}.pal') for n in range(16)]
    blocks = list(struct.iter_unpack('<8H', (folder / 'metatiles.bin').read_bytes()))
    a = (folder / 'metatile_attributes.bin').read_bytes()
    attrs = list(struct.unpack('<%dI' % (len(a) // 4), a))
    return tiles, pals, blocks, attrs

def symbols(eng):
    sym = {}
    g = (eng / 'src/data/tilesets/graphics.h').read_text()
    for m in re.finditer(r'gTilesetTiles_(\w+)\[\]\s*=\s*INCGFX_U32\("data/tilesets/(\w+)/(\w+)/tiles\.png"', g):
        sym['gTileset_' + m.group(1)] = eng / 'data/tilesets' / m.group(2) / m.group(3)
    return sym

class Pair:
    """A FRLG primary + secondary pair. Metatile ids 0..639 primary, 640.. secondary."""
    def __init__(self, pdir, sdir):
        self.P, self.S = load(Path(pdir)), load(Path(sdir))
        self.cache = {}

    def entries(self, mid):
        return self.P[2][mid] if mid < NM else self.S[2][mid - NM]

    def attr(self, mid):
        return self.P[3][mid] if mid < NM else self.S[3][mid - NM]

    def layer_tiles(self, mid, layer):
        """RGBA 16x16 of one layer (0 bottom, 1 top)."""
        P, S = self.P, self.S
        im = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        e8 = self.entries(mid)
        for q in range(4):
            e = e8[layer * 4 + q]; tid = e & 1023; bank = e >> 12
            tl = P[0] if tid < NT else S[0]; idx = tid if tid < NT else tid - NT
            if idx >= len(tl): continue
            cols = P[1][bank] if bank < NP else S[1][bank]
            for y in range(8):
                for x in range(8):
                    v = tl[idx][(7 - y if e & 2048 else y) * 8 + (7 - x if e & 1024 else x)] % 16
                    if v: im.putpixel(((q % 2) * 8 + x, (q // 2) * 8 + y), cols[v] + (255,))
        return im

    def render(self, mid):
        if mid not in self.cache:
            im = Image.new('RGB', (16, 16), self.P[1][0][0])
            for layer in range(2):
                t = self.layer_tiles(mid, layer)
                im.paste(t, (0, 0), t)
            self.cache[mid] = im
        return self.cache[mid]

    def map_image(self, grid, w):
        h = len(grid) // w
        out = Image.new('RGB', (w * 16, h * 16))
        for i, v in enumerate(grid):
            out.paste(self.render(v & 1023), ((i % w) * 16, (i // w) * 16))
        return out

    def sheet(self, path, mids=None, scale=2):
        mids = list(mids) if mids is not None else list(range(len(self.P[2]))) + [NM + i for i in range(len(self.S[2]))]
        cols = 16; c = 16 * scale + 4
        im = Image.new('RGB', (cols * c, ((len(mids) + cols - 1) // cols) * (c + 10)), (30, 30, 36))
        d = ImageDraw.Draw(im)
        for i, m in enumerate(mids):
            x, y = (i % cols) * c, (i // cols) * (c + 10)
            im.paste(self.render(m).resize((16 * scale, 16 * scale), Image.NEAREST), (x, y))
            d.text((x, y + 16 * scale), f'{m:x}', fill='white')
        im.save(path)

def layout(eng, layout_dir):
    eng = Path(eng)
    lay = next(l for l in json.loads((eng / 'data/layouts/layouts.json').read_text())['layouts']
               if l.get('blockdata_filepath', '').startswith(f'data/layouts/{layout_dir}/'))
    w, h = lay['width'], lay['height']
    grid = list(struct.unpack('<%dH' % (w * h), (eng / lay['blockdata_filepath']).read_bytes()))
    return lay, grid

def pair_for(eng, lay):
    sym = symbols(Path(eng))
    return Pair(sym[lay['primary_tileset']], sym[lay['secondary_tileset']])

def main(argv):
    eng = Path(argv[0])
    if argv[1] == '--sheet':
        sym = symbols(eng)
        Pair(sym[argv[2]], sym[argv[3]]).sheet(argv[4])
        return
    lay, grid = layout(eng, argv[1])
    pair_for(eng, lay).map_image(grid, lay['width']).save(argv[2])
    print(lay['name'], lay['width'], lay['height'], lay['primary_tileset'], lay['secondary_tileset'])

if __name__ == '__main__':
    main(sys.argv[1:])
