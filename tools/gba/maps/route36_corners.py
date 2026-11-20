#!/usr/bin/env python3
"""Route 36's ridge corners rounded (owner review of #39: "rock ledge corners: adjust and smooth").

    python3 tools/gba/maps/route36_corners.py PATH/TO/pokeemerald-expansion [--write]

Route 36 has no generator in this repo, so this patches its tileset and map in place, after route36_stairs.py.

The thin ridge's three corners are redrawn as round bends: the north-west double ridge, the jog above the east
crossing (one bend, then the leg eases a cell east over the blocked cells), and the south-west corner. A bend is
the straight band carried round a quarter circle: each pixel at distance d from the bend's centre takes the band's
cross-section at d minus the inner radius, its texture read along the arc from the straight band it continues
(the west-running band above the diagonal, the south-running band below it). Old band pixels outside the bend
become the route's lawn. Trees are never touched (only the ridge's own colours in large connected runs move).

Each changed cell gets a new secondary metatile: the lawn (and any tree crown pixels) on the bottom layer, the
ridge on the top layer, as the route's own ridge cells split them; the picture is the same pixel for pixel. Collision and behaviour are the old cell's.
Tiles are deduplicated (with flips) against the whole tileset and written into free slots; every quadrant takes
a bank that already holds its colours. Without --write it saves before/after previews to gba/art/route36-corners/.
"""
from __future__ import annotations
import math, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from tiles import Tileset                    # noqa: E402

TS = 'johto_route36'
W = 82
ROOT = HERE.parents[2]
OUT = ROOT / 'gba/art/route36-corners'
LAWN = {(104, 208, 152), (104, 200, 152), (96, 192, 144), (88, 176, 136)}
is_lawn = lambda p: tuple(int(v) for v in p) in LAWN

def bend(out, src, cx, cy, a, th, H, V, lawn_at, clear=(), band=None):
    """In `out`: an outer corner, the band running west above C (cx, cy) and south right of it, bent round C at
    inner radius a, thickness th. H(t, s), V(t, s): the straight bands' colour at cross position t (0 at the
    inner edge) and along position s."""
    R = a + th
    for y in range(cy - R - 3, cy + 1):
        for x in range(cx, cx + R + 4):
            p = out[y, x]
            if not (band[y, x] or is_lawn(p)):
                continue
            dx, dy = x - cx + 0.5, cy - y - 0.5
            d = math.hypot(dx, dy)
            if a <= d < R:
                t = int(d - a); ang = math.atan2(dy, dx)
                rm = a + th / 2
                out[y, x] = H(t, int(round((math.pi / 2 - ang) * rm))) if ang >= math.pi / 4 else V(t, int(round(ang * rm)))
            else:
                out[y, x] = lawn_at(x, y)

RIDGE = {(80, 56, 64), (88, 80, 72), (96, 64, 48), (104, 72, 56), (104, 96, 88), (120, 88, 64), (128, 96, 80),
         (136, 96, 96), (136, 104, 80), (160, 120, 96)}
def ridge_mask(img):
    from scipy.ndimage import label
    m = np.zeros(img.shape[:2], bool)
    for c in RIDGE:
        m |= (img == c).all(-1)
    lab, n = label(m)
    sizes = np.bincount(lab.ravel())
    return m & (sizes[lab] > 40)

def bend(out, src, cx, cy, a, th, H, V, lawn_at, clear=(), band=None):
    """In `out` (and reading textures from `src`): an outer corner, the band running west above C and south
    right of C, bent round C at inner radius a. Cells of `clear` (x0,y0,x1,y1) lose their old band first."""
    for x0, y0, x1, y1 in clear:
        for y in range(y0, y1):
            for x in range(x0, x1):
                if band[y, x]: out[y, x] = lawn_at(x, y)
    R = a + th
    for y in range(cy - R - 3, cy + 1):
        for x in range(cx, cx + R + 4):
            p = out[y, x]
            if not (band[y, x] or is_lawn(p)): continue
            dx, dy = x - cx + 0.5, cy - y - 0.5
            d = math.hypot(dx, dy)
            if a <= d < R:
                t = int(d - a); ang = math.atan2(dy, dx)
                rm = a + th / 2
                out[y, x] = H(t, int(round((math.pi / 2 - ang) * rm))) if ang >= math.pi / 4 else V(t, int(round(ang * rm)))
            else:
                out[y, x] = lawn_at(x, y)

