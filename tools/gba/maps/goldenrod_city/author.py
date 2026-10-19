"""First-authoring only: HGSS texture-preserving native Goldenrod exterior.
The committed native maps are authoritative thereafter. Never replay on them.
"""
from pathlib import Path
import sys,json,hashlib,struct,subprocess
import numpy as np
from PIL import Image,ImageDraw
from scipy.cluster.vq import kmeans2
R=Path(__file__).resolve().parents[4];S=R/'gba/art/goldenrod-city/source';E=S.parent/'evidence';G=Path(sys.argv[1]);W,H=84,56
assert not subprocess.check_output(['git','-C',str(G),'ls-files','data/maps/Goldenrod*'],text=True).strip(),'Preserve committed native maps'
S.mkdir(exist_ok=True,parents=True);E.mkdir(exist_ok=True,parents=True)
ref=Image.open(S/'hgss-reference.png').convert('RGB');canvas=Image.new('RGB',(W*16,H*16));canvas.paste(ref);canvas.paste(ref.crop((1328,0,1330,885)).resize((16,885)),(1328,0));canvas.paste(canvas.crop((0,880,1344,885)).resize((1344,16)),(0,880));raw=np.array(canvas);fg=np.zeros((H*16,W*16,4),np.uint8);solid=np.zeros((H,W),bool);material=np.full((H,W),'paving',dtype='<U24');roof=np.zeros((H,W),bool);features=[]
def mask(poly):
 m=Image.new('L',canvas.size);ImageDraw.Draw(m).polygon(poly,fill=255);return np.array(m)>0
# The source ocean/shore outline is retained, including the narrow causeway.
land=mask([(312,0),(1344,0),(1344,896),(824,896),(824,844),(592,844),(592,752),(560,752),(560,600),(112,600),(112,312),(392,312),(392,416),(560,416),(560,320),(624,320),(624,280),(560,280),(560,128),(624,128),(624,56),(312,56)])
# Land polygon includes sea left of the peninsula; explicit cutouts retain the
# source water around the island, harbour and the causeway's lower side.
land[:312,:312]=False;land[56:312,312:560]=False;land[600:,:592]=False;land[512:600,392:560]=False;land[600:752,560:592]=False
water=(~land)&(raw[...,2].astype(int)>raw[...,0].astype(int)+40)&(raw[...,2].astype(int)>raw[...,1].astype(int)+5)
water[128:400,168:320]=False # tower above its island footprint, not ocean
# A seamless32px original-water core replaces nonperiodic overview repetition.
core=raw[0:32,0:32].copy();Y,X=np.indices(water.shape);raw[water]=core[Y[water]%32,X[water]%32]
for y,x in np.ndindex(H,W):
 sl=np.s_[y*16:y*16+16,x*16:x*16+16]
 if (~land[sl]).mean()>.5:solid[y,x]=True;material[y,x]='water/shore'
# Streets traced separately from the structure/collision footprints.
roads=[[(896,144),(976,144),(976,240),(1168,240),(1168,312),(976,312),(976,672),(1072,672),(1072,736),(976,736),(976,784),(896,784),(896,736),(800,736),(800,672),(896,672),(896,496),(400,496),(400,440),(896,440),(896,312),(736,312),(736,256),(896,256)]]
for poly in roads:
 m=mask(poly)
 for y,x in np.ndindex(H,W):
  if m[y*16+8,x*16+8]:material[y,x]='stone street'
