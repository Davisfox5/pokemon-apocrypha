"""Pinned correction of the rejected terrain pass using actual HGSS mesh/BDHC.
Never runs the first-authoring generator. Re-encodes this private map pair only.
"""
from pathlib import Path
import sys,json,subprocess,shutil,struct
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_edt,binary_opening,binary_closing,binary_dilation,binary_erosion,gaussian_filter,binary_fill_holes
ROOT=Path(__file__).resolve().parents[4];G=Path(sys.argv[1]);PT=Path(sys.argv[2]);S=ROOT/'gba/art/route38-39-terrain/source';D=S/'refinement';E=S.parent/'evidence/refinement';M=S/'masters'
assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()=='fee08659d8f68d735ac48e507554526a9d72e9d3','Apply only to the reviewed first pass.'
B=E/'before'
if not B.exists():
 B.mkdir()
 for n in [38,39]:
  for tag in ['native','native-grid','comparison','levels']:
   p=E.parent/f'route{n}-{tag}.png'
   if p.exists():shutil.copyfile(p,B/p.name)
art={p.stem:np.array(Image.open(p).convert('RGBA')) for p in M.glob('*.png')};allpairs=[];unique={};maps=[];reports=[];boundarycases=[]
def rounded(mask,r=3):
 yy,xx=np.ogrid[-r:r+1,-r:r+1];disk=xx*xx+yy*yy<=r*r
 return binary_closing(binary_opening(mask,structure=disk,border_value=0),structure=disk,border_value=0)
def geom(route,W,H,members):
 ph,pw=H*16,W*16;Y,X=np.indices((ph,pw));heights=np.full((ph,pw),np.nan);road=Image.new('L',(pw,ph));wall=road.copy();ramps=road.copy();grassramps=road.copy();nx=np.zeros((ph,pw));nz=nx.copy();weight=nx.copy();planes=[]
 for mid,ox,oy in members:
  data=json.loads((D/f'chunk{mid}-geometry.json').read_text())
  for p in data['planes']:
   x1,z1,x2,z2=p['rect'];a,b,c=p['normal'];dist=p['distance'];planes.append(dict(member=mid,rect=[x1+ox,z1+oy,x2+ox,z2+oy],normal=[a,b,c],distance=dist))
   m=(X/16+.03125>=x1+ox)&(X/16+.03125<x2+ox)&(Y/16+.03125>=z1+oy)&(Y/16+.03125<z2+oy)
   v=-(a*(X/16+.03125-ox-16)+c*(Y/16+.03125-oy-16)+dist)/b;heights[m]=v[m]
  for t in data['triangles']:
   name=t['material'];v=np.array(t['xyz']);ps=[((q[0]+16+ox)*16,(q[2]+16+oy)*16) for q in v]
   if name.startswith('road01'):ImageDraw.Draw(road).polygon(ps,fill=255)
   if name=='slope':ImageDraw.Draw(ramps).polygon(ps,fill=255)
   if name=='grass_slope':ImageDraw.Draw(grassramps).polygon(ps,fill=255)
   if not name.startswith(('wall01','wall_area06')):continue
   ImageDraw.Draw(wall).polygon(ps,fill=255)
   normal=np.cross(v[1]-v[0],v[2]-v[0]);length=np.linalg.norm(normal[[0,2]])
   if length<1e-5:continue
   if normal[1]<0:normal=-normal
   normal=normal[[0,2]]/length
   tmp=Image.new('L',(pw,ph));ImageDraw.Draw(tmp).polygon(ps,fill=255);m=np.array(tmp)>0
   nx[m]+=normal[0];nz[m]+=normal[1];weight[m]+=1
 # Missing BDHC coverage is rock or occluded ground, never a claimed original
 # walkable flat. Fill it from its closest defined plane only for native backing.
 known=np.isfinite(heights);ix=distance_transform_edt(~known,return_distances=False,return_indices=True);heights[~known]=heights[tuple(ix[:,~known])]
 valid=weight>0
 if valid.any():
  ids=distance_transform_edt(~valid,return_distances=False,return_indices=True);nx[~valid]=nx[tuple(ids[:,~valid])];nz[~valid]=nz[tuple(ids[:,~valid])]
 nx=gaussian_filter(nx,1.5);nz=gaussian_filter(nz,1.5)
 normal=np.hypot(nx,nz);nx/=np.maximum(normal,1e-6);nz/=np.maximum(normal,1e-6)
 return heights,known,np.array(road)>0,np.array(wall)>0,np.array(ramps)>0,np.array(grassramps)>0,nx,nz,planes
