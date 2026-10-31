"""Audit the installed Dark Cave and its wiring on Routes 45 and 46, from the native files.

    python3 tools/gba/maps/dark_cave/check.py ENGINE_CHECKOUT

Checks, per Dark Cave map: the decode of data/layouts/<map> with gTileset_DarkCavePrimary /
gTileset_DarkCave equals the packer's native image on every pixel; behaviour, collision,
elevation and layer type per cell equal the traversal ledger; movement as Gen 3 moves
(elevation, ledges one way, Surf) reaches exactly the cells HGSS's own permissions reach, from
the map's exits, with the field obstacles counted apart (Rock Smash, Strength), and joins each exit
to the others exactly as HGSS does (the Route 45 side's ledges run one way: from the hole up from
the Route 31 side, HGSS reaches no way back up to Route 45, and neither does Gen 3); every warp's
pair points back. Routes 45 and 46 (locked): their decodes equal BASE's on every pixel; map.bin
differs from BASE only by the mouth cell's collision, metatile_attributes.bin only by the mouth
metatile's behaviour, map.json only by its one warp. Budgets, and the changed file list.
Writes evidence/audit.json.
"""
from __future__ import annotations
import json, re, subprocess, sys, tempfile
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pack as P                                    # noqa: E402
import install as I                                 # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/dark-cave'
SRC, EV = ART / 'source', ART / 'evidence'
W = H = 64
SIDES = {'route45-side': 'DarkCaveRoute45Side', 'route31-side': 'DarkCaveRoute31Side'}
ROUTES = {'Route45': ('cherrygrove', 'route_45', 32, 160), 'Route46': ('cherrygrove', 'route_46', 32, 70)}

def read_pal(p): return [tuple(map(int, l.split())) for l in p.read_text().replace('\r', '').splitlines()[3:19]]

