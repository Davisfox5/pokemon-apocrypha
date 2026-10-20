"""Guarded refinement of existing Ecruteak native sources, not layout regeneration.

Only the two private tilesets/layouts are re-encoded. Original source, native
entry attributes, placements and before evidence are locked before editing.
"""
from pathlib import Path
import sys,json,subprocess,hashlib,shutil,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'));from tiles import Tileset
G=Path(sys.argv[1]);PT=Path(sys.argv[2]);S=ROOT/'gba/art/ecruteak-city/source';E=S.parent/'evidence';D=S/'refinement';B=D/'baseline';M=S/'masters';W,H=72,52
assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()=='dbf53f6f3975eb20179c26badd6ba48169857ad1','Patch only the reviewed first-pass source.'
if not B.exists():
 B.mkdir();shutil.copytree(M,B/'masters')
 for n in ['background.png','foreground.png','material-grid.npy','ground-material-grid.npy','solid.npy','behaviors.npy','tree-footprints.npy']:shutil.copyfile(S/n,B/n)
 shutil.copyfile(E/'assembly.json',B/'assembly.json');shutil.copyfile(E/'native-map.png',B/'native-map.png')
 lock={}
 for p in G.glob('data/tilesets/*/ecruteak_*/*'):
  for q in ([p] if p.is_file() else p.glob('*')):
   if q.is_file():lock[str(q.relative_to(G))]=hashlib.sha256(q.read_bytes()).hexdigest()
 for p in G.glob('data/layouts/JohtoEcruteak*/*.bin'):lock[str(p.relative_to(G))]=hashlib.sha256(p.read_bytes()).hexdigest()
 (B/'native-input-lock.json').write_text(json.dumps(lock,indent=2)+'\n')
oldbg=np.array(Image.open(B/'background.png').convert('RGBA'));oldfg=np.array(Image.open(B/'foreground.png').convert('RGBA'));bg=oldbg.copy();fg=oldfg.copy();solid=np.load(B/'solid.npy');beh=np.load(B/'behaviors.npy');mat=np.load(B/'material-grid.npy');ground=np.load(B/'ground-material-grid.npy');above=np.zeros((H,W),bool);assembly=json.loads((B/'assembly.json').read_text())
# Decode the baseline attributes from the immutable native inputs, rather than
# reconstructing engine behavior from authoring labels.
for name,bank,h,y0 in [('JohtoEcruteakTempleDistrict','ecruteak_temple',27,0),('JohtoEcruteakCity','ecruteak_city',25,27)]:
 g=np.frombuffer(subprocess.check_output(['git','-C',str(G),'show','HEAD:data/layouts/'+name+'/map.bin']),'<u2').reshape(h,W)
 aa=[]
 for side in ['primary','secondary']:aa.append(np.frombuffer(subprocess.check_output(['git','-C',str(G),'show',f'HEAD:data/tilesets/{side}/{bank}/metatile_attributes.bin']),'<u2'))
 for y,x in np.ndindex(h,W):mid=int(g[y,x]&1023);above[y+y0,x]=(aa[mid>=512][mid%512]&0x3000)==0
art={p.stem:np.array(Image.open(p).convert('RGBA')) for p in (B/'masters').glob('*.png')};Y,X=np.indices((H*16,W*16));changes=[]
def save(name,a):
 a=a.copy();a[...,:3]&=248;a[a[...,3]==0,:3]=0;art[name]=a;Image.fromarray(a).save(M/(name+'.png'))
def texture(mask,name):
 a=art[name];bg[mask]=a[(Y[mask]-16)%len(a),(X[mask]-64)%a.shape[1]]
def rect(sx,sy,w,h):
 m=np.zeros((H*16,W*16),bool);m[sy+16:sy+16+h,sx+64:sx+64+w]=True;return m
def composite(a,b):
 c=a.copy();m=b[...,3]>0;c[m]=b[m];return c
