"""Mahogany Town converted from HGSS's own art (second draft, after the owner rejected the
Gen 3 element build as "done from scratch": flat textures, wrong houses, wrong rock depth).

    python3 tools/gba/maps/mahogany/convert.py ENGINE_CHECKOUT PHG_CHECKOUT

Every pixel comes from HGSS Mahogany's own map data (hgss_render.py: land_data chunk 85,
its terrain textures and its building models, 16 px per tile, heights lifted up the screen
as Gen 3 draws fronts and roofs, cliff and ledge fronts snapped to whole 8 px rows). Only
the Pokemon Center is replaced, by the owner-locked C06. Nothing is redrawn: the ground,
grass, road, cliffs, low walls, ledges, trees, houses, Gym, Route 43 gate, lookout towers,
antenna tree and signposts are HGSS's textures as HGSS lays them out.

Layers. The bottom layer is HGSS's ground as rendered (terrain, lifted fronts, contact
shadows). Buildings and signposts go on the top layer over it. Where a walkable cell holds
art lifted from something further south (a wall cap, a roof, a crown), that art goes on the
top layer too and the bottom shows the ground seen from straight above, so the player walks
behind it (pack.above_player decides each cell's layer type by the art's base row).

Colour and tiles. The C06 Center keeps its exact colours in banks 8 and 9. The rest of the
map is fitted to the other eleven banks (0-7, 10-12) by k-means per bank, every 8x8 tile
taking the bank that loses least; tiles are then deduplicated with flips. The map has its
own tileset pair, gTileset_MahoganyPrimary (512 tiles, banks 0-5) and gTileset_MahoganyTown
(496 tiles, banks 6-12, 16 slots kept for door animation).

Writes source/convert/{layers.npz,pack.npz,traversal.json}, evidence/convert/{native.png,
pack.json}.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build as B                                   # noqa: E402
import elements as E                                # noqa: E402
import pack as P                                    # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/mahogany-town'
SRC, EV = ART / 'source', ART / 'evidence'
OUT_SRC, OUT_EV = SRC / 'convert', EV / 'convert'
W = H = 32
TOWN_BANKS = [0, 1, 2, 3, 4, 5, 6, 7, 10, 11, 12]
CENTER_BANKS = [8, 9]
PRIMARY_TILES, SECONDARY_TILES = 512, 496
CENTER_ORIGIN = E.CENTER_ORIGIN                     # (20, 19): C06's door (2, 4) on HGSS's (22, 23)
LIFT = 24                                           # colour step that marks a lifted pixel over the flat ground

# HGSS placements (hgss-render.json) by model and position -> object names.
def object_names(buildings):
    names = []
    for b in buildings:
        m, (x, _, z) = b['model'], b['pos']
        n = {29: 'town_sign', 31: 'shop_sign', 33: 'gym_sign', 35: 'gate', 136: 'antenna_tree',
             138: 'gym', 16: 'gym', 40: 'pokemon_center', 15: 'pokemon_center'}.get(m)
        if m in (134, 135):
            n = 'souvenir_shop' if x < 22 else 'east_house'
        if m == 249:
            n = 'tower_west' if x < 16 else 'tower_east'
        names.append(n or f'model_{m}')
    return names

def layers(phg):
    sys.path.insert(0, str(HERE))
    import hgss_render as R
    R.SNAP = True
    r = R.render(phg)
    ground = np.array(r['ground'].convert('RGB'))
    terrain = np.array(r['terrain'].convert('RGB'))
    fg = np.array(r['fg'])
    names = object_names(r['buildings'])
    _, _, _, flat = E.topdown(phg)
    owner = np.full((H * 16, W * 16), '', object)
    o = r['fg_owner']
    for i, n in enumerate(names):
        owner[o == i] = n
    return ground, terrain, flat, fg, owner, r

def compose(phg):
    ground, terrain, flat, fg, owner, r = layers(phg)
    cells = E.ledger(phg)
    bottom = ground.copy()
    top = np.zeros((H * 16, W * 16, 4), np.uint8)
    a = fg[..., 3] > 0
    top[a] = fg[a]
    # C06 replaces HGSS's Center (hgss_render leaves the Center and its shadow out of fg/ground).
    shared = np.zeros_like(top)
    shared_src = np.zeros((H * 16, W * 16), np.uint8)
    c06 = np.array(Image.open(SRC / 'shared-art/pokemon-center.png').convert('RGBA'))
    X, Y = CENTER_ORIGIN[0] * 16, CENTER_ORIGIN[1] * 16
    sl = np.s_[Y:Y + c06.shape[0], X:X + c06.shape[1]]
    ca = c06[..., 3] > 0
    shared[sl][ca] = c06[ca]; shared_src[sl][ca] = 2; owner[sl][ca] = 'pokemon_center'
    # Lifted terrain over walkable cells goes to the top layer; the bottom shows it from above.
    lifted = np.abs(terrain.astype(int) - flat.astype(int)).max(-1) > LIFT
    art, edge = P.object_art(top, shared, owner)
    trav = P.traversal(Path(sys.argv[1]).resolve(), cells, art, edge)
    # The art is HGSS's own, so the only cells HGSS blocks for a model the map no longer draws
    # are the ones its replaced Center rose over (north of C06); every other blocked cell keeps
    # HGSS's collision.
    cx, cy = CENTER_ORIGIN
    for c in trav:
        if c.get('adaptation', '').startswith("HGSS's taller building model") and not (cx <= c['x'] < cx + 5 and c['y'] < cy + 1):
            c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3, behavior_id=0)
            del c['adaptation']
    walk = np.array([[trav[y * W + x]['foot'] in ('open', 'door') for x in range(W)] for y in range(H)])
    wpx = walk.repeat(16, 0).repeat(16, 1)
    move = wpx & lifted & ~a & (shared[..., 3] == 0)
    top[move, :3] = ground[move]; top[move, 3] = 255
    bottom[move] = flat[move]
    return bottom, top, shared, shared_src, owner, cells, trav

MARGIN = 8                                          # spare tile slots kept after merging

def canon(ix):
    vs = B.flips(ix)
    return min(v.tobytes() for v in vs)

def merge_tiles(jobs, banks, limit):
    """Share near-identical tiles until the map fits `limit`. Candidates are tile pairs in
    the same bank and layer with the same transparent pixels (any flip); the cost is the
    summed colour change, in 5-bit levels, of every use of the rarer tile. Center tiles are
    never touched. Cheapest merges go first; returns how many tiles were merged away."""
    groups = {}
    for j in jobs.values():
        if j['center']:
            continue
        groups.setdefault(canon(j['ix']), []).append(j)
    count = lambda: len({canon(j['ix']) for j in jobs.values()}) + 1
    merged = 0
    while count() > limit:
        uniq = {}
        for j in jobs.values():
            if j['center']:
                continue
            k = (canon(j['ix']), j['bank'], j['layer'])
            u = uniq.setdefault(k, dict(ix=j['ix'], bank=j['bank'], layer=j['layer'], uses=0, jobs=[]))
            u['uses'] += j['weight']; u['jobs'].append(j)
        items = list(uniq.values())
        best = None
        by = {}
        for u in items:
            by.setdefault((u['bank'], u['layer']), []).append(u)
        for (bank, layer), us in by.items():
            pal = np.array([(0, 0, 0)] + list(banks[bank]), float)
            ixs = np.stack([np.stack(B.flips(u['ix'])) for u in us])              # n,4,8,8
            col = pal[ixs]                                                       # n,4,8,8,3
            base = col[:, 0]
            for a, u in enumerate(us):
                d = np.abs(col - base[a][None, None]).max(-1)                    # n,4,8,8
                same_mask = ((ixs == 0) == (u['ix'] == 0)[None, None]).all((2, 3))
                cost = d.sum((2, 3))
                cost[~same_mask] = 1e9
                cost[a] = 1e9
                worst = d.max((2, 3)); cost[worst > 6] = 1e9
                b, f = np.unravel_index(np.argmin(cost), cost.shape)
                c = cost[b, f] * u['uses']
                if cost[b, f] < 1e9 and us[b]['uses'] >= u['uses'] and (best is None or c < best[0]):
                    best = (c, u, ixs[b, f])
        if best is None:
            break
        for j in best[1]['jobs']:
            j['ix'] = best[2].copy()
        merged += 1
    return merged

def tiles_of(img, mask=None):
    out = []
    for ty in range(H * 2):
        for tx in range(W * 2):
            sl = np.s_[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            out.append(((tx, ty), img[sl], None if mask is None else mask[sl]))
    return out

def main(engine, phg):
    OUT_SRC.mkdir(parents=True, exist_ok=True); OUT_EV.mkdir(parents=True, exist_ok=True)
    bottom, top, shared, shared_src, owner, cells, trav = compose(phg)
    walkable = np.array([[trav[y * W + x]['foot'] in ('open', 'door', 'water') for x in range(W)] for y in range(H)])
    above = P.above_player(walkable, top, shared, owner)
    for c in trav:
        c['layer'] = 'normal' if above[c['y'], c['x']] else 'covered'

    # Tile positions: bottom (opaque) and top (masked); C06 positions keep exact colours.
    from collections import Counter
    common = Counter(bottom[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].tobytes() for ty in range(H * 2) for tx in range(W * 2)).most_common(1)[0][0]
    filler = np.frombuffer(common, np.uint8).reshape(8, 8, 3)
    lay = {}
    for ty in range(H * 2):
        for tx in range(W * 2):
            sl = np.s_[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            sh = shared[sl][..., 3] > 0
            tp = top[sl][..., 3] > 0
            if sh.all() and not above[ty // 2, tx // 2]:
                lay[(tx, ty, 0)] = dict(px=shared[sl][..., :3], mask=np.ones((8, 8), bool), center=True)
                continue
            # under fully opaque top-layer art the bottom tile is never seen: reuse a plain one
            hidden = tp.all() and not sh.any()
            lay[(tx, ty, 0)] = dict(px=filler if hidden else bottom[sl], mask=np.ones((8, 8), bool), center=False)
            if sh.any():
                assert not tp.any(), ('Center over top-layer art', tx, ty)
                lay[(tx, ty, 1)] = dict(px=shared[sl][..., :3], mask=sh, center=True)
            elif tp.any():
                lay[(tx, ty, 1)] = dict(px=top[sl][..., :3], mask=tp, center=False)
    jobs = {}
    for pos, L in lay.items():
        k = P.key5(L['px'], None if pos[2] == 0 else L['mask'])
        jk = (k, pos[2], L['center'])
        j = jobs.setdefault(jk, dict(px=B.rgb5(L['px']).reshape(64, 3), mask=L['mask'].ravel().astype(np.uint8), weight=0,
                                     layer=pos[2], center=L['center'], material=np.full(64, pos[2])))
        j['weight'] += 1
        L['job'] = jk
    center = [j for j in jobs.values() if j['center']]
    town = [j for j in jobs.values() if not j['center']]
    cp, ca, cerr = P.exact_banks(center, len(CENTER_BANKS))
    assert cerr == 0, 'C06 does not split exactly over two banks'
    banks = {}
    for j, k in zip(center, ca):
        j['bank'] = CENTER_BANKS[k]
    for b, p in zip(CENTER_BANKS, cp):
        banks[b] = [tuple(int(v) for v in c) for c in p]
    tp_, ta, terr = B.best_banks(town, len(TOWN_BANKS), ('sqrt', 'log'), seeds=range(4))
    for j, k in zip(town, ta):
        j['bank'] = TOWN_BANKS[k]
    for b, p in zip(TOWN_BANKS, tp_):
        banks[b] = [tuple(int(v) for v in c) for c in p]

    for j in jobs.values():
        pal = np.array(banks[j['bank']], float)
        ix = (((j['px'][:, None, :].astype(float) - pal[None]) ** 2 * B.CH_W).sum(-1).argmin(-1) + 1).astype(np.uint8)
        if j['layer'] == 1:
            ix = np.where(j['mask'] > 0, ix, 0).astype(np.uint8)
        j['ix'] = ix.reshape(8, 8)
    merged = merge_tiles(jobs, banks, PRIMARY_TILES + SECONDARY_TILES - MARGIN)
    patterns = {np.zeros((8, 8), np.uint8).tobytes(): 0}
    for j in jobs.values():
        vs = B.flips(j['ix'])
        o = min(range(4), key=lambda i: vs[i].tobytes())
        kk = vs[o].tobytes()
        if kk not in patterns:
            patterns[kk] = len(patterns)
        j['pattern'], j['flip'] = patterns[kk], o
    n = len(patterns)
    assert n <= PRIMARY_TILES + SECONDARY_TILES, ('tiles over budget', n)
    # Pattern p is tile p (0-511 primary, then 512+ secondary).
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
    # Metatiles drawing only primary tiles go to the primary (ids 0-511); the rest, which use
    # secondary tiles (the buildings, C06), go to the secondary (512+).
    order = sorted(metas, key=lambda k: (any((e & 1023) >= PRIMARY_TILES for e in k[0]), metas[k]))
    n_prim = sum(1 for k in order if not any((e & 1023) >= PRIMARY_TILES for e in k[0]))
    assert n_prim <= 512 and len(order) - n_prim <= 512, ('metatiles over budget', n_prim, len(order) - n_prim)
    ids = {k: (i if i < n_prim else 512 + i - n_prim) for i, k in enumerate(order)}
    inv = {i: k for k, i in metas.items()}
    grid = np.array([[ids[inv[int(grid[y, x])]] for x in range(W)] for y in range(H)], np.uint16)
    metas = ids
    pat = np.zeros((n, 8, 8), np.uint8)
    for kk, i in patterns.items():
        pat[i] = np.frombuffer(kk, np.uint8).reshape(8, 8)
    pal_rgb = np.zeros((16, 16, 3), np.uint8)
    for b, p in banks.items():
        for i, c in enumerate(p[:15]):
            pal_rgb[b, i + 1] = [(v << 3) | (v >> 2) for v in c]
    meta_by_id = {i: k for k, i in metas.items()}
    meta_list = meta_by_id
    native = np.zeros((H * 16, W * 16, 3), np.uint8)
    for y in range(H):
        for x in range(W):
            ents, _ = meta_list[int(grid[y, x])]
            for li, e in enumerate(ents):
                ix = pat[e & 1023]
                if e & 0x400: ix = ix[:, ::-1]
                if e & 0x800: ix = ix[::-1]
                qi = li % 4
                oy, ox = y * 16 + (qi // 2) * 8, x * 16 + (qi % 2) * 8
                m = ix > 0 if li >= 4 else np.ones((8, 8), bool)
                native[oy:oy + 8, ox:ox + 8][m] = pal_rgb[e >> 12][ix[m]]
    want = E.preview(bottom, top, shared)
    d5 = np.abs(B.rgb5(native) - B.rgb5(want)).max(-1)
    shared_exact = bool((d5[shared[..., 3] > 0] == 0).all())
    assert shared_exact, 'C06 pixels changed'
    Image.fromarray(native).save(OUT_EV / 'native.png')
    Image.fromarray(want).save(OUT_EV / 'composed.png')
    np.savez_compressed(OUT_SRC / 'pack.npz', grid=grid, patterns=pat, palettes=pal_rgb,
                        metatiles=np.array([[i] + list(k[0]) + [k[1]] for i, k in sorted(meta_by_id.items())], np.uint16).reshape(-1, 10),
                        collision=np.array([[trav[y * W + x]['collision'] for x in range(W)] for y in range(H)], np.uint8),
                        elevation=np.array([[trav[y * W + x]['elevation'] for x in range(W)] for y in range(H)], np.uint8))
    (OUT_SRC / 'traversal.json').write_text(json.dumps(trav) + '\n')
    report = dict(tiles=n, tile_limit=PRIMARY_TILES + SECONDARY_TILES, primary_tiles=min(n, PRIMARY_TILES),
                  secondary_tiles=max(0, n - PRIMARY_TILES), metatiles=len(metas), primary_metatiles=n_prim,
                  secondary_metatiles=len(metas) - n_prim, merged_tiles=merged, distinct_tile_jobs=len(jobs),
                  town_bank_error=terr, colour_rgb5=dict(exact=int((d5 == 0).sum()), within_1=int((d5 <= 1).sum()),
                  within_2=int((d5 <= 2).sum()), within_4=int((d5 <= 4).sum()), total=int(d5.size), worst=int(d5.max())),
                  center_pixels_exact=shared_exact,
                  adaptations={f"{c['x']},{c['y']}": c['adaptation'] for c in trav if 'adaptation' in c})
    (OUT_EV / 'pack.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'adaptations'}))
    np.savez_compressed(OUT_SRC / 'layers.npz', bottom=bottom, top=top, shared=shared, shared_src=shared_src,
                        owner=owner.astype(str))
    return report

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