def tileset(d):
    a = np.array(Image.open(d / 'tiles.png')) & 15
    tiles = [a[y:y + 8, x:x + 8] for y in range(0, a.shape[0], 8) for x in range(0, a.shape[1], 8)]
    metas = np.frombuffer((d / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
    attrs = np.frombuffer((d / 'metatile_attributes.bin').read_bytes(), '<u2')
    return tiles, metas, attrs

def decode(g, layout, pfolder, sfolder, w, h):
    """A layout's map.bin with its tileset pair, composed as the game draws it (a bottom-layer
    index 0 shows the backdrop)."""
    prim, sec = g / f'data/tilesets/primary/{pfolder}', g / f'data/tilesets/secondary/{sfolder}'
    pt, pm, pa = tileset(prim)
    st, sm, sa = tileset(sec)
    pals = [np.array(read_pal((prim if i < 6 else sec) / 'palettes' / f'{i:02}.pal')) for i in range(16)]
    tiles = pt[:512] + [np.zeros((8, 8), np.uint8)] * (512 - len(pt[:512])) + st
    pad = 512 - len(pm[:512])
    metas = list(pm[:512]) + [np.zeros(8, np.uint16)] * pad + list(sm)
    attrs = list(pa[:512]) + [0] * pad + list(sa)
    grid = np.frombuffer((g / f'data/layouts/{layout}/map.bin').read_bytes(), '<u2').reshape(h, w)
    img = np.zeros((h * 16, w * 16, 3), np.uint8)
    beh, layer, coll, elev = (np.zeros((h, w), np.int32) for _ in range(4))
    for y, x in np.ndindex(h, w):
        v = int(grid[y, x]); m = v & 1023
        coll[y, x], elev[y, x] = (v >> 10) & 3, v >> 12
        beh[y, x], layer[y, x] = int(attrs[m]) & 0xFF, (int(attrs[m]) >> 12) & 3
        for i, e in enumerate(metas[m]):
            e = int(e); t = tiles[e & 1023]
            if e & 1024: t = t[:, ::-1]
            if e & 2048: t = t[::-1]
            q = i % 4; oy, ox = y * 16 + (q // 2) * 8, x * 16 + (q % 2) * 8
            sub = img[oy:oy + 8, ox:ox + 8]
            if i >= 4:
                sub[t > 0] = pals[e >> 12][t[t > 0]]
            else:
                sub[:] = np.where(t[..., None] > 0, pals[e >> 12][t], pals[0][0])
    return dict(img=img, beh=beh, layer=layer, coll=coll, elev=elev, grid=grid, tiles=(len(pt), len(st)), metas=(len(pm), len(sm)))

def base_files(g, tmp, rels):
    for rel in rels:
        p = tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(subprocess.check_output(['git', '-C', str(g), 'show', f'{I.BASE}:{rel}']))
    return tmp

def gen3_reach(names, beh, coll, elev, starts, surf=True, blocked=()):
    """Gen 3 movement: a step needs collision 0 and no elevation mismatch (cell elevation not 0
    or 15 and differing from the player's); a ledge jumps one way onto the cell beyond; Surf starts
    from elevation 3 onto surfable water and stops onto an elevation-3 cell. Cells in `blocked`
    (objects) are solid."""
    b = lambda x, y: names[int(beh[y, x])]
    inside = lambda x, y: 0 <= x < W and 0 <= y < H
    mism = lambda e, x, y: e != 0 and elev[y, x] not in (0, 15) and elev[y, x] != e
    water = lambda x, y: b(x, y) in ('MB_POND_WATER', 'MB_OCEAN_WATER')
    jumps = {(0, 1): 'MB_JUMP_SOUTH', (-1, 0): 'MB_JUMP_WEST', (1, 0): 'MB_JUMP_EAST', (0, -1): 'MB_JUMP_NORTH'}
    free = lambda x, y: not coll[y, x] and (x, y) not in blocked
    q = deque((x, y, 'walk', int(elev[y, x])) for x, y in starts)
    seen = set(q)
    walked, surfed = set(), set()
    while q:
        x, y, mode, e = q.popleft()
        (walked if mode == 'walk' else surfed).add((x, y))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if not inside(nx, ny):
                continue
            nxt = None
            if mode == 'walk':
                if b(nx, ny) == jumps[(dx, dy)]:
                    lx, ly = nx + dx, ny + dy
                    if inside(lx, ly) and free(lx, ly) and not mism(e, lx, ly) and not water(lx, ly):
                        nxt = (lx, ly, 'walk', int(elev[ly, lx]))
                elif free(nx, ny) and not mism(e, nx, ny) and not water(nx, ny):
                    nxt = (nx, ny, 'walk', int(elev[ny, nx]))
                elif surf and e == 3 and free(nx, ny) and water(nx, ny):
                    nxt = (nx, ny, 'surf', 1)
            else:
                if free(nx, ny) and water(nx, ny):
                    nxt = (nx, ny, 'surf', 1)
                elif free(nx, ny) and elev[ny, nx] == 3:
                    nxt = (nx, ny, 'walk', 3)
            if nxt and nxt not in seen:
                seen.add(nxt); q.append(nxt)
    return walked, surfed

def hgss_reach(side, starts, surf=True, blocked=()):
    perm = np.load(SRC / f'hgss/{side}/hgss-permissions.npz')
    t, k = perm['types'], perm['collision']
    foot = {}
    for y, x in np.ndindex(H, W):
        v = int(t[y, x])
        foot[(x, y)] = ('ledge_south' if v == 0x3B else 'ledge_west' if v == 0x39 else 'surf' if v == 0x15
                        else 'blocked' if k[y, x] & 0x80 or (v == 0 and k[y, x] == 0) else 'open')
    for c in blocked:
        foot[c] = 'blocked'
    passable = ('open', 'surf') if surf else ('open',)
    seen = set(starts); q = deque(starts)
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if foot.get(n) in passable:
                if n not in seen:
                    seen.add(n); q.append(n)
            elif (foot.get(n), dx, dy) in (('ledge_south', 0, 1), ('ledge_west', -1, 0)):
                land = (x + 2 * dx, y + 2 * dy)
                if foot.get(land) in passable and land not in seen:
                    seen.add(land); q.append(land)
    return seen

def main(g):
    names = {v: k for k, v in P.behaviors(g).items()}
    fails, report = [], dict(maps={}, routes={})
    need = lambda ok, what: ok or fails.append(what)
    maps = {}
    for side, name in SIDES.items():
        d = decode(g, name, 'dark_cave', 'dark_cave', W, H)
        maps[name] = json.loads((g / f'data/maps/{name}/map.json').read_text())
        native = np.array(Image.open(EV / f'{side}-native.png').convert('RGB'))
        diff = int((d['img'] != native).any(-1).sum())
        need(diff == 0, f'{side}: decode differs from the packer on {diff} px')
        trav = json.loads((SRC / f'pack/traversal-{side}.json').read_text())
        bad = [(c['x'], c['y']) for c in trav
               if (names[int(d['beh'][c['y'], c['x']])], int(d['coll'][c['y'], c['x']]), int(d['elev'][c['y'], c['x']]),
                   int(d['layer'][c['y'], c['x']])) != (c['behavior'], c['collision'], c['elevation'], 1)]
        need(not bad, f'{side}: cells differ from the ledger {bad[:10]}')
        exits = [(w['x'], w['y']) for w in maps[name]['warp_events']]
        objs = {(o['x'], o['y']): o['graphics_id'] for o in maps[name]['object_events']}
        unwired = [c for (s, c) in P.UNWIRED if s == side]
        hg_all = hgss_reach(side, exits) - set(unwired)
        walked, surfed = gen3_reach(names, d['beh'], d['coll'], d['elev'], exits)
        g3_all = walked | surfed
        need(g3_all == hg_all, f'{side}: Gen 3 reach differs from HGSS: +{sorted(g3_all - hg_all)[:8]} -{sorted(hg_all - g3_all)[:8]}')
        # each exit from each other, with Surf and every obstacle cleared; and what the obstacles hold back
        joined = {}
        for a in exits:
            w1, s1 = gen3_reach(names, d['beh'], d['coll'], d['elev'], [a])
            hg1 = hgss_reach(side, [a])
            joined[f'{a[0]},{a[1]}'] = [f'{e[0]},{e[1]}' for e in exits if e in w1]
            need([e in w1 for e in exits] == [e in hg1 for e in exits], f'{side}: exits joined from {a} unlike HGSS')
        foot_only = gen3_reach(names, d['beh'], d['coll'], d['elev'], exits, surf=False)[0]
        need(foot_only == hgss_reach(side, exits, surf=False) - set(unwired), f'{side}: foot reach differs from HGSS')
        blocked = gen3_reach(names, d['beh'], d['coll'], d['elev'], exits, blocked=set(objs))
        hg_blocked = hgss_reach(side, exits, blocked=set(objs)) - set(unwired)
        need(blocked[0] | blocked[1] == hg_blocked, f'{side}: reach with the obstacles in place differs from HGSS')
        report['maps'][name] = dict(decode_px_differing=diff, cells_differing_from_ledger=len(bad), exits=exits,
                                    reach_cells=len(g3_all), hgss_reach_cells=len(hg_all), exits_reached_from=joined, walked=len(walked), surfed=len(surfed),
                                    foot_only_cells=len(foot_only),
                                    reach_with_obstacles_in_place=len(blocked[0] | blocked[1]),
                                    held_back_by_obstacles=len(g3_all - (blocked[0] | blocked[1]) - set(objs)),
                                    objects={f'{x},{y}': v for (x, y), v in objs.items()},
                                    unwired={f'{x},{y}': next(v for (s, c), v in P.UNWIRED.items() if c == (x, y)) for x, y in unwired},
                                    tiles=d['tiles'], metatiles=d['metas'])
    # warps pair both ways
    for r in ROUTES:
        maps[r] = json.loads((g / f'data/maps/{r}/map.json').read_text())
    by_id = {I.map_id(n): n for n in maps}
    for n, m in maps.items():
        for i, w in enumerate(m['warp_events']):
            other = maps[by_id[w['dest_map']]]
            back = other['warp_events'][int(w['dest_warp_id'])]
            need(back['dest_map'] == I.map_id(n) and int(back['dest_warp_id']) == i, f'{n} warp {i} does not pair back')
    # behaviours on the warp cells
    for n, m in maps.items():
        for w in m['warp_events']:
            if n in ROUTES:
                pf, sf, ww, hh = ROUTES[n]
                d = decode(g, n, pf, sf, ww, hh)
            else:
                d = decode(g, n, 'dark_cave', 'dark_cave', W, H)
            beh = names[int(d['beh'][w['y'], w['x']])]
            need(beh in ('MB_SOUTH_ARROW_WARP', 'MB_NON_ANIMATED_DOOR') and d['coll'][w['y'], w['x']] == 0,
                 f'{n} warp at {(w["x"], w["y"])}: {beh}')
    # Routes 45 and 46: native wiring edits only
    with tempfile.TemporaryDirectory() as tmp:
        for r, ((cx, cy), mid, folder) in I.MOUTHS.items():
            pf, sf, ww, hh = ROUTES[r]
            rels = [f'data/layouts/{r}/map.bin', f'data/maps/{r}/map.json'] + \
                   [f'{d}/{f}' for d in (f'data/tilesets/primary/{pf}', folder) for f in ('tiles.png', 'metatiles.bin', 'metatile_attributes.bin')] + \
                   [f'{d}/palettes/{b:02}.pal' for d in (f'data/tilesets/primary/{pf}', folder) for b in range(16)]
            base = base_files(g, Path(tmp), rels)
            now, was = decode(g, r, pf, sf, ww, hh), decode(base, r, pf, sf, ww, hh)
            px = int((now['img'] != was['img']).any(-1).sum())
            need(px == 0, f'{r}: {px} px changed')
            cells = np.argwhere(now['grid'] != was['grid'])
            need([tuple(c[::-1]) for c in cells] == [(cx, cy)] and int(now['grid'][cy, cx]) == int(was['grid'][cy, cx]) & ~0xC00,
                 f'{r}: map.bin changes {cells.tolist()}')
            a_now = np.frombuffer((g / folder / 'metatile_attributes.bin').read_bytes(), '<u2')
            a_was = np.frombuffer((base / folder / 'metatile_attributes.bin').read_bytes(), '<u2')
            ch = np.nonzero(a_now != a_was)[0].tolist()
            need(ch == [mid - 512] and names[int(a_now[mid - 512]) & 0xFF] == 'MB_NON_ANIMATED_DOOR'
                 and a_now[mid - 512] >> 12 == a_was[mid - 512] >> 12, f'{r}: attribute changes {ch}')
            mj_was = json.loads((base / f'data/maps/{r}/map.json').read_text())
            mj_now = dict(maps[r]); wn = mj_now.pop('warp_events'); ww_ = mj_was.pop('warp_events')
            need(mj_now == mj_was and ww_ == [] and len(wn) == 1, f'{r}: map.json changes beyond its warp')
            report['routes'][r] = dict(pixels_changed=px, cell=[cx, cy], metatile=mid,
                                       behavior_was=names[int(a_was[mid - 512]) & 0xFF], behavior='MB_NON_ANIMATED_DOOR',
                                       collision_was=int(was['coll'][cy, cx]), collision=int(now['coll'][cy, cx]), warp=wn[0])
    changed = sorted(set(subprocess.check_output(['git', '-C', str(g), 'diff', '--name-only', I.BASE]).decode().split()) |
                     set(subprocess.check_output(['git', '-C', str(g), 'ls-files', '--others', '--exclude-standard']).decode().split()))
    allowed = set(I.SHARED_FILES) | set(I.ROUTE_FILES)
    stray = [f for f in changed if f not in allowed and not any(f.startswith(d + '/') for d in I.DRAFT)]
    need(not stray, f'unexpected changed files {stray}')
    report['changed_files'] = changed
    pk = json.loads((EV / 'pack.json').read_text())
    need(pk['primary_tiles'] <= 512 and pk['secondary_tiles'] <= 496 and pk['primary_metatiles'] <= 512 and pk['secondary_metatiles'] <= 512,
         'over budget')
    report['budget'] = {k: pk[k] for k in ('patterns', 'primary_tiles', 'secondary_tiles', 'metatiles', 'primary_metatiles', 'secondary_metatiles')}
    report['failures'] = fails
    (EV / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(failures=fails, maps={k: {kk: v[kk] for kk in ('reach_cells', 'hgss_reach_cells', 'foot_only_cells', 'held_back_by_obstacles')}
                                                for k, v in report['maps'].items()}, routes=report['routes'])))
    assert not fails, fails

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
