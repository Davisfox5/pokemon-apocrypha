"""Cianwood City as Gen 3 elements: ledger and terrain composer (the Blackthorn method).

    python3 tools/gba/maps/cianwood_elements/elements.py ENGINE_CHECKOUT PHG_CHECKOUT

Builds Cianwood from reusable elements instead of a 1:1 HGSS render. Every cell gets a
material and structure label from HGSS geometry (top-down height map, slopes and
permissions, map header 75, zone T24). A cell's terrace level is the top of its HGSS
layer, so cliffs become Gen 3 terraces drawn from FRLG's General mountain set recoloured
to the HGSS rock ramp (Cianwood's cliff01gs uses Blackthorn's colours), composed per 8x8
quadrant, as a top-layer overlay over plain ground with its cast shadow.

Ground is Gen 3 ground in CherrygrovePrimary's own colours: Cherrygrove's grass and sea
(animated in the primary), a Gen 3-style beach (a 16 px sand cell with scattered grains
and one-tile decals: grains, a ripple, a shell, pebbles), grass meeting sand on rounded
edges with a dithered rim on the sand side, and Cherrygrove's sandbar as the shore, its
inner corners curved with the same radius as its outer ones. HGSS's shallow-water strip
along the coast is the beach's wet edge (walkable, MB_SHALLOW_WATER), so the foam lies
where HGSS's waves are. Off the map is open sea (Route 41 to the east). Ledges are FRLG's,
the east-facing ones the same strip turned on its side. Buildings and props are HGSS's own
models and textures rendered at C06's angle (sprites.py, hgss_camera.view); the Center is
the owner-locked C06.

    source/elements/ledger.json, ledger.png, compose-C.npz
    evidence/elements/terrain-C.png
"""
from __future__ import annotations
import json, sys
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/cianwood-elements'
SRC, EV = ART / 'source', ART / 'evidence'
W, H = 32, 64
ROCK = set('TESWN')
FLOOR_HEIGHT = 1                     # HGSS height of the walkable town floor (the beach)
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
            rockpx = frac.get('sea_rock', 0) + frac.get('sea_rock_m', 0)
            if rockpx >= 48 and int(types[y, x]) not in (0x15, 0x17, 0x21):
                lab = 'R'                                     # a rock standing in the sea
            elif water:
                lab = '~'
            elif t == 0x17:
                lab = '.'                                     # shallow surf: the beach's wet edge, walkable
            elif frac.get('etc_a', 0) >= 10 and blocked:
                # one of HGSS's small stones: its bump is no slope; it sits on the plateau or on the lawn
                lab = 'T' if dominant in ROCK_MATERIALS or level[y, x] >= FLOOR_HEIGHT + 2.5 else 'X'
            elif share[y, x] > 0.25 and blocked and t not in (0x38, 0x3B, 0x3E):
                a = np.degrees(np.arctan2(ddy[y, x], ddx[y, x])) % 360
                lab = 'ESWN'[int(((a + 45) % 360) // 90)]
            elif t == 0x3B:
                lab = 'L'                                     # jump south
            elif t == 0x38:
                lab = 'K'                                     # jump east
            elif t == 0x3E:
                lab = 'L'                                     # HGSS's corner where both ledges meet: the south ledge's end
            elif blocked and (level[y, x] >= FLOOR_HEIGHT + 2.5 or dominant in ROCK_MATERIALS):
                lab = 'T'
            elif blocked:
                lab = 'X'
            else:
                lab = '.'
            # HGSS paints the grass at the cliff foot with the beach's edge material, so read
            # the cell's own top-down colour: green against cream
            px = rgb[y * 16:y * 16 + 16, x * 16:x * 16 + 16].reshape(-1, 3).astype(int)
            grass = int(((px[:, 1] > px[:, 0] + 40) & (px[:, 1] > px[:, 2])).sum())
            sand = int(((px[:, 0] > 200) & (px[:, 1] > 200) & (px[:, 2] > 150) & (abs(px[:, 0] - px[:, 1]) < 20)).sum())
            floor = 'water' if water or lab == 'R' else 'shallow' if t == 0x17 else 'grass' if grass > sand else 'sand'
            row.append(dict(lab=lab, floor=floor, level=round(float(level[y, x]), 2), peak=round(float(peak[y, x]), 2),
                            type=t, blocked=blocked, owner=int(owner[y, x]), material=dominant,
                            flowers=frac.get('flower03', 0) > 40, grass_px=int(grass), sand_px=int(sand),
                            stone=frac.get('etc_a', 0) >= 10 and blocked))
        cells.append(row)
    # A small stone's bump is no terrace: its cell takes the height of the ground round it.
    for y in range(H):
        for x in range(W):
            if cells[y][x]['stone']:
                ring = [cells[yy][xx] for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))
                        if 0 <= yy < H and 0 <= xx < W and not cells[yy][xx]['stone'] and cells[yy][xx]['lab'] == cells[y][x]['lab']]
                if ring:
                    cells[y][x]['peak'] = float(np.median([c['peak'] for c in ring]))
                    cells[y][x]['level'] = float(np.median([c['level'] for c in ring]))
    # Boulders (HGSS rock01): 2x2 props, the material marks their lower row.
    for y in range(H):
        for x in range(W):
            if cells[y][x]['material'] == 'rock01' and cells[y][x]['lab'] != 'O':
                x0 = x if x + 1 < W and cells[y][x + 1]['material'] == 'rock01' else x - 1
                for yy in (y - 1, y):
                    for xx in (x0, x0 + 1):
                        cells[yy][xx].update(lab='O', boulder=[x0, y - 1])
    # A boulder's ground is what lies round it (one stands half in the sea).
    for y in range(H):
        for x in range(W):
            if cells[y][x]['lab'] == 'O':
                ring = [cells[yy][xx]['floor'] for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))
                        if 0 <= yy < H and 0 <= xx < W and cells[yy][xx]['lab'] != 'O']
                # ties go to the surf strip, so the shore runs on under a boulder at the water's edge
                order = ['shallow', 'water', 'sand', 'grass']
                cells[y][x]['floor'] = max(sorted(set(ring), key=order.index), key=ring.count) if ring else 'sand'
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
    for y, x in ((y, x) for y in range(H) for x in range(W)):
        c = cells[y][x]
        if (x, y) in CAVE_WARPS:
            c['cave'] = CAVE_WARPS[(x, y)]
    return cells

