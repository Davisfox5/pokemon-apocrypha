"""Cherrygrove's elements in Johto's art, drawn on two whole-town layers (ground, objects).

Each element marks the cells it changes; install.py encodes them. Rows -2..-1 above the town are drawn too,
so the north wall and forest run on into Route 30's band exactly as the band draws them.
"""
from __future__ import annotations
import numpy as np
from scipy.ndimage import label

import base as B
from base import Rf, W, H
import rock as Rk                                    # noqa: E402  (route30_catalog: FRLG terraces, soft fringe)
from claude_cherrygrove import ground as G           # noqa: E402

R0 = -2                                              # first canvas row
FLOOR = 1

class Canvas:
    def __init__(self, town):
        self.town = town
        rows = H - R0
        self.ground = np.zeros((rows * 16, W * 16, 3), np.uint8)
        for r in range(R0, H):
            rr = min(max(r, 0), H - 1)
            self.ground[(r - R0) * 16:(r - R0 + 1) * 16] = town.img[rr * 16:(rr + 1) * 16]
        self.top = np.zeros((rows * 16, W * 16, 4), np.uint8)
        self.changed = set()                         # (x, r) cells drawn anew
        self.kit = {}                                # (x, r) -> (metatile, (collision, elevation)): placed by id
        self.trees = []                              # (x, root row, kind)
        self.notes = []
    def sl(self, x, r):
        return np.s_[(r - R0) * 16:(r - R0 + 1) * 16, x * 16:(x + 1) * 16]
    def put_ground(self, x, r, px):
        self.ground[self.sl(x, r)] = px
    def layers(self, x, r):
        return self.ground[self.sl(x, r)], self.top[self.sl(x, r)]

def lawn_plain():
    """Cherrygrove's lawn texture without its tufts (the tuft tones snapped to the plain dark lawn): the
    floor under the forests, two colours, so a quadrant where a blossom and a green crown meet over it fits
    one palette with them."""
    t = G.textures()[G.GRASS].copy()
    for c in ((96, 192, 144), (88, 176, 136)):
        t[(t == c).all(-1)] = (104, 200, 152)
    return t

def lawn_at(tex, x, r):
    yy, xx = np.mgrid[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16]
    return tex[yy % 32, xx % 32].astype(np.uint8)

def tree_sprites(town):
    """Cherrygrove's tree and blossom tree (T01 and its shadow; the blossom the same silhouette), cut from the
    town's standalone trees by the pixels that differ from its lawn."""
    lawn = G.textures()[G.GRASS]
    def cut(x0, y0):
        px = town.img[y0 * 16:(y0 + 3) * 16, x0 * 16:(x0 + 2) * 16]
        ys, xs = np.mgrid[y0 * 16:(y0 + 3) * 16, x0 * 16:(x0 + 2) * 16]
        a = (px != lawn[ys % 32, xs % 32]).any(-1)
        out = np.zeros((48, 32, 4), np.uint8); out[a, :3] = px[a]; out[a, 3] = 255
        return out
    green, blossom = cut(56, 5), cut(47, 5)
    assert ((green[..., 3] > 0) == (blossom[..., 3] > 0)).all(), 'the blossom tree is no longer the tree\'s silhouette'
    return dict(g=green, b=blossom)

def over(dst, src, x, y):
    h, w = src.shape[:2]
    sy0, sx0 = max(0, -y), max(0, -x)
    sy1, sx1 = min(h, dst.shape[0] - y), min(w, dst.shape[1] - x)
    s = src[sy0:sy1, sx0:sx1]; a = s[..., 3] > 0
    d = dst[y + sy0:y + sy1, x + sx0:x + sx1]; d[a] = s[a]

# --------------------------------------------------------------------------- the north edge (rock and forest)
WALL_X = [x + Rf.CG_OFFSET for x in sorted(Rf.WALL_COLS)]   # 40, 41
LAWN_X, RIM_X = 4 + Rf.CG_OFFSET, 7 + Rf.CG_OFFSET          # 39, 42 (the band's kit columns)
KIT_ROWS = range(0, 6)
CLIFF_ROWS = {7: 2, 8: 2, 9: 1}                      # terrace level per cliff row (HGSS rows 5-7: 2.9, 1.9, 1.3)
WEST_FOREST = (range(0, LAWN_X), range(0, 6))        # columns, rows of the north lattice west of the wall
EAST_FOREST = (range(Rf.CG_RIGHT_RIM, 70), range(0, 2), 2)   # columns, tree rows, the lawn row below them
NORTH = set((x, r) for r in WEST_FOREST[1] for x in WEST_FOREST[0]) | set((x, r) for r in range(0, 3) for x in EAST_FOREST[0])
SENTINEL = (248, 0, 248)                             # marks water under the rock in the render

