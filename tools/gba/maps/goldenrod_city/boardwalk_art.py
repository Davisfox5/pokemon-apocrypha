"""Goldenrod's owner-approved ten-year additions, native-sized separate assets.
No existing map is regenerated; boardwalk.py imports these into current native files.
"""
from pathlib import Path
import math,sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[4];D=R/'gba/art/goldenrod-city/source/boardwalk';D.mkdir(exist_ok=True)
lock=D/'provenance.json'
if lock.exists():
 assert '--reproduce' in sys.argv,'Native masters already authored. Preserve them; --reproduce checks the retained input hashes first.'
 for name,h in json.loads(lock.read_text())['hashes'].items():assert hashlib.sha256((D/name).read_bytes()).hexdigest()==h,('Preserve edited native art',name)

# Existing Center-compatible palette11 supplies all metal, cabin and stall colors.
P=[(0,0,0),(40,32,32),(40,40,48),(48,128,160),(64,80,88),(96,184,200),(104,16,16),(128,120,96),(136,32,16),(152,64,48),(168,128,80),(168,152,120),(200,184,160),(216,80,32),(216,208,176),(240,232,216)]
def col(i):return (*P[i],255)
a=Image.open(D/'wheel-original.png').convert('RGBA');a=a.crop(a.getbbox()).resize((128,144),Image.Resampling.LANCZOS);v=np.array(a);mask=v[...,3]>=144;pal=np.array(P[1:],np.int32);idx=((v[...,:3,None].transpose(0,1,3,2).astype(int)-pal)**2).sum(3).argmin(2)+1;v[...,:3]=np.array(P,np.uint8)[idx];v[...,3]=mask*255;v[~mask]=0;wi=Image.fromarray(v);wd=ImageDraw.Draw(wi);wd.ellipse((56,53,72,69),fill=col(13),outline=col(8));pts=[]
for k in range(10):
 r=6 if k%2==0 else 2.7;angle=-math.pi/2+k*math.pi/5;pts.append((round(64+math.cos(angle)*r),round(61+math.sin(angle)*r)))
wd.polygon(pts,fill=col(14));wd.point((64,56),fill=col(15));wi.save(D/'wheel.png')
# Compact wood deck with repeating board joints; no random pixel noise.
a=Image.new('RGBA',(32,16));d=ImageDraw.Draw(a);d.rectangle((0,0,31,15),fill=(240,192,104,255))
for y in range(0,16,4):
 d.line((0,y,31,y),fill=(200,152,80,255));d.line((0,y+1,31,y+1),fill=(240,216,152,255));x=8 if y%8 else 24;d.line((x,y,x,y+3),fill=(208,160,88,255));d.point((x-2,y+2),fill=(144,112,64,255))
