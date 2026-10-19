"""Guarded individual native house repair. Never regenerates town layout."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'));from tiles import Tileset
G=Path(sys.argv[1]);S=ROOT/'gba/art/azalea-town/source';E=S.parent/'evidence';D=S/'house-cleanup';D.mkdir(exist_ok=True)
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
pals[2][1]=[88,80,128];pals[2][3]=[152,152,208]
ref=np.array(Image.open(S/'hgss-reference.png').convert('RGBA'));ref[...,:3]&=248
placements=json.loads((E/'assembly.json').read_text())['placements'];owner=np.zeros((528,1024),np.uint16)
for i,p in enumerate(placements,1):
 a=np.array(Image.open(S/'masters'/(p['name']+'.png')).convert('RGBA'));h,w=a.shape[:2];owner[p['y']:p['y']+h,p['x']:p['x']+w][a[...,3]>0]=i
for name,ox,oy,rx,ry in [('kurt',192,104,120,80),('house',512,264,440,248)]:
 a=np.array(Image.open(D/(name+'-before.png')).convert('RGBA'));h,w=a.shape[:2];raw=ref[ry:ry+h,rx:rx+w].copy()
 # Consolidate two redundant outline shades; reserve their palette slots for glass.
 for c in [(16,16,24),(32,32,32)]:a[np.all(a[...,:3]==c,2)&(a[...,3]>0),:3]=[32,24,24]
 def fit(region,mask,colors):
  target=a[region];source=raw[region];cs=np.array(colors,dtype=int);rgb=source[...,:3].astype(int);near=np.argmin(((rgb[:,:,None,:]-cs[None,None,:,:])**2).sum(3),2);target[mask,:3]=cs[near[mask]];target[mask,3]=255
 wood=pals[2][[2,4,5,6,8,10,11,14]]
 if name=='kurt':
  win=(slice(68,84),slice(52,80));door=(slice(64,85),slice(24,48));a[:,90:]=0
 else:
  win=(slice(70,84),slice(44,72));door=(slice(68,88),slice(24,43));a[88:]=0
  # Three ridge vents are part of this house, not missing roof texture.
  vent=(slice(26,36),slice(27,51));v=raw[vent];mask=(v[...,0]>v[...,1]*1.25)&(v[...,1]<112)&(v[...,0]<176);fit(vent,mask,wood)
  # Restore the complete rounded chimney rim and shaft from the HGSS silhouette.
  a[8:32,58:80]=0
  maskim=Image.new('1',(w,h));ImageDraw.Draw(maskim).polygon([(65,11),(73,11),(77,15),(77,23),(73,29),(72,31),(65,31),(65,29),(60,24),(60,16)],fill=1)
  mask=np.array(maskim,dtype=bool)&(np.ptp(raw[...,:3].astype(int),axis=2)<40);fit((slice(None),slice(None)),mask,pals[12][[1,4,5,7,10,11,13,14,15]])
  lower=(slice(80,88),slice(43,76));fit(lower,a[lower][...,3]>0,wood)
 v=raw[win].astype(int);glass=(v[...,2]>v[...,0]+3)&(v[...,2]>v[...,1]+3)&(v[...,:3].max(2)>70);fit(win,glass,pals[2][[1,3]])
 fit(door,a[door][...,3]>0,wood)
 # Preserve original straw grain and silhouette without broad filtering.
 a[a[...,3]==0,:3]=0
 Image.fromarray(a).save(S/'masters'/(name+'.png'))
 pidx=next(i for i,p in enumerate(placements,1) if p['name']==name);zone=fg[oy:oy+h,ox:ox+w];own=owner[oy:oy+h,ox:ox+w];zone[own==pidx]=0
 mask=(a[...,3]>0)&((own==0)|(own<=pidx));zone[mask]=a[mask]
changed=np.any(layers!=old,(0,3));cells=changed.reshape(33,16,64,16).any((1,3))
# Palette changes are safe only where no surviving entries use the repurposed shades.
for y,x in np.argwhere(~cells):
 for en in entries[y,x]:
  if int(en)>>12==2:
   tid=int(en)&1023;idx=np.array(t.tiles[int(tid>=512)][tid%512]);assert not np.isin(idx,[1,3]).any(),(x,y)
composite=bg.copy();m=fg[...,3]>0;composite[m]=fg[m]
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
assert np.array_equal(grid&0xfc00,np.fromfile(D/'map-before.bin','<u2').reshape(33,64)&0xfc00)
report=dict(changed_cells=int(cells.sum()),changed_pixels=int(changed.sum()),collision_changes=0,other_art_changes=0,method='Separate original HGSS house silhouettes; restored violet glazing, warm wooden doors, missing ridge vents and complete chimney; native palette reuse and narrow direct cell patch.',baseline='a322750485104cf985359309f8983681bda0892d')
(E/'house-cleanup.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
