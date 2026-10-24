"""Local edit of c8f961 Ecruteak: courts, original fixtures and directional walls.
Does not replay the first-authoring town generator or alter unrelated maps.
"""
from pathlib import Path
import sys,json,subprocess,shutil,hashlib
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_erosion,binary_dilation,distance_transform_edt
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'));from tiles import Tileset
G=Path(sys.argv[1]);S=ROOT/'gba/art/ecruteak-city/source';E=S.parent/'evidence';D=S/'court-refinement';B=D/'baseline';M=S/'masters';W,H=72,52
assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()=='c8f961fc5a84cce6f3c71c0db58b19f8e3a9dd29'
assert not subprocess.check_output(['git','-C',str(G),'status','--porcelain','--','data/layouts/JohtoEcruteakCity','data/layouts/JohtoEcruteakTempleDistrict','data/tilesets/primary/ecruteak_city','data/tilesets/primary/ecruteak_temple','data/tilesets/secondary/ecruteak_city','data/tilesets/secondary/ecruteak_temple'],text=True).strip(),'Preserve uncommitted native edits; apply only to the clean reviewed baseline.'
if not B.exists():
 B.mkdir();shutil.copytree(M,B/'masters')
 for n in ['background.png','foreground.png','solid.npy','material-grid.npy','ground-material-grid.npy','behaviors.npy']:shutil.copyfile(S/n,B/n)
 for n in ['assembly.json','native-map.png']:shutil.copyfile(E/n,B/n)
bg=np.array(Image.open(B/'background.png').convert('RGBA'));fg=np.array(Image.open(B/'foreground.png').convert('RGBA'));solid=np.load(B/'solid.npy');mat=np.load(B/'material-grid.npy');ground=np.load(B/'ground-material-grid.npy');beh=np.load(B/'behaviors.npy');r=json.loads((B/'assembly.json').read_text());ref=np.array(Image.open(S/'hgss-reference.png').convert('RGB'));art={p.stem:np.array(Image.open(p).convert('RGBA')) for p in (B/'masters').glob('*.png')};above=np.zeros((H,W),bool)
for n,bank,h,y0 in [('JohtoEcruteakTempleDistrict','ecruteak_temple',27,0),('JohtoEcruteakCity','ecruteak_city',25,27)]:
 t=Tileset(G,bank,bank);grid=np.fromfile(G/'data/layouts'/n/'map.bin','<u2').reshape(h,W)
 for y,x in np.ndindex(h,W):mid=int(grid[y,x]&1023);above[y+y0,x]=(t.attrs[mid>=512][mid%512]&0x3000)==0
Y,X=np.indices(bg.shape[:2]);logs=[]
def rect(x,y,w,h):
 a=np.zeros(bg.shape[:2],bool);a[y+16:y+16+h,x+64:x+64+w]=True;return a
def texture(mask,name):
 a=art[name];bg[mask]=a[(Y[mask]-16)%a.shape[0],(X[mask]-64)%a.shape[1]]
def save(n,a):
 a=a.copy();a[...,:3]&=248;a[a[...,3]==0,:3]=0;art[n]=a;Image.fromarray(a).save(M/(n+'.png'))
# Restore entire receiving rectangles before rebuilding their complete rims.
# Each recess belongs to the same polygon as its court; it has its own corners.
courts=[('northwest',288,344,128,80,None),('northeast',448,344,128,80,None),('west',288,448,128,88,336),('central-empty',448,448,128,88,None),('theater',624,440,128,96,688),('mart',792,448,128,88,840),('gym',288,560,128,104,352),('southwest-house',448,560,128,104,512),('center',632,560,128,104,696),('southeast',784,560,128,104,848)]
for _,x,y,w,h,_ in courts:
 mask=rect(x-8,y-8,w+16,h+16);texture(mask,'paving')
 for yy,xx in np.ndindex(H,W):
  if mask[yy*16:yy*16+16,xx*16:xx*16+16].mean()>.3:ground[yy,xx]='P'
