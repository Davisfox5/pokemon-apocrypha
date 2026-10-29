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
        self.pals = {}                               # bank -> colours, for banks the town's art fills anew
        self.fixed = {}                              # (x, r) -> metatile id the cell keeps (doors: the door table's)
        self.doors = []                              # door animations to cut from the new art (install.py)
        self.traverse = {}                           # (x, r) -> (collision, elevation, behaviour) where it changes
        self.exact = set()                           # cells whose tiles never fold (edges and features)
        self.notes = []
    def exactly(self, f, *a):
        """Run an element; every cell it draws stays exact in the install."""
        seen, self.changed = self.changed, set()
        f(self, *a)
        self.exact |= self.changed
        self.changed |= seen
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

# --------------------------------------------------------------------------- the sea islands
SEA_ROCKS = (0x097, 0x0AB)                           # the grey boulders (and the buoy line), kept as they are
ISLAND_ROWS = range(10, 30)

def island_cells(town):
    """Each island's footprint (its blocked cells in the bay that are not a boulder), split as HGSS's islands
    are: the upper plateau over the island's first two rows as far as its first row reaches, the lower ledge
    on the rest (south and east)."""
    foot = np.zeros((H, W), bool)
    for r in ISLAND_ROWS:
        for x in range(20):                          # west of the pier and its boats
            v = int(town.words[r, x])
            foot[r, x] = (v >> 10) & 3 != 0 and v & 1023 not in SEA_ROCKS and town.attr(v & 1023) & 0xFF != B.WATER_MB
    lab, n = label(foot)
    out = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        top = ys.min(); reach = xs[ys == top].max()
        cells = list(zip(xs.tolist(), ys.tolist()))
        out.append(({c for c in cells if c[1] <= top + 1 and c[0] <= reach}, set(cells)))
    return out

def islands(cv, engine):
    """The bay's islands in Johto rock (rock.py's terraces in the HGSS ramp, as the cliff): two levels, the
    sea under every rim (its animated tiles), the boulders and the buoy line kept."""
    town = cv.town
    up = set(); every = set()
    for u, a in island_cells(town):
        up |= u; every |= a
    rows = ISLAND_ROWS
    def cell(x, r):
        if (x, r) in every:
            return dict(lab='R', floor='water', ground=float(FLOOR), peak=float(FLOOR + (2 if (x, r) in up else 1)))
        return dict(lab='.', floor='water', ground=float(FLOOR), peak=float(FLOOR))
    cells = [[cell(x, r) for x in range(W)] for r in rows]
    d, isrock = Rk.terraces(cells, FLOOR)
    water = np.zeros((16, 16, 3), np.uint8); water[:] = SENTINEL
    region = np.s_[(rows.start - R0) * 16:(rows.stop - R0) * 16]
    pieces = Rk.frlg_pieces(engine)
    ground, over_, _ = Rk.rock_frlg(cells, d, isrock, cv.ground[region].copy(), pieces, dict(water=water))
    a = over_[..., 3] > 0
    ground[a] = over_[a, :3]
    # The plateau's lower corner over the sea on one side and the ledge below: rock.py takes the over-rock
    # piece, whose lip runs past the ledge's sea rim. Clip that quadrant to the ledge's own rim line.
    for x, r in up:
        for dx, q, side in ((-1, 0, 'W'), (1, 8, 'E')):
            if (x + dx, r) not in every and (x, r + 1) in every and (x, r + 1) not in up:
                rim = pieces['nine'][('M', side)][8:16, q:q + 8] >= 0
                y0 = (r - rows.start) * 16 + 8
                sub = ground[y0:y0 + 8, x * 16 + q:x * 16 + q + 8]
                sub[~rim] = SENTINEL
    cv.ground[region] = ground
    cv.changed |= every
    cv.notes.append(f'{len(every)} island cells, {len(up)} on the upper plateau')

# --------------------------------------------------------------------------- the beach's grass edges
WEDGE = (222, 206, 148)                              # a sand tone left in 8x8 wedges on the grass side of the edge
RIM = G.PROFILES[(G.GRASS, G.SAND)][0][0]            # the lawn's pale rim against the beach

