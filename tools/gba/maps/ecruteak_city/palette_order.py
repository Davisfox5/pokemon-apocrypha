"""Preserve reference glyph indices when exact palette families are repacked.
Only palette slot order changes: every authored RGB and alpha pixel is retained.
"""
import json
import numpy as np
from PIL import Image
from pathlib import Path

def assignment(weights):
 # Hungarian minimum-cost assignment, square 15x15 matrix.
 n=len(weights);cost=-np.asarray(weights,dtype=float);u=[0.]*(n+1);v=u.copy();p=[0]*(n+1);way=p.copy()
 for i in range(1,n+1):
  p[0]=i;j0=0;mins=[float('inf')]*(n+1);used=[False]*(n+1)
  while True:
   used[j0]=True;i0=p[j0];delta=float('inf');j1=0
   for j in range(1,n+1):
    if used[j]:continue
    cur=cost[i0-1,j-1]-u[i0]-v[j]
    if cur<mins[j]:mins[j]=cur;way[j]=j0
    if mins[j]<delta:delta=mins[j];j1=j
   for j in range(n+1):
    if used[j]:u[p[j]]+=delta;v[j]-=delta
    else:mins[j]-=delta
   j0=j1
   if not p[j0]:break
  while True:
   j1=way[j0];p[j0]=p[j1];j0=j1
   if not j0:break
 out=[0]*n
 for j in range(1,n+1):out[p[j]-1]=j-1
 return out

def preserve(G,S,B,bank='ecruteak_city'):
 import sys
 sys.path.insert(0,str(Path(__file__).resolve().parent.parent));from tiles import Tileset
 oldbg=np.array(Image.open(B/'background.png'));oldfg=np.array(Image.open(B/'foreground.png'));bg=np.array(Image.open(S/'background.png'));fg=np.array(Image.open(S/'foreground.png'));t=Tileset(G,bank,bank);grid=np.fromfile(G/'data/layouts/JohtoEcruteakCity/map.bin','<u2').reshape(25,72);refs={};globalvotes={}
 for y,x in np.ndindex(25,72):
  mid=int(grid[y,x]&1023);entries=t.blocks[mid>=512][mid%512]
  for layer,source in enumerate([oldbg,oldfg]):
   for q,e in enumerate(entries[layer*4:layer*4+4]):
    yy=(y+27)*16+q//2*8;xx=x*16+q%2*8;a=source[yy:yy+8,xx:xx+8];tid=e&1023;idx=np.array(t.tiles[tid>=512][tid%512],np.uint8).reshape(8,8)
    if e&1024:idx=idx[:,::-1]
    if e&2048:idx=idx[::-1]
    key=a.tobytes();refs.setdefault(key,idx.copy())
    for c,i in zip(a[...,:3].reshape(-1,3),idx.ravel()):
     if i:globalvotes.setdefault(tuple(c),np.zeros(15))[int(i)-1]+=1
 pals=[sorted(map(tuple,p)) for p in json.loads((S/bank/'exact-palette-cover.json').read_text())['banks']];votes=[np.zeros((15,15)) for _ in pals]
 for a in [bg,fg]:
  for y in range(432,832,8):
   for x in range(0,1152,8):
    z=a[y:y+8,x:x+8];cs=set(map(tuple,z[z[...,3]>0,:3]));fits=[i for i,p in enumerate(pals) if cs<=set(p)]
    assert fits
    idx=refs.get(z.tobytes())
    if idx is None:continue
    for b in fits:
     for c,i,alpha in zip(z[...,:3].reshape(-1,3),idx.ravel(),z[...,3].ravel()):
      if alpha and i:votes[b][pals[b].index(tuple(c)),int(i)-1]+=1000/len(fits)
 out=[]
 for b,pal in enumerate(pals):
  for i,c in enumerate(pal):
   g=globalvotes.get(c)
   if g is not None and g.sum():votes[b][i]+=g/g.sum()
  slots=assignment(votes[b]);rows=['-']*16
  for c,slot in zip(pal,slots):rows[slot+1]=' '.join(map(str,c))
  (S/bank/'palette-overrides'/f'{b:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(rows)+'\n');out.append(dict(bank=b,slots={str(slot+1):list(c) for c,slot in zip(pal,slots)}))
 return out
