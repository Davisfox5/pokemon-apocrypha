"""Install Celadon round 6 (the approved concept, streamed) over the round 3 install.

    python3 tools/gba/maps/celadon_elements/install6.py ENGINE_CHECKOUT

Reads stream6.py's tables (source/stream6.npz) and interiors.py's rooms. Round 3 put
KantoCeladonCity, its Center and its rooms in the engine (install.py); every commit on
them is the agent's draft (AGENTS.md: regenerate while the map is the agent's draft), so
this rewrites them in place instead of registering anything new:

    src/data/celadon_view.h, data/celadon_view/*.bin
                the streamed art: glyphs (4bpp), the fountains' four frames, per cell its
                eight entries (glyph, flips, palette) and layer type, the palettes and their
                banks, and per player cell the palettes its screen shows (celadon_view.c)
    gTileset_KantoCeladonPrimary / gTileset_KantoCeladonCity
                stand-ins for Porymap and the engine's behaviour lookups: one metatile per
                kind of cell (open, walk-behind, solid, water, door), each a flat colour, and
                the primary's animation callback for the fountains
    KantoCeladonCity
                64 x 52 (plan.py), its collision, elevation and behaviour per cell
                (stream6.traversal), the doors to rooms that exist (the Dept Store's
                services, the hotel, the Center, the Game Corner, the cafe), the signs on
                the building fronts beside their doors and on the fountain
    rooms       FireRed's rooms as before (interiors.py); the prize room is up the Game
                Corner's stairs (no prize house), and the Gardens' room, which no door
                reaches now, leads back to the Center's door
Doors to buildings with no room yet (the apartments, the house beside the Game Corner) are
solid. The border is the north-west forest's 2 x 2 tree block.
"""
from __future__ import annotations
import json, re, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image

import common as C
import plan as PL
import stream6 as S
import interiors as I
from install import (read, write, map_id, layout_id, jasc, tiles_png, metatiles, palettes, porymap_order,
                     ROOMS, MUSIC, MAPSEC, NAME, PFOLDER, PSYM, FOLDER, SYM)

W, H = PL.W, PL.H
EV = C.EV / 'v6' / 'engine'
# The city's warps, in order: the door (stream6.ROOMS / plan.DOORS) and its room (install.ROOMS key).
WARPS = [('center', 'center'), ('dept_store', 'services'), ('hotel', 'hotel_1f'), ('gamecorner', 'game_corner'), ('cafe', 'cafe')]
OLD_DOOR = dict(services='dept_store', hotel='hotel', gamecorner='gamecorner', cafe='cafe', gardens='center')
SIGNS = [
    ('CitySign', 'fountain', 'CELADON CITY\\nThe City of Rainbow Colors.\\pRebuilt by its people.'),
    ('ServicesSign', 'dept_store', 'CELADON MARKET SERVICES\\pSALON, MOVE TUTOR and\\nEV TRAINING inside.'),
    ('HotelSign', 'hotel', 'POKéMON HOTEL\\nRooms for travelers from every region.'),
    ('GameCornerSign', 'gamecorner', 'CELADON GAME CORNER\\nA fun place for everyone!\\pPRIZE COUNTER: take the stairs\\nat the back.'),
    ('CafeSign', 'cafe', 'CELADON CAFé\\nFresh from the market every morning.'),
]
# Stand-in metatiles: (name, behaviour, layer type, colour shown in Porymap)
KINDS = [('open', 'MB_NORMAL', S.COVERED, (120, 200, 120)), ('behind', 'MB_NORMAL', S.NORMAL, (200, 248, 200)),
         ('solid', 'MB_NORMAL', S.COVERED, (96, 64, 64)), ('water', 'MB_POND_WATER', S.COVERED, (64, 96, 208)),
         ('door', 'MB_NON_ANIMATED_DOOR', S.COVERED, (248, 216, 64))]
