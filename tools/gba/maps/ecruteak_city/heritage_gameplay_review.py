"""Check complete native fixture pixels against real mGBA screenshot output."""
from pathlib import Path
import json,sys,hashlib,numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'gba/art/ecruteak-city/source';R=Path(sys.argv[1]);E=S.parent/'evidence/heritage';E.mkdir(exist_ok=True);screen=np.array(Image.open(R/'heritage-overview.png').convert('RGB'))&248;proof=[]
for n in ['heritage-shrine','offering-counter']:
 a=np.array(Image.open(S/'masters'/(n+'.png')).convert('RGBA'));m=a[...,3]>0;h,w=a.shape[:2];ys,xs=np.where(m);anchors=list(zip(ys[::max(1,len(ys)//12)],xs[::max(1,len(xs)//12)]))[:12];matches=[]
 for y in range(161-h):
  for x in range(241-w):
   if all(np.array_equal(screen[y+yy,x+xx],a[yy,xx,:3]) for yy,xx in anchors) and np.array_equal(screen[y:y+h,x:x+w][m],a[m,:3]):matches.append([x,y])
 assert len(matches)==1,(n,matches);proof.append(dict(master=n,full_visible_opaque_pixels=int(m.sum()),RGB5_errors=0,screen_position=matches[0]))
result=json.loads((R/'results.json').read_text());assert all(p['exit_code']==0 for p in result['phases']);(E/'native-object-pixels.json').write_text(json.dumps(dict(rom_sha256=result['rom_sha256'],frame='heritage-overview.png',proof=proof),indent=2)+'\n');print(proof)
