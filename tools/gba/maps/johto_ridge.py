"""Johto's thin ridge (owner standard: Route 36's one-cell dirt ridge for low-lying, foresty areas).

A one-cell-thick rock run (a single row of rock between two lower or open rows, or a single column) is drawn
with Route 36's own ridge cells instead of FRLG's thin faces, so the ridge is a full cell high, the same height
as a half flight of the standard stairs, and runs on under the stairs that cross it with no lawn between rock
and rails (owner review of #39, second pass).

Pieces, read from Route 36's installed tileset (the ridge's own colours; lawn pixels transparent):
  horizontal  371 / 372 by column parity       vertical  202 / 204 by row parity
  corner, run east and south  545              corner, run west and north  546
A thin cell needing any other shape (a T, a corner the other way round, or touching thick rock) keeps the
FRLG piece rock_frlg drew; the caller gets those cells back.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from tiles import Tileset                    # noqa: E402

PX = 16
TS = 'johto_route36'
H_IDS, V_IDS = (371, 372), (202, 204)
CORNER_ES, CORNER_WN = 545, 546
RIDGE = {(80, 56, 64), (88, 80, 72), (96, 64, 48), (104, 72, 56), (104, 96, 88), (120, 88, 64), (128, 96, 80),
         (136, 96, 96), (136, 104, 80), (160, 120, 96)}

def pieces(engine):
    """RGBA 16x16 of each piece: ridge pixels opaque, everything else transparent."""
    t = Tileset(engine, TS, TS)
    out = {}
    for m in H_IDS + V_IDS + (CORNER_ES, CORNER_WN):
        rgb = np.array(t.render(m).convert('RGB'))
        a = np.zeros((PX, PX, 4), np.uint8)
        op = np.array([[tuple(int(v) for v in p) in RIDGE for p in row] for row in rgb])
        a[op, :3] = rgb[op]; a[op, 3] = 255
        out[m] = a
    return out

def shape(rock, x, y):
    """The piece a thin cell takes, or None."""
    Hh, W = rock.shape
    at = lambda xx, yy: 0 <= xx < W and 0 <= yy < Hh and rock[yy, xx]
    n, s, w, e = at(x, y - 1), at(x, y + 1), at(x - 1, y), at(x + 1, y)
    if not n and not s and (w or e):
        # a run along a row: thin only if no rock touches it diagonally from above or below either
        return H_IDS[x % 2]
    if not w and not e and (n or s):
        return V_IDS[y % 2]
    if e and s and not n and not w and not at(x + 1, y + 1):
        return CORNER_ES
    if w and n and not s and not e and not at(x - 1, y - 1):
        return CORNER_WN
    return None

def thin_cells(rock):
    """Every rock cell that is part of a one-cell-thick run, with its piece."""
    Hh, W = rock.shape
    out = {}
    for y in range(Hh):
        for x in range(W):
            if rock[y, x]:
                k = shape(rock, x, y)
                if k is not None:
                    out[(x, y)] = k
    return out

def draw(engine, rock, bottom, over, grass):
    """Redraw rock_frlg's thin runs: in each thin cell the FRLG overlay goes, the ground is the route's lawn
    (grass: its 32x32 texture at map phase) and the Route 36 piece goes on the overlay. Returns the cells drawn."""
    p = pieces(engine)
    cells = thin_cells(rock)
    for (x, y), k in cells.items():
        sl = np.s_[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX]
        ys, xs = np.mgrid[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX]
        bottom[sl] = grass[ys % 32, xs % 32]
        over[sl] = p[k]
    return cells
