#!/usr/bin/env python3
"""Install Canalave City into an engine checkout (the `apocrypha` map source).

    python3 tools/gba/maps/canalave_city/install.py CACHE ENGINE [--fold K]

CACHE holds the reference render (cn_reference.py makes it from pret/pokeplatinum; set PLAT the first time).
Writes the two tilesets, the layout, CanalaveCity and its ten interior maps, and registers them. Running it
again replaces its own output only. Read gba/art/canalave-city/README.md.
"""
from __future__ import annotations
import json, re, sys, textwrap
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cn_compose as C
import cn_pack as P
import cn_cleanup as CL
from cn_reference import W, H, MARGIN

GROUP = 'gMapGroup_Cherrygrove'
MAPSEC = 'MAPSEC_CANALAVE_CITY'
CITY = 'MAP_CANALAVE_CITY'
def N(x, z):                              # Platinum cell -> native cell
    return x + MARGIN, z + MARGIN

# door: Platinum warp cell, interior map, its layout, its exit cells, music
DOORS = [
    ('CanalaveGym',                (7, 27),  'LAYOUT_RUSTBORO_CITY_GYM',            [(5, 19), (6, 19)], 'MUS_GYM'),
    ('CanalavePokemonCenter',      (26, 18), 'LAYOUT_SINNOH_POKEMON_CENTER_1F',     [(8, 10), (9, 10)], 'MUS_POKE_CENTER'),
    ('CanalaveMart',               (21, 36), 'LAYOUT_MART',                         [(3, 7), (4, 7)],   'MUS_POKE_MART'),
    ('CanalaveLibrary',            (5, 14),  'LAYOUT_RUSTBORO_CITY_POKEMON_SCHOOL', [(5, 10), (6, 10)], 'MUS_LILYCOVE_MUSEUM'),
    ('CanalaveSoutheastHouse',     (22, 44), 'LAYOUT_HOUSE1',                       [(3, 8), (4, 8)],   'MUS_LILYCOVE'),
    ('CanalaveSailorEldritchHouse', (7, 44), 'LAYOUT_HOUSE2',                       [(3, 7), (4, 7)],   'MUS_LILYCOVE'),
    ('CanalaveEastHouse',          (21, 28), 'LAYOUT_HOUSE3',                       [(3, 7), (4, 7)],   'MUS_LILYCOVE'),
    ('CanalaveWestHouse',          (6, 36),  'LAYOUT_HOUSE4',                       [(3, 8), (4, 8)],   'MUS_LILYCOVE'),
]
UPSTAIRS = 'CanalaveCenterUpstairs'
SHUT_DOOR = (26, 9)                       # Harbor Inn: shut in Platinum until its event
GATE = [(31, 50), (31, 51)]               # Route 218's gatehouse door, east of these cells
MUSIC = 'MUS_LILYCOVE'

def snake(n):
    return re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', n).upper()

def wrap(text, width=36):
    """Platinum message (\\n line, \\r new box, \\f scroll) -> Gen 3 string, re-wrapped to the GBA box."""
    text = ''.join(text) if isinstance(text, list) else text
    text = text.replace('’', "'").replace('“', '"').replace('”', '"').replace('Pokémon', 'POKéMON')
    pages = [p for p in re.split(r'\r', text) if p.strip()]
    out = []
    for p in pages:
        words = p.replace('\f', ' ').replace('\n', ' ').split()
        lines = textwrap.wrap(' '.join(words), width)
        s = lines[0]
        for i, l in enumerate(lines[1:]):
            s += ('\\n' if i == 0 else '\\l') + l
        out.append(s)
    return '\\p'.join(out) + '$'

