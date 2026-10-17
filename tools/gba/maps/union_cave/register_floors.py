"""Append basement map/layout IDs and wire only original visible staircase pairs."""
from pathlib import Path
import sys,json,hashlib
from config import FLOORS
G=Path(sys.argv[1]);ROOT=Path(__file__).resolve().parents[4]
def write(p,text):
 if not p.exists() or p.read_text()!=text:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
def js(p,j):write(p,json.dumps(j,indent=2)+'\n')
layouts=json.loads((G/'data/layouts/layouts.json').read_text());groups=json.loads((G/'data/maps/map_groups.json').read_text());template=json.loads((G/'data/maps/UnionCaveRoute32Entrance/map.json').read_text())
for key,c in FLOORS.items():
 name=c['name'];S=ROOT/f'gba/art/union-cave-{key}/source';manifest=S/'generated-files.json'
 if (G/'data/maps'/name/'map.json').exists() and manifest.exists():
  old=json.loads(manifest.read_text());p=f'data/maps/{name}/map.json'
  if p in old:assert hashlib.sha256((G/p).read_bytes()).hexdigest()==old[p],('Preserve map edits',name)
 if key!='1f':
  assert name not in groups['gMapGroup_Cherrygrove'] or groups['gMapGroup_Cherrygrove'].index(name)==c['map_num']
  if name not in groups['gMapGroup_Cherrygrove']:groups['gMapGroup_Cherrygrove'].append(name)
  if not any(l['id']==c['layout'] for l in layouts['layouts']):layouts['layouts'].append({'id':c['layout'],'name':name+'_Layout','width':c['size'][0],'height':c['size'][1],'primary_tileset':'gTileset_'+c['symbol']+'Primary','secondary_tileset':'gTileset_'+c['symbol']+'Secondary','border_filepath':f'data/layouts/{name}/border.bin','blockdata_filepath':f'data/layouts/{name}/map.bin','layout_version':'emerald','build_target':'emerald'})
  for part in ['Primary','Secondary']:
   symbol=c['symbol']+part;folder=f'data/tilesets/{part.lower()}/{c["set"]}';tag=f'// Union Cave {key} {part}\n';blocks={'graphics.h':f'const u32 gTilesetTiles_{symbol}[] = INCGFX_U32("{folder}/tiles.png", ".4bpp.fastSmol");\n'+f'const u16 gTilesetPalettes_{symbol}[][16] = {{\n'+''.join(f'INCGFX_U16("{folder}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16))+'};\n','metatiles.h':f'const u16 gMetatiles_{symbol}[] = INCBIN_U16("{folder}/metatiles.bin");\nconst u16 gMetatileAttributes_{symbol}[] = INCBIN_U16("{folder}/metatile_attributes.bin");\n','headers.h':f'const struct Tileset gTileset_{symbol} = {{ .isCompressed=TRUE, .isSecondary='+('TRUE' if part=='Secondary' else 'FALSE')+f', .tiles=gTilesetTiles_{symbol}, .palettes=gTilesetPalettes_{symbol}, .metatiles=gMetatiles_{symbol}, .metatileAttributes=gMetatileAttributes_{symbol}, .callback=NULL }};\n'}
   for fn,block in blocks.items():
    p=G/'src/data/tilesets'/fn;s=p.read_text()
    if tag not in s:write(p,s+'\n'+tag+block)
    else:assert block in s,('Preserve tileset registration',symbol)
  m=dict(template);m.update(id=c['id'],name=name,layout=c['layout'],object_events=[],coord_events=[],bg_events=[],connections=None);js(G/f'data/maps/{name}/map.json',m);write(G/f'data/maps/{name}/scripts.inc',name+'_MapScripts::\n    .byte 0\n')
 m=json.loads((G/f'data/maps/{name}/map.json').read_text());m['warp_events']=[{'x':x,'y':y,'elevation':3,'dest_map':dest,'dest_warp_id':str(di)} for x,y,dest,di in c['warps']];js(G/f'data/maps/{name}/map.json',m)
js(G/'data/layouts/layouts.json',layouts);js(G/'data/maps/map_groups.json',groups)
p=G/'data/event_scripts.s';s=p.read_text()
for key in ['b1f','b2f']:
 line=f'.include "data/maps/{FLOORS[key]["name"]}/scripts.inc"'
 if line not in s:s+='\n'+line+'\n'
write(p,s)
p=G/'src/apocrypha_map_proof.c';s=p.read_text();old='MAP_UNION_CAVE_ROUTE32_ENTRANCE};';new='MAP_UNION_CAVE_ROUTE32_ENTRANCE, MAP_UNION_CAVE_B1F, MAP_UNION_CAVE_B2F};'
if old in s:write(p,s.replace(old,new))
else:assert new in s
for key,c in FLOORS.items():
 S=ROOT/f'gba/art/union-cave-{key}/source';paths=[p for folder in [G/'data/layouts'/c['name'],G/'data/maps'/c['name'],G/'data/tilesets/primary'/c['set'],G/'data/tilesets/secondary'/c['set']] for p in folder.rglob('*') if p.is_file() and p.name not in ['header.inc','events.inc','connections.inc']]
 def digest(p):
  b=p.read_bytes();return hashlib.sha256(b.replace(b'\r\n',b'\n') if p.suffix=='.pal' else b).hexdigest()
 js(S/'generated-files.json',{str(p.relative_to(G)):digest(p) for p in paths})
print('Visible floors wired; maps',[(c['name'],c['map_num']) for c in FLOORS.values()])
