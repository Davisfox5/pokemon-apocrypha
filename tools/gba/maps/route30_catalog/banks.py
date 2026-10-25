"""Exact palette-bank packing (Route 43's pack_lossless.pack_sets and milp_sets, unchanged): every
tile's colour set must lie inside one bank of at most 15 colours."""
from __future__ import annotations
import numpy as np

def pack_sets(sets, nbanks, init=(), size=15, tries=200, seed=0):
    """Exact colour banks for a collection of tile colour sets: every set must lie inside one
    bank of at most `size` colours. Only maximal sets matter. Fixed banks (init) absorb what
    they already hold; each new bank is seeded with the largest unplaced set and grown with
    the set that adds the fewest new colours (ties: the larger set), until nothing fits.
    Randomised restarts keep the packing with the fewest banks. Returns banks or None."""
    distinct = set(sets)
    maximal = [c for c in distinct if not any(c < d for d in distinct)]
    rng = np.random.default_rng(seed)
    best = None
    for t in range(tries):
        banks = [set(b) for b in init]
        todo = sorted(maximal, key=lambda c: -len(c) - (rng.random() * 3 if t else 0))
        # fixed banks first: anything they hold or can take
        changed = True
        while changed and todo and banks:
            changed = False
            for c in list(todo):
                fits = [(len(c - b), -len(c & b), k) for k, b in enumerate(banks) if len(b | c) <= size]
                if fits and min(fits)[0] == 0:
                    todo.remove(c); changed = True
        for k, b in enumerate(banks):
            while True:
                fits = [(len(c - b), -len(c), i) for i, c in enumerate(todo) if len(b | c) <= size]
                if not fits:
                    break
                _, _, i = min(fits)
                b |= todo.pop(i)
        while todo:
            if len(banks) >= nbanks:
                break
            b = set(todo.pop(0))
            while True:
                fits = [(len(c - b), -len(c), i) for i, c in enumerate(todo) if len(b | c) <= size]
                if not fits:
                    break
                _, _, i = min(fits)
                b |= todo.pop(i)
            banks.append(b)
        if not todo and (best is None or len(banks) < len(best)):
            best = banks
    return best

def milp_sets(sets, nbanks, size=15, time_limit=300, fixed=(), force=()):
    """Exact bank assignment as an integer program (scipy / HiGHS): x[s,b] puts maximal set s in
    bank b, y[c,b] puts colour c in bank b; every set in one bank, its colours in that bank,
    at most `size` colours per bank. fixed pins a few sets to banks to break symmetry."""
    from scipy.optimize import milp, LinearConstraint, Bounds
    from scipy.sparse import lil_matrix
    cols = sorted(set().union(*sets)); ci = {c: i for i, c in enumerate(cols)}
    S, C, Bn = len(sets), len(cols), nbanks
    nx = S * Bn
    X = lambda s, b: s * Bn + b
    Y = lambda c, b: nx + c * Bn + b
    nv = nx + C * Bn
    rows = S + sum(len(x) for x in sets) * Bn + Bn
    A = lil_matrix((rows, nv)); lo = np.zeros(rows); hi = np.zeros(rows); r = 0
    for si in range(S):
        for b in range(Bn): A[r, X(si, b)] = 1
        lo[r] = hi[r] = 1; r += 1
    for si, st in enumerate(sets):
        for c in st:
            for b in range(Bn):
                A[r, X(si, b)] = 1; A[r, Y(ci[c], b)] = -1; lo[r] = -np.inf; hi[r] = 0; r += 1
    for b in range(Bn):
        for c in range(C): A[r, Y(c, b)] = 1
        lo[r] = 0; hi[r] = size; r += 1
    lb = np.zeros(nv); ub = np.ones(nv)
    for c, b in force:                                  # colours pinned to a bank (a family's own bank)
        lb[Y(ci[c], b)] = 1
    for si, b in fixed:
        for bb in range(Bn):
            if bb != b: ub[X(si, bb)] = 0
    res = milp(c=np.zeros(nv), constraints=LinearConstraint(A.tocsr(), lo, hi), integrality=np.ones(nv),
               bounds=Bounds(lb, ub), options=dict(time_limit=time_limit, disp=False))
    print('milp', res.status, res.message)
    if res.x is None or res.status not in (0,):
        return None
    xv = res.x[nx:].reshape(C, Bn) > 0.5
    banks = [set() for _ in range(Bn)]
    for si, st in enumerate(sets):
        b = int(np.argmax([res.x[X(si, bb)] for bb in range(Bn)]))
        banks[b] |= st
    return banks

