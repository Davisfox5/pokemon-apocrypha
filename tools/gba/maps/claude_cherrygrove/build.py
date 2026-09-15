#!/usr/bin/env python3
"""Compose the Cherrygrove exterior and install it into an isolated workbench checkout.

Pipeline: paint the ground at pixel level in the HGSS render's colours, paint every
object (HGSS-derived scenery) over it, slice both into 8x8 tiles, dedupe into a
primary tileset (terrain, shared with the route stubs) and a secondary tileset
(buildings and props), then write layouts, events, doors, palettes and route stubs.
Run from the repository root:

    python3 tools/gba/maps/claude_cherrygrove/build.py tools/vendor/gba/claude-cherrygrove
"""
from __future__ import annotations
import json, re, struct, sys
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from tiles import Tileset  # noqa: E402
from claude_cherrygrove import art, layout as L, cast, hgss, ground, banks  # noqa: E402
from claude_cherrygrove.pixel import Palette, Canvas  # noqa: E402

ROOT = HERE.parents[3]
OUT = ROOT / 'gba/art/claude-cherrygrove'

MB_SAND, MB_SIGNPOST, MB_ANIMATED_DOOR, MB_OCEAN = 33, 29, 105, 21
COVERED, NORMAL = 1 << 12, 0
G, P, S, W, R = ground.GRASS, ground.PATH, ground.SAND, ground.SEA, ground.ROCK

# ----------------------------------------------------------------- palette banks

GROUND_PAL = [hgss.GRASS, hgss.GRASS_SPECK, hgss.GRASS_SHADE, (96, 192, 144), hgss.PATH, hgss.PATH_SPECK, hgss.PATH_SPECK2,
              (128, 136, 120), (152, 144, 112), hgss.SAND, hgss.SAND2, hgss.SAND3, (208, 208, 168), (168, 216, 152), (216, 216, 176)]
SEA_PAL = [(24, 96, 216), (24, 104, 224), (32, 120, 224), (40, 136, 224), (56, 176, 224), (64, 192, 224),
           (200, 232, 224), (152, 224, 224), (104, 192, 224), (72, 160, 224),
           hgss.SAND, hgss.SAND2, hgss.SAND3, (208, 208, 168), (200, 192, 144)]

