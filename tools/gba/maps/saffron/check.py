"""Audit the installed Saffron City (v2, HGSS's plan) and its new interiors from native files.

    python3 tools/gba/maps/saffron/check.py ENGINE_CHECKOUT

Decodes data/layouts/KantoSaffronCity with gTileset_KantoSaffronPrimary and
gTileset_KantoSaffronCity exactly as the game composes them (bottom layer, then the top
layer's non-zero pixels) and checks it against the packer's decode and the traversal
ledger (behaviour, collision, elevation, layer type per cell); reachability of every
approach, sign and exit from the Center; walk-behind depth; the shared Center's and Mart's
pixels and hashes; the derived primary (Cherrygrove's kept banks, tile 0, no callback);
the warps both ways (the Center, the Mart, the Dojo's two doors into one hall, the lab);
each interior decoded from its own files equal to interiors.py's (FireRed's pixels), its
exit mats reachable; v1's door entry gone; budgets; preservation.
Writes evidence/native-audit.json and native-grid.png.
"""
from __future__ import annotations
import hashlib, json, subprocess, sys
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pack as P                                    # noqa: E402  (Saffron's packer: its Olivine helpers)
import interiors as I                               # noqa: E402
B, OP = P.B, P.OP

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/saffron-kanto'
SRC, EV = ART / 'source', ART / 'evidence'
W, H = 64, 64
NAME, FOLDER, PFOLDER = 'KantoSaffronCity', 'kanto_saffron_city', 'kanto_saffron'
START = (14, 51)                                    # in front of the Center door
BASE = 'origin/claude/olivine-city'                 # the engine branch Saffron builds on
C06_SHA256 = '89034027c4b4f3241ad70baeeb104e23a571e521b76b27f388eb89123cc79f54'   # gba/art/johto-common/approved-buildings.json
MART_SHA256 = '03aa370bc2d4b1d7f869dde3dd318324d2484254f432a4f24ca9abf356a48ca8'  # the shared Johto Mart
SHARED_ART = ROOT / 'gba/art/olivine-elements/source/shared-art'
APPROACHES = dict(center=(14, 51), mart=(38, 27), dojo_fighting=(41, 13), dojo_psychic=(48, 13), lab=(37, 42),
                  silph=(28, 38), station=(10, 17), copycat=(17, 27), mrpsychic=(43, 51),
                  station_sign=(12, 19), city_sign=(23, 19), fighting_sign=(43, 17), psychic_sign=(50, 17),
                  silph_sign=(26, 43), mrpsychic_sign=(41, 51),
                  north_gate=(20, 6), east_gate=(56, 48), south_exit=(20, 60), west_exit=(1, 48))
ROOMS = {'KantoSaffronDojo': ('dojo', 'kanto_saffron_dojo'), 'KantoSaffronSilphLab': ('lab', 'kanto_saffron_silph_lab')}

