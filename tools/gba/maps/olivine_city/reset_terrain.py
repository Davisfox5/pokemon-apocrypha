"""Fresh HGSS terrain tracing against native 601d1b07; not a town-generator replay.

The rejected independent rectangular wall strips are discarded. Original visible
contours and face texture are registered without scaling, converted to native
RGB5, and packed by plane/mask. Foreground architecture remains native input.
"""
from pathlib import Path
import sys,json,hashlib,subprocess,struct
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_fill_holes,label
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent));from tiles import Tileset
G=Path(sys.argv[1]);PT=Path(sys.argv[2]);S=ROOT/'gba/art/olivine-city/source';T=S/'terrain-reset';E=S.parent/'evidence/terrain-reset';PREV=S/'terrain-rebuild'
BASE='601d1b073e4e4723066a3dc88c679c21d317991b';W,H=72,56;OX,OY=64,16
assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()==BASE,'New owner changes require a separately reviewed baseline.'
# Refuse unrecognized local edits even when HEAD still names the old commit.
tracked=subprocess.check_output(['git','-C',str(G),'ls-files','data/layouts/JohtoOlivineCity','data/layouts/JohtoOlivineQuay','data/tilesets/primary/olivine_city','data/tilesets/secondary/olivine_city','data/tilesets/primary/olivine_quay','data/tilesets/secondary/olivine_quay'],text=True).splitlines()
def digest(raw,path):return hashlib.sha256(raw.replace(b'\r\n',b'\n') if path.endswith('.pal') else raw).hexdigest()
last=json.loads((T/'last-output.json').read_text()) if (T/'last-output.json').exists() else {}
for path in tracked:
 raw=(G/path).read_bytes();baseline=subprocess.check_output(['git','-C',str(G),'show',BASE+':'+path]);assert digest(raw,path) in [digest(baseline,path),last.get(path)],'Unrecognized native edit: '+path
assembly=json.loads((S.parent/'evidence/terrain-rebuild/assembly.json').read_text())
bg=np.array(Image.open(PREV/'background.png'));fg=np.array(Image.open(PREV/'foreground.png'));above=np.load(PREV/'above.npy');solid=np.load(PREV/'solid.npy');beh=np.load(PREV/'behaviors.npy');mat=np.load(PREV/'material-grid.npy');ground=np.load(PREV/'ground-material-grid.npy');oldsolid=solid.copy()
# Immutable baseline is already qualified against decoded native/Porymap pixels.
# Verify this session still has that source before any first write.
if not (T/'baseline-verified.json').exists():
 for d in assembly['districts']:
  ts=Tileset(G,d['tileset'],d['tileset']);grid=np.fromfile(G/'data/layouts'/d['map']/'map.bin','<u2');im=np.array(ts.map_image(grid.tolist(),W));y=d['global_y']*16;h=d['height']*16;expected=bg[y:y+h].copy();m=fg[y:y+h,:,3]>0;expected[m]=fg[y:y+h][m];assert np.array_equal(im,expected[...,:3])
 (T/'baseline-verified.json').write_text(json.dumps(dict(commit=BASE,decoded_visible_pixel_errors=0),indent=2)+'\n')
art={p.stem:np.array(Image.open(p).convert('RGBA')) for p in (S/'masters').glob('*.png')}
Y,X=np.indices(bg.shape[:2]);SX,SY=X-OX,Y-OY
ref=np.array(Image.open(S/'hgss-reference.png').convert('RGB'));rh,rw=ref.shape[:2]
RX=np.where(SX>=1024,992+(SX-992)%32,np.clip(SX,0,rw-1))
source=ref[np.clip(SY,0,rh-1),RX]
def polygon(points):
 im=Image.new('L',(W*16,H*16));ImageDraw.Draw(im).polygon([(x+OX,y+OY) for x,y in points],fill=255);return np.array(im)>0
def box(x0,y0,x1,y1):return (SX>=x0)&(SX<x1)&(SY>=y0)&(SY<y1)
def texture(name):
 a=art[name];return a[SY%a.shape[0],SX%a.shape[1]]
