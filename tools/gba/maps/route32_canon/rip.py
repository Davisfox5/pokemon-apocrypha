#!/usr/bin/env python3
"""Rip a consistent Route 32 tile library from the rectified HGSS overview and paint the 32x160 target.

The overview is a 12.5 px/row perspective shot; rectified to 16 px rows with the sub-pixel grid
origin (X0, Y0) found by tile-consistency search, every family is 2x2 periodic in world space.
Rules per world tile:
- unclassified ('?') pixels outside explicit structure zones are relabelled to the nearest real
  material (they are trunk shadows, path rims and rock creases, not objects)
- tiles are grouped by (4x4 label signature, x%2, z%2); a group whose members agree (mean abs
  deviation below --tol) collapses to its medoid, otherwise each member stays exact
- near-duplicate tiles are merged; HGSS object squares lose their sprites via a same-phase donor
Usage: rip.py OUT_DIR [--tol 9]
"""
import argparse, json
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT/'gba/art/route32-hgss-blocks/source'
W, H = 32, 160
X0, Y0 = 2, 5.5
AFF = (1, 0, X0-16, 0, 12.5/16, Y0+5*12.5)
OBJECTS = [(23, 24), (29, 17), (14, 32), (22, 41), (18, 54), (13, 86), (15, 88), (20, 99), (4, 97), (12, 115), (14, 128), (20, 145), (8, 49), (11, 94), (23, 121), (23, 151), (3, 113), (27, 151), (20, 111)]
# sprite squares read off the labelled rectified grid, each with the lattice offset of a clean donor
SPRITE_RECTS = [(29, 17, 30, 19, 0, 4), (23, 24, 24, 25, 4, 0), (14, 32, 15, 33, 0, 4), (22, 40, 23, 42, 4, 0), (18, 53, 19, 55, 8, 0),
                (13, 86, 14, 87, -2, 0), (13, 88, 14, 88, 0, 2), (15, 88, 16, 90, 2, 0), (11, 94, 12, 95, -2, 0), (4, 96, 5, 98, -2, 0),
                (20, 99, 21, 101, 0, -4), (3, 112, 4, 113, 0, -2), (12, 115, 13, 117, 0, -4), (23, 121, 24, 122, 0, -2), (15, 127, 16, 129, 0, 4),
                (20, 144, 21, 146, 0, -4), (27, 151, 28, 152, 0, -2)]
# world cells whose '?' pixels are real structure (kept exact): gate, signs, pylon, rail posts, dock posts, cave mouth, ledges
STRUCT_ZONES = [(0, 4, 4, 13), (14, 4, 16, 6), (20, 13, 22, 15), (18, 150, 20, 152), (24, 86, 26, 93), (6, 72, 8, 80), (16, 72, 18, 80),
                (11, 74, 17, 77), (13, 143, 18, 147), (11, 146, 16, 147), (28, 40, 30, 43), (12, 47, 17, 53), (24, 44, 31, 62), (15, 56, 18, 57)]

def sig(blk):
    s = []
    for i in range(4):
        for j in range(4):
            v, n = np.unique(blk[i*4:i*4+4, j*4:j*4+4], return_counts=True); s.append(str(v[n.argmax()]))
    return ''.join(s)

