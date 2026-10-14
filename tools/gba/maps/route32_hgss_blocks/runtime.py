"""Native headless Route32 tour, both ground branches, doors, barriers and ordinary flash Continue."""
from pathlib import Path
import sys,json
from collections import deque
import numpy as np
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent))
from tiles import Tileset
from johto_connections import runtime as r
G=Path(sys.argv[1]);OUT=HERE.parents[3]/'gba/art/route32-hgss-blocks';E=OUT/'evidence'
grid=np.fromfile(G/'data/layouts/JohtoRoute32/map.bin','<u2').reshape(128,32);t=Tileset(G,'route32','route32');beh=np.array([t.attrs[int(v>=512)][v-512 if v>=512 else v]&255 for v in (grid&1023).ravel()]).reshape(grid.shape);solid=((grid&0xc00)!=0)|np.isin(beh,[16,21]);solid[beh==105]=True;solid[beh==97]=True

def path(start,goal):
 q=deque([start]);parent={start:None}
 while q:
  x,y=q.popleft()
  if (x,y)==goal:break
  for dx,dy,key in [(0,-1,'UP'),(1,0,'RIGHT'),(-1,0,'LEFT'),(0,1,'DOWN')]:
   xx,yy=x+dx,y+dy
   if not(0<=xx<32 and 0<=yy<128) or solid[yy,xx]:continue
   if (xx,yy) not in parent:parent[xx,yy]=((x,y),key);q.append((xx,yy))
 assert goal in parent,('Destination blocked',start,goal)
 steps=[];node=goal
 while parent[node] is not None:prev,key=parent[node];steps.append((key,*node));node=prev
 return steps[::-1]
legs=[];walk=[];current=(23,3)
goals=[('north-grass',(27,12)),('upper-terrace',(25,25)),('central-grass',(24,36)),('middle-clearing',(21,42)),('western-grass',(10,47)),('cliff-lane',(7,57)),('northern-stairs',(9,59)),('dock-approach',(19,64)),('railway-dock-underpass',(19,68)),('fishing-arm',(14,75)),('dock-bend',(21,80)),('dock-south',(22,86)),('southern-clearing',(21,92)),('center-approach',(20,109)),('union-cave-approach',(14,118))]
for name,goal in goals:
 steps=path(current,goal);legs.append({'name':name,'start':current,'goal':goal,'steps':len(steps)})
 for key,x,y in steps:walk.append(f'step({key},1);at(43,{x},{y},"{name}");')
 walk.append(f'shot("{name}");');current=goal
# Alternate western branch must also be connected by normal walking.
walk.append('go(43,5,65);shot("western-rail-approach");');current=(5,65)
for name,goal in [('railway-land-underpass',(5,68)),('western-fishing-grass',(4,81)),('southern-stairs',(7,90)),('land-route-rejoins',(15,96))]:
 steps=path(current,goal);legs.append({'name':name,'start':current,'goal':goal,'steps':len(steps)})
 for key,x,y in steps:walk.append(f'step({key},1);at(43,{x},{y},"{name}");')
 walk.append(f'shot("{name}");');current=goal
(E/'walk-plan.json').write_text(json.dumps(legs,indent=2)+'\n')
# Probe actual blocked tree/cliff/water neighbors at each source region.
checks=[]
# Fixed probes are tied to reviewed HGSS cells, not an arbitrary generated wall.
source_probes=[('cave-boulder-footprint',22,119,'UP',22,118),('western-woodland-footprint',4,80,'RIGHT',5,80),
 ('forest-behind-center',16,104,'UP',16,103),
 ('ew-stair-lower-corner',8,61,'RIGHT',9,61),
 ('ew-stair-upper-corner',10,60,'UP',10,59)]
for name,x,y,key,bx,by in source_probes:
 assert not solid[y,x] and solid[by,bx],(name,(x,y),(bx,by))
 checks.append(f'go(43,{x},{y});step({key},1);at(43,{x},{y},"{name}");shot("{name}");')

for lo,hi in [(5,25),(25,50),(50,65),(70,88),(92,115)]:
 found=None
 for y in range(lo,hi):
  for x in range(2,30):
   if solid[y,x] or beh[y,x]:continue
   for dx,dy,key in [(1,0,'RIGHT'),(-1,0,'LEFT'),(0,-1,'UP'),(0,1,'DOWN')]:
    if solid[y+dy,x+dx] and beh[y+dy,x+dx] not in [59,97,105]:found=(x,y,key);break
   if found:break
  if found:break
 if found:
  x,y,key=found;checks.append(f'go(43,{x},{y});step({key},1);at(43,{x},{y},"barrier-{lo}");')
r.MAIN=r.MAIN[:r.MAIN.index('  // Actual east connection')]+ 'go(43,23,3);shot("northern-approach");\n'+'\n'.join(walk)+r'''
 go(43,20,109);step(UP,1);frames(360,0);observe("center-entry");need(state[2]==44,"center-entry");shot("center-interior");step(DOWN,1);frames(360,0);at(43,20,109,"center-return");shot("center-return");
 go(43,14,118);step(UP,1);frames(360,0);observe("cave-entry");need(state[2]==46,"cave-entry");shot("cave-entry-room");step(DOWN,1);frames(360,0);at(43,14,117,"cave-return");step(DOWN,1);at(43,14,118,"cave-clear-exit");shot("cave-return");
'''+ '\n'.join(checks)+r'''
 go(43,8,60);step(RIGHT,3);at(43,11,60,"east-west-stairs-up");shot("east-west-stairs");step(LEFT,3);at(43,8,60,"east-west-stairs-down");
 go(43,7,86);step(DOWN,4);at(43,7,90,"north-south-stairs-down");shot("north-south-stairs");step(UP,4);at(43,7,86,"north-south-stairs-up");
 go(43,15,118);step(UP,1);frames(360,0);observe("cave-right-entry");need(state[2]==46,"cave-right-entry");step(DOWN,1);frames(360,0);at(43,14,117,"cave-right-return");step(DOWN,1);
 go(43,25,26);step(DOWN,1);at(43,25,28,"terrace-downhill-ledge");step(UP,1);at(43,25,28,"terrace-uphill-blocked");shot("native-ledge");
 go(43,21,119);step(RIGHT,1);at(43,22,119,"floor-below-cave-boulder");shot("cave-boulder-clearance");
 go(43,27,12);step(DOWN,1);step(UP,1);at(43,27,12,"native-grass-walking");shot("grass-walking");
 go(43,19,68);shot("save-under-railway");unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
 }
 c->deinit(c);return 0;
}
'''
r.MAIN=r.MAIN.replace('11,27,18','43,19,68').replace('cold-reload-new-bark','cold-reload-route32')
if __name__=='__main__':r.main()
