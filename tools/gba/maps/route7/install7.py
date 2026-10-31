"""Install Route 7 beside Celadon, streamed as one world, and open Saffron's west gate.

    python3 tools/gba/maps/route7/install7.py ENGINE_CHECKOUT

Reads world.py's tables (source/world.npz) and gate_room.py's room. On the engine branch
Celadon is already installed (celadon_elements/install6.py); this rewrites its streamed tables
as the world's and adds:

    src/data/celadon_view.h, data/celadon_view/*.bin
                the world's streamed art (Celadon x 0-63, Route 7 x 64-96 from world row 1)
    stand-ins   install6's kinds, and the route's: tall grass, the south and east ledges, the
                east arrow warp (each covered or, where a crown hangs over it, walk-behind)
    KantoCeladonCity
                its cells as before; a map connection east to Route 7 (offset 1)
    KantoRoute7 (new, gMapGroup_Kanto, MAPSEC_ROUTE_7)
                33 x 32 on Celadon's stand-in pair, its cells from the world's traversal; a map
                connection west to Celadon (offset -1); the five arrow cells in front of the gate
                warp into the gate room; FireRed's Underground Path sign on the notice board;
                the wild table from KANTO_BATTLES' R07 row
    KantoRoute7Gatehouse (new)
                FireRed's Route 7 gate room (gate_room.py), its west arrow back to Route 7, its
                east arrow to Saffron
    KantoSaffronCity
                owner-accepted, so edited natively: its west gate's door cell (8, 27) opens as a
                west arrow warp (a copy of its metatile with the arrow behaviour) into the gate room
"""
from __future__ import annotations
import json, re, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'celadon_elements'))
sys.path.insert(0, str(HERE))
import common as C             # noqa: E402
import stream6 as S            # noqa: E402
import install6 as I6          # noqa: E402
import compose as R            # noqa: E402
import world as WD             # noqa: E402
from install import read, write, map_id, layout_id, tiles_png, metatiles, palettes, porymap_order, register   # noqa: E402

EV = R.EV / 'engine'
NAME, ROOM, GROUP = 'KantoRoute7', 'KantoRoute7Gatehouse', 'gMapGroup_Kanto'
CELADON, SAFFRON = 'KantoCeladonCity', 'KantoSaffronCity'
MAPSEC, MUSIC, ROOM_MUSIC = 'MAPSEC_ROUTE_7', 'MUS_RG_ROUTE3', 'MUS_RG_PEWTER'   # FireRed's Route 7 and its gate's
ROOM_FOLDER, ROOM_SYM = 'kanto_route7_gatehouse', 'KantoRoute7Gatehouse'
SAFFRON_GATE, SAFFRON_GATE_FROM = (8, 27), 0xA8          # the west gate's door cell and its metatile
NOTICE_TEXT = 'UNDERGROUND PATH\\nCELADON CITY - LAVENDER TOWN'      # FireRed's Route 7 sign
ROUTE_KINDS = [('tall', 'MB_TALL_GRASS', S.COVERED, (72, 160, 96)), ('tall_behind', 'MB_TALL_GRASS', S.NORMAL, (120, 200, 140)),
               ('jump_s', 'MB_JUMP_SOUTH', S.COVERED, (160, 112, 72)), ('jump_e', 'MB_JUMP_EAST', S.COVERED, (176, 128, 88)),
               ('arrow_e', 'MB_EAST_ARROW_WARP', S.COVERED, (248, 160, 64)), ('arrow_behind', 'MB_EAST_ARROW_WARP', S.NORMAL, (248, 200, 120))]
# KANTO_BATTLES, Route 7 (R07), lv 16-19: Rattata (Raticate rare), Spearow, Growlithe, and the
# Plusle / Minun / Shinx migrant slots, rare. Slots in Emerald's land rates (20 20 10 10 10 10 5 5 4 4 1 1).
WILD = [('RATTATA', 16, 17), ('SPEAROW', 16, 17), ('GROWLITHE', 16, 17), ('RATTATA', 17, 18), ('SPEAROW', 17, 18),
        ('GROWLITHE', 17, 18), ('RATTATA', 18, 19), ('SPEAROW', 18, 19), ('RATICATE', 19, 19), ('SHINX', 17, 17),
        ('PLUSLE', 17, 17), ('MINUN', 17, 17)]
