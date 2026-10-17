#!/usr/bin/env python3
"""Group the HGSS Route 32 squares into canonical roles and measure how clean an averaged tile is."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT/'gba/art/route32-hgss-blocks/source'
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
ref = np.array(Image.open(SRC/'hgss-reference.png').convert('RGB')).astype(float)[:, :480]
lab = np.load(SRC/'hgss-material-pixel-labels.npy')
H, W = 125, 30
def sig(blk):
    """4x4 dominant-label signature of a 16x16 label block."""
    s = []
    for r in range(4):
        for c in range(4):
            sub = blk[r*4:r*4+4, c*4:c*4+4]; v, n = np.unique(sub, return_counts=True); s.append(str(v[n.argmax()]))
    return ''.join(s)
groups = {}
for y in range(H):
    for x in range(W):
        blk = lab[y*16:y*16+16, x*16:x*16+16]
        if (blk == 'H').any(): continue
        groups.setdefault(sig(blk), []).append((x, y))
print('signatures', len(groups), 'squares', sum(len(v) for v in groups.values()))
rows = []
for k, cells in sorted(groups.items(), key=lambda t: -len(t[1])):
    px = np.array([ref[y*16:y*16+16, x*16:x*16+16] for x, y in cells])
    # phase split for periodic textures
    best = None
    for name, fn in (('none', lambda x, y: 0), ('x2', lambda x, y: x % 2), ('y2', lambda x, y: y % 2), ('xy2', lambda x, y: (x % 2)*2 + y % 2)):
        ph = np.array([fn(x, y) for x, y in cells]); stds = []
        for p in np.unique(ph):
            m = px[ph == p]
            if len(m) >= 2: stds.append((m.std(0).mean(), len(m)))
        if not stds: continue
        s = sum(a*b for a, b in stds)/sum(b for a, b in stds)
        if best is None or s < best[1]: best = (name, s)
    rows.append((k, len(cells), best))
for k, n, best in rows[:40]: print(f'{n:5d}  {k}  {best}')
json.dump([(k, n, best) for k, n, best in rows], open(OUT/'signatures.json', 'w'))
