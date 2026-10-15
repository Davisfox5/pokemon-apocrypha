"""Gate approach connectivity, tree footprints, artwork and preservation checks."""
from pathlib import Path
import json,sys,subprocess
from collections import deque
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from tiles import Tileset
OUT=ROOT/'gba/art/route36/gate-surround';E=OUT/'evidence';BASE='162c41c8b5987973480f7a276e63a196dfc1bf07'
G=Path(sys.argv[1]);grid=np.fromfile(G/'data/layouts/JohtoRoute36/map.bin','<u2').reshape(32,82);solid=(grid&0xc00)!=0;t=Tileset(G,'johto_route36','johto_route36')
attrs=np.array([[t.attrs[int(v>=512)][int(v%512)] for v in row&1023] for row in grid]);expected=np.load(OUT/'source/attributes.npy');assert np.array_equal(attrs,expected)
image=np.array(t.map_image(grid.ravel().tolist(),82));assert np.array_equal(image,np.array(Image.open(E/'native-overview.png')))
def walk(start,end):
 q=deque([start]);prev={start:None}
 while q:
  x,y=q.popleft()
  for dx,dy,key in [(0,-1,'UP'),(0,1,'DOWN'),(-1,0,'LEFT'),(1,0,'RIGHT')]:
   p=xx,yy=x+dx,y+dy
   if 0<=xx<82 and 0<=yy<32 and not solid[yy,xx] and p not in prev:prev[p]=((x,y),key);q.append(p)
 assert end in prev,('Unreachable',end)
 steps=[];p=end
 while prev[p] is not None:
  last,key=prev[p];steps.append([key,*p]);p=last
 return steps[::-1],prev
legs=[];current=(74,20)
for old in json.loads((ROOT/'gba/art/route36/evidence/walk-plan.json').read_text()):
 goal=tuple(old['goal']);steps,reach=walk(current,goal);legs.append({'name':old['name'],'goal':goal,'steps':steps});current=goal
assert not any(x in (0,81) or y in (0,31) for x,y in reach)
for goal in [(7,11),(6,15),(74,15),(74,21)]:walk((74,20),goal)
assert solid[9:11,0:8].all() and solid[15,0:6].all()
assert solid[14:17,75:82].all() and solid[21,75:82].all()
assert not solid[20,75] and attrs[20,75]&255==0x62
assert not solid[14,7] and not solid[15,6]
assert solid[26:32,50:67].all()
assert not solid[17,44] and solid[17,43] and solid[17,45]
assert (~solid[29,6:8]).all() and solid[29,5] and solid[29,8]
assert (~solid[22:24,20]).all() and solid[24,20]
assert (~solid[19:22,66]).all() and solid[22,66]
features=json.loads((ROOT/'gba/art/route36/source/features.json').read_text());report=json.loads((E/'structure.json').read_text());trees=features['trees']+report['rear_trees_added'];footprints=np.zeros((32,82),int)
for x,y in trees:footprints[max(0,y+1):y+3,x:x+2]+=1
assert footprints.max()==1,'Overlapping tree trunks'
# All prior behavior and sprite layering stay intact outside the gate areas.
oldraw=subprocess.check_output(['git','show',BASE+':data/layouts/JohtoRoute36/map.bin'],cwd=G);oldgrid=np.frombuffer(oldraw,'<u2').reshape(32,82)
allowed=np.load(OUT/'source/affected.npy');assert np.array_equal(grid[~allowed]&0xfc00,oldgrid[~allowed]&0xfc00)
changed=subprocess.check_output(['git','diff','--name-only',BASE],cwd=G,text=True).splitlines();prefixes=('data/layouts/JohtoRoute36/','data/tilesets/primary/johto_route36/','data/tilesets/secondary/johto_route36/')
assert all(p.startswith(prefixes) for p in changed),changed
report.update(reachable_cells=len(reach),walk_steps=sum(len(l['steps']) for l in legs),walk_approaches=len(legs),tree_count=len(trees),overlapping_tree_footprints=0,gate_back_and_front_bypasses_closed=True,door_behavior_preserved=True,all_other_maps_events_scripts_unchanged=True)
(E/'structure.json').write_text(json.dumps(report,indent=2)+'\n');(E/'walk-plan.json').write_text(json.dumps(legs,indent=2)+'\n');print(json.dumps(report))
