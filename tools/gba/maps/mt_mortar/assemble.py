"""Mt. Mortar: its four floors built the way Dark Cave and Ice Path are, in HGSS's Mt. Mortar colours.

    python3 tools/gba/maps/mt_mortar/assemble.py PATH/TO/pokeheartgold ENGINE_CHECKOUT

The owner's cave method (Dark Cave, accepted 2026-11-03): each floor is mapped cell by cell from
HGSS's own data (floor heights and tier tops from its mesh, water, ledges, stairs, ladders, exits,
rock objects), drawn with the Johto routes' own pieces (FRLG rock laid out by the routes'
rock_frlg, the routes' road, FRLG General's rock-edged pond, the catalog stairs), then every
colour is swapped for HGSS's own Mt. Mortar colours (texture set 79). The layout code is Dark
Cave's assemble.py, used as a library; nothing of Dark Cave's art or tilesets is used.

Mt. Mortar's own features:

    waterfall     1F's falls (HGSS 0x13 under the falls' face): HGSS's own pixels, as Route 45's
                  cascades are (owner-accepted); Gen 3 MB_WATERFALL from the foot to the row below
                  the crest, so Waterfall climbs to open water
    Rock Climb    HGSS's walls 0x4B/0x4C: the normal wall with HGSS's climbing holds (dr_climb)
                  pasted on (AGENTS.md); Gen 3 MB_ROCK_CLIMB
    east ledges   HGSS 0x38: FRLG's ledge turned to face east (the routes draw south and west)
    ladders       FRLG Seafoam's: up-ladders (0x3D over 0x3C) its top 654 over its foot 662, the
                  single ladders down (0x3E) its ladder into a hole 645, in HGSS's ladder wood
    small rocks   HGSS's d_rock01s: the routes' boulder (FRLG General's) in that rock's own
                  rendered tones

Writes source/assemble/<floor>{.png,-class.npy,-ledger.json,-terrace-grid.txt} and
evidence/assemble/<floor>-before-after.png.
"""
from __future__ import annotations
import importlib.util, json, sys
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
MAPS = HERE.parent
sys.path.insert(0, str(HERE))
import pack as P                                      # noqa: E402

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

R = _load('mt_mortar_hgss_render', HERE / 'hgss_render.py')
sys.path.insert(0, str(MAPS / 'dark_cave'))
A = _load('dark_cave_assemble', MAPS / 'dark_cave/assemble.py')   # the cave method: layout, ground, ponds, colour swap
E, D, G = A.E, A.D, A.G
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/mt-mortar'
SRC, EV = ART / 'source', ART / 'evidence'
A.SRC, A.EV = SRC, EV
PX = 16
VOID, FLOOR, FACE, TOP, RIM, BOULDER, STAIRS, WATER, EXIT = range(9)
SEAFOAM = ('general_frlg', 'seafoam_islands_frlg')
LADDER = dict(ladder_top=654, ladder_up=662, ladder_down=645)    # FRLG Seafoam's, stacked as Seafoam stacks them
SNOW = (641, 657)                                     # Seafoam's plain floors: their colours are cut from a piece
# The falls (owner review, Nov 6): HGSS has one waterfall row (0x13, row 22) with its upper pool, real
# surfable water, behind it; its model's face is 10 units tall, which a top-down drawing lays over that
# pool. In Gen 3 the face is a column of waterfall cells between the pools, as Meteor Falls stacks it: the
# upper pool stays water down to row 18, Emerald's waterfall crest, body and body (rows 19-22) climb to it,
# its splash (row 23) lies on the lower pool.
FALLS = {'1f-entrance': (38, 52, 18, 22)}            # x0, x1, last upper-pool row, foot row (HGSS 0x13)
CAVE_WATER = [(41, 132, 165), (33, 140, 173), (24, 148, 173)]   # Dark Cave's cave water (its HGSS driver, graded): the caves' water
STAIR = 644                                          # FRLG Seafoam's ice stairs, as Ice Path draws its flights (owner's pick)
lum = lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]

def tones(tex0, *names):
    dec = {e.name: e for e in tex0.textures}
    out = set()
    for n in names:
        if n in dec:
            out |= {tuple(int(v) for v in c) for c in R.decode(tex0, dec[n], n + '_pl')[..., :3].reshape(-1, 3)}
    return sorted(out, key=lum)

