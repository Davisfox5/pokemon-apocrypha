"""Fresh Slowpoke Well scene from decoded HGSS heights and permissions.
Fixed baseline snapshots are inputs. This is a local authoring tool, not a town generator.
"""
from pathlib import Path
import sys,json,numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion,binary_dilation
from scipy.optimize import milp,Bounds,LinearConstraint
from scipy.sparse import lil_matrix
from well_scene_pieces import frlg_pieces,FRLG_NINE,FRLG_NINE_OVER_ROCK,FRLG_INNER
HUB=Path(__file__).resolve().parents[4];S=HUB/'gba/art/azalea-town/source';D=S/'well-scene';E=S.parent/'evidence';G=Path(sys.argv[1]);M=S/'masters';W,H=64,33
bg=np.array(Image.open(D/'before-background.png').convert('RGBA'));fg=np.array(Image.open(D/'before-foreground.png').convert('RGBA'));oldcomp=bg.copy();q=fg[...,3]>0;oldcomp[q]=fg[q]
r=json.loads((D/'assembly-before.json').read_text());p=np.load(D/'hgss-permissions.npz');flat=np.load(D/'flat.npz');types,coll=p['types'],p['collision'];names=list(flat['names']);matpx=flat['mat'];heights=flat['height'];DX,DY=-1,7
core=np.zeros((H*16,W*16),bool);core[48:368,640:944]=True
# Remove entire rejected scene objects; retain unrelated town objects.
removed=[];keep=[]
for obj in r['placements']:
 x,y=obj['x'],obj['y'];im=np.array(Image.open(M/(obj['name']+'.png')).convert('RGBA'));hh,ww=im.shape[:2]
 affected=(obj['name']=='tree' and 640<=x<944 and 48<=y<368) or obj['name'].startswith('well-') or obj['name']=='well' or (obj['name'] in ['boulder','small-boulder','P12','P13','L11','L12','L13'] and x>=640 and y<352) or (obj['name']=='F01' and x>=736 and y<352)
 if affected:removed.append(obj);core[y:y+hh,x:x+ww]=True
 else:keep.append(obj)
# Entire foreground/background are reset locally to genuine grass, not the rejected layout.
Y,X=np.indices(bg.shape[:2]);grass=np.array(Image.open(M/'grass.png').convert('RGBA'));path=np.array(Image.open(M/'path.png').convert('RGBA'));bg[core]=grass[Y[core]%32,X[core]%32];fg[core]=0
solid=np.load(D/'before-solid.npy');beh=np.load(D/'before-behaviors.npy');materials=np.load(D/'before-material-grid.npy');cells=core.reshape(H,16,W,16).any((1,3));solid[cells]=False;beh[cells]=0;materials[cells]='.'
roots=np.zeros((H,W),np.uint8)
for obj in keep:
 if obj['name']=='tree':x,y=obj['x']//16,obj['y']//16;roots[y+1:y+3,x:x+2]+=1
# Raw height/material ledger. Surface heights exclude foliage, boulders and flower planes.
terrain_names={'wall01_g','wall01_d','cliff01gs'};surface_names={'grass01gs','grass01_a','grass02','grass02_r','road01','road01_r'};iswall=np.isin(matpx,[names.index(n) for n in terrain_names if n in names]);issurface=np.isin(matpx,[names.index(n) for n in surface_names if n in names]);levels=np.ones((32,64),float);rock=np.zeros((32,64),bool);ledger=[]
for hz,hx in np.ndindex(32,64):
 sl=np.s_[hz*16:hz*16+16,hx*16:hx*16+16];hh=heights[sl];rw=iswall[sl];sf=issurface[sl];blocked=bool(coll[hz,hx]&128)
 rock[hz,hx]=blocked and rw.sum()>=8
 if rock[hz,hx]:level=float(np.nanmax(hh[rw]));level=float(np.ceil(level-0.08))
 elif types[hz,hx]==6:level=1.
 elif sf.any():level=float(np.nanmedian(hh[sf]));level=float(np.round(level))
 else:level=1.
 levels[hz,hx]=level
 if 40<=hx<=60 and hz<18:ledger.append(dict(hgss=[hx,hz],native=[hx+DX,hz+DY],terrain_type=int(types[hz,hx]),collision_byte=int(coll[hz,hx]),blocked=blocked,world_height=level,relative_to_town=level-1,rock=bool(rock[hz,hx]),raw_ground_height_range=[float(np.nanmin(hh[sf|rw])) if (sf|rw).any() else None,float(np.nanmax(hh[sf|rw])) if (sf|rw).any() else None]))
