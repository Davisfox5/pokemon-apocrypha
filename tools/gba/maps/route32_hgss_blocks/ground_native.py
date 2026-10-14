"""Match HGSS ground boundaries to existing native Cherrygrove 8px tiles.
This reads the accepted tile library, never its map layout or placement.
"""
import numpy as np
from claude_cherrygrove import ground
from tiles import Tileset

def install(game,pals):
 t=Tileset(game,'cherrygrove','cherrygrove');ids=sorted({en&1023 for block in t.blocks[0] for en in block if en and en>>12==0 and 92<en&1023<512})
 candidates=[]
 for tid in ids:
  a=np.asarray(t.tiles[0][tid],np.uint8).reshape(8,8)
  if not a.all():continue
  for hf in range(2):
   for vf in range(2):candidates.append((a[::-1] if vf else a)[:,::-1] if hf else (a[::-1] if vf else a))
 unique={a.tobytes():a for a in candidates};arrays=np.array(list(unique.values()));pal=np.asarray(pals[0].gba(),int);colors=pal[arrays].astype(np.int32)
 source_paint=ground.paint;cache={}
 def paint(cells,wobble=True):
  image,mat=source_paint(cells,wobble=wobble);out=image.copy();h,w=image.shape[:2]
  for y in range(0,h,8):
   for x in range(0,w,8):
    wanted=image[y:y+8,x:x+8,:3];key=wanted.tobytes()
    if key not in cache:
     target=wanted.astype(np.int32);wanted_soil=(target[...,0]>target[...,1]+10)&(target[...,0]>140);candidate_soil=(colors[...,0]>colors[...,1]+10)&(colors[...,0]>140)
     error=((colors-target)**2).sum((1,2,3))+np.logical_xor(candidate_soil,wanted_soil).sum((1,2))*20000
     cache[key]=pal[arrays[int(error.argmin())]].astype(np.uint8)
    out[y:y+8,x:x+8,:3]=cache[key]
  return out,mat
 ground.paint=paint
 return {'native_ground_library':'primary/cherrygrove bank 0, existing opaque 8px tiles','candidate_variants':len(arrays),'layout_input':'independent HGSS survey only'}
