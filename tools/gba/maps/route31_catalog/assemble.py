"""Route 31: native art assembled by the Route 29 catalog process (Mahogany Town / Route 43), as Route 30.

    python3 tools/gba/maps/route31_catalog/assemble.py PHG_CHECKOUT CATALOG_CHECKOUT ENGINE_CHECKOUT

CATALOG_CHECKOUT is a checkout of the Johto catalog commit (pokemon-apocrypha codex/violet-city
de5d8cfb). Shared art is copied byte for byte into source/shared-art/ with its hash:

  ground      the approved Cherrygrove/Route 36 painter on an 8 px lawn/road grid read from HGSS's own
              flat ground colours, Cherrygrove's textures at Cherrygrove's phase (through Route 30)
  rock        Blackthorn's FRLG terraces (rock.py): the ridge, the walls by the pond and Dark Cave's mountain
  trees       the Cherrygrove tree (T01 with the town's contact shadow) on non-overlapping 2x2 roots
  tall grass  G15 on every HGSS tall-grass cell
  ledges      L11/L12/L13 on the jump-south runs; turned a quarter for the jump-east run
  stairs      S04 and S05, the two side flights over the ridge (HGSS's crossing, 2 cells by 3)
  pond        Route 43's natural pond: Route 30's HGSS freshwater texture with rough banks
  gatehouse   G02, the owner-approved HGSS side gate, its stairs on HGSS's gate warps
  signs       P14 (HGSS model 32) on the route sign, P13 (model 31) on the Dark Cave plaque
Local assets cut from HGSS's own render: the cave mouth (its dark opening), flower heads and the light
lawn patches.

Writes source/assemble/layers.npz, placements.json and evidence/assemble/*.png.
"""
from __future__ import annotations
import hashlib, json, shutil, struct, subprocess, sys
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import reference as Rf                               # noqa: E402
from reference import W, H, PX, HW, HH, XPHASE, YPHASE   # noqa: E402
import rock as Rk                                    # noqa: E402
from claude_cherrygrove import ground as G           # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route31-catalog'
SRC, EV = ART / 'source', ART / 'evidence'
TRACE, SHARED, LOCAL = SRC / 'trace', SRC / 'shared-art', SRC / 'local-art'
OUT, OEV = SRC / 'assemble', EV / 'assemble'

CATALOG = {n + '.png': f'gba/art/johto-common/scenery/source/{n}.png'
           for n in ('P13', 'P14', 'L11', 'L12', 'L13', 'G15', 'S04', 'S05')}
CATALOG['T01.png'] = 'gba/art/johto-common/trees/source/T01.png'
CATALOG['G02.png'] = 'gba/art/johto-common-review/gates/refinement-4/G02.png'
POND = {f'pond/pond-15-{k}.png': ('claude/route-43', f'gba/art/route-43/source/shared-art/pond/pond-15-{k}.png',
                                  f'gba/art/route30-hgss-blocks/source/materials/pond-15-{k}.png') for k in range(4)}
TREE_BOX = (896, 80, 928, 128)      # Cherrygrove's standalone tree (cells 56-57, 5-7)
FLOOR = 3                           # HGSS height of Route 31's main floor (the pond sits below it)
SIGN_ART = {32: 'P14', 31: 'P13'}
GATE_ORIGIN = (0, 9)                # G02 is 7x7 cells; its stairs (column 6, rows 4-5) stand on HGSS's gate warps (6,13)/(6,14)
FLOWER_TONES, LIGHT_TONES = 6, 3

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
    for name, (branch, rel, origin) in POND.items():
        dst = SHARED / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        rev = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', f'origin/{branch}'], capture_output=True, text=True).stdout.strip()
        dst.write_bytes(subprocess.check_output(['git', '-C', str(ROOT), 'show', f'{rev}:{rel}']))
        prov[name] = dict(source=rel, branch=branch, commit=rev, original=origin, sha256=sha(dst))
    (SHARED / 'provenance.json').write_text(json.dumps(prov, indent=2) + '\n')

