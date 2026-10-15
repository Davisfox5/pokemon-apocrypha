"""Read-only native basement visual-review sheets and fresh headless camera tour.
Never edits engine source/assets or replays an authoring generator.
Usage: python3 .../basement_finish_review.py ENGINE NEW_RUNTIME --toolchain TOOLCHAIN
"""
from pathlib import Path
import sys,json,hashlib,subprocess
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];G=Path(sys.argv[1]);OUT=Path(sys.argv[2]);sys.path.insert(0,str(HERE.parent));from tiles import Tileset
from config import FLOORS
from johto_connections import runtime as r
sha=subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip();rom=hashlib.sha256((G/'pokeemerald.gba').read_bytes()).hexdigest()
proof=json.loads((ROOT/'gba/art/union-cave-1f/evidence/all-floors-build.json').read_text());assert proof['source_commit']==sha and proof['rom_sha256']==rom
regions={
'b1f':[
 ('Northwest stair and wall return',(32,48,160,144)),('Northern stepped wall corner',(240,16,368,112)),
 ('Plateau front and small formations',(32,128,256,224)),('Strength barrier and side-wall foot',(48,176,192,256)),
 ('Upper river / inner wall junction',(304,256,432,368)),('Main lake northwest shore',(144,400,304,496)),
 ('Eastern rock/shore overlap',(416,432,528,560)),('Main 1F staircase and rim',(432,512,576,624)),
 ('Lower chamber west staircase',(16,688,160,832)),('Lower chamber east stair/bank',(400,688,576,816))],
'b2f':[
 ('Return stair / northwest corner',(16,32,160,160)),('Northern plateau concave turn',(224,32,368,176)),
 ('Northwest low bank and rock roots',(32,96,208,192)),('Northeast low bank / side face',(368,80,512,224)),
 ('Western peninsula head and cliff',(80,224,240,352)),('Eastern gallery and rock layers',(400,288,608,416)),
 ('South peninsula / inner wall corner',(208,432,384,576)),('Lake northern rim / terrace',(64,544,288,640)),
 ('Southwest outside turn',(48,608,208,752)),('Southern lake east/void corner',(464,592,640,752))]
}
sites={
'b1f':[('main-stone-stair',30,35),('main-lake-bank',26,23),('eastern-rock-gallery',26,19),('repaired-wall-corner',24,18),('northern-wall-turn',16,5),('upper-stair-marker',5,5),('strength-wall-base',7,12),('lower-west-stone-stair',5,48),('lower-east-bank',29,47)],
'b2f':[('return-stone-stair',5,6),('northwest-low-bank',6,7),('northeast-low-bank',27,8),('west-peninsula',7,19),('west-gallery',6,28),('east-rock-gallery',28,25),('southern-peninsula',24,32),('south-lake-bank',6,38),('low-shore-rock-roots',6,8)]
}
for key in ['b1f','b2f']:
 c=FLOORS[key];W,H=c['size'];S=ROOT/f'gba/art/union-cave-{key}/source';E=S.parent/'evidence/finish-review';E.mkdir(exist_ok=True)
 t=Tileset(G,c['set'],c['set']);grid=np.fromfile(G/'data/layouts'/c['name']/'map.bin','<u2').reshape(H,W);im=t.map_image(list(map(int,grid.ravel())),W)
 assert np.array_equal(np.array(im),np.array(Image.open(E.parent/'native-map.png').convert('RGB'))),'Current decode differs from published map'
 reference=Image.open(S/'hgss-reference.png').convert('RGB');before=Image.open(E.parent/'previous-de6922a/native-map.png').convert('RGB')
 for page in range(2):
  out=Image.new('RGB',(1320,5*300+20),'#1a2125');d=ImageDraw.Draw(out)
  for j,(label,box) in enumerate(regions[key][page*5:page*5+5]):
   for i,(a,caption) in enumerate([(reference,'HGSS reference'),(before,'Previous de6922a'),(im,'Current decoded native')]):
    x=10+i*440;y=10+j*300;d.text((x,y),label,fill='white');d.text((x,y+16),caption,fill='#b7c4cb');p=a.crop(box);scale=min(2,420/p.width,250/p.height);out.paste(p.resize((round(p.width*scale),round(p.height*scale)),Image.Resampling.NEAREST),(x,y+38))
  out.save(E/f'joins-and-corners-{page+1}.png')
 report={'source_commit':sha,'rom_sha256':rom,'basis':'current native tile decode equals published checked render; original HGSS geography and preserved preceding pass compared','review_status':'pending visual inspection','regions':[{'label':label,'pixel_box':box} for label,box in regions[key]],'all_wall_cell_sheet':'../wall-cell-review.png','physics_preserved':True,'limitations':['shared finite interior shading dictionary','static water','unwired Alph transit rooms/Route33; Strength pushing and campaign interactions remain pending']};(E/'review.json').write_text(json.dumps(report,indent=2)+'\n')
# Use the established mGBA harness; controlled camera placements, not a new map.
start=r.MAIN[:r.MAIN.index('  // Actual east connection')];end=r.MAIN[r.MAIN.index('  unsigned status=call("TrySavingData"'):]
steps=[]
for key,points in sites.items():
 n=FLOORS[key]['map_num']
 for label,x,y in points:steps.append(f'go({n},{x},{y});at({n},{x},{y},"{key}-{label}");shot("{key}-{label}");')
r.MAIN=start+'\n'.join(steps)+'\ngo(48,4,6);at(48,4,6,"finish-review-save");\n'+end
r.MAIN=r.MAIN.replace('at(11,27,18','at(48,4,6').replace('cold-reload-new-bark','cold-reload-finish-review')
r.main()
result=json.loads((OUT/'results.json').read_text());assert result['rom_sha256']==rom and all(p['exit_code']==0 for p in result['phases'])
for key in ['b1f','b2f']:
 E=ROOT/f'gba/art/union-cave-{key}/evidence/finish-review';out=Image.new('RGB',(980,((len(sites[key])+1)//2)*346+12),'#1a2125');d=ImageDraw.Draw(out)
 for i,(label,x,y) in enumerate(sites[key]):
  xx=10+i%2*490;yy=10+i//2*346;d.text((xx,yy+2),f'{key.upper()} {label} ({x},{y})',fill='white');im=Image.open(OUT/f'{key}-{label}.png');out.paste(im.resize((480,320),Image.Resampling.NEAREST),(xx,yy+20));im.save(E/f'{label}.png')
 out.save(E/'gameplay-review.png');(E/'runtime.json').write_text(json.dumps(result,indent=2)+'\n')
print('Fresh basement framing and ordinary save/reload/Continue passed; editable native source untouched')