def ramp(cols):
    """A route-rock ramp (outline, then six tones light to dark) from a texture's own colours."""
    cs = sorted(cols, key=lum)
    pick = [cs[min(len(cs) - 1, int(round(q * (len(cs) - 1))))] for q in (0.97, 0.82, 0.66, 0.5, 0.34, 0.18)]
    return [tuple(int(v * 0.55) for v in cs[0])] + pick

# --------------------------------------------------------------------------- the mapped shapes
def ledger(side):
    """One record per cell (assemble.ledger's fields: lab 'T' rock, '.' ground, 's' stairs, 'L'/'Q'/'R'
    ledges south/west/east; floor 'sand' or 'water'; peak, ground, level; void, boulder, exit), plus
    kind (pack.KINDS) and piece (a Seafoam ladder)."""
    hg = SRC / f'hgss/{side}'
    W, H = P.HGSS_SIZE[side]
    m = np.load(hg / 'hgss-ground-materials.npz')
    names = [str(v) for v in m['names']]
    hcls = np.array([P.CLASS.get(n, FLOOR) for n in names] + [VOID], np.int16)[m['material']]
    major = np.array([[Counter(hcls[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX].ravel().tolist()).most_common(1)[0][0]
                       for x in range(W)] for y in range(H)])
    perm = np.load(hg / 'hgss-permissions.npz')
    types, coll = perm['types'], perm['collision']
    height = np.nan_to_num(np.load(hg / 'hgss-cell-peak.npy'))
    foot = np.nan_to_num(np.load(hg / 'hgss-cell-foot.npy'))
    count = lambda n: (m['material'] == names.index(n)).reshape(H, PX, W, PX).sum((1, 3)) if n in names else np.zeros((H, W), int)
    pile, small = count('d_rock01'), count('d_rock01s')
    void = (types == 0) & (coll == 0)
    top = float(height.max()) + 1
    fx0, fx1, crest, fy = FALLS.get(side, (0, -1, 0, -1))
    cells = []
    for y in range(H):
        row = []
        for x in range(W):
            t, k, h = int(types[y, x]), int(coll[y, x]), float(height[y, x])
            c = dict(x=x, y=y, lab='.', floor='sand', ground=h, peak=h, level=h, material=major[y, x], kind='floor')
            if fx0 <= x <= fx1 and crest < y <= fy + 1:
                # the falls: Emerald's waterfall from the upper pool to the lower, its splash on the lower pool
                g = float(height[fy + 1, x])
                c.update(floor='water', level=g, ground=g, falls=True, kind='water' if y == fy + 1 else 'waterfall',
                         piece='wf_splash' if y == fy + 1 else 'wf_crest' if y == crest + 1 else 'wf_body')
            elif void[y, x]:
                c.update(lab='T', peak=top, void=True, kind='blocked')
            elif t == 0x3B:
                c.update(lab='L', kind='ledge_south')
            elif t == 0x39:
                c.update(lab='Q', kind='ledge_west')
            elif t == 0x38:
                c.update(lab='R', kind='ledge_east')
            elif t == 0x15:
                c.update(floor='water', kind='water')
            elif t in (0x4B, 0x4C):
                c.update(lab='T', climb=True, kind='climb')
            elif t == 0x6F:
                c.update(exit=True, kind='exit')
            elif t == 0x6E:
                # a hole into the wall: drawn as the wall it is set in (the face runs on unbroken), the door's
                # arch on it; still a door to walk into (pack.KINDS 'hole')
                c.update(exit=True, kind='hole', lab='T', hole=True)
            elif t in (0x3C, 0x3D, 0x3E):
                c.update(kind='ladder', piece={0x3D: 'ladder_top', 0x3C: 'ladder_up', 0x3E: 'ladder_down'}[t])
            elif k & 0x80:
                c['kind'] = 'blocked'
                if pile[y, x] >= 40:
                    # HGSS's rock pile (d_rock01, 2x2): a rock formation, one tier above its floor
                    c.update(lab='T', peak=float(foot[y, x]) + 1, formation=True)
                elif small[y, x] >= 20 and major[y, x] not in (FACE, TOP, RIM):
                    # HGSS's small rock (d_rock01s): the routes' boulder in its own tones, on the floor
                    # (or the water) under it
                    c.update(boulder=True, moss=True, floor='water' if major[y, x] == WATER else 'sand')
                else:
                    c.update(lab='T')
            elif major[y, x] == STAIRS:
                c.update(lab='s')
            elif t != 0x08:
                raise SystemExit(f'unhandled HGSS permission {side} {(x, y)} {t:#x}/{k:#x}')
            row.append(c)
        cells.append(row)
    for c in [c for row in cells for c in row if c.get('hole')]:
        # a hole's wall runs level with the wall beside it: HGSS raises the hole and its two neighbours a little,
        # which would put a bump in the face
        x, y = c['x'], c['y']
        base = [cells[y][x + dx]['peak'] for dx in (-2, 2) if 0 <= x + dx < W and cells[y][x + dx]['lab'] == 'T']
        if base:
            for dx in (-1, 0, 1):
                if 0 <= x + dx < W and cells[y][x + dx]['lab'] == 'T':
                    cells[y][x + dx]['peak'] = min(base)
        elif y > 0 and cells[y - 1][x]['lab'] == 'T':
            c['peak'] = cells[y - 1][x]['peak']
    # A lit exit's wall runs straight under it, shoulders and all, as Union Cave fits its doors (owner review,
    # Nov 8): HGSS raises the three cells under the light half a unit, which would put a bump in the rim
    for c in [c for row in cells for c in row if c['kind'] == 'exit']:
        x, y = c['x'], c['y']
        if y + 1 < H:
            base = [cells[y + 1][x + dx]['peak'] for dx in (-2, 2) if 0 <= x + dx < W and cells[y + 1][x + dx]['lab'] == 'T']
            for dx in (-1, 0, 1):
                r = cells[y + 1][x + dx] if 0 <= x + dx < W else None
                if base and r is not None and r['lab'] == 'T':
                    r['peak'] = min(base)
    for row in cells:                        # a blocked floor cell, a boulder or a ledge stands on the floor beside it
        for c in row:
            if c.get('boulder') or c['lab'] in 'LQR':
                near = [cells[c['y'] + dy][c['x'] + dx]['ground'] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                        if 0 <= c['x'] + dx < W and 0 <= c['y'] + dy < H and cells[c['y'] + dy][c['x'] + dx]['lab'] == '.']
                if near:
                    c['ground'] = min(near)
    return cells, hcls, major

