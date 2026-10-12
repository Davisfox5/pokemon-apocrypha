#!/usr/bin/env python3
"""Prepare disposable map qualification data; never run against production game/."""
import json, re, shutil, struct, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
game = Path(sys.argv[1]).resolve()
assert game != ROOT / 'game' and (game / '.git').is_dir()

def read(p): return (game/p).read_text()
def write(p,s): (game/p).write_text(s)
def dump(p,j): write(p,json.dumps(j,indent=2)+'\n')
def replace(p,a,b):
 s=read(p); assert a in s,(p,a); write(p,s.replace(a,b))

# Separate compile target from geography; default upstream behavior is unchanged.
p='tools/mapjson/mapjson.cpp'
replace(p, 'if ((version == "emerald" && region != "REGION_HOENN")\n         || (version == "firered" && region != "REGION_KANTO")) {',
 '''string build_target = json_to_string(map_data, "build_target", true);
        if (build_target.empty() ? ((version == "emerald" && region != "REGION_HOENN")
         || (version == "firered" && region != "REGION_KANTO")) : build_target != version) {''')
replace(p, 'if ((version == "emerald" && layout_version != "emerald")\n         || (version == "firered" && layout_version != "frlg"))',
 '''if (json_to_string(layout, "build_target", true).empty()
            ? ((version == "emerald" && layout_version != "emerald") || (version == "firered" && layout_version != "frlg"))
            : json_to_string(layout, "build_target", true) != version)''')
replace(p, 'if ((version == "emerald" && layout_version != "emerald") || (version == "firered" && layout_version != "frlg")) {',
 '''if (json_to_string(layout, "build_target", true).empty()
            ? ((version == "emerald" && layout_version != "emerald") || (version == "firered" && layout_version != "frlg"))
            : json_to_string(layout, "build_target", true) != version) {''')

# Explicitly include only two existing Kanto tilesets in this Emerald proof.
for file in ['graphics.h','metatiles.h','headers.h']:
 path='src/data/tilesets/'+file;s=read(path);extra=[]
 if file=='graphics.h':
  pats=[r'const u16 ALIGNED\(4\) gTilesetPalettes_General_Frlg\[\]\[16\]\s*=\s*\{.*?\n\};',r'const u32 gTilesetTiles_General_Frlg\[\].*?;',r'const u16 gTilesetPalettes_PalletTown\[\]\[16\]\s*=\s*\{.*?\n\};',r'const u32 gTilesetTiles_PalletTown\[\].*?;']
 elif file=='metatiles.h':pats=[rf'const u16 {sym}\[\].*?;' for sym in ['gMetatiles_General_Frlg','gMetatileAttributes_General_Frlg','gMetatiles_PalletTown','gMetatileAttributes_PalletTown']]
 else:pats=[rf'const struct Tileset {sym}\s*=\s*\{{.*?\n\}};' for sym in ['gTileset_General_Frlg','gTileset_PalletTown']]
 for pat in pats:
  m=re.search(pat,s,re.S); assert m,pat
  t=m[0].replace('General_Frlg','ProofKantoGeneral').replace('PalletTown','ProofKantoPallet').replace('InitTilesetAnim_ProofKantoGeneral','NULL')
  extra.append(t)
 write(path,s+'\n// Isolated qualification: native Kanto art, no donor story scripts.\n'+'\n'.join(extra)+'\n')

