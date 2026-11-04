"""Route 32 (HGSS textures): pack compose.py's art into two connected native maps and install them.

    python3 tools/gba/maps/route32_hgss/pack.py ENGINE [--install]

Why two maps: HGSS's own textures for the whole route need about 1,960 distinct 8x8 tiles; one Gen 3 map
holds 1,024 (512 primary + 512 secondary). AGENTS.md: adapt the technique to each map's hardware budget.
The route is split at the Magnet Train viaduct (native row SPLIT, the middle of the deck), where both sides
are the deck's own repeating rows:

    JohtoRoute32       native rows 0 .. SPLIT-1   (Violet City to the viaduct)
    JohtoRoute32South  native rows SPLIT .. 165   (the viaduct to the Union Cave forecourt)

Each map has its own primary and secondary tileset. A Gen 3 map draws a connected map's nearest rows with
its own tilesets, so every cell within WINDOW rows of the seam has the same metatile id, the same tiles and
the same colours in both maps (palette banks 0-5 are identical in both; seam tiles use only those banks).
North's rows 0-4 are Violet City's own metatiles at Violet's ids, and north also defines every Violet
metatile a player on those rows can see (Violet's palettes 0, 1, 3 and 11 at the same banks).

Palettes: per-tile clustering in CIE Lab (15 colours a bank). Tiles: exact dedupe with flips, then
near-duplicate merging under explicit limits until each map fits: only within the same material class and
layer, mean and worst-pixel Lab error capped, never for stairs, ledges, doors, signs, buildings, the cave
mouth, top-layer art or the seam (they can be merge targets). Every merge is logged.

Writes source/pack/{north,south}/... (tilesets, layouts) and evidence/pack/pack.json; with --install,
writes the tilesets, layouts, maps, Center, flags, map section and connections into ENGINE.
"""
from __future__ import annotations
import json, re, struct, sys
from collections import Counter, defaultdict, deque
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import reference as Rf                               # noqa: E402
from reference import W, H, PX, COL0, ROW0           # noqa: E402
from tiles import Tileset                            # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route32-hgss'
SRC, EV = ART / 'source', ART / 'evidence'
OUT, OEV = SRC / 'pack', EV / 'pack'

SPLIT = 89                     # first native row of the south map (viaduct deck rows 88.5-93.5)
WINDOW = 7                     # rows either side of the seam drawn by the other map's tilesets
MAPS = {
    'north': dict(name='JohtoRoute32', map_id='MAP_JOHTO_ROUTE32', layout='LAYOUT_JOHTO_ROUTE32',
                  rows=(0, SPLIT), ts='route32_north', sym='Route32North'),
    'south': dict(name='JohtoRoute32South', map_id='MAP_JOHTO_ROUTE32_SOUTH', layout='LAYOUT_JOHTO_ROUTE32_SOUTH',
                  rows=(SPLIT, H), ts='route32_south', sym='Route32South'),
}
CENTER, UPSTAIRS = 'Route32PokemonCenter', 'Route32CenterUpstairs'
VIOLET_BANKS = (0, 1, 3, 11)
VIOLET_SEEN_ROWS = range(64, 72)
SHARED_FREE = (2, 4, 5, 6, 7)
FAMILY = {**{n: 'lawn' for n in ('egrass', 'egrass_u', 'egrass_v', 'egrass_ri', 'egrass_ro', 'grass01_a')},
          **{n: 'flower' for n in ('flower01', 'flower02', 'flower03', 'etc_a', 'grass02', 'grass02_r')},
          **{n: 'road' for n in ('road01', 'road01_r', 'road01_sub')}, **{n: 'tree' for n in ('tree01gs', 'tree01_un', 'tree01_re')},
          'grass01gs': 'tallgrass', **{n: 'rock' for n in ('wall01_d', 'wall01_g', 'wall01_h', 'cliff01gs', 'slope', 'allpeakgs', 'allpeak_pgs', 'cavehole', 'rock01')},
          **{n: 'sea' for n in ('sea_un', 'sea_on', 'pond_line', 'sea_rock', 'sea_rock_m')}, **{n: 'pier' for n in ('bridge_b', 'bridge_c')}}
NBANK = 13
MERGE_MEAN_MAX = 11.0           # mean Lab error a merged tile may carry
MERGE_PIXEL_MAX = 30.0         # worst single pixel
PROTECT = set('^LQEJsDwCHpP')  # grid codes never merged away
CLASS = {'R': 'rock', 'X': 'rock', 'J': 'rock', 'T': 'tree', 'c': 'tree', '~': 'sea', 'O': 'sea', 'B': 'pier',
         'g': 'lawn', 'f': 'lawn', 'l': 'lawn', 'v': 'lawn', 'G': 'grass', 'd': 'road'}
ITEMS = dict(repel=('FLAG_ITEM_APOC_ROUTE32_REPEL', 'FLAG_UNUSED_0x26A', 'ITEM_REPEL', 'FLAG_HIDE_ITEMBALL_R32_REPEL'),
             great_ball=('FLAG_ITEM_APOC_ROUTE32_GREAT_BALL', 'FLAG_UNUSED_0x26B', 'ITEM_GREAT_BALL', 'FLAG_HIDE_ITEMBALL_R32_GREAT_BALL'),
             shell_bell=('FLAG_ITEM_APOC_ROUTE32_SHELL_BELL', 'FLAG_UNUSED_0x26C', 'ITEM_SHELL_BELL', 'FLAG_HIDE_ITEMBALL_R32_SHELL_BELL'),
             heart_scale=('FLAG_HIDDEN_ITEM_APOC_ROUTE32_HEART_SCALE', 'FLAG_UNUSED_0x26D', 'ITEM_HEART_SCALE', 'std_hiddenitem_r32_heart_scale'),
             hidden_great_ball=('FLAG_HIDDEN_ITEM_APOC_ROUTE32_GREAT_BALL', 'FLAG_UNUSED_0x26E', 'ITEM_GREAT_BALL', 'std_hiddenitem_r32_great_ball'),
             super_potion=('FLAG_HIDDEN_ITEM_APOC_ROUTE32_SUPER_POTION', 'FLAG_UNUSED_0x26F', 'ITEM_SUPER_POTION', 'std_hiddenitem_r32_super_potion'))
SIGN_SCRIPTS = {'Ruins of Alph': 'JohtoRoute32_AlphSign', 'Azalea': 'JohtoRoute32_RouteSign', 'Union Cave': 'JohtoRoute32_CaveSign'}

def entry(tile, hf, vf, bank): return tile | (hf << 10) | (vf << 11) | (bank << 12)