# Remove all previous wall paint/backing, plus the complete retraced coastline.
# The receiving plane is reconstructed independently from the rock geometry.
retired=(np.array(Image.open(PREV/'wall-mask.png'))>0)|(np.array(Image.open(PREV/'retired-wall-mask.png'))>0)
coast=box(824,224,952,648);west=box(20,540,104,650)
scope=retired|coast|west
receiving=texture('grass')
pave=box(104,174,470,544)|box(568,334,632,544);receiving[pave]=texture('paving')[pave]
sea=((SX>=936)&(SY>=296))|((SX>=904)&(SY>=350))|((SX>=880)&(SY>=382))|((SX>=872)&(SY>=576))|((SX>=632)&(SY>=648))
sea|=box(624,640,888,656)
receiving[sea]=texture('water')[sea]
quayjoin=box(624,544,632,640);receiving[quayjoin]=texture('deck')[quayjoin]
beach=box(-64,468,104,650);receiving[beach]=texture('sand')[beach]
# Source's small eastern beach, separate from the cliff faces.
eastbeach=polygon([(872,380),(887,380),(884,423),(873,448),(868,472),(868,550),(860,568),(850,568),(850,388)])
receiving[eastbeach]=texture('sand')[eastbeach]
bg[scope]=receiving[scope]
# Retire stair pixels as well as their backing. The replacement includes both
# complete timber abutments, head/foot treads and reference-shaped side returns.
for n,sx,sy,w,h in [('stairs',576,312,48,24),('ramp',624,528,64,64)]:
 sl=np.s_[sy+OY:sy+OY+h,sx+OX:sx+OX+w];fg[sl]=0;bg[sl]=receiving[sl];scope[sl]=True
# Regions tightly bound the original visible landforms; color separation only
# resolves their ragged stone/grass contact, not the course count or direction.
regions=[
 ('northwest-retaining',1,[(287,-16),(311,-16),(311,58),(328,59),(328,175),(106,175),(106,467),(-64,467),(-64,444),(92,444),(92,150),(288,150)]),
 ('north-main-face',1,[(470,-16),(487,-16),(487,424),(469,424)]),
 ('north-rounded-spur',2,[(487,-16),(505,-16),(505,122),(500,147),(486,149),(483,134),(483,40),(465,40),(465,-16)]),
 ('north-upper-return',3,[(503,-16),(531,-16),(531,70),(1088,70),(1088,94),(533,94),(531,114),(523,128),(505,126)]),
 ('residential-terraces',2,[(506,116),(532,116),(532,153),(553,153),(553,176),(645,176),(645,194),(665,202),(665,214),(647,214),(647,198),(513,200),(503,188)]),
 ('residential-upper-shelf',3,[(550,151),(616,151),(616,180),(551,180)]),
 ('stair-boulder-enclosure',1,[(551,308),(633,308),(633,337),(568,337),(567,394),(522,396),(522,376),(550,376)]),
 ('lighthouse-west-and-south',3,[(663,202),(696,202),(696,528),(888,528),(888,654),(624,654),(624,310),(663,310)]),
 ('eastern-shore-three-courses',3,[(903,223),(1088,223),(1088,305),(937,305),(937,351),(907,351),(907,383),(886,383),(886,441),(878,461),(878,551),(873,579),(850,579),(850,554),(824,554),(824,254),(833,254),(833,236),(855,236),(855,255),(881,255),(881,271),(903,271)]),
 ('southwest-rock-spur',1,[(25,542),(92,542),(104,551),(104,652),(38,652),(35,631),(23,631),(21,614),(21,553)])]
# Use the native Johto warm rock ladder without flattening the source's
# rounded ends, thin shelves, oblique faces or contact shadows into rectangles.
rockpal=np.array([(88,56,32),(112,72,40),(136,88,48),(152,104,56),(176,128,72),(192,152,96),(216,184,120)],np.uint8)
v=source.astype(np.int16);warm=(v[...,0]>v[...,1]+4)&(v[...,0]>v[...,2]+4)&(v[...,0]>48)
roi=np.zeros_like(scope);course=np.zeros_like(SX,dtype=np.uint8);ledger=[]
for name,level,points in regions:
 m=polygon(points);roi|=m;course[m]=level;ledger.append(dict(name=name,maximum_local_course=level,outline=points,authority='HGSS visible contours; occluded ground interpreted, not extracted DS heights'))
