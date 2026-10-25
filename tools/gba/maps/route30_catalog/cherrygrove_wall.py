"""Cherrygrove's north edge in Johto's art: its sea cliff, the cliff's turn north into Route 30's west wall,
and the route's tree lattice through its north forest.

    python3 tools/gba/maps/route30_catalog/cherrygrove_wall.py ENGINE_CHECKOUT --render     # before the pack
    python3 tools/gba/maps/route30_catalog/cherrygrove_wall.py ENGINE_CHECKOUT --install    # after the pack

Johto's rock is the owner-locked Mahogany Town's: Blackthorn's FRLG terraces (rock.py) in the HGSS rock
ramp (Blackthorn's cliff01gs), as on Route 30, Route 43 and Blackthorn. Cherrygrove's cliff was the older
warm set, so it is redrawn the same way, at HGSS's own levels (HGSS Cherrygrove, matrix (16, 12);
native = HGSS + (8, 2)):

  * the plateau north of the cliff (rows 0-6, columns 0-39) stands two terraces above the floor;
  * the cliff (rows 7-9, columns 0-41) is the upper terrace for rows 7-8 and the lower for row 9, its foot
    in the sea or on the beach;
  * the wall turns north at columns 40-41 (HGSS 32-33: 2.7 and 1.7), the two terraces of Route 30's west
    wall, and runs up the town's north edge and through the band (reference.py WALL_COLS) into Route 30;
  * where a rock top meets the plateau's grass the grass runs onto it along a wavy, dithered line (rock.py
    soften), as on Route 30.

The north forest takes the route's tree lattice (reference.py CG_ROOTS: 2x2 roots every two rows, crowns
overlapping), the Cherrygrove tree (T01 and its shadow) on Cherrygrove's lawn, so the forest runs on from
Route 30 through the band without gaps: west of the wall rows 0-5, east of the road one lattice row (rows
0-1; row 2 is lawn). The two blossom trees in that row become green, as in the band (a blossom crown can't
share a tile's palette with the green crowns it overlaps).

--render draws all of it from Cherrygrove's base revision (BASE_REV) and writes source/seam/: every new
cell's ground and object layers, and which of them Route 30 can see. The joint pack (pair_pack.py) gives
those, and Route 30's band cells, ids from 596 in Route 30's secondary (source/pack/mirror-ids.json).
--install defines the same ids in Cherrygrove's secondary with Cherrygrove's tiles and palettes, then the
rest of the new cells after them, and writes the map:

  * each cell is two layers: below, the lawn, the rock's cast shadow and the lawn rim tone in bank 0, or the
    sea's own animated tiles where the cliff's foot stands in water; above, the rock in bank 5 or the trees
    in bank 3 (Cherrygrove's tree palette). CherrygrovePrimary's palette 5 takes the rock ramp in its seven
    slots no layout on CherrygrovePrimary draws (checked over every metatile of the primary and of those
    layouts' secondaries).
  * new tiles take the Cherrygrove secondary's sheet slots its own 84 metatiles don't use.
  * map: the cliff, wall and trees blocked as before. Beside the wall, column 39 (rows 0-5) is Cherrygrove's
    lawn, blocked (the plateau, as Route 30's column 4), and column 42 the road's left rim, open. Two of the
    town's north trees give way to the wall; the cliff-top lawn west of it (row 6) no longer reaches the road.
"""
from __future__ import annotations
import io, json, re, struct, subprocess, sys, tarfile, tempfile
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
SEAM = ART / 'source/seam'
BASE_REV = '2722eaf7601ec02dc5a684fa8cdef9206c0dc377'   # the engine's apocrypha base (pack.py BASE_REV)
CG_W = 80
FLOOR = 1
OWN = Rf.CG_WALL_ID0 - 512                           # Cherrygrove's own secondary metatiles
WALL_X = [x + Rf.CG_OFFSET for x in sorted(Rf.WALL_COLS)]   # 40, 41
LAWN_X, RIM_X = 4 + Rf.CG_OFFSET, 7 + Rf.CG_OFFSET          # 39, 42 (the band's kit columns)
KIT_ROWS = range(0, 6)
CLIFF_ROWS = {7: 2, 8: 2, 9: 1}                      # terrace level per cliff row (HGSS rows 5-7: 2.9, 1.9, 1.3)
WEST_FOREST = (range(0, LAWN_X), range(0, 6))        # columns, rows of the west lattice
EAST_FOREST = (range(Rf.CG_RIGHT_RIM, 70), range(0, 2), 2)   # columns, tree rows, the lawn row below them
REGION = (range(-2, 12), range(0, CG_W))             # rows, columns rendered (two rows above: the band's wall)
BLOCKED, OPEN = (3, 3), (0, 3)                       # Cherrygrove's collision, elevation
PAL5_SLOTS = (2, 3, 4, 6, 7, 11, 12)
TOP_BANKS = (3, 5)                                   # Cherrygrove's tree palette, the rock ramp
PRIMARY_LAYOUTS = ('LAYOUT_CHERRYGROVE_CITY', 'LAYOUT_CHERRYGROVE_ROUTE29_APPROACH', 'LAYOUT_NEW_BARK_TOWN',
                   'LAYOUT_VIOLET_CITY_ENTRANCE', 'LAYOUT_CHERRYGROVE_REGIONAL_PREVIEW_29', 'LAYOUT_CHERRYGROVE_REGIONAL_PREVIEW_30')