WILD_RATE = 21                                              # FireRed's Route 7
if not any(k[0] == 'tall' for k in I6.KINDS):              # the stand-ins: Celadon's kinds, then the route's
    I6.KINDS += ROUTE_KINDS
I6.KIND_INDEX = {k[0]: i for i, k in enumerate(I6.KINDS)}

def kind(foot, layer):
    behind = layer == S.NORMAL
    if foot == 'tall':
        return 'tall_behind' if behind else 'tall'
    if foot == 'arrow_e':
        return 'arrow_behind' if behind else 'arrow_e'
    if foot in ('jump_s', 'jump_e'):
        return foot
    return I6.kind(foot, layer)

def view_data(g, z):
    """The world's tables, as install6.view_data writes Celadon's, and the header with the world's
    size and Route 7's origin."""
    d = g / 'data/celadon_view'
    d.mkdir(parents=True, exist_ok=True)
    H, W = z['entries'].shape[:2]
    n_static, pinned = int(z['n_static']), z['anim_frames'].shape[1]
    (d / 'glyphs.bin').write_bytes(b''.join(I6.pack4(t) for t in z['glyphs']))
    (d / 'anim.bin').write_bytes(b''.join(I6.pack4(t) for f in range(4) for t in z['anim_frames'][f]))
    (d / 'entries.bin').write_bytes(z['entries'].astype('<u4').tobytes())
    (d / 'layers.bin').write_bytes(z['layers'].astype(np.uint8).tobytes())
    (d / 'palettes.bin').write_bytes(b''.join(struct.pack('<16H', *[I6.rgb555(c) for c in p]) for p in z['palettes']))
    (d / 'banks.bin').write_bytes(z['banks'].astype(np.uint8).tobytes())
    screens = np.full((H, W, I6.SCREEN_MAX), 0xFF, np.uint8)
    for y in range(H):
        for x in range(W):
            ps = sorted(z['screens'][y, x][z['screens'][y, x] != 0xFF].tolist())
            assert len(ps) <= 13, ('a screen needs more than 13 palettes', x, y, ps)
            screens[y, x, :len(ps)] = ps
    (d / 'screens.bin').write_bytes(screens.tobytes())
    (g / 'src/data/celadon_view.h').write_text(
        '// Celadon City\'s and Route 7\'s streamed art (celadon_view.c), one world. Generated by\n'
        '// route7/install7.py from route7/world.py\'s tables in the hub; do not edit by hand.\n'
        f'#define CELADON_W {W}\n#define CELADON_H {H}\n#define CELADON_ROUTE7_X {WD.CW}\n#define CELADON_ROUTE7_Y {R.OY}\n'
        f'#define CELADON_STATIC {n_static}\n#define CELADON_PINNED {pinned}\n#define CELADON_PALETTES {len(z["palettes"])}\n'
        f'#define CELADON_SCREEN {I6.SCREEN_MAX}\n#define CELADON_ANIM_PERIOD {I6.ANIM_PERIOD}\n'
        'static const u32 sCeladonGlyphs[] = INCBIN_U32("data/celadon_view/glyphs.bin");\n'
        'static const u32 sCeladonAnim[] = INCBIN_U32("data/celadon_view/anim.bin");\n'
        'static const u32 sCeladonEntries[] = INCBIN_U32("data/celadon_view/entries.bin");\n'
        'static const u8 sCeladonLayers[] = INCBIN_U8("data/celadon_view/layers.bin");\n'
        'static const u16 sCeladonPalettes[] = INCBIN_U16("data/celadon_view/palettes.bin");\n'
        'static const u8 sCeladonBanks[] = INCBIN_U8("data/celadon_view/banks.bin");\n'
        'static const u8 sCeladonScreens[] = INCBIN_U8("data/celadon_view/screens.bin");\n')
    return dict(world=[W, H], glyphs=len(z['glyphs']), static=n_static, pinned=pinned, palettes=len(z['palettes']),
                bytes=sum(p.stat().st_size for p in d.iterdir()))