# Exclude visible residence roofs, original trees/props and flags from rock.
exclude=polygon([(497,210),(526,188),(542,187),(572,207),(577,275),(497,275)])|polygon([(576,207),(608,187),(625,191),(647,208),(648,275),(576,275)])
exclude|=box(578,310,617,336)|polygon([(629,549),(678,526),(681,568),(632,593)])
bg[roi]=receiving[roi]
wall=roi&warm&~exclude
wall[west]&=(v[west,0]-v[west,1]>=24)
# Small holes entirely surrounded by rock are palette noise, not openings.
wall=binary_fill_holes(wall)&roi&~exclude
components,count=label(wall);sizes=np.bincount(components.ravel());wall&=sizes[components]>=24
# NumPy multiplication must be wide: original RGB distance can exceed int16.
delta=v[:,:,None,:].astype(np.int32)-rockpal.astype(np.int32);colors=rockpal[np.argmin(np.sum(delta*delta,3),2)]
# Resolve long straight faces into reusable native runs. Each donor is an
# unobscured original patch of the SAME face and plane. Exact original bends,
# end caps, terraces and stair joins stay outside these repeat intervals.
# This is explicit tile assembly, not nearest-color replacement of geometry.
repeat_runs=[
 ('NW upper east face',(288,-16,312,48),(288,16,312,48)),
 ('NW lower east face',(304,80,328,144),(304,96,328,128)),
 ('NW forest south face',(112,152,288,176),(112,152,144,176)),
 ('western retaining east face',(88,184,112,440),(88,208,112,240)),
 ('western beach south lip',(-64,448,80,472),(16,448,48,472)),
 ('north main west face',(464,160,488,384),(464,208,488,240)),
 ('north main upper west face',(464,64,488,120),(464,208,488,240)),
 ('north inner spur',(488,-16,512,112),(488,48,512,80)),
 ('north highest west face',(504,-16,536,64),(504,16,536,48)),
 ('north forest south course',(552,72,1088,96),(704,576,736,600)),
 ('residential lower south lip',(536,176,624,200),(560,176,592,200)),
 ('residential upper south lip',(568,152,616,176),(568,152,600,176)),
 ('lighthouse upper west face',(656,232,696,296),(656,240,696,272)),
 ('lighthouse upper west inset',(672,328,696,392),(672,336,696,368)),
 ('lighthouse middle west face',(624,344,664,520),(624,416,664,448)),
 ('lighthouse lower west inset',(656,424,680,520),(656,448,680,480)),
 ('headland three south courses',(696,576,784,648),(704,576,736,648)),
 ('headland lower two courses',(784,600,832,648),(704,600,736,648)),
 ('east three north-facing courses',(944,224,1088,304),(976,224,1008,304)),
 ('east high wall lower run',(824,456,856,552),(824,480,856,512)),
 ('east high wall upper run',(824,368,856,408),(824,376,856,408)),
]
run_report=[]
for name,dst,donor in repeat_runs:
 x0,y0,x1,y1=dst;dx,dy,dr,db=donor;rw,rh=dr-dx,db-dy
 mask=box(*dst);tx=dx+(SX[mask]-x0)%rw;ty=dy+(SY[mask]-y0)%rh
 sample=ref[ty,tx].astype(np.int32);valid=(sample[:,0]>sample[:,1]+4)&(sample[:,0]>sample[:,2]+4)&(sample[:,0]>48)
 delta=sample[:,None,:]-rockpal.astype(np.int32);col=rockpal[np.argmin(np.sum(delta*delta,2),1)]
 wall[mask]=valid;colors[mask]=col;bg[mask]=receiving[mask];roi|=mask;scope|=mask
 run_report.append(dict(name=name,target=list(dst),donor=list(donor),policy='same-facing original face; bends/endpoints excluded, no scaling'))
