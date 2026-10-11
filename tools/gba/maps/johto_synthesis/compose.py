"""Reuse approved indexed Cherrygrove assets on the measured Johto plans."""
from pathlib import Path
import sys, copy
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from claude_cherrygrove import build as town,ground
from claude_cherrygrove.pixel import Canvas,Palette
from claude_routes import build as routes,layouts as L,art as ra
from johto_native_refinement import art as oldart
from johto_cohesion import art as grass_art
from johto_polish import art as hgss_terrain
from johto_native_refinement import build as old
from cherrygrove_synthesis import refine
from tiles import Tileset,palette
ROOT=HERE.parents[3];APP=ROOT/'gba/art/cherrygrove-synthesis';OUT=ROOT/'gba/art/johto-synthesis'
SOURCE=ROOT/'tools/vendor/gba/cherrygrove-synthesis-work'

def pal(bank,colors):return Palette(bank,colors[1:],[f'c{i}' for i in range(15)])
def indexed(im,bank,pals):
 im=np.asarray(im);c=Canvas(im.shape[1],im.shape[0],pals[bank]);c.pool='secondary'
 if im.ndim==2:c.px=im.copy()
 else:
  pp=np.array(pals[bank].gba()[1:],int);m=im[...,3]>0;c.px[m]=((im[m,:3].astype(int)[:,None]-pp)**2).sum(-1).argmin(-1)+1
 return c

