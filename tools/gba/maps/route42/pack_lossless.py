"""Route 42: single-map lossless pack helpers (Route 43's pack_lossless.py). pack_fixed.py, which
packs Route 42 onto Mahogany Town's tilesets, uses its traversal, family, pack_sets and
milp_sets; this main packs Route 42 alone on a tileset pair of its own (to measure it), into
source/pack-alone and evidence/pack-alone, and is not part of the install.

    python3 tools/gba/maps/route42/pack_lossless.py ENGINE_CHECKOUT PHG_CHECKOUT

Every visible native pixel keeps its assembled colour in RGB555: palette banks are packed from
exact colour sets, tiles are deduplicated only when identical under a flip, and the one
compaction is a bottom tile hidden under fully opaque top-layer art. Traversal comes from the
decoded HGSS permissions (pack.traversal): woods, cliffs, the Mt. Mortar mouths, the gate's doorway and
the Rock Climb wall blocked, tall grass, water (Surf), crown overhang the Gen 3 roots leave bare opened.
"""
from __future__ import annotations
import hashlib, json, sys
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build as B                                   # noqa: E402
import elements as E                                # noqa: E402
import pack as P                                    # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route-42'
SRC, EV = ART / 'source', ART / 'evidence'
OUT_SRC, OUT_EV = SRC / 'pack-alone', EV / 'pack-alone'
W, H = 96, 32
BANKS = 13
PRIMARY_TILES, SECONDARY_TILES = 512, 496
def traversal(engine, phg, top, owner):
    cells = E.ledger(phg)
    shared = np.zeros_like(top)
    art, edge = P.object_art(top, shared, owner)
    return P.traversal(engine, cells, art, edge), shared

def family(name):
    for k, f in (('tree', 'tree'), ('house', 'red roofs'), ('tower', 'red roofs'), ('gym', 'gym'), ('antenna', 'antenna'),
                 ('gate', 'gate'), ('pokemon', 'center'), ('sign', 'sign')):
        if name.startswith(k):
            return f
    return 'ground'

def pack_sets(sets, nbanks, init=(), size=15, tries=200, seed=0):
    """Exact colour banks for a collection of tile colour sets: every set must lie inside one
    bank of at most `size` colours. Only maximal sets matter. Fixed banks (init) absorb what
    they already hold; each new bank is seeded with the largest unplaced set and grown with
    the set that adds the fewest new colours (ties: the larger set), until nothing fits.
    Randomised restarts keep the packing with the fewest banks. Returns banks or None."""
    distinct = set(sets)
    maximal = [c for c in distinct if not any(c < d for d in distinct)]
    rng = np.random.default_rng(seed)
    best = None
    for t in range(tries):
        banks = [set(b) for b in init]
        todo = sorted(maximal, key=lambda c: -len(c) - (rng.random() * 3 if t else 0))
        # fixed banks first: anything they hold or can take
        changed = True
        while changed and todo and banks:
            changed = False
            for c in list(todo):
                fits = [(len(c - b), -len(c & b), k) for k, b in enumerate(banks) if len(b | c) <= size]
                if fits and min(fits)[0] == 0:
                    todo.remove(c); changed = True
        for k, b in enumerate(banks):
            while True:
                fits = [(len(c - b), -len(c), i) for i, c in enumerate(todo) if len(b | c) <= size]
                if not fits:
                    break
                _, _, i = min(fits)
                b |= todo.pop(i)
        while todo:
            if len(banks) >= nbanks:
                break
            b = set(todo.pop(0))
            while True:
                fits = [(len(c - b), -len(c), i) for i, c in enumerate(todo) if len(b | c) <= size]
                if not fits:
                    break
                _, _, i = min(fits)
                b |= todo.pop(i)
            banks.append(b)
        if not todo and (best is None or len(banks) < len(best)):
            best = banks
    return best