# Original structure bounds and the actual street-facing bases/door positions.
# Every roof is represented independently of its solid facade. These are
# overview interpretations; no hidden DS collision or z data is claimed.
buildings=[
 ('Radio Tower',(168,128,320,400),(176,368,304,400),(16,25)),
 ('Station annex',(608,248,736,416),(608,384,736,416),(42,26)),
 ('Magnet Train station',(728,280,864,416),(736,384,864,416),(47,26)),
 ('North gate',(896,0,976,128),(896,96,976,128),(58,8)),
 ('Goldenrod Gym',(992,144,1112,232),(1000,208,1104,232),(66,15)),
 ('Flower Shop',(1112,48,1192,208),(1112,176,1192,208),(71,13)),
 ('Northeast highrise',(1192,48,1272,192),(1192,160,1272,192),(77,12)),
 ('North house west',(1184,128,1240,224),(1184,192,1240,224),(75,14)),
 ('North house east',(1240,128,1304,208),(1240,176,1304,208),(79,13)),
 ('North orange house',(1192,184,1248,248),(1192,224,1248,248),(76,16)),
 ('Northwest highrise',(632,128,712,296),(632,264,712,296),(42,19)),
 ('Underground north',(728,168,800,232),(728,208,800,232),(47,15)),
 ('Name Rater',(792,152,864,232),(792,208,864,232),(52,15)),
 ('Game Corner',(760,472,872,560),(768,528,864,560),(51,35)),
 ('West apartment north',(632,472,696,552),(632,528,696,552),(41,35)),
 ('West apartment east',(696,472,760,552),(696,528,760,552),(45,35)),
 ('West orange house',(632,544,696,632),(632,600,696,632),(41,40)),
 ('Bill family house',(728,576,792,664),(728,632,792,664),(47,42)),
 ('Underground south',(728,648,792,728),(728,696,792,728),(47,46)),
 ('Southwest house',(584,648,648,736),(584,704,648,736),(38,47)),
 ('Southwest tower',(600,680,680,776),(600,744,680,776),(40,49)),
 ('Southwest tower south',(648,728,728,832),(648,800,728,832),(43,52)),
 ('South house west',(728,736,792,816),(728,784,792,816),(47,51)),
 ('South house east',(792,736,856,816),(792,784,856,816),(51,51)),
 ('Department Store',(992,480,1080,656),(1000,624,1072,656),(65,41)),
 ('Department annex',(1080,584,1160,680),(1080,648,1160,680),(69,43)),
 ('Bike Shop',(1080,640,1160,728),(1080,696,1160,728),(70,46)),
 ('East apartments',(1112,464,1184,544),(1112,512,1184,544),(72,35)),
 ('East orange house',(1144,520,1216,584),(1144,552,1216,584),(74,37)),
 ('East railway highrise',(1176,376,1256,496),(1176,464,1256,496),(76,32)),
 ('East tower upper',(1224,496,1304,600),(1224,568,1304,600),(79,38)),
 ('East house',(1240,584,1304,664),(1240,632,1304,664),(79,42)),
 ('East tower middle',(1224,632,1304,712),(1224,680,1304,712),(79,45)),
 ('East tower lower',(1224,696,1304,784),(1224,752,1304,784),(79,49)),
 ('Southeast house',(1224,752,1304,832),(1224,800,1304,832),(79,53)),
 ('Southeast tower',(1144,728,1224,832),(1144,800,1224,832),(74,53)),
 ('Southeast apartments upper',(1016,704,1080,776),(1016,744,1080,776),(65,49)),
 ('Southeast apartments lower',(1016,744,1080,816),(1016,784,1080,816),(65,51)),
]
for name,box,base,door in buildings:
 x0,y0,x1,y1=box;a,b,c,d=base
 for y in range(y0//16,min(H,(y1+15)//16)):
  for x in range(x0//16,min(W,(x1+15)//16)):
   material[y,x]='building';roof[y,x]=True
 for y in range((b+7)//16,min(H,(d+15)//16)):
  for x in range((a+7)//16,min(W,(c+7)//16)):solid[y,x]=True;roof[y,x]=False
 features.append(dict(name=name,reference_box=box,facade=base,door_approach=door))
# Train viaduct: original pillars flank the street; the avenue passes beneath.
material[20:24,54:84]='rail viaduct';roof[20:24,54:84]=True
solid[24:27,54:56]=True;solid[24:27,61:74]=True
# Sea walls, railings, fountain plinths, posts and the source eastern cliff.
barriers=[(7,20,8,37),(7,36,25,38),(24,31,25,37),(25,31,39,33),(35,20,36,27),(35,36,36,46),(36,51,51,53),(54,26,56,28),(61,26,74,28),(55,10,56,16),(61,10,62,16),(55,30,56,42),(61,30,62,42),(45,51,55,52),(61,51,71,52),(82,0,84,56)]
for x0,y0,x1,y1 in barriers:solid[y0:y1,x0:x1]=True;material[y0:y1,x0:x1]='wall/railing'
for x,y in [(12,33),(19,33)]:solid[y:y+2,x-1:x+2]=True;material[y:y+2,x-1:x+2]='fountain'
# Local tiny props: source signs, posts and roof corners stay on their original
# ground. Explicit cell entries supplement the independently recorded buildings.
for x,y in [(13,26),(21,26),(26,30),(39,26),(50,26),(45,15),(54,14),(61,14),(73,13),(77,17),(53,34),(61,31),(55,47),(69,49),(80,36),(76,51)]:solid[y,x]=True;material[y,x]='prop'
# Shared approved service building. Restore the complete source pad, then reuse
# the canonical80x80Center with its exact15-color quadrant-compatible RGB5 art.
M=S/'masters';M.mkdir(exist_ok=True)
# First-authoring inputs are the hash-locked canonical copies retained here.
# Their original Azalea/shared-source provenance is immutable in the manifest.
provenance=json.loads((S/'shared-provenance.json').read_text())
for item in provenance:
 assert hashlib.sha256((M/(item['name']+'.png')).read_bytes()).hexdigest()==item['sha256']
center=np.array(Image.open(M/'center.png').convert('RGBA'));center[...,:3]&=248
pave=raw[608:624,600:616].copy();Y0,X0=np.indices((96,96));raw[568:664,784:880]=pave[Y0%16,X0%16]
solid[35:42,49:55]=False;material[35:42,49:55]='paving';roof[35:42,49:55]=False
fg[576:656,800:880]=center;solid[39:41,50:55]=True;material[36:41,50:55]='shared Center';roof[36:39,50:55]=True
features.append(dict(name='approved Violet Pokemon Center',reference_box=[789,574,873,656],native_box=[800,576,880,656],facade=[800,624,880,656],door_approach=[52,41],adaptation='Approved shared prefab; source pad restored, source local Center replaced.'))
# Whole shared trees replace the clipped overview foliage. Distinct native roots,
# original forest zones retained; never repeat source half-crowns at map edges.
tree=np.array(Image.open(M/'tree.png').convert('RGBA'));tree[...,:3]&=248;grass=np.array(Image.open(M/'grass.png').convert('RGB'));regions=[(320,0,896,48),(640,48,832,128),(720,112,816,160),(1040,0,1248,48),(1024,48,1112,128),(1296,832,1344,896),(816,848,880,896)]
clean=mask([(640,48),(832,48),(832,152),(792,152),(792,168),(728,168),(728,176),(712,176),(712,128),(640,128)])
yy,xx=np.indices(clean.shape);raw[clean]=grass[yy[clean]%32,xx[clean]%32]
roots=np.zeros((H,W),np.uint8);trees=[]
for x0,y0,x1,y1 in regions:
 yy,xx=np.indices((y1-y0,x1-x0));raw[y0:y1,x0:x1]=grass[yy%32,xx%32]
 for y in range(y0,max(y0+1,y1-47),32):
  for x in range(x0,x1-31,32):
   if y+48>H*16:continue
   a=fg[y:y+48,x:x+32];m=tree[...,3]>0;a[m]=tree[m];cx,cy=x//16,y//16
   assert not roots[cy+1:cy+3,cx:cx+2].any();roots[cy+1:cy+3,cx:cx+2]=1;solid[cy+1:cy+3,cx:cx+2]=True;roof[cy,cx:cx+2]=True;material[cy+1:cy+3,cx:cx+2]='forest roots';trees.append([x,y])
# Remove the full original trunk/shadow remnants outside the replacement
# crowns, stopping at the measured highrise/roof outlines. These donor patches
# contain only unobscured canonical lawn, never character or roof pixels.
for x0,y0,x1,y1 in [(632,128,712,137),(712,152,816,176),(816,152,824,168),(824,152,832,160)]:
 yy,xx=np.indices((y1-y0,x1-x0));raw[y0:y1,x0:x1]=grass[yy%32,xx%32]
# The local purple/gold roof spire touches the old canopy repair. Restore
# its complete original silhouette, including the left tip/shaft and shoulders.
spire=mask([(830,153),(832,154),(836,159),(836,164),(842,168),(842,176),(820,176),(820,168),(824,164),(824,159)])
raw[spire]=np.array(canvas)[spire]
solid[0,:]=True;solid[-1,:]=True;solid[:,0]=True;solid[:,-1]=True
# Source edge route mouths remain closed for separately scoped route interiors.
# North/south road approaches remain identifiable rather than fictional routes.
np.save(S/'solid.npy',solid);np.save(S/'material.npy',material);np.save(S/'above.npy',roof);np.save(S/'tree-roots.npy',roots)
Image.fromarray(raw).save(S/'reference-ground.png');Image.fromarray(fg).save(S/'shared-foreground.png')
(S/'features.json').write_text(json.dumps(features,indent=2)+'\n');(S/'shared-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');(S/'trees.json').write_text(json.dumps(trees)+'\n')
# Native palette fitting is global, so district borders cannot change colors.
# Cluster8px textures by color and contrast, retaining independent architecture
# ramps. No nearest-metatile substitution, geometric rescaling or tile loss.
q=(raw.astype(np.uint16)//8).astype(np.uint8)*8;tiles=q.reshape(H*2,8,W*2,8,3).transpose(0,2,1,3,4).reshape(-1,64,3)
means=tiles.mean(1);std=tiles.std(1);feat=np.concatenate([means,std*.65],1).astype(float);cent,labels=kmeans2(feat,10,minit='++',iter=30,seed=1792);pals=[]
for k in range(10):
 pixels=tiles[labels==k].reshape(-1,3);sample=pixels[::max(1,len(pixels)//150000)]
 p=Image.fromarray(sample.reshape(-1,1,3)).quantize(colors=15,method=Image.Quantize.MEDIANCUT);cs=np.array(p.getpalette()[:45],np.uint8).reshape(15,3)&248;pals.append(cs)
# Preserve the distinctive violet/gold Name Rater roof as its own compatible
# ramp; the automatic clustering otherwise blended it into nearby ochre paving.
patch=raw[152:232,792:864].reshape(-1,3)
p=Image.fromarray(patch.reshape(-1,1,3)).quantize(colors=15,method=Image.Quantize.MEDIANCUT)
pals[9]=np.array(p.getpalette()[:45],np.uint8).reshape(15,3)&248
# Preserve the Department Store's orange paint/red rim and the Flower Shop's
# red awning. A redundant tan bank yielded ochre paint in the first fitting.
patch=np.concatenate([raw[528:592,992:1080].reshape(-1,3),raw[144:208,1112:1192].reshape(-1,3)])
p=Image.fromarray(patch.reshape(-1,1,3)).quantize(colors=15,method=Image.Quantize.MEDIANCUT)
pals[8]=np.array(p.getpalette()[:45],np.uint8).reshape(15,3)&248
# Keep repeated architecture on coherent material ramps. Independent8px
# best-color choices produced blue/tan checker seams on vents and windows.
# Tower stone, teal edging, golden roof grain and violet glazing share one
# native15-color family; residential roofs/wood/windows share another.
patch=np.concatenate([raw[136:296,632:712].reshape(-1,3),raw[728:832,648:728].reshape(-1,3),raw[48:144,1112:1192].reshape(-1,3)])
p=Image.fromarray(patch.reshape(-1,1,3)).quantize(colors=15,method=Image.Quantize.MEDIANCUT)
pals[6]=np.array(p.getpalette()[:45],np.uint8).reshape(15,3)&248
patch=raw[480:552,696:760].reshape(-1,3)
p=Image.fromarray(patch.reshape(-1,1,3)).quantize(colors=15,method=Image.Quantize.MEDIANCUT)
pals[5]=np.array(p.getpalette()[:45],np.uint8).reshape(15,3)&248
forced=np.full((H*2,W*2),-1,np.int16)
for name,box,base,door in buildings:
 bank=6 if ('highrise' in name or 'tower' in name.lower() and name!='Radio Tower' or name=='Department annex') else 5 if ('house' in name.lower() and name!='Name Rater' or 'apartment' in name.lower()) else -1
 x0,y0,x1,y1=box
 forced[y0//8:(y1+7)//8,x0//8:(x1+7)//8]=-1 # later foreground architecture supersedes its backing
 if bank>=0:
  forced[(y0+8)//8:(y1-8)//8,(x0+8)//8:(x1-8)//8]=bank
# Tile-wise palette choice protects every original texture and silhouette.
errors=np.zeros((len(tiles),10));indexes=[]
for k,pal in enumerate(pals):
 dist=np.sum((tiles.astype(np.int16)[:,:,None,:].astype(np.int32)-pal.astype(np.int32)[None,None,:,:])**2,3);ii=dist.argmin(2).astype(np.uint8);indexes.append(ii+1);errors[:,k]=np.take_along_axis(dist,ii[...,None],2)[...,0].mean(1)
choice=errors.argmin(1);force=forced.ravel();choice[force>=0]=force[force>=0];native=np.stack([pals[k][indexes[k][i]-1] for i,k in enumerate(choice)]).reshape(H*2,W*2,8,8,3).transpose(0,2,1,3,4).reshape(H*16,W*16,3)
Image.fromarray(native).save(S/'native-ground.png');comp=native.copy();m=fg[...,3]>0;comp[m]=fg[m,:3];Image.fromarray(comp).save(E/'native-map.png')
# Exact canonical foreground palette covers, independent of photographic banks.
tcs=sorted(set(map(tuple,tree[tree[...,3]>0,:3])));assert len(tcs)<=15;pals.append(np.array(tcs+[(0,0,0)]*(15-len(tcs)),np.uint8))
import z3
sets=[]
for yy in range(0,80,8):
 for xx in range(0,80,8):
  a=center[yy:yy+8,xx:xx+8];sets.append(frozenset(map(tuple,a[a[...,3]>0,:3])))
cs=sorted(set.union(*(set(s) for s in sets)));solver=z3.Solver();vs=[[z3.Bool(f'p{i}_{j}') for j in range(len(cs))] for i in range(2)]
for row in vs:solver.add(z3.PbLe([(v,1) for v in row],15))
for s in sets:solver.add(z3.Or(*[z3.And(*[row[cs.index(c)] for c in s]) for row in vs]))
assert solver.check()==z3.sat;model=solver.model()
for row in vs:
 pp=[c for c,v in zip(cs,row) if z3.is_true(model.eval(v))];pals.append(np.array(pp+[(0,0,0)]*(15-len(pp)),np.uint8))
palsets=[set(map(tuple,p)) for p in pals];encoded={};above=roof
roofpixels=np.zeros((H*16,W*16),bool)
for name,box,base,door in buildings:
 x0,y0,x1,y1=box;roofpixels[y0:base[1],x0:x1]=True
roofpixels[320:384,864:1344]=True
for gy,gx in np.ndindex(H*2,W*2):
 i=gy*W*2+gx;lo=indexes[choice[i]][i].reshape(8,8);bank=int(choice[i]);a=fg[gy*8:gy*8+8,gx*8:gx*8+8];f=np.zeros((8,8),np.uint8);fb=0
 if (a[...,3]>0).any():
  cs=set(map(tuple,a[a[...,3]>0,:3]));fb=next(k for k,p in enumerate(palsets) if cs<=p)
  for n,c in enumerate(pals[fb],1):f[(a[...,3]>0)&np.all(a[...,:3]==c,2)]=n
 elif above[gy//2,gx//2]:
  # Source roof texture is the upper hardware layer, keeping player occlusion.
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
 name='GoldenrodCity'+str(i+1).zfill(2);n,m=pack(b,True,name);report.append(dict(name=name,box=b,glyphs=n,metatiles=m))
(E/'sections.json').write_text(json.dumps(report,indent=2)+'\n');(S/'palettes.json').write_text(json.dumps([p.tolist() for p in pals])+'\n');(E/'authoring.json').write_text(json.dumps(dict(reference='https://archives.bulbagarden.net/media/upload/6/65/Goldenrod_City_HGSS.png',reference_sha256=hashlib.sha256((S/'hgss-reference.png').read_bytes()).hexdigest(),reference_size=ref.size,registration=[0,0],native_size=[W,H],palettes=len(pals),sections=len(sections),trees=trees,source='HGSS overview textures fitted to global native8px palettes. Not decoded DS terrain/collision.',limits=['Exterior only; building interiors, Gym mechanics, minigames, train and adjacent routes not implemented.','Water and fountains static pending animation.','Overview projection and occluded ground interpreted, not extracted DS elevations.']),indent=2)+'\n');print(json.dumps(report,indent=2))

# Global atlas is only a narrow runtime rendering adapter. Porymap layouts and
# each native tileset remain directly editable and independently renderable.
# Regenerate this adapter FROM native files after editing, never the reverse.
