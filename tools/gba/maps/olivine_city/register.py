"""Append Olivine native IDs, preserve every earlier map/tileset ID."""
from pathlib import Path
import sys,json
import numpy as np
G=Path(sys.argv[1]);ROOT=Path(__file__).resolve().parents[4];S=ROOT/'gba/art/olivine-city/source';E=S.parent/'evidence';a=json.loads((E/'assembly.json').read_text());solid=np.load(S/'solid.npy');W,H=a['size']
def read(p):return json.loads((G/p).read_text())
def write(p,v):(G/p).write_text(json.dumps(v,indent=2)+'\n')
l=read('data/layouts/layouts.json');groups=read('data/maps/map_groups.json');maps=a['districts'];keys=['OLIVINE_CITY','OLIVINE_QUAY','OLIVINE_HARBOR'];labels=['OlivineCity','OlivineQuay','OlivineHarbor']
assert all(not (G/'data/maps'/m['map']).exists() for m in maps)
for i,(d,key,label) in enumerate(zip(maps,keys,labels)):
 name,bank,height,offset=d['map'],d['tileset'],d['height'],d['global_y']
 for sec in [False,True]:
  side='secondary' if sec else 'primary';sym=label+('' if sec else 'Primary')
  for f,body in {'graphics.h':f'const u32 gTilesetTiles_{sym}[] = INCGFX_U32("data/tilesets/{side}/{bank}/tiles.png", ".4bpp.fastSmol");\nconst u16 gTilesetPalettes_{sym}[][16] = {{\n'+''.join(f'INCGFX_U16("data/tilesets/{side}/{bank}/palettes/{n:02}.pal", ".gbapal"),\n' for n in range(16))+'};\n','metatiles.h':f'const u16 gMetatiles_{sym}[] = INCBIN_U16("data/tilesets/{side}/{bank}/metatiles.bin");\nconst u16 gMetatileAttributes_{sym}[] = INCBIN_U16("data/tilesets/{side}/{bank}/metatile_attributes.bin");\n','headers.h':f'const struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, .isSecondary = {"TRUE" if sec else "FALSE"}, .tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym}, .metatiles = gMetatiles_{sym}, .metatileAttributes = gMetatileAttributes_{sym}, .callback = NULL }};\n'}.items():
   p=G/'src/data/tilesets'/f;p.write_text(p.read_text()+'\n// Olivine native exterior\n'+body)
 l['layouts'].append(dict(id='LAYOUT_JOHTO_'+key,name=name+'_Layout',width=W,height=height,border_width=2,border_height=2,primary_tileset='gTileset_'+label+'Primary',secondary_tileset='gTileset_'+label,border_filepath=f'data/layouts/{name}/border.bin',blockdata_filepath=f'data/layouts/{name}/map.bin',layout_version='emerald',build_target='emerald'));groups['gMapGroup_Cherrygrove'].append(name)
 m=read('data/maps/JohtoEcruteakCity/map.json');m.update(id='MAP_JOHTO_'+key,name=name,layout='LAYOUT_JOHTO_'+key,region_map_section='MAPSEC_JOHTO_OLIVINE_CITY',music='MUS_LILYCOVE',warp_events=[],connections=None,object_events=[],bg_events=[],coord_events=[],weather='WEATHER_NONE',map_type='MAP_TYPE_CITY');scripts=[name+'_MapScripts::','    .byte 0','']
 for nxt,row,dy in [(i-1,0,maps[i-1]['height']-2 if i>0 else 0),(i+1,height-1,1)]:
  if nxt<0 or nxt>=len(maps):continue
  dest=keys[nxt];gy=offset+row;delta=-1 if row==0 else 1
  for x in range(1,W-1):
   if solid[gy,x] or solid[gy+delta,x]:continue
   script=name+f'_District_{row}_{x}';m['coord_events'].append(dict(type='trigger',x=x,y=row,elevation=0,var='VAR_TEMP_1',var_value='0',script=script));scripts += [script+'::',f'    warp MAP_JOHTO_{dest}, {x}, {dy}','    waitstate','    end','']
 p=G/'data/maps'/name;p.mkdir();write(f'data/maps/{name}/map.json',m);(p/'scripts.inc').write_text('\n'.join(scripts));p=G/'data/event_scripts.s';p.write_text(p.read_text()+f'\n.include "data/maps/{name}/scripts.inc"\n')
write('data/layouts/layouts.json',l);write('data/maps/map_groups.json',groups)
r=read('src/data/region_map/region_map_sections.json');r['map_sections'].append(dict(id='MAPSEC_JOHTO_OLIVINE_CITY',name='OLIVINE CITY',x=3,y=6,width=1,height=1));write('src/data/region_map/region_map_sections.json',r)
p=G/'src/apocrypha_map_proof.c';s=p.read_text();s=s.replace('MAP_JOHTO_ECRUTEAK_TEMPLE_DISTRICT};','MAP_JOHTO_ECRUTEAK_TEMPLE_DISTRICT, '+', '.join('MAP_JOHTO_'+k for k in keys)+'};');p.write_text(s)
print({d['map']:groups['gMapGroup_Cherrygrove'].index(d['map']) for d in maps})
