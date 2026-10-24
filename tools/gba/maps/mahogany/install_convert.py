"""Install the HGSS-converted Mahogany Town (convert.py) as one native map, with its Center.

    python3 tools/gba/maps/mahogany/install_convert.py ENGINE_CHECKOUT [PACK]

Reads a packed draft: PACK 'convert' (second draft, convert.py) or 'pack3' (third draft,
assemble.py + pack_lossless.py). Mahogany is a single 32x32 map on its own tileset pair:
gTileset_MahoganyPrimary (HGSS Mahogany's ground, cliffs, trees and walls, banks 0-5) and
gTileset_MahoganyTown (the rest of HGSS's art and the owner-locked C06 Center, banks 6-12).
It replaces the first draft (the Gen 3 element build) on the engine branch: that draft's
files are removed and the shared registration files are restored from the base branch
before installing, so nothing of it lingers. It refuses if any Mahogany file was last
changed by a commit that is not this tool's (an owner edit), so it never replays over owner
edits. Existing map, layout and tileset ids are untouched; new maps are appended to
gMapGroup_Cherrygrove. Off the map is the mountain's rock top (the border).
"""
from __future__ import annotations
import json, shutil, struct, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/mahogany-town'
SRC, EV = ART / 'source', ART / 'evidence'
W = H = 32
NAME, FOLDER, SYM = 'MahoganyTown', 'mahogany_town', 'MahoganyTown'
PFOLDER, PSYM = 'mahogany', 'MahoganyPrimary'
PRIMARY = f'gTileset_{PSYM}'
BASE = 'origin/apocrypha'
BORDER = (0, 0)                     # the mountain's plain rock top, north-west corner

def read(p): return json.loads(p.read_text())
def write(p, v): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(v, indent=2) + '\n')
def map_id(name): return 'MAP_' + ''.join('_' + c if c.isupper() and i else c for i, c in enumerate(name)).upper()
def layout_id(name): return map_id(name).replace('MAP_', 'LAYOUT_', 1)

SIGNS = [  # HGSS bg events with text (msg_0620_T28), on HGSS's own signposts. The Gym sign leaves out the leader,
           # whom the design bible does not name yet; the souvenir shop's sign (its text belongs to a story beat) stays a prop.
    ('TownSign', (4, 12), 'MAHOGANY TOWN\\nHome of the Ninja'),
    ('GymSign', (8, 24), 'MAHOGANY TOWN POKéMON GYM'),
]
DOORS = [((22, 23), 'MAP_MAHOGANY_POKEMON_CENTER', '0')]
INTERIORS = [('CherrygrovePokemonCenter', 'MahoganyPokemonCenter'), ('CherrygroveCenterUpstairs', 'MahoganyCenterUpstairs')]

def jasc(colors):
    return 'JASC-PAL\n0100\n16\n' + '\n'.join(' '.join(map(str, c)) for c in colors) + '\n'

DRAFT = [f'data/layouts/{NAME}', f'data/maps/{NAME}', 'data/maps/MahoganyPokemonCenter', 'data/maps/MahoganyCenterUpstairs',
         f'data/tilesets/secondary/{FOLDER}', f'data/tilesets/primary/{PFOLDER}']
SHARED_FILES = ['data/event_scripts.s', 'data/layouts/layouts.json', 'data/maps/map_groups.json', 'include/regions.h',
                'src/apocrypha_map_proof.c', 'src/data/region_map/region_map_sections.json', 'src/data/tilesets/graphics.h',
                'src/data/tilesets/headers.h', 'src/data/tilesets/metatiles.h']

def remove_draft(g):
    """Remove the agent's earlier Mahogany install. Refuses if a Mahogany file's history has a
    commit whose message is not one of this project's Mahogany generator commits."""
    log = subprocess.run(['git', '-C', str(g), 'log', '--format=%s', f'{BASE}..HEAD', '--'] + DRAFT,
                         capture_output=True, text=True, check=True).stdout.splitlines()
    foreign = [l for l in log if not l.startswith('Mahogany')]
    if foreign:
        raise SystemExit(f'Mahogany files carry other commits {foreign}: edit native source; never replay over owner edits.')
    for d in DRAFT:
        if (g / d).exists():
            shutil.rmtree(g / d)
    subprocess.run(['git', '-C', str(g), 'restore', f'--source={BASE}', '--worktree', '--'] + SHARED_FILES, check=True)

