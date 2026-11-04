"""Pack a group of rooms into one private tileset pair (primary + secondary), from scratch.

Every 8 px quadrant's colours must sit in one of the 13 banks (15 colours each; primary 0-5, secondary
6-12). Colours are reduced only as far as the packing needs: the two closest colours (by pixel count and
distance) merge until route29_catalog/banks.py packs every quadrant's set. Identical quadrants share one
tile in any flip; identical cells share one metatile. Tiles 0-511 and metatiles 0-511 go to the primary,
the rest to the secondary.
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'route29_catalog'), str(HERE.parent / 'route30_catalog')]
import banks as BK                       # noqa: E402

NB, SIZE = 13, 15
P_TILES, S_TILES, P_META, S_META = 512, 512, 512, 512
NORMAL, COVERED = 0, 1

def key5(a):
    a = np.asarray(a).astype(np.int64) >> 3
    return (a[..., 0] << 10) | (a[..., 1] << 5) | a[..., 2]

def rgb(k):
    k = np.asarray(k)
    c = np.stack([(k >> 10) & 31, (k >> 5) & 31, k & 31], -1)
    return (c << 3) | (c >> 2)

class Cell:
    """lower RGB 16x16, upper RGBA 16x16, behaviour, collision/elevation bits."""
    def __init__(self, low, up, behavior, bits):
        self.low, self.up, self.behavior, self.bits = low, up, behavior, bits

def quadrants(cells):
    """Each cell's 8 quadrant colour keys: (keys 8x8, opaque mask 8x8)."""
    out = []
    for c in cells:
        kl, ku = key5(c.low), key5(c.up[..., :3])
        mu = c.up[..., 3] > 0
        q = []
        for y, x in ((0, 0), (0, 8), (8, 0), (8, 8)):
            q.append((kl[y:y + 8, x:x + 8], np.ones((8, 8), bool)))
        for y, x in ((0, 0), (0, 8), (8, 0), (8, 8)):
            q.append((np.where(mu[y:y + 8, x:x + 8], ku[y:y + 8, x:x + 8], -1), mu[y:y + 8, x:x + 8]))
        out.append(q)
    return out

