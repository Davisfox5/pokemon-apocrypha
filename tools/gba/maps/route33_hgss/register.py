"""Append a single area; stable IDs. Never replay over native owner edits."""
from pathlib import Path
import sys,json,numpy as np
G=Path(sys.argv[1]);assert not (G/'data/maps/JohtoRoute33').exists()
def read(p):return json.loads((G/p).read_text())
def write(p,v):(G/p).write_text(json.dumps(v,indent=2)+'\n')
for secondary in [False,True]:
 side='secondary' if secondary else 'primary';sym='Route33' if secondary else 'Route33Primary'
 for f,block in {'graphics.h':f'const u32 gTilesetTiles_{sym}[] = INCGFX_U32("data/tilesets/{side}/route33/tiles.png", ".4bpp.fastSmol");\nconst u16 gTilesetPalettes_{sym}[][16] = {{\n'+''.join(f'INCGFX_U16("data/tilesets/{side}/route33/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16))+'};\n','metatiles.h':f'const u16 gMetatiles_{sym}[] = INCBIN_U16("data/tilesets/{side}/route33/metatiles.bin");\nconst u16 gMetatileAttributes_{sym}[] = INCBIN_U16("data/tilesets/{side}/route33/metatile_attributes.bin");\n','headers.h':f'const struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, .isSecondary = {"TRUE" if secondary else "FALSE"}, .tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym}, .metatiles = gMetatiles_{sym}, .metatileAttributes = gMetatileAttributes_{sym}, .callback = NULL }};\n'}.items():
  p=G/'src/data/tilesets'/f;p.write_text(p.read_text()+'\n// Route33 HGSS native area\n'+block)
l=read('data/layouts/layouts.json');l['layouts'].append({'id':'LAYOUT_JOHTO_ROUTE33','name':'JohtoRoute33_Layout','width':34,'height':29,'border_width':2,'border_height':2,'primary_tileset':'gTileset_Route33Primary','secondary_tileset':'gTileset_Route33','border_filepath':'data/layouts/JohtoRoute33/border.bin','blockdata_filepath':'data/layouts/JohtoRoute33/map.bin','layout_version':'emerald','build_target':'emerald'});write('data/layouts/layouts.json',l)
g=read('data/maps/map_groups.json');g['gMapGroup_Cherrygrove'].append('JohtoRoute33');write('data/maps/map_groups.json',g)
r=read('src/data/region_map/region_map_sections.json');r['map_sections'].append({'id':'MAPSEC_ROUTE33','name':'ROUTE 33','x':2,'y':8,'width':1,'height':1});write('src/data/region_map/region_map_sections.json',r)
m=read('data/maps/JohtoRoute32/map.json');m.update(id='MAP_JOHTO_ROUTE33',name='JohtoRoute33',layout='LAYOUT_JOHTO_ROUTE33',region_map_section='MAPSEC_ROUTE33',warp_events=[{'x':19,'y':11,'elevation':3,'dest_map':'MAP_UNION_CAVE_ROUTE32_ENTRANCE','dest_warp_id':'3'}],connections=None,object_events=[],bg_events=[],coord_events=[],weather='WEATHER_RAIN')
p=G/'data/maps/JohtoRoute33';p.mkdir();write('data/maps/JohtoRoute33/map.json',m);(p/'scripts.inc').write_text('JohtoRoute33_MapScripts::\n    .byte 0\n')
p=G/'data/event_scripts.s';p.write_text(p.read_text()+'\n.include "data/maps/JohtoRoute33/scripts.inc"\n')
# Append south doorway warp; preserve the existing three IDs and all paired stairs.
p='data/maps/UnionCaveRoute32Entrance/map.json';c=read(p);assert len(c['warp_events'])==3;c['warp_events'].append({'x':28,'y':58,'elevation':3,'dest_map':'MAP_JOHTO_ROUTE33','dest_warp_id':'0'});write(p,c)
grid=np.fromfile(G/'data/layouts/UnionCaveRoute32Entrance/map.bin','<u2').reshape(60,34);mid=int(grid[58,28]&1023);a=G/'data/tilesets/secondary/union_cave/metatile_attributes.bin' if mid>=512 else G/'data/tilesets/primary/union_cave/metatile_attributes.bin';attrs=np.fromfile(a,'<u2');i=mid-512 if mid>=512 else mid;attrs[i]=(attrs[i]&0xff00)|101;attrs.tofile(a)
print('Route33 map ID',g['gMapGroup_Cherrygrove'].index('JohtoRoute33'),'cave exit metatile',mid)

p=G/'src/apocrypha_map_proof.c';p.write_text(p.read_text().replace('MAP_UNION_CAVE_B2F};','MAP_UNION_CAVE_B2F, MAP_JOHTO_ROUTE33};'))
