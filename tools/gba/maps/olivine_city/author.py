"""REJECTED overview-based first pass; retained historical provenance only.
Does not meet the 2026-10-20 owner city-art requirement. Never replay or use as
a new-city template. See rebuild.py for the independent-component reconstruction.
"""
from pathlib import Path
import sys,json,hashlib,struct,subprocess,shutil
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[4];S=R/'gba/art/olivine-city/source';E=S.parent/'evidence';G=Path(sys.argv[1]);W,H=65,54
assert not subprocess.check_output(['git','-C',str(G),'ls-files','data/maps/Olivine*'],text=True).strip(),'Never replay over committed native maps'
E.mkdir(parents=True,exist_ok=True);M=S/'masters';M.mkdir(exist_ok=True)
ref=Image.open(S/'hgss-reference.png').convert('RGB');canvas=Image.new('RGB',(W*16,H*16));canvas.paste(ref);canvas.paste(ref.crop((1032,0,1035,858)).resize((8,858)),(1032,0));canvas.paste(canvas.crop((0,856,1040,858)).resize((1040,8)),(0,856));raw=np.array(canvas).copy();fg=np.zeros((H*16,W*16,4),np.uint8);solid=np.ones((H,W),bool);material=np.full((H,W),'sea/cliff',dtype='<U32');roof=np.zeros((H,W),bool);features=[]
def mask(poly):
 m=Image.new('L',canvas.size);ImageDraw.Draw(m).polygon(poly,fill=255);return np.array(m)>0
# Original passable surface, separate from all appearance/palette decisions.
land=mask([(328,0),(456,0),(456,448),(472,448),(472,192),(656,192),(656,304),(632,304),(632,544),(664,576),(824,576),(824,384),(696,384),(696,544),(632,544),(632,640),(440,640),(440,696),(464,712),(464,816),(432,832),(432,864),(360,864),(360,832),(280,832),(280,736),(352,736),(352,640),(104,640),(104,544),(0,544),(0,480),(104,480),(104,176),(328,176)])
for y,x in np.ndindex(H,W):
 if land[y*16+8,x*16+8]:solid[y,x]=False;material[y,x]='stone street'
# Complete visible cliff rims, forest roots and harbor railings remain barriers.
for a,b,c,d in [(28,0,30,20),(30,0,32,12),(41,12,43,36),(40,19,41,34),(34,19,36,25),(32,22,35,26),(6,10,8,28),(0,28,6,30),(6,39,22,40),(27,39,40,40),(40,36,53,40),(51,24,53,36),(43,23,52,24),(17,46,18,52),(27,49,29,52),(17,51,22,52),(27,51,29,52),(0,29,6,30)]:
 solid[b:d,a:c]=True;material[b:d,a:c]='cliff/retaining rail'
