"""Audit every outdoor cell, active door/warp, NPC lane and directed path edge."""
from pathlib import Path
from collections import deque, Counter
import json, struct, sys, hashlib
from PIL import Image, ImageDraw
R=Path(__file__).resolve().parents[4];G=R/'tools/vendor/gba/cherrygrove-synthesis-work';E=R/'gba/art/cherrygrove-synthesis/evidence'
sys.path.insert(0,str(R/'tools/gba/maps'))
from tiles import Tileset
from events import expected_events
names={0:'CherrygroveCity',1:'CherrygrovePlayerHouse',2:'CherrygroveGoldHouse',3:'CherrygroveNeighborHouse',4:'CherrygroveTransplantHouse',5:'CherrygroveMart',6:'CherrygrovePokemonCenter',7:'CherrygrovePlayerBedroom',8:'CherrygroveCenterUpstairs',9:'CherrygroveRoute29Approach',10:'CherrygroveRoute30Approach',11:'CherrygroveHarborHouse',12:'CherrygroveGardenHouse',13:'SandgemTown',20:'FloccesyTown'}
layouts={l['id']:l for l in json.loads((G/'data/layouts/layouts.json').read_text())['layouts']}
ms={};ids={}
for mid,name in names.items():
 m=json.loads((G/f'data/maps/{name}/map.json').read_text());l=layouts[m['layout']];b=(G/l['blockdata_filepath']).read_bytes();ms[mid]=(l['width'],l['height'],struct.unpack('<'+'H'*(len(b)//2),b),m);ids[m['id']]=mid
outdoors={0,9,10};t=Tileset(G,'cherrygrove','cherrygrove')
def value(mid,x,y):
 w,h,g,_=ms[mid];assert 0<=x<w and 0<=y<h,(mid,x,y);return g[y*w+x]
def kind(mid,x,y):
 v=value(mid,x,y)
 if v&0xc00:return 'solid'
 if mid in outdoors and t.attrs[(v&1023)>=512][v&511]&255==105:return 'door'
 return 'water' if v>>12==1 else 'land'
def resolve(mid,x,y):
 w,h,g,m=ms[mid]
 if 0<=x<w and 0<=y<h:return mid,x,y
 d='left' if x<0 else 'right' if x>=w else 'up' if y<0 else 'down'
 for c in m['connections'] or []:
  if c['direction']!=d:continue
  dest=ids[c['map']];dw,dh,_,_=ms[dest];o=c['offset'];xx,yy=(x+dw,y-o) if d=='left' else (x-w,y-o) if d=='right' else (x-o,y+dh) if d=='up' else (x-o,y-h)
  if 0<=xx<dw and 0<=yy<dh:return dest,xx,yy
 return None
steps=[(1,0,16),(-1,0,32),(0,1,128),(0,-1,64)]
npc=set();npc_report=[]
for mid in outdoors:
 for e in ms[mid][3]['object_events']:
  cells={(mid,x,y) for y in range(e['y']-e['movement_range_y'],e['y']+e['movement_range_y']+1) for x in range(e['x']-e['movement_range_x'],e['x']+e['movement_range_x']+1)}
  assert all(kind(*p)=='land' for p in cells),(e['local_id'],cells)
  npc|=cells;npc_report.append(dict(map=mid,id=e['local_id'],clear_cells=len(cells)))
def flood(avoid):
 seen={(0,48,20)};q=deque(seen)
 while q:
  mid,x,y=q.popleft()
  for dx,dy,_ in steps:
   p=resolve(mid,x+dx,y+dy)
   if p and p[0] in outdoors and p not in seen and p not in avoid and kind(*p) in ('land','door'):seen.add(p);q.append(p)
 return seen
seen=flood(set());crowded=flood(npc);warps=set();warp_report=[];door_cells=set();cases=[]
def case(label,mid,x,y,key,dest,xx,yy,facing=0):cases.append((label,mid,x,y,key,dest,xx,yy,facing))
for mid in outdoors:
 for i,e in enumerate(ms[mid][3]['warp_events']):
  p=(mid,e['x'],e['y']);warps.add(p);dest=ids[e['dest_map']];target=ms[dest][3]['warp_events'][int(e['dest_warp_id'])]
  assert not value(dest,target['x'],target['y'])&0xc00,(p,'blocked destination')
  if mid==0 and i==3:
   # Reserved index from a removed building. Preserve IDs; forest has neither
   # door behavior nor walkable access. The obsolete room now exits at harbor.
   assert p not in seen and kind(*p)=='solid'
   warp_report.append(dict(map=mid,index=i,status='reserved inactive; forest blocked'));continue
  assert p in seen,(p,'unreachable warp')
  if mid==0:
   assert kind(*p)=='door';door_cells.add(p[1:]);assert (mid,e['x'],e['y']+1) in crowded,(p,'NPC can seal approach')
   case(f'door-{dest}-enter',mid,e['x'],e['y']+1,64,dest,target['x'],target['y'],2)
   exits=[w for w in ms[dest][3]['warp_events'] if w['dest_map']=='MAP_CHERRYGROVE_CITY']
   for j,w in enumerate(exits):
    assert int(w['dest_warp_id'])==i,(dest,'wrong return ID')
    case(f'door-{dest}-exit-{j}',dest,w['x'],w['y']-1,128,0,e['x'],e['y']+1,1)
  else:
   assert target['dest_map']==ms[mid][3]['id'] and int(target['dest_warp_id'])==i
   if mid==9:
    case(f'preview-{mid}-{i}-out',mid,e['x']-1,e['y'],16,dest,target['x'],target['y'],4)
    case(f'preview-{mid}-{i}-back',dest,target['x']+1,target['y'],32,mid,e['x'],e['y'],3)
   else:
    case(f'preview-{mid}-{i}-out',mid,e['x'],e['y']+1,64,dest,target['x'],target['y'],2)
    case(f'preview-{mid}-{i}-back',dest,target['x'],target['y']-1,128,mid,e['x'],e['y'],1)
  warp_report.append(dict(map=mid,index=i,x=e['x'],y=e['y'],destination=dest,status='reachable; destination clear'))
# The retained inactive slot must have no remaining incoming map warp.
for f in (G/'data/maps').glob('*/map.json'):
 for e in json.loads(f.read_text()).get('warp_events',[]):
  if e['dest_map']=='MAP_CHERRYGROVE_CITY':
   assert e['dest_warp_id']!='3',('return into forest',f,e)
actual={(i%ms[0][0],i//ms[0][0]) for i,v in enumerate(ms[0][2]) if t.attrs[(v&1023)>=512][v&511]&255==105}
assert actual==door_cells,'Missing or phantom door behavior'
# Every reachable tree trunk/canopy tile must be solid. Pixel-level examination
# also catches building-footprint resets that accidentally reopen tree cells.
for mid,x,y in seen:
 v=value(mid,x,y)&1023;count=0
 for e in t.blocks[v>=512][v%512]:
  if e>>12 in (3,10):count+=sum(c!=0 for c in t.tiles[(e&1023)>=512][e&511])
 assert count<=12,('walkable tree',mid,x,y,count)
probes=[];edge_counts=Counter();seams=[]
for mid,x,y in sorted(seen):
 for dx,dy,key in steps:
  p=resolve(mid,x+dx,y+dy);assert p is not None
  edge_counts[kind(*p)]+=1
  if p[0]!=mid:
   assert kind(*p)=='land';seams.append((mid,x,y,key,*p));case(f'seam-{mid}-{x}-{y}-{key}',mid,x,y,key,*p,{128:1,64:2,32:3,16:4}[key])
   continue
  if (mid,x,y) in warps|npc or p in warps|npc:continue
  k=kind(*p)
  if k=='door':continue
  probes.append((mid,x,y,key,0,int(k=='land'),value(*p)&1023))
# Guard obsolete interior saves and all stairs, with layout-specific directions.
for j,x in enumerate((3,4)):case(f'legacy-room-exit-{j}',4,x,7,128,0,52,32,1)
# MB_WARP stairs automatically step down onto the clear landing.
case('bedroom-up',1,8,3,64,7,7,2,1)
case('bedroom-down',7,6,1,16,1,8,3,1)
# Escalators are approached from their right-hand landing; the arrival walks off.
case('center-up',6,2,6,32,8,2,6,4)
case('center-down',8,2,6,32,6,2,6,4)
(E/'access-probes.tsv').write_text(''.join(' '.join(map(str,p))+'\n' for p in probes))
(E/'access-warps.tsv').write_text(''.join(' '.join(map(str,p))+'\n' for p in cases))
report=dict(reachable_tiles=len(seen),reachable_with_all_npc_ranges_occupied=len(crowded),npc_ranges=npc_report,warps=warp_report,active_visible_doors=len(door_cells),all_visible_door_approaches_remain_open_with_npc_ranges_occupied=True,walkable_tree_cells=0,directed_edges=dict(edge_counts),native_collision_probes=len(probes),native_travel_cases=len(cases),connection_seams=seams,layout_sha256={names[mid]:hashlib.sha256((G/layouts[ms[mid][3]['layout']]['blockdata_filepath']).read_bytes()).hexdigest() for mid in outdoors})
(E/'access-structure.json').write_text(json.dumps(report,indent=2)+'\n')
im=Image.open(E/'CherrygroveCity.png').convert('RGBA');over=Image.new('RGBA',im.size);d=ImageDraw.Draw(over)
for y in range(ms[0][1]):
 for x in range(ms[0][0]):
  k=kind(0,x,y);color=(235,65,65,90) if k=='solid' else (50,170,255,60) if k=='water' else (30,230,100,45) if (0,x,y) in seen else None
  if color:d.rectangle((x*16,y*16,x*16+15,y*16+15),fill=color)
for x,y in door_cells:d.rectangle((x*16,y*16,x*16+15,y*16+15),outline=(255,230,0,255),width=2)
Image.alpha_composite(im,over).convert('RGB').save(E/'collision-overlay.png')
print(json.dumps({k:v for k,v in report.items() if k in ('reachable_tiles','native_collision_probes','native_travel_cases','walkable_tree_cells','directed_edges')}))
