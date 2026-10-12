#!/usr/bin/env python3
"""Scoped, lossless native-tile material pass. Never changes exploration data."""
from pathlib import Path
from collections import Counter
import struct, json, hashlib, itertools, sys, math
import numpy as np
from PIL import Image
from tiles import Tileset
R=Path(__file__).resolve().parents[3]
B=R/'tools/vendor/gba/floccesy-detailed-work'
baseline='--baseline' in sys.argv
G=R/('tools/vendor/gba/floccesy-clock-baseline-work' if baseline else 'tools/vendor/gba/floccesy-clock-sample-work')
A=R/'gba/art/floccesy-clock-sample';E=A/('baseline-evidence' if baseline else 'evidence');E.mkdir(parents=True,exist_ok=True)
t=Tileset(B,'floccesy','floccesy');raw=[bytes(v) for side in t.tiles for v in side]
blocks=t.blocks[0]+t.blocks[1];attrs=t.attrs[0]+t.attrs[1]
oldgrid=list(struct.unpack('<4368H',(B/'data/layouts/FloccesyTown/map.bin').read_bytes()))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
state=E/'authored-state.json';allowed={sha(B/'data/layouts/FloccesyTown/map.bin')}
if state.exists():allowed.add(json.loads(state.read_text())['map_sha256'])
assert sha(G/'data/layouts/FloccesyTown/map.bin') in allowed,'Unknown edits in sample; preserve before rebuilding'
pals=[t.pals[b>=6][b][:] for b in range(16)]
assert all(e>>12!=12 for n in oldgrid for e in blocks[n&1023] if e&1023),'Palette 12 already in use'
rgb5=lambda c:tuple((round(v*31/255)<<3)|(round(v*31/255)>>2) for v in c)
pals[12]=[(0,0,0)]+[rgb5(c) for c in [(143,186,109),(149,192,113),(139,183,106),(155,196,119),(132,177,102),(125,169,96),(114,157,90),(107,150,86),(97,139,81),(85,127,76),(164,202,125),(117,164,93),(151,188,110),(137,181,104),(147,190,111)]]
pals[10]=t.pals[1][10][:] if baseline else [(0,0,0)]+[rgb5(c) for c in [(231,225,211),(205,195,174),(183,174,150),(165,158,136),(155,153,205),(155,146,125),(139,132,117),(132,125,146),(117,110,136),(112,110,158),(102,96,112),(89,84,121),(76,73,107),(65,62,83),(49,47,66)]]
before=t.map_image(oldgrid,56);scene=np.asarray(before).copy();bankmap=np.full((1248,896),-1,dtype=np.int8);indexmap=np.zeros((1248,896),dtype=np.uint8)
for i,n in enumerate(oldgrid):
 x=i%56*16;y=i//56*16
 for j,e in enumerate(blocks[n&1023]):
  ar=np.frombuffer(raw[e&1023],dtype=np.uint8).reshape(8,8)
  if e&1024:ar=ar[:,::-1]
  if e&2048:ar=ar[::-1]
  dx=(j%4%2)*8;dy=(j%4//2)*8
  bm=bankmap[y+dy:y+dy+8,x+dx:x+dx+8];bm[ar!=0]=e>>12;ix=indexmap[y+dy:y+dy+8,x+dx:x+dx+8];ix[ar!=0]=ar[ar!=0]
# v4 used banks 13-15, but this engine loads only 0-12. Normalize those
# references before comparing the scoped sample. No geometry changes.
for bank in (13,14,15):
 for idx,color in enumerate(t.pals[1][bank]):
  mask=(bankmap==bank)&(indexmap==idx)
  if not np.any(mask):continue
  if bank in (13,14):replacement=pals[6][idx]
  else:
   candidates=pals[6][1:]+pals[2][1:]
   replacement=min(candidates,key=lambda c:sum((int(a)-int(b))**2 for a,b in zip(c,color)))
  scene[mask]=replacement
normalized=scene.copy()
# Lawn: restrained color clusters and a shaded edge, replacing repeated V marks.
for yy in range(42*16,42*16 if baseline else 54*16):
 for xx in range(14*16,32*16):
  x,y=xx//16,yy//16;u,v=xx%16,yy%16;b=int(bankmap[yy,xx])
  if b==0 and 16<=x<=25 and 43<=y<=51:
   # Broad, low-contrast turf clusters; short leaf accents sit inside them.
   value=math.sin(u*.46)+math.cos(v*.52)+math.sin((u+v)*.31)
   ink=3 if value<-.9 else 2 if value>1.1 else 1
   if (u,v) in [(3,8),(4,8),(4,9),(9,3),(10,3),(11,4),(12,12),(13,12)]:ink=5
   if (u,v) in [(3,7),(9,2),(12,11)]:ink=4
   if (u,v) in [(6,13),(7,12),(7,13),(2,2)]:ink=11
   if x==16 and u<3:ink=7 if u<2 else 5
   if x==25 and u>13:ink=5
   # A short tapered contact shadow remains entirely on walkable lawn.
   limit={47:3,48:5,49:7,50:6}.get(y,0)
   if x==24 and u<limit:ink=7 if u<limit-2 else 5
   if y==51 and 20<=x<=24 and v<4 and (x<24 or u<6):ink=7 if v<2 else 5
   scene[yy,xx]=pals[12][ink]
  elif b==10:
   scene[yy,xx]=pals[10][t.pals[1][10].index(tuple(map(int,scene[yy,xx]))) ]
  elif b==3:
   # Dressed warm pavers, with narrow joints and a lit upper edge.
   ux=(u+(8 if v>=8 else 0))%16;vy=v%8
   ink=12 if vy==7 or ux==15 else 7 if vy==6 or ux==14 else 13 if vy==0 else 6 if ux==0 else 2
   if vy in (2,3) and ux in (4,5):ink=3
   scene[yy,xx]=pals[3][ink]
  elif b==4 and (x in (15,26) or y==52) and not (y==52 and x in (20,21)):
   # The existing solid garden wall receives a coping course and shaded face.
   ink=4 if v==0 else 7 if v==1 else 3 if v<5 else 1 if v==5 else 5 if v==15 else 2
   if v>=6 and (u+(8 if v>=11 else 0))%16==15:ink=5
   elif v in (6,11):ink=6
   elif (u,v) in [(3,8),(4,8),(10,13)]:ink=3
   scene[yy,xx]=pals[4][ink]
  elif b==2 and 29<=x<=31:
   ink=1 if (u*17+v*11)%23>2 else 2 if u%2 else 3
   edge=u if x==29 else 15-u if x==31 else 99
   if edge<4:ink=13 if edge==0 else 7 if edge<3 else 6
   elif edge<6:ink=8
   if edge<4 and v==15:ink=11
   scene[yy,xx]=pals[2][ink]
# Rework only existing flower-cell footprints into low, shaded flowering plants.
for y in range(44,44 if baseline else 52):
 for x in (17,18,23,24):
  area=bankmap[y*16:y*16+16,x*16:x*16+16]
  if not np.any(area==5):continue
  # Existing two-color flowers receive leaf clusters and shaded petals.
  for cx,cy in ((5,6),(11,10)):
   for dx,dy,ink in [(-2,3,11),(-1,3,6),(0,3,6),(1,3,11),(-3,2,6),(-2,2,7),(-1,2,9),(1,2,7),(2,2,8),(3,1,7),(0,1,6)]:
    scene[y*16+cy+dy,x*16+cx+dx]=pals[5][ink]
   for dx,dy,ink in [(-1,0,4),(0,-1,1),(1,0,1),(0,1,5),(0,0,3)]:
    scene[y*16+cy+dy,x*16+cx+dx]=pals[5][ink]
# Lossless storage optimization: lower-layer pixels hidden by an opaque upper
# layer do not need their own cropped tile. Reuse common existing patterns.
freq=Counter(e&1023 for n in oldgrid for e in blocks[n&1023])
candidates=[];refs=[]
for tid in sorted(range(1008),key=lambda i:-freq[i]):
 for flip in (0,1024,2048,3072):
  ar=np.frombuffer(raw[tid],dtype=np.uint8).reshape(8,8)
  ar=ar[:,::-1] if flip&1024 else ar;ar=ar[::-1] if flip&2048 else ar
  candidates.append(ar.ravel());refs.append(tid|flip)
candidates=np.asarray(candidates);optimized_entries=0
for mid in set(n&1023 for n in oldgrid):
 block=list(blocks[mid])
 def raster(e):
  ar=np.frombuffer(raw[e&1023],dtype=np.uint8).reshape(8,8)
  ar=ar[:,::-1] if e&1024 else ar;ar=ar[::-1] if e&2048 else ar
  return ar.ravel()
 for q in range(4):
  low,high=block[q],block[q+4];mask=raster(high)==0
  if mask.all():continue
  target=raster(low);matches=np.flatnonzero(np.all(candidates[:,mask]==target[mask],axis=1))
  if len(matches):
   entry=refs[matches[0]]|(low&0xf000)
   if entry!=low:optimized_entries+=1;block[q]=entry
 blocks[mid]=tuple(block)
# Compile only changed quads, reusing exact existing patterns and hardware flips.
lookup={}
def register(data,tid):
 ar=np.frombuffer(data,dtype=np.uint8).reshape(8,8)
 for flip in (0,1024,2048,3072):
  a=ar[:,::-1] if flip&1024 else ar
  a=a[::-1] if flip&2048 else a
  lookup.setdefault(a.tobytes(),(tid,flip))
for i,d in enumerate(raw[:1008]):register(d,i)
newraw=[]
def intern(data):
 if data in lookup:return lookup[data]
 tid=1024+len(newraw);newraw.append(data);register(data,tid);return (tid,0)
sets=[set(p[1:])|{(0,0,0)} for p in pals];maps=[{c:i for i,c in reversed(list(enumerate(p))) if i} for p in pals]
newblocks={};changes={}
for y in range(78):
 for x in range(56):
  mid=oldgrid[y*56+x]&1023;old=blocks[mid];out=[(e&1023,e&3072,e>>12) for e in old]
  for q,(dx,dy) in enumerate([(0,0),(8,0),(0,8),(8,8)]):
   pixels=scene[y*16+dy:y*16+dy+8,x*16+dx:x*16+dx+8]
   if np.array_equal(pixels,np.asarray(before)[y*16+dy:y*16+dy+8,x*16+dx:x*16+dx+8]):continue
   cs=[tuple(map(int,c)) for c in pixels.reshape(-1,3)];used=set(cs)
   choices=[(b,b) for b in range(13) if used<=sets[b]]
   if not choices:choices=[(a,b) for a,b in itertools.combinations(range(13),2) if used<=sets[a]|sets[b]]
   assert choices,('more than two palettes',x,y,q,used)
   aa,bb=choices[0];low=bytes(maps[aa].get(c,0) for c in cs);high=bytes(maps[bb].get(c,0) if c not in sets[aa] else 0 for c in cs)
   out[q]=(*intern(low),aa);out[q+4]=(*intern(high),bb)
  if out!=[(e&1023,e&3072,e>>12) for e in old]:changes[(x,y)]=(mid,out)
used=set()
for i,n in enumerate(oldgrid):
 x,y=i%56,i//56
 entries=changes[(x,y)][1] if (x,y) in changes else [(e&1023,e&3072,e>>12) for e in blocks[n&1023]]
 used.update(e[0] for e in entries)
border=struct.unpack('<4H',(B/'data/layouts/FloccesyTown/border.bin').read_bytes())
for n in border:used.update(e&1023 for e in blocks[n&1023])
free=sorted(set(range(1,1008))-used)
assert len(newraw)<=len(free),('native capacity exceeded',len(newraw),len(free))
remap={1024+i:tid for i,tid in enumerate(free[:len(newraw)])}
for i,data in enumerate(newraw):raw[remap[1024+i]]=data
finalblocks=blocks[:];finalattrs=attrs[:];grid=oldgrid[:];cache={}
for (x,y),(mid,entries) in changes.items():
 block=tuple(remap.get(tid,tid)|flip|(bank<<12) for tid,flip,bank in entries)
 key=(block,attrs[mid])
 if key not in cache:
  cache[key]=len(finalblocks);finalblocks.append(block);finalattrs.append(attrs[mid])
 grid[y*56+x]=(oldgrid[y*56+x]&0xfc00)|cache[key]
assert len(finalblocks)<=1024,len(finalblocks)
for side,start in [('primary',0),('secondary',512)]:
 folder=G/f'data/tilesets/{side}/floccesy';sheet=Image.open(B/f'data/tilesets/{side}/floccesy/tiles.png').copy()
 for i in range(512):
  im=Image.new('P',(8,8));im.putdata(raw[start+i]);sheet.paste(im,(i%16*8,i//16*8))
 sheet.save(folder/'tiles.png')
 part=finalblocks[start:start+512];at=finalattrs[start:start+512]
 (folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*b) for b in part))
 (folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(at),*at))
 (folder/'palettes/10.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pals[10])+'\n')
 (folder/'palettes/12.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pals[12])+'\n')
(G/'data/layouts/FloccesyTown/map.bin').write_bytes(struct.pack('<4368H',*grid))
installed=Tileset(G,'floccesy','floccesy');after=installed.map_image(grid,56)
assert np.array_equal(np.asarray(after),scene),'Lossless compilation failed'
mask=np.ones((1248,896),dtype=bool);mask[42*16:54*16,14*16:32*16]=False
assert np.array_equal(normalized[mask],np.asarray(after)[mask]),'Outside normalized baseline art changed'
assert all(e>>12<13 for n in grid for e in finalblocks[n&1023]),'Unsupported runtime palette'
assert all((a&0xfc00)==(b&0xfc00) and attrs[a&1023]==finalattrs[b&1023] for a,b in zip(oldgrid,grid)),'Exploration properties changed'
locked=['data/maps/FloccesyTown/map.json','data/maps/FloccesyTown/scripts.inc','data/layouts/FloccesyTown/border.bin','src/field_door.c']
for rel in locked:assert (B/rel).read_bytes()==(G/rel).read_bytes(),rel
Image.fromarray(normalized).crop((224,672,512,864)).save(E/'before-native.png');after.crop((224,672,512,864)).save(E/'after-native.png');after.save(E/'town-overview.png')
report=dict(new_patterns=len(newraw),lossless_lower_layer_reuses=optimized_entries,reclaimed_slots=len(free),tile_capacity=1008,metatiles=len(finalblocks),changed_cells=len(changes),lossless_compilation=True,outside_sample_pixel_identical_to_palette_corrected_baseline=True,supported_palette_correction=True,all_collision_elevation_behavior_layer_properties_identical=True,locked_files=locked)
(E/'integration.json').write_text(json.dumps(report,indent=2)+'\n');state.write_text(json.dumps(dict(map_sha256=sha(G/'data/layouts/FloccesyTown/map.bin')),indent=2)+'\n');print(report)
