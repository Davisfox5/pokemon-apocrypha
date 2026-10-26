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

# --------------------------------------------------------------------------- the houses
# Each house: its sprite (houses.py), mirrored or not, and the door warp it stands on. The pink skylight
# house has its door on its third column, as HGSS's model mirrored (the owner's town); the others on their
# second, as HGSS's.
HOUSES = dict(player=('skylight', True, 43, 17), gold=('gable', False, 54, 19), neighbor=('teal', False, 64, 24),
              harbor=('teal', False, 52, 31), garden=('gable', False, 65, 31))
OLD_HOUSE_BANKS = (6, 7)                             # the old houses' banks (pink and red 6, teal 7)
HOUSE_BANK = dict(skylight=6, gable=6, teal=2)       # 2: the town's copy has it free; 6: the old pink and red
LAWN = (104, 208, 152)                               # the lawn tone each house bank keeps for its door frames

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

def houses(cv):
    """The houses as HGSS's models at C06's angle (houses.py), each on its own footprint and door cell. The
    old house's pixels (its banks inside its box) are lawn again; the door cells keep their metatile ids,
    so the door table finds them, and the install cuts their open frames from the new art."""
    import json
    from PIL import Image
    town = cv.town
    src = B.ART / 'source/houses'
    info = json.loads((src / 'houses.json').read_text())['sprites']
    lawn = G.textures()[G.GRASS]
    pals = {}
    for name, (sprite, mirror, dx, dy) in HOUSES.items():
        art = np.array(Image.open(src / f'{sprite}.png').convert('RGBA'))
        c0, c1 = info[sprite]['door_columns']; r0, r1 = info[sprite]['door_rows']
        if mirror:
            art = art[:, ::-1]; c0, c1 = art.shape[1] - c1, art.shape[1] - c0
        x0 = dx * 16 - c0 if not mirror else (dx + 1) * 16 - c1     # the door inside its warp cell's columns
        y0 = (dy + 1) * 16 - art.shape[0]
        for r in range(dy - 5, dy + 1):
            for x in range(dx - 4, dx + 5):
                old = np.isin(bank_map(town, x, r), OLD_HOUSE_BANKS)
                if old.any():
                    px = cv.ground[cv.sl(x, r)].copy()
                    yy, xx = np.mgrid[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16]
                    px[old] = lawn[yy[old] % 32, xx[old] % 32]
                    cv.put_ground(x, r, px); cv.changed.add((x, r))
        over(cv.top, art, x0, y0 - R0 * 16)
        for r in range(y0 // 16, dy + 1):
            for x in range(x0 // 16, (x0 + art.shape[1] - 1) // 16 + 1):
                cv.changed.add((x, r))
        cv.fixed[(dx, dy)] = int(town.words[dy, dx]) & 1023
        cv.doors.append(dict(name=name, sprite=sprite, cell=(dx, dy), size='RIGHT' if mirror else 'LEFT', bank=HOUSE_BANK[sprite],
                             panel=(x0 + c0, y0 + r0, x0 + c1, y0 + r1)))
        pals[sprite] = [tuple(c) for c in info[sprite]['palette']]
    base = pals['skylight']
    assert pals['gable'] == base, 'the skylight and gable houses no longer share a palette'
    teal = dict(zip(base, pals['teal']))
    cv.pals[HOUSE_BANK['skylight']] = base + [LAWN]
    cv.pals[HOUSE_BANK['teal']] = [teal[c] for c in base] + [LAWN]
    cv.notes.append(f'houses: {", ".join(HOUSES)}; banks {sorted(set(HOUSE_BANK.values()))}')

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
