"""Violet gates, round 3: recompose the tree rows around both gatehouses, and add the house by the east gate.

Works on the installed Violet tileset and map (not on the base), and touches only the cells listed in ZONES
and HOUSE. Everything is drawn in painter's order from whole cut-outs (ground, trees behind the gate, the
gate, trees in front of it), then split back into tiles: one palette family per 8x8 tile and layer.

  python3 trees2.py ENGINE_ROOT OUT.pkl
"""
import pickle, sys, numpy as np
from pathlib import Path
from PIL import Image
from ts import TS

HERE = Path(__file__).resolve().parent
ENG = Path(sys.argv[1])
C = TS(str(ENG))
mt = [list(map(list, C.mt[0])), list(map(list, C.mt[1]))]
attr = [list(C.attr[0]), list(C.attr[1])]
sheets = [C.sheets[0].copy(), C.sheets[1].copy()]
pals = {b: C.pals[b].copy() for b in range(13)}
w = C.w.copy()
H, W = w.shape
TREE, GATE = 3, 2
LAWN_MT = [2, 3, 6, 7]                       # lawn metatile by (row parity, column parity)
LAWN_TILES = {0x1, 0x2, 0x3, 0x4, 0x9, 0xa, 0xb, 0xc, 0x10, 0x1c, 0x12, 0x1d, 0x1e, 0x17, 0x1f, 0x19}


def ents(m):
    m &= 1023
    return mt[0][m] if m < 512 else mt[1][m - 512]


def attr_of(m):
    m &= 1023
    return attr[0][m] if m < 512 else attr[1][m - 512]


