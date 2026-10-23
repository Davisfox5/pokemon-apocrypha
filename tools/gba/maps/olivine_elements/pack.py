"""Pack Olivine's composed elements into one native map on its own tileset pair.

    python3 tools/gba/maps/olivine_elements/pack.py ENGINE_CHECKOUT [STYLE]   # STYLE C by default

Input is elements.py's compose-STYLE.npz (bottom layer, top layer, shared Center and Mart
layer). Olivine holds a Center, a Mart, a Lighthouse, a ferry terminal, a Gym hall, a
cafe and three houses: about 850 distinct tiles, where one secondary holds 496. So it gets
a primary of its own, gTileset_OlivinePrimary, derived from CherrygrovePrimary:

  - tiles 0-92 are CherrygrovePrimary's (tile 0 and the 92 sea tiles its animation
    rewrites; the primary keeps Cherrygrove's animation callback), and so is every other
    Cherrygrove tile Olivine draws, each at its own index; every other slot holds Olivine
  - banks 0, 1 and 3 are Cherrygrove's (grass, path and creams; sea and foam; the tree
    greens); banks 2, 4 and 5, which no tile Olivine keeps uses, are learned
  - every Cherrygrove metatile that still draws exactly as it did (its tiles kept, its
    banks 0, 1 or 3) keeps its id; the other primary ids hold Olivine metatiles

The secondary, gTileset_OlivineCity, holds 496 tiles (16 door-animation slots reserved)
and 512 metatiles. Palettes are one exact fit over the ten learned banks: the owner-locked
C06 Center's 21 colours split exactly over two banks, the shared Mart's 14 take one, each
building's palette takes a free bank whole, then every other tile fits the ten banks.

Traversal is the decoded HGSS permissions in Gen 3 behaviours. A cell HGSS blocks only
because its taller building model stands there, with nothing of the Gen 3 sprite in it or
only a roof's top edge in its lower half, is open ground (the player walks behind that edge).
Writes evidence/elements/pack-STYLE.json, native-STYLE.png and source/elements/pack-STYLE.npz.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build as B                                             # palette fitting helpers  # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/olivine-elements'
SRC, EV = ART / 'source', ART / 'evidence'
W, H = 64, 64
KEPT_BANKS = [0, 1, 3]                                        # Cherrygrove's, unchanged
LEARNED = [2, 4, 5, 6, 7, 8, 9, 10, 11, 12]
ANIM = 93                                                     # tiles 0-92: tile 0 and the animated sea
SECONDARY_TILES = 496
NORMAL, COVERED = 0, 1
CENTER_ORIGIN, CENTER_DOOR = (14, 29), (2, 4)                 # C06 door on HGSS's Center door (16, 33)
MART_ORIGIN, MART_DOOR = (27, 28), (2, 5)                     # shared Mart door on HGSS's Mart door (29, 33)
MART, CENTER = 1, 2                                           # shared_src ids
CLEAR = -1
FLAT = ('stone_',)                                            # ground details: never above the player
# Objects whose colours start whole in a bank of their own (sprites.py's palette groups;
# hosted props ride in their host's bank).
BANK_GROUPS = [('gym', 'yacht'), ('cafe', 'citysign'), ('house',), ('lighthouse', 'bench'), ('terminal', 'board')]
SMALL_GROUPS = [('bunting',)]

def read_pal(p):
    v = list(map(int, p.read_text().split()[3:51]))
    return [tuple(v[i * 3:i * 3 + 3]) for i in range(16)]

def exact_banks(jobs, nbanks, size=15, tries=9000, init=None):
    """Give tiles their exact 5-bit colours where the banks allow it. Only the maximal
    colour sets are packed (every other tile's set lies inside one of them and rides
    along), largest first. Tries take turns between three choices of bank (fewest new
    colours, most colours already shared, fewest colours held), later tries jitter the
    order, and the packing that leaves the fewest tile uses unplaced wins.
    Tiles that fit nowhere are quantized into the bank that suits them, so their loss
    stays local. init gives colours the banks already hold."""
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
    pals = []
    for b in banks:
        cols = sorted(b) or [(0, 0, 0)]
        pals.append(cols + [cols[-1]] * (size - len(cols)))
    px = np.stack([j['px'] for j in jobs]).astype(float)
    mask = np.stack([j['mask'] for j in jobs]).astype(float)
    errs = np.stack([B.tile_error(px, mask, np.array(p, float)) for p in pals], 1)
    assign = np.array([next((k for k, b in enumerate(banks) if c <= b), int(errs[i].argmin())) for i, c in enumerate(sets)])
    w = np.array([j['weight'] for j in jobs], float)
    err = errs[np.arange(len(jobs)), assign]
    unplaced = [j for j, c in zip(jobs, sets) if not any(c <= b for b in banks)]
    return pals, assign, float((err * w).sum() / (mask.sum(1) * w).sum()), unplaced

def cherrygrove(engine):
    d = engine / 'data/tilesets/primary/cherrygrove'
    a = np.array(Image.open(d / 'tiles.png')) & 15
    tiles = [a[y:y + 8, x:x + 8] for y in range(0, a.shape[0], 8) for x in range(0, a.shape[1], 8)][:512]
    pals = {b: read_pal(d / f'palettes/{b:02}.pal') for b in range(6)}
    metas = np.frombuffer((d / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
    attrs = np.frombuffer((d / 'metatile_attributes.bin').read_bytes(), '<u2')
    return tiles, pals, metas, attrs

def key5(px, mask=None):
    k = B.rgb5(px).astype(np.int16)
    if mask is not None:
        k[~mask] = CLEAR
    return k.tobytes()

def primary_index(tiles, pals, banks):
    """rgb5 content -> (tile, bank, flip) for every Cherrygrove tile under the kept banks."""
    opaque, masked = {}, {}
    for t, ix in enumerate(tiles):
        for b in banks:
            p = np.array(pals[b], np.int32)
            for f, v in enumerate(B.flips(ix)):
                rgb = p[v]
                m = v != 0
                masked.setdefault(key5(rgb, m), (t, b, f))
                if m.all():
                    opaque.setdefault(key5(rgb), (t, b, f))
    return opaque, masked

def traversal(engine, cells, art, edge, shared_src):
    """Gen 3 behaviour, collision and elevation per cell from the HGSS permissions. art is
    the per-cell 'has object art' grid; edge marks cells where only a building's top edge
    reaches, in the cell's lower half."""
    MB = B.behaviors(engine)
    perm = np.load(SRC / 'hgss/hgss-permissions.npz')
    types, coll = perm['types'], perm['collision']
    doors = {(CENTER_ORIGIN[0] + CENTER_DOOR[0], CENTER_ORIGIN[1] + CENTER_DOOR[1]): 'pokemon_center',
             (MART_ORIGIN[0] + MART_DOOR[0], MART_ORIGIN[1] + MART_DOOR[1]): 'poke_mart'}
    # Shared buildings: their wall rows are solid wherever the building covers a cell, so
    # no wall edge hangs over a walkable cell; C06's top row is a walkable roof overhang.
    body = np.zeros((H, W), bool)
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
            if (x, y) in doors:
                c.update(foot='door', behavior='MB_ANIMATED_DOOR', collision=0, elevation=3, door=doors[(x, y)])
            elif body[y, x]:
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3)
                if not k & 0x80:
                    c['adaptation'] = 'open in HGSS; inside the shared building (wider than HGSS\'s)'
            elif t == 0x15:
                c.update(foot='water', behavior='MB_OCEAN_WATER', collision=0, elevation=1)
            elif t == 0x17:
                c.update(foot='open', behavior='MB_SHALLOW_WATER', collision=0, elevation=3)
            elif t == 0x21:
                c.update(foot='open', behavior='MB_SAND', collision=0, elevation=3)
            elif t == 0x4C:
                c.update(foot='blocked', behavior='MB_ROCK_CLIMB', collision=1, elevation=3,
                         adaptation="HGSS's east-west Rock Climb wall; the field move is not obtainable yet")
            elif t == 0x69:
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3, adaptation='HGSS door; interior not built, so solid')
            elif t in (0x6E, 0x6F):
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=3, adaptation='HGSS warp (Lighthouse, port); interior not built, so solid')
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

