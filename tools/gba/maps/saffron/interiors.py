"""Saffron's two new interiors, from FireRed's own rooms, on Emerald-format tilesets.

    python3 tools/gba/maps/saffron/interiors.py ENGINE_CHECKOUT

    dojo   the Saffron Dojo's one hall (the owner's brief, 2026-10-24: the Fighting and
           Psychic Dojos "each with an individual entrance but a shared interior"):
           FireRed's Fighting Dojo (SaffronCity_Dojo) built out to twice its width, one
           wall, one tatami arena for both schools; the west end FireRed's floor and
           statues, the east end Sabrina's Gym statues and pink diamond rug laid on the
           Dojo's wood (overlays: the Gym's own pixels without its floor). An exit mat at
           each end: the west mat back to the Fighting door (40, 12), the east mat to the
           Psychic door (45, 12).
    lab    Silph's research lab, open and empty (the owner's call): FireRed's Cinnabar Lab
           experiment room, its exit mat back to the lab's door (42, 30).

Each room is drawn cell by cell from FireRed's metatiles (frlg.Pair), so every cell looks
as FireRed draws it, then packed from its pixels into a secondary of its own on Emerald's
gTileset_Building primary (FireRed's pairs have a 640-tile primary and 32-bit attributes;
Emerald's maps do not): every 8x8 tile its exact 5-bit colours in palette banks 6-12 (one
exact fit), each tile kept once (any flip), each cell's layer type FireRed's. Bottom-layer
pixels are all opaque, so the primary's BG3 fill never shows.

Behaviour: the exit mats keep MB_SOUTH_ARROW_WARP; every other cell is MB_NORMAL (FireRed's
statue signposts, the Gym's teleport pads and the lab's machines need scripts or warps the
rooms do not have yet; their numbers mean other things in Emerald). Collision and elevation
are FireRed's, cell by cell; the cells the Gym's statues stand on are solid.

Writes gba/art/saffron-kanto/source/interiors/{dojo,lab}.npz, events.json and
evidence/interiors/{dojo,lab}.png.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import frlg                                     # noqa: E402
import pack as P                                # noqa: E402  (the city's exact bank fit)
B = P.B

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/saffron-kanto'
OUT, EV = ART / 'source/interiors', ART / 'evidence/interiors'
BANKS = list(range(6, 13))                      # a secondary's palette banks
TILE_LIMIT = 512
METATILE_LIMIT = 512

# --------------------------------------------------------------------------- rooms
# A room is a grid of cells: (source, metatile, collision, elevation). Sources are FireRed
# layouts on their own pairs.
SOURCES = dict(D=('SaffronCity_Dojo_Frlg', 'pewter_gym_frlg'), G=('SaffronCity_Gym_Frlg', 'saffron_gym_frlg'),
               L=('CinnabarIsland_PokemonLab_ExperimentRoom_Frlg', 'lab_frlg'))

def sources(engine):
    out = {}
    for k, (name, sec) in SOURCES.items():
        grid, _ = frlg.layout(engine, name)
        out[k] = (frlg.Pair(engine, 'building_frlg', sec), grid)
    return out

def cell(src, k, x, y):
    v = int(src[k][1][y, x])
    return (k, v & 0x3FF, (v >> 10) & 3, v >> 12)

def dojo(src):
    """The hall, 25x16: one Dojo, FireRed's Fighting Dojo (SaffronCity_Dojo) built out to
    twice its width. One wall runs the length of it, its pillars every four cells (FireRed's
    two, then three more), its window and scroll bays repeated; one tatami arena, FireRed's
    mat drawn seventeen cells long between the second and sixth pillars, shared by both
    schools. The west end is FireRed's Dojo floor as it is, its two statues and its exit mat
    (back to the Fighting door); the east end repeats it with Sabrina's Gym in it: the Gym's
    two Pokemon statues on the Dojo's wood (overlays), its pink diamond rug laid on the
    arena's east half, and the second exit mat (back to the Psychic door)."""
    W, H = 25, 16
    D = lambda x, y: cell(src, 'D', x, y)
    black = D(0, 0)
    g = [[black] * W for _ in range(H)]
    wall = [None, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 4, 9, 10, 11, 4, 5, 6, 7, 8, 9, 10, 11]
    for x in range(1, W - 1):
        sx = wall[x]
        for y in range(1, 7):
            g[y][x] = D(sx, y)
        mat = 4 if x == 4 else 8 if x == 20 else 6 if 4 < x < 20 else (wall[x] if x < 4 else 9 + (x - 21))
        for y in range(7, 12):
            g[y][x] = D(mat, y)
        low = x if x < 12 else 2 if x == 12 else max(2, x - 12)
        for y in range(12, 15):
            g[y][x] = D(low, y)
    for x0 in (5, 17):                          # the exit mats' door frames
        for i in range(3):
            g[15][x0 + i] = D(5 + i, 15)
    for x in (15, 21):                          # the east statues: plain floor under the Gym's
        for y in (12, 13, 14):
            g[y][x] = D(2, y)
        g[14][x + 1] = D(2, 14)
    overlays = [dict(src='G', cells=(12, 10, 17, 12), floor=[(12, 13, 17, 15), (10, 10, 11, 11), (17, 10, 18, 11)], at=(14 * 16, 8 * 16 + 8)),
                dict(src='G', cells=(12, 19, 13, 21), floor=[(12, 13, 17, 15), (13, 19, 14, 21)], at=(15 * 16, 12 * 16)),
                dict(src='G', cells=(12, 19, 13, 21), floor=[(12, 13, 17, 15), (13, 19, 14, 21)], at=(21 * 16, 12 * 16))]
    return dict(cells=g, overlays=overlays, blocked=[(15, 12), (15, 13), (21, 12), (21, 13)])

