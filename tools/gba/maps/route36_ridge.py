#!/usr/bin/env python3
"""Route 36's thin ridge, second owner pass on #39: softened outer corners, a real corner south of the west
crossing, and both crossings redrawn falling west at the Gen 3 angle.

    python3 tools/gba/maps/route36_ridge.py PATH/TO/pokeemerald-expansion [--write]

Run after route36_stairs.py (it reads the installed map). Route 36 has no generator, so this patches the map and
its secondary tileset in place. Only the ridge, its stairs and the stair's old shadow change:

- Outer corners: the protruding corners stay square in shape but lose their sharp point. Ridge pixels of the
  corner square beyond a small arc (radius 4-5 px) become lawn and the band's outline follows the arc. Nothing
  else in the cell changes.
- The corner south of the west crossing: the vertical band used to stop on top of the horizontal band's square
  end, so the two only crossed. The vertical band now runs on through the end of the horizontal band with its
  outline carried down (as the jog above the east crossing does) and the outer corner softened.
- The stairs (columns 14 and 32, rows 20-24): east of each crossing is the higher path, so both flights fall
  west. Slope 3/4 (johto_stairs.east_west, slope=0.75) instead of the kit's 45 degrees, and each flight's high
  end is centred on the east path so the low end runs into the west path below. The ridge runs on under the
  flight. The old flight's cast shadow on the lawn east of the ridge (3 px) goes.

Every changed cell gets a new secondary metatile. Ridge cells: lawn on the bottom layer, the ridge on top, as
the route's ridge cells split them. Stair cells: everything on the bottom layer (the player walks over them).
Collision and behaviour are the old cell's. Tiles are deduplicated with flips against the whole tileset; the
door-frame slots (secondary 1008-1023) stay free. Without --write it saves before/after previews.
"""
from __future__ import annotations
import math, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from tiles import Tileset                    # noqa: E402
import johto_stairs as JS                    # noqa: E402

TS = 'johto_route36'
LAYOUT = 'JohtoRoute36'
W = 82
ROOT = HERE.parents[2]
OUT = ROOT / 'gba/art/route36-ridge'
LAWN = {(104, 208, 152), (104, 200, 152), (96, 192, 144), (88, 176, 136)}
RIDGE = {(80, 56, 64), (88, 80, 72), (96, 64, 48), (104, 72, 56), (104, 96, 88), (120, 88, 64), (128, 96, 80),
         (136, 96, 96), (136, 104, 80), (160, 120, 96)}
RIDGE_BODY = (202, 204)                      # ridge cells by row parity (even row: 202)
SLOPE = 0.75
# (column, west path centre y, east path centre y), in map pixels
CROSSINGS = ((14, 371, 352), (32, 363, 350))
STAIR_ROWS = range(20, 25)
SHADOW = 3                                   # px of old cast shadow east of each crossing, rows 369-384
SHADE = {(88, 176, 136), (96, 192, 144)}     # the lawn's shadow tones

def rgb5(c):
    return tuple(int(v) >> 3 << 3 for v in c)

def is_ridge(p):
    return tuple(int(v) for v in p) in RIDGE

