"""Route 32 terrain levels, counted from HGSS's own heights, and their audit.

One level is one HGSS height unit (one cliff band in HGSS's projection). Walkable and other non-rock ground
stands at the rounded height of its own ground pixels (lawn, road, tall grass, ledge, pier, stairs; woods and
other covered cells take the nearest ground); the sea at the coast floor level (SEA_LEVEL). A rock cell stands at its rock top (the upper
quartile of its rock pixels' heights).

Then the rules that make the Gen 3 terraces read as HGSS's:
  * clean: each level's region is closed (3x3) and opened (2x2), so no level has one-cell jogs or stubs;
    levels stay nested (a level only exists inside the one below it);
  * one level a cell: a rock cell stands at most one level above any of its eight neighbours, so a drop of k
    levels is k nested rims, and each rim runs on round every corner at the same level until it meets ground at
    its own height (a contour of a field like this cannot end in the middle of the rock);
  * no flat rock: a rock cell with no lower neighbour that touches ground at or above its level is raised one;
  * stairs stand at the levels of the wall they cut through (row by row, or column by column across a wall).

audit() walks every level contour of every rock mass and reports breaks; there must be none.
"""
from __future__ import annotations
import numpy as np
from scipy import ndimage

SEA_LEVEL = 1                         # HGSS's sea surface (0.5) is level with its beaches and coast floor (1.0)
GROUND_MATERIALS = ('egrass', 'road', 'grass', 'flower', 'etc_a', 'bridge', 'slope', 'allpeak')

def levels(topdown, grid, cells, rows0, walls):
    """topdown: (heights, material ids, material names, rgb) of HGSS's flat decode (Rf.topdown).
    grid: native material grid (rows); cells: the HGSS ledger; rows0: native rows above HGSS row 0 (padding).
    Returns (levels int array, rock bool array)."""
    h, mat, names, _ = topdown
    HH, HW = h.shape[0] // 16, h.shape[1] // 16
    H, W = len(grid), len(grid[0])
    cell = lambda a: a.reshape(HH, 16, HW, 16).transpose(0, 2, 1, 3).reshape(HH, HW, 256)
    hh = cell(h)
    rockpx = cell(np.isin(mat, [names.index(n) for n in walls if n in names]))
    gndpx = cell(np.isin(mat, [i for i, n in enumerate(names) if n.startswith(GROUND_MATERIALS)]))
    with np.errstate(all='ignore'):
        rtop = np.nanpercentile(np.where(rockpx, hh, np.nan), 75, -1)
        gnd = np.nanpercentile(np.where(gndpx, hh, np.nan), 50, -1)
    bad = np.isnan(gnd)
    _, (iy, ix) = ndimage.distance_transform_edt(bad, return_indices=True)
    gnd = gnd[iy, ix]
    R = np.array([[c in 'RXC' for c in row] for row in grid])
    water = np.zeros((H, W), bool)
    for y in range(rows0, H):
        for x in range(W):
            c = grid[y][x]
            water[y, x] = c in '~B' or (c in 'OX' and cells[y - rows0][x]['material'].startswith('sea'))
    R &= ~water
    L = np.zeros((H, W), int)
    for y in range(H):
        for x in range(W):
            if y < rows0:
                L[y, x] = int(round(gnd[0, x]))
            elif water[y, x]:
                L[y, x] = SEA_LEVEL
            elif R[y, x]:
                t = rtop[y - rows0, x]
                L[y, x] = int(np.floor((gnd[y - rows0, x] if np.isnan(t) else t) + 0.3))
            else:
                L[y, x] = int(round(gnd[y - rows0, x]))
    L = np.where(R, np.maximum(L, SEA_LEVEL + 1), L)  # rock stands above the sea, inside an islet as at its rim
    def lipschitz(L):
        for _ in range(12):
            changed = False
            for y in range(H):
                for x in range(W):
                    if not R[y, x]:
                        continue
                    nb = [L[b, a] for a in range(max(0, x - 1), min(W, x + 2)) for b in range(max(0, y - 1), min(H, y + 2)) if (a, b) != (x, y)]
                    if L[y, x] > min(nb) + 1:
                        L[y, x] = min(nb) + 1; changed = True
            if not changed:
                return L
        return L
    # A flight of stairs is cut through a wall and stands at the wall's own levels, row by row for a north-south
    # flight (the rock either side of each row), column by column for an east-west one (the rock above and below
    # each column, Route 30's rule: rock above and below the whole flight makes it east-west). The wall beside a
    # flight keeps its levels and faces right up to the treads; without rock beside it a flight takes its foot.
    st = np.array([[c == '^' for c in row] for row in grid])
    sl, sn = ndimage.label(st)
    rk = lambda x, y: 0 <= x < W and 0 <= y < H and R[y, x]
    flights = []
    for i in range(1, sn + 1):
        m = sl == i
        ys, xs = np.nonzero(m)
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        ring = ndimage.binary_dilation(m) & ~m & ~R
        foot = int(L[ring].min()) if ring.any() else int(L[m].min())
        ew = all(rk(x, y0 - 1) and rk(x, y1 + 1) for x in range(x0, x1 + 1))
        if ew:
            for x in range(x0, x1 + 1):
                side = [int(L[y, x]) for y in (y0 - 1, y1 + 1) if rk(x, y)]
                L[y0:y1 + 1, x] = max(side) if side else foot
        else:
            for y in range(y0, y1 + 1):
                side = [int(L[y, x]) for x in (x0 - 1, x1 + 1) if rk(x, y)]
                L[y, x0:x1 + 1] = max(side) if side else foot
        flights.append(m)
    L = lipschitz(L)
    for k in range(1, int(L.max()) + 1):
        m = L >= k
        mp = np.pad(m, 3, mode='edge')
        c = ndimage.binary_opening(ndimage.binary_closing(mp, np.ones((3, 3))), np.ones((2, 2)))[3:-3, 3:-3]
        if k > 1:
            c &= L >= k - 1
        L = np.where(R & c & (L < k), k, L)
        L = np.where(R & ~c & (L >= k), k - 1, L)
    # square the corners: wherever three cells of a 2x2 block are at level k or above and the fourth is rock one
    # below, the fourth joins level k (an outline with a one-cell step becomes a square corner); a cell of level k
    # with at most one orthogonal neighbour at k or above is a spur and drops a level. Top level down, repeated.
    for _ in range(4):
        changed = False
        for k in range(int(L.max()), 0, -1):
            for y in range(H - 1):
                for x in range(W - 1):
                    blk = [(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)]
                    inn = [c for c in blk if L[c[1], c[0]] >= k]
                    if len(inn) == 3:
                        (a, b), = [c for c in blk if c not in inn]
                        if R[b, a] and L[b, a] == k - 1:
                            L[b, a] = k; changed = True
            for y in range(H):
                for x in range(W):
                    if R[y, x] and L[y, x] == k:
                        nb = sum(1 for a, b in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
                                 if not (0 <= a < W and 0 <= b < H) or L[b, a] >= k)
                        if nb <= 1:
                            L[y, x] = k - 1; changed = True
        L = lipschitz(L)
        if not changed:
            break
    for _ in range(4):                                  # no flat rock at ground level
        L = lipschitz(L)
        raised = False
        for y in range(H):
            for x in range(W):
                if not R[y, x]:
                    continue
                nb = [(a, b) for a in range(max(0, x - 1), min(W, x + 2)) for b in range(max(0, y - 1), min(H, y + 2)) if (a, b) != (x, y)]
                lower = any(L[b, a] < L[y, x] for a, b in nb)
                flush = any(not R[b, a] and L[b, a] >= L[y, x] for a, b in nb)
                if flush and not lower:
                    L[y, x] += 1; raised = True
        if not raised:
            break
    return lipschitz(L), R

