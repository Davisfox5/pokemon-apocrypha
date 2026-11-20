"""Sinnoh's Pokemon Center (owner, November 8: "convert the Center from HGSS for Johto (Same for Sinnoh and Unova
...)"). The rooms are shops_native.py's: Emerald's own Center pieces square by square on Platinum's plans (read
from pret/pokeplatinum by plat_interior.py), Emerald's 1F being Platinum's predecessor. Shared by Sinnoh's towns;
Sandgem has it now. This module installs them into each town's maps.

    Center 1F   nurse (8, 2) across her counter, PC (12, 1), escalator up (1, 8), exit (8-9, 10); the east escalator
                (Platinum's way down to its Wi-Fi Plaza, which an attendant keeps shut) is closed
    Center 2F   three counters, the lounge, escalator down (1, 8); the Union Room door is closed
"""
from __future__ import annotations
import json
from pathlib import Path

import johto_shops as JS

EXIT, EXIT2, ESCALATOR_1F, ESCALATOR_2F = (8, 10), (9, 10), (1, 8), (1, 8)
NURSE = (8, 2)

GROUPS = {
    'sinnoh_center': dict(rooms=['SinnohPokemonCenter1F'], primary='sinnoh_center',
                          secondary='sinnoh_center', psym='SinnohCenterPrimary', ssym='SinnohCenter'),
    'sinnoh_center_2f': dict(rooms=['SinnohPokemonCenter2F'], primary='sinnoh_center_2f',
                             secondary='sinnoh_center_2f', psym='SinnohCenter2FPrimary', ssym='SinnohCenter2F'),
}
import shops_native as SN                  # owner, November 8 (second pass): Emerald's own pieces on Platinum's plans
ROOMS = {n: SN.ROOMS[n] for n in ('SinnohPokemonCenter1F', 'SinnohPokemonCenter2F')}
MAPS = {
    'SinnohPokemonCenter1F': dict(layout='LAYOUT_SINNOH_POKEMON_CENTER_1F', folder='SinnohPokemonCenter1F', shared='sinnoh'),
    'SinnohPokemonCenter2F': dict(layout='LAYOUT_SINNOH_POKEMON_CENTER_2F', folder='SinnohPokemonCenter2F', shared='sinnoh'),
}
TOWNS = {'Sandgem': dict(city='MAP_SANDGEM_TOWN')}

def install(engine, towns=TOWNS):
    """Each Sinnoh town's Center and its upstairs map on the shared layouts: warps and the nurse."""
    engine = Path(engine)
    for town, t in towns.items():
        city = json.loads((engine / 'data/maps' / JS.snake_city(t['city']) / 'map.json').read_text())
        center, up = f'{town}PokemonCenter', f'{town}CenterUpstairs'
        cid, uid = ('MAP_' + JS.snake(n) for n in (center, up))
        door = next(i for i, w in enumerate(city['warp_events']) if w['dest_map'] == cid)
        edits = {
            center: dict(layout='LAYOUT_SINNOH_POKEMON_CENTER_1F',
                         warps=[JS.warp(EXIT, t['city'], door), JS.warp(EXIT2, t['city'], door), JS.warp(ESCALATOR_1F, uid, 0)],
                         objects=[JS.npc('LOCALID_NURSE', 'OBJ_EVENT_GFX_NURSE', NURSE, 'DOWN', f'{center}_Nurse')],
                         scripts=JS.center_scripts(center)),
            up: dict(layout='LAYOUT_SINNOH_POKEMON_CENTER_2F', warps=[JS.warp(ESCALATOR_2F, cid, 2)], objects=[],
                     scripts=f'{up}_MapScripts::\n    .byte 0\n'),
        }
        for name, e in edits.items():
            p = engine / 'data/maps' / name / 'map.json'
            mj = json.loads(p.read_text())
            mj['layout'] = e['layout']
            mj['warp_events'] = e['warps']
            mj['object_events'] = e['objects']
            mj['bg_events'] = []
            mj['coord_events'] = []
            p.write_text(json.dumps(mj, indent=2) + '\n')
            (p.parent / 'scripts.inc').write_text(e['scripts'])
