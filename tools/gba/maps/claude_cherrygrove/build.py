#!/usr/bin/env python3
"""Compose the Cherrygrove exterior and install it into an isolated workbench checkout.

Pipeline: paint every object onto a map-sized indexed canvas (one palette bank per
pixel), slice it into 8x8 tiles over a primary-ground grid, dedupe into the
secondary tileset, and write layouts, events, doors, palettes and route stubs.
Run from the repository root:

    python3 tools/gba/maps/claude_cherrygrove/build.py tools/vendor/gba/claude-cherrygrove
"""
from __future__ import annotations
import json, re, struct, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from tiles import Tileset  # noqa: E402
from claude_cherrygrove import art, layout as L, cast  # noqa: E402

ROOT = HERE.parents[3]
OUT = ROOT / 'gba/art/claude-cherrygrove'

MB_SAND, MB_SIGNPOST, MB_ANIMATED_DOOR, MB_OCEAN = 33, 29, 105, 21
COVERED, NORMAL = 1 << 12, 0
GRASS, WATER = 0x001, 0x170
SAND, WETSAND = 0x8000, 0x8001   # secondary ground assets, resolved by grid_for
PATH = {'C': 0x121, 'N': 0x119, 'S': 0x129, 'W': 0x120, 'E': 0x122, 'NW': 0x118, 'NE': 0x11a, 'SW': 0x128, 'SE': 0x12a}

# ----------------------------------------------------------------- canvas

class MapCanvas:
    def __init__(self, w, h):
        self.w, self.h = w * 16, h * 16
        self.bank = np.full((self.h, self.w), -1, dtype=np.int8)
        self.idx = np.zeros((self.h, self.w), dtype=np.uint8)
        self.above = np.zeros((h, w), dtype=bool)      # cells whose object layer draws above sprites
    def blit(self, c, px, py):
        h, w = c.px.shape
        x0, y0 = max(px, 0), max(py, 0); x1, y1 = min(px + w, self.w), min(py + h, self.h)
        if x1 <= x0 or y1 <= y0: return
        src = c.px[y0 - py:y1 - py, x0 - px:x1 - px]; m = src != 0
        self.bank[y0:y1, x0:x1][m] = c.pal.bank; self.idx[y0:y1, x0:x1][m] = src[m]
    def put(self, x, y, bank, i):
        if 0 <= x < self.w and 0 <= y < self.h: self.bank[y, x] = bank; self.idx[y, x] = i

# ----------------------------------------------------------------- town composition

