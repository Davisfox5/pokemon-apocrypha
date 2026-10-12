#!/usr/bin/env python3
"""Compose Route 29 and Route 30 and install them into a workbench that already has Claude's Cherrygrove.

The routes share the town's primary tileset (terrain, trees, cliff, sea, flowers, fences), so the ground and the
woods continue across both map connections. Every 8x8 tile the primary already holds is reused by its pixel
pattern; anything new (tall grass, ledges, rock walls, the Route 46 gate, Mr. Pokemon's house, the berry house)
goes into a secondary tileset of the route's own. Animated sea tiles are reused only for sea.

Seams. A GBA map keeps only its own tilesets in VRAM, so whatever the camera shows across a connection is drawn
with the current map's tilesets (seams.py measures exactly which cells). Two rules keep both sides correct:
  - route cells the town can see use primary metatiles only (appended to the shared primary table, with any
    missing tile appended to the primary pool) and only palettes the town shares (0-5, and 10/11, which every
    secondary here keeps identical: the blossom recolour and the wood props);
  - town cells a route can see are copied into that route's secondary at the very same metatile and tile ids,
    with the town's palette banks for them, so they resolve to the same picture from the route.

Writes into the workbench: the two route secondaries and their C declarations, the appended primary entries, both
layouts (the old stubs' layout ids are kept, so the town's connections and the map-proof index still apply),
both map.json/scripts.inc, the town's two connection offsets, wild encounter tables (JOHTO_BATTLES.md, day column),
one hidden-item flag, the Route 29/30 map sections, and an engine guard that skips random wild battles while the
party is empty. It runs the town build first (into a scratch folder for the town's own previews), so the primary
it extends is always the town's own:

    python3 tools/gba/maps/claude_routes/build.py tools/vendor/gba/claude-routes
"""
from __future__ import annotations
import json, struct, sys, tempfile
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from tiles import Tileset, palette as read_pal  # noqa: E402
from claude_cherrygrove import build as town, ground, hgss, banks  # noqa: E402
from claude_cherrygrove import layout as TL  # noqa: E402
from claude_cherrygrove.build import MapCanvas, index_ground, write_pal, COVERED, NORMAL  # noqa: E402
from claude_cherrygrove.pixel import Palette  # noqa: E402
from claude_routes import art, layouts as L, seams  # noqa: E402

ROOT = HERE.parents[3]
OUT = ROOT / 'gba/art/claude-routes'
G_, P_, W_ = ground.GRASS, ground.PATH, ground.SEA
MB_TALL_GRASS, MB_POND, MB_OCEAN, MB_SIGNPOST, MB_JUMP_SOUTH = 2, 16, 21, 29, 59
LEDGE = set('_abc')
HIDDEN_FLAG = 'FLAG_HIDDEN_ITEM_APOC_ROUTE29_POTION'
HIDDEN_FLAG_SLOT = 'FLAG_UNUSED_0x264'
SHARED_BANKS = {10, 11}     # identical in the town's and both routes' secondaries

# ----------------------------------------------------------------- tilesets

def read_tiles(path):
    a = np.array(Image.open(path)); rows, cols = a.shape[0] // 8, a.shape[1] // 8
    return [a[r * 8:r * 8 + 8, c * 8:c * 8 + 8].astype(np.uint8).copy() for r in range(rows) for c in range(cols)]

