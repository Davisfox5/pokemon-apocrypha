"""Celadon's ground: HGSS's own ground textures at 1:1 on the Gen 3 grid.

HGSS draws Celadon's ground with 32 px textures (hexagon paving, terrace brick, lawn) that
it stretches a little per polygon. Here each texture repeats at its own 32 px size in the
world's phase, so a material is the same few tiles wherever it runs, and the joins between
materials are drawn the Gen 3 way:

    grass    grass01gs, one 16 px quadrant of it, so the lawn repeats every cell; the
             flower01-03 beds at HGSS's own cells (its grass01_a tufts stay out: four tiles each)
    paving   tama_yuka (hexagon paving)
    terrace  tama_yuka2 (the brick the north row and the Gym stand on)
    kerb     tama_br turned to run along the terrace's edge: the light stones, a grey
             lip and the dark face, flipped where the terrace lies south of it
    lawns    HGSS's lawn edge (tama_fuch) as bands on the lawn side of the join: the
             paving's grey-olive lip, a dark line, a ragged dark-teal fringe, then grass.
             The cell mask is blurred so corners round off and straight runs stay on the
             cell edge (Cianwood's method), and the fringe's jag repeats every 16 px
    canal    pond_on's sparkling water (one 16 px quadrant of it), a deeper band along its sides (pond_edge), the
             brick lip at each end (pond_line), the sandy rim down both sides
    bridge   HGSS's footbridge: dark rails at both ends, the light kerb stones, one grey
             plank a cell running north-south, the rope posts down its sides, all in the
             grey ramp the kerbs and posts share
    ledges   allpeak: the straight strip, its rounded ends from allpeakgs
    bike lane  the story's lane (DESIGN.md Chapter 6, change 7) painted down the middle of
             the main road, the west avenue and the west road in Celadon's teal
"""
from __future__ import annotations
import numpy as np

import common as C

W, H = C.W, C.H
PAVED = ('pave', 'brick', 'kerb', 'bridge')

# HGSS's lawn edge (tama_fuch), from the paving into the lawn.
LIP, DARK, FRINGE, DITHER = (156, 165, 132), (107, 140, 115), (82, 165, 148), (99, 189, 156)
JAG = [0, 1, 1, 0, 2, 1, 0, 0, 1, 2, 1, 0, 0, 1, 0, 1]         # extra fringe depth along an edge, 16 px repeat

# Shared ground ramps, so the stone, the water and the earth each cost one set of colours:
# HGSS's kerb, bridge and post greys (tama_br, tama_f), its canal rim and ledge browns
# (pond_line, allpeak), its pond blues (pond_on, pond_edge).
GREYS = [(231, 231, 231), (198, 198, 198), (156, 156, 156), (107, 107, 90), (90, 90, 57)]
BROWNS = [(214, 181, 132), (189, 140, 99), (156, 115, 99), (132, 90, 82), (90, 66, 49)]
WATER = [(90, 222, 255), (74, 206, 255), (57, 189, 255), (57, 165, 247), (57, 140, 239)]
LEAF = [(99, 189, 156), (107, 206, 165)]                    # the flower beds' and tufts' greens (grass01_a)

def snap(img, ramp):
    """img's colours moved to the nearest colour of ramp (channel-weighted), alpha kept."""
    img = img.copy()
    p = np.array(ramp, int)
    rgb = img[..., :3].astype(int)
    img[..., :3] = p[(((rgb[..., None, :] - p) ** 2) * np.array([3, 4, 2])).sum(-1).argmin(-1)]
    return img

# The kerb (tama_br turned): its texture columns 0-15 become rows across the kerb.
KERB_FACE = GREYS[4]

# Canal colours (pond_on, pond_edge, pond_line).
DEEP = WATER[4]
RIM = [BROWNS[0], BROWNS[1], BROWNS[3]]
# Bridge (tama_br and the bridge's own planks, as HGSS draws it), in the grey ramp.
RAIL, RAIL_DARK = GREYS[3], GREYS[4]
PLANK = dict(g=GREYS[2], m=GREYS[1], l=GREYS[0], s=GREYS[1])
PLANK_ROW = "ggmmlllllllmmmsg"
POST = GREYS[4]

