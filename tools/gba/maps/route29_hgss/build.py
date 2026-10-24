#!/usr/bin/env python3
"""Route 29 reconstructed from the decoded HGSS map data, as editable Porymap source.

Reference (docs/GBA_MAP_RECONSTRUCTION.md, step 1)
    The geographic authority is the actual HeartGold data in the archived DS tree:
    the EVERYWHERE map matrix places Route 29 on three 32x32 land-data chunks
    (files/a/0/6/5), and every cell of those chunks carries a terrain-type byte and
    a collision byte. That gives the material layer (lawn, dirt, tall grass, forest,
    one-way ledge, ledge wall, gate door) and the traversal layer (blocked / open /
    jump-south) independently, per cell, without tracing a screenshot. The original
    events (signs, warps, item, objects) come from the decoded zone_event file.
    The 1:1 Bulbagarden render supplies texture only (tall grass, ledges, gate,
    Apricorn tree, flowers, sign); it is not registered well enough to decide cells.

Reconstruction (step 2)
    96 x 32 HGSS cells. Map cell (x, y) = HGSS cell (x - 1, y - 3) inside the
    reconstructed region, columns 10-87 and rows 3-31. Two ten-column town adapters
    (columns 0-9 and 88-97) and the owner's sea ridge/lookout (the accepted map's
    rows 29-47, moved to rows 32-50 so no HGSS ground is lost) are carried over from
    the accepted layout and listed as adaptations. HGSS rows 29-31, all forest, are
    replaced by the ridge. Materials and traversal are written out as separate grids.

Art (step 3)
    Accepted Cherrygrove primary art for lawn, dirt kit, 2x2 trees and the blossom
    tree; the route's own pieces sliced at 16 px from the render into a new secondary
    tileset `route29_hgss`. Trees are placed as complete 2x2 trees on exclusive
    footprints; forest cells that cannot host a whole tree are resolved explicitly
    (absorb an adjacent lawn cell, or open the cell) and every such decision is
    recorded with a connectivity check so no original barrier opens.

Usage, from the hub root, against an engine checkout of the apocrypha branch:
    python3 tools/gba/maps/route29_hgss/build.py /path/to/apocrypha-src

Writes the tileset, layout, layouts.json, map.json event moves, the three tileset
registration headers, and source/evidence under gba/art/route29-hgss/.
Original designs and art: Game Freak / Nintendo / Creatures (read-only derivation).
"""
from __future__ import annotations
import csv, glob, hashlib, json, re, struct, subprocess, sys
from collections import Counter, defaultdict, deque
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parents[2] / 'mapeditor')); sys.path.insert(0, str(HERE.parents[2] / 'regionport'))
from claude_routes import art as ra
from tiles import Tileset, palette as read_pal
from mapdata import MapMatrix
from narc import narc_read

ROOT = HERE.parents[3]
GAME = Path(sys.argv[1]).resolve()
DS = ROOT / 'disasm/pokeheartgold'
OUT = ROOT / 'gba/art/route29-hgss'
TS_NAME, TS_SYM = 'route29_hgss', 'Route29Hgss'
MAP, LAYOUT = 'CherrygroveRoute29Approach', 'LAYOUT_CHERRYGROVE_ROUTE29_APPROACH'
BASE_REV = '2722eaf7601ec02dc5a684fa8cdef9206c0dc377'      # apocrypha branch: accepted layout the adapters and ridge come from
HW, HH = 96, 32                                                # HGSS Route 29
W, H = 98, 54                                                  # GBA map
COL0, ROW0 = 1, 3                                              # HGSS (hx, hz) -> map (hx + COL0, hz + ROW0)
REGION_COLS = range(10, 88)                                    # reconstructed columns; outside are the carried adapters
RIDGE_SRC, RIDGE_DST = 29, 35                                  # accepted ridge rows 29-47 -> 35-53 (a 6-row shift keeps the adapters' tree-band phase)
MATRIX_CELLS = [(18, 12), (19, 12), (20, 12)]                  # EVERYWHERE matrix cells with header MAP_ROUTE_29 (33)
WORLD_X0, WORLD_Z0 = 18 * 32, 12 * 32                          # HGSS world coordinates of HGSS cell (0, 0)
BLOSSOM_MAX_X = 26

# ----------------------------------------------------------------------------- engine constants
MB = {n: i for i, n in enumerate(re.findall(r'^\s+(MB_[A-Z0-9_]+),', (GAME / 'include/constants/metatile_behaviors.h').read_text(), re.M))}
COVERED, NORMAL = 1 << 12, 0
PRIM = Tileset(GAME, 'cherrygrove', 'cherrygrove')
LAWN = {(0, 0): 0x028, (1, 0): 0x027, (0, 1): 0x034, (1, 1): 0x033}
# The accepted tree is 2 wide x 3 tall: crown top, crown middle, trunk. Each row exists in two lawn phases (the
# only difference between the band's two trees is the lawn under them); the blossom tree has one phase.
TREE_ROWS = {'tree': [[(0x00A, 0x007), (0x042, 0x043)], [(0x00B, 0x00C), (0x00E, 0x014)], [(0x017, 0x018), (0x020, 0x01D)]],
             'blossom': [[(0x023, 0x024)], [(0x030, 0x031)], [(0x03F, 0x040)]]}
TW, TH = 2, 3
FOREST_BAND = [(0x00B, 0x00C), (0x017, 0x018), (0x00A, 0x007), (0x00E, 0x014), (0x020, 0x01D), (0x042, 0x043)]   # adapter filler only

