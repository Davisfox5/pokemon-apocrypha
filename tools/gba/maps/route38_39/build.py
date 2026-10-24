"""Initial terrain authoring only. Committed native maps are authoritative afterward.
HGSS overview trace, cleared foreground by owner request; never replay on tracked layouts.
"""
from pathlib import Path
import sys,json,struct,subprocess,hashlib,shutil
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from tiles import Tileset
G=Path(sys.argv[1]);PT=Path(sys.argv[2]);S=ROOT/'gba/art/route38-39-terrain/source';E=S.parent/'evidence';E.mkdir(exist_ok=True);M=S/'masters';M.mkdir(exist_ok=True)
assert not subprocess.check_output(['git','-C',str(G),'ls-files','data/layouts/JohtoRoute38','data/layouts/JohtoRoute39'],text=True).strip(),'Edit committed native maps directly.'
provenance=[]
for n in ['grass','path','R02','R04','R05','R10','R11','R12']:
 p=ROOT/'gba/art/azalea-town/source/masters'/(n+'.png');shutil.copyfile(p,M/p.name);provenance.append(dict(asset=n,source=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
art={p.stem:np.array(Image.open(p).convert('RGBA')) for p in M.glob('*.png')}
donor=Tileset(G)
for mid in [0xaf,0xcf]:
 im=np.array(donor.render(mid));a=np.full((16,16,4),255,np.uint8);a[...,:3]=im;a[...,3][(im[...,1]>im[...,0]+15)&(im[...,1]>im[...,2]+15)]=0;art[hex(mid)]=a;Image.fromarray(a).save(M/(hex(mid)+'.png'))
provenance.append(dict(asset='stairs',source='unchanged Emerald general metatiles 0xaf / 0xcf; local lawn replaces green transparent donor ground'))
# Pixel trace in each original reference coordinate system. Route39 has +8,+8
# registration to keep its east-west path and 8px cliff shoulders on native axes.
paths={38:[[(0,192),(168,192),(168,64),(544,64),(544,96),(240,96),(240,232),(228,244),(0,244)],[(1077,144),(926,144),(914,153),(902,184),(490,192),(490,240),(720,247),(714,285),(699,303),(491,303),(463,315),(455,345),(368,345),(363,319),(340,316),(328,328),(328,350),(170,355),(170,395),(504,395),(509,346),(740,346),(750,304),(775,271),(857,248),(930,244),(942,187),(962,170),(1077,170)]],39:[[(599,216),(456,216),(432,202),(432,115),(369,115),(363,164),(248,164),(244,155),(223,155),(216,176),(145,177),(140,210),(363,214),(363,396),(431,396),(433,266),(599,264)],[(367,450),(425,450),(425,607),(438,616),(482,616),(482,773),(496,788),(496,881),(427,881),(427,830),(405,803),(336,778),(292,755),(282,738),(282,570),(298,554),(366,549)]]}
results=[];allpairs=[];unique={};maps=[]
for route,W,H,ox,oy in [(38,68,33,0,0),(39,38,56,8,8)]:
 Y,X=np.indices((H*16,W*16));bg=art['grass'][Y%32,X%32].copy();solid=np.zeros((H,W),bool);elev=np.full((H,W),5,np.uint8);mat=np.full((H,W),'lawn',dtype='<U16');records=[]
 mask=Image.new('L',(W*16,H*16));d=ImageDraw.Draw(mask)
 for p in paths[route]:d.polygon([(x+ox,y+oy) for x,y in p],fill=255)
 pm=np.array(mask)>0;bg[pm]=art['path'][Y[pm]%32,X[pm]%32]
 # Existing clean grass/dirt edge vocabulary, without invented curbs or fences.
 from scipy.ndimage import binary_dilation,binary_erosion
 bg[binary_dilation(pm)&~pm,:3]=[88,176,136];bg[pm&~binary_erosion(pm),:3]=[184,168,128]
 for y,x in np.ndindex(H,W):
  n=int(pm[y*16:y*16+16,x*16:x*16+16].sum());mat[y,x]='path' if n==256 else 'path/lawn' if n else 'lawn'
 def rock(x,y,kind,mirror=False,cap=False):
  if not (0<=x<W and 0<=y<H):return
  a=art[kind][:,::-1] if mirror else art[kind];bg[y*16:y*16+16,x*16:x*16+16]=a
  if cap:
   # A continuous local lawn lip belongs to the upper plane. Brown wall texture
   # below is unchanged approved R02/R04, not a custom rock replacement.
   for py in range(3):bg[y*16+py,x*16:x*16+16]=art['grass'][(y*16+py)%32,(np.arange(x*16,x*16+16))%32]
   bg[y*16+3,x*16:x*16+16,:3]=[64,136,104]
  solid[y,x]=True;mat[y,x]='rock-face';records.append(dict(x=x,y=y,asset=kind,mirror=mirror,lawn_cap=cap))
 def front(x0,x1,y):
  for x in range(x0,x1+1):rock(x,y,('R05' if x==x0 else 'R10' if x==x1 else 'R02' if x%2 else 'R04'),cap=True)
 def side(x,y0,y1,mirror=False):
  for y in range(y0,y1+1):rock(x,y,'R11' if y%2 else 'R12',mirror)
 def stairs(x,y,w=3,h=2,upper=5,lower=3):
  for yy in range(h):
   for xx in range(w):
    a=art['0xaf' if xx==0 else '0xcf'];sl=bg[(y+yy)*16:(y+yy+1)*16,(x+xx)*16:(x+xx+1)*16];m=a[...,3]>0;sl[m]=a[m];solid[y+yy,x+xx]=False;elev[y+yy,x+xx]=0;mat[y+yy,x+xx]='stairs'
  records.append(dict(stairs=[x,y,w,h],upper=upper,lower=lower))
 if route==38:
  # Visible southwest cleft, plus southeast forest cleft. Tree-covered
  # continuations terminate at the map edge; no guessed central rock ridges.
  elev[17:,:7]=3;side(7,17,32);side(8,17,32);front(0,8,16)
  elev[22:,34:]=3;side(32,22,32,True);side(33,22,32,True);front(34,67,21)
  # Only the connection's three path lanes cross the outer review boundary.
  solid[0]=solid[-1]=True;solid[:,0]=solid[:,-1]=True;solid[12:15,0]=False
 else:
  elev[28:]=3;elev[28:34,:23]=5
  # The inner western landmass remains above the exposed valley contour.
  elev[34:46,:11]=5;elev[46:49,:15]=5;elev[49:,:22]=5
  elev[25:,:6]=1;front(0,6,24)
  # The eastern outer cleft is inferred as the lower receiving plane.
  elev[18:44,33:]=1;elev[44:,34:]=1;front(32,37,17)
  front(22,30,26)
  for x in range(22,31):rock(x,27,'R02' if x%2 else 'R04')
  side(22,28,32,True);front(7,22,32)
  for x in range(7,23):rock(x,33,'R02' if x%2 else 'R04')
  side(10,34,45,True);front(10,14,46);side(14,47,48,True);front(14,21,49);side(21,50,55,True)
  side(6,25,55)
  side(32,18,43);side(31,28,43);side(33,44,55);side(32,44,55)
  # Recesses/caps join whole directional modules. No jump ledge art/behavior.
  stairs(24,26)
  # Fit the path to the first and last treads, clearing the old fence gap.
  for yy in [25,28]:
   for xx in range(24,27):
    bg[yy*16:(yy+1)*16,xx*16:(xx+1)*16]=art['path'][Y[yy*16:(yy+1)*16,xx*16:(xx+1)*16]%32,X[yy*16:(yy+1)*16,xx*16:(xx+1)*16]%32];mat[yy,xx]='path'
  elev[52:,22:32]=1;front(22,31,50)
  for x in range(22,32):rock(x,51,'R02' if x%2 else 'R04')
  stairs(28,50,3,2,3,1)
  solid[0]=solid[-1]=True;solid[:,0]=solid[:,-1]=True;solid[14:17,-1]=False
 # Ground phase at the route seam is aligned (32px vertical registration).
 # Native geographic review is intentionally bounded; endpoints to cities are
 # not connected in this terrain pass and have no fake gates or signs.
 bg[...,:3]&=248
 Image.fromarray(bg).save(S/f'route{route}-terrain.png');np.save(S/f'route{route}-solid.npy',solid);np.save(S/f'route{route}-elevation.npy',elev)
 (S/f'route{route}-materials.json').write_text(json.dumps(mat.tolist(),indent=1)+'\n')
 (S/f'route{route}-trace.json').write_text(json.dumps(dict(reference=f'hgss-route{route}.png',reference_sha256=hashlib.sha256((S/f'hgss-route{route}.png').read_bytes()).hexdigest(),native_size=[W,H],reference_origin_native_px=[ox,oy],path_polygons=paths[route],rock_and_stair_modules=records,adaptations=['all trees/fences/buildings/props/NPCs/tall grass/jump ledges removed','hidden terrain inferred from adjacent lawns and contour continuity','occluded rock banks completed to boundary; upper forest terrain inferred','external city endpoints bounded and unwired; native Route38/39 connection retained'],elevation_units='relative native planes: south/outer clefts1, valley3, farm/route5; stair cells0 bridge planes. Hidden outer planes are inferred, not decoded original heights'),indent=2)+'\n')
 cells=[]
 for y,x in np.ndindex(H,W):
  a=bg[y*16:y*16+16,x*16:x*16+16];k=a.tobytes()
  if k not in unique:unique[k]=len(allpairs);allpairs.append(a.copy())
  cells.append(unique[k]|int(elev[y,x])<<12|(0xc00 if solid[y,x] else 0))
 maps.append((route,W,H,np.array(cells,'<u2').reshape(H,W)))
 results.append(dict(route=route,width=W,height=H,cliff_cells=int((mat=='rock-face').sum()),stair_cells=int((mat=='stairs').sum()),walkable_cells=int((~solid).sum()),native_elevations=sorted(map(int,np.unique(elev)))))
# Both routes share the same new native bank. Porytiles deduplicates original
# texture quadrants exactly, with no nearest-color substitutions.
inp=S/'porytiles';out=E/'compiled';inp.mkdir(exist_ok=True);out.mkdir(exist_ok=True);rows=(len(allpairs)+7)//8
bottom=Image.new('RGBA',(128,rows*16));empty=bottom.copy()
for i,a in enumerate(allpairs):bottom.paste(Image.fromarray(a),(i%8*16,i//8*16))
bottom.save(inp/'bottom.png');empty.save(inp/'middle.png');empty.save(inp/'top.png')
cmd=[str(PT),'compile-primary','-dual-layer','-tiles-primary-override=1008','-tiles-total-override=1024','-metatiles-primary-override=1024','-pals-primary-override=13','-o',str(out),str(inp),str(G/'include/constants/metatile_behaviors.h')]
r=subprocess.run(cmd,capture_output=True,text=True);(E/'porytiles.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
im=Image.open(out/'tiles.png');blocks=(out/'metatiles.bin').read_bytes()[:len(allpairs)*16];attrs=struct.pack('<H',0x1000)*len(allpairs)
for sec in [False,True]:
 folder=G/f'data/tilesets/{"secondary" if sec else "primary"}/route38_39';(folder/'palettes').mkdir(parents=True,exist_ok=True);start=512 if sec else 0
 sh=Image.new('P',(128,256));sh.putpalette(im.getpalette())
 for i in range(512):
  tid=start+i
  if tid//16*8<im.height:sh.paste(im.crop((tid%16*8,tid//16*8,tid%16*8+8,tid//16*8+8)),(i%16*8,i//16*8))
 sh.save(folder/'tiles.png',bits=4)
 for i in range(16):
  p=out/'palettes'/f'{i:02}.pal';(folder/'palettes'/f'{i:02}.pal').write_text(p.read_text() if p.exists() else 'JASC-PAL\n0100\n16\n'+'0 0 0\n'*16)
 (folder/'metatiles.bin').write_bytes(blocks[start*16:(start+512)*16] or bytes(16));(folder/'metatile_attributes.bin').write_bytes(attrs[start*2:(start+512)*2] or bytes(2))
for route,W,H,grid in maps:
 folder=G/f'data/layouts/JohtoRoute{route}';folder.mkdir(exist_ok=True);grid.tofile(folder/'map.bin');np.full((2,2),grid[1,1]|0xc00,'<u2').tofile(folder/'border.bin')
(E/'assembly.json').write_text(json.dumps(dict(routes=results,metatiles=len(allpairs),glyphs=im.height//8*16,palette_banks=len(list((out/'palettes').glob('*.pal'))),command=cmd),indent=2)+'\n');(S/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');print(results,len(allpairs))
