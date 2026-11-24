"""Compose Fuchsia City (KantoFuchsiaCity): HGSS's Fuchsia as Gen 3 elements, in two layers.

    python3 tools/gba/maps/fuchsia_city/compose.py ENGINE_CHECKOUT

Follows the approved plan (gba/maps/plans/KantoFuchsiaCity.md) and the owner's answers of 2026-11-23:
plain HGSS Fuchsia, no story changes yet; the Mart is the one Saffron uses (FireRed's).

    lawn         FireRed's grass (general_frlg 0x001, tufts 0x008/0x009)
    pen lawn     FireRed's pale lawn and its own edge pieces (general_frlg 0x0BD-0x0CF), on the cells HGSS
                 draws with grass02
    road         HGSS's sek_fe03 at its own size in the world's phase; where it meets grass, FireRed's path
                 pieces quadrant by quadrant (grass and rim over the road), one 16 px quadrant of the texture
                 under them
    pens, ponds, rock, ledges, fences   FireRed's pieces in HGSS's colours, placed cell by cell from the
                 ledger (elements.py); nothing is copied from an HGSS render
    trees        Cherrygrove's tree (clear background) on every root in trees.json
    flowers      FireRed's flower (0x004), red and white, on HGSS's flower cells
    buildings    each HGSS model's sprite (sprites.py), the owner-locked C06 Center, FireRed's Mart; top layer
    signs        HGSS's sign models; top layer

Writes source/compose/compose.npz (bottom RGB, top RGBA) and evidence/compose.png, compare.png.
"""
from __future__ import annotations
import json, sys, zlib
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
import metatiles as MT                                    # noqa: E402
import elements as EL                                     # noqa: E402

ART = ROOT / 'gba/art/kanto-fuchsia'
SRC, EV = ART / 'source', ART / 'evidence'
W = H = 64

def grid():
    rows = [l[6:] for l in (SRC / 'trace/material-grid.txt').read_text().splitlines() if l[:3].isdigit()]
    assert len(rows) == H and all(len(r) == W for r in rows)
    return rows

def frlg(engine):
    E = Path(engine) / 'data/tilesets'
    return MT.Tileset(E / 'primary/general_frlg', E / 'secondary/fuchsia_city_frlg', None, 640, 7, 640)

def hsh(*a):
    return zlib.crc32(repr(a).encode())

# ------------------------------------------------------------------ FireRed's 9-piece edges, by quadrant
def piece_for(inside, x, y, qx, qy):
    dx, dy = (-1 if qx == 0 else 1), (-1 if qy == 0 else 1)
    h, v, d = inside(x + dx, y), inside(x, y + dy), inside(x + dx, y + dy)
    if h and v and d: return 'c'
    if h and v: return {(-1, -1): 'in_tl', (1, -1): 'in_tr', (-1, 1): 'in_bl', (1, 1): 'in_br'}[(dx, dy)]
    if h: return 't' if dy < 0 else 'b'
    if v: return 'l' if dx < 0 else 'r'
    return {(-1, -1): 'tl', (1, -1): 'tr', (-1, 1): 'bl', (1, 1): 'br'}[(dx, dy)]

PALE = dict(tl=0xBD, t=0xBE, tr=0xBF, l=0xC5, c=0xC6, r=0xC7, bl=0xCD, b=0xCE, br=0xCF)
PATH = dict(tl=0xD0, t=0xD1, tr=0xD2, l=0xD8, c=0xD9, r=0xDA, bl=0xE0, b=0xE1, br=0xE2, in_br=0x107, in_bl=0x106)

def quads(y, x, qy, qx):
    return (np.s_[y * 16 + qy * 8:y * 16 + qy * 8 + 8, x * 16 + qx * 8:x * 16 + qx * 8 + 8], np.s_[qy * 8:qy * 8 + 8, qx * 8:qx * 8 + 8])

# ------------------------------------------------------------------ the ground
from elements import GROUND, TREE, PEN, ROCK, FENCE       # bottom-layer palette families  # noqa: E402
ROAD_Q = (0, 0)                                           # the 16 px quadrant of sek_fe03 under an edge

