#!/usr/bin/env python3
"""Compile an editable Cherrygrove town proposal into an isolated qualified checkout."""
import json,struct,shutil,sys,re
from pathlib import Path
from PIL import Image
from tiles import Tileset
ROOT=Path(__file__).resolve().parents[3]
game=Path(sys.argv[1]).resolve()
assert game != ROOT/'game' and (game/'.git').is_dir()
if (game/'data/maps/CherrygroveCity').exists():
 assert '--refresh-generated' in sys.argv, 'Town already exists. Preserve native editor changes in the source patch before explicitly refreshing generated data.'
 import subprocess
 expected='b01afeda981936736c0deb49376f8575e88ea533'
 assert subprocess.check_output(['git','-C',str(game),'rev-parse','HEAD'],text=True).strip()==expected
 # Refresh only files owned by this isolated compiler from its qualified baseline.
 for name in ['tools/mapjson/mapjson.cpp','src/data/tilesets/graphics.h','src/data/tilesets/metatiles.h','src/data/tilesets/headers.h','data/layouts/layouts.json','data/maps/map_groups.json','src/data/region_map/region_map_sections.json','include/regions.h','src/new_game.c','src/apocrypha_map_proof.c','data/event_scripts.s']:
  (game/name).write_bytes(subprocess.check_output(['git','-C',str(game),'show','HEAD:'+name]))
spec=json.loads((ROOT/'gba/maps/cherrygrove/town.json').read_text())
def load(p):return json.loads((game/p).read_text())
def dump(p,v):
 p=game/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def append(p,s):
 with (game/p).open('a') as f:f.write('\n'+s+'\n')
def replace(p,a,b):
 p=game/p;s=p.read_text();assert a in s,(p,a);p.write_text(s.replace(a,b))
def binary(p,values,size='H'):
 p=game/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(struct.pack('<'+size*len(values),*values))

# A map-local native tileset. Existing pixel indices are preserved; this compiler
# changes palette data and composes/remaps existing 8x8 tile references.
base=Tileset(game); boat=Tileset(game,'slateport')
primary=game/'data/tilesets/primary/cherrygrove'
secondary=game/'data/tilesets/secondary/cherrygrove'
shutil.copytree(base.dirs[0],primary,dirs_exist_ok=True);shutil.copytree(base.dirs[1],secondary,dirs_exist_ok=True)
# Warm stone/sand, muted grass, teal water; local blossom accent has its own bank.
def grade(rgb):
 r,g,b=rgb
 if max(rgb)-min(rgb)<25:
  return (min(255,int(r*.92+13)),min(255,int(g*.94+7)),min(255,int(b*.94+1)))
 if g>r*1.12 and g>b*1.1:return (min(255,int(r*.88+10)),int(g*.83+10),min(255,int(b*.94+20)))
 if b>r*1.18 and b>g*.95:return (int(r*.70+9),min(255,int(g*.87+14)),int(b*.75+20))
 return (min(255,int(r*.94+8)),min(255,int(g*.92+7)),min(255,int(b*.86+6)))
