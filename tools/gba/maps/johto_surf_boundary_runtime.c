#define main unused_map_qualification_main
#include "runtime.c"
#undef main
int main(int argc,char **argv){
 if(argc!=4)return 2;FILE*f=fopen(argv[2],"r");if(!f)return 3;while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;mCoreConfigInit(&c->config,"surf-boundaries");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;c->rtc.override=RTC_FIXED;c->rtc.value=1789315200000LL;c->reset(c);frames(600,0);call("MapProof_Boot",0);frames(240,0);
 unsigned tested=0,movementChecks=0;
 for(unsigned edge=0;edge<2;edge++)for(unsigned n=edge?9:10;n<=(edge?37:40);n++){
  if(!edge&&n>=23&&n<=25)continue;
  unsigned x=edge?n:9,y=edge?40:n;
  call("MapProof_Enter",(x<<8)|(y<<16));frames(360,0);call("SetPlayerAvatarTransitionFlags",8);frames(30,0);
  // Establish actual surf movement away from and then into the barrier.
  frames(16,edge?64:16);frames(12,0);call("MapProof_ReadState",0);unsigned a=sym("gMapProofState");unsigned moved=c->busRead32(c,a+(edge?4:3)*4);
  if(moved!=(edge?y:x))movementChecks++;
  frames(96,edge?128:32);frames(20,0);char tag[80];sprintf(tag,"surf-%s-%u",edge?"south":"west",n);observe(tag);
  if(state[1]!=80||state[2]!=0||(!edge&&state[3]<9)||(edge&&state[4]>40))return 7;
  if(n==10||n==20||n==30||n==37)screenshot(argv[3],tag);tested++;
 }
 if(!movementChecks)return 6;printf("{\"surf_barrier_probes\":%u,\"open_water_movement_checks\":%u,\"passed\":true}\n",tested,movementChecks);c->deinit(c);return 0;
}
