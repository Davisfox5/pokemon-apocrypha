#!/usr/bin/env python3
"""Town-wide, lossless native-tile material pass. Never changes exploration data."""
from pathlib import Path
from collections import Counter
import struct, json, hashlib, itertools, sys, math
import numpy as np
from PIL import Image
from tiles import Tileset
R=Path(__file__).resolve().parents[3]
B=R/'tools/vendor/gba/floccesy-detailed-work'
baseline=False
G=R/'tools/vendor/gba/floccesy-polish-work'
A=R/'gba/art/floccesy-polish';E=A/('baseline-evidence' if baseline else 'evidence');E.mkdir(parents=True,exist_ok=True)
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
pals[6]=[(0,0,0)]+[rgb5(c) for c in [(198,226,115),(166,207,96),(142,192,82),(116,177,75),(87,157,77),(66,145,77),(47,131,76),(36,122,76),(80,115,70),(28,103,73),(20,96,70),(17,82,65),(83,66,47),(20,68,58),(16,54,49)]]
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
road=set();dirt=set()
for x,y,w,h in [(9,66,38,3),(29,39,3,29),(13,54,34,3)]:road.update((xx,yy) for yy in range(y,y+h) for xx in range(x,x+w))
for x,y,w,h in [(29,27,3,13),(30,28,17,3),(17,29,8,9),(18,25,2,5),(39,43,4,2),(40,45,3,2),(39,49,3,2),(40,51,3,2)]:dirt.update((xx,yy) for yy in range(y,y+h) for xx in range(x,x+w))
for y,x in [(46,40),(47,39),(48,38),(49,38),(50,37),(51,36)]:dirt.update((xx,yy) for yy in range(y,y+2) for xx in range(x,x+3))
def lawn_ink(u,v,x,y):
 # Broad, low-contrast turf clusters; short leaf accents sit inside them.
 value=math.sin(u*.46)+math.cos(v*.52)+math.sin((u+v)*.31)
 ink=3 if value<-.9 else 2 if value>1.1 else 1
 if (u,v) in [(3,8),(4,8),(4,9),(9,3),(10,3),(11,4),(12,12),(13,12)]:ink=5
 if (u,v) in [(3,7),(9,2),(12,11)]:ink=4
 if (u,v) in [(6,13),(7,12),(7,13),(2,2)]:ink=11
 if x==16 and 43<=y<=51 and u<3:ink=7 if u<2 else 5
 if x==25 and 43<=y<=51 and u>13:ink=5
 # A short tapered contact shadow remains entirely on walkable lawn.
 limit={47:4,48:4,49:6,50:6}.get(y,0)
 if x==24 and u<limit:ink=7 if u<limit-2 else 5
 if y==51 and 20<=x<=24 and v<4 and (x<24 or u<6):ink=7 if v<2 else 5
 return ink
def wall_ink(x,y,u,v):
 left=x==15;right=x==26;top=y==42;bottom=y==52
 cap=(left and 3<=u<=11) or (right and 4<=u<=12) or (top and 4<=v<=12) or (bottom and v<=5)
 ink=1 if left else 5 if right else 2
 if cap:
  ink=3
  # Lit outside arris, then a broad stone top and narrow inner shadow.
  if (left and u==3) or (right and u==4) or (top and v==4) or (bottom and v==0):ink=7
  elif (left and u==11) or (right and u==12) or (top and v==12) or (bottom and v==5):ink=1
  elif ((left or right) and v==15) or ((top or bottom) and u==15):ink=8
  elif (u,v) in [(7,5),(8,5),(6,10)]:ink=4
 elif bottom:
  ink=4 if v==6 else 2 if v<12 else 1 if v<15 else 5
  if (u+(8 if v>=12 else 0))%16==15:ink=5
 elif left:
  ink=4 if u==0 else 2 if u<3 else 5
 elif right:
  ink=5 if u<4 else 2 if u<15 else 1
 # The two stair jambs finish the exposed cut end of the coping.
 if bottom and ((x==19 and u==15) or (x==22 and u==0)):ink=1 if v<6 else 5
 return ink
