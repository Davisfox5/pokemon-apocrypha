#!/usr/bin/env python3
"""Route 36's two ridge crossings redrawn with the Johto standard stairs (owner review of #39).

    python3 tools/gba/maps/route36_stairs.py PATH/TO/pokeemerald-expansion [--write]

Route 36 has no generator in this repo (it came from codex/johto-editor-consolidation), so this patches its
tileset in place. Both crossings (columns 14 and 32, rows 20-24) use the same five metatiles: 369 (top cheek),
464, 473, 474 (the walked treads) and 370 (bottom cheek). Each keeps its id, collision and behaviour; only
its graphics change:

- The thin ridge runs on under the flight, unbroken: the column's base is the ridge's own body (metatiles 202
  and 204, alternating as they do above the crossing), flattened into the bottom layer.
- One east-west column of the kit (johto_stairs.east_west) is drawn over it, its bands centred on the three
  walked rows exactly as johto_stairs.place() centres a flight, falling east (FALLS).
- The 20 tiles are cut, deduplicated (with flips) and written into the old stair tiles no other metatile uses
  plus the secondary sheet's free slots. Each tile takes a palette bank that already holds its colours, or a
  bank with free slots gains them.

Without --write it only reports the budget and saves a preview to the scratch path given by PREVIEW.
"""
from __future__ import annotations
import struct, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from tiles import Tileset                    # noqa: E402
import johto_stairs as JS                    # noqa: E402

LAYOUT = 'JohtoRoute36'
TS = 'johto_route36'
STAIR_ROWS = [369, 464, 473, 474, 370]       # rows 20-24 of each crossing, north to south
RIDGE = (202, 204)                           # the ridge body, alternating by row parity (even row: 202)
FIRST_ROW = 20
FALLS = 'E'
FREE_BANKS = tuple(range(13))                # any bank's unused slots may take the new colours
ROOT = HERE.parents[2]
PREVIEW = ROOT / 'gba/art/route36-stairs/preview.png'

def rgb5(c):
    return tuple(int(v) >> 3 << 3 for v in c)

def column_art(t):
    """The 16 x 80 column: ridge body under the kit's east-west band."""
    col = np.zeros((80, 16, 4), np.uint8)
    for i in range(5):
        col[i * 16:(i + 1) * 16, :, :3] = np.array(t.render(RIDGE[(FIRST_ROW + i) % 2]))
    col[..., 3] = 255
    band = np.zeros_like(col)
    mid = (1 + 3 + 1) * JS.PX / 2                 # walked rows are cells 1..3 of the column
    width = len(JS.TOP_RAIL) + JS.TREAD_PX + len(JS.BOTTOM_RAIL)
    top0 = int(round(mid - width / 2 + len(JS.TOP_RAIL) - (JS.PX - 1) / 2))
    JS.east_west(band, 0, top0, FALLS, phase=0)
    m = band[..., 3] > 0
    # A kit colour within one 5-bit step of a colour the ridge already uses takes the ridge's (the rail outline,
    # shade and body sit one step off the ridge's browns); the tileset's free palette slots can't hold both.
    ridge = {rgb5(p) for p in col[..., :3].reshape(-1, 3)}
    for c in {rgb5(p) for p in band[m][:, :3]}:
        near = min(ridge, key=lambda r: sum(abs(a - b) for a, b in zip(r, c)))
        if c not in ridge and sum(abs(a - b) for a, b in zip(near, c)) <= 16:
            hit = m & (np.abs(band[..., :3].astype(int) - np.array(c)) < 8).all(-1)
            band[hit, :3] = near
    col[m] = band[m]
    return col

def flips(a):
    return {(0, 0): a, (1, 0): a[:, ::-1], (0, 1): a[::-1], (1, 1): a[::-1, ::-1]}

