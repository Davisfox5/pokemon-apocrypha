"""Re-encode edited private Ecruteak layers; no geography generation."""
from pathlib import Path
import numpy as np,json,struct,subprocess
from PIL import Image
from palettes import cover
def compile_native(G,PT,S,E,bg,fg,solid,beh,above,assembly):
 W,H=72,52;SPLIT=27
 stats=[]
 for name,bank,y0,y1 in [('JohtoEcruteakTempleDistrict','ecruteak_temple',0,SPLIT),('JohtoEcruteakCity','ecruteak_city',SPLIT,H)]:
  inp=S/bank;out=E/(bank+'-compiled');inp.mkdir(exist_ok=True);out.mkdir(exist_ok=True)
  unique={};cells=[];pairs=[]
  for y in range(y0,y1):
   for x in range(W):
    a=bg[y*16:y*16+16,x*16:x*16+16];b=fg[y*16:y*16+16,x*16:x*16+16];attr=int(beh[y,x])|(0 if above[y,x] else 0x1000);key=(a.tobytes(),b.tobytes(),attr)
    if key not in unique:unique[key]=len(pairs);pairs.append((a,b,attr))
    cells.append(unique[key]|0x3000|(0xc00 if solid[y,x] else 0))
  assert len(pairs)<=1024,(name,len(pairs))
  rows=(len(pairs)+7)//8;bottom=Image.new('RGBA',(128,rows*16));middle=bottom.copy();top=bottom.copy()
  for i,(a,b,attr) in enumerate(pairs):bottom.paste(Image.fromarray(a),(i%8*16,i//8*16));middle.paste(Image.fromarray(b),(i%8*16,i//8*16))
  bottom.save(inp/'bottom.png');middle.save(inp/'middle.png');top.save(inp/'top.png')
  from palettes import cover
  cover(inp,refinement=True)
  cmd=[str(PT),'compile-primary','-dual-layer','-tiles-primary-override=1008','-tiles-total-override=1024','-metatiles-primary-override=1024','-pals-primary-override=13','-o',str(out),str(inp),str(G/'include/constants/metatile_behaviors.h')]
  result=subprocess.run(cmd,capture_output=True,text=True);(E/(bank+'-porytiles.log')).write_text(result.stdout+result.stderr)
  if result.returncode:print(result.stdout,result.stderr);raise SystemExit(result.returncode)
  tileim=Image.open(out/'tiles.png');blocks=(out/'metatiles.bin').read_bytes()[:len(pairs)*16];attrs=b''.join(struct.pack('<H',v[2]) for v in pairs)
  # The indexed transparent slot and the compiler's glyph IDs stay unchanged.
  for sec in [False,True]:
   folder=G/f'data/tilesets/{"secondary" if sec else "primary"}/{bank}';(folder/'palettes').mkdir(parents=True,exist_ok=True)
   start=512 if sec else 0;sh=Image.new('P',(128,256));sh.putpalette(tileim.getpalette())
   for i in range(512):
    tid=start+i
    if tid//16*8<tileim.height:sh.paste(tileim.crop((tid%16*8,tid//16*8,tid%16*8+8,tid//16*8+8)),(i%16*8,i//16*8))
   sh.save(folder/'tiles.png',bits=4)
   for i in range(16):
    p=out/'palettes'/f'{i:02}.pal';(folder/'palettes'/f'{i:02}.pal').write_text(p.read_text() if p.exists() else 'JASC-PAL\n0100\n16\n'+'0 0 0\n'*16)
   (folder/'metatiles.bin').write_bytes(blocks[start*16:(start+512)*16] or bytes(16));(folder/'metatile_attributes.bin').write_bytes(attrs[start*2:(start+512)*2] or bytes(2))
  layout=G/'data/layouts'/name;layout.mkdir(exist_ok=True);grid=np.array(cells,dtype='<u2').reshape(y1-y0,W);grid.tofile(layout/'map.bin')
  # A district edge is city paving, never a fabricated forest across the avenue.
  border=np.full((2,2),grid[(25 if y0==0 else 2),41]|0xc00,dtype='<u2');border.tofile(layout/'border.bin')
  stats.append(dict(map=name,tileset=bank,width=W,height=y1-y0,global_y=y0,metatiles=len(pairs),compiler='porytiles-legacy 2.0.0',command=cmd))
 assembly['districts']=stats
 (E/'assembly.json').write_text(json.dumps(assembly,indent=2)+'\n')
 print(json.dumps(stats,indent=2))
