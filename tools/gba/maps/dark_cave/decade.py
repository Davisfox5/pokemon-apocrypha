"""Dark Cave ten years on: the changes laid over HGSS's mapped shapes (owner direction, November 2026).

Owner direction: make the cave read as ten years later, with bigger changes than the first mockups,
a new section dug farther into the rock for minerals, and a place in the lake to Dive down to an
underwater path and a new cave section (grotto.py, underwater.py). Use existing art from the games
in the repo wherever it exists; make no new tile art unless there is none.

Ledger edits (apply(), before any drawing, so the rock pieces draw every new wall as they draw
HGSS's own):

    mine    the Route 31 side: a drift south out of the west cavern into the solid rock, a main
            gallery, two stopes (ore west, quartz east), a crosscut, a lower gallery, a drift closed
            by a timber barricade and a loading room. Floor at the cavern's own height; the rock
            round it steps up one tier per cell (the min of its HGSS height and the mine's own
            rings), as HGSS's rings step round its halls.
    flood   the Route 45 side: the lake two cells higher over its lowest shore, never over the
            worn track, an exit or an HGSS event cell.
    deep    the Dive spot: a 3x3 patch of deep water in the lake (Emerald Cave's dive water,
            metatile 660, recoloured to the cave water).
    moss    HGSS's moss rock (d_rock01s) spread over damp floor near water and along walls,
            placed one at a time, each only where every cell stays reachable.
    rubble  rockfalls: FRLG Power Plant's debris pile (power_plant_frlg 693, top layer) in the
            cave rock ramp. One closes a corridor that has a way round; the rest are heaps at a
            wall's foot.
    props   camps and the mine's kit, each a blocked cell: Slateport's crates (822, 830, 831),
            Mauville's log stack (708) in the crates' wood, the route sign (route-46 shared P13),
            FRLG's boulder in ore and quartz tones.

After the colour swap (overlay()): props over the floor, the worn track (two floor tones lighter
along the way people walk, with the ground painter's wavy edge), and the Johto grade over the
whole image (DESIGN.md: shadows toward teal, light toward amber, midtones a little desaturated).

Not drawn: wall lamps (no Gen 3 tileset in the repo has a cave lamp; HGSS's lights are 3D
models) and rails (none exist in any tileset here). Both would be new tiles.
"""
from __future__ import annotations
import hashlib, heapq, struct
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image

ORTH = ((1, 0), (-1, 0), (0, 1), (0, -1))

# --------------------------------------------------------------------------- the plan
# The mine, Route 31 side, cells x 0-35, y 27-62. '.' floor, '#' rock, R rubble, B barricade,
# c/d/e crates, t log stack, O ore, Z quartz.
MINE_TOP = 27
MINE = [
    '##############..####################',  # 27  the drift leaves the west cavern at (14-15, 26)
    '##############..####################',  # 28
    '##############..####################',  # 29
    '##############..####################',  # 30
    '##############..####################',  # 31
    '##############..####################',  # 32
    '#####.....####..####.....###########',  # 33  alcoves over the gallery
    '###..........................R...###',  # 34  main gallery ...
    '###..........................R...###',  # 35  ... closed by a rockfall at its east end
    '#####..#########..######....########',  # 36
    '#####..#########..######....########',  # 37
    '###.......#####..######......#######',  # 38  west stope (ore), central drift, east stope (quartz)
    '##O........####..#####........######',  # 39
    '##..........###..####........Z.#####',  # 40
    '##...........##..###...........#####',  # 41
    '###............................#####',  # 42  crosscut through both stopes
    '###O........###..###..........Z#####',  # 43
    '####.......####..####.........######',  # 44
    '#####....O#####..#####......Z#######',  # 45
    '########..#####..######.....########',  # 46
    '########..#####..###################',  # 47
    '##...................###############',  # 48  lower gallery
    '##...................###############',  # 49
    '##..###############..###############',  # 50
    '##..###############..###############',  # 51
    '##..###############..###############',  # 52
    '##..##########...........t..########',  # 53  loading room
    '##..##########c.............########',  # 54
    '##..##########de...........t########',  # 55
    '##BB##########...........cd.########',  # 56  the west drift, barricaded
    '##############c.........e...########',  # 57
    '##############...........tt.########',  # 58
    '####################################',  # 59
    '####################################',  # 60
    '####################################',  # 61
    '####################################',  # 62
]
assert all(len(r) == 36 for r in MINE), [i for i, r in enumerate(MINE) if len(r) != 36]
MINE_FROM = (14, 26)                           # the west cavern cell the drift leaves from
MINE_PROPS = {'B': 'barricade', 'c': 'crate_a', 'd': 'crate_b', 'e': 'crate_c', 't': 'timber',
              'O': 'ore', 'Z': 'quartz'}

