"""Readable isolated assets and HGSS/rejected/rebuilt receiving-context sheets.
Reads references for comparison only; never authors or changes native source.
"""
from pathlib import Path
import json
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[4];S=R/'gba/art/olivine-city/source';A=S/'rebuilt';E=S.parent/'evidence';O=E/'rebuild';M=A/'masters';D=A/'modules'
ref=Image.open(S/'hgss-reference.png').convert('RGB');before=Image.open(O/'before.png').convert('RGB');after=Image.open(E/'native-map.png').convert('RGB')
def checker(w,h):
 a=Image.new('RGB',(w,h),'#dbe1df');d=ImageDraw.Draw(a)
 for y in range(0,h,8):
  for x in range(0,w,8):
   if (x//8+y//8)%2:d.rectangle((x,y,x+7,y+7),fill='#b5c2c1')
 return a
def comparison(tag,box):
 w,h=box[2]-box[0],box[3]-box[1];im=Image.new('RGB',(w*6,h*2+28),'#1f2d35');d=ImageDraw.Draw(im)
 for i,(label,a) in enumerate([('HGSS reference',ref),('Rejected first pass',before),('Rebuilt native',after)]):d.text((i*w*2+4,6),f'{label} / {box}',fill='white');im.paste(a.crop(box).resize((w*2,h*2),Image.Resampling.NEAREST),(i*w*2,28))
 im.save(O/(tag+'.png'))
comparisons={
 'gym':(160,128,328,272),'residences':(480,160,672,304),'cafe':(120,376,240,504),'lighthouse':(664,320,840,552),'ferry-terminal':(272,672,488,848),
 'service-buildings-and-lamp':(224,368,568,512),'festival-gate':(88,256,464,352),'upper-stairs':(528,272,688,368),'lighthouse-ramp-coast':(576,512,896,672),'northern-grove':(512,48,840,224),'promenade':(104,528,632,656)
}
for tag,box in comparisons.items():comparison(tag,box)
sheet=Image.new('RGB',(1080,800),'#20313b');d=ImageDraw.Draw(sheet)
for i,name in enumerate(['gym','house','cafe','lighthouse','terminal','sailboat']):
 x=i%3*360;y=i//3*400;d.text((x+12,y+8),name+' / isolated native RGBA',fill='white');a=Image.open(M/(name+'-native.png' if (M/(name+'-native.png')).is_file() else name+'.png')).convert('RGBA')
 c=checker(*a.size);c.paste(a,(0,0),a.getchannel('A'));c=c.resize((c.width*2,c.height*2),Image.Resampling.NEAREST);sheet.paste(c,(x+(360-c.width)//2,y+36))
sheet.save(O/'isolated-native-assets.png')
names=['water','paving','lawn','sand','dock','cliff-face','cliff-cap','curb','fence','lamp','sign','parasol-table','stairs','ramp','shore-rock'];sheet=Image.new('RGB',(1000,3*290),'#20313b');d=ImageDraw.Draw(sheet)
for i,n in enumerate(names):
 x=i%5*200;y=i//5*290;d.text((x+8,y+8),n,fill='white');a=Image.open(D/(n+'.png')).convert('RGBA');c=checker(*a.size);c.paste(a,(0,0),a.getchannel('A'));scale=min(4,180//a.width,250//a.height);c=c.resize((c.width*scale,c.height*scale),Image.Resampling.NEAREST);sheet.paste(c,(x+(200-c.width)//2,y+32))
sheet.save(O/'terrain-and-prop-modules.png')
# Whole-city comparison preserves full-scale originals separately.
sheet=Image.new('RGB',(2080,892),'#20313b');d=ImageDraw.Draw(sheet);d.text((8,7),'Rejected overview-based first pass',fill='white');d.text((1048,7),'Rebuilt city / independent assets',fill='white');sheet.paste(before,(0,28));sheet.paste(after,(1040,28));sheet.save(O/'before-after.png')
(O/'visual-review.json').write_text(json.dumps(dict(contexts=comparisons,findings=['Replaced all overview terrain and source foliage.','Reusable complete building/prop masters with independent ground.','Protected residence/cafe blue glass and yellow/blue flags.','Aligned actual festival gate; blocked railings, stair shoulders and rock faces.','Relocated Mart-adjacent lamp and Lighthouse sign; canonical service art remains exact.','Mixed canopy/roof quadrants split across layers to retain canonical visible tree pixels.','Native terrain completion at partial path, quay and pier edges recorded explicitly.'],owner_visual_acceptance='Pending',limits=['Static scenery; native-grid contour/projection adaptations, not extracted DS heights.','Rock/sea/paving are compact repeated native material cores; no animated water or ride/service systems.']),indent=2)+'\n')
