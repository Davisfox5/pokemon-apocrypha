"""Tree-free Route33 mountain review. Guarded native edit, never a layout replay.
Whole current R02 masters + retained local 8px mountain bevels = 24px front rises.
"""
from pathlib import Path
import sys,json,hashlib,struct,argparse
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent));from tiles import Tileset
S=ROOT/'gba/art/route33-hgss/source';E=S.parent/'evidence';M=S/'complete-rocks';D=S/'terrain-depth';D.mkdir(exist_ok=True)
p=argparse.ArgumentParser();p.add_argument('engine',type=Path);p.add_argument('baseline',type=Path);p.add_argument('--install',action='store_true');a=p.parse_args();G=a.engine
for f,h in json.loads((S/'treeless-input-lock.json').read_text())['files'].items():
 if Path(f).name in ['header.inc','events.inc','connections.inc']:continue
 b=(G/f).read_bytes();assert h in [hashlib.sha256(b).hexdigest(),hashlib.sha256(b.replace(b'\r\n',b'\n')).hexdigest()],('Owner source changed',f)
prov=json.loads((M/'provenance.json').read_text())
for r in prov['files']:assert hashlib.sha256((M/r['file']).read_bytes()).hexdigest()==r['sha256']
def decode(game):
 t=Tileset(game,'route33','route33');g=np.fromfile(game/'data/layouts/JohtoRoute33/map.bin','<u2').reshape(29,34);out=np.zeros((2,464,544,4),np.uint8);banks=np.zeros((2,58,68),np.uint8);es=np.zeros((29,34,8),np.uint16)
 for y,x in np.ndindex(29,34):
  m=int(g[y,x]&1023);es[y,x]=t.blocks[int(m>=512)][m%512]
  for l in range(2):
   for q in range(4):
    v=int(es[y,x,l*4+q]);i=v&1023;idx=np.array(t.tiles[int(i>=512)][i%512],np.uint8).reshape(8,8)
    if v&1024:idx=idx[:,::-1]
    if v&2048:idx=idx[::-1]
    yy=y*16+q//2*8;xx=x*16+q%2*8;dst=out[l,yy:yy+8,xx:xx+8];mask=idx>0;pal=np.array(t.pals[int(v>>12>=6)][v>>12],np.uint8);dst[mask,:3]=pal[idx[mask]];dst[mask,3]=255;banks[l,yy//8,xx//8]=v>>12
 return t,g,out,banks,es
t,grid,layers,banks,entries=decode(G);bt,bggrid,base,bb,be=decode(a.baseline);old=layers.copy();bg,fg=layers;original_grid=grid.copy();before=bg.copy();mask=fg[...,3]>0;before[mask]=fg[mask];Image.fromarray(before).save(D/'before.png')
# Only the two mountain surfaces restore the original native reference treatment.
# Current paths/shore/ledge/props stay authoritative; no original generator executes.
bg[:192,:440]=base[0,:192,:440];banks[0,:24,:55]=bb[0,:24,:55]
bg[192:360,352:504]=base[0,192:360,352:504];banks[0,24:45,44:63]=bb[0,24:45,44:63]
# Remove all large and Apricorn trees using the approved master footprints.
removed=np.zeros((464,544),bool);positions=json.loads((E/'assembly.json').read_text())['trees'];objs=[]
for x,y in positions:objs.append(('T01',x*16,y*16))
objs += [('T04',350,315),('T03',366,319)]
for name,x,y in objs:
 im=np.array(Image.open(S/'transparent-objects'/(name+'.png')).convert('RGBA'));h,w=im.shape[:2];m=im[...,3]>0;fg[y:y+h,x:x+w][m]=0;removed[y:y+h,x:x+w]|=m
# Remove stale mint ground pixels only if they actually belonged to removed trees.
assert not fg[removed,3].any()
# Props were layered in front of some tree crowns. Restore only their approved
# silhouettes from the exact old native foreground, never whole tree rectangles.
for name,x,y in [('boulder-west',52,224),('boulder-east',438,148)]:
 im=np.array(Image.open(S/'transparent-objects'/(name+'.png')).convert('RGBA'));h,w=im.shape[:2];m=im[...,3]>0;fg[y:y+h,x:x+w][m]=old[1,y:y+h,x:x+w][m]
# Four green pixels in the old boulder crop were foliage remnants, not stone.
green=(fg[...,3]>0)&(fg[...,1].astype(int)>fg[...,0]+15)&(fg[...,1].astype(int)>fg[...,2]+15);assert int(green.sum())<=4;fg[green]=0
props=fg.copy();rock=np.zeros_like(fg);levels=np.zeros((464,544),np.uint8);structure=np.zeros((464,544),np.uint8);placements=[];profiles=[];cap_mask=np.zeros((464,544),bool)
R={n:np.array(Image.open(M/(n+'.png')).convert('RGBA')) for n in json.loads((M/'catalog.json').read_text())}
def over(dst,im,x,y):
 h,w=im.shape[:2];m=im[...,3]>0;dst[y:y+h,x:x+w][m]=im[m]