def write_tileset(d, pats, pal, metas, banks_shown):
    (d / 'palettes').mkdir(parents=True, exist_ok=True)
    rows = max(1, (len(pats) + 15) // 16)
    buf = np.zeros((rows * 8, 128), np.uint8)
    for i, t in enumerate(pats):
        buf[(i // 16) * 8:(i // 16) * 8 + 8, (i % 16) * 8:(i % 16) * 8 + 8] = t
    im = Image.fromarray(buf, 'P'); im.putpalette([v for i in range(16) for v in (i * 17,) * 3] + [0] * 720)
    im.save(d / 'tiles.png', bits=4)
    for bank in range(16):                                     # every bank written, for Porymap's display
        (d / 'palettes' / f'{bank:02}.pal').write_text(jasc([tuple(int(v) for v in pal[bank][i]) for i in range(16)]))
    (d / 'metatiles.bin').write_bytes(b''.join(struct.pack('<8H', *[int(v) for v in r[1:9]]) for r in metas))
    (d / 'metatile_attributes.bin').write_bytes(struct.pack('<%dH' % len(metas), *[int(r[9]) for r in metas]))

def register(g, sym, folder, kind, secondary):
    with (g / 'src/data/tilesets/graphics.h').open('a') as f:
        f.write(f'\n// Mahogany Town ({kind}).\n'
                f'const u32 gTilesetTiles_{sym}[] = INCGFX_U32("data/tilesets/{kind}/{folder}/tiles.png", ".4bpp.fastSmol");\n'
                f'const u16 gTilesetPalettes_{sym}[][16] = {{\n' +
                ''.join(f'    INCGFX_U16("data/tilesets/{kind}/{folder}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n')
    with (g / 'src/data/tilesets/metatiles.h').open('a') as f:
        f.write(f'\n// Mahogany Town ({kind})\nconst u16 gMetatiles_{sym}[] = INCBIN_U16("data/tilesets/{kind}/{folder}/metatiles.bin");\n'
                f'const u16 gMetatileAttributes_{sym}[] = INCBIN_U16("data/tilesets/{kind}/{folder}/metatile_attributes.bin");\n')
    with (g / 'src/data/tilesets/headers.h').open('a') as f:
        f.write(f'\n// Mahogany Town ({kind})\nconst struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, .isSecondary = {"TRUE" if secondary else "FALSE"}, '
                f'.tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym}, .metatiles = gMetatiles_{sym}, '
                f'.metatileAttributes = gMetatileAttributes_{sym}, .callback = NULL }};\n')

BUILDS = {'convert': 'HGSS conversion (convert.py)',
          'pack3': 'third draft: shared Johto art + local HGSS buildings, lossless (assemble.py, pack_lossless.py)'}

def main(g, style):
    style = style or 'convert'
    remove_draft(g)
    z = np.load(SRC / style / 'pack.npz')
    grid, pats, pal, metas = z['grid'], z['patterns'], z['palettes'], z['metatiles']
    coll, elev = z['collision'], z['elevation']
    write_tileset(g / f'data/tilesets/primary/{PFOLDER}', pats[:512], pal, metas[metas[:, 0] < 512], range(6))
    write_tileset(g / f'data/tilesets/secondary/{FOLDER}', pats[512:], pal, metas[metas[:, 0] >= 512], range(6, 16))
    register(g, PSYM, PFOLDER, 'primary', False)
    register(g, SYM, FOLDER, 'secondary', True)
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
    m.update(id=map_id(NAME), name=NAME, layout=layout_id(NAME), music='MUS_VERDANTURF', region_map_section='MAPSEC_MAHOGANY_TOWN',
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
    report = json.loads((EV / style / 'pack.json').read_text())
    write(EV / 'capacity.json', dict(map=NAME, primary=PRIMARY, secondary=f'gTileset_{SYM}', build=BUILDS[style],
                                     **{k: report[k] for k in ('tiles', 'tile_limit', 'primary_tiles', 'secondary_tiles', 'metatiles',
                                                                'primary_metatiles', 'secondary_metatiles')}, map_ids=ids))
    print('Installed Mahogany:', ids)

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), sys.argv[2] if len(sys.argv) > 2 else None)
