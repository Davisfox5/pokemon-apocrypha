"""Render a FireRed/LeafGreen layout from the expansion checkout (640/640/7 primary split).

    python3 tools/gba/maps/fuchsia_city/frlg_render.py ENGINE LayoutDir OUT.png

tiles.py assumes Emerald's 512/512/6 split; FRLG layouts (isFrlg) use 640 tiles, 640 metatiles
and 7 palettes in the primary.
"""
import json, struct, sys
from pathlib import Path
from PIL import Image

def palette(path):
    return [tuple(map(int, l.split())) for l in path.read_text().splitlines()[3:19]]

def load(folder):
    img = Image.open(folder / 'tiles.png')
    tiles = [list(img.crop((x, y, x + 8, y + 8)).getdata()) for y in range(0, img.height, 8) for x in range(0, img.width, 8)]
    pals = [palette(folder / 'palettes' / f'{n:02}.pal') for n in range(16)]
    blocks = list(struct.iter_unpack('<8H', (folder / 'metatiles.bin').read_bytes()))
    return tiles, pals, blocks

def main(engine, layout_dir, out):
    eng = Path(engine)
    lay = next(l for l in json.loads((eng / 'data/layouts/layouts.json').read_text())['layouts']
               if l.get('blockdata_filepath', '').startswith(f'data/layouts/{layout_dir}/'))
    sym = {}
    import re
    g = (eng / 'src/data/tilesets/graphics.h').read_text()
    for m in re.finditer(r'gTilesetTiles_(\w+)\[\]\s*=\s*INCGFX_U32\("data/tilesets/(\w+)/(\w+)/tiles\.png"', g):
        sym['gTileset_' + m.group(1)] = eng / 'data/tilesets' / m.group(2) / m.group(3)
    P, S = load(sym[lay['primary_tileset']]), load(sym[lay['secondary_tileset']])
    NT, NM, NP = 640, 640, 7
    def render(mid):
        im = Image.new('RGB', (16, 16), P[1][0][0])
        e8 = P[2][mid] if mid < NM else S[2][mid - NM]
        for q8 in range(8):
            e = e8[q8]; tid = e & 1023; bank = e >> 12; q = q8 % 4
            tl = P[0] if tid < NT else S[0]; idx = tid if tid < NT else tid - NT
            if idx >= len(tl): continue
            cols = P[1][bank] if bank < NP else S[1][bank]
            for y in range(8):
                for x in range(8):
                    v = tl[idx][(7 - y if e & 2048 else y) * 8 + (7 - x if e & 1024 else x)] % 16
                    if v: im.putpixel(((q % 2) * 8 + x, (q // 2) * 8 + y), cols[v])
        return im
    w, h = lay['width'], lay['height']
    b = (eng / lay['blockdata_filepath']).read_bytes()
    grid = struct.unpack('<%dH' % (w * h), b)
    cache = {}
    out_im = Image.new('RGB', (w * 16, h * 16))
    for i, v in enumerate(grid):
        mid = v & 1023
        if mid not in cache: cache[mid] = render(mid)
        out_im.paste(cache[mid], ((i % w) * 16, (i // w) * 16))
    out_im.save(out)
    print(lay['name'], w, h, lay['primary_tileset'], lay['secondary_tileset'])

if __name__ == '__main__':
    main(*sys.argv[1:4])
