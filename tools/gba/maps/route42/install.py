"""Install Route 42 (assemble.py + pack_fixed.py), joined to Mahogany Town by a map connection.

    python3 tools/gba/maps/route42/install.py ENGINE_CHECKOUT

Route 42 is one 96x32 map west of Mahogany Town (Route 42 x 96 = Mahogany x 0, rows aligned).
It takes Mahogany's primary tileset (gTileset_MahoganyPrimary) and its own secondary,
gTileset_Route42, which carries exact copies of what Mahogany's visible west edge uses from
Mahogany's secondary (pack_fixed.py). Mahogany keeps every pixel and every metatile; its only
changes are its connection west, metatiles appended to its secondary table and tiles appended
to its secondary tile sheet (after its own 400), which no Mahogany cell uses: Route 42 cells
Mahogany's camera can show whose art Mahogany had no metatile or tile for. Route 42's border
block is Mahogany's (metatile 0).

The Mt. Mortar mouths and the Ecruteak gate's doorway stay solid (neither interior is built).
New maps are appended to gMapGroup_Cherrygrove. The installer refuses if a Route 42 or
Mahogany file carries a commit since BASE that is not this tool's, so it never replays over
owner edits.
"""
from __future__ import annotations
import json, shutil, struct, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route-42'
SRC, EV = ART / 'source', ART / 'evidence'
W, H = 96, 32
NAME, FOLDER, SYM = 'Route42', 'route_42', 'Route42'
PRIMARY = 'gTileset_MahoganyPrimary'                # shared with Mahogany Town
MAH_SECONDARY = 'data/tilesets/secondary/mahogany_town'
BASE = 'origin/claude/route-44'
MAPSEC, MAPSEC_NAME, MAPSEC_XY = 'MAPSEC_JOHTO_ROUTE_42', 'ROUTE 42', (3, 4)
MUSIC = 'MUS_ROUTE101'                              # the Johto routes' music on this branch

def read(p): return json.loads(p.read_text())
def write(p, v): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(v, indent=2) + '\n')
def map_id(name): return 'MAP_' + ''.join('_' + c if c.isupper() and i else c for i, c in enumerate(name)).upper()
def layout_id(name): return map_id(name).replace('MAP_', 'LAYOUT_', 1)

SIGNS = [  # HGSS bg events (msg_0399_R42); the east route sign stands on (86, 12) (assemble.SIGNS)
    ('WestRouteSign', (11, 17), 'ROUTE 42\\nECRUTEAK CITY - MAHOGANY TOWN'),
    ('WestMtMortarSign', (16, 11), 'MT. MORTAR\\nWATERFALL CAVE INSIDE'),
    ('EastMtMortarSign', (75, 12), 'MT. MORTAR\\nWATERFALL CAVE INSIDE'),
    ('EastRouteSign', (86, 12), 'ROUTE 42\\nMAHOGANY TOWN - ECRUTEAK CITY'),
]

def jasc(colors):
    return 'JASC-PAL\n0100\n16\n' + '\n'.join(' '.join(map(str, c)) for c in colors) + '\n'

DRAFT = [f'data/layouts/{NAME}', f'data/maps/{NAME}', f'data/tilesets/secondary/{FOLDER}']
SHARED_FILES = ['data/event_scripts.s', 'data/layouts/layouts.json', 'data/maps/map_groups.json', 'include/regions.h',
                'src/apocrypha_map_proof.c', 'src/data/region_map/region_map_sections.json', 'src/data/tilesets/graphics.h',
                'src/data/tilesets/headers.h', 'src/data/tilesets/metatiles.h']
MAHOGANY_FILES = ['data/maps/MahoganyTown/map.json', f'{MAH_SECONDARY}/metatiles.bin', f'{MAH_SECONDARY}/metatile_attributes.bin',
                  f'{MAH_SECONDARY}/tiles.png']

def git(g, *a):
    return subprocess.run(['git', '-C', str(g), *a], capture_output=True, text=True, check=True).stdout

def remove_draft(g):
    """Remove an earlier install by this tool and restore the shared registration files and
    Mahogany's touched files from BASE. Refuses if any of them carries a commit since BASE
    that is not one of this tool's Route 42 commits."""
    for paths in (DRAFT, MAHOGANY_FILES):
        foreign = [l for l in git(g, 'log', '--format=%s', f'{BASE}..HEAD', '--', *paths).splitlines() if not l.startswith('Route 42')]
        if foreign:
            raise SystemExit(f'files carry other commits {foreign}: edit native source; never replay over owner edits.')
    for d in DRAFT:
        if (g / d).exists():
            shutil.rmtree(g / d)
    subprocess.run(['git', '-C', str(g), 'restore', f'--source={BASE}', '--worktree', '--'] + SHARED_FILES + MAHOGANY_FILES, check=True)

