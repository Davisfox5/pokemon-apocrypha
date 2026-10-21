"""Append the two new terrain maps, preserving every existing stable ID."""
from pathlib import Path
import sys,json
G=Path(sys.argv[1])
def read(p):return json.loads((G/p).read_text())
def write(p,d):(G/p).write_text(json.dumps(d,indent=2)+'\n')
assert not (G/'data/maps/JohtoRoute38').exists()
for sec in [False,True]:
 side='secondary' if sec else 'primary';sym='JohtoRoute3839'+('' if sec else 'Primary')
 chunks={'graphics.h':f'const u32 gTilesetTiles_{sym}[] = INCGFX_U32("data/tilesets/{side}/route38_39/tiles.png", ".4bpp.fastSmol");\nconst u16 gTilesetPalettes_{sym}[][16] = {{\n'+''.join(f'INCGFX_U16("data/tilesets/{side}/route38_39/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16))+'};\n','metatiles.h':f'const u16 gMetatiles_{sym}[] = INCBIN_U16("data/tilesets/{side}/route38_39/metatiles.bin");\nconst u16 gMetatileAttributes_{sym}[] = INCBIN_U16("data/tilesets/{side}/route38_39/metatile_attributes.bin");\n','headers.h':f'const struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, .isSecondary = {"TRUE" if sec else "FALSE"}, .tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym}, .metatiles = gMetatiles_{sym}, .metatileAttributes = gMetatileAttributes_{sym}, .callback = NULL }};\n'}
 for f,c in chunks.items():
  p=G/'src/data/tilesets'/f;p.write_text(p.read_text()+'\n// Routes 38/39 terrain review\n'+c)
l=read('data/layouts/layouts.json');groups=read('data/maps/map_groups.json');r=read('src/data/region_map/region_map_sections.json')
for n,w,h,dest,dir,off in [(38,68,33,39,'left',-2),(39,38,56,38,'right',2)]:
 name=f'JohtoRoute{n}';key=f'JOHTO_ROUTE{n}'
 l['layouts'].append(dict(id='LAYOUT_'+key,name=name+'_Layout',width=w,height=h,border_width=2,border_height=2,primary_tileset='gTileset_JohtoRoute3839Primary',secondary_tileset='gTileset_JohtoRoute3839',border_filepath=f'data/layouts/{name}/border.bin',blockdata_filepath=f'data/layouts/{name}/map.bin',layout_version='emerald',build_target='emerald'))
 groups['gMapGroup_Cherrygrove'].append(name)
 m=read('data/maps/JohtoEcruteakCity/map.json');m.update(id='MAP_'+key,name=name,layout='LAYOUT_'+key,region_map_section='MAPSEC_'+key,music='MUS_ROUTE119',map_type='MAP_TYPE_ROUTE',connections=[dict(map=f'MAP_JOHTO_ROUTE{dest}',direction=dir,offset=off)],warp_events=[],object_events=[],bg_events=[],coord_events=[],weather='WEATHER_NONE')
 p=G/'data/maps'/name;p.mkdir();write(f'data/maps/{name}/map.json',m);(p/'scripts.inc').write_text(name+'_MapScripts::\n    .byte 0\n')
 p=G/'data/event_scripts.s';p.write_text(p.read_text()+f'\n.include "data/maps/{name}/scripts.inc"\n')
 r['map_sections'].append(dict(id='MAPSEC_'+key,name=f'ROUTE {n}',x=4 if n==38 else 3,y=5 if n==38 else 6,width=1,height=1))
write('data/layouts/layouts.json',l);write('data/maps/map_groups.json',groups);write('src/data/region_map/region_map_sections.json',r)
p=G/'src/apocrypha_map_proof.c';s=p.read_text();s=s.replace('MAP_JOHTO_ECRUTEAK_TEMPLE_DISTRICT};','MAP_JOHTO_ECRUTEAK_TEMPLE_DISTRICT, MAP_JOHTO_ROUTE38, MAP_JOHTO_ROUTE39};');p.write_text(s)
print({n:groups['gMapGroup_Cherrygrove'].index(n) for n in ['JohtoRoute38','JohtoRoute39']})
