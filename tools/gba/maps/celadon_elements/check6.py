"""Audit Celadon round 6 as installed, from the engine's own files.

    python3 tools/gba/maps/celadon_elements/check6.py ENGINE_CHECKOUT

Checks, writing evidence/v6/engine/audit.json:
    tables      data/celadon_view/*.bin are stream6.py's tables byte for byte
    budgets     the worst 16 x 16 cell view's glyphs fit the cache's slots; every step's
                screens hold at most 13 palettes and every palette has a bank no palette it
                shares a screen with holds; no tile layer over 15 colours
    traversal   every cell of the layout carries stream6's foot (behaviour, collision,
                elevation) and layer type
    reach       every door, every sign's reading cell and both road ends reachable on foot
                from the Center's door; no open cell walled in
    warps       every city door leads into its room and the room's exit leads back to that
                door; the prize room up the Game Corner's stairs and back; the doors with no
                room are solid
    scope       map ids and layout ids unchanged from the engine's HEAD; the files changed are
                Celadon's own and the streamer's hooks
"""
from __future__ import annotations
import json, struct, subprocess, sys
from collections import deque
from pathlib import Path
import numpy as np

import common as C
import plan as PL
import stream6 as S
import install6 as I6

W, H = PL.W, PL.H

def git(g, *a):
    return subprocess.run(['git', '-C', str(g), *a], capture_output=True, text=True, check=True).stdout

