"""Audit the installed Saffron City (KantoSaffronCity) from its native files.

    python3 tools/gba/maps/saffron/check.py ENGINE_CHECKOUT

Decodes data/layouts/KantoSaffronCity with gTileset_KantoSaffronPrimary and
gTileset_KantoSaffronCity exactly as the game composes them (bottom layer, then the top
layer's non-zero pixels) and checks it against compose.py's picture and the packer's
decode; FireRed's palettes (every bank as FireRed has it, banks 11 and 12 as frlg.graded
makes them); the station sprite's pixels; the traversal ledger (behaviour, collision,
elevation, layer type per cell, FireRed's layer type everywhere but the station);
reachability; the signs and doors in map.json; the Center and Mart door animation;
budgets and preservation.
Writes evidence/native-audit.json and evidence/native-grid.png.
"""
from __future__ import annotations
import json, subprocess, sys
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(HERE), str(HERE.parent / 'olivine_elements')]
import build as B                                   # noqa: E402
import frlg                                         # noqa: E402
import compose as C                                 # noqa: E402
import pack as P                                    # noqa: E402

ART = ROOT / 'gba/art/saffron-kanto'
SRC, EV = ART / 'source', ART / 'evidence'
W, H = C.W, C.H
NAME, PFOLDER, FOLDER = 'KantoSaffronCity', 'kanto_saffron', 'kanto_saffron_city'
START = (24, 39)                                    # in front of the Center door
BASE = 'origin/claude/olivine-city'                 # the engine branch Saffron builds on

