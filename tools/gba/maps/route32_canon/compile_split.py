#!/usr/bin/env python3
"""Compile the 32x160 Route 32 target as TWO maps sharing one primary tileset.

JohtoRoute32 (north, rows 0-77) and JohtoRoute32South (rows 78-159) each get their own
secondary tileset, so the HGSS detail fits the GBA budget without loose glyph merges:
glyphs and metatiles used in both halves go to the shared primary, the rest to each
half's secondary. Palettes: primary banks 0-5 shared; banks 6-15 written identically to
both secondaries (Center banks 2/7/8 fixed). Collision/layering ported from the cleanup
layout by row mapping; the approved Center prefab is kept.
Usage: compile_split.py RIP_DIR ENGINE [--tol 12]
"""
import argparse, json, shutil, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parent/'route32_native_cleanup'))
import native as nat
from native import Part, PRIMARY_GLYPHS, SECONDARY_GLYPHS
W, H, SPLIT = 32, 160, 78
CENTER_MIDS = set(range(0x387, 0x3b9)); CENTER_BANKS = {2, 7, 8}
CENTER_SRC = (17, 103, 23, 108); CENTER_DST = (15, 125)
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

def entry(tid, bank, h=0, v=0): return (tid & 1023) | (h << 10) | (v << 11) | (bank << 12)

