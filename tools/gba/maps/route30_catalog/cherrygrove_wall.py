"""Cherrygrove's sea cliff and its turn north into Route 30's west wall, in Johto's rock.

    python3 tools/gba/maps/route30_catalog/cherrygrove_wall.py ENGINE_CHECKOUT [--preview]

Johto's rock is the owner-locked Mahogany Town's: Blackthorn's FRLG terraces (rock.py) in the HGSS rock
ramp (Blackthorn's cliff01gs), as on Route 30, Route 43 and Blackthorn. Cherrygrove's cliff was the older
warm set, so it is redrawn here the same way, at HGSS's own levels (HGSS Cherrygrove, matrix (16, 12);
native = HGSS + (8, 2)):

  * the plateau north of the cliff (rows 0-6, columns 0-39) stands two terraces above the floor;
  * the cliff (rows 7-9, columns 0-41): row 7 the upper terrace (HGSS 2.9 above 1.0), rows 8-9 the lower
    (1.9 and 1.3), its foot in the sea or on the beach;
  * the wall turns north at columns 40-41 (HGSS 32-33: 2.7 and 1.7), the two terraces of Route 30's west
    wall, and runs up the town's north edge and through the band (reference.py WALL_COLS) into Route 30.

Run after the joint pack (pair_pack.py --install), which gives Route 30's band wall cells their ids from
596 (CG_WALL_ID0). Each map draws the other's wall cells across the seam with its own tilesets, so
Cherrygrove's secondary defines those ids too; its other new cells follow them.

  * Each cell is two layers in Cherrygrove's palettes: the rock above in bank 5, below it the lawn and the
    rock's cast shadow in bank 0, or the sea's own animated tiles where the cliff's foot stands in water
    (no cast shadow there). CherrygrovePrimary's palette 5 takes the rock ramp in its seven slots no layout
    on CherrygrovePrimary draws (checked here over every metatile of the primary and of those layouts'
    secondaries).
  * New tiles take the Cherrygrove secondary's sheet slots its own 84 metatiles don't use; its metatiles from
    596 are this tool's (rerunning replaces them).
  * Map: the cliff and wall cells blocked, as before. Beside the wall, column 39 (rows 0-5) is Cherrygrove's
    lawn, blocked (the plateau, as Route 30's column 4), and column 42 the road's left rim, open. A green
    tree and the blossom tree at (39-42, 0-5) give way to the wall; the cliff-top lawn west of it (row 6)
    no longer reaches the road.

--preview renders the result over Cherrygrove (evidence/cherrygrove-wall/) without installing.
"""
from __future__ import annotations
import json, re, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import reference as Rf                               # noqa: E402
import rock as Rk                                    # noqa: E402
from tiles import Tileset                            # noqa: E402
from claude_cherrygrove import ground as G           # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route30-catalog'
OUT = ART / 'evidence/cherrygrove-wall'
CG_W = 80
FLOOR = 1
OWN = Rf.CG_WALL_ID0 - 512                           # Cherrygrove's own secondary metatiles
WALL_X = [x + Rf.CG_OFFSET for x in sorted(Rf.WALL_COLS)]   # 40, 41
LAWN_X, RIM_X = 4 + Rf.CG_OFFSET, 7 + Rf.CG_OFFSET          # 39, 42 (the band's kit columns)
KIT_ROWS = range(0, 6)
CLIFF_ROWS = {7: 2, 8: 2, 9: 1}                      # terrace level per cliff row (HGSS rows 5-7: 2.9, 1.9, 1.3)
REGION = (range(-2, 12), range(0, 48))              # rows, columns rendered (two rows above: the band's wall)
BLOCKED, OPEN = (3, 3), (0, 3)                       # Cherrygrove's collision, elevation
PAL5_SLOTS = (2, 3, 4, 6, 7, 11, 12)
PRIMARY_LAYOUTS = ('LAYOUT_CHERRYGROVE_CITY', 'LAYOUT_CHERRYGROVE_ROUTE29_APPROACH', 'LAYOUT_NEW_BARK_TOWN',
                   'LAYOUT_VIOLET_CITY_ENTRANCE', 'LAYOUT_CHERRYGROVE_REGIONAL_PREVIEW_29', 'LAYOUT_CHERRYGROVE_REGIONAL_PREVIEW_30')
