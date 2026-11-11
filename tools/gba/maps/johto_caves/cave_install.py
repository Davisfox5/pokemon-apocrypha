"""Install a Johto cave (cave_pack.py): its floors on one tileset pair of their own, wired to its town.

    python3 tools/gba/maps/<cave>/install.py ENGINE_CHECKOUT

New: gTileset_<cave>Primary / gTileset_<cave> and one map per floor in HGSS's own coordinates (the
whole matrix), appended to the map group; the cave's map section (Johto). Underground, Flash not
required, music MUS_CAVE_OF_ORIGIN (Dark Cave's, Ice Path's and Mt. Mortar's).

Warps are HGSS's own, index for index (the cave's zones); a warp into an interior that is not built
(cave.UNBUILT) is left out and its cell stays solid. HGSS's Strength boulders are placed; NPCs, items
and hidden items are recorded in source/hgss-events/, not placed (campaign content).

The town (another session's map): native wiring edits only, as Ice Path wired Blackthorn. The mouth
cell's metatile, used by no other cell, becomes MB_NON_ANIMATED_DOOR with its layer kept, the cell's
collision opens, one warp is appended. No pixel changes; check.py proves it.
"""
from __future__ import annotations
import json, shutil, struct, subprocess, sys
from collections import Counter
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
import cave                                          # noqa: E402
import cave_pack as P                                # noqa: E402
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art' / cave.ART
SRC, EV = ART / 'source', ART / 'evidence'
BASE, GROUP = cave.BASE, cave.GROUP
PRIMARY_SYM, SECONDARY_SYM = cave.PRIMARY_SYM, cave.SECONDARY_SYM
PRIMARY_DIR, SECONDARY_DIR = f'data/tilesets/primary/{cave.TILESET_DIR}', f'data/tilesets/secondary/{cave.TILESET_DIR}'
MAPSEC, MUSIC = cave.MAPSEC['id'], cave.MUSIC
MAPS = {s: f['name'] for s, f in cave.FLOORS.items()}
TOWN = cave.TOWN
IDS = {f['name']: f['id'] for f in cave.FLOORS.values()} | {TOWN['map']: TOWN['id']}
HGSS = {f['header']: f['name'] for f in cave.FLOORS.values()} | {TOWN['hgss']: TOWN['map']}
TOWN_DIR = f"data/tilesets/{'primary' if TOWN['metatile'] < 512 else 'secondary'}/" + \
           (TOWN['primary'] if TOWN['metatile'] < 512 else TOWN['secondary'])

def read(p): return json.loads(p.read_text())
def write(p, v): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(v, indent=2) + '\n')
def layout_id(name): return IDS[name].replace('MAP_', 'LAYOUT_', 1)
def git(g, *a): return subprocess.run(['git', '-C', str(g), *a], capture_output=True, text=True, check=True).stdout

DRAFT = [f'data/layouts/{m}' for m in MAPS.values()] + [f'data/maps/{m}' for m in MAPS.values()] + [PRIMARY_DIR, SECONDARY_DIR]
SHARED_FILES = ['data/event_scripts.s', 'data/layouts/layouts.json', 'data/maps/map_groups.json', 'src/apocrypha_map_proof.c',
                'src/data/tilesets/graphics.h', 'src/data/tilesets/headers.h', 'src/data/tilesets/metatiles.h',
                'src/data/region_map/region_map_sections.json', 'include/regions.h']
TOWN_FILES = [f"data/maps/{TOWN['map']}/map.json", f"data/layouts/{TOWN['map']}/map.bin", f'{TOWN_DIR}/metatile_attributes.bin']

