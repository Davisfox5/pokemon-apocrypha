"""Blackthorn as Gen 3 elements: ledger, terrain composer and two rock styles.

    python3 tools/gba/maps/blackthorn/elements.py ENGINE_CHECKOUT PHG_CHECKOUT

Rebuilds Blackthorn from reusable elements instead of the 1:1 HGSS render. Every cell
gets a material and structure label from HGSS geometry (top-down height map, slopes and
permissions). The cell's terrace level is the top of its HGSS layer, so cliffs become
Gen 3 terraces: each face cell is one metatile-sized layer, drawn from its
lower-neighbour mask (band toward a lower south, side strip toward a lower east or west,
back rim toward a lower north, corners where two meet). Three rock styles share it:

    A  HGSS's own pieces: rock top, face band and side cell, one layer per metatile
    B  Emerald's General rock pieces recoloured to Blackthorn's HGSS ramp
    C  FRLG's General mountain set (nine-slice plus inner corners, the Gen 3 counterpart
       of HGSS's Kanto/Johto rock) recoloured to Blackthorn's HGSS ramp, composed per
       8x8 quadrant so any terrace outline gets matching corners; its cast shadow
       darkens the ground it falls on, and its cave mouth is FRLG's

Ground reuses the accepted Cherrygrove vocabulary (grass, sand, water, grass border) and
Route 30's pond rim, carrying the lake's own water; styles A and B use Route 31's jump
ledge, style C FRLG's, joined into the cliffs it meets. Bridge, stairs, cave mouths and boulders are
element pieces drawn here. Output is a bottom layer (opaque), a top layer (RGBA,
drawn above the player) and per-cell element labels for the packer:

    source/elements/ledger.json, ledger.png, compose-{A,B,C}.npz
    evidence/elements/terrain-{A,B,C}.png, rock-compare.png, rock-detail.png
"""
from __future__ import annotations
import json, sys
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/blackthorn-city'
SRC, EV = ART / 'source', ART / 'evidence'
W = H = 64
ROCK = set('TESWN')
GYM_ISLAND = (25, 18, 32, 24)          # x0, y0, x1, y1 cells under the Gym
FLOOR_HEIGHT = 7                     # HGSS height of the walkable town floor
DIRS = dict(n=(0, -1), ne=(1, -1), e=(1, 0), se=(1, 1), s=(0, 1), sw=(-1, 1), w=(-1, 0), nw=(-1, -1))
ROCK_MATERIALS = ('cliff01gs', 'allpeakgs', 'allpeak_pgs', 'wall01_d', 'wall01_g', 'wall01_h')

# --------------------------------------------------------------------------- ledger
def topdown(phg):
    """Flat top-down HGSS terrain: per-pixel height, material and colour."""
    sys.path.insert(0, str(HERE))
    import hgss_render as R
    land, tex0, models, chunks, meta = R.load(phg)
    cv = R.Canvas(W * 16, H * 16)
    for c in chunks:
        ch = R.hgss_map.MapChunk.parse(land[c['land']])
        ox, oz = c['cx'] * 32, c['cz'] * 32
        R.draw_model(cv, R.mdlview.Model(ch.model), tex0, lambda x, y, z, ox=ox, oz=oz: (x + 16 + ox, y, z + 16 + oz), -1, None, flat=True)
    h = np.nan_to_num(cv.height, nan=float(np.nanmin(cv.height)))
    return h, cv.mat, list(R.MATERIAL_NAMES), cv.rgb.astype(np.uint8)

