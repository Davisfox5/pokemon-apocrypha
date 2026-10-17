"""Guarded direct native repair of Route33; preserves unrelated native IDs/art.
No original authoring generator replay. Only changed native entries are cloned.
"""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent));from tiles import Tileset
G=Path(sys.argv[1]);S=ROOT/'gba/art/route33-hgss/source';E=S.parent/'evidence';O=S/'transparent-objects';W,H=34,29
lock=json.loads((S/'previous-214e38cf/native-edit-lock.json').read_text())['files']
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
original_grid=grid.copy();oldbg=bg.copy();oldfg=fg.copy();ref=np.array(Image.open(S/'hgss-reference.png').convert('RGB'))
# Seven owner-marked sections, registered directly to original HGSS pixels.
from scipy.ndimage import label,binary_fill_holes,binary_dilation,binary_closing
M=S/'marked-repairs';M.mkdir(exist_ok=True)
regions=[('A','NW rock footing',(0,32,176,56)),('B','upper rear edge',(200,32,448,56)),('C','ledge head',(200,184,232,204)),('D','ledge corner',(200,240,240,280)),('E','SE rear edge',(344,176,512,208)),('F','SE wall corner',(344,248,416,288)),('G','missing SE rock footing',(400,328,512,368))]
# A: missing raised rock padding below the front face, behind transparent crowns.
# Reuse the real unobscured HGSS/native plateau course, not another wall face.
bg[40:48,:160]=oldbg[144:152,176:336];bb[5,:20]=6
# B/E/F: only restore original rock silhouette pixels omitted by polygon clipping.
added=np.zeros((464,544),bool)
def restore_rock(box,seed):
 x0,y0,x1,y1=box;a=ref[y0:y1,x0:x1];r,g,b=a.astype(int).transpose(2,0,1);warm=(r>g+4)&(g>b+4);lab,n=label(warm);i=int(lab[seed[1]-y0,seed[0]-x0]);assert i>0
 mask=binary_fill_holes(lab==i);near=(r>g-24)&(g>b+3)&(r>72);mask|=binary_dilation(mask)&near;mask=binary_closing(mask,structure=np.ones((3,3)),border_value=1);dst=bg[y0:y1,x0:x1];oldgreen=(dst[...,1].astype(int)>dst[...,0].astype(int)+20);restore=mask&oldgreen
 dst[restore,:3]=a[restore];dst[restore,3]=255;added[y0:y1,x0:x1]|=restore
 return int(restore.sum())
restored={}
restored['B']=restore_rock((200,32,448,56),(248,48))
restored['E']=restore_rock((352,184,504,208),(400,200))
restored['F']=restore_rock((352,248,416,286),(384,272))
# G: a one-cell rock-padding course is occluded by original HGSS foliage.
# Fill that missing raised plane from the same clean native HGSS plateau course;
# the compact original native texture core fills the occluded course; rounded outer
# corners stay within the original cliff footing. No forest rows are moved.
for y in range(336,352):
 inset=round(4*((y-336)/15)**2)
 for x in range(411+inset,504-inset):
  a=oldbg[144+(y-336),176+(x-411)%16].copy();bg[y,x]=a;added[y,x]=True
grid[21,26:32]|=0xc00
# One spare native palette is reserved for mixed stone/grass edge quadrants only.
used_banks={int(e)>>12 for row in oldentries.reshape(-1,8) for e in row if e};assert 4 not in used_banks
colors=list(dict.fromkeys(tuple(c) for c in oldbg[...,:3][(oldbg[...,1].astype(int)>oldbg[...,0].astype(int)+20)]));colors=sorted(colors,key=lambda c:sum(map(int,c)))
# Accepted lawn uses five shades; retain them exactly at every restored boundary.
greens=sorted(colors,key=lambda c:-int(np.count_nonzero(np.all(oldbg[...,:3]==c,2))))[:5]
stone=[pals[6][i].tolist() for i in [1,2,3,4,6,7,9,11,13,15]];pals[4]=np.array([[0,0,0]]+[list(c) for c in greens]+stone,np.uint8)
for gy,gx in zip(*np.where(np.any(added.reshape(58,8,68,8),(1,3)))):
 a=bg[gy*8:gy*8+8,gx*8:gx*8+8,:3].astype(int);green=a[...,1]>a[...,0]+20;bb[gy,gx]=4 if green.any() else 6
# C/D: install real Emerald west-ledge body and its rounded southwest corner.
# Texture, palette, jump axis and metatile behaviors stay native Emerald.
fg[188:272,208:328]=0
arm=np.array(Image.open(S/'shared-art/emerald-0x85.png').convert('RGBA'))
# Fit the actual native vertical face and warm rounded end; no solid cliff block.
corner=np.zeros((16,16,4),np.uint8);end=np.array(Image.open(O/'L11.png').convert('RGBA'));corner[:12,:8]=arm[:12,:8];mask=end[...,3]>0;corner[mask]=end[mask]
Image.fromarray(corner).save(M/'emerald-southwest-corner.png')
def put_image(a,x,y,bank):
 h,w=a.shape[:2];m=a[...,3]>0;dst=fg[y:y+h,x:x+w];dst[m]=a[m]
 for gy in range(y//8,(y+h+7)//8):
  for gx in range(x//8,(x+w+7)//8):fb[gy,gx]=bank
# Body aligns with HGSS x217 rather than the previous x208 crop origin.
for y in range(188,252,16):put_image(arm,216,y,2)
# A compact native top cap rounds the head rather than leaving a missing square.
head=arm[:8,:8].copy();head[:2]=0;head[0,2:5,:3]=pals[2][3];head[0,2:5,3]=255;head[1,1:6,:3]=pals[2][5];head[1,1:6,3]=255;put_image(head,216,188,2)
put_image(corner,216,248,2)
for i,x in enumerate(range(232,328,16)):
 a=np.array(Image.open(O/('L13.png' if x==312 else 'L12.png')).convert('RGBA'));put_image(a,x,248,2)
# G: keep all approved crowns and root spacing unchanged. The clipped last
# footing course uses the same real raised-plane texture as A, not another face.
shifted=[]
# Source wall recovered in F closes only actual missing rock cells.
for y in range(16,18):
 for x in range(22,26):
  sl=np.s_[y*16:y*16+16,x*16:x*16+16];rock=bg[sl][...,:3].astype(int);cover=(rock[...,0]>rock[...,1]+6)&(rock[...,1]>rock[...,2]+6)
  if added[sl].any() and cover.mean()>.45:grid[y,x]|=0xc00
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
 for b in [4]:(f/'palettes'/f'{b:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pals[b])+'\n')
grid.tofile(G/'data/layouts/JohtoRoute33/map.bin');Image.fromarray(bg).save(M/'background.png');Image.fromarray(fg).save(M/'foreground.png');np.save(S/'solid.npy',(grid&0xc00)!=0)
report={'baseline':'214e38cfb94309965e0cc58d09460e58737e00a6','regions':regions,'restored_source_pixels':restored,'shifted_existing_trees':shifted,'changed_cells':int(cells.sum()),'allocated_glyphs':len(allocated),'glyph_max':max(used|set(allocated)),'metatiles':len(blocks),'water_blocked':bool(np.all(grid[:,32:]&0xc00)),'collision_changes':np.argwhere(((grid^original_grid)&0xc00)!=0).tolist(),'method':'original HGSS boundary recovery, two missing rock-footing courses and a fitted native ledge corner; all tree positions retained'}
(E/'marked-repairs.json').write_text(json.dumps(report,indent=2)+'\n');print('Marked repairs',report)
