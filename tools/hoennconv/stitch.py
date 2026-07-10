#!/usr/bin/env python3
"""Stitch the Hoenn overworld into one global metatile grid.

pokeemerald maps declare adjacency in map.json "connections"
({map, direction, offset}); placing every connected map by BFS from
MAP_LITTLEROOT_TOWN reproduces the world layout exactly the way the GBA
engine renders seams (offset = displacement along the shared edge, in
metatiles).

The result is the input for slicing into HGSS 32x32 matrix chunks: HGSS keeps
its whole overworld in one big map matrix ("EVERYWHERE", 47x17 in vanilla)
with per-cell map headers, which is structurally identical to this stitched
canvas.

Dive maps (underwater) connect via "dive"/"emerge" pseudo-directions and are
excluded from the surface canvas.
"""

from __future__ import annotations

from dataclasses import dataclass

import gba

START = "MAP_LITTLEROOT_TOWN"
_DELTAS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}


@dataclass
class Placement:
    map_id: str
    layout_id: str
    x: int          # global metatile coords of the map's top-left corner
    y: int
    width: int
    height: int


def stitch(start: str = START) -> dict[str, Placement]:
    """map_id -> Placement, in global (possibly negative) metatile coords."""
    maps = gba.maps()
    lay = gba.layouts()
    placed: dict[str, Placement] = {}
    queue = [(start, 0, 0)]
    while queue:
        map_id, x, y = queue.pop(0)
        if map_id in placed:
            continue
        m = maps[map_id]
        l = lay[m["layout"]]
        placed[map_id] = Placement(map_id, m["layout"], x, y, l["width"], l["height"])
        for c in m.get("connections") or []:
            d = c["direction"]
            if d not in _DELTAS:            # dive/emerge
                continue
            nm = maps.get(c["map"])
            if nm is None or c["map"] in placed:
                continue
            nl = lay[nm["layout"]]
            off = c["offset"]
            if d == "up":
                nx, ny = x + off, y - nl["height"]
            elif d == "down":
                nx, ny = x + off, y + l["height"]
            elif d == "left":
                nx, ny = x - nl["width"], y + off
            else:  # right
                nx, ny = x + l["width"], y + off
            queue.append((c["map"], nx, ny))
    return placed


def normalize(placed: dict[str, Placement]) -> tuple[dict[str, Placement], int, int]:
    """Shift all placements to non-negative coords; return (placed, W, H)."""
    minx = min(p.x for p in placed.values())
    miny = min(p.y for p in placed.values())
    for p in placed.values():
        p.x -= minx
        p.y -= miny
    w = max(p.x + p.width for p in placed.values())
    h = max(p.y + p.height for p in placed.values())
    return placed, w, h


def overlaps(placed: dict[str, Placement]) -> list[tuple[str, str]]:
    """Sanity check: pairs of maps whose rectangles overlap (should be none)."""
    out = []
    ps = list(placed.values())
    for i, a in enumerate(ps):
        for b in ps[i + 1:]:
            if (a.x < b.x + b.width and b.x < a.x + a.width and
                    a.y < b.y + b.height and b.y < a.y + a.height):
                out.append((a.map_id, b.map_id))
    return out
