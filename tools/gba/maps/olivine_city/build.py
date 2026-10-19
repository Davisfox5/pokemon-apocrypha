"""First-authoring only. Never replay over committed Olivine native layouts."""
from pathlib import Path
import sys,json,struct,subprocess
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation,binary_erosion
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'gba/art/olivine-city/source';E=S.parent/'evidence';M=S/'masters';G=Path(sys.argv[1]);PT=Path(sys.argv[2]);W,H=72,56;OX,OY=64,16
assert not subprocess.check_output(['git','-C',str(G),'ls-files','data/maps/JohtoOlivine*'],text=True).strip(),'Edit committed native sources directly.'
art={p.stem:np.array(Image.open(p).convert('RGBA')) for p in M.glob('*.png')}
for a in art.values():a[...,:3]&=248
Y,X=np.indices((H*16,W*16));bg=art['water'][Y%32,X%32].copy();fg=np.zeros_like(bg);solid=np.ones((H,W),bool);above=np.zeros_like(solid);mat=np.full((H,W),'W','<U1');beh=np.full((H,W),16,np.uint16);roots=np.zeros((H,W),np.uint8);placements=[];trees=[]
def px(x,y):return x+OX,y+OY
def poly(points):
 im=Image.new('L',(W*16,H*16));ImageDraw.Draw(im).polygon([px(x,y) for x,y in points],fill=255);return np.array(im)>0
def rect(box):
 x,y,r,b=box;return poly([(x,y),(r-1,y),(r-1,b-1),(x,b-1)])
def classify(mask,label,block=False,behavior=0):
 for y,x in np.ndindex(H,W):
  if mask[y*16:y*16+16,x*16:x*16+16].mean()>.3:mat[y,x]=label;solid[y,x]=block;beh[y,x]=behavior
 return mask
def texture(mask,name):
 a=art[name];bg[mask]=a[(Y[mask]-OY)%a.shape[0],(X[mask]-OX)%a.shape[1]]
def ground(mask,name,label,block=False):texture(mask,name);classify(mask,label,block)
def over(name,sx,sy,role):
 x,y=px(sx,sy);a=art[name];h,w=a.shape[:2];assert x>=0 and y>=0 and x+w<=W*16 and y+h<=H*16,(name,x,y,w,h)
 m=a[...,3]>0;fg[y:y+h,x:x+w][m]=a[m];placements.append(dict(name=name,x=x,y=y,source_xy=[sx,sy],role=role));return x,y,w,h

