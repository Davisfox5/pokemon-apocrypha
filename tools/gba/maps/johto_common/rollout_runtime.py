"""Background shared-art rollout checks, including real gate entry/return."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_service_buildings import runtime as prior
r=prior.r
r.MAIN=r.MAIN.replace(' go(0,56,10);shot("save-at-cherrygrove");',r'''
 go(29,4,16);shot("route31-shared-gate-front");step(UP,1);frames(360,0);observe("route31-gate-entry");need(state[2]==33,"route31-gate-entry");shot("route31-gate-interior");
 step(DOWN,1);frames(360,0);at(29,4,16,"route31-gate-return");shot("route31-gate-return");
 go(9,52,12);shot("route29-shared-gate");step(UP,1);observe("route29-closed-gate");need(state[2]==9,"route29-still-closed");
 go(28,10,7);shot("new-bark-mailbox");go(28,20,18);shot("new-bark-green-trees");
 go(9,17,15);step(DOWN,1);at(9,17,17,"route29-shared-ledge-jump");step(UP,1);at(9,17,17,"route29-ledge-blocks-uphill");shot("route29-ledge");
 go(10,9,3);step(DOWN,1);at(10,9,5,"route30-native-ledge-jump");step(UP,1);at(10,9,5,"route30-ledge-blocks-uphill");shot("route30-ledge");
 go(29,7,17);step(DOWN,1);at(29,7,19,"route31-native-ledge-jump");step(UP,1);at(29,7,19,"route31-ledge-blocks-uphill");shot("route31-ledge");
 go(9,21,15);shot("route29-apricorn");go(9,30,17);shot("route29-grass");
 go(10,20,7);shot("route30-pink-apricorn");go(10,12,54);shot("route30-green-apricorn");
 go(29,21,16);shot("route31-apricorn");go(29,15,21);shot("route31-grass");
 go(43,38,22);shot("violet-bridge-rails");go(43,12,61);shot("violet-forest-ground");
 go(0,66,12);shot("cherrygrove-fence");go(0,44,31);shot("cherrygrove-pink-trees");
 go(0,56,10);shot("save-at-cherrygrove");
''')
if __name__=='__main__':r.main()
