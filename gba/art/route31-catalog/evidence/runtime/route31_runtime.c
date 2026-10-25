
#define main unused_map_qualification_main
#include "/home/user/pokemon-apocrypha/tools/gba/maps/runtime.c"
#undef main
#define START_X 11
#define START_Y 2
#define DOOR_X 6
#define DOOR_Y 13
#define BACK_X 53
#define BACK_Y 14
#define TOUR_X 39
#define TOUR_Y 31
#define GRASS_X 51
#define GRASS_Y 22
#define GRASS_KEY 128
#define GRASS_N 6
#define SAVE_X 39
#define SAVE_Y 31
#define FLAG_POKE_BALL 616
#define FLAG_POTION 617
#define R30 10
#define R31 29
#define GATE 33
#define CAVE 34
#define RIGHT 16
#define LEFT 32
#define UP 64
#define DOWN 128
#define A 1
#define B 2
static const char *out;
static int shots;
static void shot(const char*t){screenshot(out,t);call("MapProof_ReadState",0);unsigned a=sym("gMapProofState");printf("{\"shot\":\"%s\",\"map\":%u,\"x\":%u,\"y\":%u}\n",t,c->busRead32(c,a+8),c->busRead32(c,a+12),c->busRead32(c,a+16));fflush(stdout);shots++;}
static void go(unsigned map,unsigned x,unsigned y){call("MapProof_Enter",map|(x<<8)|(y<<16));frames(360,0);}
static void need(int ok,const char*tag){if(!ok){fprintf(stderr,"FAILED %s (map %u at %u,%u)\n",tag,state[2],state[3],state[4]);shot(tag);exit(40);}}
static void at(unsigned map,unsigned x,unsigned y,const char*tag){observe(tag);need(state[1]==80&&state[2]==map&&state[3]==x&&state[4]==y,tag);}
static void on(unsigned map,const char*tag){observe(tag);need(state[1]==80&&state[2]==map,tag);}
static void pos(unsigned*m,unsigned*x,unsigned*y){call("MapProof_ReadState",0);unsigned a=sym("gMapProofState");*m=c->busRead32(c,a+8);*x=c->busRead32(c,a+12);*y=c->busRead32(c,a+16);}
static void step(unsigned key){unsigned m0,x0,y0,m1,x1,y1;pos(&m0,&x0,&y0);int moved=0;for(int t=0;t<32&&!moved;t++){frames(2,key);pos(&m1,&x1,&y1);moved=(m1!=m0||x1!=x0||y1!=y0);}frames(moved?40:8,0);frames(16,0);}
static void tap(unsigned key){frames(2,key);frames(12,0);}
static int locked(void){return call("ArePlayerFieldControlsLocked",0);}
static int overworld(void){unsigned cb=c->busRead32(c,sym("gMain")+4);return (cb&~1u)==(sym("CB2_Overworld")&~1u);}
static void close_dialog(void){for(int i=0;i<40&&locked();i++){frames(1,B);frames(40,0);}need(!locked(),"dialogue-closes");}
struct mv{unsigned char key;unsigned short map,x,y;const char*tag;};
static void walk(const struct mv*m,int n){for(int i=0;i<n;i++){step(m[i].key);char t[96];sprintf(t,"walk-%s",m[i].tag?m[i].tag:"step");at(m[i].map,m[i].x,m[i].y,t);need(overworld()&&!locked(),"walk-no-interruption");if(m[i].tag)shot(m[i].tag);}}
static void warp_into(unsigned key,unsigned map,const char*tag){frames(2,key);for(int i=0;i<120;i++){frames(8,key);call("MapProof_ReadState",0);if(c->busRead32(c,sym("gMapProofState")+8)==map)break;}frames(240,0);on(map,tag);shot(tag);}
static void ledge(unsigned x,unsigned y,unsigned key,int dx,int dy,const char*tag){char t[64];go(R31,x,y);step(key);sprintf(t,"%s-jump",tag);at(R31,x+2*dx,y+2*dy,t);unsigned back=key==DOWN?UP:key==UP?DOWN:key==LEFT?RIGHT:LEFT;step(back);sprintf(t,"%s-no-climb",tag);at(R31,x+2*dx,y+2*dy,t);}
static void blocked(unsigned x,unsigned y,unsigned key,const char*tag){go(R31,x,y);step(key);at(R31,x,y,tag);}
static void read_sign(unsigned x,unsigned y,const char*tag){go(R31,x,y+1);tap(UP);frames(1,A);frames(120,0);need(locked(),tag);shot(tag);close_dialog();}
static void ball(unsigned x,unsigned y,unsigned flag,const char*tag){char t[64];go(R31,x,y+1);tap(UP);sprintf(t,"%s-facing",tag);at(R31,x,y+1,t);need(call("FlagGet",flag)==0,tag);frames(1,A);frames(150,0);need(locked(),tag);shot(tag);close_dialog();frames(60,0);need(call("FlagGet",flag)==1,tag);step(UP);sprintf(t,"%s-gone",tag);at(R31,x,y,t);shot(t);}
static const struct mv TO_GATE[]={{64,10,11,1,0},{64,10,11,0,0},{64,29,39,31,"cross-into-route31"},{16,29,40,31,0},{16,29,41,31,0},{16,29,42,31,0},{16,29,43,31,0},{16,29,44,31,0},{16,29,45,31,0},{16,29,46,31,0},{16,29,47,31,"to-gate-007"},{16,29,48,31,0},{16,29,49,31,0},{16,29,50,31,0},{16,29,51,31,0},{64,29,51,30,0},{64,29,51,29,0},{64,29,51,28,0},{64,29,51,27,"to-gate-015"},{64,29,51,26,0},{64,29,51,25,0},{64,29,51,24,0},{64,29,51,23,0},{64,29,51,22,0},{64,29,51,21,0},{64,29,51,20,0},{64,29,51,19,"to-gate-023"},{64,29,51,18,0},{32,29,50,18,0},{32,29,49,18,0},{32,29,48,18,0},{32,29,47,18,0},{32,29,46,18,0},{32,29,45,18,0},{32,29,44,18,"to-gate-031"},{32,29,43,18,0},{32,29,42,18,0},{32,29,41,18,0},{32,29,40,18,0},{32,29,39,18,0},{32,29,38,18,0},{32,29,37,18,0},{32,29,36,18,"to-gate-039"},{32,29,35,18,0},{32,29,34,18,0},{32,29,33,18,0},{32,29,32,18,0},{32,29,31,18,0},{32,29,30,18,0},{32,29,29,18,0},{32,29,28,18,"to-gate-047"},{32,29,27,18,0},{32,29,26,18,0},{32,29,25,18,0},{32,29,24,18,0},{128,29,24,19,0},{128,29,24,21,0},{32,29,23,21,0},{32,29,22,21,"to-gate-055"},{32,29,21,21,0},{32,29,20,21,0},{32,29,19,21,0},{32,29,18,21,0},{32,29,17,21,0},{32,29,16,21,0},{32,29,15,21,0},{32,29,14,21,"to-gate-063"},{32,29,13,21,0},{32,29,12,21,0},{64,29,12,20,0},{32,29,11,20,0},{64,29,11,19,0},{64,29,11,18,0},{64,29,11,17,0},{32,29,10,17,"to-gate-071"},{32,29,9,17,0},{32,29,8,17,0},{64,29,8,16,0},{32,29,7,16,0},{32,29,6,16,0},{64,29,6,15,0},{64,29,6,14,0},{64,29,6,13,"to-gate-079"}};
static const struct mv TO_CAVE[]={{16,29,7,13,0},{16,29,8,13,0},{16,29,9,13,0},{16,29,10,13,0},{16,29,11,13,0},{16,29,12,13,0},{16,29,13,13,0},{16,29,14,13,"to-cave-007"},{16,29,15,13,0},{16,29,16,13,0},{16,29,17,13,0},{16,29,18,13,0},{16,29,19,13,0},{16,29,20,13,0},{16,29,22,13,0},{16,29,23,13,"to-cave-015"},{16,29,24,13,0},{16,29,25,13,0},{16,29,26,13,0},{16,29,27,13,0},{16,29,28,13,0},{16,29,29,13,0},{16,29,30,13,0},{128,29,30,14,"to-cave-023"},{128,29,30,15,0},{16,29,31,15,0},{16,29,32,15,0},{16,29,33,15,0},{128,29,33,16,0},{16,29,34,16,0},{16,29,35,16,0},{16,29,36,16,"to-cave-031"},{16,29,37,16,0},{16,29,38,16,0},{16,29,39,16,0},{16,29,40,16,0},{16,29,41,16,0},{16,29,42,16,0},{16,29,43,16,0},{16,29,44,16,"to-cave-039"},{16,29,45,16,0},{16,29,46,16,0},{16,29,47,16,0},{16,29,48,16,0},{16,29,49,16,0},{16,29,50,16,0},{16,29,51,16,0},{16,29,52,16,"to-cave-047"},{16,29,53,16,0},{64,29,53,15,0},{64,29,53,14,"to-cave-050"}};
static const struct mv TO_R30[]={{32,29,52,14,0},{128,29,52,15,0},{32,29,51,15,0},{128,29,51,16,0},{128,29,51,17,0},{128,29,51,18,0},{128,29,51,19,0},{128,29,51,20,0},{128,29,51,21,0},{128,29,51,22,0},{128,29,51,23,0},{128,29,51,24,0},{128,29,51,25,0},{128,29,51,26,0},{32,29,50,26,0},{32,29,49,26,"to-seam-015"},{32,29,48,26,0},{32,29,47,26,0},{32,29,46,26,0},{32,29,45,26,0},{32,29,44,26,0},{32,29,43,26,0},{32,29,42,26,0},{32,29,41,26,0},{32,29,40,26,0},{32,29,39,26,0},{128,29,39,27,0},{128,29,39,28,0},{128,29,39,29,0},{128,29,39,30,0},{128,29,39,31,"to-seam-030"},{128,10,11,0,"cross-back-into-route30"}};
static const struct mv TOUR[]={{32,29,38,31,0},{64,29,38,30,0},{64,29,38,29,0},{64,29,38,28,0},{64,29,38,27,0},{64,29,38,26,0},{64,29,38,25,0},{64,29,38,24,0},{64,29,38,23,"area-38-23"},{16,29,39,23,0},{16,29,40,23,0},{128,29,40,24,0},{16,29,41,24,0},{16,29,42,24,0},{128,29,42,25,0},{128,29,42,26,0},{16,29,43,26,0},{16,29,44,26,0},{16,29,45,26,0},{16,29,46,26,0},{16,29,47,26,0},{16,29,48,26,0},{16,29,49,26,0},{16,29,50,26,0},{16,29,51,26,0},{64,29,51,25,0},{64,29,51,24,0},{64,29,51,23,0},{64,29,51,22,0},{64,29,51,21,0},{64,29,51,20,0},{64,29,51,19,0},{64,29,51,18,0},{32,29,50,18,0},{32,29,49,18,0},{32,29,48,18,0},{32,29,47,18,0},{32,29,46,18,0},{32,29,45,18,0},{32,29,44,18,0},{32,29,43,18,0},{32,29,42,18,0},{32,29,41,18,0},{32,29,40,18,0},{32,29,39,18,0},{32,29,38,18,0},{32,29,37,18,0},{32,29,36,18,0},{32,29,35,18,0},{32,29,34,18,0},{32,29,33,18,0},{128,29,33,19,"area-33-19"},{32,29,32,19,0},{32,29,31,19,0},{32,29,30,19,0},{64,29,30,18,0},{64,29,30,17,0},{64,29,30,16,0},{64,29,30,15,0},{64,29,30,14,0},{64,29,30,13,"area-30-13"},{32,29,29,13,0},{32,29,28,13,0},{32,29,27,13,0},{32,29,26,13,0},{32,29,25,13,0},{32,29,24,13,0},{32,29,23,13,0},{128,29,23,14,0},{128,29,23,15,0},{128,29,23,16,0},{128,29,23,17,"area-23-17"},{16,29,24,17,0},{16,29,25,17,0},{16,29,26,17,0},{128,29,26,18,0},{128,29,26,19,0},{128,29,26,21,0},{128,29,26,22,"area-26-22"},{16,29,27,22,0},{16,29,28,22,0},{16,29,29,22,0},{16,29,30,22,0},{128,29,30,23,0},{128,29,30,24,0},{128,29,30,25,0},{128,29,30,26,"area-30-26"},{32,29,29,26,0},{32,29,28,26,0},{64,29,28,25,0},{64,29,28,24,0},{32,29,27,24,0},{32,29,26,24,0},{32,29,25,24,0},{32,29,24,24,0},{32,29,23,24,0},{32,29,22,24,0},{32,29,21,24,0},{32,29,20,24,0},{32,29,19,24,"area-19-24"},{32,29,18,24,0},{32,29,17,24,0},{32,29,16,24,0},{64,29,16,23,0},{64,29,16,22,0},{32,29,15,22,0},{32,29,14,22,0},{32,29,13,22,0},{32,29,12,22,0},{64,29,12,21,0},{64,29,12,20,0},{32,29,11,20,0},{32,29,10,20,0},{32,29,9,20,"area-9-20"},{16,29,10,20,0},{16,29,11,20,0},{64,29,11,19,0},{64,29,11,18,0},{64,29,11,17,0},{32,29,10,17,0},{32,29,9,17,0},{32,29,8,17,0},{64,29,8,16,0},{32,29,7,16,0},{64,29,7,15,0},{64,29,7,14,0},{64,29,7,13,0},{64,29,7,12,0},{32,29,6,12,0},{64,29,6,11,0},{64,29,6,10,"area-6-10"},{16,29,7,10,0},{16,29,8,10,0},{16,29,9,10,0},{16,29,10,10,0},{16,29,11,10,0},{16,29,12,10,0},{16,29,13,10,0},{16,29,14,10,0},{16,29,15,10,0},{16,29,16,10,0},{128,29,16,11,0},{128,29,16,12,0},{128,29,16,13,"area-16-13"},{16,29,17,13,0},{16,29,18,13,0},{16,29,19,13,0},{16,29,20,13,0},{16,29,22,13,0},{16,29,23,13,0},{16,29,24,13,0},{16,29,25,13,0},{16,29,26,13,0},{16,29,27,13,0},{16,29,28,13,0},{16,29,29,13,0},{16,29,30,13,0},{128,29,30,14,0},{128,29,30,15,0},{16,29,31,15,0},{16,29,32,15,0},{16,29,33,15,0},{128,29,33,16,0},{16,29,34,16,0},{16,29,35,16,0},{16,29,36,16,0},{16,29,37,16,0},{16,29,38,16,0},{16,29,39,16,0},{16,29,40,16,0},{16,29,41,16,0},{16,29,42,16,0},{128,29,42,17,"area-42-17"},{16,29,43,17,0},{16,29,44,17,0},{16,29,45,17,0},{16,29,46,17,0},{16,29,47,17,0},{64,29,47,16,0},{64,29,47,15,0},{64,29,47,14,0},{64,29,47,13,0},{64,29,47,12,"area-47-12"},{128,29,47,13,0},{128,29,47,14,0},{16,29,48,14,0},{16,29,49,14,0},{16,29,50,14,0},{128,29,50,15,0},{16,29,51,15,0},{16,29,52,15,0},{16,29,53,15,0},{16,29,54,15,0},{16,29,55,15,0},{64,29,55,14,"area-55-14"},{32,29,54,14,0},{32,29,53,14,0},{32,29,52,14,0},{128,29,52,15,0},{32,29,51,15,0},{128,29,51,16,0},{128,29,51,17,0},{128,29,51,18,0},{128,29,51,19,0},{128,29,51,20,0},{128,29,51,21,0},{128,29,51,22,0},{128,29,51,23,0},{128,29,51,24,0},{128,29,51,25,0},{128,29,51,26,0},{32,29,50,26,"area-50-26"}};

