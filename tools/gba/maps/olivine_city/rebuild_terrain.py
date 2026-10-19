"""Narrow native terrain replacement from immutable Olivine c26b9b21.

Decodes current native planes, removes the rejected rock layer, and changes only
traced wall/stair squares. Does not replay town placement or any other generator.
"""
from pathlib import Path
import sys,json,hashlib,subprocess,struct
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_erosion
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent));from tiles import Tileset
G=Path(sys.argv[1]);PT=Path(sys.argv[2]);S=ROOT/'gba/art/olivine-city/source';T=S/'terrain-rebuild';M=T/'masters';E=S.parent/'evidence/terrain-rebuild';E.mkdir(exist_ok=True)
BASE='c26b9b21d095ca6e0f8a7e5a46a091bc82701e52';W,H=72,56;OX,OY=64,16
# An immutable checkout of the rejected native source is the patch input. Later
# owner edits require a new baseline; never silently replace them.
assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()==BASE
assembly=json.loads((S.parent/'evidence/assembly.json').read_text());oldbg=np.zeros((H*16,W*16,4),np.uint8);oldfg=oldbg.copy();above=np.zeros((H,W),bool);solid=np.zeros_like(above);beh=np.zeros((H,W),np.uint16)
for dist in assembly['districts']:
 if (T/'baseline-background.png').exists():break
 name,bank,y0,h=dist['map'],dist['tileset'],dist['global_y'],dist['height'];ts=Tileset(G,bank,bank)
 # Use the immutable Git objects even on repeat local attempts. Compare current
 # source against BASE or the previous exact output before replacing native art.
 raw=subprocess.check_output(['git','-C',str(G),'show',BASE+f':data/layouts/{name}/map.bin']);grid=np.frombuffer(raw,'<u2').reshape(h,W)
 for yy,xx in np.ndindex(h,W):
  mid=int(grid[yy,xx]&1023);entries=ts.blocks[mid>=512][mid%512];attr=ts.attrs[mid>=512][mid%512];above[y0+yy,xx]=not bool(attr&0x1000);solid[y0+yy,xx]=bool(grid[yy,xx]&0xc00);beh[y0+yy,xx]=attr&255
  for layer,plane in [(0,oldbg),(1,oldfg)]:
   for q in range(4):
    e=entries[layer*4+q];tid=e&1023;ix=tid%512;bankid=e>>12;vals=np.array(ts.tiles[tid>=512][ix],np.uint8).reshape(8,8)
    if e&1024:vals=vals[:,::-1]
    if e&2048:vals=vals[::-1]
    pal=np.array(ts.pals[bankid>=6][bankid],np.uint8);a=np.dstack([pal[vals],(vals>0).astype(np.uint8)*255]);x=xx*16+q%2*8;y=(yy+y0)*16+q//2*8;plane[y:y+8,x:x+8]=a
# First run exact native parity with the preserved baseline authoring planes.
# After local output exists, an immutable source copy is used for native decode.
if not (T/'baseline-background.png').exists():
 comp=oldbg.copy();m=oldfg[...,3]>0;comp[m]=oldfg[m];expected=np.array(Image.open(S.parent/'evidence/native-map.png').convert('RGB'));assert np.array_equal(comp[...,:3],expected)
 Image.fromarray(oldbg).save(T/'baseline-background.png');Image.fromarray(oldfg).save(T/'baseline-foreground.png');np.save(T/'baseline-above.npy',above);np.save(T/'baseline-solid.npy',solid);np.save(T/'baseline-behaviors.npy',beh)
else:
 oldbg=np.array(Image.open(T/'baseline-background.png'));oldfg=np.array(Image.open(T/'baseline-foreground.png'));above=np.load(T/'baseline-above.npy');solid=np.load(T/'baseline-solid.npy');beh=np.load(T/'baseline-behaviors.npy')
