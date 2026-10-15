"""Compile review candidates into native tiles and verify every RGBA pixel."""
from pathlib import Path
import sys,json,struct,subprocess,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from tiles import palette
E=Path(sys.argv[2]) if len(sys.argv)>2 else ROOT/'gba/art/johto-common-review/gates/refinement-1';src=E/'porytiles-source';dst=E/'porytiles-compiled'
src.mkdir(exist_ok=True)
a=Image.open(E/'G01a.png').convert('RGBA');b=Image.open(E/'G02.png').convert('RGBA');items=[a,b,b.transpose(Image.Transpose.FLIP_LEFT_RIGHT)]
bottom=Image.new('RGBA',(128,384));middle=bottom.copy()
for i,im in enumerate(items):middle.paste(im,(0,i*128))
for name,im in [('bottom',bottom),('middle',middle),('top',bottom)]:im.save(src/(name+'.png'))
subprocess.run(['porytiles-legacy','compile-primary','-dual-layer','-o',str(dst),str(src),str(Path(sys.argv[1])/'include/constants/metatile_behaviors.h')],check=True)
sheet=np.asarray(Image.open(dst/'tiles.png'));tiles=[sheet[y:y+8,x:x+8] for y in range(0,sheet.shape[0],8) for x in range(0,sheet.shape[1],8)]
blocks=list(struct.iter_unpack('<8H',(dst/'metatiles.bin').read_bytes()));pals={int(p.stem):np.array(palette(p)) for p in (dst/'palettes').glob('*.pal')};decoded=np.zeros((384,128,4),np.uint8)
for i,entries in enumerate(blocks):
 x=i%8*16;y=i//8*16
 for layer in range(2):
  for q in range(4):
   en=entries[layer*4+q];ids=tiles[en&1023]
   if en&1024:ids=ids[:,::-1]
   if en&2048:ids=ids[::-1]
   part=decoded[y+q//2*8:y+q//2*8+8,x+q%2*8:x+q%2*8+8];m=ids>0;part[m,:3]=pals[en>>12][ids[m]];part[m,3]=255
assert np.array_equal(decoded,np.array(middle)),int(np.any(decoded!=np.array(middle),2).sum())
for p in (dst/'palettes').glob('*.pal'):p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
for i,(name,im) in enumerate(zip(['G01a','G02','G02-mirrored'],items)):Image.fromarray(decoded[i*128:i*128+im.height,:im.width]).save(E/(name+'-native.png'))
v=json.loads((E/'validation.json').read_text());v['native_compile']={'compiler':'Porytiles legacy','rgba_pixel_errors':0,'metatiles':len(blocks),'stored_tile_slots':len(tiles),'bank_ids':sorted(set(en>>12 for block in blocks for en in block if en&1023)),'mirrored_side_gate_verified':True,'game_maps_modified':False,'runtime_tested':False};(E/'validation.json').write_text(json.dumps(v,indent=2)+'\n');print(v['native_compile'])
