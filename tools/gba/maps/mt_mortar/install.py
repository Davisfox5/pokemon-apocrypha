"""Install Mt. Mortar (pack.py): its four floors on one tileset pair of their own, wired to Route 42.

    python3 tools/gba/maps/mt_mortar/install.py ENGINE_CHECKOUT

New: gTileset_MtMortarPrimary / gTileset_MtMortar, MtMortar_1F_Entrance (96x64), MtMortar_1F_Back
(75x88: HGSS's 96x96 is over Gen 3's map size, so its void margin is cropped, pack.CROP), MtMortar_2F
(64x64) and MtMortar_B1F (64x96) in HGSS's own coordinates (1F back offset by (16, 5)), appended to
gMapGroup_Cherrygrove; MAPSEC_MT_MORTAR (Johto). Underground, Flash not required (HGSS's Mt. Mortar
is lit), music MUS_CAVE_OF_ORIGIN (Dark Cave's and Ice Path's).

Warps are HGSS's own, index for index (zones D38R0101-0104): the four mouths to Route 42, the holes
and ladders between floors (HGSS gives an up-ladder two warp cells; both are kept). HGSS's two
Strength boulders are placed; its NPCs (Kiyo, the Mortar trainers), items and hidden items are
recorded, not placed (campaign content, as on the other routes).

The 1F falls are Emerald's own animated waterfall (general's metatiles 179/185/193, its four frames
copied in by InitTilesetAnim_MtMortar, a tileset callback added to tileset_anims.c), in cave water.

Route 42 (owner review pending, this tool set's own): native wiring edits only. Its three south
mouths share one metatile (619) and the north mouth has its own (526), each used by no other cell;
they become MB_NON_ANIMATED_DOOR with their layer kept, the cells' collision opens, and four warps
are appended. No pixel changes; check.py proves it. Route 42's Rock Climb wall stays as it is.
"""
from __future__ import annotations
import json, shutil, struct, subprocess, sys
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pack as _P                                    # noqa: E402  (OFFSET: 1F back's crop)
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/mt-mortar'
SRC, EV = ART / 'source', ART / 'evidence'
BASE = '570663a929'                                  # claude/ice-path's head: Mt. Mortar stacks on Ice Path
GROUP = 'gMapGroup_Cherrygrove'
PRIMARY_SYM, PRIMARY_DIR = 'MtMortarPrimary', 'data/tilesets/primary/mt_mortar'
SECONDARY_SYM, SECONDARY_DIR = 'MtMortar', 'data/tilesets/secondary/mt_mortar'
MAPSEC, MUSIC = 'MAPSEC_MT_MORTAR', 'MUS_CAVE_OF_ORIGIN'
MAPS = {'1f-entrance': 'MtMortar_1F_Entrance', '1f-back': 'MtMortar_1F_Back', '2f': 'MtMortar_2F', 'b1f': 'MtMortar_B1F'}
IDS = {'MtMortar_1F_Entrance': 'MAP_MT_MORTAR_1F_ENTRANCE', 'MtMortar_1F_Back': 'MAP_MT_MORTAR_1F_BACK',
       'MtMortar_2F': 'MAP_MT_MORTAR_2F', 'MtMortar_B1F': 'MAP_MT_MORTAR_B1F', 'Route42': 'MAP_ROUTE42'}
HGSS = {'MAP_MOUNT_MORTAR_1F_ENTRANCE': 'MtMortar_1F_Entrance', 'MAP_MOUNT_MORTAR_1F_BACK': 'MtMortar_1F_Back',
        'MAP_MOUNT_MORTAR_2F': 'MtMortar_2F', 'MAP_MOUNT_MORTAR_B1F': 'MtMortar_B1F', 'MAP_ROUTE_42': 'Route42'}
