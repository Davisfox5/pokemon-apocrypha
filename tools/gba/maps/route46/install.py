"""Install Route 46 (assemble.py + pack_fixed.py), joined to Route 45 by a map connection.

    python3 tools/gba/maps/route46/install.py ENGINE_CHECKOUT

Route 46 is one 32x64 map west of Route 45's foot (Route 46 (x, y) = Route 45 (x - 32, y + 128)).
It takes Route 45's primary tileset (gTileset_CherrygrovePrimary) and its own secondary,
gTileset_Route46, which carries exact copies of what Route 45's visible west edge uses from Route
45's secondary (pack_fixed.py). Route 45 is owner-accepted and locked: it keeps every pixel and
every metatile; its only changes are its connection west and metatiles appended to its secondary
table (and tiles appended to its secondary tile sheet, after its own 480), which no Route 45 cell
uses: Route 46 cells Route 45's camera can show whose art Route 45 had no metatile for. Route 46's
border block is Route 45's (Blackthorn's metatile 512, copied whole).

The Dark Cave mouth stays solid (Dark Cave is not built), and so does the Rock Climb wall; the Route
29 gatehouse at the south end is G01a's roof with no doorway (its interior and Route 29's side are
not built). The new map is appended to gMapGroup_Cherrygrove, Route 45's group. The installer
refuses if a Route 46 or Route 45 file carries a commit since BASE that is not this tool's, so it
never replays over owner edits.
"""
from __future__ import annotations
import json, shutil, struct, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route-46'
SRC, EV = ART / 'source', ART / 'evidence'
W, H = 32, 64
NAME, FOLDER, SYM = 'Route46', 'route_46', 'Route46'
PRIMARY = 'gTileset_CherrygrovePrimary'             # shared with Route 45 and Blackthorn City
NB, NB_MAP = 'Route45', 'MAP_ROUTE45'
NB_SECONDARY = 'data/tilesets/secondary/route_45'
NB_TILES, NB_METAS = 480, 380                       # Route 45's secondary as committed on BASE
NB_OFFSET = 128                                     # Route 46's row 0 is Route 45's row 128
BASE = 'origin/claude/route-45'
MAPSEC, MAPSEC_NAME, MAPSEC_XY = 'MAPSEC_JOHTO_ROUTE_46', 'ROUTE 46', (5, 5)
MUSIC = 'MUS_ROUTE101'                              # the Johto routes' music (Routes 42-44)

def read(p): return json.loads(p.read_text())
def write(p, v): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(v, indent=2) + '\n')
def map_id(name): return 'MAP_' + ''.join('_' + c if c.isupper() and i else c for i, c in enumerate(name)).upper()
def layout_id(name): return map_id(name).replace('MAP_', 'LAYOUT_', 1)

SIGNS = [  # HGSS bg events (scr_seq_R46_001 and _002)
    ('RouteSign', (20, 50), 'ROUTE 46\\nMOUNTAIN ROAD AHEAD'),
    ('DarkCaveSign', (22, 10), 'DARK CAVE'),
]

def jasc(colors):
    return 'JASC-PAL\n0100\n16\n' + '\n'.join(' '.join(map(str, c)) for c in colors) + '\n'

DRAFT = [f'data/layouts/{NAME}', f'data/maps/{NAME}', f'data/tilesets/secondary/{FOLDER}']
SHARED_FILES = ['data/event_scripts.s', 'data/layouts/layouts.json', 'data/maps/map_groups.json', 'include/regions.h',
                'src/apocrypha_map_proof.c', 'src/data/region_map/region_map_sections.json', 'src/data/tilesets/graphics.h',
                'src/data/tilesets/headers.h', 'src/data/tilesets/metatiles.h']
NB_FILES = [f'data/maps/{NB}/map.json', f'{NB_SECONDARY}/metatiles.bin', f'{NB_SECONDARY}/metatile_attributes.bin',
            f'{NB_SECONDARY}/tiles.png']

def git(g, *a):
    return subprocess.run(['git', '-C', str(g), *a], capture_output=True, text=True, check=True).stdout