def terrace_cell(x, r, town):
    hi, lo = FLOOR + 2, FLOOR + 1
    rock = lambda peak: dict(lab='R', floor='grass', ground=float(FLOOR), peak=float(peak))
    ground = lambda lvl, kind: dict(lab='.', floor=kind, ground=float(lvl), peak=float(lvl))
    if r in CLIFF_ROWS and x <= WALL_X[1]:
        return rock(hi if CLIFF_ROWS[r] == 2 and x <= WALL_X[0] else lo)
    if r < min(CLIFF_ROWS):
        if x < WALL_X[0]:
            return ground(hi, 'grass')                 # the plateau
        if x in WALL_X:
            return rock(hi if x == WALL_X[0] else lo)
    m = int(town.words[min(max(r, 0), H - 1), x]) & 1023
    if town.attr(m) & 0xFF == B.WATER_MB:
        return ground(FLOOR, 'water')
    if r > max(CLIFF_ROWS) and x <= WALL_X[1]:
        return ground(FLOOR, 'shore')                  # the beach and lawn at the cliff's foot: no cast shadow
    return ground(FLOOR, 'sand' if x in range(43, 46) else 'grass')

def north_edge(cv, engine):
    """The sea cliff and its turn north into Route 30's wall (rock.py's terraces in the HGSS ramp, the soft
    grass fringe), the north lattice (reference.py CG_ROOTS) and the kit beside the wall."""
    town = cv.town
    rows = range(R0, 12)
    cells = [[terrace_cell(x, r, town) for x in range(W)] for r in rows]
    d, isrock = Rk.terraces(cells, FLOOR)
    for x, r in sorted(NORTH):
        cv.put_ground(x, r, town.render_id(Rf.forest_ground(x, r)))
    tex = G.textures()
    water = np.zeros((16, 16, 3), np.uint8); water[:] = SENTINEL
    plain = dict(grass=tex[G.GRASS], sand=tex[G.PATH], water=water, shore=tex[G.GRASS][:16, :16])
    region = np.s_[0:len(rows) * 16]
    ground, over_, _ = Rk.rock_frlg(cells, d, isrock, cv.ground[region].copy(), Rk.frlg_pieces(engine), plain, soft=True)
    a = over_[..., 3] > 0
    ground[a] = over_[a, :3]
    cv.ground[region] = ground
    for i, r in enumerate(rows):
        for x in range(W):
            if isrock[i, x] and r >= 0:
                cv.changed.add((x, r))
    cv.changed |= {c for c in NORTH}
    for r in KIT_ROWS:
        cv.kit[(LAWN_X, r)] = (Rf.BAND_KIT[4][0][r % 2], B.BLOCKED)
        cv.kit[(RIM_X, r)] = (Rf.BAND_KIT[7][0][r % 2], B.OPEN)
    r = EAST_FOREST[2]
    for x in EAST_FOREST[0]:
        cv.kit[(x, r)] = (Rf.forest_ground(x, r), B.OPEN)
        cv.changed.discard((x, r))
    cv.trees += [(x, y, 'g') for x, y in Rf.CG_ROOTS]
    cv.trees += [(x + Rf.CG_OFFSET, y - Rf.H, 'g') for x, y in Rf.BAND_ROOTS]   # the band's, for their crowns' reach

# --------------------------------------------------------------------------- the forests
def woods_mask(town):
    m = np.zeros((H, W), bool)
    for y in range(H):
        for x in range(W):
            v = int(town.words[y, x])
            m[y, x] = (v >> 10) & 3 != 0 and bool(town.banks(v & 1023) & {3, 10})
    return m

# The east block's arm (x68-79, rows 20-32) is already the overlapping lattice, its pairs on even columns; the
# woods south of it pair on odd columns (x39 up). Each part keeps its own pairs, so no tree moves sideways,
# and both take the arm's row phase, so the south woods' top crowns overlap the arm's trunks.
ARM = (range(68, W), range(20, 33))

