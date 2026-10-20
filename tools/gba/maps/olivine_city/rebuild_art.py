"""Native-size asset preparation. No HGSS overview raster is read or sampled.
New architecture generated as isolated transparent masters; terrain/props drawn
from independent modules. Never regenerates or writes committed native maps.
"""
from pathlib import Path
import json,hashlib,math
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[4];S=R/'gba/art/olivine-city/source/rebuilt';M=S/'masters';D=S/'modules'
M.mkdir(exist_ok=True);D.mkdir(exist_ok=True)
# Explicit atlas cells, with all background alpha removed by the image tool.
# One architectural master is reused at each compatible residence location.
sheet=Image.open(S/'architecture-original.png').convert('RGBA')
boxes={'gym':((24,144,520,544),(112,96)),'house':((544,176,872,544),(72,88)),'cafe':((912,208,1240,552),(72,80)),'lighthouse':((24,568,448,1160),(120,176)),'terminal':((448,760,920,1152),(152,112)),'sailboat':((920,808,1248,1152),(80,72))}
for name,(box,size) in boxes.items():
 a=sheet.crop(box);alpha=a.getchannel('A');alpha=alpha.point(lambda v:255 if v>=144 else 0);a.putalpha(alpha);b=alpha.getbbox();assert b;a=a.crop(b).resize(size,Image.Resampling.LANCZOS);alpha=a.getchannel('A').point(lambda v:255 if v>=144 else 0);a.putalpha(alpha);a.save(M/(name+'.png'))
# Native modules: intentionally low-contrast, repeatable material detail with
# clear structure. No photographic noise or unbounded randomness.
def new(w,h,color=(0,0,0,0)):
 a=Image.new('RGBA',(w,h),color);return a,ImageDraw.Draw(a)
def save(name,a):a.save(D/(name+'.png'))
a,d=new(32,32,'#247ab0')
for y in [3,13,24]:
 x={3:2,13:16,24:6}[y];d.line([(x-4,y+1),(x,y),(x+7,y),(x+11,y-1)],fill='#328db8');d.line([(x-1,y+2),(x+5,y+2)],fill='#398fba')
# A second phase across edges makes the texture periodic without grid seams.
d.line([(27,5),(31,5)],fill='#328db8');d.line([(0,5),(3,4)],fill='#328db8');save('water',a)
a,d=new(32,32,'#a8c7c5')
# Ring-cut stone fans, the recognizable Olivine paving material rebuilt as a
# seamless native core, rather than a generic brick substitution.
for r in [5,10,15]:
 d.ellipse((16-r,16-r,16+r,16+r),outline='#91b2b2')
 for i in range(8):
  angle=(i*45+(22 if r==10 else 0))*math.pi/180
  rr=max(0,r-4);x0=16+round(rr*math.cos(angle));y0=16+round(rr*math.sin(angle));x1=16+round((r-1)*math.cos(angle));y1=16+round((r-1)*math.sin(angle));d.line((x0,y0,x1,y1),fill='#91b2b2')
 d.arc((17-r,17-r,15+r,15+r),190,270,fill='#bdd6d1')
d.ellipse((14,14,18,18),fill='#b1cecb',outline='#91b2b2');save('paving',a)
a,d=new(32,32,'#78c8a0')
for x,y in [(4,7),(22,19),(12,28)]:d.line((x,y,x+2,y),fill='#80cda5');d.point((x+1,y-1),fill='#87d1a9')
save('lawn',a)
a,d=new(32,32,'#e8d49b')
for x,y in [(4,8),(22,22),(12,30)]:d.line((x,y,x+4,y),fill='#dfc891');d.line((x+1,y-1,x+3,y-1),fill='#efdfb1')
save('sand',a)
a,d=new(32,32,'#cabf9c')
for x in range(0,32,8):
 d.rectangle((x,0,x+1,31),fill='#998c73');d.line((x+2,0,x+2,31),fill='#e1d6b7');d.line((x+6,0,x+6,31),fill='#b9aa89')
for x,y in [(4,7),(20,23)]:d.ellipse((x,y,x+2,y+4),outline='#ab9a7a')
save('dock',a)
a,d=new(32,32,'#937348')
# Broad faceted rock courses with staggered broken joints and rounded shoulders.
# Grain runs around individual rocks, never continuous wood-like striping.
for row,y in enumerate([0,16]):
 for x in range(-16,48,16):
  x+=8 if row else 0
  d.polygon([(x,y+3),(x+3,y),(x+12,y),(x+15,y+4),(x+14,y+13),(x+10,y+15),(x+2,y+14),(x,y+10)],fill='#b79a65',outline='#70573e')
  d.polygon([(x+3,y+1),(x+11,y+1),(x+13,y+4),(x+8,y+6),(x+2,y+5)],fill='#d9c28d')
  d.polygon([(x+2,y+6),(x+8,y+7),(x+12,y+5),(x+11,y+11),(x+4,y+12)],fill='#bd9b67')
  d.line([(x+4,y+13),(x+10,y+14),(x+13,y+11)],fill='#87663e')
