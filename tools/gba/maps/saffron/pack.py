"""Pack the rebuilt Saffron into one Emerald-format tileset pair.

    python3 tools/gba/maps/saffron/pack.py ENGINE_CHECKOUT

FireRed's Saffron becomes one Emerald-format pair (512-tile primary with banks 0-5,
secondary from tile 512 with banks 6-12, 16-bit attributes), so the map lives in the same
Porymap project as the Johto towns, beside them in the Emerald build:

  - every cell is packed from its pixels, both layers as FireRed (or, in an art cell, the
    placed part) draws them: each 8x8 tile kept once (any flip), every colour exact in one
    fit over all thirteen banks (Saffron draws 117 colours; FireRed's own banks hold many
    twice). A bottom layer is opaque everywhere, so where FireRed showed BG3's fill tile
    through a colour-0 pixel the fill's own colour is drawn
  - every cell keeps FireRed's layer type and behaviour; an art cell takes the rule below
  - FireRed's animated flowers in General_Frlg are drawn static

Traversal is FireRed's grid, with Apocrypha's doors: the Center and the Mart (interiors
cloned from Cherrygrove's), the Dojo's two entrances and the lab's open; every other door
and gate solid until its interior or route exists. A building blocks every cell it covers
half or more of; a street lamp its foot cell. A part's cell the player can walk draws the
part above the player when the part stands further south (walking behind it), below
otherwise; a blocked cell or a door draws it below.
Writes source/pack.npz, source/traversal.json, evidence/pack.json and evidence/native.png.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(HERE), str(HERE.parent / 'olivine_elements')]
import frlg                                     # noqa: E402
import compose as C                             # noqa: E402
import build as B                               # noqa: E402  (rgb5, flips, tile_error, behaviours)

ART = ROOT / 'gba/art/saffron-kanto'
SRC, EV = ART / 'source', ART / 'evidence'
W, H = C.W, C.H
BANKS = list(range(13))
PRIMARY_TILES, SECONDARY_TILES = 512, 496       # 16 secondary slots kept for door animation
NORMAL, COVERED = 0, 1
CLEAR = -1
# Doors with interiors (install.py clones Cherrygrove's Center, its upstairs and its Mart;
# interiors.py builds the Dojo's hall and the lab).
OPEN_DOORS = {(24, 38): 'pokemon_center', (40, 21): 'poke_mart', C.DOORS['dojo_fighting']: 'dojo_fighting',
              C.DOORS['dojo_psychic']: 'dojo_psychic', C.DOORS['lab']: 'lab'}
SOLID_DOORS = {C.DOORS['silph']: "Silph Co.'s lobby", C.DOORS['station']: 'the Magnet Train station'}
BLOCK_COVER = 0.5
MB = dict(normal=0x00, door=0x69, sign=0x1D)
WARP_BEHAVIOURS = {0x60, 0x62, 0x63, 0x64, 0x65, 0x69}

def exact_banks(jobs, nbanks, size=15, steps=3_000_000, seeds=8):
    """Every tile its exact 5-bit colours in one of nbanks banks of size colours. Only the
    maximal colour sets matter (every other tile's set lies inside one of them). Each is
    given a bank at random, then an annealed search moves sets between banks until every
    bank holds size colours or fewer; a stuck run restarts from another seed. Returns the
    banks, each job's bank and the tile uses left unplaced (0 when it succeeds)."""
    sets = [frozenset(map(tuple, j['px'][j['mask'] > 0].astype(int).tolist())) for j in jobs]
    distinct = sorted(set(sets), key=lambda c: (-len(c), sorted(c)))
    maximal = [c for c in distinct if not any(c < d for d in distinct)]
    colour_ids = {c: i for i, c in enumerate(sorted(set().union(*maximal)))}
    ms = [np.array([colour_ids[c] for c in m]) for m in maximal]
    for seed in range(seeds):
        rng = np.random.default_rng(seed)
        count = np.zeros((nbanks, len(colour_ids)), np.int32)
        where = rng.integers(nbanks, size=len(ms))
        for i, m in enumerate(ms):
            count[where[i], m] += 1
        nz = (count > 0).sum(1)
        over = lambda b: max(0, int(nz[b]) - size)
        cost, T = sum(over(b) for b in range(nbanks)), 3.0
        for step in range(steps):
            if cost == 0:
                break
            i = int(rng.integers(len(ms)))
            a, b = int(where[i]), int(rng.integers(nbanks))
            if a == b:
                continue
            m = ms[i]
            before = over(a) + over(b)
            da, db = int((count[a, m] == 1).sum()), int((count[b, m] == 0).sum())
            nz[a] -= da; nz[b] += db
            delta = over(a) + over(b) - before
            if delta <= 0 or rng.random() < np.exp(-delta / T):
                count[a, m] -= 1; count[b, m] += 1; where[i] = b; cost += delta
            else:
                nz[a] += da; nz[b] -= db
            T = max(0.02, T * 0.999998)
        if cost == 0:
            break
    rev = {i: c for c, i in colour_ids.items()}
    banks = [sorted(rev[i] for i in np.nonzero(count[b])[0]) for b in range(nbanks)]
    bank_sets = [set(bk) for bk in banks]
    assign = [next((k for k, bk in enumerate(bank_sets) if c <= bk and len(bk) <= size), None) for c in sets]
    lost = sum(j['weight'] for j, a in zip(jobs, assign) if a is None)
    return banks, assign, lost

DOOR_CELL = (24, 38)                            # the Center's door; the Mart's draws the same metatile

def door_frame_colours(engine):
    """The 5-bit colours of FireRed's sliding-door frames, per door tile (TL, TR, BL, BR)."""
    im = Image.open(engine / 'graphics/door_anims/sliding_single.png')
    ix, rgb = np.array(im), np.array(im.getpalette()[:48]).reshape(16, 3) >> 3
    out = [set() for _ in range(4)]
    for f in range(ix.shape[0] // 16):
        for q in range(4):
            t = ix[f * 16 + (q // 2) * 8:f * 16 + (q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            out[q] |= {tuple(int(v) for v in rgb[i]) for i in np.unique(t) if i}
    return out

def key5(px, mask=None):
    k = B.rgb5(px).astype(np.int16)
    if mask is not None:
        k[~mask] = CLEAR
    return k.tobytes()

def traversal(pair, g, art, owner, cover, feet):
    """Each cell's behaviour, collision and elevation. A building blocks the cells it covers
    by half or more, except its back rows (from the top row its pixels reach; one, or
    compose.BACK_ROWS): there the roof stands in front of the street behind it, so the cell
    keeps its ground's collision and, the building's foot being south of it, draws above the
    player, who walks behind."""
    back = {o: int(min(np.nonzero(owner == o)[0])) for o in C.BUILDINGS if (owner == o).any()}
    out = {}
    for y in range(H):
        for x in range(W):
            v = int(g[y, x]); mid = v & 0x3FF
            beh, coll, elev = pair.behavior(mid), (v >> 10) & 3, (v >> 12) & 15
            c = dict(x=x, y=y, frlg_behavior=beh, frlg_collision=coll)
            o = str(owner[y, x])
            if o:
                c['part'] = o
            if (x, y) in OPEN_DOORS:
                c.update(behavior=MB['door'], collision=0, elevation=3, door=OPEN_DOORS[(x, y)])
            elif (x, y) in SOLID_DOORS:
                c.update(behavior=MB['normal'], collision=1, elevation=3,
                         adaptation=f'{SOLID_DOORS[(x, y)]} door: solid until its interior is built')
            elif o and (o in C.BUILDINGS and cover[y, x] >= BLOCK_COVER and y - back[o] >= C.BACK_ROWS.get(o, 1) or o.startswith('lamp') and y == feet[o]):
                c.update(behavior=MB['normal'], collision=1, elevation=3)
                if not coll:
                    c['adaptation'] = f'{o} stands here'
            elif beh in WARP_BEHAVIOURS:
                c.update(behavior=MB['normal'], collision=1, elevation=elev,
                         adaptation='door or gate warp: solid until its interior or route is built')
            elif o:
                c.update(behavior=MB['normal'], collision=coll, elevation=elev if elev else 3)
            else:
                c.update(behavior=beh, collision=coll, elevation=elev)
            out[(x, y)] = c
    return out

def main(engine):
    z = np.load(SRC / 'compose.npz')
    g, art, owner, cover, bottom, top = z['edited'], z['art'], z['owner'], z['cover'], z['bottom'], z['top']
    feet = dict(zip(z['feet_names'].tolist(), z['feet_rows'].tolist()))
    pair = frlg.Pair(engine, C.PRIMARY, C.SECONDARY)
    trav = traversal(pair, g, art, owner, cover, feet)

    # the border block's cells are packed with the map's
    bh, bw = z['border'].shape
    bb, bt = z['border_bottom'], z['border_top']
    cells = [('map', x, y) for y in range(H) for x in range(W)] + [('border', x, y) for y in range(bh) for x in range(bw)]
    def layers(kind, x, y):
        b, t = (bottom, top) if kind == 'map' else (bb, bt)
        sl = np.s_[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
        return b[sl], t[sl]

    # 1. every 8x8 tile of both layers
    lay, jobs = {}, {}
    for cell in cells:
        kind, x, y = cell
        b16, t16 = layers(*cell)
        blocked = kind == 'map' and art[y, x] and trav[(x, y)]['collision']
        for q in range(4):
            sl = np.s_[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            tp = t16[sl][..., 3] > 0
            for layer, px, mask in ((0, b16[sl], np.ones((8, 8), bool)), (1, t16[sl][..., :3], tp)):
                if layer == 1 and not tp.any():
                    lay[(cell, q, 1)] = None
                    continue
                if layer == 0 and tp.all() and blocked:
                    lay[(cell, q, 0)] = 'hidden'
                    continue
                k = (key5(px, None if layer == 0 else mask), layer)
                j = jobs.setdefault(k, dict(px=B.rgb5(px).reshape(64, 3), mask=mask.ravel().astype(np.uint8), weight=0, layer=layer))
                j['weight'] += 1
                lay[(cell, q, layer)] = k
    order = list(jobs.values())
    # The Center's and Mart's door plays FireRed's sliding door in its own tiles' banks
    # (install.move_door): each door tile's bank must also hold that tile's frame colours.
    door = [jobs[lay[(('map',) + DOOR_CELL, q, 0)]] for q in range(4)]
    frames = door_frame_colours(engine)
    ghosts = [dict(px=np.array(sorted(set(map(tuple, j['px'].astype(int).tolist())) | frames[q])), weight=0, layer=0)
              for q, j in enumerate(door)]
    for gh in ghosts:
        gh['mask'] = np.ones(len(gh['px']), np.uint8)
    packed, assign, lost = exact_banks(order + ghosts, len(BANKS))
    assert not lost, ('tiles whose colours fit no bank', lost)
    for q, j in enumerate(door):
        assign[next(i for i, o in enumerate(order) if o is j)] = assign[len(order) + q]
    assign = assign[:len(order)]
    banks = {}
    for b, cols in zip(BANKS, packed):
        cols = cols or [(0, 0, 0)]
        banks[b] = cols + [cols[-1]] * (15 - len(cols))
    patterns = {}
    for j, a in zip(order, assign):
        j['bank'] = BANKS[a]
        pal = np.array(banks[j['bank']], float)
        ix = (((j['px'][:, None, :].astype(float) - pal[None]) ** 2 * B.CH_W).sum(-1).argmin(-1) + 1).astype(np.uint8)
        if j['layer'] == 1:
            ix = np.where(j['mask'] > 0, ix, 0).astype(np.uint8)
        vs = B.flips(ix.reshape(8, 8))
        o = min(range(4), key=lambda i: vs[i].tobytes())
        kk = vs[o].tobytes()
        patterns.setdefault(kk, len(patterns) + 1)            # slot 0 stays blank
        j['pattern'], j['flip'] = patterns[kk], o
    total = len(patterns) + 1
    assert total <= PRIMARY_TILES + SECONDARY_TILES, ('tiles over budget', total)
    all_tiles = [np.zeros((8, 8), np.uint8)] + [np.frombuffer(kk, np.uint8).reshape(8, 8)
                                                for kk, _ in sorted(patterns.items(), key=lambda kv: kv[1])]
    prim_tiles = all_tiles[:PRIMARY_TILES] + [np.zeros((8, 8), np.uint8)] * max(0, PRIMARY_TILES - len(all_tiles))
    sec_tiles = all_tiles[PRIMARY_TILES:]

    def entry(L):
        if L in (None, 'hidden'):
            return 0
        j = jobs[L]
        return j['pattern'] | ((j['flip'] & 1) << 10) | ((j['flip'] >> 1) << 11) | (j['bank'] << 12)

    # 2. metatiles: each cell's (entries, attribute), shared where equal; the cells FireRed
    # drew as they were (and the border) the primary's, the art cells' the secondary's
    keys = {}
    for cell in cells:
        kind, x, y = cell
        ents = [entry(lay[(cell, q, 0)]) for q in range(4)] + [entry(lay[(cell, q, 1)]) for q in range(4)]
        if kind == 'border':
            m = int(z['border'][y, x]) & 0x3FF
            keys[cell] = (tuple(ents), pair.behavior(m) | (pair.layer_type(m) << 12))
            continue
        c = trav[(x, y)]
        if art[y, x]:
            o = str(owner[y, x])
            layer = NORMAL if not c['collision'] and 'door' not in c and feet[o] > y else COVERED
        else:
            layer = pair.layer_type(int(g[y, x]) & 0x3FF)
        c['layer'] = {0: 'normal', 1: 'covered', 2: 'split'}[layer]
        keys[cell] = (tuple(ents), c['behavior'] | (layer << 12))
    plain = list(dict.fromkeys(keys[c] for c in cells if c[0] == 'border' or not art[c[2], c[1]]))
    parts = [k for k in dict.fromkeys(keys[c] for c in cells if c[0] == 'map' and art[c[2], c[1]]) if k not in set(plain)]
    assert len(plain) <= 512 and len(parts) <= 512, ('metatiles over budget', len(plain), len(parts))
    metas = {k: i for i, k in enumerate(plain)}
    metas.update({k: 512 + i for i, k in enumerate(parts)})
    uniq = {i: k for k, i in metas.items()}
    prim_meta = plain + [((0,) * 8, 0)] * (512 - len(plain))
    sec_meta = parts
    grid = np.zeros((H, W), np.uint16)
    for x in range(W):
        for y in range(H):
            c = trav[(x, y)]
            grid[y, x] = metas[keys[('map', x, y)]] | (c['collision'] << 10) | (c['elevation'] << 12)
    border = np.array([[metas[keys[('border', x, y)]] for x in range(bw)] for y in range(bh)], np.uint16)

    # 3. palettes and the decode
    pal_rgb = np.zeros((16, 16, 3), np.uint8)
    for b in BANKS:
        pal_rgb[b, 1:] = [[(v << 3) | (v >> 2) for v in c] for c in banks[b][:15]]
    tile_at = lambda t: all_tiles[t] if t < len(all_tiles) else np.zeros((8, 8), np.uint8)
    native = np.zeros((H * 16, W * 16, 3), np.uint8)
    for y in range(H):
        for x in range(W):
            ents, attr = uniq[int(grid[y, x]) & 0x3FF]
            for li, e in enumerate(ents):
                ix = tile_at(e & 1023)
                if e & 0x400: ix = ix[:, ::-1]
                if e & 0x800: ix = ix[::-1]
                qi = li % 4
                oy, ox = y * 16 + (qi // 2) * 8, x * 16 + (qi % 2) * 8
                m = ix > 0 if li >= 4 else np.ones((8, 8), bool)
                native[oy:oy + 8, ox:ox + 8][m] = pal_rgb[e >> 12][ix[m]]
    want = frlg.flat(bottom, top)
    d5 = np.abs(B.rgb5(native) - B.rgb5(want)).max(-1)
    hidden = np.zeros((H * 16, W * 16), bool)
    for (cell, q, l), L in lay.items():
        if L == 'hidden' and cell[0] == 'map':
            _, x, y = cell
            hidden[y * 16 + (q // 2) * 8:y * 16 + (q // 2) * 8 + 8, x * 16 + (q % 2) * 8:x * 16 + (q % 2) * 8 + 8] = True
    assert (d5[~hidden] == 0).all(), ('inexact pixels', int((d5[~hidden] > 0).sum()))
    EV.mkdir(parents=True, exist_ok=True)
    Image.fromarray(native).save(EV / 'native.png')
    np.savez_compressed(SRC / 'pack.npz', grid=grid, border=border, prim_tiles=np.array(prim_tiles, np.uint8),
                        sec_tiles=np.array(sec_tiles, np.uint8).reshape(-1, 8, 8), palettes=pal_rgb,
                        prim_meta=np.array([list(k[0]) + [k[1]] for k in prim_meta], np.uint16),
                        sec_meta=np.array([list(k[0]) + [k[1]] for k in sec_meta], np.uint16).reshape(-1, 9))
    (SRC / 'traversal.json').write_text(json.dumps([trav[(x, y)] for y in range(H) for x in range(W)]) + '\n')
    report = dict(tiles=total, primary_tiles=min(PRIMARY_TILES, total), secondary_tiles=max(0, total - PRIMARY_TILES),
                  secondary_tile_limit=SECONDARY_TILES, metatiles=len(uniq), metatiles_in_primary=len(plain),
                  metatiles_in_secondary=len(sec_meta), art_cells=int(art.sum()),
                  colours=sum(len(set(v)) for v in banks.values()),
                  colour_rgb5=dict(exact=int((d5[~hidden] == 0).sum()), total=int((~hidden).sum())),
                  adaptations={f"{c['x']},{c['y']}": c['adaptation'] for c in trav.values() if 'adaptation' in c})
    (EV / 'pack.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'adaptations'}), len(report['adaptations']), 'adapted cells')

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