# --------------------------------------------------------------------------- pieces
def ladders(engine, floor_tones, rock, wood):
    """Seafoam's ladders composed (bottom, then top) and recoloured colour for colour: wood to HGSS's
    ladder wood, Seafoam's snow cut away so the ladder stands on the cave floor, the rest to the
    floor tones; near black (the hole) kept."""
    snow = set()
    for mid in SNOW:
        b, _ = D.metatile_layers(engine, *SEAFOAM, mid)
        snow |= {tuple(int(v) for v in p) for p in b[..., :3].reshape(-1, 3)}
    out = {}
    for name, mid in LADDER.items():
        b, t = D.metatile_layers(engine, *SEAFOAM, mid)
        a = b.copy(); m = t[..., 3] > 0; a[m] = t[m]
        cut = np.array([[tuple(int(v) for v in a[yy, xx, :3]) in snow for xx in range(16)] for yy in range(16)]) & ~m
        a[cut, 3] = 0
        cols = sorted({tuple(int(v) for v in p) for p in a[a[..., 3] > 0][:, :3]}, key=lum)
        woody = [c for c in cols if c[0] - c[2] > 40]
        dark = [c for c in cols if lum(c) < 36 and c not in woody]
        rest = [c for c in cols if c not in woody and c not in dark]
        cmap = {c: c for c in dark}
        cmap.update(D.ranked(woody, wood))
        cmap.update(D.ranked(rest, floor_tones if name != 'ladder_down' else rock[1:]))
        out[name] = D.remap(a, cmap)
    return out

