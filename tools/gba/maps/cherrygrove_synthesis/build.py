"""Native B/C/E synthesis over a preserved owner-authored E snapshot."""
from pathlib import Path
import sys,json,struct,hashlib,shutil,re
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from tiles import Tileset,palette
from claude_cherrygrove import build as cb,banks
ROOT=HERE.parents[3];A=ROOT/'gba/art/cherrygrove-synthesis';G=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'tools/vendor/gba/cherrygrove-synthesis-work';S=A/'references/E';EV=A/'evidence';EV.mkdir(exist_ok=True)
# All regeneration reads the immutable tracked snapshot, never edited engine output.
t=Tileset(S,'cherrygrove','cherrygrove')
layouts=json.loads((S/'data/layouts/layouts.json').read_text())['layouts']
layouts=[l for l in layouts if l['name'] in ['CherrygroveCity_Layout','CherrygroveRoute29Approach_Layout','CherrygroveRoute30Approach_Layout']]
pals={};assets={}
for name,bank in [('house',6),('gable',6),('house2',7),('center',8),('mart',9),('mart_sign',9),('tree',3),('blossom',10),('cliff',2)]:
 src=A/'references'/('C' if name=='cliff' else 'B')/(name+'.idx.png');im=Image.open(src);assets[name]=np.array(im,dtype=np.uint8);colors=np.array(im.getpalette()[:48]).reshape(16,3);pals[bank]=[tuple(map(int,c)) for c in colors]
from refine import repair_assets,terrain,ground_sources
repair_assets(ROOT,assets,pals)
# C palette, B sea, E harbor's exact wood and boat color slots.
pals[0]=palette(A/'references/C/palettes/bank00-ground.pal');pals[1]=palette(A/'references/B/palettes/bank01-sea.pal')
textures=ground_sources(ROOT,pals[0],pals[1])
pals[5]=t.pals[1][7];pals[11]=t.pals[1][10];pals[12]=t.pals[1][11]
sea=[np.array(Image.open(A/f'references/B/sea-frame-{k}.png').convert('RGB')) for k in range(8)];seaidx=[]
for im in sea:
 pp=np.array(pals[1][1:],dtype=int);seaidx.append((((im.astype(int)[...,None,:]-pp)**2).sum(-1).argmin(-1)+1).astype(np.uint8))
grassrgb=np.array([115,156,115]);grasscolors={(115,156,115),(148,181,132),(173,206,148)}
groundpal=np.array(pals[0][1:],dtype=int)
def nearest(cs,pal):
 a=np.asarray(cs,dtype=int);p=np.array(pal[1:],dtype=int);return (((a[...,None,:]-p)**2).sum(-1).argmin(-1)+1).astype(np.uint8)
def render_arrays(grid,w):
 h=len(grid)//w;rgb=np.zeros((h*16,w*16,3),np.uint8);bk=np.zeros((h*16,w*16),np.int8);ix=np.zeros_like(bk,dtype=np.uint8)
 for i,v in enumerate(grid):
  mid=v&1023;es=t.blocks[int(mid>=512)][mid%512];x=i%w*16;y=i//w*16
  for lay in range(2):
   for q in range(4):
    e=es[lay*4+q];tid=e&1023;b=e>>12;tile=np.array(t.tiles[tid>=512][tid%512],np.uint8).reshape(8,8)
    if e&1024:tile=tile[:,::-1]
    if e&2048:tile=tile[::-1]
    xx=x+q%2*8;yy=y+q//2*8;m=tile!=0
    rgb[yy:yy+8,xx:xx+8][m]=np.array(t.pals[b>=6][b])[tile[m]];bk[yy:yy+8,xx:xx+8][m]=b;ix[yy:yy+8,xx:xx+8][m]=tile[m]
 return rgb,bk,ix