ROUTE = 'Route42'
ROUTE_DIR = 'data/tilesets/secondary/route_42'
MOUTHS = {  # Route 42 cell: (metatile id, Mt. Mortar warp it pairs with); HGSS's Route 42 warps 2-5
    (20, 11): (619, ('MtMortar_1F_Entrance', 0)), (48, 15): (619, ('MtMortar_1F_Entrance', 1)),
    (50, 4): (526, ('MtMortar_1F_Entrance', 2)), (77, 11): (619, ('MtMortar_1F_Entrance', 3)),
}
BOULDERS = {'MtMortar_1F_Back': [(51, 72)], 'MtMortar_B1F': [(26, 38)]}   # HGSS's SPRITE_ROCK objects: Strength boulders

def read(p): return json.loads(p.read_text())
def write(p, v): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(v, indent=2) + '\n')
def layout_id(name): return IDS[name].replace('MAP_', 'LAYOUT_', 1)
def git(g, *a): return subprocess.run(['git', '-C', str(g), *a], capture_output=True, text=True, check=True).stdout

DRAFT = [f'data/layouts/{m}' for m in MAPS.values()] + [f'data/maps/{m}' for m in MAPS.values()] + [PRIMARY_DIR, SECONDARY_DIR]
SHARED_FILES = ['data/event_scripts.s', 'data/layouts/layouts.json', 'data/maps/map_groups.json', 'src/apocrypha_map_proof.c',
                'src/data/tilesets/graphics.h', 'src/data/tilesets/headers.h', 'src/data/tilesets/metatiles.h',
                'src/data/region_map/region_map_sections.json', 'include/regions.h',
                'src/tileset_anims.c', 'include/tileset_anims.h']
ROUTE_FILES = [f'data/maps/{ROUTE}/map.json', f'data/layouts/{ROUTE}/map.bin', f'{ROUTE_DIR}/metatile_attributes.bin']

def remove_draft(g):
    for paths in (DRAFT, ROUTE_FILES, SHARED_FILES):
        foreign = [l for l in git(g, 'log', '--format=%s', f'{BASE}..HEAD', '--', *paths).splitlines() if not l.startswith('Mt. Mortar')]
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
    ox, oy = _P.OFFSET[side]
    ev = read(SRC / f'hgss-events/{side}.json')
    out = []
    for w in ev['warps']:
        dest = HGSS[w['dest']]
        did = w['anchor']
        if dest == ROUTE:
            did = None                                       # filled in when the mouth's warp is appended
        out.append(dict(x=w['cell'][0] - ox, y=w['cell'][1] - oy, elevation=0, dest_map=IDS[dest], dest_warp_id=str(did)))
    return out + extra

