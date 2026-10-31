"""Violet City's doors: every building's door opens with an animation and leads inside.

Each door cell takes the animated-door behaviour and is walkable; field_door.c draws the door's 2x2 block
(the door cell, the cell beside it, the row above) in three frames cut from the town's upper layer, the
door panel going dark from its far edge, on the top layer over each cell's own bottom layer (.layered, an
engine addition): one bank per frame tile, every colour of every tile checked. The frames go to graphics/door_anims/violet, their table entries to field_door.c
between this tool's markers. Each door's cell has its own metatile (pack.UNIQUE), so the door table finds
its own frames. Behind the doors are interiors on the engine's shared layouts (Center, Mart, houses, the
Pokemon School for the university and the lecture hall, a stand-in room for Sprout Tower until its floors
are built), each with its exit warps back to its door. The east gate building keeps its own warp.
"""
from __future__ import annotations
import json, re
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
import sys
sys.path[:0] = [str(HERE)]
import base as B                                     # noqa: E402

MB_ANIMATED_DOOR = 0x69
WALKABLE = 0x3000                                    # elevation 3, collision 0
DOOR_DIR = 'graphics/door_anims/violet'
BEGIN, END = '// Violet City doors (tools/gba/maps/violet_city/doors.py): begin', '// Violet City doors: end'
TABLE_BEGIN, TABLE_END = '    // Violet City door table (doors.py): begin', '    // Violet City door table: end'

def house(cx, ry):
    """A Violet house's door: the cell on its bottom row, the planked panel in the art's own place."""
    return dict(cell=(cx, ry + 1), panel=(16 * cx + 2, 16 * ry + 6, 16 * cx + 15, 16 * ry + 19))

# name, door cell, panel (px, x1/y1 exclusive), door sound, interior (None: the warp already there)
DOORS = [
    dict(name='SproutTower', cell=(39, 12), panel=(630, 190, 642, 198), sound='NORMAL',
         map='SproutTower1F', layout='LAYOUT_RUSTBORO_CITY_HOUSE1', exits=[(5, 7), (6, 7)], music='MUS_LITTLEROOT'),
    dict(name='University', cell=(57, 42), panel=(918, 670, 930, 678), sound='NORMAL',
         map='VioletUniversity', layout='LAYOUT_RUSTBORO_CITY_POKEMON_SCHOOL', exits=[(5, 10), (6, 10)], music='MUS_SCHOOL'),
    dict(name='LectureHall', cell=(31, 41), panel=(496, 651, 514, 666), sound='SLIDING',
         map='VioletLectureHall', layout='LAYOUT_RUSTBORO_CITY_POKEMON_SCHOOL', exits=[(5, 10), (6, 10)], music='MUS_SCHOOL'),
    dict(name='Mart', cell=(21, 40), panel=(339, 629, 353, 649), sound='SLIDING',
         map='VioletMart', layout='LAYOUT_MART', exits=[(3, 7), (4, 7)], music='MUS_POKE_MART', kind='mart'),
    dict(name='PokemonCenter', cell=(49, 55), panel=(784, 880, 800, 890), sound='SLIDING',
         map='VioletPokemonCenter', layout='LAYOUT_POKEMON_CENTER_1F', exits=[(7, 8), (6, 8)], music='MUS_POKE_CENTER', kind='center'),
    dict(name='House1', **house(11, 26), sound='NORMAL', map='VioletHouse1', layout='LAYOUT_HOUSE1', exits=[(3, 8), (4, 8)], music='MUS_LITTLEROOT'),
    dict(name='House2', **house(10, 37), sound='NORMAL', map='VioletHouse2', layout='LAYOUT_HOUSE2', exits=[(3, 7), (4, 7)], music='MUS_LITTLEROOT'),
    dict(name='House3', **house(26, 55), sound='NORMAL', map='VioletHouse3', layout='LAYOUT_HOUSE3', exits=[(3, 7), (4, 7)], music='MUS_LITTLEROOT'),
    dict(name='House4', **house(36, 60), sound='NORMAL', map='VioletHouse4', layout='LAYOUT_HOUSE4', exits=[(3, 8), (4, 8)], music='MUS_LITTLEROOT'),
    dict(name='House5', **house(56, 63), sound='NORMAL', map='VioletHouse5', layout='LAYOUT_HOUSE1', exits=[(3, 8), (4, 8)], music='MUS_LITTLEROOT'),
    dict(name='EastGate', **house(74, 55), sound='NORMAL', map=None),
]
UPSTAIRS = dict(map='VioletCenterUpstairs', layout='LAYOUT_POKEMON_CENTER_2F', stairs=(1, 6))
MART_STOCK = ['ITEM_POKE_BALL', 'ITEM_POTION', 'ITEM_ANTIDOTE', 'ITEM_PARALYZE_HEAL', 'ITEM_AWAKENING',
              'ITEM_ESCAPE_ROPE', 'ITEM_REPEL']   # docs/JOHTO_ITEMS.md, Violet Mart
