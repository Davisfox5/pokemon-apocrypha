"""Owner-proposed kiln and end-on firewood, using native existing material ramps.
Art/proposal only. Install with the separate locked native patch; no town generator.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json
R=Path(__file__).resolve().parents[4];S=R/'gba/art/azalea-town/source';D=S/'kurt-extension';D.mkdir(exist_ok=True)
main=Image.open(S/'masters/kurt.png').convert('RGBA')
# A small timber link attaches the masonry kiln to the original house wall.
wing=Image.new('RGBA',(64,64));d=ImageDraw.Draw(wing)
d.rectangle((0,38,23,63),fill=(56,24,16,255));d.rectangle((3,40,22,59),fill=(88,48,8,255));d.line((5,40,5,59),fill=(136,88,8,255));d.rectangle((0,60,23,63),fill=(32,24,24,255));d.rectangle((0,60,23,62),fill=(96,88,80,255))
# Existing charcoal/masonry palette 12; no extra palette and no rescaled house.
outline=(40,40,40,255);mortar=(88,72,56,255);stone=(144,120,96,255);shade=(80,80,72,255);light=(144,144,144,255)
# Full flue and chamfered cap, visibly seated in the dome behind its front surface.
d.rectangle((43,4,55,29),fill=outline);d.rectangle((44,5,52,28),fill=stone);d.rectangle((53,5,54,28),fill=mortar)
for y in [10,17,24]:
 d.line((44,y,54,y),fill=mortar);d.line((48 if y!=17 else 51,y-5,48 if y!=17 else 51,y-1),fill=mortar)
d.polygon([(40,1),(42,0),(56,0),(58,2),(58,5),(40,5)],fill=outline);d.rectangle((42,1,56,2),fill=light);d.rectangle((45,1,53,2),fill=(24,24,24,255));d.line((41,4,57,4),fill=mortar)
# A rounded masonry shell, with its own depth and curved shoulder, not a second roof.
mask=Image.new('1',(64,64));points=[(24,62),(24,36),(27,29),(32,24),(40,20),(48,23),(55,28),(61,36),(63,42),(63,61),(60,63),(25,63)];ImageDraw.Draw(mask).polygon(points,fill=1);a=np.array(wing);m=np.array(mask,dtype=bool)
for y,x in np.argwhere(m):
 a[y,x]=stone if x<52 else mortar
 # Restrained alternating stone courses: continuous blocks, no random dots.
 if y>=28 and y%7==0:a[y,x]=mortar
 elif y>=28 and (x+(5 if (y//7)%2 else 0))%12==0:a[y,x]=mortar
 elif x<29:a[y,x]=shade
wing=Image.fromarray(a);d=ImageDraw.Draw(wing);d.line(points+[points[0]],fill=outline,width=1)
d.line([(26,36),(29,30),(34,26),(40,22),(47,25)],fill=light,width=1)
# Firebox: complete arched stone surround, recessed unlit mouth and a solid hearth.
d.ellipse((30,39,54,62),fill=mortar);d.rectangle((30,50,54,62),fill=mortar);d.arc((31,40,53,61),180,360,fill=stone,width=2)
d.ellipse((34,44,50,60),fill=(24,24,24,255));d.rectangle((34,52,50,61),fill=(24,24,24,255));d.line((35,60,49,60),fill=(48,48,56,255))
d.rectangle((30,62,55,63),fill=outline);d.line((31,62,54,62),fill=shade)
# Soot stays local to the opening and flue; no light-gray marker in the black mouth.
d.line((38,43,46,43),fill=(48,48,56,255));wing.save(D/'kiln.png')
# End-facing logs: 8px cut rounds with bark rings, densely staggered and touching.
log=Image.new('RGBA',(8,8));d=ImageDraw.Draw(log)
d.polygon([(2,0),(5,0),(7,2),(7,5),(5,7),(2,7),(0,5),(0,2)],fill=(32,24,24,255))
d.polygon([(2,1),(5,1),(6,2),(6,5),(5,6),(2,6),(1,5),(1,2)],fill=(96,64,24,255))
d.ellipse((1,1,6,6),fill=(168,136,48,255));d.arc((2,2,5,5),20,290,fill=(120,88,24,255));d.line((2,2,3,2),fill=(160,120,40,255));d.point((4,3),fill=(88,48,8,255))
pile=Image.new('RGBA',(64,24))
for row,(y,starts) in enumerate([(16,range(0,64,8)),(8,range(0,64,8)),(0,range(4,60,8))]):
 for i,x in enumerate(starts):pile.alpha_composite(log.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if (row+i)%2 else log,(x,y))
pa=np.array(pile);m=pa[...,3]>0;back=np.zeros(m.shape,bool);back[8:,:]=True;back[:8,4:60]=True;pa[back&~m]=[32,24,24,255];pile=Image.fromarray(pa)
pile.save(D/'firewood-stack.png');log.save(D/'firewood-log.png')
# Preview uses preserved original native layers, not a replay of town authoring.
bg=Image.open(D/'background-before.png').convert('RGBA');fg=Image.open(D/'foreground-before.png').convert('RGBA');fa=np.array(fg);r=json.loads((D/'assembly-before.json').read_text());owners=np.zeros((528,1024),int);tc=np.zeros_like(fa)
for i,p in enumerate(r['placements'],1):
 im=np.array(Image.open(S/'masters'/(p['name']+'.png')).convert('RGBA'));h,w=im.shape[:2];owners[p['y']:p['y']+h,p['x']:p['x']+w][im[...,3]>0]=i
 if p['name']=='tree' and (p['x'],p['y']) not in [(320,96),(304,128)]:tc[p['y']:p['y']+h,p['x']:p['x']+w][im[...,3]>0]=im[im[...,3]>0]
for i,p in enumerate(r['placements'],1):
 if (p['name']=='tree' and (p['x'],p['y']) in [(320,96),(304,128)]) or p['name']=='logs':fa[owners==i]=tc[owners==i]
fg=Image.fromarray(fa);fg.alpha_composite(pile,(272,112));fg.alpha_composite(wing,(256,128));fg.alpha_composite(main,(192,104));out=Image.alpha_composite(bg,fg);out.save(D/'proposal-before-install.png');out.crop((160,64,384,224)).resize((896,640),Image.Resampling.NEAREST).save(D/'proposal-closeup.png')