# HGSS original border samples: 1px outside shade, 3px curb shadow, 4px moss
# pavers with alternating joints. Four turns continue around the inset approach.
for name,x,y,w,h,door in courts:
 inside=rect(x,y,w,h)
 depth=24 if y>=560 else 16
 if door is not None:inside &=~rect(door-16,y+h-depth,32,depth+8)
 dist=distance_transform_edt(inside);outside=binary_dilation(inside,iterations=2)&~inside
 bg[outside,:3]=[128,136,120];texture(inside,'court')
 bg[inside&(dist<=3),:3]=[120,120,112]
 band=inside&(dist>3)&(dist<=8);bg[band,:3]=[152,160,128]
 joints=band&(((X-64)%16>=12)|((Y-16)%16>=12));bg[joints,:3]=[136,144,128]
 # Recover actual mixed-square ground labels from the new receiving plane.
 for yy,xx in np.ndindex(H,W):
  if inside[yy*16:yy*16+16,xx*16:xx*16+16].mean()>.3:ground[yy,xx]='C'
 logs.append(dict(court=name,outer_source_box=[x,y,x+w,y+h],recess_center=door,recess_depth=depth if door else 0,border='continuous shaded HGSS moss-paver rim with returning recess corners'))
# Existing two-course wall footprint: use the Route32 directional Emerald sides
# and front in the accepted Cherrygrove stone ramp. Flat tops never receive faces.
texture(rect(248,120,192,152),'court');wallplacements=[]
for name in ['rock-top','emerald-0x73','emerald-0x75','emerald-0x7c','emerald-0x85','emerald-0x86','emerald-0x87']:
 save('route32-'+name,np.array(Image.open(D/(name+'.png')).convert('RGBA')))
# Complete native corner masters join the original side/front quadrants.
# The 0x85/0x86 donors are half-side pieces, not complete convex corners.
for side,donor in [('left','route32-emerald-0x73'),('right','route32-emerald-0x75')]:
 a=art['route32-emerald-0x7c'].copy();xx=slice(0,8) if side=='left' else slice(8,16);a[:8,xx]=art[donor][:8,xx];save('route32-corner-'+side,a)
def putbg(n,x,y):
 a=art[n];h,w=a.shape[:2];m=a[...,3]>0;bg[y+16:y+16+h,x+64:x+64+w][m]=a[m];wallplacements.append(dict(name=n,x=x+64,y=y+16))
# Each complete course has a continuous top and 16px directional faces. Source
# terrace is earth, so imported route lawn is not pasted along its shoulders.
for left,right,top,bottom in [(256,432,128,256),(272,416,128,224)]:
 for y in range(top,bottom-16,16):
  putbg('route32-emerald-0x73',left,y);putbg('route32-emerald-0x75',right-16,y)
 for x in range(left+16,right-16,16):
  if x in [336,352]:continue
  putbg('route32-emerald-0x7c',x,bottom-16)
 putbg('route32-corner-left',left,bottom-16);putbg('route32-corner-right',right-16,bottom-16)
# Match the small western shelf to the same route stone family.
texture(rect(160,240,48,48),'grass')
for x in [160,176,192]:
 a=art['route32-rock-top'][:16,:16].copy();save('route32-shelf-top',a);putbg('route32-shelf-top',x,240)
for x,n in [(160,'route32-corner-left'),(176,'route32-emerald-0x7c'),(192,'route32-corner-right')]:putbg(n,x,256)
# Remove previously composited fixture/building silhouettes, then recompose all
# current placements in their established canopy order. Background wall layers
# beneath the two timber houses are replaced by their actual visible master.
for p in r['placements']:
 if p['name'] not in ['gym','burned-tower','house','house-entry','house-green','house-southeast','dance-theater','bell-entrance','fence','stairs']:continue
 a=art[p['name']];h,w=a.shape[:2];m=a[...,3]>0;fg[p['y']:p['y']+h,p['x']:p['x']+w][m]=0
fg[:]=0
# Material-aware architecture review. Original texture coordinates are retained;
# colored glass and painted trim cannot be swallowed by the large wood planes.
meta={v['name']:v for v in json.loads((S/'local-asset-provenance.json').read_text()) if 'name' in v and 'box' in v}
housepal=np.array([(24,24,24),(48,40,32),(88,72,56),(128,112,96),(184,168,128),(88,24,8),(120,40,16),(152,56,32),(176,80,40),(208,112,64),(72,64,112),(128,120,176),(32,80,64),(48,120,88),(80,160,112)],np.uint8)
for name in ['house','house-entry','house-green','house-southeast']:
 a=art[name].copy();raw=ref[meta[name]['box'][1]:meta[name]['box'][3],meta[name]['box'][0]:meta[name]['box'][2]]
 # Keep restored golden door panels. Recover the source gold ridge separately
 # from terracotta: first-pass quantization had made it a neutral gray strip.
 ramp=np.array([(64,56,24),(104,88,32),(144,128,56),(184,168,80)],np.uint8)
 for y,x in np.argwhere(a[...,3]>0):
  rr,gg,bb=map(int,raw[y,x]);
  if y<14 and rr>gg*.95 and gg>bb*1.8 and gg>55:a[y,x,:3]=ramp[np.argmin(np.sum((ramp.astype(int)-raw[y,x])**2,1))]
 save(name,a)
