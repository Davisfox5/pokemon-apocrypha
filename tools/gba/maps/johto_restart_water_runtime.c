// Read-only test of Emerald's native animated water under new custom scenery.
#define main unused_map_qualification_main
#include "runtime.c"
#undef main
static int animated(unsigned t){return (t>=432&&t<462)||(t>=464&&t<474)||(t>=480&&t<490)||(t>=496&&t<502)||(t>=508&&t<512);}
static unsigned tile_hash(int moving){unsigned h=2166136261u;for(unsigned t=0;t<1008;t++)if(animated(t)==moving)for(unsigned j=0;j<32;j++)h=(h^c->busRead8(c,0x06000000+t*32+j))*16777619u;return h;}
int main(int argc,char**argv){
 if(argc!=4)return 2;FILE*f=fopen(argv[2],"r");if(!f)return 3;while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;mCoreConfigInit(&c->config,"johto-restart-water");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 c->rtc.override=RTC_FIXED;c->rtc.value=1789315200000LL;c->reset(c);frames(600,0);call("MapProof_Boot",0);frames(240,0);call("MapProof_Enter",(29<<8)|(20<<16));frames(360,0);
 unsigned stable=tile_hash(0),seen[64],count=0;
 for(unsigned i=0;i<64;i++){
  frames(8,0);if(tile_hash(0)!=stable){fprintf(stderr,"Static terrain overwritten by animation\n");return 6;}
  unsigned h=tile_hash(1);int exists=0;for(unsigned j=0;j<count;j++)if(seen[j]==h)exists=1;if(!exists)seen[count++]=h;
  char tag[80];sprintf(tag,"water-%02u",i);screenshot(argv[3],tag);
 }
 if(count<4)return 7;printf("{\"frames\":512,\"distinct_animation_states\":%u,\"static_terrain_unchanged\":true,\"native_emerald_animation\":true}\n",count);c->deinit(c);return 0;
}
