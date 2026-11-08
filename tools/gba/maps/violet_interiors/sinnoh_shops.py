"""Sinnoh's Pokemon Center from Platinum's own data (owner, November 8: "convert the Center from HGSS for Johto (Same
for Sinnoh and Unova ...)"; plat_interior.py reads pret/pokeplatinum). Shared by Sinnoh's towns; Sandgem has it now.

    Center 1F   Platinum's Pokemon Center (PokemonCenter_1F, land data 191) as it is: the nurse's counter and healing
                machine, the PC, the lounge, the escalator up to 2F on the west at (2, 10), the exit at (8, 12). The east
                escalator went down to Platinum's Wi-Fi Plaza, which an attendant keeps shut in Platinum; here it is closed.
    Center 2F   Platinum's (PokemonCenter_2F, land data 192): the three attendants' counters, the lounge, the escalator
                down at (2, 10); the Union Room door at its back is closed. It takes the place of the Gen 3 upstairs room.

Original designs and textures: Game Freak / Nintendo / Creatures (read-only derivation).
"""
from __future__ import annotations
import json
from pathlib import Path

import room as RM
import johto_shops as JS

EXIT, ESCALATOR_1F, ESCALATOR_2F, CLOSED_1F = (8, 12), (2, 10), (2, 10), (14, 10)
NURSE = (8, 4)

def center_1f():
    r = RM.compose('plat_center', list(range(0, 17)), list(range(0, 14)))
    RM.finish(r)
    r.rect = (0, 0, 17, 13)
    r.behaviors[EXIT] = 'exit'
    r.behaviors[ESCALATOR_1F] = 'escalator_up'
    r.blocked[CLOSED_1F[1], CLOSED_1F[0]] = True               # the closed basement escalator
    r.behaviors[(NURSE[0], NURSE[1] + 1)] = 'counter'
    r.behaviors[(12, 3)] = 'pc'
    r.notes.append("Platinum's Pokemon Center 1F as it is (shared by Sinnoh's towns); the basement escalator closed")
    return r

def center_2f():
    r = RM.compose('plat_center_2f', list(range(0, 17)), list(range(0, 14)))
    RM.finish(r)
    r.rect = (0, 0, 17, 13)
    r.behaviors[ESCALATOR_2F] = 'escalator_down'
    for x in (3, 7, 12):
        r.behaviors[(x, 5)] = 'counter'
    r.notes.append("Platinum's Pokemon Center 2F as it is, in place of the Gen 3 upstairs room; the Union Room door closed")
    return r

GROUPS = {
    'sinnoh_center': dict(rooms=['SinnohPokemonCenter1F'], primary='sinnoh_center',
                          secondary='sinnoh_center', psym='SinnohCenterPrimary', ssym='SinnohCenter'),
    'sinnoh_center_2f': dict(rooms=['SinnohPokemonCenter2F'], primary='sinnoh_center_2f',
                             secondary='sinnoh_center_2f', psym='SinnohCenter2FPrimary', ssym='SinnohCenter2F'),
}
ROOMS = {'SinnohPokemonCenter1F': center_1f, 'SinnohPokemonCenter2F': center_2f}
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
                         warps=[JS.warp(EXIT, t['city'], door), JS.warp(ESCALATOR_1F, uid, 0)],
                         objects=[JS.npc('LOCALID_NURSE', 'OBJ_EVENT_GFX_NURSE', NURSE, 'DOWN', f'{center}_Nurse')],
                         scripts=JS.center_scripts(center)),
            up: dict(layout='LAYOUT_SINNOH_POKEMON_CENTER_2F', warps=[JS.warp(ESCALATOR_2F, cid, 1)], objects=[],
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
