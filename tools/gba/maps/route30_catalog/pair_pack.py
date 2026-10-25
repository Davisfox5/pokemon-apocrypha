"""Joint native pack of Route 30 and Route 31 onto their shared primary tileset (route30_31).

    python3 tools/gba/maps/route30_catalog/pair_pack.py ENGINE_CHECKOUT [--install]

Each map's pack.py writes its spec (layers, traversal, layer types, cells placed by id, pinned banks:
`pack.py ENGINE --spec FILE`); this packs both at once with Mahogany's lossless rule (every native pixel keeps
its assembled RGB555 colour) and the seam rule, then installs the tilesets and has each pack.py install its
map words and events (`pack.py ENGINE --install-words FILE`).

  * The shared primary is CherrygrovePrimary with its tiles and metatiles where a seam needs them (every
    Cherrygrove cell visible from Route 30, Route 30's south band) and every primary tile either map reuses
    kept at their own indices and in palettes 0-3; its other tile slots and its palettes 4-5 hold the two
    routes' art. Cherrygrove's own cells draw the same in either primary (seams.py checks).
  * A Gen 3 map draws a connected map's nearest rows with its own tilesets. Every cell of either route that
    a player can see across the Route 30/31 seam gets a secondary metatile id reserved in both secondaries
    (Route 29's rule for New Bark's ids): each secondary draws that cell's pixels with its own tiles and
    palettes at that id, so each map draws the other's seam cells exactly.
  * Palettes: 0-3 are Cherrygrove's; 4-5 (primary, the same for both maps) and each map's secondary banks
    6-12 come from one integer program over both maps' tile colour sets, a map's sets including the other
    map's seam cells. A map's pinned banks (Route 30: bank 10, the blossom trees Cherrygrove shows across
    its seam) keep their palettes.
  * Tiles CherrygrovePrimary already has are reused; the rest go into the map's secondary (512 tiles),
    then into the shared primary's free slots.
"""
from __future__ import annotations
import json, struct, sys
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
from tiles import Tileset                            # noqa: E402

PRI_NAME, PRI_SYM = 'route30_31', 'Route30Route31Primary'
PRI_KEEP = (0, 1, 2, 3)              # CherrygrovePrimary's palettes kept as they are
SHARED_BANKS = (4, 5)                # the shared primary's palettes for route art
SEC_BANKS = tuple(range(6, 13))
SEC_TILES = 512
COVERED, NORMAL = 1, 0

def rgb5(a): return (np.asarray(a).astype(np.int32) >> 3)
def entry(tile, flip, bank): return tile | ((flip & 1) << 10) | ((flip >> 1) << 11) | (bank << 12)
def flips(ix):
    for f in range(4):
        v = ix[:, ::-1] if f & 1 else ix
        yield f, (v[::-1] if f & 2 else v)

class Primary:
    """CherrygrovePrimary: every tile under every bank (0-3) and flip, every metatile."""
    def __init__(self, engine):
        t = Tileset(engine, 'cherrygrove', 'cherrygrove')
        self.t = t
        self.tiles = [np.array(x, np.uint8).reshape(8, 8) & 15 for x in t.tiles[0]]
        self.pals = [[tuple(c) for c in p] for p in t.pals[0][:6]]
        self.opaque, self.masked = {}, {}
        for i, ix in enumerate(self.tiles):
            for f, v in flips(ix):
                for b in PRI_KEEP:
                    rgb = np.array([self.pals[b][k] for k in v.ravel()], np.uint8).reshape(8, 8, 3)
                    key = rgb5(rgb).astype(np.int16)
                    self.masked.setdefault(np.where((v > 0)[..., None], key, -1).tobytes(), (i, f, b))
                    if (v > 0).all():
                        self.opaque.setdefault(key.tobytes(), (i, f, b))
        self.metatiles = [tuple(int(e) for e in m) for m in t.blocks[0]]
        self.attrs = list(t.attrs[0])