def save_ledger(cells):
    out = SRC / 'elements'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'ledger.json').write_text(json.dumps(dict(
        note='Per-cell element ledger derived from HGSS land_data. lab: T rock top, E/S/W/N rock face by downhill '
             'direction, L jump south, K jump east, O boulder, R sea rock, X other blocked (buildings, props), '
             '~ water, . open. floor: ground under open cells (shallow: the walkable surf strip). '
             'peak: HGSS cell maximum height (terrace level = peak - 1).',
        cells=[[c['lab'] + c['floor'][0] for c in row] for row in cells],
        detail=cells)) + '\n')
    img = Image.new('RGB', (W * 12, H * 12), (20, 20, 24)); d = ImageDraw.Draw(img)
    col = dict(T=(150, 110, 80), E=(200, 120, 60), W=(200, 160, 60), S=(220, 80, 60), N=(120, 90, 160), L=(240, 220, 120),
               K=(240, 200, 100), X=(90, 90, 90), O=(120, 80, 60), R=(150, 150, 160))
    for y in range(H):
        for x in range(W):
            c = cells[y][x]
            fill = col.get(c['lab']) or dict(water=(60, 120, 230), grass=(110, 210, 160), sand=(240, 236, 200),
                                               shallow=(170, 220, 230))[c['floor']]
            d.rectangle((x * 12, y * 12, x * 12 + 11, y * 12 + 11), fill=fill)
            if c['lab'] in 'ESWNLKOR':
                d.text((x * 12 + 3, y * 12), c['lab'], fill='black')
    img.save(out / 'ledger.png')

# --------------------------------------------------------------------------- source art
def hgss_texture(phg, name, pal):
    sys.path.insert(0, str(HERE))
    import hgss_render as R
    _, tex0, _, _, _ = R.load(phg)
    e = next(t for t in tex0.textures if t.name == name)
    return R.decode(tex0, e, pal)