def main():
    p = argparse.ArgumentParser(); p.add_argument('rip'); p.add_argument('engine'); p.add_argument('--tol', type=float, default=12); a = p.parse_args()
    R = Path(a.rip); G = Path(a.engine)
    T = np.array(Image.open(R/'target.png').convert('RGB')).astype(float); L = np.load(R/'labels.npy')
    old = np.fromfile(G/'data/layouts/JohtoRoute32/map.bin', '<u2').reshape(128, 32)
    prim = Part(G/'data/tilesets/primary/route32', PRIMARY_GLYPHS, 0)
    north = Part(G/'data/tilesets/secondary/route32', SECONDARY_GLYPHS, 512)
    sdir = G/'data/tilesets/secondary/route32_south'
    if sdir.exists(): shutil.rmtree(sdir)
    shutil.copytree(G/'data/tilesets/secondary/route32', sdir)
    south = Part(sdir, SECONDARY_GLYPHS, 512)
    parts = [prim, north]
    def entries(m): return parts[m >= 512].blocks[m-512 if m >= 512 else m]
    def attr(m): return parts[m >= 512].attrs[m-512 if m >= 512 else m]
    def glyph(t): return parts[t >= 512].glyphs[t-512 if t >= 512 else t]
    def colors(b): return parts[b >= 6].pals[b]
    # ---- Center prefab
    center = {}
    sx0, sy0, sx1, sy1 = CENTER_SRC
    for sy in range(sy0, sy1+1):
        for sx in range(sx0, sx1+1):
            m = int(old[sy, sx] & 1023)
            if m in CENTER_MIDS: center[(CENTER_DST[0]+sx-sx0, CENTER_DST[1]+sy-sy0)] = (m, int(old[sy, sx]))
    m = int(old[108, 16] & 1023)
    if m in CENTER_MIDS: center[(CENTER_DST[0]-1, CENTER_DST[1]+5)] = (m, int(old[108, 16]))
    reserved_p = {0} | set(range(1, 17)); reserved_s = set()
    for (m, _) in center.values():
        for v in entries(m):
            if (v & 1023) and (v >> 12) in CENTER_BANKS: (reserved_s if (v & 1023) >= 512 else reserved_p).add(v & 1023)
    # ---- palettes
    blocks = []; blab = []; cells = []
    for z in range(H):
        for x in range(W):
            if (x, z) in center: continue
            for q in range(4):
                r0, c0 = z*16+(q//2)*8, x*16+(q % 2)*8
                blocks.append(T[r0:r0+8, c0:c0+8].reshape(-1, 3)); lb = L[r0:r0+8, c0:c0+8]
                cells.append((x, z, q))
    blocks = np.array(blocks)
    free = [b for b in range(16) if b not in CENTER_BANKS]
    # one bank per material group; labels decide membership so lawn, tall grass and path never share a 15-colour ramp
    groups = {'lawn': ['.'], 'tall': ['G'], 'path': ['P', 'S', '_'], 'tree': ['T'], 'tree2': [], 'rock': ['R'], 'rock2': [], 'water': ['W', 'N'], 'deck': ['D'], 'misc': ['B', 'H', '?']}
    lab8 = np.array([str(np.unique(L[z*16+(q//2)*8:z*16+(q//2)*8+8, x*16+(q % 2)*8:x*16+(q % 2)*8+8], return_counts=True)[0][np.unique(L[z*16+(q//2)*8:z*16+(q//2)*8+8, x*16+(q % 2)*8:x*16+(q % 2)*8+8], return_counts=True)[1].argmax()]) for (x, z, q) in cells])
    assign = np.zeros(len(blocks), int); banks = []; bank_family = {}; bi = 0
    for g, labs in groups.items():
        if not labs: continue
        b = free[bi]; bi += 1; banks.append(b); bank_family[b] = g; assign[np.isin(lab8, labs)] = b
    # second bank for the groups with the widest colour range, split by block brightness
    for g in ('water', 'tree', 'rock', 'deck', 'misc'):
        if bi >= len(free): break
        b0 = [b for b in banks if bank_family[b] == g][0]; idx = np.flatnonzero(assign == b0)
        if len(idx) < 400: continue
        b1 = free[bi]; bi += 1; banks.append(b1); bank_family[b1] = g
        means = blocks[idx].mean(1); C = kmeans(means, 2, 8); sub = np.stack([((means-c)**2).sum(1) for c in C], 1).argmin(1); assign[idx[sub == 1]] = b1
    blab = np.array([bank_family[b] for b in assign])
    pal = {b: np.array(colors(b)[1:], float) for b in range(16)}
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
        assign = np.array(banks)[err.argmin(0)]
    qidx = np.zeros((len(blocks), 64), np.uint8); qrgb = np.zeros((len(blocks), 64, 3), np.float32)
    for b in banks:
        m = np.flatnonzero(assign == b); C = pal[b]
        for s in range(0, len(m), 2048):
            sel = m[s:s+2048]; d = ((blocks[sel][:, :, None, :]-C[None, None])**2).sum(3).argmin(2); qidx[sel] = d+1; qrgb[sel] = C[d]
    half = np.array([0 if z < SPLIT else 1 for (x, z, q) in cells])
    # ---- glyph clustering, then placement into primary / north / south
    tol = a.tol
    while True:
        ex = {}; entry_of = np.zeros(len(blocks), int); flip_of = np.zeros((len(blocks), 2), int)
        for i in np.lexsort((np.arange(len(blocks)), assign)):
            b = int(assign[i]); q = qrgb[i].reshape(8, 8, 3); lst = ex.setdefault(b, []); best = None
            for j, (_, e) in enumerate(lst):
                for hh in (0, 1):
                    for vv in (0, 1):
                        c = q[:, ::-1] if hh else q; c = c[::-1] if vv else c
                        dd = np.abs(c-e); d = dd.mean()
                        if d <= tol and dd.reshape(2, 4, 2, 4, 3).mean((1, 3, 4)).max() <= 1.6*tol and (best is None or d < best[0]): best = (d, j, hh, vv)
            if best is None: lst.append((qidx[i].reshape(8, 8), q)); best = (0, len(lst)-1, 0, 0)
            entry_of[i] = best[1]; flip_of[i] = (best[2], best[3])
        # usage per half
        use = {}
        for i in range(len(blocks)): use.setdefault((int(assign[i]), int(entry_of[i])), [0, 0])[half[i]] += 1
        capP = PRIMARY_GLYPHS - len(reserved_p); capN = SECONDARY_GLYPHS; capS = SECONDARY_GLYPHS - len(reserved_s)
        both = sorted([k for k, u in use.items() if u[0] and u[1]], key=lambda k: -sum(use[k]))
        nonly = [k for k, u in use.items() if u[0] and not u[1]]; sonly = [k for k, u in use.items() if u[1] and not u[0]]
        place = {}
        for k in both:
            if capP > 0: place[k] = 'P'; capP -= 1
            else: place[k] = 'NS'; capN -= 1; capS -= 1
        for k in nonly:
            if capN > 0: place[k] = 'N'; capN -= 1
            elif capP > 0: place[k] = 'P'; capP -= 1
        for k in sonly:
            if capS > 0: place[k] = 'S'; capS -= 1
            elif capP > 0: place[k] = 'P'; capP -= 1
        total = sum(len(v) for v in ex.values())
        print('tol', tol, 'glyphs', total, 'both', len(both), 'north-only', len(nonly), 'south-only', len(sonly), 'left P/N/S', capP, capN, capS, flush=True)
        if capP >= 0 and capN >= 0 and capS >= 0 and len(place) == len(use): break
        tol += 1
    # ---- glyph slots
    freeP = [g for g in range(1, PRIMARY_GLYPHS) if g not in reserved_p]
    freeN = [512+g for g in range(SECONDARY_GLYPHS)]
    freeS = [512+g for g in range(SECONDARY_GLYPHS) if 512+g not in reserved_s]
    slotN = {}; slotS = {}
    for k, where in place.items():
        idx = ex[k[0]][k[1]][0]
        if where == 'P':
            s = freeP.pop(0); prim.glyphs[s] = idx; slotN[k] = slotS[k] = s
        if where in ('N', 'NS'):
            s = freeN.pop(0); north.glyphs[s-512] = idx; slotN[k] = s
        if where in ('S', 'NS'):
            s = freeS.pop(0); south.glyphs[s-512] = idx; slotS[k] = s
    for part, keep in ((prim, reserved_p | set(slotN.values()) | set(slotS.values())), (north, set(slotN.values())), (south, reserved_s | set(slotS.values()))):
        for i in range(part.count):
            if part.base+i not in keep: part.glyphs[i] = np.zeros((8, 8), np.uint8)
    # ---- per-cell entries
    port_y = lambda z: min(127, max(0, int(round((z+5)*0.78125+1))))
    cellN = {}; cellS = {}
    for i, (x, z, q) in enumerate(cells):
        k = (int(assign[i]), int(entry_of[i])); hh, vv = flip_of[i]
        cellN.setdefault((x, z), [0]*4)[q] = entry(slotN[k], k[0], int(hh), int(vv)) if k in slotN else 0
        cellS.setdefault((x, z), [0]*4)[q] = entry(slotS[k], k[0], int(hh), int(vv)) if k in slotS else 0
    def cell_meta(x, z):
        oldv = int(old[port_y(z), x]); om = oldv & 1023; oa = attr(om); beh = oa & 255; coll = (oldv >> 10) & 3; elev = oldv >> 12
        blk = L[z*16:z*16+16, x*16:x*16+16]; vals, cnt = np.unique(blk, return_counts=True); dom = str(vals[cnt.argmax()]); frac = cnt.max()/cnt.sum()
        if dom == 'W' and frac > 0.75: coll, elev, beh = 0, 1, 0x15
        elif dom == 'D': coll, elev, beh = 0, 3, 0
        elif (dom in 'RT' and frac > 0.6) or (dom == 'B' and (x, z) not in CAVE_WARPS): coll = 3; beh = 0 if beh == 0x15 else beh
        elif dom in '.PGS' and frac > 0.6:
            if coll == 3 and beh != 0x3b: coll = 0
            if beh == 0x15: beh = 0
            elev = 3 if elev in (0, 1) else elev
        layer = 0 if dom == 'H' else 1
        if beh not in (0, 0x15, 0x3b, 0x61): beh = 0
        if dom == '_': beh, coll = 0x3b, 0
        if (x, z) in CAVE_WARPS: coll, beh, elev, layer = 0, 0x61, 3, 1
        return coll, elev, beh, layer
    keyN = {}; keyS = {}; meta_cells = {}
    for z in range(H):
        for x in range(W):
            if (x, z) in center: continue
            coll, elev, beh, layer = cell_meta(x, z)
            es = cellN[(x, z)] if z < SPLIT else cellS[(x, z)]
            ents = ([0]*4 + es) if layer == 0 else (es + [0]*4); at = beh if layer == 0 else (1 << 12) | beh
            meta_cells[(x, z)] = (tuple(ents), at, coll, elev)
    # art identity across halves: compare by (bank, exemplar) not slot, so shared art gets a primary metatile
    def artkey(x, z):
        es = []
        for q in range(4):
            i = cells.index((x, z, q)) if False else None
        return None
    # usage of (entries, attr) per half, with entries expressed in slot space of that half; both-half detection via exemplar ids
    exkey = {}
    for i, (x, z, q) in enumerate(cells): exkey.setdefault((x, z), [None]*4)[q] = (int(assign[i]), int(entry_of[i]), int(flip_of[i][0]), int(flip_of[i][1]))
    ident = {}
    for (x, z), (ents, at, coll, elev) in meta_cells.items():
        k = (tuple(exkey[(x, z)]), at, ents[0] == 0 and ents[1] == 0 and ents[2] == 0 and ents[3] == 0)
        ident.setdefault(k, [set(), set()])[0 if z < SPLIT else 1].add((x, z))
    capPM = 512 - 1; capNM = 512; capSM = 512 - len({m for m, _ in center.values()})
    mid_of = {}; blocksP = {}; attrsP = {}; blocksN = {}; attrsN = {}; blocksS = {m: list(entries(m)) for m, _ in center.values()}; attrsS = {m: attr(m) for m, _ in center.values()}
    freePM = list(range(1, 512)); freeNM = list(range(512, 1024)); freeSM = [m for m in range(512, 1024) if m not in blocksS]
    def all_primary(k):
        anycell = next(iter(ident[k][0] or ident[k][1])); return all((e & 1023) < 512 for e in meta_cells[anycell][0] if e & 1023)
    both_keys = sorted([k for k, u in ident.items() if u[0] and u[1]], key=lambda k: -(len(ident[k][0])+len(ident[k][1])))
    n_keys = [k for k, u in ident.items() if u[0] and not u[1]]; s_keys = [k for k, u in ident.items() if u[1] and not u[0]]
    toP = set(k for k in both_keys if all_primary(k))
    # single-half keys overflowing their secondary move to the primary when all their glyphs are primary
    for keys, cap in ((n_keys, len(freeNM)), (s_keys, len(freeSM))):
        over = len(keys) + sum(1 for k in both_keys if k not in toP) - cap
        cand = sorted([k for k in keys if all_primary(k)], key=lambda k: -(len(ident[k][0])+len(ident[k][1])))
        for k in cand[:max(0, over)]: toP.add(k)
    if len(toP) > len(freePM): raise SystemExit(f'primary metatile budget exceeded: need {len(toP)}')
    for k in list(ident):
        u = ident[k]; anycell = next(iter(u[0] or u[1])); e, at = meta_cells[anycell][0], meta_cells[anycell][1]
        if k in toP:
            mid = freePM.pop(0); blocksP[mid] = list(e); attrsP[mid] = at
            for c in u[0] | u[1]: mid_of[c] = mid
            continue
        if u[0]:
            c0 = next(iter(u[0])); e0, a0 = meta_cells[c0][0], meta_cells[c0][1]
            if not freeNM: raise SystemExit('north metatile budget exceeded')
            mid = freeNM.pop(0); blocksN[mid] = list(e0); attrsN[mid] = a0
            for c in u[0]: mid_of[c] = mid
        if u[1]:
            c1 = next(iter(u[1])); e1, a1 = meta_cells[c1][0], meta_cells[c1][1]
            if not freeSM: raise SystemExit('south metatile budget exceeded')
            mid = freeSM.pop(0); blocksS[mid] = list(e1); attrsS[mid] = a1
            for c in u[1]: mid_of[c] = mid
    print('metatiles primary', len(blocksP), 'north', len(blocksN), 'south', len(blocksS), flush=True)
    # ---- Center ground
    def pure_src(ch):
        c = [c for c in meta_cells if (L[c[1]*16:c[1]*16+16, c[0]*16:c[0]*16+16] == ch).all() and c[1] >= SPLIT]
        return meta_cells[c[0]][0][:4] if c else None
    lawn_src, path_src = pure_src('.'), pure_src('P')
    for (m, _) in center.values():
        e = blocksS[m]
        for q in range(4):
            if (e[q] & 1023) and (e[q] >> 12) not in CENTER_BANKS:
                idxs = set(int(v) for v in np.unique(glyph(e[q] & 1023))) - {0}
                e[q] = (path_src if idxs and min(idxs) >= 5 and path_src else lawn_src)[q]
            if (e[4+q] & 1023) and (e[4+q] >> 12) not in CENTER_BANKS: e[4+q] = 0
    # ---- write tilesets
    for part, bl, at in ((prim, blocksP, attrsP), (north, blocksN, attrsN), (south, blocksS, attrsS)):
        for i in range(len(part.blocks)):
            mid = part.base+i
            part.blocks[i] = bl.get(mid, [0]*8); part.attrs[i] = at.get(mid, 0)
        part.pals = [[(0, 0, 0)] + [tuple(map(int, c)) for c in pal[b]] if b not in CENTER_BANKS else part.pals[b] for b in range(16)]
        part.save()
    for b in range(16):
        if b in CENTER_BANKS: continue
        txt = 'JASC-PAL\n0100\n16\n0 0 0\n' + ''.join(f'{int(c[0])} {int(c[1])} {int(c[2])}\n' for c in pal[b])
        for d in (prim.folder, north.folder, south.folder): (d/'palettes'/f'{b:02}.pal').write_text(txt)
    for b in CENTER_BANKS:  # fixed banks identical everywhere
        txt = (north.folder/'palettes'/f'{b:02}.pal').read_text()
        for d in (prim.folder, south.folder): (d/'palettes'/f'{b:02}.pal').write_text(txt)
    # ---- layouts
    gridN = np.zeros((SPLIT, W), '<u2'); gridS = np.zeros((H-SPLIT, W), '<u2')
    for (x, z), (ents, at, coll, elev) in meta_cells.items():
        v = mid_of[(x, z)] | (coll << 10) | (elev << 12)
        if z < SPLIT: gridN[z, x] = v
        else: gridS[z-SPLIT, x] = v
    for (x, z), (m, raw) in center.items(): gridS[z-SPLIT, x] = raw
    lawn_cells = [c for c in meta_cells if (L[c[1]*16:c[1]*16+16, c[0]*16:c[0]*16+16] == '.').all()]
    border_mid = next((mid_of[c] for c in lawn_cells if mid_of[c] < 512), 1)
    (G/'data/layouts/JohtoRoute32').mkdir(exist_ok=True); (G/'data/layouts/JohtoRoute32South').mkdir(exist_ok=True)
    gridN.tofile(G/'data/layouts/JohtoRoute32/map.bin'); gridS.tofile(G/'data/layouts/JohtoRoute32South/map.bin')
    for d in ('JohtoRoute32', 'JohtoRoute32South'): (G/'data/layouts'/d/'border.bin').write_bytes(struct.pack('<4H', *[border_mid]*4))
    lay = json.loads((G/'data/layouts/layouts.json').read_text()); lay['layouts'] = [l for l in lay['layouts'] if l['id'] != 'LAYOUT_JOHTO_ROUTE32_SOUTH']
    for l in lay['layouts']:
        if l['id'] == 'LAYOUT_JOHTO_ROUTE32': l['height'] = SPLIT; base = dict(l)
    lay['layouts'].append({**base, 'id': 'LAYOUT_JOHTO_ROUTE32_SOUTH', 'name': 'JohtoRoute32South_Layout', 'height': H-SPLIT, 'secondary_tileset': 'gTileset_Route32South', 'border_filepath': 'data/layouts/JohtoRoute32South/border.bin', 'blockdata_filepath': 'data/layouts/JohtoRoute32South/map.bin'})
    (G/'data/layouts/layouts.json').write_text(json.dumps(lay, indent=2)+'\n')
    # ---- maps
    mp = json.loads((G/'data/maps/JohtoRoute32/map.json').read_text())
    mp['warp_events'] = []; mp['connections'] = [{'map': 'MAP_JOHTO_ROUTE32_SOUTH', 'offset': 0, 'direction': 'down'}]
    (G/'data/maps/JohtoRoute32/map.json').write_text(json.dumps(mp, indent=2)+'\n')
    door = (CENTER_DST[0]+3, CENTER_DST[1]+5-SPLIT)
    ms = dict(mp); ms.update(id='MAP_JOHTO_ROUTE32_SOUTH', name='JohtoRoute32South', layout='LAYOUT_JOHTO_ROUTE32_SOUTH', connections=[{'map': 'MAP_JOHTO_ROUTE32', 'offset': 0, 'direction': 'up'}])
    ms['warp_events'] = [{'x': door[0], 'y': door[1], 'elevation': 0, 'dest_map': 'MAP_ROUTE32_POKEMON_CENTER', 'dest_warp_id': '0'}] + [{'x': x, 'y': y-SPLIT, 'elevation': 0, 'dest_map': 'MAP_UNION_CAVE_ROUTE32_ENTRANCE', 'dest_warp_id': '0'} for x, y in CAVE_WARPS]
    (G/'data/maps/JohtoRoute32South').mkdir(exist_ok=True); (G/'data/maps/JohtoRoute32South/map.json').write_text(json.dumps(ms, indent=2)+'\n')
    (G/'data/maps/JohtoRoute32South/scripts.inc').write_text('JohtoRoute32South_MapScripts::\n\t.byte 0\n')
    for f in ('Route32PokemonCenter', 'UnionCaveRoute32Entrance'):
        pth = G/f'data/maps/{f}/map.json'; pth.write_text(pth.read_text().replace('"MAP_JOHTO_ROUTE32"', '"MAP_JOHTO_ROUTE32_SOUTH"'))
    g = json.loads((G/'data/maps/map_groups.json').read_text())
    if 'JohtoRoute32South' not in g['gMapGroup_Cherrygrove']: g['gMapGroup_Cherrygrove'].append('JohtoRoute32South')
    (G/'data/maps/map_groups.json').write_text(json.dumps(g, indent=2)+'\n')
    es = G/'data/event_scripts.s'; s = es.read_text()
    if 'JohtoRoute32South/scripts.inc' not in s: es.write_text(s.rstrip('\n')+'\n.include "data/maps/JohtoRoute32South/scripts.inc"\n')
    mpf = G/'src/apocrypha_map_proof.c'; s = mpf.read_text()
    if 'MAP_JOHTO_ROUTE32_SOUTH' not in s: mpf.write_text(s.replace('MAP_UNION_CAVE_ROUTE32_ENTRANCE};', 'MAP_UNION_CAVE_ROUTE32_ENTRANCE, MAP_JOHTO_ROUTE32_SOUTH};'))
    # ---- tileset registration
    tag = '// Route32 south secondary\n'
    for f, block in {
        'graphics.h': f'const u32 gTilesetTiles_Route32South[] = INCGFX_U32("data/tilesets/secondary/route32_south/tiles.png", ".4bpp.fastSmol");\nconst u16 gTilesetPalettes_Route32South[][16] = {{\n' + ''.join(f'INCGFX_U16("data/tilesets/secondary/route32_south/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16)) + '};\n',
        'metatiles.h': 'const u16 gMetatiles_Route32South[] = INCBIN_U16("data/tilesets/secondary/route32_south/metatiles.bin");\nconst u16 gMetatileAttributes_Route32South[] = INCBIN_U16("data/tilesets/secondary/route32_south/metatile_attributes.bin");\n',
        'headers.h': 'const struct Tileset gTileset_Route32South = { .isCompressed = TRUE, .isSecondary = TRUE, .tiles = gTilesetTiles_Route32South, .palettes = gTilesetPalettes_Route32South, .metatiles = gMetatiles_Route32South, .metatileAttributes = gMetatileAttributes_Route32South, .callback = NULL };\n'}.items():
        pth = G/'src/data/tilesets'/f; s = pth.read_text().split(tag)[0]; pth.write_text(s.rstrip('\n')+'\n'+tag+block)
    hp = G/'src/data/tilesets/headers.h'; s = hp.read_text(); hp.write_text(s.replace('gMetatileAttributes_Route32Primary, .callback = InitTilesetAnim_CherrygrovePrimary', 'gMetatileAttributes_Route32Primary, .callback = NULL'))
    log = {'tol_final': tol, 'glyphs': sum(len(v) for v in ex.values()), 'placed': {w: sum(1 for p_ in place.values() if p_ == w) for w in ('P', 'N', 'S', 'NS')}, 'metatiles': {'primary': len(blocksP), 'north': len(blocksN), 'south': len(blocksS)}, 'split_row': SPLIT, 'door': door, 'cave_warps': [[x, y-SPLIT] for x, y in CAVE_WARPS]}
    (G/'route32-split-log.json').write_text(json.dumps(log, indent=1)); print(json.dumps(log))

if __name__ == '__main__': main()