# --------------------------------------------------------------------------- colour
def lab(c):
    c = np.asarray(c, float) / 255
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    xyz = c @ np.array([[0.4124, 0.2126, 0.0193], [0.3576, 0.7152, 0.1192], [0.1805, 0.0722, 0.9505]])
    xyz /= np.array([0.95047, 1, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)

def to5(c): return (np.asarray(c).astype(np.int64) >> 3) << 3

def kmeans_w(cols, wts, k, seed=0, iters=25):
    """Weighted k-means over distinct colours (RGB, already 5-bit). Returns <= k RGB colours."""
    cols = np.asarray(cols); wts = np.asarray(wts, float)
    if len(cols) <= k:
        return [tuple(int(v) for v in c) for c in cols]
    L = lab(cols)
    rng = np.random.default_rng(seed)
    cen = [L[np.argmax(wts)]]
    for _ in range(k - 1):
        d = ((L[:, None] - np.array(cen)[None]) ** 2).sum(-1).min(1) * wts
        cen.append(L[rng.choice(len(L), p=d / d.sum())] if d.sum() > 0 else L[rng.integers(len(L))])
    cen = np.array(cen)
    for _ in range(iters):
        a = ((L[:, None] - cen[None]) ** 2).sum(-1).argmin(1)
        new = np.array([(L[a == j] * wts[a == j, None]).sum(0) / wts[a == j].sum() if (a == j).any() else cen[j] for j in range(k)])
        if np.allclose(new, cen):
            break
        cen = new
    def lloyd(cen):
        for _ in range(iters):
            a = ((L[:, None] - cen[None]) ** 2).sum(-1).argmin(1)
            new = np.array([(L[a == j] * wts[a == j, None]).sum(0) / wts[a == j].sum() if (a == j).any() else cen[j] for j in range(len(cen))])
            if np.allclose(new, cen):
                break
            cen = new
        return cen
    def cost(cen):
        d = ((L[:, None] - cen[None]) ** 2).sum(-1).min(1)
        return float((d * wts).sum() + 4.0 * wts.mean() * d.max() * 8), d
    # farthest-colour swaps: give an outlying colour (a white petal, a trim) its own slot when that helps
    best_c, d = cost(cen)
    for _ in range(12):
        far = int(np.argmax(d))
        if d[far] < 36:
            break
        a = ((L[:, None] - cen[None]) ** 2).sum(-1).argmin(1)
        load = np.array([wts[a == j].sum() for j in range(len(cen))])
        trial = cen.copy(); trial[int(load.argmin())] = L[far]
        trial = lloyd(trial)
        c2, d2 = cost(trial)
        if c2 < best_c:
            cen, best_c, d = trial, c2, d2
        else:
            break
    a = ((L[:, None] - cen[None]) ** 2).sum(-1).argmin(1)
    out = []
    for j in range(k):                                  # each centre becomes its heaviest real member (exact source colour)
        m = a == j
        if m.any():
            idx = np.nonzero(m)[0]
            dd = ((L[idx] - cen[j]) ** 2).sum(-1) / (wts[idx] + 1e-9) ** 0.25
            out.append(tuple(int(v) for v in cols[idx[dd.argmin()]]))
    return list(dict.fromkeys(out))

# --------------------------------------------------------------------------- engine data
def behaviors(engine):
    names = re.findall(r'^\s+(MB_[A-Z0-9_]+),', (engine / 'include/constants/metatile_behaviors.h').read_text(), re.M)
    return {n: i for i, n in enumerate(names)}

class Violet:
    def __init__(self, engine):
        t = Tileset(engine, 'violet_city', 'violet_city')
        self.tiles = [[np.array(x, np.uint8).reshape(8, 8) & 15 for x in t.tiles[k]] for k in (0, 1)]
        self.pals = [[tuple(c) for c in p] for p in t.pals[0][:6]] + [[tuple(c) for c in p] for p in t.pals[1][6:16]]
        self.meta = [tuple(int(e) for e in m) for m in t.blocks[0]] + [tuple(int(e) for e in m) for m in t.blocks[1]]
        self.attrs = list(t.attrs[0]) + list(t.attrs[1])
        b = (engine / 'data/layouts/VioletCity/map.bin').read_bytes()
        self.words = np.array(struct.unpack('<%dH' % (len(b) // 2), b)).reshape(-1, 80)
    def tile(self, i):
        return self.tiles[0][i] if i < 512 else self.tiles[1][i - 512]
    def mid(self, i):
        return self.meta[i] if i < 512 else self.meta[512 + i - 512] if False else (self.meta[i] if i < len(self.meta) else None)

def pinned_ids(V):
    ids = set()
    for y in range(Rf.VIOLET_ID_ROWS):
        for x in range(W):
            vx, vy = Rf.pad_source(x, y)
            ids.add(int(V.words[vy, vx]) & 1023)
    for vy in VIOLET_SEEN_ROWS:
        for vx in range(0, min(V.words.shape[1], W + Rf.VIOLET_SHIFT + 8)):
            ids.add(int(V.words[vy, vx]) & 1023)
    return sorted(ids)

def violet_meta(V, mid):
    """Violet's metatile entries for id mid (its tilesets: 512 primary + secondary)."""
    if mid < 512:
        return V.meta[mid], V.attrs[mid]
    k = 512 + (mid - 512)
    return V.meta[k], V.attrs[k]

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
            if ch in 'Pp' and y < Rf.VIOLET_ID_ROWS:
                vx, vy = Rf.pad_source(x, y)
                v = int(V.words[vy, vx])
                c.update(foot='open' if (v >> 10) & 3 == 0 else 'blocked', behavior=None, collision=(v >> 10) & 3,
                         elevation=v >> 12, metatile=v & 1023, source=f'Violet ({vx},{vy})')
            elif ch == 'L':
                c.update(foot='ledge_south', behavior='MB_JUMP_SOUTH', collision=1, elevation=0)
            elif ch == 'E':
                c.update(foot='ledge_east', behavior='MB_JUMP_EAST', collision=1, elevation=0)
            elif ch == 'Q':
                c.update(foot='ledge_west', behavior='MB_JUMP_WEST', collision=1, elevation=0)
            elif ch == '~':
                c.update(foot='water', behavior='MB_OCEAN_WATER', collision=0, elevation=1)
            elif ch in 'XO' and hz >= 0 and cells[hz][hx]['material'].startswith('sea'):
                c.update(foot='blocked', behavior='MB_OCEAN_WATER' if ch == 'X' else 'MB_NORMAL', collision=1, elevation=1,
                         note="HGSS's blocked sea cell" if ch == 'X' else 'sea boulder')
            elif ch == 'D':
                c.update(foot='door', behavior='MB_NON_ANIMATED_DOOR', collision=0, elevation=3,
                         adaptation='non-animated door: no door animation is registered for these tilesets')
            elif ch == 'w':
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=0,
                         adaptation="HGSS's Ruins of Alph gatehouse doorway; no gatehouse interior exists yet, so it stays shut")
            elif ch == 'C':
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=0,
                         adaptation="HGSS's Union Cave mouth; Union Cave is not on this branch, so it stays shut")
            elif ch in 'TRHsJXO':
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=0)
            elif ch == 'G':
                c.update(foot='open', behavior='MB_TALL_GRASS', collision=0, elevation=3)
            else:                                       # g d f l v B ^ c
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3)
            if c['behavior']:
                c['behavior_id'] = MB[c['behavior']]
            out[y, x] = c
    return out

LEDGES = {'ledge_south': (0, 1), 'ledge_east': (1, 0), 'ledge_west': (-1, 0)}

def reach(trav, start, cut=()):
    seen = {start}; q = deque([start])
    walk = lambda p: 0 <= p[0] < W and 0 <= p[1] < H and trav[p[1], p[0]]['foot'] in ('open', 'door') and p not in cut
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

# --------------------------------------------------------------------------- pack
def membership(y):
    """Which maps' tilesets a native row's cells must be in."""
    m = set()
    if y < SPLIT + WINDOW:
        m.add('north')
    if y >= SPLIT - WINDOW:
        m.add('south')
    return m

def seam_row(y): return SPLIT - WINDOW <= y < SPLIT + WINDOW

