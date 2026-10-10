"""Check preservation, collision changes, NPC routes, and prepare native movement probes."""
from pathlib import Path
import json,struct,sys,hashlib
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R/'tools/gba/maps'));from tiles import Tileset
G=R/'tools/vendor/gba/cherrygrove-synthesis-work';A=R/'gba/art/cherrygrove-synthesis';S=A/'references/E';t=Tileset(G,'cherrygrove','cherrygrove');report=[];probes={};buildings=json.loads((A/'evidence/integration.json').read_text())['maps'][0]['buildings']
allowed=set()
for b in buildings:
 for x,y,w,h in [b['old'],[b['x'],b['y'],6 if b['style']=='center' else 5,6 if b['style']=='center' else 4 if b['style']=='mart' else 5]]:
  allowed.update((xx,yy) for yy in range(y,y+h) for xx in range(x,x+w))
 if b['style']=='mart':allowed.update((xx,yy) for yy in range(b['y']+1,b['y']+5) for xx in range(b['x']+4,b['x']+6))
for mid,name in [(0,'CherrygroveCity'),(9,'CherrygroveRoute29Approach'),(10,'CherrygroveRoute30Approach')]:
 lo=next(l for l in json.loads((G/'data/layouts/layouts.json').read_text())['layouts'] if l['name']==name+'_Layout');w,h=lo['width'],lo['height'];vals=lambda p:list(struct.unpack('<'+'H'*(w*h),p.read_bytes()));old=vals(S/f'data/layouts/{name}/map.bin');new=vals(G/f'data/layouts/{name}/map.bin');m=json.loads((G/f'data/maps/{name}/map.json').read_text());avoid=set()
 changes=[[i%w,i//w,v>>10,new[i]>>10] for i,v in enumerate(old) if v>>10!=new[i]>>10]
 assert all(mid==0 and (x,y) in allowed for x,y,_,_ in changes),'Unapproved terrain collision change'
 if mid==0:
  assert (G/f'data/maps/{name}/map.json').read_bytes()==(S/f'data/maps/{name}/map.json').read_bytes(),'Events/door coordinates changed'
 for e in m['object_events']:
  rx=e.get('movement_range_x',0);ry=e.get('movement_range_y',0)
  for y in range(e['y']-ry,e['y']+ry+1):
   for x in range(e['x']-rx,e['x']+rx+1):assert old[y*w+x]&0xc00 or not new[y*w+x]&0xc00,('New NPC obstruction',e['local_id'],x,y)
  for y in range(e['y']-3,e['y']+4):
   for x in range(e['x']-3,e['x']+4):avoid.add((x,y))
 # Warps are tested separately. Starting a collision probe on the north preview
 # warp triggers Sandgem travel before movement; it cannot measure an obstacle.
 for e in m['warp_events']:avoid.add((e['x'],e['y']))
 def kind(v):
  if v&0xc00:return 'solid'
  attr=t.attrs[(v&1023)>=512][v&511]&255
  if attr==105:return 'door'
  return 'water' if v>>12==1 else 'land'
 for y in range(1,h-1):
  for x in range(1,w-1):
   v=new[y*w+x];source=kind(v)
   if source not in ('land','water') or (x,y) in avoid:continue
   for dx,dy,key in [(1,0,16),(-1,0,32),(0,1,128),(0,-1,64)]:
    xx,yy=x+dx,y+dy;dest=new[yy*w+xx];k=kind(dest)
    if k=='door' or (xx,yy) in avoid:continue
    surf=int(source=='water');expect=int(k=='land' or (k=='water' and surf));probes.setdefault((mid,dest&1023,surf,expect),(mid,x,y,key,surf,expect,dest&1023))
 report.append(dict(map=name,collision_changes=changes,previously_clear_npc_movement_cells_preserved=True,terrain_collision_preserved_outside_buildings=True))
(A/'evidence/collision-changes.json').write_text(json.dumps(report,indent=2)+'\n');(A/'evidence/collision-probes.tsv').write_text(''.join(' '.join(map(str,p))+'\n' for p in probes.values()));print('Native probes:',len(probes))
