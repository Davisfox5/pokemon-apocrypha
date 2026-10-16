#!/usr/bin/env python3
"""Export JohtoRoute32 through the real Porymap 6.3.1 project core and compare it pixel for pixel
with the decoded native layout.  Usage: porymap_check.py ENGINE PROBE_BINARY EXPORT_DIR"""
import json, subprocess, sys, os
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
from native import Native
game, probe, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, QT_QPA_PLATFORM='offscreen')
r = subprocess.run([probe, str(game), str(out)], capture_output=True, text=True, env=env, timeout=600)
print(r.stdout[-400:], r.stderr[-400:]); r.check_returncode()
pm = np.array(Image.open(out/'JohtoRoute32.png').convert('RGB')).astype(int)
nat = np.array(Native(game).render()).astype(int)
assert pm.shape == nat.shape, (pm.shape, nat.shape)
diff = (pm != nat).any(2); cells = sorted({(int(x)//16, int(y)//16) for y, x in zip(*np.nonzero(diff))})
E = HERE.parents[3]/'gba/art/route32-native-cleanup/evidence'; E.mkdir(parents=True, exist_ok=True)
Image.fromarray(pm.astype(np.uint8)).save(E/'porymap-export-JohtoRoute32.png')
json.dump({'porymap': '6.3.1', 'method': 'headless project-core export (porymap_probe.cpp linked against the 6.3.1 sources)', 'maps_exported': json.loads(r.stdout[r.stdout.index('{'):])['maps'], 'pixel_differences_vs_native_decode': int(diff.sum()), 'differing_cells': cells[:50]}, open(E/'porymap.json', 'w'), indent=1)
print('pixel differences', int(diff.sum()), 'cells', len(cells))
