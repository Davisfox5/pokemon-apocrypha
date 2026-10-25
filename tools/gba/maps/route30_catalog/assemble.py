"""Route 30: native art assembled by the Route 29 catalog process (Mahogany Town / Route 43).

    python3 tools/gba/maps/route30_catalog/assemble.py PHG_CHECKOUT CATALOG_CHECKOUT ENGINE_CHECKOUT

CATALOG_CHECKOUT is a checkout of the Johto catalog commit (pokemon-apocrypha codex/violet-city
de5d8cfb). Shared art is copied byte for byte into source/shared-art/ with its hash:

  ground      the approved Cherrygrove/Route 36 painter (claude_cherrygrove/ground.py) on an 8 px
              lawn/road grid read from HGSS's own flat ground colours; lawn and road are Cherrygrove's
              own textures, sampled at Cherrygrove's phase so the road runs into the town unchanged
  rock        Blackthorn's FRLG terraces (rock.py): every HGSS height layer one terrace
  trees       the Cherrygrove tree (T01 with the town's contact shadow) on non-overlapping 2x2 roots
  tall grass  G15 on every HGSS tall-grass cell
  ledges      L11/L12/L13 on HGSS's jump-south runs
  stairs      the Johto stair pieces (stair_pieces.py): the earlier Route 30's grey treads on north-south
              flights, Route 36's plank flight on east-west flights through a wall
  ponds       Route 43's natural pond: Route 30's HGSS freshwater texture (pond-15) with rough banks
  signs       P14 (HGSS model 32), P16 (model 34) on HGSS's sign cells; HGSS's readable sign at
              Mr. Pokemon's house (model 30) is his mailbox (buildings.py)
Local assets from HGSS's own models and textures (source/local-art/): both houses with their doors and
Mr. Pokemon's mailbox as Gen 3 sprites (buildings.py: Blackthorn's method, HGSS's models at the C06 Center's
angle), the stairs, fences, flower heads and light lawn patches. The houses' contact shadows take the
Cherrygrove tree shadow's green.

The south padding (reference.py) is Cherrygrove's own north forest band, drawn as Cherrygrove's
primary metatiles. The west wall runs on through it (columns 5-6, reference.py WALL_COLS) into Cherrygrove,
whose half of the wall cherrygrove_wall.py renders the same way. HGSS's straight south section of road sits on Cherrygrove's road columns (a quadrant
east) with the painter's wavy edge; only its last cell before the band takes the kit's straight edge.

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
from reference import W, H, PX, COL0, ROW0, HW, HH, PAD0, XPHASE, YPHASE   # noqa: E402
import rock as Rk                                    # noqa: E402
from claude_cherrygrove import ground as G           # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route30-catalog'
SRC, EV = ART / 'source', ART / 'evidence'
TRACE, SHARED, LOCAL = SRC / 'trace', SRC / 'shared-art', SRC / 'local-art'
STAIR_ART = ROOT / 'gba/art/route30-catalog/source/shared-art/stairs'   # stair_pieces.py
OUT, OEV = SRC / 'assemble', EV / 'assemble'

CATALOG = {n + '.png': f'gba/art/johto-common/scenery/source/{n}.png'
           for n in ('P14', 'P16', 'L11', 'L12', 'L13', 'G15')}
CATALOG['T01.png'] = 'gba/art/johto-common/trees/source/T01.png'
# Route 30's installed HGSS freshwater texture, as Route 43 carries it (hub branch claude/route-43).
POND = {f'pond/pond-15-{k}.png': ('claude/route-43', f'gba/art/route-43/source/shared-art/pond/pond-15-{k}.png',
                                  f'gba/art/route30-hgss-blocks/source/materials/pond-15-{k}.png') for k in range(4)}
TREE_BOX = (896, 80, 928, 128)      # Cherrygrove's standalone tree (cells 56-57, 5-7)
FLOOR = 1                           # HGSS height of Route 30's lowest walkable floor (its south end)
FLAT_RUN = 2 * PX                   # the painter's edge wave fades out over this many px towards a straight kit run
JOIN_Q = 2                          # quadrant rows of HGSS's road that step onto Cherrygrove's road columns (one cell)
SIGN_ART = {32: 'P14', 34: 'P16'}   # model 30 is Mr. Pokemon's mailbox (HGSS's readable sign there), cut with his house
HOUSE_PARTS = {'mr_pokemon_house': (1, 2, 3), 'apricorn_house': (6, 7)}   # hgss-render building indices (house, door, mailbox): the shadow's box

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
    """Cherrygrove's standalone tree with its contact shadow: the town's pixels that differ from its lawn."""
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
    shadow = Counter(map(tuple, out[a & ~m][:, :3].tolist())).most_common(1)[0][0]
    return out, shadow

def road_texture(engine):
    """Cherrygrove's own 32 px road block (the commonest pure-road block of the town), in its own phase."""
    _, _, img = cherrygrove(engine)
    core = np.array([(216, 184, 128), (224, 200, 128)])
    sand = (img[..., None, :] == core).all(-1).any(-1)
    blocks = Counter()
    for y in range(0, img.shape[0] - 31, 32):
        for x in range(0, img.shape[1] - 31, 32):
            if sand[y:y + 32, x:x + 32].all():
                blocks[img[y:y + 32, x:x + 32].tobytes()] += 1
    return np.frombuffer(blocks.most_common(1)[0][0], np.uint8).reshape(32, 32, 3)

