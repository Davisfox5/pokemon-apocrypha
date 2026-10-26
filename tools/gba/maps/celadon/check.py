"""Audit the installed Celadon City (KantoCeladonCity) and its rooms from their native files.

    python3 tools/gba/maps/celadon/check.py ENGINE_CHECKOUT

Decodes data/layouts/KantoCeladonCity with gTileset_KantoCeladonPrimary and
gTileset_KantoCeladonCity exactly as the game composes them (bottom layer, then the top
layer's non-zero pixels) and checks it against compose.py's picture and the packer's decode;
the palettes against the packer's; every bottom-layer pixel opaque; the parts' cells in the
secondary; the traversal ledger (behaviour, collision, elevation, layer type per cell,
FireRed's layer type on every cell FireRed drew); reachability of every door, sign, the
market, the gardens by their north gate and the footbridge; the canal surfable water, the
footbridge walkable; the signs and doors in map.json; the Center's door animation (FireRed's
frames, indexed into the door's banks); every room (its blocks, its exit mats and stairs,
warps both ways); budgets and preservation.
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
sys.path[:0] = [str(HERE), str(HERE.parent / 'saffron'), str(HERE.parent / 'olivine_elements')]
import build as B                                   # noqa: E402
import frlg                                         # noqa: E402
import compose as C                                 # noqa: E402
import pack as P                                    # noqa: E402
import install as I                                 # noqa: E402

ART = ROOT / 'gba/art/celadon-kanto'
SRC, EV = ART / 'source', ART / 'evidence'
W, H = C.W, C.H
NAME, PFOLDER, FOLDER = I.NAME, I.PFOLDER, I.FOLDER
C_MAP = I.map_id(NAME)
START = (48, 12)                                    # in front of the Center door
BASE = 'origin/claude/saffron-city'                 # the engine branch Celadon builds on
STAIRS = ('MB_UP_RIGHT_STAIR_WARP', 'MB_DOWN_RIGHT_STAIR_WARP', 'MB_UP_LEFT_STAIR_WARP', 'MB_DOWN_LEFT_STAIR_WARP')

def tileset(d):
    a = np.array(Image.open(d / 'tiles.png')) & 15
    tiles = [a[y:y + 8, x:x + 8] for y in range(0, a.shape[0], 8) for x in range(0, a.shape[1], 8)]
    metas = np.frombuffer((d / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
    attrs = np.frombuffer((d / 'metatile_attributes.bin').read_bytes(), '<u2')
    return tiles, metas, attrs

def render_blocks(g, blocks):
    """Map blocks drawn with the installed pair as the game composes them (a bottom pixel of
    colour 0 shows frlg.under's fill), with each cell's attributes."""
    prim, sec = g / f'data/tilesets/primary/{PFOLDER}', g / f'data/tilesets/secondary/{FOLDER}'
    pt, pm, pa = tileset(prim)
    st, sm, sa = tileset(sec)
    pals = [B.read_pal((prim if i < 6 else sec) / 'palettes' / f'{i:02}.pal') for i in range(16)]
    tiles = pt[:512] + [np.zeros((8, 8), np.uint8)] * (512 - len(pt[:512])) + st
    metas, attrs = list(pm[:512]) + list(sm), list(pa[:512]) + list(sa)
    h, w = blocks.shape
    img = np.zeros((h * 16, w * 16, 3), np.uint8)
    beh, layer, coll, elev, mid = (np.zeros((h, w), np.int32) for _ in range(5))
    hole = np.zeros((h * 16, w * 16), bool)
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
    border = np.frombuffer((g / f'data/layouts/{NAME}/border.bin').read_bytes(), '<u2').reshape(2, 2)
    return render_blocks(g, border)['img']

def reach(foot, start=START):
    seen = {start}; q = deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if foot.get(n) in ('open', 'door') and n not in seen:
                seen.add(n); q.append(n)
    return seen

def rooms(g, city_warps):
    """Each room: installed blocks as interiors.py packed them; every warp back to the city
    names a city warp that leads into this room; every city door into it lands on an exit
    mat; the hotel's stairs land on stairs both ways."""
    MB = B.behaviors(g)
    mats = {MB['MB_SOUTH_ARROW_WARP']}
    stairs = {MB[s] for s in STAIRS}
    by_id = {I.map_id(n): k for k, (n, _) in I.ROOMS.items()}
    warps_of = {}
    out = {}
    for key, (name, _) in I.ROOMS.items():
        z = np.load(SRC / f'interiors/{key}.npz')
        h, w = z['grid'].shape
        blocks = np.frombuffer((g / f'data/layouts/{name}/map.bin').read_bytes(), '<u2').reshape(h, w)
        assert (blocks == z['grid']).all(), (name, 'blocks')
        warps_of[key] = (z, json.loads((g / f'data/maps/{name}/map.json').read_text())['warp_events'])
    for key, (z, warps) in warps_of.items():
        name = I.ROOMS[key][0]
        for wv in warps:
            x, y = wv['x'], wv['y']
            if wv['dest_map'] == C_MAP:
                cw = city_warps[int(wv['dest_warp_id'])]
                assert cw['dest_map'] == I.map_id(name), (name, 'warp back', wv)
            else:
                other = by_id[wv['dest_map']]
                oz, ow = warps_of[other]
                land = ow[int(wv['dest_warp_id'])]
                assert z['behaviour'][y, x] in stairs and oz['behaviour'][land['y'], land['x']] in stairs, (name, 'stairs', wv)
                assert ow[int(wv['dest_warp_id'])]['dest_map'] == I.map_id(name), (name, 'stairs back', wv)
        for cw in city_warps:
            if cw['dest_map'] == I.map_id(name):
                land = warps[int(cw['dest_warp_id'])]
                assert z['behaviour'][land['y'], land['x']] in mats and z['collision'][land['y'], land['x']] == 0, (name, 'landing', land)
        out[name] = dict(size=[int(z['grid'].shape[1]), int(z['grid'].shape[0])], warps=len(warps),
                         tiles=int(len(z['tiles'])), metatiles=int(len(z['meta'])))
    return out

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
    # An art cell draws a secondary metatile, or a primary one it is identical to (pack.py shares equal metatiles).
    shared_art = int((d['mid'][art] < 512).sum())
    assert not d['transparent_bottom'], 'a bottom-layer pixel of colour 0'
    trav = json.loads((SRC / 'traversal.json').read_text())
    for c in trav:
        x, y = c['x'], c['y']
        assert d['beh'][y, x] == c['behavior'], (x, y, c['behavior'])
        assert d['coll'][y, x] == c['collision'] and d['elev'][y, x] == c['elevation'], (x, y)
        assert d['layer'][y, x] == (0 if c['layer'] == 'normal' else 1), (x, y)
    for y, x in np.ndindex(H, W):
        if not art[y, x]:
            assert d['layer'][y, x] == pair.layer_type(int(comp['edited'][y, x]) & 0x3FF), ('layer type', x, y)
    MB = B.behaviors(g)
    foot = {}
    for c in trav:
        k = (c['x'], c['y'])
        foot[k] = 'door' if c['behavior'] == MB['MB_ANIMATED_DOOR'] else 'open' if c['collision'] == 0 and \
            c['behavior'] != MB['MB_POND_WATER'] else 'blocked'
    seen = reach(foot)
    open_cells = {k for k, v in foot.items() if v in ('open', 'door')}
    m = json.loads((g / f'data/maps/{NAME}/map.json').read_text())
    approaches = {f'door_{k}': (x, y + 1) for k, (x, y) in C.DOORS.items()}
    approaches.update(market=(13, 23), fountain_lawn=(11, 18), pocket_stall=(5, 15), produce_walk=(22, 19),
                      gardens_gate=(5, 25), gardens_forecourt=(12, 32), gardens_south=(10, 36), bridge_west=(24, 24),
                      bridge_east=(29, 25), canal_east_walk=(30, 30), route7_edge=(59, 13), route16_edge=(0, 23))
    for k, p in approaches.items():
        assert p in seen, ('unreachable approach', k, p)
    # every sign has a reachable cell beside it to read it from (most from below; the fenced
    # block's trainer tips from the road above)
    for bg in m['bg_events']:
        x, y = bg['x'], bg['y']
        side = next((n for n in ((x, y + 1), (x, y - 1), (x - 1, y), (x + 1, y)) if n in seen), None)
        assert side, ('sign out of reach', bg['script'])
        approaches[f'sign_{bg["script"].split("_", 1)[1]}'] = side
    # The canal: its water is FireRed's pond water (surfable, not walkable), its rims solid;
    # the footbridge's deck walkable, drawn under the player.
    x0, x1, r0, r1 = C.CANAL
    for y in range(r0, r1 + 1):
        for x in range(x0 + 1, x1):
            if y in C.BRIDGE_ROWS:
                assert d['coll'][y, x] == 0 and d['beh'][y, x] == MB['MB_NORMAL'] and d['layer'][y, x] == 1, ('bridge', x, y)
            else:
                assert d['beh'][y, x] == MB['MB_POND_WATER'], ('canal water', x, y)
    # Doors: every warp a door the player reaches, its interior built; the solid doors solid.
    doors = {(w['x'], w['y']): w['dest_map'] for w in m['warp_events']}
    assert set(doors) == set(C.DOORS.values()) and all(foot[p] == 'door' for p in doors), doors
    for (x, y), why in P.SOLID_DOORS.items():
        assert d['coll'][y, x] == 1 and d['beh'][y, x] != MB['MB_ANIMATED_DOOR'], ('solid door', x, y, why)
    for b in m['bg_events']:
        x, y = b['x'], b['y']
        assert d['coll'][y, x] == 1 and d['beh'][y, x] == MB['MB_SIGNPOST'], ('sign off a signpost', x, y)
    # The Center's door animates: FireRed's sliding door on its metatile, its frames indexed
    # into that metatile's banks, every colour FireRed's.
    cx, cy = C.DOORS['center']
    door_mid = int(d['mid'][cy, cx])
    fd = (g / 'src/field_door.c').read_text()
    entry = f'{{.metatileNum={door_mid}, .tileset=&gTileset_{I.PSYM}, .sound=DOOR_SOUND_SLIDING, .size=DOOR_SIZE_1x1, '
    pm = tileset(g / f'data/tilesets/primary/{PFOLDER}')[1]
    banks = [int(e) >> 12 for e in pm[door_mid][:4]]
    assert entry in fd and f'sKantoCeladonDoorPal_Sliding[] = {{{", ".join(map(str, banks + banks))}}};' in fd, 'door entry'
    frlg_door = Image.open(g / 'graphics/door_anims/sliding_single.png')
    fi, fp = np.array(frlg_door), np.array(frlg_door.getpalette()[:48]).reshape(16, 3)
    ni = np.array(Image.open(g / I.DOOR_PNG))
    for f in range(fi.shape[0] // 16):
        for q, b in enumerate(banks):
            sl = np.s_[f * 16 + (q // 2) * 8:f * 16 + (q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            assert ((ni[sl] == 0) == (fi[sl] == 0)).all(), ('door frame', f, q)
            got = np.array(d['pals'][b], int)[ni[sl]] >> 3
            assert (got[fi[sl] > 0] == (fp[fi[sl]] >> 3)[fi[sl] > 0]).all(), ('door frame colour', f, q)
    room_report = rooms(g, m['warp_events'])
    assert d['prim_tiles'] <= 512 and d['prim_metas'] == 512 and d['sec_metas'] <= 512, d
    assert d['sec_tiles'] <= 496 + 15, d['sec_tiles']
    sec_used = int(json.loads((EV / 'pack.json').read_text())['secondary_tiles'])
    assert sec_used <= 496
    # Preservation: existing map ids keep their order; only Celadon files changed.
    before = json.loads(subprocess.check_output(['git', '-C', str(g), 'show', f'{BASE}:data/maps/map_groups.json']))
    groups = json.loads((g / 'data/maps/map_groups.json').read_text())
    for key, values in before.items():
        assert groups[key][:len(values)] == values, key
    changed = subprocess.check_output(['git', '-C', str(g), 'diff', '--name-only', BASE], text=True).splitlines()
    changed += subprocess.check_output(['git', '-C', str(g), 'ls-files', '--others', '--exclude-standard'], text=True).splitlines()
    allowed = {'data/event_scripts.s', 'data/layouts/layouts.json', 'data/maps/map_groups.json', 'src/apocrypha_map_proof.c',
               'src/data/tilesets/graphics.h', 'src/data/tilesets/headers.h', 'src/data/tilesets/metatiles.h', 'src/field_door.c',
               I.DOOR_PNG}
    prefixes = ('data/layouts/KantoCeladon', 'data/maps/KantoCeladon', f'data/tilesets/primary/{PFOLDER}/',
                'data/tilesets/secondary/kanto_celadon_')
    unexpected = sorted(p for p in set(changed) if p not in allowed and not p.startswith(prefixes))
    assert not unexpected, unexpected
    big = Image.fromarray(img).resize((W * 32, H * 32), Image.Resampling.NEAREST); dr = ImageDraw.Draw(big)
    for i in range(W):
        dr.line((i * 32, 0, i * 32, H * 32), fill=(60, 60, 70)); dr.text((i * 32 + 2, 2), str(i), fill='white', stroke_width=1, stroke_fill='black')
    for i in range(H):
        dr.line((0, i * 32, W * 32, i * 32), fill=(60, 60, 70)); dr.text((2, i * 32 + 3), str(i), fill='white', stroke_width=1, stroke_fill='black')
    big.save(EV / 'native-grid.png')
    result = dict(cells_audited=len(trav), installed_matches_compose=True, installed_matches_packer_decode=True,
                  palettes_match_packer=list(P.BANKS), bottom_layer_opaque=True, art_cells=int(art.sum()),
                  art_cells_sharing_a_primary_metatile=shared_art,
                  ledger_behaviour_collision_elevation_layer=True, frlg_layer_types_outside_parts=True,
                  reachable_foot_cells=len(seen), open_cells=len(open_cells),
                  unreachable_open_cells=sorted(open_cells - seen), approaches=approaches,
                  canal_water_and_bridge=True, signs=len(m['bg_events']),
                  open_doors={f'{x},{y}': v for (x, y), v in doors.items()}, solid_doors={f'{x},{y}': v for (x, y), v in P.SOLID_DOORS.items()},
                  door_metatile=door_mid, door_banks=banks, interiors=room_report,
                  primary_tiles=d['prim_tiles'], secondary_tiles=sec_used, secondary_tile_limit=496,
                  primary_metatiles=d['prim_metas'], secondary_metatiles=d['sec_metas'], metatile_limit=512,
                  existing_map_ids_preserved=True, changed_files_within_scope=True)
    (EV / 'native-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('approaches', 'unreachable_open_cells')}))
    print('unreachable open cells', len(result['unreachable_open_cells']))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
