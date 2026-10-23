"""Audit the installed element-built Olivine City (one native map) from its native files.

    python3 tools/gba/maps/olivine_elements/check_elements.py ENGINE_CHECKOUT [STYLE]   # STYLE C by default

Decodes data/layouts/OlivineCity with gTileset_OlivinePrimary and gTileset_OlivineCity
exactly as the game composes them (bottom layer, then the top layer's non-zero pixels)
and checks it against the packer's decode, the traversal ledger (behaviour, collision,
elevation, layer type per cell), reachability, the shared Center's and Mart's pixels and
the C06 master hash, the derived primary (Cherrygrove's open-sea tiles and kept banks
unchanged, its own callback playing the sea into those tiles only), walk-behind cells,
budgets and preservation.
Writes evidence/elements/native-audit.json and native-grid.png.
"""
from __future__ import annotations
import hashlib, json, subprocess, sys
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build as B                                   # noqa: E402
import pack as P                                    # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/olivine-elements'
SRC, EV = ART / 'source', ART / 'evidence'
W, H = 64, 64
NAME, FOLDER, PFOLDER = 'OlivineCity', 'olivine_city', 'olivine'
START = (16, 34)                                    # in front of the Center door
BASE = 'origin/claude/cianwood-city'                # the engine branch Olivine builds on
C06_SHA256 = '89034027c4b4f3241ad70baeeb104e23a571e521b76b27f388eb89123cc79f54'   # gba/art/johto-common/approved-buildings.json
MART_SHA256 = '03aa370bc2d4b1d7f869dde3dd318324d2484254f432a4f24ca9abf356a48ca8'  # the shared Johto Mart (Blackthorn's copy)