# Platinum's residents in their default state (no story flags), on Platinum's cells
NPCS = [  # id, gfx, Platinum cell, movement, range, message id
    ('Collector', 'OBJ_EVENT_GFX_MANIAC', (26, 45), 'MOVEMENT_TYPE_WANDER_AROUND', (1, 1), 'CanalaveCity_Text_YourClothesLookDamp'),
    ('Lass', 'OBJ_EVENT_GFX_LASS', (20, 13), 'MOVEMENT_TYPE_FACE_DOWN', (0, 0), 'CanalaveCity_Text_PsyduckIsVeryClose'),
    ('Breeder', 'OBJ_EVENT_GFX_MAN_4', (27, 24), 'MOVEMENT_TYPE_WANDER_AROUND', (1, 1), 'CanalaveCity_Text_WelcomeToCanalCity'),
    ('Student', 'OBJ_EVENT_GFX_WOMAN_5', (1, 26), 'MOVEMENT_TYPE_WANDER_UP_AND_DOWN', (0, 1), 'CanalaveCity_Text_GoingToStudy'),
    ('OldMan', 'OBJ_EVENT_GFX_OLD_MAN', (9, 31), 'MOVEMENT_TYPE_WANDER_LEFT_AND_RIGHT', (1, 0), 'CanalaveCity_Text_WorkOutAtIronIsland'),
    ('SailorEldritch', 'OBJ_EVENT_GFX_SAILOR', (13, 46), 'MOVEMENT_TYPE_FACE_LEFT', (0, 0), 'CanalaveCity_Text_TellWheneverSetSail'),
]
PSYDUCK = (20, 14)
SIGN_TEXT = {
    'CanalaveCity_Sign_Library': 'CanalaveCity_Text_SignCanalaveLibrary',
    'CanalaveCity_Sign_Gym': 'CanalaveCity_Text_SignPokemonGym',
    'CanalaveCity_Sign_Dock': 'CanalaveCity_Text_SignCanalaveDock',
    'CanalaveCity_Sign_City': 'CanalaveCity_Text_MapSign',
    'CanalaveCity_Sign_EldritchHouse': 'CanalaveCity_Text_SignSailorEldritchsHouse',
    'CanalaveCity_Sign_HarborInn': 'CanalaveCity_Text_SignHarborInnFaded',
}

def base_map(name, layout, music, kind='MAP_TYPE_INDOOR'):
    return {
        'id': 'MAP_' + snake(name), 'name': name, 'layout': layout, 'music': music,
        'region_map_section': MAPSEC, 'requires_flash': False, 'weather': 'WEATHER_SUNNY' if kind != 'MAP_TYPE_INDOOR' else 'WEATHER_NONE',
        'map_type': kind, 'allow_cycling': kind != 'MAP_TYPE_INDOOR', 'allow_escaping': False, 'allow_running': True,
        'show_map_name': kind != 'MAP_TYPE_INDOOR', 'battle_scene': 'MAP_BATTLE_SCENE_NORMAL', 'connections': None,
        'object_events': [], 'warp_events': [], 'coord_events': [], 'bg_events': [], 'build_target': 'emerald', 'region': 'REGION_SINNOH'}

def npc(local, gfx, xy, move, rng, script):
    return {'local_id': local, 'graphics_id': gfx, 'x': xy[0], 'y': xy[1], 'elevation': 3, 'movement_type': move,
            'movement_range_x': rng[0], 'movement_range_y': rng[1], 'trainer_type': 'TRAINER_TYPE_NONE',
            'trainer_sight_or_berry_tree_id': '0', 'script': script, 'flag': '0'}

def warp(xy, dest, wid, elev=0):
    return {'x': xy[0], 'y': xy[1], 'elevation': elev, 'dest_map': dest, 'dest_warp_id': str(wid)}

def write_map(engine, mj, scripts):
    d = engine / 'data/maps' / mj['name']; d.mkdir(parents=True, exist_ok=True)
    (d / 'map.json').write_text(json.dumps(mj, indent=2) + '\n')
    (d / 'scripts.inc').write_text(scripts)