KIND_INDEX = {k[0]: i for i, k in enumerate(KINDS)}
ANIM_PERIOD = 10                      # frames per fountain frame (concept.py's fountains.gif: 160 ms)
SCREEN_MAX = 14                       # palette ids per player cell's screen list (13 at most, 0xFF after)

def rgb555(c):
    r, g, b = (int(v) >> 3 for v in c)
    return r | (g << 5) | (b << 10)

def pack4(ix):
    ix = np.asarray(ix, np.uint8).reshape(8, 8)
    return bytes(int(ix[y, x]) | (int(ix[y, x + 1]) << 4) for y in range(8) for x in range(0, 8, 2))

def view_data(g, z):
    """The streamed tables and their header."""
    d = g / 'data/celadon_view'
    d.mkdir(parents=True, exist_ok=True)
    glyphs, anim, ent = z['glyphs'], z['anim_frames'], z['entries']
    n_static = int(z['n_static'])
    pinned = anim.shape[1]
    (d / 'glyphs.bin').write_bytes(b''.join(pack4(t) for t in glyphs))
    (d / 'anim.bin').write_bytes(b''.join(pack4(t) for f in range(4) for t in anim[f]) or b'\0' * 32)
    (d / 'entries.bin').write_bytes(ent.astype('<u4').tobytes())
    (d / 'layers.bin').write_bytes(z['layers'].astype(np.uint8).tobytes())
    pals = z['palettes']
    (d / 'palettes.bin').write_bytes(b''.join(struct.pack('<16H', *[rgb555(c) for c in p]) for p in pals))
    (d / 'banks.bin').write_bytes(z['banks'].astype(np.uint8).tobytes())
    screens = np.full((H, W, SCREEN_MAX), 0xFF, np.uint8)
    for y in range(H):
        for x in range(W):
            ps = sorted(z['screens'][y, x][z['screens'][y, x] != 0xFF].tolist())
            assert len(ps) <= 13, ('a screen needs more than 13 palettes', x, y, ps)
            screens[y, x, :len(ps)] = ps
    (d / 'screens.bin').write_bytes(screens.tobytes())
    (g / 'src/data/celadon_view.h').write_text(
        '// Celadon City\'s streamed art (celadon_view.c). Generated by install6.py from\n'
        '// stream6.py\'s tables in the hub (tools/gba/maps/celadon_elements); do not edit by hand.\n'
        f'#define CELADON_W {W}\n#define CELADON_H {H}\n#define CELADON_STATIC {n_static}\n'
        f'#define CELADON_PINNED {pinned}\n#define CELADON_PALETTES {len(pals)}\n#define CELADON_SCREEN {SCREEN_MAX}\n'
        f'#define CELADON_ANIM_PERIOD {ANIM_PERIOD}\n'
        'static const u32 sCeladonGlyphs[] = INCBIN_U32("data/celadon_view/glyphs.bin");\n'
        'static const u32 sCeladonAnim[] = INCBIN_U32("data/celadon_view/anim.bin");\n'
        'static const u32 sCeladonEntries[] = INCBIN_U32("data/celadon_view/entries.bin");\n'
        'static const u8 sCeladonLayers[] = INCBIN_U8("data/celadon_view/layers.bin");\n'
        'static const u16 sCeladonPalettes[] = INCBIN_U16("data/celadon_view/palettes.bin");\n'
        'static const u8 sCeladonBanks[] = INCBIN_U8("data/celadon_view/banks.bin");\n'
        'static const u8 sCeladonScreens[] = INCBIN_U8("data/celadon_view/screens.bin");\n')
    return dict(glyphs=len(glyphs), static=n_static, pinned=pinned, palettes=len(pals),
                bytes=sum(p.stat().st_size for p in d.iterdir()))

