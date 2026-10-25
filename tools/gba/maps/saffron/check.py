"""Audit the installed Saffron City (KantoSaffronCity, v3) and its two rooms from their native files.

    python3 tools/gba/maps/saffron/check.py ENGINE_CHECKOUT

Decodes data/layouts/KantoSaffronCity with gTileset_KantoSaffronPrimary and
gTileset_KantoSaffronCity exactly as the game composes them (bottom layer, then the top
layer's non-zero pixels) and checks it against compose.py's picture and the packer's
decode; the palettes against the packer's; every bottom-layer pixel opaque; the parts' cells
in the secondary; the traversal ledger (behaviour, collision, elevation, layer type per
cell, FireRed's layer type on every cell FireRed drew); reachability; the signs and doors in
map.json; the Center and Mart door animation (FireRed's frames, indexed into the door's
banks); the Dojo hall and the lab (their blocks, exit mats and warps both ways); budgets
and preservation.
Writes evidence/native-audit.json and evidence/native-grid.png.
"""
from __future__ import annotations
import json, subprocess, sys
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(HERE), str(HERE.parent / 'olivine_elements')]
import build as B                                   # noqa: E402
import frlg                                         # noqa: E402
import compose as C                                 # noqa: E402
import pack as P                                    # noqa: E402

ART = ROOT / 'gba/art/saffron-kanto'
SRC, EV = ART / 'source', ART / 'evidence'
W, H = C.W, C.H
NAME, PFOLDER, FOLDER = 'KantoSaffronCity', 'kanto_saffron', 'kanto_saffron_city'
START = (24, 39)                                    # in front of the Center door
BASE = 'origin/claude/olivine-city'                 # the engine branch Saffron builds on

