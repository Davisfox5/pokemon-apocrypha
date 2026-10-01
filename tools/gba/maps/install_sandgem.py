#!/usr/bin/env python3
"""Append Sandgem and link the existing northern approach without rebuilding town."""
from pathlib import Path
import json,struct,re,copy
R=Path(__file__).resolve().parents[3];G=R/'tools/vendor/gba/johto-restart-game';A=R/'gba/art/sandgem-v1';B=R/'tools/vendor/gba/johto-before-sandgem-20260922'
def read(p):return json.loads((G/p).read_text())
def write(p,o):
 f=G/p;s=json.dumps(o,indent=2)+'\n'
 if not f.exists() or f.read_text()!=s:f.write_text(s)
def append(p,s):
 f=G/p;text=f.read_text()
 if s not in text:f.write_text(text+'\n'+s+'\n')
def mapid(name):return 'MAP_'+re.sub(r'(?<!^)(?=[A-Z])','_',name).upper().replace('POKEMON','POKEMON')
# Native declarations, separate palettes and tile allocation.
for name,side in [('SandgemPrimary','primary'),('Sandgem','secondary')]:
 path=f'data/tilesets/{side}/sandgem'
 append('src/data/tilesets/graphics.h',f'const u32 gTilesetTiles_{name}[] = INCGFX_U32("{path}/tiles.png", ".4bpp.fastSmol");\n'+f'const u16 gTilesetPalettes_{name}[][16] = {{\n'+'\n'.join(f'INCGFX_U16("{path}/palettes/{i:02}.pal", ".gbapal"),' for i in range(16))+'\n};')
 append('src/data/tilesets/metatiles.h',f'const u16 gMetatiles_{name}[] = INCBIN_U16("{path}/metatiles.bin");\n'+f'const u16 gMetatileAttributes_{name}[] = INCBIN_U16("{path}/metatile_attributes.bin");')
 append('src/data/tilesets/headers.h',f'const struct Tileset gTileset_{name} = {{ .isCompressed = TRUE, .isSecondary = '+('TRUE' if side=='secondary' else 'FALSE')+f', .tiles = gTilesetTiles_{name}, .palettes = gTilesetPalettes_{name}, .metatiles = gMetatiles_{name}, .metatileAttributes = gMetatileAttributes_{name}, .callback = '+('NULL' if side=='secondary' else 'InitTilesetAnim_General')+' };')
layouts=read('data/layouts/layouts.json');layout=copy.deepcopy(next(l for l in layouts['layouts'] if l['id']=='LAYOUT_CHERRYGROVE_CITY'));layout.update(id='LAYOUT_SANDGEM_TOWN',name='SandgemTown_Layout',width=48,height=40,primary_tileset='gTileset_SandgemPrimary',secondary_tileset='gTileset_Sandgem',border_filepath='data/layouts/SandgemTown/border.bin',blockdata_filepath='data/layouts/SandgemTown/map.bin')
layouts['layouts']=[l for l in layouts['layouts'] if l['id']!='LAYOUT_SANDGEM_TOWN']+[layout];write('data/layouts/layouts.json',layouts)
sections=read('src/data/region_map/region_map_sections.json')
if not any(s['id']=='MAPSEC_SANDGEM_TOWN' for s in sections['map_sections']):sections['map_sections'].append(dict(id='MAPSEC_SANDGEM_TOWN',name='SANDGEM TOWN',x=1,y=1,width=1,height=1))
write('src/data/region_map/region_map_sections.json',sections)
f=G/'include/regions.h';s=f.read_text()
if 'case MAPSEC_SANDGEM_TOWN:' not in s:s=s.replace('switch (sectionId) {','switch (sectionId) {\n    case MAPSEC_SANDGEM_TOWN: return REGION_SINNOH;');f.write_text(s)
spec=json.loads((A/'layout.json').read_text());town=read('data/maps/CherrygroveCity/map.json');town.update(id='MAP_SANDGEM_TOWN',name='SandgemTown',layout='LAYOUT_SANDGEM_TOWN',region='REGION_SINNOH',region_map_section='MAPSEC_SANDGEM_TOWN',music='MUS_OLDALE',connections=None,warp_events=[],object_events=[],coord_events=[],bg_events=[])
newmaps=['SandgemTown']+[b['interior'] for b in spec['buildings']]+['SandgemCenterUpstairs']
for i,b in enumerate(spec['buildings']):town['warp_events'].append(dict(x=b['door'][0],y=b['door'][1],elevation=0,dest_map=mapid(b['interior']),dest_warp_id='0'))
# Southbound stepping transitions back to the northern Johto approach.
for i,x in enumerate(range(28,31)):town['warp_events'].append(dict(x=x,y=32,elevation=0,dest_map='MAP_CHERRYGROVE_ROUTE30_APPROACH',dest_warp_id=str(min(i,2))))
cast=read('data/maps/CherrygroveCity/map.json')['object_events'];res=[]
for i,(key,x,y) in enumerate([('COMPARE_SINNOH',26,17),('COMPARE_HOENN',34,17),('COMPARE_KANTO',17,24),('COMPARE_JOHTO',26,24),('COMPARE_UNOVA',33,27),('JOHTO_BOY',19,20)]):
 o=copy.deepcopy(next(o for o in cast if o['local_id']=='LOCALID_'+key));o.update(local_id='LOCALID_VISITOR_'+str(i),x=x,y=y,movement_type='MOVEMENT_TYPE_WALK_LEFT_AND_RIGHT',movement_range_x=1,movement_range_y=0,script='SandgemTown_Visitor',flag='0');town['object_events'].append(o);res.append(dict(name=key,start=[x,y],positions=[[x,y],[x-1,y]]))
