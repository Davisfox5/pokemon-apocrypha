"""Guarded native city interaction audit/edit, from the accepted dc3c5bf1 source.
Native foreground art, ground and physical footprints are independent. Never
replays earlier city authors. Changes remain local to existing Olivine sections.
"""
from pathlib import Path
import sys,json,subprocess,struct,shutil,csv,hashlib
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
R=Path(__file__).resolve().parents[4];G=Path(sys.argv[1]);S=R/'gba/art/olivine-city/source';E=S.parent/'evidence';A=S/'interaction-audit';O=E/'interaction-audit';A.mkdir(exist_ok=True);O.mkdir(exist_ok=True);(A/'assets').mkdir(exist_ok=True)
BASE='dc3c5bf1fe54365b65e2839b01d50fcd7f6a4e41'
assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()==BASE
assert not subprocess.check_output(['git','-C',str(G),'status','--porcelain'],text=True)
# The hub layers must also be restored from the accepted baseline, never current art.
SOURCE_BASELINE={'native-ground.png': '87316a968163f4bef76d628644b8248836db3b48a7d40927b5fa2fbcdc217033', 'shared-foreground.png': '6579e5821014b47d3914cbcf78ee8f8fff0b2f78ba117fb84b8c28604acaa60f', 'solid.npy': '126d42275be47bf5aaa24d1971367048b3c4a26bede40065ff10ce62722a000b', 'above.npy': '953ad43bad5c9ad5cd744818e5c61f54bbcc8e9f4f432b34723ba4f3a9bced0a', 'flag-foreground-mask.png': '9a564e78a34a6231fd0898dee395525c17ebafa5c5544247b5f634aa74f98c8e', 'material.npy': '089948f9062fffada30d36dfe8ffdf627f0b6111d92572e89afc317bd23a1109', 'palettes.json': '39f78b30ba012163e3920b8712fa0daf4931ba660af11415a543303d497b1dfd'}
for name,digest in SOURCE_BASELINE.items():
 assert hashlib.sha256((S/name).read_bytes()).hexdigest()==digest,(name,"Restore hub c82106e baseline in an isolated checkout")
sys.path.insert(0,str(R/'tools/gba/maps'));from tiles import Tileset
bg=np.array(Image.open(S/'native-ground.png').convert('RGB'));fg=np.array(Image.open(S/'shared-foreground.png').convert('RGBA'));source=bg.copy();m=fg[...,3]>0;source[m]=fg[m,:3];oldbg=bg.copy();oldfg=fg.copy();oldsolid=np.load(S/'solid.npy');solid=oldsolid.copy();oldabove=np.load(S/'above.npy');above=oldabove.copy();materials=np.load(S/'material.npy');pals=[np.array(v,np.uint8) for v in json.loads((S/'palettes.json').read_text())];H,W=solid.shape;Y,X=np.indices(bg.shape[:2]);categories={};objects=[];reasons={};owners=np.full((H,W),'terrain',dtype='<U48');changed_ground=np.zeros(bg.shape[:2],bool)
def area(b):
 x,y,x1,y1=b;a=np.zeros(bg.shape[:2],bool);a[y:y1,x:x1]=True;return a
def polygon(points):
 im=Image.new('L',(1040,864));ImageDraw.Draw(im).polygon(points,fill=255);return np.array(im)>0
def cells(b,value,reason):
 x,y,x1,y1=b
 for yy in range(y,y1):
  for xx in range(x,x1):
   solid[yy,xx]=value;owners[yy,xx]=reason
   if bool(oldsolid[yy,xx])!=value:reasons[xx,yy]=reason
 return b
def fit(rgb,bank):
 d=((rgb.astype(np.int32)[:,:,None]-pals[bank].astype(np.int32)[None,None])**2).sum(3);return pals[bank][d.argmin(2)]
def lift(name,mask,bank=None):
 mask=mask.copy();mask&=fg[...,3]==0
 colors=source if bank is None else fit(source,bank)
 fg[mask,:3]=colors[mask];fg[mask,3]=255;above[mask.reshape(H,16,W,16).any((1,3))]=True
 categories[name]=mask

