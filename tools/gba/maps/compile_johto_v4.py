#!/usr/bin/env python3
"""Compile the HGSS-derived Cherrygrove artwork into native GBA tiles/metatiles.
Geometry is authored separately from source textures. Never writes production game/.
"""
from pathlib import Path
import sys,json,struct,hashlib,itertools
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];ART=ROOT/'gba/art/johto-v4';OUT=ART/'native';EV=ART/'evidence'
G=Path(sys.argv[1]).resolve();assert G==ROOT/'tools/vendor/gba/johto-v4-game'
OUT.mkdir(exist_ok=True);EV.mkdir(exist_ok=True)
W,H=64,32;PW,PH=W*16,H*16
# Use native source textures. The tree is the one-crown billboard texture.
def source(n):return Image.open(ART/'sources'/f'{n}.png').convert('RGBA')
images={n:source(n) for n in ['grass02','road01','beach01','cliff01gs','wall01_g','wall01_d','sea_un','sea_on','sea_rock','sea_rock_m','rock01','tree01gs','flower01','flower02','yo_sp1','fence_a','pond_on','fieldkk01']}
for n in ['house','gold_house','mart','center','sign']:images[n]=Image.open(ART/'prepared'/f'{n}.png').convert('RGBA')
# DS billboard projection adapted to one 32x48 GBA canopy; no second crown.
a=images['tree01gs'];c=a.crop(a.getbbox()).resize((32,40),Image.Resampling.NEAREST);images['tree']=Image.new('RGBA',(32,48));images['tree'].paste(c,(0,8))
# Tile families each own a palette. Building colors share four additional banks.
def colors(n):return [p[:3] for p in images[n].getdata() if p[3]]
def quant_palette(cs,n=15):
 im=Image.new('RGB',(len(cs),1));im.putdata(cs);q=im.quantize(colors=n,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE);p=q.getpalette();out=[]
 for i in sorted(set(q.getdata())):
  c=tuple((v<<3)|(v>>2) for v in [round(p[i*3+j]*31/255) for j in range(3)])
  if c not in out:out.append(c)
 return out
pals={0:quant_palette(colors('grass02')+colors('road01')),1:quant_palette(colors('sea_un')+colors('sea_on')+[(240,248,248)]*1000+[(176,216,240)]*500),2:quant_palette(colors('beach01')+colors('grass02')),3:quant_palette(colors('wall01_g')+colors('wall01_d')+colors('cliff01gs')+colors('rock01')+colors('fieldkk01')),4:quant_palette(colors('tree')),5:quant_palette(colors('yo_sp1')+colors('fence_a')+colors('flower01')+colors('flower02')),11:quant_palette(colors('sea_rock')+colors('sea_rock_m')),12:quant_palette(colors('pond_on'))}
# Roof, timber and shop materials: cluster each palette from the relevant surface.
bc=[]
for n in ['house','gold_house','mart','center']:bc+=colors(n)
groups=[[],[],[],[],[]]
for c in bc:
 r,g,b=c
 k=0 if r>g*1.2 and r>b*1.1 else 1 if b>r*1.12 else 2 if max(c)-min(c)<30 else 3 if r>=g and g>b else 4
 groups[k].append(c)
for bank,cs in zip([6,7,8,9,10],groups):pals[bank]=quant_palette(cs or bc)
palarr={b:np.array(cs,dtype=np.int32) for b,cs in pals.items()}
color_cache={}
def nearest(rgb,banks):
 key=(rgb,tuple(banks))
 if key not in color_cache:
  v=np.array(rgb);options=[]
  for b in banks:
   dd=np.sum((palarr[b]-v)**2,axis=1);i=int(np.argmin(dd));options.append((int(dd[i]),b,i))
  _,b,i=min(options);color_cache[key]=(b,i+1)
 return color_cache[key]
# Canvas encodes bank*16+index; zero is transparent only in source objects.
canvas=np.zeros((PH,PW),dtype=np.uint8);watermask=np.ones((PH,PW),dtype=bool);solid=np.ones((H,W),dtype=bool);beh=np.zeros((H,W),dtype=np.uint16)
assets={}
def asset(n,banks):
 key=(n,tuple(banks))
 if key not in assets:
  im=images[n];a=np.array(im);o=np.zeros(a.shape[:2],dtype=np.uint8)
  for rgb in set(map(tuple,a[a[:,:,3]>0,:3])):
   b,i=nearest(rgb,banks);o[np.all(a[:,:,:3]==rgb,axis=2)&(a[:,:,3]>0)]=b*16+i
  assets[key]=o
 return assets[key]
