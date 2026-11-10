"""Pack Canalave's two layers (compose.py) into a primary and a secondary tileset and a map.

- Every 8x8 tile takes one of 13 banks of 15 colours (quant.py). Bank 4 keeps Emerald's water indices 11-14,
  recoloured to Platinum's sea blues, so the General water frames animate in it.
- Primary tile 0 is blank; tiles 1-2 are Emerald's deep-water pair, which the tileset's callback animates. Secondary tiles 1008-1023
  stay empty for door frames (field_door.c).
- Identical tiles share one slot in any flip and under any bank; identical cells share one metatile.
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image
import cn_quant as Q
from cn_reference import W, H, PX

K = 13
WATER_BANK = 4
WATER_COLOURS = {11: (99, 165, 255), 12: (74, 148, 247), 13: (41, 115, 231), 14: (33, 107, 214)}
DEEP = (1, 2)                              # primary tiles: General's deep-water pair (strip tiles 22, 23), animated
DEEP_SRC = 22
DOOR_SLOTS = range(1008, 1024)
FOLD_STEP = 12                             # largest squared 5-bit colour step a folded pixel may take
BACKDROP = (0, 0, 0)

def rgb5(a):
    return (np.asarray(a, np.int64) >> 3)

def key5(a):
    a = rgb5(a)
    return (a[..., 0] << 10) | (a[..., 1] << 5) | a[..., 2]

def water_frame0(engine):
    im = Image.open(Path(engine) / 'data/tilesets/primary/general/anim/water/0.png')
    a = np.array(im); n = im.width // 8
    return [a[(i // n) * 8:(i // n) * 8 + 8, (i % n) * 8:(i % n) * 8 + 8].copy() for i in range(30)]

def deep_parity(qx, qy):
    return (qx + qy) & 1

class Packed:
    pass

def fold_tiles(itiles, assign, banks, quad, k):
    """Let a rarely used tile take a much-used one that differs from it in at most k pixels, each by a small
    step of colour, with the same transparent pixels. Rewrites itiles in place; returns the folds made."""
    import collections
    use = collections.Counter()
    for lo, hi in quad.values():
        for v in (lo, hi):
            if v is not None and v != 'water': use[v] += 1
    pal = [np.array([c if c is not None else (99, 99, 99) for c in s], float) for s in banks]
    order = sorted(range(len(itiles)), key=lambda i: -use[i])
    kept, kept_arr = [], []
    folds = []
    for i in order:
        a = itiles[i]; b = int(assign[i]); p = pal[b]
        best = None
        if kept_arr:
            A = np.stack(kept_arr)                                  # candidates in all flips
            same_mask = ((A == 0) == (a == 0)[None]).all((1, 2))
            diff = (A != a[None])
            n = diff.sum((1, 2))
            ok = same_mask & (n <= k) & (n > 0)
            exact = same_mask & (n == 0)
            if exact.any():
                continue
            for j in np.nonzero(ok)[0][np.argsort(n[ok])]:
                d = ((p[A[j]] - p[a]) ** 2).sum(-1)[diff[j]]
                if d.max() <= FOLD_STEP:
                    best = j; break
        if best is not None:
            folds.append((i, int(n[best])))
            itiles[i] = kept_arr[best].copy()
        else:
            for f in (a, a[:, ::-1], a[::-1], a[::-1, ::-1]):
                kept_arr.append(f)
    return folds

def pack(t, engine, seed=0, rounds=30, fold=0):
    frames = water_frame0(engine)
    low5, up5 = key5(t.low), key5(t.up[..., :3])
    upa = t.up[..., 3] > 0
    # still water: frame 0's own pixels in Platinum's blues
    wk = {i: (c[0] >> 3) << 10 | (c[1] >> 3) << 5 | (c[2] >> 3) for i, c in WATER_COLOURS.items()}
    QH, QW = H * 2, W * 2
    for qy in range(QH):
        for qx in range(QW):
            s = t.still[qy * 8:qy * 8 + 8, qx * 8:qx * 8 + 8]
            if s.any():
                f = frames[DEEP_SRC + deep_parity(qx, qy)]
                v = np.vectorize(lambda i: wk.get(int(i), wk[13]))(f)
                low5[qy * 8:qy * 8 + 8, qx * 8:qx * 8 + 8][s] = v[s]
    # ---- unique colour tiles
    tiles, index, quad = [], {}, {}
    def add(arr):
        k = arr.tobytes()
        if k not in index:
            index[k] = len(tiles); tiles.append(arr.copy())
        return index[k]
    for qy in range(QH):
        for qx in range(QW):
            sl = (slice(qy * 8, qy * 8 + 8), slice(qx * 8, qx * 8 + 8))
            lo = 'water' if t.sea[sl].all() else add(low5[sl])
            assert not (t.sea[sl].any() and lo != 'water')
            a = upa[sl]
            hi = add(np.where(a, up5[sl], -1)) if a.any() else None
            quad[(qx, qy)] = (lo, hi)
    cols = sorted({int(c) for a in tiles for c in np.unique(a) if c >= 0} | set(wk.values()))
    cidx = {c: i for i, c in enumerate(cols)}
    C = np.array([[(c >> 10) & 31, (c >> 5) & 31, c & 31] for c in cols])
    T = np.zeros((len(tiles), len(cols)), np.int32)
    for i, a in enumerate(tiles):
        u, n = np.unique(a[a >= 0], return_counts=True)
        T[i, [cidx[int(c)] for c in u]] = n
    fixed = {WATER_BANK: [tuple(v >> 3 for v in WATER_COLOURS[i]) for i in (11, 12, 13, 14)]}
    assign, pals, cost = Q.quantise(T, C, K, fixed=fixed, rounds=rounds, seed=seed)
    # ---- banks: 16 slots, index 0 transparent
    banks = []
    for b in range(K):
        p = [tuple(int(v) for v in c) for c in pals[b]]
        if b == WATER_BANK:
            rest = p[4:]
            slots = [None] * 16
            for j, i in enumerate((11, 12, 13, 14)): slots[i] = p[j]
            free = [i for i in range(1, 16) if slots[i] is None]
            for i, c in zip(free, rest): slots[i] = c
        else:
            slots = [None] + p + [None] * (15 - len(p))
        banks.append(slots)
    # ---- index tiles
    def to_index(a, b):
        slots = banks[b]
        ids = [i for i in range(1, 16) if slots[i] is not None]
        pc = np.array([slots[i] for i in ids], float)
        out = np.zeros((8, 8), np.uint8)
        m = a >= 0
        px = np.stack([(a[m] >> 10) & 31, (a[m] >> 5) & 31, a[m] & 31], 1).astype(float)
        out[m] = np.array(ids)[((px[:, None] - pc[None]) ** 2).sum(2).argmin(1)]
        return out
    itiles = [to_index(a, int(assign[i])) for i, a in enumerate(tiles)]
    folds = fold_tiles(itiles, assign, banks, quad, fold) if fold else []
    # ---- sheet
    sheet = [None] * 1024
    sheet[0] = np.zeros((8, 8), np.uint8)
    for i, s in enumerate(DEEP): sheet[s] = frames[DEEP_SRC + i]
    reserved = {0} | set(DEEP) | set(DOOR_SLOTS)
    free = [i for i in range(1024) if i not in reserved]
    where = {}
    def flips(a):
        return [(a, 0), (a[:, ::-1], 1), (a[::-1], 2), (a[::-1, ::-1], 3)]
    slot_of = {}                      # index-pattern bytes -> (slot, flip that turns the stored tile into it)
    def place(a):
        k = a.tobytes()
        if k in slot_of: return slot_of[k]
        assert free, 'more tiles than both sheets hold'
        s = free.pop(0); sheet[s] = a.copy()
        for f, fl in flips(a):
            slot_of.setdefault(f.tobytes(), (s, fl))
        return slot_of[k]
    order = sorted(range(len(itiles)), key=lambda i: 0)   # placement order = first use (below)
    entry = {}
    def ent(i):
        if i not in entry:
            s, fl = place(itiles[i])
            entry[i] = s | (fl << 10) | (int(assign[i]) << 12)
        return entry[i]
    # ---- metatiles
    metas, meta_of = [], {}
    words = np.zeros((H, W), np.int64)
    try:
        for r in range(H):
            for x in range(W):
                e = []
                for layer in (0, 1):
                    for q in range(4):
                        qx, qy = 2 * x + (q & 1), 2 * r + (q >> 1)
                        v = quad[(qx, qy)][layer]
                        if v is None: e.append(0)
                        elif v == 'water': e.append(DEEP[deep_parity(qx, qy)] | (WATER_BANK << 12))
                        else: e.append(ent(v))
                attr = int(t.behaviour[r, x]) | (int(t.layer[r, x]) << 12)
                k = (tuple(e), attr)
                if k not in meta_of:
                    meta_of[k] = len(metas); metas.append(k)
                words[r, x] = meta_of[k] | (int(t.coll[r, x]) << 10) | (int(t.elev[r, x]) << 12)
    except AssertionError:
        raise
    pk = Packed()
    used = len(set(e for e in entry.values() for e in [e & 1023]))
    pk.__dict__.update(banks=banks, sheet=sheet, metas=metas, words=words, tiles=tiles, itiles=itiles, assign=assign,
                       cost=cost, ncolour_tiles=len(tiles), unique_patterns=len({min(f.tobytes() for f, _ in flips(a)) for a in itiles}),
                       free=len(free), quad=quad, folds=folds, frames=frames, T=T, C=C)
    return pk

def jasc(slots):
    return 'JASC-PAL\r\n0100\r\n16\r\n' + ''.join('%d %d %d\r\n' % c for c in slots)

PRIMARY, SECONDARY, LAYOUT = 'data/tilesets/primary/canalave_city', 'data/tilesets/secondary/canalave_city', 'data/layouts/CanalaveCity'

def write(engine, pk, border):
    """Tilesets, palettes, metatiles and the layout's blocks. border: four map words (2x2)."""
    eng = Path(engine)
    grey = [v for i in range(16) for v in (i * 17, i * 17, i * 17)]
    def sheet(path, tiles):
        a = np.zeros((32 * 8, 128), np.uint8)
        for i, t in enumerate(tiles):
            if t is not None:
                a[(i // 16) * 8:(i // 16) * 8 + 8, (i % 16) * 8:(i % 16) * 8 + 8] = t
        im = Image.fromarray(a, 'P'); im.putpalette(grey + [0] * (768 - 48))
        im.save(path, bits=4)
    assert len(pk.metas) <= 1024, len(pk.metas)
    for d, tiles, metas, banks in ((eng / PRIMARY, pk.sheet[:512], pk.metas[:512], range(0, 6)),
                                   (eng / SECONDARY, pk.sheet[512:], pk.metas[512:], range(6, 13))):
        (d / 'palettes').mkdir(parents=True, exist_ok=True)
        sheet(d / 'tiles.png', tiles)
        for b in range(16):
            slots = [(0, 0, 0)] * 16
            if b in banks:
                slots = [tuple(v << 3 for v in c) if c is not None else (0, 0, 0) for c in pk.banks[b]]
                if b == 0: slots[0] = BACKDROP
            (d / f'palettes/{b:02d}.pal').write_text(jasc(slots), newline='')
        (d / 'metatiles.bin').write_bytes(b''.join(struct.pack('<8H', *e) for e, _ in metas))
        (d / 'metatile_attributes.bin').write_bytes(b''.join(struct.pack('<H', a) for _, a in metas))
    (eng / LAYOUT).mkdir(parents=True, exist_ok=True)
    (eng / LAYOUT / 'map.bin').write_bytes(struct.pack('<%dH' % pk.words.size, *[int(w) for w in pk.words.ravel()]))
    (eng / LAYOUT / 'border.bin').write_bytes(struct.pack('<4H', *[int(w) for w in border]))

def expected(t, pk):
    """The town as the packed banks draw it (water as frame 0)."""
    out = np.zeros((H * PX, W * PX, 3), np.uint8)
    def paint(sl, it, b, over):
        pal = np.array([c if c is not None else (0, 0, 0) for c in pk.banks[b]], np.uint8) << 3
        if over:
            m = it > 0; out[sl][m] = pal[it][m]
        else:
            out[sl] = pal[it]
    for (qx, qy), (lo, hi) in pk.quad.items():
        sl = (slice(qy * 8, qy * 8 + 8), slice(qx * 8, qx * 8 + 8))
        if lo == 'water': paint(sl, pk.frames[DEEP_SRC + deep_parity(qx, qy)], WATER_BANK, False)
        else: paint(sl, pk.itiles[lo], int(pk.assign[lo]), False)
        if hi is not None: paint(sl, pk.itiles[hi], int(pk.assign[hi]), True)
    return out

if __name__ == '__main__':
    import cn_compose as compose
    cache, engine, out = sys.argv[1:4]
    t = compose.build(cache, engine)
    pk = pack(t, engine, fold=int(sys.argv[4]) if len(sys.argv) > 4 else 0)
    print('folds', len(pk.folds), 'colour tiles', pk.ncolour_tiles, 'patterns', pk.unique_patterns, 'metatiles', len(pk.metas), 'free', pk.free)
    img = expected(t, pk)
    Image.fromarray(img).save(Path(out) / 'packed-preview.png')
    want = t.image(); d = np.abs(img.astype(int) - want.astype(int)).sum(-1); d[t.sea] = 0
    print('mean abs err/px', d.mean(), 'px>24', int((d > 24).sum()), 'px>48', int((d > 48).sum()), 'max', d.max())
    e = np.clip(d * 4, 0, 255).astype(np.uint8); Image.fromarray(e).save(Path(out) / 'packed-error.png')
    for b, s in enumerate(pk.banks): print(b, sum(c is not None for c in s), int((pk.assign == b).sum()))