# Gym: preserve cyan glass, violet bands, warm orange framing and roof grain.
a=art['gym'].copy();raw=ref[544:656,288:416];pal=np.array([(32,24,24),(64,48,40),(96,64,40),(128,88,48),(160,112,64),(184,136,80),(216,168,112),(112,48,16),(184,80,24),(232,120,40),(64,32,88),(104,48,136),(144,80,168),(56,136,176),(120,192,216),(200,208,200)],np.uint8)
for y,x in np.argwhere(a[...,3]>0):
 rr,gg,bb=map(int,raw[y,x]);cand=list(range(7))
 if y>=53 and bb>rr+10 and gg>rr+10:cand=[13,14]
 elif y>=53 and bb>rr+10 and bb>gg+8:cand=[10,11,12]
 elif rr>gg*1.4 and gg>bb*1.5 and rr>180:cand=[7,8,9]
 elif max(rr,gg,bb)-min(rr,gg,bb)<28 and rr>140:cand=[15]
 a[y,x,:3]=pal[cand][np.argmin(np.sum((pal[cand].astype(int)-raw[y,x])**2,1))]
# Protect the close-valued horizontal grain on the central roof spine.
# Whole-building nearest-color reduction had merged these separate bands.
for y in range(8,65):
 for x in range(46,82):
  rr,gg,bb=map(int,raw[y,x])
  if a[y,x,3] and rr<180 and gg<rr*.85 and bb<gg*.85:
   a[y,x,:3]=pal[min(6,int(np.searchsorted([45,62,76,88,104,126],(rr+gg+bb)/3)))]
# Original sign occludes this edge. Reconstruct the covered right wall from the
# unobscured symmetric left wall, then use a complete separate sign foreground.
for y in range(80,112):
 for x in range(80,108):
  if y>=94:a[y,x]=0
  elif a[y,x,3]:a[y,x]=a[y,127-x]
save('gym',a)
# Burned Tower orange timber trim is distinct from charred roof and green glass.
a=art['burned-tower'].copy();raw=ref[88:216,288:432];warm=np.array([(88,40,8),(128,56,8),(168,72,8)],np.uint8)
for y,x in np.argwhere(a[...,3]>0):
 rr,gg,bb=map(int,raw[y,x]);
 if y>=80 and rr>gg*1.4 and gg>bb*1.6 and rr>70:a[y,x,:3]=warm[np.argmin(np.sum((warm.astype(int)-raw[y,x])**2,1))]
save('burned-tower',a)
# Original little square lanterns: complete head, white light, red stem and base.
# Masks exclude their contact earth and neighboring architecture.
def extract(n,box,poly,palette):
 raw=ref[box[1]:box[3],box[0]:box[2]];im=Image.new('L',(box[2]-box[0],box[3]-box[1]));ImageDraw.Draw(im).polygon([(x-box[0],y-box[1]) for x,y in poly],fill=255);m=np.array(im)>0;a=np.zeros((*m.shape,4),np.uint8);p=np.array(palette,np.uint8);v=raw[m].astype(int);a[m,:3]=p[np.argmin(np.sum((v[:,None]-p.astype(int))**2,2),1)];a[m,3]=255;save(n,a)
fixturepal=[(24,24,24),(48,40,32),(88,72,56),(128,112,96),(184,168,128),(216,216,192),(88,24,8),(120,40,16),(176,80,40)]
extract('house-lantern',(292,372,316,412),[(296,376),(307,376),(307,386),(304,386),(304,393),(307,393),(307,403),(296,403),(296,393),(299,393),(299,386),(296,386)],fixturepal)
extract('shrine-lantern',(148,372,164,404),[(152,376),(163,376),(163,389),(160,389),(160,396),(162,396),(162,401),(153,401),(153,396),(156,396),(156,389),(152,389)],fixturepal)
# Native railing posts retain original wood texture; no house/glass palette mapping.
raw=ref[264:288,256:272];a=np.zeros((24,16,4),np.uint8);rr,gg,bb=raw.astype(int).transpose(2,0,1);yy,xx=np.indices(raw.shape[:2]);m=(yy>=4)&(yy<=19)&(rr>gg)&(bb<rr+16);m&=(yy>4)|(rr>=152)
p=np.array([(48,40,32),(88,72,56),(128,112,96),(184,168,128),(216,216,192)],np.uint8);a[m,:3]=p[np.argmin(np.sum((raw[m,None].astype(int)-p)**2,2),1)];a[m,3]=255;save('fence',a)
# Recolor treads to the same Route32 stone ramp; no changes to stair geometry.
a=art['stairs'].copy();stone=np.unique(art['route32-emerald-0x7c'][...,:3].reshape(-1,3),axis=0);stone=stone[np.argsort(stone.astype(int).sum(1))];cs,counts=np.unique(a[a[...,3]>0,:3],axis=0,return_counts=True);cs=cs[np.argsort(cs.astype(int).sum(1))]
for i,c in enumerate(cs):a[(a[...,3]>0)&np.all(a[...,:3]==c,2),:3]=stone[round(i*(len(stone)-1)/max(1,len(cs)-1))]
save('stairs',a)
placements=[]
for p in r['placements']:
 if p['name']=='P13' and p.get('role')=='original gateway marker row':
  p=p.copy();p['name']='shrine-lantern';p['x']-=4;p['y']-=4;p['source_xy']=[p['x']-64,p['y']-16]
 placements.append(p)