def compose_town(assets):
    W, H = L.W, L.H
    ground = np.full((H, W), GRASS, dtype=np.uint16)
    solid = np.zeros((H, W), dtype=bool)
    behavior = np.zeros((H, W), dtype=np.uint8)
    mc = MapCanvas(W, H)
    objects = []   # (sort_y, x_px, y_px, canvas)

    def cell_solid(x, y, w=1, h=1):
        solid[max(y, 0):y + h, max(x, 0):x + w] = True

    # Sea and beach ground.
    for y in range(H):
        for x in range(W):
            if y >= 4 and x < L.shore(y): ground[y, x] = WATER; cell_solid(x, y)
            if y < 4 and x < L.shore(4) and y >= L.CLIFF_ROWS[1]: ground[y, x] = WATER; cell_solid(x, y)
    for y in range(30, H):
        for x in range(0, 29): ground[y, x] = WATER; cell_solid(x, y)
    # Paths.
    lane = np.zeros((H, W), dtype=bool)
    for (x, y, w, h) in L.LANES + [L.BATTLE_YARD]: lane[y:y + h, x:x + w] = True
    for y in range(H):
        for x in range(W):
            if not lane[y, x]: continue
            n = y > 0 and lane[y - 1, x]; s = y < H - 1 and lane[y + 1, x]; wv = x > 0 and lane[y - 1 + 1, x - 1]; e = x < W - 1 and lane[y, x + 1]
            wv = x > 0 and lane[y, x - 1]
            n = n or y == 0; s = s or y == H - 1; wv = wv or x == 0; e = e or x == W - 1
            key = 'C'
            if not n and not wv: key = 'NW'
            elif not n and not e: key = 'NE'
            elif not s and not wv: key = 'SW'
            elif not s and not e: key = 'SE'
            elif not n: key = 'N'
            elif not s: key = 'S'
            elif not wv: key = 'W'
            elif not e: key = 'E'
            ground[y, x] = PATH[key]
    # Beach: sand painted at pixel level with an organic shoreline and grass edge.
    # Periodic (32 px) edge waves so shoreline and grass-edge tiles dedupe.
    WAVE = [2, 2, 3, 3, 4, 4, 4, 3, 3, 2, 2, 1, 1, 1, 1, 2, 2, 3, 4, 4, 5, 5, 4, 4, 3, 2, 2, 1, 0, 0, 1, 1]
    GWAVE = [3, 3, 2, 2, 1, 1, 2, 2, 3, 4, 4, 5, 5, 4, 3, 3, 2, 1, 1, 1, 2, 3, 3, 4, 5, 5, 4, 4, 3, 2, 2, 2]
    FOAM = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1]
    sand, wet = assets['sand'], assets['sand_wet']
    b = sand.pal.bank
    for y in range(4, 30):
        for x in range(L.shore(y) + 1, L.sand_end(y) - 1): ground[y, x] = SAND
    for py in range(4 * 16, 30 * 16):
        cy = py // 16
        sx = L.shore(cy) * 16 + 1 + WAVE[py % 32]
        ex = L.sand_end(cy) * 16 - 6 + GWAVE[py % 32]
        for px in list(range(sx, (L.shore(cy) + 1) * 16)) + list(range((L.sand_end(cy) - 1) * 16, ex)):
            t = sand if px >= sx + 3 else wet
            mc.put(px, py, t.pal.bank, int(t.px[py % 16, px % 16]))
        mc.put(sx - 1, py, b, sand.pal.index['foam'])
        mc.put(sx - 2, py, b, sand.pal.index['foam2'] if FOAM[py % 32] else sand.pal.index['foam'])
        if FOAM[(py + 5) % 32] and FOAM[py % 32]: mc.put(sx - 3, py, b, sand.pal.index['foam2'])
    for y in range(4, 30):
        for x in range(L.shore(y), L.sand_end(y)):
            if not solid[y, x]: behavior[y, x] = MB_SAND
    # Cliff band over the sea and beach.
    cy0 = L.CLIFF_ROWS[0]
    for x in range(L.CLIFF_X[0], L.CLIFF_X[1], 2):
        piece = assets['cliff_r'] if x + 2 >= L.CLIFF_X[1] else assets['cliff']
        objects.append((cy0 * 16 + 31, x * 16, cy0 * 16, piece)); cell_solid(x, cy0, 2, 2)
        for yy in (cy0 + 1,):
            for xx in (x, x + 1):
                ground[yy, xx] = WATER if xx < L.shore(4) else GRASS
    # Forest bands: staggered lattice, one cell of vertical overlap.
    def forest(x0, y0, x1, y1):
        for j, y in enumerate(range(y0, y1 + 1, 1)):
            for x in range(x0 + (j % 2), x1 + 1, 2):
                objects.append((y * 16 + 31 + j * 0.01, x * 16, y * 16, assets['tree']))
        cell_solid(x0, y0, x1 - x0 + 1, y1 - y0 + 1)
    for band in L.FOREST: forest(*band)
    for (x, y) in L.TREES: objects.append((y * 16 + 31, x * 16, y * 16, assets['tree'])); cell_solid(x, y, 2, 2)
    for (x, y) in L.BLOSSOMS: objects.append((y * 16 + 31, x * 16, y * 16, assets['blossom'])); cell_solid(x, y, 2, 2)
    # Buildings.
    doors = {}
    for b in L.BUILDINGS:
        c = assets[b['style']]; w, h = L.SIZE[b['style']]
        objects.append((b['y'] * 16 + h * 16 - 1, b['x'] * 16, b['y'] * 16, c)); cell_solid(b['x'], b['y'], w, h)
        dx, dy = L.door_of(b); solid[dy, dx] = False; behavior[dy, dx] = MB_ANIMATED_DOOR; doors[b['name']] = (dx, dy)
    # Gardens: beds ringed by a picket fence.
    for i, (x, y, w, h) in enumerate(L.GARDENS):
        colors = ['bed_red', 'bed_yel', 'bed_pink']
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                objects.append((yy * 16 + 15, xx * 16, yy * 16, assets[colors[(xx + yy + i) % 3]])); cell_solid(xx, yy)
        for xx in range(x, x + w):
            objects.append(((y - 1) * 16 + 15, xx * 16, (y - 1) * 16, assets['fence_h'])); cell_solid(xx, y - 1)
            objects.append(((y + h) * 16 + 15, xx * 16, (y + h) * 16, assets['fence_h'])); cell_solid(xx, y + h)
        for yy in range(y - 1, y + h + 1):
            objects.append((yy * 16 + 15, (x - 1) * 16, yy * 16, assets['fence_post' if yy in (y - 1, y + h) else 'fence_v'])); cell_solid(x - 1, yy)
            objects.append((yy * 16 + 15, (x + w) * 16, yy * 16, assets['fence_post' if yy in (y - 1, y + h) else 'fence_v'])); cell_solid(x + w, yy)
    for (x, y) in L.PARK_PROPS['bench']: objects.append((y * 16 + 15, x * 16, y * 16, assets['bench'])); cell_solid(x, y)
    for (x, y) in L.PARK_PROPS['lamp']:
        objects.append((y * 16 + 15, x * 16, (y - 1) * 16, assets['lamp'])); cell_solid(x, y); mc.above[y - 1, x] = True
    for (x, y) in L.BUSHES: objects.append((y * 16 + 15, x * 16, y * 16, assets['bush'])); cell_solid(x, y)
    for (x, y) in L.MAILBOXES: objects.append((y * 16 + 15, x * 16, y * 16, assets['mailbox'])); cell_solid(x, y)
    for (name, x, y) in L.SIGNS: objects.append((y * 16 + 15, x * 16, y * 16, assets['sign'])); cell_solid(x, y); behavior[y, x] = MB_SIGNPOST
    # Waterfront: pier, boats, nets; lookout deck under the cliff.
    p = L.PIER
    for x in range(p['x0'], p['x1']):
        top = assets['rail_v'] if x == p['x0'] else assets['deck_n']
        bot = assets['rail_v'] if x == p['x0'] else assets['deck_s']
        objects.append((p['y'] * 16 + 15, x * 16, p['y'] * 16, top)); objects.append(((p['y'] + 1) * 16 + 15, x * 16, (p['y'] + 1) * 16, bot))
        for yy in (p['y'], p['y'] + 1):
            solid[yy, x] = (x == p['x0']); behavior[yy, x] = 0
    for (x, y) in L.BOATS: objects.append((y * 16 + 31, x * 16, y * 16, assets['boat'])); cell_solid(x, y, 2, 2)
    for (x, y) in L.NETS: objects.append((y * 16 + 15, x * 16, y * 16, assets['nets'])); cell_solid(x, y, 2, 1)
    lk = L.LOOKOUT
    for x in range(lk['x'], lk['x'] + lk['w']):
        objects.append((lk['y'] * 16 + 15, x * 16, lk['y'] * 16, assets['rail_h'])); cell_solid(x, lk['y'])
        bottom = assets['rail_v'] if x == lk['x'] else assets['deck_s']
        objects.append(((lk['y'] + 1) * 16 + 15, x * 16, (lk['y'] + 1) * 16, bottom))
        solid[lk['y'] + 1, x] = (x == lk['x']); behavior[lk['y'] + 1, x] = 0
    objects.append((lk['y'] * 16 + 15.5, (lk['x'] + 2) * 16, lk['y'] * 16, assets['bench']))
    for (x, y) in L.ROCKS1: objects.append((y * 16 + 15, x * 16, y * 16, assets['rock1'])); cell_solid(x, y)
    for (x, y) in L.ROCKS2: objects.append((y * 16 + 23, x * 16, y * 16, assets['rock2'])); cell_solid(x, y, 2, 2)
    # Petal-strewn park lawn, only on open grass.
    px0, py0, pw, ph = L.PETALS
    for y in range(py0, py0 + ph):
        for x in range(px0, px0 + pw):
            if (x * 7 + y * 3) % 5 < 3 and ground[y, x] == GRASS and not solid[y, x] and not solid[max(y - 1, 0), x]:
                objects.append((-1, x * 16, y * 16, assets['petals']))
    # Paint back to front.
    for _, px, py, c in sorted(objects, key=lambda o: (o[0], o[1])): mc.blit(c, px, py)
    return dict(ground=ground, solid=solid, behavior=behavior, canvas=mc, doors=doors, W=W, H=H)

