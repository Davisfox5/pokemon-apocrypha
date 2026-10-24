"""Saffron's two new interiors, from FireRed's own rooms, on Emerald-format tilesets.

    python3 tools/gba/maps/saffron/interiors.py ENGINE_CHECKOUT

    dojo   the Saffron Dojo's one hall (the owner's brief, 2026-10-24: the Fighting and
           Psychic Dojos "each with an individual entrance but a shared interior"):
           FireRed's Fighting Dojo (SaffronCity_Dojo) is its west half, wood floor, tatami,
           scrolls and statues; Sabrina's Gym (SaffronCity_Gym's rooms) its east half,
           lilac wall, blue floor, the pink rug under the wall and the statues by the door.
           One room, open between the two (a white column where the walls meet), an
           exit mat under each half: the west mat back to the Fighting door (41, 12), the
           east mat to the Psychic door (48, 12).
    lab    Silph's research lab, open and empty (the owner's call): FireRed's Cinnabar Lab
           experiment room, its exit mat back to the wing's door (37-38, 41).

Each room is drawn cell by cell from FireRed's metatiles (frlg.Pair), so every cell looks
as FireRed draws it, then packed from its pixels into a secondary of its own on Emerald's
gTileset_Building primary (FireRed's pairs have a 640-tile primary and 32-bit attributes;
Emerald's maps do not): every 8x8 tile its exact 5-bit colours in palette banks 6-12 (one
exact fit), each tile kept once (any flip), each cell's layer type FireRed's. Bottom-layer
pixels are all opaque, so the primary's BG3 fill never shows.

Behaviour: the exit mats keep MB_SOUTH_ARROW_WARP; every other cell is MB_NORMAL (FireRed's
statue signposts, the Gym's teleport pads and the lab's machines need scripts or warps the
rooms do not have yet; their numbers mean other things in Emerald). Collision and elevation
are FireRed's, cell by cell.

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
import olivine                                  # noqa: E402
import frlg                                     # noqa: E402
OP = olivine.mod('pack')
B = olivine.mod('build')

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
    """The hall, 23x16. Columns 0-11 are FireRed's Fighting Dojo as it is (its west black
    edge, then its hall); column 12 one of the Gym wall's white columns where the two walls
    meet, the Gym's blue floor below; 13-21 the Gym's room (its columns 10-18): the wall's two rows and the shadowed
    floor under them, the pink rug under the wall where Sabrina stood, blue floor, the
    teleport pads along the east wall (drawn, not warps), the two statues and the exit mat
    from its entrance room; column 22 the black east edge."""
    W, H = 23, 16
    g = [[None] * W for _ in range(H)]
    for y in range(H):
        for x in range(12):
            g[y][x] = cell(src, 'D', x, y)
        g[y][22] = cell(src, 'D', 12, y)
    black, floor = cell(src, 'D', 12, 0), cell(src, 'G', 12, 13)
    for x in range(12, 22):
        g[0][x] = black
        g[15][x] = black
        for y in range(4, 15):
            g[y][x] = floor
    g[1][12], g[2][12], g[3][12] = cell(src, 'G', 11, 16), cell(src, 'G', 11, 17), cell(src, 'G', 11, 18)
    for gx in range(10, 19):
        for gy, hy in ((16, 1), (17, 2), (18, 3)):
            g[hy][gx + 3] = cell(src, 'G', gx, gy)
    for gx in range(12, 17):                    # the rug, its top row in the wall's shadow
        for gy, hy in ((10, 3), (11, 4), (12, 5)):
            g[hy][gx + 3] = cell(src, 'G', gx, gy)
    for hy in (6, 10):                          # the pads on the east wall
        g[hy][21] = cell(src, 'G', 18, 20)
    for gx in (12, 16):                         # the statues
        g[12][gx + 3], g[13][gx + 3] = cell(src, 'G', gx, 19), cell(src, 'G', gx, 20)
    for gx in range(13, 16):                    # the exit mat and the door frame under it
        g[14][gx + 3], g[15][gx + 3] = cell(src, 'G', gx, 23), cell(src, 'G', gx, 24)
    return g

def lab(src):
    """FireRed's experiment room as it is, 15x11."""
    h, w = src['L'][1].shape
    return [[cell(src, 'L', x, y) for x in range(w)] for y in range(h)]

ROOMS = dict(dojo=dojo, lab=lab)
EXITS = dict(dojo=[((6, 14), 'MAP_KANTO_SAFFRON_CITY', 'dojo_fighting'), ((17, 14), 'MAP_KANTO_SAFFRON_CITY', 'dojo_psychic')],
             lab=[((7, 9), 'MAP_KANTO_SAFFRON_CITY', 'lab')])

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
                k = (OP.key5(px, None if layer == 0 else mask), layer)
                j = jobs.setdefault(k, dict(px=B.rgb5(px).reshape(64, 3), mask=mask.ravel().astype(np.uint8), weight=0, layer=layer))
                j['weight'] += 1
                lay[(tx, ty, layer)] = k
    order = list(jobs.values())
    pals, assign, err, unplaced = OP.exact_banks(order, len(BANKS))
    assert not unplaced, ('a tile fits no bank', len(unplaced))
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
        bot, top, info = draw(src, room)
        p, err = pack(bot, top, info, MB)
        want = frlg.flat(bot, top)
        got = decode(p)
        d5 = np.abs(B.rgb5(got) - B.rgb5(want)).max(-1)
        assert d5.max() == 0, (name, 'packed room differs from FireRed', int((d5 > 0).sum()))
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
