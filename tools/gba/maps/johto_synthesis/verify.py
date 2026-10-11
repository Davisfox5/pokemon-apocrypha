"""Fresh headless emulator proof; never opens a desktop emulator or owner save."""
from pathlib import Path
import sys,os
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent))
from johto_connections import runtime as r
r.MAIN=r.MAIN[:r.MAIN.index('  // Actual east connection')]+r'''
  go(0,79,18);shot("town-east");step(RIGHT,1);at(9,0,18,"town-to-route29");shot("route29-entry");step(LEFT,1);at(0,79,18,"route29-to-town");
  go(0,43,0);shot("town-north");step(UP,1);at(10,8,85,"town-to-route30");shot("route30-entry");step(UP,11);at(10,8,74,"route30-entrance-corridor");go(10,8,85);step(DOWN,1);at(0,43,0,"route30-to-town");
  go(9,17,15);step(DOWN,1);at(9,17,17,"route29-ledge-down");step(UP,1);at(9,17,17,"route29-ledge-blocks-uphill");
  go(9,24,18);shot("route29-grass");step(RIGHT,3);at(9,27,18,"route29-grass-walk");
  go(9,52,12);step(UP,1);at(9,52,12,"route46-gate-closed");shot("route29-gate");
  go(9,58,28);step(DOWN,1);at(9,58,28,"lookout-railing");shot("route29-lookout");
  go(9,97,18);shot("route29-east");step(RIGHT,1);at(28,0,12,"route29-to-new-bark");shot("new-bark-entry");step(LEFT,1);at(9,97,18,"new-bark-to-route29");
  go(10,26,8);shot("route30-mr-pokemon");go(10,11,54);shot("route30-house");go(10,18,43);shot("route30-grass");step(RIGHT,4);at(10,22,43,"route30-grass-walk");
  go(10,10,30);shot("route30-stairs");step(UP,3);at(10,10,27,"route30-stairs-climb");go(10,20,52);step(RIGHT,1);at(10,20,52,"route30-pond-blocks");shot("route30-pond");
  go(10,8,64);shot("route30-lower-stairs-west");step(UP,2);at(10,8,62,"lower-west-stairs");
  go(10,18,64);shot("route30-lower-stairs-east");step(UP,2);at(10,18,62,"lower-east-stairs");
  go(10,14,6);step(RIGHT,2);at(10,16,6,"mr-pokemon-cliff-bridge");shot("route30-plateau-bridge");
  go(10,16,20);step(LEFT,1);at(10,16,20,"plateau-divider-blocks");
  go(28,19,17);step(RIGHT,1);at(28,19,17,"windmill-grass-base-blocks");shot("new-bark-windmills");
  go(28,18,16);step(DOWN,2);at(28,18,18,"windmill-cleared-from-street");
  go(28,16,7);shot("new-bark-lab");step(UP,1);frames(360,0);observe("lab-entry");need(state[2]==31,"lab-entry");shot("lab-interior");step(DOWN,2);frames(360,0);at(28,16,7,"lab-return");
  int hx[]={12,23,28,10,25,10,25},hy[]={17,19,8,30,30,39,39},hm[]={32,35,36,37,38,39,40};
  for(int i=0;i<7;i++){char tag[64];go(28,hx[i],hy[i]+1);sprintf(tag,"new-bark-house-%d",i+1);shot(tag);step(UP,1);frames(360,0);observe(tag);need(state[2]==hm[i],tag);step(DOWN,1);frames(360,0);sprintf(tag,"home-return-%d",i+1);at(28,hx[i],hy[i]+1,tag);}
  go(28,16,22);step(DOWN,18);at(28,16,40,"southern-main-street");shot("new-bark-housing");step(LEFT,6);at(28,10,40,"southern-door-approach");
  go(28,33,13);step(RIGHT,1);at(28,33,13,"new-bark-water-blocks");shot("new-bark-shore");
  go(28,13,12);step(DOWN,1);at(28,13,13,"house-rear-overhang");shot("new-bark-rear-overhang");step(DOWN,1);at(28,13,13,"house-wall-blocks");
  go(10,10,0);shot("route30-top");step(UP,1);at(29,38,29,"route30-to-route31");shot("route31-entry");step(DOWN,1);at(10,10,0,"route31-to-route30");
  step(UP,13);at(29,38,17,"route31-junction");step(LEFT,5);at(29,33,17,"route31-bridge");shot("route31-bridge");
  step(LEFT,29);step(UP,2);frames(360,0);observe("violet-gate-entry");need(state[2]==33,"violet-gate-entry");shot("violet-gate-interior");step(UP,1);step(LEFT,11);step(DOWN,2);frames(360,0);observe("violet-arrival");need(state[2]==30,"violet-arrival");shot("violet-arrival");
  go(29,52,14);shot("route31-cave");step(UP,1);frames(360,0);observe("dark-cave-entry");need(state[2]==34,"dark-cave-entry");step(DOWN,1);frames(360,0);step(DOWN,1);at(29,52,14,"dark-cave-return");
  go(29,24,18);shot("route31-grass");step(DOWN,1);at(29,24,20,"route31-ledge-jump");step(UP,1);at(29,24,20,"route31-ledge-blocks-uphill");
  // Sustained ordinary walking exercises grass effects without test teleports.
  go(9,18,18);for(int i=0;i<100;i++){step(RIGHT,6);at(9,24,18,"grass-walk-right");step(LEFT,6);at(9,18,18,"grass-walk-left");}shot("grass-walk-stress-end");
  // Seven approved town doors still use their unchanged warp IDs and artwork.
  int tx[]={43,54,64,51,61,52,65},ty[]={17,19,24,9,9,31,31},tm[]={1,2,3,5,6,11,12};
  for(int i=0;i<7;i++){char tag[64];go(0,tx[i],ty[i]+1);step(UP,1);frames(360,0);sprintf(tag,"town-door-%d",i);observe(tag);need(state[2]==tm[i],tag);}
  go(28,16,40);shot("save-at-new-bark");
  unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
 }
 c->deinit(c);return 0;
}
'''
r.MAIN=r.MAIN.replace('11,27,18','28,16,40')
os.environ.setdefault('MGBA_FLAGS','-I/opt/homebrew/include -L/opt/homebrew/lib -lmgba')
if __name__=='__main__':r.main()