WATER_MB = 0x15                                      # Cherrygrove's sea
SEEN_ROWS = 5                                        # Cherrygrove rows Route 30's camera reaches (seams.py)
COVERED = 1
SENTINEL = (248, 0, 248)                             # marks water under the rock in the render
SEA = {(0, 0): 0x03B, (1, 0): 0x03A, (0, 1): 0x04C, (1, 1): 0x04B}   # Cherrygrove's sea by (column, row) parity

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
    g = (engine / 'src/data/tilesets/graphics.h').read_text()
    m = re.search(r'gTilesetTiles_%s\[\] = INCGFX_U32\("data/tilesets/(\w+/\w+)/tiles\.png"' % sym[9:], g)
    return engine / 'data/tilesets' / m.group(1)

# --------------------------------------------------------------------------- the render
def cell(x, r, words, t):
    """Terrace cell (rock.py's fields) for Cherrygrove (x, r)."""
    hi, lo = FLOOR + 2, FLOOR + 1
    rock = lambda peak: dict(lab='R', floor='grass', ground=float(FLOOR), peak=float(peak))
    ground = lambda lvl, kind: dict(lab='.', floor=kind, ground=float(lvl), peak=float(lvl))
    if r in CLIFF_ROWS and x <= WALL_X[1]:
        return rock(hi if CLIFF_ROWS[r] == 2 and x <= WALL_X[0] else lo)
    if r < min(CLIFF_ROWS):
        if x < WALL_X[0]:
            return ground(hi, 'grass')                 # the plateau
        if x in WALL_X:
            return rock(hi if x == WALL_X[0] else lo)
    m = int(words[min(max(r, 0), words.shape[0] - 1), x]) & 1023
    mb = t.attrs[int(m >= 512)][m - 512 if m >= 512 else m] & 0xFF
    return ground(FLOOR, 'water' if mb == WATER_MB else 'sand' if x in range(43, 46) else 'grass')

def render(engine, words):
    """Composite RGB of the region, the region's cells, and the changed cells' (x, r) list."""
    t = Tileset(engine, 'cherrygrove', 'cherrygrove')
    rows, cols = REGION
    cells = [[cell(x, r, words, t) for x in cols] for r in rows]
    d, isrock = Rk.terraces(cells, FLOOR)
    town = np.array(t.map_image(words.ravel().tolist(), CG_W).convert('RGB'))
    base = np.zeros((len(rows) * 16, len(cols) * 16, 3), np.uint8)
    for i, r in enumerate(rows):
        rr = min(max(r, 0), words.shape[0] - 1)
        base[i * 16:(i + 1) * 16] = town[rr * 16:(rr + 1) * 16, cols[0] * 16:(cols[-1] + 1) * 16]
    tex = G.textures()
    water = np.zeros((16, 16, 3), np.uint8); water[:] = SENTINEL
    plain = dict(grass=tex[G.GRASS], sand=tex[G.PATH], water=water)
    bottom, over, piece = Rk.rock_frlg(cells, d, isrock, base, Rk.frlg_pieces(engine), plain)
    a = over[..., 3] > 0
    comp = bottom.copy(); comp[a] = over[a, :3]
    changed = [(x, r) for r in rows if r >= 0 for x in cols if isrock[r - rows[0], x - cols[0]]]
    return comp, changed

def cell_px(comp, x, r):
    i, j = r - REGION[0][0], x - REGION[1][0]
    return comp[i * 16:(i + 1) * 16, j * 16:(j + 1) * 16]

