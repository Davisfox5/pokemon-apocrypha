"""Johto's Pokemon Center and Mart, shared by every Johto town (owner, November 8: "convert the Center from HGSS for
Johto ... and we need to convert the Mart but adjust the size based on the new footprint of the external building
... two counters"; the owner's choices: HGSS's 1F and B1F, the second counter varying by town). The rooms are
shops_native.py's: Emerald's own Center and Mart pieces square by square on HGSS's plans (the second pass, after the
owner rejected straight DS renders). This module installs them into each town's maps with their NPCs and scripts.

    Center 1F   nurse (8, 11) across her counter, PC (4, 10), three back counters, escalator down (15, 17), exit (8-9, 19)
    Center B1F  three counters, the lounge, escalator up (15, 11); it takes the place of the Gen 3 upstairs room
    Mart        18 x 11 for M01's 7-square front: the standard counter on the west wall (clerk (1, 4)), a second
                counter mirrored on the east wall (clerk (16, 4)), exit (4-5, 11)

Each town's second counter (proposals): Cherrygrove a Discount Corner (basic stock at three quarters of the price:
the money-poor first town, docs/JOHTO_ITEMS.md); Violet HGSS's own specialty clerk (Heal Ball and Net Ball:
HGSS's list 1 for Violet's Mart, pokeheartgold src/scrcmd_mart.c, less its Tunnel Mail, which the engine lacks).
"""
from __future__ import annotations
import json
from pathlib import Path


PX = 16
CENTER_EXIT, CENTER_EXIT2, CENTER_ESCALATOR, B1F_ESCALATOR = (8, 19), (9, 19), (15, 17), (15, 11)
MART_W = 18
MART_EXIT, MART_EXIT2 = (4, 11), (5, 11)
NURSE = (8, 11)
CLERK_A, CLERK_B = (1, 4), (MART_W - 1 - 1, 4)

GROUPS = {
    'johto_center': dict(rooms=['JohtoPokemonCenter1F'], primary='johto_center', secondary='johto_center',
                         psym='JohtoCenterPrimary', ssym='JohtoCenter'),
    'johto_center_b1': dict(rooms=['JohtoPokemonCenterB1F'], primary='johto_center_b1', secondary='johto_center_b1',
                            psym='JohtoCenterB1Primary', ssym='JohtoCenterB1'),
    'johto_mart': dict(rooms=['JohtoMart'], primary='johto_mart', secondary='johto_mart', psym='JohtoMartPrimary', ssym='JohtoMart'),
}
import shops_native as SN                  # owner, November 8 (second pass): Emerald's own pieces on HGSS's plans
ROOMS = {n: SN.ROOMS[n] for n in ('JohtoPokemonCenter1F', 'JohtoPokemonCenterB1F', 'JohtoMart')}
MAPS = {
    'JohtoPokemonCenter1F': dict(layout='LAYOUT_JOHTO_POKEMON_CENTER_1F', folder='JohtoPokemonCenter1F', shared=True),
    'JohtoPokemonCenterB1F': dict(layout='LAYOUT_JOHTO_POKEMON_CENTER_B1F', folder='JohtoPokemonCenterB1F', shared=True),
    'JohtoMart': dict(layout='LAYOUT_JOHTO_MART', folder='JohtoMart', shared=True),
}

# --------------------------------------------------------------------------- the towns' maps
TOWNS = {
    'Cherrygrove': dict(city='MAP_CHERRYGROVE_CITY', standard=['ITEM_POTION', 'ITEM_ANTIDOTE', 'ITEM_PARALYZE_HEAL'],
                        second='discount', second_stock=['ITEM_POKE_BALL', 'ITEM_POTION', 'ITEM_ANTIDOTE', 'ITEM_PARALYZE_HEAL']),
    'Violet': dict(city='MAP_VIOLET_CITY', standard=['ITEM_POKE_BALL', 'ITEM_POTION', 'ITEM_ANTIDOTE', 'ITEM_PARALYZE_HEAL',
                                                    'ITEM_AWAKENING', 'ITEM_ESCAPE_ROPE', 'ITEM_REPEL'],
                   second='special', second_stock=['ITEM_HEAL_BALL', 'ITEM_NET_BALL']),          # HGSS's Tunnel Mail: no Gen 4 mail in the engine
}

def snake(n):
    import re
    return re.sub(r'(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])', '_', n).upper().replace('1_F', '1F')

def npc(local, gfx, xy, facing, script):
    return {'local_id': local, 'graphics_id': gfx, 'x': xy[0], 'y': xy[1], 'elevation': 3, 'movement_type': f'MOVEMENT_TYPE_FACE_{facing}',
            'movement_range_x': 0, 'movement_range_y': 0, 'trainer_type': 'TRAINER_TYPE_NONE',
            'trainer_sight_or_berry_tree_id': '0', 'script': script, 'flag': '0'}

