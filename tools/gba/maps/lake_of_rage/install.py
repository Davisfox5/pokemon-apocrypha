"""Install Lake of Rage (assemble.py + pack_pair.py) and repack Route 43 onto the shared primary
tileset, joined by a map connection.

    python3 tools/gba/maps/lake_of_rage/install.py ENGINE_CHECKOUT

Lake of Rage is one 96x64 map. HGSS joins its south edge to Route 43's north edge with no
gatehouse (Lake x = Route 43 x + 32), so the two maps share the primary tileset
gTileset_Route43Primary (tiles 0-511, palettes 0-5, metatiles 0-511, written by pack_pair.py
from both maps) and each keeps its own secondary: gTileset_Route43 and gTileset_LakeOfRage.
Route 43 keeps every pixel; only its tile and metatile numbering changes (its map.bin is
rewritten), and its border block becomes the Lake's woods block (shared-primary metatiles), so
the world beyond the edges looks the same from either map after crossing the seam. The
connection: Route 43 up to the Lake at offset -32, the Lake down to Route 43 at offset 32.

The two houses' doors stay solid (their interiors are not built), as Mahogany's are. New maps
are appended to gMapGroup_Cherrygrove. The installer refuses if a Lake of Rage or Route 43 file
carries a commit since BASE that is not this tool's, so it never replays over owner edits.
"""
from __future__ import annotations
import json, shutil, struct, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/lake-of-rage'
SRC, EV = ART / 'source', ART / 'evidence'
W, H = 96, 64
NAME, FOLDER, SYM = 'LakeOfRage', 'lake_of_rage', 'LakeOfRage'
PRIMARY = 'gTileset_Route43Primary'                 # shared with Route 43
R43_PRIMARY_DIR, R43_SECONDARY_DIR = 'data/tilesets/primary/route43', 'data/tilesets/secondary/route_43'
BASE = 'origin/claude/route-43'
MAPSEC, MAPSEC_NAME, MAPSEC_XY = 'MAPSEC_LAKE_OF_RAGE', 'LAKE OF RAGE', (4, 2)
MUSIC = 'MUS_ROUTE101'                              # the Johto routes' music on this branch
OFFSET = 32

def read(p): return json.loads(p.read_text())
def write(p, v): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(v, indent=2) + '\n')
def map_id(name): return 'MAP_' + ''.join('_' + c if c.isupper() and i else c for i, c in enumerate(name)).upper()
def layout_id(name): return map_id(name).replace('MAP_', 'LAYOUT_', 1)

SIGNS = [  # HGSS bg events (msg_0626_T29), on HGSS's own sign cells
    ('LakeSign', (48, 50), 'LAKE OF RAGE\\nAlso known as GYARADOS LAKE.'),
    ('GuruHouseSign', (54, 57), "FISHING GURU'S HOUSE"),
]

def jasc(colors):
    return 'JASC-PAL\n0100\n16\n' + '\n'.join(' '.join(map(str, c)) for c in colors) + '\n'

DRAFT = [f'data/layouts/{NAME}', f'data/maps/{NAME}', f'data/tilesets/secondary/{FOLDER}']
SHARED_FILES = ['data/event_scripts.s', 'data/layouts/layouts.json', 'data/maps/map_groups.json', 'include/regions.h',
                'src/apocrypha_map_proof.c', 'src/data/region_map/region_map_sections.json', 'src/data/tilesets/graphics.h',
                'src/data/tilesets/headers.h', 'src/data/tilesets/metatiles.h']
ROUTE43_FILES = ['data/layouts/Route43', 'data/maps/Route43/map.json', R43_PRIMARY_DIR, R43_SECONDARY_DIR]

def git(g, *a):
    return subprocess.run(['git', '-C', str(g), *a], capture_output=True, text=True, check=True).stdout

def remove_draft(g):
    """Remove an earlier install by this tool and restore the shared registration files and
    Route 43's repacked files from BASE. Refuses if any of them carries a commit since BASE
    that is not one of this tool's Lake of Rage commits."""
    for paths in (DRAFT, ROUTE43_FILES):
        foreign = [l for l in git(g, 'log', '--format=%s', f'{BASE}..HEAD', '--', *paths).splitlines() if not l.startswith('Lake of Rage')]
        if foreign:
            raise SystemExit(f'files carry other commits {foreign}: edit native source; never replay over owner edits.')
    for d in DRAFT:
        if (g / d).exists():
            shutil.rmtree(g / d)
    for d in (R43_PRIMARY_DIR, R43_SECONDARY_DIR):
        shutil.rmtree(g / d)
    subprocess.run(['git', '-C', str(g), 'restore', f'--source={BASE}', '--worktree', '--'] + SHARED_FILES + ROUTE43_FILES, check=True)

def write_tileset(d, pats, pal, metas):
    if not len(metas):                                         # the build refuses an empty metatile file:
        metas = np.zeros((1, 10), np.uint16)                   # one blank metatile, used by no cell
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
    (d / 'metatiles.bin').write_bytes(b''.join(struct.pack('<8H', *[int(v) for v in r[1:9]]) for r in metas))
    (d / 'metatile_attributes.bin').write_bytes(struct.pack('<%dH' % len(metas), *[int(r[9]) for r in metas]))