DIVE = {'route45-side': [(x, y) for y in range(31, 34) for x in range(37, 40)]}

FLOOD = {'route45-side': dict(box=(20, 26, 56, 46), steps=2)}

MOSS = {'route45-side': dict(box=(0, 0, 64, 64), near_water=0.3, at_wall=0.04),
        'route31-side': dict(box=(0, 0, 64, 30), near_water=0.3, at_wall=0.04)}

ROCKFALL = {  # a fallen block: HGSS's rock pile as the cave draws it (a formation one tier over its floor);
              # it closes a corridor that has a way round (check.py proves every exit and event cell is still reached)
    'route45-side': [(x, y) for y in (39, 40) for x in range(48, 52)],          # across the east shore path; the lake reaches past it
}
RUBBLE = {  # heaps of loose debris at a wall's foot
    'route45-side': [(30, 8), (31, 8)],
    'route31-side': [(33, 14), (33, 15)],
}

CAMPS = {
    'route45-side': [((41, 37), 'crate_a'), ((42, 37), 'crate_b'), ((41, 38), 'crate_c'), ((46, 37), 'timber'),
                     ((53, 2), 'crate_b'), ((54, 2), 'crate_a')],
    'route31-side': [((8, 5), 'crate_a'), ((9, 5), 'crate_b'), ((10, 5), 'timber')],
}
SIGNS = {  # cell: text (bg_event sign)
    'route31-side': {(13, 26): 'DARK CAVE MINE\nNo entry without a light.'},
}

EXITS = {'route45-side': [(60, 4), (6, 57)], 'route31-side': [(26, 4), (55, 56)]}
TRACKS = {'route45-side': [((60, 4), (6, 57))],
          'route31-side': [((26, 4), (55, 56)), ((26, 5), (15, 35))]}       # and from the hole into the mine

ORE = [(48, 24, 20), (214, 132, 82), (186, 104, 64), (156, 82, 50), (126, 64, 40), (100, 50, 34), (76, 38, 30)]
QUARTZ = [(28, 36, 70), (214, 238, 250), (172, 208, 242), (132, 170, 228), (102, 130, 204), (78, 96, 170), (54, 70, 132)]
DARKEN = 0.82                                    # props in cave light

def hsh(x, y, salt=0):
    return int(hashlib.md5(f'{x},{y},{salt}'.encode()).hexdigest()[:6], 16) / 0xFFFFFF

def events(src, side):
    import json
    d = json.loads((src / f'hgss-events/{side}.json').read_text())
    return {tuple(o['cell']) for o in d['objects']} | {tuple(h['cell']) for h in d['hidden_items']}

# --------------------------------------------------------------------------- ledger edits
def _walkable(c):
    return c['lab'] in '.s' and not c.get('boulder')

def _reach(cells, W, H, starts):
    """Cells reachable on foot or by Surf (ledges both ways: a conservative connectivity test)."""
    ok = lambda c: _walkable(c) or c['lab'] in 'LQ'
    seen, q = set(starts), deque(starts)
    while q:
        x, y = q.popleft()
        for dx, dy in ORTH:
            n = (x + dx, y + dy)
            if 0 <= n[0] < W and 0 <= n[1] < H and n not in seen and ok(cells[n[1]][n[0]]):
                seen.add(n); q.append(n)
    return seen

