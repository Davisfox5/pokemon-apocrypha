#!/usr/bin/env python3
"""Compile the canonical 32x160 Route 32 target into native Porymap source (from-scratch method).

Inputs: a rip output dir (target.png, labels.npy) and an engine checkout at the cleanup commit
(for the approved Center prefab and Codex's collision/layering, ported by row mapping
native128_y = round((z+5)*0.78125+1)).
Palettes: k-means per material bank (Center banks 2/7/8 fixed). Glyphs: greedy exemplar
clustering with flips at a pixel tolerance, raised automatically until the budget fits.
Usage: compile.py RIP_DIR ENGINE [--tol 8]
"""
import argparse, json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parent/'route32_native_cleanup'))
import native as nat
nat.LAYOUT_H = 160
from native import Native, PRIMARY_GLYPHS, SECONDARY_GLYPHS
W, H = 32, 160
CENTER_MIDS = set(range(0x387, 0x3b9)); CENTER_BANKS = {2, 7, 8}
CENTER_SRC = (17, 103, 23, 108)          # prefab cells in the cleanup layout (plus (16,108))
CENTER_DST = (15, 125)                   # top-left of the same block in the 160 grid (door lands on (18,130))
CAVE_WARPS = [(12, 143), (13, 143)]
rng = np.random.default_rng(5)

def kmeans(X, k, iters=14):
    C = X[rng.choice(len(X), k, replace=False)].astype(float)
    for _ in range(iters):
        a = np.stack([((X-c)**2).sum(1) for c in C], 1).argmin(1)
        for j in range(k):
            m = a == j
            if m.any(): C[j] = X[m].mean(0)
    return C

