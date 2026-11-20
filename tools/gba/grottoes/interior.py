#!/usr/bin/env python3
"""The shared Hidden Grotto interior: a round clearing ringed by Emerald trees, entered from the south.

    python3 tools/gba/grottoes/interior.py ENGINE [PREVIEW.png]

Writes data/layouts/HiddenGrotto/map.bin and border.bin in ENGINE (16x18, gTileset_General +
gTileset_Petalburg, stock metatiles only, so no tile or palette budget is used) and an optional
3x preview. The map's events (content object at 7,7; arrival warp at 7,15; exit triggers on row 16)
live in data/maps/HiddenGrotto/map.json and depend on this shape.

Trees follow Emerald's own stacking (Route 101): a tree is two rows, 0x1D4/0x1D5 over 0x1DC/0x1DD
when another tree stands below it or 0x1E4/0x1E5 when grass does; a tree with grass above gets the
0x1C6/0x1C7 crown-tip row, which stays walkable; side variants (0x1D6/0x1D7, 0x1E6/0x1E7,
0x1CE/0x1CF) show grass where the neighbouring tree is missing.
"""
from __future__ import annotations
import struct, sys
from pathlib import Path

GRASS, FLOWERS = 0x001, 0x004
W, H = 16, 18
# One character per 2x2 tree slot, rows 0-15; row 16-17 (lattice row 8) is trees except the path.
CLEARING = [
    "########",
    "###..###",
    "##....##",
    "#......#",
    "#......#",
    "##....##",
    "###..###",
    "###..###",
]
PATH_COLUMNS = (3, 4)
FLOWER_CELLS = [(4, 4), (11, 5), (2, 7), (13, 8), (4, 10), (11, 10)]
WALKABLE = {GRASS, FLOWERS, 0x1C6, 0x1C7, 0x1CE, 0x1CF}
SIDE = {0x1D4: 0x1D6, 0x1D5: 0x1D7, 0x1E4: 0x1E6, 0x1E5: 0x1E7, 0x1C6: 0x1CE, 0x1C7: 0x1CF}


def build():
    trees = {(i, j) for j, row in enumerate(CLEARING) for i, ch in enumerate(row) if ch == '#'}
    for i in range(-1, 9):                       # solid forest beyond the map edges
        trees |= {(i, -2), (i, -1)}
        trees |= {(i, j) for j in (8, 9) if i not in PATH_COLUMNS}
    for j in range(-2, 10):
        trees |= {(-1, j), (8, j)}
    role = {}
    for (i, j) in trees:
        for dx in (0, 1):
            x = 2 * i + dx
            cells = [(2 * j, 'U'), (2 * j + 1, 'L' if (i, j + 1) in trees else 'E')]
            if (i, j - 1) not in trees:
                cells.append((2 * j - 1, 'S'))
            for y, kind in cells:
                role.setdefault((x, y), set()).add(kind)
    grid = [[GRASS] * W for _ in range(H)]
    for (x, y), kinds in role.items():
        left = x % 2 == 0
        if 'U' in kinds:
            v = 0x1D4 if left else 0x1D5
        elif 'L' in kinds:
            v = 0x1DC if left else 0x1DD
        elif 'E' in kinds:
            v = 0x1E4 if left else 0x1E5
        else:
            v = 0x1C6 if left else 0x1C7
        if 'L' not in kinds:
            nb = (x - 1, y) if left else (x + 1, y)
            if role.get(nb) != kinds:
                v = SIDE.get(v, v)
        if 0 <= x < W and 0 <= y < H:
            grid[y][x] = v
    for x, y in FLOWER_CELLS:
        assert grid[y][x] == GRASS, (x, y)
        grid[y][x] = FLOWERS
    return grid


def write(engine: Path, grid):
    out = engine / 'data/layouts/HiddenGrotto'
    out.mkdir(parents=True, exist_ok=True)
    cells = [grid[y][x] | (0x3000 if grid[y][x] in WALKABLE else 0x3400) for y in range(H) for x in range(W)]
    (out / 'map.bin').write_bytes(struct.pack(f'<{W * H}H', *cells))
    (out / 'border.bin').write_bytes(struct.pack('<4H', *(m | 0x3400 for m in (0x1D4, 0x1D5, 0x1DC, 0x1DD))))


def preview(engine: Path, grid, path: Path):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'maps'))
    from tiles import Tileset
    from PIL import Image
    t = Tileset(engine)
    im = Image.new('RGB', (W * 16, H * 16))
    for y in range(H):
        for x in range(W):
            im.paste(t.render(grid[y][x]), (x * 16, y * 16))
    im.resize((W * 48, H * 48), Image.NEAREST).save(path)


if __name__ == '__main__':
    if len(sys.argv) not in (2, 3):
        print(__doc__); sys.exit(2)
    engine, grid = Path(sys.argv[1]), build()
    write(engine, grid)
    if len(sys.argv) == 3:
        preview(engine, grid, Path(sys.argv[2]))