# City paths to Route39 north and Route40 west are closed pending route scope.
solid[0,:]=True;solid[-1,:]=True;solid[:,0]=True;solid[:,-1]=True
buildings=[('Olivine Gym',(184,152,296,244),(192,224,288,244),(15,16)),('West residence',(272,272,344,352),(280,328,344,352),(19,22)),('North residence west',(496,184,568,272),(504,248,568,272),(33,17)),('North residence east',(576,184,648,272),(584,248,648,272),(38,17)),('Olivine Cafe',(144,400,216,480),(144,448,216,480),(11,30)),('Lighthouse',(688,344,808,520),(696,480,800,520),(46,33)),('Port terminal',(320,696,472,808),(328,776,464,800),(24,50))]
for name,box,base,door in buildings:
 x0,y0,x1,y1=box;a,b,c,d=base
 roof[y0//16:(b+15)//16,x0//16:(x1+15)//16]=True
 solid[b//16:(d+15)//16,a//16:(c+15)//16]=True
 # Upper roof projections may overhang the walkable ground; footprint metadata
 # stays independent from rendered art.
 material[y0//16:(y1+15)//16,x0//16:(x1+15)//16]='building'
 features.append(dict(name=name,reference_box=box,facade=base,door_approach=door))
# Shared masters are immutable inputs, with origin hashes retained.
orig=R/'gba/art/goldenrod-city/source/masters'
provenance=[]
for name,path in [('center',orig/'center.png'),('tree',orig/'tree.png'),('grass',orig/'grass.png'),('mart',R/'gba/art/cherrygrove-synthesis/refined/mart.png')]:
 shutil.copyfile(path,M/(name+'.png'));provenance.append(dict(name=name,origin=str(path.relative_to(R)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
center=np.array(Image.open(M/'center.png').convert('RGBA'));tree=np.array(Image.open(M/'tree.png').convert('RGBA'));mart=np.array(Image.open(M/'mart.png').convert('RGBA'));grass=np.array(Image.open(M/'grass.png').convert('RGB'))
for a in [center,tree,mart]:a[...,:3]&=248
# Restore only the old service-building shapes; keep their surrounding paths,
# street rail, flags and lamp posts intact. Masters do not contain pavement.
for name,poly,art,x,y,base,door in [
 ('approved Violet Pokemon Center',[(244,400),(320,400),(328,416),(328,480),(244,480)],center,240,400,(240,448,320,480),(17,30)),
 ('approved shared Pokemart',[(472,408),(536,408),(536,424),(560,424),(560,448),(544,456),(544,480),(472,480)],mart,464,416,(464,448,544,480),(31,30))]:
 m=mask(poly);Y,X=np.indices(m.shape);raw[m]=grass[Y[m]%grass.shape[0],X[m]%grass.shape[1]]
 h,w=art.shape[:2];a=fg[y:y+h,x:x+w];m=art[...,3]>0;a[m]=art[m]
 roof[y//16:(y+h)//16,x//16:(x+w)//16]=True
 a,b,c,d=base;solid[b//16:d//16,a//16:c//16]=True;roof[b//16:d//16,a//16:c//16]=False
 features.append(dict(name=name,reference_box=[x,y,x+w,y+h],native_box=[x,y,x+w,y+h],facade=base,door_approach=door,adaptation='Approved transparent shared master fitted to original service pad.'))
# Old Mart flag projected beyond the new prefab; reconstruct its street side
# from an unobscured same-row paving donor, not an attached lawn rectangle.
raw[416:456,544:568]=raw[416:456,576:600]
# Replace forest interiors with complete shared trees; retain the original cliff
# edge pixels and pockets, rather than stamping tree backgrounds over them.
regions=[(0,0,288,144),(0,128,80,432),(528,0,1040,64),(680,80,824,352),(824,80,1040,224)]
trees=[];roots=np.zeros((H,W),np.uint8)
for x0,y0,x1,y1 in regions:
 yy,xx=np.indices((y1-y0,x1-x0));raw[y0:y1,x0:x1]=grass[yy%grass.shape[0],xx%grass.shape[1]]
 solid[y0//16:y1//16,x0//16:x1//16]=True;material[y0//16:y1//16,x0//16:x1//16]='forest ground'
 for y in range(y0,y1-47,32):
  for x in range(x0,x1-31,32):
   a=fg[y:y+48,x:x+32];m=tree[...,3]>0;a[m]=tree[m];roots[y//16+1:y//16+3,x//16:x//16+2]=1;roof[y//16,x//16:x//16+2]=True;trees.append([x,y])
# Existing isolated source trees are retained where tightly framed by cliff
# corners; their silhouettes are not replaced by clipped shared crowns.
# Exact foreground coverage for architecture, not opaque rectangular roof masks.
roofpixels=np.zeros((H*16,W*16),bool)
for f in features:
 if 'native_box' in f:continue
 x0,y0,x1,y1=f['reference_box'];roofpixels[y0:f['facade'][1],x0:x1]=True
# Dock props and safety barriers. Clear under umbrella edges, solid plinths.
for a,b,c,d in [(8,36,13,38),(15,36,20,38),(30,36,35,38),(25,35,26,37),(7,17,8,20),(15,17,16,21),(21,24,22,28),(29,24,30,28),(10,13,12,16),(24,21,26,23),(47,32,49,34),(20,3,22,5),(28,3,29,6)]:
 solid[b:d,a:c]=True;material[b:d,a:c]='prop/railing'
# Only the lighthouse sign cell, not its door approach, is blocked.
solid[33,46]=False;solid[32:34,47]=True
# Actual short harbor-to-lighthouse ramp, between its retaining walls.
solid[34:36,39:43]=False;material[34:36,39:43]='terrace ramp'
# Central pier: preserve its continuous approach; door is deliberately closed.
solid[40:44,22:27]=False;solid[50,18:27]=False;solid[51:53,23:27]=False
# Reuse an unobscured lawn core inside the Gym's east pad. Preserve the curb
# and structure edges; spend hardware glyphs on geometry rather than lawn noise.
core=raw[208:224,144:160].copy();yy,xx=np.indices((48,32));raw[208:256,304:336]=core[yy%16,xx%16]
yy,xx=np.indices((16,48));raw[336:352,344:392]=core[yy%16,xx%16]
corep=raw[368:384,352:384].copy();yy,xx=np.indices((16,96));raw[368:384,352:448]=corep[yy%16,xx%32]
# Static flags/umbrellas preserve original detail in the native RGB conversion.
# Clean only low-contrast isolated noise within a shading plane; no smoothing
# across silhouettes or mixing architectural edges with their terrain.
a=raw.copy();neighbors=np.stack([np.roll(np.roll(a,dy,0),dx,1) for dy in [-1,0,1] for dx in [-1,0,1]])
for i in range(9):
 c=neighbors[i];same=np.all(neighbors==c[None],3).sum(0)>=7;delta=np.abs(a.astype(int)-c.astype(int)).max(2);m=same&(delta<=24)&(delta>0);raw[m]=c[m]
Image.fromarray(raw).save(S/'reference-ground.png')
np.save(S/'solid.npy',solid);np.save(S/'material.npy',material);np.save(S/'above.npy',roof);np.save(S/'tree-roots.npy',roots)
(S/'trees.json').write_text(json.dumps(trees)+'\n');(S/'features.json').write_text(json.dumps(features,indent=2)+'\n');(S/'shared-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
# Eight coherent architecture/terrain families, followed by exact shared masters.
patches=[[(0,648,100,696)],[(0,480,64,528),(328,104,448,152)],[(320,0,456,96),(24,552,88,624)],[(464,272,552,304),(112,208,176,240)],[(184,152,296,244)],[(272,272,344,352),(496,184,648,272)],[(688,344,808,520),(320,696,472,808)],[(104,544,632,640)]]
pals=[]
for boxes in patches:
 pix=np.concatenate([raw[y0:y1,x0:x1].reshape(-1,3) for x0,y0,x1,y1 in boxes]);p=Image.fromarray(pix.reshape(-1,1,3)).quantize(colors=15,method=Image.Quantize.MEDIANCUT);pals.append(np.array(p.getpalette()[:45],np.uint8).reshape(15,3)&248)
# Reserve distinct window highlights in the Gym family; median frequency alone
# would discard the small cyan entrance against its large ochre roof.
pals[4][-3:]=np.array([[80,144,168],[144,192,200],[216,232,224]],np.uint8)
# Coherent harbor/lighthouse ramp: retain cream masonry highlights alongside
# the blue roof and glass; frequency quantization alone flattened the terrace.
pals[6]=np.array([[24,48,64],[32,72,112],[32,96,144],[48,128,176],[80,152,192],[120,184,208],[176,216,224],[232,232,216],[208,208,192],[176,184,168],[144,152,136],[112,120,112],[80,88,80],[40,40,32],[168,144,104]],np.uint8)
# Shared tree bank8, Center banks9/10, Mart bank11. Leave bank12 spare.
tcs=sorted(set(map(tuple,tree[tree[...,3]>0,:3])));assert len(tcs)<=15;pals.append(np.array(tcs+[(0,0,0)]*(15-len(tcs)),np.uint8))
import z3
sets=[]
for yy in range(0,80,8):
 for xx in range(0,80,8):
  a=center[yy:yy+8,xx:xx+8];sets.append(set(map(tuple,a[a[...,3]>0,:3])))
cs=sorted(set.union(*sets));solver=z3.Solver();vs=[[z3.Bool(f'p{i}_{j}') for j in range(len(cs))] for i in range(2)]
for row in vs:solver.add(z3.PbLe([(v,1) for v in row],15))
for s in sets:solver.add(z3.Or(*[z3.And(*[row[cs.index(c)] for c in s]) for row in vs]))
assert solver.check()==z3.sat;model=solver.model()
for row in vs:
 pp=[c for c,v in zip(cs,row) if z3.is_true(model.eval(v))];pals.append(np.array(pp+[(0,0,0)]*(15-len(pp)),np.uint8))
cs=sorted(set(map(tuple,mart[mart[...,3]>0,:3])));assert len(cs)<=15;pals.append(np.array(cs+[(0,0,0)]*(15-len(cs)),np.uint8))
patch=raw[400:480,144:216].reshape(-1,3);p=Image.fromarray(patch.reshape(-1,1,3)).quantize(colors=15,method=Image.Quantize.MEDIANCUT);pals.append(np.array(p.getpalette()[:45],np.uint8).reshape(15,3)&248)
q=raw&248;tiles=q.reshape(H*2,8,W*2,8,3).transpose(0,2,1,3,4).reshape(-1,64,3)
errors=np.zeros((len(tiles),len(pals)));indexes=[]
for k,pal in enumerate(pals):
 dist=np.sum((tiles.astype(np.int32)[:,:,None,:]-pal.astype(np.int32)[None,None,:,:])**2,3);ii=dist.argmin(2).astype(np.uint8);indexes.append(ii+1);errors[:,k]=np.take_along_axis(dist,ii[...,None],2)[...,0].mean(1)
choice=errors[:,:9].argmin(1).reshape(H*2,W*2)
# Keep architectural interiors on coherent ramps; boundary quadrants can retain
# the mixed-material best bank to avoid hard rectangular conversion edges.
for name,box,base,door in buildings:
 bank=4 if 'Gym' in name else 5 if 'residence' in name else 6 if name in ['Lighthouse','Port terminal'] else 12 if name=='Olivine Cafe' else -1
 if bank>=0:
  x0,y0,x1,y1=box
  for gy in range((y0+8)//8,(y1-8)//8):
   for gx in range((x0+8)//8,(x1-8)//8):
    a=raw[gy*8:gy*8+8,gx*8:gx*8+8].astype(int)
    green=(a[...,1]>a[...,0]+15)&(a[...,1]>a[...,2]+20)
    if bank!=6 or green.mean()<.25:choice[gy,gx]=bank
choice=choice.ravel();native=np.stack([pals[k][indexes[k][i]-1] for i,k in enumerate(choice)]).reshape(H*2,W*2,8,8,3).transpose(0,2,1,3,4).reshape(H*16,W*16,3)
Image.fromarray(native).save(S/'native-ground.png');Image.fromarray(fg).save(S/'shared-foreground.png');comp=native.copy();m=fg[...,3]>0;comp[m]=fg[m,:3];Image.fromarray(comp).save(E/'native-map.png')
palsets=[set(map(tuple,p)) for p in pals];encoded={};above=roof
for gy,gx in np.ndindex(H*2,W*2):
 i=gy*W*2+gx;lo=indexes[choice[i]][i].reshape(8,8);bank=int(choice[i]);a=fg[gy*8:gy*8+8,gx*8:gx*8+8];f=np.zeros((8,8),np.uint8);fb=0
 if (a[...,3]>0).any():
  cs=set(map(tuple,a[a[...,3]>0,:3]));fb=next(k for k,p in enumerate(palsets) if cs<=p)
  for n,c in enumerate(pals[fb],1):f[(a[...,3]>0)&np.all(a[...,:3]==c,2)]=n
 elif above[gy//2,gx//2]:
  f=lo.copy();f[~roofpixels[gy*8:gy*8+8,gx*8:gx*8+8]]=0;fb=bank
 encoded[(gy,gx)]=[(lo,bank),(f,fb)]

def pack(box,write=False,name=None):
 x0,y0,x1,y1=box;glyphs=[np.zeros((8,8),np.uint8)];lookup={glyphs[0].tobytes():0};blocks=[];attrs=[];ml={};grid=np.zeros((y1-y0,x1-x0),'<u2')
 def entry(a,b):
  k=a.tobytes()
  if k not in lookup:
   t=len(glyphs);glyphs.append(a)
   for h in range(2):
    for v in range(2):lookup.setdefault((a[::-1 if v else 1,::-1 if h else 1]).tobytes(),t|h<<10|v<<11)
  return lookup[k]|b<<12
 for y in range(y0,y1):
  for x in range(x0,x1):
   es=[]
   for l in range(2):
    for n in range(4):es.append(entry(*encoded[(y*2+n//2,x*2+n%2)][l]))
   attr=0 if above[y,x] else 0x1000;key=tuple(es)+(attr,)
   if key not in ml:ml[key]=len(blocks);blocks.append(es);attrs.append(attr)
   grid[y-y0,x-x0]=ml[key]|0x3000|(0xc00 if solid[y,x] else 0)
 if not write:return len(glyphs),len(blocks)
 assert len(glyphs)<=1008 and len(blocks)<=1024
 for sec in [False,True]:
  p=G/f'data/tilesets/{"secondary" if sec else "primary"}/{name.lower()}';(p/'palettes').mkdir(exist_ok=True,parents=True);start=512 if sec else 0;count=max(1,len(glyphs)-512) if sec else 512
  im=Image.new('P',(128,((count+15)//16)*8));im.putpalette([c for i in range(256) for c in (i*17%256,)*3])
  for j in range(count):
   if start+j<len(glyphs):im.paste(Image.fromarray(glyphs[start+j],mode='P'),(j%16*8,j//16*8))
  im.save(p/'tiles.png',bits=4)
  for b in range(16):
   pp=np.vstack([np.zeros((1,3),np.uint8),pals[b]]) if b<len(pals) else np.zeros((16,3),np.uint8)
   (p/'palettes'/f'{b:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pp)+'\n')
  bb=blocks[start:start+512] or [[0]*8];aa=attrs[start:start+512] or [0];(p/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*b) for b in bb));(p/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(aa),*aa))
 p=G/'data/layouts'/name;p.mkdir(parents=True,exist_ok=True);grid.tofile(p/'map.bin');(np.ones((2,2),'<u2')*(int(grid[0,0])|0xc00)).tofile(p/'border.bin')
 return len(glyphs),len(blocks)
# Hardware sections are invisible connected parts of one registered city. Split
# only where required by actual native glyph cost; never approximate tile art.
sections=[]
def split(box):
 n,m=pack(box)
 if n<=1008 and m<=1024:sections.append(box);return
 x0,y0,x1,y1=box
 if x1-x0>=y1-y0 and x1-x0>20:a=(x0+x1)//2;split((x0,y0,a,y1));split((a,y0,x1,y1))
 else:a=(y0+y1)//2;split((x0,y0,x1,a));split((x0,a,x1,y1))
split((0,0,W,H));report=[]
for i,b in enumerate(sections):
 name='OlivineCity'+str(i+1).zfill(2);n,m=pack(b,True,name);report.append(dict(name=name,box=b,glyphs=n,metatiles=m))

(E/'sections.json').write_text(json.dumps(report,indent=2)+'\n')
(S/'palettes.json').write_text(json.dumps([p.tolist() for p in pals])+'\n')
(E/'registration.json').write_text(json.dumps(dict(reference='https://archives.bulbagarden.net/media/upload/f/f6/Olivine_City_HGSS.png',reference_size=list(ref.size),native_size=[W,H],scale=1,origin=[0,0],padding=[5,6],source='HGSS overview interpretation, not extracted DS collision',limits=['Exterior only; closed doors, no interiors, ferry or Lighthouse floors.','Route39 and Route40 exits closed pending separately scoped routes.','Static water, flags and boats.','Tightly framed isolated source trees retained beside cliff corners.']),indent=2)+'\n')
print(json.dumps(report,indent=2))
