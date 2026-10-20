from pathlib import Path
import json,shutil,numpy as np
from PIL import Image,ImageDraw,ImageFont
H=Path(__file__).resolve().parents[4];S=H/'gba/art/azalea-town/source';D=S/'well-elevation-rebuild';D.mkdir(exist_ok=True)
# Fixed d41 snapshots are committed inputs, never refreshed from live source.
assert (D/'before-native-edit-lock.json').exists()
# Preserve the previous rejected render and source; only the local well is rebuilt.
old=S/'well-gate-repair';bg=np.array(Image.open(D/'before-background.png').convert('RGBA'));fg=np.array(Image.open(D/'before-foreground.png').convert('RGBA'));b=np.array(Image.open(old/'background-before.png').convert('RGBA'));f=np.array(Image.open(old/'foreground-before.png').convert('RGBA'))
bg[96:304,640:880]=b[96:304,640:880];fg[96:304,640:880]=f[96:304,640:880]
r=json.loads((old/'assembly-before.json').read_text());grass=np.array(Image.open(S/'masters/grass.png').convert('RGBA'));Y,X=np.indices(bg.shape[:2])
for p in r['rock_placements']:
 if p['x']>=42 and p['y']<=18:
  x,y=p['x']*16,p['y']*16;bg[y:y+16,x:x+16]=grass[Y[y:y+16,x:x+16]%grass.shape[0],X[y:y+16,x:x+16]%grass.shape[1]]
A={};up=D
for name in ['R01','R02','R05','R06','R08','R10','R15','R16','R17']:
 a=np.array(Image.open(up/(name+'-shared.png')).convert('RGBA'));a[np.all(a[...,:3]==[96,192,144],2),:3]=[104,200,152];A[name]=a;Image.fromarray(a).save(D/(name+'-native.png'))
wall=np.zeros_like(bg);roles=np.zeros(bg.shape[:2],np.uint8);whole=[]
def piece(name,x,y,mirror=False,boundary=''):
 a=A[name][:,::-1] if mirror else A[name];assert x%16==0 and y%16==0
 wall[y:y+16,x:x+16]=a;roles[y:y+16,x:x+16]=1;whole.append(dict(tile='well-'+name,x=x//16,y=y//16,mirror=mirror,boundary=boundary))
# Contour boundaries selected before art: high northern rim -> upper terrace,
# upper terrace -> well court, and well court -> town. Complete 16px modules only.
for x in range(704,848,16):piece('R01',x,112,boundary='north rim / upper terrace')
piece('R16',688,112,True,'northwest return');piece('R16',848,112,False,'northeast return')
piece('R05',672,128,False,'offset northwest join');piece('R02',688,128,False,'northwest stacked face')
for y in range(144,256,16):piece('R06',672,y,True,'west outside return')
for y in range(128,288,16):piece('R06',848,y,False,'east outside return')
# The lower north course is separate, not a stretched first face. Its eastern
# end stays a complete corner; the adjacent open landing is preserved.
piece('R05',704,128,False,'northwest lower return')
for x in range(720,816,16):piece('R02',x,128,boundary='north lower course')
piece('R10',816,128,False,'lower course east return')
for y in range(144,256,16):piece('R06',704,y,True,'west court return')
for x in range(736,816,16):piece('R01',x,176,boundary='upper terrace / well court')
piece('R16',816,176,False,'court northeast return')
for y in range(192,256,16):piece('R06',816,y,False,'court east return')
# Convex foot corner is an existing complete master, not a cropped wall patch.
piece('R15',816,256,False,'court southeast foot')
piece('R15',704,256,False,'court southwest foot')
for x in range(720,768,16):piece('R01',x,256,boundary='well court / town')
m=wall[...,3]>0;bg[m]=wall[m]
# Retain the existing complete shared stair placeholders and ledge family.
props=[]
def over(name,x,y):
 a=np.array(Image.open(S/'masters'/(name+'.png')).convert('RGBA'));hh,ww=a.shape[:2];m=a[...,3]>0;fg[y:y+hh,x:x+ww][m]=a[m];props.append(dict(name=name,x=x,y=y))
over('well-S04',704,144);over('well-S01',768,256);over('well-S03',784,256)
for x,name in [(800,'L11'),(816,'L12'),(832,'L12'),(848,'L13')]:over(name,x,272)
# Replace old boulder grass backing by the actual terrain and original RGBA prop.
x,y,w,h=672,216,16,40;bg[y:y+h,x:x+w]=grass[Y[y:y+h,x:x+w]%grass.shape[0],X[y:y+h,x:x+w]%grass.shape[1]];m=wall[y:y+h,x:x+w,3]>0;bg[y:y+h,x:x+w][m]=wall[y:y+h,x:x+w][m];fg[y:y+h,x:x+w]=0
for p in r['placements']:
 a=np.array(Image.open(S/'masters'/(p['name']+'.png')).convert('RGBA'));hh,ww=a.shape[:2];x0=max(x,p['x']);x1=min(x+w,p['x']+ww);y0=max(y,p['y']);y1=min(y+h,p['y']+hh)
 if x0<x1 and y0<y1:
  cut=a[y0-p['y']:y1-p['y'],x0-p['x']:x1-p['x']];m=cut[...,3]>0;fg[y0:y1,x0:x1][m]=cut[m]
Image.fromarray(bg).save(D/'target-background.png');Image.fromarray(fg).save(D/'target-foreground.png');Image.fromarray(wall).save(D/'terrain.png');np.save(D/'terrain-roles.npy',roles)
geo=dict(shared_commit='82b98516aa17eeb538a0cd9adf373df8b3c7d3cb',registration=[64,16],whole_tiles=whole,new_props=props,new_trees=[],rail_props=[],adaptations=['Full 16x16 shared tiles only. No resizing, slicing, middle-row insertion or pixel-repainted corners.','HGSS projected outer face spans approximately 24 screen pixels; native face quantized to one complete 16px master plus separate lower course.','Northern sloping strip is represented as a complete course with an open eastern landing; exact DS slope height unavailable.','Existing shared staircase placeholders and southern ledge retained; no new story or interiors.'])
(D/'geometry.json').write_text(json.dumps(geo,indent=2)+'\n')
# elevation-plan.json is the authored contour authority, retained as input.
assert (D/'elevation-plan.json').exists()
comp=bg.copy();m=fg[...,3]>0;comp[m]=fg[m];Image.fromarray(comp).save(D/'proposal.png')