def remove_draft(g):
    """Remove an earlier install by this tool and restore the shared registration files and
    Route 45's touched files from BASE. Refuses if any of them carries a commit since BASE
    that is not one of this tool's Route 46 commits."""
    for paths in (DRAFT, NB_FILES):
        foreign = [l for l in git(g, 'log', '--format=%s', f'{BASE}..HEAD', '--', *paths).splitlines() if not l.startswith('Route 46')]
        if foreign:
            raise SystemExit(f'files carry other commits {foreign}: edit native source; never replay over owner edits.')
    for d in DRAFT:
        if (g / d).exists():
            shutil.rmtree(g / d)
    subprocess.run(['git', '-C', str(g), 'restore', f'--source={BASE}', '--worktree', '--'] + SHARED_FILES + NB_FILES, check=True)

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
        f.write(f'\n// Route 46 (secondary).\n'
                f'const u32 gTilesetTiles_{sym}[] = INCGFX_U32("data/tilesets/secondary/{folder}/tiles.png", ".4bpp.fastSmol");\n'
                f'const u16 gTilesetPalettes_{sym}[][16] = {{\n' +
                ''.join(f'    INCGFX_U16("data/tilesets/secondary/{folder}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n')
    with (g / 'src/data/tilesets/metatiles.h').open('a') as f:
        f.write(f'\n// Route 46 (secondary)\nconst u16 gMetatiles_{sym}[] = INCBIN_U16("data/tilesets/secondary/{folder}/metatiles.bin");\n'
                f'const u16 gMetatileAttributes_{sym}[] = INCBIN_U16("data/tilesets/secondary/{folder}/metatile_attributes.bin");\n')
    with (g / 'src/data/tilesets/headers.h').open('a') as f:
        f.write(f'\n// Route 46 (secondary)\nconst struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, .isSecondary = TRUE, '
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
    report = json.loads((EV / 'pack3/pack.json').read_text())
    # Route 45: metatiles appended to its secondary table, tiles to its secondary tile sheet
    # (no Route 45 cell uses them).
    md = g / NB_SECONDARY
    mt, at = (md / 'metatiles.bin').read_bytes(), (md / 'metatile_attributes.bin').read_bytes()
    app = z['route45_secondary_append']
    assert len(z['route45_primary_append']) == 0, 'a metatile for Route 45\'s primary table: not handled'
    assert len(mt) // 16 == NB_METAS, ('Route 45\'s secondary metatile table is not the one on BASE', len(mt) // 16)
    new_tiles = z['route45_new_tiles']
    im = Image.open(md / 'tiles.png')
    old = np.array(im)
    assert old.shape == (NB_TILES // 16 * 8, 128), ('Route 45\'s secondary tile sheet is not the one on BASE', old.shape)
    if len(new_tiles):
        rows = (NB_TILES + len(new_tiles) + 15) // 16
        buf = np.zeros((rows * 8, 128), np.uint8)
        buf[:old.shape[0]] = old
        for i, t in enumerate(new_tiles):
            k = NB_TILES + i
            buf[(k // 16) * 8:(k // 16) * 8 + 8, (k % 16) * 8:(k % 16) * 8 + 8] = t
        out = Image.fromarray(buf, 'P'); out.putpalette(im.getpalette())
        out.save(md / 'tiles.png', bits=4)
    (md / 'metatiles.bin').write_bytes(mt + b''.join(struct.pack('<8H', *[int(v) for v in r[:8]]) for r in app))
    (md / 'metatile_attributes.bin').write_bytes(at + struct.pack('<%dH' % len(app), *[int(r[8]) for r in app]))
    # Route 45's connection west (beside its connection up to Blackthorn).
    p = g / f'data/maps/{NB}/map.json'
    mm = read(p)
    assert [c['direction'] for c in mm['connections']] == ['up'], mm['connections']
    mm['connections'].append(dict(map=map_id(NAME), offset=NB_OFFSET, direction='left'))
    write(p, ordered(mm))
    # Route 46.
    write_tileset(g / f'data/tilesets/secondary/{FOLDER}', z['secondary_tiles'], z['palettes'], z['secondary_metatiles'])
    register(g, SYM, FOLDER)
    ld = g / f'data/layouts/{NAME}'
    ld.mkdir(parents=True)
    write_map_bin(ld / 'map.bin', z['grid'], z['collision'], z['elevation'])
    border = (g / f'data/layouts/{NB}/border.bin').read_bytes()
    reserved = {int(k): v for k, v in report['reserved_metatiles'].items()}
    assert all(v < 512 or reserved.get(v) == [0, 1, 2, 3] for v in struct.unpack('<4H', border)), \
        'Route 45\'s border block is not one Route 46 carries whole'
    (ld / 'border.bin').write_bytes(border)
    layouts = read(g / 'data/layouts/layouts.json')
    layouts['layouts'].append(dict(id=layout_id(NAME), name=f'{NAME}_Layout', width=W, height=H,
                                   primary_tileset=PRIMARY, secondary_tileset=f'gTileset_{SYM}',
                                   border_filepath=f'data/layouts/{NAME}/border.bin',
                                   blockdata_filepath=f'data/layouts/{NAME}/map.bin', layout_version='emerald'))
    write(g / 'data/layouts/layouts.json', layouts)
    m = dict(read(g / f'data/maps/{NB}/map.json'))
    m.update(id=map_id(NAME), name=NAME, layout=layout_id(NAME), music=MUSIC, region_map_section=MAPSEC,
             weather='WEATHER_NONE', map_type='MAP_TYPE_ROUTE', allow_cycling=True, allow_running=True, show_map_name=True,
             connections=[dict(map=NB_MAP, offset=-NB_OFFSET, direction='right')],
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
    anchor = 'MAP_BLACKTHORN_MART, MAP_ROUTE45};'
    assert anchor in s
    s = s.replace(anchor, f'MAP_BLACKTHORN_MART, MAP_ROUTE45, {map_id(NAME)}}};'); p.write_text(s)
    write(EV / 'capacity.json', dict(map=NAME, primary=PRIMARY + ' (Route 45\'s and Blackthorn City\'s)', secondary=f'gTileset_{SYM}',
                                     build='shared Johto art + Blackthorn FRLG rock, G01a gate roof, lossless pack beside '
                                           'Route 45\'s tilesets (assemble.py, pack_fixed.py)',
                                     pack={k: v for k, v in report.items() if k not in ('seam', 'reserved_tiles')},
                                     map_id=groups['gMapGroup_Cherrygrove'].index(NAME)))
    print('Installed Route 46:', groups['gMapGroup_Cherrygrove'].index(NAME), 'Route 45 appended', len(app), 'metatiles,',
          len(new_tiles), 'tiles')

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
