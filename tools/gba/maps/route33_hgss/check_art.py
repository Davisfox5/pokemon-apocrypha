"""Independent Porytiles round-trip of representative cave material metatiles."""
from pathlib import Path
import sys,subprocess,json,struct
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent));from tiles import Tileset
G=Path(sys.argv[1]);binary=Path(sys.argv[2]);c={'set':'route33','name':'JohtoRoute33'};S=ROOT/'gba/art/route33-hgss/source';E=S.parent/'evidence';t=Tileset(G,c['set'],c['set']);grid=np.fromfile(G/'data/layouts'/c['name']/'map.bin','<u2');mids=sorted(set(map(int,grid&1023)));selected=[mids[int(i)] for i in np.linspace(0,len(mids)-1,128)];sheet=Image.new('RGBA',(128,256))
layers=[np.zeros((256,128,4),np.uint8),np.zeros((256,128,4),np.uint8)]
for i,mid in enumerate(selected):
 block=t.blocks[int(mid>=512)][mid-512 if mid>=512 else mid]
 for layer in range(2):
  for q in range(4):
   en=block[layer*4+q];tid=en&1023;p=np.array(t.tiles[int(tid>=512)][tid-512 if tid>=512 else tid],np.uint8).reshape(8,8)
   if en&1024:p=p[:,::-1]
   if en&2048:p=p[::-1]
   x,y=i%8*16+q%2*8,i//8*16+q//2*8;dst=layers[layer][y:y+8,x:x+8];mask=p>0;colors=np.array(t.pals[int((en>>12)>=6)][en>>12],np.uint8);dst[mask,:3]=colors[p[mask]];dst[mask,3]=255
 sheet.paste(t.render(mid).convert('RGBA'),(i%8*16,i//8*16))
input=S/'porytiles-input';output=S/'porytiles-output';input.mkdir(exist_ok=True);blank=Image.new('RGBA',sheet.size);blank.save(input/'bottom.png');Image.fromarray(layers[0]).save(input/'middle.png');Image.fromarray(layers[1]).save(input/'top.png')
p=subprocess.run([str(binary),'compile-primary','-dual-layer','-pals-primary-override=13','-o',str(output),str(input),str(G/'include/constants/metatile_behaviors.h')],capture_output=True,text=True);(E/'porytiles.log').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr
im=np.array(Image.open(output/'tiles.png'));tiles=[im[y:y+8,x:x+8] for y in range(0,im.shape[0],8) for x in range(0,im.shape[1],8)];blocks=list(struct.iter_unpack('<8H',(output/'metatiles.bin').read_bytes()));pals={int(p.stem):np.array([list(map(int,l.split())) for l in p.read_text().splitlines()[3:19]],np.uint8) for p in (output/'palettes').glob('*.pal')};decoded=np.zeros((256,128,4),np.uint8)
for i,block in enumerate(blocks):
 for layer in range(2):
  for q in range(4):
   en=block[layer*4+q];p=tiles[en&1023].copy()
   if en&1024:p=p[:,::-1]
   if en&2048:p=p[::-1]
   x,y=i%8*16+q%2*8,i//8*16+q//2*8;piece=decoded[y:y+8,x:x+8];mask=p>0;piece[mask,:3]=pals[en>>12][p[mask]];piece[mask,3]=255
expected=np.array(sheet);mask=expected[...,3]>0;errors=int(np.any((decoded[...,:3]&248)!=(expected[...,:3]&248),2)[mask].sum());alpha=int((decoded[...,3]!=expected[...,3]).sum());assert errors==alpha==0,(errors,alpha)
(E/'porytiles.json').write_text(json.dumps({'version':'legacy 2.0.0','representative_material_metatiles':128,'native_RGB_errors':errors,'alpha_errors':alpha,'scope':'standalone validation only; does not repack engine tilesets','selected_native_metatiles':selected},indent=2)+'\n');print('Porytiles native RGB/alpha round-trip passed')