art={p.stem:np.array(Image.open(p).convert('RGBA')) for p in (S/'masters').glob('*.png')};mods={p.stem:np.array(Image.open(p).convert('RGBA')) for p in M.glob('*.png')}
# Keep the complete donor texture/masks. A five-step native wall ramp retains
# the full cap-to-shadow range while leaving banks for distinct receiving ground.
rpal=np.unique(mods['front'][mods['front'][...,3]>0,:3],axis=0);rpal=np.array(sorted(map(tuple,rpal),key=lambda c:sum(map(int,c))),np.uint8);rpal=rpal[np.round(np.linspace(0,len(rpal)-1,5)).astype(int)]
for n,a in mods.items():
 if n=='plateau-native':continue
 m=a[...,3]>0;v=a[m,:3].astype(int);a[m,:3]=rpal[np.argmin(np.sum((v[:,None]-rpal.astype(int))**2,2),1)]
oldsolid=solid.copy();bg=oldbg.copy();fg=oldfg.copy();Y,X=np.indices((H*16,W*16));SY=Y-OY;SX=X-OX

mat=np.load(S/'material-grid.npy').copy();ground=np.load(S/'ground-material-grid.npy').copy();# Remove the complete original wall paint mask, including minority 8px
# quadrants that were never labelled R by the rejected majority-cell ledger.
# This is a read-only recovery of the former wall geometry, not a generator run.
def oldpoly(points):
 im=Image.new('L',(W*16,H*16));ImageDraw.Draw(im).polygon([(x+OX,y+OY) for x,y in points],fill=255);return np.array(im)>0
def oldrect(box):
 x,y,r,b=box;return oldpoly([(x,y),(r-1,y),(r-1,b-1),(x,b-1)])
if (T/'retired-wall-mask.png').exists():
 oldroi=np.array(Image.open(T/'retired-wall-mask.png').convert('L'))>0
else:
 import ast
 text=(HERE/'build.py').read_text();literal=text[text.index('cliffs=[')+len('cliffs='):text.index('for name,mask in cliffs:')].strip();node=ast.parse(literal,mode='eval').body;oldroi=np.zeros((H*16,W*16),bool)
 for pair in node.elts:
  call=pair.elts[1];assert isinstance(call,ast.Call) and isinstance(call.func,ast.Name) and call.func.id in ['poly','rect'] and len(call.args)==1
  oldroi|=({'poly':oldpoly,'rect':oldrect}[call.func.id])(ast.literal_eval(call.args[0]))
oldpal=np.array([(88,56,32),(112,72,40),(136,88,48),(152,104,56),(176,128,72),(192,152,96),(216,184,120)],np.uint8)
oldrock=oldroi&np.any(np.all(oldbg[...,:3,None]==oldpal.T[None,None,:,:],axis=2),axis=2)
# Clear every rejected rock background. Receiving ground is independent of the
# new wall, including grass/sea and both original paved approaches.
restore=art['grass'][Y%16,X%16].copy();ocean=(SX>=880)&(SY>=288)|(SY>=576)&(SX>=632);a=art['water'];restore[ocean]=a[SY[ocean]%a.shape[0],SX[ocean]%a.shape[1]]
pave=((SX>=104)&(SX<464)&(SY>=176)&(SY<544))|((SX>=576)&(SX<632)&(SY>=336)&(SY<544));a=art['paving'];restore[pave]=a[SY[pave]%a.shape[0],SX[pave]%a.shape[1]]
bg[oldrock]=restore[oldrock];solid[ground=='R']=False;beh[ground=='R']=0;mat[(ground=='R')&(mat=='R')]='.';ground[ground=='R']='.'
# Existing building/tree/prop pixels are preserved. Remove only the two rejected
# stair masters so their replacement includes the complete receiving shoulders.
for n,sx,sy in [('stairs',576,312),('ramp',624,528)]:
 a=art[n];h,w=a.shape[:2];sl=np.s_[sy+OY:sy+OY+h,sx+OX:sx+OX+w];m=a[...,3]>0;fg[sl][m]=0