for route,W,H,members in [(38,64,32,[(54,0,0),(55,32,0)]),(39,32,64,[(56,0,0),(57,0,32)])]:
 h,known,road,wall,ramp,gramp,nx,nz,planes=geom(route,W,H,members);Y,X=np.indices(h.shape)
 # Keep the original three-cell stair axis; model shoulders are wall joins.
 valid_ramp=np.zeros((H,W),bool)
 for sy,sx in np.ndindex(H,W):
  hh=h[sy*16+8,sx*16+8];valid_ramp[sy,sx]=known[sy*16+8,sx*16+8] and abs(hh-round(hh))>.1 and ramp[sy*16:(sy+1)*16,sx*16:(sx+1)*16].mean()>.1
 ramp=np.repeat(np.repeat(valid_ramp,16,0),16,1)
 # Classify the original road mesh on its actual16-unit DS grid. The overview's
 # camera projection is not traced or scaled into dirt silhouettes.
 path=np.zeros((H,W),bool)
 for y,x in np.ndindex(H,W):path[y,x]=road[y*16:y*16+16,x*16:x*16+16].mean()>=.35
 pm=np.repeat(np.repeat(path,16,0),16,1);pm=rounded(np.pad(pm,4,mode='edge'),3)[4:-4,4:-4]
 bg=art['grass'][Y%32,X%32].copy();bg[pm]=art['path'][Y[pm]%32,X[pm]%32];bg[binary_dilation(pm)&~pm,:3]=[88,176,136];bg[pm&~binary_erosion(pm),:3]=[184,168,128]
 # Source geometry supplies the continuous wall footprint and rounded turns.
 # Choose the face by its actual downhill normal, not by which side of the map.
 wm=rounded(np.pad(wall,4,mode='edge'),3)[4:-4,4:-4]
 wm &= ~(ramp|gramp)
 # Front-facing depth follows the original rise: one native16px course per
 # height unit. Side width and back rims retain original mesh footprints.
 expanded=wm.copy()
 for x in range(W*16):
  line=np.flatnonzero(wm[:,x]&(nz[:,x]>.65));starts=[]
  for y in line:
   if not starts or y>starts[-1][-1]+1:starts.append([y])
   else:starts[-1].append(y)
  for run in starts:
   a,b=run[0],run[-1];upper=float(h[max(0,a-4),x]);lower=float(h[min(H*16-1,b+5),x]);drop=max(0,round(upper-lower))
   if drop>0:
    end=min(H*16,a+drop*16);expanded[a:end,x]=True
 # Restore original slope openings after contour extrusion.
 wm=expanded&~(ramp|gramp);wm=rounded(np.pad(wm,4,mode='edge'),2)[4:-4,4:-4]
 valid=wall&((abs(nx)+abs(nz))>.1);ids=distance_transform_edt(~valid,return_distances=False,return_indices=True);nx=nx[tuple(ids)];nz=nz[tuple(ids)]
 face=np.where(abs(nz)>=abs(nx),np.where(nz>=0,0,3),np.where(nx<0,1,2))
 # Matching brown material, with separate front/back and left/right ramps.
 # Texture is reused verbatim; only footprint masking and the receiving lawn lip
 # are new. Whole-map normals keep corners connected through neighboring cells.
 for f in range(4):
  m=wm&(face==f)
  for alt in [0,1]:
   mm=m&((X//16)%2==alt if f in [0,3] else (Y//16)%2==alt)
   a=art[('R02' if alt else 'R04') if f in [0,3] else ('R11' if alt else 'R12')]
   if f==2:a=a[:,::-1]
   if f==3:a=a[::-1]
   bg[mm]=a[Y[mm]%16,X[mm]%16]
 # Cap follows the higher side; contact shadow follows the lower side.
 yy=np.clip(Y-np.rint(nz*3).astype(int),0,H*16-1);xx=np.clip(X-np.rint(nx*3).astype(int),0,W*16-1)
 cap=wm&~wm[yy,xx];bg[cap]=art['grass'][Y[cap]%32,X[cap]%32]
 yy=np.clip(Y+np.rint(nz*2).astype(int),0,H*16-1);xx=np.clip(X+np.rint(nx*2).astype(int),0,W*16-1)
 foot=wm&~wm[yy,xx]&~cap;bg[foot,:3]=[72,56,40]
 # Preserve original slope footprints and the owner's accepted stair material.
 slope_cells=np.zeros((H,W),bool);grass_slope_cells=slope_cells.copy()
 for y,x in np.ndindex(H,W):
  sl=np.s_[y*16:y*16+16,x*16:x*16+16];slope_cells[y,x]=valid_ramp[y,x];grass_slope_cells[y,x]=gramp[sl].mean()>.2
  if not slope_cells[y,x]:continue
  if route==38:
   # Original west junction is a short earth ramp, not another invented gate.
   bg[sl]=art['path'][Y[sl]%32,X[sl]%32]
   for sx in [3,11]:bg[y*16:(y+1)*16,x*16+sx,:3]=[192,176,128]
  else:
   # Source main stair is three cells wide; same original Emerald treads.
   # Native placement is aligned to actual slope cells from the model.
   left=not(x>0 and slope_cells[y,x-1]);a=art['0xaf' if left else '0xcf'].copy();a[...,:3]&=248;aa=a[...,3]>0;bg[sl][aa]=a[aa]
 # Gentle grass slope in the paddock remains a traversable height transition.
 for y,x in np.argwhere(grass_slope_cells):
  sl=np.s_[y*16:y*16+16,x*16:x*16+16];bg[sl]=art['grass'][Y[sl]%32,X[sl]%32];bg[y*16+12:y*16+15,x*16:(x+1)*16,:3]=[88,176,136]
 solid=np.zeros((H,W),bool);levels=np.zeros((H,W),np.uint8);mat=np.full((H,W),'lawn',dtype='<U16');knowncells=known.reshape(H,16,W,16).transpose(0,2,1,3).mean((2,3));actual=np.zeros((H,W))
 for y,x in np.ndindex(H,W):
  sl=np.s_[y*16:y*16+16,x*16:x*16+16];actual[y,x]=h[y*16+8,x*16+8];levels[y,x]=int(np.clip(round(actual[y,x])*2-1,1,13));solid[y,x]=wm[sl].sum()>24;mat[y,x]='rock' if solid[y,x] else 'path' if path[y,x] else 'lawn'
  if slope_cells[y,x] or grass_slope_cells[y,x]:levels[y,x]=0;solid[y,x]=False;mat[y,x]='earth-ramp' if route==38 else 'grass-ramp' if grass_slope_cells[y,x] else 'stairs'
 # Closed rock contours are inaccessible raised pockets. The walking-height
 # table may continue below them; use the surrounding original mesh rim here.
 holes=binary_fill_holes(wm)&~wm
 for hy,hx in np.argwhere(holes.reshape(H,16,W,16).transpose(0,2,1,3).mean((2,3))>.3):
  top=[]
  for mid,ox,oy in members:
   for t in json.loads((D/f'chunk{mid}-geometry.json').read_text())['triangles']:
    if not t['material'].startswith('wall01'):continue
    q=np.array(t['xyz']);xx=q[:,0]+16+ox;zz=q[:,2]+16+oy
    if xx.min()<hx+2 and xx.max()>hx-1 and zz.min()<hy+2 and zz.max()>hy-1:top.extend(q[:,1].tolist())
  if top:levels[hy,hx]=round(max(top))*2-1;actual[hy,hx]=round(max(top));knowncells[hy,hx]=0
  solid[hy,hx]=True;mat[hy,hx]='raised-rock'
 # Native outer review perimeter; the actual east/west junction is opened below.
 solid[0]=solid[-1]=True;solid[:,0]=solid[:,-1]=True
 # Each side has the same original global matrix row coordinates.
 if route==38:solid[11:14,0]=False
 else:solid[11:14,-1]=False
 # Store actual native current layers and separate original height evidence.
 bg[...,:3]&=248;Image.fromarray(bg).save(D/f'route{route}-terrain.png');np.save(D/f'route{route}-solid.npy',solid);np.save(D/f'route{route}-elevation.npy',levels);np.save(D/f'route{route}-actual-height.npy',actual);np.save(D/f'route{route}-known-height.npy',knowncells)
 (D/f'route{route}-materials.json').write_text('[\n'+',\n'.join(json.dumps(row.tolist()) for row in mat)+'\n]\n')
 # Source height proof and native wall direction/depth ledger stay independent.
 ledger=[];bad=[]
 for y,x in np.ndindex(H,W):
  if solid[y,x]:
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
    xx,yy=x+dx,y+dy
    if 0<=xx<W and 0<=yy<H and not solid[yy,xx]:boundarycases.append(dict(route=route,map=53 if route==38 else 54,x=xx,y=yy,direction={(1,0):'LEFT',(-1,0):'RIGHT',(0,1):'UP',(0,-1):'DOWN'}[(dx,dy)]))
  for dx,dy in [(1,0),(0,1)]:
   xx,yy=x+dx,y+dy
   if xx<W and yy<H and not solid[y,x] and not solid[yy,xx] and levels[y,x] and levels[yy,xx] and levels[y,x]!=levels[yy,xx]:bad.append([x,y,xx,yy,int(levels[y,x]),int(levels[yy,xx])])
  ledger.append(dict(x=x,y=y,original_height=round(float(actual[y,x]),4),original_BDHC_coverage=round(float(knowncells[y,x]),3),native_elevation=int(levels[y,x]),blocked=bool(solid[y,x]),material=str(mat[y,x])))
 (E/f'route{route}-height-ledger.json').write_text('[\n'+',\n'.join(json.dumps(v,separators=(',',':')) for v in ledger)+'\n]\n');(E/f'route{route}-open-height-seams.json').write_text(json.dumps(bad)+'\n')
 cells=[]
 for y,x in np.ndindex(H,W):
  a=bg[y*16:y*16+16,x*16:x*16+16];k=a.tobytes()
  if k not in unique:unique[k]=len(allpairs);allpairs.append(a.copy())
  cells.append(unique[k]|int(levels[y,x])<<12|(0xc00 if solid[y,x] else 0))
 maps.append((route,W,H,np.array(cells,'<u2').reshape(H,W)))
 reports.append(dict(route=route,width=W,height=H,wall_cells=int((mat=='rock').sum()),stairs=np.argwhere(slope_cells).tolist(),grass_ramp=np.argwhere(grass_slope_cells).tolist(),open_height_seams=bad))
 Image.fromarray(bg).save(E/f'route{route}-candidate.png')
print(json.dumps(reports,indent=2));(E/'geometry-audit.json').write_text(json.dumps(reports,indent=2)+'\n')
# Stop before installation until material/direction and logical heights are reviewed.
np.savez(D/'native-candidate.npz',**{f'route{n}':grid for n,w,h,grid in maps},pairs=np.array(allpairs));(E/'boundary-cases.json').write_text(json.dumps(boundarycases)+'\n')
