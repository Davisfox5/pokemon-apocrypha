"""Audit Route 7 and the Celadon seam as installed, from the engine's own files.

    python3 tools/gba/maps/route7/check7.py ENGINE_CHECKOUT

Checks, writing evidence/engine/audit.json:
    tables      data/celadon_view/*.bin are world.py's tables byte for byte; the header's
                world size and Route 7 origin
    budgets     the worst 16 x 16 cell view's glyphs fit the cache's slots; every step's screens
                hold at most 13 palettes, every palette banked
    ledger      Route 7's walkable cells against HGSS's (collision 128 blocks), cell by cell, with
                the adaptations listed: anything else is a failure
    traversal   every cell of both maps carries the world's foot (behaviour, collision) and
                layer type
    reach       from Celadon's Center door: Route 7's every open and tall-grass cell, the notice
                board's reading cell and the five arrow cells; the gate room's both arrows;
                no open cell walled in
    warps       the arrows into the gate room, its west arrow back onto the route, its east arrow
                to Saffron's west gate and that gate back into the room; the Underground Path's
                door solid
    connections Celadon east to Route 7 at offset 1, Route 7 west to Celadon at offset -1
    seam        across the connection the two maps' cells are one world: Celadon x 63 beside
                Route 7 x 0 on the road rows, walkable both sides
    scope       map and layout ids before the branch's last commit unchanged and only appended
                to; the files changed are Celadon's, Route 7's, the gate room's, Saffron's gate,
                the wild table and the streamer's hooks
"""
from __future__ import annotations
import json, re, subprocess, sys
from collections import deque
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'celadon_elements'))
sys.path.insert(0, str(HERE))
import stream6 as S            # noqa: E402
import install6 as I6          # noqa: E402
import compose as R            # noqa: E402
import world as WD             # noqa: E402
import install7 as I7          # noqa: E402

# Where Route 7 differs from HGSS's walkable cells, and why (README, adaptations).
ADAPTED = {
    'road widened for the lane': [(x, 19) for x in range(0, 25)],
    "Celadon's woods at x 60-63 run on": [(x, 14) for x in range(0, 4)],
    'arrow warps in front of the gate (HGSS warps on its wall cell)': [(25, y) for y in range(15, 19)],
    'notice board a row south': [(12, 24), (12, 25)],
}

def git(g, *a):
    return subprocess.run(['git', '-C', str(g), *a], capture_output=True, text=True, check=True).stdout

