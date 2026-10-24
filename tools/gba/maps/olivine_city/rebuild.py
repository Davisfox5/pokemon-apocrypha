"""Guarded complete asset reconstruction of the rejected Olivine exterior.
Uses independently drawn terrain/modules and new isolated building masters.
Does not read the HGSS overview pixels or replay the first-authoring generator.
Preserves existing map IDs, section geometry and collision/elevation bits.
"""
from pathlib import Path
import sys,json,hashlib,subprocess,struct,io
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[4];G=Path(sys.argv[1]);S=R/'gba/art/olivine-city/source';A=S/'rebuilt';M=A/'masters';D=A/'modules';E=S.parent/'evidence';O=E/'rebuild';O.mkdir(exist_ok=True)
BASE='c996146b286add8b16f434346a4eed376e6c2b6e'
assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()==BASE,'Use the named rejected baseline in an isolated worktree; never replay onto later work.'
assert not subprocess.check_output(['git','-C',str(G),'diff','--name-only','HEAD'],text=True).strip(),'Preserve native edits'
sys.path.insert(0,str(R/'tools/gba/maps'));from tiles import Tileset
HUB_BASE='8fb82f736003228dc10db49d0a071fca0589842e'
def baseline(name):return subprocess.check_output(['git','-C',str(R),'show',HUB_BASE+':gba/art/olivine-city/source/'+name])
sections=json.loads((E/'sections.json').read_text());solid=np.load(io.BytesIO(baseline('solid.npy')));W,H=65,54
# The new centered entrance needs the sign one metatile farther east. Keep its
# approach open and move only the sign's actual ground footprint.
solid[33,47]=False;solid[33,48]=True
solid[25:28,29]=False;solid[27,28]=True
solid[20:25,29]=True;solid[19:21,38:40]=True
# HGSS railing has a real festival-gate gap at x184..240. The original
# broad collision trace incorrectly allowed walking through its other runs.
for x0,x1 in [(6,12),(15,17),(21,28)]:solid[20,x0:x1]=True
bg=Image.new('RGBA',(1040,864));fg=Image.new('RGBA',bg.size);bg_bank=np.zeros((864,1040),np.uint8);fg_bank=np.zeros_like(bg_bank);mat=np.full((H,W),'water',dtype='<U32');above=np.zeros((H,W),bool)
# Existing native palette slots for immutable Center, Mart and tree masters.
oldpals=json.loads(baseline('palettes.json'));pals=[None]*13
curated={0:['#247ab0','#328db8','#398fba','#4dacc4','#81c8d1','#b8e0d9','#e0eee0','#196a99','#3c98b5','#66b5c7','#aad6d3','#e8edd1','#1b5e88','#297ca4','#94ced1'],1:['#a8c7c5','#b1cecb','#91b2b2','#bdd6d1','#557c79','#d2e0d4','#e8eee0','#648f8c','#8caaa4','#eef3e1','#b9c6b5','#e3e8d3','#7b9590','#f6f4df','#496c70'],2:['#a78356','#70573e','#cfb77f','#937348','#87663e','#bd9b67','#b79a65','#d9c28d','#f0dba4','#7d6544','#78c8a0','#e8d49b','#dfc891','#efdfb1','#609c7e'],3:['#78c8a0','#80cda5','#87d1a9','#5fae8b','#a2d6ab','#4c9b7e','#c0dfb6','#6dbf98','#91cfac','#3e856e','#b1dbad','#79bd99','#6db18c','#9fd4ab','#458c74'],7:['#cabf9c','#998c73','#e1d6b7','#b9aa89','#ab9a7a','#5b7774','#e0e0bf','#687d75','#a8bbb0','#697c70','#475f5d','#273e43','#d4d5b5','#859e91','#777866']}
for bank,cs in curated.items():pals[bank]=np.array([tuple(bytes.fromhex(c[1:])) for c in cs],np.uint8)&248
for bank in [8,9,10,11]:pals[bank]=np.array(oldpals[bank],np.uint8)
# Four unused foliage entries carry the lawn beneath mixed tree/roof quadrants.
# Canonical tree colors/indices remain exact; no additional palette bank is used.
assert not np.array(pals[8][11:]).any()
pals[8][11:]=np.array([pals[3][0],pals[3][1],pals[3][2],pals[3][5]])
for bank,names in [(4,['gym']),(5,['house']),(6,['lighthouse','terminal','sailboat']),(12,['cafe'])]:
 pixels=[]
 for name in names:
  a=np.array(Image.open(M/(name+'.png')).convert('RGBA'));pixels.append(a[a[...,3]>0,:3])
 pix=np.concatenate(pixels);im=Image.fromarray(pix.reshape(-1,1,3)).quantize(colors=15,method=Image.Quantize.MEDIANCUT);pals[bank]=np.array(im.getpalette()[:45],np.uint8).reshape(15,3)&248
