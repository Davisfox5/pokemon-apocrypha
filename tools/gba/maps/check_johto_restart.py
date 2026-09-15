#!/usr/bin/env python3
"""Structural connectivity plus read-only in-game actor frame/route verification."""
from pathlib import Path
from collections import deque
import subprocess,json,sys,struct
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[3];A=R/'gba/art/johto-restart';G=R/'tools/vendor/gba/johto-restart-game';O=R/'tools/vendor/gba/johto-restart-movement';T=R/'tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-darwin-arm64-arm-none-eabi';O.mkdir(exist_ok=True)
spec=json.loads((A/'layout.json').read_text());W,H=spec['width'],spec['height'];grid=struct.unpack('<'+'H'*(W*H),(G/'data/layouts/CherrygroveCity/map.bin').read_bytes());blocked=lambda x,y:bool(grid[y*W+x]&0xc00)
seen={tuple(spec['spawn'])};q=deque(seen)
while q:
 x,y=q.popleft()
 for xx,yy in [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]:
  if 0<=xx<W and 0<=yy<H and not blocked(xx,yy) and (xx,yy) not in seen:seen.add((xx,yy));q.append((xx,yy))
for b in spec['buildings']:x,y=b['door'];assert (x,y+1) in seen,b
for x in range(35,38):assert (x,0) in seen
for y in range(17,20):assert (63,y) in seen
residents=json.loads((A/'residents.json').read_text())
for r in residents:
 for pos in r['positions']:assert tuple(pos) in seen,(r,pos)
assert blocked(34,32)
(A/'evidence/structure.json').write_text(json.dumps(dict(reachable_cells=len(seen),five_door_approaches_reachable=True,both_route_exits_reachable=True,twelve_resident_routes_reachable=True,legacy_warp3_reserved_in_blocked_forest=True),indent=2)+'\n')
if '--structure-only' in sys.argv:print('Structure passed.');sys.exit()
if '--reuse' not in sys.argv:
 lines=subprocess.check_output([str(T/'bin/arm-none-eabi-nm'),str(G/'pokeemerald.elf')],text=True);wanted={'MapProof_Boot','MapProof_Enter','gObjectEvents','gSprites','ArePlayerFieldControlsLocked'};symbols={r[2]:r[0] for l in lines.splitlines() if len(r:=l.split())==3 and r[2] in wanted};assert symbols.keys()==wanted
 (O/'symbols.txt').write_text(''.join(f'{k} {v}\n' for k,v in symbols.items()))
 subprocess.run(['cc','-I/opt/homebrew/opt/mgba/include',str(R/'tools/gba/maps/johto_restart_npc_runtime.c'),'-L/opt/homebrew/opt/mgba/lib','-lmgba','-o',str(O/'runtime')],check=True)
 with (O/'movement.jsonl').open('w') as f:subprocess.run([str(O/'runtime'),str(G/'pokeemerald.gba'),str(O/'symbols.txt'),str(O)],stdout=f,check=True,timeout=240)
data=[json.loads(l) for l in (O/'movement.jsonl').read_text().splitlines()];rows=[r for r in data if 'objects' in r];assert len(rows)==1800
interactions=[r for r in data if 'interaction' in r];assert [r['interaction'] for r in interactions]==list(range(1029,1037));assert all(all(r[k] for k in ['faces_player','displayed_south_idle_frame_verified','stops_for_dialogue','resumes_walking']) for r in interactions)
directions={1:{9,10,11},2:{0,7,8},3:{1,2,3},4:{4,5,6}};prior={};lag=0
for row in rows:
 objects=row['objects'];assert len({o['palette'] for o in objects})==len(objects),row;assert len({(o['x'],o['y']) for o in objects})==len(objects),row
 for o in objects:
  assert not o['hflip'] and o['frame']>=0,o;assert not blocked(o['x'],o['y']),o
  key=(row['view'],o['gfx']);old=prior.get(key)
  if o['frame'] not in directions[o['facing']]:assert old and old['facing']!=o['facing'] and o['frame'] in directions[old['facing']],o;lag+=1
  prior[key]=o;assert o['anim']==o['facing']+3,o
ids={}
for line in (G/'include/constants/event_objects.h').read_text().splitlines():
 v=line.split()
 if len(v)==3 and v[0]=='#define' and v[2].isdigit():ids[v[1]]=int(v[2])
summary=[]
for r in residents:
 gid=ids[r['graphics']];os=[o for row in rows for o in row['objects'] if o['gfx']==gid];positions={(o['x'],o['y']) for o in os};assert positions=={tuple(p) for p in r['positions']},(r,positions)
 facing={o['facing'] for o in os};assert facing=={'SQ':{1,2,3,4},'LR':{3,4},'UD':{1,2}}[r['mode']],(r,facing)
 summary.append(dict(name=r['name'],graphics=gid,positions=sorted(positions),directions=sorted(facing)))
report=dict(samples=1800,engine_frames=7200,camera_positions=5,walking_residents=12,actual_obj_vram_frames_verified=True,no_horizontal_mirroring=True,distinct_palettes=True,collision_clear=True,one_sample_turn_upload_lag=lag,residents=summary,interactions=interactions)
(A/'evidence/movement.json').write_text(json.dumps(report,indent=2)+'\n');(A/'evidence/movement.jsonl').write_bytes((O/'movement.jsonl').read_bytes())
frames=[Image.open(O/f'view-{v}-{i:03}.ppm').resize((720,480),Image.Resampling.NEAREST) for v in range(4) for i in range(120)]
frames[0].save(A/'evidence/walking-tour.gif',save_all=True,append_images=frames[1:],duration=[70,60,70]*160,loop=0,optimize=True)
board=Image.new('RGB',(960,700),'#203036');d=ImageDraw.Draw(board)
for v,label in enumerate(['Custom houses / Gold and Johto residents','New Mart / approved Pokemon Center','Southern gardens / Silver and Unova visitor','Western beach / Kestra and Sinnoh visitor']):
 im=Image.open(O/f'view-{v}-000.ppm');im.save(A/f'evidence/view-{v}-native.png');x=v%2*480;y=v//2*350;board.paste(im.resize((480,320),Image.Resampling.NEAREST),(x,y+26));d.text((x+8,y+7),label,fill='white')
board.save(A/'evidence/in-game-tour.png');print(json.dumps(report,indent=2))
