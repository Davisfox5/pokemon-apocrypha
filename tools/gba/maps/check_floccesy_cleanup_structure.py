#!/usr/bin/env python3
from pathlib import Path
from collections import deque
import struct,json,hashlib
from tiles import Tileset
R=Path(__file__).resolve().parents[3];G=R/'tools/vendor/gba/floccesy-cleanup-work';A=R/'gba/art/floccesy-cleanup';W,H=56,78;v=struct.unpack('<4368H',(G/'data/layouts/FloccesyTown/map.bin').read_bytes());t=Tileset(G,'floccesy','floccesy')
def flood(surf):
 seen={(30,62)};q=deque(seen)
 while q:
  x,y=q.popleft()
  for xx,yy in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
   if not(0<=xx<W and 0<=yy<H) or (xx,yy) in seen:continue
   n=v[yy*W+xx]
   if n&0xc00 or (not surf and n>>12==1):continue
   seen.add((xx,yy));q.append((xx,yy))
 return seen
assert all(t.attrs[n&1023>=512][(n&1023)%512]>>12==1 for n in v), "Scenery may cover player sprites"
walk=flood(False);both=flood(True);unsafe=[p for p in sorted(both) if not(8<=p[0]<=W-9 and 6<=p[1]<=H-7)];assert not unsafe,unsafe[:30]
sp=json.loads((A/'layout.json').read_text())
for b in sp['buildings']:
 x,y=b['door'];assert (x,y) in walk and (x,y+1) in walk,b
for r in json.loads((A/'residents.json').read_text()):
 for p in r['positions']:assert tuple(p) in walk,r
assert all((9,y) in walk for y in range(66,69))
B=R/'tools/vendor/gba/johto-before-floccesy-v2-20260924';assert (G/'data/layouts/CherrygroveCity/map.bin').read_bytes()==(B/'data/layouts/CherrygroveCity/map.bin').read_bytes()
report=dict(map_cells=len(v),reachable_walking=len(walk),reachable_walk_and_surf=len(both),all_doors_connected=True,all_npc_routes_connected=True,no_exposed_camera_edges=True,cherrygrove_layout_byte_identical=True)
(A/'evidence/structure.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
# Per-metatile directional movement probes from physically accessible cells.
avoid={(x+dx,y+dy) for r in json.loads((A/'residents.json').read_text()) for x,y in [r['start']] for dx in range(-3,4) for dy in range(-3,4)};rows={}
for x,y in sorted(both):
 source=v[y*W+x];surf=int(source>>12==1)
 if (x,y) in avoid or (x==9 and y in (66,67,68)) or t.attrs[source&1023>=512][(source&1023)%512]&255==0x69:continue
 for dx,dy,key in [(1,0,16),(-1,0,32),(0,1,128),(0,-1,64)]:
  xx,yy=x+dx,y+dy
  if not(0<=xx<W and 0<=yy<H) or (xx,yy) in avoid:continue
  n=v[yy*W+xx];mid=n&1023;at=t.attrs[mid>=512][mid%512]&255
  if at in [0x69,0x63]:continue
  move=int(not n&0xc00 and (n>>12!=1 or surf));rows.setdefault((mid,surf,move),(20,x,y,key,surf,move,mid))
(A/'evidence/collision-probes.tsv').write_text(''.join(' '.join(map(str,row))+'\n' for row in rows.values()));print('Movement probes:',len(rows))