rock=np.zeros_like(bg);wallmask=np.zeros((H*16,W*16),bool);runs=[]
def paint(a,sx,sy,label,level,role):
 x,y=sx+OX,sy+OY;h,w=a.shape[:2];x0,y0=max(x,0),max(y,0);x1,y1=min(x+w,W*16),min(y+h,H*16)
 if x1<=x0 or y1<=y0:return
 b=a[y0-y:y1-y,x0-x:x1-x];m=b[...,3]>0;rock[y0:y1,x0:x1][m]=b[m];wallmask[y0:y1,x0:x1]|=m
 runs.append(dict(label=label,level=level,role=role,source_box=[sx,sy,sx+w,sy+h]))
def front(x0,x1,y,label,level):
 a=mods['front'];h,w=a.shape[:2];out=a[np.arange(h)[:,None],np.arange(x1-x0)[None,:]%w];paint(out,x0,y,label,level,'south cap / face / toe')
def side(x,y0,y1,facing,label,level):
 a=mods[facing];h,w=a.shape[:2];out=a[np.arange(y1-y0)[:,None]%h,np.arange(w)[None,:]];paint(out,x,y0,label,level,facing+' cap / face / contact')
def corner(x,y,kind,label,level):paint(mods[kind],x,y,label,level,'complete '+kind+' native elbow')
# One-level northwest forest: trace its complete exposed perimeter. Every turn
# has a native elbow; the contour continues beyond the cropped map at both ends.
side(288,-16,152,'east','NW forest east return',1);front(80,288,152,'NW forest south lip',1);corner(288,152,'convex-ne','NW forest outer corner',1)
side(80,176,448,'east','west city retaining wall',1);corner(80,152,'inner','NW city recess',1);front(-64,80,448,'west beach upper lip',1);corner(80,448,'convex-ne','west beach rounded return',1)
# Main northern landform. A separate inner spur is not another repeated stripe
# across the whole long wall. Its own rounded foot ends at the HGSS branch.
side(464,-16,384,'west','main north-to-city retaining face',1);corner(464,384,'convex-nw','main northern wall foot',1);front(488,544,384,'boulder court south lip',1);corner(544,384,'convex-ne','boulder court corner',1)
side(544,336,384,'east','boulder court east return',1);corner(544,312,'convex-ne','west stair shoulder',1);front(568,576,312,'west stair seat',1)
side(504,-16,176,'west','upper residential terrace west face',2);corner(504,176,'convex-nw','upper residential terrace west turn',2);front(528,640,176,'upper residential terrace south course',2);corner(640,176,'inner-mirror','upper terrace east recess',2)
front(624,632,312,'east stair seat',1);corner(632,312,'convex-nw','east stair full retaining shoulder',1)
# North forest upper course and the short rounded spur beside Route 39.
front(528,1088,72,'north forest upper course',3);corner(504,72,'convex-nw','north forest western cap',3)
side(488,-16,120,'west','Route39 inner high spur',3);corner(488,120,'convex-nw','Route39 high spur rounded end',3)
# Lighthouse: three separately traced courses. A narrow rock shoulder belongs
# between courses; it is a rock top, never another copy of a vertical face.
side(656,192,576,'west','lighthouse highest west face',3);corner(656,576,'convex-nw','lighthouse highest SW turn',3);front(680,792,576,'lighthouse top south course',3)
side(792,568,576,'east','lighthouse upper outline step A',3);corner(792,576,'convex-ne','lighthouse top east step A',3);front(792,816,568,'lighthouse top raised shoulder',3);corner(816,568,'convex-ne','lighthouse top east step B',3)
side(816,552,568,'east','lighthouse upper outline step B',3);front(816,832,552,'lighthouse top northeast shoulder',3);corner(832,552,'convex-ne','lighthouse highest SE return',3)
side(632,336,600,'west','lighthouse middle west face',2);corner(632,600,'convex-nw','lighthouse middle SW turn',2);front(656,832,600,'lighthouse middle south course',2);front(832,848,592,'lighthouse middle east shoulder',2);corner(848,592,'convex-ne','lighthouse middle SE turn',2)
side(632,600,624,'west','shore course west return',1);corner(632,624,'convex-nw','headland shoreline SW turn',1);front(656,848,624,'headland lowest shore course',1);corner(848,624,'convex-ne','headland shoreline SE turn',1);side(848,592,624,'east','headland lowest east return',1)
# Eastern shore: the three courses step inward independently instead of making
# a single thick rectangular wall. Each bend is traced against the original.
front(880,1088,224,'east coast highest northern course',3);corner(856,224,'inner','east coast upper inward turn',3);side(856,248,336,'east','east coast highest upper face',3);front(832,856,336,'east coast highest shelf',3);corner(856,336,'convex-ne','east coast upper shelf end',3);side(832,360,552,'east','lighthouse east high face',3)
front(904,1088,248,'east coast middle northern course',2);corner(880,248,'inner','east coast middle inward turn',2);side(880,272,360,'east','east coast middle upper face',2);front(856,880,360,'east coast middle shelf',2);corner(880,360,'convex-ne','east coast middle shelf end',2);side(856,384,544,'east','east coast middle lower face',2);front(848,856,544,'east coast middle lower shelf',2);corner(856,544,'convex-ne','east coast middle lower elbow',2);side(848,568,592,'east','east coast middle bottom return',2)
front(928,1088,272,'east coast lowest northern course',1);corner(904,272,'inner','east coast lowest inward turn',1);side(904,296,328,'east','east coast lowest upper face',1);front(880,904,328,'east coast lowest shelf',1);corner(904,328,'convex-ne','east coast lowest shelf end',1);side(880,352,376,'east','east coast beach head return',1);corner(880,376,'convex-ne','east coast beach head rounded foot',1)
# Complete the shelf/shoulder backing using a compact native rocky top donor.
# It has granular plateau texture, not a cap or repeated wall face.
top=np.array(Image.open(M/'plateau-native.png').convert('RGBA')).copy();lum=top[...,:3].astype(int).mean(2);high=lum>150;top[...,:3]=[192,152,96];top[high,:3]=[216,184,120]
mods['plateau-top']=top
# All three headland courses sit on continuous ground, with the source's rock
# shoulder at every step. An opaque rock backing also seats the timber slope.
backing=np.zeros_like(wallmask)
for box in [(632,576,872,648),(632,320,680,576),(904,248,1088,272),(928,272,1088,304)]:
 x0,y0,x1,y1=box;backing[y0+OY:y1+OY,x0+OX:x1+OX]=True
