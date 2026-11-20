"""Gate G4 of docs/MAP_CHECKLIST.md: the automated checks every map must pass before owner review.

    python3 tools/gba/maps/map_gate.py ENGINE_CHECKOUT MapName [MapName ...]
        [--phg PHG_CHECKOUT]       decoded HGSS walkability comparison (needs gba/maps/gates/<MapName>.json)
        [--porymap DIR]            compare DIR/<MapName>.png (Porymap 6.3.1 probe export) with the native render
        [--build]                  run `make -j4` in ENGINE_CHECKOUT first
        [--out DIR]                write DIR/<MapName>.gate.json and seam/glitch crops for the review sheet

A map PASSES only when every check ran and passed. A check that could not run is NOT RUN, and the
map stays at G4. Deliberate differences go in the map's gate file, never in this script:

    gba/maps/gates/<MapName>.json
    {
      "hgss": "MAP_ROUTE_30",            # inventory row (docs/maps/HGSS_MAP_INVENTORY.csv)
      "offset": [5, 2],                  # native cell = HGSS tile + offset
      "adapt_walk": [[x, y], ...],       # native cells whose walkability deliberately differs from HGSS
      "adapt_warps": [0, 3],             # warp indices exempt from the entrance/return checks
      "adapt_seams": {"MAP_ROUTE_31": [[x, y], ...]},   # cells of the other map allowed to draw differently
      "reserve_tiles": [496, 511],       # secondary tile slots kept free (door frames)
      "notes": "why each adaptation exists"
    }

Checks
  glitch   every metatile the layout uses points at real tiles and palettes (no blank/garbage quadrants)
  budget   primary/secondary tiles, metatiles and palettes inside the engine limits, reserved slots free
  seams    every connection, both sides: cells visible across the seam draw the same pixels in both
           maps' tileset pairs (Gen 3 draws the neighbour's edge with its own tilesets)
  warps    every warp sits on a door/stair/ladder/arrow cell, its destination exists, and the
           destination warp leads back here
  walk     walkable cells equal decoded HGSS walkable cells (permissions in land_data) at the registered offset
  porymap  the Porymap export equals the native render pixel for pixel
  build    the ROM builds
"""
from __future__ import annotations
import json, re, struct, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(HERE), str(ROOT / 'tools/hoennconv')]
from tiles import Tileset            # noqa: E402

NUM_TILES_IN_PRIMARY, NUM_TILES_TOTAL = 512, 1024
NUM_METATILES_IN_PRIMARY, NUM_METATILES_TOTAL = 512, 1024
NUM_PALS_IN_PRIMARY, NUM_PALS_TOTAL = 6, 13
VIEW_X, VIEW_Y = 8, 5                 # cells visible either side of the player (generous: scrolling)
GATES = ROOT / 'gba/maps/gates'