def register(g, sym, folder):
    with (g / 'src/data/tilesets/graphics.h').open('a') as f:
        f.write(f'\n// Lake of Rage (secondary).\n'
                f'const u32 gTilesetTiles_{sym}[] = INCGFX_U32("data/tilesets/secondary/{folder}/tiles.png", ".4bpp.fastSmol");\n'
                f'const u16 gTilesetPalettes_{sym}[][16] = {{\n' +
                ''.join(f'    INCGFX_U16("data/tilesets/secondary/{folder}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n')
    with (g / 'src/data/tilesets/metatiles.h').open('a') as f:
        f.write(f'\n// Lake of Rage (secondary)\nconst u16 gMetatiles_{sym}[] = INCBIN_U16("data/tilesets/secondary/{folder}/metatiles.bin");\n'
                f'const u16 gMetatileAttributes_{sym}[] = INCBIN_U16("data/tilesets/secondary/{folder}/metatile_attributes.bin");\n')
    with (g / 'src/data/tilesets/headers.h').open('a') as f:
        f.write(f'\n// Lake of Rage (secondary)\nconst struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, .isSecondary = TRUE, '
                f'.tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym}, .metatiles = gMetatiles_{sym}, '
                f'.metatileAttributes = gMetatileAttributes_{sym}, .callback = NULL }};\n')

def ordered(m):
    for k in sorted(k for k in ('region', 'build_target') if k in m):  # Porymap's key order
        m[k] = m.pop(k)
    return m

def write_map_bin(path, grid, coll, elev):
    cells = grid.astype(np.uint32) | (coll.astype(np.uint32) << 10) | (elev.astype(np.uint32) << 12)
    path.write_bytes(cells.astype('<u2').tobytes())

def woods_border(grid):
    """The Lake's border block: a 2x2 of its own woods that tiles seamlessly (each of its four
    metatiles equals the one two cells away on every side), so the land beyond the edges reads
    as more forest."""
    h, w = grid.shape
    for y in range(2, h - 4, 2):
        for x in range(2, w - 4, 2):
            b = grid[y:y + 2, x:x + 2]
            if all((grid[y + dy:y + dy + 2, x + dx:x + dx + 2] == b).all() for dy, dx in ((0, 2), (2, 0), (2, 2), (-2, 0), (0, -2))):
                return x, y
    raise SystemExit('no seamless woods block for the border')

def main(g):
    remove_draft(g)
    z = np.load(SRC / 'pair/pack.npz')
    pal_r, pal_l = z['route43_palettes'], z['lake_palettes']
    prim_pal = pal_r.copy(); prim_pal[:6] = z['primary_palettes']
    assert (pal_l[:6] == z['primary_palettes']).all() and (pal_r[:6] == z['primary_palettes']).all()
    write_tileset(g / R43_PRIMARY_DIR, z['primary_patterns'], prim_pal, z['primary_metatiles'])
    write_tileset(g / R43_SECONDARY_DIR, z['route43_patterns'], pal_r, z['route43_metatiles'])
    write_tileset(g / f'data/tilesets/secondary/{FOLDER}', z['lake_patterns'], pal_l, z['lake_metatiles'])
    register(g, SYM, FOLDER)
    # Route 43: same pixels, new numbering.
    rl = g / 'data/layouts/Route43'
    write_map_bin(rl / 'map.bin', z['route43_grid'], z['route43_collision'], z['route43_elevation'])
    p = g / 'data/maps/Route43/map.json'
    rm = read(p)
    rm['connections'] = [dict(map=map_id(NAME), offset=-OFFSET, direction='up')]       # Porymap's key order
    write(p, ordered(rm))
    # Lake of Rage.
    ld = g / f'data/layouts/{NAME}'
    ld.mkdir(parents=True)
    grid = z['lake_grid']
    write_map_bin(ld / 'map.bin', grid, z['lake_collision'], z['lake_elevation'])
    # One border block for both maps: after a player crosses a connection, the tiles already on
    # screen stay until scrolled away, so the world beyond either map's edges must look the
    # same from both. The Lake's seamless woods block, all shared-primary metatiles.
    bx, by = woods_border(grid)
    border = [int(grid[by + (i >> 1), bx + (i & 1)]) for i in range(4)]
    assert all(b < 512 for b in border), 'border block must be shared-primary metatiles'
    for d in (ld, rl):
        (d / 'border.bin').write_bytes(struct.pack('<4H', *border))
    layouts = read(g / 'data/layouts/layouts.json')
    layouts['layouts'].append(dict(id=layout_id(NAME), name=f'{NAME}_Layout', width=W, height=H,
                                   primary_tileset=PRIMARY, secondary_tileset=f'gTileset_{SYM}',
                                   border_filepath=f'data/layouts/{NAME}/border.bin',
                                   blockdata_filepath=f'data/layouts/{NAME}/map.bin', layout_version='emerald'))
    write(g / 'data/layouts/layouts.json', layouts)
    m = dict(read(g / 'data/maps/JohtoRoute31/map.json'))
    m.update(id=map_id(NAME), name=NAME, layout=layout_id(NAME), music=MUSIC, region_map_section=MAPSEC,
             weather='WEATHER_NONE', map_type='MAP_TYPE_TOWN', allow_cycling=True, allow_running=True, show_map_name=True,
             connections=[dict(map='MAP_ROUTE43', offset=OFFSET, direction='down')],
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
    anchor = 'MAP_ROUTE43_MAHOGANY_GATEHOUSE};'
    assert anchor in s
    s = s.replace(anchor, f'MAP_ROUTE43_MAHOGANY_GATEHOUSE, {map_id(NAME)}}};'); p.write_text(s)
    report = json.loads((EV / 'pair/pack.json').read_text())
    write(EV / 'capacity.json', dict(map=NAME, primary=PRIMARY + ' (shared with Route 43)', secondary=f'gTileset_{SYM}',
                                     build='shared Johto art + Blackthorn FRLG rock + natural lake banks, lossless pair pack '
                                           '(assemble.py, pack_pair.py)',
                                     pair=report, border_block=[bx, by], map_id=groups['gMapGroup_Cherrygrove'].index(NAME)))
    print('Installed Lake of Rage:', groups['gMapGroup_Cherrygrove'].index(NAME), 'border block', (bx, by))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