def write_tileset(d, pats, pal, metas):
    """pats: tile index patterns from tile 512; metas: rows of 8 entries + attribute from id 512."""
    if d.exists():
        shutil.rmtree(d)
    (d / 'palettes').mkdir(parents=True, exist_ok=True)
    rows = max(1, (len(pats) + 15) // 16)
    buf = np.zeros((rows * 8, 128), np.uint8)
    for i, t in enumerate(pats):
        buf[(i // 16) * 8:(i // 16) * 8 + 8, (i % 16) * 8:(i % 16) * 8 + 8] = t
    im = Image.fromarray(buf, 'P'); im.putpalette([v for i in range(16) for v in (i * 17,) * 3] + [0] * 720)
    im.save(d / 'tiles.png', bits=4)
    for bank in range(16):                                     # every bank written, for Porymap's display
        (d / 'palettes' / f'{bank:02}.pal').write_text(jasc([tuple(int(v) for v in pal[bank][i]) for i in range(16)]))
    (d / 'metatiles.bin').write_bytes(b''.join(struct.pack('<8H', *[int(v) for v in r[:8]]) for r in metas))
    (d / 'metatile_attributes.bin').write_bytes(struct.pack('<%dH' % len(metas), *[int(r[8]) for r in metas]))

def register(g, sym, folder):
    with (g / 'src/data/tilesets/graphics.h').open('a') as f:
        f.write(f'\n// Route 42 (secondary).\n'
                f'const u32 gTilesetTiles_{sym}[] = INCGFX_U32("data/tilesets/secondary/{folder}/tiles.png", ".4bpp.fastSmol");\n'
                f'const u16 gTilesetPalettes_{sym}[][16] = {{\n' +
                ''.join(f'    INCGFX_U16("data/tilesets/secondary/{folder}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n')
    with (g / 'src/data/tilesets/metatiles.h').open('a') as f:
        f.write(f'\n// Route 42 (secondary)\nconst u16 gMetatiles_{sym}[] = INCBIN_U16("data/tilesets/secondary/{folder}/metatiles.bin");\n'
                f'const u16 gMetatileAttributes_{sym}[] = INCBIN_U16("data/tilesets/secondary/{folder}/metatile_attributes.bin");\n')
    with (g / 'src/data/tilesets/headers.h').open('a') as f:
        f.write(f'\n// Route 42 (secondary)\nconst struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, .isSecondary = TRUE, '
                f'.tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym}, .metatiles = gMetatiles_{sym}, '
                f'.metatileAttributes = gMetatileAttributes_{sym}, .callback = NULL }};\n')

def ordered(m):
    for k in sorted(k for k in ('region', 'build_target') if k in m):  # Porymap's key order
        m[k] = m.pop(k)
    return m

def write_map_bin(path, grid, coll, elev):
    cells = grid.astype(np.uint32) | (coll.astype(np.uint32) << 10) | (elev.astype(np.uint32) << 12)
    path.write_bytes(cells.astype('<u2').tobytes())

def main(g):
    remove_draft(g)
    z = np.load(SRC / 'pack3/pack.npz')
    # Mahogany: metatiles appended to its secondary table, tiles to its secondary tile sheet
    # (no Mahogany cell uses them).
    md = g / MAH_SECONDARY
    mt, at = (md / 'metatiles.bin').read_bytes(), (md / 'metatile_attributes.bin').read_bytes()
    app = z['mahogany_secondary_append']
    assert len(z['mahogany_primary_append']) == 0, 'a metatile for Mahogany\'s primary table: not handled'
    assert len(mt) // 16 == 162, ('Mahogany\'s secondary metatile table is not the accepted one with Route 44\'s two', len(mt) // 16)
    new_tiles = z['mahogany_new_tiles']
    im = Image.open(md / 'tiles.png')
    old = np.array(im)
    assert old.shape == (200, 128), ('Mahogany\'s secondary tile sheet is not the accepted one', old.shape)
    if len(new_tiles):
        rows = (400 + len(new_tiles) + 15) // 16
        buf = np.zeros((rows * 8, 128), np.uint8)
        buf[:200] = old
        for i, t in enumerate(new_tiles):
            k = 400 + i
            buf[(k // 16) * 8:(k // 16) * 8 + 8, (k % 16) * 8:(k % 16) * 8 + 8] = t
        out = Image.fromarray(buf, 'P'); out.putpalette(im.getpalette())
        out.save(md / 'tiles.png', bits=4)
    (md / 'metatiles.bin').write_bytes(mt + b''.join(struct.pack('<8H', *[int(v) for v in r[:8]]) for r in app))
    (md / 'metatile_attributes.bin').write_bytes(at + struct.pack('<%dH' % len(app), *[int(r[8]) for r in app]))
    # Mahogany's connection east.
    p = g / 'data/maps/MahoganyTown/map.json'
    mm = read(p)
    assert mm['connections'] == [dict(map='MAP_ROUTE44', offset=0, direction='right')], mm['connections']
    mm['connections'].append(dict(map=map_id(NAME), offset=0, direction='left'))         # Porymap's key order
    write(p, ordered(mm))
    # Route 42.
    write_tileset(g / f'data/tilesets/secondary/{FOLDER}', z['secondary_tiles'], z['palettes'], z['secondary_metatiles'])
    register(g, SYM, FOLDER)
    ld = g / f'data/layouts/{NAME}'
    ld.mkdir(parents=True)
    write_map_bin(ld / 'map.bin', z['grid'], z['collision'], z['elevation'])
    border = (g / 'data/layouts/MahoganyTown/border.bin').read_bytes()
    assert all(v < 512 for v in struct.unpack('<4H', border)), 'Mahogany\'s border block is not primary'
    (ld / 'border.bin').write_bytes(border)
    layouts = read(g / 'data/layouts/layouts.json')
    layouts['layouts'].append(dict(id=layout_id(NAME), name=f'{NAME}_Layout', width=W, height=H,
                                   primary_tileset=PRIMARY, secondary_tileset=f'gTileset_{SYM}',
                                   border_filepath=f'data/layouts/{NAME}/border.bin',
                                   blockdata_filepath=f'data/layouts/{NAME}/map.bin', layout_version='emerald'))
    write(g / 'data/layouts/layouts.json', layouts)
    m = dict(read(g / 'data/maps/Route43/map.json'))
    m.update(id=map_id(NAME), name=NAME, layout=layout_id(NAME), music=MUSIC, region_map_section=MAPSEC,
             weather='WEATHER_NONE', map_type='MAP_TYPE_ROUTE', allow_cycling=True, allow_running=True, show_map_name=True,
             connections=[dict(map='MAP_MAHOGANY_TOWN', offset=0, direction='right')],
             object_events=[], warp_events=[], coord_events=[], bg_events=[])
    script = f'{NAME}_MapScripts::\n    .byte 0\n'
    for label, (x, y), text in SIGNS:
        m['bg_events'].append(dict(type='sign', x=x, y=y, elevation=0, player_facing_dir='BG_EVENT_PLAYER_FACING_ANY',
                                   script=f'{NAME}_{label}'))
        script += (f'\n{NAME}_{label}::\n    msgbox {NAME}_{label}_Text, MSGBOX_SIGN\n    end\n'
                   f'\n{NAME}_{label}_Text:\n    .string "{text}$"\n')
    write(g / f'data/maps/{NAME}/map.json', ordered(m))
    (g / f'data/maps/{NAME}/scripts.inc').write_text(script)
    groups = read(g / 'data/maps/map_groups.json')
    groups['gMapGroup_Cherrygrove'].append(NAME)
    write(g / 'data/maps/map_groups.json', groups)
    with (g / 'data/event_scripts.s').open('a') as f:
        f.write(f'\n.include "data/maps/{NAME}/scripts.inc"\n')
    p = g / 'src/data/region_map/region_map_sections.json'; r = read(p)
    r['map_sections'].append(dict(id=MAPSEC, name=MAPSEC_NAME, x=MAPSEC_XY[0], y=MAPSEC_XY[1], width=1, height=1)); write(p, r)
    p = g / 'include/regions.h'; s = p.read_text()
    s = s.replace('    case MAPSEC_CHERRYGROVE_CITY:', f'    case {MAPSEC}: return REGION_JOHTO;\n    case MAPSEC_CHERRYGROVE_CITY:', 1); p.write_text(s)
    p = g / 'src/apocrypha_map_proof.c'; s = p.read_text()
    anchor = 'MAP_ROUTE44};'
    assert anchor in s
    s = s.replace(anchor, f'MAP_ROUTE44, {map_id(NAME)}}};'); p.write_text(s)
    report = json.loads((EV / 'pack3/pack.json').read_text())
    write(EV / 'capacity.json', dict(map=NAME, primary=PRIMARY + ' (Mahogany Town\'s)', secondary=f'gTileset_{SYM}',
                                     build='shared Johto art + Blackthorn FRLG rock + natural water banks, lossless pack on '
                                           'Mahogany\'s tilesets (assemble.py, pack_fixed.py)',
                                     pack={k: v for k, v in report.items() if k not in ('seam', 'reserved_tiles')},
                                     map_id=groups['gMapGroup_Cherrygrove'].index(NAME)))
    print('Installed Route 42:', groups['gMapGroup_Cherrygrove'].index(NAME), 'Mahogany appended', len(app), 'metatiles,',
          len(new_tiles), 'tiles')

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
