#!/usr/bin/env python3
"""Johto standard stairs (owner-locked 2026-11-20, from Route 32): HGSS's plank flight with a rail each side.

    python3 tools/gba/maps/johto_stairs.py            # writes gba/art/johto-common/stairs/

North-south (a flight down a south face): a west rail, plank treads, an east rail, straight down the flight.
  The first row starts NS_TOP_TRIM px into its cell, level with the cliff top beside it (no half step above).
  A full flight is two rows (two levels of steps); a half flight is the first row only.
  Kit pieces, 16 x 16 each: ns-top-{west,middle,east}, ns-lower-{west,middle,east}. A flight n cells wide is
  west, middle x (n - 2), east. The rails are 6 px, so a flight is at least 2 cells wide.

East-west (a flight across a wall, over the cliff it cuts through, upper layer): a top rail, the treads and a
  bottom rail as parallel bands on the diagonal, one pixel down per pixel toward the low side. One column is one
  level (a half flight); a full flight is two columns, the lower column one row further south so the bands run
  on unbroken. Falling east and falling west are exact mirror images.
  Kit pieces, 16 x 80 each, transparent off the bands: ew-falls-east, ew-falls-west. Anchor: the piece's
  pixel row 16 is the top of the flight's first cell (the top rail reaches 6 px into the cell above, the
  bottom rail 4 px into the fourth cell below).

Plank stripes run in a 5 px cycle counted on the map (a 16 px cell shifts the cycle by 1), so a stacked
flight's bands meet without a seam. The kit pieces are drawn at phase 0; the route assemblers call the drawing
functions with the map phase.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
from PIL import Image

PX = 16
# HGSS Route 32's flight in the route's palette: plank stripes, the treads' dark top edge, and the rails
# (outline, light edge, body, shade, outline) from the outside in for the top/west rail and from the treads
# out for the bottom/east rail.
TREAD_STRIPES = [(152, 144, 120), (168, 168, 144), (168, 168, 144), (152, 144, 120), (88, 80, 48)]
TREAD_EDGE, TREAD_PX = (88, 80, 48), 30
TOP_RAIL = [(82, 58, 52), (198, 148, 115), (165, 115, 99), (165, 115, 99), (99, 70, 66), (82, 58, 52)]
BOTTOM_RAIL = [(82, 58, 52), (165, 115, 99), (198, 148, 115), (165, 115, 99), (99, 70, 66), (82, 58, 52)]
NS_TOP_TRIM = 3       # px: the cliff beside a north-south flight starts 3 px into its row (2 px lawn, 1 px lip)

def north_south(out, x0, x1, y0, y1, first, phase=0):
    """Draw one row of a north-south flight into RGBA `out` over pixel columns x0..x1-1, rows y0..y1-1.
    `first`: the flight's top row (trimmed, dark tread edge). Stripe cycle position = (row + phase) % 5."""
    top = y0 + (NS_TOP_TRIM if first else 0)
    for Y in range(top, y1):
        edge = first and Y == top
        for k, c in enumerate(TOP_RAIL):
            out[Y, x0 + k, :3] = c
        for k, c in enumerate(BOTTOM_RAIL):
            out[Y, x1 - len(BOTTOM_RAIL) + k, :3] = c
        out[Y, x0 + len(TOP_RAIL):x1 - len(BOTTOM_RAIL), :3] = TREAD_EDGE if edge else TREAD_STRIPES[(Y + phase) % len(TREAD_STRIPES)]
        out[Y, x0:x1, 3] = 255

def east_west(out, x0, y_top, falls, phase=0):
    """Draw one column of an east-west flight into RGBA `out`: pixel column x0..x0+15, its first tread row at
    y_top on the high side. Stripe cycle position = (column pixel + phase) % 5."""
    for xx in range(PX):
        dy = xx if falls == 'E' else PX - 1 - xx
        top = y_top + dy
        bands = [(top - len(TOP_RAIL) + k, c) for k, c in enumerate(TOP_RAIL)]
        bands += [(top + k, TREAD_EDGE if k == 0 else TREAD_STRIPES[(xx + phase) % len(TREAD_STRIPES)]) for k in range(TREAD_PX)]
        bands += [(top + TREAD_PX + k, c) for k, c in enumerate(BOTTOM_RAIL)]
        for Y, c in bands:
            if 0 <= Y < out.shape[0]:
                out[Y, x0 + xx, :3] = c; out[Y, x0 + xx, 3] = 255

