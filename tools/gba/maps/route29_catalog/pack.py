"""Route 29: exact native pack onto CherrygrovePrimary, traversal from the decoded HGSS permissions,
layer types, events, and installation into the engine checkout.

    python3 tools/gba/maps/route29_catalog/pack.py ENGINE_CHECKOUT [--install]

Route 29 keeps its live connections to Cherrygrove (west, offset 0) and New Bark (east, offset 6), so
it keeps the towns' primary tileset, CherrygrovePrimary, unchanged, and puts its own art in one
secondary tileset (`route29_hgss`, banks 6-12). A Gen 3 town draws a connected map's first 7 columns
with its own tilesets, so:
  * the seam windows (columns 0-7 and 94-101) resolve to primary metatiles, or to New Bark's own
    secondary metatile ids, which this tileset carries with New Bark's definitions (pinned);
  * every New Bark secondary id that appears in New Bark's first 8 columns is pinned here, so this map
    draws New Bark correctly when the player looks across the seam from Route 29;
Everything else packs exactly (Mahogany's lossless rule): every native pixel keeps its assembled RGB555
colour; tiles that exist in CherrygrovePrimary are reused from it; the rest go into exact banks.

Traversal (source/trace/ledger.json, decoded HGSS permissions): woods under a tree root, the gatehouse,
signs and ledge corners blocked (collision 1, elevation 0 as vanilla); jump-south, jump-east and
jump-west ledges as MB_JUMP_*; tall grass MB_TALL_GRASS; everything else open. Declared adaptations:
woods cells under a crown stay solid, as HGSS has them; the gatehouse doorway stays blocked (no interior
exists).
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
from reference import W, H, PX, COL0, ROW0, WINDOW   # noqa: E402
from tiles import Tileset                            # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route29-catalog'
SRC, EV = ART / 'source', ART / 'evidence'
OUT, OEV = SRC / 'pack', EV / 'pack'
MAP, LAYOUT = 'CherrygroveRoute29Approach', 'LAYOUT_CHERRYGROVE_ROUTE29_APPROACH'
TS_NAME, TS_SYM = 'route29_hgss', 'Route29Hgss'
BASE_REV = '2722eaf7601ec02dc5a684fa8cdef9206c0dc377'
SEC_TILES = 512                     # Route 29 has no animated door, so 1008-1023 are free too
BANKS = list(range(6, 13))
COVERED, NORMAL = 1, 0
# The Route 29 Potion's flag (0x264, previously the hidden Potion's), named for what it now is: HGSS's item ball.
ITEM_FLAG = 'FLAG_ITEM_APOC_ROUTE29_POTION'

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
        self.opaque, self.masked = {}, {}
        for i, ix in enumerate(self.tiles):
            for f in range(4):
                v = ix[:, ::-1] if f & 1 else ix
                v = v[::-1] if f & 2 else v
                for b, pal in enumerate(self.pals):
                    rgb = np.array([pal[k] for k in v.ravel()], np.uint8).reshape(8, 8, 3)
                    key = rgb5(rgb).astype(np.int16)
                    self.masked.setdefault(np.where((v > 0)[..., None], key, -1).tobytes(), (i, f, b))
                    if (v > 0).all():
                        self.opaque.setdefault(key.tobytes(), (i, f, b))
        self.metatiles = [tuple(int(e) for e in m) for m in t.blocks[0]]
        self.attrs = list(t.attrs[0])
        self.render = {}
    def rendered(self, mid, sec=None):
        if mid not in self.render:
            self.render[mid] = np.array(self.t.render(mid).convert('RGB'))
        return self.render[mid]

def entry(tile, flip, bank):
    return tile | ((flip & 1) << 10) | ((flip >> 1) << 11) | (bank << 12)

# --------------------------------------------------------------------------- traversal
def traversal(engine, grid, cells, objs):
    MB = behaviors(engine)
    ledger = cells
    out = np.empty((H, W), object)
    for y in range(H):
        for x in range(W):
            ch = grid[y][x]
            hx, hz = Rf.to_hgss(x, y)
            c = dict(x=x, y=y, code=ch)
            if 0 <= hz < Rf.HH and 0 <= hx < Rf.HW:
                c['hgss'] = dict(type=ledger[hz][hx]['type'], collision=ledger[hz][hx]['collision'], label=ledger[hz][hx]['lab'])
            if ch == 'L':
                c.update(foot='ledge_south', behavior='MB_JUMP_SOUTH', collision=1, elevation=0)
            elif ch == 'E':
                c.update(foot='ledge_east', behavior='MB_JUMP_EAST', collision=1, elevation=0)
            elif ch == 'Q':
                c.update(foot='ledge_west', behavior='MB_JUMP_WEST', collision=1, elevation=0)
            elif ch in 'tBXJs':
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=0)
            elif ch == 'D':
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=0,
                         adaptation="HGSS's warp into the Route 46 gatehouse; no gatehouse interior exists yet, so the doorway stays shut")
            elif ch == 'k':
                # A woods cell under the crown of the tree south of it: solid, as HGSS has it and as the towns'
                # forest edges are (a crown over a solid cell).
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=0)
            elif ch in 'ko':
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3,
                         adaptation="HGSS woods cell under a crown or between trees where no non-overlapping 2x2 root fits "
                                    "(HGSS's offset crowns); open, the player walks behind the crown")
            elif ch == 'G':
                c.update(foot='open', behavior='MB_TALL_GRASS', collision=0, elevation=3)
            else:
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3)
            out[y, x] = c
    # An opened overhang cell may not join two areas HGSS keeps apart (Route 43's check): label HGSS's own
    # open areas with ledges as walls, then open each candidate only if its open neighbours share one area.
    lab = np.zeros((H, W), int); n = 0
    hard = lambda x, y: out[y, x]['foot'] == 'open' and out[y, x]['code'] not in 'ko'
    for y0 in range(H):
        for x0 in range(W):
            if hard(x0, y0) and not lab[y0, x0]:
                n += 1; lab[y0, x0] = n; q = deque([(x0, y0)])
                while q:
                    x, y = q.popleft()
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        a, b = x + dx, y + dy
                        if 0 <= a < W and 0 <= b < H and hard(a, b) and not lab[b, a]:
                            lab[b, a] = n; q.append((a, b))
    changed = True
    while changed:
        changed = False
        for y in range(H):
            for x in range(W):
                c = out[y, x]
                if c['foot'] != 'open' or c['code'] not in 'ko' or lab[y, x]:
                    continue
                ids = {lab[y + dy, x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                       if 0 <= x + dx < W and 0 <= y + dy < H and lab[y + dy, x + dx]}
                if len(ids) > 1:
                    c.update(foot='blocked', collision=1, elevation=0,
                             adaptation='HGSS woods cell no root fits; kept blocked because opening it would join two areas HGSS separates')
                elif ids:
                    lab[y, x] = ids.pop(); changed = True
    for y in range(H):
        for x in range(W):
            c = out[y, x]
            if 'behavior' in c:
                c['behavior_id'] = MB[c['behavior']]
    return out

def reach(trav, start, cut_open=False, cut=()):
    """Cells reachable on foot from start, with Gen 3 ledge rules (jump over a ledge in its direction)."""
    jump = {'ledge_south': (0, 1), 'ledge_east': (1, 0), 'ledge_west': (-1, 0)}
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
    """The same search on HGSS's own permissions (HGSS frame)."""
    types = {0x3B: (0, 1), 0x38: (1, 0), 0x39: (-1, 0)}
    open_ = lambda hx, hz: 0 <= hx < Rf.HW and 0 <= hz < Rf.HH and not cells[hz][hx]['blocked'] and cells[hz][hx]['type'] != 0x6E
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
            if trav[y, x]['foot'] != 'open':
                continue
            sl = np.s_[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
            a = art[sl]
            if not a.any():
                continue
            names = set(owner[sl][a].ravel().tolist()) - {''}
            out[y, x] = any(base[n] > y for n in names)
    return out

# --------------------------------------------------------------------------- pack
def pack(engine):
    OUT.mkdir(parents=True, exist_ok=True); OEV.mkdir(parents=True, exist_ok=True)
    z = np.load(SRC / 'assemble/layers.npz', allow_pickle=True)
    ground, flat, top, owner = z['ground'], z['flat'], z['objects'], z['owner'].astype(object)
    grid = [list(l.split()[1]) for l in (SRC / 'trace/material-grid.txt').read_text().splitlines() if l[:2].isdigit()]
    cells = json.loads((SRC / 'trace/ledger.json').read_text())['cells']
    trav = traversal(engine, grid, cells, None)
    above = above_player(trav, top, owner)
    P = Primary(engine)
    MB = behaviors(engine)
    nbts = Tileset(engine, 'new_bark', 'cherrygrove')
    nbgrid = np.frombuffer((engine / 'data/layouts/NewBarkTown/map.bin').read_bytes(), '<u2').reshape(-1, 36) & 1023

    # ---- pinned secondary metatiles: New Bark's seam ids
    pins = {}                                  # id -> 'nb'
    for mid in sorted({int(v) for v in nbgrid[:, :WINDOW].ravel() if v >= 512}):
        pins[mid] = 'nb'
    fixed_pal = {}                             # bank -> palette (15 colours) required by pinned tiles
    sec_tiles, sec_lookup = [np.zeros((8, 8), np.uint8)], {np.zeros((8, 8), np.uint8).tobytes(): 0}
    def add_tile(ix):
        for f in range(4):
            v = ix[:, ::-1] if f & 1 else ix
            v = v[::-1] if f & 2 else v
            if v.tobytes() in sec_lookup:
                return sec_lookup[v.tobytes()], f
        sec_lookup[ix.tobytes()] = len(sec_tiles); sec_tiles.append(ix.copy())
        return len(sec_tiles) - 1, 0
    pinned_defs = {}
    tiles_src = [np.array(x, np.uint8).reshape(8, 8) & 15 for x in nbts.tiles[1]]
    pals_src = [[tuple(c) for c in p] for p in nbts.pals[1]]
    for mid in pins:
        ents, attr = nbts.blocks[1][mid - 512], nbts.attrs[1][mid - 512]
        new = []
        for e in ents:
            e = int(e); tid, bank = e & 1023, e >> 12
            if bank >= 6:                       # a secondary palette, whether the tile is primary or secondary
                pal = pals_src[bank][1:16]
                assert fixed_pal.get(bank, pal) == pal, f'pinned tiles need two palettes in bank {bank}'
                fixed_pal[bank] = pal
            if tid < 512:
                new.append(e); continue
            ix = tiles_src[tid - 512]
            if e & 0x400: ix = ix[:, ::-1]
            if e & 0x800: ix = ix[::-1]
            t, f = add_tile(ix)
            new.append(entry(512 + t, f, bank))
        pinned_defs[mid] = (tuple(new), int(attr))

    # ---- seam windows: primary metatiles (or New Bark pins on the east side), chosen by their pixels
    want = ground.copy()
    for layer in (flat, top):
        a = layer[..., 3] > 0; want[a] = layer[a, :3]
    window_ids, window_report = {}, []
    cand_w = list(range(512))
    cand_e = list(range(512)) + [m for m, s in pins.items() if s == 'nb']
    nb_render = {m: np.array(nbts.render(m).convert('RGB')) for m, s in pins.items() if s == 'nb'}
    def render_id(m):
        return nb_render[m] if m >= 512 else P.rendered(m)
    renders = {m: render_id(m).astype(np.int16) for m in set(cand_e)}
    for y in range(H):
        for x in list(range(WINDOW)) + list(range(W - WINDOW, W)):
            tgt = want[y * 16:y * 16 + 16, x * 16:x * 16 + 16].astype(np.int16)
            c = trav[y, x]
            cands = cand_w if x < WINDOW else cand_e
            beh = MB[c['behavior']]
            best = min(cands, key=lambda m: (int((renders[m] != tgt).any(-1).sum()),
                                             (P.attrs[m] if m < 512 else pinned_defs[m][1]) & 0xFF != beh, m))
            diff = int((renders[best] != tgt).any(-1).sum())
            window_ids[(x, y)] = best
            if diff:
                window_report.append(dict(cell=[x, y], metatile=f'{best:#05x}', pixels_differing=diff, code=grid[y][x]))

    # Primary metatiles placed by id (seam windows) may draw primary tiles in secondary palette banks
    # (the towns' blossom trees use bank 10): those banks take the towns' palettes.
    cg_pals = [[tuple(c) for c in p] for p in P.t.pals[1]]
    used_primary = {m for m in window_ids.values() if m < 512}
    for m in sorted(used_primary):
        for e in P.metatiles[m]:
            bank = e >> 12
            if bank >= 6 and e:
                pal = cg_pals[bank][1:16]
                assert fixed_pal.get(bank, pal) == pal, f'primary metatile {m:#x} needs bank {bank} with another palette'
                fixed_pal[bank] = pal

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
    sys.path.insert(0, str(HERE.parent))
    from claude_cherrygrove import ground as Gr
    import assemble as As
    yy, xx = np.mgrid[0:H * 16, 0:W * 16]
    lawn_t = Gr.textures()[Gr.GRASS]
    road_t = As.road_texture(engine)
    plains = [lawn_t[yy % 32, xx % 32].astype(np.uint8), road_t[yy % 32, xx % 32].astype(np.uint8)]
    def backing(b, vis, sl):
        """A bottom tile partly hidden under opaque top-layer art: only its visible pixels count (Route 43's
        rule). If they match the plain lawn or road here, the plain (primary) tile is used."""
        if not (~vis).any():
            return b
        for pl in plains:
            if (pl[sl][vis] == b[vis]).all():
                return pl[sl].copy()
        return b
    common = Counter(ground[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].tobytes() for ty in range(H * 2) for tx in range(W * 2)).most_common(1)[0][0]
    filler = np.frombuffer(common, np.uint8).reshape(8, 8, 3)
    for y in range(H):
        for x in range(W):
            if (x, y) in window_ids:
                continue
            q = []
            for qi in range(4):
                sl = np.s_[y * 16 + (qi // 2) * 8:y * 16 + (qi // 2) * 8 + 8, x * 16 + (qi % 2) * 8:x * 16 + (qi % 2) * 8 + 8]
                gpx = ground[sl].copy()
                fl = flat[sl][..., 3] > 0
                upx = np.zeros((8, 8, 3), np.uint8)
                if above[y, x]:
                    gpx[fl] = flat[sl][..., :3][fl]               # drawn above the player: details stay in the ground
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
    # Primary reuse, then exact banks for what remains.
    for k, j in jobs.items():
        if j['layer'] == 0:
            hit = P.opaque.get(j['k5'].tobytes())
        else:
            hit = P.masked.get(j['k5'].tobytes())
        j['primary'] = hit
    rest = [j for j in jobs.values() if j['primary'] is None]
    setof = lambda j: frozenset(map(tuple, j['k5'][j['k5'][..., 0] >= 0].reshape(-1, 3).tolist()))
    over15 = [j for j in rest if len(setof(j)) > 15]
    assert not over15, f'{len(over15)} tiles hold more than 15 colours'
    fixed5 = {b: frozenset(tuple(int(v) >> 3 for v in c) for c in p) for b, p in fixed_pal.items()}
    free = [b for b in BANKS if b not in fixed5]
    sets = [setof(j) for j in rest]
    sys.path.insert(0, str(HERE))
    from banks import pack_sets
    inside_fixed = lambda s: next((b for b, f in fixed5.items() if s <= f), None)
    todo = [s for s in sets if inside_fixed(s) is None]
    newbanks = pack_sets(todo, len(free)) if todo else []
    assert newbanks is not None, 'route art does not fit the free secondary banks'
    pal5 = dict(fixed5)
    for b, s in zip(free, newbanks):
        pal5[b] = frozenset(s)
    order5 = {b: sorted(s) for b, s in pal5.items()}
    for b in fixed_pal:                       # pinned banks keep their slot order
        order5[b] = [tuple(int(v) >> 3 for v in c) for c in fixed_pal[b]]
    for j, s in zip(rest, sets):
        b = inside_fixed(s)
        if b is None:
            b = next(bb for bb in free if bb in pal5 and s <= pal5[bb])
        idx = {c: i + 1 for i, c in enumerate(order5[b])}
        k5 = j['k5']
        ix = np.zeros((8, 8), np.uint8)
        m = k5[..., 0] >= 0
        ix[m] = [idx[tuple(c)] for c in k5[m].reshape(-1, 3).tolist()]
        t, f = add_tile(ix)
        j['entry'] = entry(512 + t, f, b)
    for j in jobs.values():
        if j['primary'] is not None:
            i, f, b = j['primary']
            j['entry'] = entry(i, f, b)
    assert len(sec_tiles) <= SEC_TILES, ('secondary tiles over budget', len(sec_tiles))

    # ---- metatiles and the map
    prim_index = {(P.metatiles[m], P.attrs[m]): m for m in range(512)}
    sec_meta = {}                               # (entries, attr) -> id
    for mid, d in pinned_defs.items():
        sec_meta.setdefault(d, mid)
    next_id = [512]
    def sec_id(key):
        if key in prim_index:
            return prim_index[key]
        if key not in sec_meta:
            while next_id[0] in pins:
                next_id[0] += 1
            sec_meta[key] = next_id[0]; next_id[0] += 1
        return sec_meta[key]
    words = np.zeros((H, W), np.uint16)
    for y in range(H):
        for x in range(W):
            c = trav[y, x]
            if (x, y) in window_ids:
                mid = window_ids[(x, y)]
            else:
                bot = [jobs[b]['entry'] for b, _ in cellplan[(x, y)]]
                tp = [jobs[t]['entry'] if t else 0 for _, t in cellplan[(x, y)]]
                layer = NORMAL if above[y, x] else COVERED
                attr = c['behavior_id'] | (layer << 12)
                mid = sec_id((tuple(bot + tp), attr))
            c['metatile'] = mid
            words[y, x] = mid | (c['collision'] << 10) | (c['elevation'] << 12)
    n_sec = max([m for m in sec_meta.values()] + [511]) - 511
    assert n_sec <= 512, ('secondary metatiles over budget', n_sec)
    meta_rows = [(tuple([0] * 8), 0)] * n_sec
    for key, mid in sec_meta.items():
        meta_rows[mid - 512] = key
    # 8-bit values as the towns' palettes write them (v << 3), so Porymap shows both in the same shades
    pals = {b: [tuple(v << 3 for v in c) for c in order5[b]] for b in order5}
    for b in fixed_pal:
        pals[b] = list(fixed_pal[b])
    return dict(words=words, trav=trav, sec_tiles=sec_tiles, pals=pals, meta_rows=meta_rows, pins=pins,
                window_report=window_report, n_jobs=len(jobs), n_primary_jobs=sum(j['primary'] is not None for j in jobs.values()),
                want=want, grid=grid, cells=cells)

# --------------------------------------------------------------------------- write
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
        cols = r['pals'].get(b, [])
        cols = list(cols) + [(0, 0, 0)] * (15 - len(cols))
        (d / 'palettes' / f'{b:02}.pal').write_text('\r\n'.join(['JASC-PAL', '0100', '16', '0 0 0'] + [f'{c[0]} {c[1]} {c[2]}' for c in cols[:15]]) + '\r\n')
    (d / 'metatiles.bin').write_bytes(b''.join(struct.pack('<8H', *k[0]) for k in r['meta_rows']))
    (d / 'metatile_attributes.bin').write_bytes(struct.pack('<%dH' % len(r['meta_rows']), *[k[1] for k in r['meta_rows']]))

def register(engine):
    h = engine / 'src/data/tilesets/headers.h'; s = h.read_text()
    if f'gTileset_{TS_SYM} ' not in s and f'gTileset_{TS_SYM} =' not in s:
        s = s.replace('// End Claude routes\n', f'const struct Tileset gTileset_{TS_SYM} = {{ .isCompressed = TRUE, .isSecondary = TRUE, .tiles = gTilesetTiles_{TS_SYM}, .palettes = gTilesetPalettes_{TS_SYM}, .metatiles = gMetatiles_{TS_SYM}, .metatileAttributes = gMetatileAttributes_{TS_SYM}, .callback = NULL }};\n// End Claude routes\n', 1); h.write_text(s)
    g = engine / 'src/data/tilesets/graphics.h'; s = g.read_text()
    if f'gTilesetTiles_{TS_SYM}[]' not in s:
        s = s.rstrip('\n') + f'\n\nconst u32 gTilesetTiles_{TS_SYM}[] = INCGFX_U32("data/tilesets/secondary/{TS_NAME}/tiles.png", ".4bpp.fastSmol");\nconst u16 gTilesetPalettes_{TS_SYM}[][16] = {{\n' + ''.join(f'INCGFX_U16("data/tilesets/secondary/{TS_NAME}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n'; g.write_text(s)
    m = engine / 'src/data/tilesets/metatiles.h'; s = m.read_text()
    if f'gMetatiles_{TS_SYM}[]' not in s:
        s = s.rstrip('\n') + f'\nconst u16 gMetatiles_{TS_SYM}[] = INCBIN_U16("data/tilesets/secondary/{TS_NAME}/metatiles.bin");\nconst u16 gMetatileAttributes_{TS_SYM}[] = INCBIN_U16("data/tilesets/secondary/{TS_NAME}/metatile_attributes.bin");\n'; m.write_text(s)

def write_map(engine, r):
    words = r['words']
    trav_ok = lambda x, y: r['trav'][y, x]['foot'] == 'open'
    (engine / f'data/layouts/{MAP}/map.bin').write_bytes(struct.pack('<%dH' % (W * H), *words.ravel().tolist()))
    lj = engine / 'data/layouts/layouts.json'; L = json.loads(lj.read_text())
    for l in L['layouts']:
        if l['id'] == LAYOUT:
            l['secondary_tileset'] = 'gTileset_' + TS_SYM; l['width'] = W; l['height'] = H
    lj.write_text(json.dumps(L, indent=2) + '\n')
    base = json.loads(subprocess.check_output(['git', '-C', str(engine), 'show', f'{BASE_REV}:data/maps/{MAP}/map.json']))
    events = json.loads((SRC / 'hgss-events.json').read_text())
    signs = sorted((Rf.to_map(*s['cell']) for s in events['signs'] if s['bg_type'] == 1))
    moves = []
    bgs = []
    for b in base['bg_events']:
        b = dict(b)
        if b['type'] == 'sign':
            old = (b['x'], b['y']); b['x'], b['y'] = signs[-1]
            moves.append(dict(event='route sign (east)', old=list(old), new=list(signs[-1]), note="HGSS's east sign (86,13)"))
        elif b['type'] == 'hidden_item':
            moves.append(dict(event='hidden Potion', old=[b['x'], b['y']], new=None,
                              note="removed: HGSS has no hidden item here; its Potion is the item ball below"))
            continue
        bgs.append(b)
    west = dict(type='sign', x=signs[0][0], y=signs[0][1], elevation=0, player_facing_dir='BG_EVENT_PLAYER_FACING_ANY',
                script=next(b['script'] for b in base['bg_events'] if b['type'] == 'sign'))
    bgs.insert(1, west)
    moves.append(dict(event='route sign (west)', new=list(signs[0]), note="HGSS's west sign (5,13); reuses the route's existing sign script"))
    M = dict(base)
    M['bg_events'] = bgs
    cut = [Rf.to_map(*o['cell']) for o in events['objects'] if o['sprite'] == 'SPRITE_TREE']
    M['object_events'] = [o for o in base.get('object_events', []) if o.get('graphics_id') != 'OBJ_EVENT_GFX_CUTTABLE_TREE'] + [
        dict(graphics_id='OBJ_EVENT_GFX_CUTTABLE_TREE', x=x, y=y, elevation=3, movement_type='MOVEMENT_TYPE_LOOK_AROUND',
             movement_range_x=0, movement_range_y=0, trainer_type='TRAINER_TYPE_NONE', trainer_sight_or_berry_tree_id='0',
             script='EventScript_CutTree', flag=f'FLAG_TEMP_{11 + n}') for n, (x, y) in enumerate(cut)]
    # HGSS's item ball (obj_R29_monstarball, std_itemball_r29_potion) on its own cell, as Emerald's item balls are.
    ball = next(o for o in events['objects'] if o['sprite'] == 'SPRITE_MONSTARBALL')
    bx, by = Rf.to_map(*ball['cell'])
    assert r['trav'][by, bx]['foot'] == 'open', ('item ball cell is not open ground', bx, by)
    M['object_events'] = [o for o in M['object_events'] if o.get('graphics_id') != 'OBJ_EVENT_GFX_ITEM_BALL'] + [
        dict(graphics_id='OBJ_EVENT_GFX_ITEM_BALL', x=bx, y=by, elevation=3, movement_type='MOVEMENT_TYPE_FACE_DOWN',
             movement_range_x=0, movement_range_y=0, trainer_type='TRAINER_TYPE_NONE', trainer_sight_or_berry_tree_id='ITEM_POTION',
             script='Common_EventScript_FindItem', flag=ITEM_FLAG)]
    moves.append(dict(event='item ball Potion', new=[bx, by], note=f"HGSS's item ball {ball['cell']} ({ball['flag']}); flag {ITEM_FLAG}"))
    (engine / f'data/maps/{MAP}/map.json').write_text(json.dumps(M, indent=2) + '\n')
    return dict(moves=moves, cut_trees=cut, item_ball=[bx, by])

# --------------------------------------------------------------------------- checks
def decode(engine, words):
    t = Tileset(engine, TS_NAME, 'cherrygrove')
    return np.array(t.map_image(words.ravel().tolist(), W).convert('RGB')), t

def main(engine, install):
    r = pack(engine)
    report = dict(jobs=r['n_jobs'], primary_jobs=r['n_primary_jobs'], secondary_tiles=len(r['sec_tiles']),
                  secondary_metatiles=len(r['meta_rows']), banks={b: len(p) for b, p in sorted(r['pals'].items())},
                  pinned=dict(Counter(r['pins'].values())), window_cells_inexact=len(r['window_report']))
    trav = r['trav']
    # Reachability: native from both town edges versus HGSS's own permissions.
    cells = r['cells']
    hs = hgss_reach(cells, (0, 15))
    events = json.loads((SRC / 'hgss-events.json').read_text())
    cut = {Rf.to_map(*o['cell']) for o in events['objects'] if o['sprite'] == 'SPRITE_TREE'}
    ns = reach(trav, (0, 18), cut=cut)
    ns_cut = reach(trav, (0, 18), cut_open=True)
    hs_map = {Rf.to_map(*p) for p in hs}
    region = lambda p: Rf.WINDOW <= p[0] < W - Rf.WINDOW
    only_native = sorted(p for p in ns_cut if region(p) and p not in hs_map)
    only_hgss = sorted(p for p in hs_map if region(p) and p not in ns_cut)
    report['reach'] = dict(native_with_cut=len(ns_cut), native_before_cut=len(ns), hgss=len(hs),
                           native_only=[list(p) for p in only_native], hgss_only=[list(p) for p in only_hgss],
                           east_edge_reached=any(p[0] == W - 1 for p in ns), )
    if install:
        write_tileset(engine, r); register(engine)
        report['events'] = write_map(engine, r)
        native, _ = decode(engine, r['words'])
        Image.fromarray(native).save(OEV / 'native.png')
        want = r['want']
        d = (rgb5(native[:H * PX]) != rgb5(want[:H * PX])).any(-1)
        win = np.zeros_like(d)
        for x in list(range(WINDOW)) + list(range(W - WINDOW, W)):
            win[:, x * PX:(x + 1) * PX] = True
        report['native_pixels_differing_outside_windows'] = int((d & ~win).sum())
        report['native_pixels_differing_in_windows'] = int((d & win).sum())
    (OUT / 'traversal.json').write_text(json.dumps([trav[y, x] for y in range(H) for x in range(W)], default=int) + '\n')
    (OEV / 'pack.json').write_text(json.dumps(dict(report, window_inexact=r['window_report']), indent=1, default=int) + '\n')
    print(json.dumps(report, default=int)[:3000])

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), '--install' in sys.argv)
