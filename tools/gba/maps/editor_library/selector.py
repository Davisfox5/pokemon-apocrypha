"""Build a spatial selector sheet without changing native tile IDs.
Whole objects remain rectangular and adjacent. Unclassified used entries are omitted
from this review prototype and remain available via the eyedropper.
"""
import json,sys,math,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));from tiles import Tileset
package=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
m=json.loads((package/'manifest.json').read_text());g=Path(m['project']);pf=json.loads((package/'prefabs.json').read_text());layouts=json.loads((g/'data/layouts/layouts.json').read_text())['layouts'];specs={};reports=[]
for record in m['maps']:
 name=record['map'];l=next(v for v in layouts if v['name']==name+'_Layout');t=Tileset(g,record['tilesets'][1],record['tilesets'][0]);width=24;rows=[];heads=[];labels=[];shown=set();objects=0
 def newrows(n):
  y=len(rows);rows.extend([[-1]*width for _ in range(n)]);return y
 def heading(title):y=newrows(1);heads.append({'row':y,'title':title});return y
 def put(mid,x,y):rows[y][x]=mid;shown.add(mid)
 objs=[r for r in m['objects'] if r['map']==name]
 for cat in sorted({r['name'].split(' | ')[0] for r in objs}):
  heading(cat[3:]);x=0;y=newrows(1);shelf=0
  for obj in [r for r in objs if r['name'].startswith(cat+' | ')]:
   b=next(v for v in pf if v['name']==obj['name'] and v['primary_tileset']==l['primary_tileset'] and v['secondary_tileset']==l['secondary_tileset']);bw,bh=b['width'],b['height'];space=max(bw,6)
   if bw>width:continue
   if x+space>width:y=newrows(1);x=0;shelf=0
   if len(rows)<y+1+bh:newrows(y+1+bh-len(rows))
   labels.append({'row':y,'column':x,'width':space,'title':obj['name'].split(' | ',1)[1]})
   for cell in b['metatiles']:put(cell['metatile_id'],x+cell['x'],y+1+cell['y'])
   x+=space+1;shelf=max(shelf,bh);objects+=1
  newrows(1)
 # Native material-only entries: exclude palette combinations belonging to
 # tree canopies/buildings/props, even if these fragments happen to be walkable.
 grid=np.fromfile(g/l['blockdata_filepath'],'<u2');used=set(map(int,grid&1023));groups={}
 for mid in sorted(used-shown):
  entries=t.blocks[mid>=512][mid%512];banks=set()
  for e in entries:
   tid=e&1023;raw=t.tiles[tid>=512][tid%512]
   if any(raw):banks.add(e>>12)
  beh=t.attrs[mid>=512][mid%512]&255
  group=None
  if banks and banks<={0}:group='Ground and path transitions'
  elif banks and banks<={0,1} and beh in range(0x10,0x20):group='Water and shore transitions'
  elif banks and banks<={0,2}:group='Rock material pieces'
  elif beh==2 and banks<={0,11}:group='Tall grass edges'
  if group:groups.setdefault(group,[]).append(mid)
 for group,ids in groups.items():
  heading(group);y=newrows(math.ceil(len(ids)/width))
  for i,mid in enumerate(ids):put(mid,i%width,y+i//width)
 sources={k:v for k,v in m['source_sha256'].items() if '/tilesets/' in k and any('/'+side+'/'+d+'/' in k for side,d in zip(['primary','secondary'],record['tilesets']))}
 spec={'width':width,'primary':l['primary_tileset'],'secondary':l['secondary_tileset'],'sources':sources,'cells':sum(rows,[]),'headings':heads,'labels':labels}
 specs[l['id']]=spec
 im=Image.new('RGB',(width*16,len(rows)*16),(38,44,50));d=ImageDraw.Draw(im)
 for y,row in enumerate(rows):
  for x,mid in enumerate(row):
   if mid>=0:im.paste(t.render(mid),(x*16,y*16))
 for v in heads:d.rectangle((0,v['row']*16,width*16,v['row']*16+15),fill=(55,71,81));d.text((4,v['row']*16+2),v['title'],fill='white')
 for v in labels:d.text((v['column']*16+1,v['row']*16+3),v['title'][:v['width']*2],fill='#b7d8e8')
 im.save(out/(name+'-selector.png'));reports.append(dict(map=name,objects=objects,visible_unique_ids=len(shown),hidden_used_ids=len(used-shown),native_ids_unchanged=True))
(out/'porymap.selector.json').write_text(json.dumps({'version':1,'layouts':specs},indent=2)+'\n');(out/'report.json').write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(reports))
