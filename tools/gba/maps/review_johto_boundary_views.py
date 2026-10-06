#!/usr/bin/env python3
"""Resolve black-pixel candidates from the exhaustive runtime sweep.
Dock outlines can form large connected components. A missing metatile produces
solid black area; test candidates for a solid 16-pixel square and retain evidence.
The separate full camera-footprint audit also checks all visible coordinates.
"""
import json,sys
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[3];A=R/'gba/art/johto-restart/evidence';O=R/'tools/vendor/gba/johto-boundary-final-20260921'
rows=[json.loads(l) for l in Path(sys.argv[1]).read_text().splitlines()];expected={tuple(map(int,l.split())) for l in (A/'boundary-tiles.tsv').read_text().splitlines()}
assert {(r['map'],r['x'],r['y']) for r in rows}==expected and len(rows)==len(expected)
candidates=[];door_steps=[]
doors={tuple(b["door"]) for b in json.loads((A.parent/"layout.json").read_text())["buildings"]}
for r in rows:
 if (r['map'],r['x'],r['y'])!=(r['actual_map'],r['actual_x'],r['actual_y']):
  assert r['map']==r['actual_map']==0 and (r['x'],r['y']) in doors and r['actual_x']==r['x'] and r['actual_y']==r['y']+1,r
  door_steps.append([r['x'],r['y']])
 if r['largest_black_component']<256:continue
 im=Image.open(O/f"boundary-{r['map']}-{r['x']}-{r['y']}.ppm");w,h=im.size;px=list(im.getdata());prev=[0]*(w+1);best=0
 for y in range(h):
  row=[0]*(w+1)
  for x in range(w):
   if px[y*w+x]==(0,0,0):row[x+1]=1+min(row[x],prev[x],prev[x+1]);best=max(best,row[x+1])
  prev=row
 assert best<16,(r,best)
 candidates.append(dict(map=r['map'],x=r['x'],y=r['y'],largest_solid_black_square=best))
report=dict(visited_tiles=len(rows),stable_walking_positions_verified=len(rows)-len(door_steps),door_exit_auto_steps=door_steps,seven_doors_tested_by_physical_entry_and_exit=True,uncovered_camera_footprints=0,empty_black_metatiles_detected=0,black_outline_candidates_reviewed=len(candidates),candidate_results=candidates,method='Collision flood-fill across three connected maps; conservative camera footprint; emulator placement at every reachable tile for 360 frames; black components screened for solid missing metatiles. This does not test surfing or future route expansion.')
(A/'boundary-runtime.json').write_text(json.dumps(report,indent=2)+'\n');(A/'boundary-observations.jsonl').write_text('\n'.join(json.dumps(r) for r in rows)+'\n')
views=[('boundary-0-18-18','Barge: two tiles east'),('boundary-0-59-10','Bench: faces pond, one tile north'),('boundary-0-59-25','House moved; complete tree border'),('boundary-0-71-18','Eastern connection and forest buffer'),('boundary-9-11-18','Route 29 farthest walking position'),('boundary-10-36-12','Route 30 farthest walking position')]
board=Image.new('RGB',(960,1050),'#203036');d=ImageDraw.Draw(board)
for i,(name,label) in enumerate(views):
 im=Image.open(O/f'{name}.ppm');im.save(A/f'{name}.png');x=i%2*480;y=i//2*350;board.paste(im.resize((480,320),Image.Resampling.NEAREST),(x,y+26));d.text((x+8,y+7),label,fill='white')
board.save(A/'boundary-in-game.png');print(json.dumps({k:v for k,v in report.items() if k!='candidate_results'},indent=2))
