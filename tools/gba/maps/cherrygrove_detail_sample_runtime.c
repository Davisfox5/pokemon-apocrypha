#define main unused_map_qualification_main
#include "runtime.c"
#undef main
static void go(unsigned x,unsigned y){call("MapProof_Enter",x<<8|y<<16);frames(300,0);}
int main(int argc,char**argv){
 if(argc!=4)return 2;FILE*f=fopen(argv[2],"r");while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 3;mCoreConfigInit(&c->config,"cherrygrove-detail-sample");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 4;
 c->rtc.override=RTC_FIXED;c->rtc.value=1790784000000LL;c->reset(c);frames(600,0);call("MapProof_Boot",0);frames(240,0);
 go(16,13);observe("sample-house");screenshot(argv[3],"sample-house");if(state[1]!=80||state[2]!=0||state[3]!=16||state[4]!=13)return 5;
 frames(24,64);frames(30,0);observe("house-blocked");if(state[4]!=13)return 6;
 frames(24,16);frames(30,0);observe("path-walking");if(state[3]<=16)return 7;screenshot(argv[3],"path-walking");
 go(14,9);observe("grass-and-trees");screenshot(argv[3],"grass-and-trees");
 go(16,13);unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);char save[2048];snprintf(save,sizeof(save),"%s/sample.sav",argv[3]);f=fopen(save,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 8;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
 c->deinit(c);return 0;
}
