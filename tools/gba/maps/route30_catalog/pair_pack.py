"""Joint native pack of Route 30 and Route 31, each on its own copy of CherrygrovePrimary.

    python3 tools/gba/maps/route30_catalog/pair_pack.py ENGINE_CHECKOUT [--install]

Each map's pack.py writes its spec (layers, traversal, layer types, cells placed by id, pinned banks:
`pack.py ENGINE --spec FILE`); this packs both with Mahogany's lossless rule (every native pixel keeps its
assembled RGB555 colour) and the seam rule, then installs the tilesets and has each pack.py install its map
words and events (`pack.py ENGINE --install-words FILE`).

  * Each map's primary is CherrygrovePrimary with the palettes the map draws from kept as they are and its
    other palettes and free tile slots holding route art. Route 30 keeps palettes 0 and 3 (the Cherrygrove
    cells it can see across its south seam, and its south band, draw only from those and the pinned blossom
    bank) and every Cherrygrove tile those cells use, so Cherrygrove draws the same in either primary
    (seams.py checks); palettes 1, 2, 4 and 5 hold route art. Route 31 never draws
    Cherrygrove's sea palette (1), so it keeps 0, 2 and 3 and takes 1, 4 and 5 for route art. Crossing
    between the two loads the other primary (the engine reloads a primary that differs).
  * A Gen 3 map draws a connected map's nearest rows with its own tilesets. Every cell of either route
    that a player can see across the Route 30/31 seam gets a secondary metatile id reserved in both
    secondaries (Route 29's rule for New Bark's ids): each map draws that cell's pixels with its own tiles
    and palettes at that id, so each map draws the other's seam cells exactly.
  * Palettes per map: its tile colour sets, the other map's seam cells included, packed into its free
    primary palettes and secondary banks 6-12 (Route 43's greedy packer, then its integer program). A
    map's pinned banks (Route 30: bank 10, the blossom trees Cherrygrove shows across its seam) keep their
    palettes.
  * Tiles CherrygrovePrimary already has in a kept palette are reused; the rest go into the map's
    secondary (512 tiles), then into its primary's free slots.
  * A map's mirror cells (Route 30: its west wall in the south band, which Cherrygrove can see) take
    secondary ids from the map's mirror base (596, after Cherrygrove's own 84), one per distinct cell, and
    the map's own cells with the same art share them; cherrygrove_wall.py defines the same ids in
    Cherrygrove's secondary with Cherrygrove's tiles and palettes.
"""
from __future__ import annotations
import json, struct, sys
from collections import Counter, deque
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
from tiles import Tileset                            # noqa: E402
from banks import pack_sets, milp_sets               # noqa: E402

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
    """CherrygrovePrimary: every tile under every kept bank and flip, every metatile."""
    def __init__(self, engine, keep):
        t = Tileset(engine, 'cherrygrove', 'cherrygrove')
        self.t, self.keep = t, tuple(keep)
        self.tiles = [np.array(x, np.uint8).reshape(8, 8) & 15 for x in t.tiles[0]]
        self.pals = [[tuple(c) for c in p] for p in t.pals[0][:6]]
        self.opaque, self.masked = {}, {}
        for i, ix in enumerate(self.tiles):
            for f, v in flips(ix):
                for b in self.keep:
                    rgb = np.array([self.pals[b][k] for k in v.ravel()], np.uint8).reshape(8, 8, 3)
                    key = rgb5(rgb).astype(np.int16)
                    self.masked.setdefault(np.where((v > 0)[..., None], key, -1).tobytes(), (i, f, b))
                    if (v > 0).all():
                        self.opaque.setdefault(key.tobytes(), (i, f, b))
        self.metatiles = [tuple(int(e) for e in m) for m in t.blocks[0]]
        self.attrs = list(t.attrs[0])
        self.pal5 = {b: frozenset(tuple(int(v) >> 3 for v in c) for c in self.pals[b][1:16]) for b in self.keep}
    def match(self, j):
        return (self.opaque if j['layer'] == 0 else self.masked).get(j['k5'].tobytes())

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