def poly(points,level):
 im=Image.new('L',(544,464));ImageDraw.Draw(im).polygon(points,fill=level);m=np.array(im)>0;levels[m]=level
poly([(0,0),(360,0),(360,40),(432,40),(432,188),(160,188),(160,40),(0,40)],1)
poly([(168,0),(344,0),(344,40),(424,40),(424,166),(200,166),(200,144),(168,144)],2)
poly([(216,48),(392,48),(392,116),(344,116),(344,128),(216,128)],3)
poly([(360,192),(504,192),(504,360),(408,360),(408,288),(376,288),(360,272)],1)
poly([(392,192),(488,192),(488,320),(424,320),(424,248),(392,248)],2)
# Reuse native clean plateau quadrants only in actual missing raised planes.
core=base[0,144:160,176:192].copy()
def fill(x,y,w,h):
 yy,xx=np.indices((h,w));bg[y:y+h,x:x+w]=core[(yy+y)%16,(xx+x)%16]
fill(216,40,216,8);banks[0,5,27:54]=6
fill(424,320,64,24);banks[0,40:43,53:61]=6
# The occluded footing still needs a bevel, not eight extra pixels of flat top.
for x in range(424,488,32):bg[336:344,x:x+32]=base[0,16:24,32:64]
# Every new wall placement is a full, unaltered 16x16 catalog master or its mirror.
def tile(n,x,y,high,low,role,mirror=False):
 im=R[n][:,::-1].copy() if mirror else R[n];over(rock,im,x,y);structure[y:y+16,x:x+16]=high*16+low
 placements.append(dict(tile=n,x=x,y=y,high=high,low=low,role=role,mirror=mirror))
def side(x,y0,y1,high,low,east=False,phase=0):
 # Whole tiles may continue behind the front corner; they are never height-scaled.
 for k,y in enumerate(range(y0,y1,16)):tile('R11' if (k+phase)%2 else 'R12',x,y,high,low,'east side' if east else 'west side',east)
def front(x0,x1,base_y,high,low,name,skip=()):
 # Preserve the taller local bevel geometry, but fit its shading to the shared
 # stone ramp. One fixed source-index/ramp mapping is reused on every rise.
 ramp=sorted(set(tuple(map(int,c)) for n in ['R02','R04','R10','R11','R12'] for c in R[n][R[n][...,3]>0,:3]),key=lambda c:sum(c))
 oldramp=sorted(set(tuple(map(int,c)) for c in bt.pals[1][6][1:]),key=lambda c:sum(c))
 for x in range(x0,x1):
  if any(s0<=x<s1 for s0,s1 in skip):continue
  for y in range(base_y-24,base_y-16):
   c=bg[y,x,:3].astype(int)
   if c[0]>c[1]+5 and c[1]>c[2]+5:
    rank=min(range(len(oldramp)),key=lambda i:sum((int(c[k])-oldramp[i][k])**2 for k in range(3)))
    rock[y,x,:3]=ramp[round(rank*(len(ramp)-1)/(len(oldramp)-1))];rock[y,x,3]=255;cap_mask[y,x]=True
 profiles.append(dict(name=name,high=high,low=low,cap_top=base_y-24,face_top=base_y-16,base=base_y,depth=24,bevel=8,shared_face=16,x0=x0,x1=x1))
 for k,x in enumerate(range(x0,x1,16)):
  if any(x<s1 and x+16>s0 for s0,s1 in skip):continue
  tile('R02' if k%2==0 else 'R04',x,base_y-16,high,low,name)
