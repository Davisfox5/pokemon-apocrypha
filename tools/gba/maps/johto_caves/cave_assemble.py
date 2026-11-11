"""A Johto cave's floors built by the owner's cave method (Dark Cave, accepted 2026-11-03; Ice Path;
Mt. Mortar), its config in the cave's own folder (cave.py).

    python3 tools/gba/maps/<cave>/assemble.py PATH/TO/pokeheartgold ENGINE_CHECKOUT

Each floor is mapped cell by cell from HGSS's own data (floor heights and tier tops from its mesh,
water, ledges, stairs, ladders, exits, rock objects), drawn with the Johto routes' own pieces (FRLG
rock laid out by the routes' rock_frlg, the routes' road, FRLG General's rock-edged pond, Seafoam's
stairs and ladders), then every colour is swapped for HGSS's own colours for the cave (its texture
set). The layout code is Dark Cave's assemble.py, used as a library, with Mt. Mortar's additions and
the owner's reviews of both:

    stairs        one stair throughout: north-south flights Seafoam's 644 (Ice Path's), each climbing the
                  way HGSS's floor says; east-west flights the routes' side stairs (S04/S05), down each tier
    water         Dark Cave's cave water in FRLG's rock-edged pond
    faces         a wall HGSS shows facing north never takes a south face; a raised floor's north edge
                  is a drop with the rock's light top
    ladders       Seafoam's: an up-ladder its top over its foot (HGSS's foot alone gets the top drawn on
                  the wall above it), a ladder down its ladder into a hole
    doors         Union Cave's own door (owner direction, Mt. Mortar): its arch light on a lit exit, the
                  same arch in darks on a hole or an exit into the dark, set in a levelled wall
    small rocks   the routes' boulder (FRLG General's) in the rock's own rendered tones; on water too

Cave-specific pieces, each from cave.py:

    floor 2       a second floor texture (Dragon's Den's moss): its cells take that texture's tones
    puddles       HGSS 0x16: Emerald's own puddle (general, metatiles 200-218, its nine-slice) in cave
                  water and the floor's tones; Gen 3 MB_PUDDLE
    kept pixels   where Gen 3 has no piece (a shrine on its deck, a whirlpool, a wooden pier), HGSS's own
                  pixels, as Route 45's cascades and Mt. Mortar's climbing holds; the cells under them
                  are water at the lake's level (walkable on a deck, solid elsewhere)
    whirlpools    HGSS 0x11: Gen 3 has no Whirlpool; solid water under HGSS's own whirlpool

Writes source/assemble/<floor>{.png,-class.npy,-ledger.json,-terrace-grid.txt} and
evidence/assemble/<floor>-before-after.png.
"""
from __future__ import annotations
import importlib.util, json, sys
from collections import Counter, deque
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
MAPS = HERE.parent
import cave                                           # noqa: E402  (the cave's config, from its own folder)
import cave_pack as P                                 # noqa: E402
import cave_render                                    # noqa: E402

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

R = cave_render.renderer()
sys.path.insert(0, str(MAPS / 'dark_cave'))
A = _load('dark_cave_assemble', MAPS / 'dark_cave/assemble.py')   # the cave method: layout, ground, ponds, colour swap
E, D, G = A.E, A.D, A.G
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art' / cave.ART
SRC, EV = ART / 'source', ART / 'evidence'
A.SRC, A.EV = SRC, EV
UNION_DOOR = ROOT / 'gba/art/mt-mortar/source/union-cave/door-light.png'   # Union Cave's door, cut from its native map
PX = 16
VOID, FLOOR, FACE, TOP, RIM, BOULDER, STAIRS, WATER, EXIT = range(9)
SEAFOAM = ('general_frlg', 'seafoam_islands_frlg')
LADDER = dict(ladder_top=654, ladder_up=662, ladder_down=645)    # FRLG Seafoam's, stacked as Seafoam stacks them
SNOW = (641, 657)                                     # Seafoam's plain floors: their colours are cut from a piece
PUDDLE = {('N', 'W'): 200, ('N', 'M'): 201, ('N', 'E'): 202, ('M', 'W'): 208, ('M', 'M'): 209, ('M', 'E'): 210,
          ('S', 'W'): 216, ('S', 'M'): 217, ('S', 'E'): 218}   # Emerald general's puddle, nine-slice
