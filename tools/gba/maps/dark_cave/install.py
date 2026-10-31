"""Install Dark Cave (pack.py): its two maps on one tileset pair of their own, wired to Routes 45 and 46.

    python3 tools/gba/maps/dark_cave/install.py ENGINE_CHECKOUT

New: gTileset_DarkCavePrimary / gTileset_DarkCave (pack.py's 1,008 tiles, 13 banks, 809 metatiles),
DarkCaveRoute45Side and DarkCaveRoute31Side (64 x 64 each, HGSS coordinates), appended to
gMapGroup_Cherrygrove with Routes 45 and 46. Both are MAP_TYPE_UNDERGROUND and need Flash, as in
HGSS, under the existing MAPSEC_DARK_CAVE.

Warps, as HGSS pairs them:
    Route 45 (10,6) mouth          <-> Route 45 side (60,4) exit
    Route 45 side (6,57) exit      <-> Route 31 side (26,4) hole
    Route 31 side (55,56) exit     <-> Route 46 (20,9) mouth
The Route 31 side's exit to Route 31 (5,26) stays solid: Route 31 and DarkCaveEntrance are another
agent's maps.

Routes 45 and 46 are owner-accepted and locked: their only changes are native wiring edits. Each
mouth cell's metatile (Route 45's 523, Route 46's 538, each used by that one cell) becomes
MB_NON_ANIMATED_DOOR with its layer kept, the cell's collision opens, and one warp event is added.
No pixel changes. The installer refuses if a file it touches carries a commit since BASE that is
not this tool's, so it never replays over owner edits.

Route 31 side HM obstacles are Gen 3 objects at HGSS's cells: four Rock Smash rocks and one
Strength boulder. The NPC, item balls and hidden items are recorded in source/hgss-events, not
placed (campaign content, as on the other routes).
"""
from __future__ import annotations
import json, shutil, struct, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/dark-cave'
SRC, EV = ART / 'source', ART / 'evidence'
W = H = 64
BASE = 'origin/claude/route-46'
GROUP = 'gMapGroup_Cherrygrove'
PRIMARY_SYM, PRIMARY_DIR = 'DarkCavePrimary', 'data/tilesets/primary/dark_cave'
SECONDARY_SYM, SECONDARY_DIR = 'DarkCave', 'data/tilesets/secondary/dark_cave'
MAPSEC, MUSIC = 'MAPSEC_DARK_CAVE', 'MUS_CAVE_OF_ORIGIN'       # DarkCaveEntrance's music
MAPS = {'route45-side': 'DarkCaveRoute45Side', 'route31-side': 'DarkCaveRoute31Side'}
MOUTHS = {  # route: (cell, metatile id, secondary folder)
    'Route45': ((10, 6), 523, 'data/tilesets/secondary/route_45'),
    'Route46': ((20, 9), 538, 'data/tilesets/secondary/route_46'),
}
WARPS = {   # map: [(cell, dest map, dest warp id)]
    'DarkCaveRoute45Side': [((6, 57), 'DarkCaveRoute31Side', 0), ((60, 4), 'Route45', 0)],
    'DarkCaveRoute31Side': [((26, 4), 'DarkCaveRoute45Side', 0), ((55, 56), 'Route46', 0)],
    'Route45': [((10, 6), 'DarkCaveRoute45Side', 1)],
    'Route46': [((20, 9), 'DarkCaveRoute31Side', 1)],
}
OBJECTS = {  # HGSS Route 31 side field obstacles (zone 169_D42R0102)
    'DarkCaveRoute31Side': [
        ('OBJ_EVENT_GFX_BREAKABLE_ROCK', (17, 17), 'EventScript_RockSmash', 'FLAG_TEMP_11'),
        ('OBJ_EVENT_GFX_BREAKABLE_ROCK', (40, 13), 'EventScript_RockSmash', 'FLAG_TEMP_12'),
        ('OBJ_EVENT_GFX_BREAKABLE_ROCK', (55, 53), 'EventScript_RockSmash', 'FLAG_TEMP_13'),
        ('OBJ_EVENT_GFX_BREAKABLE_ROCK', (17, 18), 'EventScript_RockSmash', 'FLAG_TEMP_14'),
        ('OBJ_EVENT_GFX_PUSHABLE_BOULDER', (28, 20), 'EventScript_StrengthBoulder', '0'),
    ],
}

def read(p): return json.loads(p.read_text())
def write(p, v): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(v, indent=2) + '\n')
def map_id(name): return 'MAP_' + ''.join('_' + c if c.isupper() and i else c for i, c in enumerate(name)).upper()
def layout_id(name): return map_id(name).replace('MAP_', 'LAYOUT_', 1)
def jasc(colors): return 'JASC-PAL\n0100\n16\n' + '\n'.join(' '.join(map(str, c)) for c in colors) + '\n'
def git(g, *a): return subprocess.run(['git', '-C', str(g), *a], capture_output=True, text=True, check=True).stdout