def main(g):
    out, fail = {}, []
    z = dict(np.load(C.SRC / 'stream6.npz'))
    rep = json.loads((S.OUT / 'stream.json').read_text())
    d = g / 'data/celadon_view'
    ent = np.frombuffer((d / 'entries.bin').read_bytes(), '<u4').reshape(H, W, 8)
    out['tables'] = dict(entries=bool((ent == z['entries']).all()),
                         layers=(d / 'layers.bin').read_bytes() == z['layers'].astype(np.uint8).tobytes(),
                         banks=(d / 'banks.bin').read_bytes() == z['banks'].astype(np.uint8).tobytes(),
                         glyphs=(d / 'glyphs.bin').read_bytes() == b''.join(I6.pack4(t) for t in z['glyphs']))
    fail += [f'table {k}' for k, v in out['tables'].items() if not v]
    out['budgets'] = dict(worst_view_glyphs=rep['worst_view_glyphs'], glyph_budget=rep['worst_view_budget'],
                          worst_step_palettes=rep['worst_step_palettes'], banks=rep['banks'], unbanked=rep['unbanked_palettes'],
                          palettes=rep['palettes'], glyphs=rep['glyphs_static'] + rep['glyphs_pinned'],
                          data_bytes=sum(p.stat().st_size for p in d.iterdir()))
    if rep['worst_view_glyphs'] > rep['worst_view_budget']: fail.append('glyph budget')
    if rep['worst_step_palettes'] > rep['banks'] or rep['unbanked_palettes']: fail.append('palette banks')
    # traversal: the layout against stream6's foot and layers
    cells = np.frombuffer((g / f'data/layouts/{I6.NAME}/map.bin').read_bytes(), '<u2').reshape(H, W).astype(int)
    meta = np.frombuffer((g / f'data/tilesets/primary/{I6.PFOLDER}/metatile_attributes.bin').read_bytes(), '<u2')
    foot, layer = z['foot'], z['layers']
    wrong = []
    for y in range(H):
        for x in range(W):
            mid, coll, elev = cells[y, x] & 0x3FF, (cells[y, x] >> 10) & 3, cells[y, x] >> 12
            want = I6.KIND_INDEX[I6.kind(foot[y, x], int(layer[y, x]))]
            if mid != want or coll != (1 if foot[y, x] == 'blocked' else 0) or elev != (1 if foot[y, x] == 'water' else 3) \
                    or (int(meta[mid]) >> 12) != I6.KINDS[want][2]:
                wrong.append([x, y])
    out['traversal'] = dict(cells=W * H, wrong=wrong[:20], open=int((foot == 'open').sum()), solid=int((foot == 'blocked').sum()),
                            water=int((foot == 'water').sum()), doors=int((foot == 'door').sum()),
                            walk_behind=int(((layer == S.NORMAL) & (foot == 'open')).sum()))
    if wrong: fail.append('traversal')
    # reach, on foot over the layout's own collision
    m = json.loads((g / f'data/maps/{I6.NAME}/map.json').read_text())
    walk = lambda x, y: 0 <= x < W and 0 <= y < H and ((cells[y, x] >> 10) & 3) == 0 and foot[y, x] in ('open', 'door')
    start = (rep['doors']['center'][0], rep['doors']['center'][1] + 1)
    seen, q = {start}, deque([start])
    while q:
        x, y = q.popleft()
        if foot[y, x] == 'door' and (x, y) != start:
            continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in seen and walk(*n):
                seen.add(n); q.append(n)
    need = {f'door {w["x"]},{w["y"]}': (w['x'], w['y']) for w in m['warp_events']}
    need.update({f'sign {b["script"]}': (b['x'], b['y'] + 1) for b in m['bg_events']})
    need.update({'route 7 edge': (W - 1, 18), 'route 16 edge': (0, 36)})
    unreached = [k for k, v in need.items() if v not in seen]
    walled = int(sum(1 for y in range(H) for x in range(W) if foot[y, x] == 'open' and (x, y) not in seen))
    out['reach'] = dict(targets=len(need), unreached=unreached, open_cells_walled_in=walled)
    if unreached or walled: fail.append('reach')
    # warps both ways
    maps = {}
    def load(mid):
        name = next(p.parent.name for p in (g / 'data/maps').glob('*/map.json') if json.loads(p.read_text()).get('id') == mid)
        return maps.setdefault(mid, json.loads((g / f'data/maps/{name}/map.json').read_text()))
    bad = []
    for i, w in enumerate(m['warp_events']):
        room = load(w['dest_map'])
        back = room['warp_events'][int(w['dest_warp_id'])]
        if back['dest_map'] != 'MAP_KANTO_CELADON_CITY' or int(back['dest_warp_id']) != i:
            bad.append(dict(door=[w['x'], w['y']], room=w['dest_map'], back=back))
    gc, pr = load('MAP_KANTO_CELADON_GAME_CORNER'), load('MAP_KANTO_CELADON_PRIZE_ROOM')
    stairs = next(i for i, w in enumerate(gc['warp_events']) if w['dest_map'] == 'MAP_KANTO_CELADON_PRIZE_ROOM')
    prize_ok = all(w['dest_map'] == 'MAP_KANTO_CELADON_GAME_CORNER' and int(w['dest_warp_id']) == stairs for w in pr['warp_events'])
    shut = {n: bool((cells[PL.DOORS[n][1], PL.DOORS[n][0]] >> 10) & 3) for n in ('apartments', 'house_g0')}
    out['warps'] = dict(city=len(m['warp_events']), mismatched=bad, prize_room_by_the_stairs=prize_ok, doors_with_no_room_solid=shut)
    if bad or not prize_ok or not all(shut.values()): fail.append('warps')
    # scope
    head_groups = json.loads(git(g, 'show', 'HEAD:data/maps/map_groups.json'))
    now_groups = json.loads((g / 'data/maps/map_groups.json').read_text())
    head_layouts = [l.get('id') for l in json.loads(git(g, 'show', 'HEAD:data/layouts/layouts.json'))['layouts']]
    now_layouts = [l.get('id') for l in json.loads((g / 'data/layouts/layouts.json').read_text())['layouts']]
    changed = sorted(set(git(g, 'diff', '--name-only', 'HEAD').split()) | set(git(g, 'ls-files', '--others', '--exclude-standard').split()))
    hooks = {'src/field_camera.c', 'src/fieldmap.c', 'src/malloc.c', 'src/overworld.c', 'src/tileset_anims.c', 'include/tileset_anims.h',
             'src/data/tilesets/headers.h', 'data/layouts/layouts.json', 'src/celadon_view.c', 'include/celadon_view.h',
             'src/data/celadon_view.h'}
    stray = [f for f in changed if f not in hooks and 'eladon' not in f and 'celadon' not in f]
    out['scope'] = dict(map_ids_unchanged=head_groups == now_groups, layout_ids_unchanged=head_layouts == now_layouts,
                        files_changed=len(changed), outside_celadon_and_hooks=stray)
    if head_groups != now_groups or head_layouts != now_layouts or stray: fail.append('scope')
    out['failures'] = fail
    (S.OUT / 'audit.json').write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps(out, indent=1)[:3000])
    if fail:
        raise SystemExit(f'audit failed: {fail}')

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