# ----------------------------------------------------------------------------- engine data
class Engine:
    def __init__(self, path: Path):
        self.p = path
        self.layouts = {l['id']: l for l in json.loads((path / 'data/layouts/layouts.json').read_text())['layouts'] if 'id' in l}
        g = (path / 'src/data/tilesets/graphics.h').read_text()
        self.sym_dir = {}
        for m in re.finditer(r'gTilesetTiles_(\w+)\[\]\s*=\s*INCGFX_U32\("data/tilesets/(\w+)/(\w+)/tiles\.png"', g):
            self.sym_dir['gTileset_' + m.group(1)] = (m.group(2), m.group(3))
        self._ts = {}
        self.maps = {}
        for d in (path / 'data/maps').iterdir():
            j = d / 'map.json'
            if j.exists():
                m = json.loads(j.read_text())
                m['_dir'] = d.name
                self.maps[m['id']] = m
        self.by_name = {m['_dir']: m for m in self.maps.values()}
        self.warp_mb = warp_behaviors(path)

    def tileset(self, layout):
        key = (layout['primary_tileset'], layout['secondary_tileset'])
        if key not in self._ts:
            pk, pn = self.sym_dir[key[0]]
            sk, sn = self.sym_dir[key[1]]
            base = self.p / 'data/tilesets'
            ts = _load_tileset(base / pk / pn, base / sk / sn)
            self._ts[key] = ts
        return self._ts[key]

    def grid(self, layout):
        b = (self.p / layout['blockdata_filepath']).read_bytes()
        return np.array(struct.unpack('<%dH' % (len(b) // 2), b), dtype=np.uint16).reshape(layout['height'], layout['width'])

def _load_tileset(pdir, sdir):
    ts = Tileset.__new__(Tileset)
    ts.dirs = [pdir, sdir]
    ts.tiles, ts.pals, ts.blocks, ts.attrs = [], [], [], []
    from tiles import palette
    for folder in ts.dirs:
        image = Image.open(folder / 'tiles.png')
        ts.tiles.append([list(image.crop((x, y, x + 8, y + 8)).tobytes())
                         for y in range(0, image.height, 8) for x in range(0, image.width, 8)])
        ts.pals.append([palette(folder / 'palettes' / f'{n:02}.pal') for n in range(16)])
        ts.blocks.append(list(struct.iter_unpack('<8H', (folder / 'metatiles.bin').read_bytes())))
        a = (folder / 'metatile_attributes.bin').read_bytes()
        ts.attrs.append(list(struct.unpack('<%dH' % (len(a) // 2), a)))
    return ts

def behavior(ts, mid):
    part, idx = (1, mid - NUM_METATILES_IN_PRIMARY) if mid >= NUM_METATILES_IN_PRIMARY else (0, mid)
    a = ts.attrs[part]
    return a[idx] & 0xFF if idx < len(a) else None

def warp_behaviors(engine):
    """MB_ values the engine treats as warp entrances (doors, stairs, ladders, arrow warps...)."""
    names, n = {}, 0
    for line in (engine / 'include/constants/metatile_behaviors.h').read_text().split('enum', 1)[1].split('}', 1)[0].splitlines():
        m = re.match(r'\s*(MB_\w+)\s*(?:=\s*(\w+))?\s*,', line)
        if m:
            if m.group(2):
                n = int(m.group(2), 0)
            names[m.group(1)] = n
            n += 1
    preds = ['WarpDoor', 'Ladder', 'Escalator', 'NonAnimDoor', 'LavaridgeB1FWarp', 'Lavaridge1FWarp', 'AquaHideoutWarp',
             'MtPyreHole', 'MossdeepGymWarp', 'UnionRoomWarp', 'NorthArrowWarp', 'SouthArrowWarp', 'WestArrowWarp',
             'EastArrowWarp', 'DirectionalStairWarp', 'DeepSouthWarp']
    src = (engine / 'src/metatile_behavior.c').read_text()
    out = set()
    for p in preds:
        m = re.search(r'MetatileBehavior_Is' + p + r'\s*\([^)]*\)\s*\{(.*?)\n\}', src, re.S)
        if m:
            out |= {names[x] for x in re.findall(r'MB_\w+', m.group(1)) if x in names}
    return out

# ----------------------------------------------------------------------------- checks
def check_glitch(eng, layout, grid):
    ts = eng.tileset(layout)
    bad, black = [], set()
    pal_ok = [[any(c != (0, 0, 0) for c in pal[1:]) for pal in part] for part in ts.pals]
    for mid in sorted({int(v) & 1023 for v in grid.flat}):
        part, idx = (1, mid - 512) if mid >= 512 else (0, mid)
        if idx >= len(ts.blocks[part]):
            bad.append(dict(metatile=mid, problem='metatile id past the end of its tileset'))
            continue
        for q, e in enumerate(ts.blocks[part][idx]):
            tid, bank = e & 1023, e >> 12
            tpart, tidx = (1, tid - 512) if tid >= 512 else (0, tid)
            if tidx >= len(ts.tiles[tpart]):
                bad.append(dict(metatile=mid, quadrant=q, problem=f'tile {tid} does not exist'))
            elif bank >= NUM_PALS_TOTAL:
                bad.append(dict(metatile=mid, quadrant=q, problem=f'palette {bank} is past the 13 the field uses'))
            elif any(v % 16 for v in ts.tiles[tpart][tidx]) and not pal_ok[bank >= NUM_PALS_IN_PRIMARY][bank]:
                black.add(mid)          # draws solid black: fine for a deliberate void, a defect anywhere else
    cells = []
    if bad:
        badm = {b['metatile'] for b in bad}
        ys, xs = np.nonzero(np.isin(grid & 1023, list(badm)))
        cells = [[int(x), int(y)] for x, y in zip(xs, ys)][:40]
    blk = []
    if black:
        ys, xs = np.nonzero(np.isin(grid & 1023, list(black)))
        blk = [[int(x), int(y)] for x, y in zip(xs, ys)]
    return dict(ok=not bad, problems=bad[:40], cells=cells, black_metatiles=sorted(black), black_cells=len(blk),
                review='black_metatiles draw solid black (all-black palette); confirm each is a deliberate void' if black else '')

def check_budget(eng, layout, gate):
    ts = eng.tileset(layout)
    pt, st = len(ts.tiles[0]), len(ts.tiles[1])
    pm, sm = len(ts.blocks[0]), len(ts.blocks[1])
    used_pals = sorted({e >> 12 for part in ts.blocks for b in part for e in b})
    probs = []
    if pt > NUM_TILES_IN_PRIMARY: probs.append(f'primary has {pt} tiles (limit {NUM_TILES_IN_PRIMARY})')
    if st > NUM_TILES_TOTAL - NUM_TILES_IN_PRIMARY: probs.append(f'secondary has {st} tiles (limit 512)')
    if pm > NUM_METATILES_IN_PRIMARY: probs.append(f'primary has {pm} metatiles (limit 512)')
    if sm > NUM_METATILES_TOTAL - NUM_METATILES_IN_PRIMARY: probs.append(f'secondary has {sm} metatiles (limit 512)')
    if used_pals and max(used_pals) >= NUM_PALS_TOTAL: probs.append(f'palette {max(used_pals)} used (field has 13)')
    lo, hi = gate.get('reserve_tiles', [None, None])
    if lo is not None:
        refs = {e & 1023 for part in ts.blocks for b in part for e in b}
        clash = sorted(t for t in refs if lo <= t - 512 <= hi)
        if clash: probs.append(f'reserved secondary slots {lo}-{hi} used by metatiles: {clash[:10]}')
    return dict(ok=not probs, problems=probs, primary_tiles=pt, secondary_tiles=st, secondary_tiles_free=512 - st,
                primary_metatiles=pm, secondary_metatiles=sm, secondary_metatiles_free=512 - sm, palettes_used=used_pals)

def _render(ts, mid, cache):
    k = (id(ts), mid)
    if k not in cache:
        cache[k] = np.asarray(ts.render(mid).convert('RGB'))
    return cache[k]

def check_seams(eng, m, gate, cache, out=None):
    me_l = eng.layouts[m['layout']]
    me_g, me_t = eng.grid(me_l), eng.tileset(me_l)
    res, ok = {}, True
    for c in m.get('connections') or []:
        d, other = c['direction'], eng.maps.get(c['map'])
        if d not in ('up', 'down', 'left', 'right'):
            continue
        if other is None:
            res[c['map']] = dict(ok=False, problem='connected map is not in this checkout')
            ok = False
            continue
        ot_l = eng.layouts[other['layout']]
        ot_g, ot_t = eng.grid(ot_l), eng.tileset(ot_l)
        H, W = me_g.shape; h, w = ot_g.shape; o = c['offset']
        # other-map cell (ox, oy) for a position (x, y) in my coordinates
        to_other = {'up': lambda x, y: (x - o, y + h), 'down': lambda x, y: (x - o, y - H),
                    'left': lambda x, y: (x + w, y - o), 'right': lambda x, y: (x - W, y - o)}[d]
        walk = ((me_g >> 10) & 3) == 0
        seen = set()
        for y, x in zip(*np.nonzero(walk)):
            for dx in range(-VIEW_X, VIEW_X + 1):
                for dy in range(-VIEW_Y, VIEW_Y + 1):
                    ox, oy = to_other(int(x) + dx, int(y) + dy)
                    if 0 <= ox < w and 0 <= oy < h:
                        seen.add((ox, oy))
        allowed = {tuple(v) for v in gate.get('adapt_seams', {}).get(c['map'], [])}
        bad = sorted([x, y] for x, y in seen if (x, y) not in allowed and
                     (_render(me_t, int(ot_g[y, x]) & 1023, cache) != _render(ot_t, int(ot_g[y, x]) & 1023, cache)).any())
        res[f"{d}:{c['map']}"] = dict(ok=not bad, visible_cells=len(seen), drawn_differently=bad[:60], count=len(bad))
        ok &= not bad
    return dict(ok=ok, seams=res, note='checked from this side; run the gate on the neighbour for the other side')

def check_warps(eng, m, gate):
    lay = eng.layouts[m['layout']]
    g, ts = eng.grid(lay), eng.tileset(lay)
    probs = []
    skip = set(gate.get('adapt_warps', []))
    for i, wv in enumerate(m.get('warp_events') or []):
        if i in skip:
            continue
        x, y = wv['x'], wv['y']
        if not (0 <= x < g.shape[1] and 0 <= y < g.shape[0]):
            probs.append(f'warp {i} at ({x},{y}) is outside the map'); continue
        mb = behavior(ts, int(g[y, x]) & 1023)
        if mb not in eng.warp_mb:
            probs.append(f'warp {i} at ({x},{y}) sits on behavior {mb}, not a door/stair/ladder/arrow cell')
        dest = eng.maps.get(wv['dest_map'])
        if wv['dest_map'] in ('MAP_DYNAMIC', 'MAP_NONE'):
            continue
        if dest is None:
            probs.append(f'warp {i} leads to {wv["dest_map"]}, not in this checkout'); continue
        dw = dest.get('warp_events') or []
        try:
            did = int(wv['dest_warp_id'])
        except ValueError:
            continue
        if did >= len(dw):
            probs.append(f'warp {i} leads to {wv["dest_map"]} warp {did}, which does not exist'); continue
        if dw[did]['dest_map'] != m['id']:
            probs.append(f'warp {i} -> {wv["dest_map"]} warp {did}, which leads to {dw[did]["dest_map"]}, not back here')
    return dict(ok=not probs, problems=probs, warps=len(m.get('warp_events') or []))

def hgss_walk(phg: Path, const: str):
    """Decoded HGSS walkability for one map: True = walkable. From land_data permissions (collision bit 0x80)."""
    import narc, hgss_map
    maps_h = (phg / 'include/constants/maps.h').read_text()
    hid = int(re.search(r'#define ' + const + r'\s+(\d+)', maps_h).group(1))
    hdr = re.search(r'\[' + const + r'\]\s*=\s*\{(.*?)\n\s*\},', (phg / 'src/data/map_headers.h').read_text(), re.S).group(1)
    mx = re.search(r'\.matrixId\s*=\s*NARC_map_matrix_(\w+)_bin', hdr).group(1)
    d = (phg / 'files/fielddata/mapmatrix/map_matrix' / f'{mx}.bin').read_bytes()
    w, h, has_hdr, has_alt, nl = d[:5]
    p = 5 + nl
    hdrs = None
    if has_hdr:
        hdrs = struct.unpack_from('<%dH' % (w * h), d, p); p += 2 * w * h
    if has_alt:
        p += w * h
    lid = struct.unpack_from('<%dH' % (w * h), d, p)
    cells = [(x, z) for z in range(h) for x in range(w)
             if lid[z * w + x] != 0xFFFF and (hdrs is None or hdrs[z * w + x] == hid)]
    x0, z0 = min(c[0] for c in cells), min(c[1] for c in cells)
    x1, z1 = max(c[0] for c in cells), max(c[1] for c in cells)
    land = narc.load(phg / 'files/a/0/6/5')
    out = np.zeros(((z1 - z0 + 1) * 32, (x1 - x0 + 1) * 32), dtype=np.int8) - 1   # -1: no HGSS data
    for x, z in cells:
        ch = hgss_map.MapChunk.parse(land[lid[z * w + x]])
        for cy in range(32):
            for cx in range(32):
                _, col = ch.cell(cx, cy)
                out[(z - z0) * 32 + cy, (x - x0) * 32 + cx] = 0 if col & 0x80 else 1
    return out

def check_walk(eng, m, gate, phg):
    if not phg or not gate.get('hgss'):
        return dict(ok=None, problem='needs --phg and "hgss" + "offset" in the gate file')
    ref = hgss_walk(phg, gate['hgss'])
    g = eng.grid(eng.layouts[m['layout']])
    ox, oy = gate.get('offset', [0, 0])
    allowed = {tuple(v) for v in gate.get('adapt_walk', [])}
    diff, compared = [], 0
    for y in range(g.shape[0]):
        for x in range(g.shape[1]):
            hx, hy = x - ox, y - oy
            if not (0 <= hx < ref.shape[1] and 0 <= hy < ref.shape[0]) or ref[hy, hx] < 0:
                continue
            compared += 1
            native = ((int(g[y, x]) >> 10) & 3) == 0
            if native != bool(ref[hy, hx]) and (x, y) not in allowed:
                diff.append([x, y, 'open in GBA, blocked in HGSS' if native else 'blocked in GBA, open in HGSS'])
    return dict(ok=not diff, compared_cells=compared, differences=len(diff), first=diff[:60],
                note='HGSS ledges, water and counters can need adapt_walk entries; each must be explained in notes')

def native_image(eng, m):
    lay = eng.layouts[m['layout']]
    g = eng.grid(lay)
    return eng.tileset(lay).map_image([int(v) for v in g.flat], g.shape[1]).convert('RGB')

def check_porymap(eng, m, pdir):
    if not pdir:
        return dict(ok=None, problem='needs --porymap DIR with the Porymap 6.3.1 probe export')
    f = Path(pdir) / f"{m['_dir']}.png"
    if not f.exists():
        return dict(ok=None, problem=f'{f} missing')
    a = np.asarray(native_image(eng, m)); b = np.asarray(Image.open(f).convert('RGB'))
    # Porymap draws the padded layout (border cells round the map); find the map inside it.
    H, W = a.shape[:2]
    for oy in range(0, b.shape[0] - H + 1, 16):
        for ox in range(0, b.shape[1] - W + 1, 16):
            if np.array_equal(b[oy:oy + H, ox:ox + W], a):
                return dict(ok=True, offset_px=[ox, oy])
    if b.shape[:2] == a.shape[:2]:
        n = int((b != a).any(axis=2).sum())
        return dict(ok=False, problem=f'{n} pixels differ from the native render')
    return dict(ok=False, problem=f'native render {W}x{H} not found inside Porymap export {b.shape[1]}x{b.shape[0]}')

def check_build(engine):
    r = subprocess.run(['make', '-j4'], cwd=engine, capture_output=True, text=True)
    return dict(ok=r.returncode == 0, tail=(r.stdout + r.stderr)[-1500:] if r.returncode else '')

# ----------------------------------------------------------------------------- driver
def gate_file(name):
    f = GATES / f'{name}.json'
    return json.loads(f.read_text()) if f.exists() else {}

def run(engine, names, phg=None, porymap=None, build=False, out=None):
    results, all_ok = {}, True
    b = check_build(engine) if build else dict(ok=None, problem='pass --build')
    eng = Engine(engine)
    cache = {}
    for name in names:
        m = eng.by_name.get(name)
        if m is None:
            results[name] = dict(result='FAIL', problem=f'{name} not in {engine}/data/maps'); all_ok = False; continue
        gate = gate_file(name)
        lay = eng.layouts[m['layout']]
        g = eng.grid(lay)
        r = dict(build=b, glitch=check_glitch(eng, lay, g), budget=check_budget(eng, lay, gate),
                 seams=check_seams(eng, m, gate, cache), warps=check_warps(eng, m, gate),
                 walk=check_walk(eng, m, gate, phg), porymap=check_porymap(eng, m, porymap))
        states = {k: v['ok'] for k, v in r.items()}
        res = 'PASS' if all(s is True for s in states.values()) else ('FAIL' if any(s is False for s in states.values()) else 'NOT RUN')
        r['result'] = res
        r['gate_file'] = str(GATES / f'{name}.json') if gate else 'none'
        results[name] = r
        all_ok &= res == 'PASS'
        print(f'{name}: {res}')
        for k in ('build', 'glitch', 'budget', 'seams', 'warps', 'walk', 'porymap'):
            v = r[k]
            tag = {True: 'pass', False: 'FAIL', None: 'not run'}[v['ok']]
            detail = ''
            if k == 'budget':
                detail = f"secondary {v['secondary_tiles']}/512 tiles, {v['secondary_metatiles']}/512 metatiles, palettes {v['palettes_used']}"
            elif k == 'seams':
                detail = ', '.join(f"{s}: {x.get('count', x.get('problem'))} bad of {x.get('visible_cells', '?')}" for s, x in v['seams'].items()) or 'no connections'
            elif k == 'walk' and v['ok'] is not None:
                detail = f"{v['differences']} of {v['compared_cells']} cells differ"
            elif k == 'glitch' and v.get('black_cells'):
                detail = f"{v['black_cells']} cells draw solid black (metatiles {v['black_metatiles'][:6]}): confirm on the review sheet"
            elif k == 'warps':
                detail = f"{len(v['problems'])} problem(s) in {v['warps']} warps"
            elif v.get('problem'):
                detail = v['problem']
            elif v.get('problems'):
                detail = '; '.join(map(str, v['problems'][:3]))
            print(f'  {k:8} {tag:8} {detail}')
            for p in (v.get('problems') or [])[:8] if k in ('warps', 'budget', 'glitch') and v['ok'] is False else []:
                print(f'           - {p}')
        if out:
            Path(out).mkdir(parents=True, exist_ok=True)
            (Path(out) / f'{name}.gate.json').write_text(json.dumps(r, indent=1, default=str))
    return results, all_ok

def main(argv):
    args = argv[1:]
    def opt(k):
        if k in args:
            i = args.index(k); v = args[i + 1]; del args[i:i + 2]; return v
    phg, pory, out = opt('--phg'), opt('--porymap'), opt('--out')
    build = '--build' in args
    args = [a for a in args if a != '--build']
    engine, names = Path(args[0]).resolve(), args[1:]
    _, ok = run(engine, names, Path(phg).resolve() if phg else None, pory, build, out)
    return 0 if ok else 1

if __name__ == '__main__':
    sys.exit(main(sys.argv))