# HGSS rock ramp (cliff01gs, the same colours as Blackthorn's): outline, then light to dark.
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
              sand=[(240, 240, 200), (232, 232, 192), (224, 224, 184), (208, 208, 168)],      # the cream beach
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
                m = 0 if name == 'sand' else 1           # Cherrygrove's beach is a narrow strip: no margin
                if hit[max(0, ky - m):ky + 4 + m, max(0, kx - m):kx + 4 + m].all():
                    b = img[y:y + 32, x:x + 32].tobytes(); blocks[b] = blocks.get(b, 0) + 1
        out[name] = np.frombuffer(max(blocks, key=blocks.get), np.uint8).reshape(32, 32, 3)
    # Cherrygrove's beach is one 16 px metatile repeated: the sandbar's plain middle cell
    # (the cells above it carry the dock's shadow).
    out['sand'] = np.tile(img[384:400, 368:384], (2, 2, 1))
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

# --------------------------------------------------------------------------- helpers
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

def art(rows, pal):
    """RGB pixel art from rows of palette keys."""
    return np.array([[pal[ch] for ch in r] for r in rows], np.uint8)

# --------------------------------------------------------------------------- ground
FOAM = (200, 232, 224)                  # Cherrygrove's foam lip

# Cianwood's beach in Cherrygrove's cream (all CherrygrovePrimary bank 0), drawn the way
# Gen 3 draws sand (Emerald's Dewford and Route 104): a flat base with scattered light
# grains, each with a shade pixel under it, and a few darker grains. On open beach some
# cells carry a decal in one 8 px quarter (a second scatter, a ripple of HGSS's beach, a
# shell, pebbles), so the 16 px repeat does not read as a grid and each decal costs one
# tile; cells beside an edge or under an object keep the base, so edge tiles do not multiply.
SAND_PAL = {'.': (232, 232, 192), '+': (240, 240, 200), '-': (224, 224, 184), '=': (216, 216, 176), '#': (208, 208, 168),
            'w': (224, 200, 128), 't': (216, 184, 128), 'T': (184, 168, 128), 'D': (152, 144, 112)}
SAND_BASE = ["................", "..++............", "...=......+.....", "..........=.....",
             "......#.........", "..............++", ".+.............=", ".=......++......",
             ".........=......", "...#.........#..", "................", "......++........",
             ".......=.....+..", "..+.........==..", "..=.............", "..........#....."]
# name: (quarter 0-3 in reading order, 8 x 8 decal)
SAND_DECALS = dict(
    grains=(1, ["........", "...++...", "....=...", "........", ".+....#.", ".=......", "........", "....++.."]),
    ripple=(2, ["........", "..+++...", ".+===++.", "=......=", "........", "....++..", "...+==+.", "........"]),
    shell=(0, ["........", "..DDD...", ".D+w+D..", "D+w+w+D.", "DTwTwTD.", ".DTwTD..", "..DDD...", "...##..."]),
    pebbles=(3, ["........", ".tt.....", "twtT....", "ttTD..t.", ".DD..twT", ".....tTD", "......D.", "........"]),
)
SAND_ODDS = [('grains', 26), ('ripple', 18), ('shell', 4), ('pebbles', 7)]     # percent of open beach cells
LOUD = ('shell', 'pebbles')
CHERRY['sand'] = list(dict.fromkeys(CHERRY['sand'] + [(216, 216, 176)]))       # the beach's darker grain

def sand_cells():
    base = art(SAND_BASE, SAND_PAL)
    out = {'base': base}
    for name, (q, rows) in SAND_DECALS.items():
        cell = base.copy()
        cell[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8] = art(rows, SAND_PAL)
        out[name] = cell
    return out

def sand_variant(x, y):
    """The variant for an open beach cell, from a fixed hash of its position."""
    import hashlib
    h = int(hashlib.md5(f'cianwood-sand {x},{y}'.encode()).hexdigest(), 16) % 100
    for name, pct in SAND_ODDS:
        if h < pct:
            return name
        h -= pct
    return 'base'

GRASS_TUFT = (104, 208, 152)            # Cherrygrove grass's base green
SAND_RIM = (216, 216, 176)