def _tile_palettes(quads, log, iters=12, seed=0):
    """Each 8 px quadrant gets one of NB banks of SIZE colours: exact when the quadrants' colour sets pack
    (route29_catalog/banks.py), otherwise k-means over tiles: each quadrant takes the bank that draws it
    with the least error, each bank's colours re-fit to the pixels of its quadrants. Returns banks (rgb5
    keys) and, per quadrant, (bank, 8x8 index array 0-15)."""
    uq, inv = {}, []
    for q in quads:
        for k, m in q:
            key = (k.tobytes(), m.tobytes())
            if key not in uq:
                uq[key] = (k, m)
            inv.append(key)
    keys = list(uq)
    sets = [frozenset(int(v) for v in np.unique(uq[t][0][uq[t][1]])) for t in keys]
    exact = None
    if all(len(c) <= SIZE for c in sets):
        exact = BK.pack_sets([c for c in sets if c], NB, tries=60)
    if exact is not None and len(exact) <= NB:
        banks = [sorted(b) for b in exact] + [[] for _ in range(NB - len(exact))]
        log.append(f'{len(set().union(*sets))} colours, exact')
        res = {}
        for t, c in zip(keys, sets):
            k, m = uq[t]
            if not c:
                res[t] = (0, np.zeros((8, 8), np.uint8)); continue
            b = min((len(banks[i]), i) for i in range(NB) if c <= set(banks[i]))[1]
            ix = np.zeros((8, 8), np.uint8)
            lut = {v: i + 1 for i, v in enumerate(banks[b])}
            ix[m] = [lut[int(v)] for v in k[m]]
            res[t] = (b, ix)
        return banks, [res[t] for t in inv], 0.0
    # k-means over tiles
    rng = np.random.default_rng(seed)
    px = [rgb(uq[t][0][uq[t][1]]).astype(np.float64) if uq[t][1].any() else np.zeros((0, 3)) for t in keys]
    weight = np.zeros(len(keys))
    for t in inv:
        weight[keys.index(t)] += 0
    from collections import Counter
    cnt = Counter(inv); w = np.array([cnt[t] for t in keys], np.float64)
    nonempty = [i for i, p in enumerate(px) if len(p)]
    # init: banks from the most-used tiles' colours, spread by farthest-first on mean colour
    means = np.array([px[i].mean(0) for i in nonempty])
    first = [nonempty[int(np.argmax(w[nonempty] * np.array([len(set(map(tuple, px[i]))) for i in nonempty])))]] if seed == 0 else [int(rng.choice(nonempty))]
    while len(first) < NB:
        d = np.min([((means - px[f].mean(0)) ** 2).sum(1) for f in first], axis=0)
        first.append(nonempty[int(np.argmax(d))])
    pals = []
    for f in first:
        u = np.unique(px[f], axis=0)
        pals.append(u[:SIZE] if len(u) >= 1 else np.zeros((1, 3)))
    def fit(points, ws, k):
        u, ix = np.unique(points, axis=0, return_inverse=True)
        uw = np.log1p(np.bincount(ix.ravel(), weights=ws, minlength=len(u)))   # rare colours keep their detail
        if len(u) <= k:
            return u
        c = u[np.argsort(-uw)[:k]].copy()
        for _ in range(15):
            d = ((u[:, None] - c[None]) ** 2).sum(-1); a = d.argmin(1)
            for j in range(k):
                sel = a == j
                if sel.any():
                    c[j] = (u[sel] * uw[sel, None]).sum(0) / uw[sel].sum()
        return np.round(c)
    assign = np.zeros(len(keys), int)
    for it in range(iters):
        for i in nonempty:
            errs = [(((px[i][:, None] - P[None]) ** 2).sum(-1).min(1)).sum() for P in pals]
            assign[i] = int(np.argmin(errs))
        for b in range(NB):
            mem = [i for i in nonempty if assign[i] == b]
            if not mem:
                continue
            pts = np.concatenate([px[i] for i in mem]); ws = np.concatenate([np.full(len(px[i]), w[i]) for i in mem])
            pals[b] = fit(pts, ws, SIZE)
    pal5 = [np.clip(np.round(P), 0, 255).astype(np.int64) >> 3 for P in pals]
    banks = [[int((c[0] << 10) | (c[1] << 5) | c[2]) for c in P] for P in pal5]
    banks = [sorted(set(b)) for b in banks]
    res, err = {}, 0.0
    for i, t in enumerate(keys):
        k, m = uq[t]
        if not m.any():
            res[t] = (0, np.zeros((8, 8), np.uint8)); continue
        q = rgb(k[m]).astype(np.float64)
        best = None
        for bb in range(NB):                         # the final banks: each quadrant takes its best one
            if not banks[bb]:
                continue
            P = rgb(np.array(banks[bb])).astype(np.float64)
            dd = ((q[:, None] - P[None]) ** 2).sum(-1)
            e = dd.min(1).sum()
            if best is None or e < best[0]:
                best = (e, bb, dd)
        _, b, d = best
        ix = np.zeros((8, 8), np.uint8); ix[m] = d.argmin(1) + 1
        err += float(d.min(1).sum()) * w[i]
        res[t] = (b, ix)
    log.append(f'{len(set().union(*sets))} colours, k-means over {len(nonempty)} quadrants into {NB} banks (seed {seed}, error {err:.0f})')
    return banks, [res[t] for t in inv], err

def near_merge(quads, thr):
    """Each colour onto the most used colour within thr 5-bit steps on every channel (greedy, by use)."""
    from collections import Counter
    cnt = Counter()
    for q in quads:
        for k, m in q:
            cnt.update(k[m].tolist())
    reps, rep = [], {}
    for c in sorted(cnt, key=lambda c: -cnt[c]):
        rc = np.array([(c >> 10) & 31, (c >> 5) & 31, c & 31])
        hit = next((r for r, rr in reps if np.abs(rr - rc).max() <= thr), None)
        if hit is None:
            reps.append((c, rc)); rep[c] = c
        else:
            rep[c] = hit
    lut = np.vectorize(lambda v: rep.get(int(v), int(v)) if v >= 0 else -1)
    return [[(np.where(m, lut(k), -1) if thr else k, m) for k, m in q] for q in quads], len(reps)

