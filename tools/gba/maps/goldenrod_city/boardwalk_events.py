"""Read-only attraction/counter inscriptions, no inventory or persistent flags."""
from pathlib import Path
import json,subprocess
BASE='fdaf387b1ef1b0704e4f6a2f4ac0c24444d900a7'
EVENTS={
 'GoldenrodCity02':[(3,10,'Snacks',r'Boardwalk refreshments.\nColorful bottles line the shelf.'),(6,13,'Prizes',r'Bright prize balls are neatly\nlined up under the awning.'),(14,12,'Souvenirs',r'Miniature towers and trinkets\nfill the souvenir counter.'),(9,11,'Wheel',r'GOLDENROD WHEEL\nThe harbor spreads below.')],
 'GoldenrodCity04':[(0,2,'Broadcast',r'Goldenrod Radio Tower\nBroadcasting across Johto.')],
 'GoldenrodCity06':[(11,12,'Terminal',r'MAGNET TRAIN\nTicket and departure terminal.')]
}
def apply(G):
 assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()==BASE,'Preserve current native source; use the immutable baseline.'
 for name,events in EVENTS.items():
  folder=G/'data/maps'/name;path='data/maps/'+name+'/map.json'
  for leaf in ['map.json','scripts.inc']:
   pth='data/maps/'+name+'/'+leaf;original=subprocess.check_output(['git','-C',str(G),'show',BASE+':'+pth]);assert (G/pth).read_bytes()==original,('Preserve edited native events',pth)
  data=json.loads(subprocess.check_output(['git','-C',str(G),'show',BASE+':'+path]));script=f'{name}_MapScripts::\n    .byte 0\n'
  for x,y,key,msg in events:
   label=name+'_Boardwalk_'+key;data['bg_events'].append(dict(type='sign',x=x,y=y,elevation=0,player_facing_dir='BG_EVENT_PLAYER_FACING_NORTH',script=label));script+='\n'+label+'::\n    msgbox '+label+'_Text, MSGBOX_SIGN\n    end\n\n'+label+'_Text:\n    .string "'+msg+'$"\n'
  (folder/'map.json').write_text(json.dumps(data,indent=2)+'\n');(folder/'scripts.inc').write_text(script)
if __name__=='__main__':
 import sys
 apply(Path(sys.argv[1]))