# Lawn: restrained color clusters and a shaded edge, replacing repeated V marks.
for yy in range(78*16):
 for xx in range(56*16):
  x,y=xx//16,yy//16;u,v=xx%16,yy%16;b=int(bankmap[yy,xx])
  if b==0:
   ink=lawn_ink(u,v,x,y)
   scene[yy,xx]=pals[12][ink]
  elif b==6:
   scene[yy,xx]=pals[6][indexmap[yy,xx]]
  elif b==10:
   scene[yy,xx]=pals[10][t.pals[1][10].index(tuple(map(int,scene[yy,xx]))) ]
  elif b==3 and ((14<=x<=27 and 42<=y<=53) or (14<=x<=27 and 57<=y<=65) or (34<=x<=46 and 57<=y<=65)):
   # Dressed warm pavers, with narrow joints and a lit upper edge.
   ux=(u+(8 if v>=8 else 0))%16;vy=v%8
   ink=12 if vy==7 or ux==15 else 7 if vy==6 or ux==14 else 13 if vy==0 else 6 if ux==0 else 2
   if vy in (2,3) and ux in (4,5):ink=3
   scene[yy,xx]=pals[3][ink]
  elif b==4 and ((x in (15,26) and 42<=y<=52) or (y in (42,52) and 15<=x<=26)) and not (y==52 and x in (20,21)):
   # Continuous low planter rim. Side runs have longitudinal coping; their
   # profile is not the horizontal front face repeated in every direction.
   ink=wall_ink(x,y,u,v)
   scene[yy,xx]=pals[4][ink]
  elif b==2 and (x,y) in road:
   ink=1 if (u*17+v*11)%23>2 else 2 if u%2 else 3
   edges=[]
   if (x-1,y) not in road:edges.append(u)
   if (x+1,y) not in road:edges.append(15-u)
   if (x,y-1) not in road:edges.append(v)
   if (x,y+1) not in road:edges.append(15-v)
   edge=min(edges,default=99)
   if edge<4:ink=13 if edge==0 else 7 if edge<3 else 6
   elif edge<6:ink=8
   if edge<4 and ((u==15 and (x,y-1) not in road) or (v==15 and (x-1,y) not in road)):ink=11
   scene[yy,xx]=pals[2][ink]
  elif b==1 and (x,y) in dirt:
   # Keep the court's existing line pixels exactly where they are.
   if 18<=x<24 and 31<=y<37 and indexmap[yy,xx]==6:continue
   ink=1
   if (u,v) in [(1,3),(2,3),(8,12),(9,12),(12,5)]:ink=3
   elif (u,v) in [(3,3),(9,11),(13,5),(5,8)]:ink=2
   elif (u,v) in [(6,14),(14,10)]:ink=7
   scene[yy,xx]=pals[1][ink]
# Rework only existing flower-cell footprints into low, shaded flowering plants.
for y in range(78):
 for x in range(56):
  area=bankmap[y*16:y*16+16,x*16:x*16+16]
  if not np.any(area==5) or oldgrid[y*56+x]&0xc00 or (x,y) in road or not set(area.ravel())<={-1,0,5}:continue
  # Clear the old petal pixels within this same footprint, then rebuild a
  # shared low plant; retaining two overlaid flower sprites wastes tile space.
  for vv in range(16):
   for uu in range(16):
    if area[vv,uu]==5:scene[y*16+vv,x*16+uu]=pals[12][lawn_ink(uu,vv,x,y)]
  # Existing two-color flowers receive leaf clusters and shaded petals.
  for cx,cy in ((5,6),(11,10)):
   for dx,dy,ink in [(-2,3,11),(-1,3,6),(0,3,6),(1,3,11),(-3,2,6),(-2,2,7),(-1,2,9),(1,2,7),(2,2,8),(3,1,7),(0,1,6)]:
    scene[y*16+cy+dy,x*16+cx+dx]=pals[5][ink]
   for dx,dy,ink in [(-1,-1,5),(0,-2,2),(0,-1,2),(1,-1,1),(-1,0,1),(1,0,1),(-1,1,4),(0,1,5),(1,1,5),(0,0,3)]:
    scene[y*16+cy+dy,x*16+cx+dx]=pals[5][ink]
