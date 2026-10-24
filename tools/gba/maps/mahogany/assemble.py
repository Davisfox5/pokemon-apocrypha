"""Mahogany Town: native art assembled under docs/GBA_MAP_RECONSTRUCTION.md.

    python3 tools/gba/maps/mahogany/assemble.py PHG_CHECKOUT CATALOG_CHECKOUT ENGINE_CHECKOUT

The owner rejected the element build (flat textures, wrong houses, wrong rock depth) and the
direct HGSS conversion (it did not follow the guide); on the third draft the owner found the
rock faces still wrong and named Blackthorn as the reference. So:

1. Reference: trace.py registers decoded HGSS land_data chunk 85 to native cells 1:1 (numbered
   sheets, material grid, traversal ledger); elements.ledger decodes it flat, cell by cell.
2. Rock, as Blackthorn's installed rock: every HGSS height layer is one terrace (floor 0, raised
   lawns 1, mountain 2; source/assemble/terrace-grid.txt), drawn with FRLG General's mountain
   nine-slice, over-rock pieces and inner corners in the Johto rock ramp, one face per metatile,
   as a top-layer overlay on plain ground (elements.rock_frlg, Blackthorn's rock_frlg).
3. Shared art, copied unchanged with hashes into source/shared-art/ from the Johto catalog
   (CATALOG_CHECKOUT is a checkout of branch codex/violet-city):
     ground      the accepted Cherrygrove/Route 36 painter (claude_cherrygrove/ground.py), run on
                 an 8 px lawn/road grid read from HGSS's own flat ground colours
     ledges      L11/L12/L13 (warm Johto ledge ends and run)
     trees       T01 on each decoded 2x2 HGSS root
     signs       P12 signpost, P13 information plaque, P15 Gym marker
     buildings   C06 Pokemon Center, G01a front gatehouse (approved-buildings.json)
4. Local assets, authored only where the catalog has none (source/local-art/): the two houses,
   the Gym, the two lookout towers and the antenna tree from HGSS's own models and textures
   (transparent, HGSS texture colours, no baked ground); the white flower patch from HGSS's
   flower03 texture; and the west-facing ledge, Emerald's native jump-west ledge (general
   metatile 0x85) recoloured onto the L11-L13 ramp.

Writes source/assemble/layers.npz (ground RGB with ledges and flowers, rock RGBA, objects RGBA,
object owner, terrace levels), placements.json, terrace-grid.txt, evidence/assemble/*.png.
"""
from __future__ import annotations
import hashlib, json, shutil, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import elements as E                                 # noqa: E402
from claude_cherrygrove import ground as G           # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/mahogany-town'
SRC, EV = ART / 'source', ART / 'evidence'
TRACE, SHARED, LOCAL = SRC / 'trace', SRC / 'shared-art', SRC / 'local-art'
OUT, OEV = SRC / 'assemble', EV / 'assemble'
W = H = 32
PX = 16

CATALOG = {  # local name -> catalog path (branch codex/violet-city)
    'T01.png': 'gba/art/johto-common/trees/source/T01.png',
    'P12.png': 'gba/art/johto-common/scenery/source/P12.png',
    'P13.png': 'gba/art/johto-common/scenery/source/P13.png',
    'P15.png': 'gba/art/johto-common/scenery/source/P15.png',
    'L11.png': 'gba/art/johto-common/scenery/source/L11.png',
    'L12.png': 'gba/art/johto-common/scenery/source/L12.png',
    'L13.png': 'gba/art/johto-common/scenery/source/L13.png',
    'G01a.png': 'gba/art/johto-common-review/gates/refinement-4/G01a.png',
}
WAVE = True              # the approved painter's 32 px rim wave
PATH_CORE = 32           # the approved painter's full 32 px road texture
FLOOR = 4                # HGSS height of the town floor; raised lawns stand at 5, the mountain at 6

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p): return np.array(Image.open(p).convert('RGBA'))

