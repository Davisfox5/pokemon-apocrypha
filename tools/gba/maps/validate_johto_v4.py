#!/usr/bin/env python3
"""Validate the authored exterior against the engine's installed collision/warp data."""
from pathlib import Path
from collections import deque
import json,struct,numpy as np
R=Path(__file__).resolve().parents[3];G=R/'tools/vendor/gba/johto-v4-game';A=R/'gba/art/johto-v4'
l=json.loads((A/'layout.json').read_text());m=json.loads((G/'data/maps/CherrygroveCity/map.json').read_text());res=json.loads((A/'residents.json').read_text());W,H=l['width'],l['height']
grid=np.frombuffer((G/'data/layouts/CherrygroveCity/map.bin').read_bytes(),dtype='<u2').reshape(H,W);blocked=(grid>>10&3)!=0
seen={tuple(l['spawn'])};q=deque(seen)
while q:
 x,y=q.popleft()
 for xx,yy in [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]:
  if 0<=xx<W and 0<=yy<H and not blocked[yy,xx] and (xx,yy) not in seen:seen.add((xx,yy));q.append((xx,yy))
checks=[]
for b in l['buildings']:
 x,y=b['door'];assert (x,y+1) in seen,b;w=m['warp_events'][b['warp']];assert [w['x'],w['y']]==[x,y]
 checks.append(dict(building=b['name'],door=[x,y],approach_reachable=True))
for r in res:
 for pos in r['positions']:assert tuple(pos) in seen,(r['name'],pos)
assert all((x,0) in seen for x in range(35,38));assert all((63,y) in seen for y in range(14,17));assert (24,16) in seen
assert blocked[4,1] and m['warp_events'][3]['dest_map']=='MAP_CHERRYGROVE_TRANSPLANT_HOUSE'
assert len(m['object_events'])==12 and len({o['local_id'] for o in m['object_events']})==12
layouts=json.loads((G/'data/layouts/layouts.json').read_text())['layouts'];checked=[]
for name in ['CherrygroveCity','CherrygroveRoute29Approach','CherrygroveRoute30Approach']:
 mm=json.loads((G/f'data/maps/{name}/map.json').read_text());ll=next(v for v in layouts if v['id']==mm['layout']);assert (G/ll['blockdata_filepath']).stat().st_size==ll['width']*ll['height']*2
 checked.append(dict(map=name,width=ll['width'],height=ll['height']))
report=dict(reachable_cells=len(seen),active_doors=checks,dormant_warp=3,walking_residents=len(res),all_npc_routes_reachable=True,route_connections_reachable=True,layouts=checked)
(A/'evidence/structure.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