def redraw(img, t):
    """The map picture with the ridge edits applied."""
    im = img.astype(int)
    out = im.copy()
    ref = im[0:32, 384:416]                  # a plain lawn block (the lawn texture's 32 px cycle)
    lawn = lambda x, y: ref[y % 32, x % 32]

    def soften(cx, cy, sx, sy, r, edge):
        """Outer corner pixel (cx, cy); sx, sy point out of the band. Ridge pixels of the corner beyond a
        radius-r arc become lawn, and the band's outline (edge: outermost first) is laid along the arc."""
        ox, oy = cx - sx * (r - 1), cy - sy * (r - 1)
        for k in range(r + 2):
            for j in range(r + 2):
                x, y = cx - sx * j, cy - sy * k
                if (x - ox) * sx < 0 or (y - oy) * sy < 0:
                    continue
                d = math.hypot(x - ox, y - oy)
                if not is_ridge(out[y, x]):
                    continue
                if d > r - 0.5:
                    out[y, x] = lawn(x, y)
                elif d > r - 2.5:
                    out[y, x] = edge[min(int(r - 0.5 - d), len(edge) - 1)]

    # Protruding corners. Each band's outline is read off a straight stretch of the same band.
    soften(254, 51, 1, -1, 5, [im[120, 253 - i] for i in range(3)])     # north-west double ridge
    soften(510, 227, 1, -1, 4, [im[120, 253 - i] for i in range(3)])    # the jog above the east crossing
    soften(526, 259, 1, -1, 4, [im[120, 253 - i] for i in range(3)])
    soften(144, 400, -1, -1, 4, [im[460, 144 + i] for i in range(3)])   # south-west corner
    # South of the west crossing: the vertical band (x 224-237) runs on through rows 400-412, its right outline
    # down the horizontal band's end, the old square end cleared, the new outer corner softened.
    for y in range(400, 403):
        for x in range(224, 238):
            out[y, x] = im[396 - (402 - y) % 3, x]
    for y in range(400, 413):
        for x in (236, 237):
            out[y, x] = im[380 + (y % 8), x]
        for x in (238, 239):
            if is_ridge(out[y, x]):
                out[y, x] = lawn(x, y)
    soften(237, 413, 1, 1, 4, [im[380, 237 - i] for i in range(3)])

    # Stairs.
    for col, west_c, east_c in CROSSINGS:
        x0 = col * 16
        c = np.zeros((80, 16, 4), np.uint8)
        for i, r in enumerate(STAIR_ROWS):
            c[i * 16:(i + 1) * 16, :, :3] = np.array(t.render(RIDGE_BODY[r % 2]))
        c[..., 3] = 255
        band = np.zeros_like(c)
        top = int(round(east_c - JS.TREAD_PX / 2)) - STAIR_ROWS[0] * 16
        JS.east_west(band, 0, top, 'W', phase=0, slope=SLOPE)
        m = band[..., 3] > 0
        # As route36_stairs.column_art: a kit colour within one 5-bit step of a ridge colour takes the ridge's.
        ridge = {rgb5(p) for p in c[..., :3].reshape(-1, 3)}
        for k in {rgb5(p) for p in band[m][:, :3]}:
            near = min(ridge, key=lambda q: sum(abs(a - b) for a, b in zip(q, k)))
            if k not in ridge and sum(abs(a - b) for a, b in zip(near, k)) <= 16:
                hit = m & (np.abs(band[..., :3].astype(int) - np.array(k)) < 8).all(-1)
                band[hit, :3] = near
        c[m] = band[m]
        out[STAIR_ROWS[0] * 16:(STAIR_ROWS[-1] + 1) * 16, x0:x0 + 16] = c[..., :3]
        # The old flight's cast shadow on the lawn east of the ridge: a 3 px strip of path-edge grey down the
        # ridge, and a dark lawn band running down-left from under the east path. The path's own bottom edge
        # (to row 370) stays.
        for y in range(369, 385):
            for x in range(x0 + 16, x0 + 16 + SHADOW):
                if tuple(out[y, x]) not in LAWN:
                    out[y, x] = lawn(x, y)
        for y in range(371, 392):
            for x in range(x0 + 16, x0 + 28):
                if tuple(out[y, x]) in SHADE:
                    out[y, x] = lawn(x, y)
    return out.astype(np.uint8)

def flips(a):
    return {(0, 0): a, (1, 0): a[:, ::-1], (0, 1): a[::-1], (1, 1): a[::-1, ::-1]}