# --------------------------------------------------------------------------- palettes
def free_pal5_slots(engine):
    """Palette 5 slots any metatile drawn on CherrygrovePrimary reaches (the primary's own metatiles and
    every secondary's on a layout using it; this tool's metatiles excepted)."""
    L = layouts(engine)
    pri = engine / 'data/tilesets/primary/cherrygrove'
    def tiles_of(d):
        a = np.array(Image.open(d / 'tiles.png')) & 15
        return [a[y:y + 8, x:x + 8] for y in range(0, a.shape[0], 8) for x in range(0, a.shape[1], 8)]
    ptiles = tiles_of(pri)
    sets = [(pri, None, None)]
    for lid in PRIMARY_LAYOUTS:
        d = tileset_dir(engine, L[lid]['secondary_tileset'])
        sets.append((d, tiles_of(d), OWN if d.name == 'cherrygrove' else None))
    used = set()
    for d, stiles, limit in sets:
        blocks = np.frombuffer((d / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)[:limit]
        for e in blocks.ravel():
            e = int(e)
            if not e or e >> 12 != 5:
                continue
            i = e & 1023
            tl = ptiles[i] if i < 512 else (stiles[i - 512] if stiles is not None and i - 512 < len(stiles) else None)
            if tl is not None:
                used |= set(np.unique(tl).tolist())
    return used

# --------------------------------------------------------------------------- install
def main(engine, preview):
    OUT.mkdir(parents=True, exist_ok=True)
    path = engine / 'data/layouts/CherrygroveCity/map.bin'
    words = words_of(path, CG_W)
    sec = engine / 'data/tilesets/secondary/cherrygrove'
    blocks = list(struct.iter_unpack('<8H', (sec / 'metatiles.bin').read_bytes()))[:OWN]
    ab = (sec / 'metatile_attributes.bin').read_bytes()
    attrs = list(struct.unpack('<%dH' % (len(ab) // 2), ab))[:OWN]
    assert len(blocks) == OWN, ('Cherrygrove secondary has fewer metatiles than its own', len(blocks))
    t0 = Tileset(engine, 'cherrygrove', 'cherrygrove')
    comp, changed = render(engine, words)
    before = np.array(t0.map_image(words.ravel().tolist(), CG_W).convert('RGB'))
    after = before.copy()
    for x, r in changed:
        sea = np.array(t0.render(SEA[(x % 2, r % 2)]).convert('RGB'))
        px = cell_px(comp, x, r)
        after[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16] = np.where((px == SENTINEL).all(-1)[..., None], sea, px)
    for r in KIT_ROWS:
        for x, ids in ((LAWN_X, Rf.BAND_KIT[4][0]), (RIM_X, Rf.BAND_KIT[7][0])):
            after[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16] = np.array(t0.render(ids[r % 2]).convert('RGB'))
    x0, x1 = 0, 48 * 16
    side = np.concatenate([before[:14 * 16, x0:x1], np.full((14 * 16, 8, 3), 255, np.uint8), after[:14 * 16, x0:x1]], 1)
    Image.fromarray(side).resize((side.shape[1] * 2, side.shape[0] * 2), Image.NEAREST).save(OUT / 'before-after.png')
    if preview:
        Image.fromarray(after[:14 * 16, x0:x1]).save(OUT / 'preview.png')
        print('preview', len(changed), 'cells'); return
    report = {}
    # ---- ids: Route 30's band wall cells first (the same pixels on both sides), then Cherrygrove's own
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
    # A cell over the sea is also keyed by the sea tile under it (the sea alternates by column and row).
    sea_of = lambda x, r, px: SEA[(x % 2, r % 2)] if (px == SENTINEL).all(-1).any() else None
    defs = {m: (mirror[m], None) for m in ids}
    cell_id = {}
    for x, r in changed:
        px = cell_px(comp, x, r)
        sea = sea_of(x, r, px)
        hit = next((m for m, (d, sd) in defs.items() if sd == sea and (rgb5(d) == rgb5(px)).all()), None)
        if hit is None:
            assert not (x in WALL_X and r < SEEN_ROWS), ('a wall cell Route 30 can see is not one of its ids', x, r)
            hit = Rf.CG_WALL_ID0 + len(defs); defs[hit] = (px, sea)
        cell_id[(x, r)] = hit
    report['mirror_ids'] = ids
    report['cherrygrove_ids'] = sorted(m for m in defs if m not in mirror)
    # ---- palettes
    pri = engine / 'data/tilesets/primary/cherrygrove'
    clash = free_pal5_slots(engine) & set(PAL5_SLOTS)
    assert not clash, ('palette 5 slots in use', sorted(clash))
    p5 = [tuple(map(int, l.split())) for l in (pri / 'palettes/05.pal').read_text().splitlines()[3:19]]
    for slot, c in zip(PAL5_SLOTS, Rk.ROCK_RAMP):
        p5[slot] = tuple((int(v) >> 3) << 3 for v in c)   # GBA colour, written as the packs write theirs
    (pri / 'palettes/05.pal').write_text(jasc(p5))
    p0 = [tuple(map(int, l.split())) for l in (pri / 'palettes/00.pal').read_text().splitlines()[3:19]]
    idx0 = {}
    for i, c in enumerate(p0[1:], 1):
        idx0.setdefault(tuple(int(v) >> 3 for v in c), i)
    idx5 = {tuple(int(v) >> 3 for v in c): s for s, c in zip(PAL5_SLOTS, Rk.ROCK_RAMP)}
    sentinel5 = tuple(v >> 3 for v in SENTINEL)
    # ---- tiles and metatiles
    sheet_im = Image.open(sec / 'tiles.png'); sheet = np.array(sheet_im)
    n_tiles = (sheet.shape[0] // 8) * (sheet.shape[1] // 8)
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
        px5 = rgb5(defs[m][0])
        ent = [0] * 8
        for q in range(4):
            sl = np.s_[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            p = px5[sl]
            keys = [[tuple(int(v) for v in p[yy, xx]) for xx in range(8)] for yy in range(8)]
            rk = np.array([[k in idx5 for k in row] for row in keys])
            wt = np.array([[k == sentinel5 for k in row] for row in keys])
            if wt.any():                               # the cliff's foot in the sea: the sea's own tiles below
                assert (rk | wt).all(), ('water quadrant with other ground', m, q)
                ent[q] = t0.blocks[0][defs[m][1]][q]
            else:
                lo = np.ones((8, 8), np.uint8)         # under the rock: the lawn's first colour
                for yy in range(8):
                    for xx in range(8):
                        if not rk[yy, xx]:
                            assert keys[yy][xx] in idx0, ('a ground colour bank 0 lacks', m, keys[yy][xx])
                            lo[yy, xx] = idx0[keys[yy][xx]]
                tl, f = put(lo); ent[q] = entry(512 + tl, f, 0)
            if rk.any():
                hi = np.zeros((8, 8), np.uint8)
                for yy in range(8):
                    for xx in range(8):
                        if rk[yy, xx]:
                            hi[yy, xx] = idx5[keys[yy][xx]]
                tl, f = put(hi); ent[4 + q] = entry(512 + tl, f, 5)
        new_rows.append((tuple(ent), COVERED << 12))
    for i, tl in placed.items():
        sheet[(i // 16) * 8:(i // 16) * 8 + 8, (i % 16) * 8:(i % 16) * 8 + 8] = tl
    o = Image.fromarray(sheet.astype(np.uint8), 'P'); o.putpalette(sheet_im.getpalette()); o.save(sec / 'tiles.png', bits=4)
    (sec / 'metatiles.bin').write_bytes(b''.join(struct.pack('<8H', *b) for b in blocks + [r[0] for r in new_rows]))
    (sec / 'metatile_attributes.bin').write_bytes(struct.pack('<%dH' % (OWN + len(new_rows)), *(attrs + [r[1] for r in new_rows])))
    report['tiles'] = dict(new=len(placed), slots=sorted(placed), free_before=len(free))
    # ---- the map
    w = words.copy()
    setw = lambda x, y, m, ce: w.__setitem__((y, x), m | (ce[0] << 10) | (ce[1] << 12))
    for (x, r), m in cell_id.items():
        setw(x, r, m, BLOCKED)
    for r in KIT_ROWS:
        setw(LAWN_X, r, Rf.BAND_KIT[4][0][r % 2], BLOCKED)
        setw(RIM_X, r, Rf.BAND_KIT[7][0][r % 2], OPEN)
    path.write_bytes(struct.pack('<%dH' % w.size, *w.ravel().tolist()))
    report['cells_changed'] = [[int(x), int(y), f'{int(words[y, x]):#06x}', f'{int(w[y, x]):#06x}'] for y, x in zip(*np.nonzero(words != w))]
    # ---- check: every changed cell draws the render (the sea under the foot animates, so it draws the sea)
    t = Tileset(engine, 'cherrygrove', 'cherrygrove')
    img = np.array(t.map_image(w.ravel().tolist(), CG_W).convert('RGB'))
    bad = [[x, r] for (x, r) in cell_id if (rgb5(img[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16]) != rgb5(after[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16])).any()]
    assert not bad, ('cells draw wrongly', bad)
    for m in ids:
        assert (rgb5(np.array(t.render(m).convert('RGB'))) == rgb5(mirror[m])).all(), ('mirror id draws wrongly in Cherrygrove', m)
    report['cells_differing_from_render'] = 0
    Image.fromarray(img[:14 * 16, x0:x1]).resize(((x1 - x0) * 2, 14 * 32), Image.NEAREST).save(OUT / 'installed.png')
    (OUT / 'cherrygrove-wall.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'cells_changed'}), len(report['cells_changed']), 'cells changed')

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), '--preview' in sys.argv)