for x,y in [(292,372),(452,372),(292,484),(548,604),(884,604)]:
 placements.append(dict(name='house-lantern',x=x+64,y=y+16,source_xy=[x,y],role='HGSS complete decorative lantern, restored'))
 # Only the support/base blocks walking; its top is overhead.
 solid[(y+16+24)//16,(x+64+8)//16]=True;mat[(y+16+24)//16,(x+64+8)//16]='S';above[(y+16)//16:(y+16+24)//16,(x+64)//16:(x+64+24+15)//16]=True
# Recompose all complete assets; preserves all existing tree anchors/order.
for p in placements:
 a=art[p['name']];h,w=a.shape[:2];m=a[...,3]>0;fg[p['y']:p['y']+h,p['x']:p['x']+w][m]=a[m]
# Split only opaque blocked facade quadrants to fit material-specific banks.
# Roof overhangs and all visible RGB remain exact.
for p in placements:
 if p['name'] not in ['house','house-entry','house-green','house-southeast','gym','burned-tower']:continue
 a=art[p['name']];h,w=a.shape[:2]
 for y in range((p['y']+8)//8*8,(p['y']+h)//8*8,8):
  for x in range(p['x']//8*8,(p['x']+w)//8*8,8):
   q=fg[y:y+8,x:x+8].copy()
   if not np.all(q[...,3]==255) or not solid[y//16,x//16]:continue
   cc=q[...,:3].astype(int);special=(cc[...,0]>cc[...,1]*1.5)&(cc[...,1]>cc[...,2]*1.5)
   if p['name'].startswith('house'):special=(cc[...,1]>cc[...,2]*1.6)&(cc[...,0]<cc[...,1]*1.4)&(cc[...,1]>50)
   if not special.any() or special.all():continue
   cs,counts=np.unique(q[~special,:3],axis=0,return_counts=True);back=q.copy();back[special,:3]=cs[counts.argmax()];bg[y:y+8,x:x+8]=back;fg[y:y+8,x:x+8][~special]=0
for yy,xx in np.ndindex(H,W):
 if mat[yy,xx] in ['C','P']:mat[yy,xx]=ground[yy,xx]
r['placements']=placements;r['rock_placements']=[];r['directional_wall_placements']=wallplacements;r['courts']=logs
for yy,xx in np.ndindex(H*2,W*2):
 sl=np.s_[yy*8:yy*8+8,xx*8:xx*8+8]
 if np.all(fg[sl][...,3]==255):bg[sl]=art['grass'][Y[sl]%16,X[sl]%16]
bg[...,:3]&=248;fg[...,:3]&=248
for n,a in [('background',bg),('foreground',fg)]:Image.fromarray(a).save(S/(n+'.png'))
for n,a in [('solid',solid),('material-grid',mat),('ground-material-grid',ground)]:np.save(S/(n+'.npy'),a)
(E/'assembly.json').write_text(json.dumps(r,indent=2)+'\n');(D/'report.json').write_text(json.dumps(dict(baseline_source='c8f961fc5a84cce6f3c71c0db58b19f8e3a9dd29',courts=logs,fixtures=13,central_plot='Original HGSS overview shows the same unbuilt earth plot and city sign; retained.',route32_source='94bb239d7ea0d470fc5e4ecc85f9630867a1fb3b',walls=wallplacements),indent=2)+'\n')
a=bg.copy();m=fg[...,3]>0;a[m]=fg[m];Image.fromarray(a).save(D/'preview.png')
if len(sys.argv)>2:
 from compile_refinement import compile_native
 compile_native(G,Path(sys.argv[2]),S,E,bg,fg,solid,beh,above,r)
