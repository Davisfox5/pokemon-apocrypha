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
    B['FLOWERS'] = (banks.Bank(4, 'FLOWERS', 'primary').add('tulips', hgss.tulips()).add('daisies', hgss.daisies())
                    .add('bush', hgss.bush()).add('fence_h', hgss.fence_h()).add('fence_v', hgss.fence_v()).add('fence_corner', hgss.fence_corner())
                    .keep((232, 232, 240), (200, 200, 208), (152, 152, 168)))
    B['ROCKS'] = banks.Bank(5, 'ROCKS', 'primary').add('sea_rock', hgss.sea_rock()).add('rock', hgss.rock())
    B['CLIFF'].add('cliff_end', hgss.cliff_end())
    ha, hb = hgss.house_a(), hgss.house_b()
    B['HOUSE'] = banks.Bank(6, 'HOUSE', 'secondary').add('house', ha).add('gable', hb).keep(*hgss.dominant(ha, (40, 58, 14, 14), 2))
    c = hgss.center()
    B['CENTER'] = banks.Bank(8, 'CENTER', 'secondary').add('center', c).keep(*hgss.dominant(c, (12, 60, 20, 6), 1), *hgss.dominant(c, (40, 80, 16, 12), 1))
    m = hgss.mart()
    B['MART'] = banks.Bank(9, 'MART', 'secondary').add('mart', m).add('mart_sign', hgss.mart_sign()).keep(*hgss.dominant(m, (50, 48, 16, 12), 1))
    B['WOOD'] = (banks.Bank(11, 'WOOD', 'secondary').add('pier', hgss.pier(L.PIER['x1'] - L.PIER['x0'])).add('boat', hgss.boat())
                 .add('sign', hgss.signpost()).add('mailbox', hgss.mailbox()))
    for k, f in art.ASSETS.items():
        if k in ('bench', 'lamp'): B['WOOD'].add(k, f().to_rgba())
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
    palettes = {b.bank: b.palette for b in B.values()}
    palettes.update({7: pal_house2, 10: pal_blossom})
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
    claims = {}    # cell -> owner, to catch objects placed on top of each other
    warnings = []

    def claim(x, y, w, h, owner, soft=False):
        for yy in range(max(y, 0), min(y + h, Ht)):
            for xx in range(max(x, 0), min(x + w, Wd)):
                other = claims.get((xx, yy))
                if other and other != owner and not (other.startswith('forest') and owner.startswith('forest')) and not soft:
                    warnings.append(f'{owner} overlaps {other} at ({xx},{yy})')
                claims[(xx, yy)] = owner
    def cell_solid(x, y, w=1, h=1):
        solid[max(y, 0):y + h, max(x, 0):x + w] = True
    def obj(canvas, cx, cy, sort=None, flip=False, py=None):
        h = canvas.h; ypx = cy * 16 if py is None else py
        objects.append(((ypx + h - 1) if sort is None else sort, cx * 16, ypx, canvas, flip))

    # Sea, beach and cliff foot.
    for y in range(Ht):
        for x in range(Wd):
            if y >= L.SEA_TOP and x < L.shore(y): cells[y, x] = W; cell_solid(x, y)
            elif y >= L.SEA_TOP and x < L.sand_end(y): cells[y, x] = S
    for y in range(30, Ht):
        for x in range(0, 29): cells[y, x] = W; cell_solid(x, y)
    for x in range(L.CLIFF_X[0], L.CLIFF_CORNER + 2):
        cells[L.CLIFF_ROWS[1], x] = R if x < L.shore(L.SEA_TOP) else S
    # Paths.
    for (x, y, w, h) in L.LANES + [L.BATTLE_YARD]: cells[y:y + h, x:x + w] = P
    for y in range(Ht):
        for x in range(Wd):
            if cells[y, x] == S and not solid[y, x]: behavior[y, x] = MB_SAND
    # Cliff band and its corner.
    cy0, cy1 = L.CLIFF_ROWS
    for x in range(L.CLIFF_X[0], L.CLIFF_X[1], 2):
        obj(assets['cliff'] if x < L.shore(L.SEA_TOP) - 1 else assets['cliff_sand'], x, cy0, sort=cy1 * 16 + 15); cell_solid(x, cy0, 2, cy1 - cy0 + 1); claim(x, cy0, 2, 4, 'cliff')
    corner = assets['cliff_end']; obj(corner, L.CLIFF_CORNER, cy0, sort=cy0 * 16 - 8 + corner.h - 1, py=cy0 * 16 - 8)
    for yy in range(corner.h // 16 + 1):
        for xx in range(corner.w // 16):
            y0 = cy0 * 16 - 8 + yy * 16; sub = corner.px[max(0, y0 - (cy0 * 16 - 8)):max(0, y0 - (cy0 * 16 - 8)) + 16, xx * 16:xx * 16 + 16]
            cyy = (y0) // 16
            if sub.size and (sub != 0).sum() > 8 and 0 <= cyy < Ht: cell_solid(L.CLIFF_CORNER + xx, cyy); claim(L.CLIFF_CORNER + xx, cyy, 1, 1, 'cliff-corner')
    # Forest bands: the HGSS lattice, one cell between rows, alternate rows offset one cell; crowns overhang the band
    # by one cell on odd rows unless that would cover a path.
    def tree_at(x, y, owner, kind='tree'):
        if x + 1 >= Wd or x < -1 or y >= Ht: return
        if (cells[max(y, 0):y + 3, max(x, 0):x + 2] == P).any(): return
        obj(assets[kind], x, y); cell_solid(x, y, 2, 3); claim(x, y, 2, 3, owner)
    def forest(x0, y0, x1, y1):
        for j, y in enumerate(range(y0, y1 + 1)):
            for x in range(x0 - (j % 2), x1 + 1, 2):
                if x + 1 > x1 + 1: continue
                tree_at(x, y, 'forest')
    for band in L.FOREST: forest(*band)
    for (x, y) in L.TREES: tree_at(x, y, f'tree{x},{y}')
    for (x, y) in L.BLOSSOMS: tree_at(x, y, f'blossom{x},{y}', 'blossom')
    # Buildings.
    doors = {}
    for b in L.BUILDINGS:
        c = assets[b['style']]; w, h = L.SIZE[b['style']]
        obj(c, b['x'], b['y']); cell_solid(b['x'], b['y'], w, h); claim(b['x'], b['y'], w, h, b['name'])
        dx, dy = L.door_of(b); solid[dy, dx] = False; behavior[dy, dx] = MB_ANIMATED_DOOR; doors[b['name']] = (dx, dy)
        if b['style'] == 'mart':
            obj(assets['mart_sign'], b['x'] + 4, b['y'] + 1, sort=(b['y'] + 4) * 16 + 15); cell_solid(b['x'] + 4, b['y'] + 1, 2, 4); claim(b['x'] + 4, b['y'] + 1, 2, 4, 'mart-sign', soft=True)
    # Tulip beds: pickets along the front, posts down both sides, open at the back (as in HGSS).
    for gi, (x, y, w, h) in enumerate(L.GARDENS):
        for yy in range(y, y + h):
            for xx in range(x, x + w): obj(assets['tulips'], xx, yy, sort=yy * 16 + 15, py=yy * 16 - 8); cell_solid(xx, yy)
        claim(x, y, w, h, f'garden{gi}')
        for xx in range(x, x + w): obj(assets['fence_h'], xx, y + h); cell_solid(xx, y + h)
        for yy in range(y, y + h):
            obj(assets['fence_v'], x - 1, yy); obj(assets['fence_v'], x + w, yy, flip=True); cell_solid(x - 1, yy); cell_solid(x + w, yy)
        obj(assets['fence_corner'], x - 1, y + h); obj(assets['fence_corner'], x + w, y + h, flip=True); cell_solid(x - 1, y + h); cell_solid(x + w, y + h)
        claim(x - 1, y, w + 2, h + 1, f'garden{gi}')
    for (x, y) in L.PARK_PROPS['bench']: obj(assets['bench'], x, y); cell_solid(x, y); claim(x, y, 1, 1, 'bench')
    for (x, y) in L.PARK_PROPS['lamp']: obj(assets['lamp'], x, y - 1, sort=y * 16 + 15); cell_solid(x, y); mc.above[y - 1, x] = True; claim(x, y - 1, 1, 2, 'lamp')
    for (x, y) in L.MAILBOXES: obj(assets['mailbox'], x, y - 1, sort=y * 16 + 15); cell_solid(x, y); mc.above[y - 1, x] = True; claim(x, y - 1, 1, 2, 'mailbox')
    for (name, x, y) in L.SIGNS:
        obj(assets['sign'], x, y - 1, sort=y * 16 + 15); cell_solid(x, y); behavior[y, x] = MB_SIGNPOST; mc.above[y - 1, x] = True; claim(x, y - 1, 2, 2, name, soft=True)
    # Waterfront: the plank pier and two boats.
    p = L.PIER
    obj(assets['pier'], p['x0'], p['y'])
    for x in range(p['x0'], p['x1']):
        for yy in (p['y'], p['y'] + 1): solid[yy, x] = False; behavior[yy, x] = 0
    claim(p['x0'], p['y'], p['x1'] - p['x0'], 2, 'pier')
    for (x, y) in L.BOATS: obj(assets['boat'], x, y); cell_solid(x, y, 2, 1); claim(x, y, 2, 1, 'boat')
    for (x, y) in L.SEA_ROCKS: obj(assets['sea_rock'], x, y); cell_solid(x, y, 2, 2); claim(x, y, 2, 2, 'sea-rock')
    for (x, y) in L.ROCKS: obj(assets['rock'], x, y); cell_solid(x, y + 1, 2, 2); claim(x, y, 2, 3, 'rock')
    # Daisy patches on the park lawn and open grass.
    px0, py0, pw, ph = L.PETALS
    for y in range(py0, py0 + ph):
        for x in range(px0, px0 + pw - 1):
            if (x * 7 + y * 3) % 7 == 0 and cells[y, x] == G and not solid[y, x:x + 2].any() and not solid[max(y - 1, 0), x:x + 2].any() and (x, y) not in claims and (x + 1, y) not in claims:
                obj(assets['daisies'], x, y, sort=-1)
    for _, px, py, c, flip in sorted(objects, key=lambda o: (o[0], o[1])): mc.blit(c, px, py, flip)
    for w in sorted(set(warnings)): print('WARNING:', w)
    return dict(cells=cells, solid=solid, behavior=behavior, canvas=mc, doors=doors, W=Wd, H=Ht)

def compose_stub(assets, Wd, Ht, path_rect, side):
    """Route approach stubs: forest with one sand lane leaving the town edge."""
    cells = np.full((Ht, Wd), G, dtype=np.int8); solid = np.zeros((Ht, Wd), dtype=bool); behavior = np.zeros((Ht, Wd), dtype=np.uint8)
    mc = MapCanvas(Wd, Ht); objects = []
    x, y, w, h = path_rect; cells[y:y + h, x:x + w] = P
    lane = cells == P
    for j, yy in enumerate(range(-3, Ht)):
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
        self.conflicts = 0; self.conflict_cells = []; self.first_pos = {}
        self.tiles['primary'].append((0, np.zeros((8, 8), np.uint8)))   # tile 0 must stay blank: it is what an empty layer entry draws
    def pool_of(self, bank):
        return 'primary' if bank < 6 else 'secondary'
    def tile(self, bank, arr, pos=None):
        for hf in (0, 1):
            for vf in (0, 1):
                if bank == 1 and (hf or vf): continue
                a = arr[::-1] if vf else arr; a = a[:, ::-1] if hf else a
                key = (bank, a.tobytes())
                if key in self.lookup: return self.lookup[key] | (hf << 10) | (vf << 11)
        pool = self.pool_of(bank); base = 0 if pool == 'primary' else 512
        tid = base + len(self.tiles[pool])
        if len(self.tiles[pool]) >= 512:
            counts = Counter(b for b, _ in self.tiles[pool])
            raise SystemExit(f'{pool} tile budget exhausted; tiles per bank: {dict(counts)}')
        self.tiles[pool].append((bank, arr.copy())); self.lookup[(bank, arr.tobytes())] = tid
        if pos is not None: self.first_pos[tid] = pos
        return tid
    def slice(self, bank_img, idx_img, cx, cy, ground_tag=None):
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
            entries.append(self.tile(b, arr, pos=(ground_tag, x0, y0) if ground_tag else None) | (b << 12))
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
            base, _ = packer.slice(gbank, gidx, x, y, ground_tag=comp.get('tag', 'stub'))
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
    comp['mat'] = mat
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

def sea_frames(n=8):
    """n 32x32 RGB sea textures: the HGSS base water in the render's tones with the sparkle layer drifting east."""
    base = hgss._texture('sea_un'); spark = hgss._texture('sea_on', 'sea_f02_pl')
    lum = lambda c: 0.3 * c[0] + 0.6 * c[1] + 0.1 * c[2]
    bsrc = sorted({tuple(int(v) for v in c[:3]) for c in base[base[..., 3] > 0]}, key=lum)
    ssrc = sorted({tuple(int(v) for v in c[:3]) for c in spark[spark[..., 3] > 0]}, key=lum)
    btones = [SEA_PAL[0], SEA_PAL[1], SEA_PAL[2], SEA_PAL[3], SEA_PAL[3]]; stones = [SEA_PAL[3], SEA_PAL[4], SEA_PAL[5], SEA_PAL[5], SEA_PAL[5]]
    b = np.zeros((32, 32, 3), np.uint8)
    for i, c in enumerate(bsrc): b[(base[..., :3] == c).all(-1)] = btones[min(i * len(btones) // max(len(bsrc), 1), len(btones) - 1)]
    frames = []
    for k in range(n):
        f = b.copy(); dx = (k * 32) // n
        for i, c in enumerate(ssrc):
            m = (spark[..., :3] == c).all(-1) & (spark[..., 3] > 0)
            m = np.roll(m, dx, axis=1); f[m] = stones[min(i * len(stones) // max(len(ssrc), 1), len(stones) - 1)]
        frames.append(f)
    return frames

def animate_sea(packer, town, palettes):
    """Find every primary sea tile, build its frames, and move those tiles to a contiguous block after tile 0."""
    mat = town['mat']; pal = np.array(palettes[1].gba()[1:], dtype=np.int32); frames = sea_frames()
    anim = {}
    for tid, (bank, arr) in enumerate(packer.tiles['primary']):
        if bank != 1 or tid not in packer.first_pos: continue
        tag, x0, y0 = packer.first_pos[tid]
        if tag != 'town': continue
        m = mat[y0:y0 + 8, x0:x0 + 8] == W
        if not m.any(): continue
        fr = []
        for f in frames:
            a = arr.copy(); rgb = f[np.arange(y0, y0 + 8)[:, None] % 32, np.arange(x0, x0 + 8)[None, :] % 32]
            idx = ((rgb.reshape(-1, 3)[:, None, :] - pal[None]) ** 2).sum(-1).argmin(1).reshape(8, 8) + 1
            a[m] = idx[m]; fr.append(a)
        if all((x == fr[0]).all() for x in fr): continue
        anim[tid] = fr
    order = [0] + sorted(anim) + [i for i in range(1, len(packer.tiles['primary'])) if i not in anim]
    remap = {old: new for new, old in enumerate(order)}
    packer.tiles['primary'] = [packer.tiles['primary'][i] for i in order]
    def fix(e):
        tid = e & 1023
        return (e & ~1023) | remap[tid] if tid < 512 else e
    for pool in ('primary', 'secondary'):
        packer.blocks[pool] = [tuple(fix(e) for e in b) for b in packer.blocks[pool]]
    n = len(anim)
    return [[anim[old][k] for old in sorted(anim)] for k in range(8)], 1, n

def write_sea_anim(game, frames, start, n):
    folder = game / 'data/tilesets/primary/cherrygrove/anim/sea'; folder.mkdir(parents=True, exist_ok=True)
    for k, tiles in enumerate(frames):
        rows = (n + 15) // 16; im = Image.new('P', (128, max(rows, 1) * 8), 0); grey = []
        for i in range(16): grey += [i * 16, i * 16, i * 16]
        im.putpalette(grey + [0] * (768 - len(grey))); px = im.load()
        for i, arr in enumerate(tiles):
            for yy in range(8):
                for xx in range(8): px[(i % 16) * 8 + xx, (i // 16) * 8 + yy] = int(arr[yy, xx])
        im.save(folder / f'{k}.png', bits=4)
    src = game / 'src/tileset_anims.c'; s = src.read_text()
    a, b = s.find('// Claude Cherrygrove sea'), s.find('// End Claude Cherrygrove sea\n')
    if a >= 0: s = s[:a] + s[b + len('// End Claude Cherrygrove sea\n'):]
    decl = ['// Claude Cherrygrove sea']
    decl += [f'const u16 gTilesetAnims_Cherrygrove_Sea_Frame{k}[] = INCGFX_U16("data/tilesets/primary/cherrygrove/anim/sea/{k}.png", ".4bpp");' for k in range(8)]
    decl.append('const u16 *const gTilesetAnims_Cherrygrove_Sea[] = {' + ', '.join(f'gTilesetAnims_Cherrygrove_Sea_Frame{k}' for k in range(8)) + '};')
    decl.append('static void TilesetAnim_CherrygrovePrimary(u16 timer);')
    decl.append('void InitTilesetAnim_CherrygrovePrimary(void)\n{\n    sPrimaryTilesetAnimCounter = 0;\n    sPrimaryTilesetAnimCounterMax = 256;\n    sPrimaryTilesetAnimCallback = TilesetAnim_CherrygrovePrimary;\n}')
    decl.append(f'static void TilesetAnim_CherrygrovePrimary(u16 timer)\n{{\n    if (timer % 16 == 1)\n        AppendTilesetAnimToBuffer(gTilesetAnims_Cherrygrove_Sea[(timer / 16) % 8], (u16 *)(BG_VRAM + TILE_OFFSET_4BPP({start})), {n} * TILE_SIZE_4BPP);\n}}')
    decl.append('// End Claude Cherrygrove sea')
    marker = 'void InitTilesetAnim_General(void)'
    assert marker in s; s = s.replace(marker, '\n'.join(decl) + '\n\n' + marker, 1); src.write_text(s)
    h = game / 'include/tileset_anims.h'; hs = h.read_text()
    if 'InitTilesetAnim_CherrygrovePrimary' not in hs:
        hs = hs.replace('void InitTilesetAnim_General(void);', 'void InitTilesetAnim_General(void);\nvoid InitTilesetAnim_CherrygrovePrimary(void);', 1); h.write_text(hs)

def write_headers(game):
    """The primary tileset is our own: its callback animates the sea tiles."""
    h = game / 'src/data/tilesets/headers.h'; s = h.read_text()
    s2 = re.sub(r'(gTileset_CherrygrovePrimary = \{[^}]*?\.callback = )(InitTilesetAnim_General|NULL)', r'\1InitTilesetAnim_CherrygrovePrimary', s)
    if s2 != s: h.write_text(s2)

def render_preview(game, grid, Wd, Ht, path):
    t = Tileset(game, 'cherrygrove', 'cherrygrove'); t.map_image(grid, Wd).save(path)

def main():
    game = Path(sys.argv[1]).resolve(); assert game != ROOT / 'game' and (game / '.git').is_dir()
    OUT.mkdir(parents=True, exist_ok=True)
    assets, palettes = build_assets()
    packer = Packer(palettes)
    town = compose_town(assets); town['tag'] = 'town'; grid, gimg = grid_for(town, packer, palettes)
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
    frames, start, n_anim = animate_sea(packer, town, palettes); write_sea_anim(game, frames, start, n_anim)
    write_tileset(game, 'primary', 'cherrygrove', packer.tiles['primary'], packer.blocks['primary'], packer.attrs['primary'], palettes, range(0, 6))
    write_tileset(game, 'secondary', 'cherrygrove', packer.tiles['secondary'], packer.blocks['secondary'], packer.attrs['secondary'], palettes, range(6, 13))
    write_headers(game)
    from claude_cherrygrove import gold_sprite; gold_colors = gold_sprite.main(game)
    write_events(game, town, grid)
    doors = write_doors(game, assets, town, grid)
    render_preview(game, grid, L.W, L.H, OUT / 'town-overview.png')
    render_preview(game, g30, L.W, 12, OUT / 'route30-stub.png'); render_preview(game, g29, 16, L.H, OUT / 'route29-stub.png')
    report = dict(width=L.W, height=L.H, primary_tiles=len(packer.tiles['primary']), primary_metatiles=len(packer.blocks['primary']),
                  secondary_tiles=len(packer.tiles['secondary']), secondary_metatiles=len(packer.blocks['secondary']), bank_conflict_tiles=packer.conflicts, animated_sea_tiles=n_anim, gold_sprite_colors=gold_colors,
                  tiles_per_bank={str(k): v for k, v in sorted(Counter(b for pool in packer.tiles.values() for b, _ in pool).items())},
                  doors=doors, spawn=L.SPAWN, buildings=[dict(b, door=L.door_of(b)) for b in L.BUILDINGS])
    (OUT / 'build-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('conflicts by bank pair:', Counter(c[2] for c in packer.conflict_cells).most_common(8))
    print('conflict cells sample:', sorted(set((c[0], c[1]) for c in packer.conflict_cells))[:40])
    print(json.dumps({k: v for k, v in report.items() if k not in ('buildings', 'doors')}, indent=1))

if __name__ == '__main__':
    main()