# Protect semantic accent ramps rather than allowing roof area frequency to
# remove the blue glass, wood trim or cream plaster from small buildings.
pals[5]=np.array([[8,72,40],[8,104,48],[16,136,56],[48,160,64],[104,184,104],[64,40,24],[120,80,40],[176,136,72],[224,208,168],[184,168,128],[16,72,128],[40,128,192],[128,208,232],[16,24,24],[80,168,80]],np.uint8)
pals[12]=np.array([[48,24,24],[88,24,32],[120,32,40],[160,48,56],[200,80,72],[64,40,24],[112,72,32],[168,120,48],[224,176,72],[248,216,112],[216,200,160],[144,128,96],[16,56,88],[32,112,176],[112,184,216]],np.uint8)
# Fit once per master/material family, retaining the alpha silhouette. No local
# best-bank dithering on a roof, facade or shared asset.
def fit(im,bank):
 a=np.array(im.convert('RGBA'));p=pals[bank];rgb=a[...,:3];dist=((rgb.astype(np.int32)[:,:,None,:]-p[None,None].astype(np.int32))**2).sum(3);a[...,:3]=p[dist.argmin(2)];return Image.fromarray(a)
modules={};modulebanks={'water':0,'paving':1,'lawn':3,'sand':2,'dock':7,'cliff-face':2,'cliff-cap':2,'curb':1,'fence':1,'lamp':12,'sign':7,'parasol-table':6,'stairs':2,'ramp':7,'shore-rock':1}
for name,bank in modulebanks.items():modules[name]=fit(Image.open(D/(name+'.png')),bank)
def shape_mask(poly):
 a=Image.new('L',bg.size);ImageDraw.Draw(a).polygon(poly,fill=255);return a
def surface(name,poly,label=None):
 bank=modulebanks[name];mask=shape_mask(poly);mod=modules[name];fill=Image.new('RGBA',bg.size)
 for y in range(0,864,mod.height):
  for x in range(0,1040,mod.width):fill.paste(mod,(x,y))
 bg.paste(fill,(0,0),mask);ma=np.array(mask)>0;bg_bank[ma]=bank
 for y,x in np.ndindex(H,W):
  if ma[y*16+8,x*16+8]:mat[y,x]=label or name
 return mask
def rect(name,box,label=None):
 x,y,x1,y1=box;return surface(name,[(x,y),(x1-1,y),(x1-1,y1-1),(x,y1-1)],label)