def warp(xy, dest, wid):
    return {'x': xy[0], 'y': xy[1], 'elevation': 3, 'dest_map': dest, 'dest_warp_id': str(wid)}

def stock(label, items):
    return f'    .align 2\n{label}:\n' + ''.join(f'    .2byte {i}\n' for i in items) + '    pokemartlistend\n'

def mart_scripts(name, t):
    s = (f'{name}_MapScripts::\n    .byte 0\n\n'
         f'{name}_Clerk::\n    lock\n    faceplayer\n    message gText_HowMayIServeYou\n    waitmessage\n'
         f'    pokemart {name}_Stock\n    msgbox gText_PleaseComeAgain, MSGBOX_DEFAULT\n    release\n    end\n\n')
    if t['second'] == 'discount':
        s += (f'{name}_DiscountClerk::\n    lock\n    faceplayer\n    msgbox {name}_Text_Discount, MSGBOX_DEFAULT\n'
              f'    setflag FLAG_SHOP_DISCOUNT\n    pokemart {name}_SecondStock\n    clearflag FLAG_SHOP_DISCOUNT\n'
              f'    msgbox gText_PleaseComeAgain, MSGBOX_DEFAULT\n    release\n    end\n\n'
              f'{name}_Text_Discount:\n    .string "Welcome to the DISCOUNT CORNER!\\n'
              f'Everything here is a quarter off.$"\n\n')
    else:
        s += (f'{name}_SpecialClerk::\n    lock\n    faceplayer\n    msgbox {name}_Text_Special, MSGBOX_DEFAULT\n'
              f'    pokemart {name}_SecondStock\n    msgbox gText_PleaseComeAgain, MSGBOX_DEFAULT\n    release\n    end\n\n'
              f'{name}_Text_Special:\n    .string "This counter carries items you\\n'
              f'won\'t find at the regular counter.$"\n\n')
    return s + stock(f'{name}_Stock', t['standard']) + '\n' + stock(f'{name}_SecondStock', t['second_stock'])

def center_scripts(name):
    return (f'{name}_MapScripts::\n    .byte 0\n\n{name}_Nurse::\n    setvar VAR_0x800B, LOCALID_NURSE\n'
            '    call Common_EventScript_PkmnCenterNurse\n    waitmessage\n    waitbuttonpress\n    release\n    end\n')

def install(engine, towns=TOWNS):
    """Each town's Center, its basement (the old upstairs map) and its Mart on the shared layouts: warps, the nurse,
    both clerks and their scripts. The town's own door warps keep their ids (their destinations are these maps' warp 0)."""
    engine = Path(engine)
    for town, t in towns.items():
        city = json.loads((engine / 'data/maps' / snake_city(t['city']) / 'map.json').read_text())
        door = {w['dest_map']: i for i, w in enumerate(city['warp_events'])}
        center, up, shop = f'{town}PokemonCenter', f'{town}CenterUpstairs', f'{town}Mart'
        cid, uid, mid = ('MAP_' + snake(n) for n in (center, up, shop))
        edits = {
            center: dict(layout='LAYOUT_JOHTO_POKEMON_CENTER_1F',
                         warps=[warp(CENTER_EXIT, t['city'], door[cid]), warp(CENTER_EXIT2, t['city'], door[cid]),
                                warp(CENTER_ESCALATOR, uid, 0)],
                         objects=[npc('LOCALID_NURSE', 'OBJ_EVENT_GFX_NURSE', NURSE, 'DOWN', f'{center}_Nurse')],
                         scripts=center_scripts(center)),
            up: dict(layout='LAYOUT_JOHTO_POKEMON_CENTER_B1F', warps=[warp(B1F_ESCALATOR, cid, 2)], objects=[],
                     scripts=f'{up}_MapScripts::\n    .byte 0\n'),
            shop: dict(layout='LAYOUT_JOHTO_MART', warps=[warp(MART_EXIT, t['city'], door[mid]), warp(MART_EXIT2, t['city'], door[mid])],
                       objects=[npc('LOCALID_CLERK', 'OBJ_EVENT_GFX_JOHTO_CLERK', CLERK_A, 'RIGHT', f'{shop}_Clerk'),
                                npc('LOCALID_CLERK_2', 'OBJ_EVENT_GFX_JOHTO_CLERK', CLERK_B, 'LEFT',
                                    f'{shop}_DiscountClerk' if t['second'] == 'discount' else f'{shop}_SpecialClerk')],
                       scripts=mart_scripts(shop, t)),
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

def snake_city(map_const):
    return ''.join(w.capitalize() for w in map_const[4:].split('_'))