def ground(engine):
    g = grid()
    ts = frlg(engine)
    px = lambda m: ts.meta(m)[..., :3]
    tex = np.load(SRC / 'hgss/textures.npz')
    out = np.zeros((H * 16, W * 16, 3), np.uint8)
    z = np.load(SRC / 'hgss/hgss-ground-materials.npz')
    names = [str(n) for n in z['names']]
    mat = z['material']
    # lawn
    for y in range(H):
        for x in range(W):
            k = hsh('tuft', x, y) % 12
            out[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = px(0x008 if k == 0 and g[y][x] in 'gu' else 0x009 if k == 1 and g[y][x] in 'gu' else 0x001)
    # pen lawn: the cells HGSS draws mostly with grass02, and what stands on them
    pale_ids = [names.index(n) for n in ('grass02', 'grass02_r', 'grass02_a')]
    pale = np.zeros((H, W), bool)
    for y in range(H):
        for x in range(W):
            pale[y, x] = np.isin(mat[y * 16:y * 16 + 16, x * 16:x * 16 + 16], pale_ids).mean() >= 0.5
    for _ in range(8):
        for y in range(20, 33):
            for x in range(10, 52):
                if not pale[y, x] and g[y][x] in 'hbp~isX' and (pale[y - 1, x] + pale[y + 1, x] + pale[y, x - 1] + pale[y, x + 1]) >= 1:
                    pale[y, x] = True
    for y in range(20, 33):                              # the cells under a hedge post's top are pen lawn too
        for x in range(10, 52):
            if not pale[y, x] and g[y][x] == 'l' and int(pale[y - 1, x]) + int(pale[y + 1, x]) + int(pale[y, x - 1]) + int(pale[y, x + 1]) >= 3:
                pale[y, x] = True
    road = np.array([[c in 'd' or (c == 'w' and x > 50) for x, c in enumerate(r)] for r in g])
    solid = np.array([[c in 'HDCX' for c in r] for r in g])
    pale &= ~road
    ins = lambda x, y: (not (0 <= x < W and 0 <= y < H)) or bool(pale[y, x] or road[y, x] or (solid[y, x] and 20 <= y <= 32))
    pieces = {k: px(v) for k, v in PALE.items()}
    for y in range(H):
        for x in range(W):
            if pale[y, x]:
                for qy in (0, 1):
                    for qx in (0, 1):
                        k = piece_for(ins, x, y, qx, qy)
                        d, s = quads(y, x, qy, qx)
                        out[d] = pieces['c' if k.startswith('in_') else k][s]
    grass_px = out.copy()
    # road
    t = tex['sek_fe03'][..., :3][:, :32]                  # half the texture's width: its stones read the same, half the tiles
    full = np.tile(t, (H * 16 // t.shape[0] + 1, W * 16 // t.shape[1] + 1, 1))[:H * 16, :W * 16]
    edge = np.tile(t[ROAD_Q[1] * 16:ROAD_Q[1] * 16 + 16, ROAD_Q[0] * 16:ROAD_Q[0] * 16 + 16], (H, W, 1))
    pp = {k: px(v) for k, v in PATH.items()}
    pp['in_tr'], pp['in_tl'] = pp['in_br'][::-1].copy(), pp['in_bl'][::-1].copy()
    dirt = {tuple(c) for c in pp['c'].reshape(-1, 3).tolist()}
    gr = {tuple(c) for m in (0x001, 0x008, 0x009) for c in px(m).reshape(-1, 3).tolist()}
    cls = {}
    for k, img in pp.items():
        cl = np.full((16, 16), 2, np.uint8)
        for yy in range(16):
            for xx in range(16):
                c = tuple(img[yy, xx].tolist())
                cl[yy, xx] = 0 if c in dirt and c not in gr else 1 if c in gr else 2
        cls[k] = cl
    rin = lambda x, y: (not (0 <= x < W and 0 <= y < H)) or bool(road[y, x] or solid[y, x] or g[y][x] == 'w')
    for y in range(H):
        for x in range(W):
            if not road[y, x]:
                continue
            ks = [[piece_for(rin, x, y, qx, qy) for qx in (0, 1)] for qy in (0, 1)]
            inner = all(k == 'c' for r in ks for k in r)
            for qy in (0, 1):
                for qx in (0, 1):
                    k = ks[qy][qx]
                    d, s = quads(y, x, qy, qx)
                    cl = cls[k][s]
                    out[d][cl == 0] = (full if k == 'c' else edge)[d][cl == 0]
                    if k != 'c':
                        out[d][cl == 1] = grass_px[d][cl == 1]
                        out[d][cl == 2] = pp[k][s][cl == 2]
    # flowers
    fl = ts.meta(0x004)
    key = gr
    fa = fl.copy()
    for yy in range(16):
        for xx in range(16):
            if tuple(fa[yy, xx, :3].tolist()) in key:
                fa[yy, xx, 3] = 0
    white = fa.copy()
    rgb = fa[..., :3].astype(int)
    petal = (fa[..., 3] > 0) & (rgb[..., 0] > rgb[..., 1] + 40) & (rgb[..., 0] > 120)
    cols = sorted({tuple(c) for c in rgb[petal].tolist()}, key=lambda c: -(3 * c[0] + 4 * c[1] + 2 * c[2]))
    ramp = [(255, 255, 255), (231, 231, 239), (181, 181, 198)]
    for i, c in enumerate(cols):
        white[petal & np.all(rgb == c, -1), :3] = ramp[min(i * 3 // max(1, len(cols)), 2)]
    orange = fa.copy()
    oramp = [(255, 189, 132), (239, 148, 107), (198, 99, 74)]                 # HGSS's bed flowers
    for i, c in enumerate(cols):
        orange[petal & np.all(rgb == c, -1), :3] = oramp[min(i * 3 // max(1, len(cols)), 2)]
    pink = fa.copy()
    pramp = [(255, 132, 189), (231, 82, 148), (173, 49, 123)]                 # flower_sp1's pinks
    for i, c in enumerate(cols):
        pink[petal & np.all(rgb == c, -1), :3] = pramp[min(i * 3 // max(1, len(cols)), 2)]
    kinds = (orange, white, pink)
    pick = lambda x, y: hsh('fl', x, y) % 2
    for y in range(H):
        for x in range(W):
            if g[y][x] == 'f':
                f = kinds[pick(x, y)]
                d = out[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
                d[f[..., 3] > 0] = f[..., :3][f[..., 3] > 0]
    # what stands on the ground, each a Gen 3 piece on its HGSS cells (elements.py)
    fam = np.zeros((H * 16, W * 16), np.uint8)
    EL.terrain(out, fam, EL.Pieces(ts, tex), g, kinds, pick)
    return out, fam

# ------------------------------------------------------------------ what stands
def put(dst, img, X, Y, depth=None, foot=0):
    h, w = img.shape[:2]
    y0, x0, y1, x1 = max(Y, 0), max(X, 0), min(Y + h, dst.shape[0]), min(X + w, dst.shape[1])
    if y1 <= y0 or x1 <= x0:
        return
    part = img[y0 - Y:y1 - Y, x0 - X:x1 - X]
    m = part[..., 3] > 0
    sl = dst[y0:y1, x0:x1]
    sl[..., :3][m] = part[..., :3][m]
    if dst.shape[-1] == 4:
        sl[..., 3][m] = 255
    if depth is not None:
        depth[y0:y1, x0:x1][m] = foot

MIRRORED = ('hall', 'gym', 'route15_gate', 'house_pink')

# name, sprite, left edge (px), the row its foot stands on
def places(engine):
    B = SRC / 'local-art/buildings'
    load = lambda n: np.array(Image.open(B / f'{n}.png').convert('RGBA'))
    obj = json.loads((SRC / 'trace/objects.json').read_text())['models']
    def at(model, nth=0):
        return [o for o in obj if o['model'] == model][nth]['footprint']
    def centred(name, model, nth=0, dx=0, row=None):
        img = load(name)
        x0, z0, x1, z1 = at(model, nth)
        if name in MIRRORED:                                  # a symmetric model: its left half, mirrored, the axis on a tile edge
            half = img[:, :(img.shape[1] + 1) // 2]
            img = np.concatenate([half, half[:, ::-1]], 1)
            X = int(round((x0 + x1) * 8 / 8)) * 8 - img.shape[1] // 2 + dx
            pad = (-img.shape[0]) % 8
            return (name, np.concatenate([np.zeros((pad, img.shape[1], 4), np.uint8), img], 0), X, int(round(z1)) - 1 if row is None else row)
        X = int(round((x0 + x1) * 8 - img.shape[1] / 2)) + dx
        return (name if nth == 0 else f'{name}_{nth}', img, X, int(round(z1)) - 1 if row is None else row)
    out = [centred('hall', 295), centred('gym', 300), centred('house_red', 297), centred('house_pink', 298, 0),
           centred('house_pink', 298, 1), centred('warden_house', 299), centred('route15_gate', 247),
           centred('city_sign', 29), centred('notice_board', 31), centred('gym_sign', 33), centred('house_sign', 30)]
    c06 = np.array(Image.open(ROOT / 'gba/art/johto-center/source/building.png').convert('RGBA'))
    out.append(('pokemon_center', c06, 23 * 16, 55))          # 5x5, door tile (2, 4) on HGSS's Center door (25, 55)
    ts = frlg(engine)
    mart = np.concatenate([np.concatenate([ts.meta(m) for m in r], 1) for r in
                           ((0x28, 0x29, 0x2A, 0x2B), (0x30, 0x31, 0x32, 0x33), (0x38, 0x39, 0x3A, 0x3B), (0x40, 0x41, 0x62, 0x63))], 0)
    mart[..., 3] = 255
    out.append(('mart', mart, 11 * 16, 32))                   # FireRed's Mart, its door (cell 2 of 4) on HGSS's (13, 32)
    return out

def compose(engine):
    bottom, fam = ground(engine)
    top = np.zeros((H * 16, W * 16, 4), np.uint8)
    tfam = np.zeros((H * 16, W * 16), np.uint8)
    names = []
    depth = np.full((H * 16, W * 16), -1, np.int32)
    tree = np.array(Image.open(ROOT / 'gba/art/cherrygrove-synthesis/refined/tree.png').convert('RGBA'))
    tree[..., 3] = np.where(tree[..., 3] >= 128, 255, 0)
    lamp = np.array(Image.open(SRC / 'local-art/buildings/lamp.png').convert('RGBA'))
    items = []
    roots = {tuple(r) for r in json.loads((SRC / 'trace/trees.json').read_text())['roots']}
    between = {(x + 1, y + 1) for x, y in roots if {(x + 2, y), (x, y + 2), (x + 2, y + 2)} <= roots}   # the staggered rows
    for x, y in sorted(roots | between):
        items.append((y + 1, 0, 'tree', tree, x * 16, (y + 2) * 16 - tree.shape[0]))
    for o in json.loads((SRC / 'trace/objects.json').read_text())['models']:
        if o['model'] == 333:
            x0, z0, x1, z1 = o['footprint']
            items.append((int(z0), 0, 'lamp', lamp, int(round((x0 + x1) * 8 - lamp.shape[1] / 2)), int(z0) * 16 + 16 - lamp.shape[0]))
    for name, img, X, row in places(engine):
        items.append((row, 1, name, img, X, (row + 1) * 16 - img.shape[0]))
    for row, kind, name, img, X, Y in sorted(items, key=lambda i: (i[0], i[1], i[4])):
        if kind:
            base = name.rsplit('_', 1)[0] if name[-1].isdigit() else name
            if base not in names:
                names.append(base)
            before = top[..., 3].copy()
            put(top, img, X, Y, depth, row)
            h, w = img.shape[:2]
            y0, x0, y1, x1 = max(Y, 0), max(X, 0), min(Y + h, H * 16), min(X + w, W * 16)
            tfam[y0:y1, x0:x1][img[y0 - Y:y1 - Y, x0 - X:x1 - X, 3] > 0] = names.index(base) + 1
        else:                                               # a tree or lamp in front of a building is drawn over it
            h, w = img.shape[:2]
            y0, x0, y1, x1 = max(Y, 0), max(X, 0), min(Y + h, H * 16), min(X + w, W * 16)
            part = img[y0 - Y:y1 - Y, x0 - X:x1 - X]
            m = part[..., 3] > 0
            over = m & (top[y0:y1, x0:x1, 3] > 0) & (depth[y0:y1, x0:x1] < row)
            under = m & ~(top[y0:y1, x0:x1, 3] > 0)
            bottom[y0:y1, x0:x1][under | over] = part[..., :3][under | over]
            fam[y0:y1, x0:x1][under | over] = TREE if name == 'tree' else FENCE
            top[y0:y1, x0:x1, :3][over] = part[..., :3][over]
    return bottom, top, fam, tfam, names

def main(engine):
    bottom, top, fam, tfam, names = compose(engine)
    (SRC / 'compose').mkdir(parents=True, exist_ok=True)
    np.savez_compressed(SRC / 'compose/compose.npz', bottom=bottom, top=top, fam=fam, tfam=tfam, names=np.array(names))
    pic = bottom.copy()
    m = top[..., 3] > 0
    pic[m] = top[..., :3][m]
    Image.fromarray(pic).save(EV / 'compose.png')
    hg = np.array(Image.open(SRC / 'hgss/hgss-render.png').convert('RGB'))
    Image.fromarray(np.concatenate([hg, np.zeros((H * 16, 8, 3), np.uint8), pic], 1)).save(EV / 'compare.png')
    tiles = set()
    for layer in (bottom, top):
        for y in range(0, H * 16, 8):
            for x in range(0, W * 16, 8):
                t = layer[y:y + 8, x:x + 8]
                if layer.shape[-1] == 4 and not t[..., 3].any():
                    continue
                v = [t, t[:, ::-1], t[::-1], t[::-1, ::-1]]
                tiles.add(min(a.tobytes() for a in v))
    print('unique 8x8 tiles (flips folded, before palettes):', len(tiles))
    g = grid(); by = {}
    for li, layer in enumerate((bottom, top)):
        for y in range(0, H * 16, 8):
            for x in range(0, W * 16, 8):
                t = layer[y:y + 8, x:x + 8]
                if layer.shape[-1] == 4 and not t[..., 3].any():
                    continue
                by.setdefault(('top ' if li else 'bot ') + g[y // 16][x // 16], set()).add(min(a.tobytes() for a in (t, t[:, ::-1], t[::-1], t[::-1, ::-1])))
    print({k: len(v) for k, v in sorted(by.items(), key=lambda kv: -len(kv[1]))})

if __name__ == '__main__':
    main(sys.argv[1])
