"""Initial Pallet event authoring. Run once after install.py, before owner edits."""
from pathlib import Path
import json,sys
E=Path(sys.argv[1]).resolve()
TEXT={
'ApocPalletTown':{
 'LabSign':"PALLET POKEMON LAB\\nPROFESSOR BLUE",
 'RedHouseSign':"RED'S HOUSE",
 'OakHouseSign':"OAK FAMILY HOME",
 'TownSign':"PALLET TOWN\\nA quiet place of beginnings.",
 'Memorial':"In honor of RED.\\nHis journey began in PALLET TOWN."},
'ApocPalletRedHouse1F':{'Home':"RED'S home.\\nA quiet reminder of his beginnings.", 'TV':"The television is switched off."},
'ApocPalletRedHouse2F':{'Room':"RED'S room.\\nA journey began beyond this window.", 'NES':"An old game console.", 'PC':"A personal computer.\\nIt is switched off."},
'ApocPalletOakHouse':{'Oak':"OAK: I've retired from research.\\nBLUE is KANTO'S professor now.\\pIt's good to have him here in PALLET.", 'Family':"The OAK family home."},
'ApocPalletLab':{'Blue':"BLUE: I'm KANTO'S professor now.\\nMy grandfather has retired.\\pPALLET is still home.", 'Research':"Research notes and field records.\\nPALLET POKEMON LAB.", 'Computer':"The laboratory's research computer."}}
def bg(x,y,script):return dict(type='sign',x=x,y=y,elevation=0,player_facing_dir='BG_EVENT_PLAYER_FACING_ANY',script=script)
def actor(name,gfx,x,y,script):return dict(local_id='LOCALID_'+name,graphics_id=gfx,x=x,y=y,elevation=3,movement_type='MOVEMENT_TYPE_FACE_DOWN',movement_range_x=0,movement_range_y=0,trainer_type='TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id='0',script=script,flag='0')
for n,texts in TEXT.items():
 p=E/f'data/maps/{n}';j=json.loads((p/'map.json').read_text());scripts=n+'_MapScripts::\n    .byte 0\n'
 for key,text in texts.items():
  label=n+'_'+key
  scripts+=f'\n{label}::\n'
  if key in ('Oak','Blue'):scripts+=f'    lock\n    faceplayer\n    msgbox {label}_Text, MSGBOX_DEFAULT\n    release\n    end\n'
  else:scripts+=f'    msgbox {label}_Text, MSGBOX_SIGN\n    end\n'
  scripts+=f'\n{label}_Text:\n    .string "{text}$"\n'
 if n=='ApocPalletRedHouse1F':j['warp_events']=j['warp_events'][:3];j['bg_events']=[bg(6,1,n+'_TV'),bg(4,4,n+'_Home')]
 if n=='ApocPalletRedHouse2F':j['bg_events']=[bg(11,1,n+'_Room'),bg(6,5,n+'_NES'),bg(1,1,n+'_PC')]
 if n=='ApocPalletOakHouse':
  j['object_events']=[actor('OAK','OBJ_EVENT_GFX_PROF_OAK',8,6,n+'_Oak')];j['bg_events']=[bg(10,1,n+'_Family')]
 if n=='ApocPalletLab':
  j['object_events']=[actor('BLUE','OBJ_EVENT_GFX_BLUE',6,4,n+'_Blue')];j['bg_events']=[bg(6,1,n+'_Research'),bg(2,1,n+'_Computer')]
 (p/'scripts.inc').write_text(scripts);(p/'map.json').write_text(json.dumps(j,indent=2)+'\n')
# Extend the existing map-review harness without changing the production new-game start.
p=E/'src/apocrypha_map_proof.c';s=p.read_text();needle='MAP_CHERRYGROVE_REGIONAL_PREVIEW_30};';assert needle in s
s=s.replace(needle,'MAP_CHERRYGROVE_REGIONAL_PREVIEW_30, MAP_APOC_PALLET_TOWN, MAP_APOC_PALLET_RED_HOUSE_1F, MAP_APOC_PALLET_RED_HOUSE_2F, MAP_APOC_PALLET_OAK_HOUSE, MAP_APOC_PALLET_LAB};');p.write_text(s)

with (E/"data/event_scripts.s").open("a") as f:
 f.write("\n@ Pallet Town: fresh Apocrypha events, no FRLG campaign triggers.\n")
 for n in TEXT:f.write(f'.include "data/maps/{n}/scripts.inc"\n')
