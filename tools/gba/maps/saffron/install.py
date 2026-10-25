"""Install Saffron City ten years on (v3) over the first FireRed-based install.

    python3 tools/gba/maps/saffron/install.py ENGINE_CHECKOUT

Reads pack.py's and interiors.py's output. KantoSaffronCity stays a 66x55 map (FireRed's
SaffronCity_Frlg, cell for cell, with the v3 parts and green spaces) on its own
Emerald-format pair, the same symbols as the first install: gTileset_KantoSaffronPrimary
(FireRed's unchanged cells, repacked) and gTileset_KantoSaffronCity (the art cells). Its map
id, its Center, Center upstairs and Mart are kept (their warps back still name the city's
warps 0 and 1). New beside them in gMapGroup_Kanto:

    KantoSaffronDojo       the Saffron Dojo's one hall, two exit mats (interiors.py), on
                           gTileset_Building + gTileset_KantoSaffronDojo
    KantoSaffronSilphLab   Silph's research lab, open and empty, on
                           gTileset_Building + gTileset_KantoSaffronSilphLab

The city's warps, in order: the Center (24, 38), the Mart (40, 21), the Fighting door
(40, 12) and the Psychic door (45, 12) into the one hall, the lab's door (42, 30). FireRed's
sliding door entry (the Center's and the Mart's shared door metatile) moves to that
metatile's new number; the Dojo's and the lab's doors play no door animation, as in
Olivine. Signs: the first install's, ten years on. No connections: Routes 5-8 are not
built. Refuses to run once the Dojo map exists, so it never replays over owner edits.
"""
from __future__ import annotations
import json, re, struct, sys
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
# name: (interiors.py room, secondary folder and symbol, music)
ROOMS = {'KantoSaffronDojo': ('dojo', 'kanto_saffron_dojo', 'KantoSaffronDojo', 'MUS_RG_PEWTER'),
         'KantoSaffronSilphLab': ('lab', 'kanto_saffron_silph_lab', 'KantoSaffronSilphLab', 'MUS_RG_SILPH')}
# The city's warps, in order (the Center's and the Mart's interiors name 0 and 1).
WARPS = [((24, 38), 'MAP_KANTO_SAFFRON_POKEMON_CENTER', '0'), ((40, 21), 'MAP_KANTO_SAFFRON_MART', '0'),
         ((40, 12), 'MAP_KANTO_SAFFRON_DOJO', '0'), ((45, 12), 'MAP_KANTO_SAFFRON_DOJO', '3'),
         ((42, 30), 'MAP_KANTO_SAFFRON_SILPH_LAB', '0')]
# Each room's exit mats, the arrow cell first (where the player arrives), back to the city's warp.
ROOM_WARPS = {'KantoSaffronDojo': [((6, 14), '2'), ((5, 14), '2'), ((7, 14), '2'), ((18, 14), '3'), ((17, 14), '3'), ((19, 14), '3')],
              'KantoSaffronSilphLab': [((7, 9), '4')]}
# FireRed's signs, ten years on (compose.py moves the city sign and turns the Gym signposts
# plain); the station's sign is on its door, solid until the station's interior exists.
SIGNS = [
    ('CitySign', (30, 12), 'SAFFRON CITY\\nShining, Golden Land of Commerce'),
    ('StationSign', (25, 14), 'SAFFRON STATION\\nMAGNET TRAIN to GOLDENROD CITY'),
    ('FightingDojoSign', (42, 14), 'SAFFRON DOJO - FIGHTING\\nChallengers welcome.'),
    ('PsychicDojoSign', (50, 14), 'SAFFRON DOJO - PSYCHIC\\nChallengers welcome.'),
    ('LeagueOfficeSign', (49, 22), 'POKéMON LEAGUE\\nKANTO OFFICE'),
    ('SilphCoSign', (29, 31), 'SILPH CO. HEADQUARTERS\\pThe lobby is open to visitors.\\n'
                              'RESEARCH LAB entrance to the east.'),
    ('SilphMagnetTrainSign', (13, 25), 'The MAGNET TRAIN runs on\\nSILPH CO. engineering.'),
    ('TrainerTipsGreatBall', (18, 30), 'TRAINER TIPS\\pThe GREAT BALL offers improved\\ncatching rates.\\p'
                                       'Try it on those hard-to-catch\\nPOKéMON.'),
    ('TrainerTipsFullHeal', (54, 25), 'TRAINER TIPS\\pFULL HEAL cures all ailments like\\nburns, paralysis, poisoning,\\l'
                                      'freezing, and sleep.\\pIt costs a bit more, but it\'s more\\n'
                                      'convenient than buying other items.'),
    ('MrPsychicSign', (40, 38), "MR. PSYCHIC'S HOUSE"),
]
DOOR_ENTRY = re.compile(r'(    \{\.metatileNum=)(\d+)(, \.tileset=&gTileset_KantoSaffronPrimary,)')

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