def ground(cells, tex):
    """Grass, beach and sea under everything else. Beach is the cream sand above (its
    variants on open beach); grass is Cherrygrove's lawn; the sea Cherrygrove's, in phase.
    Grass meets sand the way Gen 3 draws a sand patch in a lawn (Emerald's Route 104): the
    cell mask is blurred so every corner, inner and outer, rounds off while straight runs
    stay on the cell edge, and the sand side carries the transition, a row where grass
    pixels and a darker rim alternate and a dithered rim row behind it. Keeping straight
    runs on the edge and the fuzz on the sand's own 16 px repeat lets the lawn stay
    CherrygrovePrimary's tiles and the edge reuse a few. Cells that are not grass or sand
    (rock, sea, the surf strip) lend the class of the nearest ground cell, so no edge is
    drawn against them."""
    from scipy import ndimage
    lab = np.array([[c['lab'] for c in row] for row in cells])
    floor = np.array([[c['floor'] for c in row] for row in cells])
    g = (floor == 'grass') & ~np.isin(lab, list(ROCK))
    for comp in _components(g.copy()):
        if len(comp) < 2:
            for y, x in comp: g[y, x] = False
    water = np.isin(lab, ['~', 'R']) | (np.isin(lab, ['X', 'O']) & (floor == 'water'))   # sea rocks and boulders stand in the sea
    land = ~water & (floor != 'shallow') & ~np.isin(lab, list(ROCK))
    ys, xs = np.mgrid[0:H * 16, 0:W * 16]
    sand = sand_cells()
    out = sand['base'][ys % 16, xs % 16].copy()
    near_edge = ndimage.binary_dilation(~(land & ~g), np.ones((3, 3), bool))
    # No decal where an object stands (its edge tiles would pick it up), and a shell or
    # pebbles keeps two cells clear of another, so the eye-catching ones never line up.
    covered = np.zeros((H, W), bool)
    for _, img, X, Y in objects():
        ys_, xs_ = np.nonzero(img[..., 3])
        covered[(Y + ys_) // 16, (X + xs_) // 16] = True
    picks = {}
    for y in range(H):
        for x in range(W):
            if land[y, x] and not g[y, x] and not near_edge[y, x] and not covered[y, x]:
                v = sand_variant(x, y)
                if v in LOUD and any(picks.get((x + dx, y + dy)) in LOUD for dy in (-2, -1, 0) for dx in range(-2, 3)):
                    v = 'base'
                picks[(x, y)] = v
                out[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = sand[v]
    _, (iy, ix) = ndimage.distance_transform_edt(~(land | g), return_indices=True)
    gext = g[iy, ix]
    G = ndimage.gaussian_filter(gext.repeat(16, 0).repeat(16, 1).astype(float), 3.0, mode='nearest') > 0.5
    lawn = land.repeat(16, 0).repeat(16, 1)
    ds = ndimage.distance_transform_cdt(~G, metric='taxicab')
    grass_px = lawn & G
    out[grass_px] = tex['grass'][ys % 32, xs % 32][grass_px]
    checker = (xs + ys) % 2 == 0
    sand_px = lawn & ~G
    out[sand_px & (ds == 1)] = np.where(checker[..., None], GRASS_TUFT, SAND_RIM)[sand_px & (ds == 1)]
    out[sand_px & (ds == 2) & checker] = SAND_RIM
    wat = water.repeat(16, 0).repeat(16, 1)
    out[wat] = tex['water'][ys % 32, xs % 32][wat]
    ground.shore = np.zeros((H * 2, W * 2), bool)        # no shore quadrant runs under a cliff here
    ground.grass = G & lawn
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

CAVE_WARPS = {(10, 27): 'cliff_edge_gate'}   # HGSS T24 warp 6's mouth (a west entrance in the cliff's east side)

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
    # East-facing ledges (jump east): the same strip turned on its side, so the face that
    # looks south looks east, with the rounded ends at its top and bottom.
    for y in range(H):
        for x in range(W):
            if lab(x, y) != 'K':
                continue
            vfree = lambda n: not (0 <= n < H) or (cells[n][x]['lab'] not in ROCK and cells[n][x]['lab'] not in 'LK')
            ix = lp['mid'].T.copy()
            if vfree(y - 1):
                ix[:8, :] = lp['left'].T[:8, :]
            if vfree(y + 1) and lab(x, y + 1) != 'L':
                ix[8:, :] = lp['right'].T[8:, :]
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
# (name, sprite, x px, y px): each sprite's bottom edge sits on the bottom of its object's
# lowest blocked cell. Footprints and doors are the decoded HGSS permissions and warps.
SHARED = SRC / 'shared-art'
SIGN_METATILE = 0x114                  # Cherrygrove's accepted town sign, a full opaque cell
EVENTS = json.loads((SRC / 'hgss-events.json').read_text())
SIGNS = [tuple(e['cell']) for e in EVENTS['signs'] if e['bg_type'] == 1]
CENTER_ORIGIN = (25, 45)               # C06: 5x5, door tile (2,4) on the HGSS Center door (27,49)

def objects():
    sys.path.insert(0, str(HERE))
    import sprites as S
    rgba = lambda f: np.array(Image.open(SHARED / f).convert('RGBA'))
    base = lambda img, x, row: (x * 16, (row + 1) * 16 - img.shape[0])        # bottom on the bottom of that row
    house, pharmacy, studio, cam, gym = S.load('house'), S.load('pharmacy'), S.load('studio'), S.load('camera'), S.load('gym')
    out = [
        ('north_house', house, *base(house, 6, 15)),
        ('kirks_house', house, *base(house, 9, 47)),
        ('central_house', house, *base(house, 20, 42)),
        ('pharmacy', pharmacy, *base(pharmacy, 18, 50)),
        ('studio', studio, *base(studio, 20, 34)),          # with its poster board in cell 24
        ('camera', cam, *base(cam, 25, 34)),
        ('gym', gym, *base(gym, 9, 37)),
        ('pokemon_center', rgba('pokemon-center.png'), CENTER_ORIGIN[0] * 16, CENTER_ORIGIN[1] * 16),
    ]
    rack = S.load('rack')
    out += [(f'rack_{i}', rack, *base(rack, 28, row)) for i, row in enumerate((33, 36, 39, 42))]
    rock, peb = S.load('sea_rock'), S.load('pebble')
    for i, (cx, cy) in enumerate(SEA_ROCKS):
        out.append((f'sea_rock_{i}', rock, int(round((cx * 16 - 16) / 8)) * 8, int(round((cy * 16 - rock.shape[0] / 2) / 8)) * 8))
    out.append(('pebble', peb, int(round((PEBBLE[0] * 16 - 8) / 8)) * 8, int(round((PEBBLE[1] * 16 - 6) / 8)) * 8))
    # Ground details, snapped to the 8 px grid so every copy shares the same few tiles.
    st, tf = S.load('stone'), S.load('tuft')
    for i, (cx, cy) in enumerate(STONES):                # each in the lower half of the cell it sits in
        out.append((f'stone_{i}', st, int(round((cx * 16 - 8) / 8)) * 8, int(cy) * 16 + 8))
    for i, (cx, cy) in enumerate(TUFTS):
        out.append((f'tuft_{i}', tf, int(round((cx * 16 - 8) / 8)) * 8, int(round((cy * 16 - 9) / 8)) * 8))
    return out

# HGSS's sea rocks (sea_rock material blobs, each two cells wide): centres in cells. The
# four touching rocks of row 9 are one blob in the material map and are split here.
SEA_ROCKS = [(31.0, 5.05), (28.0, 7.05), (31.0, 7.05), (25.0, 9.05), (27.0, 9.05), (29.0, 9.05), (31.0, 9.05),
             (28.0, 11.05), (27.0, 13.05), (28.0, 15.05), (30.0, 16.05), (30.0, 18.05), (30.0, 20.05),
             (29.0, 22.05), (28.0, 24.05), (28.0, 26.05)]
PEBBLE = (23.5, 10.6)
# HGSS's small stones (material etc_a) and sand tufts (beach_sub): blob centres in cells.
STONES = [(17.47, 5.56), (2.97, 7.56), (5.47, 9.56), (13.47, 10.56), (16.47, 10.56), (11.47, 13.56), (12.47, 13.56),
          (3.47, 36.56), (3.47, 54.06), (13.47, 54.56), (14.47, 54.56), (23.47, 56.56), (9.47, 57.06), (24.47, 59.06)]
TUFTS = [(15.0, 16.56), (18.5, 18.56), (13.0, 20.56), (18.0, 28.06), (13.5, 30.56), (25.5, 32.06), (18.5, 37.56),
         (14.0, 40.06), (25.5, 43.56), (15.5, 45.56), (28.5, 52.56)]

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
        # Where it overlaps the rock's top-layer overlay in a cell no player reaches (the
        # cell and the one below it blocked), that overlay drops to the bottom layer, so
        # the north house's roof against the cliff and a stone on a cliff top keep the
        # same top-layer tiles as their copies on open ground.
        hit = np.zeros(bottom.shape[:2], bool)
        hit[sl] = a
        for ty in range(Y // 8, (Y + h + 7) // 8):
            for tx in range(X // 8, (X + w + 7) // 8):
                ts = np.s_[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
                below = min(ty // 2 + 1, H - 1)
                if not hit[ts].any() or not blocked[ty * 8, tx * 8] or not blocked[below * 16, tx * 8]:
                    continue
                m = (top[ts][..., 3] > 0) & (owner[ts] == '')
                bottom[ts][m] = top[ts][..., :3][m]
                top[ts][m] = 0
        top[sl][a] = img[a]
        owner[sl][a] = name
    return owner, shared, shared_src

# --------------------------------------------------------------------------- shore
# The fallback shore profile for a strip cell no sandbar cell fits, measured from
# Cherrygrove's beach: from the land side, 2 px of dark sand, 5 px of foam, then the sea.
SHORE_SAND, SHORE_FOAM = 2, 7
# Cherrygrove's sandbar, cell by cell: (x, y) of the 16 px window in its native map for
# the shore cell beside land on one side (keyed by that side) and the outer corner cell
# beside land on one diagonal. The top edge's foam spills a cell north of the sand, so its
# window starts 5 rows up, where the plain sand begins; its north-east corner sits in the
# dock's shadow, so it is the north-west corner mirrored.
SHORE_EDGE = dict(w=(432, 384), e=(352, 384), n=(384, 400), s=(368, 341))
SHORE_CORNER = dict(nw=(432, 400, False), ne=(352, 400, False), se=(352, 341, False), sw=(352, 341, True))
SAND_RIM_TIDE = (208, 208, 168)          # Cherrygrove's dark tide line
SHORE_ROUND = 10                        # px: radius of the sea's curve at an inner corner (the sandbar's outer corners curve about 12)

def shore_pieces(tex):
    """Each sandbar window as RGBA plus a sand flag (channel 4). Cherrygrove's sea is one
    32 px block repeated, so a pixel equal to the sea at its own phase is sea (cleared);
    one equal to Cherrygrove's sand cell at its own phase is plain beach, which the
    receiving beach's own sand replaces."""
    img = np.array(Image.open(SRC / 'elements/cherrygrove-native.png').convert('RGB'))
    ys, xs = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    sea = (img == tex['water'][ys % 32, xs % 32]).all(-1)
    plain = img[384:400, 368:384]
    sand = (img == plain[ys % 16, xs % 16]).all(-1) & ~sea
    def cut(x, y, flip=False):
        a = np.dstack([img[y:y + 16, x:x + 16], np.where(sea[y:y + 16, x:x + 16], 0, 255).astype(np.uint8),
                       sand[y:y + 16, x:x + 16].astype(np.uint8)])
        return a[:, ::-1].copy() if flip else a
    return {k: cut(*v) for k, v in SHORE_EDGE.items()}, {k: cut(*v) for k, v in SHORE_CORNER.items()}

def shore(out, cells, tex):
    """HGSS's walkable shallow strip as Cherrygrove's sandbar shore: a strip cell beside
    land on one side is the sandbar's edge cell for that side (its foam and wet sand, in
    phase along the coast), one beside land on a diagonal only is the sandbar's rounded
    corner. One between two land sides is the inner corner, rounded the same way: the
    sea's edge is a quarter circle of SHORE_ROUND px and every band (wet sand, foam lip)
    keeps its own distance from it, so the sea curves into the beach instead of meeting it
    in a mitre. The curve starts in the two edge cells beside the corner, since a radius
    that reads as round does not fit inside one cell. Sea pixels stay the sea at the map's
    phase and plain beach takes Cianwood's own sand. A sea cell touching the beach
    directly gets the same shore. Off the map is sea."""
    from scipy import ndimage
    floor = np.array([[c['floor'] for c in row] for row in cells])
    lab = np.array([[c['lab'] for c in row] for row in cells])
    wet = (floor == 'shallow') | (floor == 'water') | (lab == 'R')
    land = ~wet
    dist = ndimage.distance_transform_edt(~land.repeat(16, 0).repeat(16, 1))
    ys, xs = np.mgrid[0:H * 16, 0:W * 16]
    sea = tex['water'][ys % 32, xs % 32]
    beach = sand_cells()['base'][ys % 16, xs % 16]
    edges, corners = shore_pieces(tex)
    is_land = lambda x, y: 0 <= x < W and 0 <= y < H and bool(land[y, x])
    iy, ix = np.mgrid[0:16, 0:16]
    depth = dict(w=ix, e=15 - ix, n=iy, s=15 - iy)
    def sample(piece, side, d):
        d = np.clip(np.round(d).astype(int), 0, 15)
        return {'w': piece[iy, d], 'e': piece[iy, 15 - d], 'n': piece[d, ix], 's': piece[15 - d, ix]}[side]
    sides4 = dict(w=(-1, 0), e=(1, 0), n=(0, -1), s=(0, 1))
    # Where each edge piece turns to sea, in px from its land side.
    sea_at = {k: next(d for d in range(16) if (sample(p, k, np.full((16, 16), d))[..., 3] > 0).sum() < 128)
              for k, p in edges.items()}
    def strip_cell(x, y):
        touches = any(is_land(x + dx, y + dy) for dx, dy in sides4.values())
        return 0 <= x < W and 0 <= y < H and (floor[y, x] == 'shallow' or (floor[y, x] == 'water' and lab[y, x] not in 'RO' and touches))
    def land_sides(x, y):
        return [k for k, (dx, dy) in sides4.items() if is_land(x + dx, y + dy)]
    inner = [(x, y, *land_sides(x, y)) for y in range(H) for x in range(W)
             if strip_cell(x, y) and len(land_sides(x, y)) == 2 and land_sides(x, y)[0] in 'we' and land_sides(x, y)[1] in 'ns']
    def from_land(k, cx, cy, gx, gy):
        """Depth from side k's land line of the corner cell (cx, cy), for global pixels."""
        return dict(w=gx - cx * 16, e=cx * 16 + 15 - gx, n=gy - cy * 16, s=cy * 16 + 15 - gy)[k].astype(float)
    shore.kinds = {}
    painted = np.zeros((H, W), bool)
    for y in range(H):
        for x in range(W):
            if not strip_cell(x, y):
                continue
            cell = (slice(y * 16, y * 16 + 16), slice(x * 16, x * 16 + 16))
            sides = land_sides(x, y)
            diag = [d for d, (dx, dy) in dict(nw=(-1, -1), ne=(1, -1), sw=(-1, 1), se=(1, 1)).items() if is_land(x + dx, y + dy)]
            piece = None
            if len(sides) == 1 or (x, y, *sides) in inner:
                # Each pixel samples the edge piece of its nearer land side at its depth; near
                # an inner corner the depth is measured from the curved sea edge instead.
                gy, gx = iy + y * 16, ix + x * 16
                which = np.full((16, 16), sides[0], object)
                d = depth[sides[0]].astype(float)
                if len(sides) == 2:
                    which[depth[sides[1]] < depth[sides[0]]] = sides[1]
                    d = np.minimum(d, depth[sides[1]])
                for cx, cy, a, b in inner:
                    if abs(cx - x) > 2 or abs(cy - y) > 2 or not ({a, b} & set(sides)):
                        continue
                    da, db = from_land(a, cx, cy, gx, gy), from_land(b, cx, cy, gx, gy)
                    if (cx, cy) != (x, y) and not ((sides[0] == a and (db >= 16).all()) or (sides[0] == b and (da >= 16).all())):
                        continue                                   # only the corner's own two edge runs
                    r = SHORE_ROUND
                    ca, cb = sea_at[a] + r, sea_at[b] + r
                    zone = (da >= 0) & (db >= 0) & (da < ca) & (db < cb)
                    e = np.hypot(ca - da, cb - db) - r              # px from the curved sea edge toward land
                    use_a = da <= db
                    d = np.where(zone, np.where(use_a, sea_at[a] - e, sea_at[b] - e), d)
                    which = np.where(zone, np.where(use_a, a, b), which)
                d = np.maximum(d, 0)
                piece = np.zeros((16, 16, 5), np.uint8)
                for k in set(which.ravel()):
                    m = which == k
                    piece[m] = sample(edges[k], k, d)[m]
            elif not sides and len(diag) == 1:
                piece = corners[diag[0]]
            if piece is None:
                kind = 'profile'
                strip = np.zeros((H * 16, W * 16), bool); strip[cell] = True
                out[strip] = sea[strip]
                out[strip & (dist <= SHORE_FOAM)] = FOAM
                out[strip & (dist <= SHORE_SAND)] = SAND_RIM
            else:
                kind = '+'.join(sides) if sides else diag[0]
                block = sea[cell].copy()
                a = piece[..., 3] > 0
                block[a] = piece[..., :3][a]
                plain = piece[..., 4] > 0
                block[plain] = beach[cell][plain]
                out[cell] = block
            painted[y, x] = True
            shore.kinds[kind] = shore.kinds.get(kind, 0) + 1
    # One wet-sand band for every orientation: within the shore cells, beach pixels within
    # 2 px of the dark tide line are wet (Cherrygrove's darker cream), the rest Cianwood's sand.
    strip = np.zeros((H * 16, W * 16), bool)
    for y, x in zip(*np.nonzero(painted)):
        strip[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = True
    cream = (out[..., None, :] == np.array([(240, 240, 200), (232, 232, 192), (224, 224, 184), (216, 216, 176)], np.uint8)).all(-1).any(-1)
    tide = (out == SAND_RIM_TIDE).all(-1)
    near = ndimage.distance_transform_cdt(~tide, metric='taxicab') <= 2
    out[strip & cream & near] = (224, 224, 184)
    out[strip & cream & ~near] = beach[strip & cream & ~near]
    # Shore tiles keep to the sea's own bank (CherrygrovePrimary bank 1), so they cost no
    # secondary colours: the beach's darker grain takes the tide colour, and the few green
    # pixels on Cherrygrove's sandbar tide line (its secondary bank) join the tide line.
    grain = (out == SAND_RIM).all(-1)
    out[strip & grain] = SAND_RIM_TIDE
    foam = ndimage.binary_dilation((out == FOAM).all(-1), iterations=2)
    out[strip & foam & (out == (168, 216, 152)).all(-1)] = SAND_RIM_TIDE

# --------------------------------------------------------------------------- compose
def compose(engine, phg, cells):
    tex = cherry_textures()
    tex['sand'] = np.tile(sand_cells()['base'], (2, 2, 1))     # Cianwood's beach, for what rock edges show
    sw = frlg_pieces(engine)
    bottom = ground(cells, tex)
    shore(bottom, cells, tex)
    bottom, top, level, piece = rock_frlg(cells, bottom, sw, tex, ground.shore)
    caves_frlg(bottom, top, cells, sw['cave'])
    for y in range(H):                     # a boulder on plain rock top: the top stays in the bottom layer, so
        for x in range(W):                 # every boulder shares the same top-layer tiles
            if cells[y][x].get('boulder') and piece[y, x] == '' and cells[y][x]['lab'] in ROCK:
                top[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = 0
    boulders(top, cells, hgss_texture(phg, 'rock01', 'rock01'), BLACKTHORN_RAMP)
    lg = ledges_frlg(cells, sw)
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
    bottom, top, level, piece, owner, shared, shared_src = compose(engine, phg, cells)
    np.savez_compressed(SRC / 'elements' / 'compose-C.npz', bottom=bottom, top=top, shared=shared, shared_src=shared_src,
                        owner=owner.astype(str), level=level, piece=piece.astype(str))
    v = preview(bottom, top)
    a = shared[..., 3] > 0
    v[a] = shared[..., :3][a]
    Image.fromarray(v).save(EV / 'elements' / 'terrain-C.png')
    ref = np.array(Image.open(SRC / 'hgss/hgss-reference-true-heights.png').convert('RGB'))
    sheet = Image.new('RGB', (W * 16 * 2 + 12, H * 16 + 24), (28, 32, 38)); d = ImageDraw.Draw(sheet)
    for i, (img, t) in enumerate(((ref, 'HGSS reference (decoded map data)'), (v, 'Gen 3 elements'))):
        sheet.paste(Image.fromarray(img), (i * (W * 16 + 12), 24)); d.text((i * (W * 16 + 12) + 4, 6), t, fill='white')
    sheet.save(EV / 'elements' / 'compare.png')
    print('wrote terrain-C.png and compare.png; shore cells:', shore.kinds)

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
