"""Local well terrace assembly from the shared complete R02 family.
No town generator; native trace and two receiving stair adaptations are explicit.
"""
from pathlib import Path
import json,numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'gba/art/azalea-town/source';D=S/'well-gate-repair';E=S.parent/'evidence'
bg=np.array(Image.open(D/'background-before.png').convert('RGBA'));fg=np.array(Image.open(D/'foreground-before.png').convert('RGBA'));r=json.loads((D/'assembly-before.json').read_text());grass=np.array(Image.open(S/'masters/grass.png').convert('RGBA'));Y,X=np.indices(bg.shape[:2]);wall=np.zeros_like(bg);roles=np.zeros(bg.shape[:2],np.uint8);placements=[];whole=[]
# One receiving palette adjustment to the map's established grass shade.
A={}
for name in ['R01','R02','R05','R06','R15','R16']:
 a=np.array(Image.open(D/(name+'.png')).convert('RGBA'));a[np.all(a[...,:3]==[96,192,144],2),:3]=[104,200,152];A[name]=a;Image.fromarray(a).save(D/(name+'-native.png'))
for p in r['rock_placements']:
 if p['x']>=42 and p['y']<=18:bg[p['y']*16:p['y']*16+16,p['x']*16:p['x']*16+16]=grass[Y[p['y']*16:p['y']*16+16,p['x']*16:p['x']*16+16]%grass.shape[0],X[p['y']*16:p['y']*16+16,p['x']*16:p['x']*16+16]%grass.shape[1]]
