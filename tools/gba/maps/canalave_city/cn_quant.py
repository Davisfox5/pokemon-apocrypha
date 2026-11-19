"""Tile-palette quantisation: every 8x8 tile takes one of K banks of 15 colours (RGB555)."""
import numpy as np

def kmeans_w(pts, w, k, init=None, rounds=12, rng=None):
    rng = rng or np.random.default_rng(0)
    n = len(pts)
    if n <= k:
        return pts.copy()
    if init is None or len(init) < k:
        cen = [pts[np.argmax(w)]]
        d = ((pts - cen[0]) ** 2).sum(1)
        while len(cen) < k:
            i = int(np.argmax(d * np.sqrt(w)))
            cen.append(pts[i]); d = np.minimum(d, ((pts - pts[i]) ** 2).sum(1))
        cen = np.array(cen, float)
    else:
        cen = np.array(init, float)
    for _ in range(rounds):
        dist = ((pts[:, None, :] - cen[None]) ** 2).sum(2)
        a = dist.argmin(1)
        for j in range(k):
            m = a == j
            if m.any():
                cen[j] = (pts[m] * w[m, None]).sum(0) / w[m].sum()
            else:
                i = int(np.argmax(dist.min(1) * w)); cen[j] = pts[i]
    return cen

def quantise(T, cols, K, fixed=None, rounds=25, seed=0, n=15, lock=None):
    """T: tiles x colours pixel counts; cols: colours x 3 (5-bit). fixed: {bank: [colours]} kept as they are.
    lock: {tile index: bank}. Returns (bank per tile, list of K arrays of <= n integer colours)."""
    fixed = fixed or {}; lock = lock or {}
    rng = np.random.default_rng(seed)
    cols = cols.astype(float)
    present = T > 0
    wt = T.sum(1)
    mean = (T @ cols) / wt[:, None]
    # start: k-means over tile mean colours
    cen = kmeans_w(mean, wt.astype(float), K, rounds=20)
    assign = ((mean[:, None] - cen[None]) ** 2).sum(2).argmin(1)
    for t, b in lock.items(): assign[t] = b
    pals = [None] * K
    for it in range(rounds):
        D = np.zeros((K, len(cols)))
        for k in range(K):
            fx = np.array(fixed.get(k, []), float).reshape(-1, 3)
            free = n - len(fx)
            w = T[assign == k].sum(0).astype(float)
            m = w > 0
            if m.any() and free > 0:
                if len(fx):
                    # colours a fixed entry already draws exactly need no slot
                    dfx = ((cols[:, None] - fx[None]) ** 2).sum(2).min(1)
                    w = np.where(dfx < 0.5, 0, w); m = w > 0
                init = None
                if pals[k] is not None and len(pals[k]) - len(fx) == free:
                    init = pals[k][len(fx):]
                c = kmeans_w(cols[m], w[m], free, init=init) if m.any() else np.zeros((0, 3))
                pals[k] = np.vstack([fx, c]) if len(fx) else c
            elif len(fx):
                pals[k] = fx
            else:
                pals[k] = cols[[int(rng.integers(len(cols)))]]
            D[k] = ((cols[:, None] - pals[k][None]) ** 2).sum(2).min(1)
        cost = T @ D.T
        new = cost.argmin(1)
        for t, b in lock.items(): new[t] = b
        if (new == assign).all() and it > 3:
            break
        assign = new
    out = []
    for k in range(K):
        p = np.clip(np.rint(pals[k]), 0, 31).astype(int)
        seen = []
        for c in map(tuple, p):
            if c not in seen: seen.append(c)
        out.append(np.array(seen).reshape(-1, 3))
    D = np.stack([((cols[:, None] - p[None]) ** 2).sum(2).min(1) for p in out])
    cost = T @ D.T
    assign = cost.argmin(1)
    for t, b in lock.items(): assign[t] = b
    return assign, out, cost[np.arange(len(T)), assign]
