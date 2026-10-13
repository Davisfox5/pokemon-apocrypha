#!/usr/bin/env python3
"""Headless normal-input Route 29 tour, connection and save proof."""
from pathlib import Path
import sys,json
from collections import deque
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent))
from tiles import Tileset
from johto_connections import runtime as r
G=Path(sys.argv[1]);OUT=ROOT/'gba/art/route29-hgss-blocks';E=OUT/'evidence'
grid=np.fromfile(G/'data/layouts/CherrygroveRoute29Approach/map.bin','<u2').reshape(48,98);t=Tileset(G,'claude_route29','cherrygrove')
beh=np.array([t.attrs[int(v>=512)][v-512 if v>=512 else v]&255 for v in (grid&1023).ravel()]).reshape(grid.shape);solid=((grid&0xc00)!=0)|(beh==16)
def path(start,goal):
 q=deque([start]);parent={start:None}
 while q:
  x,y=q.popleft()
  if (x,y)==goal:break
  for dx,dy,key in [(0,-1,'UP'),(1,0,'RIGHT'),(-1,0,'LEFT'),(0,1,'DOWN')]:
   xx,yy=x+dx,y+dy
   if not(0<=xx<98 and 0<=yy<48):continue
   if solid[yy,xx]:
    if dy==1 and beh[yy,xx]==59 and yy+1<48 and not solid[yy+1,xx]:yy+=1
    else:continue
   if (xx,yy) not in parent:parent[xx,yy]=((x,y),key);q.append((xx,yy))
 assert goal in parent,('Destination blocked',start,goal)
 steps=[];node=goal
 while parent[node] is not None:prev,key=parent[node];steps.append((key,*node));node=prev
 return steps[::-1]
walk=[];legs=[];current=(0,18)
for name,goal in [('apricorn-clearing',(21,14)),('western-grass',(33,15)),('route46-gate',(52,12)),('northern-grass',(66,12)),('eastern-grass',(70,20)),('coastal-lookout',(62,27)),('new-bark-approach',(97,18))]:
 steps=path(current,goal);legs.append({'name':name,'start':current,'goal':goal,'steps':steps})
 for i,(key,x,y) in enumerate(steps):
  walk.append(f' step({key},1);at(9,{x},{y},"{name}-{i:03}");')
  if i%16==0:walk.append(f' shot("walk-{name}-{i:03}");')
 walk.append(f' shot("{name}");')
 if name=='route46-gate':walk.append(' step(UP,1);at(9,52,12,"gate-door-closed");')
 current=goal
(E/'walk-plan.json').write_text(json.dumps(legs,indent=2)+'\n')
probes=[]
for lo,hi in [(10,25),(25,45),(45,65),(65,85)]:
 candidates=[]
 for y in range(9,29):
  for x in range(lo,hi):
   if solid[y,x] or beh[y,x]:continue
   for dx,dy,key in [(1,0,'RIGHT'),(-1,0,'LEFT'),(0,-1,'UP'),(0,1,'DOWN')]:
    if solid[y+dy,x+dx] and beh[y+dy,x+dx]!=59:candidates.append((x,y,key,x+dx,y+dy))
 if candidates:probes.extend([candidates[0],candidates[-1]])
checks='\n'.join(f' go(9,{x},{y});step({key},1);at(9,{x},{y},"barrier-{xx}-{yy}");' for x,y,key,xx,yy in probes)
(E/'barrier-probes.json').write_text(json.dumps(probes,indent=2)+'\n')
r.MAIN=r.MAIN[:r.MAIN.index('  // Actual east connection')]+r'''
 go(0,79,18);shot("cherrygrove-east-seam");step(RIGHT,1);at(9,0,18,"cherrygrove-to-route29");shot("route29-west-seam");step(LEFT,1);at(0,79,18,"route29-to-cherrygrove");step(RIGHT,1);at(9,0,18,"tour-start");
'''+ '\n'.join(walk)+r'''
 step(RIGHT,1);at(28,0,12,"route29-to-new-bark");shot("new-bark-west-seam");step(LEFT,1);at(9,97,18,"new-bark-to-route29");shot("route29-east-seam");
 go(9,94,18);shot("east-crossing-before");for(int i=0;i<5;i++){step(RIGHT,1);char tag[80];sprintf(tag,"east-crossing-%d",i);shot(tag);}
 go(9,24,15);step(DOWN,1);at(9,24,17,"western-ledge-downhill");step(UP,1);at(9,24,17,"western-ledge-blocks-uphill");shot("western-ledge");
 go(9,60,23);step(DOWN,1);at(9,60,25,"central-ledge-downhill");step(UP,1);at(9,60,25,"central-ledge-blocks-uphill");shot("central-ledge");
 go(9,66,12);for(int i=0;i<10;i++){step(RIGHT,1);at(9,67,12,"grass-right");step(LEFT,1);at(9,66,12,"grass-left");}shot("native-grass-walking");
 read_sign(9,12,17,"western-route-sign");read_sign(9,87,16,"eastern-route-sign");
'''+checks+r'''
 go(9,52,12);shot("save-at-route29");unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
 }
 c->deinit(c);return 0;
}
'''
r.MAIN=r.MAIN.replace('11,27,18','9,52,12').replace('cold-reload-new-bark','cold-reload-route29')
if __name__=='__main__':r.main()
