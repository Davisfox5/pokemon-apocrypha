"""Rebuild only the arch's receiving grass/forest join before native packing."""
from pathlib import Path
import numpy as np,json
from PIL import Image
S=Path(__file__).resolve().parents[4]/'gba/art/ecruteak-city/source';E=S.parent/'evidence';r=json.loads((E/'assembly.json').read_text());bg=np.array(Image.open(S/'background.png'));fg=np.array(Image.open(S/'foreground.png'));x,y,xx,yy=624,688,720,752;grass=np.array(Image.open(S/'masters/grass.png').convert('RGBA'));Y,X=np.indices((yy-y,xx-x));bg[y:yy,x:xx]=grass[(Y+y-16)%32,(X+x-64)%32];fg[y:yy,x:xx]=0
for p in r['placements']:
 a=np.array(Image.open(S/'masters'/(p['name']+'.png')).convert('RGBA'));h,w=a.shape[:2];l=max(x,p['x']);t=max(y,p['y']);rr=min(xx,p['x']+w);bb=min(yy,p['y']+h)
 if l>=rr or t>=bb:continue
 v=a[t-p['y']:bb-p['y'],l-p['x']:rr-p['x']];m=v[...,3]>0;fg[t:bb,l:rr][m]=v[m]
for n,a in [('background',bg),('foreground',fg)]:Image.fromarray(a).save(S/(n+'.png'))
