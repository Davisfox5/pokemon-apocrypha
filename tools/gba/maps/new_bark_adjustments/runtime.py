"""Ordinary-input town tour, all eight door returns, seven mailbox barriers and saves."""
from pathlib import Path
import sys,json,re
from collections import deque
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent))
from johto_connections import runtime as r
from tiles import Tileset
G=Path(sys.argv[1]);E=ROOT/'gba/art/new-bark-adjustments/evidence';t=Tileset(G,'new_bark','cherrygrove');g=np.fromfile(G/'data/layouts/NewBarkTown/map.bin','<u2').reshape(53,36);solid=(g&0xc00)!=0;beh=np.array([t.attrs[int(v>=512)][int(v)%512]&255 for v in (g&1023).ravel()]).reshape(g.shape);solid|=np.isin(beh,[16,105])
m=json.loads((G/'data/maps/NewBarkTown/map.json').read_text());hdr=(G/'include/constants/map_groups.h').read_text();ids={name:int(n) for name,n in re.findall(r'(MAP_NEW_BARK_\w+)\s*=\s*\((\d+) \|',hdr)}
def walk(start,goal):
 q=deque([start]);parents={start:None}
 while q:
  x,y=q.popleft()
  if (x,y)==goal:break
  for dx,dy,key in [(0,-1,'UP'),(1,0,'RIGHT'),(0,1,'DOWN'),(-1,0,'LEFT')]:
   a,b=x+dx,y+dy
   if 0<=a<36 and 0<=b<53 and not solid[b,a] and (a,b) not in parents:parents[a,b]=((x,y),key);q.append((a,b))
 assert goal in parents,('Unreachable',start,goal)
 result=[];p=goal
 while parents[p]:prev,key=parents[p];result.append((key,*p));p=prev
 return result[::-1]
current=(0,15);tour=[];plan=[]
for i,d in enumerate(m['warp_events']):
 goal=(d['x'],d['y']+1);steps=walk(current,goal);plan.append({'warp':i,'front':goal,'steps':steps})
 for j,(key,x,y) in enumerate(steps):tour.append(f' step({key},1);at(28,{x},{y},"door-{i}-walk-{j}");')
 tour.append(f' shot("house-{i}-exterior");step(UP,1);frames(360,0);observe("door-{i}-entry");need(state[2]=={ids[d["dest_map"]]},"door-{i}-entry");shot("door-{i}-inside");step(DOWN,1);frames(360,0);at(28,{goal[0]},{goal[1]},"door-{i}-return");shot("door-{i}-return");')
 current=goal
mailboxes=json.loads((E/'edit.json').read_text())['mailboxes']
for i,(x,y) in enumerate(mailboxes):
 for key,a,b in walk(current,(x,y+1)):tour.append(f' step({key},1);at(28,{a},{b},"mailbox-{i}-walk");')
 tour.append(f' step(UP,1);at(28,{x},{y+1},"mailbox-{i}-blocked");shot("mailbox-{i}");');current=(x,y+1)
for key,x,y in walk(current,(16,44)):tour.append(f' step({key},1);at(28,{x},{y},"bottom-forest-walk");')
tour.append(' step(DOWN,1);at(28,16,44,"bottom-complete-trees-block");shot("bottom-complete-trees");');current=(16,44)
for key,x,y in walk(current,(0,15)):tour.append(f' step({key},1);at(28,{x},{y},"town-return-walk");')
(E/'walk-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
r.MAIN=r.MAIN[:r.MAIN.index('  // Actual east connection')]+'''
 go(9,97,18);step(RIGHT,1);at(28,0,15,"route29-to-new-bark");shot("west-connection");
'''+ '\n'.join(tour)+r'''
 step(LEFT,1);at(9,97,18,"new-bark-to-route29");step(RIGHT,1);at(28,0,15,"new-bark-return");
 go(28,23,3);step(UP,1);at(28,23,3,"north-forest-block");shot("trees-behind-lab");
 go(28,11,9);step(UP,1);at(28,11,9,"lab-left-trees-block");shot("lab-left-trees");
 go(28,23,9);step(LEFT,1);at(28,23,9,"lab-side-block");
 go(28,17,10);shot("save-at-new-bark");unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
 }
 c->deinit(c);return 0;
}
'''
r.MAIN=r.MAIN.replace('11,27,18','28,17,10')
if __name__=='__main__':r.main()