def remove_draft(g):
    for paths in (DRAFT, TOWN_FILES, SHARED_FILES):
        foreign = [l for l in git(g, 'log', '--format=%s', f'{BASE}..HEAD', '--', *paths).splitlines()
                   if not l.startswith(cave.COMMIT_PREFIX)]
        if foreign:
            raise SystemExit(f'files carry other commits {foreign}: edit native source; never replay over owner edits.')
    for d in DRAFT:
        if (g / d).exists():
            shutil.rmtree(g / d)
    subprocess.run(['git', '-C', str(g), 'restore', f'--source={BASE}', '--worktree', '--'] + SHARED_FILES + TOWN_FILES, check=True)

def ordered(m):
    for k in sorted(k for k in ('region', 'build_target') if k in m):
        m[k] = m.pop(k)
    return m

def warps(name):
    """HGSS's warps for a floor, index for index; one into an unbuilt interior is left out (it is HGSS's last)."""
    side = {v: k for k, v in MAPS.items()}[name]
    ev = read(SRC / f'hgss-events/{side}.json')
    out, skipped = [], []
    for w in ev['warps']:
        if w['dest'] in cave.UNBUILT:
            skipped.append(w)
            continue
        assert not skipped, 'a left-out warp must come last, so the others keep their indices'
        dest = HGSS[w['dest']]
        did = None if dest == TOWN['map'] else w['anchor']   # the town's: filled in when its warp is appended
        out.append(dict(x=w['cell'][0], y=w['cell'][1], elevation=0, dest_map=IDS[dest], dest_warp_id=str(did)))
    return out, skipped

def town_layout(g):
    return [l for l in read(g / 'data/layouts/layouts.json')['layouts'] if l.get('name') == f"{TOWN['map']}_Layout"][0]