def corners(img):
    """Route 36's map picture with its three ridge corners rounded."""
    im = img.astype(int); out = im.copy(); band = ridge_mask(im)
    W = im.shape[1]
    ref = im[0:32, 384:416]
    lawn = lambda x, y: ref[y % 32, x % 32]
    # 1: the double ridge north-west: horizontal rows 51-79 (inner edge 80), vertical x 224-253 (inner 224)
    a, th = 12, 30; cx, cy = 224 - a, 80 + a
    bend(out, im, cx, cy, a, th, lambda t, s: im[79 - t, 128 + (-s % 32)],
         lambda t, s: im[cy + 40 + s % 32, 224 + t], lawn, band=band)
    # 2: the single ridge's jog. The band (horizontal y 227-239, inner edge 240) bends south round x 496 (the
    # old leg's inner edge), then its leg eases east by a cell, smoothly, to the col-32 leg (x 512-524) by row 17 (y 272), where the leg's cells are blocked.
    a, th = 10, 13; cx, cy = 496 - a, 240 + a
    for y in range(238, 300):
        for x in range(486, 530):
            if (band[y, x] and (x < 512 or y < 272)) or (is_lawn(out[y, x]) and x < 512): out[y, x] = lawn(x, y)
    bend(out, im, cx, cy, a, th, lambda t, s: im[239 - t, 400 + (-s % 32)],
         lambda t, s: im[300 + s % 32, 512 + t], lawn, band=band)
    for y in range(cy, 272):
        u = (y - cy) / (272 - cy); off = 496 + 16 * (3 * u * u - 2 * u * u * u)
        for t in range(th):
            x = int(round(off)) + t
            if band[y, x] or is_lawn(out[y, x]):
                out[y, x] = im[300 + (y - cy) % 32, 512 + t]
    # 3: the south-west corner, mirrored: band east along y 400-413 (inner 414), south along x 144-156 (inner 157)
    f = out[:, ::-1].copy(); fi = im[:, ::-1]
    fx = lambda x: W - 1 - x
    a, th = 10, 14; cx, cy = fx(156) - a, 414 + a
    bend(f, fi, cx, cy, a, th, lambda t, s: fi[413 - t, fx(200) + (-s % 32)],
         lambda t, s: fi[450 + s % 32, fx(156) + t], lambda x, y: ref[y % 32, (W - 1 - x) % 32], band=band[:, ::-1])
    out = f[:, ::-1]
    return out.astype(np.uint8)