# Explicit material ownership prevents legacy plants from surviving on hard
# surfaces. This is independent of collision, so a walkable step is still stone.
paving={(xx,yy) for x,y,w,h in [(14,42,14,12),(14,57,14,9),(34,57,13,9)] for yy in range(y,y+h) for xx in range(x,x+w)}
wall={(x,y) for y in range(42,53) for x in (15,26)}|{(x,y) for y in (42,52) for x in range(15,27)}
steps={(x,y) for y in (39,40) for x in (29,30,31)}|{(20,52),(21,52)}
wall-=steps
spec=json.loads((A/'layout.json').read_text());door_cells={tuple(b['door']) for b in spec['buildings']}
hard=road|dirt|paving|wall|steps|door_cells
# Garden interior is lawn, not paving; retain its existing plants.
hard-={(x,y) for y in range(43,52) for x in range(16,26)}
def floor_rgb(xx,yy):
 x,y=xx//16,yy//16;u,v=xx%16,yy%16
 if (x,y) in steps:return pals[4][5 if v%5==4 else 4 if v%5==0 else 3]
 if (x,y) in wall:return pals[4][wall_ink(x,y,u,v)]
 if 16<=x<=25 and 43<=y<=51:return pals[12][lawn_ink(u,v,x,y)]
 if (x,y) in paving:
  ux=(u+(8 if v>=8 else 0))%16;vy=v%8
  ink=12 if vy==7 or ux==15 else 7 if vy==6 or ux==14 else 13 if vy==0 else 6 if ux==0 else 2
  if vy in (2,3) and ux in (4,5):ink=3
  return pals[3][ink]
 if (x,y) in road:
  ink=1 if (u*17+v*11)%23>2 else 2 if u%2 else 3;edges=[]
  if (x-1,y) not in road:edges.append(u)
  if (x+1,y) not in road:edges.append(15-u)
  if (x,y-1) not in road:edges.append(v)
  if (x,y+1) not in road:edges.append(15-v)
  edge=min(edges,default=99)
  if edge<4:ink=13 if edge==0 else 7 if edge<3 else 6
  elif edge<6:ink=8
  if edge<4 and ((u==15 and (x,y-1) not in road) or (v==15 and (x-1,y) not in road)):ink=11
  return pals[2][ink]
 if (x,y) in dirt or (x,y) in door_cells:return pals[1][1]
 return pals[12][lawn_ink(u,v,x,y)]
cleaned=0
for x,y in hard:
 for v in range(16):
  for u in range(16):
   xx=x*16+u;yy=y*16+v
   if bankmap[yy,xx] in (0,5):scene[yy,xx]=floor_rgb(xx,yy);cleaned+=1
# Recover clean building silhouettes from their preserved native source alpha.
# Restore only outline pixels and invalid vegetation, not the entire sprite.
arch=np.zeros_like(scene);owner=np.zeros(scene.shape[:2],dtype=np.uint8);boxes=[]
for b in spec['buildings']+[dict(style='tower',x=19,y=44,pixel_dx=0)]:
 style=b['style'];bank={'house':7,'alder':8,'center':9,'tower':10,'shed':11}[style]
 im=np.asarray(Image.open(R/f'gba/art/floccesy-v4/native/{style}.png').convert('RGBA'));gx=b['x']*16+b['pixel_dx'];gy=b['y']*16
 alpha=im[:,:,3]>0;hh,ww=alpha.shape
 for v,u in zip(*np.nonzero(alpha)):
  color=tuple(map(int,im[v,u,:3]));idx=t.pals[bank>=6][bank].index(color);arch[gy+v,gx+u]=pals[bank][idx];owner[gy+v,gx+u]=bank
 boxes.append((gx,gy,ww,hh,bank))
