"""Original HGSS reference for the complete routes; independent of earlier route drafts."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools/gba/maps/route31_catalog'))
import hgss_render as R
PHG=Path(sys.argv[1]);S=ROOT/'gba/art/routes3839-complete/source'
for n in [38,39]:
 R.AREA_BANK=7;R.HEADER_ID=n+4;R.MATERIAL_NAMES.clear();R.SNAP=True
 out=S/f'route{n}';out.mkdir(parents=True,exist_ok=True)
 r=R.render(PHG);r['full'].save(out/'original.png');r['ground'].save(out/'ground.png');r['fg'].save(out/'foreground.png')
 np.savez_compressed(out/'permissions.npz',types=r['types'],collision=r['collision'])
 np.savez_compressed(out/'materials.npz',material=r['ground_mat'],names=np.array(r['materials']),height=r['cell_height'])
 (out/'original.json').write_text(json.dumps(dict(route=n,revision='6988158691eb6178cff697cda0428045ddcba5fb',registration=dict(px_per_cell=16,offset=[0,0]),meta=r['meta'],buildings=r['buildings'],sha256={p:hashlib.sha256((PHG/p).read_bytes()).hexdigest() for p in ['files/a/0/6/5','files/a/0/4/2','files/a/0/4/4','files/a/0/4/0']}),indent=2)+'\n')
 print('Original route',n,r['full'].size,flush=True)
