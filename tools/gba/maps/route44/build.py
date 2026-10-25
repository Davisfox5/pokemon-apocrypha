"""Palette and tile helpers (Mahogany's and Blackthorn's): 5-bit colour, JASC palettes,
behaviour ids, tile flips and the bank fitting used for tiles that no fixed palette holds
exactly. Route 44 uses rgb5, read_pal, behaviors and flips.
"""
from __future__ import annotations
import re
import numpy as np

CH_W = np.array([3.0, 4.0, 2.0])        # channel weights for colour error

# ----------------------------------------------------------------------------- helpers
def rgb5(a):
    return np.asarray(a, np.int32) >> 3

def read_pal(path):
    return [tuple(map(int, l.split())) for l in path.read_text().replace('\r', '').splitlines()[3:19]]

def behaviors(game):
    names = re.findall(r'^\s+(MB_[A-Z0-9_]+),', (game / 'include/constants/metatile_behaviors.h').read_text(), re.M)
    return {n: i for i, n in enumerate(names)}

def flips(t):
    """The four orientations of an 8x8 array, in (hflip, vflip) order 00, 10, 01, 11."""
    return [t, t[:, ::-1], t[::-1], t[::-1, ::-1]]

# ----------------------------------------------------------------------------- palettes
def kmeans_colors(colors, weights, k, init=None, iters=40):
    """Weighted k-means over unique RGB5 colours."""
    colors = colors.astype(float)
    if len(colors) <= k:
        return np.array(list(colors) + [colors[0]] * (k - len(colors))).astype(int)
    if init is None:
        cent = [colors[int(np.argmax(weights))]]
        for _ in range(k - 1):
            d = np.min([((colors - c) ** 2 * CH_W).sum(1) for c in cent], 0) * weights
            cent.append(colors[int(np.argmax(d))])
        cent = np.array(cent)
    else:
        cent = np.array(init, float)
    for _ in range(iters):
        lab = (((colors[:, None] - cent[None]) ** 2) * CH_W).sum(-1).argmin(1)
        new = cent.copy()
        for j in range(k):
            m = lab == j
            if m.any():
                new[j] = (colors[m] * weights[m, None]).sum(0) / weights[m].sum()
        if np.allclose(new, cent):
            break
        cent = new
    return np.clip(np.rint(cent), 0, 31).astype(int)

def tile_error(px, mask, pal):
    d = ((px[:, :, None, :] - pal[None, None]) ** 2 * CH_W).sum(-1).min(-1)
    return (d * mask).sum(1)

def fit_banks(jobs, nbanks, seed, scheme, rounds=25):
    """Assign tiles to banks and fit 15 colours per bank (alternating, k-means style)."""
    px = np.stack([j['px'] for j in jobs]).astype(float)
    mask = np.stack([j['mask'] for j in jobs]).astype(float)
    # How much a tile's usage counts: 'flat' (every distinct tile once, so a small
    # material is not outvoted by the mountain mass), 'sqrt' or 'log' (damped usage).
    use = np.array([j['weight'] for j in jobs], float)
    w = {'flat': np.ones(len(jobs)), 'sqrt': np.sqrt(use), 'log': 1 + np.log2(use)}[scheme]
    uc, inv = np.unique(px[mask > 0].astype(int), axis=0, return_inverse=True)
    glob = kmeans_colors(uc, np.bincount(inv.ravel()).astype(float), 48)
    lab = ((px[:, :, None, :] - glob[None, None]) ** 2 * CH_W).sum(-1).argmin(-1)
    hist = np.zeros((len(jobs), len(glob)))
    for i in range(len(jobs)):
        np.add.at(hist[i], lab[i], mask[i])
    hist /= np.maximum(hist.sum(1, keepdims=True), 1)
    rng = np.random.default_rng(seed)
    cent = hist[rng.choice(len(jobs), nbanks, replace=False, p=w / w.sum())]
    for _ in range(25):
        assign = ((hist[:, None] - cent[None]) ** 2).sum(-1).argmin(1)
        for k in range(nbanks):
            if (assign == k).any():
                cent[k] = np.average(hist[assign == k], 0, w[assign == k])
    pals = [None] * nbanks
    for _ in range(rounds):
        for k in range(nbanks):
            m = assign == k
            if not m.any():
                continue
            sel = mask[m] > 0
            cols = px[m][sel].astype(int)
            ww = np.repeat(w[m], 64).reshape(-1, 64)[sel]
            uc, inv = np.unique(cols, axis=0, return_inverse=True)
            pals[k] = kmeans_colors(uc, np.bincount(inv.ravel(), ww).astype(float), 15, init=pals[k])
        errs = np.stack([tile_error(px, mask, np.array(p, float)) if p is not None else np.full(len(jobs), np.inf)
                         for p in pals], 1)
        new = errs.argmin(1)
        if (new == assign).all():
            break
        assign = new
    total = float((errs.min(1) * w).sum() / (mask.sum(1) * w).sum())
    return pals, assign, total

def visible_loss(jobs, pals, assign):
    """Share of each material's map area whose colour moves by two or more 5-bit
    levels: the mean over materials plus the worst one, so a fit that keeps the
    mountain exact but flattens the pond glints or the bridge grain loses."""
    px = np.stack([j['px'] for j in jobs]).astype(float)
    mask = np.stack([j['mask'] for j in jobs]) > 0
    use = np.array([j['weight'] for j in jobs], float)
    mat = np.stack([j['material'] for j in jobs])
    pal = np.stack([np.array(p, float) for p in pals])[assign]                  # n,15,3
    q = np.take_along_axis(pal, (((px[:, :, None, :] - pal[:, None]) ** 2 * CH_W).sum(-1).argmin(-1))[..., None], 1)
    bad = (np.abs(q - px).max(-1) >= 2) & mask
    shares = []
    for m in np.unique(mat):
        area = ((mat == m) & mask) * use[:, None]
        if area.sum() >= 500:
            shares.append(float((area * bad).sum() / area.sum()))
    return float(np.mean(shares)) + max(shares)

def best_banks(jobs, nbanks, schemes, seeds=range(8)):
    fits = [fit_banks(jobs, nbanks, s, scheme) for scheme in schemes for s in seeds]
    return min(fits, key=lambda r: visible_loss(jobs, r[0], r[1]))
