"""Group identical changed cells for coordinate-labelled tree cleanup review."""
from PIL import Image,ImageDraw
import numpy as np,json
from pathlib import Path
import sys
p=Path(sys.argv[1]);a=np.array(Image.open(p/'review/before-full.png'));b=np.array(Image.open(p/'review/native-full.png'));groups={}
for y in range(32):
 for x in range(82):
  aa=a[y*16:y*16+16,x*16:x*16+16];bb=b[y*16:y*16+16,x*16:x*16+16]
  if np.array_equal(aa,bb):continue
  key=aa.tobytes()+bb.tobytes()
  if key not in groups:groups[key]={'before':aa,'after':bb,'cells':[]}
  groups[key]['cells'].append([x,y])
g=list(groups.values());print('unique',len(g))
for start in range(0,len(g),48):
 im=Image.new('RGB',(1152,800),'#25323b');d=ImageDraw.Draw(im)
 for k,v in enumerate(g[start:start+48]):
  x=k%8*144;y=k//8*132;d.text((x,y),str(v['cells'][0])+' x'+str(len(v['cells'])),fill='white')
  for j,n in enumerate(['before','after']):im.paste(Image.fromarray(v[n]).resize((64,64),Image.Resampling.NEAREST),(x+j*68,y+20))
 im.save(p/'review'/f'tile-review-{start//48+1}.png')
(p/'evidence/tile-review.json').write_text(json.dumps([{'cells':v['cells'],'sheet':i//48+1,'review':'pending'} for i,v in enumerate(g)],indent=2)+'\n')
