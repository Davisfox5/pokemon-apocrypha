"""Violet City's edges after the owner's review of #39 (docs/maps/reviews/PR39-2026-11-20.md).

- A row of trees along the top above Sprout Tower (rows 0-2), the tower's weathervane showing between the crowns.
- The bottom forest runs on off the map: rows 70-71 continue the woods instead of a lawn strip below them.
- The west gate is the standard G02 (gba/art/johto-common-review/gates/refinement-4/G02.png, the same master as
  Route 31's), its stairs facing the town, the strip under it sealed with trees.
- The east gate toward Route 31 is G02 mirrored, its stairs facing the town, where the stand-in house stood,
  sealed with trees above and below.

The woods are Violet's own forest metatiles placed on the forest's own lattice (an even row takes the crown
top 513/514 where a band starts, 579/580 inside; odd rows 516/517; the last row 581/582; even columns the
left half). A gate's cells are blocked except its two stair cells, which take the arrow-warp behaviour toward
the gate and the gate's two warps (GATES). The gates' art sits on the upper layer over lawn, in a bank of its own
(GATE_BANK, G02 merged to 15 colours).
"""
from __future__ import annotations
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image

import base as B
import elements as E

H, W = B.H, B.W
ENGINE_REV_G02 = 'de9e3638'                          # hub commit holding the approved gate masters
G02_PATH = 'gba/art/johto-common-review/gates/refinement-4/G02.png'
BLOCKED = 0x3400                                     # elevation 3, collision 1
WALKABLE = 0x3000
MB_EAST_ARROW_WARP, MB_WEST_ARROW_WARP = 0x62, 0x63

TOP, START, BODY_EVEN, BODY_ODD, LAST = (513, 514), (513, 514), (579, 580), (516, 517), (581, 582)

# Each gate: G02 origin (cells), mirrored or not, its stair cells (the gate's own column 6 or 0, rows 4-5),
# the arrow toward the gate and the warp's destination.
GATES = [
    dict(name='east', origin=(73, 53), mirror=True, stairs=[(73, 57), (73, 58)], mb=MB_EAST_ARROW_WARP,
         dest_map='MAP_VIOLET_EAST_GATE', dest_warp_id='0'),
    dict(name='west', origin=(0, 25), mirror=False, stairs=[(6, 29), (6, 30)], mb=MB_WEST_ARROW_WARP,
         dest_map='MAP_VIOLET_WEST_GATE', dest_warp_id='2'),
]

def gate_warps():
    """Violet's first four warps: each gate's first stair (ids 0 and 1, as the gate interiors expect), then
    each gate's second stair (ids 2 and 3)."""
    first = [dict(x=g['stairs'][0][0], y=g['stairs'][0][1], elevation=0, dest_map=g['dest_map'], dest_warp_id=g['dest_warp_id']) for g in GATES]
    second = [dict(x=g['stairs'][1][0], y=g['stairs'][1][1], elevation=0, dest_map=g['dest_map'], dest_warp_id=g['dest_warp_id']) for g in GATES]
    return first + second

GATE_BANK = 10                                       # a bank Violet's art no longer draws: the gates' own colours
GATE_COLOURS = 15

def g02(v=None):
    """The approved G02 master. With v: its 21 colours merged down to the 15 one bank holds (the two nearest
    5-bit colours, weighted by how many pixels each covers, become the more used one, until 15 are left).
    The gates take GATE_BANK whole (pack.RESERVED)."""
    hub = B.ROOT
    local = hub / G02_PATH
    if local.exists():
        a = np.array(Image.open(local).convert('RGBA'))
    else:
        import io
        data = subprocess.check_output(['git', '-C', str(hub), 'show', f'{ENGINE_REV_G02}:{G02_PATH}'])
        a = np.array(Image.open(io.BytesIO(data)).convert('RGBA'))
    if v is None:
        return a
    op = a[..., 3] > 0
    a[..., :3] = a[..., :3] >> 3 << 3
    count = {}
    for p in a[op][:, :3]:
        k = tuple(int(x) for x in p); count[k] = count.get(k, 0) + 1
    to = {c: c for c in count}
    while len(count) > GATE_COLOURS:
        cs = sorted(count)
        d, c1, c2 = min((sum(abs(i - j) for i, j in zip(c1, c2)), c1, c2) for n, c1 in enumerate(cs) for c2 in cs[n + 1:])
        keep, drop = (c1, c2) if count[c1] >= count[c2] else (c2, c1)
        count[keep] += count.pop(drop)
        for k in to:
            if to[k] == drop:
                to[k] = keep
    for c, t in to.items():
        if c != t:
            a[op & (a[..., :3] == c).all(-1), :3] = t
    return a

