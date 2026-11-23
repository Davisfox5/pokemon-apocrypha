#!/usr/bin/env python3
"""Hidden Grotto art for Johto: three interior layouts and the big-tree entrance, drawn with
Cherrygrove's tree (the Johto standard) and packed into one secondary tileset.

    python3 tools/gba/grottoes/johto_art.py extract ENGINE   copy the tree stamps out of CherrygroveCity
    python3 tools/gba/grottoes/johto_art.py build ENGINE     write the tileset, layouts and previews
    python3 tools/gba/grottoes/johto_art.py check ENGINE     rebuild in memory and compare with ENGINE

ENGINE is a pokeemerald-expansion checkout on the `apocrypha` branch.

How the art is made (nothing is redrawn by hand except the hollow's shading):
  * Stamps. Cherrygrove's green and pink trees are 2x3 cells; `extract` copies them pixel for pixel
    out of CherrygroveCity (both layers, minus the grass under them) into gba/art/hidden-grottoes/.
  * Ground. Walkable ground is CherrygrovePrimary's own grass metatiles (0x033 plain, 0x034/0x027
    tufts). Flower beds are its 0x0C5 flowers.
  * Layouts. Each map is a character grid (LAYOUTS below). '#'/'%' cells are forest and get filled
    with green/pink trees, densely: rows two cells apart, every other row shifted one cell, so each
    row's crowns cover the trunks of the row behind and no grass shows through. Any cell still bare
    gets an extra tree that fits inside the forest. The grid is padded with forest so the camera
    never reaches the map edge.
  * Layers. Trees and flowers sit on the metatile's top layer over grass (COVERED, both under the
    player), as in Cherrygrove. In walkable cells, any tree pixels go above the player (NORMAL).
  * Packing. Every 8x8 tile is matched against CherrygrovePrimary (any flip, any of its palettes)
    first; only new tiles go into the secondary tileset `hidden_grotto`, with new palettes in 6-12.

Entrance (ENTRANCES, shown on the TestWoods layout): no gap. Two trees of a forest wall stand
side by side as usual; only the background showing between their sides (grass and shadow) turns
dark, deepest at the seam. The two trunk-row cells at the seam are the entrance (MB_NON_ANIMATED_DOOR,
passable): the player walks north into either one.
"""
from __future__ import annotations
import hashlib, json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'tools/gba/maps'))
from tiles import Tileset  # noqa: E402

ART = ROOT / 'gba/art/hidden-grottoes'
TS_DIR = 'data/tilesets/secondary/hidden_grotto'
PRIMARY = 'cherrygrove'
GRASS, TUFT_A, TUFT_B, FLOWERS = 0x033, 0x034, 0x027, 0x0C5
NORMAL, COVERED = 0, 1
PASS, BLOCK = 0x3000, 0x3400            # elevation 3; collision bit for blocked cells
PADX, PADY = 8, 6
SHADOW = (64, 136, 104)
DARK = [(64, 56, 40), (64, 64, 40), (72, 72, 48), (80, 88, 40)]

# Stamp sources in CherrygroveCity (top-left cell of a 2x3 tree). Pinned by hash in `check`.
STAMPS = {'green': (48, 26), 'pink': (48, 0)}