def pack(engine):
    bottom = np.array(Image.open(SRC / 'compose/bottom.png').convert('RGB'))
    top = np.array(Image.open(SRC / 'compose/top.png').convert('RGBA'))
    grid = [l[6:] for l in (SRC / 'trace/material-grid.txt').read_text().splitlines() if not l.startswith('#')]
    cells = json.loads((SRC / 'trace/ledger.json').read_text())['cells']
    V = Violet(engine)
    trav = traversal(engine, grid, cells, V)
    # art labels: the cells the shared buildings (G02, C06) actually cover, whatever HGSS has beneath them
    art_grid = [list(r) for r in grid]
    comp = json.loads((SRC / 'compose/compose.json').read_text())
    for o in comp['objects']:
        size = 112 if 'G02' in o['name'] else 80 if 'C06' in o['name'] else 0
        for cy in range(o['xy'][1] // PX, (o['xy'][1] + size) // PX):
            for cx in range(o['xy'][0] // PX, (o['xy'][0] + size) // PX):
                if art_grid[cy][cx] not in 'Dw':
                    art_grid[cy][cx] = 'H'
    art_grid = [''.join(r) for r in art_grid]
    pins = pinned_ids(V)
    bottom5, top5 = to5(bottom), to5(top[..., :3])
    alpha = top[..., 3] > 127
    want = bottom5.copy(); want[alpha] = top5[alpha]

    # ---- quads: (y, x, layer, qy, qx)
    quads = []                                         # dict(key, rgb (8,8,3), mask (8,8), maps, seam, cls, protect)
    for y in range(H):
        if grid[y][0] in 'Pp' and all(grid[y][x] in 'Pp' for x in range(W)):
            continue                                   # Violet's metatiles by id
        for x in range(W):
            ch = art_grid[y][x]
            for layer in (0, 1):
                for q in range(4):
                    py, px_ = y * PX + (q // 2) * 8, x * PX + (q % 2) * 8
                    if layer == 0:
                        rgb = bottom5[py:py + 8, px_:px_ + 8]; mask = np.ones((8, 8), bool)
                        if alpha[py:py + 8, px_:px_ + 8].all():
                            rgb = None                 # hidden under an opaque top tile: the blank tile
                    else:
                        mask = alpha[py:py + 8, px_:px_ + 8]
                        rgb = top5[py:py + 8, px_:px_ + 8] if mask.any() else None
                    quads.append(dict(y=y, x=x, layer=layer, q=q, rgb=rgb, mask=mask, maps=membership(y), seam=seam_row(y),
                                      cls=CLASS.get(ch, 'feature:' + ch), protect=ch in PROTECT or layer == 1))
    live = [qd for qd in quads if qd['rgb'] is not None]

    # ---- palettes
    vpal = {b: [to5(c) for c in V.pals[b][1:16]] for b in VIOLET_BANKS}
    vpal = {b: [tuple(int(v) for v in c) for c in cs] for b, cs in vpal.items()}
    fixed = {('north', b): vpal[b] for b in VIOLET_BANKS}
    # Banks 0-7 are identical in both maps (0, 1, 3 Violet's; 2, 4-7 fitted): seam tiles use only these.
    free = list(BANK_PLAN)
    banks = dict(fixed)
    # distinct quads (content, scope) for fitting; each carries its multiplicity
    groups = {}
    for qd in live:
        k = (qd['rgb'].tobytes(), qd['mask'].tobytes(), qd['seam'], tuple(sorted(qd['maps'])))
        g = groups.get(k)
        if g is None:
            c = qd['rgb'][qd['mask']]
            u, n = np.unique(c.reshape(-1, 3), axis=0, return_counts=True)
            g = groups[k] = dict(u=u, n=n, L=lab(u), seam=qd['seam'], maps=qd['maps'], w=0.0, members=[])
        g['w'] += 4.0 if qd['protect'] else 1.0
        g['members'].append(qd)
    G = list(groups.values())
    print(len(live), 'quads,', len(G), 'distinct', flush=True)
    fam = families(art_grid, top)
    for g in G:
        g['fam'] = Counter(fam[(q['y'], q['x'], q['layer'], q['q'])] for q in g['members']).most_common(1)[0][0]
    core = plan_banks(G, banks, art_grid)
    def allowed_g(g):
        if g['seam']:
            return [k for k in banks if k[0] == 'shared']
        m = next(iter(g['maps']))
        return [k for k in banks if k[0] in ('shared', m)]
    def errs(g, ks, PL):
        out = []
        for k in ks:
            d = ((g['L'][:, None] - PL[k][None]) ** 2).sum(-1).min(1)
            out.append(float((d * np.sqrt(g['n'])).sum() + 4.0 * d.max()))
        return out
    def sticky(PL):
        """One material, one bank: within each material class (per map scope), tiles stay in the class's
        majority bank unless it represents them clearly worse, so a road or a cliff cap doesn't change tone
        from one 8x8 square to the next (GBA_MAP_RECONSTRUCTION.md: coordinate palette ramps across banks)."""
        load = defaultdict(Counter)
        for g in G:
            g['ck'] = (g['fam'], g['seam'], tuple(sorted(g['maps'])))
            load[g['ck']][g['bank']] += g['w'] * g['n'].sum()
        moved = 0
        for g in G:
            sb = load[g['ck']].most_common(1)[0][0]
            if sb == g['bank'] or sb not in allowed_g(g):
                continue
            e_best, e_s = errs(g, [g['bank'], sb], PL)
            if e_s <= 1.35 * e_best + 40:
                g['bank'] = sb; moved += 1
        return moved
    best = (float('inf'), None)
    for it in range(12):
        PL = {k: lab(np.array(v)) for k, v in banks.items()}
        total = 0.0
        for g in G:
            ks = allowed_g(g)
            e = errs(g, ks, PL)
            j = int(np.argmin(e)); g['bank'] = ks[j]
        sticky(PL)
        total = sum(errs(g, [g['bank']], PL)[0] * g['w'] for g in G)
        if total < best[0]:
            best = (total, dict(banks))
        for k in free:
            grp = [g for g in G if g['bank'] == k]
            if grp:
                banks[k] = refit(grp, core[k])
        print(f'palette pass {it}: weighted error {total / sum(g["n"].sum() * g["w"] for g in G):.2f}', flush=True)
    banks.clear(); banks.update(best[1])
    PL = {k: lab(np.array(v)) for k, v in banks.items()}
    for g in G:
        ks = allowed_g(g)
        g['bank'] = ks[int(np.argmin(errs(g, ks, PL)))]
    print('sticky moves', sticky(PL), flush=True)
    for g in G:
        for qd in g['members']:
            qd['bank'] = g['bank']

    # ---- overflow: a square whose colours its bank can't hold puts the missing ones in the cell's upper tile, both
    # layers below the player (METATILE_LAYER_TYPE_COVERED), so the picture keeps them. Only cells with no art above
    # the player and outside the seam. Features first (stairs, cave mouth, doors, buildings, signs), then the worst
    # remaining squares, up to OVERFLOW_CAP a map (each split costs a tile, which merging has to win back).
    covered = set()
    cellq = defaultdict(dict)
    for qd in quads:
        cellq[(qd['x'], qd['y'])][(qd['layer'], qd['q'])] = qd
    PLb = {k: lab(np.array(v)) for k, v in banks.items()}
    cand = []
    for (x, y), cq in cellq.items():
        if seam_row(y) or y < Rf.VIOLET_ID_ROWS or any(cq[(1, q)]['rgb'] is not None for q in range(4)):
            continue
        feature = art_grid[y][x] in '^CDHwsJLEQ'
        for q in range(4):
            qd = cq[(0, q)]
            if qd['rgb'] is None:
                continue
            Lq = lab(qd['rgb'].reshape(-1, 3))
            dA = ((Lq[:, None] - PLb[qd['bank']][None]) ** 2).sum(-1).min(1)
            worst = float(np.sqrt(dA).max())
            if worst < (6 if feature else 12):
                continue
            m = next(iter(qd['maps']))
            ks = [k for k in banks if k[0] in ('shared', m)]
            D = {k: ((Lq[:, None] - PLb[k][None]) ** 2).sum(-1).min(1) for k in ks}
            best = None
            for ka in ks:                               # the best pair: lower tile in ka, missing colours above in kb
                for kb in ks:
                    if kb == ka:
                        continue
                    use = D[kb] + 4 < D[ka]
                    e = np.where(use, D[kb], D[ka])
                    if best is None or e.sum() < best[0].sum():
                        best = (e, kb, use, ka)
            if best is None or not best[2].any() or best[0].sum() > 0.7 * dA.sum():
                continue
            gain = float(dA.sum() - best[0].sum())
            cand.append((not feature, -gain, m, x, y, q, best[1], best[2], best[3]))
    cand.sort(key=lambda c: c[:2])
    used = Counter()
    for nf, g, m, x, y, q, kb, use, ka in cand:
        if nf and used[m] >= OVERFLOW_CAP[m]:
            continue
        qd = cellq[(x, y)][(0, q)]; top_q = cellq[(x, y)][(1, q)]
        qd['bank'] = ka
        top_q.update(rgb=qd['rgb'].copy(), mask=use.reshape(8, 8), bank=kb, protect=True)
        live.append(top_q)
        covered.add((x, y)); used[m] += 1
    print('overflow split quads', dict(used), 'cells', len(covered), 'candidates', len(cand), flush=True)

    # ---- quantize: index tiles (index 0 = transparent, 1..15 = bank colours)
    for qd in live:
        P = np.array(banks[qd['bank']]); PL = lab(P)
        flat = qd['rgb'].reshape(-1, 3)
        idx = ((lab(flat)[:, None] - PL[None]) ** 2).sum(-1).argmin(1) + 1
        idx = idx.reshape(8, 8).astype(np.uint8)
        idx[~qd['mask']] = 0
        qd['idx'] = idx
        mk = qd['mask'].ravel()
        qd['qerr'] = float(np.sqrt(((lab(flat[mk]) - PL[idx.ravel()[mk] - 1]) ** 2).sum(-1)).mean())

    qimg = want.copy()
    for qd in live:
        P = np.concatenate([[[0, 0, 0]], np.array(banks[qd['bank']])])
        py, px_ = qd['y'] * PX + (qd['q'] // 2) * 8, qd['x'] * PX + (qd['q'] % 2) * 8
        reg = qimg[py:py + 8, px_:px_ + 8]
        reg[qd['mask']] = P[qd['idx']][qd['mask']]
    OEV.mkdir(parents=True, exist_ok=True)
    Image.fromarray(qimg.astype(np.uint8)).save(OEV / 'quantized-before-merge.png')

    # ---- tiles per map: appearances (pattern, bank) -> patterns, then merging to budget
    result = {}
    vtiles = {}
    for mid in pins:                                   # Violet's tiles (north only), by their own patterns
        ent, _ = violet_meta(V, mid)
        for e in ent:
            t = e & 1023
            vtiles[t] = V.tile(t)
    for m in ('north', 'south'):
        result[m] = tiles_for(m, live, banks, vtiles if m == 'north' else {})

    # ---- metatiles
    cellmeta = {}
    def quad_entry(m, qd):
        if qd['rgb'] is None:
            return 0
        tile, hf, vf, bank = result[m]['quad'][id(qd)]
        return entry(tile, hf, vf, bank)
    byxy = defaultdict(list)
    for qd in quads:
        byxy[(qd['x'], qd['y'])].append(qd)
    meta = {m: {} for m in MAPS}                      # map -> {key: id}
    words = {m: np.zeros((MAPS[m]['rows'][1] - MAPS[m]['rows'][0], W), np.int64) for m in MAPS}
    # Violet pins (north): Violet's entries with north's tile ids
    ids = {m: {} for m in MAPS}                       # map -> {id: (entries, attr)}
    for mid in pins:
        ent, attr = violet_meta(V, mid)
        ids['north'][mid] = (tuple(entry(result['north']['violet'][e & 1023], (e >> 10) & 1, (e >> 11) & 1, e >> 12) for e in ent), attr)
    # seam cells first, identical ids in both maps
    used = set(pins)
    def free_id(m, prefer_primary=True):
        taken = set(ids[m]) | (used if m == 'north' else set())
        rng_ = list(range(1, 512)) + list(range(512, 1024))
        return next(i for i in rng_ if i not in taken and i not in seam_ids_all)
    seam_ids_all = set()
    seam_key_id = {}
    def cell_key(m, x, y):
        qs = sorted(byxy[(x, y)], key=lambda q: (q['layer'], q['q']))
        ent = tuple(quad_entry(m, q) for q in qs)
        t = trav[y, x]
        attr = t['behavior_id'] | ((1 if (x, y) in covered else 0) << 12)   # COVERED for overflow cells, else NORMAL
        return ent, attr
    for y in range(SPLIT - WINDOW, SPLIT + WINDOW):
        for x in range(W):
            kn, ks = cell_key('north', x, y), cell_key('south', x, y)
            # identical pictures: both maps' tiles for the seam are the same patterns in banks 0-5
            sig = (tuple(e & ~1023 & 0xFFFF for e in kn[0]), kn[1], tuple(result['north']['pattern_of'][e & 1023] for e in kn[0]))
            if sig not in seam_key_id:
                i = 1
                while i in pins or i in seam_ids_all:
                    i += 1
                seam_key_id[sig] = i; seam_ids_all.add(i)
                ids['north'][i] = kn; ids['south'][i] = ks
            mid = seam_key_id[sig]
            for m in MAPS:
                r0, r1 = MAPS[m]['rows']
                if r0 <= y < r1:
                    t = trav[y, x]
                    words[m][y - r0, x] = mid | (t['collision'] << 10) | (t['elevation'] << 12)
    for m in MAPS:
        r0, r1 = MAPS[m]['rows']
        rev = {v: k for k, v in ids[m].items()}
        for y in range(r0, r1):
            if seam_row(y):
                continue
            for x in range(W):
                t = trav[y, x]
                if t.get('metatile') is not None:
                    mid = t['metatile']
                else:
                    k = cell_key(m, x, y)
                    if k in rev:
                        mid = rev[k]
                    else:
                        taken = set(ids[m]) | seam_ids_all
                        mid = next(i for i in list(range(1, 512)) + list(range(512, 1024)) if i not in taken)
                        ids[m][mid] = k; rev[k] = mid
                words[m][y - r0, x] = mid | (t['collision'] << 10) | (t['elevation'] << 12)
    return dict(V=V, trav=trav, grid=grid, cells=cells, pins=pins, banks=banks, result=result, ids=ids, words=words,
                want=want, live=live, seam_ids=sorted(seam_ids_all))

def families(grid, top):
    """Material family of every quad: the majority HGSS material under it (ground layer); objects and the deck."""
    mats = np.load(SRC / 'hgss/hgss-ground-materials.npz')
    names = list(mats['names']) + ['none']
    m = mats['material']
    fam_px = np.full((H * PX, W * PX), 'lawn', object)
    look = np.array([FAMILY.get(n, 'other') for n in names], object)
    fam_px[ROW0 * PX:] = look[np.where(m >= 0, m, len(names) - 1)]
    v0, v1 = round((Rf.VIADUCT[0] + ROW0) * PX), round((Rf.VIADUCT[1] + ROW0) * PX)
    fam_px[v0:v1] = 'deck'
    for y in range(H):
        for x in range(W):
            if grid[y][x] in 'HDw':
                fam_px[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX] = 'object'
            elif grid[y][x] == 's':
                fam_px[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX] = 'sign'
    out = {}
    for y in range(H):
        for x in range(W):
            for q in range(4):
                py, px_ = y * PX + (q // 2) * 8, x * PX + (q % 2) * 8
                cnt = Counter(fam_px[py:py + 8, px_:px_ + 8].ravel().tolist())
                # small features (petals, light patches) decide the family once they cover a few pixels
                out[(y, x, 0, q)] = 'flower' if cnt.get('flower', 0) >= 6 else cnt.most_common(1)[0][0]
                out[(y, x, 1, q)] = 'deck' if v0 <= py < v1 else 'sign'
    return out

# One bank per material family, chosen by hand so the plan is explicit. Banks 2 and 4-10 are the same in both
# maps (the seam uses only these); north keeps Violet's 0, 1, 3 and 11; south's 0, 1, 3, 11, 12 are its own.
BANK_PLAN = {('shared', 2): ('sea',), ('shared', 4): ('rock',), ('shared', 5): ('tree',), ('shared', 6): ('pier',),
             ('shared', 7): ('deck',), ('shared', 8): ('lawn', 'flower'), ('shared', 9): ('road',), ('shared', 10): ('tallgrass',),
             ('north', 12): ('object',),
             ('south', 0): ('object',), ('south', 1): ('rock',), ('south', 3): ('sea',), ('south', 11): ('tree',),
             ('south', 12): ('lawn', 'flower')}
FEATURES = set('^CDHwsLEQJ')
FEATURE_SLOTS = 16
OVERFLOW_CAP = dict(north=160, south=160)
CORE_MAX = 12          # a family's own most-used colours kept exactly in its bank; the rest of the bank fits joins

def plan_banks(G, banks, art_grid):
    core = {}
    held = defaultdict(set)                             # family -> colours an earlier bank already holds
    for k, fams in BANK_PLAN.items():
        scope = k[0]
        grp = [g for g in G if g['fam'] in fams and (scope == 'shared' or scope in g['maps'])]
        if not grp:
            core[k] = []; banks[k] = [(0, 0, 0)]; continue
        keep = []
        accs, need = {}, {}
        for f in fams:                                  # each family keeps its own most-used colours
            acc = Counter()
            for g in grp:
                if g['fam'] == f:
                    for c, n in zip(map(tuple, g['u']), g['n']):
                        acc[tuple(int(v) for v in c)] += n * len(g['members'])
            tot = sum(acc.values()) or 1; run = 0; need[f] = 0
            for c, n in acc.most_common():
                if run >= 0.99 * tot:
                    break
                run += n; need[f] += 1
            accs[f] = acc
        for f in fams:                                  # slots in proportion to each family's colour need
            lim = CORE_MAX if len(fams) > 1 else 13
            cap = max(1, round(lim * need[f] / max(1, sum(need.values()))))
            ranked = [c for c, n in accs[f].most_common()]
            if held[f]:                                 # a second bank: the base tones, then what the first lacks
                base = ranked[:cap // 2]
                ranked = base + [c for c in ranked if c not in held[f] and c not in base]
            for c in ranked[:max(cap, 0)]:
                if c not in keep and len(keep) < lim:
                    keep.append(c)
            held[f] |= set(keep)
        core[k] = keep
        banks[k] = refit(grp, keep)
    # Buildings carry more than 15 colours (G02, C06: 21). Their colours the object bank lacks get locked slots
    # in banks with room, which the overflow split (both layers below the player) then draws from.
    for k, fams in BANK_PLAN.items():
        if 'object' not in fams:
            continue
        acc = Counter()
        for g in G:
            if g['fam'] == 'object' and (k[0] in g['maps']):
                for c, n in zip(map(tuple, g['u']), g['n']):
                    acc[tuple(int(v) for v in c)] += n
        K = lab(np.array(banks[k]))
        miss = [c for c, n in acc.most_common() if ((lab(np.array([c])) - K) ** 2).sum(-1).min() > 9]
        for c in miss[:8]:
            room = [b for b in BANK_PLAN if b[0] in ('shared', k[0]) and b != k and len(core[b]) < 13]
            if not room:
                break
            b = min(room, key=lambda b: len(core[b]))
            core[b].append(c)
        for b in BANK_PLAN:
            grp = [g for g in G if g['fam'] in BANK_PLAN[b] and (b[0] == 'shared' or b[0] in g['maps'])]
            banks[b] = refit(grp, core[b]) if grp else list(core[b]) or [(0, 0, 0)]
        print('  object overflow colours', k, len(miss), flush=True)
    # Feature colours (stairs, the cave mouth, doors, buildings, signs, ledges) that no bank holds get locked
    # slots, so these squares (directly or through the overflow layer) keep them.
    for scope in ('north', 'south'):
        acc = Counter()
        for g in G:
            if scope not in g['maps']:
                continue
            q = g['members'][0]
            if art_grid[q['y']][q['x']] not in FEATURES:
                continue
            for c, n in zip(map(tuple, g['u']), g['n']):
                acc[tuple(int(v) for v in c)] += n * len(g['members'])
        mine = [b for b in BANK_PLAN if b[0] in ('shared', scope)]
        added = 0
        for c, n in acc.most_common():
            if added >= FEATURE_SLOTS or n < 6:
                break
            have = min(float(((lab(np.array([c])) - lab(np.array(core[b] or [(0, 0, 0)]))) ** 2).sum(-1).min()) for b in mine)
            if have <= 36:                              # within 6 Lab of a held colour
                continue
            room = [b for b in mine if len(core[b]) < 15 and b[0] == scope] or [b for b in mine if len(core[b]) < 15]
            if not room:
                break
            b = min(room, key=lambda b: len(core[b]))
            core[b].append(c); added += 1
        print('  feature colours locked', scope, added, flush=True)
    for b in BANK_PLAN:
        grp = [g for g in G if g['fam'] in BANK_PLAN[b] and (b[0] == 'shared' or b[0] in g['maps'])]
        banks[b] = refit(grp, core[b]) if grp else list(core[b]) or [(0, 0, 0)]
    print('  core colours', {f'{k[0]}:{k[1]}:{BANK_PLAN[k][0]}': len(v) for k, v in core.items()}, flush=True)
    return core

def refit(grp, keep):
    """The bank: its family's core colours exactly, the remaining slots fitted to what else its tiles need."""
    u, n = merge_hist(grp, weighted=True)
    if len(keep):
        K = lab(np.array(keep))
        d = ((lab(u)[:, None] - K[None]) ** 2).sum(-1).min(1)
        rest = d > 4.0
        u, n = u[rest], n[rest] * np.sqrt(d[rest])
    extra = kmeans_w(u, n, 15 - len(keep)) if len(u) and len(keep) < 15 else []
    return list(dict.fromkeys(list(keep) + [tuple(int(v) for v in c) for c in extra]))[:15]

def split_banks(u, w, n):
    if n == 1:
        return [kmeans_w(u, w, 15)]
    L = lab(u)
    order = np.argsort(L[:, 0])                         # split a family's ramp by lightness
    cw = np.cumsum(w[order]) / w.sum()
    parts = np.array_split(order, [int(np.searchsorted(cw, k / n)) for k in range(1, n)])
    return [kmeans_w(u[p], w[p], 15) for p in parts if len(p)]

def fit_split(u, w, n):
    return [c for cols in split_banks(u, w, n) for c in cols]

def merge_hist(grp, weighted=False):
    acc = Counter()
    for g in grp:
        for c, n in zip(map(tuple, g['u']), g['n']):
            acc[c] += n * (g['w'] if weighted else len(g['members']))
    # square-root weights: big flat areas don't starve small features (flowers, trims) of their colours
    u = np.array(list(acc.keys())); n = np.sqrt(np.array(list(acc.values()), float))
    return u, n

FLIPS = ((0, 0), (1, 0), (0, 1), (1, 1))
def flip(a, hf, vf):
    if hf: a = a[:, ::-1]
    if vf: a = a[::-1]
    return a

def tiles_for(m, live, banks, vtiles):
    """Patterns for map m: exact dedupe (with flips), then logged near-duplicate merges to fit 1024 tiles."""
    mine = [qd for qd in live if m in qd['maps']]
    budget = 1023 - len({v.astype(np.uint8).tobytes() for v in vtiles.values()} - {bytes(64)})     # tile 0 is the blank tile
    # appearances: (canonical pattern, bank)
    app = {}                                           # key -> dict(pattern, bank, users, rgbL, protect, cls, layer)
    for qd in mine:
        pat, (hf, vf) = canon(qd['idx'])
        k = (pat, qd['bank'])
        a = app.setdefault(k, dict(pat=pat, bank=qd['bank'], users=[], protect=False, cls=set(), layer=qd['layer'],
                                   seam=False, mask=flip(qd['idx'], hf, vf) > 0))
        a['users'].append((qd, hf, vf)); a['protect'] |= qd['protect'] or qd['seam'] or qd['layer'] == 1
        a['seam'] |= qd['seam']; a['cls'].add(qd['cls'])
    keys = list(app)
    for k in keys:
        a = app[k]
        P = np.array(banks[a['bank']])
        arr = np.frombuffer(a['pat'], np.uint8).reshape(8, 8)
        a['rgb'] = np.where(arr[..., None] > 0, P[np.maximum(arr, 1) - 1], 0)
        a['L'] = lab(a['rgb'].reshape(-1, 3)).reshape(8, 8, 3)
    patterns = lambda: len({app[k]['pat'] for k in keys if app[k].get('into') is None})
    n_exact = patterns()
    merges = []
    if n_exact > budget:
        # candidate merges A -> B: same layer, shared material class, B's picture under some flip
        cand = []
        Ls = np.stack([app[k]['L'] for k in keys])                          # (N,8,8,3)
        flipped = np.stack([np.stack([flip(app[k]['L'], hf, vf) for hf, vf in FLIPS]) for k in keys])  # (N,4,8,8,3)
        for i, ka in enumerate(keys):
            A = app[ka]
            if A['protect'] or A['layer'] == 1:
                continue
            d = np.sqrt(((flipped - Ls[i][None, None]) ** 2).sum(-1))       # (N,4,8,8)
            mean = d.mean((2, 3)); mx = d.max((2, 3))
            for j, kb in enumerate(keys):
                if i == j or app[kb]['layer'] != A['layer'] or not (app[kb]['cls'] & A['cls']):
                    continue
                f = int(mean[j].argmin())
                if mean[j, f] <= MERGE_MEAN_MAX and mx[j, f] <= MERGE_PIXEL_MAX:
                    cand.append((float(mean[j, f]) * (1 + 0.02 * len(A['users'])), i, j, f, float(mean[j, f]), float(mx[j, f])))
        cand.sort()
        absorbed = set()
        count = n_exact
        pat_users = Counter(app[k]['pat'] for k in keys)
        for score, i, j, f, mean_, max_ in cand:
            if count <= budget:
                break
            ka, kb = keys[i], keys[j]
            A, B = app[ka], app[kb]
            if A.get('into') is not None or B.get('into') is not None or ka in absorbed:
                continue
            A['into'] = (kb, FLIPS[f]); absorbed.add(kb)
            pat_users[A['pat']] -= 1
            if pat_users[A['pat']] == 0:
                count -= 1
            merges.append(dict(map=m, frm=[A['bank'][1], len(A['users'])], into_bank=B['bank'][1], flip=list(FLIPS[f]),
                               mean_lab=round(mean_, 2), max_lab=round(max_, 2), cls=sorted(A['cls']),
                               cells=sorted({(qd['x'], qd['y']) for qd, _, _ in A['users']})[:6]))
        assert count <= budget, (m, 'does not fit', count, budget)
    # allocate tile ids
    tiles = [np.zeros((8, 8), np.uint8)]
    pid = {tiles[0].tobytes(): 0}
    violet = {}
    for t, arr in vtiles.items():                     # Violet's tiles as they are (its entries carry their own flips)
        raw = arr.astype(np.uint8).tobytes()
        if raw not in pid:
            pid[raw] = len(tiles); tiles.append(arr.astype(np.uint8))
        violet[t] = pid[raw]
    quad = {}
    for k in keys:
        a = app[k]
        tgt, extra = k, (0, 0)
        if a.get('into') is not None:
            tgt, extra = a['into']
        b = app[tgt]
        if b['pat'] not in pid:
            pid[b['pat']] = len(tiles); tiles.append(np.frombuffer(b['pat'], np.uint8).reshape(8, 8))
        for qd, hf, vf in a['users']:
            # qd = flip(canonical A, hf, vf); A ~ flip(B, extra) => qd ~ flip(flip(B, extra), hf, vf)
            quad[id(qd)] = (pid[b['pat']], hf ^ extra[0], vf ^ extra[1], b['bank'][1])
    pattern_of = {i: t.tobytes() for i, t in enumerate(tiles)}
    assert len(tiles) <= 1024, (m, len(tiles))
    return dict(tiles=tiles, quad=quad, violet=violet, exact=n_exact, merged=len(merges), merges=merges, budget=budget,
                pattern_of=pattern_of)

def canon(idx):
    """Canonical pattern bytes and the flip that turns the canonical pattern into idx."""
    best = None
    for hf, vf in FLIPS:
        b = flip(idx, hf, vf).tobytes()
        if best is None or b < best[0]:
            best = (b, (hf, vf))
    return best

# --------------------------------------------------------------------------- outputs
def jasc(cols):
    cols = [(0, 0, 0)] + list(cols) + [(0, 0, 0)] * (15 - len(cols))
    return '\r\n'.join(['JASC-PAL', '0100', '16'] + [f'{c[0]} {c[1]} {c[2]}' for c in cols[:16]]) + '\r\n'

def bank_list(r, m):
    out = {}
    for (scope, b), cols in r['banks'].items():
        if scope in ('shared', m):
            out[b] = cols
    return out

def write_tilesets(engine, r, m):
    cfg = MAPS[m]; res = r['result'][m]; pals = bank_list(r, m)
    meta = r['ids'][m]
    n_sec = max([i - 511 for i in meta if i >= 512] + [0])
    for kind, lo, hi, banks in (('primary', 0, 512, range(0, 6)), ('secondary', 512, 1024, range(6, 13))):
        d = engine / 'data/tilesets' / kind / cfg['ts']
        (d / 'palettes').mkdir(parents=True, exist_ok=True)
        tl = res['tiles'][lo:hi]
        if kind == 'primary':
            tl = tl + [np.zeros((8, 8), np.uint8)] * (512 - len(tl))
        tl = tl or [np.zeros((8, 8), np.uint8)]
        rows = max(1, (len(tl) + 15) // 16)
        sheet = np.zeros((rows * 8, 128), np.uint8)
        for i, t in enumerate(tl):
            sheet[(i // 16) * 8:(i // 16) * 8 + 8, (i % 16) * 8:(i % 16) * 8 + 8] = t
        im = Image.fromarray(sheet, 'P'); im.putpalette([v for i in range(16) for v in (i * 17, i * 17, i * 17)] + [0] * 720)
        im.save(d / 'tiles.png', bits=4)
        for b in range(16):
            (d / 'palettes' / f'{b:02}.pal').write_text(jasc(pals.get(b, []) if b in banks else []))
        idr = range(0, 512) if kind == 'primary' else range(512, 512 + n_sec)
        rows_ = [meta.get(i, ((0,) * 8, 0)) for i in idr]
        (d / 'metatiles.bin').write_bytes(b''.join(struct.pack('<8H', *k[0]) for k in rows_))
        (d / 'metatile_attributes.bin').write_bytes(struct.pack('<%dH' % len(rows_), *[k[1] for k in rows_]))

def register_tilesets(engine, m):
    sym, name = MAPS[m]['sym'], MAPS[m]['ts']
    h = engine / 'src/data/tilesets/headers.h'; s = h.read_text()
    for s_, sec in ((sym + 'Primary', 'FALSE'), (sym, 'TRUE')):
        if f'gTileset_{s_} =' not in s:
            s = s.rstrip('\n') + f'\n\nconst struct Tileset gTileset_{s_} = {{ .isCompressed = TRUE, .isSecondary = {sec}, .tiles = gTilesetTiles_{s_}, .palettes = gTilesetPalettes_{s_}, .metatiles = gMetatiles_{s_}, .metatileAttributes = gMetatileAttributes_{s_}, .callback = NULL }};\n'
    h.write_text(s)
    g = engine / 'src/data/tilesets/graphics.h'; s = g.read_text()
    for s_, kind in ((sym + 'Primary', 'primary'), (sym, 'secondary')):
        if f'gTilesetTiles_{s_}[]' not in s:
            s = s.rstrip('\n') + f'\n\nconst u32 gTilesetTiles_{s_}[] = INCGFX_U32("data/tilesets/{kind}/{name}/tiles.png", ".4bpp.fastSmol");\nconst u16 gTilesetPalettes_{s_}[][16] = {{\n' + ''.join(f'INCGFX_U16("data/tilesets/{kind}/{name}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n'
    g.write_text(s)
    mt = engine / 'src/data/tilesets/metatiles.h'; s = mt.read_text()
    for s_, kind in ((sym + 'Primary', 'primary'), (sym, 'secondary')):
        if f'gMetatiles_{s_}[]' not in s:
            s = s.rstrip('\n') + f'\nconst u16 gMetatiles_{s_}[] = INCBIN_U16("data/tilesets/{kind}/{name}/metatiles.bin");\nconst u16 gMetatileAttributes_{s_}[] = INCBIN_U16("data/tilesets/{kind}/{name}/metatile_attributes.bin");\n'
    mt.write_text(s)

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

SCRIPTS_NORTH = '''JohtoRoute32_MapScripts::
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
'''
SCRIPTS_SOUTH = '''JohtoRoute32South_MapScripts::
    .byte 0

JohtoRoute32_CaveSign::
    msgbox JohtoRoute32_CaveSign_Text, MSGBOX_SIGN
    end

JohtoRoute32_CaveSign_Text:
    .string "UNION CAVE\\nAHEAD$"
'''

def up(s): return 'MAP_' + re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', s).upper()

def write_center(engine):
    for name, src in ((CENTER, 'VioletPokemonCenter'), (UPSTAIRS, 'VioletCenterUpstairs')):
        d = engine / 'data/maps' / name
        d.mkdir(parents=True, exist_ok=True)
        mp = json.loads((engine / f'data/maps/{src}/map.json').read_text())
        mp['id'] = up(name); mp['name'] = name; mp['region_map_section'] = 'MAPSEC_JOHTO_ROUTE_32'
        for w in mp['warp_events']:
            if w['dest_map'] == 'MAP_VIOLET_CITY':
                w['dest_map'], w['dest_warp_id'] = MAPS['south']['map_id'], '0'
            elif w['dest_map'] == 'MAP_VIOLET_CENTER_UPSTAIRS':
                w['dest_map'] = up(UPSTAIRS)
            elif w['dest_map'] == 'MAP_VIOLET_POKEMON_CENTER':
                w['dest_map'] = up(CENTER)
        txt = (engine / f'data/maps/{src}/scripts.inc').read_text().replace(src, name)
        for o in mp.get('object_events', []):
            if isinstance(o.get('script'), str):
                o['script'] = o['script'].replace(src, name)
        (d / 'map.json').write_text(json.dumps(mp, indent=2) + '\n')
        (d / 'scripts.inc').write_text(txt)

def register_maps(engine):
    g = engine / 'data/maps/map_groups.json'; d = json.loads(g.read_text())
    grp = next(k for k, v in d.items() if isinstance(v, list) and 'VioletCity' in v)
    names = [MAPS['north']['name'], MAPS['south']['name'], CENTER, UPSTAIRS]
    for n in names:
        if n not in d[grp]:
            d[grp].append(n)
    g.write_text(json.dumps(d, indent=2) + '\n')
    lj = engine / 'data/layouts/layouts.json'; L = json.loads(lj.read_text())
    for m, c in MAPS.items():
        L['layouts'] = [l for l in L['layouts'] if l.get('id') != c['layout']]
        if True:
            L['layouts'].append(dict(id=c['layout'], name=f'{c["name"]}_Layout', width=W, height=c['rows'][1] - c['rows'][0],
                                     primary_tileset=f'gTileset_{c["sym"]}Primary', secondary_tileset=f'gTileset_{c["sym"]}',
                                     border_filepath=f'data/layouts/{c["name"]}/border.bin',
                                     blockdata_filepath=f'data/layouts/{c["name"]}/map.bin'))
    lj.write_text(json.dumps(L, indent=2) + '\n')
    es = engine / 'data/event_scripts.s'; t = es.read_text()
    anchor = '.include "data/maps/VioletHouse5/scripts.inc"\n'
    for n in names:
        line = f'.include "data/maps/{n}/scripts.inc"\n'
        if line not in t:
            t = t.replace(anchor, anchor + '\n' + line, 1); anchor = line
    es.write_text(t)
    pf = engine / 'src/apocrypha_map_proof.c'; t = pf.read_text()     # test-only warp list
    for n in names:
        if up(n) not in t:
            t = t.replace('};\nvoid MapProof_Boot', f', {up(n)}}};\nvoid MapProof_Boot', 1)
    pf.write_text(t)
    v = engine / 'data/maps/VioletCity/map.json'; M = json.loads(v.read_text())
    conns = [c for c in (M.get('connections') or []) if c['map'] != MAPS['north']['map_id']]
    conns.append(dict(map=MAPS['north']['map_id'], direction='down', offset=Rf.VIOLET_SHIFT))
    M['connections'] = conns
    v.write_text(json.dumps(M, indent=2) + '\n')

def which(y): return 'north' if y < SPLIT else 'south'

def write_maps(engine, r):
    events = json.loads((SRC / 'hgss-events.json').read_text())
    ev = {m: dict(bg=[], obj=[], warp=[]) for m in MAPS}
    moves = []
    hidden = {v[3]: v for v in ITEMS.values()}
    for s in events['signs']:
        x, y = Rf.to_map(*s['cell']); m = which(y); ly = y - MAPS[m]['rows'][0]
        if s['bg_type'] == 1:
            script = next(v for k, v in SIGN_SCRIPTS.items() if k in s['text'])
            ev[m]['bg'].append(dict(type='sign', x=x, y=ly, elevation=0, player_facing_dir='BG_EVENT_PLAYER_FACING_ANY', script=script))
            moves.append(dict(event=script, map=m, cell=[x, ly], native=[x, y], hgss=s['cell'], text=s['text']))
        elif s['script'] in hidden:
            name, _, item, _ = hidden[s['script']]
            ev[m]['bg'].append(dict(type='hidden_item', x=x, y=ly, elevation=3, item=item, flag=name, quantity=1, underfoot=False))
            moves.append(dict(event=f'hidden {item}', map=m, cell=[x, ly], native=[x, y], hgss=s['cell'], flag=name))
    balls = {v[3]: v for v in ITEMS.values()}
    for o in events['objects']:
        x, y = Rf.to_map(*o['cell']); m = which(y); ly = y - MAPS[m]['rows'][0]
        base = dict(x=x, y=ly, elevation=3, movement_range_x=0, movement_range_y=0, trainer_type='TRAINER_TYPE_NONE')
        if o['sprite'] == 'SPRITE_TREE':
            ev[m]['obj'].append(dict(graphics_id='OBJ_EVENT_GFX_CUTTABLE_TREE', movement_type='MOVEMENT_TYPE_LOOK_AROUND',
                                     trainer_sight_or_berry_tree_id='0', script='EventScript_CutTree', flag='FLAG_TEMP_11', **base))
            moves.append(dict(event='cuttable tree', map=m, cell=[x, ly], native=[x, y], hgss=o['cell']))
        elif o['sprite'] == 'SPRITE_BREAKROCK':
            ev[m]['obj'].append(dict(graphics_id='OBJ_EVENT_GFX_BREAKABLE_ROCK', movement_type='MOVEMENT_TYPE_LOOK_AROUND',
                                     trainer_sight_or_berry_tree_id='0', script='EventScript_RockSmash', flag='FLAG_TEMP_12', **base))
            moves.append(dict(event='breakable rock', map=m, cell=[x, ly], native=[x, y], hgss=o['cell']))
        elif o['sprite'] == 'SPRITE_MONSTARBALL' and o['flag'] in balls:
            name, _, item, _ = balls[o['flag']]
            assert r['trav'][y, x]['foot'] == 'open', ('item ball cell is not open ground', x, y)
            ev[m]['obj'].append(dict(graphics_id='OBJ_EVENT_GFX_ITEM_BALL', movement_type='MOVEMENT_TYPE_FACE_DOWN',
                                     trainer_sight_or_berry_tree_id=item, script='Common_EventScript_FindItem', flag=name, **base))
            moves.append(dict(event=f'item ball {item}', map=m, cell=[x, ly], native=[x, y], hgss=o['cell'], flag=name))
        else:
            moves.append(dict(event=o['id'], hgss=o['cell'], note='not placed: trainers, NPCs and the TM09 ball are campaign work'))
    door = next((x, y) for y, row in enumerate(r['grid']) for x, ch in enumerate(row) if ch == 'D')
    ev['south']['warp'].append(dict(x=door[0], y=door[1] - SPLIT, elevation=0, dest_map=up(CENTER), dest_warp_id='0'))
    conns = dict(north=[dict(map='MAP_VIOLET_CITY', direction='up', offset=-Rf.VIOLET_SHIFT),
                        dict(map=MAPS['south']['map_id'], direction='down', offset=0)],
                 south=[dict(map=MAPS['north']['map_id'], direction='up', offset=0)])
    borders = {}
    for m, c in MAPS.items():
        words = r['words'][m]
        d = engine / f'data/layouts/{c["name"]}'; d.mkdir(parents=True, exist_ok=True)
        (d / 'map.bin').write_bytes(struct.pack('<%dH' % words.size, *words.ravel().tolist()))
        border = border_of(r, m)
        borders[m] = [f'{b & 1023:#05x}' for b in border]
        (d / 'border.bin').write_bytes(struct.pack('<4H', *border))
        M = dict(id=c['map_id'], name=c['name'], layout=c['layout'], music='MUS_LITTLEROOT', region='REGION_JOHTO',
                 region_map_section='MAPSEC_JOHTO_ROUTE_32', requires_flash=False, weather='WEATHER_SUNNY', map_type='MAP_TYPE_ROUTE',
                 allow_cycling=True, allow_escaping=False, allow_running=True, show_map_name=True, battle_scene='MAP_BATTLE_SCENE_NORMAL',
                 build_target='emerald', connections=conns[m], object_events=ev[m]['obj'], warp_events=ev[m]['warp'],
                 coord_events=[], bg_events=ev[m]['bg'])
        md = engine / f'data/maps/{c["name"]}'; md.mkdir(parents=True, exist_ok=True)
        (md / 'map.json').write_text(json.dumps(M, indent=2) + '\n')
        (md / 'scripts.inc').write_text(SCRIPTS_NORTH if m == 'north' else SCRIPTS_SOUTH)
    write_flags(engine); write_mapsec(engine); write_center(engine); register_maps(engine)
    return dict(moves=moves, door=[door[0], door[1] - SPLIT], borders=borders)

def border_of(r, m):
    """North: the woods along its west edge (2x2, blocked); south: the open sea east of the route."""
    grid, words = r['grid'], r['words'][m]
    r0, r1 = MAPS[m]['rows']
    want = 'T' if m == 'north' else '~'
    deck = range(int(Rf.VIADUCT[0]) + ROW0 - 1, int(Rf.VIADUCT[1]) + ROW0 + 2)      # not under the viaduct
    ok = lambda x, y: y not in deck and all(r0 <= y + dy < r1 and 0 <= x + dx < W and grid[y + dy][x + dx] == want
                                            for dx in (-1, 0, 1) for dy in (-1, 0, 1))
    pick = {}
    for y in range(r0 + 1, r1 - 1):
        for x in range(1, W - 1):
            if ok(x, y):
                pick.setdefault((x % 2, y % 2), (x, y))
    return [int(words[pick[(px, py)][1] - r0, pick[(px, py)][0]]) & 1023 | (1 << 10) | ((1 if m == 'south' else 0) << 12)
            for py in (0, 1) for px in (0, 1)]

# --------------------------------------------------------------------------- checks
def decode(engine, m, words):
    c = MAPS[m]
    t = Tileset(engine, c['ts'], c['ts'])
    return np.array(t.map_image(words.ravel().tolist(), W).convert('RGB')), t

def report_of(engine, r):
    rep = dict(split=SPLIT, window=WINDOW, seam_metatiles=len(r['seam_ids']), pinned_violet_metatiles=len(r['pins']))
    for m in MAPS:
        res = r['result'][m]
        meta = r['ids'][m]
        rep[m] = dict(tiles=len(res['tiles']), exact_patterns=res['exact'], merged=res['merged'], budget=res['budget'],
                      primary_metatiles=sum(1 for i in meta if i < 512), secondary_metatiles=sum(1 for i in meta if i >= 512),
                      banks={b: len(c) for b, c in sorted(bank_list(r, m).items())})
    q = np.array([qd['qerr'] for qd in r['live']])
    rep['palette_error_lab'] = dict(mean=round(float(q.mean()), 2), p95=round(float(np.percentile(q, 95)), 2), max=round(float(q.max()), 2))
    trav, cells = r['trav'], r['cells']
    events = json.loads((SRC / 'hgss-events.json').read_text())
    cut = {Rf.to_map(*o['cell']) for o in events['objects'] if o['sprite'] in ('SPRITE_TREE', 'SPRITE_BREAKROCK')}
    start = (min(Rf.VIOLET_ROAD), 0)
    hs = {Rf.to_map(*p) for p in hgss_reach(cells, (15, 0))}
    ns = reach(trav, start)
    rep['reach'] = dict(native=len([p for p in ns if p[1] >= ROW0]), hgss=len(hs),
                        native_only=sorted(list(p) for p in ns if p[1] >= ROW0 and p not in hs),
                        hgss_only=sorted(list(p) for p in hs if p not in ns),
                        south_edge_reached=any(p[1] == H - 1 for p in ns))
    return rep

def main(engine, install):
    OUT.mkdir(parents=True, exist_ok=True); OEV.mkdir(parents=True, exist_ok=True)
    r = pack(engine)
    rep = report_of(engine, r)
    merges = r['result']['north']['merges'] + r['result']['south']['merges']
    (OUT / 'merges.json').write_text(json.dumps(merges) + '\n')
    (OUT / 'palettes.json').write_text(json.dumps({f'{s}:{b}': c for (s, b), c in sorted(r['banks'].items())}) + '\n')
    if install:
        for m in MAPS:
            write_tilesets(engine, r, m); register_tilesets(engine, m)
        rep['events'] = write_maps(engine, r)
        full = np.zeros((H * PX, W * PX, 3), np.uint8)
        for m in MAPS:
            img, _ = decode(engine, m, r['words'][m])
            r0, r1 = MAPS[m]['rows']
            full[r0 * PX:r1 * PX] = img
            Image.fromarray(img).save(OEV / f'native-{m}.png')
        Image.fromarray(full).save(OEV / 'native.png')
        dd = np.sqrt(((lab(full.reshape(-1, 3)) - lab(r['want'].reshape(-1, 3))) ** 2).sum(-1)).reshape(H * PX, W * PX)
        rep['native_vs_art_lab'] = dict(mean=round(float(dd.mean()), 3), p99=round(float(np.percentile(dd, 99)), 2),
                                        over_10=int((dd > 10).sum()))
    (OUT / 'traversal.json').write_text(json.dumps([r['trav'][y, x] for y in range(H) for x in range(W)], default=int) + '\n')
    (OEV / 'pack.json').write_text(json.dumps(rep, indent=1, default=int) + '\n')
    print(json.dumps({k: v for k, v in rep.items() if k != 'events'}, default=int)[:4000])

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), '--install' in sys.argv)
