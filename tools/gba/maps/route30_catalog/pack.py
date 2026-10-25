"""Route 30: exact native pack onto CherrygrovePrimary, traversal from the decoded HGSS permissions,
layer types, events, and installation into the engine checkout (Route 29's pack.py, for Route 30).

    python3 tools/gba/maps/route30_catalog/pack.py ENGINE_CHECKOUT [--install]
    python3 tools/gba/maps/route30_catalog/pack.py ENGINE_CHECKOUT --spec FILE | --install-words FILE

The installed pack is the joint Route 30/31 pack (pair_pack.py), which runs this file with --spec (this map's
layers, traversal and pins) and --install-words (its map words, events and checks); the single pack below
is Route 30 alone, kept for comparison.

Route 30 keeps its live connections to Cherrygrove (south, offset 35) and Route 31 (north, offset -28). A
Gen 3 map draws a connected map's nearest 7 rows with its own tilesets, so Route 30's primary is
CherrygrovePrimary with only its palettes 4 and 5 changed (`cherrygrove_route30`): every Cherrygrove tile
and metatile a Cherrygrove cell visible from Route 30 uses keeps its index and look in palettes 0-3;
palettes 4-5 and the free tile slots hold route art. The route's own art goes in one secondary tileset
(`route30_hgss`, banks 6-12):
  * the south band (reference.py) is Cherrygrove's own primary metatiles, so Cherrygrove draws it exactly,
    and Cherrygrove's own top rows are primary metatiles, which Route 30 draws exactly;
  * the cells either map can see across the Route 30/31 seam sit at secondary ids both secondaries define
    (pair_pack.py); seams.py checks both seams from both sides.
Everything else packs exactly (Mahogany's lossless rule): every native pixel keeps its assembled RGB555
colour; tiles that exist in CherrygrovePrimary are reused from it; the rest go into exact banks.

Traversal (source/trace/ledger.json, decoded HGSS permissions): woods under a tree root, rock, houses,
fences, signs and ledge ends blocked (collision 1, elevation 0 as vanilla); jump-south ledges
MB_JUMP_SOUTH; pond water MB_POND_WATER (collision 0, elevation 1); tall grass MB_TALL_GRASS; stairs and
everything else open. Declared adaptations: woods cells under a crown stay solid, as HGSS has them; both
house doors stay shut (no interiors exist yet); the north padding's road (reference.py) is open.
"""
from __future__ import annotations
import json, re, struct, subprocess, sys
from collections import Counter, deque
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import reference as Rf                               # noqa: E402
from reference import W, H, PX, COL0, ROW0, PAD0     # noqa: E402
from tiles import Tileset                            # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route30-catalog'
SRC, EV = ART / 'source', ART / 'evidence'
OUT, OEV = SRC / 'pack', EV / 'pack'
MAP, LAYOUT = 'CherrygroveRoute30Approach', 'LAYOUT_CHERRYGROVE_ROUTE30_APPROACH'
TS_NAME, TS_SYM = 'route30_hgss', 'Route30Hgss'
PRI_NAME, PRI_SYM = 'cherrygrove_route30', 'CherrygroveRoute30Primary'
PRI_KEEP = (0, 1, 2, 3)              # CherrygrovePrimary's palettes kept as they are
PRI_FREE = (4, 5)                    # palettes the route art takes (no Cherrygrove cell near either seam uses them)
BASE_REV = '2722eaf7601ec02dc5a684fa8cdef9206c0dc377'
SEC_TILES = 512
BANKS = list(PRI_FREE) + list(range(6, 13))
COVERED, NORMAL = 1, 0
# JOHTO_ITEMS.md: Route 30's Antidote ball, Potion ball and hidden Potion near the Trainer Tips sign.
ITEMS = dict(antidote=('FLAG_ITEM_APOC_ROUTE30_ANTIDOTE', 'FLAG_UNUSED_0x265', 'ITEM_ANTIDOTE'),
             potion=('FLAG_ITEM_APOC_ROUTE30_POTION', 'FLAG_UNUSED_0x266', 'ITEM_POTION'),
             hidden=('FLAG_HIDDEN_ITEM_APOC_ROUTE30_POTION', 'FLAG_UNUSED_0x267', 'ITEM_POTION'))
SIGN_SCRIPTS = {'Rt. 30': 'CherrygroveRoute30Approach_RouteSign', 'Straight Ahead': 'CherrygroveRoute30Approach_JunctionSign',
                'Trainer Tips': 'CherrygroveRoute30Approach_TrainerTips', 'House': 'CherrygroveRoute30Approach_MrPokemonSign'}

def rgb5(a): return (np.asarray(a).astype(np.int32) >> 3)

# --------------------------------------------------------------------------- engine data
def behaviors(engine):
    names = re.findall(r'^\s+(MB_[A-Z0-9_]+),', (engine / 'include/constants/metatile_behaviors.h').read_text(), re.M)
    return {n: i for i, n in enumerate(names)}

