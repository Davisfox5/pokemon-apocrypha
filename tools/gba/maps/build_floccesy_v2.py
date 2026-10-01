#!/usr/bin/env python3
"""Compile approved Floccesy art into editable 4bpp tiles and native metatiles.
Never runs an emulator. Preserves other maps, and refuses unknown owner changes.
"""
from pathlib import Path
from collections import deque
import json,struct,hashlib,math,random,shutil
import numpy as np
from PIL import Image,ImageDraw
from tiles import Tileset
R=Path(__file__).resolve().parents[3];G=R/'tools/vendor/gba/johto-restart-game';A=R/'gba/art/floccesy-v2';B=R/'tools/vendor/gba/johto-before-floccesy-v2-20260924';N=A/'native';E=A/'evidence'
W,H=56,78
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
state=E/'authored-state.json';old=G/'data/layouts/FloccesyTown/map.bin'
allowed={sha(B/'data/layouts/FloccesyTown/map.bin')}
if state.exists():allowed.add(json.loads(state.read_text())['map_sha256'])
assert sha(old) in allowed,'Preserve new owner edits before rebuilding.'
def rgb5(c):return tuple((n<<3)|(n>>2) for n in [round(v*31/255) for v in c])
pals={};sources={}
def prepare(name,size,bank,path=None):
 im=Image.open(path or A/f'generated/{name}.png').convert('RGBA');im.putalpha(im.getchannel('A').point(lambda a:255 if a>=144 else 0));im=im.crop(im.getbbox());im=im.resize(size,Image.Resampling.LANCZOS)
 alpha=np.array(im)[:,:,3]>=144
 # Quantization uses only opaque pixels, excluding the transparent matte.
 a=np.array(im);strip=Image.fromarray(a[:,:,:3][alpha][None,:,:]);q=strip.quantize(colors=15,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE);pal=q.getpalette();cs=list(dict.fromkeys(rgb5(tuple(pal[i*3:i*3+3])) for i in sorted(set(q.getdata()))));cs=[rgb5(tuple(int(.48*c[j]+.52*(157,195,111)[j]) for j in range(3))) for c in cs] if name=='grass' else cs;pals[bank]=[(0,0,0)]+cs+[(0,0,0)]*(15-len(cs));ca=np.array(cs,dtype=int);a[:,:,:3]=(.48*a[:,:,:3]+.52*np.array([157,195,111])).astype('uint8') if name=='grass' else a[:,:,:3];ix=((a[:,:,:3,None].transpose(0,1,3,2).astype(int)-ca)**2).sum(3).argmin(2);out=ca[ix].astype('uint8');rgba=np.dstack((out,alpha.astype('uint8')*255));im=Image.fromarray(rgba);im.save(N/f'{name}.png');sources[name]=im
for args in [('tree',(32,40),6),('house',(80,96),7),('alder',(80,80),8),('center',(96,96),9),('tower',(64,96),10),('shed',(80,96),11)]:prepare(*args)
# Terrain palettes are independently budgeted instead of sharing fifteen colors.
prepare('grass',(32,32),0)
pals[1]=[(0,0,0)]+list(map(rgb5,[(233,213,155),(240,223,170),(223,199,135),(213,184,118),(246,231,184),(204,170,103),(233,207,145),(225,193,125),(245,225,168),(207,178,111),(234,217,159),(218,191,128),(199,166,97),(242,218,156),(249,236,194)]))
pals[2]=[(0,0,0)]+list(map(rgb5,[(120,122,119),(125,127,123),(116,119,116),(129,131,127),(160,162,151),(197,196,178),(214,211,190),(101,105,102),(148,151,144),(178,178,164),(184,171,145),(151,133,108),(219,207,180),(114,112,103),(135,137,132)]))
pals[3]=[(0,0,0)]+list(map(rgb5,[(197,151,104),(204,159,113),(211,166,119),(188,141,95),(177,129,85),(226,184,139),(168,123,84),(233,195,153),(190,144,100),(203,155,106),(214,173,130),(151,112,79),(236,205,167),(177,142,105),(222,185,146)]))
pals[4]=[(0,0,0)]+list(map(rgb5,[(124,115,92),(153,140,115),(186,174,145),(217,208,178),(99,99,80),(169,151,120),(225,217,187),(141,122,96),(185,153,112),(208,185,139),(111,99,77),(147,131,99),(167,159,127),(201,196,165),(232,224,196)]))
pals[5]=[(0,0,0)]+list(map(rgb5,[(242,240,208),(255,251,230),(235,196,122),(200,125,135),(247,191,191),(74,124,58),(99,157,72),(126,180,74),(156,199,83),(178,216,106),(56,99,53),(103,135,59),(221,201,114),(174,102,75),(200,164,111)]))
pals[12]=pals[3][:]
# Native terrain patterns. Small repeatable patches bound VRAM use.
def patch(name,bank,fn):
 im=Image.new('RGBA',(16,16));im.putdata([(*pals[bank][fn(x,y)],255) for y in range(16) for x in range(16)]);sources[name]=im;im.save(N/f'{name}.png')
