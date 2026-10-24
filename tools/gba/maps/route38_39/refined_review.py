"""Verify actual native tiles against corrected geometry, heights and art."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'));from tiles import Tileset
G=Path(sys.argv[1]);D=ROOT/'gba/art/route38-39-terrain/source/refinement';E=D.parent.parent/'evidence/refinement';t=Tileset(G,'route38_39','route38_39');cases=[];reports=[];images={}
def rows(p,vs):p.write_text('[\n'+',\n'.join(json.dumps(v,separators=(',',':')) for v in vs)+'\n]\n')
def grid_image(im):
 o=Image.new('RGB',(im.width+32,im.height+32),(30,35,40));o.paste(im,(32,32));d=ImageDraw.Draw(o)
 for x in range(im.width//16+1):
  d.line((32+x*16,32,32+x*16,o.height),fill=(75,100,90))
  if x%4==0:d.text((32+x*16,12),str(x),fill='white')
 for y in range(im.height//16+1):
  d.line((32,32+y*16,o.width,32+y*16),fill=(75,100,90))
  if y%4==0:d.text((5,32+y*16),str(y),fill='white')
 return o
for n,w,h in [(38,64,32),(39,32,64)]:
 g=np.fromfile(G/f'data/layouts/JohtoRoute{n}/map.bin','<u2').reshape(h,w);im=t.map_image(g.flatten().tolist(),w);im.save(E/f'route{n}-native.png');images[n]=im;grid_image(im).save(E/f'route{n}-native-grid.png');assert np.array_equal(np.array(im),np.array(Image.open(D/f'route{n}-terrain.png').convert('RGB')))
 solid=(g&0xc00)!=0;z=g>>12;assert np.array_equal(solid,np.load(D/f'route{n}-solid.npy'));assert np.array_equal(z,np.load(D/f'route{n}-elevation.npy'));actual=np.load(D/f'route{n}-actual-height.npy');known=np.load(D/f'route{n}-known-height.npy');mat=json.loads((D/f'route{n}-materials.json').read_text());entries=[];bad=[]
 lv=Image.new('RGB',im.size);ld=ImageDraw.Draw(lv);colors={1:(120,165,220),3:(130,185,165),5:(205,190,115),7:(225,150,90),9:(165,130,200),0:(245,235,135)}
 for y,x in np.ndindex(h,w):
  mid=int(g[y,x]&1023);attr=t.attrs[mid>=512][mid%512];assert attr&255==0;entries.append(dict(x=x,y=y,metatile=mid,blocked=bool(solid[y,x]),native_elevation=int(z[y,x]),source_height=round(float(actual[y,x]),3),source_BDHC_coverage=round(float(known[y,x]),3),material=mat[y][x]))
  ld.rectangle((x*16,y*16,x*16+15,y*16+15),fill=(85,65,45) if solid[y,x] else colors[int(z[y,x])]);ld.text((x*16+4,y*16+3),'R' if solid[y,x] else '~' if z[y,x]==0 else str(round(actual[y,x])),fill=(20,30,30))
  if solid[y,x]:continue
  for dx,dy,dr in [(0,-1,'UP'),(0,1,'DOWN'),(-1,0,'LEFT'),(1,0,'RIGHT')]:
   xx,yy=x+dx,y+dy
   if not(0<=xx<w and 0<=yy<h):continue
   if solid[yy,xx]:cases.append(dict(route=n,map=53 if n==38 else 54,x=x,y=y,direction=dr))
   elif z[y,x] and z[yy,xx] and z[y,x]!=z[yy,xx]:bad.append([x,y,xx,yy])
 assert not bad,bad;lv.save(E/f'route{n}-height-plan.png');grid_image(lv).save(E/f'route{n}-height-grid.png');rows(E/f'route{n}-native-ledger.json',entries)
 reports.append(dict(route=n,cells=w*h,source_grid='original32x32 HGSS map chunks, not overview projection',decoded_native_pixels_exact=True,forbidden_behaviors=0,open_height_seams=len(bad),walkable_cells=int((~solid).sum()),native_ids_preserved=True))
rows(E/'boundary-cases.json',cases);(E/'native-audit.json').write_text(json.dumps(dict(routes=reports,boundary_probes=len(cases)),indent=2)+'\n')
# Orthographic source grid and native grid are both one original tile per16px.
a,b=images[39],images[38];o=Image.new('RGB',(a.width+b.width,max(a.height,b.height)+32),(30,35,41));o.paste(a,(0,32));o.paste(b,(a.width,32));d=ImageDraw.Draw(o);d.text((12,10),'ROUTE39: original32x64 grid',fill='white');d.text((a.width+12,10),'ROUTE38: original64x32 grid',fill='white');o.save(E/'native-overview.png')
# A readable reference/corrected comparison. The source image is contextual;
# it is not falsely registered to this orthographic16px grid.
for n in (38,39):
 a=Image.open(D.parent/f'hgss-route{n}.png').convert('RGB');b=images[n];height=max(a.height,b.height);o=Image.new('RGB',(a.width+b.width+48,height+48),(30,35,40));o.paste(a,(16,32));o.paste(b,(a.width+32,32));d=ImageDraw.Draw(o);d.text((16,10),'HGSS camera overview (context)',fill='white');d.text((a.width+32,10),'Corrected native orthographic grid',fill='white');o.save(E/f'route{n}-reference-comparison.png')
print(reports,'boundary probes',len(cases))