def reset_ground(mask,kind):
 donor={'paving':oldbg[496:504,352:360],'lawn':oldbg[208:216,144:152],'sand':oldbg[0:8,400:408],'dock':oldbg[648:656,360:368]}[kind];yy,xx=np.nonzero(mask);bg[yy,xx]=donor[yy%8,xx%8];changed_ground[mask]=True
# Physical footprints authored from visible bases/solid ground, not from canopies.
# Move the western fence barrier off its adjacent clear walkway onto its posts.
cells((7,11,8,30),False,'western street outside fence')
cells((8,11,9,30),True,'western vertical fence')
cells((8,12,22,13),True,'Gym rear fence')
cells((21,5,22,11),True,'north approach left fence')
cells((28,5,29,11),True,'north approach right fence')
# Complete service-yard fence runs, including the previously passable side runs.
for box in [(8,27,21,28),(22,26,23,30),(34,27,36,28),(35,28,36,30)]:cells(box,True,'service yard fence')
for box,reason in [((6,11,7,28),'western cliff face'),((9,20,12,21),'west yard fence'),((16,20,17,21),'west yard fence'),((22,20,28,21),'west yard fence'),((35,21,36,25),'lower terrace west cliff'),((42,24,43,33),'lighthouse west cliff'),((51,24,52,36),'lighthouse east cliff'),((32,25,35,26),'grove south cliff'),((6,39,22,40),'quay safety rail'),((27,39,40,40),'quay safety rail'),((20,44,22,46),'water under terminal roof'),((17,46,18,52),'terminal west safety rail'),((18,51,22,52),'terminal south safety rail'),((27,50,28,53),'terminal east safety rail'),((22,53,28,54),'closed south exit')]:cells(box,True,reason)
# New solid building floors; upper projected roofs remain foreground overhangs.
buildings=[('Gym',(12,12,18,16)),('West residence',(17,18,22,22)),('North west residence',(31,13,36,17)),('North east residence',(36,13,41,17)),('Cafe',(9,27,14,30)),('Center',(15,27,20,30)),('Mart',(29,27,34,30)),('Lighthouse',(43,26,50,33)),('Terminal',(20,47,29,50))]
for name,b in buildings:cells(b,True,name+' solid footprint');objects.append(dict(name=name,kind='building',physical_box=list(b),upper_roof='existing transparent native foreground'))
# Lamp geometry: free the suspended upper projection; block actual bases only.
for b in [(15,17,16,20),(21,24,22,27),(29,24,30,27),(28,3,29,4)]:cells(b,False,'ground behind elevated lamp')
posts=[('west-left',115,272,320,[(7,20)]),('west-right',240,272,320,[(14,20),(15,20)]),('central-left',338,384,432,[(20,27),(21,27)]),('central-right',464,384,432,[(28,27),(29,27)]),('north-left',336,16,64,[(20,4),(21,4)]),('north-right',464,16,64,[(28,4),(29,4)])]
for name,cx,top,base,roots in posts:
 for x,y in roots:cells((x,y,x+1,y+1),True,'lamp base '+name)
 # Eight-sided globe and thin shaft. The bottom/base stay behind front walkers.
 globe=polygon([(cx,top),(cx+7,top+7),(cx+5,top+12),(cx,top+16),(cx-6,top+11),(cx-7,top+6)])
 c=source.astype(np.int16);warm=(c[...,0]>=c[...,1]-8)&(c[...,0]>c[...,2]+16);dark=c.max(2)<120
 globe&=warm|dark
 shaft=area((cx-2,top+12,cx+3,base));lift('lamp-'+name,globe|shaft,6)
 objects.append(dict(name=name,kind='lamp',base_cells=roots,foreground_until_y=base))
