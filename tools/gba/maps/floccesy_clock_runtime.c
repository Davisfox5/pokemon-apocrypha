#define main unused_qualification_main
#include "runtime.c"
#undef main
static const char *out;
static unsigned shots;
static void snap(const char *tag){screenshot(out,tag);}
static void walk(unsigned key,unsigned x,unsigned y,const char *tag){
 unsigned ok=0;
 for(unsigned f=0;f<240;f++){
  frames(1,key);
  if(f%4==0){char name[80];sprintf(name,"walk-%03u",shots++);snap(name);}
  call("MapProof_ReadState",0);unsigned a=sym("gMapProofState");
  if(c->busRead32(c,a+12)==x&&c->busRead32(c,a+16)==y){ok=1;break;}
 }
 frames(16,0);observe(tag);if(!ok||state[3]!=x||state[4]!=y)exit(41);
}
static void blocked(unsigned key,unsigned x,unsigned y,const char *tag){frames(24,key);frames(24,0);observe(tag);if(state[3]!=x||state[4]!=y)exit(42);}
int main(int argc,char **argv){
 if(argc!=5)return 2;out=argv[3];FILE *f=fopen(argv[2],"r");if(!f)return 3;
 while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;
 mCoreConfigInit(&c->config,"floccesy-clock-proof");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 char flash[2048];snprintf(flash,sizeof(flash),"%s/clock.sav",out);
 if(strcmp(argv[4],"write")){unsigned char data[131072];f=fopen(flash,"rb");if(!f||fread(data,1,sizeof(data),f)!=sizeof(data))return 6;fclose(f);if(!c->savedataRestore(c,data,sizeof(data),false))return 7;}
 c->rtc.override=RTC_FIXED;c->rtc.value=1789315200000LL;c->reset(c);frames(600,0);
 if(!strcmp(argv[4],"menu")){
  frames(1,8);frames(180,0);frames(1,1);frames(300,0);frames(1,1);frames(180,0);frames(1,1);frames(300,0);observe("clock-title-continue");snap("clock-continue");if(state[3]!=17||state[4]!=48)return 10;
 }else if(!strcmp(argv[4],"read")){
  if(call("LoadGameSave",0)!=1)return 8;call("MapProof_Resume",0);frames(240,0);observe("clock-cold-reload");snap("clock-reload");if(state[3]!=17||state[4]!=48)return 9;
 }else{
  call("MapProof_Boot",0);frames(240,0);call("MapProof_Enter",20|(17<<8)|(48<<16));frames(360,0);snap("clock");observe("clock-start");
  walk(128,17,51,"south-through-garden");walk(32,16,51,"west-to-wall");blocked(32,16,51,"west-wall-blocks");blocked(128,16,51,"south-wall-blocks");
  walk(16,20,51,"garden-exit-approach");walk(128,20,53,"garden-steps");walk(16,22,53,"clock-frontage");walk(128,22,54,"steps-to-street");walk(16,30,54,"street-crossing");walk(64,30,48,"north-on-street");snap("street");
  call("MapProof_Enter",20|(22<<8)|(53<<16));frames(360,0);frames(1,16);frames(20,0);
  for(unsigned i=0;i<120&&!call("ArePlayerFieldControlsLocked",0);i++){frames(1,1);frames(16,0);}
  if(!call("ArePlayerFieldControlsLocked",0)){snap("dialogue-failed");observe("dialogue-failed");return 12;}frames(90,0);snap("npc-dialogue");observe("npc-dialogue");
  for(unsigned i=0;i<40&&call("ArePlayerFieldControlsLocked",0);i++){frames(1,2);frames(40,0);}
  if(call("ArePlayerFieldControlsLocked",0))return 13;observe("dialogue-return-to-field");
  call("MapProof_Enter",20|(17<<8)|(48<<16));frames(360,0);unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);
 }
 c->deinit(c);return 0;
}