# Legend: '#' green forest, '%' pink forest, '.' grass, 'f' flower bed (walkable),
# 'O' grotto content (grass), 'W' arrival warp (grass), 'X' exit trigger (grass, shaded),
# 'A'/'B' fixed trees (each a 2x3 block of one letter; alternate letters for neighbours).
LAYOUTS = {
    # B2W2's hollow: a round clearing ringed by trees, content in the middle, way out to the south.
    'HiddenGrotto': [
        "################",
        "######....######",
        "####........####",
        "###..........###",
        "##..f......f..##",
        "##............##",
        "##.....O......##",
        "##............##",
        "###..........###",
        "####.f....f.####",
        "######....######",
        "#######..#######",
        "#######W.#######",
        "#######XX#######",
    ],
    # Spring version: pink trees ring the clearing and one stands behind the content.
    'HiddenGrottoBlossom': [
        "################",
        "#####%%%%%%#####",
        "####%%....%%####",
        "###%...%%...%###",
        "##%....%%....%##",
        "##%.f..%%..f.%##",
        "##%....O.....%##",
        "##%..f....f..%##",
        "###%........%###",
        "####%%....%%####",
        "######%..%######",
        "######%..%######",
        "#######W.#######",
        "#######XX#######",
    ],
    # A path that bends through the woods before it opens into a small clearing.
    'HiddenGrottoWinding': [
        "################",
        "################",
        "###......#######",
        "##..f.....######",
        "##...O.....#####",
        "##.........#####",
        "###.f.....######",
        "#####.....######",
        "######....######",
        "######.....#####",
        "#######....#####",
        "#######...######",
        "#######W.#######",
        "#######XX#######",
    ],
    # Test field with a grotto entrance in its forest wall (the entrance piece in context).
    # Test field: a forest wall with three grotto entrances (ENTRANCES), one per interior.
    'HiddenGrottoTestWoods': [
        "##############################",
        "##############################",
        "##############################",
        "AABBAABBAABBAABBAABBAABBAABBAA",
        "AABBAABBAABBAABBAABBAABBAABBAA",
        "AABBAABBAABBAABBAABBAABBAABBAA",
        "..............................",
        "..............................",
        "..............................",
        "..............................",
        "..............................",
    ],
}
# Grass ground only (no pad of forest) on these sides of a layout.
OPEN_SIDES = {'HiddenGrottoTestWoods': {'bottom', 'left', 'right'}}
# Grotto entrances: the left of the two trunk-row cells where two trees of a wall meet (grid coords).
ENTRANCES = {'HiddenGrottoTestWoods': [(5, 5), (15, 5), (25, 5)]}
WALK = set('.fOWX')