def stand_ins(g, MB):
    """The two tilesets: flat-colour stand-in metatiles, palettes, the fountains' callback."""
    pal = np.zeros((16, 16, 3), np.uint8)
    for i, (_, _, _, c) in enumerate(KINDS):
        pal[0, i + 1] = c
    tiles = [np.zeros((8, 8), np.uint8)] + [np.full((8, 8), i + 1, np.uint8) for i in range(len(KINDS))]
    pd = g / f'data/tilesets/primary/{PFOLDER}'
    tiles_png(pd / 'tiles.png', tiles)
    palettes(pd, pal)
    rows = []
    for i, (_, mb, layer, _) in enumerate(KINDS):
        t = 1 + i
        rows.append([t] * 4 + ([0] * 4) + [MB[mb] | (layer << 12)])
    rows += [[0] * 9] * (512 - len(rows))
    metatiles(pd, rows)
    sd = g / f'data/tilesets/secondary/{FOLDER}'
    tiles_png(sd / 'tiles.png', [np.zeros((8, 8), np.uint8)])
    palettes(sd, pal, pd)
    metatiles(sd, [[0] * 9])
    for f in (pd / 'anim', sd / 'anim'):
        if f.exists():
            raise SystemExit(f'unexpected {f}')
    p = g / 'src/data/tilesets/headers.h'
    s = p.read_text()
    pat = re.compile(r'(const struct Tileset gTileset_' + PSYM + r' = \{[^}]*\.callback = )(\w+)( \};)')
    assert pat.search(s), 'primary header'
    s = pat.sub(r'\1InitTilesetAnim_KantoCeladonView\3', s)
    p.write_text(s)
    return {k[0]: i for i, k in enumerate(KINDS)}

def kind(foot, layer):
    if foot == 'water':
        return 'water'
    if foot == 'door':
        return 'door'
    if foot == 'blocked':
        return 'solid'
    return 'behind' if layer == S.NORMAL else 'open'

def sign_cells(foot, doors):
    """Each sign on a solid cell of its building's front beside the door, read from the open
    cell south of it; the city sign on the fountain's south rim."""
    out = {}
    for label, where, _ in SIGNS:
        if where == 'fountain':
            fx, fy = next((x, int(b)) for n, k, x, b in PL.PLACES if n == 'fountain')
            cands = [(int(fx) + dx, fy) for dx in (1, 0, 2, -1)]
        else:
            x, y = doors[where]
            cands = [(x + 1, y), (x - 1, y), (x + 2, y), (x - 2, y)]
        for cx, cy in cands:
            if foot[cy, cx] == 'blocked' and foot[cy + 1, cx] in ('open',):
                out[label] = (cx, cy)
                break
        else:
            raise SystemExit(f'no wall for the {label}')
    return out

