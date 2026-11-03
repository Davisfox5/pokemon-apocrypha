"""Audit the installed Ice Path and its wiring on Route 44 and Blackthorn, from the native files.

    python3 tools/gba/maps/ice_path/check.py ENGINE_CHECKOUT

Per floor: the decode with gTileset_IcePathPrimary / gTileset_IcePath equals the packer's image on
every pixel; behaviour, collision, elevation and layer per cell equal the ledger; Gen 3 movement
(dark_cave/check.py gen3_reach, ice counted as open floor; the slide itself is walked in mGBA)
reaches exactly the ledger's cells from the floor's warps, and HGSS's own permissions reach the
same cells, with B1F's holes counted as HGSS's script triggers. Warps pair back (a ladder's second
HGSS cell points at its first cell's partner, as in HGSS). B1F's four boulders reveal B2F's four
fallen boulders (trainer_type flag = the B2F boulder's flag); IcePath_1F hides them once. Route 44
and Blackthorn: decodes equal BASE's on every pixel; map.bin differs only at the mouth cell's
collision, metatile_attributes.bin only at the mouth metatile's behaviour, map.json only by one
appended warp. Budgets, and the changed file list. Writes evidence/audit.json.
"""
from __future__ import annotations
import importlib.util, json, re, subprocess, sys, tempfile
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
ART = ROOT / 'gba/art/ice-path'
SRC, EV = ART / 'source', ART / 'evidence'
decode = DC.decode
ROUTES = {'Route44': ('mahogany', 'route_44', 96, 32), 'BlackthornCity': ('cherrygrove', 'blackthorn_city', 64, 64)}

def hgss_reach(side, starts):
    perm = np.load(SRC / f'hgss/{side}/hgss-permissions.npz')
    t, k = perm['types'], perm['collision']
    H, W = t.shape
    holes = set(I.DROPS and [h for h, _ in I.DROPS]) if side == 'b1f' else set()
    ok = lambda x, y: 0 <= x < W and 0 <= y < H and ((x, y) in holes or (not k[y, x] & 0x80 and not (t[y, x] == 0 and k[y, x] == 0)))
    seen, q = set(starts), list(starts)
    while q:
        x, y = q.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in seen and ok(*n):
                seen.add(n); q.append(n)
    return seen

