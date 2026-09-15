// Read-only NPC observation during ordinary engine movement. Struct offsets are
// documented in this pinned engine's global.fieldmap.h and sprite.h.
#define main unused_map_qualification_main
#include "runtime.c"
#undef main
// Compare the actual OBJ VRAM pixels with each native image cell. Direction
// fields alone do not prove that a stopped NPC displays the corresponding pose.
static int visible_frame(unsigned sprite){
 unsigned vram=0x06010000+(c->busRead16(c,sprite+4)&1023)*32;
 unsigned images=c->busRead32(c,sprite+0xc);
 for(int f=0;f<12;f++){
  unsigned data=c->busRead8(c,images+6) ? c->busRead32(c,images)+f*c->busRead16(c,images+4) : c->busRead32(c,images+f*8);int same=1;
  for(unsigned i=0;i<512;i+=4)if(c->busRead32(c,vram+i)!=c->busRead32(c,data+i)){same=0;break;}
  if(same)return f;
 }
 return -1;
}
static unsigned view;
static void sample(unsigned tick){
 printf("{\"view\":%u,\"tick\":%u,\"objects\":[",view,tick);int comma=0;
 for(unsigned i=0;i<16;i++){
  unsigned o=sym("gObjectEvents")+i*0x24;
  if(!(c->busRead8(c,o)&1))continue;
  unsigned gid=c->busRead16(c,o+4),sid=c->busRead8(c,o+0x23),s=sym("gSprites")+sid*0x44;
  if(gid<1024||gid>=1037||gid==1028)continue;
  printf("%s{\"gfx\":%u,\"local\":%u,\"x\":%d,\"y\":%d,\"facing\":%u,\"anim\":%u,\"cmd\":%u,\"palette\":%u,\"hflip\":%u,\"frame\":%d}",comma++?",":"",gid,c->busRead8(c,o+8),(short)c->busRead16(c,o+0x10)-7,(short)c->busRead16(c,o+0x12)-7,c->busRead8(c,o+0x18)&15,c->busRead8(c,s+0x2a),c->busRead8(c,s+0x2b),c->busRead16(c,s+4)>>12,c->busRead8(c,s+0x3f)&1,visible_frame(s));
 }
 printf("]}\n");
}
static const char *argv_out;
static void interaction(unsigned gid,unsigned x,unsigned y,const char *tag){
 call("MapProof_Enter",(x<<8)|(y<<16));frames(360,0);
 frames(1,64);frames(20,0);
 for(unsigned i=0;i<80&&!call("ArePlayerFieldControlsLocked",0);i++){frames(1,1);frames(16,0);}
 if(!call("ArePlayerFieldControlsLocked",0)){screenshot(argv_out,"interaction-failed");fprintf(stderr,"Could not interact with %u\n",gid);exit(31);}
 frames(180,0);screenshot(argv_out,tag);
 unsigned o=0;for(unsigned i=0;i<16;i++){unsigned q=sym("gObjectEvents")+i*0x24;if((c->busRead8(c,q)&1)&&c->busRead16(c,q+4)==gid)o=q;}
 if(!o||(c->busRead8(c,o+0x18)&15)!=1)exit(32);
 unsigned sprite=sym("gSprites")+c->busRead8(c,o+0x23)*0x44;
 if(visible_frame(sprite)!=9){fprintf(stderr,"NPC %u faces south but displays frame %d\n",gid,visible_frame(sprite));exit(36);}
 unsigned pos=c->busRead32(c,o+0x10);
 frames(120,0);if(c->busRead32(c,o+0x10)!=pos)exit(33);
 for(unsigned i=0;i<40&&call("ArePlayerFieldControlsLocked",0);i++){frames(1,2);frames(40,0);}
 if(call("ArePlayerFieldControlsLocked",0))exit(34);
 int resumed=0;for(unsigned i=0;i<80;i++){frames(4,0);if(c->busRead32(c,o+0x10)!=pos)resumed=1;}
 if(!resumed)exit(35);
 printf("{\"interaction\":%u,\"faces_player\":true,\"displayed_south_idle_frame_verified\":true,\"stops_for_dialogue\":true,\"resumes_walking\":true}\n",gid);
}
int main(int argc,char**argv){
 if(argc!=4)return 2;argv_out=argv[3];
 FILE*f=fopen(argv[2],"r");if(!f)return 3;
 while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);
 c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;
 mCoreConfigInit(&c->config,"johto-v4-npc");c->setVideoBuffer(c,pixels,240);
 if(!mCoreLoadFile(c,argv[1]))return 5;
 c->rtc.override=RTC_FIXED;c->rtc.value=1789315200000LL;
 c->reset(c);frames(600,0);call("MapProof_Boot",0);frames(240,0);
 const unsigned views[][2]={{40,16},{47,8},{54,20},{30,17},{36,7}};
 for(view=0;view<5;view++){
  call("MapProof_Enter",(views[view][0]<<8)|(views[view][1]<<16));frames(360,0);
  for(unsigned i=0;i<360;i++){
   frames(4,0);sample(i*4);char tag[80];sprintf(tag,"view-%u-%03u",view,i);screenshot(argv[3],tag);
  }
 }
 interaction(1029,39,16,"gold-dialogue");
 interaction(1030,49,20,"silver-dialogue");
 interaction(1031,37,19,"kestra-dialogue");
 interaction(1032,47,11,"hoenn-dialogue");
 interaction(1033,58,16,"kanto-dialogue");
 interaction(1034,39,11,"johto-dialogue");
 interaction(1035,31,19,"sinnoh-dialogue");
 interaction(1036,52,23,"unova-dialogue");
 c->deinit(c);return 0;
}