def piece(name,x,y,w=16,h=16,mirror=False,role='side'):
 a=Image.fromarray(A[name]);a=a.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if mirror else a;a=np.array(a.resize((w,h),Image.Resampling.NEAREST)) if h!=24 else np.concatenate([np.array(a)[:8],np.array(a)[4:12],np.array(a)[8:16]],axis=0);wall[y:y+h,x:x+w]=a;roles[y:y+h,x:x+w]=1 if role=='front' else 2
 placements.append(dict(asset=name,x=x,y=y,width=w,height=h,mirror=mirror,role=role))
 if w==h==16 and x%16==y%16==0:whole.append(dict(tile='well-'+name,x=x//16,y=y//16,mirror=mirror))
# One continuous 24px outer drop, not two repeated front courses.
for x in range(704,848,16):piece('R01',x,104,h=24,role='front')
piece('R16',688,104,h=24,mirror=True,role='corner');piece('R16',848,104,h=24,role='corner')
# The offset northwest return leaves a complete western landing beside the ramp.
piece('R05',672,128,role='corner');piece('R02',688,128,role='front')
for y in range(144,256,16):piece('R06',672,y,mirror=True)
for y in range(128,288,16):piece('R06',848,y)
# Lower northern ramp progressively meets the eastern grass landing.
piece('R05',704,128,role='corner')
for x,h in [(720,16),(736,16),(752,16),(768,12),(784,12),(800,8),(816,8)]:piece('R02',x,128,h=h,role='tapered front')
# Inner terrace has its own 16px face and matching side/corner plane.
for x in range(736,816,16):piece('R01',x,176,role='front')
piece('R16',816,176,role='corner')
for y in range(192,272,16):piece('R06',816,y)
for y in range(144,256,16):piece('R06',704,y,mirror=True)
# Short front drop below the well court; wide north/south steps occupy its opening.
piece('R15',704,256,role='corner')
for x in range(720,768,16):piece('R01',x,256,role='front')
m=wall[...,3]>0;bg[m]=wall[m]
# Native gray variants retain the complete approved silhouettes and tread direction.
gray=np.array([[80,80,72],[96,96,96],[112,112,112],[144,144,144],[192,192,192]],int)
for name in ['S01','S03','S04','P03','P04']:
 a=np.array(Image.open(D/(name+'-original.png')).convert('RGBA'));mask=a[...,3]>0
 cs=np.unique(a[mask,:3],axis=0);source=a.copy()
 for i,c in enumerate(cs):a[np.all(source[...,:3]==c,2)&mask,:3]=gray[i] if name.startswith('S') else gray[np.argmin(((gray-c.astype(int))**2).sum(1))]
 a[~mask,:3]=0;Image.fromarray(a).save(D/(name+'-native.png'))
# Three inconsistent central rail-shading pixels are aligned with the adjacent
# intact tread section; silhouette and every tread endpoint are unchanged.
sa=np.array(Image.open(D/'S04-native.png').convert('RGBA'));sa[24:32,:8]=sa[16:24,:8];Image.fromarray(sa).save(D/'S04-native.png')
new=[]
def over(name,x,y,role):
 a=np.array(Image.open(D/(name+'-native.png')).convert('RGBA'));h,w=a.shape[:2];m=a[...,3]>0;fg[y:y+h,x:x+w][m]=a[m];new.append(dict(name='well-'+name,x=x,y=y,role=role))
over('S04',704,144,'Complete shared side stairs, descend west; east/west traversal')
over('S01',768,256,'North/south stair flight, left edge');over('S03',784,256,'North/south stair flight, right edge')
# Existing short ledge vocabulary marks the low southern return.
for x,name in [(800,'L11'),(816,'L12'),(832,'L12'),(848,'L13')]:
 a=np.array(Image.open(S/'masters'/(name+'.png')).convert('RGBA'));m=a[...,3]>0;fg[272:288,x:x+16][m]=a[m];new.append(dict(name=name,x=x,y=272,role='Lower southern terrace return / down-only ledge'))
# Complete aligned trees continue the northern forest behind the gate roof.
# Their root footprints stop at the real building front, not inside its walls.
railprops=[];newtrees=[];ta=np.array(Image.open(S/'masters/tree.png').convert('RGBA'));owner=np.zeros(fg.shape[:2],np.uint16)
for i,p in enumerate(r['placements'],1):
 a=np.array(Image.open(S/'masters'/(p['name']+'.png')).convert('RGBA'));h,w=a.shape[:2];owner[p['y']:p['y']+h,p['x']:p['x']+w][a[...,3]>0]=i
oldtreeids={i for i,p in enumerate(r['placements'],1) if p['name']=='tree'}
for x,y in [(0,192),(32,192),(64,192),(96,192),(96,224)]:
 old=owner[y:y+48,x:x+32];m=(ta[...,3]>0)&((old==0)|np.isin(old,list(oldtreeids)));fg[y:y+48,x:x+32][m]=ta[m];newtrees.append(dict(name='tree',x=x,y=y,role='Aligned forest extension behind gate roof; clear of building wall footprint'))
# One short existing rail closes the southern seam below the real gate base.
a=np.array(Image.open(D/'P04-native.png').convert('RGBA'));h,w=a.shape[:2];x,y=112,304;m=(a[...,3]>0)&(fg[y:y+h,x:x+w,3]==0);fg[y:y+h,x:x+w][m]=a[m];railprops.append(dict(name='gate-P04',x=x,y=y,role='Short shared rail joins gate base to the southern forest'))
# Reconstruct the receiving ground beneath the existing transparent foreground
# boulder instead of retaining its old native grass backing over the new cliff.
x,y=672,216;w=16;h=40;bg[y:y+h,x:x+w]=grass[Y[y:y+h,x:x+w]%grass.shape[0],X[y:y+h,x:x+w]%grass.shape[1]];mask=wall[y:y+h,x:x+w,3]>0;bg[y:y+h,x:x+w][mask]=wall[y:y+h,x:x+w][mask];fg[y:y+h,x:x+w]=0
for p in r['placements']:
 a=np.array(Image.open(S/'masters'/(p['name']+'.png')).convert('RGBA'));hh,ww=a.shape[:2];x0=max(x,p['x']);x1=min(x+w,p['x']+ww);y0=max(y,p['y']);y1=min(y+h,p['y']+hh)
 if x0>=x1 or y0>=y1:continue
 cut=a[y0-p['y']:y1-p['y'],x0-p['x']:x1-p['x']];m=cut[...,3]>0;fg[y0:y1,x0:x1][m]=cut[m]
Image.fromarray(bg).save(D/'target-background.png');Image.fromarray(fg).save(D/'target-foreground.png');Image.fromarray(wall).save(D/'terrain.png');np.save(D/'terrain-roles.npy',roles)
(D/'geometry.json').write_text(json.dumps(dict(shared_commit='82b98516aa17eeb538a0cd9adf373df8b3c7d3cb',registration=[64,16],wall_segments=placements,whole_tiles=whole,new_props=new,rail_props=railprops,new_trees=newtrees,adaptations=['One complete 24px outer drop, a separately tapering 16/12/8px lower ramp, and a 16px inner drop.','West outside side-plane shifts 8px from the traced midpoint to reserve a full native landing.','Shared west-descending stairs substitute for the reference sloped notch; two north/south edge tiles mark the southern descent.','Shared terrain grass shade (96,192,144) maps to the existing bank8 (104,200,152); four existing neutral shades encode stair/rail silhouettes.']),indent=2)+'\n')
out=bg.copy();m=fg[...,3]>0;out[m]=fg[m];Image.fromarray(out).save(D/'proposal.png')