def block(box,label,yes=True):
 x,y,r,b=box;x,y=px(x,y);r,b=px(r,b);sl=np.s_[y//16:(b+15)//16,x//16:(r+15)//16];solid[sl]=yes;mat[sl]=label;beh[sl]=0
# Registered coast; original projected concave headland corners stay explicit.
land=poly([(-64,-16),(1088,-16),(1088,280),(944,280),(944,320),(928,320),(928,352),(912,352),(912,400),(880,400),(880,544),(864,544),(864,648),(632,648),(632,544),(104,544),(104,648),(-64,648)])
ground(land,'grass','.');bg[land&~binary_erosion(land),:3]=[216,184,120];shore=binary_dilation(land,iterations=3)&~land;bg[shore,:3]=[216,184,120]
# West Route 40 beach and north Route 39 apron; sandy, never random rock.
ground(rect((-64,480,104,648)),'sand','S');ground(rect((336,-16,448,96)),'sand','S')
# The original avenue and east stair lane stay distinct from grassy building lots.
pave=poly([(104,176),(336,176),(336,96),(464,96),(464,384),(560,384),(560,336),(576,336),(576,320),(616,320),(616,336),(632,336),(632,544),(104,544)])
ground(pave,'paving','P')
# Continuous two-pixel lawn curb, all internal corners included.
edge=pave&~binary_erosion(pave,iterations=2);bg[edge,:3]=art['grass'][0,0,:3]
for box in [(136,200,352,256),(248,320,440,368),(136,432,336,496),(456,440,544,496),(496,200,656,304)]:
 m=rect(box);ground(m,'grass','.');edge=m&~binary_erosion(m,iterations=2);bg[edge,:3]=art['grass'][0,0,:3]
# Broad boardwalk, central pier, terminal platform and south approach.
dock=poly([(104,544),(632,544),(632,640),(440,640),(440,736),(472,736),(472,816),(432,816),(432,896),(360,896),(360,832),(280,832),(280,736),(360,736),(360,640),(104,640)])
ground(dock,'deck','D');edge=dock&~binary_erosion(dock,iterations=2);bg[edge,:3]=[88,112,120]
# Cliff tops, side face and front courses use material-compatible original cores.
# The explicit masks retain the original terrace outline; modules use local
# plane-oriented cores instead of nearest-tile compression.
cliffs=[('cliff-front',poly([(96,144),(320,144),(320,176),(112,176),(112,448),(0,448),(0,480),(96,480)])),
 ('cliff-side',rect((288,-16,320,144))),('cliff-side',poly([(464,-16),(528,-16),(528,144),(512,144),(512,208),(496,208),(496,384),(480,384),(480,176),(464,176)])),
 ('cliff-front',poly([(528,144),(624,144),(624,176),(656,176),(656,208),(640,208),(640,192),(544,192),(544,176),(528,176)])),
 ('cliff-side',rect((656,208,688,544))),('cliff-side',rect((632,320,656,544))),
 ('cliff-front',rect((560,304,640,336))),('cliff-side',rect((544,320,576,384))),
 ('cliff-front',poly([(528,368),(544,368),(544,384),(528,384),(528,400),(496,400),(496,384),(528,384)])),
 ('cliff-front',poly([(688,576),(816,576),(816,560),(832,560),(832,544),(864,544),(864,592),(832,592),(832,608),(688,608)])),
 ('cliff-toe',poly([(672,608),(832,608),(832,592),(864,592),(864,640),(848,648),(672,648),(672,640),(632,640),(632,592),(656,592),(656,608)])),
 ('cliff-side',poly([(864,240),(944,240),(944,280),(928,280),(928,320),(912,320),(912,352),(896,352),(896,432),(880,432),(880,544),(848,544),(848,352),(864,352)])),
 ('cliff-toe',rect((632,576,688,648))),('cliff-front',rect((912,224,1088,256))),('cliff-front',rect((944,256,1088,288)))]
for name,mask in cliffs:ground(mask,name,'R',True)
# Clear receiving land and the original east lane; separate walkable stairs.
ground(rect((688,352,832,576)),'grass','.');ground(rect((576,336,632,544)),'paving','P')
over('stairs',576,312,'original south-facing stair, complete first/last treads');block((576,312,624,336),'A',False)
over('ramp',624,528,'lighthouse original diagonal timber ramp; native east-west axis');block((632,544,688,576),'A',False)
# Preserve coherent wooden ramp backing under its full footprint.
ground(rect((632,544,688,576)),'deck','A')
ground_mat=mat.copy()
# Service buildings are the exact accepted shared masters, fitted to local lots.
buildings=[('civic-hall',176,144,(19,17)),('house',272,272,(23,24)),('house-pair',496,176,(37,18)),('house-pair',576,176,(42,18)),('cafe',144,400,(15,31)),('center',224,400,(20,31)),('mart',464,400,(36,32)),('lighthouse',688,336,(50,34)),('terminal',304,688,(29,51))]
for name,sx,sy,door in buildings:
 x,y,w,h=over(name,sx,sy,'approved shared service art' if name in ['center','mart'] else 'original local architecture; footprint registered')
 for yy in range(y//16,(y+h+15)//16):
  for xx in range(x//16,(x+w+15)//16):
   a=art[name][max(0,yy*16-y):min(h,yy*16+16-y),max(0,xx*16-x):min(w,xx*16+16-x)]
   if a.size and (a[...,3]>0).any():
    mat[yy,xx]='B';above[yy,xx]=yy*16<y+h-24
    if yy*16>=y+h-32:solid[yy,xx]=True
# Complete forest crowns: trunks occupy distinct 2x2 roots. Padding completes
# all clipped HGSS perimeter trees; paths and original clearings remain open.
def tree(sx,sy):
 x,y=px(sx,sy);cx,cy=x//16,y//16
 if x<0 or y<0 or x+32>W*16 or y+48>H*16:return
 if roots[cy+1:cy+3,cx:cx+2].any():return
 if any(sx<bx+art[n].shape[1] and sx+32>bx and sy+16<by+art[n].shape[0] and sy+48>by and not(n=='lighthouse' and sy<352) for n,bx,by,_ in buildings):return
 if np.any(pave[y+16:y+48,x:x+32]) or np.any(dock[y+16:y+48,x:x+32]):return
 over('tree',sx,sy,'complete shared crown; separate root collision');roots[cy+1:cy+3,cx:cx+2]=1;solid[cy+1:cy+3,cx:cx+2]=True;beh[cy+1:cy+3,cx:cx+2]=0;mat[cy+1:cy+3,cx:cx+2]='T';above[cy,cx:cx+2]=True;trees.append(dict(name='tree',x=cx,y=cy))
for sy in range(-16,448,32):
 for sx in range(-64,1088,32):
  wanted=(sx<64 or (sy<128 and sx<288) or (sx>=528 and sy<128) or (sx>=688 and sy<224) or (688<=sx<816 and sy<352) or (sy<16 and 304<=sx<336))
  if wanted:tree(sx,sy)
for sx,sy in [(496,288),(528,288),(496,320),(496,352),(848,224),(848,288),(848,416),(848,480),(816,224),(816,256),(816,288),(816,320)]:tree(sx,sy)
# Buildings occlude the complete crowns behind them, preserving the original
# dense lighthouse grove instead of clearing its whole rectangular sprite box.
over('lighthouse',688,336,'local lighthouse in front of complete northern grove crowns')
# Timber rail follows quay lip; pier and two mooring openings remain unblocked.
for sx in range(104,632,32):
 if 248<=sx<328 or 344<=sx<440 or 472<=sx<552:continue
 over('rail',sx,624,'continuous quayside railing');block((sx,632,sx+32,640),'F')
for sx in [136,248,488]:
 over('bench',sx-8,576,'original quay bench, full feet and contact');block((sx,592,sx+64,608),'F')
 over('umbrella',sx,544,'original blue parasol over independent deck');above[(544+OY)//16:(576+OY)//16,(sx+OX)//16:(sx+OX+64)//16]=True
for sx in [248,472]:over('boat',sx,608,'original sailboat; entire mast/sail/hull silhouette; marine foreground')
for sx,sy in [(104,272),(328,384),(328,0)]:
 over('bunting',sx,sy,'original maritime street bunting; open below suspended flags');block((sx+4,sy+32,sx+16,sy+56),'F');block((sx+132,sy+32,sx+144,sy+56),'F');above[(sy+OY)//16:(sy+OY+32)//16,(sx+OX)//16:(sx+OX+152)//16]=True
for sx,sy in [(160,208),(384,328),(760,512),(392,560)]:
 over('P12',sx,sy,'shared sign on original sign footprint');block((sx,sy+16,sx+16,sy+32),'S')
for sx,sy in [(520,336),(848,256),(848,448),(848,512)]:over('land-rock',sx,sy,'complete local outcrop over independent ground');block((sx+8,sy+16,sx+24,sy+32),'R')
# Original breakwater chain, including the stepped lower elbow. One native rock
# master retains a real outline over water; it is never used as land or a cliff.
rocks=[(952,304),(968,352),(904,376),(944,384),(936,408),(936,432),(936,456),(944,480),(952,504),(968,528),(968,552),(968,576),(984,600),(1000,624),(1016,648),(1000,672),(968,680),(936,680),(904,680),(872,680),(840,688),(808,696),(776,704),(744,704),(712,704),(680,704),(648,704),(616,704),(584,704),(552,704),(520,704),(488,704),(248,728),(216,728),(184,712),(152,704),(120,704),(88,704),(56,704),(24,704),(88,640),(88,672)]
for sx,sy in rocks:
 over('sea-rock',sx,sy,'individual original breakwater boulder; independent surf water');block((sx+4,sy+16,sx+28,sy+32),'R')
solid[0]=True;solid[-1]=True;solid[:,0]=True;solid[:,-1]=True
# Do not render collision/water behind solid foreground as foreground geometry.
for gy,gx in np.ndindex(H*2,W*2):
 sl=np.s_[gy*8:gy*8+8,gx*8:gx*8+8]
 if np.all(fg[sl][...,3]==255):bg[sl]=art['grass'][Y[sl]%16,X[sl]%16]
Image.fromarray(bg).save(S/'background.png');Image.fromarray(fg).save(S/'foreground.png')
for name,a in [('material-grid',mat),('ground-material-grid',ground_mat),('solid',solid),('behaviors',beh),('tree-footprints',roots)]:np.save(S/(name+'.npy'),a)
(S/'blocks.txt').write_text('\n'.join(''.join(r) for r in mat)+'\n');comp=bg.copy();m=fg[...,3]>0;comp[m]=fg[m];Image.fromarray(comp).save(E/'authoring-preview.png')
stats=[]
for name,bank,y0,y1 in [('JohtoOlivineCity','olivine_city',0,26),('JohtoOlivineQuay','olivine_quay',26,44),('JohtoOlivineHarbor','olivine_harbor',44,H)]:
 inp=S/bank;out=E/(bank+'-compiled');inp.mkdir(exist_ok=True);out.mkdir(exist_ok=True);unique={};cells=[];pairs=[]
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
 for sec in [False,True]:
  folder=G/f'data/tilesets/{"secondary" if sec else "primary"}/{bank}';(folder/'palettes').mkdir(parents=True,exist_ok=True);start=512 if sec else 0;sh=Image.new('P',(128,256));sh.putpalette(tileim.getpalette())
  for i in range(512):
   tid=start+i
   if tid//16*8<tileim.height:sh.paste(tileim.crop((tid%16*8,tid//16*8,tid%16*8+8,tid//16*8+8)),(i%16*8,i//16*8))
  sh.save(folder/'tiles.png',bits=4)
  for i in range(16):
   p=out/'palettes'/f'{i:02}.pal';(folder/'palettes'/f'{i:02}.pal').write_text(p.read_text() if p.exists() else 'JASC-PAL\n0100\n16\n'+'0 0 0\n'*16)
  (folder/'metatiles.bin').write_bytes(blocks[start*16:(start+512)*16] or bytes(16));(folder/'metatile_attributes.bin').write_bytes(attrs[start*2:(start+512)*2] or bytes(2))
 layout=G/'data/layouts'/name;layout.mkdir(exist_ok=True);grid=np.array(cells,dtype='<u2').reshape(y1-y0,W);grid.tofile(layout/'map.bin');np.full((2,2),grid[18 if y0==0 else 1,28]|0xc00,dtype='<u2').tofile(layout/'border.bin')
 stats.append(dict(map=name,tileset=bank,width=W,height=y1-y0,global_y=y0,metatiles=len(pairs),compiler='Porytiles legacy 2.0.0',command=cmd))
(E/'assembly.json').write_text(json.dumps(dict(size=[W,H],reference_size=[1035,858],registration_offset=[OX,OY],districts=stats,trees=trees,buildings=buildings,placements=placements),indent=2)+'\n');print(json.dumps(stats,indent=2))
