"""Reachability, immutability and native asset checks for the first Violet exterior."""
import sys,json,hashlib,subprocess
from pathlib import Path
from collections import deque
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent))
from tiles import Tileset
G=Path(sys.argv[1]);OUT=ROOT/'gba/art/violet-city';EV=OUT/'evidence'
grid=np.fromfile(G/'data/layouts/VioletCity/map.bin',dtype='<u2').reshape(72,80);solid=(grid&0xc00)!=0
start=(74,57)
def path(start,goal):
 q=deque([start]);p={start:None}
 while q:
  x,y=q.popleft()
  for dx,dy,key in [(0,-1,'UP'),(0,1,'DOWN'),(-1,0,'LEFT'),(1,0,'RIGHT')]:
   xx,yy=x+dx,y+dy
   if 0<=xx<80 and 0<=yy<72 and not solid[yy,xx] and (xx,yy) not in p:p[xx,yy]=((x,y),key);q.append((xx,yy))
 assert goal in p,('unreachable',goal)
 out=[];node=goal
 while p[node] is not None:
  prev,key=p[node];out.append([key,*node]);node=prev
 return out[::-1],p
legs=[];current=start
for b in json.loads((OUT/'source/landmarks.json').read_text()):
 steps,_=path(current,tuple(b['approach']));legs.append({'name':b['name'],'goal':b['approach'],'steps':steps});current=tuple(b['approach'])
_,reachable=path(start,start)
assert not any(x in [0,79] or y in [0,71] for x,y in reachable),'open map edge'
# New gate points back correctly, and preceding maps remain byte-identical.
m=json.loads((G/'data/maps/VioletCity/map.json').read_text());gate=json.loads((G/'data/maps/VioletEastGate/map.json').read_text());assert all(gate['warp_events'][i]['dest_map']=='MAP_VIOLET_CITY' for i in [0,1]);assert m['warp_events'][0]['dest_map']=='MAP_VIOLET_EAST_GATE'
protected=['data/tilesets/primary/cherrygrove','data/tilesets/secondary/claude_route30','data/tilesets/secondary/cherrygrove','data/layouts/CherrygroveRoute30Approach','data/layouts/JohtoRoute31','data/layouts/NewBarkTown','data/layouts/CherrygroveCity','data/layouts/VioletCityEntrance']
assert not subprocess.check_output(['git','diff','aa8ea35e','--',*protected],cwd=G),'protected map changed'
t=Tileset(G,'violet_city','violet_city');assert len(t.tiles[0])+len(t.tiles[1])<=1008
for mid in set(map(int,grid.ravel()&1023)):
 es=t.blocks[mid>=512][mid-512 if mid>=512 else mid];assert all((e>>12)<13 for e in es)
report={'reachable_cells':len(reachable),'landmark_approaches':len(legs),'open_edges':0,'protected_maps_and_tilesets_unchanged':True,'warp_pair_valid':True,'walk_steps':sum(len(l['steps']) for l in legs)}
(EV/'walk-plan.json').write_text(json.dumps(legs,indent=2)+'\n');(EV/'structure.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
