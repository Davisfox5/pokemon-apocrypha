"""Native Pallet revision: HGSS model projections, FRLG landmark reference.
All drawing is at native resolution. Material and traversal grids are authored
separately. This explicitly authorized replacement changes only Pallet maps.
"""
from pathlib import Path
import sys,json,csv
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT/'tools/gba/maps/pallet_rebuild'),str(ROOT/'tools/gba/maps')]
from native import numbered
from claude_cherrygrove import hgss as CG
A=ROOT/'gba/art/pallet-native';S=A/'source';EV=A/'evidence';AS=S/'assets'
E=Path('/workspace/apocrypha-src')
NAMES=['ApocPalletTown','ApocPalletRedHouse1F','ApocPalletRedHouse2F','ApocPalletOakHouse','ApocPalletLab']
SPECS=[(36,36),(18,14),(16,13),(18,14),(20,18)]
placements=[];maps={}
def snap(a):
 a=np.array(a.convert('RGBA'));a[...,:3]&=248;return Image.fromarray(a)
def quant(im,n=15):
 a=np.array(im.convert('RGBA'));mask=a[...,3]>0
 if not mask.any():return im
 pal=Image.fromarray(a[...,:3][mask].reshape(-1,1,3)).quantize(n,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
 rgb=np.array(Image.fromarray(a[...,:3]).quantize(palette=pal,dither=Image.Dither.NONE).convert('RGB'))&248
 return Image.fromarray(np.dstack([rgb,a[...,3]]))
def tone(im,low,high):
 a=np.array(im.convert('RGBA'));lum=a[...,:3].astype(float)@np.array([.24,.55,.21]);valid=a[...,3]>0
 l,h=np.percentile(lum[valid],[1,99]);t=np.clip((lum-l)/max(1,h-l),0,1)
 a[...,:3]=(np.array(low)[None,None,:]*(1-t[...,None])+np.array(high)[None,None,:]*t[...,None]).astype('uint8')&248
 return Image.fromarray(a)
def repeat(im,size):
 out=Image.new('RGBA',size)
 for y in range(0,size[1],im.height):
  for x in range(0,size[0],im.width):out.paste(im,(x,y))
 return out
# Palette budgets follow native tile rows of the building, not one palette for a whole facade.
def building(name):
 im=Image.open(AS/(name+'.png')).convert('RGBA');a=np.array(im);rgb=a[...,:3].astype(float)
 if name=='house':
  red=(rgb[...,0]>rgb[...,1]*1.2)&(rgb[...,0]>rgb[...,2]*1.2)
  lum=rgb@np.array([.3,.5,.2]);t=np.clip((lum-55)/170,0,1)
  for k,(lo,hi) in enumerate(zip((88,48,48),(224,144,104))):a[...,k][red]=(lo+(hi-lo)*t[red]).astype('uint8')
  # Cool slate trim and warm pale siding preserve every HGSS mullion and clapboard.
  wall=(~red)&(a[...,3]>0);t=np.clip((lum-55)/180,0,1)
  for k,(lo,hi) in enumerate(zip((56,72,88),(240,232,208))):a[...,k][wall]=(lo+(hi-lo)*t[wall]).astype('uint8')
 else:
  # Restrained sandstone and blue-gray metal, retaining roof grid and skylights.
  a[...,:3]=np.minimum(248,rgb*np.array([.94,.98,1.02])).astype('uint8')
 im=Image.fromarray(a);out=Image.new('RGBA',im.size)
 for y0,y1 in ([(0,64),(64,im.height)] if name=='house' else [(0,48),(48,im.height)]):out.paste(quant(im.crop((0,y0,im.width,y1))),(0,y0))
 out.save(AS/(name+'-native.png'));return out
house=building('house');lab=building('lab')
tree=Image.open(ROOT/'gba/art/route31-catalog/source/local-art/cherrygrove-tree-with-shadow.png').convert('RGBA')
lawn=quant(tone(Image.fromarray(CG.grass_texture()),(104,152,104),(144,184,128)),6)
path=quant(tone(Image.fromarray(CG.path_texture()),(192,184,144),(216,208,168)),3)
# Original HGSS water uses a restrained coastal ramp, retaining all original wave shapes.
water=quant(tone(Image.open(ROOT/'gba/art/pallet-town-rebuild/source/assets/hgss-water.png'),(48,104,136),(104,168,176)),6);water.save(AS/'hgss-water.png')
flower=Image.open(ROOT/'gba/art/pallet-town-rebuild/source/assets/hgss-flowers.png').convert('RGBA')
fence=Image.open(ROOT/'gba/art/pallet-town-rebuild/source/assets/picket-fence.png').convert('RGBA')
props={p.stem:quant(Image.open(p).convert('RGBA')) for p in AS.glob('*.png') if p.stem in ['mailbox','sign','lab-sign','kitchen','tv','dining','bookshelf','bed','desk','storage','console','research','lab-desk','research-table','cabinet','lab-machine','sofa','armchair','coffee-table','plant']}

def start(name,w,h,base):
 global cur,g,f,mat,front,collision,elevation,behavior
 cur=name;g=repeat(base,(w*16,h*16));f=Image.new('RGBA',g.size)
 mat=np.full((h,w),'lawn' if name==NAMES[0] else 'wood floor',object);front=[[[] for x in range(w)] for y in range(h)]
 collision=np.zeros((h,w),np.uint8);elevation=np.full((h,w),3,np.uint8);behavior=np.zeros((h,w),np.uint8)
def material(rect,label,coll=None,elev=None,beh=None):
 x0,y0,x1,y1=rect;mat[y0:y1,x0:x1]=label
 if coll is not None:collision[y0:y1,x0:x1]=coll
 if elev is not None:elevation[y0:y1,x0:x1]=elev
 if beh is not None:behavior[y0:y1,x0:x1]=beh
def place(im,x,y,label,block=None):
 f.alpha_composite(im,(x,y));placements.append(dict(map=cur,asset=label,x=x,y=y,width=im.width,height=im.height,collision_rect=block))
 aa=np.array(im)[...,3]>0
 for cy in range(max(0,y//16),min(len(front),(y+im.height+15)//16)):
  for cx in range(max(0,x//16),min(len(front[0]),(x+im.width+15)//16)):
   if aa[max(0,cy*16-y):min(im.height,(cy+1)*16-y),max(0,cx*16-x):min(im.width,(cx+1)*16-x)].any():front[cy][cx].append(label)
 if block:
  x0,y0,x1,y1=block;collision[y0:y1,x0:x1]=1

def surf(rect,tex,label):
 x0,y0,x1,y1=rect;g.paste(repeat(tex,((x1-x0)*16,(y1-y0)*16)),(x0*16,y0*16));material(rect,label)
def walkway(rect):
 surf(rect,path,'gravel path')
def rug(rect,color):
 x0,y0,x1,y1=[v*16 for v in rect];d=ImageDraw.Draw(g)
 d.rectangle((x0,y0,x1-1,y1-1),fill=(72,88,88,255));d.rectangle((x0+2,y0+2,x1-3,y1-3),fill=(*color,255));d.rectangle((x0+5,y0+5,x1-6,y1-6),outline=(200,192,160,255))
 material(rect,'woven rug')
def end(warps,bgs=None,actors=None):
 name=cur;d=S/name;d.mkdir(exist_ok=True)
 # Native 8x8 tiles use material-family palettes. Quantization is deferred to pack.
 snap(g).save(d/'ground.png');snap(f).save(d/'foreground.png')
 m=json.loads((E/f'data/maps/{name}/map.json').read_text())
 assert len(warps)==len(m['warp_events'])
 for ev,xy in zip(m['warp_events'],warps):
  ev['x'],ev['y']=xy;collision[xy[1],xy[0]]=0;ev['elevation']=0 if name==NAMES[0] else 3
 if bgs is not None:
  assert len(bgs)==len(m['bg_events'])
  for ev,xy in zip(m['bg_events'],bgs):ev['x'],ev['y']=xy
 if actors:
  for ev,xy in zip(m['object_events'],actors):ev['x'],ev['y']=xy;collision[xy[1],xy[0]]=0
 records=[]
 for y in range(mat.shape[0]):
  for x in range(mat.shape[1]):records.append(dict(x=x,y=y,ground=mat[y,x],foreground=front[y][x],collision=int(collision[y,x]),elevation=int(elevation[y,x]),behavior=int(behavior[y,x])))
 (d/'cells.json').write_text(json.dumps(records,indent=1)+'\n');(d/'map.json').write_text(json.dumps(m,indent=2)+'\n')
 with (d/'materials.csv').open('w') as out:
  wr=csv.writer(out,lineterminator="\n");wr.writerow(['x','y','ground','foreground','collision','elevation','behavior'])
  for r in records:wr.writerow([r['x'],r['y'],r['ground'],';'.join(r['foreground']),r['collision'],r['elevation'],r['behavior']])
 im=g.copy();im.alpha_composite(f);im.save(EV/(name+'-assembly.png'));numbered(im,2).save(EV/(name+'-assembly-grid.png'))
 maps[name]=dict(width=mat.shape[1],height=mat.shape[0],warps=warps)

start(NAMES[0],36,36,lawn)
# Spacious FRLG landmark arrangement: homes north; flower garden west; lab southeast; south inlet.
walkway((17,0,19,19));walkway((4,16,32,19));walkway((15,19,18,30))
for dx in (0,18):
 walkway((7+dx,13,9+dx,17));walkway((6+dx,13,12+dx,14))
 # Complete property boundaries are low pickets with a two-cell entrance.
 for x in range(4+dx,14+dx):
  if x in (7+dx,8+dx):continue
  place(fence.crop((x%2*16,0,x%2*16+16,16)),x*16,15*16,'yard fence',(x,15,x+1,16))
 place(house,(5+dx)*16+4,7*16,'HGSS house',(5+dx,7,13+dx,13))
 place(props['mailbox'],(5+dx)*16+2,14*16-10,'mailbox',(5+dx,14,6+dx,15))
 # Beds at the window side, away from the entrance and player lane.
 for x in (10+dx,11+dx,12+dx):place(flower,x*16,14*16,'flowers')
# Laboratory: broad paved entry forecourt and visible side clearance.
walkway((23,25,27,28));walkway((18,27,30,29));walkway((21,24,30,25))
place(lab,21*16+7,19*16,'HGSS laboratory',(21,19,30,24))
place(props['lab-sign'],28*16,26*16-5,'laboratory sign',(28,26,29,27))
# Garden preserves the FRLG southwest flower landmark, with a usable perimeter.
walkway((5,22,14,23));walkway((5,23,6,28));walkway((13,23,14,28));walkway((5,27,14,28));walkway((14,25,16,27))
for y in (23,24,25):
 for x in range(7,12):place(flower,x*16,y*16,'garden flowers')
for x in range(6,13):place(fence.crop((x%2*16,0,x%2*16+16,16)),x*16,21*16,'garden fence',(x,21,x+1,22))
place(props['sign'],10*16+1,27*16-4,'Red memorial',(10,27,11,28))
place(props['sign'],18*16+1,20*16-4,'town sign',(18,20,19,21))
# Round path corners and draw the grass/gravel seam as a narrow material transition.
mask=Image.fromarray(np.where(mat=='gravel path',255,0).astype('uint8')).resize(g.size,Image.Resampling.NEAREST)
mask=mask.filter(ImageFilter.GaussianBlur(2)).point(lambda v:255 if v>=128 else 0)
edge=mask.filter(ImageFilter.MaxFilter(3));g.paste(repeat(lawn,g.size),(0,0),Image.fromarray(np.where(np.array(edge)>0,255,0).astype('uint8')))
rim=Image.new('RGBA',g.size,(160,176,128,255));g.paste(rim,(0,0),edge);g.paste(repeat(path,g.size),(0,0),mask)
# Coastal inlet retains a walkable west/east bank and opens south to Route 21.
for y in range(30,36):
 x0,x1=(11,20) if y==30 else (10,21)
 surf((x0,y,x1,y+1),water,'coastal water');material((x0,y,x1,y+1),'coastal water',0,1,0x15)
# Complete rounded inlet corners with an unbroken three-pixel stone lip.
mask=Image.new('L',g.size);md=ImageDraw.Draw(mask);md.rounded_rectangle((160,480,335,640),radius=16,fill=255)
outer=mask.filter(ImageFilter.MaxFilter(7));g.paste((136,152,136,255),(0,0),outer);g.paste((184,192,168,255),(0,0),mask.filter(ImageFilter.MaxFilter(3)));g.paste(repeat(water,g.size),(0,0),mask)
# Distinct tree root beds; crowns overlap only the previous row's canopy.
roots=[(x,y) for y in range(2,34,2) for x in (0,2,32,34)]
roots += [(x,y) for y in (2,4) for x in range(4,32,2) if x not in (16,18)]
roots += [(x,y) for y in (32,34) for x in list(range(4,10,2))+list(range(22,32,2))]
for x,y in sorted(set(roots),key=lambda p:(p[1],p[0])):
 place(tree,x*16,(y-1)*16,'shared Cherrygrove tree',(x,y-1,x+2,y+2))
# Door panels are native complete HGSS planes aligned to one walkable metatile.
# Their jambs remain from the original model; adapting the panel to 16x24 preserves its frame.
for x,y,asset,box in [(7,12,house,(24,78,49,96)),(25,12,house,(24,78,49,96)),(25,23,lab,(53,60,77,79))]:
 panel=asset.crop(box).resize((16,24),Image.Resampling.NEAREST)
 place(panel,x*16,(y-1)*16+8,'HGSS entrance panel');behavior[y,x]=0x69
end([(7,12),(25,12),(25,23)],[(28,26),(5,14),(23,14),(18,20),(10,27)])

# Rooms: HGSS furniture in coherent rooms, with a continuous floor and articulated walls.
# The original HGSS floor material is recolored to a quieter warm oak ramp.
sys.path.insert(0,str(ROOT/'tools/gba/maps/pallet_native'))
import assets as assets_module
texbank=assets_module.R.Tex0(assets_module.R.narc.load(assets_module.PHG/'files/a/0/4/4')[43])
def texture(name):
 e=next(e for e in texbank.textures if e.name==name);return Image.fromarray(assets_module.R.decode(texbank,e,next((p.name for p in texbank.palettes if p.name==name+'_pl'),texbank.pal_for(e).name)))
wood=quant(tone(texture('red_h_yuka1'),(152,120,88),(184,152,112)),5)
walltex=quant(tone(texture('red_h_kabe1'),(120,136,136),(224,224,200)),6)
# Architectural room shell is deliberately assembled from original material planes.
def room(name,w,h,labroom=False):
 floor=wood
 if labroom:
  floor=Image.new('RGBA',(32,32),(176,192,184,255));d=ImageDraw.Draw(floor);d.line((0,31,31,31),fill=(152,168,168));d.line((31,0,31,31),fill=(152,168,168))
 start(name,w,h,floor)
 # Dark exterior void; complete sidewall thickness and continuous rear wall.
 d=ImageDraw.Draw(g);d.rectangle((0,0,w*16-1,h*16-1),outline=(40,56,64),width=8)
 g.paste((216,216,192,255),(16,16,(w-1)*16,40))
 g.paste(repeat(walltex,((w-2)*16,8)),(16,40))
 d=ImageDraw.Draw(g);d.rectangle((8,8,w*16-9,15),fill=(80,104,112));d.line((16,16,w*16-17,16),fill=(232,232,208),width=2)
 d.rectangle((8,16,15,(h-1)*16-1),fill=(96,120,120));d.rectangle(((w-1)*16,16,w*16-9,(h-1)*16-1),fill=(72,96,104))
 d.line((16,47,w*16-17,47),fill=(88,112,112),width=3);d.line((16,45,w*16-17,45),fill=(216,216,192))
 d.rectangle((8,(h-1)*16,w*16-9,h*16-9),fill=(80,104,112));d.line((16,(h-1)*16,w*16-17,(h-1)*16),fill=(216,216,192),width=2)
 material((0,0,w,3),'rear wall',1);material((0,0,1,h),'side wall',1);material((w-1,0,w,h),'side wall',1);material((0,h-1,w,h),'front wall',1)
 # Windows have complete casing, sill and soft cool glass; original window texture.
 win=quant(texture('red_h_mado'));place(win,7*16,22,'HGSS window')
def prop(key,x,y,block=None):place(props[key],int(x*16),int(y*16),key,block)
def entrance(xs,y):
 x0=min(xs);x1=max(xs)+1
 rug((x0,y-1,x1,y+1),(136,88,72))
 for x in xs:
  material((x,y,x+1,y+1),'exit mat',0,3,0x65)
  g.paste((40,56,64,255),(x*16,(y+1)*16,x*16+16,(y+2)*16))
def stairs(x,y,up=True):
 # HGSS actual staircase material with its entire tread/wall join, at original scale.
 src=Image.open(Path('/workspace/tooling/pallet-rebuild-reference')/('Red1F' if up else 'Red2F')/'hgss-terrain.png').convert('RGBA').crop((160,16,208,64))
 place(quant(tone(src,(72,88,96),(200,192,152)),12),x*16,y*16,'HGSS staircase',(x,y,x+3,y+3))
 material((x+2,y+1,x+3,y+2),'stair landing',0,3,0xeb if up else 0xee)
 if up:material((x+1,y+1,x+2,y+3),'stair approach',0,3,0)
 # Visible lower tread remains a clear approach, south of the landing.
 material((x+2,y+2,x+3,y+3),'stair approach',0,3,0)

room(NAMES[1],18,14)
rug((3,6,9,10),(112,136,136));prop('dining',4,6,(4,6,9,9))
prop('kitchen',2,3,(2,3,6,6));prop('tv',10,3,(10,3,13,6))
rug((11,7,15,11),(152,136,104));prop('sofa',11,7,(11,7,14,9));prop('coffee-table',12,10,(12,10,14,12))
prop('plant',2,10,(2,10,4,12));prop('plant',15,10,(15,10,17,12))
stairs(13,2,True);entrance([8,9],12)
end([(9,12),(8,12),(15,3)],[(11,5),(6,8)])
room(NAMES[2],16,13)
rug((3,6,10,10),(104,136,144));prop('bed',2,6,(2,6,5,10));prop('desk',6,3,(6,3,9,7));prop('storage',2,3,(2,3,5,6));prop('console',8,8,(8,8,9,9));prop('plant',12,9,(12,9,14,11))
stairs(11,2,False)
end([(13,3)],[(10,2),(8,8),(6,6)])
room(NAMES[3],18,14)
rug((8,6,14,10),(136,136,104));prop('dining',9,6,(9,6,14,9));prop('kitchen',12,3,(12,3,16,6));prop('tv',8,3,(8,3,11,6));prop('storage',2,3,(2,3,5,6));prop('bookshelf',6,3,(6,3,8,6))
rug((2,7,6,11),(144,128,104));prop('armchair',2,7,(2,7,4,10));prop('coffee-table',4,9,(4,9,6,11));prop('plant',15,10,(15,10,17,12));entrance([7,8,9],12)
end([(8,12),(9,12),(7,12)],[(3,5)],[(12,10)])
room(NAMES[4],20,18,True)
prop('research',2,3,(2,3,5,7));prop('lab-desk',6,3,(6,3,12,7));prop('cabinet',14,3,(14,3,17,6));prop('cabinet',16.5,3,(16,3,19,6))
prop('lab-machine',2,8,(2,8,6,13));prop('research-table',13,8,(13,8,17,11))
for x,bx in [(2,2),(4.5,4),(14,14),(16.5,16)]:prop('cabinet',x,13,(bx,13,bx+3,16))
prop('plant',6,9,(6,9,8,11));prop('plant',17,9,(17,9,19,11))
entrance([8,9,10],16)
end([(9,16),(10,16),(8,16)],[(9,6),(6,6)],[(9,9)])
(S/'maps.json').write_text(json.dumps(maps,indent=2)+'\n');(S/'placements.json').write_text(json.dumps(placements,indent=2)+'\n')
print('Assembled native layers for',len(maps),'maps.')
