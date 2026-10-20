"""Guarded individual native house repair. Never regenerates town layout."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'));from tiles import Tileset
G=Path(sys.argv[1]);S=ROOT/'gba/art/azalea-town/source';E=S.parent/'evidence';D=S/'kurt-extension';D.mkdir(exist_ok=True)
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
t,grid,old,entries=decode(G);original_grid=grid.copy();layers=old.copy();bg,fg=layers
pals={i:np.array(t.pals[int(i>=6)][i],np.uint8) for i in range(16)}
r=json.loads((D/'assembly-before.json').read_text());owner=np.zeros((528,1024),np.uint16);treecanvas=np.zeros_like(fg);removed={(320,96),(304,128)}
solid=np.load(D/'solid-before.npy');mat=np.load(D/'material-before.npy');original_solid=solid.copy();desired_attrs=np.zeros((33,64),np.uint16)
for y,x in np.ndindex(grid.shape):mid=int(grid[y,x]&1023);desired_attrs[y,x]=t.attrs[int(mid>=512)][mid%512]
original_attrs_grid=desired_attrs.copy()
for i,p in enumerate(r['placements'],1):
 a=np.array(Image.open(S/'masters'/(p['name']+'.png')).convert('RGBA'));h,w=a.shape[:2];m=a[...,3]>0;owner[p['y']:p['y']+h,p['x']:p['x']+w][m]=i
 if p['name']=='tree' and (p['x'],p['y']) not in removed:treecanvas[p['y']:p['y']+h,p['x']:p['x']+w][m]=a[m]
for i,p in enumerate(r['placements'],1):
 if (p['name']=='tree' and (p['x'],p['y']) in removed) or p['name']=='logs':
  mask=owner==i;fg[mask]=treecanvas[mask]
for px,py in removed:
 x,y=px//16,py//16;solid[y+1:y+3,x:x+2]=False;mat[y+1:y+3,x:x+2]='.';desired_attrs[y+1:y+3,x:x+2]=0x1000
solid[9:11,18]=False;mat[9:11,18]='.'
# New objects are behind the original house, never stamped over its accepted pixels.
pid=next(i for i,p in enumerate(r['placements'],1) if p['name']=='kurt')
newprops=[dict(name='kurt-firewood',x=272,y=112,role='Owner proposal: large rear firewood stack'),dict(name='kurt-kiln',x=256,y=128,role='Owner proposal: attached masonry kiln and chimney')]
for p,filename in zip(newprops,['firewood-stack.png','kiln.png']):
 a=np.array(Image.open(D/filename).convert('RGBA'));h,w=a.shape[:2];Image.fromarray(a).save(S/'masters'/(p['name']+'.png'));x,y=p['x'],p['y'];m=(a[...,3]>0)&(owner[y:y+h,x:x+w]!=pid);fg[y:y+h,x:x+w][m]=a[m]
 for cy in range(y//16,(y+h+15)//16):
  for cx in range(x//16,(x+w+15)//16):
   cut=a[max(0,cy*16-y):min(h,cy*16+16-y),max(0,cx*16-x):min(w,cx*16+16-x)]
   if (cut[...,3]>0).any():mat[cy,cx]='O' if p['name']=='kurt-firewood' else 'B'
solid[7:9,17:21]=True;desired_attrs[7:9,17:21]=0x1000
solid[10:12,17:20]=True;desired_attrs[8:10,16:20]=0;desired_attrs[10:12,17:20]=0x1000
# A narrow, rounded branch from the original doorstep to the new side yard.
# Reuse the town's exact grass/path texture and edge palette, not a new ground family.
from scipy.ndimage import binary_dilation,binary_erosion
pm=Image.new('1',(1024,528));dd=ImageDraw.Draw(pm);dd.rounded_rectangle((232,194,333,206),radius=6,fill=1);dd.rounded_rectangle((322,150,334,206),radius=6,fill=1);pathmask=np.array(pm,dtype=bool)
pt=np.array(Image.open(S/'masters/path.png').convert('RGBA'));pt[...,:3]&=248;Y,X=np.indices(pathmask.shape);dirt=set(map(tuple,pt[...,:3].reshape(-1,3)));oldpath=np.zeros(pathmask.shape,bool)
for c in dirt:oldpath|=np.all(bg[...,:3]==c,2)
union=pathmask|oldpath;bg[pathmask]=pt[Y[pathmask]%pt.shape[0],X[pathmask]%pt.shape[1]]
zone=binary_dilation(pathmask);edge=binary_dilation(union)&~union&zone;inner=union&~binary_erosion(union)&zone;bg[edge,:3]=[88,176,136];bg[inner,:3]=[184,168,128]
for cy,cx in np.ndindex(grid.shape):
 if pathmask[cy*16:cy*16+16,cx*16:cx*16+16].mean()>.25 and not solid[cy,cx]:mat[cy,cx]='P'
# Keep native elevation and behavior stable; only the proposed occupied cells change.
grid=(grid&0xf3ff)|(solid.astype(np.uint16)*0xc00)
# Where the flue overlaps the tightly stacked rear logs, keep stone above
# timber in the two native hardware layers. The rest of the kiln is grid-aligned.
stone_mask=np.zeros((528,1024),bool);ka=np.array(Image.open(D/'kiln.png').convert('RGBA'));km=np.zeros(ka.shape[:2],bool)
for c in pals[12][1:]:km|=np.all(ka[...,:3]==c,2)&(ka[...,3]>0)
stone_mask[128:192,256:320]=km&(owner[128:192,256:320]!=pid)
for yy in range(128,192,8):
 for xx in range(280,320,8):
  f=fg[yy:yy+8,xx:xx+8];b=bg[yy:yy+8,xx:xx+8];cs=set(map(tuple,f[f[...,3]>0,:3]))
  if any(cs<=set(map(tuple,pals[k][1:])) for k in range(13)):continue
  stone=stone_mask[yy:yy+8,xx:xx+8];other=(f[...,3]>0)&~stone;b[other]=f[other];f[other]=0;b[stone]=[120,88,24,255]
changed=np.any(layers!=old,(0,3));cells=changed.reshape(33,16,64,16).any((1,3))|(solid!=original_solid)|(desired_attrs!=original_attrs_grid)
composite=bg.copy();m=fg[...,3]>0;composite[m]=fg[m]
outside=changed.copy();outside[96:209,192:353]=False;assert not outside.any()
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
  cs=set(map(tuple,im[im[...,3]>0,:3]));bs=[b for b in [pref,2,12]+list(range(13)) if cs<=set(map(tuple,pals[b][1:]))];assert bs,(y,x,l,q,cs);b=bs[0];idx=np.zeros((8,8),np.uint8)
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
  attr=int(desired_attrs[y,x]);k=tuple(es)+(attr,)
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
np.save(S/'solid.npy',solid);np.save(S/'material-grid.npy',mat);(S/'blocks.txt').write_text('\n'.join(''.join(v) for v in mat)+'\n')
# Update the editable placement and footprint ledger, preserving the original snapshot.
placements=[]
for p in r['placements']:
 if (p['name']=='tree' and (p['x'],p['y']) in removed) or p['name']=='logs':continue
 if p['name']=='kurt':placements.extend(newprops)
 placements.append(p)
r['placements']=placements;r['trees']=[v for v in r['trees'] if (v[0]*16,v[1]*16) not in removed];r['tree_count']=len(r['trees']);roots=np.zeros((33,64),np.uint8)
for x,y in r['trees']:roots[y+1:y+3,x:x+2]+=1
assert roots.max()==1 and np.all(solid[roots>0]);np.save(S/'tree-footprints.npy',roots)
r['glyphs']=max(used|set(allocated))+1;r['metatiles']=len(blocks);r['owner_adaptation']='Proposed ten-year Kurt property growth: attached kiln and chimney, tight end-on rear firewood stack, exactly two removed complete trees and connected side-yard path.'
(E/'assembly.json').write_text(json.dumps(r,indent=2)+'\n')
report=dict(baseline='d822306675e15abe67c85235d9faf8d6e676d449',design_status='Owner-authorized proposal; visual acceptance pending',removed_trees=[list(v) for v in sorted(removed)],new_objects=newprops,original_house_pixels_changed=0,changed_cells=int(cells.sum()),collision_cells_changed=int(np.count_nonzero(solid!=original_solid)),glyphs=r['glyphs'],metatiles=r['metatiles'],palette_changes=0,regular_house_changes=0,Route33_changes=0)
(E/'kurt-extension.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