a.save(D/'deck.png')
# Independent awning/counter masters: keep the foreground alpha, ground separate.
for kind in ['snacks','souvenirs','prizes']:
 a=Image.new('RGBA',(48,48));d=ImageDraw.Draw(a);accent=3 if kind=='souvenirs' else 13;shadow=4 if accent==3 else 8
 d.rectangle((4,13,6,46),fill=col(1));d.rectangle((41,13,43,46),fill=col(1));d.line((5,16,5,44),fill=col(10));d.line((42,16,42,44),fill=col(12))
 d.rectangle((7,21,40,37),fill=col(7));d.rectangle((8,21,39,34),fill=col(14));d.line((10,23,37,23),fill=col(15))
 # Back shelf, small goods, then top and front of the wooden counter.
 d.rectangle((7,32,40,34),fill=col(1));d.line((8,32,39,32),fill=col(12))
 for i in range(5):
  x=10+i*6
  if kind=='snacks':
   d.rectangle((x,26,x+3,31),fill=col(13 if i%2 else 3));d.line((x+1,25,x+2,25),fill=col(15));d.point((x+1,27),fill=col(15))
  elif kind=='prizes':
   d.ellipse((x-1,26,x+4,31),fill=col(1));d.arc((x,26,x+3,30),180,360,fill=col(13));d.arc((x,26,x+3,30),0,180,fill=col(15));d.point((x+1,28),fill=col(14))
  else:
   d.rectangle((x,27,x+3,31),fill=col(3));d.polygon([(x,27),(x+2,24),(x+4,27)],fill=col(14));d.point((x+1,28),fill=col(15))
 d.rectangle((5,35,42,46),fill=col(1));d.rectangle((6,36,41,38),fill=col(12));d.line((7,36,40,36),fill=col(15));d.rectangle((7,39,40,44),fill=col(10))
 for x in [12,23,34]:d.line((x,40,x,44),fill=col(7))
 d.line((8,44,39,44),fill=col(11));d.rectangle((7,46,10,47),fill=col(1));d.rectangle((37,46,40,47),fill=col(1))
 # Contiguous curved awning silhouette, supports and crisp scalloped valance.
 d.polygon([(3,3),(44,3),(47,17),(47,21),(0,21),(0,17)],fill=col(1))
 for x in range(2,46):
  stripe=(x-2)//7%2;c=accent if stripe==0 else 15
  d.line((x,5,x,16),fill=col(c));d.line((x,17,x,20-(x%7 in [0,6])),fill=col(shadow if stripe==0 else 14))
 d.line((4,4,43,4),fill=col(15));d.line((2,16,45,16),fill=col(14));a.save(D/(kind+'.png'))
# Small sign/kiosk assets, reused teal/cyan/cream language from the native Center.
a=Image.new('RGBA',(64,24));d=ImageDraw.Draw(a);d.rounded_rectangle((0,0,63,23),radius=3,fill=col(1));d.rounded_rectangle((1,1,62,22),radius=2,fill=col(12));d.rectangle((3,3,60,20),fill=col(2));d.line((5,4,58,4),fill=col(5));d.rectangle((5,6,13,17),fill=col(3));d.line((7,8,11,8),fill=col(15));d.rectangle((7,10,11,14),fill=col(5));d.point((7,16),fill=col(15));d.point((11,16),fill=col(15))
for y,n in [(7,34),(11,28),(15,31)]:
 for x in range(18,n+18,3):d.line((x,y,x+1,y),fill=col(15))
 d.line((54,y,57,y),fill=col(5))
a.save(D/'departures.png')
a=Image.new('RGBA',(16,32));d=ImageDraw.Draw(a);d.rounded_rectangle((1,1,14,30),radius=2,fill=col(1));d.rectangle((2,2,13,28),fill=col(4));d.rectangle((3,3,12,7),fill=col(3));d.rectangle((3,9,12,17),fill=col(15));d.rectangle((4,10,11,14),fill=col(5));d.line((5,11,10,11),fill=col(3));d.line((5,13,8,13),fill=col(3));d.rectangle((4,20,11,23),fill=col(1));d.line((5,20,10,20),fill=col(12));d.rectangle((5,25,10,26),fill=col(14));d.line((2,29,13,29),fill=col(7));a.save(D/'ticket-kiosk.png')
a=Image.new('RGBA',(16,32));d=ImageDraw.Draw(a);d.rectangle((6,17,9,29),fill=col(1));d.rectangle((3,29,12,31),fill=col(4));d.rounded_rectangle((0,0,15,21),radius=2,fill=col(1));d.rectangle((1,1,14,19),fill=col(14));d.rectangle((2,2,13,17),fill=col(3));d.arc((4,4,11,11),180,355,fill=col(15));d.arc((6,7,9,10),180,355,fill=col(5));d.ellipse((7,10,8,11),fill=col(15));d.line((4,14,11,14),fill=col(5));a.save(D/'broadcast.png')
# Wood rail sections: exact shared colors of native bank0.
B=[(56,48,48,255),(120,72,40,255),(168,136,96,255),(144,112,56,255)]
for side in ['N','S','W','E']:
 a=Image.new('RGBA',(16,16));d=ImageDraw.Draw(a)
 if side in ['N','S']:
  for y in [5,10]:d.rectangle((0,y,15,y+2),fill=B[0]);d.line((0,y,15,y),fill=B[2])
  d.rectangle((0,1,4,15),fill=B[0]);d.rectangle((1,2,3,14),fill=B[1]);d.line((1,2,1,13),fill=B[2]);d.rectangle((0,0,5,3),fill=B[0]);d.line((1,1,4,1),fill=B[2])
 else:
  x=1 if side=='W' else 11;d.rectangle((x+1,0,x+3,15),fill=B[0]);d.line((x+1,0,x+1,15),fill=B[2]);d.rectangle((x,7,x+4,15),fill=B[0]);d.rectangle((x+1,8,x+3,14),fill=B[1]);d.rectangle((x,6,x+5,9),fill=B[0]);d.line((x+1,7,x+4,7),fill=B[2])
 a.save(D/('rail-'+side+'.png'))
