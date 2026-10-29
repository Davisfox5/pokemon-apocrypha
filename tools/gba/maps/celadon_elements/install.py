"""Install Celadon City: one native map, its Center and its rooms.

    python3 tools/gba/maps/celadon_elements/install.py ENGINE_CHECKOUT

Reads pack.py's and interiors.py's output. KantoCeladonCity is the 60x50 map (HGSS's Celadon
as Gen 3 elements, compose.py) on its own tileset pair: gTileset_KantoCeladonPrimary (512
tiles, 512 metatiles) and gTileset_KantoCeladonCity (the rest). It joins gMapGroup_Kanto
beside Saffron; FireRed's own Celadon maps stay as they are. New with it:

    KantoCeladonPokemonCenter, KantoCeladonCenterUpstairs   cloned from Cherrygrove's
    KantoCeladonMarketServices   the market's services (HGSS's Dept Store; FireRed's 1F)
    KantoCeladonHotelLobby, KantoCeladonHotelUpstairs   the Pokemon Hotel (HGSS's
                                 Condominiums; FireRed's Condominiums 1F and 2F)
    KantoCeladonGameCorner, KantoCeladonPrizeRoom
    KantoCeladonGardens          the Botanical Gardens (HGSS's Gym; FireRed's Celadon Gym)
    KantoCeladonCafe             the cafe (HGSS's restaurant; FireRed's Restaurant)

each room on gTileset_Building and a secondary of its own (interiors.py). Signs stand where
HGSS's do (the city sign a cell east, clear of a market stall), their text ten years on. No
connections: Routes 7 and 16 are not built. Off the map is the forest (border: a 2x2 block of
it). First authoring only: refuses to run if the city map exists, so it never replays over
owner edits.
"""
from __future__ import annotations
import json, re, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image

import common as C
import pack as P
import interiors as I

W, H, SRC, EV = C.W, C.H, C.SRC, C.EV
NAME, GROUP = 'KantoCeladonCity', 'gMapGroup_Kanto'
PFOLDER, PSYM = 'kanto_celadon', 'KantoCeladonPrimary'
FOLDER, SYM = 'kanto_celadon_city', 'KantoCeladonCity'
MAPSEC, MUSIC = 'MAPSEC_CELADON_CITY', 'MUS_RG_CELADON'
BORDER = (4, 44)                    # an even cell inside the west forest: one tree block, the forest's 2x2 repeat
CENTER = [('CherrygrovePokemonCenter', 'KantoCeladonPokemonCenter'), ('CherrygroveCenterUpstairs', 'KantoCeladonCenterUpstairs')]
ROOMS = {'services': ('KantoCeladonMarketServices', MUSIC), 'hotel_1f': ('KantoCeladonHotelLobby', MUSIC),
         'hotel_2f': ('KantoCeladonHotelUpstairs', MUSIC), 'game_corner': ('KantoCeladonGameCorner', 'MUS_RG_GAME_CORNER'),
         'prize_room': ('KantoCeladonPrizeRoom', 'MUS_RG_GAME_CORNER'), 'gardens': ('KantoCeladonGardens', MUSIC),
         'cafe': ('KantoCeladonCafe', MUSIC)}
NOTES = {'services': "the market's services (FireRed's Dept Store 1F)", 'game_corner': "the Game Corner (FireRed's)",
         'prize_room': "the Game Corner's prize room (FireRed's)", 'gardens': "the Botanical Gardens (FireRed's Celadon Gym)",
         'cafe': "the cafe (FireRed's Restaurant)", 'hotel_1f': "the Pokemon Hotel's lobby (FireRed's Condominiums 1F)",
         'hotel_2f': "the Pokemon Hotel's upper floor (FireRed's Condominiums 2F)"}
# The city's warps, in order: (pack.DOORS name, destination room ('center' for the Center))
WARPS = [('pokemon_center', 'center'), ('services', 'services'), ('hotel', 'hotel_1f'), ('gamecorner', 'game_corner'),
         ('prize', 'prize_room'), ('gardens', 'gardens'), ('cafe', 'cafe')]
