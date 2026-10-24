"""Pack Saffron's composed elements into one native map on its own tileset pair.

    python3 tools/gba/maps/saffron/pack.py ENGINE_CHECKOUT

Input is terrain.py's compose.npz (bottom layer, top layer, shared Center and Mart layer).
Saffron holds the Magnet Train station, Silph Co. and its lab wing, the Dojo, two
gatehouses, the Center, the Mart and some thirty apartment blocks: more tiles than one
secondary holds. So, as Olivine does (olivine_elements/pack.py), it gets a primary of its
own, gTileset_KantoSaffronPrimary, derived from CherrygrovePrimary:

  - tile 0 and every Cherrygrove tile Saffron draws (its grass and its tree) stay at their
    own indices; every other slot holds Saffron. Saffron draws no sea, so the primary
    plays no animation (callback NULL)
  - banks 0 and 3 are Cherrygrove's (grass, path and creams; the tree greens), bank 3 with
    Cherrygrove's two plain greens in two slots no Cherrygrove tile draws (Olivine's), so a
    tree drawn on the bottom layer over grass fits its own bank; the other eleven are learned
  - every Cherrygrove metatile that still draws exactly as it did keeps its id

The secondary, gTileset_KantoSaffronCity, holds up to 496 tiles (16 door-animation slots
reserved) and 512 metatiles. Palettes are one exact fit over the eleven learned banks: the
owner-locked C06 Center over two, the shared Mart one, each building family's palette a
bank whole (art.py's groups; the Dojo's Fighting and Psychic halves one each), the street's
(road, paving, kerbs, railings, hydrants) one, then every other tile fits the eleven.

Traversal is the decoded HGSS permissions in Gen 3 behaviours, with Apocrypha's doors: the
Center, the Mart, the Dojo's two entrances and the lab's open; every other HGSS warp (Silph's
lobby, the station, the houses, the gates and the city's four exits) is solid until its
interior or route exists. A cell HGSS leaves open that a Gen 3 building's wall fills (walls())
is solid. A cell HGSS blocks only because its taller building model stands
there, with nothing of the Gen 3 sprite in it or only a roof's top edge in its lower half,
is open ground (the player walks behind that edge).
Writes evidence/pack.json, native.png and source/pack.npz, traversal.json.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import olivine                                                # noqa: E402
OP = olivine.mod('pack')                                      # Olivine's packer: exact banks, Cherrygrove's primary, depth
B = olivine.mod('build')

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/saffron-kanto'
SRC, EV = ART / 'source', ART / 'evidence'
W, H = 64, 64
KEPT_BANKS = [0, 3]                                           # Cherrygrove's
LEARNED = [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12]
SECONDARY_TILES = 496
NORMAL, COVERED = 0, 1
CENTER_ORIGIN, CENTER_DOOR = (12, 46), (2, 4)                 # C06 door on HGSS's Center door (14, 50)
MART_ORIGIN, MART_DOOR = (36, 21), (2, 5)                     # shared Mart door on HGSS's Mart door (38, 26)
MART, CENTER = 1, 2
FLAT = ('manhole_',)
# Doors with interiors: the Center and Mart (cloned from Cherrygrove's), the Dojo's two
# entrances into its one hall, the lab wing's door (interiors.py).
DOORS = {(14, 50): 'pokemon_center', (38, 26): 'poke_mart', (41, 12): 'dojo_fighting', (48, 12): 'dojo_psychic',
         (37, 41): 'lab', (38, 41): 'lab'}
SOLID_WARPS = {(10, 16): 'Magnet Train station', (17, 26): "the Copycat's house", (28, 37): 'Silph Co.', (29, 37): 'Silph Co.',
               (43, 50): "Mr. Psychic's house", (20, 5): 'the north gate (Route 5)', (21, 5): 'the north gate (Route 5)',
               (57, 48): 'the east gate (Route 8)', (57, 49): 'the east gate (Route 8)',
               (20, 61): 'the south exit (Route 6)', (21, 61): 'the south exit (Route 6)',
               (0, 48): 'the west exit (Route 7)', (0, 49): 'the west exit (Route 7)'}
# Warps not entered northward: the east gate's from the west, the west and south exits.
SIDE_WARPS = {(57, 48), (57, 49), (0, 48), (0, 49), (20, 61), (21, 61)}
# Each family's own palette starts whole in a bank (art.py's groups).
BANK_GROUPS = [('station',), ('silph',), ('dojo_w',), ('dojo_e',), ('apt',), ('house',), ('gate',)]

WALL_COVER = 0.75
GROUND_LEVEL = ('', 'tree', 'street')

def walls(owner, family):
    """Cells a Gen 3 building's wall fills: WALL_COVER or more of the cell drawn by one
    building whose base row is this row or the next (a roof the player walks behind stands
    further south). HGSS leaves some such cells open where its model is narrower. The cell in
    front of a door entered northward (where a gate's steps are drawn) stays open."""
    foot, cover = {}, {}
    for y in range(H):
        for x in range(W):
            sl = np.s_[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
            o, f = owner[sl], family[sl]
            for name in set(np.unique(o[~np.isin(f, GROUND_LEVEL)]).tolist()) - {''}:
                m = o == name
                foot[name] = max(foot.get(name, 0), y * 16 + int(np.nonzero(m.any(1))[0].max()))
                cover[(x, y, name)] = m.mean()
    out = {}
    for (x, y, name), c in cover.items():
        if c >= WALL_COVER and foot[name] // 16 - y <= 1:
            out[(x, y)] = name.rstrip('_0123456789') if name[-1:].isdigit() else name
    return out

def traversal(engine, cells, art, edge, shared_src, wall):
    MB = B.behaviors(engine)
    perm = np.load(SRC / 'hgss/hgss-permissions.npz')
    types, coll = perm['types'], perm['collision']
    body = np.zeros((H, W), bool)                             # the shared buildings' wall rows are solid
    for src, (ox, oy), rows, cols in ((MART, MART_ORIGIN, 6, 7), (CENTER, CENTER_ORIGIN, 5, 5)):
        for cy in range(oy + 1, oy + rows):
            for cx in range(ox, ox + cols):
                if (shared_src[cy * 16:cy * 16 + 16, cx * 16:cx * 16 + 16] == src).any():
                    body[cy, cx] = True
    out = []
    for y in range(H):
        for x in range(W):
            t, k = int(types[y, x]), int(coll[y, x])
            cl = cells[y][x]
            lab = cl['lab']
            c = dict(x=x, y=y, hgss_type=t, hgss_collision=k, element=lab + cl['floor'][0])
            if (x, y) in DOORS:
                c.update(foot='door', behavior='MB_ANIMATED_DOOR', collision=0, elevation=3, door=DOORS[(x, y)])
                if not t & 0x60 and DOORS[(x, y)] == 'lab':
                    c['adaptation'] = "the lab wing's door (new: the wing stands on an apartment block's lot)"
            elif (x, y) in SOLID_WARPS:
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3,
                         adaptation=f'HGSS warp to {SOLID_WARPS[(x, y)]}: solid until its interior or route is built')
            elif body[y, x]:
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3)
                if not k & 0x80:
                    c['adaptation'] = "open in HGSS; inside the shared building (wider than HGSS's)"
            elif not k & 0x80 and (x, y) in wall and not ((x, y - 1) in DOORS or (x, y - 1) in SOLID_WARPS and (x, y - 1) not in SIDE_WARPS):
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3,
                         adaptation=f"open in HGSS; the Gen 3 {wall[(x, y)]}'s wall fills it (wider than HGSS's model)")
            elif k & 0x80 and lab in ('X', 'B') and cl['owner'] >= 0 and not art[y, x]:
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3,
                         adaptation="HGSS's taller building model blocks it; the Gen 3 sprite does not reach this cell")
            elif k & 0x80 and lab in ('X', 'B') and cl['owner'] >= 0 and edge[y, x]:
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3,
                         adaptation="HGSS's taller building model blocks it; only the Gen 3 roof's top edge reaches this cell, and the player walks behind it")
            elif k & 0x80:
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3)
            else:
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3)
            c['behavior_id'] = MB[c['behavior']]
            out.append(c)
    return out