def tile_idx(e):
    t = e & 1023
    sh = sheets[t >= 512]; i = t - 512 if t >= 512 else t
    v = sh[(i // 16) * 8:(i // 16) * 8 + 8, (i % 16) * 8:(i % 16) * 8 + 8]
    if e & 1024: v = v[:, ::-1]
    if e & 2048: v = v[::-1]
    return v


def rgba(e, lower):
    i = tile_idx(e); out = np.zeros((8, 8, 4), np.int16)
    out[..., :3] = pals[e >> 12][i]; out[..., 3] = 255
    if lower: out[i == 0, :3] = pals[0][0]
    else: out[i == 0] = 0
    return out


def over(dst, src):
    m = src[..., 3] > 0
    dst[m] = src[m]


def cell_pic(E):
    p = np.zeros((16, 16, 4), np.int16)
    for q in range(4):
        y, x = (q // 2) * 8, (q % 2) * 8
        p[y:y + 8, x:x + 8] = rgba(E[q], True)
        over(p[y:y + 8, x:x + 8], rgba(E[4 + q], False))
    return p


def lawn_ents(x, y):
    return ents(LAWN_MT[(y % 2) * 2 + x % 2])


# ---- cut-outs -------------------------------------------------------------------------------------
# One tree, 32x48 (43 px used), read from the lone tree's own tiles: no keying by colour.
T_ROWS = [[(0x3005, 0), (0x3006, 0), (0x300d, 0), (0x3405, 0)],
          [(0x3007, 0), (0x3008, 0), (0x300e, 0), (0x300f, 0)],
          [(0x3014, 0), (0x3011, 1), (0x3016, 1), (0x301a, 0)],
          [(0x3015, 0), (0x3013, 1), (0x3018, 1), (0x301b, 0)],
          [(0x311e, 0), (0x311f, 0), (0x3121, 0), (0x3122, 0)],
          [(0, 0), (0x3120, 0), (0x3123, 0), (0, 0)]]
tree = np.zeros((48, 32, 4), np.int16)
for r, row in enumerate(T_ROWS):
    for c, (e, opaque) in enumerate(row):
        if opaque: assert (tile_idx(e) != 0).all()
        tree[r * 8:r * 8 + 8, c * 8:c * 8 + 8] = rgba(e, False)
gate_w = np.array(Image.open(HERE / 'gate15.png').convert('RGBA')).astype(np.int16)
gate_w[gate_w[..., 3] == 0] = 0
GATES = {'west': (0, 400, gate_w), 'east': (1168, 848, gate_w[:, ::-1])}

# ---- layout ---------------------------------------------------------------------------------------
# Trees as (x, crown-top y) in pixels. The row behind each gate stands 32 px above the gate's origin and
# the row in front 96 px below it: the distances measured on the finished Route 31 and Route 36 gates.
# Between those and the untouched forest, rows sit 40 px apart so no half row is left over.
def rows(pairs, ys): return [(x, y) for x in pairs for y in ys]
BEHIND = {'west': rows((0, 32, 64, 96), (288, 328, 368)),
          'east': rows((1216, 1248), (736, 776, 816)) + rows((1184,), (776, 816))}
FRONT = {'west': rows((0, 32, 64), (496, 536, 576)) + rows((96,), (512, 544, 576)),
         'east': rows((1184, 1216, 1248), (944, 984, 1024)) + rows((1152,), (960, 992, 1024))}
ZONES = {'west': (0, 8, 20, 37), 'east': (72, 80, 48, 65)}     # x0, x1, y0, y1 in cells

cur = np.zeros((H * 16, W * 16, 4), np.int16)
for y in range(H):
    for x in range(W):
        cur[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = cell_pic(ents(int(w[y, x])))

zone_cells = set()
for side, (zx0, zx1, zy0, zy1) in ZONES.items():
    zone_cells |= {(x, y) for x in range(zx0, zx1) for y in range(zy0, zy1)}
stay = set()
for y in range(H):
    for x in range(W):
        if (x, y) not in zone_cells: stay.update(e & 1023 for e in ents(int(w[y, x])))
pidx = {b: set() for b in range(13)}
for y in range(H):
    for x in range(W):
        for i, e in enumerate(ents(int(w[y, x]))):
            v = set(np.unique(tile_idx(e)).tolist()); v.discard(0); pidx[e >> 12] |= v
plan = {}        # (x, y) -> [8 x ('e', entry) | ('n', bank, idx)], attr, collision or None
problems = []; NOTE = []


LOOK = {}
def index_tiles(tiles):
    for t in tiles:
        base = tile_idx(t)
        for fl, v in ((0, base), (1024, base[:, ::-1]), (2048, base[::-1]), (3072, base[::-1, ::-1])):
            for b in range(13):
                p = np.zeros((8, 8, 4), np.int16); p[..., :3] = pals[b][v]; p[..., 3] = 255; p[v == 0] = 0
                LOOK.setdefault(p.tobytes(), t | fl | (b << 12))


def need(pic, bank, lower):
    """A tile showing `pic`: an existing one in any bank if there is one, else a new one in `bank`."""
    k = pic.astype(np.int16).tobytes()
    if k in LOOK: return ('e', LOOK[k])
    P = pals[bank].astype(int); idx = np.zeros((8, 8), np.uint8)
    used = sorted(pidx[bank])
    for yy in range(8):
        for xx in range(8):
            if pic[yy, xx, 3] == 0: continue
            d = ((P[used] - pic[yy, xx, :3].astype(int)) ** 2).sum(-1)
            idx[yy, xx] = used[int(d.argmin())]
    if lower: assert (idx != 0).all()
    err = int(np.abs(P[idx] - pic[..., :3]).sum(-1)[pic[..., 3] > 0].max()) if (pic[..., 3] > 0).any() else 0
    return ('n', bank, idx, err)


def bank_with(pic, prefer):
    """A bank holding every colour of `pic`; failing that, the one needing the fewest added to unused slots."""
    cols = set(map(tuple, pic[pic[..., 3] > 0][:, :3].tolist()))
    best = None
    for b in prefer:
        have = set(tuple(int(v) for v in pals[b][k]) for k in pidx[b])
        miss = sorted(cols - have); spare = [k for k in range(1, 16) if k not in pidx[b]]
        if len(miss) <= len(spare) and (best is None or len(miss) < len(best[1])): best = (b, miss, spare)
    if best is None: return None
    b, miss, spare = best
    for c, k in zip(miss, spare):
        pals[b][k] = c; pidx[b].add(k); print('palette', b, 'slot', k, 'takes', c)
    return b


index_tiles(sorted(stay))
for side, (zx0, zx1, zy0, zy1) in ZONES.items():
    gx, gy, G = GATES[side]
    y0, y1, x0, x1 = zy0 * 16, zy1 * 16, zx0 * 16, zx1 * 16
    def layer(trees):
        L = np.zeros((H * 16, W * 16, 4), np.int16)
        for tx, ty in sorted(trees, key=lambda t: t[1]): over(L[ty:ty + 48, tx:tx + 32], tree)
        return L
    TB, TF = layer(BEHIND[side]), layer(FRONT[side])
    GA = np.zeros((H * 16, W * 16, 4), np.int16); GA[gy:gy + 112, gx:gx + 112] = G
    for cy in range(zy0, zy1):
        for cx in range(zx0, zx1):
            E = ents(int(w[cy, cx])); sl = (slice(cy * 16, cy * 16 + 16), slice(cx * 16, cx * 16 + 16))
            in_gate = gx <= cx * 16 < gx + 112 and gy <= cy * 16 < gy + 112
            lawnish = all((e & 1023) in LAWN_TILES or (e >> 12) == TREE for e in E[:4])
            tb, tf, ga = TB[sl], TF[sl], GA[sl]
            if not (in_gate or lawnish):
                if (tb[..., 3] > 0).any() or (tf[..., 3] > 0).any(): problems.append(('tree over foreign cell', cx, cy))
                continue
            LE = lawn_ents(cx, cy); ground = cell_pic(LE[:4] + [0, 0, 0, 0])
            P = ground.copy(); over(P, tb); over(P, ga); over(P, tf)
            if (P == cur[sl]).all(): continue
            out = []; lo = [None] * 4; up = [None] * 4
            for q in range(4):
                qs = (slice((q // 2) * 8, (q // 2) * 8 + 8), slice((q % 2) * 8, (q % 2) * 8 + 8))
                g, b_, f_, gr = ga[qs], tb[qs].copy(), tf[qs], ground[qs]
                b_[g[..., 3] > 0] = 0                                   # behind the gate: hidden
                has_g, has_b, has_f = (g[..., 3] > 0).any(), (b_[..., 3] > 0).any(), (f_[..., 3] > 0).any()
                same = (P[qs] == cur[sl][qs]).all()
                if not has_g:
                    t = b_.copy(); over(t, f_)
                    lo[q] = ('e', LE[q]); up[q] = need(t, TREE, False) if (t[..., 3] > 0).any() else ('e', 0)
                elif same and not has_b and not has_f:
                    lo[q] = ('e', E[q]); up[q] = ('e', E[4 + q])
                elif has_f and not has_b:
                    base = gr.copy(); over(base, g)
                    cl = rgba(E[q], True)
                    seen = (g[..., 3] > 0) & (f_[..., 3] == 0)          # gate pixels the tree leaves in view
                    if not seen.any():
                        lo[q] = ('e', LE[q])
                    elif (cl == base).all(): lo[q] = ('e', E[q])
                    elif base.astype(np.int16).tobytes() in LOOK: lo[q] = need(base, 0, True)
                    else:
                        b = bank_with(base, [7, 12, 0, 1, 4, 10, 5, 6, 9, 2])
                        if b is not None: lo[q] = need(base, b, True)
                        else:
                            # no bank holds lawn and all of the gate's colours here: the tree bank takes the lawn,
                            # the tree and the gate pixels it has colours for; the rest of the gate goes on top
                            have3 = set(tuple(int(v) for v in pals[TREE][k]) for k in pidx[TREE])
                            in3 = np.array([[tuple(int(v) for v in g[yy, xx, :3]) in have3 for xx in range(8)] for yy in range(8)])
                            lowpic = gr.copy(); m = seen & in3; lowpic[m] = g[m]; over(lowpic, f_)
                            top = np.zeros_like(g); m = seen & ~in3; top[m] = g[m]
                            lo[q] = need(lowpic, TREE, True); up[q] = need(top, GATE, False); NOTE.append(('split', cx, cy, q)); continue
                    up[q] = need(f_, TREE, False)
                elif has_b and not has_f:
                    base = gr.copy(); over(base, tb[qs])        # what the gate hides may as well be the whole tree
                    lo[q] = need(base, TREE, True); up[q] = need(g, GATE, False)
                elif not has_b and not has_f:
                    lo[q] = ('e', LE[q]); up[q] = need(g, GATE, False)
                else:
                    problems.append(('trees both sides of the gate', cx, cy, q)); lo[q] = ('e', E[q]); up[q] = ('e', E[4 + q])
            has_tree = (tb[..., 3] > 0).any() or (tf[..., 3] > 0).any()
            if in_gate: a, col = attr_of(int(w[cy, cx])), None
            else: a, col = 0x0000, (1 if has_tree else 0)
            plan[(cx, cy)] = (lo + up, a, col, P)

# ---- the house by the east gate ---------------------------------------------------------------------
# The same house as the one at (9..13, 33..38), tile for tile, set on the north edge of the road so the
# paving meets its door step. Ground quarters take the ground of the new spot; house tiles are kept.
HOUSE_SRC, HOUSE_DST = (9, 33), (69, 38)
house_cells = {}
for dy in range(6):
    for dx in range(5):
        sx, sy = HOUSE_SRC[0] + dx, HOUSE_SRC[1] + dy; x, y = HOUSE_DST[0] + dx, HOUSE_DST[1] + dy
        SE = ents(int(C.w[sy, sx])); DE = ents(int(w[y, x]))
        dest_ground = DE[:4] if all((e >> 12) != TREE for e in DE[:4]) and not any(DE[4:]) else lawn_ents(x, y)[:4]
        if any((e >> 12) == TREE for e in DE): dest_ground = lawn_ents(x, y)[:4]
        E = []
        for q in range(4):
            E.append(dest_ground[q] if (SE[q] >> 12) == 0 and (SE[q] & 1023) in LAWN_TILES else SE[q])
        E += SE[4:]
        if E == DE: continue
        col = (int(C.w[sy, sx]) >> 10) & 3
        if (sx, sy) == (10, 37): col = 1                # the door: no interior yet, so it is solid
        P = cell_pic(E)
        house_cells[(x, y)] = ([('e', e) for e in E], attr_of(int(C.w[sy, sx])), 1 if col else 0, P)
plan.update(house_cells)

print(NOTE)
# ---- behind Sprout Tower ----------------------------------------------------------------------------
# The top roof stands in the air over the ground behind the tower. Its two top rows become open ground the
# player walks behind: same tiles (the roof is already all on the top layer), layer type normal so it is
# drawn over the player. The spire's cells in the row above draw over the player's head the same way.
for y in (3, 4):
    for x in range(36, 43):
        E = ents(int(w[y, x])); assert all((e & 1023) == 0 or (e & 1023) in LAWN_TILES for e in E[:4]), (x, y)
        plan[(x, y)] = ([('e', e) for e in E], attr_of(int(w[y, x])) & 0x0FFF, 0, cell_pic(E))
for x in range(38, 42):
    E = ents(int(w[2, x]))
    if any(e >> 12 == 7 for e in E[4:]) and all(e == 0 or e >> 12 == 7 for e in E[4:]):   # spire only, no tree foot
        plan[(x, 2)] = ([('e', e) for e in E], attr_of(int(w[2, x])) & 0x0FFF, None, cell_pic(E))

if problems:
    for p in problems: print('PROBLEM', p)

# ---- tiles ----------------------------------------------------------------------------------------
used = set()
for y in range(H):
    for x in range(W):
        if (x, y) in plan: continue
        used.update(e & 1023 for e in ents(int(w[y, x])))
for E, a, col, P in plan.values():
    used.update(v[1] & 1023 for v in E if v[0] == 'e')
used.add(0)
free = [t for t in range(1, 1008) if t not in used]
print('cells rebuilt', len(plan), 'free tile slots', len(free))
store = {}
for t in sorted(used):
    i = tile_idx(t)
    for fl, v in ((0, i), (1024, i[:, ::-1]), (2048, i[::-1]), (3072, i[::-1, ::-1])):
        store.setdefault(v.tobytes(), (t, fl))
new_count = 0; worst = 0; LOG = []; CELL = None; NEWT = []; BAKED = []


def place(v):
    global new_count, worst
    if v[0] == 'e': return v[1]
    _, bank, idx, err = v; worst = max(worst, err); LOG.append((CELL, bank, err))
    k = idx.tobytes()
    if k not in store:
        P = pals[bank]; lawn = [i for i in range(1, 16) if tuple(int(c) for c in P[i]) in ((104, 208, 152), (104, 200, 152))]
        if len(lawn) == 2:
            for (b2, i2, tfl) in BAKED:
                if b2 != bank: continue
                for fl, f in ((0, lambda a: a), (1024, lambda a: a[:, ::-1])):
                    a = f(i2); d = a != idx
                    if not d.any() or (np.isin(a[d], lawn).all() and np.isin(idx[d], lawn).all()):
                        t0, f0 = tfl; store[k] = (t0, f0 ^ fl); break
                if k in store: break
    if k not in store:
        if not free: print('OUT OF TILES'); free.append(1007 - new_count)
        t = free.pop(0); new_count += 1; NEWT.append((CELL, bank, idx.copy())); BAKED.append((bank, idx.copy(), (t, 0)))
        sh = sheets[t >= 512]; i = t - 512 if t >= 512 else t
        sh[(i // 16) * 8:(i // 16) * 8 + 8, (i % 16) * 8:(i % 16) * 8 + 8] = idx
        for fl, vv in ((0, idx), (1024, idx[:, ::-1]), (2048, idx[::-1]), (3072, idx[::-1, ::-1])):
            store.setdefault(vv.tobytes(), (t, fl))
    t, fl = store[k]
    return t | fl | (bank << 12)


newmt = []
def add_mt(E, a):
    for part in (0, 1):
        for n, (E2, a2) in enumerate(zip(mt[part], attr[part])):
            if E2 == E and a2 == a: return part * 512 + n
    mt[1].append(list(E)); attr[1].append(a); newmt.append(E)
    return 512 + len(mt[1]) - 1


bad = 0
for (x, y), (E, a, col, P) in sorted(plan.items()):
    CELL = (x, y); E2 = [place(v) for v in E]
    if not (cell_pic(E2) == P).all(): bad += 1; print("inexact", (x, y), int(np.abs(cell_pic(E2) - P).max()), int((cell_pic(E2) != P).any(-1).sum()))
    word = int(w[y, x]); c = (word >> 10) & 3
    if col is not None: c = (c or 1) if col else 0
    w[y, x] = (word & 0xF000) | (c << 10) | add_mt(E2, a)
print('new tiles', new_count, 'left', len(free), 'new metatiles', len(newmt), 'secondary metatiles', len(mt[1]),
      'cells not pixel-exact', bad, 'worst colour error', worst)
assert len(mt[1]) <= 512
sheet = np.zeros((10, len(NEWT) * 10, 3), np.uint8) + np.array([255, 0, 255], np.uint8)
for n, (cell, bank, idx) in enumerate(NEWT):
    c = pals[bank][idx]; c[idx == 0] = (255, 0, 255); sheet[1:9, n * 10 + 1:n * 10 + 9] = c
Image.fromarray(sheet).resize((sheet.shape[1] * 8, 80), Image.NEAREST).save(str(HERE / 'newtiles.png'))
print('new tiles at', sorted(set(c for c, b, i in NEWT)))
pickle.dump((mt, attr, sheets, pals, w), open(sys.argv[2], 'wb'))