# The former generic small boulder was oversized. Decode the real 15x8 etc_a
# stone silhouette, with transparent background and the existing native stone ramp.
import sys as _sys
_sys.path.insert(0,str(HUB/'tools/gba/maps'));from tiles import Tileset
stone=np.zeros((16,16,4),np.uint8);cut=flat['rgb'][176:192,752:768].astype(np.uint8);mask=(matpx[176:192,752:768]==names.index('etc_a'));stone[mask,:3]=cut[mask];stone[mask,3]=255;Image.fromarray(stone).save(D/'small-stone-hgss.png')
pal=np.array(Tileset(G,'azalea','azalea').pals[1][7][1:],int)
for c in np.unique(stone[mask,:3],axis=0):
 k=np.argmin(((pal-c.astype(int))**2).sum(1));stone[np.all(stone[...,:3]==c,2)&mask,:3]=pal[k]
Image.fromarray(stone).save(M/'well-small-stone.png')
# Recreate actual well dirt material at pixel level with the accepted native texture.
road_material=np.isin(matpx,[names.index(n) for n in ['road01','road01_r']]);source_rgb=flat['rgb'];road=road_material&(source_rgb[...,0]>source_rgb[...,1]+8);dirt=np.zeros(core.shape,bool)
for hz in range(16):
 for hx in range(41,60):
  nx,ny=hx+DX,hz+DY
  if not(0<=nx<W and 0<=ny<H):continue
  sl=np.s_[ny*16:ny*16+16,nx*16:nx*16+16];hs=np.s_[hz*16:hz*16+16,hx*16:hx*16+16];dirt[sl]=road[hs]
# Reuse the existing native Cherrygrove-style ground kit for 8px transitions.
# Only the shape comes from HGSS. This avoids treating the green corners inside
# road01_r as dirt, or manufacturing a new noisy pixel curve for every placement.
from collections import Counter
base=np.array(Image.open(D/'before-background.png').convert('RGBA'));basefg=np.array(Image.open(D/'before-foreground.png').convert('RGBA'))
gc=set(map(tuple,grass[...,:3].reshape(-1,3)));pc=set(map(tuple,path[...,:3].reshape(-1,3)))|{(184,168,128)};allowed_colors=gc|pc|{(88,176,136)}
classes=np.zeros((66,128),np.uint8);eligible=np.zeros_like(classes,bool)
for gy,gx in np.ndindex(classes.shape):
 cut=base[gy*8:gy*8+8,gx*8:gx*8+8];cs=set(map(tuple,cut[...,:3].reshape(-1,3)))
 if cut[...,3].min()<255 or not cs<=allowed_colors:continue
 ng=sum(tuple(c) in gc for c in cut[...,:3].reshape(-1,3));npth=sum(tuple(c) in pc for c in cut[...,:3].reshape(-1,3));classes[gy,gx]=1 if ng>=npth else 2;eligible[gy,gx]=not basefg[gy*8:gy*8+8,gx*8:gx*8+8,3].any()
neighbor=[(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1)]
def key(k,x,y):
 me=int(k[y,x]);return (me,)+tuple(int(k[yy,xx]) or me if 0<=yy<66 and 0<=xx<128 else me for dx,dy in neighbor for xx,yy in [(x+dx,y+dy)])
lib={}
for gy,gx in np.argwhere(eligible):
 k=key(classes,int(gx),int(gy));lib.setdefault(k,[]).append((int(gx)%4,int(gy)%4,base[gy*8:gy*8+8,gx*8:gx*8+8].copy()))
k=np.where(dirt.reshape(66,8,128,8).mean((1,3))>=.5,2,1).astype(np.uint8);ground_reuse=[]
for gy,gx in np.argwhere(core.reshape(66,8,128,8).any((1,3))):
 wanted=key(k,int(gx),int(gy));candidates=[v for v in lib if v[0]==wanted[0]]
 score=lambda v:sum((16 if i%2==0 else 1)*(v[i+1]!=wanted[i+1]) for i in range(8))
 match=min(candidates,key=lambda v:(score(v),v));opts=lib[match];phase=[v for v in opts if v[0]==gx%4 and v[1]==gy%4];opts=phase or opts;hist=Counter(a[2].tobytes() for a in opts);raw=max(sorted(hist),key=hist.get);bg[gy*8:gy*8+8,gx*8:gx*8+8]=np.frombuffer(raw,np.uint8).reshape(8,8,4)
 if wanted!=match:ground_reuse.append(dict(native_8px_cell=[int(gx),int(gy)],requested=list(wanted),used=list(match),weighted_difference=int(score(match))))