class Primary:
    """CherrygrovePrimary: every tile under every bank and flip, every metatile's rendering."""
    def __init__(self, engine):
        t = Tileset(engine, 'cherrygrove', 'cherrygrove')
        self.t = t
        self.tiles = [np.array(x, np.uint8).reshape(8, 8) & 15 for x in t.tiles[0]]
        self.pals = [[tuple(c) for c in p] for p in t.pals[0][:6]]
        self.keep = PRI_KEEP
        self.opaque, self.masked = {}, {}
        for i, ix in enumerate(self.tiles):
            for f in range(4):
                v = ix[:, ::-1] if f & 1 else ix
                v = v[::-1] if f & 2 else v
                for b, pal in enumerate(self.pals):
                    if b not in PRI_KEEP:
                        continue
                    rgb = np.array([pal[k] for k in v.ravel()], np.uint8).reshape(8, 8, 3)
                    key = rgb5(rgb).astype(np.int16)
                    self.masked.setdefault(np.where((v > 0)[..., None], key, -1).tobytes(), (i, f, b))
                    if (v > 0).all():
                        self.opaque.setdefault(key.tobytes(), (i, f, b))
        self.metatiles = [tuple(int(e) for e in m) for m in t.blocks[0]]
        self.attrs = list(t.attrs[0])

def entry(tile, flip, bank):
    return tile | ((flip & 1) << 10) | ((flip >> 1) << 11) | (bank << 12)

def cherrygrove_words(engine):
    b = (engine / 'data/layouts/CherrygroveCity/map.bin').read_bytes()
    return np.array(struct.unpack('<%dH' % (len(b) // 2), b)).reshape(-1, 80)

# --------------------------------------------------------------------------- traversal
def traversal(engine, grid, cells):
    MB = behaviors(engine)
    cg = cherrygrove_words(engine)
    out = np.empty((H, W), object)
    for y in range(H):
        for x in range(W):
            ch = grid[y][x]
            hx, hz = Rf.to_hgss(x, y)
            c = dict(x=x, y=y, code=ch)
            if 0 <= hz < Rf.HH and 0 <= hx < Rf.HW:
                c['hgss'] = dict(type=cells[hz][hx]['type'], collision=cells[hz][hx]['collision'], label=cells[hz][hx]['lab'])
            if ch in 'Pp':
                cx, cy = Rf.pad_source(x, y)
                v = int(cg[cy, cx])
                c.update(foot='open' if (v >> 10) & 3 == 0 else 'blocked', behavior=None, collision=(v >> 10) & 3,
                         elevation=v >> 12, metatile=v & 1023, source=f'Cherrygrove ({cx},{cy})')
            elif ch == 'L':
                c.update(foot='ledge_south', behavior='MB_JUMP_SOUTH', collision=1, elevation=0)
            elif ch == '~':
                c.update(foot='water', behavior='MB_POND_WATER', collision=0, elevation=1)
            elif ch == 'D':
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=0,
                         adaptation="HGSS's house door; no interior exists yet, so the doorway stays shut")
            elif ch in 'tkoRHnsJX':
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=0)
            elif ch == 'G':
                c.update(foot='open', behavior='MB_TALL_GRASS', collision=0, elevation=3)
            else:
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3)
            if c['behavior']:
                c['behavior_id'] = MB[c['behavior']]
            out[y, x] = c
    return out

def reach(trav, start, cut_open=False, cut=()):
    """Cells reachable on foot from start, with Gen 3 ledge rules (jump over a ledge in its direction)."""
    jump = {'ledge_south': (0, 1)}
    seen = {start}; q = deque([start])
    walk = lambda p: 0 <= p[0] < W and 0 <= p[1] < H and trav[p[1], p[0]]['foot'] == 'open' and (cut_open or p not in cut)
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if not (0 <= n[0] < W and 0 <= n[1] < H):
                continue
            f = trav[n[1], n[0]]['foot']
            if f in jump and jump[f] == (dx, dy):
                n = (n[0] + dx, n[1] + dy)
            if walk(n) and n not in seen:
                seen.add(n); q.append(n)
    return seen