# Northern outer rise: 0->1. Main front is 24px deep, including its local bevel.
side(344,0,40,1,0,True);front(0,160,40,1,0,'northwest exterior front')
side(160,40,172,1,0);side(416,40,172,1,0,True)
front(160,432,188,1,0,'northern exterior front',[(288,336)])
# Keep native inside shoulder: complete R17 has the opposite receiving turn.
tile('R10',160,172,1,0,'outer southwest front corner',True);tile('R10',416,172,1,0,'outer southeast front corner')
# Preserve complete accepted cave arch/shoulders rather than drawing rock across it.
rock[156:192,288:336]=0
# Middle rise: 1->2, with its stepped southern contour and correct side overlaps.
side(168,40,128,2,1);side(408,40,150,2,1,True)
front(168,200,144,2,1,'middle west return');tile('R10',168,128,2,1,'middle southwest return',True)
side(200,144,150,2,1)
front(200,424,166,2,1,'middle southern front');tile('R10',200,150,2,1,'middle southwest corner',True);tile('R10',408,150,2,1,'middle southeast corner')
# Inner summit: 2->3. Preserve both front baselines, not one flattened front.
side(216,48,112,3,2);side(376,48,100,3,2,True)
front(216,344,128,3,2,'summit long front');tile('R10',216,112,3,2,'summit southwest corner',True)
front(344,392,116,3,2,'summit short eastern front');tile('R10',376,100,3,2,'summit southeast corner');tile('R10',328,112,3,2,'summit stepped southeast return')
# Southeast outer platform: keep the footprint and one complete 24px rise.
side(360,192,272,1,0);side(488,192,344,1,0,True)
front(360,408,288,1,0,'southeast short outer return');tile('R10',360,272,1,0,'southeast outer southwest return',True)
side(408,288,344,1,0) # Native receiving inside corner remains, no false convex block.
front(408,504,360,1,0,'southeast outer footing, originally occluded');tile('R10',408,344,1,0,'southeast outer southwest corner',True);tile('R10',488,344,1,0,'southeast outer southeast corner')
# Southeast raised L: both front depths stay 24px above the same outer platform.
side(392,192,232,2,1);side(480,192,304,2,1,True)
front(392,424,248,2,1,'southeast upper short front');tile('R10',392,232,2,1,'southeast upper west corner',True)
side(424,248,304,2,1);front(424,488,320,2,1,'southeast upper long front');tile('R10',424,304,2,1,'southeast upper southwest corner',True);tile('R10',472,304,2,1,'southeast upper southeast corner')
# New rock always lies behind the retained non-tree props and ledge art.
fg[:]=rock; m=props[...,3]>0;fg[m]=props[m]
# The native cliff face is opaque terrain. Canonicalize only fully hidden 8x8
# backing quadrants to the existing plateau core; visible RGB is unchanged. This
# saves the hardware budget without dropping cap detail or substituting art.
hidden=0
for gy,gx in np.ndindex(58,68):
 sl=np.s_[gy*8:gy*8+8,gx*8:gx*8+8]
 if np.all(rock[sl][...,3]==255):
  yy,xx=np.indices((8,8));bg[sl]=core[(yy+gy*8)%16,(xx+gx*8)%16];banks[0,gy,gx]=6;hidden+=1
# Bank3 was the removed tree family. No retained object may still require it.
pals={i:np.array(t.pals[int(i>=6)][i],np.uint8) for i in range(16)}
colors=sorted(set(tuple(map(int,c)) for n in sorted({v['tile'] for v in placements}) for im in [R[n]] for c in im[im[...,3]>0,:3]));assert len(colors)<=15
pals[3]=np.array([[0,0,0]]+list(colors)+[[0,0,0]]*(15-len(colors)),np.uint8)
# Bank10 was Apricorn art; it is now available for rare mixed ledge/wall quadrants.
free_indices={10:list(range(1,16))};pals[10]=np.zeros((16,3),np.uint8)
for l,im in enumerate([bg,fg]):
 for gy,gx in np.ndindex(58,68):
  imq=im[gy*8:gy*8+8,gx*8:gx*8+8];cs=set(map(tuple,imq[imq[...,3]>0,:3]));pref=int(banks[l,gy,gx]);choices=[pref,3]+list(range(13));valid=[b for b in choices if cs<=set(map(tuple,pals[b][1:]))]
  if not valid:
   spare=free_indices[10];present=set(map(tuple,pals[10][1:]));missing=cs-present;assert len(missing)<=len(spare),('Exact palette capacity',l,gx,gy,len(cs),len(missing),len(spare))
   for c in sorted(missing):pals[10][spare.pop(0)]=c
   valid=[10]
  banks[l,gy,gx]=valid[0]
