"""Canalave City's reference: Platinum's own map data rendered 1:1 at 16 px per cell.

    PLAT=path/to/pokeplatinum python3 tools/gba/maps/canalave_city/reference.py CACHE_DIR

Reads pret/pokeplatinum's res/field (land data, map and prop texture sets, prop models, events) through the HGSS
renderer (route29_catalog/hgss_render.py, as violet_interiors/plat_interior.py does for rooms). Canalave is the
TownsAndRoutes matrix cells (1, 22) and (1, 23); the render takes the chunks round it too, so the native map can
carry a camera margin of Platinum's own surroundings: sea to the north, forest west, south and east, and Route
218's first seven columns (its gatehouse front) east of rows 32-63.

Native cell = Platinum cell + (7, 7); the native map is 46 x 78.

Original designs and textures: Game Freak / Nintendo / Creatures (read-only derivation).
"""
from __future__ import annotations
import json, os, pickle, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
PATHS = [str(HERE.parent / "violet_interiors"), str(HERE.parent / "route29_catalog")]

MARGIN = 7
CW, CH = 32, 64                          # Platinum Canalave, cells
W, H = CW + 2 * MARGIN, CH + 2 * MARGIN  # native map
MATRIX = (1, 22)                         # Canalave's north chunk in TownsAndRoutes
PX = 16

def _region(PI, folder, cells):
    R, F = PI.R, PI.F
    h = json.loads((F / 'maps' / folder / 'header.json').read_text())
    area = json.loads((F / 'area_data' / f'{h["areaData"]}.json').read_text())
    tex0 = R.Tex0((F / 'mapmodels/texture_sets' / f'{area["mapTextureSet"]}.nsbtx').read_bytes())
    pset = int(area['mapPropSet'].split('_')[-1])
    pt = F / 'props/texture_sets' / f'prop_texture_set_{pset:03d}.nsbtx'
    PI._prop_tex['tex'] = R.Tex0(pt.read_bytes()) if pt.exists() else None
    g = json.loads((F / 'maps/groups.json').read_text())[0]
    x0, z0 = min(c[0] for c in cells), min(c[1] for c in cells)
    chunks = [dict(cx=x - x0, cz=z - z0, land=int(g['maps'][z][x].split('_')[1]))
              for x, z in cells if g['maps'][z][x] != 'MAP_NONE']
    R.load = lambda phg: (PI._Land(), tex0, PI.prop_models(), chunks, dict(area=h['areaData'], **area))
    R.SNAP = True; R.mdlview.Model = PI._Model
    r = R.render(None)
    return {k: (np.array(v) if isinstance(v, Image.Image) else v) for k, v in r.items()}

def render(cache):
    """Render (or load) the neighbourhood and Route 218's west end."""
    cache = Path(cache); cache.mkdir(parents=True, exist_ok=True)
    p = cache / 'canalave-reference.pkl'
    if p.exists():
        return pickle.loads(p.read_bytes())
    sys.path[:0] = PATHS
    import plat_interior as PI
    mx, mz = MATRIX
    a = _region(PI, 'canalave_city', [(x, z) for z in range(mz - 1, mz + 3) for x in range(mx - 1, mx + 2) if (x, z) != (mx + 1, mz + 1)])
    b = _region(PI, 'route_218', [(mx + 1, mz + 1)])
    ev = json.loads((PI.F / 'maps/canalave_city/events.json').read_text())
    text = json.loads((PI.PLAT / 'res/text/canalave_city.json').read_text())['messages']
    d = dict(a=a, b=b, events=ev, text=text, plat_rev=os.popen(f'git -C {PI.PLAT} rev-parse HEAD').read().strip())
    p.write_bytes(pickle.dumps(d))
    return d

def crop(d):
    """The native map's window of the render: full, ground, fg (RGBA), sea mask, material names per pixel,
    Platinum collision and terrain types per cell (margin cells blocked, type 0)."""
    a, b = d['a'], d['b']
    x0 = z0 = 32 - MARGIN
    def cut(arr):
        return arr[z0 * PX:(z0 + H) * PX, x0 * PX:(x0 + W) * PX].copy()
    out = {k: cut(a[k]) for k in ('full', 'ground', 'terrain', 'fg', 'ground_mat', 'fg_owner', 'holes')}
    names = list(a['materials']); nb = list(b['materials'])
    mat = np.array(names + ['?'], object)[np.clip(out['ground_mat'], -1, len(names))]
    ex, ez = (MARGIN + CW) * PX, (MARGIN + 32) * PX
    for k in ('full', 'ground', 'terrain', 'fg'):
        out[k][ez:ez + 32 * PX, ex:ex + MARGIN * PX] = b[k][:32 * PX, :MARGIN * PX]
    mat[ez:ez + 32 * PX, ex:ex + MARGIN * PX] = np.array(nb + ['?'], object)[np.clip(b['ground_mat'][:32 * PX, :MARGIN * PX], -1, len(nb))]
    out['holes'][ez:ez + 32 * PX, ex:ex + MARGIN * PX] = b['holes'][:32 * PX, :MARGIN * PX]
    out['fg_owner'][ez:ez + 32 * PX, ex:ex + MARGIN * PX] = -1
    out['mat'] = mat
    out['sea'] = (mat == 'sea') | out['holes']
    coll = np.ones((H, W), bool); types = np.zeros((H, W), np.uint8)
    coll[MARGIN:MARGIN + CH, MARGIN:MARGIN + CW] = a['collision'][32:96, 32:64] != 0
    types[MARGIN:MARGIN + CH, MARGIN:MARGIN + CW] = a['types'][32:96, 32:64]
    out['collision'], out['types'] = coll, types
    out['buildings'] = [dict(b_, pos=[b_['pos'][0] - x0, b_['pos'][1], b_['pos'][2] - z0],
                             footprint=[b_['footprint'][0] - x0, b_['footprint'][1] - z0, b_['footprint'][2] - x0, b_['footprint'][3] - z0])
                        for b_ in a['buildings']]
    return out

if __name__ == '__main__':
    d = render(sys.argv[1]); c = crop(d)
    Image.fromarray(c['full']).save(Path(sys.argv[1]) / 'platinum-canalave.png')
    print(c['full'].shape, d['plat_rev'])
