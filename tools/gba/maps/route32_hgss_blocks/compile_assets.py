"""Porytiles validation of the new local art and reused native grass; never repacks existing engine banks."""
from pathlib import Path
import sys,json,subprocess,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'gba/art/route32-hgss-blocks/source';E=S.parent/'evidence'
def main(game,binary):
 input=S/'porytiles-local-input';output=S/'porytiles-local-output';input.mkdir(exist_ok=True);sheet=Image.new('RGBA',(128,256));m=S/'refined-materials'
 sheet.paste(Image.open(m/'gate.png').convert('RGBA'),(0,0));sheet.paste(Image.open(m/'coastal-rock.png').convert('RGBA'),(96,64));sheet.paste(Image.open(m/'boards.png').convert('RGBA'),(0,112))
 for i in range(4):sheet.paste(Image.open(m/f'rail-{i}.png').convert('RGBA'),(96,i*16))
 for i,p in enumerate(sorted(m.glob('grass-*.png'))):sheet.paste(Image.open(p).convert('RGBA'),(i%8*16,160+i//8*16))
 sheet.paste(Image.open(m/'rock-top.png').convert('RGBA'),(0,208));sheet.paste(Image.open(m/'stairs-ns.png').convert('RGBA'),(48,208));sheet.paste(Image.open(m/'stairs-ew.png').convert('RGBA'),(96,192))
 blank=Image.new('RGBA',sheet.size);blank.save(input/'bottom.png');sheet.save(input/'middle.png');blank.save(input/'top.png')
 run=subprocess.run([str(binary),'compile-primary','-dual-layer','-o',str(output),str(input),str(game/'include/constants/metatile_behaviors.h')],capture_output=True,text=True);(E/'porytiles.log').write_text(run.stdout+run.stderr);assert run.returncode==0,run.stderr
 tiles=np.array(Image.open(output/'tiles.png'));tiles=[tiles[y:y+8,x:x+8] for y in range(0,tiles.shape[0],8) for x in range(0,tiles.shape[1],8)];blocks=list(struct.iter_unpack('<8H',(output/'metatiles.bin').read_bytes()));pal={int(p.stem):np.array([list(map(int,l.split())) for l in p.read_text().splitlines()[3:19]],np.uint8) for p in (output/'palettes').glob('*.pal')};decoded=np.zeros((256,128,4),np.uint8)
 for i,b in enumerate(blocks):
  bx,by=i%8*16,i//8*16
  for layer in range(2):
   for q in range(4):
    en=b[layer*4+q];px=tiles[en&1023].copy()
    if en&1024:px=px[:,::-1]
    if en&2048:px=px[::-1]
    x,y=bx+q%2*8,by+q//2*8;piece=decoded[y:y+8,x:x+8];mask=px>0;piece[mask,:3]=pal[en>>12][px[mask]];piece[mask,3]=255
 expected=np.array(sheet);mask=expected[...,3]>0;errors=int(np.any((decoded[...,:3]&248)!=(expected[...,:3]&248),2)[mask].sum());alpha=int(np.any(decoded[...,3]!=expected[...,3]).sum());assert errors==alpha==0,(errors,alpha)
 (E/'porytiles.json').write_text(json.dumps({'version':'legacy 2.0.0','compiled_metatiles':len(blocks),'native_5bit_RGB_errors':errors,'alpha_errors':alpha,'scope':'new local gate/rail/dock/boulder family plus reused HGSS grass; current engine primary and metatile IDs never repacked','engine_asset_import':'fixed native palettes and reusable primary glyphs'},indent=2)+'\n');print('Porytiles validated',len(blocks),'metatiles')
if __name__=='__main__':main(Path(sys.argv[1]),Path(sys.argv[2]))
