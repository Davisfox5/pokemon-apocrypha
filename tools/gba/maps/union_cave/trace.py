"""Original HGSS Union Cave 1F reference trace; never reads a prior native layout."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'gba/art/union-cave-1f/source';E=S.parent/'evidence'
a=np.array(Image.open(S/'hgss-reference.png').convert('RGB'))[:960];r,g,b=a.transpose(2,0,1).astype(int)
# Source terrain colors: cool gray floor, blue pools, warm rock, black void.
floor=(g>=48)&(g>=r+4)&(abs(g-b)<=4)&(g-r<=32)
water=(b>=96)&(b-g>=24)&(g-r>=32)
void=(a.max(2)<32);rock=~(floor|water|void)
label=np.full(a.shape[:2],'R',dtype='<U1');label[floor]='.';label[water]='W';label[void]='X'
# Teal stalagmites are foreground rock features, not dark ordinary floor.
from scipy.ndimage import binary_dilation,label as components
seed=(g-r>=24)&(g-b>=8)&(r<80)&(g<=112)
cc,n=components(seed);sizes=np.bincount(cc.ravel());keep=(sizes>=20);keep[0]=False;seed=keep[cc]
candidate=(g-r>=24)&(g<=112)&(b<=g+8);cc,n=components(candidate);ids=np.unique(cc[seed]);ids=ids[ids>0];props=np.isin(cc,ids);label[props]='O'
# Character/item pixels occlude actual floor; retain rocks/stalagmites as scenery.
occluders=[('north-firebreather',(136,80,164,113)),('north-item',(64,192,81,207)),('west-hiker',(92,348,116,380)),('east-hiker',(330,382,354,416)),('south-firebreather',(378,604,404,640)),('south-trainer',(204,740,228,777)),('west-item',(80,596,96,614)),('east-item',(480,660,497,676)),('south-item',(384,914,402,933))]
# Clean reusable floor sample; only replace character/item ink, not surrounding walls.
clean=a.copy();sample=a[288:304,96:112].copy()
for name,(x0,y0,x1,y1) in occluders:
 for y in range(y0,y1):
  for x in range(x0,x1):
   rr,gg,bb=map(int,a[y,x]);terrain_earth=(rr>=gg>=bb and rr<160 and bb>32 and rr-gg<=32)
   if not terrain_earth:clean[y,x]=sample[y%16,x%16];label[y,x]='.'
# Reconstruct the actual terrain behind sprites that straddle a wall or pool.
# These are context-specific source repairs, not blanket floor rectangles.
def floor_fill(box):
 x0,y0,x1,y1=box
 for y in range(y0,y1):
  for x in range(x0,x1):clean[y,x]=sample[y%16,x%16];label[y,x]='.'
for box in [(330,382,354,416),(64,192,81,207),(80,596,96,614),(480,660,496,676),(384,914,402,933)]:floor_fill(box)
# North sprite stands on floor directly in front of a tall stalagmite.
floor_fill((138,80,162,112))
rock_sprite=a[448:480,480:496].copy();rock_labels=label[448:480,480:496].copy()
mask=rock_labels=='O';dst=clean[56:88,144:160];dst[mask]=rock_sprite[mask];label[56:88,144:160][mask]='O'
# Hiker's head occludes a straight rock face; feet stand below its lower edge.
for x0 in [88,104]:
 clean[344:368,x0:x0+16]=a[344:368,112:128];label[344:368,x0:x0+16]='R'
floor_fill((88,368,120,384))
# The southern firebreather's head covers the recessed front face, not floor.
clean[608:624,384:400]=a[608:624,400:416];label[608:624,384:400]='R'
floor_fill((380,624,408,640))
# The final trainer's head covers the pool's bottom bank; restore its water.
clean[740:764,204:224]=a[740:764,184:204];label[740:764,204:224]=label[740:764,184:204].copy()
clean[736:752,208:224]=a[736:752,192:208];label[736:752,208:224]='W'
# Source exit light is an entrance feature on walkable floor.
for x0,y0,x1,y1 in [(440,286,472,316),(440,904,472,938)]:label[y0:y1,x0:x1]='.'
# Floor and pool texture continuity; preserve original wall/shore silhouette.
floor_template=np.array(Image.fromarray(sample).quantize(colors=6).convert('RGB'))
for y in range(960):
 for x in range(544):
  if label[y,x]=='.' and not ((440<=x<472 and 286<=y<316) or (440<=x<472 and 904<=y<938)):clean[y,x]=floor_template[y%16,x%16]
# Repeat a clean HGSS plateau texture over bright plateau cores only.
# Keep the original outline and all front/side shading unchanged.
top=a[128:144,64:80].copy()
for x0,y0,x1,y1 in [(32,104,120,164),(64,316,144,360),(320,572,416,628)]:
 for y in range(y0,y1):
  for x in range(x0,x1):
   rr,gg,bb=map(int,a[y,x])
   if label[y,x]=='R' and rr>=112 and gg>=104 and rr>=gg>=bb:clean[y,x]=top[y%16,x%16]
# Native 16px material trace, separate from visual glyph packing.
plan=np.full((60,34),'R',dtype='<U1');confidence=np.zeros(plan.shape,float)
for y in range(60):
 for x in range(34):
  p=label[y*16:y*16+16,x*16:x*16+16];co={c:int((p==c).sum()) for c in '.WROX'}
  if co['O']>=48:ch='O'
  elif co['.']>=112:ch='.'
  elif co['W']>=112:ch='W'
  elif co['X']>=180:ch='X'
  else:ch='R'
  plan[y,x]=ch;confidence[y,x]=co[ch]/256
# Original staircase heads are occluded/rock-colored, recorded as explicit features.
features={'route32_entrance':[28,18],'route33_exit':[28,57],'north_lower_access':[6,16],'south_lower_access':[29,38]}
for name,(x,y) in features.items():plan[y,x]='.'
# Foreground heads may overlap the player; only each formation's bottom row
# occupies its rock footprint. Keep wall behind a head blocked independently.
blocked=np.isin(plan,['R','W','X']);heads=np.zeros(label.shape,bool);formations=[]
cc,n=components(label=='O')
from scipy.ndimage import find_objects
for i,box in enumerate(find_objects(cc),1):
 if box is None:continue
 yy,xx=box;mask=cc[box]==i
 if mask.sum()<30:continue
 root_y=(yy.stop-1)//16;roots=[[x,root_y] for x in range(xx.start//16,(xx.stop-1)//16+1)]
 for x,y in roots:blocked[y,x]=True
 local=heads[box];local[mask & (np.arange(yy.start,yy.stop)[:,None]//16<root_y)]=True
 formations.append({'source_pixel_box':[xx.start,yy.start,xx.stop,yy.stop],'root_cells':roots,'overhead_head_rows':'above root row'})
for y,x in zip(*np.where(plan=='O')):
 if any([int(x),int(y)] in f['root_cells'] for f in formations):continue
 piece=label[y*16:y*16+16,x*16:x*16+16];blocked[y,x]=int((piece=='R').sum())>=80 or int((piece=='X').sum())>=32
np.save(S/'hgss-foot-blocked.npy',blocked);np.save(S/'hgss-overhead-rock-heads.npy',heads);(S/'stalagmite-footprints.json').write_text(json.dumps(formations,indent=2)+'\n')
(S/'hgss-material-grid.txt').write_text('\n'.join(''.join(row) for row in plan)+'\n');np.save(S/'hgss-pixel-materials.npy',label);np.save(S/'hgss-material-confidence.npy',confidence);Image.fromarray(clean).save(S/'clean-terrain.png')
(S/'reference.json').write_text(json.dumps({'reference':'https://archives.bulbagarden.net/wiki/File:Union_Cave_1F_HGSS.png','image_url':'https://archives.bulbagarden.net/media/upload/6/65/Union_Cave_1F_HGSS.png','credits':'Nintendo / Game Freak / Creatures; overview hosted by Bulbagarden Archives','sha256':hashlib.sha256((S/'hgss-reference.png').read_bytes()).hexdigest(),'dimensions':[544,962],'native_grid':[34,60],'origin':[0,0],'scale':1,'crop':'bottom two border pixels omitted; map remains 34x60','basis':'visual terrain interpretation, not extracted DS collision','occluders_removed':occluders,'features':features,'scope':'1F; Route33 exterior and lower floors not built in this pass'},indent=2)+'\n')
ref=Image.open(S/'hgss-reference.png').convert('RGB');out=Image.new('RGB',(610,1010),'white');out.paste(ref,(45,30));d=ImageDraw.Draw(out)
for x in range(35):d.line((45+x*16,30,45+x*16,990),fill='#777777');d.text((45+x*16,10),str(x),fill='black')
for y in range(61):d.line((45,30+y*16,589,30+y*16),fill='#777777');d.text((5,30+y*16),str(y),fill='black')
out.save(E/'numbered-hgss.png')
print('Traced',plan.shape,'materials',dict(zip(*np.unique(plan,return_counts=True))))
