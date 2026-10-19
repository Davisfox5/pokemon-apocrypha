"""Direct native closure of the original northern picket fence/gate footprint."""
from pathlib import Path
import sys,json,subprocess
import numpy as np
R=Path(__file__).resolve().parents[4];G=Path(sys.argv[1]);S=R/'gba/art/goldenrod-city/source';E=S.parent/'evidence'
assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()=='fed2667cecb075aa6dcca84f0f380821f58c1584'
subprocess.run(['python3',str(G/'tools/goldenrod/check.py')],check=True)
solid=np.load(S/'solid.npy');mat=np.load(S/'material.npy');cells={}
for x in list(range(39,56))+list(range(61,82)):cells[x,3]='picket fence'
for y in range(8):
 for x in range(56,61):cells[x,y]='north gate building'
for y in range(56):cells[81,y]='east cliff'
changes=[]
for section in json.loads((E/'sections.json').read_text()):
 n=section['name'];x0,y0,x1,y1=section['box'];p=G/f'data/layouts/{n}/map.bin';g=np.fromfile(p,'<u2').reshape(y1-y0,x1-x0);changed=False
 for (x,y),material in cells.items():
  if not (x0<=x<x1 and y0<=y<y1):continue
  if not g[y-y0,x-x0]&0xc00:changes.append([x,y])
  g[y-y0,x-x0]|=0xc00;solid[y,x]=True;mat[y,x]=material;changed=True
 if changed:g.tofile(p)
np.save(S/'solid.npy',solid);np.save(S/'material.npy',mat);(E/'north-fence-fix.json').write_text(json.dumps({'baseline':'fed2667cecb075aa6dcca84f0f380821f58c1584','newly_blocked_cells':changes,'intent':'Visible pickets block passage; the closed northern gate cannot be bypassed through its roof footprint. No external route is invented.','static_RGB_changes':0},indent=2)+'\n');print('Northern fence/gate closure',len(changes))