edge_repairs=0
canopy_quads=np.isin(bankmap,(6,13,14,15)).reshape(156,8,112,8).any(axis=(1,3))
for gx,gy,ww,hh,bank in boxes:
 for yy in range(gy,gy+hh):
  for xx in range(gx,gx+ww):
   b=int(bankmap[yy,xx])
   if canopy_quads[yy//8,xx//8]:continue # preserve two-palette canopy junctions
   if owner[yy,xx]:
    edge=any(owner[yy+dy,xx+dx]==0 for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)])
    if b in (0,5) or (edge and b!=owner[yy,xx]):
     if not np.array_equal(scene[yy,xx],arch[yy,xx]):edge_repairs+=1
     scene[yy,xx]=arch[yy,xx]
   elif b==bank:
    scene[yy,xx]=floor_rgb(xx,yy);edge_repairs+=1
# The existing court becomes a maintained clay battle surface. It stays flat,
# walkable, and open to the south, with the same benches and fence obstacles.
# All original grass has moved to bank 12; reuse bank 0 for court clay.
pals[0]=pals[1][:]
for ink,color in {1:(194,139,89),2:(183,128,82),3:(209,154,101),5:(248,242,217),7:(163,116,81),10:(135,97,70),12:(218,162,111)}.items():pals[0][ink]=rgb5(color)
for yy in range(29*16,38*16):
 for xx in range(17*16,25*16):
  x,y=xx//16,yy//16;u,v=xx%16,yy%16
  fx=xx-18*16;fy=yy-31*16
  ink=1
  if (u,v) in [(2,4),(3,4),(10,11),(11,11)]:ink=3
  elif (u,v) in [(4,4),(12,10),(6,13)]:ink=2
  # A compacted perimeter apron and inner marked rectangle.
  if -8<=fx<=103 and -8<=fy<=103 and not (0<=fx<=95 and 0<=fy<=95):ink=7 if (u+v)%7 else 3
  if 0<=fx<=95 and 0<=fy<=95:
   if fx in (0,95) or fy in (0,95):ink=10
   if fx in (2,3,92,93) or fy in (2,3,92,93):ink=5
   # Center stripe with a crisp Poké Ball ring, readable at game scale.
   rr=(fx-47.5)**2+(fy-47.5)**2
   if fy in (47,48):ink=5
   if 18**2<=rr<=20**2:ink=5
   if 5**2<=rr<=7**2:ink=5
   if rr<5**2:ink=1
   # Trainer starting boxes use paint, not new gameplay triggers or props.
   for top in (10,74):
    if 35<=fx<=60 and top<=fy<=top+11 and (fx in (35,36,59,60) or fy in (top,top+1,top+10,top+11)):ink=5
  scene[yy,xx]=pals[0][ink]
# Restore the authored bench silhouettes above the new court, including the
# pixels whose old wood palette was shared with soil.
bench=np.asarray(Image.open(R/'gba/art/floccesy-v4/native/court-bench.png').convert('RGBA'))
for bx in (17,24):
 for v,u in zip(*np.nonzero(bench[:,:,3])):scene[34*16+v,bx*16+u]=bench[v,u,:3]
