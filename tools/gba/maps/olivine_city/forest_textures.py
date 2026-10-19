"""Retain the stone silhouettes; join existing same-face texture glyphs.

The earlier texture selection minimized each 8px square independently. Here
the same finite native glyph vocabulary also accounts for its four neighbors.
The source's intended shading discontinuities remain in the objective, so a
terrace lip is not mistaken for a seam. No averaging, blur or new geometry.
"""
import json
import numpy as np
from collections import defaultdict
from scipy.cluster.vq import kmeans2
from reset_tiles import plane

def tidy(bg,rock,wall,fg,ref,previous):
 h,w=wall.shape;Y,X=np.indices((h,w));sx,sy=X-64,Y-16
 rx=np.where(sx>=1024,992+(sx-992)%32,np.clip(sx,0,ref.shape[1]-1))
 source=ref[np.clip(sy,0,ref.shape[0]-1),rx].copy()
 for run in json.loads((previous/'repeated-runs.json').read_text()):
  x0,y0,x1,y1=run['target'];dx,dy,dr,db=run['donor'];m=(sx>=x0)&(sx<x1)&(sy>=y0)&(sy<y1)
  source[m]=ref[dy+(sy[m]-y0)%(db-dy),dx+(sx[m]-x0)%(dr-dx)]
 colors=np.array([(88,56,32),(112,72,40),(136,88,48),(152,104,56),(176,128,72),(192,152,96),(216,184,120)],np.int32)
 wanted=np.argmin(((source[:,:,None,:].astype(np.int32)-colors)**2).sum(3),2).astype(float)
 current=np.argmin(((rock[:,:,None,:3].astype(np.int32)-colors)**2).sum(3),2).astype(float)
 original=current.copy();groups=defaultdict(list)
 for y in range(0,704,8):
  for x in range(0,w,8):
   sl=np.s_[y:y+8,x:x+8]
   if wall[sl].all() and (fg[sl][...,3]==0).any():groups[(y>=416,plane(x,y))].append((y,x))
 banks={k:np.stack([np.frombuffer(b,float).reshape(8,8) for b in sorted({current[y:y+8,x:x+8].tobytes() for y,x in ps})]) for k,ps in groups.items()}
 vocabulary={str(k):len(v) for k,v in banks.items()}
 # Keep room for complete new ledges; consolidate only interior east-face
 # texture variations. All contours and receiving-material glyphs are exempt.
 for key,bank in list(banks.items()):
  if key!=(True,'east') or len(bank)<=24:continue
  values=bank.reshape(len(bank),-1);centers,assigned=kmeans2(values,24,minit='++',iter=30,seed=29);chosen=[]
  for i,center in enumerate(centers):
   ids=np.flatnonzero(assigned==i)
   if len(ids):chosen.append(ids[np.argmin(((values[ids]-center)**2).sum(1))])
  banks[key]=bank[chosen]
 def objective():
  data=((current-wanted)**2)[wall].sum();seams=0.
  for axis in [0,1]:
   delta=np.diff(current,axis=axis)-np.diff(wanted,axis=axis)
   ok=(wall[1:]&wall[:-1]) if axis==0 else (wall[:,1:]&wall[:,:-1])
   boundary=((np.arange(h-1)+1)%8==0)[:,None] if axis==0 else ((np.arange(w-1)+1)%8==0)[None,:]
   seams+=(delta**2)[ok&boundary].sum()
  return dict(reference_tone_error=float(data),join_gradient_error=float(seams),combined=float(data+4*seams))
 before=objective()
 for sweep in range(4):
  for key,positions in groups.items():
   bank=banks[key]
   for y,x in positions[::1 if sweep%2==0 else -1]:
    target=wanted[y:y+8,x:x+8];cost=((bank-target)**2).sum((1,2))
    # Restrict the overall face brightness to the baseline's shading plane.
    allowed=np.abs(bank.mean((1,2))-original[y:y+8,x:x+8].mean())<=.5
    for dy,dx,edge,neighbor in [(-1,0,(0,slice(None)),(y-1,slice(x,x+8))),(1,0,(-1,slice(None)),(y+8,slice(x,x+8))),(0,-1,(slice(None),0),(slice(y,y+8),x-1)),(0,1,(slice(None),-1),(slice(y,y+8),x+8))]:
     if not (0<=y+dy*8<h and 0<=x+dx*8<w):continue
     ok=wall[neighbor];desired=target[edge]-wanted[neighbor]
     error=bank[(slice(None),*edge)]-current[neighbor]-desired
     cost+=4*(error[:,ok]**2).sum(1)
    if allowed.any():cost[~allowed]=np.inf
    current[y:y+8,x:x+8]=bank[np.argmin(cost)]
 after=objective();changed=wall&(current!=original)
 rock[changed,:3]=colors[current[changed].astype(int)].astype(np.uint8)
 bg[changed]=rock[changed]
 assert after['combined']<=before['combined']
 return changed,dict(method='Existing same-face glyphs; source-tone and neighboring edge-gradient objective; fixed wall mask and face brightness',before=before,after=after,texture_vocabulary_before=vocabulary,texture_vocabulary_after={str(k):len(v) for k,v in banks.items()},changed_stone_pixels=int(changed.sum()),contour_changes=0,new_colors=0,new_texture_glyphs=0)
