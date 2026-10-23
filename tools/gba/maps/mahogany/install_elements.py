"""Install the element-built Mahogany Town as one native map, with its Pokemon Center.

    python3 tools/gba/maps/mahogany/install_elements.py ENGINE_CHECKOUT [STYLE]   # STYLE C by default

Reads pack.py's output. Mahogany is a single 32x32 map on gTileset_CherrygrovePrimary
(the accepted Johto primary: ground, trees, signs) and its own secondary,
gTileset_MahoganyTown, which carries the owner-locked C06 Center. First authoring only:
refuses to run if any Mahogany map already exists, so it never replays over owner edits.
Existing map, layout and tileset ids are untouched; new maps are appended to
gMapGroup_Cherrygrove. Off the map is the mountain's rock top (the border); Routes 42, 43
and 44 are not built, so the town has no connections.
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/mahogany-town'
SRC, EV = ART / 'source', ART / 'evidence'
W = H = 32
NAME, FOLDER, SYM = 'MahoganyTown', 'mahogany_town', 'MahoganyTown'
PRIMARY = 'gTileset_CherrygrovePrimary'
BORDER = (0, 0)                     # the mountain's plain rock top, north-west corner

def read(p): return json.loads(p.read_text())
def write(p, v): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(v, indent=2) + '\n')
def map_id(name): return 'MAP_' + ''.join('_' + c if c.isupper() and i else c for i, c in enumerate(name)).upper()
def layout_id(name): return map_id(name).replace('MAP_', 'LAYOUT_', 1)

SIGNS = [  # HGSS bg events with text (msg_0620_T28). The Gym sign leaves out the leader, whom the design
           # bible does not name yet; the souvenir shop's sign (its text belongs to a story beat) stays a prop.
    ('TownSign', (4, 12), 'MAHOGANY TOWN\\nHome of the Ninja'),
    ('GymSign', (8, 24), 'MAHOGANY TOWN POKéMON GYM'),
]
DOORS = [((22, 23), 'MAP_MAHOGANY_POKEMON_CENTER', '0')]
INTERIORS = [('CherrygrovePokemonCenter', 'MahoganyPokemonCenter'), ('CherrygroveCenterUpstairs', 'MahoganyCenterUpstairs')]

def jasc(colors):
    return 'JASC-PAL\n0100\n16\n' + '\n'.join(' '.join(map(str, c)) for c in colors) + '\n'

def main(g, style):
    if any((g / 'data/maps' / n).exists() for n in [NAME] + [b for _, b in INTERIORS]):
        raise SystemExit('Mahogany maps exist: edit native source; never replay over owner edits.')
    z = np.load(SRC / 'elements' / f'pack-{style}.npz')
    grid, pats, pal, sec = z['grid'], z['patterns'], z['palettes'], z['sec_meta']
    coll, elev = z['collision'], z['elevation']
    d = g / f'data/tilesets/secondary/{FOLDER}'
    (d / 'palettes').mkdir(parents=True, exist_ok=True)
    rows = max(1, (len(pats) + 15) // 16)
    buf = np.zeros((rows * 8, 128), np.uint8)
    for i, t in enumerate(pats):
        buf[(i // 16) * 8:(i // 16) * 8 + 8, (i % 16) * 8:(i % 16) * 8 + 8] = t
    im = Image.fromarray(buf, 'P'); im.putpalette([v for i in range(16) for v in (i * 17,) * 3] + [0] * 720)
    im.save(d / 'tiles.png', bits=4)
    for bank in range(16):
        if bank < 6:                                            # primary banks, for Porymap's display
            text = (g / f'data/tilesets/primary/cherrygrove/palettes/{bank:02}.pal').read_text()
        else:
            text = jasc([tuple(int(v) for v in pal[bank][i]) for i in range(16)])
        (d / 'palettes' / f'{bank:02}.pal').write_text(text)
    (d / 'metatiles.bin').write_bytes(b''.join(struct.pack('<8H', *[int(v) for v in r[:8]]) for r in sec))
    (d / 'metatile_attributes.bin').write_bytes(struct.pack('<%dH' % len(sec), *[int(r[8]) for r in sec]))
    with (g / 'src/data/tilesets/graphics.h').open('a') as f:
        f.write(f'\n// Mahogany Town: one native map; primary {PRIMARY}, element-built secondary.\n'
                f'const u32 gTilesetTiles_{SYM}[] = INCGFX_U32("data/tilesets/secondary/{FOLDER}/tiles.png", ".4bpp.fastSmol");\n'
                f'const u16 gTilesetPalettes_{SYM}[][16] = {{\n' +
                ''.join(f'    INCGFX_U16("data/tilesets/secondary/{FOLDER}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n')
    with (g / 'src/data/tilesets/metatiles.h').open('a') as f:
        f.write(f'\n// Mahogany Town\nconst u16 gMetatiles_{SYM}[] = INCBIN_U16("data/tilesets/secondary/{FOLDER}/metatiles.bin");\n'
                f'const u16 gMetatileAttributes_{SYM}[] = INCBIN_U16("data/tilesets/secondary/{FOLDER}/metatile_attributes.bin");\n')
    with (g / 'src/data/tilesets/headers.h').open('a') as f:
        f.write(f'\n// Mahogany Town\nconst struct Tileset gTileset_{SYM} = {{ .isCompressed = TRUE, .isSecondary = TRUE, '
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
                                   primary_tileset=PRIMARY, secondary_tileset=f'gTileset_{SYM}',
                                   border_filepath=f'data/layouts/{NAME}/border.bin',
                                   blockdata_filepath=f'data/layouts/{NAME}/map.bin', layout_version='emerald'))
    write(g / 'data/layouts/layouts.json', layouts)

    m = dict(read(g / 'data/maps/CherrygroveCity/map.json'))
    m.update(id=map_id(NAME), name=NAME, layout=layout_id(NAME), music='MUS_LAVARIDGE', region_map_section='MAPSEC_MAHOGANY_TOWN',
             weather='WEATHER_NONE', map_type='MAP_TYPE_TOWN', allow_cycling=True, allow_running=True, show_map_name=True,
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
        for a, b in (('CherrygrovePokemonCenter', 'MahoganyPokemonCenter'), ('CherrygroveCenterUpstairs', 'MahoganyCenterUpstairs'),
                     ('MAP_CHERRYGROVE_POKEMON_CENTER', 'MAP_MAHOGANY_POKEMON_CENTER'),
                     ('MAP_CHERRYGROVE_CENTER_UPSTAIRS', 'MAP_MAHOGANY_CENTER_UPSTAIRS'),
                     ('MAP_CHERRYGROVE_CITY', map_id(NAME)), ('MAPSEC_CHERRYGROVE_CITY', 'MAPSEC_MAHOGANY_TOWN')):
            text = text.replace(a, b)
        im_ = json.loads(text)
        for w in im_['warp_events']:
            if w['dest_map'] == map_id(NAME):
                w['dest_warp_id'] = '0'
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
    sec_ = dict(r['map_sections'][-1]); sec_.update(id='MAPSEC_MAHOGANY_TOWN', name='MAHOGANY TOWN'); r['map_sections'].append(sec_); write(p, r)
    p = g / 'include/regions.h'; s = p.read_text()
    s = s.replace('    case MAPSEC_CHERRYGROVE_CITY:', '    case MAPSEC_MAHOGANY_TOWN: return REGION_JOHTO;\n    case MAPSEC_CHERRYGROVE_CITY:', 1); p.write_text(s)
    p = g / 'src/apocrypha_map_proof.c'; s = p.read_text()
    anchor = 'MAP_CHERRYGROVE_REGIONAL_PREVIEW_30};'
    assert anchor in s
    s = s.replace(anchor, 'MAP_CHERRYGROVE_REGIONAL_PREVIEW_30, ' + ', '.join(map_id(n) for n in all_new) + '};'); p.write_text(s)
    ids = {n: groups['gMapGroup_Cherrygrove'].index(n) for n in all_new}
    report = json.loads((EV / 'elements' / f'pack-{style}.json').read_text())
    write(EV / 'capacity.json', dict(map=NAME, primary=PRIMARY, secondary=f'gTileset_{SYM}', style=style,
                                     secondary_tiles=report['secondary_tiles'], secondary_tile_limit=report['secondary_tile_limit'],
                                     secondary_metatiles=report['secondary_metatiles'], metatile_limit=512, map_ids=ids))
    print('Installed Mahogany:', ids)

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), sys.argv[2] if len(sys.argv) > 2 else 'C')
