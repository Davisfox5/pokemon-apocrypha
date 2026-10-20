"""Focused immutable first-pass/current/reference review for each asset."""
from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'gba/art/ecruteak-city/source';E=S.parent/'evidence';D=S/'refinement';B=D/'baseline';O=E/'refinement';O.mkdir(exist_ok=True)
now=Image.open(E/'native-map.png').convert('RGB');before=Image.open(B/'native-map.png').convert('RGB');reference=Image.new('RGB',now.size,'#223039');reference.paste(Image.open(S/'hgss-reference.png'),(64,16));assembly=json.loads((E/'assembly.json').read_text());font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
def sheet(name,box,views):
 w,h=box[2]-box[0],box[3]-box[1];im=Image.new('RGB',(len(views)*(w*2+16)+8,h*2+48),'#223039');d=ImageDraw.Draw(im)
 for i,(label,v) in enumerate(views):
  x=8+i*(w*2+16);d.text((x,8),label,font=font,fill='white');im.paste(v.crop(box).resize((w*2,h*2),Image.Resampling.NEAREST),(x,36))
 im.save(O/(name+'.png'))
checked=[]
for name in ['burned-tower','bell-entrance','house','house-entry','house-green','house-southeast','dance-theater','gym','center','mart','south-gate','gate']:
 ps=[p for p in assembly['placements'] if p['name']==name]
 for i,p in enumerate(ps):
  a=Image.open(S/'masters'/(name+'.png'));box=(max(0,p['x']-16),max(0,p['y']-16),min(now.width,p['x']+a.width+16),min(now.height,p['y']+a.height+24));n=name+('-'+str(i+1) if len(ps)>1 else '')
  sheet(n,box,[('HGSS reference',reference),('First pass',before),('Refined native',now)]);checked.append(dict(asset=name,box=list(box),evidence=n+'.png',review='roof silhouette, eave ends, wall planes, windows/doors, footing, receiving court and path seam'))
bare=np.array(Image.open(S/'background.png').convert('RGBA'))
for p in assembly['placements']:
 if p['name'] in ['tree-hgss','maple-hgss','maple-amber','maple-autumn']:continue
 a=np.array(Image.open(S/'masters'/(p['name']+'.png')).convert('RGBA'));a[...,:3]&=248;h,w=a.shape[:2];m=a[...,3]>0;bare[p['y']:p['y']+h,p['x']:p['x']+w][m]=a[m]
bare=Image.fromarray(bare[...,:3]);sheet('rocks-without-canopies',(176,96,536,320),[('HGSS visible / hidden faces uncertain',reference),('Refined without canopies',bare),('Refined with canopies',now)])
sheet('whole-map',(0,0,now.width,now.height),[('First pass',before),('Refined native',now)])
names=['tree','tree-hgss','maple-hgss','maple-amber','maple-autumn'];t=Image.new('RGB',(len(names)*160,264),'#83b78b');d=ImageDraw.Draw(t)
for i,n in enumerate(names):
 a=Image.open(S/'masters'/(n+'.png')).convert('RGBA');d.text((i*160+4,8),n,font=font,fill='#223039');t.paste(a.resize((128,192),Image.Resampling.NEAREST),(i*160+16,48),a.resize((128,192),Image.Resampling.NEAREST))
t.save(O/'tree-masters.png')
(O/'asset-review.json').write_text(json.dumps(dict(buildings=checked,source='HGSS Ecruteak overview',tree_source_masks='../../source/refinement/tree-reconstruction.json',rock_source_catalog='../../source/refinement/shared-rocks/catalog.json',native_ground_repair='Hidden foreground backing restored from preserved independent material layer before mask changes.',review_limits='Original hidden rock planes inferred from neighboring faces; native adaptations remain for owner visual review.'),indent=2)+'\n')
print('Building/placement views:',len(checked))
