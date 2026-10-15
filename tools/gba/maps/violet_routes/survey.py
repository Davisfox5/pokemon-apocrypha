"""Independent HGSS image sampling ledger; not native blockdata or DS collision."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];OUT=ROOT/'gba/art/violet-route-references'
for route in [36,32]:
 source=OUT/f'route{route}-hgss.png';im=Image.open(source).convert('RGB');a=np.asarray(im,int);w,h=im.width//16,im.height//16;r,g,b=a[...,0],a[...,1],a[...,2]
 masks={'woods':(g>r)&(b<80),'ordinary_grass':(g>r+45)&(b>100)&(g>170),'tall_grass':(g>r+35)&(b>50)&(g<175),'water':(b>g+25)&(b>r+40),'path':(r>g+12)&(r>170),'rock':(r>g+20)&(r>90)&(r<205)&(b<130),'roof':(g>r+30)&(b>r+30)&(g<195)&(b>100)}
 ledger=[]
 for y in range(h):
  for x in range(w):
   box=[x*16,y*16,(x+1)*16,(y+1)*16];fractions={k:round(float(m[box[1]:box[3],box[0]:box[2]].mean()),3) for k,m in masks.items()};kind=max(fractions,key=fractions.get)
   if fractions[kind]<.2:kind='needs_manual_review'
   ledger.append({'x':x,'y':y,'reference_box_px':box,'pixel_fractions':fractions,'provisional_category':kind,'native_placement':None,'collision':'not inferred yet'})
 (OUT/f'route{route}-survey.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'grid':'provisional 16px sampling, origin (0,0); registration must be checked before native composition','full_cells':[w,h],'uncovered_right_bottom_px':[im.width-w*16,im.height-h*16],'cells':ledger},indent=2)+'\n')
 board=im.convert('RGBA');grid=Image.new('RGBA',im.size);d=ImageDraw.Draw(grid)
 for x in range(0,w*16+1,16):d.line((x,0,x,h*16),fill=(240,248,255,55))
 for y in range(0,h*16+1,16):d.line((0,y,w*16,y),fill=(240,248,255,55))
 Image.alpha_composite(board,grid).convert('RGB').save(OUT/f'route{route}-sampling-grid.png')
 print(route,w,h,len(ledger))