def hgss_reach(cells, start):
    """The same search on HGSS's own permissions (HGSS frame); water and doors are not walked."""
    types = {0x3B: (0, 1), 0x38: (1, 0), 0x39: (-1, 0)}
    open_ = lambda hx, hz: (0 <= hx < Rf.HW and 0 <= hz < Rf.HH and not cells[hz][hx]['blocked']
                            and cells[hz][hx]['type'] not in (0x10, 0x69))
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
    """Walkable cells whose object art belongs to something standing further south draw above the
    player (Route 43's rule: a crown or roof the player walks behind)."""
    art = top[..., 3] > 0
    base = {}
    for name in set(owner[art].ravel().tolist()) - {''}:
        base[name] = int(np.nonzero((owner == name).any(1))[0].max()) // 16
    out = np.zeros((H, W), bool)
    for y in range(H):
        for x in range(W):
            if trav[y, x]['foot'] != 'open' or trav[y, x]['code'] in 'Pp':
                continue
            sl = np.s_[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
            a = art[sl]
            if not a.any():
                continue
            names = {n for n in set(owner[sl][a].ravel().tolist()) - {''} if not n.startswith('fence')}
            out[y, x] = any(base[n] > y for n in names)
    return out

# --------------------------------------------------------------------------- pack
def visible_cherrygrove(engine, trav=None):
    """Cherrygrove's metatiles a player on Route 30 can see across the seam: from every walkable Route 30
    cell, the camera's 8 columns either side and 5 rows below (seams.py's rule). Without a traversal, the
    south band's road (the only walkable cells within 5 rows of Cherrygrove)."""
    cg = cherrygrove_words(engine)
    walk = [(x, y) for y in range(H - 6, H) for x in range(W)
            if (trav[y, x]['foot'] == 'open' if trav is not None else x in Rf.ROAD_COLS)]
    out = set()
    for x, y in walk:
        for dx in range(-8, 9):
            for dy in range(-5, 6):
                cx, cy = x + dx + Rf.CG_OFFSET, y + dy - H
                if 0 <= cy < cg.shape[0] and 0 <= cx < cg.shape[1]:
                    out.add(int(cg[cy, cx]) & 1023)
    return out

def prepare(engine):
    """Layers, traversal, layer types, the band placed by id and the banks it pins (the joint pack and
    the single pack share this)."""
    z = np.load(SRC / 'assemble/layers.npz', allow_pickle=True)
    ground, flat, top, owner = z['ground'], z['flat'], z['objects'], z['owner'].astype(object)
    grid = [list(l.split()[1]) for l in (SRC / 'trace/material-grid.txt').read_text().splitlines() if l[:3].isdigit()]
    cells = json.loads((SRC / 'trace/ledger.json').read_text())['cells']
    trav = traversal(engine, grid, cells)
    above = above_player(trav, top, owner)
    P = Primary(engine)
    want = ground.copy()
    for layer in (flat, top):
        a = layer[..., 3] > 0; want[a] = layer[a, :3]
    fixed_pal, placed = {}, {}
    # The south band: Cherrygrove's own metatile ids (primary), with Cherrygrove's collision and elevation.
    for y in range(PAD0, H):
        for x in range(W):
            placed[(x, y)] = trav[y, x]['metatile']
    # Primary metatiles placed by id may draw primary tiles in secondary palette banks (the towns' blossom
    # trees use bank 10): those banks take the towns' palettes.
    cg_pals = [[tuple(c) for c in p] for p in P.t.pals[1]]
    visible = visible_cherrygrove(engine, trav)
    assert all(m < 512 for m in visible), 'a visible Cherrygrove secondary metatile would need pinning'
    for m in sorted({m for m in placed.values() if m < 512} | visible):
        for e in P.metatiles[m]:
            bank = e >> 12
            if bank >= 6 and e:
                pal = cg_pals[bank][1:16]
                assert fixed_pal.get(bank, pal) == pal, f'primary metatile {m:#x} needs bank {bank} with another palette'
                fixed_pal[bank] = pal
    from claude_cherrygrove import ground as Gr
    import assemble as As
    yy, xx = np.mgrid[0:H * 16, 0:W * 16]
    lawn_t = Gr.textures()[Gr.GRASS]
    road_t = As.road_texture(engine)
    plains = [lawn_t[(yy + Rf.YPHASE) % 32, (xx + Rf.XPHASE) % 32].astype(np.uint8),
              road_t[(yy + Rf.YPHASE) % 32, (xx + Rf.XPHASE) % 32].astype(np.uint8)]
    return dict(ground=ground, flat=flat, top=top, owner=owner, grid=grid, cells=cells, trav=trav, above=above, P=P,
                want=want, placed=placed, fixed_pal=fixed_pal, visible=visible, plains=plains)

def save_pair_spec(engine, path):
    """This map's input to the joint Route 30/31 pack (pair_pack.py)."""
    import pair_pack as PP
    d = prepare(engine)
    trav = d['trav']
    get = lambda k: np.array([[trav[y, x][k] if trav[y, x].get(k) is not None else 0 for x in range(W)] for y in range(H)])
    PP.save_spec(path, 'route30', W, H, d['ground'], d['flat'], d['top'], d['owner'], d['above'], get('behavior_id'),
                 get('collision'), get('elevation'), d['placed'], d['fixed_pal'],
                 d['visible'] | {m for m in d['placed'].values() if m < 512}, d['plains'])

def pack(engine):
    OUT.mkdir(parents=True, exist_ok=True); OEV.mkdir(parents=True, exist_ok=True)
    d = prepare(engine)
    ground, flat, top, owner, grid, cells = d['ground'], d['flat'], d['top'], d['owner'], d['grid'], d['cells']
    trav, above, P, want, placed, fixed_pal, visible, plains = (d[k] for k in ('trav', 'above', 'P', 'want', 'placed', 'fixed_pal', 'visible', 'plains'))
    pinned_defs = {}
    sec_tiles, sec_lookup = [np.zeros((8, 8), np.uint8)], {np.zeros((8, 8), np.uint8).tobytes(): 0}
    def add_tile(ix):
        for f in range(4):
            v = ix[:, ::-1] if f & 1 else ix
            v = v[::-1] if f & 2 else v
            if v.tobytes() in sec_lookup:
                return sec_lookup[v.tobytes()], f
        sec_lookup[ix.tobytes()] = len(sec_tiles); sec_tiles.append(ix.copy())
        return len(sec_tiles) - 1, 0

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
    def backing(b, vis, sl):
        """A bottom tile partly hidden under opaque top-layer art: only its visible pixels count (Route 43's
        rule). If they match the plain lawn or road here, the plain (primary) tile is used."""
        if not (~vis).any():
            return b
        for pl in plains:
            if (pl[sl][vis] == b[vis]).all():
                return pl[sl].copy()
        return b
    common = Counter(ground[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].tobytes() for ty in range(PAD0 * 2) for tx in range(W * 2)).most_common(1)[0][0]
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
                if up.all():
                    b = job(filler, None, 0)
                else:
                    b = job(backing(gpx, ~up, sl), None, 0)
                t = job(upx, up, 1) if up.any() else None
                q.append((b, t))
            cellplan[(x, y)] = q
    for k, j in jobs.items():
        j['primary'] = (P.opaque if j['layer'] == 0 else P.masked).get(j['k5'].tobytes())
    rest = [j for j in jobs.values() if j['primary'] is None]
    setof = lambda j: frozenset(map(tuple, j['k5'][j['k5'][..., 0] >= 0].reshape(-1, 3).tolist()))
    over15 = [j for j in rest if len(setof(j)) > 15]
    assert not over15, f'{len(over15)} tiles hold more than 15 colours'
    fixed5 = {b: frozenset(tuple(int(v) >> 3 for v in c) for c in p) for b, p in fixed_pal.items()}
    # A secondary tile may draw in a primary palette: sets inside one of CherrygrovePrimary's six take it.
    prim5 = {b: [tuple(int(v) >> 3 for v in c) for c in P.pals[b][1:16]] for b in PRI_KEEP}
    free = [b for b in BANKS if b not in fixed5]
    sets = [setof(j) for j in rest]
    from banks import pack_sets
    inside_fixed = lambda s: next((b for b, f in list(fixed5.items()) + [(b, frozenset(p)) for b, p in prim5.items()] if s <= f), None)
    todo = [s for s in sets if inside_fixed(s) is None]
    newbanks = pack_sets(todo, len(free)) if todo else []
    if newbanks is None:                             # the greedy packer gave up: Route 43's exact program
        from banks import milp_sets
        distinct = set(todo)
        maximal = sorted((c for c in distinct if not any(c < d for d in distinct)), key=lambda c: (-len(c), sorted(c)))
        newbanks = milp_sets(maximal, len(free), fixed=[(0, 0)])
    assert newbanks is not None, 'route art does not fit the free secondary banks'
    pal5 = dict(fixed5)
    for b, s in zip(free, newbanks):
        pal5[b] = frozenset(s)
    order5 = {b: sorted(s) for b, s in pal5.items()}
    for b in fixed_pal:
        order5[b] = [tuple(int(v) >> 3 for v in c) for c in fixed_pal[b]]
    slots = dict(order5); slots.update(prim5)
    for j, s in zip(rest, sets):
        b = inside_fixed(s)
        if b is None:
            b = next(bb for bb in free if bb in pal5 and s <= pal5[bb])
        idx = {}
        for i, c in enumerate(slots[b]):
            idx.setdefault(c, i + 1)
        k5 = j['k5']
        ix = np.zeros((8, 8), np.uint8)
        m = k5[..., 0] >= 0
        ix[m] = [idx[tuple(c)] for c in k5[m].reshape(-1, 3).tolist()]
        t, f = add_tile(ix)
        j['tile'] = (t, f, b)
    # The shared primary keeps every Cherrygrove tile a seam can show (the cells visible across it, the
    # south band) and every primary tile the route reuses; its other slots take what the secondary cannot.
    keep = {0}
    for m in visible | {m for m in placed.values() if m < 512}:
        keep |= {e & 1023 for e in P.metatiles[m] if e}
    for j in jobs.values():
        if j['primary'] is not None:
            keep.add(j['primary'][0])
    for m in visible:
        assert all((e >> 12) in PRI_KEEP or (e >> 12) >= 6 for e in P.metatiles[m] if e), f'visible Cherrygrove metatile {m:#x} draws in palette 4 or 5'
    free_slots = [i for i in range(512) if i not in keep]
    overflow = max(0, len(sec_tiles) - SEC_TILES)
    assert overflow <= len(free_slots), ('tiles over the secondary and the primary slots', len(sec_tiles), len(free_slots))
    final = lambda t: 512 + t if t < SEC_TILES else free_slots[t - SEC_TILES]
    for j in jobs.values():
        if j['primary'] is not None:
            i, f, b = j['primary']
            j['entry'] = entry(i, f, b)
        else:
            t, f, b = j['tile']
            j['entry'] = entry(final(t), f, b)
    pri_tiles = {free_slots[t - SEC_TILES]: sec_tiles[t] for t in range(SEC_TILES, len(sec_tiles))}
    sec_tiles = sec_tiles[:SEC_TILES]

    # ---- metatiles and the map
    prim_index = {(P.metatiles[m], P.attrs[m]): m for m in range(512)}
    sec_meta = {}
    for mid, d in pinned_defs.items():
        sec_meta.setdefault(d, mid)
    next_id = [512]
    def sec_id(key):
        if key in prim_index:
            return prim_index[key]
        if key not in sec_meta:
            while next_id[0] in pinned_defs:
                next_id[0] += 1
            sec_meta[key] = next_id[0]; next_id[0] += 1
        return sec_meta[key]
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
                mid = sec_id((tuple(bot + tp), c['behavior_id'] | (layer << 12)))
            c['metatile'] = mid
            words[y, x] = mid | (c['collision'] << 10) | (c['elevation'] << 12)
    n_sec = max([m for m in sec_meta.values()] + [511]) - 511
    assert n_sec <= 512, ('secondary metatiles over budget', n_sec)
    meta_rows = [(tuple([0] * 8), 0)] * n_sec
    for key, mid in sec_meta.items():
        meta_rows[mid - 512] = key
    pals = {b: [tuple(v << 3 for v in c) for c in order5[b]] for b in order5}
    for b in fixed_pal:
        pals[b] = list(fixed_pal[b])
    # Primary metatiles drawn in a changed palette would look different: none may be placed by id or reused.
    for (x, y), m in placed.items():
        if m < 512:
            assert all((e >> 12) in PRI_KEEP for e in P.metatiles[m] if e), f'placed primary metatile {m:#x} uses palette 4 or 5'
    return dict(words=words, trav=trav, sec_tiles=sec_tiles, pri_tiles=pri_tiles, keep=sorted(keep), pals=pals, meta_rows=meta_rows,
                n_jobs=len(jobs), n_primary_jobs=sum(j['primary'] is not None for j in jobs.values()),
                want=want, grid=grid, cells=cells, above=above)

# --------------------------------------------------------------------------- write
def write_primary(engine, r):
    """CherrygrovePrimary's metatiles and attributes, copied as they are; its tiles, with the slots no seam
    shows and the route does not reuse holding the route tiles the secondary cannot; palettes 4 and 5 from
    the route art. Palettes 0-3 (and 6-15, which a primary never shows) are Cherrygrove's."""
    import shutil
    src, d = engine / 'data/tilesets/primary/cherrygrove', engine / 'data/tilesets/primary' / PRI_NAME
    (d / 'palettes').mkdir(parents=True, exist_ok=True)
    for f in ('metatiles.bin', 'metatile_attributes.bin'):
        shutil.copyfile(src / f, d / f)
    im = Image.open(src / 'tiles.png')
    a = np.array(im)
    for i, t in r['pri_tiles'].items():
        a[(i // 16) * 8:(i // 16) * 8 + 8, (i % 16) * 8:(i % 16) * 8 + 8] = t
    out = Image.fromarray(a.astype(np.uint8), 'P'); out.putpalette(im.getpalette())
    out.save(d / 'tiles.png', bits=4)
    for b in range(16):
        if b in PRI_FREE:
            cols = list(r['pals'].get(b, [])) + [(0, 0, 0)] * 15
            (d / 'palettes' / f'{b:02}.pal').write_text('\r\n'.join(['JASC-PAL', '0100', '16', '0 0 0'] + [f'{c[0]} {c[1]} {c[2]}' for c in cols[:15]]) + '\r\n')
        else:
            shutil.copyfile(src / 'palettes' / f'{b:02}.pal', d / 'palettes' / f'{b:02}.pal')
    (OUT / 'primary-state.json').write_text(json.dumps(dict(
        note='Route 30 in the shared primary: palettes 4-5 and the tile slots it fills; every other slot is CherrygrovePrimary\'s.',
        palettes={str(b): r['pals'].get(b, []) for b in PRI_FREE}, route30_slots=sorted(r['pri_tiles']), kept_cherrygrove=r['keep'])) + '\n')

def write_tileset(engine, r):
    d = engine / 'data/tilesets/secondary' / TS_NAME
    d.mkdir(parents=True, exist_ok=True); (d / 'palettes').mkdir(exist_ok=True)
    tiles = r['sec_tiles']
    rows = max(1, (len(tiles) + 15) // 16)
    sheet = np.zeros((rows * 8, 128), np.uint8)
    for i, t in enumerate(tiles):
        sheet[(i // 16) * 8:(i // 16) * 8 + 8, (i % 16) * 8:(i % 16) * 8 + 8] = t
    im = Image.fromarray(sheet, 'P'); im.putpalette([v for i in range(16) for v in (i * 17, i * 17, i * 17)] + [0] * 720)
    im.save(d / 'tiles.png', bits=4)
    for b in range(16):
        cols = r['pals'].get(b, []) if b >= 6 else []
        cols = list(cols) + [(0, 0, 0)] * (15 - len(cols))
        (d / 'palettes' / f'{b:02}.pal').write_text('\r\n'.join(['JASC-PAL', '0100', '16', '0 0 0'] + [f'{c[0]} {c[1]} {c[2]}' for c in cols[:15]]) + '\r\n')
    (d / 'metatiles.bin').write_bytes(b''.join(struct.pack('<8H', *k[0]) for k in r['meta_rows']))
    (d / 'metatile_attributes.bin').write_bytes(struct.pack('<%dH' % len(r['meta_rows']), *[k[1] for k in r['meta_rows']]))

def register(engine):
    h = engine / 'src/data/tilesets/headers.h'; s = h.read_text()
    if f'gTileset_{PRI_SYM} =' not in s:
        s = s.replace('// End Claude routes\n', f'const struct Tileset gTileset_{PRI_SYM} = {{ .isCompressed = TRUE, .isSecondary = FALSE, .tiles = gTilesetTiles_{PRI_SYM}, .palettes = gTilesetPalettes_{PRI_SYM}, .metatiles = gMetatiles_{PRI_SYM}, .metatileAttributes = gMetatileAttributes_{PRI_SYM}, .callback = NULL }};\n// End Claude routes\n', 1)
    if f'gTileset_{TS_SYM} =' not in s:
        s = s.replace('// End Claude routes\n', f'const struct Tileset gTileset_{TS_SYM} = {{ .isCompressed = TRUE, .isSecondary = TRUE, .tiles = gTilesetTiles_{TS_SYM}, .palettes = gTilesetPalettes_{TS_SYM}, .metatiles = gMetatiles_{TS_SYM}, .metatileAttributes = gMetatileAttributes_{TS_SYM}, .callback = NULL }};\n// End Claude routes\n', 1)
    h.write_text(s)
    g = engine / 'src/data/tilesets/graphics.h'; s = g.read_text()
    if f'gTilesetTiles_{PRI_SYM}[]' not in s:
        s = s.rstrip('\n') + f'\n\nconst u32 gTilesetTiles_{PRI_SYM}[] = INCGFX_U32("data/tilesets/primary/{PRI_NAME}/tiles.png", ".4bpp.fastSmol");\nconst u16 gTilesetPalettes_{PRI_SYM}[][16] = {{\n' + ''.join(f'INCGFX_U16("data/tilesets/primary/{PRI_NAME}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n'
    if f'gTilesetTiles_{TS_SYM}[]' not in s:
        s = s.rstrip('\n') + f'\n\nconst u32 gTilesetTiles_{TS_SYM}[] = INCGFX_U32("data/tilesets/secondary/{TS_NAME}/tiles.png", ".4bpp.fastSmol");\nconst u16 gTilesetPalettes_{TS_SYM}[][16] = {{\n' + ''.join(f'INCGFX_U16("data/tilesets/secondary/{TS_NAME}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n'
    g.write_text(s)
    m = engine / 'src/data/tilesets/metatiles.h'; s = m.read_text()
    if f'gMetatiles_{PRI_SYM}[]' not in s:
        s = s.rstrip('\n') + f'\nconst u16 gMetatiles_{PRI_SYM}[] = INCBIN_U16("data/tilesets/primary/{PRI_NAME}/metatiles.bin");\nconst u16 gMetatileAttributes_{PRI_SYM}[] = INCBIN_U16("data/tilesets/primary/{PRI_NAME}/metatile_attributes.bin");\n'
    if f'gMetatiles_{TS_SYM}[]' not in s:
        s = s.rstrip('\n') + f'\nconst u16 gMetatiles_{TS_SYM}[] = INCBIN_U16("data/tilesets/secondary/{TS_NAME}/metatiles.bin");\nconst u16 gMetatileAttributes_{TS_SYM}[] = INCBIN_U16("data/tilesets/secondary/{TS_NAME}/metatile_attributes.bin");\n'
    m.write_text(s)

def write_flags(engine):
    f = engine / 'include/constants/flags.h'; s = f.read_text()
    anchor = next(l for l in s.splitlines() if l.startswith('#define FLAG_HIDDEN_ITEM_APOC_ROUTE29_POTION'))
    add = [f'#define {name} {slot} // Route 30: {what} (JOHTO_ITEMS.md, HGSS {"hidden item" if k == "hidden" else "item ball"})'
           for k, (name, slot, what) in ITEMS.items() if f'#define {name} ' not in s]
    if add:
        s = s.replace(anchor, anchor + '\n' + '\n'.join(add), 1); f.write_text(s)

SCRIPTS = '''CherrygroveRoute30Approach_MapScripts::
    .byte 0

CherrygroveRoute30Approach_JunctionSign::
    msgbox CherrygroveRoute30Approach_JunctionSign_Text, MSGBOX_SIGN
    end

CherrygroveRoute30Approach_JunctionSign_Text:
    .string "MR. POKéMON'S HOUSE\\nSTRAIGHT AHEAD!$"

CherrygroveRoute30Approach_RouteSign::
    msgbox CherrygroveRoute30Approach_RouteSign_Text, MSGBOX_SIGN
    end

CherrygroveRoute30Approach_RouteSign_Text:
    .string "ROUTE 30\\nSOUTH TO CHERRYGROVE CITY$"

CherrygroveRoute30Approach_TrainerTips::
    msgbox CherrygroveRoute30Approach_TrainerTips_Text, MSGBOX_SIGN
    end

CherrygroveRoute30Approach_TrainerTips_Text:
    .string "TRAINER TIPS\\p"
    .string "No stealing other people's POKéMON!\\p"
    .string "POKé BALLS are to be thrown only at\\n"
    .string "wild POKéMON!$"

CherrygroveRoute30Approach_MrPokemonSign::
    msgbox CherrygroveRoute30Approach_MrPokemonSign_Text, MSGBOX_SIGN
    end

CherrygroveRoute30Approach_MrPokemonSign_Text:
    .string "MR. POKéMON'S HOUSE$"
'''

def write_map(engine, r, connections=None):
    words = r['words']
    (engine / f'data/layouts/{MAP}/map.bin').write_bytes(struct.pack('<%dH' % (W * H), *words.ravel().tolist()))
    lj = engine / 'data/layouts/layouts.json'; L = json.loads(lj.read_text())
    for l in L['layouts']:
        if l['id'] == LAYOUT:
            l['primary_tileset'] = 'gTileset_' + PRI_SYM; l['secondary_tileset'] = 'gTileset_' + TS_SYM; l['width'] = W; l['height'] = H
    lj.write_text(json.dumps(L, indent=2) + '\n')
    base = json.loads(subprocess.check_output(['git', '-C', str(engine), 'show', f'{BASE_REV}:data/maps/{MAP}/map.json']))
    events = json.loads((SRC / 'hgss-events.json').read_text())
    bgs, moves = [], []
    for s in events['signs']:
        x, y = Rf.to_map(*s['cell'])
        if s['bg_type'] == 1:
            script = next(v for k, v in SIGN_SCRIPTS.items() if k in s['text'])
            bgs.append(dict(type='sign', x=x, y=y, elevation=0, player_facing_dir='BG_EVENT_PLAYER_FACING_ANY', script=script))
            moves.append(dict(event=script, cell=[x, y], hgss=s['cell'], text=s['text']))
        elif s['script'] == 'std_hiddenitem_r30_potion':
            name, _, item = ITEMS['hidden']
            assert r['trav'][y, x]['foot'] == 'open', ('hidden item cell is not open ground', x, y)
            bgs.append(dict(type='hidden_item', x=x, y=y, elevation=3, item=item, flag=name, quantity=1, underfoot=False))
            moves.append(dict(event='hidden Potion', cell=[x, y], hgss=s['cell'], flag=name))
        else:
            moves.append(dict(event=s['script'], hgss=s['cell'], note='outside Route 30 (the Route 29/30/Cherrygrove border Nugget): not placed'))
    objs = []
    cut = [Rf.to_map(*o['cell']) for o in events['objects'] if o['sprite'] == 'SPRITE_TREE']
    for n, (x, y) in enumerate(cut):
        objs.append(dict(graphics_id='OBJ_EVENT_GFX_CUTTABLE_TREE', x=x, y=y, elevation=3, movement_type='MOVEMENT_TYPE_LOOK_AROUND',
                         movement_range_x=0, movement_range_y=0, trainer_type='TRAINER_TYPE_NONE', trainer_sight_or_berry_tree_id='0',
                         script='EventScript_CutTree', flag=f'FLAG_TEMP_{11 + n}'))
    for o in events['objects']:
        if o['sprite'] != 'SPRITE_MONSTARBALL':
            continue
        k = 'antidote' if 'ANTIDOTE' in o['flag'] else 'potion'
        name, _, item = ITEMS[k]
        x, y = Rf.to_map(*o['cell'])
        assert r['trav'][y, x]['foot'] == 'open', ('item ball cell is not open ground', x, y)
        objs.append(dict(graphics_id='OBJ_EVENT_GFX_ITEM_BALL', x=x, y=y, elevation=3, movement_type='MOVEMENT_TYPE_FACE_DOWN',
                         movement_range_x=0, movement_range_y=0, trainer_type='TRAINER_TYPE_NONE', trainer_sight_or_berry_tree_id=item,
                         script='Common_EventScript_FindItem', flag=name))
        moves.append(dict(event=f'item ball {item}', cell=[x, y], hgss=o['cell'], flag=name, hgss_flag=o['flag']))
    M = dict(base)
    M['bg_events'] = bgs
    M['object_events'] = objs
    M['warp_events'] = []
    if connections is not None:
        M['connections'] = connections
    (engine / f'data/maps/{MAP}/map.json').write_text(json.dumps(M, indent=2) + '\n')
    (engine / f'data/maps/{MAP}/scripts.inc').write_text(SCRIPTS)
    write_flags(engine)
    return dict(moves=moves, cut_trees=cut)

# --------------------------------------------------------------------------- checks
def decode(engine, words):
    t = Tileset(engine, TS_NAME, PRI_NAME)
    return np.array(t.map_image(words.ravel().tolist(), W).convert('RGB')), t

def report_of(engine, r):
    report = dict(jobs=r['n_jobs'], primary_jobs=r['n_primary_jobs'], secondary_tiles=len(r['sec_tiles']), primary_slot_tiles=len(r['pri_tiles']),
                  secondary_metatiles=len(r['meta_rows']), banks={b: len(p) for b, p in sorted(r['pals'].items())})
    trav, cells = r['trav'], r['cells']
    events = json.loads((SRC / 'hgss-events.json').read_text())
    cut = {Rf.to_map(*o['cell']) for o in events['objects'] if o['sprite'] == 'SPRITE_TREE'}
    hs = hgss_reach(cells, (5, 94))
    ns_cut = reach(trav, (9, H - 1), cut_open=True)
    ns = reach(trav, (9, H - 1), cut=cut)
    hs_map = {Rf.to_map(*p) for p in hs}
    region = lambda p: p[1] < PAD0
    report['reach'] = dict(native_with_cut=len([p for p in ns_cut if region(p)]), native_before_cut=len([p for p in ns if region(p)]),
                           hgss=len(hs), native_only=sorted(list(p) for p in ns_cut if region(p) and p not in hs_map),
                           hgss_only=sorted(list(p) for p in hs_map if p not in ns_cut),
                           north_edge_reached=any(p[1] == 0 for p in ns))
    return report

def install_pair(engine, words_path):
    """Install the map words the joint Route 30/31 pack wrote (pair_pack.py installs the tilesets), with
    this map's events, and check the native render against the assembled art."""
    d = prepare(engine)
    words = np.load(words_path)
    for y in range(H):
        for x in range(W):
            d['trav'][y, x]['metatile'] = int(words[y, x]) & 1023
    r = dict(words=words, trav=d['trav'], cells=d['cells'])
    report = dict(events=write_map(engine, r))
    native, _ = decode(engine, words)
    Image.fromarray(native).save(OEV / 'native.png')
    report['native_pixels_differing'] = int((rgb5(native) != rgb5(d['want'])).any(-1).sum())
    tr = dict(n_jobs=0, n_primary_jobs=0, sec_tiles=[], pri_tiles={}, meta_rows=[], pals={}, trav=d['trav'], cells=d['cells'])
    report['reach'] = report_of(engine, tr)['reach']
    (OUT / 'traversal.json').write_text(json.dumps([d['trav'][y, x] for y in range(H) for x in range(W)], default=int) + '\n')
    (OEV / 'install.json').write_text(json.dumps(report, indent=1, default=int) + '\n')
    print(json.dumps(dict(native_pixels_differing=report['native_pixels_differing'], reach={k: v for k, v in report['reach'].items() if not isinstance(v, list)})))

def main(engine, install):
    r = pack(engine)
    report = report_of(engine, r)
    if install:
        write_primary(engine, r); write_tileset(engine, r); register(engine)
        report['events'] = write_map(engine, r)
        native, _ = decode(engine, r['words'])
        Image.fromarray(native).save(OEV / 'native.png')
        d = (rgb5(native) != rgb5(r['want'])).any(-1)
        report['native_pixels_differing'] = int(d.sum())
    (OUT / 'traversal.json').write_text(json.dumps([r['trav'][y, x] for y in range(H) for x in range(W)], default=int) + '\n')
    (OEV / 'pack.json').write_text(json.dumps(report, indent=1, default=int) + '\n')
    print(json.dumps(report, default=int)[:3000])

if __name__ == '__main__':
    eng = Path(sys.argv[1]).resolve()
    if '--spec' in sys.argv:
        save_pair_spec(eng, sys.argv[sys.argv.index('--spec') + 1])
    elif '--install-words' in sys.argv:
        install_pair(eng, sys.argv[sys.argv.index('--install-words') + 1])
    else:
        main(eng, '--install' in sys.argv)
