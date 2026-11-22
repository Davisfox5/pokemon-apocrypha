"""Install Fuchsia City into the engine checkout as an Emerald-format map.

    python3 tools/gba/maps/fuchsia_city/pack.py ENGINE BUILD_OUT

The Emerald build does not compile FireRed's tilesets (they sit under IS_FRLG), so FireRed's own
Fuchsia art is re-split into an Emerald-format pair, pixel for pixel:

  - primary `kanto_fuchsia`: FireRed General's tiles 0-511 at the same indices (so the engine's BG3
    fill tile 0x14 is FireRed's), palette banks 0-5 from General
  - secondary `fuchsia_city_kanto`: every used tile above 511 (General's 512-639 and the Fuchsia
    secondary's), palette bank 6 from General and banks 7-12 from FireRed's Fuchsia secondary
  - palette bank numbers do not change, so no tile is recoloured; FireRed's General metatiles
    0-511 keep their ids, every other used metatile (and the sign composites) moves to the secondary
  - behaviours carry over (the expansion shares MB_* numbering), layer types too
  - secondary tiles 496-511 stay free for door animation frames
  - FireRed General's animated flowers and water are drawn with their first frame (no callback)

BUILD_OUT is build.py's output (frlg-grid.json). Writes data/tilesets/{primary/kanto_fuchsia,
secondary/fuchsia_city_kanto}, data/layouts/KantoFuchsiaCity/{map.bin,border.bin} and
BUILD_OUT/pack.json (budget and id map).
"""
from __future__ import annotations
import json, shutil, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image

FRLG_NT, FRLG_NM = 640, 640
EM_NT, EM_NM = 512, 512
SEC_TILE_LIMIT = 496                     # 512 - 16 door-animation slots
PRIMARY_DIR, SECONDARY_DIR = 'kanto_fuchsia', 'fuchsia_city_kanto'
LAYOUT_DIR = 'KantoFuchsiaCity'

def tiles_of(d):
    im = Image.open(d / 'tiles.png')
    a = np.array(im if im.mode == 'P' else im.convert('P')) & 15
    return [a[y:y + 8, x:x + 8].copy() for y in range(0, a.shape[0], 8) for x in range(0, a.shape[1], 8)]

