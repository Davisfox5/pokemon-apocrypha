"""Install Route 43 (assemble.py + pack_lossless.py) as one native map, with its two gatehouses,
and wire Mahogany Town's north gate to it.

    python3 tools/gba/maps/route43/install.py ENGINE_CHECKOUT

Route 43 is a single 32x64 map on its own tileset pair: gTileset_Route43Primary (tiles
0-511) and gTileset_Route43 (the rest). It sits directly north of Mahogany Town in HGSS's map
matrix (Route 43 at (16,3)-(16,4), Mahogany at (16,5)), with HGSS's Mahogany gatehouse
straddling the seam. The two maps are not joined by a map connection: Gen 3 draws a connected
map with the current map's tilesets, and Mahogany and Route 43 each have their own pair, so
the walk between them is the gatehouse's warps and each map shows its own rock border beyond
the seam.

Gatehouse interiors: Emerald's north-south gatehouse layout (LAYOUT_BATTLE_FRONTIER_RECEPTION_GATE:
south arrow warp (4,13), north doorway (4,1)), without its attendants. FRLG's N-S entrance
layout is not used because FRLG tilesets are not compiled into the Emerald build.

    Route43Gatehouse          the toll gate: south door (25,47)/(26,47), north arrow warps (25,39)/(26,39)
    Route43MahoganyGatehouse  Mahogany (12,5)/(13,5) to Route 43's arrow warps (12,61)/(13,61)

Mahogany is owner-accepted and locked: its wiring is a native-source edit (two warp events, the
two doorway cells' collision cleared, their two single-use metatiles given MB_NON_ANIMATED_DOOR),
applied idempotently; no Mahogany generator is run and no Mahogany pixel changes.

New maps are appended to gMapGroup_Cherrygrove. Existing ids are untouched. The installer
refuses if any Route 43 file was last changed by a commit that is not this tool's.
"""
from __future__ import annotations
import json, re, shutil, struct, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route-43'
SRC, EV = ART / 'source', ART / 'evidence'
W, H = 32, 64
NAME, FOLDER, SYM = 'Route43', 'route_43', 'Route43'
PFOLDER, PSYM = 'route43', 'Route43Primary'
PRIMARY = f'gTileset_{PSYM}'
BASE = 'origin/claude/mahogany-town'
BORDER = (30, 62)                   # the east ridge's plain rock top (2x2 block, cells 30-31, rows 62-63)
MAPSEC, MAPSEC_NAME, MAPSEC_XY = 'MAPSEC_JOHTO_ROUTE_43', 'ROUTE 43', (4, 3)
MUSIC = 'MUS_ROUTE101'              # the Johto routes' and gates' music on this branch
GATE_LAYOUT = 'LAYOUT_BATTLE_FRONTIER_RECEPTION_GATE'

def read(p): return json.loads(p.read_text())
def write(p, v): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(v, indent=2) + '\n')
def map_id(name): return 'MAP_' + ''.join('_' + c if c.isupper() and i else c for i, c in enumerate(name)).upper()
def layout_id(name): return map_id(name).replace('MAP_', 'LAYOUT_', 1)

TRAINER_TIPS = ("TRAINER TIPS\\p"
                "All POKéMON have pros and cons\\ndepending on their types.\\p"
                "If their types differ, even a\\nhigher-level POKéMON may lose\\lin battle.\\p"
                "Learn which types are strong or\\nweak against your POKéMON's type.")
SIGNS = [  # HGSS bg events (msg_0401_R43), on HGSS's own sign cells
    ('NorthSign', (20, 3), 'ROUTE 43\\nNORTH: LAKE OF RAGE\\pSOUTH: MAHOGANY TOWN'),
    ('TrainerTips', (20, 50), TRAINER_TIPS),
    ('SouthSign', (15, 58), 'ROUTE 43\\nNORTH: LAKE OF RAGE'),
]
GATEHOUSE, MGATEHOUSE = 'Route43Gatehouse', 'Route43MahoganyGatehouse'
WARPS = [  # Route 43 warp events, in HGSS's order (zone event R43)
    ((12, 61), MGATEHOUSE, '1'), ((13, 61), MGATEHOUSE, '1'),
    ((25, 47), GATEHOUSE, '0'), ((26, 47), GATEHOUSE, '0'),
    ((25, 39), GATEHOUSE, '1'), ((26, 39), GATEHOUSE, '1'),
]
INTERIORS = {  # interior: (south warp destination, north warp destination) as (map, warp id)
    GATEHOUSE: ((NAME, '2'), (NAME, '4')),
    MGATEHOUSE: (('MahoganyTown', '1'), (NAME, '0')),
}
MAHOGANY_DOORS = [(12, 5), (13, 5)]

def jasc(colors):
    return 'JASC-PAL\n0100\n16\n' + '\n'.join(' '.join(map(str, c)) for c in colors) + '\n'

DRAFT = [f'data/layouts/{NAME}', f'data/maps/{NAME}', f'data/maps/{GATEHOUSE}', f'data/maps/{MGATEHOUSE}',
         f'data/tilesets/secondary/{FOLDER}', f'data/tilesets/primary/{PFOLDER}']
