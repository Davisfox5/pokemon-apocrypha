"""Install the reviewed fresh native kit into an isolated source checkout."""
from pathlib import Path
import sys,json,struct,subprocess
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];G=Path(sys.argv[1]);PT=Path(sys.argv[2]);S=ROOT/'gba/art/route38-39-native/source';E=S.parent/'evidence';BANK='route3839_native'
assert not subprocess.check_output(['git','-C',str(G),'ls-files',f'data/tilesets/primary/{BANK}'],text=True).strip(),'Current native source is authoritative after first authoring.'
z=np.load(S/'native-input.npz');pairs=z['pairs'];inp=S/'porytiles';out=E/'compiled';inp.mkdir(exist_ok=True);out.mkdir(exist_ok=True);rows=(len(pairs)+7)//8;bottom=Image.new('RGBA',(128,rows*16));empty=bottom.copy()
for i,a in enumerate(pairs):bottom.paste(Image.fromarray(a),(i%8*16,i//8*16))
bottom.save(inp/'bottom.png');empty.save(inp/'middle.png');empty.save(inp/'top.png')
cmd=[str(PT),'compile-primary','-dual-layer','-tiles-primary-override=1008','-tiles-total-override=1024','-metatiles-primary-override=1024','-pals-primary-override=13','-o',str(out),str(inp),str(G/'include/constants/metatile_behaviors.h')];r=subprocess.run(cmd,capture_output=True,text=True);(E/'porytiles.log').write_text(r.stdout+r.stderr);assert not r.returncode,r.stderr
im=Image.open(out/'tiles.png');blocks=(out/'metatiles.bin').read_bytes()[:len(pairs)*16];attrs=struct.pack('<H',0x1000)*len(pairs)
for sec in [False,True]:
 side='secondary' if sec else 'primary';sym='Route3839Native'+('' if sec else 'Primary');folder=G/f'data/tilesets/{side}/{BANK}';(folder/'palettes').mkdir(parents=True,exist_ok=True);start=512 if sec else 0;sh=Image.new('P',(128,256));sh.putpalette(im.getpalette())
 for i in range(512):
  tid=start+i
  if tid//16*8<im.height:sh.paste(im.crop((tid%16*8,tid//16*8,tid%16*8+8,tid//16*8+8)),(i%16*8,i//16*8))
 sh.save(folder/'tiles.png',bits=4)
 for i in range(16):
  p=out/'palettes'/f'{i:02}.pal';(folder/'palettes'/f'{i:02}.pal').write_text(p.read_text() if p.exists() else 'JASC-PAL\n0100\n16\n'+'0 0 0\n'*16)
 (folder/'metatiles.bin').write_bytes(blocks[start*16:(start+512)*16] or bytes(16));(folder/'metatile_attributes.bin').write_bytes(attrs[start*2:(start+512)*2] or bytes(2))
 entries={'graphics.h':f'const u32 gTilesetTiles_{sym}[] = INCGFX_U32("data/tilesets/{side}/{BANK}/tiles.png", ".4bpp.fastSmol");\nconst u16 gTilesetPalettes_{sym}[][16] = {{\n'+''.join(f'INCGFX_U16("data/tilesets/{side}/{BANK}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16))+'};\n','metatiles.h':f'const u16 gMetatiles_{sym}[] = INCBIN_U16("data/tilesets/{side}/{BANK}/metatiles.bin");\nconst u16 gMetatileAttributes_{sym}[] = INCBIN_U16("data/tilesets/{side}/{BANK}/metatile_attributes.bin");\n','headers.h':f'const struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, .isSecondary = {"TRUE" if sec else "FALSE"}, .tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym}, .metatiles = gMetatiles_{sym}, .metatileAttributes = gMetatileAttributes_{sym}, .callback = NULL }};\n'}
 for f,v in entries.items():
  p=G/'src/data/tilesets'/f
  if f'gTileset_{sym} ' not in p.read_text() if f=='headers.h' else f'gTilesetTiles_{sym}[]' not in p.read_text() if f=='graphics.h' else f'gMetatiles_{sym}[]' not in p.read_text():p.write_text(p.read_text()+'\n// Routes38/39 terrain rebuild\n'+v)
ls=json.loads((G/'data/layouts/layouts.json').read_text())
for n in [38,39]:
 grid=z[f'route{n}'];folder=G/f'data/layouts/JohtoRoute{n}';grid.astype('<u2').tofile(folder/'map.bin');border=grid[2:4,2:4].copy()|0xc00;border.astype('<u2').tofile(folder/'border.bin')
 for l in ls['layouts']:
  if l['name']==f'JohtoRoute{n}_Layout':l.update(primary_tileset='gTileset_Route3839NativePrimary',secondary_tileset='gTileset_Route3839Native')
(G/'data/layouts/layouts.json').write_text(json.dumps(ls,indent=2)+'\n');(E/'packing.json').write_text(json.dumps(dict(metatiles=len(pairs),allocated_glyphs=im.height//8*16,palettes_used=sorted(set(map(int,np.frombuffer(blocks,'<u2')>>12))),command=cmd),indent=2)+'\n');print('Installed new private native tile kit:',len(pairs),'metatiles,',im.height//8*16,'glyph slots')
