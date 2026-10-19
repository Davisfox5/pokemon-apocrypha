"""Append Goldenrod sections without changing existing map/layout IDs."""
from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[4];G=Path(sys.argv[1]);sections=json.loads((R/'gba/art/goldenrod-city/evidence/sections.json').read_text())
def read(p):return json.loads((G/p).read_text())
def write(p,v):(G/p).write_text(json.dumps(v,indent=2)+'\n')
l=read('data/layouts/layouts.json');groups=read('data/maps/map_groups.json');reg=read('src/data/region_map/region_map_sections.json');assert not any(n.startswith('Goldenrod') for n in groups['gMapGroup_Cherrygrove'])
reg['map_sections'].append(dict(id='MAPSEC_GOLDENROD_CITY',name='GOLDENROD CITY',x=1,y=6,width=2,height=2));write('src/data/region_map/region_map_sections.json',reg)
for s in sections:
 name=s['name'];x,y,x1,y1=s['box'];folder=name.lower();a=name+'Primary';b=name
 for sec,sym in [(False,a),(True,b)]:
  side='secondary' if sec else 'primary';prefix=f'data/tilesets/{side}/{folder}'
  for f,text in {'graphics.h':f'const u32 gTilesetTiles_{sym}[] = INCGFX_U32("{prefix}/tiles.png", ".4bpp.fastSmol");\nconst u16 gTilesetPalettes_{sym}[][16] = {{\n'+''.join(f'INCGFX_U16("{prefix}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16))+'};\n','metatiles.h':f'const u16 gMetatiles_{sym}[] = INCBIN_U16("{prefix}/metatiles.bin");\nconst u16 gMetatileAttributes_{sym}[] = INCBIN_U16("{prefix}/metatile_attributes.bin");\n','headers.h':f'const struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, .isSecondary = {"TRUE" if sec else "FALSE"}, .tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym}, .metatiles = gMetatiles_{sym}, .metatileAttributes = gMetatileAttributes_{sym}, .callback = NULL }};\n'}.items():
   p=G/'src/data/tilesets'/f;p.write_text(p.read_text()+'\n// Goldenrod native exterior\n'+text)
 l['layouts'].append(dict(id='LAYOUT_'+name.upper(),name=name+'_Layout',width=x1-x,height=y1-y,border_width=2,border_height=2,primary_tileset='gTileset_'+a,secondary_tileset='gTileset_'+b,border_filepath=f'data/layouts/{name}/border.bin',blockdata_filepath=f'data/layouts/{name}/map.bin',layout_version='emerald',build_target='emerald'))
 connections=[]
 for t in sections:
  if t is s:continue
  xx,yy,xx1,yy1=t['box'];direction=None
  if x1==xx and max(y,yy)<min(y1,yy1):direction='right';off=yy-y
  if xx1==x and max(y,yy)<min(y1,yy1):direction='left';off=yy-y
  if y1==yy and max(x,xx)<min(x1,xx1):direction='down';off=xx-x
  if yy1==y and max(x,xx)<min(x1,xx1):direction='up';off=xx-x
  if direction:connections.append(dict(direction=direction,offset=off,map='MAP_'+t['name'].upper()))
 m=read('data/maps/JohtoAzaleaTown/map.json');m.update(id='MAP_'+name.upper(),name=name,layout='LAYOUT_'+name.upper(),region_map_section='MAPSEC_GOLDENROD_CITY',music='MUS_LILYCOVE',connections=connections,show_map_name=False)
 p=G/'data/maps'/name;p.mkdir(exist_ok=True);write(f'data/maps/{name}/map.json',m);(p/'scripts.inc').write_text(name+'_MapScripts::\n    .byte 0\n');groups['gMapGroup_Cherrygrove'].append(name)
 p=G/'data/event_scripts.s';p.write_text(p.read_text()+f'\n.include "data/maps/{name}/scripts.inc"\n')
write('data/layouts/layouts.json',l);write('data/maps/map_groups.json',groups)
p=G/'src/apocrypha_map_proof.c';p.write_text(p.read_text().replace('MAP_JOHTO_AZALEA_TOWN};','MAP_JOHTO_AZALEA_TOWN, '+', '.join('MAP_'+s['name'].upper() for s in sections)+'};'))
print('Goldenrod map IDs',[(s['name'],groups['gMapGroup_Cherrygrove'].index(s['name'])) for s in sections])
