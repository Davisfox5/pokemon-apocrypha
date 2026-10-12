#!/usr/bin/env python3
"""Route 29 (Cherrygrove to New Bark) rebuilt from HGSS slices as a Porymap tileset.

What this does, in order:

1. Slices the route's vocabulary out of the 1:1 HGSS render
   (gba/art/claude-routes/references/route29-hgss.png): tall grass as a nine-slice,
   the one-way ledges and their walls, the Route 46 gate, the Apricorn tree, the
   orange flowers, the light lawn patch and the route sign. Each piece is cut on
   the render's own 16 px cell grid, so every piece is already Gen 3 metatile size.
2. Composites each piece over the town's lawn (the primary tileset's lawn
   metatiles, so the route reads as the same world as Cherrygrove), splits the
   result into 8x8 tiles, dedupes them with flips, and packs them into a new
   secondary tileset `apoc_route29` with its own palette banks (6-9), plus the
   town's blossom palette in bank 10 for the west-end blossom trees.
3. Lays the map out from the HGSS cell plan (gba/art/claude-routes/route29-plan.npy,
   read off the same render): forest from the town's lattice-tree metatiles, lawn
   and sand path from the primary's own kit, and the sliced pieces where HGSS has
   them. The Cherrygrove seam (columns 0-9) and the sea ridge with the lookout
   (rows 29-47) are carried over verbatim from the accepted layout so nothing the
   owner has reviewed moves.
4. Apocrypha changes on top of HGSS: blossom trees at the west end where Gold's
   grove spills onto the route (design bible, Chapter 1 world design), fading out
   by the first ledge.

Outputs into an engine checkout (argument 1): the tileset, the layout blockdata,
layouts.json, and the three tileset registration headers. Run from the hub root:

    python3 tools/gba/maps/apoc_route29/build.py /path/to/apocrypha-src

Original designs and art: Game Freak / Nintendo / Creatures (read-only derivation).
"""
from __future__ import annotations
import json, re, struct, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from claude_routes import art as ra          # HGSS render slicing helpers
from tiles import Tileset, palette as read_pal

ROOT = HERE.parents[3]
GAME = Path(sys.argv[1]).resolve()
OUT_ART = ROOT / 'gba/art/apoc-route29'
TS_NAME, TS_SYM = 'apoc_route29', 'ApocRoute29'
MAP, LAYOUT = 'CherrygroveRoute29Approach', 'LAYOUT_CHERRYGROVE_ROUTE29_APPROACH'
W, H = 98, 48
PLAN = np.load(ROOT / 'gba/art/claude-routes/route29-plan.npy')   # 34 x 98, HGSS cells
ROW0 = 2                       # plan row r sits at map row r + ROW0
KEEP_COLS = 10                 # Cherrygrove seam window, carried over verbatim
KEEP_ROW = 29                  # lookout row, cliff, beach and sea, carried over verbatim
BLOSSOM_MAX_X = 26             # blossom handoff fades out before the first ledge
BASE_REV = '2722eaf7601ec02dc5a684fa8cdef9206c0dc377'   # apocrypha branch commit the seam and ridge are carried from

# ----------------------------------------------------------------------------- engine constants
def mb():
    text = (GAME / 'include/constants/metatile_behaviors.h').read_text()
    names = re.findall(r'^\s+(MB_[A-Z0-9_]+),', text, re.M)
    return {n: i for i, n in enumerate(names)}
MB = mb()
COVERED = 1 << 12                 # layer type: bottom + middle
NORMAL = 0                        # middle + top

# ----------------------------------------------------------------------------- primary kit (town art)
PRIM = Tileset(GAME, 'cherrygrove', 'cherrygrove')
LAWN = {(0, 0): 0x028, (1, 0): 0x027, (0, 1): 0x034, (1, 1): 0x033}      # (x%2, y%2) -> plain route lawn
FOREST_BAND = [(0x00B, 0x00C), (0x017, 0x018), (0x00A, 0x007), (0x00E, 0x014), (0x020, 0x01D), (0x042, 0x043)]
BLOSSOM = [(0x230, 0x231), (0x030, 0x031), (0x03F, 0x040)]               # the town's blossom tree, replaces band rows 0-2

