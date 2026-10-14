"""Headless ordinary-input traversal of Violet, including both gate directions."""
import sys,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent))
from johto_connections import runtime as r
OUT=ROOT/'gba/art/violet-city'
legs=json.loads((OUT/'evidence/walk-plan.json').read_text());walk=[]
for leg in legs:
 for i,(key,x,y) in enumerate(leg['steps']):walk.append(f' step({key},1);at(43,{x},{y},"walk-{len(walk):03}");')
 walk.append('shot("'+leg['name'].lower().replace(' ','-')+'");')
r.MAIN=r.MAIN[:r.MAIN.index('  // Actual east connection')]+r'''
 go(33,1,4);step(DOWN,2);frames(360,0);at(43,74,57,"gate-to-violet");shot("east-arrival");
 step(UP,1);frames(360,0);observe("violet-to-gate");need(state[2]==33,"violet-to-gate");shot("gate-return");
 go(43,74,57);
'''+ '\n'.join(walk)+r'''
 go(43,39,13);step(UP,1);at(43,39,13,"tower-door-closed");shot("tower-approach");
 go(43,38,20);step(LEFT,1);at(43,38,20,"bridge-rail-blocks");shot("bridge-rail");
 go(43,33,24);shot("stone-landing");
 go(43,23,20);shot("lake-bank");
 go(43,31,26);step(LEFT,1);at(43,31,26,"island-water-blocks");
 go(43,49,56);step(UP,1);at(43,49,56,"center-closed");shot("center-entrance");
 go(43,68,44);step(UP,1);at(43,68,44,"library-sign-blocks");
 read_sign(43,53,43,"university-sign");read_sign(43,35,14,"tower-sign");read_sign(43,68,43,"library-sign");read_sign(43,26,42,"lecture-sign");read_sign(43,70,59,"city-sign");read_sign(43,54,47,"practice-sign");
 go(43,31,42);step(UP,1);at(43,31,42,"lecture-door-closed");shot("lecture-hall-front");
 go(43,28,42);step(UP,1);at(43,28,42,"lecture-front-wall-blocks");
 go(43,36,39);step(LEFT,1);at(43,36,39,"lecture-side-wall-blocks");
 go(43,57,42);step(UP,1);at(43,57,42,"university-door-closed");shot("university-entrance");
 go(43,46,39);step(RIGHT,1);at(43,46,39,"university-west-wall-blocks");shot("university-west-edge");
 go(43,67,39);step(LEFT,1);at(43,67,39,"university-east-wall-blocks");shot("university-east-edge");
 go(43,48,35);step(DOWN,1);at(43,48,35,"university-rear-wall-blocks");shot("university-roof-overlap");
 go(43,54,34);shot("clock-tower-upper");
 go(43,36,38);shot("lecture-upper-story");
 go(43,21,41);step(UP,1);at(43,21,41,"mart-door-closed");shot("mart-entrance");
 go(43,26,39);step(LEFT,1);at(43,26,39,"mart-east-wall-blocks");shot("mart-east-wall");
 go(43,24,42);step(UP,1);at(43,24,41,"mart-old-sign-space-clear");step(UP,1);at(43,24,41,"mart-showroom-wall-blocks");shot("mart-showroom");
 go(43,61,52);shot("teaching-court");step(UP,3);at(43,61,49,"court-walk");
 go(43,56,53);step(DOWN,1);at(43,56,53,"court-bench-blocks");shot("court-benches");
 go(43,11,28);step(UP,1);at(43,11,28,"northwest-house-closed");
 go(43,26,57);step(UP,1);at(43,26,57,"west-garden-house-closed");
 go(43,56,65);step(UP,1);at(43,56,65,"south-garden-house-closed");
 go(43,7,30);step(LEFT,3);frames(360,0);observe("west-gate-interior");need(state[2]==45,"west-gate-interior");shot("route36-gate");go(43,7,30);
 go(43,23,70);step(DOWN,1);at(43,23,71,"route32-city-boundary");step(DOWN,1);at(43,23,71,"route32-unbuilt-destination-blocks");shot("route32-exit");
 go(43,37,26);step(UP,1);at(43,37,26,"landing-finial-blocks");shot("bridge-finials");
 go(43,44,25);shot("lake-island-and-pads");
 read_sign(43,9,32,"route36-sign");read_sign(43,25,67,"route32-sign");
 go(43,39,13);shot("save-at-violet");
 unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
 }
 c->deinit(c);return 0;
}
'''
r.MAIN=r.MAIN.replace('11,27,18','43,39,13').replace('cold-reload-new-bark','cold-reload-violet')
if __name__=='__main__':r.main()
