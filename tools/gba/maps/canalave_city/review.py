#!/usr/bin/env python3
"""Review sheets and the trace ledger for Canalave City.

    python3 tools/gba/maps/canalave_city/review.py CACHE ENGINE RUNTIME_OUT

Writes gba/art/canalave-city/evidence/review/ (whole map and four numbered sheets, Platinum left, native right;
a gameplay sheet from the headless run) and source/trace/ (material grid, traversal ledger).
"""
from __future__ import annotations
import collections, hashlib, json, shutil, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(HERE), str(HERE.parent)]
import cn_compose as C, cn_reference as Rf, runtime as RT, install as I   # noqa: E402
from cn_reference import W, H, MARGIN                                     # noqa: E402

ART = ROOT / 'gba/art/canalave-city'
# material ledger letters
LETTER = {'sea': '~', 'tree01': 'T', 'conttree_t': 'T', 'conttree_b': 'T', 'tshadow': 't', 'ngrass': 'g', 'imped': 'x',
          'bridge': 'D', 'seaside3': 'W'}
def letter(name):
    if name in LETTER: return LETTER[name]
    if name.startswith('c02_road'): return 'r'
    if name.startswith('c02_base'): return 'p'
    if name.startswith('c2_rale'): return 'W'
    if name.startswith('c2_light'): return 'L'
    return '?'

def grid(img, scale=2, every=1, origin=(0, 0)):
    im = Image.fromarray(img).resize((img.shape[1] * scale, img.shape[0] * scale), Image.NEAREST)
    d = ImageDraw.Draw(im)
    for x in range(0, img.shape[1] // 16):
        for y in range(0, img.shape[0] // 16):
            if (x + origin[0]) % 4 == 0 and (y + origin[1]) % 4 == 0:
                d.text((x * 16 * scale + 1, y * 16 * scale), f'{x + origin[0]},{y + origin[1]}', fill=(255, 255, 0))
    for x in range(0, img.shape[1] // 16 + 1):
        d.line([(x * 16 * scale, 0), (x * 16 * scale, im.height)], fill=(0, 0, 0) if (x + origin[0]) % 4 else (255, 0, 0), width=1)
    for y in range(0, img.shape[0] // 16 + 1):
        d.line([(0, y * 16 * scale), (im.width, y * 16 * scale)], fill=(0, 0, 0) if (y + origin[1]) % 4 else (255, 0, 0), width=1)
    return im

def main():
    cache, engine, run = Path(sys.argv[1]), Path(sys.argv[2]).resolve(), Path(sys.argv[3])
    t = C.build(cache, engine)
    plat = t.full
    native, ts, words = RT.decode(engine)
    out = ART / 'evidence/review'; out.mkdir(parents=True, exist_ok=True)
    whole = np.hstack([plat, np.zeros((plat.shape[0], 8, 3), np.uint8), native])
    Image.fromarray(whole).save(out / 'whole.png')
    rows = [(0, 22), (20, 42), (40, 60), (58, 78)]
    for i, (a, b) in enumerate(rows, 1):
        l = grid(plat[a * 16:b * 16], origin=(0, a)); r = grid(native[a * 16:b * 16], origin=(0, a))
        sheet = Image.new('RGB', (l.width + r.width + 8, l.height), (0, 0, 0)); sheet.paste(l, (0, 0)); sheet.paste(r, (l.width + 8, 0))
        sheet.save(out / f'sheet-{i}.png')
    # gameplay sheet
    shots = sorted(run.glob('tour-*.png')) + sorted(run.glob('layer-*.png')) + sorted(run.glob('inside-*.png')) + \
        [run / f'{n}.png' for n in ('center-1f', 'center-2f', 'nurse', 'clerk', 'CanalaveCity_Sign_Gym', 'harbor-inn-door', 'gate', 'sailor-eldritch', 'cold-reload')]
    shots = [s for s in shots if s.exists()]
    cols = 6
    sheet = Image.new('RGB', (cols * 244, ((len(shots) + cols - 1) // cols) * 164), (20, 20, 20))
    for i, s in enumerate(shots):
        sheet.paste(Image.open(s), ((i % cols) * 244 + 2, (i // cols) * 164 + 2))
    sheet.save(out / 'gameplay.png')
    # trace: material grid (majority terrain material per cell, top-layer owner marked) and traversal
    tr = ART / 'source/trace'; tr.mkdir(parents=True, exist_ok=True)
    own, B = t.c['fg_owner'], t.c['buildings']
    lines = ['Canalave City material grid: native cells, x across, y down. Majority Platinum terrain material per cell;',
             'upper case B = a building or prop of the top layer covers most of the cell.',
             '~ sea  p paving (c02_base*)  r road paving (c02_road*)  W canal wall/rail  L lamp base  g grass  T tree  t tree shadow',
             'D dock/bridge terrain  x impassable filler  B building/prop', '']
    mats = collections.Counter()
    for r in range(H):
        row = ''
        for x in range(W):
            sl = t.cell(x, r)
            if (t.c['fg'][sl][..., 3] > 0).sum() > 128: ch = 'B'
            else:
                ch = letter(collections.Counter(t.mat[sl].ravel().tolist()).most_common(1)[0][0])
            mats[ch] += 1; row += ch
        lines.append(f'{r:2d} {row}')
    (tr / 'material-grid.txt').write_text('\n'.join(lines) + '\n')
    words = np.frombuffer((engine / 'data/layouts/CanalaveCity/map.bin').read_bytes(), '<u2').reshape(H, W)
    p = RT.plan(cache, engine)
    lines = ['Canalave City traversal: native cells. Left: Platinum permission grid (margin blocked). Right: installed map.',
             '# blocked  . walk  ~ surf water  = deck (Platinum bridge type)  d door  s sign (blocked in Gen 3)', '']
    signs = {I.N(*c) for c in __import__('cn_cleanup').SIGNS}
    diffs = []
    for r in range(H):
        a = b = ''
        for x in range(W):
            pc, pt = t.c['collision'][r, x], t.c['types'][r, x]
            a += 'd' if pt == C.T_DOOR else '~' if (pt == C.T_WATER and not pc) else '=' if (pt == C.T_BRIDGE and not pc) else '#' if pc else '.'
            nc = (int(words[r, x]) >> 10) & 3; nb = int(p['beh'][r, x])
            ch = 'd' if (x, r) in p['doors'] else '~' if (nb == C.MB_OCEAN_WATER and not nc) else 's' if (x, r) in signs else '#' if nc else ('=' if pt == C.T_BRIDGE else '.')
            b += ch
            if ch != a[-1]: diffs.append(dict(cell=[x, r], platinum=a[-1], native=ch))
        lines.append(f'{r:2d} {a}   {b}')
    (tr / 'traversal.txt').write_text('\n'.join(lines) + '\n')
    (tr / 'adaptations.json').write_text(json.dumps(dict(traversal_differences=diffs, cleanup=t.notes), indent=1) + '\n')
    print(json.dumps(dict(material_cells=mats, traversal_differences=len(diffs)), default=dict))

if __name__ == '__main__':
    main()
