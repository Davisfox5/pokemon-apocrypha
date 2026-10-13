#!/usr/bin/env python3
"""Headless ordinary-input tour and physical barrier checks for the HGSS survey."""
import sys,json
from pathlib import Path
from collections import deque
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent))
from tiles import Tileset
from johto_connections import runtime as r
G=Path(sys.argv[1]).resolve();OUT=ROOT/'gba/art/route30-hgss-blocks'
grid=np.fromfile(G/'data/layouts/CherrygroveRoute30Approach/map.bin',dtype='<u2').reshape(86,35)
t=Tileset(G,'claude_route30','cherrygrove');solid=(grid&0xc00)!=0
beh=np.array([t.attrs[int(v>=512)][v-512 if v>=512 else v]&255 for v in (grid&1023).ravel()]).reshape(grid.shape)
plan=np.load(OUT/'source/plan.npy')
def path(start,goal):
 q=deque([start]);parent={start:None}
 while q:
  x,y=q.popleft()
  if (x,y)==goal:break
  for dx,dy,key in [(0,-1,'UP'),(1,0,'RIGHT'),(-1,0,'LEFT'),(0,1,'DOWN')]:
   xx,yy=x+dx,y+dy
   if not 0<=xx<35 or not 0<=yy<86:continue
   if solid[yy,xx]:
    if dy==1 and beh[yy,xx]==59 and yy+1<86 and not solid[yy+1,xx]:yy+=1
    else:continue
   if (xx,yy) not in parent:parent[xx,yy]=((x,y),key);q.append((xx,yy))
 assert goal in parent,('Required HGSS destination is not reachable',start,goal)
 result=[];node=goal
 while parent[node] is not None:
  prev,key=parent[node];result.append((key,*node));node=prev
 return result[::-1]
walk=[];legs=[];current=(8,85)
for name,goal in [('southern-house',(16,53)),('grass-landmark',(20,44)),('mr-pokemon-house',(27,6)),('violet-approach',(10,0))]:
 steps=path(current,goal);legs.append({'name':name,'start':current,'goal':goal,'steps':steps})
 for i,(key,x,y) in enumerate(steps):
  walk.append(f' step({key},1);at(10,{x},{y},"{name}-{i:03}");')
  if i%16==0:walk.append(f' shot("walk-{name}-{i:03}");')
 walk.append(f' shot("{name}");')
 if name in ['southern-house','mr-pokemon-house']:walk.append(f' step(UP,1);at(10,{goal[0]},{goal[1]},"{name}-door-still-closed");')
 current=goal
(OUT/'evidence/walk-plan.json').write_text(json.dumps(legs,indent=2)+'\n')
barriers=[]
for lo,hi in [(7,20),(22,33),(35,46),(48,62),(64,74)]:
 candidate=[]
 for y in range(lo,hi):
  for x in range(1,34):
   if solid[y,x] or beh[y,x]!=0:continue
   for dx,dy,key in [(1,0,'RIGHT'),(-1,0,'LEFT'),(0,1,'DOWN'),(0,-1,'UP')]:
    if plan[y+dy,x+dx] in ('T','#') and solid[y+dy,x+dx] and beh[y+dy,x+dx]!=59:candidate.append((x,y,key,x+dx,y+dy))
 if candidate:barriers.extend([candidate[0],candidate[-1]])
checks='\n'.join(f' go(10,{x},{y});step({key},1);at(10,{x},{y},"blocked-{xx}-{yy}");' for x,y,key,xx,yy in barriers)
(OUT/'evidence/barrier-probes.json').write_text(json.dumps(barriers,indent=2)+'\n')
r.MAIN=r.MAIN[:r.MAIN.index('  // Actual east connection')]+r'''
 go(0,43,0);shot("cherrygrove-north-seam");step(UP,1);at(10,8,85,"cherrygrove-to-route30");shot("route30-south-seam");
 step(DOWN,1);at(0,43,0,"route30-to-cherrygrove");step(UP,1);at(10,8,85,"tour-start");
'''+ '\n'.join(walk)+r'''
 step(UP,1);at(29,38,29,"route30-to-route31");shot("route31-south-seam");step(DOWN,1);at(10,10,0,"route31-to-route30");shot("route30-north-seam");
 go(29,38,27);shot("north-crossing-before");step(DOWN,1);shot("north-crossing-28");step(DOWN,1);shot("north-crossing-29");step(DOWN,1);at(10,10,0,"north-crossing-load");shot("north-crossing-00");step(DOWN,1);shot("north-crossing-01");step(DOWN,1);shot("north-crossing-02");
 go(10,18,6);step(DOWN,1);at(10,18,6,"original-cut-barrier-blocks");shot("original-cut-barrier");
 go(10,10,3);step(DOWN,1);at(10,10,5,"northern-ledge-downhill");step(UP,1);at(10,10,5,"northern-ledge-blocks-uphill");shot("northern-ledge");
 go(10,13,22);step(UP,1);at(10,13,21,"HGSS-ledge-bypass-under-canopy");shot("ledge-bypass-canopy");step(RIGHT,1);at(10,13,21,"divider-trunk-blocks");
 go(10,10,20);step(DOWN,1);at(10,10,22,"ledge-downhill");step(UP,1);at(10,10,22,"ledge-blocks-uphill");
 go(10,20,54);step(RIGHT,1);at(10,20,54,"upper-pond-bank-blocks");shot("upper-pond");
 go(10,20,44);for(int i=0;i<10;i++){step(RIGHT,1);at(10,21,44,"native-grass-right");step(LEFT,1);at(10,20,44,"native-grass-left");}shot("native-grass-walking");
 read_sign(10,8,24,"northern-sign");read_sign(10,20,34,"mr-pokemon-direction-sign");read_sign(10,13,58,"southern-sign");
'''+checks+r'''
 go(10,16,53);shot("save-at-route30");
 unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
 }
 c->deinit(c);return 0;
}
'''
r.MAIN=r.MAIN.replace('11,27,18','10,16,53').replace('cold-reload-new-bark','cold-reload-route30')
if __name__=='__main__':r.main()
