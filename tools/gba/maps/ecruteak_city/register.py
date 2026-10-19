"""Append Ecruteak IDs; never renumber or edit another area's native sources."""
from pathlib import Path
import sys,json
import numpy as np
G=Path(sys.argv[1]);ROOT=Path(__file__).resolve().parents[4];S=ROOT/'gba/art/ecruteak-city/source'
def read(p):return json.loads((G/p).read_text())
def write(p,v):(G/p).write_text(json.dumps(v,indent=2)+'\n')
maps=[('JohtoEcruteakCity','EcruteakCity','ECRUTEAK_CITY','ecruteak_city',25,27),('JohtoEcruteakTempleDistrict','EcruteakTemple','ECRUTEAK_TEMPLE_DISTRICT','ecruteak_temple',27,0)]
assert all(not (G/'data/maps'/n).exists() for n,*_ in maps)
l=read('data/layouts/layouts.json');groups=read('data/maps/map_groups.json');solid=np.load(S/'solid.npy');mat=np.load(S/'material-grid.npy')
for name,label,key,bank,height,offset in maps:
 for sec in [False,True]:
  side='secondary' if sec else 'primary';sym=label+('' if sec else 'Primary')
  for f,block in {'graphics.h':f'const u32 gTilesetTiles_{sym}[] = INCGFX_U32("data/tilesets/{side}/{bank}/tiles.png", ".4bpp.fastSmol");\nconst u16 gTilesetPalettes_{sym}[][16] = {{\n'+''.join(f'INCGFX_U16("data/tilesets/{side}/{bank}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16))+'};\n','metatiles.h':f'const u16 gMetatiles_{sym}[] = INCBIN_U16("data/tilesets/{side}/{bank}/metatiles.bin");\nconst u16 gMetatileAttributes_{sym}[] = INCBIN_U16("data/tilesets/{side}/{bank}/metatile_attributes.bin");\n','headers.h':f'const struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, .isSecondary = {"TRUE" if sec else "FALSE"}, .tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym}, .metatiles = gMetatiles_{sym}, .metatileAttributes = gMetatileAttributes_{sym}, .callback = NULL }};\n'}.items():
   p=G/'src/data/tilesets'/f;p.write_text(p.read_text()+'\n// Ecruteak native exterior\n'+block)
 l['layouts'].append(dict(id='LAYOUT_JOHTO_'+key,name=name+'_Layout',width=72,height=height,border_width=2,border_height=2,primary_tileset='gTileset_'+label+'Primary',secondary_tileset='gTileset_'+label,border_filepath=f'data/layouts/{name}/border.bin',blockdata_filepath=f'data/layouts/{name}/map.bin',layout_version='emerald',build_target='emerald'))
 groups['gMapGroup_Cherrygrove'].append(name)
 m=read('data/maps/JohtoAzaleaTown/map.json');m.update(id='MAP_JOHTO_'+key,name=name,layout='LAYOUT_JOHTO_'+key,region_map_section='MAPSEC_JOHTO_ECRUTEAK_CITY',music='MUS_FALLARBOR',warp_events=[],connections=None,object_events=[],bg_events=[],coord_events=[],weather='WEATHER_NONE',map_type='MAP_TYPE_CITY')
 # Rendering districts use a brief ordinary map fade at the central avenue.
 # Separate banks must never appear as a false seamless connection: the GBA
 # connection renderer would decode the neighboring strip with the wrong art.
 row=0 if offset else 26;gy=offset+row;dest='ECRUTEAK_TEMPLE_DISTRICT' if offset else 'ECRUTEAK_CITY';dy=25 if offset else 1;scripts=[name+'_MapScripts::','    .byte 0','']
 for x in range(1,71):
  if solid[gy,x] or solid[gy+(-1 if offset else 1),x]:continue
  script=name+f'_District_{x}'
  m['coord_events'].append(dict(type='trigger',x=x,y=row,elevation=0,var='VAR_TEMP_1',var_value='0',script=script))
  scripts += [script+'::',f'    warp MAP_JOHTO_{dest}, {x}, {dy}','    waitstate','    end','']
 p=G/'data/maps'/name;p.mkdir();write(f'data/maps/{name}/map.json',m);(p/'scripts.inc').write_text('\n'.join(scripts))
 p=G/'data/event_scripts.s';p.write_text(p.read_text()+f'\n.include "data/maps/{name}/scripts.inc"\n')
write('data/layouts/layouts.json',l);write('data/maps/map_groups.json',groups)
r=read('src/data/region_map/region_map_sections.json');r['map_sections'].append(dict(id='MAPSEC_JOHTO_ECRUTEAK_CITY',name='ECRUTEAK CITY',x=5,y=5,width=1,height=1));write('src/data/region_map/region_map_sections.json',r)
p=G/'src/apocrypha_map_proof.c';p.write_text(p.read_text().replace('MAP_JOHTO_AZALEA_TOWN};','MAP_JOHTO_AZALEA_TOWN, MAP_JOHTO_ECRUTEAK_CITY, MAP_JOHTO_ECRUTEAK_TEMPLE_DISTRICT};'))
print({name:groups['gMapGroup_Cherrygrove'].index(name) for name,*_ in maps})