# Preserve the highest lawn and the east stair lane, including all foreground.
backing[(SY<576)&(SX>=680)&(SX<832)]=False;backing[(SX<632)&(SY<544)]=False
bg[backing]=top[Y[backing]%16,X[backing]%16];wallmask|=backing
# New walls lie beneath the current native foreground. Accepted trees, buildings,
# service pixels and all existing placements remain byte-for-byte visible.
m=rock[...,3]>0;bg[m]=rock[m]
# Static retaining planes live on the native lower plane; existing trees and
# architectural foregrounds keep their own banks and remain in front.
# Upper north/south stairs: complete width, opaque treads and native stone
# shoulders, with first/last treads seated against their actual receiving planes.
ref=np.array(Image.open(S/'hgss-reference.png').convert('RGB'));stair=ref[312:336,576:616].copy();wood=np.array(sorted(set(map(tuple,rpal))|set(map(tuple,np.unique(top[...,:3].reshape(-1,3),axis=0))),key=lambda c:sum(map(int,c))),np.uint8)
v=stair.astype(int);stair=wood[np.argmin(np.sum((v[:,:,None]-wood.astype(int))**2,3),2)];stair[:3]=wood[-2];stair[3]=wood[1];stair=np.dstack([stair,np.full(stair.shape[:2],255,np.uint8)])
# First and last treads extend to the opening shoulders; no grey paving appears
# inside the bounding footprint. The real city paving begins below the foot.
fg[312+OY:336+OY,576+OX:616+OX]=stair;fg[312+OY:336+OY,616+OX:624+OX]=stair[:,-1:,];wallmask[312+OY:336+OY,576+OX:624+OX]=True
# Timber east/west ramp, preserved original silhouette over a continuous stone
# retaining face. The old rectangular grey deck backing is removed completely.
ramp=art['ramp'];hh,ww=ramp.shape[:2];sl=np.s_[528+OY:528+OY+hh,624+OX:624+OX+ww];m=ramp[...,3]>0;fg[sl][m]=ramp[m]
# Update only wall/stair cells. Restore old solid foreground independently so
# clearing a rejected wall can never open a tree, building, sign or sea boulder.
for y,x in np.ndindex(H,W):
 sl=np.s_[y*16:y*16+16,x*16:x*16+16]
 if wallmask[sl].mean()>.3:solid[y,x]=True;beh[y,x]=0;ground[y,x]='R'
 if ground[y,x]=='R' and mat[y,x] not in ['T','B','S','F']:mat[y,x]='R'
 if mat[y,x] in ['T','B','S','F'] and oldsolid[y,x]:solid[y,x]=True