GATE_WARPS = 2                                       # Violet's own warps (the east gate's door, the west gate) come first

def mark(cv):
    """The door cells: the animated-door behaviour, walkable; each its own metatile."""
    import pack as P
    P.UNIQUE = set()
    for d in DOORS:
        x, y = d['cell']
        cv.attr[y, x] = (int(cv.attr[y, x]) & 0xF000) | MB_ANIMATED_DOOR
        cv.bits[y, x] = WALKABLE
        cv.retraverse.add((x, y)); cv.changed.add((x, y))
        P.UNIQUE.add((x, y))
    cv.notes.append(f'{len(DOORS)} animated doors')

def banks(engine):
    """The installed 13 banks (primary 0-5, secondary 6-12)."""
    out = []
    for b in range(13):
        d = engine / (B.PRIMARY if b < 6 else B.SECONDARY)
        out.append(B.read_pal(d / f'palettes/{b:02d}.pal'))
    return out

def snake(name):
    return re.sub(r'(?<!^)(?=[A-Z0-9])', '_', name).upper().replace('_1_F', '_1F')

def frames(engine, cv, words):
    """Three frames per door: each cell's own upper layer (cv, as packed) with the door panel going dark from its
    far edge. field_door.c draws them on the top layer over the cell's own bottom layer (.layered), so the ground
    under the building stays its own tiles; each frame tile takes a bank holding every colour it draws (the
    tile's own upper bank always does) and the dark tone nearest the panel's darkest. Written with their door
    table entries."""
    pals = banks(engine)
    p5 = [np.array(b[1:16], int) >> 3 for b in pals]
    (engine / DOOR_DIR).mkdir(parents=True, exist_ok=True)
    defs, table, report = [], [], {}
    for d in DOORS:
        x, y = d['cell']
        x0, y0 = x * 16, (y - 1) * 16                # the block: the door cell and the one right of it, the row above
        up = cv.upper[y0:y0 + 32, x0:x0 + 32].astype(int)
        comp = cv.image()[y0:y0 + 32, x0:x0 + 32].astype(int)
        px0, py0, px1, py1 = d['panel']
        px0, px1 = max(px0, x0), min(px1, x0 + 32)
        panel = comp[py0 - y0:py1 - y0, px0 - x0:px1 - x0].reshape(-1, 3)
        dark = panel[np.argmin(panel.sum(1))] >> 3   # the panel's own darkest tone: the open doorway
        fr = []                                      # (rgb5, opaque) per frame
        for k in range(3):
            rgb, a = up[..., :3] >> 3, up[..., 3] > 0
            rgb, a = rgb.copy(), a.copy()
            cut = px1 - int(round((px1 - px0) * (k + 1) / 3))
            rgb[py0 - y0:py1 - y0, cut - x0:px1 - x0] = -1   # the doorway: the bank's tone nearest dark
            a[py0 - y0:py1 - y0, cut - x0:px1 - x0] = True
            fr.append((rgb, a))
        order = [(cx, cy, q) for cx, cy in ((0, 0), (0, 1), (1, 0), (1, 1)) for q in range(4)]
        data, tile_banks, off = bytearray(), [], 0
        for i, (cx, cy, q) in enumerate(order):
            sl = np.s_[cy * 16 + (q // 2) * 8:cy * 16 + (q // 2) * 8 + 8, cx * 16 + (q % 2) * 8:cx * 16 + (q % 2) * 8 + 8]
            need = {tuple(p) for rgb, a in fr for p in rgb[sl][a[sl]] if p[0] >= 0}
            fits = [b for b in range(13) if need <= {tuple(c) for c in p5[b]}]
            if not fits:
                fits = [min(range(13), key=lambda b: len(need - {tuple(c) for c in p5[b]}))]
                off += len(need - {tuple(c) for c in p5[fits[0]]})
            tile_banks.append(min(fits, key=lambda b: int(((p5[b] - dark) ** 2).sum(1).min())))
        for rgb, a in fr:
            for i, (cx, cy, q) in enumerate(order):
                sl = np.s_[cy * 16 + (q // 2) * 8:cy * 16 + (q // 2) * 8 + 8, cx * 16 + (q % 2) * 8:cx * 16 + (q % 2) * 8 + 8]
                pal = p5[tile_banks[i]]
                t = np.where(rgb[sl] < 0, dark, rgb[sl])
                idx = 1 + ((t[..., None, :] - pal[None, None]) ** 2).sum(-1).argmin(-1)
                idx[~a[sl]] = 0
                for row in idx:
                    data += bytes(int(row[j]) | (int(row[j + 1]) << 4) for j in range(0, 8, 2))
        (engine / DOOR_DIR / f'{d["name"]}.4bpp').write_bytes(bytes(data))
        m = int(words[y, x]) & 1023
        tileset = 'gTileset_VioletCity' if m >= 512 else 'gTileset_VioletCityPrimary'
        pal = ','.join(str(b) for b in tile_banks) + ',0,0,0,0'
        defs.append(f'static const u8 sVioletDoor_{d["name"]}[] = INCBIN_U8("{DOOR_DIR}/{d["name"]}.4bpp");\n'
                    f'static const u8 sVioletDoorPal_{d["name"]}[20] = {{{pal}}};')
        table.append(f'    {{.metatileNum={m}, .tileset=&{tileset}, .sound=DOOR_SOUND_{d["sound"]}, .size=DOOR_SIZE_2x2_LEFT, '
                     f'.tiles=sVioletDoor_{d["name"]}, .palettes=sVioletDoorPal_{d["name"]}, .layered=TRUE}},')
        report[d['name']] = dict(cell=[x, y], metatile=m, banks=tile_banks, colours_off_palette=off)
    src = (engine / 'src/field_door.c').read_text()
    block_defs = '\n'.join([BEGIN, 'extern const struct Tileset gTileset_VioletCityPrimary;',
                            'extern const struct Tileset gTileset_VioletCity;'] + defs + [END])
    block_table = '\n'.join([TABLE_BEGIN] + table + [TABLE_END])
    if BEGIN in src:
        src = re.sub(re.escape(BEGIN) + r'.*?' + re.escape(END), lambda _: block_defs, src, flags=re.S)
        src = re.sub(re.escape(TABLE_BEGIN) + r'.*?' + re.escape(TABLE_END), lambda _: block_table, src, flags=re.S)
    else:
        anchor = 'static const struct DoorGraphics sDoorAnimGraphicsTable[] =\n{\n'
        assert src.count(anchor) == 1, 'the door table'
        src = src.replace(anchor, block_defs + '\n\n' + anchor + block_table + '\n')
    (engine / 'src/field_door.c').write_text(src)
    gi = engine / '.gitignore'
    g = gi.read_text()
    if f'!{DOOR_DIR}/*.4bpp' not in g:
        g = g.replace('!graphics/door_anims/sandgem/*.4bpp\n', f'!graphics/door_anims/sandgem/*.4bpp\n!{DOOR_DIR}/*.4bpp\n')
        gi.write_text(g)
    return report

# --------------------------------------------------------------------------- warps and interiors
def interior_json(name, layout, music, warps, objects=()):
    return {
        'id': 'MAP_' + snake(name), 'name': name, 'layout': layout, 'music': music, 'region': 'REGION_JOHTO',
        'region_map_section': 'MAPSEC_VIOLET_CITY', 'requires_flash': False, 'weather': 'WEATHER_NONE',
        'map_type': 'MAP_TYPE_INDOOR', 'allow_cycling': False, 'allow_escaping': False, 'allow_running': True,
        'show_map_name': False, 'battle_scene': 'MAP_BATTLE_SCENE_NORMAL', 'build_target': 'emerald',
        'connections': None, 'object_events': list(objects), 'warp_events': warps, 'coord_events': [], 'bg_events': []}

def npc(local, gfx, x, y, facing, script):
    return {'local_id': local, 'graphics_id': gfx, 'x': x, 'y': y, 'elevation': 3, 'movement_type': f'MOVEMENT_TYPE_FACE_{facing}',
            'movement_range_x': 0, 'movement_range_y': 0, 'trainer_type': 'TRAINER_TYPE_NONE',
            'trainer_sight_or_berry_tree_id': '0', 'script': script, 'flag': '0'}

def scripts(name, kind):
    s = f'{name}_MapScripts::\n    .byte 0\n'
    if kind == 'center':
        s += (f'\n{name}_Nurse::\n    setvar VAR_0x800B, LOCALID_NURSE\n    call Common_EventScript_PkmnCenterNurse\n'
              '    waitmessage\n    waitbuttonpress\n    release\n    end\n')
    if kind == 'mart':
        s += (f'\n{name}_Clerk::\n    lock\n    faceplayer\n    message gText_HowMayIServeYou\n    waitmessage\n'
              f'    pokemart {name}_Stock\n    msgbox gText_PleaseComeAgain, MSGBOX_DEFAULT\n    release\n    end\n\n'
              f'    .align 2\n{name}_Stock:\n' + ''.join(f'    .2byte {i}\n' for i in MART_STOCK) + '    pokemartlistend\n')
    return s

def interiors(engine):
    """Violet's door warps (after its own two), each interior's map, scripts, group and include."""
    vj = engine / 'data/maps/VioletCity/map.json'
    violet = json.loads(vj.read_text())
    warps = violet['warp_events'][:GATE_WARPS]
    made = []
    for d in DOORS:
        x, y = d['cell']
        if d['map'] is None:
            assert any((w['x'], w['y']) == (x, y) for w in warps), ('a door with no warp', d['name'])
            continue
        idx = len(warps)
        warps.append({'x': x, 'y': y, 'elevation': 0, 'dest_map': 'MAP_' + snake(d['map']), 'dest_warp_id': '0'})
        exits = [{'x': ex, 'y': ey, 'elevation': 3 if d.get('kind') == 'center' else 0, 'dest_map': 'MAP_VIOLET_CITY',
                  'dest_warp_id': str(idx)} for ex, ey in d['exits']]
        objs = []
        if d.get('kind') == 'center':
            exits.append({'x': UPSTAIRS['stairs'][0], 'y': UPSTAIRS['stairs'][1], 'elevation': 4,
                          'dest_map': 'MAP_' + snake(UPSTAIRS['map']), 'dest_warp_id': '0'})
            objs = [npc('LOCALID_NURSE', 'OBJ_EVENT_GFX_NURSE', 7, 2, 'DOWN', f'{d["map"]}_Nurse')]
        if d.get('kind') == 'mart':
            objs = [npc('LOCALID_CLERK', 'OBJ_EVENT_GFX_JOHTO_CLERK', 1, 3, 'RIGHT', f'{d["map"]}_Clerk')]
        made.append((d['map'], interior_json(d['map'], d['layout'], d['music'], exits, objs), scripts(d['map'], d.get('kind'))))
        if d.get('kind') == 'center':
            up = [{'x': UPSTAIRS['stairs'][0], 'y': UPSTAIRS['stairs'][1], 'elevation': 4, 'dest_map': 'MAP_' + snake(d['map']), 'dest_warp_id': '2'}]
            made.append((UPSTAIRS['map'], interior_json(UPSTAIRS['map'], UPSTAIRS['layout'], 'MUS_POKE_CENTER', up), scripts(UPSTAIRS['map'], None)))
    violet['warp_events'] = warps
    vj.write_text(json.dumps(violet, indent=2) + '\n')
    groups = json.loads((engine / 'data/maps/map_groups.json').read_text())
    grp = next(g for g in groups['group_order'] if 'VioletCity' in groups[g])
    es = (engine / 'data/event_scripts.s').read_text()
    for name, mj, sc in made:
        d = engine / 'data/maps' / name
        d.mkdir(exist_ok=True)
        (d / 'map.json').write_text(json.dumps(mj, indent=2) + '\n')
        (d / 'scripts.inc').write_text(sc)
        if name not in groups[grp]:
            groups[grp].append(name)
        inc = f'.include "data/maps/{name}/scripts.inc"'
        if inc not in es:
            es = es.replace('.include "data/maps/VioletWestGate/scripts.inc"\n',
                            '.include "data/maps/VioletWestGate/scripts.inc"\n\n' + inc + '\n', 1) if name == made[0][0] else \
                 es.replace(f'.include "data/maps/{prev}/scripts.inc"\n', f'.include "data/maps/{prev}/scripts.inc"\n\n' + inc + '\n', 1)
        prev = name
    (engine / 'data/maps/map_groups.json').write_text(json.dumps(groups, indent=2) + '\n')
    (engine / 'data/event_scripts.s').write_text(es)
    return [n for n, _, _ in made]