# Recover ground hidden by the old foreground before changing any silhouettes.
# This prevents the old grass backing from appearing as square holes in courts.
for gy,gx in np.ndindex(H*2,W*2):
 sl=np.s_[gy*8:gy*8+8,gx*8:gx*8+8]
 if np.all(oldfg[sl][...,3]==255):
  n={'.':'grass','P':'paving','C':'court','W':'water','R':'court','A':'court'}.get(str(ground[gy//2,gx//2]),'grass');a=art[n];bg[sl]=a[(Y[sl]-16)%len(a),(X[sl]-64)%a.shape[1]]
# Reviewable HGSS tree reconstructions. Explicit masks exclude neighboring road,
# grass and other crowns. Missing lower foliage is interpreted from that tree's
# own visible planes; no source character or terrain pixels become foliage.
ref=Image.open(S/'hgss-reference.png').convert('RGB');tree_reports=[]
def tree_asset(name,box,poly):
 raw=ref.crop(box).convert('RGBA');mask=Image.new('L',raw.size);ImageDraw.Draw(mask).polygon([(x-box[0],y-box[1]) for x,y in poly],fill=255);raw.putalpha(mask)
 # Gen 3 32x48 receiving footprint; preserve tier structure and clean binary alpha.
 im=raw.resize((32,48),Image.Resampling.LANCZOS);a=np.array(im);a[...,3]=np.where(a[...,3]>=128,255,0)
 if name=='tree-hgss':
  ys,xs=np.where(a[...,3]>0);im=Image.fromarray(a[:,xs.min():xs.max()+1]).resize((32,48),Image.Resampling.LANCZOS);a=np.array(im);a[...,3]=np.where(a[...,3]>=128,255,0)
 green=np.array([(56,56,32),(64,72,32),(80,96,32),(96,120,32),(112,144,32),(136,168,40)],np.uint8);trunk=np.array([(48,40,24),(80,64,32),(112,88,48)],np.uint8)
 for y,x in np.argwhere(a[...,3]>0):
  c=a[y,x,:3].astype(int);p=trunk if y>=42 and c[0]>=c[1] else green;a[y,x,:3]=p[np.argmin(np.sum((p.astype(int)-c)**2,1))]
 save(name,a);tree_reports.append(dict(name=name,source_box=box,source_polygon=poly,native_size=[32,48],adaptation='HGSS foliage planes and silhouette reconstructed into native footprint; 6-step leaf / 3-step trunk ramp'))
tree_asset('tree-hgss',(376,328,408,408),[(391,332),(395,337),(400,343),(405,348),(404,354),(401,357),(405,361),(406,371),(403,385),(398,394),(397,401),(390,404),(385,400),(384,394),(379,386),(377,375),(378,365),(382,357),(379,352),(380,347),(385,341)])
tree_asset('maple-hgss',(432,208,480,272),[(454,209),(464,213),(471,219),(473,225),(468,230),(477,236),(478,244),(473,250),(466,255),(463,264),(454,269),(445,265),(442,257),(433,252),(432,242),(439,234),(437,227),(441,219)])
for name,ramp in [('maple-amber',[(80,56,32),(112,72,32),(152,96,32),(192,128,40),(224,160,48),(240,192,80)]),('maple-autumn',[(80,40,24),(112,48,24),(152,56,24),(192,72,32),(224,96,40),(240,128,56)])]:
 a=art['maple-hgss'].copy();v=art['maple-hgss'];leaf=(v[...,3]>0)&(v[...,1]>v[...,0]);cs=sorted(set(map(tuple,v[leaf,:3])),key=lambda c:sum(map(int,c)))
 # The darkest olive shade belongs to foliage too; use the same source ramp.
 leaf=(v[...,3]>0)&~((np.indices(v.shape[:2])[0]>=42)&(v[...,0]>=v[...,1]))
 cs=sorted(set(map(tuple,v[leaf,:3])),key=lambda c:sum(map(int,c)))
 for i,c in enumerate(cs):a[np.all(v[...,:3]==c,2)&leaf,:3]=ramp[min(i,5)]
 save(name,a)
(D/'tree-reconstruction.json').write_text(json.dumps(tree_reports,indent=2)+'\n')
# Complete approved rock masters, including their own caps. Never decompose a
# shared master into loose slivers or paint a new approximation of its face.
rocks={p.stem:np.array(Image.open(p).convert('RGBA')) for p in (D/'shared-rocks').glob('R*.png')};rock_placements=[]
for n,a in rocks.items():save(n,a)
for name in ['boulder','plateau']:
 a=np.array(Image.open(ROOT/'gba/art/azalea-town/source/masters'/f'{name}.png').convert('RGBA'));save('shared-'+name,a)
# Remove the rejected tower rock patch; retain the original court and two courses.
area=rect(248,120,192,152);texture(area,'court')
def rock(n,sx,sy,mirror=False):
 a=rocks[n][:,::-1] if mirror else rocks[n];bg[sy+16:sy+32,sx+64:sx+80]=a;rock_placements.append(dict(name=n,x=sx+64,y=sy+16,mirror=mirror))
for sx in range(272,416,16):
 if sx not in [336,352]:rock('R02' if sx%32 else 'R04',sx,240)
rock('R17',256,240);rock('R10',416,240)
for sy in range(144,240,16):rock('R11' if sy%32 else 'R12',256,sy);rock('R11' if sy%32 else 'R12',416,sy,True)
rock('R05',256,128);rock('R10',416,128)
for sx in range(288,400,16):
 if sx not in [336,352]:rock('R02' if sx%32 else 'R04',sx,216)
rock('R17',272,216);rock('R10',400,216)
for sy in range(136,216,16):rock('R11' if sy%32 else 'R12',272,sy);rock('R11' if sy%32 else 'R12',400,sy,True)
rock('R05',272,120);rock('R10',400,120)
# The old overview mask blocked half a grass/apron column beyond the wall.
# Align that outside boundary to the reused face; retain the fence and stairs.
solid[9:17,19]=False;mat[9:17,19]='.'
# The small western clearing is a raised stone shelf, not a flat brown blob.
for sx,n,mirror in [(160,'R16',True),(176,'R01',False),(192,'R16',False)]:rock(n,sx,240,mirror)
for sx,n,mirror in [(160,'R15',True),(176,'R08',False),(192,'R15',False)]:rock(n,sx,256,mirror)
# Restore every local architectural piece independently, protecting material hue.
# Widen clipped mask edges only where actual source structure is visible.
local=json.loads((S/'local-asset-provenance.json').read_text());meta={v['name']:v for v in local if 'name' in v and 'box' in v}
gp=[]
for hn in ['house-entry','house-green']:
 raw=np.array(ref.crop(meta[hn]['box']));aa=art[hn]
 for yy,xx in np.argwhere(aa[...,3]>0):
  r,g,b=map(int,raw[yy,xx])
  if yy>=43 and r>70 and r*.6<g<r*.9 and b<g*.55:gp.append(raw[yy,xx])
q=Image.fromarray(np.array(gp,np.uint8).reshape(-1,1,3)).quantize(colors=4,method=Image.Quantize.MEDIANCUT);gold=np.unique(np.array(q.getpalette()[:12],np.uint8).reshape(4,3)&248,axis=0)
for name in ['house','house-entry','house-green','house-southeast','burned-tower','bell-entrance','dance-theater','gym','south-gate']:
 a=art[name].copy();raw=np.array(ref.crop(meta[name]['box']));before=a.copy();h,w=a.shape[:2]
 # Repair isolated quantizer noise inside each opaque material plane; preserve
 # outlines, seams and purposeful texture clusters with conservative agreement.
 fixed=0
 for y in range(1,h-1):
  for x in range(1,w-1):
   if not np.all(before[y-1:y+2,x-1:x+2,3]>0):continue
   nb=before[y-1:y+2,x-1:x+2,:3].reshape(9,3);cs,counts=np.unique(nb,axis=0,return_counts=True);j=np.argmax(counts);c=before[y,x,:3]
   if counts[j]>=7 and np.count_nonzero(np.all(nb==c,1))==1 and np.sum(abs(cs[j].astype(int)-c.astype(int)))<=48:a[y,x,:3]=cs[j];fixed+=1
 # Recover omitted lower wall/footing segments at exact visible source coordinates.
 additions={'house':[(18,43,83,65)],'house-entry':[(18,43,83,71)],'house-green':[(10,44,78,71)],'house-southeast':[(10,44,78,71)],'dance-theater':[(19,74,112,97)],'bell-entrance':[(10,64,175,79)],'burned-tower':[(16,86,112,113)]}
 pal=np.unique(before[before[...,3]>0,:3],axis=0)
 for x0,y0,x1,y1 in additions.get(name,[]):
  for y in range(y0,min(h,y1)):
   for x in range(x0,min(w,x1)):
    if a[y,x,3]:continue
    c=raw[y,x].astype(int)
    # Original plaster/timber/step only; no earth or lawn introduced as wall.
    if max(c)-min(c)<28 and max(c)<190 and np.count_nonzero(before[max(0,y-1):min(h,y+2),max(0,x-1):min(w,x+2),3])>=4:
     a[y,x,:3]=pal[np.argmin(np.sum((pal.astype(int)-c)**2,1))];a[y,x,3]=255
 # The original sliding-door houses have golden vertical timber panels. The
 # first material pass had flattened those into the neutral wall ramp.
 panel=0
 if name in ['house-entry','house-green']:
  for y in range(43,h):
   for x in range(w):
    if not a[y,x,3]:continue
    r,g,b=map(int,raw[y,x])
    if r>70 and r*.6<g<r*.9 and b<g*.55:
     a[y,x,:3]=gold[np.argmin(np.sum((gold.astype(int)-raw[y,x].astype(int))**2,1))];panel+=1
 glazing=0
 if name in ['bell-entrance','burned-tower']:
  for y,x in np.argwhere(a[...,3]>0):
   r,g,b=map(int,raw[y,x])
   if name=='bell-entrance' and y>=56 and b>r+7 and b>g+5:
    a[y,x,:3]=[72,64,112] if (r+g+b)/3<105 else [128,120,176];glazing+=1
   elif name=='burned-tower' and y>=80 and g>r+8 and g>b+5:
    a[y,x,:3]=[24,56,40] if (r+g+b)/3<55 else [40,80,48];glazing+=1
 if name=='bell-entrance':
  mask=np.zeros((h,w),bool)
  for y in range(24,64):
   for x in range(8,69):
    r,g,b=map(int,raw[y,x]);mask[y,x]=a[y,x,3]>0 and r>g*1.25 and g>b*1.2
  pix=raw[mask];q=Image.fromarray(pix.reshape(-1,1,3)).quantize(colors=5,method=Image.Quantize.MEDIANCUT);pa=np.array(q.getpalette()[:15]).reshape(5,3);order=np.argsort(pa.sum(1));warm=np.unique(before[before[...,3]>0,:3],axis=0);warm=warm[(warm[:,0]>warm[:,1]*1.25)&(warm[:,1]>warm[:,2]*1.1)];warm=warm[np.argsort(warm.astype(int).sum(1))];ramp=warm[np.linspace(0,len(warm)-1,5).round().astype(int)];indexed=np.argmin(np.sum((pix[:,None].astype(int)-pa.astype(int))**2,2),1);mapping={int(v):ramp[i] for i,v in enumerate(order)};a[mask,:3]=np.array([mapping[int(v)] for v in indexed])
  merges=[]
  while True:
   cs,counts=np.unique(a[a[...,3]>0,:3],axis=0,return_counts=True)
   if len(cs)<=15:break
   pairs=[]
   for i,c in enumerate(cs):
    for j,d in enumerate(cs):
     if i>=j or c[2]>c[0]+8 or d[2]>d[0]+8 or sum(map(int,c))<120 or sum(map(int,d))<120:continue
     pairs.append((int(np.sum((c.astype(int)-d.astype(int))**2)),i,j))
   delta,i,j=min(pairs);assert delta<=1536
   if counts[i]>counts[j]:i,j=j,i
   mm=(a[...,3]>0)&np.all(a[...,:3]==cs[i],2);a[mm,:3]=cs[j];merges.append(dict(source=list(map(int,cs[i])),receiving=list(map(int,cs[j])),pixels=int(mm.sum())))
  changes.append(dict(asset='bell-material-ramp',preserved='Violet glazing and structured annex roof grain',nearby_same_material_shades_consolidated=merges))
 consolidation=None
 if name=='burned-tower':
  cs,counts=np.unique(a[a[...,3]>0,:3],axis=0,return_counts=True)
  if len(cs)>15:
   choices=[]
   for i,c in enumerate(cs):
    for j,d in enumerate(cs):
     if i>=j or sum(map(int,c))<120 or sum(map(int,d))<120:continue
     if c[1]>c[0]+8 or d[1]>d[0]+8:continue
     choices.append((int(np.sum((c.astype(int)-d.astype(int))**2)),i,j))
   delta,i,j=min(choices);assert delta<=1024
   if counts[i]>counts[j]:i,j=j,i
   m=(a[...,3]>0)&np.all(a[...,:3]==cs[i],2);a[m,:3]=cs[j];consolidation=dict(source=list(map(int,cs[i])),receiving=list(map(int,cs[j])),pixels=int(m.sum()),purpose='Reserve the fifteenth native shade for original green glazing; merge only neighboring non-green material shades.')
 save(name,a);changes.append(dict(asset=name,isolated_same_plane_pixels_cleaned=fixed,restored_structure_pixels=int(np.sum((a[...,3]>0)&(before[...,3]==0))),restored_original_timber_panel_pixels=panel,restored_glazing_pixels=glazing,palette_consolidation=consolidation))
# Recreate curb recesses and receiving courts to fit actual door centers.
def court(sx,sy,w,h,door=None):
 m=rect(sx,sy,w,h);texture(m,'court')
 for edge,c in [(rect(sx-2,sy-2,w+4,h+4)&~m,[136,152,112]),(m&~rect(sx+2,sy+2,w-4,h-4),[152,152,112])]:bg[edge,:3]=c
 if door is not None:
  m=rect(door-16,sy+h-8,32,16);texture(m,'paving')
for box in [(616,552,160,112),(776,432,160,112)]:texture(rect(*box),'paving')
for x0,y0,x1,y1,door in [(288,344,408,424,None),(448,344,568,424,None),(288,448,408,536,336),(448,448,568,536,None),(624,440,752,536,688),(792,448,920,536,840),(288,560,408,656,352),(448,560,568,656,528),(632,560,760,656,696),(784,560,912,656,864)]:court(x0,y0,x1-x0,y1-y0,door)
# Recompose the existing foreground placements over preserved native ground.
# This also removes superseded masks rather than overlaying a second cutout.
owner=np.zeros((H*16,W*16),np.uint16)
for i,p in enumerate(assembly['placements'],1):
 a=np.array(Image.open(B/'masters'/(p['name']+'.png')).convert('RGBA'));h,w=a.shape[:2];owner[p['y']:p['y']+h,p['x']:p['x']+w][a[...,3]>0]=i
fg[owner>0]=0;placements=[]
for p in assembly['placements']:
 p=p.copy();n=p['name'];sx,sy=p['x']-64,p['y']-16
 if n=='grove-outcrop':continue
 if n=='pond-boulder':n='shared-boulder';sy=240
 elif n=='tree':n='tree-hgss'
 elif n=='tree-amber':n='maple-amber'
 elif n=='tree-autumn':n='maple-autumn'
 if n=='maple-amber' and 432<=sx<480 and sy>=208:n='maple-hgss'
 if n=='center':sx+=16
 if n=='mart':sy-=8
 if n=='P12' and (sx,sy)==(640,496):n='P13';sx=648
 p.update(name=n,x=sx+64,y=sy+16,source_xy=[sx,sy]);a=art[n];h,w=a.shape[:2];m=a[...,3]>0;fg[p['y']:p['y']+h,p['x']:p['x']+w][m]=a[m];placements.append(p)
 # Wall footprints move with approved shared buildings, not with roof overhangs.
 if n in ['center','mart']:
  old=next(v for v in assembly['placements'] if v['name']==n);ox,oy=old['x'],old['y'];solid[(oy+h-32)//16:(oy+h+15)//16,ox//16:(ox+w+15)//16]=False
  for yy in range(p['y']//16,(p['y']+h+15)//16):
   for xx in range(p['x']//16,(p['x']+w+15)//16):
    q=a[max(0,yy*16-p['y']):min(h,yy*16+16-p['y']),max(0,xx*16-p['x']):min(w,xx*16+16-p['x'])]
    if q.size and (q[...,3]>0).any():mat[yy,xx]='B';above[yy,xx]=yy*16<p['y']+h-24;solid[yy,xx]=yy*16>=p['y']+h-32
# Keep ordinary traversal and root occupancy at the tower; rebuild artwork only.
for p in placements:
 if p['name']=='stairs':
  # Source treads/axis remain the same; preserve the original green stone ramp.
  raw=np.array(ref.crop(meta.get('stairs',{'box':[336,208,360,256]})['box']));a=art['stairs'];stone=np.unique(rocks['R02'][...,:3].reshape(-1,3)&248,axis=0);stone=stone[np.argsort(stone.astype(int).sum(1))];pal=stone[np.linspace(0,len(stone)-1,5).round().astype(int)];m=a[...,3]>0;v=raw[m].astype(int).mean(1);bins=np.clip(((v-40)/36).astype(int),0,4);a=a.copy();a[m,:3]=pal[bins];save('stairs',a);fg[p['y']:p['y']+48,p['x']:p['x']+24][m]=a[m]
# Encode restored timber grain separately from the old neutral wall frame.
# Only opaque blocked wall quadrants qualify, so priorities and visible pixels
# remain unchanged while the house ramp and timber ramp each stay coherent.
split_timber=0
for p in placements:
 if p['name'] not in ['house-entry','house-green']:continue
 a0=art[p['name']];hh,ww=a0.shape[:2]
 for yy in range((p['y']+40)//8*8,(p['y']+hh)//8*8,8):
  for xx in range(p['x']//8*8,(p['x']+ww)//8*8,8):
   sl=np.s_[yy:yy+8,xx:xx+8];a=fg[sl].copy();panel=np.any(np.all(a[...,:3,None]==gold.T[None,None,:,:],2),2)&(a[...,3]>0)
   if not panel.any() or panel.all() or not np.all(a[...,3]==255) or not solid[yy//16,xx//16]:continue
   cs,counts=np.unique(a[~panel,:3],axis=0,return_counts=True);back=a.copy();back[panel,:3]=cs[np.argmax(counts)];bg[sl]=back;fg[sl][~panel]=0;split_timber+=1
# Encode restored Bell glazing on a separate native layer from its timber frame.
# Only opaque, blocked wall quadrants qualify; roof overhang priority and every
# visible RGB pixel stay exact. This avoids spending a bank on mixed wood/glass.
split_windows=0
for p in placements:
 if p['name']!='bell-entrance' or len(np.unique(art['bell-entrance'][art['bell-entrance'][...,3]>0,:3],axis=0))<=15:continue
 for yy in range((p['y']+56)//8*8,(p['y']+88)//8*8,8):
  for xx in range(p['x']//8*8,(p['x']+192)//8*8,8):
   sl=np.s_[yy:yy+8,xx:xx+8];a=fg[sl].copy();glass=(np.all(a[...,:3]==[72,64,112],2)|np.all(a[...,:3]==[128,120,176],2))&(a[...,3]>0)
   if not glass.any() or not np.all(a[...,3]==255) or not solid[yy//16,xx//16]:continue
   if glass.all():continue
   cs,counts=np.unique(a[~glass,:3],axis=0,return_counts=True);back=a.copy();back[glass,:3]=cs[np.argmax(counts)];bg[sl]=back;fg[sl][~glass]=0;split_windows+=1
bg[...,:3]&=248;fg[...,:3]&=248
for n,a in [('background',bg),('foreground',fg)]:Image.fromarray(a).save(S/(n+'.png'))
np.save(S/'solid.npy',solid);np.save(S/'material-grid.npy',mat)
assembly['placements']=placements
for t in assembly['trees']:
 t['name']={'tree':'tree-hgss','tree-amber':'maple-amber','tree-autumn':'maple-autumn'}[t['name']]
 if t['name']=='maple-amber' and 432<=t['x']*16-64<480 and t['y']*16-16>=208:t['name']='maple-hgss'
assembly['rock_placements']=rock_placements
from refinement_ground import update_ground
ground=update_ground(ground,assembly);np.save(S/'ground-material-grid.npy',ground)
for b in assembly['buildings']:
 if b[0]=='center':b[1]+=16;b[3]=[47,41]
 if b[0]=='mart':b[2]-=8;b[3]=[56,34]
(E/'assembly.json').write_text(json.dumps(assembly,indent=2)+'\n')
Image.fromarray(composite(bg,fg)).save(D/'refined-preview.png')
(D/'refinement-report.json').write_text(json.dumps(dict(buildings=changes,rock_placements=rock_placements,tree_reconstruction=tree_reports,placements=placements,blocked_wall_timber_quadrants_relayered=split_timber,baseline_source='dbf53f6f3975eb20179c26badd6ba48169857ad1',rules='Edit current source only; no town-layout generator replay, unrelated map repack or nearest-tile replacement.'),indent=2)+'\n')
from compile_refinement import compile_native
compile_native(G,PT,S,E,bg,fg,solid,beh,above,assembly)
