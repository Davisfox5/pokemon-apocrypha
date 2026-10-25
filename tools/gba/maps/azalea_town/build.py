"""First Azalea exterior authoring, HGSS geography plus locked shared masters.
Never rerun over an existing committed layout. Native files become the editor.
"""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'gba/art/azalea-town/source';E=S.parent/'evidence';M=S/'masters';G=Path(sys.argv[1]);W,H=64,33
import subprocess
if (G/'data/maps/JohtoAzaleaTown').exists():
 assert '--authoring-only' in sys.argv and not subprocess.check_output(['git','-C',str(G),'ls-files','data/maps/JohtoAzaleaTown'],text=True).strip(),'Native committed map exists; edit it directly, never replay.'
if (G/'data/layouts/JohtoAzaleaTown/map.bin').exists():assert '--authoring-only' in sys.argv,'Preserve native authoring'
for v in json.loads((S/'shared-provenance.json').read_text()):assert hashlib.sha256((M/(v['name']+'.png')).read_bytes()).hexdigest()==v['sha256']
art={p.stem:np.array(Image.open(p).convert('RGBA')) for p in M.glob('*.png')};Y,X=np.indices((H*16,W*16));tex=art['grass'];bg=tex[Y%tex.shape[0],X%tex.shape[1]].copy();fg=np.zeros_like(bg);solid=np.zeros((H,W),bool);mat=np.full((H,W),'.','<U1');beh=np.zeros((H,W),np.uint16);above=np.zeros((H,W),bool);placements=[];roots=np.zeros((H,W),np.uint8)
# 1:1 original reference, source(0,0)->native(64,16). Padding completes the west
# gate and edge tree crowns. Paths preserve the source loop/spurs and east access.
pm=Image.new('L',(W*16,H*16));d=ImageDraw.Draw(pm)
def path(points,width=32):
 d.line(points,fill=255,width=width)
 for x,y in points:r=width//2;d.ellipse((x-r,y-r,x+r-1,y+r-1),fill=255)
path([(112,288),(544,288)]);path([(224,208),(224,432)]);path([(224,432),(448,432)]);path([(448,288),(448,432)]);path([(544,224),(544,288)]);path([(448,384),(560,384),(560,352)]);path([(784,384),(1040,384)])
# Source main loop encloses the Gym; no dirt shortcuts through its central lawn.
m=np.array(pm)>0;pt=art['path'];bg[m]=pt[Y[m]%pt.shape[0],X[m]%pt.shape[1]]
# Existing grass/dirt transition vocabulary, coherent contour through every turn.
from scipy.ndimage import binary_dilation,binary_erosion
edge=binary_dilation(m)&~m;inner=m&~binary_erosion(m);bg[edge,:3]=[88,176,136];bg[inner,:3]=[184,168,128]
for y,x in np.ndindex(H,W):
 if m[y*16:(y+1)*16,x*16:(x+1)*16].mean()>.25:mat[y,x]='P'
# Shared complete rock masters in the well's distinct nested, grassy terraces.
# Every placement is an intact16px module with explicit orientation.
rock=[]
def rocktile(name,x,y,mirror=False):
 im=art[name][:,::-1] if mirror else art[name];a=bg[y*16:y*16+16,x*16:x*16+16];mask=im[...,3]>0;a[mask]=im[mask];solid[y,x]=True;mat[y,x]='R';rock.append(dict(tile=name,x=x,y=y,mirror=mirror))
