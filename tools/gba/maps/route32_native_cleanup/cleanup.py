#!/usr/bin/env python3
"""Route 32 native visual cleanup: small local edits to the committed Porymap source.

Usage: cleanup.py ENGINE [--only step,step] [--dry-run]

Each step is a listed, reviewable local repair (see README).  The script refuses
to run unless the source files match the recorded Codex baseline 7049fd5d or the
state this script already produced, so it never replays over owner edits.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
from native import Native
ROOT = HERE.parents[3]
HUB = ROOT/'gba/art/route32-native-cleanup'
REF = ROOT/'gba/art/route32-hgss-blocks/source/hgss-reference.png'   # HGSS overview, 16px squares, native = source + (1,1)

WATER = 0x03a
LIP = {0x001:'LT',0x00e:'LB',0x00f:'LR',0x017:'LR',0x01a:'LB',0x01b:'TB',0x01c:'TB',0x01d:'TB',0x020:'LR',0x026:'L',0x02c:'B',
       0x3e0:'LT',0x3e2:'RT',0x3e4:'R',0x3e5:'L',0x3e9:'T',0x3ea:'RT',0x3eb:'LT',0x3ee:'R',0x3f2:'L',0x3fc:'L',0x03a:''}
PIECE = {'':0x03a,'L':0x3e5,'R':0x3e4,'T':0x3e9,'B':0x02c,'LT':0x001,'LB':0x00e,'RT':0x3e2,'TB':0x01c,'LR':0x00f}
RAIL_WATER = {0x3f7,0x3f9,0x3fa,0x3fb}
BOULDER_WATER = {0x3f3,0x3f4,0x3f5,0x3f6,0x3ff,0x00b,0x00c,0x3e7,0x3ef,0x00d,0x010,0x012,0x013,0x014,0x015,0x016,0x018,0x019}
DOCK = set(range(0x309, 0x344)) - {0x312, 0x313, 0x316, 0x31a, 0x31b, 0x31c, 0x31d, 0x320, 0x32d, 0x333}   # deck pieces only; rock, rail and grass in that range excluded

def ref_cell(ref, x, y):
    """HGSS pixels under native cell (x,y)."""
    return ref[(y-1)*16:(y)*16, (x-1)*16:(x)*16]

class Cleanup:
    def __init__(self, game, dry):
        self.n = Native(game); self.dry = dry; self.findings = []
        self.ref = np.array(Image.open(REF).convert('RGB')).astype(int)
    def note(self, step, text): self.findings.append({'step': step, 'finding': text}); print(f'[{step}] {text}')

    # 1. gate shadow row 12: remove stray black trunk arcs (HGSS has none under the gate)
    def gate_arcs(self):
        n = self.n; removed = 0
        for mid in (0x24f, 0x251, 0x253):
            e = n.entries(mid)
            for q in (6, 7):
                tid = e[q] & 1023
                if tid == 0: continue
                g = n.glyph(tid).copy()
                refs = sum(1 for p in n.parts for b in p.blocks for w in b if (w & 1023) == tid)
                keep = np.zeros_like(g, bool)
                if tid == 0x29b: keep[:, 6] = True; keep[7, 7] = True   # gate pillar outline stays
                arc = (g == 1) & ~keep
                if not arc.any(): continue
                removed += int(arc.sum()); g[arc] = 0
                if refs > 1:   # shared glyph: give this metatile its own cleaned copy
                    new, h, v = n.alloc_glyph(g, 6, 'gate shadow without arc'); e[q] = n.entry(new, 6, h, v); n.set_entries(mid, e)
                else: n.set_glyph(tid, g)
        self.note('gate_arcs', f'removed {removed} stray black arc pixels from gate-shadow metatiles 24f/251/253 (native row 12, x=2,4,6)')

    # 2. cave mouth: isolated cream speckles in the left jamb face
    def cave_speckle(self):
        n = self.n; g = n.glyph(0x161).copy(); k = int((g == 1).sum()); g[g == 1] = 2; n.set_glyph(0x161, g)
        self.note('cave_speckle', f'cleaned {k} isolated light pixels in cave jamb glyph 161 (metatile 3c8 at native (13,117))')

    # 3. rock column bottom at (24,64): lawn glyph under the rounded corner -> water
    def rock_corner_water(self):
        n = self.n; e = n.entries(0x312); w = n.entries(WATER)
        assert (e[2] & 1023) == 0x074
        e[2] = w[2]; n.set_entries(0x312, e)
        self.note('rock_corner_water', 'metatile 312 (native (24,64)): bottom-left quadrant lawn glyph 074 replaced by the water glyph; the green corner under the rock end is gone')

    # 4. north-south stairs: third tread row instead of the bare sand landing square
    def ns_stairs(self):
        n = self.n
        assert [n.mid(x, 89) for x in (6, 7, 8, 9)] == [0x357, 0x0da, 0x2eb, 0x358]
        for x, m in zip((6, 7, 8), (0x34c, 0x34d, 0x34e)): n.put(x, 89, m, note='third stair tread row')
        n.put(9, 89, 0x27c, note='plain rock face beside the lowest tread')
        self.note('ns_stairs', 'native (6-8,89): bare sand landing replaced by a third tread row so the flight spans rows 87-89 as in HGSS; (9,89) rock face continues the right wall')

    # 5. dock: the long pier keeps vertical grain through the fishing-arm junction
    def dock_grain(self):
        n = self.n
        for y in range(73, 77):
            fam = (0x317, 0x318, 0x319) if y % 2 else (0x30f, 0x310, 0x311)
            for x, m in zip((17, 18, 19), fam): n.put(x, y, m, note='pier vertical grain through arm junction')
        self.note('dock_grain', 'native (17-19,73-76): pier planks run vertically through the fishing-arm junction; the arm (13-16) keeps horizontal grain, matching HGSS')

    # 6. west coast pillar (x=9-10, rows 70-77): straight face instead of alternating lobes/recesses
    def west_pillar(self):
        n = self.n
        for y in range(70, 78):
            n.put(10, y, 0x04d if y % 2 else 0x04e, note='straight right face of the west coast pillar')
        for y in (70, 75, 76, 77):
            n.put(11, y, WATER, coll=0, elev=1, note='HGSS water beside the pillar (was a rock lobe)')
        self.note('west_pillar', 'native (10,70-77) now one continuous right-facing rock wall as in HGSS; the four rock lobes at (11,70/75/76/77) are water again (Surf cells opened to match the original shoreline)')

    # 7. shoreline lips around the docks and the straightened pillar: each water square
    #    bordering land/deck carries the lip on exactly those edges (other shores untouched)
    def lips(self):
        n = self.n; changed = []
        def waterish(m):
            if m in RAIL_WATER or m in (0x3fd, 0x3fe, 0x009, 0x00a): return True
            if (n.attr(m) & 255) == 0x15: return True
            e = n.entries(m)   # boulders and other props standing in water keep their own outline
            return all((v & 1023) in (7, 8, 9, 10) and (v >> 12) == 1 for v in e[:4])
        for y in range(128):
            for x in range(32):
                m = n.mid(x, y)
                if m not in LIP or m == 0x026: continue
                # add lips against deck squares and the straightened pillar face; keep the lips a square
                # already has unless that neighbour is now plain water; never add lips elsewhere
                cur_set = set(LIP[m]); req = ''; near_dock = x == 11 and 70 <= y <= 77
                for key, (dx, dy) in (('L', (-1, 0)), ('R', (1, 0)), ('T', (0, -1)), ('B', (0, 1))):
                    xx, yy = x+dx, y+dy
                    if not (0 <= xx < 32 and 0 <= yy < 128): continue
                    nm = n.mid(xx, yy)
                    if nm in DOCK: near_dock = True
                    pillar = xx == 10 and 70 <= yy <= 77
                    if nm in DOCK or pillar: req += key
                    elif key in cur_set and nm not in LIP: req += key
                if not near_dock: continue
                req = ''.join(k for k in 'LRTB' if k in req)
                cur = ''.join(k for k in 'LRTB' if k in LIP[m])
                if req == cur: continue
                if req == 'RB':
                    if not hasattr(self, 'rb'):
                        self.rb = n.alloc_metatile(n.hflip_entries(n.entries(0x00e)), n.attr(0x00e), 'water lip right+bottom (mirror of 00e)')
                    piece = self.rb
                elif req in PIECE: piece = PIECE[req]
                else: self.note('lips', f'no lip piece for edges {req} at ({x},{y}); left {m:03x}'); continue
                n.put(x, y, piece, note=f'lip {cur or "none"} -> {req}'); changed.append((x, y, cur, req))
        self.note('lips', f'{len(changed)} water squares beside the docks/pillar re-lipped to their actual land edges: ' + ', '.join(f'({x},{y}) {c or "-"}>{r}' for x, y, c, r in changed))

    # 8. Magnet Train pylon from the HGSS pixels (rows 70-75, x=24-25)
    def pylon(self):
        n = self.n; ref = self.ref
        # HGSS block: registered rows 69..76, x=23..26 -> 64x128 px; shift 2px up, 7px left so the shaft sits in cells 24-25
        blk = np.concatenate([np.concatenate([ref_cell(ref, x, y) for x in (23, 24, 25, 26)], 1) for y in range(69, 77)], 0)
        water = (blk[..., 2] > blk[..., 0]+60) & (blk[..., 2] > blk[..., 1]+20)
        gray_boulder = np.zeros(water.shape, bool); gray_boulder[16:16+24, 49:] = True   # boulder top-right, rows 70.0-71.5
        solid = ~water & ~gray_boulder; solid[:18] = False; solid[:, 55:] = False
        # destination: native rows 70..75 (96px) x cells 24..25 (32px). src row r_dst+2+16 ; src col c_dst+7+16
        art = np.zeros((96, 32, 3), int); mask = np.zeros((96, 32), bool)
        for r in range(96):
            for c in range(32):
                sr, sc = r+16+2, c+16+7
                if sr < 128 and solid[sr, sc]: art[r, c] = blk[sr, sc]; mask[r, c] = True
        # tidy: fill small holes inside the shaft rows (anything between the leftmost and rightmost solid px in rows above the base)
        for r in range(96):
            cols = np.flatnonzero(mask[r])
            if len(cols) > 8 and r < 84:
                lo, hi = cols[0], cols[-1]
                for c in range(lo, hi+1):
                    if not mask[r, c]: mask[r, c] = True; art[r, c] = blk[r+18, c+23]
        new_m = {}
        for row in range(6):
            y = 70+row; cells = []
            for col in range(2):
                x = 24+col; entries = list(n.entries(WATER)); errs = []
                for q in range(4):
                    r0, c0 = row*16+(q//2)*8, col*16+(q % 2)*8
                    sub = art[r0:r0+8, c0:c0+8]; sm = mask[r0:r0+8, c0:c0+8]
                    if not sm.any(): entries[4+q] = 0; continue
                    bank, mean, mx, idx = n.best_bank(sub, (10, 8), sm)
                    tid, h, v = n.alloc_glyph(idx, bank, f'pylon r{row} c{col} q{q}')
                    entries[4+q] = n.entry(tid, bank, h, v); errs.append(round(mean, 1))
                if row <= 4: attr = 0x0000; coll = 3      # NORMAL layer type, MB_NORMAL, blocked: pylon body
                else: attr = 0x1015; coll = 0             # COVERED, ocean water, foam ring stays surfable
                mid = n.alloc_metatile(entries, attr, f'pylon row {row} col {col} err {errs}')
                n.put(x, y, mid, coll=coll, elev=1 if coll == 0 else n.elev(x, y), note='pylon from HGSS pixels')
        self.note('pylon', 'native (24-25,70-75): Magnet Train pylon redrawn from the HGSS pixels (shaft, collar, orange band, base and foam); rows 70-74 are blocked like the original, row 75 is surfable water with the foam ring on the covered layer. The former flat teal rectangle on surfable water is gone')

    # 9. railway support posts at x=8 and x=16 (HGSS dark pillars across the four rail rows)
    def posts(self):
        n = self.n; ref = self.ref; made = {}
        for y in range(66, 70):
            for x in (8, 16):
                base = n.mid(x, y)
                if base not in made:
                    src = ref_cell(ref, 8, y)   # HGSS post occupies columns 3..8; shifted left one so it stays in the left quadrants
                    entries = list(n.entries(base))
                    for q in (4, 6):
                        v = entries[q]; tid = v & 1023; bank = v >> 12
                        g = n.glyph(tid).copy()
                        if v & 1024: g = g[:, ::-1]
                        if v & 2048: g = g[::-1, :]
                        rows = slice(0, 8) if q == 4 else slice(8, 16)
                        idx, mean, mx = n.quantize(src[rows, 3:9], bank)
                        g[:, 2:8] = idx
                        new, h, vv = n.alloc_glyph(g, bank, f'rail post row {y}')
                        entries[q] = n.entry(new, bank, h, vv)
                    made[base] = n.alloc_metatile(entries, n.attr(base), f'railway {base:03x} with support post')
                n.put(x, y, made[base], note='railway support post')
        self.note('posts', 'native (8,66-69) and (16,66-69): HGSS bridge support posts added to the railway top layer over the land and water underpass cells (traversal unchanged)')

    # 10. HGSS flower clusters on the northern lawn
    def flowers(self):
        n = self.n; ref = self.ref; lawn = {0x027, 0x028, 0x033, 0x034, 0x236, 0x237, 0x255, 0x256}; made = []
        cells = [(x, y) for y in (6, 7, 8) for x in range(14, 19)] + [(12, 13), (13, 13)]
        for x, y in cells:
            m = n.mid(x, y)
            if m not in lawn: continue
            src = ref_cell(ref, x, y); petal = (src[..., 0] >= 176) & (src[..., 1] >= 120)   # orange and white petals; leaves stay lawn
            if petal.sum() < 6: continue
            entries = list(n.entries(m)); errs = []
            for q in range(4):
                r0, c0 = (q//2)*8, (q % 2)*8
                sm = petal[r0:r0+8, c0:c0+8]
                if not sm.any(): continue
                idx, mean, mx = n.quantize(src[r0:r0+8, c0:c0+8], 8, sm)
                tid, h, v = n.alloc_glyph(idx, 8, f'flowers ({x},{y}) q{q}'); entries[4+q] = n.entry(tid, 8, h, v); errs.append(round(mean, 1))
            mid = n.alloc_metatile(entries, n.attr(m), f'lawn with HGSS flowers ({x},{y}) err {errs}')
            n.put(x, y, mid, note='HGSS flowers on lawn'); made.append((x, y))
        self.note('flowers', f'{len(made)} lawn squares carry the HGSS flower petals on the covered layer: {made}')

STEPS = ['gate_arcs', 'cave_speckle', 'rock_corner_water', 'ns_stairs', 'dock_grain', 'west_pillar', 'lips', 'pylon', 'posts', 'flowers']

def main():
    p = argparse.ArgumentParser(); p.add_argument('game', type=Path); p.add_argument('--only'); p.add_argument('--dry-run', action='store_true'); a = p.parse_args()
    c = Cleanup(a.game, a.dry_run)
    baseline = json.loads((HUB/'source/baseline-hashes.json').read_text())
    hashes = c.n.source_hashes()
    if hashes != baseline['codex_7049fd5d']:
        raise SystemExit('source does not match the Codex 7049fd5d baseline; refusing to edit (run once from that state)')
    for s in (a.only.split(',') if a.only else STEPS): getattr(c, s)()
    free = len(c.n.free_static_glyphs()); print('free static glyphs after', free, 'free primary metatiles', len(c.n.free_primary_metatiles()))
    if not a.dry_run:
        c.n.save()
        HUB.mkdir(parents=True, exist_ok=True); (HUB/'source').mkdir(exist_ok=True)
        (HUB/'source/edit-log.json').write_text(json.dumps({'steps': c.findings, 'edits': c.n.log, 'after_hashes': c.n.source_hashes()}, indent=1)+'\n')
    else: print(json.dumps(c.findings, indent=1))

if __name__ == '__main__': main()
