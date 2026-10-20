"""Append only Azalea exterior. Route33 art/source is deliberately untouched."""
from pathlib import Path
import sys,json
G=Path(sys.argv[1]);assert not (G/'data/maps/JohtoAzaleaTown').exists()
def read(p):return json.loads((G/p).read_text())
def write(p,v):(G/p).write_text(json.dumps(v,indent=2)+'\n')
for secondary in [False,True]:
 side='secondary' if secondary else 'primary';sym='Azalea' if secondary else 'AzaleaPrimary'
 for f,block in {'graphics.h':f'const u32 gTilesetTiles_{sym}[] = INCGFX_U32("data/tilesets/{side}/azalea/tiles.png", ".4bpp.fastSmol");\nconst u16 gTilesetPalettes_{sym}[][16] = {{\n'+''.join(f'INCGFX_U16("data/tilesets/{side}/azalea/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16))+'};\n','metatiles.h':f'const u16 gMetatiles_{sym}[] = INCBIN_U16("data/tilesets/{side}/azalea/metatiles.bin");\nconst u16 gMetatileAttributes_{sym}[] = INCBIN_U16("data/tilesets/{side}/azalea/metatile_attributes.bin");\n','headers.h':f'const struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, .isSecondary = {"TRUE" if secondary else "FALSE"}, .tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym}, .metatiles = gMetatiles_{sym}, .metatileAttributes = gMetatileAttributes_{sym}, .callback = NULL }};\n'}.items():
  p=G/'src/data/tilesets'/f;p.write_text(p.read_text()+'\n// Azalea native exterior\n'+block)
l=read('data/layouts/layouts.json');l['layouts'].append({'id':'LAYOUT_JOHTO_AZALEA_TOWN','name':'JohtoAzaleaTown_Layout','width':64,'height':33,'border_width':2,'border_height':2,'primary_tileset':'gTileset_AzaleaPrimary','secondary_tileset':'gTileset_Azalea','border_filepath':'data/layouts/JohtoAzaleaTown/border.bin','blockdata_filepath':'data/layouts/JohtoAzaleaTown/map.bin','layout_version':'emerald','build_target':'emerald'});write('data/layouts/layouts.json',l)
g=read('data/maps/map_groups.json');g['gMapGroup_Cherrygrove'].append('JohtoAzaleaTown');write('data/maps/map_groups.json',g)
r=read('src/data/region_map/region_map_sections.json');r['map_sections'].append({'id':'MAPSEC_JOHTO_AZALEA_TOWN','name':'AZALEA TOWN','x':1,'y':8,'width':1,'height':1});write('src/data/region_map/region_map_sections.json',r)
m=read('data/maps/JohtoRoute33/map.json');m.update(id='MAP_JOHTO_AZALEA_TOWN',name='JohtoAzaleaTown',layout='LAYOUT_JOHTO_AZALEA_TOWN',region_map_section='MAPSEC_JOHTO_AZALEA_TOWN',music='MUS_VERDANTURF',warp_events=[],connections=None,object_events=[],bg_events=[],coord_events=[],weather='WEATHER_NONE',map_type='MAP_TYPE_TOWN')
p=G/'data/maps/JohtoAzaleaTown';p.mkdir();write('data/maps/JohtoAzaleaTown/map.json',m);(p/'scripts.inc').write_text('JohtoAzaleaTown_MapScripts::\n    .byte 0\n')
p=G/'data/event_scripts.s';p.write_text(p.read_text()+'\n.include "data/maps/JohtoAzaleaTown/scripts.inc"\n')
p=G/'src/apocrypha_map_proof.c';p.write_text(p.read_text().replace('MAP_JOHTO_ROUTE33};','MAP_JOHTO_ROUTE33, MAP_JOHTO_AZALEA_TOWN};'))
print('Azalea map ID',g['gMapGroup_Cherrygrove'].index('JohtoAzaleaTown'))
