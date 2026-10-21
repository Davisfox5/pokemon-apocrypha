"""Independent directional-face and native high/low consistency audit."""
from pathlib import Path
import sys,json,csv,hashlib
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[4];S=R/'gba/art/olivine-city/source';A=S/'base-terrain';O=S.parent/'evidence/base-terrain'
height=np.load(A/'height.npy');solid=np.load(A/'solid.npy');geo=json.loads((A/'geometry.json').read_text());rows=geo['cliffs'];native=Image.open(O/'native-map.png');ref=Image.open(S/'hgss-reference.png')
# Hand-reviewed source landmarks anchor the relative planes independently of
# the edge picker. Numbers are relative planes inferred from the overview.
anchors=[('main avenue',24,18,0),('residential lawn',37,17,1),('lighthouse lawn',47,33,2),('middle coastal shelf',53,37,1),('coastal footing',53,39,0),('ocean',59,39,-1),('north woodland',40,2,3),('north middle woodland',40,8,2),('west woodland',3,20,1)]
for name,x,y,h in anchors:assert int(height[y,x])==h,(name,x,y)
# Native donor semantics: 70 rises toward E, 72 rises toward W, 79 toward N.
# Convex and concave corners are distinct, never generic blended intersections.
semantics={0x70:{'W'},0x72:{'E'},0x69:{'N'},0x79:{'S'},0x68:{'N','W'},0x6a:{'N','E'},0x78:{'S','W'},0x7a:{'S','E'}}
deltas={'N':(0,-1),'E':(1,0),'S':(0,1),'W':(-1,0)}
for row in rows:
 x,y=row['x'],row['y'];mid=int(row['donor_metatile'],16);assert solid[y,x]
 if mid in semantics:
  assert set(row['low_sides'])==semantics[mid],row
  for side in semantics[mid]:
   dx,dy=deltas[side];assert height[y+dy,x+dx]<height[y,x],row
 else:assert mid in [0x73,0x74,0x76,0x77] and not row['low_sides'],row
# Both long sides of the SAME plateau must rise INWARD, with a south face
# across the bottom. These concrete locations catch the rejected reuse bug.
bycell={(r['x'],r['y']):int(r['donor_metatile'],16) for r in rows}
for x,y,mid in [(42,25,0x70),(52,25,0x72),(47,36,0x79),(40,30,0x70),(55,30,0x72),(47,38,0x79),(29,16,0x70),(34,23,0x72),(19,4,0x72)]:assert bycell[x,y]==mid,(x,y,bycell.get((x,y)),mid)
for y,x in np.ndindex(height.shape):
 if solid[y,x]:continue
 for dx,dy in deltas.values():
  xx,yy=x+dx,y+dy
  if 0<=xx<65 and 0<=yy<54 and not solid[yy,xx]:assert height[y,x]==height[yy,xx],(x,y,xx,yy,'unprotected level change')
with (O/'cliff-directions.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys(),lineterminator="\n");w.writeheader();w.writerows(rows)
# The review sheet uses actual decoded native output, no generated concept.
boxes=[('North entrance',(280,0,704,208)),('Residential return',(448,272,688,432)),('Lighthouse west and coastal south',(608,480,896,656)),('Eastern coast corners',(816,224,944,576))]
width=max((b[2]-b[0])*4 for _,b in boxes);sheet=Image.new('RGB',(width,sum((b[3]-b[1])*2+30 for _,b in boxes)),'#182028');d=ImageDraw.Draw(sheet);yy=0
for name,box in boxes:
 w,h=box[2]-box[0],box[3]-box[1];d.text((0,yy),name+' | original HGSS (left) / decoded native (right)',fill='white');yy+=30
 sheet.paste(ref.crop(box).resize((w*2,h*2),Image.Resampling.NEAREST),(0,yy));sheet.paste(native.crop(box).resize((w*2,h*2),Image.Resampling.NEAREST),(w*2,yy));yy+=h*2
sheet.save(O/'cliff-reference-comparison.png')
report=dict(reference_sha256=hashlib.sha256((S/'hgss-reference.png').read_bytes()).hexdigest(),reference_method='Visual interpretation of HGSS overview; not extracted DS elevation data.',cliff_cells=len(rows),landmark_height_checks=len(anchors),opposed_face_landmark_checks=9,unprotected_open_height_changes=0,stairs=0,passed=True,adaptations=['16px aligned courses from projected overview; original 20-24px courses reduced to one native rock course.', 'Former tree/roof-covered returns completed from visible neighboring edges.', 'Repeated original Gen 3 directional silhouettes with one shared warm Johto rock ramp.'])
(O/'elevation-review.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