def bank_sets(sets, banks, label):
    """Exact banks for a map's colour sets: Route 43's greedy packer, then its integer program."""
    new = pack_sets(sets, len(banks)) if sets else []
    if new is None:
        maximal = sorted((c for c in sets if not any(c < d for d in sets)), key=lambda c: (-len(c), sorted(c)))
        new = milp_sets(maximal, len(banks), fixed=[(0, 0)], time_limit=1200)
    assert new is not None, f'{label}: art does not fit its banks'
    new = list(new) + [set()] * (len(banks) - len(new))
    return {b: frozenset(c) for b, c in zip(banks, new)}

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
def pack_pair(engine, specs, maps, upper, lower, offset):
    """specs: {name: spec}; maps: {name: dict(keep=primary palettes kept, free=primary palettes for route
    art)}; upper/lower: names of the map above and below; offset: the lower map's "up" connection offset
    (the upper map's column 0 at the lower map's column `offset`)."""
    jobs = {}
    plans = {n: plan_cells(s, jobs) for n, s in specs.items()}
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
    attr = lambda n, x, y: int(specs[n]['behavior'][y, x]) | ((NORMAL if specs[n]['above'][y, x] else COVERED) << 12)
    seam_ids = {}
    for n in (upper, lower):
        for (x, y) in seam[n]:
            seam_ids.setdefault((tuple(plans[n][(x, y)]), attr(n, x, y)), 512 + len(seam_ids))
    out, report = {}, dict(jobs=len(jobs), seam_cells={n: len(v) for n, v in seam.items()}, seam_metatiles=len(seam_ids), maps={})
    for n, s in specs.items():
        P = Primary(engine, maps[n]['keep'])
        mine = sorted((k for k, j in jobs.items() if n in j['maps']), key=lambda k: (-jobs[k]['n'], k))
        reuse = {k: P.match(jobs[k]) for k in mine}
        pinned = {b: frozenset(tuple(int(v) >> 3 for v in c) for c in p) for b, p in s['fixed_pal'].items()}
        fixed = {**P.pal5, **pinned}
        free = list(maps[n]['free']) + [b for b in SEC_BANKS if b not in pinned]
        sets = {st for st in (setof(jobs[k]) for k in mine if reuse[k] is None) if not any(st <= f for f in fixed.values())}
        assert all(len(st) <= 15 for st in sets), (n, 'a tile holds more than 15 colours')
        pal = {**bank_sets(sets, free, n), **pinned}
        order = {b: [tuple(int(v) >> 3 for v in c) for c in P.pals[b][1:16]] for b in P.keep}
        order.update({b: [tuple(int(v) >> 3 for v in c) for c in p] for b, p in s['fixed_pal'].items()})
        for b in free:
            order[b] = sorted(pal[b])
        def assign(st):
            for b, f in fixed.items():
                if st <= f:
                    return b
            return next(b for b in free if st <= pal[b])
        def indices(j, bank):
            idx = {}
            for i, c in enumerate(order[bank]):
                idx.setdefault(c, i + 1)
            k5 = j['k5']; ix = np.zeros((8, 8), np.uint8); m = k5[..., 0] >= 0
            ix[m] = [idx[tuple(c)] for c in k5[m].reshape(-1, 3).tolist()]
            return ix
        # Tile slots: the primary keeps tile 0, every tile of the Cherrygrove metatiles a seam needs, and
        # every tile reused; free slots take what the secondary cannot.
        keep_meta = {0} | set(s['keep_meta'])
        keep = {0}
        for m in keep_meta:
            keep |= {e & 1023 for e in P.metatiles[m] if e}
        for m in keep_meta:
            assert all((e >> 12) in P.keep or (e >> 12) in pinned for e in P.metatiles[m] if e), (n, 'kept metatile draws a freed palette', m)
        keep |= {r[0] for r in reuse.values() if r is not None}
        free_slots = [i for i in range(512) if i not in keep]
        sec, lookup, ent, pri_tiles, pri_lookup = [np.zeros((8, 8), np.uint8)], {np.zeros((8, 8), np.uint8).tobytes(): 0}, {}, {}, {}
        for k in mine:
            if reuse[k] is not None:
                i, f, b = reuse[k]; ent[k] = entry(i, f, b); continue
            j = jobs[k]; b = assign(setof(j)); ix = indices(j, b)
            hit = next(((lookup[v.tobytes()], f) for f, v in flips(ix) if v.tobytes() in lookup), None)
            if hit is None and len(sec) < SEC_TILES:
                lookup[ix.tobytes()] = len(sec); sec.append(ix.copy()); hit = (len(sec) - 1, 0)
            if hit is not None:
                ent[k] = entry(512 + hit[0], hit[1], b); continue
            hit = next(((pri_lookup[v.tobytes()], f) for f, v in flips(ix) if v.tobytes() in pri_lookup), None)
            if hit is None:
                assert len(pri_tiles) < len(free_slots), (n, 'primary tile slots exhausted', len(free_slots))
                i = free_slots[len(pri_tiles)]; pri_tiles[i] = ix.copy(); pri_lookup[ix.tobytes()] = i; hit = (i, 0)
            ent[k] = entry(hit[0], hit[1], b)
        defn = lambda q: tuple([ent[b] for b, _ in q] + [ent[t] if t else 0 for _, t in q])
        # Metatiles: the seam block first (the same ids in both secondaries), then this map's own.
        rows = [None] * len(seam_ids)
        for (q, a), mid in seam_ids.items():
            rows[mid - 512] = (defn(q), a)
        prim_index = {(P.metatiles[m], P.attrs[m]): m for m in keep_meta}
        by_key, seam_set = {}, set(seam[n])
        # Mirror cells: their own block of ids from the mirror base; the ids between take this map's own.
        if s['mirror_cells']:
            base = s['mirror_base'] - 512
            assert base >= len(rows), (n, 'mirror base inside the seam block')
            rows += [None] * (base - len(rows))
            for (x, y) in sorted(s['mirror_cells'], key=lambda c: (c[1], c[0])):
                key = (defn(plans[n][(x, y)]), attr(n, x, y))
                if key not in by_key:
                    by_key[key] = 512 + len(rows); rows.append(key)
        holes = deque(i for i, r in enumerate(rows) if r is None)
        def new_id(key):
            if holes:
                i = holes.popleft(); rows[i] = key
            else:
                i = len(rows); rows.append(key)
            return 512 + i
        words = np.zeros((s['H'], s['W']), np.uint16)
        for y in range(s['H']):
            for x in range(s['W']):
                if (x, y) in s['placed']:
                    mid = s['placed'][(x, y)]
                elif (x, y) in seam_set:
                    mid = seam_ids[(tuple(plans[n][(x, y)]), attr(n, x, y))]
                else:
                    key = (defn(plans[n][(x, y)]), attr(n, x, y))
                    if key in prim_index:
                        mid = prim_index[key]
                    else:
                        if key not in by_key:
                            by_key[key] = new_id(key)
                        mid = by_key[key]
                words[y, x] = mid | (int(s['collision'][y, x]) << 10) | (int(s['elevation'][y, x]) << 12)
        assert len(rows) <= 512, (n, 'secondary metatiles over budget', len(rows))
        rows = [r if r is not None else (tuple([0] * 8), 0) for r in rows]
        mirror_ids = sorted({int(words[y, x]) & 1023 for x, y in s['mirror_cells']})
        rgb = lambda b: list(s['fixed_pal'][b]) if b in s['fixed_pal'] else [tuple(v << 3 for v in c) for c in order[b]]
        out[n] = dict(sec_tiles=sec, words=words, meta_rows=rows, pals={b: rgb(b) for b in SEC_BANKS if b in order},
                      primary=dict(tiles=pri_tiles, pals={b: rgb(b) for b in maps[n]['free']}, keep_tiles=sorted(keep), keep_metatiles=sorted(keep_meta)))
        report['maps'][n] = dict(jobs=len(mine), primary_reused=sum(r is not None for r in reuse.values()), secondary_tiles=len(sec),
                                 primary_slots=dict(free=len(free_slots), used=len(pri_tiles)), secondary_metatiles=len(rows), mirror_ids=mirror_ids,
                                 banks={b: len(order[b]) for b in sorted(order) if b not in P.keep})
    return out, report, seam

