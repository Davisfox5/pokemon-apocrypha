"""Johto's Pokemon Center and Mart, shared by every Johto town (owner, November 8: "convert the Center from HGSS for
Johto ... and we need to convert the Mart but adjust the size based on the new footprint of the external building
... two counters, one of which will be standard items, the other of which will either be the 'Discount Corner' or
a special items dealer"; the owner's choices: HGSS's 1F and B1F, the second counter varying by town).

    Center 1F   HGSS's Pokemon Center (T21PC0101) as it is: the nurse's counter and healing machine, the PC, the
                raised back with its three counters, the escalator down at (14, 17), the exit at (8, 19)
    Center B1F  HGSS's basement (T27PC0105): its three counters, the lounge, the escalator up at (14, 10); it takes
                the place of the Gen 3 upstairs room
    Mart        HGSS's Mart (T21FS0101) four columns wider for the M01 building's 7-wide front: the standard counter
                on the west as HGSS has it, a second counter mirrored on the east wall, HGSS's shelves, cooler wall,
                cafe table and plants between, the exit at (4, 11)

Each town's second counter (proposals): Cherrygrove a Discount Corner (basic stock at three quarters of the price:
the money-poor first town, docs/JOHTO_ITEMS.md); Violet HGSS's own specialty clerk (Heal Ball and Net Ball:
HGSS's list 1 for Violet's Mart, pokeheartgold src/scrcmd_mart.c, less its Tunnel Mail, which the engine lacks).

Original designs and textures: Game Freak / Nintendo / Creatures (read-only derivation).
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np

import room as RM

PX = 16
CENTER_EXIT, CENTER_ESCALATOR, B1F_ESCALATOR = (8, 19), (14, 17), (14, 10)
MART_W = 18
MART_COLS = list(range(0, 12)) + [8, 9, 10, 11] + [12, 13]     # HGSS columns 8-11 again: four more columns of floor
MART_EXIT = (4, 11)
NURSE = (8, 11)
CLERK_A, CLERK_B = (2, 4), (MART_W - 1 - 2, 4)

def center_1f():
    r = RM.compose('center', list(range(0, 17)), list(range(0, 21)))
    RM.finish(r)
    r.rect = (0, 0, 17, 20)
    r.behaviors[CENTER_EXIT] = 'exit'
    r.behaviors[CENTER_ESCALATOR] = 'escalator_down'
    r.behaviors[(NURSE[0], NURSE[1] + 1)] = 'counter'
    for x in (2, 6, 11):                                        # the back counters
        r.behaviors[(x, 5)] = 'counter'
    r.behaviors[(4, 8)] = 'pc'                                  # HGSS's PC terminal (model 15, its sign at (4, 8))
    r.notes.append("HGSS's Pokemon Center 1F as it is (shared by Johto's towns)")
    return r

def center_b1():
    r = RM.compose('center_b1', list(range(0, 17)), list(range(0, 14)))
    RM.finish(r)
    r.rect = (0, 0, 17, 13)
    r.behaviors[B1F_ESCALATOR] = 'escalator_up'
    for x in (4, 8, 12):
        r.behaviors[(x, 5)] = 'counter'
    r.notes.append("HGSS's Pokemon Center B1F as it is, in place of the Gen 3 upstairs room")
    return r

def mart():
    """HGSS's Mart four columns wider, its counter mirrored on the east wall as the second counter."""
    r = RM.compose('mart', MART_COLS, list(range(0, 13)), keep=lambda k, p: False)
    W = MART_W
    m = lambda x: W - x                                          # HGSS's west counter mirrored onto the east wall
    # the counter's own floor and wall (HGSS columns 1-3, rows 0-8) flipped onto columns W-2 .. W-4
    h = RM.hgss_room('mart')
    T = h['terrain']
    block = h['collision'] == 128
    for hy in range(0, 9):                                       # its back wall too, so the coolers stay in the middle
        for hx in (1, 2, 3):
            nx = W - 1 - hx
            r.lower[hy * PX:(hy + 1) * PX, nx * PX:(nx + 1) * PX] = T[hy * PX:(hy + 1) * PX, hx * PX:(hx + 1) * PX][:, ::-1]
            r.blocked[hy, nx] = block[hy, hx]
    fit_quadrants(r.lower)
    # what compose took from HGSS's furniture-free collision; the furniture blocks where it stands
    props = [
        (75, 1.5, 3.5, {}), (75, 2.5, 3.5, {}), (43, 3.5, 3.5, dict(y=0.87)), (52, 3.5, 5.5, dict(y=0.86)),
        (59, 2.25, 3.0, dict(y=2.25)),                                         # the standard counter (west)
        (75, m(1.5), 3.5, dict(scale=(-1.0, 1.0, 1.0))), (75, m(2.5), 3.5, dict(scale=(-1.0, 1.0, 1.0))),
        (43, m(3.5), 3.5, dict(y=0.87, scale=(-1.0, 1.0, 1.0))), (52, m(3.5), 5.5, dict(y=0.86, scale=(-1.0, 1.0, 1.0))),
        (59, m(2.25), 3.0, dict(y=2.25, scale=(-1.0, 1.0, 1.0))),             # the second counter (east)
        (48, 5.0, 3.0, {}), (48, 7.0, 3.0, {}),                                # wall shelves
        (50, 7.0, 7.0, {}), (50, 10.0, 7.0, {}), (50, 13.0, 7.0, {}),          # display shelves
        (42, 9.0, 10.0, {}), (57, 10.5, 9.5, dict(y=-0.06, block=False)), (57, 7.5, 10.5, dict(y=-0.06, block=False)),
        (58, 10.5, 10.5, dict(y=-0.06, block=False)), (58, 7.5, 9.5, dict(y=-0.06, block=False)),   # the cafe table
        (46, 12.5, 10.0, {}),                                                  # the drinks fridge
        (23, 1.5, 11.5, {}), (23, W - 1.5, 11.5, {}),                          # plants by the door wall
        (1, 4.5, 11.5, dict(block=False)),                                     # the exit mat
    ]
    RM.finish(r, [(mdl, x, z, dict(kind=r.kind, **kw)) for mdl, x, z, kw in props])
    limit_colours(r, 68)
    r.rect = (0, 0, W, 12)
    r.behaviors[MART_EXIT] = 'exit'
    r.behaviors[(CLERK_A[0] + 1, CLERK_A[1])] = 'counter'
    r.behaviors[(CLERK_B[0] - 1, CLERK_B[1])] = 'counter'
    r.notes.append("HGSS's Mart four columns wider for the M01 front, a second counter mirrored on the east wall (proposal)")
    return r

