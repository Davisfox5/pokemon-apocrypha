"""The interior of the house by Violet's east gate (door at (70, 42)).

The house outside is a copy of a Violet house, and its door block is the same four metatiles as House 1's
door, so House 1's door animation plays on it as it is: no new tile, no new metatile. This opens the door
cell, appends Violet's warp for it (after every other warp, so no warp id moves) and adds VioletHouse6 on
the plain Violet house layout (LAYOUT_VIOLET_HOUSE_5), with its exit back to the door.

Usage: house_interior.py ENGINE   (safe to run again)
"""
import json, struct, sys
from pathlib import Path

DOOR = (70, 42)
NAME, MAP, LAYOUT, EXIT = 'VioletHouse6', 'MAP_VIOLET_HOUSE_6', 'LAYOUT_VIOLET_HOUSE_5', (4, 8)
DOOR_METATILE = 202                                  # House 1's door: animated-door behaviour, a door table entry
WIDTH = 80

def main(engine):
    engine = Path(engine)
    mp = engine / 'data/layouts/VioletCity/map.bin'
    words = list(struct.unpack(f'<{mp.stat().st_size // 2}H', mp.read_bytes()))
    i = DOOR[1] * WIDTH + DOOR[0]
    assert words[i] & 1023 == DOOR_METATILE, hex(words[i])
    words[i] = 0x3000 | DOOR_METATILE                # walkable, elevation 3, as the other house doors
    mp.write_bytes(struct.pack(f'<{len(words)}H', *words))

    vj = engine / 'data/maps/VioletCity/map.json'
    violet = json.loads(vj.read_text())
    warps = violet['warp_events']
    mine = [k for k, w in enumerate(warps) if w['dest_map'] == MAP]
    if not mine:
        warps.append({'x': DOOR[0], 'y': DOOR[1], 'elevation': 0, 'dest_map': MAP, 'dest_warp_id': '0'})
        mine = [len(warps) - 1]
        vj.write_text(json.dumps(violet, indent=2) + '\n')

    d = engine / 'data/maps' / NAME
    d.mkdir(exist_ok=True)
    (d / 'map.json').write_text(json.dumps({
        'id': MAP, 'name': NAME, 'layout': LAYOUT, 'music': 'MUS_LITTLEROOT', 'region': 'REGION_JOHTO',
        'region_map_section': 'MAPSEC_VIOLET_CITY', 'requires_flash': False, 'weather': 'WEATHER_NONE',
        'map_type': 'MAP_TYPE_INDOOR', 'allow_cycling': False, 'allow_escaping': False, 'allow_running': True,
        'show_map_name': False, 'battle_scene': 'MAP_BATTLE_SCENE_NORMAL', 'build_target': 'emerald',
        'connections': None, 'object_events': [],
        'warp_events': [{'x': EXIT[0], 'y': EXIT[1], 'elevation': 0, 'dest_map': 'MAP_VIOLET_CITY', 'dest_warp_id': str(mine[0])}],
        'coord_events': [], 'bg_events': []}, indent=2) + '\n')
    (d / 'scripts.inc').write_text(f'{NAME}_MapScripts::\n    .byte 0\n')

    gp = engine / 'data/maps/map_groups.json'
    groups = json.loads(gp.read_text())
    grp = next(g for g in groups['group_order'] if 'VioletCity' in groups[g])
    if NAME not in groups[grp]:
        groups[grp].append(NAME)
        gp.write_text(json.dumps(groups, indent=2) + '\n')
    ep = engine / 'data/event_scripts.s'
    es = ep.read_text()
    inc = f'.include "data/maps/{NAME}/scripts.inc"'
    if inc not in es:
        prev = '.include "data/maps/VioletHouse5/scripts.inc"\n'
        assert es.count(prev) == 1
        ep.write_text(es.replace(prev, prev + '\n' + inc + '\n'))
    print(json.dumps({'door': DOOR, 'violet_warp': mine[0], 'map': NAME, 'layout': LAYOUT}))

if __name__ == '__main__':
    main(sys.argv[1])
