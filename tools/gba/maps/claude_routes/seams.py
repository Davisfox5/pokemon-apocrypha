"""Which cells of one map get drawn while the player is in the other, at each connection.

A GBA map keeps only its own two tilesets in VRAM, so every cell drawn across a connection is rendered with the
current map's tilesets. Two things put such cells on screen:
  - the camera: the 240x160 screen shows the player's cell +-7 columns, 4 rows above and 5 below (one more on
    every side covers a scroll in progress), from any reachable cell near the edge;
  - the crossing itself: the BG holds a 16x16-cell window, 7 cells behind to 8 ahead of the player on both axes
    (field_camera.c DrawWholeMapViewInternal). Crossing a connection loads the new map's secondary tileset and
    palettes (overworld.c LoadMapFromCameraTransition) without redrawing that window, so every cell in it at
    the moment of crossing, on both sides of the seam, must draw the same with either map's tilesets.
Reachability is a plain flood fill over passable cells (ledges count as passable both ways, which over-counts
and so stays safe).
"""
from __future__ import annotations
import struct
from collections import deque
import numpy as np

CAM_X, CAM_UP, CAM_DOWN = 8, 5, 6

def read_layout(game, name, w, h):
    raw = (game / f'data/layouts/{name}/map.bin').read_bytes()
    grid = np.array(struct.unpack('<' + 'H' * (w * h), raw), dtype=np.uint16).reshape(h, w)
    return grid & 1023, (grid & 0xC00) != 0

def reachable(solid, start):
    h, w = solid.shape; seen = np.zeros_like(solid); q = deque([start]); seen[start[1], start[0]] = True
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            xx, yy = x + dx, y + dy
            if 0 <= xx < w and 0 <= yy < h and not seen[yy, xx] and not solid[yy, xx]:
                seen[yy, xx] = True; q.append((xx, yy))
    return seen

def visible_across(reach_a, shape_b, ox, oy):
    """Cells of map B visible from reachable cells of map A, where B's (0,0) sits at A's (ox, oy)."""
    hb, wb = shape_b; vis = np.zeros(shape_b, bool)
    for y, x in zip(*np.nonzero(reach_a)):
        x0, x1 = x - CAM_X - ox, x + CAM_X - ox; y0, y1 = y - CAM_UP - oy, y + CAM_DOWN - oy
        if x1 < 0 or y1 < 0 or x0 >= wb or y0 >= hb: continue
        vis[max(y0, 0):min(y1, hb - 1) + 1, max(x0, 0):min(x1, wb - 1) + 1] = True
    return vis

WIN_LO, WIN_HI = 7, 8

def crossing_windows(sol_a, sol_b, ox, oy):
    """Cells of A and of B inside the BG window at every crossing between A and B (B's (0,0) at A's (ox, oy)).
    Returns (mask over A, mask over B)."""
    ha, wa = sol_a.shape; hb, wb = sol_b.shape
    wa_m = np.zeros(sol_a.shape, bool); wb_m = np.zeros(sol_b.shape, bool)
    def mark(cx, cy):          # a window centred on A-coordinates (cx, cy)
        x0, x1, y0, y1 = cx - WIN_LO, cx + WIN_HI, cy - WIN_LO, cy + WIN_HI
        wa_m[max(y0, 0):min(y1, ha - 1) + 1, max(x0, 0):min(x1, wa - 1) + 1] = True
        bx0, bx1, by0, by1 = x0 - ox, x1 - ox, y0 - oy, y1 - oy
        if bx1 >= 0 and by1 >= 0 and bx0 < wb and by0 < hb:
            wb_m[max(by0, 0):min(by1, hb - 1) + 1, max(bx0, 0):min(bx1, wb - 1) + 1] = True
    pairs = 0
    for y in range(ha):
        for x in range(wa):
            if sol_a[y, x]: continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                bx, by = x + dx - ox, y + dy - oy
                inside_a = 0 <= x + dx < wa and 0 <= y + dy < ha
                if not inside_a and 0 <= bx < wb and 0 <= by < hb and not sol_b[by, bx]:
                    mark(x, y); mark(x + dx, y + dy); pairs += 1
    return wa_m, wb_m, pairs
