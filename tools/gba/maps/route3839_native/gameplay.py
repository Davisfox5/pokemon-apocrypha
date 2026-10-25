"""Compare final real game captures and actual Porymap exports with native terrain pixels."""
from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'gba/art/route38-39-native/source';E=S.parent/'evidence';RUN=Path(sys.argv[1]);O=E/'gameplay';O.mkdir(exist_ok=True)
ims={n:np.array(Image.open(E/f'route{n}-native.png').convert('RGB')) for n in [38,39]};lawn=np.array(Image.open(S/'shared-lawn.png').convert('RGB'))&248
for n in [38,39]:
 p=np.array(Image.open(E/f'porymap/JohtoRoute{n}.png').convert('RGB'));assert np.array_equal(p,ims[n]),n
cases=[('route38-upper-path',38,12,4),('route38-raised-southern-bank',38,30,21),('route38-west-corner',38,10,21),('farm-stair-head',39,19,24),('farm-stair-foot-19',39,19,29),('south-stair-head-23',39,23,55),('south-stair-foot-23',39,23,59),('lower-farm-paddock',39,9,28),('east-wall-compound-corner',39,24,48),('west-wall-middle',39,8,42),('west-wall-lower-corner',39,11,52),('west-junction-12',39,31,12),('earth-ramp-12',38,2,12)]
proof=[];gallery=Image.new('RGB',(4*240,4*180),(28,33,38));d=ImageDraw.Draw(gallery)
for i,(name,n,x,y) in enumerate(cases):
 p=RUN/(name+'.png');shutil.copy2(p,O/p.name);frame=np.array(Image.open(p).convert('RGB'));expected=np.zeros_like(frame);ox,oy=x*16-112,y*16-72
 for sy,sx in np.ndindex((160,240)):
  wx,wy=ox+sx,oy+sy;m=n;a=ims[n]
  if n==38 and wx<0 and 0<=wy<1024:wx+=512;m=39;a=ims[39]
  elif n==39 and wx>=512 and 0<=wy<512:wx-=512;m=38;a=ims[38]
  expected[sy,sx]=a[wy,wx] if 0<=wy<a.shape[0] and 0<=wx<a.shape[1] else lawn[(oy+sy)%32,(ox+sx)%32]
 mask=np.ones((160,240),bool);mask[40:100,100:140]=False
 if 'junction' in name or 'earth-ramp' in name:mask[:40,:100]=False
 bad=((frame>>3)!=(expected>>3)).any(-1)&mask
 assert not bad.any(),(name,int(bad.sum()),np.argwhere(bad)[:10].tolist())
 proof.append(dict(frame=name,route=n,player=[x,y],native_RGB5_pixels_checked=int(mask.sum()),different=int(bad.sum()),player_exclusion=[100,40,140,100],map_name_popup_exclusion=[0,0,100,40] if 'junction' in name or 'earth-ramp' in name else None));gallery.paste(Image.fromarray(frame),(i%4*240,i//4*180+20));d.text((i%4*240+3,i//4*180+3),name,fill='white')
gallery.save(E/'gameplay-contact.png');(E/'gameplay-pixels.json').write_text(json.dumps(proof,indent=2)+'\n');print('Porymap exact; gameplay',sum(p['native_RGB5_pixels_checked'] for p in proof),'pixels, 0 differences')
