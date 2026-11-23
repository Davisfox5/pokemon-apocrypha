"""Pack Fuchsia's composed picture into a tileset pair of its own and install the layout.

    python3 tools/gba/maps/fuchsia_city/pack.py ENGINE_CHECKOUT

Input: compose.py's compose.npz (bottom RGB, top RGBA). Output, in the engine checkout:
data/tilesets/primary/kanto_fuchsia (512 tiles, tile 0 blank, 512 metatiles, banks 0-5),
data/tilesets/secondary/fuchsia_city_kanto (the rest, banks 6-12), data/layouts/KantoFuchsiaCity.
Nothing in either comes from another tileset.

Palettes: every 8x8 tile of either layer must sit in one bank of 15 colours, 13 banks. Colours are
5-bit. The owner-locked C06 Center's colours are never changed. Past that the closest pair of colours
(by use) is folded, one pair at a time, until every tile fits a bank (largest colour sets placed first).
evidence/pack.json reports how many pixels kept their exact 5-bit colour.

Traversal: HGSS's permissions (trace/traversal.json) in Gen 3 terms. Open ground elevation 3; ponds
MB_POND_WATER at elevation 1; ledges MB_JUMP_WEST/EAST/SOUTH; every door and gate mouth solid until its
interior exists. The Mart is FireRed's 4x4 with its door on HGSS's (13, 32), so it stands on x 11-14
(HGSS: x 12-15, plus the roof's back row); those cells are the gate file's adapt_walk.
"""
from __future__ import annotations
import json, re, struct, sys
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
import compose as Cm                                      # noqa: E402

W = H = 64
ART = ROOT / 'gba/art/kanto-fuchsia'
SRC, EV = ART / 'source', ART / 'evidence'
PRIMARY, SECONDARY, LAYOUT = 'kanto_fuchsia', 'fuchsia_city_kanto', 'KantoFuchsiaCity'
NBANKS, NCOL = 13, 15
MART = (11, 14, 29, 32)

def behaviors(engine):
    names = re.findall(r'^\s+(MB_[A-Z0-9_]+),', (engine / 'include/constants/metatile_behaviors.h').read_text(), re.M)
    return {n: i for i, n in enumerate(names)}

def c5(a):
    a = a.astype(np.int32) >> 3
    return (a[..., 0] << 10) | (a[..., 1] << 5) | a[..., 2]

def rgb(c):
    return ((c >> 10) & 31, (c >> 5) & 31, c & 31)

def dist(a, b):
    (r1, g1, b1), (r2, g2, b2) = rgb(a), rgb(b)
    return 3 * (r1 - r2) ** 2 + 4 * (g1 - g2) ** 2 + 2 * (b1 - b2) ** 2

# Palette banks, each seeded with a job (the bottom layer's families, then the buildings).
BOTTOM_BANK = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4}             # ground, trees, pens, rock and ponds, fences and lights
TOP_BANK = dict(pokemon_center=(5, 6), mart=7, hall=8, gym=9, route15_gate=10, house_red=11, house_pink=11, warden_house=12,
                notice_board=4, city_sign=4, house_sign=4, gym_sign=4)

def tile_bank(fam_tile, table, ground=None):
    v, n = np.unique(fam_tile, return_counts=True)
    order = sorted(zip(n.tolist(), v.tolist()), reverse=True)
    for _, f in order:
        if f != ground:
            return table[f]
    return table[ground]

def fold(pool, locked):
    """pool: colour -> pixels. Fold the cheapest pair until 15 are left; returns colour -> kept colour."""
    live = dict(pool)
    mp = {c: c for c in pool}
    while len(live) > NCOL:
        cols = sorted(live)
        best = None
        for i, a in enumerate(cols):
            for b in cols[i + 1:]:
                if a in locked and b in locked:
                    continue
                k = dist(a, b) * min(live[a], live[b]) ** 0.5
                if best is None or k < best[0]:
                    best = (k, a, b)
        _, a, b = best
        keep, drop = (a, b) if (a in locked or (b not in locked and live[a] >= live[b])) else (b, a)
        mp[drop] = keep
        live[keep] += live.pop(drop)
    def res(c):
        while mp[c] != c:
            c = mp[c]
        return c
    return {c: res(c) for c in pool}, sorted(live)