DRAFT = [f'data/layouts/{m}' for m in MAPS.values()] + [f'data/maps/{m}' for m in MAPS.values()] + [PRIMARY_DIR, SECONDARY_DIR]
SHARED_FILES = ['data/event_scripts.s', 'data/layouts/layouts.json', 'data/maps/map_groups.json',
                'src/apocrypha_map_proof.c', 'src/data/tilesets/graphics.h', 'src/data/tilesets/headers.h',
                'src/data/tilesets/metatiles.h']
ROUTE_FILES = [f for r, (_, _, d) in MOUTHS.items() for f in (f'data/maps/{r}/map.json', f'data/layouts/{r}/map.bin',
                                                               f'{d}/metatile_attributes.bin')]

def remove_draft(g):
    for paths in (DRAFT, ROUTE_FILES):
        foreign = [l for l in git(g, 'log', '--format=%s', f'{BASE}..HEAD', '--', *paths).splitlines() if not l.startswith('Dark Cave')]
        if foreign:
            raise SystemExit(f'files carry other commits {foreign}: edit native source; never replay over owner edits.')
    for d in DRAFT:
        if (g / d).exists():
            shutil.rmtree(g / d)
    subprocess.run(['git', '-C', str(g), 'restore', f'--source={BASE}', '--worktree', '--'] + SHARED_FILES + ROUTE_FILES, check=True)

def write_tileset(d, pats, pal, metas):
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

