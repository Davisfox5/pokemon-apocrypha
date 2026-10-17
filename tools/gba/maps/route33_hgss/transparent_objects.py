"""Extract only original object pixels; keep terrain out of alpha silhouettes."""
from pathlib import Path
import numpy as np,json
from PIL import Image
from scipy.ndimage import label,binary_fill_holes,binary_dilation
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'gba/art/route33-hgss/source';O=S/'transparent-objects';O.mkdir(exist_ok=True);ref=np.array(Image.open(S/'hgss-reference.png').convert('RGB'))
report={'approved_tree_masters':'T01/T03/T04 from pinned hub 3d593788; do not regenerate or substitute','objects':[]}
for name,box in [('boulder-west',(52,224,88,260)),('boulder-east',(438,148,474,184))]:
 x0,y0,x1,y1=box;a=ref[y0:y1,x0:x1].copy();r,g,b=a.astype(int).transpose(2,0,1);warm=(r>g+4)&(g>b+4);cut=5 if name.endswith('west') else 8;warm[:cut]=False;lab,n=label(warm);counts=np.bincount(lab.ravel());counts[0]=0;body=binary_fill_holes(lab==counts.argmax());rim=binary_dilation(body)&~body;mask=body|(rim&(a.max(2)<150)&(np.ptp(a.astype(int),axis=2)<60));mask[:cut]=False;out=np.dstack([a,mask.astype(np.uint8)*255]);out[~mask,:3]=0;Image.fromarray(out).save(O/(name+'.png'));report['objects'].append({'name':name,'source_box':box,'opaque_pixels':int(mask.sum())})
(O/'provenance.json').write_text(json.dumps(report,indent=2)+'\n')
