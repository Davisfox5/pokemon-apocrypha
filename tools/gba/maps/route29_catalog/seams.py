"""Seam check: a Gen 3 map draws a connected map's nearest 7 columns with its own tilesets. Every metatile
on both sides of both seams must draw the same pixels in Route 29's tileset pair as in the town's.

    python3 tools/gba/maps/route29_catalog/seams.py ENGINE_CHECKOUT
"""
import json, struct, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
from tiles import Tileset
from reference import W, H

def grid(engine, layout, w):
    b = (engine / f'data/layouts/{layout}/map.bin').read_bytes()
    return np.array(struct.unpack('<%dH' % (len(b) // 2), b)).reshape(-1, w) & 1023

def main(engine):
    r29 = Tileset(engine, 'route29_hgss', 'cherrygrove')
    towns = dict(west=('CherrygroveCity', 'cherrygrove', 80), east=('NewBarkTown', 'new_bark', 36))
    g = grid(engine, 'CherrygroveRoute29Approach', W)
    out = {}
    for side, (layout, sec, w) in towns.items():
        t = Tileset(engine, sec, 'cherrygrove'); tg = grid(engine, layout, w)
        theirs = tg[:, w - 8:] if side == 'west' else tg[:, :8]
        ours = g[:, :8] if side == 'west' else g[:, W - 8:]
        def bad(ids):
            return sorted(f'{m:#05x}' for m in {int(v) for v in ids.ravel()}
                          if (np.array(r29.render(m)) != np.array(t.render(m))).any())
        out[side] = dict(town=layout, town_edge_ids_drawn_differently_by_route29=bad(theirs),
                         route29_edge_ids_drawn_differently_by_town=bad(ours),
                         town_edge_ids=len({int(v) for v in theirs.ravel()}), route29_edge_ids=len({int(v) for v in ours.ravel()}))
    # What a player can actually see across each seam: the camera shows 7 columns either side of the player
    # (8 while scrolling) and 5 rows above and below. Count only cells visible from a walkable town cell.
    for side, (layout, sec, w) in towns.items():
        b = (engine / f'data/layouts/{layout}/map.bin').read_bytes()
        words = np.array(struct.unpack('<%dH' % (len(b) // 2), b)).reshape(-1, w)
        walk = (words >> 10) & 3 == 0
        off = 0 if side == 'west' else 6
        t = Tileset(engine, sec, 'cherrygrove')
        seen = set()
        for ty, tx in zip(*np.nonzero(walk)):
            reach = 8 - (w - 1 - tx) if side == 'west' else 8 - tx
            for k in range(max(0, reach)):
                rx = k if side == 'west' else W - 1 - k
                for dy in range(-5, 6):
                    ry = ty + off + dy if side == 'east' else ty + dy
                    if 0 <= ry < H:
                        seen.add((rx, ry))
        bad = sorted({(x, y) for x, y in seen if (np.array(r29.render(int(g[y, x]))) != np.array(t.render(int(g[y, x])))).any()})
        out[side]['route29_cells_visible_from_town'] = len(seen)
        out[side]['visible_cells_drawn_differently'] = [list(c) for c in bad]
    print(json.dumps(out, indent=1))
    ok = all(not v['town_edge_ids_drawn_differently_by_route29'] and not v['visible_cells_drawn_differently'] for v in out.values())
    print('seams clean' if ok else 'SEAM MISMATCH')
    return out, ok

if __name__ == '__main__':
    o, ok = main(Path(sys.argv[1]).resolve()); sys.exit(0 if ok else 1)