# Reorient side rails along the fence run, using the existing blocked cells.
for y in range(28,38):
 for x in range(16,26):
  if not (y==28 or x in (16,25)):continue
  for v in range(16):
   for u in range(16):
    if y==28:
     wood=(5<=v<=9) or (6<=u<=9 and 1<=v<=14)
     ink=4 if v==5 else 1 if v==9 else 2
     if 6<=u<=9:ink=4 if u==6 else 1 if u==9 else 3
    else:
     wood=(5<=u<=9) or (3<=u<=12 and 5<=v<=10)
     ink=4 if u==5 else 1 if u==9 else 2
     if 5<=v<=10:ink=4 if v==5 else 1 if v==10 else 3
    scene[y*16+v,x*16+u]=pals[4][ink] if wood else pals[12][lawn_ink(u,v,x,y)]
from floccesy_polish_art import polish
scene=polish(scene,pals,spec,oldgrid,R,A,lawn_ink,floor_rgb)
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
   aa,bb=choices[0]
   if bb==12 and aa!=12:aa,bb=bb,aa # lawn beneath architecture and plants
   low=bytes(maps[aa].get(c,0) for c in cs);high=bytes(maps[bb].get(c,0) if c not in sets[aa] else 0 for c in cs)
   out[q]=(*intern(low),aa);out[q+4]=(*intern(high),bb)
  if out!=[(e&1023,e&3072,e>>12) for e in old]:changes[(x,y)]=(mid,out)