# Tree roots/wooded ground around the stair terrace are not walk-through lawn.
cells((30,21,32,26),True,'terrace tree grove trunks and dense floor')
cells((32,21,34,22),True,'terrace right tree trunk')
treezones=[(488,296,528,336),(520,296,552,336),(488,328,528,368),(488,360,528,400),(496,136,536,176),(632,160,672,208)]
c=source.astype(np.int16);leaf=(c[...,1]>=c[...,0]-8)&(c[...,1]<=168)&(c[...,2]<=112)&(c[...,0]<=152)
for i,b in enumerate(treezones):lift('tree-crown-'+str(i+1),area(b)&leaf)
# Signs: only their posts/plinths are physical; upper boards can cover walkers.
for b in [(10,13,12,15),(24,21,26,22),(25,35,26,36)]:cells(b,False,'ground behind sign board')
signs=[('Gym sign',(168,220,184,236),(10,15,12,16)),('Residence sign',(392,338,408,352),(24,22,26,23)),('Promenade information board',(408,568,426,576),(25,36,27,37)),('Lighthouse sign',(768,520,784,528),(48,33,49,34))]
for name,b,foot in signs:
 cells(foot,True,name+' base');lift(name,area(b));objects.append(dict(name=name,kind='sign',foreground_box=list(b),physical_box=list(foot)))
# Existing lighthouse sign is already a transparent asset, but its upper cell
# was on the covered layer: explicitly promote just the upper board cell.
above[32,48]=True
# Horizontal fence caps above their blocked bases. Connected white cap groups
# locate the actual narrow pickets; never promote an opaque terrain strip.
for name,b,root in [('Gym fence west',(136,176,192,192),192),('Gym fence east',(288,176,352,192),192),('west fence west',(128,304,192,320),320),('west fence east',(240,304,448,320),320),('service fence',(136,411,336,432),432),('Mart fence',(472,411,568,432),432)]:
 x,y,x1,y1=b;cut=source[y:y1,x:x1];bright=(cut[...,0]>170)&(cut[...,1]>180)&(cut[...,2]>160);labs,n=label(bright);mask=np.zeros(bg.shape[:2],bool)
 for k in range(1,n+1):
  yy,xx=np.nonzero(labs==k)
  if len(xx)<3 or xx.max()-xx.min()>8:continue
  a=x+int(xx.min());d=x+int(xx.max())+1;top=y+int(yy.min());mask[top:min(top+8,root),a:d]=True
 lift(name,mask)
# Tables are solid; the unobscured canopy above them is not.
tables=[('west parasol',0,(8,36,13,38)),('middle parasol',112,(15,36,20,38)),('east parasol',352,(30,36,35,38))]
canopy=np.zeros((32,64),bool);first=oldbg[544:576,136:200]
for row in range(32):
 dark=np.max(first[row],1)<105;xx=np.where(dark)[0]
 if len(xx)>=2:canopy[row,xx.min():xx.max()+1]=True
# Keep only the canopy's closed silhouette, excluding the staff below it.
# The final two pixels of the upper staff remain in front until the table base.
asset=np.zeros((32,64,4),np.uint8);asset[canopy,:3]=first[canopy];asset[canopy,3]=255;Image.fromarray(asset).save(A/'assets/parasol-canopy.png')
for name,dx,foot in tables:
 cells(foot,True,name+' table and legs');x=136+dx;y=544;mask=np.zeros(bg.shape[:2],bool);mask[y:y+32,x:x+64]=canopy
 # Reuse one fully isolated canopy, preserving its native color vocabulary.
 fg[y:y+32,x:x+64][canopy]=asset[canopy];above[mask.reshape(H,16,W,16).any((1,3))]=True;categories[name]=mask
 objects.append(dict(name=name,kind='parasol',canopy_origin=[x,y],physical_box=list(foot),foreground_mask='assets/parasol-canopy.png'))
# Rectify the projected harbor ramp to its existing two-row native crossing.
# Keep local original wood grain and rebuild old projected corners first.
rampold=area((632,528,688,592));cliff=oldbg[496:528,640:672];yy,xx=np.nonzero(rampold);bg[yy,xx]=cliff[(yy-496)%32,(xx-640)%32];changed_ground[rampold]=True
reset_ground(rampold&(X>=672)&(Y<576),'lawn')
# Retain the city's unobscured plank grain, recolored to the original warm
# ramp timber family. Regular tread seams align with native movement cells.
woodgrain=oldbg[648:664,360:376].mean(2);v=(woodgrain-woodgrain.mean())/max(float(woodgrain.std()),1);woodcolors=pals[2][[9,6,5]];wood=woodcolors[np.clip(np.floor(v*.45+1.3),0,2).astype(int)];wood[:,0]=pals[2][11];wood[:,1]=pals[2][5];wood[:,8]=pals[2][11];wood[:,9]=pals[2][5];yy,xx=np.indices((32,64));bg[544:576,624:688]=wood[yy%16,xx%16];changed_ground[536:584,624:688]=True
# A simple warm timber guard is solid at its base, clear between its posts.
railbank=2;railcolors=pals[railbank];darkidx=np.argmin(railcolors.mean(1));goldidx=np.argmin(((railcolors.astype(int)-np.array([176,136,80]))**2).sum(1));lightidx=np.argmin(((railcolors.astype(int)-np.array([208,168,104]))**2).sum(1))
for y in [536,576]:
 bg[y:y+3,624:688]=railcolors[goldidx];bg[y,624:688]=railcolors[lightidx]
 for x in range(624,688,16):bg[y:y+8,x:x+3]=railcolors[goldidx]