def lab(src):
    """FireRed's experiment room as it is, 15x11."""
    h, w = src['L'][1].shape
    return dict(cells=[[cell(src, 'L', x, y) for x in range(w)] for y in range(h)], overlays=[], blocked=[])

ROOMS = dict(dojo=dojo, lab=lab)
EXITS = dict(dojo=[((6, 14), 'MAP_KANTO_SAFFRON_CITY', 'dojo_fighting'), ((18, 14), 'MAP_KANTO_SAFFRON_CITY', 'dojo_psychic')],
             lab=[((7, 9), 'MAP_KANTO_SAFFRON_CITY', 'lab')])

def piece(src, k, x0, y0, x1, y1):
    """FireRed's picture of a block of a source's cells (x1, y1 exclusive), both layers flat."""
    pair, grid = src[k]
    b, t = frlg.render(pair, grid[y0:y1, x0:x1])
    return frlg.flat(b, t)

def overlay(src, bot, o):
    """Paste a source block's own pixels (those not in its floor's colours) onto a room."""
    px = piece(src, o['src'], *o['cells'])
    floor = {tuple(c) for r in o['floor'] for c in piece(src, o['src'], *r).reshape(-1, 3).tolist()}
    keep = ~np.array([[tuple(c) in floor for c in row] for row in px.tolist()])
    X, Y = o['at']
    bot[Y:Y + px.shape[0], X:X + px.shape[1]][keep] = px[keep]

# --------------------------------------------------------------------------- pixels
def draw(src, room):
    H, W = len(room), len(room[0])
    bot = np.zeros((H * 16, W * 16, 3), np.uint8)
    top = np.zeros((H * 16, W * 16, 4), np.uint8)
    info = []
    for y in range(H):
        row = []
        for x in range(W):
            k, mid, coll, elev = room[y][x]
            pair = src[k][0]
            b, t = pair.cell(mid)
            bot[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = b
            top[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = t
            row.append(dict(src=k, metatile=mid, collision=coll, elevation=elev, layer=pair.layer_type(mid),
                            frlg_behavior=pair.behavior(mid)))
        info.append(row)
    return bot, top, info

def pack(bot, top, info, behaviors):
    """One exact Emerald-format secondary for a room: tiles, banks 6-12, metatiles."""
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
    packed, assign, lost = P.exact_banks(order, len(BANKS))
    assert not lost, ('a tile fits no bank', len(lost))
    pals = [(c or [(0, 0, 0)]) + [(c or [(0, 0, 0)])[-1]] * (15 - len(c or [(0, 0, 0)])) for c in packed]
    err = 0
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
            mb = behaviors['MB_SOUTH_ARROW_WARP'] if c['frlg_behavior'] == behaviors['MB_SOUTH_ARROW_WARP'] else behaviors['MB_NORMAL']
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
                elevation=np.array([[c['elevation'] for c in r] for r in info], np.uint8)), err

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
    src = sources(engine)
    MB = B.behaviors(engine)
    OUT.mkdir(parents=True, exist_ok=True)
    EV.mkdir(parents=True, exist_ok=True)
    report = {}
    for name, build in ROOMS.items():
        room = build(src)
        bot, top, info = draw(src, room['cells'])
        for o in room['overlays']:
            overlay(src, bot, o)
        for x, y in room['blocked']:
            info[y][x]['collision'] = 1
        p, err = pack(bot, top, info, MB)
        want = frlg.flat(bot, top)
        got = decode(p)
        d5 = np.abs(B.rgb5(got) - B.rgb5(want)).max(-1)
        assert d5.max() == 0, (name, 'packed room differs from its picture', int((d5 > 0).sum()))
        np.savez_compressed(OUT / f'{name}.npz', **p)
        big = Image.fromarray(got).resize((got.shape[1] * 2, got.shape[0] * 2), Image.Resampling.NEAREST)
        big.save(EV / f'{name}.png')
        h, w = p['grid'].shape
        report[name] = dict(size=[w, h], tiles=len(p['tiles']), metatiles=len(p['meta']), bank_error=err,
                            pixels_exact=True, exits=[dict(x=x, y=y, dest=dest, door=door) for (x, y), dest, door in EXITS[name]],
                            walkable=int(((p['collision'] == 0)).sum()))
        for (x, y), _, _ in EXITS[name]:
            assert p['behaviour'][y, x] == MB['MB_SOUTH_ARROW_WARP'] and p['collision'][y, x] == 0, (name, 'exit mat', x, y)
        print(name, report[name])
    (OUT / 'events.json').write_text(json.dumps(report, indent=1) + '\n')

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
