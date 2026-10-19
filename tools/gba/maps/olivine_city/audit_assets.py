"""Read-only per-master, per-placement and native-metatile review boards."""
from pathlib import Path
from collections import Counter
import json,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from tiles import Tileset
G=Path(sys.argv[1]);B=ROOT/'gba/art/olivine-city';S=B/'source';T=S/'asset-cleanup';E=B/'evidence/asset-cleanup'
assembly=json.loads((E/'assembly.json').read_text());native=Image.open(E/'native-map.png').convert('RGB');now=np.array(native)
old=Image.open(B/'evidence/forest-refinement/native-map.png').convert('RGB')
ref=Image.open(S/'hgss-reference.png').convert('RGBA');registered=Image.new('RGB',native.size,'#223039');registered.paste(ref,(64,16))
origins={v['name']:v['box'] for v in json.loads((S/'local-asset-provenance.json').read_text()) if 'box' in v};origins['olivine-tree']=[876,264,924,328]
counts=Counter(p['name'] for p in assembly['placements']);masters={};owner=np.zeros(now.shape[:2],np.uint16)
def load(n,previous=False):
 for folder in ([S/'forest-refinement/masters',S/'masters'] if previous else [T/'masters',S/'forest-refinement/masters',S/'masters']):
  p=folder/(n+'.png')
  if p.exists():
   a=np.array(Image.open(p).convert('RGBA'));a[...,:3]&=248;return Image.fromarray(a)
def compare(path,ims,scale=3):
 w=max(im.width for _,im in ims);h=max(im.height for _,im in ims);out=Image.new('RGB',(len(ims)*(w*scale+16)+16,h*scale+48),'#3b4145');d=ImageDraw.Draw(out)
 for i,(label,im) in enumerate(ims):
  x=16+i*(w*scale+16);d.text((x,8),label,fill='white');im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
  out.paste(im,(x,36),im if im.mode=='RGBA' else None)
 out.save(path)
for i,p in enumerate(assembly['placements'],1):
 a=np.array(load(p['name']));masters[p['name']]=a;h,w=a.shape[:2];x,y=p['x'],p['y'];m=a[...,3]>0
 owner[y:y+h,x:x+w][m]=i
instances=[]
for i,p in enumerate(assembly['placements'],1):
 a=masters[p['name']];h,w=a.shape[:2];x,y=p['x'],p['y'];m=owner[y:y+h,x:x+w]==i
 assert np.array_equal(now[y:y+h,x:x+w][m],a[m,:3]),p
 instances.append(dict(**p,visible_pixels=int(m.sum()),native_RGB_errors=0))
inventory=[]
for n in sorted(counts):
 a=Image.fromarray(masters[n]);before=load(n,True)
 if n in ['stairs','ramp']:
  p=next(p for p in assembly['placements'] if p['name']==n);x,y=p['x'],p['y'];before=Image.open(S/'forest-refinement/foreground.png').crop((x,y,x+a.width,y+a.height))
  box=[x-64,y-16,x-64+a.width,y-16+a.height]
 elif n in origins:box=origins[n]
 else:
  p=next(p for p in assembly['placements'] if p['name']==n);x,y=p['source_xy'];box=[x,y,x+a.width,y+a.height]
 compare(E/(n+'-asset-review.png'),[('HGSS reference',ref.crop(box)),('Previous native',before),('Current native master',a)],4)
 inventory.append(dict(name=n,placement_records=counts[n],native_canvas=list(a.size),reference_box=box,master_changed=not np.array_equal(np.array(before),np.array(a)),review_sheet=n+'-asset-review.png'))
for n in ['grass','sand','paving','deck','water']:
 a=load(n);box=origins.get(n,[352,208,352+a.width,208+a.height]);repeat=Image.new('RGBA',(a.width*4,a.height*4))
 for y in range(4):
  for x in range(4):repeat.paste(a,(x*a.width,y*a.height))
 compare(E/(n+'-surface-review.png'),[('HGSS material',ref.crop(box)),('Native core',a),('Native 4 x 4 joins',repeat)],3)
 inventory.append(dict(name=n,role='receiving material',retained=True,review_sheet=n+'-surface-review.png'))
regions=[('northern-rows',(0,0,1152,192)),('western-civic',(0,144,560,416)),('eastern-residences',(544,144,1152,416)),('town-services',(0,400,752,560)),('lighthouse-coast',(688,320,1152,672)),('quay-props',(0,544,768,704)),('harbor',(0,672,1152,896))]
covered=np.zeros(now.shape[:2],bool)
for name,box in regions:
 x,y,x1,y1=box;covered[y:y1,x:x1]=True
 compare(E/(name+'-before-after.png'),[('HGSS',registered.crop(box)),('8eb23f67 before',old.crop(box)),('Current native',native.crop(box))],1 if box[2]-box[0]>800 else 2)
 native.crop(box).resize(((x1-x)*2,(y1-y)*2),Image.Resampling.NEAREST).save(E/(name+'-native-detail.png'))
assert covered.all()
compare(E/'whole-map-before-after.png',[('HGSS',registered),('8eb23f67 before',old),('Current native',native)],1)
pages=[];tiles=[]
for d in assembly['districts']:
 t=Tileset(G,d['tileset'],d['tileset']);grid=np.fromfile(G/'data/layouts'/d['map']/'map.bin','<u2').reshape(d['height'],72)
 ids=sorted(set(map(int,(grid&1023).ravel())))
 for start in range(0,len(ids),192):
  subset=ids[start:start+192];out=Image.new('RGB',(768,768),'#223039');draw=ImageDraw.Draw(out)
  for j,mid in enumerate(subset):
   y,x=np.argwhere((grid&1023)==mid)[0];cx=j%16*48;cy=j//16*64
   out.paste(t.render(mid).resize((48,48),Image.Resampling.NEAREST),(cx,cy));draw.text((cx,cy+48),f'{mid:03X}',fill='white')
   tiles.append(dict(map=d['map'],metatile=mid,native_example=[int(x),int(y)+d['global_y']],instances=int(((grid&1023)==mid).sum())))
  name=f"{d['tileset']}-metatiles-{start//192+1}.png";out.save(E/name);pages.append(name)
(E/'asset-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
(E/'instance-audit.json').write_text(json.dumps(instances,indent=2)+'\n')
(E/'tile-inventory.json').write_text(json.dumps(dict(pages=pages,used_metatiles=tiles,covered_cells=4032,region_review_covers_all_native_pixels=True,regions=[dict(name=n,box=b) for n,b in regions]),indent=2)+'\n')
print(json.dumps(dict(master_families=len(counts),placement_records=len(instances),distinct_placements=len({(p['name'],p['x'],p['y']) for p in instances}),tile_pages=pages,used_metatiles=len(tiles)),indent=2))