# --------------------------------------------------------------------------- jobs
def plan_cells(spec, jobs):
    """Per cell, four (bottom job, top job or None) quadrants (Route 29's pack rules)."""
    ground, flat, top = spec['ground'], spec['flat'], spec['top']
    above, H, W = spec['above'], spec['H'], spec['W']
    def job(px, mask, layer):
        k5 = rgb5(px).astype(np.int16)
        if mask is not None:
            k5 = np.where(mask[..., None], k5, -1)
        key = (k5.tobytes(), layer)
        if key not in jobs:
            jobs[key] = dict(k5=k5, layer=layer, n=0, maps=set())
        jobs[key]['n'] += 1; jobs[key]['maps'].add(spec['name'])
        return key
    plains = spec['plains']
    def backing(b, vis, sl):
        if not (~vis).any():
            return b
        for pl in plains:
            if (pl[sl][vis] == b[vis]).all():
                return pl[sl].copy()
        return b
    common = Counter(ground[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].tobytes() for ty in range(H * 2) for tx in range(W * 2)).most_common(1)[0][0]
    filler = np.frombuffer(common, np.uint8).reshape(8, 8, 3)
    plan = {}
    for y in range(H):
        for x in range(W):
            if (x, y) in spec['placed']:
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
                b = job(filler, None, 0) if up.all() else job(backing(gpx, ~up, sl), None, 0)
                t = job(upx, up, 1) if up.any() else None
                q.append((b, t))
            plan[(x, y)] = q
    return plan

def setof(j):
    return frozenset(map(tuple, j['k5'][j['k5'][..., 0] >= 0].reshape(-1, 3).tolist()))

def joint_banks(groups, shared, own, size=15, time_limit=900):
    """Every colour set of both maps in one integer program (scipy / HiGHS): groups is a list of (sets,
    allowed virtual banks); a virtual bank is ('shared', b) for a primary bank both maps draw, or (map, b)
    for a map's own secondary bank. Each set lies inside one allowed bank, each bank holds at most `size`
    colours, and the colours placed are as few as can be. Returns {virtual bank: colour set} or None."""
    from scipy.optimize import milp, LinearConstraint, Bounds
    from scipy.sparse import lil_matrix
    vbanks = [('shared', b) for b in shared] + [(n, b) for n, bs in own.items() for b in bs]
    vi = {v: i for i, v in enumerate(vbanks)}
    items = [(st, [vi[v] for v in allowed]) for sets, allowed in groups for st in sets]
    cols = sorted(set().union(*[st for st, _ in items])); ci = {c: i for i, c in enumerate(cols)}
    X = {}
    for si, (st, al) in enumerate(items):
        for b in al:
            X[(si, b)] = len(X)
    nx = len(X); Y = lambda c, b: nx + c * len(vbanks) + b
    nv = nx + len(cols) * len(vbanks)
    rows = len(items) + sum(len(st) * len(al) for st, al in items) + len(vbanks)
    A = lil_matrix((rows, nv)); lo = np.zeros(rows); hi = np.zeros(rows); r = 0
    for si, (st, al) in enumerate(items):
        for b in al: A[r, X[(si, b)]] = 1
        lo[r] = hi[r] = 1; r += 1
    for si, (st, al) in enumerate(items):
        for c in st:
            for b in al:
                A[r, X[(si, b)]] = 1; A[r, Y(ci[c], b)] = -1; lo[r] = -np.inf; hi[r] = 0; r += 1
    for b in range(len(vbanks)):
        for c in range(len(cols)): A[r, Y(c, b)] = 1
        lo[r] = 0; hi[r] = size; r += 1
    cost = np.zeros(nv); cost[nx:] = 1
    res = milp(c=cost, constraints=LinearConstraint(A.tocsr(), lo, hi), integrality=np.ones(nv),
               bounds=Bounds(np.zeros(nv), np.ones(nv)), options=dict(time_limit=time_limit, disp=False))
    print('joint milp', res.status, res.message)
    if res.x is None:
        return None
    out = {v: set() for v in vbanks}
    for si, (st, al) in enumerate(items):
        out[vbanks[max(al, key=lambda b: res.x[X[(si, b)]])]] |= st
    return {v: frozenset(c) for v, c in out.items()}

# --------------------------------------------------------------------------- seam
def seam_cells(a, b, offset, rev=False):
    """Cells of map a (above) visible from walkable cells of map b (below), a's column 0 at b's column
    `offset` (seams.py's camera: 8 columns either side, 5 rows above and below); rev: cells of b visible
    from a."""
    seen = set()
    src, dst = (a, b) if rev else (b, a)
    walk = (src['collision'] == 0) & (src['elevation'] == 3)
    for y, x in zip(*np.nonzero(walk)):
        for dx in range(-8, 9):
            for dy in range(-5, 6):
                tx, ty = (x + dx + offset, y + dy - a['H']) if rev else (x + dx - offset, y + dy + a['H'])
                if 0 <= tx < dst['W'] and 0 <= ty < dst['H']:
                    seen.add((tx, ty))
    return seen

