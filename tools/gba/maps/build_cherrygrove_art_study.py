#!/usr/bin/env python3
"""Reference-led native Cherrygrove study; writes only the isolated study source."""
from pathlib import Path
import json, struct, shutil, itertools, hashlib
from collections import deque
import numpy as np
from PIL import Image, ImageDraw
from tiles import Tileset
R=Path(__file__).resolve().parents[3]
G=R/'tools/vendor/gba/cherrygrove-art-study-work'
A=R/'gba/art/cherrygrove-art-study-v1'; N=A/'native'; E=A/'evidence'
W,H=66,42; OX,OY=128,96; IW,IH=800,480
ref=Image.open(A/'reference.png').convert('RGB')
small=ref.resize((IW,IH),Image.Resampling.LANCZOS)
rgb=np.asarray(small).astype(int)
rgb5=lambda c:tuple((n<<3)|(n>>2) for n in [round(int(v)*31/255) for v in c])
pals={}; assets={}
# Joint material palettes retain both warm stone and white-painted garden detail.
for bank,boxes in [(4,[(146,287,302,369),(330,145,395,207)]),(11,[(1345,183,1413,226),(1270,251,1374,351)])]:
 strip=Image.new('RGB',(sum((b[2]-b[0])*(b[3]-b[1]) for b in boxes),1));off=0
 for box in boxes:
  ar=np.array(ref.crop(box)).reshape(-1,3);strip.paste(Image.fromarray(ar[None,:,:]),(off,0));off+=len(ar)
 q=strip.quantize(colors=15,method=Image.Quantize.MEDIANCUT);cols=list(dict.fromkeys(rgb5(c) for c in q.convert('RGB').getdata()));pals[bank]=[(0,0,0)]+cols+[(0,0,0)]*(15-len(cols))

def quant(im,bank,name):
 ar=np.array(im.convert('RGBA')); alpha=ar[:,:,3]>127
 strip=Image.fromarray(ar[:,:,:3][alpha][None,:,:]); q=strip.quantize(colors=15,method=Image.Quantize.MEDIANCUT)
 cols=[rgb5(c) for c in q.convert('RGB').getdata()]; cs=list(dict.fromkeys(cols))
 if bank not in pals:pals[bank]=[(0,0,0)]+cs+[(0,0,0)]*(15-len(cs))
 pa=np.array(pals[bank][1:],int); src=ar[:,:,:3].astype(int); ix=((src[:,:,None,:]-pa)**2).sum(3).argmin(2)
 out=Image.fromarray(np.dstack((pa[ix].astype('uint8'),alpha.astype('uint8')*255)))
 out.save(N/(name+'.png'));assets[name]=(out,bank);return out
def extract(name,box,size,bank,kind='building'):
 im=ref.crop(box).convert('RGBA').resize(size,Image.Resampling.LANCZOS); ar=np.array(im); r,g,b=[ar[:,:,i].astype(int) for i in range(3)]
 if kind=='building':alpha=~((g>r*1.05)&(g>b*1.07))
 elif kind=='boat':alpha=~((b>r*1.18)&(b>g*.96))
 elif kind=='reef':alpha=(abs(b-g)<45)&(abs(b-r)<75)
 elif kind=='tree':
  yy,xx=np.indices((size[1],size[0]));alpha=(((xx-size[0]/2)/(size[0]/2))**2+((yy-15)/17)**2<=1)|((yy>=27)&(xx>=11)&(xx<=21)&(yy<39))
 else:alpha=np.ones(ar.shape[:2],bool)
 ar[:,:,3]=alpha*255;return quant(Image.fromarray(ar),bank,name)
