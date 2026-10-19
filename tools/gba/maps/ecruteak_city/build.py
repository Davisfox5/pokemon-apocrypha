"""First-authoring only: registered HGSS Ecruteak exterior, native Porytiles.

Two connected rendering districts preserve the city's geography while giving
the temples their own tile budget. Never replay over committed native maps.
"""
from pathlib import Path
import sys,json,struct,subprocess,hashlib
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation,binary_erosion
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'gba/art/ecruteak-city/source';E=S.parent/'evidence';M=S/'masters'
G=Path(sys.argv[1]);PT=Path(sys.argv[2]);W,H=72,52;OX,OY=64,16;SPLIT=27
assert not subprocess.check_output(['git','-C',str(G),'ls-files','data/maps/JohtoEcruteak*'],text=True).strip(),'Committed maps must be edited natively.'
assert '--authoring-only' in sys.argv or not (G/'data/layouts/JohtoEcruteakCity/map.bin').exists()
art={p.stem:np.array(Image.open(p).convert('RGBA')) for p in M.glob('*.png')}
for a in art.values():a[...,:3]&=248
# Reserve silhouettes and corners before spare pavement texture variants.
# The retained 16px HGSS core preserves the paving grain and stone material.
art['paving']=art['paving'][:,:16].copy()
Y,X=np.indices((H*16,W*16));bg=art['grass'][Y%16,X%16].copy();fg=np.zeros_like(bg)
solid=np.zeros((H,W),bool);water=np.zeros_like(solid);above=np.zeros_like(solid);mat=np.full((H,W),'.','<U1');beh=np.zeros((H,W),np.uint16);roots=np.zeros((H,W),np.uint8);placements=[]
def px(x,y):return x+OX,y+OY
def maskpoly(points):
 im=Image.new('L',(W*16,H*16));ImageDraw.Draw(im).polygon([px(x,y) for x,y in points],fill=255);return np.array(im)>0
def material(mask,label,block=False):
 for y,x in np.ndindex(H,W):
  if mask[y*16:y*16+16,x*16:x*16+16].mean()>.3:mat[y,x]=label;solid[y,x]=block
def texture(mask,name):
 a=art[name];bg[mask]=a[(Y[mask]-OY)%a.shape[0],(X[mask]-OX)%a.shape[1]]
def over(name,sx,sy,role):
 x,y=px(sx,sy);im=art[name];h,w=im.shape[:2];assert x>=0 and y>=0 and x+w<=W*16 and y+h<=H*16,(name,x,y,w,h)
 m=im[...,3]>0;fg[y:y+h,x:x+w][m]=im[m];placements.append(dict(name=name,x=x,y=y,source_xy=[sx,sy],role=role))
 return x,y,w,h
