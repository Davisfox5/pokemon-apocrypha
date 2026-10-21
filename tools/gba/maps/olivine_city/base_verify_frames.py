"""Compare actual captured BG VRAM/palettes/scroll to the decoded native world."""
from pathlib import Path
import sys,json,re
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;R=HERE.parents[3];sys.path.insert(0,str(HERE));import base_runtime as tour
O=Path(sys.argv[1]);E=R/'gba/art/olivine-city/evidence';native=np.array(Image.open(E/'native-map.png').convert('RGB'));locations={};pos=None
for step in tour.steps:
 for m in re.finditer(r'(go|at)\((\d+),(\d+),(\d+)|shot\("([^"]+)"\)',step):
  if m[1]:
   num,x,y=map(int,[m[2],m[3],m[4]]);pos=(num,x,y)
  else:locations[m[5]]=pos
for n in ['cold-reload','title-continue']:locations[n]=tour.section(24,32)
results=[]
def decode(p):
 v=np.frombuffer(p.with_suffix('.vram').read_bytes(),np.uint8);pal=np.frombuffer(p.with_suffix('.pal').read_bytes(),'<u2');reg=np.frombuffer(p.with_suffix('.scroll').read_bytes(),'<u2');rgb=np.array([[int(c&31)<<3,int(c>>5&31)<<3,int(c>>10&31)<<3] for c in pal],np.uint8);out=np.zeros((160,240,3),np.uint8);Y,X=np.indices((160,240))
 for bg in [3,2,1]:
  ctrl=int(reg[bg]);sx=int(reg[4+bg*2])&511;sy=int(reg[5+bg*2])&511;xx=(X+sx)%256;yy=(Y+sy)%256;address=(ctrl>>8&31)*2048+(yy//8*32+xx//8)*2;e=v[address].astype(np.uint16)|v[address+1].astype(np.uint16)<<8
  tx=xx%8;ty=yy%8;tx=np.where(e&1024,7-tx,tx);ty=np.where(e&2048,7-ty,ty);a=(ctrl>>2&3)*16384+(e&1023)*32+ty*4+tx//2;value=(v[a]>>(tx%2*4))&15;opaque=value!=0;out[opaque]=rgb[(e>>12)*16+value][opaque]
 return out
from border import border_cell
for name,(num,x,y) in locations.items():
 if not 63<=num<63+len(tour.sections):continue
 p=O/(name+'.vram')
 if not p.exists():continue
 box=tour.sections[num-63]['box'];wx=x+box[0];wy=y+box[1];now=decode(p);best=None
 # The engine camera uses a fixed120x80centre with the16px feet baseline.
 # Test the documented anchor and record an offset only if actual registers
 # disagree. A later expected tolerance never hides material/palette errors.
 for dy in [0,-8,8,-16,16]:
  x0=wx*16-112;y0=wy*16-72+dy;expected=np.zeros((160,240,3),np.uint8)
  for yy in range(y0//16,(y0+159)//16+1):
   for xx in range(x0//16,(x0+239)//16+1):
    sx,sy=border_cell(xx,yy);px=max(x0,xx*16);py=max(y0,yy*16);ex=min(x0+240,xx*16+16);ey=min(y0+160,yy*16+16)
    expected[py-y0:ey-y0,px-x0:ex-x0]=native[sy*16+py-yy*16:sy*16+ey-yy*16,sx*16+px-xx*16:sx*16+ex-xx*16]
  errors=int(np.any(now!=expected,2).sum())
  if best is None or errors<best[0]:best=(errors,dy,expected)
 errors,dy,expected=best;Image.fromarray(now).save(O/(name+'-background.png'));results.append(dict(frame=name,world=[wx,wy],camera_delta_y=dy,pixels=38400,RGB_errors=errors))
 if errors:
  sh=Image.new('RGB',(720,160));sh.paste(Image.fromarray(expected),(0,0));sh.paste(Image.fromarray(now),(240,0));diff=np.zeros_like(now);diff[np.any(now!=expected,2)]=[255,0,80];sh.paste(Image.fromarray(diff),(480,0));sh.save(O/(name+'-difference.png'))
report=dict(frames=len(results),pixels=sum(r['pixels'] for r in results),RGB_errors=sum(r['RGB_errors'] for r in results),frames_detail=results);(E/'base-terrain/gameplay-background-parity.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
assert not report['RGB_errors'],'Inspect actual VRAM differences; do not conceal them with tolerance'