SIGNS = [
    ('CitySign', (22, 21), 'CELADON CITY\\nThe City of Rainbow Colors.\\pRebuilt by its people.'),
    ('ServicesSign', (19, 14), 'CELADON MARKET SERVICES\\pSALON, MOVE TUTOR and\\nEV TRAINING inside.'),
    ('HotelSign', (36, 13), 'POKéMON HOTEL\\nRooms for travelers from every region.'),
    ('GameCornerSign', (35, 28), 'CELADON GAME CORNER\\nA fun place for everyone!'),
    ('TrainerTipsGuardSpec', (45, 28), 'TRAINER TIPS\\pGUARD SPEC. protects POKéMON\\nfrom status-reduction moves during\\l'
                                       'battle.\\pFind it at the CELADON MARKET!'),
    ('GardensSign', (20, 44), 'CELADON BOTANICAL GARDENS\\nOpen to everyone. Mind the BELLOSSOM.'),
    ('CafeSign', (44, 38), 'CELADON CAFé\\nFresh from the market every morning.'),
]

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
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, bits=4)

def metatiles(d, rows):
    (d / 'metatiles.bin').write_bytes(b''.join(struct.pack('<8H', *[int(v) for v in r[:8]]) for r in rows))
    (d / 'metatile_attributes.bin').write_bytes(struct.pack('<%dH' % len(rows), *[int(r[8]) for r in rows]))

def palettes(d, pal, primary_dir=None):
    (d / 'palettes').mkdir(parents=True, exist_ok=True)
    for b in range(16):
        if primary_dir is not None and b < 6:                  # a secondary shows its primary's banks in Porymap
            text = (primary_dir / f'palettes/{b:02}.pal').read_text()
        else:
            text = jasc([tuple(int(v) for v in pal[b][i]) for i in range(16)])
        (d / 'palettes' / f'{b:02}.pal').write_text(text)

def porymap_order(m):
    for k in sorted(k for k in ('region', 'build_target') if k in m):
        m[k] = m.pop(k)
    return m