SHARED_FILES = ['data/event_scripts.s', 'data/layouts/layouts.json', 'data/maps/map_groups.json', 'include/regions.h',
                'src/apocrypha_map_proof.c', 'src/data/region_map/region_map_sections.json', 'src/data/tilesets/graphics.h',
                'src/data/tilesets/headers.h', 'src/data/tilesets/metatiles.h']
MAHOGANY_FILES = ['data/maps/MahoganyTown/map.json', 'data/layouts/MahoganyTown/map.bin',
                  'data/tilesets/primary/mahogany/metatile_attributes.bin', 'data/tilesets/secondary/mahogany_town/metatile_attributes.bin']

def git(g, *a):
    return subprocess.run(['git', '-C', str(g), *a], capture_output=True, text=True, check=True).stdout

def remove_draft(g):
    """Remove an earlier Route 43 install by this tool and restore the shared registration files
    and Mahogany's four wiring files from BASE. Refuses if a Route 43 or Mahogany file carries a
    commit (since BASE) that is not one of this tool's Route 43 commits."""
    for paths in (DRAFT, MAHOGANY_FILES):
        foreign = [l for l in git(g, 'log', '--format=%s', f'{BASE}..HEAD', '--', *paths).splitlines() if not l.startswith('Route 43')]
        if foreign:
            raise SystemExit(f'files carry other commits {foreign}: edit native source; never replay over owner edits.')
    for d in DRAFT:
        if (g / d).exists():
            shutil.rmtree(g / d)
    subprocess.run(['git', '-C', str(g), 'restore', f'--source={BASE}', '--worktree', '--'] + SHARED_FILES + MAHOGANY_FILES, check=True)

