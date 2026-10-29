"""Audit the installed Celadon City (KantoCeladonCity) and its rooms from their native files.

    python3 tools/gba/maps/celadon_elements/check.py ENGINE_CHECKOUT

Decodes data/layouts/KantoCeladonCity with gTileset_KantoCeladonPrimary and
gTileset_KantoCeladonCity as the game composes them (bottom layer, then the top layer's
non-zero pixels) and checks: the picture against compose.py's and the packer's decode, pixel
for pixel in 5-bit colour; the palettes against the packer's; the C06 Center exact where it
stands; the traversal ledger (behaviour, collision, elevation, layer type per cell); every
door, sign, the market, the Gardens' beds and forecourt, both ends of the footbridge and
both road ends reachable on foot, no open cell walled in (the teal house's fenced
garden by the canal is reached by Surf, as in HGSS); the canal's water pond water and the
footbridge walkable; the warps and signs in map.json; every room (its blocks, its exit mats
and stairs, warps both ways); budgets; existing map ids and the file scope.
Writes evidence/native-audit.json and evidence/native-grid.png.
"""
from __future__ import annotations
import json, subprocess, sys
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

import common as C
import build as B
import compose as Cm
import pack as P
import install as I

W, H, SRC, EV = C.W, C.H, C.SRC, C.EV
NAME, PFOLDER, FOLDER = I.NAME, I.PFOLDER, I.FOLDER
C_MAP = I.map_id(NAME)
BASE = 'origin/claude/saffron-city'                 # the engine branch Celadon builds on
STAIRS = ('MB_UP_RIGHT_STAIR_WARP', 'MB_DOWN_RIGHT_STAIR_WARP', 'MB_UP_LEFT_STAIR_WARP', 'MB_DOWN_LEFT_STAIR_WARP')
APPROACHES = dict(plaza_fountain=(17, 27), market_west=(13, 24), market_east=(22, 24), gardens_bed_west=(12, 40),
                  gardens_bed_east=(23, 40), gardens_forecourt=(17, 44), below_the_ledges=(18, 47), bridge_west=(25, 34),
                  bridge_east=(30, 34), bridge_middle=(27, 34), south_east_loop=(42, 40), game_corner_lawn=(36, 21),
                  north_corridor=(33, 4), route7_edge=(59, 16), route16_edge=(0, 34))