def gate_colours(v):
    a = g02(v)
    return {tuple(int(x) >> 3 for x in p) for p in a[a[..., 3] > 0][:, :3]}

def lawn_at(cv, x, r):
    lawn = E.G.textures()[E.G.GRASS]
    ys, xs = np.mgrid[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16]
    return lawn[ys % 32, xs % 32]

def put(cv, x, r, m, keep_front=False):
    """Cell (x, r) takes Violet's metatile m (both layers, its attribute), blocked. keep_front: pixels of the
    old cell that are not lawn stay, on the lower layer under the crowns (the tower's vane)."""
    if not (0 <= x < W and 0 <= r < H):
        return
    low, up = cv.v.layers(m)
    sl = cv.sl(x, r)
    if keep_front:
        old = cv.image()[sl]
        front = ~(old == lawn_at(cv, x, r)).all(-1)
        lo = low.copy(); lo[front] = old[front]      # the vane on the ground layer, the crowns over it (a bank
        cv.lower[sl] = lo; cv.upper[sl] = up         # holds the vane with the lawn, none with the crowns)
    else:
        cv.lower[sl] = low; cv.upper[sl] = up
    cv.attr[r, x] = cv.v.attr(m)
    cv.bits[r, x] = BLOCKED
    cv.changed.add((x, r)); cv.retraverse.add((x, r))

def woods(cv, xs, r0, r1, start_top=True, end_last=True, keep_front=False):
    """Forest on columns xs (whole trees: even columns pair with the next) from row r0 to r1 inclusive. r0 must be
    even when the band starts there (a crown top), r1 even when it ends there (the trunks)."""
    for r in range(r0, r1 + 1):
        if r == r0 and start_top:
            pair = START
        elif r == r1 and end_last:
            pair = LAST
        else:
            pair = BODY_EVEN if r % 2 == 0 else BODY_ODD
        for x in xs:
            put(cv, x, r, pair[x % 2], keep_front)

def gate(cv, g):
    art = g02(cv.v)
    if g['mirror']:
        art = art[:, ::-1].copy()
    gx, gy = g['origin']
    for cy in range(7):
        for cx in range(7):
            x, r = gx + cx, gy + cy
            if not (0 <= x < W):
                continue
            sl = cv.sl(x, r)
            piece = art[cy * 16:(cy + 1) * 16, cx * 16:(cx + 1) * 16]
            low = lawn_at(cv, x, r).copy()
            a = piece[..., 3] > 0
            cv.lower[sl] = low; cv.upper[sl] = 0; cv.upper[sl][a, :3] = piece[a, :3]; cv.upper[sl][a, 3] = 255
            if (x, r) in g['stairs']:
                # walked on: the gate's art on the middle layer, under the player
                cv.attr[r, x] = (B.COVERED << 12) | g['mb']; cv.bits[r, x] = WALKABLE
            else:
                cv.attr[r, x] = B.NORMAL << 12; cv.bits[r, x] = BLOCKED
            cv.changed.add((x, r)); cv.retraverse.add((x, r))

def edges(cv):
    # Top: one band of trees over rows 0-2 between the north woods (columns 34-45), the vane in front.
    woods(cv, range(34, 46), 0, 2, keep_front=True)
    # Bottom: where row 70 is the woods' last row, the woods run on off the map.
    for x in range(W):
        m70 = int(cv.v.words[70, x]) & 1023
        if m70 in LAST:
            woods(cv, [x], 70, 71, start_top=False, end_last=False)
    # West gate: G02 at (0, 25); under it (rows 32-33) a band of trees joining the woods from row 34 on.
    gate(cv, GATES[1])
    woods(cv, range(0, 8), 32, 34, end_last=False)
    # East gate: G02 mirrored at (73, 53). Above it a band of trees (rows 50-52, columns 74-77) between the
    # lawn and the gate, the stand-in house's other cells lawn; below it (rows 60-61) a band joining the woods.
    for x, r in [(73, 51), (73, 52)] + [(x, r) for x in range(74, 78) for r in range(51, 53)]:
        sl = cv.sl(x, r)
        cv.lower[sl] = lawn_at(cv, x, r); cv.upper[sl][..., 3] = 0
        cv.attr[r, x] = B.NORMAL << 12; cv.bits[r, x] = WALKABLE
        cv.changed.add((x, r)); cv.retraverse.add((x, r))
    woods(cv, range(74, 78), 50, 52)
    woods(cv, range(78, 80), 52, 52, start_top=False)     # the east woods end on the gate's top row too
    gate(cv, GATES[0])
    woods(cv, range(72, 78), 60, 62, end_last=False)
    cv.notes.append('edges: tree band above Sprout Tower, bottom woods run on, standard G02 gates west and east, sealed with trees')