def city(g, z, kinds, MB, layouts):
    foot, layer = z['foot'], z['layers']
    elev = np.where(foot == 'water', 1, 3)
    coll = np.where(np.isin(foot, ['blocked']), 1, 0)
    grid = np.zeros((H, W), np.uint32)
    for y in range(H):
        for x in range(W):
            grid[y, x] = kinds[kind(foot[y, x], int(layer[y, x]))]
    cells = grid | (coll.astype(np.uint32) << 10) | (elev.astype(np.uint32) << 12)
    ld = g / f'data/layouts/{NAME}'
    (ld / 'map.bin').write_bytes(cells.astype('<u2').tobytes())
    solid = kinds['solid'] | (1 << 10) | (3 << 12)
    (ld / 'border.bin').write_bytes(struct.pack('<4H', *[solid] * 4))
    lay = next(l for l in layouts['layouts'] if l.get('id') == layout_id(NAME))
    lay.update(width=W, height=H)
    m = read(g / f'data/maps/{NAME}/map.json')
    doors = {k: tuple(v) for k, v in json.loads((EV / 'stream.json').read_text())['doors'].items()}
    m['warp_events'] = []
    for door, room in WARPS:
        x, y = doors[door]
        if room == 'center':
            dest, warp = map_id('KantoCeladonPokemonCenter'), '0'
        else:
            from install import arrival
            dest, warp = map_id(ROOMS[room][0]), str(arrival(room))
        m['warp_events'].append(dict(x=x, y=y, elevation=0, dest_map=dest, dest_warp_id=warp))
    where = sign_cells(foot, doors)
    m['bg_events'] = []
    script = f'{NAME}_MapScripts::\n    .byte 0\n'
    for label, _, text in SIGNS:
        x, y = where[label]
        m['bg_events'].append(dict(type='sign', x=x, y=y, elevation=0, player_facing_dir='BG_EVENT_PLAYER_FACING_NORTH',
                                   script=f'{NAME}_{label}'))
        script += (f'\n{NAME}_{label}::\n    msgbox {NAME}_{label}_Text, MSGBOX_SIGN\n    end\n'
                   f'\n{NAME}_{label}_Text:\n    .string "{text}$"\n')
    write(g / f'data/maps/{NAME}/map.json', porymap_order(m))
    (g / f'data/maps/{NAME}/scripts.inc').write_text(script)
    colour = {i: k[3] for i, k in enumerate(KINDS)}             # the stand-ins as Porymap draws them
    Image.fromarray(np.array([[colour[int(v)] for v in row] for row in grid], np.uint8).repeat(16, 0).repeat(16, 1)).save(EV / 'standin.png')
    return dict(warps=[(d, r) for d, r in WARPS], signs={k: list(v) for k, v in where.items()})

def city_warp_index(door):
    return next(i for i, (d, _) in enumerate(WARPS) if d == door)

def rooms(g, layouts):
    """The rooms' files rewritten from interiors.py (tiles, banks, metatiles, blocks) and their
    warps pointed at round 6's doors."""
    out = {}
    for key, (name, music) in ROOMS.items():
        z = np.load(C.SRC / f'interiors/{key}.npz')
        folder = f'kanto_celadon_{key}'
        d = g / f'data/tilesets/secondary/{folder}'
        tiles_png(d / 'tiles.png', z['tiles'])
        palettes(d, z['palettes'], g / 'data/tilesets/primary/building')
        metatiles(d, z['meta'])
        ld = g / f'data/layouts/{name}'
        (ld / 'map.bin').write_bytes(z['grid'].astype('<u2').tobytes())
        h = z['grid'].shape[0]
        black = int(z['grid'][h - 1, 0])                   # the room's black, as install.py takes it
        (ld / 'border.bin').write_bytes(struct.pack('<4H', *[black] * 4))
        warps = []
        for (x, y), to in I.ROOMS[key][2].items():
            where, n = to.split(':')
            if where == 'city':
                dest, warp = map_id(NAME), str(city_warp_index(OLD_DOOR[n]))
            else:
                dest, warp = map_id(ROOMS[where][0]), n
            warps.append(dict(x=x, y=y, elevation=3, dest_map=dest, dest_warp_id=warp))
        m = read(g / f'data/maps/{name}/map.json')
        m['warp_events'] = warps
        write(g / f'data/maps/{name}/map.json', porymap_order(m))
        out[name] = [(w['x'], w['y'], w['dest_map'], w['dest_warp_id']) for w in warps]
    return out

def main(g):
    import build as B
    MB = B.behaviors(g)
    z = dict(np.load(C.SRC / 'stream6.npz'))
    if 'screens' not in z:
        raise SystemExit('stream6.npz has no screens table: rerun stream6.py')
    layouts = read(g / 'data/layouts/layouts.json')
    rep = dict(view=view_data(g, z))
    kinds = stand_ins(g, MB)
    rep['city'] = city(g, z, kinds, MB, layouts)
    rep['rooms'] = rooms(g, layouts)
    write(g / 'data/layouts/layouts.json', layouts)
    (EV / 'install.json').write_text(json.dumps(rep, indent=1) + '\n')
    print(json.dumps(rep['view']), rep['city']['signs'])

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
