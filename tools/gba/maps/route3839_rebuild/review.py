"""Read-only native audit against original layers and the rebuilt kit ledger."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'));from tiles import Tileset
G=Path(sys.argv[1]);S=ROOT/'gba/art/route38-39-rebuild/source';E=S.parent/'evidence';t=Tileset(G,'route3839_rebuild','route3839_rebuild');cases=[];report=[];images={}
def rows(p,vs):p.write_text('[\n'+',\n'.join(json.dumps(v,separators=(',',':')) for v in vs)+'\n]\n')
def grid(im):
 o=Image.new('RGB',(im.width+32,im.height+32),(32,37,40));o.paste(im,(32,32));d=ImageDraw.Draw(o)
 for x in range(im.width//16+1):
  d.line((32+x*16,32,32+x*16,o.height),fill=(80,105,95))
  if x%4==0:d.text((32+x*16,12),str(x),fill='white')
 for y in range(im.height//16+1):
  d.line((32,32+y*16,o.width,32+y*16),fill=(80,105,95))
  if y%4==0:d.text((4,32+y*16),str(y),fill='white')
 return o
for n,w,h in [(38,64,32),(39,32,64)]:
 g=np.fromfile(G/f'data/layouts/JohtoRoute{n}/map.bin','<u2').reshape(h,w);layers=np.load(S/f'route{n}-layers.npz');ref=np.load(S/f'route{n}-original.npz');im=t.map_image(g.ravel().tolist(),w);im.save(E/f'route{n}-native.png');images[n]=im
 assert np.array_equal(np.array(im),np.array(Image.open(S/f'route{n}-art.png').convert('RGB'))),'Native compiler changed pixels'
 solid=(g&0xc00)!=0;z=g>>12;assert np.array_equal(solid,layers['solid']);assert np.array_equal(z,layers['elevation']);records=[];bad=[];color=Image.new('RGB',im.size);d=ImageDraw.Draw(color);level=Image.new('RGB',im.size);ld=ImageDraw.Draw(level);palette={0:(240,225,140),1:(100,150,200),3:(115,185,155),5:(205,190,120),7:(215,145,90),9:(160,130,195)}
 for y,x in np.ndindex(h,w):
  mid=int(g[y,x]&1023);a=t.attrs[mid>=512][mid%512];assert a&255==0;material=str(layers['material'][y,x]);records.append(dict(x=x,y=y,original_type=int(ref['types'][y,x]),original_collision=int(ref['collision'][y,x]),material=material,blocked=bool(solid[y,x]),elevation=int(z[y,x]),metatile=mid,original_height=round(float(layers['source_height'][y,x]),3),height_defined=bool(layers['source_height_known'][y,x])))
  cl={'L':(112,200,152),'P':(224,200,136),'R':(128,88,56),'O':(184,144,88),'A':(125,185,100),'D':(205,165,105),'S':(170,170,175)}[material];d.rectangle((x*16,y*16,x*16+15,y*16+15),fill=cl);d.text((x*16+4,y*16+2),material,fill=(25,35,30));ld.rectangle((x*16,y*16,x*16+15,y*16+15),fill=(90,65,45) if solid[y,x] else palette[int(z[y,x])]);ld.text((x*16+4,y*16+2),'R' if solid[y,x] else '~' if not z[y,x] else str(round(float(layers['source_height'][y,x]))),fill=(25,30,30))
  if solid[y,x]:continue
  for dx,dy,dr in [(0,-1,'UP'),(0,1,'DOWN'),(-1,0,'LEFT'),(1,0,'RIGHT')]:
   xx,yy=x+dx,y+dy
   if not(0<=xx<w and 0<=yy<h):continue
   if solid[yy,xx]:cases.append(dict(route=n,map=53 if n==38 else 54,x=x,y=y,direction=dr))
   elif z[y,x] and z[yy,xx] and z[y,x]!=z[yy,xx]:bad.append([x,y,xx,yy])
 assert not bad,bad
 rows(E/f'route{n}-native-audit.json',records);grid(im).save(E/f'route{n}-native-grid.png');grid(color).save(E/f'route{n}-material-grid.png');grid(level).save(E/f'route{n}-levels.png');report.append(dict(route=n,cells=w*h,decoded_RGB5_pixels_exact=True,no_forbidden_behavior=True,open_height_seams=0,wall_cells=int((layers['material']=='R').sum())))
rows(E/'boundary-cases.json',cases);(E/'audit.json').write_text(json.dumps(dict(routes=report,boundary_probes=len(cases)),indent=2)+'\n')
a,b=images[39],images[38];o=Image.new('RGB',(1536,1056),(28,33,38));o.paste(a,(0,32));o.paste(b,(512,32));d=ImageDraw.Draw(o);d.text((12,10),'ROUTE39 — native terrain rebuild',fill='white');d.text((524,10),'ROUTE38 — native terrain rebuild',fill='white');o.save(E/'native-overview.png')
# Every used tile has a named source/master role. Keep an editable used kit atlas.
ledger=sum([json.loads((S/f'route{n}-tile-ledger.json').read_text()) for n in [38,39]],[]);names=sorted({x['tile'] for x in ledger if (S/'kit'/(x['tile']+'.png')).exists()});atlas=Image.new('RGBA',(16*16,((len(names)+15)//16)*16));sheet=Image.new('RGB',(16*64,((len(names)+15)//16)*80),(34,40,42));sd=ImageDraw.Draw(sheet)
for i,name in enumerate(names):
 a=Image.open(S/'kit'/(name+'.png')).convert('RGBA');atlas.paste(a,(i%16*16,i//16*16));sheet.paste(a.resize((48,48),Image.Resampling.NEAREST),(i%16*64,i//16*80),a.resize((48,48),Image.Resampling.NEAREST));sd.text((i%16*64,i//16*80+50),str(i),fill='white')
atlas.save(S/'used-kit.png');sheet.save(E/'used-kit-review.png');rows(S/'used-kit-index.json',[dict(index=i,name=n) for i,n in enumerate(names)]);print(report,'boundaries',len(cases),'used kit pieces',len(names))
