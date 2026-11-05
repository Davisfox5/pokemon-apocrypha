"""Install Ice Path (pack.py): its four floors on one tileset pair of their own, wired to Route 44 and
Blackthorn.

    python3 tools/gba/maps/ice_path/install.py ENGINE_CHECKOUT

New: gTileset_IcePathPrimary / gTileset_IcePath, IcePath_1F (64x64), IcePath_B1F (32x64),
IcePath_B2F (64x32) and IcePath_B3F (32x32) in HGSS's own coordinates, appended to
gMapGroup_Cherrygrove; MAPSEC_ICE_PATH (Johto). Underground, Flash not required (HGSS's Ice Path
is lit), music MUS_CAVE_OF_ORIGIN (Dark Cave's).

Warps are HGSS's own, index for index (zones D39R0101-0104): the exits to Route 44 and Blackthorn,
the ladders between floors (HGSS gives most ladders two warp cells; both are kept). B1F's four
drop holes, which HGSS triggers by script, are Gen 3 MB_MT_PYRE_HOLE cells with a warp each to the
cell HGSS drops the player on, and B2F gains those four arrival warps.

Strength boulders work as FRLG's Seafoam Islands' do (field_control_avatar.c
HandleBoulderFallThroughHole): a B1F boulder pushed onto a hole falls, its own flag hides it, and
the flag in its trainer_type field is cleared, which shows its copy on B2F (HGSS's FALLEN boulders,
there ice stoppers). The B2F copies start hidden: IcePath_1F's ON_TRANSITION sets their flags once
(every way into Ice Path passes 1F first). Flags 0x4E7-0x4EF (unused in this tree) are named for
this. The B3F Rock Smash rock is placed; HGSS's NPCs, items and hidden items are recorded, not
placed (campaign content, as on the other routes).

Route 44 (owner review pending, this tool set's own) and Blackthorn (built in another session):
native wiring edits only. Each mouth cell's metatile (Route 44's 641, Blackthorn's 551, each used
by that one cell) becomes MB_NON_ANIMATED_DOOR with its layer kept, the cell's collision opens, and
one warp is appended. No pixel changes; check.py proves it.
"""
from __future__ import annotations
import json, shutil, struct, subprocess, sys
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/ice-path'
SRC, EV = ART / 'source', ART / 'evidence'
BASE = 'ca543dd961'                                  # claude/ice-path: the Mahogany and Blackthorn stacks joined
GROUP = 'gMapGroup_Cherrygrove'
PRIMARY_SYM, PRIMARY_DIR = 'IcePathPrimary', 'data/tilesets/primary/ice_path'
SECONDARY_SYM, SECONDARY_DIR = 'IcePath', 'data/tilesets/secondary/ice_path'
MAPSEC, MUSIC = 'MAPSEC_ICE_PATH', 'MUS_CAVE_OF_ORIGIN'
MAPS = {'1f': 'IcePath_1F', 'b1f': 'IcePath_B1F', 'b2f': 'IcePath_B2F', 'b3f': 'IcePath_B3F'}
IDS = {'IcePath_1F': 'MAP_ICE_PATH_1F', 'IcePath_B1F': 'MAP_ICE_PATH_B1F', 'IcePath_B2F': 'MAP_ICE_PATH_B2F',
       'IcePath_B3F': 'MAP_ICE_PATH_B3F', 'Route44': 'MAP_ROUTE44', 'BlackthornCity': 'MAP_BLACKTHORN_CITY'}
HGSS = {'MAP_ICE_PATH_1F': 'IcePath_1F', 'MAP_ICE_PATH_B1F': 'IcePath_B1F', 'MAP_ICE_PATH_B2F': 'IcePath_B2F',
        'MAP_ICE_PATH_B3F': 'IcePath_B3F', 'MAP_ROUTE_44': 'Route44', 'MAP_BLACKTHORN': 'BlackthornCity'}
