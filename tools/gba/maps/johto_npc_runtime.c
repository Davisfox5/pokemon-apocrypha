// Read-only NPC observation during ordinary engine movement. Struct offsets are
// documented in this pinned engine's global.fieldmap.h and sprite.h.
#define main unused_map_qualification_main
#include "runtime.c"
#undef main
static unsigned boy(void){
 for(unsigned i=0;i<16;i++){unsigned o=sym("gObjectEvents")+i*0x24;if((c->busRead8(c,o)&1)&&c->busRead16(c,o+4)==1024)return o;}
 exit(30);
}
static void sample(unsigned tick){
 printf("{\"tick\":%u,\"objects\":[",tick);int comma=0;
 for(unsigned i=0;i<16;i++){
  unsigned o=sym("gObjectEvents")+i*0x24;
  if(!(c->busRead8(c,o)&1))continue;
  unsigned gid=c->busRead16(c,o+4),sid=c->busRead8(c,o+0x23),s=sym("gSprites")+sid*0x44;
  if(gid<1024||gid>=1029)continue;
  printf("%s{\"gfx\":%u,\"local\":%u,\"x\":%d,\"y\":%d,\"facing\":%u,\"anim\":%u,\"cmd\":%u,\"palette\":%u,\"hflip\":%u}",comma++?",":"",gid,c->busRead8(c,o+8),(short)c->busRead16(c,o+0x10)-7,(short)c->busRead16(c,o+0x12)-7,c->busRead8(c,o+0x18)&15,c->busRead8(c,s+0x2a),c->busRead8(c,s+0x2b),c->busRead16(c,s+4)>>12,c->busRead8(c,s+0x3f)&1);
 }
 printf("]}\n");
}
int main(int argc,char**argv){
 if(argc!=4)return 2;
 FILE*f=fopen(argv[2],"r");if(!f)return 3;
 while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);
 c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;
 mCoreConfigInit(&c->config,"johto-npc");c->setVideoBuffer(c,pixels,240);
 if(!mCoreLoadFile(c,argv[1]))return 5;
 c->rtc.override=RTC_FIXED;c->rtc.value=1789300800000LL;
 c->reset(c);frames(600,0);call("MapProof_Boot",0);frames(240,0);
 call("MapProof_Enter",(50<<8)|(13<<16));frames(360,0);
 screenshot(argv[3],"residents");
 for(unsigned i=0;i<360;i++){
  frames(4,0);sample(i*4);char tag[80];sprintf(tag,"npc-%03u",i);screenshot(argv[3],tag);
 }
 // Controlled camera/starting position; interaction itself uses normal buttons.
 call("MapProof_Enter",(48<<8)|(12<<16));frames(360,0);
 frames(1,64);frames(20,0);
 for(unsigned i=0;i<40&&!call("ArePlayerFieldControlsLocked",0);i++){frames(1,1);frames(16,0);}
 if(!call("ArePlayerFieldControlsLocked",0))return 31;
 frames(180,0);screenshot(argv[3],"walking-resident-dialogue");
 unsigned o=boy(),pos=c->busRead32(c,o+0x10);
 if((c->busRead8(c,o+0x18)&15)!=1)return 32;
 frames(120,0);if(c->busRead32(c,o+0x10)!=pos)return 33;
 for(unsigned i=0;i<40&&call("ArePlayerFieldControlsLocked",0);i++){frames(1,2);frames(40,0);}
 if(call("ArePlayerFieldControlsLocked",0))return 34;
 int resumed=0;
 for(unsigned i=0;i<32;i++){frames(4,0);if(c->busRead32(c,boy()+0x10)!=pos)resumed=1;}
 if(!resumed)return 35;
 screenshot(argv[3],"walking-resident-resumed");
 printf("{\"interaction\":true,\"faces_player\":true,\"stops_for_dialogue\":true,\"resumes_walking\":true}\n");
 c->deinit(c);return 0;
}
