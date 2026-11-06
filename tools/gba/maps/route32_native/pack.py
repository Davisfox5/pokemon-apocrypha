"""Route 32: exact native pack onto its own primary and secondary, traversal from the decoded HGSS
permissions, layer types, events, and installation into the engine checkout (Route 30's pack.py, for
Route 32).

    python3 tools/gba/maps/route32_native/pack.py ENGINE_CHECKOUT [--install]

Route 32 (`JohtoRoute32`, 32 x 166) joins Violet City (north, offset -VIOLET_SHIFT). Violet is on its own
primary (VioletCityPrimary); the engine reloads a primary and redraws the view on a crossing (PR #39), so
Route 32 takes a primary of its own (`route32`) and a secondary (`route32_hgss`): 1024 tile slots and 1024
metatile ids, the route's art in banks 0-12.
A Gen 3 map draws a connected map's nearest rows with its own tilesets, so:
  * padding rows 0-4 (reference.py) are Violet's own metatiles placed by id: Violet draws them as itself;
  * every Violet metatile those rows use, and every one a player on Route 32 can see in Violet (its rows
    66-71, the camera's 8 columns either side of the walkable padding), is defined in Route 32's tilesets at
    the same id with Violet's tiles, in banks that take Violet's palettes (VIOLET_BANKS);
  * seams.py checks both directions.
Everything else packs exactly (Mahogany's lossless rule): every native pixel keeps its assembled RGB555
colour.

Traversal (source/trace/ledger.json, decoded HGSS permissions): woods under a tree root, rock, buildings,
signs, boulders, ledge ends and HGSS's blocked sea (under the viaduct) blocked (collision 1, elevation 0 as
vanilla); jump-south and jump-east ledges MB_JUMP_SOUTH / MB_JUMP_EAST; the sea MB_OCEAN_WATER (collision 0,
elevation 1); the pier, stairs and everything else open land; tall grass MB_TALL_GRASS; the Center door a
warp into Route 32's Center. Declared adaptations: woods cells under a crown stay solid, as HGSS has them;
the Ruins of Alph gatehouse doorway and the Union Cave mouth stay shut (no gatehouse interior or Union Cave
on this branch); the Center door is a non-animated door (no door animation registered for these tilesets).
"""
from __future__ import annotations
import json, re, shutil, struct, subprocess, sys
from collections import Counter, deque
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import reference as Rf                               # noqa: E402
from reference import W, H, PX, COL0, ROW0          # noqa: E402
from tiles import Tileset                            # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route32-native'
SRC, EV = ART / 'source', ART / 'evidence'
OUT, OEV = SRC / 'pack', EV / 'pack'
MAP, LAYOUT, MAP_ID = 'JohtoRoute32', 'LAYOUT_JOHTO_ROUTE32', 'MAP_JOHTO_ROUTE32'
CENTER, UPSTAIRS = 'Route32PokemonCenter', 'Route32CenterUpstairs'
PRI_NAME, PRI_SYM = 'route32', 'Route32Primary'
TS_NAME, TS_SYM = 'route32_hgss', 'Route32Hgss'
VIOLET_BANKS = (0, 1, 3, 11)         # the banks Violet's pinned metatiles draw in: Route 32 takes Violet's palettes there
VIOLET_SEEN_ROWS = range(66, 72)     # Violet rows a player on Route 32's padding can see
COVERED, NORMAL = 1, 0
# The two 21-colour masters (G02, C06) are drawn across both layers where the player never walks in front of
# them: their SPLIT_N least common colours go in the bottom tile (over the ground), the rest in the top tile, so
# each master's top tiles fit one palette. The picture is the same pixel for pixel.
SPLIT = ('gate_alph', 'pokemon_center')
SPLIT_N = 6
COUNT_ONLY = '--count' in sys.argv
ITEMS = dict(repel=('FLAG_ITEM_APOC_ROUTE32_REPEL', 'FLAG_UNUSED_0x26A', 'ITEM_REPEL', 'FLAG_HIDE_ITEMBALL_R32_REPEL'),
             great_ball=('FLAG_ITEM_APOC_ROUTE32_GREAT_BALL', 'FLAG_UNUSED_0x26B', 'ITEM_GREAT_BALL', 'FLAG_HIDE_ITEMBALL_R32_GREAT_BALL'),
             shell_bell=('FLAG_ITEM_APOC_ROUTE32_SHELL_BELL', 'FLAG_UNUSED_0x26C', 'ITEM_SHELL_BELL', 'FLAG_HIDE_ITEMBALL_R32_SHELL_BELL'),
             heart_scale=('FLAG_HIDDEN_ITEM_APOC_ROUTE32_HEART_SCALE', 'FLAG_UNUSED_0x26D', 'ITEM_HEART_SCALE', 'std_hiddenitem_r32_heart_scale'),
             hidden_great_ball=('FLAG_HIDDEN_ITEM_APOC_ROUTE32_GREAT_BALL', 'FLAG_UNUSED_0x26E', 'ITEM_GREAT_BALL', 'std_hiddenitem_r32_great_ball'),
             super_potion=('FLAG_HIDDEN_ITEM_APOC_ROUTE32_SUPER_POTION', 'FLAG_UNUSED_0x26F', 'ITEM_SUPER_POTION', 'std_hiddenitem_r32_super_potion'))
SIGN_SCRIPTS = {'Ruins of Alph': 'JohtoRoute32_AlphSign', 'Azalea': 'JohtoRoute32_RouteSign', 'Union Cave': 'JohtoRoute32_CaveSign'}

def rgb5(a): return (np.asarray(a).astype(np.int32) >> 3)
def entry(tile, flip, bank): return tile | ((flip & 1) << 10) | ((flip >> 1) << 11) | (bank << 12)

# --------------------------------------------------------------------------- engine data
def behaviors(engine):
    names = re.findall(r'^\s+(MB_[A-Z0-9_]+),', (engine / 'include/constants/metatile_behaviors.h').read_text(), re.M)
    return {n: i for i, n in enumerate(names)}