def forests(cv):
    """Every woods block not already on the lattice takes the route's tree lattice: 2x2 roots every two
    columns and rows, the crown rising into the row above (AGENTS.md, Johto trees). One row phase per block,
    so neighbouring columns never stagger: the phase of the lattice already there (the east arm), else the
    one that puts the trunks on the block's bottom row. A crown above a block's top row stands over the
    walkable cell there, drawn above the player. A tree is a blossom where the town's blossom stood."""
    town = cv.town
    woods = woods_mask(town)
    for x, r in NORTH | cv.changed | set(cv.kit):      # cells the north edge already drew or placed
        if 0 <= r < H:
            woods[r, x] = False
    lab, n = label(woods)
    pink = pink_mask(town)
    claimed = np.zeros_like(pink)
    lawn = lawn_plain()
    for i in range(1, n + 1):
        block = lab == i
        if block.sum() <= 6:
            continue                                 # a standalone tree is already a lattice of one
        ys, xs = np.nonzero(block)
        has_arm = block[ARM[1].start:ARM[1].stop, ARM[0].start:ARM[0].stop].all()
        phase = 1 if has_arm else (ys.max() - 1) % 2
        parts = [block]
        if has_arm:
            arm = np.zeros_like(block); arm[ARM[1].start:ARM[1].stop, ARM[0].start:ARM[0].stop] = True
            parts = [block & arm, block & ~arm]
        for part in parts:
            py, px = np.nonzero(part)
            x0, x1 = px.min(), px.max()
            assert (x1 - x0 + 1) % 2 == 0 or x1 == W - 1, ('a woods block of odd width inside the map', i, x0, x1)
            for x in range(x0, x1 + 1, 2):
                rows = sorted(set(py[(px == x) | (px == x + 1)].tolist()))
                top, bot = rows[0], rows[-1]
                y = bot - 1 if (bot - 1) % 2 == phase else bot
                assert y + 1 <= bot or bot == H - 1, ('a trunk below the woods', i, x, bot)
                while y >= top:                      # the last root sits on the top row or the row below it
                    cv.trees.append((x, y, 'b' if take_blossom(pink, claimed, x, y) else 'g'))
                    y -= 2
        for y, x in zip(ys, xs):
            cv.put_ground(x, y, lawn_at(lawn, x, y))
            cv.changed.add((x, y))
        cv.notes.append(f'woods block {i}: x{xs.min()}-{xs.max()} rows {ys.min()}-{ys.max()}, roots on '
                        f'{"odd" if phase else "even"} rows{", the east arm keeping its even column pairs" if has_arm else ""}')

def pink_mask(town):
    pal10 = town.t.pals[1][10]
    pinks = {tuple(c) for c in pal10[5:12]}
    img = town.img
    return np.isin(img.view([('r', 'u1'), ('g', 'u1'), ('b', 'u1')]).reshape(img.shape[:2]),
                   np.array(sorted(pinks), dtype=[('r', 'u1'), ('g', 'u1'), ('b', 'u1')]))

def take_blossom(pink, claimed, x, yr):
    """A lattice tree is a blossom when most of a blossom crown of the old town stands where its crown does."""
    sl = np.s_[(yr - 1) * 16 + 4:(yr + 1) * 16 - 4, x * 16:(x + 2) * 16]
    if yr - 1 < 0:
        sl = np.s_[0:(yr + 1) * 16 - 4, x * 16:(x + 2) * 16]
    hit = pink[sl] & ~claimed[sl]
    if hit.sum() < 120:
        return False
    claimed[max(0, (yr - 2) * 16):(yr + 2) * 16, x * 16:(x + 2) * 16] |= pink[max(0, (yr - 2) * 16):(yr + 2) * 16, x * 16:(x + 2) * 16]
    return True

def draw_trees(cv, sprites):
    for x, y, k in sorted(cv.trees, key=lambda t: (t[1], t[0])):
        over(cv.top, sprites[k], x * 16, (y - 1 - R0) * 16)
    for x, y, k in cv.trees:                          # a crown over the cell above a block: drawn anew, above the player
        for dx in (0, 1):
            c = (x + dx, y - 1)
            if 0 <= c[0] < W and 0 <= c[1] < H and c not in cv.kit:
                cv.changed.add(c)
