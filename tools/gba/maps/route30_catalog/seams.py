"""Seam check for Route 30's connections (Route 29's seams.py, for north-south seams and both directions).

    python3 tools/gba/maps/route30_catalog/seams.py ENGINE_CHECKOUT

A Gen 3 map draws a connected map's nearest rows with its own tilesets. For every cell of the other map a
player can see from a walkable cell (the camera shows 7 columns either side, 8 while scrolling, and 4 rows
above and 5 below; counted generously as 8 and 5), the metatile must draw the same pixels in this map's
tileset pair as in its own map's pair. Checked from both sides of each seam.
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
from tiles import Tileset

def layout(engine, layout_id):
    L = json.loads((engine / 'data/layouts/layouts.json').read_text())['layouts']
    l = next(l for l in L if l.get('id') == layout_id)
    b = (engine / l['blockdata_filepath']).read_bytes()
    words = np.array(struct.unpack('<%dH' % (len(b) // 2), b)).reshape(l['height'], l['width'])
    name = lambda sym: next(p for p in (engine / 'data/tilesets').glob('*/*') if p.is_dir() and _sym(p) == sym)
    return words, Tileset(engine, name(l['secondary_tileset']).name, name(l['primary_tileset']).name)

def _sym(p):
    """gTileset_ symbol of a tileset directory (from graphics.h's INCGFX path)."""
    if not hasattr(_sym, 'map'):
        g = (p.parents[3] / 'src/data/tilesets/graphics.h').read_text()
        import re
        _sym.map = {m.group(2): m.group(1) for m in re.finditer(r'gTilesetTiles_(\w+)\[\] = INCGFX_U32\("data/tilesets/(\w+/\w+)/tiles\.png"', g)}
    rel = f'{p.parent.name}/{p.name}'
    return 'gTileset_' + _sym.map.get(rel, '')

def check(engine, upper, lower, offset):
    """upper: (layout id) of the map above; lower: the map below; offset: the lower map's "up" connection
    offset (the upper map's column 0 sits at the lower map's column `offset`)."""
    (wu, tu), (wl, tl) = layout(engine, upper), layout(engine, lower)
    hu = wu.shape[0]
    render = {}
    def px(t, m):
        k = (id(t), m)
        if k not in render:
            render[k] = np.array(t.render(m).convert('RGB'))
        return render[k]
    out = {}
    for name, (w_me, t_me, w_ot, t_ot, to_other) in dict(
            from_lower=(wl, tl, wu, tu, lambda x, y: (x - offset, y + hu)),
            from_upper=(wu, tu, wl, tl, lambda x, y: (x + offset, y - hu))).items():
        walk = (w_me >> 10) & 3 == 0
        seen = set()
        for y, x in zip(*np.nonzero(walk)):
            for dx in range(-8, 9):
                for dy in range(-5, 6):
                    ox, oy = to_other(x + dx, y + dy)
                    if 0 <= ox < w_ot.shape[1] and 0 <= oy < w_ot.shape[0]:
                        seen.add((ox, oy))
        bad = sorted([int(x), int(y)] for x, y in seen if (px(t_me, int(w_ot[y, x]) & 1023) != px(t_ot, int(w_ot[y, x]) & 1023)).any())
        out[name] = dict(visible_cells=len(seen), drawn_differently=bad)
    return out

def main(engine):
    res = dict(cherrygrove=check(engine, 'LAYOUT_CHERRYGROVE_ROUTE30_APPROACH', 'LAYOUT_CHERRYGROVE_CITY', 35))
    m30 = json.loads((engine / 'data/maps/CherrygroveRoute30Approach/map.json').read_text())
    up = next((c for c in m30['connections'] if c['direction'] == 'up'), None)
    if up and up['map'] == 'MAP_JOHTO_ROUTE31':
        res['route31'] = check(engine, 'LAYOUT_JOHTO_ROUTE31', 'LAYOUT_CHERRYGROVE_ROUTE30_APPROACH', up['offset'])
    print(json.dumps({k: {kk: dict(visible_cells=vv['visible_cells'], drawn_differently=len(vv['drawn_differently']), first=vv['drawn_differently'][:6]) for kk, vv in v.items()} for k, v in res.items()}))
    ok = all(not v['drawn_differently'] for r in res.values() for v in r.values())
    print('seams clean' if ok else 'SEAM MISMATCH')
    return res, ok

if __name__ == '__main__':
    r, ok = main(Path(sys.argv[1]).resolve()); sys.exit(0 if ok else 1)