def tileset(d):
    a = np.array(Image.open(d / 'tiles.png')) & 15
    tiles = [a[y:y + 8, x:x + 8] for y in range(0, a.shape[0], 8) for x in range(0, a.shape[1], 8)]
    metas = np.frombuffer((d / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
    attrs = np.frombuffer((d / 'metatile_attributes.bin').read_bytes(), '<u2')
    return tiles, metas, attrs

def render_blocks(g, blocks):
    """Map blocks (metatile id | collision << 10 | elevation << 12), any shape, drawn with
    the installed pair as the game composes them (a bottom pixel of colour 0 shows
    frlg.under's fill); with each cell's attributes."""
    prim, sec = g / f'data/tilesets/primary/{PFOLDER}', g / f'data/tilesets/secondary/{FOLDER}'
    pt, pm, pa = tileset(prim)
    st, sm, sa = tileset(sec)
    pals = [B.read_pal((prim if i < 6 else sec) / 'palettes' / f'{i:02}.pal') for i in range(16)]
    tiles = pt[:512] + [np.zeros((8, 8), np.uint8)] * (512 - len(pt[:512])) + st
    metas, attrs = list(pm[:512]) + list(sm), list(pa[:512]) + list(sa)
    h, w = blocks.shape
    img = np.zeros((h * 16, w * 16, 3), np.uint8)
    beh, layer, coll, elev, mid = (np.zeros((h, w), np.int32) for _ in range(5))
    hole = np.zeros((h * 16, w * 16), bool)          # bottom pixels of colour 0 the top layer does not cover
    for y, x in np.ndindex(h, w):
        v = int(blocks[y, x]); m = v & 1023
        mid[y, x], coll[y, x], elev[y, x] = m, (v >> 10) & 3, v >> 12
        beh[y, x], layer[y, x] = int(attrs[m]) & 0xFF, (int(attrs[m]) >> 12) & 3
        fill = frlg.under(tiles[frlg.FILL_TILE], layer[y, x], pals)
        for i, e in enumerate(metas[m]):
            e = int(e); t = tiles[e & 1023]
            if e & 1024: t = t[:, ::-1]
            if e & 2048: t = t[::-1]
            q = i % 4; oy, ox = y * 16 + (q // 2) * 8, x * 16 + (q % 2) * 8
            if i < 4:
                hole[oy:oy + 8, ox:ox + 8] = t == 0
                img[oy:oy + 8, ox:ox + 8] = np.where((t == 0)[..., None], fill, np.array(pals[e >> 12], np.uint8)[t])
            else:
                img[oy:oy + 8, ox:ox + 8][t > 0] = np.array(pals[e >> 12])[t[t > 0]]
                hole[oy:oy + 8, ox:ox + 8][t > 0] = False
    return dict(img=img, beh=beh, layer=layer, coll=coll, elev=elev, mid=mid, pals=pals, transparent_bottom=int(hole.sum()),
                prim_tiles=len(pt), sec_tiles=len(st), prim_metas=len(pm), sec_metas=len(sm))

def decode(g):
    grid = np.frombuffer((g / f'data/layouts/{NAME}/map.bin').read_bytes(), '<u2').reshape(H, W)
    return render_blocks(g, grid)

def border_image(g):
    """The 2x2 border block as the camera sees it past the map's edges."""
    border = np.frombuffer((g / f'data/layouts/{NAME}/border.bin').read_bytes(), '<u2').reshape(2, 2)
    return render_blocks(g, border)['img']

def reach(foot):
    seen = {START}; q = deque([START])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if foot.get(n) in ('open', 'door') and n not in seen:
                seen.add(n); q.append(n)
            elif foot.get(n) == 'ledge_south' and dy == 1 and foot.get((x, y + 2)) in ('open', 'door') and (x, y + 2) not in seen:
                seen.add((x, y + 2)); q.append((x, y + 2))
    return seen

def rooms(g, city_warps):
    """The Dojo hall and the lab: installed blocks as interiors.py packed them, every exit mat
    an arrow warp back to its city door, and every city door to them landing on a mat."""
    import install as I
    MB = B.behaviors(g)
    out = {}
    for name, (key, folder, sym, music) in I.ROOMS.items():
        z = np.load(SRC / f'interiors/{key}.npz')
        h, w = z['grid'].shape
        blocks = np.frombuffer((g / f'data/layouts/{name}/map.bin').read_bytes(), '<u2').reshape(h, w)
        assert (blocks == z['grid']).all(), (name, 'blocks')
        m = json.loads((g / f'data/maps/{name}/map.json').read_text())
        warps = m['warp_events']
        for wv in warps:
            x, y = wv['x'], wv['y']
            assert z['behaviour'][y, x] == MB['MB_SOUTH_ARROW_WARP'] or (x, y) != (warps[0]['x'], warps[0]['y']), (name, 'mat', x, y)
            cw = city_warps[int(wv['dest_warp_id'])]
            assert wv['dest_map'] == C_MAP and cw['dest_map'] == I.map_id(name), (name, 'warp back', wv)
        for cw in city_warps:
            if cw['dest_map'] == I.map_id(name):
                land = warps[int(cw['dest_warp_id'])]
                assert z['behaviour'][land['y'], land['x']] == MB['MB_SOUTH_ARROW_WARP'] and z['collision'][land['y'], land['x']] == 0, \
                    (name, 'landing', land)
        out[name] = dict(size=[w, h], warps=len(warps), tiles=int(len(z['tiles'])), metatiles=int(len(z['meta'])))
    return out

C_MAP = 'MAP_KANTO_SAFFRON_CITY'

def steps(foot, start):
    """Walking distance from start to every reachable foot cell (no ledges)."""
    dist = {start: 0}; q = deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if foot.get(n) in ('open', 'door') and n not in dist:
                dist[n] = dist[(x, y)] + 1; q.append(n)
    return dist

def main(g):
    d = decode(g)
    img = d['img']
    comp = np.load(SRC / 'compose.npz')
    want = frlg.flat(comp['bottom'], comp['top'])
    assert (B.rgb5(img) == B.rgb5(want)).all(), 'installed map differs from compose.py'
    built = np.array(Image.open(EV / 'native.png').convert('RGB'))
    assert (B.rgb5(img) == B.rgb5(built)).all(), 'installed map differs from the packer decode'
    pk = np.load(SRC / 'pack.npz')
    for b in P.BANKS:
        assert [tuple(v >> 3 for v in c) for c in d['pals'][b]] == [tuple(int(v) >> 3 for v in c) for c in pk['palettes'][b]], ('bank', b)
    pair = frlg.Pair(g, C.PRIMARY, C.SECONDARY)
    art = comp['art']
    assert (d['mid'][art] >= 512).all(), 'art metatiles outside the secondary'
    assert not d['transparent_bottom'], 'a bottom-layer pixel of colour 0'
    # The traversal ledger.
    trav = json.loads((SRC / 'traversal.json').read_text())
    for c in trav:
        x, y = c['x'], c['y']
        assert d['beh'][y, x] == c['behavior'], (x, y, c['behavior'])
        assert d['coll'][y, x] == c['collision'] and d['elev'][y, x] == c['elevation'], (x, y)
        assert d['layer'][y, x] == (0 if c['layer'] == 'normal' else 1), (x, y)
    # Every cell FireRed drew (no part in it) draws in FireRed's layer type for its (edited) metatile.
    for y, x in np.ndindex(H, W):
        if not art[y, x]:
            assert d['layer'][y, x] == pair.layer_type(int(comp['edited'][y, x]) & 0x3FF), ('layer type', x, y)
    MB = B.behaviors(g)
    foot = {}
    for c in trav:
        k = (c['x'], c['y'])
        foot[k] = ('door' if c['behavior'] == MB['MB_ANIMATED_DOOR'] else 'ledge_south' if c['behavior'] == MB['MB_JUMP_SOUTH']
                   else 'open' if c['collision'] == 0 else 'blocked')
    seen = reach(foot)
    open_cells = {k for k, v in foot.items() if v in ('open', 'door')}
    m = json.loads((g / f'data/maps/{NAME}/map.json').read_text())
    approaches = dict(center=(24, 39), mart=(40, 22), silph=(33, 31), lab=(42, 31), station=(25, 15), fighting_dojo=(40, 13),
                      psychic_dojo=(45, 13), league_office=(49, 23), copycat_house=(19, 22), mr_psychic=(43, 39),
                      south_gate=(34, 45), fountain_garden=(34, 43), plaza=(44, 15), behind_silph=(33, 14))
    approaches.update({f'sign_{b["script"].split("_", 1)[1]}': (b['x'], b['y'] + 1) for b in m['bg_events']})
    for k, p in approaches.items():
        assert p in seen, ('unreachable approach', k, p)
    # Trees stand off the walkways: with their blocked cells opened, no route between two
    # approaches is shorter than it is with them.
    treeless = dict(foot)
    for tx, ty in C.TREES:
        for j in (1, 2):
            for i in (0, 1):
                treeless[(tx + i, ty + j)] = 'open'
    longer = []
    for k, p in approaches.items():
        a, b = steps(foot, p), steps(treeless, p)
        longer += [(k, k2) for k2, q in approaches.items() if a.get(q, 10 ** 6) > b.get(q, 10 ** 6)]
    assert not longer, ('a tree lengthens a route', longer)
    # Every FireRed warp a new building has not built over (solid now unless it is a door
    # with an interior) still has a reachable cell beside it, as do the new doors. The
    # gates' outer doors (west, east and south) face Routes 7, 8 and 6, outside the walls.
    owner = comp['owner']
    adapted = [(c['x'], c['y']) for c in trav if c.get('adaptation', '').startswith('door or gate warp')]
    frlg_warps = {(w['x'], w['y']) for w in json.loads((g / 'data/maps/SaffronCity_Frlg/map.json').read_text())['warp_events']}
    built_over = {(x, y) for x, y in frlg_warps if str(owner[y, x]) in C.BUILDINGS} - set(C.DOORS.values())
    copycat = tuple(int(v) for v in np.add(C.COPYCAT_HOUSE, (1, 1)))
    must_reach = sorted(frlg_warps - {(22, 14)} - built_over | set(C.DOORS.values()) | {copycat})   # (22, 14): the Copycat's old door, under the station
    for x, y in must_reach:
        assert any(n in seen for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))), ('door out of reach', x, y)
    outer_gate_doors = sorted(p for p in adapted if p not in must_reach)
    assert not any(n in seen for x, y in outer_gate_doors for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))), \
        outer_gate_doors
    # Signs on blocked cells: FireRed's signposts, and the station sign on its door.
    for b in m['bg_events']:
        x, y = b['x'], b['y']
        assert d['coll'][y, x] == 1, ('sign on a walkable cell', x, y)
        assert d['beh'][y, x] == MB['MB_SIGNPOST'] or (x, y) == C.STATION_DOOR, ('sign off a signpost', x, y)
    doors = {(w['x'], w['y']): w['dest_map'] for w in m['warp_events']}
    assert set(doors) == set(P.OPEN_DOORS) and all(foot[p] == 'door' for p in doors), doors
    # The Center and Mart doors animate: FireRed's sliding door on their one metatile, its
    # frames indexed into that metatile's banks, every colour FireRed's.
    door_mid = int(d['mid'][38, 24])
    assert int(d['mid'][21, 40]) == door_mid
    fd = (g / 'src/field_door.c').read_text()
    entry = f'{{.metatileNum={door_mid}, .tileset=&gTileset_KantoSaffronPrimary, .sound=DOOR_SOUND_SLIDING, .size=DOOR_SIZE_1x1, '
    pm = tileset(g / f'data/tilesets/primary/{PFOLDER}')[1]
    banks = [int(e) >> 12 for e in pm[door_mid][:4]]
    assert entry in fd and f'sKantoSaffronDoorPal_Sliding[] = {{{", ".join(map(str, banks + banks))}}};' in fd, 'door entry'
    frlg_door = Image.open(g / 'graphics/door_anims/sliding_single.png')
    fi, fp = np.array(frlg_door), np.array(frlg_door.getpalette()[:48]).reshape(16, 3)
    ni = np.array(Image.open(g / 'graphics/door_anims/kanto_saffron_sliding.png'))
    for f in range(fi.shape[0] // 16):
        for q, b in enumerate(banks):
            sl = np.s_[f * 16 + (q // 2) * 8:f * 16 + (q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            assert ((ni[sl] == 0) == (fi[sl] == 0)).all(), ('door frame', f, q)
            got = np.array(d['pals'][b], int)[ni[sl]] >> 3
            assert (got[fi[sl] > 0] == (fp[fi[sl]] >> 3)[fi[sl] > 0]).all(), ('door frame colour', f, q)
    room_report = rooms(g, m['warp_events'])
    # Budgets: 512 primary tiles and metatiles; 496 secondary tiles (16 kept for door
    # animation), 512 secondary metatiles.
    assert d['prim_tiles'] <= 512 and d['prim_metas'] == 512 and d['sec_metas'] <= 512, d
    assert d['sec_tiles'] <= 496 + 15, d['sec_tiles']             # tiles.png pads its last row of 16
    sec_used = int(json.loads((EV / 'pack.json').read_text())['secondary_tiles'])
    assert sec_used <= 496
    # Preservation: existing map ids keep their order; only Saffron files changed.
    before = json.loads(subprocess.check_output(['git', '-C', str(g), 'show', f'{BASE}:data/maps/map_groups.json']))
    groups = json.loads((g / 'data/maps/map_groups.json').read_text())
    for key, values in before.items():
        assert groups[key][:len(values)] == values, key
    changed = subprocess.check_output(['git', '-C', str(g), 'diff', '--name-only', BASE], text=True).splitlines()
    changed += subprocess.check_output(['git', '-C', str(g), 'ls-files', '--others', '--exclude-standard'], text=True).splitlines()
    allowed = {'data/event_scripts.s', 'data/layouts/layouts.json', 'data/maps/map_groups.json', 'src/apocrypha_map_proof.c',
               'src/data/tilesets/graphics.h', 'src/data/tilesets/headers.h', 'src/data/tilesets/metatiles.h', 'src/field_door.c',
               'graphics/door_anims/kanto_saffron_sliding.png'}
    prefixes = ('data/layouts/KantoSaffron', 'data/maps/KantoSaffron', f'data/tilesets/primary/{PFOLDER}/',
                'data/tilesets/secondary/kanto_saffron_')
    unexpected = sorted(p for p in set(changed) if p not in allowed and not p.startswith(prefixes))
    assert not unexpected, unexpected
    # Coordinate-labelled native grid for review.
    big = Image.fromarray(img).resize((W * 32, H * 32), Image.Resampling.NEAREST); dr = ImageDraw.Draw(big)
    for i in range(W):
        dr.line((i * 32, 0, i * 32, H * 32), fill=(60, 60, 70)); dr.text((i * 32 + 2, 2), str(i), fill='white', stroke_width=1, stroke_fill='black')
    for i in range(H):
        dr.line((0, i * 32, W * 32, i * 32), fill=(60, 60, 70)); dr.text((2, i * 32 + 3), str(i), fill='white', stroke_width=1, stroke_fill='black')
    big.save(EV / 'native-grid.png')
    result = dict(cells_audited=len(trav), installed_matches_compose=True, installed_matches_packer_decode=True,
                  palettes_match_packer=list(P.BANKS), bottom_layer_opaque=True, art_cells=int(art.sum()),
                  ledger_behaviour_collision_elevation_layer=True, frlg_layer_types_outside_parts=True,
                  reachable_foot_cells=len(seen), open_cells=len(open_cells),
                  unreachable_open_cells=sorted(open_cells - seen), approaches=approaches, trees_lengthen_no_route=True,
                  doors_reached=must_reach, frlg_warps_built_over=sorted(built_over), outer_gate_doors=outer_gate_doors,
                  signs=len(m['bg_events']), open_doors={f'{x},{y}': v for (x, y), v in doors.items()},
                  door_metatile=door_mid, door_banks=banks, interiors=room_report,
                  primary_tiles=d['prim_tiles'], secondary_tiles=sec_used, secondary_tile_limit=496,
                  primary_metatiles=d['prim_metas'], secondary_metatiles=d['sec_metas'], metatile_limit=512,
                  existing_map_ids_preserved=True, changed_files_within_scope=True)
    (EV / 'native-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'approaches'}))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