a=Image.new('RGBA',(32,16));d=ImageDraw.Draw(a)
for y in [1,5,10]:d.rectangle((1,y,30,y+2),fill=B[0]);d.line((2,y,29,y),fill=B[2])
for x in [3,26]:d.rectangle((x,2,x+2,15),fill=B[0]);d.line((x+1,3,x+1,13),fill=B[1])
a.save(D/'bench.png')
# A compact lantern, same bank11 steel and warm glass as the wheel.
a=Image.new('RGBA',(16,32));d=ImageDraw.Draw(a);d.rectangle((7,12,9,29),fill=col(1));d.line((7,13,7,28),fill=col(4));d.rectangle((4,29,12,31),fill=col(1));d.line((5,29,11,29),fill=col(12));d.polygon([(3,3),(7,0),(10,0),(14,3),(13,5),(4,5)],fill=col(4));d.rectangle((4,5,12,12),fill=col(1));d.rectangle((5,6,11,10),fill=col(14));d.line((6,6,6,10),fill=col(15));d.rectangle((5,12,11,14),fill=col(4));d.point((8,2),fill=col(15));a.save(D/'lantern.png')
# Bank10 has four unused entries, extended locally without changing tree colors.
T=[(0,0,0),(64,56,40),(64,64,40),(72,72,48),(80,88,40),(88,104,32),(88,112,32),(96,120,32),(112,144,32),(120,152,32),(136,104,64),(136,168,40),(160,208,200),(216,80,32),(240,232,216),(240,192,104)]
for height,name in [(32,'planter'),(40,'retaining-planter')]:
 w=32 if name=='planter' else 48
 a=Image.new('RGBA',(w,height));d=ImageDraw.Draw(a);c=lambda i:(*T[i],255)
 d.rectangle((0,10,w-1,height-1),fill=c(1));d.rectangle((2,12,w-3,height-3),fill=c(12));d.line((3,height-3,w-4,height-3),fill=c(2));d.rectangle((4,7,w-5,13),fill=c(10));d.line((5,8,w-6,8),fill=c(1))
 for x in [0,w-4]:d.rectangle((x,8,x+3,height-1),fill=c(2));d.rectangle((x,8,x+3,10),fill=c(12));d.line((x+1,9,x+2,9),fill=c(14))
 d.line((5,14,w-6,14),fill=c(14))
 for x in range(12,w-5,12):d.line((x,16,x,height-4),fill=c(10))
 if height==40:d.line((4,26,w-5,26),fill=c(10))
 for i,x in enumerate([6,13,20,26] if w==32 else [7,14,21,28,35,41]):
  y=5+(i%3);d.ellipse((x-4,y+2,x+3,y+8),fill=c(4));d.ellipse((x-3,y+1,x+2,y+5),fill=c(8));d.line((x,y+3,x+2,y+1),fill=c(11));flower=13 if i%3==0 else 14 if i%3==1 else 15
  for dx,dy in [(-2,0),(2,0),(0,-2),(0,2)]:d.rectangle((x+dx-1,y+dy,x+dx,y+dy+1),fill=c(flower))
  d.rectangle((x-1,y,x,y+1),fill=c(15 if flower!=15 else 13))
 a.save(D/(name+'.png'))
print('Boardwalk native masters:',len(list(D.glob('*.png'))))
