"""Celadon's rooms: FireRed's own, repurposed, on Emerald-format tilesets.

    python3 tools/gba/maps/celadon_elements/interiors.py ENGINE_CHECKOUT

Chapter 6's retheme (CHAPTER6_SCENES_SPEC.md, "Repurpose interiors, don't rebuild"): each room
is FireRed's as it is, drawn cell by cell from FireRed's metatiles (frlg.Pair) and packed from
its pixels into a secondary of its own on Emerald's gTileset_Building primary: every 8x8 tile
its exact 5-bit colours in palette banks 6-12 (one exact fit), each tile kept once (any flip),
each cell's layer type and collision FireRed's.

    services     the market's services building (HGSS's Dept Store): FireRed's Dept Store 1F
                 (its counters for the salon, the move tutor and EV training); both its exit
                 mats lead to the one HGSS door
    hotel_1f     the Pokemon Hotel's lobby (HGSS's Condominiums) and hotel_2f its upper floor
                 (Looker's room): FireRed's Condominiums 1F and 2F, the stairs between them
    cafe         FireRed's Restaurant (HGSS's restaurant)
    gardens      the glasshouse: FireRed's Celadon Gym, its garden as it is
    game_corner  FireRed's Game Corner, and prize_room its prize room
    apartments   the apartment block (HGSS's tower, 238): HGSS's Condominiums 1F (hgss_rooms.py,
                 T07R0201) cell for cell, drawn in FireRed's Condominiums pieces (owner,
                 2026-11-01): the elevator, directory board, display cabinet and two windows on its
                 back wall, the plants, the inner block with the stairs up in its corner, the mat
                 under HGSS's door; the elevator and stairs solid until the floors above exist
    cade_house   Cade's house (the plum house beside the Game Corner; owner, 2026-11-01):
                 FireRed's Celadon house (House5's layout), empty until Cade's scene is written

Behaviour: the exit mats keep MB_SOUTH_ARROW_WARP and the hotel's stairs their stair warps;
every other cell is MB_NORMAL (FireRed's counters, slot machines and signposts need scripts the
rooms do not have yet). A warp cell to a place not built (the store's upper floors and
elevator, the old condominiums' 3F and back door, the Game Corner's stairs down) is solid.

Writes gba/art/celadon-elements/source/interiors/*.npz, events.json and evidence/interiors/*.png.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

import common as C
sys.path.append(str(C.HERE.parent / 'saffron'))
import frlg                                     # noqa: E402  (Saffron's FireRed reader)
import build as B                               # noqa: E402
import pack as P                                # noqa: E402  (key5)
import pack_olivine_shim as O                   # noqa: E402  (exact_banks)

OUT, EV = C.SRC / 'interiors', C.EV / 'interiors'
BANKS = list(range(6, 13))                      # a secondary's palette banks
TILE_LIMIT = 512
METATILE_LIMIT = 512

# room: (FireRed map, its secondary's folder, the warps kept: (x, y) -> (destination key, its warp key))
# Destination keys: 'city:<door>' a city door (install.py numbers them), '<room>:<n>' another
# room's n-th kept warp.
ROOMS = {
    'services': ('CeladonCity_DepartmentStore_1F_Frlg', 'department_store_frlg',
                 {(1, 15): 'city:services', (2, 14): 'city:services', (3, 15): 'city:services',
                  (9, 15): 'city:services', (10, 14): 'city:services', (11, 15): 'city:services'}),
    'hotel_1f': ('CeladonCity_Condominiums_1F_Frlg', 'condominiums_frlg',
                 {(11, 19): 'city:hotel', (12, 18): 'city:hotel', (13, 19): 'city:hotel',
                  (4, 2): 'hotel_2f:0', (12, 2): 'hotel_2f:1'}),
    'hotel_2f': ('CeladonCity_Condominiums_2F_Frlg', 'condominiums_frlg',
                 {(4, 2): 'hotel_1f:3', (12, 2): 'hotel_1f:4'}),
    'cafe': ('CeladonCity_Restaurant_Frlg', 'restaurant_hotel_frlg',
             {(5, 9): 'city:cafe', (6, 9): 'city:cafe', (7, 9): 'city:cafe'}),
    'gardens': ('CeladonCity_Gym_Frlg', 'celadon_gym_frlg',
                {(5, 18): 'city:gardens', (6, 18): 'city:gardens', (7, 18): 'city:gardens'}),
    # Round 6 (owner, 2026-10-27): no prize house; the prize counter is in the Game Corner,
    # up its stairs (FireRed's stairs down to the hideout) in FireRed's prize room.
    'game_corner': ('CeladonCity_GameCorner_Frlg', 'game_corner_frlg',
                    {(9, 13): 'city:gamecorner', (10, 13): 'city:gamecorner', (11, 13): 'city:gamecorner',
                     (15, 2): 'prize_room:1'}),
    'prize_room': ('CeladonCity_GameCorner_PrizeRoom_Frlg', 'game_corner_frlg',
                   {(3, 9): 'game_corner:3', (4, 8): 'game_corner:3', (5, 9): 'game_corner:3'}),
    # Owner, 2026-11-01: the apartments open, their room HGSS's Condominiums 1F; the plum house is
    # Cade's, open with an empty room.
    'apartments': ('@apartments', 'condominiums_frlg',
                   {(5, 13): 'city:apartments', (6, 12): 'city:apartments', (7, 13): 'city:apartments'}),
    'cade_house': ('CeladonCity_House1_Frlg', 'generic_building_1_frlg',
                   {(3, 7): 'city:house_g0', (4, 7): 'city:house_g0', (5, 7): 'city:house_g0'}),
}
LAYOUTS = {'CeladonCity_House1_Frlg': 'House5_Frlg'}     # a FireRed map whose layout has another name

KEEP = ('MB_SOUTH_ARROW_WARP', 'MB_UP_RIGHT_STAIR_WARP', 'MB_DOWN_RIGHT_STAIR_WARP', 'MB_UP_LEFT_STAIR_WARP',
        'MB_DOWN_LEFT_STAIR_WARP')

def room_cells(engine, name):
    mapname, sec, _ = ROOMS[name]
    pair = frlg.Pair(engine, 'building_frlg', sec)
    if mapname.startswith('@'):
        return pair, BUILT[mapname[1:]]()
    grid, _ = frlg.layout(engine, LAYOUTS.get(mapname, mapname))
    return pair, grid

# --------------------------------------------------------------------------- rooms built from HGSS's
# HGSS's Condominiums 1F (gba/art/celadon-elements/source/hgss-rooms/condominiums_1f): its floor
# x 1-15, rows 3-13 (a Gen 3 room drops HGSS's outer wall column and its top wall row, so a cell
# is HGSS's less one each way), the back wall two rows high as FireRed draws it. FireRed's
# Condominiums metatiles: 289/291 wall, 281 floor, 282 the floor's shaded edge, 2db/2dc/2eb and
# 2e3/2e4/2ec its doorway, 28b/293 the board, 2f8/2f9 a window, 2ba-2bd the display cabinet,
# 2ca/2c9 over 2d1 a plant, 2a1 floor meeting a wall top, 294 a wall's left side, the stairs
# 2f1/2ad and 2ae-2bf, 2e8-2ea the mat, 1a-1c the exit.
def apartments_grid():
    """HGSS's Condominiums 1F in FireRed's Condominiums pieces: metatile | collision << 10 | elevation << 12."""
    W, H = 15, 14
    FLOOR, SHADE = 0x281, 0x282
    m = np.full((H, W), FLOOR, int); coll = np.zeros((H, W), int)
    m[2, :] = SHADE; m[:, 0] = SHADE
    m[0, :] = 0x289; m[1, :] = 0x291; coll[0:2, :] = 1
    m[0, 2:5] = [0x2db, 0x2dc, 0x2eb]; m[1, 2:5] = [0x2e3, 0x2e4, 0x2ec]   # the elevator (HGSS (3, 2)), FireRed's doorway and frame
    m[0, 5], m[1, 5] = 0x28b, 0x293                                  # the directory board (HGSS's sign, (5, 2))
    m[0, 8:10] = [0x2ba, 0x2bb]; m[1, 8:10] = [0x2c2, 0x2c3]; m[2, 8:10] = [0x2bc, 0x2bd]; coll[2, 8:10] = 1   # HGSS's cabinet (9-10, 3)
    m[0, 11], m[1, 11] = 0x2f8, 0x2f9; m[0, 13], m[1, 13] = 0x2f8, 0x2f9   # HGSS's two windows
    m[1, 0], m[2, 0] = 0x2ca, 0x2d1; coll[2, 0] = 1                  # plant (HGSS (1, 3))
    m[11, 0], m[12, 0] = 0x2c9, 0x2d1; coll[12, 0] = 1               # plant (HGSS (1, 12-13))
    # the inner block, HGSS x 9-16 rows 7-11, the stair nook in its south-east corner
    m[5, 8:15] = 0x2a1
    m[6:9, 8:15] = 0x8; coll[6:11, 8:15] = 1
    m[6:9, 8] = 0x294
    m[9, 8:12] = 0x289; m[10, 8:12] = 0x291
    m[9:11, 12:15] = 0x8
    m[7, 12:15] = [0x289, 0x289, 0x289]; m[8, 12:15] = [0x291, 0x2ae, 0x2af]
    m[9, 12:15] = [0x2f1, 0x2b6, 0x2b7]; m[10, 12:15] = [0x2ad, 0x2be, 0x2bf]
    coll[9, 12] = 1                                                   # the stairs up: 2F not built
    m[11, 8:15] = SHADE
    m[12, 5:8] = [0x2e8, 0x2e9, 0x2ea]                               # the mat under HGSS's door (7, 13)
    m[13, :] = 0x8; coll[13, :] = 1; m[13, 5:8] = [0x1a, 0x1b, 0x1c]
    elev = np.where(coll == 0, 3, 0)
    return (m | (coll << 10) | (elev << 12)).astype(np.uint16)

BUILT = dict(apartments=apartments_grid)

def draw(pair, grid):
    H, W = grid.shape
    bot = np.zeros((H * 16, W * 16, 3), np.uint8)
    top = np.zeros((H * 16, W * 16, 4), np.uint8)
    info = []
    for y in range(H):
        row = []
        for x in range(W):
            v = int(grid[y, x]); mid = v & 0x3FF
            b, t = pair.cell(mid)
            bot[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = b
            top[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = t
            row.append(dict(metatile=mid, collision=(v >> 10) & 3, elevation=v >> 12, layer=pair.layer_type(mid),
                            frlg_behavior=pair.behavior(mid)))
        info.append(row)
    return bot, top, info

def pack(bot, top, info, behaviors, keep):
    """One exact Emerald-format secondary for a room: tiles, banks 6-12, metatiles. A cell in
    `keep` keeps its FireRed behaviour; every other cell is MB_NORMAL."""
    H, W = len(info), len(info[0])
    jobs, lay = {}, {}
    for ty in range(H * 2):
        for tx in range(W * 2):
            sl = np.s_[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            for layer, px, mask in ((0, bot[sl], np.ones((8, 8), bool)), (1, top[sl][..., :3], top[sl][..., 3] > 0)):
                if layer == 1 and not mask.any():
                    lay[(tx, ty, 1)] = None
                    continue
                k = (P.key5(px, None if layer == 0 else mask), layer)
                j = jobs.setdefault(k, dict(px=B.rgb5(px).reshape(64, 3), mask=mask.ravel().astype(np.uint8), weight=0, layer=layer))
                j['weight'] += 1
                lay[(tx, ty, layer)] = k
    order = list(jobs.values())
    packed, assign, _, lost = O.exact_banks(order, len(BANKS))
    assert not lost, ('a tile fits no bank', len(lost))
    packed = [sorted(set(p)) for p in packed]
    pals = [(c or [(0, 0, 0)]) + [(c or [(0, 0, 0)])[-1]] * (15 - len(c or [(0, 0, 0)])) for c in packed]
    patterns = {}
    for j, a in zip(order, assign):
        j['bank'] = BANKS[a]
        pal = np.array(pals[a], float)
        ix = (((j['px'][:, None, :].astype(float) - pal[None]) ** 2 * B.CH_W).sum(-1).argmin(-1) + 1).astype(np.uint8)
        if j['layer'] == 1:
            ix = np.where(j['mask'] > 0, ix, 0).astype(np.uint8)
        vs = B.flips(ix.reshape(8, 8))
        o = min(range(4), key=lambda i: vs[i].tobytes())
        j['pattern'], j['flip'] = patterns.setdefault(vs[o].tobytes(), len(patterns)), o
    assert len(patterns) <= TILE_LIMIT, ('tiles over budget', len(patterns))
    tiles = [np.frombuffer(kk, np.uint8).reshape(8, 8) for kk, _ in sorted(patterns.items(), key=lambda kv: kv[1])]

    def entry(k):
        if k is None:
            return 0
        j = jobs[k]
        return (512 + j['pattern']) | ((j['flip'] & 1) << 10) | ((j['flip'] >> 1) << 11) | (j['bank'] << 12)

    metas, grid = {}, np.zeros((H, W), np.uint16)
    behaviour = np.zeros((H, W), np.uint16)
    for y in range(H):
        for x in range(W):
            c = info[y][x]
            q = [(2 * x, 2 * y), (2 * x + 1, 2 * y), (2 * x, 2 * y + 1), (2 * x + 1, 2 * y + 1)]
            ents = [entry(lay[(a, b, 0)]) for a, b in q] + [entry(lay[(a, b, 1)]) for a, b in q]
            mb = c['frlg_behavior'] if (x, y) in keep else behaviors['MB_NORMAL']
            behaviour[y, x] = mb
            key = (tuple(ents), mb | (c['layer'] << 12))
            mid = metas.setdefault(key, 512 + len(metas))
            grid[y, x] = mid | (c['collision'] << 10) | (c['elevation'] << 12)
    assert len(metas) <= METATILE_LIMIT, ('metatiles over budget', len(metas))
    pal_rgb = np.zeros((16, 16, 3), np.uint8)
    for b, p in zip(BANKS, pals):
        for i, c in enumerate(p[:15]):
            pal_rgb[b, i + 1] = [(v << 3) | (v >> 2) for v in c]
    meta = np.array([list(k[0]) + [k[1]] for k, _ in sorted(metas.items(), key=lambda kv: kv[1])], np.uint16)
    return dict(grid=grid, tiles=np.array(tiles, np.uint8), palettes=pal_rgb, meta=meta, behaviour=behaviour,
                collision=np.array([[c['collision'] for c in r] for r in info], np.uint8),
                elevation=np.array([[c['elevation'] for c in r] for r in info], np.uint8))

def decode(p):
    """The packed room as the game draws it (bottom layer opaque, then the top)."""
    H, W = p['grid'].shape
    out = np.zeros((H * 16, W * 16, 3), np.uint8)
    for y in range(H):
        for x in range(W):
            ents = p['meta'][(int(p['grid'][y, x]) & 0x3FF) - 512][:8]
            for li, e in enumerate(ents):
                e = int(e)
                if li >= 4 and e == 0:
                    continue
                ix = p['tiles'][(e & 1023) - 512]
                if e & 0x400: ix = ix[:, ::-1]
                if e & 0x800: ix = ix[::-1]
                q = li % 4
                oy, ox = y * 16 + (q // 2) * 8, x * 16 + (q % 2) * 8
                m = ix > 0 if li >= 4 else np.ones((8, 8), bool)
                out[oy:oy + 8, ox:ox + 8][m] = p['palettes'][e >> 12][ix[m]]
    return out

def main(engine):
    MB = B.behaviors(engine)
    keep_mb = {MB[k] for k in KEEP}
    OUT.mkdir(parents=True, exist_ok=True)
    EV.mkdir(parents=True, exist_ok=True)
    report = {}
    for name, (mapname, sec, warps) in ROOMS.items():
        pair, grid = room_cells(engine, name)
        bot, top, info = draw(pair, grid)
        frlg_warps = list(warps) if mapname.startswith('@') else             [(w['x'], w['y']) for w in json.loads((engine / f'data/maps/{mapname}/map.json').read_text())['warp_events']]
        keep = {xy for xy in warps if info[xy[1]][xy[0]]['frlg_behavior'] in keep_mb}
        dead = [xy for xy in frlg_warps if xy not in warps]
        for x, y in dead:
            info[y][x]['collision'] = 1
        p = pack(bot, top, info, MB, keep)
        want = frlg.flat(bot, top)
        got = decode(p)
        d5 = np.abs(B.rgb5(got) - B.rgb5(want)).max(-1)
        assert d5.max() == 0, (name, 'packed room differs from its picture', int((d5 > 0).sum()))
        np.savez_compressed(OUT / f'{name}.npz', **p)
        Image.fromarray(got).resize((got.shape[1] * 2, got.shape[0] * 2), Image.Resampling.NEAREST).save(EV / f'{name}.png')
        h, w = p['grid'].shape
        report[name] = dict(source=mapname, size=[w, h], tiles=len(p['tiles']), metatiles=len(p['meta']), pixels_exact=True,
                            warps=[dict(x=x, y=y, to=to) for (x, y), to in warps.items()], solid_warps=[list(xy) for xy in dead],
                            walkable=int((p['collision'] == 0).sum()))
        for (x, y), to in warps.items():
            assert p['collision'][y, x] == 0 or info[y][x]['frlg_behavior'] == MB['MB_NORMAL'], (name, 'warp blocked', x, y)
        print(name, {k: v for k, v in report[name].items() if k not in ('warps',)})
    (OUT / 'events.json').write_text(json.dumps(report, indent=1) + '\n')

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