def compose_stub(assets, W, H, path_rect, side):
    """Route approach stubs: forest with one sand lane leaving the town edge."""
    ground = np.full((H, W), GRASS, dtype=np.uint16); solid = np.zeros((H, W), dtype=bool); behavior = np.zeros((H, W), dtype=np.uint8)
    mc = MapCanvas(W, H); objects = []
    x, y, w, h = path_rect
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            if side == 'up': ground[yy, xx] = PATH['W'] if xx == x else PATH['E'] if xx == x + w - 1 else PATH['C']
            else: ground[yy, xx] = PATH['N'] if yy == y else PATH['S'] if yy == y + h - 1 else PATH['C']
    lane = ground != GRASS
    for j, yy in enumerate(range(-1, H)):
        for xx in range(-2 + (j % 2), W, 2):
            if lane[max(yy, 0):yy + 2, max(xx, 0):xx + 2].any(): continue
            objects.append((yy * 16 + 31 + j * 0.01, xx * 16, yy * 16, assets['tree']))
    solid[:] = ~lane
    for _, px, py, c in sorted(objects, key=lambda o: (o[0], o[1])): mc.blit(c, px, py)
    return dict(ground=ground, solid=solid, behavior=behavior, canvas=mc, W=W, H=H)

# ----------------------------------------------------------------- packing