def layer(t, m, which):
    """RGBA 16x16 of one layer of metatile m."""
    out = np.zeros((16, 16, 4), np.uint8)
    ents = t.blocks[m >= 512][m - 512 if m >= 512 else m]
    for q in range(4):
        e = ents[which * 4 + q]; tid = e & 1023; bank = e >> 12
        tiles = t.tiles[tid >= 512]; idx = tid - 512 if tid >= 512 else tid
        if idx >= len(tiles):
            continue
        cols = t.pals[bank >= 6][bank]
        for y in range(8):
            for x in range(8):
                v = tiles[idx][(7 - y if e & 2048 else y) * 8 + (7 - x if e & 1024 else x)] % 16
                if v:
                    out[(q // 2) * 8 + y, (q % 2) * 8 + x, :3] = cols[v]; out[(q // 2) * 8 + y, (q % 2) * 8 + x, 3] = 255
    return out

def flips(a):
    return {(0, 0): a, (1, 0): a[:, ::-1], (0, 1): a[::-1], (1, 1): a[::-1, ::-1]}

def plan(engine):
    t = Tileset(engine, TS, TS)
    words = np.frombuffer((Path(engine) / 'data/layouts/JohtoRoute36/map.bin').read_bytes(), '<u2').reshape(-1, W).astype(np.int64)
    img = np.array(t.map_image([int(v) for v in words.ravel()], W).convert('RGB'))
    new = corners(img)
    diff = (new != img).any(-1)
    cells = sorted({(int(x) // 16, int(y) // 16) for y, x in zip(*np.nonzero(diff))}, key=lambda c: (c[1], c[0]))
    rgb5 = lambda c: tuple(int(v) >> 3 << 3 for v in c)
    pals = {b: [rgb5(c) for c in t.pals[b >= 6][b]] for b in range(13)}
    # every existing tile by content (index map) and bank, for reuse
    lookup = {}
    for part in range(2):
        for i, e8 in enumerate(t.blocks[part]):
            for e in e8:
                tid = e & 1023
                tl = t.tiles[tid >= 512]; idx = tid - 512 if tid >= 512 else tid
                if idx < len(tl):
                    a = np.array(tl[idx], np.uint8).reshape(8, 8) % 16
                    lookup.setdefault((e >> 12, a.tobytes()), tid)
    new_tiles = []                                   # (bank, index map)
    def entry(px, mask):
        """One 8x8 layer quadrant (RGB, opaque mask) -> metatile entry."""
        if not mask.any():
            return 0
        cs = {rgb5(p) for p in px[mask]}
        bank = next((b for b in range(13) if cs <= set(pals[b][1:])), None)
        assert bank is not None, ('no bank holds', sorted(cs))
        idx = np.zeros((8, 8), np.uint8)
        for y in range(8):
            for x in range(8):
                if mask[y, x]:
                    idx[y, x] = pals[bank].index(rgb5(px[y, x]), 1)
        for (h, v), f in flips(idx).items():
            hit = lookup.get((bank, f.tobytes()))
            if hit is not None:
                return hit | (h << 10) | (v << 11) | (bank << 12)
        new_tiles.append((bank, idx)); key = ('new', len(new_tiles) - 1)
        lookup[(bank, idx.tobytes())] = key
        return key, bank
    ref = img[0:32, 384:416]                          # a plain lawn block (the lawn texture's 32 px cycle)
    metas = []                                        # (cell, old id, 8 entries)
    for x, r in cells:
        m = int(words[r, x]) & 1023
        sl = np.s_[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16]
        pic = new[sl]
        grass = ~np.array([[tuple(int(v) for v in p) in RIDGE for p in row] for row in pic])   # lawn and tree pixels
        bottom = np.where(grass[..., None], pic, ref[(np.arange(16)[:, None] + r * 16) % 32, (np.arange(16)[None] + x * 16) % 32])
        top = np.zeros((16, 16, 4), np.uint8); top[..., :3] = pic; top[..., 3] = np.where(grass, 0, 255)
        ents = []
        for q in range(4):
            s = np.s_[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            ents.append(entry(bottom[s], np.ones((8, 8), bool)))
        for q in range(4):
            s = np.s_[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            ents.append(entry(top[s][..., :3], top[s][..., 3] > 0))
        metas.append(((x, r), m, ents))
    return t, words, img, new, cells, metas, new_tiles

def write(engine, t, words, metas, new_tiles):
    base = Path(engine) / 'data/tilesets'
    used = {e & 1023 for part in range(2) for e8 in t.blocks[part] for e in e8}
    sec = Image.open(base / 'secondary' / TS / 'tiles.png'); prim = Image.open(base / 'primary' / TS / 'tiles.png')
    n_sec = sec.width // 8 * (sec.height // 8)
    # the secondary's last 16 slots are the door frames' (field_door.c: NUM_TILES_TOTAL - 16)
    slots = [512 + k for k in range(496) if 512 + k not in used and k < n_sec] + [512 + k for k in range(n_sec, 496)] \
        + [k for k in range(1, 512) if k not in used]
    assert len(new_tiles) <= len(slots), (len(new_tiles), len(slots))
    tid_of = slots[:len(new_tiles)]
    sa, pa = np.array(sec), np.array(prim)
    need = max([(k - 512) // 16 + 1 for k in tid_of if k >= 512] + [sa.shape[0] // 8])
    if need * 8 > sa.shape[0]:
        sa = np.concatenate([sa, np.zeros((need * 8 - sa.shape[0], sa.shape[1]), sa.dtype)])
    for (b, idx), tid in zip(new_tiles, tid_of):
        sheet, k = (sa, tid - 512) if tid >= 512 else (pa, tid)
        sheet[(k // 16) * 8:(k // 16) * 8 + 8, (k % 16) * 8:(k % 16) * 8 + 8] = idx
    for arr, part, src in ((sa, 'secondary', sec), (pa, 'primary', prim)):
        if part == 'primary' and not any(k < 512 for k in tid_of):
            continue
        o = Image.fromarray(arr, 'P'); o.putpalette(src.getpalette()); o.save(base / part / TS / 'tiles.png')
    fix = lambda e: e if isinstance(e, int) else tid_of[e[0][1]] | (e[1] << 12)
    mt = base / 'secondary' / TS / 'metatiles.bin'; at = base / 'secondary' / TS / 'metatile_attributes.bin'
    mdata, adata = bytearray(mt.read_bytes()), bytearray(at.read_bytes())
    ids = {}
    for (x, r), m, ents in metas:
        e8 = tuple(fix(e) for e in ents)
        attr = t.attrs[m >= 512][m - 512 if m >= 512 else m]
        key = (e8, attr)
        if key not in ids:
            ids[key] = 512 + len(mdata) // 16
            mdata += struct.pack('<8H', *e8); adata += struct.pack('<H', attr)
        words[r, x] = (int(words[r, x]) & ~1023) | ids[key]
    assert len(mdata) // 16 <= 512
    mt.write_bytes(bytes(mdata)); at.write_bytes(bytes(adata))
    (Path(engine) / 'data/layouts/JohtoRoute36/map.bin').write_bytes(words.astype('<u2').tobytes())
    return tid_of, sorted(set(ids.values()))

def main():
    engine = Path(sys.argv[1]).resolve()
    t, words, img, new, cells, metas, new_tiles = plan(engine)
    OUT.mkdir(parents=True, exist_ok=True)
    print('cells', len(cells), 'new tiles', len(new_tiles))
    if '--write' in sys.argv:
        tid_of, ids = write(engine, t, words, metas, new_tiles)
        print('tiles at', tid_of, 'metatiles', ids)
        t2 = Tileset(engine, TS, TS)
        got = np.array(t2.map_image([int(v) for v in words.ravel()], W).convert('RGB'))
        bad = ((got >> 3) != (new >> 3)).any(-1).sum()
        print('pixels off the plan', int(bad))
        Image.fromarray(np.concatenate([img, np.full((8, img.shape[1], 3), 255, np.uint8), got])).save(OUT / 'before-after.png')

if __name__ == '__main__':
    main()
