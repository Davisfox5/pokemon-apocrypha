#!/usr/bin/env python3
"""Enumerate all reachable exterior cells and their conservative camera footprint."""
from pathlib import Path
from collections import deque,Counter
import json,struct
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[4];G=R/'tools/vendor/gba/cherrygrove-synthesis-work';A=R/'gba/art/cherrygrove-synthesis/evidence'
names={0:'CherrygroveCity',9:'CherrygroveRoute29Approach',10:'CherrygroveRoute30Approach'}
layouts={v['id']:v for v in json.loads((G/'data/layouts/layouts.json').read_text())['layouts']}
ms={}; ids={}
for mid,name in names.items():
 m=json.loads((G/f'data/maps/{name}/map.json').read_text());l=layouts[m['layout']];b=(G/l['blockdata_filepath']).read_bytes();ms[mid]=(l['width'],l['height'],struct.unpack('<'+'H'*(len(b)//2),b),m);ids[m['id']]=mid

def resolve(mid,x,y):
 w,h,g,m=ms[mid]
 if 0<=x<w and 0<=y<h:return mid,x,y
 direction='left' if x<0 else 'right' if x>=w else 'up' if y<0 else 'down'
 for c in m['connections'] or []:
  if c['direction']!=direction:continue
  dest=ids[c['map']];dw,dh,_,_=ms[dest];off=c['offset']
  xx,yy=(x+dw,y-off) if direction=='left' else (x-w,y-off) if direction=='right' else (x-off,y+dh) if direction=='up' else (x-off,y-h)
  if 0<=xx<dw and 0<=yy<dh:return dest,xx,yy
 return None

def walk(p):
 mid,x,y=p;w,h,g,m=ms[mid];return not g[y*w+x]&0xc00 and (g[y*w+x]>>12)!=1
seen={(0,48,20)};q=deque(seen)
while q:
 mid,x,y=q.popleft()
 for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
  p=resolve(mid,x+dx,y+dy)
  if p and p not in seen and walk(p):seen.add(p);q.append(p)
assert {p[0] for p in seen}=={0,9,10}, "Both routes must connect on foot"
exposed=[];footprints=[]
for mid,x,y in sorted(seen):
 for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
  if resolve(mid,x+dx,y+dy) is None:exposed.append([mid,x,y,dx,dy])
 missing=[(xx,yy) for yy in range(y-6,y+7) for xx in range(x-8,x+9) if resolve(mid,xx,yy) is None]
 if missing:footprints.append(dict(map=mid,x=x,y=y,missing=missing))
allwalk={(mid,x,y) for mid,(w,h,g,m) in ms.items() for y in range(h) for x in range(w) if walk((mid,x,y))}
report=dict(reachable_tiles=len(seen),by_map={names[k]:v for k,v in Counter(p[0] for p in seen).items()},unreachable_collision_clear_tiles=sorted(allwalk-seen),exposed_player_edges=exposed,camera_half_extent_tiles=[8,6],uncovered_camera_footprints=footprints)
(A/'boundary-structure.json').write_text(json.dumps(report,indent=2)+'\n');(A/'boundary-tiles.tsv').write_text(''.join('%d %d %d\n'%p for p in sorted(seen)))
im=Image.open(A/'CherrygroveCity.png').convert('RGBA');overlay=Image.new('RGBA',im.size);d=ImageDraw.Draw(overlay)
# The overview is exported at native map resolution.
sx=im.width/ms[0][0];sy=im.height/ms[0][1]
for mid,x,y in seen:
 if mid==0:d.rectangle((x*sx,y*sy,(x+1)*sx-1,(y+1)*sy-1),fill=(40,220,240,70))
Image.alpha_composite(im,overlay).convert('RGB').save(A/'reachable-walking-tiles.png')
print(json.dumps({k:v for k,v in report.items() if k!='unreachable_collision_clear_tiles'},indent=2))
assert not exposed and not footprints

# Conservative combined walking/surfing flood fill. Native water has elevation 1,
# clear collision; the rocky reef remains impassable with ordinary behavior.
combined={(0,48,20)};q=deque(combined)
while q:
 mid,x,y=q.popleft()
 for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
  p=resolve(mid,x+dx,y+dy)
  if not p or p in combined:continue
  mm,xx,yy=p;w,h,g,m=ms[mm]
  if not g[yy*w+xx]&0xc00:combined.add(p);q.append(p)
for mid,x,y in combined:
 for yy in range(y-6,y+7):
  for xx in range(x-8,x+9):assert resolve(mid,xx,yy) is not None,('surf camera edge',mid,x,y,xx,yy)
water=[p for p in combined if p[0]==0 and ms[0][2][p[2]*ms[0][0]+p[1]]>>12==1]
assert water and min(p[1] for p in water)>=9 and max(p[2] for p in water)<=40
(A/'surf-structure.json').write_text(json.dumps(dict(reachable_walk_and_surf_cells=len(combined),reachable_water_cells=len(water),westernmost_surf_x=min(p[1] for p in water),southernmost_surf_y=max(p[2] for p in water),all_camera_footprints_covered=True),indent=2)+'\n')
