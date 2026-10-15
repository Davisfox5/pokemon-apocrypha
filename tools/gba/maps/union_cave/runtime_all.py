"""Native cave-floor traversal, original stair pairs, water gates and normal saves.
Controlled proof warps onto water initialize the engine's existing Surf state;
this tests map water movement/disembark, not campaign HM acquisition/badge gates.
"""
from pathlib import Path
from collections import deque
import sys,json
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent));from config import FLOORS
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent));from johto_connections import runtime as r
G=Path(sys.argv[1]);save_key='b2f'
if '--save-floor' in sys.argv:
 i=sys.argv.index('--save-floor');save_key=sys.argv[i+1];del sys.argv[i:i+2]
ROOT=HERE.parents[3];E=ROOT/'gba/art/union-cave-1f/evidence';grids={};plans={}
for key,c in FLOORS.items():
 W,H=c['size'];grids[key]=np.fromfile(G/'data/layouts'/c['name']/'map.bin','<u2').reshape(H,W);plans[key]=np.load(ROOT/f'gba/art/union-cave-{key}/source/native-material-grid.npy')
legs=[]
def path(key,start,goal,surf=False,allow_warp=None):
 c=FLOORS[key];g=grids[key];p=plans[key];W,H=c['size'];warps={(x,y) for x,y,dm,di in c['warps']};q=deque([(start[0],start[1],surf)]);parent={q[0]:None};end=None
 while q:
  node=q.popleft();x,y,wet=node
  if (x,y)==goal:end=node;break
  for dx,dy,k in [(0,-1,'UP'),(1,0,'RIGHT'),(-1,0,'LEFT'),(0,1,'DOWN')]:
   xx,yy=x+dx,y+dy
   if not(0<=xx<W and 0<=yy<H):continue
   water=p[yy,xx]=='W'
   if g[yy,xx]&0xc00 and not(wet and water):continue
   if water and not wet:continue
   if (xx,yy) in warps and (xx,yy)!=allow_warp:continue
   nxt=(xx,yy,bool(wet and water))
   if nxt not in parent:parent[nxt]=(node,k);q.append(nxt)
 assert end is not None,('No source-consistent route',key,start,goal,surf)
 out=[];node=end
 while parent[node] is not None:prev,k=parent[node];out.append((k,node[0],node[1]));node=prev
 return out[::-1]
steps=[]
def leg(key,start,goal,tag,surf=False):
 c=FLOORS[key];s=path(key,start,goal,surf);legs.append({'floor':key,'from':start,'to':goal,'tag':tag,'steps':len(s),'initial_proof_Surf':surf})
 for k,x,y in s:steps.append(f'step({k},1);at({c["map_num"]},{x},{y},"{tag}");')
 steps.append(f'shot("{tag}");')
 return goal
