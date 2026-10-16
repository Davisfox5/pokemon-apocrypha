"""Read-only native Emerald/FireRed metatile and map decoder."""
from pathlib import Path
import numpy as np,json,struct
from PIL import Image
class Native:
 def __init__(self,game,layout):
  self.game=game;self.split=640 if game.name=='pokefirered' else 512;self.palsplit=7 if self.split==640 else 6
  self.tiles=[];self.blocks=[];self.pals=[];self.paths=[]
  for kind in ['primary','secondary']:
   symbol=layout[kind+'_tileset'].removeprefix('gTileset_').lower();folder=next(p for p in (game/'data/tilesets'/kind).iterdir() if p.name.replace('_','').lower()==symbol.removesuffix('primary'))
   self.paths.append(str(folder.relative_to(game)));im=Image.open(folder/'tiles.png');self.tiles.append([np.array(im.crop((x,y,x+8,y+8))) for y in range(0,im.height,8) for x in range(0,im.width,8)])
   self.blocks.append(list(struct.iter_unpack('<8H',(folder/'metatiles.bin').read_bytes())))
   self.pals.append([np.array([list(map(int,l.split())) for l in (folder/'palettes'/f'{i:02d}.pal').read_text().splitlines()[3:19]],dtype=np.uint8) for i in range(16)])
 def tile(self,mid):
  out=np.zeros((16,16,3),np.uint8)
  for q,e in enumerate(self.blocks[mid>=self.split][mid-self.split if mid>=self.split else mid]):
   tid=e&1023;b=e>>12;tile=self.tiles[tid>=self.split][tid-self.split if tid>=self.split else tid].copy()
   if e&1024:tile=tile[:,::-1]
   if e&2048:tile=tile[::-1]
   dest=out[q%4//2*8:q%4//2*8+8,q%2*8:q%2*8+8];mask=tile!=0;dest[mask]=self.pals[b>=self.palsplit][b][tile[mask]]
  return out
 def map(self,l):
  grid=np.fromfile(self.game/l['blockdata_filepath'],dtype='<u2').reshape(l['height'],l['width'])&1023;cache={int(i):self.tile(int(i)) for i in np.unique(grid)}
  out=np.zeros((l['height']*16,l['width']*16,3),np.uint8)
  for y,x in np.ndindex(grid.shape):out[y*16:y*16+16,x*16:x*16+16]=cache[int(grid[y,x])]
  return Image.fromarray(out)
