"""Platinum rooms from pret/pokeplatinum's own data (res/field), drawn by the HGSS room renderer (owner, November 8:
the Sinnoh Pokemon Center from its game). Platinum's land data is HGSS's without the background-sound block; its
building models take their textures from the area's prop texture set when they carry none.

    PLAT=path/to/pokeplatinum (res/field checked out; default: the scratch clone)

Original designs and textures: Game Freak / Nintendo / Creatures (read-only derivation).
"""
from __future__ import annotations
import json, os, re, struct, sys
from functools import lru_cache
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / 'route29_catalog')]
import hgss_render as R                 # noqa: E402
import room as RM                       # noqa: E402

PLAT = Path(os.environ.get('PLAT', '/tmp/claude-0/-home-user/68303ed6-ddf7-536b-9663-7e8a2a8f7c53/scratchpad/plat'))
F = PLAT / 'res/field'
KIND = 2                                 # room.models(): Platinum's prop models
# name: (map folder under res/field/maps, its group in groups.json)
ROOMS = {
    'plat_center': 'sandgem_town_pokecenter_1f',
    'plat_center_2f': 'sandgem_town_pokecenter_2f',
    'plat_mart': 'sandgem_town_mart',
}

def order(meson):
    return re.findall(r"'([^']+\.(?:nsbmd|nsbtx|bin))'", meson.read_text())

@lru_cache(None)
def prop_models():
    return [(F / 'props/models' / n).read_bytes() for n in order(F / 'props/models/meson.build')]

def header(room):
    return json.loads((F / 'maps' / ROOMS[room] / 'header.json').read_text())

def land_index(room):
    h = json.loads((F / 'maps' / ROOMS[room] / 'header.json').read_text())
    groups = json.loads((F / 'maps/groups.json').read_text())
    # the room's matrix: the group whose 1x1 map serves this header (header.json's mapGroup)
    g = next(g for g in groups if g['id'] == h['mapGroup'])
    return [[int(m.split('_')[1]) for m in row] for row in g['maps']]

class _Land(list):
    """Platinum land data as HGSS's: the empty background-sound block HGSS reads after the header."""
    def __getitem__(self, i):
        d = (F / f'mapmodels/data/map_data_{i:03d}.bin').read_bytes()
        return d[:16] + struct.pack('<HH', 0x1234, 0) + d[16:]

_prop_tex = {}

class _Model(R.mdlview.Model):
    def __init__(self, blob):
        super().__init__(blob)
        if self.tex is None and 'tex' in _prop_tex:
            self.tex = _prop_tex['tex']

def loader(room):
    h = header(room)
    area = json.loads((F / 'area_data' / f'{h["areaData"]}.json').read_text())
    tex0 = R.Tex0((F / 'mapmodels/texture_sets' / f'{area["mapTextureSet"]}.nsbtx').read_bytes())
    pset = int(area['mapPropSet'].split('_')[-1])
    pt = F / 'props/texture_sets' / f'prop_texture_set_{pset:03d}.nsbtx'
    _prop_tex['tex'] = R.Tex0(pt.read_bytes()) if pt.exists() else None
    grid = land_index(room)
    chunks = [dict(cx=x, cz=z, land=grid[z][x]) for z in range(len(grid)) for x in range(len(grid[0]))]
    def load(phg):
        return _Land(), tex0, prop_models(), chunks, dict(platinum=ROOMS[room], area=h['areaData'], **area)
    return load

def plat_room(name):
    """As room.hgss_room, for a Platinum room."""
    R.load = loader(name)
    R.SNAP = True
    R.mdlview.Model = _Model
    RM._cache[KIND] = prop_models()
    r = R.render(None)
    terrain = np.array(r['terrain'].convert('RGB'))
    hgt, wid = terrain.shape[:2]
    props = [RM.Prop(b['model'], tuple(b['pos']), tuple(b['scale']), KIND).draw(wid, hgt) for b in r['buildings']]
    return dict(terrain=terrain, props=props, collision=r['collision'], types=r['types'], kind=KIND, size=(wid // RM.PX, hgt // RM.PX))

def events(name):
    return json.loads((F / 'maps' / ROOMS[name] / 'events.json').read_text())
