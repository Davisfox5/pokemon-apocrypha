"""Violet City's edges after the owner's review of #39 (docs/maps/reviews/PR39-2026-11-20.md).

- A row of trees along the top above Sprout Tower (rows 0-2), open over the tower's weathervane (no tree is drawn
  over it).
- The bottom forest runs on off the map: rows 70-71 continue the woods instead of a lawn strip below them.
- The west gate is the standard G02 (gba/art/johto-common-review/gates/refinement-4/G02.png, the same master as
  Route 31's), its stairs facing the town, the woods behind its roof and a band of trees under it.
- The east gate toward Route 31 is G02 mirrored, its stairs facing the town, where the stand-in house stood, the
  woods behind its roof and a band of trees under it.

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

def put(cv, x, r, m):
    """Cell (x, r) takes Violet's metatile m (both layers, its attribute), blocked."""
    if not (0 <= x < W and 0 <= r < H):
        return
    low, up = cv.v.layers(m)
    sl = cv.sl(x, r)
    cv.lower[sl] = low; cv.upper[sl] = up
    cv.attr[r, x] = cv.v.attr(m)
    cv.bits[r, x] = BLOCKED
    cv.changed.add((x, r)); cv.retraverse.add((x, r))

def woods(cv, xs, r0, r1, start_top=True, end_last=True):
    """Forest on columns xs (whole trees: even columns pair with the next) from row r0 to r1 inclusive. r0 must be
    even when the band starts there (a crown top), r1 even when it ends there (the trunks). start_top=False
    carries on a forest that already runs above r0 (crown bodies over the trunks of the row above)."""
    for r in range(r0, r1 + 1):
        if r == r0 and start_top:
            pair = START
        elif r == r1 and end_last:
            pair = LAST
        else:
            pair = BODY_EVEN if r % 2 == 0 else BODY_ODD
        for x in xs:
            put(cv, x, r, pair[x % 2])

def gate(cv, g, behind=()):
    """G02 at g's origin on the upper layer. The lower layer is lawn, except in the cells of `behind` (the woods
    north of the gate), where the trees go on behind the roof, whole, and the gate stands in front of them. To
    spend as few tiles as possible there, each 8x8 tile of such a cell takes one of three forms: the gate misses
    it, so it keeps the tree's own two layers (tiles the sheets already hold); the gate covers it whole, so its
    lower layer is lawn (also held); the gate covers part of it, so its lower layer is the tree flattened (the
    gate's colours have a bank of their own, so the gate cannot share the tree's upper tile)."""
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
            a = piece[..., 3] > 0
            lawn = lawn_at(cv, x, r)
            low = lawn.copy()
            up = np.zeros((16, 16, 4), np.uint8); up[a, :3] = piece[a, :3]; up[a, 3] = 255
            if (x, r) in behind:
                flat = cv.image()[sl].copy()
                old_low, old_up = cv.lower[sl].copy(), cv.upper[sl].copy()
                for ty in (0, 8):
                    for tx in (0, 8):
                        q = np.s_[ty:ty + 8, tx:tx + 8]
                        if not a[q].any():
                            low[q] = old_low[q]; up[q] = old_up[q]
                        elif not a[q].all():
                            low[q] = flat[q]
            cv.lower[sl] = low; cv.upper[sl] = up
            if (x, r) in g['stairs']:
                # walked on: the gate's art on the middle layer, under the player
                cv.attr[r, x] = (B.COVERED << 12) | g['mb']; cv.bits[r, x] = WALKABLE
            else:
                cv.attr[r, x] = B.NORMAL << 12; cv.bits[r, x] = BLOCKED
            cv.changed.add((x, r)); cv.retraverse.add((x, r))

def edges(cv):
    # Top: trees over rows 0-2 between the north woods (columns 34-45), except the two trees whose cells hold
    # Sprout Tower's weathervane (columns 38-41): those cells stay as they were, the vane against the lawn.
    woods(cv, [x for x in range(34, 46) if x not in range(38, 42)], 0, 2)
    # Bottom: where row 70 is the woods' last row, the woods run on off the map.
    for x in range(W):
        m70 = int(cv.v.words[70, x]) & 1023
        if m70 in LAST:
            woods(cv, [x], 70, 71, start_top=False, end_last=False)
    # West gate: G02 at (0, 25). The woods above it (columns 0-7, trunks on row 24) run on one more tree row
    # (trunks on row 26), behind the gate's top two rows, so no lawn shows between the trees and the roof. Under
    # it (rows 32-33) a band of trees joining the woods from row 34 on.
    woods(cv, range(0, 8), 24, 26, start_top=False)
    gate(cv, GATES[1], behind={(x, r) for x in range(0, 7) for r in (25, 26)})
    woods(cv, range(0, 8), 32, 34, end_last=False)
    # East gate: G02 mirrored at (73, 53), where the stand-in house stood (its other cells lawn). Above it the
    # woods: columns 76-79 carry on down from the east woods (no new crown top over their trunks on row 50),
    # columns 74-75 start a tree on row 50; all end with trunks on row 54, behind the gate's top two rows.
    # Below it (rows 60-61) a band joining the woods.
    for x, r in [(73, 51), (73, 52)] + [(x, r) for x in range(74, 78) for r in range(51, 53)]:
        sl = cv.sl(x, r)
        cv.lower[sl] = lawn_at(cv, x, r); cv.upper[sl][..., 3] = 0
        cv.attr[r, x] = B.NORMAL << 12; cv.bits[r, x] = WALKABLE
        cv.changed.add((x, r)); cv.retraverse.add((x, r))
    woods(cv, range(74, 76), 50, 54)
    woods(cv, range(76, 80), 50, 54, start_top=False)
    gate(cv, GATES[0], behind={(x, r) for x in range(74, 80) for r in (53, 54)})
    woods(cv, range(72, 78), 60, 62, end_last=False)
    cv.notes.append('edges: tree band above Sprout Tower (open over the vane), bottom woods run on, standard G02 '
                    'gates west and east with the woods behind their roofs')
