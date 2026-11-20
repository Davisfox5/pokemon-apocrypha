"""Pack Violet City's cells into its two private tilesets from scratch.

Violet is the only map on VioletCityPrimary and VioletCity, so every tile and metatile can be laid out
anew: each cell's lower and upper quadrants take the bank that holds their colours (the cell's own bank
first, as the base had it), identical quadrants share one tile in any flip, identical cells share one
metatile. The 13 banks are Violet's own, with new colours in their free slots (Canvas.pals).
"""
from __future__ import annotations
import struct
import numpy as np
from PIL import Image

import base as B

UNIQUE = set()                                       # cells that keep a metatile of their own (doors.py)
P_TILES, S_TILES = 512, 496                          # the secondary's last 16 slots are the door frames' (field_door.c)
P_META, S_META = 512, 512

def rgb5(a):
    return (np.asarray(a).astype(np.int16) >> 3).astype(np.int16)

class Packer:
    def __init__(self, v, banks):
        self.v = v
        self.banks = banks                           # 13 lists of 16 RGB (slot 0 unused)
        self.index = [{tuple(int(x) >> 3 for x in c): i for i, c in reversed(list(enumerate(b))) if i} for b in banks]
        self.backdrop = tuple(int(x) >> 3 for x in v.backdrop)
        self.tiles = [np.zeros((8, 8), np.uint8)]    # tile 0: empty
        self.lookup = {np.zeros((8, 8), np.uint8).tobytes(): (0, 0)}
        self.metas, self.meta_id = [], {}
        self.misses = []
        self.fold_k, self.folded = 0, 0
        self.free_families = set()
        self.family = {}
        self.pal5 = [np.array([tuple(int(x) >> 3 for x in c) for c in b], np.int16) for b in banks]
        self.pal_fam = [np.full(16, -1) for _ in banks]

    def families(self, fams):
        """fams: list of colour sets (RGB), one per ground texture."""
        self.family = {tuple(int(x) >> 3 for x in c): i for i, f in enumerate(fams) for c in f}
        for b in range(len(self.banks)):
            self.pal_fam[b] = np.array([self.family.get(tuple(int(x) for x in c), -1) if i else -1 for i, c in enumerate(self.pal5[b])])

    def _bank(self, cols, prefer):
        order = list(prefer) + [b for b in range(13) if b not in prefer]
        return next((b for b in order if cols <= self.index[b].keys()), None)

    def _find(self, ix):
        for f in range(4):
            v = ix[:, ::-1] if f & 1 else ix
            v = v[::-1] if f & 2 else v
            hit = self.lookup.get(v.tobytes())
            if hit is not None:
                return hit[0], f
        return None

    def _tile(self, ix):
        for f in range(4):
            v = ix[:, ::-1] if f & 1 else ix
            v = v[::-1] if f & 2 else v
            hit = self.lookup.get(v.tobytes())
            if hit is not None:
                return hit[0], f
        i = len(self.tiles)
        self.tiles.append(ix.copy()); self.lookup[ix.tobytes()] = (i, 0)
        return i, 0

    def entry(self, px5, mask, transparent_is_backdrop, prefer, where):
        """One quadrant layer: px5 8x8x3, mask the pixels it draws."""
        keys = [tuple(int(v) for v in p) for p in px5[mask]]
        if transparent_is_backdrop:                  # the lower layer: backdrop pixels stay index 0
            keys = [k for k in keys if k != self.backdrop]
        if not keys:
            return 0
        cols = set(keys)
        order = list(prefer) + [b for b in range(13) if b not in prefer]
        cands = [b for b in order if cols <= self.index[b].keys()]
        if not cands:
            self.misses.append((where, sorted(cols)))
            return 0
        best = None
        for bank in cands:                           # a bank that draws these pixels with a tile already placed
            ix = np.zeros((8, 8), np.uint8)
            idx = self.index[bank]
            for y, x in zip(*np.nonzero(mask)):
                k = tuple(int(v) for v in px5[y, x])
                if not (transparent_is_backdrop and k == self.backdrop):
                    ix[y, x] = idx[k]
            hit = self._find(ix)
            if hit is not None:
                return hit[0] | (hit[1] << 10) | (bank << 12)
            if best is None:
                best = (bank, ix)
        bank, ix = best
        if self.fold_k:
            hit = self._near(px5, mask, transparent_is_backdrop, cands)
            if hit is not None:
                return hit
        t, f = self._tile(ix)
        return t | (f << 10) | (bank << 12)

    def _near(self, px5, mask, lower, cands):
        """A tile already placed that draws these pixels in one of the banks with at most fold_k pixels moved,
        each to another tone of the same texture: the texture fold. In an edge material (free_families excluded)
        only a pixel inside it (all four neighbours of its kind) moves; rims, outlines and art never move."""
        fam = np.array([[self.family.get(tuple(int(v) for v in p), -1) for p in row] for row in px5])
        care = mask.copy()
        if lower:
            care &= ~(px5 == np.array(self.backdrop)).all(-1)
        if ((fam < 0) & care).any():
            return None                              # only pure ground texture folds
        pf = np.pad(fam, 1, mode='edge')             # the tile's own edge stands in for its neighbour's
        inner = (fam >= 0) & (pf[:-2, 1:-1] == fam) & (pf[2:, 1:-1] == fam) & (pf[1:-1, :-2] == fam) & (pf[1:-1, 2:] == fam)
        inner |= np.isin(fam, list(self.free_families))   # textures with no edge of their own move anywhere in themselves
        T = np.array(self.tiles)                     # n x 8 x 8 indices
        flips = np.stack([T, T[:, :, ::-1], T[:, ::-1, :], T[:, ::-1, ::-1]], 1)
        best = None
        for bank in cands:
            pal = self.pal5[bank]
            col = pal[flips]                         # n x 4 x 8 x 8 x 3
            same = (col == px5[None, None]).all(-1)
            fam_t = self.pal_fam[bank][flips]
            ok = (same | ((fam_t == fam[None, None]) & (fam_t >= 0) & inner[None, None])) | ~care[None, None]   # only inner dither moves
            shape = (flips > 0) == care[None, None]      # transparent (or backdrop) exactly where it was
            good = (ok & shape).all((2, 3))
            diff = np.where(good, (~same & care[None, None]).sum((2, 3)), 99)
            i, f = np.unravel_index(int(diff.argmin()), diff.shape)
            if diff[i, f] <= self.fold_k and (best is None or diff[i, f] < best[0]):
                best = (int(diff[i, f]), int(i), int(f), bank)
        if best is None:
            return None
        self.folded += best[0]
        return best[1] | (best[2] << 10) | (best[3] << 12)

    def metatile(self, low, up, attr, prefer, where):
        lo5, up5 = rgb5(low), rgb5(up[..., :3])
        ent = []
        for q in range(4):
            sl = np.s_[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            ent.append(self.entry(lo5[sl], np.ones((8, 8), bool), True, prefer[q], where))
        for q in range(4):
            sl = np.s_[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            ent.append(self.entry(up5[sl], up[sl][..., 3] > 0, False, prefer[4 + q], where))
        key = (tuple(ent), attr) + ((where,) if where in UNIQUE else ())   # a door's cell: its own metatile, for the door table
        if key not in self.meta_id:
            self.meta_id[key] = len(self.metas); self.metas.append(key[:2])
        return self.meta_id[key]

def pieces(cells, backdrop5):
    """Every quadrant layer's colour set (rgb5) and the banks it would rather take."""
    out = []
    for low, up, attr, bits, prefer in cells:
        lo5, up5 = rgb5(low), rgb5(up[..., :3])
        for q in range(4):
            sl = np.s_[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            s = {tuple(int(v) for v in p) for p in lo5[sl].reshape(-1, 3)} - {backdrop5}
            if s:
                out.append((frozenset(s), tuple(prefer[q])))
            m = up[sl][..., 3] > 0
            s = {tuple(int(v) for v in p) for p in up5[sl][m]}
            if s:
                out.append((frozenset(s), tuple(prefer[4 + q])))
    return out

def place_sets(need, sets, time_limit=120):
    """When the greedy fill runs out of room: each colour set goes to one bank, every bank's colours within 15,
    as few colours added as possible (an integer program)."""
    from scipy.optimize import milp, LinearConstraint, Bounds
    sets = [s for s in sets if not any(s <= n for n in need)]
    nb = len(need)
    colours = sorted(set().union(*sets)) if sets else []
    X = {(i, b): k for k, (i, b) in enumerate((i, b) for i in range(len(sets)) for b in range(nb) if len(need[b] | sets[i]) <= 15)}
    Y = {(c, b): len(X) + k for k, (c, b) in enumerate((c, b) for c in colours for b in range(nb) if c not in need[b])}
    N = len(X) + len(Y)
    rows, lo, hi = [], [], []
    def row(d):
        r = np.zeros(N)
        for k, v in d.items():
            r[k] = v
        return r
    for i in range(len(sets)):
        rows.append(row({X[i, b]: 1 for b in range(nb) if (i, b) in X})); lo.append(1); hi.append(1)
        for b in range(nb):
            if (i, b) in X:
                for c in sets[i] - need[b]:
                    rows.append(row({Y[c, b]: 1, X[i, b]: -1})); lo.append(0); hi.append(1)
    for b in range(nb):
        rows.append(row({Y[c, b]: 1 for c in colours if (c, b) in Y})); lo.append(0); hi.append(15 - len(need[b]))
    cost = np.zeros(N); cost[len(X):] = 1
    res = milp(cost, constraints=LinearConstraint(np.array(rows), lo, hi), integrality=np.ones(N), bounds=Bounds(0, 1),
               options=dict(time_limit=time_limit))
    if res.x is None:
        print('place_sets:', res.status, res.message, flush=True)
        return None
    out = [set(n) for n in need]
    for (c, b), k in Y.items():
        if res.x[k] > 0.5:
            out[b].add(c)
    return out

RESERVED = {}                                        # bank -> rgb5 colours it holds alone (edges.GATE_BANK)

def pack_sets(need, sets, tries=4000, seed=1):
    """A fast try before the integer program: each set, largest first (ties shuffled), goes to the bank that
    already holds most of it and has room, across many shuffled orders. None when no order fits."""
    import random
    rnd = random.Random(seed)
    sets = [s for s in sets if not any(s <= n for n in need)]
    for t in range(tries):
        order = sorted(sets, key=lambda s: (-len(s), rnd.random())) if t else sorted(sets, key=lambda s: -len(s))
        if t > tries // 2:
            order = sorted(sets, key=lambda s: -len(s) + rnd.random() * 4)
        out = [set(n) for n in need]
        for s in order:
            cand = [(len(s & out[b]) + rnd.random() * (t > 0), -len(out[b]), b) for b in range(len(out))
                    if len(out[b] | s) <= 15 and b not in RESERVED]
            if not cand:
                break
            out[max(cand)[2]] |= s
        else:
            return out
    return None

def allocate(banks, cells, backdrop):
    """Violet's banks, kept where its art still draws them: a slot no quadrant needs any more is free, and
    each colour set no bank holds goes to the bank that already holds most of it and has room for the rest."""
    b5 = [[tuple(int(x) >> 3 for x in c) for c in b] for b in banks]
    backdrop5 = tuple(int(x) >> 3 for x in backdrop)
    ps = pieces(cells, backdrop5)
    need = [set(RESERVED.get(b, ())) for b in range(len(banks))]
    unfit = []
    for s, prefer in sorted(set(ps), key=lambda p: -len(p[0])):
        order = list(prefer) + [b for b in range(len(banks)) if b not in prefer]
        b = next((b for b in order if s <= set(b5[b][1:])), None)
        if b is None:
            unfit.append(s)
        else:
            need[b] |= s
    greedy = [set(n) for n in need]
    ok = True
    for s in sorted(set(unfit), key=len, reverse=True):
        if any(s <= greedy[b] for b in range(len(banks))):
            continue
        cand = [(len(s & greedy[b]), -len(greedy[b]), b) for b in range(len(banks)) if len(greedy[b] | s) <= 15]
        if not cand:
            ok = False
            break
        greedy[max(cand)[2]] |= s
    if not ok:
        placed = place_sets(need, set(unfit))
        if placed is None:
            # No room keeping each set where Violet's art had it: every bank is laid out anew from the maximal
            # colour sets (palette slots move; the pack cuts every tile anew anyway).
            sets = {s for s, _ in ps}
            maximal = {s for s in sets if not any(s < t for t in sets)}
            fresh = [set(RESERVED.get(b, ())) for b in range(len(banks))]
            placed = pack_sets(fresh, maximal) or place_sets(fresh, maximal, time_limit=1500)
            assert placed is not None, 'no palette layout holds every colour set'
        greedy = placed
    need = greedy
    out = []
    for b, bank in enumerate(b5):
        slots = [c if (i and c in need[b] and c not in bank[1:i]) else None for i, c in enumerate(bank)]
        slots[0] = bank[0]
        new = sorted(need[b] - set(c for c in slots[1:] if c))
        for i in range(1, 16):
            if slots[i] is None and new:
                slots[i] = new.pop(0)
        assert not new, ('bank overflow', b)
        out.append([tuple(int(x) for x in banks[b][i]) if slots[i] == bank[i] else
                    ((tuple(v << 3 for v in slots[i])) if slots[i] is not None else (0, 0, 0)) for i in range(16)])
    return out

def meta_index(i):
    """Metatile list position -> map id: the primary's 512 first, then the secondary's."""
    return i if i < P_META else 512 + (i - P_META)

def tile_index(i):
    return i if i < P_TILES else 512 + (i - P_TILES)

def remap(e):
    return (e & ~1023) | tile_index(e & 1023)

def pack(v, cells, banks, border_cells, fold_k=0, families=(), free=()):
    """cells: {(x, r): (lower RGB, upper RGBA, attr, bits, prefer)}; border_cells: four such tuples.
    Returns (words, border words, packer)."""
    banks = allocate(banks, list(cells.values()) + list(border_cells), v.backdrop)
    pk = Packer(v, banks)
    pk.fold_k = fold_k
    pk.families(families)
    pk.free_families = set(free)
    words = np.zeros((B.H, B.W), np.int64)
    for r in range(B.H):
        for x in range(B.W):
            low, up, attr, bits, prefer = cells[(x, r)]
            words[r, x] = meta_index(pk.metatile(low, up, attr, prefer, (x, r))) | bits
    border = [meta_index(pk.metatile(low, up, attr, prefer, 'border')) | bits for low, up, attr, bits, prefer in border_cells]
    assert not pk.misses, ('quadrants no bank holds', pk.misses[:5], len(pk.misses))
    assert len(pk.tiles) <= P_TILES + S_TILES, ('more tiles than both sheets hold', len(pk.tiles))
    assert len(pk.metas) <= P_META + S_META, ('more metatiles than both tilesets hold', len(pk.metas))
    return words, border, pk

def write(engine, v, words, border, pk):
    eng = engine
    def sheet(path, tiles, base_png):
        n = max(1, len(tiles))
        rows = (n + 15) // 16
        a = np.zeros((rows * 8, 128), np.uint8)
        for i, t in enumerate(tiles):
            a[(i // 16) * 8:(i // 16) * 8 + 8, (i % 16) * 8:(i % 16) * 8 + 8] = t
        im = Image.fromarray(a, 'P'); im.putpalette(Image.open(base_png).getpalette()); im.save(path)
    pdir, sdir = eng / B.PRIMARY, eng / B.SECONDARY
    sheet(pdir / 'tiles.png', pk.tiles[:P_TILES], v.base / B.PRIMARY / 'tiles.png')
    sheet(sdir / 'tiles.png', pk.tiles[P_TILES:], v.base / B.SECONDARY / 'tiles.png')
    for b in range(16):
        (pdir / f'palettes/{b:02d}.pal').write_text(B.jasc(pk.banks[b] if b < 6 else v.pals[0][b]))
        (sdir / f'palettes/{b:02d}.pal').write_text(B.jasc(pk.banks[b] if 6 <= b < 13 else v.pals[1][b]))
    metas = pk.metas
    for d, part in ((pdir, metas[:P_META]), (sdir, metas[P_META:])):
        (d / 'metatiles.bin').write_bytes(b''.join(struct.pack('<8H', *[remap(e) for e in ent]) for ent, _ in part))
        (d / 'metatile_attributes.bin').write_bytes(b''.join(struct.pack('<H', a) for _, a in part))
    (eng / B.LAYOUT / 'map.bin').write_bytes(struct.pack('<%dH' % words.size, *[int(w) for w in words.ravel()]))
    (eng / B.LAYOUT / 'border.bin').write_bytes(struct.pack('<4H', *[int(w) for w in border]))
