from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json
R=Path(__file__).resolve().parents[4];S=R/'gba/art/azalea-town/source';D=S/'kurt-extension';D.mkdir(exist_ok=True)
main=Image.open(S/'masters/kurt.png').convert('RGBA');ma=np.array(main)
# Lower, attached shed-roof wing. Same native straw and wood modules, no scaled house.
wing=Image.new('RGBA',(64,64));d=ImageDraw.Draw(wing)
d.rectangle((0,36,55,62),fill=(56,24,16,255));d.rectangle((0,38,53,60),fill=(88,48,8,255))
# Front wall panels and original-house posts/foundation vocabulary.
for x in [10,30,50]:
 d.rectangle((x,39,x+2,60),fill=(32,24,24,255));d.line((x+3,40,x+3,59),fill=(136,88,8,255))
d.rectangle((0,60,54,63),fill=(32,24,24,255));d.rectangle((0,60,53,62),fill=(96,88,80,255))
for x in [13,29,45]:d.point((x,61),fill=(96,64,24,255))
# One window on the addition, copied at native scale from Kurt's existing window.
window=main.crop((52,68,76,80));wing.alpha_composite(window,(24,47))
# Shallow attached thatch plane; original roof overlaps the high left join.
mask=Image.new('1',(64,64));ImageDraw.Draw(mask).polygon([(0,4),(48,16),(63,32),(63,47),(9,47),(0,39)],fill=1)
wa=np.array(wing);m=np.array(mask,dtype=bool)
# Repeat an intact 16px directional texture core; preserve grain and native glyph reuse.
core=ma[40:56,56:72]
for y,x in np.argwhere(m):wa[y,x]=core[y%16,x%16]
wing=Image.fromarray(wa);d=ImageDraw.Draw(wing)
# Warm shadow at fascia and hip plane, with complete rounded lower corners.
d.line([(0,4),(48,16),(63,32),(63,45),(61,47),(9,47),(0,39)],fill=(32,24,24,255),width=1)
d.line([(1,5),(48,17),(62,33)],fill=(136,104,24,255))
d.line([(1,38),(10,45),(60,45),(62,43)],fill=(96,64,24,255),width=2)
# Right hip is one darker straw plane rather than a raw vertical edge.
a=np.array(wing)
for y in range(19,44):
 for x in range(49,63):
  if x<48+(y-16)*.52 or not m[y,x]:continue
  c=tuple(a[y,x,:3]);mapping={(168,136,48):(160,120,40),(160,120,40):(136,104,24),(136,104,24):(120,88,24)}
  if c in mapping:a[y,x,:3]=mapping[c]
wing=Image.fromarray(a);wing.save(D/'annex.png')
# Broad stacked firewood: staggered rows of sawn logs, native warm wood ramp.
log=Image.new('RGBA',(16,8));d=ImageDraw.Draw(log)
d.polygon([(2,0),(13,0),(15,2),(15,5),(13,7),(2,7),(0,5),(0,2)],fill=(32,24,24,255))
d.rectangle((4,1,13,6),fill=(88,48,8,255));d.line((5,1,12,1),fill=(168,136,48,255));d.line((6,2,14,2),fill=(120,88,24,255));d.line((5,5,13,5),fill=(56,24,16,255))
d.polygon([(2,1),(4,1),(6,3),(6,5),(4,6),(2,6),(1,4),(1,3)],fill=(120,88,24,255));d.line((2,2,4,2),fill=(168,136,48,255));d.line((2,3,2,4),fill=(168,136,48,255));d.point((4,4),fill=(56,24,16,255));d.point((3,5),fill=(88,48,8,255))
pile=Image.new('RGBA',(64,24))
for y,starts in [(16,[0,16,32,48]),(8,[0,16,32,48]),(0,[8,24,40])]:
 for x in starts:pile.alpha_composite(log,(x,y))
from scipy.ndimage import binary_closing
pa=np.array(pile);mask=pa[...,3]>0;holes=binary_closing(mask,structure=np.ones((3,3),bool))&~mask;pa[holes]=[32,24,24,255];pile=Image.fromarray(pa)
pile.save(D/'firewood-stack.png');log.save(D/'firewood-log.png')
# Proposal assembly for close native-scale inspection, before installing source.
bg=Image.open(S/'background.png').convert('RGBA');fg=Image.open(S/'foreground.png').convert('RGBA');fa=np.array(fg)
r=json.loads((S.parent/'evidence/assembly.json').read_text());owners=np.zeros((528,1024),int)
for i,p in enumerate(r['placements'],1):
 im=np.array(Image.open(S/'masters'/(p['name']+'.png')).convert('RGBA'));h,w=im.shape[:2];owners[p['y']:p['y']+h,p['x']:p['x']+w][im[...,3]>0]=i
for i,p in enumerate(r['placements'],1):
 if (p['name']=='tree' and (p['x'],p['y']) in [(320,96),(304,128)]) or p['name']=='logs':fa[owners==i]=0
# Composite the pile/wing behind the original house; never stamp a second house.
fg=Image.fromarray(fa);fg.alpha_composite(pile,(272,112));fg.alpha_composite(wing,(264,128));fg.alpha_composite(main,(192,104));out=Image.alpha_composite(bg,fg);out.save(D/'proposal-before-install.png');out.crop((160,64,384,224)).resize((896,640),Image.Resampling.NEAREST).save(D/'proposal-closeup.png')