def write_tileset(d, pats, pal, metas):
    if not len(metas):                                         # the build refuses an empty metatile file:
        metas = np.zeros((1, 10), np.uint16)                   # one blank metatile, used by no cell
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
        f.write(f'\n// Route 43 ({kind}).\n'
                f'const u32 gTilesetTiles_{sym}[] = INCGFX_U32("data/tilesets/{kind}/{folder}/tiles.png", ".4bpp.fastSmol");\n'
                f'const u16 gTilesetPalettes_{sym}[][16] = {{\n' +
                ''.join(f'    INCGFX_U16("data/tilesets/{kind}/{folder}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n')
    with (g / 'src/data/tilesets/metatiles.h').open('a') as f:
        f.write(f'\n// Route 43 ({kind})\nconst u16 gMetatiles_{sym}[] = INCBIN_U16("data/tilesets/{kind}/{folder}/metatiles.bin");\n'
                f'const u16 gMetatileAttributes_{sym}[] = INCBIN_U16("data/tilesets/{kind}/{folder}/metatile_attributes.bin");\n')
    with (g / 'src/data/tilesets/headers.h').open('a') as f:
        f.write(f'\n// Route 43 ({kind})\nconst struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, .isSecondary = {"TRUE" if secondary else "FALSE"}, '
                f'.tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym}, .metatiles = gMetatiles_{sym}, '
                f'.metatileAttributes = gMetatileAttributes_{sym}, .callback = NULL }};\n')

def ordered(m):
    for k in sorted(k for k in ('region', 'build_target') if k in m):  # Porymap's key order
        m[k] = m.pop(k)
    return m

def wire_mahogany(g):
    """Mahogany's native-source edit: the gate doorway cells open onto the Mahogany gatehouse.
    Idempotent."""
    behaviors = re.findall(r'^\s+(MB_[A-Z0-9_]+),', (g / 'include/constants/metatile_behaviors.h').read_text(), re.M)
    door = behaviors.index('MB_NON_ANIMATED_DOOR')
    lay = g / 'data/layouts/MahoganyTown/map.bin'
    m = np.frombuffer(lay.read_bytes(), '<u2').reshape(32, 32).copy()
    for x, y in MAHOGANY_DOORS:
        mt = int(m[y, x] & 0x3FF)
        assert int(((m & 0x3FF) == mt).sum()) == 1, ('Mahogany gate metatile is shared', mt)
        f = g / ('data/tilesets/primary/mahogany/metatile_attributes.bin' if mt < 512 else
                 'data/tilesets/secondary/mahogany_town/metatile_attributes.bin')
        at = np.frombuffer(f.read_bytes(), '<u2').copy()
        i = mt if mt < 512 else mt - 512
        at[i] = (int(at[i]) & 0xFF00) | door
        f.write_bytes(at.astype('<u2').tobytes())
        m[y, x] = int(m[y, x]) & 0xF3FF                          # collision 0, elevation kept (3)
    lay.write_bytes(m.astype('<u2').tobytes())
    p = g / 'data/maps/MahoganyTown/map.json'
    mj = read(p)
    mj['warp_events'] = [w for w in mj['warp_events'] if (w['x'], w['y']) not in MAHOGANY_DOORS]
    for x, y in MAHOGANY_DOORS:
        mj['warp_events'].append(dict(x=x, y=y, elevation=0, dest_map=map_id(MGATEHOUSE), dest_warp_id='0'))
    write(p, ordered(mj))

def main(g):
    remove_draft(g)
    z = np.load(SRC / 'pack3/pack.npz')
    grid, pats, pal, metas = z['grid'], z['patterns'], z['palettes'], z['metatiles']
    coll, elev = z['collision'], z['elevation']
    write_tileset(g / f'data/tilesets/primary/{PFOLDER}', pats[:512], pal, metas[metas[:, 0] < 512])
    write_tileset(g / f'data/tilesets/secondary/{FOLDER}', pats[512:], pal, metas[metas[:, 0] >= 512])
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

    m = dict(read(g / 'data/maps/JohtoRoute31/map.json'))
    m.update(id=map_id(NAME), name=NAME, layout=layout_id(NAME), music=MUSIC, region_map_section=MAPSEC,
             weather='WEATHER_NONE', map_type='MAP_TYPE_ROUTE', allow_cycling=True, allow_running=True, show_map_name=True,
             connections=None,
             object_events=[], warp_events=[], coord_events=[], bg_events=[])
    for (x, y), dest, warp in WARPS:
        m['warp_events'].append(dict(x=x, y=y, elevation=0, dest_map=map_id(dest), dest_warp_id=warp))
    script = f'{NAME}_MapScripts::\n    .byte 0\n'
    for label, (x, y), text in SIGNS:
        m['bg_events'].append(dict(type='sign', x=x, y=y, elevation=0, player_facing_dir='BG_EVENT_PLAYER_FACING_ANY',
                                   script=f'{NAME}_{label}'))
        script += (f'\n{NAME}_{label}::\n    msgbox {NAME}_{label}_Text, MSGBOX_SIGN\n    end\n'
                   f'\n{NAME}_{label}_Text:\n    .string "{text}$"\n')
    write(g / f'data/maps/{NAME}/map.json', ordered(m))
    (g / f'data/maps/{NAME}/scripts.inc').write_text(script)

    src = read(g / 'data/maps/BattleFrontier_ReceptionGate/map.json')
    assert src['layout'] == GATE_LAYOUT and [(w['x'], w['y']) for w in src['warp_events']] == [(4, 13), (4, 1)]
    for name, (south, north) in INTERIORS.items():
        im_ = dict(src)
        im_.update(id=map_id(name), name=name, music=MUSIC, region_map_section=MAPSEC, map_type='MAP_TYPE_INDOOR',
                   show_map_name=False, connections=None, object_events=[], coord_events=[], bg_events=[],
                   warp_events=[dict(x=4, y=13, elevation=0, dest_map=map_id(south[0]), dest_warp_id=south[1]),
                                dict(x=4, y=1, elevation=0, dest_map=map_id(north[0]), dest_warp_id=north[1])])
        write(g / f'data/maps/{name}/map.json', ordered(im_))
        (g / f'data/maps/{name}/scripts.inc').write_text(f'{name}_MapScripts::\n    .byte 0\n')
    all_new = [NAME, GATEHOUSE, MGATEHOUSE]
    groups = read(g / 'data/maps/map_groups.json')
    groups['gMapGroup_Cherrygrove'].extend(all_new)
    write(g / 'data/maps/map_groups.json', groups)
    with (g / 'data/event_scripts.s').open('a') as f:
        for n in all_new:
            f.write(f'\n.include "data/maps/{n}/scripts.inc"\n')
    p = g / 'src/data/region_map/region_map_sections.json'; r = read(p)
    r['map_sections'].append(dict(id=MAPSEC, name=MAPSEC_NAME, x=MAPSEC_XY[0], y=MAPSEC_XY[1], width=1, height=1)); write(p, r)
    p = g / 'include/regions.h'; s = p.read_text()
    s = s.replace('    case MAPSEC_CHERRYGROVE_CITY:', f'    case {MAPSEC}: return REGION_JOHTO;\n    case MAPSEC_CHERRYGROVE_CITY:', 1); p.write_text(s)
    p = g / 'src/apocrypha_map_proof.c'; s = p.read_text()
    anchor = 'MAP_MAHOGANY_CENTER_UPSTAIRS};'
    assert anchor in s
    s = s.replace(anchor, 'MAP_MAHOGANY_CENTER_UPSTAIRS, ' + ', '.join(map_id(n) for n in all_new) + '};'); p.write_text(s)
    wire_mahogany(g)
    ids = {n: groups['gMapGroup_Cherrygrove'].index(n) for n in all_new}
    report = json.loads((EV / 'pack3/pack.json').read_text())
    write(EV / 'capacity.json', dict(map=NAME, primary=PRIMARY, secondary=f'gTileset_{SYM}',
                                     build='shared Johto art + Blackthorn FRLG rock, lossless (assemble.py, pack_lossless.py)',
                                     **{k: report[k] for k in ('tiles', 'tile_limit', 'primary_tiles', 'secondary_tiles', 'metatiles',
                                                                'primary_metatiles', 'secondary_metatiles')}, map_ids=ids))
    print('Installed Route 43:', ids)

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