def tileset(d):
    a = np.array(Image.open(d / 'tiles.png')) & 15
    tiles = [a[y:y + 8, x:x + 8] for y in range(0, a.shape[0], 8) for x in range(0, a.shape[1], 8)]
    metas = np.frombuffer((d / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
    attrs = np.frombuffer((d / 'metatile_attributes.bin').read_bytes(), '<u2')
    return tiles, metas, attrs

def decode(g):
    prim, sec = g / f'data/tilesets/primary/{PFOLDER}', g / f'data/tilesets/secondary/{FOLDER}'
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
            elif foot.get(n) == 'ledge_east' and dx == 1 and foot.get((x + 2, y)) in passable and (x + 2, y) not in seen:
                seen.add((x + 2, y)); q.append((x + 2, y))
    return seen

def main(g, style):
    img, beh, layer, coll, elev, mid, n_sec_tiles, n_metas = decode(g)
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
    approaches = dict(center=(16, 34), mart=(29, 34), civic_hall=(13, 15), cafe=(9, 34), house_south=(17, 24),
                      house_north=(31, 18), house_northeast=(36, 18), lighthouse=(45, 40), pier_end=(23, 51),
                      north_exit=(23, 0), west_exit=(0, 35), stair_top=(35, 20), lighthouse_ramp=(39, 41),
                      city_sign=(23, 24), pier_sign=(24, 43), lighthouse_sign=(46, 41), east_cove=(53, 27))
    for k, p in approaches.items():
        assert p in surfed, ('unreachable approach', k, p)
    # Depth: a walkable cell draws its art above the player (layer type normal) exactly
    # when that art's object stands further south (P.above_player: a roof or crown the
    # player walks behind); doors and other base-row cells, and every blocked cell, keep
    # their art below the player (covered).
    comp = np.load(SRC / 'elements' / f'compose-{style}.npz', allow_pickle=True)
    art = (comp['top'][..., 3] > 0) | (comp['shared'][..., 3] > 0)
    owner = comp['owner']
    walkable = np.array([[foot[(x, y)] in ('open', 'door', 'water') for x in range(W)] for y in range(H)])
    above = P.above_player(walkable, comp['top'], comp['shared'], owner)
    walk_behind, behind_player = {}, {}
    for y, x in np.ndindex(H, W):
        cell = art[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
        who = sorted(set(owner[y * 16:y * 16 + 16, x * 16:x * 16 + 16][cell].ravel()) - {''}) or ['terrain']
        if above[y, x]:
            assert layer[y, x] == 0, ('walk-behind art not drawn above the player', x, y)
            for o in who:
                walk_behind.setdefault(o, []).append([x, y])
        else:
            assert layer[y, x] == 1, ('art drawn above the player in front of its object', x, y)
            if walkable[y, x] and cell.any():
                for o in who:
                    behind_player.setdefault(o, []).append([x, y])
    # Shared Center and Mart: the locked C06 master and the shared Mart, every opaque pixel
    # exact in the installed map.
    assert hashlib.sha256((SRC / 'shared-art/pokemon-center.png').read_bytes()).hexdigest() == C06_SHA256
    assert hashlib.sha256((SRC / 'shared-art/poke-mart.png').read_bytes()).hexdigest() == MART_SHA256
    shared = comp['shared'][..., 3] > 0
    assert (B.rgb5(img)[shared] == B.rgb5(comp['shared'][..., :3])[shared]).all()
    # The derived primary: Cherrygrove's tile 0 and open-sea tiles 1-16 at their own
    # indices, Olivine's callback playing Cherrygrove's sea frames into those 16 and no
    # further; banks 0 and 1 unchanged, bank 3 unchanged in every slot a Cherrygrove tile draws.
    cp, op = g / 'data/tilesets/primary/cherrygrove', g / f'data/tilesets/primary/{PFOLDER}'
    ct, ot = tileset(cp)[0], tileset(op)[0]
    assert all((ct[i] == ot[i]).all() for i in range(P.ANIM)), 'sea animation tiles moved'
    for b in (0, 1, 3):
        a, o = B.read_pal(cp / f'palettes/{b:02}.pal'), B.read_pal(op / f'palettes/{b:02}.pal')
        free = set(P.TREE_BANK_GREENS) if b == 3 else set()
        assert all(a[i] == o[i] for i in range(16) if i not in free), ('kept bank changed', b)
    assert 'InitTilesetAnim_OlivinePrimary' in (g / 'src/data/tilesets/headers.h').read_text().split('gTileset_OlivinePrimary =')[1].split(';')[0]
    anim = (g / 'src/tileset_anims.c').read_text().split('// Claude Olivine sea')[1].split('// End Claude Olivine sea')[0]
    assert f'TILE_OFFSET_4BPP(1)), {P.ANIM - 1} * TILE_SIZE_4BPP' in anim and 'gTilesetAnims_Cherrygrove_Sea[' in anim
    # Budgets: 512 primary tiles and metatiles; 496 secondary tiles (16 kept for door
    # animation), 512 secondary metatiles.
    n_tiles = n_sec_tiles                                       # tiles.png pads its last row of 16
    assert n_tiles <= 496 and n_metas <= 512 and len(ot) <= 512, (n_tiles, n_metas, len(ot))
    # Preservation: existing map ids keep their order; only Olivine files changed.
    before = json.loads(subprocess.check_output(['git', '-C', str(g), 'show', f'{BASE}:data/maps/map_groups.json']))
    groups = json.loads((g / 'data/maps/map_groups.json').read_text())
    for key, values in before.items():
        if isinstance(values, list):
            assert groups[key][:len(values)] == values, key
    changed = subprocess.check_output(['git', '-C', str(g), 'diff', '--name-only', BASE], text=True).splitlines()
    changed += subprocess.check_output(['git', '-C', str(g), 'ls-files', '--others', '--exclude-standard'], text=True).splitlines()
    allowed = {'data/event_scripts.s', 'data/layouts/layouts.json', 'data/maps/map_groups.json', 'include/regions.h',
               'src/apocrypha_map_proof.c', 'src/data/region_map/region_map_sections.json', 'src/data/tilesets/graphics.h',
               'src/data/tilesets/headers.h', 'src/data/tilesets/metatiles.h', 'src/tileset_anims.c', 'include/tileset_anims.h'}
    prefixes = (f'data/layouts/{NAME}/', 'data/maps/OlivineCity/', 'data/maps/OlivinePokemonCenter/',
                'data/maps/OlivineCenterUpstairs/', 'data/maps/OlivineMart/', f'data/tilesets/secondary/{FOLDER}/',
                f'data/tilesets/primary/{PFOLDER}/')
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
                  walkable_cells_with_art_below_player=behind_player,
                  shared_building_pixels_exact=int(shared.sum()), center_master_sha256=C06_SHA256, mart_sha256=MART_SHA256,
                  primary_tiles=len(ot), sea_animation_tiles_kept=True,
                  secondary_tiles=n_tiles, secondary_tile_limit=496,
                  secondary_metatiles=n_metas, metatile_limit=512, existing_map_ids_preserved=True,
                  changed_files_within_scope=True)
    (EV / 'elements' / 'native-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('walk_behind', 'approaches')}))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), sys.argv[2] if len(sys.argv) > 2 else 'C')
