"""Directed movement, every door, immutable town pixels and connected-camera proof."""
from compose import *
import json,struct
from collections import deque
from claude_routes import seams
G=Path(sys.argv[1]).resolve();EV=OUT/'evidence'
layouts=json.loads((G/'data/layouts/layouts.json').read_text())['layouts'];ms={};ids={}
for name,sec in [('CherrygroveCity','cherrygrove'),('CherrygroveRoute29Approach','claude_route29'),('CherrygroveRoute30Approach','claude_route30'),('NewBarkTown','new_bark'),('JohtoRoute31','route31'),('VioletCityEntrance','violet_entrance')]:
 m=json.loads((G/'data/maps'/name/'map.json').read_text());l=next(x for x in layouts if x['id']==m['layout']);g=np.frombuffer((G/l['blockdata_filepath']).read_bytes(),'<u2').reshape(l['height'],l['width']);t=Tileset(G,sec,'cherrygrove');at=np.array([t.attrs[int((v&1023)>=512)][v&511] for v in g.ravel()]).reshape(g.shape);ms[name]=(m,g,t,at);ids[m['id']]=name
 # Only the camera-facing art is fixed; all tiles and both layers must decode.
 for v in set((g&1023).ravel()):
  for e in t.blocks[int(v>=512)][v%512]:assert e&1023<1008 and e>>12<13
m,g,t,at=ms['CherrygroveCity'];assert t.map_image(g.ravel().tolist(),80).tobytes()==Image.open(APP/'evidence/CherrygroveCity.png').convert('RGB').tobytes(),'approved town appearance changed'
def resolve(n,x,y):
 m,g,_,_=ms[n];h,w=g.shape
 if 0<=x<w and 0<=y<h:return n,x,y
 direction='left' if x<0 else 'right' if x>=w else 'up' if y<0 else 'down'
 for c in m['connections'] or []:
  if c['direction']!=direction or c['map'] not in ids:continue
  dest=ids[c['map']];dh,dw=ms[dest][1].shape;o=c['offset'];xx,yy=(x+dw,y-o) if direction=='left' else (x-w,y-o) if direction=='right' else (x-o,y+dh) if direction=='up' else (x-o,y-h)
  if 0<=xx<dw and 0<=yy<dh:return dest,xx,yy
 return None
seen={('CherrygroveCity',48,20)};q=deque(seen)
while q:
 n,x,y=q.popleft()
 for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
  p=resolve(n,x+dx,y+dy)
  if p:
   nn,xx,yy=p;_,g,_,at=ms[nn]
   if dy==1 and at[yy,xx]&255==59:
    p=resolve(nn,xx,yy+1)
    if not p:continue
    nn,xx,yy=p;_,g,_,at=ms[nn]
   if not g[yy,xx]&0xc00 and g[yy,xx]>>12!=1 and p not in seen:seen.add(p);q.append(p)
report={};probes=[]
for n,(m,g,t,at) in ms.items():
 if n=='VioletCityEntrance':continue
 reach={(x,y) for nn,x,y in seen if nn==n}
 assert reach,('map disconnected',n)
 doors=[]
 for i,w in enumerate(m['warp_events']):
  if n=='CherrygroveCity' and i==3:continue
  assert (w['x'],w['y']) in reach,('unreachable door',n,i,w)
  assert at[w['y'],w['x']]&255 in (105,97),('warp behavior',n,w)
  doors.append([w['x'],w['y']])
 for e in m['bg_events']:
  x,y=e['x'],e['y'];assert any((x+dx,y+dy) in reach for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]),('unreachable sign/item',n,e)
 report[n]=dict(reachable_cells=len(reach),doors=doors)
 # Representative wall, grass, ledge and water collision probes use actual
 # runtime collision APIs, with cases on all four sides of buildings.
 if n=='CherrygroveCity':continue
 mapid=json.loads((G/'data/maps/map_groups.json').read_text())['gMapGroup_Cherrygrove'].index(n)
 for y in range(1,g.shape[0]-1):
  for x in range(1,g.shape[1]-1):
   if (x,y) not in reach or at[y,x]&255 in (105,97):continue
   for dx,dy,d in [(1,0,4),(-1,0,3),(0,1,1),(0,-1,2)]:
    xx,yy=x+dx,y+dy
    if at[yy,xx]&255 in (59,105,97):continue
    blocked=bool(g[yy,xx]&0xc00 or g[yy,xx]>>12==1)
    if blocked or (at[y,x]&255==2 and x%5==0 and y%5==0):probes.append((mapid,x,y,d,int(blocked)))