def build_assets():
    """All scenery as indexed canvases with their bank palettes and tile pools."""
    B = {}
    B['GROUND'] = banks.Bank(0, 'GROUND', 'primary'); B['GROUND'].palette = Palette(0, GROUND_PAL, [f'c{i}' for i in range(15)])
    B['SEA'] = banks.Bank(1, 'SEA', 'primary'); B['SEA'].palette = Palette(1, SEA_PAL, [f'c{i}' for i in range(15)])
    B['CLIFF'] = banks.Bank(2, 'CLIFF', 'primary').add('cliff', hgss.cliff()).add('cliff_sand', hgss.cliff_sand())
    B['TREE'] = banks.Bank(3, 'TREE', 'primary').add('tree', hgss.tree())
    B['FLOWERS'] = (banks.Bank(4, 'FLOWERS', 'primary').add('tulips0', hgss.tulips(0)).add('tulips1', hgss.tulips(1)).add('daisies', hgss.daisies())
                    .add('bush', hgss.bush()).add('fence_h', hgss.fence_h()).add('fence_v', hgss.fence_v()).add('fence_corner', hgss.fence_corner())
                    .keep((232, 232, 240), (200, 200, 208), (152, 152, 168)))
    B['ROCKS'] = banks.Bank(5, 'ROCKS', 'primary').add('sea_rock', hgss.sea_rock()).add('sea_rock_small', hgss.sea_rock_small()).add('rock', hgss.rock())
    ha, hb = hgss.house_a(), hgss.house_b()
    B['HOUSE'] = banks.Bank(6, 'HOUSE', 'secondary').add('house', ha).add('gable', hb).keep(*hgss.dominant(ha, (40, 58, 14, 14), 2))
    c = hgss.center()
    B['CENTER'] = banks.Bank(8, 'CENTER', 'secondary').add('center', c).keep(*hgss.dominant(c, (12, 60, 20, 6), 1), *hgss.dominant(c, (40, 80, 16, 12), 1))
    m = hgss.mart()
    B['MART'] = banks.Bank(9, 'MART', 'secondary').add('mart', m).add('mart_sign', hgss.mart_sign()).keep(*hgss.dominant(m, (50, 48, 16, 12), 1))
    assets = {}
    for b in B.values():
        if b.assets: assets.update(b.build())
    # Recolours share tiles: blue-roof transplant home (bank 7), blossom trees (bank 10).
    pal_house2 = banks.recolor(B['HOUSE'].palette, 7, lambda c: banks.hue_shift(c, 165, 0.8, 1.0) if c[0] > c[1] + 24 and c[0] > c[2] + 8 else c)
    pal_blossom = banks.recolor(B['TREE'].palette, 10, lambda c: banks.hue_shift(c, 245, 0.5, 1.35) if c[1] > c[0] and c[1] > c[2] else c)
    def clone(cv, pal):
        n = Canvas(cv.w, cv.h, pal); n.px = cv.px.copy(); n.pool = 'secondary'; return n
    assets['house2'] = clone(assets['house'], pal_house2); assets['house_l'] = assets['house']
    assets['blossom'] = clone(assets['tree'], pal_blossom)
    # Wood props from the hand-painted set (bank 11) plus the HGSS signpost and mailbox mapped into it.
    wood = art.PALETTES['WOOD']
    for k, f in art.ASSETS.items():
        if k in ('deck', 'deck_s', 'deck_n', 'deck_w', 'deck_e', 'rail_h', 'rail_v', 'boat', 'nets', 'bench', 'lamp'):
            cv = f(); cv.pool = 'secondary'; assets[k] = cv
    arr = np.array(wood.colors, dtype=np.int32)
    for k, a in (('sign', hgss.signpost()), ('mailbox', hgss.mailbox())):
        cv = Canvas(a.shape[1], a.shape[0], wood); mk = a[..., 3] > 0
        idx = ((a[mk][:, :3].astype(np.int32)[:, None, :] - arr[None]) ** 2).sum(-1).argmin(1)
        cv.px[mk] = np.array(wood.slots)[idx]; cv.pool = 'secondary'; assets[k] = cv
    palettes = {b.bank: b.palette for b in B.values()}
    palettes.update({7: pal_house2, 10: pal_blossom, 11: wood})
    return assets, palettes

# ----------------------------------------------------------------- canvas

class MapCanvas:
    def __init__(self, w, h):
        self.w, self.h = w * 16, h * 16
        self.bank = np.full((self.h, self.w), -1, dtype=np.int8)
        self.idx = np.zeros((self.h, self.w), dtype=np.uint8)
        self.above = np.zeros((h, w), dtype=bool)      # cells whose object layer draws above sprites
    def blit(self, c, px, py, flip=False):
        src = c.px[:, ::-1] if flip else c.px
        h, w = src.shape
        x0, y0 = max(px, 0), max(py, 0); x1, y1 = min(px + w, self.w), min(py + h, self.h)
        if x1 <= x0 or y1 <= y0: return
        s = src[y0 - py:y1 - py, x0 - px:x1 - px]; m = s != 0
        self.bank[y0:y1, x0:x1][m] = c.pal.bank; self.idx[y0:y1, x0:x1][m] = s[m]