# Cherrygrove's road kit beside its north road (rows 6-9, plain lawn on both sides): left rim, road's
# left column, road's right column, right rim; even rows / odd rows of Cherrygrove (Route 30 rows share
# their parity, H is even).
KIT_V = dict(left=((0x04F, 0x060), (0x003, 0x010)), right=((0x032, 0x026), (0x005, 0x012)))

def kit_profiles(engine):
    """The kit's vertical road edges as the painter's ring profiles: grass-side (5 px) and path-side (4 px)
    colours by distance from the edge, per y phase (32 px). Plain lawn / road pixels are None."""
    t, _, _ = cherrygrove(engine)
    lawn = {(104, 200, 152), (104, 208, 152)}
    body = {(224, 200, 128), (216, 184, 128)}
    out = {}
    for side, (rim, road) in KIT_V.items():
        strip = np.zeros((32, 32, 3), np.uint8)        # rim | road (left) or road | rim (right)
        for p in (0, 1):
            a = np.array(t.render(rim[p]).convert('RGB')); b = np.array(t.render(road[p]).convert('RGB'))
            strip[p * 16:(p + 1) * 16] = np.concatenate([a, b] if side == 'left' else [b, a], 1)
        e = 16
        col = lambda y, xs, plain: [None if tuple(strip[y, x]) in plain else tuple(int(v) for v in strip[y, x]) for x in xs]
        if side == 'left':
            out[side] = dict(grass=[col(y, range(e - 1, e - 6, -1), lawn) for y in range(32)],
                             path=[col(y, range(e, e + 4), body) for y in range(32)])
        else:
            out[side] = dict(grass=[col(y, range(e, e + 5), lawn) for y in range(32)],
                             path=[col(y, range(e - 1, e - 5, -1), body) for y in range(32)])
    return out

