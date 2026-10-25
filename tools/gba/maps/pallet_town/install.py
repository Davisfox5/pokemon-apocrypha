#!/usr/bin/env python3
"""One-time format adapter for NEW Pallet maps. Refuses existing destinations.
The committed Porymap layouts are authoritative after installation; do not replay.
No image synthesis, quantization or nearest-tile matching: original indices retained.
"""
from pathlib import Path
import json,struct,sys,shutil
from PIL import Image
from native import Bank,words
ROOT=Path(__file__).resolve().parents[4]
ENGINE=Path(sys.argv[1]).resolve()
ART=ROOT/'gba/art/pallet-town'
SPECS=[
 ('ApocPalletTown','PalletTown_Frlg','APOC_PALLET_TOWN','general_frlg','pallet_town_frlg','PalletOutdoor','ApocPallet'),
 ('ApocPalletRedHouse1F','PalletTown_PlayersHouse_1F_Frlg','APOC_PALLET_RED_HOUSE_1F','building_frlg','generic_building_1_frlg','PalletIndoor','PalletRedHouse'),
 ('ApocPalletRedHouse2F','PalletTown_PlayersHouse_2F_Frlg','APOC_PALLET_RED_HOUSE_2F','building_frlg','generic_building_1_frlg','PalletIndoor','PalletRedHouse'),
 ('ApocPalletOakHouse','PalletTown_RivalsHouse_Frlg','APOC_PALLET_OAK_HOUSE','building_frlg','generic_building_2_frlg','PalletIndoor','PalletOakHouse'),
 ('ApocPalletLab','PalletTown_ProfessorOaksLab_Frlg','APOC_PALLET_LAB','building_frlg','lab_frlg','PalletIndoor','PalletLab')]
