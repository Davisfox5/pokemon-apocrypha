"""Native art derived from HGSS textures and accepted Cherrygrove assets."""
from pathlib import Path
import json,struct
import numpy as np
from PIL import Image,ImageDraw
from claude_cherrygrove.pixel import Canvas
from claude_cherrygrove import banks
ROOT=Path(__file__).resolve().parents[4];OUT=ROOT/'gba/art/route30-hgss-blocks';REF=ROOT/'gba/art/johto-cohesion/references';CG=ROOT/'gba/art/cherrygrove-synthesis'

def indexed(path,bank,pals):
 im=Image.open(path);c=Canvas(im.width,im.height,pals[bank]);c.px=np.asarray(im).copy();return c

def rgba_to_canvas(a,bank,pals):
 c=Canvas(a.shape[1],a.shape[0],pals[bank]);m=a[...,3]>0
 pal=np.asarray(pals[bank].gba()[1:],int);c.px[m]=((a[m,:3].astype(int)[:,None]-pal[None])**2).sum(2).argmin(1)+1
 return c

def scenery(t,mid,bank,pals):
 c=Canvas(16,16,pals[bank]);entries=t.blocks[0][mid]
 for layer in range(2):
  for q in range(4):
   e=entries[layer*4+q]
   if e>>12!=bank:continue
   tid=e&1023;a=np.asarray(t.tiles[int(tid>=512)][tid-512 if tid>=512 else tid]).reshape(8,8)
   if e&1024:a=a[:,::-1]
   if e&2048:a=a[::-1]
   y,x=q//2*8,q%2*8;d=c.px[y:y+8,x:x+8];d[a>0]=a[a>0]
 return c

