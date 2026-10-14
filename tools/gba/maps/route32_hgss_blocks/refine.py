"""Owner-authorized Route32 refinement; original HGSS is the placement authority.
Preserves the first draft and other maps. Native Emerald directional geometry,
accepted Cherrygrove colors/ground/trees, measured foreground masks and two BG layers.
"""
from pathlib import Path
import sys,json,shutil,struct,re
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from scipy.ndimage import distance_transform_edt
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));sys.path.insert(0,str(HERE.parent))
from tiles import Tileset,palette
from claude_cherrygrove.pixel import Canvas,Palette
from claude_cherrygrove import build as native,ground
from claude_routes import build as packing
from cherrygrove_synthesis import refine as cg_ground
import build as draft,layers,preservation
ROOT=HERE.parents[3];OUT=ROOT/'gba/art/route32-hgss-blocks';S=OUT/'source';E=OUT/'evidence';M=S/'refined-materials';W,H=32,128

def raster(polys):
 im=Image.new('1',(512,2048));d=ImageDraw.Draw(im)
 for poly in polys:d.polygon(poly,fill=1)
 a=np.asarray(im,bool);out=np.zeros((H,W),bool)
 # Sample the true cell centers; rounding inclusive polygon vertices inflated every footprint.
 for y in range(1,126):
  for x in range(1,31):out[y,x]=a[(y-1)*16+8,(x-1)*16+8]
 return out

def ground_painter(pals):
 # Read committed Cherrygrove source strips without rewriting their provenance.
 textures={};folder=ROOT/'gba/art/cherrygrove-synthesis/references/HGSS-direct';pp=np.array(pals[0].gba()[1:],int)
 for name in ['grass','path','sand']:
  rgb=np.array(Image.open(folder/f'{name}-source.png').convert('RGB'),int);textures[name]=((rgb[...,None,:]-pp)**2).sum(3).argmin(2).astype(np.uint8)+1
 edges={}
 rgb=np.array(Image.open(folder/'path-edge-source.png').convert('RGB'),int);inside=(rgb[...,0]>rgb[...,1])&(rgb[...,0]>150);anchors=np.array([np.flatnonzero(r)[-1] for r in inside]);idx=((rgb[...,None,:]-pp)**2).sum(3).argmin(2).astype(np.uint8)+1
 edges['path-edge']={'idx':idx,'bank':np.zeros(idx.shape,np.uint8),'anchors':anchors};textures['_edges']=edges
 # Other profiles are unused because Route32 has no beach. Supply compatible source arrays.
 edges['sand-edge']=edges['water-edge']=edges['path-edge'];textures['_sand_sea']=textures['sand'];textures['_sand_lookup']=np.arange(16,dtype=np.uint8)
 def paint(cells,wobble=True):
  h,w=cells.shape;gy,gx=np.indices((h*16,w*16));pg=np.repeat(np.repeat(cells==ground.PATH,16,0),16,1);safe=np.ones(pg.shape,bool);ni=np.zeros(pg.shape,np.uint8);nb=np.zeros(pg.shape,np.uint8);water=np.zeros(pg.shape,bool)
  cg_ground.terrain(ni,nb,safe&~pg,pg,water,gx+640,gy,textures)
  rgba=np.empty((h*16,w*16,4),np.uint8);rgba[...,:3]=np.array(pals[0].gba(),np.uint8)[ni];rgba[...,3]=255
  return rgba,np.repeat(np.repeat(cells,16,0),16,1)
 ground.paint=paint;return {'source':'accepted Cherrygrove HGSS-native ground strips','method':'literal texture phases and signed-distance rounded path rims; no nearest-ground-tile approximation'}

