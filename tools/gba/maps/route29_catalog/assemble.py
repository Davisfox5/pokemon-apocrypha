"""Route 29: native art assembled by the process the owner accepted for Mahogany Town and Route 43.

    python3 tools/gba/maps/route29_catalog/assemble.py PHG_CHECKOUT CATALOG_CHECKOUT ENGINE_CHECKOUT

CATALOG_CHECKOUT is a checkout of the Johto catalog commit (pokemon-apocrypha codex/violet-city
de5d8cfb). Every piece is shared art copied byte for byte into source/shared-art/ with its hash:

  ground      the approved Cherrygrove/Route 36 painter (claude_cherrygrove/ground.py) on an 8 px
              lawn/road grid read from HGSS's own flat ground colours; the road is Cherrygrove's own
              road texture so the road continues into the town unchanged
  trees       the Cherrygrove tree (T01, identical pixel for pixel, with the town's contact shadow)
              on non-overlapping 2x2 roots over HGSS's woods (reference.py), crown one row behind,
              painted north to south so each crown covers the trunk of the tree behind it
  tall grass  G15, the whole-cell piece, on every HGSS tall-grass cell
  ledges      L11/L12/L13 on HGSS's jump-south runs; the same pieces turned a quarter for the
              jump-east and jump-west runs; corners join both
  gatehouse   G01a on HGSS's Route 46 gatehouse (model 35), doorway on HGSS's gate warps
  signs       P14 (HGSS model 32) on both HGSS route signs
Local assets lifted from HGSS's own ground textures: flower heads (flower01-03, every pixel that is
not lawn green) and the light lawn patches (grass02 family), as Mahogany's flowers were.

The 8-column seam windows (columns 0-7 and 94-101) are drawn by the neighbouring town with its own
tilesets, so their ground follows the town's road rows and their art must resolve to primary
metatiles (checked in pack.py). The map is HGSS Route 29 only.

Writes source/assemble/layers.npz, placements.json and evidence/assemble/*.png.
"""
from __future__ import annotations
import hashlib, json, shutil, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import reference as Rf                               # noqa: E402
from reference import W, H, PX, COL0, ROW0, HW, HH, WINDOW   # noqa: E402
from claude_cherrygrove import ground as G           # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route29-catalog'
SRC, EV = ART / 'source', ART / 'evidence'
TRACE, SHARED, LOCAL = SRC / 'trace', SRC / 'shared-art', SRC / 'local-art'
OUT, OEV = SRC / 'assemble', EV / 'assemble'

CATALOG = {
    'P14.png': 'gba/art/johto-common/scenery/source/P14.png',
    'L11.png': 'gba/art/johto-common/scenery/source/L11.png',
    'L12.png': 'gba/art/johto-common/scenery/source/L12.png',
    'L13.png': 'gba/art/johto-common/scenery/source/L13.png',
    'G01a.png': 'gba/art/johto-common-review/gates/refinement-4/G01a.png',
    'G15.png': 'gba/art/johto-common/scenery/source/G15.png',
    'T01.png': 'gba/art/johto-common/trees/source/T01.png',
}
TREE_BOX = (896, 80, 928, 128)      # Cherrygrove's standalone tree (cells 56-57, 5-7), as Mahogany's elements.cherry_tree
ROAD_ROWS = (17, 18, 19)            # Cherrygrove's and New Bark's road rows at the seam (both towns, this map's rows)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p): return np.array(Image.open(p).convert('RGBA'))

