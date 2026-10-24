"""Route 43: native art assembled under docs/GBA_MAP_RECONSTRUCTION.md, by the process the
owner accepted for Mahogany Town (tools/gba/maps/mahogany/assemble.py).

    python3 tools/gba/maps/route43/assemble.py PHG_CHECKOUT CATALOG_CHECKOUT ENGINE_CHECKOUT

1. Reference: trace.py registers decoded HGSS land_data chunks 87 (north) and 88 (south) to
   native cells 1:1 (numbered sheets, material grid, traversal ledger); elements.ledger
   decodes them flat, cell by cell.
2. Rock, as Blackthorn's and Mahogany's installed rock: every HGSS height layer is one terrace
   (floor 0; the south-west massif's three steps 1-3; the east ridge 1-2;
   source/assemble/terrace-grid.txt), drawn with FRLG General's mountain nine-slice,
   over-rock pieces and inner corners in the Johto rock ramp, one face per metatile, as a
   top-layer overlay on plain ground (elements.rock_frlg).
3. Shared art, copied unchanged with hashes into source/shared-art/ from the Johto catalog
   (CATALOG_CHECKOUT is a checkout of branch codex/violet-city):
     ground      the accepted Cherrygrove/Route 36 painter (claude_cherrygrove/ground.py), run on
                 an 8 px lawn/road grid read from HGSS's own flat ground colours
     ponds       Route 30's installed HGSS freshwater pieces (route30-hgss-blocks pond-<mask>-
                 <phase>) on HGSS's water cells, by which neighbours are water too
     tall grass  G00-G15 on HGSS's tall-grass cells, chosen by which of the four neighbours
                 (north, south, west, east) are tall grass too; one-cell strips take full pieces
     ledges      L11/L12/L13 (warm Johto ledge ends and run)
     trees       T01 on non-overlapping 2x2 roots on HGSS's woods cells (elements.tree_footprints)
     signs       P14 green route sign (HGSS model 32), P16 blue information board (model 34)
     gatehouse   G01a front gatehouse: the Route 43 toll gate on HGSS's gate, and the top two
                 rows of Mahogany's north gatehouse (Mahogany places the same G01a at its
                 cell (10,-2), which is this map's (10,62))
4. Local asset: the flower patches, lifted from HGSS's own flower01-03 ground textures (every
   pixel of the texture that is not lawn green), as Mahogany's white flowers were.

Writes source/assemble/layers.npz (ground RGB with ledges, flowers and tall grass, rock RGBA,
objects RGBA, object owner, terrace levels), placements.json, terrace-grid.txt,
evidence/assemble/*.png.
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
ART = ROOT / 'gba/art/route-43'
SRC, EV = ART / 'source', ART / 'evidence'
TRACE, SHARED, LOCAL = SRC / 'trace', SRC / 'shared-art', SRC / 'local-art'
OUT, OEV = SRC / 'assemble', EV / 'assemble'
W, H = 32, 64
PX = 16

CATALOG = {  # local name -> catalog path (branch codex/violet-city)
    'T01.png': 'gba/art/johto-common/trees/source/T01.png',
    'P14.png': 'gba/art/johto-common/scenery/source/P14.png',
    'P16.png': 'gba/art/johto-common/scenery/source/P16.png',
    'L11.png': 'gba/art/johto-common/scenery/source/L11.png',
    'L12.png': 'gba/art/johto-common/scenery/source/L12.png',
    'L13.png': 'gba/art/johto-common/scenery/source/L13.png',
    'G01a.png': 'gba/art/johto-common-review/gates/refinement-4/G01a.png',
    **{f'G{i:02}.png': f'gba/art/johto-common/scenery/source/G{i:02}.png' for i in range(16)},
    # Route 30's installed HGSS freshwater (tools/gba/maps/route30_hgss_blocks/assets.py):
    # pond-<bits>-<phase>, bits 1 north, 2 south, 4 west, 8 east where water continues,
    # phase (y % 2) * 2 + x % 2 of its 32 px water texture.
    **{f'pond/pond-{b}-{f}.png': f'gba/art/route30-hgss-blocks/source/materials/pond-{b}-{f}.png' for b in range(16) for f in range(4)},
}
WAVE = True              # the approved painter's 32 px rim wave
PATH_CORE = 32           # the approved painter's full 32 px road texture
FLOOR = 4                # HGSS height of the route floor; the massif's steps stand at 5-7, the east ridge at 5-6

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p): return np.array(Image.open(p).convert('RGBA'))

def stage_shared(catalog):
    """Copy every catalog master used here, unchanged, with its hash and the catalog commit."""
    commit = subprocess.run(['git', '-C', str(catalog), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    prov = dict(catalog=dict(branch='codex/violet-city', commit=commit,
                             rule='Masters copied byte for byte; native tile ids and palette slots may differ, visible colours do not.'))
    for name, rel in CATALOG.items():
        dst = SHARED / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(catalog / rel, dst)
        prov[name] = dict(source=rel, sha256=sha(dst))
    (SHARED / 'provenance.json').write_text(json.dumps(prov, indent=2) + '\n')

# --------------------------------------------------------------------------- rock
def terraces(cells):
    """Blackthorn's rock structure: every HGSS height layer is one Gen 3 terrace. A rock cell
    (ledger label T, E, S, W or N: HGSS's cliff cells, decoded flat) stands at its rock peak
    above the floor; every other cell at its ground height (floor 0; under a tree crown, the
    cell's lowest point; the ponds sit below the floor and count as 0)."""
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
    """Blackthorn's installed rock (elements.rock_frlg): FRLG General's mountain nine-slice, its
    over-rock version where an edge drops to a lower terrace, and its four inner corners,
    recoloured to the Johto rock ramp, one face per metatile. The rock is a top-layer overlay;
    under its clear pixels the bottom carries the plainest 8x8 block of the ground beyond the
    edge, and its cast shadow is Cherrygrove's border grey. Ledges keep their own art."""
    d, face, isrock = terraces(cells)
    E.layers = lambda _cells: (d, face, isrock)
    plain_cells = [[dict(c, lab='.' if c['lab'] in E.LEDGES else c['lab']) for c in row] for row in cells]
    out, over, _, piece = E.rock_frlg(plain_cells, ground, E.frlg_pieces(ENGINE), E.cherry_textures())
    return out, over, d, isrock, piece

# --------------------------------------------------------------------------- ground
def paint_ground(q):
    """The accepted Cherrygrove/Route 36 painter (claude_cherrygrove/ground.paint) on an 8 px
    material grid: its own textures, rim profiles, 32 px wobble wave and order, with each
    material square 8 px instead of 16 so lawn edges can sit mid-cell where HGSS puts them."""
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
    against road sand); quadrants HGSS shows too little open ground in keep their cell's
    material. HGSS's water cells (type 0x10, ledger '~') are lawn here; the pond pieces go
    over them (pond()). Ledge stones are read past: a south ledge cell's lower
    quadrants take the ground above them."""
    _, _, _, rgb = E.topdown(PHG)
    rgb = rgb.astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    rockpx = np.repeat(np.repeat(rock, PX, 0), PX, 1)
    water = (b > g + 30) & (b > 150)
    lawn = (g > r + 20) & ~rockpx & ~water
    sand = (r >= g) & (r > 180) & (b < 175) & ~rockpx
    q = np.repeat(np.repeat(np.array([[G.PATH if c['floor'] == 'sand' else G.GRASS for c in row] for row in cells]), 2, 0), 2, 1).astype(np.int8)
    for qy in range(H * 2):
        for qx in range(W * 2):
            lab = cells[qy // 2][qx // 2]['lab']
            if lab in 'FG~':
                q[qy, qx] = G.GRASS                       # HGSS's woods, tall grass and pond banks stand on lawn
                continue
            sl = np.s_[qy * 8:qy * 8 + 8, qx * 8:qx * 8 + 8]
            nl, ns = int(lawn[sl].sum()), int(sand[sl].sum())
            if ns >= 32 and ns > nl:
                q[qy, qx] = G.PATH
            elif nl >= 8:
                q[qy, qx] = G.GRASS
    for y in range(H):
        for x in range(W):
            if cells[y][x]['lab'] in 'LJ':
                q[2 * y + 1, 2 * x:2 * x + 2] = q[2 * y, 2 * x:2 * x + 2]
    return q

def tall_grass(cells):
    """Catalog tall grass on every HGSS tall-grass cell: G<mask>, mask bits north, south, west,
    east (1 where that neighbour is tall grass too; off the map counts as not). A strip one
    cell wide would take a piece trimmed on both sides, half a cell across; it takes the
    full-width piece instead (both side bits set), and a strip one cell tall the full-height
    piece, so every tall-grass cell is a whole cell of grass."""
    grass = np.array([[c['lab'] == 'G' for c in row] for row in cells])
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    used = {}
    for y, x in zip(*np.nonzero(grass)):
        n = y > 0 and grass[y - 1, x]
        s = y + 1 < H and grass[y + 1, x]
        w = x > 0 and grass[y, x - 1]
        e = x + 1 < W and grass[y, x + 1]
        if not (w or e):
            w = e = True
        if not (n or s):
            n = s = True
        k = int(n) * 8 + int(s) * 4 + int(w) * 2 + int(e)
        art[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX] = rgba(SHARED / f'G{k:02}.png')
        used[f'G{k:02}'] = used.get(f'G{k:02}', 0) + 1
    return art, used

def pond(cells):
    """Route 30's HGSS freshwater on every HGSS water cell: pond-<bits>-<phase>, bits 1 north,
    2 south, 4 west, 8 east where the water continues (off the map counts as not), phase from
    the cell's position on the water texture's 32 px repeat. The bank and rim are inside the
    water cells, so the Surf boundary is the cell edge."""
    water = np.array([[c['lab'] == '~' for c in row] for row in cells])
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    used = {}
    for y, x in zip(*np.nonzero(water)):
        bits = sum(f for f, (dy, dx) in zip((1, 2, 4, 8), ((-1, 0), (1, 0), (0, -1), (0, 1)))
                   if 0 <= y + dy < H and 0 <= x + dx < W and water[y + dy, x + dx])
        name = f'pond-{bits}-{(y % 2) * 2 + x % 2}'
        art[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX] = rgba(SHARED / f'pond/{name}.png')
        used[name] = used.get(name, 0) + 1
    return art, used

def flowers(phg):
    """HGSS's flower cells (flower01-03): the flower heads lifted from the decoded ground
    texture, every pixel that is not one of the texture's lawn greens (green over red by 40)."""
    h, mat, names, rgb = E.topdown(phg)
    fm = np.isin(mat, [names.index(n) for n in ('flower01', 'flower02', 'flower03') if n in names])
    cells = sorted({(int(x) // PX, int(y) // PX) for y, x in zip(*np.nonzero(fm))})
    c = rgb.astype(int)
    m = fm & ~(c[..., 1] - c[..., 0] >= 40)
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    art[m, :3] = rgb[m]; art[m, 3] = 255
    LOCAL.mkdir(parents=True, exist_ok=True)
    Image.fromarray(art).save(LOCAL / 'flowers.png')
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

# G01a's doorway is its cells (2,7) and (3,7). The toll gate's doors stand on HGSS's gate warps
# (25,47),(26,47); Mahogany's north gatehouse stands at Mahogany (10,-2), this map's (10,62).
GATES = {'gate': (23 * PX, 40 * PX), 'gate_mahogany': (10 * PX, 62 * PX)}
# Sign art: centred on the HGSS model's x, its base on the HGSS model's base row, on 8 px tiles.
SIGN_XY = {(20, 3): ('P14.png', 312, 32), (20, 50): ('P16.png', 312, 784), (15, 58): ('P14.png', 232, 912)}

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
        '# Route 43 rock terraces (assemble.terraces), one line per cell row: level 0-3, rock cells upper-case A/B/C\n'
        '# (the first, second and third terrace), from HGSS land_data 87-88 decoded flat (elements.ledger).\n' +
        ''.join(f'{y:02d}    ' + ''.join(('ABC'[min(d[y, x], 3) - 1] if isrock[y, x] else str(d[y, x])) for x in range(W)) + '\n'
                for y in range(H)))
    # Ponds, flowers, tall grass, then ledges, on the ground layer.
    pd, pd_used = pond(cells)
    a = pd[..., 3] > 0
    bottom[a] = pd[a, :3]; owner[a] = 'pond'
    fl, fcells = flowers(phg)
    a = fl[..., 3] > 0
    bottom[a] = fl[a, :3]; owner[a] = 'flowers'
    tg, tg_used = tall_grass(cells)
    a = tg[..., 3] > 0
    bottom[a] = tg[a, :3]; owner[a] = 'tall_grass'
    l11, l12, l13 = (rgba(SHARED / f'{n}.png') for n in ('L11', 'L12', 'L13'))
    single = np.concatenate([l11[:, :8], l13[:, 8:]], axis=1)
    ledges = []
    for y in range(H):
        for x in range(W):
            if grid[y][x] != 'L':
                continue
            left = x > 0 and grid[y][x - 1] == 'L'
            right = x + 1 < W and grid[y][x + 1] == 'L'
            art, kind = (l12, 'L12') if left and right else (l11, 'L11') if right else (l13, 'L13') if left else (single, 'L11+L13')
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
    for name, xy in GATES.items():
        objs.append(dict(name=name, master='shared-art/G01a.png', xy=list(xy), art=rgba(SHARED / 'G01a.png')))
    for (sx, sy), (f, x, y) in SIGN_XY.items():
        objs.append(dict(name=f'sign_{sx}_{sy}', master=f'shared-art/{f}', xy=[x, y], art=rgba(SHARED / f), cell=[sx, sy]))
    for o in objs:
        a = o['art'][..., 3] > 0
        o['base'] = o['xy'][1] + int(np.nonzero(a.any(1))[0].max())
    objs.sort(key=lambda o: (o['base'], o['xy'][0]))
    for o in objs:
        over(top, o['art'], o['xy'][0], o['xy'][1], owner, o['name'])
    return bottom, rock, top, owner, d, objs, ledges, fcells, tg_used, pd_used

ENGINE = None
PHG = None

def main(phg, catalog, engine):
    global ENGINE
    ENGINE = engine
    for d in (OUT, OEV, LOCAL, SHARED):
        d.mkdir(parents=True, exist_ok=True)
    stage_shared(catalog)
    ground, rock, top, owner, levels, objs, ledges, fcells, tg_used, pd_used = compose(phg)
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
             '(T01 bottom on the root bottom, crown one row behind); the gatehouses and signs stand on HGSS\'s own.',
        objects=[{k: v for k, v in o.items() if k != 'art'} for o in objs], ledges=ledges, flower_cells=fcells,
        tall_grass_pieces=tg_used, pond_pieces=pd_used), indent=1, default=int) + '\n')
    print('objects', len(objs), 'ledges', len(ledges), 'flower cells', len(fcells), 'tall grass', tg_used, 'pond', len(pd_used))

if __name__ == '__main__':
    main(*(Path(a).resolve() for a in sys.argv[1:4]))
