"""Close the bounded restoration worksite and finish the pond approach."""
from pathlib import Path
import json,numpy as np
from PIL import Image
S=Path(__file__).resolve().parents[4]/'gba/art/ecruteak-city/source'
solid=np.load(S/'solid.npy');mat=np.load(S/'material-grid.npy');ground=np.load(S/'ground-material-grid.npy');restricted=[(20,7)]+[(31,y) for y in range(7,17)]
for x,y in restricted:solid[y,x]=True;mat[y,x]='B'
ground[22:24,59:61]='P'
for n,a in [('solid',solid),('material-grid',mat),('ground-material-grid',ground)]:np.save(S/(n+'.npy'),a)
fg=np.array(Image.open(S/'foreground.png'));fg[352:384,944:976]=0;Image.fromarray(fg).save(S/'foreground.png')
(S/'heritage/restricted-worksite.json').write_text(json.dumps(dict(cells=restricted,reason='Non-public pockets enclosed by restoration scaffolding, existing tower walls and fence. No walking access is opened through the conservation worksite.'),indent=2)+'\n')