def blockbox(box,label):
 x0,y0=px(box[0],box[1]);x1,y1=px(box[2],box[3]);solid[y0//16:(y1+15)//16,x0//16:(x1+15)//16]=True;mat[y0//16:(y1+15)//16,x0//16:(x1+15)//16]=label
# Square-by-square registration uses source pixels without geometric scaling.
# Paved streets step around the pond; courtyards are separate brown material.
pave=maskpoly([(248,272),(392,272),(392,312),(568,312),(568,288),(640,288),(640,360),(720,360),(720,384),(800,384),(800,408),(944,408),(944,688),(248,688),(248,448),(136,448),(136,408),(248,408)])
texture(pave,'paving');material(pave,'P')
rim=binary_dilation(pave,iterations=2)&~pave;bg[rim,:3]=[96,136,104]
inside=pave&~binary_erosion(pave,iterations=2);bg[inside,:3]=[144,160,120]
courts=[(288,344,408,424),(448,344,568,424),(288,448,408,536),(448,448,568,536),(624,440,752,536),(784,448,912,536),(288,560,408,656),(448,560,568,656),(624,560,752,656),(784,560,912,656)]
for x0,y0,x1,y1 in courts:
 m=maskpoly([(x0,y0),(x1-1,y0),(x1-1,y1-1),(x0,y1-1)]);texture(m,'court');material(m,'C')
 # Continuous moss-lined paver curb, including each corner.
 edge=binary_dilation(m,iterations=2)&~m;bg[edge,:3]=[136,152,112]
 edge=m&~binary_erosion(m,iterations=2);bg[edge,:3]=[152,152,112]
# Preserve the original court's little recess at each southern doorway.
for sx,sy in [(336,416),(496,416),(336,528),(496,528),(680,528),(832,528),(336,648),(496,648),(680,648),(848,648)]:
 m=maskpoly([(sx,sy),(sx+31,sy),(sx+31,sy+15),(sx,sy+15)]);texture(m,'paving');material(m,'P')
# Two nested courses beneath the Burned Tower; sides remain stone, not trees.
terrace=maskpoly([(256,120),(416,120),(432,144),(432,264),(248,264),(248,144)])
texture(terrace,'court');material(terrace,'R',True)
# The original terrace master carries the continuous side/front courses. Its
# outer apron remains earth, rather than an additional band of repeated faces.
# All rock planes share the reference terrace ramp, including hidden backing.
pal=np.unique(art['terrace'][art['terrace'][...,3]>0,:3],axis=0)
v=bg[terrace,:3].astype(int);bg[terrace,:3]=pal[np.argmin(np.sum((v[:,None]-pal.astype(int))**2,2),1)]
tt=art['terrace'];tx,ty=px(248,120);tm=tt[...,3]>0;bg[ty:ty+tt.shape[0],tx:tx+tt.shape[1]][tm]=tt[tm]
# Open upper court and actual visible stair axis. No warp marker squares.
court=maskpoly([(288,120),(399,120),(399,215),(288,215)])
texture(court,'court');material(court,'C')
over('stairs',336,208,'Burned Tower south-facing stairs')
blockbox((336,208,368,256),'A');solid[(208+OY)//16:(256+OY)//16,(336+OX)//16:(368+OX)//16]=False
apron=maskpoly([(312,256),(367,256),(367,271),(312,271)]);texture(apron,'court');material(apron,'C')
for sx in range(248,488,16):
 if 312<=sx<392:continue
 over('fence',sx,264,'HGSS terrace fence; complete posts');blockbox((sx,264,sx+16,280),'F')
# Original angular pond outline and continuous shore lip.
pond=maskpoly([(664,280),(816,280),(816,360),(744,360),(744,336),(664,336)])
texture(pond,'water');material(pond,'W',True)
shore=binary_dilation(pond,iterations=4)&~pond;bg[shore,:3]=[184,152,104]
bank=binary_dilation(pond,iterations=2)&~pond;bg[bank,:3]=[152,120,80]
foam=pond&~binary_erosion(pond);bg[foam,:3]=[104,192,200]
for y,x in np.ndindex(H,W):
 if pond[y*16:y*16+16,x*16:x*16+16].mean()>.3:water[y,x]=True;beh[y,x]=16
over('spring',720,280,'pond spring from original reference')
ground_mat=mat.copy()
for name,sx,sy,box in [('grove-outcrop',152,240,(160,240,208,272)),('pond-boulder',664,232,(672,240,688,272))]:
 over(name,sx,sy,'HGSS stone foreground with separate grass backing');blockbox(box,'R')
# Architectural masters remain local. Approved Center/Mart need deliberately
# wider receiving courts and clear front approaches than the original models.
buildings=[('burned-tower',288,88,(25,14)),('bell-entrance',480,184,(41,18)),('house',288,336,(25,26)),('house',448,336,(35,26)),('house-entry',288,448,(25,34)),('house-green',472,568,(37,41)),('house-southeast',808,568,(57,41)),('dance-theater',624,424,(47,34)),('gym',288,544,(26,41)),('center',640,552,(46,41)),('mart',800,440,(56,35)),('south-gate',560,672,(41,46)),('gate',-48,352,(4,26)),('gate',976,472,(67,33))]
for name,sx,sy,door in buildings:
 x,y=px(sx,sy);h,w=art[name].shape[:2]
 # Clear source-sized courts are widened only for accepted shared architecture.
 if name in ['center','mart']:
  m=maskpoly([(sx-8,sy+8),(sx+w+7,sy+8),(sx+w+7,sy+h+7),(sx-8,sy+h+7)]);texture(m,'court');material(m,'C')
  for yy,xx in np.ndindex(H,W):
   if m[yy*16:yy*16+16,xx*16:xx*16+16].mean()>.3:ground_mat[yy,xx]='C'
 over(name,sx,sy,'shared architecture' if name in ['center','mart','gate'] else 'Ecruteak local architecture')
 for yy in range(y//16,(y+h+15)//16):
  for xx in range(x//16,(x+w+15)//16):
   a=art[name][max(0,yy*16-y):min(h,yy*16+16-y),max(0,xx*16-x):min(w,xx*16+16-x)]
   if a.size and (a[...,3]>0).any():
    mat[yy,xx]='B';above[yy,xx]=yy*16<y+h-24
    if yy*16>=y+h-32:solid[yy,xx]=True
# Complete southern torii opening. Both stone feet stay occupied; its lintel
# draws overhead, with unobstructed paving under the visible arch.
gx,gy=px(560,672);solid[(gy+32)//16:(gy+64)//16,(gx+16)//16:(gx+64)//16]=False
above[gy//16:(gy+32)//16,gx//16:(gx+80)//16]=True
# Underlying root positions are selected independently of foreground canopies.
# Peripheral forest follows the source clearings, with complete outward padding.
forest=[]
def tree(name,sx,sy):
 x,y=px(sx,sy);cx,cy=x//16,y//16
 if roots[cy+1:cy+3,cx:cx+2].any():return
 over(name,sx,sy,'complete forest crown / distinct root footprint');roots[cy+1:cy+3,cx:cx+2]=1;solid[cy+1:cy+3,cx:cx+2]=True;mat[cy+1:cy+3,cx:cx+2]='T';above[cy,cx:cx+2]=True;forest.append(dict(name=name,x=cx,y=cy))
for sy in range(-16,784,32):
 for sx in range(-64,1088,32):
  # Geographic forest regions, reviewed against numbered source cells.
  wanted=(sy<112 or (sx<224 and not(352<=sy<448)) or (sx>=944 and not(472<=sy<568)) or (sy>=688 and not(544<=sx<752)) or (sy<256 and 432<=sx<480) or (sy<176 and 400<=sx<848) or (sy<272 and 816<=sx<944))
  if not wanted:continue
  if sx<208 and sx+32>152 and sy+16<272 and sy+48>240:continue
  x,y=px(sx,sy)
  if x<0 or y<0 or x+32>W*16 or y+48>H*16:continue
  if any(sx<bx+art[n].shape[1] and sx+32>bx and sy+16<by+art[n].shape[0] and sy+48>by for n,bx,by,_ in buildings):continue
  if np.any(pave[y+16:y+48,x:x+32]) or np.any(terrace[y+16:y+48,x:x+32]) or np.any(pond[y+16:y+48,x:x+32]):continue
  name='tree'
  if 224<=sx<848 and sy<256:name='tree-autumn' if sx>=288 and sy<176 else 'tree-amber'
  tree(name,sx,sy)
# Courtyard trees exactly mirror the original paired residential planting.
for sx,sy in [(384,336),(544,336),(384,448),(448,560),(784,560)]:
 tree('tree',sx,sy);tree('tree',sx,sy+32)
# Source marker rows beside each route gateway; independent props on lawn.
for sx in [152,168,184,200,872,888,904,920]:
 x,y,w,h=over('P13',sx,376,'original gateway marker row');blockbox((sx,392,sx+16,408),'S')
for sx,sy in [(368,248),(632,248),(640,496),(368,624),(536,496)]:
 x,y,w,h=over('P12',sx,sy,'shared freestanding sign');blockbox((sx,sy+16,sx+16,sy+32),'S')
# Protect all outside edges until the adjoining routes have their own source.
solid[0]=True;solid[-1]=True;solid[:,0]=True;solid[:,-1]=True
# Compact only fully hidden 8px backing. The opaque foreground preserves every
# visible pixel and silhouette; partial boundary quadrants are never replaced.
hidden=0
for gy,gx in np.ndindex(H*2,W*2):
 sl=np.s_[gy*8:gy*8+8,gx*8:gx*8+8]
 if np.all(fg[sl][...,3]==255):
  bg[sl]=art['grass'][Y[sl]%16,X[sl]%16];hidden+=1
Image.fromarray(bg).save(S/'background.png');Image.fromarray(fg).save(S/'foreground.png')
np.save(S/'material-grid.npy',mat);np.save(S/'solid.npy',solid);np.save(S/'behaviors.npy',beh);np.save(S/'tree-footprints.npy',roots)
np.save(S/'ground-material-grid.npy',ground_mat)
(S/'blocks.txt').write_text('\n'.join(''.join(r) for r in mat)+'\n')
comp=bg.copy();m=fg[...,3]>0;comp[m]=fg[m];Image.fromarray(comp).save(E/'authoring-preview.png')
# Porytiles performs real palette covering, exact native tile deduplication and
# flipped-tile reuse. Each district is compiled with its full native budget,
# then split at the engine's immutable 512 primary/secondary boundary.
stats=[]
for name,bank,y0,y1 in [('JohtoEcruteakTempleDistrict','ecruteak_temple',0,SPLIT),('JohtoEcruteakCity','ecruteak_city',SPLIT,H)]:
 inp=S/bank;out=E/(bank+'-compiled');inp.mkdir(exist_ok=True);out.mkdir(exist_ok=True)
 unique={};cells=[];pairs=[]
 for y in range(y0,y1):
  for x in range(W):
   a=bg[y*16:y*16+16,x*16:x*16+16];b=fg[y*16:y*16+16,x*16:x*16+16];attr=int(beh[y,x])|(0 if above[y,x] else 0x1000);key=(a.tobytes(),b.tobytes(),attr)
   if key not in unique:unique[key]=len(pairs);pairs.append((a,b,attr))
   cells.append(unique[key]|0x3000|(0xc00 if solid[y,x] else 0))
 assert len(pairs)<=1024,(name,len(pairs))
 rows=(len(pairs)+7)//8;bottom=Image.new('RGBA',(128,rows*16));middle=bottom.copy();top=bottom.copy()
 for i,(a,b,attr) in enumerate(pairs):bottom.paste(Image.fromarray(a),(i%8*16,i//8*16));middle.paste(Image.fromarray(b),(i%8*16,i//8*16))
 bottom.save(inp/'bottom.png');middle.save(inp/'middle.png');top.save(inp/'top.png')
 from palettes import cover
 cover(inp)
 cmd=[str(PT),'compile-primary','-dual-layer','-tiles-primary-override=1008','-tiles-total-override=1024','-metatiles-primary-override=1024','-pals-primary-override=13','-o',str(out),str(inp),str(G/'include/constants/metatile_behaviors.h')]
 result=subprocess.run(cmd,capture_output=True,text=True);(E/(bank+'-porytiles.log')).write_text(result.stdout+result.stderr)
 if result.returncode:print(result.stdout,result.stderr);raise SystemExit(result.returncode)
 tileim=Image.open(out/'tiles.png');blocks=(out/'metatiles.bin').read_bytes()[:len(pairs)*16];attrs=b''.join(struct.pack('<H',v[2]) for v in pairs)
 # The indexed transparent slot and the compiler's glyph IDs stay unchanged.
 for sec in [False,True]:
  folder=G/f'data/tilesets/{"secondary" if sec else "primary"}/{bank}';(folder/'palettes').mkdir(parents=True,exist_ok=True)
  start=512 if sec else 0;sh=Image.new('P',(128,256));sh.putpalette(tileim.getpalette())
  for i in range(512):
   tid=start+i
   if tid//16*8<tileim.height:sh.paste(tileim.crop((tid%16*8,tid//16*8,tid%16*8+8,tid//16*8+8)),(i%16*8,i//16*8))
  sh.save(folder/'tiles.png',bits=4)
  for i in range(16):
   p=out/'palettes'/f'{i:02}.pal';(folder/'palettes'/f'{i:02}.pal').write_text(p.read_text() if p.exists() else 'JASC-PAL\n0100\n16\n'+'0 0 0\n'*16)
  (folder/'metatiles.bin').write_bytes(blocks[start*16:(start+512)*16] or bytes(16));(folder/'metatile_attributes.bin').write_bytes(attrs[start*2:(start+512)*2] or bytes(2))
 layout=G/'data/layouts'/name;layout.mkdir(exist_ok=True);grid=np.array(cells,dtype='<u2').reshape(y1-y0,W);grid.tofile(layout/'map.bin')
 # A district edge is city paving, never a fabricated forest across the avenue.
 border=np.full((2,2),grid[(25 if y0==0 else 2),41]|0xc00,dtype='<u2');border.tofile(layout/'border.bin')
 stats.append(dict(map=name,tileset=bank,width=W,height=y1-y0,global_y=y0,metatiles=len(pairs),compiler='porytiles-legacy 2.0.0',command=cmd))
(E/'assembly.json').write_text(json.dumps(dict(size=[W,H],reference_size=[1032,785],registration_offset=[OX,OY],split_row=SPLIT,trees=forest,buildings=buildings,placements=placements,fully_hidden_backing_quadrants=hidden,districts=stats),indent=2)+'\n')
print(json.dumps(stats,indent=2))