MOUTHS = {  # map: (cell, metatile id, secondary folder, Ice Path warp it pairs with)
    'Route44': ((89, 9), 641, 'data/tilesets/secondary/route_44', ('IcePath_1F', 0)),
    'BlackthornCity': ((57, 16), 551, 'data/tilesets/secondary/blackthorn_city', ('IcePath_1F', 1)),
}
DROPS = [((11, 10), (12, 12)), ((10, 18), (10, 21)), ((18, 7), (20, 10)), ((19, 19), (21, 23))]   # B1F hole -> B2F cell (D39R0102 scripts)
FLAGS = {f'FLAG_HIDE_ICE_PATH_BOULDER_{i}_INIT': f'FLAG_UNUSED_0x{0x4E6 + i:03X}' for i in range(1, 5)}
FLAGS.update({f'FLAG_HIDE_ICE_PATH_BOULDER_{i}_FALLEN': f'FLAG_UNUSED_0x{0x4EA + i:03X}' for i in range(1, 5)})
FLAGS['FLAG_ICE_PATH_FALLEN_BOULDERS_HIDDEN'] = 'FLAG_UNUSED_0x4EF'
B1F_BOULDERS = [((10, 13), 1), ((13, 14), 2), ((18, 12), 3), ((25, 12), 4), ((12, 44), None)]
B2F_FALLEN = [((12, 13), 1), ((11, 21), 2), ((19, 10), 3), ((20, 22), 4)]

def read(p): return json.loads(p.read_text())
def write(p, v): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(v, indent=2) + '\n')
def layout_id(name): return IDS[name].replace('MAP_', 'LAYOUT_', 1)
def git(g, *a): return subprocess.run(['git', '-C', str(g), *a], capture_output=True, text=True, check=True).stdout

DRAFT = [f'data/layouts/{m}' for m in MAPS.values()] + [f'data/maps/{m}' for m in MAPS.values()] + [PRIMARY_DIR, SECONDARY_DIR]
SHARED_FILES = ['data/event_scripts.s', 'data/layouts/layouts.json', 'data/maps/map_groups.json', 'src/apocrypha_map_proof.c',
                'src/data/tilesets/graphics.h', 'src/data/tilesets/headers.h', 'src/data/tilesets/metatiles.h',
                'src/data/region_map/region_map_sections.json', 'include/regions.h', 'include/constants/flags.h']
ROUTE_FILES = [f for r, (_, _, d, _) in MOUTHS.items() for f in (f'data/maps/{r}/map.json', f'data/layouts/{r}/map.bin',
                                                                   f'{d}/metatile_attributes.bin')]

def remove_draft(g):
    for paths in (DRAFT, ROUTE_FILES, SHARED_FILES):
        foreign = [l for l in git(g, 'log', '--format=%s', f'{BASE}..HEAD', '--', *paths).splitlines() if not l.startswith('Ice Path')]
        if foreign:
            raise SystemExit(f'files carry other commits {foreign}: edit native source; never replay over owner edits.')
    for d in DRAFT:
        if (g / d).exists():
            shutil.rmtree(g / d)
    subprocess.run(['git', '-C', str(g), 'restore', f'--source={BASE}', '--worktree', '--'] + SHARED_FILES + ROUTE_FILES, check=True)

def ordered(m):
    for k in sorted(k for k in ('region', 'build_target') if k in m):
        m[k] = m.pop(k)
    return m

def warps(name, extra):
    """HGSS's warps for a floor, index for index, then its extras."""
    side = {v: k for k, v in MAPS.items()}[name]
    ev = read(SRC / f'hgss-events/{side}.json')
    out = []
    for w in ev['warps']:
        dest = HGSS[w['dest']]
        did = w['anchor']
        if dest in MOUTHS:
            did = None                                       # filled in when the mouth's warp is appended
        out.append(dict(x=w['cell'][0], y=w['cell'][1], elevation=0, dest_map=IDS[dest], dest_warp_id=str(did)))
    return out + extra

