"""Audit the installed third-draft Mahogany Town from its native files.

    python3 tools/gba/maps/mahogany/check3.py ENGINE_CHECKOUT PHG_CHECKOUT

Decodes data/layouts/MahoganyTown with its tileset pair exactly as the game composes it and
checks: the decode equals the packer's (pixel for pixel, RGB555) and the assembled art on
every visible pixel; behaviour, collision, elevation and layer type per cell against the
traversal ledger; reachability of every approach; walk-behind layering; budgets; that the
shared masters are byte-identical to the catalog's; and that only Mahogany files changed.

Material audit (docs/GBA_MAP_RECONSTRUCTION.md section 4): every decoded pixel is classified
by colour against vocabularies built from the source masters (the lawn and road textures and
their rims, the rock face and top ramps, the ledges, T01, each building), never from the
layout's own labels; each cell is compared with what HGSS's decoded reference shows there. Writes evidence/pack3/{native-audit.json, material-audit.json, native-grid.png}.
"""
from __future__ import annotations
import hashlib, json, subprocess, sys
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import build as B                                   # noqa: E402
import pack as P                                    # noqa: E402
import check_convert as CC                          # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/mahogany-town'
SRC, EV = ART / 'source', ART / 'evidence'
OUT = EV / 'pack3'
W = H = 32
BASE = 'origin/apocrypha'

def rgba(p): return np.array(Image.open(p).convert('RGBA'))
def c5set(a, m=None):
    a = np.asarray(a)
    px = a[..., :3][a[..., 3] > 0] if a.shape[-1] == 4 and m is None else (a[m] if m is not None else a.reshape(-1, 3))
    return {tuple(c) for c in (px.astype(int) >> 3).tolist()}

def vocab():
    """Colour vocabularies from the masters themselves."""
    from claude_cherrygrove import ground as G
    tex = G.textures()
    sh = SRC / 'shared-art'
    import elements as E
    pieces = E.frlg_pieces(ENGINE)
    ramp = {i for group in ('nine', 'rock', 'inner') for p in pieces[group].values() for i in p.ravel().tolist() if i >= 0}
    v = dict(
        lawn=c5set(tex[G.GRASS]) | {tuple(np.array(c) >> 3) for c in G.PROFILES[(G.GRASS, G.PATH)][0]},
        road=c5set(tex[G.PATH]) | {tuple(np.array(c) >> 3) for c in G.PROFILES[(G.GRASS, G.PATH)][1]},
        rock={tuple(np.array(E.ROCK_RAMP[i]) >> 3) for i in ramp},
        ledge=set().union(*(c5set(rgba(sh / f'{n}.png')) for n in ('L11', 'L12', 'L13'))),
        flowers={(29, 28, 26)},
        tree=c5set(rgba(sh / 'T01.png')),
        center=c5set(rgba(sh / 'pokemon-center.png')), gate=c5set(rgba(sh / 'G01a.png')),
        sign=set().union(*(c5set(rgba(sh / f'{n}.png')) for n in ('P12', 'P13', 'P15'))),
        houses_towers=c5set(rgba(SRC / 'local-art/house.png')) | c5set(rgba(SRC / 'local-art/tower.png')),
        gym=c5set(rgba(SRC / 'local-art/gym.png')), antenna_tree=c5set(rgba(SRC / 'local-art/antenna_tree.png')))
    return v

OBJECTS = ('tree', 'center', 'gate', 'sign', 'houses_towers', 'gym', 'antenna_tree')
TERRAIN = ('lawn', 'road', 'flowers', 'rock', 'ledge')
MODEL_CLASS = {29: 'sign', 31: 'sign', 33: 'sign', 35: 'gate', 134: 'houses_towers', 135: 'houses_towers',
               249: 'houses_towers', 136: 'antenna_tree', 138: 'gym', 16: 'gym'}