def flights(cells, W, H):
    """HGSS's stair cells (its `dslope`) as flights, each read from the floor at its ends: a flight
    whose floor north and south differ climbs north-south, one whose floor west and east differ climbs
    east-west. Returns Dark Cave's flight records [(kind, x, y, n, face)] for rock_cells (a north-south
    flight row by row, an east-west one column by column, its face looking to its lower side) and
    {cell: direction it climbs}."""
    from scipy import ndimage
    s = np.array([[c['lab'] == 's' for c in row] for row in cells])
    lab, n = ndimage.label(s)
    g = lambda x, y: cells[y][x]['ground'] if 0 <= x < W and 0 <= y < H and cells[y][x]['lab'] == '.' else None
    mean = lambda v: float(np.mean(v)) if v else None
    out, up = [], {}
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
        north = mean([v for x in range(x0, x1 + 1) if (v := g(x, y0 - 1)) is not None])
        south = mean([v for x in range(x0, x1 + 1) if (v := g(x, y1 + 1)) is not None])
        west = mean([v for y in range(y0, y1 + 1) if (v := g(x0 - 1, y)) is not None])
        east = mean([v for y in range(y0, y1 + 1) if (v := g(x1 + 1, y)) is not None])
        if north is not None and south is not None and abs(north - south) >= 0.5:
            d = 'north' if north > south else 'south'
            out += [('row', x0, y, x1 - x0 + 1, 'S') for y in range(y0, y1 + 1)]
        elif west is not None and east is not None and abs(west - east) >= 0.5:
            d = 'east' if east > west else 'west'
            out += [('column', x, y0, y1 - y0 + 1, 'W' if d == 'east' else 'E') for x in range(x0, x1 + 1)]
        else:
            raise SystemExit(f'flight ({x0}-{x1}, {y0}-{y1}): no floor either side tells its direction')
        up.update({(int(x), int(y)): d for y, x in zip(ys, xs)})
    return out, up

def stair_art(engine, rock):
    """Seafoam's ice stairs (Ice Path's flights) in the rock's tones, rank for rank, near black kept;
    one per direction it climbs: as drawn it climbs north, turned on its side for east and west (as
    the routes turn FRLG's ledge for a west ledge)."""
    b, t = D.metatile_layers(engine, *SEAFOAM, STAIR)
    a = b.copy(); m = t[..., 3] > 0; a[m] = t[m]
    cols = sorted({tuple(int(v) for v in p) for p in a[..., :3].reshape(-1, 3)}, key=lum)
    dark = [c for c in cols if lum(c) < 36]
    cmap = {c: c for c in dark}
    cmap.update(D.ranked([c for c in cols if c not in dark], rock[1:]))
    art = D.remap(a, cmap)[..., :3]
    return dict(north=art, south=art[::-1], east=np.rot90(art, -1), west=np.rot90(art, 1))

def east_ledges(cells, pieces, W, H):
    """FRLG's ledge turned to face east: the routes' west-facing ledge (route46 ledges_frlg) unmirrored."""
    top = np.zeros((H * PX, W * PX, 4), np.uint8)
    lp = pieces['ledge']
    lab = lambda x, y: cells[y][x]['lab'] if 0 <= x < W and 0 <= y < H else 'T'
    side = lambda p: p.T                                   # face looking east
    for y in range(H):
        for x in range(W):
            if lab(x, y) != 'R':
                continue
            vfree = lambda n: lab(x, n) not in E.ROCK and lab(x, n) not in E.LEDGES and lab(x, n) not in 'RF'
            ix = side(lp['mid']).copy()
            if vfree(y - 1):
                ix[:8, :] = side(lp['left'])[:8, :]
            if vfree(y + 1):
                ix[8:, :] = side(lp['right'])[8:, :]
            for (yy, xx), k in np.ndenumerate(ix):
                if k >= 0:
                    top[y * PX + yy, x * PX + xx] = E.ROCK_RAMP[k] + (255,)
                elif k == E.SHADOW and not top[y * PX + yy, x * PX + xx, 3]:
                    top[y * PX + yy, x * PX + xx] = E.BORDER_GRAY + (255,)
    return top