# --------------------------------------------------------------------------- engine art
class Engine:
    def __init__(self, path):
        self.root = Path(path)
        self.t = Tileset(self.root, secondary='cherrygrove', primary=PRIMARY)
        self.ptiles = [np.array(x, np.uint8).reshape(8, 8) & 15 for x in self.t.tiles[0]]
        self.ppals = [[tuple(int(v) for v in c) for c in p] for p in self.t.pals[0][:6]]

    def entries(self, mid):
        return self.t.blocks[mid >= 512][mid % 512]

    def tile_rgba(self, e):
        """RGBA of one metatile entry (index 0 transparent)."""
        tid, b = e & 1023, e >> 12
        tl = self.t.tiles[tid >= 512]
        if tid % 512 >= len(tl):
            return np.zeros((8, 8, 4), np.uint8)
        px = np.array(tl[tid % 512], np.uint8).reshape(8, 8) & 15
        if e & 1024: px = px[:, ::-1]
        if e & 2048: px = px[::-1]
        pal = self.t.pals[b >= 6][b]
        out = np.zeros((8, 8, 4), np.uint8)
        for y in range(8):
            for x in range(8):
                if px[y, x]:
                    out[y, x] = tuple(pal[px[y, x]]) + (255,)
        return out

    def metatile(self, mid, objects_only=False):
        out = np.zeros((16, 16, 4), np.uint8)
        for layer in (0, 1):
            for q, e in enumerate(self.entries(mid)[layer * 4:layer * 4 + 4]):
                if objects_only and (e >> 12) == 0:
                    continue
                t = self.tile_rgba(e)
                sl = out[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
                m = t[..., 3] > 0
                sl[m] = t[m]
        return out


def cherrygrove_blocks(eng):
    lay = next(l for l in json.loads((eng.root / 'data/layouts/layouts.json').read_text())['layouts']
               if l['id'] == 'LAYOUT_CHERRYGROVE_CITY')
    w, h = lay['width'], lay['height']
    return w, struct.unpack(f'<{w*h}H', (eng.root / lay['blockdata_filepath']).read_bytes())


def extract(eng):
    w, v = cherrygrove_blocks(eng)
    ART.mkdir(parents=True, exist_ok=True)
    for name, (x0, y0) in STAMPS.items():
        a = np.zeros((48, 32, 4), np.uint8)
        for j in range(3):
            for i in range(2):
                a[j * 16:j * 16 + 16, i * 16:i * 16 + 16] = eng.metatile(v[(y0 + j) * w + x0 + i] & 1023, True)
        Image.fromarray(a).save(ART / f'tree_{name}.png')
        print('wrote', ART / f'tree_{name}.png')


def stamps():
    return {n: np.array(Image.open(ART / f'tree_{n}.png').convert('RGBA')) for n in STAMPS}


# --------------------------------------------------------------------------- composition
def pad(name):
    rows = LAYOUTS[name]
    w = len(rows[0])
    assert all(len(r) == w for r in rows), name
    sides = OPEN_SIDES.get(name, set())
    px = 0 if 'left' in sides else PADX
    qx = 0 if 'right' in sides else PADX
    py = PADY
    qy = 0 if 'bottom' in sides else PADY
    grid = ['#' * (px + w + qx)] * py + ['#' * px + r + '#' * qx for r in rows] + ['#' * (px + w + qx)] * qy
    return grid, px, py


def place_trees(grid, name=''):
    """Tree positions (x, y, kind) covering every forest cell, Cherrygrove's 2x3 lattice first."""
    h, w = len(grid), len(grid[0])
    forest = lambda x, y: not (0 <= x < w and 0 <= y < h) or grid[y][x] in '#%AB'
    fixed = lambda x, y: 0 <= x < w and 0 <= y < h and grid[y][x] in 'AB'
    def kind_at(x, y):
        cells = [grid[y + j][x + i] for j in range(3) for i in range(2) if 0 <= x + i < w and 0 <= y + j < h]
        return 'pink' if '%' in cells else 'green'
    # A tree may stand behind a fixed tree (its lower rows hidden by it), never in front of one.
    fits = lambda x, y: all(forest(x + i, y + j) and (j > 0 or not fixed(x + i, y + j)) for j in range(3) for i in range(2)) \
        and not any(fixed(x + i, y + j) and not fixed(x + i, y + j - 1) and j == 0 for j in range(3) for i in range(2))
    trees, covered = [], set()
    def add(x, y):
        trees.append((x, y, kind_at(x, y)))
        covered.update((x + i, y + j) for j in range(3) for i in range(2))
    # Fixed trees (a wall drawn tree by tree).
    for y in range(h):
        for x in range(w):
            if grid[y][x] in 'AB' and (y == 0 or grid[y - 1][x] != grid[y][x]) and (x == 0 or grid[y][x - 1] != grid[y][x]):
                trees.append((x, y, 'green_' + grid[y][x]))
                covered.update((x + i, y + j) for j in range(3) for i in range(2))
    # Dense woods: a row of trees every two cells, alternate rows shifted one cell. Pick the phase
    # that leaves the fewest bare forest cells.
    fixed_tops = {}
    for (fx, fy, _) in list(trees):
        for i in range(2):
            fixed_tops[fx + i] = min(fixed_tops.get(fx + i, h), fy)
    # Woods behind a fixed wall start two rows above it (their trunks hidden by its crowns).
    behind = lambda x, y: all(y <= fixed_tops.get(x + i, h + 9) - 2 for i in range(2))
    fixed_par = {(fy, fx % 2) for (fx, fy, _) in trees}
    def lattice(ox, oy):
        got, cov = [], set(covered)
        for y in range(oy - 4, h, 2):
            for x in range(ox - 2 + ((y - oy) // 2) % 2, w, 2):
                if fits(x, y) and behind(x, y):
                    got.append((x, y))
                    cov.update((x + i, y + j) for j in range(3) for i in range(2))
        bare = sum(1 for y in range(h) for x in range(w) if grid[y][x] in '#%' and (x, y) not in cov)
        # The row right behind a fixed wall sits half a tree over, as in the rest of the woods.
        aligned = sum(1 for x, y in got if (y + 2, x % 2) in fixed_par)
        staggered = sum(1 for x, y in got if (y + 2, 1 - x % 2) in fixed_par)
        return bare, aligned - staggered, got
    *_, got = min((lattice(ox, oy) for oy in range(2) for ox in range(2)), key=lambda r: r[:2])
    for x, y in got:
        add(x, y)
    for y in range(h):
        for x in range(w):
            if forest(x, y) and grid[y][x] in '#%' and (x, y) not in covered:
                best = None
                for dy in (0, -1, -2):
                    for dx in (0, -1):
                        if fits(x + dx, y + dy) and behind(x + dx, y + dy):
                            overlap = sum((x + dx + i, y + dy + j) in covered for j in range(3) for i in range(2))
                            if best is None or overlap < best[0]:
                                best = (overlap, x + dx, y + dy)
                if best is None:
                    raise SystemExit(f'{name}: forest cell ({x},{y}) cannot hold a 2x3 tree; widen the forest there')
                add(best[1], best[2])
    trees.sort(key=lambda t: (t[1], t[0]))
    return trees


def compose(name, eng, st):
    grid, px, py = pad(name)
    h, w = len(grid), len(grid[0])
    trees = place_trees(grid, name)
    ground = np.zeros((h * 16, w * 16, 4), np.uint8)
    ground_mid = {}
    for y in range(h):
        for x in range(w):
            r = (x * 7 + y * 13) % 11
            mid = TUFT_A if (grid[y][x] in '.O' and r == 0) else TUFT_B if (grid[y][x] in '.O' and r == 5) else GRASS
            ground_mid[(x, y)] = mid
            ground[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = eng.metatile(mid)
    canopy = np.zeros_like(ground)       # tree pixels (above the player in walkable cells)
    under = np.zeros_like(ground)        # shadows, flowers, hollow: always under the player
    tree_mask = np.zeros(ground.shape[:2], bool)
    for x, y, kind in trees:
        s = st[kind.split('_')[0]]
        ox, oy = x * 16, y * 16
        for j in range(48):
            for i in range(32):
                X, Y = ox + i, oy + j
                if s[j, i, 3] and 0 <= X < w * 16 and 0 <= Y < h * 16:
                    c = tuple(int(v) for v in s[j, i, :3])
                    if c == SHADOW and tree_mask[Y, X]:
                        continue                 # a shadow never covers another tree
                    canopy[Y, X] = tuple(c) + (255,)
                    tree_mask[Y, X] = c != SHADOW
    flowers = eng.metatile(FLOWERS, True)
    for y in range(h):
        for x in range(w):
            ch = grid[y][x]
            if ch == 'f':
                sl = under[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
                m = flowers[..., 3] > 0
                sl[m] = flowers[m]
            elif ch == 'X':
                shade(under, x, y, ch, grid)
    entrances = [(ex + px, ey + py) for ex, ey in ENTRANCES.get(name, [])]
    for ex, ey in entrances:
        entrance(canopy, tree_mask, ex, ey)
    # Shadows that landed on walkable cells stay under the player.
    walk = np.zeros(ground.shape[:2], bool)
    for y in range(h):
        for x in range(w):
            if grid[y][x] in WALK:
                walk[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = True
    sh = (canopy[..., 3] > 0) & ~tree_mask & walk
    under[sh] = canopy[sh]
    canopy[sh] = 0
    return dict(grid=grid, w=w, h=h, px=px, py=py, ground=ground, ground_mid=ground_mid,
                under=under, canopy=canopy, trees=trees, entrances=entrances)


def entrance(canopy, tree_mask, ex, ey):
    """Darken the background between two trees' sides at the seam right of cell ex, over the
    trees' three rows (ey is the trunk row). Tree pixels are untouched; only the grass and shadow
    showing between the trees change, darkest at the seam and at the bottom."""
    bayer = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
    seam = ex * 16 + 16
    for Y in range((ey - 2) * 16, ey * 16 + 16):
        up = (ey * 16 + 16 - Y) / 48.0                 # 0 at the bottom of the trunk row, 1 at the top
        for X in range(ex * 16, ex * 16 + 32):
            if tree_mask[Y, X]:
                continue
            low = max(0.0, (Y - (ey * 16 + 6)) / 10.0)  # fade out over the trunk row's lower part
            d = 1.0 - abs(X + 0.5 - seam) / 12.0 - up * 0.3 - low * 0.7
            b = bayer[Y % 4, X % 4]
            if d > 0.62:
                col = DARK[0]
            elif d > 0.5:
                col = DARK[0] if b < (d - 0.5) / 0.12 else DARK[2]
            elif d > 0.36:
                col = DARK[2]
            elif d > 0.22:
                col = DARK[2] if b < (d - 0.22) / 0.14 else SHADOW
            elif d > 0.05:
                if canopy[Y, X, 3] == 0 and b >= (d - 0.05) / 0.17:
                    continue
                col = SHADOW
            else:
                continue
            canopy[Y, X] = col + (255,)


def shade(under, x, y, ch, grid):
    """Exit row X: the forest's shadow creeping onto the last row (ordered dither)."""
    bayer = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
    for j in range(16):
        for i in range(16):
            if bayer[j % 4, i % 4] < max(0.0, (j - 6) / 14.0):
                under[y * 16 + j, x * 16 + i] = SHADOW + (255,)


# --------------------------------------------------------------------------- packing
def flips(ix):
    return [(0, ix), (1, ix[:, ::-1]), (2, ix[::-1]), (3, ix[::-1, ::-1])]


class Packer:
    def __init__(self, eng):
        self.eng = eng
        self.pals = [list(p) for p in eng.ppals]          # 0-5 fixed
        self.sec = []                                      # palettes 6.. (lists of colours, [0] unused)
        self.tiles = []                                    # secondary tiles (8x8 index arrays)
        self.index = {}
        for i, ix in enumerate(eng.ptiles):
            for f, v in flips(ix):
                self.index.setdefault(v.tobytes(), (i, f))
        self.metatiles, self.attrs, self.mindex = [], [], {}

    def palette_for(self, colors):
        for b, p in enumerate(self.pals):
            if colors <= set(p[1:]):
                return b
        for k, p in enumerate(self.sec):
            if colors <= set(p[1:]):
                return 6 + k
        best = None
        for k, p in enumerate(self.sec):
            new = colors - set(p[1:])
            if len(p) - 1 + len(new) <= 15 and (best is None or len(new) < best[0]):
                best = (len(new), k)
        if best is not None:
            p = self.sec[best[1]]
            p += sorted(colors - set(p[1:]))
            return 6 + best[1]
        if len(self.sec) >= 7 or len(colors) > 15:
            raise SystemExit(f'out of palettes for a tile with {len(colors)} colours')
        self.sec.append([(0, 0, 0)] + sorted(colors))
        return 6 + len(self.sec) - 1

    def tile(self, rgba, opaque):
        a = rgba[..., 3] > 0
        if not a.any() and not opaque:
            return 0
        if opaque and not a.all():
            raise SystemExit('internal: bottom-layer tile has holes')
        colors = {tuple(int(v) for v in c) for c in rgba[a][:, :3]}
        b = self.palette_for(colors)
        pal = self.pals[b] if b < 6 else self.sec[b - 6]
        lut = {c: pal.index(c, 1) for c in colors}
        ix = np.zeros((8, 8), np.uint8)
        for y in range(8):
            for x in range(8):
                if a[y, x]:
                    ix[y, x] = lut[tuple(int(v) for v in rgba[y, x, :3])]
        key = ix.tobytes()
        if key not in self.index:
            n = 512 + len(self.tiles)
            self.tiles.append(ix)
            for f, v in flips(ix):
                self.index.setdefault(v.tobytes(), (n, f))
        tid, f = self.index[key]
        return tid | (f << 10) | (b << 12)

    def metatile(self, bottom, top, layer, behavior):
        ents = []
        for img, opaque in ((bottom, True), (top, False)):
            for q in range(4):
                ents.append(self.tile(img[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8], opaque))
        attr = behavior | (layer << 12)
        key = (tuple(ents), attr)
        if key not in self.mindex:
            self.mindex[key] = 512 + len(self.metatiles)
            self.metatiles.append(ents)
            self.attrs.append(attr)
        return self.mindex[key]


def behaviors(root):
    import re
    names = re.findall(r'^\s+(MB_[A-Z0-9_]+),', (root / 'include/constants/metatile_behaviors.h').read_text(), re.M)
    return {n: i for i, n in enumerate(names)}


def build_all(eng):
    st = stamps()
    mb = behaviors(eng.root)
    pk = Packer(eng)
    maps = {}
    for name in LAYOUTS:
        c = compose(name, eng, st)
        grid, w, h = c['grid'], c['w'], c['h']
        blocks = []
        for y in range(h):
            for x in range(w):
                sl = np.s_[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
                ch = grid[y][x]
                under, canopy, ground = c['under'][sl], c['canopy'][sl], c['ground'][sl]
                walk = ch in WALK
                door = any((x, y) in ((ex, ey), (ex + 1, ey)) for ex, ey in c['entrances'])
                beh = mb['MB_NON_ANIMATED_DOOR'] if door else mb['MB_NORMAL']
                coll = PASS if walk or door else BLOCK
                if not under[..., 3].any() and not canopy[..., 3].any():
                    blocks.append(c['ground_mid'][(x, y)] | coll)       # stock CherrygrovePrimary grass
                    continue
                objects = canopy.copy()
                m = under[..., 3] > 0
                if walk and canopy[..., 3].any():
                    # Canopy over a walkable cell: shadows/hollow flattened into the ground, tree on top.
                    flat = ground.copy()
                    flat[m] = under[m]
                    mid = pk.metatile(flat, canopy, NORMAL, beh)
                else:
                    objects[m & ~(objects[..., 3] > 0)] = under[m & ~(objects[..., 3] > 0)]
                    mid = pk.metatile(ground, objects, COVERED, beh)
                blocks.append(mid | coll)
        maps[name] = dict(c, blocks=blocks)
    return pk, maps


def preview(eng, pk, c, scale=1):
    """Render a map exactly from the packed data (proves the pack is lossless)."""
    w, h = c['w'], c['h']
    out = np.zeros((h * 16, w * 16, 3), np.uint8)
    def ent_rgba(e):
        tid, f, b = e & 1023, (e >> 10) & 3, e >> 12
        ix = eng.ptiles[tid] if tid < 512 else pk.tiles[tid - 512]
        if f & 1: ix = ix[:, ::-1]
        if f & 2: ix = ix[::-1]
        pal = pk.pals[b] if b < 6 else pk.sec[b - 6]
        rgba = np.zeros((8, 8, 4), np.uint8)
        for y in range(8):
            for x in range(8):
                if ix[y, x]:
                    rgba[y, x] = pal[ix[y, x]] + (255,)
        return rgba
    cache = {}
    for k, v in enumerate(c['blocks']):
        mid = v & 1023
        if mid not in cache:
            ents = eng.entries(mid) if mid < 512 else pk.metatiles[mid - 512]
            img = np.zeros((16, 16, 3), np.uint8)
            for layer in (0, 1):
                for q in range(4):
                    t = ent_rgba(ents[layer * 4 + q])
                    sl = img[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
                    m = t[..., 3] > 0
                    sl[m] = t[m][:, :3]
            cache[mid] = img
        x, y = k % w, k // w
        out[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = cache[mid]
    im = Image.fromarray(out)
    return im.resize((im.width * scale, im.height * scale), Image.NEAREST) if scale > 1 else im


def outputs(eng, pk, maps):
    """Every engine file this tool owns, as {relative path: bytes}."""
    files = {}
    tiles = pk.tiles + [np.zeros((8, 8), np.uint8)] * ((-len(pk.tiles)) % 16)
    rows = len(tiles) // 16
    im = Image.new('P', (128, rows * 8))
    im.putpalette([v for i in range(16) for v in (i * 16, i * 16, i * 16)] + [0] * (240 * 3))
    a = np.zeros((rows * 8, 128), np.uint8)
    for n, t in enumerate(tiles):
        a[(n // 16) * 8:(n // 16) * 8 + 8, (n % 16) * 8:(n % 16) * 8 + 8] = t
    im.putdata(a.ravel().tolist())
    import io
    buf = io.BytesIO(); im.save(buf, 'PNG', optimize=False); files[f'{TS_DIR}/tiles.png'] = buf.getvalue()
    for n in range(16):
        if 6 <= n < 6 + len(pk.sec):
            p = pk.sec[n - 6] + [(0, 0, 0)] * (16 - len(pk.sec[n - 6]))
        else:
            p = [(0, 0, 0)] * 16
        files[f'{TS_DIR}/palettes/{n:02}.pal'] = ('JASC-PAL\r\n0100\r\n16\r\n' +
                                                 ''.join(f'{r} {g} {b}\r\n' for r, g, b in p)).encode()
    files[f'{TS_DIR}/metatiles.bin'] = b''.join(struct.pack('<8H', *m) for m in pk.metatiles)
    files[f'{TS_DIR}/metatile_attributes.bin'] = struct.pack(f'<{len(pk.attrs)}H', *pk.attrs)
    for name, c in maps.items():
        files[f'data/layouts/{name}/map.bin'] = struct.pack(f'<{len(c["blocks"])}H', *c['blocks'])
        # Border: one Cherrygrove-lattice tree's worth of forest is 2x3, so the 2x2 border is the tree's
        # top-left/top-right and middle cells; the maps are padded so it is never on screen.
        w = c['w']
        border = [GRASS] * 4 if name in OPEN_SIDES else [c['blocks'][r * w + q] for r in (0, 1) for q in (0, 1)]
        files[f'data/layouts/{name}/border.bin'] = struct.pack('<4H', *border)
    return files


def layout_events(name, c):
    """Cell positions (map coordinates) of the special characters, for map.json."""
    found = {}
    for y, row in enumerate(c['grid']):
        for x, ch in enumerate(row):
            if ch in 'OWX':
                found.setdefault(ch, []).append((x, y))
    if c['entrances']:
        found['E'] = c['entrances']
    return found


def main(argv):
    if len(argv) < 3 or argv[1] not in ('extract', 'build', 'check'):
        print(__doc__); return 2
    eng = Engine(argv[2])
    if argv[1] == 'extract':
        extract(eng); return 0
    pk, maps = build_all(eng)
    files = outputs(eng, pk, maps)
    print(f'secondary tiles {len(pk.tiles)}/496, metatiles {len(pk.metatiles)}/512, palettes {len(pk.sec)}/7')
    for name, c in maps.items():
        ev = layout_events(name, c)
        print(f'{name}: {c["w"]}x{c["h"]} trees {len(c["trees"])} ' + ' '.join(f'{k}={v}' for k, v in sorted(ev.items())))
    if argv[1] == 'build':
        for rel, data in files.items():
            p = eng.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        out = ROOT / 'gba/evidence/hidden-grottoes'
        out.mkdir(parents=True, exist_ok=True)
        for name, c in maps.items():
            preview(eng, pk, c).save(out / f'layout-{name}.png')
        print('wrote', len(files), 'engine files and previews in', out)
        return 0
    bad = [rel for rel, data in files.items() if not (eng.root / rel).exists() or (eng.root / rel).read_bytes() != data]
    if bad:
        print('ERROR out of date: ' + ', '.join(bad)); return 1
    print('ok: tileset and layouts match the builder')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
