#!/usr/bin/env python3
"""Paint a 32x160 Route 32 target image from canonical HGSS tiles.

Source: the HGSS overview rectified to 16 px tiles (vertical scale 1.28; the overview is a
perspective shot with 12.5 px rows). World mapping: world col = image col + 1, world row =
image row - 5. Canonical tiles are built per label signature and 2x2 phase: mean for ground,
grass, path, water and deck families (denoises the resample), medoid for forest, exact pixels
for rock and structures. HGSS object positions remove NPC and item sprites.
Usage: paint.py OUT_DIR
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT/'gba/art/route32-hgss-blocks/source'
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
W, H = 32, 160
# HGSS zone_event 033_R32 objects (world x, z) minus chunk origin (448, 288); sprites cover (x, z-1..z)
OBJECTS = [(23, 24), (29, 17), (14, 32), (22, 41), (18, 54), (13, 86), (15, 88), (20, 99), (4, 97), (12, 115), (14, 128), (20, 145), (8, 49), (11, 94), (23, 121), (23, 151), (3, 113), (27, 151), (20, 111)]
MEAN_FAMILIES = set('.PGWDS_')

def main():
    im = Image.open(SRC/'hgss-reference.png').convert('RGB'); w, h = im.size
    rect = np.array(im.resize((w, int(round(h*1.28))), Image.LANCZOS)).astype(float)
    lab = np.load(SRC/'hgss-material-pixel-labels.npy')
    labr = np.array(Image.fromarray(np.vectorize(ord)(lab).astype(np.uint8)).resize((480, rect.shape[0]), Image.NEAREST))
    labr = np.vectorize(chr)(labr)
    # world canvases
    T = np.zeros((H*16, W*16, 3), float); L = np.full((H*16, W*16), 'N')
    # image px (ix, iy) -> world px (ix+16, iy-80)
    ys0, ys1 = 80, min(rect.shape[0], 80+H*16)
    T[0:ys1-ys0, 16:16+490] = rect[ys0:ys1, :490]; L[0:ys1-ys0, 16:16+480] = labr[ys0:ys1, :480]
    # columns 0 and 31 (31 partly) and rows past the overview: mirror neighbours
    T[:, 0:16] = T[:, 16:32][:, ::-1]; L[:, 0:16] = L[:, 16:32][:, ::-1]
    T[:, 506:512] = T[:, 500:506][:, ::-1]; L[:, 506:512] = L[:, 500:506][:, ::-1]
    L[:, 496:512][L[:, 496:512] == 'N'] = 'W'
    last = ys1-ys0
    if last < H*16: T[last:] = T[last-16:last][::-1].repeat(1, 0)[: H*16-last] if False else np.tile(T[last-16:last], ((H*16-last)//16+1, 1, 1))[:H*16-last]; L[last:] = np.tile(L[last-16:last], ((H*16-last)//16+1, 1))[:H*16-last]
    # ---- sprite removal: object squares take the nearest square with the same label signature
    def sig(blk):
        s = []
        for i in range(4):
            for j in range(4):
                v, n = np.unique(blk[i*4:i*4+4, j*4:j*4+4], return_counts=True); s.append(str(v[n.argmax()]))
        return ''.join(s)
    sprite_cells = set()
    for x, z in OBJECTS:
        for zz in (z-1, z):
            if 0 <= zz < H: sprite_cells.add((x, zz))
    sigs = {}
    for z in range(H):
        for x in range(W):
            sigs[(x, z)] = sig(L[z*16:z*16+16, x*16:x*16+16])
    def donor(x, z):
        want = sigs[(x, z)]
        for r in range(1, 40):
            for dz in range(-r, r+1):
                for dx in range(-r, r+1):
                    if max(abs(dx), abs(dz)) != r: continue
                    xx, zz = x+dx, z+dz
                    if (xx, zz) in sprite_cells or not (0 <= xx < W and 0 <= zz < H): continue
                    if sigs[(xx, zz)] == want and (xx-x) % 2 == 0 and (zz-z) % 2 == 0: return xx, zz
        return None
    replaced = []
    for (x, z) in sorted(sprite_cells):
        d = donor(x, z)
        if d:
            xx, zz = d; T[z*16:z*16+16, x*16:x*16+16] = T[zz*16:zz*16+16, xx*16:xx*16+16]; replaced.append([x, z, xx, zz])
    # ---- canonical tiles
    groups = {}
    for z in range(H):
        for x in range(W):
            if (x, z) in sprite_cells: continue
            groups.setdefault((sigs[(x, z)], x % 2, z % 2), []).append((x, z))
    canon = {}; kinds = {}
    for key, cells in groups.items():
        s = key[0]; fam = set(s)
        px = np.array([T[z*16:z*16+16, x*16:x*16+16] for x, z in cells])
        if fam <= MEAN_FAMILIES and len(cells) >= 2:
            canon[key] = px.mean(0); kinds[key] = 'mean'
        elif fam == {'T'} or (fam <= {'T', '.', 'G', 'P'} and 'T' in fam and len(cells) >= 3):
            m = px.mean(0); d = np.abs(px-m).mean((1, 2, 3)); canon[key] = px[d.argmin()]; kinds[key] = 'medoid'
        else:
            canon[key] = None; kinds[key] = 'exact'
    # ---- paint
    P = T.copy(); cells = []
    for z in range(H):
        for x in range(W):
            key = (sigs[(x, z)], x % 2, z % 2); c = canon.get(key)
            if c is not None: P[z*16:z*16+16, x*16:x*16+16] = c
            cells.append({'x': x, 'z': z, 'sig': key[0], 'kind': kinds.get(key, 'exact')})
    Image.fromarray(np.clip(P, 0, 255).astype(np.uint8)).save(OUT/'target-160.png')
    Image.fromarray(np.clip(T, 0, 255).astype(np.uint8)).save(OUT/'rectified-world-160.png')
    json.dump({'cells': cells, 'sprites_replaced': replaced, 'canonical_tiles': len([k for k, v in canon.items() if v is not None]), 'exact_cells': sum(1 for c in cells if c['kind'] == 'exact')}, open(OUT/'paint.json', 'w'))
    from collections import Counter
    print('canonical keys', len(groups), 'kinds', Counter(kinds.values()), 'exact cells', sum(1 for c in cells if c['kind'] == 'exact'), 'sprites replaced', len(replaced))

if __name__ == '__main__': main()