# Full seam pixels and behavior from each palette/tile pair.
seam_count=0
for an,bn,ox,oy in [('CherrygroveCity','CherrygroveRoute29Approach',80,0),('CherrygroveCity','CherrygroveRoute30Approach',35,-86),('CherrygroveRoute29Approach','NewBarkTown',98,6),('CherrygroveRoute30Approach','JohtoRoute31',-28,-30)]:
 _,ag,at,_=ms[an];_,bg,bt,_=ms[bn];sa=((ag&0xc00)!=0)|((ag>>12)==1);sb=((bg&0xc00)!=0)|((bg>>12)==1);va,vb,cross=seams.crossing_windows(sa,sb,ox,oy);va|=seams.visible_across(~sb,sa.shape,-ox,-oy);vb|=seams.visible_across(~sa,sb.shape,ox,oy)
 for v in set((ag[va]&1023).tolist())|set((bg[vb]&1023).tolist()):
  assert at.render(v).tobytes()==bt.render(v).tobytes(),('seam pixels',an,bn,v)
  assert at.attrs[v>=512][v%512]==bt.attrs[v>=512][v%512],('seam behavior',an,bn,v)
  seam_count+=1
# Negative reachability: rock/forest boundaries must prevent access to unfinished
# regions. Door reachability alone cannot detect an unintended shortcut.
forbidden=[('CherrygroveRoute29Approach',50,0,55,4,'closed Route 46 continuation'),
 ('CherrygroveRoute29Approach',10,30,98,32,'lookout cliff'),
 ('CherrygroveRoute30Approach',32,0,35,46,'eastern rock rim'),
 ('JohtoRoute31',44,0,63,12,'Dark Cave upper terraces'),
 ('JohtoRoute31',55,12,63,18,'unmapped eastern continuation')]
for n,x0,y0,x1,y1,label in forbidden:
 assert not any((n,x,y) in seen for y in range(y0,y1) for x in range(x0,x1)),('boundary leak',label)
def local_reach(n,start,deny=lambda x,y:False):
 _,g,_,at=ms[n];todo=deque([start]);visited={start}
 while todo:
  x,y=todo.popleft()
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
   xx,yy=x+dx,y+dy
   if not (0<=xx<g.shape[1] and 0<=yy<len(g)) or deny(xx,yy):continue
   if dy==1 and at[yy,xx]&255==59:yy+=1
   if not 0<=yy<len(g) or deny(xx,yy):continue
   if g[yy,xx]&0xc00 or g[yy,xx]>>12==1 or (xx,yy) in visited:continue
   visited.add((xx,yy));todo.append((xx,yy))
 return visited
# Route 31 has exactly one crossing of its east/west rock divide: the bridge.
r31=local_reach('JohtoRoute31',(38,25),lambda x,y:33<=x<35 and 16<=y<18)
assert (4,16) not in r31,'walked around Route 31 bridge'
# Route 30 retains both lower stairs and the two intended plateau approaches.
r30='CherrygroveRoute30Approach';g=ms[r30][1];at=ms[r30][3]
for x in range(5,26):
 if x not in list(range(6,10))+list(range(17,21)):assert g[63,x]&0xc00,('lower rim gap',x)
assert (26,8) in local_reach(r30,(8,85)),'Mr Pokemon plateau disconnected'
no_encounters=local_reach(r30,(8,85),lambda x,y:at[y,x]&255==2)
assert (26,8) not in no_encounters,'Route 30 encounters can all be bypassed'
for y in range(3,28):
 if y not in (5,6,7):assert g[y,15]&0xc00,('plateau divider gap',y)
# Jump art always uses the correct one-way behavior; retain the actual ledge
# gaps from HGSS, rather than treating the whole edge as a jumpable fence.
ledge_count=0
for n,(_,g,_,at) in ms.items():
 if n=='CherrygroveCity':continue
 for y,x in zip(*np.nonzero((at&255)==59)):
  assert g[y,x]&0xc00,('walkable ledge',n,x,y);ledge_count+=1
report['boundaries']={'forbidden_regions':len(forbidden),'route31_bridge_cannot_be_bypassed':True,
 'route30_encounters_cannot_all_be_bypassed':True,'route30_lower_stair_flights':2,
 'one_way_ledge_cells':ledge_count}
report['seam_metatiles_verified']=seam_count;report['approved_town_pixels_identical']=True
report['collision_probes']=len(probes)
(EV/'structure.json').write_text(json.dumps(report,indent=2)+'\n');(EV/'probes.json').write_text(json.dumps(probes)+'\n')
print(json.dumps(report,indent=2))
