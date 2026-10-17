"""Validate pinned shared masters before native installation; no writes to art."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];O=ROOT/'gba/art/route33-hgss/source/transparent-objects';d=json.loads((O/'approved-tree-catalog.json').read_text());checked=[]
for a in d['assets']:
 if a['id'] not in ['T01','T03','T04']:continue
 p=O/(a['id']+'.png');assert hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256'];im=np.array(Image.open(p).convert('RGBA'));assert not im[im[...,3]==0].any();checked.append(a['id'])
assert np.array_equal(np.array(Image.open(O/'T01.png')),np.array(Image.open(O.parent/'shared-art/tree.png')))
origin=json.loads((O/'approved-master-origin.json').read_text());assert origin['hub_commit']=='3d593788873f5e3446e2d032764bc1b43c1ffcbc'
colors=set()
for n in ['T03','T04']:
 a=np.array(Image.open(O/(n+'.png')).convert('RGBA'));colors|={tuple(c&248) for c in a[a[...,3]>0,:3]}
print('Locked RGBA masters verified:',checked,'; Apricorn native conversion:',len(colors),'source shades -> 15-color shared native bank (RGBA masters unchanged).')
