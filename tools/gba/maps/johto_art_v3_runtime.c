// Camera-framed native captures and a short walk for the revised Johto art import.
#define main unused_map_qualification_main
#include "runtime.c"
#undef main
static void go(unsigned x,unsigned y){call("MapProof_Enter",(x<<8)|(y<<16));frames(360,0);}
int main(int argc,char**argv){
 if(argc!=4)return 2;
 FILE*f=fopen(argv[2],"r");if(!f)return 3;
 while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);
 c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;
 mCoreConfigInit(&c->config,"johto-art");c->setVideoBuffer(c,pixels,240);
 if(!mCoreLoadFile(c,argv[1]))return 5;
 c->rtc.override=RTC_FIXED;c->rtc.value=1789300800000LL;
 c->reset(c);frames(600,0);call("MapProof_Boot",0);frames(240,0);
 go(44,20);screenshot(argv[3],"johto-house");
 go(53,8);screenshot(argv[3],"johto-center");
 go(41,5);screenshot(argv[3],"johto-trees");
 go(30,11);screenshot(argv[3],"north-coast");
 go(28,24);screenshot(argv[3],"west-beach");
 go(45,29);screenshot(argv[3],"blossom-park");
 go(30,36);
 for(unsigned i=0;i<8;i++){frames(8,0);char tag[80];sprintf(tag,"water-%02u",i);screenshot(argv[3],tag);}
 go(52,10);
 for(unsigned i=0;i<40;i++){frames(4,i<20?16:32);char tag[80];sprintf(tag,"walk-%02u",i);screenshot(argv[3],tag);}
 c->deinit(c);return 0;
}