# Complete the upper residential shelf where the smaller shared tree exposes
# the original occluded termination. Rounded outward return, matching face.
cap=polygon([(616,152),(621,153),(624,157),(624,169),(621,173),(616,175)])
capcol=colors.copy();cx=560+(SX[cap]-616)%8;cy=SY[cap];sample=ref[cy,cx].astype(np.int32);delta=sample[:,None,:]-rockpal.astype(np.int32);capcol[cap]=rockpal[np.argmin(np.sum(delta*delta,2),1)]
wall[cap]=True;colors[cap]=capcol[cap];roi|=cap;scope|=cap
(T/'repeated-runs.json').write_text(json.dumps(run_report,indent=2)+'\n')
# The HGSS overview contains original tree-root/prop fragments inside these
# occluded regions. They are not cliff geometry and the native trees already
# own their full roots. Remove detached remnants after run assembly as well.
components,count=label(wall,structure=np.ones((3,3),bool));sizes=np.bincount(components.ravel());detached=wall&(sizes[components]<96);wall[detached]=False;bg[detached]=receiving[detached]
(T/'removed-occlusion-fragments.json').write_text(json.dumps(dict(pixels=int(detached.sum()),policy='8-connected detached rock-colored fragments smaller than 96px; full native foreground roots/props untouched'),indent=2)+'\n')
bg[wall,:3]=colors[wall];bg[wall,3]=255;scope|=roi
from reset_tiles import compact
packing=compact(bg,wall,receiving,fg,art['grass'],art['water'],art['sand'])
(T/'native-tile-adaptation.json').write_text(json.dumps(packing,indent=2,default=int)+'\n')
# Native material masks and plane annotations are independent of collision.
rock=np.zeros_like(bg);rock[wall]=bg[wall]
# Original stair/ramp pixels are opaque within their precise timber silhouette.
# Native shoulders remain background rock; no rectangular paving underlay.
stairs=box(578,312,618,336);ramp=polygon([(630,549),(678,527),(679,567),(632,590)])
for mask in [stairs,ramp]:
 fg[mask,:3]=colors[mask];fg[mask,3]=255;scope|=mask
# Restore original opening approaches to match the 16px walking axis.
# Stair head is high lawn, foot is civic paving; east-west ramp joins quay/lawn.
for y,x in np.ndindex(H,W):
 sl=np.s_[y*16:y*16+16,x*16:x*16+16]
 if not scope[sl].any():continue
 oldfeature=mat[y,x] in ['T','B','S','F'] and oldsolid[y,x]
 cov=wall[sl].mean();water=sea[sl].mean()>.5
 if cov>.28:ground[y,x]='R';solid[y,x]=True;beh[y,x]=0
 elif water:ground[y,x]='W';solid[y,x]=True;beh[y,x]=16
 else:ground[y,x]='P' if pave[sl].mean()>.5 else '.';solid[y,x]=False;beh[y,x]=0
 if mat[y,x] not in ['T','B','S','F']:mat[y,x]=ground[y,x]
 if oldfeature:solid[y,x]=True;beh[y,x]=0
