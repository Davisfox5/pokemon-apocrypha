"""Source / clean receiving terrain / final native repair evidence."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
R=Path(__file__).resolve().parents[4];S=R/'gba/art/olivine-city/source';O=S.parent/'evidence/middle-ground';A=S/'middle-ground';font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
ref=Image.open(S/'hgss-reference.png').convert('RGB');clean=Image.open(A/'cleaned-ground.png').convert('RGB');native=Image.open(O/'after.png').convert('RGB')
crops=[('West residence / reconstructed fence',(232,256,456,376)),('Mart / preserved lamp / street shoulder',(440,376,576,504)),('Lighthouse / forest, lawn and independent sign',(664,336,832,560)),('Boat / complete quay railing / water',(232,592,344,696)),('Terminal / deck and water beneath roof',(296,672,488,840)),('Gym / hidden rear railing',(168,136,320,264))]
for i,(name,b) in enumerate(crops,1):
 w,h=b[2]-b[0],b[3]-b[1];out=Image.new('RGB',(w*6,h*2+65),'#182028');d=ImageDraw.Draw(out);d.text((8,5),name+' — world px '+str(b),font=font,fill='white')
 for j,(label,im) in enumerate([('HGSS source',ref),('Clean receiving ground',clean),('Final native placement',native)]):
  d.text((j*w*2+8,30),label,font=font,fill='white');out.paste(im.crop(b).resize((w*2,h*2),Image.Resampling.NEAREST),(j*w*2,65))
 out.save(O/f'{i:02}-context.png')
# Preserve a full clean background and show the actual map at native resolution.
clean.save(O/'cleaned-ground.png')
comparison=Image.new('RGB',(2080,900),'#182028');d=ImageDraw.Draw(comparison);d.text((10,8),'Rejected generic terrain',font=font,fill='white');d.text((1050,8),'HGSS terrain + repaired receiving contexts + polished masters',font=font,fill='white');comparison.paste(Image.open(O/'before.png'),(0,36));comparison.paste(native,(1040,36));comparison.save(O/'comparison.png')
print('Wrote six source / cleaned ground / native context sheets')