def prop(name,x,y,bank=None,upper=True):
 im=modules[name] if name in modules else Image.open(S/'masters'/(name+'.png')).convert('RGBA') if name in ['center','mart','tree'] else fit(Image.open(M/(name+'.png')),bank)
 if bank==8 or name in ['center','mart','tree']:im=Image.open(S/'masters'/(name+'.png')).convert('RGBA');a=np.array(im);a[...,:3]&=248;im=Image.fromarray(a)
 bank=modulebanks.get(name,bank);mask=np.array(im.getchannel('A'))>0;w,h=im.size;assert x>=0 and y>=0 and x+w<=1040 and y+h<=864,(name,x,y)
 if name in ['gym','house','cafe','lighthouse','terminal']:
  # Hardware has one foreground palette per 8px quadrant. Move neighboring
  # canopy pixels underneath the new roof into the background only in mixed
  # quadrants, preserving the exact canonical tree colors and grass beneath.
  am=np.zeros((864,1040),bool);am[y:y+h,x:x+w]=mask
  for gy in range(y//8,(y+h+7)//8):
   for gx in range(x//8,(x+w+7)//8):
    yy,xx=gy*8,gx*8;box=(xx,yy,xx+8,yy+8);fa=np.array(fg.crop(box));tm=(fg_bank[yy:yy+8,xx:xx+8]==8)&(fa[...,3]>0)
    if tm.any() and am[yy:yy+8,xx:xx+8].any():
     ba=np.array(bg.crop(box));ba[tm]=fa[tm];bg.paste(Image.fromarray(ba),(xx,yy));bg_bank[yy:yy+8,xx:xx+8]=8;fa[tm]=0;fg.paste(Image.fromarray(fa),(xx,yy))
 fg.paste(im,(x,y),im.getchannel('A'));f=fg_bank[y:y+h,x:x+w];f[mask]=bank if bank is not None else 0
 if upper:above[y//16:(y+h+15)//16,x//16:(x+w+15)//16]=True
 return im
rect('water',(0,0,1040,864))
# Measured outer coastline, stepped at the actual bay/peninsula shoulders.
land=[(0,0),(1040,0),(1040,304),(936,304),(936,352),(904,352),(904,400),(880,400),(880,640),(632,640),(632,544),(104,544),(104,640),(64,640),(24,624),(24,544),(0,544)]
surface('lawn',land,'lawn / forest floor')
# Main lower city paving and individual transparent-building lawns.
paving=[(328,0),(456,0),(456,448),(472,448),(472,400),(552,400),(552,480),(568,480),(568,336),(632,336),(632,544),(104,544),(104,176),(328,176)]
surface('paving',paving,'cut stone street')
rect('sand',(328,0,456,96),'Route39 sandy approach');rect('sand',(0,480,56,544),'Route40 sandy approach')
# Complete explicit cliff planes. Cap/face assembly is local; the horizontal
# cap is never smeared across a flat lawn. Sidewalls retain vertical depth.
cliffs=[('upper eastern forest ledge',(520,64,1040,80)),('northwest south',(88,144,328,176)),('northwest side',(288,0,328,176)),('west forest south',(0,432,104,480)),('north avenue east',(456,0,504,192)),('avenue side upper',(448,144,488,320)),('avenue side lower',(464,320,488,400)),('north houses back',(552,160,680,192)),('north houses east',(656,176,696,336)),('north houses south',(552,304,656,336)),('path east',(640,320,680,544)),('lighthouse west',(640,384,696,544)),('lighthouse south',(640,576,880,640)),('lighthouse east',(832,352,880,640)),('east upper coast',(824,224,1040,256)),('east coast middle',(880,256,944,352)),('east coast lower',(864,352,912,400)),('west harbor outcrop',(24,544,104,640))]
cliff_masks=[]
for label,box in cliffs:
 x,y,x1,y1=box;mask=rect('cliff-face',box,'rock front/side');cliff_masks.append((label,box));cap=modules['cliff-cap']
 for xx in range(x,x1,16):
  cw=min(16,x1-xx);bg.paste(cap.crop((0,0,cw,16)),(xx,y));bg_bank[y:y+16,xx:xx+cw]=2
# Flat terraces with an intact raised lip and distinct wall faces beneath.
rect('lawn',(488,192,656,304),'north house terrace');rect('lawn',(680,384,832,576),'lighthouse lawn')
# Source architecture sits on small lawn pads with complete stone curbs.
for box in [(136,200,352,256),(256,328,432,368),(136,448,232,496),(232,448,336,496),(456,448,552,496)]:
 rect('lawn',box,'building lawn pad');x,y,x1,y1=box
 for xx in range(x,x1,16):
  mod=modules['curb'];bg.paste(mod,(xx,y1-8),mod.getchannel('A'));m=np.array(mod.getchannel('A'))>0;patch=bg_bank[y1-8:y1+8,xx:xx+16];patch[m]=1
# Full-width descending path head, stair shoulders and joined promenade ramp.
prop('stairs',576,304,upper=False);mat[19:21,36:38]='terrace stairs'
rect('paving',(560,336,640,544),'lower terrace path')
# Wooden quays/piers constructed before their independent buildings and props.
for box in [(104,544,640,640),(352,640,448,864),(320,704,464,800),(280,736,432,832),(432,736,464,800)]:rect('dock',box,'timber promenade / pier')
# Visible pile/fascia under the actual promenade, not a tiled land screenshot.
d=ImageDraw.Draw(bg)
for x0,x1,y in [(104,352,640),(440,640,640),(280,352,832)]:
 d.rectangle((x0,y,x1-1,y+4),fill=tuple(map(int,pals[7][1]))+(255,));bg_bank[y:y+5,x0:x1]=7
 for x in range(x0+8,x1,32):d.rectangle((x,y+4,x+4,y+14),fill=tuple(map(int,pals[7][1]))+(255,));d.line((x,y+5,x,y+13),fill=tuple(map(int,pals[7][2]))+(255,));bg_bank[y+4:y+15,x:x+5]=7
# Rebuilt intertidal rock breakwater, one complete reusable faceted master.
rocks=[(88,640),(24,704),(56,704),(88,696),(120,704),(152,696),(184,704),(216,720),(248,720),(472,720),(504,704),(536,696),(568,696),(600,696),(632,696),(664,704),(696,704),(728,696),(760,688),(792,688),(824,688),(856,688),(888,680),(920,680),(952,672),(984,664),(1000,640),(1000,608),(984,576),(984,544),(968,512),(968,480),(952,448),(936,416),(936,384),(968,352),(904,376),(936,480),(920,504),(952,600),(968,632),(944,712),(728,736),(488,752),(152,736),(64,760),(0,816)]
for x,y in rocks:prop('shore-rock',x,y,upper=False)
# Complete native trees throughout every wooded region; no original conifers
# or screenshot color keys survive. Receiving ground is independently rebuilt.
trees=json.loads(baseline('trees.json'));extras=[(528,80),(560,80),(592,80),(624,80),(528,112),(560,112),(592,112),(624,112),(488,304),(520,304),(488,352),(824,224),(880,240),(832,288),(880,288),(848,432),(848,480)]
for x,y in extras:
 if solid[y//16+1:y//16+3,x//16:x//16+2].all():trees.append([x,y])
# Fill remaining old-forest footprints with whole trees only on blocked roots.
for x,y in [(680,336),(712,336),(744,336),(776,336)]:
 if solid[y//16+1:y//16+3,x//16:x//16+2].all():trees.append([x,y])
roots=np.zeros((H,W),np.uint8)
for x,y in trees:
 assert not roots[y//16+1:y//16+3,x//16:x//16+2].any(),'Distinct roots required'
 assert solid[y//16+1:y//16+3,x//16:x//16+2].all(),'Do not close an existing path with a tree'
 # A complete small grass cap beneath isolated trees is constructed separately.
 if [x,y] not in json.loads(baseline('trees.json')):rect('lawn',(x,y,x+32,y+48),'wooded cliff shoulder')
 prop('tree',x,y,8);roots[y//16+1:y//16+3,x//16:x//16+2]=1
# Rebuilt architecture: masters have no terrain attached. Their opaque lower
# facade is below the player; the precise transparent upper silhouette occludes.
placements=[('gym',184,148,4,224),('house',272,264,5,328),('house',496,184,5,248),('house',576,184,5,248),('cafe',144,400,12,448),('lighthouse',688,344,6,480),('terminal',320,688,6,776)]
for name,x,y,bank,facade in placements:
 im=prop(name,x,y,bank);above[facade//16:(y+im.height+15)//16,x//16:(x+im.width+15)//16]=False
 # Save exact converted native master for asset-first inspection/provenance.
 im.save(M/(name+'-native.png'))
for name,x,y,bank,facade in [('center',240,400,9,448),('mart',464,416,11,448)]:
 im=prop(name,x,y,bank);above[facade//16:(y+im.height+15)//16,x//16:(x+im.width+15)//16]=False
# Separate reconstructed harbor sailboats, outside the walkable quay.
for x,y in [(248,608),(464,608)]:
 boat=prop('sailboat',x,y,6);boat.save(M/'sailboat-native.png')
# Fences, flags, signs, parasols and ramp are rebuilt reusable native modules.
for x0,x1,y in [(104,184,176),(296,456,176),(104,184,312),(248,272,312),(344,448,312),(104,352,624),(440,632,624),(280,352,816)]:
 for x in range(x0,x1,16):prop('fence',x,y,upper=False)
# Pier side rails share the same picket material, with aligned corner posts.
rail=modules['fence'].rotate(90,expand=True)
for x,y0,y1 in [(280,736,816),(432,800,832)]:
 for y in range(y0,y1,16):
  fg.paste(rail,(x,y),rail.getchannel('A'));p=fg_bank[y:y+16,x:x+16];p[np.array(rail.getchannel('A'))>0]=1
for x,y in [(104,272),(232,272),(328,384),(448,384),(328,0),(448,0)]:prop('lamp',x,y)
# Cable pennants: simple clean shared geometry with a genuine transparent gap.
for x0,x1,y in [(120,240,288),(344,464,400),(344,456,24)]:
 cable=Image.new('RGBA',(x1-x0,16));cd=ImageDraw.Draw(cable);cd.line((0,0,x1-x0-1,0),fill=tuple(map(int,pals[7][10]))+(255,))
 for i,x in enumerate(range(4,x1-x0-8,18)):cd.polygon([(x,1),(x+10,1),(x+7,10),(x+3,10)],fill=tuple(map(int,pals[12][9 if i%2 else 13]))+(255,))
 # Fit this compact mixed trim to the harbor blue/cream family consistently.
 cable=fit(cable,12);fg.paste(cable,(x0,y),cable.getchannel('A'));p=fg_bank[y:y+16,x0:x1];p[np.array(cable.getchannel('A'))>0]=12;above[y//16,x0//16:(x1+15)//16]=True
for x,y in [(168,224),(392,344),(400,568),(768,520)]:prop('sign',x,y,upper=False)
for x,y in [(136,544),(248,544),(488,544)]:prop('parasol-table',x,y)
prop('ramp',632,536,upper=False)
# A thin water-side foam lip follows the reconstructed coastal silhouette;
# it is clipped to real water, never painted over cliff rock or timber decking.
from scipy.ndimage import binary_dilation
lm=np.array(shape_mask(land))>0;shore=binary_dilation(lm,iterations=2)&~lm&(bg_bank==0)
a=np.array(bg);a[shore,:3]=pals[0][5];bg=Image.fromarray(a)
# Material and occupancy arrays are independent. All open squares must still
# show a real receiving surface even under a transparent roof overhang.
# Former overview occlusions can otherwise leave water under an approach.
open_surface_findings=[]
for y,x in np.ndindex(H,W):
 if not solid[y,x] and mat[y,x] in ['water','rock front/side']:
  raise AssertionError(('Open cell needs measured ground, not inferred color',x,y))
# Exact canonical Center uses two palette banks; all other converted masters
# already use one coherent family. Encode only actual silhouettes above ground.
bga=np.array(bg);fga=np.array(fg);encoded={};nativebg=np.zeros((864,1040,3),np.uint8);nativefg=np.zeros((864,1040,4),np.uint8)
for gy,gx in np.ndindex(H*2,W*2):
 y,x=gy*8,gx*8;a=bga[y:y+8,x:x+8];bank=int(np.bincount(bg_bank[y:y+8,x:x+8].ravel(),minlength=13).argmax())
 # Boundary quadrants fit a single native material bank; structural foreground
 # remains separate, so this never paints a lawn over a neighboring building.
 best=None
 for b in ([8] if (bg_bank[y:y+8,x:x+8]==8).any() else [bank,0,1,2,3,7]):
  pal=pals[b];dist=((a[...,:3].astype(np.int32)[:,:,None,:]-pal.astype(np.int32)[None,None])**2).sum(3);ii=dist.argmin(2);err=np.take_along_axis(dist,ii[...,None],2).sum()
  if best is None or err<best[0]:best=(err,b,ii)
 _,bank,ii=best;lo=ii.astype(np.uint8)+1;nativebg[y:y+8,x:x+8]=pals[bank][ii]
 a=fga[y:y+8,x:x+8];m=a[...,3]>0;hi=np.zeros((8,8),np.uint8);fb=0
 if m.any():
  colors=set(map(tuple,a[m,:3]));candidate=[b for b,p in enumerate(pals) if colors<=set(map(tuple,p))]
  if candidate:fb=candidate[0]
  else:
   # Foreground modules overlapping within a quadrant use the family minimizing
   # their actual visible colors; never discard silhouette pixels.
   opts=np.unique(fg_bank[y:y+8,x:x+8][m]);fb=min(opts,key=lambda b:(((a[m,:3].astype(np.int32)[:,None]-pals[b].astype(np.int32)[None])**2).sum(2).min(1)).sum())
  dist=((a[...,:3].astype(np.int32)[:,:,None]-pals[fb].astype(np.int32)[None,None])**2).sum(3);hi[m]=dist.argmin(2)[m]+1;nativefg[y:y+8,x:x+8,:3]=pals[fb][np.maximum(hi,1)-1];nativefg[y:y+8,x:x+8,3]=m*255
 encoded[(gy,gx)]=[(lo,bank),(hi,int(fb))]
# Guarded native repack, retaining the original section IDs and choosing the
# existing metatile number for each distinct edited cell whenever compatible.
plans=[];stats=[]
for sec in sections:
 n=sec['name'];x0,y0,x1,y1=sec['box'];old=np.fromfile(G/f'data/layouts/{n}/map.bin','<u2').reshape(y1-y0,x1-x0);oldts=Tileset(G,n.lower(),n.lower());glyphs=[np.zeros((8,8),np.uint8)];lookup={glyphs[0].tobytes():0};used={};assigned={};blocks={};attrs={};grid=old.copy()
 def entry(a,b):
  k=a.tobytes()
  if k not in lookup:
   t=len(glyphs);glyphs.append(a)
   for h in range(2):
    for v in range(2):lookup.setdefault(a[::-1 if v else 1,::-1 if h else 1].tobytes(),t|h<<10|v<<11)
  return lookup[k]|b<<12
 for cy,cx in np.ndindex(old.shape):
  y,x=cy+y0,cx+x0;es=[]
  for layer in range(2):
   for q in range(4):es.append(entry(*encoded[y*2+q//2,x*2+q%2][layer]))
  attr=0 if above[y,x] else 0x1000;key=tuple(es)+(attr,);preferred=int(old[cy,cx]&1023)
  if key in assigned:mid=assigned[key]
  else:
   mid=preferred if preferred not in blocks else next(i for i in range(1024) if i not in blocks)
   blocks[mid]=es;attrs[mid]=attr;assigned[key]=mid
  grid[cy,cx]=(int(old[cy,cx])&~1023)|mid
 expected=old.copy()
 for cy,cx in np.ndindex(grid.shape):
  wy,wx=cy+y0,cx+x0;grid[cy,cx]=(int(grid[cy,cx])&~0xc00)|(0xc00 if solid[wy,wx] else 0)
  if (wx,wy) not in [(47,33),(48,33),(29,25),(29,26),(29,27),(28,27)]+[(29,yy) for yy in range(20,25)]+[(xx,yy) for xx in [38,39] for yy in [19,20]]+[(xx,20) for xx in list(range(6,12))+[15,16]+list(range(21,28))]:assert int(grid[cy,cx]&0xfc00)==int(old[cy,cx]&0xfc00),'Preserve all other collision/elevation bits'
 assert len(glyphs)<=1008,(n,len(glyphs))
 count=max(blocks)+1;bb=[blocks.get(i,[0]*8) for i in range(count)];aa=[attrs.get(i,0x1000) for i in range(count)];plans.append((sec,glyphs,bb,aa,grid));stats.append(dict(map=n,glyphs=len(glyphs),metatile_slots=count,stable_map_ID=True,elevation_exact_collision_repairs_documented=True))
# Every section passes before the first native mutation.
for sec,glyphs,blocks,attrs,grid in plans:
 n=sec['name']
 for part in range(2):
  p=G/f'data/tilesets/{"secondary" if part else "primary"}/{n.lower()}';start=512*part;count=max(1,len(glyphs)-512) if part else 512
  im=Image.new('P',(128,((count+15)//16)*8));im.putpalette([c for i in range(256) for c in (i*17%256,)*3])
  for i in range(count):
   if start+i<len(glyphs):im.paste(Image.fromarray(glyphs[start+i]).convert('P'),(i%16*8,i//16*8))
  im.save(p/'tiles.png',bits=4);bb=blocks[start:start+512] or [[0]*8];aa=attrs[start:start+512] or [0x1000];(p/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*b) for b in bb));(p/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(aa),*aa))
  for b in range(16):
   pal=np.vstack([np.zeros((1,3),np.uint8),pals[b]]) if b<13 else np.zeros((16,3),np.uint8);(p/'palettes'/f'{b:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pal)+'\n')
 grid.tofile(G/f'data/layouts/{n}/map.bin');np.full((2,2),int(grid[0,0])|0xc00,'<u2').tofile(G/f'data/layouts/{n}/border.bin')
Image.fromarray(nativebg).save(S/'native-ground.png');Image.fromarray(nativefg).save(S/'shared-foreground.png');Image.fromarray(np.array(bg)).save(A/'assembled-ground.png');Image.fromarray(np.array(fg)).save(A/'assembled-foreground.png');np.save(S/'solid.npy',solid);np.save(S/'material.npy',mat);np.save(S/'above.npy',above);np.save(S/'tree-roots.npy',roots);(S/'trees.json').write_text(json.dumps(trees)+'\n');(S/'palettes.json').write_text(json.dumps([p.tolist() for p in pals])+'\n')
comp=nativebg.copy();mask=nativefg[...,3]>0;comp[mask]=nativefg[mask,:3];Image.fromarray(comp).save(E/'native-map.png');Image.fromarray(comp).save(O/'after.png')
features=json.loads(baseline('features.json'))
for f in features:
 if f['name']=='Olivine Gym':f['native_box']=[184,148,296,244]
 if f['name']=='West residence':f['native_box']=[272,264,344,352]
 if f['name']=='Port terminal':f['native_box']=[320,688,472,800]
(S/'features.json').write_text(json.dumps(features,indent=2)+'\n')
baseline_solid=np.load(io.BytesIO(baseline('solid.npy')));changes=[dict(cell=[int(x),int(y)],before_solid=bool(baseline_solid[y,x]),after_solid=bool(solid[y,x])) for y,x in np.argwhere(baseline_solid!=solid)]
(O/'collision-adaptations.json').write_text(json.dumps(dict(baseline=BASE,changes=changes,reason='Visible source railings, the actual festival gate, cliff faces, two-cell stair, and moved prop bases.'),indent=2)+'\n')
(A/'placements.json').write_text(json.dumps(dict(buildings=placements,trees=trees,rocks=rocks,cliff_planes=cliff_masks,coastline=land,main_paving=paving,all_source_surfaces_rebuilt=True,original_overview_raster_used=False),indent=2)+'\n')
(O/'native-edit.json').write_text(json.dumps(dict(baseline=BASE,sections=stats,elevation_exact_collision_repairs_documented=True,prop_footprint_moves=[[47,33,False],[48,33,True],[29,25,False],[29,26,False],[29,27,False],[28,27,True]],map_IDs_unchanged=True,all_terrain_reconstructed=True,original_overview_pixels_read=False,terrain_edge_adaptations=['House-terrace east lip moved8px to complete native lawn cell40.','Lower path and quay east edges completed to x640 from x632.','Upper stair at576,304 is two32px-deep native columns; adjacent old bypass closed.','Avenue wall steps from x448 to464 at y320, matching whole road cells.'],cliff_collision_corrections=[[29,yy] for yy in range(20,25)]+[[xx,yy] for xx in [38,39] for yy in [19,20]],tree_count=len(trees),native_palette_banks=13),indent=2)+'\n');print(stats)