class Packer:
    def __init__(self, primary_blocks):
        self.tiles = []          # list of (bank, 64 indices)
        self.lookup = {}
        self.blocks = []         # secondary metatiles: 8 entries
        self.attrs = []
        self.block_lookup = {}
        self.primary_blocks = primary_blocks
        self.conflicts = 0
        self.conflict_cells = []
    def tile(self, bank, arr):
        if bank < 0: return None
        for hf in (0, 1):
            for vf in (0, 1):
                a = arr[::-1] if vf else arr; a = a[:, ::-1] if hf else a
                key = (bank, a.tobytes())
                if key in self.lookup: return self.lookup[key] | (hf << 10) | (vf << 11)
        key = (bank, arr.tobytes()); tid = 512 + len(self.tiles)
        if tid >= 1024:
            counts = {}
            for b, _ in self.tiles: counts[b] = counts.get(b, 0) + 1
            raise SystemExit(f'secondary tile budget exhausted; tiles per bank: {counts}')
        self.tiles.append((bank, arr.copy())); self.lookup[key] = tid; return tid
    def slice(self, mc, cx, cy, palettes):
        """Four 8x8 object tiles of one cell -> metatile entries (or None when empty)."""
        entries = []; opaque = True
        for q in range(4):
            x0, y0 = cx * 16 + (q % 2) * 8, cy * 16 + (q // 2) * 8
            bank = mc.bank[y0:y0 + 8, x0:x0 + 8]; idx = mc.idx[y0:y0 + 8, x0:x0 + 8].astype(np.int64)
            if (bank < 0).all(): entries.append(0); opaque = False; continue
            if (bank < 0).any(): opaque = False
            banks = [b for b in np.unique(bank) if b >= 0]
            if len(banks) > 1:
                counts = {b: int((bank == b).sum()) for b in banks}; major = max(counts, key=counts.get); self.conflicts += 1
                self.conflict_cells.append((cx, cy, tuple(int(b) for b in banks)))
                pal = np.array(palettes[major].gba()[1:])
                for b in banks:
                    if b == major: continue
                    src = np.array(palettes[b].gba()[1:])
                    for yy, xx in zip(*np.nonzero(bank == b)):
                        rgb = src[idx[yy, xx] - 1]; idx[yy, xx] = int(((pal - rgb) ** 2).sum(axis=1).argmin()) + 1
                bank = np.where(bank >= 0, major, -1)
            arr = np.where(bank >= 0, idx, 0).astype(np.uint8)
            b = int(banks[0]) if len(banks) == 1 else int(major)
            entries.append(self.tile(b, arr) | (b << 12))
        return entries, opaque
    def metatile(self, entries, attr):
        key = (tuple(entries), attr)
        if key in self.block_lookup: return self.block_lookup[key]
        mid = 512 + len(self.blocks); assert mid < 1024, 'secondary metatile budget exhausted'
        self.blocks.append(tuple(entries)); self.attrs.append(attr); self.block_lookup[key] = mid; return mid

def grid_for(comp, packer, palettes):
    W, H, mc = comp['W'], comp['H'], comp['canvas']
    grid = []
    for y in range(H):
        for x in range(W):
            g = int(comp['ground'][y, x])
            if g >= 0x8000:
                tile = packer.ground_assets[g]; base = []
                for q in range(4):
                    arr = tile.px[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8].astype(np.uint8)
                    base.append(packer.tile(tile.pal.bank, arr) | (tile.pal.bank << 12))
                base = base + [0, 0, 0, 0]; g_attr = 0
            else:
                base = packer.primary_blocks[g]; g_attr = packer.primary_attrs[g] & 0xF000
            entries, opaque = packer.slice(mc, x, y, palettes)
            beh = int(comp['behavior'][y, x])
            if all(e == 0 for e in entries):
                if beh or g >= 0x8000:
                    mid = packer.metatile(list(base), beh | g_attr)
                else:
                    mid = g
            elif opaque and not mc.above[y, x]:
                mid = packer.metatile(entries + [0, 0, 0, 0], beh | COVERED)
            elif mc.above[y, x]:
                mid = packer.metatile(list(base[:4]) + entries, beh | NORMAL)
            else:
                mid = packer.metatile(list(base[:4]) + entries, beh | COVERED)
            v = mid | (0x3 << 12) | (0xC00 if comp['solid'][y, x] else 0)
            grid.append(v)
    return grid

def base_attr(packer, g):
    return packer.primary_attrs[g]

# ----------------------------------------------------------------- engine writing

def write_palettes(game, palettes):
    sec = game / 'data/tilesets/secondary/cherrygrove/palettes'; sec.mkdir(parents=True, exist_ok=True)
    for bank in range(16):
        pal = next((p for p in palettes.values() if p.bank == bank and bank >= 6), None)
        colors = pal.gba() if pal else [(0, 0, 0)] * 16
        (sec / f'{bank:02}.pal').write_text('JASC-PAL\n0100\n16\n' + '\n'.join(' '.join(map(str, c)) for c in colors) + '\n')

def grade(rgb):
    """Johto grade for the primary general palette: minty grass, cream sand, clearer sea."""
    r, g, b = rgb
    if g > r * 1.15 and g > b * 1.1:     # greens
        return (int(r * 0.80 + 6), int(g * 0.90 + 12), int(b * 0.86 + 34))
    if b > r * 1.25 and b > g * 1.05:    # blues
        return (int(r * 0.78 + 4), int(g * 0.94 + 6), min(255, int(b * 0.96 + 10)))
    if r > 180 and g > 150 and b < 160 and r - b > 60:   # sands
        return (min(255, int(r * 0.96 + 8)), min(255, int(g * 0.97 + 8)), min(255, int(b * 0.9 + 30)))
    return rgb

def write_primary_palettes(game, overrides):
    """Grade the general palettes; then place the flower and beach colours in free slots of banks 2 and 5."""
    src = game / 'data/tilesets/primary/general/palettes'; dst = game / 'data/tilesets/primary/cherrygrove/palettes'
    graded = []
    for n in range(16):
        colors = [tuple(map(int, l.split())) for l in (src / f'{n:02}.pal').read_text().splitlines()[3:19]]
        colors = [grade(c) for c in colors]
        for pal in overrides:
            if pal.bank == n:
                for slot, i in pal.by_slot.items(): colors[slot] = pal.colors[i]
        graded.append(colors)
        (dst / f'{n:02}.pal').write_text('JASC-PAL\n0100\n16\n' + '\n'.join(' '.join(map(str, c)) for c in colors) + '\n')
    return graded

def write_tiles(game, packer):
    n = len(packer.tiles); rows = max(1, (n + 15) // 16)
    im = Image.new('P', (128, rows * 8), 0)
    pal = []
    for i in range(16): pal += [i * 16, i * 16, i * 16]
    im.putpalette(pal + [0] * (768 - len(pal)))
    px = im.load()
    for i, (bank, arr) in enumerate(packer.tiles):
        for yy in range(8):
            for xx in range(8): px[(i % 16) * 8 + xx, (i // 16) * 8 + yy] = int(arr[yy, xx])
    folder = game / 'data/tilesets/secondary/cherrygrove'; folder.mkdir(parents=True, exist_ok=True)
    im.save(folder / 'tiles.png', bits=4)
    (folder / 'metatiles.bin').write_bytes(b''.join(struct.pack('<8H', *b) for b in packer.blocks))
    (folder / 'metatile_attributes.bin').write_bytes(struct.pack('<' + 'H' * len(packer.attrs), *packer.attrs))

def write_layout(game, layouts, name, grid, W, H, border):
    folder = game / f'data/layouts/{name}'; folder.mkdir(parents=True, exist_ok=True)
    (folder / 'map.bin').write_bytes(struct.pack('<' + 'H' * len(grid), *grid))
    (folder / 'border.bin').write_bytes(struct.pack('<4H', *border))
    for lay in layouts['layouts']:
        if lay['name'] == name + '_Layout': lay['width'] = W; lay['height'] = H

def door_frames(assets, b):
    """Three 16x32 frames of the door column opening; returns a P-mode 16x96 image and the bank."""
    c = assets[b['style']]; w, h = L.SIZE[b['style']]
    col = L.DOOR_COLUMN[b['style']] * 16; y0 = (h - 2) * 16
    closed = c.px[y0:y0 + 32, col:col + 16].copy()
    pal = c.pal; ol = pal.index['ol']
    sliding = b['style'] in ('center', 'mart')
    if sliding:
        panes = (2, 14, 42 - y0 + (0 if b['style'] == 'center' else -13), 60 - y0 + (0 if b['style'] == 'center' else -13))
        x0, x1, ya, yb = panes
    else:
        x0, x1, ya, yb = 2, 14, 42 - y0, 61 - y0
    frames = []
    for k, amount in enumerate((4, 8, 12)):
        f = closed.copy()
        f[ya:yb, x0:x1] = ol
        f[yb - 2:yb, x0:x1] = pal.index['w0'] if 'w0' in pal.index else ol
        if sliding:
            half = (x1 - x0) // 2; shift = amount // 2
            left = closed[ya:yb, x0:x0 + half]; right = closed[ya:yb, x0 + half:x1]
            f[ya:yb, max(x0 - shift, 0):max(x0 - shift, 0) + max(half - shift, 0)] = left[:, shift:] if shift < half else left[:, :0]
            f[ya:yb, x0 + half + shift:x1] = right[:, :max(half - shift, 0)]
        else:
            keep = x1 - x0 - amount
            if keep > 0:
                src = closed[ya:yb, x0:x1]
                cols = np.linspace(0, x1 - x0 - 1, keep).astype(int)
                f[ya:yb, x0:x0 + keep] = src[:, cols]
        frames.append(f)
    strip = np.concatenate(frames, axis=0)
    im = Image.fromarray(strip.astype(np.uint8), 'P')
    flat = []
    for r, g, bb in pal.gba(): flat += [r, g, bb]
    im.putpalette(flat + [0] * (768 - len(flat)))
    return im, pal.bank

def write_doors(game, assets, comp, grid):
    folder = game / 'graphics/door_anims/claude_cherrygrove'; folder.mkdir(parents=True, exist_ok=True)
    src_path = game / 'src/field_door.c'; source = src_path.read_text()
    start = source.find('// Claude Cherrygrove doors'); end = source.find('// End Claude Cherrygrove doors')
    if start >= 0: source = source[:start] + source[end + len('// End Claude Cherrygrove doors\n'):]
    decl = ['// Claude Cherrygrove doors', 'extern const struct Tileset gTileset_Cherrygrove;']; table = []; report = []
    for b in L.BUILDINGS:
        im, bank = door_frames(assets, b); name = b['name']
        im.save(folder / f'{name}.png', bits=4)
        dx, dy = comp['doors'][name]; mid = grid[dy * comp['W'] + dx] & 1023
        decl.append(f'static const u8 sClaudeDoor_{name}[] = INCGFX_U8("graphics/door_anims/claude_cherrygrove/{name}.png", ".4bpp");')
        decl.append(f'static const u8 sClaudeDoorPal_{name}[8] = {{{", ".join([str(bank)] * 8)}}};')
        sound = 'DOOR_SOUND_SLIDING' if b['style'] in ('center', 'mart') else 'DOOR_SOUND_NORMAL'
        table.append(f'    {{.metatileNum = {mid}, .tileset = &gTileset_Cherrygrove, .sound = {sound}, .size = DOOR_SIZE_1x2, .tiles = sClaudeDoor_{name}, .palettes = sClaudeDoorPal_{name}}},')
        report.append(dict(name=name, door=[dx, dy], metatile=mid, bank=bank))
    marker = 'static const struct DoorGraphics sDoorAnimGraphicsTable[] =\n{'
    assert marker in source
    source = source.replace(marker, '\n'.join(decl) + '\n// End Claude Cherrygrove doors\n' + marker + '\n' + '\n'.join(table))
    src_path.write_text(source)
    return report

def write_events(game, comp, grid):
    mp = game / 'data/maps/CherrygroveCity/map.json'; m = json.loads(mp.read_text())
    order = ['PlayerHouse', 'GoldHouse', 'NeighborHouse', 'TransplantHouse', 'Mart', 'PokemonCenter']
    ids = {b['name']: 'MAP_CHERRYGROVE_' + re.sub(r'(?<!^)(?=[A-Z])', '_', b['name']).upper() for b in L.BUILDINGS}
    m['warp_events'] = [dict(x=comp['doors'][n][0], y=comp['doors'][n][1], elevation=0, dest_map=ids[n], dest_warp_id='0') for n in order]
    scripts = ['CherrygroveCity_MapScripts::\n    .byte 0\n']
    def text_block(label, text):
        scripts.append(f'{label}::\n    msgbox {label}_Text, MSGBOX_NPC\n    end\n\n{label}_Text:\n    .string "{text}$"\n')
    m['bg_events'] = []
    for name, x, y in L.SIGNS:
        label = f'CherrygroveCity_{name}'; text_block(label, cast.SIGNS[name])
        m['bg_events'].append(dict(type='sign', x=x, y=y, elevation=0, player_facing_dir='BG_EVENT_PLAYER_FACING_ANY', script=label))
    m['object_events'] = []
    for npc in cast.NPCS:
        label = f'CherrygroveCity_{npc["id"]}'
        if npc.get('script'): scripts.append(npc['script'].replace('LABEL', label))
        else: text_block(label, npc['text'])
        x, y = npc['pos']
        if comp['solid'][y, x]: print('WARNING: NPC on solid cell', npc['id'], x, y)
        m['object_events'].append(dict(local_id='LOCALID_' + npc['id'].upper(), graphics_id=npc['gfx'], x=x, y=y, elevation=3,
                                       movement_type=npc['move'], movement_range_x=npc.get('range', (0, 0))[0], movement_range_y=npc.get('range', (0, 0))[1],
                                       trainer_type='TRAINER_TYPE_NONE', trainer_sight_or_berry_tree_id='0', script=label, flag='0'))
    mp.write_text(json.dumps(m, indent=2) + '\n')
    (game / 'data/maps/CherrygroveCity/scripts.inc').write_text('\n'.join(scripts))
    # Spawn for a new game.
    ng = game / 'src/new_game.c'; s = ng.read_text()
    s = re.sub(r'MAP_NUM\(MAP_CHERRYGROVE_CITY\), WARP_ID_NONE, \d+, \d+', f'MAP_NUM(MAP_CHERRYGROVE_CITY), WARP_ID_NONE, {L.SPAWN[0]}, {L.SPAWN[1]}', s)
    ng.write_text(s)

def render_preview(game, grid, W, H, path):
    t = Tileset(game, 'cherrygrove', 'cherrygrove'); t.map_image(grid, W).save(path)

def main():
    game = Path(sys.argv[1]).resolve(); assert game != ROOT / 'game' and (game / '.git').is_dir()
    assets = art.build_all(); palettes = {p.bank: p for p in art.PALETTES.values() if p.bank >= 6}
    OUT.mkdir(parents=True, exist_ok=True)
    base = Tileset(game, 'petalburg', 'general')
    # Match the shore water tones to the graded primary water so foam sits on live water.
    water_tiles = [e & 1023 for e in base.blocks[0][WATER][:4]]; wbank = base.blocks[0][WATER][0] >> 12
    counts = {}
    for tid in water_tiles:
        for v in base.tiles[0][tid]: counts[v % 16] = counts.get(v % 16, 0) + 1
    top = sorted(counts, key=counts.get, reverse=True)[:3]
    original = [tuple(map(int, l.split())) for l in (game / f'data/tilesets/primary/general/palettes/{wbank:02}.pal').read_text().splitlines()[3:19]]
    tones = sorted((grade(original[i]) for i in top), key=lambda c: -sum(c))
    shore = art.PALETTES['SHORE']
    for name, col in zip(['wl', 'wm', 'wd'], tones): shore.colors[shore.by_slot[shore.index[name]]] = tuple(col)
    graded = write_primary_palettes(game, [art.PALETTES['FLOWER'], art.PALETTES['SHORE']])
    write_palettes(game, palettes)
    palettes.update({2: art.PALETTES['FLOWER'], 5: art.PALETTES['SHORE']})
    packer = Packer(base.blocks[0]); packer.primary_attrs = base.attrs[0]; packer.ground_assets = {SAND: assets['sand'], WETSAND: assets['sand_wet']}
    town = compose_town(assets); grid = grid_for(town, packer, palettes)
    # Border: dense canopy from a small forest composition.
    forest = compose_stub(assets, 4, 4, (0, 0, 0, 0), 'up'); fgrid = grid_for(forest, packer, palettes)
    border = [fgrid[1 * 4 + 1] & 1023, fgrid[1 * 4 + 2] & 1023, fgrid[2 * 4 + 1] & 1023, fgrid[2 * 4 + 2] & 1023]
    border = [b | 0x3c00 for b in border]
    layouts = json.loads((game / 'data/layouts/layouts.json').read_text())
    write_layout(game, layouts, 'CherrygroveCity', grid, L.W, L.H, border)
    r30 = compose_stub(assets, L.W, 12, (L.NORTH_EXIT[0], 0, L.NORTH_EXIT[1] - L.NORTH_EXIT[0], 12), 'up')
    g30 = grid_for(r30, packer, palettes); write_layout(game, layouts, 'CherrygroveRoute30Approach', g30, L.W, 12, border)
    r29 = compose_stub(assets, 16, L.H, (0, L.EAST_EXIT[0], 16, L.EAST_EXIT[1] - L.EAST_EXIT[0]), 'right')
    g29 = grid_for(r29, packer, palettes); write_layout(game, layouts, 'CherrygroveRoute29Approach', g29, 16, L.H, border)
    (game / 'data/layouts/layouts.json').write_text(json.dumps(layouts, indent=2) + '\n')
    write_tiles(game, packer)
    write_events(game, town, grid)
    doors = write_doors(game, assets, town, grid)
    render_preview(game, grid, L.W, L.H, OUT / 'town-overview.png')
    render_preview(game, g30, L.W, 12, OUT / 'route30-stub.png'); render_preview(game, g29, 16, L.H, OUT / 'route29-stub.png')
    report = dict(width=L.W, height=L.H, secondary_tiles=len(packer.tiles), secondary_metatiles=len(packer.blocks), bank_conflict_tiles=packer.conflicts,
                  doors=doors, spawn=L.SPAWN, buildings=[dict(b, door=L.door_of(b)) for b in L.BUILDINGS])
    (OUT / 'build-report.json').write_text(json.dumps(report, indent=2) + '\n')
    from collections import Counter
    print('conflicts by bank pair:', Counter(c[2] for c in packer.conflict_cells).most_common(8))
    print('conflict cells sample:', sorted(set((c[0], c[1]) for c in packer.conflict_cells))[:40])
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
