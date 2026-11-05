"""Audit the installed Mt. Mortar and its wiring on Route 42, from the native files.

    python3 tools/gba/maps/mt_mortar/check.py ENGINE_CHECKOUT

Per floor: the decode with gTileset_MtMortarPrimary / gTileset_MtMortar equals the packer's image on
every pixel; behaviour, collision, elevation and layer per cell equal the ledger. Reach: Gen 3
movement with every field move (walking, ledges one way, Surf, Waterfall up and the falls' current
down, Rock Climb rides along the climbing wall) from the floor's warps reaches exactly the cells
HGSS's own permissions reach under the same moves (the falls' face counted on neither side: HGSS
climbs it as one step, Gen 3 rides it). Warps pair back (an up-ladder's second HGSS cell points at
its first cell's partner, as in HGSS); every warp cell is a warp behaviour with collision 0. Route 42:
its decode equals BASE's on every pixel; map.bin differs only at the four mouths' collision,
metatile_attributes.bin only at the mouth metatiles' behaviour, map.json only by four appended
warps. Budgets, and the changed file list. 1F back is HGSS's matrix cropped (pack.CROP): its native cell (x, y) is HGSS's (x + 16, y + 5).
Every floor fits Gen 3's map buffer ((width + 15) * (height + 14) <= 10240). Writes evidence/audit.json.
"""
from __future__ import annotations
import importlib.util, json, subprocess, sys, tempfile
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pack as P                                    # noqa: E402
import install as I                                 # noqa: E402
spec = importlib.util.spec_from_file_location('dark_cave_check', HERE.parent / 'dark_cave/check.py')
sys.path.insert(0, str(HERE.parent / 'dark_cave'))
DC = importlib.util.module_from_spec(spec); spec.loader.exec_module(DC)

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/mt-mortar'
SRC, EV = ART / 'source', ART / 'evidence'
ROUTE = ('Route42', 'mahogany', 'route_42', 96, 32)
ROUTES = {ROUTE[0]: ROUTE[1:]}                      # porymap.py and review.py decode Route 42 with these
decode = DC.decode
STEPS = ((1, 0), (-1, 0), (0, 1), (0, -1))

def reach(kind_of, starts, W, H):
    """Field-move reach over cell kinds: 'open', 'water', 'fall' (the falls' face), 'ledge_s/w/e',
    'climb_ns' / 'climb_ew', 'blocked'. Entering the falls northward climbs to the first cell past it;
    any other way in, its current carries the player south past it. A climbing wall is ridden along
    its own axis to the first cell past it, which must be open."""
    inside = lambda x, y: 0 <= x < W and 0 <= y < H
    k = lambda x, y: kind_of(x, y) if inside(x, y) else 'blocked'
    jump = {(0, 1): 'ledge_s', (-1, 0): 'ledge_w', (1, 0): 'ledge_e'}
    q = deque((x, y) for x, y in starts); seen = set(q)
    def go(n):
        if n and n not in seen:
            seen.add(n); q.append(n)
    while q:
        x, y = q.popleft()
        me = k(x, y)
        for dx, dy in STEPS:
            nx, ny = x + dx, y + dy
            nk = k(nx, ny)
            if nk == 'open' or (nk == 'water' and me in ('open', 'water')):
                go((nx, ny))
            elif nk == jump.get((dx, dy)) and me == 'open' and k(nx + dx, ny + dy) == 'open':
                go((nx + dx, ny + dy))
            elif nk == 'fall' and me in ('water', 'fall'):
                sx, sy = nx, ny
                d = (0, -1) if (dx, dy) == (0, -1) else (0, 1)
                while k(sx, sy) == 'fall':
                    sx, sy = sx + d[0], sy + d[1]
                if k(sx, sy) == 'water':
                    go((sx, sy))
            elif nk in ('climb_ns', 'climb_ew') and me == 'open' and (nk == 'climb_ns') == (dx == 0):
                sx, sy = nx, ny
                while k(sx, sy) == nk:
                    sx, sy = sx + dx, sy + dy
                if k(sx, sy) == 'open':
                    go((sx, sy))
    return seen

def hgss_kinds(side):
    perm = np.load(SRC / f'hgss/{side}/hgss-permissions.npz')
    t, c = perm['types'], perm['collision']
    ox, oy = P.OFFSET[side]
    def kind(x, y):
        tt, kk = int(t[y + oy, x + ox]), int(c[y + oy, x + ox])
        if tt == 0x13:
            return 'fall'
        if tt == 0x15:
            return 'water'
        if tt == 0x3B: return 'ledge_s'
        if tt == 0x39: return 'ledge_w'
        if tt == 0x38: return 'ledge_e'
        if tt == 0x4B: return 'climb_ns'
        if tt == 0x4C: return 'climb_ew'
        if kk & 0x80 or (tt == 0 and kk == 0):
            return 'blocked'
        return 'open'
    return kind

