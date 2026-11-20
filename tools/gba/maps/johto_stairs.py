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