def reduce(lb, lt, fam, tfam, names, lawn):
    """Each tile goes to the bank of what it shows; each bank keeps the 15 colours that cost least to keep."""
    bank_b = np.zeros((H * 2, W * 2), np.int32); bank_t = np.full((H * 2, W * 2), -1, np.int32)
    ttab = {i + 1: TOP_BANK[n] for i, n in enumerate(names)}
    pools = [Counter() for _ in range(NBANKS)]
    c06_sets = set()
    for ty in range(H * 2):
        for tx in range(W * 2):
            sl = np.s_[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            bank_b[ty, tx] = tile_bank(fam[sl], BOTTOM_BANK, 0)
            v, n = np.unique(lb[sl], return_counts=True)
            pools[bank_b[ty, tx]].update(dict(zip(v.tolist(), n.tolist())))
            t = lt[sl]
            if (t >= 0).any():
                b = tile_bank(tfam[sl][t >= 0], ttab)
                if isinstance(b, tuple):
                    c06_sets.add(frozenset(np.unique(t[t >= 0]).tolist()))
                    bank_t[ty, tx] = -2
                else:
                    bank_t[ty, tx] = b
                    v, n = np.unique(t[t >= 0], return_counts=True)
                    pools[b].update(dict(zip(v.tolist(), n.tolist())))
    # the owner-locked Center: its colours exactly, over two banks
    two = [set(), set()]
    for st in sorted(c06_sets, key=lambda q: (-len(q), sorted(q))):
        if any(st <= b for b in two):
            continue
        i = min((i for i in (0, 1) if len(two[i] | st) <= NCOL), key=lambda i: len(two[i] | st) - len(two[i]))
        two[i] |= st
    maps, banks = [None] * NBANKS, [None] * NBANKS
    for b in range(NBANKS):
        if b in (5, 6):
            banks[b] = sorted(two[b - 5]); maps[b] = {c: c for c in banks[b]}
        else:
            maps[b], banks[b] = fold(pools[b], lawn if b < 5 else ())
    qb, qt = lb.copy(), lt.copy()
    for ty in range(H * 2):
        for tx in range(W * 2):
            sl = np.s_[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            m = maps[bank_b[ty, tx]]
            qb[sl] = np.vectorize(m.get)(lb[sl])
            if bank_t[ty, tx] == -2:
                st = set(np.unique(lt[sl]).tolist()) - {-1}
                bank_t[ty, tx] = 5 if st <= two[0] else 6
            elif bank_t[ty, tx] >= 0:
                m = dict(maps[bank_t[ty, tx]]); m[-1] = -1
                qt[sl] = np.vectorize(m.get)(lt[sl])
    return qb, qt, banks, bank_b, bank_t

def traversal(engine):
    g = Cm.grid()
    mb = behaviors(engine)
    cells = json.loads((SRC / 'trace/traversal.json').read_text())['cells']
    foot = {(c['hx'], c['hz']): c['foot'] for c in cells}
    solid = {(c['hx'], c['hz']): c['collision'] & 0x80 for c in cells}
    beh = np.zeros((H, W), np.int32); col = np.ones((H, W), np.int32); elev = np.zeros((H, W), np.int32)
    for y in range(H):
        for x in range(W):
            c = g[y][x]
            if c == '~':
                beh[y, x], col[y, x], elev[y, x] = mb['MB_POND_WATER'], int(bool(solid[(x, y)])), 1
            elif c in 'LQE':
                beh[y, x], col[y, x], elev[y, x] = mb[dict(L='MB_JUMP_SOUTH', Q='MB_JUMP_WEST', E='MB_JUMP_EAST')[c]], 0, 3
            elif c in 'DCwHXJRtkohbxisp':
                pass                                        # solid
            elif foot[(x, y)] == 'walk' or c in 'gldfuca':               # the cut tree and the Apricorn tree are objects; their cells are open, as in HGSS
                col[y, x], elev[y, x] = 0, 3
    x0, x1, y0, y1 = MART
    for y in range(28, 33):
        for x in range(11, 17):
            if g[y][x] in 'HDXg':
                inside = x0 <= x <= x1 and y0 <= y <= y1
                col[y, x], elev[y, x] = (1, 0) if inside else (0, 3)
    return beh, col, elev

def main(engine):
    engine = Path(engine)
    z = np.load(SRC / 'compose/compose.npz')
    bottom, top = z['bottom'], z['top']
    lb = c5(bottom)
    lt = np.where(top[..., 3] > 0, c5(top[..., :3]), -1)
    c06 = np.array(Image.open(ROOT / 'gba/art/johto-center/source/building.png').convert('RGBA'))
    locked = set(np.unique(c5(c06[..., :3])[c06[..., 3] > 0]).tolist())
    before = len((set(np.unique(lb).tolist()) | set(np.unique(lt).tolist())) - {-1})
    lawn = set(np.unique(lb[:16, 28 * 16:34 * 16]).tolist()) | set(np.unique(lb[20 * 16:21 * 16, 12 * 16:20 * 16]).tolist())
    qb, qt, banks, bank_b, bank_t = reduce(lb, lt, z['fam'], z['tfam'], [str(n) for n in z['names']], lawn)
    ncol, folds = len({c for b in banks for c in b}), 0
    exact = float(((qb == lb).sum() + ((qt == lt) & (lt >= 0)).sum()) / (lb.size + (lt >= 0).sum()))
    index = [{c: i + 1 for i, c in enumerate(b)} for b in banks]

    tiles, tile_id = [np.zeros((8, 8), np.uint8)], {np.zeros((8, 8), np.uint8).tobytes(): (0, 0)}
    def entry(a, y, x):
        t = a[y:y + 8, x:x + 8]
        s = set(np.unique(t).tolist()) - {-1}
        if not s:
            return 0
        bank = int((bank_b if a is qb else bank_t)[y // 8, x // 8])
        assert s <= set(banks[bank]), (x, y, bank)
        lut = index[bank]
        px = np.array([[lut.get(int(v), 0) for v in r] for r in t], np.uint8)
        for f, v in enumerate((px, px[:, ::-1], px[::-1], px[::-1, ::-1])):
            k = v.tobytes()
            if k in tile_id:
                tid, f0 = tile_id[k]
                return tid | ((f ^ f0) << 10) | (bank << 12)
        tile_id[px.tobytes()] = (len(tiles), 0)
        tiles.append(px)
        return (len(tiles) - 1) | (bank << 12)

    beh, col, elev = traversal(engine)
    metas, meta_id, grid_ids = [], {}, np.zeros((H, W), np.int32)
    for y in range(H):
        for x in range(W):
            e = [entry(qb, y * 16 + (q // 2) * 8, x * 16 + (q % 2) * 8) for q in range(4)] + \
                [entry(qt, y * 16 + (q // 2) * 8, x * 16 + (q % 2) * 8) for q in range(4)]
            k = (tuple(e), int(beh[y, x]))
            if k not in meta_id:
                meta_id[k] = len(metas); metas.append(k)
            grid_ids[y, x] = meta_id[k]
    rep = dict(colours_before=before, colours_after=ncol, folds=folds, exact_pixel_share=round(exact, 4),
               tiles=len(tiles), tile_limit=1024, metatiles=len(metas), metatile_limit=1024,
               banks=[len(b) for b in banks])
    print(json.dumps(rep))
    (EV / 'pack.json').write_text(json.dumps(rep, indent=1) + '\n')
    assert len(tiles) <= 1024 and len(metas) <= 1024, rep

    def write_tiles(path, ts):
        n = max(1, len(ts)); rows = (n + 15) // 16
        a = np.zeros((rows * 8, 128), np.uint8)
        for i, t in enumerate(ts):
            a[(i // 16) * 8:(i // 16) * 8 + 8, (i % 16) * 8:(i % 16) * 8 + 8] = t
        im = Image.fromarray(a, 'P')
        im.putpalette([v for i in range(16) for v in (i * 17, i * 17, i * 17)] + [0] * (768 - 48))
        im.save(path, bits=4)
    def jasc(cols):
        cols = [(0, 0, 0)] + [tuple(v * 8 + (v >> 2) for v in rgb(c)) for c in cols]
        cols += [(0, 0, 0)] * (16 - len(cols))
        return 'JASC-PAL\r\n0100\r\n16\r\n' + ''.join(f'{r} {g} {b}\r\n' for r, g, b in cols)
    pd, sd = engine / 'data/tilesets/primary' / PRIMARY, engine / 'data/tilesets/secondary' / SECONDARY
    for d in (pd, sd):
        (d / 'palettes').mkdir(parents=True, exist_ok=True)
        for b in range(16):
            (d / f'palettes/{b:02}.pal').write_text(jasc(banks[b] if b < NBANKS else []), newline='')
    write_tiles(pd / 'tiles.png', tiles[:512] + [np.zeros((8, 8), np.uint8)] * max(0, 512 - len(tiles)))
    write_tiles(sd / 'tiles.png', tiles[512:] or [np.zeros((8, 8), np.uint8)])
    def meta_bytes(ms):
        return struct.pack('<%dH' % (len(ms) * 8), *[v for k in ms for v in k[0]]), struct.pack('<%dH' % len(ms), *[k[1] for k in ms])
    pm = metas[:512] + [((0,) * 8, 0)] * max(0, 512 - len(metas))
    for d, ms in ((pd, pm), (sd, metas[512:] or [((0,) * 8, 0)])):
        m, a = meta_bytes(ms)
        (d / 'metatiles.bin').write_bytes(m); (d / 'metatile_attributes.bin').write_bytes(a)
    ld = engine / 'data/layouts' / LAYOUT
    ld.mkdir(parents=True, exist_ok=True)
    vals = [int(grid_ids[y, x]) | (int(col[y, x]) << 10) | (int(elev[y, x]) << 12) for y in range(H) for x in range(W)]
    (ld / 'map.bin').write_bytes(struct.pack('<%dH' % len(vals), *vals))
    border = [int(grid_ids[y, x]) | 0x400 for y in (4, 5) for x in (2, 3)]
    (ld / 'border.bin').write_bytes(struct.pack('<4H', *border))
    np.savez_compressed(SRC / 'compose/pack.npz', bottom=qb, top=qt, ids=grid_ids, col=col, elev=elev, beh=beh)
    # the packed picture, for the review sheet
    pic = np.zeros((H * 16, W * 16, 3), np.uint8)
    for a in (qb, qt):
        m = a >= 0
        r, g_, b_ = (a >> 10) & 31, (a >> 5) & 31, a & 31
        for i, ch in enumerate((r, g_, b_)):
            pic[..., i][m] = (ch[m] * 8 + (ch[m] >> 2)).astype(np.uint8)
    Image.fromarray(pic).save(EV / 'native.png')

if __name__ == '__main__':
    main(sys.argv[1])
