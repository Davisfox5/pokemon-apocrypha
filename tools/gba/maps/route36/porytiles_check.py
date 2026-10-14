"""Compile the exact reused grass family with Porytiles and compare every pixel."""
from pathlib import Path
import json,struct,subprocess,sys
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent))
from tiles import palette
OUT=ROOT/'gba/art/route36';S=OUT/'source';src=S/'porytiles-grass';dest=S/'porytiles-compiled';src.mkdir(exist_ok=True)
names=[f'grass-{i:04b}' for i in range(16)];atlas=[Image.open(S/'materials'/(n+'.png')).convert('RGBA') for n in names]
bottom=Image.new('RGBA',(128,32));middle=bottom.copy()
for i,im in enumerate(atlas):middle.paste(im,(i%8*16,i//8*16))
for n,im in [('bottom',bottom),('middle',middle),('top',bottom)]:im.save(src/(n+'.png'))
subprocess.run(['porytiles-legacy','compile-primary','-dual-layer','-o',str(dest),str(src),str(Path(sys.argv[1])/'include/constants/metatile_behaviors.h')],check=True)
for p in (dest/'palettes').glob('*.pal'):p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
sheet=np.array(Image.open(dest/'tiles.png'));tiles=[sheet[y:y+8,x:x+8] for y in range(0,sheet.shape[0],8) for x in range(0,128,8)];blocks=list(struct.iter_unpack('<8H',(dest/'metatiles.bin').read_bytes()));pals={int(p.stem):np.array(palette(p)) for p in (dest/'palettes').glob('*.pal')}
for i,expected in enumerate(atlas):
 out=np.zeros((16,16,4),np.uint8)
 for layer in range(2):
  for q in range(4):
   en=blocks[i][layer*4+q];a=tiles[en&1023].copy()
   if en&1024:a=a[:,::-1]
   if en&2048:a=a[::-1]
   part=out[q//2*8:q//2*8+8,q%2*8:q%2*8+8];m=a>0;part[m,:3]=pals[en>>12][a[m]];part[m,3]=255
 assert np.array_equal(out,np.array(expected)),names[i]
(OUT/'evidence/porytiles.json').write_text(json.dumps({'version':'2.0.0 legacy','grass_variants':16,'RGB_alpha_errors':0,'use':'Asset compiler round trip; final native layout packed with established two-layer map assembler'},indent=2)+'\n')
print('16 grass variants: exact RGBA equality')