# --------------------------------------------------------------------------- pack
def pack_pair(engine, specs, upper, lower, offset):
    """specs: {name: spec}; upper/lower: names of the map above and below; offset: the lower map's "up"
    connection offset (the upper map's column 0 at the lower map's column `offset`)."""
    P = Primary(engine)
    jobs = {}
    plans = {n: plan_cells(s, jobs) for n, s in specs.items()}
    for j in jobs.values():
        j['primary'] = (P.opaque if j['layer'] == 0 else P.masked).get(j['k5'].tobytes())
    # Seam cells of both maps (never placed-by-id cells: the band is not near this seam). Each map also
    # draws the other's.
    seam = {upper: seam_cells(specs[upper], specs[lower], offset), lower: seam_cells(specs[upper], specs[lower], offset, rev=True)}
    other = {upper: lower, lower: upper}
    for n in seam:
        seam[n] = sorted(c for c in seam[n] if c not in specs[n]['placed'])
        for c in seam[n]:
            for qb, qt in plans[n][c]:
                for k in (qb, qt):
                    if k is not None:
                        jobs[k]['maps'].add(other[n])
    # Palettes.
    cg5 = {b: frozenset(tuple(int(v) >> 3 for v in c) for c in P.pals[b][1:16]) for b in PRI_KEEP}
    pinned = {n: {b: frozenset(tuple(int(v) >> 3 for v in c) for c in p) for b, p in s['fixed_pal'].items()} for n, s in specs.items()}
    own = {n: [b for b in SEC_BANKS if b not in pinned[n]] for n in specs}
    fixed = {n: {**cg5, **pinned[n]} for n in specs}
    groups = []
    for n in specs:
        mine = {st for st in (setof(j) for j in jobs.values() if n in j['maps'] and j['primary'] is None)
                if not any(st <= f for f in fixed[n].values())}
        assert all(len(st) <= 15 for st in mine), (n, 'a tile holds more than 15 colours')
        groups.append(([c for c in mine if not any(c < d for d in mine)], [('shared', b) for b in SHARED_BANKS] + [(n, b) for b in own[n]]))
    vb = joint_banks(groups, SHARED_BANKS, own)
    assert vb is not None, 'the two routes do not fit their banks'
    shared = {b: vb[('shared', b)] for b in SHARED_BANKS}
    pal = {n: {**{b: vb[(n, b)] for b in own[n]}, **shared} for n in specs}
    pinned_order = {n: {b: [tuple(int(v) >> 3 for v in c) for c in p] for b, p in s['fixed_pal'].items()} for n, s in specs.items()}
    def slots(n, b):
        if b in PRI_KEEP:
            return [tuple(int(v) >> 3 for v in c) for c in P.pals[b][1:16]]
        if b in pinned_order[n]:
            return pinned_order[n][b]
        return sorted(pal[n][b])
    def assign(n, st):
        for b, f in fixed[n].items():
            if st <= f:
                return b
        return next(b for b in list(SHARED_BANKS) + own[n] if st <= pal[n][b])
    def indices(j, n, bank):
        idx = {}
        for i, c in enumerate(slots(n, bank)):
            idx.setdefault(c, i + 1)
        k5 = j['k5']; ix = np.zeros((8, 8), np.uint8); m = k5[..., 0] >= 0
        ix[m] = [idx[tuple(c)] for c in k5[m].reshape(-1, 3).tolist()]
        return ix
    # Tile slots. The shared primary keeps tile 0, every tile of the Cherrygrove metatiles a seam needs, and
    # every primary tile reused; free slots take each map's overflow (one tile serves both maps when its
    # indices match, whatever the bank).
    keep_meta = {0} | {m for s in specs.values() for m in s['keep_meta']}
    keep = {0}
    for m in keep_meta:
        keep |= {e & 1023 for e in P.metatiles[m] if e}
    for j in jobs.values():
        if j['primary'] is not None:
            keep.add(j['primary'][0])
    free_slots = [i for i in range(512) if i not in keep]
    pri_tiles, pri_lookup = {}, {}
    def slot_tile(ix):
        for f, v in flips(ix):
            if v.tobytes() in pri_lookup:
                return pri_lookup[v.tobytes()], f
        assert len(pri_tiles) < len(free_slots), ('shared primary tile slots exhausted', len(free_slots))
        i = free_slots[len(pri_tiles)]
        pri_tiles[i] = ix.copy(); pri_lookup[ix.tobytes()] = i
        return i, 0
    out = {}
    for n in specs:
        sec, lookup, ent = [np.zeros((8, 8), np.uint8)], {np.zeros((8, 8), np.uint8).tobytes(): 0}, {}
        mine = sorted((k for k, j in jobs.items() if n in j['maps'] and j['primary'] is None), key=lambda k: (-jobs[k]['n'], k))
        for k in mine:
            j = jobs[k]; b = assign(n, setof(j)); ix = indices(j, n, b)
            hit = next(((lookup[v.tobytes()], f) for f, v in flips(ix) if v.tobytes() in lookup), None)
            if hit is None and len(sec) < SEC_TILES:
                lookup[ix.tobytes()] = len(sec); sec.append(ix.copy()); hit = (len(sec) - 1, 0)
            if hit is not None:
                ent[k] = entry(512 + hit[0], hit[1], b)
            else:
                t, f = slot_tile(ix); ent[k] = entry(t, f, b)
        out[n] = dict(sec_tiles=sec, entries=ent)
    def entry_of(n, k):
        j = jobs[k]
        if j['primary'] is not None:
            i, f, b = j['primary']; return entry(i, f, b)
        return out[n]['entries'][k]
    attr = lambda n, x, y: int(specs[n]['behavior'][y, x]) | ((NORMAL if specs[n]['above'][y, x] else COVERED) << 12)
    # Metatiles. Seam cells first: one id per distinct (jobs, attributes), reserved in both secondaries.
    seam_ids = {}
    for n in (upper, lower):
        for (x, y) in seam[n]:
            seam_ids.setdefault((tuple(plans[n][(x, y)]), attr(n, x, y)), 512 + len(seam_ids))
    prim_index = {(P.metatiles[m], P.attrs[m]): m for m in keep_meta}
    for n, s in specs.items():
        sec_meta = {}
        for (q, a), mid in seam_ids.items():
            sec_meta[(tuple([entry_of(n, b) for b, _ in q] + [entry_of(n, t) if t else 0 for _, t in q]), a, mid)] = mid
        seam_set = set(seam[n])
        by_key = {}
        nxt = [512 + len(seam_ids)]
        words = np.zeros((s['H'], s['W']), np.uint16)
        for y in range(s['H']):
            for x in range(s['W']):
                if (x, y) in s['placed']:
                    mid = s['placed'][(x, y)]
                elif (x, y) in seam_set:
                    mid = seam_ids[(tuple(plans[n][(x, y)]), attr(n, x, y))]
                else:
                    q = plans[n][(x, y)]
                    key = (tuple([entry_of(n, b) for b, _ in q] + [entry_of(n, t) if t else 0 for _, t in q]), attr(n, x, y))
                    if key in prim_index:
                        mid = prim_index[key]
                    else:
                        if key not in by_key:
                            by_key[key] = nxt[0]; nxt[0] += 1
                        mid = by_key[key]
                words[y, x] = mid | (int(s['collision'][y, x]) << 10) | (int(s['elevation'][y, x]) << 12)
        rows = [None] * (nxt[0] - 512)
        for (ents, a, mid) in sec_meta:
            rows[mid - 512] = (ents, a)
        for key, mid in by_key.items():
            rows[mid - 512] = key
        assert len(rows) <= 512, (n, 'secondary metatiles over budget', len(rows))
        pals = {b: [tuple(v << 3 for v in c) for c in slots(n, b)] for b in own[n]}
        for b, p in s['fixed_pal'].items():
            pals[b] = list(p)
        out[n].update(words=words, meta_rows=rows, pals=pals)
    shared_rgb = {b: [tuple(v << 3 for v in c) for c in sorted(cs)] for b, cs in shared.items()}
    report = dict(jobs=len(jobs), primary_reused=sum(j['primary'] is not None for j in jobs.values()),
                  seam_cells={n: len(v) for n, v in seam.items()}, seam_metatiles=len(seam_ids),
                  primary_slots=dict(free=len(free_slots), used=len(pri_tiles)),
                  maps={n: dict(secondary_tiles=len(o['sec_tiles']), secondary_metatiles=len(o['meta_rows']),
                                banks={b: len(p) for b, p in sorted(o['pals'].items())}) for n, o in out.items()},
                  shared_banks={b: len(p) for b, p in sorted(shared_rgb.items())})
    primary = dict(tiles=pri_tiles, pals=shared_rgb, keep_tiles=sorted(keep), keep_metatiles=sorted(keep_meta))
    return out, primary, report, seam