def milp_sets(sets, nbanks, size=15, time_limit=300, fixed=(), force=()):
    """Exact bank assignment as an integer program (scipy / HiGHS): x[s,b] puts maximal set s in
    bank b, y[c,b] puts colour c in bank b; every set in one bank, its colours in that bank,
    at most `size` colours per bank. fixed pins a few sets to banks to break symmetry."""
    from scipy.optimize import milp, LinearConstraint, Bounds
    from scipy.sparse import lil_matrix
    cols = sorted(set().union(*sets)); ci = {c: i for i, c in enumerate(cols)}
    S, C, Bn = len(sets), len(cols), nbanks
    nx = S * Bn
    X = lambda s, b: s * Bn + b
    Y = lambda c, b: nx + c * Bn + b
    nv = nx + C * Bn
    rows = S + sum(len(x) for x in sets) * Bn + Bn
    A = lil_matrix((rows, nv)); lo = np.zeros(rows); hi = np.zeros(rows); r = 0
    for si in range(S):
        for b in range(Bn): A[r, X(si, b)] = 1
        lo[r] = hi[r] = 1; r += 1
    for si, st in enumerate(sets):
        for c in st:
            for b in range(Bn):
                A[r, X(si, b)] = 1; A[r, Y(ci[c], b)] = -1; lo[r] = -np.inf; hi[r] = 0; r += 1
    for b in range(Bn):
        for c in range(C): A[r, Y(c, b)] = 1
        lo[r] = 0; hi[r] = size; r += 1
    lb = np.zeros(nv); ub = np.ones(nv)
    for c, b in force:                                  # colours pinned to a bank (a family's own bank)
        lb[Y(ci[c], b)] = 1
    for si, b in fixed:
        for bb in range(Bn):
            if bb != b: ub[X(si, bb)] = 0
    res = milp(c=np.zeros(nv), constraints=LinearConstraint(A.tocsr(), lo, hi), integrality=np.ones(nv),
               bounds=Bounds(lb, ub), options=dict(time_limit=time_limit, disp=False))
    print('milp', res.status, res.message)
    if res.x is None or res.status not in (0,):
        return None
    xv = res.x[nx:].reshape(C, Bn) > 0.5
    banks = [set() for _ in range(Bn)]
    for si, st in enumerate(sets):
        b = int(np.argmax([res.x[X(si, bb)] for bb in range(Bn)]))
        banks[b] |= st
    return banks