def register(g, sym, kind, folder, note):
    sec = 'TRUE' if kind == 'secondary' else 'FALSE'
    for path, text in (
            ('src/data/tilesets/graphics.h',
             f'\n// Kanto Celadon: {note}; {kind} tileset.\n'
             f'const u32 gTilesetTiles_{sym}[] = INCGFX_U32("data/tilesets/{kind}/{folder}/tiles.png", ".4bpp.fastSmol");\n'
             f'const u16 gTilesetPalettes_{sym}[][16] = {{\n' +
             ''.join(f'    INCGFX_U16("data/tilesets/{kind}/{folder}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n'),
            ('src/data/tilesets/metatiles.h',
             f'\n// Kanto Celadon: {note}\nconst u16 gMetatiles_{sym}[] = INCBIN_U16("data/tilesets/{kind}/{folder}/metatiles.bin");\n'
             f'const u16 gMetatileAttributes_{sym}[] = INCBIN_U16("data/tilesets/{kind}/{folder}/metatile_attributes.bin");\n'),
            ('src/data/tilesets/headers.h',
             f'\n// Kanto Celadon: {note}\nconst struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, .isSecondary = {sec}, '
             f'.tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym}, .metatiles = gMetatiles_{sym}, '
             f'.metatileAttributes = gMetatileAttributes_{sym}, .callback = NULL }};\n')):
        p = g / path
        s = p.read_text()
        assert f'_{sym}[]' not in s and f'gTileset_{sym} ' not in s, (path, sym)
        p.write_text(s + text)

def city_warp_index(door):
    return next(i for i, (k, _) in enumerate(WARPS) if k == door)

ROOM_DOOR = {'services': 'services', 'hotel_1f': 'hotel', 'game_corner': 'gamecorner', 'prize_room': 'prize',
             'gardens': 'gardens', 'cafe': 'cafe'}

def arrival(room):
    """The warp a city door lands on in its room: of the warps back to that door, the one on
    the exit mat (the cell interiors.py kept a warp behaviour on)."""
    beh = np.load(SRC / f'interiors/{room}.npz')['behaviour']
    ws = [(i, xy) for i, (xy, to) in enumerate(I.ROOMS[room][2].items()) if to.startswith('city:')]
    return next(i for i, (x, y) in ws if beh[y, x])

def city(g, layouts):
    z = np.load(SRC / 'elements/pack.npz')
    grid, pal, meta = z['grid'], z['palettes'], z['metatiles']
    coll, elev = z['collision'], z['elevation']
    prim_meta = [list(r) for r in meta[:512]] + [[0] * 9] * max(0, 512 - len(meta))
    sec_meta = [list(r) for r in meta[512:]]
    pd = g / f'data/tilesets/primary/{PFOLDER}'
    tiles_png(pd / 'tiles.png', z['prim_tiles'])
    palettes(pd, pal)
    metatiles(pd, prim_meta)
    d = g / f'data/tilesets/secondary/{FOLDER}'
    tiles_png(d / 'tiles.png', z['sec_tiles'])
    palettes(d, pal, pd)
    metatiles(d, sec_meta)
    register(g, PSYM, 'primary', PFOLDER, "HGSS's Celadon as Gen 3 elements, its ground, trees and the first buildings")
    register(g, SYM, 'secondary', FOLDER, "the rest of its buildings, the Center and the market")
    ld = g / f'data/layouts/{NAME}'
    ld.mkdir(parents=True)
    cells = grid.astype(np.uint32) | (coll.astype(np.uint32) << 10) | (elev.astype(np.uint32) << 12)
    (ld / 'map.bin').write_bytes(cells.astype('<u2').tobytes())
    bx, by = BORDER
    (ld / 'border.bin').write_bytes(struct.pack('<4H', *[int(grid[by + (i >> 1), bx + (i & 1)]) for i in range(4)]))
    layouts['layouts'].append(dict(id=layout_id(NAME), name=f'{NAME}_Layout', width=W, height=H,
                                   primary_tileset=f'gTileset_{PSYM}', secondary_tileset=f'gTileset_{SYM}',
                                   border_filepath=f'data/layouts/{NAME}/border.bin',
                                   blockdata_filepath=f'data/layouts/{NAME}/map.bin', layout_version='emerald'))
    m = dict(read(g / 'data/maps/CherrygroveCity/map.json'))
    m.update(id=map_id(NAME), name=NAME, layout=layout_id(NAME), music=MUSIC, region_map_section=MAPSEC,
             weather='WEATHER_NONE', map_type='MAP_TYPE_CITY', allow_cycling=True, allow_running=True, show_map_name=True,
             connections=None, object_events=[], warp_events=[], coord_events=[], bg_events=[],
             build_target='emerald', region='REGION_KANTO')
    doors = {v: k for k, v in P.DOORS.items()}
    for key, room in WARPS:
        x, y = doors[key]
        if room == 'center':
            dest, warp = map_id(CENTER[0][1]), '0'
        else:
            dest, warp = map_id(ROOMS[room][0]), str(arrival(room))
        m['warp_events'].append(dict(x=x, y=y, elevation=0, dest_map=dest, dest_warp_id=warp))
    script = f'{NAME}_MapScripts::\n    .byte 0\n'
    for label, (x, y), text in SIGNS:
        m['bg_events'].append(dict(type='sign', x=x, y=y, elevation=0, player_facing_dir='BG_EVENT_PLAYER_FACING_ANY',
                                   script=f'{NAME}_{label}'))
        script += (f'\n{NAME}_{label}::\n    msgbox {NAME}_{label}_Text, MSGBOX_SIGN\n    end\n'
                   f'\n{NAME}_{label}_Text:\n    .string "{text}$"\n')
    write(g / f'data/maps/{NAME}/map.json', porymap_order(m))
    (g / f'data/maps/{NAME}/scripts.inc').write_text(script)

def center(g):
    renames = [('CherrygrovePokemonCenter', 'KantoCeladonPokemonCenter'), ('CherrygroveCenterUpstairs', 'KantoCeladonCenterUpstairs'),
               ('MAP_CHERRYGROVE_POKEMON_CENTER', 'MAP_KANTO_CELADON_POKEMON_CENTER'),
               ('MAP_CHERRYGROVE_CENTER_UPSTAIRS', 'MAP_KANTO_CELADON_CENTER_UPSTAIRS'),
               ('MAP_CHERRYGROVE_CITY', map_id(NAME)), ('MAPSEC_CHERRYGROVE_CITY', MAPSEC)]
    for old, new in CENTER:
        text = json.dumps(read(g / f'data/maps/{old}/map.json'))
        for a, b in renames:
            text = text.replace(a, b)
        m = json.loads(text)
        m['region'] = 'REGION_KANTO'
        for w in m['warp_events']:
            if w['dest_map'] == map_id(NAME):
                w['dest_warp_id'] = str(city_warp_index('pokemon_center'))
        write(g / f'data/maps/{new}/map.json', porymap_order(m))
        (g / f'data/maps/{new}/scripts.inc').write_text((g / f'data/maps/{old}/scripts.inc').read_text().replace(old, new))

def rooms(g, layouts):
    template = read(g / 'data/maps/KantoSaffronMart/map.json')
    out = {}
    for key, (name, music) in ROOMS.items():
        z = np.load(SRC / f'interiors/{key}.npz')
        h, w = z['grid'].shape
        folder, sym = f'kanto_celadon_{key}', 'KantoCeladon' + ''.join(p.capitalize() for p in key.split('_'))
        d = g / f'data/tilesets/secondary/{folder}'
        tiles_png(d / 'tiles.png', z['tiles'])
        palettes(d, z['palettes'], g / 'data/tilesets/primary/building')
        metatiles(d, z['meta'])
        register(g, sym, 'secondary', folder, NOTES[key])
        ld = g / f'data/layouts/{name}'
        ld.mkdir(parents=True)
        (ld / 'map.bin').write_bytes(z['grid'].astype('<u2').tobytes())
        black = int(z['grid'][h - 1, 0])
        (ld / 'border.bin').write_bytes(struct.pack('<4H', *[black] * 4))
        layouts['layouts'].append(dict(id=layout_id(name), name=f'{name}_Layout', width=w, height=h,
                                       primary_tileset='gTileset_Building', secondary_tileset=f'gTileset_{sym}',
                                       border_filepath=f'data/layouts/{name}/border.bin',
                                       blockdata_filepath=f'data/layouts/{name}/map.bin', layout_version='emerald'))
        warps = []
        for (x, y), to in I.ROOMS[key][2].items():
            where, n = to.split(':')
            if where == 'city':
                dest, warp = map_id(NAME), str(city_warp_index(n))
            else:
                dest, warp = map_id(ROOMS[where][0]), n
            warps.append(dict(x=x, y=y, elevation=3, dest_map=dest, dest_warp_id=warp))
        m = {k: v for k, v in template.items()}
        m.update(id=map_id(name), name=name, layout=layout_id(name), music=music, region_map_section=MAPSEC,
                 object_events=[], coord_events=[], bg_events=[], warp_events=warps)
        m['region'] = 'REGION_KANTO'
        write(g / f'data/maps/{name}/map.json', porymap_order(m))
        (g / f'data/maps/{name}/scripts.inc').write_text(f'{name}_MapScripts::\n    .byte 0\n')
        out[name] = dict(size=[w, h], tiles=int(len(z['tiles'])), metatiles=int(len(z['meta'])), warps=len(warps))
    return out

def main(g):
    names = [NAME] + [b for _, b in CENTER] + [n for n, _ in ROOMS.values()]
    if any((g / 'data/maps' / n / 'map.json').exists() for n in names):
        raise SystemExit('Celadon is installed: edit native source; never replay over owner edits.')
    layouts = read(g / 'data/layouts/layouts.json')
    city(g, layouts)
    center(g)
    room_report = rooms(g, layouts)
    write(g / 'data/layouts/layouts.json', layouts)
    groups = read(g / 'data/maps/map_groups.json')
    assert GROUP in groups and not set(names) & set(groups[GROUP])
    groups[GROUP].extend(names)
    write(g / 'data/maps/map_groups.json', groups)
    with (g / 'data/event_scripts.s').open('a') as f:
        for n in names:
            f.write(f'\n.include "data/maps/{n}/scripts.inc"\n')
    p = g / 'src/apocrypha_map_proof.c'; s = p.read_text()
    anchor = re.search(r'(MAP_KANTO_SAFFRON_SILPH_LAB)\};', s)
    assert anchor, 'map proof list'
    p.write_text(s.replace(anchor.group(0), anchor.group(1) + ', ' + ', '.join(map_id(n) for n in names) + '};'))
    ids = {n: groups[GROUP].index(n) for n in names}
    report = read(EV / 'pack.json')
    write(EV / 'capacity.json', dict(map=NAME, group=GROUP, size=[W, H], primary=f'gTileset_{PSYM}', secondary=f'gTileset_{SYM}',
                                     tiles=report['tiles'], tile_limit=report['tile_limit'], primary_tiles=report['primary_tiles'],
                                     secondary_tiles=report['secondary_tiles'], metatiles=report['metatiles'],
                                     colours=report['colours'], interiors=room_report, map_ids=ids))
    print('Installed Celadon:', ids)

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
