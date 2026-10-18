"""Lossless packing for a dedicated outdoor tileset; pins animated glyphs/labels."""
import inspect,struct,json
import numpy as np
from PIL import Image
from violet_city.packing import Probe
from violet_city import packing
from tiles import Tileset
from johto_service_buildings.build import decode
from route36.gate_surround.build import over

def pack(game,c,t,grid,attrs,layers,target,changed):
 layouts=json.loads((game/'data/layouts/layouts.json').read_text())['layouts'];uses=[v for v in layouts if v['primary_tileset']==c['layout']['primary_tileset']];assert len(uses)==1,'Dedicated map only'
 border=np.fromfile(game/c['layout']['border_filepath'],'<u2');bl,_,_,ba=decode(t,border.reshape(2,2));border_rgb=bl[0].copy();over(border_rgb,bl[1]);oldgrid=grid.copy();pals=[list(t.pals[i>=6][i]) for i in range(13)];probe=Probe();records=[];changed_cells=changed.reshape(grid.shape[0],16,grid.shape[1],16).any((1,3))
 def records_for(lays,words,attributes):
  rec=[]
  for y,x in np.ndindex(words.shape):
   mid=int(words[y,x]&1023);entries=[]
   for li in range(2):
    for q in range(4):
     a=lays[li][y*16+q//2*8:y*16+q//2*8+8,x*16+q%2*8:x*16+q%2*8+8];mask=a[:,:,3]>0;cs=set(map(tuple,a[mask,:3]));oe=t.blocks[mid>=512][mid%512][li*4+q];pref=oe>>12;bank=next(b for b in [pref]+list(range(13)) if cs<=set(pals[b][1:]));ix=np.zeros((8,8),np.uint8)
     for i,col in enumerate(pals[bank][1:],1):ix[mask&np.all(a[:,:,:3]==col,2)]=i
     # Unchanged animated tiles keep their original source entry and palette.
     orig=np.array(t.tiles[(oe&1023)>=512][(oe&1023)%512],np.uint8).reshape(8,8)
     if oe&1024:orig=orig[:,::-1]
     if oe&2048:orig=orig[::-1]
     pinned=(oe&1023)<93 and bank==pref and np.array_equal(ix,orig)
     probe.tile(bank,ix);entries.append([bank,ix,oe if pinned else None])
   rec.append([entries,int(attributes[y,x]),mid])
  return rec
 main=records_for(layers,grid,attrs);br=records_for(bl,border.reshape(2,2),ba)
 # Correct local-variable shadowing in the existing optimizer without altering it.
 source=inspect.getsource(packing.optimize).replace('fixed=dict(zip','labels_fixed=dict(zip').replace('fixed[0]=0','labels_fixed[0]=0').replace('fixed.values()','labels_fixed.values()').replace('fixed.items()','labels_fixed.items()').replace('source in fixed:','source in labels_fixed:');ns={'np':np};exec(source,ns)
 lut,stats=ns['optimize'](probe,fixed=(0,1,6,7,8,9,11));print('Lossless packing',c['map'],stats['unique_tiles_before'],stats['unique_tiles_after'],flush=True)
 for bank,perm in lut.items():
  old=pals[bank];new=list(old)
  for i in range(16):new[int(perm[i])]=old[i]
  pals[bank]=new
 raw=[np.array(v,np.uint8).reshape(8,8) for v in t.tiles[0]+t.tiles[1]];raw+= [np.zeros((8,8),np.uint8) for _ in range(1008-len(raw))];cache={};used=set(range(93));free=list(range(93,1008))
 def addkey(a,i):
  for ar,bits in [(a,0),(a[:,::-1],1024),(a[::-1],2048),(a[::-1,::-1],3072)]:cache.setdefault(ar.tobytes(),i|bits)
 # Static source data must not reuse animated nonzero glyphs even when identical.
 addkey(raw[0],0)
 def entry(r):
  bank,ix,pinned=r
  if pinned is not None:return pinned
  ix=lut.get(bank,np.arange(16,dtype=np.uint8))[ix];key=ix.tobytes()
  if key not in cache:
   assert free,('Dedicated graphics capacity',c['map'],stats)
   i=free.pop(0);used.add(i);raw[i]=ix;addkey(ix,i)
  return cache[key]|bank<<12
 blocks=[list(v) for v in t.blocks[0]+t.blocks[1]];ats=list(t.attrs[0]+t.attrs[1]);blocks+= [[0]*8 for _ in range(1024-len(blocks))];ats += [0]*(1024-len(ats))
 active=set(map(int,(grid&1023)[~changed_cells]))|set(map(int,border&1023));free_mids=[i for i in range(1024) if i not in active];cacheblocks={}
 # Keep unchanged metatile IDs, including every door and animated shoreline cell.
 for i,(es,at,mid) in enumerate(main+br):
  is_changed=i<len(main) and bool(changed_cells.ravel()[i])
  if is_changed:continue
  newes=list(map(entry,es));key=tuple(newes),at
  if mid in cacheblocks:assert cacheblocks[mid]==key
  cacheblocks[mid]=key;blocks[mid]=newes;ats[mid]=at
 bycontent={v:k for k,v in cacheblocks.items()}
 for i,(es,at,mid) in enumerate(main):
  if not changed_cells.ravel()[i]:continue
  key=tuple(map(entry,es)),at
  if key not in bycontent:
   assert free_mids,'Metatile capacity';nm=free_mids.pop(0);bycontent[key]=nm;blocks[nm]=list(key[0]);ats[nm]=at
  grid.ravel()[i]=(int(grid.ravel()[i])&0xfc00)|bycontent[key]
 # All capacity checks finish before file writes.
 for k,folder in enumerate(t.dirs):
  start=k*512;end=512 if k==0 else 1008;im=Image.new('P',(128,256 if k==0 else 248));im.putpalette(Image.open(folder/'tiles.png').getpalette())
  for i,ar in enumerate(raw[start:end]):im.paste(Image.fromarray(ar),(i%16*8,i//16*8))
  im.save(folder/'tiles.png',bits=4);(folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*v) for v in blocks[start:start+512]));(folder/'metatile_attributes.bin').write_bytes(struct.pack('<512H',*ats[start:start+512]))
  for bank in range(13):
   if (bank>=6)==bool(k):(folder/'palettes'/f'{bank:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,col)) for col in pals[bank])+'\n')
 grid.astype('<u2').tofile(game/c['layout']['blockdata_filepath'])
 check=Tileset(game,c['secondary'],c['primary']);out=np.array(check.map_image(grid.ravel().tolist(),grid.shape[1]));assert np.array_equal(out,target[:,:,:3]);ll,_,_,aa=decode(check,grid);assert np.array_equal(aa,attrs);assert np.array_equal(oldgrid&0xfc00,grid&0xfc00);assert np.array_equal(np.array(check.map_image(border.tolist(),2)),border_rgb[:,:,:3]);assert all(np.array_equal(raw[i],np.array(t.tiles[0][i]).reshape(8,8)) for i in range(93))
 return dict(changed_cells=int(changed_cells.sum()),native_pixel_errors=0,behavior_errors=0,collision_elevation_errors=0,free_graphic_slots=len(free),animated_glyphs_pinned=93,palette_optimization=stats)