def refine(quads, banks, per, iters=8):
    """Start from a valid assignment (every quadrant in a bank that draws it); refit each bank's colours to
    its quadrants' original pixels (k-means, by use) and let quadrants move to a bank that draws them
    better. Squared error never rises, so no quadrant is drawn from a bank far from its colours."""
    flat = [(k, m) for q in quads for k, m in q]
    assign = [b for b, _ in per]
    px = [rgb(k[m]).astype(np.float64) for k, m in flat]
    pals = [rgb(np.array(b)).astype(np.float64) if b else np.zeros((0, 3)) for b in banks]
    def cost(i, P):
        if not len(px[i]) or not len(P):
            return 0.0 if not len(px[i]) else np.inf
        return ((px[i][:, None] - P[None]) ** 2).sum(-1).min(1).sum()
    for _ in range(iters):
        for b in range(NB):
            mem = [i for i, a in enumerate(assign) if a == b and len(px[i])]
            if not mem:
                continue
            pts = np.concatenate([px[i] for i in mem])
            u, ix = np.unique(pts, axis=0, return_inverse=True)
            uw = np.bincount(ix.ravel(), minlength=len(u)).astype(np.float64)
            if len(u) <= SIZE:
                pals[b] = u; continue
            c = pals[b].copy() if len(pals[b]) == SIZE else u[np.argsort(-uw)[:SIZE]].copy()
            for _ in range(10):
                a = ((u[:, None] - c[None]) ** 2).sum(-1).argmin(1)
                for j in range(SIZE):
                    sel = a == j
                    if sel.any():
                        c[j] = (u[sel] * uw[sel, None]).sum(0) / uw[sel].sum()
            new = np.round(c / 8).clip(0, 31) * 8 + np.round(c / 8).clip(0, 31) / 4
            new = np.floor(new)
            # keep the refit only if it draws this bank's quadrants no worse
            if sum(cost(i, new) for i in mem) <= sum(cost(i, pals[b]) for i in mem):
                pals[b] = new
        for i in range(len(flat)):
            if len(px[i]):
                cs = [cost(i, P) for P in pals]
                if min(cs) < cs[assign[i]]:
                    assign[i] = int(np.argmin(cs))
    keys = [sorted({int(((int(c[0]) >> 3) << 10) | ((int(c[1]) >> 3) << 5) | (int(c[2]) >> 3)) for c in P}) for P in pals]
    out = []
    for i, (k, m) in enumerate(flat):
        if not m.any():
            out.append((0, np.zeros((8, 8), np.uint8))); continue
        b = assign[i]; P = rgb(np.array(keys[b])).astype(np.float64)
        ix = np.zeros((8, 8), np.uint8)
        ix[m] = ((px[i][:, None] - P[None]) ** 2).sum(-1).argmin(1) + 1
        out.append((b, ix))
    return keys, out

def tile_palettes(quads, log, restarts=5, iters=20):
    for thr in (0, 1, 2, 3):                        # exact banks after merging only near-identical colours
        mq, n = near_merge(quads, thr)
        sets = {frozenset(int(v) for v in np.unique(k[m])) for q in mq for k, m in q if m.any()}
        if all(len(c) <= SIZE for c in sets) and BK.pack_sets(list(sets), NB, tries=100) is not None:
            sub = []
            r = _tile_palettes(mq, sub)
            if r[2] == 0.0 and sub and 'exact' in sub[-1]:
                if thr == 0:
                    log.append(f'exact ({n} colours)')
                    return r[0], r[1]
                banks, per = refine(quads, r[0], r[1])
                cand = [(score(quads, banks, per), banks, per, f'banks from merging colours within {thr} five-bit steps '
                         f'({n} colours), each refit to its quadrants\' original colours')]
                sub = []
                kb, kp = _kmeans_best(quads, sub, restarts, iters)
                cand.append((score(quads, kb, kp), kb, kp, sub[-1]))
                fixed = []
                for _, b, p, h in cand:
                    rb, rp, nf = repair(quads, b, p)
                    fixed.append((score(quads, rb, rp), rb, rp, h + f', {nf} quadrants repaired'))
                cand = fixed + cand
                sc, banks, per, how = min(cand, key=lambda c: c[0])
                log.append(f'{how}; score {sc:.2f} (alternative {max(c[0] for c in cand):.2f})')
                return banks, per
    return _kmeans_best(quads, log, restarts, iters)

