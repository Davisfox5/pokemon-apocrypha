"""Celadon City, fourth round: the revised plan (owner, 2026-10-26).

HGSS's Celadon is the skeleton (the north row of big buildings on its brick terrace, the
main road east to Route 7, the west avenue and the west road to Route 16, the fountain plaza
west, the Game Corner in the middle), grown by ten years and the owner's brief:

    canal       one canal winds through the whole city on a smooth curve: down from the north
                woods beside the Dept Store, under the main road, past the market, under the
                cross street, south and east into the Arboretum where it opens into a lake
                with an island, then east and north up the east side, under the east lane and
                the main road again, and away into the north-east woods. Six bridges.
    cycleway    along the canal's bank the whole way, joined by the west road to Route 16
                (the Cycling Road) and the main road to Route 7
    arboretum   the Gym is gone. Its block is the Arboretum's entrance garden (hedged flower
                beds), and the woods south of the town are the Arboretum itself: the lake and
                its island, groves of three kinds of tree, meadows, gravel walks, benches,
                the glass conservatory
    market      stalls in a ring round the fountain plaza, lamps and bunting
    buildings   bigger: the Dept Store the tallest building in town, the Game Corner with its
                marquee, the Pokemon Hotel (the Condominiums) and the apartment tower; the
                houses one family of timber cottages (Fuchsia's HGSS models, the cafe's
                kind), roofs in Celadon's colours

Cell floors (grass, pave, brick, kerb, meadow, garden, gravel) come from rectangles; the
canal, the lake and the cycleway are curves at pixel level (masks), and a cell takes water
or cycleway where most of its pixels do. W x H = 84 x 64 cells.
"""
from __future__ import annotations
import numpy as np

W, H = 84, 64
CANAL = [(27, -3), (27, 6), (25.5, 14), (24.5, 22), (23.5, 30), (25, 38), (29, 45), (36, 49.5), (46, 50),
         (54, 47), (59.5, 40), (60.5, 32), (59.5, 24), (60, 16), (63, 8), (67, -3)]
CANAL_R = 30.0                       # half-width, px (about four cells of water)
LAKE = ((41, 56), (9.5, 4.8))        # centre, radii (cells)
ISLAND = ((41, 56.3), (3.0, 1.6))
CYCLE_OFFSET = (CANAL_R + 6, CANAL_R + 36)   # the cycleway's band beside the canal, px from its centre line
CYCLE_SIDE = 1                       # the canal's outer bank: the market side, the Arboretum side, the east side

def spline(points, step=0.05):
    """Catmull-Rom through the points, in cells."""
    p = np.array(points, float)
    p = np.vstack([p[0] * 2 - p[1], p, p[-1] * 2 - p[-2]])
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for t in np.arange(0, 1, step):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(p[-2])
    return np.array(out)

def masks():
    """Pixel masks: water (canal and lake), island, cycleway; and the canal's centre line."""
    from scipy import ndimage
    line = spline(CANAL) * 16
    hh, ww = H * 16, W * 16
    ys, xs = np.mgrid[0:hh, 0:ww]
    # distance to the centre line, and which side of it each pixel lies on
    pts = np.zeros((hh, ww), bool)
    dense = spline(CANAL, 0.005) * 16
    for x, y in dense:
        if 0 <= int(y) < hh and 0 <= int(x) < ww:
            pts[int(y), int(x)] = True
    dist, (iy, ix) = ndimage.distance_transform_edt(~pts, return_indices=True)
    along = np.zeros((hh, ww))
    run = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(dense, axis=0).T))])
    for k, (x, y) in enumerate(dense):
        if 0 <= int(y) < hh and 0 <= int(x) < ww:
            along[int(y), int(x)] = run[k]
    along = along[iy, ix]                                 # distance along the canal of each pixel's nearest point
    # tangent at the nearest point, for the side
    tang = np.zeros((hh, ww, 2))
    for k in range(len(dense) - 1):
        x, y = dense[k]
        if 0 <= int(y) < hh and 0 <= int(x) < ww:
            tang[int(y), int(x)] = dense[k + 1] - dense[k]
    t = tang[iy, ix]
    side = np.sign(t[..., 0] * (ys - iy) - t[..., 1] * (xs - ix))
    water = dist <= CANAL_R
    (cx, cy), (rx, ry) = LAKE
    lake = ((xs / 16 - cx) / rx) ** 2 + ((ys / 16 - cy) / ry) ** 2 <= 1
    (ix0, iy0), (irx, iry) = ISLAND
    island = ((xs / 16 - ix0) / irx) ** 2 + ((ys / 16 - iy0) / iry) ** 2 <= 1
    water = (water | lake) & ~island
    cycle = (dist >= CYCLE_OFFSET[0]) & (dist <= CYCLE_OFFSET[1]) & (side == CYCLE_SIDE) & ~lake & ~island
    return dict(water=water, island=island, cycle=cycle, dist=dist, side=side, line=line, along=along)