def stamp(n,x,y,banks,collision=None):
 a=asset(n,banks);h,w=a.shape;xx=max(x,0);yy=max(y,0);xe=min(x+w,PW);ye=min(y+h,PH)
 if xe<=xx or ye<=yy:return
 aa=a[yy-y:ye-y,xx-x:xe-x];mask=aa!=0;v=canvas[yy:ye,xx:xe];v[mask]=aa[mask];watermask[yy:ye,xx:xe][mask]=False
 if collision:
  l,t,r,b=collision
  solid[max(0,(y+t)//16):min(H,(y+b+15)//16),max(0,(x+l)//16):min(W,(x+r+15)//16)]=True
objects=[]
def obj(n,x,y,banks,collision=None):stamp(n,x,y,banks,collision);objects.append(dict(name=n,x=x,y=y,width=images[n].width,height=images[n].height))
def tilefill(n,banks,mask=None):
 a=asset(n,banks);z=np.tile(a,((PH+a.shape[0]-1)//a.shape[0],(PW+a.shape[1]-1)//a.shape[1]))[:PH,:PW]
 if mask is None:canvas[:]=z
 else:canvas[mask]=z[mask];watermask[mask]=False

def polygon(points):
 im=Image.new('1',(PW,PH));ImageDraw.Draw(im).polygon([(round(x*16),round(y*16)) for x,y in points],fill=1);return np.array(im,dtype=bool)
def rectmask(x,y,w,h):return polygon([(x,y),(x+w,y),(x+w,y+h),(x,y+h)])
tilefill('sea_un',[1])
land=polygon([(33,0),(64,0),(64,32),(31,32),(31,24),(28,23),(27,21),(25,21),(24,19),(24,10),(28,9),(33,9)])|rectmask(0,0,33,6)
tilefill('grass02',[0],land)
for y in range(H):
 for x in range(W):solid[y,x]=not land[y*16+8,x*16+8]
# Cream western beach, following the original map's bay.
sand=polygon([(25,9),(30,9),(29,11),(28,13),(28,16),(29,18),(31,20),(32,21),(31,23),(28,22),(26,21),(24,19),(24,11)])
tilefill('beach01',[2],sand)
for y in range(H):
 for x in range(W):
  if sand[y*16+8,x*16+8]:solid[y,x]=False
# Low offshore sandbar and irregular rocky island.
sandbar=rectmask(12,19,6,3);tilefill('beach01',[2],sandbar)
island=polygon([(1,12),(5,12),(5,14),(8,14),(9,15),(9,17),(4,17),(4,15),(1,15)]) | polygon([(0,20),(4,20),(5,21),(5,24),(0,24)])
tilefill('fieldkk01',[3],island)
# Native cliff faces have a grassy cap and a coherent continuous front.
images['north_cliff']=images['wall01_g'].resize((32,48),Image.Resampling.NEAREST)
for x in range(0,33*16,32):obj('north_cliff',x,6*16,[3])
solid[6:9,:33]=True
# Vertical north cliff return and southern headland, both supported by rocky top.
images['side_cliff']=images['wall01_g'].crop((0,0,32,16)).transpose(Image.Transpose.ROTATE_90)
for y in range(0,6*16,32):stamp('side_cliff',32*16,y,[3])
solid[:9,32:33]=True
for x,y,w in [(1,14,3),(4,16,5),(0,23,5)]:
 for xx in range(x*16,(x+w)*16,32):stamp('wall01_d',xx,y*16,[3])
for y in range(23*16,PH,32):stamp('side_cliff',30*16,y,[3])
solid[23:,30:32]=True
# Worn paths use compact two/three-tile widths, faithful to the source arrangement.
paths=set()
def lane(x,y,w,h):paths.update((xx,yy) for yy in range(y,y+h) for xx in range(x,x+w) if 0<=xx<W and 0<=yy<H)
lane(35,0,3,13);lane(33,10,19,3);lane(39,11,3,10);lane(33,16,9,2);lane(39,18,13,3);lane(50,10,3,14);lane(51,14,13,3);lane(51,22,7,2);lane(42,8,2,3);lane(51,8,2,3);lane(34,14,2,3);lane(45,16,2,4);lane(54,19,2,4)
# Pixel-edge masks retain small grassy corners instead of square path intersections.
pm=Image.new('1',(PW,PH));dr=ImageDraw.Draw(pm)
for x,y in paths:
 dr.rectangle((x*16,y*16,x*16+15,y*16+15),fill=1)
 for dx,dy,box in [(-1,-1,(0,0,5,5)),(1,-1,(10,0,15,5)),(-1,1,(0,10,5,15)),(1,1,(10,10,15,15))]:
  if (x+dx,y) not in paths and (x,y+dy) not in paths:
   bx,by,bw,bh=box
   for py in range(by,bh+1):
    for px in range(bx,bw+1):
     cx=5 if dx<0 else 10;cy=5 if dy<0 else 10
     if (px-cx)**2+(py-cy)**2>30:dr.point((x*16+px,y*16+py),fill=0)
pathmask=np.array(pm,dtype=bool)&land;tilefill('road01',[0],pathmask)
for x,y in paths:
 if land[y*16+8,x*16+8]:solid[y,x]=False
for xx,yy,ww,hh in [(33,10,5,6),(43,12,6,6),(53,15,5,7)]:
 plot=rectmask(xx,yy,ww,hh);tilefill('grass02',[0],plot);pathmask[plot]=False
# Shade the ragged path edge using the native road-edge palette color.
edge=pathmask & (~np.roll(pathmask,1,axis=0)|~np.roll(pathmask,-1,axis=0)|~np.roll(pathmask,1,axis=1)|~np.roll(pathmask,-1,axis=1))
eb,ei=nearest((160,176,120),[0,2]);canvas[edge]=eb*16+ei
# Water at the northeast pocket is a separate quiet pond, as in HGSS.
pond=polygon([(54,0),(61,0),(61,6),(59,8),(56,6),(54,4)]);tilefill('pond_on',[12],pond)
# Shore foam is a narrow edge, not a hard rectangular sand stamp.
water0=watermask.copy();shore=(sand|sandbar|island)&(~np.roll(water0,1,0)|~water0)
foam=(water0 & (np.roll(~water0,1,0)|np.roll(~water0,-1,0)|np.roll(~water0,1,1)|np.roll(~water0,-1,1)))
fb,fi=nearest((232,248,240),[1]);canvas[foam]=fb*16+fi
# Keep foam static but preserve moving sea beneath it at tile packing time.
watermask[foam]=False
for x,y,kind in [(5,10,'sea_rock'),(6,12,'sea_rock'),(9,11,'sea_rock'),(2,18,'sea_rock'),(6,24,'sea_rock'),(10,23,'sea_rock'),(14,25,'sea_rock'),(23,20,'sea_rock'),(25,19,'sea_rock'),(27,19,'sea_rock'),(23,22,'sea_rock_m'),(24,24,'sea_rock'),(11,9,'rock01'),(23,9,'rock01'),(25,9,'rock01')]:obj(kind,x*16,y*16,[11] if 'sea' in kind else [3])
# Single-crown forests, sorted back to front, with trunk collision and occluding canopy.
trees=set()
for y in [0,2,3]:
 trees.update((x,y) for x in range(0,32,2));trees.update((x,y) for x in range(38,54,2))
for y in [4,6,8]:trees.update((x,y) for x in range(60,64,2))
for x,y in [(54,4),(56,6),(58,7),(38,5),(46,4),(48,4)]:trees.add((x,y))
for y in range(20,32,2):trees.update((x,y) for x in range(33,40,2))
for y in range(24,32,2):trees.update((x,y) for x in range(39,60,2))
for y in range(18,32,2):trees.update((x,y) for x in range(60,64,2))
for y in range(21,32,2):trees.add((58,y))
# Dense interior forest floor uses the original canopy's shadow color.
for x,y in trees:
 if (x+2,y) in trees and (x,y+2) in trees:
  b,i=nearest((80,88,40),[4]);canvas[(y+1)*16:min(PH,(y+4)*16),x*16:min(PW,(x+2)*16)]=b*16+i
for x,y in sorted(trees,key=lambda p:(p[1],p[0])):obj('tree',x*16,y*16,[4],(0,32,32,48))
# Flower beds and white picket fences from the same HGSS texture set.
images['flowers']=images['yo_sp1'].crop((0,0,16,32));images['flowers']=images['flowers'].crop(images['flowers'].getbbox()).resize((16,16),Image.Resampling.NEAREST)
images['fence']=images['fence_a'].crop((0,0,32,16))
for x,y,w,h in [(55,10,6,2),(42,21,6,2),(58,17,3,2)]:
 for yy in range(y,y+h):
  for xx in range(x,x+w):stamp('flowers',xx*16,yy*16,[5]);solid[yy,xx]=True
 for xx in range(x*16,(x+w)*16,32):stamp('fence',xx,(y*16-4 if y==21 else (y+h)*16-4),[5])
 solid[y if y==21 else y+h,x:x+w]=True
for x,y in [(37,18),(38,19),(43,13),(42,14),(49,19)]:stamp('flower02',x*16,y*16,[5])
# Five originals, keeping the sixth legacy interior in source but off this faithful town.
buildings=[dict(name='PlayerHouse',style='house',x=33,y=10,door=[34,14],warp=0),dict(name='GoldHouse',style='gold_house',x=43,y=11.5,door=[45,16],warp=1),dict(name='NeighborHouse',style='house',x=53,y=15,door=[54,19],warp=2),dict(name='Mart',style='mart',x=41,y=4,door=[42,8],warp=4),dict(name='PokemonCenter',style='center',x=49,y=3.5,door=[51,8],warp=5)]
for b in buildings:
 n=b['style'];x=int(b['x']*16);y=int(b['y']*16);obj(n,x,y,[6,7,8,9,10],(0,0,images[n].width,images[n].height-16))
 dx,dy=b['door'];solid[dy,dx]=False;solid[dy+1,dx]=False
 # Animated door warp behavior; elevation zero at the entry.
 beh[dy,dx]=0x69
obj('sign',41*16,12*16-8,[3,8,9],(0,8,16,24))
# Route openings and player spawn remain on unobstructed paths.
solid[:3,35:38]=False;solid[14:17,62:64]=False
spawn=[39,16]
# Palettes are RGBA555-expanded and every pixel is assigned a native bank/index.
paletteRGB=np.zeros((256,3),dtype=np.int32)
for b,cs in pals.items():
 for i,c in enumerate(cs,1):paletteRGB[b*16+i]=c
render=Image.fromarray(paletteRGB[canvas].astype(np.uint8));render.save(EV/'authored-overview.png')
np.savez(OUT/'scene.npz',canvas=canvas,water=watermask,solid=solid,beh=beh,palette=paletteRGB)
(ART/'layout.json').write_text(json.dumps(dict(width=W,height=H,spawn=spawn,north_exit=[35,0,3],east_exit=[63,14,3],buildings=buildings,objects=objects,tree_positions=sorted(trees),reference='gba/art/johto-v1/references/cherrygrove-hgss.png',reference_y_offset=48),indent=2)+'\n')
# GBA tile allocation: primary+secondary each 512 entries. Reserve 1..16 for live sea.
newtiles=[bytes(64)];lookup={bytes(64):0};water=asset('sea_un',[1]);water_indices=water%16
for y in range(0,32,8):
 for x in range(0,32,8):newtiles.append(bytes(water_indices[y:y+8,x:x+8].flatten()))
terrain_merges=0
def tile(data,terrain=False,covered=False):
 global terrain_merges
 raw=np.asarray(data,dtype=np.uint8).tobytes()
 if raw not in lookup and covered:
  arr=np.frombuffer(raw,dtype=np.uint8);mask=arr!=0
  for i,t in enumerate(newtiles[17:],17):
   b=np.frombuffer(t,dtype=np.uint8)
   if np.array_equal(arr[mask],b[mask]):lookup[raw]=i;break
 if raw not in lookup:
  idx=len(newtiles);newtiles.append(raw);a=np.frombuffer(raw,dtype=np.uint8).reshape(8,8)
  for v,h,bits in [(False,False,0),(False,True,1024),(True,False,2048),(True,True,3072)]:
   q=a[::-1,:] if v else a;q=q[:,::-1] if h else q;lookup.setdefault(q.tobytes(),idx|bits)
 return lookup[raw]
def waterent(x,y):return 1+(y//8%4)*4+x//8%4 | 1<<12
# Local two-palette fitting only at overlaps; source families remain exact elsewhere.
errors=[];blocks=[];attrs=[];bl={};grid=[]
def encoded_quad(a,x,y):
 bankset=sorted(set(int(v)//16 for v in a.flatten()));wm=watermask[y:y+8,x:x+8];haswater=bool(wm.any())
 if haswater:
  remaining=a[~wm];banks=sorted(set(int(v)//16 for v in remaining));base=waterent(x,y)
  if not len(remaining):return base,0
  opts=banks
  best=None
  for b in opts:
   cs=paletteRGB[remaining];ds=np.sum((cs[:,None,:]-palarr[b][None,:,:])**2,2);cost=int(ds.min(1).sum())
   if best is None or cost<best[0]:best=(cost,b,ds.argmin(1)+1)
  cost,b,ix=best;hi=np.zeros((8,8),dtype=np.uint8);hi[~wm]=ix;errors.append(cost)
  return base,tile(hi.flatten())|b<<12
 if bankset==[4]:return 0,tile((a%16).flatten())|4<<12
 if len(bankset)<=2:
  lo=bankset[0];hi=bankset[-1];return tile(np.where(a//16==lo,a%16,0).flatten(),terrain=len(bankset)==1 and lo in [0,2],covered=len(bankset)==2)|lo<<12,tile(np.where(a//16!=lo,a%16,0).flatten())|hi<<12
 best=None;cs=paletteRGB[a.flatten()]
 for bs in itertools.combinations(bankset,2):
  pp=np.concatenate([palarr[b] for b in bs]);ds=np.sum((cs[:,None,:]-pp[None,:,:])**2,2);cost=int(ds.min(1).sum())
  if best is None or cost<best[0]:best=(cost,bs,ds.argmin(1))
 cost,(lo,hi),ix=best;n=len(palarr[lo]);errors.append(cost)
 return tile(np.where(ix<n,ix+1,0),covered=True)|lo<<12,tile(np.where(ix>=n,ix-n+1,0))|hi<<12
for y in range(H):
 for x in range(W):
  entries=[encoded_quad(canvas[y*16+dy:y*16+dy+8,x*16+dx:x*16+dx+8],x*16+dx,y*16+dy) for dx,dy in [(0,0),(8,0),(0,8),(8,8)]]
  es=tuple(v[0] for v in entries)+tuple(v[1] for v in entries)
  # Only canopies occupy the foreground BG. Ground and facades stay behind people.
  hascanopy=bool(np.any(canvas[y*16:y*16+16,x*16:x*16+16]//16==4))
  at=int(beh[y,x]) | (0 if hascanopy else 0x1000);key=(es,at)
  if key not in bl:bl[key]=len(blocks);blocks.append(es);attrs.append(at)
  flags=0 if beh[y,x]==0x69 else 0x3c00 if solid[y,x] else 0x3000
  grid.append(bl[key]|flags)
assert len(newtiles)<=1008,('tile overflow; last 16 reserved for doors',len(newtiles));assert len(blocks)<=1024,('metatile overflow',len(blocks))
for part,kind in enumerate(['primary','secondary']):
 folder=G/f'data/tilesets/{kind}/cherrygrove';tiles=newtiles[part*512:(part+1)*512];tiles+= [bytes(64)]*(512-len(tiles));sheet=Image.new('P',(128,256));sheet.putpalette([v for i in range(256) for v in (i,i,i)])
 for i,t in enumerate(tiles):q=Image.new('P',(8,8));q.putdata(t);sheet.paste(q,(i%16*8,i//16*8))
 sheet.save(folder/'tiles.png')
 for b in range(16):
  cs=[(0,0,0)]+pals.get(b,[]);cs+= [(0,0,0)]*(16-len(cs));(folder/f'palettes/{b:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in cs)+'\n')
 bs=blocks[part*512:(part+1)*512];ats=attrs[part*512:(part+1)*512];bs+=[(0,)*8]*(512-len(bs));ats+=[0]*(512-len(ats))
 (folder/'metatiles.bin').write_bytes(struct.pack('<4096H',*[v for b in bs for v in b]));(folder/'metatile_attributes.bin').write_bytes(struct.pack('<512H',*ats))
(G/'data/layouts/CherrygroveCity/map.bin').write_bytes(struct.pack('<'+'H'*len(grid),*grid))
# Byte-exact decode verification of installed scene, including reported seam fitting.
from tiles import Tileset
ts=Tileset(G,'cherrygrove','cherrygrove');actual=ts.map_image(grid,W);actual.save(EV/'town-overview.png')
err=np.abs(np.array(actual).astype(int)-np.array(render).astype(int));report=dict(tiles=len(newtiles),tile_capacity=1008,door_tiles_reserved=16,terrain_grain_merges=terrain_merges,metatiles=len(blocks),metatile_capacity=1024,mean_channel_error=float(err.mean()),overlap_quantized_quadrants=sum(v>0 for v in errors),max_channel_error=int(err.max()),tree_source='HGSS tree01gs',buildings=buildings)
(EV/'integration.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
# 32-frame native sea loop. Primary animation callback uploads only reserved slots.
anim=OUT/'water';anim.mkdir(exist_ok=True)
for phase in range(32):
 a=np.roll(water_indices,phase,axis=1);data=bytes(int(t[i])|int(t[i+1])<<4 for y in range(0,32,8) for x in range(0,32,8) for t in [a[y:y+8,x:x+8].flatten()] for i in range(0,64,2));(anim/f'{phase:02}.4bpp').write_bytes(data)