CAVE_WATER = [(41, 132, 165), (33, 140, 173), (24, 148, 173)]   # Dark Cave's cave water: the caves' water
STAIR = 644                                          # FRLG Seafoam's stairs, as Ice Path draws its flights
DARKS = [(56, 56, 64), (40, 40, 48), (28, 28, 36), (16, 16, 24), (8, 8, 12)]   # Union Cave's arch in darks
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

def kept_models(side):
    """Indices (hgss-render.json buildings) of the models whose own pixels are kept."""
    meta = json.loads((SRC / f'hgss/{side}/hgss-render.json').read_text())
    return [i for i, b in enumerate(meta['buildings']) if set(b['names']) & set(cave.KEEP_MODELS)]

def reach_open(types, coll, starts):
    """Cells reachable from the warps over every cell HGSS leaves open (its collision bit 7 clear), water
    included: what is not, among HGSS's empty cells (type 0, collision 0), is the void outside the cave."""
    H, W = types.shape
    seen = set(starts); q = deque(starts)
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if 0 <= n[0] < W and 0 <= n[1] < H and n not in seen and not coll[n[1], n[0]] & 0x80:
                seen.add(n); q.append(n)
    return seen

# --------------------------------------------------------------------------- the mapped shapes
def ledger(side):
    """One record per cell (Dark Cave's ledger fields: lab 'T' rock, '.' ground, 's' stairs, 'L'/'Q'/'R'
    ledges south/west/east; floor 'sand' or 'water'; peak, ground, level; void, boulder, exit), plus
    kind (cave_pack.KINDS) and piece (a Seafoam ladder)."""
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
    count = lambda *ns: sum(((m['material'] == names.index(n)).reshape(H, PX, W, PX).sum((1, 3)) for n in ns if n in names),
                            np.zeros((H, W), int))
    pile, small, sea = count('d_rock01'), count(*cave.SMALL_ROCKS), count(*cave.SEA_ROCKS)
    deck = count(*cave.DECK_MATERIALS)
    owner = np.load(hg / 'hgss-foreground-owner.npz')['owner']
    model = np.isin(owner, kept_models(side)).reshape(H, PX, W, PX).sum((1, 3))
    ev = json.loads((SRC / f'hgss-events/{side}.json').read_text())
    starts = [tuple(w['cell']) for w in ev['warps']]
    void = (types == 0) & (coll == 0)
    seen = reach_open(types, coll, starts)
    void &= ~np.array([[(x, y) in seen for x in range(W)] for y in range(H)])
    water = types == 0x15
    lake = float(np.median(height[water])) if water.any() else 0.0      # the lake's level, for decks over it
    top = float(height.max()) + 1
    dark = count('chole_in', 'chole_out') > count('chole_light', 'chole_light2', 'light')
    unbuilt = {tuple(w['cell']) for w in ev['warps'] if w['dest'] in cave.UNBUILT}
    cells = []
    for y in range(H):
        row = []
        for x in range(W):
            t, k, h = int(types[y, x]), int(coll[y, x]), float(height[y, x])
            c = dict(x=x, y=y, lab='.', floor='sand', ground=h, peak=h, level=h, material=major[y, x], kind='floor')
            covered = model[y, x] * 2 > PX * PX or (deck[y, x] * 2 > PX * PX and t != 0x15)
            if void[y, x]:
                c.update(lab='T', peak=top, void=True, kind='blocked')
            elif t == 0x3B:
                c.update(lab='L', kind='ledge_south')
            elif t == 0x39:
                c.update(lab='Q', kind='ledge_west')
            elif t == 0x38:
                c.update(lab='R', kind='ledge_east')
            elif t == 0x11:
                # a whirlpool: Gen 3 has no Whirlpool; solid water under HGSS's own whirlpool
                c.update(floor='water', level=lake, ground=lake, peak=lake, kind='blocked', whirlpool=True)
            elif t == 0x15:
                c.update(floor='water', kind='blocked' if k & 0x80 else 'water')
            elif t == 0x16:
                c.update(kind='puddle', puddle=True)
            elif t in (0x4B, 0x4C):
                c.update(lab='T', climb=True, kind='climb')
            elif t == 0x6F:
                c.update(exit=True, kind='exit', dark=bool(dark[y, x] or (y > 0 and dark[y - 1, x])))
            elif t == 0x6E:
                # a hole into the wall: drawn as the wall it is set in, the door's dark arch on it
                c.update(exit=True, kind='hole', lab='T', hole=True)
            elif t in (0x3C, 0x3D, 0x3E):
                c.update(kind='ladder', piece={0x3D: 'ladder_top', 0x3C: 'ladder_up', 0x3E: 'ladder_down'}[t])
            elif covered or (x, y) in unbuilt:
                # under a kept model or on a deck (a shrine, its deck, a pier): water at the lake's level under
                # HGSS's own pixels; walkable where HGSS lets the player walk
                c.update(floor='water', level=lake, ground=lake, peak=lake, deck=True,
                         kind='blocked' if k & 0x80 or (x, y) in unbuilt else 'floor')
            elif k & 0x80:
                c['kind'] = 'blocked'
                if pile[y, x] >= 40:
                    # HGSS's rock pile (d_rock01, 2x2): a rock formation, one tier above its floor
                    c.update(lab='T', peak=float(foot[y, x]) + 1, formation=True)
                elif sea[y, x] > 0 or (cave.SEA_ROCKS and major[y, x] == WATER):
                    # a rock standing in the lake: the routes' boulder in its own tones, on water
                    c.update(boulder=True, moss=True, sea=True, floor='water', level=lake, ground=lake)
                elif small[y, x] >= 20 and major[y, x] not in (FACE, TOP, RIM):
                    # a small rock: the routes' boulder in its own tones, on the floor (or the water) under it
                    c.update(boulder=True, moss=True, floor='water' if major[y, x] == WATER else 'sand')
                else:
                    c.update(lab='T')
            elif major[y, x] == STAIRS:
                c.update(lab='s')
            elif t not in (0x08, 0x00):
                raise SystemExit(f'unhandled HGSS permission {side} {(x, y)} {t:#x}/{k:#x}')
            row.append(c)
        cells.append(row)
    # an up-ladder HGSS gives its foot alone (0x3C, the wall above it solid): Seafoam's top on that wall,
    # so the ladder is whole (owner review, Ice Path)
    for c in [c for row in cells for c in row if c.get('piece') == 'ladder_up']:
        x, y = c['x'], c['y']
        if y > 0 and cells[y - 1][x].get('piece') != 'ladder_top' and cells[y - 1][x]['kind'] == 'blocked':
            cells[y - 1][x]['piece'] = 'ladder_top'
            cells[y - 1][x]['ladder_wall'] = True
    for c in [c for row in cells for c in row if c.get('hole')]:
        # a hole's wall runs level with the wall beside it
        x, y = c['x'], c['y']
        base = [cells[y][x + dx]['peak'] for dx in (-2, 2) if 0 <= x + dx < W and cells[y][x + dx]['lab'] == 'T']
        if base:
            for dx in (-1, 0, 1):
                if 0 <= x + dx < W and cells[y][x + dx]['lab'] == 'T':
                    cells[y][x + dx]['peak'] = min(base)
        elif y > 0 and cells[y - 1][x]['lab'] == 'T':
            c['peak'] = cells[y - 1][x]['peak']
    # an exit's wall runs straight under it, shoulders and all, as Union Cave fits its doors
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
            if (c.get('boulder') and not c.get('sea')) or c['lab'] in 'LQR':
                near = [cells[c['y'] + dy][c['x'] + dx]['ground'] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                        if 0 <= c['x'] + dx < W and 0 <= c['y'] + dy < H and cells[c['y'] + dy][c['x'] + dx]['lab'] == '.']
                if near:
                    c['ground'] = min(near)
    return cells, hcls, major

