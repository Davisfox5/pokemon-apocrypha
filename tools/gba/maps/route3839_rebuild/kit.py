"""Finite native16px cliff and path vocabulary, assembled before map placement."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'gba/art/route38-39-rebuild/source';A=S/'kit';A.mkdir(exist_ok=True);M=ROOT/'gba/art/ecruteak-city/source/masters';P=ROOT/'gba/art/azalea-town/source/masters'
grass=np.array(Image.open(P/'grass.png').convert('RGBA'));dirt=np.array(Image.open(P/'path.png').convert('RGBA'));rock={f'R{i:02}':np.array(Image.open(M/f'R{i:02}.png').convert('RGBA')) for i in range(1,13)}
assets={};provenance=[]
for p in [P/'grass.png',P/'path.png']+[M/f'R{i:02}.png' for i in range(1,13)]:provenance.append(dict(source=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
def lawn(px,py):return grass[np.arange(py,py+16)[:,None]%32,np.arange(px,px+16)[None,:]%32].copy()
def save(n,a):
 a=a.copy();a[...,:3]&=248;Image.fromarray(a).save(A/(n+'.png'));assets[n]=a
for py in [0,1]:
 for px in [0,1]:
  base=lawn(px*16,py*16);save(f'lawn-{px}{py}',base)
  for mask in range(16):
   # N/E/S/W bits indicate another dirt square. Edge strips and3px corner
   # radii are one fixed tile family, never arbitrary map polygons.
   y,x=np.indices((16,16));m=np.ones((16,16),bool)
   for bit,edge in [(1,y<2),(2,x>=14),(4,y>=14),(8,x<2)]:
    if not(mask&bit):m&=~edge
   for bb,xx,yy in [(1|8,x,y),(1|2,15-x,y),(4|8,x,15-y),(4|2,15-x,15-y)]:
    if mask&bb==0:m&=~((xx<5)&(yy<5)&((xx-4)**2+(yy-4)**2>16))
   a=base.copy();tex=dirt[(y+py*16)%32,(x+px*16)%32];a[m]=tex[m]
   from scipy.ndimage import binary_erosion,binary_dilation
   a[m&~binary_erosion(m,border_value=1),:3]=[184,168,128];save(f'dirt-{mask:02x}-{px}{py}',a)
  for face in 'SNWE':
   n='R01' if face=='S' and px==0 else 'R03' if face=='S' else 'R08' if face=='N' and px==0 else 'R09' if face=='N' else 'R06' if py==0 else 'R07'
   a=rock[n].copy()
   if face=='E':a=a[:,::-1].copy()
   # Keep exact donor rock and replace only its green ground with receiving
   # lawn phase; no recoloring, blur, resized texture or per-map face painting.
   green=(a[...,1]>a[...,0])&(a[...,1]>a[...,2]);a[green]=base[green];save(f'{face}-rim-{px}{py}',a)
   a=rock['R02' if (px if face in 'SN' else py)==0 else 'R04'].copy() if face in 'SN' else rock['R11' if py==0 else 'R12'].copy()
   if face=='N':a=a[::-1].copy()
   if face=='E':a=a[:,::-1].copy()
   save(f'{face}-body-{px}{py}',a)
  # Complete convex corners: authored native silhouettes join both full-width
  # wall arms. The outer foot has a6px turn; the high-plane lip occupies the
  # meeting corner of the two neighboring rims. The donor is an intact rock turn.
  for high in ['NE','NW','SE','SW']:
   a=rock['R10' if high in ['NE','SW'] else 'R05'].copy();y,x=np.indices((16,16));u=x if 'E' in high else 15-x;v=y if 'S' in high else 15-y
   # High corner is u,v>=12; opposite low corner is u,v<=5.
   side=rock['R06' if ((py-1 if 'N' in high else py+1)%2)==0 else 'R07']
   if 'W' in high:side=side[:,::-1]
   sg=(side[...,1]>side[...,0])&(side[...,1]>side[...,2]);xedge=sg[-1 if 'N' in high else 0,:]
   npx=(px+1 if 'E' in high else px-1)%2;front=rock[('R01' if npx==0 else 'R03') if 'N' in high else ('R08' if npx==0 else 'R09')];fg=(front[...,1]>front[...,0])&(front[...,1]>front[...,2]);yedge=fg[:,0 if 'E' in high else -1]
   hi=yedge[:,None]&xedge[None,:];low=(u<6)&(v<6)&((u-6)**2+(v-6)**2>36);raw=a.copy()
   for exposure in range(4):
    corner=raw.copy();cut=hi if exposure&1 else np.zeros_like(hi);corner[cut]=base[cut];save(f'corner-{high}-{exposure}-{px}{py}',corner)
   a[hi|low]=base[hi|low];save(f'corner-{high}-{px}{py}',a)
   # Re-entrant turn around one low quadrant. Coherent rock radius, broad
   # receiving grass plane, with complete outline/cap rather than a pointed join.
   b=base.copy();qx=x if 'E' in high else 15-x;qy=y if 'S' in high else 15-y;m=(qx<12)&(qy<12)&(((qx-1)**2+(qy-1)**2)<170);b[m]=a[m];save(f'inner-{high}-{px}{py}',b)
(S/'kit-provenance.json').write_text(json.dumps(dict(shared_sources=provenance,cliff_rims='R01/R03 south; R08/R09 north; R06/R07 west, mirrored east',bodies='R02/R04 front courses and R11/R12 side courses',corners='full16px R05/R10 turns with6px outer foot radius and receiving high-plane lip; finite convex/reentrant tiles',path='native16px adjacency kit; two-pixel grass transition and3px corner radius; approved32px texture phase preserved'),indent=2)+'\n')

def finish_cliff(name, tile, exposed, phase, ground_kind):
 """One finite Wang outline variant; the low-plane corner remains transparent."""
 key=f'{name}-outline{exposed:x}-{ground_kind}'
 if key not in assets:
  a=tile.copy();yy,xx=np.indices((16,16));cut=np.zeros((16,16),bool)
  for bit,u,v in [(1,xx,yy),(2,15-xx,yy),(4,15-xx,15-yy),(8,xx,15-yy)]:
   if exposed&bit:cut|=(u<6)&(v<6)&((u-6)**2+(v-6)**2>36)
  a[cut,3]=0;save(key,a)
 a=assets[key];base=lawn(int(phase[0])*16,int(phase[1])*16)
 if ground_kind=='P':
  py=int(phase[1])*16;px=int(phase[0])*16;base=dirt[np.arange(py,py+16)[:,None]%32,np.arange(px,px+16)[None,:]%32].copy()
 m=a[...,3]>0;base[m]=a[m];return key,base
