"""Celadon round 6 for the engine: the approved concept (concept.py) as streamed glyphs.

    python3 tools/gba/maps/celadon_elements/stream6.py

The concept holds about 3,500 unique 8x8 tiles in 366 colours, against one tileset pair's
1,024 tiles and 13 banks of 15 colours. So the city streams, as Goldenrod does
(codex/olivine-goldenrod-playbook-20261019, src/goldenrod_view.c): every cell's eight tile
entries come from this module's tables by map position, and the engine copies each glyph
into a VRAM slot when the cell is drawn and frees it when the cell leaves the 16 x 16 cell
view. Palettes stream the same way: each glyph entry names one of the city's palettes, each
palette has a fixed bank (0-12) such that no two palettes sharing a bank ever stand in one
view, and the engine loads a palette into its bank when a cell drawn with it arrives.

The pictures are the concept's own (concept.compose(layers=True)): the ground with its
bridges, flowers and painted lanes, then everything that stands in painter's order. Each
8x8 tile is split the Olivine way (AGENTS.md, "Objects have no background"): the frontmost
object takes the top layer and the bottom layer is the picture with that object left out,
so no pixel of either is lost and palettes stay with their families. Every colour is the
concept's exact 5-bit colour; a tile layer of more than 15 colours (none expected) would
be reduced and reported.

Traversal (per cell: behaviour, collision, elevation, layer type) follows AGENTS.md's depth
rule: a walkable cell draws above the player only when its top-layer object's base row lies
further south (a roof, crown or lamp head the player walks behind); a building's art blocks
its cells but a cell its art reaches only in the lower half (a roof's top edge) is open; a
tree blocks its two foot rows, a lamp, bench, plant or stall its base row; the canal and pond are
pond water; doors with an interior are doors, a door to nothing yet is solid.

Writes gba/art/celadon-elements/source/stream6.npz and evidence/v6/engine/{stream.json,
native.png, traversal.png}.
"""
from __future__ import annotations
import json, sys
from collections import deque, defaultdict
from pathlib import Path
import numpy as np
from PIL import Image

import common as C
import concept as K
import plan as PL
import custom_art as A
import build as B                                             # Olivine's palette helpers
import pack_olivine_shim as O

W, H = PL.W, PL.H
OUT = C.EV / 'v6' / 'engine'
SLOTS = 1008                          # VRAM glyph slots the cache may use (the top 16 stay reserved for doors)
MARGIN = 7                            # the camera's reach past the player (MAP_OFFSET)
VIEW = 16                             # the BG tilemap's 32 x 32 tiles: 16 x 16 cells
SCREEN = (7, 7, 5, 5)                 # cells shown left, right, above and below the player (240 x 160, a row spare)
BANKS = 13
NORMAL, COVERED = 0, 1
BUILDINGS = ('dept_store', 'apartments', 'hotel', 'center', 'game_corner', 'cafe', 'flat')
BASE_ONLY = ('lamp', 'bench', 'plant', 'stall')        # AGENTS.md: a stall blocks its counter row, its canopy is walk-behind
# The doors (plan.DOORS) and the rooms behind them; None: no interior yet, so the door is solid.
ROOMS = dict(dept_store='MAP_KANTO_CELADON_MARKET_SERVICES', apartments=None, hotel='MAP_KANTO_CELADON_HOTEL_LOBBY',
             center='MAP_KANTO_CELADON_POKEMON_CENTER', gamecorner='MAP_KANTO_CELADON_GAME_CORNER', house_g0=None,
             cafe='MAP_KANTO_CELADON_CAFE')
START = (45, 15)                      # in front of the Center, for reachability
# A caller streaming more than the city (route7/world.py: Celadon and Route 7 as one world) sets
# these: where the tables go, which foot kinds a player stands on, and a hook over the tile jobs.
NPZ = C.SRC / 'stream6.npz'
WALKABLE = ('open', 'door')
JOB_HOOK = None

def rgb5(a):
    return (np.asarray(a)[..., :3] >> 3).astype(np.uint8)