# Include inherited cells in exact storage optimization without changing pixels.
for i,n in enumerate(oldgrid):
 pos=(i%56,i//56)
 if pos not in changes:
  mid=n&1023;changes[pos]=(mid,[(e&1023,e&3072,e>>12) for e in blocks[mid]])
# Optimize newly authored lower layers too: retain every visible pixel while
# replacing cropped backgrounds with reusable complete ground patterns.
allraw={i:d for i,d in enumerate(raw[:1008])};allraw.update({1024+i:d for i,d in enumerate(newraw)})
usage=Counter()
for i,n in enumerate(oldgrid):
 pos=(i%56,i//56)
 es=changes[pos][1] if pos in changes else [(e&1023,e&3072,e>>12) for e in blocks[n&1023]]
 usage.update(e[0] for e in es)
refs=[];candidates=[]
for tid in sorted(allraw,key=lambda i:(-usage[i],-sum(bool(v) for v in allraw[i]))):
 for flip in (0,1024,2048,3072):
  ar=np.frombuffer(allraw[tid],dtype=np.uint8).reshape(8,8)
  ar=ar[:,::-1] if flip&1024 else ar;ar=ar[::-1] if flip&2048 else ar
  refs.append((tid,flip));candidates.append(ar.ravel())
candidates=np.asarray(candidates);new_lower_reuses=0
for mid,es in changes.values():
 def resolved(e):
  tid,flip,bank=e;ar=np.frombuffer(allraw[tid],dtype=np.uint8).reshape(8,8)
  ar=ar[:,::-1] if flip&1024 else ar;ar=ar[::-1] if flip&2048 else ar
  return ar.ravel()
 for q in range(4):
  mask=resolved(es[q+4])==0
  if mask.all():continue
  target=resolved(es[q]);matches=np.flatnonzero(np.all(candidates[:,mask]==target[mask],axis=1))
  if len(matches):
   tid,flip=refs[matches[0]];entry=(tid,flip,es[q][2])
   if entry!=es[q]:new_lower_reuses+=1;es[q]=entry
# Lossless, cost-checked two-layer factorization. All references to a pattern
# are replaced together; a tile still needed as another tile's base is retained.
active=Counter();positions={}
for i,n in enumerate(oldgrid):
 es=changes[(i%56,i//56)][1] if (i%56,i//56) in changes else [(e&1023,e&3072,e>>12) for e in blocks[n&1023]]
 active.update(e[0] for e in es)
 if (i%56,i//56) in changes:
  for q in range(4):
   tid,flip,bank=es[q]
   if resolved(es[q]).all() and not resolved(es[q+4]).any():positions.setdefault(tid,[]).append((es,q))
selected=[j for j,(tid,flip) in enumerate(refs) if active[tid]>0];bases=candidates[selected]
groups={}
for tid,poses in positions.items():
 if active[tid]!=len(poses):continue
 target=np.frombuffer(allraw[tid],dtype=np.uint8);delta=bases!=target;cost=delta.sum(axis=1)
 for j in np.argsort(cost)[:256]:
  bt,bf=refs[selected[j]]
  if bt==tid:continue
  ar=np.where(delta[j],target,0).astype(np.uint8).reshape(8,8)
  forms=[ar.tobytes(),ar[:,::-1].tobytes(),ar[::-1].tobytes(),ar[::-1,::-1].tobytes()];signature=min(forms)
  choices=groups.setdefault(signature,{})
  if tid not in choices or active[bt]>active[choices[tid][0]]:choices[tid]=(bt,bf,ar.tobytes())
reduced=0;done=set()
for signature,options in sorted(groups.items(),key=lambda item:-len(item[1])):
 available={tid:v for tid,v in options.items() if tid not in done and active[tid]==len(positions[tid]) and active[tid]>0 and active[v[0]]>0}
 if not available:continue
 detail_ref=lookup.get(signature);existing=detail_ref and active[detail_ref[0]]>0
 bases_needed={v[0] for v in available.values()}
 saved=len(set(available)-bases_needed)-(0 if existing else 1)
 if saved<=0:continue
 for tid,(bt,bf,detail) in available.items():
  done.add(tid)
  dt,df=intern(detail)
  if dt>=1024:allraw[dt]=newraw[dt-1024]
  for es,q in positions[tid]:
   old,flip,bank=es[q];active[old]-=1;active[es[q+4][0]]-=1
   es[q]=(bt,bf^flip,bank);es[q+4]=(dt,df^flip,bank);active[bt]+=1;active[dt]+=1
 reduced+=saved
print('Lossless pattern savings',reduced)
# Canonicalize inherited duplicated/flipped patterns as well as new ones.
def canon(e):
 tid,flip,bank=e
 ar=np.frombuffer(allraw[tid],dtype=np.uint8).reshape(8,8)
 ar=ar[:,::-1] if flip&1024 else ar;ar=ar[::-1] if flip&2048 else ar
 t,f=lookup[ar.tobytes()]
 return (t,f,bank)
for mid,es in changes.values():
 for j,e in enumerate(es):es[j]=canon(e)
for mid in set(n&1023 for n in oldgrid):
 es=[canon((e&1023,e&3072,e>>12)) for e in blocks[mid]]
 blocks[mid]=tuple(tid|flip|(bank<<12) for tid,flip,bank in es)
used=set()
for i,n in enumerate(oldgrid):
 x,y=i%56,i//56
 entries=changes[(x,y)][1] if (x,y) in changes else [(e&1023,e&3072,e>>12) for e in blocks[n&1023]]
 used.update(e[0] for e in entries)
border=struct.unpack('<4H',(B/'data/layouts/FloccesyTown/border.bin').read_bytes())
for n in border:
 mid=n&1023;blocks[mid]=tuple((e&0xfff)|(6<<12) if e>>12 in (13,14) else e for e in blocks[mid])
for n in border:used.update(e&1023 for e in blocks[n&1023])
free=sorted(set(range(1,1008))-used)
needed=sorted(i for i in used if i>=1024)
if len(needed)>len(free):
 bybank={b:set() for b in range(13)}
 for i,n in enumerate(oldgrid):
  es=changes[(i%56,i//56)][1] if (i%56,i//56) in changes else [(e&1023,e&3072,e>>12) for e in blocks[n&1023]]
  for tid,flip,b in es:bybank[b].add(tid)
 print('Bank patterns', {b:len(v) for b,v in bybank.items()})
assert len(needed)<=len(free),('native capacity exceeded',len(needed),len(free))
remap=dict(zip(needed,free))
for old,tid in remap.items():raw[tid]=newraw[old-1024]
finalblocks=blocks[:];finalattrs=attrs[:];grid=oldgrid[:];cache={}
spare_ids=iter(i for i in range(len(blocks)) if i not in {n&1023 for n in border})
for (x,y),(mid,entries) in changes.items():
 block=tuple(remap.get(tid,tid)|flip|(bank<<12) for tid,flip,bank in entries)
 key=(block,attrs[mid])
 if key not in cache:
  slot=next(spare_ids,len(finalblocks));cache[key]=slot
  if slot==len(finalblocks):finalblocks.append(block);finalattrs.append(attrs[mid])
  else:finalblocks[slot]=block;finalattrs[slot]=attrs[mid]
 grid[y*56+x]=(oldgrid[y*56+x]&0xfc00)|cache[key]
assert len(finalblocks)<=1024,len(finalblocks)
for side,start in [('primary',0),('secondary',512)]:
 folder=G/f'data/tilesets/{side}/floccesy';sheet=Image.open(B/f'data/tilesets/{side}/floccesy/tiles.png').copy()
 for i in range(512):
  im=Image.new('P',(8,8));im.putdata(raw[start+i]);sheet.paste(im,(i%16*8,i//16*8))
 sheet.save(folder/'tiles.png')
 for bank in range(13):
  (folder/f'palettes/{bank:02d}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pals[bank])+'\n')
 part=finalblocks[start:start+512];at=finalattrs[start:start+512]
 (folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*b) for b in part))
 (folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(at),*at))
 (folder/'palettes/00.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pals[0])+'\n')
 (folder/'palettes/01.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pals[1])+'\n')
 (folder/'palettes/06.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pals[6])+'\n')
 (folder/'palettes/10.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pals[10])+'\n')
 (folder/'palettes/12.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pals[12])+'\n')
(G/'data/layouts/FloccesyTown/map.bin').write_bytes(struct.pack('<4368H',*grid))
installed=Tileset(G,'floccesy','floccesy');after=installed.map_image(grid,56)
assert np.array_equal(np.asarray(after),scene),'Lossless compilation failed'
mask=np.ones((1248,896),dtype=bool);mask[42*16:54*16,14*16:32*16]=False
# Whole-town material expansion is now authorized; geometry remains locked.
assert all(e>>12<13 for n in grid+list(border) for e in finalblocks[n&1023]),'Unsupported runtime palette'
assert all((a&0xfc00)==(b&0xfc00) and attrs[a&1023]==finalattrs[b&1023] for a,b in zip(oldgrid,grid)),'Exploration properties changed'
locked=['data/maps/FloccesyTown/map.json','data/maps/FloccesyTown/scripts.inc','data/layouts/FloccesyTown/border.bin']
for rel in locked:assert (B/rel).read_bytes()==(G/rel).read_bytes(),rel
Image.fromarray(normalized).crop((224,672,512,864)).save(E/'before-native.png');after.crop((224,672,512,864)).save(E/'after-native.png');after.save(E/'town-overview.png')
report=dict(rebuilt_roofs_and_canopy_order=True,rebuilt_fences_park_and_forest_opening=True,lossless_detail_pattern_savings=reduced,native_referenced_patterns=len(used),removed_hard_surface_plant_pixels=cleaned,building_edge_repairs=edge_repairs,new_patterns=len(needed),new_lower_reuses=new_lower_reuses,lossless_lower_layer_reuses=optimized_entries,reclaimed_slots=len(free),tile_capacity=1008,metatiles=len(finalblocks),changed_cells=len(changes),lossless_compilation=True,whole_town_materials=True,supported_palette_correction=True,all_collision_elevation_behavior_layer_properties_identical=True,locked_files=locked)
(E/'integration.json').write_text(json.dumps(report,indent=2)+'\n');state.write_text(json.dumps(dict(map_sha256=sha(G/'data/layouts/FloccesyTown/map.bin')),indent=2)+'\n');print(report)
