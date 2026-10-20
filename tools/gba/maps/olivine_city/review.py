"""Independent native decode, shared-master, traversal and context review."""
from pathlib import Path
import sys,json,hashlib,csv
from collections import deque
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[4];G=Path(sys.argv[1]);P=Path(sys.argv[2]) if len(sys.argv)>2 else None;S=R/'gba/art/olivine-city/source';E=S.parent/'evidence'
sys.path.insert(0,str(R/'tools/gba/maps'));from tiles import Tileset
sections=json.loads((E/'sections.json').read_text());solid=np.load(S/'solid.npy');mat=np.load(S/'material.npy');above=np.load(S/'above.npy');H,W=solid.shape;native=Image.new('RGB',(W*16,H*16));actual=np.zeros_like(solid);porymap=[]
for sec in sections:
 n=sec['name'];x,y,x1,y1=sec['box'];t=Tileset(G,n.lower(),n.lower());grid=np.fromfile(G/f'data/layouts/{n}/map.bin','<u2').reshape(y1-y,x1-x)
 im=t.map_image(list(map(int,grid.ravel())),x1-x);native.paste(im,(x*16,y*16));actual[y:y1,x:x1]=grid&0xc00!=0
 if P:
  export=Image.open(P/(n+'.png')).convert('RGB');assert export.size==im.size;err=int(np.any(np.array(export)!=np.array(im),2).sum());assert err==0,(n,err);porymap.append(dict(name=n,pixels=im.width*im.height,RGB_errors=err))
assert np.array_equal(actual,solid),'Native collision differs from independent ledger'
bg=np.array(Image.open(S/'native-ground.png').convert('RGB'));fg=np.array(Image.open(S/'shared-foreground.png').convert('RGBA'));expected=bg.copy();m=fg[...,3]>0;expected[m]=fg[m,:3];a=np.array(native);assert np.array_equal(a,expected),'Native source differs from intended layers'
native.save(E/'native-map.png');native.resize((W*32,H*32),Image.Resampling.NEAREST).save(E/'native-map-2x.png')
seen={(24,32)};todo=deque(seen)
while todo:
 x,y=todo.popleft()
 for xx,yy in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
  if 0<=xx<W and 0<=yy<H and not solid[yy,xx] and (xx,yy) not in seen:seen.add((xx,yy));todo.append((xx,yy))
features=json.loads((S/'features.json').read_text());approaches=[]
for f in features:
 x,y=f['door_approach'];approaches.append(dict(name=f['name'],approach=[x,y],open=not bool(solid[y,x]),reachable=(x,y) in seen))
# Coordinate labelled per-building context sheets, including receiving terrain.
ref=Image.open(S/'hgss-reference.png').convert('RGB');contexts=[]
for i,f in enumerate(features):
 x0,y0,x1,y1=f['reference_box'];box=(max(0,x0-32),max(0,y0-24),min(W*16,x1+32),min(H*16,y1+32));w,h=box[2]-box[0],box[3]-box[1];sheet=Image.new('RGB',(w*4,h*2+28),(24,32,40));d=ImageDraw.Draw(sheet);d.text((4,6),f'{f["name"]} — HGSS | native; world px {box}',fill='white');sheet.paste(ref.crop(box).resize((w*2,h*2),Image.Resampling.NEAREST),(0,28));sheet.paste(native.crop(box).resize((w*2,h*2),Image.Resampling.NEAREST),(w*2,28));p=E/'building-contexts';p.mkdir(exist_ok=True);sheet.save(p/f'{i+1:02}.png');contexts.append(dict(name=f['name'],box=box,evidence=f'building-contexts/{i+1:02}.png'))
# Shared art exactness is checked at actual placements, not just input hashes.
shared=[]
placements=[('center',240,400),('mart',464,416)]+[('tree',x,y) for x,y in json.loads((S/'trees.json').read_text())]
for order,(name,x,y) in enumerate(placements):
 master=np.array(Image.open(S/'masters'/(name+'.png')).convert('RGBA'));master[...,:3]&=248;h,w=master.shape[:2];m=master[...,3]>0
 # Check only visible pixels; neighboring complete canopies may overlap, while
 # their independently recorded root footprints remain distinct.
 for nn,xx,yy in placements[order+1:]:
  other=np.array(Image.open(S/'masters'/(nn+'.png')).convert('RGBA'));hh,ww=other.shape[:2];left=max(x,xx);top=max(y,yy);right=min(x+w,xx+ww);bottom=min(y+h,yy+hh)
  if left<right and top<bottom:m[top-y:bottom-y,left-x:right-x]&=other[top-yy:bottom-yy,left-xx:right-xx,3]==0
 if name=='tree' and (S/'rebuilt/placements.json').is_file():
  for nn,xx,yy,bank,facade in json.loads((S/'rebuilt/placements.json').read_text())['buildings']:
   other=np.array(Image.open(S/'rebuilt/masters'/(nn+'-native.png')).convert('RGBA'));hh,ww=other.shape[:2];left=max(x,xx);top=max(y,yy);right=min(x+w,xx+ww);bottom=min(y+h,yy+hh)
   if left<right and top<bottom:m[top-y:bottom-y,left-x:right-x]&=other[top-yy:bottom-yy,left-xx:right-xx,3]==0
 err=int(np.any(a[y:y+h,x:x+w,:][m]!=master[...,:3][m],1).sum());assert not err,(name,x,y,err);shared.append(dict(name=name,origin=[x,y],opaque_pixels=int(m.sum()),RGB_errors=err))
# Grid/collision views retain readable source underneath overlays.
for label,base in [('reference-grid',ref),('native-grid',native),('collision-review',native)]:
 im=base.copy().convert('RGBA');overlay=Image.new('RGBA',im.size);d=ImageDraw.Draw(overlay)
 for y,x in np.ndindex(H,W):
  if label=='collision-review' and solid[y,x]:d.rectangle((x*16,y*16,x*16+15,y*16+15),fill=(255,20,50,75))
 for x in range(0,W+1,4):d.line((x*16,0,x*16,H*16),fill=(240,240,255,90));d.text((x*16+1,0),str(x),fill=(0,0,0,255))
 for y in range(0,H+1,4):d.line((0,y*16,W*16,y*16),fill=(240,240,255,90));d.text((0,y*16+1),str(y),fill=(0,0,0,255))
 Image.alpha_composite(im,overlay).convert('RGB').save(E/(label+'.png'))
with (E/'cell-ledger.csv').open('w') as out:
 w=csv.writer(out,lineterminator="\n");w.writerow(['x','y','material','solid','upper_layer','reachable'])
 for y,x in np.ndindex(H,W):w.writerow([x,y,mat[y,x],int(solid[y,x]),int(above[y,x]),int((x,y) in seen)])
report=dict(cells=W*H,native_RGB_errors=0,porymap=porymap,approaches=approaches,reachable_cells=len(seen),shared=shared,contexts=contexts)
(E/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(approaches,indent=2));assert all(f['reachable'] and f['open'] for f in approaches),'Fix real native approaches before building'