def plan_banks(jl):
    """Exact banks, planned by family. Each family's own tiles are packed exactly into the
    fewest banks that hold them; the tiles where two families overlap (a crown behind a tower,
    the antenna tree against a house) then go into the slots and banks left over, with the
    family banks as fixed starting content."""
    setof = lambda j: frozenset(map(tuple, j['px'][j['mask'] > 0].tolist()))
    single = {}
    for i, j in enumerate(jl):
        if len(j['families']) == 1:
            single.setdefault(next(iter(j['families'])), []).append(i)
    init, plan = [], {}
    for f in sorted(single, key=lambda f: -len(set().union(*(setof(jl[i]) for i in single[f])))):
        banks = pack_sets([setof(jl[i]) for i in single[f]], BANKS)
        assert banks is not None, ('family does not fit', f)
        plan[f] = list(range(len(init), len(init) + len(banks)))
        init += banks
    assert len(init) <= BANKS, ('families need more banks than the hardware has', {f: len(b) for f, b in plan.items()})
    banks = pack_sets([setof(j) for j in jl], BANKS, init=init)
    if banks is None:
        allsets = list({setof(j) for j in jl})
        maximal = [c for c in allsets if not any(c < d for d in allsets)]
        key = hashlib.sha256(repr(sorted(sorted(c) for c in maximal)).encode()).hexdigest()
        cache = OUT_SRC / 'banks-cache.json'
        if cache.exists() and json.loads(cache.read_text()).get('key') == key:
            banks = [set(map(tuple, b)) for b in json.loads(cache.read_text())['banks']]
        if banks is None:
            # Exact solve. The large families keep the banks they packed into (their colours
            # are pinned there, which also removes bank-order symmetry); every set, the small
            # families' and the overlap tiles', is then placed by the integer program.
            keep = [f for f in plan if f not in ('junction',) and len(plan[f]) == 1]
            force, nb = [], 0
            for f in keep:
                for k in plan[f]:
                    force += [(c, nb) for c in init[k]]
                    nb += 1
            colours = set().union(*maximal)
            force = [(c, b) for c, b in force if c in colours]
            # the free banks are interchangeable: pin a clique of sets that pairwise cannot
            # share a bank (and fit none of the pinned ones) to distinct free banks
            pinned = [set(init[k]) for f in keep for k in plan[f]]
            cand = sorted((i for i, c in enumerate(maximal) if not any(len(c | b) <= 15 for b in pinned)),
                          key=lambda i: -len(maximal[i]))
            fixed = []
            for i in cand:
                if nb + len(fixed) >= BANKS:
                    break
                if all(len(maximal[i] | maximal[j]) > 15 for j, _ in fixed):
                    fixed.append((i, nb + len(fixed)))
            banks = milp_sets(maximal, BANKS, force=force, fixed=fixed, time_limit=900)
            if banks is not None:
                cache.write_text(json.dumps(dict(key=key, banks=[sorted(b) for b in banks])) + '\n')
    if banks is None:
        mixed = Counter(tuple(sorted(j['families'])) for j in jl
                        if not any(setof(j) <= b for b in init))
        print('not inside a family bank:', dict(mixed))
    assert banks is not None, ('overlap tiles do not fit the remaining banks', {f: len(b) for f, b in plan.items()})
    pals = []
    for b in banks + [set() for _ in range(BANKS - len(banks))]:
        cols = sorted(b) or [(0, 0, 0)]
        pals.append(cols + [cols[-1]] * (15 - len(cols)))
    assign = []
    for j in jl:
        c = setof(j)
        assign.append(next(k for k, p in enumerate(pals) if c <= set(p)))
    return pals, np.array(assign), plan