extract('house',(806,243,947,387),(64,72),7)
extract('mart',(980,97,1113,225),(64,64),8)
extract('center',(1176,94,1318,229),(72,64),9)
im=Image.open(A/'tree-source.png').convert('RGBA');im.putalpha(im.getchannel('A').point(lambda v:255 if v>=144 else 0));im=im.crop(im.getbbox()).resize((32,40),Image.Resampling.LANCZOS);im.putalpha(im.getchannel('A').point(lambda v:255 if v>=144 else 0));quant(im,6,'tree')
extract('cargo',(397,275,450,463),(24,88),10,'boat')
extract('fishing-north',(525,301,567,386),(24,40),10,'boat')
extract('fishing-east',(526,500,637,547),(56,24),10,'boat')
extract('reef',(113,230,156,261),(16,16),5,'reef')
extract('rock-island',(146,287,302,369),(72,40),4,'boat')
extract('cliff',(330,145,395,207),(32,32),4,'solid')
extract('bench',(1345,183,1413,226),(32,24),11)
extract('garden',(1270,251,1374,351),(48,48),11,'solid')
extract('mart-sign',(1105,178,1146,222),(24,24),8)
extract('pond',(1320,64,1457,184),(64,56),12,'solid')
# Limited repeated terrain surfaces, sampled from the reference's materials.
for name,bank,colors in [('grass',0,[(175,218,111),(160,207,100),(151,197,96),(192,229,120),(128,178,88)]),('sand',1,[(242,214,153),(237,204,139),(229,195,130),(248,224,172)]),('water',2,[(32,114,175),(37,128,186),(45,139,196),(69,154,208)]),('wood',3,[(180,130,78),(200,150,93),(221,178,118),(137,93,57),(109,74,49)])]:
 pals[bank]=[(0,0,0)]+[rgb5(c) for c in colors];pals[bank]+=[pals[bank][-1]]*(16-len(pals[bank]))
 im=Image.new('RGBA',(32,32),(*pals[bank][1],255));d=ImageDraw.Draw(im)
 if name=='grass':
  for x,y in [(4,7),(19,18),(23,5),(8,25)]:d.line((x,y,x+2,y-2),fill=(*pals[bank][2],255));d.point((x+2,y-3),fill=(*pals[bank][4],255))
 elif name=='sand':
  for x,y in [(4,7),(19,18),(23,5),(8,25)]:d.line((x,y,x+1,y),fill=(*pals[bank][2],255))
 elif name=='water':
  for y in [4,20]:d.line([(0,y+3),(8,y),(16,y+3),(24,y+1),(31,y+3)],fill=(*pals[bank][3],255))
 else:
  for y in [0,8,16,24]:d.line((0,y,31,y),fill=(*pals[bank][4],255));d.line((0,y+1,31,y+1),fill=(*pals[bank][3],255))
 im.save(N/(name+'.png'));assets[name]=(im,bank)
canvas=Image.new('RGBA',(W*16,H*16)); bankmap=np.zeros((H*16,W*16),dtype='uint8'); solid=np.ones((H*16,W*16),bool);water=np.zeros_like(solid)
def stamp(name,x,y,blocked=True):
 im,bank=assets[name];canvas.alpha_composite(im,(x,y));ar=np.array(im);hh,ww=ar.shape[:2];ax0=max(0,x);ay0=max(0,y);ax1=min(W*16,x+ww);ay1=min(H*16,y+hh)
 if ax0>=ax1 or ay0>=ay1:return
 mask=ar[ay0-y:ay1-y,ax0-x:ax1-x,3]>0;view=bankmap[ay0:ay1,ax0:ax1];view[mask]=bank
 if blocked:solid[ay0:ay1,ax0:ax1][mask]=True;water[ay0:ay1,ax0:ax1][mask]=False
def floor(name,x,y):stamp(name,x,y,False)
for y in range(0,H*16,32):
 for x in range(0,W*16,32):floor('grass',x,y)
# Rich repeated ground patches sampled from the approved image.
# Repeated soft turf clusters keep grass richly shaded without embedded edges.
import math
im=Image.new('RGBA',(32,32));pa=pals[0]
for yy in range(32):
 for xx in range(32):
  v=math.sin(xx*.48)+math.cos(yy*.56)+math.sin((xx+yy)*.29);ink=1 if v>1.1 else 2 if v>-.8 else 3
  im.putpixel((xx,yy),(*pa[ink],255))
d=ImageDraw.Draw(im)
for xx,yy in [(4,8),(20,24),(27,6)]:
 d.line([(xx,yy),(xx,yy-3),(xx+1,yy)],fill=(*pa[5],255));d.point((xx+1,yy-2),fill=(*pa[4],255))
im.save(N/'grass.png');assets['grass']=(im,0)
quant(ref.crop((8,366,72,430)).resize((32,32),Image.Resampling.LANCZOS).convert('RGBA'),2,'water')
for y in range(0,H*16,32):
 for x in range(0,W*16,32):floor('grass',x,y)
