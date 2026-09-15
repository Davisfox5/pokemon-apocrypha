// Read-only VRAM verification of the isolated town's reserved sea animation.
#define main unused_map_qualification_main
#include "runtime.c"
#undef main
static unsigned hash(unsigned addr,unsigned bytes){unsigned h=2166136261u;for(unsigned i=0;i<bytes;i++)h=(h^c->busRead8(c,addr+i))*16777619u;return h;}
int main(int argc,char**argv){
 if(argc!=4)return 2;FILE*f=fopen(argv[2],"r");if(!f)return 3;
 while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;
 mCoreConfigInit(&c->config,"johto-v4-water");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 c->rtc.override=RTC_FIXED;c->rtc.value=1789315200000LL;c->reset(c);frames(600,0);call("MapProof_Boot",0);frames(240,0);
 call("MapProof_Enter",(29<<8)|(16<<16));frames(360,0);
 unsigned stable=hash(0x06000000+17*32,(1008-17)*32),seen[64],unique=0;
 for(unsigned i=0;i<64;i++){
  frames(8,0);unsigned sea=hash(0x06000000+32,512);int found=0;for(unsigned j=0;j<unique;j++)if(seen[j]==sea)found=1;if(!found)seen[unique++]=sea;
  if(hash(0x06000000+17*32,(1008-17)*32)!=stable){fprintf(stderr,"Static scenery changed during sea loop\n");return 6;}
  char tag[80];sprintf(tag,"water-%02u",i);screenshot(argv[3],tag);
 }
 if(unique!=32){fprintf(stderr,"Expected 32 sea phases, saw %u\n",unique);return 7;}
 printf("{\"sea_phases\":%u,\"engine_frames\":512,\"static_tile_region_unchanged\":true,\"reserved_tile_range\":[1,16]}\n",unique);c->deinit(c);return 0;
}
