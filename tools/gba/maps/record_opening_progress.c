// Ordinary button input through the opening; mGBA core has no desktop window.
#define main unused_map_qualification_main
#define frames unused_frames
#include "runtime.c"
#undef frames
#include <mgba/core/blip_buf.h>
static FILE *video,*audio,*chapters;
static unsigned recorded=0;
static void mark(const char *title){fprintf(chapters,"%u\t%s\n",recorded,title);fflush(chapters);}
static void frames(int n,unsigned keys){
 c->setKeys(c,keys);
 for(int i=0;i<n;i++){c->runFrame(c);if(fwrite(pixels,sizeof(pixels),1,video)!=1)exit(60);recorded++;
  short samples[8192];int a=blip_samples_avail(c->getAudioChannel(c,0));int b=blip_samples_avail(c->getAudioChannel(c,1));if(b<a)a=b;if(a>4096)a=4096;
  blip_read_samples(c->getAudioChannel(c,0),samples,a,1);blip_read_samples(c->getAudioChannel(c,1),samples+1,a,1);fwrite(samples,4,a,audio);
 }c->setKeys(c,0);
}
#undef main
static void tap(unsigned key){frames(1,key);frames(180,0);}
static const char *romPath,*outPath;
static void boot_core(void){c=mCoreFind(romPath);if(!c||!c->init(c))exit(3);mCoreConfigInit(&c->config,"apoc-opening");c->rtc.override=RTC_FIXED;c->rtc.value=1790524800000LL;c->setVideoBuffer(c,pixels,240);c->setAudioBufferSize(c,4096);blip_set_rates(c->getAudioChannel(c,0),c->frequency(c),48000);blip_set_rates(c->getAudioChannel(c,1),c->frequency(c),48000);if(!mCoreLoadFile(c,romPath))exit(4);}
static void close_text(void){for(int i=0;i<40 && call("ArePlayerFieldControlsLocked",0);i++)tap(2);if(call("ArePlayerFieldControlsLocked",0))exit(41);}
static void require(unsigned stage,unsigned map){observe("assert-stage");if(call("VarGet",0x40F7)!=stage||state[1]!=80||state[2]!=map)exit(42);}
static void save_continue(unsigned stage,unsigned map,const char *tag){
 // Save through the ordinary Start menu, then reload the serialized flash in
 // an entirely new emulator core and choose Continue with ordinary buttons.
 tap(8);tap(128);if(stage==4)tap(128);tap(1);
 for(int i=0;i<8;i++)tap(1);close_text();
 void*data=NULL;size_t size=c->savedataClone(c,&data);if(size!=131072)exit(43);
 char path[2048];snprintf(path,sizeof(path),"%s/%s.sav",outPath,tag);FILE*f=fopen(path,"wb");if(!f||fwrite(data,1,size,f)!=size)exit(44);fclose(f);
 c->deinit(c);boot_core();if(!c->savedataRestore(c,data,size,false))exit(45);free(data);c->reset(c);frames(600,0);
 for(int i=0;i<100;i++){tap(1);if((c->busRead32(c,sym("gMain")+4)&~1u)==sym("CB2_Overworld") && call("VarGet",0x40F7)==stage && !call("ArePlayerFieldControlsLocked",0))break;}
 require(stage,map);screenshot(outPath,tag);
}
int main(int argc,char **argv){
 if(argc!=4 && argc!=5)return 2;
 romPath=argv[1];outPath=argv[3];
 video=popen("/opt/homebrew/bin/ffmpeg -hide_banner -loglevel error -y -f rawvideo -pixel_format rgb0 -video_size 240x160 -framerate 16777216/280896 -i pipe:0 -vf scale=960:640:flags=neighbor -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p tools/vendor/gba/opening-recording/video.mp4", "w");
 audio=fopen("tools/vendor/gba/opening-recording/audio.s16","wb");chapters=fopen("tools/vendor/gba/opening-recording/chapters.tsv","w");if(!video||!audio||!chapters)return 59;
 mark("Opening playthrough — New Game");
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
 require(1,1);mark("New home, moving boxes and exit guard");

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
 for(int i=0;i<4;i++)tap(1);
 screenshot(argv[3],"08-pc-menu");
 for(int i=0;i<3;i++)tap(2);
 printf("pc_stage=%u potion_flag=%u potion_count=%u\n",call("VarGet",0x40F7),call("FlagGet",0x21),call("CountTotalItemQuantityInBag",28));
 observe("after-pc");
 require(2,7);if(call("CountTotalItemQuantityInBag",28)!=1)return 46;
 mark("Bedroom and one-time Potion");
 // Revisit the PC: no duplicate Potion and the classic item PC still opens.
 frames(8,64);frames(20,0);tap(1);close_text();
 if(call("CountTotalItemQuantityInBag",28)!=1)return 47;
 frames(64,32);frames(20,0);frames(16,64);frames(180,0);
 screenshot(argv[3],"09-mom-handoff");close_text();require(4,1);
 if(!call("FlagGet",0x20))return 48;
 mark("Mom handoff and ordinary Save / Continue");screenshot(argv[3],"10-home-after-handoff");save_continue(4,1,"continue-after-handoff");
 frames(16,16);frames(20,0);frames(96,128);frames(180,0);
 require(4,0);screenshot(argv[3],"11-outside-home");
 // The exterior's existing home door must return to the updated home.
 frames(16,64);frames(180,0);require(4,1);screenshot(argv[3],"12-home-return");
 frames(32,64);frames(20,0);require(4,1);if(state[4]>=8)return 49;
 frames(8,16);frames(20,0);tap(1);frames(220,0);screenshot(argv[3],"moving-box-interaction");close_text();
 mark("Moving boxes, Pokegear phone and clock");tap(8);screenshot(argv[3],"13-pokegear-menu");tap(128);tap(1);
 frames(220,0);screenshot(argv[3],"14-pokegear-phone");tap(1);frames(220,0);tap(1);frames(220,0);screenshot(argv[3],"15-mom-call");
 tap(2);frames(220,0);tap(2);frames(220,0);tap(1);frames(220,0);screenshot(argv[3],"16-pokegear-clock");close_text();
 unsigned sb2=c->busRead32(c,sym("gSaveBlock2Ptr"));
 printf("gender=%u potion_final=%u stage_final=%u\n",c->busRead8(c,sb2+8),call("CountTotalItemQuantityInBag",28),call("VarGet",0x40F7));
 if(c->busRead8(c,sb2+8)!=(argc==5?1:0))return 50;

 mark("Map / art previews — debug camera repositioning; story unfinished");
 const unsigned views[][3]={
 {0,43,18},{0,39,17},{0,53,25},{0,48,9},{0,30,20},{0,32,10},{0,44,2},
 {13,19,16},{13,27,17},{13,21,25},{13,32,27},{13,29,29},
 {20,30,62},{20,23,59},{20,32,58},{20,21,33},{20,27,23},{20,41,47},{20,33,15},{20,17,48}
 };
 unsigned previous=999;
 for(unsigned i=0;i<sizeof(views)/sizeof(views[0]);i++){
  unsigned map=views[i][0];
  if(map!=previous){mark(map==0?"Cherrygrove City — map preview":map==13?"Sandgem Town — map preview":"Floccesy Town — map preview");previous=map;}
  call("MapProof_Enter",map|(views[i][1]<<8)|(views[i][2]<<16));frames(240,0);observe("preview-camera");
  frames(64,16);frames(180,0);frames(64,32);frames(180,0);
 }
 mark("End");c->deinit(c);int status=pclose(video);fclose(audio);fclose(chapters);printf("recorded_frames=%u encoder_status=%d\n",recorded,status);return status;

}
