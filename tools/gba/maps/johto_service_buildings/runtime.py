"""Background checks of approved shared service buildings and their entrances."""
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent))
from johto_connections import runtime as r
r.MAIN=r.MAIN[:r.MAIN.index('  // Actual east connection')]+r'''
 go(0,56,10);shot("cherrygrove-service-street");
 go(0,51,10);shot("mart-front");
 for(int i=0;i<90;i++){frames(1,i<28?UP:0);if(i%3==0){char tag[60];sprintf(tag,"mart-door-%03d",i);shot(tag);}}
 frames(360,0);observe("mart-entry");need(state[2]==5,"mart-entry");shot("mart-interior");
 step(DOWN,1);frames(360,0);at(0,51,10,"mart-return");shot("mart-return");
 go(0,61,10);shot("center-front");
 for(int i=0;i<90;i++){frames(1,i<28?UP:0);if(i%3==0){char tag[60];sprintf(tag,"center-door-%03d",i);shot(tag);}}
 frames(360,0);observe("center-entry");need(state[2]==6,"center-entry");shot("center-interior");
 step(DOWN,1);frames(360,0);at(0,61,10,"center-return");shot("center-return");
 go(0,60,10);step(UP,1);at(0,60,10,"center-front-wall");
 go(0,58,7);step(RIGHT,1);at(0,58,7,"center-west-wall");shot("center-side");
 go(0,61,4);step(DOWN,1);at(0,61,5,"center-roof-overlap");shot("center-roof-overlap");step(DOWN,1);at(0,61,5,"center-rear-wall");
 go(0,50,10);step(UP,1);at(0,50,10,"mart-front-wall");
 go(0,48,7);step(RIGHT,1);at(0,48,7,"mart-west-wall");
 go(0,54,11);step(UP,1);at(0,54,10,"old-mart-sign-ground-clear");shot("old-sign-cleared");
 go(0,54,20);step(UP,1);frames(360,0);observe("existing-house-entry");need(state[2]==2,"existing-house-entry");shot("existing-house-interior");
 step(DOWN,1);frames(360,0);at(0,54,20,"existing-house-return");
 go(0,65,8);shot("pond-animation-0");frames(20,0);shot("pond-animation-1");
 go(43,49,56);shot("violet-center-front");step(UP,1);at(43,49,56,"violet-center-still-closed");
 go(43,46,53);step(RIGHT,1);at(43,46,53,"violet-center-wall");
 go(43,49,50);step(DOWN,1);at(43,49,51,"violet-center-roof-overlap");shot("violet-center-roof-overlap");step(DOWN,1);at(43,49,51,"violet-center-rear-wall");
 go(43,21,41);step(UP,1);at(43,21,41,"violet-mart-still-closed");shot("violet-mart-preserved");
 go(0,56,10);shot("save-at-cherrygrove");
 unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
 }
 c->deinit(c);return 0;
}
'''
r.MAIN=r.MAIN.replace('11,27,18','0,56,10').replace('cold-reload-new-bark','cold-reload-cherrygrove')
if __name__=='__main__':r.main()
