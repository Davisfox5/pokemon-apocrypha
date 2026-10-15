"""Native Union Cave 1F walk, barriers, entrance and ordinary save checks."""
from pathlib import Path
from collections import deque
import sys,json
import numpy as np
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent));from johto_connections import runtime as r
G=Path(sys.argv[1]);E=HERE.parents[3]/'gba/art/union-cave-1f/evidence';grid=np.fromfile(G/'data/layouts/UnionCaveRoute32Entrance/map.bin','<u2').reshape(60,34);solid=(grid&0xc00)!=0;solid[19,28]=True

def path(start,goal):
 q=deque([start]);parent={start:None}
 while q:
  x,y=q.popleft()
  if (x,y)==goal:break
  for dx,dy,k in [(0,-1,'UP'),(1,0,'RIGHT'),(-1,0,'LEFT'),(0,1,'DOWN')]:
   xx,yy=x+dx,y+dy
   if 0<=xx<34 and 0<=yy<60 and not solid[yy,xx] and (xx,yy) not in parent:parent[xx,yy]=((x,y),k);q.append((xx,yy))
 assert goal in parent,('Blocked tour goal',goal)
 out=[];p=goal
 while parent[p] is not None:prev,k=parent[p];out.append((k,*p));p=prev
 return out[::-1]
steps=[];legs=[];current=(28,18)
goals=[('northern-junction',(5,18)),('northwest-pocket',(4,12)),('north-chamber',(8,5)),('northern-staircase',(6,16)),('central-pool-bank',(20,23)),('east-bend',(29,26)),('east-corridor',(29,33)),('middle-chamber',(20,35)),('southern-staircase',(29,38)),('southern-pool-east',(18,41)),('southern-lake-bend',(17,44)),('southern-lake-bank',(13,47)),('southwest-pocket',(4,48)),('southern-junction',(23,49)),('southeast-chamber',(29,53)),('route33-exit-location',(28,57)),('cave-save',(27,56))]
for tag,goal in goals:
 leg=path(current,goal);legs.append({'name':tag,'from':current,'to':goal,'steps':len(leg)})
 for k,x,y in leg:steps.append(f'step({k},1);at(46,{x},{y},"{tag}");')
 steps.append(f'shot("{tag}");');current=goal
(E/'walk-plan.json').write_text(json.dumps(legs,indent=2)+'\n')
start=r.MAIN[:r.MAIN.index('  // Actual east connection')];end=r.MAIN[r.MAIN.index('  unsigned status=call("TrySavingData"'):]
r.MAIN=start+r'''
 go(43,14,118);step(UP,1);frames(360,0);observe("route32-cave-entry");need(state[2]==46,"route32-cave-entry");shot("route32-cave-entry");
 go(46,28,18);step(DOWN,1);frames(360,0);at(43,14,117,"cave-to-route32");step(DOWN,1);at(43,14,118,"route32-clear-door");shot("route32-return");
 go(43,15,118);step(UP,1);frames(360,0);observe("second-entrance-cell");need(state[2]==46,"second-entrance-cell");
 go(46,28,18);
'''+ '\n'.join(steps)+r'''
 go(46,22,25);shot("stalagmite-overlap");step(DOWN,1);at(46,22,25,"stalagmite-root-blocks");shot("stalagmite-root-blocks");
 go(46,9,21);step(RIGHT,1);at(46,9,21,"central-water-blocks-foot");shot("water-barrier");
 go(46,4,12);step(LEFT,1);at(46,3,12,"west-floor-approach");step(LEFT,1);at(46,3,12,"west-rock-wall-blocks");shot("rock-barrier");
 go(46,27,56);at(46,27,56,"save-in-union-cave");shot("save-in-union-cave");
'''+end
r.MAIN=r.MAIN.replace('at(11,27,18','at(46,27,56').replace('cold-reload-new-bark','cold-reload-union-cave')
if __name__=='__main__':r.main()