def ledger(phg):
    h, mat, names, rgb = topdown(phg)
    perm = np.load(SRC / 'hgss/hgss-permissions.npz')
    types, coll = perm['types'], perm['collision']
    gy, gx = np.gradient(h)
    slope = np.hypot(gx, gy) > 0.05
    share = slope.reshape(H, 16, W, 16).mean(axis=(1, 3))
    ddx = -(gx * slope).reshape(H, 16, W, 16).sum(axis=(1, 3))
    ddy = -(gy * slope).reshape(H, 16, W, 16).sum(axis=(1, 3))
    level = np.median(h.reshape(H, 16, W, 16), axis=(1, 3))
    peak = h.reshape(H, 16, W, 16).max(axis=(1, 3))
    nm = np.array(names + ['none'])
    m = np.where(mat >= 0, mat, len(names)).reshape(H, 16, W, 16).transpose(0, 2, 1, 3).reshape(H, W, 256)
    blds = json.loads((SRC / 'hgss/hgss-render.json').read_text())['buildings']
    owner = np.full((H, W), -1, int)
    for i, b in enumerate(blds):
        x0, z0, x1, z1 = b['footprint']
        owner[int(np.floor(z0)):int(np.ceil(z1)), int(np.floor(x0)):int(np.ceil(x1))] = i
    cells = []
    for y in range(H):
        row = []
        for x in range(W):
            u, cnt = np.unique(nm[m[y, x]], return_counts=True)
            dominant = str(u[np.argmax(cnt)])
            frac = {str(k): int(v) for k, v in zip(u, cnt)}
            blocked = bool(coll[y, x] & 0x80)
            t = int(types[y, x])
            water = t in (0x10, 0x15)
            if water:
                lab = '~'
            elif share[y, x] > 0.25 and blocked:
                a = np.degrees(np.arctan2(ddy[y, x], ddx[y, x])) % 360
                lab = 'ESWN'[int(((a + 45) % 360) // 90)]
            elif t == 0x3B:
                lab = 'L'
            elif blocked and (level[y, x] >= 9.5 or dominant in ROCK_MATERIALS):
                lab = 'T'
            elif blocked:
                lab = 'X'
            else:
                lab = '.'
            grass = sum(v for k, v in frac.items() if k.startswith('grass') or k == 'flower03')
            sand = sum(v for k, v in frac.items() if k.startswith('road'))
            floor = 'water' if water else 'bridge' if dominant == 'bridge_a' else 'stairs' if dominant == 'slope' else \
                    'grass' if grass > sand else 'sand'
            row.append(dict(lab=lab, floor=floor, level=round(float(level[y, x]), 2), peak=round(float(peak[y, x]), 2),
                            type=t, blocked=blocked, owner=int(owner[y, x]), material=dominant,
                            flowers=frac.get('flower03', 0) > 40, grass_px=int(grass), sand_px=int(sand)))
        cells.append(row)
    # Boulders (HGSS rock01): 2x2 props, the material marks their lower row.
    for y in range(H):
        for x in range(W):
            if cells[y][x]['material'] == 'rock01' and cells[y][x]['lab'] != 'O':
                x0 = x if x + 1 < W and cells[y][x + 1]['material'] == 'rock01' else x - 1
                for yy in (y - 1, y):
                    for xx in (x0, x0 + 1):
                        cells[yy][xx].update(lab='O', boulder=[x0, y - 1], floor='sand' if cells[y + 1][xx]['floor'] != 'grass' else 'grass')
    # A boulder sitting on the plateau is part of the rock top; only its sprite is drawn.
    seen = set()
    for y in range(H):
        for x in range(W):
            b = cells[y][x].get('boulder')
            if b and tuple(b) not in seen:
                seen.add(tuple(b))
                ring = [cells[yy][xx]['lab'] for yy in range(b[1] - 1, b[1] + 3) for xx in range(b[0] - 1, b[0] + 3)
                        if 0 <= yy < H and 0 <= xx < W and not (b[1] <= yy < b[1] + 2 and b[0] <= xx < b[0] + 2)]
                if sum(l in ROCK for l in ring) > len(ring) / 2:
                    for yy in (b[1], b[1] + 1):
                        for xx in (b[0], b[0] + 1):
                            cells[yy][xx]['lab'] = 'T'
    # The Gym's roof stands over the pond; only its hall's foot rests on the grass island,
    # which stays inside the hall's outline so the shoreline runs straight up to the
    # Gym on both sides instead of stepping round a sliver of island.
    x0, y0, x1, y1 = GYM_ISLAND
    for y in range(y0, y1):
        for x in range(x0, x1):
            cells[y][x]['floor'] = 'grass' if y == y1 - 1 or (y == y1 - 2 and x0 < x < x1 - 1) else 'water'
            if cells[y][x]['lab'] in ROCK:                    # the Gym's own slopes, not terrain
                cells[y][x]['lab'] = 'X'
    # Rock-labelled slivers beside the bridge deck over water are the railing's end posts.
    bx = sorted({x for y in range(H) for x in range(W) if cells[y][x]['floor'] == 'bridge'})
    for y in range(H - 1):
        for rx in (bx[0] - 1, bx[-1] + 1):
            if cells[y][bx[0]]['floor'] == 'bridge' and cells[y][rx]['lab'] in ROCK and cells[y + 1][rx]['lab'] == 'X':
                cells[y][rx]['lab'] = 'X'
    for y, x in ((y, x) for y in range(H) for x in range(W)):
        c = cells[y][x]
        if c['material'] in ('cavehole', 'icehole') and c['lab'] == '.':
            c['cave'] = 'dragons_den' if c['material'] == 'cavehole' else 'ice_path'
            if c['material'] == 'icehole':
                c['floor'] = 'grass'                          # Ice Path's frost lies on the grass
    return cells

def save_ledger(cells):
    out = SRC / 'elements'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'ledger.json').write_text(json.dumps(dict(
        note='Per-cell element ledger derived from HGSS land_data. lab: T rock top, E/S/W/N rock face by downhill '
             'direction, L jump ledge, O boulder, X other blocked (buildings, props), ~ water, . open. '
             'floor: ground under open cells. peak: HGSS cell maximum height (terrace level = peak - 7).',
        cells=[[c['lab'] + c['floor'][0] for c in row] for row in cells],
        detail=cells)) + '\n')
    img = Image.new('RGB', (W * 12, H * 12), (20, 20, 24)); d = ImageDraw.Draw(img)
    col = dict(T=(150, 110, 80), E=(200, 120, 60), W=(200, 160, 60), S=(220, 80, 60), N=(120, 90, 160), L=(240, 220, 120),
               X=(90, 90, 90), O=(120, 80, 60))
    for y in range(H):
        for x in range(W):
            c = cells[y][x]
            fill = col.get(c['lab']) or dict(water=(60, 120, 230), grass=(110, 210, 160), sand=(230, 200, 140),
                                               bridge=(150, 110, 70), stairs=(170, 140, 90))[c['floor']]
            d.rectangle((x * 12, y * 12, x * 12 + 11, y * 12 + 11), fill=fill)
            if c['lab'] in 'ESWNLO':
                d.text((x * 12 + 3, y * 12), c['lab'], fill='black')
    img.save(out / 'ledger.png')

# --------------------------------------------------------------------------- source art
def hgss_texture(phg, name, pal):
    sys.path.insert(0, str(HERE))
    import hgss_render as R
    _, tex0, _, _, _ = R.load(phg)
    e = next(t for t in tex0.textures if t.name == name)
    return R.decode(tex0, e, pal)

# Blackthorn's HGSS rock ramp: outline, then light to dark.
BLACKTHORN_RAMP = [(82, 58, 52), (239, 189, 140), (222, 173, 123), (198, 148, 115), (165, 115, 99), (132, 90, 74), (99, 70, 66)]

def _read_pal(p):
    v = list(map(int, p.read_text().split()[3:51]))
    return [tuple(c & 0xF8 for c in v[i * 3:i * 3 + 3]) for i in range(16)]

def _tiles(d):
    a = np.array(Image.open(d / 'tiles.png')) & 15
    return [a[y:y + 8, x:x + 8] for y in range(0, a.shape[0], 8) for x in range(0, a.shape[1], 8)]

def emerald_pieces(engine):
    """Emerald General rock pieces (bank 3 ramp 8-14, outline 5) recoloured to Blackthorn's ramp."""
    d = engine / 'data/tilesets/primary/general'
    tiles, pal = _tiles(d), _read_pal(d / 'palettes/03.pal')
    blocks = np.frombuffer((d / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
    remap = {pal[i]: BLACKTHORN_RAMP[k] for k, i in enumerate((8, 9, 10, 11, 12, 13, 14))}
    remap[pal[5]] = BLACKTHORN_RAMP[0]
    def piece(i):
        m = np.zeros((16, 16, 3), np.uint8)
        for q in range(4):
            e = int(blocks[i][4 + q]) if int(blocks[i][4 + q]) & 1023 else int(blocks[i][q])
            t = tiles[e & 1023]
            if e & 0x400: t = t[:, ::-1]
            if e & 0x800: t = t[::-1]
            m[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8] = np.array(
                [remap.get(pal[v], pal[v]) for v in t.ravel()], np.uint8).reshape(8, 8, 3)
        return m
    return dict(top=piece(0x071), face=piece(0x0A9), front=piece(0x07C), side=piece(0x073))

def rock_swatches(style, engine, phg):
    if style == 'C':
        return frlg_pieces(engine)
    if style == 'A':
        r = np.array(Image.open(SRC / 'hgss/hgss-render.png').convert('RGB'))
        return dict(top=hgss_texture(phg, 'cliff01gs', 'cliff01')[:, :, :3],
                    band=r[853:869, 30 * 16:30 * 16 + 32], foot=r[885:893, 30 * 16:30 * 16 + 32],
                    side=r[32 * 16:34 * 16, 11 * 16:12 * 16])
    t = emerald_pieces(engine)
    band = np.concatenate([t['front'], t['front']], 1)
    return dict(top=np.tile(t['top'], (2, 2, 1)), band=band, foot=band[8:16], side=np.concatenate([t['side'], t['side']], 0))

# Cherrygrove ground (accepted Johto vocabulary), learned from its decoded native map.
CHERRY = dict(grass=[(104, 208, 152), (88, 176, 136), (128, 136, 120), (104, 200, 152), (96, 192, 144)],
              sand=[(224, 200, 128), (216, 184, 128), (184, 168, 128)],
              water=[(24, 96, 216), (32, 120, 224), (40, 136, 224), (24, 104, 224), (56, 176, 224), (64, 192, 224)])
BORDER_GRAY, BORDER_GREEN, DASH, DASH_GAP = (128, 136, 120), (88, 176, 136), (184, 168, 128), (216, 184, 128)

def cherry_textures():
    """Cherrygrove's canonical 32x32 grass, sand and water blocks (its 32 px grid)."""
    img = np.array(Image.open(SRC / 'elements/cherrygrove-native.png').convert('RGB'))
    a = img.reshape(img.shape[0] // 8, 8, img.shape[1] // 8, 8, 3).transpose(0, 2, 1, 3, 4).reshape(img.shape[0] // 8, img.shape[1] // 8, 64, 3)
    out = {}
    for name, cols in CHERRY.items():
        hit = sum((a == np.array(c)).all(-1).sum(-1) for c in cols) >= (64 if name == 'water' else 40)
        blocks = {}
        for y in range(0, img.shape[0] - 31, 32):
            for x in range(0, img.shape[1] - 31, 32):
                ky, kx = y // 8, x // 8
                if hit[max(0, ky - 1):ky + 5, max(0, kx - 1):kx + 5].all():
                    b = img[y:y + 32, x:x + 32].tobytes(); blocks[b] = blocks.get(b, 0) + 1
        out[name] = np.frombuffer(max(blocks, key=blocks.get), np.uint8).reshape(32, 32, 3)
    return out

def route31_ledge(engine):
    """Route 31's accepted jump ledge (top layer, two 8x8 tiles), recoloured to Blackthorn's rock."""
    d = engine / 'data/tilesets/secondary/route31'
    tiles, pal = _tiles(d), _read_pal(d / 'palettes/08.pal')
    strip = np.concatenate([tiles[0x38d - 0x200], tiles[0x38e - 0x200]], 1)
    used = sorted(set(strip.ravel()) - {0}, key=lambda i: -sum(pal[i]))
    ramp = BLACKTHORN_RAMP[1:] + [BLACKTHORN_RAMP[0]]
    remap = {i: ramp[min(len(ramp) - 1, round(k * (len(ramp) - 1) / max(1, len(used) - 1)))] for k, i in enumerate(used)}
    rgba = np.zeros((8, 16, 4), np.uint8)
    for (yy, xx), v in np.ndenumerate(strip):
        if v:
            rgba[yy, xx] = remap[v] + (255,)
    return rgba

# --------------------------------------------------------------------------- distance helpers
def _dist(mask, steps=8):
    """4-connected (L1) distance from each True pixel to the nearest False pixel, capped."""
    d = np.where(mask, steps + 1, 0)
    cur = mask.copy()
    for i in range(1, steps + 1):
        pad = np.pad(cur, 1, mode='edge')
        inner = pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:]
        d[cur & ~inner] = np.minimum(d[cur & ~inner], i)
        cur = cur & inner
    return d

def _axis_dist(mask):
    def run(m):
        out = np.full(m.shape, 99)
        for flip in (False, True):
            a = m[::-1] if flip else m
            r = np.zeros(a.shape, int); acc = np.full(a.shape[1], 99)
            for i in range(a.shape[0]):
                acc = np.where(a[i], acc + 1, 0); r[i] = acc
            out = np.minimum(out, r[::-1] if flip else r)
        return out
    return run(mask), run(mask.T).T

def _components(mask):
    seen = np.zeros_like(mask)
    for y0, x0 in zip(*np.nonzero(mask)):
        if seen[y0, x0]:
            continue
        comp, q = [], deque([(y0, x0)]); seen[y0, x0] = True
        while q:
            y, x = q.popleft(); comp.append((y, x))
            for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= yy < mask.shape[0] and 0 <= xx < mask.shape[1] and mask[yy, xx] and not seen[yy, xx]:
                    seen[yy, xx] = True; q.append((yy, xx))
        yield comp

# --------------------------------------------------------------------------- ground
NB8 = [(-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0)]
GRASS_C, SAND_C, WATER_C = 1, 2, 3

def _classes8(img):
    a = img.reshape(img.shape[0] // 8, 8, img.shape[1] // 8, 8, 3).transpose(0, 2, 1, 3, 4).reshape(img.shape[0] // 8, img.shape[1] // 8, 64, 3)
    count = lambda cols: sum((a == np.array(c)).all(-1).sum(-1) for c in cols)
    g, s, w = count(CHERRY['grass']), count(CHERRY['sand']), count(CHERRY['water'])
    return np.where(w >= 40, WATER_C, np.where(g >= 40, GRASS_C, np.where(s >= 40, SAND_C, 0)))

def _key(k, ty, tx):
    """Own class plus the class of each of the eight neighbours; anything that is not
    ground (rock, buildings) counts as the tile's own class, so no rim is drawn there."""
    me = int(k[ty, tx])
    out = [me]
    for dx, dy in NB8:
        yy, xx = ty + dy, tx + dx
        v = int(k[yy, xx]) if 0 <= yy < k.shape[0] and 0 <= xx < k.shape[1] else 0
        out.append(v if v else me)
    return tuple(out)

def learn_ground(in_primary=None):
    """Cherrygrove's own ground tiles by neighbour configuration, with their texture phase;
    only tiles that exist in CherrygrovePrimary are kept when that check is given."""
    img = np.array(Image.open(SRC / 'elements/cherrygrove-native.png').convert('RGB'))
    k = _classes8(img)
    lib = {}
    for ty in range(1, k.shape[0] - 1):
        for tx in range(1, k.shape[1] - 1):
            if k[ty, tx] == 0:
                continue
            t = img[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            if in_primary is not None and not in_primary(t):
                continue
            lib.setdefault(_key(k, ty, tx), {}).setdefault((tx % 4, ty % 4), []).append(t.tobytes())
    return lib

def learn_pond_rim():
    """Route 30's accepted pond rim (grey lip, rounded corners) for every grass-water
    configuration, learned the way ground() reads Blackthorn: one class per cell."""
    img = np.array(Image.open(SRC / 'elements/route30-native.png').convert('RGB'))
    a = img.reshape(img.shape[0] // 16, 16, img.shape[1] // 16, 16, 3).transpose(0, 2, 1, 3, 4).reshape(img.shape[0] // 16, img.shape[1] // 16, 256, 3)
    count = lambda cols: sum((a == np.array(c)).all(-1).sum(-1) for c in cols)
    k = np.where(count(CHERRY['water']) >= 128, WATER_C, np.where(count(CHERRY['grass']) >= 128, GRASS_C, 0)).repeat(2, 0).repeat(2, 1)
    lib = {}
    for ty in range(1, k.shape[0] - 1):
        for tx in range(1, k.shape[1] - 1):
            key = _key(k, ty, tx)
            if k[ty, tx] and WATER_C in key and GRASS_C in key:
                lib.setdefault(key, {}).setdefault((tx % 4, ty % 4), []).append(img[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].tobytes())
    # Route 30's pond has trees along its north side, so it never shows grass north of water.
    # Its mirror images fill the configurations it lacks (ground() repaints the water).
    for fy, fx in ((True, False), (False, True), (True, True)):
        for key, by_phase in list(lib.items()):
            nk = _flip_key(key, fy, fx)
            if nk in lib:
                continue
            flip = lambda b: np.frombuffer(b, np.uint8).reshape(8, 8, 3)[::-1 if fy else 1, ::-1 if fx else 1].tobytes()
            lib[nk] = {((3 - px) if fx else px, (3 - py) if fy else py): [flip(b) for b in v] for (px, py), v in by_phase.items()}
    return lib

def _flip_key(key, fy, fx):
    """A neighbour key (own class, then NB8 order) as seen in a mirrored tile."""
    out = [key[0]]
    for dx, dy in NB8:
        out.append(key[1 + NB8.index((-dx if fx else dx, -dy if fy else dy))])
    return tuple(out)

def rock_beyond(cells):
    """For every 8x8 quadrant of a rock cell, the ground class its clear pixels show in
    style C (rock_frlg's rule: what lies past its lower vertical edge, else its lower
    side, else its lower diagonal), or 0 for rock, bridge, stairs or no lower edge."""
    d, _, isrock = layers(cells)
    lab = np.array([[c['lab'] for c in row] for row in cells])
    floor = np.array([[c['floor'] for c in row] for row in cells])
    cls = np.where(((lab == '~') & (floor != 'bridge')) | ((lab == 'X') & (floor == 'water')), WATER_C,
                   np.where(floor == 'grass', GRASS_C, SAND_C))
    cls[isrock | np.isin(floor, ['bridge', 'stairs'])] = 0
    out = np.zeros((H * 2, W * 2), int)
    lvl = lambda x, y: d[min(max(y, 0), H - 1), min(max(x, 0), W - 1)]
    for y, x in zip(*np.nonzero(isrock)):
        lo = {k: lvl(x + dx, y + dy) < d[y, x] for k, (dx, dy) in DIRS.items()}
        for qy in (0, 1):
            for qx in (0, 1):
                vk, hk = 'ns'[qy], 'we'[qx]
                t = next((DIRS[k] for k in (vk, hk, vk + hk) if lo[k]), None)
                if t:
                    cx, cy = min(max(x + t[0], 0), W - 1), min(max(y + t[1], 0), H - 1)
                    out[y * 2 + qy, x * 2 + qx] = cls[cy, cx]
    return out

def ground(cells, tex, shore=False):
    """Cherrygrove ground: its own tiles for every neighbour configuration it has
    (preferring the one at the same 32 px texture phase), drawn only where it has none.
    With shore, a rock quadrant whose clear pixels show grass or water beside the other
    (rock_beyond) takes part in the pond rim, so a shoreline runs on under a cliff's edge
    instead of stopping at it; ground.shore marks those quadrants for rock_frlg."""
    lab = np.array([[c['lab'] for c in row] for row in cells])
    floor = np.array([[c['floor'] for c in row] for row in cells])
    g = (floor == 'grass')
    for comp in _components(g.copy()):
        if len(comp) < 2:
            for y, x in comp: g[y, x] = False
    water = ((lab == '~') & (floor != 'bridge')) | ((lab == 'X') & (floor == 'water'))
    ground_cell = ~np.isin(lab, list(ROCK) + ['O']) & ~((lab == 'X') & ~np.isin(floor, ['grass', 'sand', 'water']))
    k = np.where(water, WATER_C, np.where(~ground_cell, 0, np.where(g, GRASS_C, SAND_C))).repeat(2, 0).repeat(2, 1)
    ground.shore = np.zeros(k.shape, bool)
    if shore:
        rb = rock_beyond(cells)
        pad = np.pad(k, 1)
        near = lambda c: (pad[:-2, 1:-1] == c) | (pad[2:, 1:-1] == c) | (pad[1:-1, :-2] == c) | (pad[1:-1, 2:] == c)
        ground.shore = (k == 0) & (((rb == GRASS_C) & near(WATER_C)) | ((rb == WATER_C) & near(GRASS_C)))
        k[ground.shore] = rb[ground.shore]
    lib = learn_ground(ground.in_primary)
    lib.update(learn_pond_rim())
    ys, xs = np.mgrid[0:H * 16, 0:W * 16]
    out = np.where(g.repeat(16, 0).repeat(16, 1)[..., None], tex['grass'][ys % 32, xs % 32], tex['sand'][ys % 32, xs % 32]).astype(np.uint8)
    wat = water.repeat(16, 0).repeat(16, 1)
    out[wat] = tex['water'][ys % 32, xs % 32][wat]
    missing = {}
    def lookup(key, ph):
        cand = lib.get(key)
        if cand is None:
            # a dry configuration never borrows a pond rim tile (its grey lip reads as a shore)
            same = ([q for q in lib if q[0] == key[0] and (WATER_C in q) == (WATER_C in key)]
                    or [q for q in lib if q[0] == key[0]])
            wgt = [1, 3, 1, 3, 1, 3, 1, 3]
            q = min(same, key=lambda q: sum(wv * (a != b) for wv, a, b in zip(wgt, q[1:], key[1:])))
            cand = lib[q]; missing[key] = missing.get(key, 0) + 1
        tiles = cand.get(ph) or max(cand.values(), key=len)
        best = max(sorted(set(tiles)), key=tiles.count)              # sorted: ties break the same way every run
        return np.frombuffer(best, np.uint8).reshape(8, 8, 3)
    rank = lambda t: np.select([(t[..., None, :] == np.array(CHERRY['water'], np.uint8)).all(-1).any(-1),
                                (t == BORDER_GRAY).all(-1), (t == BORDER_GREEN).all(-1)], [0, 1, 2], 3)
    SIDES = {1: (0, 2), 3: (2, 4), 5: (4, 6), 7: (6, 0)}          # N, E, S, W and their diagonals in NB8 order
    for ty in range(H * 2):
        for tx in range(W * 2):
            if k[ty, tx] == 0:
                continue
            key = _key(k, ty, tx)
            nb = key[1:]
            ph = (tx % 4, ty % 4)
            if key[0] == WATER_C and not any(nb[a] == GRASS_C and nb[b] == GRASS_C for a, b in ((1, 3), (3, 5), (5, 7), (7, 1))):
                continue    # open water or a straight shore: the lip is on the grass side, so this stays the lake
            if key[0] == GRASS_C and WATER_C in nb and key not in lib:
                # A grass corner Route 30 never shows: the straight edge for each side that meets
                # water (and the corner piece for a lone wet diagonal), lip pixels over grass.
                parts = [{s, *SIDES[s]} for s in SIDES if nb[s] == WATER_C]
                parts += [{d} for d in (0, 2, 4, 6) if nb[d] == WATER_C and not any(d in p for p in parts)]
                tiles = [lookup((key[0],) + tuple(v if (i in p or v != WATER_C) else GRASS_C for i, v in enumerate(nb)), ph) for p in parts]
                r = np.stack([rank(t) for t in tiles])
                pick = r.argmin(0)
                t = np.take_along_axis(np.stack(tiles), pick[None, ..., None].repeat(3, -1), 0)[0]
                missing[key] = missing.get(key, 0) + 1
            else:
                t = lookup(key, ph)
            out[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8] = t
    # Learned rim tiles bring the water of the map they came from, at that map's phase (or
    # one tile repeated where the phase is missing). Keep their lip and grass, and give every
    # water pixel the lake's own texture at its 32 px phase, so a shore reads as the same lake.
    wet = (out[..., None, :] == np.array(CHERRY['water'], np.uint8)).all(-1).any(-1)
    out[wet] = tex['water'][ys % 32, xs % 32][wet]
    ground.missing = missing
    return out

# --------------------------------------------------------------------------- rock
def layers(cells):
    """Integer terrace level per cell (HGSS layer top minus floor height) and the face set."""
    lab = np.array([[c['lab'] for c in row] for row in cells])
    rock = np.isin(lab, list(ROCK))
    d = np.zeros((H, W), int)
    for y in range(H):
        for x in range(W):
            c = cells[y][x]
            d[y, x] = max(1, round(c['peak']) - FLOOR_HEIGHT) if rock[y, x] else min(0, round(c['level']) - FLOOR_HEIGHT)
    # A boulder lying on the plateau is not a terrace of its own: its cells take the level
    # of the rock around it (the boulder's peak would otherwise raise a 2x2 mound).
    for y in range(H):
        for x in range(W):
            if rock[y, x] and cells[y][x].get('boulder'):
                ring = [int(d[yy, xx]) for yy in range(max(0, y - 1), min(H, y + 2)) for xx in range(max(0, x - 1), min(W, x + 2))
                        if rock[yy, xx] and not cells[yy][xx].get('boulder')]
                if ring:
                    d[y, x] = max(set(ring), key=ring.count)
    pad = np.pad(d, 1, mode='edge')
    lower = np.zeros((H, W), bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                lower |= pad[1 + dy:1 + dy + H, 1 + dx:1 + dx + W] < d
    return d, rock & lower, rock

def rock(cells, base, sw):
    """Paint every rock cell from its lower-neighbour mask (blob autotiling)."""
    d, face, isrock = layers(cells)
    out = base.copy()
    rockpx = np.zeros(out.shape[:2], bool)
    piece = np.full((H, W), '', object)
    top, band, side = sw['top'], sw['band'], sw['side']
    level = lambda x, y: d[min(max(y, 0), H - 1), min(max(x, 0), W - 1)]
    opn = lambda x, y: not isrock[min(max(y, 0), H - 1), min(max(x, 0), W - 1)]
    for y in range(H):
        for x in range(W):
            if not isrock[y, x]:
                continue
            X0, Y0 = x * 16, y * 16
            bx = (np.arange(16) + X0) % band.shape[1]
            cell = top[(np.arange(16) + Y0) % top.shape[0]][:, (np.arange(16) + X0) % top.shape[1]].copy()
            name = 'top'
            if face[y, x]:
                me = d[y, x]
                lo = {k: level(x + dx, y + dy) < me for k, (dx, dy) in DIRS.items()}
                strip = side[(np.arange(16) + Y0) % side.shape[0]]
                b = band[:, bx].copy()
                if opn(x, y + 1):
                    b[8:] = sw['foot'][:, bx]
                name = ''.join(k for k in DIRS if lo[k])
                if lo['n']:                                   # hidden north face: back rim
                    cell[0:2] = BLACKTHORN_RAMP[0]; cell[2] = BLACKTHORN_RAMP[2]
                if lo['s']:
                    cell = b.copy()
                if lo['e']:
                    cell[:, 6:] = strip[:, 6:]
                    if lo['s']:
                        cell[12:, 6:] = b[12:, 6:]
                elif lo['se'] and not lo['s']:
                    cell[:, 6:] = b[:, 6:]
                if lo['w']:
                    cell[:, :10] = strip[:, ::-1][:, :10]
                    if lo['s']:
                        cell[12:, :10] = b[12:, :10]
                elif lo['sw'] and not lo['s']:
                    cell[:, :10] = b[:, :10]
                if lo['ne'] and not lo['n'] and not lo['e']:
                    cell[:3, 6:] = strip[:3, 6:]
                if lo['nw'] and not lo['n'] and not lo['w']:
                    cell[:3, :10] = strip[:3, ::-1][:, :10]
            out[Y0:Y0 + 16, X0:X0 + 16] = cell
            rockpx[Y0:Y0 + 16, X0:X0 + 16] = True
            piece[y, x] = name
    pad = np.pad(rockpx, 1, mode='edge')
    edge = rockpx & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    out[edge] = BLACKTHORN_RAMP[0]
    return out, d, piece

# FRLG mountain set: bank 1 ramp 9-14 light to dark; 4 is the cast shadow, 5 and 8 the
# cave mouth's interior and threshold.
FRLG_RAMP = {9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 6}
FRLG_NINE = {('N', 'W'): 0x68, ('N', 'M'): 0x69, ('N', 'E'): 0x6A, ('M', 'W'): 0x70, ('M', 'M'): 0x71,
             ('M', 'E'): 0x72, ('S', 'W'): 0x78, ('S', 'M'): 0x79, ('S', 'E'): 0x7A}
FRLG_NINE_OVER_ROCK = {('N', 'W'): 0x6B, ('N', 'M'): 0x6C, ('N', 'E'): 0x6D, ('M', 'W'): 0x73, ('M', 'M'): 0x71,
                       ('M', 'E'): 0x75, ('S', 'W'): 0x7B, ('S', 'M'): 0x7C, ('S', 'E'): 0x7D}   # an edge onto lower rock
FRLG_INNER = dict(se=0xB2, sw=0xB3, ne=0xBA, nw=0xBB)          # whole-cell inner corners
FRLG_LEDGE = dict(mid=0x87, left=0xB0, right=0xB1)             # jump ledge and its rounded ends
FRLG_JOIN = dict(w=0x1F1, e=0x1F2)       # a mountain side with a ledge running into its foot from the west / east
FRLG_CAVE = 0xA9
CLEAR, SHADOW, CAVE_DARK, CAVE_SILL = -1, -2, -3, -4

def frlg_pieces(engine):
    """FRLG General's mountain pieces as index maps into Blackthorn's ramp (bank 1 only)."""
    d = engine / 'data/tilesets/primary/general_frlg'
    tiles = _tiles(d)
    blocks = np.frombuffer((d / 'metatiles.bin').read_bytes(), '<u2').reshape(-1, 8)
    def piece(m):
        out = np.full((16, 16), CLEAR, int)
        for li in range(8):
            e = int(blocks[m][li])
            if e >> 12 != 1:
                continue
            t = tiles[e & 1023]
            if e & 0x400: t = t[:, ::-1]
            if e & 0x800: t = t[::-1]
            q = li % 4
            sub = out[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            for (yy, xx), v in np.ndenumerate(t):
                if v:
                    sub[yy, xx] = FRLG_RAMP.get(int(v), {5: CAVE_DARK, 8: CAVE_SILL}.get(int(v), SHADOW))
        return out
    return dict(nine={k: piece(v) for k, v in FRLG_NINE.items()}, rock={k: piece(v) for k, v in FRLG_NINE_OVER_ROCK.items()},
                inner={k: piece(v) for k, v in FRLG_INNER.items()}, ledge={k: piece(v) for k, v in FRLG_LEDGE.items()},
                join={k: piece(v) for k, v in FRLG_JOIN.items()},
                cave=piece(FRLG_CAVE))

PLAIN = dict(sand=(8, 8), grass=(16, 0), water=(16, 0))   # flattest 8x8 block of each Cherrygrove texture

def rock_frlg(cells, base, pieces, tex, shore=None):
    """Blob autotiling from FRLG's set. A cell whose only lower neighbours are diagonal
    takes FRLG's whole inner-corner piece (two of them split down the middle when both
    lower diagonals are on one side), which joins the face and the side as one L. Every
    other cell is composed per 8x8 quadrant from the nine-slice piece its two edges call
    for, using FRLG's over-rock pieces where the quadrant faces a lower terrace and its
    over-ground pieces where it faces ground. As in FRLG, the rock is a top-layer overlay:
    its clear pixels show the bottom layer, which carries what lies beyond that edge (the
    lower terrace's top, or the plainest 8x8 block of that ground, a primary tile), and
    its cast shadow is Cherrygrove's border grey, so edge tiles and cells never pick up
    the ground texture's phase. Under a fully opaque quadrant the bottom is the rock top
    itself, so solid rock is one metatile. A shore quadrant (ground.shore) keeps the rim
    tile ground() drew for it, so a shoreline meeting the cliff carries on under its edge."""
    d, face, isrock = layers(cells)
    out = base.copy()
    over = np.zeros(base.shape[:2] + (4,), np.uint8)
    nine, nine_rock, inner, join = pieces['nine'], pieces['rock'], pieces['inner'], pieces['join']
    ledge_mid = pieces['ledge']['mid']
    is_ledge = lambda x, y: 0 <= x < W and cells[y][x]['lab'] == 'L'
    clamp = lambda x, y: (min(max(x, 0), W - 1), min(max(y, 0), H - 1))
    lvl = lambda x, y: d[clamp(x, y)[1], clamp(x, y)[0]]
    fill = np.array([BLACKTHORN_RAMP[i] for i in nine[('M', 'M')].ravel()], np.uint8).reshape(16, 16, 3)
    def beyond(x, y):
        """(pixels, ground class) of what lies past an edge toward cell (x, y)."""
        cx, cy = clamp(x, y)
        if isrock[cy, cx]:
            return fill, 'rock'
        c = cells[cy][cx]
        if c['floor'] in ('bridge', 'stairs'):
            return base[cy * 16:cy * 16 + 16, cx * 16:cx * 16 + 16], 'sand'
        px = base[cy * 16:cy * 16 + 16, cx * 16:cx * 16 + 16].reshape(-1, 3)
        count = {k: sum(int((px == np.array(v)).all(-1).sum()) for v in CHERRY[k]) for k in ('grass', 'sand', 'water')}
        k = max(count, key=count.get)
        return plain[k], k
    plain = {k: np.tile(tex[k][oy:oy + 8, ox:ox + 8], (2, 2, 1)) for k, (oy, ox) in PLAIN.items()}
    cast = dict(grass=BORDER_GRAY, sand=BORDER_GRAY, rock=None, water=None)
    piece = np.full((H, W), '', object)
    for y in range(H):
        for x in range(W):
            if not isrock[y, x]:
                continue
            me = d[y, x]
            lo = {k: lvl(x + dx, y + dy) < me for k, (dx, dy) in DIRS.items()}
            X0, Y0 = x * 16, y * 16
            cell, ov = out[Y0:Y0 + 16, X0:X0 + 16], over[Y0:Y0 + 16, X0:X0 + 16]
            diag = [k for k in ('ne', 'se', 'sw', 'nw') if lo[k]]
            whole = None
            if not any(lo[k] for k in 'nesw') and diag:
                if len(diag) == 1:
                    whole = inner[diag[0]]
                elif sorted(diag) in (['se', 'sw'], ['ne', 'nw']):
                    r, l = ('se', 'sw') if 'se' in diag else ('ne', 'nw')
                    whole = np.concatenate([inner[l][:, :8], inner[r][:, 8:]], 1)
            for qy in (0, 1):
                v = ('N', 'S')[qy] if lo['n'] and lo['s'] else 'N' if lo['n'] else 'S' if lo['s'] else 'M'
                for qx in (0, 1):
                    h = ('W', 'E')[qx] if lo['w'] and lo['e'] else 'W' if lo['w'] else 'E' if lo['e'] else 'M'
                    sl = np.s_[qy * 8:qy * 8 + 8, qx * 8:qx * 8 + 8]
                    vk, hk = 'ns'[qy], 'we'[qx]
                    toward = next((DIRS[k] for k in (vk, hk, vk + hk) if lo[k]), None)
                    bg, kind = beyond(x + toward[0], y + toward[1]) if toward else (fill, 'rock')
                    if whole is not None:
                        ix = whole[sl]
                    elif lo[vk + hk] and not lo[vk] and not lo[hk]:
                        ix = inner[vk + hk][sl]
                    else:
                        ix = (nine_rock if kind == 'rock' else nine)[(v, h)][sl]
                    if qy == 1 and is_ledge(x + (1 if qx else -1), y):
                        # A ledge runs into this cliff's foot: FRLG's join piece on a plain side,
                        # otherwise the ledge carried on under the rock's clear and shadow pixels.
                        if (v, h) == ('M', 'W' if qx == 0 else 'E'):
                            ix = join['w' if qx == 0 else 'e'][sl]
                        else:
                            ix = np.where((ix < 0) & (ledge_mid[sl] >= 0), ledge_mid[sl], ix)
                    if shore is None or not shore[y * 2 + qy, x * 2 + qx]:
                        cell[sl] = bg[sl]
                    q = ov[sl]
                    for (yy, xx), k in np.ndenumerate(ix):
                        if k >= 0:
                            q[yy, xx] = BLACKTHORN_RAMP[k] + (255,)
                        elif k == SHADOW and cast[kind]:
                            q[yy, xx] = cast[kind] + (255,)
                    if (q[..., 3] > 0).all():
                        cell[sl] = fill[sl]
            piece[y, x] = ''.join(k for k in DIRS if lo[k])
    return out, over, d, piece

# Frost and snow in CherrygrovePrimary bank 0's whites, which share a bank with its grass,
# so the snow drift's tiles need no secondary palette.
ICE = [(240, 240, 200), (224, 224, 184), (208, 208, 168), (128, 136, 120)]

def caves_frlg(out, over, cells, cave):
    """FRLG's cave mouth on each warp cell (a south face), on the rock's top layer. Ice
    Path's arch is rimmed with frost and a drift of snow spills onto the ground in front."""
    for (x, y), kind in CAVE_WARPS.items():
        X0, Y0 = x * 16, y * 16
        sl = over[Y0:Y0 + 16, X0:X0 + 16]
        dark = (36, 30, 32) if kind == 'dragons_den' else (56, 56, 72)        # shared with the houses' and Gym's darks
        sill = BLACKTHORN_RAMP[0] if kind == 'dragons_den' else ICE[2]
        floor = BORDER_GRAY                                 # the rock's own cast-shadow grey
        for (yy, xx), k in np.ndenumerate(cave):
            sl[yy, xx] = (BLACKTHORN_RAMP[k] if k >= 0 else dark if k == CAVE_DARK else sill if k == CAVE_SILL
                          else floor) + (255,)
        sl = sl[..., :3]
        if kind != 'ice_path':
            continue
        inside = cave == CAVE_DARK
        pad = np.pad(inside, 1)
        rim = ~inside & (pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:])
        ov = over[Y0:Y0 + 16, X0:X0 + 16]
        ov[rim & (cave >= 0)] = ICE[1] + (255,)
        ov[rim & (cave >= 0) & (np.arange(16)[:, None] < 6)] = ICE[0] + (255,)
        for r in range(18):                                   # snow drift fanning out of the mouth
            py = Y0 + 16 + r
            half = int(round(22 * (1 - ((r - 2) / 16) ** 2) ** 0.5)) if r >= 2 else 12 + 4 * r
            for px in range(X0 + 8 - half, X0 + 8 + half):
                edge = px - (X0 + 8 - half) < 2 or (X0 + 7 + half) - px < 2 or r >= 16
                if edge and (px + py) % 2:
                    continue
                out[py, px] = ICE[1] if edge else ICE[2] if r < 2 else ICE[0] if (px * 5 + r * 3) % 11 else ICE[1]

# --------------------------------------------------------------------------- elements
# Bridge and stair wood: CherrygrovePrimary's own wood ramp (bank 2), so plain wood tiles need no secondary palette.
WOOD = [(88, 64, 64), (120, 80, 56), (136, 96, 64), (160, 120, 88), (184, 136, 96), (200, 168, 112)]

def bridge(out, cells, water, rails=None):
    """North-south plank bridge: boards across, beams along both sides; the blocked
    cells either side of the deck carry its railing over the water. With rails (an RGBA
    top layer), the railing goes there over plain water, so no tile mixes wood and water."""
    xs = sorted({x for y in range(H) for x in range(W) if cells[y][x]['floor'] == 'bridge'})
    ys = sorted({y for y in range(H) for x in range(W) if cells[y][x]['floor'] == 'bridge'})
    x0, x1, y0, y1 = xs[0] * 16, xs[-1] * 16 + 16, ys[0] * 16, ys[-1] * 16 + 16
    yy, xx = np.mgrid[0:H * 16, 0:W * 16]
    for side, rx in ((-1, xs[0] - 1), (1, xs[-1] + 1)):
        for y in range(ys[0], ys[-1] + 1):
            if cells[y][rx]['lab'] != 'X':
                continue
            X0, Y0 = rx * 16, y * 16
            out[Y0:Y0 + 16, X0:X0 + 16] = water[yy[Y0:Y0 + 16, X0:X0 + 16] % 32, xx[Y0:Y0 + 16, X0:X0 + 16] % 32]
            dst, a = (out, ()) if rails is None else (rails, (255,))
            c0 = X0 + 11 if side < 0 else X0
            dst[Y0:Y0 + 16, c0:c0 + 5] = WOOD[2] + a
            dst[Y0:Y0 + 16, c0 + (0 if side < 0 else 4)] = WOOD[0] + a
            dst[Y0:Y0 + 16, c0 + (4 if side < 0 else 0)] = WOOD[1] + a
            dst[Y0 + 6:Y0 + 10, c0:c0 + 5] = WOOD[1] + a
    for py in range(y0, y1):
        r = (py - y0) % 8
        row = WOOD[4] if r in (0, 1) else WOOD[3] if r in (2, 3, 4) else WOOD[2] if r in (5, 6) else WOOD[1]
        out[py, x0:x1] = row
        if r == 3:                                            # nail heads near both beams
            out[py, x0 + 5] = WOOD[1]; out[py, x1 - 6] = WOOD[1]
        out[py, x0:x0 + 3] = (WOOD[2], WOOD[1], WOOD[0])[::-1] if False else (WOOD[0], WOOD[1], WOOD[2])
        out[py, x1 - 3:x1] = (WOOD[2], WOOD[1], WOOD[0])
        if (py - y0) % 32 in (0, 1, 2):                       # posts along the beams
            out[py, x0:x0 + 3] = WOOD[1]; out[py, x1 - 3:x1] = WOOD[1]
    return (x0, y0, x1, y1)

def stairs(out, cells):
    """Wooden steps: light treads with dark risers, one cell wide."""
    for y in range(H):
        for x in range(W):
            if cells[y][x]['floor'] != 'stairs':
                continue
            X0, Y0 = x * 16, y * 16
            for r in range(16):
                k = r % 4
                out[Y0 + r, X0:X0 + 16] = (WOOD[5], WOOD[4], WOOD[2], WOOD[0])[k]
            out[Y0:Y0 + 16, X0] = WOOD[0]; out[Y0:Y0 + 16, X0 + 15] = WOOD[0]

CAVE_WARPS = {(32, 4): 'dragons_den', (57, 16): 'ice_path'}   # HGSS T30 warps 2 and 0

def caves(out, cells, band):
    """Cave mouths: a dark arch cut into a face band on the warp cell; Ice Path gets frost."""
    for (x, y), kind in CAVE_WARPS.items():
        X0, Y0 = x * 16, y * 16
        out[Y0:Y0 + 16, X0:X0 + 16] = band[:, (np.arange(16) + X0) % band.shape[1]]
        for py in range(Y0 - 6, Y0 + 16):
            cy = py - (Y0 - 6)
            half = 6 if cy >= 6 else int(round((36 - (6 - cy) ** 2) ** 0.5))
            if not half:
                continue
            xl, xr = X0 + 8 - half, X0 + 8 + half
            out[py, xl:xr] = (8, 8, 16)
            out[py, xl - 1] = BLACKTHORN_RAMP[0]; out[py, xr] = BLACKTHORN_RAMP[0]
            if kind == 'ice_path':
                out[py, xl] = (189, 189, 189); out[py, xr - 1] = (156, 156, 156)
        if kind == 'ice_path':                                # frost on the ground in front
            for fx in (x - 1, x, x + 1):
                sl = out[(y + 1) * 16:(y + 1) * 16 + 6, fx * 16:fx * 16 + 16]
                sl[:] = (sl.astype(int) * 0.4 + np.array((236, 240, 244)) * 0.6).astype(np.uint8)

def boulders(out, cells, rock01, ramp=None):
    """HGSS's boulder (already clean pixel art) as a 2x2 prop, into an RGB bottom layer
    or an RGBA top layer; with ramp, its shades are snapped to that ramp by brightness."""
    a = rock01[..., 3] > 0
    rock01 = rock01.copy()
    if ramp is not None:
        light = sorted(ramp, key=sum)
        lum = rock01[..., :3].astype(int).sum(-1)
        levels = np.quantile(lum[a], np.linspace(0, 1, len(light) + 1)[1:-1])
        rock01[..., :3] = np.array(light, np.uint8)[np.searchsorted(levels, lum)]
    px = rock01 if out.shape[2] == 4 else rock01[..., :3]
    done = set()
    for y in range(H):
        for x in range(W):
            b = cells[y][x].get('boulder')
            if b and tuple(b) not in done:
                done.add(tuple(b))
                X0, Y0 = b[0] * 16, b[1] * 16
                sl = out[Y0:Y0 + 32, X0:X0 + 32]
                sl[a] = px[a]

def ledges_frlg(cells, pieces):
    """FRLG's jump ledge in Blackthorn's ramp on the top layer: rounded ends where the
    ledge stops on open ground, the plain strip where it runs into a cliff (the cliff's
    own join piece carries it on), Cherrygrove's border grey for its shadow."""
    top = np.zeros((H * 16, W * 16, 4), np.uint8)
    lp = pieces['ledge']
    lab = lambda x, y: cells[y][x]['lab'] if 0 <= x < W else 'T'
    for y in range(H):
        for x in range(W):
            if lab(x, y) != 'L':
                continue
            free = lambda n: lab(n, y) not in ROCK and lab(n, y) != 'L'
            ix = lp['mid'].copy()
            if free(x - 1):
                ix[:, :8] = lp['left'][:, :8]
            if free(x + 1):
                ix[:, 8:] = lp['right'][:, 8:]
            for (yy, xx), k in np.ndenumerate(ix):
                if k >= 0:
                    top[y * 16 + yy, x * 16 + xx] = BLACKTHORN_RAMP[k] + (255,)
                elif k == SHADOW:
                    top[y * 16 + yy, x * 16 + xx] = BORDER_GRAY + (255,)
    return top

def ledges(cells, strip):
    top = np.zeros((H * 16, W * 16, 4), np.uint8)
    L = lambda x, y: 0 <= x < W and cells[y][x]['lab'] == 'L'
    for y in range(H):
        for x in range(W):
            if not L(x, y):
                continue
            t = strip.copy()
            if not L(x - 1, y):                               # rounded west end
                t[0:2, 0:2, 3] = 0; t[0, 2, 3] = 0; t[2:6, 0] = BLACKTHORN_RAMP[0] + (255,)
            if not L(x + 1, y):
                t[0:2, 14:16, 3] = 0; t[0, 13, 3] = 0; t[2:6, 15] = BLACKTHORN_RAMP[0] + (255,)
            top[y * 16 + 8:y * 16 + 16, x * 16:x * 16 + 16] = t
    return top

# --------------------------------------------------------------------------- objects
# (sprite, left cell, top cell): sprites sit with their bottom edge on the bottom of
# their lowest blocked cell. Footprints and doors are the decoded HGSS permissions.
SHARED = SRC / 'shared-art'
SIGN_METATILE = 0x114                  # Cherrygrove's accepted town sign, a full opaque cell
SIGNS = [(31, 6), (21, 48), (26, 25), (13, 43), (52, 42)]

def objects():
    sys.path.insert(0, str(HERE))
    import sprites as S
    rgba = lambda f: np.array(Image.open(SHARED / f).convert('RGBA'))
    post = S.gate_post()
    return [
        ('gym', S.gym(), 25 * 16, 19 * 16),
        ('west_house', S.hut(), 19 * 16, 33 * 16),
        ('tutor_house', S.hut(), 17 * 16, 44 * 16),
        ('east_house', S.hut(), 43 * 16, 36 * 16),
        ('stone', S.standing_stone(), 23 * 16, 38 * 16 - 56),
        ('gate_post_west', post, 21 * 16, 54 * 16 - post.shape[0]),
        ('gate_post_east', S.gate_post(True), 25 * 16, 54 * 16 - post.shape[0]),
        ('poke_mart', rgba('poke-mart.png'), 25 * 16, 43 * 16),
        ('pokemon_center', rgba('pokemon-center.png'), 31 * 16, 43 * 16),
    ]

def place(bottom, top, cells, tex):
    """Objects go to the bottom layer over blocked cells and to the top layer (drawn
    above the player) over cells the player can occupy, so the player walks behind
    them; a building's own footprint is always bottom layer."""
    sign = np.array(Image.open(SRC / 'elements/cherrygrove-sign-cell.png').convert('RGB'))
    for sx, sy in SIGNS:
        bottom[sy * 16:sy * 16 + 16, sx * 16:sx * 16 + 16] = sign
    blocked = np.array([[c['blocked'] or c['lab'] in ROCK for c in row] for row in cells]).repeat(16, 0).repeat(16, 1)
    owner = np.full(bottom.shape[:2], '', object)
    shared = np.zeros(bottom.shape[:2] + (4,), np.uint8)       # Center and Mart, exact palettes
    shared_src = np.zeros(bottom.shape[:2], np.uint8)           # 1 Mart, 2 Center
    for name, img, X, Y in objects():
        h, w = img.shape[:2]
        a = img[..., 3] > 0
        sl = np.s_[Y:Y + h, X:X + w]
        if name in ('poke_mart', 'pokemon_center'):
            shared[sl][a] = img[a]
            shared_src[sl][a] = 1 if name == 'poke_mart' else 2
            owner[sl][a] = name
            continue
        # Every object lives on the top layer over plain ground, so its tiles never mix
        # with a ground texture (the three houses share every tile) and the ground below
        # stays the primary's own. The packer picks the layer type per cell: drawn above
        # the player where the cell is walkable (walk-behind), below it where blocked.
        top[sl][a] = img[a]
        owner[sl][a] = name
    return owner, shared, shared_src

# --------------------------------------------------------------------------- compose
def primary_check(engine):
    sys.path.insert(0, str(HERE))
    import pack as P
    tiles, pals, _, _ = P.primary(engine)
    opaque, _ = P.primary_index(tiles, pals)
    return lambda t: P.key5(t) in opaque

def compose(engine, phg, style, cells):
    if not hasattr(ground, 'in_primary'):
        ground.in_primary = primary_check(engine)
    tex = cherry_textures()
    sw = rock_swatches(style, engine, phg)
    bottom = ground(cells, tex, shore=style == 'C')
    rails = np.zeros(bottom.shape[:2] + (4,), np.uint8) if style == 'C' else None
    bridge(bottom, cells, tex['water'], rails)
    stairs(bottom, cells)
    if style == 'C':
        bottom, top, level, piece = rock_frlg(cells, bottom, sw, tex, ground.shore)
        a = rails[..., 3] > 0
        top[a] = rails[a]
        caves_frlg(bottom, top, cells, sw['cave'])
    else:
        bottom, level, piece = rock(cells, bottom, sw)
        caves(bottom, cells, sw['band'])
        top = np.zeros(bottom.shape[:2] + (4,), np.uint8)
    if style == 'C':                       # a boulder on plain rock top: the top stays in the bottom layer, so
        for y in range(H):                 # every boulder shares the same top-layer tiles
            for x in range(W):
                if cells[y][x].get('boulder') and piece[y, x] == '' and cells[y][x]['lab'] in ROCK:
                    top[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = 0
    boulders(top if style == 'C' else bottom, cells, hgss_texture(phg, 'rock01', 'rock01'),
             BLACKTHORN_RAMP if style == 'C' else None)
    lg = ledges_frlg(cells, sw) if style == 'C' else ledges(cells, route31_ledge(engine))
    a = lg[..., 3] > 0
    top[a] = lg[a]
    owner, shared, shared_src = place(bottom, top, cells, tex)
    return bottom, top, level, piece, owner, shared, shared_src

def preview(bottom, top):
    out = bottom.copy()
    a = top[..., 3] > 0
    out[a] = top[..., :3][a]
    return out

def main(engine, phg):
    cells = ledger(phg)
    save_ledger(cells)
    (EV / 'elements').mkdir(parents=True, exist_ok=True)
    views = {}
    for style in ('A', 'B', 'C'):
        bottom, top, level, piece, owner, shared, shared_src = compose(engine, phg, style, cells)
        np.savez_compressed(SRC / 'elements' / f'compose-{style}.npz', bottom=bottom, top=top, shared=shared, shared_src=shared_src,
                            owner=owner.astype(str), level=level, piece=piece.astype(str))
        v = preview(bottom, top)
        a = shared[..., 3] > 0
        v[a] = shared[..., :3][a]
        views[style] = v
        Image.fromarray(views[style]).save(EV / 'elements' / f'terrain-{style}.png')
    ref = np.array(Image.open(SRC / 'hgss/hgss-reference-true-heights.png').convert('RGB'))
    for name, box, s in (('rock-compare', (4, 26, 40, 58), 2), ('rock-detail', (4, 24, 24, 44), 3)):
        x0, y0, x1, y1 = [v * 16 for v in box]
        w, h = (x1 - x0) * s, (y1 - y0) * s
        sheet = Image.new('RGB', (w * 4 + 36, h + 24), (28, 32, 38)); d = ImageDraw.Draw(sheet)
        for i, (img, t) in enumerate(((ref, 'HGSS reference'), (views['A'], 'A: HGSS pieces, one layer per metatile'),
                                      (views['B'], 'B: Emerald rock recoloured to Blackthorn'),
                                      (views['C'], 'C: FRLG mountain set recoloured to Blackthorn'))):
            sheet.paste(Image.fromarray(img[y0:y1, x0:x1]).resize((w, h), Image.Resampling.NEAREST), (i * (w + 12), 24))
            d.text((i * (w + 12) + 4, 6), t, fill='white')
        sheet.save(EV / 'elements' / f'{name}.png')
    print('wrote terrain-A/B/C.png and comparison sheets')

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