regions=['Hoenn','Johto','Kanto','Sinnoh','Unova']
groups=json.loads(read('data/maps/map_groups.json')); layouts=json.loads(read('data/layouts/layouts.json'));sections=json.loads(read('src/data/region_map/region_map_sections.json'))
base=json.loads(read('data/maps/LittlerootTown/map.json'))
pallet=next(l for l in layouts['layouts'] if l['id']=='LAYOUT_PALLET_TOWN')
for n,region in enumerate(regions):
 name='MapProof'+region; mid='MAP_PROOF_'+region.upper(); lid='LAYOUT_MAP_PROOF_'+region.upper(); sec='MAPSEC_PROOF_'+region.upper(); path=game/'data/maps'/name;path.mkdir()
 group='gMapGroup_Proof'+region; groups['group_order'].append(group);groups[group]=[name]
 sections['map_sections'].append(dict(id=sec,name=region.upper()+' MAP TEST',x=1+n,y=1,width=1,height=1))
 layout=dict(id=lid,name=name+'_Layout',width=24,height=20,primary_tileset='gTileset_General',secondary_tileset='gTileset_Petalburg',border_filepath=f'data/layouts/{name}/border.bin',blockdata_filepath=f'data/layouts/{name}/map.bin',layout_version='emerald',build_target='emerald')
 folder=game/'data/layouts'/name;folder.mkdir()
 if region=='Kanto':
  layout.update(primary_tileset='gTileset_ProofKantoGeneral',secondary_tileset='gTileset_ProofKantoPallet',layout_version='frlg',border_width=2,border_height=2)
  shutil.copyfile(game/pallet['blockdata_filepath'],folder/'map.bin');shutil.copyfile(game/pallet['border_filepath'],folder/'border.bin')
 else:
  if region=='Unova':layout.update(width=80,height=80)
  w,h=layout['width'],layout['height'];grid=[0x3001]*(w*h)
  # Solid perimeter except reciprocal east/west connection between Johto and Sinnoh.
  for y in range(h):
   for x in range(w):
    if x in (0,w-1) or y in (0,h-1):grid[y*w+x]=0x3c0e
  if region=='Johto':
   for y in range(8,15):grid[y*w+w-1]=0x3001
  if region=='Sinnoh':
   for y in range(8,15):grid[y*w]=0x3001
  grid[11*w+12]=0x3c0e # collision sentinel for movement verification
  (folder/'map.bin').write_bytes(struct.pack('<'+'H'*len(grid),*grid));(folder/'border.bin').write_bytes(struct.pack('<4H',*([0x3c0e]*4)))
 layouts['layouts'].append(layout)
 m={k:v for k,v in base.items() if k not in ['object_events','warp_events','coord_events','bg_events','connections']}
 m.update(id=mid,name=name,layout=lid,region='REGION_'+region.upper(),build_target='emerald',region_map_section=sec,show_map_name=True,connections=None,object_events=[],warp_events=[],coord_events=[],bg_events=[])
 if region in ['Johto','Sinnoh']:m['connections']=[dict(map='MAP_PROOF_'+('SINNOH' if region=='Johto' else 'JOHTO'),offset=0,direction='right' if region=='Johto' else 'left')]
 # Scripted transport uses the ordinary warp command, without donor events.
 m['object_events']=[dict(local_id='LOCALID_PROOF_GUIDE',graphics_id='OBJ_EVENT_GFX_SCIENTIST_1',x=10,y=10,elevation=3,movement_type='MOVEMENT_TYPE_FACE_DOWN',movement_range_x=0,movement_range_y=0,trainer_type='TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id='0',script=name+'_Guide',flag='0')]
 nxt='MAP_PROOF_'+regions[(n+1)%5].upper()
 script=f'''{name}_MapScripts::
    .byte 0

{name}_Guide::
    lock
    faceplayer
    setvar VAR_TEMP_1, 77
    msgbox {name}_Text, MSGBOX_DEFAULT
    warp {nxt}, 10, 11
    waitstate
    release
    end

{name}_Text:
    .string "{region.upper()} MAP PIPELINE TEST.\\nNext region, please!$"
'''
 (path/'scripts.inc').write_text(script);(path/'map.json').write_text(json.dumps(m,indent=2)+'\n')
 # Map scripts are aggregated explicitly upstream.
 with (game/'data/event_scripts.s').open('a') as f:f.write(f'\n.include "data/maps/{name}/scripts.inc"\n')

dump('data/maps/map_groups.json',groups);dump('data/layouts/layouts.json',layouts);dump('src/data/region_map/region_map_sections.json',sections)
# Runtime geography proof without inventing final location IDs or changing existing ones.
replace('include/regions.h','    if (sectionId >= KANTO_MAPSEC_START', '    switch (sectionId) {\n'+''.join(f'    case MAPSEC_PROOF_{r.upper()}: return REGION_{r.upper()};\n' for r in regions)+'    }\n    if (sectionId >= KANTO_MAPSEC_START')
replace('src/new_game.c','SetWarpDestination(MAP_GROUP(MAP_INSIDE_OF_TRUCK), MAP_NUM(MAP_INSIDE_OF_TRUCK), WARP_ID_NONE, -1, -1);','SetWarpDestination(MAP_GROUP(MAP_PROOF_HOENN), MAP_NUM(MAP_PROOF_HOENN), WARP_ID_NONE, 10, 11);')
replace('src/overworld.c','gFieldCallback = ExecuteTruckSequence;','gFieldCallback = NULL; // isolated map qualification starts outdoors')
replace('src/new_game.c', 'void NewGameInitData(void)\n{', 'extern void MapProof_Keep(void);\nvoid NewGameInitData(void)\n{\n    MapProof_Keep();')
shutil.copyfile(ROOT/'tools/gba/maps/probe.c' ,game/'src/apocrypha_map_proof.c')
print(json.dumps({'maps':len(regions),'appended_group_ids':list(range(len(groups['group_order'])-5,len(groups['group_order']))),'largest_layout':[80,80],'largest_grid_cells':95*94,'kanto':'native FRLG layout and art in an Emerald ROM'},indent=2))