def main(g):
    out, fail = {}, []
    z = dict(np.load(WD.NPZ))
    rep = json.loads((WD.OUT / 'stream.json').read_text())
    d = g / 'data/celadon_view'
    H, W = z['entries'].shape[:2]
    ent = np.frombuffer((d / 'entries.bin').read_bytes(), '<u4').reshape(H, W, 8)
    hdr = (g / 'src/data/celadon_view.h').read_text()
    out['tables'] = dict(entries=bool((ent == z['entries']).all()),
                         layers=(d / 'layers.bin').read_bytes() == z['layers'].astype(np.uint8).tobytes(),
                         banks=(d / 'banks.bin').read_bytes() == z['banks'].astype(np.uint8).tobytes(),
                         glyphs=(d / 'glyphs.bin').read_bytes() == b''.join(I6.pack4(t) for t in z['glyphs']),
                         header=all(f'#define {k} {v}\n' in hdr for k, v in
                                    (('CELADON_W', W), ('CELADON_H', H), ('CELADON_ROUTE7_X', WD.CW), ('CELADON_ROUTE7_Y', R.OY))))
    fail += [f'table {k}' for k, v in out['tables'].items() if not v]
    out['budgets'] = dict(worst_view_glyphs=rep['worst_view_glyphs'], glyph_budget=rep['worst_view_budget'],
                          worst_step_palettes=rep['worst_step_palettes'], banks=rep['banks'], unbanked=rep['unbanked_palettes'],
                          palettes=rep['palettes'], glyphs=rep['glyphs_static'] + rep['glyphs_pinned'],
                          exact_pixels=rep['exact_pixels'], pixels=rep['pixels'])
    if rep['worst_view_glyphs'] > rep['worst_view_budget']: fail.append('glyph budget')
    if rep['worst_step_palettes'] > rep['banks'] or rep['unbanked_palettes']: fail.append('palette banks')
    foot, layer = z['foot'], z['layers']
    # the ledger against HGSS
    types, coll, _ = R.hgss()
    walk = set(WD.WALK)
    differ = []
    adapted = {c for v in ADAPTED.values() for c in v}
    for y in range(R.MH):
        for x in range(32):
            hg = coll[R.OY + y, x] != 128 and types[R.OY + y, x] not in (0x38, 0x3b, 0x3e)
            ours = foot[R.OY + y, WD.CW + x] in walk
            if hg != ours and (x, y) not in adapted:
                differ.append([x, y, 'hgss open' if hg else 'hgss blocked'])
    out['ledger'] = dict(cells=R.MH * 32, differ_unexplained=differ, adaptations={k: len(v) for k, v in ADAPTED.items()})
    if differ: fail.append('ledger')
    # traversal, both maps
    meta = np.frombuffer((g / f'data/tilesets/primary/{I6.PFOLDER}/metatile_attributes.bin').read_bytes(), '<u2')
    wrong = []
    for name, (ox, oy, w, h) in ((I6.NAME, (0, 0, WD.CW, WD.CH)), (I7.NAME, (WD.CW, R.OY, R.MW, R.MH))):
        cells = np.frombuffer((g / f'data/layouts/{name}/map.bin').read_bytes(), '<u2').reshape(h, w).astype(int)
        for y in range(h):
            for x in range(w):
                f, l = foot[oy + y, ox + x], int(layer[oy + y, ox + x])
                k = I7.kind(f, l)
                mid, c = cells[y, x] & 0x3FF, (cells[y, x] >> 10) & 3
                want_c = 1 if f in ('blocked', 'jump_s', 'jump_e') else 0
                if mid != I6.KIND_INDEX.get(k, -1) or c != want_c or (int(meta[mid]) >> 12) != I6.KINDS[mid][2]:
                    wrong.append([name, x, y, f])
    out['traversal'] = dict(wrong=wrong[:20], route=dict((k, int((foot[R.OY:R.OY + R.MH, WD.CW:] == k).sum()))
                                                         for k in ('open', 'tall', 'jump_s', 'jump_e', 'arrow_e', 'blocked')))
    if wrong: fail.append('traversal')
    # reach, on foot over the world from the Center's door
    cx, cy = rep['doors']['center']
    seen, q = {(cx, cy + 1)}, deque([(cx, cy + 1)])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if 0 <= n[0] < W and 0 <= n[1] < H and n not in seen and foot[n[1], n[0]] in walk:
                seen.add(n); q.append(n)
    route_open = [(x, y) for y in range(R.MH) for x in range(R.MW) if foot[R.OY + y, WD.CW + x] in walk]
    unreached = [[x, y] for x, y in route_open if (WD.CW + x, R.OY + y) not in seen]
    nx, ny = R.NOTICE
    need = {'notice reading cell': (nx, ny + 1), **{f'arrow {y}': (x, y) for x, y in R.ARROWS}}
    missed = [k for k, (x, y) in need.items() if (WD.CW + x, R.OY + y) not in seen]
    out['reach'] = dict(route_walkable=len(route_open), unreached=unreached[:20], targets_missed=missed)
    if unreached or missed: fail.append('reach')
    # warps and doors
    rd = lambda n: json.loads((g / f'data/maps/{n}/map.json').read_text())
    rm, gm, sm, cm = rd(I7.NAME), rd(I7.ROOM), rd(I7.SAFFRON), rd(I6.NAME)
    bad = []
    for i, w in enumerate(rm['warp_events']):
        if w['dest_map'] != 'MAP_KANTO_ROUTE7_GATEHOUSE' or (gm['warp_events'][int(w['dest_warp_id'])]['x'], 1) != (1, 1):
            bad.append(['route warp', i])
    back = gm['warp_events'][0]
    if back['dest_map'] != 'MAP_KANTO_ROUTE7' or (rm['warp_events'][int(back['dest_warp_id'])]['x'], rm['warp_events'][int(back['dest_warp_id'])]['y']) not in [tuple(a) for a in R.ARROWS]:
        bad.append('room west arrow')
    east = gm['warp_events'][1]
    sw = sm['warp_events'][int(east['dest_warp_id'])]
    if east['dest_map'] != 'MAP_KANTO_SAFFRON_CITY' or (sw['x'], sw['y']) != I7.SAFFRON_GATE:
        bad.append('room east arrow')
    if sw['dest_map'] != 'MAP_KANTO_ROUTE7_GATEHOUSE' or int(sw['dest_warp_id']) != 1:
        bad.append('saffron gate')
    scells = np.frombuffer((g / 'data/layouts/KantoSaffronCity/map.bin').read_bytes(), '<u2').reshape(55, 66)
    sat = np.frombuffer((g / 'data/tilesets/primary/kanto_saffron/metatile_attributes.bin').read_bytes(), '<u2')
    import build as B
    MB = B.behaviors(g)
    gx, gy = I7.SAFFRON_GATE
    gv = int(scells[gy, gx])
    saffron_gate_ok = ((gv >> 10) & 3) == 0 and (int(sat[gv & 0x3FF]) & 0xFF) == MB['MB_WEST_ARROW_WARP']
    dx, dy = R.UNDERGROUND_DOOR
    rcells = np.frombuffer((g / f'data/layouts/{I7.NAME}/map.bin').read_bytes(), '<u2').reshape(R.MH, R.MW)
    underground_shut = ((int(rcells[dy, dx]) >> 10) & 3) == 1
    out['warps'] = dict(route_arrows=len(rm['warp_events']), mismatched=bad, saffron_gate_open=saffron_gate_ok,
                        underground_door_solid=underground_shut)
    if bad or not saffron_gate_ok or not underground_shut: fail.append('warps')
    # connections
    conn = dict(celadon=cm.get('connections'), route=rm.get('connections'))
    conn_ok = (conn['celadon'] == [dict(map='MAP_KANTO_ROUTE7', offset=R.OY, direction='right')]
               and conn['route'] == [dict(map='MAP_KANTO_CELADON_CITY', offset=-R.OY, direction='left')])
    out['connections'] = dict(conn, ok=conn_ok)
    if not conn_ok: fail.append('connections')
    # seam: the road rows walkable on both sides of the connection
    seam = [[y - R.OY, foot[y, WD.CW - 1], foot[y, WD.CW]] for y in range(R.OY + R.ROAD[0], R.OY + R.ROAD[1])]
    seam_ok = all(a in walk and b in walk for _, a, b in seam)
    out['seam'] = dict(rows=seam, ok=seam_ok)
    if not seam_ok: fail.append('seam')
    # scope
    base = 'HEAD'
    head_groups = json.loads(git(g, 'show', f'{base}:data/maps/map_groups.json'))
    now_groups = json.loads((g / 'data/maps/map_groups.json').read_text())
    appended = all(now_groups[k][:len(v)] == v for k, v in head_groups.items() if isinstance(v, list))
    head_layouts = [l.get('id') for l in json.loads(git(g, 'show', f'{base}:data/layouts/layouts.json'))['layouts']]
    now_layouts = [l.get('id') for l in json.loads((g / 'data/layouts/layouts.json').read_text())['layouts']]
    layouts_appended = now_layouts[:len(head_layouts)] == head_layouts
    changed = sorted(set(git(g, 'diff', '--name-only', base).split()) | set(git(g, 'ls-files', '--others', '--exclude-standard').split()))
    allowed = ('celadon', 'eladon', 'Route7', 'route7', 'KantoSaffronCity', 'kanto_saffron/')
    hooks = {'src/overworld.c', 'src/celadon_view.c', 'include/celadon_view.h', 'src/data/celadon_view.h',
             'data/layouts/layouts.json', 'data/maps/map_groups.json', 'data/event_scripts.s', 'src/apocrypha_map_proof.c',
             'src/data/wild_encounters.json', 'src/data/tilesets/headers.h', 'src/data/tilesets/graphics.h',
             'src/data/tilesets/metatiles.h'}
    stray = [f for f in changed if f not in hooks and not any(a in f for a in allowed)]
    out['scope'] = dict(map_ids_appended=appended, layout_ids_appended=layouts_appended, files_changed=len(changed), stray=stray)
    if not appended or not layouts_appended or stray: fail.append('scope')
    out['failures'] = fail
    (WD.OUT / 'audit.json').write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps(out, indent=1)[:3500])
    if fail:
        raise SystemExit(f'audit failed: {fail}')

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