def plan(engine):
    t = Tileset(engine, TS, TS)
    col = column_art(t)
    rgb = np.array([[rgb5(p) for p in row] for row in col[..., :3]], np.uint8)
    # Palettes as editable lists (bank -> 16 colours), primary 0-5, secondary 6-12.
    pals = {b: [rgb5(c) for c in t.pals[b >= 6][b]] for b in range(13)}
    used = {b: set() for b in range(13)}
    for part in range(2):
        for e in t.blocks[part]:
            for x in e:
                tid, bank = x & 1023, x >> 12
                tiles = t.tiles[tid >= 512]
                idx = tid - 512 if tid >= 512 else tid
                if idx < len(tiles):
                    used[bank] |= {v % 16 for v in tiles[idx]}
    free_slots = {b: [i for i in range(1, 16) if i not in used[b]] for b in FREE_BANKS}
    added = {}
    # Cut 20 tiles, find each one's bank.
    cells = []
    for i in range(5):
        quads = []
        for q in range(4):
            y0, x0 = i * 16 + (q // 2) * 8, (q % 2) * 8
            quads.append(rgb[y0:y0 + 8, x0:x0 + 8])
        cells.append(quads)
    # Banks: a tile whose colours one bank already holds takes it; the rest are packed into the banks with
    # free slots by a small integer program (each tile in one bank, each bank's added colours within its
    # free slots).
    from scipy.optimize import milp, LinearConstraint, Bounds
    keys = [(i, q) for i in range(5) for q in range(4)]
    cset = {k: {tuple(map(int, p)) for p in cells[k[0]][k[1]].reshape(-1, 3)} for k in keys}
    bank_of = {}
    for k in keys:
        b = next((b for b in range(13) if cset[k] <= set(pals[b][1:])), None)
        if b is not None:
            bank_of[k] = b
    rest = [k for k in keys if k not in bank_of]
    if rest:
        colours = sorted(set().union(*(cset[k] for k in rest)))
        X = {(k, b): n for n, (k, b) in enumerate((k, b) for k in rest for b in FREE_BANKS)}
        Y = {(c, b): len(X) + n for n, (c, b) in enumerate((c, b) for c in colours for b in FREE_BANKS)}
        N = len(X) + len(Y)
        A, lo, hi = [], [], []
        for k in rest:
            row = np.zeros(N); row[[X[k, b] for b in FREE_BANKS]] = 1; A.append(row); lo.append(1); hi.append(1)
            for b in FREE_BANKS:
                for c in cset[k] - set(pals[b][1:]):
                    row = np.zeros(N); row[Y[c, b]] = 1; row[X[k, b]] = -1; A.append(row); lo.append(0); hi.append(1)
        for b in FREE_BANKS:
            row = np.zeros(N)
            for c in colours:
                if c not in pals[b][1:]:
                    row[Y[c, b]] = 1
            A.append(row); lo.append(0); hi.append(len(free_slots[b]))
        cost = np.zeros(N); cost[len(X):] = 1
        res = milp(cost, constraints=LinearConstraint(np.array(A), lo, hi), integrality=np.ones(N), bounds=Bounds(0, 1))
        if res.x is None:
            raise SystemExit(f'the stair tiles do not fit the free palette slots: {res.message} {[len(free_slots[b]) for b in FREE_BANKS]}')
        for (c, b), n in Y.items():
            if res.x[n] > 0.5:
                s_ = free_slots[b].pop(0); pals[b][s_] = c; added.setdefault(b, []).append(s_)
        for (k, b), n in X.items():
            if res.x[n] > 0.5:
                bank_of[k] = b
    entries, uniq = [], []          # entries[cell][q] = (uniq index, hflip, vflip, bank)
    for i, quads in enumerate(cells):
        row = []
        for q, tile in enumerate(quads):
            b = bank_of[(i, q)]
            idx = np.array([[pals[b].index(tuple(map(int, p))) for p in r] for r in tile], np.uint8)
            hit = None
            for k, (ub, ua) in enumerate(uniq):
                if ub != b:
                    continue
                for (h, v), f in flips(idx).items():
                    if (f == ua).all():
                        hit = (k, h, v); break
                if hit:
                    break
            if hit is None:
                uniq.append((b, idx)); hit = (len(uniq) - 1, 0, 0)
            row.append(hit + (b,))
        entries.append(row)
    return t, col, pals, entries, uniq, added

def write(engine, t, pals, entries, uniq, added):
    base = Path(engine) / 'data/tilesets'
    # Slots: the old stair tiles only these metatiles use, then the secondary sheet's free slots.
    users = {}
    for part in range(2):
        for i, e in enumerate(t.blocks[part]):
            for x in e:
                users.setdefault(x & 1023, set()).add(part * 512 + i)
    old = sorted({x & 1023 for m in STAIR_ROWS for x in t.blocks[0][m]} - {0})
    slots = [tid for tid in old if users[tid] <= set(STAIR_ROWS)]
    sec = Image.open(base / 'secondary' / TS / 'tiles.png')
    n_sec = sec.width // 8 * (sec.height // 8)
    slots += [512 + k for k in range(n_sec, 512)]
    assert len(uniq) <= len(slots), (len(uniq), len(slots))
    tid_of = [slots[k] for k in range(len(uniq))]
    # Tiles: grow the secondary sheet to hold the highest slot used.
    a = np.array(sec)
    need_rows = max([(t_ - 512) // 16 + 1 for t_ in tid_of if t_ >= 512] + [a.shape[0] // 8])
    if need_rows * 8 > a.shape[0]:
        a = np.concatenate([a, np.zeros((need_rows * 8 - a.shape[0], a.shape[1]), a.dtype)])
    prim = np.array(Image.open(base / 'primary' / TS / 'tiles.png'))
    for (b, idx), tid in zip(uniq, tid_of):
        sheet, k = (a, tid - 512) if tid >= 512 else (prim, tid)
        y, x = (k // 16) * 8, (k % 16) * 8
        sheet[y:y + 8, x:x + 8] = idx
    changed = {'secondary': any(t_ >= 512 for t_ in tid_of), 'primary': any(t_ < 512 for t_ in tid_of)}
    for img, part in ((a, 'secondary'), (prim, 'primary')):
        if not changed[part]:
            continue
        out = Image.fromarray(img, 'P')
        src = Image.open(base / part / TS / 'tiles.png')
        out.putpalette(src.getpalette())
        out.save(base / part / TS / 'tiles.png')
    # Palettes: only the slots that took a new colour change; every other line stays byte for byte.
    for b, cols in pals.items():
        if b not in added:
            continue
        part = 'primary' if b < 6 else 'secondary'
        p = base / part / TS / 'palettes' / f'{b:02}.pal'
        raw = p.read_bytes().decode()
        nl = '\r\n' if '\r\n' in raw else '\n'
        lines = raw.splitlines()
        for slot in added[b]:
            lines[3 + slot] = '%d %d %d' % cols[slot]
        p.write_bytes((nl.join(lines) + nl).encode())
    # Metatiles: bottom layer from the plan, middle layer empty; ids, collision and behaviour unchanged.
    mt = base / 'primary' / TS / 'metatiles.bin'
    data = bytearray(mt.read_bytes())
    for m, row in zip(STAIR_ROWS, entries):
        words = [tid_of[k] | (h << 10) | (v << 11) | (b << 12) for k, h, v, b in row] + [0, 0, 0, 0]
        data[m * 16:(m + 1) * 16] = struct.pack('<8H', *words)
    mt.write_bytes(bytes(data))
    return tid_of

def main():
    engine = Path(sys.argv[1]).resolve()
    t, col, pals, entries, uniq, added = plan(engine)
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(col).resize((16 * 8, 80 * 8), Image.NEAREST).save(PREVIEW)
    print('unique tiles', len(uniq), 'banks', sorted({b for b, _ in uniq}))
    if '--write' in sys.argv:
        print('tiles at', write(engine, t, pals, entries, uniq, added))

if __name__ == '__main__':
    main()