# Re-exposed coast is water, not walkable grass left by the removed wall.
watercols=np.unique(art['water'][...,:3].reshape(-1,3),axis=0)
for yy,xx in np.ndindex(H,W):
 sl=np.s_[yy*16:yy*16+16,xx*16:xx*16+16]
 if not oldrock[sl].any():continue
 v=bg[sl][...,:3];waterpixels=np.any(np.all(v[...,None]==watercols.T[None,None,:,:],axis=2),axis=2)
 if waterpixels.mean()>.5 and wallmask[sl].mean()<=.3 and mat[yy,xx] not in ['T','B','S','F']:
  solid[yy,xx]=True;beh[yy,xx]=16;ground[yy,xx]='W';mat[yy,xx]='W'
# Exact visible stair axes and ramp receiving approaches.
for x0,y0,x1,y1 in [(576,312,624,336),(632,544,688,576)]:
 x0,y0,x1,y1=x0+OX,y0+OY,x1+OX,y1+OY;solid[y0//16:(y1+15)//16,x0//16:(x1+15)//16]=False;beh[y0//16:(y1+15)//16,x0//16:(x1+15)//16]=0;mat[y0//16:(y1+15)//16,x0//16:(x1+15)//16]='A'
solid[0]=True;solid[-1]=True;solid[:,0]=True;solid[:,-1]=True
# Save editable native-derived planes and independent material/traversal ledgers.
Image.fromarray(bg).save(T/'background.png');Image.fromarray(fg).save(T/'foreground.png');Image.fromarray(rock).save(T/'rock-layer.png');Image.fromarray((wallmask*255).astype(np.uint8)).save(T/'wall-mask.png');Image.fromarray((oldroi*255).astype(np.uint8)).save(T/'retired-wall-mask.png');np.save(T/'above.npy',above)
for name,a in [('material-grid',mat),('ground-material-grid',ground),('solid',solid),('behaviors',beh)]:np.save(T/(name+'.npy'),a)
comp=bg.copy();m=fg[...,3]>0;comp[m]=fg[m];Image.fromarray(comp).save(E/'native-proposal.png');Image.fromarray(rock).save(E/'rock-only.png')
(T/'target-ramp.json').write_text(json.dumps(dict(native_face_colors=rpal.tolist(),top_colors=[[192,152,96],[216,184,120]],policy='Unscaled Route36 cap/face/toe masks and texture; five native face shades plus two separate plateau shades; no nearest-tile substitution.'),indent=2)+'\n')
(T/'wall-courses.json').write_text(json.dumps(dict(source_reference='HGSS Olivine 1035x858, native offset +64,+16, no scaling',interpretation='Observed face courses and occluded connections, not extracted HGSS z data.',course_pitch=24,runs=runs,stairs=[dict(source_box=[576,312,624,336],axis='north/south',repair='opaque complete tread/shoulder footprint'),dict(source_box=[624,528,688,592],axis='east/west',repair='same visible slope, continuous retaining-wall backing')]),indent=2)+'\n')
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