def beach_edges(cv):
    """The beach's diagonal edges against the lawn: old tile reuse filled the wedge between the beach's 8 px
    steps and the diagonal with a darker sand (the only pixels of WEDGE in town). The wedges are beach again,
    and the edge takes the ground painter's beach/lawn rim (ground.py PROFILES) along the diagonal."""
    town = cv.town
    m = (town.img == WEDGE).all(-1)
    tex = G.textures()
    sand_tones = {tuple(c) for c in G.PROFILES[(G.GRASS, G.SAND)][1]} | {tuple(c) for c in tex[G.SAND].reshape(-1, 3)}
    lawn_tones = {tuple(c) for c in tex[G.GRASS].reshape(-1, 3)} | {RIM}
    grass_side, sand_side = G.PROFILES[(G.GRASS, G.SAND)]
    cells = sorted({(int(x) // 16, int(y) // 16) for y, x in zip(*np.nonzero(m))})
    for x, r in cells:
        y0, x0 = max(0, r * 16 - 8), max(0, x * 16 - 8)
        img = town.img[y0:(r + 1) * 16 + 8, x0:(x + 1) * 16 + 8]
        wedge = m[y0:(r + 1) * 16 + 8, x0:(x + 1) * 16 + 8]
        sand = wedge | np.array([[tuple(p) in sand_tones for p in row] for row in img])
        grass = ~wedge & np.array([[tuple(p) in lawn_tones for p in row] for row in img])
        to_grass, to_sand = G._chamfer(grass), G._chamfer(sand)
        yy, xx = np.mgrid[y0:y0 + img.shape[0], x0:x0 + img.shape[1]]
        px = img.copy()
        px[wedge] = tex[G.SAND][yy[wedge] % 32, xx[wedge] % 32]
        old_rim = sand & ~wedge & (to_grass > len(sand_side)) & np.isin(
            img.view([('r', 'u1'), ('g', 'u1'), ('b', 'u1')])[..., 0], np.array([tuple(c) for c in sand_side], dtype=[('r', 'u1'), ('g', 'u1'), ('b', 'u1')]))
        px[old_rim] = tex[G.SAND][yy[old_rim] % 32, xx[old_rim] % 32]   # the rim the old steps left inside the beach
        for i, c in enumerate(sand_side):
            px[sand & (to_grass == i + 1)] = c
        rim = grass & (to_sand == 1)
        px[rim] = grass_side[0]
        stale = grass & (to_sand > 1) & (img == RIM).all(-1)   # a rim pixel the old steps left inland
        px[stale] = tex[G.GRASS][yy[stale] % 32, xx[stale] % 32]
        oy, ox = r * 16 - y0, x * 16 - x0
        cv.put_ground(x, r, px[oy:oy + 16, ox:ox + 16]); cv.changed.add((x, r))
    cv.notes.append(f'beach edges: {len(cells)} cells, the sand wedges beach again')

# --------------------------------------------------------------------------- the pond
POND_SEED = 29
POND_BANK = 12                                       # the town's free secondary palette: the pond's tones

def pond(cv):
    """The pond as Route 30's ponds are (Route 43's pond(): Route 30's HGSS freshwater texture, a rough mud
    and grass bank, the shore about two pixels inside the water cells so the Surf boundary stays the cell
    edge). The old stone rim is lawn again first. The forest's lawn row above (placed by id) and the Center
    stay as they are; the bank forms below that row as if land stood there."""
    import assemble as As
    from scipy.ndimage import distance_transform_edt, gaussian_filter
    town = cv.town
    wet = np.zeros((H, W), bool)
    for r in range(0, 10):
        for x in range(60, 72):
            wet[r, x] = town.attr(int(town.words[r, x]) & 1023) & 0xFF == B.WATER_MB
    rs, xs = np.nonzero(wet)
    rows, cols = range(rs.min(), rs.max() + 2), range(xs.min() - 1, xs.max() + 2)
    win = np.s_[(rows.start - R0) * 16:(rows.stop - R0) * 16, cols.start * 16:cols.stop * 16]
    water = np.repeat(np.repeat(wet[rows.start - 1:rows.stop, cols.start:cols.stop], 16, 0), 16, 1)   # a land row above
    rng = np.random.default_rng(POND_SEED)
    h, w = water.shape
    soft = gaussian_filter(water.astype(float), 5, mode='nearest') > 0.5
    d = distance_transform_edt(soft) - distance_transform_edt(~soft)
    shore = d - 2 + 2.6 * As.smooth_noise(h, w, 14, rng) + 1.2 * As.smooth_noise(h, w, 6, rng) + 0.5 * As.smooth_noise(h, w, 3, rng)
    tuft = As.smooth_noise(h, w, 3, rng) + 0.5 * rng.uniform(-1, 1, (h, w))
    broken = As.smooth_noise(h, w, 5, rng)
    tex = np.concatenate([np.concatenate([As.rgba(As.SHARED / f'pond/pond-15-{r * 2 + c}.png')[..., :3] for c in (0, 1)], 1)
                          for r in (0, 1)], 0)
    ys, xs_ = np.mgrid[0:h, 0:w]
    yy, xx = ys + (rows.start - 1) * 16, xs_ + cols.start * 16                   # town pixels
    lawn = G.textures()[G.GRASS][yy % 32, xx % 32]
    img = town.img[(rows.start - 1) * 16:rows.stop * 16, cols.start * 16:cols.stop * 16]
    art = np.where(((distance_transform_edt(~water) <= 13) | water)[..., None], lawn, img).astype(np.uint8)   # the rim, lawn again
    def put(m, col):
        art[m] = col
    deep = tex[ys % 32, xs_ % 32]
    near = d > -6
    put(near & (shore >= 4.5), deep[near & (shore >= 4.5)])
    put(near & (shore >= 3.2) & (shore < 4.5) & (broken > -0.35), As.SHALLOW)
    m = near & (shore >= 3.2) & (shore < 4.5) & (broken <= -0.35); art[m] = deep[m]
    put(near & (shore >= 2.2) & (shore < 3.2), As.BANK)
    mud = near & (shore >= 0.3) & (shore < 2.2)
    put(mud, As.MUD)
    put(mud & (tuft > 0.75), As.GRASS_EDGE)
    put(mud & (tuft < -0.95), As.BANK)
    put(near & (shore >= -0.6) & (shore < 0.3), As.GRASS_DARK)
    centre = water & (ys % 16 == 8) & (xs_ % 16 == 8)
    assert (shore[centre] >= 3.2).all(), 'a water cell centre is not open water'
    # A cell holding other art away from the pond (the Center's edge) keeps its pixels but the old rim's,
    # which take the plain lawn tone, so the cell's own bank still fits it.
    tones = {tuple(c) for c in G.textures()[G.GRASS].reshape(-1, 3)} | {As.GRASS_EDGE, As.GRASS_DARK}
    is_lawn = np.array([[tuple(p) in tones for p in row] for row in img])
    other = ~is_lawn & (distance_transform_edt(~water) > 13) & ~water
    art, other, lawn = art[16:], other[16:], lawn[16:]   # drop the land row above
    cols5 = set()
    for r in rows:
        for x in cols:
            sl = np.s_[(r - rows.start) * 16:(r - rows.start + 1) * 16, (x - cols.start) * 16:(x - cols.start + 1) * 16]
            a = art[sl]
            if other[sl].any():                      # the old rim only, in the plain lawn tone
                a = town.img[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16].copy()
                rim = ~np.array([[tuple(p) in tones for p in row] for row in a]) & ~other[sl]
                a[rim] = As.GRASS_EDGE
            else:
                cols5 |= {tuple(int(v) >> 3 for v in c) for c in a.reshape(-1, 3)}
            if (a != town.img[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16]).any():
                cv.put_ground(x, r, a); cv.changed.add((x, r))
    assert len(cols5) <= 15, ('the pond needs more than one bank', len(cols5))
    cv.pals[POND_BANK] = sorted(tuple(v << 3 for v in c) for c in cols5)
    cv.notes.append(f'pond: water x{cols.start + 1}-{cols.stop - 2} rows {rows.start}-{rows.stop - 2}, {len(cols5)} tones in bank {POND_BANK}')

# --------------------------------------------------------------------------- the dirt paths
# Cherrygrove's paths had dashed grey rims and square corners. They take Route 30's road ground now: the
# ground painter's sand and its soft lawn rim (claude_cherrygrove/ground.py), the corners rounded as HGSS's
# are. Only lawn and path pixels change: houses, signs, fences, flowers and
# shadows keep every pixel. The path network is the town's own (path_grid); the cells the north edge,
# islands, pond, beach and forests drew keep their art.
GROUND_RIMS = {tuple(c) for side in G.PROFILES[(G.GRASS, G.PATH)] for c in side}
OLD_RIMS = {(128, 136, 120), (152, 144, 112)}        # the town's dashed rim and its dark sand line
ROUND = 6                                            # corner radius, px
PATH_SNAP = {(216, 168, 128): (216, 184, 128)}        # the texture's darkest pebbles, which the town's path never drew (no primary bank has them)

def ground_tones():
    tex = G.textures()
    return {tuple(c) for c in tex[G.GRASS].reshape(-1, 3)} | {tuple(c) for c in tex[G.PATH].reshape(-1, 3)} | GROUND_RIMS | OLD_RIMS

def path_grid(town):
    """'p' where a base cell's middle is mostly path, else 'g'."""
    path_t = {tuple(c) for c in G.textures()[G.PATH].reshape(-1, 3)}
    lawn_t = {tuple(c) for c in G.textures()[G.GRASS].reshape(-1, 3)}
    out = np.full((H, W), 'g', object)
    for r in range(H):
        for x in range(W):
            mid = [tuple(c) for c in town.img[r * 16 + 4:r * 16 + 12, x * 16 + 4:x * 16 + 12].reshape(-1, 3)]
            p, g = sum(c in path_t for c in mid), sum(c in lawn_t for c in mid)
            if p > g and p > 20:
                out[r, x] = 'p'
    return out

def disk(r):
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    return xx * xx + yy * yy <= r * r

def path_pixels(cells):
    """Per-pixel path mask over the town (rows 0..H-1): the cell grid, opened and closed with a disk so its
    convex and concave corners round off. The edges stay straight (the painter's wobble made every corner
    and run unique: more tiles than the sheets hold)."""
    from scipy.ndimage import binary_closing, binary_opening
    path = np.repeat(np.repeat(cells, 16, 0), 16, 1)
    pad = 2 * ROUND
    p = np.pad(path, pad, mode='edge')               # the roads run on past the map's edges
    p = binary_opening(binary_closing(p, disk(ROUND)), disk(ROUND))
    return p[pad:-pad, pad:-pad]

def paint_ground(path):
    """The painter's lawn and sand by absolute pixel, and its grass/path rim profile either side of the edge."""
    tex = G.textures()
    sand = tex[G.PATH].copy()
    for c, to in PATH_SNAP.items():
        sand[(sand == c).all(-1)] = to
    h, w = path.shape
    ys, xs = np.mgrid[0:h, 0:w]
    out = np.where(path[..., None], sand[ys % 32, xs % 32], tex[G.GRASS][ys % 32, xs % 32]).astype(np.uint8)
    pa, pb = G.PROFILES[(G.GRASS, G.PATH)]
    to_path, to_lawn = G._chamfer(path), G._chamfer(~path)
    for i, c in enumerate(pa):
        out[~path & (to_path == i + 1)] = c
    for i, c in enumerate(pb):
        out[path & (to_lawn == i + 1)] = c
    return out

def paths(cv, lots=()):
    """lots: (cells, banks) whose pixels in those banks (old buildings) are ground again too."""
    town = cv.town
    grid = path_grid(town)
    cells = grid == 'p'
    for x in BOARDWALK[0]:                           # the boardwalk joins the shore path: no rim on that side
        for r in BOARDWALK[1]:
            cells[r, x] = True
    for (x, r), w in DOOR_NOTCHES.items():           # each notch runs on under its building's bottom row
        cells[r - 1, x:x + w] = True
    path = path_pixels(cells)
    paint = paint_ground(path)
    tones = ground_tones()
    sand_sea = {tuple(c) for c in G.textures()[G.SAND].reshape(-1, 3)} | sea_tones(town)
    near = np.zeros((H, W), bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            near |= np.roll(np.roll(cells, dy, 0), dx, 1)
    clear = {}
    for cs, banks in lots:
        for c in cs:
            clear[c] = banks
            near[c[1], c[0]] = True
    n = px = 0
    for r in range(H):
        for x in range(W):
            if not near[r, x] or (x, r) in cv.changed or (x, r) in cv.kit or x in BOARDWALK[0] and r in BOARDWALK[1]:
                continue
            g = cv.ground[cv.sl(x, r)]
            keys = [[tuple(int(v) for v in p) for p in row] for row in g]
            if any(k in sand_sea for row in keys for k in row) and (x, r) not in clear:
                continue                             # the beach's and the sea's edges keep their art
            mask = np.array([[k in tones for k in row] for row in keys])
            if (x, r) in clear:
                mask |= np.isin(bank_map(town, x, r), clear[(x, r)])
            new = paint[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16]
            diff = mask & (g != new).any(-1)
            if diff.any():
                g[diff] = new[diff]; cv.changed.add((x, r)); n += 1; px += int(diff.sum())
    cv.notes.append(f'paths: the road painter in {n} cells ({px} pixels), corners rounded {ROUND} px')

# --------------------------------------------------------------------------- the approved Center and Mart
# gba/art/johto-common/approved-buildings.json (owner, October 15): C06 is the Johto Center, M01 the Johto
# Mart, both at Cherrygrove's own lots. The masters are transparent; the ground under them is the town's
# (paths()), the art draws on the object layer, pixel for pixel.
JOHTO = B.ART.parent
CENTER_ART, CENTER_AT, CENTER_DOOR = JOHTO / 'johto-center/source/building.png', (59, 5), (61, 9)
CENTER_PANEL = (32, 64, 48, 74)                      # C06's glass doors in the master (x0, y0, x1, y1)
CENTER_BANKS = (8, 9)                                # the old Center's and old Mart's secondary banks, free with them gone
MART_ART, MART_PAL = JOHTO / 'johto-mart/source/building.png', JOHTO / 'johto-mart/source/palette.pal'
MART_AT, MART_DOOR = (49, 4), (51, 9)
MART_PANEL = (35, 69, 49, 89)                        # M01's glass doors
MART_BANK = 2                                        # free in the town's copy
DOOR_NOTCHES = {(51, 10): 2, (61, 10): 2}            # the path notch below each door (its first cell, width)
OLD_LOTS = (({(x, r) for x in range(46, 58) for r in range(3, 12)}, (9,)),    # the old Mart and its flag sign
            ({(x, r) for x in range(56, 67) for r in range(3, 11)}, (8,)))    # the old Center

def rgba(p):
    from PIL import Image
    return np.array(Image.open(p).convert('RGBA'))

def building(cv, art, at, door, blocked_from):
    """The master on the object layer; its cells blocked from row blocked_from (the rows above draw over the
    player), but the door, which keeps its id (the door table's) and its behaviour."""
    town = cv.town
    x0, y0 = at[0] * 16, at[1] * 16
    over(cv.top, art, x0, y0 - R0 * 16)
    h, w = art.shape[0] // 16, art.shape[1] // 16
    for r in range(at[1], at[1] + h):
        for x in range(at[0], at[0] + w):
            cv.changed.add((x, r))
            if (x, r) == door:
                continue
            cv.traverse[(x, r)] = ((1, 3) if r >= blocked_from else (0, 3)) + (B.MB_NORMAL,)
    cv.fixed[door] = int(town.words[door[1], door[0]]) & 1023

def center(cv):
    art = rgba(CENTER_ART)
    a = art[..., 3] > 0
    cols = sorted({tuple(int(v) for v in c) for c in art[a][:, :3]})
    edge = set()                                     # colours of quadrants with ground showing: one bank holds them
    for y in range(0, art.shape[0], 8):
        for x in range(0, art.shape[1], 8):
            q = a[y:y + 8, x:x + 8]
            if q.any() and not q.all():
                edge |= {tuple(int(v) for v in c) for c in art[y:y + 8, x:x + 8][q][:, :3]}
    rest = [c for c in cols if c not in edge]
    assert len(edge) <= 15 and len(rest) <= 15, ('the Center needs a third bank', len(edge), len(rest))
    cv.pals[CENTER_BANKS[0]] = sorted(edge)
    cv.pals[CENTER_BANKS[1]] = rest
    building(cv, art, CENTER_AT, CENTER_DOOR, CENTER_AT[1] + 1)
    px0, py0, px1, py1 = CENTER_PANEL
    x0, y0 = CENTER_AT[0] * 16, CENTER_AT[1] * 16
    cv.doors.append(dict(name='center', cell=CENTER_DOOR, size='LEFT', banks=CENTER_BANKS + (0,),
                         panel=(x0 + px0, y0 + py0, x0 + px1, y0 + py1)))
    cv.notes.append(f'center: C06 at {CENTER_AT}, door {CENTER_DOOR}, banks {CENTER_BANKS}')

def mart(cv):
    """M01: its top row draws over the player, its wall rows are solid (johto-mart/README.md); the two cells
    the old Mart's flag sign blocked east of it are lawn and walkable."""
    art = rgba(MART_ART)
    pal = [tuple(int(v) for v in l.split()) for l in MART_PAL.read_text().splitlines()[4:19]]
    used = {tuple(int(v) for v in c) for c in art[art[..., 3] > 0][:, :3]}
    assert used <= set(pal), 'the Mart draws a colour outside its palette'
    cv.pals[MART_BANK] = [c for c in pal if c in used]
    building(cv, art, MART_AT, MART_DOOR, MART_AT[1] + 1)
    for x, r in ((54, 10), (55, 10)):
        cv.traverse[(x, r)] = (0, 3, B.MB_NORMAL)
    px0, py0, px1, py1 = MART_PANEL
    x0, y0 = MART_AT[0] * 16, MART_AT[1] * 16
    cv.doors.append(dict(name='mart', cell=MART_DOOR, size='LEFT', banks=(MART_BANK, 0), panel=(x0 + px0, y0 + py0, x0 + px1, y0 + py1)))
    cv.notes.append(f'mart: M01 at {MART_AT}, door {MART_DOOR}')

def bank_map(town, x, r):
    """The palette bank each pixel of a base cell draws in (-1 where nothing draws)."""
    m = int(town.words[r, x]) & 1023
    blk = town.t.blocks[int(m >= 512)][m - 512 if m >= 512 else m]
    out = np.full((16, 16), -1, int)
    for layer in (0, 1):
        for q in range(4):
            e = blk[layer * 4 + q]; i = e & 1023
            tiles = town.t.tiles[int(i >= 512)]
            j = i - 512 if i >= 512 else i
            if j >= len(tiles):
                continue
            t = np.array(tiles[j]).reshape(8, 8) % 16
            if e & 0x400: t = t[:, ::-1]
            if e & 0x800: t = t[::-1]
            sub = out[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            sub[t > 0] = e >> 12
    return out

# --------------------------------------------------------------------------- the forest's shore
# South of the beach the sea runs along the forest's west column (x38, ocean water, rows 28-47). It was a
# flat grey band with white dots; it takes the beach's own edge (sampled from the north beach: sea, foam,
# its pale wash, the sand rim, then sand) over the animated sea, wobbling as the beach does, and turns
# smoothly out of the beach's diagonal at rows 27-28.
SHORE_X, SHORE_ROWS = 38, range(28, H)
SHORE_EDGE = SHORE_X * 16 + 10                       # the sand's waterline, town pixels
FOAM, SAND_RIM = (200, 232, 224), (208, 208, 168)
WASH = FOAM                                          # the beach's pale wash is bank 4 only; over the animated sea the foam (bank 1) carries it

def shore(cv):
    """After the forests (their lawn is the ground this edges). Where a boulder stands on the strip
    (x38, rows 40-41) the boulder stays and only the old strip's pixels beside it change, the foam in the
    boulder's own bank's pale tone."""
    town = cv.town
    sand = G.textures()[G.SAND]
    img = town.img
    old = {tuple(int(v) for v in c) for c in img[30 * 16:32 * 16, SHORE_X * 16:(SHORE_X + 1) * 16].reshape(-1, 3)}
    def diag(y):                                     # the beach's waterline on a row above the strip
        row = img[y, 33 * 16:SHORE_X * 16 + 16]
        hit = np.nonzero((row == FOAM).all(-1))[0]
        return 33 * 16 + int(hit.max()) + 1 if len(hit) else SHORE_EDGE
    y_turn0, y_turn1 = 27 * 16, 29 * 16
    d0 = diag(y_turn0)
    for y in range(y_turn0, H * 16):
        wob = G.WAVE[y % 32] // 2
        e = SHORE_EDGE + wob if y >= y_turn1 else int(round(d0 + (SHORE_EDGE - d0) * (y - y_turn0) / (y_turn1 - y_turn0)))
        x0 = 36 * 16 if y < y_turn1 else SHORE_X * 16
        for x in range(x0, (SHORE_X + 1) * 16):
            cx, cy = x // 16, y // 16
            boulder = (int(town.words[cy, cx]) >> 10) & 3 != 0
            if boulder and tuple(int(v) for v in img[y, x]) not in old:
                continue                             # the boulder's own pixels
            k = x - e
            if k < -6:
                if boulder:
                    continue
                c = SENTINEL
            elif k < 0:
                c = BOULDER_FOAM if boulder else FOAM
            elif k == 0:
                c = SAND_RIM
            else:
                c = tuple(int(v) for v in sand[y % 32, x % 32])
            cv.ground[y - R0 * 16, x] = c
    for r in range(27, H):
        for x in (36, 37, SHORE_X):
            if r >= 29 and x < SHORE_X:
                continue
            cv.changed.add((x, r))
    cv.notes.append('shore: x38 rows 28-47 on the beach\'s edge')

BOULDER_FOAM = (214, 222, 222)                      # the boulders' bank (4) has this pale, not the beach foam
E_SEA = object()

# --------------------------------------------------------------------------- the pier, the boats, the sea
PIER = (range(25, 27), range(15, 23))               # the north-south pier, its post cap on row 15, its foot on the islet
BOARDWALK = (range(27, 38), (18, 19))                # the east-west run to the shore path
PIER_TEX = B.ART / 'source/hgss/pier.png'            # HGSS Route 32's pier (hgss_pier.py): 8 px rails, 32 px of boards
PIER_COLS = list(range(0, 8)) + list(range(16, 32)) + list(range(40, 48))   # the rails and the boards' middle 16 px
JOIN_COLS = list(range(0, 8)) + list(range(16, 40))  # where the boardwalk joins: the boards run on to the east edge
WOOD_MERGE = {(198, 165, 123): (206, 173, 132)}      # its rarest tone into the next, so the wood takes six slots
BEAM = (165, 132, 90)                                # its darkest tone: the end beams
WOOD_BANK = 9                                        # with the Center's roof tones (CENTER_BANKS)

def dock(cv):
    """The pier and boardwalk had dark plank seams every three pixels and a nail every few: they take HGSS's
    own pier (Route 32), a rail down each side and cross boards with their grain between, the boardwalk the
    same turned a quarter (its rails along the walk), a beam across each end."""
    tex = rgba(PIER_TEX)[..., :3].copy()
    for a, b in WOOD_MERGE.items():
        tex[(tex == a).all(-1)] = b
    wood = sorted({tuple(int(v) for v in c) for c in tex.reshape(-1, 3)})
    pier, join = tex[:, PIER_COLS], tex[:, JOIN_COLS]
    x0, y0, y1 = PIER[0].start * 16, PIER[1].start * 16, PIER[1].stop * 16
    for y in range(y0, y1):
        src = join if BOARDWALK[1][0] * 16 <= y < (BOARDWALK[1][-1] + 1) * 16 else pier
        row = src[y % 32].copy()
        if y < y0 + 2 or y >= y1 - 2:
            row[:] = BEAM
        cv.ground[y - R0 * 16, x0:x0 + 32] = row
    bx0, bx1 = BOARDWALK[0].start * 16, BOARDWALK[0].stop * 16
    by0 = BOARDWALK[1][0] * 16
    for x in range(bx0, bx1):
        col = pier[x % 32].copy()                    # turned: the rails run along the walk
        if x >= bx1 - 2:
            col[:] = BEAM
        cv.ground[by0 - R0 * 16:by0 - R0 * 16 + 32, x] = col
    for r in PIER[1]:
        for x in PIER[0]:
            cv.changed.add((x, r))
    for r in BOARDWALK[1]:
        for x in BOARDWALK[0]:
            cv.changed.add((x, r))
    pal = cv.pals.setdefault(WOOD_BANK, [])
    pal += [c for c in wood if c not in pal]
    assert len(pal) <= 15, ('the wood does not fit its bank', len(pal))
    cv.notes.append(f'dock: HGSS Route 32 pier boards, {len(wood)} tones in bank {WOOD_BANK}')

BOATS = dict(fishing=(27, 14, 29, 18), motorboat=(28, 23, 32, 26))   # the two small boats' cell boxes (boats.py)

def sea_tones(town):
    """Every colour the base town's open sea draws (its first frame)."""
    a = town.img[30 * 16:46 * 16, 2 * 16:30 * 16].reshape(-1, 3)
    return {tuple(int(v) for v in c) for c in np.unique(a, axis=0)}

def boats(cv):
    """The two small boats, redrawn clean on their own silhouettes in their own bank (boats.py). Where the
    old boat drew and the new one does not, the sea animates again. The large boat west of the pier is as
    the base town draws it."""
    import boats as Bt
    town = cv.town
    sea = sea_tones(town)
    for name, (x0, r0, x1, r1) in BOATS.items():
        base = town.img[r0 * 16:r1 * 16, x0 * 16:x1 * 16]
        old = ~np.array([[tuple(int(v) for v in p) in sea for p in row] for row in base])
        art = Bt.fishing() if name == 'fishing' else Bt.motorboat(old)
        g = cv.ground[(r0 - R0) * 16:(r1 - R0) * 16, x0 * 16:x1 * 16]
        a = art[..., 3] > 0
        g[old & ~a] = SENTINEL
        g[a] = art[..., :3][a]
        for r in range(r0, r1):
            for x in range(x0, x1):
                cv.changed.add((x, r))
        cv.notes.append(f'boats: the {name} redrawn, {int(a.sum())} pixels')

def keep_sea(cv):
    """In every redrawn cell, a pixel the base town drew from the sea's animated tiles and the cleanup left
    as it was is the sea again (the sentinel), so it keeps animating."""
    town = cv.town
    sea = sea_tones(town)
    n = 0
    for x, r in sorted(cv.changed):
        if not 0 <= r < H:
            continue
        anim = anim_map(town, x, r)
        if not anim.any():
            continue
        g = cv.ground[cv.sl(x, r)]
        is_sea = np.array([[tuple(int(v) for v in p) in sea for p in row] for row in g])
        same = (g == town.img[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16]).all(-1) & anim & is_sea
        g[same] = SENTINEL; n += int(same.sum())
    cv.notes.append(f'sea kept animated under {n} redrawn pixels')

def settle(cv):
    """Last: a cell an element redrew exactly as the base town draws it (same pixels, the sea animating on
    the same pixels, nothing above the player) keeps its id and its tiles."""
    town, n = cv.town, 0
    for x, r in sorted(cv.changed):
        if not 0 <= r < H or (x, r) in cv.fixed or (x, r) in cv.kit or (x, r) in cv.traverse:
            continue
        g, tp = cv.layers(x, r)
        if (tp[..., 3] > 0).any():
            continue
        m = int(town.words[r, x]) & 1023
        blk = town.t.blocks[int(m >= 512)][m - 512 if m >= 512 else m]
        if (town.attr(m) >> 12) & 3 == B.NORMAL and any(e & 1023 for e in blk[4:]):
            continue
        wet = (g == SENTINEL).all(-1)
        base = town.img[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16]
        if (wet != anim_map(town, x, r)).any() or ((g >> 3) != (base >> 3)).any(-1)[~wet].any():
            continue
        cv.changed.discard((x, r)); cv.exact.discard((x, r)); n += 1
    cv.notes.append(f'settle: {n} cells drawn as before keep their ids')

def anim_map(town, x, r):
    """Pixels of a base cell its sea animation draws (the topmost drawn tile is one of tiles 1-92)."""
    m = int(town.words[r, x]) & 1023
    blk = town.t.blocks[int(m >= 512)][m - 512 if m >= 512 else m]
    out = np.zeros((16, 16), bool)
    for layer in (0, 1):
        for q in range(4):
            e = blk[layer * 4 + q]; i = e & 1023
            tiles = town.t.tiles[int(i >= 512)]
            j = i - 512 if i >= 512 else i
            if j >= len(tiles):
                continue
            t = np.array(tiles[j]).reshape(8, 8) % 16
            if e & 0x400: t = t[:, ::-1]
            if e & 0x800: t = t[::-1]
            sub = out[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            sub[t > 0] = 1 <= i <= 92
    return out

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
            # the arm's columns (even pairs, as Route 29's forest across the seam) run on down to the map's
            # foot; west of them the woods keep their odd pairs
            east = np.zeros_like(block); east[:, ARM[0].start:] = True
            parts = [block & east, block & ~east]
        for part in parts:
            py, px = np.nonzero(part)
            x0, x1 = px.min(), px.max()
            single = (x1 - x0 + 1) % 2 == 1 and x1 != W - 1
            for x in range(x0, x1 + 1, 2):
                rows = sorted(set(py[(px == x) | (px == x + 1)].tolist()))
                top, bot = rows[0], rows[-1]
                y = bot - 1 if (bot - 1) % 2 == phase else bot
                assert y + 1 <= bot or bot == H - 1, ('a trunk below the woods', i, x, bot)
                at = x - 0.5 if single and x == x1 else x    # a leftover column: the tree straddles it, half a cell each way
                while y >= top:                      # the last root sits on the top row or the row below it
                    cv.trees.append((at, y, 'b' if take_blossom(pink, claimed, x, y) else 'g'))
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
    cv.canopy = set()                                 # cells a crown covers (the texture folds stay inside them)
    for x, y, k in sorted(cv.trees, key=lambda t: (t[1], t[0])):
        over(cv.top, sprites[k], int(round(x * 16)), (y - 1 - R0) * 16)
        cv.canopy |= {(int(x) + dx, y + dy) for dx in range(3 if x != int(x) else 2) for dy in (-1, 0)}
    for x, y, k in cv.trees:                          # a crown over the cell above a block: drawn anew, above the player
        for dx in ((0, 1) if x == int(x) else (0, 1, 2)):
            c = (int(x) + dx, y - 1)
            if 0 <= c[0] < W and 0 <= c[1] < H and c not in cv.kit:
                cv.changed.add(c)

