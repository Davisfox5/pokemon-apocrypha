"""Route 43's flat HGSS decode and rock pieces (Mahogany's elements.py, the Blackthorn method).

Used by trace.py, assemble.py, pack_lossless.py and check3.py for: topdown (HGSS's flat
top-down materials, heights and colours), ledger (per-cell label: rock cells T/E/S/W/N by
slope and collision, ledges L, woods F, tall grass G, pond water ~, other blocked X; ground
height, peak, floor material), tree_footprints (2x2 HGSS tree roots), frlg_pieces and
rock_frlg (FRLG General's mountain nine-slice in the Johto rock ramp, one face per
metatile, as a top-layer overlay) and cherry_textures (Cherrygrove's 32 px lawn and sand
blocks under the rock's clear pixels). HGSS Route 43's floor is height 4; the south-west
massif steps up to 7 and the east ridge to 6, the ponds sit at 2.

The rest of this module (Mahogany's element composer and its main) is not used for Route 43.
"""
from __future__ import annotations
import json, sys
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route-43'
SRC, EV = ART / 'source', ART / 'evidence'
W, H = 32, 64
ROCK = set('TESWN')
LEDGES = set('LQJ')                  # jump south, jump west, the blocked corner where they meet
FLOOR_HEIGHT = 4                     # HGSS height of the walkable town floor
DIRS = dict(n=(0, -1), ne=(1, -1), e=(1, 0), se=(1, 1), s=(0, 1), sw=(-1, 1), w=(-1, 0), nw=(-1, -1))
ROCK_MATERIALS = ('cliff01gs', 'allpeakgs', 'allpeak_pgs', 'wall01_d', 'wall01_g', 'wall01_h')
LEDGE_MATERIALS = ('allpeakgs', 'allpeak_pgs')
TREE_MATERIALS = ('tree01gs', 'tree01_un', 'tree01_re')

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
    low = h.reshape(H, 16, W, 16).min(axis=(1, 3))
    nm = np.array(names + ['none'])
    m = np.where(mat >= 0, mat, len(names)).reshape(H, 16, W, 16).transpose(0, 2, 1, 3).reshape(H, W, 256)
    # A rock cell's peak counts only its rock pixels: tree crowns beside a wall reach higher.
    hc = h.reshape(H, 16, W, 16).transpose(0, 2, 1, 3).reshape(H, W, 256)
    isrockpx = np.isin(nm[m], ROCK_MATERIALS)
    peak = np.where(isrockpx.any(-1), np.where(isrockpx, hc, -1e9).max(-1), hc.max(-1))
    blds = json.loads((SRC / 'hgss/hgss-render.json').read_text())['buildings']
    owner = np.full((H, W), -1, int)
    for i, b in enumerate(blds):
        x0, z0, x1, z1 = b['footprint']
        owner[max(0, int(np.floor(z0))):int(np.ceil(z1)), max(0, int(np.floor(x0))):int(np.ceil(x1))] = i
    cells = []
    for y in range(H):
        row = []
        for x in range(W):
            u, cnt = np.unique(nm[m[y, x]], return_counts=True)
            dominant = str(u[np.argmax(cnt)])
            frac = {str(k): int(v) for k, v in zip(u, cnt)}
            blocked = bool(coll[y, x] & 0x80)
            t = int(types[y, x])
            tree = t == 0x06
            if tree:
                lab = 'F'                                     # HGSS tree (its crown is in the terrain mesh)
            elif t == 0x10:
                lab = '~'                                     # pond water (Surf)
            elif t == 0x02:
                lab = 'G'                                     # tall grass (encounters)
            elif share[y, x] > 0.25 and blocked and t not in (0x39, 0x3B) and dominant not in LEDGE_MATERIALS:
                a = np.degrees(np.arctan2(ddy[y, x], ddx[y, x])) % 360
                lab = 'ESWN'[int(((a + 45) % 360) // 90)]
            elif t == 0x3B:
                lab = 'L'                                     # jump south
            elif t == 0x39:
                lab = 'Q'                                     # jump west
            elif blocked and dominant in LEDGE_MATERIALS:
                lab = 'J'                                     # ledge corner: drawn as ledge, blocked as in HGSS
            elif blocked and (level[y, x] >= FLOOR_HEIGHT + 1.5 or dominant in ROCK_MATERIALS):
                lab = 'T'
            elif blocked:
                lab = 'X'
            else:
                lab = '.'
            grass = sum(v for k, v in frac.items() if k.startswith('grass') or k == 'flower03' or k in TREE_MATERIALS)
            sand = sum(v for k, v in frac.items() if k.startswith('road'))
            # Ground level under trees and props: the lowest point of the cell (a crown or a
            # roof lifts the median); everywhere else the median.
            ground = low[y, x] if (tree or lab == 'X') else level[y, x]
            row.append(dict(lab=lab, floor='grass' if grass > sand else 'sand', level=round(float(level[y, x]), 2),
                            ground=round(float(ground), 2), peak=round(float(peak[y, x]), 2),
                            type=t, blocked=blocked, owner=int(owner[y, x]), material=dominant,
                            flowers=frac.get('flower03', 0) > 40, grass_px=int(grass), sand_px=int(sand)))
        cells.append(row)
    return cells

def tree_footprints(cells):
    """HGSS trees stand on 2 x 2 footprints: a crown row (tree01gs / tree01_re) over a trunk
    row (tree01_un). Each run of trunk cells pairs up from its west end. In dense woods a
    crown hides the trunk row of the tree behind it, so the woods cells (F) no tree covers
    are then filled with 2 x 2 footprints, north-west first, on F cells only."""
    out = []
    for y in range(1, H):
        x = 0
        while x < W:
            c = cells[y][x]
            if c['lab'] == 'F' and c['material'] == 'tree01_un':
                x1 = x
                while x1 < W and cells[y][x1]['lab'] == 'F' and cells[y][x1]['material'] == 'tree01_un':
                    x1 += 1
                for tx in range(x, x1 - 1, 2):
                    out.append((tx, y - 1))
                x = x1
            else:
                x += 1
    cov = {(tx + dx, ty + dy) for tx, ty in out for dx in (0, 1) for dy in (0, 1)}
    free = lambda x, y: x < W and y < H and cells[y][x]['lab'] == 'F' and (x, y) not in cov
    for y in range(H - 1):
        for x in range(W - 1):
            if all(free(x + dx, y + dy) for dx in (0, 1) for dy in (0, 1)):
                out.append((x, y))
                cov |= {(x + dx, y + dy) for dx in (0, 1) for dy in (0, 1)}
    # A woods cell still bare gets one more tree on a 2 x 2 of F cells holding it, overlapping
    # its neighbours as HGSS's own crowns overlap (the one whose 2 x 2 holds most bare cells).
    isf = lambda x, y: 0 <= x < W and 0 <= y < H and cells[y][x]['lab'] == 'F'
    for y in range(H):
        for x in range(W):
            if not isf(x, y) or (x, y) in cov:
                continue
            opts = [(x - ax, y - ay) for ax in (0, 1) for ay in (0, 1)
                    if all(isf(x - ax + dx, y - ay + dy) for dx in (0, 1) for dy in (0, 1))]
            if opts:
                tx, ty = max(opts, key=lambda o: (sum((o[0] + dx, o[1] + dy) not in cov for dx in (0, 1) for dy in (0, 1)), -o[1], -o[0]))
                out.append((tx, ty))
                cov |= {(tx + dx, ty + dy) for dx in (0, 1) for dy in (0, 1)}
    return sorted(out, key=lambda t: (t[1], t[0]))

def save_ledger(cells, trees):
    out = SRC / 'elements'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'ledger.json').write_text(json.dumps(dict(
        note='Per-cell element ledger derived from HGSS land_data. lab: T rock top, E/S/W/N rock face by downhill '
             'direction, L jump south, Q jump west, J blocked ledge corner, F tree, X other blocked (buildings, '
             'props), . open. floor: ground under the cell. ground: HGSS ground height (terrace level = ground - 4; '
             'rock cells use peak - 4). trees: HGSS 2x2 tree footprints, top-left cell.',
        cells=[[c['lab'] + c['floor'][0] for c in row] for row in cells],
        trees=trees, detail=cells)) + '\n')
    s = 16
    img = Image.new('RGB', (W * s, H * s), (20, 20, 24)); d = ImageDraw.Draw(img)
    col = dict(T=(150, 110, 80), E=(200, 120, 60), W=(200, 160, 60), S=(220, 80, 60), N=(120, 90, 160), L=(240, 220, 120),
               Q=(240, 220, 120), J=(240, 200, 90), F=(40, 110, 60), X=(90, 90, 90))
    for y in range(H):
        for x in range(W):
            c = cells[y][x]
            fill = col.get(c['lab']) or dict(grass=(110, 210, 160), sand=(230, 200, 140))[c['floor']]
            d.rectangle((x * s, y * s, x * s + s - 1, y * s + s - 1), fill=fill)
            if c['lab'] in 'ESWNLQJ':
                d.text((x * s + 4, y * s + 2), c['lab'], fill='black')
    for tx, ty in trees:
        d.rectangle((tx * s + 2, ty * s + 2, tx * s + 2 * s - 3, ty * s + 2 * s - 3), outline=(200, 255, 200))
    img.save(out / 'ledger.png')

# --------------------------------------------------------------------------- source art
def hgss_texture(phg, name, pal):
    sys.path.insert(0, str(HERE))
    import hgss_render as R
    _, tex0, _, _, _ = R.load(phg)
    e = next(t for t in tex0.textures if t.name == name)
    return R.decode(tex0, e, pal)

# The HGSS rock ramp, outline then light to dark. Mahogany's cliff01gs is the same texture
# and palette as Blackthorn's (decoded from both area texture sets), so this is Blackthorn's.
ROCK_RAMP = [(82, 58, 52), (239, 189, 140), (222, 173, 123), (198, 148, 115), (165, 115, 99), (132, 90, 74), (99, 70, 66)]

def _tiles(d):
    a = np.array(Image.open(d / 'tiles.png')) & 15
    return [a[y:y + 8, x:x + 8] for y in range(0, a.shape[0], 8) for x in range(0, a.shape[1], 8)]

# Cherrygrove ground (accepted Johto vocabulary), learned from its decoded native map.
CHERRY = dict(grass=[(104, 208, 152), (88, 176, 136), (128, 136, 120), (104, 200, 152), (96, 192, 144)],
              sand=[(224, 200, 128), (216, 184, 128), (184, 168, 128)])
BORDER_GRAY, BORDER_GREEN = (128, 136, 120), (88, 176, 136)

def cherry_textures():
    """Cherrygrove's canonical 32x32 grass and sand blocks (its 32 px grid)."""
    img = np.array(Image.open(SRC / 'elements/cherrygrove-native.png').convert('RGB'))
    a = img.reshape(img.shape[0] // 8, 8, img.shape[1] // 8, 8, 3).transpose(0, 2, 1, 3, 4).reshape(img.shape[0] // 8, img.shape[1] // 8, 64, 3)
    out = {}
    for name in ('grass', 'sand'):
        cols = CHERRY[name]
        hit = sum((a == np.array(c)).all(-1).sum(-1) for c in cols) >= 40
        blocks = {}
        for y in range(0, img.shape[0] - 31, 32):
            for x in range(0, img.shape[1] - 31, 32):
                ky, kx = y // 8, x // 8
                if hit[max(0, ky - 1):ky + 5, max(0, kx - 1):kx + 5].all():
                    b = img[y:y + 32, x:x + 32].tobytes(); blocks[b] = blocks.get(b, 0) + 1
        out[name] = np.frombuffer(max(blocks, key=blocks.get), np.uint8).reshape(32, 32, 3)
    return out

# Cherrygrove's standalone tree (the one west of its Mart, cells (56..57, 5..7) of the
# decoded native town): 32 x 48 with its trunk and contact shadow, bottom on its cell row.
TREE_BOX = (896, 80, 928, 128)

def cherry_tree(tex):
    img = np.array(Image.open(SRC / 'elements/cherrygrove-native.png').convert('RGB'))
    x0, y0, x1, y1 = TREE_BOX
    ys, xs = np.mgrid[y0:y1, x0:x1]
    px = img[y0:y1, x0:x1]
    lawn = tex['grass'][ys % 32, xs % 32]
    out = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
    a = (px != lawn).any(-1)
    out[a, :3] = px[a]; out[a, 3] = 255
    return out

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

# --------------------------------------------------------------------------- ground
NB8 = [(-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0)]
GRASS_C, SAND_C = 1, 2

def _classes8(img):
    a = img.reshape(img.shape[0] // 8, 8, img.shape[1] // 8, 8, 3).transpose(0, 2, 1, 3, 4).reshape(img.shape[0] // 8, img.shape[1] // 8, 64, 3)
    count = lambda cols: sum((a == np.array(c)).all(-1).sum(-1) for c in cols)
    g, s = count(CHERRY['grass']), count(CHERRY['sand'])
    return np.where(g >= 40, GRASS_C, np.where(s >= 40, SAND_C, 0))

def _key(k, ty, tx):
    """Own class plus the class of each of the eight neighbours; anything that is not
    ground (rock) counts as the tile's own class, so no rim is drawn there."""
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

def ground(cells, tex):
    """Cherrygrove ground: its own tiles for every grass/sand neighbour configuration it has
    (preferring the one at the same 32 px texture phase); the nearest configuration it has
    where it lacks one. Trees, ledges and props stand on their own floor class, so the lawn
    runs on under them; rock counts as its neighbour's class, so no border runs along it."""
    lab = np.array([[c['lab'] for c in row] for row in cells])
    floor = np.array([[c['floor'] for c in row] for row in cells])
    g = (floor == 'grass')
    for comp in _components(g.copy()):
        if len(comp) < 2:
            for y, x in comp: g[y, x] = False
    ground_cell = ~np.isin(lab, list(ROCK))
    k = np.where(~ground_cell, 0, np.where(g, GRASS_C, SAND_C)).repeat(2, 0).repeat(2, 1)
    lib = learn_ground(ground.in_primary)
    ys, xs = np.mgrid[0:H * 16, 0:W * 16]
    out = np.where(g.repeat(16, 0).repeat(16, 1)[..., None], tex['grass'][ys % 32, xs % 32], tex['sand'][ys % 32, xs % 32]).astype(np.uint8)
    missing = {}
    def lookup(key, ph):
        cand = lib.get(key)
        if cand is None:
            same = [q for q in lib if q[0] == key[0]]
            wgt = [1, 3, 1, 3, 1, 3, 1, 3]
            q = min(same, key=lambda q: (sum(wv * (a != b) for wv, a, b in zip(wgt, q[1:], key[1:])), q))
            cand = lib[q]; missing[key] = missing.get(key, 0) + 1
        tiles = cand.get(ph) or max(cand.values(), key=len)
        best = max(sorted(set(tiles)), key=tiles.count)              # sorted: ties break the same way every run
        return np.frombuffer(best, np.uint8).reshape(8, 8, 3)
    for ty in range(H * 2):
        for tx in range(W * 2):
            if k[ty, tx] == 0:
                continue
            out[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8] = lookup(_key(k, ty, tx), (tx % 4, ty % 4))
    ground.missing = missing
    return out

# --------------------------------------------------------------------------- rock
def layers(cells):
    """Integer terrace level per cell (rock cells: HGSS peak height above the floor) and the
    face set. All ground is level 0, the raised lawns included: HGSS draws the low walls
    round them as thick walls with a brown cap, so each wall is a one-cell Gen 3 ridge with
    a rim on its high side and a face on its low side, over lawn on both."""
    lab = np.array([[c['lab'] for c in row] for row in cells])
    rock = np.isin(lab, list(ROCK))
    d = np.zeros((H, W), int)
    for y in range(H):
        for x in range(W):
            c = cells[y][x]
            d[y, x] = max(1, round(c['peak']) - FLOOR_HEIGHT) if rock[y, x] else 0
    pad = np.pad(d, 1, mode='edge')
    lower = np.zeros((H, W), bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                lower |= pad[1 + dy:1 + dy + H, 1 + dx:1 + dx + W] < d
    return d, rock & lower, rock

# FRLG mountain set: bank 1 ramp 9-14 light to dark; 4 is the cast shadow.
FRLG_RAMP = {9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 6}
FRLG_NINE = {('N', 'W'): 0x68, ('N', 'M'): 0x69, ('N', 'E'): 0x6A, ('M', 'W'): 0x70, ('M', 'M'): 0x71,
             ('M', 'E'): 0x72, ('S', 'W'): 0x78, ('S', 'M'): 0x79, ('S', 'E'): 0x7A}
FRLG_NINE_OVER_ROCK = {('N', 'W'): 0x6B, ('N', 'M'): 0x6C, ('N', 'E'): 0x6D, ('M', 'W'): 0x73, ('M', 'M'): 0x71,
                       ('M', 'E'): 0x75, ('S', 'W'): 0x7B, ('S', 'M'): 0x7C, ('S', 'E'): 0x7D}   # an edge onto lower rock
FRLG_INNER = dict(se=0xB2, sw=0xB3, ne=0xBA, nw=0xBB)          # whole-cell inner corners
FRLG_LEDGE = dict(mid=0x87, left=0xB0, right=0xB1)             # jump ledge and its rounded ends
FRLG_JOIN = dict(w=0x1F1, e=0x1F2)       # a mountain side with a ledge running into its foot from the west / east
CLEAR, SHADOW = -1, -2

def frlg_pieces(engine):
    """FRLG General's mountain pieces as index maps into the rock ramp (bank 1 only)."""
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
                    sub[yy, xx] = FRLG_RAMP.get(int(v), SHADOW)
        return out
    return dict(nine={k: piece(v) for k, v in FRLG_NINE.items()}, rock={k: piece(v) for k, v in FRLG_NINE_OVER_ROCK.items()},
                inner={k: piece(v) for k, v in FRLG_INNER.items()}, ledge={k: piece(v) for k, v in FRLG_LEDGE.items()},
                join={k: piece(v) for k, v in FRLG_JOIN.items()})

PLAIN = dict(sand=(8, 8), grass=(16, 0))   # flattest 8x8 block of each Cherrygrove texture

def rock_frlg(cells, base, pieces, tex):
    """Blob autotiling from FRLG's set (Blackthorn's rock_frlg). A cell whose only lower
    neighbours are diagonal takes FRLG's whole inner-corner piece (two of them split down
    the middle when both lower diagonals are on one side), which joins the face and the
    side as one L. Every other cell is composed per 8x8 quadrant from the nine-slice piece
    its two edges call for, using FRLG's over-rock pieces where the quadrant faces a lower
    rock terrace and its over-ground pieces where it faces ground (the raised lawns count
    as ground: a wall seen from below them shows the lawn past its edge). The rock is a
    top-layer overlay: its clear pixels show the bottom layer, which carries the plainest
    8x8 block of the ground beyond that edge, and its cast shadow is Cherrygrove's border
    grey. Under a fully opaque quadrant the bottom is the rock top itself."""
    d, face, isrock = layers(cells)
    out = base.copy()
    over = np.zeros(base.shape[:2] + (4,), np.uint8)
    nine, nine_rock, inner, join = pieces['nine'], pieces['rock'], pieces['inner'], pieces['join']
    ledge_mid = pieces['ledge']['mid']
    is_ledge = lambda x, y: 0 <= x < W and cells[y][x]['lab'] in 'LJ'
    clamp = lambda x, y: (min(max(x, 0), W - 1), min(max(y, 0), H - 1))
    lvl = lambda x, y: d[clamp(x, y)[1], clamp(x, y)[0]]
    fill = np.array([ROCK_RAMP[i] for i in nine[('M', 'M')].ravel()], np.uint8).reshape(16, 16, 3)
    plain = {k: np.tile(tex[k][oy:oy + 8, ox:ox + 8], (2, 2, 1)) for k, (oy, ox) in PLAIN.items()}
    def beyond(x, y):
        """(pixels, ground class) of what lies past an edge toward cell (x, y)."""
        cx, cy = clamp(x, y)
        if isrock[cy, cx]:
            return fill, 'rock'
        k = cells[cy][cx]['floor']
        return plain[k], k
    cast = dict(grass=BORDER_GRAY, sand=BORDER_GRAY, rock=None)
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
                    cell[sl] = bg[sl]
                    q = ov[sl]
                    for (yy, xx), k in np.ndenumerate(ix):
                        if k >= 0:
                            q[yy, xx] = ROCK_RAMP[k] + (255,)
                        elif k == SHADOW and cast[kind]:
                            q[yy, xx] = cast[kind] + (255,)
                    if (q[..., 3] > 0).all():
                        cell[sl] = fill[sl]
            piece[y, x] = ''.join(k for k in DIRS if lo[k])
    return out, over, d, piece

def ledges_frlg(cells, pieces):
    """FRLG's jump ledge in the rock ramp on the top layer: rounded ends where the ledge
    stops on open ground, the plain strip where it runs into a cliff or another ledge.
    West-facing ledges (jump west) are the strip turned on its side and mirrored, so the
    face looks west; the blocked corner where the west run meets the south run carries
    both. Cherrygrove's border grey is the shadow."""
    top = np.zeros((H * 16, W * 16, 4), np.uint8)
    lp = pieces['ledge']
    lab = lambda x, y: cells[y][x]['lab'] if 0 <= x < W and 0 <= y < H else 'T'
    def paint(x, y, ix):
        for (yy, xx), k in np.ndenumerate(ix):
            if k >= 0:
                top[y * 16 + yy, x * 16 + xx] = ROCK_RAMP[k] + (255,)
            elif k == SHADOW and not top[y * 16 + yy, x * 16 + xx, 3]:
                top[y * 16 + yy, x * 16 + xx] = BORDER_GRAY + (255,)
    for y in range(H):
        for x in range(W):
            if lab(x, y) not in 'LJ':
                continue
            free = lambda n: lab(n, y) not in ROCK and lab(n, y) not in LEDGES and lab(n, y) != 'F'
            ix = lp['mid'].copy()
            if free(x - 1):
                ix[:, :8] = lp['left'][:, :8]
            if free(x + 1):
                ix[:, 8:] = lp['right'][:, 8:]
            paint(x, y, ix)
    for y in range(H):
        for x in range(W):
            if lab(x, y) not in 'QJ' or (lab(x, y) == 'J' and lab(x, y - 1) != 'Q'):
                continue
            vfree = lambda n: lab(x, n) not in ROCK and lab(x, n) not in LEDGES and lab(x, n) != 'F'
            side = lambda p: p.T[:, ::-1]                     # face looking west
            ix = side(lp['mid']).copy()
            if vfree(y - 1):
                ix[:8, :] = side(lp['left'])[:8, :]
            if lab(x, y) == 'Q' and vfree(y + 1):
                ix[8:, :] = side(lp['right'])[8:, :]
            if lab(x, y) == 'J':
                ix[8:, :] = CLEAR                               # the south run carries the corner's lower half
            paint(x, y, ix)
    return top

# --------------------------------------------------------------------------- objects
# (name, sprite, left px, top px): sprites sit with their bottom edge on the bottom of their
# base row. Footprints and doors are the decoded HGSS placements and permissions. The houses,
# the Gym, the Route 43 gate, the lookout towers and the antenna tree are written by
# sprites.py from HGSS's own models; the Center is the owner-locked C06.
SHARED = SRC / 'shared-art'
SIGNS = [(4, 12), (14, 14), (8, 24)]   # HGSS bg events: town sign, souvenir shop sign, Gym sign
CENTER_ORIGIN = (20, 19)               # C06's door (2, 4) on the HGSS Center door (22, 23)

def objects():
    sys.path.insert(0, str(HERE))
    import sprites as S
    rgba = lambda f: np.array(Image.open(SHARED / f).convert('RGBA'))
    base = lambda img, x, row: (x * 16, (row + 1) * 16 - img.shape[0])        # bottom on the bottom of that row
    house, gym, gate, tower, antree = S.load('house'), S.load('gym'), S.load('gate'), S.load('tower'), S.load('antree')
    return [
        ('gate', gate, *base(gate, 10, 5)),
        ('tower_west', tower, *base(tower, 6, 8)),
        ('tower_east', tower, *base(tower, 25, 8)),
        ('souvenir_shop', house, *base(house, 15, 14)),
        ('east_house', house, *base(house, 24, 14)),
        ('antenna_tree', antree, *base(antree, 19, 14)),            # 4 px east of HGSS's centre, clear of the shop's wall
        ('gym', gym, *base(gym, 8, 23)),
        ('pokemon_center', rgba('pokemon-center.png'), CENTER_ORIGIN[0] * 16, CENTER_ORIGIN[1] * 16),
    ]

def place(bottom, top, cells, tex, trees):
    """Trees and objects go to the top layer over plain ground, so their tiles never mix with
    a ground texture; the packer picks each cell's layer type (above the player where the
    player walks behind the art, below it elsewhere). Trees go north to south, so a crown
    covers the trunk of the tree behind it, and so on for every object."""
    sign = np.array(Image.open(SRC / 'elements/cherrygrove-sign-cell.png').convert('RGB'))
    for sx, sy in SIGNS:
        bottom[sy * 16:sy * 16 + 16, sx * 16:sx * 16 + 16] = sign
    owner = np.full(bottom.shape[:2], '', object)
    shared = np.zeros(bottom.shape[:2] + (4,), np.uint8)       # the Center, exact palette
    shared_src = np.zeros(bottom.shape[:2], np.uint8)           # 2 Center
    tree = cherry_tree(tex)
    place.order, place.layers = {}, {}
    def record(name, sl, mask, px):
        lay = np.zeros(top.shape, np.uint8)
        lay[sl][mask] = px[mask]
        place.layers[name] = lay
        place.order[name] = len(place.order)
    # Painter's order: every object by its base row (the bottom of its sprite), then west to
    # east, so whatever stands further south is drawn in front.
    items = [(f'tree_{n}', tree, tx * 16, (ty + 2) * 16 - tree.shape[0])
             for n, (tx, ty) in enumerate(sorted(trees, key=lambda t: (t[1], t[0])))] + objects()
    for name, img, X, Y in sorted(items, key=lambda it: (it[3] + it[1].shape[0], it[2])):
        h, w = img.shape[:2]
        a = img[..., 3] > 0
        y0 = max(0, -Y)
        sl = np.s_[Y + y0:Y + h, X:X + w]
        a = a[y0:]; img = img[y0:]
        if name == 'pokemon_center':
            shared[sl][a] = img[a]
            shared_src[sl][a] = 2
            owner[sl][a] = name
            continue
        top[sl][a] = img[a]
        owner[sl][a] = name
        record(name, sl, a, img)
    return owner, shared, shared_src

# --------------------------------------------------------------------------- compose
def primary_check(engine):
    sys.path.insert(0, str(HERE))
    import pack as P
    tiles, pals, _, _ = P.primary(engine)
    opaque, _ = P.primary_index(tiles, pals)
    return lambda t: P.key5(t) in opaque

def compose(engine, phg, cells, trees):
    if not hasattr(ground, 'in_primary'):
        ground.in_primary = primary_check(engine)
    tex = cherry_textures()
    sw = frlg_pieces(engine)
    bottom = ground(cells, tex)
    bottom, top, level, piece = rock_frlg(cells, bottom, sw, tex)
    lg = ledges_frlg(cells, sw)
    a = lg[..., 3] > 0
    top[a] = lg[a]
    terrain_top = top.copy()
    owner, shared, shared_src = place(bottom, top, cells, tex, trees)
    flatten(bottom, top, owner, terrain_top, place.order)
    return bottom, top, level, piece, owner, shared, shared_src

# Objects whose sprites share one set of colours (sprites.py's palette groups; every tree is
# Cherrygrove's tree) may share a top-layer tile.
FAMILIES = dict(tree='tree', souvenir_shop='house', east_house='house', tower_west='tower', tower_east='tower',
                antenna_tree='tower', gym='gym', gate='gate')

def family(name):
    return FAMILIES[name.rstrip('0123456789').rstrip('_')]

def flatten(bottom, top, owner, terrain_top, order):
    """One palette bank per 8x8 tile: where a tile's top layer holds things from different
    colour families (a crown over a cliff, a roof over a crown), only the frontmost family
    (whatever is drawn last, and its kin) stays on the top layer; the rock overlay and every
    object behind it are composited into the opaque bottom layer, so each layer's tile takes
    its colours from one ramp. The picture is unchanged."""
    behind = np.zeros(top.shape, np.uint8)                  # what the top layer covered, per pixel
    behind[..., :3] = bottom
    for ty in range(H * 2):
        for tx in range(W * 2):
            sl = np.s_[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            names = set(owner[sl][top[sl][..., 3] > 0].ravel().tolist()) - {''}
            rock = (terrain_top[sl][..., 3] > 0).any()
            fams = {family(n) for n in names}
            if not names or (len(fams) == 1 and not rock):
                continue
            front_fam = family(max(names, key=order.get))
            front = {n for n in names if family(n) == front_fam}
            keep = np.isin(owner[sl], list(front)) & (top[sl][..., 3] > 0)
            pic = bottom[sl].copy()
            a = terrain_top[sl][..., 3] > 0
            pic[a] = terrain_top[sl][..., :3][a]
            for n in sorted(names - front, key=order.get):
                lay = place.layers[n][sl]
                a = lay[..., 3] > 0
                pic[a] = lay[..., :3][a]
            bottom[sl] = pic
            top[sl][~keep] = 0
            owner[sl][~keep] = ''
            flatten.count = getattr(flatten, 'count', 0) + 1

def preview(bottom, top, shared=None):
    out = bottom.copy()
    a = top[..., 3] > 0
    out[a] = top[..., :3][a]
    if shared is not None:
        a = shared[..., 3] > 0
        out[a] = shared[..., :3][a]
    return out

def main(engine, phg):
    cells = ledger(phg)
    trees = tree_footprints(cells)
    save_ledger(cells, trees)
    (EV / 'elements').mkdir(parents=True, exist_ok=True)
    bottom, top, level, piece, owner, shared, shared_src = compose(engine, phg, cells, trees)
    np.savez_compressed(SRC / 'elements' / 'compose-C.npz', bottom=bottom, top=top, shared=shared, shared_src=shared_src,
                        owner=owner.astype(str), level=level, piece=piece.astype(str))
    Image.fromarray(preview(bottom, top, shared)).save(EV / 'elements' / 'terrain-C.png')
    print('trees', len(trees), 'ground configurations borrowed', sum(ground.missing.values()))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
