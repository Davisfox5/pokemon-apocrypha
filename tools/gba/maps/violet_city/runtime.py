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
 read_sign(43,53,43,"university-sign");read_sign(43,35,14,"tower-sign");read_sign(43,68,43,"library-sign");read_sign(43,27,42,"lecture-sign");read_sign(43,70,59,"city-sign");read_sign(43,54,47,"practice-sign");
 go(43,57,42);step(UP,1);at(43,57,42,"university-door-closed");shot("university-entrance");
 go(43,61,52);shot("teaching-court");step(UP,3);at(43,61,49,"court-walk");
 go(43,56,53);step(DOWN,1);at(43,56,53,"court-bench-blocks");shot("court-benches");
 go(43,11,28);step(UP,1);at(43,11,28,"northwest-house-closed");
 go(43,26,57);step(UP,1);at(43,26,57,"west-garden-house-closed");
 go(43,56,69);step(UP,1);at(43,56,69,"south-garden-house-closed");
 go(43,39,13);shot("save-at-violet");
 unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
 }
 c->deinit(c);return 0;
}
'''
r.MAIN=r.MAIN.replace('11,27,18','43,39,13').replace('cold-reload-new-bark','cold-reload-violet')
if __name__=='__main__':r.main()
