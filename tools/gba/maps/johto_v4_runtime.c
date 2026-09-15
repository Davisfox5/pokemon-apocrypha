// NPC preview acceptance: HGSS exterior coverage, ordinary doors and matching Continue save.
#define main unused_map_qualification_main
#include "runtime.c"
#undef main
static void close_dialog(void){for(int i=0;i<40 && call("ArePlayerFieldControlsLocked",0);i++){frames(1,2);frames(40,0);}if(call("ArePlayerFieldControlsLocked",0)){fprintf(stderr,"field still locked after dialogue\n");exit(45);}}
static void go(unsigned map,unsigned x,unsigned y){call("MapProof_Enter",map|(x<<8)|(y<<16));frames(360,0);}
static void expect(unsigned map,const char*tag){observe(tag);if(state[0]!=2||state[1]!=80||state[2]!=map){fprintf(stderr,"expected town group 80 map %u at %s\n",map,tag);exit(40);}}
int main(int argc,char**argv){
 if(argc!=5){fprintf(stderr,"town-runtime ROM SYMBOLS OUT write|read\n");return 2;}
 FILE*f=fopen(argv[2],"r");if(!f)return 3;while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;mCoreConfigInit(&c->config,"cherrygrove");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 char flash[2048];snprintf(flash,sizeof(flash),"%s/town.sav",argv[3]);
 if(strcmp(argv[4],"write")){unsigned char data[131072];f=fopen(flash,"rb");if(!f||fread(data,1,sizeof(data),f)!=sizeof(data))return 6;fclose(f);if(!c->savedataRestore(c,data,sizeof(data),false))return 7;}
 c->rtc.override=RTC_FIXED;c->rtc.value=1789315200000LL;
 c->reset(c);frames(600,0);
 if(!strcmp(argv[4],"menu")){
  screenshot(argv[3],"boot-before-start");frames(1,8);frames(180,0);screenshot(argv[3],"boot-after-start");frames(1,1);frames(300,0);screenshot(argv[3],"boot-after-a");frames(1,1);frames(180,0);screenshot(argv[3],"continue-menu");frames(1,1);frames(300,0);screenshot(argv[3],"ordinary-continue");expect(0,"ordinary-title-continue");if(state[3]!=39||state[4]!=16)return 12;
 }else if(!strcmp(argv[4],"read")){
  unsigned s=call("LoadGameSave",0);if(s!=1)return 8;call("MapProof_Resume",0);frames(240,0);expect(0,"cold-reload");screenshot(argv[3],"cold-reload");if(state[3]!=39||state[4]!=16)return 9;
 }else{
  call("MapProof_Boot",0);frames(240,0);expect(0,"town-spawn");screenshot(argv[3],"town-spawn");
  const unsigned doors[][2]={{34,14},{45,16},{54,19},{42,8},{51,8}};
  const unsigned maps[]={1,2,3,5,6};
  const unsigned exits[][2]={{9,8},{3,8},{3,8},{3,7},{7,8}};
  for(unsigned i=0;i<5;i++){
   go(0,doors[i][0],doors[i][1]+1);
   for(unsigned t=0;t<100;t++){frames(1,t<20?64:0);if(t%2==0){char tag[80];sprintf(tag,"door-%u-%03u",i,t);screenshot(argv[3],tag);}}
   frames(120,0);char tag[80];sprintf(tag,"door-in-%u",maps[i]);expect(maps[i],tag);screenshot(argv[3],tag);
   go(maps[i],exits[i][0],exits[i][1]-1);frames(20,128);frames(180,0);sprintf(tag,"door-out-%u",maps[i]);expect(0,tag);
  }
  go(1,8,3);frames(20,64);frames(180,0);expect(7,"bedroom-stairs-up");screenshot(argv[3],"bedroom");
  go(7,6,1);frames(20,16);frames(180,0);expect(1,"bedroom-stairs-down");
  go(0,61,15);frames(64,16);frames(40,0);expect(9,"route29-out");screenshot(argv[3],"route29");frames(80,32);frames(40,0);expect(0,"route29-return");
  go(0,36,2);frames(64,64);frames(40,0);expect(10,"route30-out");screenshot(argv[3],"route30");frames(80,128);frames(40,0);expect(0,"route30-return");
  go(0,24,16);frames(32,32);frames(20,0);expect(0,"shore-collision");if(state[3]!=24)return 10;
  go(0,39,16);screenshot(argv[3],"residential-lane");
  go(0,49,20);screenshot(argv[3],"flower-lane");
  go(0,45,18);screenshot(argv[3],"gold-house");
  go(0,47,10);screenshot(argv[3],"center-and-mart");
  go(0,30,17);screenshot(argv[3],"shoreline");
  go(5,3,3);frames(8,32);frames(8,0);frames(1,1);frames(150,0);frames(1,1);frames(90,0);screenshot(argv[3],"mart-menu");close_dialog();
  go(0,39,16);expect(0,"save-by-residents");screenshot(argv[3],"waterfront");unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
 }
 c->deinit(c);return 0;
}