def hgss_classes(phg, grid):
    """Per pixel, what HGSS shows, decoded flat (the way the rock terraces are built): its
    cliff and wall materials (rock), ledge materials, tree materials, lawn or road by its own
    ground colours, then its building models (hgss-foreground) and the Center (left out of
    hgss-foreground; its grid cells)."""
    import elements as E
    h, mat, names, rgb = E.topdown(phg)
    nm = np.array(names + ['none'])
    m = nm[np.where(mat >= 0, mat, len(names))]
    rgb = rgb.astype(int)
    cls = np.full((H * 16, W * 16), '', object)
    cls[(rgb[..., 1] > rgb[..., 0] + 20)] = 'lawn'
    cls[(rgb[..., 0] >= rgb[..., 1]) & (rgb[..., 0] > 180) & (rgb[..., 2] < 175)] = 'road'
    cls[np.isin(m, E.ROCK_MATERIALS) & ~np.isin(m, E.LEDGE_MATERIALS)] = 'rock'
    cls[np.isin(m, E.LEDGE_MATERIALS)] = 'ledge'
    cls[np.isin(m, E.TREE_MATERIALS)] = 'tree'
    for y in range(H):
        for x in range(W):
            if grid[y][x] == 'C':
                cls[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = 'center'
    own = np.load(SRC / 'hgss/hgss-foreground-owner.npz')['owner']
    models = [b['model'] for b in json.loads((SRC / 'hgss/hgss-render.json').read_text())['buildings']]
    for i, mm in enumerate(models):
        if mm in MODEL_CLASS:
            cls[own == i] = MODEL_CLASS[mm]
    return cls

def material_audit(img, grid, phg):
    """Square by square: native classes from decoded colours (each colour votes for every
    vocabulary that holds it), HGSS classes from the decoded reference. A terrain cell matches
    when the native's leading terrain material is one HGSS shows there (at least 24 px); an
    object cell when the same kind of object leads in both. Cells where an object leads in
    one but terrain in the other are listed as foreground differences, not counted as
    matches."""
    v = vocab()
    owner = {}
    for k, s_ in v.items():
        for c in s_:
            owner.setdefault(c, set()).add(k)
    hc = hgss_classes(phg, grid)
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
            n_obj = max((votes[k] for k in OBJECTS), default=0)
            native_obj = n_obj >= 128
            hgss_obj = max((hv[k] for k in OBJECTS), default=0) >= 128
            nat_lead = max(OBJECTS if native_obj else TERRAIN, key=lambda k: votes[k])
            h_lead = max(OBJECTS if hgss_obj else TERRAIN, key=lambda k: hv[k])
            if native_obj != hgss_obj:
                status = 'foreground differs'
            elif native_obj:
                status = 'match' if votes[h_lead] >= 64 else 'mismatch'
            else:
                status = 'match' if hv[nat_lead] >= 24 or votes[h_lead] >= 24 else 'mismatch'
                if status == 'match' and grid[y][x] == 'f' and votes['flowers'] < 3:
                    status = 'mismatch'                                  # HGSS's flower cells keep their white heads
            row = dict(cell=[x, y], code=grid[y][x], status=status, native_lead=nat_lead, hgss_lead=h_lead,
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
    img, beh, layer, coll, elev, mid, _, n_metas = CC.decode(g)
    built = np.array(Image.open(OUT / 'native.png').convert('RGB'))
    assert (B.rgb5(img) == B.rgb5(built)).all(), 'installed map differs from the packer decode'
    z = np.load(SRC / 'assemble/layers.npz')
    want = z['ground'].copy()
    for layer_ in (z['rock'], z['objects']):
        a = layer_[..., 3] > 0
        want[a] = layer_[a, :3]
    assert (B.rgb5(img) == B.rgb5(want)).all(), 'installed map differs from the assembled art'
    trav = json.loads((SRC / 'pack3/traversal.json').read_text())
    MB = B.behaviors(g)
    for c in trav:
        x, y = c['x'], c['y']
        assert beh[y, x] == MB[c['behavior']], (x, y, c['behavior'])
        assert coll[y, x] == c['collision'] and elev[y, x] == c['elevation'], (x, y)
        assert layer[y, x] == (0 if c['layer'] == 'normal' else 1), (x, y)
    foot = {(c['x'], c['y']): c['foot'] for c in trav}
    seen = CC.reach(foot, False)
    open_cells = {k for k, v in foot.items() if v in ('open', 'door')}
    approaches = dict(center=(22, 24), gym=(11, 24), souvenir_shop=(16, 15), east_house=(25, 15),
                      route43_gate=(13, 6), west_edge=(0, 12), east_edge=(31, 16), town_sign=(4, 13),
                      gym_sign=(8, 25), souvenir_sign=(14, 15), west_lawn=(8, 10), gym_lawn_west=(5, 22),
                      center_lawn=(18, 22), behind_center=(22, 18), behind_gym=(11, 17))
    missing = {k: p for k, p in approaches.items() if p not in seen}
    assert not missing, ('unreachable approach', missing)
    # Walk-behind: object art in a walkable cell is above the player exactly when its object
    # stands further south (pack.above_player); every other cell draws under the player.
    top, owner = z['objects'], z['owner']
    walkable = np.array([[foot[(x, y)] in ('open', 'door') for x in range(W)] for y in range(H)])
    above = P.above_player(walkable, top, np.zeros_like(top), owner)
    walk_behind = {}
    for y, x in np.ndindex(H, W):
        assert layer[y, x] == (0 if above[y, x] else 1), ('layer type', x, y)
        if above[y, x]:
            cell = top[y * 16:y * 16 + 16, x * 16:x * 16 + 16][..., 3] > 0
            for o in sorted(set(owner[y * 16:y * 16 + 16, x * 16:x * 16 + 16][cell].ravel()) - {''}):
                walk_behind.setdefault(o.split('_')[0], []).append([x, y])
    # Shared masters are the catalog's bytes.
    prov = json.loads((SRC / 'shared-art/provenance.json').read_text())
    shared_ok = {}
    for name, rec in prov.items():
        if isinstance(rec, dict) and 'sha256' in rec and (SRC / 'shared-art' / name).exists():
            shared_ok[name] = hashlib.sha256((SRC / 'shared-art' / name).read_bytes()).hexdigest() == rec['sha256']
    assert all(shared_ok.values()), shared_ok
    used = np.concatenate([np.frombuffer((g / f'data/tilesets/{k}/metatiles.bin').read_bytes(), '<u2') & 1023
                           for k in ('primary/mahogany', 'secondary/mahogany_town')])
    n_tiles = int(used.max()) + 1
    n_prim_metas = len(np.frombuffer((g / 'data/tilesets/primary/mahogany/metatiles.bin').read_bytes(), '<u2')) // 8
    assert n_tiles <= 1008 and n_metas <= 512 and n_prim_metas <= 512, (n_tiles, n_metas, n_prim_metas)
    before = json.loads(subprocess.check_output(['git', '-C', str(g), 'show', f'{BASE}:data/maps/map_groups.json']))
    groups = json.loads((g / 'data/maps/map_groups.json').read_text())
    for key, values in before.items():
        if isinstance(values, list):
            assert groups[key][:len(values)] == values, key
    changed = subprocess.check_output(['git', '-C', str(g), 'diff', '--name-only', BASE], text=True).splitlines()
    changed += subprocess.check_output(['git', '-C', str(g), 'ls-files', '--others', '--exclude-standard'], text=True).splitlines()
    allowed = {'data/event_scripts.s', 'data/layouts/layouts.json', 'data/maps/map_groups.json', 'include/regions.h',
               'src/apocrypha_map_proof.c', 'src/data/region_map/region_map_sections.json', 'src/data/tilesets/graphics.h',
               'src/data/tilesets/headers.h', 'src/data/tilesets/metatiles.h'}
    prefixes = ('data/layouts/MahoganyTown/', 'data/maps/MahoganyTown/', 'data/maps/MahoganyPokemonCenter/',
                'data/maps/MahoganyCenterUpstairs/', 'data/tilesets/secondary/mahogany_town/', 'data/tilesets/primary/mahogany/')
    unexpected = sorted(p for p in set(changed) if p not in allowed and not p.startswith(prefixes))
    assert not unexpected, unexpected
    # Material audit against the traced grid.
    grid = [list(l.split()[1]) for l in (SRC / 'trace/material-grid.txt').read_text().splitlines() if l[:2].isdigit()]
    rows, mism, fg_diff, unknown = material_audit(img, grid, phg)
    (OUT / 'material-audit.json').write_text(json.dumps(dict(
        method=material_audit.__doc__.strip() + ' Native vocabularies come from the source masters (shared catalog art, '
               'the Cherrygrove ground painter, the FRLG mountain pieces in the rock ramp, the local HGSS buildings); HGSS '
               'classes from the flat decode (cliff, wall, ledge and tree materials, ground colours) and its building models.',
        cells=len(rows), matches=sum(r['status'] == 'match' for r in rows), mismatches=mism, foreground_differs=fg_diff,
        unclassified_colours={str(k): n for k, n in unknown.most_common(20)}, per_cell=rows), indent=1) + '\n')
    big = Image.fromarray(img).resize((W * 32, H * 32), Image.Resampling.NEAREST); d = ImageDraw.Draw(big)
    for i in range(W):
        d.line((i * 32, 0, i * 32, H * 32), fill=(60, 60, 70)); d.text((i * 32 + 2, 2), str(i), fill='white', stroke_width=1, stroke_fill='black')
    for i in range(H):
        d.line((0, i * 32, W * 32, i * 32), fill=(60, 60, 70)); d.text((2, i * 32 + 3), str(i), fill='white', stroke_width=1, stroke_fill='black')
    for m in mism:
        x, y = m['cell']
        d.rectangle((x * 32, y * 32, x * 32 + 31, y * 32 + 31), outline=(255, 0, 255), width=2)
    for m in fg_diff:
        x, y = m['cell']
        d.rectangle((x * 32 + 2, y * 32 + 2, x * 32 + 29, y * 32 + 29), outline=(0, 220, 255), width=1)
    big.save(OUT / 'native-grid.png')
    result = dict(installed_matches_packer_decode=True, installed_matches_assembled_art=True, cells_audited=len(trav),
                  ledger_behaviour_collision_elevation_layer=True, reachable_foot_cells=len(seen), open_cells=len(open_cells),
                  unreachable_open_cells=sorted(open_cells - seen), approaches=approaches,
                  walk_behind_cells={k: len(v) for k, v in sorted(walk_behind.items())}, walk_behind=walk_behind,
                  shared_masters_byte_identical=shared_ok, tiles=n_tiles, tile_limit=1008, primary_metatiles=n_prim_metas,
                  secondary_metatiles=n_metas, metatile_limit_each=512, existing_map_ids_preserved=True,
                  changed_files_within_scope=True, material_cells=len(rows),
                  material_matches=sum(r['status'] == 'match' for r in rows),
                  material_mismatches=[m['cell'] for m in mism], foreground_differs=[m['cell'] for m in fg_diff])
    (OUT / 'native-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('walk_behind', 'approaches', 'shared_masters_byte_identical')}))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