cells((39,34,43,36),False,'harbor ramp deck');cells((39,33,43,34),True,'harbor ramp north guard');cells((39,36,43,37),True,'harbor ramp south guard')
# South guard upper rail projects four pixels into the deck and covers feet.
railmask=area((624,572,688,576));bg[572:576,624:688]=railcolors[goldidx];bg[572,624:688]=railcolors[lightidx];bg[575,624:688]=railcolors[darkidx];fg[railmask,:3]=bg[railmask];fg[railmask,3]=255;above[railmask.reshape(H,16,W,16).any((1,3))]=True;categories['ramp south guard']=railmask
objects.append(dict(name='harbor ramp',kind='rectified ramp',deck_box=[39,34,43,36],guard_rows=[33,36],method='Native wood grain retained; projected corners restored; axis aligned to existing crossing'))
# The stair's side guard caps can overlap a walker on its two-column tread.
c=source.astype(np.int16);timber=(c[...,0]>c[...,2]+16)&(c[...,0]>=c[...,1])
lift('upper stair guard caps',(area((576,304,580,312))|area((604,304,608,312)))&timber)
# Prepare the new maritime bunting from a genuinely transparent original master.
original=A/'assets/bunting-original.png'
if not original.exists():shutil.copyfile('/workspace/generated_images/exec-355aca70-12dc-48f5-826e-f28b2ad2394b.png',original)
a=Image.open(original).convert('RGBA');aa=np.array(a)[...,3];yy,xx=np.nonzero(aa>32);a=a.crop((int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1))).resize((124,24),Image.Resampling.LANCZOS);bunting=np.array(a);bunting[...,:3]=fit(bunting[...,:3],6);bunting[...,3]=np.where(bunting[...,3]>=128,255,0);bunting[bunting[...,3]==0]=0;Image.fromarray(bunting).save(A/'assets/bunting-native.png')
# Erase every superseded cloth/rope pixel, including the north-entrance string.
oldflag=np.array(Image.open(S/'flag-foreground-mask.png'))>0;legacy=np.array(Image.open(E/'flag-underpasses/mask.png'))>0;north=np.zeros_like(oldflag);north[0:64,336:480]=legacy[256:320,112:256];erase=oldflag|north
fg[oldflag]=0
# Different receiving planes are restored separately. Preserve actual lamp art.
protected=np.zeros_like(erase)
for name,cx,top,base,roots in posts:
 protected|=area((cx-8,top,cx+9,top+17))|area((cx-3,top+12,cx+4,base+16))
erase|=area((352,24,456,48))|area((344,392,456,416))
cleanup=erase&~protected;north_rock=cleanup&(Y<64)&((X<352)|(X>=456));yy,xx=np.nonzero(north_rock);bg[yy,xx]=oldbg[48+yy%8,xx];changed_ground[north_rock]=True;reset_ground(cleanup&(Y<64)&(X>=352)&(X<456),'sand');reset_ground(cleanup&(Y>=64)&(X>=136)&(X<184)&(Y<320),'lawn');reset_ground(cleanup&(Y>=64)&~((X>=136)&(X<184)&(Y<320)),'paving')
newflags=np.zeros_like(oldflag)
for name,x,y in [('west',116,278),('central',340,390),('north',340,22)]:
 h,w=bunting.shape[:2];m=bunting[...,3]>0;v=fg[y:y+h,x:x+w];v[m]=bunting[m];mask=np.zeros_like(oldflag);mask[y:y+h,x:x+w]=m;newflags|=mask;above[mask.reshape(H,16,W,16).any((1,3))]=True;categories['bunting '+name]=mask
 objects.append(dict(name=name+' bunting',kind='suspended flags',origin=[x,y],palette=6,asset='assets/bunting-native.png',physical='none; lamp bases separate'))