def assets():
 t=Tileset(SOURCE,'cherrygrove','cherrygrove');pals={b:pal(b,t.pals[b>=6][b]) for b in range(13)}
 base,_=town.build_assets();a={}
 for name in ('house','house_mirror','house2','gable','center','mart','tree','blossom'):
  bank={'house':6,'house_mirror':6,'house2':7,'gable':6,'center':8,'mart':9,'tree':3,'blossom':10}[name]
  a[name]=indexed(Image.open(APP/'refined'/f'{name}.png'),bank,pals)
 for name,c in base.items():
  if name not in a:a[name]=indexed(c.to_rgba(),4 if name not in ('sign','bench','mailbox') else 5,pals)
 a['cliff']=indexed(Image.open(APP/'references/C/cliff.idx.png'),2,pals)
 # Preserve the approved laboratory's exact converted source and palette.
 lab=np.asarray(Image.open(ROOT/'gba/art/johto-native-refinement/native/institute.png').convert('RGBA'))
 labpal=palette(OUT/'references/native-base/data/tilesets/secondary/new_bark/palettes/08.pal')
 labpals=dict(pals);labpals[8]=pal(8,labpal);a['institute']=indexed(lab,8,labpals)
 # Route tall grass keeps the recovered HGSS ladder, in its own bank.
 grass=grass_art.tall_slices();cols=[]
 for c in grass.reshape(-1,4):
  rgb=tuple(c[:3]);
  if c[3] and rgb not in cols:cols.append(rgb)
 pals[11]=Palette(11,cols,[f'c{i}' for i in range(len(cols))])
 for n in (0,1):
  for s in (0,1):
   for w in (0,1):
    for e in (0,1):a[f'tall{n}{s}{w}{e}']=indexed(grass_art.tall_cell(grass,n,s,w,e),11,pals)
 # Thin earthen ledges and orientation-specific faces are actual HGSS cuts.
 for k,v in ra.ledges().items():a[k]=indexed(v,2,pals)
 # The left donor crop includes a foreground tree trunk. Reuse the clean HGSS
 # end cap mirrored, retaining its actual pixels and eliminating that fragment.
 a['ledge_l']=a['ledge_r'].flip()
 for k,v in ra.cliff_pieces().items():a[k]=indexed(v,2,pals)
 for k in ('top','mid','low'):a['stairs_'+k]=indexed(ra.stairs(k),5,pals)
 bridge=ra.cells(30,15,5,2,3);bridge[:,24:,3]=0
 rgb=bridge[...,:3].astype(int);bridge[(rgb[...,1]>rgb[...,0]+15)&(rgb[...,1]>rgb[...,2]+15),3]=0
 a['plateau_bridge']=indexed(bridge,5,pals)
 a['apricorn']=indexed(ra.apricorn(),3,pals);a['berry_tree']=indexed(ra.berry_tree(),3,pals);a['orange']=indexed(a['daisies'].to_rgba()[:16,:16],4,pals)
 # Architecture is placed whole and cell aligned, keeping the door anchors.
 def padded(c,w,h,x,y):
  r=Canvas(w,h,c.pal);r.px[y:y+c.h,x:x+c.w]=c.px;r.pool='secondary';return r
 a['gate']=padded(a['gable'],144,144,32,64)
 a['mr_pokemon']=padded(a['gable'],112,112,16,16)
 a['berry_house']=padded(a['house2'],96,80,0,0)
 for name in ('annex','staff_b'):a[name]=a['gable']
 a['west_house']=a['house'];a['east_house']=a['house2'];a['staff_a']=a['house']
 props=oldart.props(a)
 for name,v in props.items():a[name]=indexed(v,4,pals)
 a['upper_wind']=a['wind'];a['east_mailbox']=a['red_mailbox']
 # Keep Cherrygrove's warm rock palette, with black and a cool cave threshold.
 pals[12]=Palette(12,pals[2].colors[:13]+[(0,0,0),(64,64,80)],[f'c{i}' for i in range(15)])
 raw=hgss_terrain.route31();land=raw['cliff'].copy()
 # Remove the reference's sign with the adjacent identical bottom face course.
 land[192:224,80:112]=land[192:224,48:80]
 # Exact silhouettes; reject only green ground outside the rock, never rock colors.
 def no_ground(v):
  v=v.copy();rgb=v[...,:3].astype(int)
  v[(rgb[...,1]>rgb[...,0]+15)&(rgb[...,1]>rgb[...,2]+15),3]=0
  return v
 land=no_ground(land)
 # Reuse a native 32px plateau material inside the source's measured tiers.
 # Keep the real terrace lips, vertical faces, corners and cave silhouette.
 from PIL import ImageDraw
 mask=Image.new('L',(288,224));d=ImageDraw.Draw(mask)
 for poly in [[(184,0),(287,0),(287,120),(194,120),(184,108)],
              [(120,16),(160,16),(160,112),(176,144),(287,144),(287,152),(144,152),(136,136),(120,120)],
              [(40,32),(96,32),(96,76),(80,76),(64,64),(48,64)],
              [(64,80),(96,80),(104,112),(128,144),(128,168),(64,168)]]:
  d.polygon(poly,fill=255)
 d.rectangle((48,24,95,31),fill=255)
 src=np.asarray(Image.open(ROOT/'gba/art/hgss-connections/references/route31-hgss.png').convert('RGBA').crop((928,32,960,64)))
 reuse=np.tile(src,(7,9,1));inside=np.asarray(mask)>0;inside=np.repeat(np.repeat(inside.reshape(28,8,36,8).all(axis=(1,3)),8,0),8,1);land[inside]=reuse[inside]
 # A repeated straight face course is reusable; preserve all stepped corners.
 land[160:192,192:288]=np.tile(land[160:192,208:240],(1,3,1))
 # Shift the complete arch eight pixels to align its center with warp (52,13).
 # Rock terraces move together; the source's right edge continues off-map.
 expanded=np.zeros((224,304,4),np.uint8);expanded[:,8:296]=land;expanded[:,296:]=land[:,-8:]
 a['landform']=indexed(expanded,12,pals)
 im=Image.open(ROOT/'gba/art/hgss-connections/references/route31-hgss.png').convert('RGBA')
 a['route31_wall']=indexed(no_ground(np.asarray(im.crop((536,144,552,176)))),12,pals)
 a['bridge']=indexed(raw['bridge'],5,pals)
 # The full landform already contains the actual cave arch; no second stamp.
 a['cave_mouth']=Canvas(48,48,pals[12]);a['bankwall']=Canvas(16,16,pals[12])
 return a,pals,labpals[8]