rng=random.Random(731);dirt_values=[rng.choices([1,2,3,7],[78,10,5,7])[0] for _ in range(256)]
patch('dirt',1,lambda x,y:dirt_values[y*16+x])
patch('road',2,lambda x,y:1 if (x*17+y*11)%23>2 else 2 if x%2 else 3)
patch('paving',3,lambda x,y:7 if y%8==7 or (x+(8 if y//8 else 0))%16==15 else 6 if y%8==0 else 4 if y%8==6 else 1 if y<8 else 2)
canvas=Image.new('RGBA',(W*16,H*16));grass=sources['grass']
for y in range(0,H*16,32):
 for x in range(0,W*16,32):canvas.paste(grass,(x,y))
flags=[0x3000]*(W*H);behavior=[0]*(W*H);objects=[];buildings=[]
def tile(name,x,y,solid=False):
 if 0<=x<W and 0<=y<H:canvas.alpha_composite(sources[name],(x*16,y*16));flags[y*W+x]=0x3c00 if solid else 0x3000
def rect(name,x,y,w,h,solid=False):
 for yy in range(y,y+h):
  for xx in range(x,x+w):tile(name,xx,yy,solid)
def obj(name,x,y,dx=0,solid=True):
 im=sources[name];gx=x*16+dx;gy=y*16;canvas.alpha_composite(im,(gx,gy));alpha=np.array(im)[:,:,3]
 for yy in range(im.height):
  for xx in range(im.width):
   if alpha[yy,xx] and 0<=gx+xx<W*16 and 0<=gy+yy<H*16 and solid:flags[((gy+yy)//16)*W+(gx+xx)//16]=0x3c00
 objects.append(dict(name=name,x=x,y=y,pixel_dx=dx,width=im.width,height=im.height))
# Road layout/warp endpoints retained, architecture gets the scale of the approved art.
road=set()
def lane(x,y,w,h):road.update((xx,yy) for yy in range(y,y+h) for xx in range(x,x+w))
lane(9,66,38,3);lane(29,39,3,29);lane(13,54,34,3)
for x,y in road:tile('road',x,y)
rect('paving',14,42,14,12);rect('paving',14,57,14,9);rect('paving',34,57,13,9)
# Paint curbs as reusable native tile shapes, leaving the middle of crossings open.
for x,y in road:
 im=canvas.crop((x*16,y*16,x*16+16,y*16+16));d=ImageDraw.Draw(im)
 for side,missing in [('w',(x-1,y) not in road),('e',(x+1,y) not in road),('n',(x,y-1) not in road),('s',(x,y+1) not in road)]:
  if not missing:continue
  lines={'w':[(0,0,0,15),(1,0,1,15)],'e':[(15,0,15,15),(14,0,14,15)],'n':[(0,0,15,0),(0,1,15,1)],'s':[(0,15,15,15),(0,14,15,14)]}[side]
  for k,line in enumerate(lines):d.line(line,fill=(*pals[2][6 if k==0 else 8],255))
 canvas.paste(im,(x*16,y*16))
# Garden uses raised masonry rather than a wall of impassable flower tiles.
for y in range(43,52):
 for x in range(16,26):canvas.paste(grass.crop((x%2*16,y%2*16,x%2*16+16,y%2*16+16)),(x*16,y*16))
patch('wall',4,lambda x,y:5 if y in (6,15) or (x+(8 if y<7 else 0))%16==15 else 4 if y in (0,7) else 3 if y in (1,8) else 2)
rect('wall',15,42,12,1,True);rect('wall',15,52,5,1,True);rect('wall',22,52,5,1,True);rect('wall',15,43,1,9,True);rect('wall',26,43,1,9,True)
obj('tower',19,44)
# Reuse a real approved bench, quantized to the paving/wood bank.
im=Image.open(R/'gba/art/johto-restart/native/park-bench.png').convert('RGBA').resize((48,24),Image.Resampling.LANCZOS);a=np.array(im);cs=np.array(pals[3][1:]);ix=((a[:,:,:3,None].transpose(0,1,3,2).astype(int)-cs)**2).sum(3).argmin(2);sources['bench']=Image.fromarray(np.dstack((cs[ix].astype('uint8'),(a[:,:,3]>=144).astype('uint8')*255)));sources['bench'].save(N/'bench.png');obj('bench',40,44)
# Natural path joins; clipped grass tufts soften their cell boundaries.
dirt=set()
def dl(x,y,w,h):dirt.update((xx,yy) for yy in range(y,y+h) for xx in range(x,x+w))
dl(29,27,3,13);dl(30,28,17,3);dl(17,29,8,9);dl(18,25,2,5)
for yy,xx in [(46,40),(47,39),(48,38),(49,38),(50,37),(51,36)]:dl(xx,yy,3,2)
for x,y in dirt:
 tile('dirt',x,y)
 im=canvas.crop((x*16,y*16,x*16+16,y*16+16));p=im.load();gp=grass.load()
 for yy in range(16):
  for xx in range(16):
   edge=((x-1,y) not in dirt and xx<1+(yy*7%3)) or ((x+1,y) not in dirt and xx>14-(yy*7%3)) or ((x,y-1) not in dirt and yy<1+(xx*5%3)) or ((x,y+1) not in dirt and yy>14-(xx*5%3))
   if edge:p[xx,yy]=gp[(x*16+xx)%32,(y*16+yy)%32]
 canvas.paste(im,(x*16,y*16))
# Fences, court, shallow steps and flowers are reusable palette-indexed props.
fence=Image.new('RGBA',(16,16));d=ImageDraw.Draw(fence);d.rectangle((0,5,15,7),fill=(*pals[4][3],255));d.rectangle((0,8,15,9),fill=(*pals[4][1],255));d.rectangle((6,1,9,14),fill=(*pals[4][2],255));d.line((6,1,9,1),fill=(*pals[4][4],255));sources['fence']=fence
for x in range(16,26):tile('fence',x,28,True)
for y in range(29,38):tile('fence',16,y,True);tile('fence',25,y,True)
for y in range(31,37):
 for x in range(18,24):
  im=sources['dirt'].copy();p=im.load()
  for yy in range(16):
   for xx in range(16):
    u=(x-18)*16+xx;v=(y-31)*16+yy;r=(u-47.5)**2+(v-47.5)**2
    if u in (1,94,47) or v in (1,94) or 20**2<=r<=21**2:p[xx,yy]=(*pals[1][6],255)
  canvas.paste(im,(x*16,y*16))
patch('steps',4,lambda x,y:5 if y%5==4 else 4 if y%5==0 else 3)
for y in range(39,41):rect('steps',29,y,3,1)
rect('steps',20,52,2,1)
for name,style,x,y,door,dx in [('PokemonCenter','center',15,57,[18,62],10),('HouseWest','house',34,57,[36,62],0),('HouseEast','house',40,57,[42,62],0),('Lodge','alder',17,21,[19,25],1),('ShedWest','shed',29,21,[31,26],1),('ShedEast','shed',35,21,[37,26],1)]:
 obj(style,x,y,dx);buildings.append(dict(name=name,style=style,x=x,y=y,door=door,pixel_dx=dx,interior='Floccesy'+name))
 xx,yy=door;flags[yy*W+xx]=0;behavior[yy*W+xx]=0x69
# Full round crowns are drawn once each in consistent rows.
trees=[]
for y in range(-1,H,2):
 for x in range(0,W,2):
  west=x<12 and not(y in (65,67) and x>=8);east=x>=48;bottom=y>=69;top=y<19
  if top and 26<=x<38 and 9<=y<15:top=False
  if top and x in (26,28) and 13<=y<19:top=False
  strip=y==41 and 12<=x<28;northeast=34<=x<48 and 33<=y<41
  if west or east or bottom or top or strip or northeast:trees.append((x,y))
for x,y in sorted(trees,key=lambda t:(t[1],t[0])):obj('tree',x,y)
# Existing authored rock texture supplies the western escarpment's masonry.
cliff=Image.open(R/'gba/art/johto-restart/native/cliff.png').convert('RGBA').crop((48,8,80,40));aa=np.array(cliff);cs=np.array(pals[4][1:]);ix=((aa[:,:,:3,None].transpose(0,1,3,2).astype(int)-cs)**2).sum(3).argmin(2);cliff=Image.fromarray(np.dstack((cs[ix].astype('uint8'),np.full((32,32),255,dtype='uint8'))));sources['cliff']=cliff;cliff.save(N/'cliff.png')
for yy in range(0,64,2):obj('cliff',6,yy)
# The bank ends with a solid foot at the southwest bend, outside the travel lane.
rect('wall',6,64,2,1,True)
flower=Image.new('RGBA',(16,16));d=ImageDraw.Draw(flower)
for x,y in [(5,6),(10,11)]:
 d.line((x,y+1,x,y+5),fill=(*pals[5][6],255));d.rectangle((x-2,y-1,x+2,y+1),fill=(*pals[5][1],255));d.rectangle((x-1,y-2,x+1,y+2),fill=(*pals[5][2],255));d.point((x,y),fill=(*pals[5][3],255))
sources['flowers']=flower;flower.save(N/'flowers.png')
for x,y in [(17,44),(24,44),(17,47),(24,47),(17,50),(24,50),(39,44),(43,45),(44,48),(35,51),(43,52),(13,62),(13,63),(27,25),(27,26)]:
 if flags[y*W+x]&0xc00==0:tile('flowers',x,y)
for y in range(28,31):tile('fence',46,y,True)
for y in range(66,69):flags[y*W+9]=0x3000;behavior[y*W+9]=0x63
spec=dict(name='FloccesyTown',width=W,height=H,spawn=[30,62],buildings=buildings,trees=trees,objects=objects,west_warp_x=9,west_warp_y=[66,67,68]);(A/'layout.json').write_text(json.dumps(spec,indent=2)+'\n')
# Compile every pixel to one or two hardware palette banks per 8x8 quad.
pmap={b:{c:i for i,c in reversed(list(enumerate(cs))) if i} for b,cs in pals.items()};pset={b:set(cs) for b,cs in pmap.items()}
tiles=[bytes(64)];lookup={bytes(64):0}
def tileid(raw):
 raw=bytes(raw)
 if raw not in lookup:
  tid=len(tiles);assert tid<1008,('tile capacity exceeded',tid);tiles.append(raw)
  for hf,vf,bits in [(0,0,0),(1,0,1024),(0,1,2048),(1,1,3072)]:lookup.setdefault(bytes(raw[(7-y if vf else y)*8+(7-x if hf else x)] for y in range(8) for x in range(8)),tid|bits)
 return lookup[raw]
import itertools
blocks=[];attrs=[];bl={};grid=[];arr=np.array(canvas)[:,:,:3];unmapped=[]
for y in range(H):
 for x in range(W):
  low=[];high=[]
  for dx,dy in [(0,0),(8,0),(0,8),(8,8)]:
   cs=[tuple(map(int,c)) for c in arr[y*16+dy:y*16+dy+8,x*16+dx:x*16+dx+8].reshape(-1,3)];used=set(cs);choices=[(b,b) for b in range(13) if used<=pset[b]]
   if not choices:choices=[(a,b) for a,b in itertools.combinations(range(13),2) if used<=pset[a]|pset[b]]
   if not choices:
    original=np.array(cs,dtype=int);best=None
    candidates=[b for b in range(13) if used & pset[b]]
    for aa,bb in itertools.combinations(candidates,2):
     palette=np.array(list(pset[aa]|pset[bb]),dtype=int);dist=((original[:,None,:]-palette[None,:,:])**2).sum(2);ix=dist.argmin(1);err=dist[np.arange(64),ix].sum()
     if best is None or err<best[0]:best=(err,aa,bb,palette[ix])
    error,aa,bb,recolored=best;unmapped.append(dict(x=x,y=y,quadrant=[dx,dy],squared_error=int(error)));cs=[tuple(map(int,c)) for c in recolored];arr[y*16+dy:y*16+dy+8,x*16+dx:x*16+dx+8]=recolored.reshape(8,8,3);choices=[(aa,bb)]
   def pair(a,b):return bytes(pmap[a].get(c,0) for c in cs),bytes(0 if c in pmap[a] else pmap[b][c] for c in cs)
   a,b=min(choices,key=lambda ab:sum(r not in lookup for r in pair(*ab)));lo,hi=pair(a,b);low.append(tileid(lo)|a<<12);high.append(tileid(hi)|b<<12)
  ent=tuple(low+high);at=0x1000|behavior[y*W+x];key=(ent,at)
  if key not in bl:bl[key]=len(blocks);blocks.append(ent);attrs.append(at)
  assert len(blocks)<=1024,'Metatile capacity exceeded';grid.append(bl[key]|flags[y*W+x])
# Both banks are owned solely by Floccesy; callback disabled (no animated terrain).
for side,start in [('primary',0),('secondary',512)]:
 folder=G/f'data/tilesets/{side}/floccesy';sheet=Image.new('P',(128,256));sheet.putpalette([v for c in pals[6] for v in c]+[0]*720)
 for i in range(512):
  tile=Image.new('P',(8,8));tile.putdata(tiles[start+i] if start+i<len(tiles) else bytes(64));sheet.paste(tile,(i%16*8,i//16*8))
 sheet.save(folder/'tiles.png');shutil.copy2(folder/'tiles.png',N/f'{side}-tiles.png')
 part=blocks[start:start+512];pat=attrs[start:start+512]
 if side=='secondary' and not part:part=[(0,)*8];pat=[0x1000]
 if side=='primary':part+= [(0,)*8]*(512-len(part));pat+=[0x1000]*(512-len(pat))
 (folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*b) for b in part));(folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(pat),*pat))
 for bank in range(16):
  cs=pals.get(bank,[(0,0,0)]*16);txt='JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in cs)+'\n';(folder/f'palettes/{bank:02}.pal').write_text(txt)
  if bank<13:(N/f'{bank:02}.pal').write_text(txt)
layout=G/'data/layouts/FloccesyTown';(layout/'map.bin').write_bytes(struct.pack('<'+'H'*len(grid),*grid));(layout/'border.bin').write_bytes(struct.pack('<4H',*[grid[y*W+x] for y in [1,2] for x in [2,3]]))
f=G/'src/data/tilesets/headers.h';s=f.read_text();a=s.index('const struct Tileset gTileset_FloccesyPrimary');b=s.index('};',a);chunk=s[a:b].replace('InitTilesetAnim_General','NULL');s=s[:a]+chunk+s[b:];f.write_text(s)
installed=Tileset(G,'floccesy','floccesy');decoded=installed.map_image(grid,W);assert np.array_equal(np.array(decoded),arr),'Hardware roundtrip mismatch';decoded.save(E/'town-overview.png')
installed.sheet(E/'metatile-sheet.png')
# Save a colorized 8x8 tile atlas; raw indexed source sheets remain separate.
report=dict(native_tiles=len(tiles),tile_capacity=1008,metatiles=len(blocks),metatile_capacity=1024,palettes=13,colors_per_palette=15,exact_scene_roundtrip=True,all_layers_below_characters=True,no_emulator_run=True,palette_junction_quads=len(unmapped))
(E/'integration.json').write_text(json.dumps(report,indent=2)+'\n');state.write_text(json.dumps(dict(map_sha256=sha(layout/'map.bin')),indent=2)+'\n');print(report)