for x in range(43,54):rocktile('R02' if x%2 else 'R04',x,7)
rocktile('R05',43,7);rocktile('R10',53,7)
for y in range(8,16):rocktile('R11' if y%2 else 'R12',43,y);rocktile('R11' if y%2 else 'R12',53,y,True)
for x in range(44,52):rocktile('R02' if x%2 else 'R04',x,8)
rocktile('R05',44,8)
for y in range(9,16):rocktile('R11' if y%2 else 'R12',44,y)
for x in range(46,52):rocktile('R02' if x%2 else 'R04',x,10)
rocktile('R10',51,10)
for y in range(11,16):rocktile('R11' if y%2 else 'R12',51,y,True)
# Native ground at the actual well court; its southern opening remains clear.
wellpad=Image.new('L',(W*16,H*16));ImageDraw.Draw(wellpad).rounded_rectangle((736,192,800,256),radius=8,fill=255);wm=np.array(wellpad)>0;bg[wm]=pt[Y[wm]%pt.shape[0],X[wm]%pt.shape[1]];bg[binary_dilation(wm)&~wm,:3]=[88,176,136];bg[wm&~binary_erosion(wm),:3]=[184,168,128];mat[12:16,46:50]='P'
# Original small outcrop at the southeast of the Gym loop. Its visible top is
# raised stone, not lawn or repeated front tiles. The lower face is partly hidden
# by the source forest; existing complete face/side modules remain intact.
stonepal=np.array(sorted(set(map(tuple,art['boulder'][art['boulder'][...,3]>0,:3]))),np.uint8);top=art['plateau'].copy()
for c in np.unique(top[...,:3].reshape(-1,3),axis=0):top[np.all(top[...,:3]==c,2),:3]=stonepal[np.argmin(np.sum((stonepal.astype(int)-c.astype(int))**2,1))]
outcrop=Image.new('L',(1024,528));ImageDraw.Draw(outcrop).rounded_rectangle((488,416,559,463),radius=8,fill=255);oc=np.array(outcrop)>0;outcrop_ground=bg.copy();bg[oc]=top[Y[oc]%16,X[oc]%16]
for xx in range(488,552,16):
 a=art['R02' if xx%32 else 'R04'];mask=a[...,3]>0;bg[448:464,xx:xx+16][mask]=a[mask]
for yy in [432,448]:
 a=art['R11'];mask=a[...,3]>0;bg[yy:yy+16,488:504][mask]=a[mask]
for yy,xx in np.ndindex(H,W):
 if oc[yy*16:(yy+1)*16,xx*16:(xx+1)*16].mean()>.35:solid[yy,xx]=True;mat[yy,xx]='R'
# Split the rounded grass/top edge into the two native layers. Hidden backing
# uses only the top family; the actual visible grass contour stays pixel-exact.
for gy in range(52,58):
 for gx in range(61,70):
  sl=np.s_[gy*8:gy*8+8,gx*8:gx*8+8];mask=oc[sl]
  if mask.any() and not mask.all():
   bg[sl][~mask]=bg[sl][mask][0];fg[sl][~mask]=outcrop_ground[sl][~mask]
# Building destinations registered by front-door approaches, not donor backdrop.
buildings=[('kurt',192,104,(14,11)),('center',368,176,(25,15)),('mart',512,128,(34,13)),('gym',256,304,(20,23)),('house',512,264,(34,21)),('gate',16,208,(7,18)),('well',736,192,(48,15))]
# Forest roots occupy distinct2x2 cells. Canopy overlap only on the supported
# 32px row pitch, behind later buildings. No half tree is cropped at any edge.
regions=[(0,0,1024,112),(0,80,176,224),(288,80,512,176),(624,80,688,240),(480,144,512,240),(864,80,1024,368),(0,320,176,528),(608,288,736,448),(768,416,1024,528),(0,448,1024,528)]
def over(name,x,y,role):
 im=art[name];h,w=im.shape[:2];assert 0<=x and 0<=y and x+w<=W*16 and y+h<=H*16,(name,x,y);m=im[...,3]>0;fg[y:y+h,x:x+w][m]=im[m];placements.append(dict(name=name,x=x,y=y,role=role))