def create(pals,t,game):
 a={name:indexed(CG/'refined'/(name+'.png'),bank,pals) for name,bank in [('tree',3),('gable',6),('house_mirror',6)]}
 # Exact Emerald Expansion general metatiles; donor lawn is transparent.
 donor=__import__('tiles').Tileset(game)
 mids={'cliff-west-0':0x76,'cliff-west-1':0x76,'cliff-east-0':0x75,'cliff-east-1':0x75,'cliff-cap-0':0x7c,'cliff-cap-1':0x7c,'cliff-face-0':0x7c,'cliff-face-1':0x7c,'ledge-left':0xd5,'ledge-middle':0x87,'ledge-right':0xd6,'step-left':0xaf,'step-middle':0xcf,'step-right':0xaf}
 rgb={name:np.asarray(donor.render(mid)) for name,mid in mids.items()}
 colors=sorted({tuple(map(int,c)) for im in rgb.values() for c in im.reshape(-1,3) if not (int(c[1])>int(c[0])+15 and int(c[1])>int(c[2])+15)})
 from claude_cherrygrove.pixel import Palette
 assert len(colors)<=15,colors
 existing=pals[8].gba();assert all(color in existing for color in colors),('Native palette missing',colors,existing)
 for name,im in rgb.items():
  c=Canvas(16,16,pals[8])
  for i,color in enumerate(colors,1):c.px[np.all(im==color,2)]=existing.index(color)
  if name=='step-right':c.px=c.px[:,::-1].copy()
  a[name]=c
 sign=np.asarray(Image.open(CG/'references/C/sign.png').convert('RGBA'))[:,:16];a['sign']=rgba_to_canvas(sign,5,pals)
 (OUT/'source/emerald-assets.json').write_text(json.dumps({'primary':'general','metatiles':{name:hex(mid) for name,mid in mids.items()},'palette_bank':8,'original_RGB':True,'cuttable_tree':'native OBJ_EVENT_GFX_CUTTABLE_TREE object and EventScript_CutTree'},indent=2)+'\n')
 # Small HGSS Apricorn silhouette; keep pixels at native size, clean lawn mask.
 raw=np.asarray(Image.open(OUT/'source/hgss-reference.png').convert('RGBA'))[75:107,339:355].copy()
 lawn=np.asarray([(104,208,152),(104,200,152),(96,192,144),(88,176,136),(96,200,152),(104,216,152)])
 dist=((raw[...,:3].astype(int)[...,None,:]-lawn)**2).sum(3).min(2);raw[...,3][dist<200]=0
 a['apricorn']=rgba_to_canvas(raw,3,pals)
 for i,mid in enumerate([197,198,199,200]):a['flower-'+str(i)]=scenery(t,mid,4,pals)
 # Native grass edge masks come from the real TEX0 egrass family.
 full=np.asarray(Image.open(REF/'egrass.png').convert('RGBA')).copy();up=np.asarray(Image.open(REF/'egrass_u.png').convert('RGBA'));vertical=np.asarray(Image.open(REF/'egrass_v.png').convert('RGBA'))
 grass_colors=[(32,112,80),(32,120,88),(40,136,80),(56,152,88),(64,168,112),(80,192,120)]
 native=np.asarray(grass_colors,int);original=full[...,:3].copy()
 ordered=sorted(np.unique(original.reshape(-1,3),axis=0),key=lambda v:int(v.sum()))
 for old,new in zip(ordered,grass_colors):full[...,:3][np.all(original==old,axis=2)]=new
 up=up.copy();vertical=vertical.copy()
 for tex in [up,vertical]:tex[...,3][np.all(tex[...,:3]==(123,123,123),axis=2)]=0
 # HGSS combines the ground grass texture and upright grass billboard. Keep
 # both at native scale rather than stretching a shaded floor into bands.
 source_palette=np.asarray(ordered,int);up_native=native[((up[...,:3].astype(int)[...,None,:]-source_palette)**2).sum(3).argmin(2)]
 full[up[...,3]>0,:3]=up_native[up[...,3]>0]
 yy,xx=np.indices((16,16));upper=np.array([np.flatnonzero(up[:,x,3]>0)[0] if (up[:,x,3]>0).any() else 8 for x in range(16)])
 left=np.array([np.flatnonzero(vertical[y,:,3]>0)[0] if (vertical[y,:,3]>0).any() else 4 for y in range(16)])
 raw_assets={}
 for n in range(2):
  for s in range(2):
   for w in range(2):
    for e in range(2):
     q=full.copy();mask=np.ones((16,16),bool)
     if not n:mask&=yy>=upper[xx]
     if not s:mask&=yy<16-upper[xx]//2
     if not w:mask&=xx>=left[yy]
     if not e:mask&=xx<16-left[yy]
     q[...,3]=mask*255;raw_assets[f'grass-{n}{s}{w}{e}']=q
 # Shared bank 12 contains the exact grass ladder plus a small freshwater ladder.
 water=np.asarray(Image.open(OUT/'source/hgss-reference.png').convert('RGB'))[788:820,370:402]
 for bits in range(16):
  for phase in range(4):
   q=np.zeros((16,16,4),np.uint8);q[...,:3]=water[phase//2*16:phase//2*16+16,phase%2*16:phase%2*16+16];q[...,3]=255
   distance=np.full((16,16),16)
   for side,flag in enumerate([1,2,4,8]):
    if not bits&flag:distance=np.minimum(distance,[yy,15-yy,xx,15-xx][side])
   q[distance==0,3]=0;q[distance==1,:3]=(104,208,152);q[distance==2,:3]=(160,144,104);q[distance==3,:3]=(88,112,80);q[distance==4,:3]=(72,200,224)
   for vertical,horizontal in [(1,4),(1,8),(2,4),(2,8)]:
    if not bits&vertical and not bits&horizontal:
     corner_y=yy if vertical==1 else 15-yy;corner_x=xx if horizontal==4 else 15-xx;q[corner_y+corner_x<5,3]=0
   raw_assets['pond-'+str(bits)+'-'+str(phase)]=q
 b=banks.Bank(12,'HGSS_GRASS_FRESHWATER','secondary').keep(*grass_colors)
 for k,q in raw_assets.items():b.add(k,q)
 for i,color in enumerate([(104,208,152),(104,200,152),(88,176,136),(96,192,144)]):b.add('ground-'+str(i),np.asarray([[list(color)+[255]]],np.uint8)).keep(color)
 a.update(b.build());pals[12]=b.palette
 # Import the independently compiled Porytiles family only after exact native
 # RGB/alpha equivalence. The common CG tilesets are not compiler input.
 compiled=OUT/'source/porytiles-native'
 if compiled.exists():
  sheet=np.asarray(Image.open(compiled/'tiles.png'));tiles=[sheet[y:y+8,x:x+8] for y in range(0,sheet.shape[0],8) for x in range(0,sheet.shape[1],8)]
  blocks=list(struct.iter_unpack('<8H',(compiled/'metatiles.bin').read_bytes()));cp={int(p.stem):np.asarray([list(map(int,line.split())) for line in p.read_text().splitlines()[3:19]],np.uint8) for p in (compiled/'palettes').glob('*.pal')}
  names=[k for k in a if k.startswith('grass-')]
  for i,name in enumerate(names):
   decoded=np.zeros((16,16,4),np.uint8)
   for layer in range(2):
    for q in range(4):
     en=blocks[i][layer*4+q];pixels=tiles[en&1023].copy()
     if en&1024:pixels=pixels[:,::-1]
     if en&2048:pixels=pixels[::-1]
     y,x=q//2*8,q%2*8;part=decoded[y:y+8,x:x+8];m=pixels>0;part[m,:3]=cp[en>>12][pixels[m]];part[m,3]=255
   assert np.array_equal(decoded,a[name].to_rgba()),('Porytiles family mismatch',name)
   a[name]=rgba_to_canvas(decoded,12,pals)
  (OUT/'evidence/porytiles.json').write_text(json.dumps({'version':'legacy 2.0.0','compiled_variants':16,'native_RGB_and_alpha_errors':0,'import_palette_bank':12},indent=2)+'\n')

 material=OUT/'source/materials';material.mkdir(exist_ok=True)
 for k,c in a.items():Image.fromarray(c.to_rgba()).save(material/(k+'.png'))
 # Standalone Porytiles input; current map tilesets are never reordered by it.
 p=OUT/'source/porytiles-grass';p.mkdir(exist_ok=True);bottom=Image.new('RGBA',(128,32));middle=bottom.copy()
 for i,k in enumerate(k for k in a if k.startswith('grass-')):middle.paste(Image.fromarray(a[k].to_rgba()),(i%8*16,i//8*16))
 bottom.save(p/'bottom.png');middle.save(p/'middle.png');bottom.save(p/'top.png')
 return a