# --------------------------------------------------------------------------- build
def main(phg, engine):
    land, tex0, models, chunks, meta = R.load(phg)
    floor_t = tones(tex0, 'droad01')
    floor2_t = tones(tex0, 'droad02')
    rock_t = tones(tex0, 'dwall_s', 'dcliff01', 'dallpeak_p')
    dec = {e.name: e for e in tex0.textures}
    A.FLOOR_TEX = R.decode(tex0, dec['droad01'], 'droad01_pl')[..., :3]
    A.WATER_TEX = R.decode(tex0, dec['driver'], 'driver_pl')[..., :3]
    A.CAVE_RAMP = ramp(rock_t)
    A.POND = A.pond_pieces(engine)
    out_dir = SRC / 'assemble'; out_dir.mkdir(parents=True, exist_ok=True)
    (EV / 'assemble').mkdir(parents=True, exist_ok=True)
    tex = E.cherry_textures()
    tex['water'] = np.tile(A.POND[('M', 'M')][0], (2, 2, 1))
    pieces = E.frlg_pieces(engine)
    boulder = E.frlg_boulder(engine)
    report = {}
    for side in P.SIDES:
        W, H = P.HGSS_SIZE[side]
        A.W, A.H = E.W, E.H = W, H
        cells, hcls, major = ledger(side)
        ref = np.array(Image.open(SRC / f'hgss/{side}/hgss-render.png').convert('RGB'))
        m = np.load(SRC / f'hgss/{side}/hgss-ground-materials.npz')
        names = [str(v) for v in m['names']]
        mat = lambda *ns: np.isin(m['material'], [names.index(n) for n in ns if n in names])
        cellmask = lambda f: np.repeat(np.repeat(np.array([[bool(f(c)) for c in row] for row in cells]), PX, 0), PX, 1)
        # HGSS's small rocks in their own rendered tones; HGSS's ladder wood
        stones = sorted({tuple(int(v) for v in p) for p in ref[mat('d_rock01s')]}, key=lum)
        pebble = ramp(stones) if len(stones) > 6 else A.CAVE_RAMP
        wood = sorted({tuple(int(v) for v in p) for p in ref[cellmask(lambda c: c['kind'] == 'ladder')] if int(p[0]) - int(p[2]) > 30},
                      key=lum) or [(140, 90, 50)]
        lad = ladders(engine, floor_t, A.CAVE_RAMP, wood)
        A.WATER_TEX = np.array(CAVE_WATER, np.uint8).reshape(1, -1, 3)   # the caves' water: Dark Cave's (owner review, Nov 6)
        A.ROCK_BASE = int(np.floor(min(c['ground'] for row in cells for c in row if c['lab'] == '.') + 0.5))
        fl, climbs = flights(cells, W, H)
        rc = A.rock_cells(cells, fl)
        d, face, isrock = A.terraces(rc)
        nubs = A.regularise(rc, d, isrock)
        d, face, isrock = A.terraces(rc)
        # a wall HGSS shows facing north (its dwall_s: a floor's south wall, not seen from above) never takes a
        # south face: where the terraces would give it one, its top comes down to the level south of it, so it
        # reads as the drop HGSS draws (owner review, Nov 6)
        per = lambda *ns: mat(*ns).reshape(H, PX, W, PX).sum((1, 3))
        looks_north, looks_south = per('dwall_s', 'dwall_es', 'dwall_sw'), per('dwall_n', 'dwall_ne', 'dwall_wn')
        north_wall = {(int(x), int(y)) for y, x in np.argwhere((looks_north * 2 > PX * PX) & (looks_south * 2 < PX * PX))}
        lowered = set()
        for _ in range(4):
            lower = [(x, y) for x, y in north_wall if y + 1 < H and isrock[y, x] and d[y + 1, x] < d[y, x]]
            if not lower:
                break
            for x, y in lower:
                s_ = rc[y + 1][x]
                rc[y][x]['peak'] = s_['peak'] if isrock[y + 1, x] else s_['level'] if s_['floor'] == 'water' else s_['ground']
            lowered |= set(lower)
            d, face, isrock = A.terraces(rc)
        nubs['north_wall'] = sorted(lowered)
        E.layers = lambda _cells, _d=d, _f=face, _r=isrock: (_d, _f, _r)
        ground = A.paint_ground(np.full((H * 2, W * 2), G.PATH, np.int8), tex)
        pond = A.ponds(rc, A.POND)
        a = pond[..., 3] > 0
        ground[a] = pond[a, :3]
        # a raised floor's north edge is a drop with the rock's light top (Ice Path, owner review Nov 5)
        back = A.south_faces(rc, d, isrock)
        drops = {(x, y) for x, y in back if d[y + 1, x] >= d[y, x]}
        bottom, over, _, piece = E.rock_frlg(rc, ground, pieces, tex, None, A.topped(rc, d, isrock), back - drops, ())
        for layer in (E.ledges_frlg(rc, pieces), east_ledges(rc, pieces, W, H)):
            a = layer[..., 3] > 0
            over[a] = layer[a]
        # an east-west flight crosses a run of north-south wall tiers, a step down each tier's face: each
        # column is the routes' side stair (S04 descending west, S05 east), as Dark Cave draws its east-west
        # flights, so the steps follow the walls' angle (owner review, Nov 8)
        top = np.zeros((H * PX, W * PX, 4), np.uint8)
        for kind, x, y, n, f in fl:
            if kind == 'row':
                continue
            art = np.array(Image.open(A.STAIR_ART / ('S04.png' if f == 'W' else 'S05.png')).convert('RGBA'))
            sl = np.s_[y * PX:min(H * PX, y * PX + art.shape[0]), x * PX:(x + 1) * PX]
            art = art[:sl[0].stop - sl[0].start]
            aa = over[sl][..., 3] > 0
            bottom[sl][aa] = over[sl][aa, :3]
            over[sl] = 0
            mm = art[..., 3] > 0
            top[sl][mm] = art[mm]
        comp = bottom[..., :3].copy()
        for layer in (over, top):
            a = layer[..., 3] > 0
            comp[a] = layer[a, :3]
        comp, cmap = A.recolour(comp, tex)
        rk = over[..., 3] > 0
        # HGSS's second floor (droad02, 1F back's brown hall): its cells take droad02's tones by rank
        hg_floor = sorted({tuple(int(v) for v in c) for c in A.FLOOR_TEX.reshape(-1, 3)}, key=lum)
        brown = D.ranked(hg_floor, floor2_t)
        n1 = sum((m['material'] == names.index(n)) for n in names if n.startswith('droad01'))
        n2 = sum((m['material'] == names.index(n)) for n in names if n.startswith('droad02'))
        if np.ndim(n2) and n2.any():
            per = lambda a: a.reshape(H, PX, W, PX).sum((1, 3))
            hall = np.repeat(np.repeat(per(n2) > per(n1), PX, 0), PX, 1) & ~rk
            keys = {c: d_ for c, d_ in brown.items()}
            for yy, xx in zip(*np.nonzero(hall)):
                c = tuple(int(v) for v in comp[yy, xx])
                if c in keys:
                    comp[yy, xx] = keys[c]
        shade = cmap.get(str(tuple(E.BORDER_GRAY))) or min(map(tuple, np.unique(A.FLOOR_TEX.reshape(-1, 3), axis=0).tolist()), key=lum)
        for row in rc:
            for c in row:
                if c.get('moss'):
                    cell = comp[c['y'] * PX:(c['y'] + 1) * PX, c['x'] * PX:(c['x'] + 1) * PX]
                    for (yy, xx), k in np.ndenumerate(pieces['boulder']):
                        if k >= 0:
                            cell[yy, xx] = pebble[k]
                        elif k == E.SHADOW:
                            cell[yy, xx] = shade
                elif c.get('piece') in lad:
                    sl = np.s_[c['y'] * PX:(c['y'] + 1) * PX, c['x'] * PX:(c['x'] + 1) * PX]
                    img = lad[c['piece']]
                    mm = (img[..., 3] > 0) & ~rk[sl]
                    comp[sl][mm] = img[mm, :3]
        # every north-south flight in Ice Path's stair, climbing the way HGSS's floor says; it replaces the wall it cuts
        stairs = stair_art(engine, A.CAVE_RAMP)
        for (x, y), d_ in climbs.items():
            if d_ in ('north', 'south'):
                comp[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX] = stairs[d_]
        # the falls: Emerald's waterfall, frame 0 (tileset_anims.c animates it)
        for row in rc:
            for c in row:
                if c.get('falls'):
                    comp[c['y'] * PX:(c['y'] + 1) * PX, c['x'] * PX:(c['x'] + 1) * PX] = P.waterfall_art(engine, c['piece'])
        # The doors are Union Cave's (owner review, Nov 8): its lit door, the arch of light the owner accepted
        # there, lifted exactly from Union Cave's native map (source/union-cave/door-light.png), stands on every
        # lit exit with its foot on the straight wall rim; a hole into the wall is the same arch in dark tones
        # (its light tones rank for rank to near black, the deepest in the middle), so neither has HGSS's
        # ragged edge. Nothing of HGSS's exit art is used.
        light = np.array(Image.open(SRC / 'union-cave/door-light.png').convert('RGBA'))
        lit = sorted({tuple(int(v) for v in p) for p in light[light[..., 3] > 0][:, :3]}, key=lum)
        darks = dict(zip(lit, [(56, 56, 64), (40, 40, 48), (28, 28, 36), (16, 16, 24), (8, 8, 12)][:len(lit)]))
        hole = light.copy()
        for c, d_ in darks.items():
            hole[(light[..., :3] == c).all(-1) & (light[..., 3] > 0), :3] = d_
        ex = np.zeros((H * PX, W * PX), bool)
        for row in cells:
            for c in row:
                if c['kind'] not in ('exit', 'hole'):
                    continue
                spr = light if c['kind'] == 'exit' else hole
                h_, w_ = spr.shape[:2]
                y0, x0 = c['y'] * PX + PX - h_, c['x'] * PX + (PX - w_) // 2
                sub = comp[y0:y0 + h_, x0:x0 + w_]
                mm = spr[..., 3] > 0
                sub[mm] = spr[mm, :3]
                ex[y0:y0 + h_, x0:x0 + w_] |= mm
        holds = mat('dr_climb')
        comp[holds] = ref[holds]
        cls = np.full((H * PX, W * PX), FLOOR, np.int16)
        cls[rk] = FACE
        cls[cellmask(lambda c: c['floor'] == 'water') & ~rk] = WATER
        cls[holds] = FACE
        cls[cellmask(lambda c: (c['x'], c['y']) in climbs)] = STAIRS
        cls[top[..., 3] > 0] = STAIRS
        cls[ex] = EXIT
        # the Gen 3 map: HGSS's matrix cropped where it would not load (pack.CROP)
        (ox, oy), (cw, ch) = P.OFFSET[side], P.SIZE[side]
        win = np.s_[oy * PX:(oy + ch) * PX, ox * PX:(ox + cw) * PX]
        Image.fromarray(comp[win]).save(out_dir / f'{side}.png')
        np.save(out_dir / f'{side}-class.npy', cls[win].astype(np.int8))
        (out_dir / f'{side}-ledger.json').write_text(json.dumps(dict(offset=[ox, oy], cells=[
            dict(x=c['x'] - ox, y=c['y'] - oy, kind=c['kind'], lab=c['lab'], floor=c['floor'], piece=c.get('piece'), void=bool(c.get('void')))
            for row in rc[oy:oy + ch] for c in row[ox:ox + cw]])) + '\n')
        (out_dir / f'{side}-terrace-grid.txt').write_text(
            f'# Mt. Mortar {side} (HGSS coordinates, uncropped): one line per cell row. Ground and water: their terrace level (0-9); rock: a letter\n'
            f'# (A = level 0 ...); stairs s, ledges L/Q/R (south/west/east), boulders o, ladders H, falls F, Rock Climb C,\n'
            f'# void #. Decoded from HGSS land_data (assemble.ledger).\n' +
            ''.join(f'{y:02d}  ' + ''.join(
                '#' if c.get('void') else 'H' if c['kind'] == 'ladder' else 'F' if c.get('falls') else 'C' if c.get('climb')
                else 's' if c['lab'] == 's' else c['lab'] if c['lab'] in 'LQR' else 'o' if c.get('boulder')
                else chr(65 + min(25, d[y, x])) if isrock[y, x] else str(min(9, d[y, x]))
                for x, c in enumerate(cells[y])) + '\n' for y in range(H)))
        both = Image.new('RGB', (W * 32 + 12, H * 16), (24, 26, 30))
        both.paste(Image.fromarray(ref), (0, 0)); both.paste(Image.fromarray(comp), (W * 16 + 12, 0))
        both.save(EV / f'assemble/{side}-before-after.png')
        report[side] = dict(flights=len(fl), rock_cells=int(isrock.sum()), regularised={k: len(v) for k, v in nubs.items()},
                            kinds=dict(Counter(c['kind'] for row in rc for c in row)))
        print(side, report[side])
    (EV / 'assemble/report.json').write_text(json.dumps(dict(cave_ramp=A.CAVE_RAMP, floor_tones=floor_t, floors=report), indent=1) + '\n')
    return report

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