# Tree roots remain explicit even where source-original crowns hid a contour.
roots=np.load(S/'tree-footprints.npy');solid[roots>0]=True;beh[roots>0]=0
for x0,y0,x1,y1 in [(576,312,624,336),(632,544,688,576)]:
 sl=np.s_[(y0+OY)//16:(y1+OY+15)//16,(x0+OX)//16:(x1+OX+15)//16];solid[sl]=False;beh[sl]=0;mat[sl]='A'
solid[0]=True;solid[-1]=True;solid[:,0]=True;solid[:,-1]=True
# Empty fully hidden BG quadrants retain the existing native compact substrate.
for y in range(0,H*16,8):
 for x in range(0,W*16,8):
  sl=np.s_[y:y+8,x:x+8]
  if np.all(fg[sl][...,3]==255):bg[sl]=art['grass'][Y[sl]%16,X[sl]%16]
from reset_tiles import hidden_background
hidden_report=hidden_background(bg,fg)
(T/'hidden-background-reuse.json').write_text(json.dumps(hidden_report,indent=2)+'\n')
for name,a in [('background',bg),('foreground',fg),('rock-layer',rock)]:Image.fromarray(a).save(T/(name+'.png'))
scope=np.repeat(np.repeat(scope.reshape(H*2,8,W*2,8).any(axis=(1,3)),8,axis=0),8,axis=1)
for name,a in [('wall-mask',wall),('scope-mask',scope),('reference-regions',roi)]:Image.fromarray((a*255).astype(np.uint8)).save(T/(name+'.png'))
for name,a in [('above',above),('material-grid',mat),('ground-material-grid',ground),('solid',solid),('behaviors',beh),('local-course-count',course)]:np.save(T/(name+'.npy'),a)
(T/'contours.json').write_text(json.dumps(ledger,indent=2)+'\n')
comp=bg.copy();m=fg[...,3]>0;comp[m]=fg[m];Image.fromarray(comp).save(E/'native-proposal.png');Image.fromarray(rock).save(E/'rock-only.png')
mods={'front':np.dstack([rockpal.reshape(1,-1,3),np.full((1,len(rockpal)),255,np.uint8)]),'plateau-top':art['cliff-top']}
if '--preview' in sys.argv:raise SystemExit(0)
# Compile ONLY current Olivine planes. IDs outside the three affected tileset
# pairs, layouts and collision entries remain untouched.
source=S;stats=[]
for dist in assembly['districts']:
 name,bank,y0,y1=dist['map'],dist['tileset'],dist['global_y'],dist['global_y']+dist['height']
 if bank=='olivine_harbor':stats.append(dist);continue
 inp=T/bank;out=E/(bank+'-compiled');inp.mkdir(exist_ok=True);out.mkdir(exist_ok=True);unique={};cells=[];pairs=[]
 for y in range(y0,y1):
  for x in range(W):
   a=bg[y*16:y*16+16,x*16:x*16+16];b=fg[y*16:y*16+16,x*16:x*16+16];attr=int(beh[y,x])|(0 if above[y,x] else 0x1000);key=(a.tobytes(),b.tobytes(),attr)
   if key not in unique:unique[key]=len(pairs);pairs.append((a,b,attr))
   cells.append(unique[key]|0x3000|(0xc00 if solid[y,x] else 0))
 assert len(pairs)<=1024,(name,len(pairs));rows=(len(pairs)+7)//8;bottom=Image.new('RGBA',(128,rows*16));middle=bottom.copy();topim=bottom.copy()
 for i,(a,b,attr) in enumerate(pairs):bottom.paste(Image.fromarray(a),(i%8*16,i//8*16));middle.paste(Image.fromarray(b),(i%8*16,i//8*16))
 bottom.save(inp/'bottom.png');middle.save(inp/'middle.png');topim.save(inp/'top.png')
 from terrain_palettes import cover
 cover(inp,S,mods)
 cmd=[str(PT),'compile-primary','-dual-layer','-tiles-primary-override=1008','-tiles-total-override=1024','-metatiles-primary-override=1024','-pals-primary-override=13','-o',str(out),str(inp),str(G/'include/constants/metatile_behaviors.h')]
 r=subprocess.run(cmd,capture_output=True,text=True);(E/(bank+'-porytiles.log')).write_text(r.stdout+r.stderr)
 if r.returncode:print(r.stdout,r.stderr);raise SystemExit(r.returncode)
 tileim=Image.open(out/'tiles.png');blocks=(out/'metatiles.bin').read_bytes()[:len(pairs)*16];attrs=b''.join(struct.pack('<H',v[2]) for v in pairs)
 for sec in [False,True]:
  folder=G/f'data/tilesets/{"secondary" if sec else "primary"}/{bank}';start=512 if sec else 0;sh=Image.new('P',(128,256));sh.putpalette(tileim.getpalette())
  for i in range(512):
   tid=start+i
   if tid//16*8<tileim.height:sh.paste(tileim.crop((tid%16*8,tid//16*8,tid%16*8+8,tid//16*8+8)),(i%16*8,i//16*8))
  sh.save(folder/'tiles.png',bits=4)
  for i in range(16):
   p=out/'palettes'/f'{i:02}.pal';(folder/'palettes'/f'{i:02}.pal').write_text(p.read_text() if p.exists() else 'JASC-PAL\n0100\n16\n'+'0 0 0\n'*16)
  (folder/'metatiles.bin').write_bytes(blocks[start*16:(start+512)*16] or bytes(16));(folder/'metatile_attributes.bin').write_bytes(attrs[start*2:(start+512)*2] or bytes(2))
 layout=G/'data/layouts'/name;grid=np.array(cells,dtype='<u2').reshape(y1-y0,W);grid.tofile(layout/'map.bin');np.full((2,2),grid[18 if y0==0 else 1,28]|0xc00,dtype='<u2').tofile(layout/'border.bin')
 stats.append(dict(map=name,tileset=bank,width=W,height=y1-y0,global_y=y0,metatiles=len(pairs),command=cmd))
assembly['districts']=stats;(E/'assembly.json').write_text(json.dumps(assembly,indent=2)+'\n');print(json.dumps(stats,indent=2))

(T/'last-output.json').write_text(json.dumps({p:digest((G/p).read_bytes(),p) for p in tracked},indent=2)+'\n')
