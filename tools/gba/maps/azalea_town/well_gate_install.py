"""Guarded individual native house repair. Never regenerates town layout."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'));from tiles import Tileset
G=Path(sys.argv[1]);S=ROOT/'gba/art/azalea-town/source';E=S.parent/'evidence';D=S/'well-gate-repair';D.mkdir(exist_ok=True)
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
t,grid,old,entries=decode(G);original_grid=grid.copy();layers=np.stack([np.array(Image.open(D/'target-background.png').convert('RGBA')),np.array(Image.open(D/'target-foreground.png').convert('RGBA'))]);bg,fg=layers
pals={i:np.array(t.pals[int(i>=6)][i],np.uint8) for i in range(16)};sets={i:set(map(tuple,pals[i][1:])) for i in range(13)}
r=json.loads((D/'assembly-before.json').read_text());geo=json.loads((D/'geometry.json').read_text());solid=np.load(D/'solid-before.npy');oldsolid=solid.copy();beh=np.load(D/'behaviors-before.npy');oldbeh=beh.copy();mat=np.load(D/'material-before.npy');roles=np.load(D/'terrain-roles.npy');desired_attrs=np.zeros(grid.shape,np.uint16)
for y,x in np.ndindex(grid.shape):mid=int(grid[y,x]&1023);desired_attrs[y,x]=t.attrs[int(mid>=512)][mid%512]
original_attrs_grid=desired_attrs.copy()
# Remove only superseded well wall occupancy, not buildings/props or other rocks.
for p in r['rock_placements']:
 if p['x']>=42 and p['y']<=18:solid[p['y'],p['x']]=False;mat[p['y'],p['x']]='.'
for y,x in np.ndindex(grid.shape):
 if np.any(roles[y*16:y*16+16,x*16:x*16+16]):solid[y,x]=True;mat[y,x]='R';desired_attrs[y,x]=0x1000
# Explicit tread axes and complete landings; side-stair shoulders stay solid.
solid[10,44]=False;mat[10,44]='S';desired_attrs[10,44]=0x1000
for x in [48,49]:solid[16,x]=False;mat[16,x]='S';desired_attrs[16,x]=0x1000
for x in range(50,54):solid[17,x]=True;beh[17,x]=59;mat[17,x]='L';desired_attrs[17,x]=0x1000|59
# Preserve root footprints; add complete, aligned trees behind the gate roof.
roots=np.load(D/'roots-before.npy')
for p in geo['new_trees']:
 x,y=p['x']//16,p['y']//16;assert not roots[y+1:y+3,x:x+2].any();roots[y+1:y+3,x:x+2]+=1;solid[y+1:y+3,x:x+2]=True;mat[y+1:y+3,x:x+2]='T'
solid[roots>0]=True
# The actual visible gate facade begins one row above its old collision mask.
solid[17,1:8]=True;mat[17,1:8]='B';desired_attrs[17,1:8]=0x1000
solid[19:21,7]=True;mat[19:21,7]='O';desired_attrs[19:21,7]=0x1000
assert solid[:,7].all() and not solid[18,8],(np.where(~solid[:,7])[0].tolist(),bool(solid[18,8]))
# A local exact two-layer encoding handles overlapping approved foreground
# objects without painting their former grass masks onto the new rock plane.
layer_changes=[]
for yy in range(0,528,8):
 for xx in range(0,1024,8):
  f=fg[yy:yy+8,xx:xx+8];b=bg[yy:yy+8,xx:xx+8];fc=set(map(tuple,f[f[...,3]>0,:3]));bc=set(map(tuple,b[b[...,3]>0,:3]))
  if any(fc<=v for v in sets.values()) and any(bc<=v for v in sets.values()):continue
  visible=set(map(tuple,b[(f[...,3]==0)&(b[...,3]>0),:3]));options=[]
  for base in range(13):
   if not visible<=sets[base]:continue
   for top in range(13):
    if not fc<=sets[base]|sets[top]:continue
    move=(f[...,3]>0)&~np.array([[tuple(c) in sets[top] for c in row] for row in f[...,:3]])
    options.append((int(move.sum()),base,top,move))
  if not options:
   # A partial-height face can share a quadrant with ordinary lawn. Preserve
   # exact RGB by factoring that mixed terrain into the same two hardware layers.
   comp=b.copy();opaque=f[...,3]>0;comp[opaque]=f[opaque];cs=set(map(tuple,comp[comp[...,3]>0,:3]));fallback=[]
   for base in range(13):
    for top in range(13):
     if not cs<=sets[base]|sets[top]:continue
     isbase=np.array([[tuple(c) in sets[base] for c in row] for row in comp[...,:3]]);istop=np.array([[tuple(c) in sets[top] for c in row] for row in comp[...,:3]]);upper=(~isbase|(opaque&istop))&(comp[...,3]>0);cost=int(np.count_nonzero(upper!=opaque));fallback.append((cost,base,top,upper))
   assert fallback,('Unencodable layer overlap',xx,yy,fc,bc)
   _,base,top,upper=min(fallback,key=lambda o:(o[0],o[1],o[2]));b[:]=comp;f[:]=0;f[upper]=comp[upper];b[upper]=[*pals[base][1],255];layer_changes.append(dict(x=xx,y=yy,base_palette=base,upper_palette=top,method='Exact mixed terrain split'));continue
  _,base,top,move=min(options,key=lambda o:(o[0],o[1],o[2]));b[move]=f[move];f[move]=0
  hidden=f[...,3]>0
  for ly,lx in np.argwhere(hidden):
   if tuple(b[ly,lx,:3]) not in sets[base]:b[ly,lx]=[*pals[base][1],255]
  assert set(map(tuple,b[b[...,3]>0,:3]))<=sets[base];layer_changes.append(dict(x=xx,y=yy,base_palette=base,upper_palette=top,foreground_pixels_in_lower_layer=int(move.sum())))
# All decoded behavior and elevation changes are explicit; no extra warps/doors.
for y,x in np.ndindex(grid.shape):desired_attrs[y,x]=(desired_attrs[y,x]&0xff00)|beh[y,x]
grid=(grid&0xf3ff)|(solid.astype(np.uint16)*0xc00)
changed=np.any(layers!=old,(0,3));cells=changed.reshape(33,16,64,16).any((1,3))|(solid!=oldsolid)|(beh!=oldbeh)|(desired_attrs!=original_attrs_grid)
composite=bg.copy();m=fg[...,3]>0;composite[m]=fg[m]
allowed=np.zeros((528,1024),bool);allowed[96:304,640:880]=True;allowed[192:352,0:144]=True;assert not changed[~allowed].any()
if True:
 glyphs=[np.array(v,np.uint8).reshape(8,8) for v in t.tiles[0]+t.tiles[1]];blocks=[list(v) for v in t.blocks[0]];attrs=list(t.attrs[0]);original_attrs=list(attrs);used={0};border=np.fromfile(G/'data/layouts/JohtoAzaleaTown/border.bin','<u2')
 for y,x in np.argwhere(~cells):used.update(int(v)&1023 for v in entries[y,x])
 for mid in border&1023:used.update(int(v)&1023 for v in t.blocks[int(mid>=512)][int(mid)%512])
 lookup={}
 def keys(im,tid):
  for h in range(2):
   for v in range(2):lookup.setdefault(((im[::-1] if v else im)[:,::-1] if h else (im[::-1] if v else im)).tobytes(),tid|h<<10|v<<11)
 for tid in sorted(used):keys(glyphs[tid],tid)
 # Azalea has two static NULL-callback tilesets; no animation reserve is active.
 # The engine loads all 1024 tile slots (512+512), so the top 16 are valid here.
 headers=(G/'src/data/tilesets/headers.h').read_text();assert all('.callback = NULL' in next(v for v in headers.splitlines() if 'const struct Tileset '+n+' =' in v) for n in ['gTileset_AzaleaPrimary','gTileset_Azalea'])
 assert '#define NUM_TILES_TOTAL 1024' in (G/'include/fieldmap.h').read_text()
 # Door animations also use the top 16 slots. This exterior has no doors or
 # events; repack below 1008 before wiring animated building interiors.
 mapmeta=json.loads((G/'data/maps/JohtoAzaleaTown/map.json').read_text());assert not any(mapmeta.get(k) for k in ['warp_events','object_events','coord_events','bg_events'])
 free=[i for i in range(1,1024) if i not in used];allocated=[]
 bankids={b:{0} for b in range(13)}
 for y,x in np.ndindex(grid.shape):
  for e in entries[y,x]:
   if int(e)>>12<13:bankids[int(e)>>12].add(int(e)&1023)
 hidden_reuse=[]
 def ent(im,pref,visible=None):
  if visible is not None and not visible.all():
   cs=set(map(tuple,im[visible&(im[...,3]>0),:3]))
   for b in list(dict.fromkeys([pref]+list(range(13)))):
    if b>=13 or not cs<=set(map(tuple,pals[b][1:])):continue
    target=np.zeros((8,8),np.uint8)
    for i,c in enumerate(pals[b][1:],1):target[np.all(im[...,:3]==c,2)&(im[...,3]>0)]=i
    for tid in sorted(bankids[b]&set(used|set(allocated))):
     tile=glyphs[tid]
     for h in range(2):
      for v in range(2):
       candidate=(tile[::-1] if v else tile)[:,::-1] if h else (tile[::-1] if v else tile)
       if not np.array_equal(candidate[visible],target[visible]):continue
       replacement=np.zeros((8,8,4),np.uint8);m=candidate>0;replacement[m,:3]=pals[b][candidate[m]];replacement[m,3]=255
       if np.any(replacement[~visible]!=im[~visible]):hidden_reuse.append(dict(x=int(xx),y=int(yy),palette=b,tile=tid))
       im[:]=replacement;return tid|h<<10|v<<11|b<<12

  cs=set(map(tuple,im[im[...,3]>0,:3]));bs=[b for b in [pref,2,12]+list(range(13)) if cs<=set(map(tuple,pals[b][1:]))];assert bs,(y,x,l,q,cs);b=bs[0];idx=np.zeros((8,8),np.uint8)
  for i,c in enumerate(pals[b][1:],1):idx[np.all(im[...,:3]==c,2)&(im[...,3]>0)]=i
  if not idx.any():return 0
  k=idx.tobytes()
  if k not in lookup:
   assert free,'Native tile budget';tid=free.pop(0);allocated.append(tid)
   while tid>=len(glyphs):glyphs.append(np.zeros((8,8),np.uint8))
   glyphs[tid]=idx;keys(idx,tid)
  result=lookup[k]|b<<12;bankids[b].add(result&1023);return result
 mids=set(map(int,(grid&1023)[~cells]))|set(map(int,border&1023));fm=[i for i in range(len(blocks)) if i not in mids];ml={tuple(blocks[i])+(attrs[i],):i for i in mids};og=grid.copy()
 for y,x in np.argwhere(cells):
  es=[]
  for l in range(2):
   for q in range(4):
    yy=y*16+q//2*8;xx=x*16+q%2*8;es.append(ent(layers[l,yy:yy+8,xx:xx+8],int(entries[y,x,l*4+q])>>12,(fg[yy:yy+8,xx:xx+8,3]==0) if l==0 else None))
  attr=int(desired_attrs[y,x]);k=tuple(es)+(attr,)
  if k not in ml:
   i=fm.pop(0) if fm else len(blocks)
   if i==len(blocks):blocks.append(es);attrs.append(attr)
   else:blocks[i]=es;attrs[i]=attr
   ml[k]=i
  grid[y,x]=(grid[y,x]&0xfc00)|ml[k]
 assert max(used|set(allocated))<1024
 for part in range(2):
  folder=G/f'data/tilesets/{"secondary" if part else "primary"}/azalea';sheet=np.zeros((256 if part==0 else max(8,((len(glyphs)-512+15)//16)*8),128),np.uint8)
  for i in range(512 if not part else (sheet.shape[0]//8)*16):
   if i+part*512<len(glyphs):sheet[i//16*8:i//16*8+8,i%16*8:i%16*8+8]=glyphs[i+part*512]
  im=Image.fromarray(sheet,'P');im.putpalette([v for i in range(256) for v in (i*17%256,)*3]);im.save(folder/'tiles.png',bits=4)
  bs=blocks[part*512:(part+1)*512] or [[0]*8];aa=attrs[part*512:(part+1)*512] or [0];(folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*v) for v in bs));(folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(aa),*aa));(folder/'palettes/02.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in pals[2])+'\n')
 grid.tofile(G/'data/layouts/JohtoAzaleaTown/map.bin');actual=Tileset(G,'azalea','azalea').map_image(grid.ravel().tolist(),64);assert np.array_equal(np.array(actual),composite[...,:3])

Image.fromarray(bg).save(S/'background.png');Image.fromarray(fg).save(S/'foreground.png');np.save(S/'solid.npy',solid);np.save(S/'behaviors.npy',beh);np.save(S/'material-grid.npy',mat);np.save(S/'tree-footprints.npy',roots);(S/'blocks.txt').write_text('\n'.join(''.join(v) for v in mat)+'\n')
for n in ['R01','R02','R05','R06','R15','R16','S01','S03','S04']:Image.open(D/(n+'-native.png')).save(S/'masters'/('well-'+n+'.png'))
Image.open(D/'P04-native.png').save(S/'masters/gate-P04.png')
# Record shared whole modules separately from receiving-height contour segments.
r['rock_placements']=[p for p in r['rock_placements'] if not(p['x']>=42 and p['y']<=18)]+geo['whole_tiles']
props=r['placements'];idx=next(i for i,p in enumerate(props) if p['name']!='tree');props=geo['rail_props']+props[:idx]+geo['new_trees']+props[idx:]+geo['new_props'];r['placements']=props
r['trees'] += [[p['x']//16,p['y']//16] for p in geo['new_trees']];r['tree_count']=len(r['trees']);r['glyphs']=max(used|set(allocated))+1;r['metatiles']=len(blocks);r['well_geometry']='source/well-gate-repair/geometry.json'
(E/'assembly.json').write_text(json.dumps(r,indent=2)+'\n')
rep=dict(baseline='38200410b559a842e4b4c7ef17e5dc8e77164f9a',shared_source_commit=geo['shared_commit'],changed_cells=int(cells.sum()),collision_cells_changed=int(np.count_nonzero(solid!=oldsolid)),behavior_cells_changed=int(np.count_nonzero(beh!=oldbeh)),added_full_trees=len(geo['new_trees']),gate_north_bypass_closed=True,gate_south_bypass_closed=True,gate_approach=[8,18],stair_landings={'west':[43,10],'east':[45,10],'south_foot':[49,17],'south_head':[49,16]},native_layer_repairs=layer_changes,occluded_background_reuse=hidden_reuse,tile_capacity=1024,static_tileset_callbacks='Both NULL; no tileset animation writes',door_animation_limit='Top 16 slots are used by static art; no door/events/warps exist. Repack below 1008 before adding animated doors.',glyphs=r['glyphs'],metatiles=r['metatiles'],palette_changes=0,owner_visual_acceptance='pending',limits='Exterior only; gate and well interiors remain closed. Source overview trace and native adaptations, not decoded DS collision.')
(E/'well-gate-repair.json').write_text(json.dumps(rep,indent=2)+'\n');print(json.dumps(rep,indent=2))
