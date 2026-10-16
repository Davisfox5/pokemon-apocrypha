#!/usr/bin/env python3
"""Retile Route 32 from the HGSS overview pixels (three comparison variants).

Usage: compile.py ENGINE VARIANT [--budget N]
  A: every square from the HGSS pixels (approved Center kept)
  B: HGSS terrain, the accepted Cherrygrove tree squares kept
  C: only rock, water/shore and boulders from HGSS; every other square kept verbatim

The overview is registered at 16 px per square (native = source + 1,1).  NPC and item
sprites are removed by copying the nearest clean square with the same material pattern.
Structures (railway, pylon, gate, signs, docks, boulders, stairs) are compiled exactly;
terrain squares are vector-quantised to the metatile budget and 8x8 glyphs to the glyph
budget, always snapping to real HGSS pixels.  Collision, elevation, behaviour and
walk-behind layering come from the current native layout square by square.
"""
import argparse, json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parent/'route32_native_cleanup'))
from native import Native, PRIMARY_GLYPHS, SECONDARY_GLYPHS
ROOT = HERE.parents[3]
SRC = ROOT/'gba/art/route32-hgss-blocks/source'
W, H = 32, 128
CENTER_MIDS = set(range(0x387, 0x3b9))
CENTER_BANKS = {2, 7, 8}
WATER_ANIM_SLOTS = list(range(1, 17))
STRUCTURE = {'?', 'H', 'D', 'B', 'S'}        # compiled square-exact (no square-level VQ)
# NPC / item sprites in the overview (native squares), removed before slicing
SPRITE_CELLS = [(29, 18), (29, 19), (30, 18), (30, 19), (23, 24), (23, 25), (22, 37), (22, 38), (15, 31), (18, 48), (19, 48), (18, 49), (19, 49),
                (13, 73), (13, 74), (15, 75), (15, 76), (4, 80), (4, 81), (20, 83), (20, 84), (3, 93), (4, 93), (12, 95), (13, 95), (12, 96), (13, 96),
                (23, 100), (24, 100), (23, 101), (24, 101), (15, 105), (15, 106), (20, 118), (20, 119)]
rng = np.random.default_rng(7)

def kmeans(X, k, iters=20):
    X = np.asarray(X, float)
    if len(X) <= k: return X.copy(), np.arange(len(X))
    C = X[rng.choice(len(X), k, replace=False)]
    for _ in range(iters):
        d = np.stack([((X-c)**2).sum(1) for c in C], 1); a = d.argmin(1)
        for j in range(k):
            m = a == j
            C[j] = X[m].mean(0) if m.any() else X[rng.integers(len(X))]
    d = np.stack([((X-c)**2).sum(1) for c in C], 1)
    return C, d.argmin(1)

