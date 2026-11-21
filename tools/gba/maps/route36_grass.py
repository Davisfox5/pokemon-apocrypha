#!/usr/bin/env python3
"""Route 36's tall grass in the Johto standard (owner-approved 2026-11-21, docs/maps/JOHTO_ELEMENT_STANDARDS.md):
the hand-drawn G3 tile, rounded patch corners, a wavy edge, blade tips on top.

    python3 tools/gba/maps/route36_grass.py PATH/TO/pokeemerald-expansion [--write]

Run after route36_ridge.py. Route 36 has no generator, so this patches the map and its secondary tileset in place,
with route36_ridge's writer. The picture is standards/johto_tall_grass.restyle(): only pixels inside tall-grass
cells change, carved pixels take the neighbouring ground. Each changed cell gets a new secondary metatile: the
picture on the bottom layer, and the cell's old top layer kept wherever it still shows (tree crowns over the
grass stay above the player). Collision and behaviour are the old cell's.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / 'standards')]
import route36_ridge as R                    # noqa: E402
import johto_tall_grass as TG                # noqa: E402
from tiles import Tileset                    # noqa: E402

OUT = R.ROOT / 'gba/art/route36-grass'
GRASS = {tuple(int(v) >> 3 << 3 for v in c) for c in TG.P.values()} | R.LAWN

def top_layer(t, m):
    """RGBA 16x16 of metatile m's top layer."""
    out = np.zeros((16, 16, 4), np.uint8)
    e8 = t.blocks[m >= 512][m - 512 if m >= 512 else m]
    for q in range(4):
        e = e8[4 + q]; tid = e & 1023; bank = e >> 12
        tl = t.tiles[tid >= 512]; idx = tid - 512 if tid >= 512 else tid
        if idx >= len(tl):
            continue
        a = np.array(tl[idx], np.uint8).reshape(8, 8) % 16
        if e & 1024: a = a[:, ::-1]
        if e & 2048: a = a[::-1]
        pal = t.pals[bank >= 6][bank]
        for y in range(8):
            for x in range(8):
                if a[y, x]:
                    out[(q // 2) * 8 + y, (q % 2) * 8 + x, :3] = pal[a[y, x]][:3]
                    out[(q // 2) * 8 + y, (q % 2) * 8 + x, 3] = 255
    return out

def plan(engine):
    t = Tileset(engine, R.TS, R.TS)
    words = np.frombuffer((Path(engine) / f'data/layouts/{R.LAYOUT}/map.bin').read_bytes(), '<u2').reshape(-1, R.W).astype(np.int64)
    img = np.array(t.map_image([int(v) for v in words.ravel()], R.W).convert('RGB'))
    old, new, tg = TG.restyle(engine, R.LAYOUT)
    new = new.astype(np.uint8)
    assert old.shape == img.shape and (old >> 3 == img >> 3).all(), 'restyle read a different picture'
    tile = TG.parse(TG.TILE)
    cells = sorted({(x, r) for r, x in zip(*np.nonzero(tg))
                    if (new[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16] != img[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16]).any()},
                   key=lambda c: (c[1], c[0]))
    pals = {b: [R.rgb5(c) for c in t.pals[b >= 6][b]] for b in range(13)}
    lookup, used = {}, {b: {0} for b in range(13)}
    for part in range(2):
        for e8 in t.blocks[part]:
            for e in e8:
                tid = e & 1023
                tl = t.tiles[tid >= 512]; idx = tid - 512 if tid >= 512 else tid
                if idx < len(tl):
                    a = np.array(tl[idx], np.uint8).reshape(8, 8) % 16
                    lookup.setdefault((e >> 12, a.tobytes()), tid)
                    if (e >> 12) < 13:
                        used[e >> 12] |= set(int(v) for v in a.ravel())
    free = {b: [i for i in range(1, 16) if i not in used[b]] for b in range(13)}
    added, new_tiles, snapped = {}, [], []

    def entry(px, mask):
        if not mask.any():
            return 0
        cs = {R.rgb5(p) for p in px[mask]}
        bank = next((b for b in range(13) if cs <= set(pals[b][1:])), None)
        if bank is None:
            fits = [(len(cs - set(pals[b][1:])), b) for b in range(13) if len(cs - set(pals[b][1:])) <= len(free[b])]
            if fits:
                bank = min(fits)[1]
                for c in sorted(cs - set(pals[bank][1:])):
                    slot = free[bank].pop(0); pals[bank][slot] = c; added.setdefault(bank, []).append(slot)
            else:
                # Grass against sand: no bank holds the grass greens and the sand together. The grass bank (the
                # one holding most of the grass) takes the quadrant; a grass colour it lacks goes in a free slot,
                # and each sand tone it lacks is drawn with its nearest sand tone (the darker sand of the lawn's rim).
                bank = max(range(13), key=lambda b: (len(cs & GRASS & set(pals[b][1:])), len(free[b])))
                for c in sorted((cs & GRASS) - set(pals[bank][1:])):
                    assert free[bank], ('no slot for a grass colour', c)
                    slot = free[bank].pop(0); pals[bank][slot] = c; added.setdefault(bank, []).append(slot)
                for c in cs - set(pals[bank][1:]):
                    near = min(pals[bank][1:], key=lambda q: sum(abs(a - b) for a, b in zip(q, c)))
                    snapped.append((c, near))
                    for y in range(8):
                        for x in range(8):
                            if mask[y, x] and R.rgb5(px[y, x]) == c:
                                px[y, x] = near
        idx = np.zeros((8, 8), np.uint8)
        for y in range(8):
            for x in range(8):
                if mask[y, x]:
                    idx[y, x] = pals[bank].index(R.rgb5(px[y, x]), 1)
        for (h, v), f in R.flips(idx).items():
            hit = lookup.get((bank, f.tobytes()))
            if hit is not None:
                return (hit, bank, h, v)
        new_tiles.append((bank, idx))
        lookup[(bank, idx.tobytes())] = ('new', len(new_tiles) - 1)
        return (('new', len(new_tiles) - 1), bank, 0, 0)

    metas = []
    for x, r in cells:
        m = int(words[r, x]) & 1023
        pic = new[r * 16:(r + 1) * 16, x * 16:(x + 1) * 16]
        top = top_layer(t, m)
        keep = (top[..., 3] > 0) & ((top[..., :3] >> 3) == (pic >> 3)).all(-1)
        top[~keep] = 0
        # under a kept crown pixel the grass tile goes on (unseen; it keeps the bottom layer one texture)
        bottom = np.where(keep[..., None], tile[(np.arange(16)[:, None] + r * 16) % 16, (np.arange(16)[None] + x * 16) % 16], pic)
        bottom = bottom.astype(np.uint8).copy()
        ents = []
        for q in range(4):
            s = np.s_[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            ents.append(entry(bottom[s], np.ones((8, 8), bool)))
        for q in range(4):
            s = np.s_[(q // 2) * 8:(q // 2) * 8 + 8, (q % 2) * 8:(q % 2) * 8 + 8]
            ents.append(entry(top[s][..., :3], top[s][..., 3] > 0))
        pic[:] = np.where(top[..., 3:] > 0, top[..., :3], bottom)       # any colour the banks forced
        metas.append(((x, r), m, ents))
    from collections import Counter
    print('snapped', Counter(snapped).most_common())
    return t, words, img, new, cells, metas, new_tiles, (pals, added)

def main():
    engine = Path(sys.argv[1]).resolve()
    t, words, img, new, cells, metas, new_tiles, palplan = plan(engine)
    OUT.mkdir(parents=True, exist_ok=True)
    print('cells', len(cells), 'new tiles', len(new_tiles), 'palette slots added', palplan[1])
    Image.fromarray(new).save(OUT / 'plan.png')
    if '--write' in sys.argv:
        tid_of, ids = R.write(engine, t, words, metas, new_tiles, palplan)
        print('tiles', len(tid_of), 'metatiles', ids[0], '-', ids[-1], 'count', len(ids))
        t2 = Tileset(engine, R.TS, R.TS)
        got = np.array(t2.map_image([int(v) for v in words.ravel()], R.W).convert('RGB'))
        print('pixels off the plan', int(((got >> 3) != (new >> 3)).any(-1).sum()))
        Image.fromarray(np.concatenate([img, np.full((8, img.shape[1], 3), 255, np.uint8), got])).save(OUT / 'before-after.png')

if __name__ == '__main__':
    main()
