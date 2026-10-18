"""Guarded direct native repair of Route33; preserves unrelated native IDs/art.
No original authoring generator replay. Only changed native entries are cloned.
"""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent));from tiles import Tileset
G=Path(sys.argv[1]);S=ROOT/'gba/art/route33-hgss/source';E=S.parent/'evidence';O=S/'transparent-objects';W,H=34,29
lock=json.loads((S/'previous-224ee13c/native-edit-lock.json').read_text())['files']
for f,h in lock.items():
 if Path(f).name in ['events.inc','connections.inc','header.inc']:continue # generated mapjson output
 b=(G/f).read_bytes();assert h in [hashlib.sha256(b).hexdigest(),hashlib.sha256(b.replace(b'\r\n',b'\n')).hexdigest()],('Preserve changed native source',f)
t=Tileset(G,'route33','route33');grid=np.fromfile(G/'data/layouts/JohtoRoute33/map.bin','<u2').reshape(H,W);pals={i:np.array(t.pals[int(i>=6)][i],np.uint8) for i in range(16)}
blocks=[list(b) for b in t.blocks[0]];attrs=list(t.attrs[0]);assert len(blocks)<512
# All current route metatiles are primary; tile glyphs span both private banks.
glyphs=[np.array(a,np.uint8).reshape(8,8) for a in t.tiles[0]+t.tiles[1]]
bg=np.zeros((464,544,4),np.uint8);fg=bg.copy();bb=np.zeros((58,68),np.uint8);fb=bb.copy();oldentries=np.zeros((H,W,8),np.uint16)
for y in range(H):
 for x in range(W):
  mid=int(grid[y,x]&1023);entries=blocks[mid];oldentries[y,x]=entries
  for l in range(2):
   for q in range(4):
    en=entries[l*4+q];a=glyphs[en&1023].copy()
    if en&1024:a=a[:,::-1]
    if en&2048:a=a[::-1]
    xx=x*16+q%2*8;yy=y*16+q//2*8;dst=(bg if l==0 else fg)[yy:yy+8,xx:xx+8];m=a>0;dst[m,:3]=pals[en>>12][a[m]];dst[m,3]=255;(bb if l==0 else fb)[yy//8,xx//8]=en>>12
oldbg=bg.copy();oldfg=fg.copy();ref=np.array(Image.open(S/'hgss-reference.png').convert('RGB'))
# Keep real object pixels only, rebuilding foreground from separated RGBA sources.
positions=json.loads((E/'previous-224ee13c/assembly.json').read_text())['trees']
for x,y in positions:fg[y*16:y*16+48,x*16:x*16+32]=0
for box in [(52,224,88,260),(438,148,474,184),(352,315,401,352)]:
 x0,y0,x1,y1=box;fg[y0:y1,x0:x1]=0
# Retain every original terrain contour, texture phase and material cell.
# Only the actual source opening's gray floor residue is changed to black.
pals[11]=pals[6].copy();pals[11][15]=[0,0,0]
for y in range(160,192):
 for x in range(288,328):
  if (ref[y,x].max()<80 and abs(int(ref[y,x,0])-int(ref[y,x,1]))<20) or (y>=180 and 297<=x<=315):bg[y,x,:3]=0
mouth=np.all(bg[...,:3]==0,2)&~np.all(oldbg[...,:3]==0,2)
for gy,gx in zip(*np.where(np.any(mouth.reshape(58,8,68,8),(1,3)))):bb[gy,gx]=11
# Original HGSS shore pixels only: no invented cap or procedural coast contour.
for y in range(463):
 for x in range(504,512):
  r,g,b=map(int,ref[y,x]);sea=(b>r+25 and b>g+5);foam=(r>175 and g>185 and b>175 and max(r,g,b)-min(r,g,b)<65)
  if sea or foam:bg[y,x,:3]=ref[y,x]