def city(engine, town, text):
    mj = base_map('CanalaveCity', 'LAYOUT_CANALAVE_CITY', MUSIC, 'MAP_TYPE_CITY')
    for name, cell, *_ in DOORS:
        mj['warp_events'].append(warp(N(*cell), 'MAP_' + snake(name), 0))
    s = ['CanalaveCity_MapScripts::', '\t.byte 0', '']
    for nid, gfx, cell, move, rng, msg in NPCS:
        mj['object_events'].append(npc(f'LOCALID_CANALAVE_{snake(nid)}', gfx, N(*cell), move, rng, f'CanalaveCity_{nid}'))
        s += [f'CanalaveCity_{nid}::', f'\tmsgbox CanalaveCity_Text_{nid}, MSGBOX_NPC', '\tend', '',
              f'CanalaveCity_Text_{nid}:', f'\t.string "{wrap(text[msg])}"', '']
    mj['object_events'].append(npc('LOCALID_CANALAVE_PSYDUCK', 'OBJ_EVENT_GFX_SPECIES(PSYDUCK)', N(*PSYDUCK), 'MOVEMENT_TYPE_FACE_DOWN', (0, 0), 'CanalaveCity_Psyduck'))
    s += ['CanalaveCity_Psyduck::', '\tlock', '\tfaceplayer', '\twaitse', '\tplaymoncry SPECIES_PSYDUCK, CRY_MODE_NORMAL',
          '\tmsgbox CanalaveCity_Text_Psyduck, MSGBOX_DEFAULT', '\twaitmoncry', '\trelease', '\tend', '',
          'CanalaveCity_Text_Psyduck:', f'\t.string "{wrap(text["CanalaveCity_Text_PsyduckCryGua"])}"', '']
    def sign(cell, script):
        return {'type': 'sign', 'x': cell[0], 'y': cell[1], 'elevation': 0, 'player_facing_dir': 'BG_EVENT_PLAYER_FACING_ANY', 'script': script}
    for cell, (_, script) in CL.SIGNS.items():
        mj['bg_events'].append(sign(N(*cell), script))
        s += [f'{script}::', f'\tmsgbox {script}_Text, MSGBOX_SIGN', '\tend', '', f'{script}_Text:', f'\t.string "{wrap(text[SIGN_TEXT[script]])}"', '']
    d = dict(sign(N(*SHUT_DOOR), 'CanalaveCity_HarborInnDoor'), player_facing_dir='BG_EVENT_PLAYER_FACING_NORTH')
    mj['bg_events'].append(d)
    s += ['CanalaveCity_HarborInnDoor::', '\tmsgbox CanalaveCity_HarborInnDoor_Text, MSGBOX_SIGN', '\tend', '',
          'CanalaveCity_HarborInnDoor_Text:', f'\t.string "{wrap(text["CanalaveCity_Text_DoorIsTightlyShut"])}"', '']
    for gx, gz in GATE:
        x, y = N(gx, gz)
        mj['bg_events'].append(dict(sign((x + 1, y), 'CanalaveCity_Gate'), player_facing_dir='BG_EVENT_PLAYER_FACING_EAST'))
    s += ['CanalaveCity_Gate::', '\tmsgbox CanalaveCity_Gate_Text, MSGBOX_SIGN', '\tend', '',
          'CanalaveCity_Gate_Text:', '\t.string "ROUTE 218 GATE\\nThe gate is closed for now.$"', '']
    write_map(engine, mj, '\n'.join(s))

def interiors(engine):
    for i, (name, cell, layout, exits, music) in enumerate(DOORS):
        mj = base_map(name, layout, music)
        elev = 3 if 'SINNOH' in layout else 0
        mj['warp_events'] = [warp(e, CITY, i, elev) for e in exits]
        s = [f'{name}_MapScripts::', '\t.byte 0', '']
        if name == 'CanalavePokemonCenter':
            mj['warp_events'].append(warp((1, 8), 'MAP_' + snake(UPSTAIRS), 0, 3))
            mj['object_events'].append(npc('LOCALID_NURSE', 'OBJ_EVENT_GFX_NURSE', (8, 2), 'MOVEMENT_TYPE_FACE_DOWN', (0, 0), f'{name}_Nurse'))
            s += [f'{name}_Nurse::', '\tsetvar VAR_0x800B, LOCALID_NURSE', '\tcall Common_EventScript_PkmnCenterNurse',
                  '\twaitmessage', '\twaitbuttonpress', '\trelease', '\tend', '']
        if name == 'CanalaveMart':
            mj['object_events'].append(npc('LOCALID_CANALAVE_CLERK', 'OBJ_EVENT_GFX_MART_EMPLOYEE', (1, 3), 'MOVEMENT_TYPE_FACE_RIGHT', (0, 0), f'{name}_Clerk'))
            s += [f'{name}_Clerk::', '\tlock', '\tfaceplayer', '\tmessage gText_HowMayIServeYou', '\twaitmessage',
                  f'\tpokemart {name}_Stock', '\tmsgbox gText_PleaseComeAgain, MSGBOX_DEFAULT', '\trelease', '\tend', '',
                  '\t.align 2', f'{name}_Stock:'] + [f'\t.2byte ITEM_{it}' for it in
                  ('POKE_BALL', 'GREAT_BALL', 'POTION', 'SUPER_POTION', 'ANTIDOTE', 'PARALYZE_HEAL', 'AWAKENING', 'ESCAPE_ROPE', 'REPEL')] + ['\tpokemartlistend', '']
        write_map(engine, mj, '\n'.join(s))
    mj = base_map(UPSTAIRS, 'LAYOUT_SINNOH_POKEMON_CENTER_2F', 'MUS_POKE_CENTER')
    mj['warp_events'] = [warp((1, 8), 'MAP_CANALAVE_POKEMON_CENTER', 2, 3)]
    write_map(engine, mj, f'{UPSTAIRS}_MapScripts::\n\t.byte 0\n')

