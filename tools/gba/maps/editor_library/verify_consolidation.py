"""Check assembled maps against native Porymap exports and pinned source previews."""
import sys,json,re,subprocess,hashlib
from pathlib import Path
from PIL import Image,ImageChops
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));from tiles import Tileset
hub=Path(__file__).resolve().parents[4];dest=Path(sys.argv[1]);out=hub/'gba/art/johto-common/editor-consolidation';layouts=json.loads((dest/'data/layouts/layouts.json').read_text())['layouts'];graphics=(dest/'src/data/tilesets/graphics.h').read_text();carry=json.loads((out/'owner-edit-carry.json').read_text());owner=Path('/Users/davisfox/Documents/GitHub/apocrypha-src');ot=Tileset(owner,'claude_route30','cherrygrove');records=[]
mapping={'NewBarkTown':'latest','CherrygroveCity':'latest','VioletCity':'latest','JohtoRoute31':'latest','JohtoRoute36':'latest','CherrygroveRoute29Approach':'route29','CherrygroveRoute30Approach':'route30','JohtoRoute32':'route32','JohtoRoute33':'route33'}
for path in sorted((out/'native').glob('*.png')):
 name=path.stem;l=next(v for v in layouts if v['name']==name+'_Layout');dirs=[]
 for side in ['primary','secondary']:
  sym='gTilesetTiles_'+l[side+'_tileset'].removeprefix('gTileset_');dirs.append(re.search(re.escape(sym)+r'\[\].*?"data/tilesets/'+side+r'/([^/]+)/tiles.png"',graphics,re.S)[1])
 t=Tileset(dest,dirs[1],dirs[0]);grid=np.fromfile(dest/l['blockdata_filepath'],'<u2');decoded=t.map_image(grid.tolist(),l['width']);native=Image.open(path).convert('RGB');assert decoded.size==native.size and ImageChops.difference(decoded,native).getbbox() is None,name
 row={'map':name,'native_Porymap_matches_decoder':True}
 if name in mapping:
  expected=Image.open(hub/'gba/art/johto-common/editor-library'/mapping[name]/'previews'/f'{name}.png').convert('RGB')
  if name=='CherrygroveRoute30Approach':
   for v in carry['applied']:expected.paste(ot.render(v['saved_word']&1023),(v['x']*16,v['y']*16));assert int(grid[v['y']*35+v['x']])>>10==v['saved_word']>>10
   row['owner_cells_carried']=len(carry['applied']);row['owner_cells_pending']=len(carry['pending'])
  assert expected.size==native.size and ImageChops.difference(expected,native).getbbox() is None,(name,'Source art drift')
  row['matches_pinned_source_with_only_recorded_owner_edits']=True
 records.append(row)
base=json.loads(subprocess.check_output(['git','show','1643f58a48:data/maps/map_groups.json'],cwd=dest));now=json.loads((dest/'data/maps/map_groups.json').read_text())
for key,vals in base.items():
 if isinstance(vals,list):assert now[key][:len(vals)]==vals,('Existing map IDs moved',key)
result={'existing_map_numbers_preserved':True,'maps':records};(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