# Use the reference's actual broad ground mask; classify at 8px resolution.
watermask=(rgb[:,:,2]>rgb[:,:,0]+25)&(rgb[:,:,2]>rgb[:,:,1]*1.02)
# Ocean silhouette is traced in normalized reference coordinates. Objects are
# overlaid separately, so no false grass survives below rocks or vessels.
wm=Image.new('1',(IW,IH));ImageDraw.Draw(wm).polygon([(0,102),(367,102),(342,117),(328,144),(323,192),(324,239),(345,267),(384,293),(391,480),(0,480)],fill=1);watermask=np.array(wm,dtype=bool)
sandmask=(rgb[:,:,0]>170)&(rgb[:,:,0]>rgb[:,:,1]*1.035)&(rgb[:,:,1]>rgb[:,:,2]*1.20)
forestmask=(rgb[:,:,1]>rgb[:,:,0]*1.2)&(rgb[:,:,1]>rgb[:,:,2]*1.06)&(rgb[:,:,1]<170)
for yy in range(0,IH,8):
 for xx in range(0,IW,8):
  region=np.s_[yy:yy+8,xx:xx+8];wn=watermask[region].mean();sn=sandmask[region].mean();name='water' if wn>.55 else 'sand' if sn>.55 else 'grass'
  im,bank=assets[name];piece=im.crop((xx%32,yy%32,xx%32+8,yy%32+8));canvas.alpha_composite(piece,(xx+OX,yy+OY));bankmap[yy+OY:yy+OY+8,xx+OX:xx+OX+8]=bank
  solid[yy+OY:yy+OY+8,xx+OX:xx+OX+8]=False;water[yy+OY:yy+OY+8,xx+OX:xx+OX+8]=name=='water'
# A continuous bank and pale surf edge follow the traced ocean silhouette.
from scipy.ndimage import distance_transform_edt
inside=distance_transform_edt(watermask);outside=distance_transform_edt(~watermask)
pals[2][5]=rgb5((201,234,241))
ar=np.array(canvas)
for yy,xx in zip(*np.nonzero((inside>0)&(inside<=2))):
 if yy<104:continue
 ar[yy+OY,xx+OX,:3]=pals[2][5];bankmap[yy+OY,xx+OX]=2
canvas=Image.fromarray(ar)
# Shared crowns laid on a regular grid prevent stacked or inconsistent trees.
trees=[]
for yy in range(0,IH,32):
 for xx in range(0,IW,32):
  area=forestmask[yy:min(yy+32,IH),xx:min(xx+32,IW)]
  if area.mean()>.38:trees.append((xx+OX,yy+OY))
# Padded scenery keeps the camera inside artwork; water margins remain solid.
for yy in range(0,H*16,32):
 for xx in range(0,W*16,32):
  if xx<OX or xx>=OX+IW or yy<OY or yy>=OY+IH:trees.append((xx,yy))
for x,y in sorted(set(trees),key=lambda p:(p[1],p[0])):stamp('tree',x,y)
# Reusable northern rock face follows the exact reference bank.
for x in range(OX,OX+416,32):stamp('cliff',x,OY+72)
# Wharf and accessible sandy island retain reference positions.
def rectangle(name,x,y,w,h,blocked=False):
 for yy in range(y,y+h,16):
  for xx in range(x,x+w,16):
   im,bank=assets[name];piece=im.crop((0,0,16,16));canvas.alpha_composite(piece,(xx,yy));bankmap[yy:yy+16,xx:xx+16]=bank;solid[yy:yy+16,xx:xx+16]=blocked;water[yy:yy+16,xx:xx+16]=False