def celadon(g, z, kinds, MB, layouts):
    """Celadon's cells as install6 writes them (the world's west 64 columns), and its connection."""
    I6.EV = EV
    (EV / 'stream.json').exists() or (_ for _ in ()).throw(SystemExit('run world.py first'))
    zc = dict(z)
    zc['foot'], zc['layers'] = z['foot'][:, :WD.CW], z['layers'][:, :WD.CW]
    rep = I6.city(g, zc, kinds, MB, layouts)
    p = g / f'data/maps/{CELADON}/map.json'
    m = read(p)
    m['connections'] = [dict(map=map_id(NAME), offset=R.OY, direction='right')]
    write(p, porymap_order(m))
    Image.open(EV / 'standin.png').save(EV / 'standin-celadon.png')
    return rep

def cells_for(foot, layer, kinds):
    h, w = foot.shape
    grid = np.zeros((h, w), np.uint32)
    for y in range(h):
        for x in range(w):
            grid[y, x] = kinds[kind(foot[y, x], int(layer[y, x]))]
    blocked = np.isin(foot, ['blocked', 'jump_s', 'jump_e'])          # Emerald's ledges are solid cells with the jump behaviour
    return grid, grid | (blocked.astype(np.uint32) << 10) | (np.uint32(3) << 12)

def route(g, z, kinds, layouts, groups):
    sl = np.s_[R.OY:R.OY + R.MH, WD.CW:WD.CW + R.MW]
    foot, layer = z['foot'][sl], z['layers'][sl]
    grid, cells = cells_for(foot, layer, kinds)
    ld = g / f'data/layouts/{NAME}'
    ld.mkdir(parents=True, exist_ok=True)
    (ld / 'map.bin').write_bytes(cells.astype('<u2').tobytes())
    solid = kinds['solid'] | (1 << 10) | (3 << 12)
    (ld / 'border.bin').write_bytes(struct.pack('<4H', *[solid] * 4))
    lay = dict(id=layout_id(NAME), name=f'{NAME}_Layout', width=R.MW, height=R.MH,
               primary_tileset=f'gTileset_{I6.PSYM}', secondary_tileset=f'gTileset_{I6.SYM}',
               border_filepath=f'data/layouts/{NAME}/border.bin', blockdata_filepath=f'data/layouts/{NAME}/map.bin',
               layout_version='emerald')
    layouts['layouts'] = [l for l in layouts['layouts'] if not l or l.get('id') != lay['id']] + [lay]
    m = dict(read(g / f'data/maps/{CELADON}/map.json'))
    room_id = map_id(ROOM)
    nx, ny = R.NOTICE
    m.update(id=map_id(NAME), name=NAME, layout=layout_id(NAME), music=MUSIC, region_map_section=MAPSEC,
             map_type='MAP_TYPE_ROUTE', weather='WEATHER_SUNNY', show_map_name=True, allow_cycling=True,
             connections=[dict(map=map_id(CELADON), offset=-R.OY, direction='left')], object_events=[], coord_events=[],
             warp_events=[dict(x=x, y=y, elevation=0, dest_map=room_id, dest_warp_id='0') for x, y in R.ARROWS],
             bg_events=[dict(type='sign', x=nx, y=ny, elevation=0, player_facing_dir='BG_EVENT_PLAYER_FACING_NORTH',
                             script=f'{NAME}_UndergroundPathSign')])
    m['region'] = 'REGION_KANTO'
    write(g / f'data/maps/{NAME}/map.json', porymap_order(m))
    (g / f'data/maps/{NAME}/scripts.inc').write_text(
        f'{NAME}_MapScripts::\n    .byte 0\n'
        f'\n{NAME}_UndergroundPathSign::\n    msgbox {NAME}_UndergroundPathSign_Text, MSGBOX_SIGN\n    end\n'
        f'\n{NAME}_UndergroundPathSign_Text:\n    .string "{NOTICE_TEXT}$"\n')
    colour = {i: k[3] for i, k in enumerate(I6.KINDS)}
    Image.fromarray(np.array([[colour[int(v)] for v in row] for row in grid], np.uint8).repeat(16, 0).repeat(16, 1)).save(EV / 'standin.png')
    return dict(size=[R.MW, R.MH], warps=len(R.ARROWS), notice=[nx, ny],
                kinds={k: int((grid == kinds[k]).sum()) for k in kinds if (grid == kinds[k]).any()})

