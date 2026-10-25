"""Route 42: native art assembled under docs/GBA_MAP_RECONSTRUCTION.md, by the process the
owner accepted for Mahogany Town, Route 43, Lake of Rage and Route 44.

    python3 tools/gba/maps/route42/assemble.py PHG_CHECKOUT CATALOG_CHECKOUT ENGINE_CHECKOUT

1. Reference: trace.py registers decoded HGSS land_data chunks 82-84 to native cells 1:1
   (numbered sheets, material grid, traversal ledger); elements.ledger decodes them flat, cell
   by cell, and labels the stairs, the Mt. Mortar mouths, the Ecruteak gate's doorway and the
   Rock Climb wall.
2. Rock, as Blackthorn's and Mahogany's installed rock: every HGSS height layer is one terrace
   (source/assemble/terrace-grid.txt), drawn with FRLG General's mountain nine-slice,
   over-rock pieces and inner corners in the Johto rock ramp, one face per metatile, as a
   top-layer overlay on plain ground (elements.rock_frlg).
3. Shared art, copied unchanged with hashes into source/shared-art/ from the Johto catalog
   (CATALOG_CHECKOUT is a checkout of branch codex/violet-city):
     ground      the accepted Cherrygrove/Route 36 painter (claude_cherrygrove/ground.py), run on
                 an 8 px lawn/road grid read from HGSS's own flat ground colours
     water       Route 30's installed HGSS freshwater texture (route30-hgss-blocks pond-15) on
                 HGSS's water cells, inside the natural bank the owner approved on Route 43
                 (water()), its shore noise repeating every 64 px along each edge, as on the Lake
     tall grass  G15, the whole-cell tall grass piece, on every HGSS tall-grass cell
     stairs      S04, the catalog's diagonal flight descending west, on HGSS's slope cells
     trees       T01 on one regular lattice of 2x2 roots per woods block (elements.tree_footprints)
     signs       P14 green rounded sign (HGSS model 32), P13 grey plaque (model 31)
     gatehouse   G02, the owner-approved east-west gatehouse, on HGSS's Ecruteak gate (model 36)
4. Local assets, HGSS's own pixels lifted from the decoded true-heights render by material:
   the Mt. Mortar mouths (cavehole), the dark cave-floor dirt (road05) and the boulders (rock01); the flower patches (flower01-03, every pixel that is not
   lawn green), as Mahogany's were.
5. The Mahogany seam: Route 42 joins Mahogany Town by a map connection, and a Gen 3 connection
   draws the neighbour with the current map's tilesets. Mahogany is locked, so the part of
   Route 42 its tilesets ever draw is built from Mahogany's own metatiles (views(); pack_fixed.py
   proves it).

Writes source/assemble/layers.npz (ground RGB with water, stairs and the cave floor, rock RGBA
with the boulders, objects RGBA, object owner, terrace levels), placements.json,
terrace-grid.txt, evidence/assemble/*.png.
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
ART = ROOT / 'gba/art/route-42'
SRC, EV = ART / 'source', ART / 'evidence'
TRACE, SHARED, LOCAL = SRC / 'trace', SRC / 'shared-art', SRC / 'local-art'
OUT, OEV = SRC / 'assemble', EV / 'assemble'
W, H = 96, 32
PX = 16

CATALOG = {  # local name -> catalog path (branch codex/violet-city)
    'T01.png': 'gba/art/johto-common/trees/source/T01.png',
    'P13.png': 'gba/art/johto-common/scenery/source/P13.png',
    'P14.png': 'gba/art/johto-common/scenery/source/P14.png',
    'G15.png': 'gba/art/johto-common/scenery/source/G15.png',
    'S04.png': 'gba/art/johto-common/scenery/source/S04.png',
    'G02.png': 'gba/art/johto-common-review/gates/refinement-4/G02.png',
    # Route 30's installed HGSS freshwater (tools/gba/maps/route30_hgss_blocks/assets.py): pond-15-<phase>
    # is open water, phase (y % 2) * 2 + x % 2 of its 32 px water texture.
    **{f'pond/pond-15-{f}.png': f'gba/art/route30-hgss-blocks/source/materials/pond-15-{f}.png' for f in range(4)},
}
WAVE = True              # the approved painter's 32 px rim wave
PATH_CORE = 32           # the approved painter's full 32 px road texture
FLOOR = 4                # HGSS height of the route floor

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
CAVE_FLOOR = ('road05', 'road05_sub')       # HGSS's dark cave-floor dirt on the Mt. Mortar ledge
ROCK_BASE = 3                               # HGSS height of Route 42's lowest ground (the lawns by the ponds)

def boulder_cells():
    """The cells HGSS's boulders (rock01) stand on: a quarter of a cell's pixels or more."""
    z = np.load(SRC / 'hgss/hgss-ground-materials.npz')
    m = z['material'] == list(z['names']).index('rock01')
    return m.reshape(H, PX, W, PX).sum(axis=(1, 3)) >= 32

def unboulder(cells):
    """HGSS reads each boulder's 2x2 footprint as a little cliff. Here a boulder is one object
    (assemble.boulders), so its cells take the ground round it: the rock top it sits on, at that
    rock's height, or the lawn, road or water about it. Collision stays HGSS's (pack.traversal)."""
    bc = boulder_cells()
    out = [list(row) for row in cells]
    for y, x in zip(*np.nonzero(bc)):
        near = [cells[ny][nx] for ny in range(y - 1, y + 2) for nx in range(x - 1, x + 2)
                if 0 <= ny < H and 0 <= nx < W and not bc[ny, nx]]
        rock = [c for c in near if c['lab'] in E.ROCK]
        water = [c for c in near if c['type'] == 0x10]
        ground = [c for c in near if c not in rock and c not in water]
        kind = max((len(rock), 'rock'), (len(water), 'water'), (len(ground), 'ground'))[1]
        c = cells[y][x]
        if kind == 'rock':
            # the rock it stands on: its own row's rock either side, else the rock about it
            row = [cells[y][nx] for nx in range(x - 3, x + 4) if 0 <= nx < W and not bc[y, nx] and cells[y][nx]['lab'] in E.ROCK]
            out[y][x] = dict(c, lab='T', peak=float(np.median([n['peak'] for n in (row or rock)])), boulder=True)
        else:
            pool = water if kind == 'water' else ground
            floors = [n['floor'] for n in pool]
            out[y][x] = dict(c, lab='.', floor=max(set(floors), key=floors.count), boulder=True)
    return out

def rock_cells(cells):
    """The ledger for the rock pass: a Mt. Mortar mouth is a face cell of the cliff it is cut
    into (its art goes over the face), and so is HGSS's Rock Climb wall (Gen 3 has none). The
    stair cells are part of the cliff they cut through: S04 is a transparent flight that needs
    its cliff behind it (Johto catalog), so the cliff runs on unbroken and the flight goes over
    it (stairs(); the cells stay walkable). The Mt. Mortar ledge's cave-floor cells are their own
    ground class, so a rock edge onto the ledge shows its dirt (owner review, Route 42)."""
    out = []
    for row in unboulder(cells):
        r = []
        for c in row:
            if c['lab'] in 'DK':
                c = dict(c, lab='S')
            elif c['lab'] == 's':
                c = dict(c, lab='W')
            if c['material'] in CAVE_FLOOR and c['lab'] not in E.ROCK:
                c = dict(c, floor='cave')
            r.append(c)
        out.append(r)
    return out

def terraces(cells):
    """Blackthorn's rock structure: every HGSS height layer is one Gen 3 terrace. A rock cell
    (ledger label T, E, S, W or N: HGSS's cliff cells, decoded flat) stands at its rock peak
    above Route 42's lowest ground (ROCK_BASE, the lawns by the ponds), so every HGSS step is a
    wall of its own (owner review: counted against HGSS, a step was missing round Mt. Mortar);
    the Mt. Mortar ledge stands at its own height, so it meets the Rock Climb slope level; every
    other cell is ground, 0."""
    lab = np.array([[c['lab'] for c in row] for row in cells])
    rock = np.isin(lab, list(E.ROCK))
    d = np.zeros((H, W), int)
    for y in range(H):
        for x in range(W):
            c = cells[y][x]
            if rock[y, x]:
                d[y, x] = max(1, round(c['peak']) - ROCK_BASE)
            elif c.get('floor') == 'cave':
                d[y, x] = round(c['ground']) - ROCK_BASE
    pad = np.pad(d, 1, mode='edge')
    lower = np.zeros((H, W), bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                lower |= pad[1 + dy:1 + dy + H, 1 + dx:1 + dx + W] < d
    return d, rock & lower, rock

def frlg_rock(cells, ground, dirt):
    """Blackthorn's installed rock (elements.rock_frlg): FRLG General's mountain nine-slice, its
    over-rock version where an edge drops to a lower terrace, and its four inner corners,
    recoloured to the Johto rock ramp, one face per metatile. The rock is a top-layer overlay;
    under its clear pixels the bottom carries the plainest 8x8 block of the ground beyond the
    edge, and its cast shadow is Cherrygrove's border grey. Any jump ledges are FRLG's, in the
    same ramp (elements.ledges_frlg), merged into the overlay."""
    rc = rock_cells(cells)
    d, face, isrock = terraces(rc)
    E.layers = lambda _cells: (d, face, isrock)
    pieces = E.frlg_pieces(ENGINE)
    out, over, _, piece = E.rock_frlg(rc, ground, pieces, E.cherry_textures(), dict(cave=dirt))
    ledge = E.ledges_frlg(rc, pieces)
    a = ledge[..., 3] > 0
    over[a] = ledge[a]
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
    material. HGSS's woods, tall grass and water cells are lawn here (the water goes over them). Ledge stones are read past: a south ledge cell's lower quadrants
    take the ground above them."""
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
            if cells[y][x]['lab'] in 'LJ':
                q[2 * y + 1, 2 * x:2 * x + 2] = q[2 * y, 2 * x:2 * x + 2]
    # G02 stands on lawn, and so does the row under it: the road meets its stairs, it does not
    # run under its base or round its foot.
    (c0, c1), (r0, r1) = E.GATE_COLS, E.GATE_ROWS
    q[2 * r0:2 * r1 + 4, 2 * c0:2 * c1 + 2] = G.GRASS
    return q

def tall_grass(cells):
    """Catalog tall grass on every HGSS tall-grass cell: G15, the whole-cell piece (AGENTS.md)."""
    grass = np.array([[c['lab'] == 'G' for c in row] for row in cells])
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    g15 = rgba(SHARED / 'G15.png')
    for y, x in zip(*np.nonzero(grass)):
        art[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX] = g15
    return art, {'G15': int(grass.sum())}

# --------------------------------------------------------------------------- water
POND_SEED = 44
GRASS_EDGE, GRASS_DARK = (104, 208, 152), (88, 176, 136)       # Cherrygrove lawn tones
MUD, BANK, SHALLOW = (160, 144, 104), (88, 112, 80), (72, 200, 224)   # Route 30's HGSS pond rim tones

def periodic_noise1(n, period, step, rng):
    """1D value noise in [-1, 1] that repeats every `period` px (grid every `step` px, wrapped)."""
    g = rng.uniform(-1, 1, period // step)
    t = np.arange(n) / step
    i0 = np.floor(t).astype(int) % len(g)
    f = t - np.floor(t)
    return g[i0] * (1 - f) + g[(i0 + 1) % len(g)] * f

def periodic_noise2(h, w, period, step, rng):
    """2D value noise in [-1, 1] that repeats every `period` px both ways."""
    k = period // step
    g = rng.uniform(-1, 1, (k, k))
    ys, xs = np.mgrid[0:h, 0:w] / step
    y0, x0 = np.floor(ys).astype(int), np.floor(xs).astype(int)
    fy, fx = ys - y0, xs - x0
    a, b = g[y0 % k, x0 % k], g[y0 % k, (x0 + 1) % k]
    c, d = g[(y0 + 1) % k, x0 % k], g[(y0 + 1) % k, (x0 + 1) % k]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy

def water_texture():
    return np.concatenate([np.concatenate([rgba(SHARED / f'pond/pond-15-{r * 2 + c}.png')[..., :3] for c in (0, 1)], 1)
                           for r in (0, 1)], 0)

def water(cells, ground, keep_dry):
    """HGSS's water cells as the natural ponds the owner
    approved on Route 43: Route 30's HGSS freshwater texture inside a rough bank in Route 30's
    rim tones (mud, dark bank line, shallow water), rounded corners, three octaves of seeded
    value noise along each edge (repeating every 64 px, for the tile budget, as on the Lake),
    lawn tufts breaking into the mud. The mean shore sits two pixels inside the water cells
    and open water reaches at least 4 px round every water cell's centre, so the Surf
    boundary is the cell edge. Rock standing in the water has water at its foot (no bank). keep_dry: Route 42 pixels drawn under Mahogany's tilesets (views()), which
    Mahogany's tilesets cannot draw water or bank in; the shore is pushed out of them."""
    from scipy.ndimage import distance_transform_edt, gaussian_filter
    rng = np.random.default_rng(POND_SEED)
    water_px = np.repeat(np.repeat(np.array([[c['lab'] == '~' for c in row] for row in cells]), PX, 0), PX, 1)
    # Rock standing in the water (the islands, the cliffs along the ponds) has water at its foot,
    # as HGSS draws it: a rock cell pixel whose nearest open ground is water counts as wet, so
    # the water runs on under the rock's clear pixels and no bank lies between rock and water.
    rockcell = np.repeat(np.repeat(np.array([[c['lab'] in 'TESWNDK' for c in row] for row in cells]), PX, 0), PX, 1)
    _, (iy, ix) = distance_transform_edt(rockcell, return_indices=True)
    wet = water_px | (rockcell & water_px[iy, ix])
    h, w = wet.shape
    soft = gaussian_filter(wet.astype(float), 5) > 0.5
    d = distance_transform_edt(soft) - distance_transform_edt(~soft)
    gy, gx = np.gradient(d)
    along_x = gy ** 2 / np.maximum(gx ** 2 + gy ** 2, 1e-9)
    nx = sum(a * periodic_noise1(w, 64, st, rng) for a, st in ((2.6, 16), (1.2, 8), (0.5, 4)))
    ny = sum(a * periodic_noise1(h, 64, st, rng) for a, st in ((2.6, 16), (1.2, 8), (0.5, 4)))
    shore = d - 2 + along_x * nx[None, :] + (1 - along_x) * ny[:, None]
    ys, xs = np.mgrid[0:h, 0:w]
    r = np.hypot(ys % PX - (PX - 1) / 2, xs % PX - (PX - 1) / 2)
    centre_cell = water_px & ~np.repeat(np.repeat(keep_dry.reshape(H, PX, W, PX).any(axis=(1, 3)), PX, 0), PX, 1)
    shore = np.where(centre_cell, np.maximum(shore, 4.5 + (4 - r) * 1.5), shore)
    if keep_dry.any():
        # Out of Mahogany's view the shore rises over 10 px from its edge, so the bank is whole.
        dd = distance_transform_edt(~keep_dry)
        shore = np.where(keep_dry, -9.0, np.minimum(shore, -0.6 + (dd - 1) * 0.6))
    tuft = periodic_noise2(h, w, 32, 4, rng) + 0.5 * periodic_noise2(h, w, 32, 1, rng)
    broken = periodic_noise2(h, w, 32, 8, rng)
    tex = water_texture()
    art = np.zeros((h, w, 4), np.uint8)
    def put(m, col):
        art[m, :3] = col; art[m, 3] = 255
    near = d > -6
    open_ = near & (shore >= 4.5)
    put(open_, tex[ys % 32, xs % 32][open_])
    band = near & (shore >= 3.2) & (shore < 4.5)
    put(band & (broken > -0.35), SHALLOW)
    put(band & (broken <= -0.35), tex[ys % 32, xs % 32][band & (broken <= -0.35)])
    put(near & (shore >= 2.2) & (shore < 3.2), BANK)
    mud = near & (shore >= 0.3) & (shore < 2.2)
    put(mud, MUD)
    put(mud & (tuft > 0.75), GRASS_EDGE)
    put(mud & (tuft < -0.95), BANK)
    put(near & (shore >= -0.6) & (shore < 0.3), GRASS_DARK)
    art[(art[..., 3] > 0) & (art[..., :3] == ground[..., :3]).all(-1), 3] = 0
    assert not (art[..., 3] > 0)[keep_dry].any(), 'water art inside the part of Route 42 Mahogany shows'
    centre = centre_cell & (ys % PX == PX // 2) & (xs % PX == PX // 2)
    assert (shore[centre] >= 3.2).all(), 'a water cell centre is not open water'
    Image.fromarray(art).save(LOCAL / 'water-banks.png')
    return art

# --------------------------------------------------------------------------- HGSS local pieces
def hgss_material(names, opaque=True):
    """HGSS's own pixels of the given materials, from the decoded true-heights render, where no
    HGSS model (a sign) stands over them."""
    z = np.load(SRC / 'hgss/hgss-ground-materials.npz')
    nm = list(z['names'])
    ref = np.array(Image.open(SRC / 'hgss/hgss-reference-true-heights.png').convert('RGB'))
    m = np.isin(z['material'], [nm.index(n) for n in names if n in nm])
    m &= np.load(SRC / 'hgss/hgss-foreground-owner.npz')['owner'] < 0     # not under a model (the signs)
    art = np.zeros(ref.shape[:2] + (4,), np.uint8)
    art[m, :3] = ref[m]; art[m, 3] = 255
    return art

def snap_pieces(art, step=8):
    """Each separate piece of a lifted HGSS layer moved to the nearest step-px corner (at most
    step / 2 px), so identical pieces share their tiles. Returns the moved layer and the moves."""
    from scipy.ndimage import label, find_objects
    lb, n = label(art[..., 3] > 0)
    out = np.zeros_like(art)
    moves = []
    for i, sl in enumerate(find_objects(lb), 1):
        y0, x0 = sl[0].start, sl[1].start
        sub = art[sl].copy(); sub[lb[sl] != i] = 0
        ny, nx = int(round(y0 / step)) * step, int(round(x0 / step)) * step
        over(out, sub, nx, ny)
        moves.append(dict(hgss_xy=[int(x0), int(y0)], xy=[nx, ny]))
    return out, moves

PEG_TONES = ((239, 214, 165), (214, 181, 148), (189, 156, 123), (165, 140, 99))   # r_climb's light pegs

PEG_SHIFT = 5           # px east: from the face's light west strip onto its darker middle

def climb_pegs(rock):
    """HGSS's Rock Climb pegs on the FRLG faces of the slope (its cells are face edge to edge):
    the light tones of HGSS's r_climb texture in the nearest light Johto rock-ramp tones, a
    one-pixel outline in the ramp's darkest tone, moved PEG_SHIFT px east onto the darker middle
    of each face, and only over the rock (rock: the rock overlay)."""
    from scipy.ndimage import binary_dilation
    art = hgss_material(['r_climb'])
    light = np.zeros(art.shape[:2], bool)
    for t in PEG_TONES:
        light |= (art[..., :3] == t).all(-1) & (art[..., 3] > 0)
    from scipy.ndimage import label
    on_rock = rock[..., 3] > 0
    light = np.roll(light, PEG_SHIFT, axis=1) & on_rock
    lb, n = label(light, np.ones((3, 3), bool))
    sizes = np.bincount(lb.ravel())
    light = (sizes[lb] >= 6) & (lb > 0)                   # whole pegs only, not specks of highlight
    ring = binary_dilation(light, np.ones((3, 3), bool)) & ~light
    ramp = np.array(E.ROCK_RAMP[1:4], int)
    src = np.roll(art, PEG_SHIFT, axis=1)
    out = np.zeros_like(art)
    for y, x in zip(*np.nonzero(light)):
        out[y, x, :3] = ramp[np.abs(ramp - src[y, x, :3].astype(int)).sum(-1).argmin()]
        out[y, x, 3] = 255
    out[ring & on_rock] = E.ROCK_RAMP[6] + (255,)
    return out

def plain_dirt(art):
    """HGSS's cave-floor dirt in its commonest tone: its one pebble (its other tones, 10x7 px on
    the Mt. Mortar ledge) is left out, for want of tile slots under Mahogany's tilesets. Only the
    ledge's own cells have it in view, and they are reached by Rock Climb alone, which Gen 3
    lacks. Returns the layer and the pebble's place."""
    a = art[..., 3] > 0
    cols, cnt = np.unique(art[a, :3], axis=0, return_counts=True)
    dirt = cols[np.argmax(cnt)]
    odd = a & (art[..., :3] != dirt).any(-1)
    out = art.copy()
    out[odd, :3] = dirt
    ys, xs = np.nonzero(odd)
    return out, ([dict(hgss_box=[int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1], left_out=True)]
                 if len(ys) else [])

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
    Image.fromarray(art).save(LOCAL / 'flowers.png')
    return art, cells

# --------------------------------------------------------------------------- colour reduction
# Local HGSS pieces: at most this many tones that Mahogany's palettes lack (Route 42 packs onto
# Mahogany's tilesets, and its own art gets the free palette slots).
# Each piece's tones merge toward the Mahogany bank its surroundings are drawn in: the cave
# mouths sit in the rock (bank 10), the flower heads and the cave-floor dirt on the lawn and
# road (bank 4). The boulders are FRLG's, in the rock ramp itself.
REDUCE = {'cave': (2, [10]), 'cave_floor': (0, [4]), 'flowers': (0, [4])}

def mahogany_tones(banks):
    """The colours in the given banks of Mahogany Town's installed palettes, RGB555."""
    out = set()
    for b in banks:
        d = 'primary/mahogany' if b < 6 else 'secondary/mahogany_town'
        lines = (ENGINE / 'data/tilesets' / d / 'palettes' / f'{b:02}.pal').read_text().splitlines()[4:19]
        out |= {tuple(int(v) >> 3 for v in l.split()) for l in lines}
    return out

def reduce_local(art, n, anchors):
    """Merge the closest pair of RGB555 tones (the rarer into the commoner; a tone Mahogany's
    palettes hold is never dropped) until at most n of the piece's tones are ones Mahogany's
    palettes lack. Shapes untouched; each kept tone keeps its HGSS 8-bit value, or takes
    Mahogany's when it merges into one of Mahogany's."""
    m = art[..., 3] > 0
    c5 = art[..., :3].astype(int) >> 3
    cols, inv, cnt = np.unique(c5[m], axis=0, return_inverse=True, return_counts=True)
    inv = inv.ravel()
    w = cnt.astype(float)
    tones = [tuple(c) for c in cols]
    anchor = [t in anchors for t in tones]
    target = list(range(len(cols)))
    near = sorted(anchors)
    merged = []
    cw = np.array([3.0, 4.0, 2.0])
    def new_count():
        return sum(1 for i in set(target) if not anchor[i] and i < len(cols) and target[i] == i)
    extra = []                                           # anchors pulled in as merge targets
    while sum(1 for i in range(len(tones)) if target[i] == i and not anchor[i]) > n:
        best = None
        alive = [i for i in range(len(tones)) if target[i] == i]
        for i in alive:
            if anchor[i]:
                continue
            for j in alive:
                if j == i:
                    continue
                d = float((((np.array(tones[i]) - np.array(tones[j])) ** 2) * cw).sum()) * np.sqrt(min(w[i], w[j]))
                if best is None or d < best[0]:
                    best = (d, i, j)
            # or straight onto Mahogany's nearest tone
            a = np.array(near)
            dd = (((a - np.array(tones[i])) ** 2) * cw).sum(1)
            k = int(dd.argmin())
            d = float(dd[k]) * np.sqrt(w[i])
            if best is None or d < best[0]:
                best = (d, i, ('anchor', tuple(near[k])))
        _, i, j = best
        if isinstance(j, tuple):
            tones.append(j[1]); anchor.append(True); w = np.append(w, 0.0); target.append(len(tones) - 1)
            j = len(tones) - 1
        keep, drop = (j, i) if anchor[j] or w[j] >= w[i] else (i, j)
        w[keep] += w[drop]
        target = [keep if t == drop else t for t in target]
        merged.append([[int(v) << 3 for v in tones[drop]], [int(v) << 3 for v in tones[keep]], int(w[drop])])
    first8 = {}
    flat = art[m]
    for k in range(len(cols)):
        first8[k] = flat[inv == k][0, :3]
    def colour(k):
        t = target[k]
        if t < len(cols) and not anchor[t]:
            return first8[t]
        return np.array([(v << 3) | (v >> 2) for v in tones[t]], np.uint8)
    out = art.copy()
    lut = np.array([colour(k) for k in range(len(cols))], np.uint8)
    out[m, :3] = lut[inv]
    return out, merged

# --------------------------------------------------------------------------- compose
def over(dst, src, x, y, owner=None, name=''):
    h, w = src.shape[:2]
    sy0, sx0 = max(0, -y), max(0, -x)
    sy1, sx1 = min(h, dst.shape[0] - y), min(w, dst.shape[1] - x)
    s = src[sy0:sy1, sx0:sx1]
    a = s[..., 3] > 0
    d = dst[y + sy0:y + sy1, x + sx0:x + sx1]
    d[a] = s[a][:, :dst.shape[-1]]
    if owner is not None:
        owner[y + sy0:y + sy1, x + sx0:x + sx1][a] = name

# Signs on their HGSS models, as Route 43 and the Lake placed them: P14 (model 32) top-left
# (x * 16 - 8, (y - 1) * 16), P13 (model 31) top-left (x * 16 - 8, (y - 1.5) * 16). The east
# route sign stands on (86, 12), two cells west of HGSS's (88, 12): there its board would lie in
# the columns Mahogany's tilesets draw (views()), and Mahogany has no tiles for it (declared
# adaptation; HGSS_SIGN_CELLS keeps HGSS's cell).
SIGNS = {(11, 17): ('P14.png', 11 * PX - 8, 16 * PX), (86, 12): ('P14.png', 86 * PX - 8, 11 * PX),
         (16, 11): ('P13.png', 16 * PX - 8, int(9.5 * PX)), (75, 12): ('P13.png', 75 * PX - 8, int(10.5 * PX))}
HGSS_SIGN_CELLS = {(86, 12): (88, 12)}
STAIRS = (70, 12)                          # S04 (one cell wide, three tall) over HGSS's slope cells (70, 13-14)
GATE = (0, 11 * PX)                        # G02's stairs on HGSS's gate doorway (6, 15-16)

def stairs(bottom, rock):
    """S04 over the cliff it cuts through (rock_cells): in S04's cells the cliff comes down to
    the ground layer, and the flight (stairs_art) goes over it on the top layer as a flat ground
    detail, so a player on the stairs stands on them (pack.FLAT). The rock and the stone treads
    keep palettes of their own."""
    x0, y0 = STAIRS[0] * PX, STAIRS[1] * PX
    h, w = rgba(SHARED / 'S04.png').shape[:2]
    sl = np.s_[y0:y0 + h, x0:x0 + w]
    a = rock[sl][..., 3] > 0
    bottom[sl][a] = rock[sl][a, :3]
    rock[sl] = 0

def stairs_art():
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    over(art, rgba(SHARED / 'S04.png'), STAIRS[0] * PX, STAIRS[1] * PX)
    return art

MAH_DX = 96                                # Route 42 x = Mahogany x + 96 (Mahogany is east of the route)

def views():
    """What each map's camera shows of the other while the other's secondary tileset is loaded.
    The player's cell is drawn at screen (112, 72), so a standing view spans x * 16 - 112 to
    x * 16 + 128 and y * 16 - 72 to y * 16 + 88. Crossing a connection swaps the secondary
    tileset at the start of the step (fieldmap.c CameraMove), while the old view is still on
    screen and scrolls out over the step. So Route 42 pixels drawn under Mahogany's tilesets are
    those in view from every walkable Mahogany cell, and from every Route 42 cell on the seam
    that steps into Mahogany; Mahogany pixels drawn under Route 42's tilesets likewise.
    Returns (route42_px, mahogany_px) masks, in each map's own pixels."""
    mt = json.loads((MAHOGANY / 'source/pack3/traversal.json').read_text())
    walk_m = {(c['x'], c['y']) for c in mt if c['foot'] in ('open', 'door')}
    cells = E.ledger(PHG)
    walk_r = {(x, y) for y in range(H) for x in range(W) if not cells[y][x]['blocked'] or cells[y][x]['type'] == 0x10}
    edge_r, edge_m = (W - 1, 0) if MAH_DX > 0 else (0, 31)
    seam_rows = {y for y in range(H) if (edge_m, y) in walk_m and (edge_r, y) in walk_r}
    r42 = np.zeros((H * PX, W * PX), bool)
    mah = np.zeros((32 * PX, 32 * PX), bool)
    def show(mask, x, y):
        """Mark the standing view centred on cell (x, y) of mask's map (x may lie outside it)."""
        x0, x1 = x * PX - 112, x * PX + 128
        y0, y1 = y * PX - 72, y * PX + 88
        mask[max(0, y0):max(0, min(mask.shape[0], y1)), max(0, x0):max(0, min(mask.shape[1], x1))] = True
    for x, y in walk_m:
        show(r42, x + MAH_DX, y)
    for y in seam_rows:
        show(r42, edge_r, y)                   # stepping into Mahogany from Route 42's edge
    for x, y in walk_r:
        show(mah, x - MAH_DX, y)
    for y in seam_rows:
        show(mah, edge_m, y)                   # stepping into Route 42 from Mahogany's edge
    return r42, mah

def compose(phg):
    global PHG
    PHG = phg
    cells = E.ledger(phg)
    trees = json.loads((TRACE / 'trees.json').read_text())['trees']
    lab = np.array([[c['lab'] for c in row] for row in cells])
    ub = unboulder(cells)
    ublab = np.array([[c['lab'] for c in row] for row in ub])
    ground, _ = paint_ground(ground_quadrants(ub, np.isin(ublab, list(E.ROCK) + ['D', 'K'])))
    reductions = {}
    lim = lambda k: (REDUCE[k][0], mahogany_tones(REDUCE[k][1]))
    fd, reductions['cave_floor'] = reduce_local(hgss_material(list(CAVE_FLOOR)), *lim('cave_floor'))
    fd, pebble_moves = plain_dirt(fd)
    Image.fromarray(fd).save(LOCAL / 'cave-floor.png')
    # The Mt. Mortar ledge is cave-floor dirt edge to edge (its commonest tone under HGSS's own
    # pixels), and it is what a rock edge onto the ledge shows past it.
    cols, cnt = np.unique(fd[fd[..., 3] > 0, :3], axis=0, return_counts=True)
    dirt = np.tile(cols[np.argmax(cnt)], (16, 16, 1)).astype(np.uint8)
    for y, x in zip(*np.nonzero(np.array([[c['material'] in CAVE_FLOOR and c['lab'] not in E.ROCK for c in row] for row in cells]))):
        ground[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX, :3] = dirt
    bottom, rock, d, isrock, piece = frlg_rock(cells, ground[..., :3].copy(), dirt)
    owner = np.full((H * PX, W * PX), '', object)
    (OUT / 'terrace-grid.txt').write_text(
        '# Route 42 rock terraces (assemble.terraces), one line per cell row: level 0-3, rock cells upper-case A/B/C\n'
        '# (the first, second and third terrace), from HGSS land_data 82-84 decoded flat (elements.ledger).\n' +
        ''.join(f'{y:02d}    ' + ''.join(('ABC'[min(d[y, x], 3) - 1] if isrock[y, x] else str(d[y, x])) for x in range(W)) + '\n'
                for y in range(H)))
    view, mah_view = views()
    # Water, the cave-floor dirt, stairs, flowers and tall grass on the ground layer.
    wa = water(cells, bottom, view)
    a = wa[..., 3] > 0
    bottom[a] = wa[a, :3]; owner[a] = 'water'
    a = fd[..., 3] > 0
    bottom[a] = fd[a, :3]; owner[a] = 'cave_floor'
    stairs(bottom, rock)
    fl, fcells = flowers(phg)
    fl, reductions['flowers'] = reduce_local(fl, *lim('flowers'))
    Image.fromarray(fl).save(LOCAL / 'flowers.png')
    tg, tg_used = tall_grass(cells)
    # The boulders on the rock layer (HGSS draws them into its rock); the Mt. Mortar mouths
    # below. HGSS's Rock Climb wall is plain FRLG cliff face here: Gen 3 has no Rock Climb.
    cave, reductions['cave'] = reduce_local(hgss_material(['cavehole']), *lim('cave'))
    # HGSS's boulders become FRLG General's boulder (metatile 0x9F's top layer) in the Johto rock
    # ramp, the rock the map is built of: one on the middle of each HGSS boulder's footprint.
    _, boulder_moves = snap_pieces(hgss_material(['rock01']), 16)
    stones = np.zeros((H * PX, W * PX, 4), np.uint8)
    frlg_boulder = E.frlg_boulder(ENGINE)
    for b in boulder_moves:
        b['frlg_xy'] = [b['xy'][0] + 8, b['xy'][1] + 8]
        over(stones, frlg_boulder, *b['frlg_xy'])
    # HGSS's Rock Climb wall is FRLG cliff face like the rest of the slope, with HGSS's climbing
    # pegs (r_climb's light tones, in the nearest rock-ramp tones) on its faces.
    pegs = climb_pegs(rock)
    a = pegs[..., 3] > 0
    stones[a] = pegs[a]
    cave, cave_moves = snap_pieces(cave)
    (LOCAL / 'reductions.json').write_text(json.dumps(dict(
        note='Local HGSS pieces: closest RGB555 tones merge (the rarer into the commoner, or onto the nearest tone '
             'Mahogany\'s palettes hold) until at most the limit of tones Mahogany lacks remain; shapes untouched. '
             'Entries: [dropped tone, kept tone, pixels].', limits={k: dict(new_tones=v[0], mahogany_banks=v[1]) for k, v in REDUCE.items()}, **reductions), indent=1) + '\n')
    Image.fromarray(cave).save(LOCAL / 'mt-mortar-mouths.png')
    Image.fromarray(stones).save(LOCAL / 'boulders-and-pegs.png')
    a = stones[..., 3] > 0
    rock[a] = stones[a]; owner[a] = 'boulder'
    # Objects, painted north to south by their base row so the nearer one covers.
    top = np.zeros((H * PX, W * PX, 4), np.uint8)
    # Tall grass and flower heads are flat ground details on the top layer, never above the
    # player (pack.FLAT), as the Lake's driftwood: their tiles then hold only their own tones
    # over a plain lawn bottom, and the colours fit Mahogany's free palette slots.
    # The Mt. Mortar mouths are too (their dark openings over the cliff faces), and S04 over
    # the cliff it cuts through (stairs()).
    for art, name in ((tg, 'flat_tall_grass'), (fl, 'flat_flowers'), (cave, 'flat_cave'), (stairs_art(), 'flat_stairs')):
        a = art[..., 3] > 0
        top[a] = art[a]; owner[a] = name
    objs = []
    t01 = rgba(SHARED / 'T01.png')
    for i, (tx, ty) in enumerate(trees):
        objs.append(dict(name=f'tree_{i}', master='shared-art/T01.png', xy=[tx * PX, ty * PX - PX], art=t01, root=[tx, ty]))
    for (sx, sy), (f, x, y) in SIGNS.items():
        objs.append(dict(name=f'sign_{sx}_{sy}', master=f'shared-art/{f}', xy=[x, y], art=rgba(SHARED / f), cell=[sx, sy],
                         hgss_cell=list(HGSS_SIGN_CELLS.get((sx, sy), (sx, sy)))))
    objs.append(dict(name='gate_ecruteak', master='shared-art/G02.png', xy=list(GATE), art=rgba(SHARED / 'G02.png')))
    for o in objs:
        a = o['art'][..., 3] > 0
        o['base'] = o['xy'][1] + int(np.nonzero(a.any(1))[0].max())
    # Round the gate the trees overlap it, as on the owner-approved Route 36 gate surround: the
    # rear row stands behind its top rows and the gate, painted later by base row, draws over
    # them with the trees seen round its roof; the first southern row stands in front, its
    # crowns over the gate's foundation (elements.gate_anchors).
    objs.sort(key=lambda o: (o['base'], o['xy'][0]))
    for o in objs:
        over(top, o['art'], o['xy'][0], o['xy'][1], owner, o['name'])
    compose.boulders, compose.caves, compose.pebbles = boulder_moves, cave_moves, pebble_moves
    # The trees alone and the gate alone, whole: where a tree and the gate share a tile, the
    # packer keeps the hidden one whole under the other, so those tiles repeat.
    compose.trees, compose.gate = np.zeros_like(top), np.zeros_like(top)
    for o in objs:
        if o['name'].startswith('tree_'):
            over(compose.trees, o['art'], o['xy'][0], o['xy'][1])
        if o['name'] == 'gate_ecruteak':
            over(compose.gate, o['art'], o['xy'][0], o['xy'][1])
    return bottom, rock, top, owner, d, objs, fcells, tg_used, view, mah_view

ENGINE = None
PHG = None
MAHOGANY = ROOT / 'gba/art/mahogany-town'

def main(phg, catalog, engine):
    global ENGINE
    ENGINE = engine
    for d in (OUT, OEV, LOCAL, SHARED):
        d.mkdir(parents=True, exist_ok=True)
    stage_shared(catalog)
    ground, rock, top, owner, levels, objs, fcells, tg_used, view, mah_view = compose(phg)
    view_img = ground.copy()
    for layer in (rock, top):
        a = layer[..., 3] > 0
        view_img[a] = layer[a, :3]
    Image.fromarray(view_img).save(OEV / 'composed.png')
    Image.fromarray(ground).save(OEV / 'ground.png')
    Image.fromarray(rock).save(OEV / 'rock.png')
    Image.fromarray(top).save(OEV / 'objects.png')
    np.savez_compressed(OUT / 'layers.npz', ground=ground, rock=rock, objects=top, owner=owner.astype(str), levels=levels, trees=compose.trees, gate=compose.gate,
                        mahogany_view=view, route_view_of_mahogany=mah_view)
    (OUT / 'placements.json').write_text(json.dumps(dict(
        note='Every placed object: master file, top-left pixel, base row. Trees sit on their decoded HGSS 2x2 roots '
             '(T01 bottom on the root bottom, crown one row behind); the signs and the gate stand on HGSS\'s own.',
        objects=[{k: v for k, v in o.items() if k != 'art'} for o in objs], flower_cells=fcells,
        tall_grass_pieces=tg_used, stairs=STAIRS, boulders=compose.boulders, cave_mouths=compose.caves, cave_floor_pebbles=compose.pebbles), indent=1, default=int) + '\n')
    print('objects', len(objs), 'flower cells', len(fcells), 'tall grass', tg_used)

if __name__ == '__main__':
    main(*(Path(a).resolve() for a in sys.argv[1:4]))