class Retile:
    def __init__(self, engine, variant, budget):
        self.engine = Path(engine); self.variant = variant; self.budget = budget
        self.n = Native(engine)
        self.ref = np.array(Image.open(SRC/'hgss-reference.png').convert('RGB')).astype(int)
        lab = np.load(SRC/'hgss-material-pixel-labels.npy')
        self.lab = np.full((2000, 490), '?'); self.lab[:, :480] = lab
        self.nat = np.array(self.n.render()).astype(int)
        self.log = {'variant': variant}

    # ------------------------------------------------------------------ source image
    def build_target(self):
        T = np.zeros((H*16, W*16, 3), int); L = np.full((H*16, W*16), 'N')
        T[16:2016, 16:506] = self.ref; L[16:2016, 16:506] = self.lab
        T[16:2016, 0:16] = T[16:2016, 16:32][:, ::-1]; L[16:2016, 0:16] = L[16:2016, 16:32][:, ::-1]
        T[16:2016, 506:512] = T[16:2016, 500:506][:, ::-1]; L[16:2016, 506:512] = L[16:2016, 500:506][:, ::-1]
        T[0:16] = T[16:32][::-1]; L[0:16] = L[16:32][::-1]
        T[2016:2048] = T[1984:2016][::-1]; L[2016:2048] = L[1984:2016][::-1]
        self.L = L; self.remove_sprites(T, L)
        self.keep_exact = np.zeros((H, W), bool)      # squares whose native metatile is kept verbatim
        if self.variant == 'B':
            self.keep_exact = self.tree_cells()
            for y in range(H):
                for x in range(W):
                    if self.keep_exact[y, x]: continue
                    blk = L[y*16:y*16+16, x*16:x*16+16]
                    if (blk == 'T').any() and (blk != 'T').any(): self.fill_label(T, L, x, y, 'T')
        elif self.variant == 'C':
            for y in range(H):
                for x in range(W):
                    blk = L[y*16:y*16+16, x*16:x*16+16]
                    if not np.isin(blk, ['R', 'W', 'B']).any(): self.keep_exact[y, x] = True
            m = ~np.isin(L, ['R', 'W', 'B']); T[m] = self.nat[m]      # mixed squares: HGSS rock/water, native remainder
        # Center footprint is always kept
        for y in range(103, 109):
            for x in range(16, 24):
                m = self.n.mid(x, y)
                if m in CENTER_MIDS and any((v & 1023) and (v >> 12) in CENTER_BANKS for v in self.n.entries(m)):
                    self.keep_exact[y, x] = True
        self.T = T
        Image.fromarray(T.astype(np.uint8)).save(self.engine/'route32-target.png')

    def tree_cells(self):
        keep = np.zeros((H, W), bool)
        for y in range(H):
            for x in range(W):
                if any((v & 1023) and (v >> 12) in (3, 4) for v in self.n.entries(self.n.mid(x, y))): keep[y, x] = True
        return keep

    def donor(self, L, x, y, blk, radius=40, exclude=(), tolerance=0):
        """Nearest square whose label pattern equals blk (outside unknown pixels, up to `tolerance` pixels) and that holds no unknown pixels."""
        mask = ~np.isin(blk, ['?', 'H'])
        for tol in sorted({0, tolerance}):
            for r in range(1, radius+1):
                for dy in range(-r, r+1):
                    for dx in range(-r, r+1):
                        if max(abs(dx), abs(dy)) != r: continue
                        xx, yy = x+dx, y+dy
                        if not (0 <= xx < W and 0 <= yy < H) or (xx, yy) in exclude: continue
                        cand = L[yy*16:yy*16+16, xx*16:xx*16+16]
                        if np.isin(cand, ['?', 'H']).any(): continue
                        if (cand[mask] != blk[mask]).sum() <= tol: return xx, yy
        return None

    def remove_sprites(self, T, L):
        done = []; ex = set(SPRITE_CELLS)
        for (x, y) in SPRITE_CELLS:
            blk = L[y*16:y*16+16, x*16:x*16+16]
            src = self.donor(L, x, y, blk, exclude=ex, tolerance=12)
            if src is None:
                # relax: match only the dominant material
                vals, cnt = np.unique(blk[~np.isin(blk, ['?', 'H'])], return_counts=True)
                if len(vals) == 0: continue
                want = np.full((16, 16), vals[cnt.argmax()]); src = self.donor(L, x, y, want, exclude=ex)
            if src is None: continue
            sx, sy = src
            T[y*16:y*16+16, x*16:x*16+16] = T[sy*16:sy*16+16, sx*16:sx*16+16]; L[y*16:y*16+16, x*16:x*16+16] = L[sy*16:sy*16+16, sx*16:sx*16+16]
            done.append([x, y, sx, sy])
        self.log['sprite_squares_replaced'] = done

    def fill_label(self, T, L, x, y, bad):
        blk = L[y*16:y*16+16, x*16:x*16+16]
        others = [c for c in np.unique(blk) if c not in (bad, 'N', '?')]
        if not others: return
        vals, cnt = np.unique(blk[np.isin(blk, others)], return_counts=True); want = np.full((16, 16), vals[cnt.argmax()])
        src = self.donor(L, x, y, want)
        if src is None: return
        sx, sy = src; mask = blk == bad
        T[y*16:y*16+16, x*16:x*16+16][mask] = T[sy*16:sy*16+16, sx*16:sx*16+16][mask]; L[y*16:y*16+16, x*16:x*16+16][mask] = want[mask]

    # ------------------------------------------------------------------ plan
    def plan_cells(self):
        self.compile_cells = [(x, y) for y in range(H) for x in range(W) if not self.keep_exact[y, x]]
        self.kept = {(x, y): self.n.mid(x, y) for y in range(H) for x in range(W) if self.keep_exact[y, x]}
        self.center_cells = {(x, y) for (x, y), m in self.kept.items() if m in CENTER_MIDS and 16 <= x <= 23 and 103 <= y <= 108}
        # banks the kept squares depend on stay fixed (Center art banks always)
        fixed = set(CENTER_BANKS)
        for (x, y), m in self.kept.items():
            if (x, y) in self.center_cells: continue
            for v in self.n.entries(m):
                if v & 1023: fixed.add(v >> 12)
        if self.variant == 'B': fixed |= {3, 4}
        self.fixed_banks = fixed
        self.log.update(compiled_cells=len(self.compile_cells), kept_cells=len(self.kept), fixed_banks=sorted(fixed))

    # ------------------------------------------------------------------ palettes
    def fit_palettes(self):
        T = self.T; blocks = []; labels = []
        for (x, y) in self.compile_cells:
            for q in range(4):
                r0, c0 = y*16+(q//2)*8, x*16+(q % 2)*8
                blocks.append(T[r0:r0+8, c0:c0+8].reshape(-1, 3)); lb = self.L[r0:r0+8, c0:c0+8]
                vals, cnt = np.unique(lb, return_counts=True); labels.append(str(vals[cnt.argmax()]))
        self.blocks = np.array(blocks); self.block_labels = np.array(labels)
        free = [b for b in range(16) if b not in self.fixed_banks]
        if not free: raise RuntimeError('no free palette banks')
        groups = {'ground': ['.', 'P', 'S', 'G', 'N'], 'tree': ['T'], 'rock': ['R'], 'water': ['W', 'D', 'B'], 'misc': ['?', 'H']}
        counts = {g: int(np.isin(self.block_labels, labs).sum()) for g, labs in groups.items()}
        # share banks by sqrt of block count, at least one bank per non-empty group while banks last
        weights = {g: np.sqrt(c) for g, c in counts.items() if c}
        share = {g: 1 for g in weights}; left = len(free) - len(share)
        while left > 0:
            g = max(weights, key=lambda g: weights[g]/share[g]); share[g] += 1; left -= 1
        while sum(share.values()) > len(free):
            g = max(share, key=lambda g: share[g]); share[g] -= 1
        assign = np.zeros(len(self.blocks), int); bi = 0; banks = []
        for g, k in share.items():
            idx = np.flatnonzero(np.isin(self.block_labels, groups[g]))
            if len(idx) == 0: continue
            _, sub = kmeans(self.blocks[idx].mean(1), k)
            for j in range(k):
                b = free[bi]; bi += 1; banks.append(b); assign[idx[sub == j]] = b
        self.pal = {b: np.array(self.n.bank_colors(b)[1:], float) for b in range(16)}
        for it in range(4):
            for b in banks:
                members = self.blocks[assign == b]
                if len(members) == 0: continue
                px = members.reshape(-1, 3); px = px[rng.choice(len(px), min(len(px), 40000), replace=False)]
                C, _ = kmeans(px, 15, 12); self.pal[b] = np.round(C/8)*8
            errs = np.zeros((len(banks), len(self.blocks)), np.float32)
            for bi_, b in enumerate(banks):
                C = self.pal[b].astype(np.float32)
                for s0 in range(0, len(self.blocks), 1024):
                    blk = self.blocks[s0:s0+1024].astype(np.float32)
                    errs[bi_, s0:s0+1024] = ((blk[:, :, None, :]-C[None, None]) ** 2).sum(3).min(2).mean(1)
            assign = np.array(banks)[errs.argmin(0)]
        self.assign = assign; self.banks = banks
        self.log['bank_shares'] = share

    # ------------------------------------------------------------------ quantise and VQ
    def quantise(self):
        idx = np.zeros((len(self.blocks), 64), np.uint8); rgb = np.zeros((len(self.blocks), 64, 3), int)
        for b in set(self.assign.tolist()):
            m = np.flatnonzero(self.assign == b); C = self.pal[b]
            for s0 in range(0, len(m), 1024):
                sel = m[s0:s0+1024]
                a = ((self.blocks[sel][:, :, None, :]-C[None, None]) ** 2).sum(3).argmin(2)
                idx[sel] = a+1; rgb[sel] = C[a]
        self.q_idx = idx; self.q_rgb = rgb

    def cell_quantise(self):
        n = self.n; cells = self.compile_cells; N = len(cells)
        free_mids = 1024 - len(set(self.kept.values()))
        cell_budget = free_mids - 20
        keyof = lambda i: tuple((int(self.assign[4*i+q]), self.q_idx[4*i+q].tobytes()) for q in range(4))
        groups = {}; exact = set()
        for i, (x, y) in enumerate(cells):
            m = n.mid(x, y); attr = n.attr(m)
            lb = self.L[y*16:y*16+16, x*16:x*16+16]; vals, cnt = np.unique(lb, return_counts=True); dom = str(vals[cnt.argmax()])
            if dom in STRUCTURE or (lb == '?').sum() > 64: exact.add(keyof(i)); continue
            groups.setdefault((''.join(sorted(set(lb.ravel().tolist()))), (attr >> 12) & 3, attr & 255), []).append(i)
        distinct = {g: len({keyof(i) for i in idx}) for g, idx in groups.items()}
        total = sum(distinct.values()) + len(exact); self.log['distinct_squares_before_vq'] = total; self.log['exact_structure_squares'] = len(exact)
        vq_budget = cell_budget - len(exact)
        if sum(distinct.values()) <= vq_budget: return
        vec = np.array([np.concatenate([self.q_rgb[4*i+q].reshape(-1) for q in range(4)]) for i in range(N)], float)
        weights = {g: d ** 0.85 for g, d in distinct.items()}; tot = sum(weights.values())
        for g, idx in groups.items():
            keys = {}
            for i in idx: keys.setdefault(keyof(i), []).append(i)
            ks = list(keys); kb = max(1, int(vq_budget*weights[g]/tot))
            if len(ks) <= kb: continue
            X = np.array([vec[keys[k][0]] for k in ks]); wts = np.array([len(keys[k]) for k in ks], float)
            C, a = kmeans(X, kb, 12)
            for j in range(kb):
                mem = np.flatnonzero(a == j)
                if len(mem) == 0: continue
                d = ((X[mem]-C[j]) ** 2).sum(1) / np.sqrt(wts[mem]); med = keys[ks[mem[d.argmin()]]][0]
                for mi in mem:
                    for i in keys[ks[mi]]:
                        if i != med:
                            for q in range(4):
                                self.q_idx[4*i+q] = self.q_idx[4*med+q]; self.q_rgb[4*i+q] = self.q_rgb[4*med+q]; self.assign[4*i+q] = self.assign[4*med+q]
        self.log['cell_budget'] = cell_budget

    def reserved_glyphs(self):
        reserved = set(WATER_ANIM_SLOTS) | {0}
        lawn_compiled = any((self.L[y*16:y*16+16, x*16:x*16+16] == '.').all() for (x, y) in self.compile_cells)
        for (x, y), m in self.kept.items():
            for v in self.n.entries(m):
                if (v & 1023) and ((x, y) not in self.center_cells or (v >> 12) in CENTER_BANKS or not lawn_compiled): reserved.add(v & 1023)
        return reserved

    def vector_quantise(self):
        keys = {}
        for i in range(len(self.blocks)):
            keys.setdefault((int(self.assign[i]), self.q_idx[i].tobytes()), []).append(i)
        distinct = list(keys); self.log['distinct_glyphs_before_vq'] = len(distinct)
        budget = min(self.budget, PRIMARY_GLYPHS + SECONDARY_GLYPHS - len(self.reserved_glyphs()) - 12)
        self.log['glyph_budget_effective'] = budget
        self.rep = {i: k for k, members in keys.items() for i in members}
        if len(distinct) <= budget: return
        # structure glyphs (railway, pylon, gate, docks, boulders, signs, stairs) stay exact; terrain glyphs share the rest
        struct_keys = {k for k, members in keys.items() if any(self.block_labels[i] in ('?', 'S') for i in members)}
        cap = int(budget*0.4); exact_keys = set(struct_keys)
        if len(struct_keys) > cap:      # too many structure glyphs: merge them lightly among themselves
            ks = list(struct_keys); X = np.array([self.q_rgb[keys[k][0]].reshape(-1) for k in ks], float); wts = np.array([len(keys[k]) for k in ks], float)
            C, a = kmeans(X, cap, 15); exact_keys = set()
            for j in range(cap):
                m = np.flatnonzero(a == j)
                if len(m) == 0: continue
                d = ((X[m]-C[j]) ** 2).sum(1) / np.sqrt(wts[m]); med = ks[m[d.argmin()]]; exact_keys.add(med)
                for mi in m:
                    for i in keys[ks[mi]]: self.rep[i] = med
        budget_terrain = budget - len(exact_keys)
        per_bank = {}
        for k in distinct:
            if k not in struct_keys: per_bank.setdefault(k[0], []).append(k)
        weights = {b: len(v) ** 0.8 for b, v in per_bank.items()}; tot = sum(weights.values())
        self.log['glyph_vq'] = {'exact_structure_glyphs': len(exact_keys), 'terrain_budget': budget_terrain, 'per_bank': {str(b): [len(v), max(4, int(budget_terrain*weights[b]/tot))] for b, v in per_bank.items()}}
        for b, ks in per_bank.items():
            kb = max(4, int(budget_terrain*weights[b]/tot))
            if len(ks) <= kb: continue
            X = np.array([self.q_rgb[keys[k][0]].reshape(-1) for k in ks], float); wts = np.array([len(keys[k]) for k in ks], float)
            C, a = kmeans(X, kb, 15)
            for j in range(kb):
                m = np.flatnonzero(a == j)
                if len(m) == 0: continue
                d = ((X[m]-C[j]) ** 2).sum(1) / np.sqrt(wts[m]); med = ks[m[d.argmin()]]
                for mi in m:
                    for i in keys[ks[mi]]: self.rep[i] = med

    # ------------------------------------------------------------------ assemble
    def assemble(self):
        n = self.n; reserved = self.reserved_glyphs()
        free_glyphs = [g for g in range(1, PRIMARY_GLYPHS) if g not in reserved] + [512+g for g in range(SECONDARY_GLYPHS) if 512+g not in reserved]
        self.log['reserved_glyphs'] = len(reserved); self.log['free_glyph_slots'] = len(free_glyphs)
        glyph_id = {}; glyph_pixels = {}
        def key_flips(arr):
            best = None
            for h in (0, 1):
                for v in (0, 1):
                    c = arr[:, ::-1] if h else arr; c = c[::-1, :] if v else c; kb = c.tobytes()
                    if best is None or kb < best[0]: best = (kb, h, v, c)
            return best
        def glyph_for(i):
            bank, raw = self.rep[i]; arr = np.frombuffer(raw, np.uint8).reshape(8, 8)
            kb, h, v, canon = key_flips(arr); k = (bank, kb)
            if k not in glyph_id:
                if not free_glyphs: raise RuntimeError('glyph budget exceeded')
                gid = free_glyphs.pop(0); glyph_id[k] = gid; glyph_pixels[gid] = canon
            return Native.entry(glyph_id[k], bank, h, v)
        cell_entries = {}; bi = 0
        for (x, y) in self.compile_cells:
            es = [glyph_for(bi+q) for q in range(4)]; bi += 4
            attr = n.attr(n.mid(x, y)); layer = (attr >> 12) & 3; beh = attr & 255
            if layer == 0: entries = [0, 0, 0, 0] + es; a = beh                 # NORMAL: art on the top layer (walk-behind / under-bridge)
            else: entries = es + [0, 0, 0, 0]; a = (1 << 12) | beh              # COVERED: art under the player
            cell_entries[(x, y)] = (tuple(entries), a)
        lawn_cells = [c for c in self.compile_cells if (self.L[c[1]*16:c[1]*16+16, c[0]*16:c[0]*16+16] == '.').all() and ((n.attr(n.mid(*c)) >> 12) & 3) == 1]
        lawn_src = cell_entries[lawn_cells[0]][0][:4] if lawn_cells else (0, 0, 0, 0)
        used_kept = set(self.kept.values())
        new_blocks = {m: list(n.entries(m)) for m in used_kept}; new_attrs = {m: n.attr(m) for m in used_kept}
        if lawn_cells:   # swap the Cherrygrove lawn behind the Center for the HGSS lawn; otherwise (variant C) it stays
            for (x, y) in self.center_cells:
                e = new_blocks[self.kept[(x, y)]]
                for q in range(4):
                    if (e[q] & 1023) and (e[q] >> 12) not in CENTER_BANKS: e[q] = lawn_src[q]
                    if (e[4+q] & 1023) and (e[4+q] >> 12) not in CENTER_BANKS: e[4+q] = 0
        kept_glyphs = {v & 1023 for m in used_kept for v in new_blocks[m] if v & 1023}
        meta_id = {}; free_mids = [m for m in range(1, 1024) if m not in used_kept]
        grid = n.grid.copy()
        for (x, y), (entries, a) in cell_entries.items():
            k = (entries, a)
            if k not in meta_id:
                if not free_mids: raise RuntimeError('metatile budget exceeded')
                mid = free_mids.pop(0); meta_id[k] = mid; new_blocks[mid] = list(entries); new_attrs[mid] = a
            grid[y, x] = (grid[y, x] & 0xfc00) | meta_id[k]
        self.log['metatiles_used'] = len(meta_id)+len(used_kept); self.log['glyphs_used'] = len(glyph_id)+len(kept_glyphs)
        for p in n.parts:
            for i in range(p.count):
                gid = p.base+i
                if gid in glyph_pixels: p.glyphs[i] = glyph_pixels[gid]
                elif gid not in reserved and gid not in kept_glyphs: p.glyphs[i] = np.zeros((8, 8), np.uint8)
            for i in range(len(p.blocks)):
                mid = p.base+i
                if mid in new_blocks: p.blocks[i] = new_blocks[mid]; p.attrs[i] = new_attrs[mid]
                else: p.blocks[i] = [0]*8; p.attrs[i] = 0
        n.grid = grid
        lawn_mid = meta_id[cell_entries[lawn_cells[0]]] if lawn_cells else 0
        (n.layout_dir/'border.bin').write_bytes(struct.pack('<4H', lawn_mid, lawn_mid, lawn_mid, lawn_mid))
        for b in range(16):
            if b in self.fixed_banks: continue
            cols = self.pal[b]
            text = 'JASC-PAL\n0100\n16\n0 0 0\n' + ''.join(f'{int(c[0])} {int(c[1])} {int(c[2])}\n' for c in cols)
            for part in ('primary', 'secondary'):
                (self.engine/f'data/tilesets/{part}/route32/palettes/{b:02}.pal').write_text(text)
        for p in n.parts:
            p.pals = [p.pals[b] if b in self.fixed_banks else [(0, 0, 0)] + [tuple(map(int, c)) for c in self.pal[b]] for b in range(16)]
        n.save()

    def run(self):
        try:
            self.build_target(); print('target', flush=True); self.plan_cells(); print('plan', self.log, flush=True); self.fit_palettes(); print('palettes', flush=True)
            self.quantise(); self.cell_quantise(); print('cellvq', {k: self.log.get(k) for k in ('distinct_squares_before_vq', 'exact_structure_squares', 'cell_budget')}, flush=True)
            self.vector_quantise(); print('glyphvq', self.log.get('distinct_glyphs_before_vq'), self.log.get('glyph_budget_effective'), flush=True); self.assemble()
        finally:
            (self.engine/'route32-retile-log.json').write_text(json.dumps(self.log, indent=1, default=str))
        print(json.dumps({k: v for k, v in self.log.items() if k != 'sprite_squares_replaced'}, indent=1, default=str))

if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('engine'); p.add_argument('variant', choices='ABC'); p.add_argument('--budget', type=int, default=840)
    a = p.parse_args(); Retile(a.engine, a.variant, a.budget).run()