def plan(engine):
    t = Tileset(engine, TS, TS)
    words = np.frombuffer((Path(engine) / f'data/layouts/{LAYOUT}/map.bin').read_bytes(), '<u2').reshape(-1, W).astype(np.int64)
    img = np.array(t.map_image([int(v) for v in words.ravel()], W).convert('RGB'))
    new = redraw(img, t)
    diff = (new != img).any(-1)
    cells = {(int(x) // 16, int(y) // 16) for y, x in zip(*np.nonzero(diff))}
    stairs = {(col, r) for col, _, _ in CROSSINGS for r in STAIR_ROWS}
    cells = sorted(cells | stairs, key=lambda c: (c[1], c[0]))
    pals = {b: [rgb5(c) for c in t.pals[b >= 6][b]] for b in range(13)}
    lookup = {}
    for part in range(2):
        for e8 in t.blocks[part]:
            for e in e8:
                tid = e & 1023
                tl = t.tiles[tid >= 512]; idx = tid - 512 if tid >= 512 else tid
                if idx < len(tl):
                    a = np.array(tl[idx], np.uint8).reshape(8, 8) % 16
                    lookup.setdefault((e >> 12, a.tobytes()), tid)
    used = {b: {0} for b in range(13)}
    for part in range(2):
        for e8 in t.blocks[part]:
            for e in e8:
                tid = e & 1023
                tl = t.tiles[tid >= 512]; idx = tid - 512 if tid >= 512 else tid
                if idx < len(tl) and (e >> 12) < 13:
                    used[e >> 12] |= {v % 16 for v in tl[idx]}
    free = {b: [i for i in range(1, 16) if i not in used[b]] for b in range(13)}
    added = {}
    new_tiles = []

    def entry(px, mask):
        if not mask.any():
            return 0
        cs = {rgb5(p) for p in px[mask]}
        bank = next((b for b in range(13) if cs <= set(pals[b][1:])), None)
        if bank is None:
            # the bank that needs fewest new colours and has the free slots for them takes them
            fits = [(len(cs - set(pals[b][1:])), b) for b in range(13) if len(cs - set(pals[b][1:])) <= len(free[b])]
            if fits:
                bank = min(fits)[1]
                for c in sorted(cs - set(pals[bank][1:])):
                    slot = free[bank].pop(0); pals[bank][slot] = c; added.setdefault(bank, []).append(slot)
            else:
                # No free slots: the bank missing fewest colours takes the quadrant, each missing colour drawn
                # with that bank's nearest (at most one 5-bit step on one channel pair; the picture is updated).
                bank = min(range(13), key=lambda b: len(cs - set(pals[b][1:])))
                for c in cs - set(pals[bank][1:]):
                    near = min(pals[bank][1:], key=lambda q: sum(abs(a - b) for a, b in zip(q, c)))
                    assert sum(abs(a - b) for a, b in zip(near, c)) <= 24, ('no bank holds', sorted(cs))
                    for y in range(8):
                        for x in range(8):
                            if mask[y, x] and rgb5(px[y, x]) == c:
                                px[y, x] = near
                cs = {rgb5(p) for p in px[mask]}
        idx = np.zeros((8, 8), np.uint8)
        for y in range(8):
            for x in range(8):
                if mask[y, x]:
                    idx[y, x] = pals[bank].index(rgb5(px[y, x]), 1)
        for (h, v), f in flips(idx).items():
            hit = lookup.get((bank, f.tobytes()))
            if hit is not None:
                return (hit, bank, h, v)
        new_tiles.append((bank, idx))
        lookup[(bank, idx.tobytes())] = ('new', len(new_tiles) - 1)
        return (('new', len(new_tiles) - 1), bank, 0, 0)

    ref = img[0:32, 384:416]
    metas = []
    for x, r in cells:
        m = int(words[r, x]) & 1023
        pic = new[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16]
        if (x, r) in stairs:
            bottom = pic; top = np.zeros((16, 16, 4), np.uint8)
        else:
            grass = ~np.array([[is_ridge(p) for p in row] for row in pic])
            bottom = np.where(grass[..., None], pic, ref[(np.arange(16)[:, None] + r * 16) % 32, (np.arange(16)[None] + x * 16) % 32])
            top = np.zeros((16, 16, 4), np.uint8); top[..., :3] = pic; top[..., 3] = np.where(grass, 0, 255)
        ents = []
        for q in range(4):
            s = np.s_[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            ents.append(entry(bottom[s], np.ones((8, 8), bool)))
        for q in range(4):
            s = np.s_[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            ents.append(entry(top[s][..., :3], top[s][..., 3] > 0))
        pic[:] = np.where(top[..., 3:] > 0, top[..., :3], bottom)       # any colour the banks forced
        metas.append(((x, r), m, ents))
    return t, words, img, new, cells, metas, new_tiles, (pals, added)

def write(engine, t, words, metas, new_tiles, palplan):
    base = Path(engine) / 'data/tilesets'
    used = {e & 1023 for part in range(2) for e8 in t.blocks[part] for e in e8}
    sec = Image.open(base / 'secondary' / TS / 'tiles.png'); prim = Image.open(base / 'primary' / TS / 'tiles.png')
    n_sec = sec.width // 8 * (sec.height // 8)
    # secondary 1008-1023 are the door frames' (field_door.c: NUM_TILES_TOTAL - 16)
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

    pals, added = palplan
    for b, slots_ in added.items():
        part = 'primary' if b < 6 else 'secondary'
        p = base / part / TS / 'palettes' / f'{b:02}.pal'
        raw = p.read_bytes().decode()
        nl = '\r\n' if '\r\n' in raw else '\n'
        lines = raw.splitlines()
        for slot in slots_:
            lines[3 + slot] = '%d %d %d' % pals[b][slot]
        p.write_bytes((nl.join(lines) + nl).encode())

    def fix(e):
        if isinstance(e, int):
            return e
        ref, bank, h, v = e
        tid = tid_of[ref[1]] if isinstance(ref, tuple) else ref
        return tid | (h << 10) | (v << 11) | (bank << 12)
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
    (Path(engine) / f'data/layouts/{LAYOUT}/map.bin').write_bytes(words.astype('<u2').tobytes())
    return tid_of, sorted(set(ids.values()))

def main():
    engine = Path(sys.argv[1]).resolve()
    t, words, img, new, cells, metas, new_tiles, palplan = plan(engine)
    OUT.mkdir(parents=True, exist_ok=True)
    print('cells', len(cells), 'new tiles', len(new_tiles), 'palette slots added', palplan[1])
    Image.fromarray(new).save(OUT / 'plan.png')
    if '--write' in sys.argv:
        tid_of, ids = write(engine, t, words, metas, new_tiles, palplan)
        print('tiles at', tid_of[:4], '...', len(tid_of), 'metatiles', ids[0], '-', ids[-1])
        t2 = Tileset(engine, TS, TS)
        got = np.array(t2.map_image([int(v) for v in words.ravel()], W).convert('RGB'))
        print('pixels off the plan', int(((got >> 3) != (new >> 3)).any(-1).sum()))
        Image.fromarray(np.concatenate([img, np.full((8, img.shape[1], 3), 255, np.uint8), got])).save(OUT / 'before-after.png')

if __name__ == '__main__':
    main()
