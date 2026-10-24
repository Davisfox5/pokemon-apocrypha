"""Install Saffron City ten years on as one native map, with its Center and Mart.

    python3 tools/gba/maps/saffron/install.py ENGINE_CHECKOUT

Reads pack.py's output. KantoSaffronCity is a 66x55 map on its own Emerald-format pair:
gTileset_KantoSaffronPrimary (FireRed's kept tiles and metatiles, 512 each) and
gTileset_KantoSaffronCity (the station's and the Psychic Dojo plate's). It goes in a new
group, gMapGroup_Kanto, beside FireRed's own SaffronCity_Frlg, which stays as it is
(FireRed's maps are not in the Emerald build). The Center and the Mart open, on interiors
cloned from Cherrygrove's, and their doors play FireRed's sliding door. No connections:
Routes 5-8 are not built, so the four gates are solid. First authoring only: refuses to
run if any of its maps already exists, so it never replays over owner edits.
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/saffron-kanto'
SRC, EV = ART / 'source', ART / 'evidence'
W, H = 66, 55
NAME, GROUP = 'KantoSaffronCity', 'gMapGroup_Kanto'
PFOLDER, PSYM = 'kanto_saffron', 'KantoSaffronPrimary'
FOLDER, SYM = 'kanto_saffron_city', 'KantoSaffronCity'
MAPSEC = 'MAPSEC_SAFFRON_CITY'
DOORS = [((24, 38), 'MAP_KANTO_SAFFRON_POKEMON_CENTER', '0'), ((40, 21), 'MAP_KANTO_SAFFRON_MART', '0')]
INTERIORS = [('CherrygrovePokemonCenter', 'KantoSaffronPokemonCenter'),
             ('CherrygroveCenterUpstairs', 'KantoSaffronCenterUpstairs'),
             ('CherrygroveMart', 'KantoSaffronMart')]
# KANTO_ITEMS.md (Marts): the badge-1 tier, not FireRed's endgame Kanto stock
MART_STOCK = ['ITEM_POKE_BALL', 'ITEM_GREAT_BALL', 'ITEM_POTION', 'ITEM_SUPER_POTION', 'ITEM_ANTIDOTE',
              'ITEM_PARALYZE_HEAL', 'ITEM_BURN_HEAL', 'ITEM_AWAKENING', 'ITEM_REPEL', 'ITEM_SUPER_REPEL',
              'ITEM_ESCAPE_ROPE']
# FireRed's signs, ten years on (compose.py moves the city sign and turns the Gym signposts
# plain); the station's sign is on its door, solid until the station's interior exists.
SIGNS = [
    ('CitySign', (30, 12), 'SAFFRON CITY\\nShining, Golden Land of Commerce'),
    ('StationSign', (25, 14), 'SAFFRON STATION\\nMAGNET TRAIN to GOLDENROD CITY'),
    ('FightingDojoSign', (42, 14), 'FIGHTING DOJO\\nChallengers welcome.'),
    ('PsychicDojoSign', (50, 14), 'PSYCHIC DOJO\\nChallengers welcome.'),
    ('LeagueOfficeSign', (49, 22), 'POKéMON LEAGUE\\nKANTO OFFICE'),
    ('SilphCoSign', (29, 31), 'SILPH CO. HEADQUARTERS\\nThe lobby is open to visitors.'),
    ('SilphMagnetTrainSign', (13, 25), 'The MAGNET TRAIN runs on\\nSILPH CO. engineering.'),
    ('TrainerTipsGreatBall', (18, 30), 'TRAINER TIPS\\pThe GREAT BALL offers improved\\ncatching rates.\\p'
                                       'Try it on those hard-to-catch\\nPOKéMON.'),
    ('TrainerTipsFullHeal', (54, 25), 'TRAINER TIPS\\pFULL HEAL cures all ailments like\\nburns, paralysis, poisoning,\\l'
                                      'freezing, and sleep.\\pIt costs a bit more, but it\'s more\\n'
                                      'convenient than buying other items.'),
    ('MrPsychicSign', (40, 38), "MR. PSYCHIC'S HOUSE"),
]
DOOR_C = '''// Kanto Saffron doors: FireRed's sliding door, on the Center and the Mart
extern const struct Tileset gTileset_KantoSaffronPrimary;
static const u8 sKantoSaffronDoor_Sliding[] = INCGFX_U8("graphics/door_anims/sliding_single.png", ".4bpp");
static const u8 sKantoSaffronDoorPal_Sliding[] = {3, 3, 3, 3, 3, 3, 3, 3};
// End Kanto Saffron doors
'''

def read(p): return json.loads(p.read_text())
def write(p, v): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(v, indent=2, ensure_ascii=False) + '\n')
def map_id(name): return 'MAP_' + ''.join('_' + c if c.isupper() and i else c for i, c in enumerate(name)).upper()
def layout_id(name): return map_id(name).replace('MAP_', 'LAYOUT_', 1)

def jasc(colors):
    return 'JASC-PAL\n0100\n16\n' + '\n'.join(' '.join(map(str, c)) for c in colors) + '\n'

def tiles_png(path, tiles):
    rows = max(1, (len(tiles) + 15) // 16)
    buf = np.zeros((rows * 8, 128), np.uint8)
    for i, t in enumerate(tiles):
        buf[(i // 16) * 8:(i // 16) * 8 + 8, (i % 16) * 8:(i % 16) * 8 + 8] = t
    im = Image.fromarray(buf, 'P'); im.putpalette([v for i in range(16) for v in (i * 17,) * 3] + [0] * 720)
    im.save(path, bits=4)

def metatiles(d, rows):
    (d / 'metatiles.bin').write_bytes(b''.join(struct.pack('<8H', *[int(v) for v in r[:8]]) for r in rows))
    (d / 'metatile_attributes.bin').write_bytes(struct.pack('<%dH' % len(rows), *[int(r[8]) for r in rows]))

def porymap_order(m):
    for k in sorted(k for k in ('region', 'build_target') if k in m):
        m[k] = m.pop(k)
    return m

def main(g):
    all_new = [NAME] + [b for _, b in INTERIORS]
    if any((g / 'data/maps' / n).exists() for n in all_new):
        raise SystemExit('Saffron maps exist: edit native source; never replay over owner edits.')
    z = np.load(SRC / 'pack.npz')
    grid, pal = z['grid'], z['palettes']
    bank = lambda b: jasc([tuple(int(v) for v in pal[b][i]) for i in range(16)])
    # Primary: 512 tiles, banks 0-5 (FireRed's 0-3 and 5, the station's 4), 512 metatiles.
    pd = g / f'data/tilesets/primary/{PFOLDER}'
    (pd / 'palettes').mkdir(parents=True, exist_ok=True)
    tiles_png(pd / 'tiles.png', z['prim_tiles'])
    for b in range(16):
        (pd / 'palettes' / f'{b:02}.pal').write_text(bank(b))
    metatiles(pd, z['prim_meta'])
    # Secondary: the new tiles past 512, banks 6-12 (FireRed's 8-12, two spare), the art metatiles.
    d = g / f'data/tilesets/secondary/{FOLDER}'
    (d / 'palettes').mkdir(parents=True, exist_ok=True)
    tiles_png(d / 'tiles.png', z['sec_tiles'])
    for b in range(16):
        (d / 'palettes' / f'{b:02}.pal').write_text(bank(b))
    metatiles(d, z['sec_meta'])
    with (g / 'src/data/tilesets/graphics.h').open('a') as f:
        for sym, kind, folder, note in ((PSYM, 'primary', PFOLDER, "FireRed's Saffron, repacked"),
                                        (SYM, 'secondary', FOLDER, 'the station and the Psychic Dojo plate')):
            f.write(f'\n// Kanto Saffron City: one native map; {kind} tileset, {note}.\n'
                    f'const u32 gTilesetTiles_{sym}[] = INCGFX_U32("data/tilesets/{kind}/{folder}/tiles.png", ".4bpp.fastSmol");\n'
                    f'const u16 gTilesetPalettes_{sym}[][16] = {{\n' +
                    ''.join(f'    INCGFX_U16("data/tilesets/{kind}/{folder}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n')
    with (g / 'src/data/tilesets/metatiles.h').open('a') as f:
        for sym, kind, folder in ((PSYM, 'primary', PFOLDER), (SYM, 'secondary', FOLDER)):
            f.write(f'\n// Kanto Saffron City\nconst u16 gMetatiles_{sym}[] = INCBIN_U16("data/tilesets/{kind}/{folder}/metatiles.bin");\n'
                    f'const u16 gMetatileAttributes_{sym}[] = INCBIN_U16("data/tilesets/{kind}/{folder}/metatile_attributes.bin");\n')
    with (g / 'src/data/tilesets/headers.h').open('a') as f:
        f.write(f'\n// Kanto Saffron City\nconst struct Tileset gTileset_{PSYM} = {{ .isCompressed = TRUE, .isSecondary = FALSE, '
                f'.tiles = gTilesetTiles_{PSYM}, .palettes = gTilesetPalettes_{PSYM}, .metatiles = gMetatiles_{PSYM}, '
                f'.metatileAttributes = gMetatileAttributes_{PSYM}, .callback = NULL }};\n'
                f'const struct Tileset gTileset_{SYM} = {{ .isCompressed = TRUE, .isSecondary = TRUE, '
                f'.tiles = gTilesetTiles_{SYM}, .palettes = gTilesetPalettes_{SYM}, .metatiles = gMetatiles_{SYM}, '
                f'.metatileAttributes = gMetatileAttributes_{SYM}, .callback = NULL }};\n')
    # the Center and Mart doors: one metatile, FireRed's sliding door (its own bank 3)
    door_mids = {int(grid[y, x]) & 0x3FF for (x, y), _, _ in DOORS}
    assert len(door_mids) == 1 and min(door_mids) < 512, door_mids
    door_mid = door_mids.pop()
    p = g / 'src/field_door.c'; s = p.read_text()
    anchor = 'static const struct DoorGraphics sDoorAnimGraphicsTable[] =\n{\n'
    assert anchor in s and 'sKantoSaffronDoor_Sliding' not in s
    s = s.replace(anchor, DOOR_C + anchor + f'    {{.metatileNum={door_mid}, .tileset=&gTileset_{PSYM}, .sound=DOOR_SOUND_SLIDING, '
                  f'.size=DOOR_SIZE_1x1, .tiles=sKantoSaffronDoor_Sliding, .palettes=sKantoSaffronDoorPal_Sliding}},\n', 1)
    p.write_text(s)

    ld = g / f'data/layouts/{NAME}'
    ld.mkdir(parents=True)
    (ld / 'map.bin').write_bytes(grid.astype('<u2').tobytes())
    (ld / 'border.bin').write_bytes(struct.pack('<4H', *[int(v) for v in z['border']]))
    layouts = read(g / 'data/layouts/layouts.json')
    layouts['layouts'].append(dict(id=layout_id(NAME), name=f'{NAME}_Layout', width=W, height=H,
                                   primary_tileset=f'gTileset_{PSYM}', secondary_tileset=f'gTileset_{SYM}',
                                   border_filepath=f'data/layouts/{NAME}/border.bin',
                                   blockdata_filepath=f'data/layouts/{NAME}/map.bin', layout_version='emerald'))
    write(g / 'data/layouts/layouts.json', layouts)

    m = dict(read(g / 'data/maps/CherrygroveCity/map.json'))
    m.update(id=map_id(NAME), name=NAME, layout=layout_id(NAME), music='MUS_RG_PEWTER', region_map_section=MAPSEC,
             weather='WEATHER_NONE', map_type='MAP_TYPE_CITY', allow_cycling=True, allow_running=True, show_map_name=True,
             connections=None, object_events=[], warp_events=[], coord_events=[], bg_events=[],
             build_target='emerald', region='REGION_KANTO')
    for (x, y), dest, warp in DOORS:
        m['warp_events'].append(dict(x=x, y=y, elevation=0, dest_map=dest, dest_warp_id=warp))
    script = f'{NAME}_MapScripts::\n    .byte 0\n'
    for label, (x, y), text in SIGNS:
        m['bg_events'].append(dict(type='sign', x=x, y=y, elevation=0, player_facing_dir='BG_EVENT_PLAYER_FACING_ANY',
                                   script=f'{NAME}_{label}'))
        script += (f'\n{NAME}_{label}::\n    msgbox {NAME}_{label}_Text, MSGBOX_SIGN\n    end\n'
                   f'\n{NAME}_{label}_Text:\n    .string "{text}$"\n')
    write(g / f'data/maps/{NAME}/map.json', porymap_order(m))
    (g / f'data/maps/{NAME}/scripts.inc').write_text(script)
    renames = [('CherrygrovePokemonCenter', 'KantoSaffronPokemonCenter'), ('CherrygroveCenterUpstairs', 'KantoSaffronCenterUpstairs'),
               ('CherrygroveMart', 'KantoSaffronMart'), ('MAP_CHERRYGROVE_POKEMON_CENTER', 'MAP_KANTO_SAFFRON_POKEMON_CENTER'),
               ('MAP_CHERRYGROVE_CENTER_UPSTAIRS', 'MAP_KANTO_SAFFRON_CENTER_UPSTAIRS'), ('MAP_CHERRYGROVE_MART', 'MAP_KANTO_SAFFRON_MART'),
               ('MAP_CHERRYGROVE_CITY', map_id(NAME)), ('MAPSEC_CHERRYGROVE_CITY', MAPSEC)]
    for old, new in INTERIORS:
        text = json.dumps(read(g / f'data/maps/{old}/map.json'))
        for a, b in renames:
            text = text.replace(a, b)
        im_ = json.loads(text)
        im_['region'] = 'REGION_KANTO'
        for w in im_['warp_events']:
            if w['dest_map'] == map_id(NAME):
                w['dest_warp_id'] = '0' if new == 'KantoSaffronPokemonCenter' else '1'
        write(g / f'data/maps/{new}/map.json', porymap_order(im_))
        s = (g / f'data/maps/{old}/scripts.inc').read_text().replace(old, new)
        if new == 'KantoSaffronMart':
            head, sep, _ = s.partition(f'{new}_Stock:\n')
            assert sep, 'Mart stock label not found'
            s = head + sep + ''.join(f'    .2byte {i}\n' for i in MART_STOCK) + '    pokemartlistend\n'
        (g / f'data/maps/{new}/scripts.inc').write_text(s)
    groups = read(g / 'data/maps/map_groups.json')
    assert GROUP not in groups
    groups['group_order'].append(GROUP)
    groups[GROUP] = all_new
    write(g / 'data/maps/map_groups.json', groups)
    with (g / 'data/event_scripts.s').open('a') as f:
        for n in all_new:
            f.write(f'\n.include "data/maps/{n}/scripts.inc"\n')
    p = g / 'src/apocrypha_map_proof.c'; s = p.read_text()
    anchor = 'MAP_OLIVINE_MART};'
    assert anchor in s
    s = s.replace(anchor, 'MAP_OLIVINE_MART, ' + ', '.join(map_id(n) for n in all_new) + '};'); p.write_text(s)
    ids = {n: groups[GROUP].index(n) for n in all_new}
    report = read(EV / 'pack.json')
    write(EV / 'capacity.json', dict(map=NAME, group=GROUP, primary=f'gTileset_{PSYM}', secondary=f'gTileset_{SYM}',
                                     primary_tiles=report['primary_tiles'], secondary_tiles=report['secondary_tiles'],
                                     secondary_tile_limit=report['secondary_tile_limit'],
                                     primary_metatiles=report['metatiles_in_primary'], secondary_metatiles=report['metatiles_in_secondary'],
                                     door_metatile=door_mid, map_ids=ids))
    print('Installed Saffron:', ids, 'door metatile', door_mid)

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