base_scripts='SandgemTown_MapScripts::\n\t.byte 0\n\nSandgemTown_Visitor::\n\tlock\n\tfaceplayer\n\tmsgbox SandgemTown_VisitorText, MSGBOX_DEFAULT\n\trelease\n\tend\n\nSandgemTown_VisitorText::\n\t.string "The sea breeze is cool here.\\nSANDGEM is a peaceful place to walk.$"\n'
(G/'data/maps/SandgemTown').mkdir(exist_ok=True);write('data/maps/SandgemTown/map.json',town);(G/'data/maps/SandgemTown/scripts.inc').write_text(base_scripts)
(A/'residents.json').write_text(json.dumps(res,indent=2)+'\n')
for i,b in enumerate(spec['buildings']):
 name=b['interior'];donor='LittlerootTown_ProfessorBirchsLab' if b['name']=='Lab' else 'CherrygrovePokemonCenter' if b['name']=='PokemonCenter' else 'CherrygroveMart' if b['name']=='Mart' else 'CherrygroveHarborHouse';m=read(f'data/maps/{donor}/map.json');m.update(id=mapid(name),name=name,region='REGION_SINNOH',region_map_section='MAPSEC_SANDGEM_TOWN',build_target='emerald',allow_running=True,coord_events=[],bg_events=[],connections=None)
 if b['name']=='Lab':m['object_events']=[]
 if b['name'] in ['HouseWest','HouseSouth']:m['object_events']=[]
 for o in m['object_events']:o['script']=o['script'].replace(donor,name)
 for w in m['warp_events']:
  if w['dest_map']=='MAP_CHERRYGROVE_CENTER_UPSTAIRS':w['dest_map']='MAP_SANDGEM_CENTER_UPSTAIRS'
  else:w.update(dest_map='MAP_SANDGEM_TOWN',dest_warp_id=str(i))
 folder=G/f'data/maps/{name}';folder.mkdir(exist_ok=True);write(f'data/maps/{name}/map.json',m)
 scripts=(G/f'data/maps/{donor}/scripts.inc').read_text().replace(donor,name) if b['name'] in ['PokemonCenter','Mart'] else f'{name}_MapScripts::\n\t.byte 0\n'
 (folder/'scripts.inc').write_text(scripts)
name='SandgemCenterUpstairs';m=read('data/maps/CherrygroveCenterUpstairs/map.json');m.update(id=mapid(name),name=name,region='REGION_SINNOH',region_map_section='MAPSEC_SANDGEM_TOWN');m['warp_events'][0]['dest_map']='MAP_SANDGEM_POKEMON_CENTER';(G/f'data/maps/{name}').mkdir(exist_ok=True);write(f'data/maps/{name}/map.json',m);(G/f'data/maps/{name}/scripts.inc').write_text(f'{name}_MapScripts::\n\t.byte 0\n')
groups=read('data/maps/map_groups.json')
for name in newmaps:
 if name not in groups['gMapGroup_Cherrygrove']:groups['gMapGroup_Cherrygrove'].append(name)
 append('data/event_scripts.s',f'.include "data/maps/{name}/scripts.inc"')
write('data/maps/map_groups.json',groups)
# Clone only three approach tiles with north-arrow behavior; no change to town.
D=G/'data/tilesets/secondary/cherrygrove';OLD=B/'data/tilesets/secondary/cherrygrove';blocks=list(struct.iter_unpack('<8H',(OLD/'metatiles.bin').read_bytes()));attrs=list(struct.unpack('<'+'H'*((OLD/'metatile_attributes.bin').stat().st_size//2),(OLD/'metatile_attributes.bin').read_bytes()));grid=list(struct.unpack('<1440H',(B/'data/layouts/CherrygroveRoute30Approach/map.bin').read_bytes()));added=[]
for x in range(43,46):
 mid=grid[12*80+x]&1023;assert mid>=512;clone=512+len(blocks);blocks.append(blocks[mid-512]);attrs.append((attrs[mid-512]&~255)|0x64);grid[12*80+x]=0x3000|clone;added.append(clone)
(D/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*b) for b in blocks));(D/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(attrs),*attrs));(G/'data/layouts/CherrygroveRoute30Approach/map.bin').write_bytes(struct.pack('<1440H',*grid))
m=read('data/maps/CherrygroveRoute30Approach/map.json');m['warp_events']=[dict(x=x,y=12,elevation=0,dest_map='MAP_SANDGEM_TOWN',dest_warp_id=str(5+i)) for i,x in enumerate(range(43,46))];write('data/maps/CherrygroveRoute30Approach/map.json',m)
f=G/'src/apocrypha_map_proof.c';s=f.read_text();a=s.index('const u16 sMapProofMaps[]');b=s.index(';',a);existing=s[a:b]
for name in newmaps:
 id=mapid(name)
 if id not in existing:existing=existing[:-1].rstrip()+', '+id+'}'
s=s[:a]+existing+s[b:];f.write_text(s)
assert (G/'data/layouts/CherrygroveCity/map.bin').read_bytes()==(B/'data/layouts/CherrygroveCity/map.bin').read_bytes()
print('Installed',newmaps,'; Cherrygrove layout byte-identical.')