pixels=bg[:,504:512,:3].reshape(-1,1,3);q=Image.fromarray(pixels).quantize(colors=15,method=Image.Quantize.MEDIANCUT);pals[1]=np.vstack(([0,0,0],np.array((q.getpalette()+[0]*45)[:45]).reshape(15,3)&248)).astype(np.uint8);bb[:,63]=1
# Apply objects with explicit native palette/layer hints, never baked backdrops.
def put(name,x,y,b):
 a=np.array(Image.open(O/(name+'.png')).convert('RGBA'));h,w=a.shape[:2];m=a[...,3]>0;dst=fg[y:y+h,x:x+w];dst[m]=a[m]
 for gy in range(y//8,(y+h+7)//8):
  for gx in range(x//8,(x+w+7)//8):
   if fg[gy*8:gy*8+8,gx*8:gx*8+8,3].any():fb[gy,gx]=b
for x,y in positions:put('T01',x*16,y*16,3)
put('boulder-west',52,224,8);put('boulder-east',438,148,8)
pix=np.concatenate([np.array(Image.open(O/(n+'.png')).convert('RGBA')).reshape(-1,4) for n in ['T03','T04']]);pix=pix[pix[:,3]>0,:3];q=Image.fromarray(pix.reshape(-1,1,3)).quantize(colors=15,method=Image.Quantize.MEDIANCUT);pals[10]=np.vstack(([0,0,0],np.array((q.getpalette()+[0]*45)[:45]).reshape(15,3)&248)).astype(np.uint8)
put('T04',350,315,10);put('T03',366,319,10)
# Locked transparent ledge masters over independent grass backing.
fg[256:272,208:320]=0
for x in range(13,20):put('L11' if x==13 else 'L13' if x==19 else 'L12',x*16,256,2)
arm=np.array(Image.open(S/'shared-art/emerald-0x85.png').convert('RGBA'));m=arm[:12,:4,3]>0;fg[256:268,208:212][m]=arm[:12,:4][m]
fb[32:34,26:40]=2
# Native entry patching uses only freed/unreferenced glyph slots and preserves all
# old metatile indices. Clone each touched cell, leaving unaffected entries intact.
changed=np.any(bg!=oldbg,2)|np.any(fg!=oldfg,2);cells=np.any(changed.reshape(H,16,W,16),(1,3));
# Preserve all original native terrain palette choices outside the tiny mouth/shore edits.
# Full opaque backings for every modified native square; choose edge-appropriate banks.
# Remove mint from all reused foreground, including any old mixed-bank fragments.
fg[np.all(fg[...,:3]==[64,136,104],2)]=0
used=set()
for y in range(H):
 for x in range(W):
  if not cells[y,x]:used.update(int(e)&1023 for e in oldentries[y,x])
# Border courses refer to unchanged southern canopy glyphs. Preserve their IDs.
border=np.fromfile(G/'data/layouts/JohtoRoute33/border.bin','<u2')
for m in border&1023:used.update(int(e)&1023 for e in blocks[int(m)])
lookup={}
for tid in sorted(used):
 a=glyphs[tid]
 for hf in range(2):
  for vf in range(2):lookup.setdefault(((a[::-1] if vf else a)[:,::-1] if hf else (a[::-1] if vf else a)).tobytes(),tid|(hf<<10)|(vf<<11))
free=[i for i in range(1,1008) if i not in used];allocated=[]
def ent(a,b,alpha=None):
 p=pals[b].astype(np.int32);dist=((a.astype(np.int32)[...,None,:]-p)**2).sum(3);dist[...,0]=10**9;idx=dist.argmin(2).astype(np.uint8)
 if alpha is not None:idx[~alpha]=0
 if not idx.any():return 0
 k=idx.tobytes()
 if k not in lookup:
  assert free,'Native glyph budget exhausted';tid=free.pop(0);allocated.append(tid)
  while tid>=len(glyphs):glyphs.append(np.zeros((8,8),np.uint8))
  glyphs[tid]=idx
  for hf in range(2):
   for vf in range(2):lookup.setdefault(((idx[::-1] if vf else idx)[:,::-1] if hf else (idx[::-1] if vf else idx)).tobytes(),tid|(hf<<10)|(vf<<11))
 return lookup[k]|(b<<12)
ml={tuple(b)+(attrs[i],):i for i,b in enumerate(blocks)}
for y,x in zip(*np.where(cells)):
 entries=[]
 for l in range(2):
  for j in range(4):
   px=x*16+j%2*8;py=y*16+j//2*8;a=(bg if l==0 else fg)[py:py+8,px:px+8];b=int((bb if l==0 else fb)[py//8,px//8]);entries.append(ent(a[...,:3],b,None if l==0 else a[...,3]>0))
 old=int(grid[y,x]&1023);attr=attrs[old]
 key=tuple(entries)+(attr,)
 if key not in ml:ml[key]=len(blocks);blocks.append(entries);attrs.append(attr)
 grid[y,x]=(grid[y,x]&0xfc00)|ml[key]
assert len(blocks)<1024
# All map water and the hidden east corridor are blocked; keep original main path.
grid[:,32:]|=0xc00
for part in range(2):
 f=G/f'data/tilesets/{"secondary" if part else "primary"}/route33';start=512*part;n=512 if not part else max(1,min(1008,len(glyphs))-512);sheet=np.zeros((((n+15)//16)*8,128),np.uint8)
 for i in range(n):
  if start+i<len(glyphs):sheet[i//16*8:i//16*8+8,i%16*8:i%16*8+8]=glyphs[start+i]
 im=Image.fromarray(sheet,mode='P');im.putpalette([v for i in range(256) for v in (i*17%256,)*3]);im.save(f/'tiles.png',bits=4)
 bs=blocks[start:start+512];aa=attrs[start:start+512]
 if not bs:bs=[[0]*8];aa=[0]
 (f/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*a) for a in bs));(f/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(aa),*aa))
 for b in [1,10,11]:(f/'palettes'/f'{b:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pals[b])+'\n')
grid.tofile(G/'data/layouts/JohtoRoute33/map.bin');Image.fromarray(bg).save(S/'repaired-background.png');Image.fromarray(fg).save(S/'repaired-foreground.png');np.save(S/'solid.npy',(grid&0xc00)!=0)
(E/'layer-repair.json').write_text(json.dumps({'baseline':'224ee13c','changed_cells':int(cells.sum()),'allocated_glyphs':len(allocated),'glyph_max':max(used|set(allocated)),'metatiles':len(blocks),'extra_trees':[],'water_blocked':bool(np.all(grid[:,32:]&0xc00)),'preserved':'all map/warp IDs, main-path collision, cave interior and unrelated art','method':'original terrain retained tile for tile; locked foreground masters and bounded source-derived mouth/shore corrections only'},indent=2)+'\n')
print('Patched cells',cells.sum(),'glyphs',len(allocated),'max',max(used|set(allocated)),'metatiles',len(blocks))