# ------------------------------------------------------------------ engine registration (idempotent)
def insert_once(path, marker, block, before=None):
    s = path.read_text()
    if marker in s:
        a = s.index(marker); b = s.index(marker.replace('Begin', 'End'), a) + len(marker.replace('Begin', 'End')) + 1
        s = s[:a] + s[b:]
    block = f'{marker}\n{block.rstrip()}\n{marker.replace("Begin", "End")}\n'
    if before and before in s:
        i = s.index(before); s = s[:i] + block + s[i:]
    else:
        s = s.rstrip('\n') + '\n' + block
    path.write_text(s)

def register(engine):
    M = '// Begin Canalave City'
    pals = lambda d: ''.join(f'INCGFX_U16("data/tilesets/{d}/canalave_city/palettes/{i:02d}.pal", ".gbapal"),\n' for i in range(16))
    insert_once(engine / 'src/data/tilesets/graphics.h', M, f'''const u32 gTilesetTiles_CanalaveCityPrimary[] = INCGFX_U32("data/tilesets/primary/canalave_city/tiles.png", ".4bpp.fastSmol");
const u16 gTilesetPalettes_CanalaveCityPrimary[][16] = {{
{pals('primary')}}};
const u32 gTilesetTiles_CanalaveCity[] = INCGFX_U32("data/tilesets/secondary/canalave_city/tiles.png", ".4bpp.fastSmol");
const u16 gTilesetPalettes_CanalaveCity[][16] = {{
{pals('secondary')}}};''')
    insert_once(engine / 'src/data/tilesets/metatiles.h', M, '''const u16 gMetatiles_CanalaveCityPrimary[] = INCBIN_U16("data/tilesets/primary/canalave_city/metatiles.bin");
const u16 gMetatileAttributes_CanalaveCityPrimary[] = INCBIN_U16("data/tilesets/primary/canalave_city/metatile_attributes.bin");
const u16 gMetatiles_CanalaveCity[] = INCBIN_U16("data/tilesets/secondary/canalave_city/metatiles.bin");
const u16 gMetatileAttributes_CanalaveCity[] = INCBIN_U16("data/tilesets/secondary/canalave_city/metatile_attributes.bin");''')
    insert_once(engine / 'src/data/tilesets/headers.h', M, '''const struct Tileset gTileset_CanalaveCityPrimary = { .isCompressed = TRUE, .isSecondary = FALSE, .tiles = gTilesetTiles_CanalaveCityPrimary, .palettes = gTilesetPalettes_CanalaveCityPrimary, .metatiles = gMetatiles_CanalaveCityPrimary, .metatileAttributes = gMetatileAttributes_CanalaveCityPrimary, .callback = InitTilesetAnim_CanalaveCityPrimary };
const struct Tileset gTileset_CanalaveCity = { .isCompressed = TRUE, .isSecondary = TRUE, .tiles = gTilesetTiles_CanalaveCity, .palettes = gTilesetPalettes_CanalaveCity, .metatiles = gMetatiles_CanalaveCity, .metatileAttributes = gMetatileAttributes_CanalaveCity, .callback = NULL };''')
    insert_once(engine / 'src/tileset_anims.c', M, f'''// Emerald's deep-water pair (General water strip tiles {P.DEEP_SRC}-{P.DEEP_SRC + 1}) animated at primary tiles {P.DEEP[0]}-{P.DEEP[1]}.
static void TilesetAnim_CanalaveCityPrimary(u16 timer);
void InitTilesetAnim_CanalaveCityPrimary(void)
{{
    sPrimaryTilesetAnimCounter = 0;
    sPrimaryTilesetAnimCounterMax = 256;
    sPrimaryTilesetAnimCallback = TilesetAnim_CanalaveCityPrimary;
}}
static void TilesetAnim_CanalaveCityPrimary(u16 timer)
{{
    if (timer % 16 == 1)
        AppendTilesetAnimToBuffer(gTilesetAnims_General_Water[(timer / 16) % 8] + {P.DEEP_SRC} * TILE_SIZE_4BPP / 2, (u16 *)(BG_VRAM + TILE_OFFSET_4BPP({P.DEEP[0]})), 2 * TILE_SIZE_4BPP);
}}''', before='void InitTilesetAnim_General(void)')
    h = engine / 'include/tileset_anims.h'; s = h.read_text()
    if 'InitTilesetAnim_CanalaveCityPrimary' not in s:
        h.write_text(s.replace('void InitTilesetAnim_CherrygrovePrimary(void);', 'void InitTilesetAnim_CherrygrovePrimary(void);\nvoid InitTilesetAnim_CanalaveCityPrimary(void);'))
    # layout
    p = engine / 'data/layouts/layouts.json'; L = json.loads(p.read_text())
    L['layouts'] = [l for l in L['layouts'] if not (l and l.get('id') == 'LAYOUT_CANALAVE_CITY')]
    L['layouts'].append({'id': 'LAYOUT_CANALAVE_CITY', 'name': 'CanalaveCity_Layout', 'width': W, 'height': H,
                         'primary_tileset': 'gTileset_CanalaveCityPrimary', 'secondary_tileset': 'gTileset_CanalaveCity',
                         'border_filepath': 'data/layouts/CanalaveCity/border.bin', 'blockdata_filepath': 'data/layouts/CanalaveCity/map.bin',
                         'build_target': 'emerald', 'layout_version': 'emerald'})
    p.write_text(json.dumps(L, indent=2) + '\n')
    # map group (append only)
    p = engine / 'data/maps/map_groups.json'; G = json.loads(p.read_text())
    names = ['CanalaveCity'] + [d[0] for d in DOORS] + [UPSTAIRS]
    for n in names:
        if n not in G[GROUP]: G[GROUP].append(n)
    p.write_text(json.dumps(G, indent=2) + '\n')
    # map section
    p = engine / 'src/data/region_map/region_map_sections.json'; R = json.loads(p.read_text())
    key = next(k for k, v in R.items() if isinstance(v, list))
    if not any(e.get('id') == MAPSEC for e in R[key]):
        i = next(i for i, e in enumerate(R[key]) if e.get('id') == 'MAPSEC_SANDGEM_TOWN')
        R[key].insert(i + 1, {'id': MAPSEC, 'name': 'CANALAVE CITY', 'x': 1, 'y': 1, 'width': 1, 'height': 1})
        p.write_text(json.dumps(R, indent=2) + '\n')
    p = engine / 'include/regions.h'; s = p.read_text()
    if MAPSEC not in s:
        p.write_text(s.replace('    case MAPSEC_SANDGEM_TOWN: return REGION_SINNOH;', f'    case MAPSEC_SANDGEM_TOWN: return REGION_SINNOH;\n    case {MAPSEC}: return REGION_SINNOH;'))
    # scripts
    p = engine / 'data/event_scripts.s'; s = p.read_text()
    anchor = '.include "data/maps/SandgemCenterUpstairs/scripts.inc"\n'
    for n in names:
        line = f'.include "data/maps/{n}/scripts.inc"\n'
        if line not in s:
            s = s.replace(anchor, anchor + line); anchor = line
        else:
            anchor = line
    p.write_text(s)
    # test entry points
    p = engine / 'src/apocrypha_map_proof.c'; s = p.read_text()
    m = re.search(r'const u16 sMapProofMaps\[\] = \{(.*?)\};', s)
    ids = [x.strip() for x in m.group(1).split(',')]
    for n in names:
        if 'MAP_' + snake(n) not in ids: ids.append('MAP_' + snake(n))
    p.write_text(s[:m.start(1)] + ', '.join(ids) + s[m.end(1):])
    return {('MAP_' + snake(n)): ids.index('MAP_' + snake(n)) for n in names}