oldtree=np.array(Image.open(ROOT/'gba/art/johto-restart/native/tree.png').convert('RGBA'));maps=[];misc=[]
for l in layouts:
 name=l['name'].removesuffix('_Layout');w,h=l['width'],l['height'];data=(S/f'data/layouts/{name}/map.bin').read_bytes();grid=np.array(struct.unpack('<'+'H'*(w*h),data),np.uint16).reshape(h,w);rgb,bk,ix=render_arrays(grid.ravel(),w)
 treemask=(bk==6)&(ix<12)&(ix>0);positions=[]
 for y in range(-32,h*16,16):
  for x in range(-16,w*16,16):
   x0=max(x,0);y0=max(y,0);x1=min(x+32,w*16);y1=min(y+32,h*16)
   if y1<=y0 or x1<=x0:continue
   ref=oldtree[y0-y:y1-y,x0-x:x1-x];mask=ref[...,3]>0
   if mask.sum()<20:continue
   score=(np.abs(rgb[y0:y1,x0:x1].astype(int)-ref[...,:3]).max(-1)[mask]<3).mean()
   if score>.88:positions.append((x,y))
 erase=treemask.copy();buildings=[]
 if name=='CherrygroveCity':
  spec=[('PlayerHouse','house_mirror',43,17),('GoldHouse','gable',54,19),('NeighborHouse','house2',64,24),('Mart','mart',51,9),('PokemonCenter','center',61,9),('HarborHouse','house2',52,31),('GardenHouse','gable',65,31)]
  for label,style,dx,dy in spec:
   # E footprints, exact latest owner placements.
   ox,oy=dx-2,dy-4;erase[oy*16:(dy+1)*16,ox*16:(ox+(6 if style=='mart' else 5))*16]=True
   hh,ww=assets[style].shape;col={'house':1,'house_mirror':3,'house2':1,'gable':2,'mart':1,'center':3}[style];x=dx-col;y=dy-hh//16+1
   if label=='NeighborHouse':erase[y*16:(dy+1)*16,x*16:x*16+ww]=True
   buildings.append(dict(name=label,style=style,x=x,y=y,door=[dx,dy],width=ww//16,height=hh//16,old=[ox,oy,6 if style=='mart' else 5,5]))
  # E cliff is a three-cell face; C's middle rock courses fit between the same crest and toe.
  erase[7*16:10*16,:40*16]=True
 # Normalize ground and erase replaced art. All other harbor silhouettes remain E pixels.
 isgrass=np.zeros_like(erase)
 for c in grasscolors:isgrass|=(rgb==c).all(-1)
 isgrass|=erase
 water=(bk==4)&(ix>=7)&(ix<=14)&~erase
 ground=(bk==5)&(ix>=11)&(ix<=14)&~erase
 nb=np.full_like(bk,4);ni=np.zeros_like(ix);nb[isgrass|ground]=0
 gy,gx=np.indices(isgrass.shape)
 nb[water]=1;ni[water]=seaidx[0][gy[water]%32,gx[water]%32]
 foam=terrain(ni,nb,isgrass,ground,water,gx,gy,textures)
 ni[water]=seaidx[0][gy[water]%32,gx[water]%32]
 for old,new in [(7,5),(10,11),(11,12)]:
  m=(bk==old)&~(isgrass|ground|water|foam);nb[m]=new;ni[m]=ix[m]
 rem=nb==4;misc.append(rgb[rem]);maps.append(dict(name=name,w=w,h=h,grid=grid,rgb=rgb,bank=nb,idx=ni,water=water,positions=positions,buildings=buildings,oldbank=bk))
# Remaining native fences/flowers/signs/reef share one measured palette. No blanket scene quantization.
b=banks.Bank(4,'PROPS','primary');allmisc=np.concatenate(misc);b.add('props',np.concatenate([allmisc,np.full((len(allmisc),1),255,np.uint8)],axis=1).reshape(1,-1,4));b.build();pals[4]=b.palette.gba()
for m in maps:
 mask=m['bank']==4;m['idx'][mask]=nearest(m['rgb'][mask],pals[4])
 def stamp(arr,bank,x,y):
  hh,ww=arr.shape;x0=max(0,x);y0=max(0,y);x1=min(m['w']*16,x+ww);y1=min(m['h']*16,y+hh)
  if x1<=x0 or y1<=y0:return
  a=arr[y0-y:y1-y,x0-x:x1-x];mask=a!=0;m['bank'][y0:y1,x0:x1][mask]=bank;m['idx'][y0:y1,x0:x1][mask]=a[mask];m['water'][y0:y1,x0:x1][mask]=False
 added=[]
 if m['name']=='CherrygroveCity':
  # One coherent southeast grove, on a 32px lattice, joins the southern row.
  m['positions']=[(x,y) for x,y in m['positions'] if not (x>=68*16 and 20*16<=y<33*16)]
  added=[(x*16,y*16) for y in range(20,31,2) for x in range(68,80,2)]
  added += [(x*16,y*16) for x,y in [(47,5),(56,5),(45,14),(48,26),(56,26)]]
  m['positions']+=added
 m['tree_footprints']=[]
 pinktrees={(39,27),(43,27),(39,3),(48,0),(62,0),(74,6),(76,12),(74,22),(78,28),(59,33),(73,33),(47,5),(45,14),(56,26)}
 for x,y in m['positions']:
  pink=m['name']=='CherrygroveCity' and (x//16,y//16) in pinktrees
  ar=assets['blossom' if pink else 'tree'];stamp(ar,10 if pink else 3,x,y)
  if (x,y) in added:
   cx,cy=x//16,y//16;m['tree_footprints'].append([cx,cy,2,3])
   for yy in range(3):
    for xx in range(2):
     if np.count_nonzero(ar[yy*16:yy*16+16,xx*16:xx*16+16])>12:m['grid'][cy+yy,cx+xx]=(m['grid'][cy+yy,cx+xx]&1023)|0x3c00
 if m['name']=='CherrygroveCity':
  cliff=assets['cliff'];cliff=cliff[:48].copy();cliff[-2:]=nearest(np.array([104,72,56]),pals[2])
  # The final two columns taper into E's established landward edge.
  for x in range(0,40,2):
   v=cliff.copy()
   if x==38:
    for y in range(48):v[y,max(0,32-max(0,y-8)//2):]=0
   stamp(v,2,x*16,7*16)
  for d in m['buildings']:
   ar=assets[d['style']];bank={'house':6,'house_mirror':6,'gable':6,'house2':7,'mart':9,'center':8}[d['style']];stamp(ar,bank,d['x']*16,d['y']*16)
   ox,oy,ow,oh=d['old'];g=m['grid'];g[oy:oy+oh,ox:ox+ow]=(g[oy:oy+oh,ox:ox+ow]&1023)|0x3000
   # Every visibly occupied facade cell is solid, except the original door anchor.
   for yy in range(ar.shape[0]//16):
    for xx in range(ar.shape[1]//16):
     if (ar[yy*16:yy*16+16,xx*16:xx*16+16]!=0).sum()>12:g[d['y']+yy,d['x']+xx]=(g[d['y']+yy,d['x']+xx]&1023)|0x3c00
   dx,dy=d['door'];g[dy,dx]&=1023
   if d['style']=='mart':
    sign=assets['mart_sign'];sx=d['x']+4;sy=d['y']+1;stamp(sign,9,sx*16,sy*16)
    for yy in range(sign.shape[0]//16):
     for xx in range(sign.shape[1]//16):
      if np.count_nonzero(sign[yy*16:yy*16+16,xx*16:xx*16+16])>12:g[sy+yy,sx+xx]=(g[sy+yy,sx+xx]&1023)|0x3c00
 # Building footprint clearing must not reopen a newly planted tree beside it.
 # Test final visible pixels, so a hidden canopy under a facade adds no barrier.
 for cx,cy,tw,th in m['tree_footprints']:
  for yy in range(cy,cy+th):
   for xx in range(cx,cx+tw):
    bk=m['bank'][yy*16:(yy+1)*16,xx*16:(xx+1)*16]
    if np.count_nonzero((bk==3)|(bk==10))>12:
     m['grid'][yy,xx]=(m['grid'][yy,xx]&1023)|0x3c00
 # Store editable source and render before packing.
 rgb=np.zeros((*m['idx'].shape,3),np.uint8)
 for bank in range(13):
  mask=m['bank']==bank;rgb[mask]=np.array(pals[bank],np.uint8)[m['idx'][mask]]
 m['expected']=rgb;Image.fromarray(rgb).save(EV/(m['name']+'-authored.png'))
# Reuse HGSS edge modules on the native 8px grid. Match their 2px material
# silhouettes; permit only one-pixel contour corrections when choosing the
# shared module. Entire grass/path texture blocks remain the literal crops.
edge_modules={};edge_reuse=[]
classes=np.array([0,1,1,1,1,2,2,2,2,2,3,3,3,3,1,3])
for m in maps:
 for y in range(0,m['h']*16,8):
  for x in range(0,m['w']*16,8):
   bk=m['bank'][y:y+8,x:x+8];ar=m['idx'][y:y+8,x:x+8]
   if not (bk==0).all():continue
   shape=classes[ar];families=set(shape.ravel())
   if not (1 in families and families&{2,3}):continue
   small=np.rint(shape.reshape(4,2,4,2).mean(axis=(1,3))).astype('uint8');key=small.tobytes()
   choices=edge_modules.setdefault(key,[]);replacement=None
   for prior in choices:
    other=classes[prior];different=shape!=other
    if np.count_nonzero(different)>10:continue
    pad=np.pad(shape,1,mode='edge');near=np.stack([pad[dy:dy+8,dx:dx+8] for dy,dx in [(0,1),(2,1),(1,0),(1,2),(1,1)]])
    if ((near==other).any(axis=0)).all():replacement=prior;break
   if replacement is None:choices.append(ar.copy())
   elif not np.array_equal(ar,replacement):
    edge_reuse.append(dict(map=m['name'],x=x,y=y,pixels=int(np.count_nonzero(ar!=replacement)),contour_pixels=int(np.count_nonzero(shape!=classes[replacement]))))
    ar[:]=replacement;m['expected'][y:y+8,x:x+8]=np.array(pals[0],np.uint8)[ar]
# Complete authored ground tiles can also serve behind foreground objects.
# Search these before creating silhouette-specific background copies.
ground_candidates=[]
for m in maps:
 for y in range(0,m['h']*16,8):
  for x in range(0,m['w']*16,8):
   if (m['bank'][y:y+8,x:x+8]==0).all():ground_candidates.append(m['idx'][y:y+8,x:x+8].copy())
ground_candidates=np.unique(np.stack(ground_candidates),axis=0)
print('composition',[(m['name'],len(m['positions'])) for m in maps])
# Two GBA layers, exact palette factoring; global tile dedupe allows either bank in either tile pool.
tiles=[np.zeros((8,8),np.uint8)];lookup={tiles[0].tobytes():0};animations={};blocks=[];attrs=[];bl={};tilebanks={0:0}
def tile(arr,bank,watermask=None,pos=None):
 if not arr.any():return 0
 if watermask is not None and watermask.any():
  yy,xx=pos;fr=[]
  for f in seaidx:
   a=arr.copy();patch=f[np.arange(yy,yy+8)[:,None]%32,np.arange(xx,xx+8)[None,:]%32];a[watermask]=patch[watermask];fr.append(a)
  key=b''.join(a.tobytes() for a in fr)
  if key not in animations:animations[key]=(len(tiles),fr);tilebanks[len(tiles)]=bank;tiles.append(fr[0])
  return animations[key][0]|bank<<12
 for hf,vf,bits in [(0,0,0),(1,0,1024),(0,1,2048),(1,1,3072)]:
  v=arr[::-1] if vf else arr;v=v[:,::-1] if hf else v
  if v.tobytes() in lookup:return lookup[v.tobytes()]|bits|bank<<12
 tid=len(tiles);tilebanks[tid]=bank;tiles.append(arr.copy());lookup[arr.tobytes()]=tid;return tid|bank<<12
seam_fixes=[]
for m in maps:
 grid=[];doors={tuple(d['door']) for d in m['buildings']}
 for cy in range(m['h']):
  for cx in range(m['w']):
   pairs=[]
   for q in range(4):
    x=cx*16+q%2*8;y=cy*16+q//2*8;bk=m['bank'][y:y+8,x:x+8];ix=m['idx'][y:y+8,x:x+8];bs=list(np.unique(bk));rgb=m['expected'][y:y+8,x:x+8]
    # Shared colors can be represented by a neighboring bank, avoiding a third layer.
    if len(bs)>2:
     found=False
     for a in range(13):
      for b in range(a,13):
       cs={tuple(c) for c in np.concatenate([np.array(pals[a][1:]),np.array(pals[b][1:])])}
       if all(tuple(c) in cs for c in rgb.reshape(-1,3)):
        nb=np.full((8,8),b,np.int8);ni=nearest(rgb,pals[b]);pm={tuple(c):i for i,c in enumerate(pals[a]) if i}
        for yy in range(8):
         for xx in range(8):
          if tuple(rgb[yy,xx]) in pm:nb[yy,xx]=a;ni[yy,xx]=pm[tuple(rgb[yy,xx])]
        bk,ix=nb,ni;bs=list(np.unique(nb));found=True;break
      if found:break
     if not found:
      # Author a bounded seam correction into source pixels before exact packing.
      # Preserve animated water; select the two source banks with least color error.
      best=None
      for a in bs:
       for b in bs:
        if 1 in bs and a!=1 and b!=1:continue
        pp=np.array(pals[a][1:]+pals[b][1:],int);dist=((rgb.astype(int)[...,None,:]-pp)**2).sum(-1);cost=dist.min(-1).sum()
        if best is None or cost<best[0]:best=(cost,a,b,dist.argmin(-1),pp)
      cost,a,b,ids,pp=best;bk=np.where(ids<15,a,b).astype(np.int8);ix=(ids%15+1).astype(np.uint8);bs=list(np.unique(bk))
      m['expected'][y:y+8,x:x+8]=pp[ids];m['bank'][y:y+8,x:x+8]=bk;m['idx'][y:y+8,x:x+8]=ix
      seam_fixes.append(dict(map=m['name'],x=x,y=y,squared_error=int(cost)))
    # Water is an opaque lower layer underneath scenery. Animate the hidden
    # pixels too, so boat/tree silhouettes do not require duplicate water tiles.
    bs.sort(key=lambda b:(b!=1,int(b)));es=[]
    for b in bs:
     ar=np.where(bk==b,ix,0).astype(np.uint8);wm=None
     if b==0 and 1 not in bs:
      # Ground is the lower layer. Fill pixels hidden by scenery with the
      # matching original texture, avoiding a new cutout tile per tree edge.
      known=bk==0;best=None
      for texture in [textures[k] for k in ['grass','path','sand']]:
       pat=texture[np.arange(y,y+8)[:,None]%texture.shape[0],np.arange(x,x+8)[None,:]%texture.shape[1]]
       score=np.count_nonzero(pat[known]!=ix[known])
       if best is None or score<best[0]:best=(score,pat)
      matches=np.flatnonzero((ground_candidates[:,known]==ix[known]).all(axis=1))
      if len(matches):ar[:]=ground_candidates[matches[0]]
      else:ar[~known]=best[1][~known]
     if b==1:
      wm=m['water'][y:y+8,x:x+8].copy();covered=bk!=1;pattern=seaidx[0][np.arange(y,y+8)[:,None]%32,np.arange(x,x+8)[None,:]%32]
      if wm.any():ar[covered]=pattern[covered];wm|=covered
      else:
       sand=textures['_sand_sea'];patch=sand[np.arange(y,y+8)[:,None]%sand.shape[0],np.arange(x,x+8)[None,:]%sand.shape[1]]
       ar[covered]=patch[covered]
     es.append(tile(ar,int(b),wm,(y,x)))
    pairs.append(es+[0]*(2-len(es)))
   entries=tuple(v[0] for v in pairs)+tuple(v[1] for v in pairs)
   old=int(m['grid'][cy,cx]);mid=old&1023;at=t.attrs[int(mid>=512)][mid%512]
   if (cx,cy) in doors:at=0x1069
   else:at=(at&0xfff)|0x1000
   key=(entries,at)
   if key not in bl:bl[key]=len(blocks);blocks.append(entries);attrs.append(at)
   grid.append((old&~1023)|bl[key])
 m['output']=grid
from collections import Counter
print('tile banks',Counter(tilebanks.values()),'animations',len(animations))
print('map tile demand',[(m['name'],len({e&1023 for v in m['output'] for e in blocks[v&1023]})) for m in maps])
assert len(tiles)<=1008,('tiles',len(tiles));assert len(blocks)<=1024,('metatiles',len(blocks))
# Animate an explicit contiguous block, remapping both tile pools afterwards.
an=[v for v in animations.values()];oldids=[v[0] for v in an];order=[0]+oldids+[i for i in range(1,len(tiles)) if i not in set(oldids)];remap={v:i for i,v in enumerate(order)};tiles=[tiles[i] for i in order];blocks=[tuple((e&~1023)|remap[e&1023] for e in b) for b in blocks]
for part in range(2):
 folder=G/f'data/tilesets/{"secondary" if part else "primary"}/cherrygrove';sheet=Image.new('P',(128,256));sheet.putpalette([i*16 for i in range(16) for _ in range(3)]+[0]*720)
 for i,ar in enumerate(tiles[part*512:(part+1)*512]):sheet.paste(Image.frombytes('P',(8,8),ar.tobytes()),(i%16*8,i//16*8))
 sheet.save(folder/'tiles.png',bits=4);bb=blocks[part*512:(part+1)*512];aa=attrs[part*512:(part+1)*512]
 if not bb:bb=[(0,)*8];aa=[0]
 (folder/'metatiles.bin').write_bytes(struct.pack('<'+'H'*len(bb)*8,*[e for b in bb for e in b]));(folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(aa),*aa))
 for b,pal in pals.items():cb.write_pal(folder/'palettes'/f'{b:02}.pal',pal)
cb.write_sea_anim(G,[[fr[k] for _,fr in an] for k in range(8)],1,len(an))
# The shared generator leaves blank lines when replacing its section. Keep
# regeneration byte-stable across differing numbers of authoring runs.
animsrc=G/'src/tileset_anims.c';animsrc.write_text(re.sub(r'\n{3,}(?=// Claude Cherrygrove sea)', '\n\n', animsrc.read_text()))
headers=G/'src/data/tilesets/headers.h';s=headers.read_text();a=s.index('const struct Tileset gTileset_CherrygrovePrimary');end=s.index('};',a);chunk=s[a:end].replace('InitTilesetAnim_General','InitTilesetAnim_CherrygrovePrimary');s=s[:a]+chunk+s[end:];headers.write_text(s)
for m in maps:
 f=G/f'data/layouts/{m["name"]}';f.joinpath('map.bin').write_bytes(struct.pack('<'+'H'*len(m['output']),*m['output']))
 # Existing border is scenery beyond padded maps. Use a solid complete grass cell;
 # the visible outer forest is contained in the preserved 8-cell camera padding.
 v=[m['output'][0],m['output'][1],m['output'][m['w']],m['output'][m['w']+1]];f.joinpath('border.bin').write_bytes(struct.pack('<4H',*v))
installed=Tileset(G,'cherrygrove','cherrygrove')
for m in maps:
 im=installed.map_image(m['output'],m['w']);assert np.array_equal(np.array(im),m['expected']),('roundtrip',m['name']);im.save(EV/(m['name']+'.png'))
(EV/'integration.json').write_text(json.dumps(dict(tiles=len(tiles),metatiles=len(blocks),animated_tiles=len(an),exact_pixel_roundtrip=True,edge_module_reuse=edge_reuse,seam_fixes=seam_fixes,maps=[dict(name=m['name'],trees=len(m['positions']),tree_footprints=m['tree_footprints'],buildings=m['buildings']) for m in maps]),indent=2)+'\n')
print('native',len(tiles),'tiles',len(blocks),'metatiles',len(an),'animated')

from events import apply_events
apply_events(G)