int main(int argc,char**argv){
 if(argc!=5){fprintf(stderr,"runtime ROM SYMBOLS OUT write|read|menu\n");return 2;}
 out=argv[3];FILE*f=fopen(argv[2],"r");if(!f)return 3;while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;mCoreConfigInit(&c->config,"route31-catalog");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 char flash[2048];snprintf(flash,sizeof(flash),"%s/route31.sav",argv[3]);
 if(!strcmp(argv[4],"read")||!strcmp(argv[4],"menu")){unsigned char data[131072];f=fopen(flash,"rb");if(!f||fread(data,1,sizeof(data),f)!=sizeof(data))return 6;fclose(f);if(!c->savedataRestore(c,data,sizeof(data),false))return 7;}
 c->rtc.override=RTC_FIXED;c->rtc.value=1789315200000LL;
 c->reset(c);frames(600,0);
 if(!strcmp(argv[4],"menu")){
  frames(1,8);frames(180,0);frames(1,A);frames(300,0);frames(1,A);frames(180,0);shot("continue-menu");frames(1,A);frames(300,0);shot("title-continue");at(R31,SAVE_X,SAVE_Y,"title-continue");
 }else if(!strcmp(argv[4],"read")){
  unsigned s=call("LoadGameSave",0);need(s==1,"load-status");call("MapProof_Resume",0);frames(240,0);shot("cold-reload");at(R31,SAVE_X,SAVE_Y,"cold-reload");
  need(call("FlagGet",FLAG_POKE_BALL)==1&&call("FlagGet",FLAG_POTION)==1,"item-flags-survive-save");
 }else{
  call("MapProof_Boot",0);frames(240,0);observe("new-game");
  {static const unsigned char nm[]={0xCA,0xC6,0xBB,0xD3,0xBF,0xCC,0xFF,0xFF};unsigned sb2=c->busRead32(c,sym("gSaveBlock2Ptr"));for(int i=0;i<8;i++)c->busWrite8(c,sb2+i,nm[i]);}
  need(call("CalculatePlayerPartyCount",0)==0,"empty-party");
  // Route 30's north end -> Route 31 -> the gatehouse doorway on foot, every step checked; west warps.
  go(R30,START_X,START_Y);at(R30,START_X,START_Y,"start-route30");shot("route30-start");
  walk(TO_GATE,sizeof(TO_GATE)/sizeof(TO_GATE[0]));
  warp_into(LEFT,GATE,"gatehouse-warp");
  // From the gatehouse's return warp (doorway cell) to Dark Cave's opening on foot; north warps.
  go(R31,DOOR_X,DOOR_Y);at(R31,DOOR_X,DOOR_Y,"doorway");
  walk(TO_CAVE,sizeof(TO_CAVE)/sizeof(TO_CAVE[0]));
  warp_into(UP,CAVE,"dark-cave-warp");
  // Back across the seam into Route 30.
  go(R31,BACK_X,BACK_Y);at(R31,BACK_X,BACK_Y,"seam-start");
  walk(TO_R30,sizeof(TO_R30)/sizeof(TO_R30[0]));
  printf("{\"walked\":\"Route30-Route31-gate, gate warp, doorway-Dark Cave, cave warp, Route31-Route30\"}\n");
  go(R31,TOUR_X,TOUR_Y);at(R31,TOUR_X,TOUR_Y,"tour-start");
  walk(TOUR,sizeof(TOUR)/sizeof(TOUR[0]));
  ball(45,13,FLAG_POTION,"item-ball-45-13");ball(33,25,FLAG_POKE_BALL,"item-ball-33-25");
  printf("{\"items\":\"both balls picked up and gone\"}\n");
  ledge(20,15,16,1,0,"ledge_east-21-15");ledge(9,17,128,0,1,"ledge_south-9-18");ledge(17,17,128,0,1,"ledge_south-17-18");ledge(25,19,128,0,1,"ledge_south-25-20");ledge(31,19,128,0,1,"ledge_south-31-20");
  blocked(40,22,64,"cut-tree-40-21");shot("cut-tree-40-21");blocked(21,13,64,"cut-tree-21-12");shot("cut-tree-21-12");blocked(10,13,64,"sign-10-12");shot("sign-10-12");blocked(51,15,64,"sign-51-14");shot("sign-51-14");blocked(25,12,16,"pond-edge");shot("pond-edge");blocked(6,11,32,"gatehouse-wall");shot("gatehouse-wall");blocked(31,26,16,"rock");shot("rock");blocked(52,14,64,"cave-rock");shot("cave-rock");
  go(R31,GRASS_X,GRASS_Y);for(int i=0;i<GRASS_N;i++){step(GRASS_KEY);need(overworld()&&!locked(),"grass-no-battle");}shot("tall-grass");
  printf("{\"tall_grass_steps_without_battle\":%d}\n",GRASS_N);
  read_sign(10,12,"read-sign-10-12");read_sign(51,14,"read-sign-51-14");
  go(R31,SAVE_X,SAVE_Y);at(R31,SAVE_X,SAVE_Y,"save-spot");shot("save-spot");
  unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
 }
 c->deinit(c);return 0;
}