def lawn_id(x, y):
    return LAWN[(x % 2, y % 2)]

def learn_path_kit():
    """Which path metatile the town uses for each 4-neighbour mask and column parity."""
    data = (GAME / 'data/layouts/CherrygroveCity/map.bin').read_bytes()
    g = np.array(struct.unpack('<%dH' % (len(data) // 2), data)).reshape(-1, 80) & 1023
    sand = set()
    for mid in np.unique(g):
        im = np.asarray(PRIM.render(int(mid))).astype(int)
        frac = ((im[..., 0] > 190) & (im[..., 1] > 170) & (im[..., 2] < 170) & (im[..., 2] > 90)).mean()
        if frac > 0.9: sand.add(int(mid))
    kit = defaultdict(Counter)
    h, w = g.shape
    for y in range(h):
        for x in range(w):
            if int(g[y, x]) not in sand: continue
            mask = tuple(int(g[y + dy, x + dx]) in sand if 0 <= y + dy < h and 0 <= x + dx < w else True
                         for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)))
            kit[(mask, x % 2)][int(g[y, x])] += 1
    return {k: c.most_common(1)[0][0] for k, c in kit.items()}, sand
PATH_KIT, SAND_IDS = learn_path_kit()

def path_id(mask, x):
    if (mask, x % 2) in PATH_KIT: return PATH_KIT[(mask, x % 2)]
    full = (True, True, True, True)
    return PATH_KIT.get((full, x % 2), 0x004)

# ----------------------------------------------------------------------------- the HGSS slices
def composite(overlay, lawn):
    """Opaque 16x16 RGB: the primary lawn metatile with an RGBA slice on top."""
    base = np.asarray(PRIM.render(lawn)).astype(np.uint8).copy()
    m = overlay[..., 3] > 0
    base[m] = overlay[m][:, :3]
    return base

def slices():
    sl = ra.tall_slices()
    tall = {(n, s, w, e): ra.tall_cell(sl, n, s, w, e) for n in (0, 1) for s in (0, 1) for w in (0, 1) for e in (0, 1)}
    ledges = ra.ledges()
    gate = ra.gate()                                   # 144 x 144 at plan cells (48..56, 1..9)
    apricorn = ra.apricorn()                           # 48 x 48 at plan cells (20..22, 9..11)
    flowers = ra.orange_flowers()
    light = ra.cells(29, 22, 12)                       # the upper lawn patch, one canonical cell
    light = np.dstack([light[..., :3], np.full((16, 16), 255, np.uint8)])
    sign = ra.clear(ra.cells(29, 87, 14), ra.GRASS29 + ra.PATH, 10)
    return tall, ledges, gate, apricorn, flowers, light, sign

# ----------------------------------------------------------------------------- tile packer
class Packer:
    """8x8 tiles for one secondary tileset: per-bank palettes, flip dedupe, 512 cap."""
    def __init__(self):
        self.pal = {}                 # bank -> list of up to 15 RGB
        self.pixels = defaultdict(list)   # bank -> list of 16x16 RGB arrays queued for quantisation
        self.tiles = []               # list of 8x8 uint8 index arrays (secondary ids from 512)
        self.lookup = {}              # bytes -> (tile index, hflip, vflip)
        self.metatiles = []           # list of 8 u16 entries
        self.attrs = []
        self.mt_lookup = {}

    def bank_colors(self, bank, fixed=()):
        px = np.concatenate([a.reshape(-1, 3) for a in self.pixels[bank]])
        u, n = np.unique(px, axis=0, return_counts=True)
        colors = [tuple(int(v) for v in c) for c in u]
        fixed = [c for c in fixed if c in colors]
        if len(colors) <= 15:
            return colors
        rest = [c for c in colors if c not in fixed]
        budget = 15 - len(fixed)
        pop = np.repeat(u, n, axis=0).reshape(1, -1, 3).astype(np.uint8)
        q = Image.fromarray(pop).quantize(colors=budget, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        qp = np.array(q.getpalette()[:budget * 3]).reshape(-1, 3)
        arr = np.array(rest, dtype=np.int32); out = list(fixed)
        for c in qp:
            s = rest[int(((arr - c) ** 2).sum(1).argmin())]
            if s not in out: out.append(s)
        return out[:15]

    def finish_palettes(self, fixed_banks):
        for bank in list(self.pixels):
            if bank in fixed_banks: self.pal[bank] = fixed_banks[bank]
            else: self.pal[bank] = self.bank_colors(bank)

    def index(self, rgb, bank):
        arr = np.array(self.pal[bank], dtype=np.int32)
        flat = rgb.reshape(-1, 3).astype(np.int32)
        return (((flat[:, None, :] - arr[None]) ** 2).sum(-1).argmin(1) + 1).reshape(rgb.shape[:2]).astype(np.uint8)

    def tile(self, idx8, bank):
        for hf in (0, 1):
            for vf in (0, 1):
                a = idx8[::-1] if vf else idx8
                a = a[:, ::-1] if hf else a
                key = a.tobytes()
                if key in self.lookup:
                    t = self.lookup[key]
                    return (512 + t) | (hf << 10) | (vf << 11) | (bank << 12)
        t = len(self.tiles); self.tiles.append(idx8.copy()); self.lookup[idx8.tobytes()] = t
        return (512 + t) | (bank << 12)

    def metatile(self, rgb16, bank, attr):
        """An opaque 16x16 RGB cell as one bottom-layer metatile (top layer empty)."""
        idx = self.index(rgb16, bank)
        entries = [self.tile(idx[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8], bank) for q in range(4)] + [0, 0, 0, 0]
        return self.raw_metatile(entries, attr)

    def raw_metatile(self, entries, attr):
        key = (tuple(entries), attr)
        if key not in self.mt_lookup:
            self.mt_lookup[key] = 512 + len(self.metatiles)
            self.metatiles.append(list(entries)); self.attrs.append(attr)
        return self.mt_lookup[key]

    def write(self, folder, pal16):
        folder.mkdir(parents=True, exist_ok=True); (folder / 'palettes').mkdir(exist_ok=True)
        n = len(self.tiles); rows = max(1, (n + 15) // 16)
        sheet = np.zeros((rows * 8, 128), np.uint8)
        for i, t in enumerate(self.tiles): sheet[(i // 16) * 8:(i // 16) * 8 + 8, (i % 16) * 8:(i % 16) * 8 + 8] = t
        im = Image.fromarray(sheet, 'P')
        grey = [v for i in range(16) for v in (i * 17, i * 17, i * 17)]
        im.putpalette(grey + [0] * (768 - 48)); im.save(folder / 'tiles.png', bits=4)
        for b in range(16):
            colors = pal16.get(b) or self.pal.get(b) or []
            lines = ['JASC-PAL', '0100', '16', '0 0 0'] + [f'{r} {g} {bb}' for r, g, bb in colors] + ['0 0 0'] * (15 - len(colors))
            (folder / 'palettes' / f'{b:02}.pal').write_text('\r\n'.join(lines) + '\r\n')
        (folder / 'metatiles.bin').write_bytes(b''.join(struct.pack('<8H', *m) for m in self.metatiles))
        (folder / 'metatile_attributes.bin').write_bytes(struct.pack('<%dH' % len(self.attrs), *self.attrs))

# ----------------------------------------------------------------------------- build
def main():
    tall, ledges, gate, apricorn, flowers, light, sign = slices()
    old = Tileset(GAME, 'claude_route29', 'cherrygrove')
    import subprocess
    cur = subprocess.check_output(['git', '-C', str(GAME), 'show', f'{BASE_REV}:data/layouts/{MAP}/map.bin'])   # the accepted layout, not a rebuilt one
    cur = np.array(struct.unpack('<%dH' % (len(cur) // 2), cur)).reshape(H, W)
    town = Tileset(GAME, 'cherrygrove', 'cherrygrove')

    # 1. materials grid for the generated region
    mat = np.full((H, W), 'T', dtype='<U1')
    mat[ROW0:ROW0 + PLAN.shape[0], :] = PLAN
    mat[KEEP_ROW:, :] = 'X'
    mat[:, :KEEP_COLS] = 'X'
    # the gate footprint and the Apricorn tree are their own materials
    for cy in range(1, 10):
        for cx in range(48, 57): mat[cy + ROW0, cx] = 'g'
    for cy in range(9, 12):
        for cx in range(20, 23): mat[cy + ROW0, cx] = 'A'
    for cy in range(11, 14):
        for cx in range(20, 28): mat[cy + ROW0, cx] = 'L'
    mat[14 + ROW0, 87] = 's'
    # flowers: HGSS lawn cells where only a small orange/white cluster survives clearing the lawn
    for cy in range(PLAN.shape[0]):
        for cx in range(W):
            if mat[cy + ROW0, cx] != '.': continue
            a = ra.clear(ra.cells(29, cx, cy), ra.GRASS29 + ra.PATH, 10)
            k = int((a[..., 3] > 0).sum())
            if 8 <= k <= 90:
                px = a[a[..., 3] > 0][:, :3].astype(int)
                if ((px[:, 0] > 200) & (px[:, 1] < 170)).any(): mat[cy + ROW0, cx] = 'f'

    # 2. pack the sliced vocabulary; every piece is composited over the lawn of its cell phase
    pk = Packer()
    def phases(): return [(0, 0), (1, 0), (0, 1), (1, 1)]
    comps = {}
    for key, ov in tall.items():
        for ph in phases(): comps[('G', key, ph)] = (composite(ov, LAWN[ph]), 6)
    for name, ov in ledges.items():
        for ph in phases(): comps[('ledge', name, ph)] = (composite(ov, LAWN[ph]), 7)
    for ph in phases(): comps[('f', ph)] = (composite(flowers, LAWN[ph]), 7)
    for ph in phases(): comps[('s', ph)] = (composite(sign, LAWN[ph]), 9)
    for cy in range(9):
        for cx in range(9):
            ov = gate[cy * 16:cy * 16 + 16, cx * 16:cx * 16 + 16]
            if not ov[..., 3].any(): continue
            ph = ((48 + cx) % 2, (1 + cy + ROW0) % 2)
            comps[('g', cx, cy)] = (composite(ov, LAWN[ph]), 8)
    for cy in range(3):
        for cx in range(3):
            ov = apricorn[cy * 16:cy * 16 + 16, cx * 16:cx * 16 + 16]
            ph = ((20 + cx) % 2, (9 + cy + ROW0) % 2)
            comps[('A', cx, cy)] = (composite(ov, LAWN[ph]), 9)
    comps[('L',)] = (light[..., :3].copy(), 9)
    for k, (rgb, bank) in comps.items(): pk.pixels[bank].append(rgb)
    blossom_pal = read_pal(GAME / 'data/tilesets/secondary/cherrygrove/palettes/10.pal')[1:]
    pk.finish_palettes({10: blossom_pal})

    def attr(beh, layer=COVERED): return layer | MB[beh]
    mt = {}
    for k, (rgb, bank) in comps.items():
        beh = {'G': 'MB_TALL_GRASS', 'ledge': None, 'f': 'MB_NORMAL', 's': 'MB_NORMAL', 'g': 'MB_NORMAL', 'A': 'MB_NORMAL', 'L': 'MB_NORMAL'}[k[0]]
        if k[0] == 'ledge': beh = 'MB_JUMP_SOUTH' if k[1].startswith('ledge') else 'MB_NORMAL'
        layer = NORMAL if (k[0] == 'g' and k[2] <= 1) else COVERED      # gate roof ridge draws over the player
        mt[k] = pk.metatile(rgb, bank, attr(beh, layer))
    # carried-over metatiles (seam lawn, ridge) and the blossom crowns: primary tiles only, copied entries
    carry = {}
    free_banks = [11, 12]; bank_map = {}
    def carried_entry(e):
        """An old claude_route29 entry, re-homed: primary tiles as they are, secondary tiles copied into this pack."""
        tid = e & 1023
        if tid < 512: return e
        bank = e >> 12
        if bank not in bank_map:
            assert free_banks, 'carried tiles need more palette banks than are free'
            bank_map[bank] = free_banks.pop(0); pk.pal[bank_map[bank]] = old.pals[1][bank][1:]
        idx = (np.array(old.tiles[1][tid - 512], dtype=np.uint8) % 16).reshape(8, 8)
        if e & 2048: idx = idx[::-1]
        if e & 1024: idx = idx[:, ::-1]
        return pk.tile(idx, bank_map[bank])
    for mid in sorted({int(v) & 1023 for v in cur[KEEP_ROW:, :].ravel()} | {int(v) & 1023 for v in cur[:, :KEEP_COLS].ravel()}):
        if mid >= 512:
            ents = [carried_entry(e) for e in old.blocks[1][mid - 512]]
            carry[mid] = pk.raw_metatile(ents, old.attrs[1][mid - 512])
    for mid in (0x230, 0x231):
        ents = town.blocks[1][mid - 512]
        assert all((e & 1023) < 512 for e in ents)
        carry[mid] = pk.raw_metatile(list(ents), town.attrs[1][mid - 512])

    # 3. lay the map out
    grid = np.zeros((H, W), np.uint16)
    def put(x, y, mid, col, elev=3): grid[y, x] = (mid & 1023) | (col << 10) | (elev << 12)
    # forest runs per column
    for x in range(W):
        y = 0
        while y < H:
            if mat[y, x] != 'T': y += 1; continue
            y0 = y
            while y < H and mat[y, x] == 'T': y += 1
            # HGSS forest exactly as the accepted route (and its Cherrygrove seam) draws it: a
            # six-row band of overlapping trees on a global phase, so blocks join the seam columns.
            for yy in range(y0, y):
                put(x, yy, FOREST_BAND[yy % 6][x % 2], 3)
    # blossom handoff: trees at the bottom edge of west-end forest blocks become blossom trees
    placed = 0
    rng = np.random.default_rng(29)
    BLOSSOM_IDS = {carry.get(v, v) for pair in BLOSSOM for v in pair}
    for y in range(ROW0, KEEP_ROW - 1):
        for x in range(KEEP_COLS, BLOSSOM_MAX_X, 2):
            # a blossom tree is three cells tall: it replaces a 2x2 tree and the row above it,
            # so its trunk row lands on the tree's trunk row
            if y % 6 != 0 or y + 2 >= KEEP_ROW or not all(mat[y + i, x + j] == 'T' for i in range(3) for j in range(2)): continue
            if any((grid[y + i, x + j] & 1023) in BLOSSOM_IDS for i in range(-1, 4) for j in range(-2, 4) if 0 <= y + i < H and 0 <= x + j < W): continue
            # density fades west to east: Gold's grove spills onto the route, then ordinary woodland
            chance = 0.6 * (1 - (x - KEEP_COLS) / (BLOSSOM_MAX_X - KEEP_COLS))
            if rng.random() > chance: continue
            for i, (l, r) in enumerate(BLOSSOM):
                put(x, y + i, carry.get(l, l), 3); put(x + 1, y + i, carry.get(r, r), 3)
            placed += 1
    # ground, path and the sliced pieces
    for y in range(H):
        for x in range(W):
            m = mat[y, x]
            if m in 'TX' or grid[y, x]: continue
            ph = (x % 2, y % 2)
            if m == '.': put(x, y, lawn_id(x, y), 0)
            elif m == 'P':
                mask = tuple((0 <= y + dy < H and 0 <= x + dx < W and (mat[y + dy, x + dx] == 'P' or (mat[y + dy, x + dx] == 'X' and ((cur[y + dy, x + dx] & 1023) in SAND_IDS))))
                             for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)))
                put(x, y, path_id(mask, x), 0)
            elif m == 'G':
                nb = tuple(int(0 <= y + dy < H and 0 <= x + dx < W and mat[y + dy, x + dx] == 'G') for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)))
                put(x, y, mt[('G', nb, ph)], 0)
            elif m == '_': put(x, y, mt[('ledge', 'ledge_a' if x % 2 else 'ledge_b', ph)], 0)
            elif m == '|': put(x, y, mt[('ledge', 'wall', ph)], 3)
            elif m == '^': put(x, y, mt[('ledge', 'wall_top', ph)], 3)
            elif m == 'a': put(x, y, mt[('ledge', 'corner_se', ph)], 3)
            elif m == 'b': put(x, y, mt[('ledge', 'corner_sw', ph)], 3)
            elif m == 'c': put(x, y, mt[('ledge', 'corner_ne', ph)], 3)
            elif m == 'f': put(x, y, mt[('f', ph)], 0)
            elif m == 's': put(x, y, mt[('s', ph)], 3)
            elif m == 'L': put(x, y, mt[('L',)], 0)
            elif m == 'g':
                k = ('g', x - 48, y - ROW0 - 1)
                if k in mt: put(x, y, mt[k], 3)
                else: put(x, y, lawn_id(x, y), 0)
            elif m == 'A': put(x, y, mt[('A', x - 20, y - ROW0 - 9)], 3)
    # carried-over regions, remapped
    for y in range(H):
        for x in range(W):
            if mat[y, x] == 'X':
                v = int(cur[y, x]); mid = v & 1023
                grid[y, x] = (carry.get(mid, mid) & 1023) | (v & 0xFC00)

    # 4. write everything
    ts = GAME / 'data/tilesets/secondary' / TS_NAME
    pk.write(ts, {10: blossom_pal, **{nb: old.pals[1][ob][1:] for ob, nb in bank_map.items()}})
    (GAME / f'data/layouts/{MAP}/map.bin').write_bytes(struct.pack('<%dH' % (W * H), *grid.ravel().tolist()))
    lj = GAME / 'data/layouts/layouts.json'; L = json.loads(lj.read_text())
    for l in L['layouts']:
        if l['id'] == LAYOUT: l['secondary_tileset'] = 'gTileset_' + TS_SYM
    lj.write_text(json.dumps(L, indent=2) + '\n')
    register()
    OUT_ART.mkdir(parents=True, exist_ok=True)
    full = Tileset(GAME, TS_NAME, 'cherrygrove')
    full.map_image(grid.ravel().tolist(), W).save(OUT_ART / 'route29-overview.png')
    full.sheet(OUT_ART / 'tileset-sheet.png')
    report = dict(tiles=len(pk.tiles), metatiles=len(pk.metatiles), banks={b: len(c) for b, c in pk.pal.items()},
                  blossoms=placed, materials={k: int(v) for k, v in Counter(mat.ravel()).items()},
                  carried_metatiles={int(k): int(v) for k, v in carry.items()})
    (OUT_ART / 'build-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))

def register():
    h = GAME / 'src/data/tilesets/headers.h'; s = h.read_text()
    if TS_SYM not in s:
        line = (f'const struct Tileset gTileset_{TS_SYM} = {{ .isCompressed = TRUE, .isSecondary = TRUE, .tiles = gTilesetTiles_{TS_SYM}, '
                f'.palettes = gTilesetPalettes_{TS_SYM}, .metatiles = gMetatiles_{TS_SYM}, .metatileAttributes = gMetatileAttributes_{TS_SYM}, .callback = NULL }};\n')
        s = s.replace('// End Claude routes\n', line + '// End Claude routes\n', 1); h.write_text(s)
    g = GAME / 'src/data/tilesets/graphics.h'; s = g.read_text()
    if TS_SYM not in s:
        block = f'const u32 gTilesetTiles_{TS_SYM}[] = INCGFX_U32("data/tilesets/secondary/{TS_NAME}/tiles.png", ".4bpp.fastSmol");\n'
        block += f'const u16 gTilesetPalettes_{TS_SYM}[][16] = {{\n' + ''.join(f'INCGFX_U16("data/tilesets/secondary/{TS_NAME}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n'
        s = s.rstrip('\n') + '\n\n' + block; g.write_text(s)
    m = GAME / 'src/data/tilesets/metatiles.h'; s = m.read_text()
    if TS_SYM not in s:
        s = s.rstrip('\n') + f'\nconst u16 gMetatiles_{TS_SYM}[] = INCBIN_U16("data/tilesets/secondary/{TS_NAME}/metatiles.bin");\n'
        s += f'const u16 gMetatileAttributes_{TS_SYM}[] = INCBIN_U16("data/tilesets/secondary/{TS_NAME}/metatile_attributes.bin");\n'; m.write_text(s)

if __name__ == '__main__':
    main()