# --------------------------------------------------------------------------- pieces
def piece_rgba(engine, primary, secondary, mid):
    b, t = D.metatile_layers(engine, primary, secondary, mid)
    a = b.copy(); m = t[..., 3] > 0; a[m] = t[m]
    return a

def ladders(engine, floor_tones, rock, wood):
    """Seafoam's ladders composed and recoloured colour for colour: wood to HGSS's ladder wood, Seafoam's
    snow cut away so the ladder stands on the cave floor, the rest to the floor tones; near black kept."""
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

def puddles(engine, floor_tones, rock):
    """Emerald's puddle nine-slice in cave water: its blues to the caves' water and its outline to the
    rock's dark tones, rank for rank; anything else to the floor's tones."""
    out = {}
    cols = set()
    raw = {k: piece_rgba(engine, 'general', 'petalburg', mid) for k, mid in PUDDLE.items()}
    for a in raw.values():
        cols |= {tuple(int(v) for v in p) for p in a[..., :3].reshape(-1, 3)}
    blue = [c for c in cols if c[2] > c[0] + 40]
    rest = [c for c in cols if c not in blue]
    cmap = dict(D.ranked(blue, CAVE_WATER))
    cmap.update(D.ranked(rest, [rock[0], rock[-1], rock[-2]]))
    for k, a in raw.items():
        out[k] = D.remap(a, cmap)[..., :3]
    return out