def tileset(d):
    a = np.array(Image.open(d / 'tiles.png')) & 15
    tiles = [a[y:y + 8, x:x + 8] for y in range(0, a.shape[0], 8) for x in range(0, a.shape[1], 8)]
    metas = np.frombuffer((d / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
    attrs = np.frombuffer((d / 'metatile_attributes.bin').read_bytes(), '<u2')
    return tiles, metas, attrs

def decode(g, layout, w, h, prim, sec):
    pt, pm, pa = tileset(prim)
    st, sm, sa = tileset(sec)
    pals = [B.read_pal((prim if i < 6 else sec) / 'palettes' / f'{i:02}.pal') for i in range(16)]
    tiles = pt[:512] + [np.zeros((8, 8), np.uint8)] * (512 - len(pt[:512])) + st
    metas, attrs = list(pm[:512]) + [np.zeros(8, np.uint16)] * (512 - len(pm[:512])) + list(sm), \
        list(pa[:512]) + [0] * (512 - len(pa[:512])) + list(sa)
    grid = np.frombuffer((g / f'data/layouts/{layout}/map.bin').read_bytes(), '<u2').reshape(h, w)
    img = np.zeros((h * 16, w * 16, 3), np.uint8)
    beh, layer, coll, elev, mid = (np.zeros((h, w), np.int32) for _ in range(5))
    for y, x in np.ndindex(h, w):
        v = int(grid[y, x]); m = v & 1023
        mid[y, x], coll[y, x], elev[y, x] = m, (v >> 10) & 3, v >> 12
        beh[y, x], layer[y, x] = int(attrs[m]) & 0xFF, (int(attrs[m]) >> 12) & 3
        for i, e in enumerate(metas[m]):
            e = int(e); t = tiles[e & 1023]
            if e & 1024: t = t[:, ::-1]
            if e & 2048: t = t[::-1]
            q = i % 4; oy, ox = y * 16 + (q // 2) * 8, x * 16 + (q % 2) * 8
            mask = t > 0 if i >= 4 else np.ones((8, 8), bool)
            img[oy:oy + 8, ox:ox + 8][mask] = np.array(pals[e >> 12])[t[mask]]
    return img, beh, layer, coll, elev, mid, len(st), len(sm)

def reach(passable, start):
    seen = {start}; q = deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n in passable and n not in seen:
                seen.add(n); q.append(n)
    return seen

def audit_city(g, MB):
    prim, sec = g / f'data/tilesets/primary/{PFOLDER}', g / f'data/tilesets/secondary/{FOLDER}'
    img, beh, layer, coll, elev, mid, n_sec_tiles, n_metas = decode(g, NAME, W, H, prim, sec)
    built = np.array(Image.open(EV / 'native.png').convert('RGB'))
    assert (B.rgb5(img) == B.rgb5(built)).all(), 'installed map differs from the packer decode'
    trav = json.loads((SRC / 'traversal.json').read_text())
    for c in trav:
        x, y = c['x'], c['y']
        assert beh[y, x] == MB[c['behavior']], (x, y, c['behavior'])
        assert coll[y, x] == c['collision'] and elev[y, x] == c['elevation'], (x, y)
        assert layer[y, x] == (0 if c['layer'] == 'normal' else 1), (x, y)
    foot = {(c['x'], c['y']): c['foot'] for c in trav}
    open_cells = {k for k, v in foot.items() if v in ('open', 'door')}
    seen = reach(open_cells, START)
    for k, p in APPROACHES.items():
        assert p in seen, ('unreachable approach', k, p)
    # Depth (Olivine's rule): a walkable cell draws its art above the player exactly when
    # that art's object stands further south; doors, base rows and blocked cells keep it below.
    comp = np.load(SRC / 'compose.npz', allow_pickle=True)
    art = (comp['top'][..., 3] > 0) | (comp['shared'][..., 3] > 0)
    owner = comp['owner']
    OP.H, OP.W, OP.FLAT = H, W, P.FLAT
    walkable = np.array([[foot[(x, y)] in ('open', 'door') for x in range(W)] for y in range(H)])
    above = OP.above_player(walkable, comp['top'], comp['shared'], owner)
    walk_behind = {}
    for y, x in np.ndindex(H, W):
        cell = art[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
        who = sorted(set(owner[y * 16:y * 16 + 16, x * 16:x * 16 + 16][cell].ravel()) - {''}) or ['terrain']
        if above[y, x]:
            assert layer[y, x] == 0, ('walk-behind art not drawn above the player', x, y)
            for o in who:
                walk_behind.setdefault(o.rstrip('_0123456789') if o[-1:].isdigit() else o, []).append([x, y])
        else:
            assert layer[y, x] == 1, ('art drawn above the player in front of its object', x, y)
    # The shared Center and Mart: their masters, every opaque pixel exact in the map.
    assert hashlib.sha256((SHARED_ART / 'pokemon-center.png').read_bytes()).hexdigest() == C06_SHA256
    assert hashlib.sha256((SHARED_ART / 'poke-mart.png').read_bytes()).hexdigest() == MART_SHA256
    shared = comp['shared'][..., 3] > 0
    assert (B.rgb5(img)[shared] == B.rgb5(comp['shared'][..., :3])[shared]).all()
    # The derived primary: Cherrygrove's tile 0, its banks 0 and 3 (3 with the two plain
    # greens in slots no Cherrygrove tile draws), every kept Cherrygrove tile at its index.
    cp = g / 'data/tilesets/primary/cherrygrove'
    ct, ot = tileset(cp)[0], tileset(prim)[0]
    assert (ct[0] == ot[0]).all() and len(ot) <= 512
    kept = [i for i in range(1, min(len(ct), len(ot))) if (ct[i] == ot[i]).all() and ct[i].any()]
    for b in P.KEPT_BANKS:
        a, o = B.read_pal(cp / f'palettes/{b:02}.pal'), B.read_pal(prim / f'palettes/{b:02}.pal')
        free = set(OP.TREE_BANK_GREENS) if b == 3 else set()
        assert all(a[i] == o[i] for i in range(16) if i not in free), ('kept bank changed', b)
    head = (g / 'src/data/tilesets/headers.h').read_text().split('gTileset_KantoSaffronPrimary =')[1].split(';')[0]
    assert '.callback = NULL' in head
    assert 'KantoSaffronPrimary' not in (g / 'src/field_door.c').read_text(), "v1's door entry is still there"
    assert n_sec_tiles <= P.SECONDARY_TILES and n_metas <= 512, (n_sec_tiles, n_metas)
    return dict(cells_audited=len(trav), installed_matches_packer_decode=True, ledger_behaviour_collision_elevation_layer=True,
                reachable_cells=len(seen), open_cells=len(open_cells), unreachable_open_cells=sorted(open_cells - seen),
                approaches=APPROACHES, walk_behind_cells={k: len(v) for k, v in sorted(walk_behind.items())},
                shared_building_pixels_exact=int(shared.sum()), center_master_sha256=C06_SHA256, mart_sha256=MART_SHA256,
                primary_tiles=len(ot), cherrygrove_tiles_at_their_index=len(kept) + 1, primary_callback=None,
                secondary_tiles=n_sec_tiles, secondary_tile_limit=P.SECONDARY_TILES, secondary_metatiles=n_metas,
                v1_door_entry_removed=True), img, beh

def audit_warps(g, MB, beh):
    city = json.loads((g / f'data/maps/{NAME}/map.json').read_text())
    out = []
    for i, w in enumerate(city['warp_events']):
        x, y = w['x'], w['y']
        assert beh[y, x] == MB['MB_ANIMATED_DOOR'], ('city warp not on a door', x, y)
        dest = w['dest_map']
        room = next(n for n in json.loads((g / 'data/maps/map_groups.json').read_text())['gMapGroup_Kanto']
                    if json.loads((g / f'data/maps/{n}/map.json').read_text())['id'] == dest)
        back = json.loads((g / f'data/maps/{room}/map.json').read_text())['warp_events']
        tw = back[int(w['dest_warp_id'])]
        assert tw['dest_map'] == 'MAP_KANTO_SAFFRON_CITY', (room, tw)
        out.append(dict(city_warp=i, door=[x, y], to=room, arrives=[tw['x'], tw['y']], back_to_city_warp=int(tw['dest_warp_id'])))
    # every room warp returns to a city door of its own building
    for o in out:
        assert city['warp_events'][o['back_to_city_warp']]['dest_map'] == city['warp_events'][o['city_warp']]['dest_map'], o
    return out

def audit_rooms(g, MB):
    out = {}
    prim = g / 'data/tilesets/primary/building'
    for name, (key, folder) in ROOMS.items():
        z = np.load(SRC / f'interiors/{key}.npz')
        h, w = z['grid'].shape
        img, beh, layer, coll, elev, mid, nt, nm = decode(g, name, w, h, prim, g / f'data/tilesets/secondary/{folder}')
        assert (B.rgb5(img) == B.rgb5(I.decode(z))).all(), (name, 'installed room differs from interiors.py')
        assert (coll == z['collision']).all() and (beh == z['behaviour']).all(), name
        m = json.loads((g / f'data/maps/{name}/map.json').read_text())
        arrows = [(wv['x'], wv['y']) for wv in m['warp_events'] if beh[wv['y'], wv['x']] == MB['MB_SOUTH_ARROW_WARP']]
        assert arrows, (name, 'no exit mat')
        walk = {(x, y) for y, x in np.ndindex(h, w) if coll[y, x] == 0}
        seen = reach(walk, arrows[0])
        assert all(a in seen for a in arrows), (name, 'an exit mat is cut off from the others')
        assert nt <= 512 and nm <= 512
        out[name] = dict(size=[w, h], tiles=nt, metatiles=nm, matches_fireRed_pixels=True, exit_mats=[list(a) for a in arrows],
                         walkable=len(walk), reachable_from_exit=len(seen))
    return out

def preservation(g):
    before = json.loads(subprocess.check_output(['git', '-C', str(g), 'show', f'{BASE}:data/maps/map_groups.json']))
    groups = json.loads((g / 'data/maps/map_groups.json').read_text())
    for key, values in before.items():
        if isinstance(values, list):
            assert groups[key][:len(values)] == values, key
    changed = subprocess.check_output(['git', '-C', str(g), 'diff', '--name-only', BASE], text=True).splitlines()
    changed += subprocess.check_output(['git', '-C', str(g), 'ls-files', '--others', '--exclude-standard'], text=True).splitlines()
    allowed = {'data/event_scripts.s', 'data/layouts/layouts.json', 'data/maps/map_groups.json', 'src/apocrypha_map_proof.c',
               'src/data/tilesets/graphics.h', 'src/data/tilesets/headers.h', 'src/data/tilesets/metatiles.h'}
    prefixes = ('data/layouts/KantoSaffron', 'data/maps/KantoSaffron', 'data/tilesets/secondary/kanto_saffron',
                f'data/tilesets/primary/{PFOLDER}/')
    unexpected = sorted(p for p in set(changed) if p not in allowed and not p.startswith(prefixes))
    assert not unexpected, unexpected
    return dict(existing_map_ids_preserved=True, changed_files_within_scope=True, field_door_unchanged_from_base='src/field_door.c' not in changed)

def main(g):
    MB = B.behaviors(g)
    result, img, beh = audit_city(g, MB)
    result['warps'] = audit_warps(g, MB, beh)
    result['interiors'] = audit_rooms(g, MB)
    result.update(preservation(g))
    big = Image.fromarray(img).resize((W * 32, H * 32), Image.Resampling.NEAREST); d = ImageDraw.Draw(big)
    for i in range(W):
        d.line((i * 32, 0, i * 32, H * 32), fill=(60, 60, 70)); d.text((i * 32 + 2, 2), str(i), fill='white', stroke_width=1, stroke_fill='black')
    for i in range(H):
        d.line((0, i * 32, W * 32, i * 32), fill=(60, 60, 70)); d.text((2, i * 32 + 3), str(i), fill='white', stroke_width=1, stroke_fill='black')
    big.save(EV / 'native-grid.png')
    (EV / 'native-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('approaches', 'warps')}))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
