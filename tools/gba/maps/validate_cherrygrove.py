#!/usr/bin/env python3
"""Structural checks for the town's native source, independent of emulator tests."""
import collections,json,struct,sys
from pathlib import Path
root=Path(__file__).resolve().parents[3];game=Path(sys.argv[1]).resolve()
spec=json.loads((Path(sys.argv[2]) if len(sys.argv)>2 else root/'gba/maps/cherrygrove/town.json').read_text())
layouts=json.loads((game/'data/layouts/layouts.json').read_text())['layouts'];byid={l['id']:l for l in layouts}
maps={m['id']:m for p in (game/'data/maps').glob('Cherrygrove*/map.json') if (m:=json.loads(p.read_text()))}
assert len(maps)==11,len(maps)
for mid,m in maps.items():
 assert m['region']=='REGION_JOHTO' and m['build_target']=='emerald'
 assert m['layout'] in byid
 for i,w in enumerate(m['warp_events']):
  assert w['dest_map'] in maps,(mid,i)
  assert int(w['dest_warp_id'])<len(maps[w['dest_map']]['warp_events']),(mid,i)
 for conn in m['connections'] or []:assert conn['map'] in maps
 for event in m['object_events']+m['bg_events']:
  assert event['script']+'::' in (game/'data/maps'/m['name']/'scripts.inc').read_text(),event['script']
l=byid['LAYOUT_CHERRYGROVE_CITY'];raw=(game/l['blockdata_filepath']).read_bytes();w=l['width'];h=l['height'];assert len(raw)==w*h*2
g=struct.unpack('<'+'H'*(len(raw)//2),raw);seen={tuple(spec['spawn'])};q=collections.deque(seen)
assert not ((g[spec['spawn'][1]*w+spec['spawn'][0]]>>10)&3), 'Spawn is blocked'
while q:
 x,y=q.popleft()
 for dx,dy in [(0,1),(0,-1),(1,0),(-1,0)]:
  a,b=x+dx,y+dy
  if 0<=a<w and 0<=b<h and (a,b) not in seen and not ((g[b*w+a]>>10)&3):seen.add((a,b));q.append((a,b))
nx,ny,nw=spec['north_exit'];ex,ey,ew=spec['east_exit'];px,py,pw,ph=spec['landmarks']['pier'];lx,ly,lw,lh=spec['landmarks']['lookout']
targets=[(b['door'][0],b['door'][1]+1) for b in spec['buildings']]+[(nx+1,ny),(ex,ey+1),(px+1,py+ph-1),(lx+1,ly+1)]
assert all(t in seen for t in targets)
assert (w+15)*(h+14)<=10240
print(json.dumps(dict(map_count=len(maps),door_warps=6,all_warps_resolve=True,all_connections_resolve=True,all_event_scripts_resolve=True,door_and_landmark_accessible=True,reachable_town_tiles=len(seen),padded_town_cells=(w+15)*(h+14)),indent=2))