# Mark all newly lifted foreground cells without changing lower wall/base layers.
# Quantize only changed ground; native source/master colors outside it stay exact.
sections=json.loads((E/'sections.json').read_text());encoded={};nativebg=bg.copy();nativefg=fg.copy();edited_cells=(np.any(bg!=oldbg,2)|np.any(fg!=oldfg,2)).reshape(H,16,W,16).any((1,3))|(solid!=oldsolid)|(above!=oldabove)
for gy,gx in np.ndindex(H*2,W*2):
 y,x=gy*8,gx*8;rgb=bg[y:y+8,x:x+8];colors=set(map(tuple,rgb.reshape(-1,3)));opts=[b for b in range(13) if colors<=set(map(tuple,pals[b]))]
 if opts:
  bank=opts[0];pal=pals[bank];lo=np.zeros((8,8),np.uint8)
  for i,color in enumerate(pal,1):lo[np.all(rgb==color,2)]=i
 else:
  best=None
  for bank in [0,1,2,3,7,8]:
   d=((rgb.astype(np.int32)[:,:,None]-pals[bank].astype(np.int32)[None,None])**2).sum(3);ii=d.argmin(2);error=np.take_along_axis(d,ii[...,None],2).sum()
   if best is None or error<best[0]:best=(error,bank,ii)
  _,bank,ii=best;lo=(ii+1).astype(np.uint8);nativebg[y:y+8,x:x+8]=pals[bank][ii]
 rgb=fg[y:y+8,x:x+8];m=rgb[...,3]>0;hi=np.zeros((8,8),np.uint8);fb=0
 if m.any():
  colors=set(map(tuple,rgb[m,:3]));opts=[b for b in range(13) if colors<=set(map(tuple,pals[b]))]
  if not opts:
   original=oldfg[y:y+8,x:x+8];protected=(original[...,3]>0)&m&np.all(original[...,:3]==rgb[...,:3],2);protected_colors=set(map(tuple,rgb[protected,:3]));legal=[b for b in range(13) if protected_colors<=set(map(tuple,pals[b]))];assert legal,('Protected foreground palette',x,y)
   best=None
   for b in legal:
    d=((rgb[...,:3].astype(np.int32)[:,:,None]-pals[b].astype(np.int32)[None,None])**2).sum(3);ii=d.argmin(2);error=np.take_along_axis(d,ii[...,None],2)[m&~protected].sum()
    if best is None or error<best[0]:best=(error,b,ii)
   _,fb,ii=best;rgb[m&~protected,:3]=pals[fb][ii][m&~protected];nativefg[y:y+8,x:x+8]=rgb;opts=[fb]
  fb=opts[0]
  for i,color in enumerate(pals[fb],1):hi[m&np.all(rgb[...,:3]==color,2)]=i
 encoded[gy,gx]=[(lo,bank),(hi,fb)]