def main():
    cache, engine = Path(sys.argv[1]), Path(sys.argv[2])
    fold = int(sys.argv[sys.argv.index('--fold') + 1]) if '--fold' in sys.argv else 0
    town = C.build(cache, engine)
    for name, cell, *_ in DOORS:                       # Gen 3 doors are cells the player steps into
        x, r = N(*cell)
        town.coll[r, x] = False; town.elev[r, x] = 3; town.layer[r, x] = C.LAYER_COVERED
        town.behaviour[r, x] = C.MB_NON_ANIMATED_DOOR
    x, r = N(*SHUT_DOOR); town.behaviour[r, x] = C.MB_NORMAL
    pk = P.pack(town, engine, fold=fold)
    border = [int(pk.words[H - 2 + (i >> 1), (i & 1)]) for i in range(4)]
    P.write(engine, pk, border)
    text = {m['id']: m['en_US'] for m in town.d['text']}
    city(engine, town, text); interiors(engine)
    proof = register(engine)
    out = dict(tiles_free=pk.free, metatiles=len(pk.metas), colour_tiles=pk.ncolour_tiles, folds=len(pk.folds),
               proof_index=proof, notes=town.notes, plat_rev=town.d['plat_rev'])
    print(json.dumps(out, indent=1))
    return town, pk

if __name__ == '__main__':
    main()