class Violet:
    """Violet City's tilesets and map: every metatile's entries, attributes and tiles (index maps)."""
    def __init__(self, engine):
        t = Tileset(engine, 'violet_city', 'violet_city')
        self.t = t
        self.tiles = [[np.array(x, np.uint8).reshape(8, 8) & 15 for x in t.tiles[k]] for k in (0, 1)]
        self.pals = [[tuple(c) for c in p] for p in t.pals[0][:6]] + [[tuple(c) for c in p] for p in t.pals[1][6:16]]
        self.meta = [tuple(int(e) for e in m) for m in t.blocks[0]] + [tuple(int(e) for e in m) for m in t.blocks[1]]
        self.attrs = list(t.attrs[0]) + list(t.attrs[1])
        b = (engine / 'data/layouts/VioletCity/map.bin').read_bytes()
        self.words = np.array(struct.unpack('<%dH' % (len(b) // 2), b)).reshape(-1, 80)
    def tile(self, i):
        return self.tiles[0][i] if i < 512 else self.tiles[1][i - 512]

def pinned_ids(V):
    """Violet metatile ids Route 32 must define as Violet does: the padding's (rows 0-4, by id) and those a
    player on the padding's road can see in Violet (its rows 66-71, 8 columns either side)."""
    ids = set()
    for y in range(Rf.VIOLET_ID_ROWS):
        for x in range(W):
            vx, vy = Rf.pad_source(x, y)
            ids.add(int(V.words[vy, vx]) & 1023)
    for vy in VIOLET_SEEN_ROWS:
        for x in range(min(Rf.VIOLET_ROAD) - 8, max(Rf.VIOLET_ROAD) + 9):
            vx = x + Rf.VIOLET_SHIFT
            if 0 <= vx < V.words.shape[1]:
                ids.add(int(V.words[vy, vx]) & 1023)
    return sorted(ids)

# --------------------------------------------------------------------------- traversal
def traversal(engine, grid, cells, V):
    MB = behaviors(engine)
    out = np.empty((H, W), object)
    for y in range(H):
        for x in range(W):
            ch = grid[y][x]
            hx, hz = Rf.to_hgss(x, y)
            c = dict(x=x, y=y, code=ch)
            if hz >= 0:
                c['hgss'] = dict(type=cells[hz][hx]['type'], collision=cells[hz][hx]['collision'], label=cells[hz][hx]['lab'])
            if ch in 'Pp' or (ch == 'v'):
                vx, vy = Rf.pad_source(x, y)
                v = int(V.words[vy, vx])
                c.update(foot='open' if (v >> 10) & 3 == 0 else 'blocked', behavior=None, collision=(v >> 10) & 3,
                         elevation=v >> 12, metatile=v & 1023, source=f'Violet ({vx},{vy})')
                if ch == 'v' or y >= Rf.VIOLET_ID_ROWS:          # row 5 is route art (lawn, the road's end cap)
                    c.update(behavior='MB_NORMAL', metatile=None)
            elif ch == 'L':
                c.update(foot='ledge_south', behavior='MB_JUMP_SOUTH', collision=1, elevation=0)
            elif ch == 'E':
                c.update(foot='ledge_east', behavior='MB_JUMP_EAST', collision=1, elevation=0)
            elif ch == 'Q':
                c.update(foot='ledge_west', behavior='MB_JUMP_WEST', collision=1, elevation=0)
            elif ch == '~':
                c.update(foot='water', behavior='MB_OCEAN_WATER', collision=0, elevation=1)
            elif ch == 'X' and hz >= 0 and cells[hz][hx]['material'].startswith('sea'):
                c.update(foot='blocked', behavior='MB_OCEAN_WATER', collision=1, elevation=1, note="HGSS's blocked sea under the viaduct")
            elif ch == 'O' and hz >= 0 and cells[hz][hx]['material'].startswith('sea'):
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=1, note='sea boulder')
            elif ch == 'D':
                c.update(foot='door', behavior='MB_NON_ANIMATED_DOOR', collision=0, elevation=3,
                         adaptation='non-animated door: no door animation is registered for these tilesets')
            elif ch == 'w':
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=0,
                         adaptation="HGSS's Ruins of Alph gatehouse doorway; no gatehouse interior exists yet, so it stays shut")
            elif ch == 'C':
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=0,
                         adaptation="HGSS's Union Cave mouth; Union Cave is not on this branch, so it stays shut")
            elif ch in 'tkoRHsJXOc':
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=0)
            elif ch == 'G':
                c.update(foot='open', behavior='MB_TALL_GRASS', collision=0, elevation=3)
            else:
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3)
            if ch == 'c':                              # the cuttable tree is an object on open ground
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3)
            if c['behavior']:
                c['behavior_id'] = MB[c['behavior']]
            out[y, x] = c
    return out

LEDGES = {'ledge_south': (0, 1), 'ledge_east': (1, 0), 'ledge_west': (-1, 0)}

def reach(trav, start, cut_open=False, cut=()):
    """Cells reachable on foot from start, with Gen 3 ledge rules (jump over a ledge in its direction)."""
    seen = {start}; q = deque([start])
    walk = lambda p: 0 <= p[0] < W and 0 <= p[1] < H and trav[p[1], p[0]]['foot'] in ('open', 'door') and (cut_open or p not in cut)
    while q:
        x, y = q.popleft()
        if trav[y, x]['foot'] == 'door':
            continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if not (0 <= n[0] < W and 0 <= n[1] < H):
                continue
            f = trav[n[1], n[0]]['foot']
            if f in LEDGES and LEDGES[f] == (dx, dy):
                n = (n[0] + dx, n[1] + dy)
            if walk(n) and n not in seen:
                seen.add(n); q.append(n)
    return seen

def hgss_reach(cells, start):
    """The same search on HGSS's own permissions (HGSS frame); water, doors and warps are not walked."""
    types = {0x3B: (0, 1), 0x38: (1, 0), 0x39: (-1, 0)}
    open_ = lambda hx, hz: (0 <= hx < Rf.HW and 0 <= hz < Rf.HH and not cells[hz][hx]['blocked']
                            and cells[hz][hx]['type'] not in (0x10, 0x15, 0x69, 0x6D, 0x6E))
    seen = {start}; q = deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if not (0 <= n[0] < Rf.HW and 0 <= n[1] < Rf.HH):
                continue
            t = cells[n[1]][n[0]]['type']
            if t in types and types[t] == (dx, dy):
                n = (n[0] + dx, n[1] + dy)
            if open_(*n) and n not in seen:
                seen.add(n); q.append(n)
    return seen

