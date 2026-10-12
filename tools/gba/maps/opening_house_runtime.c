// Ordinary button input through the opening; mGBA core has no desktop window.
#define main unused_map_qualification_main
#include "runtime.c"
#undef main
static void tap(unsigned key){frames(1,key);frames(50,0);}
static const char *romPath,*outPath;
static void boot_core(void){c=mCoreFind(romPath);if(!c||!c->init(c))exit(3);mCoreConfigInit(&c->config,"apoc-opening");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,romPath))exit(4);}
static void close_text(void){for(int i=0;i<40 && call("ArePlayerFieldControlsLocked",0);i++)tap(2);if(call("ArePlayerFieldControlsLocked",0))exit(41);}
static void require(unsigned stage,unsigned map){observe("assert-stage");if(call("VarGet",0x40F7)!=stage||state[1]!=80||state[2]!=map)exit(42);}
static void save_continue(unsigned stage,unsigned map,const char *tag){
 // Save through the ordinary Start menu, then reload the serialized flash in
 // an entirely new emulator core and choose Continue with ordinary buttons.
 tap(8);tap(128);if(stage==4)tap(128);tap(1);
 for(int i=0;i<20;i++)tap(1);close_text();
 void*data=NULL;size_t size=c->savedataClone(c,&data);if(size!=131072)exit(43);
 char path[2048];snprintf(path,sizeof(path),"%s/%s.sav",outPath,tag);FILE*f=fopen(path,"wb");if(!f||fwrite(data,1,size,f)!=size)exit(44);fclose(f);
 c->deinit(c);boot_core();if(!c->savedataRestore(c,data,size,false))exit(45);free(data);c->reset(c);frames(600,0);
 for(int i=0;i<100;i++){tap(1);if((c->busRead32(c,sym("gMain")+4)&~1u)==sym("CB2_Overworld") && call("VarGet",0x40F7)==stage && !call("ArePlayerFieldControlsLocked",0))break;}
 require(stage,map);screenshot(outPath,tag);
}
int main(int argc,char **argv){
 if(argc!=4 && argc!=5)return 2;
 romPath=argv[1];outPath=argv[3];
 FILE*f=fopen(argv[2],"r");while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);
 boot_core();c->reset(c);frames(600,0);
 screenshot(argv[3],"00-boot");tap(1);frames(180,0);screenshot(argv[3],"01-menu");
 tap(1);frames(240,0);screenshot(argv[3],"02-appearance");
 tap(1);frames(180,0);screenshot(argv[3],"03-cold-open");
 unsigned chose=0;
 for(int i=0;i<100;i++){
  if(!chose && call("FindTaskIdByFunc",sym("Task_NewGameBirchSpeech_ChooseGender")|1)!=255){
   if(argc==5){tap(128);frames(180,0);}
   screenshot(argv[3],"appearance-choice");chose=1;
  }
  tap(1);char tag[64];sprintf(tag,"opening-%02d",i);screenshot(argv[3],tag);if(call("VarGet",0x40F7)==1 && !call("ArePlayerFieldControlsLocked",0))break;
 }
 screenshot(argv[3],"04-home-ready");
 observe("welcome-finished");
 printf("home_stage=%u gear=%u potion=%u\n",call("VarGet",0x40F7),call("FlagGet",0x20),call("FlagGet",0x21));
 require(1,1);save_continue(1,1,"continue-before-pc");

 // Walk around furniture to test the guarded doorway.
 frames(32,32);frames(48,128);frames(50,0);
 observe("exit-blocked");screenshot(argv[3],"05-exit-guard");
 for(int i=0;i<12 && call("ArePlayerFieldControlsLocked",0);i++)tap(2);
 observe("exit-guard-return");
 // Return via the clear eastern aisle and enter the stairs.
 frames(32,64);frames(16,32);frames(32,64);frames(180,0);
 observe("upstairs");screenshot(argv[3],"06-bedroom");
 // Approach the desk from its south side.
 frames(64,16);frames(20,0);frames(8,64);frames(20,0);tap(1);
 screenshot(argv[3],"07-pc-potion");
 for(int i=0;i<24;i++)tap(1);
 screenshot(argv[3],"08-pc-menu");
 for(int i=0;i<8;i++)tap(2);
 printf("pc_stage=%u potion_flag=%u potion_count=%u\n",call("VarGet",0x40F7),call("FlagGet",0x21),call("CountTotalItemQuantityInBag",28));
 observe("after-pc");
 require(2,7);if(call("CountTotalItemQuantityInBag",28)!=1)return 46;
 save_continue(2,7,"continue-after-pc");
 // Revisit the PC: no duplicate Potion and the classic item PC still opens.
 frames(8,64);frames(20,0);tap(1);close_text();
 if(call("CountTotalItemQuantityInBag",28)!=1)return 47;
 frames(64,32);frames(20,0);frames(16,64);frames(180,0);
 screenshot(argv[3],"09-mom-handoff");close_text();require(4,1);
 if(!call("FlagGet",0x20))return 48;
 screenshot(argv[3],"10-home-after-handoff");save_continue(4,1,"continue-after-handoff");
 frames(16,16);frames(20,0);frames(96,128);frames(180,0);
 require(4,0);screenshot(argv[3],"11-outside-home");
 // The exterior's existing home door must return to the updated home.
 frames(16,64);frames(180,0);require(4,1);screenshot(argv[3],"12-home-return");
 frames(32,64);frames(20,0);require(4,1);if(state[4]>=8)return 49;
 frames(8,16);frames(20,0);tap(1);frames(220,0);screenshot(argv[3],"moving-box-interaction");close_text();
 tap(8);screenshot(argv[3],"13-pokegear-menu");tap(128);tap(1);
 frames(220,0);screenshot(argv[3],"14-pokegear-phone");tap(1);frames(220,0);tap(1);frames(220,0);screenshot(argv[3],"15-mom-call");
 tap(2);frames(220,0);tap(2);frames(220,0);tap(1);frames(220,0);screenshot(argv[3],"16-pokegear-clock");close_text();
 unsigned sb2=c->busRead32(c,sym("gSaveBlock2Ptr"));
 printf("gender=%u potion_final=%u stage_final=%u\n",c->busRead8(c,sb2+8),call("CountTotalItemQuantityInBag",28),call("VarGet",0x40F7));
 if(c->busRead8(c,sb2+8)!=(argc==5?1:0))return 50;
 c->deinit(c);return 0;
}