def register(g):
    for sym, folder, sec in ((PRIMARY_SYM, PRIMARY_DIR, False), (SECONDARY_SYM, SECONDARY_DIR, True)):
        kind = 'secondary' if sec else 'primary'
        with (g / 'src/data/tilesets/graphics.h').open('a') as f:
            f.write(f'\n// Dark Cave ({kind}).\n'
                    f'const u32 gTilesetTiles_{sym}[] = INCGFX_U32("{folder}/tiles.png", ".4bpp.fastSmol");\n'
                    f'const u16 gTilesetPalettes_{sym}[][16] = {{\n' +
                    ''.join(f'    INCGFX_U16("{folder}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n')
        with (g / 'src/data/tilesets/metatiles.h').open('a') as f:
            f.write(f'\n// Dark Cave ({kind})\nconst u16 gMetatiles_{sym}[] = INCBIN_U16("{folder}/metatiles.bin");\n'
                    f'const u16 gMetatileAttributes_{sym}[] = INCBIN_U16("{folder}/metatile_attributes.bin");\n')
        with (g / 'src/data/tilesets/headers.h').open('a') as f:
            f.write(f'\n// Dark Cave ({kind})\nconst struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, '
                    f'.isSecondary = {"TRUE" if sec else "FALSE"}, .tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym}, '
                    f'.metatiles = gMetatiles_{sym}, .metatileAttributes = gMetatileAttributes_{sym}, .callback = NULL }};\n')

def ordered(m):
    for k in sorted(k for k in ('region', 'build_target') if k in m):  # Porymap's key order
        m[k] = m.pop(k)
    return m

def warp_events(name):
    return [dict(x=x, y=y, elevation=0, dest_map=map_id(dest), dest_warp_id=str(i)) for (x, y), dest, i in WARPS[name]]

def wire_mouth(g, route, mb):
    """Native wiring edit on a locked route: the mouth metatile's behaviour, the cell's collision, one warp."""
    (cx, cy), mid, folder = MOUTHS[route]
    p = g / f'{folder}/metatile_attributes.bin'
    at = list(struct.unpack('<%dH' % (p.stat().st_size // 2), p.read_bytes()))
    k = mid - 512
    at[k] = (at[k] & 0xF000) | mb['MB_NON_ANIMATED_DOOR']
    p.write_bytes(struct.pack('<%dH' % len(at), *at))
    lay = [l for l in read(g / 'data/layouts/layouts.json')['layouts'] if l['name'] == f'{route}_Layout'][0]
    bp = g / lay['blockdata_filepath']
    a = np.frombuffer(bp.read_bytes(), '<u2').reshape(lay['height'], lay['width']).copy()
    assert int(a[cy, cx] & 1023) == mid, (route, int(a[cy, cx] & 1023))
    assert ((a & 1023) == mid).sum() == 1, f'{route} metatile {mid} is used by more than the mouth cell'
    a[cy, cx] &= ~np.uint16(3 << 10)
    bp.write_bytes(a.astype('<u2').tobytes())
    mp = g / f'data/maps/{route}/map.json'
    m = read(mp)
    assert m['warp_events'] == [], (route, m['warp_events'])
    m['warp_events'] = warp_events(route)
    write(mp, ordered(m))

def main(g):
    sys.path.insert(0, str(HERE))
    import pack as P
    remove_draft(g)
    mb = P.behaviors(g)
    z = np.load(SRC / 'pack/pack.npz')
    pats, pal, metas = z['patterns'], z['palettes'], z['metatiles']
    write_tileset(g / PRIMARY_DIR, pats[:512], pal, metas[:512])
    write_tileset(g / SECONDARY_DIR, pats[512:], pal, metas[512:])
    register(g)
    layouts = read(g / 'data/layouts/layouts.json')
    groups = read(g / 'data/maps/map_groups.json')
    for side, name in MAPS.items():
        key = side.replace('-', '_')
        grid, coll, elev = z[f'grid_{key}'], z[f'collision_{key}'], z[f'elevation_{key}']
        # the border block: the metatile of this map's solid black void cells (beyond the cave, as in HGSS)
        img = np.array(Image.open(EV / f'{side}-native.png').convert('RGB')).reshape(H, 16, W, 16, 3)
        black = [(y, x) for y in range(H) for x in range(W) if not img[y, :, x].any()]
        ids = {int(grid[y, x]) for y, x in black}
        assert len(ids) == 1, ('black void cells use more than one metatile', ids)
        border = ids.pop()
        ld = g / f'data/layouts/{name}'
        ld.mkdir(parents=True)
        cells = grid.astype(np.uint32) | (coll.astype(np.uint32) << 10) | (elev.astype(np.uint32) << 12)
        (ld / 'map.bin').write_bytes(cells.astype('<u2').tobytes())
        (ld / 'border.bin').write_bytes(struct.pack('<4H', *[border] * 4))
        layouts['layouts'].append(dict(id=layout_id(name), name=f'{name}_Layout', width=W, height=H,
                                       primary_tileset=f'gTileset_{PRIMARY_SYM}', secondary_tileset=f'gTileset_{SECONDARY_SYM}',
                                       border_filepath=f'data/layouts/{name}/border.bin',
                                       blockdata_filepath=f'data/layouts/{name}/map.bin', layout_version='emerald'))
        objs = [dict(graphics_id=gfx, x=x, y=y, elevation=3, movement_type='MOVEMENT_TYPE_LOOK_AROUND',
                     movement_range_x=0, movement_range_y=0, trainer_type='TRAINER_TYPE_NONE',
                     trainer_sight_or_berry_tree_id='0', script=script, flag=flag)
                for gfx, (x, y), script, flag in OBJECTS.get(name, [])]
        m = dict(id=map_id(name), name=name, layout=layout_id(name), music=MUSIC, region_map_section=MAPSEC,
                 requires_flash=True, weather='WEATHER_NONE', map_type='MAP_TYPE_UNDERGROUND', allow_cycling=True,
                 allow_escaping=True, allow_running=True, show_map_name=True, battle_scene='MAP_BATTLE_SCENE_NORMAL',
                 connections=None, object_events=objs, warp_events=warp_events(name), coord_events=[], bg_events=[],
                 build_target='emerald', region='REGION_JOHTO')
        write(g / f'data/maps/{name}/map.json', ordered(m))
        (g / f'data/maps/{name}/scripts.inc').write_text(f'{name}_MapScripts::\n    .byte 0\n')
        groups[GROUP].append(name)
        with (g / 'data/event_scripts.s').open('a') as f:
            f.write(f'\n.include "data/maps/{name}/scripts.inc"\n')
    write(g / 'data/layouts/layouts.json', layouts)
    write(g / 'data/maps/map_groups.json', groups)
    for route in MOUTHS:
        wire_mouth(g, route, mb)
    p = g / 'src/apocrypha_map_proof.c'; s = p.read_text()
    anchor = 'MAP_ROUTE45, MAP_ROUTE46};'
    assert anchor in s
    s = s.replace(anchor, 'MAP_ROUTE45, MAP_ROUTE46, ' + ', '.join(map_id(n) for n in MAPS.values()) + '};'); p.write_text(s)
    report = read(EV / 'pack.json')
    write(EV / 'capacity.json', dict(maps=list(MAPS.values()), primary=f'gTileset_{PRIMARY_SYM}', secondary=f'gTileset_{SECONDARY_SYM}',
                                     build='HGSS Dark Cave render, fitted banks and medoid tile reuse (pack.py)',
                                     pack=report, map_ids={n: groups[GROUP].index(n) for n in MAPS.values()},
                                     route_edits={r: dict(cell=list(c), metatile=mid, behavior='MB_NON_ANIMATED_DOOR', collision=0,
                                                          warp=warp_events(r)[0]) for r, (c, mid, _) in MOUTHS.items()}))
    print('Installed Dark Cave:', {n: groups[GROUP].index(n) for n in MAPS.values()})

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