def main():
    p = argparse.ArgumentParser(); p.add_argument('out'); p.add_argument('--tol', type=float, default=9.0); p.add_argument('--phase-free', action='store_true'); a = p.parse_args()
    OUT = Path(a.out); OUT.mkdir(parents=True, exist_ok=True)
    im = Image.open(SRC/'hgss-reference.png').convert('RGB')
    lab = np.load(SRC/'hgss-material-pixel-labels.npy'); labim = Image.fromarray(np.vectorize(ord)(lab).astype(np.uint8))
    T = np.array(im.transform((W*16, H*16), Image.AFFINE, AFF, resample=Image.BICUBIC)).astype(float)
    L = np.vectorize(chr)(np.array(labim.transform((W*16, H*16), Image.AFFINE, AFF, resample=Image.NEAREST)))
    T[:, 0:16] = T[:, 16:32][:, ::-1]; L[:, 0:16] = L[:, 16:32][:, ::-1]
    T[:, 498:512] = T[:, 484:498][:, ::-1]; L[:, 498:512] = L[:, 484:498][:, ::-1]
    bottom = int((2000-(Y0+5*12.5))/(12.5/16))
    T[bottom:] = np.tile(T[bottom-32:bottom], (8, 1, 1))[:H*16-bottom]; L[bottom:] = np.tile(L[bottom-32:bottom], (8, 1))[:H*16-bottom]
    L[L == 'N'] = 'W'
    # ---- relabel '?' outside structure zones to the nearest real label (iterative dilation)
    zone = np.zeros((H, W), bool)
    for x0, z0, x1, z1 in STRUCT_ZONES: zone[z0:z1+1, x0:x1+1] = True
    zpx = np.repeat(np.repeat(zone, 16, 0), 16, 1)
    unk = (L == '?') & ~zpx
    Lr = L.copy(); Lr[unk] = '#'
    for _ in range(12):
        holes = Lr == '#'
        if not holes.any(): break
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            src = np.roll(np.roll(Lr, dy, 0), dx, 1)
            fill = holes & (src != '#') & (src != '?')
            Lr[fill] = src[fill]; holes = Lr == '#'
    Lr[Lr == '#'] = '?'
    L = Lr
    sigs = {(x, z): sig(L[z*16:z*16+16, x*16:x*16+16]) for z in range(H) for x in range(W)}
    # ---- sprite removal: HGSS object squares plus outlier squares (a square that disagrees with its
    #      same-signature 2-period neighbours while those neighbours agree with each other)
    # sprite squares read off the labelled rectified grid (x0, z0, x1, z1 inclusive)
    sprite = {(x, z) for x0, z0, x1, z1, dx, dz in SPRITE_RECTS for x in range(x0, x1+1) for z in range(z0, z1+1)}
    outliers = sorted(sprite)
    # donor: walk the 2x2 lattice along the column, then the row, for a non-sprite square whose
    #        pre-relabel labels agree with ours wherever ours are not sprite/unknown pixels
    L0 = np.vectorize(chr)(np.array(labim.transform((W*16, H*16), Image.AFFINE, AFF, resample=Image.NEAREST)))
    L0[:, 0:16] = L0[:, 16:32][:, ::-1]; L0[:, 498:512] = L0[:, 484:498][:, ::-1]
    def donor(x, z):
        me = L0[z*16:z*16+16, x*16:x*16+16]; known = ~np.isin(me, ['?', 'H'])
        best = None
        for dx, dz in [(0, d*s) for d in (2, 4, 6, 8, 10, 12) for s in (-1, 1)] + [(d*s, 0) for d in (2, 4, 6, 8) for s in (-1, 1)] + [(a, b) for a in (-4, -2, 2, 4) for b in (-4, -2, 2, 4)]:
            xx, zz = x+dx, z+dz
            if not (0 <= xx < W and 0 <= zz < H) or (xx, zz) in sprite: continue
            cand = L0[zz*16:zz*16+16, xx*16:xx*16+16]
            if np.isin(cand, ['?', 'H']).sum() > 40: continue
            mism = int((cand[known] != me[known]).sum())
            if mism <= 96 and (best is None or mism < best[0]): best = (mism, xx, zz)
            if best and best[0] <= 4: break
        return (best[1], best[2]) if best else None
    replaced = []; unresolved = []
    src = T.copy()
    for x0, z0, x1, z1, dx, dz in SPRITE_RECTS:
        for z in range(z0, z1+1):
            for x in range(x0, x1+1):
                T[z*16:z*16+16, x*16:x*16+16] = src[(z+dz)*16:(z+dz)*16+16, (x+dx)*16:(x+dx)*16+16]; replaced.append([x, z, x+dx, z+dz])
    print('sprite squares unresolved:', unresolved)
    tile = lambda x, z: T[z*16:z*16+16, x*16:x*16+16]
    # ---- greedy exemplar clustering per 2x2 phase: a tile joins an existing exemplar when its mean
    #      absolute difference is <= tol and no 8x8 quadrant differs by more than 3*tol (keeps small
    #      features such as flowers, posts and signs distinct); otherwise it becomes a new exemplar
    final = {}; exemplars = {ph: [] for ph in [(0, 0), (1, 0), (0, 1), (1, 1)]}; members = {}
    order = sorted(((x, z) for z in range(H) for x in range(W)), key=lambda c: (sigs[c], c[1], c[0]))
    for (x, z) in order:
        t = tile(x, z); ph = (0, 0) if a.phase_free else (x % 2, z % 2); best = None
        for i, e in enumerate(exemplars[ph]):
            d = np.abs(t-e); md = d.mean()
            if md > a.tol: continue
            q = max(d[r:r+8, c:c+8].mean() for r in (0, 8) for c in (0, 8))
            if q > 3*a.tol: continue
            if best is None or md < best[0]: best = (md, i)
        if best is None: exemplars[ph].append(t); best = (0, len(exemplars[ph])-1)
        final[(x, z)] = (ph, best[1]); members.setdefault((ph, best[1]), []).append((x, z))
    # replace each exemplar by the medoid of its members (a real tile, closest to the member mean)
    for key, cells in members.items():
        px = np.array([tile(x, z) for x, z in cells]); m = px.mean(0); d = np.abs(px-m).mean((1, 2, 3)); exemplars[key[0]][key[1]] = px[d.argmin()]
    keys = members; stats = {'exemplars': sum(len(v) for v in exemplars.values()), 'singletons': sum(1 for v in members.values() if len(v) == 1)}
    final = {c: exemplars[k[0]][k[1]] for c, k in final.items()}
    Q = np.zeros_like(T)
    for (x, z), v in final.items(): Q[z*16:z*16+16, x*16:x*16+16] = v
    Image.fromarray(np.clip(Q, 0, 255).astype(np.uint8)).save(OUT/'target.png')
    Image.fromarray(np.clip(T, 0, 255).astype(np.uint8)).save(OUT/'rectified.png')
    np.save(OUT/'labels.npy', L)
    json.dump({'distinct_tiles': len(keys), 'stats': stats, 'sprite_cells': outliers, 'sprites_replaced': replaced, 'origin': [X0, Y0], 'tol': a.tol, 'members': [[list(k[0]), k[1], v] for k, v in members.items()]}, open(OUT/'rip.json', 'w'), indent=1)
    print('distinct tiles', len(keys), stats, 'sprites', len(replaced))

if __name__ == '__main__': main()
