"""Compare literal HGSS ground crops with pixels recovered from native GBA tiles."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R/'tools/gba/maps'));from tiles import Tileset
A=R/'gba/art/cherrygrove-synthesis';G=R/'tools/vendor/gba/cherrygrove-synthesis-work';t=Tileset(G,'cherrygrove','cherrygrove')
lookup={}
for pool in range(2):
 for i,raw in enumerate(t.tiles[pool]):
  ar=np.array(raw,np.uint8).reshape(8,8)
  for flip,view in [(0,ar),(1,ar[:,::-1]),(2,ar[::-1]),(3,ar[::-1,::-1])]:lookup.setdefault(view.tobytes(),[pool*512+i,flip])
board=Image.new('RGB',(600,352),(28,34,37));d=ImageDraw.Draw(board);report=[]
for k,(name,bank) in enumerate([('grass',0),('path',0),('sand',1)]):
 source=Image.open(A/f'references/HGSS-direct/{name}-source.png').convert('RGB');rgb=np.array(source,int);pal=np.array(t.pals[bank>=6][bank],int);ids=(((rgb[...,None,:]-pal[1:])**2).sum(-1).argmin(-1)+1).astype(np.uint8)
 tiles=[];native=np.zeros_like(rgb,dtype=np.uint8)
 for y in range(0,ids.shape[0],8):
  for x in range(0,ids.shape[1],8):
   patch=ids[y:y+8,x:x+8];key=patch.tobytes();assert key in lookup,(name,x,y)
   tid,flip=lookup[key];ar=np.array(t.tiles[tid>=512][tid%512],np.uint8).reshape(8,8)
   if flip&1:ar=ar[:,::-1]
   if flip&2:ar=ar[::-1]
   native[y:y+8,x:x+8]=pal[ar];tiles.append([x,y,tid,flip])
 assert np.array_equal(native,pal[ids])
 x=k*200;d.text((x+8,6),name+' / HGSS source',fill='white');d.text((x+8,180),'Native GBA atlas pixels',fill='white')
 board.paste(source.resize((128,128),Image.Resampling.NEAREST),(x+8,28));board.paste(Image.fromarray(native).resize((128,128),Image.Resampling.NEAREST),(x+8,204))
 report.append(dict(material=name,palette_bank=bank,native_tiles=tiles,exact_after_palette_conversion=True))
board.save(A/'evidence/terrain-source-check.png');(A/'evidence/terrain-source-check.json').write_text(json.dumps(report,indent=2)+'\n');print('HGSS grass, path and sand crops verified against native atlas tiles.')
