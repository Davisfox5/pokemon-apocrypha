from pathlib import Path
import json,struct
from collections import deque
R=Path(__file__).resolve().parents[3];G=R/'tools/vendor/gba/johto-restart-game';A=R/'gba/art/johto-restart/evidence'
classes=json.loads((A/'collision-audit.json').read_text())['classes'];layouts=json.loads((G/'data/layouts/layouts.json').read_text())['layouts'];probes={}
for mid,name,start in [(0,'CherrygroveCity',(48,20)),(9,'CherrygroveRoute29Approach',(0,18)),(10,'CherrygroveRoute30Approach',(44,17))]:
 l=next(l for l in layouts if l['blockdata_filepath']==f'data/layouts/{name}/map.bin');w,h=l['width'],l['height'];data=(G/l['blockdata_filepath']).read_bytes();v=struct.unpack('<'+'H'*(len(data)//2),data);m=json.loads((G/f'data/maps/{name}/map.json').read_text());avoid=set()
 for o in m.get('object_events',[]):
  for y in range(o['y']-3,o['y']+4):
   for x in range(o['x']-3,o['x']+4):avoid.add((x,y))
 seen={start};q=deque(seen)
 while q:
  x,y=q.popleft()
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
   xx,yy=x+dx,y+dy
   if 0<=xx<w and 0<=yy<h and not v[yy*w+xx]&0xc00 and (xx,yy) not in seen:seen.add((xx,yy));q.append((xx,yy))
 for x,y in sorted(seen):
  source=classes[f'{v[y*w+x]&1023:03x}']
  if source not in ['walk','water'] or (x,y) in avoid:continue
  for dx,dy,key in [(1,0,16),(-1,0,32),(0,1,128),(0,-1,64)]:
   xx,yy=x+dx,y+dy
   if not(0<=xx<w and 0<=yy<h) or (xx,yy) in avoid:continue
   tile=v[yy*w+xx]&1023;kind=classes[f'{tile:03x}']
   if kind=='door':continue
   surf=source=='water';expect=int(kind=='walk' or (kind=='water' and surf));k=(mid,tile,surf,expect)
   probes.setdefault(k,(mid,x,y,key,int(surf),expect,tile))
rows=list(probes.values());(A/'collision-probes.tsv').write_text(''.join(' '.join(map(str,r))+'\n' for r in rows));print('Native collision probes:',len(rows))