def gen3_kinds(names, d):
    beh, coll = d['beh'], d['coll']
    def kind(x, y):
        b = names[int(beh[y, x])]
        if b == 'MB_WATERFALL': return 'fall'
        if b in ('MB_POND_WATER', 'MB_OCEAN_WATER', 'MB_DEEP_WATER'): return 'water'
        if b == 'MB_JUMP_SOUTH': return 'ledge_s'
        if b == 'MB_JUMP_WEST': return 'ledge_w'
        if b == 'MB_JUMP_EAST': return 'ledge_e'
        if b == 'MB_ROCK_CLIMB':
            return CLIMB_AXIS[(x, y)]
        return 'blocked' if coll[y, x] else 'open'
    return kind

DC_FALLS = {}
CLIMB_AXIS = {}

def main(g):
    global DC_FALLS
    sys.path.insert(0, str(HERE))
    DC_FALLS = {'1f-entrance': (38, 52, 13, 22)}
    names = {v: k for k, v in P.behaviors(g).items()}
    fails, report = [], dict(maps={}, routes={})
    need = lambda ok, what: ok or fails.append(what)
    maps, decoded = {}, {}
    for side, name in I.MAPS.items():
        w, h = P.SIZE[side]
        need((w + 15) * (h + 14) <= 10240, f'{side}: {w}x{h} is over Gen 3\'s MAX_MAP_DATA_SIZE')   # fieldmap.h
        d = decoded[name] = DC.decode(g, name, 'mt_mortar', 'mt_mortar', w, h)
        maps[name] = json.loads((g / f'data/maps/{name}/map.json').read_text())
        native = np.array(Image.open(EV / f'{side}-native.png').convert('RGB'))
        diff = int((d['img'] != native).any(-1).sum())
        need(diff == 0, f'{side}: decode differs from the packer on {diff} px')
        trav = json.loads((SRC / f'pack/traversal-{side}.json').read_text())
        bad = [(c['x'], c['y']) for c in trav
               if (names[int(d['beh'][c['y'], c['x']])], int(d['coll'][c['y'], c['x']]), int(d['elev'][c['y'], c['x']]),
                   int(d['layer'][c['y'], c['x']])) != (c['behavior'], c['collision'], c['elevation'], 1)]
        need(not bad, f'{side}: cells differ from the ledger {bad[:10]}')
        perm = np.load(SRC / f'hgss/{side}/hgss-permissions.npz')
        CLIMB_AXIS.clear()
        ox, oy = P.OFFSET[side]
        CLIMB_AXIS.update({(int(x) - ox, int(y) - oy): 'climb_ns' if perm['types'][y, x] == 0x4B else 'climb_ew'
                           for y, x in np.argwhere(np.isin(perm['types'], (0x4B, 0x4C)))})
        starts = [(wv['x'], wv['y']) for wv in maps[name]['warp_events']]
        x0, x1, crest, fy = DC_FALLS.get(side, (0, -1, 0, -1))
        face = {(x, y) for x in range(x0, x1 + 1) for y in range(crest + 1, fy + 1)}
        gk, hk = gen3_kinds(names, d), hgss_kinds(side)
        g3 = reach(gk, starts, w, h) - face
        hg = reach(hk, starts, w, h) - face
        need(g3 == hg, f'{side}: reach differs from HGSS +{sorted(g3 - hg)[:6]} -{sorted(hg - g3)[:6]}')
        walk_only = reach(lambda x, y: 'blocked' if gk(x, y) in ('water', 'fall', 'climb_ns', 'climb_ew') else gk(x, y), starts, w, h)
        kinds = {}
        for c in trav:
            kinds[c['kind']] = kinds.get(c['kind'], 0) + 1
        report['maps'][name] = dict(decode_px_differing=diff, cells_differing_from_ledger=len(bad), reach_cells=len(g3),
                                    hgss_reach_cells=len(hg), reach_on_foot=len(walk_only), kinds=kinds, warps=len(starts),
                                    tiles=d['tiles'], metatiles=d['metas'])
    r, pf, sf, ww, hh = ROUTE
    maps[r] = json.loads((g / f'data/maps/{r}/map.json').read_text())
    by_id = {I.IDS[n]: n for n in list(I.MAPS.values()) + [r]}
    for n, m in maps.items():
        for i, wv in enumerate(m['warp_events']):
            if wv['dest_map'] not in by_id:
                continue
            other = maps[by_id[wv['dest_map']]]
            back = other['warp_events'][int(wv['dest_warp_id'])]
            pairs = by_id.get(back['dest_map']) == n and int(back['dest_warp_id']) == i
            if not pairs and by_id.get(back['dest_map']) == n:
                twin = m['warp_events'][int(back['dest_warp_id'])]   # an up-ladder's second HGSS cell
                pairs = abs(twin['x'] - wv['x']) + abs(twin['y'] - wv['y']) == 1 and twin['dest_map'] == wv['dest_map']
            need(pairs, f'{n} warp {i} does not pair back')
    for n in I.MAPS.values():
        d = decoded[n]
        for wv in maps[n]['warp_events']:
            beh = names[int(d['beh'][wv['y'], wv['x']])]
            need(beh in ('MB_SOUTH_ARROW_WARP', 'MB_LADDER', 'MB_NON_ANIMATED_DOOR') and d['coll'][wv['y'], wv['x']] == 0,
                 f'{n} warp at {(wv["x"], wv["y"])}: {beh}')
    with tempfile.TemporaryDirectory() as tmp:
        rels = [f'data/layouts/{r}/map.bin', f'data/maps/{r}/map.json'] + \
               [f'{dd}/{f}' for dd in (f'data/tilesets/primary/{pf}', f'data/tilesets/secondary/{sf}')
                for f in ('tiles.png', 'metatiles.bin', 'metatile_attributes.bin')] + \
               [f'{dd}/palettes/{b:02}.pal' for dd in (f'data/tilesets/primary/{pf}', f'data/tilesets/secondary/{sf}') for b in range(16)]
        for rel in rels:
            p = Path(tmp) / rel; p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(subprocess.check_output(['git', '-C', str(g), 'show', f'{I.BASE}:{rel}']))
        now, was = DC.decode(g, r, pf, sf, ww, hh), DC.decode(Path(tmp), r, pf, sf, ww, hh)
        px = int((now['img'] != was['img']).any(-1).sum())
        need(px == 0, f'{r}: {px} px changed')
        cells = sorted(tuple(int(v) for v in c[::-1]) for c in np.argwhere(now['grid'] != was['grid']))
        need(cells == sorted(I.MOUTHS) and all(int(now['grid'][y, x]) == int(was['grid'][y, x]) & ~0xC00 for x, y in cells),
             f'{r}: map.bin changes {cells}')
        sd = f'data/tilesets/secondary/{sf}'
        a_now = np.frombuffer((g / sd / 'metatile_attributes.bin').read_bytes(), '<u2')
        a_was = np.frombuffer((Path(tmp) / sd / 'metatile_attributes.bin').read_bytes(), '<u2')
        ch = np.nonzero(a_now != a_was)[0].tolist()
        mids = sorted({mid - 512 for mid, _ in I.MOUTHS.values()})
        need(ch == mids and all(names[int(a_now[k]) & 0xFF] == 'MB_NON_ANIMATED_DOOR' for k in ch), f'{r}: attribute changes {ch}')
        mj_was = json.loads((Path(tmp) / f'data/maps/{r}/map.json').read_text())
        mj_now = dict(maps[r]); wn = mj_now.pop('warp_events'); ww_ = mj_was.pop('warp_events')
        need(mj_now == mj_was and wn[:len(ww_)] == ww_ and sorted((v['x'], v['y']) for v in wn[len(ww_):]) == sorted(I.MOUTHS),
             f'{r}: map.json changes beyond its warps')
        report['routes'][r] = dict(pixels_changed=px, cells=cells, metatiles=sorted({mid for mid, _ in I.MOUTHS.values()}),
                                   warps=wn[len(ww_):])
    changed = sorted(set(subprocess.check_output(['git', '-C', str(g), 'diff', '--name-only', I.BASE]).decode().split()) |
                     set(subprocess.check_output(['git', '-C', str(g), 'ls-files', '--others', '--exclude-standard']).decode().split()))
    allowed = set(I.SHARED_FILES) | set(I.ROUTE_FILES)
    stray = [f for f in changed if f not in allowed and not any(f.startswith(d + '/') for d in I.DRAFT)]
    need(not stray, f'unexpected changed files {stray}')
    report['changed_files'] = changed
    pk = json.loads((EV / 'pack.json').read_text())
    need(pk['primary_tiles'] <= 512 and pk['secondary_tiles'] <= 496 and pk['primary_metatiles'] <= 512, 'over budget')
    report['budget'] = {k: pk[k] for k in ('patterns', 'primary_tiles', 'secondary_tiles', 'metatiles')}
    report['failures'] = fails
    (EV / 'audit.json').write_text(json.dumps(report, indent=2, default=str) + '\n')
    print(json.dumps(dict(failures=fails, maps={k: {kk: v[kk] for kk in ('reach_cells', 'hgss_reach_cells', 'reach_on_foot')}
                                                for k, v in report['maps'].items()},
                          routes={k: v['pixels_changed'] for k, v in report['routes'].items()})))
    assert not fails, fails

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