def repair(quads, banks, per, bad=32, near=16):
    """Quadrants with a pixel more than `bad` off on a channel: their missing colours go into a bank, in a
    free slot or in place of a colour that has a near twin (within `near`) in the same bank; the quadrant
    moves there. Every quadrant is then redrawn from its bank's nearest colours."""
    flat = [(k, m) for q in quads for k, m in q]
    assign = [b for b, _ in per]
    banks = [list(b) for b in banks]
    C = lambda key: rgb(np.array([key]))[0].astype(np.int64)
    def missing(i, b):
        k, m = flat[i]
        if not m.any() or not banks[b]:
            return set(int(v) for v in np.unique(k[m])) if m.any() else set()
        cols = [int(v) for v in np.unique(k[m])]
        P = rgb(np.array(banks[b])).astype(np.int64)
        return {c for c in cols if np.abs(P - C(c)).max(1).min() > bad}
    fixed = 0
    for i in range(len(flat)):
        if not flat[i][1].any():
            continue
        need = missing(i, assign[i])
        if not need:
            continue
        for b in sorted(range(NB), key=lambda b: len(missing(i, b))):
            miss = missing(i, b)
            ok = True; plan = list(banks[b])
            for c in miss:
                if len(plan) < SIZE:
                    plan.append(c); continue
                P = rgb(np.array(plan)).astype(np.int64)
                d = np.abs(P[:, None] - P[None]).max(-1); np.fill_diagonal(d, 999)
                twins = [j for j in range(len(plan)) if d[j].min() <= near and plan[j] not in miss]
                if not twins:
                    ok = False; break
                plan[twins[0]] = c
            if ok:
                banks[b] = plan; assign[i] = b; fixed += 1
                break
    out = []
    for i, (k, m) in enumerate(flat):
        if not m.any():
            out.append((0, np.zeros((8, 8), np.uint8))); continue
        b = assign[i]
        P = rgb(np.array(banks[b])).astype(np.float64)
        q = rgb(k[m]).astype(np.float64)
        best = None
        for bb in range(NB):                        # each quadrant takes its best bank once more
            if not banks[bb]:
                continue
            PP = rgb(np.array(banks[bb])).astype(np.float64)
            dd = ((q[:, None] - PP[None]) ** 2).sum(-1)
            e = (dd.min(1) + 1e6 * (np.sqrt(dd.min(1)) > bad * 1.7)).sum()
            if best is None or e < best[0]:
                best = (e, bb, dd)
        _, b, dd = best
        ix = np.zeros((8, 8), np.uint8); ix[m] = dd.argmin(1) + 1
        out.append((b, ix))
    return banks, out, fixed

def score(quads, banks, per):
    """Mean channel error, plus a heavy charge for every pixel more than 32 off on a channel (a wrong colour)."""
    flat = [(k, m) for q in quads for k, m in q]
    tot = n = bad = 0
    for (k, m), (b, ix) in zip(flat, per):
        if not m.any():
            continue
        want = rgb(k[m]).astype(np.int64)
        got = rgb(np.array(banks[b])[ix[m] - 1]).astype(np.int64)
        e = np.abs(want - got)
        tot += e.sum(); n += e.size; bad += int((e.max(1) > 32).sum())
    return tot / max(1, n) + 2000.0 * bad / max(1, n)

def _kmeans_best(quads, log, restarts, iters):
    best = None
    for seed in range(restarts):
        sub = []
        r = _tile_palettes(quads, sub, iters=iters, seed=seed)
        if best is None or r[2] < best[0][2]:
            best = (r, sub)
        if r[2] == 0.0:
            break
    log += best[1]
    return best[0][0], best[0][1]