# Main floor remains walkable through the original northern route.
current=(28,18)
for tag,goal in [('1f-small-rock-formations',(24,18)),('1f-west-rock-edge',(7,16)),('1f-north-stair-approach',(5,6)),('1f-central-grassless-floor',(20,23)),('1f-main-bend',(29,26)),('1f-south-boulder-approach',(28,38)),('1f-lake-bank',(13,47)),('1f-southern-doorway',(28,57))]:current=leg('1f',current,goal,tag)
steps.append('go(46,5,6);step(UP,1);frames(240,0);at(47,31,35,"north-stairs-descend");shot("b1f-main-entrance");step(LEFT,1);at(47,30,35,"b1f-step-off-stairs");step(RIGHT,1);frames(240,0);at(46,5,5,"north-stairs-ascend");step(DOWN,1);at(46,5,6,"north-stair-clear");shot("1f-northern-stairs");')
# Water-separated southern 1F pocket -> western B1F lower chamber.
steps.append('go(46,6,54);need(c->busRead8(c,sym("gPlayerAvatar"))&8,"1f-proof-Surf");shot("1f-Surf-pocket");')
leg('1f',(6,54),(7,56),'1f-southern-pocket-land',True)
steps.append('need(!(c->busRead8(c,sym("gPlayerAvatar"))&8),"1f-Surf-disembark");step(DOWN,1);frames(240,0);at(47,4,48,"south-stairs-descend");shot("b1f-lower-west-entry");step(RIGHT,1);at(47,5,48,"lower-west-step-off");step(LEFT,1);frames(240,0);at(46,7,57,"south-stairs-ascend");step(UP,1);at(46,7,56,"southern-stair-clear");shot("1f-southern-stairs");')
# Existing Surf movement across the lower B1F pool, then the real B2F staircase.
steps.append('go(47,20,47);need(c->busRead8(c,sym("gPlayerAvatar"))&8,"b1f-proof-Surf");shot("b1f-lower-Surf");')
leg('b1f',(20,47),(29,47),'b1f-lower-east-bank',True)
steps.append('need(!(c->busRead8(c,sym("gPlayerAvatar"))&8),"b1f-Surf-disembark");step(UP,1);frames(240,0);at(48,4,5,"b1f-to-b2f");shot("b2f-entrance");step(DOWN,1);at(48,4,6,"b2f-step-off-stairs");step(UP,1);frames(240,0);at(47,29,46,"b2f-to-b1f");step(DOWN,1);at(47,29,47,"b1f-clear-b2f-stair");')
# B1F's upper branch genuinely requires Surf from its main entrance region.
steps.append('go(47,25,29);need(c->busRead8(c,sym("gPlayerAvatar"))&8,"b1f-main-proof-Surf");')
current=leg('b1f',(25,29),(26,23),'b1f-main-lake-land',True)
for tag,goal in [('b1f-east-rocks',(26,19)),('b1f-north-gallery',(16,5)),('b1f-upper-unwired-Alph-stair',(5,5))]:current=leg('b1f',current,goal,tag)
steps.append('go(47,7,12);step(RIGHT,1);at(47,7,12,"original-strength-rock-blocks");shot("b1f-strength-rock");')
# Qualify each represented B2F landmass by normal Surf input and disembark.
for tag,goal in [('b2f-north-bank',(6,7)),('b2f-northeast-pocket',(27,8)),('b2f-west-peninsula',(7,19)),('b2f-western-gallery',(6,28)),('b2f-east-gallery',(28,25)),('b2f-south-peninsula',(24,32))]:
 steps.append('go(48,10,15);need(c->busRead8(c,sym("gPlayerAvatar"))&8,"b2f-proof-Surf");')
 leg('b2f',(10,15),goal,tag,True);steps.append(f'need(!(c->busRead8(c,sym("gPlayerAvatar"))&8),"{tag}-disembark");')
steps.append('go(48,15,40);need(c->busRead8(c,sym("gPlayerAvatar"))&8,"b2f-southern-lake-Surf");shot("b2f-southern-lake");')
leg('b2f',(15,40),(6,38),'b2f-southern-lake-land',True)
steps+=['go(46,7,16);step(LEFT,1);at(46,7,16,"1f-north-boulder-blocks");shot("1f-north-boulder");','go(46,28,38);step(RIGHT,1);at(46,28,38,"1f-south-boulder-blocks");shot("1f-south-boulder");','go(48,6,8);step(DOWN,1);at(48,6,8,"b2f-low-bank-water-blocks-foot");shot("b2f-low-shore");']
(E/'all-floors-walk-plan.json').write_text(json.dumps(legs,indent=2)+'\n')
start=r.MAIN[:r.MAIN.index('  // Actual east connection')];end=r.MAIN[r.MAIN.index('  unsigned status=call("TrySavingData"'):];mapnum,x,y={'1f':(46,27,56),'b1f':(47,30,35),'b2f':(48,4,6)}[save_key]
entry=r'''
 go(43,14,118);step(UP,1);frames(300,0);at(46,28,19,"route32-entry-threshold");step(UP,1);at(46,28,18,"route32-entry-floor");shot("1f-route32-entrance");
 go(46,28,18);step(DOWN,2);frames(300,0);at(43,14,117,"route32-return");step(DOWN,1);at(43,14,118,"route32-clear-door");
 go(43,15,118);step(UP,1);frames(300,0);at(46,28,19,"route32-second-cell-threshold");step(UP,1);at(46,28,18,"route32-second-cell-floor");
'''
r.MAIN=start+(entry+'\n'.join(steps) if save_key=='b2f' else '')+f'go({mapnum},{x},{y});at({mapnum},{x},{y},"save-{save_key}");shot("save-{save_key}");\n'+end
r.MAIN=r.MAIN.replace('at(11,27,18',f'at({mapnum},{x},{y}').replace('cold-reload-new-bark','cold-reload-'+save_key)
if __name__=='__main__':r.main()