def above_player(walkable, top, shared, owner):
    """Cells whose art draws above the player (layer type normal). A Gen 3 player is two
    cells tall: feet in its own cell, head in the cell north of it. Object art in a walkable
    cell draws above the player only when the object's base (the lowest row holding its
    pixels) lies further south, so the object stands in front: a roof or crown the player
    walks behind. A door, or any cell on an object's base row, is behind a player standing
    on it or south of it and stays below the player (covered), like every blocked cell.
    Top-layer art that belongs to no object keeps the plain rule (walkable means above)."""
    art = (top[..., 3] > 0) | (shared[..., 3] > 0)
    base = {}
    for name in set(owner[art].ravel().tolist()) - {''}:
        base[name] = int(np.nonzero((owner == name).any(1))[0].max()) // 16
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

def object_art(top, shared, owner):
    px = (top[..., 3] > 0) | (shared[..., 3] > 0)
    bld = px & ~np.char.startswith(owner, 'tree') & ~np.char.startswith(owner, 'fence')
    art = bld.reshape(H, 16, W, 16).any(axis=(1, 3))
    upper = bld.reshape(H, 16, W, 16)[:, :8].any(axis=(1, 3))
    edge = art & ~upper
    return art, edge

def main(engine, style):
    comp = np.load(SRC / 'elements' / f'compose-{style}.npz', allow_pickle=True)
    bottom, top, shared, shared_src, owner = comp['bottom'], comp['top'], comp['shared'], comp['shared_src'], comp['owner']
    cells = json.loads((SRC / 'elements/ledger.json').read_text())['detail']
    tiles, pals, metas, attrs = cherrygrove(engine)
    opaque_idx, masked_idx = primary_index(tiles, pals, KEPT_BANKS)
    trav = traversal(engine, cells, *object_art(top, shared, owner), shared_src)
    walkable = np.array([[trav[y * W + x]['foot'] in ('open', 'door', 'water') for x in range(W)] for y in range(H)])
    above = above_player(walkable, top, shared, owner)

    # Each 8x8 position's bottom and top content.
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

    # Cherrygrove's own tiles first (under its unchanged banks); a hidden bottom tile under
    # fully opaque top-layer art points at tile 0's neighbour, any kept tile will do.
    kept_sets = {b: {tuple(v >> 3 for v in c) for c in pals[b][1:]} for b in KEPT_BANKS}
    jobs, used = {}, set()
    stats = dict(cherrygrove=0, kept_bank=0, center=0, mart=0, learned=0, hidden=0)
    for pos, L in lay.items():
        layer = pos[2]
        if L.get('hidden'):
            L['entry'] = ('hidden',); stats['hidden'] += 1
            continue
        k = key5(L['px'], None if layer == 0 else L['mask'])
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
    cpals, cassign, cerr, _ = exact_banks(center, 2)
    assert cerr == 0, ('C06 does not split exactly over two banks', cerr)
    cbanks = [LEARNED[-2], LEARNED[-1]]
    for j, a in zip(center, cassign):
        j['bank'] = cbanks[a]
        init[j['bank']] |= {tuple(int(v) for v in c) for c in j['px'][j['mask'] > 0]}
    mart_pal = [tuple(v >> 3 for v in c) for c in read_pal(SRC / 'shared-art/poke-mart.pal')[1:]]
    mbank = LEARNED[-3]
    init[mbank] = set(mart_pal)
    for j in mart:
        assert {tuple(int(v) for v in c) for c in j['px'][j['mask'] > 0]} <= init[mbank], 'Mart colour outside its palette'
        j['bank'] = mbank
    kind = np.char.rstrip(np.char.rstrip(owner.astype(str), '0123456789'), '_')
    # The flag lines' eight colours ride in whichever Center bank has room (C06 fills one
    # bank and a part of the other).
    for names in SMALL_GROUPS:
        m = (top[..., 3] > 0) & np.isin(kind, names)
        cols = {tuple(c) for c in B.rgb5(top[m][:, :3]).tolist()}
        room = [b for b in cbanks + [mbank] if len(init[b] | cols) <= 15]
        assert room, ('no shared-building bank has room for', names)
        init[min(room, key=lambda b: len(init[b] | cols))] |= cols
    free = [b for b in LEARNED if not init[b]]
    for names, b in zip(BANK_GROUPS, free):
        m = (top[..., 3] > 0) & np.isin(kind, names)
        init[b] = {tuple(c) for c in B.rgb5(top[m][:, :3]).tolist()}
        assert len(init[b]) <= 15, ('palette group over one bank', names, len(init[b]))
    pals_l, assign, err, unplaced = exact_banks(town, len(LEARNED), init=[init[b] for b in LEARNED])
    for j, a in zip(town, assign):
        j['bank'] = LEARNED[a]
    for b, p in zip(LEARNED, pals_l):
        banks[b] = [tuple(int(v) for v in c) for c in p]
    for j in center + mart:
        assert {tuple(int(v) for v in c) for c in j['px'][j['mask'] > 0]} <= set(banks[j['bank']]), 'shared building colour lost'

    # Quantize and share patterns across flips.
    patterns = {}
    for j in jobs.values():
        pal = np.array(banks[j['bank']], float)
        ix = (((j['px'][:, None, :].astype(float) - pal[None]) ** 2 * B.CH_W).sum(-1).argmin(-1) + 1).astype(np.uint8)
        if j['layer'] == 1:
            ix = np.where(j['mask'] > 0, ix, 0).astype(np.uint8)
        ix = ix.reshape(8, 8)
        vs = B.flips(ix)
        o = min(range(4), key=lambda i: vs[i].tobytes())
        kk = vs[o].tobytes()
        if kk not in patterns:
            patterns[kk] = len(patterns)
        j['pattern'], j['flip'] = patterns[kk], o
    # Tile slots: Cherrygrove's sea animation and every Cherrygrove tile Olivine draws stay
    # where they are; Olivine's patterns fill the primary's other slots, then the secondary.
    keep = set(range(ANIM)) | used
    free_slots = [t for t in range(512) if t not in keep]
    order = sorted(patterns.items(), key=lambda kv: kv[1])
    slot = {}
    for n, (kk, i) in enumerate(order):
        slot[i] = free_slots[n] if n < len(free_slots) else 512 + n - len(free_slots)
    n_sec = max(0, len(order) - len(free_slots))
    assert n_sec <= SECONDARY_TILES, ('tiles over budget', len(order), len(free_slots) + SECONDARY_TILES)
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

    # Metatiles: a Cherrygrove metatile that still draws as it did keeps its id; Olivine's
    # go to the secondary first, then the primary's free ids.
    ok_meta = {}
    for i in range(len(metas)):
        es = [int(v) for v in metas[i]]
        if all((e & 1023) in keep and (e >> 12) in KEPT_BANKS for e in es):
            ok_meta[(tuple(es), int(attrs[i]))] = i
    free_prim_ids = [i for i in range(512) if i not in set(ok_meta.values())]
    new_meta, grid = {}, np.zeros((H, W), np.uint16)
    blank_top = [0, 0, 0, 0]
    for y in range(H):
        for x in range(W):
            q = [(2 * x, 2 * y), (2 * x + 1, 2 * y), (2 * x, 2 * y + 1), (2 * x + 1, 2 * y + 1)]
            bot = [entry(lay[(a, b, 0)]) for a, b in q]
            tp = [entry(lay.get((a, b, 1))) for a, b in q]
            has_top = any((a, b, 1) in lay for a, b in q)
            c = trav[y * W + x]
            layer = NORMAL if above[y, x] else COVERED
            c['layer'] = 'normal' if layer == NORMAL else 'covered'
            attr = c['behavior_id'] | (layer << 12)
            k = (tuple(bot + (tp if has_top else blank_top)), attr)
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

    # Palettes: 16 banks of 16 (index 0 transparent).
    pal_rgb = np.zeros((16, 16, 3), np.uint8)
    for b in KEPT_BANKS:
        pal_rgb[b] = np.array(pals[b], np.uint8)
    for b in LEARNED:
        for i, c in enumerate(banks[b][:15]):
            pal_rgb[b, i + 1] = [(v << 3) | (v >> 2) for v in c]

    # Decode the result back to pixels (what the GBA will draw).
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
    (EV / 'elements').mkdir(parents=True, exist_ok=True)
    Image.fromarray(native).save(EV / 'elements' / f'native-{style}.png')
    np.savez_compressed(SRC / 'elements' / f'pack-{style}.npz', grid=grid, prim_tiles=np.array(prim_tiles, np.uint8),
                        sec_tiles=np.array(sec_tiles, np.uint8).reshape(-1, 8, 8), palettes=pal_rgb,
                        prim_meta=np.array([list(k[0]) + [k[1]] for k in prim_meta], np.uint16),
                        sec_meta=np.array([list(k[0]) + [k[1]] for k in sec_meta], np.uint16).reshape(-1, 9),
                        collision=np.array([[trav[y * W + x]['collision'] for x in range(W)] for y in range(H)], np.uint8),
                        elevation=np.array([[trav[y * W + x]['elevation'] for x in range(W)] for y in range(H)], np.uint8))
    (SRC / 'elements' / f'traversal-{style}.json').write_text(json.dumps(trav) + '\n')
    bad = (d5 > 0) & ~hidden
    report = dict(style=style, olivine_tiles=len(order), primary_slots_free=len(free_slots), secondary_tiles=n_sec,
                  secondary_tile_limit=SECONDARY_TILES, cherrygrove_tiles_kept=len(keep),
                  new_metatiles=len(new_meta), metatiles_in_secondary=len(sec_meta),
                  metatiles_in_primary=len(new_meta) - len(sec_meta), cherrygrove_metatiles_kept=len(ok_meta),
                  tile_positions=stats, learned_bank_error=err, unplaced_tile_kinds=len(unplaced),
                  colour_rgb5=dict(exact=int((d5[~hidden] == 0).sum()), within_1=int((d5[~hidden] <= 1).sum()),
                                   total=int((~hidden).sum()), worst=int(d5[~hidden].max())),
                  inexact_cells=sorted({(int(x) // 16, int(y) // 16) for y, x in zip(*np.nonzero(bad))})[:60],
                  shared_building_pixels_exact=shared_exact,
                  adaptations={f"{c['x']},{c['y']}": c['adaptation'] for c in trav if 'adaptation' in c})
    (EV / 'elements' / f'pack-{style}.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('adaptations',)}), len(report['adaptations']), 'adapted cells')

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), sys.argv[2] if len(sys.argv) > 2 else 'C')