# Bike lane: Celadon's teal (the teal of its houses' trim) between white edge lines.
LANE, LANE_LINE = (66, 173, 165), (239, 239, 222)
LANE_ROWS = (17, 34)                # main road east to Route 7; west road to Route 16
LANE_COL = 11                       # the west avenue
LANE_SPAN = dict(row17=(LANE_COL, W - 1), row34=(0, LANE_COL), col11=(17, 34))

def tile(tex, ys, xs):
    return tex[ys % tex.shape[0], xs % tex.shape[1], :3]

GRASS_BLOCK = (0, 16)                # grass01gs's quadrant used as the lawn: one cell, so the lawn repeats every cell

def textures(t):
    """HGSS's ground textures as Celadon draws them: the lawn one cell of grass01gs, the
    stone, water and earth snapped onto their shared ramps, the beds' greens onto LEAF."""
    oy, ox = GRASS_BLOCK
    g = dict(t)
    g['grass'] = t['grass01gs'][oy:oy + 16, ox:ox + 16]
    g['tama_br'] = snap(t['tama_br'], GREYS)
    g['tama_f'] = snap(t['tama_f'], GREYS)
    g['pond_on'] = snap(t['pond_on'], WATER)
    g['pond_edge'] = snap(t['pond_edge'], WATER)
    g['pond_line'] = snap(t['pond_line'], BROWNS)
    for k in ('allpeakgs', 'allpeak_pgs'):
        g[k] = snap(t[k], BROWNS)
    mint = list({tuple(int(v) for v in c) for c in g['grass'].reshape(-1, 4)[:, :3]})
    for k in ('flower01', 'flower02', 'flower03', 'grass01_a'):
        a = t[k].copy()
        rgb = a[..., :3].astype(int)
        green = (rgb[..., 1] > rgb[..., 0] + 30) & (a[..., 3] > 0)
        a[green] = snap(a[green][None], LEAF + mint)[0]
        g[k] = a
    return g

def kerb_cell(t, south):
    """A kerb cell: three rows of terrace brick, the stones and grey lip of tama_br
    (its columns 2-13 turned into rows), the dark face. south: the terrace lies south of
    the kerb (its back edge), so the cell is drawn flipped."""
    br = t['tama_br'][..., :3].transpose(1, 0, 2)                   # rows = the texture's columns
    cell = np.zeros((16, 16, 3), np.uint8)
    cell[3:15] = br[2:14, :16]
    cell[15] = KERB_FACE
    return cell, south