def register_secondary(g, sym, folder, note):
    for path, text in (
            ('src/data/tilesets/graphics.h',
             f'\n// Kanto Saffron: {note}; secondary tileset.\n'
             f'const u32 gTilesetTiles_{sym}[] = INCGFX_U32("data/tilesets/secondary/{folder}/tiles.png", ".4bpp.fastSmol");\n'
             f'const u16 gTilesetPalettes_{sym}[][16] = {{\n' +
             ''.join(f'    INCGFX_U16("data/tilesets/secondary/{folder}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n'),
            ('src/data/tilesets/metatiles.h',
             f'\n// Kanto Saffron: {note}\nconst u16 gMetatiles_{sym}[] = INCBIN_U16("data/tilesets/secondary/{folder}/metatiles.bin");\n'
             f'const u16 gMetatileAttributes_{sym}[] = INCBIN_U16("data/tilesets/secondary/{folder}/metatile_attributes.bin");\n'),
            ('src/data/tilesets/headers.h',
             f'\n// Kanto Saffron: {note}\nconst struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, .isSecondary = TRUE, '
             f'.tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym}, .metatiles = gMetatiles_{sym}, '
             f'.metatileAttributes = gMetatileAttributes_{sym}, .callback = NULL }};\n')):
        p = g / path
        s = p.read_text()
        assert f'_{sym}[]' not in s and f'gTileset_{sym} ' not in s, (path, sym)
        p.write_text(s + text)

DOOR_PNG = 'graphics/door_anims/kanto_saffron_sliding.png'

def move_door(g, grid, meta, pal):
    """The Center's and the Mart's door metatile (one FireRed cell, in the primary) keeps
    FireRed's sliding door under its new number. Its tiles' banks moved in the repack, so the
    door's frames (FireRed's sliding_single.png) are indexed again into those banks, tile by
    tile, every colour exact, and its palette list names them."""
    mids = {int(grid[y, x]) & 0x3FF for (x, y), _, _ in WARPS[:2]}
    assert len(mids) == 1 and min(mids) < 512, ('Center and Mart doors', mids)
    mid = mids.pop()
    banks = [int(e) >> 12 for e in meta[mid][:4]]
    src = Image.open(g / 'graphics/door_anims/sliding_single.png')
    ix, rgb = np.array(src), np.array(src.getpalette()[:48]).reshape(16, 3) >> 3
    out = np.zeros_like(ix)
    for f in range(ix.shape[0] // 16):
        for q, b in enumerate(banks):
            sl = np.s_[f * 16 + (q // 2) * 8:f * 16 + (q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            bank = [tuple(int(v) >> 3 for v in c) for c in pal[b]]
            for i in np.unique(ix[sl]):
                if i:
                    out[sl][ix[sl] == i] = bank.index(tuple(int(v) for v in rgb[i]), 1)
    im = Image.fromarray(out.astype(np.uint8), 'P'); im.putpalette([v for c in pal[banks[0]] for v in c] + [0] * 720)
    im.save(g / DOOR_PNG, bits=4)
    p = g / 'src/field_door.c'; s = p.read_text()
    s, n = DOOR_ENTRY.subn(lambda m: f'{m[1]}{mid}{m[3]}', s)
    assert n == 1, ('v1 door entries', n)
    old_png = 'INCGFX_U8("graphics/door_anims/sliding_single.png", ".4bpp");\nstatic const u8 sKantoSaffronDoorPal_Sliding[] = {3, 3, 3, 3, 3, 3, 3, 3};'
    assert old_png in s, 'v1 door frames not found'
    s = s.replace(old_png, f'INCGFX_U8("{DOOR_PNG}", ".4bpp");\nstatic const u8 sKantoSaffronDoorPal_Sliding[] = '
                           f'{{{", ".join(map(str, banks + banks))}}};')
    p.write_text(s)
    return mid

def city(g):
    z = np.load(SRC / 'pack.npz')
    grid, pal = z['grid'], z['palettes']
    pd = g / f'data/tilesets/primary/{PFOLDER}'
    tiles_png(pd / 'tiles.png', z['prim_tiles'])
    palettes(pd, pal)
    metatiles(pd, z['prim_meta'])
    d = g / f'data/tilesets/secondary/{FOLDER}'
    tiles_png(d / 'tiles.png', z['sec_tiles'])
    palettes(d, pal)
    metatiles(d, z['sec_meta'])
    p = g / 'src/data/tilesets/graphics.h'
    p.write_text(p.read_text().replace('secondary tileset, the station and the Psychic Dojo plate.',
                                       'secondary tileset, its new buildings, props and lawns.'))
    ld = g / f'data/layouts/{NAME}'
    (ld / 'map.bin').write_bytes(grid.astype('<u2').tobytes())
    (ld / 'border.bin').write_bytes(struct.pack('<4H', *[int(v) for v in np.asarray(z['border']).ravel()]))

    p = g / f'data/maps/{NAME}/map.json'
    m = read(p)
    m['warp_events'] = [dict(x=x, y=y, elevation=0, dest_map=dest, dest_warp_id=warp) for (x, y), dest, warp in WARPS]
    m['bg_events'] = []
    script = f'{NAME}_MapScripts::\n    .byte 0\n'
    for label, (x, y), text in SIGNS:
        m['bg_events'].append(dict(type='sign', x=x, y=y, elevation=0, player_facing_dir='BG_EVENT_PLAYER_FACING_ANY',
                                   script=f'{NAME}_{label}'))
        script += (f'\n{NAME}_{label}::\n    msgbox {NAME}_{label}_Text, MSGBOX_SIGN\n    end\n'
                   f'\n{NAME}_{label}_Text:\n    .string "{text}$"\n')
    write(p, porymap_order(m))
    (g / f'data/maps/{NAME}/scripts.inc').write_text(script)
    return move_door(g, grid, z['prim_meta'], pal)

def rooms(g):
    template = read(g / 'data/maps/KantoSaffronMart/map.json')
    layouts = read(g / 'data/layouts/layouts.json')
    out = {}
    for name, (key, folder, sym, music) in ROOMS.items():
        z = np.load(SRC / f'interiors/{key}.npz')
        h, w = z['grid'].shape
        d = g / f'data/tilesets/secondary/{folder}'
        d.mkdir(parents=True)
        tiles_png(d / 'tiles.png', z['tiles'])
        palettes(d, z['palettes'], g / 'data/tilesets/primary/building')
        metatiles(d, z['meta'])
        register_secondary(g, sym, folder, {'dojo': "the Saffron Dojo's one hall (FireRed's Fighting Dojo, built out, with Sabrina's Gym in its east end)",
                                            'lab': "Silph's research lab (FireRed's Cinnabar Lab experiment room)"}[key])
        ld = g / f'data/layouts/{name}'
        ld.mkdir(parents=True)
        (ld / 'map.bin').write_bytes(z['grid'].astype('<u2').tobytes())
        black = int(z['grid'][h - 1, 0])                        # the black edge under the bottom wall
        (ld / 'border.bin').write_bytes(struct.pack('<4H', *[black] * 4))
        layouts['layouts'].append(dict(id=layout_id(name), name=f'{name}_Layout', width=w, height=h,
                                       primary_tileset='gTileset_Building', secondary_tileset=f'gTileset_{sym}',
                                       border_filepath=f'data/layouts/{name}/border.bin',
                                       blockdata_filepath=f'data/layouts/{name}/map.bin', layout_version='emerald'))
        m = {k: v for k, v in template.items()}
        m.update(id=map_id(name), name=name, layout=layout_id(name), music=music, region_map_section=MAPSEC,
                 object_events=[], coord_events=[], bg_events=[],
                 warp_events=[dict(x=x, y=y, elevation=3, dest_map=map_id(NAME), dest_warp_id=warp) for (x, y), warp in ROOM_WARPS[name]])
        m['region'] = 'REGION_KANTO'
        write(g / f'data/maps/{name}/map.json', porymap_order(m))
        (g / f'data/maps/{name}/scripts.inc').write_text(f'{name}_MapScripts::\n    .byte 0\n')
        out[name] = dict(size=[w, h], tiles=int(len(z['tiles'])), metatiles=int(len(z['meta'])))
    write(g / 'data/layouts/layouts.json', layouts)
    groups = read(g / 'data/maps/map_groups.json')
    groups[GROUP].extend(ROOMS)
    write(g / 'data/maps/map_groups.json', groups)
    with (g / 'data/event_scripts.s').open('a') as f:
        for n in ROOMS:
            f.write(f'\n.include "data/maps/{n}/scripts.inc"\n')
    p = g / 'src/apocrypha_map_proof.c'; s = p.read_text()
    anchor = 'MAP_KANTO_SAFFRON_MART};'
    assert anchor in s
    p.write_text(s.replace(anchor, 'MAP_KANTO_SAFFRON_MART, ' + ', '.join(map_id(n) for n in ROOMS) + '};'))
    return out, {n: groups[GROUP].index(n) for n in groups[GROUP]}

def main(g):
    if any((g / 'data/maps' / n / 'map.json').exists() for n in ROOMS):
        raise SystemExit('Saffron v3 is installed: edit native source; never replay over owner edits.')
    assert (g / f'data/maps/{NAME}/map.json').exists(), 'the first Saffron install is not in this checkout'
    door = city(g)
    room_report, ids = rooms(g)
    report = read(EV / 'pack.json')
    write(EV / 'capacity.json', dict(map=NAME, group=GROUP, size=[W, H], primary=f'gTileset_{PSYM}', secondary=f'gTileset_{SYM}',
                                     primary_tiles=report['primary_tiles'], secondary_tiles=report['secondary_tiles'],
                                     secondary_tile_limit=report['secondary_tile_limit'],
                                     primary_metatiles=report['metatiles_in_primary'], secondary_metatiles=report['metatiles_in_secondary'],
                                     colours=report['colours'], door_metatile=door, interiors=room_report, map_ids=ids))
    print('Installed Saffron v3:', ids, 'door metatile', door)

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