WALL={'house':(0,1,4,5),'house2':(0,1,4,5),'gable':(1,1,5,5)}
def building_geometry(comp,name,c,x,y,wall,door=None):
 mc=comp['canvas'];solid=comp['solid'];l,t,r,b=wall
 solid[y:y+c.h//16,x:x+c.w//16]=False
 for yy in range(c.h//16):
  for xx in range(c.w//16):
   if not c.px[yy*16:yy*16+16,xx*16:xx*16+16].any():continue
   solid[y+yy,x+xx]=l<=xx<r and t<=yy<b
   if not solid[y+yy,x+xx]:mc.above[y+yy,x+xx]=True
 if door:
  dx,dy=door;solid[dy,dx]=False;comp['behavior'][dy,dx]=105
 comp.setdefault('buildings',[]).append(dict(name=name,x=x,y=y,width=c.w//16,height=c.h//16,wall=[x+l,y+t,r-l,b-t],door=door))

def route_comp(number,a):
 p=L.route29() if number==29 else L.route30()
 if number==30:
  # The HGSS cliff divides the main northern lane from Mr Pokemon's plateau.
  p[3:28,15]='#';p[5:8,15:17]='.'
  p[28:33,25:28]='.'
  for _,x,y,_ in L.R30_STAIRS:
   if y>1:p[y-2:y,x:x+2]='P'
   if y+3<len(p):p[y+2:y+4,x:x+2]='P'
 # Suppress old interleaved trees, then stamp whole approved trees only.
 stub=Canvas(32,48,a['tree'].pal);aa=dict(a,tree=stub,blossom=stub)
 comp=routes.compose(number,p,aa);mc=comp['canvas'];p=comp['plan']
 # Positions are unchanged; Mr Pokemon roof is snapped to full cells instead
 # of the old -4px placement, so its doorway and wall face align cleanly.
 if number==30:
  mx,my=L.R30_MR_POKEMON
  mask=(mc.bank==6);mc.bank[mask]=-1;mc.idx[mask]=0
  mc.blit(a['mr_pokemon'],mx*16,my*16)
  mc.blit(a['plateau_bridge'],15*16,5*16)
 forest_plan=np.pad(p,((1,0),(0,0)),constant_values='T') if number==30 else p
 for px,py,c in oldart.forest(forest_plan,a['tree']):
  if number==30:
   py-=16
   if py<0 or py+48>len(p)*16:continue
  c=a['blossom'] if number==29 and px//16<=6 else c
  # Trees are in forest-only footprints; nothing clips through architecture.
  mc.blit(c,px,py)
 comp['solid'][p=='T']=True
 if number==29:
  x,y=L.R29_GATE;building_geometry(comp,'closed-route46-gate',a['gable'],x+2,y+4,WALL['gable'])
 else:
  x,y=L.R30_MR_POKEMON;building_geometry(comp,'mr-pokemon',a['gable'],x+1,y+1,WALL['gable'])
  x,y=L.R30_BERRY_HOUSE;building_geometry(comp,'berry-house',a['house2'],x,y,WALL['house2'])
 return comp

def new_bark(a):
 p=old.layout('new_bark');q=np.full((50,36),'T',dtype='<U1');q[:24,6:]=p;q[9:14,:6]='.';q[12:14,:6]='P';q[22:42,7:29]='.';q[7:12,16:18]='P';q[21:41,16:18]='P';q[31:33,9:28]='P';q[40:42,9:28]='P';q[29:32,10:12]='P';q[29:32,25:27]='P';q[38:41,10:12]='P';q[38:41,25:27]='P';q[12:39,34:]='W';q[38:,30:]='W'
  # Move windmills into dedicated lawn pockets before trees are placed.
 q[14:18,19:21]='.';q[16:20,30:32]='.';q[3:7,24:26]='.';q[6:10,32:34]='.'
 aa=dict(a)
 for key in ('wind','labwind','upper_wind'):
  aa[key]=Canvas(a[key].w,a[key].h,a[key].pal)
 comp=old.compose('new_bark',q,aa)
 for x,y in [(25,6),(18,17),(29,19),(33,9)]:comp['solid'][y,x]=False
 comp['windmills']=[]
 for key,x,y in [('labwind',24,3),('wind',19,14),('wind',30,16),('upper_wind',32,6)]:
  c=a[key];assert (comp['cells'][y:y+4,x:x+2]==ground.GRASS).all(),('windmill on path',x,y)
  comp['canvas'].blit(c,x*16,y*16);comp['solid'][y+3,x+1]=True
  comp['windmills'].append(dict(x=x,y=y,base=[x+1,y+3]))
 for name,x,y,dx in old.BUILDINGS:
  c=a[name];style='gable' if name in ('annex','staff_b') else 'house'
  wall=(0,2,11,7) if name=='institute' else WALL[style]
  building_geometry(comp,name,c,x,y,wall,(x+dx,y+c.h//16-1))
 # Scatter a few exact pink counterparts, retaining every source trunk.
 mc=comp['canvas'];tree=a['tree'];chosen=0
 for y in range(0,comp['H']-2,3):
  for x in range(0,comp['W']-1,2):
   if (x,y) not in {(2,6),(2,24),(30,0),(28,45),(32,21)}:continue
   sl=np.s_[y*16:y*16+48,x*16:x*16+32];m=tree.px>0
   if np.array_equal(mc.idx[sl][m],tree.px[m]) and (mc.bank[sl][m]==3).all():mc.bank[sl][m]=10;chosen+=1
 return comp

def route31(a):
 p=old.layout('route31')
 # HGSS: the cave forecourt ends against woods immediately east of the arch.
 p[12:18,55:]='T'
 p[7:28,34]='.'
 p[18,10:12]='.'
 p[28:30,35:]='#';p[28:30,37:40]='='
 # Keep the west approach against the woods instead of an extra northern lawn.
 p[11:13,8:20]='T'
 p[12,8:20]='.'
 # HGSS's upper terrace is inaccessible; its visible rock is the boundary.
 # Render no inherited cliff, cave or wall stamps, then place the exact sources.
 aa=dict(a,cliff=Canvas(304,224,a['landform'].pal),bridge=Canvas(48,64,a['bridge'].pal))
 comp=old.compose('route31',p,aa);mc=comp['canvas']
 mc.blit(a['landform'],44*16,0)
 for y in list(range(7,15,2))+list(range(18,28,2)):mc.blit(a['route31_wall'],33*16,y*16)
 mc.blit(a['bridge'],528,240)
 # The southern rock rim and stair flight continue into Route 30's north rim.
 for y in (28,29):
  for x in range(35,63):
   if 37<=x<40:continue
   mc.blit(a['top'+str(y-28)],x*16,y*16);comp['solid'][y,x]=True
 mc.blit(a['stairs_top'],37*16,28*16)
 comp['cells'][28:30,37:40]=ground.PATH;comp['solid'][28:30,37:40]=False
 # Redraw the independent sign after the rock rather than burying it.
 mc.blit(a['sign'],51*16,12*16)
 # Every visible rock cell is solid except the bridge and real cave opening.
 # This also closes the unimplemented plateau/outer-map access.
 for c,px,py in [(a['landform'],704,0)]:
  for y in range(py//16,min(comp['H'],(py+c.h+15)//16)):
   for x in range(px//16,min(comp['W'],(px+c.w+15)//16)):
    y0=max(0,y*16-py);x0=max(0,x*16-px)
    if (c.px[y0:min(c.h,(y+1)*16-py),x0:min(c.w,(x+1)*16-px)]>0).sum()>=48:comp['solid'][y,x]=True
 comp['solid'][:12,44:]=True
 comp['cells'][7:28,33:35]=ground.GRASS;comp['behavior'][7:28,33:35]=0
 comp['solid'][7:28,33:35]=False;comp['solid'][7:28,33]=True;comp['solid'][15:18,33:35]=False
 comp['solid'][13,52]=False;comp['behavior'][13,52]=97
 # Cave threshold and apron connect directly to the existing path, as in HGSS.
 comp['cells'][13:16,51:54]=ground.PATH
 comp['plan']=p
 return comp

def all_comps():
 a,pals,labpal=assets();result={}
 for n in (29,30):result[f'route{n}']=(route_comp(n,a),dict(pals))
 nb=new_bark(a);npals=dict(pals);npals[8]=labpal;result['new_bark']=(nb,npals)
 aa=dict(a,cliff=a['landform']);aa['gate']=Canvas(128,96,a['gable'].pal);aa['gate'].px[16:96,32:112]=a['gable'].px
 comp=route31(aa)
 comp['solid'][10:16,:8]=False
 building_geometry(comp,'violet-gate',a['gable'],2,11,WALL['gable'],(4,15))
 result['route31']=(comp,dict(pals))
 # Small Violet arrival remains bounded to the already authored gate approach.
 from johto_connections import build as b
 p=b.L.violet_entrance();p[p=='V']='P';va,vp=b.assets('violet_entrance',a,pals)
 va['house']=a['house'];va['tree']=a['tree'];va['gate']=a['gate'];vp.update(pals)
 result['violet_entrance']=(b.compose('violet_entrance',p,va,forest_builder=oldart.forest),vp)
 return result

def ground_pixels(comp,pals):
 cells=comp['cells'];h,w=cells.shape;gy,gx=np.indices((h*16,w*16));m=np.repeat(np.repeat(cells,16,0),16,1)
 from PIL import ImageFilter
 water=np.array(Image.fromarray((m==ground.SEA).astype('uint8')*255).filter(ImageFilter.MedianFilter(9)).filter(ImageFilter.GaussianBlur(3)))>=128
 path=m==ground.PATH;grass=~water&~path
 textures=refine.ground_sources(ROOT,pals[0].gba(),pals[1].gba())
 nb=np.zeros_like(m,dtype=np.int8);ni=np.zeros_like(m,dtype=np.uint8)
 # Every route uses dirt, and the approved rounded pond bank. Offset only
 # the reference's town-specific shoreline split, not texture phase.
 refine.terrain(ni,nb,grass,path,water,gx+640,gy,textures)
 sea=np.array(Image.open(APP/'references/B/sea-frame-0.png').convert('RGB'),int);pp=np.array(pals[1].gba()[1:],int)
 si=((sea[...,None,:]-pp)**2).sum(-1).argmin(-1)+1
 nb[water]=1;ni[water]=si[gy[water]%32,gx[water]%32]
 return nb,ni,water,textures