(D/'ground-kit-adaptations.json').write_text(json.dumps(ground_reuse,indent=2)+'\n')
# Existing FRLG direction/corner modules as used by accepted Blackthorn/Mahogany.
# Use the established Azalea/Johto RGB5 ramp; no silhouette or texture is redrawn.
pieces=frlg_pieces(G);ramp=np.array([[88,80,72],[192,144,96],[160,120,96],[160,112,80],[136,104,80],[104,72,56],[80,56,64]],np.uint8);shadow=np.array([104,200,152],np.uint8);directions=dict(n=(0,-1),ne=(1,-1),e=(1,0),se=(1,1),s=(0,1),sw=(-1,1),w=(-1,0),nw=(-1,-1));wallmods=[];wallmask=np.zeros((H,W),bool)
level=lambda x,y:levels[min(31,max(0,y)),min(63,max(0,x))]
for hz in range(16):
 for hx in range(41,60):
  if not rock[hz,hx]:continue
  nx,ny=hx+DX,hz+DY;me=levels[hz,hx];lo={k:level(hx+dx,hz+dy)<me for k,(dx,dy) in directions.items()};ix=np.full((16,16),-1,int);mod=[]
  diag=[k for k in ['ne','se','sw','nw'] if lo[k]];whole=pieces['inner'][diag[0]] if not any(lo[k] for k in 'nesw') and len(diag)==1 else None
  for qy,qx in np.ndindex(2,2):
   v=('N','S')[qy] if lo['n'] and lo['s'] else 'N' if lo['n'] else 'S' if lo['s'] else 'M';h=('W','E')[qx] if lo['w'] and lo['e'] else 'W' if lo['w'] else 'E' if lo['e'] else 'M';vk,hk='ns'[qy],'we'[qx];sl=np.s_[qy*8:qy*8+8,qx*8:qx*8+8];toward=next((directions[k] for k in [vk,hk,vk+hk] if lo[k]),None)
   beyondrock=False
   if toward:
    bx,by=hx+toward[0],hz+toward[1];beyondrock=0<=bx<64 and 0<=by<32 and rock[by,bx]
   if whole is not None:tile=whole;source=f'inner:{diag[0]}'
   elif lo[vk+hk] and not lo[vk] and not lo[hk]:tile=pieces['inner'][vk+hk];source=f'inner:{vk+hk}'
   else:tile=pieces['rock' if beyondrock else 'nine'][(v,h)];source=f'{"over-rock" if beyondrock else "over-ground"}:{v}{h}'
   ix[sl]=tile[sl];mod.append(dict(quadrant=[qx,qy],source=source))
  im=np.zeros((16,16,4),np.uint8);m=ix>=0;im[m,:3]=ramp[ix[m]];im[m,3]=255;m=ix==-2;im[m,:3]=shadow;im[m,3]=255
  x,y=nx*16,ny*16;fg[y:y+16,x:x+16]=im;wallmask[ny,nx]=True;materials[ny,nx]='R'
  # Opaque rock quadrants have a true rock backing, never a pasted donor lawn.
  for qy,qx in np.ndindex(2,2):
   sl=np.s_[qy*8:qy*8+8,qx*8:qx*8+8]
   if np.all(im[sl][...,3]):bg[y+qy*8:y+qy*8+8,x+qx*8:x+qx*8+8,:3]=ramp[pieces['nine'][('M','M')][sl]]
  wallmods.append(dict(hgss=[hx,hz],native=[nx,ny],level=float(me),downhill=[k for k in directions if lo[k]],native_quadrants=mod))
# Original permissions, including low collision bits that are NOT blockers.
forest=np.zeros((H,W),bool)
for y,x in np.argwhere(cells):
 hx,hz=x-DX,y-DY
 if 0<=hx<64 and 0<=hz<32:
  solid[y,x]=bool(coll[hz,hx]&128);forest[y,x]=types[hz,hx]==6
  if types[hz,hx]==0x3b:beh[y,x]=59;materials[y,x]='L'
 elif hz<0:solid[y,x]=True;forest[y,x]=True
 if forest[y,x]:materials[y,x]='T'
# Complete trees: solve 2x2 root packing against the decoded woods and retained roots.
candidates=[]
for y in range(4,23):
 for x in range(40,59):
  if y+1<H and x+1<W and forest[y:y+2,x:x+2].all() and not roots[y:y+2,x:x+2].any():candidates.append((x,y))
A=lil_matrix((H*W,len(candidates)))
for i,(x,y) in enumerate(candidates):
 for yy in range(y,y+2):
  for xx in range(x,x+2):A[yy*W+xx,i]=1