def index_ground(rgba, mat, palettes):
    """Ground pixels -> (bank, idx) per 8x8 tile: sea-touching tiles use the SEA bank, the rest GROUND."""
    h, w = mat.shape
    bank = np.zeros((h, w), dtype=np.int8); idx = np.zeros((h, w), dtype=np.uint8)
    pals = {0: np.array(palettes[0].gba()[1:], dtype=np.int32), 1: np.array(palettes[1].gba()[1:], dtype=np.int32)}
    sea_tile = (mat == W).reshape(h // 8, 8, w // 8, 8).any(axis=(1, 3))
    foam = np.isin(rgba[..., :3].reshape(-1, 3).view([('', np.uint8)] * 3).ravel(),
                   np.array(SEA_PAL[6:10], dtype=np.uint8).view([('', np.uint8)] * 3).ravel()).reshape(h, w)
    sea_tile |= foam.reshape(h // 8, 8, w // 8, 8).any(axis=(1, 3))
    tb = np.repeat(np.repeat(sea_tile, 8, axis=0), 8, axis=1).astype(np.int8)
    for b in (0, 1):
        m = tb == b
        flat = rgba[m][:, :3].astype(np.int32)
        idx[m] = ((flat[:, None, :] - pals[b][None]) ** 2).sum(-1).argmin(1) + 1
        bank[m] = b
    return bank, idx

# ----------------------------------------------------------------- town composition

def compose_town(assets):
    Wd, Ht = L.W, L.H
    cells = np.full((Ht, Wd), G, dtype=np.int8)
    solid = np.zeros((Ht, Wd), dtype=bool)
    behavior = np.zeros((Ht, Wd), dtype=np.uint8)
    mc = MapCanvas(Wd, Ht)
    objects = []   # (sort_y, x_px, y_px, canvas, flip)

    def cell_solid(x, y, w=1, h=1):
        solid[max(y, 0):y + h, max(x, 0):x + w] = True
    def obj(canvas, cx, cy, sort=None, flip=False):
        h = canvas.h; objects.append(((cy * 16 + h - 1) if sort is None else sort, cx * 16, cy * 16, canvas, flip))

    # Sea, beach and cliff foot.
    for y in range(Ht):
        for x in range(Wd):
            if y >= L.SEA_TOP and x < L.shore(y): cells[y, x] = W; cell_solid(x, y)
            elif y >= L.SEA_TOP and x < L.sand_end(y): cells[y, x] = S
    for y in range(30, Ht):
        for x in range(0, 29): cells[y, x] = W; cell_solid(x, y)
    for x in range(L.CLIFF_X[0], L.CLIFF_X[1]):
        cells[L.CLIFF_ROWS[1], x] = R if x < L.shore(L.SEA_TOP) else S
    # Paths.
    for (x, y, w, h) in L.LANES + [L.BATTLE_YARD]: cells[y:y + h, x:x + w] = P
    for y in range(Ht):
        for x in range(Wd):
            if cells[y, x] == S and not solid[y, x]: behavior[y, x] = MB_SAND
    # Cliff band.
    cy0, cy1 = L.CLIFF_ROWS
    for x in range(L.CLIFF_X[0], L.CLIFF_X[1], 2):
        obj(assets['cliff'] if x < L.shore(L.SEA_TOP) - 1 else assets['cliff_sand'], x, cy0, sort=cy1 * 16 + 15); cell_solid(x, cy0, 2, cy1 - cy0 + 1)
    # Forest bands: the HGSS lattice (32 px rows and columns, odd rows offset one cell).
    def forest(x0, y0, x1, y1):
        for j, y in enumerate(range(y0, y1 + 1, 2)):
            for x in range(x0 + (j % 2), x1 + 1, 2):
                obj(assets['tree'], x, y)
        cell_solid(x0, y0, x1 - x0 + 1, y1 - y0 + 3)   # crowns two cells, trunks land one row below the last row
    for band in L.FOREST: forest(*band)
    for (x, y) in L.TREES: obj(assets['tree'], x, y); cell_solid(x, y, 2, 3)
    for (x, y) in L.BLOSSOMS: obj(assets['blossom'], x, y); cell_solid(x, y, 2, 3)
    # Buildings.
    doors = {}
    for b in L.BUILDINGS:
        c = assets[b['style']]; w, h = L.SIZE[b['style']]
        obj(c, b['x'], b['y']); cell_solid(b['x'], b['y'], w, h)
        dx, dy = L.door_of(b); solid[dy, dx] = False; behavior[dy, dx] = MB_ANIMATED_DOOR; doors[b['name']] = (dx, dy)
        if b['style'] == 'mart':
            obj(assets['mart_sign'], b['x'] + 4, b['y'] + 1, sort=(b['y'] + 4) * 16 + 15); cell_solid(b['x'] + 4, b['y'] + 1, 2, 4)
    # Gardens: tulip beds ringed by a picket fence.
    for (x, y, w, h) in L.GARDENS:
        for yy in range(y, y + h):
            for xx in range(x, x + w): obj(assets['tulips0' if (yy - y) % 2 == 0 else 'tulips1'], xx, yy); cell_solid(xx, yy)
        for xx in range(x, x + w):
            obj(assets['fence_h'], xx, y - 1); obj(assets['fence_h'], xx, y + h); cell_solid(xx, y - 1); cell_solid(xx, y + h)
        for yy in range(y, y + h):
            obj(assets['fence_v'], x - 1, yy); obj(assets['fence_v'], x + w, yy, flip=True); cell_solid(x - 1, yy); cell_solid(x + w, yy)
        obj(assets['fence_corner'], x - 1, y + h); obj(assets['fence_corner'], x + w, y + h, flip=True)
        obj(assets['fence_corner'], x - 1, y - 1); obj(assets['fence_corner'], x + w, y - 1, flip=True)
        cell_solid(x - 1, y - 1); cell_solid(x + w, y - 1); cell_solid(x - 1, y + h); cell_solid(x + w, y + h)
    for (x, y) in L.PARK_PROPS['bench']: obj(assets['bench'], x, y); cell_solid(x, y)
    for (x, y) in L.PARK_PROPS['lamp']: obj(assets['lamp'], x, y - 1, sort=y * 16 + 15); cell_solid(x, y); mc.above[y - 1, x] = True
    for (x, y) in L.BUSHES: obj(assets['bush'], x, y - 1, sort=y * 16 + 15); cell_solid(x, y); mc.above[y - 1, x] = True
    for (x, y) in L.MAILBOXES: obj(assets['mailbox'], x, y - 1, sort=y * 16 + 15); cell_solid(x, y); mc.above[y - 1, x] = True
    for (name, x, y) in L.SIGNS:
        obj(assets['sign'], x, y - 1, sort=y * 16 + 15); cell_solid(x, y); behavior[y, x] = MB_SIGNPOST; mc.above[y - 1, x] = True
    # Waterfront: pier, boats, nets; lookout deck under the cliff.
    p = L.PIER
    for x in range(p['x0'], p['x1']):
        top = assets['rail_v'] if x == p['x0'] else assets['deck_n']
        bot = assets['rail_v'] if x == p['x0'] else assets['deck_s']
        obj(top, x, p['y']); obj(bot, x, p['y'] + 1)
        for yy in (p['y'], p['y'] + 1): solid[yy, x] = (x == p['x0']); behavior[yy, x] = 0
    for (x, y) in L.BOATS: obj(assets['boat'], x, y); cell_solid(x, y, 2, 2)
    for (x, y) in L.NETS: obj(assets['nets'], x, y); cell_solid(x, y, 2, 1)
    lk = L.LOOKOUT
    for x in range(lk['x'], lk['x'] + lk['w']):
        obj(assets['rail_h'], x, lk['y']); cell_solid(x, lk['y'])
        obj(assets['rail_v'] if x == lk['x'] else assets['deck_s'], x, lk['y'] + 1)
        solid[lk['y'] + 1, x] = (x == lk['x']); behavior[lk['y'] + 1, x] = 0
    obj(assets['bench'], lk['x'] + 2, lk['y'], sort=lk['y'] * 16 + 15.5)
    for (x, y) in L.SEA_ROCKS: obj(assets['sea_rock'], x, y); cell_solid(x, y, 2, 2)
    for (x, y) in L.SEA_ROCKS_SMALL: obj(assets['sea_rock_small'], x, y); cell_solid(x, y)
    for (x, y) in L.ROCKS: obj(assets['rock'], x, y); cell_solid(x, y, 2, 2)
    # Daisy patches on the park lawn and open grass.
    px0, py0, pw, ph = L.PETALS
    for y in range(py0, py0 + ph):
        for x in range(px0, px0 + pw - 1):
            if (x * 7 + y * 3) % 7 == 0 and cells[y, x] == G and not solid[y, x:x + 2].any() and not solid[max(y - 1, 0), x:x + 2].any():
                obj(assets['daisies'], x, y, sort=-1)
    for _, px, py, c, flip in sorted(objects, key=lambda o: (o[0], o[1])): mc.blit(c, px, py, flip)
    return dict(cells=cells, solid=solid, behavior=behavior, canvas=mc, doors=doors, W=Wd, H=Ht)

def compose_stub(assets, Wd, Ht, path_rect, side):
    """Route approach stubs: forest with one sand lane leaving the town edge."""
    cells = np.full((Ht, Wd), G, dtype=np.int8); solid = np.zeros((Ht, Wd), dtype=bool); behavior = np.zeros((Ht, Wd), dtype=np.uint8)
    mc = MapCanvas(Wd, Ht); objects = []
    x, y, w, h = path_rect; cells[y:y + h, x:x + w] = P
    lane = cells == P
    for j, yy in enumerate(range(-3, Ht, 2)):
        for xx in range(-2 + (j % 2), Wd, 2):
            if lane[max(yy, 0):yy + 3, max(xx, 0):xx + 2].any(): continue
            objects.append((yy * 16 + 47, xx * 16, yy * 16, assets['tree'], False))
    solid[:] = ~lane
    for _, px, py, c, flip in sorted(objects, key=lambda o: (o[0], o[1])): mc.blit(c, px, py, flip)
    return dict(cells=cells, solid=solid, behavior=behavior, canvas=mc, W=Wd, H=Ht)

# ----------------------------------------------------------------- packing

class Packer:
    """Two tile pools (primary 0-511, secondary 512-1023) and two metatile tables."""
    def __init__(self, palettes):
        self.palettes = palettes
        self.tiles = {'primary': [], 'secondary': []}
        self.lookup = {}
        self.blocks = {'primary': [], 'secondary': []}
        self.attrs = {'primary': [], 'secondary': []}
        self.block_lookup = {}
        self.conflicts = 0; self.conflict_cells = []
        self.tiles['primary'].append((0, np.zeros((8, 8), np.uint8)))   # tile 0 must stay blank: it is what an empty layer entry draws
    def pool_of(self, bank):
        return 'primary' if bank < 6 else 'secondary'
    def tile(self, bank, arr):
        for hf in (0, 1):
            for vf in (0, 1):
                a = arr[::-1] if vf else arr; a = a[:, ::-1] if hf else a
                key = (bank, a.tobytes())
                if key in self.lookup: return self.lookup[key] | (hf << 10) | (vf << 11)
        pool = self.pool_of(bank); base = 0 if pool == 'primary' else 512
        tid = base + len(self.tiles[pool])
        if len(self.tiles[pool]) >= 512:
            counts = Counter(b for b, _ in self.tiles[pool])
            raise SystemExit(f'{pool} tile budget exhausted; tiles per bank: {dict(counts)}')
        self.tiles[pool].append((bank, arr.copy())); self.lookup[(bank, arr.tobytes())] = tid; return tid
    def slice(self, bank_img, idx_img, cx, cy):
        """Four 8x8 tiles of one cell -> metatile entries (0 when empty), and whether the cell is fully opaque."""
        entries = []; opaque = True
        for q in range(4):
            x0, y0 = cx * 16 + (q % 2) * 8, cy * 16 + (q // 2) * 8
            bank = bank_img[y0:y0 + 8, x0:x0 + 8]; idx = idx_img[y0:y0 + 8, x0:x0 + 8].astype(np.int64)
            if (bank < 0).all(): entries.append(0); opaque = False; continue
            if (bank < 0).any(): opaque = False
            bks = [int(b) for b in np.unique(bank) if b >= 0]
            if len(bks) > 1:
                counts = {b: int((bank == b).sum()) for b in bks}; major = max(counts, key=counts.get); self.conflicts += 1
                self.conflict_cells.append((cx, cy, tuple(bks)))
                pal = np.array(self.palettes[major].gba()[1:])
                for b in bks:
                    if b == major: continue
                    src = np.array(self.palettes[b].gba()[1:])
                    for yy, xx in zip(*np.nonzero(bank == b)):
                        rgb = src[idx[yy, xx] - 1]; idx[yy, xx] = int(((pal - rgb) ** 2).sum(axis=1).argmin()) + 1
                bank = np.where(bank >= 0, major, -1)
            arr = np.where(bank >= 0, idx, 0).astype(np.uint8)
            b = bks[0] if len(bks) == 1 else major
            entries.append(self.tile(b, arr) | (b << 12))
        return entries, opaque
    def metatile(self, entries, attr):
        key = (tuple(entries), attr)
        if key in self.block_lookup: return self.block_lookup[key]
        pool = 'primary' if all((e & 1023) < 512 for e in entries) else 'secondary'
        base = 0 if pool == 'primary' else 512
        mid = base + len(self.blocks[pool]); assert len(self.blocks[pool]) < 512, f'{pool} metatile budget exhausted'
        self.blocks[pool].append(tuple(entries)); self.attrs[pool].append(attr); self.block_lookup[key] = mid; return mid

def grid_for(comp, packer, palettes):
    Wd, Ht, mc = comp['W'], comp['H'], comp['canvas']
    gimg, mat = ground.paint(comp['cells'])
    gbank, gidx = index_ground(gimg, mat, palettes)
    grid = []
    for y in range(Ht):
        for x in range(Wd):
            base, _ = packer.slice(gbank, gidx, x, y)
            entries, opaque = packer.slice(mc.bank, mc.idx, x, y)
            beh = int(comp['behavior'][y, x])
            if all(e == 0 for e in entries):
                mid = packer.metatile(base + [0, 0, 0, 0], beh)
            elif opaque and not mc.above[y, x]:
                mid = packer.metatile(entries + [0, 0, 0, 0], beh | COVERED)
            elif mc.above[y, x]:
                mid = packer.metatile(base + entries, beh | NORMAL)
            else:
                mid = packer.metatile(base + entries, beh | COVERED)
            grid.append(mid | (0x3 << 12) | (0xC00 if comp['solid'][y, x] else 0))
    return grid, gimg

# ----------------------------------------------------------------- engine writing

def write_pal(path, colors):
    path.write_text('JASC-PAL\n0100\n16\n' + '\n'.join(' '.join(map(str, c)) for c in colors) + '\n')

def write_tileset(game, kind, name, tiles, blocks, attrs, palettes, bank_range):
    folder = game / f'data/tilesets/{kind}/{name}'; folder.mkdir(parents=True, exist_ok=True)
    (folder / 'palettes').mkdir(exist_ok=True)
    for bank in range(16):
        pal = palettes.get(bank) if bank in bank_range else None
        write_pal(folder / 'palettes' / f'{bank:02}.pal', pal.gba() if pal else [(0, 0, 0)] * 16)
    n = max(len(tiles), 1); rows = (n + 15) // 16
    im = Image.new('P', (128, rows * 8), 0)
    grey = []
    for i in range(16): grey += [i * 16, i * 16, i * 16]
    im.putpalette(grey + [0] * (768 - len(grey)))
    px = im.load()
    for i, (bank, arr) in enumerate(tiles):
        for yy in range(8):
            for xx in range(8): px[(i % 16) * 8 + xx, (i // 16) * 8 + yy] = int(arr[yy, xx])
    im.save(folder / 'tiles.png', bits=4)
    (folder / 'metatiles.bin').write_bytes(b''.join(struct.pack('<8H', *b) for b in blocks))
    (folder / 'metatile_attributes.bin').write_bytes(struct.pack('<' + 'H' * len(attrs), *attrs))

def write_layout(game, layouts, name, grid, Wd, Ht, border):
    folder = game / f'data/layouts/{name}'; folder.mkdir(parents=True, exist_ok=True)
    (folder / 'map.bin').write_bytes(struct.pack('<' + 'H' * len(grid), *grid))
    (folder / 'border.bin').write_bytes(struct.pack('<4H', *border))
    for lay in layouts['layouts']:
        if lay['name'] == name + '_Layout': lay['width'] = Wd; lay['height'] = Ht

def door_frames(assets, b):
    """Three 16x32 frames of the door opening; returns a P-mode 16x96 image and the bank."""
    c = assets[b['style']]; w, h = L.SIZE[b['style']]
    col = L.DOOR_COLUMN[b['style']] * 16; y0 = (h - 2) * 16
    closed = c.px[y0:y0 + 32, col:col + 16].copy(); pal = c.pal
    rgb = np.array(pal.gba()); dark = int(np.argmin(rgb[1:].sum(1)) + 1)
    sliding = b['style'] in ('center', 'mart')
    # Door leaf: the dominant colour family of the lower cell's centre.
    core = closed[20:30, 4:12]; leaf_idx = Counter(core.ravel().tolist()).most_common(1)[0][0]
    leaf_rgb = rgb[leaf_idx]
    near = [i for i in range(1, 16) if i in pal.by_slot and ((rgb[i] - leaf_rgb) ** 2).sum() < 40 ** 2]
    leaf = np.isin(closed, near); leaf[:12, :] = False; ys, xs = np.nonzero(leaf)
    if len(ys) == 0: ys, xs = np.array([18, 30]), np.array([3, 13])
    ya, yb, xa, xb = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    frames = []
    for k, amount in enumerate((1, 2, 3)):
        f = closed.copy(); block = closed[ya:yb, xa:xb].copy(); wd = xb - xa
        if sliding:
            half = wd // 2; shift = (half * amount) // 3
            f[ya:yb, xa:xb] = dark
            lw = half - shift; rw = (wd - half) - shift
            if lw > 0: f[ya:yb, xa:xa + lw] = block[:, shift:shift + lw]
            if rw > 0: f[ya:yb, xb - rw:xb] = block[:, half:half + rw]
        else:
            keep = wd - (wd * amount) // 3
            f[ya:yb, xa:xb] = dark
            if keep > 0:
                cols = np.linspace(0, wd - 1, keep).astype(int); f[ya:yb, xa:xa + keep] = block[:, cols]
        frames.append(f)
    strip = np.concatenate(frames, axis=0)
    im = Image.fromarray(strip.astype(np.uint8)).convert('P') if False else Image.fromarray(strip.astype(np.uint8), 'P')
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
    ng = game / 'src/new_game.c'; s = ng.read_text()
    s = re.sub(r'MAP_NUM\(MAP_CHERRYGROVE_CITY\), WARP_ID_NONE, \d+, \d+', f'MAP_NUM(MAP_CHERRYGROVE_CITY), WARP_ID_NONE, {L.SPAWN[0]}, {L.SPAWN[1]}', s)
    ng.write_text(s)

def write_headers(game):
    """The primary tileset is our own now: no General tile animation may write over it."""
    h = game / 'src/data/tilesets/headers.h'; s = h.read_text()
    s2 = re.sub(r'(gTileset_CherrygrovePrimary = \{[^}]*?\.callback = )InitTilesetAnim_General', r'\1NULL', s)
    if s2 != s: h.write_text(s2)

def render_preview(game, grid, Wd, Ht, path):
    t = Tileset(game, 'cherrygrove', 'cherrygrove'); t.map_image(grid, Wd).save(path)

def main():
    game = Path(sys.argv[1]).resolve(); assert game != ROOT / 'game' and (game / '.git').is_dir()
    OUT.mkdir(parents=True, exist_ok=True)
    assets, palettes = build_assets()
    packer = Packer(palettes)
    town = compose_town(assets); grid, gimg = grid_for(town, packer, palettes)
    Image.fromarray(gimg).save(OUT / 'evidence' / 'ground-layer.png') if (OUT / 'evidence').is_dir() else None
    # Border: dense canopy from a small forest composition.
    forest = compose_stub(assets, 4, 6, (0, 0, 0, 0), 'up'); fgrid, _ = grid_for(forest, packer, palettes)
    border = [fgrid[2 * 4 + 1] & 1023, fgrid[2 * 4 + 2] & 1023, fgrid[3 * 4 + 1] & 1023, fgrid[3 * 4 + 2] & 1023]
    border = [b | 0x3c00 for b in border]
    layouts = json.loads((game / 'data/layouts/layouts.json').read_text())
    write_layout(game, layouts, 'CherrygroveCity', grid, L.W, L.H, border)
    r30 = compose_stub(assets, L.W, 12, (L.NORTH_EXIT[0], 0, L.NORTH_EXIT[1] - L.NORTH_EXIT[0], 12), 'up')
    g30, _ = grid_for(r30, packer, palettes); write_layout(game, layouts, 'CherrygroveRoute30Approach', g30, L.W, 12, border)
    r29 = compose_stub(assets, 16, L.H, (0, L.EAST_EXIT[0], 16, L.EAST_EXIT[1] - L.EAST_EXIT[0]), 'right')
    g29, _ = grid_for(r29, packer, palettes); write_layout(game, layouts, 'CherrygroveRoute29Approach', g29, 16, L.H, border)
    (game / 'data/layouts/layouts.json').write_text(json.dumps(layouts, indent=2) + '\n')
    write_tileset(game, 'primary', 'cherrygrove', packer.tiles['primary'], packer.blocks['primary'], packer.attrs['primary'], palettes, range(0, 6))
    write_tileset(game, 'secondary', 'cherrygrove', packer.tiles['secondary'], packer.blocks['secondary'], packer.attrs['secondary'], palettes, range(6, 13))
    write_headers(game)
    write_events(game, town, grid)
    doors = write_doors(game, assets, town, grid)
    render_preview(game, grid, L.W, L.H, OUT / 'town-overview.png')
    render_preview(game, g30, L.W, 12, OUT / 'route30-stub.png'); render_preview(game, g29, 16, L.H, OUT / 'route29-stub.png')
    report = dict(width=L.W, height=L.H, primary_tiles=len(packer.tiles['primary']), primary_metatiles=len(packer.blocks['primary']),
                  secondary_tiles=len(packer.tiles['secondary']), secondary_metatiles=len(packer.blocks['secondary']), bank_conflict_tiles=packer.conflicts,
                  tiles_per_bank={str(k): v for k, v in sorted(Counter(b for pool in packer.tiles.values() for b, _ in pool).items())},
                  doors=doors, spawn=L.SPAWN, buildings=[dict(b, door=L.door_of(b)) for b in L.BUILDINGS])
    (OUT / 'build-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('conflicts by bank pair:', Counter(c[2] for c in packer.conflict_cells).most_common(8))
    print('conflict cells sample:', sorted(set((c[0], c[1]) for c in packer.conflict_cells))[:40])
    print(json.dumps({k: v for k, v in report.items() if k not in ('buildings', 'doors')}, indent=1))

if __name__ == '__main__':
    main()
