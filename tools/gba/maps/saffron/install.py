"""Install Saffron City ten years on, HGSS's plan (v2), over the first FireRed-based install.

    python3 tools/gba/maps/saffron/install.py ENGINE_CHECKOUT

Reads pack.py's and interiors.py's output. KantoSaffronCity becomes a 64x64 map (HGSS's
Saffron, cell for cell) on its own Emerald-format pair, the same symbols as before:
gTileset_KantoSaffronPrimary (derived from CherrygrovePrimary, pack.py) and
gTileset_KantoSaffronCity. Its map id, its Center, Center upstairs and Mart are kept (their
warps back still name the city's warps 0 and 1). New beside them in gMapGroup_Kanto:

    KantoSaffronDojo       the Dojo's one hall, two exit mats (interiors.py), on
                           gTileset_Building + gTileset_KantoSaffronDojo
    KantoSaffronSilphLab   Silph's research lab, open and empty, on
                           gTileset_Building + gTileset_KantoSaffronSilphLab

The city's warps: the Center (14, 50), the Mart (38, 26), the Fighting Dojo door (41, 12)
and the Psychic Dojo door (48, 12) into the one hall, the lab wing's door (37-38, 41).
FireRed's sliding door entry for v1's door metatile is removed (the new primary's metatile
of that number is not a door; the C06 Center and the shared Mart play no door animation,
as in Olivine). Signs: HGSS's six, ten years on (the Gym's is the Psychic Dojo's). No
connections: Routes 5-8 are not built. Refuses to run once the Dojo map exists, so it never
replays over owner edits.
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
W, H = 64, 64
NAME, GROUP = 'KantoSaffronCity', 'gMapGroup_Kanto'
PFOLDER, PSYM = 'kanto_saffron', 'KantoSaffronPrimary'
FOLDER, SYM = 'kanto_saffron_city', 'KantoSaffronCity'
MAPSEC = 'MAPSEC_SAFFRON_CITY'
BORDER_TREE = (60, 19)                          # a tree's top-left cell deep in the east forest: the border is forest
# name: (layout size from interiors.py, secondary folder and symbol, music)
ROOMS = {'KantoSaffronDojo': ('dojo', 'kanto_saffron_dojo', 'KantoSaffronDojo', 'MUS_RG_PEWTER'),
         'KantoSaffronSilphLab': ('lab', 'kanto_saffron_silph_lab', 'KantoSaffronSilphLab', 'MUS_RG_SILPH')}
# The city's warps, in order (the Center's and the Mart's interiors name 0 and 1).
WARPS = [((14, 50), 'MAP_KANTO_SAFFRON_POKEMON_CENTER', '0'), ((38, 26), 'MAP_KANTO_SAFFRON_MART', '0'),
         ((41, 12), 'MAP_KANTO_SAFFRON_DOJO', '0'), ((48, 12), 'MAP_KANTO_SAFFRON_DOJO', '3'),
         ((37, 41), 'MAP_KANTO_SAFFRON_SILPH_LAB', '0'), ((38, 41), 'MAP_KANTO_SAFFRON_SILPH_LAB', '0')]
# Each room's exit mats, the arrow cell first (where the player arrives), back to the city's warp.
ROOM_WARPS = {'KantoSaffronDojo': [((6, 14), '2'), ((5, 14), '2'), ((7, 14), '2'), ((17, 14), '3'), ((16, 14), '3'), ((18, 14), '3')],
              'KantoSaffronSilphLab': [((7, 9), '4')]}
# HGSS's signs (zone 056_T11, msg_0529_T11), ten years on.
SIGNS = [
    ('StationSign', (12, 18), 'SAFFRON CITY STATION\\nKANTO-JOHTO MAGNET TRAIN LINE'),
    ('CitySign', (23, 18), 'SAFFRON CITY\\nShining Big City'),
    ('FightingDojoSign', (43, 16), 'FIGHTING DOJO\\nEveryone is welcome!'),
    ('PsychicDojoSign', (50, 16), 'PSYCHIC DOJO\\nEveryone is welcome!'),
    ('SilphCoSign', (26, 42), 'SILPH CO. OFFICE BUILDING'),
    ('MrPsychicSign', (41, 50), "MR. PSYCHIC'S HOUSE\\nDon't call me Uncle Psychic!"),
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

def remove_v1_door(g):
    p = g / 'src/field_door.c'; s = p.read_text()
    a, b = '// Kanto Saffron doors: FireRed\'s sliding door, on the Center and the Mart\n', '// End Kanto Saffron doors\n'
    assert a in s and b in s, 'v1 door block not found'
    s = s[:s.index(a)] + s[s.index(b) + len(b):]
    s, n = re.subn(r'    \{\.metatileNum=\d+, \.tileset=&gTileset_KantoSaffronPrimary,[^\n]*\n', '', s)
    assert n == 1, ('v1 door entries', n)
    p.write_text(s)

def city(g):
    z = np.load(SRC / 'pack.npz')
    grid, pal, coll, elev = z['grid'], z['palettes'], z['collision'], z['elevation']
    pd = g / f'data/tilesets/primary/{PFOLDER}'
    tiles_png(pd / 'tiles.png', z['prim_tiles'])
    palettes(pd, pal)
    metatiles(pd, z['prim_meta'])
    d = g / f'data/tilesets/secondary/{FOLDER}'
    tiles_png(d / 'tiles.png', z['sec_tiles'])
    palettes(d, pal, pd)
    metatiles(d, z['sec_meta'])
    ld = g / f'data/layouts/{NAME}'
    cells = grid.astype(np.uint32) | (coll.astype(np.uint32) << 10) | (elev.astype(np.uint32) << 12)
    (ld / 'map.bin').write_bytes(cells.astype('<u2').tobytes())
    bx, by = BORDER_TREE
    border = [int(cells[by + (i >> 1), bx + (i & 1)]) for i in range(4)]
    (ld / 'border.bin').write_bytes(struct.pack('<4H', *border))
    layouts = read(g / 'data/layouts/layouts.json')
    lay = next(l for l in layouts['layouts'] if l.get('id') == layout_id(NAME))
    lay.update(width=W, height=H)
    write(g / 'data/layouts/layouts.json', layouts)

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
    return border

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
        register_secondary(g, sym, folder, {'dojo': "the Dojo's one hall (FireRed's Fighting Dojo and Sabrina's Gym)",
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
    if any((g / 'data/maps' / n).exists() for n in ROOMS):
        raise SystemExit('Saffron v2 is installed: edit native source; never replay over owner edits.')
    assert (g / f'data/maps/{NAME}/map.json').exists(), 'v1 Saffron not installed'
    remove_v1_door(g)
    border = city(g)
    room_report, ids = rooms(g)
    report = read(EV / 'pack.json')
    write(EV / 'capacity.json', dict(map=NAME, group=GROUP, size=[W, H], primary=f'gTileset_{PSYM}', secondary=f'gTileset_{SYM}',
                                     saffron_tiles=report['saffron_tiles'], primary_slots_free=report['primary_slots_free'],
                                     secondary_tiles=report['secondary_tiles'], secondary_tile_limit=report['secondary_tile_limit'],
                                     new_metatiles=report['new_metatiles'], metatiles_in_primary=report['metatiles_in_primary'],
                                     metatiles_in_secondary=report['metatiles_in_secondary'], border=border,
                                     interiors=room_report, map_ids=ids))
    print('Installed Saffron v2:', ids)

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