rectangle('wood',OX+224,OY+192,160,32);rectangle('wood',OX+224,OY+160,32,96)
rectangle('sand',OX+200,OY+240,64,32)
extract('dock-vertical',(453,314,521,516),(32,96),3,'solid')
extract('dock-horizontal',(515,384,774,452),(128,32),3,'solid')
stamp('dock-vertical',OX+224,OY+160,False);stamp('dock-horizontal',OX+256,OY+192,False)
stamp('cargo',OX+192,OY+144);stamp('fishing-north',OX+264,OY+152);stamp('fishing-east',OX+264,OY+248)
stamp('rock-island',OX+80,OY+144);stamp('rock-island',OX+24,OY+256)
for y in range(OY+112,OY+432,16):stamp('reef',OX+56,y)
for x in range(OX+56,OX+384,16):stamp('reef',x,OY+416)
stamp('pond',OX+656,OY+32);stamp('bench',OX+664,OY+96);stamp('garden',OX+624,OY+128)
stamp('mart-sign',OX+552,OY+88)
buildings=[]
for name,style,x,y,warp,doorx in [('PlayerHouse','house',400,120,0,24),('GoldHouse','house',520,144,1,24),('NeighborHouse','house',624,200,2,24),('HarborHouse','house',496,256,6,24),('GardenHouse','house',640,272,7,24),('Mart','mart',488,48,4,32),('PokemonCenter','center',576,48,5,32)]:
 x+=OX;y+=OY;stamp(style,x,y);hh=assets[style][0].height;door=[(x+doorx)//16,(y+hh-8)//16]
 buildings.append(dict(name=name,style=style,x=x//16,y=y//16,pixel_dx=x%16,pixel_dy=y%16,door=door,warp=warp))
# Normalize each building's actual door and threshold to a native cell, keeping
# the whole facade. Each is clear for entry, surrounded by solid building cells.
flags=[];behavior=[]
for y in range(H):
 for x in range(W):
  sl=np.s_[y*16:y*16+16,x*16:x*16+16];iswater=water[sl].mean()>.5;blocked=solid[sl].mean()>.20
  flags.append(0x1400 if iswater and blocked else 0x1000 if iswater else 0x3400 if blocked else 0x3000);behavior.append(0x15 if iswater else 0)
for b in buildings:
 x,y=b['door'];flags[y*W+x]=0x3000;behavior[y*W+x]=0x69;flags[(y+1)*W+x]=0x3000
for x,y,b in [(36,6,0x64),(57,18,0x62)]:flags[y*W+x]=0x3000;behavior[y*W+x]=b
spec=dict(name='CherrygroveCity',width=W,height=H,spawn=[40,21],buildings=buildings,artwork_region=[8,6,50,30]);(A/'layout.json').write_text(json.dumps(spec,indent=2)+'\n')
# Preserve native palette ownership per pixel; each 8px area supports two banks.
arr=np.array(canvas)[:,:,:3];tiles=[bytes(64)];lookup={bytes(64):0}
def tileid(raw):
 raw=bytes(raw)
 if raw not in lookup:
  tid=len(tiles);tiles.append(raw)
  for hf,vf,bits in [(0,0,0),(1,0,1024),(0,1,2048),(1,1,3072)]:lookup.setdefault(bytes(raw[(7-y if vf else y)*8+(7-x if hf else x)] for y in range(8) for x in range(8)),tid|bits)
 return lookup[raw]
blocks=[];attrs=[];bl={};grid=[];junctions=0
pmap={b:{c:i for i,c in reversed(list(enumerate(cs))) if i} for b,cs in pals.items()}
for y in range(H):
 for x in range(W):
  low=[];high=[]
  for dx,dy in [(0,0),(8,0),(0,8),(8,8)]:
   sl=np.s_[y*16+dy:y*16+dy+8,x*16+dx:x*16+dx+8];cs=arr[sl].reshape(64,3);bm=bankmap[sl].reshape(64); banks=list(dict.fromkeys(bm.tolist()))
   if len(banks)>2:
    junctions+=1;counts=np.bincount(bm,minlength=13);banks=list(np.argsort(counts)[-2:]);colors=np.array(pals[banks[0]][1:]+pals[banks[1]][1:],int);ix=((cs[:,None,:].astype(int)-colors)**2).sum(2).argmin(1);cs=colors[ix];bm=np.where(ix<15,banks[0],banks[1]);arr[sl]=cs.reshape(8,8,3)
   a=banks[0];b=banks[-1];lo=[];hi=[]
   for c,bank in zip(cs,bm):
    c=tuple(map(int,c));lo.append(pmap[a][c] if bank==a else 0);hi.append(pmap[b][c] if bank!=a else 0)
   low.append(tileid(lo)|a<<12);high.append(tileid(hi)|b<<12)
  at=0x1000|behavior[y*W+x];key=(tuple(low+high),at)
  if key not in bl:bl[key]=len(blocks);blocks.append(key[0]);attrs.append(at)
  grid.append(bl[key]|flags[y*W+x])
print('Native patterns',len(tiles),'metatiles',len(blocks))
assert len(tiles)<=1008,('native capacity',len(tiles));assert len(blocks)<=1024
# New dedicated tilesets leave old towns and route artwork intact.
for side,start in [('primary',0),('secondary',512)]:
 folder=G/f'data/tilesets/{side}/cherry_study';(folder/'palettes').mkdir(parents=True,exist_ok=True)
 sheet=Image.new('P',(128,256));sheet.putpalette([v for c in pals[6] for v in c]+[0]*720)
 for i in range(512):
  tile=Image.new('P',(8,8));tile.putdata(tiles[start+i] if start+i<len(tiles) else bytes(64));sheet.paste(tile,(i%16*8,i//16*8))
 sheet.save(folder/'tiles.png');part=blocks[start:start+512];pat=attrs[start:start+512]
 if side=='primary':part += [(0,)*8]*(512-len(part));pat += [0x1000]*(512-len(pat))
 if not part:part=[(0,)*8];pat=[0x1000]
 (folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*b) for b in part));(folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(pat),*pat))
 for bank in range(16):
  cs=pals.get(bank,[(0,0,0)]*16);(folder/f'palettes/{bank:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in cs)+'\n')
layout=G/'data/layouts/CherrygroveCity';(layout/'map.bin').write_bytes(struct.pack('<'+'H'*len(grid),*grid));(layout/'border.bin').write_bytes(struct.pack('<4H',*[grid[y*W+x] for y in [1,2] for x in [1,2]]))
import re
for fn in ['graphics.h','metatiles.h','headers.h']:
 path=G/'src/data/tilesets'/fn;s=(R/'tools/vendor/gba/johto-restart-game/src/data/tilesets'/fn).read_text();chunks=[]
 for match in re.finditer(r'const [^;]+(?:CherrygrovePrimary|Cherrygrove)[^;]+;',s):
  chunk=match.group(0)
  if 'gTileset' in chunk or 'gMetatile' in chunk:chunks.append(chunk.replace('CherrygrovePrimary','CherryStudyPrimary').replace('Cherrygrove','CherryStudy').replace('/cherrygrove/','/cherry_study/').replace('InitTilesetAnim_General','NULL'))
 path.write_text(s+'\n'+'\n'.join(chunks)+'\n')
p=G/'data/layouts/layouts.json';data=json.loads(p.read_text());row=next(v for v in data['layouts'] if v['id']=='LAYOUT_CHERRYGROVE_CITY');row.update(width=W,height=H,primary_tileset='gTileset_CherryStudyPrimary',secondary_tileset='gTileset_CherryStudy');p.write_text(json.dumps(data,indent=2)+'\n')
# Warp IDs retained, so all original interiors return through their matching door.
p=G/'data/maps/CherrygroveCity/map.json';data=json.loads(p.read_text());data['connections']=[]
for b in buildings:data['warp_events'][b['warp']].update(x=b['door'][0],y=b['door'][1])
data['warp_events'][3].update(x=2,y=2)
data['warp_events']=data['warp_events'][:8]+[dict(x=36,y=6,elevation=0,dest_map='MAP_CHERRYGROVE_ROUTE30_APPROACH',dest_warp_id='3'),dict(x=57,y=18,elevation=0,dest_map='MAP_CHERRYGROVE_ROUTE29_APPROACH',dest_warp_id='2')]
occupied=set()
for i,event in enumerate(data['object_events']):
 positions=[(40,20),(40,14),(42,28),(48,29),(38,21),(50,23),(35,20),(45,17),(50,18),(37,14),(34,23),(45,28)]
 event['x'],event['y']=positions[i];event['movement_type']='MOVEMENT_TYPE_WALK_LEFT_AND_RIGHT';event['movement_range_x']=1;event['movement_range_y']=0
 # Move a proposed walker to a clear three-cell row if scenery occupies it.
 choices=[(x,y) for y in range(12,H-7) for x in range(25,W-8) if all(grid[y*W+xx]>>12==3 and not grid[y*W+xx]&0xc00 and behavior[y*W+xx]!=0x69 and (xx,y) not in occupied for xx in [x-1,x,x+1])]
 event['x'],event['y']=min(choices,key=lambda q:abs(q[0]-event['x'])+abs(q[1]-event['y']))
 occupied.update((xx,event['y']) for xx in [event['x']-1,event['x'],event['x']+1])
data['bg_events']=[];p.write_text(json.dumps(data,indent=2)+'\n')
decoded=Tileset(G,'cherry_study','cherry_study').map_image(grid,W);assert np.array_equal(np.array(decoded),arr);decoded.save(E/'town-overview.png');decoded.crop((OX,OY,OX+IW,OY+IH)).save(E/'artwork-area.png')
(E/'integration.json').write_text(json.dumps(dict(native_tiles=len(tiles),metatiles=len(blocks),palettes=13,exact_native_roundtrip=True,palette_junctions_reduced=junctions,reference_size=list(ref.size),native_artwork_size=[IW,IH],map_size=[W,H],buildings=buildings),indent=2)+'\n')
