"""Pack Celadon's composed elements into one native map on a tileset pair of its own.

    python3 tools/gba/maps/celadon_elements/pack.py ENGINE_CHECKOUT

Input is compose.py's compose.npz (bottom layer, top layer, the C06 Center's layer). Celadon
holds a Center, the Dept Store, the Condominiums and the tower beside them, the Game Corner
and its prize corner, eleven houses, the teal house, the cafe, the Gardens, the fountain
and the market: more than one secondary's 496 tiles. So it gets a primary of its own,
gTileset_KantoCeladonPrimary (512 tiles, tile 0 blank, banks 0-5), beside
gTileset_KantoCeladonCity (504 tiles, the last 8 kept for a 1x1 door animation, banks 6-12). Nothing in
either comes from another tileset; every colour is learned.

Palettes are one exact fit over the thirteen banks: the owner-locked C06 Center's 21 colours
split exactly over two banks, then every other tile fits the eleven left (Olivine's
exact_banks: the maximal colour sets packed largest first, many tries).

Traversal is HGSS's permissions in Gen 3 behaviours (traversal()). Writes
evidence/pack.json, native.png and source/elements/pack.npz, traversal.json.
"""
from __future__ import annotations
import json, sys
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image

import common as C
import build as B                                             # Olivine's palette helpers
import pack_olivine_shim as O

W, H, SRC, EV = C.W, C.H, C.SRC, C.EV
PRIMARY_TILES, SECONDARY_TILES = 512, 504
PRIMARY_BANKS, SECONDARY_BANKS = list(range(6)), list(range(6, 13))
NORMAL, COVERED = 0, 1
CENTER_BANKS = [11, 12]
CLEAR = -1
FLAT = ('post_',)

# HGSS's doors (its warps), the doors Celadon keeps; the Center's is C06's door.
DOORS = {(17, 13): 'services', (34, 13): 'hotel', (47, 13): 'pokemon_center', (34, 25): 'gamecorner',
         (39, 25): 'prize', (17, 42): 'gardens', (41, 37): 'cafe'}
START = (47, 15)                                              # in front of the Center, for reachability

def key5(px, mask=None):
    k = B.rgb5(px).astype(np.int16)
    if mask is not None:
        k[~mask] = CLEAR
    return k.tobytes()

def object_cells(top, shared, owner):
    """Per cell: whether object art shows there (not trees or posts), whether only its
    lower half holds any, and the names shown."""
    px = (top[..., 3] > 0) | (shared[..., 3] > 0)
    bld = px & ~np.char.startswith(owner, 'tree') & ~np.char.startswith(owner, 'post') & (owner != '')
    art = bld.reshape(H, 16, W, 16).any(axis=(1, 3))
    upper = bld.reshape(H, 16, W, 16)[:, :8].any(axis=(1, 3))
    return art, art & ~upper

def bases(owner):
    """Each object's base row: the lowest row its pixels reach."""
    out = {}
    for name in set(np.unique(owner).tolist()) - {''}:
        out[name] = int(np.nonzero((owner == name).any(1))[0].max()) // 16
    return out