def rect(grid, x0, y0, x1, y1, v):
    for y in range(max(0, y0), min(H, y1)):
        for x in range(max(0, x0), min(W, x1)):
            grid[y][x] = v

def floors(m=None):
    m = m or masks()
    g = [['forest'] * W for _ in range(H)]
    rect(g, 6, 5, 80, 16, 'brick')                       # the terrace the north row stands on
    rect(g, 6, 16, 80, 17, 'kerb')
    rect(g, 4, 17, W, 22, 'pave')                        # the main road, east to Route 7
    rect(g, 4, 17, 10, 42, 'pave')                       # the west avenue
    rect(g, 0, 36, 10, 40, 'pave')                       # the west road, west to Route 16
    rect(g, 10, 22, 22, 36, 'pave')                      # the market plaza
    rect(g, 12, 24, 20, 34, 'lawn')
    rect(g, 10, 36, 58, 40, 'pave')                      # the cross street
    rect(g, 29, 22, 57, 36, 'pave')                      # the Game Corner's square and its block
    rect(g, 30, 33, 56, 36, 'grass')
    rect(g, 29, 40, 56, 46, 'grass')                     # cottages south of the cross street
    rect(g, 29, 40, 56, 41, 'pave')
    rect(g, 63, 22, 80, 46, 'grass')                     # cottages east of the canal
    rect(g, 63, 30, 80, 33, 'pave')                      # the east lane
    rect(g, 56, 30, 63, 33, 'pave')
    rect(g, 4, 42, 22, 48, 'garden')                     # the Arboretum's entrance garden (the Gym's block)
    rect(g, 4, 48, 80, 62, 'meadow')                     # the Arboretum
    rect(g, 22, 44, 30, 48, 'meadow')
    for x0, y0, x1, y1 in WALKS:
        rect(g, x0, y0, x1, y1, 'gravel')
    share = lambda k: m[k].reshape(H, 16, W, 16).mean(axis=(1, 3))
    wat, cyc, isl = share('water'), share('cycle'), share('island')
    for y in range(H):
        for x in range(W):
            if wat[y, x] > 0.5:
                g[y][x] = 'water'
            elif cyc[y, x] > 0.4:
                g[y][x] = 'cycle'
            elif isl[y, x] > 0.4:
                g[y][x] = 'meadow'
    for (x0, y0, x1, y1), _ in BRIDGES.values():
        rect(g, x0, y0, x1, y1, 'bridge')
    return g

WALKS = [(12, 42, 14, 62), (4, 47, 22, 48), (14, 52, 30, 54), (52, 52, 80, 54), (44, 46, 46, 52), (64, 46, 66, 52),
         (30, 60, 52, 62), (70, 54, 72, 62)]
# Bridges: name, cells (x0, y0, x1, y1) of the deck, the way the street runs ('ew' or 'ns').
BRIDGES = dict(main_west=((22, 17, 29, 22), 'ew'), main_east=((56, 17, 64, 22), 'ew'), cross=((21, 36, 30, 40), 'ew'),
               arboretum=((44, 44, 47, 54), 'ns'), east=((56, 30, 65, 33), 'ew'), island=((40, 51, 42, 55), 'ns'))

# What stands where: name, kind, left cell, base row (the row the art's foot stands on).
PLACES = [
    ('house_n0', 'cottage_red', 6, 15), ('services', 'services', 11, 15), ('tower', 'tower', 30, 15),
    ('hotel', 'hotel', 36, 15), ('center', 'center', 44, 15), ('house_n1', 'cottage_green', 50, 15),
    ('house_n2', 'cottage_orange', 65, 15), ('house_n3', 'cottage_teal', 70, 15), ('house_n4', 'cottage_red', 75, 15),
    ('gamecorner', 'gamecorner', 31, 29), ('prize', 'prize', 44, 29), ('flat', 'cottage_teal', 50, 29),
    ('cafe', 'cafe', 30, 45), ('house_s0', 'cottage_green', 36, 45), ('house_s1', 'cottage_orange', 41, 45),
    ('house_s2', 'cottage_red', 48, 45),
    ('house_e0', 'cottage_orange', 64, 28), ('house_e1', 'cottage_teal', 69, 28), ('house_e2', 'cottage_green', 74, 28),
    ('house_e3', 'cottage_red', 64, 44), ('house_e4', 'cottage_orange', 69, 44), ('house_e5', 'cottage_teal', 74, 44),
    ('conservatory', 'conservatory', 4, 59), ('fountain', 'fountain', 13, 31),
]
STALLS = [(10, 26, 'red'), (18, 26, 'orange'), (10, 35, 'green'), (18, 35, 'blue'), (14, 24, 'violet')]
DOORS = dict(services=(17, 15), hotel=(40, 15), center=(46, 15), gamecorner=(36, 29), prize=(46, 29), cafe=(32, 45))
