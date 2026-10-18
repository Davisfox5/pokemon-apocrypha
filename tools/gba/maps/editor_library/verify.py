"""Check every prefab against its source map and preview; detect source drift."""
import json,hashlib,struct,sys
from pathlib import Path
from PIL import Image,ImageChops
base=Path(sys.argv[1]);results=[]
for mf in base.glob('*/manifest.json'):
 p=mf.parent;m=json.loads(mf.read_text());g=Path(m['project']);prefabs=json.loads((p/'prefabs.json').read_text());look={v['name']:v for v in prefabs};objects=0
 for rel,sha in m['source_sha256'].items():assert hashlib.sha256((g/rel).read_bytes()).hexdigest()==sha,(p.name,rel)
 for r in m['objects']:
  spec=next(v for v in prefabs if v['name']==r['name'] and v['primary_tileset']==next(x for x in json.loads((g/'data/layouts/layouts.json').read_text())['layouts'] if x['name']==r['map']+'_Layout')['primary_tileset'] and v['secondary_tileset']==next(x for x in json.loads((g/'data/layouts/layouts.json').read_text())['layouts'] if x['name']==r['map']+'_Layout')['secondary_tileset'])
  layout=next(x for x in json.loads((g/'data/layouts/layouts.json').read_text())['layouts'] if x['name']==r['map']+'_Layout');raw=(g/layout['blockdata_filepath']).read_bytes();x,y,w,h=r['box']
  for cell in spec['metatiles']:
   i=(y+cell['y'])*layout['width']+x+cell['x'];v=struct.unpack_from('<H',raw,i*2)[0];assert v==cell['metatile_id']|(cell['collision']<<10)|(cell['elevation']<<12)
  source=Image.open(p/'previews'/f'{r["map"]}.png').crop((x*16,y*16,(x+w)*16,(y+h)*16));assert ImageChops.difference(source,Image.open(p/r['preview'])).getbbox() is None;objects+=1
 for v in prefabs:
  assert len({(c['x'],c['y']) for c in v['metatiles']})==len(v['metatiles'])
  for c in v['metatiles']:assert 0<=c['metatile_id']<1024 and 0<=c['collision']<=3 and 0<=c['elevation']<=15 and 0<=c['x']<v['width'] and 0<=c['y']<v['height']
 results.append(dict(package=p.name,objects=objects,selections=len(prefabs),native_source_hashes_unchanged=True,preview_and_collision_match=True))
(base/'validation.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
