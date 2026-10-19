"""Compile explicitly supplied Olivine planes, without reconstructing geography."""
import json,struct,subprocess
from pathlib import Path
import numpy as np
from PIL import Image

def compile_planes(G,PT,S,T,E,assembly,bg,fg,above,solid,beh,mods):
 W=72;stats=[];staged=[]
 for dist in assembly['districts']:
  name,bank,y0,y1=dist['map'],dist['tileset'],dist['global_y'],dist['global_y']+dist['height']
  if bank=='olivine_harbor':stats.append(dist);continue
  inp=T/bank;out=E/(bank+'-compiled');inp.mkdir(exist_ok=True);out.mkdir(exist_ok=True);unique={};cells=[];pairs=[]
  for y in range(y0,y1):
   for x in range(W):
    a=bg[y*16:y*16+16,x*16:x*16+16];b=fg[y*16:y*16+16,x*16:x*16+16];attr=int(beh[y,x])|(0 if above[y,x] else 0x1000);key=(a.tobytes(),b.tobytes(),attr)
    if key not in unique:unique[key]=len(pairs);pairs.append((a,b,attr))
    cells.append(unique[key]|0x3000|(0xc00 if solid[y,x] else 0))
  assert len(pairs)<=1024,(name,len(pairs));rows=(len(pairs)+7)//8;bottom=Image.new('RGBA',(128,rows*16));middle=bottom.copy();topim=bottom.copy()
  for i,(a,b,attr) in enumerate(pairs):bottom.paste(Image.fromarray(a),(i%8*16,i//8*16));middle.paste(Image.fromarray(b),(i%8*16,i//8*16))
  bottom.save(inp/'bottom.png');middle.save(inp/'middle.png');topim.save(inp/'top.png')
  from terrain_palettes import cover
  cover(inp,S,mods,[S.parent/'evidence/terrain-reset'/(bank+'-compiled')/'palettes'])
  cmd=[str(PT),'compile-primary','-dual-layer','-tiles-primary-override=1008','-tiles-total-override=1024','-metatiles-primary-override=1024','-pals-primary-override=13','-o',str(out),str(inp),str(G/'include/constants/metatile_behaviors.h')]
  r=subprocess.run(cmd,capture_output=True,text=True);(E/(bank+'-porytiles.log')).write_text(r.stdout+r.stderr)
  if r.returncode:print(r.stdout,r.stderr);raise SystemExit(r.returncode)
  staged.append((name,bank,y0,y1,out,len(pairs),pairs,cells))
  stats.append(dict(map=name,tileset=bank,width=W,height=y1-y0,global_y=y0,metatiles=len(pairs),command=cmd))
 # Stage every district successfully before mutating native source.
 for name,bank,y0,y1,out,pair_count,pairs,cells in staged:
  tileim=Image.open(out/'tiles.png');blocks=(out/'metatiles.bin').read_bytes()[:pair_count*16];attrs=b''.join(struct.pack('<H',v[2]) for v in pairs)
  for sec in [False,True]:
   folder=G/f'data/tilesets/{"secondary" if sec else "primary"}/{bank}';start=512 if sec else 0;sh=Image.new('P',(128,256));sh.putpalette(tileim.getpalette())
   for i in range(512):
    tid=start+i
    if tid//16*8<tileim.height:sh.paste(tileim.crop((tid%16*8,tid//16*8,tid%16*8+8,tid//16*8+8)),(i%16*8,i//16*8))
   sh.save(folder/'tiles.png',bits=4)
   for i in range(16):
    p=out/'palettes'/f'{i:02}.pal';(folder/'palettes'/f'{i:02}.pal').write_text(p.read_text() if p.exists() else 'JASC-PAL\n0100\n16\n'+'0 0 0\n'*16)
   (folder/'metatiles.bin').write_bytes(blocks[start*16:(start+512)*16] or bytes(16));(folder/'metatile_attributes.bin').write_bytes(attrs[start*2:(start+512)*2] or bytes(2))
  layout=G/'data/layouts'/name;grid=np.array(cells,dtype='<u2').reshape(y1-y0,W);grid.tofile(layout/'map.bin');np.full((2,2),grid[18 if y0==0 else 1,28]|0xc00,dtype='<u2').tofile(layout/'border.bin')
 assembly['districts']=stats
 (E/'assembly.json').write_text(json.dumps(assembly,indent=2)+'\n')
 return stats
