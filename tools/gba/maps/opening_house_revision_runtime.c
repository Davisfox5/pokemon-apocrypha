// Ordinary button input through the opening; mGBA core has no desktop window.
#define main unused_map_qualification_main
#include "runtime.c"
#undef main
static void tap(unsigned key){frames(1,key);frames(50,0);}
static const char *romPath,*outPath;
static void boot_core(void){c=mCoreFind(romPath);if(!c||!c->init(c))exit(3);mCoreConfigInit(&c->config,"apoc-opening");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,romPath))exit(4);}
static void close_text(void){for(int i=0;i<40 && call("ArePlayerFieldControlsLocked",0);i++)tap(2);if(call("ArePlayerFieldControlsLocked",0))exit(41);}
static void actor(unsigned id,int x,int y,unsigned facing,const char *tag){
 unsigned base=sym("gObjectEvents");
 for(int i=0;i<16;i++){unsigned a=base+i*0x24;if(!(c->busRead8(c,a)&1))continue;
  if(id==255?!(c->busRead8(c,a+2)&1):c->busRead8(c,a+8)!=id)continue;
  int ax=(short)c->busRead16(c,a+16)-7,ay=(short)c->busRead16(c,a+18)-7;unsigned af=c->busRead8(c,a+24)&15;
  printf("{\"actor\":%u,\"step\":\"%s\",\"x\":%d,\"y\":%d,\"facing\":%u}\n",id,tag,ax,ay,af);
  if(ax!=x||ay!=y||af!=facing)exit(55);return;
 }exit(56);
}
static void require(unsigned stage,unsigned map){observe("assert-stage");if(call("VarGet",0x40F7)!=stage||state[1]!=80||state[2]!=map)exit(42);}
static void save_continue(unsigned stage,unsigned map,const char *tag){
 // Save through the ordinary Start menu, then reload the serialized flash in
 // an entirely new emulator core and choose Continue with ordinary buttons.
 tap(8);while(c->busRead8(c,sym("sStartMenuCursorPos")))tap(64);tap(128);if(stage==4)tap(128);tap(1);
 for(int i=0;i<20;i++)tap(1);close_text();
 void*data=NULL;size_t size=c->savedataClone(c,&data);if(size!=131072)exit(43);
 char path[2048];snprintf(path,sizeof(path),"%s/%s.sav",outPath,tag);FILE*f=fopen(path,"wb");if(!f||fwrite(data,1,size,f)!=size)exit(44);fclose(f);
 c->deinit(c);boot_core();if(!c->savedataRestore(c,data,size,false))exit(45);free(data);c->reset(c);frames(600,0);
 for(int i=0;i<100;i++){tap(1);if((c->busRead32(c,sym("gMain")+4)&~1u)==sym("CB2_Overworld") && call("VarGet",0x40F7)==stage && !call("ArePlayerFieldControlsLocked",0))break;}
 require(stage,map);screenshot(outPath,tag);
}
int main(int argc,char **argv){
 if(argc!=4 && argc!=5 && argc!=6)return 2;
 romPath=argv[1];outPath=argv[3];
 FILE*f=fopen(argv[2],"r");while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);
 boot_core();c->reset(c);frames(600,0);
 screenshot(argv[3],"00-boot");tap(1);frames(180,0);screenshot(argv[3],"01-menu");
 tap(1);frames(240,0);screenshot(argv[3],"02-appearance");
 tap(1);frames(180,0);screenshot(argv[3],"03-cold-open");
 unsigned chose=0, welcomeFaced=0;
 for(int i=0;i<100;i++){
  if(!chose && call("FindTaskIdByFunc",sym("Task_NewGameBirchSpeech_ChooseGender")|1)!=255){
   if(argc==5){tap(128);frames(180,0);}
   screenshot(argv[3],"appearance-choice");chose=1;
  }
  tap(1);
  if(!welcomeFaced && call("VarGet",0x40F7)==0){
   unsigned a=sym("gObjectEvents");int mom=0,player=0;
   for(int o=0;o<16;o++){unsigned z=a+o*0x24;if(!(c->busRead8(c,z)&1))continue;int x=(short)c->busRead16(c,z+16)-7,y=(short)c->busRead16(c,z+18)-7;unsigned face=c->busRead8(c,z+24)&15;
    if(c->busRead8(c,z+8)==1&&x==5&&y==4&&face==3)mom=1;
    if((c->busRead8(c,z+2)&1)&&x==4&&y==4&&face==4)player=1;
   }
   if(mom&&player){welcomeFaced=1;frames(60,0);screenshot(argv[3],"welcome-facing");}
  }
  char tag[64];sprintf(tag,"opening-%02d",i);screenshot(argv[3],tag);if(call("VarGet",0x40F7)==1 && !call("ArePlayerFieldControlsLocked",0))break;
 }
 if(!welcomeFaced)return 57;
 screenshot(argv[3],"04-home-ready");
 observe("welcome-finished");actor(1,2,7,2,"mom-door");
 printf("home_stage=%u gear=%u potion=%u\n",call("VarGet",0x40F7),call("FlagGet",0x20),call("FlagGet",0x21));
 require(1,1);save_continue(1,1,"continue-before-pc");

 // Walk around furniture to test the guarded doorway.
 frames(32,32);frames(32,128);frames(50,0);
 observe("exit-blocked");actor(1,2,7,2,"mom-guard");actor(255,2,6,1,"player-guard");screenshot(argv[3],"05-exit-guard");
 for(int i=0;i<12 && call("ArePlayerFieldControlsLocked",0);i++)tap(2);
 observe("exit-guard-return");
 // Return via the clear eastern aisle and enter the stairs.
 frames(48,64);frames(20,0);frames(16,32);frames(180,0);
 observe("upstairs");actor(255,2,3,4,"stair-right-arrival");screenshot(argv[3],"06-bedroom");
 // Approach the desk from its south side.
 frames(16,128);frames(20,0);frames(48,16);frames(20,0);frames(8,64);frames(20,0);tap(1);
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
 frames(48,32);frames(20,0);frames(16,64);frames(20,0);frames(16,32);frames(180,0);
 actor(1,3,3,3,"mom-handoff");actor(255,2,3,4,"player-handoff");screenshot(argv[3],"09-mom-handoff");close_text();require(4,1);
 if(!call("FlagGet",0x20))return 48;
 actor(1,3,5,1,"mom-unpacking");screenshot(argv[3],"10-home-after-handoff");save_continue(4,1,"continue-after-handoff");
 frames(80,128);frames(180,0);
 require(4,0);screenshot(argv[3],"11-outside-home");
 // Chapter 1 now starts its automatic street scene as soon as the house is
 // exited. The historical house/Pokegear-only harness can stop at that seam;
 // chapter_continuous_runtime.c drives the remaining scenes from this save.
 if(argc==6){c->deinit(c);return 0;}
 // The exterior's existing home door must return to the updated home.
 frames(16,64);frames(180,0);require(4,1);actor(1,3,5,1,"mom-return");screenshot(argv[3],"12-home-return");
 frames(32,64);frames(20,0);require(4,1);if(state[4]>=7)return 49;
 frames(8,128);frames(20,0);tap(1);frames(220,0);screenshot(argv[3],"moving-box-interaction");close_text();
 tap(8);while(c->busRead8(c,sym("sStartMenuCursorPos")))tap(64);screenshot(argv[3],"13-pokegear-menu");tap(128);tap(1);
 frames(220,0);screenshot(argv[3],"14-pokegear-clock");tap(1);screenshot(argv[3],"clock-24h");tap(1);tap(256);screenshot(argv[3],"15-pokegear-radio");
 tap(16);screenshot(argv[3],"radio-no-signal");tap(8);tap(32);tap(1);
 if((call("VarGet",0x40F9)&127)!=17)return 58;
 tap(32);tap(8);tap(128);tap(1);screenshot(argv[3],"16-radio-music");tap(8);
 tap(256);screenshot(argv[3],"17-pokegear-map-card");tap(256);screenshot(argv[3],"18-pokegear-phone");
 tap(1);screenshot(argv[3],"19-mom-call");tap(2);tap(256);screenshot(argv[3],"20-pokegear-style");
 tap(16);screenshot(argv[3],"21-pink-style");
 for(int i=2;i<6;i++){tap(16);char tag[64];sprintf(tag,"style-%d",i);screenshot(argv[3],tag);}
 tap(16);tap(16);tap(1);tap(2);tap(2);frames(180,0);
 save_continue(4,1,"continue-gear-settings");
 if(call("VarGet",0x40F8)!=12)return 53;
 if(call("VarGet",0x40F9)!=304)return 54;
 tap(8);while(c->busRead8(c,sym("sStartMenuCursorPos")))tap(64);tap(128);tap(1);frames(180,0);screenshot(argv[3],"gear-style-cold-reopen");tap(2);tap(2);
 unsigned sb2=c->busRead32(c,sym("gSaveBlock2Ptr"));
 printf("gender=%u potion_final=%u stage_final=%u\n",c->busRead8(c,sb2+8),call("CountTotalItemQuantityInBag",28),call("VarGet",0x40F7));
 if(c->busRead8(c,sb2+8)!=(argc==5?1:0))return 50;
 c->deinit(c);return 0;
}