def pack(groups, log):
    """groups: {map name: (W, H, [Cell])}. Returns tiles, banks, metatiles, words per map."""
    allq = []
    order = []
    for name, (W, H, cs) in groups.items():
        qs = quadrants(cs)
        allq += qs
        order.append((name, W, H, cs, len(qs)))
    banks, per = tile_palettes(allq, log)
    tiles = [np.zeros((8, 8), np.uint8)]
    lookup = {tiles[0].tobytes(): 0}
    def tile(ix):
        for f in range(4):
            v = ix[:, ::-1] if f & 1 else ix
            v = v[::-1] if f & 2 else v
            t = lookup.get(v.tobytes())
            if t is not None:
                return t, f
        lookup[ix.tobytes()] = len(tiles); tiles.append(ix.copy())
        return len(tiles) - 1, 0
    def entry(b, ix):
        if not ix.any():
            return 0
        t, flip = tile(ix)
        return t | ((flip & 1) << 10) | ((flip >> 1) << 11) | (b << 12)
    metas, meta_id, words = [], {}, {}
    n = 0
    for name, W, H, cs, nq in order:
        out = np.zeros((H, W), np.int64)
        for i, c in enumerate(cs):
            ent = [entry(*per[n * 8 + j]) for j in range(8)]
            n += 1
            layer = NORMAL if any(e for e in ent[4:]) else COVERED
            key = (tuple(ent), c.behavior | (layer << 12))
            if key not in meta_id:
                meta_id[key] = len(metas); metas.append(key)
            out[i // W, i % W] = meta_id[key] | c.bits
        words[name] = out
    assert len(tiles) <= P_TILES + S_TILES, f'{len(tiles)} tiles'
    assert len(metas) <= P_META + S_META, f'{len(metas)} metatiles'
    log.append(f'{len(tiles)} tiles, {len(metas)} metatiles')
    pal = [[tuple(int(x) for x in rgb(v)) for v in b] for b in banks]
    return dict(tiles=tiles, banks=pal, metas=metas, words=words)

def jasc(cols):
    cols = list(cols)[:15] + [(0, 0, 0)] * (15 - len(cols[:15]))
    return '\r\n'.join(['JASC-PAL', '0100', '16', '0 0 0'] + [f'{r} {g} {b}' for r, g, b in cols]) + '\r\n'

def sheet(tiles):
    rows = max(1, (len(tiles) + 15) // 16)
    a = np.zeros((rows * 8, 128), np.uint8)
    for i, t in enumerate(tiles):
        a[(i // 16) * 8:(i // 16) * 8 + 8, (i % 16) * 8:(i % 16) * 8 + 8] = t
    im = Image.fromarray(a, 'P'); im.putpalette([v for i in range(16) for v in (i * 17, i * 17, i * 17)] + [0] * 720)
    return im

def write(engine, prim, sec, r):
    """Write the pair. Tile numbers in entries: primary 0-511, secondary 512+ (as the engine reads them)."""
    tiles, metas = r['tiles'], r['metas']
    for kind, name, t0, t1, m0, m1, b0, b1 in (('primary', prim, 0, P_TILES, 0, P_META, 0, 6),
                                                ('secondary', sec, P_TILES, P_TILES + S_TILES, P_META, P_META + S_META, 6, 13)):
        d = engine / 'data/tilesets' / kind / name
        (d / 'palettes').mkdir(parents=True, exist_ok=True)
        sheet(tiles[t0:t1] or [np.zeros((8, 8), np.uint8)]).save(d / 'tiles.png', bits=4)
        for b in range(16):
            (d / 'palettes' / f'{b:02d}.pal').write_text(jasc(r['banks'][b] if b0 <= b < b1 else []))
        part = metas[m0:m1] or [((0,) * 8, 0)]           # never an empty file (INCBIN)
        (d / 'metatiles.bin').write_bytes(b''.join(struct.pack('<8H', *e) for e, _ in part))
        (d / 'metatile_attributes.bin').write_bytes(b''.join(struct.pack('<H', a) for _, a in part))