# --------------------------------------------------------------------------- the pictures
def pictures():
    L = K.compose(layers=True)
    ground = L['ground'][..., :3].copy()
    objs = []
    kinds = {name: kind for name, kind, *_ in PL.PLACES}
    for X, Y, img, fam, name in L['objects']:
        if fam == 'house':
            fam = kinds[name]                                   # house_plum, house_amber, ...
        a = img[..., 3] > 0
        ys = np.nonzero(a.any(1))[0]
        objs.append(dict(X=X, Y=Y, img=img, fam=fam, name=name, base=(Y + int(ys.max())) // 16))
    return ground, objs, L['cells']

def frames(objs):
    """The fountains' four frames: the objects' images per frame (frame 0 is the concept's)."""
    out = []
    for f in range(4):
        fr = []
        for o in objs:
            if o['fam'] == 'fountain':
                img = A.fountain(f)
            elif o['fam'] == 'blossom_pool':
                img = A.blossom_pool(f)
            else:
                img = o['img']
            assert img.shape == o['img'].shape, (o['name'], img.shape, o['img'].shape)
            fr.append(img)
        out.append(fr)
    return out

def paint(ground, objs, imgs, skip=None):
    """Ground, then every object but `skip` in painter's order; and per pixel the front object."""
    pic = ground.copy()
    front = np.full(ground.shape[:2], -1, np.int32)
    for i, (o, img) in enumerate(zip(objs, imgs)):
        if i == skip or img is None:
            continue
        X, Y = o['X'], o['Y']
        y0, x0 = max(Y, 0), max(X, 0)
        y1, x1 = min(Y + img.shape[0], H * 16), min(X + img.shape[1], W * 16)
        if y1 <= y0 or x1 <= x0:
            continue
        part = img[y0 - Y:y1 - Y, x0 - X:x1 - X]
        m = part[..., 3] > 0
        pic[y0:y1, x0:x1][m] = part[..., :3][m]
        front[y0:y1, x0:x1][m] = i
    return pic, front

# --------------------------------------------------------------------------- traversal
def object_mask(o, img=None):
    img = o['img'] if img is None else img
    m = np.zeros((H * 16, W * 16), bool)
    X, Y = o['X'], o['Y']
    y0, x0 = max(Y, 0), max(X, 0)
    y1, x1 = min(Y + img.shape[0], H * 16), min(X + img.shape[1], W * 16)
    if y1 > y0 and x1 > x0:
        m[y0:y1, x0:x1] = img[y0 - Y:y1 - Y, x0 - X:x1 - X, 3] > 0
    return m

def traversal(cells, objs):
    """Per cell: foot ('open', 'blocked', 'water', 'door'), and what decided it."""
    foot = np.full((H, W), 'open', '<U8')
    why = np.full((H, W), '', '<U24')
    foot[cells == 'forest'] = 'blocked'; why[cells == 'forest'] = 'forest'
    foot[cells == 'water'] = 'water'; why[cells == 'water'] = 'water'
    for o in objs:
        m = object_mask(o).reshape(H, 16, W, 16)
        art = m.any(axis=(1, 3))
        upper = m[:, :8].any(axis=(1, 3))
        ys, xs = np.nonzero(art)
        for y, x in zip(ys, xs):
            if o['fam'] == 'tree':
                hit = y >= o['base'] - 1
            elif o['fam'] in BASE_ONLY:
                hit = y == o['base']
            else:
                hit = y <= o['base'] and (upper[y, x] or y == o['base'])   # a roof's top edge alone is open
            if hit and foot[y, x] != 'water':
                foot[y, x] = 'blocked'; why[y, x] = o['name'][:24]
    doors = {}
    for name, (x, y) in PL.DOORS.items():
        room = ROOMS.get(name)
        if room is None:
            why[y, x] = f'door to nothing: {name}'[:24]
            continue
        foot[y, x] = 'door'; why[y, x] = name; doors[name] = (x, y)
    # open cells the player cannot reach stay blocked (walled in behind buildings)
    seen, q = {START}, deque([START])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if 0 <= n[0] < W and 0 <= n[1] < H and n not in seen and foot[n[1], n[0]] in ('open', 'door'):
                seen.add(n)
                if foot[n[1], n[0]] == 'open':
                    q.append(n)
    walled = 0
    for y in range(H):
        for x in range(W):
            if foot[y, x] == 'open' and (x, y) not in seen:
                foot[y, x] = 'blocked'; why[y, x] = 'walled in'; walled += 1
    return foot, why, doors, walled

# --------------------------------------------------------------------------- layers
def split(ground, objs, imgs, foot):
    """Per 8x8 tile: the bottom layer (opaque RGB, or None where the top hides it all) and
    the top layer (RGB and mask, or None); per cell its layer type and any depth conflict.
    The top layer holds the frontmost object and every other object in the tile of its own
    palette group (a house beside its terrace neighbour), so the bottom is the ground alone
    wherever it can be. A tree behind a tree stays in the bottom over its grass: the trees'
    banks hold their grass, and two crowns in one top tile pack worse."""
    pic, front = paint(ground, objs, imgs)
    kin = [group_of(o['fam'], 1) for o in objs]
    cache = {}
    def without(skip):
        if skip not in cache:
            cache[skip] = paint(ground, objs, [None if i in skip else im for i, im in enumerate(imgs)])[0]
        return cache[skip]
    bot, top = {}, {}
    for ty in range(H * 2):
        for tx in range(W * 2):
            sl = np.s_[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            f = front[sl]
            if (f < 0).all():
                bot[(tx, ty)] = pic[sl]
                continue
            F = int(f.max())
            same = frozenset(int(i) for i in np.unique(f) if i >= 0 and kin[i] == kin[F] and (kin[F] != 'tree' or i == F))
            m = np.isin(f, list(same))
            top[(tx, ty)] = (pic[sl].copy(), m, F, same)
            bot[(tx, ty)] = None if m.all() else without(same)[sl]
    layer = np.full((H, W), COVERED, np.uint8)
    conflicts = []
    for y in range(H):
        for x in range(W):
            if foot[y, x] not in WALKABLE:
                continue
            tops = [top.get((2 * x + a, 2 * y + b)) for b in (0, 1) for a in (0, 1)]
            over = set().union(*[t[3] for t in tops if t is not None])
            if not over:
                continue
            south = {i for i in over if objs[i]['base'] > y}
            if south:
                layer[y, x] = NORMAL
                if over - south:
                    conflicts.append((x, y, 'top mixes', sorted(objs[i]['name'] for i in over)))
    return pic, bot, top, layer, conflicts

# --------------------------------------------------------------------------- palettes
def colour_set(px, mask=None, five=False):
    c = (np.asarray(px)[..., :3] if five else rgb5(px)).reshape(-1, 3)
    if mask is not None:
        c = c[mask.ravel()]
    return frozenset(map(tuple, c.tolist()))

# Palette groups: each element family's tiles go into banks of their own, `k` of them, after
# its colours are brought down to `target` (None: as drawn) by weighted k-means seeded
# farthest-first, each cluster taking its member nearest the centre (so every colour left is
# one the art already had). The owner-locked C06 Center keeps all 21 of its colours, split
# exactly over two banks. Bottom tiles where an object stands behind the front one go with
# that object's group (a tree behind a tree, over grass, in the trees' banks).
GROUPS = dict(center=(2, None), dept_store=(2, None), game_corner_top=(1, None), game_corner_front=(1, None), hotel=(1, None), apartments=(1, None),
              flat=(1, None), cafe=(1, None), house_a=(1, None), house_b=(1, None), house_c=(1, None), stall=(2, None), tree=(3, 'near1'), street=(1, None),
              plant=(1, None), fountain=(1, None), blossom_pool=(1, None), ground=(5, 'near2'))
PROPS = dict(lamp='street', bench='street',
             # the houses' hues in pairs that stand near each other: the Game Corner's plum and
             # amber, the north row's coral and teal, the terrace's blue and green
             house_plum='house_a', house_amber='house_a', house_coral='house_b', house_teal='house_b',
             house_blue='house_c', house_green='house_c')
EXACT = ('center',)
# Tall buildings whose roof and front take a bank each, split at this cell row, so the views
# south of the building hold only its front's bank (the Game Corner beside the cafe and houses).
SPLIT_ROWS = dict(game_corner=25)                   # never quantized (the owner-locked C06 Center)
def group_of(fam, layer):
    if layer == 1:
        return PROPS.get(fam, fam)
    rest = [f for f in fam.split('+') if f != 'ground']
    return PROPS.get(rest[0], rest[0]) if rest else 'ground'

def reduce_colours(jobs, target):
    """The group's colours down to `target`, as a colour -> colour map."""
    w = defaultdict(int)
    for j in jobs:
        for px, m in [(j['px'], j['mask'])] + list(j.get('frames', {}).values()):
            c = px.reshape(-1, 3) if m is None else px[m]
            for t in map(tuple, c.tolist()):
                w[t] += 1
    cols = sorted(w)
    if isinstance(target, str):                                # 'near': fold each colour into a more used one
        d = int(target[4:])                                    # at most d 5-bit steps away in every channel,
        together = defaultdict(set)                            # and never in one tile with it (so no texture flattens)
        for j in jobs:
            for px, m in [(j['px'], j['mask'])] + list(j.get('frames', {}).values()):
                cs = set(map(tuple, (px.reshape(-1, 3) if m is None else px[m]).tolist()))
                for c in cs:
                    together[c] |= cs
        out = {c: c for c in cols}
        for c in sorted(cols, key=lambda c: (w[c], c)):
            if out[c] != c:
                continue
            near = [o for o in cols if o != c and out[o] == o and w[o] > w[c] and max(abs(a - b) for a, b in zip(c, o)) <= d
                    and not ({k for k in cols if out[k] == c} & together[o]) and o not in together[c]]
            if near:
                to = min(near, key=lambda o: (sum((a - b) ** 2 for a, b in zip(c, o)), -w[o], o))
                for k in cols:
                    if out[k] == c:
                        out[k] = to
        return out
    if target is None or len(cols) <= target:
        return {c: c for c in cols}
    arr = np.array(cols, float)
    wt = np.array([w[c] for c in cols], float)
    cent = B.kmeans_colors(arr, wt, target).astype(float)
    lab = (((arr[:, None] - cent[None]) ** 2) * B.CH_W).sum(-1).argmin(1)
    out = {}
    for k in range(len(cent)):
        idx = np.nonzero(lab == k)[0]
        if not len(idx):
            continue
        rep = idx[(((arr[idx] - cent[k]) ** 2) * B.CH_W).sum(1).argmin()]
        for i in idx:
            out[cols[i]] = cols[rep]
    return out

def remap(px, cmap):
    flat = px.reshape(-1, 3)
    return np.array([cmap.get(tuple(c), tuple(c)) for c in flat.tolist()], np.uint8).reshape(px.shape)

def pack_local(js, lam=8.0, near=8):
    """One group's tile layers into palettes of 15 colours, every tile exact: its colour sets
    largest first, each into the group palette it grows least, where a palette not yet used
    within `near` cells of the set's tiles costs `lam` more, so neighbouring tiles of one
    object keep to few palettes; a new palette costs the set's size plus `lam`."""
    sets = defaultdict(list)
    for j in js:
        c = colour_set(j['px'], j['mask'], True)
        for px, m in j['frames'].values():
            c = c | colour_set(px, m, True)
        j['set'] = c
        sets[c].append((j['key'][0] // 2, j['key'][1] // 2))
    pals, choice = [], {}
    for c in sorted(sets, key=lambda c: (-len(c), -len(sets[c]), sorted(c))):
        cells = sets[c]
        best = (len(c) + lam, None)
        for n, p in enumerate(pals):
            u = len(p['cols'] | c)
            if u > 15:
                continue
            fresh = sum(1 for x, y in cells if not p['near'][y, x]) / len(cells)
            cost = (u - len(p['cols'])) + lam * fresh
            if cost < best[0]:
                best = (cost, n)
        n = best[1]
        if n is None:
            pals.append(dict(cols=set(), near=np.zeros((H, W), bool)))
            n = len(pals) - 1
        p = pals[n]
        p['cols'] |= c
        for x, y in cells:
            p['near'][max(0, y - near):y + near + 1, max(0, x - near):x + near + 1] = True
        choice[c] = n
    for j in js:
        j['pal'] = choice[j['set']]
    out = []
    for p in pals:
        cols = sorted(p['cols'], key=lambda c: (3 * c[0] + 4 * c[1] + 2 * c[2], c))
        out.append(cols + [cols[-1]] * (15 - len(cols)))
    return out

def pack_palettes(jobs):
    """Every job's group, its colours reduced, its tiles packed into the group's banks
    (Olivine's exact_banks). Returns the palettes (15 colours each) and per group its
    reduction and the tiles no bank holds exactly (quantized into the bank that suits them)."""
    by = defaultdict(list)
    for j in jobs:
        j['group'] = group_of(j['fam'], j['key'][2])
        if j['group'] in SPLIT_ROWS:                           # a tall building's roof and front in banks of their own
            j['group'] += '_top' if j['key'][1] < SPLIT_ROWS[j['group']] * 2 else '_front'
        by[j['group']].append(j)
    pals, lossy = [], {}
    for g in sorted(by):
        k, target = GROUPS[g]
        js = by[g]
        cmap = reduce_colours(js, target)
        for j in js:
            j['px'] = remap(j['px'], cmap)
            j['frames'] = {f: (remap(px, cmap), m) for f, (px, m) in j.get('frames', {}).items()}
        uniq = {}
        for j in js:
            for px, m in [(j['px'], j['mask'])] + list(j['frames'].values()):
                mm = np.ones(64, np.uint8) if m is None else m.ravel().astype(np.uint8)
                key = (px.tobytes(), mm.tobytes())
                if key not in uniq:
                    uniq[key] = dict(px=px.reshape(64, 3).astype(int), mask=mm, weight=0, owners=[])
                # a bottom tile where an object stands over the ground (a stall behind a bench, a house
                # behind its neighbour) must keep its ground's colours in this group's banks
                uniq[key]['weight'] += 40 if (j['key'][2] == 0 and '+' in j['fam'] and g != 'tree') else 1
                uniq[key]['owners'].append(j)
        ej = list(uniq.values())
        p, assign, err, unplaced = O.exact_banks(ej, k, tries=3000 if g == 'ground' else 300)
        how = 'exact'
        if unplaced and g not in EXACT:
            fits = [B.fit_banks(ej, k, seed, scheme) for scheme in ('flat', 'sqrt') for seed in range(4)]
            fp, fa, fe = min(fits, key=lambda r: r[2])
            if fe < 0.6 * err:                                 # exact keeps most tiles exact; a fit must earn it
                p, assign, err, how = [[tuple(int(v) for v in c) for c in pp] for pp in fp], fa, fe, 'fit'
        assert g not in EXACT or not unplaced, (g, 'not exact')
        base = len(pals)
        pals += [[tuple(int(v) for v in c) for c in pp] for pp in p]
        for e, a in zip(ej, assign):
            for j in e['owners']:
                j.setdefault('banks', []).append(base + int(a))
        for j in js:
            j['pal'] = j['banks'][0]                           # a fountain frame that landed elsewhere is quantized into frame 0's
            j['palette_group'] = g
        lossy[g] = dict(tiles=len(js), drawn=len(cmap), how=how, unplaced=len(unplaced) if how == 'exact' else None,
                        error=round(err, 3))
    return pals, lossy

# --------------------------------------------------------------------------- glyphs and views
def flips(ix):
    return [ix, ix[:, ::-1], ix[::-1], ix[::-1, ::-1]]

def outside(x, y):
    """Where an off-map cell's art comes from (the engine's CeladonViewSource): the town's
    border forest repeats with its own period (2 across, 4 down) from the north-west corner's
    pure forest, the roads to Route 7 and Route 16 and the canal run on off their edges."""
    if 0 <= x < W and 0 <= y < H:
        return x, y
    if x < 0 and 34 <= y < 38:
        return x & 1, y
    if x >= W and 16 <= y < 21:
        return W - 2 + (x & 1), y
    if y < 0 and 0 <= x < W:
        return x, y & 3
    return x & 1, y & 3

def colour_banks(conflict, nodes, restarts=400, limit=2_000_000):
    """Banks for the palettes so no two in one view share one: DSATUR (the palette with the
    most banks already taken by its neighbours first), restarted with seeded tie-breaks, then
    an exact DSATUR backtracking search; None if the views cannot be coloured with BANKS."""
    import random
    nodes = list(nodes)
    adj = {p: set(conflict.get(p, ())) & set(nodes) for p in nodes}
    def dsatur(rng):
        bank = {}
        tie = {q: rng.random() for q in nodes}
        while len(bank) < len(nodes):
            p = max((q for q in nodes if q not in bank), key=lambda q: (len({bank[r] for r in adj[q] if r in bank}), len(adj[q]), tie[q]))
            used = {bank[r] for r in adj[p] if r in bank}
            free = [b for b in range(BANKS) if b not in used]
            if not free:
                return None
            bank[p] = free[0]
        return bank
    for t in range(restarts):
        b = dsatur(random.Random(t))
        if b is not None:
            return b
    out, steps = {}, [0]
    def go():
        if len(out) == len(nodes):
            return True
        steps[0] += 1
        if steps[0] > limit:
            return False
        p = max((q for q in nodes if q not in out), key=lambda q: (len({out[r] for r in adj[q] if r in out}), len(adj[q])))
        used = {out[r] for r in adj[p] if r in out}
        for b in range(BANKS):
            if b not in used:
                out[p] = b
                if go():
                    return True
                del out[p]
        return False
    return dict(out) if go() else None

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    import os, pickle
    cache = Path(os.environ['STREAM6_CACHE']) if os.environ.get('STREAM6_CACHE') else None
    if cache and cache.exists():
        ground, objs, cells, fr, foot, why, doors, walled, pic, bot, top, layer, conflicts, frame_split = pickle.load(open(cache, 'rb'))
    else:
        ground, objs, cells = pictures()
        fr = frames(objs)
        foot, why, doors, walled = traversal(cells, objs)
        pic, bot, top, layer, conflicts = split(ground, objs, fr[0], foot)
        frame_split = [None] + [split(ground, objs, fr[f], foot)[1:3] for f in (1, 2, 3)]
        if cache:
            pickle.dump((ground, objs, cells, fr, foot, why, doors, walled, pic, bot, top, layer, conflicts, frame_split), open(cache, 'wb'))
    anim = [i for i, o in enumerate(objs) if o['fam'] in ('fountain', 'blossom_pool')]
    # the fountains' tiles: every 8x8 tile a fountain or blossom pool touches, in every frame
    anim_tiles = set()
    for i in anim:
        m = object_mask(objs[i]).reshape(H * 2, 8, W * 2, 8).any(axis=(1, 3))
        anim_tiles |= {(int(tx), int(ty)) for ty, tx in zip(*np.nonzero(m))}

    # jobs: one per tile layer, its pixels, mask and family
    jobs, where = [], {}
    def job(px, mask, fam, key, animated=False):
        cols = colour_set(px, mask)
        j = dict(px=rgb5(px), mask=mask, fam=fam, cols=cols, key=key, animated=animated)
        if len(cols) > 15:
            raise SystemExit(f'tile layer {key} holds {len(cols)} colours')
        jobs.append(j); where[key] = j
        return j
    in_tile = defaultdict(set)                                 # per 8x8 tile, every object with pixels in it
    for i, o in enumerate(objs):
        m = object_mask(o).reshape(H * 2, 8, W * 2, 8).any(axis=(1, 3))
        for ty, tx in zip(*np.nonzero(m)):
            in_tile[(tx, ty)].add(i)
    for (tx, ty), px in bot.items():
        if px is None:
            continue
        t = top.get((tx, ty))
        behind = in_tile[(tx, ty)] - (set(t[3]) if t else set())
        fam = '+'.join(['ground'] + sorted({objs[i]['fam'] for i in behind}))
        job(px, None, fam, (tx, ty, 0), (tx, ty) in anim_tiles)
    for (tx, ty), (px, m, F, _) in top.items():
        job(px, m, objs[F]['fam'], (tx, ty, 1), (tx, ty) in anim_tiles)
    # animated tiles: each frame's tile layers share their frame-0 palette, so the union goes in
    for f in (1, 2, 3):
        b2, t2 = frame_split[f]
        for (tx, ty) in anim_tiles:
            for l, src in ((0, b2), (1, t2)):
                v = src.get((tx, ty))
                j = where.get((tx, ty, l))
                if v is None or j is None:
                    if (v is None) != (j is None):
                        raise SystemExit(f'fountain tile {tx},{ty} layer {l} changes shape in frame {f}')
                    continue
                px, m = (v, None) if l == 0 else (v[0], v[1])
                j.setdefault('frames', {})[f] = (rgb5(px), m)
                j['cols'] = j['cols'] | colour_set(px, m)
    if JOB_HOOK is not None:
        JOB_HOOK(jobs)
    pals, lossy = pack_palettes(jobs)
    pal_arr = [np.array(p, int) for p in pals]

    # glyphs: index patterns, deduped with flips; glyph 0 is the clear tile
    glyphs, gid = [np.zeros((8, 8), np.uint8)], {np.zeros((8, 8), np.uint8).tobytes(): 0}
    def encode(px5, mask, pal):
        d = (((px5.reshape(-1, 1, 3).astype(int) - pal_arr[pal][None]) ** 2) * B.CH_W).sum(-1)
        ix = (d.argmin(1) + 1).reshape(8, 8).astype(np.uint8)
        if mask is not None:
            ix[~mask] = 0
        return ix
    def intern(ix):
        vs = flips(ix)
        for o, v in enumerate(vs):
            k = v.tobytes()
            if k in gid:
                return gid[k], o
        gid[ix.tobytes()] = len(glyphs); glyphs.append(ix)
        return len(glyphs) - 1, 0
    anim_glyphs = []                                           # pinned: [frame0 glyph slot, frames 0-3 patterns]
    for j in jobs:
        ix = encode(j['px'], j['mask'], j['pal'])
        if j['animated']:
            seq = [ix] + [encode(j['frames'][f][0], j['frames'][f][1], j['pal']) for f in (1, 2, 3)]
            if all((s == ix).all() for s in seq):
                j['glyph'], j['flip'] = intern(ix)
            else:
                j['glyph'], j['flip'] = -1 - len(anim_glyphs), 0
                anim_glyphs.append(seq)
        else:
            j['glyph'], j['flip'] = intern(ix)
    n_static = len(glyphs)
    # pinned glyphs sit after the static ones; the engine keeps them in fixed slots
    for j in jobs:
        if j['glyph'] < 0:
            j['glyph'] = n_static + (-1 - j['glyph'])
    all_glyphs = glyphs + [seq[0] for seq in anim_glyphs]
    anim_frames = np.array([[seq[f] for seq in anim_glyphs] for f in range(4)], np.uint8).reshape(4, -1, 8, 8)

    # entries: per cell, bottom then top quadrants (TL, TR, BL, BR), glyph | flips << 16 | palette << 24
    entries = np.zeros((H, W, 8), np.uint32)
    for y in range(H):
        for x in range(W):
            for li in range(8):
                l, q = li // 4, li % 4
                k = (2 * x + q % 2, 2 * y + q // 2, l)
                j = where.get(k)
                if j is None:
                    continue
                entries[y, x, li] = j['glyph'] | (j['flip'] << 16) | (j['pal'] << 24)

    # glyph views: every 16 x 16 cell buffer the camera can hold, the map's margin included
    src = {(x, y): outside(x, y) for x in range(-MARGIN - 2, W + MARGIN + 2) for y in range(-MARGIN - 2, H + MARGIN + 2)}
    pinned = len(anim_glyphs)
    cell_glyphs = [[{int(v) & 0xFFFF for v in entries[y, x] if 0 < (int(v) & 0xFFFF) < n_static} for x in range(W)] for y in range(H)]
    cell_pals = [[{int(v) >> 24 for v in entries[y, x] if int(v) & 0xFFFF or int(v) >> 24} for x in range(W)] for y in range(H)]
    worst_glyphs, worst_at = 0, None
    for vy in range(-MARGIN, H + MARGIN - VIEW + 1):
        for vx in range(-MARGIN, W + MARGIN - VIEW + 1):
            gl = set()
            for y in range(vy, vy + VIEW):
                for x in range(vx, vx + VIEW):
                    sx, sy = src[(x, y)]
                    gl |= cell_glyphs[sy][sx]
            if len(gl) > worst_glyphs:
                worst_glyphs, worst_at = len(gl), (vx, vy)
    # palette views: what the screen shows around each player cell (SCREEN), and on every
    # step the union of the window left and the window entered; the engine loads a step's
    # palettes when the step begins (CeladonViewStep)
    def window(px, py):
        out = set()
        for y in range(py - SCREEN[2], py + SCREEN[3] + 1):
            for x in range(px - SCREEN[0], px + SCREEN[1] + 1):
                sx, sy = src[(x, y)]
                out |= cell_pals[sy][sx]
        return out
    win = {(x, y): window(x, y) for x in range(W) for y in range(H)}
    pal_conflict = defaultdict(set)
    worst_pals, worst_pal_at = 0, None
    over = []
    step_pals = {}
    for (x, y), a in win.items():
        for dx, dy in ((0, 0), (1, 0), (0, 1)):
            b = win.get((x + dx, y + dy))
            if b is None:
                continue
            u = a | b
            if len(u) > worst_pals:
                worst_pals, worst_pal_at = len(u), (x, y, dx, dy)
            if len(u) > BANKS:
                over.append((len(u), x, y, dx, dy, tuple(sorted(u))))
            for p in u:
                pal_conflict[p] |= u - {p}
    # banks: colour the palettes so no two in one view share a bank (largest degree first)
    bank = colour_banks(pal_conflict, range(len(pals)))
    if bank is None:
        bank = {p: -1 for p in range(len(pals))}
    unbanked = [p for p, b in bank.items() if b < 0]

    # the native decode: what the engine will draw (bottom, then the top's opaque pixels)
    pal_rgb = np.zeros((len(pals), 16, 3), np.uint8)
    for n, p in enumerate(pals):
        for i, c in enumerate(p):
            pal_rgb[n, i + 1] = [(v << 3) | (v >> 2) for v in c]
    native = np.zeros((H * 16, W * 16, 3), np.uint8)
    for y in range(H):
        for x in range(W):
            for li in range(8):
                e = int(entries[y, x, li])
                g, f, p = e & 0xFFFF, (e >> 16) & 3, e >> 24
                ix = all_glyphs[g]
                if f & 1: ix = ix[:, ::-1]
                if f & 2: ix = ix[::-1]
                q = li % 4
                oy, ox = y * 16 + (q // 2) * 8, x * 16 + (q % 2) * 8
                m = ix > 0 if li >= 4 else np.ones((8, 8), bool)
                if li < 4 and g == 0 and where.get((2 * x + q % 2, 2 * y + q // 2, 0)) is None:
                    continue
                native[oy:oy + 8, ox:ox + 8][m] = pal_rgb[p][ix[m]]
    d5 = np.abs(rgb5(native).astype(int) - rgb5(pic).astype(int)).max(-1)
    Image.fromarray(native).save(OUT / 'native.png')

    behav = dict(open='MB_NORMAL', blocked='MB_NORMAL', water='MB_POND_WATER', door='MB_NON_ANIMATED_DOOR')
    tv = np.zeros((H, W, 3), np.uint8)
    colours = dict(open=(120, 200, 120), blocked=(90, 60, 60), water=(60, 90, 200), door=(250, 220, 60))
    for y in range(H):
        for x in range(W):
            tv[y, x] = colours.get(foot[y, x], (230, 200, 90))       # a route's tall grass, ledges, arrow warps
            if layer[y, x] == NORMAL:
                tv[y, x] = (200, 250, 200)
    Image.fromarray(tv).resize((W * 8, H * 8), Image.Resampling.NEAREST).save(OUT / 'traversal.png')

    walk_behind = {}                                           # per object, one walkable cell it draws over the player in
    for y in range(H):
        for x in range(W):
            if layer[y, x] != NORMAL:
                continue
            for q in range(4):
                t = top.get((2 * x + q % 2, 2 * y + q // 2))
                if t is not None and objs[t[2]]['base'] > y:
                    walk_behind.setdefault(objs[t[2]]['name'], [x, y])
    palette_group_names = [None] * len(pals)
    for j in jobs:
        palette_group_names[j['pal']] = j['palette_group']
    report = dict(
        glyphs_static=n_static, glyphs_pinned=pinned, glyph_slots=SLOTS, worst_view_glyphs=worst_glyphs, worst_view_at=worst_at,
        worst_view_budget=SLOTS - 1 - pinned, palettes=len(pals), worst_step_palettes=worst_pals, worst_step_at=worst_pal_at, banks=BANKS,
        unbanked_palettes=unbanked, tile_layers=len(jobs), colours=len({c for p in pals for c in p}), groups=lossy,
        exact_pixels=int((d5 == 0).sum()), pixels=int(d5.size), worst_rgb5_error=int(d5.max()),
        doors={k: list(v) for k, v in doors.items()}, walled_in_cells=walled, depth_conflicts=conflicts, walk_behind=walk_behind,
        palette_groups=palette_group_names)
    (OUT / 'stream.json').write_text(json.dumps(report, indent=1) + '\n')
    screens = np.full((H, W, 14), 0xFF, np.uint8)               # per player cell: the palettes its screen shows
    for (x, y), u in win.items():
        u = sorted(u)
        screens[y, x, :len(u)] = u
    np.savez_compressed(NPZ, glyphs=np.array(all_glyphs, np.uint8), anim_frames=anim_frames, screens=screens,
                        entries=entries, layers=layer, palettes=pal_rgb, banks=np.array([bank.get(p, 0) % 256 for p in range(len(pals))], np.uint8),
                        foot=foot, why=why, n_static=n_static)
    print(json.dumps({k: v for k, v in report.items() if k not in ('palette_groups', 'depth_conflicts', 'groups')}))
    for g, v in lossy.items():
        print(' ', g, v)
    print('depth conflicts', len(conflicts), conflicts[:8])
    pg = [None] * len(pals)
    for j in jobs:
        pg[j['pal']] = j['palette_group']
    import collections
    print('steps over', len(over))
    seen = set()
    for n, x, y, dx, dy, u in sorted(over, reverse=True):
        if u in seen:
            continue
        seen.add(u)
        print(n, (x, y, dx, dy), dict(collections.Counter(pg[p] for p in u)))
        if len(seen) > 8:
            break

if __name__ == '__main__':
    main()