def tileset(d):
    a = np.array(Image.open(d / 'tiles.png')) & 15
    tiles = [a[y:y + 8, x:x + 8] for y in range(0, a.shape[0], 8) for x in range(0, a.shape[1], 8)]
    metas = np.frombuffer((d / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
    attrs = np.frombuffer((d / 'metatile_attributes.bin').read_bytes(), '<u2')
    return tiles, metas, attrs

def render_blocks(g, blocks):
    """Map blocks (metatile id | collision << 10 | elevation << 12), any shape, drawn with
    the installed pair as the game composes them (a bottom pixel of colour 0 shows
    frlg.under's fill); with each cell's attributes."""
    prim, sec = g / f'data/tilesets/primary/{PFOLDER}', g / f'data/tilesets/secondary/{FOLDER}'
    pt, pm, pa = tileset(prim)
    st, sm, sa = tileset(sec)
    pals = [B.read_pal((prim if i < 6 else sec) / 'palettes' / f'{i:02}.pal') for i in range(16)]
    tiles = pt[:512] + [np.zeros((8, 8), np.uint8)] * (512 - len(pt[:512])) + st
    metas, attrs = list(pm[:512]) + list(sm), list(pa[:512]) + list(sa)
    h, w = blocks.shape
    img = np.zeros((h * 16, w * 16, 3), np.uint8)
    beh, layer, coll, elev, mid = (np.zeros((h, w), np.int32) for _ in range(5))
    for y, x in np.ndindex(h, w):
        v = int(blocks[y, x]); m = v & 1023
        mid[y, x], coll[y, x], elev[y, x] = m, (v >> 10) & 3, v >> 12
        beh[y, x], layer[y, x] = int(attrs[m]) & 0xFF, (int(attrs[m]) >> 12) & 3
        fill = frlg.under(tiles[frlg.FILL_TILE], layer[y, x], pals)
        for i, e in enumerate(metas[m]):
            e = int(e); t = tiles[e & 1023]
            if e & 1024: t = t[:, ::-1]
            if e & 2048: t = t[::-1]
            q = i % 4; oy, ox = y * 16 + (q // 2) * 8, x * 16 + (q % 2) * 8
            if i < 4:
                img[oy:oy + 8, ox:ox + 8] = np.where((t == 0)[..., None], fill, np.array(pals[e >> 12], np.uint8)[t])
            else:
                img[oy:oy + 8, ox:ox + 8][t > 0] = np.array(pals[e >> 12])[t[t > 0]]
    return dict(img=img, beh=beh, layer=layer, coll=coll, elev=elev, mid=mid, pals=pals,
                prim_tiles=len(pt), sec_tiles=len(st), prim_metas=len(pm), sec_metas=len(sm))

def decode(g):
    grid = np.frombuffer((g / f'data/layouts/{NAME}/map.bin').read_bytes(), '<u2').reshape(H, W)
    return render_blocks(g, grid)

def border_image(g):
    """The 2x2 border block as the camera sees it past the map's edges."""
    border = np.frombuffer((g / f'data/layouts/{NAME}/border.bin').read_bytes(), '<u2').reshape(2, 2)
    return render_blocks(g, border)['img']

def reach(foot):
    seen = {START}; q = deque([START])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if foot.get(n) in ('open', 'door') and n not in seen:
                seen.add(n); q.append(n)
            elif foot.get(n) == 'ledge_south' and dy == 1 and foot.get((x, y + 2)) in ('open', 'door') and (x, y + 2) not in seen:
                seen.add((x, y + 2)); q.append((x, y + 2))
    return seen

def main(g):
    d = decode(g)
    img = d['img']
    comp = np.load(SRC / 'compose.npz')
    want = frlg.flat(comp['bottom'], comp['top'])
    assert (B.rgb5(img) == B.rgb5(want)).all(), 'installed map differs from compose.py'
    built = np.array(Image.open(EV / 'native.png').convert('RGB'))
    assert (B.rgb5(img) == B.rgb5(built)).all(), 'installed map differs from the packer decode'
    # FireRed's palettes: every bank Saffron draws as FireRed has it, banks 11 and 12 graded.
    pair = frlg.Pair(g, C.PRIMARY, C.SECONDARY)
    graded = frlg.graded(pair.pals)
    for b in P.FRLG_BANKS:
        ref = graded[b] if b in frlg.GRADE else pair.pals[b]
        assert [tuple(v >> 3 for v in c) for c in d['pals'][b]] == [tuple(v >> 3 for v in c) for c in ref], ('bank', b)
    # The station: every opaque sprite pixel exact; its cells blocked and drawn below the player.
    sprite, sx, sy = C.station_sprite()
    a = sprite[..., 3] > 0
    region = img[sy:sy + sprite.shape[0], sx:sx + sprite.shape[1]]
    assert (B.rgb5(region)[a] == B.rgb5(sprite[..., :3])[a]).all(), 'station pixels'
    station = comp['station_cells']
    assert (d['coll'][station] == 1).all() and (d['layer'][station] == 1).all(), 'station cells'
    assert (d['mid'][station] >= 512).all() and (d['mid'][comp['art']] >= 512).all(), 'art metatiles outside the secondary'
    # The traversal ledger.
    trav = json.loads((SRC / 'traversal.json').read_text())
    for c in trav:
        x, y = c['x'], c['y']
        assert d['beh'][y, x] == c['behavior'], (x, y, c['behavior'])
        assert d['coll'][y, x] == c['collision'] and d['elev'][y, x] == c['elevation'], (x, y)
        assert d['layer'][y, x] == (0 if c['layer'] == 'normal' else 1), (x, y)
    # Every cell but the station's draws in FireRed's layer type for its (edited) metatile.
    for y, x in np.ndindex(H, W):
        if not station[y, x]:
            assert d['layer'][y, x] == pair.layer_type(int(comp['edited'][y, x]) & 0x3FF), ('layer type', x, y)
    MB = B.behaviors(g)
    foot = {}
    for c in trav:
        k = (c['x'], c['y'])
        foot[k] = ('door' if c['behavior'] == MB['MB_ANIMATED_DOOR'] else 'ledge_south' if c['behavior'] == MB['MB_JUMP_SOUTH']
                   else 'open' if c['collision'] == 0 else 'blocked')
    seen = reach(foot)
    open_cells = {k for k, v in foot.items() if v in ('open', 'door')}
    m = json.loads((g / f'data/maps/{NAME}/map.json').read_text())
    approaches = dict(center=(24, 39), mart=(40, 22), silph=(33, 31), station=(25, 15), fighting_dojo=(40, 13),
                      psychic_dojo=(46, 13), league_office=(47, 22), copycat_house=(19, 22), mr_psychic=(43, 39),
                      south_gate=(34, 45), plaza=(44, 15))
    approaches.update({f'sign_{b["script"].split("_", 1)[1]}': (b['x'], b['y'] + 1) for b in m['bg_events']})
    for k, p in approaches.items():
        assert p in seen, ('unreachable approach', k, p)
    # Every FireRed warp (solid now unless it is the Center's or the Mart's) still has a
    # reachable cell beside it, as do the station's and the Copycat's new doors. The gates'
    # outer doors (west, east and south) face Routes 7, 8 and 6, outside the city's walls.
    adapted = [(c['x'], c['y']) for c in trav if 'adaptation' in c]
    frlg_warps = {(w['x'], w['y']) for w in json.loads((g / 'data/maps/SaffronCity_Frlg/map.json').read_text())['warp_events']}
    copycat = tuple(int(v) for v in np.add(C.COPYCAT_HOUSE, (1, 1)))
    must_reach = sorted(frlg_warps - {(22, 14)} | {C.STATION_DOOR, copycat})    # (22, 14): the Copycat's old door, under the station
    for x, y in must_reach:
        assert any(n in seen for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))), ('door out of reach', x, y)
    outer_gate_doors = sorted(p for p in adapted if p not in must_reach)
    assert not any(n in seen for x, y in outer_gate_doors for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))), \
        outer_gate_doors
    # Signs on blocked cells: FireRed's signposts, and the station sign on its door.
    for b in m['bg_events']:
        x, y = b['x'], b['y']
        assert d['coll'][y, x] == 1, ('sign on a walkable cell', x, y)
        assert d['beh'][y, x] == MB['MB_SIGNPOST'] or (x, y) == C.STATION_DOOR, ('sign off a signpost', x, y)
    doors = {(w['x'], w['y']): w['dest_map'] for w in m['warp_events']}
    assert set(doors) == set(P.OPEN_DOORS) and all(foot[p] == 'door' for p in doors), doors
    # The Center and Mart doors animate: FireRed's sliding door on their metatile, drawn in
    # the primary's bank 3 (FireRed's own).
    dx, dy = next(iter(P.OPEN_DOORS))
    door_mid = int(d['mid'][dy, dx])
    fd = (g / 'src/field_door.c').read_text()
    entry = f'{{.metatileNum={door_mid}, .tileset=&gTileset_KantoSaffronPrimary, .sound=DOOR_SOUND_SLIDING, .size=DOOR_SIZE_1x1, '
    assert entry in fd and 'sKantoSaffronDoorPal_Sliding[] = {3, 3, 3, 3, 3, 3, 3, 3}' in fd
    assert all(int(d['mid'][y, x]) == door_mid for x, y in P.OPEN_DOORS)
    assert d['pals'][3] == B.read_pal(g / 'data/tilesets/primary/general_frlg/palettes/03.pal')
    # The engine's BG3 fill under normal-layer cells is FireRed's own tile 0x14.
    prim_tiles = tileset(g / f'data/tilesets/primary/{PFOLDER}')[0]
    assert (prim_tiles[frlg.FILL_TILE] == pair.tiles[frlg.FILL_TILE]).all(), 'fill tile'
    # Budgets: 512 primary tiles and metatiles; 496 secondary tiles (16 kept for door
    # animation), 512 secondary metatiles.
    assert d['prim_tiles'] <= 512 and d['prim_metas'] == 512 and d['sec_metas'] <= 512, d
    assert d['sec_tiles'] <= 496 + 15, d['sec_tiles']             # tiles.png pads its last row of 16
    sec_used = int(json.loads((EV / 'pack.json').read_text())['secondary_tiles'])
    assert sec_used <= 496
    # Preservation: existing map ids keep their order; only Saffron files changed.
    before = json.loads(subprocess.check_output(['git', '-C', str(g), 'show', f'{BASE}:data/maps/map_groups.json']))
    groups = json.loads((g / 'data/maps/map_groups.json').read_text())
    for key, values in before.items():
        assert groups[key][:len(values)] == values, key
    changed = subprocess.check_output(['git', '-C', str(g), 'diff', '--name-only', BASE], text=True).splitlines()
    changed += subprocess.check_output(['git', '-C', str(g), 'ls-files', '--others', '--exclude-standard'], text=True).splitlines()
    allowed = {'data/event_scripts.s', 'data/layouts/layouts.json', 'data/maps/map_groups.json', 'src/apocrypha_map_proof.c',
               'src/data/tilesets/graphics.h', 'src/data/tilesets/headers.h', 'src/data/tilesets/metatiles.h', 'src/field_door.c'}
    prefixes = (f'data/layouts/{NAME}/', 'data/maps/KantoSaffron', f'data/tilesets/primary/{PFOLDER}/',
                f'data/tilesets/secondary/{FOLDER}/')
    unexpected = sorted(p for p in set(changed) if p not in allowed and not p.startswith(prefixes))
    assert not unexpected, unexpected
    # Coordinate-labelled native grid for review.
    big = Image.fromarray(img).resize((W * 32, H * 32), Image.Resampling.NEAREST); dr = ImageDraw.Draw(big)
    for i in range(W):
        dr.line((i * 32, 0, i * 32, H * 32), fill=(60, 60, 70)); dr.text((i * 32 + 2, 2), str(i), fill='white', stroke_width=1, stroke_fill='black')
    for i in range(H):
        dr.line((0, i * 32, W * 32, i * 32), fill=(60, 60, 70)); dr.text((2, i * 32 + 3), str(i), fill='white', stroke_width=1, stroke_fill='black')
    big.save(EV / 'native-grid.png')
    result = dict(cells_audited=len(trav), installed_matches_compose=True, installed_matches_packer_decode=True,
                  frlg_palettes_kept=[b for b in P.FRLG_BANKS if b not in frlg.GRADE], graded_banks=sorted(frlg.GRADE),
                  station_pixels_exact=int(a.sum()), station_cells=int(station.sum()),
                  ledger_behaviour_collision_elevation_layer=True, frlg_layer_types_outside_station=True,
                  reachable_foot_cells=len(seen), open_cells=len(open_cells),
                  unreachable_open_cells=sorted(open_cells - seen), approaches=approaches,
                  doors_reached=must_reach, outer_gate_doors=outer_gate_doors, solid_former_doors=len(adapted), signs=len(m['bg_events']),
                  open_doors={f'{x},{y}': v for (x, y), v in doors.items()}, door_metatile=door_mid,
                  primary_tiles=d['prim_tiles'], secondary_tiles=sec_used, secondary_tile_limit=496,
                  primary_metatiles=d['prim_metas'], secondary_metatiles=d['sec_metas'], metatile_limit=512,
                  existing_map_ids_preserved=True, changed_files_within_scope=True)
    (EV / 'native-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'approaches'}))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