def walk(cells, W, H, a, b):
    """The way people walk between two cells (water costs more): the worn track."""
    ok = lambda c: c['lab'] in '.sLQ' and not c.get('boulder')
    dist, prev, q = {a: 0}, {}, [(0, a)]
    while q:
        d, (x, y) = heapq.heappop(q)
        if (x, y) == b:
            break
        for dx, dy in ORTH:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < W and 0 <= ny < H) or not ok(cells[ny][nx]):
                continue
            nd = d + (6 if cells[ny][nx]['floor'] == 'water' else 1)
            if nd < dist.get((nx, ny), 1e9):
                dist[(nx, ny)] = nd; prev[(nx, ny)] = (x, y); heapq.heappush(q, (nd, (nx, ny)))
    out, cur = [], b
    while cur in prev:
        out.append(cur); cur = prev[cur]
    return out + [a]

def apply(side, cells, src, W=64, H=64):
    """Edits the ledger in place; returns {kind: [[x, y], ...]}."""
    edits = {k: [] for k in ('mine', 'rings', 'flood', 'deep', 'moss', 'rockfall', 'rubble', 'props', 'signs')}
    inside = lambda x, y: 0 <= x < W and 0 <= y < H
    is_floor = lambda c: c['lab'] == '.' and c['floor'] == 'sand' and not c.get('boulder')
    keep = set(EXITS.get(side, [])) | events(src, side)
    if side == 'route31-side':
        g0 = cells[MINE_FROM[1]][MINE_FROM[0]]['ground']
        mine = {}
        for j, row in enumerate(MINE):
            for x, ch in enumerate(row):
                if ch != '#':
                    mine[(x, MINE_TOP + j)] = ch
        for (x, y), ch in mine.items():
            c = cells[y][x]
            for k in ('void', 'exit', 'formation', 'moss', 'rubble'):
                c.pop(k, None)
            c.update(lab='.', floor='sand', ground=g0, peak=g0, level=g0, boulder=False, mine=True)
            edits['mine'].append([x, y])
            if ch == 'R':                              # the gallery's rockfall
                c.update(lab='T', peak=g0 + 1, formation=True, rockfall=True)
                edits['rockfall'].append([x, y])
            elif ch in MINE_PROPS:
                c.update(boulder=True, prop=MINE_PROPS[ch])
                edits['props'].append([x, y, MINE_PROPS[ch]])
        # the rock round the mine steps up one tier a cell, as HGSS's rings do round its halls
        for y in range(H):
            for x in range(W):
                c = cells[y][x]
                if c['lab'] != 'T':
                    continue
                d = min((max(abs(x - mx), abs(y - my)) for mx, my in mine), default=99)
                if d <= 3:
                    c['ring'] = True                    # already regular: assemble.regularise leaves it
                    peak = g0 + d
                    if c.get('void') or peak < c['peak']:
                        c.pop('void', None)
                        c['peak'] = min(peak, c['peak']) if not c.get('void') else peak
                        edits['rings'].append([x, y])
    for x, y in ROCKFALL.get(side, []):
        assert is_floor(cells[y][x]) and (x, y) not in keep, (side, x, y)
        cells[y][x].update(lab='T', peak=cells[y][x]['ground'] + 1, formation=True, rockfall=True)
        edits['rockfall'].append([x, y])
    track = set()
    for a, b in TRACKS.get(side, []):
        track |= set(walk(cells, W, H, a, b))
    wet = lambda x, y: inside(x, y) and cells[y][x]['floor'] == 'water'
    if side in FLOOD:
        x0, y0, x1, y1 = FLOOD[side]['box']
        low = min(c['ground'] for row in cells for c in row if is_floor(c))
        for _ in range(FLOOD[side]['steps']):
            grow = [(x, y) for y in range(y0, y1) for x in range(x0, x1)
                    if is_floor(cells[y][x]) and (x, y) not in track and (x, y) not in keep
                    and abs(cells[y][x]['ground'] - low) < 1.6 and any(wet(x + dx, y + dy) for dx, dy in ORTH)]
            for x, y in grow:
                cells[y][x].update(floor='water', level=low - 0.5)
                edits['flood'].append([x, y])
        # no one-cell fingers: a new water cell with land on three sides goes back to floor, and a floor
        # cell the water has surrounded on three sides goes under (never the track, exits or event cells)
        for _ in range(4):
            moved = False
            for y in range(y0, y1):
                for x in range(x0, x1):
                    c = cells[y][x]
                    wet_n = sum(wet(x + dx, y + dy) for dx, dy in ORTH)
                    if [x, y] in edits['flood'] and wet_n <= 1:
                        c.update(floor='sand', level=c['ground']); edits['flood'].remove([x, y]); moved = True
                    elif (is_floor(c) and wet_n >= 3 and (x, y) not in track and (x, y) not in keep
                          and abs(c['ground'] - low) < 1.6):
                        c.update(floor='water', level=low - 0.5); edits['flood'].append([x, y]); moved = True
            if not moved:
                break
    for x, y in DIVE.get(side, []):
        assert cells[y][x]['floor'] == 'water' and cells[y][x]['lab'] == '.', (side, x, y)
        cells[y][x]['deep'] = True
        edits['deep'].append([x, y])
    starts = list(EXITS.get(side, []))
    base = _reach(cells, W, H, starts)

    def place(x, y, **kw):
        """Block a floor cell only if everything reachable stays reachable."""
        c = cells[y][x]
        old = dict(c)
        c.update(boulder=True, **kw)
        if _reach(cells, W, H, starts) != base - {(x, y)}:
            cells[y][x] = old
            return False
        base.discard((x, y))
        return True

    for x, y in RUBBLE.get(side, []):
        assert is_floor(cells[y][x]) and (x, y) not in keep, (side, x, y)
        cells[y][x].update(boulder=True, prop='rubble', rubble=True)
        edits['rubble'].append([x, y])
    base = _reach(cells, W, H, starts)
    for (x, y), name in CAMPS.get(side, []):
        assert is_floor(cells[y][x]) and (x, y) not in keep, (side, x, y, name)
        assert place(x, y, prop=name), (side, x, y, name)
        edits['props'].append([x, y, name])
    for (x, y), text in SIGNS.get(side, {}).items():
        assert is_floor(cells[y][x]) and (x, y) not in keep, (side, x, y)
        assert place(x, y, prop='sign', sign=text), (side, x, y)
        edits['signs'].append([x, y])
    if side in MOSS:
        cfg = MOSS[side]
        x0, y0, x1, y1 = cfg['box']
        clear = track | keep | {(x + dx, y + dy) for x, y in keep for dx, dy in ORTH}
        for y in range(y0, y1):
            for x in range(x0, x1):
                c = cells[y][x]
                if not is_floor(c) or c.get('exit') or c.get('mine') or (x, y) in clear:
                    continue
                if any(inside(x + dx, y + dy) and cells[y + dy][x + dx]['lab'] in 'sLQ' for dx, dy in ORTH):
                    continue                            # stairs and ledges keep their approaches
                if any(inside(x + dx, y + dy) and cells[y + dy][x + dx].get('boulder') for dx, dy in ORTH):
                    continue                            # loose, not in rows: no new moss rock beside another rock
                near_w = any(wet(x + dx, y + dy) for dx in (-2, -1, 0, 1, 2) for dy in (-2, -1, 0, 1, 2))
                at_wall = any(inside(x + dx, y + dy) and cells[y + dy][x + dx]['lab'] == 'T' for dx, dy in ORTH)
                if (near_w and hsh(x, y) < cfg['near_water']) or (at_wall and hsh(x, y, 7) < cfg['at_wall']):
                    if place(x, y, moss=True):
                        edits['moss'].append([x, y])
    edits['track'] = sorted([x, y] for x, y in track)
    return edits