def write_tiles(path, tiles, pal):
    n = len(tiles)
    rows = max(1, (n + 15) // 16)
    a = np.zeros((rows * 8, 128), np.uint8)
    for i, t in enumerate(tiles):
        a[(i // 16) * 8:(i // 16) * 8 + 8, (i % 16) * 8:(i % 16) * 8 + 8] = t
    im = Image.fromarray(a, 'P')
    flat = [c for rgb in pal for c in rgb]
    im.putpalette(flat + [0] * (768 - len(flat)))
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, bits=4)

def read_pal(p):
    v = list(map(int, p.read_text().split()[3:51]))
    return [tuple(v[i * 3:i * 3 + 3]) for i in range(16)]

def main(engine: Path, out: Path):
    g = json.loads((out / 'frlg-grid.json').read_text())
    W, H = g['width'], g['height']
    cells, blocked = g['cells'], g['blocked']
    comps = {int(k): tuple(v) for k, v in g['composites'].items()}
    gp = engine / 'data/tilesets/primary/general_frlg'
    fs = engine / 'data/tilesets/secondary/fuchsia_city_frlg'
    tiles = tiles_of(gp)[:FRLG_NT] + tiles_of(fs)
    pm = np.frombuffer((gp / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
    sm = np.frombuffer((fs / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
    pa = np.frombuffer((gp / 'metatile_attributes.bin').read_bytes(), '<u4')
    sa = np.frombuffer((fs / 'metatile_attributes.bin').read_bytes(), '<u4')
    meta = lambda m: [int(v) for v in (pm[m] if m < FRLG_NM else sm[m - FRLG_NM])]
    attr = lambda m: int(pa[m] if m < FRLG_NM else sa[m - FRLG_NM])

    used = sorted({c for c in cells if c < 0x1000} | set(g['border']))
    for k in sorted({c for c in cells if c >= 0x1000}):
        used_k = comps[k]
    # tiles: General 0-511 stay put; every other referenced tile is appended to the secondary
    sec_tiles, tile_map = [], {}
    def tid(t):
        if t < EM_NT: return t
        if t not in tile_map:
            tile_map[t] = EM_NT + len(sec_tiles); sec_tiles.append(tiles[t])
        return tile_map[t]
    def remap(e):
        return (e & ~0x3FF) | tid(e & 0x3FF)
    # metatiles
    prim_meta = [[0] * 8 for _ in range(EM_NM)]
    prim_attr = [0] * EM_NM
    sec_meta, sec_attr, id_map = [], [], {}
    def em_attr(m):
        a = attr(m)
        beh, layer = a & 0x1FF, (a >> 29) & 3
        assert beh < 0x100, (hex(m), hex(beh))
        return beh | (layer << 12)
    for m in used:
        if m < EM_NM:
            prim_meta[m] = [remap(e) for e in meta(m)]
            prim_attr[m] = em_attr(m)
            id_map[m] = m
        else:
            id_map[m] = EM_NM + len(sec_meta)
            sec_meta.append([remap(e) for e in meta(m)]); sec_attr.append(em_attr(m))
    for k, (under, top) in sorted(comps.items()):
        e = meta(under)[:4] + meta(top)[4:]
        id_map[k] = EM_NM + len(sec_meta)
        sec_meta.append([remap(v) for v in e])
        a_top = attr(top)
        sec_attr.append((a_top & 0x1FF) | (((a_top >> 29) & 3) << 12))
    assert len(sec_tiles) <= SEC_TILE_LIMIT, len(sec_tiles)
    assert len(sec_meta) <= EM_NM, len(sec_meta)

    pd = engine / 'data/tilesets/primary' / PRIMARY_DIR
    sd = engine / 'data/tilesets/secondary' / SECONDARY_DIR
    for d in (pd, sd):
        if d.exists(): shutil.rmtree(d)
        (d / 'palettes').mkdir(parents=True)
    for b in range(16):
        shutil.copy(gp / f'palettes/{b:02}.pal', pd / f'palettes/{b:02}.pal')
        src = gp / f'palettes/{b:02}.pal' if b == 6 else fs / f'palettes/{b:02}.pal'
        shutil.copy(src, sd / f'palettes/{b:02}.pal')
    write_tiles(pd / 'tiles.png', tiles[:EM_NT], read_pal(gp / 'palettes/00.pal'))
    write_tiles(sd / 'tiles.png', sec_tiles or [np.zeros((8, 8), np.uint8)], read_pal(fs / 'palettes/07.pal'))
    (pd / 'metatiles.bin').write_bytes(struct.pack('<%dH' % (EM_NM * 8), *[v for m in prim_meta for v in m]))
    (pd / 'metatile_attributes.bin').write_bytes(struct.pack('<%dH' % EM_NM, *prim_attr))
    (sd / 'metatiles.bin').write_bytes(struct.pack('<%dH' % (len(sec_meta) * 8), *[v for m in sec_meta for v in m]))
    (sd / 'metatile_attributes.bin').write_bytes(struct.pack('<%dH' % len(sec_attr), *sec_attr))

    ld = engine / 'data/layouts' / LAYOUT_DIR
    ld.mkdir(parents=True, exist_ok=True)
    vals = []
    for c, b in zip(cells, blocked):
        vals.append(id_map[c] | (0x400 if b else 0) | (0 if b else 0x3000))
    (ld / 'map.bin').write_bytes(struct.pack('<%dH' % len(vals), *vals))
    (ld / 'border.bin').write_bytes(struct.pack('<4H', *[id_map[m] | 0x400 for m in g['border']]))
    rep = dict(primary=dict(tiles=EM_NT, metatiles_used=sum(1 for m in used if m < EM_NM), palettes='0-5'),
               secondary=dict(tiles=len(sec_tiles), tile_limit=SEC_TILE_LIMIT, metatiles=len(sec_meta), palettes='6-12'),
               id_map={str(k): v for k, v in id_map.items()})
    (out / 'pack.json').write_text(json.dumps(rep, indent=1) + '\n')
    print(json.dumps({k: rep[k] for k in ('primary', 'secondary')}))

if __name__ == '__main__':
    main(Path(sys.argv[1]), Path(sys.argv[2]))
