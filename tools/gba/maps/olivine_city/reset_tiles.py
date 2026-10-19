"""Native terrain modules with compatible contours, contact planes and shading.

Round subpixel overview noise by <=1 native pixel; preserve corner occupancy,
connected components and edge contact topology. Foreground is never modified.
Use original texture medoids, never averaged/blurry synthetic pixel blocks.
"""
import numpy as np
from scipy.ndimage import label,binary_dilation,distance_transform_edt
from scipy.cluster.vq import kmeans2
from collections import Counter,defaultdict

def plane(x,y):
 x-=64;y-=16
 if 20<=x<104 and y>=540:return 'plateau' if y<616 else 'front'
 if ((88<=x<112 and 176<=y<448) or (288<=x<328 and y<152) or (824<=x<944 and y>=304)):return 'east'
 if ((464<=x<536 and y<176) or (464<=x<488 and y<424) or (624<=x<696 and 200<=y<576)):return 'west'
 return 'front'
def signature(q):return (tuple(q[[0,0,7,7],[0,7,0,7]]),tuple(bool(r.any()) for r in [q[0],q[-1],q[:,0],q[:,-1]]),label(q)[1],label(~q)[1])
def compact(bg,wall,receiving,fg,grass,water,sand):
 report=[]
 for y0,y1 in [(0,416),(416,704)]:
  # Most frequent observed silhouette wins; explicit topology/distance bounds
  # protect turns, open shoulders, thin side walls and rounded terminal caps.
  freq=Counter(wall[y:y+8,x:x+8].tobytes() for y in range(y0,y1,8) for x in range(0,1152,8));bank=[];mapping={}
  for raw,n in freq.most_common():
   q=np.frombuffer(raw,bool).reshape(8,8);sig=signature(q);chosen=q
   if q.any() and not q.all():
    for b,bs,bd in bank:
     if sig!=bs or np.count_nonzero(q!=b)>(5 if y0==0 else 8):continue
     if np.any(q&~bd) or np.any(b&~binary_dilation(q)):continue
     chosen=b;break
    else:bank.append((q,sig,binary_dilation(q)))
   mapping[raw]=chosen
  mixed=defaultdict(list);full=defaultdict(list);changed=0
  for y in range(y0,y1,8):
   for x in range(0,1152,8):
    sl=np.s_[y:y+8,x:x+8];old=wall[sl].copy()
    if not old.any():continue
    q=mapping[old.tobytes()];a=bg[sl].copy();r=receiving[sl].copy()
    # A single accepted grass texture core at the contact strip saves spare
    # lawn variants, preserving room for the cliff silhouette and face detail.
    gc=np.unique(grass[...,:3].reshape(-1,3),axis=0)
    isgrass=np.any(np.all(r[...,:3,None]==gc.T[None,None,:,:],axis=2),axis=2)
    r[isgrass]=grass[:8,:8][isgrass]
    if y0:
     for material in [water,sand]:
      cc=np.unique(material[...,:3].reshape(-1,3),axis=0);inside=np.any(np.all(r[...,:3,None]==cc.T[None,None,:,:],axis=2),axis=2);r[inside]=material[:8,:8][inside]
    # Preserve the source stone colors at new <=1px contour positions.
    _,ix=distance_transform_edt(~old,return_indices=True);extended=a[ix[0],ix[1]];a[q]=extended[q];a[~q]=r[~q]
    changed+=np.count_nonzero(old!=q);wall[sl]=q;bg[sl]=a
    if q.all():full[plane(x,y)].append((y,x,a))
    else:
     under=r.copy();under[q]=0
     mixed[(q.tobytes(),under.tobytes(),plane(x,y))].append((y,x,a,q))
  # One exact texture representative per compatible outline/receiving plane.
  for group in mixed.values():
   if len(group)<2:continue
   values=np.stack([a[q,:3].reshape(-1) for y,x,a,q in group]).astype(float);center=values.mean(0);idx=np.argmin(((values-center)**2).sum(1));best=group[idx][2]
   for y,x,a,q in group:bg[y:y+8,x:x+8]=best
  texture_counts={}
  for role,group in full.items():
   unique={a.tobytes():a for y,x,a in group};arr=np.stack(list(unique.values()));values=arr[...,:3].reshape(len(arr),-1).astype(float);limits={'west':16,'east':16,'front':32,'plateau':8} if not y0 else {'west':16,'east':16,'front':32,'plateau':8};count=min(len(arr),limits[role]);texture_counts[role]=count
   if len(arr)<=count:continue
   centers,assign=kmeans2(values,count,minit='++',iter=30,seed=19)
   medoids=[]
   for k in range(count):
    ids=np.flatnonzero(assign==k)
    if not len(ids):continue
    i=ids[np.argmin(((values[ids]-centers[k])**2).sum(1))];medoids.append(arr[i])
   candidates=np.stack(medoids);vals=candidates[...,:3].astype(float)
   for y,x,a in group:
    index=np.argmin(((vals-a[None,...,:3])**2).sum(axis=(1,2,3)));bg[y:y+8,x:x+8]=candidates[index]
  report.append(dict(native_rows=[y0//16,y1//16],edge_templates=len(bank),mixed_material_modules=len(mixed),texture_modules=texture_counts,contour_pixels_adjusted=changed,maximum_contour_displacement=1,maximum_changed_pixels_per_8px_tile=5 if y0==0 else 8,topology='same component counts, corner occupancy and touched edges',foreground_changes=0))
 return report


def hidden_background(bg,fg):
 report=[]
 for y0,y1 in [(0,416),(416,704)]:
  qs=[(y,x,bg[y:y+8,x:x+8].copy(),fg[y:y+8,x:x+8,3]==0) for y in range(y0,y1,8) for x in range(0,1152,8)]
  freq=Counter(q.tobytes() for y,x,q,m in qs);bank=np.stack([np.frombuffer(k,np.uint8).reshape(8,8,4) for k,_ in freq.most_common()])
  for y,x,q,m in qs:
   if m.all():continue
   options=np.flatnonzero(np.all(bank[:,m]==q[m],axis=(1,2)))
   if len(options):bg[y:y+8,x:x+8]=bank[options[0]]
  after=len({bg[y:y+8,x:x+8].tobytes() for y,x,q,m in qs});report.append(dict(rows=[y0//16,y1//16],glyphs_before=len(freq),glyphs_after=after,visible_pixel_changes=0))
 return report
