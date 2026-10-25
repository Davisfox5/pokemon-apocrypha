"""Final emulator pixels against decoded native maps, both sides of the real horizontal seam."""
from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];E=ROOT/'gba/art/routes3839-complete/evidence';RUN=Path(sys.argv[1]);OUT=E/'gameplay';OUT.mkdir(exist_ok=True)
ims={n:np.array(Image.open(E/f'route{n}/native.png').convert('RGB')) for n in [38,39]}
locations=[(39,23,55),(39,14,50),(39,14,38),(39,19,29),(39,19,24),(39,9,30),(39,9,13),(39,9,5),(39,19,12),(38,2,12),(38,12,5),(38,20,6),(38,20,20),(38,21,25),(38,34,21),(38,52,12),(38,58,7),(38,62,7),(38,52,12),(39,28,12)]
proof=[];gallery=Image.new('RGB',(4*240,5*180),(25,30,35));draw=ImageDraw.Draw(gallery)
for i,(n,x,y) in enumerate(locations):
 name=f'tour-{i:02}';frame=np.array(Image.open(RUN/f'{name}.png').convert('RGB'));expected=np.zeros_like(frame);valid=np.zeros((160,240),bool);ox,oy=x*16-112,y*16-72
 for sy,sx in np.ndindex((160,240)):
  wx,wy=ox+sx,oy+sy;a=ims[n]
  if n==38 and wx<0 and 0<=wy<1024:wx+=512;a=ims[39]
  elif n==39 and wx>=512 and 0<=wy<512:wx-=512;a=ims[38]
  if 0<=wy<a.shape[0] and 0<=wx<a.shape[1]:expected[sy,sx]=a[wy,wx];valid[sy,sx]=True
 valid[40:100,100:140]=False
 if i in (9,19):valid[:40,:100]=False
 bad=((frame>>3)!=(expected>>3)).any(-1)&valid
 assert not bad.any(),(name,int(bad.sum()),np.argwhere(bad)[:10].tolist())
 shutil.copyfile(RUN/f'{name}.png',OUT/f'{name}.png');gallery.paste(Image.fromarray(frame),(i%4*240,i//4*180+20));draw.text((i%4*240+4,i//4*180+4),f'Route {n}: ({x},{y})',fill='white')
 proof.append(dict(frame=name,route=n,player=[x,y],native_pixels_checked=int(valid.sum()),differences=0,exclusions='Player rectangle; map-name popup at crossing; outside native map bounds.'))
gallery.save(E/'gameplay-contact.png');(E/'gameplay-pixels.json').write_text(json.dumps(proof,indent=2)+'\n')
for name in ['cold-reload','title-continue','farmhouse-label','stable-label','save-route39']:
 shutil.copyfile(RUN/f'{name}.png',OUT/f'{name}.png')
print(sum(p['native_pixels_checked'] for p in proof),'native game pixels match exactly in RGB555')
