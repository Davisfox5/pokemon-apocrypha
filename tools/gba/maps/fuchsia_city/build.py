"""Fuchsia City (HGSS MAP_FUCHSIA) as a native FRLG-format map, square by square.

Layout authority: the decoded HGSS map (hgss_render.py output plus decoded walkability), 64 x 64 cells,
native = HGSS + (0, 0). Art: FireRed's own Fuchsia metatiles, gTileset_General_Frlg + the Fuchsia
secondary, placed as FireRed places them (approved sourcing plan, gba/maps/plans/FuchsiaCity.md).

    python3 tools/gba/maps/fuchsia_city/build.py ENGINE PHG REF_DIR OUT_DIR

REF_DIR is hgss_render.py's output. Writes OUT_DIR/map.bin (64 x 64 FRLG blocks), border.bin,
material.txt (the per-cell material grid), walk-diff.txt and preview.png.
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent), str(HERE.parents[2] / 'tools/hoennconv'), str(HERE.parents[2] / 'tools/regionport')]
import frlg_render as F  # noqa: E402

W = H = 64
SEC = 640                      # FRLG secondary metatile base
def S(i): return i             # ids below are written the way FRLG's map.bin stores them (secondary already +0x280)

# ------------------------------------------------------------------ FRLG pieces (ids as in FuchsiaCity_Frlg)
LAWN = {(0, 0): 0x9, (1, 0): 0x8, (0, 1): 0x11, (1, 1): 0x10}     # (x%2, y%2)
PALE = dict(nw=0xBD, n=0xBE, ne=0xBF, w=0xC5, c=0xC6, e=0xC7, sw=0xCD, s=0xCE, se=0xCF,
            inw=0xC3, ine=0xC4, isw=0xCB, ise=0xCC)
PATH = dict(nw=0xD3, n=0xD4, ne=0xD5, w=0xDB, c=0xDC, e=0xDD, sw=0xE3, s=0xE4, se=0xE5,
            inw=0x102, ine=0x103, isw=0x104, ise=0x105)
FLOWER = 0x4
SIGN = 0x2
FENCE = dict(h=0xE7, lend=0xEE, rend=0xEF, vl=0xF4, vr=0xF5, nw=0xEC, ne=0xED, sw=0xFC, se=0xFD,
             vl_end=0xF7, vr_end=0xF6)
ROCK = dict(nw=0x68, n=0x69, ne=0x6A, w=0x70, c=0x71, e=0x72, sw=0x78, s=0x79, se=0x7A,
            wall_w_top=0x83, wall_e_top=0x84, wall_w=0x85, wall_e=0x86, wall_sw=0x8D, wall_se=0x8E,
            ledge=0x87, ledge_l=0xB0, ledge_r=0xB1)

# ------------------------------------------------------------------ helpers
def load_frlg(engine, name):
    lay, grid = F.layout(engine, name)
    return np.array(grid, np.uint16).reshape(lay['height'], lay['width'])

def nine(region, x, y, P):
    """9-slice autotile for a boolean region (outside the map counts as inside, so edges run off-map)."""
    def r(dx, dy):
        xx, yy = x + dx, y + dy
        if not (0 <= xx < W and 0 <= yy < H): return True
        return bool(region[yy, xx])
    n, s, w_, e = r(0, -1), r(0, 1), r(-1, 0), r(1, 0)
    if not n and not w_: return P['nw']
    if not n and not e: return P['ne']
    if not s and not w_: return P['sw']
    if not s and not e: return P['se']
    if not n: return P['n']
    if not s: return P['s']
    if not w_: return P['w']
    if not e: return P['e']
    if not r(-1, -1): return P['inw']
    if not r(1, -1): return P['ine']
    if not r(-1, 1): return P['isw']
    if not r(1, 1): return P['ise']
    return P['c']

class Map:
    def __init__(self):
        self.mid = np.zeros((H, W), np.int32)
        self.blocked = np.zeros((H, W), bool)
        self.mat = np.full((H, W), '.', '<U1')
        self.locked = np.zeros((H, W), bool)       # cells a stamp owns; later passes leave them alone
        self.comps = {}                            # code -> (bottom-layer FRLG metatile, top-layer FRLG metatile)

    def comp(self, under, top):
        for k, v in self.comps.items():
            if v == (under, top): return k
        k = 0x1000 + len(self.comps); self.comps[k] = (under, top); return k

    def put(self, x, y, mid, blocked=None, mat=None, lock=True):
        self.mid[y, x] = mid
        if blocked is not None: self.blocked[y, x] = blocked
        if mat is not None: self.mat[y, x] = mat
        if lock: self.locked[y, x] = True

    def stamp(self, src, sx, sy, w, h, dx, dy, mat, frlg_bits=True):
        """Copy FRLG cells verbatim (metatile and collision)."""
        for j in range(h):
            for i in range(w):
                v = int(src[sy + j, sx + i])
                self.put(dx + i, dy + j, v & 0x3FF, bool((v >> 10) & 3), mat)

def build(engine, phg, ref):
    import map_gate
    walk = map_gate.hgss_walk(Path(phg), 'MAP_FUCHSIA') == 1            # True = walkable in HGSS
    cell = np.load(ref / 'cellmat.npy') if (ref / 'cellmat.npy').exists() else None
    names = [str(n) for n in np.load(ref / 'hgss-ground-materials.npz')['names']]
    if cell is None:
        mat = np.load(ref / 'hgss-ground-materials.npz')['material']
        cell = np.zeros((H, W), int)
        for y in range(H):
            for x in range(W):
                cell[y, x] = np.bincount(mat[y * 16:(y + 1) * 16, x * 16:(x + 1) * 16].ravel()).argmax()
    nm = np.vectorize(lambda v: names[v])(cell)
    tree = np.vectorize(lambda n: n.startswith('tree'))(nm)
    tree[62:64, 23:27] = True        # HGSS: blocked lawn under a tree row that starts on row 63; one whole tree pair here
    path = np.isin(nm, ['sek_fe03', 'sek_fe03_r'])
    pale = np.isin(nm, ['grass02', 'grass02_r'])
    flower = np.isin(nm, ['flower01', 'flower02'])

    fu = load_frlg(engine, 'FuchsiaCity_Frlg')
    r15 = load_frlg(engine, 'Route15_Frlg')
    r5 = load_frlg(engine, 'Route5_Frlg')
    M = Map()

    # ---------------------------------------------------------- 1. ground: lawn everywhere
    for y in range(H):
        for x in range(W):
            M.put(x, y, LAWN[(x % 2, y % 2)], False, '.', lock=False)

    # ---------------------------------------------------------- 2. stamps (buildings, pens, gates)
    # Pal Park hall: FRLG Safari Zone building (FRLG (22..27, 3..5)) under the Safari Office's roof top
    # (FRLG (26..31, 12)) and roof rows (FRLG (22..27, 0)). Doors (30, 19) and (31, 19).
    hx, top = 28, 9
    M.stamp(fu, 26, 12, 6, 1, hx, top, 'B')
    for yy in range(top + 1, 17):
        M.stamp(fu, 22, 0, 6, 1, hx, yy, 'B')
    M.stamp(fu, 22, 3, 6, 3, hx, 17, 'B')
    # Mart: FRLG (9..12, 12..15); its door is the third column, on HGSS's door (13, 32).
    M.stamp(fu, 9, 12, 4, 4, 11, 29, 'B')
    # Gym: FRLG (6..12, 28..32), door middle, on (11, 55).
    M.stamp(fu, 6, 28, 7, 5, 8, 51, 'B')
    # Pokemon Center: FRLG (23..27, 27..31), door middle, on (25, 55).
    M.stamp(fu, 23, 27, 5, 5, 23, 51, 'B')
    # Houses: FRLG house1 (13..17, 28..31) cut to HGSS's four-wide footprints (column 3 left out).
    def house(src_x, src_y, dx, dy, door=True):
        cols = [src_x, src_x + 1, src_x + 3, src_x + 4]
        for i, c in enumerate(cols):
            M.stamp(fu, c, src_y, 1, 4, dx + i, dy, 'B')
        if not door:
            M.put(dx + 1, dy + 3, int(fu[src_y + 3, src_x + 2]) & 0x3FF, True, 'B')
    house(13, 28, 15, 52, door=True)       # southwest house, door (16, 55)
    house(18, 28, 19, 52, door=False)
    house(32, 28, 37, 48, door=True)       # warden's house, door (38, 51)
    house(32, 28, 41, 48, door=False)      # FRLG house2's top row carries its shed; the warden's house top is used for both

    # Pens (hedge enclosures): FRLG pond pen (5..11, 6..10) and sand pen (12..18, 6..10), sized to HGSS's.
    def pen(x0, y0, w, h, kind):
        top = [0x290] + [0x291] * (w - 2) + [0x292]
        mid = [0x293] + [0x294] * (w - 2) + [0x295]
        rows_in = h - 3
        for i, v in enumerate(top): M.put(x0 + i, y0, v, True, 'P')
        for i, v in enumerate(mid): M.put(x0 + i, y0 + 1, v, True, 'P')
        for j in range(rows_in):
            yy = y0 + 2 + j
            M.put(x0, yy, 0x29B, True, 'P'); M.put(x0 + w - 1, yy, 0x29B, True, 'P')
            for i in range(1, w - 1):
                first, last = j == 0, j == rows_in - 1
                if kind == 'pond':
                    row = (0x1A5, 0x1A6, 0x1A7) if first else ((0x333, 0x334, 0x335) if last else (0x1AD, 0x1AE, 0x1AF))
                elif kind == 'bed':
                    row = (0xD3, 0xD4, 0xD5) if first else ((0xE3, 0xE4, 0xE5) if last else (0xDB, 0xDC, 0xDD))
                else:
                    row = (FLOWER, FLOWER, FLOWER)
                v = row[0] if i == 1 else (row[2] if i == w - 2 else row[1])
                M.put(x0 + i, yy, v, True, 'P')
        yb = y0 + h - 1
        M.put(x0, yb, 0x29C, True, 'P'); M.put(x0 + w - 1, yb, 0x29C, True, 'P')
        for i in range(1, w - 1):
            M.put(x0 + i, yb, 0x28F if i == w - 2 else 0x28E, True, 'P')
    pen(12, 21, 7, 6, 'pond')
    pen(21, 21, 6, 6, 'flower')
    pen(35, 21, 6, 6, 'bed')
    pen(43, 21, 7, 6, 'flower')
    pen(39, 27, 7, 5, 'bed')

    # Southwest pond pen: hedge along its top and east side, trees to its west (HGSS rows 36..39).
    for i, v in enumerate([0x290] + [0x291] * 6 + [0x292]): M.put(12 + i, 36, v, True, 'P')
    for i, v in enumerate([0x293] + [0x294] * 6 + [0x295]): M.put(12 + i, 37, v, True, 'P')
    for i in range(7):
        v1 = 0x1A5 if i == 0 else (0x1A7 if i == 6 else 0x1A6)
        v2 = 0x333 if i == 0 else (0x335 if i == 6 else 0x334)
        M.put(12 + i, 38, v1, True, 'P'); M.put(12 + i, 39, v2, True, 'P')
    M.put(19, 38, 0x29B, True, 'P'); M.put(19, 39, 0x29C, True, 'P')

    # East pond by the warden's house: FRLG's fenced pond (35..41, 24..26) sized to HGSS's (39..47, 42..46).
    for i in range(9):
        x = 39 + i
        a, b, c = (0x1A5, 0x1AD, 0x133) if i == 0 else ((0x1A7, 0x1AF, 0x133) if i == 8 else (0x1A6, 0x1AE, 0x133))
        M.put(x, 42, a, False, '~'); M.put(x, 43, b, False, '~'); M.put(x, 44, b, False, '~'); M.put(x, 45, b, False, '~')
        M.put(x, 46, c, False, '.')

    # Route 15 gatehouse exterior: FRLG Route 15's gate (cols 9..14 of rows 8..12), west door on (57, 39).
    for j in range(5):
        for i, sx in enumerate([9, 10, 11, 12, 13, 14, 14]):
            v = int(r15[8 + j, sx])
            M.put(57 + i, 36 + j, v & 0x3FF, bool((v >> 10) & 3), 'G')
    # Route 19 gatehouse exterior: FRLG Route 5's south gate (cols 22..27, rows 32..34), doors (19, 61), (20, 61).
    for j in range(3):
        for i in range(6):
            v = int(r5[32 + j, 22 + i])
            M.put(17 + i, 61 + j, v & 0x3FF, bool((v >> 10) & 3), 'G')

    # ---------------------------------------------------------- 3. rock: plateau behind the south row, low walls, south hills
    plateau = np.zeros((H, W), bool); plateau[45:52, 6:30] = True
    for y in range(45, 52):
        for x in range(6, 30):
            if M.locked[y, x]: continue
            col = 'w' if x == 6 else ('e' if x == 29 else 'm')
            row = 'n' if y == 45 else ('s' if y == 51 and not 15 <= x <= 22 else 'm')   # the houses' roofs stand on the rock
            key = {('n', 'w'): 'nw', ('n', 'm'): 'n', ('n', 'e'): 'ne', ('m', 'w'): 'w', ('m', 'm'): 'c',
                   ('m', 'e'): 'e', ('s', 'w'): 'sw', ('s', 'm'): 's', ('s', 'e'): 'se'}[(row, col)]
            M.put(x, y, ROCK[key], True, 'R')
    for x, top_piece, wall in ((6, ROCK['wall_w_top'], ROCK['wall_w']), (29, ROCK['wall_e_top'], ROCK['wall_e'])):
        M.put(x, 52, top_piece, True, 'R')
        for y in range(53, 59): M.put(x, y, wall, True, 'R')
    M.put(6, 59, ROCK['wall_sw'], True, 'R'); M.put(29, 59, ROCK['wall_se'], True, 'R')
    for x, v in ((7, ROCK['ledge']), (8, ROCK['ledge_r']), (13, ROCK['ledge_l']), (14, ROCK['ledge']),
                 (15, ROCK['ledge']), (16, ROCK['ledge_r']), (24, ROCK['ledge_l']), (25, ROCK['ledge']),
                 (26, ROCK['ledge']), (27, ROCK['ledge']), (28, ROCK['ledge'])):
        M.put(x, 59, v, True, 'R')
    hills = np.zeros((H, W), bool); hills[62:64, 0:17] = True; hills[62:64, 27:32] = True
    for y in range(62, 64):
        for x in list(range(0, 17)) + list(range(27, 32)):
            M.put(x, y, nine(hills, x, y, ROCK) if y == 62 or x in (0, 16, 27, 31) else ROCK['c'], True, 'R')
    # hill edges at the map edge keep their side piece only where the hill really ends
    M.put(0, 62, ROCK['n'], True, 'R'); M.put(0, 63, ROCK['c'], True, 'R')

    # ---------------------------------------------------------- 4. pale lawn around the pens
    for y in range(H):
        for x in range(W):
            if pale[y, x] and not M.locked[y, x]:
                M.put(x, y, nine(pale, x, y, PALE), False, ',', lock=False)

    # ---------------------------------------------------------- 5. paths (HGSS dirt + its stone edging)
    region = path.copy()
    for y in range(H):
        for x in range(W):
            if region[y, x] and not M.locked[y, x]:
                M.put(x, y, nine(region, x, y, PATH), False, '=', lock=False)

    # ---------------------------------------------------------- 6. flowers outside the pens
    for y in range(H):
        for x in range(W):
            if flower[y, x] and not M.locked[y, x] and M.mat[y, x] == '.':
                M.put(x, y, FLOWER, False, '*', lock=False)

    # ---------------------------------------------------------- 7. signs (HGSS bg events)
    # A sign on dirt or pale lawn is FRLG's sign (its top layer) over that cell's own ground (bottom layer).
    for (x, y), top in {(29, 21): 0x2, (36, 51): 0x2, (24, 40): 0x2, (9, 57): 0x168}.items():
        under = int(M.mid[y, x])
        M.put(x, y, top if under in LAWN.values() else M.comp(under, top), True, 's')

    # ---------------------------------------------------------- 8. fences: HGSS blocked lawn/pale cells that nothing else explains
    LAMPS = {(10, 20), (51, 20), (27, 27), (34, 27), (4, 61), (29, 61)}     # HGSS lamp posts, not reproduced
    T0 = tree.copy(); T0[M.locked & (M.mat != 'T')] = False
    fence = np.zeros((H, W), bool)
    for y in range(H):
        for x in range(W):
            if M.locked[y, x] or tree[y, x] or (x, y) in LAMPS: continue
            if walk[y, x]: continue
            below = (x, y + 1)
            if y + 1 < H and (tree[y + 1, x] or M.mat[y + 1, x] in 'BG'):
                continue                      # HGSS's tree canopy or roof overhang: open lawn here (adapt_walk)
            fence[y, x] = True
    def f(x, y): return 0 <= x < W and 0 <= y < H and fence[y, x]
    for y in range(H):
        for x in range(W):
            if not fence[y, x]: continue
            n, s, w_, e = f(x, y - 1), f(x, y + 1), f(x - 1, y), f(x + 1, y)
            if (n or s) and not (w_ or e):
                # which side of the enclosure: look along the run for a corner
                v = FENCE['vl']
                yy = y
                while f(x, yy + 1): yy += 1
                if f(x - 1, yy) and not f(x + 1, yy): v = FENCE['vr']
                if not s: v = FENCE['vl_end'] if v == FENCE['vl'] else FENCE['vr_end']
            elif s and e and not w_: v = FENCE['nw']
            elif s and w_ and not e: v = FENCE['ne']
            elif n and e and not w_: v = FENCE['sw']
            elif n and w_ and not e: v = FENCE['se']
            elif e and not w_: v = FENCE['lend']
            elif w_ and not e: v = FENCE['rend']
            else: v = FENCE['h']
            M.put(x, y, v, True, 'F')

    # ---------------------------------------------------------- 9. trees: FRLG 2 x 2 trees on HGSS's tree squares
    T = tree.copy()
    T[M.locked] = False
    def t(x, y): return not (0 <= x < W and 0 <= y < H) or T[y, x]
    for y0 in range(0, H, 2):
        x = 0
        while x < W:
            if T[y0, x] and y0 + 1 < H and T[y0 + 1, x]:
                for dx in (0, 1):
                    for dy in (0, 1):
                        xx, yy = x + dx, y0 + dy
                        if dy == 0:
                            if not t(xx, yy - 1): v = 0xE if dx == 0 else 0xF
                            elif dx == 0: v = 0x1C if t(xx - 1, yy) else 0x1E
                            else: v = 0x1D if t(xx + 1, yy) else 0x1F
                        else:
                            if not t(xx, yy + 1):
                                v = (0x24 if t(xx - 1, yy) else 0x26) if dx == 0 else (0x25 if t(xx + 1, yy) else 0x27)
                            else:
                                v = (0x14 if t(xx - 1, yy) else 0x16) if dx == 0 else (0x15 if t(xx + 1, yy) else 0x17)
                        M.put(xx, yy, v, True, 'T')
                x += 2
            else:
                x += 1
    # HGSS's warp cells (doors and gate exits) stay solid until their interiors or routes exist.
    for x, y in [(57, 38), (57, 39), (19, 61), (20, 61), (13, 32), (30, 19), (31, 19), (11, 55), (16, 55), (25, 55), (38, 51)]:
        M.blocked[y, x] = True
    # Traversal follows HGSS: a building, gate or pond-bank cell blocks wherever HGSS blocks it.
    for y in range(H):
        for x in range(W):
            if M.mat[y, x] in 'BG' and not walk[y, x]: M.blocked[y, x] = True
            if M.mat[y, x] == '.' and M.locked[y, x] and not walk[y, x]: M.blocked[y, x] = True
    return M, walk

def write(M, walk, out: Path, engine):
    out.mkdir(parents=True, exist_ok=True)
    # FRLG block word: metatile | collision << 10 | elevation << 12 (walkable ground at elevation 3, as FRLG Fuchsia)
    vals = []
    for y in range(H):
        for x in range(W):
            v = (int(M.mid[y, x]) & 0x3FF if int(M.mid[y, x]) < 0x1000 else 0) | (1 << 10 if M.blocked[y, x] else 0) | (0 if M.blocked[y, x] else 3 << 12)
            vals.append(v)
    (out / 'frlg-grid.json').write_text(json.dumps(dict(
        width=W, height=H, cells=[int(v) for v in M.mid.ravel()], blocked=[int(b) for b in M.blocked.ravel()],
        composites={str(k): list(v) for k, v in M.comps.items()}, border=[0x1C, 0x1D, 0x14, 0x15])) + '\n')
    (out / 'material.txt').write_text('\n'.join(''.join(r) for r in M.mat) + '\n')
    diff = [(x, y) for y in range(H) for x in range(W) if (not M.blocked[y, x]) != bool(walk[y, x])]
    (out / 'walk-diff.txt').write_text('\n'.join(f'{x},{y} native={"walk" if not M.blocked[y, x] else "block"} hgss={"walk" if walk[y, x] else "block"} mat={M.mat[y, x]}' for x, y in diff) + '\n')
    sym = F.symbols(Path(engine))
    pair = F.Pair(sym['gTileset_General_Frlg'], sym['gTileset_FuchsiaCity'])
    from PIL import Image
    img = Image.new('RGB', (W * 16, H * 16))
    for i, v in enumerate(M.mid.ravel()):
        v = int(v)
        if v in M.comps:
            u, t = M.comps[v]
            c = pair.render(u).copy(); top = pair.layer_tiles(t, 1); c.paste(top, (0, 0), top)
        else:
            c = pair.render(v)
        img.paste(c, ((i % W) * 16, (i // W) * 16))
    img.save(out / 'preview.png')
    return diff

if __name__ == '__main__':
    eng, phg, ref, out = map(Path, sys.argv[1:5])
    M, walk = build(eng, phg, ref)
    d = write(M, walk, out, eng)
    print('walk differences:', len(d))