def palwrite(folder,n,colors):
 (folder/'palettes'/f'{n:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in colors)+'\n')
for folder,oldpals in [(primary,base.pals[0]),(secondary,base.pals[1])]:
 for n,colors in enumerate(oldpals):palwrite(folder,n,[grade(c) for c in colors])
pink=[grade(c) for c in base.pals[0][2]]
pink[1:5]=[(255,220,218),(232,159,174),(192,103,139),(109,68,98)]
palwrite(secondary,7,pink)
palwrite(secondary,11,[grade(c) for c in boat.pals[1][8]])
palwrite(secondary,12,[grade(c) for c in boat.pals[1][11]])
palwrite(secondary,9,[grade(c) for c in boat.pals[1][6]])
amber=[grade(c) for c in base.pals[0][1]]
amber[11:15]=[(246,215,147),(216,177,105),(178,131,76),(123,90,60)]
palwrite(secondary,10,amber)
blocks=list(base.blocks[1]);attrs=list(base.attrs[1]);tiles=list(base.tiles[1]);tile_ids={}
def add(entries,attr=0):
 mid=512+len(blocks);assert mid<1023;blocks.append(tuple(entries));attrs.append(attr);return mid
blossoms={}
for mid in [0xe,0x1d4,0x1d5,0x1e4,0x1e5,0x1f4,0x1f5]:
 e=list(base.blocks[0][mid]);e=[((v&0xfff)|0x7000) if v>>12==2 and (v&1023) not in (2,3) else v for i,v in enumerate(e)]
 blossoms[mid]=add(e,base.attrs[0][mid])
def import_block(mid,background=None):
 entries=list(boat.blocks[1][mid-512]);new=[]
 for i,e in enumerate(entries):
  tid=e&1023;bank=e>>12
  if background is not None and i<4:new.append(base.blocks[0][background][i]);continue
  if tid>=512:
   if tid not in tile_ids:tile_ids[tid]=512+len(tiles);tiles.append(boat.tiles[1][tid-512])
   e=(e&~1023)|tile_ids[tid]
  if bank>=6:
   assert bank in (6,8,11),(hex(mid),bank)
   e=(e&0xfff)|({6:9,8:11,11:12}[bank]<<12)
  new.append(e)
 return add(new,0)
boats=[import_block(m,0x170) for m in [0x220,0x221,0x222,0x228,0x229,0x22a]]
chairs=[import_block(m,1) for m in [0x2e0,0x2e1,0x2f0,0x2f1]]
nets=[import_block(m,0x121) for m in [0x2c8,0x2c9]]
# Gold's weathered amber roof distinguishes his house without a monument.
gold_roof={mid:add([(e&0xfff)|0xa000 if e>>12==1 else e for e in base.blocks[0][mid]],base.attrs[0][mid]) for mid in [8,9,10,16,17,18,24,25,26]}
# Petals use native flower tiles with blossom colors on a plain grass base.
flower=list(base.blocks[0][4]);flower=[(e&0xfff)|0x7000 if i>=4 and e>>12==2 else e for i,e in enumerate(flower)]
petals=add(flower)
# Native wood wall strips composed into weathered decking; no tile pixels edited.
wood=list(base.blocks[0][0x014]);deck=add(wood)
rail=add(wood[:4]+list(base.blocks[0][0x132][4:]))
assert len(tiles)<=512,len(tiles)
im=Image.new('P',(128,((len(tiles)+15)//16)*8));im.putpalette(Image.open(secondary/'tiles.png').getpalette())
for i,t in enumerate(tiles):
 for y in range(8):
  for x in range(8):im.putpixel(((i%16)*8+x,(i//16)*8+y),t[y*8+x])
im.save(secondary/'tiles.png')
binary('data/tilesets/secondary/cherrygrove/metatiles.bin',[e for m in blocks for e in m]);binary('data/tilesets/secondary/cherrygrove/metatile_attributes.bin',attrs)
for p,part,label,secflag,callback in [('primary',primary,'CherrygrovePrimary','FALSE','InitTilesetAnim_General'),('secondary',secondary,'Cherrygrove','TRUE','NULL')]:
 rel=f'data/tilesets/{p}/cherrygrove'
 append('src/data/tilesets/graphics.h',f'const u32 gTilesetTiles_{label}[] = INCGFX_U32("{rel}/tiles.png", ".4bpp.fastSmol");\nconst u16 gTilesetPalettes_{label}[][16] = {{\n'+''.join(f'INCGFX_U16("{rel}/palettes/{n:02}.pal", ".gbapal"),\n' for n in range(16))+'};')
 append('src/data/tilesets/metatiles.h',f'const u16 gMetatiles_{label}[] = INCBIN_U16("{rel}/metatiles.bin");\nconst u16 gMetatileAttributes_{label}[] = INCBIN_U16("{rel}/metatile_attributes.bin");')
 append('src/data/tilesets/headers.h',f'const struct Tileset gTileset_{label} = {{ .isCompressed = TRUE, .isSecondary = {secflag}, .tiles = gTilesetTiles_{label}, .palettes = gTilesetPalettes_{label}, .metatiles = gMetatiles_{label}, .metatileAttributes = gMetatileAttributes_{label}, .callback = {callback} }};')

W,H=spec['width'],spec['height'];grid=[0x3001]*(W*H)
def rect(x,y,w,h,mid,solid=False):
 for yy in range(y,y+h):
  for xx in range(x,x+w):
   if 0<=xx<W and 0<=yy<H:grid[yy*W+xx]=(0x3c00 if solid else 0x3000)|mid

def stamp(x,y,rows,raw=False):
 for yy,row in enumerate(rows):
  for xx,m in enumerate(row):
   if m is not None:grid[(y+yy)*W+x+xx]=m if raw else 0x3c00|m

def tree(x,y,pink=False):
 mids=[0x1d4,0x1d5,0x1e4,0x1e5,0x1f4,0x1f5]
 if pink:mids=[blossoms[m] for m in mids]
 stamp(x,y,[mids[:2],mids[2:4],mids[4:]])
# Closed natural boundaries, west and south coast, inland tree walls.
rect(0,0,4,H,0x170,True);rect(0,34,W,6,0x170,True)
rect(4,30,40,4,0x121)
for x in range(4,44,2):
 if not 14<=x<18:tree(x,0);tree(x,2)
for y in range(4,29,3):
 tree(4,y)
 if not 16<=y<=22:tree(42,y)
# Curving coast break and sandy approach to the waterfront.
for y in range(4,30):rect(3,y,1,1,0x123,True)
for x in range(4,44):rect(x,33,1,1,0x12c,True)
# Main lanes. Paths use the native sand family with connected edge selection.
path=set()
def lane(x,y,w,h):
 for yy in range(y,y+h):
  for xx in range(x,x+w):path.add((xx,yy))
lane(14,0,4,31);lane(9,17,35,4);lane(9,15,3,5);lane(23,8,3,11);lane(32,9,3,11)
lane(6,25,10,3);lane(25,20,3,11);lane(35,27,3,5);lane(7,8,9,3)
for x,y in path:
 n=(x,y-1) in path;s=(x,y+1) in path;w=(x-1,y) in path;e=(x+1,y) in path
 mid=0x121
 if not n:mid=0x119
 if not s:mid=0x129
 if not w:mid=0x120 if n and s else (0x118 if not n else 0x128)
 if not e:mid=0x122 if n and s else (0x11a if not n else 0x12a)
 rect(x,y,1,1,mid)
# Small park, framed by mature cherry trees; Gold's garden and battle clearing.
for x,y in [(7,3),(10,3),(6,6),(10,6),(19,11),(22,11),(29,13),(30,17),(20,22),(30,23),(9,28),(11,28),(38,6),(38,10)]:tree(x,y,True)
for x,y in [(8,8),(9,9),(11,9),(20,15),(28,20),(29,21),(28,26),(18,23)]:rect(x,y,1,1,petals)
rect(23,22,7,4,0x10c)
# Worn practice ring: light stone corners, open center, no monument.
for x,y,m in [(23,22,0x118),(29,22,0x11a),(23,25,0x128),(29,25,0x12a)]:rect(x,y,1,1,m)
# Buildings have explicit door coordinates and preserve native warp behavior.
house=[[0x408,0x409,0x409,0x409,0x40a],[0x410,0x411,0x411,0x411,0x412],[0x418,0x40b,0x419,0x40b,0x41a],[0x420,0x413,0x421,0x413,0x422]]
mart=[[0x430,0x431,0x432,0x433],[0x438,0x439,0x43a,0x43b],[0x460,0x441,0x442,0x443]]
center=[[0x3048,0x3049,0x304a,0x304b],[0x450,0x451,0x452,0x453],[0x458,0x459,0x45a,0x45b],[0x460,0x461,0x462,0x463]]
for b in spec['buildings']:
 rows=dict(house=house,mart=mart,center=center)[b['style']]
 if b['name']=='GoldHouse':rows=[[(m&~1023)|gold_roof.get(m&1023,m&1023) for m in row] for row in rows]
 stamp(b['x'],b['y'],rows,True)
# Wooden pier and two idle boats: decoration and collision only; no boarding warps.
rect(21,31,3,8,deck)
stamp(17,35,[boats[:3],boats[3:]])
stamp(25,34,[boats[:3],boats[3:]])
stamp(27,31,[nets])
# Beach seating and a small SE lookout; reused native deck-chair components.
stamp(10,9,[chairs[:2],chairs[2:]])
rect(34,30,7,3,deck)
stamp(37,30,[chairs[:2],chairs[2:]])
# Low white fence at the end of the lookout, keeping the sea non-walkable.
rect(34,32,7,1,rail,True)
# Signs and unobtrusive flowerbeds beside homes.
for x,y in [(12,17),(18,2),(40,17),(28,21),(20,30)]:rect(x,y,1,1,3,True)
for x,y in [(7,16),(11,16),(23,21),(27,21),(34,28),(38,28)]:rect(x,y,1,1,4)
# Solid cap at the end of the pier, as with the lookout.
rect(21,38,3,1,rail,True)

layouts=load('data/layouts/layouts.json');groups=load('data/maps/map_groups.json');sections=load('src/data/region_map/region_map_sections.json')
section='MAPSEC_CHERRYGROVE_CITY';sections['map_sections'].append(dict(id=section,name='CHERRYGROVE CITY',x=3,y=6,width=1,height=1))
replace('include/regions.h','    switch (sectionId) {',f'    switch (sectionId) {{\n    case {section}: return REGION_JOHTO;')
names=['CherrygroveCity']+['Cherrygrove'+b['name'] for b in spec['buildings']]+['CherrygrovePlayerBedroom','CherrygroveCenterUpstairs','CherrygroveRoute29Approach','CherrygroveRoute30Approach']
group_id=len(groups['group_order']);assert group_id==80
groups['group_order'].append('gMapGroup_Cherrygrove');groups['gMapGroup_Cherrygrove']=names
ids={n:'MAP_'+re.sub(r'(?<!^)(?=[A-Z])','_',n).upper() for n in names}
# Explicit words keep familiar constants in the runtime harness.
ids={n:'MAP_CHERRYGROVE_'+re.sub(r'(?<!^)(?=[A-Z])','_',n.removeprefix('Cherrygrove')).upper() for n in names}
base_map=load('data/maps/PetalburgCity/map.json')
maps={};scripts={}
def newmap(name,layout,indoors=False):
 m={k:v for k,v in base_map.items() if k not in ['object_events','warp_events','coord_events','bg_events','connections']}
 m.update(id=ids[name],name=name,layout=layout,region='REGION_JOHTO',build_target='emerald',region_map_section=section,music='MUS_LITTLEROOT',weather='WEATHER_NONE' if indoors else 'WEATHER_SUNNY',map_type='MAP_TYPE_INDOOR' if indoors else 'MAP_TYPE_CITY',show_map_name=not indoors,allow_cycling=False,connections=None,object_events=[],warp_events=[],coord_events=[],bg_events=[])
 maps[name]=m;scripts[name]=f'{name}_MapScripts::\n    .byte 0\n';return m

def newlayout(name,grid,w,h,primary='gTileset_CherrygrovePrimary',secondary='gTileset_Cherrygrove'):
 lid='LAYOUT_'+ids[name].removeprefix('MAP_');folder=f'data/layouts/{name}'
 binary(folder+'/map.bin',grid);binary(folder+'/border.bin',[(0x3c00|0x170) if name=='CherrygroveCity' else 0x3c0e]*4)
 layouts['layouts'].append(dict(id=lid,name=name+'_Layout',width=w,height=h,primary_tileset=primary,secondary_tileset=secondary,border_filepath=folder+'/border.bin',blockdata_filepath=folder+'/map.bin',layout_version='emerald',build_target='emerald'))
 return lid

town=newmap(names[0],newlayout(names[0],grid,W,H));town['connections']=[dict(map=ids[names[-2]],offset=0,direction='right'),dict(map=ids[names[-1]],offset=0,direction='up')]

def warp(x,y,dest,index,elevation=0):return dict(x=x,y=y,elevation=elevation,dest_map=ids[dest],dest_warp_id=str(index))
def text_event(name,label,text):
 full=name+'_'+label
 escaped=text.replace('\\','\\')
 scripts[name]+=f'\n{full}::\n    msgbox {full}_Text, MSGBOX_NPC\n    end\n\n{full}_Text:\n    .string "{escaped}$"\n'
 return full

def npc(name,gfx,x,y,label,text):
 scr=text_event(name,label,text)
 maps[name]['object_events'].append(dict(local_id='LOCALID_'+label.upper(),graphics_id='OBJ_EVENT_GFX_'+gfx,x=x,y=y,elevation=3,movement_type='MOVEMENT_TYPE_FACE_DOWN',movement_range_x=0,movement_range_y=0,trainer_type='TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id='0',script=scr,flag='0'))

def sign(x,y,label,text):
 script=text_event(names[0],label,text)
 town['bg_events'].append(dict(type='sign',x=x,y=y,elevation=0,player_facing_dir='BG_EVENT_PLAYER_FACING_ANY',script=script))
for b in spec['buildings']:
 name='Cherrygrove'+b['name'];i=names.index(name)
 donor='PetalburgCity_House1'
 if b['name']=='PlayerHouse':donor='LittlerootTown_BrendansHouse_1F'
 if b['name']=='PokemonCenter':donor='PetalburgCity_PokemonCenter_1F'
 if b['name']=='Mart':donor='PetalburgCity_Mart'
 old=load('data/maps/'+donor+'/map.json');m=newmap(name,old['layout'],True)
 index=len(town['warp_events']);town['warp_events'].append(warp(*b['door'],name,0))
 m['warp_events']=[warp(w['x'],w['y'],names[0],index,w['elevation']) for w in old['warp_events'][:2]]
 if b['name']=='PlayerHouse':m['warp_events'].append(warp(8,2,'CherrygrovePlayerBedroom',0));npc(name,'MOM',5,4,'Mother','Our new home!\\nTake a look around, honey.')
 if b['name']=='PlayerHouse':
  npc(name,'MOVING_BOX',4,6,'BoxOne','A box from the move.')
  npc(name,'MOVING_BOX',5,6,'BoxTwo','Still waiting to be unpacked.')
 if b['name']=='TransplantHouse':npc(name,'WOMAN_2',5,4,'Resident','We moved here for the quiet.\\nJust like Gold did.')
 if b['name']=='NeighborHouse':npc(name,'FAT_MAN',5,4,'Neighbor','Gold has made a home here.\\nWe look after our neighbors.')
 if b['name']=='PokemonCenter':
  m['music']='MUS_POKE_CENTER';m['warp_events'].append(warp(1,6,'CherrygroveCenterUpstairs',0,4))
  npc(name,'NURSE',7,2,'Nurse','Welcome to our POKEMON CENTER!')
  # Reuse the system nurse, without the donor's campaign transition callbacks.
  scripts[name]=f'{name}_MapScripts::\n    .byte 0\n\n{name}_Nurse::\n    setvar VAR_0x800B, LOCALID_NURSE\n    call Common_EventScript_PkmnCenterNurse\n    waitmessage\n    waitbuttonpress\n    release\n    end\n'
 if b['name']=='Mart':
  npc(name,'MART_EMPLOYEE',1,3,'Clerk','Welcome!')
  scripts[name]=f'{name}_MapScripts::\n    .byte 0\n\n{name}_Clerk::\n    lock\n    faceplayer\n    message gText_HowMayIServeYou\n    waitmessage\n    pokemart {name}_Stock\n    msgbox gText_PleaseComeAgain, MSGBOX_DEFAULT\n    release\n    end\n\n    .align 2\n{name}_Stock:\n    .2byte ITEM_POTION\n    .2byte ITEM_ANTIDOTE\n    .2byte ITEM_PARALYZE_HEAL\n    pokemartlistend\n'
# Upstairs rooms preserve working reciprocal stairs, but have no donor scene scripts.
for name,donor,dest,index in [('CherrygrovePlayerBedroom','LittlerootTown_BrendansHouse_2F','CherrygrovePlayerHouse',2),('CherrygroveCenterUpstairs','PetalburgCity_PokemonCenter_2F','CherrygrovePokemonCenter',2)]:
 old=load('data/maps/'+donor+'/map.json');m=newmap(name,old['layout'],True);w=old['warp_events'][0];m['warp_events']=[warp(w['x'],w['y'],dest,index,w['elevation'])]
# Short connected approaches qualify travel. No encounters, teams, rewards or chapter gates.
for name,w,h,side in [(names[-2],16,40,'left'),(names[-1],44,12,'down')]:
 g=[0x3c0e]*(w*h)
 for y in range(h):
  for x in range(w):
   if (side=='left' and 18<=y<22 and x<12) or (side=='down' and 14<=x<18 and y>=4):g[y*w+x]=0x3121
 lid=newlayout(name,g,w,h);m=newmap(name,lid);m['connections']=[dict(map=ids[names[0]],offset=0,direction=side)];m['show_map_name']=False
npc(names[0],'WOMAN_5',19,31,'Waterfront','These boats do not go far anymore.\\nNow they mostly just... sit.')
npc(names[0],'MAN_4',29,18,'Commuter','Half the kids here ride to New Bark\\nfor the labs now. Not Gold.\\pHe came to Cherrygrove to get\\naway from all that humming.')
sign(12,17,'TownSign','CHERRYGROVE CITY\\nWhere the cherry trees and the sea\\plook after their own.')
sign(18,2,'NorthSign','ROUTE 30\\nNorth toward VIOLET CITY')
sign(40,17,'EastSign','ROUTE 29\\nEast toward NEW BARK TOWN')
sign(28,21,'GoldSign','A quiet house and a worn battle yard.\\nA man who has done enough.')
sign(20,30,'WaterfrontSign','CHERRYGROVE WATERFRONT')
for name in names:
 dump('data/maps/'+name+'/map.json',maps[name]);(game/'data/maps'/name/'scripts.inc').write_text(scripts[name]);append('data/event_scripts.s',f'.include "data/maps/{name}/scripts.inc"')
dump('data/maps/map_groups.json',groups);dump('data/layouts/layouts.json',layouts);dump('src/data/region_map/region_map_sections.json',sections)
replace('src/new_game.c','MAP_GROUP(MAP_PROOF_HOENN), MAP_NUM(MAP_PROOF_HOENN), WARP_ID_NONE, 10, 11','MAP_GROUP(MAP_CHERRYGROVE_CITY), MAP_NUM(MAP_CHERRYGROVE_CITY), WARP_ID_NONE, 9, 17')
# Reuse the qualified test entry points; locations are arbitrary map index + coordinates.
probe=(game/'src/apocrypha_map_proof.c').read_text()
a=probe.index('const u16 sMapProofMaps[]');b=probe.index(';',a)+1
probe=probe[:a]+'const u16 sMapProofMaps[] = {'+', '.join(ids[n] for n in names)+'};'+probe[b:]
probe=probe.replace('region % 5','region % '+str(len(names)))
probe=probe.replace('WARP_ID_NONE, 10, 11','WARP_ID_NONE, (region >> 8) & 255, (region >> 16) & 255')
probe=probe.replace('sMapProofMaps[region % '+str(len(names))+']','sMapProofMaps[(region & 255) % '+str(len(names))+']')
(game/'src/apocrypha_map_proof.c').write_text(probe)
# Porymap sees one uniform Emerald-format town tileset. No mixed FRLG layout required.
cfg=game/'porymap.project.cfg'
if cfg.exists():
 t=cfg.read_text().replace('base_game_version=pokeruby','base_game_version=pokeemerald');cfg.write_text(t)
preview=Tileset(game,'cherrygrove','cherrygrove').map_image(grid,W)
out=ROOT/'gba/evidence/cherrygrove';out.mkdir(parents=True,exist_ok=True);preview.save(out/'town-overview.png')
manifest=dict(group=group_id,map_ids=ids,dimensions=[W,H],secondary_tile_count=len(tiles),secondary_metatiles=len(blocks),blossom_metatiles=blossoms,buildings=spec['buildings'],spawn=spec['spawn'],native_formats='Emerald 512/512 tiles, 16-bit metatile attributes',source='Pinned pokeemerald-expansion general, Petalburg and Slateport native assets; map-local palette and metatile composition')
(out/'layout-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