# Review-stage tree removal preserves forest/fruit collision; no new paths open.
# Lower footing remains blocked, as in the source revision. No event/warp changes.
changed=np.any(layers!=old,(0,3));cells=changed.reshape(29,16,34,16).any((1,3));composite=bg.copy();m=fg[...,3]>0;composite[m]=fg[m]
for n,im in [('background',bg),('foreground',fg),('removed-tree-mask',np.where(removed,255,0).astype(np.uint8)),('target',composite)]:Image.fromarray(im).save(D/(n+'.png'))
Image.fromarray(np.where(cap_mask,255,0).astype(np.uint8)).save(D/'bevel-mask.png');np.save(D/'levels.npy',levels);np.save(D/'structure.npy',structure)
report=dict(baseline_engine='6e4d438b705604ca6e2cfc5fb5172377afa52d8e',mountain_native_reference='214e38cfb94309965e0cc58d09460e58737e00a6',shared_source=prov['commit'],tree_free_review=True,removed_large_trees=len(positions),removed_apricorn_trees=2,profiles=profiles,placements=placements,changed_cells=int(cells.sum()),hidden_backing_quadrants=hidden,collision_changes=[],behavior_changes=0,level_semantics='Visual design levels, not GBA elevation bits. 24px rise =8px local bevel (shared stone ramp) +16px unmodified complete face.',occluded_interpretation='SE level1 footing behind original foliage uses the same 24px rise as other level1 faces.',installed=a.install)
if a.install:
 glyphs=[np.array(v,np.uint8).reshape(8,8) for v in t.tiles[0]+t.tiles[1]];blocks=[list(v) for v in t.blocks[0]];attrs=list(t.attrs[0]);oa=attrs.copy();used={0}
 for y,x in np.argwhere(~cells):used.update(int(v)&1023 for v in entries[y,x])
 # Border tree art is removed too. Replace it with the closed native lawn course.
 border=np.fromfile(G/'data/layouts/JohtoRoute33/border.bin','<u2');lookup={}
 def keys(im,tid):
  for h in range(2):
   for v in range(2):lookup.setdefault(((im[::-1] if v else im)[:,::-1] if h else (im[::-1] if v else im)).tobytes(),tid|h<<10|v<<11)
 for tid in used:keys(glyphs[tid],tid)
 free=[i for i in range(1,1008) if i not in used];allocated=[]
 def ent(im,b):
  idx=np.zeros((8,8),np.uint8)
  for i,c in enumerate(pals[b][1:],1):idx[np.all(im[...,:3]==c,2)&(im[...,3]>0)]=i
  assert np.all(idx[im[...,3]>0]>0)
  if not idx.any():return 0
  k=idx.tobytes()
  if k not in lookup:
   assert free,'Native tile budget';tid=free.pop(0);allocated.append(tid)
   while tid>=len(glyphs):glyphs.append(np.zeros((8,8),np.uint8))
   glyphs[tid]=idx;keys(idx,tid)
  return lookup[k]|b<<12
 mids=set(map(int,(grid&1023)[~cells]));fm=[i for i in range(len(blocks)) if i not in mids];ml={tuple(blocks[i])+(attrs[i],):i for i in mids}
 def block(es,attr):
  k=tuple(es)+(attr,)
  if k not in ml:
   i=fm.pop(0) if fm else len(blocks)
   if i==len(blocks):blocks.append(es);attrs.append(attr)
   else:blocks[i]=es;attrs[i]=attr
   ml[k]=i
  return ml[k]
 for y,x in np.argwhere(cells):
  es=[]
  for l,im in enumerate([bg,fg]):
   for q in range(4):
    yy=y*16+q//2*8;xx=x*16+q%2*8;es.append(ent(im[yy:yy+8,xx:xx+8],int(banks[l,yy//8,xx//8])))
  grid[y,x]=(grid[y,x]&0xfc00)|block(es,oa[int(original_grid[y,x]&1023)])
 lawn=old[0,224:240,320:336];bes=[ent(lawn[q//2*8:q//2*8+8,q%2*8:q%2*8+8],0) for q in range(4)]+[0]*4;bid=block(bes,0x1000);border[:]=(border&0xfc00)|bid;assert len(blocks)<1024
 for part in range(2):
  folder=G/f'data/tilesets/{"secondary" if part else "primary"}/route33';sheet=np.zeros((256 if part==0 else 248,128),np.uint8)
  for i in range(512 if not part else 496):
   if i+part*512<len(glyphs):sheet[i//16*8:i//16*8+8,i%16*8:i%16*8+8]=glyphs[i+part*512]
  im=Image.fromarray(sheet,'P');im.putpalette([v for i in range(256) for v in (i*17%256,)*3]);im.save(folder/'tiles.png',bits=4)
  bs=blocks[part*512:(part+1)*512] or [[0]*8];aa=attrs[part*512:(part+1)*512] or [0];(folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*v) for v in bs));(folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(aa),*aa))
  for b in [3,10]:(folder/'palettes'/f'{b:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pals[b])+'\n')
 grid.tofile(G/'data/layouts/JohtoRoute33/map.bin');border.tofile(G/'data/layouts/JohtoRoute33/border.bin');test=Tileset(G,'route33','route33').map_image(grid.ravel().tolist(),34);assert np.array_equal(np.array(test),composite[...,:3]);test.save(E/'native-map.png');np.save(S/'solid.npy',(grid&0xc00)!=0);report.update(glyph_max=max(used|set(allocated)),allocated_glyphs=len(allocated),metatiles=len(blocks))
(E/'terrain-depth.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k not in ['profiles','placements']})