# --------------------------------------------------------------------------- write
def jasc(cols):
    cols = list(cols) + [(0, 0, 0)] * 15
    return '\r\n'.join(['JASC-PAL', '0100', '16', '0 0 0'] + [f'{c[0]} {c[1]} {c[2]}' for c in cols[:15]]) + '\r\n'

def write_primary(engine, name, primary):
    """CherrygrovePrimary's metatiles and attributes, copied as they are; its tiles, with the free slots
    holding the route tiles its secondary cannot; the freed palettes from the route art. The kept palettes
    (and 6-15, which a primary never shows) are Cherrygrove's."""
    import shutil
    src, d = engine / 'data/tilesets/primary/cherrygrove', engine / 'data/tilesets/primary' / name
    (d / 'palettes').mkdir(parents=True, exist_ok=True)
    for f in ('metatiles.bin', 'metatile_attributes.bin'):
        shutil.copyfile(src / f, d / f)
    im = Image.open(src / 'tiles.png'); a = np.array(im)
    for i, t in primary['tiles'].items():
        a[(i // 16) * 8:(i // 16) * 8 + 8, (i % 16) * 8:(i % 16) * 8 + 8] = t
    o = Image.fromarray(a.astype(np.uint8), 'P'); o.putpalette(im.getpalette()); o.save(d / 'tiles.png', bits=4)
    for b in range(16):
        if b in primary['pals']:
            (d / 'palettes' / f'{b:02}.pal').write_text(jasc(primary['pals'][b]))
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

def unregister(engine, sym, name, primary=False):
    """Drop a tileset this pack no longer installs (registrations and files)."""
    import re, shutil
    h = engine / 'src/data/tilesets/headers.h'
    h.write_text(''.join(l for l in h.read_text().splitlines(True) if f'gTileset_{sym} =' not in l))
    g = engine / 'src/data/tilesets/graphics.h'
    g.write_text(re.sub(r'\n\nconst u32 gTilesetTiles_%s\[\] = [^\n]*\nconst u16 gTilesetPalettes_%s\[\]\[16\] = \{\n(?:[^\n]*\n)*?\};\n' % (sym, sym), '\n', g.read_text()))
    m = engine / 'src/data/tilesets/metatiles.h'
    m.write_text(''.join(l for l in m.read_text().splitlines(True) if f'gMetatiles_{sym}[]' not in l and f'gMetatileAttributes_{sym}[]' not in l))
    d = engine / 'data/tilesets' / ('primary' if primary else 'secondary') / name
    if d.exists():
        shutil.rmtree(d)

def load_spec(path):
    z = np.load(path, allow_pickle=True)
    s = {k: z[k] for k in z.files}
    meta = json.loads(str(s.pop('meta')))
    s.update(meta)
    s['placed'] = {tuple(map(int, k.split(','))): int(v) for k, v in meta['placed'].items()}
    s['fixed_pal'] = {int(b): [tuple(c) for c in p] for b, p in meta['fixed_pal'].items()}
    s['keep_meta'] = set(meta['keep_meta'])
    s['plains'] = [s['plain0'], s['plain1']]
    s['mirror_cells'] = [tuple(c) for c in meta.get('mirror_cells', [])]
    s['mirror_base'] = meta.get('mirror_base')
    return s

def save_spec(path, name, W, H, ground, flat, top, owner, above, behavior, collision, elevation, placed, fixed_pal, keep_meta, plains,
              mirror_cells=(), mirror_base=None):
    meta = dict(name=name, W=W, H=H, placed={f'{x},{y}': int(m) for (x, y), m in placed.items()},
                fixed_pal={str(b): [list(c) for c in p] for b, p in fixed_pal.items()}, keep_meta=sorted(int(m) for m in keep_meta),
                mirror_cells=[[int(x), int(y)] for x, y in mirror_cells], mirror_base=mirror_base)
    np.savez_compressed(path, ground=ground, flat=flat, top=top, owner=np.asarray(owner).astype(str), above=above, behavior=behavior,
                        collision=collision, elevation=elevation, plain0=plains[0], plain1=plains[1], meta=json.dumps(meta))

# --------------------------------------------------------------------------- driver
ROOT = HERE.parents[3]
MAPS = dict(route30=dict(tool=HERE / 'pack.py', ts=('route30_hgss', 'Route30Hgss'), pri=('cherrygrove_route30', 'CherrygroveRoute30Primary'),
                         keep=(0, 3), free=(1, 2, 4, 5), art=ROOT / 'gba/art/route30-catalog'),
            route31=dict(tool=HERE.parent / 'route31_catalog/pack.py', ts=('route31_hgss', 'Route31Hgss'), pri=('cherrygrove_route31', 'CherrygroveRoute31Primary'),
                         keep=(0, 2, 3), free=(1, 4, 5), art=ROOT / 'gba/art/route31-catalog'))
UPPER, LOWER, OFFSET = 'route31', 'route30', -27     # Route 30's "up" connection: Route 31 column 0 at Route 30 column -27
RETIRED = [('Route30Route31Primary', 'route30_31')]   # the earlier shared primary

def main(engine, install):
    import subprocess, tempfile
    tmp = Path(tempfile.mkdtemp(prefix='pair-pack-'))
    for n, m in MAPS.items():
        subprocess.run([sys.executable, str(m['tool']), str(engine), '--spec', str(tmp / f'{n}.npz')], check=True)
    specs = {n: load_spec(tmp / f'{n}.npz') for n in MAPS}
    out, report, seam = pack_pair(engine, specs, MAPS, UPPER, LOWER, OFFSET)
    print(json.dumps(report, default=int))
    if install:
        for sym, name in RETIRED:
            unregister(engine, sym, name, primary=True)
        for n, m in MAPS.items():
            write_primary(engine, m['pri'][0], out[n]['primary']); register(engine, m['pri'][1], m['pri'][0], primary=True)
            write_secondary(engine, m['ts'][0], out[n]); register(engine, m['ts'][1], m['ts'][0])
        for n, m in MAPS.items():
            np.save(tmp / f'{n}-words.npy', out[n]['words'])
            subprocess.run([sys.executable, str(m['tool']), str(engine), '--install-words', str(tmp / f'{n}-words.npy')], check=True)
    report['seam'] = {n: [list(c) for c in v] for n, v in seam.items()}
    for n, m in MAPS.items():
        (m['art'] / 'evidence/pack').mkdir(parents=True, exist_ok=True); (m['art'] / 'source/pack').mkdir(parents=True, exist_ok=True)
        (m['art'] / 'evidence/pack/pair-pack.json').write_text(json.dumps(report, indent=1, default=int) + '\n')
        p = out[n]['primary']
        (m['art'] / 'source/pack/primary-state.json').write_text(json.dumps(dict(
            note=f'{m["pri"][0]}: CherrygrovePrimary with palettes {list(m["free"])} and these tile slots holding route art.',
            palettes={str(b): c for b, c in p['pals'].items()}, tile_slots=sorted(p['tiles']),
            kept_cherrygrove_tiles=p['keep_tiles'], kept_cherrygrove_metatiles=p['keep_metatiles']), default=int) + '\n')

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), '--install' in sys.argv)
