import subprocess,json,re,tarfile,io,sys
from pathlib import Path
repo=Path(__import__('os').environ.get('JOHTO_SOURCE','/Users/davisfox/Documents/GitHub/apocrypha-src'));out=Path(sys.argv[2]);out.mkdir(exist_ok=True)
rev=sys.argv[1]
paths=['data/layouts/layouts.json','src/data/tilesets/graphics.h']
raw=subprocess.check_output(['git','show',rev+':data/layouts/layouts.json'],cwd=repo);ls=json.loads(raw)['layouts'];gh=subprocess.check_output(['git','show',rev+':src/data/tilesets/graphics.h'],cwd=repo).decode()
names=sys.argv[3:]
for l in ls:
 if l['name'].removesuffix('_Layout') not in names:continue
 paths.extend([l['blockdata_filepath'],l['border_filepath']])
 for side in ['primary','secondary']:
  sym='gTilesetTiles_'+l[side+'_tileset'].removeprefix('gTileset_');m=re.search(re.escape(sym)+r'\[\].*?"(data/tilesets/'+side+r'/[^/]+)/tiles.png"',gh,re.S);paths.append(m[1])
raw=subprocess.check_output(['git','archive',rev,*sorted(set(paths))],cwd=repo)
with tarfile.open(fileobj=io.BytesIO(raw)) as tf:tf.extractall(out,filter='data')
