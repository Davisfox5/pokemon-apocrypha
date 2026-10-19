"""Guarded individual native house repair. Never regenerates town layout."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'));from tiles import Tileset
G=Path(sys.argv[1]);S=ROOT/'gba/art/azalea-town/source';E=S.parent/'evidence';D=S/'kurt-edge-cleanup';D.mkdir(exist_ok=True)
lock=D/'input-lock.json'
for f,h in json.loads(lock.read_text())['files'].items():
 if Path(f).name in ['header.inc','events.inc','connections.inc']:continue
 b=(G/f).read_bytes();assert h in [hashlib.sha256(v).hexdigest() for v in [b,b.replace(b'\r\n',b'\n'),b.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')]],f
def decode(game):
 t=Tileset(game,'azalea','azalea');g=np.fromfile(game/'data/layouts/JohtoAzaleaTown/map.bin','<u2').reshape(33,64);out=np.zeros((2,528,1024,4),np.uint8);es=np.zeros((33,64,8),np.uint16)
 for y,x in np.ndindex(33,64):
  mid=int(g[y,x]&1023);es[y,x]=t.blocks[int(mid>=512)][mid%512]
  for l in range(2):
   for q in range(4):
    en=int(es[y,x,l*4+q]);i=en&1023;idx=np.array(t.tiles[int(i>=512)][i%512],np.uint8).reshape(8,8)
    if en&1024:idx=idx[:,::-1]
    if en&2048:idx=idx[::-1]
    yy=y*16+q//2*8;xx=x*16+q%2*8;dst=out[l,yy:yy+8,xx:xx+8];m=idx>0;pal=np.array(t.pals[int(en>>12>=6)][en>>12],np.uint8);dst[m,:3]=pal[idx[m]];dst[m,3]=255
 return t,g,out,es
t,grid,old,entries=decode(G);layers=old.copy();bg,fg=layers
pals={i:np.array(t.pals[int(i>=6)][i],np.uint8) for i in range(16)}
a=np.array(Image.open(D/'kurt-before.png').convert('RGBA'));before=a.copy()
# The right eave ends at x84. Everything farther right is log cutout residue.
a[:,85:]=0
# Continue the existing straight dark side, then its short rounded eave corner.
a[31:64,84]=[32,24,24,255]
for y,end in [(64,84),(65,83),(66,82),(67,81),(68,80)]:
 a[y,end+1:]=0;a[y,end]=[32,24,24,255]
a[a[...,3]==0,:3]=0
placements=json.loads((E/'assembly.json').read_text())['placements'];owner=np.zeros((528,1024),np.uint16)
for i,p in enumerate(placements,1):
 im=np.array(Image.open(S/'masters'/(p['name']+'.png')).convert('RGBA'));h,w=im.shape[:2];owner[p['y']:p['y']+h,p['x']:p['x']+w][im[...,3]>0]=i
pid=next(i for i,p in enumerate(placements,1) if p['name']=='kurt');h,w=a.shape[:2];zone=fg[104:104+h,192:192+w];own=owner[104:104+h,192:192+w];zone[own==pid]=0;m=(a[...,3]>0)&((own==0)|(own<=pid));zone[m]=a[m]
Image.fromarray(a).save(S/'masters/kurt.png')
changed=np.any(layers!=old,(0,3));cells=changed.reshape(33,16,64,16).any((1,3));composite=bg.copy();m=fg[...,3]>0;composite[m]=fg[m]
assert not changed[owner!=pid].any();assert not changed[:104].any() and not changed[200:].any();assert np.array_equal(bg,old[0])
if True:
 glyphs=[np.array(v,np.uint8).reshape(8,8) for v in t.tiles[0]+t.tiles[1]];blocks=[list(v) for v in t.blocks[0]];attrs=list(t.attrs[0]);original_attrs=list(attrs);used={0};border=np.fromfile(G/'data/layouts/JohtoAzaleaTown/border.bin','<u2')
 for y,x in np.argwhere(~cells):used.update(int(v)&1023 for v in entries[y,x])
 for mid in border&1023:used.update(int(v)&1023 for v in t.blocks[int(mid>=512)][int(mid)%512])
 lookup={}
 def keys(im,tid):
  for h in range(2):
   for v in range(2):lookup.setdefault(((im[::-1] if v else im)[:,::-1] if h else (im[::-1] if v else im)).tobytes(),tid|h<<10|v<<11)
 for tid in sorted(used):keys(glyphs[tid],tid)
 free=[i for i in range(1,1008) if i not in used];allocated=[]
 def ent(im,pref):
  cs=set(map(tuple,im[im[...,3]>0,:3]));bs=[b for b in [pref,2,12]+list(range(13)) if cs<=set(map(tuple,pals[b][1:]))];assert bs,cs;b=bs[0];idx=np.zeros((8,8),np.uint8)
  for i,c in enumerate(pals[b][1:],1):idx[np.all(im[...,:3]==c,2)&(im[...,3]>0)]=i
  if not idx.any():return 0
  k=idx.tobytes()
  if k not in lookup:
   assert free,'Native tile budget';tid=free.pop(0);allocated.append(tid)
   while tid>=len(glyphs):glyphs.append(np.zeros((8,8),np.uint8))
   glyphs[tid]=idx;keys(idx,tid)
  return lookup[k]|b<<12
 mids=set(map(int,(grid&1023)[~cells]))|set(map(int,border&1023));fm=[i for i in range(len(blocks)) if i not in mids];ml={tuple(blocks[i])+(attrs[i],):i for i in mids};og=grid.copy()
 for y,x in np.argwhere(cells):
  es=[]
  for l in range(2):
   for q in range(4):
    yy=y*16+q//2*8;xx=x*16+q%2*8;es.append(ent(layers[l,yy:yy+8,xx:xx+8],int(entries[y,x,l*4+q])>>12))
  attr=original_attrs[int(og[y,x]&1023)];k=tuple(es)+(attr,)
  if k not in ml:
   i=fm.pop(0) if fm else len(blocks)
   if i==len(blocks):blocks.append(es);attrs.append(attr)
   else:blocks[i]=es;attrs[i]=attr
   ml[k]=i
  grid[y,x]=(grid[y,x]&0xfc00)|ml[k]
 for part in range(2):
  folder=G/f'data/tilesets/{"secondary" if part else "primary"}/azalea';sheet=np.zeros((256 if part==0 else max(8,((len(glyphs)-512+15)//16)*8),128),np.uint8)
  for i in range(512 if not part else (sheet.shape[0]//8)*16):
   if i+part*512<len(glyphs):sheet[i//16*8:i//16*8+8,i%16*8:i%16*8+8]=glyphs[i+part*512]
  im=Image.fromarray(sheet,'P');im.putpalette([v for i in range(256) for v in (i*17%256,)*3]);im.save(folder/'tiles.png',bits=4)
  bs=blocks[part*512:(part+1)*512] or [[0]*8];aa=attrs[part*512:(part+1)*512] or [0];(folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*v) for v in bs));(folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(aa),*aa));(folder/'palettes/02.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pals[2])+'\n')
 grid.tofile(G/'data/layouts/JohtoAzaleaTown/map.bin');actual=Tileset(G,'azalea','azalea').map_image(grid.ravel().tolist(),64);assert np.array_equal(np.array(actual),composite[...,:3])

Image.fromarray(bg).save(S/'background.png');Image.fromarray(fg).save(S/'foreground.png')
report=dict(changed_pixels=int(changed.sum()),changed_cells=int(cells.sum()),collision_changes=0,regular_house_changes=0,separate_log_pile_changes=0,method='Remove log cutout remnants beyond house eave; continue straight side outline and rounded lower corner.',baseline='76a8e5f16b')
(E/'kurt-edge-cleanup.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