def fit_quadrants(img, limit=14):
    """HGSS's drinks coolers draw up to 24 colours in an 8 px quadrant; Gen 3 has 15 a quadrant. Each busier quadrant
    keeps its `limit` most representative colours (median cut), in place."""
    from PIL import Image
    v = (img.astype(int) >> 3)
    for y in range(0, img.shape[0], 8):
        for x in range(0, img.shape[1], 8):
            q = v[y:y + 8, x:x + 8]
            if len(np.unique(q[..., 0] * 1024 + q[..., 1] * 32 + q[..., 2])) <= limit:
                continue
            pim = Image.fromarray(img[y:y + 8, x:x + 8]).quantize(colors=limit, method=Image.Quantize.MEDIANCUT)
            img[y:y + 8, x:x + 8] = np.array(pim.convert('RGB'))

def limit_colours(r, n):
    """The Mart's HGSS art (coolers of drinks, shelves of goods, the tiled floor) carries more colours than 13 Gen 3
    banks hold together; the whole room, both layers, takes one palette of its n most representative colours."""
    from PIL import Image
    base = r.layers
    def layers():
        low, up = base()
        on = up[..., 3] > 0
        both = np.concatenate([low.reshape(-1, 3), up[..., :3][on]])
        pal = Image.fromarray(both.reshape(-1, 1, 3)).quantize(colors=n, method=Image.Quantize.MEDIANCUT, kmeans=2)
        P = np.array(pal.getpalette()[:3 * n], int).reshape(-1, 3)
        mx, my = MART_EXIT
        mat = low[my * PX:(my + 1) * PX, mx * PX:(mx + 1) * PX].reshape(-1, 3)       # the exit mat keeps its own reds
        P = np.unique(np.concatenate([P, np.unique(mat, axis=0)]), axis=0)
        d = ((both[:, None, :].astype(int) - P[None]) ** 2).sum(-1)
        q = P[d.argmin(1)].astype(np.uint8)
        low = q[:low.size // 3].reshape(low.shape)
        up = up.copy(); up[..., :3][on] = q[low.size // 3:]
        return low, up
    r.layers = layers

GROUPS = {
    'johto_center': dict(rooms=['JohtoPokemonCenter1F'], primary='johto_center', secondary='johto_center',
                         psym='JohtoCenterPrimary', ssym='JohtoCenter'),
    'johto_center_b1': dict(rooms=['JohtoPokemonCenterB1F'], primary='johto_center_b1', secondary='johto_center_b1',
                            psym='JohtoCenterB1Primary', ssym='JohtoCenterB1'),
    'johto_mart': dict(rooms=['JohtoMart'], primary='johto_mart', secondary='johto_mart', psym='JohtoMartPrimary', ssym='JohtoMart'),
}
ROOMS = {'JohtoPokemonCenter1F': center_1f, 'JohtoPokemonCenterB1F': center_b1, 'JohtoMart': mart}
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
                         warps=[warp(CENTER_EXIT, t['city'], door[cid]), warp(CENTER_ESCALATOR, uid, 0)],
                         objects=[npc('LOCALID_NURSE', 'OBJ_EVENT_GFX_NURSE', NURSE, 'DOWN', f'{center}_Nurse')],
                         scripts=center_scripts(center)),
            up: dict(layout='LAYOUT_JOHTO_POKEMON_CENTER_B1F', warps=[warp(B1F_ESCALATOR, cid, 1)], objects=[],
                     scripts=f'{up}_MapScripts::\n    .byte 0\n'),
            shop: dict(layout='LAYOUT_JOHTO_MART', warps=[warp(MART_EXIT, t['city'], door[mid])],
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
