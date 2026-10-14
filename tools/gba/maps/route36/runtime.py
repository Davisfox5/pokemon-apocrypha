"""Background Route 36 gate round trip and ordinary-input route traversal."""
from pathlib import Path
import sys,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent))
from johto_connections import runtime as r
OUT=ROOT/'gba/art/route36'
legs=json.loads((OUT/'evidence/walk-plan.json').read_text());walk=[]
for leg in legs:
 for key,x,y in leg['steps']:walk.append(f' step({key},1);at(44,{x},{y},"walk-{len(walk):03}");')
 walk.append('shot("'+leg['name']+'");')
prefix=r.MAIN[:r.MAIN.index('  // Actual east connection')]
r.MAIN=prefix+r'''
 go(43,7,30);shot("violet-west-approach");step(LEFT,3);frames(360,0);observe("violet-to-west-gate");need(state[2]==45,"violet-to-west-gate");shot("west-gate-interior");
 step(UP,1);step(LEFT,11);step(DOWN,2);frames(360,0);observe("gate-to-route36");need(state[2]==44,"gate-to-route36");shot("route36-arrival");
 go(44,74,20);
'''+ '\n'.join(walk)+r'''
 go(44,74,20);step(RIGHT,2);frames(360,0);observe("route36-to-gate");need(state[2]==45,"route36-to-gate");shot("route36-return-gate");
 step(UP,1);step(RIGHT,11);step(DOWN,2);frames(360,0);observe("gate-to-violet");need(state[2]==43,"gate-to-violet");shot("violet-return");
 go(44,13,23);step(RIGHT,2);at(44,15,23,"west-stairs-eastward");step(LEFT,2);at(44,13,23,"west-stairs-westward");
 go(44,31,23);step(RIGHT,2);at(44,33,23,"east-stairs-eastward");step(LEFT,2);at(44,31,23,"east-stairs-westward");
 go(44,13,20);step(RIGHT,1);at(44,13,20,"west-wall-blocks");
 go(44,33,20);step(LEFT,1);at(44,33,20,"east-wall-blocks");
 go(44,15,20);step(RIGHT,9);at(44,24,20,"grass-crossing");shot("grass-at-native-scale");
 go(44,19,1);step(UP,1);at(44,19,1,"route37-pending-edge");
 go(44,10,30);step(DOWN,1);at(44,10,30,"route35-pending-edge");
 go(44,7,14);step(LEFT,1);at(44,7,14,"park-interior-pending");
 read_sign(44,23,1,"route37-sign");read_sign(44,7,12,"park-sign");read_sign(44,70,17,"violet-sign");read_sign(44,55,20,"alph-sign");
 go(44,68,20);shot("save-at-route36");
 unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
 }
 c->deinit(c);return 0;
}
'''
r.MAIN=r.MAIN.replace('11,27,18','44,68,20').replace('cold-reload-new-bark','cold-reload-route36')
if __name__=='__main__':r.main()
