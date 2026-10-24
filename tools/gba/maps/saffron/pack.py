"""Pack the edited Saffron into one Emerald-format tileset pair.

    python3 tools/gba/maps/saffron/pack.py ENGINE_CHECKOUT

FireRed's Saffron uses 488 of its tileset pair's tiles and 10 of its 13 palette banks
(0-3, 5, 8-12). Here they become one Emerald-format pair (512-tile primary with banks 0-5,
secondary from tile 512 with banks 6-12, 16-bit attributes), so the map lives in the same
Porymap project as the Johto towns, beside them in the Emerald build:

  - every cell left as FireRed drew it keeps its metatile: its tile entries remapped to the
    new pair, its palette banks the same numbers (FireRed's bank 6 and 7 slots are free in
    Saffron), its behaviour and layer type as they were; these fill the primary
  - the art cells (the station, the Psychic Dojo's plate) are packed from their pixels:
    each 8x8 tile reuses a FireRed tile wherever one draws the same, the rest are new;
    the station's colours take bank 4, and a bottom tile behind it whose colours no
    FireRed bank holds goes to banks 6 and 7, all exact. Their metatiles are the
    secondary's; the station's draw below the player (covered), the plate's keep
    FireRed's layer type
  - FireRed's tile 0x14 keeps slot 0x14: the engine fills BG3 under normal-layer
    metatiles with that slot, and FireRed's roof corners show it (frlg.under)
  - FireRed's animated flowers in General_Frlg are drawn static (Emerald's engine plays
    no General_Frlg animation)

Traversal is FireRed's grid, with Apocrypha's doors: the Center and the Mart open (their
interiors are cloned from Cherrygrove's, install.py), every other door and gate solid
until its interior or route exists, the station blocked across its footprint.
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
FRLG_BANKS = [0, 1, 2, 3, 5, 8, 9, 10, 11, 12]
STATION_BANK = 4
SPARE = [6, 7]
PRIMARY_TILES, SECONDARY_TILES = 512, 496       # 16 secondary slots kept for door animation
NORMAL, COVERED = 0, 1
CLEAR = -1
# Doors with interiors (install.py clones Cherrygrove's Center, its upstairs and its Mart).
OPEN_DOORS = {(24, 38): 'pokemon_center', (40, 21): 'poke_mart'}
MB = dict(normal=0x00, door=0x69, sign=0x1D)
WARP_BEHAVIOURS = {0x60, 0x62, 0x63, 0x64, 0x65, 0x69}

def exact_banks(jobs, nbanks, size=15, tries=4000, init=None):
    """Olivine's exact palette packing (olivine_elements/pack.py): maximal colour sets,
    largest first, the packing that leaves the fewest tile uses unplaced."""
    sets = [frozenset(map(tuple, j['px'][j['mask'] > 0].astype(int).tolist())) for j in jobs]
    distinct = sorted(set(sets), key=lambda c: sorted(c))
    maximal = [c for c in distinct if not any(c < d for d in distinct)]
    rng = np.random.default_rng(0)
    best = None
    for t in range(tries):
        order = sorted(maximal, key=lambda c: (-len(c) * (1 + (rng.random() * 0.8 if t else 0)), sorted(c)))
        banks = [set(init[k]) if init else set() for k in range(nbanks)]
        rule = t % 3
        for c in order:
            fits = [((len(c - b), -len(c & b)) if rule == 0 else (-len(c & b), len(c - b)) if rule == 1 else (len(c - b), len(b)))
                    + (k,) for k, b in enumerate(banks) if len(b | c) <= size]
            if fits:
                banks[min(fits)[-1]] |= c
        lost = sum(j['weight'] for j, c in zip(jobs, sets) if not any(c <= b for b in banks))
        if best is None or lost < best[0]:
            best = (lost, [set(b) for b in banks])
        if not lost:
            break
    banks = best[1]
    assign = [next((k for k, b in enumerate(banks) if c <= b), None) for c in sets]
    return [sorted(b) for b in banks], assign, best[0]

def key5(px, mask=None):
    k = B.rgb5(px).astype(np.int16)
    if mask is not None:
        k[~mask] = CLEAR
    return k.tobytes()

def frlg_index(pair, pals):
    """rgb5 content -> (FireRed tile, bank, flip) for every tile under every bank Saffron uses."""
    opaque, masked = {}, {}
    for t, ix in enumerate(pair.tiles):
        for b in FRLG_BANKS:
            p = np.array(pals[b], np.int32)
            for f, v in enumerate(B.flips(ix)):
                m = v != 0
                masked.setdefault(key5(p[v], m), (t, b, f))
                if m.all():
                    opaque.setdefault(key5(p[v]), (t, b, f))
    return opaque, masked

def traversal(pair, g, art, station):
    out = {}
    for y in range(H):
        for x in range(W):
            v = int(g[y, x]); mid = v & 0x3FF
            beh, coll, elev = pair.behavior(mid), (v >> 10) & 3, (v >> 12) & 15
            c = dict(x=x, y=y, frlg_behavior=beh, frlg_collision=coll)
            if (x, y) in OPEN_DOORS:
                c.update(behavior=MB['door'], collision=0, elevation=3, door=OPEN_DOORS[(x, y)])
            elif station[y, x]:
                c.update(behavior=MB['normal'], collision=1, elevation=0)
                if (x, y) == C.STATION_DOOR:
                    c['adaptation'] = 'Magnet Train station door: solid until the station interior is built'
            elif beh in WARP_BEHAVIOURS:
                c.update(behavior=MB['normal'], collision=1, elevation=elev,
                         adaptation='door or gate warp: solid until its interior or route is built')
            else:
                c.update(behavior=beh, collision=coll, elevation=elev)
            out[(x, y)] = c
    return out

def main(engine):
    z = np.load(SRC / 'compose.npz')
    g, art, station, bottom, top = z['edited'], z['art'], z['station_cells'], z['bottom'], z['top']
    pair = frlg.Pair(engine, C.PRIMARY, C.SECONDARY)
    pals = {b: [tuple(int(v) for v in c) for c in z['pals'][b]] for b in range(13)}
    opaque_idx, masked_idx = frlg_index(pair, pals)
    trav = traversal(pair, g, art, station)

    # 1. FireRed metatiles kept as they are, and the tiles they use
    used_tiles = set()
    kept_meta = set(int(v) & 0x3FF for v in z['border'].ravel())
    for y in range(H):
        for x in range(W):
            if not art[y, x]:
                kept_meta.add(int(g[y, x]) & 0x3FF)
    for m in kept_meta:
        used_tiles |= {e & 1023 for e in pair.meta[m]}

    # 2. the art cells, per 8x8 tile
    lay, jobs = {}, {}
    for y in range(H):
        for x in range(W):
            if not art[y, x]:
                continue
            for q in range(4):
                tx, ty = x * 2 + q % 2, y * 2 + q // 2
                sl = np.s_[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
                tp = top[sl][..., 3] > 0
                for layer, px, mask in ((0, bottom[sl], np.ones((8, 8), bool)), (1, top[sl][..., :3], tp)):
                    if layer == 1 and not tp.any():
                        lay[(tx, ty, 1)] = ('empty',)
                        continue
                    if layer == 0 and tp.all() and station[y, x]:
                        lay[(tx, ty, 0)] = ('hidden',)
                        continue
                    k = key5(px, None if layer == 0 else mask)
                    hit = (opaque_idx if layer == 0 else masked_idx).get(k)
                    if hit:
                        lay[(tx, ty, layer)] = ('frlg',) + hit
                        used_tiles.add(hit[0])
                        continue
                    cols = {tuple(int(v) for v in c) for c in B.rgb5(px)[mask]}
                    is_station = layer == 1 and station[y, x]
                    fixed = STATION_BANK if is_station else next((b for b in FRLG_BANKS
                                                                  if cols <= {tuple(v >> 3 for v in c) for c in pals[b][1:]}), None)
                    jk = (k, layer, fixed)
                    j = jobs.setdefault(jk, dict(px=B.rgb5(px).reshape(64, 3), mask=mask.ravel().astype(np.uint8), weight=0,
                                                 bank=fixed, layer=layer, station=is_station))
                    j['weight'] += 1
                    lay[(tx, ty, layer)] = ('job', jk)
    # station colours (its sprite's 15) fill bank 4; the rest of the new tiles fit banks 6, 7
    sprite = np.array(Image.open(SRC / 'sprites/station.png').convert('RGBA'))
    station_cols = sorted({tuple(int(v) >> 3 for v in c) for c in sprite[sprite[..., 3] > 0][:, :3].tolist()})
    assert len(station_cols) <= 15, len(station_cols)
    banks = {b: [tuple(v >> 3 for v in c) for c in pals[b][1:16]] for b in FRLG_BANKS}
    banks[STATION_BANK] = station_cols + [station_cols[-1]] * (15 - len(station_cols))
    free = [j for j in jobs.values() if j['bank'] is None]
    lost = 0
    if free:
        packed, assign, lost = exact_banks(free, len(SPARE))
        for j, a in zip(free, assign):
            j['bank'] = SPARE[a] if a is not None else SPARE[0]
        for b, cols in zip(SPARE, packed):
            cols = cols or [(0, 0, 0)]
            banks[b] = cols + [cols[-1]] * (15 - len(cols))
    for b in SPARE:
        banks.setdefault(b, [(0, 0, 0)] * 15)
    # quantize the new tiles in their banks and share patterns across flips
    patterns = {}
    for j in jobs.values():
        pal = np.array(banks[j['bank']], float)
        ix = (((j['px'][:, None, :].astype(float) - pal[None]) ** 2 * B.CH_W).sum(-1).argmin(-1) + 1).astype(np.uint8)
        if j['layer'] == 1:
            ix = np.where(j['mask'] > 0, ix, 0).astype(np.uint8)
        vs = B.flips(ix.reshape(8, 8))
        o = min(range(4), key=lambda i: vs[i].tobytes())
        kk = vs[o].tobytes()
        patterns.setdefault(kk, len(patterns))
        j['pattern'], j['flip'] = patterns[kk], o

    # 3. tile slots: tile 0 blank, FireRed's kept tiles (its tile 0x14 at slot 0x14: the
    # engine fills BG3 under normal-layer metatiles with that slot, frlg.under), then the
    # new patterns
    assert not pair.tiles[0].any(), 'FireRed tile 0 is not blank'
    rest = sorted(used_tiles - {0, frlg.FILL_TILE})
    order = [0] + rest[:frlg.FILL_TILE - 1] + [frlg.FILL_TILE] + rest[frlg.FILL_TILE - 1:]
    assert order[frlg.FILL_TILE] == frlg.FILL_TILE
    slot_of = {t: i for i, t in enumerate(order)}
    new_slot = {p: len(order) + i for i, p in enumerate(sorted(patterns.values()))}
    total = len(order) + len(patterns)
    assert total <= PRIMARY_TILES + SECONDARY_TILES, ('tiles over budget', total)
    all_tiles = [pair.tiles[t] for t in order] + [np.frombuffer(kk, np.uint8).reshape(8, 8)
                                                  for kk, _ in sorted(patterns.items(), key=lambda kv: kv[1])]
    prim_tiles = all_tiles[:PRIMARY_TILES] + [np.zeros((8, 8), np.uint8)] * max(0, PRIMARY_TILES - len(all_tiles))
    sec_tiles = all_tiles[PRIMARY_TILES:]

    def remap(e):
        return slot_of[e & 1023] | (e & 0xFC00)

    def entry(L):
        if L[0] in ('empty', 'hidden'):
            return 0
        if L[0] == 'frlg':
            t, b, f = L[1:]
            return slot_of[t] | ((f & 1) << 10) | ((f >> 1) << 11) | (b << 12)
        j = jobs[L[1]]
        return new_slot[j['pattern']] | ((j['flip'] & 1) << 10) | ((j['flip'] >> 1) << 11) | (j['bank'] << 12)

    # 4. metatiles: each cell's (entries, attribute), shared where equal. FireRed's kept
    # metatiles fill the primary (ids 0-511); the art cells' (the station, the plate) are
    # the secondary's, from id 512.
    keys = {}
    for y in range(H):
        for x in range(W):
            c = trav[(x, y)]
            v = int(g[y, x])
            if art[y, x]:
                q = [(2 * x, 2 * y), (2 * x + 1, 2 * y), (2 * x, 2 * y + 1), (2 * x + 1, 2 * y + 1)]
                ents = [entry(lay[(a, b, 0)]) for a, b in q] + [entry(lay[(a, b, 1)]) for a, b in q]
                layer = COVERED if station[y, x] else pair.layer_type(v & 0x3FF)   # the plate keeps FireRed's
            else:
                m = v & 0x3FF
                ents = [remap(e) for e in pair.meta[m]]
                layer = pair.layer_type(m)
            c['layer'] = 'covered' if layer == COVERED else 'normal'
            keys[(x, y)] = (tuple(ents), c['behavior'] | (layer << 12))
    border_keys = [(tuple(remap(e) for e in pair.meta[int(v) & 0x3FF]),
                    pair.behavior(int(v) & 0x3FF) | (pair.layer_type(int(v) & 0x3FF) << 12)) for v in z['border'].ravel()]
    cells = [(x, y) for y in range(H) for x in range(W)]
    prim_keys = list(dict.fromkeys([keys[p] for p in cells if not art[p[1], p[0]]] + border_keys))
    sec_keys = [k for k in dict.fromkeys(keys[p] for p in cells if art[p[1], p[0]]) if k not in set(prim_keys)]
    assert len(prim_keys) <= 512 and len(sec_keys) <= 512, (len(prim_keys), len(sec_keys))
    metas = {k: i for i, k in enumerate(prim_keys)}
    metas.update({k: 512 + i for i, k in enumerate(sec_keys)})
    grid = np.zeros((H, W), np.uint16)
    for x, y in cells:
        c = trav[(x, y)]
        grid[y, x] = metas[keys[(x, y)]] | (c['collision'] << 10) | (c['elevation'] << 12)
    border = np.array([metas[k] for k in border_keys], np.uint16)
    prim_meta = prim_keys + [((0,) * 8, 0)] * (512 - len(prim_keys))
    sec_meta = sec_keys

    # 5. palettes and the decode
    pal_rgb = np.zeros((16, 16, 3), np.uint8)
    for b in range(13):
        if b in FRLG_BANKS:
            pal_rgb[b] = np.array(pals[b], np.uint8)
        else:
            pal_rgb[b, 1:] = [[(v << 3) | (v >> 2) for v in c] for c in banks[b][:15]]
    tile_at = lambda t: prim_tiles[t] if t < PRIMARY_TILES else sec_tiles[t - PRIMARY_TILES]
    allmeta = {i: k for k, i in metas.items()}
    native = np.zeros((H * 16, W * 16, 3), np.uint8)
    for y in range(H):
        for x in range(W):
            ents, attr = allmeta[int(grid[y, x]) & 0x3FF]
            fill = frlg.under(tile_at(frlg.FILL_TILE), attr >> 12, pal_rgb)
            for li, e in enumerate(ents):
                ix = tile_at(e & 1023)
                if e & 0x400: ix = ix[:, ::-1]
                if e & 0x800: ix = ix[::-1]
                qi = li % 4
                oy, ox = y * 16 + (qi // 2) * 8, x * 16 + (qi % 2) * 8
                if li < 4:
                    native[oy:oy + 8, ox:ox + 8] = np.where((ix == 0)[..., None], fill, pal_rgb[e >> 12][ix])
                else:
                    m = ix > 0
                    native[oy:oy + 8, ox:ox + 8][m] = pal_rgb[e >> 12][ix[m]]
    want = frlg.flat(bottom, top)
    d5 = np.abs(B.rgb5(native) - B.rgb5(want)).max(-1)
    hidden = np.zeros((H * 16, W * 16), bool)
    for (tx, ty, l), L in lay.items():
        if L[0] == 'hidden':
            hidden[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8] = True
    EV.mkdir(parents=True, exist_ok=True)
    Image.fromarray(native).save(EV / 'native.png')
    np.savez_compressed(SRC / 'pack.npz', grid=grid, border=border, prim_tiles=np.array(prim_tiles, np.uint8),
                        sec_tiles=np.array(sec_tiles, np.uint8).reshape(-1, 8, 8), palettes=pal_rgb,
                        prim_meta=np.array([list(k[0]) + [k[1]] for k in prim_meta], np.uint16),
                        sec_meta=np.array([list(k[0]) + [k[1]] for k in sec_meta], np.uint16).reshape(-1, 9))
    (SRC / 'traversal.json').write_text(json.dumps([trav[(x, y)] for y in range(H) for x in range(W)]) + '\n')
    report = dict(frlg_tiles_kept=len(order), new_tiles=len(patterns), primary_tiles=min(PRIMARY_TILES, total),
                  secondary_tiles=max(0, total - PRIMARY_TILES), secondary_tile_limit=SECONDARY_TILES,
                  metatiles=len(metas), metatiles_in_primary=len(prim_keys), metatiles_in_secondary=len(sec_meta),
                  frlg_metatiles_kept=len(kept_meta),
                  art_cells=int(art.sum()), unplaced_tile_uses=int(lost),
                  colour_rgb5=dict(exact=int((d5[~hidden] == 0).sum()), total=int((~hidden).sum()), worst=int(d5[~hidden].max())),
                  banks=dict(frlg=FRLG_BANKS, station=STATION_BANK, spare=SPARE),
                  adaptations={f"{c['x']},{c['y']}": c['adaptation'] for c in trav.values() if 'adaptation' in c})
    (EV / 'pack.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'adaptations'}), len(report['adaptations']), 'adapted cells')

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
