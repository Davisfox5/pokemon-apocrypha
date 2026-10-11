// Exact entry/return coordinates and facing, driven by the reviewed map events.
#define main unused_map_qualification_main
#include "../runtime.c"
#undef main
int main(int argc,char **argv){
 if(argc!=5)return 2;FILE*f=fopen(argv[2],"r");if(!f)return 3;
 while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;mCoreConfigInit(&c->config,"access-audit");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 c->rtc.override=RTC_FIXED;c->rtc.value=1789315200000LL;c->reset(c);frames(600,0);call("MapProof_Boot",0);frames(240,0);
 f=fopen(argv[3],"r");char tag[100];unsigned map,x,y,key,dest,xx,yy,facing,count=0,fail=0;
 while(fscanf(f,"%99s %u %u %u %u %u %u %u %u",tag,&map,&x,&y,&key,&dest,&xx,&yy,&facing)==9){
  call("MapProof_Enter",map|(x<<8)|(y<<16));frames(360,0);
  // One step crosses connection seams; door and staircase animations need the
  // longer press to initiate their normal field transition.
  if(!strncmp(tag,"seam-",5)){
   unsigned desired=key==128?1:key==64?2:key==32?3:4;
   // Turning in place consumes the first input. Finish it before taking exactly
   // one seam-crossing step, instead of mistaking a turn for blocked movement.
   if(call("GetPlayerFacingDirection",0)!=desired){frames(8,key);frames(16,0);}
   frames(8,key);
  }else frames(!strncmp(tag,"preview-",8)?40:20,key);frames(240,0);
  call("MapProof_ReadState",0);unsigned a=sym("gMapProofState");for(int i=0;i<10;i++)state[i]=c->busRead32(c,a+4*i);
  unsigned dir=call("GetPlayerFacingDirection",0);int ok=state[1]==80&&state[2]==dest&&state[3]==xx&&state[4]==yy&&(!facing||dir==facing)&&!call("ArePlayerFieldControlsLocked",0);
  printf("{\"case\":\"%s\",\"map\":%u,\"x\":%u,\"y\":%u,\"facing\":%u,\"expected_map\":%u,\"expected_x\":%u,\"expected_y\":%u,\"expected_facing\":%u,\"passed\":%s}\n",tag,state[2],state[3],state[4],dir,dest,xx,yy,facing,ok?"true":"false");fflush(stdout);
  if(!ok||!strncmp(tag,"door-",5)||!strncmp(tag,"center-",7))screenshot(argv[4],tag);
  if(!ok)fail++;count++;
 }
 fprintf(stderr,"Travel cases %u; failures %u\n",count,fail);fclose(f);c->deinit(c);return fail?6:0;
}