def wire_mouth(g, route, mb, ice_warps):
    """Native wiring edit: the mouth metatile's behaviour, the cell's collision, one warp appended."""
    (cx, cy), mid, folder, (dest, wid) = MOUTHS[route]
    p = g / f'{folder}/metatile_attributes.bin'
    at = list(struct.unpack('<%dH' % (p.stat().st_size // 2), p.read_bytes()))
    k = mid - 512
    at[k] = (at[k] & 0xF000) | mb['MB_NON_ANIMATED_DOOR']
    p.write_bytes(struct.pack('<%dH' % len(at), *at))
    lay = [l for l in read(g / 'data/layouts/layouts.json')['layouts'] if l.get('name') == f'{route}_Layout' or l.get('id') == layout_id(route)][0]
    bp = g / lay['blockdata_filepath']
    a = np.frombuffer(bp.read_bytes(), '<u2').reshape(lay['height'], lay['width']).copy()
    assert int(a[cy, cx] & 1023) == mid, (route, int(a[cy, cx] & 1023))
    assert ((a & 1023) == mid).sum() == 1, f'{route} metatile {mid} is used by more than the mouth cell'
    a[cy, cx] &= ~np.uint16(3 << 10)
    bp.write_bytes(a.astype('<u2').tobytes())
    mp = g / f'data/maps/{route}/map.json'
    m = read(mp)
    assert all((w['x'], w['y']) != (cx, cy) for w in m['warp_events']), route
    m['warp_events'].append(dict(x=cx, y=cy, elevation=0, dest_map=IDS[dest], dest_warp_id=str(wid)))
    ice_warps[dest][wid]['dest_warp_id'] = str(len(m['warp_events']) - 1)
    write(mp, ordered(m))

def register_tilesets(g):
    for sym, folder, sec in ((PRIMARY_SYM, PRIMARY_DIR, False), (SECONDARY_SYM, SECONDARY_DIR, True)):
        kind = 'secondary' if sec else 'primary'
        with (g / 'src/data/tilesets/graphics.h').open('a') as f:
            f.write(f'\n// Ice Path ({kind}).\n'
                    f'const u32 gTilesetTiles_{sym}[] = INCGFX_U32("{folder}/tiles.png", ".4bpp.fastSmol");\n'
                    f'const u16 gTilesetPalettes_{sym}[][16] = {{\n' +
                    ''.join(f'    INCGFX_U16("{folder}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n')
        with (g / 'src/data/tilesets/metatiles.h').open('a') as f:
            f.write(f'\n// Ice Path ({kind})\nconst u16 gMetatiles_{sym}[] = INCBIN_U16("{folder}/metatiles.bin");\n'
                    f'const u16 gMetatileAttributes_{sym}[] = INCBIN_U16("{folder}/metatile_attributes.bin");\n')
        with (g / 'src/data/tilesets/headers.h').open('a') as f:
            f.write(f'\n// Ice Path ({kind})\nconst struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, '
                    f'.isSecondary = {"TRUE" if sec else "FALSE"}, .tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym}, '
                    f'.metatiles = gMetatiles_{sym}, .metatileAttributes = gMetatileAttributes_{sym}, .callback = NULL }};\n')

def register_mapsec(g):
    p = g / 'src/data/region_map/region_map_sections.json'
    d = read(p)
    d['map_sections'].append(dict(id=MAPSEC, name='ICE PATH', x=5, y=3, width=1, height=1))
    p.write_text(json.dumps(d, indent=2) + '\n')
    p = g / 'include/regions.h'; s = p.read_text()
    anchor = '    case MAPSEC_DARK_CAVE: return REGION_JOHTO;\n'
    assert anchor in s
    p.write_text(s.replace(anchor, anchor + f'    case {MAPSEC}: return REGION_JOHTO;\n'))

def register_flags(g):
    p = g / 'include/constants/flags.h'; s = p.read_text()
    block = '\n// Ice Path (tools/gba/maps/ice_path/install.py): Strength boulders through B1F\'s holes to B2F\n' + \
            ''.join(f'#define {k} {v}\n' for k, v in FLAGS.items())
    anchor = '#endif // GUARD_CONSTANTS_FLAGS_H'
    assert anchor in s and 'ICE_PATH_BOULDER' not in s
    p.write_text(s.replace(anchor, block + '\n' + anchor))

def main(g):
    sys.path.insert(0, str(HERE))
    import pack as P
    sys.path.insert(0, str(HERE.parent / 'dark_cave'))
    from importlib.util import spec_from_file_location, module_from_spec
    spec = spec_from_file_location('dark_cave_install', HERE.parent / 'dark_cave/install.py')
    DC = module_from_spec(spec); spec.loader.exec_module(DC)
    remove_draft(g)
    mb = P.behaviors(g)
    z = np.load(SRC / 'pack/pack.npz')
    pats, pal, metas = z['patterns'], z['palettes'], z['metatiles']
    DC.write_tileset(g / PRIMARY_DIR, pats[:512], pal, metas[:512])
    DC.write_tileset(g / SECONDARY_DIR, pats[512:], pal, metas[512:])
    register_tilesets(g)
    register_mapsec(g)
    register_flags(g)
    layouts = read(g / 'data/layouts/layouts.json')
    groups = read(g / 'data/maps/map_groups.json')
    b1f_holes = len(read(SRC / 'hgss-events/b1f.json')['warps'])
    b2f_arrivals = len(read(SRC / 'hgss-events/b2f.json')['warps'])
    ice_warps = {
        'IcePath_1F': warps('IcePath_1F', []),
        'IcePath_B1F': warps('IcePath_B1F', [dict(x=hx, y=hy, elevation=0, dest_map=IDS['IcePath_B2F'], dest_warp_id=str(b2f_arrivals + i))
                                             for i, ((hx, hy), _) in enumerate(DROPS)]),
        'IcePath_B2F': warps('IcePath_B2F', [dict(x=ax, y=ay, elevation=0, dest_map=IDS['IcePath_B1F'], dest_warp_id=str(b1f_holes + i))
                                             for i, (_, (ax, ay)) in enumerate(DROPS)]),
        'IcePath_B3F': warps('IcePath_B3F', []),
    }
    for route in MOUTHS:
        wire_mouth(g, route, mb, ice_warps)
    for side, name in MAPS.items():
        key = side
        w, h = P.SIZE[side]
        grid, coll, elev = z[f'grid_{key}'], z[f'collision_{key}'], z[f'elevation_{key}']
        trav = read(SRC / f'pack/traversal-{side}.json')
        ring = [c for c in trav if c.get('void')] or [c for c in trav if c['foot'] == 'blocked']
        border = Counter(int(grid[c['y'], c['x']]) for c in ring).most_common(1)[0][0]
        ld = g / f'data/layouts/{name}'
        ld.mkdir(parents=True)
        cells = grid.astype(np.uint32) | (coll.astype(np.uint32) << 10) | (elev.astype(np.uint32) << 12)
        (ld / 'map.bin').write_bytes(cells.astype('<u2').tobytes())
        (ld / 'border.bin').write_bytes(struct.pack('<4H', *[border] * 4))
        layouts['layouts'].append(dict(id=layout_id(name), name=f'{name}_Layout', width=w, height=h,
                                       primary_tileset=f'gTileset_{PRIMARY_SYM}', secondary_tileset=f'gTileset_{SECONDARY_SYM}',
                                       border_filepath=f'data/layouts/{name}/border.bin',
                                       blockdata_filepath=f'data/layouts/{name}/map.bin', layout_version='emerald'))
        obj = lambda gfx, x, y, script, flag, ttype='TRAINER_TYPE_NONE': dict(
            graphics_id=gfx, x=x, y=y, elevation=3, movement_type='MOVEMENT_TYPE_FACE_DOWN', movement_range_x=0, movement_range_y=0,
            trainer_type=ttype, trainer_sight_or_berry_tree_id='0', script=script, flag=flag)
        objs, script = [], [f'{name}_MapScripts::']
        if name == 'IcePath_B1F':
            objs = [obj('OBJ_EVENT_GFX_PUSHABLE_BOULDER', x, y, 'EventScript_StrengthBoulder',
                        f'FLAG_HIDE_ICE_PATH_BOULDER_{i}_INIT' if i else '0',
                        f'FLAG_HIDE_ICE_PATH_BOULDER_{i}_FALLEN' if i else 'TRAINER_TYPE_NONE') for (x, y), i in B1F_BOULDERS]
        elif name == 'IcePath_B2F':
            objs = [obj('OBJ_EVENT_GFX_PUSHABLE_BOULDER', x, y, 'IcePath_B2F_EventScript_SunkenBoulder',
                        f'FLAG_HIDE_ICE_PATH_BOULDER_{i}_FALLEN') for (x, y), i in B2F_FALLEN]
        elif name == 'IcePath_B3F':
            objs = [obj('OBJ_EVENT_GFX_BREAKABLE_ROCK', 10, 12, 'EventScript_RockSmash', 'FLAG_TEMP_11')]
        if name == 'IcePath_1F':
            script += ['    map_script MAP_SCRIPT_ON_TRANSITION, IcePath_1F_OnTransition', '    .byte 0', '',
                       'IcePath_1F_OnTransition:', '    goto_if_set FLAG_ICE_PATH_FALLEN_BOULDERS_HIDDEN, IcePath_1F_EventScript_End'] + \
                      [f'    setflag FLAG_HIDE_ICE_PATH_BOULDER_{i}_FALLEN' for i in range(1, 5)] + \
                      ['    setflag FLAG_ICE_PATH_FALLEN_BOULDERS_HIDDEN', 'IcePath_1F_EventScript_End:', '    end']
        else:
            script.append('    .byte 0')
        if name == 'IcePath_B2F':
            script += ['', 'IcePath_B2F_EventScript_SunkenBoulder::', '    msgbox IcePath_B2F_Text_SunkenBoulder, MSGBOX_NPC', '    end', '',
                       'IcePath_B2F_Text_SunkenBoulder:', '    .string "It has sunk in and cannot be moved.$"']
        m = dict(id=IDS[name], name=name, layout=layout_id(name), music=MUSIC, region_map_section=MAPSEC,
                 requires_flash=False, weather='WEATHER_NONE', map_type='MAP_TYPE_UNDERGROUND', allow_cycling=True,
                 allow_escaping=True, allow_running=True, show_map_name=True, battle_scene='MAP_BATTLE_SCENE_NORMAL',
                 connections=None, object_events=objs, warp_events=ice_warps[name], coord_events=[], bg_events=[],
                 build_target='emerald', region='REGION_JOHTO')
        write(g / f'data/maps/{name}/map.json', ordered(m))
        (g / f'data/maps/{name}/scripts.inc').write_text('\n'.join(script) + '\n')
        groups[GROUP].append(name)
        with (g / 'data/event_scripts.s').open('a') as f:
            f.write(f'\n.include "data/maps/{name}/scripts.inc"\n')
    write(g / 'data/layouts/layouts.json', layouts)
    write(g / 'data/maps/map_groups.json', groups)
    p = g / 'src/apocrypha_map_proof.c'; s = p.read_text()
    anchor = 'MAP_DARK_CAVE_UNDERWATER'
    assert anchor in s
    first = s.index('};', s.index('sMapProofMaps'))
    s = s[:first] + ', ' + ', '.join(IDS[n] for n in MAPS.values()) + s[first:]
    p.write_text(s)
    write(EV / 'capacity.json', dict(maps=list(MAPS.values()), primary=f'gTileset_{PRIMARY_SYM}', secondary=f'gTileset_{SECONDARY_SYM}',
                                     pack=read(EV / 'pack.json'), map_ids={n: groups[GROUP].index(n) for n in MAPS.values()},
                                     flags=FLAGS, mouths={r: dict(cell=list(c), metatile=mid, behavior='MB_NON_ANIMATED_DOOR', collision=0)
                                                          for r, (c, mid, _, _) in MOUTHS.items()}))
    print('Installed Ice Path:', {n: groups[GROUP].index(n) for n in MAPS.values()})

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
