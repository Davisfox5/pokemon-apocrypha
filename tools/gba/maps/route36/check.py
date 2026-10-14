"""Native reachability, preserved-city pixels/physics and warp validation."""
from pathlib import Path
import sys,json,subprocess
import numpy as np
from PIL import Image,ImageDraw
from collections import deque
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent))
from tiles import Tileset
G=Path(sys.argv[1]);OUT=ROOT/'gba/art/route36';E=OUT/'evidence';S=OUT/'source';BASE='ac6e1ee42257ba3551452a9f193b8d9c3a3fd1e3';W,H=82,32
r=np.fromfile(G/'data/layouts/JohtoRoute36/map.bin','<u2').reshape(H,W);solid=(r&0xc00)!=0
features=json.loads((S/'features.json').read_text());current=(74,20);legs=[]
def path(start,end,blocked=None):
 wall=solid if blocked is None else blocked;q=deque([start]);prev={start:None}
 while q:
  x,y=q.popleft()
  for dx,dy,key in [(0,-1,'UP'),(0,1,'DOWN'),(-1,0,'LEFT'),(1,0,'RIGHT')]:
   xx,yy=x+dx,y+dy
   if 0<=xx<W and 0<=yy<H and not wall[yy,xx] and (xx,yy) not in prev:prev[xx,yy]=((x,y),key);q.append((xx,yy))
 assert end in prev,('Unreachable approach',end)
 steps=[];p=end
 while prev[p] is not None:
  old,key=prev[p];steps.append([key,*p]);p=old
 return steps[::-1],prev
for name,goal in [('east-flowers',(66,19)),('alph-approach',(59,24)),('wooded-neck',(44,20)),('east-stairs',(33,23)),('grass-terrace',(20,20)),('west-stairs',(13,23)),('national-park',(7,14)),('route35-approach',(7,30)),('route37-approach',(19,1)),('violet-return',(74,20))]:
 steps,reach=path(current,goal);legs.append({'name':name,'goal':goal,'steps':steps});current=goal
assert not any(x in [0,W-1] or y in [0,H-1] for x,y in reach)
sealed=solid.copy();sealed[22:24,14]=True;sealed[22:24,32]=True
_,sealed_reach=path((74,20),(74,20),sealed)
assert (20,20) not in sealed_reach,'Terrace bypasses both stairs'

# Width/depth contracts measured from HGSS, then adapted to whole GBA cells.
# Test actual collision cells, not just the visual survey or a BFS endpoint.
assert not solid[17,44] and solid[17,43] and solid[17,45], 'Central neck must be one tile wide'
assert (~solid[29,6:8]).all() and solid[29,5] and solid[29,8], 'Route35 must remain two tiles wide'
assert (~solid[22:24,20]).all() and solid[24,20], 'Plateau south path must end at the tree wall'
assert (~solid[19:22,66]).all() and solid[22,66], 'Eastern dirt path must retain three walking rows'
# Whole-tree footprints are exclusive; no partial leaf/trunk fillers.
footprints=np.zeros((H,W),int)
for x,y in features['trees']:footprints[max(0,y+1):y+3,x:x+2]+=1
assert footprints.max()==1, 'Overlapping tree trunks/footprints'
# Every reference block is accounted for, including explicit native adapters.
ledger=json.loads((S/'block-ledger.json').read_text());assert len(ledger)==W*H
survey_plan=np.load(S/'plan.npy')
border=np.fromfile(G/'data/layouts/JohtoRoute36/border.bin','<u2').reshape(2,2)
assert np.array_equal(border,r[6:8,60:62]) and ((border&0xc00)!=0).all(), 'Continuous forest border must come from interior canopy rows'
for v in ledger:
 x,y=v['x'],v['y'];v.update(native_block=int(r[y,x]&1023),native_blocked=bool(solid[y,x]),tree_footprint=bool(footprints[y,x]),native_terrain=str(survey_plan[y,x]))
(S/'block-ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')

oldraw=subprocess.check_output(['git','show',BASE+':data/layouts/VioletCity/map.bin'],cwd=G);old=np.frombuffer(oldraw,'<u2').reshape(72,80);new=np.fromfile(G/'data/layouts/VioletCity/map.bin','<u2').reshape(72,80)
changed=np.argwhere((old&0xfc00)!=(new&0xfc00));assert changed.tolist()==[[30,5]],changed.tolist()
city=Tileset(G,'violet_city','violet_city').map_image(new.ravel().tolist(),80);before=Image.open(ROOT/'gba/art/violet-city/evidence/native-overview.png').convert('RGB');assert np.array_equal(city,before)
t=Tileset(G,'johto_route36','johto_route36');attrs=np.array(t.attrs[0]);beh=attrs[r&1023]&255;plan=np.load(S/'plan.npy');assert (beh[plan=='G']==2).all()
assert beh[20,75]==0x62
routes=json.loads((G/'data/maps/JohtoRoute36/map.json').read_text());gate=json.loads((G/'data/maps/VioletWestGate/map.json').read_text());citymap=json.loads((G/'data/maps/VioletCity/map.json').read_text())
assert routes['warp_events'][0]['dest_map']=='MAP_VIOLET_WEST_GATE'
assert citymap['warp_events'][1]['dest_map']=='MAP_VIOLET_WEST_GATE'
assert gate['warp_events'][0]['dest_map']=='MAP_JOHTO_ROUTE36' and gate['warp_events'][2]['dest_map']=='MAP_VIOLET_CITY'
report={'reachable_cells':len(reach),'walk_steps':sum(len(l['steps']) for l in legs),'approaches':len(legs),'unexpected_open_edges':0,'violet_changed_pixels':0,'violet_collision_changed_cells':changed.tolist(),'all_other_maps_unchanged':not bool(subprocess.check_output(['git','diff',BASE,'--','data/layouts/CherrygroveCity','data/layouts/CherrygroveRoute30Approach','data/layouts/JohtoRoute31','data/layouts/NewBarkTown'],cwd=G)),'grass_behavior_errors':0,'warp_pair_source_valid':True,'terrace_requires_stair_crossing':True,'onward_destinations_implemented':False,'surveyed_cells':W*H,'tree_count':len(features['trees']),'overlapping_tree_footprints':int((footprints>1).sum()),'path_widths':{'central_neck':1,'route35':2,'plateau_south_path':2,'eastern_dirt_path':3},'previous_draft_reachable_cells':888,'removed_excess_walkable_cells':888-len(reach)}
(E/'structure.json').write_text(json.dumps(report,indent=2)+'\n');(E/'walk-plan.json').write_text(json.dumps(legs,indent=2)+'\n')
# Same-scale survey comparison; native map expands to full 16px cells.
ref=Image.open(S/'hgss-reference.png').convert('RGB');native=Image.open(E/'native-overview.png').convert('RGB');board=Image.new('RGB',(1312,1056),(24,30,40));d=ImageDraw.Draw(board);d.text((8,7),'HGSS ROUTE 36 / SOURCE GEOGRAPHY',fill='white');board.paste(ref,(0,28));d.text((8,518),'NATIVE JOHTO RECONSTRUCTION / SAME PIXEL SCALE',fill='white');board.paste(native,(0,544));board.save(E/'source-comparison.png')
print(json.dumps(report))