# ----------------------------------------------------------------------------- 1. reference
def decode_hgss():
    mfile = glob.glob(str(DS / 'files/fielddata/mapmatrix/map_matrix/*0000*EVERYWHERE*'))[0]
    m = MapMatrix.parse(Path(mfile).read_bytes())
    land = narc_read(str(DS / 'files/a/0/6/5'))
    typ = np.zeros((HH, HW), np.uint8); col = np.zeros((HH, HW), np.uint8); models = []
    for i, (cx, cy) in enumerate(MATRIX_CELLS):
        assert m.headers[cy * m.width + cx] == 33, 'matrix cell is not Route 29'
        mid = m.models[cy * m.width + cx]; models.append(mid); mem = land[mid]
        magic, n = struct.unpack_from('<HH', mem, 16); p = mem[20 + n:20 + n + 0x800]
        for z in range(32):
            for x in range(32):
                k = (z * 32 + x) * 2; typ[z, i * 32 + x] = p[k]; col[z, i * 32 + x] = p[k + 1]
    ev = json.loads((DS / 'files/fielddata/eventdata/zone_event/030_R29.json').read_text())
    events = {}
    for kind in ('bgs', 'objects', 'warps', 'coords'):
        events[kind] = [dict(e, hx=e['x'] - WORLD_X0, hz=e['z'] - WORLD_Z0) for e in ev.get(kind, [])]
    ref = dict(matrix=Path(mfile).name, matrix_cells=MATRIX_CELLS, land_models=models,
               land_sha256=hashlib.sha256((DS / 'files/a/0/6/5').read_bytes()).hexdigest(),
               ds_tree=subprocess.check_output(['git', '-C', str(DS), 'rev-parse', 'HEAD'], text=True).strip(),
               size=[HW, HH], registration=dict(map_col=f'hx + {COL0}', map_row=f'hz + {ROW0}', region_cols=[10, 87], region_rows=[3, 31]),
               terrain_types={'0x00': 'ordinary ground (collision byte 0x04 = lawn, 0x00 = dirt)', '0x02': 'tall grass', '0x06': 'forest (blocked)',
                              '0x3b': 'one-way ledge, jump south', '0x38': 'ledge wall, high side west', '0x39': 'ledge wall, high side east',
                              '0x3e': 'ledge wall corner', '0x6e': 'gatehouse door'},
               render=dict(file='gba/art/claude-routes/references/route29-hgss.png', use='texture only; cell registration is approximate (about 50% cell agreement for tall grass), so it decides no cell'))
    return typ, col, events, ref

# ----------------------------------------------------------------------------- 2. material and traversal layers
def layers(typ, col, events):
    mat = np.full((HH, HW), '?', dtype='<U1')
    trav = np.full((HH, HW), 'X', dtype='<U1')          # X blocked, . open, v jump south, D door
    notes = []
    gate = {(x, z) for x in range(48, 54) for z in range(0, 6)}
    for z in range(HH):
        for x in range(HW):
            t, c = int(typ[z, x]), int(col[z, x]); blocked = bool(c & 0x80)
            if t == 0x06: mat[z, x], trav[z, x] = 'T', 'X'
            elif t == 0x02: mat[z, x], trav[z, x] = 'G', '.'
            elif t == 0x3b: mat[z, x], trav[z, x] = '_', 'v'
            elif t == 0x38: mat[z, x], trav[z, x] = '|', 'X'
            elif t == 0x39: mat[z, x], trav[z, x] = '!', 'X'
            elif t == 0x3e: mat[z, x], trav[z, x] = 'c', 'X'
            elif t == 0x6e: mat[z, x], trav[z, x] = 'D', 'D'
            elif t == 0x00:
                if (x, z) in gate: mat[z, x], trav[z, x] = 'g', 'X'
                elif blocked: mat[z, x], trav[z, x] = 'c', 'X'; notes.append((x, z, 'blocked ordinary ground: ledge corner or prop, see events'))
                elif c & 0x04: mat[z, x], trav[z, x] = '.', '.'
                else: mat[z, x], trav[z, x] = 'P', '.'
            else: notes.append((x, z, f'unknown terrain type {t:#x}'))
    # original objects that occupy ground
    for o in events['objects']:
        x, z = o['hx'], o['hz']
        if o['id'] == 'obj_R29_bonguri': mat[z, x], trav[z, x] = 'A', 'X'
        elif o['spriteId'] == 'SPRITE_TREE': mat[z, x], trav[z, x] = 'x', 'X'
    for b in events['bgs']:
        if b['type'] == 1 and 0 <= b['hx'] < HW: mat[b['hz'], b['hx']], trav[b['hz'], b['hx']] = 's', 'X'
    return mat, trav, notes

def decorations(mat):
    """Flowers and the light lawn patch: visible in the render only. Recorded as image-derived decoration."""
    deco = {}
    for z in range(HH):
        for x in range(HW):
            if mat[z, x] != '.': continue
            c = ra.cells(29, x + 1, z + 1)
            a = ra.clear(c, ra.GRASS29 + ra.PATH, 10); k = int((a[..., 3] > 0).sum())
            px = a[a[..., 3] > 0][:, :3].astype(int) if k else np.zeros((0, 3), int)
            if 8 <= k <= 90 and ((px[:, 0] > 200) & (px[:, 1] < 170)).any(): deco[(x, z)] = 'f'
            elif ra.near(c, [(120, 216, 176), (128, 216, 176), (136, 224, 184), (112, 208, 168), (120, 208, 168)], 10).mean() > 0.8: deco[(x, z)] = 'L'
    # the light patch is one rectangle in HGSS; the render registration frays its edge, so snap it to its bounding box
    L = {k for k, v in deco.items() if v == 'L'}
    for k in L: del deco[k]
    while L:                                                        # each 8-connected patch of at least four cells -> its bounding box
        comp = {L.pop()}; q = deque(comp)
        while q:
            x, z = q.popleft()
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    n = (x + dx, z + dz)
                    if n in L: L.remove(n); comp.add(n); q.append(n)
        if len(comp) < 4: continue
        xs, zs = [x for x, _ in comp], [z for _, z in comp]
        for z in range(min(zs), max(zs) + 1):
            for x in range(min(xs), max(xs) + 1):
                if mat[z, x] == '.' and (x, z) not in deco: deco[(x, z)] = 'L'
    return deco