def gate_room(g, layouts):
    z = np.load(R.SRC / 'interiors/gate.npz')
    h, w = z['grid'].shape
    d = g / f'data/tilesets/secondary/{ROOM_FOLDER}'
    tiles_png(d / 'tiles.png', z['tiles'])
    palettes(d, z['palettes'], g / 'data/tilesets/primary/building')
    metatiles(d, z['meta'])
    if f'gTileset_{ROOM_SYM} ' not in (g / 'src/data/tilesets/headers.h').read_text():
        register(g, ROOM_SYM, 'secondary', ROOM_FOLDER, "Route 7's gatehouse (FireRed's Route 7 gate room)")
    ld = g / f'data/layouts/{ROOM}'
    ld.mkdir(parents=True, exist_ok=True)
    (ld / 'map.bin').write_bytes(z['grid'].astype('<u2').tobytes())
    black = int(z['grid'][h - 1, 0])
    (ld / 'border.bin').write_bytes(struct.pack('<4H', *[black] * 4))
    lay = dict(id=layout_id(ROOM), name=f'{ROOM}_Layout', width=w, height=h, primary_tileset='gTileset_Building',
               secondary_tileset=f'gTileset_{ROOM_SYM}', border_filepath=f'data/layouts/{ROOM}/border.bin',
               blockdata_filepath=f'data/layouts/{ROOM}/map.bin', layout_version='emerald')
    layouts['layouts'] = [l for l in layouts['layouts'] if not l or l.get('id') != lay['id']] + [lay]
    m = dict(read(g / 'data/maps/KantoSaffronMart/map.json'))
    middle = len(R.ARROWS) // 2
    m.update(id=map_id(ROOM), name=ROOM, layout=layout_id(ROOM), music=ROOM_MUSIC, region_map_section=MAPSEC,
             object_events=[], coord_events=[], bg_events=[],
             warp_events=[dict(x=1, y=5, elevation=3, dest_map=map_id(NAME), dest_warp_id=str(middle)),
                          dict(x=11, y=5, elevation=3, dest_map=map_id(SAFFRON), dest_warp_id=str(saffron_warp_index(g)))])
    m['region'] = 'REGION_KANTO'
    write(g / f'data/maps/{ROOM}/map.json', porymap_order(m))
    (g / f'data/maps/{ROOM}/scripts.inc').write_text(f'{ROOM}_MapScripts::\n    .byte 0\n')
    return dict(size=[w, h], tiles=int(len(z['tiles'])), metatiles=int(len(z['meta'])))

def saffron_warp_index(g):
    ws = read(g / f'data/maps/{SAFFRON}/map.json')['warp_events']
    return next(i for i, w in enumerate(ws) if (w['x'], w['y']) == SAFFRON_GATE)

