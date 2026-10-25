"""Pack reviewed private layers into the two existing native layouts only."""
from pathlib import Path
import sys,json,struct,subprocess
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];G=Path(sys.argv[1]);PT=Path(sys.argv[2]);S=ROOT/'gba/art/route38-39-terrain/source/refinement';E=S.parent.parent/'evidence/refinement'
assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()=='fee08659d8f68d735ac48e507554526a9d72e9d3'
z=np.load(S/'native-candidate.npz');pairs=z['pairs'];inp=S/'porytiles';out=E/'compiled';inp.mkdir(exist_ok=True);out.mkdir(exist_ok=True);rows=(len(pairs)+7)//8
bottom=Image.new('RGBA',(128,rows*16));empty=bottom.copy()
for i,a in enumerate(pairs):bottom.paste(Image.fromarray(a),(i%8*16,i//8*16))
bottom.save(inp/'bottom.png');empty.save(inp/'middle.png');empty.save(inp/'top.png')
cmd=[str(PT),'compile-primary','-dual-layer','-tiles-primary-override=1008','-tiles-total-override=1024','-metatiles-primary-override=1024','-pals-primary-override=13','-o',str(out),str(inp),str(G/'include/constants/metatile_behaviors.h')]
r=subprocess.run(cmd,capture_output=True,text=True);(E/'porytiles.log').write_text(r.stdout+r.stderr);assert not r.returncode,r.stderr
im=Image.open(out/'tiles.png');blocks=(out/'metatiles.bin').read_bytes()[:len(pairs)*16];attrs=struct.pack('<H',0x1000)*len(pairs)
for sec in [False,True]:
 folder=G/f'data/tilesets/{"secondary" if sec else "primary"}/route38_39';start=512 if sec else 0;sh=Image.new('P',(128,256));sh.putpalette(im.getpalette())
 for i in range(512):
  tid=start+i
  if tid//16*8<im.height:sh.paste(im.crop((tid%16*8,tid//16*8,tid%16*8+8,tid//16*8+8)),(i%16*8,i//16*8))
 sh.save(folder/'tiles.png',bits=4)
 for i in range(16):
  p=out/'palettes'/f'{i:02}.pal';(folder/'palettes'/f'{i:02}.pal').write_text(p.read_text() if p.exists() else 'JASC-PAL\n0100\n16\n'+'0 0 0\n'*16)
 (folder/'metatiles.bin').write_bytes(blocks[start*16:(start+512)*16] or bytes(16));(folder/'metatile_attributes.bin').write_bytes(attrs[start*2:(start+512)*2] or bytes(2))
layouts=json.loads((G/'data/layouts/layouts.json').read_text())
for n in [38,39]:
 grid=z[f'route{n}'];h,w=grid.shape;folder=G/f'data/layouts/JohtoRoute{n}';grid.astype('<u2').tofile(folder/'map.bin');np.full((2,2),int(grid[2,2])|0xc00,'<u2').tofile(folder/'border.bin')
 for layout in layouts['layouts']:
  if layout['name']==f'JohtoRoute{n}_Layout':layout.update(width=w,height=h)
 p=G/f'data/maps/JohtoRoute{n}/map.json';d=json.loads(p.read_text());assert len(d['connections'])==1;d['connections'][0]['offset']=0;p.write_text(json.dumps(d,indent=2)+'\n')
(G/'data/layouts/layouts.json').write_text(json.dumps(layouts,indent=2)+'\n')
entries=np.frombuffer(blocks,'<u2');used_pals=sorted(set(map(int,entries>>12)));(E/'native-budget.json').write_text(json.dumps(dict(metatiles=len(pairs),allocated_glyphs=im.height//8*16,palette_indices=used_pals,command=cmd),indent=2)+'\n');print('Packed',len(pairs),'metatiles,',im.height//8*16,'glyph slots, palettes',used_pals)
