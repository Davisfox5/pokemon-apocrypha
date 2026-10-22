"""Derive Blackthorn's city-view tables from its native Porymap sections.

Safe after ordinary native edits: this reads map.bin, metatiles, attributes, tiles and
palettes and never writes a layout or tileset. Run it after editing any Blackthorn
section, then commit the native edits and these outputs together; the engine's
build fails on a stale table (tools/city_view/check.py).

    python3 tools/gba/maps/blackthorn/stream.py ENGINE_CHECKOUT

Writes data/city_views/blackthorn/{glyphs.bin,entries.bin,layers.bin,source-hashes.json}
and src/data/city_views/blackthorn.h.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SECTIONS = [('BlackthornCity01', 0, 24), ('BlackthornCity02', 24, 44), ('BlackthornCity03', 44, 64)]
W, H = 64, 64
SLOTS = 1008
RING = 16                                   # the BG buffers hold 16x16 metatiles

def tileset(g, kind, folder):
    d = g / f'data/tilesets/{kind}/{folder}'
    im = np.array(Image.open(d / 'tiles.png'))
    tiles = [im[y:y + 8, x:x + 8].astype(np.uint8) & 15 for y in range(0, im.shape[0], 8) for x in range(0, im.shape[1], 8)]
    blocks = np.frombuffer((d / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
    attrs = np.frombuffer((d / 'metatile_attributes.bin').read_bytes(), '<u2')
    pals = [(d / 'palettes' / f'{i:02}.pal').read_text().replace('\r\n', '\n') for i in range(16)]
    return tiles, blocks, attrs, pals, d

def digest(p):
    data = p.read_bytes()
    return hashlib.sha256(data.replace(b'\r\n', b'\n') if p.suffix == '.pal' else data).hexdigest()

def main(g):
    glyphs = [bytes(32)]
    lookup = {bytes(32): 0}
    entries = np.zeros((H, W, 8), '<u4')
    layers = np.zeros((H, W), np.uint8)
    passable = np.zeros((H, W), bool)                 # collision 0: open ground, doors and water
    palettes = None
    inputs = []
    for name, y0, y1 in SECTIONS:
        folder = name.lower().replace('city', '_city')
        pt, pb, pa, pp, pd = tileset(g, 'primary', folder)
        st, sb, sa, sp, sd = tileset(g, 'secondary', folder)
        # One coherent palette set: the view never reloads palettes between sections.
        here = pp[:6] + sp[6:13]
        if palettes is None:
            palettes = here
        assert here == palettes, f'{name} palettes differ; propagate bank edits to every Blackthorn section'
        tiles = pt[:512] + [np.zeros((8, 8), np.uint8)] * (512 - len(pt[:512])) + st
        blocks = list(pb[:512]) + [None] * (512 - len(pb[:512])) + list(sb)
        attrs = list(pa[:512]) + [0] * (512 - len(pa[:512])) + list(sa)
        grid = np.frombuffer((g / f'data/layouts/{name}/map.bin').read_bytes(), '<u2').reshape(y1 - y0, W)
        for y, x in np.ndindex(grid.shape):
            mid = int(grid[y, x] & 1023)
            passable[y0 + y, x] = (int(grid[y, x]) >> 10) & 3 == 0
            layers[y0 + y, x] = (int(attrs[mid]) >> 12) & 3
            for i, e in enumerate(blocks[mid]):
                e = int(e)
                px = tiles[e & 1023].ravel()
                raw = bytes(px[0::2] | (px[1::2] << 4))
                if raw not in lookup:
                    lookup[raw] = len(glyphs); glyphs.append(raw)
                entries[y0 + y, x, i] = lookup[raw] | ((e & 0xFC00) << 16)
        inputs += [g / f'data/layouts/{name}/map.bin', g / f'data/layouts/{name}/border.bin', g / f'data/maps/{name}/map.json']
        inputs += [p for d in (pd, sd) for p in sorted(d.rglob('*')) if p.is_file() and p.suffix in ('.bin', '.png', '.pal')]
    assert len(glyphs) < 65536
    # Camera margin beyond the city. Where the edge cell is open ground or water
    # (the river, the bridge toward Route 45) the last two cells continue outward;
    # everywhere else the margin is open rock, so a cliff band is never stacked.
    same = lambda a, b: (entries[a[1], a[0]] == entries[b[1], b[0]]).all()
    rock = next((x, y) for y in range(0, H - 3, 2) for x in range(0, W - 3, 2)
                if all(same((x + dx, y + dy), (x + dx + 2 * i, y + dy + 2 * j)) for dx in (0, 1) for dy in (0, 1) for i in (0, 1) for j in (0, 1))
                and all(layers[y + dy, x + dx] == 1 for dx in (0, 1) for dy in (0, 1)))
    north = [0 if passable[0, x] else None for x in range(W)]
    south = [H - 2 if passable[H - 1, x] else None for x in range(W)]
    west = [0 if passable[y, 0] else None for y in range(H)]
    east = [W - 2 if passable[y, W - 1] else None for y in range(H)]
    def cell(x, y):
        inside_x, inside_y = 0 <= x < W, 0 <= y < H
        if not inside_x and not inside_y:
            return rock[0] + (x & 1), rock[1] + (y & 1)
        if x < 0:
            return (west[y] if west[y] is not None else rock[0]) + (x & 1), y if west[y] is not None else rock[1] + (y & 1)
        if x >= W:
            return (east[y] if east[y] is not None else rock[0]) + (x & 1), y if east[y] is not None else rock[1] + (y & 1)
        if y < 0:
            return (x if north[x] is not None else rock[0] + (x & 1)), (north[x] if north[x] is not None else rock[1]) + (y & 1)
        if y >= H:
            return (x if south[x] is not None else rock[0] + (x & 1)), (south[x] if south[x] is not None else rock[1]) + (y & 1)
        return x, y
    # Margin tables for the engine: 0xFF means "use the open-rock block".
    tables = {k: bytes(0xFF if v is None else v for v in t) for k, t in (('north', north), ('south', south), ('west', west), ('east', east))}
    # Worst 16x16-metatile window, camera margin included, must fit the 1007 streaming slots.
    pad = 16
    padded = np.zeros((H + 2 * pad, W + 2 * pad, 8), np.uint32)
    for py, px in np.ndindex(padded.shape[:2]):
        x, y = cell(px - pad, py - pad)
        padded[py, px] = entries[y, x]
    peak, at = 0, None
    for y in range(-pad, H):
        for x in range(-pad, W):
            n = len(np.unique(padded[y + pad:y + pad + RING, x + pad:x + pad + RING] & 0xFFFF)) - 1
            if n > peak:
                peak, at = n, (x, y)
    assert peak < SLOTS, (peak, at)
    out = g / 'data/city_views/blackthorn'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'glyphs.bin').write_bytes(b''.join(glyphs))
    (out / 'entries.bin').write_bytes(entries.tobytes())
    (out / 'layers.bin').write_bytes(layers.tobytes())
    for k, t in tables.items():
        (out / f'margin-{k}.bin').write_bytes(t)
    header = ('// Generated FROM native Porymap files by the hub\'s tools/gba/maps/blackthorn/stream.py. Do not edit.\n'
              f'#define BLACKTHORN_GLYPH_COUNT {len(glyphs)}\n'
              'static const u32 sBlackthornGlyphs[] = INCBIN_U32("data/city_views/blackthorn/glyphs.bin");\n'
              f'static const u32 sBlackthornEntries[{H} * {W} * 8] = INCBIN_U32("data/city_views/blackthorn/entries.bin");\n'
              f'static const u8 sBlackthornLayers[{H} * {W}] = INCBIN_U8("data/city_views/blackthorn/layers.bin");\n' +
              ''.join(f'static const u8 sBlackthornMargin{k.title()}[{n}] = INCBIN_U8("data/city_views/blackthorn/margin-{k}.bin");\n'
                      for k, n in (('north', W), ('south', W), ('west', H), ('east', H))) +
              'static const struct CityViewSection sBlackthornSections[] =\n{\n' +
              ''.join(f'    {{ MAP_GROUP(MAP_{n.upper().replace("CITY", "_CITY")}), MAP_NUM(MAP_{n.upper().replace("CITY", "_CITY")}), 0, {y0} }},\n'
                      for n, y0, _ in SECTIONS) + '};\n'
              '#define CITY_VIEW_BLACKTHORN { .sections = sBlackthornSections, .sectionCount = ARRAY_COUNT(sBlackthornSections), '
              f'.width = {W}, .height = {H}, .glyphCount = BLACKTHORN_GLYPH_COUNT, .glyphs = sBlackthornGlyphs, '
              '.entries = sBlackthornEntries, .layers = sBlackthornLayers, .marginNorth = sBlackthornMarginNorth, '
              '.marginSouth = sBlackthornMarginSouth, .marginWest = sBlackthornMarginWest, .marginEast = sBlackthornMarginEast, '
              f'.rockX = {rock[0]}, .rockY = {rock[1]} }}\n')
    hp = g / 'src/data/city_views/blackthorn.h'
    hp.parent.mkdir(parents=True, exist_ok=True)
    hp.write_text(header)
    hashes = {str(p.relative_to(g)): digest(p) for p in sorted(inputs + [out / 'glyphs.bin', out / 'entries.bin', out / 'layers.bin', hp]
                                                              + [out / f'margin-{k}.bin' for k in tables])}
    (out / 'source-hashes.json').write_text(json.dumps(hashes, indent=2) + '\n')
    report = dict(glyphs=len(glyphs), rom_bytes=len(glyphs) * 32 + entries.nbytes + layers.nbytes, worst_16x16_window_glyphs=peak,
                  worst_window_origin=at, streaming_slots=SLOTS - 1, margin_rock_block=list(rock),
                  margin_edges_using_open_rock={k: sum(1 for v in t if v is None) for k, t in (('north', north), ('south', south), ('west', west), ('east', east))}, cache_heap_bytes=4 + 256 * 8 * 2 + SLOTS * 4 + 2 + len(glyphs) * 2,
                  source='native tiles, palettes, metatiles, attributes and map entries of the three sections')
    ev = ROOT / 'gba/art/blackthorn-city/evidence'
    ev.mkdir(parents=True, exist_ok=True)
    (ev / 'stream-capacity.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
