"""Install the element-built Olivine City as one native map, with its Center and Mart.

    python3 tools/gba/maps/olivine_elements/install_elements.py ENGINE_CHECKOUT [STYLE]   # STYLE C by default

Reads pack.py's output. Olivine is a single 64x64 map on its own tileset pair:
gTileset_OlivinePrimary (derived from CherrygrovePrimary: its sea animation, ground,
sea and tree colours kept where Olivine draws them; see pack.py) and gTileset_OlivineCity,
which carries the owner-locked C06 Center and the shared Johto Mart. First authoring only:
refuses to run if any Olivine map already exists, so it never replays over owner edits.
Existing map, layout and tileset ids are untouched; new maps are appended to
gMapGroup_Cherrygrove. Off the map is open sea (the border).
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/olivine-elements'
SRC, EV = ART / 'source', ART / 'evidence'
W, H = 64, 64
NAME, FOLDER, SYM = 'OlivineCity', 'olivine_city', 'OlivineCity'
PFOLDER, PSYM = 'olivine', 'OlivinePrimary'
BORDER = (40, 58)                   # an even cell of open sea, so the border keeps the sea's 32 px phase

def read(p): return json.loads(p.read_text())
def write(p, v): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(v, indent=2) + '\n')
def map_id(name): return 'MAP_' + ''.join('_' + c if c.isupper() and i else c for i, c in enumerate(name)).upper()
def layout_id(name): return map_id(name).replace('MAP_', 'LAYOUT_', 1)

SIGNS = [  # HGSS's readable signs (bg type 1), text from msg_0604_T26; the Gym sign stays out (no Gym), hidden items too
    ('CitySign', (23, 23), 'OLIVINE CITY\\nThe Port with Sea Breezes'),
    ('PierSign', (24, 42), 'OLIVINE PORT\\nFAST-SHIP PIER'),
    ('LighthouseSign', (46, 40), "OLIVINE'S LIGHTHOUSE\\pIt is also known as\\nthe GLITTER LIGHTHOUSE."),
]
DOORS = [((16, 33), 'MAP_OLIVINE_POKEMON_CENTER', '0'), ((29, 33), 'MAP_OLIVINE_MART', '0')]
INTERIORS = [('CherrygrovePokemonCenter', 'OlivinePokemonCenter'), ('CherrygroveCenterUpstairs', 'OlivineCenterUpstairs'),
             ('CherrygroveMart', 'OlivineMart')]

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

def main(g, style):
    if any((g / 'data/maps' / n).exists() for n in [NAME] + [b for _, b in INTERIORS]):
        raise SystemExit('Olivine maps exist: edit native source; never replay over owner edits.')
    z = np.load(SRC / 'elements' / f'pack-{style}.npz')
    grid, pal = z['grid'], z['palettes']
    coll, elev = z['collision'], z['elevation']
    cherry = g / 'data/tilesets/primary/cherrygrove'
    # Primary: 512 tiles, banks 0-5 (0, 1, 3 Cherrygrove's), 512 metatiles, the sea animation.
    pd = g / f'data/tilesets/primary/{PFOLDER}'
    (pd / 'palettes').mkdir(parents=True, exist_ok=True)
    tiles_png(pd / 'tiles.png', z['prim_tiles'])
    for bank in range(16):
        if bank in (0, 1, 3) or bank > 5:
            text = (cherry / f'palettes/{bank:02}.pal').read_text()
        else:
            text = jasc([tuple(int(v) for v in pal[bank][i]) for i in range(16)])
        (pd / 'palettes' / f'{bank:02}.pal').write_text(text)
    metatiles(pd, z['prim_meta'])
    # Secondary: its tiles, banks 6-12, its metatiles.
    d = g / f'data/tilesets/secondary/{FOLDER}'
    (d / 'palettes').mkdir(parents=True, exist_ok=True)
    tiles_png(d / 'tiles.png', z['sec_tiles'])
    for bank in range(16):
        if bank < 6:                                            # primary banks, for Porymap's display
            text = (pd / f'palettes/{bank:02}.pal').read_text()
        else:
            text = jasc([tuple(int(v) for v in pal[bank][i]) for i in range(16)])
        (d / 'palettes' / f'{bank:02}.pal').write_text(text)
    metatiles(d, z['sec_meta'])
    with (g / 'src/data/tilesets/graphics.h').open('a') as f:
        for sym, kind, folder, note in ((PSYM, 'primary', PFOLDER, 'derived from CherrygrovePrimary (its sea animation kept)'),
                                        (SYM, 'secondary', FOLDER, 'element-built')):
            f.write(f'\n// Olivine City: one native map; {kind} tileset, {note}.\n'
                    f'const u32 gTilesetTiles_{sym}[] = INCGFX_U32("data/tilesets/{kind}/{folder}/tiles.png", ".4bpp.fastSmol");\n'
                    f'const u16 gTilesetPalettes_{sym}[][16] = {{\n' +
                    ''.join(f'    INCGFX_U16("data/tilesets/{kind}/{folder}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n')
    with (g / 'src/data/tilesets/metatiles.h').open('a') as f:
        for sym, kind, folder in ((PSYM, 'primary', PFOLDER), (SYM, 'secondary', FOLDER)):
            f.write(f'\n// Olivine City\nconst u16 gMetatiles_{sym}[] = INCBIN_U16("data/tilesets/{kind}/{folder}/metatiles.bin");\n'
                    f'const u16 gMetatileAttributes_{sym}[] = INCBIN_U16("data/tilesets/{kind}/{folder}/metatile_attributes.bin");\n')
    with (g / 'src/data/tilesets/headers.h').open('a') as f:
        f.write(f'\n// Olivine City\nconst struct Tileset gTileset_{PSYM} = {{ .isCompressed = TRUE, .isSecondary = FALSE, '
                f'.tiles = gTilesetTiles_{PSYM}, .palettes = gTilesetPalettes_{PSYM}, .metatiles = gMetatiles_{PSYM}, '
                f'.metatileAttributes = gMetatileAttributes_{PSYM}, .callback = InitTilesetAnim_CherrygrovePrimary }};\n'
                f'const struct Tileset gTileset_{SYM} = {{ .isCompressed = TRUE, .isSecondary = TRUE, '
                f'.tiles = gTilesetTiles_{SYM}, .palettes = gTilesetPalettes_{SYM}, .metatiles = gMetatiles_{SYM}, '
                f'.metatileAttributes = gMetatileAttributes_{SYM}, .callback = NULL }};\n')
    ld = g / f'data/layouts/{NAME}'
    ld.mkdir(parents=True)
    cells = grid.astype(np.uint32) | (coll.astype(np.uint32) << 10) | (elev.astype(np.uint32) << 12)
    (ld / 'map.bin').write_bytes(cells.astype('<u2').tobytes())
    bx, by = BORDER
    border = [int(grid[by + (i >> 1), bx + (i & 1)]) for i in range(4)]
    (ld / 'border.bin').write_bytes(struct.pack('<4H', *border))
    layouts = read(g / 'data/layouts/layouts.json')
    layouts['layouts'].append(dict(id=layout_id(NAME), name=f'{NAME}_Layout', width=W, height=H,
                                   primary_tileset=f'gTileset_{PSYM}', secondary_tileset=f'gTileset_{SYM}',
                                   border_filepath=f'data/layouts/{NAME}/border.bin',
                                   blockdata_filepath=f'data/layouts/{NAME}/map.bin', layout_version='emerald'))
    write(g / 'data/layouts/layouts.json', layouts)

    m = dict(read(g / 'data/maps/CherrygroveCity/map.json'))
    m.update(id=map_id(NAME), name=NAME, layout=layout_id(NAME), music='MUS_SLATEPORT', region_map_section='MAPSEC_OLIVINE_CITY',
             weather='WEATHER_NONE', map_type='MAP_TYPE_CITY', allow_cycling=True, allow_running=True, show_map_name=True,
             connections=None, object_events=[], warp_events=[], coord_events=[], bg_events=[])
    for (x, y), dest, warp in DOORS:
        m['warp_events'].append(dict(x=x, y=y, elevation=0, dest_map=dest, dest_warp_id=warp))
    script = f'{NAME}_MapScripts::\n    .byte 0\n'
    for label, (x, y), text in SIGNS:
        m['bg_events'].append(dict(type='sign', x=x, y=y, elevation=0, player_facing_dir='BG_EVENT_PLAYER_FACING_ANY',
                                   script=f'{NAME}_{label}'))
        script += (f'\n{NAME}_{label}::\n    msgbox {NAME}_{label}_Text, MSGBOX_SIGN\n    end\n'
                   f'\n{NAME}_{label}_Text:\n    .string "{text}$"\n')
    for k in sorted(k for k in ('region', 'build_target') if k in m):  # Porymap's key order
        m[k] = m.pop(k)
    write(g / f'data/maps/{NAME}/map.json', m)
    (g / f'data/maps/{NAME}/scripts.inc').write_text(script)
    for old, new in INTERIORS:
        text = json.dumps(read(g / f'data/maps/{old}/map.json'))
        for a, b in (('CherrygrovePokemonCenter', 'OlivinePokemonCenter'), ('CherrygroveCenterUpstairs', 'OlivineCenterUpstairs'),
                     ('CherrygroveMart', 'OlivineMart'), ('MAP_CHERRYGROVE_POKEMON_CENTER', 'MAP_OLIVINE_POKEMON_CENTER'),
                     ('MAP_CHERRYGROVE_CENTER_UPSTAIRS', 'MAP_OLIVINE_CENTER_UPSTAIRS'), ('MAP_CHERRYGROVE_MART', 'MAP_OLIVINE_MART'),
                     ('MAP_CHERRYGROVE_CITY', map_id(NAME)), ('MAPSEC_CHERRYGROVE_CITY', 'MAPSEC_OLIVINE_CITY')):
            text = text.replace(a, b)
        im_ = json.loads(text)
        for w in im_['warp_events']:
            if w['dest_map'] == map_id(NAME):
                w['dest_warp_id'] = '0' if new == 'OlivinePokemonCenter' else '1'
        for k in sorted(k for k in ('region', 'build_target') if k in im_):
            im_[k] = im_.pop(k)
        write(g / f'data/maps/{new}/map.json', im_)
        s = (g / f'data/maps/{old}/scripts.inc').read_text().replace(old, new)
        (g / f'data/maps/{new}/scripts.inc').write_text(s)
    all_new = [NAME] + [b for _, b in INTERIORS]
    groups = read(g / 'data/maps/map_groups.json')
    groups['gMapGroup_Cherrygrove'].extend(all_new)
    write(g / 'data/maps/map_groups.json', groups)
    with (g / 'data/event_scripts.s').open('a') as f:
        for n in all_new:
            f.write(f'\n.include "data/maps/{n}/scripts.inc"\n')
    p = g / 'src/data/region_map/region_map_sections.json'; r = read(p)
    sec_ = dict(r['map_sections'][-1]); sec_.update(id='MAPSEC_OLIVINE_CITY', name='OLIVINE CITY'); r['map_sections'].append(sec_); write(p, r)
    p = g / 'include/regions.h'; s = p.read_text()
    s = s.replace('    case MAPSEC_CHERRYGROVE_CITY:', '    case MAPSEC_OLIVINE_CITY: return REGION_JOHTO;\n    case MAPSEC_CHERRYGROVE_CITY:', 1); p.write_text(s)
    p = g / 'src/apocrypha_map_proof.c'; s = p.read_text()
    anchor = 'MAP_CIANWOOD_CENTER_UPSTAIRS};'
    assert anchor in s
    s = s.replace(anchor, 'MAP_CIANWOOD_CENTER_UPSTAIRS, ' + ', '.join(map_id(n) for n in all_new) + '};'); p.write_text(s)
    ids = {n: groups['gMapGroup_Cherrygrove'].index(n) for n in all_new}
    report = json.loads((EV / 'elements' / f'pack-{style}.json').read_text())
    write(EV / 'capacity.json', dict(map=NAME, primary=f'gTileset_{PSYM}', secondary=f'gTileset_{SYM}', style=style,
                                     olivine_tiles=report['olivine_tiles'], primary_slots=report['primary_slots_free'],
                                     secondary_tiles=report['secondary_tiles'], secondary_tile_limit=report['secondary_tile_limit'],
                                     new_metatiles=report['new_metatiles'], metatile_limit=1024 - report['cherrygrove_metatiles_kept'],
                                     map_ids=ids))
    print('Installed Olivine:', ids)

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), sys.argv[2] if len(sys.argv) > 2 else 'C')