def main(g):
    names = {v: k for k, v in P.behaviors(g).items()}
    fails, report = [], dict(maps={}, routes={})
    need = lambda ok, what: ok or fails.append(what)
    maps, decoded = {}, {}
    for side, name in I.MAPS.items():
        w, h = P.SIZE[side]
        d = decoded[name] = DC.decode(g, name, 'ice_path', 'ice_path', w, h)
        maps[name] = json.loads((g / f'data/maps/{name}/map.json').read_text())
        native = np.array(Image.open(EV / f'{side}-native.png').convert('RGB'))
        diff = int((d['img'] != native).any(-1).sum())
        need(diff == 0, f'{side}: decode differs from the packer on {diff} px')
        trav = json.loads((SRC / f'pack/traversal-{side}.json').read_text())
        bad = [(c['x'], c['y']) for c in trav
               if (names[int(d['beh'][c['y'], c['x']])], int(d['coll'][c['y'], c['x']]), int(d['elev'][c['y'], c['x']]),
                   int(d['layer'][c['y'], c['x']])) != (c['behavior'], c['collision'], c['elevation'], 1)]
        need(not bad, f'{side}: cells differ from the ledger {bad[:10]}')
        starts = [(wv['x'], wv['y']) for wv in maps[name]['warp_events']]
        walked, surfed = DC.gen3_reach(names, d['beh'], d['coll'], d['elev'], starts)
        led = DC.ledger_reach(trav, starts)
        hg = hgss_reach(side, starts)
        need(walked | surfed == led, f'{side}: Gen 3 reach differs from the ledger {sorted((walked | surfed) ^ led)[:8]}')
        need(led == hg, f'{side}: reach differs from HGSS +{sorted(led - hg)[:6]} -{sorted(hg - led)[:6]}')
        kinds = {}
        for c in trav:
            kinds[c['kind']] = kinds.get(c['kind'], 0) + 1
        report['maps'][name] = dict(decode_px_differing=diff, cells_differing_from_ledger=len(bad), reach_cells=len(led),
                                    hgss_reach_cells=len(hg), kinds=kinds, warps=len(starts), tiles=d['tiles'], metatiles=d['metas'])
    for r in ROUTES:
        maps[r] = json.loads((g / f'data/maps/{r}/map.json').read_text())
    by_id = {I.IDS[n]: n for n in list(I.MAPS.values()) + list(ROUTES)}
    for n, m in maps.items():
        for i, wv in enumerate(m['warp_events']):
            if wv['dest_map'] not in by_id:
                continue
            other = maps[by_id[wv['dest_map']]]
            back = other['warp_events'][int(wv['dest_warp_id'])]
            pairs = by_id.get(back['dest_map']) == n and int(back['dest_warp_id']) == i
            if not pairs and by_id.get(back['dest_map']) == n:
                twin = m['warp_events'][int(back['dest_warp_id'])]   # a ladder's second HGSS cell
                pairs = abs(twin['x'] - wv['x']) + abs(twin['y'] - wv['y']) == 1 and twin['dest_map'] == wv['dest_map']
            need(pairs, f'{n} warp {i} does not pair back')
    for n in I.MAPS.values():
        d = decoded[n]
        for wv in maps[n]['warp_events']:
            beh = names[int(d['beh'][wv['y'], wv['x']])]
            arrival = n == 'IcePath_B2F' and (wv['x'], wv['y']) in [a for _, a in I.DROPS]
            ok = beh in ('MB_SOUTH_ARROW_WARP', 'MB_LADDER', 'MB_MT_PYRE_HOLE') or (arrival and beh in ('MB_ICE', 'MB_CAVE'))
            need(ok and d['coll'][wv['y'], wv['x']] == 0, f'{n} warp at {(wv["x"], wv["y"])}: {beh}')
    b1 = {o['trainer_type']: (o['x'], o['y']) for o in maps['IcePath_B1F']['object_events'] if o['trainer_type'].startswith('FLAG_')}
    b2 = {o['flag']: (o['x'], o['y']) for o in maps['IcePath_B2F']['object_events']}
    need(set(b1) == set(b2) and len(b1) == 4, f'boulder flags B1F {sorted(b1)} B2F {sorted(b2)}')
    scr = (g / 'data/maps/IcePath_1F/scripts.inc').read_text()
    need(all(f'setflag {f}' in scr for f in b2) and 'MAP_SCRIPT_ON_TRANSITION' in scr, '1F hides the fallen boulders once')
    holes = [(int(x), int(y)) for y, x in np.argwhere(np.vectorize(lambda v: names[int(v)])(decoded['IcePath_B1F']['beh']) == 'MB_MT_PYRE_HOLE')]
    need(sorted(holes) == sorted(h for h, _ in I.DROPS), f'B1F holes {holes}')
    report['boulders'] = dict(b1f=b1, b2f=b2, holes=holes)
    with tempfile.TemporaryDirectory() as tmp:
        for r, ((cx, cy), mid, folder, _) in I.MOUTHS.items():
            pf, sf, ww, hh = ROUTES[r]
            rels = [f'data/layouts/{r}/map.bin', f'data/maps/{r}/map.json'] + \
                   [f'{dd}/{f}' for dd in (f'data/tilesets/primary/{pf}', folder) for f in ('tiles.png', 'metatiles.bin', 'metatile_attributes.bin')] + \
                   [f'{dd}/palettes/{b:02}.pal' for dd in (f'data/tilesets/primary/{pf}', folder) for b in range(16)]
            for rel in rels:
                p = Path(tmp) / rel; p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(subprocess.check_output(['git', '-C', str(g), 'show', f'{I.BASE}:{rel}']))
            now, was = DC.decode(g, r, pf, sf, ww, hh), DC.decode(Path(tmp), r, pf, sf, ww, hh)
            px = int((now['img'] != was['img']).any(-1).sum())
            need(px == 0, f'{r}: {px} px changed')
            cells = np.argwhere(now['grid'] != was['grid'])
            need([tuple(c[::-1]) for c in cells] == [(cx, cy)] and int(now['grid'][cy, cx]) == int(was['grid'][cy, cx]) & ~0xC00,
                 f'{r}: map.bin changes {cells.tolist()}')
            a_now = np.frombuffer((g / folder / 'metatile_attributes.bin').read_bytes(), '<u2')
            a_was = np.frombuffer((Path(tmp) / folder / 'metatile_attributes.bin').read_bytes(), '<u2')
            ch = np.nonzero(a_now != a_was)[0].tolist()
            need(ch == [mid - 512] and names[int(a_now[mid - 512]) & 0xFF] == 'MB_NON_ANIMATED_DOOR', f'{r}: attribute changes {ch}')
            mj_was = json.loads((Path(tmp) / f'data/maps/{r}/map.json').read_text())
            mj_now = dict(maps[r]); wn = mj_now.pop('warp_events'); ww_ = mj_was.pop('warp_events')
            need(mj_now == mj_was and wn[:-1] == ww_ and (wn[-1]['x'], wn[-1]['y']) == (cx, cy), f'{r}: map.json changes beyond its warp')
            report['routes'][r] = dict(pixels_changed=px, cell=[cx, cy], metatile=mid, collision=int(now['coll'][cy, cx]), warp=wn[-1])
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
    print(json.dumps(dict(failures=fails, maps={k: {kk: v[kk] for kk in ('reach_cells', 'hgss_reach_cells', 'kinds')} for k, v in report['maps'].items()},
                          routes={k: v['pixels_changed'] for k, v in report['routes'].items()})))
    assert not fails, fails

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