save('cliff-face',a)
a,d=new(16,16,'#b79a65')
d.polygon([(0,0),(15,0),(15,5),(12,6),(9,4),(5,5),(2,4),(0,6)],fill='#78c8a0')
d.line([(0,6),(3,5),(6,6),(9,5),(12,7),(15,6)],fill='#609c7e')
d.polygon([(0,7),(3,6),(7,7),(10,6),(15,8),(15,11),(10,12),(4,11),(0,12)],fill='#d9c28d')
d.line([(1,13),(4,14),(10,14),(14,12)],fill='#937348');save('cliff-cap',a)
a,d=new(16,16)
d.rectangle((0,7,15,9),fill='#8caaa4');d.line((0,7,15,7),fill='#eef3e1');d.rectangle((0,12,15,14),fill='#b9c6b5')
for x in [1,9]:d.polygon([(x,3),(x+2,1),(x+4,3),(x+4,15),(x,15)],fill='#e3e8d3',outline='#7b9590');d.line((x+1,4,x+1,13),fill='#f6f4df')
save('fence',a)
a,d=new(16,64)
d.rectangle((6,10,9,56),fill='#334e57');d.line((6,10,6,54),fill='#90a6a5');d.rectangle((3,54,12,60),fill='#aab3a2',outline='#3d5c60');d.rectangle((2,60,13,63),fill='#cdd0b4',outline='#536761');d.ellipse((3,1,12,11),fill='#f0c960',outline='#866f39');d.ellipse((5,3,8,7),fill='#fff0b0');d.rectangle((5,12,10,15),fill='#b4a16a');save('lamp',a)
a,d=new(16,24);d.rectangle((6,14,9,23),fill='#777866');d.rounded_rectangle((1,1,14,17),radius=2,fill='#475f5d',outline='#273e43');d.rectangle((3,3,12,14),fill='#d4d5b5');d.line((5,6,10,6),fill='#859e91');d.line((5,9,10,9),fill='#859e91');save('sign',a)
a,d=new(64,56)
# Eight triangular clean parasol panels, complete central hub and pole.
c=(30,8);p=[(30,0),(46,4),(54,15),(42,25),(18,25),(6,15),(14,4)]
for i in range(len(p)):d.polygon([c,p[i],p[(i+1)%len(p)]],fill=['#dcece0','#42b4cb','#2388ab','#dcece0','#42b4cb','#dcece0','#2388ab'][i])
d.line(p+[p[0]],fill='#315e67',width=1);d.ellipse((28,6,32,10),fill='#e5d89b');d.rectangle((29,12,31,43),fill='#527273');d.line((29,17,29,43),fill='#d1dfd0')
d.rectangle((0,39,63,51),fill='#5b7774');d.rectangle((1,36,62,47),fill='#e0e0bf',outline='#687d75')
for x in [5,15,25,35,45,55]:d.line((x,38,x,45),fill='#a8bbb0')
d.rectangle((5,49,9,55),fill='#697c70');d.rectangle((53,49,57,55),fill='#697c70');save('parasol-table',a)
a,d=new(32,32)
d.rectangle((0,0,31,31),fill='#7c7762')
for y in range(0,32,4):d.rectangle((3,y,28,y+2),fill='#d1c49c');d.line((3,y,28,y),fill='#eee0b6');d.line((3,y+3,28,y+3),fill='#8c8267')
d.rectangle((0,0,2,31),fill='#a49470');d.rectangle((29,0,31,31),fill='#a49470');save('stairs',a)
a,d=new(48,64)
d.polygon([(0,24),(47,0),(47,39),(0,63)],fill='#9b926e',outline='#59645c')
for x in range(0,48,6):
 y=24-x//2;d.line((x,y,x,y+38),fill='#d2c8a2');d.line((x+1,y,x+1,y+38),fill='#afa17b')
for x,y in [(0,24),(47,0)]:d.line((x,y,x,y+38),fill='#4b635f',width=2)
d.line((0,24,47,0),fill='#d9d2ac',width=3);d.line((0,62,47,38),fill='#d9d2ac',width=3);save('ramp',a)
# Reconstructed shore rocks: faceted surfaces are reusable complete silhouettes.
a,d=new(24,24);d.polygon([(4,9),(9,2),(16,2),(21,10),(22,17),(18,22),(6,22),(1,17)],fill='#879f96',outline='#496c70');d.polygon([(4,9),(9,3),(15,3),(13,13),(5,17),(2,16)],fill='#d4d8b8');d.polygon([(15,3),(20,10),(21,16),(14,18),(13,13)],fill='#adbca4');d.line((6,22,18,22),fill='#d3e2cf');save('shore-rock',a)
# Bank palette overrides shared by every private native section. One family per
# rebuilt building avoids quadrant checker seams; terrain stays independent.
colors={}
for name in ['water','paving','sand','lawn','dock','cliff-face','cliff-cap','curb','fence','lamp','sign','parasol-table','stairs','ramp','shore-rock']:
 p=D/(name+'.png');colors[name]=hashlib.sha256(p.read_bytes()).hexdigest()
(S/'art-provenance.json').write_text(json.dumps(dict(architecture_generator='image_gen; six isolated original buildings/boat using HGSS as architecture reference only',architecture_source='architecture-original.png',architecture_sha256=hashlib.sha256((S/'architecture-original.png').read_bytes()).hexdigest(),masters={n:dict(crop=b,target_size=z,sha256=hashlib.sha256((M/(n+'.png')).read_bytes()).hexdigest()) for n,(b,z) in boxes.items()},terrain='Native-size independently drawn repeatable modules; no overview pixels',modules=colors),indent=2)+'\n')