# --------------------------------------------------------------------------- write
def jasc(cols):
    cols = list(cols) + [(0, 0, 0)] * 15
    return '\r\n'.join(['JASC-PAL', '0100', '16', '0 0 0'] + [f'{c[0]} {c[1]} {c[2]}' for c in cols[:15]]) + '\r\n'

def write_primary(engine, primary):
    """CherrygrovePrimary's metatiles and attributes, copied as they are; its tiles, with the free slots
    holding the route tiles the secondaries cannot; palettes 4-5 from the route art. Palettes 0-3 (and
    6-15, which a primary never shows) are Cherrygrove's."""
    import shutil
    src, d = engine / 'data/tilesets/primary/cherrygrove', engine / 'data/tilesets/primary' / PRI_NAME
    (d / 'palettes').mkdir(parents=True, exist_ok=True)
    for f in ('metatiles.bin', 'metatile_attributes.bin'):
        shutil.copyfile(src / f, d / f)
    im = Image.open(src / 'tiles.png'); a = np.array(im)
    for i, t in primary['tiles'].items():
        a[(i // 16) * 8:(i // 16) * 8 + 8, (i % 16) * 8:(i % 16) * 8 + 8] = t
    o = Image.fromarray(a.astype(np.uint8), 'P'); o.putpalette(im.getpalette()); o.save(d / 'tiles.png', bits=4)
    for b in range(16):
        if b in SHARED_BANKS:
            (d / 'palettes' / f'{b:02}.pal').write_text(jasc(primary['pals'].get(b, [])))
        else:
            shutil.copyfile(src / 'palettes' / f'{b:02}.pal', d / 'palettes' / f'{b:02}.pal')

def write_secondary(engine, ts_name, o):
    d = engine / 'data/tilesets/secondary' / ts_name
    d.mkdir(parents=True, exist_ok=True); (d / 'palettes').mkdir(exist_ok=True)
    tiles = o['sec_tiles']
    rows = max(1, (len(tiles) + 15) // 16)
    sheet = np.zeros((rows * 8, 128), np.uint8)
    for i, t in enumerate(tiles):
        sheet[(i // 16) * 8:(i // 16) * 8 + 8, (i % 16) * 8:(i % 16) * 8 + 8] = t
    im = Image.fromarray(sheet, 'P'); im.putpalette([v for i in range(16) for v in (i * 17, i * 17, i * 17)] + [0] * 720)
    im.save(d / 'tiles.png', bits=4)
    for b in range(16):
        (d / 'palettes' / f'{b:02}.pal').write_text(jasc(o['pals'].get(b, []) if b >= 6 else []))
    (d / 'metatiles.bin').write_bytes(b''.join(struct.pack('<8H', *k[0]) for k in o['meta_rows']))
    (d / 'metatile_attributes.bin').write_bytes(struct.pack('<%dH' % len(o['meta_rows']), *[k[1] for k in o['meta_rows']]))

def register(engine, sym, name, primary=False):
    h = engine / 'src/data/tilesets/headers.h'; s = h.read_text()
    kind = 'primary' if primary else 'secondary'
    if f'gTileset_{sym} =' not in s:
        s = s.replace('// End Claude routes\n', f'const struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, .isSecondary = {"FALSE" if primary else "TRUE"}, .tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym}, .metatiles = gMetatiles_{sym}, .metatileAttributes = gMetatileAttributes_{sym}, .callback = NULL }};\n// End Claude routes\n', 1)
    h.write_text(s)
    g = engine / 'src/data/tilesets/graphics.h'; s = g.read_text()
    if f'gTilesetTiles_{sym}[]' not in s:
        s = s.rstrip('\n') + f'\n\nconst u32 gTilesetTiles_{sym}[] = INCGFX_U32("data/tilesets/{kind}/{name}/tiles.png", ".4bpp.fastSmol");\nconst u16 gTilesetPalettes_{sym}[][16] = {{\n' + ''.join(f'INCGFX_U16("data/tilesets/{kind}/{name}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n'
    g.write_text(s)
    m = engine / 'src/data/tilesets/metatiles.h'; s = m.read_text()
    if f'gMetatiles_{sym}[]' not in s:
        s = s.rstrip('\n') + f'\nconst u16 gMetatiles_{sym}[] = INCBIN_U16("data/tilesets/{kind}/{name}/metatiles.bin");\nconst u16 gMetatileAttributes_{sym}[] = INCBIN_U16("data/tilesets/{kind}/{name}/metatile_attributes.bin");\n'
    m.write_text(s)

def load_spec(path):
    z = np.load(path, allow_pickle=True)
    s = {k: z[k] for k in z.files}
    meta = json.loads(str(s.pop('meta')))
    s.update(meta)
    s['placed'] = {tuple(map(int, k.split(','))): int(v) for k, v in meta['placed'].items()}
    s['fixed_pal'] = {int(b): [tuple(c) for c in p] for b, p in meta['fixed_pal'].items()}
    s['keep_meta'] = set(meta['keep_meta'])
    s['plains'] = [s['plain0'], s['plain1']]
    return s

def save_spec(path, name, W, H, ground, flat, top, owner, above, behavior, collision, elevation, placed, fixed_pal, keep_meta, plains):
    meta = dict(name=name, W=W, H=H, placed={f'{x},{y}': int(m) for (x, y), m in placed.items()},
                fixed_pal={str(b): [list(c) for c in p] for b, p in fixed_pal.items()}, keep_meta=sorted(int(m) for m in keep_meta))
    np.savez_compressed(path, ground=ground, flat=flat, top=top, owner=np.asarray(owner).astype(str), above=above, behavior=behavior,
                        collision=collision, elevation=elevation, plain0=plains[0], plain1=plains[1], meta=json.dumps(meta))

# --------------------------------------------------------------------------- driver
ROOT = HERE.parents[3]
MAPS = dict(route30=dict(tool=HERE / 'pack.py', ts=('route30_hgss', 'Route30Hgss')),
            route31=dict(tool=HERE.parent / 'route31_catalog/pack.py', ts=('route31_hgss', 'Route31Hgss')))
UPPER, LOWER, OFFSET = 'route31', 'route30', -28     # Route 30's "up" connection: Route 31 column 0 at Route 30 column -28

def main(engine, install):
    import subprocess, tempfile
    tmp = Path(tempfile.mkdtemp(prefix='pair-pack-'))
    for n, m in MAPS.items():
        subprocess.run([sys.executable, str(m['tool']), str(engine), '--spec', str(tmp / f'{n}.npz')], check=True)
    specs = {n: load_spec(tmp / f'{n}.npz') for n in MAPS}
    out, primary, report, seam = pack_pair(engine, specs, UPPER, LOWER, OFFSET)
    print(json.dumps(report, default=int))
    if install:
        write_primary(engine, primary)
        register(engine, PRI_SYM, PRI_NAME, primary=True)
        for n, m in MAPS.items():
            write_secondary(engine, m['ts'][0], out[n]); register(engine, m['ts'][1], m['ts'][0])
        for n, m in MAPS.items():
            np.save(tmp / f'{n}-words.npy', out[n]['words'])
            subprocess.run([sys.executable, str(m['tool']), str(engine), '--install-words', str(tmp / f'{n}-words.npy')], check=True)
    ev = ROOT / 'gba/art/route30-catalog/evidence/pack'; ev.mkdir(parents=True, exist_ok=True)
    report['seam'] = {n: [list(c) for c in v] for n, v in seam.items()}
    (ev / 'pair-pack.json').write_text(json.dumps(report, indent=1, default=int) + '\n')
    (ROOT / 'gba/art/route30-catalog/source/pack/primary-state.json').write_text(json.dumps(dict(
        note='The shared Route 30/31 primary: CherrygrovePrimary with these tile slots and palettes 4-5 holding route art.',
        palettes={str(b): primary['pals'][b] for b in SHARED_BANKS}, tile_slots=sorted(primary['tiles']),
        kept_cherrygrove_tiles=primary['keep_tiles'], kept_cherrygrove_metatiles=primary['keep_metatiles']), default=int) + '\n')

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), '--install' in sys.argv)