def wire_route(g, mb, mm_warps):
    """Native wiring edit on Route 42: the mouth metatiles' behaviour, the mouth cells' collision, four warps appended."""
    p = g / f'{ROUTE_DIR}/metatile_attributes.bin'
    at = list(struct.unpack('<%dH' % (p.stat().st_size // 2), p.read_bytes()))
    lay = [l for l in read(g / 'data/layouts/layouts.json')['layouts'] if l.get('name') == f'{ROUTE}_Layout'][0]
    bp = g / lay['blockdata_filepath']
    a = np.frombuffer(bp.read_bytes(), '<u2').reshape(lay['height'], lay['width']).copy()
    for mid in {mid for mid, _ in MOUTHS.values()}:
        users = {(int(x), int(y)) for y, x in np.argwhere((a & 1023) == mid)}
        assert users == {c for c, (m_, _) in MOUTHS.items() if m_ == mid}, (mid, sorted(users))
        at[mid - 512] = (at[mid - 512] & 0xF000) | mb['MB_NON_ANIMATED_DOOR']
    p.write_bytes(struct.pack('<%dH' % len(at), *at))
    mp = g / f'data/maps/{ROUTE}/map.json'
    m = read(mp)
    for (cx, cy), (mid, (dest, wid)) in MOUTHS.items():
        assert int(a[cy, cx] & 1023) == mid and all((w['x'], w['y']) != (cx, cy) for w in m['warp_events'])
        a[cy, cx] &= ~np.uint16(3 << 10)
        m['warp_events'].append(dict(x=cx, y=cy, elevation=0, dest_map=IDS[dest], dest_warp_id=str(wid)))
        mm_warps[dest][wid]['dest_warp_id'] = str(len(m['warp_events']) - 1)
    bp.write_bytes(a.astype('<u2').tobytes())
    write(mp, ordered(m))

def register_tilesets(g):
    for sym, folder, sec in ((PRIMARY_SYM, PRIMARY_DIR, False), (SECONDARY_SYM, SECONDARY_DIR, True)):
        kind = 'secondary' if sec else 'primary'
        with (g / 'src/data/tilesets/graphics.h').open('a') as f:
            f.write(f'\n// Mt. Mortar ({kind}).\n'
                    f'const u32 gTilesetTiles_{sym}[] = INCGFX_U32("{folder}/tiles.png", ".4bpp.fastSmol");\n'
                    f'const u16 gTilesetPalettes_{sym}[][16] = {{\n' +
                    ''.join(f'    INCGFX_U16("{folder}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n')
        with (g / 'src/data/tilesets/metatiles.h').open('a') as f:
            f.write(f'\n// Mt. Mortar ({kind})\nconst u16 gMetatiles_{sym}[] = INCBIN_U16("{folder}/metatiles.bin");\n'
                    f'const u16 gMetatileAttributes_{sym}[] = INCBIN_U16("{folder}/metatile_attributes.bin");\n')
        with (g / 'src/data/tilesets/headers.h').open('a') as f:
            f.write(f'\n// Mt. Mortar ({kind})\nconst struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, '
                    f'.isSecondary = {"TRUE" if sec else "FALSE"}, .tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym}, '
                    f'.metatiles = gMetatiles_{sym}, .metatileAttributes = gMetatileAttributes_{sym}, '
                    f'.callback = {"NULL" if sec else "InitTilesetAnim_MtMortar"} }};\n')

def register_waterfall(g, pack):
    """The falls' animation, Emerald's own (tileset_anims.c TilesetAnim_General's waterfall): its four
    frames, reindexed to the palette bank pack.py gave them, copied into primary tiles WF_TILE.. every
    16 frames."""
    wf = pack['waterfall']
    d = g / PRIMARY_DIR / 'anim/waterfall'
    d.mkdir(parents=True, exist_ok=True)
    for i in range(wf['frames']):
        shutil.copy(SRC / f'pack/waterfall-{i}.png', d / f'{i}.png')
    p = g / 'include/tileset_anims.h'; s = p.read_text()
    anchor = 'void InitTilesetAnim_General(void);\n'
    assert anchor in s and 'MtMortar' not in s
    p.write_text(s.replace(anchor, anchor + 'void InitTilesetAnim_MtMortar(void);\n'))
    with (g / 'src/tileset_anims.c').open('a') as f:
        f.write('\n// Mt. Mortar (tools/gba/maps/mt_mortar/install.py): the falls, Emerald\'s waterfall in cave water\n' +
                ''.join(f'const u16 gTilesetAnims_MtMortar_Waterfall_Frame{i}[] = INCGFX_U16("{PRIMARY_DIR}/anim/waterfall/{i}.png", ".4bpp");\n'
                        for i in range(wf['frames'])) +
                'const u16 *const gTilesetAnims_MtMortar_Waterfall[] = {\n' +
                ''.join(f'    gTilesetAnims_MtMortar_Waterfall_Frame{i},\n' for i in range(wf['frames'])) + '};\n\n'
                'static void TilesetAnim_MtMortar(u16 timer)\n{\n'
                '    if (timer % 16 == 2)\n'
                f'        AppendTilesetAnimToBuffer(gTilesetAnims_MtMortar_Waterfall[(timer >> 4) % ARRAY_COUNT(gTilesetAnims_MtMortar_Waterfall)], '
                f'(u16 *)(BG_VRAM + TILE_OFFSET_4BPP({wf["tiles"][0]})), {len(wf["tiles"])} * TILE_SIZE_4BPP);\n}}\n\n'
                'void InitTilesetAnim_MtMortar(void)\n{\n    sPrimaryTilesetAnimCounter = 0;\n'
                '    sPrimaryTilesetAnimCounterMax = 256;\n    sPrimaryTilesetAnimCallback = TilesetAnim_MtMortar;\n}\n')

def register_mapsec(g):
    p = g / 'src/data/region_map/region_map_sections.json'
    d = read(p)
    d['map_sections'].append(dict(id=MAPSEC, name='MT. MORTAR', x=5, y=4, width=1, height=1))
    p.write_text(json.dumps(d, indent=2) + '\n')
    p = g / 'include/regions.h'; s = p.read_text()
    anchor = '    case MAPSEC_ICE_PATH: return REGION_JOHTO;\n'
    assert anchor in s
    p.write_text(s.replace(anchor, anchor + f'    case {MAPSEC}: return REGION_JOHTO;\n'))

def main(g):
    sys.path.insert(0, str(HERE))
    import pack as P
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
    register_waterfall(g, read(EV / 'pack.json'))
    register_mapsec(g)
    layouts = read(g / 'data/layouts/layouts.json')
    groups = read(g / 'data/maps/map_groups.json')
    mm_warps = {name: warps(name, []) for name in MAPS.values()}
    wire_route(g, mb, mm_warps)
    for side, name in MAPS.items():
        key = side.replace('-', '_')
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
        objs = [dict(graphics_id='OBJ_EVENT_GFX_PUSHABLE_BOULDER', x=x, y=y, elevation=3, movement_type='MOVEMENT_TYPE_FACE_DOWN',
                     movement_range_x=0, movement_range_y=0, trainer_type='TRAINER_TYPE_NONE', trainer_sight_or_berry_tree_id='0',
                     script='EventScript_StrengthBoulder', flag='0')
                for x, y in ((bx - P.OFFSET[side][0], by - P.OFFSET[side][1]) for bx, by in BOULDERS.get(name, []))]
        m = dict(id=IDS[name], name=name, layout=layout_id(name), music=MUSIC, region_map_section=MAPSEC,
                 requires_flash=False, weather='WEATHER_NONE', map_type='MAP_TYPE_UNDERGROUND', allow_cycling=True,
                 allow_escaping=True, allow_running=True, show_map_name=True, battle_scene='MAP_BATTLE_SCENE_NORMAL',
                 connections=None, object_events=objs, warp_events=mm_warps[name], coord_events=[], bg_events=[],
                 build_target='emerald', region='REGION_JOHTO')
        write(g / f'data/maps/{name}/map.json', ordered(m))
        (g / f'data/maps/{name}/scripts.inc').write_text(f'{name}_MapScripts::\n    .byte 0\n')
        groups[GROUP].append(name)
        with (g / 'data/event_scripts.s').open('a') as f:
            f.write(f'\n.include "data/maps/{name}/scripts.inc"\n')
    write(g / 'data/layouts/layouts.json', layouts)
    write(g / 'data/maps/map_groups.json', groups)
    p = g / 'src/apocrypha_map_proof.c'; s = p.read_text()
    assert 'MAP_ICE_PATH_B3F' in s
    first = s.index('};', s.index('sMapProofMaps'))
    s = s[:first] + ', ' + ', '.join(IDS[n] for n in MAPS.values()) + s[first:]
    p.write_text(s)
    write(EV / 'capacity.json', dict(maps=list(MAPS.values()), primary=f'gTileset_{PRIMARY_SYM}', secondary=f'gTileset_{SECONDARY_SYM}',
                                     pack=read(EV / 'pack.json'), map_ids={n: groups[GROUP].index(n) for n in MAPS.values()},
                                     mouths={f'{c[0]},{c[1]}': dict(metatile=mid, behavior='MB_NON_ANIMATED_DOOR', collision=0, pairs=list(d))
                                             for c, (mid, d) in MOUTHS.items()}))
    print('Installed Mt. Mortar:', {n: groups[GROUP].index(n) for n in MAPS.values()})

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