def wire_town(g, mb, cave_warps):
    """Native wiring edit: the mouth metatile's behaviour, the cell's collision, one warp appended."""
    (cx, cy), mid = TOWN['cell'], TOWN['metatile']
    p = g / f'{TOWN_DIR}/metatile_attributes.bin'
    at = list(struct.unpack('<%dH' % (p.stat().st_size // 2), p.read_bytes()))
    lay = town_layout(g)
    bp = g / lay['blockdata_filepath']
    a = np.frombuffer(bp.read_bytes(), '<u2').reshape(lay['height'], lay['width']).copy()
    assert int(a[cy, cx] & 1023) == mid and ((a & 1023) == mid).sum() == 1, f"{TOWN['map']} metatile {mid} is not the mouth's alone"
    k = mid if mid < 512 else mid - 512
    at[k] = (at[k] & 0xF000) | mb['MB_NON_ANIMATED_DOOR']
    p.write_bytes(struct.pack('<%dH' % len(at), *at))
    a[cy, cx] &= ~np.uint16(3 << 10)
    bp.write_bytes(a.astype('<u2').tobytes())
    mp = g / f"data/maps/{TOWN['map']}/map.json"
    m = read(mp)
    assert all((w['x'], w['y']) != (cx, cy) for w in m['warp_events'])
    side, wid = TOWN['pair']
    m['warp_events'].append(dict(x=cx, y=cy, elevation=0, dest_map=IDS[MAPS[side]], dest_warp_id=str(wid)))
    cave_warps[MAPS[side]][wid]['dest_warp_id'] = str(len(m['warp_events']) - 1)
    write(mp, ordered(m))

def register_tilesets(g):
    for sym, folder, sec in ((PRIMARY_SYM, PRIMARY_DIR, False), (SECONDARY_SYM, SECONDARY_DIR, True)):
        kind = 'secondary' if sec else 'primary'
        with (g / 'src/data/tilesets/graphics.h').open('a') as f:
            f.write(f'\n// {cave.NAME} ({kind}).\n'
                    f'const u32 gTilesetTiles_{sym}[] = INCGFX_U32("{folder}/tiles.png", ".4bpp.fastSmol");\n'
                    f'const u16 gTilesetPalettes_{sym}[][16] = {{\n' +
                    ''.join(f'    INCGFX_U16("{folder}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n')
        with (g / 'src/data/tilesets/metatiles.h').open('a') as f:
            f.write(f'\n// {cave.NAME} ({kind})\nconst u16 gMetatiles_{sym}[] = INCBIN_U16("{folder}/metatiles.bin");\n'
                    f'const u16 gMetatileAttributes_{sym}[] = INCBIN_U16("{folder}/metatile_attributes.bin");\n')
        with (g / 'src/data/tilesets/headers.h').open('a') as f:
            f.write(f'\n// {cave.NAME} ({kind})\nconst struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, '
                    f'.isSecondary = {"TRUE" if sec else "FALSE"}, .tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym}, '
                    f'.metatiles = gMetatiles_{sym}, .metatileAttributes = gMetatileAttributes_{sym}, .callback = NULL }};\n')

def register_mapsec(g):
    p = g / 'src/data/region_map/region_map_sections.json'
    d = read(p)
    d['map_sections'].append(dict(id=MAPSEC, name=cave.MAPSEC['name'], x=cave.MAPSEC['x'], y=cave.MAPSEC['y'], width=1, height=1))
    p.write_text(json.dumps(d, indent=2) + '\n')
    p = g / 'include/regions.h'; s = p.read_text()
    tail = ': return REGION_JOHTO;\n'
    i = s.rindex(tail) + len(tail)
    p.write_text(s[:i] + f'    case {MAPSEC}{tail}' + s[i:])

def main(g):
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
    layouts = read(g / 'data/layouts/layouts.json')
    groups = read(g / 'data/maps/map_groups.json')
    built = {name: warps(name) for name in MAPS.values()}
    cave_warps = {n: w for n, (w, _) in built.items()}
    wire_town(g, mb, cave_warps)
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
                     script='EventScript_StrengthBoulder', flag='0') for x, y in cave.BOULDERS.get(side, [])]
        m = dict(id=IDS[name], name=name, layout=layout_id(name), music=MUSIC, region_map_section=MAPSEC,
                 requires_flash=False, weather='WEATHER_NONE', map_type='MAP_TYPE_UNDERGROUND', allow_cycling=True,
                 allow_escaping=True, allow_running=True, show_map_name=True, battle_scene='MAP_BATTLE_SCENE_NORMAL',
                 connections=None, object_events=objs, warp_events=cave_warps[name], coord_events=[], bg_events=[],
                 build_target='emerald', region='REGION_JOHTO')
        write(g / f'data/maps/{name}/map.json', ordered(m))
        (g / f'data/maps/{name}/scripts.inc').write_text(f'{name}_MapScripts::\n    .byte 0\n')
        groups[GROUP].append(name)
        with (g / 'data/event_scripts.s').open('a') as f:
            f.write(f'\n.include "data/maps/{name}/scripts.inc"\n')
    write(g / 'data/layouts/layouts.json', layouts)
    write(g / 'data/maps/map_groups.json', groups)
    p = g / 'src/apocrypha_map_proof.c'; s = p.read_text()
    first = s.index('};', s.index('sMapProofMaps'))
    assert s[:first].rstrip().endswith(cave.PROOF_LAST), 'sMapProofMaps no longer ends where BASE left it'
    s = s[:first] + ', ' + ', '.join(IDS[n] for n in MAPS.values()) + s[first:]
    p.write_text(s)
    ids = {n: groups[GROUP].index(n) for n in list(MAPS.values()) + [TOWN['map']]}
    write(EV / 'capacity.json', dict(maps=list(MAPS.values()), primary=f'gTileset_{PRIMARY_SYM}', secondary=f'gTileset_{SECONDARY_SYM}',
                                     pack=read(EV / 'pack.json'), map_ids=ids,
                                     left_out_warps={n: sk for n, (_, sk) in built.items() if sk},
                                     town=dict(map=TOWN['map'], cell=list(TOWN['cell']), metatile=TOWN['metatile'],
                                               behavior='MB_NON_ANIMATED_DOOR', collision=0, pairs=list(TOWN['pair']))))
    print(f'Installed {cave.NAME}:', ids)