forest=[]
for y in range(0,H*16-47,32):
 for x in range(0,W*16-31,32):
  if y==128 and 320<=x<=480:x-=16 # complete row closes the gap beside Kurt woodpiles
  if not any(x>=a and x+32<=c and y+16>=b and y+48<=e for a,b,c,e in regions):continue
  # Occupied building fronts/trees may not share their ground footprints.
  if any(x<bx+art[n].shape[1] and x+32>bx and y+16<by+art[n].shape[0] and y+48>by+max(16,art[n].shape[0]-48) for n,bx,by,door in buildings):continue
  if m[max(0,y+16):y+48,x:x+32].any():continue
  if x<304 and x+32>280 and y+16<184 and y+48>136:continue # woodpiles, not a tree trunk
  if any(43<=cx<=53 and 7<=cy<=16 for cy in range((y+16)//16,(y+48)//16) for cx in range(x//16,(x+32)//16)):continue
  cx,cy=x//16,y//16;assert not roots[cy+1:cy+3,cx:cx+2].any();roots[cy+1:cy+3,cx:cx+2]=1;solid[cy+1:cy+3,cx:cx+2]=True;mat[cy+1:cy+3,cx:cx+2]='T';above[cy,cx:cx+2]=True;over('tree',x,y,'aligned shared forest');forest.append([cx,cy])
for n,x,y,door in buildings:
 over(n,x,y,'shared building' if n in ['center','mart','gate'] else 'Azalea local architecture')
 h,w=art[n].shape[:2]
 # Complete exterior footprint blocks; upper roof may overlap player rendering,
 # but no unintended corridor opens behind a building through forest air.
 for yy in range(y//16,(y+h+15)//16):
  for xx in range(x//16,(x+w+15)//16):
   a=art[n][max(0,yy*16-y):min(h,yy*16+16-y),max(0,xx*16-x):min(w,xx*16+16-x)]
   if np.any(a[...,3]):
    mat[yy,xx]='B' if n!='well' else 'O'
    if yy*16>=y+h-32:solid[yy,xx]=True # wall/base, not overhead roof
  above[yy,x//16:min(W,(x+w+15)//16)]=yy<(y+h)//16-2
over('logs',280,128,'HGSS woodpiles beside Kurt');solid[9:11,18]=True;mat[9:11,18]='O'

for name,x,y in [('boulder',136,192),('boulder',648,216),('small-boulder',728,240)]:
 im=art[name];h,w=im.shape[:2]
 if name=='boulder':
  # Exact two-layer native encoding of a foreground rock in front of foliage.
  # Source alpha and final RGB stay exact. Compact hidden backing avoids a14th
  # mixed tree/stone palette without changing any visible pixel or master.
  oldcomp=bg[y:y+h,x:x+w].copy();oldleaf=fg[y:y+h,x:x+w];om=oldleaf[...,3]>0;oldcomp[om]=oldleaf[om]
  for yy in range(0,h,8):
   for xx in range(0,w,8):
    a=im[yy:yy+8,xx:xx+8];mask=a[...,3]>0
    if not mask.any():continue
    b=bg[y+yy:y+yy+8,x+xx:x+xx+8];b[:]=im[im[...,3]>0][0];b[mask]=a[mask]
    f=fg[y+yy:y+yy+8,x+xx:x+xx+8];f[:]=oldcomp[yy:yy+8,xx:xx+8];f[mask]=0
  placements.append(dict(name=name,x=x,y=y,role='exact native rock before foliage; two-layer encoding'))
 else:over(name,x,y,'stone foreground on source lawn')
 cy=(y+h-8)//16;cx=(x+w//2)//16;solid[cy,cx]=True;mat[cy,cx]='O'
# Small shared props sit on source lawn, not on paths or door approaches.
for name,x,y in [('P09-native',240,208),('P09-native',504,344),('P12',472,248),('P13',736,256),('P15',384,360)]:
 over(name,x,y,'shared town prop');h,w=art[name].shape[:2];cy=(y+h-8)//16;cx=(x+w//2)//16;solid[cy,cx]=True;mat[cy,cx]='S';above[y//16,cx]=True
for x,y in [(176,176),(176,192),(448,208),(448,224),(400,336),(400,352),(176,432),(192,432),(800,304),(816,304),(832,304)]:over('F01',x,y,'shared flower cluster')
for x0,x1,y in [(10,13,13),(45,49,20),(50,55,20)]:
 for x in range(x0,x1):over('L11' if x==x0 else 'L13' if x==x1-1 else 'L12',x*16,y*16,'south ledge');solid[y,x]=True;beh[y,x]=59;mat[y,x]='L'
# The adjacent routes/forest gate/well and interiors are not invented here.
# Keep outer map limits closed until area wiring has its own reviewed source.
solid[0]=True;solid[-1]=True;solid[:,0]=True;solid[:,-1]=True
# Native raw masters with non-RGB5 channels use the existing hardware reduction.
# No canonical source PNG is altered. Record exact source/native differences.
rounding={}
for name in set(p['name'] for p in placements):
 im=art[name];vals=im[im[...,3]>0,:3];rounding[name]=int(np.any(vals%8,1).sum())
fg[...,:3]&=248;bg[...,:3]&=248
Image.fromarray(bg).save(S/'background.png');Image.fromarray(fg).save(S/'foreground.png');comp=bg.copy();mask=fg[...,3]>0;comp[mask]=fg[mask];Image.fromarray(comp).save(E/'authoring-preview.png')
# Exact palette covering of every final 8px layer, no nearest-tile substitution.
sets={}
for l,im in enumerate([bg,fg]):
 for gy,gx in np.ndindex(H*2,W*2):
  a=im[gy*8:gy*8+8,gx*8:gx*8+8];cs=frozenset(map(tuple,a[a[...,3]>0,:3]));assert len(cs)<=15,('8px palette',l,gx,gy,len(cs));sets[(l,gy,gx)]=cs
# Seed complete compatible families. Shared Center and gate are covered exactly
# with a tiny native palette solver; no RGB approximation is permitted.
def colors(name):
 a=art[name];return set(map(tuple,a[a[...,3]>0,:3]&248))
ps=[set(map(tuple,bg[...,:3].reshape(-1,3)))|colors('F01'),colors('tree')|set(map(tuple,art['grass'][...,:3].reshape(-1,3)&248)),colors('kurt'),colors('gym'),colors('mart'),colors('well')|colors('P12')|colors('P13')|colors('P15'),colors('P09-native'),colors('boulder'),set.union(*(colors(n) for n in ['R02','R04','R05','R10','R11','R12','R17','L11','L12','L13']))]
# Grass/dirt and solid stone are separate BG families.
ps[0]=set(map(tuple,art['grass'][...,:3].reshape(-1,3)&248))|set(map(tuple,art['path'][...,:3].reshape(-1,3)&248))|{(88,176,136),(184,168,128)}|colors('F01')
assert all(len(p)<=15 for p in ps),[len(p) for p in ps]
import z3
for name in ['center','gate']:
 a=art[name].copy();a[...,:3]&=248;ss=[]
 for yy in range(0,a.shape[0],8):
  for xx in range(0,a.shape[1],8):
   q=a[yy:yy+8,xx:xx+8];ss.append(frozenset(map(tuple,q[q[...,3]>0,:3])))
 cs=sorted(set.union(*(set(v) for v in ss)));solver=z3.Solver();solver.set(timeout=10000);vars=[[z3.Bool(f'{name}_{i}_{j}') for j in range(len(cs))] for i in range(2)]
 for row in vars:solver.add(z3.PbLe([(v,1) for v in row],15))
 for v in set(ss):solver.add(z3.Or(*[z3.And(*[row[cs.index(c)] for c in v]) for row in vars]))
 assert solver.check()==z3.sat;model=solver.model()
 for row in vars:ps.append({c for c,v in zip(cs,row) if z3.is_true(model.eval(v))})
unique=sorted(set(sets.values())-{frozenset()},key=lambda v:(-len(v),sorted(v)))
for cs in unique:
 if any(cs<=p for p in ps):continue
 fit=[(len(p|cs)-len(p),i) for i,p in enumerate(ps) if len(p|cs)<=15]
 if fit:_,i=min(fit);ps[i]|=cs
 else:
  ps.append(set(cs))
print('Palette banks',len(ps),[len(p) for p in ps]);assert len(ps)<=13,'Preserve shared art; adjust assembly, never lossy nearest tiles'
pals=[np.array([[0,0,0]]+list(sorted(p))+[[0,0,0]]*(15-len(p)),np.uint8) for p in ps];pals += [np.zeros((16,3),np.uint8)]*(16-len(pals));glyphs=[np.zeros((8,8),np.uint8)];lookup={glyphs[0].tobytes():0};blocks=[];attrs=[];ml={};grid=np.zeros((H,W),np.uint16)
def ent(im,cs):
 if not cs:return 0
 b=next(i for i,p in enumerate(ps) if cs<=p);idx=np.zeros((8,8),np.uint8)
 for i,c in enumerate(pals[b][1:],1):idx[np.all(im[...,:3]==c,2)&(im[...,3]>0)]=i
 k=idx.tobytes()
 if k not in lookup:
  tid=len(glyphs);glyphs.append(idx)
  for h in range(2):
   for v in range(2):lookup.setdefault(((idx[::-1] if v else idx)[:,::-1] if h else (idx[::-1] if v else idx)).tobytes(),tid|h<<10|v<<11)
 return lookup[k]|b<<12
for y,x in np.ndindex(H,W):
 es=[]
 for l,im in enumerate([bg,fg]):
  for q in range(4):
   gy=y*2+q//2;gx=x*2+q%2;es.append(ent(im[gy*8:gy*8+8,gx*8:gx*8+8],sets[(l,gy,gx)]))
 attr=int(beh[y,x])|(0 if above[y,x] else 0x1000);k=tuple(es)+(attr,)
 if k not in ml:ml[k]=len(blocks);blocks.append(es);attrs.append(attr)
 grid[y,x]=ml[k]|0x3000|(0xc00 if solid[y,x] else 0)
print('Native glyphs/metatiles',len(glyphs),len(blocks));assert len(glyphs)<=1008 and len(blocks)<=1024
for secondary in [False,True]:
 folder=G/f'data/tilesets/{"secondary" if secondary else "primary"}/azalea';(folder/'palettes').mkdir(parents=True,exist_ok=True);start=512 if secondary else 0;n=max(1,len(glyphs)-start) if secondary else 512
 sheet=Image.new('P',(128,((n+15)//16)*8));sheet.putpalette([v for i in range(256) for v in (i*17%256,)*3])
 for i in range(n):
  if start+i<len(glyphs):sheet.paste(Image.fromarray(glyphs[start+i],mode='P'),(i%16*8,i//16*8))
 sheet.save(folder/'tiles.png',bits=4)
 for b in range(16):(folder/'palettes'/f'{b:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pals[b])+'\n')
 bb=blocks[start:start+512] or [[0]*8];aa=attrs[start:start+512] or [0];(folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*b) for b in bb));(folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(aa),*aa))
folder=G/'data/layouts/JohtoAzaleaTown';folder.mkdir(exist_ok=True);grid.tofile(folder/'map.bin');(grid[29:31,0:2]|0xc00).tofile(folder/'border.bin')
for n,im in [('background',bg),('foreground',fg)]:Image.fromarray(im).save(S/(n+'.png'))
comp=bg.copy();m=fg[...,3]>0;comp[m]=fg[m];Image.fromarray(comp).save(E/'native-map.png')
np.save(S/'material-grid.npy',mat);np.save(S/'solid.npy',solid);np.save(S/'behaviors.npy',beh);np.save(S/'tree-footprints.npy',roots);(S/'blocks.txt').write_text('\n'.join(''.join(r) for r in mat)+'\n')
(E/'assembly.json').write_text(json.dumps(dict(size=[W,H],reference_size=[932,508],registration_offset=[64,16],trees=forest,tree_count=len(forest),overlapping_tree_roots=0,placements=placements,rock_placements=rock,buildings=buildings,RGB5_rounding_source_pixels=rounding,palettes=len(ps),glyphs=len(glyphs),metatiles=len(blocks),limits=['Exterior only; no building/well interiors or campaign NPCs invented.','Route33/Ilex connections remain closed for separate integration; Route33 source untouched.','Source occluded ground is inferred from adjacent materials.']),indent=2)+'\n')
