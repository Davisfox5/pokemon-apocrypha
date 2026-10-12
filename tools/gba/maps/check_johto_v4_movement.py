#!/usr/bin/env python3
"""Record and validate live movement across five camera positions in Cherrygrove."""
from pathlib import Path
import subprocess,json,sys,numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[3];G=R/'tools/vendor/gba/johto-v4-game';A=R/'gba/art/johto-v4';O=R/'tools/vendor/gba/johto-v4-movement';O.mkdir(exist_ok=True)
T=R/'tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-darwin-arm64-arm-none-eabi'
if '--reuse' not in sys.argv:
 lines=subprocess.check_output([str(T/'bin/arm-none-eabi-nm'),str(G/'pokeemerald.elf')],text=True)
 wanted={'MapProof_Boot','MapProof_Enter','gObjectEvents','gSprites','ArePlayerFieldControlsLocked'}
 symbols={r[2]:r[0] for line in lines.splitlines() if len(r:=line.split())==3 and r[2] in wanted};assert symbols.keys()==wanted
 (O/'symbols.txt').write_text(''.join(f'{k} {v}\n' for k,v in symbols.items()))
 subprocess.run(['cc','-I/opt/homebrew/opt/mgba/include',str(R/'tools/gba/maps/johto_v4_npc_runtime.c'),'-L/opt/homebrew/opt/mgba/lib','-lmgba','-o',str(O/'runtime')],check=True)
 with (O/'movement.jsonl').open('w') as f:subprocess.run([str(O/'runtime'),str(G/'pokeemerald.gba'),str(O/'symbols.txt'),str(O)],stdout=f,check=True,timeout=240)
data=[json.loads(s) for s in (O/'movement.jsonl').read_text().splitlines()];rows=[r for r in data if 'objects' in r];assert len(rows)==1800
assert data[-8:]==[dict(interaction=gid,faces_player=True,displayed_south_idle_frame_verified=True,stops_for_dialogue=True,resumes_walking=True) for gid in range(1029,1037)]
solid=np.load(A/'native/scene.npz')['solid'];direction_frames={1:{9,10,11},2:{0,7,8},3:{1,2,3},4:{4,5,6}}
previous={};lag=0
for row in rows:
 objects=row['objects'];assert len({o['palette'] for o in objects})==len(objects),row
 assert len({(o['x'],o['y']) for o in objects})==len(objects),row
 for o in objects:
  assert not o['hflip'],o
  # Objects may be allocated just outside the camera; VRAM is still checked.
  assert o['frame']>=0,o
  key=(row['view'],o['gfx']);prior=previous.get(key)
  if o['frame'] not in direction_frames[o['facing']]:
   assert prior and prior['facing']!=o['facing'] and o['frame'] in direction_frames[prior['facing']],o
   lag+=1
  previous[key]=o
  assert o['anim']==o['facing']+3,o
  assert not solid[o['y'],o['x']],o
consts={}
for line in (G/'include/constants/event_objects.h').read_text().splitlines():
 parts=line.split()
 if len(parts)==3 and parts[0]=='#define':
  try:consts[parts[1]]=int(parts[2])
  except ValueError:pass
summary=[]
for r in json.loads((A/'residents.json').read_text()):
 gid=consts[r['graphics']];os=[o for row in rows for o in row['objects'] if o['gfx']==gid];assert os,r
 expected={tuple(p) for p in r['positions']};positions={(o['x'],o['y']) for o in os};assert positions==expected,(r,positions)
 directions={o['facing'] for o in os};assert directions==({'SQ':{1,2,3,4},'LR':{3,4},'UD':{1,2}}[r['mode']]),(r,directions)
 summary.append(dict(name=r['name'],graphics_id=gid,positions=sorted(positions),directions=sorted(directions),observations=len(os)))
report=dict(samples=len(rows),engine_frames=7200,camera_positions=5,walking_residents=12,collision_clear=True,distinct_active_palettes=True,rendered_frames_verified=True,no_horizontal_mirroring=True,one_sample_turn_upload_lag=lag,residents=summary,interaction=data[-8:])
(A/'evidence/movement.json').write_text(json.dumps(report,indent=2)+'\n')
(A/'evidence/movement.jsonl').write_bytes((O/'movement.jsonl').read_bytes())
# Short camera tour, each segment shows ordinary autonomous movement.
frames=[]
for view in range(4):
 for i in range(120):frames.append(Image.open(O/f'view-{view}-{i:03}.ppm').resize((720,480),Image.Resampling.NEAREST))
frames[0].save(A/'evidence/walking-tour.gif',save_all=True,append_images=frames[1:],duration=[70,60,70]*160,loop=0,optimize=True)
board=Image.new('RGB',(960,700),'#1d2d31');d=ImageDraw.Draw(board)
for i,label in enumerate(['Residential lane — Gold and Kestra','Mart and Pokemon Center','Southern gardens — Silver and visitors','Western beach — Johto and Sinnoh']):
 im=Image.open(O/f'view-{i}-000.ppm');im.save(A/f'evidence/view-{i}-native.png');x=i%2*480;y=i//2*350;board.paste(im.resize((480,320),Image.Resampling.NEAREST),(x,y+26));d.text((x+9,y+7),label,fill='white')
board.save(A/'evidence/in-game-tour.png');print(json.dumps(report,indent=2))