def flights(grid, W, H, stair='^', rock='R'):
    """HGSS's stair cells as flights: [(kind, cells)] with kind 'ew' (rock above and below every column: a
    crossing of a wall) or 'ns' (climbed up or down a face)."""
    g = lambda x, y: grid[y][x] if 0 <= x < W and 0 <= y < H else '#'
    out, seen = [], set()
    for y0 in range(H):
        for x0 in range(W):
            if g(x0, y0) != stair or (x0, y0) in seen:
                continue
            comp, todo = set(), [(x0, y0)]
            while todo:
                c = todo.pop()
                if c in comp or g(*c) != stair:
                    continue
                comp.add(c); todo += [(c[0] + dx, c[1] + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            seen |= comp
            xs = sorted({c[0] for c in comp})
            cols = {x: sorted(y for cx, y in comp if cx == x) for x in xs}
            ew = all(g(x, cols[x][0] - 1) in rock and g(x, cols[x][-1] + 1) in rock for x in xs)
            out.append(('ew' if ew else 'ns', sorted(comp)))
    return out

def falls_by_ground(grid, W, H, ground, stair='^'):
    """A `falls` rule for place(): an east-west flight falls toward the side whose lawn is lower, read from
    `ground(x, y)` on the cells just west and east of the flight."""
    def falls(cells):
        xs = [x for x, _ in cells]
        ys = sorted({y for _, y in cells})
        side = lambda x: [ground(x, y) for y in ys if 0 <= x < W and grid[y][x] != stair]
        w, e = side(min(xs) - 1), side(max(xs) + 1)
        return 'E' if w and e and sum(e) / len(e) < sum(w) / len(w) else 'W'
    return falls

def cliff_under(grid, W, H, d, isrock, cells, stair='^', rock='R'):
    """The cliff an east-west flight crosses runs on under it, unbroken (Route 32's rule): each flight cell
    terraces as rock at the level of the rock just north of its column, and the face beside it continues the
    face above it (the neighbour's floor is the floor of the cell north of the flight). Returns the rock mask to
    hand to rock_frlg; `d` and `cells` are updated in place."""
    draw = isrock.copy()
    for kind, fc in flights(grid, W, H, stair, rock):
        if kind != 'ew':
            continue
        for x, y in fc:
            top = min(yy for xx, yy in fc if xx == x) - 1
            draw[y, x] = True; d[y, x] = d[top, x]
            for nx in (x - 1, x + 1):
                if 0 <= nx < W and (nx, y) not in fc:
                    cells[y][nx] = dict(cells[y][nx], floor=cells[top][nx]['floor'])
    return draw

def place(grid, W, H, falls=lambda cells: 'E', stair='^', rock='R'):
    """Draw every flight with the kit. Returns (art RGBA, placements). North-south flights fill their rows;
    an east-west flight's bands are centred on its cells (rails reaching over the cliff above and below), so
    the caller draws the art after the cliff."""
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    placed = []
    for kind, cells in flights(grid, W, H, stair, rock):
        xs, ys = sorted({c[0] for c in cells}), sorted({c[1] for c in cells})
        if kind == 'ns':
            for y in ys:
                row = sorted(x for x, yy in cells if yy == y)
                north_south(art, row[0] * PX, (row[-1] + 1) * PX, y * PX, (y + 1) * PX, y == ys[0])
                placed += [dict(cell=[x, y], art='johto_stairs north-south' + (' top' if y == ys[0] else ''), flight='north-south') for x in row]
        else:
            f = falls(cells)
            order = xs if f == 'E' else xs[::-1]
            mid = (ys[0] + ys[-1] + 1) * PX / 2
            band = len(TOP_RAIL) + TREAD_PX + len(BOTTOM_RAIL)
            top0 = int(round(mid - band / 2 + len(TOP_RAIL) - (len(xs) * PX - 1) / 2))
            for i, x in enumerate(order):
                east_west(art, x * PX, top0 + i * PX, f, phase=x * PX)
            placed += [dict(cell=list(c), art=f'johto_stairs east-west falling {f}', flight='east-west') for c in cells]
    return art, placed

def kit():
    """The kit pieces at phase 0, by name."""
    p = {}
    for row, first in (('top', True), ('lower', False)):
        a = np.zeros((PX, 3 * PX, 4), np.uint8)              # a 3-cell flight row, cut into its three pieces
        north_south(a, 0, 3 * PX, 0, PX, first)
        for i, part in enumerate(('west', 'middle', 'east')):
            p[f'ns-{row}-{part}'] = a[:, i * PX:(i + 1) * PX].copy()
    e = np.zeros((5 * PX, PX, 4), np.uint8)
    east_west(e, 0, PX, 'E')
    p['ew-falls-east'] = e
    p['ew-falls-west'] = e[:, ::-1].copy()
    return p

def preview(p):
    """Left to right: NS full, NS half, EW full falling east and west, EW half falling east and west (2x)."""
    bg = (104, 208, 152)
    sheet = np.zeros((7 * PX, 21 * PX, 3), np.uint8); sheet[:] = bg
    def put(img, x, y):
        m = img[..., 3] > 0
        sheet[y:y + img.shape[0], x:x + img.shape[1]][m] = img[..., :3][m]
    for x0, rows in ((PX, ('top', 'lower')), (5 * PX, ('top',))):          # NS full, NS half
        for r, row in enumerate(rows):
            for i, part in enumerate(('west', 'middle', 'east')):
                put(p[f'ns-{row}-{part}'], x0 + i * PX, PX + r * PX)
    put(p['ew-falls-east'], 9 * PX, 0); put(p['ew-falls-east'], 10 * PX, PX)  # EW full, falling east (phase aside)
    put(p['ew-falls-west'], 12 * PX, PX); put(p['ew-falls-west'], 13 * PX, 0)  # EW full, falling west
    put(p['ew-falls-east'], 16 * PX, 0)                                         # EW half, falling east
    put(p['ew-falls-west'], 19 * PX, 0)                                         # EW half, falling west
    return Image.fromarray(sheet).resize((sheet.shape[1] * 2, sheet.shape[0] * 2), Image.NEAREST)

def main():
    out = Path(__file__).resolve().parents[3] / 'gba/art/johto-common/stairs'
    out.mkdir(parents=True, exist_ok=True)
    p = kit()
    for name, a in p.items():
        Image.fromarray(a).save(out / f'{name}.png')
    preview(p).save(out / 'preview.png')
    assert (p['ew-falls-west'] == p['ew-falls-east'][:, ::-1]).all()
    print(sorted(p))

if __name__ == '__main__':
    main()