def main():
    p = argparse.ArgumentParser(); p.add_argument('rip'); p.add_argument('engine'); p.add_argument('--tol', type=float, default=8); p.add_argument('--start-tol', type=float); a = p.parse_args()
    R = Path(a.rip); G = Path(a.engine)
    T = np.array(Image.open(R/'target.png').convert('RGB')).astype(float); L = np.load(R/'labels.npy')
    # ---- source engine state (cleanup commit): 128-row layout, used for the Center prefab and collision port
    old = np.fromfile(G/'data/layouts/JohtoRoute32/map.bin', '<u2').reshape(128, 32)
    (G/'data/layouts/JohtoRoute32/map.bin').write_bytes(np.zeros(W*H, '<u2').tobytes())
    n = Native(G)
    old_attr = lambda m: n.attr(m)
    # ---- Center prefab cells
    center = {}
    sx0, sy0, sx1, sy1 = CENTER_SRC
    for sy in range(sy0, sy1+1):
        for sx in range(sx0, sx1+1):
            m = int(old[sy, sx] & 1023)
            if m in CENTER_MIDS: center[(CENTER_DST[0]+sx-sx0, CENTER_DST[1]+sy-sy0)] = (m, int(old[sy, sx]))
    m = int(old[108, 16] & 1023)
    if m in CENTER_MIDS: center[(CENTER_DST[0]-1, CENTER_DST[1]+5)] = (m, int(old[108, 16]))
    reserved = {0} | set(range(1, 17))
    for (m, _) in center.values():
        for v in n.entries(m):
            if (v & 1023) and (v >> 12) in CENTER_BANKS: reserved.add(v & 1023)
    # ---- palettes
    fam = {'.': 'ground', 'P': 'ground', 'G': 'ground', 'S': 'ground', '_': 'ground', 'T': 'tree', 'R': 'rock', 'W': 'water', 'D': 'water', 'B': 'misc', 'H': 'misc', '?': 'misc', 'N': 'water'}
    blocks = []; blab = []; cells = []
    for z in range(H):
        for x in range(W):
            if (x, z) in center: continue
            for q in range(4):
                r0, c0 = z*16+(q//2)*8, x*16+(q % 2)*8
                blocks.append(T[r0:r0+8, c0:c0+8].reshape(-1, 3)); lb = L[r0:r0+8, c0:c0+8]
                v, c = np.unique(lb, return_counts=True); blab.append(fam.get(str(v[c.argmax()]), 'misc')); cells.append((x, z, q))
    blocks = np.array(blocks); blab = np.array(blab)
    free = [b for b in range(16) if b not in CENTER_BANKS]
    share = {'ground': 3, 'tree': 2, 'rock': 3, 'water': 2, 'misc': 3}
    assert sum(share.values()) <= len(free)
    assign = np.zeros(len(blocks), int); bi = 0; banks = []; bank_family = {}
    for g, k in share.items():
        idx = np.flatnonzero(blab == g)
        if len(idx) == 0: continue
        means = blocks[idx].mean(1); C = kmeans(means, k, 8); sub = np.stack([((means-c)**2).sum(1) for c in C], 1).argmin(1)
        for j in range(k):
            b = free[bi]; bi += 1; banks.append(b); bank_family[b] = g; assign[idx[sub == j]] = b
    pal = {b: np.array(n.bank_colors(b)[1:], float) for b in range(16)}
    for it in range(3):
        for b in banks:
            px = blocks[assign == b].reshape(-1, 3)
            if len(px) == 0: continue
            px = px[rng.choice(len(px), min(len(px), 30000), replace=False)]
            pal[b] = np.round(kmeans(px, 15, 10)/8)*8
        err = np.full((len(banks), len(blocks)), np.inf, np.float32)
        for i, b in enumerate(banks):
            C = pal[b].astype(np.float32); allowed = np.flatnonzero(blab == bank_family[b])
            for s in range(0, len(allowed), 2048):
                sel = allowed[s:s+2048]; blk = blocks[sel].astype(np.float32); err[i, sel] = ((blk[:, :, None, :]-C[None, None])**2).sum(3).min(2).mean(1)
        assign = np.array(banks)[err.argmin(0)]      # reassign only within the block's own material family
    # quantise
    qidx = np.zeros((len(blocks), 64), np.uint8); qrgb = np.zeros((len(blocks), 64, 3), np.float32)
    for b in banks:
        m = np.flatnonzero(assign == b); C = pal[b]
        for s in range(0, len(m), 2048):
            sel = m[s:s+2048]; d = ((blocks[sel][:, :, None, :]-C[None, None])**2).sum(3).argmin(2); qidx[sel] = d+1; qrgb[sel] = C[d]
    # ---- glyph clustering with flips, raising tolerance until it fits
    budget = PRIMARY_GLYPHS + SECONDARY_GLYPHS - len(reserved) - 8
    tol = a.start_tol or a.tol
    while True:
        ex = {}   # bank -> list of (idx8x8, rgb8x8)
        entry_of = np.zeros(len(blocks), int); flip_of = np.zeros((len(blocks), 2), int)
        order = np.lexsort((np.arange(len(blocks)), assign))
        for i in order:
            b = int(assign[i]); q = qrgb[i].reshape(8, 8, 3); lst = ex.setdefault(b, []); best = None
            for j, (_, e) in enumerate(lst):
                for h in (0, 1):
                    for v in (0, 1):
                        c = q[:, ::-1] if h else q; c = c[::-1] if v else c
                        dd = np.abs(c-e); d = dd.mean()
                        if d <= tol and dd.reshape(2, 4, 2, 4, 3).mean((1, 3, 4)).max() <= 1.6*tol and (best is None or d < best[0]): best = (d, j, h, v)
            if best is None: lst.append((qidx[i].reshape(8, 8), q)); best = (0, len(lst)-1, 0, 0)
            entry_of[i] = best[1]; flip_of[i] = (best[2], best[3])
        total = sum(len(v) for v in ex.values())
        print('tol', tol, 'glyphs', total, 'budget', budget, flush=True)
        if total <= budget: break
        tol += 2
    # ---- assign glyph slots
    free_slots = [g for g in range(1, PRIMARY_GLYPHS) if g not in reserved] + [512+g for g in range(SECONDARY_GLYPHS) if 512+g not in reserved]
    slot = {}
    for b, lst in ex.items():
        for j, (idx, _) in enumerate(lst):
            s = free_slots.pop(0); slot[(b, j)] = s; n.set_glyph(s, idx)
    for pi, part in enumerate(n.parts):
        for i in range(part.count):
            gid = part.base+i
            if gid not in reserved and gid not in slot.values(): part.glyphs[i] = np.zeros((8, 8), np.uint8)
    # ---- metatiles
    port_y = lambda z: min(127, max(0, int(round((z+5)*0.78125+1))))
    cell_entries = {}; cell_meta = {}
    for i, (x, z, q) in enumerate(cells):
        b = int(assign[i]); h, v = flip_of[i]
        cell_entries.setdefault((x, z), [0]*8)[q] = Native.entry(slot[(b, entry_of[i])], b, int(h), int(v))
    grid = np.zeros((H, W), '<u2'); meta_id = {}; new_blocks = {}; new_attrs = {}
    for (x, z), (m, raw) in center.items():
        new_blocks[m] = list(n.entries(m)); new_attrs[m] = n.attr(m); grid[z, x] = raw
    free_mids = [m for m in range(1, 1024) if m not in new_blocks]; overflow = False
    for z in range(H):
        for x in range(W):
            if (x, z) in center: continue
            oldv = int(old[port_y(z), x]); om = oldv & 1023; oa = old_attr(om); layer = (oa >> 12) & 3; beh = oa & 255; coll = (oldv >> 10) & 3; elev = oldv >> 12
            blk = L[z*16:z*16+16, x*16:x*16+16]; vals, cnt = np.unique(blk, return_counts=True); dom = str(vals[cnt.argmax()]); frac = cnt.max()/cnt.sum()
            # material overrides
            if dom == 'W' and frac > 0.75: coll, elev, beh, layer = 0, 1, 0x15, 1
            elif dom == 'D': coll, elev, beh, layer = 0, 3, 0, 1
            elif dom in 'RTB' and frac > 0.6 and dom != 'B' or (dom == 'B' and (x, z) not in CAVE_WARPS): coll = 3; beh = 0 if beh == 0x15 else beh; layer = 1 if layer == 1 or dom != 'T' else layer
            elif dom in '.PGS' and frac > 0.6:
                if coll == 3 and beh not in (0x3b,): coll = 0
                if beh == 0x15: beh = 0
                elev = 3 if elev in (0, 1) else elev
            layer = 0 if dom == 'H' else 1            # art under the player everywhere except beneath the railway
            if beh not in (0, 0x15, 0x3b, 0x61): beh = 0  # keep only the behaviours this map needs, so one art has one metatile
            if dom == '_': beh, coll = 0x3b, 0
            if (x, z) in CAVE_WARPS: coll, beh, elev, layer = 0, 0x61, 3, 1
            es = cell_entries[(x, z)]
            if layer == 0: entries = [0, 0, 0, 0] + es[:4]; attr = beh
            else: entries = es[:4] + [0, 0, 0, 0]; attr = (1 << 12) | beh
            k = (tuple(entries), attr)
            if k not in meta_id:
                if not free_mids:
                    print('metatile budget exceeded: distinct so far', len(meta_id), 'at cell', (x, z), flush=True); overflow = True; break
                mid = free_mids.pop(0); meta_id[k] = mid; new_blocks[mid] = list(entries); new_attrs[mid] = attr
            grid[z, x] = meta_id[k] | (coll << 10) | (elev << 12)
        if overflow: break
    if overflow:
        need = len({(tuple(cell_entries[c][:4]), ) for c in cell_entries}); print('distinct square entry tuples ignoring attr', need); raise SystemExit(3)
    # ground behind the Center prefab: Cherrygrove lawn glyphs (indices 1-4) -> HGSS lawn, path glyphs (5-7) -> HGSS path
    def pure_src(ch):
        c = [c for c in cell_entries if (L[c[1]*16:c[1]*16+16, c[0]*16:c[0]*16+16] == ch).all()]
        return cell_entries[c[0]][:4] if c else None
    lawn = [c for c in cell_entries if (L[c[1]*16:c[1]*16+16, c[0]*16:c[0]*16+16] == '.').all()]
    lawn_src, path_src = pure_src('.'), pure_src('P')
    for (m, _) in center.values():
        e = new_blocks[m]
        for q in range(4):
            if (e[q] & 1023) and (e[q] >> 12) not in CENTER_BANKS:
                idxs = set(int(v) for v in np.unique(n.glyph(e[q] & 1023))) - {0}
                e[q] = (path_src if idxs and min(idxs) >= 5 and path_src else lawn_src)[q]
            if (e[4+q] & 1023) and (e[4+q] >> 12) not in CENTER_BANKS: e[4+q] = 0
    for part in n.parts:
        for i in range(len(part.blocks)):
            mid = part.base+i
            if mid in new_blocks: part.blocks[i] = new_blocks[mid]; part.attrs[i] = new_attrs[mid]
            else: part.blocks[i] = [0]*8; part.attrs[i] = 0
    n.grid = grid
    for b in range(16):
        if b in CENTER_BANKS: continue
        txt = 'JASC-PAL\n0100\n16\n0 0 0\n' + ''.join(f'{int(c[0])} {int(c[1])} {int(c[2])}\n' for c in pal[b])
        for part in ('primary', 'secondary'): (G/f'data/tilesets/{part}/route32/palettes/{b:02}.pal').write_text(txt)
    for part in n.parts: part.pals = [part.pals[b] if b in CENTER_BANKS else [(0, 0, 0)] + [tuple(map(int, c)) for c in pal[b]] for b in range(16)]
    n.save()
    lawn_mid = meta_id[(tuple(cell_entries[lawn[0]][:4]+[0]*4), (1 << 12))] if lawn and (tuple(cell_entries[lawn[0]][:4]+[0]*4), (1 << 12)) in meta_id else 1
    (n.layout_dir/'border.bin').write_bytes(struct.pack('<4H', lawn_mid, lawn_mid, lawn_mid, lawn_mid))
    # layout height, warps, static water callback
    lay = json.loads((G/'data/layouts/layouts.json').read_text())
    for l in lay['layouts']:
        if l['id'] == 'LAYOUT_JOHTO_ROUTE32': l['height'] = H
    (G/'data/layouts/layouts.json').write_text(json.dumps(lay, indent=2)+'\n')
    mp = json.loads((G/'data/maps/JohtoRoute32/map.json').read_text())
    door = (CENTER_DST[0]+3, CENTER_DST[1]+5)
    mp['warp_events'] = [{'x': door[0], 'y': door[1], 'elevation': 0, 'dest_map': 'MAP_ROUTE32_POKEMON_CENTER', 'dest_warp_id': '0'}] + [{'x': x, 'y': y, 'elevation': 0, 'dest_map': 'MAP_UNION_CAVE_ROUTE32_ENTRANCE', 'dest_warp_id': '0'} for x, y in CAVE_WARPS]
    (G/'data/maps/JohtoRoute32/map.json').write_text(json.dumps(mp, indent=2)+'\n')
    hp = G/'src/data/tilesets/headers.h'; s = hp.read_text()
    s = s.replace('gMetatileAttributes_Route32Primary, .callback = InitTilesetAnim_CherrygrovePrimary', 'gMetatileAttributes_Route32Primary, .callback = NULL'); hp.write_text(s)
    log = {'tol_final': tol, 'glyphs': sum(len(v) for v in ex.values()), 'glyph_budget': budget, 'metatiles': len(meta_id)+len({m for m, _ in center.values()}), 'banks': {str(b): share for b in [0]}, 'bank_share': share, 'center_cells': len(center), 'door': door, 'cave_warps': CAVE_WARPS}
    (G/'route32-scratch-log.json').write_text(json.dumps(log, indent=1)); print(json.dumps(log))

if __name__ == '__main__': main()
