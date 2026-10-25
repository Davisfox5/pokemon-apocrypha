"""Audit the installed Route 42, and Mahogany Town beside it, from their native files.

    python3 tools/gba/maps/route42/check3.py ENGINE_CHECKOUT PHG_CHECKOUT

Decodes data/layouts/Route42 and data/layouts/MahoganyTown with their installed tileset pairs
exactly as the game composes them (a bottom-layer index 0 shows the backdrop) and checks: Route
42's decode equals the packer's and its assembled art on every pixel; Mahogany's decode, with
the metatiles and tiles appended to its tables, equals its accepted native decode (no Mahogany pixel
changed); every Route 42 pixel Mahogany's tilesets ever draw (assemble.views), decoded with
Mahogany's installed pair the way the engine draws a connection, equals Route 42's; every
Mahogany pixel Route 42's tilesets ever draw equals Mahogany's; the connection both ways and
matching foot access across the seam; behaviour, collision, elevation and layer type per cell
against the traversal ledger; reachability on foot (ledges one way) and with Surf; walk-behind
layering; budgets; shared masters byte-identical; only Route 42 files, Mahogany's connection and
its appended metatiles, and the shared registration files changed.

Material audit (docs/GBA_MAP_RECONSTRUCTION.md section 4): every decoded Route 42 pixel is
classified by colour against vocabularies built from the source masters, never from the
layout's labels, and each cell compared with what HGSS's flat decode shows there. Writes
evidence/pack3/{native-audit.json, material-audit.json, native-grid.png}.
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
import elements as E                                # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route-42'
MAH = ROOT / 'gba/art/mahogany-town'
SRC, EV = ART / 'source', ART / 'evidence'
OUT = EV / 'pack3'
W, H = 96, 32
BASE = 'origin/claude/route-44'
LAYOUTS = {'route42': ('Route42', 'mahogany', 'route_42', 96, 32), 'mahogany': ('MahoganyTown', 'mahogany', 'mahogany_town', 32, 32)}

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

def decode(g, layout, pfolder, sfolder, w, h, grid=None):
    """Decode a layout's map.bin (or the given grid of metatile ids) with the tileset pair
    (pfolder, sfolder). Ids past the pair's tables draw nothing."""
    prim, sec = g / f'data/tilesets/primary/{pfolder}', g / f'data/tilesets/secondary/{sfolder}'
    pt, pm, pa = tileset(prim)
    st, sm, sa = tileset(sec)
    pals = [np.array(B.read_pal((prim if i < 6 else sec) / 'palettes' / f'{i:02}.pal')) for i in range(16)]
    tiles = pt[:512] + [np.zeros((8, 8), np.uint8)] * (512 - len(pt[:512])) + st
    pad = 512 - len(pm[:512])
    metas = list(pm[:512]) + [np.zeros(8, np.uint16)] * pad + list(sm)
    attrs = list(pa[:512]) + [0] * pad + list(sa)
    if grid is None:
        grid = np.frombuffer((g / f'data/layouts/{layout}/map.bin').read_bytes(), '<u2').reshape(h, w)
    hh, ww = grid.shape
    img = np.zeros((hh * 16, ww * 16, 3), np.uint8)
    beh, layer, coll, elev = (np.zeros((hh, ww), np.int32) for _ in range(4))
    for y, x in np.ndindex(hh, ww):
        v = int(grid[y, x]); m = v & 1023
        coll[y, x], elev[y, x] = (v >> 10) & 3, v >> 12
        if m >= len(metas):
            continue
        beh[y, x], layer[y, x] = int(attrs[m]) & 0xFF, (int(attrs[m]) >> 12) & 3
        for i, e in enumerate(metas[m]):
            e = int(e); t = tiles[e & 1023] if (e & 1023) < len(tiles) else np.zeros((8, 8), np.uint8)
            if e & 1024: t = t[:, ::-1]
            if e & 2048: t = t[::-1]
            q = i % 4; oy, ox = y * 16 + (q // 2) * 8, x * 16 + (q % 2) * 8
            sub = img[oy:oy + 8, ox:ox + 8]
            if i >= 4:
                sub[t > 0] = pals[e >> 12][t[t > 0]]
            else:
                sub[:] = np.where(t[..., None] > 0, pals[e >> 12][t], pals[0][0])
    return img, beh, layer, coll, elev, len(st), len(sm), len(pm), grid

def reach(foot, starts, surf):
    """Cells reachable from the seam, on foot (ledges one way) or with Surf as well."""
    seen = set(starts); q = deque(starts)
    passable = ('open', 'door', 'surf') if surf else ('open', 'door')
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if foot.get(n) in passable:
                if n not in seen:
                    seen.add(n); q.append(n)
            else:
                land = (x + 2 * dx, y + 2 * dy)
                if (foot.get(n), dx, dy) in (('ledge_south', 0, 1), ('ledge_west', -1, 0)) and foot.get(land) in passable and land not in seen:
                    seen.add(land); q.append(land)
    return seen

# --------------------------------------------------------------------------- material audit
def vocab():
    from claude_cherrygrove import ground as G
    tex = G.textures()
    sh, la = SRC / 'shared-art', SRC / 'local-art'
    import elements as E
    pieces = E.frlg_pieces(ENGINE)
    ramp = {i for group in ('nine', 'rock', 'inner', 'ledge') for p in pieces[group].values() for i in p.ravel().tolist() if i >= 0}
    grass = c5set(tex[G.GRASS])
    water = set().union(*(c5set(rgba(p)) for p in (sh / 'pond').glob('pond-15-*.png')))
    return dict(
        lawn=grass | {tuple(np.array(c) >> 3) for c in G.PROFILES[(G.GRASS, G.PATH)][0]} | c5set(rgba(la / 'flowers.png')),
        road=c5set(tex[G.PATH]) | {tuple(np.array(c) >> 3) for c in G.PROFILES[(G.GRASS, G.PATH)][1]},
        rock={tuple(np.array(E.ROCK_RAMP[i]) >> 3) for i in ramp} | c5set(rgba(la / 'boulders.png')),
        water=water, bank=c5set(rgba(la / 'water-banks.png')) - grass,
        tall=c5set(rgba(sh / 'G15.png')), stairs=c5set(rgba(sh / 'S04.png')), cave=c5set(rgba(la / 'mt-mortar-mouths.png')),
        cave_floor=c5set(rgba(la / 'cave-floor.png')), gate=c5set(rgba(sh / 'G02.png')),
        tree=c5set(rgba(sh / 'T01.png')), sign=c5set(rgba(sh / 'P13.png')) | c5set(rgba(sh / 'P14.png')))

OBJECTS = ('tree', 'sign', 'gate')
TERRAIN = ('lawn', 'road', 'rock', 'water', 'bank', 'tall', 'stairs', 'cave', 'cave_floor')
WATER_MATERIALS = ('pond_un', 'pond_on', 'pond_edge')
RIM_MATERIALS = ('pond_line',)                                    # HGSS's pond rim: drawn as the natural bank
MODEL_CLASS = {31: 'sign', 32: 'sign', 36: 'gate'}

def hgss_classes(phg):
    """Per pixel, what HGSS shows, decoded flat: water, its rim (the bank class: the native
    draws it as the owner-approved natural bank), tall grass, stairs, the Mt. Mortar
    mouth, cliffs and boulders, trees, lawn or road by its own colours, then its sign models."""
    import elements as E
    h, mat, names, rgb = E.topdown(phg)
    nm = np.array(names + ['none'])
    m = nm[np.where(mat >= 0, mat, len(names))]
    rgb = rgb.astype(int)
    cls = np.full((H * 16, W * 16), '', object)
    cls[(rgb[..., 1] > rgb[..., 0] + 20)] = 'lawn'
    cls[(rgb[..., 0] >= rgb[..., 1]) & (rgb[..., 0] > 180) & (rgb[..., 2] < 175)] = 'road'
    cls[np.isin(m, E.ROCK_MATERIALS) | (m == 'rock01')] = 'rock'
    cls[np.isin(m, WATER_MATERIALS)] = 'water'
    cls[np.isin(m, RIM_MATERIALS)] = 'bank'
    cls[np.isin(m, ('road05', 'road05_sub'))] = 'cave_floor'
    cls[np.char.startswith(m.astype(str), 'egrass')] = 'tall'
    cls[m == 'slope'] = 'stairs'
    cls[m == 'cavehole'] = 'cave'
    cls[np.isin(m, E.TREE_MATERIALS)] = 'tree'
    own = np.load(SRC / 'hgss/hgss-foreground-owner.npz')['owner']
    models = [b['model'] for b in json.loads((SRC / 'hgss/hgss-render.json').read_text())['buildings']]
    for i, mm in enumerate(models):
        if mm in MODEL_CLASS:
            cls[own == i] = MODEL_CLASS[mm]
    return cls

def material_audit(img, phg):
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
    hc = hgss_classes(phg)
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
    r42 = decode(g, *LAYOUTS['route42'])
    mah = decode(g, *LAYOUTS['mahogany'])
    img = r42[0]
    # Route 42: installed decode = packer decode = assembled art.
    assert (B.rgb5(img) == B.rgb5(np.array(Image.open(OUT / 'native.png').convert('RGB')))).all(), 'differs from the pack decode'
    z = np.load(SRC / 'assemble/layers.npz')
    want = z['ground'].copy()
    for layer_ in (z['rock'], z['objects']):
        a = layer_[..., 3] > 0
        want[a] = layer_[a, :3]
    assert (B.rgb5(img) == B.rgb5(want)).all(), 'differs from the assembled art'
    # Mahogany: every pixel as accepted.
    accepted = np.array(Image.open(MAH / 'evidence/pack3/native.png').convert('RGB'))
    assert (B.rgb5(mah[0]) == B.rgb5(accepted)).all(), 'Mahogany pixels changed'
    # The seam, from the installed files: each map's grid drawn with the other's tileset pair.
    view, mview = z['mahogany_view'], z['route_view_of_mahogany']
    seen_r = decode(g, 'Route42', 'mahogany', 'mahogany_town', W, H, grid=r42[8])[0]
    d = (B.rgb5(seen_r) != B.rgb5(img)).any(-1) & view
    assert not d.any(), ('Route 42 pixels Mahogany shows differ under Mahogany\'s tilesets', int(d.sum()))
    seen_m = decode(g, 'MahoganyTown', 'mahogany', 'route_42', 32, 32, grid=mah[8])[0]
    d = (B.rgb5(seen_m) != B.rgb5(mah[0])).any(-1) & mview
    assert not d.any(), ('Mahogany pixels Route 42 shows differ under Route 42\'s tilesets', int(d.sum()))
    r42_map = json.loads((g / 'data/maps/Route42/map.json').read_text())
    mah_map = json.loads((g / 'data/maps/MahoganyTown/map.json').read_text())
    assert r42_map['connections'] == [dict(map='MAP_MAHOGANY_TOWN', offset=0, direction='right')]
    assert mah_map['connections'] == [dict(map='MAP_ROUTE44', offset=0, direction='right'), dict(map='MAP_ROUTE42', offset=0, direction='left')]
    border_r = (g / 'data/layouts/Route42/border.bin').read_bytes()
    assert border_r == (g / 'data/layouts/MahoganyTown/border.bin').read_bytes(), 'border blocks differ'
    # Ledger.
    trav = json.loads((SRC / 'pack3/traversal.json').read_text())
    _, beh, layer, coll, elev = r42[:5]
    for c in trav:
        x, y = c['x'], c['y']
        assert beh[y, x] == MB[c['behavior']], (x, y, c['behavior'])
        assert coll[y, x] == c['collision'] and elev[y, x] == c['elevation'], (x, y)
        assert layer[y, x] == (0 if c['layer'] == 'normal' else 1), (x, y)
    foot = {(c['x'], c['y']): c['foot'] for c in trav}
    mfoot = {(c['x'], c['y']): c['foot'] for c in json.loads((MAH / 'source/pack3/traversal.json').read_text())}
    walk = lambda f: f in ('open', 'door')
    crossing = [y for y in range(H) if walk(foot[(W - 1, y)]) and walk(mfoot[(0, y)])]
    mismatch = [y for y in range(H) if walk(foot[(W - 1, y)]) != walk(mfoot[(0, y)])]
    assert not mismatch, ('foot access differs across the seam', mismatch)
    # Reachability from the seam.
    starts = [(W - 1, y) for y in crossing]
    seen, surfed = reach(foot, starts, False), reach(foot, starts, True)
    open_cells = {k for k, v in foot.items() if walk(v)}
    approaches = dict(seam_road=(95, 13), east_route_sign=(86, 13), east_mt_mortar_sign=(75, 13), east_cave_front=(77, 12),
                      tall_grass=(80, 19), stairs_top=(71, 13), stairs_foot=(69, 13), lower_lawn=(68, 18))
    missing = {k: p for k, p in approaches.items() if p not in seen}
    assert not missing, ('unreachable approach', missing)
    water = {k for k, v in foot.items() if v == 'surf'}
    # As in HGSS, the middle and the west are reached through Mt. Mortar or by Surf; Mt. Mortar
    # is not built, so Surf. The pockets behind HGSS's Rock Climb wall are not reached (Gen 3
    # has no Rock Climb).
    by_surf = {k: p for k, p in dict(east_pond=(62, 12), middle_lawn=(45, 18), middle_cave_front=(48, 16), west_pond=(30, 12),
                                     west_road=(12, 14), gate_front=(7, 15), west_route_sign=(11, 18), west_cave_front=(20, 12),
                                     north_west_lawn=(15, 10)).items() if p not in surfed}
    assert not by_surf, ('unreachable with Surf', by_surf)
    # The woods close on the gate (AGENTS.md; owner review, Route 42): G02's footprint is solid,
    # and so is every cell along its north and south sides, so no one walks round it.
    (c0, c1), (r0, r1) = E.GATE_COLS, E.GATE_ROWS
    round_gate = [(x, y) for x in range(c0, c1 + 1) for y in range(r0 - 1, r1 + 2) if walk(foot[(x, y)])]
    assert not round_gate, ('walkable cells in or beside the gate', round_gate)
    # Walk-behind layering.
    top, owner = z['objects'], z['owner']
    walkable = np.array([[walk(foot[(x, y)]) for x in range(W)] for y in range(H)])
    above = P.above_player(walkable, top, np.zeros_like(top), owner)
    seam_cells = {tuple(s['cell']) for s in json.loads((OUT / 'pack.json').read_text())['seam']}
    walk_behind = Counter()
    for y, x in np.ndindex(H, W):
        if (x, y) in seam_cells:
            continue                                       # these take Mahogany's metatiles and their attributes
        assert layer[y, x] == (0 if above[y, x] else 1), ('layer type', x, y)
        if above[y, x]:
            cell = top[y * 16:y * 16 + 16, x * 16:x * 16 + 16][..., 3] > 0
            for o in set(owner[y * 16:y * 16 + 16, x * 16:x * 16 + 16][cell].ravel()) - {''}:
                if not o.startswith(P.FLAT[0]):
                    walk_behind[o.split('_')[0]] += 1
    seam_layers = Counter((bool(walkable[y, x]), int(layer[y, x])) for x, y in seam_cells)
    # Shared masters, budgets, scope.
    prov = json.loads((SRC / 'shared-art/provenance.json').read_text())
    shared_ok = {n: hashlib.sha256((SRC / 'shared-art' / n).read_bytes()).hexdigest() == r['sha256']
                 for n, r in prov.items() if isinstance(r, dict) and 'sha256' in r}
    assert all(shared_ok.values()), shared_ok
    budgets = dict(secondary_tiles=r42[5], secondary_metatiles=r42[6], primary_metatiles=r42[7],
                   mahogany_secondary_metatiles=mah[6])
    assert budgets['secondary_tiles'] <= 496 and budgets['secondary_metatiles'] <= 512 and budgets['primary_metatiles'] <= 512, budgets
    before = json.loads(subprocess.check_output(['git', '-C', str(g), 'show', f'{BASE}:data/maps/map_groups.json']))
    groups = json.loads((g / 'data/maps/map_groups.json').read_text())
    for key, values in before.items():
        if isinstance(values, list):
            assert groups[key][:len(values)] == values, key
    changed = subprocess.check_output(['git', '-C', str(g), 'diff', '--name-only', BASE], text=True).splitlines()
    changed += subprocess.check_output(['git', '-C', str(g), 'ls-files', '--others', '--exclude-standard'], text=True).splitlines()
    allowed = {'data/event_scripts.s', 'data/layouts/layouts.json', 'data/maps/map_groups.json', 'include/regions.h',
               'src/apocrypha_map_proof.c', 'src/data/region_map/region_map_sections.json', 'src/data/tilesets/graphics.h',
               'src/data/tilesets/headers.h', 'src/data/tilesets/metatiles.h', 'data/maps/MahoganyTown/map.json',
               'data/tilesets/secondary/mahogany_town/metatiles.bin', 'data/tilesets/secondary/mahogany_town/metatile_attributes.bin',
               'data/tilesets/secondary/mahogany_town/tiles.png'}
    prefixes = ('data/layouts/Route42/', 'data/maps/Route42/', 'data/tilesets/secondary/route_42/')
    unexpected = sorted(p for p in set(changed) if p not in allowed and not p.startswith(prefixes))
    assert not unexpected, unexpected
    mt_before = subprocess.check_output(['git', '-C', str(g), 'show', f'{BASE}:data/tilesets/secondary/mahogany_town/metatiles.bin'])
    mt_now = (g / 'data/tilesets/secondary/mahogany_town/metatiles.bin').read_bytes()
    assert mt_now[:len(mt_before)] == mt_before, 'Mahogany\'s own metatiles changed'
    mah_diff = subprocess.check_output(['git', '-C', str(g), 'diff', BASE, '--', 'data/maps/MahoganyTown/map.json'], text=True)
    assert all(l.strip(' -+,{}"') in ('', 'map": "MAP_ROUTE42', 'offset": 0', 'direction": "left', 'direction": "right')
               for l in mah_diff.splitlines() if l[:1] in '+-' and not l.startswith(('+++', '---'))), mah_diff
    # Mahogany's own tiles unchanged: its tile sheet only grows.
    old_tiles = np.array(Image.open(__import__('io').BytesIO(subprocess.check_output(
        ['git', '-C', str(g), 'show', f'{BASE}:data/tilesets/secondary/mahogany_town/tiles.png']))))
    assert (np.array(Image.open(g / 'data/tilesets/secondary/mahogany_town/tiles.png'))[:old_tiles.shape[0]] == old_tiles).all(), 'Mahogany tiles changed'
    # Material audit.
    rows, mism, fg_diff, unknown = material_audit(img, phg)
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
    result = dict(route42_matches_pack_decode_and_assembled_art=True, mahogany_pixels_unchanged=True,
                  route42_pixels_mahogany_shows_exact=int(view.sum()), mahogany_pixels_route42_shows_exact=int(mview.sum()),
                  connections=dict(route42=r42_map['connections'], mahogany=mah_map['connections']), border_shared=True,
                  ledger_behaviour_collision_elevation_layer=True, seam_crossing_rows=crossing,
                  reachable_foot_cells=len(seen), open_cells=len(open_cells), unreachable_open_cells=sorted(open_cells - seen),
                  surf_reachable_cells=len(surfed), water_cells=len(water), approaches=approaches,
                  walk_behind_cells=dict(walk_behind), seam_cells_walkable_layer=[[k[0], k[1], n] for k, n in sorted(seam_layers.items())],
                  shared_masters_byte_identical=shared_ok, budgets=budgets,
                  existing_map_ids_preserved=True, changed_files_within_scope=True, mahogany_metatiles_unchanged=True,
                  mahogany_map_json_only_connection=True, material_cells=len(rows),
                  material_matches=sum(r['status'] == 'match' for r in rows),
                  material_mismatches=[m_['cell'] for m_ in mism], foreground_differs=[m_['cell'] for m_ in fg_diff])
    (OUT / 'native-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('approaches', 'shared_masters_byte_identical', 'foreground_differs',
                                                                    'unreachable_open_cells')}))
    print('unreachable open cells', sorted(open_cells - seen)[:30], len(open_cells - seen), 'foreground differs', len(fg_diff))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
