"""Mirror new northern seam art into unused Route 31 storage.
Existing tile/metatile IDs and nonzero artwork are never replaced. Door slots
1008–1023 remain reserved. Cherrygrove's native approach is handled separately.
"""
import struct
import numpy as np
from claude_routes import build as packing,seams
from tiles import Tileset

def synchronize(game,base,grid,primary,packer,solid):
 t=Tileset(base,'route31','cherrygrove');ng,ns=seams.read_layout(game,'JohtoRoute31',63,30)
 nr=seams.reachable(ns,(38,29));nw,visible,_=seams.crossing_windows(ns,solid,28,30)
 visible|=seams.visible_across(nr,grid.shape,28,30)
 # Only padding slots unused by Route 31's entire actual layout qualify.
 used=set()
 for mid in np.unique(ng):
  for en in t.blocks[int(mid>=512)][int(mid)-512 if mid>=512 else int(mid)]:
   if en&1023>=512:used.add(en&1023)
 for border in [game/'data/layouts/JohtoRoute31/border.bin']:
  if border.exists():
   for word in np.fromfile(border,'<u2'):
    mid=int(word&1023)
    for en in t.blocks[int(mid>=512)][mid-512 if mid>=512 else mid]:
     if en&1023>=512:used.add(en&1023)
 free=[i for i in range(512,1008) if i not in used and (i-512>=len(t.tiles[1]) or not np.asarray(t.tiles[1][i-512]).any())]
 known={}
 for part in range(2):
  for i,pixels in enumerate(t.tiles[part]):
   tid=i+part*512
   if 1<=tid<=92:continue
   a=np.asarray(pixels,np.uint8).reshape(8,8)
   for hf in range(2):
    for vf in range(2):
     q=(a[::-1] if vf else a)[:,::-1] if hf else (a[::-1] if vf else a)
     known.setdefault(q.tobytes(),tid|(hf<<10)|(vf<<11))
 shared_tiles={};mapped={};common={};required=sorted(set(int(v&1023) for v in grid[visible] if v&1023>=512))
 for mid in required:
  entries,attr=packer.sec_blocks[mid];result=[]
  for en in entries:
   tid=en&1023
   if tid<512:result.append(en);continue
   raw=packer.sec_tiles[tid];key=raw.tobytes()
   if key not in mapped:
    found=known.get(key)
    # A slot used elsewhere by the new Route 30 cannot be overwritten.
    if found is not None and (found&1023)>=512:
     existing=packer.sec_tiles.get(found&1023)
     if existing is not None and not np.array_equal(existing,np.asarray(t.tiles[1][(found&1023)-512],np.uint8).reshape(8,8)):found=None
    if found is None:
     candidates=[i for i in free if i not in shared_tiles and (i not in packer.sec_tiles or np.array_equal(packer.sec_tiles[i],raw))]
     if not candidates:raise ValueError(('Northern shared tile storage exhausted','new tiles',len(shared_tiles),'unused padding',len(free)))
     found=candidates[0];shared_tiles[found]=raw.copy()
    mapped[key]=found
   result.append((en&0xf000)|((en&0x0c00)^mapped[key]))
  common[mid]=(tuple(result),attr)
 next_mid=max(512+len(t.blocks[1]),max(packer.sec_blocks,default=511)+1);shared_blocks={};relocated={}
 for mid,block in common.items():
  if mid-512<len(t.blocks[1]) and t.blocks[1][mid-512]==block[0] and t.attrs[1][mid-512]==block[1]:relocated[mid]=mid;continue
  assert next_mid<1024,'Northern shared metatile storage exhausted'
  relocated[mid]=next_mid;shared_blocks[next_mid]=block;next_mid+=1
 for mid,new in relocated.items():
  mask=visible&((grid&1023)==mid);grid[mask]=(grid[mask]&0xfc00)|new
 packer.sec_tiles.update(shared_tiles);packer.sec_blocks.update(shared_blocks)
 # Existing matching RG31 graphic IDs also need their immutable pixels in R30.
 for mid in relocated.values():
  entries=shared_blocks[mid][0] if mid in shared_blocks else t.blocks[1][mid-512]
  for en in entries:
   tid=en&1023
   if tid>=512 and tid not in packer.sec_tiles:packer.sec_tiles[tid]=np.asarray(t.tiles[1][tid-512],np.uint8).reshape(8,8)
 tiles=[np.asarray(a,np.uint8).reshape(8,8) for a in t.tiles[1]]
 if shared_tiles:
  tiles.extend([np.zeros((8,8),np.uint8) for _ in range(max(shared_tiles)-512+1-len(tiles))])
  for tid,a in shared_tiles.items():tiles[tid-512]=a
 blocks=list(t.blocks[1]);attrs=list(t.attrs[1])
 if shared_blocks:
  delta=max(shared_blocks)-512+1-len(blocks);blocks.extend([(0,)*8]*delta);attrs.extend([0]*delta)
  for mid,(entries,attr) in shared_blocks.items():blocks[mid-512]=entries;attrs[mid-512]=attr
 folder=game/'data/tilesets/secondary/route31';packing.write_tiles(folder/'tiles.png',tiles)
 (folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*b) for b in blocks));(folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(attrs),*attrs))
 return {'new_shared_tiles':len(shared_tiles),'reused_existing_tile_ids':len(mapped)-len(shared_tiles),'new_shared_metatiles':len(shared_blocks),'visible_route_cells':int(visible.sum()),'existing_nonzero_graphics_replaced':0,'existing_metatile_ids_changed':0,'door_slots_reserved':[1008,1023],'neighbor_layouts_changed':False}