def ground(cells, t):
    t = textures(t)
    floor = np.array([[c['floor'] for c in row] for row in cells])
    lab = np.array([[c['lab'] for c in row] for row in cells])
    ys, xs = np.mgrid[0:H * 16, 0:W * 16]
    out = tile(t['grass'], ys, xs).copy()
    paveA = tile(t['tama_yuka'], ys, xs)
    brick = tile(t['tama_yuka2'], ys, xs)
    water = tile(t['pond_on'][0:16, 0:16], ys, xs)            # one cell of pond_on, so the canal repeats every cell
    cellpx = lambda m: m.repeat(16, 0).repeat(16, 1)
    out[cellpx(floor == 'pave')] = paveA[cellpx(floor == 'pave')]
    out[cellpx(floor == 'brick')] = brick[cellpx(floor == 'brick')]
    wat = cellpx(floor == 'water')
    out[wat] = water[wat]
    # Kerbs: the terrace's front (terrace north of the kerb) or back (south of it).
    kc, _ = kerb_cell(t, False)
    for y in range(H):
        for x in range(W):
            if floor[y, x] != 'kerb':
                continue
            south = y + 1 < H and floor[y + 1, x] == 'brick'
            c = kc.copy()
            c[:3] = brick[y * 16:y * 16 + 3, x * 16:x * 16 + 16] if not south else c[:3]
            if south:
                c = c[::-1].copy()
                c[13:] = brick[y * 16 + 13:y * 16 + 16, x * 16:x * 16 + 16]
            out[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = c
    lawn_edges(out, floor)
    canal(out, floor, t)
    bridge(out, floor)
    decals(out, cells, t)
    ledges(out, lab, t)
    bike_lane(out, floor)
    return out

def lawn_edges(out, floor):
    """HGSS's lawn edge, drawn on the lawn side of every join with paving."""
    from scipy import ndimage
    g = floor == 'grass'
    land = floor != 'water'
    _, (iy, ix) = ndimage.distance_transform_edt(~land, return_indices=True)
    gext = g[iy, ix]                                    # water lends the class of the land beside it
    G = ndimage.gaussian_filter(gext.repeat(16, 0).repeat(16, 1).astype(float), 3.0, mode='nearest') > 0.5
    ys, xs = np.mgrid[0:H * 16, 0:W * 16]
    d = ndimage.distance_transform_cdt(G, metric='taxicab')    # 1 at the lawn's own edge pixel
    lawnpx = G & land.repeat(16, 0).repeat(16, 1)
    jag = np.array(JAG)[(xs + ys) % 16]
    out[lawnpx & (d <= 2)] = LIP
    out[lawnpx & (d == 3)] = DARK
    out[lawnpx & (d >= 4) & (d <= 4 + jag)] = FRINGE
    dither = lawnpx & (d == 5 + jag) & ((xs + ys) % 2 == 0)
    out[dither] = DITHER
    # Paving that the blurred mask hands to the lawn at an outer corner keeps its paving:
    # only cells whose floor is grass take the lawn's bands.
    notlawn = ~g.repeat(16, 0).repeat(16, 1) & lawnpx
    return notlawn

def canal(out, floor, t):
    """pond_on's water, the deeper band along both sides, the brick lip at each end, the
    sandy rim down both sides (on the water cell's outer pixels)."""
    edge = t['pond_edge'][..., :3]
    lip = t['pond_line']
    for y in range(H):
        for x in range(W):
            if floor[y, x] != 'water':
                continue
            X0, Y0 = x * 16, y * 16
            cell = out[Y0:Y0 + 16, X0:X0 + 16]
            wn = y > 0 and floor[y - 1, x] in ('water', 'bridge')
            ws = y + 1 < H and floor[y + 1, x] in ('water', 'bridge')
            ww = floor[y, x - 1] == 'water'
            we = floor[y, x + 1] == 'water'
            if not ww:
                cell[:, 2:6] = np.where((edge[:, :4] == DEEP).all(-1)[..., None] | True, DEEP, cell[:, 2:6])
            if not we:
                cell[:, 10:14] = DEEP
            if not ww:
                rim_side(cell, left=True, y=y)
            if not we:
                rim_side(cell, left=False, y=y)
            if not wn:
                m = lip[..., 3] > 0
                top = cell[:12].copy()
                top[m[:12]] = lip[:12][..., :3][m[:12]]
                cell[:12] = top
            if not ws:
                m = lip[::-1][..., 3] > 0
                bot = cell[4:].copy()
                bot[m[4:]] = lip[::-1][4:][..., :3][m[4:]]
                cell[4:] = bot

def rim_side(cell, left, y):
    """The canal's sandy rim, three pixels on the land side of the water, a brown dot
    every few pixels, as HGSS draws it."""
    cols = (0, 1, 2) if left else (15, 14, 13)
    cell[:, cols[0]] = RIM[0]
    cell[:, cols[1]] = RIM[0]
    cell[:, cols[2]] = RIM[1]
    for r in (2, 9):
        cell[r:r + 2, cols[1]] = RIM[2]
    for r in (5, 13):
        cell[r, cols[0]] = RIM[1]

def bridge(out, floor):
    """HGSS's footbridge over the canal: one grey plank a cell, dark rails at the ends, the
    light kerb stones under the north rail, the rope posts and the canal's rim down its
    sides."""
    row = np.array([PLANK[ch] for ch in PLANK_ROW], np.uint8)
    for y in range(H):
        for x in range(W):
            if floor[y, x] != 'bridge':
                continue
            X0, Y0 = x * 16, y * 16
            cell = np.repeat(row[None], 16, 0)
            north = floor[y - 1, x] != 'bridge'
            south = floor[y + 1, x] != 'bridge'
            if north:
                cell[0:5] = RAIL
                cell[5] = RAIL_DARK
                cell[6:12] = GREYS[0]
                cell[6:12, 0] = cell[6:12, 15] = GREYS[1]
                cell[11] = GREYS[1]
            if south:
                cell[11:15] = RAIL
                cell[15] = RAIL_DARK
            if floor[y, x - 1] != 'bridge':
                cell[:, 0] = GREYS[3]
                cell[(6 if north else 0):(11 if south else 16), 4] = POST
            if floor[y, x + 1] != 'bridge':
                cell[:, 15] = GREYS[3]
                cell[(6 if north else 0):(11 if south else 16), 11] = POST
            out[Y0:Y0 + 16, X0:X0 + 16] = cell

TUFT_OFF = ('grass01_a',)          # HGSS's nine grass tufts stay out: each costs four tiles of its own

def decals(out, cells, t):
    for y in range(H):
        for x in range(W):
            dk = cells[y][x]['deco']
            if dk in TUFT_OFF:
                continue
            if dk and cells[y][x]['floor'] == 'grass' and cells[y][x]['lab'] in '.':
                C.put(out, t[dk], x * 16, y * 16)

def ledges(out, lab, t):
    """HGSS's jump ledges (allpeak): the straight strip, rounded ends where a run stops."""
    mid = t['allpeak_pgs']
    ends = t['allpeakgs'][16:32]
    for y in range(H):
        for x in range(W):
            if lab[y, x] != 'L':
                continue
            img = mid
            if lab[y, x - 1] != 'L':
                img = ends[:, 0:16]
            elif lab[y, x + 1] != 'L':
                img = ends[:, 16:32]
            C.put(out, img, x * 16, y * 16)

def bike_lane(out, floor):
    def band(X0, Y0, vertical):
        cell = out[Y0:Y0 + 16, X0:X0 + 16]
        if vertical:
            cell[:, 4:12] = LANE
            cell[:, 4] = cell[:, 11] = LANE_LINE
        else:
            cell[4:12] = LANE
            cell[4] = cell[11] = LANE_LINE
    x0, x1 = LANE_SPAN['row17']
    for x in range(x0, x1 + 1):
        band(x * 16, LANE_ROWS[0] * 16, False)
    x0, x1 = LANE_SPAN['row34']
    for x in range(x0, x1 + 1):
        band(x * 16, LANE_ROWS[1] * 16, False)
    y0, y1 = LANE_SPAN['col11']
    for y in range(y0, y1 + 1):
        band(LANE_COL * 16, y * 16, True)
    for y in LANE_ROWS:                                     # the turns: the band runs on across the corner cell
        cell = out[y * 16:y * 16 + 16, LANE_COL * 16:LANE_COL * 16 + 16]
        cell[4:12, 4:12] = LANE
    c = out[LANE_ROWS[0] * 16:LANE_ROWS[0] * 16 + 16, LANE_COL * 16:LANE_COL * 16 + 16]
    c[4, 4:12] = LANE_LINE; c[4:12, 4] = LANE_LINE; c[11, 4] = LANE_LINE
    c = out[LANE_ROWS[1] * 16:LANE_ROWS[1] * 16 + 16, LANE_COL * 16:LANE_COL * 16 + 16]
    c[11, 4:12] = LANE_LINE; c[4:12, 11] = LANE_LINE; c[4, 11] = LANE_LINE