def audit(L, R):
    """Every rock mass, every level in it: the level's edge cells and whether the contour is contiguous (each
    edge cell of level k inside the mass touches another edge cell of level k, or the map edge, or ground at
    level >= k where the rim meets ground of its own height). Reports breaks; also the maximum drop between
    neighbours (must be 1 on rock)."""
    H, W = L.shape
    out = []
    lab, n = ndimage.label(R, structure=np.ones((3, 3)))
    worst = 0
    for y in range(H):
        for x in range(W):
            if R[y, x]:
                for a, b in ((x + 1, y), (x, y + 1), (x + 1, y + 1), (x - 1, y + 1)):
                    if 0 <= a < W and 0 <= b < H:
                        worst = max(worst, abs(int(L[y, x]) - int(L[b, a])) if R[b, a] else 0)
    for i in range(1, n + 1):
        m = lab == i
        ys, xs = np.nonzero(m)
        mass = dict(mass=i, cells=int(m.sum()), box=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                    levels={}, breaks=[])
        for k in sorted(set(L[m].tolist())):
            edge = m & (L == k) & ndimage.binary_dilation(L < k, np.ones((3, 3)))
            mass['levels'][int(k)] = int(edge.sum())
            for y, x in zip(*np.nonzero(edge)):
                ok = False
                for a in range(x - 1, x + 2):
                    for b in range(y - 1, y + 2):
                        if (a, b) == (x, y):
                            continue
                        if not (0 <= a < W and 0 <= b < H) or edge[b, a] or (not R[b, a] and L[b, a] >= k):
                            ok = True
                if not ok:
                    mass['breaks'].append([int(x), int(y), int(k)])
        out.append(mass)
    return dict(masses=out, max_rock_step=int(worst), breaks=sum(len(m['breaks']) for m in out))