def traversal(engine, cells, top, shared, owner):
    """Gen 3 behaviour, collision and elevation per cell.

    HGSS's permissions decide, with the Gen 3 sprites' own reach: a building cell HGSS blocks
    (its 3D model stands there) is blocked where the sprite has art in the cell and stands
    on or north of its base row; where the sprite misses it or only a roof's top edge
    reaches its lower half, it is open ground the player walks behind. Open cells that the
    player cannot reach from the street (behind the north row) stay blocked. The story's
    pieces block their own feet: a stall's bench row, a lamp's or a sign's cell. The
    Gardens' flower lots are open."""
    MB = B.behaviors(engine)
    perm = np.load(SRC / 'hgss/hgss-permissions.npz')
    types, coll = perm['types'], perm['collision']
    art, edge = object_cells(top, shared, owner)
    base = bases(owner)
    feet = {}
    for name, row in base.items():
        if name.startswith(('stall', 'lamp', 'board', 'citysign', 'fountain')):
            xs = np.nonzero((owner[row * 16:row * 16 + 16] == name).any(0))[0] // 16
            for x in set(xs.tolist()):
                feet[(int(x), row)] = name
    out = []
    for y in range(H):
        for x in range(W):
            t, k = int(types[y, x]), int(coll[y, x])
            cl = cells[y][x]
            lab = cl['lab']
            c = dict(x=x, y=y, hgss_type=t, hgss_collision=k, element=lab + cl['floor'][0])
            if (x, y) in DOORS:
                c.update(foot='door', behavior='MB_ANIMATED_DOOR', collision=0, elevation=3, door=DOORS[(x, y)])
            elif (x, y) in feet:
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3, prop=feet[(x, y)])
            elif cl['floor'] == 'water':
                c.update(foot='water', behavior='MB_POND_WATER', collision=0, elevation=1)
            elif lab == 'L':
                c.update(foot='ledge_south', behavior='MB_JUMP_SOUTH', collision=1, elevation=0)
            elif cl.get('story') == 'gardens bed':
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3, adaptation='a house lot in HGSS; the Gardens\' flower beds')
            elif lab in ('X', 'B') and (x, y) not in feet and not art[y, x]:
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3,
                         adaptation="HGSS blocks it (its 3D model or a prop the story moved); no Gen 3 art stands here")
            elif lab in ('X', 'B') and edge[y, x]:
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3,
                         adaptation="HGSS's taller model blocks it; only the Gen 3 roof's top edge reaches this cell")
            elif k & 0x80 or lab in ('T', 'f', 'X'):
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3)
            else:
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3)
            out.append(c)
    # Open cells the player cannot reach from the street stay blocked (behind the north row).
    foot = {(c['x'], c['y']): c for c in out}
    seen, q = {START}, deque([START])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            c = foot.get(n)
            if c is None or n in seen:
                continue
            if c['foot'] in ('open', 'door', 'water'):
                seen.add(n); q.append(n)
            elif c['foot'] == 'ledge_south' and dy == 1 and foot.get((n[0], n[1] + 1), {}).get('foot') == 'open':
                seen.add((n[0], n[1] + 1)); q.append((n[0], n[1] + 1))
    for c in out:
        if c['foot'] == 'open' and (c['x'], c['y']) not in seen:
            c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3)
            c['adaptation'] = 'open in Gen 3 terms but walled in (behind the buildings); blocked'
        c['behavior_id'] = MB[c['behavior']]
    return out