# --------------------------------------------------------------------------- town art
def cherrygrove(engine):
    from tiles import Tileset
    t = Tileset(engine, 'cherrygrove', 'cherrygrove')
    b = (engine / 'data/layouts/CherrygroveCity/map.bin').read_bytes()
    words = np.array(struct.unpack('<%dH' % (len(b) // 2), b)).reshape(-1, 80)
    return t, words, np.array(t.map_image(words.ravel().tolist(), 80))

def cherry_tree(engine, lawn_tex):
    _, _, img = cherrygrove(engine)
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
    _, _, img = cherrygrove(engine)
    core = np.array([(216, 184, 128), (224, 200, 128)])
    sand = (img[..., None, :] == core).all(-1).any(-1)
    blocks = Counter()
    for y in range(0, img.shape[0] - 31, 32):
        for x in range(0, img.shape[1] - 31, 32):
            if sand[y:y + 32, x:x + 32].all():
                blocks[img[y:y + 32, x:x + 32].tobytes()] += 1
    return np.frombuffer(blocks.most_common(1)[0][0], np.uint8).reshape(32, 32, 3)

# --------------------------------------------------------------------------- ground
def native_cells(cells):
    """The ledger in the native frame (HGSS's own). The cave mouth is rock; the gatehouse's roof row is
    gatehouse; blocked corners beside rock count as rock."""
    out = [[dict(cells[y][x]) for x in range(W)] for y in range(H)]
    for y in range(H):
        for x in range(W):
            c = out[y][x]
            if c['lab'] == 'C':
                c.update(lab='R')
            elif c['lab'] == 'X' and y + 1 < H and out[y + 1][x]['lab'] == 'B':
                c.update(lab='B')
    for y in range(H):
        for x in range(W):
            c = out[y][x]
            if c['lab'] == 'X':
                rk = [out[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                      if 0 <= x + dx < W and 0 <= y + dy < H and out[y + dy][x + dx]['lab'] == 'R']
                if rk:
                    c.update(lab='R', peak=max(n['peak'] for n in rk))
    return out

def ground_quadrants(phg, ncells):
    """Lawn or road per 8 px quadrant from HGSS's own flat ground colours (Route 43's rule); woods, tall
    grass, water, rock and the gatehouse stand on their cell's floor. Ledge stones are read past."""
    _, _, _, rgb = Rf.topdown(phg)
    rgb = rgb.astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    rock = np.array([[c['lab'] == 'R' for c in row] for row in ncells])
    rockpx = np.repeat(np.repeat(rock, PX, 0), PX, 1)
    water = (b > g + 30) & (b > 150)
    lawn = (g > r + 20) & ~rockpx & ~water
    sand = (r >= g) & (r > 180) & (b < 175) & ~rockpx
    q = np.repeat(np.repeat(np.array([[G.PATH if c['floor'] == 'sand' else G.GRASS for c in row] for row in ncells]), 2, 0), 2, 1).astype(np.int8)
    for qy in range(H * 2):
        for qx in range(W * 2):
            lab = ncells[qy // 2][qx // 2]['lab']
            if lab in 'FG~B':
                q[qy, qx] = G.GRASS
                continue
            sl = np.s_[qy * 8:qy * 8 + 8, qx * 8:qx * 8 + 8]
            nl, ns = int(lawn[sl].sum()), int(sand[sl].sum())
            if ns >= 32 and ns > nl:
                q[qy, qx] = G.PATH
            elif nl >= 8:
                q[qy, qx] = G.GRASS
    for y in range(H):
        for x in range(W):
            if ncells[y][x]['lab'] in 'LJ':
                q[2 * y + 1, 2 * x:2 * x + 2] = q[2 * y, 2 * x:2 * x + 2]
            elif ncells[y][x]['lab'] == 'E':
                q[2 * y:2 * y + 2, 2 * x + 1] = q[2 * y:2 * y + 2, 2 * x]
    from scipy.ndimage import label
    for val, other, small in ((G.PATH, G.GRASS, 6), (G.GRASS, G.PATH, 3)):
        lab, n = label(q == val)
        sizes = np.bincount(lab.ravel())
        for i in range(1, n + 1):
            if sizes[i] < small:
                q[lab == i] = other
    return q

def paint_ground(q, road):
    """The approved painter on an 8 px material grid, textures at Cherrygrove's phase."""
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
        out[mm] = t[(ys[mm] + YPHASE) % t.shape[0], (xs[mm] + XPHASE) % t.shape[1]]
    dist = {m: G._chamfer(mat == m) for m in tex}
    pa, pb = G.PROFILES[(G.GRASS, G.PATH)]
    for k, c in enumerate(pa):
        out[(mat == G.GRASS) & (dist[G.PATH] == k + 1)] = c
    for k, c in enumerate(pb):
        out[(mat == G.PATH) & (dist[G.GRASS] == k + 1)] = c
    return out, mat, tex

# --------------------------------------------------------------------------- HGSS-derived details
def lift(phg, names, keep):
    h, mat, nm, rgb = Rf.topdown(phg)
    ids = [nm.index(n) for n in names if n in nm]
    m = np.isin(mat, ids) & keep(rgb.astype(int))
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    art[m, :3] = rgb[m]; art[m, 3] = 255
    return art

def hgss_lawn_colours(phg):
    h, mat, nm, rgb = Rf.topdown(phg)
    return {tuple(int(v) for v in c) for c in np.unique(rgb[mat == nm.index('grass01gs')], axis=0)}

def flowers(phg):
    plain = np.array(sorted(hgss_lawn_colours(phg)))
    return lift(phg, Rf.FLOWERS, lambda c: ~(c[..., None, :] == plain[None, None]).all(-1).any(-1))

def light_lawn(phg):
    plain = np.array(sorted(hgss_lawn_colours(phg)))
    art = lift(phg, Rf.LIGHT, lambda c: ~(c[..., None, :] == plain[None, None]).all(-1).any(-1))
    from scipy.ndimage import label
    lab, n = label(art[..., 3] > 0, structure=np.ones((3, 3)))
    sizes = np.bincount(lab.ravel())
    art[(sizes[lab] < 24) & (lab > 0)] = 0                # isolated pixel noise round the patches
    return art

def cave_mouth(phg):
    """HGSS's Dark Cave opening: every pixel of the projected HGSS ground render whose material is
    cavehole (the dark mouth and its threshold), drawn over the FRLG face."""
    ref = np.array(Image.open(SRC / 'hgss/hgss-ground.png').convert('RGB'))
    mz = np.load(SRC / 'hgss/hgss-ground-materials.npz')
    names = [str(n) for n in mz['names']]
    m = mz['material'] == names.index('cavehole')
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    art[m, :3] = ref[m]; art[m, 3] = 255
    return art

def _lab(c):
    c = np.asarray(c, float) / 255
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    xyz = c @ np.array([[0.4124, 0.2126, 0.0193], [0.3576, 0.7152, 0.1192], [0.1805, 0.0722, 0.9505]])
    xyz /= np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)

def reduce_tones(arts, keep, n):
    """Route 30's medoid reduction: n tones kept farthest-first in Lab from the most common, every other
    tone joining its nearest, each group led by its most common member (an original HGSS tone)."""
    cnt = Counter()
    for a in arts:
        m = a[..., 3] > 0
        cnt.update(c for c in map(tuple, a[m][:, :3].tolist()) if c not in keep)
    cols = sorted(cnt, key=lambda c: -cnt[c])
    if len(cols) <= n:
        return {c: c for c in cols}
    lab = _lab(np.array(cols))
    chosen = [0]
    dmin = np.linalg.norm(lab - lab[0], axis=1)
    while len(chosen) < n:
        i = int(np.argmax(dmin)); chosen.append(i)
        dmin = np.minimum(dmin, np.linalg.norm(lab - lab[i], axis=1))
    for _ in range(4):
        own = np.argmin(np.linalg.norm(lab[:, None] - lab[chosen][None], axis=2), 1)
        chosen = [max((i for i in range(len(cols)) if own[i] == g), key=lambda i: cnt[cols[i]]) for g in range(len(chosen)) if (own == g).any()]
    own = np.argmin(np.linalg.norm(lab[:, None] - lab[chosen][None], axis=2), 1)
    return {cols[i]: cols[chosen[own[i]]] for i in range(len(cols))}

def apply_tones(a, mapping):
    out = a.copy()
    m = out[..., 3] > 0
    sub = out[m]
    sub[:, :3] = np.array([mapping.get(tuple(c), tuple(c)) for c in sub[:, :3].tolist()], np.uint8).reshape(-1, 3)
    out[m] = sub
    return out

# --------------------------------------------------------------------------- stairs, ledges
def stairs(grid):
    """HGSS's ridge crossing: two side flights side by side, each through one ridge cell, three rows tall:
    S04 (the west flight) and S05 (the east flight), each 16x48, top on the crossing's first row."""
    s = {k: rgba(SHARED / f'{k}.png') for k in ('S04', 'S05')}
    g = lambda x, y: grid[y][x] if 0 <= x < W and 0 <= y < H else '#'
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    placed = []
    for y in range(H):
        for x in range(W):
            if g(x, y) != '^' or g(x, y - 1) == '^':
                continue
            k = 'S04' if g(x + 1, y) == '^' else 'S05'
            n = 1
            while g(x, y + n) == '^':
                n += 1
            assert n == 3, ('side flight is not three rows', x, y, n)
            piece = s[k]
            sl = np.s_[y * PX:y * PX + 48, x * PX:(x + 1) * PX]
            a = piece[..., 3] > 0
            art[sl][a] = piece[a]
            placed.append(dict(cell=[x, y], art=k, rows=n))
    return art, placed

def ledges(grid):
    """L11/L12/L13 on jump-south runs; the same pieces turned a quarter anticlockwise on the jump-east run
    (high side west), its south end joined into the corner where it meets the south run (Route 29's)."""
    l11, l12, l13 = (rgba(SHARED / f'{n}.png') for n in ('L11', 'L12', 'L13'))
    south = dict(left=l11, mid=l12, right=l13, single=np.concatenate([l11[:, :8], l13[:, 8:]], 1))
    ccw = lambda a: np.rot90(a, 1).copy()
    east = dict(top=ccw(l13), mid=ccw(l12), bottom=ccw(l11))
    g = lambda x, y: grid[y][x] if 0 <= x < W and 0 <= y < H else '#'
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    placed = []
    def put(x, y, piece, name):
        sl = np.s_[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX]
        a = piece[..., 3] > 0
        art[sl][a] = piece[a]
        placed.append(dict(cell=[x, y], art=name))
    for y in range(H):
        for x in range(W):
            ch = g(x, y)
            if ch == 'L':
                left, right = g(x - 1, y) in 'LJR', g(x + 1, y) in 'LJR'
                k = 'mid' if left and right else 'left' if right else 'right' if left else 'single'
                put(x, y, south[k], f'L-{k}')
            elif ch == 'E':
                up, down = g(x, y - 1) == 'E', g(x, y + 1) in 'EJ'
                k = 'mid' if up and down else 'top' if down else 'bottom' if up else 'mid'
                put(x, y, east[k], f'E-{k}')
            elif ch == 'J':
                run_west, run_east = g(x - 1, y) == 'L', g(x + 1, y) == 'L'
                k = 'mid' if run_west and run_east else 'right' if run_west else 'left'
                base = south[k].copy()
                if g(x, y - 1) == 'E':
                    lip = int(np.nonzero((base[..., 3] > 0).any(1))[0].min())
                    top = east['mid'].copy(); top[lip:] = 0
                    m = top[..., 3] > 0
                    base[m] = top[m]
                put(x, y, base, f'corner-{k}')
    return art, placed

# --------------------------------------------------------------------------- pond (Route 43)
POND_SEED = 31
GRASS_EDGE, GRASS_DARK = (104, 208, 152), (88, 176, 136)
MUD, BANK, SHALLOW = (160, 144, 104), (88, 112, 80), (72, 200, 224)

def smooth_noise(h, w, step, rng):
    gh, gw = h // step + 2, w // step + 2
    g = rng.uniform(-1, 1, (gh, gw))
    ys, xs = np.mgrid[0:h, 0:w] / step
    y0, x0 = ys.astype(int), xs.astype(int)
    fy, fx = ys - y0, xs - x0
    top = g[y0, x0] * (1 - fx) + g[y0, x0 + 1] * fx
    bot = g[y0 + 1, x0] * (1 - fx) + g[y0 + 1, x0 + 1] * fx
    return top * (1 - fy) + bot * fy

def pond(grid, ground):
    """HGSS's water cells as a natural pond (Route 43's pond(), the owner's review there). Where the pond
    meets rock (the ridge to its east, the wall on its south-west), the rock's own face is the bank."""
    from scipy.ndimage import distance_transform_edt, gaussian_filter
    rng = np.random.default_rng(POND_SEED)
    water = np.repeat(np.repeat(np.array([[ch == '~' for ch in row] for row in grid]), PX, 0), PX, 1)
    h, w = water.shape
    soft = gaussian_filter(water.astype(float), 5, mode='nearest') > 0.5
    d = distance_transform_edt(soft) - distance_transform_edt(~soft)
    shore = d - 2 + 2.6 * smooth_noise(h, w, 14, rng) + 1.2 * smooth_noise(h, w, 6, rng) + 0.5 * smooth_noise(h, w, 3, rng)
    tuft = smooth_noise(h, w, 3, rng) + 0.5 * rng.uniform(-1, 1, (h, w))
    broken = smooth_noise(h, w, 5, rng)
    tex = np.concatenate([np.concatenate([rgba(SHARED / f'pond/pond-15-{r * 2 + c}.png')[..., :3] for c in (0, 1)], 1)
                          for r in (0, 1)], 0)
    ys, xs = np.mgrid[0:h, 0:w]
    art = np.zeros((h, w, 4), np.uint8)
    def put(m, col):
        art[m, :3] = col; art[m, 3] = 255
    near = d > -6
    deep = tex[ys % 32, xs % 32]
    m = near & (shore >= 4.5); put(m, deep[m])
    put(near & (shore >= 3.2) & (shore < 4.5) & (broken > -0.35), SHALLOW)
    m = near & (shore >= 3.2) & (shore < 4.5) & (broken <= -0.35); put(m, deep[m])
    put(near & (shore >= 2.2) & (shore < 3.2), BANK)
    mud = near & (shore >= 0.3) & (shore < 2.2)
    put(mud, MUD)
    put(mud & (tuft > 0.75), GRASS_EDGE)
    put(mud & (tuft < -0.95), BANK)
    put(near & (shore >= -0.6) & (shore < 0.3), GRASS_DARK)
    rock = np.repeat(np.repeat(np.array([[ch == 'R' for ch in row] for row in grid]), PX, 0), PX, 1)
    art[rock] = 0
    art[(art[..., 3] > 0) & (art[..., :3] == ground[..., :3]).all(-1), 3] = 0
    centre = water & (ys % PX == PX // 2) & (xs % PX == PX // 2)
    assert (shore[centre] >= 3.2).all(), 'a water cell centre is not open water'
    return art

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
    lines = [l for l in (TRACE / 'material-grid.txt').read_text().splitlines() if l[:3].isdigit()]
    return [list(l.split()[1]) for l in lines]

def compose(phg, engine):
    grid = read_grid()
    cells = json.loads((TRACE / 'ledger.json').read_text())['cells']
    ncells = native_cells(cells)
    events = json.loads((SRC / 'hgss-events.json').read_text())
    rinfo = json.loads((SRC / 'hgss/hgss-render.json').read_text())
    roots = [tuple(r) for r in json.loads((TRACE / 'trees.json').read_text())['roots']]
    road = road_texture(engine)
    q = ground_quadrants(phg, ncells)
    bottom, mat, tex = paint_ground(q, road)
    d, isrock = Rk.terraces(ncells, FLOOR)
    bottom, rock_over, piece = Rk.rock_frlg(ncells, d, isrock, bottom, Rk.frlg_pieces(engine), dict(grass=tex[G.GRASS], sand=tex[G.PATH]))
    owner = np.full((H * PX, W * PX), '', object)
    flat = np.zeros((H * PX, W * PX, 4), np.uint8)
    flat_owner = np.full((H * PX, W * PX), '', object)
    def lay(art, name):
        a = art[..., 3] > 0
        flat[a] = art[a]; flat_owner[a] = name
    light, flw = light_lawn(phg), flowers(phg)
    tones = {}
    for name, n in (('flowers', FLOWER_TONES), ('light_lawn', LIGHT_TONES)):
        art = flw if name == 'flowers' else light
        m = reduce_tones([art], keep=set(), n=n); tones[name] = m
        art = apply_tones(art, m)
        Image.fromarray(art).save(LOCAL / f"{name.replace('_', '-')}.png")
        if name == 'flowers':
            flw = art
        else:
            light = art
    (LOCAL / 'reductions.json').write_text(json.dumps(dict(
        rule=('Local HGSS art, reduced by medoids in Lab (Route 30\'s rule): the flower heads keep 6 tones, the light lawn 3.'),
        merged={k: {'%d,%d,%d' % a: '%d,%d,%d' % b for a, b in sorted(v.items()) if a != b} for k, v in tones.items()}), indent=1) + '\n')
    pond_art = pond(grid, bottom)
    cave = cave_mouth(phg)
    Image.fromarray(cave).save(LOCAL / 'cave-mouth.png')
    sa, stair_list = stairs(grid)
    # Terrain belongs to the bottom layer: rock faces, the pond, the cave mouth and the stairs are drawn into
    # the ground, so whatever stands on top (crowns, the gatehouse, signs) never shares a tile with them.
    for art in (rock_over, pond_art, cave, sa):
        a = art[..., 3] > 0
        bottom[a] = art[a][:, :3]
    lay(light, 'light_lawn')
    lay(flw, 'flowers')
    g15 = rgba(SHARED / 'G15.png')
    tg = np.zeros_like(flat); n_g15 = 0
    for y in range(H):
        for x in range(W):
            if grid[y][x] == 'G':
                tg[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX] = g15; n_g15 += 1
    lay(tg, 'tall_grass')
    la, ledge_list = ledges(grid)
    lay(la, 'ledge')
    top = np.zeros((H * PX, W * PX, 4), np.uint8)
    tree = cherry_tree(engine, tex[G.GRASS])
    objs = [dict(name=f'tree_{i}', master='local-art/cherrygrove-tree-with-shadow.png (T01 + shadow)', xy=[x * PX, (y - 1) * PX], art=tree, root=[x, y])
            for i, (x, y) in enumerate(roots)]
    gx, gy = GATE_ORIGIN
    objs.append(dict(name='gate_violet', master='shared-art/G02.png', xy=[gx * PX, gy * PX], art=rgba(SHARED / 'G02.png')))
    for s in events['signs']:
        if s['bg_type'] != 1:
            continue
        hx, hz = s['cell']
        b = next(b for b in rinfo['buildings'] if b['model'] in SIGN_ART and b['footprint'][0] - 0.5 <= hx + 0.5 <= b['footprint'][2] + 0.5
                 and b['footprint'][1] - 1 <= hz + 0.5 <= b['footprint'][3] + 1)
        k = SIGN_ART[b['model']]
        art = rgba(SHARED / f'{k}.png')
        x, y = Rf.to_map(hx, hz)
        objs.append(dict(name=f'sign_{x}_{y}', master=f'shared-art/{k}.png', model=b['model'], xy=[x * PX - 8, (y + 1) * PX - art.shape[0]], art=art, cell=[x, y]))
    for o in objs:
        al = o['art'][..., 3] > 0
        o['base'] = o['xy'][1] + int(np.nonzero(al.any(1))[0].max())
    objs.sort(key=lambda o: (o['base'], o['xy'][0]))
    for o in objs:
        over(top, o['art'], o['xy'][0], o['xy'][1], owner, o['name'])
    return dict(bottom=bottom, flat=flat, flat_owner=flat_owner, top=top, owner=owner, objs=objs, ledges=ledge_list,
                stairs=stair_list, n_g15=n_g15, q=q, terrace=d, rock_piece=piece)

def main(phg, catalog, engine):
    for d in (OUT, OEV, LOCAL, SHARED):
        d.mkdir(parents=True, exist_ok=True)
    stage_shared(catalog)
    r = compose(phg, engine)
    view = r['bottom'].copy()
    for layer in (r['flat'], r['top']):
        a = layer[..., 3] > 0
        view[a] = layer[a, :3]
    Image.fromarray(view).save(OEV / 'composed.png')
    np.savez_compressed(OUT / 'layers.npz', ground=r['bottom'], flat=r['flat'], flat_owner=r['flat_owner'].astype(str), objects=r['top'],
                        owner=r['owner'].astype(str), quadrants=r['q'], terrace=r['terrace'])
    (OUT / 'placements.json').write_text(json.dumps(dict(
        note='Every placed object: master, top-left pixel, base row. Trees on the 2x2 roots of reference.py, crown one row behind.',
        objects=[{k: v for k, v in o.items() if k != 'art'} for o in r['objs']], ledges=r['ledges'], stairs=r['stairs'],
        tall_grass_cells=r['n_g15']), indent=1, default=int) + '\n')
    print('objects', len(r['objs']), 'ledges', len(r['ledges']), 'stairs', r['stairs'], 'tall grass', r['n_g15'])

if __name__ == '__main__':
    main(*(Path(a).resolve() for a in sys.argv[1:4]))
