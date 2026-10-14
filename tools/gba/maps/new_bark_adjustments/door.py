"""Refresh only the recolored gable's existing facade animation, retaining its ID."""
from pathlib import Path
import sys,re
import numpy as np
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent))
from tiles import Tileset
G=Path(sys.argv[1]);t=Tileset(G,'new_bark','cherrygrove');grid=np.fromfile(G/'data/layouts/NewBarkTown/map.bin','<u2').reshape(53,36);rgb=np.asarray(t.map_image(grid.ravel().tolist(),36),int)
for number,x,y in [(0,17,9),(7,24,41)]:
 closed=rgb[(y-1)*16:(y+1)*16,x*16:(x+2)*16].copy();frames=[];top,bot,right=(8,31,20) if number==0 else (13,29,16)
 for n in (1,2,3):
  f=closed.copy();f[top:bot,:right]=[24,32,40];keep=right-right*n//3
  if keep:f[top:bot,:keep]=closed[top:bot,np.linspace(0,right-1,keep).astype(int)]
  frames.append(f)
 quads=[(x+dx,y+dy) for x,y in [(0,0),(0,16),(16,0),(16,16)] for dx,dy in [(0,0),(8,0),(0,8),(8,8)]];bs=[];raw=bytearray()
 for qx,qy in quads:
  cs=np.concatenate([f[qy:qy+8,qx:qx+8].reshape(-1,3) for f in frames]);cost=[]
  for bank in range(13):
   pp=np.asarray(t.pals[bank>=6][bank][1:],int);cost.append(((cs[:,None]-pp)**2).sum(2).min(1).sum())
  bs.append(int(np.argmin(cost)))
 for f in frames:
  for (qx,qy),bank in zip(quads,bs):
   pp=np.asarray(t.pals[bank>=6][bank][1:],int);cs=f[qy:qy+8,qx:qx+8].reshape(-1,3);ids=((cs[:,None]-pp)**2).sum(2).argmin(1)+1;raw.extend(int(ids[k])|(int(ids[k+1])<<4) for k in range(0,64,2))
 (G/f'graphics/door_anims/johto_synthesis/NewBarkTown_{number}.4bpp').write_bytes(raw)
 p=G/'src/field_door.c';s=p.read_text();s=re.sub(r'(sJohtoSynthesisDoorPal_NewBarkTown_'+str(number)+r'\[20\] = )\{[^}]+\}',lambda m:m[1]+'{'+','.join(map(str,bs+[0]*4))+'}',s);p.write_text(s);print('Updated door',number,'palettes',bs)
