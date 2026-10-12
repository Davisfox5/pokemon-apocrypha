#define main unused_map_qualification_main
#include "runtime.c"
#undef main
int main(int argc,char**argv){
 if(argc!=5)return 2;FILE*f=fopen(argv[2],"r");if(!f)return 3;while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;mCoreConfigInit(&c->config,"collision-audit");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;c->rtc.override=RTC_FIXED;c->rtc.value=1789315200000LL;c->reset(c);frames(600,0);call("MapProof_Boot",0);frames(240,0);
 f=fopen(argv[3],"r");unsigned map,x,y,key,surf,expect,mid,count=0,fail=0;
 while(fscanf(f,"%u %u %u %u %u %u %u",&map,&x,&y,&key,&surf,&expect,&mid)==7){
  call("MapProof_Enter",map|(x<<8)|(y<<16));frames(360,0);if(surf){call("SetPlayerAvatarTransitionFlags",8);frames(30,0);}frames(24,key);frames(80,0);
  call("MapProof_ReadState",0);unsigned a=sym("gMapProofState");unsigned mx=c->busRead32(c,a+12),my=c->busRead32(c,a+16);int moved=mx!=x||my!=y;
  int ok=moved==expect;printf("{\"map\":%u,\"x\":%u,\"y\":%u,\"key\":%u,\"surf\":%u,\"target_metatile\":%u,\"expected_move\":%u,\"final_x\":%u,\"final_y\":%u,\"passed\":%s}\n",map,x,y,key,surf,mid,expect,mx,my,ok?"true":"false");fflush(stdout);
  if(!ok){char tag[80];sprintf(tag,"collision-failure-%u",count);screenshot(argv[4],tag);fail++;}count++;
 }
 fprintf(stderr,"Probes %u; failures %u\n",count,fail);fclose(f);c->deinit(c);return fail?6:0;
}
