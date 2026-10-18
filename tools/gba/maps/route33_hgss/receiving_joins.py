"""Guarded Route33 receiving-join edit over f3022508. No layout replay.
Existing native corner modules for taller HGSS mountain geometry; canonical
straight faces retained. Native HGSS source guides the arch and path footprint.
"""
from pathlib import Path
import sys,json,hashlib,struct,argparse
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent));from tiles import Tileset
S=ROOT/'gba/art/route33-hgss/source';E=S.parent/'evidence';D=S/'receiving-joins';D.mkdir(exist_ok=True)
p=argparse.ArgumentParser();p.add_argument('engine',type=Path);p.add_argument('native_reference',type=Path);p.add_argument('--install',action='store_true');a=p.parse_args();G=a.engine
for f,h in json.loads((S/'joins-input-lock.json').read_text())['files'].items():
 if Path(f).name in ['header.inc','events.inc','connections.inc']:continue
 b=(G/f).read_bytes();vs=[b]
 if Path(f).suffix in ['.pal','.inc','.json']:vs += [b.replace(b'\r\n',b'\n'),b.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')]
 assert h in [hashlib.sha256(v).hexdigest() for v in vs],('Source changed',f)
def decode(game):
 t=Tileset(game,'route33','route33');g=np.fromfile(game/'data/layouts/JohtoRoute33/map.bin','<u2').reshape(29,34);out=np.zeros((2,464,544,4),np.uint8);es=np.zeros((29,34,8),np.uint16)
 for y,x in np.ndindex(29,34):
  mid=int(g[y,x]&1023);es[y,x]=t.blocks[int(mid>=512)][mid%512]
  for l in range(2):
   for q in range(4):
    en=int(es[y,x,l*4+q]);i=en&1023;idx=np.array(t.tiles[int(i>=512)][i%512],np.uint8).reshape(8,8)
    if en&1024:idx=idx[:,::-1]
    if en&2048:idx=idx[::-1]
    yy=y*16+q//2*8;xx=x*16+q%2*8;dst=out[l,yy:yy+8,xx:xx+8];m=idx>0;pal=np.array(t.pals[int(en>>12>=6)][en>>12],np.uint8);dst[m,:3]=pal[idx[m]];dst[m,3]=255
 return t,g,out,es

t,grid,old,entries=decode(G);rt,rg,ref,re=decode(a.native_reference);layers=old.copy();bg,fg=layers
pals={i:np.array(t.pals[int(i>=6)][i],np.uint8) for i in range(16)}
# Complete R02/R04 straight faces stay intact. R10 is a north-facing stacked
# elbow, not a southern side-to-front receiving turn. The shared catalog has no
# compatible 24px lower elbow; reuse retained native mountain-corner modules.
# This is a geometry-specific gap, not a replacement for the shared family.
stone=pals[3][1:11];transition=pals[4][1:];nativecap=ref[0]
def fit(im,ramp):
 out=im.copy()
 for c in np.unique(im[...,:3].reshape(-1,3),axis=0):
  near=ramp[np.argmin(np.sum((ramp.astype(int)-c.astype(int))**2,1))];out[np.all(im[...,:3]==c,2),:3]=near
 return out
corners=[(160,172,'outer southwest'),(416,172,'outer southeast'),(168,128,'middle west return'),(200,150,'middle southwest'),(408,150,'middle southeast'),(216,112,'summit southwest'),(376,100,'summit southeast'),(328,112,'summit eastern step'),(360,272,'SE outer southwest'),(408,344,'SE outer lower southwest'),(488,344,'SE outer lower southeast'),(392,236,'SE upper short southwest'),(424,308,'SE upper long southwest'),(472,308,'SE upper long southeast')]
# Correct the southeast upper tier's front baselines against HGSS: 252 and324,
# four pixels lower than the previous248/320 draft. Reuse the complete
# accepted front textures unchanged; alter placement, never stretch their height.
for x0,x1,oldbase,newbase in [(392,424,248,252),(424,488,320,324)]:
 y0=oldbase-24;src=old[1,y0:oldbase,x0:x1].copy();fg[y0:newbase,x0:x1]=0
 bg[y0:y0+4,x0:x1]=ref[0,y0:y0+4,x0:x1]
 fg[y0+4:newbase,x0:x1]=src
 # Native side shading fills the four-pixel continuation at each shoulder.
 for x in [x0,x1-16]:
  bg[y0:y0+4,x:x+16]=ref[0,y0:y0+4,x:x+16]
# Preserve the upper face's cast contact line on its receiving lower plane.
# Native original modules preserve slope, orientation and turn silhouette.
for x,y,role in corners:
 # For relocated upper SE corners, use original source at their true baseline.
 dx,dy=(160,172) if role=='SE outer lower southwest' else ((416,172) if role=='SE outer lower southeast' else (x,y))
 donor=ref[0,dy:dy+16,dx:dx+16].copy() # matching exposed24px turn, not foliage pixels
 # Original native module has backing above and face below. Retain its silhouette
 # and source shading order; fit the body to the exact shared stone ramp.
 joined=fit(donor,transition)
 ground=(donor[...,1].astype(int)>donor[...,0].astype(int)+15);bg[y:y+16,x:x+16][ground]=donor[ground];joined[ground]=0
 fg[y:y+16,x:x+16]=joined
 # Top eight pixels are a local mountain bevel, continuous with the flat plane.
 cap=ref[0,dy-8:dy,dx:dx+16].copy();fg[y-8:y,x:x+16]=fit(cap,transition)
# Local inside shoulders are available native concave corners; restore their
# proper receiving texture instead of covering them with R10 convex elbows.
for x,y,w,h in [(160,32,24,16),(200,128,16,24),(216,40,16,16),(344,96,16,24),(376,184,24,24),(408,240,16,24)]:
 # Only exposed background, not the approved straight face foreground, is edited.
 bg[y:y+h,x:x+w]=ref[0,y:y+h,x:x+w]
# Cave arch: actual HGSS opening width/center and rim silhouette, quantized into
# the existing private native arch palette. No new building/rock art is invented.
hg=np.array(Image.open(S/'hgss-reference.png').convert('RGBA'))
x0,x1,y0,y1=288,328,152,188
arch=hg[y0:y1,x0:x1].copy();arch[...,3]=255
arch=fit(arch,pals[11][1:]);fg[y0:y1,x0:x1]=arch
# Source threshold is a recessed step, with the warp on the black interior at
# (19,11). Keep the recess black and tint the visible lower threshold stone,
# avoiding the old blue/gray marker rectangle.
for y in range(180,188):
 for x in range(288,328):
  c=hg[y,x,:3].astype(int)
  if max(c)-min(c)<45 and 45<max(c)<135:
   fg[y,x,:3]=stone[2 if y<184 else 5]
# Short cave approach: copy only original material geometry using the existing
# native lawn/dirt/grass-border palette. The sign hides part of the source;
# reconstruct that small ground area from its adjacent path, not sign colors.
y0,y1,x0,x1=188,212,288,340;patch=hg[y0:y1,x0:x1].copy()
for y in range(y1-y0):
 for x in range(x1-x0):
  ax=x+x0;ay=y+y0
  if ax<306 and ay>=192:
   left=290 if ay<200 else (292 if ay<204 else 298)
   patch[y,x,:3]=(224,200,128) if ay<208 and ax>=left else (104,200,152)
patch=fit(patch,pals[0][1:]);
# Reuse native lawn behind the complete affected 8px quadrants, including the
# opaque arch/face backing. This prevents old wall colors leaking into dirt.
lawn=old[0,224:240,320:336];yy,xx=np.indices((32,56));bg[184:216,288:344]=lawn[(yy+184)%16,(xx+288)%16]
bg[y0:y1,x0:x1]=patch;fg[y0:y1,x0:x1]=0
# Do not paint source sign/flower/sea pixels into ordinary lawn. The retained
# native sign is a separate prop west of this small dirt patch.
# Blend each cap's lower two pixels toward the face, without altering straight
# face masters or raising/lowering any other terrace.
for v in json.loads((E/'terrain-depth.json').read_text())['profiles']:
 if v['name'].startswith('southeast upper'):continue
 x0,x1,y=v['x0'],v['x1'],v['face_top']
 for yy in range(y-2,y):
  for xx in range(x0,x1):
   if 288<=xx<328 and 152<=yy<188:continue
   # Existing cap pixels only, no whole-row solid bands or silhouette changes.
   c=fg[yy,xx,:3].astype(int)
   if fg[yy,xx,3] and c.sum()>440:fg[yy,xx,:3]=transition[np.argmin(np.sum((transition.astype(int)-np.maximum(0,c-8))**2,1))]
changed=np.any(layers!=old,(0,3));cells=changed.reshape(29,16,34,16).any((1,3));composite=bg.copy();m=fg[...,3]>0;composite[m]=fg[m]
for n,im in [('before',np.where(old[1,...,3:]>0,old[1],old[0])),('target',composite),('background',bg),('foreground',fg)]:Image.fromarray(im).save(D/(n+'.png'))
if a.install:
 glyphs=[np.array(v,np.uint8).reshape(8,8) for v in t.tiles[0]+t.tiles[1]];blocks=[list(v) for v in t.blocks[0]];attrs=list(t.attrs[0]);original_attrs=attrs.copy();used={0};border=np.fromfile(G/'data/layouts/JohtoRoute33/border.bin','<u2')
 for y,x in np.argwhere(~cells):used.update(int(v)&1023 for v in entries[y,x])
 for mid in border&1023:used.update(int(v)&1023 for v in t.blocks[int(mid>=512)][int(mid)%512])
 lookup={};spare=list(range(1,15));pals[5]=np.zeros((16,3),np.uint8)
 used10=set()
 for es in entries.reshape(-1,8):
  for v in es:
   if int(v)>>12==10:used10.update(map(int,glyphs[int(v)&1023].ravel()))
 spare10=[i for i in range(1,15) if i not in used10]
 def keys(im,tid):
  for h in range(2):
   for v in range(2):lookup.setdefault(((im[::-1] if v else im)[:,::-1] if h else (im[::-1] if v else im)).tobytes(),tid|h<<10|v<<11)
 for tid in sorted(used):keys(glyphs[tid],tid)
 free=[i for i in range(1,1008) if i not in used];allocated=[]
 def ent(im,pref):
  cs=set(map(tuple,im[im[...,3]>0,:3]));bs=[b for b in [pref,4]+list(range(13)) if cs<=set(map(tuple,pals[b][1:]))]
  if not bs:
   missing=cs-set(map(tuple,pals[5][1:]));b=5;slots=spare
   if len(missing)>len(slots):b=10;slots=spare10;missing=cs-set(map(tuple,pals[b][1:]))
   assert len(missing)<=len(slots),('Palette capacity',l,xx,yy,cs,missing,len(slots))
   for c in sorted(missing):pals[b][slots.pop(0)]=c
   bs=[b]
  b=bs[0];idx=np.zeros((8,8),np.uint8)
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
  folder=G/f'data/tilesets/{"secondary" if part else "primary"}/route33';sheet=np.zeros((256 if part==0 else 248,128),np.uint8)
  for i in range(512 if not part else 496):
   if i+part*512<len(glyphs):sheet[i//16*8:i//16*8+8,i%16*8:i%16*8+8]=glyphs[i+part*512]
  im=Image.fromarray(sheet,'P');im.putpalette([v for i in range(256) for v in (i*17%256,)*3]);im.save(folder/'tiles.png',bits=4)
  bs=blocks[part*512:(part+1)*512] or [[0]*8];aa=attrs[part*512:(part+1)*512] or [0];(folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*v) for v in bs));(folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(aa),*aa));
  for b in [5,10]:(folder/'palettes'/f'{b:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pals[b])+'\n')
 grid.tofile(G/'data/layouts/JohtoRoute33/map.bin');actual=Tileset(G,'route33','route33').map_image(grid.ravel().tolist(),34);assert np.array_equal(np.array(actual),composite[...,:3])

(E/'receiving-joins.json').write_text(json.dumps(dict(baseline='f3022508260da8dbe88277549a39398056a16c9a',corners=corners,SE_front_baselines=[252,324],changed_cells=int(cells.sum()),changed_pixels=int(changed.sum()),collision_changes=0,installed=a.install),indent=2)+'\n');print('Changed cells',int(cells.sum()))