def tileset(d):
    a = np.array(Image.open(d / 'tiles.png')) & 15
    tiles = [a[y:y + 8, x:x + 8] for y in range(0, a.shape[0], 8) for x in range(0, a.shape[1], 8)]
    metas = np.frombuffer((d / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
    attrs = np.frombuffer((d / 'metatile_attributes.bin').read_bytes(), '<u2')
    return tiles, metas, attrs

def decode(g):
    prim, sec = g / f'data/tilesets/primary/{PFOLDER}', g / f'data/tilesets/secondary/{FOLDER}'
    pt, pm, pa = tileset(prim)
    st, sm, sa = tileset(sec)
    pals = [B.read_pal((prim if i < 6 else sec) / 'palettes' / f'{i:02}.pal') for i in range(16)]
    tiles = pt[:512] + [np.zeros((8, 8), np.uint8)] * (512 - len(pt[:512])) + st
    metas, attrs = list(pm[:512]) + list(sm), list(pa[:512]) + list(sa)
    blocks = np.frombuffer((g / f'data/layouts/{NAME}/map.bin').read_bytes(), '<u2').reshape(H, W)
    img = np.zeros((H * 16, W * 16, 3), np.uint8)
    beh, layer, coll, elev, mid = (np.zeros((H, W), np.int32) for _ in range(5))
    for y, x in np.ndindex(H, W):
        v = int(blocks[y, x]); m = v & 1023
        mid[y, x], coll[y, x], elev[y, x] = m, (v >> 10) & 3, v >> 12
        beh[y, x], layer[y, x] = int(attrs[m]) & 0xFF, (int(attrs[m]) >> 12) & 3
        for i, e in enumerate(metas[m]):
            e = int(e); t = tiles[e & 1023]
            if e & 1024: t = t[:, ::-1]
            if e & 2048: t = t[::-1]
            q = i % 4; oy, ox = y * 16 + (q // 2) * 8, x * 16 + (q % 2) * 8
            if i < 4:
                img[oy:oy + 8, ox:ox + 8] = np.array(pals[e >> 12], np.uint8)[t]
            else:
                img[oy:oy + 8, ox:ox + 8][t > 0] = np.array(pals[e >> 12], np.uint8)[t[t > 0]]
    return dict(img=img, beh=beh, layer=layer, coll=coll, elev=elev, mid=mid, pals=pals,
                prim_tiles=len(pt), sec_tiles=len(st), prim_metas=len(pm), sec_metas=len(sm))

def rooms(g, city_warps):
    MB = B.behaviors(g)
    mats = {MB['MB_SOUTH_ARROW_WARP']}
    stairs = {MB[s] for s in STAIRS}
    by_id = {I.map_id(n): k for k, (n, _) in I.ROOMS.items()}
    warps_of, out = {}, {}
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
                oz, ow = warps_of[by_id[wv['dest_map']]]
                land = ow[int(wv['dest_warp_id'])]
                assert z['behaviour'][y, x] in stairs and oz['behaviour'][land['y'], land['x']] in stairs, (name, 'stairs', wv)
                assert land['dest_map'] == I.map_id(name), (name, 'stairs back', wv)
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
    comp = np.load(SRC / 'elements/compose.npz')
    want = Cm.preview(comp['bottom'], comp['top'], comp['shared'])
    assert (B.rgb5(img) == B.rgb5(want)).all(), 'installed map differs from compose.py'
    built = np.array(Image.open(EV / 'native.png').convert('RGB'))
    assert (B.rgb5(img) == B.rgb5(built)).all(), 'installed map differs from the packer decode'
    pk = np.load(SRC / 'elements/pack.npz')
    for b in range(13):
        assert [tuple(v >> 3 for v in c) for c in d['pals'][b]] == [tuple(int(v) >> 3 for v in c) for c in pk['palettes'][b]], ('bank', b)
    c06 = np.array(Image.open(SRC / 'shared-art/pokemon-center.png').convert('RGBA'))
    ox, oy = Cm.CENTER_ORIGIN[0] * 16, Cm.CENTER_ORIGIN[1] * 16
    a = c06[..., 3] > 0
    shown = img[oy:oy + c06.shape[0], ox:ox + c06.shape[1]]
    assert (B.rgb5(shown[a]) == B.rgb5(c06[..., :3][a])).all(), 'C06 changed'
    trav = json.loads((SRC / 'elements/traversal.json').read_text())
    for c in trav:
        x, y = c['x'], c['y']
        assert d['beh'][y, x] == c['behavior_id'], (x, y, c['behavior'])
        assert d['coll'][y, x] == c['collision'] and d['elev'][y, x] == c['elevation'], (x, y)
        assert d['layer'][y, x] == (0 if c['layer'] == 'normal' else 1), (x, y)
    foot = {(c['x'], c['y']): c['foot'] for c in trav}
    def reach(surf):
        ok = ('open', 'door', 'water') if surf else ('open', 'door')
        seen, q = {P.START}, deque([P.START])
        while q:
            x, y = q.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if n in seen or n not in foot:
                    continue
                if foot[n] in ok:
                    seen.add(n); q.append(n)
                elif foot[n] == 'ledge_south' and dy == 1 and foot.get((n[0], n[1] + 1)) == 'open':
                    seen.add((n[0], n[1] + 1)); q.append((n[0], n[1] + 1))
        return seen
    seen, with_surf = reach(False), reach(True)
    open_cells = {k for k, v in foot.items() if v in ('open', 'door')}
    approaches = dict(APPROACHES)
    for p, name in P.DOORS.items():
        approaches[f'door_{name}'] = p
    for k, p in approaches.items():
        assert p in seen, ('unreachable', k, p)
    m = json.loads((g / f'data/maps/{NAME}/map.json').read_text())
    for bg in m['bg_events']:
        x, y = bg['x'], bg['y']
        side = next((n for n in ((x, y + 1), (x, y - 1), (x - 1, y), (x + 1, y)) if n in seen), None)
        assert side, ('sign out of reach', bg['script'])
        assert d['coll'][y, x] == 1, ('sign on an open cell', bg['script'])
        approaches[f'sign_{bg["script"].split("_", 1)[1]}'] = side
    MB = B.behaviors(g)
    cells = json.loads((SRC / 'elements/cells.json').read_text())
    for y, x in np.ndindex(H, W):
        f = cells[y][x]['floor']
        if f == 'water':
            assert d['beh'][y, x] == MB['MB_POND_WATER'] and d['coll'][y, x] == 0, ('canal water', x, y)
        if f == 'bridge':
            assert d['coll'][y, x] == 0 and (x, y) in seen, ('bridge deck', x, y)
    water = [k for k, v in foot.items() if v == 'water']
    doors = {(w['x'], w['y']): w['dest_map'] for w in m['warp_events']}
    assert set(doors) == set(P.DOORS) and all(d['beh'][y, x] == MB['MB_ANIMATED_DOOR'] for x, y in doors), doors
    room_report = rooms(g, m['warp_events'])
    assert d['prim_tiles'] <= 512 and d['prim_metas'] == 512 and d['sec_metas'] <= 512, d
    report = json.loads((EV / 'pack.json').read_text())
    assert report['secondary_tiles'] <= P.SECONDARY_TILES and report['colour_rgb5']['worst'] == 0
    before = json.loads(subprocess.check_output(['git', '-C', str(g), 'show', f'{BASE}:data/maps/map_groups.json']))
    groups = json.loads((g / 'data/maps/map_groups.json').read_text())
    for key, values in before.items():
        assert groups[key][:len(values)] == values, key
    changed = subprocess.check_output(['git', '-C', str(g), 'diff', '--name-only', BASE], text=True).splitlines()
    changed += subprocess.check_output(['git', '-C', str(g), 'ls-files', '--others', '--exclude-standard'], text=True).splitlines()
    allowed = {'data/event_scripts.s', 'data/layouts/layouts.json', 'data/maps/map_groups.json', 'src/apocrypha_map_proof.c',
               'src/data/tilesets/graphics.h', 'src/data/tilesets/headers.h', 'src/data/tilesets/metatiles.h'}
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
                  palettes_match_packer=True, c06_exact=True, ledger_behaviour_collision_elevation_layer=True,
                  reachable_foot_cells=len(seen), open_cells=len(open_cells), surf_only_cells=sorted(open_cells - seen),
                  unreachable_open_cells=sorted(open_cells - with_surf),
                  canal_water_cells=len(water), bridge_walkable=True, approaches=approaches, signs=len(m['bg_events']),
                  doors={f'{x},{y}': v for (x, y), v in doors.items()}, interiors=room_report,
                  primary_tiles=d['prim_tiles'], secondary_tiles=report['secondary_tiles'], secondary_tile_limit=P.SECONDARY_TILES,
                  primary_metatiles=d['prim_metas'], secondary_metatiles=d['sec_metas'], colours=report['colours'],
                  existing_map_ids_preserved=True, changed_files_within_scope=True)
    (EV / 'native-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    assert not result['unreachable_open_cells'], result['unreachable_open_cells']
    print(json.dumps({k: v for k, v in result.items() if k not in ('approaches', 'surf_only_cells', 'unreachable_open_cells', 'interiors')}))
    print('unreachable open cells', len(result['unreachable_open_cells']), '; reached only by Surf', len(result['surf_only_cells']),
          '(the teal house\'s fenced garden by the canal, as in HGSS)')

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
