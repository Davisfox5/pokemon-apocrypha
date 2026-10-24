"""Route 43 and Lake of Rage: one lossless pack with a shared primary tileset, so the two maps
can be joined by a map connection.

    python3 tools/gba/maps/lake_of_rage/pack_pair.py ENGINE_CHECKOUT PHG_CHECKOUT

HGSS joins Lake of Rage's south edge to Route 43's north edge with no gatehouse (Lake x =
Route 43 x + 32). A Gen 3 connection draws the neighbouring map's metatiles with the current
map's tilesets, so everything either map can show of the other must mean the same in both:
the seam strips (Route 43 rows 0-6, Lake rows 56-63 x 24-71, wider than the camera's reach
across the seam) use only the shared primary tileset (tiles 0-511, palettes 0-5, metatiles
0-511), as Emerald's own connected routes do with its General tileset. Each map keeps its own
secondary tileset (tiles 512-1007, palettes 6-12, metatiles 512+).

Lossless as before (pack_lossless.py): every visible native pixel keeps its assembled colour
in RGB555, palette banks are exact colour sets, tiles dedupe only under a flip, and the only
compaction is a bottom tile hidden under fully opaque top-layer art. The script fails if the
art does not fit, and proves: each map decoded with its own pair equals its assembled art;
each seam strip decoded with the other map's pair equals its own assembled art.

Reads gba/art/route-43/source/{assemble/layers.npz, pack3/traversal.json} and
gba/art/lake-of-rage/source/assemble/layers.npz; writes gba/art/lake-of-rage/source/pair/pack.npz,
traversal.json and evidence/pair/{pack.json, route43-native.png, lake-native.png, seam-*.png}.
"""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import build as B                                   # noqa: E402
import pack as P                                    # noqa: E402
import pack_lossless as PL                          # noqa: E402

ROOT = HERE.parents[3]
R43, LAKE = ROOT / 'gba/art/route-43', ROOT / 'gba/art/lake-of-rage'
OUT_SRC, OUT_EV = LAKE / 'source/pair', LAKE / 'evidence/pair'
MAPS = {'route43': (32, 64), 'lake': (96, 64)}
OFFSET = 32                                          # Lake x = Route 43 x + 32
SEAM = {'route43': (0, 0, 32, 7), 'lake': (24, 56, 72, 64)}   # x0, y0, x1, y1 in cells
PRIMARY_BANKS, BANKS = 6, 13
PRIMARY_TILES, SECONDARY_TILES, METAS = 512, 496, 512

