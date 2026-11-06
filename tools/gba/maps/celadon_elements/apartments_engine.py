"""The apartment block's elevator and floor scripts in the engine (called by install6.py).

    the car     KantoCeladonApartmentsLift on Lilycove Dept Store's own elevator layout (the car
                as Emerald draws it, its window lights included), its attendant at the panel as
                Lilycove's; she takes the player to 1F-6F (the roof is up the penthouse's stairs)
                with Emerald's elevator ride (special MoveElevator); the car's two exit cells
                lead out by the dynamic warp
    the floors  each floor (KantoCeladonApartments, ...Floor2-6) on arriving sets
                VAR_APOC_CELADON_LIFT_FLOOR to its number and the dynamic warp to its own
                elevator door, so the car always opens where the player got in
    the var     VAR_APOC_CELADON_LIFT_FLOOR is VAR_UNUSED_0x4083 (named in vars.h, the
                Apocrypha way: an alias on an unused var)

Rewrites its files on every run; adds the car to gMapGroup_Kanto, data/event_scripts.s and
src/apocrypha_map_proof.c once.
"""
from __future__ import annotations
import json, re
from pathlib import Path

LIFT = 'KantoCeladonApartmentsLift'
FLOORS = [(1, 'KantoCeladonApartments'), (2, 'KantoCeladonApartmentsFloor2'), (3, 'KantoCeladonApartmentsFloor3'),
          (4, 'KantoCeladonApartmentsFloor4'), (5, 'KantoCeladonApartmentsFloor5'), (6, 'KantoCeladonApartmentsFloor6')]
DOOR = (16, 1)                                  # each floor's elevator door (apartments_native.LIFT + 1, row 1)
VAR, VAR_SLOT = 'VAR_APOC_CELADON_LIFT_FLOOR', 'VAR_UNUSED_0x4083'
MAPSEC, MUSIC = 'MAPSEC_CELADON_CITY', 'MUS_RG_CELADON'

def map_id(name):
    return 'MAP_' + ''.join('_' + c if c.isupper() and i else c for i, c in enumerate(name)).upper()

def read(p): return json.loads(p.read_text())
def write(p, v): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(v, indent=2, ensure_ascii=False) + '\n')

def var(g):
    p = g / 'include/constants/vars.h'
    s = p.read_text()
    if f'#define {VAR} ' in s:
        return
    line = f'#define {VAR} {VAR_SLOT} // Apocrypha: the Celadon apartments\' elevator, the floor the player is on (1-6)\n'
    anchor = '\n#if TESTING\n'
    assert anchor in s, 'vars.h layout'
    p.write_text(s.replace(anchor, '\n' + line + anchor, 1))

def floor_scripts(g):
    for n, name in FLOORS:
        (g / f'data/maps/{name}/scripts.inc').write_text(
            f'{name}_MapScripts::\n'
            f'    map_script MAP_SCRIPT_ON_TRANSITION, {name}_OnTransition\n'
            f'    .byte 0\n'
            f'\n{name}_OnTransition:\n'
            f'    setvar {VAR}, {n}\n'
            f'    setdynamicwarp {map_id(name)}, {DOOR[0]}, {DOOR[1]}\n'
            f'    end\n')
    roof = 'KantoCeladonApartmentsRoof'
    (g / f'data/maps/{roof}/scripts.inc').write_text(f'{roof}_MapScripts::\n    .byte 0\n')

def lift_script():
    L = LIFT
    s = (f'{L}_MapScripts::\n    .byte 0\n\n'
         f'{L}_EventScript_Attendant::\n'
         f'    lock\n    faceplayer\n'
         f'    message {L}_Text_WhichFloor\n    waitmessage\n'
         f'    setvar VAR_0x8004, 6\n    subvar VAR_0x8004, {VAR}\n'
         f'    dynmultichoice 0, 0, FALSE, 7, VAR_0x8004, DYN_MULTICHOICE_CB_NONE, '
         + ', '.join(f'{L}_Text_{k}F' for k in range(6, 0, -1)) + f', {L}_Text_Exit\n'
         f'    switch VAR_RESULT\n')
    for i, k in enumerate(range(6, 0, -1)):
        s += f'    case {i}, {L}_EventScript_{k}F\n'
    s += f'    goto {L}_EventScript_Exit\n    end\n'
    for k in range(6, 0, -1):
        name = dict(FLOORS)[k]
        s += (f'\n{L}_EventScript_{k}F::\n'
              f'    setdynamicwarp {map_id(name)}, {DOOR[0]}, {DOOR[1]}\n'
              f'    goto_if_eq {VAR}, {k}, {L}_EventScript_Exit\n'
              f'    copyvar VAR_0x8005, {VAR}\n'
              f'    setvar VAR_0x8006, {k}\n'
              f'    call {L}_EventScript_Ride\n'
              f'    setvar {VAR}, {k}\n'
              f'    goto {L}_EventScript_Exit\n    end\n')
    s += (f'\n{L}_EventScript_Ride::\n'
          f'    closemessage\n'
          f'    applymovement VAR_LAST_TALKED, Common_Movement_WalkInPlaceFasterDown\n'
          f'    waitmovement 0\n    waitse\n    special MoveElevator\n    waitstate\n    return\n'
          f'\n{L}_EventScript_Exit::\n    closemessage\n    release\n    end\n')
    for k in range(6, 0, -1):
        s += f'\n{L}_Text_{k}F:\n    .string "{k}F$"\n'
    s += f'\n{L}_Text_Exit:\n    .string "EXIT$"\n'
    s += f'\n{L}_Text_WhichFloor:\n    .string "Which floor would you like?$"\n'
    return s

def lift(g):
    src = read(g / 'data/maps/LilycoveCity_DepartmentStoreElevator/map.json')
    m = dict(src)
    m.update(id=map_id(LIFT), name=LIFT, music=MUSIC, region_map_section=MAPSEC, connections=None,
             object_events=[dict(src['object_events'][0], script=f'{LIFT}_EventScript_Attendant')],
             warp_events=src['warp_events'], coord_events=[], bg_events=[])
    m['region'] = 'REGION_KANTO'
    m['build_target'] = 'emerald'                  # a Kanto map in the Emerald build (mapjson drops it otherwise)
    for k in sorted(k for k in ('region', 'build_target') if k in m):
        m[k] = m.pop(k)
    write(g / f'data/maps/{LIFT}/map.json', m)
    (g / f'data/maps/{LIFT}/scripts.inc').write_text(lift_script())
    groups = read(g / 'data/maps/map_groups.json')
    if LIFT not in groups['gMapGroup_Kanto']:
        groups['gMapGroup_Kanto'].append(LIFT)
        write(g / 'data/maps/map_groups.json', groups)
    ev = g / 'data/event_scripts.s'
    inc = f'.include "data/maps/{LIFT}/scripts.inc"'
    if inc not in ev.read_text():
        with ev.open('a') as f:
            f.write(f'\n{inc}\n')
    p = g / 'src/apocrypha_map_proof.c'; s = p.read_text()
    if map_id(LIFT) not in s:
        anchor = re.search(r'(const u16 sMapProofMaps\[\] = \{[^}]*)\};', s)   # appended: the list keeps the group's order
        assert anchor, 'map proof list'
        p.write_text(s.replace(anchor.group(0), anchor.group(1) + ', ' + map_id(LIFT) + '};', 1))

def install(g: Path):
    var(g)
    lift(g)
    floor_scripts(g)
    return dict(lift=LIFT, floors=[name for _, name in FLOORS], var=f'{VAR} = {VAR_SLOT}')