def street_colours(bottom, top, family, kept_sets):
    """The ground and street furniture's colours, one bank whole: every tile layer that holds
    nothing else (no building) and does not draw in a kept Cherrygrove bank. Seeded so a
    tile with paving and a hydrant, say, finds both in one bank."""
    out = set()
    for ty in range(H * 2):
        for tx in range(W * 2):
            sl = np.s_[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            if set(np.unique(family[sl]).tolist()) - {'', 'street'}:
                continue
            a = top[sl][..., 3] > 0
            for px in (bottom[sl].reshape(-1, 3), top[sl][a][:, :3]):
                cols = {tuple(c) for c in B.rgb5(px).tolist()}
                if cols and not any(cols <= k for k in kept_sets.values()):
                    out |= cols
    return out

def tiles_by_owner(lay, jobs, owner):
    """Tiles only one building (or the ground, or a tile where two meet) draws, by kind."""
    users = {}
    for (tx, ty, layer), L in lay.items():
        if L['entry'][0] != 'job':
            continue
        o = owner[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
        names = {n.rstrip('_0123456789') if n[-1:].isdigit() else n for n in np.unique(o).tolist() if n}
        kind = 'ground' if not names else names.pop() if len(names) == 1 else 'two meet'
        users.setdefault(jobs[L['entry'][1]]['pattern'], set()).add(kind)
    out = {}
    for kinds in users.values():
        k = kinds.pop() if len(kinds) == 1 else 'shared'
        out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))

