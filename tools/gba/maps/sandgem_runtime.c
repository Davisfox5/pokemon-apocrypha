// NPC preview acceptance: unchanged town coverage; Continue starts by residents.
#define main unused_map_qualification_main
#include "runtime.c"
#undef main
static void close_dialog(void){for(int i=0;i<40 && call("ArePlayerFieldControlsLocked",0);i++){frames(1,2);frames(40,0);}if(call("ArePlayerFieldControlsLocked",0)){fprintf(stderr,"field still locked after dialogue\n");exit(45);}}
static void go(unsigned map,unsigned x,unsigned y){call("MapProof_Enter",map|(x<<8)|(y<<16));frames(360,0);}
static void expect(unsigned map,const char*tag){observe(tag);if(state[0]!=(map>=13?4:2)||state[1]!=80||state[2]!=map){fprintf(stderr,"expected town group 80 map %u at %s\n",map,tag);exit(40);}}
int main(int argc,char**argv){
 if(argc!=5){fprintf(stderr,"town-runtime ROM SYMBOLS OUT write|read\n");return 2;}
 FILE*f=fopen(argv[2],"r");if(!f)return 3;while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;mCoreConfigInit(&c->config,"cherrygrove");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 char flash[2048];snprintf(flash,sizeof(flash),"%s/town.sav",argv[3]);
 if(strcmp(argv[4],"write")){unsigned char data[131072];f=fopen(flash,"rb");if(!f||fread(data,1,sizeof(data),f)!=sizeof(data))return 6;fclose(f);if(!c->savedataRestore(c,data,sizeof(data),false))return 7;}
 c->rtc.override=RTC_FIXED;c->rtc.value=1789315200000LL;
 c->reset(c);frames(600,0);
 if(!strcmp(argv[4],"menu")){
  screenshot(argv[3],"boot-before-start");frames(1,8);frames(180,0);screenshot(argv[3],"boot-after-start");frames(1,1);frames(300,0);screenshot(argv[3],"boot-after-a");frames(1,1);frames(180,0);screenshot(argv[3],"continue-menu");frames(1,1);frames(300,0);screenshot(argv[3],"ordinary-continue");expect(13,"ordinary-title-continue");if(state[3]!=29||state[4]!=29)return 12;
 }else if(!strcmp(argv[4],"read")){
  unsigned s=call("LoadGameSave",0);if(s!=1)return 8;call("MapProof_Resume",0);frames(240,0);expect(13,"cold-reload");screenshot(argv[3],"cold-reload");if(state[3]!=29||state[4]!=29)return 9;
 }else{
  call("MapProof_Boot",0);frames(240,0);
  go(0,44,2);frames(64,64);frames(60,0);expect(10,"north-out-of-cherrygrove");
  frames(100,64);frames(240,0);expect(13,"walk-into-sandgem");screenshot(argv[3],"arrival");
  go(13,29,31);frames(40,128);frames(240,0);expect(10,"walk-back-to-johto");
  frames(150,128);frames(120,0);expect(0,"cherrygrove-return");screenshot(argv[3],"cherrygrove-preserved");
  const unsigned doors[][2]={{15,13},{23,13},{33,13},{14,22},{23,22}};
  const unsigned exits[][2]={{6,12},{7,8},{3,7},{3,8},{3,8}};
  for(unsigned i=0;i<5;i++){
   go(13,doors[i][0],doors[i][1]+1);
   for(unsigned t=0;t<100;t++){frames(1,t<20?64:0);if(t%5==0){char tag[80];sprintf(tag,"door-%u-%03u",i,t);screenshot(argv[3],tag);}}
   frames(150,0);char tag[80];sprintf(tag,"door-in-%u",i);expect(14+i,tag);screenshot(argv[3],tag);
   go(14+i,exits[i][0],exits[i][1]-1);frames(20,128);frames(180,0);sprintf(tag,"door-out-%u",i);expect(13,tag);
  }
  go(15,2,6);frames(20,32);frames(180,0);expect(19,"center-upstairs");
  go(19,2,6);frames(20,32);frames(180,0);expect(15,"center-downstairs");
  go(13,19,16);screenshot(argv[3],"laboratory");
  go(13,27,17);screenshot(argv[3],"center");
  go(13,21,25);screenshot(argv[3],"houses");
  go(13,32,27);screenshot(argv[3],"beach");
  go(13,29,29);expect(13,"sandgem-save");screenshot(argv[3],"sandgem-start");
  unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);

 }
 c->deinit(c);return 0;
}