plans=[];stats=[]
for sec in sections:
 n=sec['name'];x0,y0,x1,y1=sec['box']
 if not edited_cells[y0:y1,x0:x1].any():continue
 old=np.fromfile(G/f'data/layouts/{n}/map.bin','<u2').reshape(y1-y0,x1-x0);grid=old.copy();glyphs=[np.zeros((8,8),np.uint8)];lookup={glyphs[0].tobytes():0};blocks={};attrs={};assigned={}
 def entry(a,b):
  key=a.tobytes()
  if key not in lookup:
   tid=len(glyphs);glyphs.append(a)
   for h in range(2):
    for v in range(2):lookup.setdefault(a[::-1 if v else 1,::-1 if h else 1].tobytes(),tid|h<<10|v<<11)
  return lookup[key]|b<<12
 for cy,cx in np.ndindex(grid.shape):
  y,x=cy+y0,cx+x0;es=[]
  for layer in range(2):
   for q in range(4):es.append(entry(*encoded[y*2+q//2,x*2+q%2][layer]))
  attr=0 if above[y,x] else 0x1000;key=tuple(es)+(attr,);preferred=int(old[cy,cx]&1023)
  if key not in assigned:
   mid=preferred if preferred not in blocks else next(i for i in range(1024) if i not in blocks);blocks[mid]=es;attrs[mid]=attr;assigned[key]=mid
  grid[cy,cx]=(int(old[cy,cx])&~0xfff)|assigned[key]|(0xc00 if solid[y,x] else 0)
 assert np.array_equal(grid&0xf000,old&0xf000),'Elevation must stay stable'
 assert len(glyphs)<=1008,(n,len(glyphs));plans.append((n,glyphs,blocks,attrs,grid));stats.append(dict(map=n,glyphs=len(glyphs),changed_cells=int(edited_cells[y0:y1,x0:x1].sum())))
# All banks pass before mutating native source.
for n,glyphs,blocks,attrs,grid in plans:
 for part in range(2):
  p=G/f'data/tilesets/{"secondary" if part else "primary"}/{n.lower()}';start=part*512;count=512 if part==0 else max(1,len(glyphs)-512);im=Image.new('P',(128,((count+15)//16)*8));im.putpalette([c for i in range(256) for c in (i*17%256,)*3])
  for i in range(count):
   if start+i<len(glyphs):im.paste(Image.fromarray(glyphs[start+i]).convert('P'),(i%16*8,i//16*8))
  im.save(p/'tiles.png',bits=4);(p/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*blocks.get(i,[0]*8)) for i in range(start,start+512)));(p/'metatile_attributes.bin').write_bytes(struct.pack('<512H',*[attrs.get(i,0x1000) for i in range(start,start+512)]))
 grid.tofile(G/f'data/layouts/{n}/map.bin');np.full((2,2),int(grid[0,0])|0xc00,'<u2').tofile(G/f'data/layouts/{n}/border.bin')
# Persist independently reviewable source layers, footprints and every-cell ledger.
Image.fromarray(nativebg).save(S/'native-ground.png');Image.fromarray(nativefg).save(S/'shared-foreground.png');np.save(S/'solid.npy',solid);np.save(S/'above.npy',above);np.save(A/'physical-labels.npy',owners);Image.fromarray(newflags.astype(np.uint8)*255).save(S/'flag-foreground-mask.png')
comp=nativebg.copy();m=nativefg[...,3]>0;comp[m]=nativefg[m,:3];Image.fromarray(source).save(O/'before.png');Image.fromarray(comp).save(O/'after.png');Image.fromarray(comp).save(E/'native-map.png')
for name,mask in categories.items():Image.fromarray(mask.astype(np.uint8)*255).save(A/(name.replace(' ','-')+'-mask.png'))
(A/'objects.json').write_text(json.dumps(objects,indent=2)+'\n');(A/'overlay-masks.json').write_text(json.dumps({n:n.replace(' ','-')+'-mask.png' for n in categories},indent=2)+'\n')
changes=[dict(cell=[int(x),int(y)],before=bool(oldsolid[y,x]),after=bool(solid[y,x]),reason=reasons.get((int(x),int(y)),str(owners[y,x]))) for y,x in np.argwhere(oldsolid!=solid)]
(O/'native-edit.json').write_text(json.dumps(dict(baseline=BASE,sections=stats,collision_changes=changes,objects=len(objects),cells=W*H,elevation_changes=0,palettes_changed=False),indent=2)+'\n')
with (O/'all-cells.csv').open('w') as f:
 writer=csv.writer(f);writer.writerow(['x','y','ground_material','physical_owner','solid','foreground_pixels','overlay_types','collision_changed'])
 for y,x in np.ndindex(H,W):
  hits=[name for name,m in categories.items() if m[y*16:y*16+16,x*16:x*16+16].any()];writer.writerow([x,y,materials[y,x],owners[y,x],int(solid[y,x]),int((nativefg[y*16:y*16+16,x*16:x*16+16,3]>0).sum()),' | '.join(hits),int(oldsolid[y,x]!=solid[y,x])])
print(json.dumps(dict(sections=stats,collision_changes=len(changes),open_cells=int((~solid).sum()),overlays=len(categories)),indent=2))