def plan_layers(z, layer_of, W, H):
    """pack_lossless's per-8x8 layer plan, for one map: objects on the top layer over the
    terrain, part-rock tiles split onto the top layer where the cell draws under the player,
    overlapping objects split back and front, hidden bottom pixels compacted."""
    ground, rock, top, owner = z['ground'], z['rock'], z['objects'], z['owner'].astype(object)
    terrain = ground.copy()
    rk_all = rock[..., 3] > 0
    terrain[rk_all] = rock[rk_all, :3]
    above = np.array([[layer_of[(x, y)] == 'normal' for x in range(W)] for y in range(H)])
    common = Counter(ground[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].tobytes() for ty in range(H * 2) for tx in range(W * 2)).most_common(1)[0][0]
    filler = np.frombuffer(common, np.uint8).reshape(8, 8, 3)
    fam = np.vectorize(PL.family)(owner)
    lay = {}
    base = np.zeros(owner.shape, np.int32)
    for name in set(owner.ravel().tolist()) - {''}:
        mm = owner == name
        base[mm] = int(np.nonzero(mm.any(1))[0].max())
    from claude_cherrygrove import ground as G
    tex = G.textures()
    yy, xx = np.mgrid[0:H * 16, 0:W * 16]
    grass_plain = tex[G.GRASS][yy % tex[G.GRASS].shape[0], xx % tex[G.GRASS].shape[1]].astype(np.uint8)
    path_plain = tex[G.PATH][yy % tex[G.PATH].shape[0], xx % tex[G.PATH].shape[1]].astype(np.uint8)

    def backing(b, vis, sl):
        for plain in (grass_plain, path_plain):
            if (plain[sl][vis] == b[vis]).all():
                return plain[sl].copy()
        if (ground[sl][vis] == b[vis]).all():
            return ground[sl].copy()
        if rk_all[sl].all() and (rock[sl][..., :3][vis] == b[vis]).all():
            return rock[sl][..., :3].copy()
        v = b[vis].reshape(-1, 3)
        cols, cnt = np.unique(v, axis=0, return_counts=True)
        b[~vis] = cols[cnt.argmax()]
        return b

    full = np.ones((8, 8), bool)
    for ty in range(H * 2):
        for tx in range(W * 2):
            sl = np.s_[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            ob = top[sl][..., 3] > 0
            rk = rk_all[sl]
            fs = set(fam[sl][ob].ravel().tolist())
            if len(fs) > 1 and not above[ty // 2, tx // 2]:
                front = fam[sl][ob].ravel()[np.argmax(base[sl][ob].ravel())]
                fm = ob & (fam[sl] == front)
                bm = ob & ~fm
                b = terrain[sl].copy(); b[bm] = top[sl][bm, :3]
                hide = bool(fm.all())
                lay[(tx, ty, 0)] = dict(px=filler if hide else backing(b, ~fm, sl), mask=full)
                lay[(tx, ty, 1)] = dict(px=top[sl][..., :3], mask=fm)
            elif ob.any():
                hide = bool(ob.all())
                lay[(tx, ty, 0)] = dict(px=filler if hide else backing(terrain[sl].copy(), ~ob, sl), mask=full)
                lay[(tx, ty, 1)] = dict(px=top[sl][..., :3], mask=ob)
            elif rk.all():
                lay[(tx, ty, 0)] = dict(px=rock[sl][..., :3], mask=full)
            elif rk.any() and not above[ty // 2, tx // 2]:
                lay[(tx, ty, 0)] = dict(px=backing(ground[sl].copy(), ~rk, sl), mask=full)
                lay[(tx, ty, 1)] = dict(px=rock[sl][..., :3], mask=rk)
            else:
                lay[(tx, ty, 0)] = dict(px=terrain[sl], mask=full)
    want = terrain.copy()
    a = top[..., 3] > 0
    want[a] = top[a, :3]
    return lay, want

def lake_traversal(engine, phg):
    """Lake of Rage traversal (pack.traversal on its decoded permissions) and layer types."""
    z = np.load(LAKE / 'source/assemble/layers.npz')
    import elements as E
    trav, shared = PL.traversal(engine, phg, z['objects'], z['owner'].astype(object))
    W, H = MAPS['lake']
    walkable = np.array([[trav[y * W + x]['foot'] in ('open', 'door') for x in range(W)] for y in range(H)])
    above = P.above_player(walkable, z['objects'], shared, z['owner'].astype(object))
    for c in trav:
        c['layer'] = 'normal' if above[c['y'], c['x']] else 'covered'
    return trav

def in_seam(m, tx, ty):
    x0, y0, x1, y1 = SEAM[m]
    return x0 <= tx // 2 < x1 and y0 <= ty // 2 < y1

def colour_set(L):
    return frozenset(map(tuple, B.rgb5(L['px'])[L['mask']].reshape(-1, 3).tolist()))

def pack_into(sets, nbanks, label):
    distinct = list(set(sets))
    banks = PL.pack_sets(distinct, nbanks)
    if banks is None:
        maximal = [c for c in distinct if not any(c < d for d in distinct)]
        banks = PL.milp_sets(maximal, nbanks, time_limit=600)
    assert banks is not None, (label, 'colour sets do not fit', nbanks, 'banks')
    return [set(b) for b in banks]

def main(engine, phg):
    OUT_SRC.mkdir(parents=True, exist_ok=True); OUT_EV.mkdir(parents=True, exist_ok=True)
    MB = B.behaviors(engine)
    trav = {'route43': json.loads((R43 / 'source/pack3/traversal.json').read_text()), 'lake': lake_traversal(engine, phg)}
    plans, wants = {}, {}
    for m, src in (('route43', R43), ('lake', LAKE)):
        W, H = MAPS[m]
        z = np.load(src / 'source/assemble/layers.npz')
        layer_of = {(c['x'], c['y']): c['layer'] for c in trav[m]}
        plans[m], wants[m] = plan_layers(z, layer_of, W, H)
    # ---- palettes: shared banks 0-5 hold every seam tile's colours (both maps), then take
    # whatever other colour sets still fit their free slots (one decision for both maps); each
    # map's own tiles go into its banks 6-12.
    seam_sets = [colour_set(L) for m in MAPS for (tx, ty, _), L in plans[m].items() if in_seam(m, tx, ty)]
    shared = pack_into(seam_sets, PRIMARY_BANKS, 'seam')
    shared += [set() for _ in range(PRIMARY_BANKS - len(shared))]
    rest = Counter(colour_set(L) for m in MAPS for L in plans[m].values())
    for c, _ in rest.most_common():
        if any(c <= b for b in shared):
            continue
        fits = [(len(c - b), k) for k, b in enumerate(shared) if len(b | c) <= 15]
        if fits:
            shared[min(fits)[1]] |= c
    own = {}
    for m in MAPS:
        left = [colour_set(L) for L in plans[m].values() if not any(colour_set(L) <= b for b in shared)]
        own[m] = pack_into(left, BANKS - PRIMARY_BANKS, m) if left else []
    def bank_list(m):
        return shared + own[m]
    # ---- tiles: each 8x8 layer entry gets its bank and an index pattern; patterns dedupe under
    # flips across both maps.
    pals = {}
    for m in MAPS:
        pl = []
        for b in bank_list(m):
            cols = sorted(b) or [(0, 0, 0)]
            pl.append(cols + [cols[-1]] * (15 - len(cols)))
        pals[m] = pl + [pl[-1]] * (BANKS - len(pl))
    patterns, users = {np.zeros((8, 8), np.uint8).tobytes(): 0}, Counter()
    for m in MAPS:
        for pos, L in plans[m].items():
            c = colour_set(L)
            k = next(i for i, p in enumerate(pals[m]) if c <= set(p))
            pal = np.array(pals[m][k], int)
            px = B.rgb5(L['px']).reshape(64, 3).astype(int)
            d = np.abs(px[:, None, :] - pal[None]).sum(-1)
            ix = (d.argmin(-1) + 1).astype(np.uint8)
            assert (d.min(-1)[L['mask'].ravel()] == 0).all()
            if pos[2] == 1:
                ix = np.where(L['mask'].ravel(), ix, 0).astype(np.uint8)
            vs = B.flips(ix.reshape(8, 8))
            o = min(range(4), key=lambda i: vs[i].tobytes())
            kk = vs[o].tobytes()
            if kk not in patterns:
                patterns[kk] = len(patterns)
            L.update(bank=k, pattern=patterns[kk], flip=o)
            users[(patterns[kk], m)] += 1
    # Primary tiles: the seam's, then those both maps use, then the fullest map's own.
    used = {m: {L['pattern'] for L in plans[m].values()} | {0} for m in MAPS}
    seam_p = {L['pattern'] for m in MAPS for (tx, ty, _), L in plans[m].items() if in_seam(m, tx, ty)} | {0}
    prim = list(sorted(seam_p))
    assert len(prim) <= PRIMARY_TILES, ('seam tiles exceed the primary tileset', len(prim))
    both = sorted((used['route43'] & used['lake']) - set(prim))
    prim += both[:PRIMARY_TILES - len(prim)]
    while len(prim) < PRIMARY_TILES:
        need = {m: len(used[m] - set(prim)) for m in MAPS}
        m = max(need, key=need.get)
        cand = sorted(used[m] - set(prim))
        if not cand:
            break
        prim.append(cand[0])
    pset = set(prim)
    tile_id = {m: {p: i for i, p in enumerate(prim)} for m in MAPS}
    for m in MAPS:
        sec = sorted(used[m] - pset)
        assert len(sec) <= SECONDARY_TILES, (m, 'secondary tiles over budget', len(sec))
        tile_id[m].update({p: PRIMARY_TILES + i for i, p in enumerate(sec)})
    # ---- metatiles: the seam's (both maps) and the ones both maps use are primary.
    def entry(m, L):
        if L is None:
            return 0
        return tile_id[m][L['pattern']] | ((L['flip'] & 1) << 10) | ((L['flip'] >> 1) << 11) | (L['bank'] << 12)
    metakey = {}
    for m in MAPS:
        W, H = MAPS[m]
        t = {(c['x'], c['y']): c for c in trav[m]}
        for y in range(H):
            for x in range(W):
                q = [(2 * x, 2 * y), (2 * x + 1, 2 * y), (2 * x, 2 * y + 1), (2 * x + 1, 2 * y + 1)]
                ents = tuple(entry(m, plans[m][(a, b, 0)]) for a, b in q) + tuple(entry(m, plans[m].get((a, b, 1))) for a, b in q)
                c = t[(x, y)]
                attr = c['behavior_id'] | ((0 if c['layer'] == 'normal' else 1) << 12)
                metakey[(m, x, y)] = (ents, attr)
    in_seam_cell = lambda m, x, y: in_seam(m, 2 * x, 2 * y)
    seam_m = {k for (m, x, y), k in metakey.items() if in_seam_cell(m, x, y)}
    for k in seam_m:
        assert all((e & 1023) < PRIMARY_TILES and (e >> 12) < PRIMARY_BANKS for e in k[0]), ('seam metatile leaves the primary', k)
    per = {m: {k for (mm, x, y), k in metakey.items() if mm == m} for m in MAPS}
    shareable = lambda k: all((e & 1023) < PRIMARY_TILES for e in k[0])
    pmeta = sorted(seam_m)
    pmeta += sorted(k for k in (per['route43'] & per['lake']) - set(pmeta) if shareable(k))
    assert len(pmeta) <= METAS, ('primary metatiles over budget', len(pmeta))
    for m in sorted(MAPS, key=lambda m: -len(per[m])):
        extra = sorted(k for k in per[m] - set(pmeta) if shareable(k))
        over = len(per[m] - set(pmeta)) - METAS
        if over > 0:
            pmeta += extra[:min(over, METAS - len(pmeta))]
    meta_id = {m: {k: i for i, k in enumerate(pmeta)} for m in MAPS}
    for m in MAPS:
        sec = sorted(per[m] - set(pmeta))
        assert len(sec) <= METAS, (m, 'secondary metatiles over budget', len(sec))
        meta_id[m].update({k: METAS + i for i, k in enumerate(sec)})
    # ---- decode and prove.
    pat = np.zeros((len(patterns), 8, 8), np.uint8)
    for kk, i in patterns.items():
        pat[i] = np.frombuffer(kk, np.uint8).reshape(8, 8)
    def rgb_pal(m):
        out = np.zeros((16, 16, 3), np.uint8)
        for b, p in enumerate(pals[m]):
            for i, c in enumerate(p[:15]):
                out[b, i + 1] = [(v << 3) | (v >> 2) for v in c]
        return out
    tiles = {m: {tid: pat[p] for p, tid in tile_id[m].items()} for m in MAPS}
    metas = {m: {i: k for k, i in meta_id[m].items()} for m in MAPS}
    def draw(grid_ids, tm, pal_m):
        h, w = grid_ids.shape
        img = np.zeros((h * 16, w * 16, 3), np.uint8)
        pal = rgb_pal(pal_m)
        for y in range(h):
            for x in range(w):
                ents, _ = metas[tm][int(grid_ids[y, x])]               # the drawing map's metatiles, as the engine does
                for li, e in enumerate(ents):
                    ix = tiles[tm][e & 1023]
                    if e & 0x400: ix = ix[:, ::-1]
                    if e & 0x800: ix = ix[::-1]
                    qi = li % 4
                    oy, ox = y * 16 + (qi // 2) * 8, x * 16 + (qi % 2) * 8
                    msk = ix > 0 if li >= 4 else np.ones((8, 8), bool)
                    img[oy:oy + 8, ox:ox + 8][msk] = pal[e >> 12][ix[msk]]
        return img
    grids, report = {}, dict(method='lossless pair pack: shared primary (tiles 0-511, palettes 0-5, metatiles 0-511) '
                                    'for the seam strips; each map its own secondary')
    for m in MAPS:
        W, H = MAPS[m]
        g = np.array([[meta_id[m][metakey[(m, x, y)]] for x in range(W)] for y in range(H)], np.uint16)
        grids[m] = g
        native = draw(g, m, m)
        d5 = np.abs(B.rgb5(native) - B.rgb5(wants[m])).max(-1)
        assert d5.max() == 0, (m, 'native pixels differ from the assembled art', int((d5 > 0).sum()))
        Image.fromarray(native).save(OUT_EV / f'{m}-native.png')
        report[m] = dict(native_pixels_exact=int((d5 == 0).sum()), native_pixels=int(d5.size),
                         primary_tiles_used=len(used[m] & pset), secondary_tiles=len(used[m] - pset),
                         primary_metatiles_used=len(per[m] & set(pmeta)), secondary_metatiles=len(per[m] - set(pmeta)),
                         banks=[len(b) for b in bank_list(m)])
    # Each seam strip drawn with the other map's tilesets (what the engine shows across the connection).
    for m, other in (('route43', 'lake'), ('lake', 'route43')):
        x0, y0, x1, y1 = SEAM[m]
        g = grids[m][y0:y1, x0:x1]
        img = draw(g, other, other)
        want = wants[m][y0 * 16:y1 * 16, x0 * 16:x1 * 16]
        d5 = np.abs(B.rgb5(img) - B.rgb5(want)).max(-1)
        assert d5.max() == 0, (m, 'seam strip differs under the other map\'s tilesets', int((d5 > 0).sum()))
        Image.fromarray(img).save(OUT_EV / f'seam-{m}-with-{other}-tilesets.png')
        report[f'seam_{m}_with_{other}_tilesets_exact'] = True
    report.update(primary_tiles=len(prim), primary_metatiles=len(pmeta), shared_banks=[len(b) for b in shared],
                  seam=SEAM, offset=OFFSET)
    # ---- save.
    def meta_rows(m, sec_only):
        rows = []
        for i in sorted(metas[m]):
            if sec_only != (i >= METAS):
                continue
            ents, attr = metas[m][i]
            rows.append([i] + list(ents) + [attr])
        return np.array(rows, np.uint16).reshape(-1, 10)
    np.savez_compressed(
        OUT_SRC / 'pack.npz',
        primary_patterns=np.array([pat[p] for p in prim]), primary_palettes=rgb_pal('lake')[:PRIMARY_BANKS],
        primary_metatiles=meta_rows('lake', False),
        **{f'{m}_{k}': v for m in MAPS for k, v in (
            ('patterns', np.array([pat[p] for p, tid in sorted(tile_id[m].items(), key=lambda kv: kv[1]) if tid >= PRIMARY_TILES]).reshape(-1, 8, 8)),
            ('palettes', rgb_pal(m)), ('metatiles', meta_rows(m, True)), ('grid', grids[m]),
            ('collision', np.array([[c['collision'] for c in trav[m][y * MAPS[m][0]:(y + 1) * MAPS[m][0]]] for y in range(MAPS[m][1])], np.uint8)),
            ('elevation', np.array([[c['elevation'] for c in trav[m][y * MAPS[m][0]:(y + 1) * MAPS[m][0]]] for y in range(MAPS[m][1])], np.uint8)))})
    assert (meta_rows('lake', False) == meta_rows('route43', False)).all()
    (OUT_SRC / 'traversal.json').write_text(json.dumps(trav['lake']) + '\n')
    (OUT_EV / 'pack.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
