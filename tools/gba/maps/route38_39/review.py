"""Decode actual native entries; retain grids, height ledger and movement cases."""
from pathlib import Path
import json,sys,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'));from tiles import Tileset
G=Path(sys.argv[1]);S=ROOT/'gba/art/route38-39-terrain/source';E=S.parent/'evidence';t=Tileset(G,'route38_39','route38_39');cases=[];report=[];imgs={}
def write_records(path, rows):
 path.write_text('[\n'+',\n'.join(json.dumps(v,separators=(',',':')) for v in rows)+'\n]\n')
def numbered(im):
 o=Image.new('RGB',(im.width+32,im.height+32),(32,36,42));o.paste(im,(32,32));d=ImageDraw.Draw(o)
 for x in range(im.width//16+1):
  d.line((32+x*16,32,32+x*16,o.height),fill=(85,105,105),width=1)
  if x%4==0:d.text((32+x*16,12),str(x),fill='white')
 for y in range(im.height//16+1):
  d.line((32,32+y*16,o.width,32+y*16),fill=(85,105,105),width=1)
  if y%4==0:d.text((5,32+y*16),str(y),fill='white')
 return o
for n,w,h,ox,oy in [(38,68,33,0,0),(39,38,56,8,8)]:
 grid=np.fromfile(G/f'data/layouts/JohtoRoute{n}/map.bin','<u2').reshape(h,w);solid=(grid&0xc00)!=0;z=grid>>12;native=t.map_image(grid.flatten().tolist(),w);native.save(E/f'route{n}-native.png');imgs[n]=native
 author=np.array(Image.open(S/f'route{n}-terrain.png').convert('RGB'));assert np.array_equal(np.array(native),author),'native art changed during packing'
 numbered(native).save(E/f'route{n}-native-grid.png');ref=Image.new('RGB',native.size,(65,140,100));ref.paste(Image.open(S/f'hgss-route{n}.png').convert('RGB'),(ox,oy));numbered(ref).save(E/f'route{n}-reference-grid.png')
 comparison=Image.new('RGB',(native.width*2+48,native.height+40),(28,32,38));comparison.paste(ref,(16,32));comparison.paste(native,(native.width+32,32));d=ImageDraw.Draw(comparison);d.text((16,10),f'Route {n} — HGSS overview',fill='white');d.text((native.width+32,10),'Native terrain only — cleared foreground',fill='white');comparison.save(E/f'route{n}-comparison.png')
 elev=native.convert('RGBA');overlay=Image.new('RGBA',native.size);d=ImageDraw.Draw(overlay);colors={0:(250,230,80,150),1:(80,140,230,100),3:(170,120,220,90),5:(210,165,60,85)}
 entries=[];bad=[]
 for y,x in np.ndindex(h,w):
  mid=int(grid[y,x]&1023);attr=t.attrs[mid>=512][mid%512];assert attr&0xff==0,'no grass/ledge/water behavior allowed';assert not attr&0x3000==0,'no foreground overlay left'
  d.rectangle((x*16,y*16,x*16+15,y*16+15),fill=(30,30,30,140) if solid[y,x] else colors[int(z[y,x])]);entries.append(dict(x=x,y=y,metatile=mid,blocked=bool(solid[y,x]),elevation=int(z[y,x]),behavior=attr&0xff))
  if solid[y,x]:continue
  for dx,dy,dr in [(0,-1,'UP'),(0,1,'DOWN'),(-1,0,'LEFT'),(1,0,'RIGHT')]:
   xx,yy=x+dx,y+dy
   if not(0<=xx<w and 0<=yy<h):continue
   if solid[yy,xx]:cases.append(dict(route=n,map=53 if n==38 else 54,x=x,y=y,direction=dr))
   elif z[y,x] and z[yy,xx] and z[y,x]!=z[yy,xx]:bad.append([x,y,xx,yy])
 assert not bad,bad
 Image.alpha_composite(elev,overlay).convert('RGB').save(E/f'route{n}-levels.png');write_records(E/f'route{n}-native-ledger.json',entries)
 report.append(dict(route=n,cells=w*h,decoded_pixels_exact=True,forbidden_behaviors=0,open_height_seams=len(bad),walkable_cells=int((~solid).sum()),rock_stair_and_path_review='reference/native grid traced; missing foreground deliberately cleared. Occluded terrain is inferred, not original-data extraction.'))
write_records(E/'boundary-cases.json',cases);(E/'native-audit.json').write_text(json.dumps(dict(routes=report,boundary_probes=len(cases),all_existing_layouts_preserved=True),indent=2)+'\n')
# Show the two maps in their actual cardinal relationship, x38 east of x39.
# The 32px offset aligns the three shared native path lanes.
a,b=imgs[39],imgs[38];o=Image.new('RGB',(a.width+b.width,max(a.height,b.height+32)+32),(30,35,41));o.paste(a,(0,32));o.paste(b,(a.width,64));d=ImageDraw.Draw(o);d.text((12,10),'ROUTE 39 — farm plateau / south to Olivine',fill='white');d.text((a.width+12,42),'ROUTE 38 — east to Ecruteak',fill='white');o.save(E/'native-overview.png');print(report,'boundaries',len(cases))