# --------------------------------------------------------------------------- ground
def native_cells(cells, grid):
    """The ledger in the native frame. West of HGSS column 0 is woods at column 0's height (its rock's top
    where column 0 is HGSS's west wall); the south
    padding is Cherrygrove's band at HGSS row 95's ground; the north padding is HGSS row 0 with its stairs as
    road. Blocked corners beside rock count as rock."""
    out = []
    for y in range(H):
        row = []
        for x in range(W):
            hx, hz = Rf.to_hgss(x, y)
            if y >= PAD0:                                 # Cherrygrove's band at the floor, the west wall running on through it
                c = dict(cells[HH - 1][min(max(hx, 0), HW - 1)])
                c.update(band_cell(x))
            elif hx < 0:                                  # woods beyond HGSS's west edge, at the height of what stands there:
                c = dict(cells[max(hz, 0)][0])             # where column 0 is HGSS's west wall, the wall's top, so the wall
                if c['lab'] == 'R':                        # keeps only its own east face, as at HGSS's map edge
                    c['ground'] = c['peak']
                c.update(lab='F', floor='grass')
            elif hz < 0:                                  # north padding: HGSS row 0, its stairs as road at the plateau's height
                c = dict(cells[0][hx])
                if c['lab'] == '^':
                    c.update(lab='.', floor='sand', ground=c['peak'], blocked=False)
            else:
                c = dict(cells[hz][hx])
            row.append(c)
        out.append(row)
    for y in range(H):
        for x in range(W):
            c = out[y][x]
            if c['lab'] == 'X':
                nb = [out[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= x + dx < W and 0 <= y + dy < H]
                rk = [n for n in nb if n['lab'] == 'R']
                if rk:
                    c.update(lab='R', peak=max(n['peak'] for n in rk))
    return out

def band_cell(x):
    """A band or Cherrygrove cell beside the west wall: the wall's rock at its terrace level, the woods west of
    it at the wall's top (so the wall keeps only its east faces, as on the route), the floor east of it."""
    lo = min(Rf.WALL_COLS)
    if x in Rf.WALL_COLS:
        return dict(lab='R', floor='grass', ground=float(FLOOR), peak=float(FLOOR + Rf.WALL_COLS[x]))
    top = FLOOR + Rf.WALL_COLS[lo] if x < lo else FLOOR
    return dict(lab='P', floor='sand' if x in Rf.ROAD_COLS else 'grass', ground=float(top), peak=float(top))

def ground_quadrants(phg, ncells):
    """Lawn or road per 8 px quadrant from HGSS's own flat ground colours (Route 43's rule); woods, tall
    grass, water and rock stand on their cell's floor. Ledge stones are read past. Next to the south band
    HGSS's road takes Cherrygrove's road columns: its lawn row 95 opens onto the band's road, and its left
    edge steps from column 7 to 8 for the straight run."""
    _, _, _, rgb = Rf.topdown(phg)
    rgb = rgb.astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    rock = np.array([[c['lab'] == 'R' for c in row] for row in ncells])
    rockpx = np.repeat(np.repeat(rock[ROW0:ROW0 + HH, COL0:COL0 + HW], PX, 0), PX, 1)
    water = (b > g + 30) & (b > 150)
    lawn = (g > r + 20) & ~rockpx & ~water
    sand = (r >= g) & (r > 180) & (b < 175) & ~rockpx
    q = np.repeat(np.repeat(np.array([[G.PATH if c['floor'] == 'sand' else G.GRASS for c in row] for row in ncells]), 2, 0), 2, 1).astype(np.int8)
    for qy in range(H * 2):
        for qx in range(W * 2):
            x, y = qx // 2, qy // 2
            lab = ncells[y][x]['lab']
            if lab in 'FG~P' or y >= PAD0 or x < COL0 or y < ROW0:
                if lab != 'P' and not (y < ROW0 and ncells[y][x]['floor'] == 'sand'):
                    q[qy, qx] = G.GRASS
                continue
            hqx, hqy = qx - COL0 * 2, qy - ROW0 * 2
            sl = np.s_[hqy * 8:hqy * 8 + 8, hqx * 8:hqx * 8 + 8]
            nl, ns = int(lawn[sl].sum()), int(sand[sl].sum())
            if ns >= 32 and ns > nl:
                q[qy, qx] = G.PATH
            elif nl >= 8:
                q[qy, qx] = G.GRASS
    for y in range(H):
        for x in range(W):
            if ncells[y][x]['lab'] in 'LJ':
                q[2 * y + 1, 2 * x:2 * x + 2] = q[2 * y, 2 * x:2 * x + 2]
    # Specks: flower heads and pebbles read as a quadrant or two of road; lawn holes inside the road.
    from scipy.ndimage import label
    for val, other, small in ((G.PATH, G.GRASS, 6), (G.GRASS, G.PATH, 3)):
        lab, n = label(q == val)
        sizes = np.bincount(lab.ravel())
        for i in range(1, n + 1):
            if sizes[i] < small:
                q[lab == i] = other
    # The join with Cherrygrove's road. HGSS's road stops half a row short of its south edge and sits one
    # quadrant west of Cherrygrove's: it opens onto the band's road, and its straight south section moves one
    # quadrant east onto the town's columns, so the edges run on without a step. The section keeps the
    # painter's wavy edge, as on the rest of the route; only its last JOIN_Q quadrant rows (one cell) take
    # the kit's straight edge, which the band continues.
    c0, c1 = 2 * Rf.ROAD_COLS.start, 2 * Rf.ROAD_COLS.stop          # quadrant columns of Cherrygrove's road
    band = range(c0 - 6, c1 + 6)
    has = lambda r: any(q[r, c] == G.PATH for c in band)
    last = max(r for r in range(2 * PAD0) if has(r))
    q[last + 1:2 * PAD0, c0:c1] = G.PATH
    runs = []
    for edge, want in (('left', c0), ('right', c1 - 1)):
        def edge_of(r):
            cols = [c for c in band if q[r, c] == G.PATH]
            return None if not cols else (cols[0] if edge == 'left' else cols[-1])
        have = edge_of(last)
        qy = last
        while qy >= 0 and edge_of(qy) == have:
            lo, hi = sorted((have, want))
            q[qy, lo:hi + 1] = G.PATH if (want < have) == (edge == 'left') else G.GRASS
            q[qy, want] = G.PATH
            qy -= 1
        x = want * 8 if edge == 'left' else (want + 1) * 8
        runs.append(dict(edge=edge, x=x, y0=(last - JOIN_Q + 1) * 8, y1=PAD0 * PX, hgss_edge_quadrant=int(have),
                         moved_from_quadrant_row=int(qy + 1)))
    flats = stair_landings(q, ncells)
    return q, runs, flats

STAIR_LANDING = 2                    # cells above and below a north-south flight whose road takes the flight's columns

def stair_landings(q, ncells):
    """The road meets each north-south flight edge to edge: for STAIR_LANDING cells above and below it, the
    road's quadrants are the flight's own columns and the quadrant either side lawn, wherever the road runs
    on into that cell; the painter's wave fades out there, so the road edges stand on the treads' ends.
    Returns the flat rectangles (px)."""
    lab = lambda x, y: ncells[y][x]['lab'] if 0 <= x < W and 0 <= y < H else '#'
    flats, seen = [], set()
    for y in range(H):
        for x in range(W):
            if lab(x, y) != '^' or (x, y) in seen or lab(x - 1, y) == '^' or lab(x, y - 1) == '^':
                continue
            x1 = x
            while lab(x1 + 1, y) == '^':
                x1 += 1
            if x1 == x:
                continue                                   # a one-cell column: an east-west flight
            y1 = y
            while all(lab(c, y1 + 1) == '^' for c in range(x, x1 + 1)):
                y1 += 1
            seen |= {(c, r) for c in range(x, x1 + 1) for r in range(y, y1 + 1)}
            for r in list(range(y - STAIR_LANDING, y)) + list(range(y1 + 1, y1 + 1 + STAIR_LANDING)):
                if not (0 <= r < H) or not any(q[2 * r + k, c] == G.PATH for k in (0, 1) for c in range(2 * x - 1, 2 * x1 + 3)):
                    continue
                q[2 * r:2 * r + 2, 2 * x:2 * x1 + 2] = G.PATH
                for c in (2 * x - 1, 2 * x1 + 2):
                    if 0 <= c < q.shape[1] and lab(c // 2, r) not in 'R^':
                        q[2 * r:2 * r + 2, c] = G.GRASS
            flats.append((x * PX - 8, (y - STAIR_LANDING) * PX, (x1 + 1) * PX + 8, (y1 + 1 + STAIR_LANDING) * PX))
    return flats

def paint_ground(q, road, runs, kits, flats=()):
    """The approved painter on an 8 px material grid, textures at Cherrygrove's phase. Along the straight
    runs the edge is the kit's own (no wave, the kit's profile)."""
    U = 8
    hq, wq = q.shape
    h, w = hq * U, wq * U
    tex = G.textures()
    tex[G.PATH] = road
    ys, xs = np.mgrid[0:h, 0:w]
    wave = np.array(G.WAVE)
    near = np.clip(1 - (PAD0 * PX - 1 - ys) / FLAT_RUN, 0, 1)
    for r in runs:
        dy = np.maximum(np.maximum(r['y0'] - ys, ys - (r['y1'] - 1)), 0)
        near = np.maximum(near, np.clip(1 - dy / FLAT_RUN, 0, 1) * np.clip(1 - np.abs(xs - r['x']) / FLAT_RUN, 0, 1))
    for x0, y0, x1, y1 in flats:                                     # straight road edges on the stair landings
        dx_ = np.maximum(np.maximum(x0 - xs, xs - (x1 - 1)), 0); dy_ = np.maximum(np.maximum(y0 - ys, ys - (y1 - 1)), 0)
        near = np.maximum(near, np.clip(1 - np.maximum(dx_, dy_) / FLAT_RUN, 0, 1))
    fade = 1 - near
    dx = np.rint(wave[ys % 32] * fade).astype(int); dyy = np.rint(wave[(xs + 11) % 32] * fade).astype(int)
    sx = np.clip(xs + dx, 0, w - 1) // U; sy = np.clip(ys + dyy, 0, h - 1) // U
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
    for r in runs:
        prof = kits[r['edge']]
        for y in range(r['y0'], r['y1']):
            for part in ('grass', 'path'):
                outward = (part == 'grass') == (r['edge'] == 'left')       # toward smaller x
                t = tex[G.GRASS if part == 'grass' else G.PATH]
                for k, c in enumerate(prof[part][(y + YPHASE) % 32]):
                    x = r['x'] - 1 - k if outward else r['x'] + k
                    out[y, x] = t[(y + YPHASE) % 32, (x + XPHASE) % 32] if c is None else c
    return out, mat, tex

def band(engine, bottom, flat):
    """The south padding: Cherrygrove's rows 0-2, drawn as its own metatiles; beside the west wall, which runs
    on through it, Cherrygrove's lawn and road rim."""
    t, words, _ = cherrygrove(engine)
    ids = {}
    for y in range(PAD0, H):
        for x in range(W):
            if x in Rf.WALL_COLS:
                continue
            if x in Rf.BAND_KIT:
                m = Rf.BAND_KIT[x][0][y % 2]
            else:
                cx, cy = Rf.pad_source(x, y)
                m = int(words[cy, cx]) & 1023
            sl = np.s_[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX]
            bottom[sl] = np.array(t.render(m).convert('RGB')); flat[sl] = 0
            ids[(x, y)] = m
    return ids

# --------------------------------------------------------------------------- HGSS-derived details
def lift(phg, names, keep):
    """HGSS ground-texture pixels of the named materials, in the native frame."""
    h, mat, nm, rgb = Rf.topdown(phg)
    ids = [nm.index(n) for n in names if n in nm]
    m = np.isin(mat, ids) & keep(rgb.astype(int))
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    a = art[ROW0 * PX:ROW0 * PX + HH * PX, COL0 * PX:COL0 * PX + HW * PX]
    a[m, :3] = rgb[m]; a[m, 3] = 255
    return art

def hgss_lawn_colours(phg):
    h, mat, nm, rgb = Rf.topdown(phg)
    return {tuple(int(v) for v in c) for c in np.unique(rgb[mat == nm.index('grass01gs')], axis=0)}

def flowers(phg):
    plain = np.array(sorted(hgss_lawn_colours(phg)))
    art = lift(phg, Rf.FLOWERS, lambda c: ~(c[..., None, :] == plain[None, None]).all(-1).any(-1))
    Image.fromarray(art).save(LOCAL / 'flowers.png')
    return art

def light_lawn(phg):
    plain = np.array(sorted(hgss_lawn_colours(phg)))
    art = lift(phg, Rf.LIGHT, lambda c: ~(c[..., None, :] == plain[None, None]).all(-1).any(-1))
    # Isolated pixel noise around the patches (single light specks on the plain lawn) is dropped.
    from scipy.ndimage import label
    lab, n = label(art[..., 3] > 0, structure=np.ones((3, 3)))
    sizes = np.bincount(lab.ravel())
    art[(sizes[lab] < 24) & (lab > 0)] = 0
    Image.fromarray(art).save(LOCAL / 'light-lawn.png')
    return art

def fences(phg, grid):
    """HGSS's fences: every pixel of the projected HGSS ground render whose material is fence_b (the
    posts rise above their cells, as HGSS draws them)."""
    ref = np.array(Image.open(SRC / 'hgss/hgss-ground.png').convert('RGB'))
    mz = np.load(SRC / 'hgss/hgss-ground-materials.npz')
    names = [str(n) for n in mz['names']]
    m = mz['material'] == names.index('fence_b')
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    a = art[ROW0 * PX:ROW0 * PX + HH * PX, COL0 * PX:COL0 * PX + HW * PX]
    a[m, :3] = ref[m]; a[m, 3] = 255
    Image.fromarray(art).save(LOCAL / 'fences.png')
    return art

def houses(shadow, grid):
    """Both HGSS houses and Mr. Pokemon's mailbox as Gen 3 sprites (buildings.py: HGSS's models at C06's
    angle, Blackthorn's finish), each door on HGSS's door cell and each sprite's bottom on its base row.
    Contact shadow: where HGSS's ground render is darker than its bare terrain inside the house's box, the
    Cherrygrove tree shadow's green, in the ground."""
    own = np.load(SRC / 'hgss/hgss-foreground-owner.npz')['owner']
    gnd = np.array(Image.open(SRC / 'hgss/hgss-ground.png').convert('RGB')).astype(int)
    ter = np.array(Image.open(SRC / 'hgss/hgss-terrain.png').convert('RGB')).astype(int)
    info = json.loads((LOCAL / 'buildings/buildings.json').read_text())['sprites']
    doors = sorted((x, y) for y, row in enumerate(grid) for x, ch in enumerate(row) if ch == 'D')
    mailbox = next((x, y) for y, row in enumerate(grid) for x, ch in enumerate(row) if ch == 's' and any(grid[y][x + d] == 'H' for d in (1, 2)))
    out = []
    for name, parts in HOUSE_PARTS.items():
        m = np.isin(own, parts)
        ys, xs = np.nonzero(m)
        y0, x0, y1, x1 = ys.min(), xs.min(), ys.max() + 1, xs.max() + 1
        dark = np.zeros((y1 - y0 + 16, x1 - x0, 4), np.uint8)
        sel = (gnd[y0:y1 + 16, x0:x1].sum(-1) + 24 < ter[y0:y1 + 16, x0:x1].sum(-1))
        dark[sel, :3] = shadow; dark[sel, 3] = 255
        art = rgba(LOCAL / f'buildings/{name}.png')
        hx0, hx1 = x0 // PX + COL0, (x1 - 1) // PX + COL0           # the door cell inside this house's columns
        dx, dy = next(d for d in doors if hx0 <= d[0] <= hx1)
        c0, c1 = info[name]['door_columns']
        xy = [dx * PX + PX // 2 - (c0 + c1) // 2, (dy + 1) * PX - art.shape[0]]
        top = dy * PX - (y0 + ROW0 * PX)                             # HGSS's taller house cast shadow beside its roof:
        dark[:max(top, 0)] = 0                                       # the Gen 3 sprite keeps it from the door row down
        out.append(dict(name=name, master=f'local-art/buildings/{name}.png (HGSS model {info[name]["models"][0]} at C06\'s angle)',
                        art=art, xy=xy, door=[dx, dy], shadow=dark, shadow_xy=[x0 + COL0 * PX, y0 + ROW0 * PX]))
    art = rgba(LOCAL / 'buildings/mailbox.png')
    mx, my = mailbox
    out.append(dict(name='mailbox', master='local-art/buildings/mailbox.png (HGSS model 30 at C06\'s angle)', art=art,
                    xy=[mx * PX + (PX - art.shape[1]) // 2, (my + 1) * PX - art.shape[0]], cell=[mx, my]))
    return out

LOCAL_TONES = 15                    # each local HGSS house keeps 15 tones (Mahogany's figure), one bank of its own
FLOWER_TONES, LIGHT_TONES, FENCE_TONES = 6, 3, 4

def _lab(c):
    """sRGB (0-255) to CIE Lab (D65)."""
    c = np.asarray(c, float) / 255
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    xyz = c @ np.array([[0.4124, 0.2126, 0.0193], [0.3576, 0.7152, 0.1192], [0.1805, 0.0722, 0.9505]])
    xyz /= np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)

def reduce_tones(arts, keep, n=LOCAL_TONES):
    """Reduce the local HGSS art to n tones (Mahogany's reduction: closest tones merge, shapes untouched).
    The kept tones are chosen farthest-first in Lab, starting from the most common, so a small but
    distinct tone (a red door, a blue skirting board, a chimney's black) survives; every other tone joins its nearest kept
    tone, and each group takes its most common member, an original HGSS tone. `keep` colours (the shared
    shadow) are left alone. Returns the mapping {old: new}."""
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
        i = int(np.argmax(dmin))
        chosen.append(i)
        dmin = np.minimum(dmin, np.linalg.norm(lab - lab[i], axis=1))
    for _ in range(4):                                    # refine: each group's most common member leads it
        cent = lab[chosen]
        own = np.argmin(np.linalg.norm(lab[:, None] - cent[None], axis=2), 1)
        chosen = [max((i for i in range(len(cols)) if own[i] == g), key=lambda i: cnt[cols[i]]) for g in range(len(chosen)) if (own == g).any()]
    cent = lab[chosen]
    own = np.argmin(np.linalg.norm(lab[:, None] - cent[None], axis=2), 1)
    return {cols[i]: cols[chosen[own[i]]] for i in range(len(cols))}

SNAP5 = 3.0                         # a local tone within 3 five-bit steps of a shared colour takes that colour

def shared_colours(engine, arts):
    """RGB colours of the shared art and of CherrygrovePrimary's palettes (the tones local art may snap to)."""
    from tiles import Tileset
    t = Tileset(engine, 'cherrygrove', 'cherrygrove')
    out = {tuple(int(v) for v in c) for p in t.pals[0][:6] for c in p[1:]}
    for a in arts:
        m = a[..., 3] > 0 if a.shape[-1] == 4 else np.ones(a.shape[:2], bool)
        out |= set(map(tuple, a[m][:, :3].tolist()))
    return out

def snap_tones(arts, shared):
    """Closest-tone merge of local art onto shared colours (Mahogany's reduction, against the route's own
    shared palette): a local tone within SNAP5 five-bit steps of a shared colour becomes that colour."""
    sh = np.array(sorted(shared))
    cols = set()
    for a in arts:
        m = a[..., 3] > 0
        cols |= set(map(tuple, a[m][:, :3].tolist()))
    mapping = {}
    for c in cols - shared:
        d = np.sqrt((((sh >> 3) - (np.array(c) >> 3)) ** 2).sum(-1))
        i = int(np.argmin(d))
        if d[i] <= SNAP5:
            mapping[c] = tuple(int(v) for v in sh[i])
    return mapping

def apply_tones(a, mapping):
    out = a.copy()
    m = out[..., 3] > 0
    px = out[m][:, :3]
    new = np.array([mapping.get(tuple(c), tuple(c)) for c in px.tolist()], np.uint8).reshape(-1, 3)
    sub = out[m]; sub[:, :3] = new; out[m] = sub
    return out

# --------------------------------------------------------------------------- stairs, ledges
EW_PLANK_TONES = 6
EW_ROCK_SNAP = 14.0                  # Lab distance within which a Route 36 rock colour takes Route 30/31's rock ramp

def fit_ew(pieces):
    """Route 36's flight sits in this route's wall: its rock cheeks take the wall's FRLG rock ramp (each rock
    colour its nearest ramp tone), its planks keep their own tones, reduced to EW_PLANK_TONES."""
    ramp = [tuple(int(v) for v in c) for c in Rk.ROCK_RAMP]
    lab_r = _lab(np.array(ramp))
    snap = {}
    cols = sorted({tuple(c) for p in pieces.values() for c in p[..., :3].reshape(-1, 3).tolist()})
    for c in cols:
        d = np.linalg.norm(lab_r - _lab(np.array([c]))[0], axis=1)
        if d.min() < EW_ROCK_SNAP:
            snap[c] = ramp[int(d.argmin())]
    planks = {k: apply_tones(v, snap) for k, v in pieces.items()}
    m = reduce_tones(list(planks.values()), keep=set(ramp), n=EW_PLANK_TONES)
    return {k: apply_tones(v, m) for k, v in planks.items()}


def stairs(grid):
    """The Johto stair pieces (stair_pieces.py), placed flight by flight on HGSS's stair cells. A flight with
    rock above and below it is crossed east-west: each of its columns takes Route 36's plank flight (its top
    cell with the dark cheek, plank cells, the bottom cell with the brown cheek). Every other flight is
    climbed north-south: each of its rows takes the earlier Route 30's grey treads (left end, middle, right
    end)."""
    p = {k: rgba(STAIR_ART / f'{k}.png') for k in ('ns-left', 'ns-mid', 'ns-right', 'ew-top', 'ew-mid', 'ew-bottom')}
    p.update(fit_ew({k: v for k, v in p.items() if k.startswith('ew')}))
    g = lambda x, y: grid[y][x] if 0 <= x < W and 0 <= y < H else '#'
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    placed, seen = [], set()
    for y0 in range(H):
        for x0 in range(W):
            if g(x0, y0) != '^' or (x0, y0) in seen:
                continue
            comp, todo = set(), [(x0, y0)]
            while todo:
                c = todo.pop()
                if c in comp or g(*c) != '^':
                    continue
                comp.add(c); todo += [(c[0] + dx, c[1] + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            seen |= comp
            xs, ys = sorted({c[0] for c in comp}), sorted({c[1] for c in comp})
            ew = all(g(x, ys[0] - 1) == 'R' and g(x, ys[-1] + 1) == 'R' for x in xs)
            for (x, y) in sorted(comp):
                if ew:
                    k = 'ew-top' if y == ys[0] else 'ew-bottom' if y == ys[-1] else 'ew-mid'
                else:
                    k = 'ns-left' if x == xs[0] else 'ns-right' if x == xs[-1] else 'ns-mid'
                art[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX] = p[k]
                placed.append(dict(cell=[x, y], art=k, flight='east-west' if ew else 'north-south'))
    return art, placed

def ledge_pieces():
    l11, l12, l13 = (rgba(SHARED / f'{n}.png') for n in ('L11', 'L12', 'L13'))
    return dict(left=l11, mid=l12, right=l13, single=np.concatenate([l11[:, :8], l13[:, 8:]], 1))

def ledges(grid):
    south = ledge_pieces()
    g = lambda x, y: grid[y][x] if 0 <= x < W and 0 <= y < H else '#'
    art = np.zeros((H * PX, W * PX, 4), np.uint8)
    placed = []
    for y in range(H):
        for x in range(W):
            if g(x, y) not in 'LJ':
                continue
            if g(x, y) == 'J' and not any(g(x + dx, y) == 'L' for dx in (-1, 1)):
                continue
            left, right = g(x - 1, y) in 'LJR', g(x + 1, y) in 'LJR'
            k = 'mid' if left and right else 'left' if right else 'right' if left else 'single'
            sl = np.s_[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX]
            a = south[k][..., 3] > 0
            art[sl][a] = south[k][a]
            placed.append(dict(cell=[x, y], art=f'L-{k}'))
    return art, placed

# --------------------------------------------------------------------------- ponds (Route 43)
POND_SEED = 30
GRASS_EDGE, GRASS_DARK = (104, 208, 152), (88, 176, 136)
MUD, BANK, SHALLOW = (160, 144, 104), (88, 112, 80), (72, 200, 224)

def smooth_noise(h, w, step, rng):
    """Value noise in [-1, 1]: a random grid every `step` px, bilinear between grid points (Route 43's)."""
    gh, gw = h // step + 2, w // step + 2
    g = rng.uniform(-1, 1, (gh, gw))
    ys, xs = np.mgrid[0:h, 0:w] / step
    y0, x0 = ys.astype(int), xs.astype(int)
    fy, fx = ys - y0, xs - x0
    top = g[y0, x0] * (1 - fx) + g[y0, x0 + 1] * fx
    bot = g[y0 + 1, x0] * (1 - fx) + g[y0 + 1, x0 + 1] * fx
    return top * (1 - fy) + bot * fy

def pond(grid, ground):
    """HGSS's water cells as natural ponds (Route 43's pond(), the owner's review there): Route 30's
    HGSS freshwater texture, a rough bank in Route 30's own rim tones; the shore sits about two pixels
    inside the water cells, so the Surf boundary stays the cell edge."""
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
    near[PAD0 * PX:] = False                              # the band below is Cherrygrove's own
    deep = tex[ys % 32, xs % 32]
    put(near & (shore >= 4.5), deep[near & (shore >= 4.5)])
    put(near & (shore >= 3.2) & (shore < 4.5) & (broken > -0.35), SHALLOW)
    m = near & (shore >= 3.2) & (shore < 4.5) & (broken <= -0.35); put(m, deep[m])
    put(near & (shore >= 2.2) & (shore < 3.2), BANK)
    mud = near & (shore >= 0.3) & (shore < 2.2)
    put(mud, MUD)
    put(mud & (tuft > 0.75), GRASS_EDGE)
    put(mud & (tuft < -0.95), BANK)
    put(near & (shore >= -0.6) & (shore < 0.3), GRASS_DARK)
    art[(art[..., 3] > 0) & (art[..., :3] == ground[..., :3]).all(-1), 3] = 0
    centre = water & (ys % PX == PX // 2) & (xs % PX == PX // 2)
    assert (shore[centre] >= 3.2).all(), 'a water cell centre is not open water'
    Image.fromarray(art).save(LOCAL / 'pond.png')
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
    ncells = native_cells(cells, grid)
    events = json.loads((SRC / 'hgss-events.json').read_text())
    rinfo = json.loads((SRC / 'hgss/hgss-render.json').read_text())
    roots = [tuple(r) for r in json.loads((TRACE / 'trees.json').read_text())['roots']]
    road = road_texture(engine)
    q, runs, flats = ground_quadrants(phg, ncells)
    bottom, mat, tex = paint_ground(q, road, runs, kit_profiles(engine), flats)
    # Rock terraces over the ground (bottom keeps the plain block beyond each edge).
    d, isrock = Rk.terraces(ncells, FLOOR)
    plain_tex = dict(grass=tex[G.GRASS], sand=tex[G.PATH])
    bottom, rock_over, piece = Rk.rock_frlg(ncells, d, isrock, bottom, Rk.frlg_pieces(engine), plain_tex)
    owner = np.full((H * PX, W * PX), '', object)
    flat = np.zeros((H * PX, W * PX, 4), np.uint8)
    flat_owner = np.full((H * PX, W * PX), '', object)
    def lay(art, name):
        a = art[..., 3] > 0
        flat[a] = art[a]; flat_owner[a] = name
    light, flw = light_lawn(phg), flowers(phg)
    pond_art = pond(grid, bottom)
    local_flat = dict(light_lawn=light, flowers=flw)
    g15 = rgba(SHARED / 'G15.png')
    tg = np.zeros_like(flat); n_g15 = 0
    for y in range(H):
        for x in range(W):
            if grid[y][x] == 'G':
                tg[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX] = g15; n_g15 += 1
    la, ledge_list = ledges(grid)
    sa, stair_list = stairs(grid)
    Image.fromarray(sa).save(LOCAL / 'stairs.png')
    # Terrain belongs to the bottom layer: rock faces, ponds and stairs are drawn into the ground, so
    # whatever stands on top (crowns, roofs, signs) never shares a tile, and a palette bank, with them.
    for art in (rock_over, pond_art, sa):
        a = art[..., 3] > 0
        bottom[a] = art[a][:, :3]
    top = np.zeros((H * PX, W * PX, 4), np.uint8)
    tree, shadow = cherry_tree(engine, tex[G.GRASS])
    objs = [dict(name=f'tree_{i}', master='local-art/cherrygrove-tree-with-shadow.png (T01 + shadow)', xy=[x * PX, (y - 1) * PX], art=tree, root=[x, y])
            for i, (x, y) in enumerate(roots)]
    hs = houses(shadow, grid)
    fa = fences(phg, grid)
    # Local HGSS art: the buildings and fences share 15 tones (Mahogany's rule); the flower heads and the
    # light lawn keep their closest tones within FLOWER_TONES and LIGHT_TONES, so the route's art fits
    # its seven secondary palettes.
    snap = {}
    for k, n in (('flowers', FLOWER_TONES), ('light_lawn', LIGHT_TONES)):
        m = reduce_tones([local_flat[k]], keep=set(), n=n)
        snap.update(m)
        local_flat[k] = apply_tones(local_flat[k], m)
    # The houses and the mailbox are finished Gen 3 sprites (15 colours each with the outline); each
    # house's contact shadow is ground (the bottom layer). The fences keep 4 tones.
    tones = {}
    for h in hs:
        if 'shadow' not in h:
            continue
        x0, y0 = h.pop('shadow_xy'); sa_ = h.pop('shadow'); a_ = sa_[..., 3] > 0
        region = bottom[y0:y0 + sa_.shape[0], x0:x0 + sa_.shape[1]]
        region[a_[:region.shape[0], :region.shape[1]]] = sa_[:region.shape[0], :region.shape[1]][a_[:region.shape[0], :region.shape[1]]][:, :3]
    m = reduce_tones([fa], keep=set(), n=FENCE_TONES)
    tones.update(m)
    fa = apply_tones(fa, m)
    Image.fromarray(fa).save(LOCAL / 'fences.png')
    for k, v in local_flat.items():
        Image.fromarray(v).save(LOCAL / f"{k.replace('_', '-')}.png")
    (LOCAL / 'reductions.json').write_text(json.dumps(dict(
        rule=('Local HGSS art, reduced by medoids in Lab (the most distinct original tones kept farthest-first, every other '
              'tone joining its nearest): the flower heads keep 6 tones, the light lawn 3 and the fences 4. The houses and '
              'the mailbox are Gen 3 sprites in 15 colours each (buildings.py); their contact shadows are the Cherrygrove tree '
              'shadow green, in the ground.'),
        flowers_and_light_lawn={'%d,%d,%d' % k: '%d,%d,%d' % v for k, v in sorted(snap.items())},
        merged={'%d,%d,%d' % k: '%d,%d,%d' % v for k, v in sorted(tones.items()) if k != v}), indent=1) + '\n')
    lay(local_flat['light_lawn'], 'light_lawn')
    lay(local_flat['flowers'], 'flowers')
    lay(tg, 'tall_grass')
    lay(la, 'ledge')
    band_ids = band(engine, bottom, flat)
    objs += hs
    # Each fence run is its own object, painted in order of its base row like everything that stands.
    from scipy.ndimage import label
    lab_, n_ = label(fa[..., 3] > 0, structure=np.ones((3, 3)))
    for i in range(1, n_ + 1):
        ys_, xs_ = np.nonzero(lab_ == i)
        y0_, y1_, x0_, x1_ = ys_.min(), ys_.max() + 1, xs_.min(), xs_.max() + 1
        part = np.zeros((y1_ - y0_, x1_ - x0_, 4), np.uint8)
        sel = lab_[y0_:y1_, x0_:x1_] == i
        part[sel] = fa[y0_:y1_, x0_:x1_][sel]
        objs.append(dict(name=f'fence_{i}', master='local-art/fences.png', xy=[int(x0_), int(y0_)], art=part))
    for s in events['signs']:
        if s['bg_type'] != 1:
            continue
        hx, hz = s['cell']
        b = next((b for b in rinfo['buildings'] if b['model'] in (30, 32, 34) and b['footprint'][0] - 0.5 <= hx + 0.5 <= b['footprint'][2] + 0.5
                  and b['footprint'][1] - 1 <= hz + 0.5 <= b['footprint'][3] + 1), None)
        if b is None or b['model'] not in SIGN_ART:
            continue                                     # Mr. Pokemon's mailbox: cut with his house
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
    # Nothing of Route 30's own is drawn over Cherrygrove's band.
    top[PAD0 * PX:] = 0; owner[PAD0 * PX:] = ''
    return dict(bottom=bottom, flat=flat, flat_owner=flat_owner, top=top, owner=owner, objs=objs, ledges=ledge_list,
                stairs=stair_list, n_g15=n_g15, q=q, runs=runs, band=band_ids, terrace=d, rock_piece=piece)

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
        objects=[{k: v for k, v in o.items() if k not in ('art', 'shadow')} for o in r['objs']], ledges=r['ledges'], stairs=r['stairs'],
        tall_grass_cells=r['n_g15'], straight_runs=r['runs'],
        band={f'{x},{y}': f'{m:#05x}' for (x, y), m in sorted(r['band'].items())}), indent=1, default=int) + '\n')
    print('objects', len(r['objs']), 'ledges', len(r['ledges']), 'stairs', len(r['stairs']), 'tall grass', r['n_g15'], 'runs', r['runs'])

if __name__ == '__main__':
    main(*(Path(a).resolve() for a in sys.argv[1:4]))