def flights(cells, W, H):
    """HGSS's stair cells (its `dslope`) as flights, each read from the floor at its ends: a flight whose
    floor north and south differ climbs north-south, one whose floor west and east differ climbs east-west.
    A run whose ends do not differ is floor (recorded). Returns Dark Cave's flight records, {cell: direction}
    and the runs read as floor."""
    from scipy import ndimage
    s = np.array([[c['lab'] == 's' for c in row] for row in cells])
    lab, n = ndimage.label(s)
    g = lambda x, y: cells[y][x]['ground'] if 0 <= x < W and 0 <= y < H and cells[y][x]['lab'] == '.' else None
    mean = lambda v: float(np.mean(v)) if v else None
    out, up, flat = [], {}, []
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
            for y, x in zip(ys, xs):
                cells[y][x]['lab'] = '.'
            flat.append([x0, y0, x1, y1])
            continue
        up.update({(int(x), int(y)): d for y, x in zip(ys, xs)})
    return out, up, flat

def stair_art(engine, rock):
    """Seafoam's stairs (Ice Path's flights) in the rock's tones, rank for rank, near black kept."""
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
    side = lambda p: p.T
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
    floor_t = tones(tex0, cave.FLOOR_TEX)
    # the second floor's own colour: its moss, not the dirt path drawn through the texture
    floor2_t = [c for c in tones(tex0, cave.FLOOR2['tex']) if c[1] > c[0] + 12] if cave.FLOOR2 else []
    rock_t = tones(tex0, *cave.ROCK_TEX)
    dec = {e.name: e for e in tex0.textures}
    A.FLOOR_TEX = R.decode(tex0, dec[cave.FLOOR_TEX], cave.FLOOR_TEX + '_pl')[..., :3]
    A.CAVE_RAMP = ramp(rock_t)
    A.POND = A.pond_pieces(engine)
    out_dir = SRC / 'assemble'; out_dir.mkdir(parents=True, exist_ok=True)
    (EV / 'assemble').mkdir(parents=True, exist_ok=True)
    tex = E.cherry_textures()
    tex['water'] = np.tile(A.POND[('M', 'M')][0], (2, 2, 1))
    pieces = E.frlg_pieces(engine)
    report = {}
    light = np.array(Image.open(UNION_DOOR).convert('RGBA'))
    lit = sorted({tuple(int(v) for v in p) for p in light[light[..., 3] > 0][:, :3]}, key=lum)
    hole = light.copy()
    for c, d_ in zip(lit, DARKS):
        hole[(light[..., :3] == c).all(-1) & (light[..., 3] > 0), :3] = d_
    for side in P.SIDES:
        W, H = P.HGSS_SIZE[side]
        A.W, A.H = E.W, E.H = W, H
        cells, hcls, major = ledger(side)
        ref = np.array(Image.open(SRC / f'hgss/{side}/hgss-render.png').convert('RGB'))
        m = np.load(SRC / f'hgss/{side}/hgss-ground-materials.npz')
        names = [str(v) for v in m['names']]
        mat = lambda *ns: np.isin(m['material'], [names.index(n) for n in ns if n in names])
        cellmask = lambda f: np.repeat(np.repeat(np.array([[bool(f(c)) for c in row] for row in cells]), PX, 0), PX, 1)
        # rocks in their own rendered tones; HGSS's ladder wood
        grey = lambda cs: [c for c in cs if max(c) - min(c) < 40 and lum(c) < 215]   # the rock itself, not water, moss or foam
        stones = sorted({tuple(int(v) for v in p) for p in ref[mat(*cave.SMALL_ROCKS)]}, key=lum)
        pebble = ramp(stones) if len(stones) > 6 else A.CAVE_RAMP
        sea_st = sorted(grey({tuple(int(v) for v in p) for p in ref[mat(*cave.SEA_ROCKS)]}), key=lum) if cave.SEA_ROCKS else []
        sea_ramp = ramp(sea_st) if len(sea_st) > 6 else pebble
        wood = sorted({tuple(int(v) for v in p) for p in ref[cellmask(lambda c: c['kind'] == 'ladder')] if int(p[0]) - int(p[2]) > 30},
                      key=lum) or [(140, 90, 50)]
        lad = ladders(engine, floor_t, A.CAVE_RAMP, wood)
        pud = puddles(engine, floor_t, A.CAVE_RAMP)
        A.WATER_TEX = np.array(CAVE_WATER, np.uint8).reshape(1, -1, 3)
        A.ROCK_BASE = int(np.floor(min(c['ground'] for row in cells for c in row if c['lab'] == '.') + 0.5))
        fl, climbs, flat = flights(cells, W, H)
        rc = A.rock_cells(cells, fl)
        d, face, isrock = A.terraces(rc)
        nubs = A.regularise(rc, d, isrock)
        d, face, isrock = A.terraces(rc)
        # a wall HGSS shows facing north never takes a south face (owner review, Mt. Mortar)
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
        back = A.south_faces(rc, d, isrock)
        drops = {(x, y) for x, y in back if d[y + 1, x] >= d[y, x]}
        bottom, over, _, piece = E.rock_frlg(rc, ground, pieces, tex, None, A.topped(rc, d, isrock), back - drops, ())
        for layer in (E.ledges_frlg(rc, pieces), east_ledges(rc, pieces, W, H)):
            a = layer[..., 3] > 0
            over[a] = layer[a]
        # east-west flights: the routes' side stairs (S04 descending west, S05 east), a step down each tier
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
        # a second floor texture (cave.FLOOR2): its cells take that texture's tones by rank
        if floor2_t:
            hg_floor = sorted({tuple(int(v) for v in c) for c in A.FLOOR_TEX.reshape(-1, 3)}, key=lum)
            second = D.ranked(hg_floor, floor2_t)
            n1 = per(*[n for n in names if n.startswith(cave.FLOOR_TEX)])
            n2 = per(*[n for n in names if n.startswith(cave.FLOOR2['prefixes'])])
            hall = np.repeat(np.repeat(n2 > n1, PX, 0), PX, 1) & ~rk
            for yy, xx in zip(*np.nonzero(hall)):
                c = tuple(int(v) for v in comp[yy, xx])
                if c in second:
                    comp[yy, xx] = second[c]
        shade = cmap.get(str(tuple(E.BORDER_GRAY))) or min(map(tuple, np.unique(A.FLOOR_TEX.reshape(-1, 3), axis=0).tolist()), key=lum)
        wet = lambda x, y: not (0 <= x < W and 0 <= y < H) or rc[y][x].get('puddle')
        for row in rc:
            for c in row:
                sl = np.s_[c['y'] * PX:(c['y'] + 1) * PX, c['x'] * PX:(c['x'] + 1) * PX]
                if c.get('moss'):
                    cell = comp[sl]
                    for (yy, xx), k in np.ndenumerate(pieces['boulder']):
                        if k >= 0:
                            cell[yy, xx] = (sea_ramp if c.get('sea') else pebble)[k]
                        elif k == E.SHADOW:
                            cell[yy, xx] = shade
                elif c.get('puddle'):
                    x, y = c['x'], c['y']
                    v = 'N' if not wet(x, y - 1) else 'S' if not wet(x, y + 1) else 'M'
                    h = 'W' if not wet(x - 1, y) else 'E' if not wet(x + 1, y) else 'M'
                    comp[sl] = pud[(v, h)]
                if c.get('piece') in lad:
                    img = lad[c['piece']]
                    mm = (img[..., 3] > 0) & (~rk[sl] | bool(c.get('ladder_wall')))
                    comp[sl][mm] = img[mm, :3]
        stairs = stair_art(engine, A.CAVE_RAMP)
        for (x, y), d_ in climbs.items():
            if d_ in ('north', 'south'):
                comp[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX] = stairs[d_]
        # Union Cave's door: its arch light on a lit exit, the same arch in darks on a hole or an exit into the dark
        ex = np.zeros((H * PX, W * PX), bool)
        for row in cells:
            for c in row:
                if c['kind'] not in ('exit', 'hole'):
                    continue
                spr = light if c['kind'] == 'exit' and not c.get('dark') else hole
                h_, w_ = spr.shape[:2]
                y0, x0 = c['y'] * PX + PX - h_, c['x'] * PX + (PX - w_) // 2
                sub = comp[y0:y0 + h_, x0:x0 + w_]
                mm = spr[..., 3] > 0
                sub[mm] = spr[mm, :3]
                ex[y0:y0 + h_, x0:x0 + w_] |= mm
        holds = mat('dr_climb')
        comp[holds] = ref[holds]
        # HGSS's own pixels where Gen 3 has no piece (cave.KEEP_MODELS, cave.KEEP_MATERIALS)
        owner = np.load(SRC / f'hgss/{side}/hgss-foreground-owner.npz')['owner']
        keep = np.isin(owner, kept_models(side)) | mat(*cave.KEEP_MATERIALS)
        comp[keep] = ref[keep]
        # each kept group in at most 15 colours of its own (one Gen 3 palette bank), so the cave round it packs exact
        meta = json.loads((SRC / f'hgss/{side}/hgss-render.json').read_text())
        groups = [np.isin(owner, [i for i in kept_models(side) if 'uzushio' in meta['buildings'][i]['names']])]
        groups.append(keep & ~groups[0])
        for gm in groups:
            if gm.any():
                px = Image.fromarray((comp[gm] >> 3 << 3).reshape(1, -1, 3).astype(np.uint8))
                q = px.quantize(colors=15, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert('RGB')
                comp[gm] = np.array(q).reshape(-1, 3)
        cls = np.full((H * PX, W * PX), FLOOR, np.int16)
        cls[rk] = FACE
        cls[cellmask(lambda c: c['floor'] == 'water') & ~rk] = WATER
        cls[holds] = FACE
        cls[cellmask(lambda c: (c['x'], c['y']) in climbs)] = STAIRS
        cls[top[..., 3] > 0] = STAIRS
        cls[ex] = EXIT
        cls[keep] = BOULDER
        Image.fromarray(comp).save(out_dir / f'{side}.png')
        np.save(out_dir / f'{side}-class.npy', cls.astype(np.int8))
        (out_dir / f'{side}-ledger.json').write_text(json.dumps(dict(offset=[0, 0], cells=[
            dict(x=c['x'], y=c['y'], kind=c['kind'], lab=c['lab'], floor=c['floor'], piece=c.get('piece'), void=bool(c.get('void')))
            for row in rc for c in row])) + '\n')
        (out_dir / f'{side}-terrace-grid.txt').write_text(
            f'# {cave.NAME} {side} (HGSS coordinates): one line per cell row. Ground and water: their terrace level (0-9); rock: a\n'
            f'# letter (A = level 0 ...); stairs s, ledges L/Q/R (south/west/east), boulders o, ladders H, puddles p, decks d,\n'
            f'# whirlpools @, void #. Decoded from HGSS land_data (cave_assemble.ledger).\n' +
            ''.join(f'{y:02d}  ' + ''.join(
                '#' if c.get('void') else 'H' if c['kind'] == 'ladder' else '@' if c.get('whirlpool') else 'p' if c.get('puddle')
                else 'd' if c.get('deck') else 's' if c['lab'] == 's' else c['lab'] if c['lab'] in 'LQR' else 'o' if c.get('boulder')
                else chr(65 + min(25, d[y, x])) if isrock[y, x] else str(min(9, d[y, x]))
                for x, c in enumerate(cells[y])) + '\n' for y in range(H)))
        both = Image.new('RGB', (W * 32 + 12, H * 16), (24, 26, 30))
        both.paste(Image.fromarray(ref), (0, 0)); both.paste(Image.fromarray(comp), (W * 16 + 12, 0))
        both.save(EV / f'assemble/{side}-before-after.png')
        report[side] = dict(flights=len(fl), stair_runs_read_as_floor=flat, rock_cells=int(isrock.sum()),
                            regularised={k: len(v) for k, v in nubs.items()}, kept_pixels=int(keep.sum()),
                            kinds=dict(Counter(c['kind'] for row in rc for c in row)))
        print(side, report[side])
    (EV / 'assemble/report.json').write_text(json.dumps(dict(cave_ramp=A.CAVE_RAMP, floor_tones=floor_t, floors=report), indent=1) + '\n')
    return report
