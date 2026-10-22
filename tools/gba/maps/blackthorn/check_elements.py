"""Audit the installed element-built Blackthorn City (one native map) from its native files.

    python3 tools/gba/maps/blackthorn/check_elements.py ENGINE_CHECKOUT [STYLE]   # STYLE C by default

Decodes data/layouts/BlackthornCity with gTileset_CherrygrovePrimary and
gTileset_BlackthornCity exactly as the game composes them (bottom layer, then the top
layer's non-zero pixels) and checks it against the packer's decode, the traversal
ledger (behaviour, collision, elevation, layer type per cell), reachability, the shared
Center and Mart pixels and palettes, walk-behind cells, budgets and preservation.
Writes evidence/elements/native-audit.json and native-grid.png.
"""
from __future__ import annotations
import json, subprocess, sys
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build as B                                   # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/blackthorn-city'
SRC, EV = ART / 'source', ART / 'evidence'
W = H = 64
NAME, FOLDER = 'BlackthornCity', 'blackthorn_city'
START = (34, 49)                                    # in front of the Center door

def tileset(d):
    a = np.array(Image.open(d / 'tiles.png')) & 15
    tiles = [a[y:y + 8, x:x + 8] for y in range(0, a.shape[0], 8) for x in range(0, a.shape[1], 8)]
    metas = np.frombuffer((d / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
    attrs = np.frombuffer((d / 'metatile_attributes.bin').read_bytes(), '<u2')
    return tiles, metas, attrs

def decode(g):
    prim, sec = g / 'data/tilesets/primary/cherrygrove', g / f'data/tilesets/secondary/{FOLDER}'
    pt, pm, pa = tileset(prim)
    st, sm, sa = tileset(sec)
    pals = [B.read_pal((prim if i < 6 else sec) / 'palettes' / f'{i:02}.pal') for i in range(16)]
    tiles = pt[:512] + [np.zeros((8, 8), np.uint8)] * (512 - len(pt[:512])) + st
    metas, attrs = list(pm[:512]) + list(sm), list(pa[:512]) + list(sa)
    grid = np.frombuffer((g / f'data/layouts/{NAME}/map.bin').read_bytes(), '<u2').reshape(H, W)
    img = np.zeros((H * 16, W * 16, 3), np.uint8)
    beh, layer, coll, elev, mid = (np.zeros((H, W), np.int32) for _ in range(5))
    for y, x in np.ndindex(H, W):
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

def reach(foot, surf):
    seen = {START}; q = deque([START])
    passable = ('open', 'door', 'water') if surf else ('open', 'door')
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

def main(g, style):
    img, beh, layer, coll, elev, mid, _, n_metas = decode(g)
    built = np.array(Image.open(EV / 'elements' / f'native-{style}.png').convert('RGB'))
    assert (B.rgb5(img) == B.rgb5(built)).all(), 'installed map differs from the packer decode'
    trav = json.loads((SRC / 'elements' / f'traversal-{style}.json').read_text())
    MB = B.behaviors(g)
    for c in trav:
        x, y = c['x'], c['y']
        assert beh[y, x] == MB[c['behavior']], (x, y, c['behavior'])
        assert coll[y, x] == c['collision'] and elev[y, x] == c['elevation'], (x, y)
        assert layer[y, x] == (0 if c['layer'] == 'normal' else 1), (x, y)
    foot = {(c['x'], c['y']): c['foot'] for c in trav}
    seen, surfed = reach(foot, False), reach(foot, True)
    open_cells = {k for k, v in foot.items() if v in ('open', 'door')}
    approaches = dict(center=(34, 49), mart=(27, 49), gym_forecourt=(28, 24), dragons_den=(32, 5), ice_path=(57, 17),
                      bridge_south=(23, 63), city_sign=(52, 43), gym_sign=(26, 26), den_sign=(31, 7), west_house=(20, 38),
                      east_house=(44, 41), tutor_house=(18, 49))
    for k, p in approaches.items():
        assert p in surfed, ('unreachable approach', k, p)
    # Walk-behind: every walkable cell with object or rock art on the top layer draws it
    # above the player (layer type normal); every blocked cell keeps it below (covered).
    comp = np.load(SRC / 'elements' / f'compose-{style}.npz', allow_pickle=True)
    top_a = comp['top'][..., 3] > 0
    owner = comp['owner']
    walk_behind = {}
    for y, x in np.ndindex(H, W):
        cell = top_a[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
        if foot[(x, y)] in ('open', 'door', 'water') and cell.any():
            assert layer[y, x] == 0, ('walkable cell with top art not drawn above the player', x, y)
            who = sorted(set(owner[y * 16:y * 16 + 16, x * 16:x * 16 + 16][cell].ravel()) - {''})
            for o in who or ['terrain']:
                walk_behind.setdefault(o, []).append([x, y])
        elif foot[(x, y)] in ('blocked', 'ledge_south'):
            assert layer[y, x] == 1, ('blocked cell drawn above the player', x, y)
    # Shared Center and Mart: every opaque source pixel exact, palettes identical.
    shared = comp['shared'][..., 3] > 0
    assert (B.rgb5(img)[shared] == B.rgb5(comp['shared'][..., :3])[shared]).all()
    sec = g / f'data/tilesets/secondary/{FOLDER}/palettes'
    assert (sec / '08.pal').read_text() == (g / 'data/tilesets/secondary/cherrygrove/palettes/08.pal').read_text()
    assert (sec / '09.pal').read_text() == (SRC / 'shared-art/poke-mart.pal').read_text().replace('\r\n', '\n')
    # Budgets: 496 secondary tiles (16 kept for door animation), 512 secondary metatiles.
    sm = np.frombuffer((g / f'data/tilesets/secondary/{FOLDER}/metatiles.bin').read_bytes(), '<u2') & 1023
    n_tiles = int(sm[sm >= 512].max()) - 511                   # tiles.png pads its last row of 16
    assert n_tiles <= 496 and n_metas <= 512, (n_tiles, n_metas)
    # Preservation: existing map ids keep their order; only Blackthorn files changed.
    before = json.loads(subprocess.check_output(['git', '-C', str(g), 'show', 'origin/apocrypha:data/maps/map_groups.json']))
    groups = json.loads((g / 'data/maps/map_groups.json').read_text())
    for key, values in before.items():
        if isinstance(values, list):
            assert groups[key][:len(values)] == values, key
    changed = subprocess.check_output(['git', '-C', str(g), 'diff', '--name-only', 'origin/apocrypha'], text=True).splitlines()
    changed += subprocess.check_output(['git', '-C', str(g), 'ls-files', '--others', '--exclude-standard'], text=True).splitlines()
    allowed = {'data/event_scripts.s', 'data/layouts/layouts.json', 'data/maps/map_groups.json', 'include/regions.h',
               'src/apocrypha_map_proof.c', 'src/data/region_map/region_map_sections.json', 'src/data/tilesets/graphics.h',
               'src/data/tilesets/headers.h', 'src/data/tilesets/metatiles.h'}
    prefixes = (f'data/layouts/{NAME}/', 'data/maps/BlackthornCity/', 'data/maps/BlackthornPokemonCenter/',
                'data/maps/BlackthornCenterUpstairs/', 'data/maps/BlackthornMart/', f'data/tilesets/secondary/{FOLDER}/')
    unexpected = sorted(p for p in set(changed) if p not in allowed and not p.startswith(prefixes))
    assert not unexpected, unexpected
    # Coordinate-labelled native grid for review.
    big = Image.fromarray(img).resize((W * 32, H * 32), Image.Resampling.NEAREST); d = ImageDraw.Draw(big)
    for i in range(W):
        d.line((i * 32, 0, i * 32, H * 32), fill=(60, 60, 70)); d.text((i * 32 + 2, 2), str(i), fill='white', stroke_width=1, stroke_fill='black')
    for i in range(H):
        d.line((0, i * 32, W * 32, i * 32), fill=(60, 60, 70)); d.text((2, i * 32 + 3), str(i), fill='white', stroke_width=1, stroke_fill='black')
    big.save(EV / 'elements' / 'native-grid.png')
    result = dict(style=style, cells_audited=len(trav), installed_matches_packer_decode=True,
                  ledger_behaviour_collision_elevation_layer=True, reachable_foot_cells=len(seen), open_cells=len(open_cells),
                  unreachable_open_cells=sorted(open_cells - surfed), open_cells_reached_only_by_surf=len(open_cells & surfed - seen),
                  approaches_needing_surf=[k for k, p in approaches.items() if p not in seen], approaches=approaches,
                  walk_behind_cells={k: len(v) for k, v in sorted(walk_behind.items())}, walk_behind=walk_behind,
                  shared_building_pixels_exact=int(shared.sum()), center_bank8_palette_identical_to_cherrygrove=True,
                  mart_bank9_palette_identical_to_shared_art=True, secondary_tiles=n_tiles, secondary_tile_limit=496,
                  secondary_metatiles=n_metas, metatile_limit=512, existing_map_ids_preserved=True,
                  changed_files_within_scope=True)
    (EV / 'elements' / 'native-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('walk_behind', 'approaches')}))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), sys.argv[2] if len(sys.argv) > 2 else 'C')