def main(engine, phg):
    OUT_SRC.mkdir(parents=True, exist_ok=True); OUT_EV.mkdir(parents=True, exist_ok=True)
    z = np.load(SRC / 'assemble/layers.npz')
    ground, rock, top, owner = z['ground'], z['rock'], z['objects'], z['owner'].astype(object)
    terrain = ground.copy()
    rk_all = rock[..., 3] > 0
    terrain[rk_all] = rock[rk_all, :3]
    trav, shared = traversal(engine, phg, top, owner)
    walkable = np.array([[trav[y * W + x]['foot'] in ('open', 'door') for x in range(W)] for y in range(H)])
    above = P.above_player(walkable, top, shared, owner)
    for c in trav:
        c['layer'] = 'normal' if above[c['y'], c['x']] else 'covered'

    # Layer plan per 8x8 tile. Objects take the top layer over the terrain. Where no object is,
    # a tile part rock and part ground puts the rock on the top layer, transparent, over pure
    # ground (its cell draws both layers under the player, so nothing changes on screen); in a
    # cell that draws its top layer above the player the rock stays composited in the bottom.
    common = Counter(ground[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].tobytes() for ty in range(H * 2) for tx in range(W * 2)).most_common(1)[0][0]
    filler = np.frombuffer(common, np.uint8).reshape(8, 8, 3)
    fam = np.vectorize(family)(owner)
    lay, hidden, split, split_obj = {}, 0, 0, 0
    base = np.zeros(owner.shape, np.int32)                      # each object pixel's base row: who stands in front
    for name in set(owner.ravel().tolist()) - {''}:
        mm = owner == name
        base[mm] = int(np.nonzero(mm.any(1))[0].max())
    sys.path.insert(0, str(HERE.parent))
    from claude_cherrygrove import ground as G
    tex = G.textures()
    yy, xx = np.mgrid[0:H * 16, 0:W * 16]
    grass_plain = tex[G.GRASS][yy % tex[G.GRASS].shape[0], xx % tex[G.GRASS].shape[1]].astype(np.uint8)
    path_plain = tex[G.PATH][yy % tex[G.PATH].shape[0], xx % tex[G.PATH].shape[1]].astype(np.uint8)

    def backing(b, vis, sl, fams):
        """A bottom tile partly hidden under opaque top-layer art: only its visible pixels
        count. If they match the pure ground or pure rock tile here, use that tile; otherwise
        hidden pixels take a colour the tile already shows, so no hidden colour costs a slot."""
        for plain in (grass_plain, path_plain):
            if (plain[sl][vis] == b[vis]).all():
                return plain[sl].copy(), {'ground'}
        if (ground[sl][vis] == b[vis]).all():
            return ground[sl].copy(), {'ground'}
        if rk_all[sl].all() and (rock[sl][..., :3][vis] == b[vis]).all():
            return rock[sl][..., :3].copy(), {'rock'}
        v = b[vis].reshape(-1, 3)
        cols, cnt = np.unique(v, axis=0, return_counts=True)
        b[~vis] = cols[cnt.argmax()]
        vr = rk_all[sl] & vis
        out = set(f for f in fams if f not in ('rock', 'ground', 'junction'))
        if vr.any(): out.add('rock')
        if (vis & ~rk_all[sl]).any() and (b[vis & ~rk_all[sl]] != 0).any(): out.add('ground')
        return b, out or {'ground'}

    for ty in range(H * 2):
        for tx in range(W * 2):
            sl = np.s_[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            ob = top[sl][..., 3] > 0
            rk = rk_all[sl]
            fs = set(fam[sl][ob].ravel().tolist())
            if len(fs) > 1 and not above[ty // 2, tx // 2]:
                # Two objects overlap in a cell drawn under the player: the one behind joins
                # the bottom layer over the terrain, the one in front keeps the top layer.
                front = fam[sl][ob].ravel()[np.argmax(base[sl][ob].ravel())]
                fm = ob & (fam[sl] == front)
                bm = ob & ~fm
                b = terrain[sl].copy(); b[bm] = top[sl][bm, :3]
                hide = bool(fm.all())
                hidden += hide
                rest = rk & ~bm
                bfam = set(fam[sl][bm].ravel().tolist()) | ({'rock'} if rest.all() and not (~bm & ~rk).any() else set())
                if (~bm & ~rk).any(): bfam |= {'ground'}
                if rest.any(): bfam |= {'rock'}
                split_obj += 1
                if not hide:
                    b, bfam = backing(b, ~fm, sl, bfam)
                lay[(tx, ty, 0)] = dict(px=filler if hide else b, mask=np.ones((8, 8), bool), fam={'ground'} if hide else bfam)
                lay[(tx, ty, 1)] = dict(px=top[sl][..., :3], mask=fm, fam={front})
            elif ob.any():
                hide = bool(ob.all())
                hidden += hide
                bfam = 'rock' if rk.all() else 'junction' if rk.any() else 'ground'
                b = terrain[sl]
                if not hide:
                    b, fset = backing(b.copy(), ~ob, sl, {bfam})
                    bfam = next(iter(fset)) if len(fset) == 1 else 'junction'
                lay[(tx, ty, 0)] = dict(px=filler if hide else b, mask=np.ones((8, 8), bool), fam={'ground' if hide else bfam})
                lay[(tx, ty, 1)] = dict(px=top[sl][..., :3], mask=ob, fam=fs)
            elif rk.all():
                lay[(tx, ty, 0)] = dict(px=rock[sl][..., :3], mask=np.ones((8, 8), bool), fam={'rock'})
            elif rk.any() and not above[ty // 2, tx // 2]:
                split += 1
                b, _ = backing(ground[sl].copy(), ~rk, sl, {'ground'})
                lay[(tx, ty, 0)] = dict(px=b, mask=np.ones((8, 8), bool), fam={'ground'})
                lay[(tx, ty, 1)] = dict(px=rock[sl][..., :3], mask=rk, fam={'rock'})
            else:
                lay[(tx, ty, 0)] = dict(px=terrain[sl], mask=np.ones((8, 8), bool), fam={'junction' if rk.any() else 'ground'})
    jobs = {}
    for pos, L in lay.items():
        k = (P.key5(L['px'], None if pos[2] == 0 else L['mask']), pos[2])
        j = jobs.setdefault(k, dict(px=B.rgb5(L['px']).reshape(64, 3), mask=L['mask'].ravel().astype(np.uint8), weight=0, layer=pos[2],
                                    families=set()))
        j['weight'] += 1
        j['families'] |= L['fam']
        L['job'] = k
    jl = list(jobs.values())
    ncol = [len({tuple(c) for c in j['px'][j['mask'] > 0].tolist()}) for j in jl]
    over15 = sum(n > 15 for n in ncol)
    assert not over15, f'{over15} tiles hold more than 15 colours'
    pals, assign, plan = plan_banks(jl)
    sets = [frozenset(map(tuple, j['px'][j['mask'] > 0].tolist())) for j in jl]
    lost = [j for j, s, a in zip(jl, sets, assign) if not s <= set(map(tuple, pals[a]))]
    if lost:
        print('unplaced', Counter(tuple(sorted(j['families'])) for j in lost), 'plan', plan)
    assert not lost, f'{len(lost)} tiles fit no exact bank'
    banks = {b: [tuple(int(v) for v in c) for c in p] for b, p in enumerate(pals)}
    for j, a in zip(jl, assign):
        j['bank'] = int(a)
        pal = np.array(banks[j['bank']], int)
        d = np.abs(j['px'][:, None, :] - pal[None]).sum(-1)
        ix = (d.argmin(-1) + 1).astype(np.uint8)
        assert (d.min(-1)[j['mask'] > 0] == 0).all()
        if j['layer'] == 1:
            ix = np.where(j['mask'] > 0, ix, 0).astype(np.uint8)
        j['ix'] = ix.reshape(8, 8)
    patterns = {np.zeros((8, 8), np.uint8).tobytes(): 0}
    for j in jl:
        vs = B.flips(j['ix'])
        o = min(range(4), key=lambda i: vs[i].tobytes())
        kk = vs[o].tobytes()
        if kk not in patterns:
            patterns[kk] = len(patterns)
        j['pattern'], j['flip'] = patterns[kk], o
    n = len(patterns)
    if n > PRIMARY_TILES + SECONDARY_TILES:
        byfam = {}
        for j in jl:
            byfam.setdefault('+'.join(sorted(j['families'])) + f"/L{j['layer']}", set()).add(j['pattern'])
        print('tiles by family', sorted(((k, len(v)) for k, v in byfam.items()), key=lambda kv: -kv[1]))
    assert n <= PRIMARY_TILES + SECONDARY_TILES, ('tiles over budget', n)

    def entry(L):
        if L is None:
            return 0
        j = jobs[L['job']]
        return j['pattern'] | ((j['flip'] & 1) << 10) | ((j['flip'] >> 1) << 11) | (j['bank'] << 12)
    metas, grid = {}, np.zeros((H, W), np.uint16)
    for y in range(H):
        for x in range(W):
            q = [(2 * x, 2 * y), (2 * x + 1, 2 * y), (2 * x, 2 * y + 1), (2 * x + 1, 2 * y + 1)]
            bot = [entry(lay[(a, b, 0)]) for a, b in q]
            tp = [entry(lay.get((a, b, 1))) for a, b in q]
            c = trav[y * W + x]
            attr = c['behavior_id'] | ((0 if c['layer'] == 'normal' else 1) << 12)
            k = (tuple(bot + tp), attr)
            metas.setdefault(k, len(metas))
            grid[y, x] = metas[k]
    order = sorted(metas, key=lambda k: (any((e & 1023) >= PRIMARY_TILES for e in k[0]), metas[k]))
    n_prim = sum(1 for k in order if not any((e & 1023) >= PRIMARY_TILES for e in k[0]))
    assert n_prim <= 512 and len(order) - n_prim <= 512, ('metatiles over budget', n_prim, len(order) - n_prim)
    ids = {k: (i if i < n_prim else 512 + i - n_prim) for i, k in enumerate(order)}
    inv = {i: k for k, i in metas.items()}
    grid = np.array([[ids[inv[int(grid[y, x])]] for x in range(W)] for y in range(H)], np.uint16)
    meta_by_id = {i: k for k, i in ids.items()}
    pat = np.zeros((n, 8, 8), np.uint8)
    for kk, i in patterns.items():
        pat[i] = np.frombuffer(kk, np.uint8).reshape(8, 8)
    pal_rgb = np.zeros((16, 16, 3), np.uint8)
    for b, p in banks.items():
        for i, c in enumerate(p[:15]):
            pal_rgb[b, i + 1] = [(v << 3) | (v >> 2) for v in c]
    # Decode the native result and prove every visible pixel kept its colour.
    native = np.zeros((H * 16, W * 16, 3), np.uint8)
    for y in range(H):
        for x in range(W):
            ents, _ = meta_by_id[int(grid[y, x])]
            for li, e in enumerate(ents):
                ix = pat[e & 1023]
                if e & 0x400: ix = ix[:, ::-1]
                if e & 0x800: ix = ix[::-1]
                qi = li % 4
                oy, ox = y * 16 + (qi // 2) * 8, x * 16 + (qi % 2) * 8
                m = ix > 0 if li >= 4 else np.ones((8, 8), bool)
                native[oy:oy + 8, ox:ox + 8][m] = pal_rgb[e >> 12][ix[m]]
    want = terrain.copy()
    a = top[..., 3] > 0
    want[a] = top[a, :3]
    d5 = np.abs(B.rgb5(native) - B.rgb5(want)).max(-1)
    assert d5.max() == 0, ('native pixels differ from the assembled art', int((d5 > 0).sum()))
    Image.fromarray(native).save(OUT_EV / 'native.png')
    np.savez_compressed(OUT_SRC / 'pack.npz', grid=grid, patterns=pat, palettes=pal_rgb,
                        metatiles=np.array([[i] + list(k[0]) + [k[1]] for i, k in sorted(meta_by_id.items())], np.uint16).reshape(-1, 10),
                        collision=np.array([[trav[y * W + x]['collision'] for x in range(W)] for y in range(H)], np.uint8),
                        elevation=np.array([[trav[y * W + x]['elevation'] for x in range(W)] for y in range(H)], np.uint8))
    (OUT_SRC / 'traversal.json').write_text(json.dumps(trav) + '\n')
    report = dict(method='lossless: exact RGB555 banks, flip dedupe, hidden-backing compaction only',
                  tiles=n, tile_limit=PRIMARY_TILES + SECONDARY_TILES, primary_tiles=min(n, PRIMARY_TILES),
                  secondary_tiles=max(0, n - PRIMARY_TILES), metatiles=len(metas), primary_metatiles=n_prim,
                  secondary_metatiles=len(metas) - n_prim, distinct_tile_jobs=len(jobs), hidden_backing_tiles=hidden, rock_on_top_layer_tiles=split, overlap_tiles_split_across_layers=split_obj,
                  family_banks=plan, banks_used=sum(1 for p in pals if len(set(p)) > 1), colours_per_bank=[len(set(p)) for p in pals],
                  native_pixels_exact=int((d5 == 0).sum()), native_pixels=int(d5.size),
                  adaptations={f"{c['x']},{c['y']}": c['adaptation'] for c in trav if 'adaptation' in c})
    (OUT_EV / 'pack.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'adaptations'}))
    return report

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