WATER_MB = 0x15                                      # Cherrygrove's sea
SEEN = (5, range(27, CG_W))                          # Cherrygrove rows and columns Route 30's camera reaches (seams.py)
COVERED = 1
SENTINEL = (248, 0, 248)                             # marks water under the rock in the render
SEA = {(0, 0): 0x03B, (1, 0): 0x03A, (0, 1): 0x04C, (1, 1): 0x04B}   # Cherrygrove's sea by (column, row) parity

def rgb5(a): return np.asarray(a).astype(np.int32) >> 3
def entry(tile, flip, bank): return tile | ((flip & 1) << 10) | ((flip >> 1) << 11) | (bank << 12)
def words_of(data, w):
    return np.array(struct.unpack('<%dH' % (len(data) // 2), data)).reshape(-1, w)
def jasc(cols):
    return '\r\n'.join(['JASC-PAL', '0100', '16'] + [f'{c[0]} {c[1]} {c[2]}' for c in cols]) + '\r\n'
def read_pal(path):
    return [tuple(map(int, l.split())) for l in path.read_text().splitlines()[3:19]]
def layouts(engine):
    return {l['id']: l for l in json.loads((engine / 'data/layouts/layouts.json').read_text())['layouts'] if 'id' in l}
def tileset_dir(engine, sym):
    g = (engine / 'src/data/tilesets/graphics.h').read_text()
    m = re.search(r'gTilesetTiles_%s\[\] = INCGFX_U32\("data/tilesets/(\w+/\w+)/tiles\.png"' % sym[9:], g)
    return engine / 'data/tilesets' / m.group(1)

def base_checkout(engine):
    """Cherrygrove's map and tilesets at BASE_REV, unpacked in the engine's layout (reruns start from them)."""
    d = Path(tempfile.mkdtemp(prefix='cherrygrove-base-'))
    tar = subprocess.check_output(['git', '-C', str(engine), 'archive', BASE_REV, 'data/layouts/CherrygroveCity',
                                   'data/tilesets/primary/cherrygrove', 'data/tilesets/secondary/cherrygrove'])
    tarfile.open(fileobj=io.BytesIO(tar)).extractall(d)
    return d

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

def forest_cells():
    west = [(x, r) for r in WEST_FOREST[1] for x in WEST_FOREST[0]]
    east = [(x, r) for r in EAST_FOREST[1] for x in EAST_FOREST[0]]
    return west + east

def render(base, engine):
    """Ground (with the rock) and object layers of the region, and the new cells' (x, r) list."""
    import assemble as As
    words = words_of((base / 'data/layouts/CherrygroveCity/map.bin').read_bytes(), CG_W)
    t = Tileset(base, 'cherrygrove', 'cherrygrove')
    rows, cols = REGION
    cells = [[cell(x, r, words, t) for x in cols] for r in rows]
    d, isrock = Rk.terraces(cells, FLOOR)
    town = np.array(t.map_image(words.ravel().tolist(), CG_W).convert('RGB'))
    R0 = rows[0]
    base_img = np.zeros((len(rows) * 16, len(cols) * 16, 3), np.uint8)
    for i, r in enumerate(rows):
        rr = min(max(r, 0), words.shape[0] - 1)
        base_img[i * 16:(i + 1) * 16] = town[rr * 16:(rr + 1) * 16]
    put = lambda img, x, r, px: img.__setitem__(np.s_[(r - R0) * 16:(r - R0 + 1) * 16, x * 16:(x + 1) * 16], px)
    for x, r in forest_cells():
        put(base_img, x, r, np.array(t.render(Rf.forest_ground(x, r)).convert('RGB')))
    tex = G.textures()
    water = np.zeros((16, 16, 3), np.uint8); water[:] = SENTINEL
    plain = dict(grass=tex[G.GRASS], sand=tex[G.PATH], water=water)
    ground, over, piece = Rk.rock_frlg(cells, d, isrock, base_img, Rk.frlg_pieces(engine), plain, soft=True)
    a = over[..., 3] > 0
    ground[a] = over[a, :3]
    # The trees, in Route 30's order (by base row, then column): Cherrygrove's lattice and the band's.
    tree, _ = As.cherry_tree(base, tex[G.GRASS])
    top = np.zeros(ground.shape[:2] + (4,), np.uint8)
    roots = Rf.CG_ROOTS + [(x + Rf.CG_OFFSET, y - Rf.H) for x, y in Rf.BAND_ROOTS]
    for x, y in sorted(roots, key=lambda p: (p[1], p[0])):
        As.over(top, tree, x * 16, (y - 1 - R0) * 16)
    changed = sorted(set([(x, r) for r in rows if r >= 0 for x in cols if isrock[r - R0, x - cols[0]]] + forest_cells()),
                     key=lambda p: (p[1], p[0]))
    return ground, top, changed, words, t

def layers_of(ground, top, x, r):
    sl = np.s_[(r - REGION[0][0]) * 16:(r - REGION[0][0] + 1) * 16, x * 16:(x + 1) * 16]
    return ground[sl], top[sl]

def composite(g, tp):
    px = g.copy(); a = tp[..., 3] > 0; px[a] = tp[a, :3]
    return px

def seen(x, r):
    return r < SEEN[0] and x in SEEN[1]

def do_render(engine, preview_only=False):
    OUT.mkdir(parents=True, exist_ok=True); SEAM.mkdir(parents=True, exist_ok=True)
    base = base_checkout(engine)
    ground, top, changed, words, t = render(base, engine)
    lay = [layers_of(ground, top, x, r) for x, r in changed]
    np.savez_compressed(SEAM / 'cherrygrove-cells.npz', cells=np.array(changed), ground=np.array([g for g, _ in lay]),
                        top=np.array([tp for _, tp in lay]), visible=np.array([seen(x, r) for x, r in changed]))
    before = np.array(t.map_image(words.ravel().tolist(), CG_W).convert('RGB'))
    after = expected(before, changed, lay, t)
    side = np.concatenate([before[:14 * 16, :56 * 16], np.full((14 * 16, 8, 3), 255, np.uint8), after[:14 * 16, :56 * 16]], 1)
    Image.fromarray(side).save(OUT / 'before-after.png')
    (SEAM / 'cherrygrove-kit.json').write_text(json.dumps(dict(
        note='Primary metatiles placed by id: x, row, metatile, collision, elevation.',
        cells=[[x, r, m, ce[0], ce[1]] for x, r, m, ce in kit()])) + '\n')
    (SEAM / 'README.md').write_text('Written by cherrygrove_wall.py --render: Cherrygrove\'s new cells (ground and object '
                                    'layers, `cherrygrove-cells.npz`), which of them Route 30 can see (`visible`), and the '
                                    'primary metatiles it places by id (`cherrygrove-kit.json`).\n')
    print('rendered', len(changed), 'cells,', int(sum(seen(x, r) for x, r in changed)), 'visible from Route 30')
    return base, changed, lay, words, t, after

def expected(before, changed, lay, t):
    """Cherrygrove as installed (the sea under the cliff's foot drawn as its first animation frame), kit included."""
    after = before.copy()
    for (x, r), (g, tp) in zip(changed, lay):
        px = composite(g, tp)
        sea = np.array(t.render(SEA[(x % 2, r % 2)]).convert('RGB'))
        after[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16] = np.where((px == SENTINEL).all(-1)[..., None], sea, px)
    for x, r, m, _ in kit():
        after[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16] = np.array(t.render(m).convert('RGB'))
    return after

def kit():
    """Primary metatiles placed by id: (x, r, metatile, (collision, elevation))."""
    out = []
    for r in KIT_ROWS:
        out.append((LAWN_X, r, Rf.BAND_KIT[4][0][r % 2], BLOCKED))
        out.append((RIM_X, r, Rf.BAND_KIT[7][0][r % 2], OPEN))
    r = EAST_FOREST[2]
    out += [(x, r, Rf.forest_ground(x, r), OPEN) for x in EAST_FOREST[0]]
    return out

# --------------------------------------------------------------------------- palettes
def pal5_in_use(engine):
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
def do_install(engine):
    base, changed, lay, words, t0 = do_render(engine)
    report = {}
    # ---- the mirror block: Route 30's band cells and the Cherrygrove cells Route 30 sees
    mid = json.loads((ART / 'source/pack/mirror-ids.json').read_text())
    z = np.load(ART / 'source/assemble/layers.npz', allow_pickle=True)
    want = z['ground'].copy()
    for k in ('flat', 'objects'):
        a = z[k][..., 3] > 0; want[a] = z[k][a, :3]
    art = {c: composite(*l) for c, l in zip(changed, lay)}
    defs = {}
    def define(m, px, sea=None):
        if m in defs:
            assert defs[m][1] == sea and (rgb5(defs[m][0]) == rgb5(px)).all(), ('one id, two looks', m)
        defs[m] = (px, sea)
    for k, m in mid['band'].items():
        x, y = map(int, k.split(','))
        define(m, want[y * 16:(y + 1) * 16, x * 16:(x + 1) * 16])
    for k, m in mid['other'].items():
        define(m, art[tuple(map(int, k.split(',')))])
    ids = sorted(defs)
    assert ids == list(range(Rf.CG_WALL_ID0, Rf.CG_WALL_ID0 + len(ids))), ('the mirror block is not contiguous', ids)
    sea_of = lambda x, r, px: SEA[(x % 2, r % 2)] if (px == SENTINEL).all(-1).any() else None
    cell_id = {}
    for x, r in changed:
        px = art[(x, r)]; sea = sea_of(x, r, px)
        m = mid['other'].get(f'{x},{r}')
        if m is None:
            m = next((m for m, (d, sd) in defs.items() if sd == sea and (rgb5(d) == rgb5(px)).all()), None)
        if m is None:
            assert not seen(x, r), ('a cell Route 30 can see has no id in its secondary', x, r)
            m = Rf.CG_WALL_ID0 + len(defs); defs[m] = (px, sea)
        cell_id[(x, r)] = m
    report['mirror_ids'] = [ids[0], ids[-1]]
    report['cherrygrove_ids'] = [m for m in sorted(defs) if m not in ids]
    # ---- palettes
    pri = engine / 'data/tilesets/primary/cherrygrove'
    (pri / 'palettes/05.pal').write_text((base / 'data/tilesets/primary/cherrygrove/palettes/05.pal').read_text())
    clash = pal5_in_use(engine) & set(PAL5_SLOTS)
    assert not clash, ('palette 5 slots in use', sorted(clash))
    p5 = read_pal(pri / 'palettes/05.pal')
    for slot, c in zip(PAL5_SLOTS, Rk.ROCK_RAMP):
        p5[slot] = tuple((int(v) >> 3) << 3 for v in c)   # GBA colour, written as the packs write theirs
    (pri / 'palettes/05.pal').write_text(jasc(p5))
    def index(pal):
        out = {}
        for i, c in enumerate(pal[1:], 1):
            out.setdefault(tuple(int(v) >> 3 for v in c), i)
        return out
    idx0 = index(read_pal(pri / 'palettes/00.pal'))
    idx_top = {3: index(read_pal(pri / 'palettes/03.pal')), 5: index(p5)}
    sentinel5 = tuple(v >> 3 for v in SENTINEL)
    # ---- tiles and metatiles, from the base secondary's own 84
    sec, bsec = engine / 'data/tilesets/secondary/cherrygrove', base / 'data/tilesets/secondary/cherrygrove'
    blocks = list(struct.iter_unpack('<8H', (bsec / 'metatiles.bin').read_bytes()))
    ab = (bsec / 'metatile_attributes.bin').read_bytes()
    attrs = list(struct.unpack('<%dH' % (len(ab) // 2), ab))
    assert len(blocks) == OWN, ("Cherrygrove secondary's own metatiles", len(blocks))
    sheet_im = Image.open(bsec / 'tiles.png'); sheet = np.array(sheet_im)
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
            keys = [[tuple(int(v) for v in px5[sl][yy, xx]) for xx in range(8)] for yy in range(8)]
            low = np.array([[k in idx0 for k in row] for row in keys])
            wet = np.array([[k == sentinel5 for k in row] for row in keys])
            up = ~low & ~wet
            if wet.any():                              # the cliff's foot in the sea: the sea's own tiles below
                assert not low.any(), ('water quadrant with other ground', m, q)
                ent[q] = t0.blocks[0][defs[m][1]][q]
            else:
                lo = np.ones((8, 8), np.uint8)         # under the layer above: the lawn's first colour
                for yy in range(8):
                    for xx in range(8):
                        if low[yy, xx]:
                            lo[yy, xx] = idx0[keys[yy][xx]]
                tl, f = put(lo); ent[q] = entry(512 + tl, f, 0)
            if up.any():
                need = {keys[yy][xx] for yy in range(8) for xx in range(8) if up[yy, xx]}
                bank = next((b for b in TOP_BANKS if need <= set(idx_top[b])), None)
                assert bank is not None, ('no palette holds the layer above', m, q, sorted(need))
                hi = np.zeros((8, 8), np.uint8)
                for yy in range(8):
                    for xx in range(8):
                        if up[yy, xx]:
                            hi[yy, xx] = idx_top[bank][keys[yy][xx]]
                tl, f = put(hi); ent[4 + q] = entry(512 + tl, f, bank)
        new_rows.append((tuple(ent), COVERED << 12))
    for i, tl in placed.items():
        sheet[(i // 16) * 8:(i // 16) * 8 + 8, (i % 16) * 8:(i % 16) * 8 + 8] = tl
    o = Image.fromarray(sheet.astype(np.uint8), 'P'); o.putpalette(sheet_im.getpalette()); o.save(sec / 'tiles.png', bits=4)
    (sec / 'metatiles.bin').write_bytes(b''.join(struct.pack('<8H', *b) for b in blocks + [r[0] for r in new_rows]))
    (sec / 'metatile_attributes.bin').write_bytes(struct.pack('<%dH' % (OWN + len(new_rows)), *(attrs + [r[1] for r in new_rows])))
    report['tiles'] = dict(new=len(placed), free_before=len(free))
    # ---- the map, from the base map
    w = words.copy()
    setw = lambda x, y, m, ce: w.__setitem__((y, x), m | (ce[0] << 10) | (ce[1] << 12))
    for (x, r), m in cell_id.items():
        setw(x, r, m, BLOCKED)
    for x, r, m, ce in kit():
        setw(x, r, m, ce)
    (engine / 'data/layouts/CherrygroveCity/map.bin').write_bytes(struct.pack('<%dH' % w.size, *w.ravel().tolist()))
    report['cells_changed'] = int((words != w).sum())
    # ---- check: every cell draws as rendered, and every mirror id draws the other map's pixels
    t = Tileset(engine, 'cherrygrove', 'cherrygrove')
    img = np.array(t.map_image(w.ravel().tolist(), CG_W).convert('RGB'))
    before = np.array(t0.map_image(words.ravel().tolist(), CG_W).convert('RGB'))
    after = expected(before, changed, lay, t0)
    bad = [[x, r] for (x, r) in cell_id if (rgb5(img[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16]) != rgb5(after[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16])).any()]
    assert not bad, ('cells draw wrongly', bad)
    for m in ids:
        assert (rgb5(np.array(t.render(m).convert('RGB'))) == rgb5(defs[m][0])).all(), ('mirror id draws wrongly in Cherrygrove', m)
    report['cells_differing_from_render'] = 0
    Image.fromarray(img[:16 * 16, :56 * 16]).save(OUT / 'installed.png')
    (OUT / 'cherrygrove-wall.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report))

if __name__ == '__main__':
    eng = Path(sys.argv[1]).resolve()
    do_install(eng) if '--install' in sys.argv else do_render(eng)
