"""Celadon and Route 7 streamed as one world (AGENTS.md, "Streamed towns").

    python3 tools/gba/maps/route7/world.py

Gen 3 draws a connected map with the current map's tiles, and Celadon's map holds stand-in
tiles, so the route joins Celadon's streamer: one picture, Celadon's 64 x 52 cells with Route 7's
canvas (compose.py: the map's 33 columns, Celadon's 52 rows, woods above and below the map)
beside it, x 64-96. Route 7's map row y is world row y + 1 (the map connection's offset). Each
map's view looks up the world from its own origin, so either side of the seam shows the other's
real art, and the glyph cache and palette banks run on across a connection.

stream6.py does the streaming, on the world: its pictures and traversal are this module's
(Celadon's own traversal for the city's cells, compose.traversal for the route's), its outside()
the world's, and the route's ground tiles east of the paving get palettes of their own
('route_ground': its road, rock, tall grass and ledges; a tile in colours the city's ground
already holds stays in the city's banks), so the city's ground banks are packed as before and the
route's palettes stay off the city's busiest views.

Writes gba/art/route7/source/world.npz (stream6's tables, world-sized) and
gba/art/route7/evidence/engine/{stream.json, native.png, traversal.png}.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'celadon_elements'))
sys.path.insert(0, str(HERE))
import common as C             # noqa: E402
import plan as PL              # noqa: E402
import stream6 as S            # noqa: E402
import compose as R            # noqa: E402

CW, CH = PL.W, PL.H            # Celadon
WW, WH = CW + R.MW, CH         # the world
WALK = ('open', 'door', 'tall', 'arrow_e')
OUT = R.EV / 'engine'
NPZ = R.SRC / 'world.npz'
ROUTE_FAMS = dict(gate='gate', underground='underground', notice='underground')

def outside(x, y):
    """Where an off-world cell's art comes from (the engine's Source): west of Celadon its road
    to Route 16 runs on; north of the city its canal and woods run on; everywhere else the city's
    north-west forest repeats with its own period (2 across, 4 down), which is the woods' lattice
    phase on both maps."""
    if 0 <= x < WW and 0 <= y < WH:
        return x, y
    if x < 0 and 34 <= y < 38:
        return x & 1, y
    if y < 0 and 0 <= x < CW:
        return x, y & 3
    return x & 1, y & 3

def build():
    # Celadon: the concept's pictures and the city's own traversal, at its own size
    ground_c, objs_c, cells_c = S.pictures()
    foot_c, why_c, doors, walled = S.traversal(cells_c, objs_c)
    # Route 7's canvas
    kind = R.ledger()[0]
    ground_r = R.ground(kind)
    objs_r = R.objects(kind)
    foot_r, why_r = R.traversal(kind, objs_r)
    # the world
    ground = np.concatenate([ground_c, ground_r], 1)
    objs = [o for o in objs_c if o['X'] < CW * 16]          # the city's trees planted past its east edge are the route's
    for o in objs_r:
        objs.append(dict(o, X=o['X'] + CW * 16, fam=ROUTE_FAMS.get(o['fam'], o['fam']), name='r7_' + o['name']))
    objs.sort(key=lambda o: (o['Y'] + o['img'].shape[0], o['X']))
    for o in objs:
        a = o['img'][..., 3] > 0
        o['base'] = (o['Y'] + int(np.nonzero(a.any(1))[0].max())) // 16
    cells = np.concatenate([cells_c, np.where(kind == 'forest', 'forest', 'route').astype(cells_c.dtype)], 1)
    foot = np.concatenate([foot_c, foot_r.astype(foot_c.dtype)], 1)
    why = np.concatenate([why_c, why_r.astype(why_c.dtype)], 1)
    # walled in: the route's open cells the player cannot reach from the city
    from collections import deque
    walk = set(WALK)
    start = (CW - 1, 17)
    seen, q = {start}, deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if 0 <= n[0] < WW and 0 <= n[1] < WH and n not in seen and foot[n[1], n[0]] in walk:
                seen.add(n); q.append(n)
    shut = 0
    for y in range(WH):
        for x in range(CW, WW):
            if foot[y, x] in walk and (x, y) not in seen:
                foot[y, x] = 'blocked'; why[y, x] = 'walled in'; shut += 1
    return ground, objs, cells, foot, why, doors, walled + shut

def main():
    ground, objs, cells, foot, why, doors, walled = build()
    OUT.mkdir(parents=True, exist_ok=True)
    S.W, S.H = WW, WH
    S.OUT, S.NPZ = OUT, NPZ
    S.WALKABLE = WALK
    S.pictures = lambda: (ground, objs, cells)
    S.traversal = lambda cells_, objs_: (foot, why, doors, walled)
    S.outside = outside
    S.GROUPS.update(gate=(1, 15), underground=(1, 15), route_ground=(3, 'near2'))
    def hook(jobs):
        """A route ground tile whose colours the city's ground already holds (grass, the paving and
        lane run on, the grass edges along them) stays in the city's ground banks, so the route's
        own palettes stand only where its road, rock, tall grass and ledges are."""
        city = set()
        for j in jobs:
            if j['key'][2] == 0 and j['fam'] == 'ground' and j['key'][0] < CW * 2:
                city |= j['cols']
        for j in jobs:
            tx, ty, layer = j['key']
            if layer == 0 and j['fam'] == 'ground' and tx >= CW * 2 and not j['cols'] <= city:
                j['fam'] = 'route_ground'
    S.JOB_HOOK = hook
    S.main()
    rep = json.loads((OUT / 'stream.json').read_text())
    rep['world'] = dict(width=WW, height=WH, celadon=[0, 0, CW, CH], route7=[CW, R.OY, R.MW, R.MH])
    (OUT / 'stream.json').write_text(json.dumps(rep, indent=1) + '\n')

if __name__ == '__main__':
    main()
