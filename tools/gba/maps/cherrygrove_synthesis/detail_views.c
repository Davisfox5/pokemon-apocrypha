// Native screenshots of the revised edges, captured without a desktop emulator.
#define main unused_map_qualification_main
#include "../runtime.c"
#undef main
int main(int argc,char **argv){
 if(argc!=4)return 2;
 FILE*f=fopen(argv[2],"r");if(!f)return 3;
 while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;
 fclose(f);struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);
 c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;
 mCoreConfigInit(&c->config,"cherrygrove-detail");c->setVideoBuffer(c,pixels,240);
 if(!mCoreLoadFile(c,argv[1]))return 5;c->rtc.override=RTC_FIXED;c->rtc.value=1789315200000LL;
 c->reset(c);frames(600,0);call("MapProof_Boot",0);frames(240,0);
 const unsigned views[][2]={{68,8},{36,16},{66,26},{54,20}};
 const char*names[]={"detail-pond","detail-shore","detail-southeast","detail-gable"};
 for(unsigned i=0;i<4;i++){call("MapProof_Enter",(views[i][0]<<8)|(views[i][1]<<16));frames(360,0);screenshot(argv[3],names[i]);}
 c->deinit(c);return 0;
}