# --------------------------------------------------------------------------- layer types
def above_player(trav, top, owner):
    """Walkable cells whose object art belongs to something standing further south draw above the player
    (Route 43's rule); every cell under the viaduct does too, walkable or water."""
    art = top[..., 3] > 0
    base = {}
    for name in set(owner[art].ravel().tolist()) - {''}:
        base[name] = int(np.nonzero((owner == name).any(1))[0].max()) // 16
    out = np.zeros((H, W), bool)
    for y in range(H):
        for x in range(W):
            sl = np.s_[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
            a = art[sl]
            if not a.any():
                continue
            names = set(owner[sl][a].ravel().tolist()) - {''}
            if 'viaduct' in names:
                out[y, x] = True
                continue
            if trav[y, x]['foot'] not in ('open', 'door') or trav[y, x]['code'] in 'Pp':
                continue
            out[y, x] = any(base[n] > y for n in names)
    return out

# --------------------------------------------------------------------------- pack
def prepare(engine):
    z = np.load(SRC / 'assemble/layers.npz', allow_pickle=True)
    ground, flat, top, owner = z['ground'], z['flat'], z['objects'], z['owner'].astype(object)
    grid = [list(l.split()[1]) for l in (SRC / 'trace/material-grid.txt').read_text().splitlines() if l[:3].isdigit()]
    cells = json.loads((SRC / 'trace/ledger.json').read_text())['cells']
    V = Violet(engine)
    trav = traversal(engine, grid, cells, V)
    above = above_player(trav, top, owner)
    want = ground.copy()
    for layer in (flat, top):
        a = layer[..., 3] > 0; want[a] = layer[a, :3]
    placed = {(x, y): trav[y, x]['metatile'] for y in range(ROW0) for x in range(W) if trav[y, x]['metatile'] is not None}
    return dict(ground=ground, flat=flat, top=top, owner=owner, grid=grid, cells=cells, trav=trav, above=above, V=V,
                want=want, placed=placed, pins=pinned_ids(V))

def pack(engine):
    OUT.mkdir(parents=True, exist_ok=True); OEV.mkdir(parents=True, exist_ok=True)
    d = prepare(engine)
    ground, flat, top, grid, cells, trav, above, V, want, placed, pins = (d[k] for k in (
        'ground', 'flat', 'top', 'grid', 'cells', 'trav', 'above', 'V', 'want', 'placed', 'pins'))
    tiles, lookup = [np.zeros((8, 8), np.uint8)], {np.zeros((8, 8), np.uint8).tobytes(): 0}
    def add_tile(ix):
        for f in range(4):
            v = ix[:, ::-1] if f & 1 else ix
            v = v[::-1] if f & 2 else v
            if v.tobytes() in lookup:
                return lookup[v.tobytes()], f
        lookup[ix.tobytes()] = len(tiles); tiles.append(ix.copy())
        return len(tiles) - 1, 0
    # ---- Violet's pinned metatiles: Violet's tiles (index maps), Violet's banks and palettes.
    fixed_pal = {b: V.pals[b][1:16] for b in VIOLET_BANKS}
    pin_defs = {}
    for m in pins:
        ents = []
        for e in V.meta[m]:
            b = e >> 12
            assert e == 0 or b in VIOLET_BANKS, f'Violet metatile {m:#x} draws in bank {b}'
            t, f = add_tile(V.tile(e & 1023))
            fl = ((e >> 10) & 1) | (((e >> 11) & 1) << 1)
            # compose the flips: the stored tile may itself be a flip of Violet's
            ents.append(('pin', t, f ^ fl, b))
        pin_defs[m] = (ents, V.attrs[m])
    # ---- exact jobs for the rest
    jobs, cellplan = {}, {}
    def job(px, mask, layer):
        k5 = rgb5(px).astype(np.int16)
        if mask is not None:
            k5 = np.where(mask[..., None], k5, -1)
        key = (k5.tobytes(), layer)
        if key not in jobs:
            jobs[key] = dict(k5=k5, px=px.copy(), mask=None if mask is None else mask.copy(), layer=layer, n=0)
        jobs[key]['n'] += 1
        return key
    owner = d['owner']
    lower = {}
    for name in SPLIT:
        m = owner == name
        cnt = Counter(map(tuple, rgb5(top[m][:, :3]).tolist()))
        lower[name] = {c for c, _ in cnt.most_common()[::-1][:SPLIT_N]} if len(cnt) > 15 else set()
    common = Counter(ground[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].tobytes() for ty in range(2 * ROW0, H * 2) for tx in range(W * 2)).most_common(1)[0][0]
    filler = np.frombuffer(common, np.uint8).reshape(8, 8, 3)
    for y in range(H):
        for x in range(W):
            if (x, y) in placed:
                continue
            q = []
            for qi in range(4):
                sl = np.s_[y * 16 + (qi // 2) * 8:y * 16 + (qi // 2) * 8 + 8, x * 16 + (qi % 2) * 8:x * 16 + (qi % 2) * 8 + 8]
                gpx = ground[sl].copy()
                fl = flat[sl][..., 3] > 0
                upx = np.zeros((8, 8, 3), np.uint8)
                if above[y, x]:
                    gpx[fl] = flat[sl][..., :3][fl]
                    up = np.zeros((8, 8), bool)
                else:
                    upx[fl] = flat[sl][..., :3][fl]; up = fl.copy()
                ob = top[sl][..., 3] > 0
                upx[ob] = top[sl][..., :3][ob]; up |= ob
                if not above[y, x]:
                    osl = owner[sl]; t5 = rgb5(top[sl][..., :3])
                    for name, low in lower.items():
                        mv = ob & (osl == name) & np.array([[tuple(t5[i, j]) in low for j in range(8)] for i in range(8)])
                        if mv.any():
                            gpx[mv] = top[sl][..., :3][mv]; up &= ~mv
                if up.all():
                    b = job(filler, None, 0)
                else:
                    hid = up & ob
                    if hid.any():                      # hidden under standing objects: the commonest visible ground colour
                        vis = gpx[~up]
                        cols, cnt = np.unique(vis >> 3, axis=0, return_counts=True)
                        mode = vis[(vis >> 3 == cols[cnt.argmax()]).all(-1)][0]
                        gpx[hid] = mode
                    b = job(gpx, None, 0)
                t = job(upx, up, 1) if up.any() else None
                q.append((b, t))
            cellplan[(x, y)] = q
    if COUNT_ONLY:
        def fk(j):
            a = j['k5']
            return min(a.tobytes(), a[:, ::-1].tobytes(), a[::-1].tobytes(), a[::-1, ::-1].tobytes())
        n = len({fk(j) for j in jobs.values()}) + len(lookup)
        bycode = {}
        for (x, y), q in cellplan.items():
            for b, t in q:
                for k in (b, t):
                    if k is not None:
                        bycode.setdefault((grid[y][x], jobs[k]['layer']), set()).add(fk(jobs[k]))
        print(sorted(((c, l, len(v)) for (c, l), v in bycode.items()), key=lambda t: -t[2])[:16])
        raise SystemExit(f'tile count (upper bound): {n} of 1024; pinned Violet tiles {len(lookup)}')
    setof = lambda j: frozenset(map(tuple, j['k5'][j['k5'][..., 0] >= 0].reshape(-1, 3).tolist()))
    rest = list(jobs.values())
    over15 = [j for j in rest if len(setof(j)) > 15]
    assert not over15, f'{len(over15)} tiles hold more than 15 colours'
    fixed5 = {b: frozenset(tuple(int(v) >> 3 for v in c) for c in p) for b, p in fixed_pal.items()}
    free = [b for b in range(13) if b not in fixed5]
    sets = [setof(j) for j in rest]
    from banks import pack_sets, milp_sets
    # Violet's banks join the packing holding the colours the pinned Violet tiles use: route sets inside them
    # use them, and their unused slots may take route colours.
    vb = list(VIOLET_BANKS)
    used_idx = {b: set() for b in vb}
    for m in pins:
        for e in V.meta[m]:
            if e:
                used_idx[e >> 12] |= set(int(v) for v in np.unique(V.tile(e & 1023))) - {0}
    vio5 = {b: [tuple(int(v) >> 3 for v in c) for c in fixed_pal[b]] for b in vb}
    held = {b: {vio5[b][i - 1] for i in used_idx[b]} for b in vb}
    distinct = set(sets)
    maximal = sorted((c for c in distinct if not any(c < dd for dd in distinct)), key=lambda c: (-len(c), sorted(c)))
    import hashlib
    key = hashlib.sha256(repr((sorted(sorted(c) for c in maximal), [sorted(held[b]) for b in vb])).encode()).hexdigest()
    cache = OUT / 'banks-cache.json'
    packed = None
    if cache.exists() and json.loads(cache.read_text()).get('key') == key:   # the same colour sets: the same banks
        packed = [set(map(tuple, b)) for b in json.loads(cache.read_text())['banks']]
    for seed in range(8 if packed is None else 0):
        packed = pack_sets(maximal, 13, init=[set(held[b]) for b in vb], tries=400, seed=seed)
        if packed is not None:
            break
    if packed is None and '--greedy-only' in sys.argv:
        loose = pack_sets(maximal, 60, init=[set(held[b]) for b in vb], tries=50)
        import pickle; (OUT / 'sets-debug.pkl').write_bytes(pickle.dumps(dict(maximal=maximal, held=held, loose=loose)))
        raise SystemExit(f'greedy packer gave up on {len(maximal)} sets, needs {len(loose)} (the exact program runs without --greedy-only)')
    if packed is None:                                    # the greedy packer gave up: Route 43's exact program
        sets_ = list(maximal) + [frozenset(held[b]) for b in vb]
        pins = [(len(maximal) + i, i) for i in range(len(vb))]   # Violet's sets in their own banks
        res = milp_sets(sets_, 13, fixed=pins, time_limit=3600)
        if res is not None:
            packed = [set(b) for b in res]
    if packed is None:
        loose = pack_sets(maximal, 60, init=[set(held[b]) for b in vb], tries=50)
        import pickle; (OUT / 'sets-debug.pkl').write_bytes(pickle.dumps(dict(maximal=maximal, held=held, loose=loose)))
        raise SystemExit(f'route art does not fit 13 banks: {len(maximal)} sets; greedy needs {len(loose) if loose else None}')
    cache.write_text(json.dumps(dict(key=key, banks=[sorted(b) for b in packed])) + '\n')
    pal5 = {b: frozenset(packed[i]) for i, b in enumerate(vb)}
    for b, st in zip(free, packed[len(vb):]):
        pal5[b] = frozenset(st)
    order5 = {b: sorted(st) for b, st in pal5.items()}
    for b in vb:                                          # Violet's used slots stay; route colours take the others
        slots = list(vio5[b])
        open_ = [i for i in range(15) if i + 1 not in used_idx[b]]
        extra = sorted(pal5[b] - held[b])
        assert len(extra) <= len(open_), ('Violet bank over full', b)
        for i, c in zip(open_, extra):
            slots[i] = c
        order5[b] = slots
        fixed_pal[b] = [tuple(v << 3 for v in c) for c in slots]
    inside = lambda st: next((b for b in list(vb) + free if b in pal5 and st <= pal5[b]), None)
    for j, s in zip(rest, sets):
        b = inside(s)
        idx = {}
        for i, c in enumerate(order5[b]):
            idx.setdefault(c, i + 1)
        k5 = j['k5']
        ix = np.zeros((8, 8), np.uint8)
        m = k5[..., 0] >= 0
        ix[m] = [idx[tuple(c)] for c in k5[m].reshape(-1, 3).tolist()]
        t, f = add_tile(ix)
        j['tile'] = (t, f, b)
    assert len(tiles) <= 1024, ('tiles over the two tilesets', len(tiles))
    final = lambda t: t                                   # tile t < 512 in the primary, else secondary 512 + (t - 512)
    for j in jobs.values():
        t, f, b = j['tile']
        j['entry'] = entry(final(t), f, b)
    pin_meta = {m: (tuple(entry(final(t), f, b) if kind == 'pin' else 0 for kind, t, f, b in ents), attr)
                for m, (ents, attr) in pin_defs.items()}
    for m, (ents, attr) in pin_defs.items():                # Violet's empty entries stay 0
        pin_meta[m] = (tuple(0 if V.meta[m][i] == 0 else pin_meta[m][0][i] for i in range(8)), attr)
    # ---- metatiles: pinned ids first, then the route's cells in the free ids (primary 1-511, secondary 512-1023)
    meta = dict(pin_meta)
    by_def = {v: k for k, v in pin_meta.items()}
    free_ids = [i for i in list(range(1, 512)) + list(range(512, 1024)) if i not in meta]
    nxt = iter(free_ids)
    def meta_id(key):
        if key not in by_def:
            i = next(nxt)
            by_def[key] = i; meta[i] = key
        return by_def[key]
    words = np.zeros((H, W), np.uint16)
    for y in range(H):
        for x in range(W):
            c = trav[y, x]
            if (x, y) in placed:
                mid = placed[(x, y)]
            else:
                bot = [jobs[b]['entry'] for b, _ in cellplan[(x, y)]]
                tp = [jobs[t]['entry'] if t else 0 for _, t in cellplan[(x, y)]]
                layer = NORMAL if above[y, x] else COVERED
                mid = meta_id((tuple(bot + tp), c['behavior_id'] | (layer << 12)))
            c['metatile'] = mid
            words[y, x] = mid | (c['collision'] << 10) | (c['elevation'] << 12)
    pals = {b: [tuple(v << 3 for v in c) for c in order5[b]] for b in order5}
    for b in fixed_pal:
        pals[b] = list(fixed_pal[b])
    n_pri = 1 + max([i for i in meta if i < 512] + [0]); n_sec = max([i - 511 for i in meta if i >= 512] + [0])
    return dict(words=words, trav=trav, tiles=tiles, pals=pals, meta=meta, n_pri_meta=n_pri, n_sec_meta=n_sec, pins=pins,
                n_jobs=len(jobs), want=want, grid=grid, cells=cells, above=above, maximal_sets=len(maximal), violet_pals=fixed_pal)

# --------------------------------------------------------------------------- write
def jasc(cols):
    cols = list(cols) + [(0, 0, 0)] * (15 - len(cols))
    return '\r\n'.join(['JASC-PAL', '0100', '16', '0 0 0'] + [f'{c[0]} {c[1]} {c[2]}' for c in cols[:15]]) + '\r\n'

def write_tilesets(engine, r):
    for kind, name, lo, hi, banks in (('primary', PRI_NAME, 0, 512, range(0, 6)), ('secondary', TS_NAME, 512, 1024, range(6, 13))):
        d = engine / 'data/tilesets' / kind / name
        (d / 'palettes').mkdir(parents=True, exist_ok=True)
        tl = r['tiles'][lo:hi]
        if kind == 'primary':
            tl = tl + [np.zeros((8, 8), np.uint8)] * (512 - len(tl))
        rows = max(1, (len(tl) + 15) // 16)
        sheet = np.zeros((rows * 8, 128), np.uint8)
        for i, t in enumerate(tl):
            sheet[(i // 16) * 8:(i // 16) * 8 + 8, (i % 16) * 8:(i % 16) * 8 + 8] = t
        im = Image.fromarray(sheet, 'P'); im.putpalette([v for i in range(16) for v in (i * 17, i * 17, i * 17)] + [0] * 720)
        im.save(d / 'tiles.png', bits=4)
        for b in range(16):
            (d / 'palettes' / f'{b:02}.pal').write_text(jasc(r['pals'].get(b, []) if b in banks else []))
        ids = range(0, 512) if kind == 'primary' else range(512, 512 + r['n_sec_meta'])
        rows_ = [r['meta'].get(i, (tuple([0] * 8), 0)) for i in ids]
        (d / 'metatiles.bin').write_bytes(b''.join(struct.pack('<8H', *k[0]) for k in rows_))
        (d / 'metatile_attributes.bin').write_bytes(struct.pack('<%dH' % len(rows_), *[k[1] for k in rows_]))

def register(engine):
    h = engine / 'src/data/tilesets/headers.h'; s = h.read_text()
    for sym, sec in ((PRI_SYM, 'FALSE'), (TS_SYM, 'TRUE')):
        if f'gTileset_{sym} =' not in s:
            s = s.rstrip('\n') + f'\n\nconst struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, .isSecondary = {sec}, .tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym}, .metatiles = gMetatiles_{sym}, .metatileAttributes = gMetatileAttributes_{sym}, .callback = NULL }};\n'
    h.write_text(s)
    g = engine / 'src/data/tilesets/graphics.h'; s = g.read_text()
    for sym, kind, name in ((PRI_SYM, 'primary', PRI_NAME), (TS_SYM, 'secondary', TS_NAME)):
        if f'gTilesetTiles_{sym}[]' not in s:
            s = s.rstrip('\n') + f'\n\nconst u32 gTilesetTiles_{sym}[] = INCGFX_U32("data/tilesets/{kind}/{name}/tiles.png", ".4bpp.fastSmol");\nconst u16 gTilesetPalettes_{sym}[][16] = {{\n' + ''.join(f'INCGFX_U16("data/tilesets/{kind}/{name}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n'
    g.write_text(s)
    m = engine / 'src/data/tilesets/metatiles.h'; s = m.read_text()
    for sym, kind, name in ((PRI_SYM, 'primary', PRI_NAME), (TS_SYM, 'secondary', TS_NAME)):
        if f'gMetatiles_{sym}[]' not in s:
            s = s.rstrip('\n') + f'\nconst u16 gMetatiles_{sym}[] = INCBIN_U16("data/tilesets/{kind}/{name}/metatiles.bin");\nconst u16 gMetatileAttributes_{sym}[] = INCBIN_U16("data/tilesets/{kind}/{name}/metatile_attributes.bin");\n'
    m.write_text(s)

def write_flags(engine):
    f = engine / 'include/constants/flags.h'; s = f.read_text()
    anchor = next(l for l in s.splitlines() if l.startswith('#define FLAG_ITEM_APOC_ROUTE31_POTION'))
    add = [f'#define {name} {slot} // Route 32: {item} (HGSS {"hidden item" if "HIDDEN" in name else "item ball"}; not yet in JOHTO_ITEMS.md)'
           for name, slot, item, _ in ITEMS.values() if f'#define {name} ' not in s]
    if add:
        s = s.replace(anchor, anchor + '\n' + '\n'.join(add), 1); f.write_text(s)

def write_mapsec(engine):
    j = engine / 'src/data/region_map/region_map_sections.json'; d = json.loads(j.read_text())
    if not any(m['id'] == 'MAPSEC_JOHTO_ROUTE_32' for m in d['map_sections']):
        i = next(k for k, m in enumerate(d['map_sections']) if m['id'] == 'MAPSEC_JOHTO_ROUTE_36')
        d['map_sections'].insert(i + 1, dict(id='MAPSEC_JOHTO_ROUTE_32', name='ROUTE 32', x=2, y=5, width=1, height=1))
        j.write_text(json.dumps(d, indent=2) + '\n')

SCRIPTS = '''JohtoRoute32_MapScripts::
    .byte 0

JohtoRoute32_AlphSign::
    msgbox JohtoRoute32_AlphSign_Text, MSGBOX_SIGN
    end

JohtoRoute32_AlphSign_Text:
    .string "RUINS OF ALPH\\nEAST ENTRANCE$"

JohtoRoute32_RouteSign::
    msgbox JohtoRoute32_RouteSign_Text, MSGBOX_SIGN
    end

JohtoRoute32_RouteSign_Text:
    .string "ROUTE 32\\n"
    .string "VIOLET CITY - AZALEA TOWN$"

JohtoRoute32_CaveSign::
    msgbox JohtoRoute32_CaveSign_Text, MSGBOX_SIGN
    end

JohtoRoute32_CaveSign_Text:
    .string "UNION CAVE\\nAHEAD$"
'''

def base_map(engine, name, src):
    return json.loads((engine / f'data/maps/{src}/map.json').read_text())

def write_center(engine):
    """Route 32's Center and its upstairs: Violet's, retargeted (the shared Center interior)."""
    for name, src in ((CENTER, 'VioletPokemonCenter'), (UPSTAIRS, 'VioletCenterUpstairs')):
        d = engine / 'data/maps' / name
        d.mkdir(parents=True, exist_ok=True)
        m = base_map(engine, name, src)
        up = lambda s: re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', s).upper()
        m['id'] = 'MAP_' + up(name); m['name'] = name; m['region_map_section'] = 'MAPSEC_JOHTO_ROUTE_32'
        for w in m['warp_events']:
            if w['dest_map'] == 'MAP_VIOLET_CITY':
                w['dest_map'], w['dest_warp_id'] = MAP_ID, '0'
            elif w['dest_map'] == 'MAP_VIOLET_CENTER_UPSTAIRS':
                w['dest_map'] = 'MAP_' + up(UPSTAIRS)
            elif w['dest_map'] == 'MAP_VIOLET_POKEMON_CENTER':
                w['dest_map'] = 'MAP_' + up(CENTER)
        txt = (engine / f'data/maps/{src}/scripts.inc').read_text().replace(src, name)
        for o in m.get('object_events', []):
            if isinstance(o.get('script'), str):
                o['script'] = o['script'].replace(src, name)
        (d / 'map.json').write_text(json.dumps(m, indent=2) + '\n')
        (d / 'scripts.inc').write_text(txt)

def register_maps(engine):
    g = engine / 'data/maps/map_groups.json'; d = json.loads(g.read_text())
    grp = next(k for k, v in d.items() if isinstance(v, list) and 'VioletCity' in v)
    for n in (MAP, CENTER, UPSTAIRS):
        if n not in d[grp]:
            d[grp].append(n)
    g.write_text(json.dumps(d, indent=2) + '\n')
    lj = engine / 'data/layouts/layouts.json'; L = json.loads(lj.read_text())
    L['layouts'] = [l for l in L['layouts'] if l.get('id') != LAYOUT]
    if True:
        L['layouts'].append(dict(id=LAYOUT, name=f'{MAP}_Layout', width=W + PADL + PADR, height=H, primary_tileset='gTileset_' + PRI_SYM,
                                 secondary_tileset='gTileset_' + TS_SYM, border_filepath=f'data/layouts/{MAP}/border.bin',
                                 blockdata_filepath=f'data/layouts/{MAP}/map.bin'))
    lj.write_text(json.dumps(L, indent=2) + '\n')
    es = engine / 'data/event_scripts.s'; t = es.read_text()
    anchor = '.include "data/maps/VioletHouse5/scripts.inc"\n'
    for n in (MAP, CENTER, UPSTAIRS):
        line = f'.include "data/maps/{n}/scripts.inc"\n'
        if line not in t:
            t = t.replace(anchor, anchor + '\n' + line, 1); anchor = line
    es.write_text(t)
    pf = engine / 'src/apocrypha_map_proof.c'; t = pf.read_text()     # test-only warp list, in the group's order
    up = lambda s: 'MAP_' + re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', s).upper()
    for n in (MAP, CENTER, UPSTAIRS):
        mid = MAP_ID if n == MAP else up(n)
        if mid not in t:
            t = t.replace('};\nvoid MapProof_Boot', f', {mid}}};\nvoid MapProof_Boot', 1)
    pf.write_text(t)
    v = engine / 'data/maps/VioletCity/map.json'; M = json.loads(v.read_text())
    conns = [c for c in (M.get('connections') or []) if c['map'] != MAP_ID]
    conns.append(dict(map=MAP_ID, direction='down', offset=Rf.VIOLET_SHIFT - PADL))
    M['connections'] = conns
    v.write_text(json.dumps(M, indent=2) + '\n')

def write_map(engine, r):
    words = r['words']
    (engine / f'data/layouts/{MAP}').mkdir(parents=True, exist_ok=True)
    (engine / f'data/layouts/{MAP}/map.bin').write_bytes(struct.pack('<%dH' % words.size, *words.ravel().tolist()))
    NW = words.shape[1]
    # Border: the open sea east of the route (HGSS's EVERYWHERE), two by two at the texture's phase.
    sea = [(x, y) for y in range(ROW0, H) for x in range(NW) if r['grid'][y][x] == '~'
           and all(0 <= x + dx < NW and 0 <= y + dy < H and r['grid'][y + dy][x + dx] == '~' for dx in (-1, 0, 1) for dy in (-1, 0, 1))]
    pick = {}
    for x, y in sea:
        pick.setdefault((x % 2, y % 2), (x, y))
    border = [int(words[pick[(px, py)][1], pick[(px, py)][0]]) & 1023 | (1 << 10) | (1 << 12) for py in (0, 1) for px in (0, 1)]
    (engine / f'data/layouts/{MAP}/border.bin').write_bytes(struct.pack('<4H', *border))
    events = json.loads((SRC / 'hgss-events.json').read_text())
    bgs, moves, objs, warps = [], [], [], []
    hidden = {v[3]: v for v in ITEMS.values()}
    for s in events['signs']:
        x, y = Rf.to_map(*s['cell']); x += PADL
        if s['bg_type'] == 1:
            script = next(v for k, v in SIGN_SCRIPTS.items() if k in s['text'])
            bgs.append(dict(type='sign', x=x, y=y, elevation=0, player_facing_dir='BG_EVENT_PLAYER_FACING_ANY', script=script))
            moves.append(dict(event=script, cell=[x, y], hgss=s['cell'], text=s['text']))
        elif s['script'] in hidden:
            name, _, item, _ = hidden[s['script']]
            # Gen 3 finds a hidden item on the cell the player faces, so a blocked cell (HGSS hides the Heart Scale
            # on a rock in the sea) works as HGSS has it.
            bgs.append(dict(type='hidden_item', x=x, y=y, elevation=3, item=item, flag=name, quantity=1, underfoot=False))
            moves.append(dict(event=f'hidden {item}', cell=[x, y], hgss=s['cell'], flag=name))
    balls = {v[3]: v for v in ITEMS.values()}
    for n, o in enumerate(events['objects']):
        x, y = Rf.to_map(*o['cell']); x += PADL
        if o['sprite'] == 'SPRITE_TREE':
            objs.append(dict(graphics_id='OBJ_EVENT_GFX_CUTTABLE_TREE', x=x, y=y, elevation=3, movement_type='MOVEMENT_TYPE_LOOK_AROUND',
                             movement_range_x=0, movement_range_y=0, trainer_type='TRAINER_TYPE_NONE', trainer_sight_or_berry_tree_id='0',
                             script='EventScript_CutTree', flag='FLAG_TEMP_11'))
            moves.append(dict(event='cuttable tree', cell=[x, y], hgss=o['cell']))
        elif o['sprite'] == 'SPRITE_BREAKROCK':
            objs.append(dict(graphics_id='OBJ_EVENT_GFX_BREAKABLE_ROCK', x=x, y=y, elevation=3, movement_type='MOVEMENT_TYPE_LOOK_AROUND',
                             movement_range_x=0, movement_range_y=0, trainer_type='TRAINER_TYPE_NONE', trainer_sight_or_berry_tree_id='0',
                             script='EventScript_RockSmash', flag='FLAG_TEMP_12'))
            moves.append(dict(event='breakable rock', cell=[x, y], hgss=o['cell']))
        elif o['sprite'] == 'SPRITE_MONSTARBALL' and o['flag'] in balls:
            name, _, item, _ = balls[o['flag']]
            assert r['trav'][y, x]['foot'] == 'open', ('item ball cell is not open ground', x, y)
            objs.append(dict(graphics_id='OBJ_EVENT_GFX_ITEM_BALL', x=x, y=y, elevation=3, movement_type='MOVEMENT_TYPE_FACE_DOWN',
                             movement_range_x=0, movement_range_y=0, trainer_type='TRAINER_TYPE_NONE', trainer_sight_or_berry_tree_id=item,
                             script='Common_EventScript_FindItem', flag=name))
            moves.append(dict(event=f'item ball {item}', cell=[x, y], hgss=o['cell'], flag=name, hgss_flag=o['flag']))
        else:
            moves.append(dict(event=o['id'], hgss=o['cell'], note='not placed: trainers, NPCs and the TM09 ball are campaign work'))
    door = next((x, y) for y, row in enumerate(r['grid']) for x, ch in enumerate(row) if ch == 'D')
    warps.append(dict(x=door[0], y=door[1], elevation=0, dest_map='MAP_ROUTE32_POKEMON_CENTER', dest_warp_id='0'))
    M = dict(id=MAP_ID, name=MAP, layout=LAYOUT, music='MUS_LITTLEROOT', region='REGION_JOHTO', region_map_section='MAPSEC_JOHTO_ROUTE_32',
             requires_flash=False, weather='WEATHER_SUNNY', map_type='MAP_TYPE_ROUTE', allow_cycling=True, allow_escaping=False,
             allow_running=True, show_map_name=True, battle_scene='MAP_BATTLE_SCENE_NORMAL', build_target='emerald',
             connections=[dict(map='MAP_VIOLET_CITY', direction='up', offset=PADL - Rf.VIOLET_SHIFT)],
             object_events=objs, warp_events=warps, coord_events=[], bg_events=bgs)
    (engine / f'data/maps/{MAP}').mkdir(parents=True, exist_ok=True)
    (engine / f'data/maps/{MAP}/map.json').write_text(json.dumps(M, indent=2) + '\n')
    (engine / f'data/maps/{MAP}/scripts.inc').write_text(SCRIPTS)
    write_flags(engine); write_mapsec(engine); write_center(engine); register_maps(engine)
    return dict(moves=moves, door=list(door), border=[f'{b & 1023:#05x}' for b in border])

# --------------------------------------------------------------------------- checks
def decode(engine, words, width=None):
    t = Tileset(engine, TS_NAME, PRI_NAME)
    return np.array(t.map_image(words.ravel().tolist(), width or W).convert('RGB')), t

def report_of(engine, r):
    report = dict(jobs=r['n_jobs'], tiles=len(r['tiles']), primary_metatiles=r['n_pri_meta'], secondary_metatiles=r['n_sec_meta'],
                  pinned_violet_metatiles=len(r['pins']), maximal_colour_sets=r['maximal_sets'],
                  banks={b: len(p) for b, p in sorted(r['pals'].items())})
    trav, cells = r['trav'], r['cells']
    events = json.loads((SRC / 'hgss-events.json').read_text())
    cut = {Rf.to_map(*o['cell']) for o in events['objects'] if o['sprite'] in ('SPRITE_TREE', 'SPRITE_BREAKROCK')}
    start = (min(Rf.VIOLET_ROAD), 0)
    hs = hgss_reach(cells, (15, 0))
    ns_cut = reach(trav, start, cut_open=True)
    ns = reach(trav, start, cut=cut)
    hs_map = {Rf.to_map(*p) for p in hs}
    region = lambda p: p[1] >= ROW0
    report['reach'] = dict(native_with_cut=len([p for p in ns_cut if region(p)]), native_before_cut=len([p for p in ns if region(p)]),
                           hgss=len(hs), native_only=sorted(list(p) for p in ns_cut if region(p) and p not in hs_map),
                           hgss_only=sorted(list(p) for p in hs_map if p not in ns_cut),
                           south_edge_reached=any(p[1] == H - 1 for p in ns_cut))
    return report

# --------------------------------------------------------------------------- edge padding
PADL, PADR = 5, 4                    # columns west and east: (width + 15) x (166 + 14) must fit MAX_MAP_DATA_SIZE 10240, so 41 wide at most

def pad_out(r):
    """Woods (west, and east where the route's east column is land) or sea (east, beside the route's sea) beyond
    HGSS's edges, from periodic 2x2 blocks of the route's own forest and sea metatiles; the Violet padding rows and
    the viaduct's rows run on as their edge cell. Every padding cell is blocked. Returns padded words, grid, trav."""
    words, grid, trav = r['words'], r['grid'], r['trav']
    def periodic(code):
        for y in range(ROW0, H - 3):
            for x in range(W - 3):
                if all(grid[y + dy][x + dx] in code for dx in range(4) for dy in range(4)) and \
                   all((words[y + dy, x + dx] & 1023) == (words[y + dy + 2, x + dx] & 1023) == (words[y + dy, x + dx + 2] & 1023)
                       for dx in (0, 1) for dy in (0, 1)):
                    return {(dx, dy): int(words[y + dy, x + dx]) & 1023 for dx in (0, 1) for dy in (0, 1)}, (x, y)
        raise AssertionError(('no periodic block', code))
    woods, wat = periodic('t')
    sea, sat = periodic('~')
    v0, v1 = round((Rf.VIADUCT[0] + ROW0) * PX) // PX, -(-round((Rf.VIADUCT[1] + ROW0) * PX) // PX)
    NW = W + PADL + PADR
    out = np.zeros((H, NW), np.uint16)
    out[:, PADL:PADL + W] = words
    blocked = lambda m: m | (1 << 10)
    for y in range(H):
        for k in range(PADL):
            x = PADL - 1 - k                              # west columns, outward
            if y < ROW0 or v0 <= y < v1:
                m = int(words[y, 0]) & 1023
            else:
                m = woods[((x - wat[0]) % 2, (y - wat[1]) % 2)]
            out[y, x] = blocked(m)
        east_sea = grid[y][W - 1] in '~XO' and trav[y, W - 1].get('behavior') in ('MB_OCEAN_WATER', None) and \
            grid[y][W - 1] != 'R' and (grid[y][W - 1] == '~' or trav[y, W - 1].get('note', '').startswith(('HGSS', 'sea')))
        for k in range(PADR):
            x = PADL + W + k
            if y < ROW0 or v0 <= y < v1:
                m = int(words[y, W - 1]) & 1023
            elif east_sea:
                m = sea[((x - PADL - sat[0]) % 2, (y - sat[1]) % 2)]
            else:
                m = woods[((x - PADL - wat[0]) % 2, (y - wat[1]) % 2)]
            out[y, x] = blocked(m)
    pgrid = [['#'] * PADL + list(row) + ['#'] * PADR for row in grid]
    ptrav = np.empty((H, NW), object)
    for y in range(H):
        for x in range(NW):
            if PADL <= x < PADL + W:
                c = dict(trav[y, x - PADL]); c['x'] = x
            else:
                c = dict(x=x, y=y, code='#', foot='blocked', behavior='MB_NORMAL', collision=1, elevation=0, note='edge padding')
            ptrav[y, x] = c
    return dict(words=out, grid=pgrid, trav=ptrav, width=NW, woods_block=list(wat), sea_block=list(sat))

def main(engine, install):
    r = pack(engine)
    report = report_of(engine, r)
    if install:
        write_tilesets(engine, r); register(engine)
        native, _ = decode(engine, r['words'])
        Image.fromarray(native).save(OEV / 'native.png')
        dd = (rgb5(native) != rgb5(r['want'])).any(-1)
        report['native_pixels_differing'] = int(dd.sum())
        pad = pad_out(r)
        r.update(words=pad['words'], grid=pad['grid'], trav=pad['trav'])
        report['padding'] = dict(west=PADL, east=PADR, width=pad['width'], woods_block=pad['woods_block'], sea_block=pad['sea_block'])
        report['events'] = write_map(engine, r)
        padded, _ = decode(engine, r['words'], pad['width'])
        Image.fromarray(padded).save(OEV / 'native-padded.png')
    NWd = r['words'].shape[1]
    (OUT / 'traversal.json').write_text(json.dumps([r['trav'][y, x] for y in range(H) for x in range(NWd)], default=int) + '\n')
    (OEV / 'pack.json').write_text(json.dumps(report, indent=1, default=int) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('events',)}, default=int)[:3000])

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), '--install' in sys.argv)