def stage_shared(catalog):
    commit = subprocess.run(['git', '-C', str(catalog), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    prov = dict(catalog=dict(repository='pokemon-apocrypha', branch='codex/violet-city', commit=commit,
                             rule='Masters copied byte for byte; native tile ids and palette slots may differ, visible colours do not.'))
    for name, rel in CATALOG.items():
        dst = SHARED / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(catalog / rel, dst)
        prov[name] = dict(source=rel, sha256=sha(dst))
    (SHARED / 'provenance.json').write_text(json.dumps(prov, indent=2) + '\n')

# --------------------------------------------------------------------------- town art
def cherrygrove_native(engine):
    sys.path.insert(0, str(HERE.parent))
    from tiles import Tileset
    import struct
    t = Tileset(engine, 'cherrygrove', 'cherrygrove')
    b = (engine / 'data/layouts/CherrygroveCity/map.bin').read_bytes()
    return np.array(t.map_image(list(struct.unpack('<%dH' % (len(b) // 2), b)), 80))

def cherry_tree(engine, lawn_tex):
    """Cherrygrove's standalone tree with its contact shadow: the town's pixels that differ from its lawn."""
    img = cherrygrove_native(engine)
    x0, y0, x1, y1 = TREE_BOX
    ys, xs = np.mgrid[y0:y1, x0:x1]
    px = img[y0:y1, x0:x1]
    a = (px != lawn_tex[ys % 32, xs % 32]).any(-1)
    out = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
    out[a, :3] = px[a]; out[a, 3] = 255
    t01 = rgba(SHARED / 'T01.png'); m = t01[..., 3] > 0
    assert (out[m, :3] == t01[m, :3]).all() and a[m].all(), 'Cherrygrove tree is no longer T01 plus its shadow'
    LOCAL.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out).save(LOCAL / 'cherrygrove-tree-with-shadow.png')
    return out

def road_texture(engine):
    """Cherrygrove's own 32 px road block (the commonest pure-road block of the town)."""
    img = cherrygrove_native(engine)
    core = np.array([(216, 184, 128), (224, 200, 128)])            # the road's two body colours (no rim shade)
    sand = (img[..., None, :] == core).all(-1).any(-1)
    from collections import Counter
    blocks = Counter()
    for y in range(0, img.shape[0] - 31, 32):
        for x in range(0, img.shape[1] - 31, 32):
            if sand[y:y + 32, x:x + 32].all():          # 32-aligned, so the block keeps the town's texture phase
                blocks[img[y:y + 32, x:x + 32].tobytes()] += 1
    return np.frombuffer(blocks.most_common(1)[0][0], np.uint8).reshape(32, 32, 3)

# --------------------------------------------------------------------------- ground
def paint_ground(q, road):
    """The approved painter (Mahogany/Route 43 assemble.paint_ground) on an 8 px material grid."""
    U = 8
    hq, wq = q.shape
    h, w = hq * U, wq * U
    tex = G.textures()
    tex[G.PATH] = road
    ys, xs = np.mgrid[0:h, 0:w]
    wave = np.array(G.WAVE)
    dx = wave[ys % 32]; dy = wave[(xs + 11) % 32]
    sx = np.clip(xs + dx, 0, w - 1) // U; sy = np.clip(ys + dy, 0, h - 1) // U
    mat = q[sy, sx]
    out = np.zeros((h, w, 3), np.uint8)
    for m, t in tex.items():
        mm = mat == m
        out[mm] = t[ys[mm] % t.shape[0], xs[mm] % t.shape[1]]
    dist = {m: G._chamfer(mat == m) for m in tex}
    for (a, b) in [(G.GRASS, G.PATH)]:
        pa, pb = G.PROFILES[(a, b)]
        for k, c in enumerate(pa):
            out[(mat == a) & (dist[b] == k + 1)] = c
        for k, c in enumerate(pb):
            out[(mat == b) & (dist[a] == k + 1)] = c
    return out, mat

def ground_quadrants(phg, grid):
    """Lawn or road per 8 px quadrant from HGSS's own flat ground colours (Route 43's rule). The four
    padding columns repeat HGSS column 0; the seam windows carry the towns' road rows."""
    _, _, _, rgb = Rf.topdown(phg)
    rgb = rgb.astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    lawn = g > r + 20
    sand = (r >= g) & (r > 180) & (b < 175)
    q = np.zeros((H * 2, W * 2), np.int8)
    q[:] = G.GRASS
    for qy in range(ROW0 * 2, H * 2):
        for qx in range(W * 2):
            x, y = qx // 2, qy // 2
            hx, hz = Rf.to_hgss(x, y)
            hqx = (qx % 2) if hx < 0 else (HW - 1) * 2 + (qx % 2) if hx >= HW else qx - COL0 * 2
            hqy = qy - ROW0 * 2
            ch = grid[y][x]
            if ch in 'tkoGBD':
                continue
            sl = np.s_[hqy * 8:hqy * 8 + 8, hqx * 8:hqx * 8 + 8]
            nl, ns = int(lawn[sl].sum()), int(sand[sl].sum())
            if ns >= 32 and ns > nl:
                q[qy, qx] = G.PATH
    # Ledge stones are read past: a ledge cell's quadrants take the ground on its high side.
    for y in range(H):
        for x in range(W):
            ch = grid[y][x]
            if ch == 'L' or ch in 'XJ':
                q[2 * y + 1, 2 * x:2 * x + 2] = q[2 * y, 2 * x:2 * x + 2]
            elif ch == 'E':
                q[2 * y:2 * y + 2, 2 * x + 1] = q[2 * y:2 * y + 2, 2 * x]
            elif ch == 'Q':
                q[2 * y:2 * y + 2, 2 * x] = q[2 * y:2 * y + 2, 2 * x + 1]
    # Seam windows: the road runs on the towns' road rows; everything else there is lawn.
    for x in list(range(WINDOW)) + list(range(W - WINDOW, W)):
        q[:, 2 * x:2 * x + 2] = G.GRASS
        for y in ROAD_ROWS:
            q[2 * y:2 * y + 2, 2 * x:2 * x + 2] = G.PATH
    return q

def seam_windows(engine, bottom, flat):
    """The seam windows carry the towns' own road: Cherrygrove's road kit on the west side and New Bark's on
    the east side, on both towns' road rows, plain lawn elsewhere; flat details are left out (a town draws
    these cells with its own tilesets, which hold no tall grass or HGSS flowers)."""
    from tiles import Tileset
    cg = Tileset(engine, 'cherrygrove', 'cherrygrove'); nb = Tileset(engine, 'new_bark', 'cherrygrove')
    kit = {'west': (cg, {17: (0x0B4, 0x0B3), 18: (0x004, 0x0C3), 19: (0x0DB, 0x0DA)}),
           'east': (nb, {17: (0x206, 0x207), 18: (0x154, 0x153), 19: (0x0DB, 0x0DA)})}
    lawn = G.textures()[G.GRASS]
    ys, xs = np.mgrid[0:PX, 0:PX]
    for side, cols in (('west', range(WINDOW)), ('east', range(W - WINDOW, W))):
        ts, rows = kit[side]
        for x in cols:
            for y in range(H):
                sl = np.s_[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX]
                flat[sl] = 0
                if y in rows:
                    bottom[sl] = np.array(ts.render(rows[y][x % 2]).convert('RGB'))
                else:
                    bottom[sl] = lawn[(ys + y * PX) % 32, (xs + x * PX) % 32]

def lift(phg, names, keep):
    """HGSS ground-texture pixels of the named materials, in the native frame."""
    h, mat, nm, rgb = Rf.topdown(phg)
    ids = [nm.index(n) for n in names if n in nm]
    fm = np.isin(mat, ids)
    c = rgb.astype(int)
    m = fm & keep(c)
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    sl = np.s_[ROW0 * PX:ROW0 * PX + HH * PX, COL0 * PX:COL0 * PX + HW * PX]   # padding columns hold no details
    a = art[sl]
    a[m, :3] = rgb[m]; a[m, 3] = 255
    return art

def hgss_lawn_colours(phg):
    """The colours of HGSS's own plain lawn (grass01gs), which the Cherrygrove lawn replaces."""
    h, mat, nm, rgb = Rf.topdown(phg)
    px = rgb[mat == nm.index('grass01gs')]
    return {tuple(int(v) for v in c) for c in np.unique(px, axis=0)}

def flowers(phg):
    """HGSS's flower cells: every texture pixel that is not one of HGSS's plain lawn colours, so the
    heads keep their leaves (Route 43 dropped every green; here only the lawn the Cherrygrove lawn replaces)."""
    plain = np.array(sorted(hgss_lawn_colours(phg)))
    art = lift(phg, Rf.FLOWERS, lambda c: ~(c[..., None, :] == plain[None, None]).all(-1).any(-1))
    Image.fromarray(art).save(LOCAL / 'flowers.png')
    return art

def light_lawn(phg):
    """HGSS's light lawn patches (grass02, its rim grass02_r and corner grass02_a): every pixel that is
    not one of HGSS's plain lawn colours, so the patch sits on the Cherrygrove lawn with no frame."""
    plain = np.array(sorted(hgss_lawn_colours(phg)))
    art = lift(phg, Rf.LIGHT, lambda c: ~(c[..., None, :] == plain[None, None]).all(-1).any(-1))
    Image.fromarray(art).save(LOCAL / 'light-lawn.png')
    return art

# --------------------------------------------------------------------------- ledges
def ledge_pieces():
    l11, l12, l13 = (rgba(SHARED / f'{n}.png') for n in ('L11', 'L12', 'L13'))
    south = dict(left=l11, mid=l12, right=l13, single=np.concatenate([l11[:, :8], l13[:, 8:]], 1))
    # A south ledge faces down the screen. Turned a quarter anticlockwise it faces east (its high side
    # west); clockwise it faces west. A run's north end is the piece's right end turned (east) or its
    # left end turned (west).
    ccw = lambda a: np.rot90(a, 1).copy()
    cw = lambda a: np.rot90(a, -1).copy()
    east = dict(top=ccw(l13), mid=ccw(l12), bottom=ccw(l11))
    west = dict(top=cw(l11), mid=cw(l12), bottom=cw(l13))
    return south, east, west

def ledges(grid):
    south, east, west = ledge_pieces()
    g = lambda x, y: grid[y][x] if 0 <= x < W and 0 <= y < H else '#'
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    placed = []
    def put(x, y, piece, name):
        sl = np.s_[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX]
        m = piece[..., 3] > 0
        art[sl][m] = piece[m]
        placed.append(dict(cell=[x, y], art=name))
    for y in range(H):
        for x in range(W):
            ch = g(x, y)
            if ch == 'L':
                left, right = g(x - 1, y) in 'LXJ', g(x + 1, y) in 'LXJ'
                k = 'mid' if left and right else 'left' if right else 'right' if left else 'single'
                put(x, y, south[k], f'L-{k}')
            elif ch in 'EQ':
                d = east if ch == 'E' else west
                up, down = g(x, y - 1) == ch, g(x, y + 1) in (ch + 'XJ')
                k = 'mid' if up and down else 'top' if down else 'bottom' if up else 'mid'
                put(x, y, d[k], f'{ch}-{k}')
            elif ch in 'XJ' and any(g(x + dx, y) == 'L' for dx in (-1, 1)):
                # Corner: the side run comes down into the south run. Draw the south run's end joined
                # under the side piece's middle, so the two lips meet.
                side = 'E' if g(x, y - 1) == 'E' else 'Q' if g(x, y - 1) == 'Q' else None
                run_west, run_east = g(x - 1, y) == 'L', g(x + 1, y) == 'L'
                k = 'mid' if run_west and run_east else 'right' if run_west else 'left'
                base = south[k].copy()
                if side:
                    vert = (east if side == 'E' else west)['mid']
                    lip = int(np.nonzero((base[..., 3] > 0).any(1))[0].min())
                    top = vert.copy(); top[lip:] = 0
                    m = top[..., 3] > 0
                    base[m] = top[m]
                put(x, y, base, f'corner-{side or "none"}-{k}')
    return art, placed

# --------------------------------------------------------------------------- objects
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

def compose(phg, engine):
    grid = read_grid()
    events = json.loads((SRC / 'hgss-events.json').read_text())
    roots = [tuple(r) for r in json.loads((TRACE / 'trees.json').read_text())['roots']]
    tex = G.textures()
    road = road_texture(engine)
    q = ground_quadrants(phg, grid)
    bottom, mat = paint_ground(q, road)
    # Flat ground details (light lawn, flowers, tall grass, ledges) form their own layer: the packer puts
    # them over the plain lawn on the upper tile layer, or into the ground under a cell drawn above the player.
    owner = np.full((H * PX, W * PX), '', object)
    flat = np.zeros((H * PX, W * PX, 4), np.uint8)
    flat_owner = np.full((H * PX, W * PX), '', object)
    def lay(art, name):
        a = art[..., 3] > 0
        flat[a] = art[a]; flat_owner[a] = name
    lay(light_lawn(phg), 'light_lawn')
    lay(flowers(phg), 'flowers')
    g15 = rgba(SHARED / 'G15.png')
    tg = np.zeros_like(flat)
    n_g15 = 0
    for y in range(H):
        for x in range(W):
            if grid[y][x] == 'G':
                tg[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX] = g15; n_g15 += 1
    lay(tg, 'tall_grass')
    la, ledge_list = ledges(grid)
    lay(la, 'ledge')
    seam_windows(engine, bottom, flat)
    # Objects: painted north to south by base row, so the nearer one covers.
    top = np.zeros((H * PX, W * PX, 4), np.uint8)
    tree = cherry_tree(engine, tex[G.GRASS])
    objs = [dict(name=f'tree_{i}', master='local-art/cherrygrove-tree-with-shadow.png (T01 + shadow)', xy=[x * PX, (y - 1) * PX], art=tree, root=[x, y])
            for i, (x, y) in enumerate(roots)]
    gx, gy = Rf.GATE_ORIGIN
    objs.append(dict(name='gate_route46', master='shared-art/G01a.png', xy=[gx * PX, gy * PX], art=rgba(SHARED / 'G01a.png')))
    p14 = rgba(SHARED / 'P14.png')
    for s in events['signs']:
        if s['bg_type'] != 1:
            continue
        x, y = Rf.to_map(*s['cell'])
        objs.append(dict(name=f'sign_{x}_{y}', master='shared-art/P14.png', xy=[x * PX - 8, (y + 1) * PX - p14.shape[0]], art=p14, cell=[x, y]))
    for o in objs:
        al = o['art'][..., 3] > 0
        o['base'] = o['xy'][1] + int(np.nonzero(al.any(1))[0].max())
    objs.sort(key=lambda o: (o['base'], o['xy'][0]))
    for o in objs:
        over(top, o['art'], o['xy'][0], o['xy'][1], owner, o['name'])
    return bottom, flat, flat_owner, top, owner, objs, ledge_list, n_g15, q

def main(phg, catalog, engine):
    for d in (OUT, OEV, LOCAL, SHARED):
        d.mkdir(parents=True, exist_ok=True)
    stage_shared(catalog)
    bottom, flat, flat_owner, top, owner, objs, ledge_list, n_g15, q = compose(phg, engine)
    view = bottom.copy()
    for layer in (flat, top):
        a = layer[..., 3] > 0
        view[a] = layer[a, :3]
    Image.fromarray(view).save(OEV / 'composed.png')
    np.savez_compressed(OUT / 'layers.npz', ground=bottom, flat=flat, flat_owner=flat_owner.astype(str), objects=top,
                        owner=owner.astype(str), quadrants=q)
    (OUT / 'placements.json').write_text(json.dumps(dict(
        note='Every placed object: master, top-left pixel, base row. Trees on the 2x2 roots of reference.py, crown one row behind.',
        objects=[{k: v for k, v in o.items() if k != 'art'} for o in objs], ledges=ledge_list, tall_grass_cells=n_g15), indent=1, default=int) + '\n')
    print('objects', len(objs), 'ledges', len(ledge_list), 'tall grass', n_g15)

if __name__ == '__main__':
    main(*(Path(a).resolve() for a in sys.argv[1:4]))