# ----------------------------------------------------------------------------- 3. trees with real footprints
def place_trees(mat, trav):
    """Complete 2x3 trees over the forest mask, in map coordinates (region columns, rows 0..RIDGE_DST-1; the three
    padding rows above the HGSS origin are forest). A tree may stand one or two rows below the tree behind it so that
    its crown top overlaps that tree's trunk or middle row: that is the canopy stacking the HGSS forest shows and it
    is drawn with composite metatiles. Forest runs shorter than a tree absorb adjacent lawn when that keeps every open
    region connected. Returns anchors [(x, y)], the adaptation list and the final open mask."""
    X0, X1, Y1 = REGION_COLS.start, REGION_COLS.stop, RIDGE_DST
    forest = np.zeros((Y1, W), bool); openm = np.zeros((Y1, W), bool); lawn = np.zeros((Y1, W), bool)
    for y in range(Y1):
        for x in range(X0, X1):
            hz, hx = y - ROW0, x - COL0
            if hz < 0 or hz >= HH: forest[y, x] = True; continue
            forest[y, x] = mat[hz, hx] == 'T'; openm[y, x] = trav[hz, hx] != 'X'; lawn[y, x] = mat[hz, hx] == '.'
    used = np.zeros_like(forest); cover = np.zeros(forest.shape, np.int8); trees = []; anchors = set(); adapt = []
    def regions(m):
        lab = np.zeros(m.shape, np.int32); n = 0
        for y in range(Y1):
            for x in range(X0, X1):
                if m[y, x] and not lab[y, x]:
                    n += 1; q = deque([(y, x)]); lab[y, x] = n
                    while q:
                        cy, cx = q.popleft()
                        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < Y1 and X0 <= nx < X1 and m[ny, nx] and not lab[ny, nx]: lab[ny, nx] = n; q.append((ny, nx))
        return lab, n
    base_n = regions(openm)[1]
    def absorbable(cells):
        if any(not (0 <= y < Y1 and X0 < x < X1 - 1) or not lawn[y, x] or used[y, x] for x, y in cells): return False
        test = openm.copy()
        for x, y in cells: test[y, x] = False
        return regions(test)[1] == base_n
    def absorb(cells, why):
        for x, y in cells:
            openm[y, x] = False; lawn[y, x] = False; forest[y, x] = True
            adapt.append(dict(cell=[x, y], change='lawn absorbed under a whole tree (blocked)', reason=why))
    def place(ax, ay):
        used[ay:ay + TH, ax:ax + TW] = True; cover[ay:ay + TH, ax:ax + TW] += 1; trees.append((ax, ay)); anchors.add((ax, ay))
    def fill_run(x, y0, h):
        """Trees for the run rows y0..y0+h-1 of columns x, x+1. The run may start one row inside the tree directly
        above it (crown over that trunk). Strides are 2 (crown over trunk) with one 3 or 1 to make the parity."""
        start = y0 - 1 if (x, y0 - 3) in anchors else y0
        s = y0 + h - start
        if s < 3: return False
        gaps = s - 3
        strides = [2] * (gaps // 2)
        if gaps % 2: strides = (strides[:-1] + [3]) if gaps >= 3 else [1]
        p = start
        place(x, p)
        for st in strides: p += st; place(x, p)
        return True
    for parity in (X0 % 2, 1 - X0 % 2):
        for x in range(X0, X1 - 1):
            if x % 2 != parity: continue
            y = 0
            while y < Y1:
                ok = lambda yy: yy < Y1 and forest[yy, x] and forest[yy, x + 1] and not used[yy, x] and not used[yy, x + 1]
                if not ok(y): y += 1; continue
                y0 = y
                while ok(y): y += 1
                h = y - y0
                if fill_run(x, y0, h): continue
                need = 3 - h if (x, y0 - 3) not in anchors else 2 - h
                for cells in ([(x + j, y0 - k) for k in range(1, need + 1) for j in range(TW)],
                              [(x + j, y0 + h - 1 + k) for k in range(1, need + 1) for j in range(TW)],
                              [(x + j, y0 - 1) for j in range(TW)] + [(x + j, y0 + h) for j in range(TW)]):
                    if len(cells) == need * TW and absorbable(cells):
                        absorb(cells, f'forest run at columns {x}-{x + 1}, rows {y0}-{y0 + h - 1} is {h} rows, shorter than a tree')
                        ys = [cy for _, cy in cells] + list(range(y0, y0 + h)); fill_run(x, min(ys), max(ys) - min(ys) + 1); break
    # leftover cells (odd-width blobs, parity-straddling blocks): a whole tree that may absorb lawn beside it and may
    # overlap trees already placed (at most three deep), the HGSS canopy stacking. Fewest absorbed cells first,
    # then the most newly covered forest.
    for y in range(Y1):
        for x in range(X0, X1):
            if not forest[y, x] or used[y, x]: continue
            best = None
            for ax in (x - 1, x):
                for ay in (y - 2, y - 1, y):
                    cells = [(ax + j, ay + i) for i in range(TH) for j in range(TW)]
                    if any(not (0 <= cy < Y1 and X0 <= cx < X1) or cover[cy, cx] >= 3 for cx, cy in cells): continue
                    need = [(cx, cy) for cx, cy in cells if not forest[cy, cx]]
                    fresh = sum(1 for cx, cy in cells if forest[cy, cx] and not used[cy, cx])
                    if need and (any(used[cy, cx] for cx, cy in need) or not absorbable(need)): continue
                    score = (len(need), -fresh)
                    if best is None or score < best[0]: best = (score, (ax, ay), need)
            if best is None:
                adapt.append(dict(cell=[x, y], change='forest cell left without tree art; kept BLOCKED and drawn as lawn', reason='no whole-tree fit: no absorbable lawn and every overlap would stack more than three trees'))
                continue
            _, (ax, ay), need = best
            if need: absorb(need, f'forest cell {[x, y]} had no whole-tree fit')
            overlapped = [(cx, cy) for cx, cy in [(ax + j, ay + i) for i in range(TH) for j in range(TW)] if cover[cy, cx]]
            if overlapped: adapt.append(dict(cell=[x, y], change=f'whole tree at {[ax, ay]} overlaps earlier trees on {len(overlapped)} cells', reason='HGSS forest here is narrower than two native trees'))
            place(ax, ay)
    return trees, adapt, openm

# ----------------------------------------------------------------------------- tile packer (one secondary tileset)
class Packer:
    def __init__(self):
        self.pal = {}; self.pixels = defaultdict(list); self.tiles = [np.zeros((8, 8), np.uint8)]; self.lookup = {}; self.metatiles = []; self.attrs = []; self.mt_lookup = {}; self.reserved = {}
        # tile 0x200 stays blank and unused: after a map-connection crossing the engine showed the first secondary tile
        # of the newly loaded tileset as stale VRAM (seen on both sides of the New Bark seam); a direct warp is clean
    def bank_colors(self, bank):
        px = np.concatenate([a.reshape(-1, 3) for a in self.pixels[bank]]); u, n = np.unique(px, axis=0, return_counts=True)
        colors = [tuple(int(v) for v in c) for c in u]
        if len(colors) <= 15: return colors
        pop = np.repeat(u, n, axis=0).reshape(1, -1, 3).astype(np.uint8)
        q = Image.fromarray(pop).quantize(colors=15, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        qp = np.array(q.getpalette()[:45]).reshape(-1, 3); arr = np.array(colors, dtype=np.int32); out = []
        for c in qp:
            s = colors[int(((arr - c) ** 2).sum(1).argmin())]
            if s not in out: out.append(s)
        return out[:15]
    def finish(self, fixed):
        for b in list(self.pixels): self.pal[b] = fixed[b] if b in fixed else self.bank_colors(b)
        for b, p in fixed.items(): self.pal.setdefault(b, p)
    def index(self, rgb, bank):
        arr = np.array(self.pal[bank], dtype=np.int32); flat = rgb.reshape(-1, 3).astype(np.int32)
        return (((flat[:, None, :] - arr[None]) ** 2).sum(-1).argmin(1) + 1).reshape(rgb.shape[:2]).astype(np.uint8)
    def tile(self, idx8, bank):
        for hf in (0, 1):
            for vf in (0, 1):
                a = idx8[::-1] if vf else idx8; a = a[:, ::-1] if hf else a
                if a.tobytes() in self.lookup: return (512 + self.lookup[a.tobytes()]) | (hf << 10) | (vf << 11) | (bank << 12)
        assert len(self.tiles) < 512, 'secondary tile budget exceeded'
        t = len(self.tiles); self.tiles.append(idx8.copy()); self.lookup[idx8.tobytes()] = t
        return (512 + t) | (bank << 12)
    def metatile(self, rgb16, bank, attr):
        idx = self.index(rgb16, bank)
        ents = [self.tile(idx[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8], bank) for q in range(4)] + [0, 0, 0, 0]
        return self.raw(ents, attr)
    def layered(self, ground_mid, overlay_rgba, bank, attr):
        """Ground metatile (primary, both layers kept) with an RGBA overlay on the top layer: needs 3 layers, so
        the ground is flattened into one bottom layer first (composite), and the overlay becomes the top layer."""
        m = overlay_rgba[..., 3] > 0
        top = np.zeros((16, 16), np.uint8)
        idx_top = self.index(overlay_rgba[..., :3], bank); top[m] = idx_top[m]
        ents = PRIM.blocks[0][ground_mid]
        if not any(ents[4:8]):                                    # single-layer ground (lawn, dirt kit): keep its own primary tiles
            bottom = list(ents[:4])
        else:
            base = np.asarray(PRIM.render(ground_mid)).astype(np.uint8).copy()
            idx_bot = self.index(base, bank)
            bottom = [self.tile(idx_bot[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8], bank) for q in range(4)]
        over = [self.tile(top[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8], bank) if top[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8].any() else 0 for q in range(4)]
        return self.raw(bottom + over, attr)
    def reserve(self, mid, ents, attr):
        """Pin a metatile at a fixed id (seam cells are drawn by the neighbouring town with ITS tileset, so the ids
        and the look must agree on both sides)."""
        assert mid not in self.reserved or self.reserved[mid] == (list(ents), attr), f'reserved id {mid:#x} defined twice'
        self.reserved[mid] = (list(ents), attr)
    def raw(self, ents, attr):
        key = (tuple(ents), attr)
        if key not in self.mt_lookup:
            mid = 512 + len(self.metatiles)
            while mid in self.reserved: self.metatiles.append(None); self.attrs.append(0); mid += 1
            self.mt_lookup[key] = mid; self.metatiles.append(list(ents)); self.attrs.append(attr)
        return self.mt_lookup[key]
    def table(self):
        n = max([512 + len(self.metatiles)] + [m + 1 for m in self.reserved]) - 512
        mts = [(self.metatiles[i] if i < len(self.metatiles) else None) for i in range(n)]; ats = [(self.attrs[i] if i < len(self.attrs) else 0) for i in range(n)]
        for mid, (ents, attr) in self.reserved.items(): mts[mid - 512] = ents; ats[mid - 512] = attr
        return [m or [0] * 8 for m in mts], ats
    def write(self, folder):
        folder.mkdir(parents=True, exist_ok=True); (folder / 'palettes').mkdir(exist_ok=True)
        n = len(self.tiles); rows = max(1, (n + 15) // 16); sheet = np.zeros((rows * 8, 128), np.uint8)
        for i, t in enumerate(self.tiles): sheet[(i // 16) * 8:(i // 16) * 8 + 8, (i % 16) * 8:(i % 16) * 8 + 8] = t
        im = Image.fromarray(sheet, 'P'); im.putpalette([v for i in range(16) for v in (i * 17, i * 17, i * 17)] + [0] * 720); im.save(folder / 'tiles.png', bits=4)
        for b in range(16):
            colors = self.pal.get(b, [])
            (folder / 'palettes' / f'{b:02}.pal').write_text('\r\n'.join(['JASC-PAL', '0100', '16', '0 0 0'] + [f'{r} {g} {bb}' for r, g, bb in colors] + ['0 0 0'] * (15 - len(colors))) + '\r\n')
        mts, ats = self.table()
        (folder / 'metatiles.bin').write_bytes(b''.join(struct.pack('<8H', *m) for m in mts))
        (folder / 'metatile_attributes.bin').write_bytes(struct.pack('<%dH' % len(ats), *ats))

# ----------------------------------------------------------------------------- 4. assemble
def main():
    typ, col, events, ref = decode_hgss()
    mat, trav, notes = layers(typ, col, events)
    deco = decorations(mat)
    trees, adapt, open_after = place_trees(mat, trav)
    base = subprocess.check_output(['git', '-C', str(GAME), 'show', f'{BASE_REV}:data/layouts/{MAP}/map.bin'])
    cur = np.array(struct.unpack('<%dH' % (len(base) // 2), base)).reshape(48, W)
    old = Tileset(GAME, 'claude_route29', 'cherrygrove')
    town = Tileset(GAME, 'cherrygrove', 'cherrygrove')

    # --- sliced route vocabulary over the accepted lawn and dirt
    sl = ra.tall_slices(); tall = {(n, s, w, e): ra.tall_cell(sl, n, s, w, e) for n in (0, 1) for s in (0, 1) for w in (0, 1) for e in (0, 1)}
    ledges = ra.ledges(); flowers = ra.orange_flowers(); apricorn = ra.apricorn()
    light = ra.cells(29, 22, 12); light = np.dstack([light[..., :3], np.full((16, 16), 255, np.uint8)])
    sign = ra.clear(ra.cells(29, 87, 14), ra.GRASS29 + ra.PATH, 10)
    gate = ra.cutout(ra.cells(29, 48, 0, 8, 10, dx=7), ra.GRASS29 + ra.PATH + ra.TREE + [(48, 128, 104), (56, 144, 112)], tol=14)   # render cells x48-55, y0-9; dx puts the building's left edge on HGSS column 48 (footprint 48-53)
    # gate registration: the steps row is the lowest opaque row -> HGSS door row 5
    rows_opaque = [cy for cy in range(10) if gate[cy * 16:cy * 16 + 16][..., 3].any()]
    gate_bottom = rows_opaque[-1]; gate_rows = {cy: 5 - (gate_bottom - cy) for cy in rows_opaque}       # render row -> HGSS row

    pk = Packer()
    def phase(hx, hz): return LAWN[((hx + COL0) % 2, (hz + ROW0) % 2)]
    DIRT = learn_path_kit()
    comps = {}
    for key, ov in tall.items():
        for ph in LAWN.values(): comps[('G', key, ph)] = (ov, ph, 6)
    # ground under ledges and walls: the dirt kit where the path meets them (the sand runs up to the wall, as in HGSS)
    def ledge_ground(hx, hz):
        nb = [(0 <= hz + dz < HH and 0 <= hx + dx < HW and mat[hz + dz, hx + dx]) for dx, dz in ((0, -1), (0, 1), (-1, 0), (1, 0))]
        if not any(n == 'P' for n in nb): return phase(hx, hz)
        return DIRT(tuple(bool(n) and n in 'P_|!c' for n in nb), hx + COL0)
    grounds = {ledge_ground(hx, hz) for hz in range(HH) for hx in range(HW) if mat[hz, hx] in '_|!c'} | set(LAWN.values())
    for name, ov in ledges.items():
        for g in grounds: comps[('ledge', name, g)] = (ov, g, 7)
    for ph in LAWN.values():
        comps[('f', ph)] = (flowers, ph, 7); comps[('s', ph)] = (sign, ph, 9)
        comps[('A', 'crown', ph)] = (apricorn[16:32, 16:32], ph, 9); comps[('A', 'trunk', ph)] = (apricorn[32:48, 16:32], ph, 9)   # 1 wide x 2 tall; the 43 px spilling into the next column are dropped
    for cy in rows_opaque:
        for cx in range(8):
            ov = gate[cy * 16:cy * 16 + 16, cx * 16:cx * 16 + 16]
            if ov[..., 3].any(): comps[('g', cx, cy)] = (ov, LAWN[((47 + cx + COL0) % 2, (gate_rows[cy] + ROW0) % 2)], 8)
    comps[('L',)] = (light, None, 12)
    # bank 12: flattened tree rows (lawn + tree colours) under overlapping crown tops, plus the light lawn
    for kind, rows in TREE_ROWS.items():
        if kind != 'tree': continue
        for i in (0, 1, 2):
            for pair in rows[i]:
                for mid in pair: pk.pixels[12].append(np.asarray(PRIM.render(mid)).astype(np.uint8))
    for k, (ov, ph, bank) in comps.items():
        rgb = ov[..., :3][ov[..., 3] > 0] if ph is not None else ov[..., :3].reshape(-1, 3)
        pk.pixels[bank].append(rgb.reshape(-1, 1, 3));
        if ph is not None: pk.pixels[bank].append(np.asarray(PRIM.render(ph)).astype(np.uint8))
    blossom_pal = read_pal(GAME / 'data/tilesets/secondary/cherrygrove/palettes/10.pal')[1:]
    # carried-over secondary tiles from the accepted map (seam lawn, ridge, lookout) keep their own banks
    pk.finish({10: blossom_pal})
    # Seam rule: cells within about eight columns of a map connection are drawn by the neighbouring map with ITS
    # tilesets, and the neighbour's cells are drawn here with THIS tileset. So every secondary metatile id used in
    # those windows keeps its id and its look: the accepted route's own cells (carried verbatim), New Bark's first
    # eight columns and Cherrygrove's last eight. Secondary palette banks 10 (town = New Bark) and 11 (New Bark =
    # accepted route) are therefore fixed; the rest are free for the route's own art.
    carry = {}
    def rehome(e, src):
        tid = e & 1023
        if tid < 512: return e
        bank = e >> 12
        if bank >= 6:
            if bank in pk.pal: assert pk.pal[bank] == src.pals[1][bank][1:], f'palette bank {bank} needed by two different seam palettes'
            else: pk.pal[bank] = src.pals[1][bank][1:]
        idx = (np.array(src.tiles[1][tid - 512], dtype=np.uint8) % 16).reshape(8, 8)
        if e & 2048: idx = idx[::-1]
        if e & 1024: idx = idx[:, ::-1]
        return pk.tile(idx, bank)
    def pin(mid, src):
        if mid < 512 or mid in pk.reserved: return
        pk.reserve(mid, [rehome(e, src) for e in src.blocks[1][mid - 512]], src.attrs[1][mid - 512])
    keep = {int(v) & 1023 for v in cur[RIDGE_SRC:, :].ravel()} | {int(v) & 1023 for v in cur[:, :10].ravel()} | {int(v) & 1023 for v in cur[:, 88:].ravel()}
    for mid in sorted(keep): pin(mid, old); carry[mid] = mid
    newbark = Tileset(GAME, 'new_bark', 'cherrygrove')
    nbgrid = np.frombuffer((GAME / 'data/layouts/NewBarkTown/map.bin').read_bytes(), dtype='<u2').reshape(-1, 36) & 1023
    towngrid = np.frombuffer((GAME / 'data/layouts/CherrygroveCity/map.bin').read_bytes(), dtype='<u2').reshape(-1, 80) & 1023
    seam_pins = dict(new_bark=sorted({int(v) for v in nbgrid[:, :8].ravel() if v >= 512}), cherrygrove=sorted({int(v) for v in towngrid[:, 72:].ravel() if v >= 512}))
    for mid in seam_pins['new_bark']: pin(mid, newbark)
    for mid in seam_pins['cherrygrove']: pin(mid, town)
    def attr(beh, layer=COVERED): return layer | MB[beh]
    mt = {}
    for k, (ov, ph, bank) in comps.items():
        beh = {'G': 'MB_TALL_GRASS', 'ledge': None, 'f': 'MB_NORMAL', 's': 'MB_NORMAL', 'g': 'MB_NORMAL', 'A': 'MB_NORMAL', 'L': 'MB_NORMAL', 'x': 'MB_NORMAL'}[k[0]]
        if beh is None: beh = 'MB_JUMP_SOUTH' if k[1].startswith('ledge') else 'MB_NORMAL'
        if ph is None: mt[k] = pk.metatile(ov[..., :3].copy(), bank, attr(beh)); continue
        top_layer = (k[0] == 'g' and gate_rows[k[2]] < 0) or (k[0] == 'A' and k[1] == 'crown') or (k[0] == 'x' and k[2] == 0)   # roof above the footprint and crowns draw over the player
        mt[k] = pk.layered(ph, ov, bank, attr(beh, NORMAL if top_layer else COVERED))
    # tree rows by lawn phase: match each variant's lawn tiles (palette bank 0) to the lawn metatiles
    def lawn_ids(mid): return {e & 1023 for e in PRIM.blocks[0][mid][:4] if (e >> 12) == 0}
    lawn_phase_ids = {key: lawn_ids(mid) for key, mid in LAWN.items()}
    row_tiles = {}                                                   # (kind, i, (px, py)) -> metatile id, exact phase where a variant exists
    for kind, rows in TREE_ROWS.items():
        for i, variants in enumerate(rows):
            for pair in variants:
                for j, mid in enumerate(pair):
                    key = max(lawn_phase_ids, key=lambda k: len(lawn_ids(mid) & lawn_phase_ids[k]))
                    row_tiles[(kind, i, j, key)] = mid
    phase_misses = Counter()
    def tree_tile(kind, i, j, x, y):
        key = (x % 2, y % 2)
        if (kind, i, j, key) in row_tiles: return row_tiles[(kind, i, j, key)]
        phase_misses[kind] += 1
        alt = [k for k in row_tiles if k[:3] == (kind, i, j)]
        same_y = [k for k in alt if k[3][1] == key[1]]
        return row_tiles[(same_y or alt)[0]]
    composites = {}
    def layer_rgba(mid):
        """The foreground of a primary metatile: its middle-layer tiles plus any tree-bank tile on its bottom layer."""
        ents = PRIM.blocks[0][mid]; out = np.zeros((16, 16, 4), np.uint8)
        for q in range(4):
            e = ents[4 + q] if ents[4 + q] else (ents[q] if (ents[q] >> 12) != 0 else 0)
            if not e: continue
            tid, bank = e & 1023, e >> 12; t = np.array(PRIM.tiles[0][tid], dtype=np.uint8).reshape(8, 8) % 16
            if e & 2048: t = t[::-1]
            if e & 1024: t = t[:, ::-1]
            pal = PRIM.pals[0][bank]
            for v in range(1, 16):
                m = t == v
                if m.any():
                    sub = out[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]; sub[m] = (*pal[v], 255)
        return out
    def composite(stack):
        """Trees stacked on one cell, back to front: everything but the front tree is flattened into one bank-12
        bottom layer; the front tree's own foliage/trunk tiles stay on the middle layer."""
        key = tuple(stack)
        if key not in composites:
            base = np.asarray(PRIM.render(stack[0])).astype(np.uint8).copy()
            for mid in stack[1:-1]:
                ov = layer_rgba(mid); m = ov[..., 3] > 0; base[m] = ov[..., :3][m]
            idx = pk.index(base, 12)
            bottom = [pk.tile(idx[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8], 12) for q in range(4)]
            ents = PRIM.blocks[0][stack[-1]]
            middle = [ents[4 + q] if ents[4 + q] else (ents[q] if (ents[q] >> 12) != 0 else 0) for q in range(4)]
            composites[key] = pk.raw(bottom + middle, COVERED | MB['MB_NORMAL'])
        return composites[key]
    # blossom metatiles (0x030/0x031/0x03F/0x040) are primary art whose tiles use palette bank 10, so they work here
    # because bank 10 is fixed to the town's bank 10 above; nothing to carry.

    # --- the map
    grid = np.zeros((H, W), np.uint16)
    def put(x, y, mid, blocked, elev=3): grid[y, x] = (mid & 1023) | ((3 if blocked else 0) << 10) | (elev << 12)
    # adapters and ridge, carried verbatim
    for y in range(48):
        for x in list(range(0, 10)) + list(range(88, 98)):
            yy = y if y < RIDGE_SRC else y + (RIDGE_DST - RIDGE_SRC)
            v = int(cur[y, x]); grid[yy, x] = (carry.get(v & 1023, v & 1023) & 1023) | (v & 0xFC00)
        for x in range(10, 88):
            if y >= RIDGE_SRC:
                v = int(cur[y, x]); grid[y + (RIDGE_DST - RIDGE_SRC), x] = (carry.get(v & 1023, v & 1023) & 1023) | (v & 0xFC00)
    for y in range(RIDGE_SRC, RIDGE_DST):           # adapter rows between the HGSS region bottom and the moved ridge
        for x in range(0, 10): put(x, y, FOREST_BAND[y % 6][x % 2], True)
        for x in range(88, 98): put(x, y, FOREST_BAND[y % 6][x % 2], True)
    # trees (map coordinates): every cell lists the trees covering it, back to front
    cellmap = defaultdict(list)
    for (tx, ty) in trees:
        for i in range(TH):
            for j in range(TW): cellmap[(tx + j, ty + i)].append((tx, ty, i, j))
    for v in cellmap.values(): v.sort(key=lambda t: (t[1], t[0]))        # back to front: higher trees first, then left before right
    overlapping = {t[:2] for v in cellmap.values() if len(v) > 1 for t in v}
    rng = np.random.default_rng(29); blossoms = []
    behind = {t[:2] for v in cellmap.values() for t in v[:-1]}            # trees drawn behind another on some cell (their flattened rows need the tree palette)
    for (tx, ty) in trees:                                                # front trees near Cherrygrove become blossom trees (design bible: fading from the town)
        if (tx, ty) in behind: continue
        if 10 <= tx < BLOSSOM_MAX_X and rng.random() < 0.6 * (1 - (tx - 10) / (BLOSSOM_MAX_X - 10)): blossoms.append((tx, ty))
    blossoms = set(blossoms)
    def kind_of(t): return 'blossom' if t[:2] in blossoms else 'tree'
    for (x, y), ts in cellmap.items():
        back, front = ts[0], ts[-1]
        if len(ts) == 1 or front[2] == 1:                                 # single tree, or an opaque crown middle in front
            t = front; put(x, y, tree_tile(kind_of(t), t[2], t[3], x, y), True)
        else:                                                             # crown top or trunk row in front of the tree(s) behind
            put(x, y, composite([tree_tile(kind_of(t), t[2], t[3], x, y) for t in ts]), True)
    leftover_cells = {tuple(a['cell']) for a in adapt if 'left without' in a['change']}
    absorbed = {tuple(a['cell']) for a in adapt if 'absorbed' in a['change']}
    # HGSS region
    for hz in range(HH):
        for hx in range(HW):
            x, y = hx + COL0, hz + ROW0
            if x not in REGION_COLS or y >= RIDGE_DST: continue
            m = mat[hz, hx]; ph = phase(hx, hz); blocked = trav[hz, hx] == 'X'
            if (x, y) in cellmap: continue
            if (x, y) in leftover_cells: put(x, y, ph, True); continue
            if m == '.':
                d = deco.get((hx, hz))
                if d == 'f': put(x, y, mt[('f', ph)], False)
                elif d == 'L': put(x, y, mt[('L',)], False)
                else: put(x, y, ph, False)
            elif m == 'P':
                mask = tuple(0 <= hz + dz < HH and 0 <= hx + dx < HW and mat[hz + dz, hx + dx] == 'P' for dx, dz in ((0, -1), (0, 1), (-1, 0), (1, 0)))
                put(x, y, DIRT(mask, x), False)
            elif m == 'G':
                nb = tuple(int(0 <= hz + dz < HH and 0 <= hx + dx < HW and mat[hz + dz, hx + dx] == 'G') for dx, dz in ((0, -1), (0, 1), (-1, 0), (1, 0)))
                put(x, y, mt[('G', nb, ph)], False)
            elif m == '_': put(x, y, mt[('ledge', 'ledge_a' if hx % 2 else 'ledge_b', ledge_ground(hx, hz))], True)      # native convention: ledge cells are impassable in the layout, the jump overrides it (Route 101)
            elif m in '!|': put(x, y, mt[('ledge', 'wall', ledge_ground(hx, hz))], True)   # both HGSS wall types (0x38/0x39) draw the same bar in the render
            elif m == 'c':
                up = hz > 0 and mat[hz - 1, hx] in '|!'; right = hx + 1 < HW and mat[hz, hx + 1] == '_'; left = hx > 0 and mat[hz, hx - 1] == '_'
                name = 'corner_se' if (up and right) else 'corner_sw' if (up and left) else 'corner_ne' if (not up and (right or left)) else 'wall_top'
                put(x, y, mt[('ledge', name, ledge_ground(hx, hz))], True)
            elif m == 's': put(x, y, mt[('s', ph)], True)
            elif m == 'A': put(x, y, mt[('A', 'trunk', ph)], True)
            elif m == 'x': put(x, y, ph, False)                      # HGSS cuttable tree = object sprite; placed as the native cuttable-tree object event below
            elif m == 'g' or m == 'D':
                put(x, y, ph, True)                                   # filled below from the gate art
            elif m == 'T': put(x, y, ph, True)                        # should not happen: every forest cell is a tree, leftover or absorbed
            else: put(x, y, ph, blocked)
    # gate art placed by its registered rows; the two door cells stay walkable up to the door (blocked: interior not built)
    for cy in rows_opaque:
        hz = gate_rows[cy]
        for cx in range(8):
            k = ('g', cx, cy)
            if k not in mt: continue
            hx = 47 + cx; x, y = hx + COL0, hz + ROW0
            if x in REGION_COLS and 0 <= y < RIDGE_DST: put(x, y, mt[k], True)
    # overlay rows for the Apricorn tree and the cuttable trees: the crown above the object cell draws over the player
    for o in events['objects']:
        hx, hz = o['hx'], o['hz']
        if o['id'] == 'obj_R29_bonguri' and hz > 0 and mat[hz - 1, hx] == '.':
            put(hx + COL0, hz - 1 + ROW0, mt[('A', 'crown', phase(hx, hz - 1))], False)       # crown over the walkable cell above, as in HGSS
    # map edge columns of the region are inside adapters; nothing else to fill

    # --- write engine files
    ts = GAME / 'data/tilesets/secondary' / TS_NAME; pk.write(ts)
    (GAME / f'data/layouts/{MAP}/map.bin').write_bytes(struct.pack('<%dH' % (W * H), *grid.ravel().tolist()))
    lj = GAME / 'data/layouts/layouts.json'; L = json.loads(lj.read_text())
    for l in L['layouts']:
        if l['id'] == LAYOUT: l['secondary_tileset'] = 'gTileset_' + TS_SYM; l['height'] = H
    lj.write_text(json.dumps(L, indent=2) + '\n')
    mj = GAME / f'data/maps/{MAP}/map.json'; M = json.loads(mj.read_text()); moves = []
    for b in M['bg_events']:
        if b.get('type') == 'hidden_item' and b['y'] == 27:
            moves.append(dict(event='hidden Potion', old=[b['x'], b['y']], new=[b['x'], b['y'] + (RIDGE_DST - RIDGE_SRC)])); b['y'] += RIDGE_DST - RIDGE_SRC
    cut_trees = [(o['hx'] + COL0, o['hz'] + ROW0) for o in events['objects'] if o['spriteId'] == 'SPRITE_TREE']
    M['object_events'] = [o for o in M['object_events'] if o.get('graphics_id') != 'OBJ_EVENT_GFX_CUTTABLE_TREE']
    for n, (x, y) in enumerate(cut_trees):                            # the native cuttable tree (Emerald object + EventScript_CutTree) on the HGSS tree cells
        M['object_events'].append(dict(graphics_id='OBJ_EVENT_GFX_CUTTABLE_TREE', x=x, y=y, elevation=3, movement_type='MOVEMENT_TYPE_LOOK_AROUND', movement_range_x=0, movement_range_y=0,
                                       trainer_type='TRAINER_TYPE_NONE', trainer_sight_or_berry_tree_id='0', script='EventScript_CutTree', flag=f'FLAG_TEMP_{11 + n}'))
    if not any(b.get('script') == f'{MAP}_WestSign' for b in M['bg_events']):
        M['bg_events'].append(dict(type='sign', x=9 + COL0, y=13 + ROW0, elevation=0, player_facing_dir='BG_EVENT_PLAYER_FACING_ANY', script=f'{MAP}_EastSign'))
        moves.append(dict(event='west sign (HGSS 5,13)', old=[5 + COL0, 13 + ROW0], new=[9 + COL0, 13 + ROW0], note='HGSS cell is inside the carried Cherrygrove adapter; placed on the first HGSS lawn cell east of it, reusing the route sign script'))
    mj.write_text(json.dumps(M, indent=2) + '\n')
    register()

    # --- source and evidence
    OUT.mkdir(parents=True, exist_ok=True); (OUT / 'source').mkdir(exist_ok=True); (OUT / 'evidence').mkdir(exist_ok=True)
    (OUT / 'source/reference.json').write_text(json.dumps(ref, indent=2) + '\n')
    (OUT / 'source/hgss-terrain-types.txt').write_text('\n'.join(' '.join(f'{int(v):02x}' for v in row) for row in typ) + '\n')
    (OUT / 'source/hgss-collision.txt').write_text('\n'.join(' '.join(f'{int(v):02x}' for v in row) for row in col) + '\n')
    (OUT / 'source/material-grid.txt').write_text('\n'.join(''.join(row) for row in mat) + '\n')
    (OUT / 'source/traversal-grid.txt').write_text('\n'.join(''.join(row) for row in trav) + '\n')
    (OUT / 'source/hgss-events.json').write_text(json.dumps(events, indent=2) + '\n')
    with (OUT / 'source/traversal-ledger.csv').open('w', newline='') as f:
        w = csv.writer(f); w.writerow(['hgss_x', 'hgss_z', 'map_x', 'map_y', 'terrain_type', 'collision_byte', 'material', 'traversal', 'in_region'])
        for hz in range(HH):
            for hx in range(HW): w.writerow([hx, hz, hx + COL0, hz + ROW0, f'{int(typ[hz, hx]):#04x}', f'{int(col[hz, hx]):#04x}', mat[hz, hx], trav[hz, hx], int(hx + COL0 in REGION_COLS and hz + ROW0 < RIDGE_DST)])
    adaptations = dict(
        carried_from_accepted_layout=dict(base=BASE_REV, west_adapter_cols=[0, 9], east_adapter_cols=[88, 97], ridge_rows_old=[RIDGE_SRC, 47], ridge_rows_new=[RIDGE_DST, RIDGE_DST + 18],
                                           hgss_cells_overridden='HGSS columns 0-8 and 87-95 (town seam windows); the accepted sea ridge is appended below the HGSS region'),
        tree_overlaps=sorted(overlapping), lawn_phase_misses=dict(phase_misses),
        seam_pinned_metatiles=dict(accepted_route=sorted(f'{m:#x}' for m in keep if m >= 512), **{k: [f'{m:#x}' for m in v] for k, v in seam_pins.items()}),
        decorations_from_render={f'{x},{z}': d for (x, z), d in sorted(deco.items())},
        tree_fitting=adapt, trees=len(trees), blossoms=sorted(blossoms), event_moves=moves,
        notes=[dict(cell=[x, z], note=n) for x, z, n in notes],
        cuttable_trees=cut_trees,
        unwired=['Route 46 gatehouse door cells (50,5) and (51,5): interior map not built, door kept blocked', 'original NPCs, Apricorn harvesting and the HGSS item ball Potion at (78,2) are campaign work and are not placed'])
    (OUT / 'source/adaptations.json').write_text(json.dumps(adaptations, indent=2) + '\n')
    full = Tileset(GAME, TS_NAME, 'cherrygrove')
    full.map_image(grid.ravel().tolist(), W).save(OUT / 'evidence/native-map.png'); full.sheet(OUT / 'evidence/tileset-sheet.png')
    report = dict(tiles=len(pk.tiles), metatiles=len(pk.table()[0]), banks={b: len(c) for b, c in pk.pal.items()}, trees=len(trees), blossoms=len(blossoms),
                  leftover_forest_cells=len(leftover_cells), absorbed_lawn_cells=len(absorbed), materials={k: int(v) for k, v in Counter(mat.ravel()).items()},
                  map_size=[W, H], layout_sha256=hashlib.sha256((GAME / f'data/layouts/{MAP}/map.bin').read_bytes()).hexdigest())
    (OUT / 'evidence/build-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))

def learn_path_kit():
    data = (GAME / 'data/layouts/CherrygroveCity/map.bin').read_bytes()
    g = np.array(struct.unpack('<%dH' % (len(data) // 2), data)).reshape(-1, 80) & 1023
    sand = set()
    for mid in np.unique(g):
        im = np.asarray(PRIM.render(int(mid))).astype(int)
        if ((im[..., 0] > 190) & (im[..., 1] > 170) & (im[..., 2] < 170) & (im[..., 2] > 90)).mean() > 0.9: sand.add(int(mid))
    kit = defaultdict(Counter); h, w = g.shape
    for y in range(h):
        for x in range(w):
            if int(g[y, x]) not in sand: continue
            mask = tuple(int(g[y + dy, x + dx]) in sand if 0 <= y + dy < h and 0 <= x + dx < w else True for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)))
            kit[(mask, x % 2)][int(g[y, x])] += 1
    table = {k: c.most_common(1)[0][0] for k, c in kit.items()}
    def pick(mask, x): return table.get((mask, x % 2), table.get(((True, True, True, True), x % 2), 0x004))
    return pick

def register():
    h = GAME / 'src/data/tilesets/headers.h'; s = h.read_text()
    if TS_SYM not in s:
        s = s.replace('// End Claude routes\n', f'const struct Tileset gTileset_{TS_SYM} = {{ .isCompressed = TRUE, .isSecondary = TRUE, .tiles = gTilesetTiles_{TS_SYM}, .palettes = gTilesetPalettes_{TS_SYM}, .metatiles = gMetatiles_{TS_SYM}, .metatileAttributes = gMetatileAttributes_{TS_SYM}, .callback = NULL }};\n// End Claude routes\n', 1); h.write_text(s)
    g = GAME / 'src/data/tilesets/graphics.h'; s = g.read_text()
    if TS_SYM not in s:
        s = s.rstrip('\n') + f'\n\nconst u32 gTilesetTiles_{TS_SYM}[] = INCGFX_U32("data/tilesets/secondary/{TS_NAME}/tiles.png", ".4bpp.fastSmol");\nconst u16 gTilesetPalettes_{TS_SYM}[][16] = {{\n' + ''.join(f'INCGFX_U16("data/tilesets/secondary/{TS_NAME}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n'; g.write_text(s)
    m = GAME / 'src/data/tilesets/metatiles.h'; s = m.read_text()
    if TS_SYM not in s:
        s = s.rstrip('\n') + f'\nconst u16 gMetatiles_{TS_SYM}[] = INCBIN_U16("data/tilesets/secondary/{TS_NAME}/metatiles.bin");\nconst u16 gMetatileAttributes_{TS_SYM}[] = INCBIN_U16("data/tilesets/secondary/{TS_NAME}/metatile_attributes.bin");\n'; m.write_text(s)

if __name__ == '__main__':
    main()