def write_tiles(path, tiles):
    n = max(len(tiles), 1); rows = (n + 15) // 16
    im = Image.new('P', (128, rows * 8), 0); grey = []
    for i in range(16): grey += [i * 16] * 3
    im.putpalette(grey + [0] * (768 - len(grey))); px = im.load()
    for i, arr in enumerate(tiles):
        if arr is None: continue
        for yy in range(8):
            for xx in range(8): px[(i % 16) * 8 + xx, (i // 16) * 8 + yy] = int(arr[yy, xx])
    im.save(path, bits=4)

class Primary:
    """The town's primary tileset, extended in place with the entries route seam cells need."""
    def __init__(self, game, n_anim, n_tiles):
        self.folder = game / 'data/tilesets/primary/cherrygrove'
        self.tiles = read_tiles(self.folder / 'tiles.png')[:n_tiles]     # drop the sheet's blank padding
        self.blocks = list(struct.iter_unpack('<8H', (self.folder / 'metatiles.bin').read_bytes()))
        self.attrs = list(struct.unpack('<' + 'H' * len(self.blocks), (self.folder / 'metatile_attributes.bin').read_bytes()))
        self.n_tiles0, self.n_blocks0 = len(self.tiles), len(self.blocks)
        self.animated = set(range(1, 1 + n_anim))
        self.lookup = {}
        for tid, t in enumerate(self.tiles): self._index(tid, t)
        self.block_lookup = {(tuple(b), a): i for i, (b, a) in enumerate(zip(self.blocks, self.attrs))}
    def _index(self, tid, t):
        for hf in (0, 1):
            for vf in (0, 1):
                a = t[::-1] if vf else t; a = a[:, ::-1] if hf else a
                self.lookup.setdefault(a.tobytes(), (tid, hf, vf))
    def find(self, bank, arr):
        hit = self.lookup.get(arr.tobytes())
        if hit is None: return None
        tid, hf, vf = hit; sea = tid in self.animated
        if (bank == 1) != sea or (sea and (hf or vf)): return None
        return tid | (hf << 10) | (vf << 11)
    def add_tile(self, arr):
        tid = len(self.tiles)
        if tid >= 512: raise SystemExit('primary tile budget exhausted by seam cells')
        self.tiles.append(arr.copy()); self._index(tid, arr); return tid
    def add_block(self, entries, attr):
        key = (tuple(entries), attr)
        if key in self.block_lookup: return self.block_lookup[key]
        mid = len(self.blocks); assert mid < 512, 'primary metatile budget exhausted by seam cells'
        self.blocks.append(tuple(entries)); self.attrs.append(attr); self.block_lookup[key] = mid; return mid
    def write(self):
        write_tiles(self.folder / 'tiles.png', self.tiles)
        (self.folder / 'metatiles.bin').write_bytes(b''.join(struct.pack('<8H', *b) for b in self.blocks))
        (self.folder / 'metatile_attributes.bin').write_bytes(struct.pack('<' + 'H' * len(self.attrs), *self.attrs))

class RoutePacker(town.Packer):
    """Primary first; seam cells stay in the primary; everything else fills the route's secondary around the
    town tiles and metatiles reserved at their own ids."""
    def __init__(self, palettes, primary):
        super().__init__(palettes)
        self.primary = primary; self.force = False
        self.sec_tiles = {}; self.slookup = {}; self.sec_blocks = {}; self.sblock_lookup = {}
        self.next_tile = 512; self.next_block = 512
    def reserve(self, town_tiles, town_blocks, town_attrs, mids):
        for m in sorted(mids):
            entries = town_blocks[m - 512]
            for e in entries:
                tid = e & 1023
                if tid >= 512 and tid not in self.sec_tiles:
                    arr = town_tiles[tid - 512]; self.sec_tiles[tid] = arr; self.slookup.setdefault(arr.tobytes(), tid)
            self.sec_blocks[m] = (tuple(entries), town_attrs[m - 512]); self.sblock_lookup[(tuple(entries), town_attrs[m - 512])] = m
    def tile(self, bank, arr, pos=None):
        hit = self.primary.find(bank, arr)
        if hit is not None: return hit
        if self.force: return self.primary.add_tile(arr)
        for hf in (0, 1):
            for vf in (0, 1):
                a = arr[::-1] if vf else arr; a = a[:, ::-1] if hf else a
                if a.tobytes() in self.slookup: return self.slookup[a.tobytes()] | (hf << 10) | (vf << 11)
        while self.next_tile in self.sec_tiles: self.next_tile += 1
        tid = self.next_tile
        if tid >= 1024: raise SystemExit('secondary tile budget exhausted')
        self.sec_tiles[tid] = arr.copy(); self.slookup[arr.tobytes()] = tid
        return tid
    def metatile(self, entries, attr):
        if self.force:
            assert all((e & 1023) < 512 for e in entries)
            return self.primary.add_block(entries, attr)
        key = (tuple(entries), attr)
        if key in self.primary.block_lookup: return self.primary.block_lookup[key]
        if key in self.sblock_lookup: return self.sblock_lookup[key]
        while self.next_block in self.sec_blocks: self.next_block += 1
        mid = self.next_block; assert mid < 1024, 'secondary metatile budget exhausted'
        self.sec_blocks[mid] = key; self.sblock_lookup[key] = mid; return mid

def route_grid(comp, packer, palettes, forced, allowed_banks):
    """grid_for, with the cells in `forced` packed into the primary under the shared-palette rule."""
    Wd, Ht, mc = comp['W'], comp['H'], comp['canvas']
    gimg, mat = ground.paint(comp['cells'])
    gbank, gidx = index_ground(gimg, mat, palettes)
    grid = []; problems = []
    for y in range(Ht):
        for x in range(Wd):
            packer.force = bool(forced[y, x])
            entries, opaque = packer.slice(mc.bank, mc.idx, x, y)
            beh = int(comp['behavior'][y, x]); col = 0xC00 if comp['solid'][y, x] else 0
            if opaque and not mc.above[y, x]:
                ent, attr = entries + [0, 0, 0, 0], beh | COVERED
            else:
                base, _ = packer.slice(gbank, gidx, x, y, ground_tag=comp['tag'])
                if all(e == 0 for e in entries): ent, attr = base + [0, 0, 0, 0], beh
                elif mc.above[y, x]: ent, attr = base + entries, beh | NORMAL
                else: ent, attr = base + entries, beh | COVERED
            if packer.force:
                bad = {e >> 12 for e in ent if e} - allowed_banks
                if bad: problems.append((x, y, sorted(bad)))
            grid.append(packer.metatile(ent, attr) | (0x3 << 12) | col)
    packer.force = False
    if problems: raise SystemExit(f'{comp["tag"]}: cells the town can see use route-only palettes: {problems[:20]}')
    comp['mat'] = mat
    return grid, gimg

# ----------------------------------------------------------------- per-route scenery banks

def route_banks(route, town_assets, town_palettes, reserved):
    """Indexed scenery for one route. Town assets keep their banks; new pieces take the secondary banks that the
    town copies (reserved) and the shared blossom/wood banks leave free."""
    A = dict(town_assets)
    sl = art.tall_slices(); groups = []
    tall = [(f'tall{n}{s}{w}{e}', art.tall_cell(sl, n, s, w, e)) for n in (0, 1) for s in (0, 1) for w in (0, 1) for e in (0, 1)]
    ledge = list(art.ledges().items())
    flora = [('orange', art.orange_flowers(route))]
    if route == 29:
        flora.append(('apricorn', art.apricorn()))
        groups = [('TALL', tall), ('LEDGE', ledge), ('GATE', [('gate', art.gate())]), ('FLORA', flora)]
    else:
        ledge += list(art.cliff_pieces().items()) + [('stairs_' + k, art.stairs(k)) for k in ('top', 'mid', 'low')]
        flora.append(('berry_tree', art.berry_tree()))
        groups = [('TALL', tall), ('LEDGE', ledge), ('MRPOKEMON', [('mr_pokemon', art.mr_pokemon_house())]),
                  ('BERRYHOUSE', [('berry_house', art.berry_house())]), ('FLORA', flora)]
    free = [b for b in range(6, 13) if b not in reserved and b not in SHARED_BANKS]
    if len(groups) > len(free):     # one bank short: the flowers and the berry tree share the tall grass bank
        tall_i = [i for i, g in enumerate(groups) if g[0] == 'TALL'][0]; fl = [g for g in groups if g[0] == 'FLORA'][0]
        groups[tall_i] = ('TALL', groups[tall_i][1] + fl[1]); groups.remove(fl)
    assert len(groups) <= len(free), (route, groups, free)
    pals = {k: v for k, v in town_palettes.items() if k <= 5 or k in SHARED_BANKS}
    assignment = {}
    for (name, items), b in zip(groups, free):
        bank = banks.Bank(b, name, 'secondary')
        for k, v in items: bank.add(k, v)
        A.update(bank.build()); pals[b] = bank.palette; assignment[name] = b
    return A, pals, assignment

# ----------------------------------------------------------------- composition

def compose(route, g, A):
    Ht, Wd = g.shape
    cells = np.full((Ht, Wd), G_, dtype=np.int8)
    solid = np.zeros((Ht, Wd), dtype=bool)
    behavior = np.zeros((Ht, Wd), dtype=np.uint8)
    mc = MapCanvas(Wd, Ht)
    objects = []
    report = Counter()
    def obj(c, cx, cy, sort=None, flip=False, py=None, px=None):
        ypx = cy * 16 if py is None else py; xpx = cx * 16 if px is None else px
        objects.append(((ypx + c.h - 1) if sort is None else sort, xpx, ypx, c, flip))
    g = g.copy()

    # Buildings first: they claim their cells (no trees there) and set their own collision from coverage.
    def building(c, cx, cy, py=0, walkable_rows=()):
        obj(c, cx, cy, py=cy * 16 + py)
        a = c.px != 0
        for yy in range(cy, cy + (c.h + 15 - py) // 16 + 1):
            for xx in range(cx, cx + c.w // 16):
                if not (0 <= yy < Ht and 0 <= xx < Wd): continue
                y0 = yy * 16 - (cy * 16 + py); sub = a[max(y0, 0):max(y0 + 16, 0), (xx - cx) * 16:(xx - cx) * 16 + 16]
                cover = sub.sum() / 256 if sub.size else 0
                if cover > 0.05 and g[yy, xx] == 'T': g[yy, xx] = '.'
                if cover > 0.45 and yy not in walkable_rows: solid[yy, xx] = True
    if route == 29:
        gx, gy = L.R29_GATE; building(A['gate'], gx, gy, walkable_rows=(9,))
        solid[8, 52] = True        # the gate's door: closed in this build
        ax, ay = L.R29_APRICORN; obj(A['apricorn'], ax, ay); solid[ay + 2, ax + 1] = True
    else:
        mx, my = L.R30_MR_POKEMON; building(A['mr_pokemon'], mx, my, py=-4)
        bx, by = L.R30_BERRY_HOUSE; building(A['berry_house'], bx, by)
        for (tx, ty) in L.R30_BERRY_TREES: obj(A['berry_tree'], tx, ty); solid[ty + 1, tx + 1] = True

    # Ground materials.
    for y in range(Ht):
        for x in range(Wd):
            ch = g[y, x]
            if ch in 'P=': cells[y, x] = P_
            elif ch == 'W': cells[y, x] = W_; solid[y, x] = True; behavior[y, x] = MB_POND
    if route == 29:
        cy0, cy1 = L.R29_COAST
        for x in range(Wd):
            if g[cy0 - 1, x] == 'T': g[cy0 - 1, x] = 'k'          # the cliff-top lawn under the last row of trees
            for y in range(cy0, Ht): g[y, x] = 'C'
            cells[cy1:, x] = W_; solid[cy0 - 1:, x] = True; behavior[cy1 + 1:, x] = MB_OCEAN
        for x in range(0, Wd, 2):
            obj(A['cliff'], x, cy0, sort=cy1 * 16 + 15)

    # Trees on the HGSS lattice wherever the whole footprint is forest.
    xpar, phase = L.R29_LATTICE if route == 29 else L.R30_LATTICE
    covered = np.zeros((Ht, Wd), bool); trees = []
    def fits(x0, ypx):
        r0, r1 = ypx // 16, (ypx + 31) // 16
        cols = [xx for xx in (x0, x0 + 1) if 0 <= xx < Wd]; rows = [yy for yy in range(r0, r1 + 1) if 0 <= yy < Ht]
        return (cols and rows and all(g[yy, xx] == 'T' for yy in rows for xx in cols)), cols, rows
    for x in range(xpar - 2, Wd, 2):
        for ypx in range(phase - 48, Ht * 16, 24):
            ok, cols, rows = fits(x, ypx)
            if ok: trees.append((x, ypx)); covered[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1] = True
    # Fillers: a forest cell the strict lattice misses (an odd-column edge, a short strip) gets a tree one column
    # off the lattice when that tree's whole footprint is forest. HGSS edges are just as ragged.
    for y in range(Ht):
        for x in range(Wd):
            if g[y, x] != 'T' or covered[y, x]: continue
            placed = False
            for x0 in (x - 1, x):
                for ypx in range(phase - 48, Ht * 16, 24):
                    if not (ypx // 16 <= y <= (ypx + 31) // 16): continue
                    ok, cols, rows = fits(x0, ypx)
                    if ok:
                        trees.append((x0, ypx)); covered[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1] = True; report['filler_trees'] += 1; placed = True; break
                if placed: break
    trees.sort(key=lambda t: (t[1], t[0]))
    def front(x, ypx):
        r1 = (ypx + 31) // 16 + 1
        return 0 <= r1 < Ht and any(0 <= xx < Wd and g[r1, xx] not in 'TkC' for xx in (x, x + 1))
    for (x, ypx) in trees:
        kind = 'blossom' if route == 29 and x <= L.R29_BLOSSOM_MAX_X and front(x, ypx) else 'tree'
        if kind == 'blossom': report['blossom_trees'] += 1
        obj(A[kind], x, 0, py=ypx - hgss.TREE_TIP[1], px=x * 16 - hgss.TREE_TIP[0])
    report['trees'] = len(trees)
    for y in range(Ht):
        for x in range(Wd):
            if g[y, x] != 'T': continue
            if covered[y, x]: solid[y, x] = True; continue
            # A forest cell no tree reaches shows as lawn. It stays walkable as a woodland margin unless it touches a
            # ledge, wall, rock or water, where walking it would get round the end of that barrier.
            barrier = any(0 <= y + dy < Ht and 0 <= x + dx < Wd and g[y + dy, x + dx] in '_|^abc#F=Wk' for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if barrier: solid[y, x] = True; report['margin_cells_solid'] += 1
            else: report['margin_cells_walkable'] += 1
    # Tall grass, ledges, walls, rock, steps, railing.
    isG = g == 'G'
    for y in range(Ht):
        for x in range(Wd):
            ch = g[y, x]
            if ch == 'G':
                nb = lambda yy, xx: bool(isG[yy, xx]) if 0 <= yy < Ht and 0 <= xx < Wd else True
                key = f'tall{int(nb(y - 1, x))}{int(nb(y + 1, x))}{int(nb(y, x - 1))}{int(nb(y, x + 1))}'
                obj(A[key], x, y, sort=-2); behavior[y, x] = MB_TALL_GRASS
            elif ch == '_':
                wl = x > 0 and g[y, x - 1] in LEDGE; el = x + 1 < Wd and g[y, x + 1] in LEDGE
                piece = 'ledge_l' if not wl else 'ledge_r' if not el else ('ledge_a' if x % 2 == 0 else 'ledge_b')
                obj(A[piece], x, y, sort=-1); solid[y, x] = True; behavior[y, x] = MB_JUMP_SOUTH
            elif ch in '|^abc':
                piece = {'|': 'wall', '^': 'wall_top', 'a': 'corner_se', 'b': 'corner_sw', 'c': 'ledge_r'}[ch]
                obj(A[piece], x, y, sort=-1); solid[y, x] = True
            elif ch == '#':
                if y <= 1: piece = f'corner{y}{x - 32}' if x >= 32 else f'top{y}'
                elif x >= 32: piece = f'east{x - 32}'
                elif (x > 0 and g[y, x - 1] in '#=') or (x + 1 < Wd and g[y, x + 1] in '#='): piece = 'cross'
                else: piece = 'west'
                obj(A[piece], x, y, sort=-1); solid[y, x] = True
            elif ch == 'F':
                obj(A['fence_h'], x, y); solid[y, x] = True
    if route == 30:
        for kind, sx, sy, dy in L.R30_STAIRS: obj(A['stairs_' + kind], sx, sy, py=sy * 16 + dy, sort=-1)
    # Flowers, signs, benches.
    for (x, y) in (L.R29_ORANGE if route == 29 else L.R30_ORANGE):
        if g[y, x] == '.' and not solid[y, x]: obj(A['orange'], x, y, sort=-3)
    for (x, y) in (L.R29_DAISIES if route == 29 else L.R30_DAISIES):
        if (g[y:y + 2, x:x + 3] == '.').all(): obj(A['daisies'], x, y, sort=-3)
    signs = L.R29_SIGNS if route == 29 else L.R30_SIGNS
    for (name, x, y) in signs:
        obj(A['sign'], x, y - 1, sort=y * 16 + 15); solid[y, x] = True; behavior[y, x] = MB_SIGNPOST; mc.above[y - 1, x] = True
    if route == 29:
        for (x, y) in L.R29_BENCHES: obj(A['bench'], x, y); solid[y, x] = True
    for _, px, py, c, flip in sorted(objects, key=lambda o: (o[0], o[1])): mc.blit(c, px, py, flip)
    return dict(cells=cells, solid=solid, behavior=behavior, canvas=mc, W=Wd, H=Ht, plan=g, report=report, signs=signs, tag=f'r{route}')

# ----------------------------------------------------------------- engine writing

def write_route_tileset(game, name, packer, palettes):
    folder = game / f'data/tilesets/secondary/{name}'; (folder / 'palettes').mkdir(parents=True, exist_ok=True)
    for bank in range(16):
        pal = palettes.get(bank) if bank >= 6 else None
        write_pal(folder / 'palettes' / f'{bank:02}.pal', pal.gba() if pal else [(0, 0, 0)] * 16)
    n = max(packer.sec_tiles) - 511 if packer.sec_tiles else 1
    write_tiles(folder / 'tiles.png', [packer.sec_tiles.get(512 + i) for i in range(n)])
    nb = max(packer.sec_blocks) - 511 if packer.sec_blocks else 0
    blocks = [packer.sec_blocks.get(512 + i, ((0,) * 8, 0)) for i in range(nb)]
    (folder / 'metatiles.bin').write_bytes(b''.join(struct.pack('<8H', *b[0]) for b in blocks))
    (folder / 'metatile_attributes.bin').write_bytes(struct.pack('<' + 'H' * len(blocks), *[b[1] for b in blocks]))
    return n, nb

def register_tilesets(game, names):
    """C declarations for the route secondaries (idempotent: the marked block is replaced)."""
    def splice(path, block):
        s = path.read_text(); a, b = s.find('// Claude routes'), s.find('// End Claude routes\n')
        if a >= 0: s = s[:a].rstrip('\n') + '\n' + s[b + len('// End Claude routes\n'):]
        s = s.rstrip('\n') + '\n\n// Claude routes\n' + block + '// End Claude routes\n'
        path.write_text(s)
    gfx, meta, head = '', '', ''
    for n in names:
        sym = ''.join(p.capitalize() for p in n.split('_'))
        gfx += f'const u32 gTilesetTiles_{sym}[] = INCGFX_U32("data/tilesets/secondary/{n}/tiles.png", ".4bpp.fastSmol");\n'
        gfx += f'const u16 gTilesetPalettes_{sym}[][16] = {{\n' + ''.join(f'INCGFX_U16("data/tilesets/secondary/{n}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n'
        meta += f'const u16 gMetatiles_{sym}[] = INCBIN_U16("data/tilesets/secondary/{n}/metatiles.bin");\n'
        meta += f'const u16 gMetatileAttributes_{sym}[] = INCBIN_U16("data/tilesets/secondary/{n}/metatile_attributes.bin");\n'
        head += (f'const struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, .isSecondary = TRUE, .tiles = gTilesetTiles_{sym}, '
                 f'.palettes = gTilesetPalettes_{sym}, .metatiles = gMetatiles_{sym}, .metatileAttributes = gMetatileAttributes_{sym}, .callback = NULL }};\n')
    splice(game / 'src/data/tilesets/graphics.h', gfx)
    splice(game / 'src/data/tilesets/metatiles.h', meta)
    splice(game / 'src/data/tilesets/headers.h', head)
    return {n: 'gTileset_' + ''.join(p.capitalize() for p in n.split('_')) for n in names}

def write_layout(game, layouts, name, grid, Wd, Ht, border, secondary):
    folder = game / f'data/layouts/{name}'; folder.mkdir(parents=True, exist_ok=True)
    (folder / 'map.bin').write_bytes(struct.pack('<' + 'H' * len(grid), *grid))
    (folder / 'border.bin').write_bytes(struct.pack('<4H', *border))
    for lay in layouts['layouts']:
        if lay['name'] == name + '_Layout':
            lay['width'] = Wd; lay['height'] = Ht; lay['secondary_tileset'] = secondary; lay['primary_tileset'] = 'gTileset_CherrygrovePrimary'

SIGN_TEXT = {
    'WestSign': 'ROUTE 29\\nCHERRYGROVE CITY - NEW BARK TOWN',
    'EastSign': 'ROUTE 29\\nCHERRYGROVE CITY - NEW BARK TOWN',
    'JunctionSign': 'MR. POKéMON\'S HOUSE\\nSTRAIGHT AHEAD!',
    'RouteSign': 'ROUTE 30\\nVIOLET CITY - CHERRYGROVE CITY',
}

def write_map(game, route, comp):
    name = f'CherrygroveRoute{route}Approach'; mp = game / f'data/maps/{name}/map.json'; m = json.loads(mp.read_text())
    m.update(music='MUS_ROUTE101', map_type='MAP_TYPE_ROUTE', show_map_name=True, region_map_section=f'MAPSEC_JOHTO_ROUTE_{route}', allow_cycling=True, allow_running=True)
    if route == 29: m['connections'] = [dict(map='MAP_CHERRYGROVE_CITY', offset=-L.R29_TOWN_OFFSET, direction='left')]
    else: m['connections'] = [dict(map='MAP_CHERRYGROVE_CITY', offset=-L.R30_TOWN_OFFSET, direction='down')]
    scripts = [f'{name}_MapScripts::\n    .byte 0\n']
    m['bg_events'] = []
    for sign, x, y in comp['signs']:
        label = f'{name}_{sign}'
        scripts.append(f'{label}::\n    msgbox {label}_Text, MSGBOX_SIGN\n    end\n\n{label}_Text:\n    .string "{SIGN_TEXT[sign]}$"\n')
        m['bg_events'].append(dict(type='sign', x=x, y=y, elevation=0, player_facing_dir='BG_EVENT_PLAYER_FACING_ANY', script=label))
    if route == 29:
        hx, hy = L.R29_HIDDEN_POTION
        m['bg_events'].append(dict(type='hidden_item', x=hx, y=hy, elevation=3, item='ITEM_POTION', flag=HIDDEN_FLAG))
    m['object_events'] = []; m['warp_events'] = []; m['coord_events'] = []
    mp.write_text(json.dumps(m, indent=2) + '\n')
    (game / f'data/maps/{name}/scripts.inc').write_text('\n'.join(scripts))
    city = game / 'data/maps/CherrygroveCity/map.json'; c = json.loads(city.read_text())
    for conn in c['connections']:
        if conn['map'] == 'MAP_CHERRYGROVE_ROUTE29_APPROACH': conn['offset'] = L.R29_TOWN_OFFSET
        if conn['map'] == 'MAP_CHERRYGROVE_ROUTE30_APPROACH': conn['offset'] = L.R30_TOWN_OFFSET
    city.write_text(json.dumps(c, indent=2) + '\n')

ENCOUNTERS = {
    # docs/JOHTO_BATTLES.md, Morning/Day column (this engine runs one table per map: OW_TIME_OF_DAY_ENCOUNTERS is off).
    29: [('PIDGEY', 2, 3), ('SENTRET', 2, 3), ('PIDGEY', 3, 4), ('SENTRET', 3, 4), ('RATTATA', 2, 3), ('PIDGEY', 2, 4),
         ('SENTRET', 2, 4), ('RATTATA', 3, 4), ('PIDGEY', 4, 4), ('SENTRET', 4, 4), ('RATTATA', 4, 4), ('RATTATA', 4, 4)],
    30: [('PIDGEY', 3, 4), ('RATTATA', 3, 4), ('PIDGEY', 4, 5), ('RATTATA', 4, 5), ('CATERPIE', 4, 5), ('WEEDLE', 4, 5),
         ('CATERPIE', 5, 6), ('WEEDLE', 5, 6), ('PIDGEY', 5, 5), ('RATTATA', 5, 5), ('BELLSPROUT', 5, 5), ('BELLSPROUT', 6, 6)],
}

def write_encounters(game):
    p = game / 'src/data/wild_encounters.json'; d = json.loads(p.read_text()); grp = d['wild_encounter_groups'][0]
    grp['encounters'] = [e for e in grp['encounters'] if e.get('map') not in ('MAP_CHERRYGROVE_ROUTE29_APPROACH', 'MAP_CHERRYGROVE_ROUTE30_APPROACH')]
    for route, slots in ENCOUNTERS.items():
        grp['encounters'].append({'map': f'MAP_CHERRYGROVE_ROUTE{route}_APPROACH', 'base_label': f'gCherrygroveRoute{route}Approach',
                                  'land_mons': {'encounter_rate': 20, 'mons': [dict(min_level=a, max_level=b, species='SPECIES_' + s) for s, a, b in slots]}})
    p.write_text(json.dumps(d, indent=2) + '\n')

def write_engine(game):
    # One hidden-item flag, aliased onto an unused slot inside the hidden-item range (Codex's campaign uses 0x020-0x02F).
    f = game / 'include/constants/flags.h'; s = f.read_text()
    line = f'#define {HIDDEN_FLAG} {HIDDEN_FLAG_SLOT} // Apocrypha: Route 29 lookout Potion (design bible: the route\'s one hidden item)\n'
    if HIDDEN_FLAG not in s:
        i = s.rfind('#endif'); s = s[:i] + line + '\n' + s[i:]; f.write_text(s)
    # No random wild battles while the party is empty (the opening walks the player through Route 30's grass first).
    c = game / 'src/field_control_avatar.c'; s = c.read_text()
    guard = '    if (CalculatePlayerPartyCount() == 0) // Apocrypha: no wild battles before the first Pokemon\n        return TRUE;\n\n'
    anchor = 'static bool32 ShouldDisableRandomEncounters(void)\n{\n'
    if 'Apocrypha: no wild battles' not in s:
        assert anchor in s; s = s.replace(anchor, anchor + guard, 1); c.write_text(s)
    # Map sections: ROUTE 29 and ROUTE 30 in Johto, beside Cherrygrove on the region map grid.
    j = game / 'src/data/region_map/region_map_sections.json'; d = json.loads(j.read_text()); secs = d['map_sections']
    secs[:] = [e for e in secs if e['id'] not in ('MAPSEC_JOHTO_ROUTE_29', 'MAPSEC_JOHTO_ROUTE_30')]
    i = next(k for k, e in enumerate(secs) if e['id'] == 'MAPSEC_CHERRYGROVE_CITY') + 1
    secs[i:i] = [dict(id='MAPSEC_JOHTO_ROUTE_29', name='ROUTE 29', x=4, y=6, width=1, height=1),
                 dict(id='MAPSEC_JOHTO_ROUTE_30', name='ROUTE 30', x=3, y=5, width=1, height=1)]
    j.write_text(json.dumps(d, indent=2) + '\n')
    r = game / 'include/regions.h'; s = r.read_text()
    if 'MAPSEC_JOHTO_ROUTE_29' not in s:
        s = s.replace('    case MAPSEC_CHERRYGROVE_CITY: return REGION_JOHTO;\n',
                      '    case MAPSEC_CHERRYGROVE_CITY: return REGION_JOHTO;\n    case MAPSEC_JOHTO_ROUTE_29: return REGION_JOHTO;\n    case MAPSEC_JOHTO_ROUTE_30: return REGION_JOHTO;\n', 1)
        assert 'MAPSEC_JOHTO_ROUTE_29' in s; r.write_text(s)

# ----------------------------------------------------------------- main

def run_town(game):
    """The town build, with its previews sent to a scratch folder (the town's committed evidence stays as it is)."""
    scratch = Path(tempfile.mkdtemp(prefix='claude-town-'))
    town.OUT = scratch; argv = sys.argv; sys.argv = [argv[0], str(game)]
    try:
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()): town.main()
    finally:
        sys.argv = argv
    return json.loads((scratch / 'build-report.json').read_text())

def main():
    game = Path(sys.argv[1]).resolve(); assert game != ROOT / 'game' and (game / '.git').is_dir()
    (OUT / 'evidence').mkdir(parents=True, exist_ok=True)
    town_report = run_town(game)
    town_assets, town_palettes = town.build_assets()
    primary = Primary(game, town_report['animated_sea_tiles'], town_report['primary_tiles'])
    tsec = game / 'data/tilesets/secondary/cherrygrove'
    town_tiles = read_tiles(tsec / 'tiles.png')
    town_blocks = list(struct.iter_unpack('<8H', (tsec / 'metatiles.bin').read_bytes()))
    town_attrs = list(struct.unpack('<' + 'H' * len(town_blocks), (tsec / 'metatile_attributes.bin').read_bytes()))
    town_pals = {b: Palette(b, read_pal(tsec / 'palettes' / f'{b:02}.pal')[1:], [f'c{i}' for i in range(15)]) for b in range(6, 13)}
    tmid, tsol = seams.read_layout(game, 'CherrygroveCity', TL.W, TL.H)
    treach = seams.reachable(tsol, TL.SPAWN)
    border = list(struct.unpack('<4H', (game / 'data/layouts/CherrygroveCity/border.bin').read_bytes()))
    layouts = json.loads((game / 'data/layouts/layouts.json').read_text())
    names = {29: 'claude_route29', 30: 'claude_route30'}; syms = register_tilesets(game, list(names.values()))
    report = {}; previews = {}
    for route in (29, 30):
        g = L.route29() if route == 29 else L.route30()
        Wd, Ht = g.shape[1], g.shape[0]
        ox, oy = (TL.W, L.R29_TOWN_OFFSET) if route == 29 else (L.R30_TOWN_OFFSET, -L.R30_H)   # route (0,0) in town coordinates
        # First pass with provisional banks, only to learn the route's collision for the seam analysis.
        A0, _, _ = route_banks(route, town_assets, town_palettes, set())
        comp0 = compose(route, g, A0)
        start = (0, 16) if route == 29 else (8, Ht - 1)
        rreach = seams.reachable(comp0['solid'], start)
        town_seen = seams.visible_across(rreach, (TL.H, TL.W), -ox, -oy)          # town cells on screen from the route
        route_seen = seams.visible_across(treach, (Ht, Wd), ox, oy)               # route cells on screen from the town
        tw, rw, crossings = seams.crossing_windows(tsol, comp0['solid'], ox, oy)  # both sides of the BG window at a crossing
        town_seen |= tw; route_seen |= rw
        town_mids = {int(m) for m in tmid[town_seen] if m >= 512}
        town_banks = {e >> 12 for m in town_mids for e in town_blocks[m - 512] if e} - set(range(6))
        A, pals, assignment = route_banks(route, town_assets, town_palettes, town_banks - SHARED_BANKS)
        for b in town_banks: pals[b] = town_pals[b]
        comp = compose(route, g, A)
        packer = RoutePacker(pals, primary)
        packer.reserve(town_tiles, town_blocks, town_attrs, town_mids)
        grid, gimg = route_grid(comp, packer, pals, route_seen, set(range(6)) | SHARED_BANKS | town_banks)
        n_tiles, n_blocks = write_route_tileset(game, names[route], packer, pals)
        write_layout(game, layouts, f'CherrygroveRoute{route}Approach', grid, Wd, Ht, border, syms[names[route]])
        write_map(game, route, comp)
        np.save(OUT / f'route{route}-plan.npy', comp['plan'])
        (OUT / f'route{route}-collision.txt').write_text('\n'.join(''.join('#' if comp['solid'][y, x] else '.' for x in range(Wd)) for y in range(Ht)) + '\n')
        used = {e & 1023 for k in packer.sec_blocks for e in packer.sec_blocks[k][0] if (e & 1023) < 512}
        report[f'route{route}'] = dict(width=Wd, height=Ht, secondary_tiles=len(packer.sec_tiles), secondary_tile_span=n_tiles,
                                       secondary_metatiles=len(packer.sec_blocks), secondary_metatile_span=n_blocks,
                                       town_metatiles_copied_for_the_seam=len(town_mids), town_palette_banks_copied=sorted(town_banks - SHARED_BANKS),
                                       seam_cells_in_primary=int(route_seen.sum()), seam_crossing_cells=crossings, reused_primary_tiles=len(used),
                                       palette_banks={k: v for k, v in sorted(assignment.items(), key=lambda kv: kv[1])},
                                       bank_conflict_tiles=packer.conflicts, **dict(comp['report']))
        previews[route] = (grid, Wd)
    primary.write()
    report['primary_appended'] = dict(tiles=len(primary.tiles) - primary.n_tiles0, metatiles=len(primary.blocks) - primary.n_blocks0,
                                      tiles_total=len(primary.tiles), metatiles_total=len(primary.blocks))
    (game / 'data/layouts/layouts.json').write_text(json.dumps(layouts, indent=2) + '\n')
    write_encounters(game); write_engine(game)
    for route, (grid, Wd) in previews.items():
        Tileset(game, names[route], 'cherrygrove').map_image(grid, Wd).save(OUT / f'route{route}-overview.png')
    (OUT / 'build-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=1))

if __name__ == '__main__':
    main()
