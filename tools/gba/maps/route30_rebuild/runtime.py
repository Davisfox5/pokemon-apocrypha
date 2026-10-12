#!/usr/bin/env python3
"""Headless ordinary-input Route 30 travel, grass, signs, collision and save proof."""
import sys,json
from pathlib import Path
from collections import deque
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from johto_connections import runtime as r
from tiles import Tileset
import numpy as np
G=Path(sys.argv[1]);grid=np.frombuffer((G/'data/layouts/CherrygroveRoute30Approach/map.bin').read_bytes(),'<u2').reshape(86,35)
t=Tileset(G,'claude_route30','cherrygrove');solid=(grid&0xC00)!=0
beh=np.array([t.attrs[int(v>=512)][v-512 if v>=512 else v]&255 for v in (grid&1023).ravel()]).reshape(grid.shape)
start=(8,85);goal=(10,0);queue=deque([start]);parents={start:None}
while queue:
 x,y=queue.popleft()
 if (x,y)==goal:break
 for dx,dy,key in [(0,-1,'UP'),(-1,0,'LEFT'),(1,0,'RIGHT'),(0,1,'DOWN')]:
  xx,yy=x+dx,y+dy
  if not (0<=xx<35 and 0<=yy<86):continue
  if solid[yy,xx]:
   if dy==1 and beh[yy,xx]==59 and yy+1<86 and not solid[yy+1,xx]:yy+=1
   else:continue
  if (xx,yy) not in parents:parents[xx,yy]=((x,y),key);queue.append((xx,yy))
assert goal in parents,'No ordinary land path from Cherrygrove to Route 31'
steps=[];node=goal
while parents[node] is not None:
 prev,key=parents[node];steps.append((key,node));node=prev
steps.reverse();walk=[]
for i,(key,(x,y)) in enumerate(steps):
 walk.append(f'  step({key},1);at(10,{x},{y},"continuous-route30-{i:03}");')
 if i%12==0:walk.append(f'  shot("continuous-route30-{i:03}");')
Path('/workspace/scratch/route30-walk-plan.json').write_text(json.dumps({'start':start,'goal':goal,'steps':steps},indent=2)+'\n')
r.MAIN=r.MAIN[:r.MAIN.index('  // Actual east connection')]+r'''
  go(0,43,0);shot("cherrygrove-north-seam");step(UP,1);at(10,8,85,"cherrygrove-to-route30");shot("route30-south-seam");
  step(DOWN,1);at(0,43,0,"route30-to-cherrygrove");step(UP,1);at(10,8,85,"route30-walk-start");
'''+ '\n'.join(walk)+r'''
  shot("route30-north-seam");step(UP,1);at(29,38,29,"route30-to-route31");shot("route31-south-seam");step(DOWN,1);at(10,10,0,"route31-to-route30");
  go(10,26,8);shot("mr-pokemon-house");go(10,12,54);shot("southern-house");go(10,10,30);shot("middle-stair-landing");go(10,19,64);shot("southern-stairs");
  go(10,23,44);shot("inside-new-grass");for(int i=0;i<10;i++){step(RIGHT,2);at(10,25,44,"grass-right");step(LEFT,2);at(10,23,44,"grass-left");}shot("grass-walking");
  go(10,20,54);step(RIGHT,1);at(10,20,54,"pond-bank-blocks");shot("freshwater-pond");
  go(10,10,19);step(DOWN,1);at(10,10,21,"ledge-jump-down");step(UP,1);at(10,10,21,"ledge-blocks-uphill");
  read_sign(10,20,34,"mr-pokemon-direction-sign");read_sign(10,13,58,"route30-sign");
  go(10,12,54);shot("save-at-route30");
  unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
 }
 c->deinit(c);return 0;
}
'''
# Test access restrictions at independent forest/cliff edges, not just travel.
plan=np.load(Path(__file__).resolve().parents[4]/'gba/art/route30-rebuild/source/plan.npy')
barrier_checks=[]
for lo,hi in [(3,18),(18,33),(33,48),(48,63),(63,70)]:
 candidates=[]
 for y in range(lo,hi):
  for x in range(1,34):
   if solid[y,x] or beh[y,x]!=0:continue
   for dx,dy,key in [(1,0,'RIGHT'),(-1,0,'LEFT'),(0,1,'DOWN'),(0,-1,'UP')]:
    xx,yy=x+dx,y+dy
    if plan[yy,xx] in ('T','#') and solid[yy,xx] and beh[yy,xx]!=59:
     candidates.append((x,y,key,xx,yy))
 if candidates:
  for candidate in [candidates[0],candidates[-1]]:
   x,y,key,xx,yy=candidate;barrier_checks.append(candidate)
   check=f'  go(10,{x},{y});step({key},1);at(10,{x},{y},"original-barrier-{xx}-{yy}");\n'
   r.MAIN=r.MAIN.replace('  go(10,12,54);shot("save-at-route30");',check+'  go(10,12,54);shot("save-at-route30");')
Path('/workspace/scratch/route30-barrier-probes.json').write_text(json.dumps(barrier_checks,indent=2)+'\n')
r.MAIN=r.MAIN.replace('11,27,18','10,12,54')
if __name__=='__main__':r.main()
