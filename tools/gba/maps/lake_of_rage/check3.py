"""Audit the installed Lake of Rage, and Route 43 on the shared primary, from their native files.

    python3 tools/gba/maps/lake_of_rage/check3.py ENGINE_CHECKOUT PHG_CHECKOUT

Decodes data/layouts/LakeOfRage and data/layouts/Route43 with their tileset pairs exactly as
the game composes them and checks: each decode equals the pair packer's and its assembled art
on every visible pixel (Route 43's also equals its own earlier native decode, so the repack
changed no pixel); behaviour, collision, elevation and layer type per cell against each
traversal ledger; each seam strip, decoded with the other map's installed tilesets the way
the engine draws a connection, equals its own art; the connection both ways and matching foot
access across the seam; reachability on foot and with Surf; walk-behind layering; budgets;
shared masters byte-identical; only Lake of Rage and Route 43 files changed.

Material audit (docs/GBA_MAP_RECONSTRUCTION.md section 4): every decoded Lake pixel is
classified by colour against vocabularies built from the source masters, never from the
layout's labels, and each cell compared with what HGSS's flat decode shows there. Writes
evidence/pair/{native-audit.json, material-audit.json, native-grid.png}.
"""
from __future__ import annotations
import hashlib, json, subprocess, sys
from collections import Counter, deque
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import build as B                                   # noqa: E402
import pack as P                                    # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/lake-of-rage'
R43 = ROOT / 'gba/art/route-43'
SRC, EV = ART / 'source', ART / 'evidence'
OUT = EV / 'pair'
W, H = 96, 64
BASE = 'origin/claude/route-43'
LAYOUTS = {'lake': ('LakeOfRage', 'route43', 'lake_of_rage', 96, 64), 'route43': ('Route43', 'route43', 'route_43', 32, 64)}
SEAM = {'route43': (0, 0, 32, 7), 'lake': (24, 56, 72, 64)}
OFFSET = 32

def rgba(p): return np.array(Image.open(p).convert('RGBA'))
def c5set(a, m=None):
    a = np.asarray(a)
    px = a[..., :3][a[..., 3] > 0] if a.shape[-1] == 4 and m is None else (a[m] if m is not None else a.reshape(-1, 3))
    return {tuple(c) for c in (px.astype(int) >> 3).tolist()}