# --------------------------------------------------------------------------- art from the repo's tilesets
def _pal(p):
    return np.array([tuple(map(int, l.split())) for l in p.read_text().replace('\r', '').splitlines()[3:19]], np.uint8)

def metatile_layers(engine, primary, secondary, mid):
    """(bottom, top) RGBA 16x16 of a metatile, as its tileset pair draws it."""
    nprim = 640 if primary.endswith('frlg') else 512
    npal = 7 if nprim == 640 else 6
    dirs = [engine / f'data/tilesets/primary/{primary}', engine / f'data/tilesets/secondary/{secondary}']
    tiles, metas = [], []
    for k, d in enumerate(dirs):
        a = np.array(Image.open(d / 'tiles.png')) & 15
        t = [a[y:y + 8, x:x + 8] for y in range(0, a.shape[0], 8) for x in range(0, a.shape[1], 8)]
        m = list(np.frombuffer((d / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8))
        if k == 0:
            t = t[:nprim] + [np.zeros((8, 8), np.uint8)] * (nprim - len(t[:nprim]))
            m = m[:nprim] + [np.zeros(8, np.uint16)] * (nprim - len(m[:nprim]))
        tiles += t; metas += m
    pals = [_pal((dirs[0] if b < npal else dirs[1]) / 'palettes' / f'{b:02}.pal') for b in range(16)]
    out = [np.zeros((16, 16, 4), np.uint8), np.zeros((16, 16, 4), np.uint8)]
    for i, e in enumerate(metas[mid]):
        e = int(e); t = tiles[e & 1023] if (e & 1023) < len(tiles) else np.zeros((8, 8), np.uint8)
        if e & 0x400: t = t[:, ::-1]
        if e & 0x800: t = t[::-1]
        q = i % 4
        sub = out[i // 4][(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
        m = t > 0
        sub[m, :3] = pals[e >> 12][t[m]]; sub[m, 3] = 255
    return out

def ranked(src, dst):
    lum = lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
    src = sorted(set(src), key=lum); dst = sorted(set(dst), key=lum)
    return {s: dst[min(len(dst) - 1, round(i * (len(dst) - 1) / max(1, len(src) - 1)))] for i, s in enumerate(src)}

def remap(a, cmap):
    out = a.copy()
    for (yy, xx) in zip(*np.nonzero(a[..., 3] > 0)):
        out[yy, xx, :3] = cmap[tuple(int(v) for v in a[yy, xx, :3])]
    return out

def colours(a):
    return [tuple(int(v) for v in c) for c in a[a[..., 3] > 0][:, :3]]

def darken(a, f=DARKEN):
    out = a.copy(); out[..., :3] = (a[..., :3] * f).astype(np.uint8)
    return out

def prop_art(engine, shared, boulder_ix, shadow, rock_ramp):
    """Every prop, RGBA 16x16 (the sign as the routes stage it)."""
    crate_a = metatile_layers(engine, 'general', 'slateport', 822)[1]
    wood = colours(crate_a)
    timber = metatile_layers(engine, 'general', 'mauville', 708)[1]
    timber = remap(timber, ranked(colours(timber), wood))               # the logs in the crates' wood
    rubble = metatile_layers(engine, 'building_frlg', 'power_plant_frlg', 693)[1]
    rubble = remap(rubble, ranked(colours(rubble), [tuple(c) for c in rock_ramp[1:]]))   # debris in the cave rock
    # the barricade: the log stack, turned so the logs lie across the drift
    barricade = np.rot90(timber).copy()

    def boulder(ramp):
        out = np.zeros((16, 16, 4), np.uint8)
        for (yy, xx), k in np.ndenumerate(boulder_ix):
            if k >= 0:
                out[yy, xx] = tuple(ramp[k]) + (255,)
            elif k == -2:                                                  # elements.SHADOW
                out[yy, xx] = tuple(shadow) + (255,)
        return out
    sign = np.array(Image.open(shared / 'P13.png').convert('RGBA'))
    return dict(crate_a=darken(crate_a), crate_b=darken(metatile_layers(engine, 'general', 'slateport', 830)[1]),
                crate_c=darken(metatile_layers(engine, 'general', 'slateport', 831)[1]), timber=darken(timber),
                barricade=darken(barricade), rubble=rubble, sign=darken(sign, 0.9), ore=boulder(ORE), quartz=boulder(QUARTZ))

def deep_water(engine, water_tones):
    """Emerald Cave's dive water (metatile 660) in the cave water's hue, each of its colours as
    bright, relative to the cave water, as it is relative to Emerald Cave's own water (368): the
    same step down Emerald draws between its pool and its dive spot."""
    lum = lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
    deep = metatile_layers(engine, 'general', 'cave', 660)[0]
    pool = metatile_layers(engine, 'general', 'cave', 368)[0]
    ref = np.mean([lum(c) for c in colours(pool)])
    base = np.mean(np.array(sorted(set(water_tones), key=lum), float), 0)
    cmap = {}
    for c in set(colours(deep)):
        v = np.clip(base * lum(c) / ref, 0, 255).astype(int)
        cmap[c] = tuple(int((k >> 3) << 3 | (k >> 5)) for k in v)
    return remap(deep, cmap)[..., :3]

# --------------------------------------------------------------------------- after the colour swap
WAVE16 = [0, 1, 1, 2, 2, 1, 1, 0, 0, -1, -1, -2, -2, -1, -1, 0]

def worn(img, cls_floor, cells, track, W, H, PX=16, floor_tones=()):
    """Two floor tones lighter along the track (the floor texture's own four tones), its edge on
    the ground painter's wave."""
    from collections import Counter
    floor = cls_floor
    tones = sorted((c for c, _ in Counter(map(tuple, img[floor].reshape(-1, 3).tolist())).most_common(4)), key=sum)
    up = {t: tones[min(len(tones) - 1, i + 2)] for i, t in enumerate(tones)}
    on = np.zeros((H, W), bool)
    for x, y in track:
        c = cells[y][x]
        if c['lab'] == '.' and c['floor'] == 'sand' and not c.get('boulder'):
            on[y, x] = True
    ys, xs = np.mgrid[0:H * PX, 0:W * PX]
    wave = np.array(WAVE16)
    sx = np.clip(xs + wave[ys % 16] * 2, 0, W * PX - 1) // PX
    sy = np.clip(ys + wave[(xs + 5) % 16] * 2, 0, H * PX - 1) // PX
    m = on[sy, sx] & floor
    out = img.copy()
    keys = {t: np.all(img == t, -1) for t in up}
    for t, k in keys.items():
        out[k & m] = up[t]
    return out

def paste(img, art, cx, cy, PX=16):
    h, w = art.shape[:2]
    y0, x0 = cy * PX + PX - h, cx * PX + (PX - w) // 2
    sub = img[y0:y0 + h, x0:x0 + w]
    m = art[..., 3] > 0
    sub[m] = art[m, :3]

def grade(img):
    """DESIGN.md's Johto grade: shadows toward teal, highlights toward amber, midtones a little
    desaturated; then back to GBA RGB555 steps."""
    f = img.astype(float) / 255
    L = (0.299 * f[..., 0] + 0.587 * f[..., 1] + 0.114 * f[..., 2])[..., None]
    f = L + (f - L) * 0.85
    ws = np.clip((0.55 - L) / 0.55, 0, 1); wh = np.clip((L - 0.45) / 0.55, 0, 1)
    f = f + ws * np.array([-0.06, 0.03, 0.07]) + wh * np.array([0.10, 0.05, -0.07])
    out = (np.clip(f, 0, 1) * 255).astype(int)
    return ((out >> 3) << 3 | (out >> 5)).astype(np.uint8)
