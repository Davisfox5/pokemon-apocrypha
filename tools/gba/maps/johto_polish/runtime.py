#!/usr/bin/env python3
"""Native input, door, collision and ordinary cold-Continue checks for the HGSS revision."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from johto_connections import runtime as r
r.MAIN=r.MAIN[:r.MAIN.index('  // Actual east connection')]+r'''
  go(9,97,16);shot("route29-before-crossing");step(RIGHT,1);at(11,0,12,"route29-to-new-bark");shot("new-bark-seam");
  step(LEFT,1);at(9,97,16,"new-bark-to-route29");
  step(RIGHT,20);at(11,19,12,"new-bark-square");shot("new-bark-square");
  step(UP,4);frames(360,0);observe("institute-entry");need(state[2]==14,"institute-entry");shot("institute-interior");
  step(DOWN,2);frames(360,0);at(11,19,9,"institute-return");shot("institute-return");
  go(11,13,18);step(UP,1);frames(360,0);need(state[2]==15,"west-home-entry");step(DOWN,1);frames(360,0);at(11,13,18,"west-home-return");
  go(11,24,20);step(UP,1);frames(360,0);need(state[2]==18,"east-home-entry");step(DOWN,1);frames(360,0);at(11,24,20,"east-home-return");
  go(11,27,11);step(UP,1);frames(360,0);need(state[2]==19,"upper-home-entry");step(DOWN,1);frames(360,0);at(11,27,11,"upper-home-return");shot("upper-home-return");
  read_sign(11,15,8,"institute-sign");go(11,33,13);step(RIGHT,1);at(11,33,13,"eastern-water-blocks");shot("new-bark-east");
  go(10,10,0);step(UP,1);at(12,38,29,"route30-to-route31");shot("route31-seam");step(DOWN,1);at(10,10,0,"route31-to-route30");
  step(UP,12);at(12,38,18,"route31-east");shot("route31-east");
  step(UP,1);step(LEFT,5);at(12,33,17,"route31-bridge");shot("route31-bridge");
  step(LEFT,29);step(UP,2);frames(360,0);need(state[2]==16,"violet-gate-entry");shot("violet-gate-interior");
  step(UP,1);step(LEFT,11);step(DOWN,2);frames(360,0);need(state[2]==13,"violet-arrival");shot("violet-arrival");
  go(12,52,14);step(UP,1);frames(360,0);need(state[2]==17,"dark-cave-entry");shot("dark-cave-interior");
  step(DOWN,1);frames(360,0);step(DOWN,1);at(12,52,14,"dark-cave-return");shot("dark-cave-exterior");
  go(12,24,18);step(DOWN,1);at(12,24,20,"route31-ledge-jump");step(UP,1);at(12,24,20,"route31-ledge-blocks-uphill");
  read_sign(12,10,13,"route31-sign");read_sign(12,51,13,"cave-sign");
  go(11,19,14);shot("save-at-new-bark");
  unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
 }
 c->deinit(c);return 0;
}
'''
r.MAIN=r.MAIN.replace('11,27,18','11,19,14').replace('need(state[2]', 'observe("door-state");need(state[2]')
r.FILM=r.FILM.replace('go(11,10,17)', 'go(11,15,20)').replace('state[3]>10','state[3]>15')
if __name__=='__main__':r.main()