cost=np.array([-1-0.0001*((x%2)==1)-0.00001*((y%2)==1) for x,y in candidates]);opt=milp(cost,integrality=np.ones(len(cost)),bounds=Bounds(0,1),constraints=LinearConstraint(A.tocsr(),0,1),options={'time_limit':10});assert opt.x is not None
newtrees=[dict(name='tree',x=x*16,y=(y-1)*16,role='HGSS woods / complete independent T01 roots') for (x,y),v in zip(candidates,opt.x) if v>.5]
for p in newtrees:
 x,y=p['x']//16,p['y']//16;assert not roots[y+1:y+3,x:x+2].any();roots[y+1:y+3,x:x+2]+=1
props=[dict(name='well',x=744,y=184,role='Existing transparent well master; front approaches HGSS cell49,8'),dict(name='P13',x=744,y=296,role='Original HGSS sign anchor48.5,13.5'),dict(name='boulder',x=648,y=272,role='Original HGSS rock01 boulder west of well'),dict(name='well-small-stone',x=736,y=288,role='Stone beside original southern wall / sign')]
# Reuse the shared flowers at the original HGSS flower cells.
fc=(matpx==names.index('flower03')).reshape(32,16,64,16).sum((1,3))
for hz,hx in np.argwhere(fc>32):
 nx,ny=int(hx)+DX,int(hz)+DY
 if 40<=nx<59 and 3<=ny<23:props.append(dict(name='F01',x=nx*16,y=ny*16,role='HGSS flower03 cell with shared native flowers'))
# Original surrounding ledge: retain the shared actual ledge silhouette and signed direction.
for y,x in np.argwhere(cells & (beh==59)):
 left=x>0 and beh[y,x-1]==59;right=x+1<W and beh[y,x+1]==59;props.append(dict(name='L12' if left and right else 'L11' if right else 'L13',x=x*16,y=y*16,role='HGSS jump-south ledge'))
# Repaint canonical retained objects locally, then new complete trees and well props.
newobjects=newtrees+props
for p in keep+newobjects:
 a=np.array(Image.open(M/(p['name']+'.png')).convert('RGBA'));a[...,:3]&=248;hh,ww=a.shape[:2];x,y=p['x'],p['y'];assert 0<=x and 0<=y and x+ww<=W*16 and y+hh<=H*16
 mask=a[...,3]>0
 if p in keep:mask &= core[y:y+hh,x:x+ww]
 else:core[y:y+hh,x:x+ww]=True
 fg[y:y+hh,x:x+ww][mask]=a[mask]
# Forest collision remains on all original wood cells, even where a complete tree
# cannot cover a narrow residual run. No walkable gaps are introduced.
solid[roots>0]=True
# Native well silhouette is slightly wider than HGSS; keep original passage columns47/51 open.
solid[12:15,47:50]=True;solid[15,48]=False;beh[15,48]=0
# Source sign and boulders are scenery blockers.
solid[20,47]=True;solid[18,41:43]=True;solid[19,47]=True
# Keep town/world edges closed as before.
solid[0]=True;solid[-1]=True;solid[:,0]=True;solid[:,-1]=True
above=np.zeros((H,W),bool)
for p in keep+newobjects:
 if p['name']=='tree':x,y=p['x']//16,p['y']//16;above[y,x:x+2]=True
bg[...,:3]&=248;fg[...,:3]&=248;comp=bg.copy();m=fg[...,3]>0;comp[m]=fg[m]
# All changed visible pixels lie in the authorized scene (including whole moved trees).
changed=np.any(comp!=oldcomp,2);assert not changed[~core].any()
Image.fromarray(bg).save(D/'target-background.png');Image.fromarray(fg).save(D/'target-foreground.png');Image.fromarray(comp).save(D/'proposal.png');np.save(D/'solid.npy',solid);np.save(D/'behaviors.npy',beh);np.save(D/'material.npy',materials);np.save(D/'roots.npy',roots);np.save(D/'above.npy',above);np.save(D/'edit-mask.npy',core)
(D/'ledger.json').write_text(json.dumps(dict(authority='Decoded HGSS land_data height mesh, header74 area4; no screenshot guessed heights',town_world_height=1,well_world_height=-2,well_relative_to_town=-3,native_registration=[DX,DY],cells=ledger,wall_modules=wallmods),indent=2)+'\n')
(D/'placements.json').write_text(json.dumps(dict(retained=keep,new=newobjects,removed=removed,trees=[[p['x']//16,p['y']//16] for p in keep+newobjects if p['name']=='tree']),indent=2)+'\n')
print('Fresh scene:',len(wallmods),'signed cliff cells;',len(newtrees),'complete trees;',changed.sum(),'changed visible pixels')
