"""Cherrygrove's east-west cliff turned north into Route 30's west wall.

    python3 tools/gba/maps/route30_catalog/cherrygrove_wall.py ENGINE_CHECKOUT

Run after the joint pack (pair_pack.py --install), which gives Route 30's band wall cells their ids from
596 (reference.py CG_WALL_ID0) in Route 30's secondary. Cherrygrove's cliff (its rows 7-9, columns 30-39)
runs on to column 39 and its wall turns north at columns 40-41 to the town's north edge, where the band
carries it on into Route 30 (native columns 5-6). Each map draws the other's wall cells across the seam
with its own tilesets, so Cherrygrove's secondary defines the same ids:

  * The art is Route 30's rock render carried on into Cherrygrove's rows (assemble.py,
    local-art/cherrygrove-wall.png): rows 0-8 are the band's cells exactly; row 9 is the wall's foot.
  * Each cell is two layers in Cherrygrove's palettes: the lawn and the rock's cast shadow below in bank 0,
    the rock above in bank 5. CherrygrovePrimary's palette 5 takes the HGSS rock ramp in its seven slots no
    layout on CherrygrovePrimary draws (checked here: every metatile of the primary and of each of those
    layouts' secondaries).
  * New tiles go into Cherrygrove's secondary sheet slots no metatile of its own 84 uses; its metatiles from
    596 are the wall's (rerunning replaces them).
  * Map: columns 40-41, rows 0-9, the wall (blocked). Column 39, rows 0-5, Cherrygrove's lawn, blocked (the
    plateau beside the wall, as Route 30's column 4); column 42, rows 0-5, the road's left rim, open. The
    cliff's east end piece at column 39 (and 38 in row 9) becomes its middle piece, so it runs into the wall.
    Two of the town's north trees (a green and the blossom) give way to the wall, and the cliff-top lawn
    west of it (row 6) no longer connects to the road.
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import reference as Rf                               # noqa: E402
import rock as Rk                                    # noqa: E402
from tiles import Tileset                            # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route30-catalog'
WALL_PNG = ART / 'source/local-art/cherrygrove-wall.png'
OUT = ART / 'evidence/cherrygrove-wall'
CG_W = 80
OWN = Rf.CG_WALL_ID0 - 512                           # Cherrygrove's own secondary metatiles
WALL_X = [x + Rf.CG_OFFSET for x in sorted(Rf.WALL_COLS)]   # 40, 41
LAWN_X, RIM_X = 4 + Rf.CG_OFFSET, 7 + Rf.CG_OFFSET          # 39, 42 (the band's kit columns)
KIT_ROWS = range(0, 6)
BLOCKED, OPEN = (3, 3), (0, 3)                       # Cherrygrove's collision, elevation
CLIFF = {(39, 7): 0x05E, (39, 8): 0x074, (38, 9): 0x084, (39, 9): 0x085}   # its middle pieces (odd / even columns)
PAL5_SLOTS = (2, 3, 4, 6, 7, 11, 12)
PRIMARY_LAYOUTS = ('LAYOUT_CHERRYGROVE_CITY', 'LAYOUT_CHERRYGROVE_ROUTE29_APPROACH', 'LAYOUT_NEW_BARK_TOWN',
                   'LAYOUT_VIOLET_CITY_ENTRANCE', 'LAYOUT_CHERRYGROVE_REGIONAL_PREVIEW_29', 'LAYOUT_CHERRYGROVE_REGIONAL_PREVIEW_30')
COVERED = 1
SEEN_ROWS = 5                                        # Cherrygrove rows Route 30's camera reaches (seams.py)

def rgb5(a): return np.asarray(a).astype(np.int32) >> 3
def entry(tile, flip, bank): return tile | ((flip & 1) << 10) | ((flip >> 1) << 11) | (bank << 12)
def words_of(path, w):
    b = path.read_bytes()
    return np.array(struct.unpack('<%dH' % (len(b) // 2), b)).reshape(-1, w)
def jasc(cols):
    return '\r\n'.join(['JASC-PAL', '0100', '16'] + [f'{c[0]} {c[1]} {c[2]}' for c in cols]) + '\r\n'

def layouts(engine):
    return {l['id']: l for l in json.loads((engine / 'data/layouts/layouts.json').read_text())['layouts'] if 'id' in l}

def tileset_dir(engine, sym):
    import re
    g = (engine / 'src/data/tilesets/graphics.h').read_text()
    m = re.search(r'gTilesetTiles_%s\[\] = INCGFX_U32\("data/tilesets/(\w+/\w+)/tiles\.png"' % sym[9:], g)
    return engine / 'data/tilesets' / m.group(1)

def free_pal5_slots(engine):
    """Palette 5 slots any metatile drawn on CherrygrovePrimary (the primary's own and every secondary's on
    a layout using it, the wall's excepted) reaches."""
    L = layouts(engine)
    pri = engine / 'data/tilesets/primary/cherrygrove'
    used = set()
    def tiles_of(d):
        a = np.array(Image.open(d / 'tiles.png')) & 15
        return [a[y:y + 8, x:x + 8] for y in range(0, a.shape[0], 8) for x in range(0, a.shape[1], 8)]
    ptiles = tiles_of(pri)
    sets = [(pri, ptiles, None)]
    for lid in PRIMARY_LAYOUTS:
        d = tileset_dir(engine, L[lid]['secondary_tileset'])
        sets.append((d, tiles_of(d), OWN if d.name == 'cherrygrove' else None))
    for d, tiles, limit in sets:
        blocks = np.frombuffer((d / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
        if limit is not None:
            blocks = blocks[:limit]
        sec_tiles = tiles if d != pri else None
        for blk in blocks:
            for e in blk:
                e = int(e)
                if e >> 12 != 5 or not e:
                    continue
                i = e & 1023
                t = ptiles[i] if i < 512 else (sec_tiles[i - 512] if sec_tiles is not None and i - 512 < len(sec_tiles) else None)
                if t is not None:
                    used |= set(np.unique(t).tolist())
    return used

def cells_of(img):
    return [[img[y * 16:(y + 1) * 16, x * 16:(x + 1) * 16] for x in range(img.shape[1] // 16)] for y in range(img.shape[0] // 16)]

def main(engine):
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    # ---- the art: Route 30's band wall cells (the mirror ids) and Cherrygrove's rows of the render
    r30 = layouts(engine)['LAYOUT_CHERRYGROVE_ROUTE30_APPROACH']
    w30 = words_of(engine / r30['blockdata_filepath'], r30['width'])
    z = np.load(ART / 'source/assemble/layers.npz', allow_pickle=True)
    want = z['ground'].copy()
    for k in ('flat', 'objects'):
        a = z[k][..., 3] > 0; want[a] = z[k][a, :3]
    mirror = {}
    for y in range(Rf.PAD0, Rf.H):
        for x in Rf.WALL_COLS:
            m = int(w30[y, x]) & 1023
            px = want[y * 16:(y + 1) * 16, x * 16:(x + 1) * 16]
            assert (rgb5(mirror.setdefault(m, px)) == rgb5(px)).all(), ('one id, two looks', m)
    ids = sorted(mirror)
    assert ids == list(range(Rf.CG_WALL_ID0, Rf.CG_WALL_ID0 + len(ids))), ('Route 30 band wall ids are not the mirror block', ids)
    art = cells_of(np.array(Image.open(WALL_PNG).convert('RGB')))
    assert len(art) == len(Rf.CG_WALL_ROWS) and len(art[0]) == len(WALL_X)
    cell_id, defs = {}, {m: mirror[m] for m in ids}
    for r in Rf.CG_WALL_ROWS:
        for k, cx in enumerate(WALL_X):
            px = art[r][k]
            hit = next((m for m in ids if (rgb5(mirror[m]) == rgb5(px)).all()), None)
            if hit is None:
                assert r >= SEEN_ROWS, ('a wall cell Route 30 can see is not one of its ids', cx, r)
                hit = next((m for m, d in defs.items() if (rgb5(d) == rgb5(px)).all()), None)
                if hit is None:
                    hit = Rf.CG_WALL_ID0 + len(defs); defs[hit] = px
            cell_id[(cx, r)] = hit
    report['mirror_ids'] = ids
    report['cherrygrove_only_ids'] = [m for m in defs if m not in mirror]
    # ---- palettes: bank 0 below (lawn, road, cast shadow), bank 5 above (the rock ramp)
    pri = engine / 'data/tilesets/primary/cherrygrove'
    used = free_pal5_slots(engine)
    clash = used & set(PAL5_SLOTS)
    assert not clash, ('palette 5 slots in use', sorted(clash))
    p5 = [tuple(map(int, l.split())) for l in (pri / 'palettes/05.pal').read_text().splitlines()[3:19]]
    for slot, c in zip(PAL5_SLOTS, Rk.ROCK_RAMP):
        p5[slot] = tuple(c)
    (pri / 'palettes/05.pal').write_text(jasc(p5))
    p0 = [tuple(map(int, l.split())) for l in (pri / 'palettes/00.pal').read_text().splitlines()[3:19]]
    idx0 = {}
    for i, c in enumerate(p0[1:], 1):
        idx0.setdefault(tuple(int(v) >> 3 for v in c), i)
    idx5 = {tuple(int(v) >> 3 for v in c): s for s, c in zip(PAL5_SLOTS, Rk.ROCK_RAMP)}
    # ---- tiles and metatiles in Cherrygrove's secondary
    sec = engine / 'data/tilesets/secondary/cherrygrove'
    sheet_im = Image.open(sec / 'tiles.png'); sheet = np.array(sheet_im)
    n_tiles = (sheet.shape[0] // 8) * (sheet.shape[1] // 8)
    blocks = list(struct.iter_unpack('<8H', (sec / 'metatiles.bin').read_bytes()))[:OWN]
    attrs = list(struct.unpack('<%dH' % (len((sec / 'metatile_attributes.bin').read_bytes()) // 2), (sec / 'metatile_attributes.bin').read_bytes()))[:OWN]
    assert len(blocks) == OWN, ('Cherrygrove secondary has fewer metatiles than its own', len(blocks))
    referenced = {0} | {(e & 1023) - 512 for b in blocks for e in b if (e & 1023) >= 512}
    free = [i for i in range(n_tiles) if i not in referenced]
    placed, lookup = {}, {}
    def put(ix):
        for f in range(4):
            v = ix[:, ::-1] if f & 1 else ix
            v = v[::-1] if f & 2 else v
            if v.tobytes() in lookup:
                return lookup[v.tobytes()], f
        assert len(placed) < len(free), 'no free tile slots in the Cherrygrove secondary'
        i = free[len(placed)]; placed[i] = ix.copy(); lookup[ix.tobytes()] = i
        return i, 0
    new_rows = []
    for m in sorted(defs):
        px5 = rgb5(defs[m])
        rock = np.zeros((16, 16), bool)
        for c, _ in idx5.items():
            rock |= (px5 == c).all(-1)
        ent = [0] * 8
        for q in range(4):
            sl = np.s_[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            p, rk = px5[sl], rock[sl]
            lo = np.ones((8, 8), np.uint8)              # under the rock: the lawn's first colour
            for (yy, xx), v in np.ndenumerate(rk):
                if not v:
                    key = tuple(int(t) for t in p[yy, xx])
                    assert key in idx0, ('a non-rock colour bank 0 lacks', m, key)
                    lo[yy, xx] = idx0[key]
            t, f = put(lo); ent[q] = entry(512 + t, f, 0)
            if rk.any():
                hi = np.zeros((8, 8), np.uint8)
                for (yy, xx), v in np.ndenumerate(rk):
                    if v:
                        hi[yy, xx] = idx5[tuple(int(t) for t in p[yy, xx])]
                t, f = put(hi); ent[4 + q] = entry(512 + t, f, 5)
        new_rows.append((tuple(ent), COVERED << 12))
    for i, t in placed.items():
        sheet[(i // 16) * 8:(i // 16) * 8 + 8, (i % 16) * 8:(i % 16) * 8 + 8] = t
    o = Image.fromarray(sheet.astype(np.uint8), 'P'); o.putpalette(sheet_im.getpalette()); o.save(sec / 'tiles.png', bits=4)
    (sec / 'metatiles.bin').write_bytes(b''.join(struct.pack('<8H', *b) for b in blocks + [r[0] for r in new_rows]))
    (sec / 'metatile_attributes.bin').write_bytes(struct.pack('<%dH' % (OWN + len(new_rows)), *(attrs + [r[1] for r in new_rows])))
    report['tiles'] = dict(new=len(placed), slots=sorted(placed), free_before=len(free))
    # ---- the map
    path = engine / 'data/layouts/CherrygroveCity/map.bin'
    w = words_of(path, CG_W)
    before = w.copy()
    put_w = lambda x, y, m, ce: w.__setitem__((y, x), m | (ce[0] << 10) | (ce[1] << 12))
    for (cx, r), m in cell_id.items():
        put_w(cx, r, m, BLOCKED)
    for r in KIT_ROWS:
        put_w(LAWN_X, r, Rf.BAND_KIT[4][0][r % 2], BLOCKED)
        put_w(RIM_X, r, Rf.BAND_KIT[7][0][r % 2], OPEN)
    for (cx, r), m in CLIFF.items():
        put_w(cx, r, m, BLOCKED)
    path.write_bytes(struct.pack('<%dH' % w.size, *w.ravel().tolist()))
    report['cells_changed'] = [[int(x), int(y), f'{int(before[y, x]):#06x}', f'{int(w[y, x]):#06x}'] for y, x in zip(*np.nonzero(before != w))]
    # ---- check: the wall draws its art; nothing else changed in the render
    t = Tileset(engine, 'cherrygrove', 'cherrygrove')
    img = np.array(t.map_image(w.ravel().tolist(), CG_W).convert('RGB'))
    bad = [[cx, r] for (cx, r) in cell_id if (rgb5(img[r * 16:(r + 1) * 16, cx * 16:(cx + 1) * 16]) != rgb5(art[r][WALL_X.index(cx)])).any()]
    assert not bad, ('wall cells draw wrongly', bad)
    for m in ids:
        assert (rgb5(np.array(t.render(m).convert('RGB'))) == rgb5(mirror[m])).all(), ('mirror id draws wrongly in Cherrygrove', m)
    report['wall_cells_differing'] = 0
    x0, x1 = 28 * 16, 50 * 16
    Image.fromarray(img[:14 * 16, x0:x1]).resize(((x1 - x0) * 2, 14 * 32), Image.NEAREST).save(OUT / 'cherrygrove-north-east.png')
    (OUT / 'cherrygrove-wall.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'cells_changed'}), len(report['cells_changed']), 'cells changed')

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
