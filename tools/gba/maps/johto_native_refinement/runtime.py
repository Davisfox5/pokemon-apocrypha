#!/usr/bin/env python3
"""Headless native refinement proof and gameplay-scale captures for every affected map."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from johto_connections import runtime as r
r.MAIN=r.MAIN[:r.MAIN.index('  // Actual east connection')]+r'''
  go(0,59,12);shot("cherrygrove-route29-seam");step(RIGHT,1);at(9,0,16,"cherrygrove-to-route29");step(LEFT,1);at(0,59,12,"route29-to-cherrygrove");
  go(0,32,0);shot("cherrygrove-route30-seam");step(UP,1);at(10,8,73,"cherrygrove-to-route30");step(DOWN,1);at(0,32,0,"route30-to-cherrygrove");
  go(9,17,13);step(DOWN,1);at(9,17,15,"route29-ledge-down");step(UP,1);at(9,17,15,"route29-ledge-blocks-uphill");
  go(9,97,16);shot("route29-before-crossing");step(RIGHT,1);at(11,0,12,"route29-to-new-bark");shot("new-bark-seam");step(LEFT,1);at(9,97,16,"new-bark-to-route29");
  go(9,24,16);shot("route29-native-grass");go(9,52,10);shot("route29-gate");
  go(10,26,8);shot("route30-mr-pokemon");go(10,11,54);shot("route30-berry-house");go(10,18,39);shot("route30-native-grass");go(10,18,43);shot("route30-inside-grass");step(RIGHT,4);at(10,22,43,"route30-grass-walk");shot("route30-grass-walk");go(10,10,30);shot("route30-stair-landing");
  go(11,16,7);shot("enlarged-institute");step(UP,1);frames(360,0);observe("institute-entry");need(state[2]==14,"institute-entry");shot("institute-interior");step(DOWN,2);frames(360,0);at(11,16,7,"institute-return");
  go(11,12,18);step(UP,1);frames(360,0);observe("west-home-entry");need(state[2]==15,"west-home-entry");step(DOWN,1);frames(360,0);at(11,12,18,"west-home-return");
  go(11,23,20);step(UP,1);frames(360,0);observe("east-home-entry");need(state[2]==18,"east-home-entry");step(DOWN,1);frames(360,0);at(11,23,20,"east-home-return");
  go(11,28,9);step(UP,1);frames(360,0);observe("upper-home-entry");need(state[2]==19,"upper-home-entry");step(DOWN,1);frames(360,0);at(11,28,9,"upper-home-return");
  int dx[]={10,25,10,25},dy[]={30,30,39,39};
  for(int i=0;i<4;i++){char label[64];go(11,dx[i],dy[i]+1);sprintf(label,"southern-home-%d",i+1);shot(label);step(UP,1);frames(360,0);observe(label);need(state[2]==20+i,label);step(DOWN,1);frames(360,0);sprintf(label,"southern-home-return-%d",i+1);at(11,dx[i],dy[i]+1,label);}
  go(11,16,22);step(DOWN,18);at(11,16,40,"southern-central-street");shot("southern-housing-street");step(LEFT,6);at(11,10,40,"southern-door-approach");
  go(11,33,13);step(RIGHT,1);at(11,33,13,"eastern-water-blocks");shot("new-bark-east");
  go(10,10,0);step(UP,1);at(12,38,29,"route30-to-route31");shot("route31-seam");step(DOWN,1);at(10,10,0,"route31-to-route30");
  step(UP,12);at(12,38,18,"route31-east");shot("route31-east");step(UP,1);step(LEFT,5);at(12,33,17,"route31-bridge");shot("route31-bridge");
  step(LEFT,29);step(UP,2);frames(360,0);observe("violet-gate-entry");need(state[2]==16,"violet-gate-entry");shot("violet-gate-interior");step(UP,1);step(LEFT,11);step(DOWN,2);frames(360,0);observe("violet-arrival");need(state[2]==13,"violet-arrival");shot("violet-arrival");
  go(12,52,14);step(UP,1);frames(360,0);observe("dark-cave-entry");need(state[2]==17,"dark-cave-entry");step(DOWN,1);frames(360,0);step(DOWN,1);at(12,52,14,"dark-cave-return");shot("dark-cave-exterior");
  go(12,24,18);step(DOWN,1);at(12,24,20,"route31-ledge-jump");step(UP,1);at(12,24,20,"route31-ledge-blocks-uphill");
  go(11,16,40);shot("save-at-new-bark");
  unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
 }
 c->deinit(c);return 0;
}
'''
r.MAIN=r.MAIN.replace('11,27,18','11,16,40')
r.FILM=r.FILM.replace('go(11,10,17)','go(11,16,28)').replace('frames(1,RIGHT)','frames(1,DOWN)').replace('state[3]>10','state[4]>28')
if __name__=='__main__':r.main()