def main(engine):
    comp = np.load(SRC / 'compose.npz', allow_pickle=True)
    bottom, top, shared, shared_src, owner, family = (comp[k] for k in ('bottom', 'top', 'shared', 'shared_src', 'owner', 'family'))
    cells = json.loads((SRC / 'ledger.json').read_text())['detail']
    tiles, pals, metas, attrs = OP.cherrygrove(engine)
    opaque_idx, masked_idx = OP.primary_index(tiles, pals, KEPT_BANKS)
    OP.H, OP.W = H, W
    trav = traversal(engine, cells, *OP.object_art(top, shared, owner), shared_src, walls(owner, family))
    walkable = np.array([[trav[y * W + x]['foot'] in ('open', 'door') for x in range(W)] for y in range(H)])
    OP.FLAT = FLAT
    above = OP.above_player(walkable, top, shared, owner)

    lay = {}
    for ty in range(H * 2):
        for tx in range(W * 2):
            sl = np.s_[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            sh = shared[sl][..., 3] > 0
            src = set(shared_src[sl][sh].ravel().tolist())
            fixed = {frozenset({MART}): 'mart', frozenset({CENTER}): 'center'}.get(frozenset(src))
            assert len(src) < 2, ('Center and Mart share a tile', tx, ty)
            tp = top[sl][..., 3] > 0
            if sh.all() and not above[ty // 2, tx // 2]:
                lay[(tx, ty, 0)] = dict(px=shared[sl][..., :3], mask=np.ones((8, 8), bool), fixed=fixed)
                continue
            hidden = tp.all() and not sh.any()
            lay[(tx, ty, 0)] = dict(px=None if hidden else bottom[sl], mask=np.ones((8, 8), bool), fixed=None, hidden=hidden)
            if sh.any():
                assert not tp.any(), ('shared building over top-layer art', tx, ty)
                lay[(tx, ty, 1)] = dict(px=shared[sl][..., :3], mask=sh, fixed=fixed)
            elif tp.any():
                lay[(tx, ty, 1)] = dict(px=top[sl][..., :3], mask=tp, fixed=None)

    kept_sets = {b: {tuple(v >> 3 for v in c) for c in pals[b][1:]} for b in KEPT_BANKS}
    jobs, used = {}, set()
    stats = dict(cherrygrove=0, kept_bank=0, center=0, mart=0, learned=0, hidden=0)
    for pos, L in lay.items():
        layer = pos[2]
        if L.get('hidden'):
            L['entry'] = ('hidden',); stats['hidden'] += 1
            continue
        k = OP.key5(L['px'], None if layer == 0 else L['mask'])
        hit = (opaque_idx if layer == 0 else masked_idx).get(k)
        if hit and L['fixed'] is None:
            L['entry'] = ('cherry',) + hit; used.add(hit[0]); stats['cherrygrove'] += 1
            continue
        cols = {tuple(int(v) for v in c) for c in B.rgb5(L['px'])[L['mask']]}
        bank = None if L['fixed'] else next((b for b in KEPT_BANKS if cols <= kept_sets[b]), None)
        jk = (k, layer, bank, L['fixed'])
        j = jobs.setdefault(jk, dict(px=B.rgb5(L['px']).reshape(64, 3), mask=L['mask'].ravel().astype(np.uint8), weight=0,
                                     bank=bank, layer=layer, fixed=L['fixed']))
        j['weight'] += 1
        L['entry'] = ('job', jk)
    banks = {b: [tuple(v >> 3 for v in c) for c in pals[b][1:16]] for b in KEPT_BANKS}
    center = [j for j in jobs.values() if j['fixed'] == 'center']
    mart = [j for j in jobs.values() if j['fixed'] == 'mart']
    town = [j for j in jobs.values() if j['bank'] is None and not j['fixed']]
    stats.update(kept_bank=len(jobs) - len(center) - len(mart) - len(town), center=len(center), mart=len(mart), learned=len(town))
    init = {b: set() for b in LEARNED}
    cpals, cassign, cerr, _ = OP.exact_banks(center, 2)
    assert cerr == 0, ('C06 does not split exactly over two banks', cerr)
    cbanks = [LEARNED[-2], LEARNED[-1]]
    for j, a in zip(center, cassign):
        j['bank'] = cbanks[a]
        init[j['bank']] |= {tuple(int(v) for v in c) for c in j['px'][j['mask'] > 0]}
    mart_pal = [tuple(v >> 3 for v in c) for c in OP.read_pal(olivine.DIR.parent.parent.parent.parent /
                                                               'gba/art/olivine-elements/source/shared-art/poke-mart.pal')[1:]]
    mbank = LEARNED[-3]
    init[mbank] = set(mart_pal)
    for j in mart:
        assert {tuple(int(v) for v in c) for c in j['px'][j['mask'] > 0]} <= init[mbank], 'Mart colour outside its palette'
        j['bank'] = mbank
    free = [b for b in LEARNED if not init[b]]
    for names, b in zip(BANK_GROUPS, free):
        m = (top[..., 3] > 0) & np.isin(family, names)
        init[b] = {tuple(c) for c in B.rgb5(top[m][:, :3]).tolist()}
        assert len(init[b]) <= 15, ('palette group over one bank', names, len(init[b]))
    b = free[len(BANK_GROUPS)]
    init[b] = street_colours(bottom, top, family, kept_sets)
    assert len(init[b]) <= 15, ('the street over one bank', len(init[b]))
    pals_l, assign, err, unplaced = OP.exact_banks(town, len(LEARNED), init=[init[b] for b in LEARNED])
    for j, a in zip(town, assign):
        j['bank'] = LEARNED[a]
    for b, p in zip(LEARNED, pals_l):
        banks[b] = [tuple(int(v) for v in c) for c in p]
    for j in center + mart:
        assert {tuple(int(v) for v in c) for c in j['px'][j['mask'] > 0]} <= set(banks[j['bank']]), 'shared building colour lost'

    patterns = {}
    for j in jobs.values():
        pal = np.array(banks[j['bank']], float)
        ix = (((j['px'][:, None, :].astype(float) - pal[None]) ** 2 * B.CH_W).sum(-1).argmin(-1) + 1).astype(np.uint8)
        if j['layer'] == 1:
            ix = np.where(j['mask'] > 0, ix, 0).astype(np.uint8)
        vs = B.flips(ix.reshape(8, 8))
        o = min(range(4), key=lambda i: vs[i].tobytes())
        kk = vs[o].tobytes()
        if kk not in patterns:
            patterns[kk] = len(patterns)
        j['pattern'], j['flip'] = patterns[kk], o
    keep = {0} | used
    free_slots = [t for t in range(512) if t not in keep]
    order = sorted(patterns.items(), key=lambda kv: kv[1])
    slot = {}
    for n, (kk, i) in enumerate(order):
        slot[i] = free_slots[n] if n < len(free_slots) else 512 + n - len(free_slots)
    n_sec = max(0, len(order) - len(free_slots))
    report_budget = dict(saffron_tiles=len(order), primary_slots_free=len(free_slots), secondary_tiles=n_sec,
                         tiles_by_owner=tiles_by_owner(lay, jobs, owner))
    assert n_sec <= SECONDARY_TILES, ('tiles over budget', report_budget)
    prim_tiles = [tiles[t] if t in keep else np.zeros((8, 8), np.uint8) for t in range(512)]
    sec_tiles = [np.zeros((8, 8), np.uint8) for _ in range(n_sec)]
    for kk, i in order:
        ix = np.frombuffer(kk, np.uint8).reshape(8, 8)
        if slot[i] < 512:
            prim_tiles[slot[i]] = ix
        else:
            sec_tiles[slot[i] - 512] = ix
    filler = (sorted(used)[0], 0, 0)

    def entry(L):
        if L is None:
            return 0
        e = L['entry']
        if e[0] == 'cherry':
            t, b, f = e[1:]
        elif e[0] == 'hidden':
            t, b, f = filler
        else:
            j = jobs[e[1]]; t, b, f = slot[j['pattern']], j['bank'], j['flip']
        return t | ((f & 1) << 10) | ((f >> 1) << 11) | (b << 12)

    ok_meta = {}
    for i in range(len(metas)):
        es = [int(v) for v in metas[i]]
        if all((e & 1023) in keep and (e >> 12) in KEPT_BANKS for e in es):
            ok_meta[(tuple(es), int(attrs[i]))] = i
    free_prim_ids = [i for i in range(512) if i not in set(ok_meta.values())]
    new_meta, grid = {}, np.zeros((H, W), np.uint16)
    for y in range(H):
        for x in range(W):
            q = [(2 * x, 2 * y), (2 * x + 1, 2 * y), (2 * x, 2 * y + 1), (2 * x + 1, 2 * y + 1)]
            bot = [entry(lay[(a, b, 0)]) for a, b in q]
            tp = [entry(lay.get((a, b, 1))) for a, b in q]
            c = trav[y * W + x]
            layer = NORMAL if above[y, x] else COVERED
            c['layer'] = 'normal' if layer == NORMAL else 'covered'
            k = (tuple(bot + tp), c['behavior_id'] | (layer << 12))
            if k in ok_meta:
                grid[y, x] = ok_meta[k]
                continue
            if k not in new_meta:
                n = len(new_meta)
                new_meta[k] = 512 + n if n < 512 else free_prim_ids[n - 512]
            grid[y, x] = new_meta[k]
    assert len(new_meta) <= 512 + len(free_prim_ids), ('metatiles over budget', len(new_meta))
    prim_meta = [(tuple(int(v) for v in metas[i]), int(attrs[i])) if i in set(ok_meta.values()) else ((0,) * 8, 0)
                 for i in range(512)]
    sec_meta = []
    for k, i in sorted(new_meta.items(), key=lambda kv: kv[1]):
        if i < 512:
            prim_meta[i] = k
        else:
            sec_meta.append(k)

    pal_rgb = np.zeros((16, 16, 3), np.uint8)
    for b in KEPT_BANKS:
        pal_rgb[b] = np.array(pals[b], np.uint8)
    for b in LEARNED:
        for i, c in enumerate(banks[b][:15]):
            pal_rgb[b, i + 1] = [(v << 3) | (v >> 2) for v in c]

    allmeta = {i: prim_meta[i] for i in range(512)}
    for n, k in enumerate(sec_meta):
        allmeta[512 + n] = k
    tile_at = lambda t: prim_tiles[t] if t < 512 else sec_tiles[t - 512]
    native = np.zeros((H * 16, W * 16, 3), np.uint8)
    for y in range(H):
        for x in range(W):
            ents, _ = allmeta[int(grid[y, x])]
            for li, e in enumerate(ents):
                ix = tile_at(e & 1023)
                if e & 0x400: ix = ix[:, ::-1]
                if e & 0x800: ix = ix[::-1]
                qi = li % 4
                oy, ox = y * 16 + (qi // 2) * 8, x * 16 + (qi % 2) * 8
                m = ix > 0 if li >= 4 else np.ones((8, 8), bool)
                native[oy:oy + 8, ox:ox + 8][m] = pal_rgb[e >> 12][ix[m]]
    want = bottom.copy()
    a = top[..., 3] > 0; want[a] = top[..., :3][a]
    a = shared[..., 3] > 0; want[a] = shared[..., :3][a]
    d5 = np.abs(B.rgb5(native) - B.rgb5(want)).max(-1)
    hidden = np.zeros(d5.shape, bool)
    for (tx, ty, l), L in lay.items():
        if L.get('hidden'):
            hidden[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8] = True
    shared_exact = bool((d5[shared[..., 3] > 0] == 0).all())
    assert shared_exact, 'shared building pixels changed'
    EV.mkdir(parents=True, exist_ok=True)
    Image.fromarray(native).save(EV / 'native.png')
    np.savez_compressed(SRC / 'pack.npz', grid=grid, prim_tiles=np.array(prim_tiles, np.uint8),
                        sec_tiles=np.array(sec_tiles, np.uint8).reshape(-1, 8, 8), palettes=pal_rgb,
                        prim_meta=np.array([list(k[0]) + [k[1]] for k in prim_meta], np.uint16),
                        sec_meta=np.array([list(k[0]) + [k[1]] for k in sec_meta], np.uint16).reshape(-1, 9),
                        collision=np.array([[trav[y * W + x]['collision'] for x in range(W)] for y in range(H)], np.uint8),
                        elevation=np.array([[trav[y * W + x]['elevation'] for x in range(W)] for y in range(H)], np.uint8))
    (SRC / 'traversal.json').write_text(json.dumps(trav) + '\n')
    bad = (d5 > 0) & ~hidden
    report = dict(report_budget, secondary_tile_limit=SECONDARY_TILES, cherrygrove_tiles_kept=len(keep),
                  new_metatiles=len(new_meta), metatiles_in_secondary=len(sec_meta),
                  metatiles_in_primary=len(new_meta) - len(sec_meta), cherrygrove_metatiles_kept=len(ok_meta),
                  tile_positions=stats, learned_bank_error=err, unplaced_tile_kinds=len(unplaced),
                  colour_rgb5=dict(exact=int((d5[~hidden] == 0).sum()), within_1=int((d5[~hidden] <= 1).sum()),
                                   total=int((~hidden).sum()), worst=int(d5[~hidden].max())),
                  inexact_cells=sorted({(int(x) // 16, int(y) // 16) for y, x in zip(*np.nonzero(bad))})[:60],
                  shared_building_pixels_exact=shared_exact,
                  adaptations={f"{c['x']},{c['y']}": c['adaptation'] for c in trav if 'adaptation' in c})
    (EV / 'pack.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('adaptations',)}), len(report['adaptations']), 'adapted cells')

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