def above_player(walkable, top, shared, owner):
    """Olivine's rule: object art in a walkable cell draws above the player only when the
    object's base row lies further south (a roof or crown the player walks behind)."""
    art = (top[..., 3] > 0) | (shared[..., 3] > 0)
    base = bases(owner)
    out = np.zeros((H, W), bool)
    for y in range(H):
        for x in range(W):
            sl = np.s_[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
            a = art[sl]
            if not (walkable[y, x] and a.any()):
                continue
            names = set(owner[sl][a].ravel().tolist())
            out[y, x] = ('' in names and (top[sl][..., 3] > 0).any()) or \
                any(base[n] > y for n in names - {''} if not n.startswith(FLAT))
    return out

def bank_seeds(cells):
    """Each learned bank's colours to start from: four ground banks (lawn and paving;
    terrace, kerb and bridge with the stone greys; canal and ledges with the earth browns;
    the flower beds), the trees, and buildings.py's six palette groups. Grass and its
    lawn-edge colours go in every ground bank, so an edge tile fits whichever bank its
    material is in."""
    import ground as G, props as P, buildings as Bd
    t = C.textures()
    g = G.ground(cells, t)
    rgb5 = lambda a: {tuple(int(v) for v in c) for c in B.rgb5(a.reshape(-1, 3)).tolist()}
    cls = dict(lawn=set(), terrace=set(), water=set(), beds=set())
    for y in range(H):
        for x in range(W):
            c = cells[y][x]
            px = rgb5(g[y * 16:y * 16 + 16, x * 16:x * 16 + 16])
            if c['deco'] in ('flower01', 'flower02', 'flower03'):
                cls['beds'] |= px
            elif c['floor'] == 'water' or c['lab'] == 'L':
                cls['water'] |= px
            elif c['floor'] in ('brick', 'kerb', 'bridge'):
                cls['terrace'] |= px
            else:
                cls['lawn'] |= px
    tree = P.tree(t)
    out = {f'ground_{k}': v for k, v in cls.items()}
    out['tree'] = rgb5(tree[tree[..., 3] > 0][:, :3]) | {tuple(int(v) >> 3 for v in (115, 222, 173))}
    for names, _ in Bd.GROUPS:
        cols = set()
        for n in names:
            img = Bd.load(n)
            cols |= rgb5(img[img[..., 3] > 0][:, :3])
        out[names[0]] = cols
    post = P.post(t)
    out['ground_terrace'] |= rgb5(post[post[..., 3] > 0][:, :3])
    for k, v in out.items():
        print(k, len(v), sorted(v)) if len(v) > 15 else None
    return out

def main(engine):
    comp = np.load(SRC / 'elements/compose.npz')
    bottom, top, shared, owner = comp['bottom'], comp['top'], comp['shared'], comp['owner']
    cells = json.loads((SRC / 'elements/cells.json').read_text())
    trav = traversal(engine, cells, top, shared, owner)
    walkable = np.array([[trav[y * W + x]['foot'] in ('open', 'door', 'water') for x in range(W)] for y in range(H)])
    above = above_player(walkable, top, shared, owner)

    lay = {}
    for ty in range(H * 2):
        for tx in range(W * 2):
            sl = np.s_[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            sh = shared[sl][..., 3] > 0
            tp = top[sl][..., 3] > 0
            fixed = 'center' if sh.any() else None
            if sh.all() and not above[ty // 2, tx // 2]:
                lay[(tx, ty, 0)] = dict(px=shared[sl][..., :3], mask=np.ones((8, 8), bool), fixed=fixed)
                continue
            hidden = tp.all() and not sh.any()
            lay[(tx, ty, 0)] = dict(px=None if hidden else bottom[sl], mask=np.ones((8, 8), bool), fixed=None, hidden=hidden)
            if sh.any():
                assert not tp.any(), ('Center over top-layer art', tx, ty)
                lay[(tx, ty, 1)] = dict(px=shared[sl][..., :3], mask=sh, fixed=fixed)
            elif tp.any():
                lay[(tx, ty, 1)] = dict(px=top[sl][..., :3], mask=tp, fixed=None)

    jobs = {}
    for pos, L in lay.items():
        if L.get('hidden'):
            L['entry'] = ('hidden',)
            continue
        k = key5(L['px'], None if pos[2] == 0 else L['mask'])
        jk = (k, pos[2], L['fixed'])
        j = jobs.setdefault(jk, dict(px=B.rgb5(L['px']).reshape(64, 3), mask=L['mask'].ravel().astype(np.uint8), weight=0,
                                     layer=pos[2], fixed=L['fixed']))
        j['weight'] += 1
        L['entry'] = ('job', jk)
    center = [j for j in jobs.values() if j['fixed'] == 'center']
    town = [j for j in jobs.values() if not j['fixed']]
    cpals, cassign, cerr, _ = O.exact_banks(center, 2)
    assert cerr == 0, ('C06 does not split exactly over two banks', cerr)
    banks = {}
    for j, a in zip(center, cassign):
        j['bank'] = CENTER_BANKS[a]
    for b, p in zip(CENTER_BANKS, cpals):
        banks[b] = [tuple(int(v) for v in c) for c in p]
    seeds = bank_seeds(cells)
    learned = [b for b in range(13) if b not in CENTER_BANKS]
    assert len(seeds) == len(learned), (len(seeds), len(learned))
    init = [seeds[k] for k in seeds] + [set(banks[b]) for b in CENTER_BANKS]
    order = learned + CENTER_BANKS
    pals_l, assign, err, unplaced = O.exact_banks(town, len(order), init=init)
    for j, a in zip(town, assign):
        j['bank'] = order[a]
    for b, p in zip(order, pals_l):
        banks[b] = [tuple(int(v) for v in c) for c in p]
    report_seeds = {k: len(v) for k, v in seeds.items()}

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
    n_pat = len(patterns)
    report = dict(bank_seeds=report_seeds, tiles=n_pat, tile_limit=PRIMARY_TILES - 1 + SECONDARY_TILES, jobs=len(jobs), unplaced_tile_kinds=len(unplaced),
                  unplaced_uses=sum(j['weight'] for j in unplaced), bank_error=err,
                  colours=sum(len(set(v)) for v in banks.values()))
    print(json.dumps(report))
    if n_pat > PRIMARY_TILES - 1 + SECONDARY_TILES:
        raise SystemExit('tiles over budget')
    # Tile slots: 0 blank, then the primary, then the secondary. A tile drawn only with
    # secondary banks may still live in the primary; any tile may use any bank.
    order = sorted(patterns.items(), key=lambda kv: kv[1])
    slot = {i: (1 + n if n < PRIMARY_TILES - 1 else PRIMARY_TILES + n - (PRIMARY_TILES - 1)) for n, (_, i) in enumerate(order)}
    prim_tiles = [np.zeros((8, 8), np.uint8) for _ in range(PRIMARY_TILES)]
    sec_tiles = [np.zeros((8, 8), np.uint8) for _ in range(max(0, n_pat - (PRIMARY_TILES - 1)))]
    for kk, i in order:
        ix = np.frombuffer(kk, np.uint8).reshape(8, 8)
        if slot[i] < PRIMARY_TILES:
            prim_tiles[slot[i]] = ix
        else:
            sec_tiles[slot[i] - PRIMARY_TILES] = ix
    filler = (1, 0, 0)

    def entry(L):
        if L is None:
            return 0
        e = L['entry']
        if e[0] == 'hidden':
            t, b, f = filler
        else:
            j = jobs[e[1]]; t, b, f = slot[j['pattern']], j['bank'], j['flip']
        return t | ((f & 1) << 10) | ((f >> 1) << 11) | (b << 12)

    metas, grid = {}, np.zeros((H, W), np.uint16)
    for y in range(H):
        for x in range(W):
            q = [(2 * x, 2 * y), (2 * x + 1, 2 * y), (2 * x, 2 * y + 1), (2 * x + 1, 2 * y + 1)]
            bot = [entry(lay[(a, b, 0)]) for a, b in q]
            tp = [entry(lay.get((a, b, 1))) for a, b in q]
            c = trav[y * W + x]
            layer = NORMAL if above[y, x] else COVERED
            c['layer'] = 'normal' if layer == NORMAL else 'covered'
            k = (tuple(bot + tp), c['behavior_id'] | (layer << 12))
            if k not in metas:
                metas[k] = len(metas)
            grid[y, x] = metas[k]
    assert len(metas) <= 1024, ('metatiles over budget', len(metas))
    meta_rows = [list(k[0]) + [k[1]] for k, _ in sorted(metas.items(), key=lambda kv: kv[1])]
    pal_rgb = np.zeros((16, 16, 3), np.uint8)
    for b in range(13):
        for i, c in enumerate(banks[b][:15]):
            pal_rgb[b, i + 1] = [(v << 3) | (v >> 2) for v in c]

    tile_at = lambda t: prim_tiles[t] if t < PRIMARY_TILES else sec_tiles[t - PRIMARY_TILES]
    native = np.zeros((H * 16, W * 16, 3), np.uint8)
    for y in range(H):
        for x in range(W):
            ents = meta_rows[int(grid[y, x])][:8]
            for li, e in enumerate(ents):
                ix = tile_at(e & 1023)
                if e & 0x400: ix = ix[:, ::-1]
                if e & 0x800: ix = ix[::-1]
                qi = li % 4
                oy, ox = y * 16 + (qi // 2) * 8, x * 16 + (qi % 2) * 8
                m = ix > 0 if li >= 4 else np.ones((8, 8), bool)
                native[oy:oy + 8, ox:ox + 8][m] = pal_rgb[e >> 12][ix[m]]
    want = bottom.copy()
    for layer in (top, shared):
        a = layer[..., 3] > 0
        want[a] = layer[..., :3][a]
    d5 = np.abs(B.rgb5(native) - B.rgb5(want)).max(-1)
    hidden = np.zeros(d5.shape, bool)
    for (tx, ty, l), L in lay.items():
        if L.get('hidden'):
            hidden[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8] = True
    center_exact = bool((d5[shared[..., 3] > 0] == 0).all())
    assert center_exact, 'C06 pixels changed'
    EV.mkdir(parents=True, exist_ok=True)
    Image.fromarray(native).save(EV / 'native.png')
    np.savez_compressed(SRC / 'elements/pack.npz', grid=grid, prim_tiles=np.array(prim_tiles, np.uint8),
                        sec_tiles=np.array(sec_tiles, np.uint8).reshape(-1, 8, 8), palettes=pal_rgb,
                        metatiles=np.array(meta_rows, np.uint16).reshape(-1, 9),
                        collision=np.array([[trav[y * W + x]['collision'] for x in range(W)] for y in range(H)], np.uint8),
                        elevation=np.array([[trav[y * W + x]['elevation'] for x in range(W)] for y in range(H)], np.uint8))
    (SRC / 'elements/traversal.json').write_text(json.dumps(trav) + '\n')
    bad = (d5 > 0) & ~hidden
    report.update(primary_tiles=min(n_pat, PRIMARY_TILES - 1) + 1, secondary_tiles=len(sec_tiles), secondary_tile_limit=SECONDARY_TILES,
                  metatiles=len(metas), metatile_limit=1024,
                  colour_rgb5=dict(exact=int((d5[~hidden] == 0).sum()), total=int((~hidden).sum()), worst=int(d5[~hidden].max())),
                  inexact_cells=sorted({(int(x) // 16, int(y) // 16) for y, x in zip(*np.nonzero(bad))})[:60],
                  center_pixels_exact=center_exact,
                  adaptations={f"{c['x']},{c['y']}": c['adaptation'] for c in trav if 'adaptation' in c})
    (EV / 'pack.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'adaptations'}), len(report['adaptations']), 'adapted cells')

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