def main(game):
 preservation.check(game,S);M.mkdir(exist_ok=True)
 t=Tileset(game,'cherrygrove','cherrygrove');pals={i:Palette(i,t.pals[i>=6][i][1:],[f'c{j}' for j in range(15)]) for i in range(16)}
 # Palette banks remain supported; existing primary palettes are never modified.
 for b in [6,9,10,12]:pals[b]=Palette(b,palette(game/f'data/tilesets/secondary/route32/palettes/{b:02}.pal')[1:],[f'c{j}' for j in range(15)])
 colors=pals[10].gba()[1:];colors[14]=(248,248,248);pals[10]=Palette(10,colors,[f'r{i}' for i in range(15)])
 a={}
 def canvas(name,rgba,bank):
  rgba=np.asarray(rgba);c=Canvas(rgba.shape[1],rgba.shape[0],pals[bank]);opaque=rgba[...,3]>0;pp=np.array(pals[bank].gba()[1:],int);c.px[opaque]=((rgba[opaque,:3].astype(int)[:,None]-pp)**2).sum(2).argmin(1)+1;a[name]=c;return c
 def indexed(name,bank):
  im=Image.open(ROOT/f'gba/art/cherrygrove-synthesis/refined/{name}.png');c=Canvas(im.width,im.height,pals[bank]);c.px=np.array(im);a[name]=c;return c
 tree=indexed('tree',3);ref=Image.open(S/'hgss-reference.png').convert('RGBA');raw=np.array(ref)
 # Shared Center cleanup: remove only the measured exterior right-edge strip.
 original=np.array(Image.open(S/'shared-art/violet-pokemon-center.png').convert('RGBA'));center=original.copy();center[20:54,99:,3]=0
 center[center[...,3]==0,:3]=0
 canvas('center',center,8);assert np.array_equal(center[79:89,48:64],original[79:89,48:64]),'Center door changed'
 center_removed=int(((original[...,3]>0)&(center[...,3]==0)).sum());Image.fromarray(center).save(S/'shared-art/violet-pokemon-center-cleaned.png')
 # Native Emerald foreground pieces, recolored only through accepted Cherrygrove rock palette.
 donor=Tileset(game)
 def donor_canvas(mid,bank,neutral=False):
  rgba=np.array(donor.render(mid).convert('RGBA'));rgb=rgba[...,:3].astype(int);green=(rgb[...,1]>rgb[...,0]+15)&(rgb[...,1]>rgb[...,2]+15);rgba[green,3]=0
  if neutral:rgba[(rgb.max(2)-rgb.min(2)>12),3]=0
  c=canvas('emerald-'+hex(mid),rgba,bank)
  if bank==2:
   # Material-aware native stone ladder, matching the accepted warm Cherrygrove palette.
   for old,index in [((98,65,82),12),((131,90,90),7),((156,115,115),5),((189,148,139),3),((222,180,164),2),((131,131,139),10)]:
    c.px[np.all(rgb==old,2)&(rgba[...,3]>0)]=index
  return c
 for mid in [0x73,0x75,0x7c,0x85,0x86,0x87,0xd5,0xd6,0xa6,0xa7,0xa8,0x9f]:donor_canvas(mid,2)
 donor_canvas(0xaf,10,True);donor_canvas(0xcf,10,True)
 # Clean native rock-top family: real HGSS chunks, three warm shared colors, one-pixel seamless margins.
 best=None
 for sx in range(286,305,4):
  for sy in range(416,433,4):
   rgb0=np.array(ref.crop((sx,sy,sx+32,sy+32)))
   light=rgb0[...,:3].mean(2);classes=np.where(light>157,0,np.where(light>139,1,2)).astype(np.uint8)
   classes=np.array(Image.fromarray(classes).filter(ImageFilter.MedianFilter(3)))
   error=int(np.abs(classes[:,0].astype(int)-classes[:,-1]).sum()+np.abs(classes[0].astype(int)-classes[-1]).sum())
   if best is None or error<best[0]:best=(error,sx,sy,classes)
 _,soil_x,soil_y,classes=best
 classes[:,0]=classes[:,-1]=np.rint((classes[:,0].astype(float)+classes[:,-1])/2).astype(np.uint8)
 classes[0]=classes[-1]=np.rint((classes[0].astype(float)+classes[-1])/2).astype(np.uint8)
 soil=Canvas(32,32,pals[2]);soil.px=np.array([2,3,4],np.uint8)[classes];a['rock-top']=soil
 for f in (S/'shared-art/materials').glob('grass-*.png'):canvas(f.stem,Image.open(f).convert('RGBA'),12)
 canvas('sign',Image.open(S/'shared-art/materials/sign.png').convert('RGBA'),5)
 # A measured gate silhouette; remove foreign lawn/woods only, not turquoise roofing.
 gate=np.array(Image.open(S/'materials/gate.png').convert('RGBA'));gr=np.array(ref.crop((0,80,96,176)))
 rg=gr[...,:3].astype(int);foreign=((rg[...,1]-rg[...,2]>24)&(rg[...,1]>rg[...,0]+35)&(rg[...,0]>55))|((rg[...,1]>rg[...,0])&(rg[...,2]<80));gate[foreign,3]=0;canvas('gate',gate,6)
 for i in range(4):canvas('rail-'+str(i),Image.open(S/f'materials/rail-{i}.png').convert('RGBA'),10)
 # A complete source boulder, not the clipped half from the prior draft. Separate stone from foam.
 from scipy.ndimage import label,binary_fill_holes,binary_dilation
 rock=np.array(ref.crop((408,1128,440,1160)));rg=rock[...,:3].astype(int);stone=(np.ptp(rg,axis=2)<25)&(rg[...,0]>65)&(rg[...,0]<210);labels,n=label(stone);counts=np.bincount(labels.ravel());counts[0]=0;body=binary_fill_holes(labels==counts.argmax());ring=binary_dilation(body,iterations=1)&~body
 rock[...,3]=body*255;rock[ring,:3]=[192,216,224];rock[ring,3]=255
 colors=pals[10].gba()[1:];colors[13]=(192,216,224);pals[10]=Palette(10,colors,[f'r{i}' for i in range(15)]);canvas('coastal-rock',rock,10)
 # Build clean, long boards with continuous timber seams and restrained grain.
 pals[9]=Palette(9,[(72,64,40),(104,88,56),(128,112,72),(152,128,88),(168,144,96),(184,160,112),(200,176,128)],[f'w{i}' for i in range(7)])
 boards=Canvas(32,32,pals[9]);boards.px[:]=5
 for y in range(32):
  if y%8==0:boards.px[y]=3
  elif y%8==1:boards.px[y]=6
 for x,y,n in [(3,4,5),(18,6,6),(8,13,7),(23,19,4),(2,28,6),(16,30,5)]:boards.px[y,x:x+n]=4
 a['boards']=boards
 # Exact original masks, source grid registration, no inclusive-vertex enlargement.
 traces=json.loads(json.dumps(draft.TRACES))
 # Correct the southern landing's original 10px tracing error against the HGSS reference.
 traces['path'][-1]=[(312,y) if x==340 and y in [1400,1486] else (x,y) for x,y in traces['path'][-1]]
 m={name:raster(poly) for name,poly in traces.items()};p=np.full((H,W),'.',dtype='<U1')
 rgb=raw[...,:3].astype(int);woods=(rgb[...,1]>rgb[...,0])&(rgb[...,2]<80);score=np.zeros((H,W));score[1:126,1:31]=woods[:2000,:480].reshape(125,16,30,16).mean((1,3));score[:,0]=score[:,-1]=1;score[:2]=1;score[-2:]=1
 # Preserve the measured first-draft marine contour, correcting fringe islands at piers.
 old=np.load(S/'revision-baseline/plan.npy');m['water']=np.isin(old,['W','D'])
 for name,ch in [('water','W'),('path','P'),('grass','G'),('cliff','R'),('dock','D')]:p[m[name]]=ch
 # Original small eastern sea outcrops, omitted from the first draft.
 for poly in [[(429,1197),(490,1197),(490,1248),(443,1248),(443,1236),(429,1236)],[(436,1298),(469,1298),(469,1321),(490,1321),(490,1367),(417,1367),(417,1339),(436,1339)]]:
  p[raster([poly])]='R'
 p[66:70,12:]='W';p[66:70,18:20]='D'
 # Source stairs: east-west 32x48 at the northern descent, north-south 48x32 below.
 p[59:62,9:11]='S';p[59:62,8]='P';p[59:62,11]='G'
 p[87:89,6:9]='S';p[89,6:9]='P';p[86,6:9]='G';p[87:90,5]='R';p[87:90,9]='R'
 # Source paths and terrace ledges; each has a landing, never a texture endpoint against stairs.
 p[27,24:27]='_';p[44:46,21]='P';p[46,21]='_'
 p[104:111,18:24]='P';p[6:12,1:7]='.'
 # Keep Center at its established door coordinate; make a joined dirt forecourt.
 p[103:109,17:24]='.';p[109:111,18:24]='P';p[117:120,12:18]='P';p[125,12:23]='R'
 cells=np.full((H,W),ground.GRASS,np.int8);cells[p=='P']=ground.PATH;cells[p=='S']=ground.PATH
 solid=np.isin(p,list('RW_'));beh=np.zeros((H,W),np.uint8);beh[p=='W']=21
 mc=native.MapCanvas(W,H);fore=native.MapCanvas(W,H)
 def put(c,x,y,fg=False):
  mc.blit(c,x*16,y*16)
  if fg:fore.blit(c,x*16,y*16)
 # Render each entire landform, including convex and concave joins, before foreground props.
 mask=np.repeat(np.repeat(p=='R',16,0),16,1)
 for y,x in zip(*np.where(p=='R')):
  for dy,dx in [(-1,-1),(-1,1),(1,-1),(1,1)]:
   if y==125 and x>=12:continue # The source's southern ridge is cropped by the reference edge.
   ny,nx=y+dy,x+dx
   ey,ex=y+dy,x;sy,sx=y,x+dx
   if 0<=ey<H and 0<=sx<W and p[ey,ex]!='R' and p[sy,sx]!='R':
    yy,xx=np.indices((16,16));u=xx if dx<0 else 15-xx;v=yy if dy<0 else 15-yy;outside=(u<7)&(v<7)&((7-u)**2+(7-v)**2>49);mask[y*16:y*16+16,x*16:x*16+16][outside]=False
 # Measured HGSS terrace heights: these are drawn levels on inaccessible rock, not new mechanics.
 heights=np.where(p=='R',2,0).astype(np.uint8)
 terrace_specs=[(3,[[(218,260),(368,260),(368,332),(218,332)]]),
                (5,[[(359,616),(388,616),(388,572),(490,572),(490,853),(359,853)]]),
                (4,[[(294,818),(359,818),(359,853),(490,853),(490,880),(294,880)]]),
                (3,[[(137,850),(294,850),(294,880),(490,880),(490,894),(137,894)]]),
                (2,[[(137,894),(490,894),(490,927),(137,927)]]),
                (1,[[(137,927),(490,927),(490,948),(137,948)]])]
 for level,polys in terrace_specs:
  region=raster(polys)&(p=='R');heights[region]=np.maximum(heights[region],level) if level>1 else 1
 hp=np.repeat(np.repeat(heights,16,0),16,1);hp[~mask]=0
 # Ease each upper convex corner into its lower shelf, never into an arbitrary lawn tile.
 for level in range(2,6):
  high=heights>=level
  for cy,cx in zip(*np.where(high)):
   for dy,dx in [(-1,-1),(-1,1),(1,-1),(1,1)]:
    if cy==125 and cx>=12:continue
    ny,nx=cy+dy,cx+dx
    if 0<=ny<H and 0<=nx<W and not high[ny,cx] and not high[cy,nx]:
     vv,uu=np.indices((16,16));u=uu if dx<0 else 15-uu;v=vv if dy<0 else 15-vv;cut=(u<7)&(v<7)&((7-u)**2+(7-v)**2>49);block=hp[cy*16:cy*16+16,cx*16:cx*16+16];block[cut&(block>=level)]=level-1
 yy,xx=np.indices(mask.shape);west=np.zeros(mask.shape,int);east=west.copy();south=west.copy();north=west.copy()
 for level in range(1,6):
  threshold=hp>=level;select=hp==level
  wd=xx-np.maximum.accumulate(np.where(~threshold,xx,-1),axis=1)-1
  ed=(xx-np.maximum.accumulate(np.where(~threshold[:,::-1],xx,-1),axis=1)-1)[:,::-1]
  sd=(yy-np.maximum.accumulate(np.where(~threshold[::-1],yy,-1),axis=0)-1)[::-1]
  nd=yy-np.maximum.accumulate(np.where(~threshold,yy,-1),axis=0)-1
  for dst,src in [(west,wd),(east,ed),(south,sd),(north,nd)]:dst[select]=src[select]
 rockpixels=a['rock-top'].px[yy%32,xx%32].copy();face=a['emerald-0x7c'].px;front=mask&(south<16);rockpixels[front]=face[(15-south[front]).clip(0,15),xx[front]%16]
 left=mask&(west<10)&~front;right=mask&(east<10)&~front;rockpixels[left]=a['emerald-0x73'].px[yy[left]%16,west[left].clip(0,15)];rockpixels[right]=a['emerald-0x75'].px[yy[right]%16,(15-east[right]).clip(0,15)]
 # A continuous cap separates top plane from face; quarter corners share the same profile.
 rockpixels[mask&(south==15)]=2;rockpixels[mask&(north==0)]=2
 rockpixels[~mask]=0;cliff=Canvas(W*16,H*16,pals[2]);cliff.px=rockpixels;mc.blit(cliff,0,0)
 for y in range(H):
  for x in range(W):
   ch=p[y,x]
   if ch=='G':
    bits=''.join(str(int(0<=nx<W and 0<=ny<H and p[ny,nx]=='G')) for ny,nx in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]);put(a['grass-'+bits],x,y);beh[y,x]=2
   elif ch=='D':
    c=Canvas(16,16,pals[9]);c.px=boards.px[(y%2)*16:(y%2+1)*16,(x%2)*16:(x%2+1)*16].copy()
    for side,ny,nx in [('n',y-1,x),('s',y+1,x),('w',y,x-1),('e',y,x+1)]:
     if 0<=ny<H and 0<=nx<W and p[ny,nx]=='D':continue
     if side=='n':c.px[:2]=2;c.px[2]=7
     elif side=='s':c.px[-3]=3;c.px[-2]=2;c.px[-1]=1
     elif side=='w':c.px[:,:2]=2;c.px[:,2]=7
     else:c.px[:,-3]=3;c.px[:,-2]=2;c.px[:,-1]=1
    put(c,x,y)
   elif ch=='_':
    mid=0xd5 if x==0 or p[y,x-1]!='_' else 0xd6 if x+1==W or p[y,x+1]!='_' else 0x87;put(a['emerald-'+hex(mid)],x,y);beh[y,x]=59
 # Complete native stair assemblies; original stair pixels, correct direction, mirrored end rail.
 edge=a['emerald-0xaf'].px;step=a['emerald-0xcf'].px
 north=Canvas(48,32,pals[10]);north.px=np.tile(np.concatenate([edge,step,edge[:,::-1]],axis=1),(2,1))
 eaststairs=Canvas(32,48,pals[10]);eaststairs.px=np.rot90(north.px).copy();a['stairs-ns']=north;a['stairs-ew']=eaststairs
 put(eaststairs,9,59);put(north,6,87)
 # Native jambs form a complete 32px doorway, with continuous black opening on the foreground layer.
 for x,mid in [(12,0xa6),(15,0xa8)]:put(a['emerald-'+hex(mid)],x,116)
 cave_rgb=np.concatenate([np.array(donor.render(0x9f)),np.array(donor.render(0xa7))],axis=0)
 cave_rgb=np.concatenate([cave_rgb[:,:8],np.repeat(cave_rgb[:,7:8],8,1),np.repeat(cave_rgb[:,8:9],8,1),cave_rgb[:,8:]],axis=1)
 canvas('cave-native-frame',np.dstack([cave_rgb,np.full((32,32),255,np.uint8)]),2);put(a['cave-native-frame'],13,115)
 mc.background_bank=mc.bank.copy();mc.background_idx=mc.idx.copy()
 # Whole trees on shared two-row ground courses. Score entire footprints, not isolated color pixels.
 reserved=np.zeros((H,W),bool);reserved[5:12,0:7]=True;reserved[101:111,17:25]=True;reserved[:8,22:26]=True
 for x,y in [(16,8),(22,15),(20,122)]:reserved[y-1:y+2,x:x+1]=True
 roots=np.zeros((H,W),bool);positions=[];absorbed=0
 for y in range(0,H-2,2):
  candidates=[]
  for x in range(W-1):
   area=p[y+1:y+3,x:x+2];target=score[y+1:y+3,x:x+2];canopy=p[y,x:x+2]
   if not np.all(area=='.') or reserved[y:y+3,x:x+2].any() or not np.all(np.isin(canopy,['.','R'])):continue
   wanted=int((target>.25).sum())
   if not wanted:continue
   candidates.append((-wanted,int((target<.2).sum()),x%2,x))
  for _,cost,phase,x in sorted(candidates):
   if roots[y+1:y+3,x:x+2].any():continue
   roots[y+1:y+3,x:x+2]=True;positions.append((x,y));absorbed+=cost
 opaque=tree.px>0;seen=np.zeros((H*16,W*16),bool);overlap_pixels=0
 for x,y in sorted(positions,key=lambda q:(q[1],q[0])):
  target=seen[y*16:y*16+48,x*16:x*16+32];overlap=target&opaque;assert not overlap[16:].any(),('Tree body overlap',x,y);overlap_pixels+=int(overlap.sum());target|=opaque;put(tree,x,y,True);solid[y+1:y+3,x:x+2]=True;mc.above[y,x:x+2]=True
 for x,y in [(16,8),(22,15),(20,122)]:put(a['sign'],x,y-1,True);solid[y,x]=True;beh[y,x]=29;mc.above[y-1,x]=True
 put(a['center'],17,103,True);solid[104:109,17:24]=True;solid[108,20]=False;beh[108,20]=105;mc.above[103:107,17:24]=True
 put(a['gate'],1,6,True);solid[7:12,1:7]=True;mc.above[6:9,1:7]=True
 for y in range(66,70):
  for x in range(W):put(a['rail-'+str(y-66)],x,y,True);mc.above[y,x]=True
 # Use an exact native-scale source support, isolating it from foam/background.
 support=Canvas(32,64,pals[10]);support.px[:52,5:27]=11;support.px[:52,8:24]=12;support.px[:52,9:12]=13;support.px[52:58,3:29]=8;support.px[58:62,5:27]=7;support.px[62:,6:26]=6
 put(support,24,70,True);solid[73,24:26]=True;beh[73,24:26]=0;mc.above[70:73,24:26]=True
 rocks=[]
 # The northern boulder fence follows HGSS's 24px vertical spacing at native pixel scale.
 for xp,yp in [(26*16,70*16+i*24) for i in range(4)]+[(25*16,79*16),(25*16,81*16),(27*16,81*16),(26*16,88*16),(27*16,91*16),(25*16,93*16),(25*16,96*16)]:
  x,y=xp//16,yp//16;hh=(yp%16+32+15)//16
  if np.all(p[y:y+hh,x:x+2]=='W'):
   mc.blit(a['coastal-rock'],xp,yp);fore.blit(a['coastal-rock'],xp,yp);solid[y:y+hh,x:x+2]=True;beh[y:y+hh,x:x+2]=0;rocks.append([xp,yp])
 mouth=Canvas(32,32,pals[6]);mouth.px[(cave_rgb.max(2)<80)]=1
 put(mouth,13,115,True);mc.above[115,13:15]=True;a['cave-opening']=mouth
 solid[116,13:15]=False;beh[116,13:15]=97
 # Marine rims are overlays on animated native water, not frozen ocean rectangles.
 pals[11]=Palette(11,[(104,208,152),(104,200,152),(88,176,136),(96,192,144),(128,120,112),(104,72,56),(184,136,104),(192,216,224),(200,232,224),(152,224,224),(104,192,224),(72,160,224),(216,184,128)],[f's{i}' for i in range(13)])
 marine=np.repeat(np.repeat(p=='W',16,0),16,1);rounded=np.array(Image.fromarray(marine.astype('uint8')*255).filter(ImageFilter.GaussianBlur(2)))>=128
 distance=distance_transform_edt(rounded)-distance_transform_edt(~rounded)
 for y,x in zip(*np.where(p=='W')):
  if (fore.bank[y*16:y*16+16,x*16:x*16+16]>=0).any():continue
  nearby=[(ny,nx) for ny,nx in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)] if 0<=ny<H and 0<=nx<W and p[ny,nx] not in 'WD']
  if not nearby:continue
  dd=distance[y*16:y*16+16,x*16:x*16+16];stone=any(p[ny,nx]=='R' for ny,nx in nearby);c=Canvas(16,16,pals[11]);c.px[dd<1]=5 if stone else 3;c.px[(dd>=1)&(dd<2)]=8 if stone else 4;c.px[(dd>=2)&(dd<3)]=9 if stone else 10;c.px[(dd>=3)&(dd<4)]=10;c.px[(dd>=4)&(dd<5)]=11;put(c,x,y,True)
 solid[:,0]=True;solid[:,-1]=True;solid[0]=True;solid[0,23:25]=False;solid[-1]=True
 mc.fore_bank=fore.bank;mc.fore_idx=fore.idx;provenance=ground_painter(pals)
 class Primary(packing.Primary):
  def __init__(self,*args):
   super().__init__(*args);self.lookup={}
   for tid in range(93,len(self.tiles)):self._index(tid,self.tiles[tid])
  def find(self,bank,arr):
   hit=self.lookup.get(arr.tobytes())
   if hit is None:return 0 if not arr.any() else None
   tid,hf,vf=hit;return tid|(hf<<10)|(vf<<11)
 class Packer(packing.RoutePacker):
  def metatile(self,entries,attr):
   key=(tuple(entries),attr)
   if key in self.primary.block_lookup:return self.primary.block_lookup[key]
   if key not in self.sblock_lookup:
    mid=512+len(self.sec_blocks);self.sec_blocks[mid]=key;self.sblock_lookup[key]=mid
   return self.sblock_lookup[key]<<16
 primary=Primary(game,92,512);packer=Packer(pals,primary);grid=np.zeros((H,W),np.uint32);comp={'W':W,'H':H,'cells':cells,'solid':solid,'behavior':beh,'canvas':mc};layer_report=layers.pack(comp,packer,pals,grid,S)
 for y,x in zip(*np.where(p=='W')):
  fa=fore.bank[y*16:y*16+16,x*16:x*16+16];ix=fore.idx[y*16:y*16+16,x*16:x*16+16];top=[]
  for q in range(4):
   px=ix[q//2*8:q//2*8+8,q%2*8:q%2*8+8];banks=fa[q//2*8:q//2*8+8,q%2*8:q%2*8+8];bs=[int(v) for v in np.unique(banks) if v>=0];assert len(bs)<=1,(x,y,q,bs);top.append((packer.tile(bs[0],px)|(bs[0]<<12)) if bs and px.any() else 0)
  attr=int(beh[y,x])|(0 if mc.above[y,x] else 0x1000);grid[y,x]=packer.metatile(list(t.blocks[0][58][:4])+top,attr)|0x1000|(0xc00 if beh[y,x]!=21 and solid[y,x] else 0)
 # Rounded sea-side cliff corners expose water, not unrelated grass wedges.
 for y,x in zip(*np.where(p=='R')):
  if (fore.bank[y*16:y*16+16,x*16:x*16+16]>=0).any():continue
  if not any(0<=ny<H and 0<=nx<W and p[ny,nx]=='W' for ny,nx in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]):continue
  top=[]
  for q in range(4):
   px=cliff.px[y*16+q//2*8:y*16+q//2*8+8,x*16+q%2*8:x*16+q%2*8+8];top.append(packer.tile(2,px)|(2<<12) if px.any() else 0)
  grid[y,x]=packer.metatile(list(t.blocks[0][58][:4])+top,0x1000)|0x3c00
 # Drop temporary land-backed ocean variants before allocating final native IDs.
 logical=grid>>16;used=set(int(v) for v in np.unique(logical) if v);primary_mids=set(int(v&1023) for v in grid.ravel() if not v>>16)
 referenced=set();fixed=set()
 for mid in used:
  referenced|={en&1023 for en in packer.sec_blocks[mid][0] if en&1023>=512}
 for mid in primary_mids:
  glyphs={en&1023 for en in t.blocks[0][mid] if en&1023>=512};referenced|=glyphs;fixed|=glyphs
 assert not any(tid>=1008 for tid in fixed),('Primary uses door scratch tiles',fixed)
 if len(referenced)>496:raise SystemExit(f'Native static glyph budget: {len(referenced)} referenced secondary tiles; need<=496')
 free=iter(tid for tid in range(512,1008) if tid not in fixed);glyphmap={tid:tid for tid in fixed}
 for tid in sorted(referenced-fixed):glyphmap[tid]=next(free)
 metamap={mid:512+i for i,mid in enumerate(sorted(used))}
 if len(metamap)>512:raise SystemExit(f'Native metatile budget: {len(metamap)} final secondary entries; need<=512')
 blocks={}
 for mid in used:
  entries,attr=packer.sec_blocks[mid];entries=tuple((en&~1023)|glyphmap.get(en&1023,en&1023) for en in entries);blocks[metamap[mid]]=(entries,attr)
 packer.sec_blocks=blocks;packer.sec_tiles={glyphmap[tid]:packer.sec_tiles[tid] for tid in referenced}
 for y in range(H):
  for x in range(W):
   v=int(grid[y,x]);grid[y,x]=(v&0xfc00)|metamap[v>>16] if v>>16 else v
 nt,nb=packing.write_route_tileset(game,'route32',packer,pals)
 door=game/'src/field_door.c';old=door.read_text();updated=re.sub(r'metatileNum=\d+(, \.tileset=&gTileset_Route32)','metatileNum='+str(int(grid[108,20]&1023))+r'\1',old)
 if updated!=old:door.write_text(updated)
 folder=game/'data/layouts/JohtoRoute32';grid.astype('<u2').tofile(folder/'map.bin')
 ps=set(positions);bx,by=next((x,y) for x,y in positions if (x,y+2) in ps and (x+2,y) in ps and (x+2,y+2) in ps);(grid[by+2:by+4,bx:bx+2]|0xc00).astype('<u2').tofile(folder/'border.bin')
 for name,c in a.items():Image.fromarray(c.to_rgba()).save(M/f'{name}.png')
 Image.fromarray(cliff.to_rgba()).save(E/'cliff-layer.png');np.save(S/'refined-plan.npy',p);np.save(S/'terrace-heights.npy',heights);np.save(S/'solid.npy',solid)
 report={'reference':'original HGSS Route32','authoring_basis':'owner-authorized refinement of rejected7bae845, not owner edits','native_size':[W,H],'terrace_height_sources':terrace_specs,'tiles':nt,'metatiles':nb,'rock_top_reference_box':[soil_x,soil_y,soil_x+32,soil_y+32],'coastal_rocks_pixels':rocks,'whole_trees':positions,'tree_body_overlap_pixels':0,'permitted_rear_canopy_overlap_pixels':overlap_pixels,'open_lawn_absorbed_by_whole_trees':absorbed,'stairs':[{'at':[9,59],'size':[2,3],'direction':'east-west'},{'at':[6,87],'size':[3,2],'direction':'north-south'}],'center':{'shared_source':'Violet Center','exterior_fringe_pixels_removed':center_removed,'door_pixels_unchanged':True,'forecourt_joined':True},'ground':provenance,'cliff':'continuous landform render, real HGSS top texture, native Emerald directional sides/front/cave/ledges in Cherrygrove palette','layers':layer_report}
 native_image=Tileset(game,'route32','cherrygrove').map_image(grid.ravel().tolist(),W);rgb=np.array(native_image);expected=np.zeros_like(rgb);fg_mask=fore.bank>=0
 for bank in np.unique(fore.bank):
  if bank>=0:
   chosen=fore.bank==bank;expected[chosen]=np.array(pals[int(bank)].gba(),np.uint8)[fore.idx[chosen]]
 errors=int((np.any(rgb!=expected,2)&fg_mask).sum());assert errors==0,('Foreground palette/mask errors',errors);report['foreground_RGB_errors']=errors
 (E/'refinement.json').write_text(json.dumps(report,indent=2)+'\n');Tileset(game,'route32','cherrygrove').map_image(grid.ravel().tolist(),W).save(E/'native-map.png');preservation.record(game,S);print('Refined Route32',nt,nb,len(positions))
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