def saffron(g, MB):
    """The west gate's door cell opens: a copy of its metatile with FireRed's west arrow
    behaviour, the cell walkable, a warp into the gate room."""
    lay = next(l for l in read(g / 'data/layouts/layouts.json')['layouts'] if l and l.get('id') == layout_id(SAFFRON))
    folder = 'data/tilesets/primary/kanto_saffron'
    mb = np.frombuffer((g / folder / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8).copy()
    at = np.frombuffer((g / folder / 'metatile_attributes.bin').read_bytes(), '<u2').copy()
    want = (at[SAFFRON_GATE_FROM] & 0xF000) | MB['MB_WEST_ARROW_WARP']
    have = [i for i in range(len(mb)) if (mb[i] == mb[SAFFRON_GATE_FROM]).all() and at[i] == want]
    if have:
        new = have[0]
    else:
        new = next(i for i in range(1, len(mb)) if not mb[i].any() and at[i] == 0)
        mb[new], at[new] = mb[SAFFRON_GATE_FROM], want
        (g / folder / 'metatiles.bin').write_bytes(mb.astype('<u2').tobytes())
        (g / folder / 'metatile_attributes.bin').write_bytes(at.astype('<u2').tobytes())
    p = g / lay['blockdata_filepath']
    grid = np.frombuffer(p.read_bytes(), '<u2').reshape(lay['height'], lay['width']).copy()
    x, y = SAFFRON_GATE
    grid[y, x] = new | (0 << 10) | (int(grid[y, x]) >> 12 << 12)
    p.write_bytes(grid.astype('<u2').tobytes())
    mp = g / f'data/maps/{SAFFRON}/map.json'
    m = read(mp)
    if not any((w['x'], w['y']) == SAFFRON_GATE for w in m['warp_events']):
        m['warp_events'].append(dict(x=x, y=y, elevation=0, dest_map=map_id(ROOM), dest_warp_id='1'))
    write(mp, porymap_order(m))
    return dict(cell=[x, y], metatile=int(new), warp=saffron_warp_index(g))

def wild(g):
    p = g / 'src/data/wild_encounters.json'
    w = read(p)
    grp = next(x for x in w['wild_encounter_groups'] if x['label'] == 'gWildMonHeaders')
    grp['encounters'] = [e for e in grp['encounters'] if e.get('map') != map_id(NAME)]
    grp['encounters'].append(dict(map=map_id(NAME), base_label='gKantoRoute7', land_mons=dict(
        encounter_rate=WILD_RATE, mons=[dict(min_level=a, max_level=b, species=f'SPECIES_{s}') for s, a, b in WILD])))
    p.write_text(json.dumps(w, indent=2, ensure_ascii=False) + '\n')
    return WILD

def register_maps(g, groups):
    names = [n for n in (NAME, ROOM) if n not in groups[GROUP]]
    groups[GROUP].extend(names)
    if names:
        with (g / 'data/event_scripts.s').open('a') as f:
            for n in names:
                f.write(f'\n.include "data/maps/{n}/scripts.inc"\n')
        p = g / 'src/apocrypha_map_proof.c'; s = p.read_text()
        anchor = re.search(r'(MAP_KANTO_CELADON_CAFE)\};', s)
        assert anchor, 'map proof list'
        p.write_text(s.replace(anchor.group(0), anchor.group(1) + ', ' + ', '.join(map_id(n) for n in names) + '};'))
    return {n: groups[GROUP].index(n) for n in (NAME, ROOM)}

def main(g):
    import build as B
    MB = B.behaviors(g)
    z = dict(np.load(WD.NPZ))
    layouts = read(g / 'data/layouts/layouts.json')
    groups = read(g / 'data/maps/map_groups.json')
    rep = dict(view=view_data(g, z))
    kinds = I6.stand_ins(g, MB)
    rep['ids'] = register_maps(g, groups)
    rep['celadon'] = celadon(g, z, kinds, MB, layouts)
    rep['route'] = route(g, z, kinds, layouts, groups)
    rep['saffron'] = saffron(g, MB)
    rep['room'] = gate_room(g, layouts)
    rep['wild'] = wild(g)
    write(g / 'data/layouts/layouts.json', layouts)
    write(g / 'data/maps/map_groups.json', groups)
    (EV / 'install.json').write_text(json.dumps(rep, indent=1) + '\n')
    print(json.dumps({k: v for k, v in rep.items() if k != 'wild'}))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
