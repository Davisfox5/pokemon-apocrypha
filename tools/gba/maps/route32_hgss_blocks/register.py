"""Append new native source IDs; existing layouts and maps remain byte-identical."""
from pathlib import Path
import sys,json,struct
import numpy as np
import preservation
G=Path(sys.argv[1]);W,H=32,128
S=Path(__file__).resolve().parents[4]/'gba/art/route32-hgss-blocks/source';preservation.check(G,S)
def read(p):return json.loads((G/p).read_text())
def write(p,v):
 target=G/p;text=json.dumps(v,indent=2)+'\n'
 if not target.exists() or target.read_text()!=text:target.write_text(text)
sym='Route32';name='route32'
for f,block in {
'graphics.h':f'const u32 gTilesetTiles_{sym}[] = INCGFX_U32("data/tilesets/secondary/{name}/tiles.png", ".4bpp.fastSmol");\nconst u16 gTilesetPalettes_{sym}[][16] = {{\n'+''.join(f'INCGFX_U16("data/tilesets/secondary/{name}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16))+'};\n',
'metatiles.h':f'const u16 gMetatiles_{sym}[] = INCBIN_U16("data/tilesets/secondary/{name}/metatiles.bin");\nconst u16 gMetatileAttributes_{sym}[] = INCBIN_U16("data/tilesets/secondary/{name}/metatile_attributes.bin");\n',
'headers.h':f'const struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, .isSecondary = TRUE, .tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym}, .metatiles = gMetatiles_{sym}, .metatileAttributes = gMetatileAttributes_{sym}, .callback = NULL }};\n'
}.items():
 p=G/'src/data/tilesets'/f;s=p.read_text();tag='// Route32 HGSS reconstruction\n';s=s.split(tag)[0];p.write_text(s+'\n'+tag+block)
l=read('data/layouts/layouts.json');l['layouts']=[x for x in l['layouts'] if x['id']!='LAYOUT_JOHTO_ROUTE32'];l['layouts'].append({'id':'LAYOUT_JOHTO_ROUTE32','name':'JohtoRoute32_Layout','width':W,'height':H,'border_width':2,'border_height':2,'primary_tileset':'gTileset_CherrygrovePrimary','secondary_tileset':'gTileset_Route32','border_filepath':'data/layouts/JohtoRoute32/border.bin','blockdata_filepath':'data/layouts/JohtoRoute32/map.bin','layout_version':'emerald','build_target':'emerald'});write('data/layouts/layouts.json',l)
r=read('src/data/region_map/region_map_sections.json');sec=r['map_sections'] if 'map_sections' in r else r['sections'];
if not any(x['id']=='MAPSEC_ROUTE32' for x in sec):sec.append({'id':'MAPSEC_ROUTE32','name':'ROUTE 32','x':2,'y':5,'width':1,'height':3})
write('src/data/region_map/region_map_sections.json',r)
g=read('data/maps/map_groups.json')
for n in ['JohtoRoute32','Route32PokemonCenter','Route32CenterUpstairs','UnionCaveRoute32Entrance']:
 if n not in g['gMapGroup_Cherrygrove']:g['gMapGroup_Cherrygrove'].append(n)
write('data/maps/map_groups.json',g)
def warp(x,y,dm,di=0,e=0):return {'x':x,'y':y,'elevation':e,'dest_map':dm,'dest_warp_id':str(di)}
m=read('data/maps/JohtoRoute31/map.json');m.update(id='MAP_JOHTO_ROUTE32',name='JohtoRoute32',layout='LAYOUT_JOHTO_ROUTE32',region_map_section='MAPSEC_ROUTE32',connections=None,object_events=[],bg_events=[],warp_events=[warp(20,108,'MAP_ROUTE32_POKEMON_CENTER'),warp(13,116,'MAP_UNION_CAVE_ROUTE32_ENTRANCE'),warp(14,116,'MAP_UNION_CAVE_ROUTE32_ENTRANCE')],coord_events=[])
def save_map(n,m,s):
 folder=G/'data/maps'/n;folder.mkdir(exist_ok=True);write(f'data/maps/{n}/map.json',m);(folder/'scripts.inc').write_text(s)
