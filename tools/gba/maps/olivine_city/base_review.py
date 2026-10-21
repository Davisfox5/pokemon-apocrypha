"""Decode every native terrain metatile and compare actual Porymap exports."""
from pathlib import Path
from collections import deque
import sys,json,csv
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[4];G=Path(sys.argv[1]);P=Path(sys.argv[2]);sys.path.insert(0,str(R/'tools/gba/maps'));from tiles import Tileset
S=R/'gba/art/olivine-city/source';A=S/'base-terrain';E=S.parent/'evidence';O=E/'base-terrain';sections=json.loads((E/'sections.json').read_text());solid=np.load(A/'solid.npy');mat=np.load(A/'material.npy');ids=np.load(A/'metatile-map.npy');height=np.load(A/'height.npy');native=Image.new('RGB',(1040,864));rows=[]
for sec in sections:
 n=sec['name'];x,y,x1,y1=sec['box'];t=Tileset(G,n.lower(),n.lower());grid=np.fromfile(G/f'data/layouts/{n}/map.bin','<u2').reshape(y1-y,x1-x);im=t.map_image(list(map(int,grid.ravel())),x1-x)
 assert np.array_equal(grid>>12, (height[y:y1,x:x1]*2+3));assert np.array_equal(grid&1023,ids[y:y1,x:x1]);assert np.array_equal(grid&0xc00!=0,solid[y:y1,x:x1]);assert all(t.attrs[int(i>=512)][int(i%512)]==0x1000 for i in np.unique(grid&1023))
 export=Image.open(P/(n+'.png')).convert('RGB');assert export.size==im.size;err=int(np.any(np.array(export)!=np.array(im),2).sum());assert not err,(n,err);rows.append(dict(map=n,pixels=im.width*im.height,RGB_errors=err));native.paste(im,(x*16,y*16))
assert np.array_equal(np.array(native),np.array(Image.open(A/'assembled-preview.png')))
seen=set();components=[];reachable=set()
for start in [(24,32)]+[(int(x),int(y)) for y,x in np.argwhere(~solid)]:
 if start in seen:continue
 c={start};q=deque(c);seen.add(start)
 while q:
  x,y=q.popleft()
  for xx,yy in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
   if 0<=xx<65 and 0<=yy<54 and not solid[yy,xx] and (xx,yy) not in seen:seen.add((xx,yy));c.add((xx,yy));q.append((xx,yy))
 components.append(dict(start=list(start),cells=len(c),city_component=start==(24,32)))
 if start==(24,32):reachable=c
native.save(E/'native-map.png');native.save(O/'native-map.png');native.resize((2080,1728),Image.Resampling.NEAREST).save(E/'native-map-2x.png')
for name in ['native-grid','collision-review']:
 im=native.convert('RGBA');over=Image.new('RGBA',im.size);d=ImageDraw.Draw(over)
 if name=='collision-review':
  for y,x in np.argwhere(solid):d.rectangle((int(x)*16,int(y)*16,int(x)*16+15,int(y)*16+15),fill=(255,20,50,75))
 for x in range(0,66,4):d.line((x*16,0,x*16,864),fill=(240,240,255,110));d.text((x*16+1,0),str(x),fill='black')
 for y in range(0,55,4):d.line((0,y*16,1040,y*16),fill=(240,240,255,110));d.text((0,y*16+1),str(y),fill='black')
 Image.alpha_composite(im,over).convert('RGB').save(O/(name+'.png'));Image.alpha_composite(im,over).convert('RGB').save(E/(name+'.png'))
with (O/'cell-ledger.csv').open('w') as f:
 w=csv.writer(f,lineterminator="\n");w.writerow(['x','y','metatile','material','solid','city_reachable'])
 for y,x in np.ndindex(54,65):w.writerow([x,y,int(ids[y,x]),str(mat[y,x]),int(solid[y,x]),int((x,y) in reachable)])
report=dict(cells=3510,native_RGB_errors=0,porymap=rows,components=components,stairs=0,foreground_objects=0)
(O/'review.json').write_text(json.dumps(report,indent=2)+'\n');(E/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