def stage_shared(catalog):
    """Copy every catalog master used here, unchanged, with its hash and the catalog commit."""
    commit = subprocess.run(['git', '-C', str(catalog), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    prov = json.loads((SHARED / 'provenance.json').read_text()) if (SHARED / 'provenance.json').exists() else {}
    prov['catalog'] = dict(branch='codex/violet-city', commit=commit,
                           rule='Masters copied byte for byte; native tile ids and palette slots may differ, visible colours do not.')
    for name, rel in CATALOG.items():
        dst = SHARED / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(catalog / rel, dst)
        prov[name] = dict(source=rel, sha256=sha(dst))
    for k in [k for k in prov if k.startswith('rock/')]:     # the third draft's R02 rock is retired
        del prov[k]
    (SHARED / 'provenance.json').write_text(json.dumps(prov, indent=2) + '\n')

# --------------------------------------------------------------------------- rock
def terraces(cells):
    """Blackthorn's rock structure: every HGSS height layer is one Gen 3 terrace. A rock cell
    (ledger label T, E, S, W or N: HGSS's cliff and wall cells, decoded flat) stands at its
    rock peak above the floor (mountain 2, the low walls round the raised lawns 1); every other
    cell at its ground height (floor 0, raised lawns 1; under a tree crown or a roof, the
    cell's lowest point). So a low wall is the face of the lawn terrace above it, not a ridge."""
    lab = np.array([[c['lab'] for c in row] for row in cells])
    rock = np.isin(lab, list(E.ROCK))
    d = np.zeros((H, W), int)
    for y in range(H):
        for x in range(W):
            c = cells[y][x]
            d[y, x] = max(1, round(c['peak']) - FLOOR) if rock[y, x] else max(0, round(c['ground']) - FLOOR)
    pad = np.pad(d, 1, mode='edge')
    lower = np.zeros((H, W), bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                lower |= pad[1 + dy:1 + dy + H, 1 + dx:1 + dx + W] < d
    return d, rock & lower, rock

def frlg_rock(cells, ground):
    """Blackthorn's installed rock (style C, tools/gba/maps/blackthorn/elements.rock_frlg, kept
    here as elements.rock_frlg): FRLG General's mountain nine-slice, its over-rock version
    where an edge drops to a lower terrace, and its four inner corners, recoloured to the
    Johto rock ramp, one face per metatile. The rock is a top-layer overlay; under its clear
    pixels the bottom carries the plainest 8x8 block of the ground beyond the edge, and its
    cast shadow is Cherrygrove's border grey. Ledges keep their own art (no FRLG join piece)."""
    d, face, isrock = terraces(cells)
    E.layers = lambda _cells: (d, face, isrock)
    plain_cells = [[dict(c, lab='.' if c['lab'] in E.LEDGES else c['lab']) for c in row] for row in cells]
    out, over, _, piece = E.rock_frlg(plain_cells, ground, E.frlg_pieces(ENGINE), E.cherry_textures())
    return out, over, d, isrock, piece

def paint_ground(q):
    """The accepted Cherrygrove/Route 36 painter (claude_cherrygrove/ground.paint) on an 8 px
    material grid: its own textures, rim profiles, 32 px wobble wave and order, with each
    material square 8 px instead of 16 so lawn edges can sit mid-cell where HGSS puts them.
    WAVE and PATH_CORE can trade the wave and the road's 32 px texture for tiles (both on here)."""
    U = 8
    hq, wq = q.shape
    h, w = hq * U, wq * U
    tex = G.textures()
    tex[G.PATH] = np.tile(tex[G.PATH][:PATH_CORE, :PATH_CORE], (32 // PATH_CORE, 32 // PATH_CORE, 1))
    ys, xs = np.mgrid[0:h, 0:w]
    wave = np.array(G.WAVE) if WAVE else np.zeros(32, int)
    dx = wave[ys % 32]; dy = wave[(xs + 11) % 32]
    sx = np.clip(xs + dx, 0, w - 1) // U; sy = np.clip(ys + dy, 0, h - 1) // U
    mat = q[sy, sx]
    out = np.zeros((h, w, 4), np.uint8); out[..., 3] = 255
    for m, t in tex.items():
        mm = mat == m
        out[..., :3][mm] = t[ys[mm] % t.shape[0], xs[mm] % t.shape[1]]
    dist = {m: G._chamfer(mat == m) for m in tex}
    for (a, b) in [(G.GRASS, G.PATH), (G.GRASS, G.SAND), (G.PATH, G.SAND), (G.PATH, G.SEA), (G.GRASS, G.SEA), (G.SAND, G.SEA), (G.ROCK, G.SEA)]:
        pa, pb = G.PROFILES[(a, b)]
        if not (mat == a).any() or not (mat == b).any():
            continue
        for k, c in enumerate(pa):
            out[..., :3][(mat == a) & (dist[b] == k + 1)] = c
        for k, c in enumerate(pb):
            out[..., :3][(mat == b) & (dist[a] == k + 1)] = c
    return out, mat

def ground_quadrants(cells, rock):
    """Lawn or road per 8 px quadrant, read from HGSS's own flat ground colours (lawn greens
    against road sand: HGSS's road01_r rim texture is half lawn, so its material name
    misleads); quadrants HGSS shows too little open ground in keep their cell's material.
    Ledge stones are read past: a south ledge cell's lower quadrants and a west ledge cell's
    left ones take the ground beside them."""
    _, _, _, rgb = E.topdown(PHG)
    rgb = rgb.astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    rockpx = np.repeat(np.repeat(rock, PX, 0), PX, 1)
    lawn = (g > r + 20) & ~rockpx
    sand = (r >= g) & (r > 180) & (b < 175) & ~rockpx
    q = np.repeat(np.repeat(np.array([[G.PATH if c['floor'] == 'sand' else G.GRASS for c in row] for row in cells]), 2, 0), 2, 1).astype(np.int8)
    for qy in range(H * 2):
        for qx in range(W * 2):
            if cells[qy // 2][qx // 2]['lab'] == 'F':
                q[qy, qx] = G.GRASS                       # HGSS's woods stand on lawn
                continue
            sl = np.s_[qy * 8:qy * 8 + 8, qx * 8:qx * 8 + 8]
            nl, ns = int(lawn[sl].sum()), int(sand[sl].sum())
            if ns >= 32 and ns > nl:
                q[qy, qx] = G.PATH
            elif nl >= 8:
                q[qy, qx] = G.GRASS
    for y in range(H):
        for x in range(W):
            c = cells[y][x]['lab']
            if c in 'LJ':
                q[2 * y + 1, 2 * x:2 * x + 2] = q[2 * y, 2 * x:2 * x + 2]
            if c in 'QJ':
                q[2 * y:2 * y + 2, 2 * x] = q[2 * y:2 * y + 2, 2 * x + 1]
    return q

# --------------------------------------------------------------------------- local assets
def west_ledge():
    """Emerald general metatile 0x85 (MB_JUMP_WEST): its top-layer stone band, recoloured by
    tone onto the warm L11-L13 ramp."""
    d = ENGINE / 'data/tilesets/primary/general'
    tiles = np.array(Image.open(d / 'tiles.png')) & 15
    T = [tiles[y:y + 8, x:x + 8] for y in range(0, tiles.shape[0], 8) for x in range(0, tiles.shape[1], 8)]
    pal = lambda b: np.array(list(map(int, (d / f'palettes/{b:02}.pal').read_text().split()[3:51])), np.uint8).reshape(16, 3)
    M = np.frombuffer((d / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
    out = np.zeros((16, 16, 4), np.uint8)
    for q in range(4):
        e = int(M[0x85][4 + q]); t = T[e & 1023]
        if e & 0x400: t = t[:, ::-1]
        if e & 0x800: t = t[::-1]
        oy, ox = (q // 2) * 8, (q % 2) * 8
        out[oy:oy + 8, ox:ox + 8, :3] = pal(e >> 12)[t]; out[oy:oy + 8, ox:ox + 8, 3] = (t > 0) * 255
    tone = {(98, 65, 82): (104, 72, 56), (131, 131, 139): (104, 72, 56), (131, 90, 90): (128, 88, 64),
            (156, 115, 115): (160, 112, 80), (189, 148, 139): (192, 144, 96), (222, 180, 164): (192, 144, 96)}
    a = out[..., 3] > 0
    for (src, dst) in tone.items():
        out[a & (out[..., :3] == src).all(-1), :3] = dst
    assert {tuple(c) for c in out[a][:, :3].tolist()} <= set(tone.values()), 'unmapped 0x85 colour'
    Image.fromarray(out).save(LOCAL / 'ledge-west.png')
    return out

def ledge_corner(q, l12):
    """Where the west run turns into the south run (HGSS (6,12)): the west band down to the
    south run's top, then the south run's stone band."""
    out = np.zeros((16, 16, 4), np.uint8)
    out[:9] = q[:9]
    a = l12[..., 3] > 0
    out[a] = l12[a]
    Image.fromarray(out).save(LOCAL / 'ledge-corner.png')
    return out

BUILDINGS = {  # local master -> HGSS placements (hgss-render.json model ids, door models with their house)
    'house': [134, 135], 'gym': [138, 16], 'tower': [249], 'antenna_tree': [136],
}

def local_buildings(phg):
    """HGSS's own building models rendered at true heights (hgss_render), cut out exactly:
    transparent outside the model, every colour an HGSS texture colour."""
    import hgss_render as R
    R.SNAP = True
    r = R.render(phg)
    fg, own = np.array(r['fg']), r['fg_owner']
    placed = []
    for i, b in enumerate(r['buildings']):
        b['index'] = i
    groups = []                                                 # one placement per main model, with its door model
    for b in r['buildings']:
        for name, ids in BUILDINGS.items():
            if b['model'] == ids[0]:
                parts = [b['index']] + [o['index'] for o in r['buildings'] if len(ids) > 1 and o['model'] == ids[1]
                                        and abs(o['pos'][0] - b['pos'][0]) < 2 and abs(o['pos'][2] - b['pos'][2]) < 3]
                groups.append((name, b, parts))
    for name, b, parts in groups:
        m = np.isin(own, parts) & (fg[..., 3] > 0)
        ys, xs = np.nonzero(m)
        x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
        a = fg[y0:y1, x0:x1].copy(); a[~m[y0:y1, x0:x1]] = 0
        # Native tile fit: the cut-out's top-left moves to the nearest 8 px tile corner (at
        # most 4 px), so the building occupies whole tiles instead of straddling one more.
        sx, sy = int(round(x0 / 8.0)) * 8, int(round(y0 / 8.0)) * 8
        placed.append(dict(name=name, model=b['model'], pos=[float(v) for v in b['pos']], xy=[sx, sy], hgss_xy=[x0, y0], art=a))
    # One master per model: identical renders (the two houses, the two towers) share a file.
    masters = {}
    for p in placed:
        same = next((k for k, v in masters.items() if k.startswith(p['name']) and v.shape == p['art'].shape and (v == p['art']).all()), None)
        if same is None:
            same = p['name'] if p['name'] not in masters else f"{p['name']}-{len(masters)}"
            masters[same] = p['art']
            Image.fromarray(p['art']).save(LOCAL / f'{same}.png')
        p['master'] = same
    reductions = {}
    for group, (prefixes, limit) in REDUCE.items():
        names = [n for n in masters if n.startswith(prefixes)]
        offs = [tuple(next(p['xy'] for p in placed if p['master'] == n)) for n in names]
        arts, merged = reduce_colours([masters[n] for n in names], limit, offs, BANKS_FOR.get(group))
        for n, art in zip(names, arts):
            Image.fromarray(masters[n]).save(LOCAL / f'{n}-hgss.png')
            Image.fromarray(art).save(LOCAL / f'{n}.png')
            masters[n] = art
        hg = np.concatenate([rgba(LOCAL / f'{n}-hgss.png')[..., :4].reshape(-1, 4) for n in names])
        nv = np.concatenate([a.reshape(-1, 4) for a in arts])
        reductions[group] = dict(masters=names, hgss_colours=int(len(np.unique(hg[hg[:, 3] > 0][:, :3] >> 3, axis=0))),
                                 native_colours=int(len(np.unique(nv[nv[:, 3] > 0][:, :3] >> 3, axis=0))), merged=merged)
    for p in placed:
        p['art'] = masters[p['master']]
    (LOCAL / 'reductions.json').write_text(json.dumps(dict(
        note='Local HGSS building masters: <name>-hgss.png is the exact cut-out of the HGSS model render; <name>.png is '
             'the native master. Each group shares one tone set: the closest pair of tones (RGB555, weighted by the '
             'smaller pixel count) merges, the rarer into the commoner, until the limit. Shapes are untouched. The '
             'houses and lookout towers share HGSS red-roof and timber tones and one bank.',
        groups=reductions), indent=1) + '\n')
    return placed

REDUCE = {'red roofs and timber': (('house', 'tower'), 15), 'gym': (('gym',), 30), 'antenna tree': (('antenna_tree',), 15)}
BANKS_FOR = {'gym': 2}       # the Gym may span two banks: reduce only until its placed tiles pack into two

def tile_sets(arts, offs):
    out = []
    for a, (x, y) in zip(arts, offs):
        ox, oy = x % 8, y % 8
        h, w = a.shape[:2]
        c = np.zeros((oy + h + 8, ox + w + 8, 4), np.uint8); c[oy:oy + h, ox:ox + w] = a
        for ty in range(0, c.shape[0] - 7, 8):
            for tx in range(0, c.shape[1] - 7, 8):
                t = c[ty:ty + 8, tx:tx + 8]
                m = t[..., 3] > 0
                if m.any():
                    out.append(frozenset(map(tuple, (t[m][:, :3] >> 3).tolist())))
    return out

def reduce_colours(arts, n, offs=None, banks=None):
    """Merge the closest pair of RGB555 tones, the rarer into the commoner, until n remain
    across all the given masters together (and, with banks, until the masters' tiles as
    placed fit that many exact 15-colour banks)."""
    from pack_lossless import pack_sets
    flat = np.concatenate([a.reshape(-1, 4) for a in arts])
    m = flat[:, 3] > 0
    c5 = flat[:, :3].astype(int) >> 3
    cols, inv, cnt = np.unique(c5[m], axis=0, return_inverse=True, return_counts=True)
    inv = inv.ravel()
    w = cnt.astype(float)
    alive = list(range(len(cols)))
    target = list(range(len(cols)))
    merged = []
    cw = np.array([3.0, 4.0, 2.0])

    def apply(target):
        first8 = {k: flat[m][inv == k][0, :3] for k in range(len(cols))}      # each tone keeps its HGSS 8-bit value
        out = flat.copy()
        out[m, :3] = np.array([first8[target[k]] for k in inv], np.uint8)
        res, o = [], 0
        for a in arts:
            k = a.shape[0] * a.shape[1]
            res.append(out[o:o + k].reshape(a.shape)); o += k
        return res

    def fits(target):
        return banks is None or pack_sets(tile_sets(apply(target), offs), banks, tries=40) is not None
    while len(alive) > n or not fits(target):
        best = None
        for ii, i in enumerate(alive):
            for j in alive[ii + 1:]:
                d = float((((cols[i] - cols[j]) ** 2) * cw).sum()) * np.sqrt(min(w[i], w[j]))
                if (cols[i][2] > cols[i][0]) != (cols[j][2] > cols[j][0]):
                    d *= 20                                   # keep cool tones (window glass) apart from warm ones
                if best is None or d < best[0]:
                    best = (d, i, j)
        _, i, j = best
        keep, drop = (i, j) if w[i] >= w[j] else (j, i)
        w[keep] += w[drop]
        alive.remove(drop)
        target = [keep if t == drop else t for t in target]
        merged.append([[int(v) << 3 for v in cols[drop]], [int(v) << 3 for v in cols[keep]], int(cnt[drop])])
    return apply(target), merged

def flowers(phg):
    """HGSS's flower03 cells: the white flower heads lifted from the decoded ground texture."""
    h, mat, names, rgb = E.topdown(phg)
    fi = names.index('flower03')
    cells = sorted({(x // PX, y // PX) for y, x in zip(*np.nonzero(mat == fi))})
    m = (mat == fi) & (rgb.min(-1) >= 200)
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    art[m, :3] = rgb[m]; art[m, 3] = 255
    return art, cells

# --------------------------------------------------------------------------- compose
def over(dst, src, x, y, owner=None, name=''):
    h, w = src.shape[:2]
    sy0, sx0 = max(0, -y), max(0, -x)
    sy1, sx1 = min(h, dst.shape[0] - y), min(w, dst.shape[1] - x)
    s = src[sy0:sy1, sx0:sx1]
    a = s[..., 3] > 0
    d = dst[y + sy0:y + sy1, x + sx0:x + sx1]
    d[a] = s[a]
    if owner is not None:
        owner[y + sy0:y + sy1, x + sx0:x + sx1][a] = name

def read_grid():
    lines = [l for l in (TRACE / 'material-grid.txt').read_text().splitlines() if l[:2].isdigit()]
    return [list(l.split()[1]) for l in lines]

GATE_XY = (160, -32)          # G01a at cell (10,-2): door column (x+3, y+7) on HGSS warp (13,5), body on HGSS x10..16
CENTER_ORIGIN = (20, 19)      # C06 door (2,4) on HGSS's Center door (22,23)
SIGN_XY = {(4, 12): ('P12.png', 64, 176), (14, 14): ('P13.png', 216, 200), (8, 24): ('P15.png', 120, 360)}   # bases on HGSS's sign bases

def compose(phg):
    global PHG
    PHG = phg
    grid = read_grid()
    cells = E.ledger(phg)
    trees = json.loads((TRACE / 'trees.json').read_text())['trees']
    lab = np.array([[c['lab'] for c in row] for row in cells])
    ground, _ = paint_ground(ground_quadrants(cells, np.isin(lab, list(E.ROCK))))
    bottom, rock, d, isrock, piece = frlg_rock(cells, ground[..., :3].copy())
    owner = np.full((H * PX, W * PX), '', object)
    (OUT / 'terrace-grid.txt').write_text(
        '# Mahogany rock terraces (assemble.terraces), one line per cell row: level 0-2, rock cells upper-case R/M\n'
        '# (R a low wall, M the mountain), from HGSS land_data 85 decoded flat (elements.ledger).\n' +
        ''.join(f'{y:02d}    ' + ''.join(('RM'[min(d[y, x], 2) - 1] if isrock[y, x] else str(d[y, x])) for x in range(W)) + '\n'
                for y in range(H)))
    # Flowers, then ledges, on the ground layer.
    fl, fcells = flowers(phg)
    a = fl[..., 3] > 0
    bottom[a] = fl[a, :3]; owner[a] = 'flowers'
    l11, l12, l13 = (rgba(SHARED / f'{n}.png') for n in ('L11', 'L12', 'L13'))
    q = west_ledge(); j = ledge_corner(q, l12)
    single = np.concatenate([l11[:, :8], l13[:, 8:]], axis=1)
    ledges = []
    for y in range(H):
        for x in range(W):
            c = grid[y][x]
            if c == 'L':
                left = x > 0 and grid[y][x - 1] in 'LJ'
                right = x + 1 < W and grid[y][x + 1] == 'L'
                art, kind = (l12, 'L12') if left and right else (l11, 'L11') if right else (l13, 'L13') if left else (single, 'L11+L13')
            elif c == 'Q':
                art, kind = q, 'west ledge (0x85)'
            elif c == 'J':
                art, kind = j, 'ledge corner'
            else:
                continue
            sl = np.s_[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX]
            m = art[..., 3] > 0
            bottom[sl][m] = art[m, :3]; owner[sl][m] = 'ledge'
            ledges.append(dict(cell=[x, y], art=kind))
    # Objects, painted north to south by their base row so the nearer one covers.
    top = np.zeros((H * PX, W * PX, 4), np.uint8)
    objs = []
    t01 = rgba(SHARED / 'T01.png')
    for i, (tx, ty) in enumerate(trees):
        objs.append(dict(name=f'tree_{i}', master='shared-art/T01.png', xy=[tx * PX, ty * PX - PX], art=t01, root=[tx, ty]))
    for p in local_buildings(phg):
        objs.append(dict(name=f"{p['name']}_{len(objs)}", master=f"local-art/{p['master']}.png", xy=p['xy'], art=p['art'],
                         model=p['model'], pos=p['pos'], hgss_xy=p['hgss_xy']))
    objs.append(dict(name='gate', master='shared-art/G01a.png', xy=list(GATE_XY), art=rgba(SHARED / 'G01a.png')))
    objs.append(dict(name='pokemon_center', master='shared-art/pokemon-center.png',
                     xy=[CENTER_ORIGIN[0] * PX, CENTER_ORIGIN[1] * PX], art=rgba(SHARED / 'pokemon-center.png')))
    for (sx, sy), (f, x, y) in SIGN_XY.items():
        objs.append(dict(name=f'sign_{sx}_{sy}', master=f'shared-art/{f}', xy=[x, y], art=rgba(SHARED / f), cell=[sx, sy]))
    for o in objs:
        a = o['art'][..., 3] > 0
        o['base'] = o['xy'][1] + int(np.nonzero(a.any(1))[0].max())
    objs.sort(key=lambda o: (o['base'], o['xy'][0]))
    for o in objs:
        over(top, o['art'], o['xy'][0], o['xy'][1], owner, o['name'])
    return bottom, rock, top, owner, d, objs, ledges, fcells

ENGINE = None
PHG = None

def main(phg, catalog, engine):
    global ENGINE
    ENGINE = engine
    for d in (OUT, OEV, LOCAL, SHARED):
        d.mkdir(parents=True, exist_ok=True)
    stage_shared(catalog)
    ground, rock, top, owner, levels, objs, ledges, fcells = compose(phg)
    view = ground.copy()
    for layer in (rock, top):
        a = layer[..., 3] > 0
        view[a] = layer[a, :3]
    Image.fromarray(view).save(OEV / 'composed.png')
    Image.fromarray(ground).save(OEV / 'ground.png')
    Image.fromarray(rock).save(OEV / 'rock.png')
    Image.fromarray(top).save(OEV / 'objects.png')
    np.savez_compressed(OUT / 'layers.npz', ground=ground, rock=rock, objects=top, owner=owner.astype(str), levels=levels)
    (OUT / 'placements.json').write_text(json.dumps(dict(
        note='Every placed object: master file, top-left pixel, base row. Trees sit on their decoded HGSS 2x2 roots '
             '(T01 bottom on the root bottom, crown one row behind); local buildings keep their HGSS render position.',
        objects=[{k: v for k, v in o.items() if k != 'art'} for o in objs], ledges=ledges, flower_cells=fcells), indent=1, default=int) + '\n')
    print('objects', len(objs), 'ledges', len(ledges), 'flower cells', fcells)

if __name__ == '__main__':
    main(*(Path(a).resolve() for a in sys.argv[1:4]))