layouts=json.loads((ENGINE/'data/layouts/layouts.json').read_text());groups=json.loads((ENGINE/'data/maps/map_groups.json').read_text())
for n,*_ in SPECS:assert not (ENGINE/'data/maps'/n).exists(),f'{n} exists; edit current native sources instead'
oldids={json.loads((ENGINE/f'data/maps/{old}/map.json').read_text())['id']:'MAP_'+mid for n,old,mid,*_ in SPECS}
newbanks={};provenance=[]
def dump(p,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2)+'\n')
def makebank(bank,part,name):
 key=(part,name)
 if key in newbanks:return
 folder=ENGINE/'data/tilesets'/('primary' if not part else 'secondary')/('pallettown' if name=='ApocPallet' else name.lower());assert not folder.exists();(folder/'palettes').mkdir(parents=True)
 # Keep global tile IDs, including original animation addresses. Only split ownership changes.
 tiles=(bank.tiles[0][:512] if not part else bank.tiles[0][512:640]+bank.tiles[1]);assert len(tiles)<=512
 im=Image.new('P',(128,((len(tiles)+15)//16)*8));im.putpalette(Image.open(bank.dirs[0]/'tiles.png').getpalette())
 for i,t in enumerate(tiles):im.paste(t,(i%16*8,i//16*8))
 im.save(folder/'tiles.png')
 blocks=bank.blocks[0][:512] if not part else bank.blocks[0][512:640]+bank.blocks[1]
 attrs=bank.attrs[0][:512] if not part else bank.attrs[0][512:640]+bank.attrs[1]
 assert len(blocks)<=512 and all((a&511)<256 for a in attrs)
 (folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*b) for b in blocks))
 (folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(attrs),*[a&255|((a>>29)&3)<<12 for a in attrs]))
 for i in range(16):shutil.copyfile(bank.dirs[i>=7]/'palettes'/f'{i:02}.pal',folder/'palettes'/f'{i:02}.pal')
 # All 16 stored for ordinary editor compatibility; engine loads primary 0..5, secondary 6..12.
 newbanks[key]=folder
 provenance.append(dict(tileset=name,tiles=len(tiles),metatiles=len(blocks),originals=[str(d.relative_to(ENGINE)) for d in bank.dirs],part=part))
for name,old,mid,pr,se,pn,sn in SPECS:
 bank=Bank(ENGINE,'primary/'+pr,'secondary/'+se)
 makebank(bank,0,pn);makebank(bank,1,sn)
 donor=json.loads((ENGINE/f'data/maps/{old}/map.json').read_text());lo=next(l for l in layouts['layouts'] if l['id']==donor['layout'])
 target=ENGINE/'data/layouts'/name;target.mkdir(parents=True)
 for file,key in [('map.bin','blockdata_filepath'),('border.bin','border_filepath')]:shutil.copyfile(ENGINE/lo[key],target/file)
 layouts['layouts'].append(dict(lo,id='LAYOUT_'+mid,name=name+'_Layout',primary_tileset='gTileset_'+pn,secondary_tileset='gTileset_'+sn,border_filepath=f'data/layouts/{name}/border.bin',blockdata_filepath=f'data/layouts/{name}/map.bin',layout_version='emerald',build_target='emerald'))
 m=dict(donor,id='MAP_'+mid,name=name,layout='LAYOUT_'+mid,build_target='emerald',connections=None,object_events=[],coord_events=[],bg_events=[],allow_running=True)
 for w in m['warp_events']:w['dest_map']=oldids[w['dest_map']]
 # New signs and scripts, never donor campaign flags, gifts, rewards or Oak's catch tutorial.
 if name=='ApocPalletTown':
  labels=['LabSign','RedHouseSign','OakHouseSign','TownSign','Memorial']
  m['bg_events']=[dict(e,script=name+'_'+lab) for e,lab in zip(donor['bg_events'],labels)]
 dump(ENGINE/f'data/maps/{name}/map.json',m)
 (ENGINE/f'data/maps/{name}/scripts.inc').write_text(name+'_MapScripts::\n    .byte 0\n')
 groups['gMapGroup_Cherrygrove'].append(name)
 # Exact original native data and reference provenance stay independently inspectable.
 dump(ART/f'source/{name}-reference.json',dict(original_map=old,layout=lo,reference='FRLG source decoded directly, not a screenshot trace',registration=dict(scale=1,origin=[0,0],crop=None,expansion=None)))
for file,obj in [('data/layouts/layouts.json',layouts),('data/maps/map_groups.json',groups)]:dump(ENGINE/file,obj)
for (part,name),folder in newbanks.items():
 rel=str(folder.relative_to(ENGINE));sym=name
 p=ENGINE/'src/data/tilesets/graphics.h'
 with p.open('a') as f:
  f.write(f'\n// Pallet: lossless FRLG native assets, Emerald bank ownership.\nconst u32 gTilesetTiles_{sym}[] = INCGFX_U32("{rel}/tiles.png", ".4bpp.smol");\nconst u16 gTilesetPalettes_{sym}[][16] = {{\n')
  for i in range(16):f.write(f'    INCGFX_U16("{rel}/palettes/{i:02}.pal", ".gbapal"),\n')
  f.write('};\n')
 with (ENGINE/'src/data/tilesets/metatiles.h').open('a') as f:f.write(f'\nconst u16 gMetatiles_{sym}[] = INCBIN_U16("{rel}/metatiles.bin");\nconst u16 gMetatileAttributes_{sym}[] = INCBIN_U16("{rel}/metatile_attributes.bin");\n')
 callback='InitTilesetAnim_General_Frlg' if name=='PalletOutdoor' else 'NULL'
 with (ENGINE/'src/data/tilesets/headers.h').open('a') as f:f.write(f'\nconst struct Tileset gTileset_{sym} = {{\n    .isCompressed = TRUE, .isSecondary = {"TRUE" if part else "FALSE"},\n    .tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym},\n    .metatiles = gMetatiles_{sym}, .metatileAttributes = gMetatileAttributes_{sym},\n    .callback = {callback},\n}};\n')
# Enable ORIGINAL doors against only the new outdoor tileset; no changes to existing entries.
p=ENGINE/'src/field_door.c';s=p.read_text();marker='static const struct DoorGraphics sDoorAnimGraphicsTable[] ='
extra='''extern const struct Tileset gTileset_ApocPallet;
static const u8 sApocPalletDoorTiles[] = INCGFX_U8("graphics/door_anims/pallet.png", ".4bpp");
static const u8 sApocPalletLabDoorTiles[] = INCGFX_U8("graphics/door_anims/oaks_lab.png", ".4bpp");
static const u8 sApocPalletDoorPal[] = {8,8,8,8,8,8,8,8};
static const u8 sApocPalletLabDoorPal[] = {10,10,10,10,10,10,10,10};
'''
s=s.replace(marker,extra+marker)
needle=marker+'\n{';s=s.replace(needle,needle+'''
    {.metatileNum=0x2a3, .tileset=&gTileset_ApocPallet, .sound=DOOR_SOUND_NORMAL, .size=DOOR_SIZE_1x1, .tiles=sApocPalletDoorTiles, .palettes=sApocPalletDoorPal},
    {.metatileNum=0x2ac, .tileset=&gTileset_ApocPallet, .sound=DOOR_SOUND_NORMAL, .size=DOOR_SIZE_1x1, .tiles=sApocPalletLabDoorTiles, .palettes=sApocPalletLabDoorPal},''')
p.write_text(s)
dump(ART/'source/normalization.json',provenance)
print('Appended five native maps; original layouts and shared tilesets untouched.')