# --------------------------------------------------------------------------- native decode
def tileset(d):
    a = np.array(Image.open(d / 'tiles.png')) & 15
    tiles = [a[y:y + 8, x:x + 8] for y in range(0, a.shape[0], 8) for x in range(0, a.shape[1], 8)]
    metas = np.frombuffer((d / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
    attrs = np.frombuffer((d / 'metatile_attributes.bin').read_bytes(), '<u2')
    return tiles, metas, attrs

def decode(g, layout, pfolder, sfolder, w, h, window=None):
    """Decode a layout (or a window x0, y0, x1, y1 of it) with the tileset pair (pfolder, sfolder)."""
    prim, sec = g / f'data/tilesets/primary/{pfolder}', g / f'data/tilesets/secondary/{sfolder}'
    pt, pm, pa = tileset(prim)
    st, sm, sa = tileset(sec)
    pals = [B.read_pal((prim if i < 6 else sec) / 'palettes' / f'{i:02}.pal') for i in range(16)]
    tiles = pt[:512] + [np.zeros((8, 8), np.uint8)] * (512 - len(pt[:512])) + st
    pad = 512 - len(pm[:512])
    metas = list(pm[:512]) + [np.zeros(8, np.uint16)] * pad + list(sm)
    attrs = list(pa[:512]) + [0] * pad + list(sa)
    grid = np.frombuffer((g / f'data/layouts/{layout}/map.bin').read_bytes(), '<u2').reshape(h, w)
    x0, y0, x1, y1 = window or (0, 0, w, h)
    grid = grid[y0:y1, x0:x1]
    hh, ww = grid.shape
    img = np.zeros((hh * 16, ww * 16, 3), np.uint8)
    beh, layer, coll, elev = (np.zeros((hh, ww), np.int32) for _ in range(4))
    for y, x in np.ndindex(hh, ww):
        v = int(grid[y, x]); m = v & 1023
        coll[y, x], elev[y, x] = (v >> 10) & 3, v >> 12
        beh[y, x], layer[y, x] = int(attrs[m]) & 0xFF, (int(attrs[m]) >> 12) & 3
        for i, e in enumerate(metas[m]):
            e = int(e); t = tiles[e & 1023]
            if e & 1024: t = t[:, ::-1]
            if e & 2048: t = t[::-1]
            q = i % 4; oy, ox = y * 16 + (q // 2) * 8, x * 16 + (q % 2) * 8
            mask = t > 0 if i >= 4 else np.ones((8, 8), bool)
            img[oy:oy + 8, ox:ox + 8][mask] = np.array(pals[e >> 12])[t[mask]]
    return img, beh, layer, coll, elev, len(st), len(sm), len(pm)

def reach(foot, surf):
    """Cells reachable from the seam (every open cell of the Lake's bottom row; Route 43 joins
    both its openings), on foot or with Surf as well."""
    starts = [(x, H - 1) for x in range(W) if foot.get((x, H - 1)) in ('open', 'door')]
    seen = set(starts); q = deque(starts)
    passable = ('open', 'door', 'surf') if surf else ('open', 'door')
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if foot.get(n) in passable:
                if n not in seen:
                    seen.add(n); q.append(n)
            elif foot.get(n) == 'ledge_south' and dy == 1 and foot.get((x, y + 2)) in passable and (x, y + 2) not in seen:
                seen.add((x, y + 2)); q.append((x, y + 2))
    return seen

# --------------------------------------------------------------------------- material audit
def vocab():
    from claude_cherrygrove import ground as G
    tex = G.textures()
    sh, la = SRC / 'shared-art', SRC / 'local-art'
    import elements as E
    pieces = E.frlg_pieces(ENGINE)
    ramp = {i for group in ('nine', 'rock', 'inner') for p in pieces[group].values() for i in p.ravel().tolist() if i >= 0}
    grass = c5set(tex[G.GRASS])
    water = set().union(*(c5set(rgba(p)) for p in (sh / 'pond').glob('pond-15-*.png')))
    water |= c5set(rgba(la / 'lake-banks.png')) - grass
    water |= c5set(rgba(la / 'flooded-tree-shadow-small.png')) | c5set(rgba(la / 'flooded-tree-shadow-large.png'))
    return dict(
        lawn=grass | {tuple(np.array(c) >> 3) for c in G.PROFILES[(G.GRASS, G.PATH)][0]},
        road=c5set(tex[G.PATH]) | {tuple(np.array(c) >> 3) for c in G.PROFILES[(G.GRASS, G.PATH)][1]},
        rock={tuple(np.array(E.ROCK_RAMP[i]) >> 3) for i in ramp},
        ledge=set().union(*(c5set(rgba(sh / f'{n}.png')) for n in ('L11', 'L12', 'L13'))),
        water=water, driftwood=c5set(rgba(la / 'driftwood.png')),
        bank=c5set(rgba(la / 'lake-banks.png')),
        crown=c5set(rgba(la / 'flooded-tree-tree-water.png')) | c5set(rgba(la / 'flooded-tree-tree-w.png')),
        tree=c5set(rgba(sh / 'T01.png')), house=c5set(rgba(sh / 'house.png')), sign=c5set(rgba(sh / 'P13.png')))

OBJECTS = ('tree', 'house', 'sign', 'crown')
TERRAIN = ('lawn', 'road', 'rock', 'ledge', 'water', 'driftwood', 'bank')
RIM_MATERIALS = ('wall01_g', 'wall01_d', 'slope')                 # HGSS's lake rim: drawn as the natural bank
MODEL_CLASS = {31: 'sign', 134: 'house', 135: 'house'}
WATER_MATERIALS = ('river', 'river_r', 'pond_un', 'pond_sub')
CROWN_MATERIALS = ('tree_water1', 'tree_water2', 'tree_w12', 'tree_w22')
DRIFT_MATERIALS = ('ki_obj1', 'ki_obj2', 'ki_obj3', 'etc_a')

def hgss_classes(phg, water_cells):
    """Per pixel, what HGSS shows, decoded flat: water, flooded crowns, driftwood, cliffs,
    ledges, trees, lawn or road by its own colours, then its house and sign models. HGSS's lake
    rim (its wall and slope materials within a cell of the water) is the bank class: the native
    draws it as the owner-approved natural bank (owner review, Route 43)."""
    import elements as E
    h, mat, names, rgb = E.topdown(phg)
    nm = np.array(names + ['none'])
    m = nm[np.where(mat >= 0, mat, len(names))]
    rgb = rgb.astype(int)
    cls = np.full((H * 16, W * 16), '', object)
    cls[(rgb[..., 1] > rgb[..., 0] + 20)] = 'lawn'
    cls[(rgb[..., 0] >= rgb[..., 1]) & (rgb[..., 0] > 180) & (rgb[..., 2] < 175)] = 'road'
    cls[np.isin(m, WATER_MATERIALS)] = 'water'
    cls[np.isin(m, DRIFT_MATERIALS)] = 'driftwood'
    cls[np.isin(m, E.ROCK_MATERIALS) & ~np.isin(m, E.LEDGE_MATERIALS)] = 'rock'
    cls[np.isin(m, E.LEDGE_MATERIALS)] = 'ledge'
    cls[np.isin(m, E.TREE_MATERIALS)] = 'tree'
    cls[np.isin(m, CROWN_MATERIALS)] = 'crown'
    near = np.zeros((H, W), bool)
    for x, y in water_cells:
        near[max(0, y - 1):y + 2, max(0, x - 1):x + 2] = True
    cls[np.isin(m, RIM_MATERIALS) & np.repeat(np.repeat(near, 16, 0), 16, 1)] = 'bank'
    own = np.load(SRC / 'hgss/hgss-foreground-owner.npz')['owner']
    models = [b['model'] for b in json.loads((SRC / 'hgss/hgss-render.json').read_text())['buildings']]
    for i, mm in enumerate(models):
        if mm in MODEL_CLASS:
            cls[own == i] = MODEL_CLASS[mm]
    return cls

def material_audit(img, phg, water_cells):
    """Square by square: native classes from decoded colours (each colour votes for every
    vocabulary that holds it), HGSS classes from the flat decode. A terrain cell matches when
    the native's leading terrain material is one HGSS shows there (at least 24 px); an object
    cell when the same kind of object leads in both. Cells where an object leads in one but
    terrain in the other are foreground differences, not counted as matches."""
    v = vocab()
    owner = {}
    for k, s_ in v.items():
        for c in s_:
            owner.setdefault(c, set()).add(k)
    hc = hgss_classes(phg, water_cells)
    c5 = img.astype(int) >> 3
    rows, mism, fg_diff, unknown = [], [], [], Counter()
    for y in range(H):
        for x in range(W):
            px = c5[y * 16:y * 16 + 16, x * 16:x * 16 + 16].reshape(-1, 3)
            votes = Counter()
            for c in map(tuple, px.tolist()):
                o = owner.get(c)
                if o is None:
                    unknown[c] += 1
                for k in o or ():
                    votes[k] += 1
            hv = Counter(hc[y * 16:y * 16 + 16, x * 16:x * 16 + 16].ravel().tolist())
            hv.pop('', None)
            native_obj = max((votes[k] for k in OBJECTS), default=0) >= 128
            hgss_obj = max((hv[k] for k in OBJECTS), default=0) >= 128
            nat_lead = max(OBJECTS if native_obj else TERRAIN, key=lambda k: votes[k])
            h_lead = max(OBJECTS if hgss_obj else TERRAIN, key=lambda k: hv[k])
            if native_obj != hgss_obj:
                status = 'foreground differs'
            elif native_obj:
                status = 'match' if votes[h_lead] >= 64 else 'mismatch'
            else:
                status = 'match' if hv[nat_lead] >= 24 or votes[h_lead] >= 24 else 'mismatch'
            row = dict(cell=[x, y], status=status, native_lead=nat_lead, hgss_lead=h_lead,
                       native=dict(votes.most_common(4)), hgss=dict(hv.most_common(4)))
            rows.append(row)
            if status == 'mismatch':
                mism.append(row)
            elif status == 'foreground differs':
                fg_diff.append(row)
    return rows, mism, fg_diff, unknown

ENGINE = None

def main(g, phg):
    global ENGINE
    ENGINE = g
    MB = B.behaviors(g)
    dec = {m: decode(g, *LAYOUTS[m][:3], *LAYOUTS[m][3:]) for m in LAYOUTS}
    # Each map: installed decode = pair packer decode = assembled art; Route 43 also = its earlier native.
    for m, art in (('lake', ART), ('route43', R43)):
        img = dec[m][0]
        assert (B.rgb5(img) == B.rgb5(np.array(Image.open(OUT / f'{m}-native.png').convert('RGB')))).all(), (m, 'differs from the pair decode')
        z = np.load(art / 'source/assemble/layers.npz')
        want = z['ground'].copy()
        for layer_ in (z['rock'], z['objects']):
            a = layer_[..., 3] > 0
            want[a] = layer_[a, :3]
        assert (B.rgb5(img) == B.rgb5(want)).all(), (m, 'differs from the assembled art')
    r43_before = np.array(Image.open(R43 / 'evidence/pack3/native.png').convert('RGB'))
    assert (B.rgb5(dec['route43'][0]) == B.rgb5(r43_before)).all(), 'Route 43 pixels changed in the repack'
    travs = {'lake': json.loads((SRC / 'pair/traversal.json').read_text()),
             'route43': json.loads((R43 / 'source/pack3/traversal.json').read_text())}
    for m, trav in travs.items():
        _, beh, layer, coll, elev = dec[m][:5]
        for c in trav:
            x, y = c['x'], c['y']
            assert beh[y, x] == MB[c['behavior']], (m, x, y, c['behavior'])
            assert coll[y, x] == c['collision'] and elev[y, x] == c['elevation'], (m, x, y)
            assert layer[y, x] == (0 if c['layer'] == 'normal' else 1), (m, x, y)
    # Seams: each strip drawn with the other map's installed tileset pair.
    seams = {}
    for m, other in (('route43', 'lake'), ('lake', 'route43')):
        layout, _, _, w, h = LAYOUTS[m]
        _, pf, sf, _, _ = LAYOUTS[other]
        x0, y0, x1, y1 = SEAM[m]
        img = decode(g, layout, pf, sf, w, h, window=SEAM[m])[0]
        own = dec[m][0][y0 * 16:y1 * 16, x0 * 16:x1 * 16]
        assert (B.rgb5(img) == B.rgb5(own)).all(), (m, 'seam strip differs under', other, 'tilesets')
        seams[f'{m}_strip_with_{other}_tilesets'] = 'exact'
    lake_map = json.loads((g / 'data/maps/LakeOfRage/map.json').read_text())
    r43_map = json.loads((g / 'data/maps/Route43/map.json').read_text())
    assert lake_map['connections'] == [dict(map='MAP_ROUTE43', direction='down', offset=OFFSET)]
    assert r43_map['connections'] == [dict(map='MAP_LAKE_OF_RAGE', direction='up', offset=-OFFSET)]
    lfoot = {(c['x'], c['y']): c['foot'] for c in travs['lake']}
    rfoot = {(c['x'], c['y']): c['foot'] for c in travs['route43']}
    crossing = [x for x in range(32) if rfoot[(x, 0)] in ('open', 'door') and lfoot[(x + OFFSET, H - 1)] in ('open', 'door')]
    mismatch = [x for x in range(32) if (rfoot[(x, 0)] in ('open', 'door')) != (lfoot[(x + OFFSET, H - 1)] in ('open', 'door'))]
    assert not mismatch, ('foot access differs across the seam', mismatch)
    # Lake reachability, walk-behind, budgets, scope.
    seen, surfed = reach(lfoot, False), reach(lfoot, True)
    open_cells = {k for k, v in lfoot.items() if v in ('open', 'door')}
    approaches = dict(route43_road=(48, 62), lake_sign=(48, 51), guru_house=(56, 58), ledge_top=(22, 48), ledge_below=(22, 50),
                      south_lawn=(26, 54), east_shore=(66, 44), east_clearing=(74, 26), seam_west=(34, 63), seam_east=(50, 63))
    missing = {k: p for k, p in approaches.items() if p not in seen}
    assert not missing, ('unreachable approach', missing)
    water = {k for k, v in lfoot.items() if v == 'surf'}
    by_surf = {k: p for k, p in dict(north_clearing=(25, 3), north_east_clearing=(60, 5), west_house=(17, 12),
                                     west_pocket=(9, 41)).items() if p not in surfed}
    assert not by_surf, ('unreachable with Surf', by_surf)
    z = np.load(SRC / 'assemble/layers.npz')
    top, owner = z['objects'], z['owner']
    walkable = np.array([[lfoot[(x, y)] in ('open', 'door') for x in range(W)] for y in range(H)])
    above = P.above_player(walkable, top, np.zeros_like(top), owner)
    layer = dec['lake'][2]
    walk_behind = Counter()
    for y, x in np.ndindex(H, W):
        assert layer[y, x] == (0 if above[y, x] else 1), ('layer type', x, y)
        if above[y, x]:
            cell = top[y * 16:y * 16 + 16, x * 16:x * 16 + 16][..., 3] > 0
            for o in set(owner[y * 16:y * 16 + 16, x * 16:x * 16 + 16][cell].ravel()) - {''}:
                walk_behind[o.split('_')[0]] += 1
    prov = json.loads((SRC / 'shared-art/provenance.json').read_text())
    shared_ok = {n: hashlib.sha256((SRC / 'shared-art' / n).read_bytes()).hexdigest() == r['sha256']
                 for n, r in prov.items() if isinstance(r, dict) and 'sha256' in r}
    assert all(shared_ok.values()), shared_ok
    budgets = {m: dict(secondary_tiles=dec[m][5], secondary_metatiles=dec[m][6], primary_metatiles=dec[m][7]) for m in dec}
    for b in budgets.values():
        assert b['secondary_tiles'] <= 496 and b['secondary_metatiles'] <= 512 and b['primary_metatiles'] <= 512, b
    before = json.loads(subprocess.check_output(['git', '-C', str(g), 'show', f'{BASE}:data/maps/map_groups.json']))
    groups = json.loads((g / 'data/maps/map_groups.json').read_text())
    for key, values in before.items():
        if isinstance(values, list):
            assert groups[key][:len(values)] == values, key
    changed = subprocess.check_output(['git', '-C', str(g), 'diff', '--name-only', BASE], text=True).splitlines()
    changed += subprocess.check_output(['git', '-C', str(g), 'ls-files', '--others', '--exclude-standard'], text=True).splitlines()
    allowed = {'data/event_scripts.s', 'data/layouts/layouts.json', 'data/maps/map_groups.json', 'include/regions.h',
               'src/apocrypha_map_proof.c', 'src/data/region_map/region_map_sections.json', 'src/data/tilesets/graphics.h',
               'src/data/tilesets/headers.h', 'src/data/tilesets/metatiles.h', 'data/maps/Route43/map.json'}
    prefixes = ('data/layouts/LakeOfRage/', 'data/maps/LakeOfRage/', 'data/tilesets/secondary/lake_of_rage/',
                'data/layouts/Route43/', 'data/tilesets/primary/route43/', 'data/tilesets/secondary/route_43/')
    unexpected = sorted(p for p in set(changed) if p not in allowed and not p.startswith(prefixes))
    assert not unexpected, unexpected
    img = dec['lake'][0]
    rows, mism, fg_diff, unknown = material_audit(img, phg, water)
    (OUT / 'material-audit.json').write_text(json.dumps(dict(
        method=material_audit.__doc__.strip(), cells=len(rows), matches=sum(r['status'] == 'match' for r in rows),
        mismatches=mism, foreground_differs=fg_diff, unclassified_colours={str(k): n for k, n in unknown.most_common(20)},
        per_cell=rows), indent=1) + '\n')
    big = Image.fromarray(img).resize((W * 24, H * 24), Image.Resampling.NEAREST); d = ImageDraw.Draw(big)
    for i in range(W):
        d.line((i * 24, 0, i * 24, H * 24), fill=(60, 60, 70)); d.text((i * 24 + 2, 2), str(i), fill='white', stroke_width=1, stroke_fill='black')
    for i in range(H):
        d.line((0, i * 24, W * 24, i * 24), fill=(60, 60, 70)); d.text((2, i * 24 + 3), str(i), fill='white', stroke_width=1, stroke_fill='black')
    for m_ in mism:
        x, y = m_['cell']
        d.rectangle((x * 24, y * 24, x * 24 + 23, y * 24 + 23), outline=(255, 0, 255), width=2)
    for m_ in fg_diff:
        x, y = m_['cell']
        d.rectangle((x * 24 + 2, y * 24 + 2, x * 24 + 21, y * 24 + 21), outline=(0, 220, 255), width=1)
    big.save(OUT / 'native-grid.png')
    result = dict(lake_and_route43_match_pair_decode_and_assembled_art=True, route43_pixels_unchanged=True,
                  ledger_behaviour_collision_elevation_layer=True, seams=seams, seam_crossing_columns_route43=crossing,
                  connections=dict(lake=lake_map['connections'], route43=r43_map['connections']),
                  reachable_foot_cells=len(seen), open_cells=len(open_cells), unreachable_open_cells=sorted(open_cells - seen),
                  surf_reachable_cells=len(surfed), water_cells=len(water), approaches=approaches,
                  walk_behind_cells=dict(walk_behind), shared_masters_byte_identical=shared_ok, budgets=budgets,
                  existing_map_ids_preserved=True, changed_files_within_scope=True, material_cells=len(rows),
                  material_matches=sum(r['status'] == 'match' for r in rows),
                  material_mismatches=[m_['cell'] for m_ in mism], foreground_differs=[m_['cell'] for m_ in fg_diff])
    (OUT / 'native-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('approaches', 'shared_masters_byte_identical', 'foreground_differs',
                                                                    'unreachable_open_cells')}))
    print('unreachable open cells', len(open_cells - seen), 'foreground differs', len(fg_diff))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