save_map('JohtoRoute32',m,'JohtoRoute32_MapScripts::\n    .byte 0\n')
for n,original in [('Route32PokemonCenter','CherrygrovePokemonCenter'),('Route32CenterUpstairs','CherrygroveCenterUpstairs'),('UnionCaveRoute32Entrance','DarkCaveEntrance')]:
 mm=read(f'data/maps/{original}/map.json');mm['id']={'Route32PokemonCenter':'MAP_ROUTE32_POKEMON_CENTER','Route32CenterUpstairs':'MAP_ROUTE32_CENTER_UPSTAIRS','UnionCaveRoute32Entrance':'MAP_UNION_CAVE_ROUTE32_ENTRANCE'}[n];mm['name']=n;mm['region_map_section']='MAPSEC_ROUTE32'
 if n=='Route32PokemonCenter':
  for w in mm['warp_events']:
   w['dest_map']='MAP_ROUTE32_CENTER_UPSTAIRS' if w['dest_map']=='MAP_CHERRYGROVE_CENTER_UPSTAIRS' else 'MAP_JOHTO_ROUTE32';w['dest_warp_id']='0'
  for o in mm['object_events']:o['script']=o['script'].replace(original,n)
 elif n=='Route32CenterUpstairs':
  for w in mm['warp_events']:w['dest_map']='MAP_ROUTE32_POKEMON_CENTER';w['dest_warp_id']='2'
 else:
  for w in mm['warp_events']:w['dest_map']='MAP_JOHTO_ROUTE32';w['dest_warp_id']='1'
 scripts=(G/f'data/maps/{original}/scripts.inc').read_text().replace(original,n).replace('CherrygrovePokemonCenter','Route32PokemonCenter');save_map(n,mm,scripts)
# Reuse exact accepted Center door frames and palette; door metatile IDs remain scoped to new tileset.
grid=np.fromfile(G/'data/layouts/JohtoRoute32/map.bin','<u2').reshape(H,W);mid=int(grid[108,20]&1023);p=G/'src/field_door.c';s=p.read_text();tag='// Route32 door\n';
if tag not in s:
 s=s.replace('static const struct DoorGraphics sDoorAnimGraphicsTable[]', 'extern const struct Tileset gTileset_Route32;\nstatic const struct DoorGraphics sDoorAnimGraphicsTable[]');s=s.replace('static const struct DoorGraphics sDoorAnimGraphicsTable[] =\n{','static const struct DoorGraphics sDoorAnimGraphicsTable[] =\n{\n    '+tag+f'    {{.metatileNum={mid}, .tileset=&gTileset_Route32, .sound=DOOR_SOUND_NORMAL, .size=DOOR_SIZE_2x2_LEFT, .tiles=sRestartDoor_PokemonCenter, .palettes=sRestartDoorPal_PokemonCenter}},');p.write_text(s)
p=G/'.gitattributes';s=p.read_text();
if '*.pal whitespace=cr-at-eol' not in s:p.write_text(s+'\n*.pal whitespace=cr-at-eol\n')
print('Appended maps',[(n,g['gMapGroup_Cherrygrove'].index(n)) for n in g['gMapGroup_Cherrygrove'][-4:]])
p=G/'data/event_scripts.s';s=p.read_text()
for n in ['JohtoRoute32','Route32PokemonCenter','Route32CenterUpstairs','UnionCaveRoute32Entrance']:
 line=f'.include "data/maps/{n}/scripts.inc"'
 if line not in s:s+='\n'+line+'\n'
p.write_text(s)
import re
p=G/'src/field_door.c';s=p.read_text();s=re.sub(r'metatileNum=\d+(, \.tileset=&gTileset_Route32)',str('metatileNum='+str(mid))+r'\1',s);p.write_text(s)
p=G/'src/apocrypha_map_proof.c';s=p.read_text();old='MAP_CHERRYGROVE_REGIONAL_PREVIEW_30};';new='MAP_CHERRYGROVE_REGIONAL_PREVIEW_30, MAP_JOHTO_ROUTE32, MAP_ROUTE32_POKEMON_CENTER, MAP_ROUTE32_CENTER_UPSTAIRS, MAP_UNION_CAVE_ROUTE32_ENTRANCE};'
if old in s:p.write_text(s.replace(old,new))
# Dedicated native entrance test room; no changes to Dark Cave or its placeholder blocks.
folder=G/'data/layouts/UnionCaveRoute32Entrance';folder.mkdir(exist_ok=True)
original=np.fromfile(G/'data/layouts/RusturfTunnel/map.bin','<u2').reshape(24,36);entry=original[:12,:14].copy();entry[(entry&1023)==512]=0x3e0c;entry.astype('<u2').tofile(folder/'map.bin');np.full(4,0x3e0c,'<u2').tofile(folder/'border.bin')
l=read('data/layouts/layouts.json')
if not any(x['id']=='LAYOUT_UNION_CAVE_ROUTE32_ENTRANCE' for x in l['layouts']):
 l['layouts'].append({'id':'LAYOUT_UNION_CAVE_ROUTE32_ENTRANCE','name':'UnionCaveRoute32Entrance_Layout','width':14,'height':12,'primary_tileset':'gTileset_General','secondary_tileset':'gTileset_RusturfTunnel','border_filepath':'data/layouts/UnionCaveRoute32Entrance/border.bin','blockdata_filepath':'data/layouts/UnionCaveRoute32Entrance/map.bin','layout_version':'emerald','build_target':'emerald'})
write('data/layouts/layouts.json',l);mm=read('data/maps/UnionCaveRoute32Entrance/map.json');mm['layout']='LAYOUT_UNION_CAVE_ROUTE32_ENTRANCE';mm['warp_events'][0]['elevation']=3;write('data/maps/UnionCaveRoute32Entrance/map.json',mm)

preservation.record(G,S)
