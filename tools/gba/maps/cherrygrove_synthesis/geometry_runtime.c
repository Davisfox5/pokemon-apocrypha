// Approach each physical wall through ordinary movement and capture roof overlap.
#define main unused_map_qualification_main
#include "../runtime.c"
#undef main
int main(int argc,char **argv){
 if(argc!=5)return 2;FILE*f=fopen(argv[2],"r");if(!f)return 3;
 while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;mCoreConfigInit(&c->config,"building-geometry");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 c->rtc.override=RTC_FIXED;c->rtc.value=1789315200000LL;c->reset(c);frames(600,0);call("MapProof_Boot",0);frames(240,0);
 f=fopen(argv[3],"r");char tag[100];unsigned x,y,key,xx,yy,count=0,fail=0;
 while(fscanf(f,"%99s %u %u %u %u %u",tag,&x,&y,&key,&xx,&yy)==6){
  call("MapProof_Enter",(x<<8)|(y<<16));frames(360,0);frames(64,key);frames(60,0);
  call("MapProof_ReadState",0);unsigned a=sym("gMapProofState");for(int i=0;i<10;i++)state[i]=c->busRead32(c,a+4*i);
  int ok=state[1]==80&&state[2]==0&&state[3]==xx&&state[4]==yy;
  printf("{\"case\":\"%s\",\"x\":%u,\"y\":%u,\"expected_x\":%u,\"expected_y\":%u,\"passed\":%s}\n",tag,state[3],state[4],xx,yy,ok?"true":"false");fflush(stdout);screenshot(argv[4],tag);if(!ok)fail++;count++;
 }
 fprintf(stderr,"Building wall approaches %u; failures %u\n",count,fail);fclose(f);c->deinit(c);return fail?6:0;
}
