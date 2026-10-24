
#define main unused_map_qualification_main
#include "/home/user/pokemon-apocrypha/tools/gba/maps/runtime.c"
#undef main
#define START_X 76
#define START_Y 18
#define TOUR_X 2
#define TOUR_Y 18
#define GRASS_X 69
#define GRASS_Y 6
#define WEST_SIGN_X 9
#define WEST_SIGN_Y 16
#define EAST_SIGN_X 90
#define EAST_SIGN_Y 16
#define SAVE_X 65
#define SAVE_Y 30
#define HIDDEN_FLAG 612
#define TOWN 0
#define R29 9
#define NEWBARK 28
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
static void pos(unsigned*m,unsigned*x,unsigned*y){call("MapProof_ReadState",0);unsigned a=sym("gMapProofState");*m=c->busRead32(c,a+8);*x=c->busRead32(c,a+12);*y=c->busRead32(c,a+16);}
static void step(unsigned key){unsigned m0,x0,y0,m1,x1,y1;pos(&m0,&x0,&y0);int moved=0;for(int t=0;t<32&&!moved;t++){frames(2,key);pos(&m1,&x1,&y1);moved=(m1!=m0||x1!=x0||y1!=y0);}frames(moved?40:8,0);frames(16,0);}
static void tap(unsigned key){frames(2,key);frames(12,0);}
static int locked(void){return call("ArePlayerFieldControlsLocked",0);}
static int overworld(void){unsigned cb=c->busRead32(c,sym("gMain")+4);return (cb&~1u)==(sym("CB2_Overworld")&~1u);}
static void close_dialog(void){for(int i=0;i<40&&locked();i++){frames(1,B);frames(40,0);}need(!locked(),"dialogue-closes");}
struct mv{unsigned char key;unsigned short map,x,y;const char*tag;};
static void walk(const struct mv*m,int n){for(int i=0;i<n;i++){step(m[i].key);char t[96];sprintf(t,"walk-%s",m[i].tag?m[i].tag:"step");at(m[i].map,m[i].x,m[i].y,t);need(overworld()&&!locked(),"walk-no-interruption");if(m[i].tag)shot(m[i].tag);}}
static void ledge(unsigned x,unsigned y,unsigned key,int dx,int dy,const char*tag){char t[64];go(R29,x,y);step(key);sprintf(t,"%s-jump",tag);at(R29,x+2*dx,y+2*dy,t);unsigned back=key==DOWN?UP:key==UP?DOWN:key==LEFT?RIGHT:LEFT;step(back);sprintf(t,"%s-no-climb",tag);at(R29,x+2*dx,y+2*dy,t);}
static void blocked(unsigned x,unsigned y,unsigned key,const char*tag){go(R29,x,y);step(key);at(R29,x,y,tag);}
static void read_sign(unsigned x,unsigned y,const char*tag){go(R29,x,y+1);tap(UP);frames(1,A);frames(120,0);need(locked(),tag);shot(tag);close_dialog();}
static const struct mv ROUTE_OUT[]={{16,0,77,18,0},{16,0,78,18,0},{16,0,79,18,0},{16,9,0,18,"cross-into-route29"},{16,9,1,18,0},{16,9,2,18,0},{16,9,3,18,0},{16,9,4,18,0},{16,9,5,18,0},{16,9,6,18,0},{16,9,7,18,0},{16,9,8,18,"route-007"},{16,9,9,18,0},{16,9,10,18,0},{16,9,11,18,0},{16,9,12,18,0},{16,9,13,18,0},{16,9,14,18,0},{16,9,15,18,0},{128,9,15,19,"route-015"},{128,9,15,20,0},{128,9,15,21,0},{16,9,16,21,0},{16,9,17,21,0},{16,9,18,21,0},{16,9,19,21,0},{16,9,20,21,0},{16,9,21,21,"route-023"},{16,9,22,21,0},{16,9,23,21,0},{16,9,24,21,0},{16,9,25,21,0},{16,9,26,21,0},{16,9,27,21,0},{16,9,28,21,0},{16,9,29,21,"route-031"},{16,9,30,21,0},{16,9,31,21,0},{16,9,32,21,0},{16,9,33,21,0},{16,9,34,21,0},{16,9,35,21,0},{16,9,36,21,0},{16,9,37,21,"route-039"},{16,9,38,21,0},{128,9,38,22,0},{128,9,38,23,0},{128,9,38,24,0},{128,9,38,25,0},{128,9,38,27,0},{16,9,39,27,0},{16,9,40,27,"route-047"},{16,9,41,27,0},{16,9,42,27,0},{16,9,43,27,0},{16,9,44,27,0},{16,9,45,27,0},{16,9,46,27,0},{16,9,47,27,0},{16,9,48,27,"route-055"},{16,9,49,27,0},{16,9,50,27,0},{16,9,51,27,0},{16,9,52,27,0},{16,9,53,27,0},{16,9,54,27,0},{16,9,55,27,0},{16,9,56,27,"route-063"},{16,9,57,27,0},{16,9,58,27,0},{16,9,59,27,0},{16,9,60,27,0},{16,9,61,27,0},{64,9,61,26,0},{64,9,61,25,0},{16,9,62,25,"route-071"},{16,9,63,25,0},{16,9,64,25,0},{16,9,65,25,0},{64,9,65,24,0},{64,9,65,23,0},{16,9,66,23,0},{16,9,67,23,0},{16,9,68,23,"route-079"},{16,9,69,23,0},{16,9,70,23,0},{16,9,71,23,0},{16,9,72,23,0},{16,9,73,23,0},{16,9,74,23,0},{16,9,75,23,0},{16,9,76,23,"route-087"},{16,9,77,23,0},{16,9,78,23,0},{16,9,80,23,0},{16,9,81,23,0},{16,9,82,23,0},{16,9,83,23,0},{16,9,84,23,0},{16,9,85,23,"route-095"},{16,9,86,23,0},{16,9,87,23,0},{16,9,88,23,0},{16,9,89,23,0},{16,9,90,23,0},{16,9,91,23,0},{16,9,92,23,0},{16,9,93,23,"route-103"},{64,9,93,22,0},{64,9,93,21,0},{16,9,94,21,0},{16,9,95,21,0},{16,9,96,21,0},{16,9,97,21,0},{16,9,98,21,0},{16,9,99,21,"route-111"},{16,9,100,21,0},{16,9,101,21,0},{64,9,101,20,0},{64,9,101,19,0},{64,9,101,18,"route-116"},{16,28,0,12,"cross-into-new-bark"},{16,28,1,12,0}};
static const struct mv ROUTE_BACK[]={{32,28,0,12,0},{32,9,101,18,"cross-back-into-route29"},{32,9,100,18,0},{32,9,99,18,0},{32,9,98,18,0},{32,9,97,18,0},{32,9,96,18,0},{32,9,95,18,0},{32,9,94,18,0},{32,9,93,18,0},{32,9,92,18,0},{32,9,91,18,0},{32,9,90,18,0},{32,9,89,18,0},{32,9,88,18,0},{32,9,87,18,0},{32,9,86,18,0},{32,9,85,18,"back-015"},{32,9,84,18,0},{32,9,83,18,0},{32,9,82,18,0},{32,9,81,18,0},{32,9,80,18,0},{128,9,80,19,0},{128,9,80,20,0},{128,9,80,21,0},{128,9,80,22,0},{128,9,80,23,0},{128,9,80,24,0},{128,9,80,25,0},{128,9,80,26,0},{128,9,80,27,0},{32,9,79,27,0},{32,9,78,27,"back-031"},{32,9,77,27,0},{32,9,76,27,0},{32,9,75,27,0},{32,9,74,27,0},{32,9,73,27,0},{32,9,72,27,0},{32,9,71,27,0},{32,9,70,27,0},{128,9,70,28,0},{128,9,70,29,0},{128,9,70,30,0},{32,9,69,30,0},{32,9,68,30,0},{32,9,67,30,0},{32,9,66,30,0},{32,9,65,30,"back-047"},{32,9,64,30,0},{32,9,63,30,0},{32,9,62,30,0},{32,9,61,30,0},{64,9,61,29,0},{64,9,61,28,0},{64,9,61,27,0},{64,9,61,26,0},{64,9,61,25,0},{16,9,62,25,0},{16,9,63,25,0},{16,9,64,25,0},{16,9,65,25,0},{64,9,65,24,0},{64,9,65,23,0},{16,9,66,23,"back-063"},{64,9,66,22,0},{64,9,66,21,0},{64,9,66,20,0},{64,9,66,19,0},{64,9,66,18,0},{32,9,65,18,0},{32,9,64,18,0},{32,9,63,18,0},{32,9,62,18,0},{32,9,61,18,0},{32,9,60,18,0},{32,9,59,18,0},{32,9,58,18,0},{32,9,57,18,0},{32,9,56,18,0},{32,9,55,18,"back-079"},{32,9,54,18,0},{32,9,53,18,0},{32,9,52,18,0},{32,9,51,18,0},{32,9,50,18,0},{32,9,49,18,0},{32,9,48,18,0},{32,9,47,18,0},{32,9,46,18,0},{64,9,46,17,0},{64,9,46,16,0},{32,9,45,16,0},{32,9,44,16,0},{32,9,43,16,0},{32,9,42,16,0},{64,9,42,15,"back-095"},{64,9,42,14,0},{32,9,41,14,0},{32,9,40,14,0},{32,9,39,14,0},{32,9,38,14,0},{32,9,37,14,0},{32,9,36,14,0},{32,9,35,14,0},{32,9,34,14,0},{32,9,33,14,0},{32,9,32,14,0},{128,9,32,15,0},{128,9,32,16,0},{32,9,31,16,0},{32,9,30,16,0},{32,9,29,16,"back-111"},{32,9,28,16,0},{32,9,27,16,0},{32,9,26,16,0},{32,9,25,16,0},{32,9,24,16,0},{32,9,23,16,0},{32,9,22,16,0},{32,9,21,16,0},{32,9,20,16,0},{32,9,19,16,0},{32,9,18,16,0},{128,9,18,17,0},{32,9,17,17,0},{32,9,15,17,0},{32,9,14,17,0},{32,9,13,17,"back-127"},{32,9,12,17,0},{32,9,11,17,0},{32,9,10,17,0},{32,9,9,17,0},{32,9,8,17,0},{32,9,7,17,0},{32,9,6,17,0},{32,9,5,17,0},{32,9,4,17,0},{32,9,3,17,0},{32,9,2,17,0},{32,9,1,17,0},{32,9,0,17,0},{128,9,0,18,0},{32,0,79,18,"cross-back-into-cherrygrove"}};
static const struct mv TOUR[]={{16,9,3,18,0},{16,9,4,18,0},{16,9,5,18,0},{16,9,6,18,0},{16,9,7,18,0},{16,9,8,18,0},{16,9,9,18,0},{16,9,10,18,0},{16,9,11,18,0},{16,9,12,18,0},{16,9,13,18,0},{16,9,14,18,0},{16,9,15,18,0},{128,9,15,19,0},{128,9,15,20,0},{128,9,15,21,0},{16,9,16,21,0},{16,9,17,21,0},{16,9,18,21,0},{16,9,19,21,0},{16,9,20,21,0},{16,9,21,21,0},{16,9,22,21,0},{16,9,23,21,0},{16,9,24,21,0},{64,9,24,20,0},{64,9,24,19,0},{64,9,24,18,0},{64,9,24,17,0},{64,9,24,16,0},{64,9,24,15,0},{64,9,24,14,0},{64,9,24,13,0},{64,9,24,12,"upper-lawn"},{16,9,25,12,0},{16,9,26,12,0},{16,9,27,12,0},{16,9,28,12,0},{16,9,29,12,0},{16,9,30,12,0},{16,9,32,12,0},{16,9,33,12,0},{64,9,33,11,0},{64,9,33,10,"north-grass"},{16,9,34,10,0},{16,9,35,10,0},{16,9,36,10,0},{16,9,37,10,0},{16,9,38,10,0},{16,9,39,10,0},{16,9,40,10,0},{16,9,41,10,0},{128,9,41,11,0},{16,9,42,11,0},{16,9,43,11,0},{128,9,43,12,0},{128,9,43,13,0},{16,9,44,13,0},{16,9,45,13,0},{16,9,46,13,0},{16,9,47,13,0},{16,9,48,13,0},{16,9,49,13,0},{16,9,50,13,0},{16,9,51,13,0},{16,9,52,13,0},{16,9,53,13,0},{16,9,54,13,0},{64,9,54,12,0},{64,9,54,11,0},{64,9,54,10,0},{64,9,54,9,"gatehouse-front"},{16,9,55,9,0},{16,9,56,9,0},{16,9,57,9,0},{128,9,57,10,0},{128,9,57,11,0},{128,9,57,12,0},{128,9,57,13,0},{128,9,57,14,0},{128,9,57,15,0},{16,9,58,15,0},{16,9,59,15,0},{16,9,60,15,0},{16,9,61,15,0},{16,9,62,15,0},{16,9,63,15,0},{16,9,64,15,0},{16,9,65,15,0},{16,9,66,15,0},{16,9,67,15,0},{64,9,67,14,0},{64,9,67,13,0},{64,9,67,12,0},{16,9,68,12,0},{16,9,69,12,0},{16,9,70,12,0},{16,9,71,12,0},{16,9,72,12,0},{64,9,72,11,0},{64,9,72,10,0},{64,9,72,9,0},{64,9,72,8,0},{64,9,72,7,0},{64,9,72,6,"north-east-grass"},{16,9,73,6,0},{16,9,74,6,0},{16,9,75,6,0},{128,9,75,7,0},{128,9,75,8,0},{128,9,75,9,0},{128,9,75,10,0},{128,9,75,11,0},{128,9,75,12,0},{128,9,75,13,0},{128,9,75,14,0},{128,9,75,15,0},{128,9,75,16,0},{128,9,75,17,0},{16,9,76,17,0},{16,9,77,17,0},{16,9,78,17,0},{16,9,80,17,0},{16,9,81,17,0},{16,9,82,17,0},{16,9,83,17,0},{16,9,84,17,0},{16,9,85,17,0},{16,9,86,17,0},{16,9,87,17,0},{16,9,88,17,0},{64,9,88,16,0},{64,9,88,15,"east-sign-lawn"},{32,9,87,15,0},{32,9,86,15,0},{32,9,85,15,0},{32,9,84,15,0},{128,9,84,16,0},{128,9,84,17,0},{128,9,84,18,0},{128,9,84,19,0},{128,9,84,20,0},{128,9,84,21,0},{128,9,84,22,"east-grass"},{32,9,83,22,0},{32,9,82,22,0},{32,9,81,22,0},{32,9,80,22,0},{128,9,80,23,0},{128,9,80,24,0},{128,9,80,25,0},{128,9,80,26,0},{128,9,80,27,0},{32,9,79,27,0},{32,9,78,27,0},{32,9,77,27,0},{32,9,76,27,0},{32,9,75,27,0},{32,9,74,27,0},{32,9,73,27,0},{32,9,72,27,0},{32,9,71,27,0},{32,9,70,27,"south-east-pocket"},{128,9,70,28,0},{128,9,70,29,0},{128,9,70,30,0},{32,9,69,30,0},{32,9,68,30,0},{32,9,67,30,0},{32,9,66,30,0},{32,9,65,30,0},{32,9,64,30,0},{32,9,63,30,0},{32,9,62,30,0},{32,9,61,30,0},{32,9,60,30,0},{64,9,60,29,0},{64,9,60,28,0},{64,9,60,27,0},{64,9,60,26,0},{64,9,60,25,0},{32,9,59,25,0},{32,9,58,25,0},{32,9,57,25,0},{32,9,56,25,0},{32,9,54,25,0},{32,9,53,25,0},{32,9,52,25,0},{64,9,52,24,"centre"},{32,9,51,24,0},{32,9,50,24,0},{128,9,50,25,0},{32,9,49,25,0},{32,9,48,25,0},{32,9,47,25,0},{128,9,47,26,0},{128,9,47,27,0},{32,9,46,27,0},{32,9,45,27,0},{32,9,44,27,0},{32,9,43,27,0},{32,9,42,27,0},{32,9,41,27,0},{32,9,40,27,"south-lawn"},{16,9,41,27,0},{16,9,42,27,0},{16,9,43,27,0},{16,9,44,27,0},{16,9,45,27,0},{16,9,46,27,0},{16,9,47,27,0},{16,9,48,27,0},{16,9,49,27,0},{16,9,50,27,0},{16,9,51,27,0},{16,9,52,27,0},{16,9,53,27,0},{16,9,54,27,0},{16,9,55,27,0},{16,9,56,27,0},{16,9,57,27,0},{16,9,58,27,0},{16,9,59,27,0},{16,9,60,27,0},{128,9,60,28,0},{128,9,60,29,0},{128,9,60,30,"lookout"},{16,9,61,30,0},{16,9,62,30,0},{16,9,63,30,0},{16,9,64,30,0},{16,9,65,30,"by-the-potion"}};

int main(int argc,char**argv){
 if(argc!=5){fprintf(stderr,"runtime ROM SYMBOLS OUT write|read|menu\n");return 2;}
 out=argv[3];FILE*f=fopen(argv[2],"r");if(!f)return 3;while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;mCoreConfigInit(&c->config,"route29-catalog");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 char flash[2048];snprintf(flash,sizeof(flash),"%s/route29.sav",argv[3]);
 if(!strcmp(argv[4],"read")||!strcmp(argv[4],"menu")){unsigned char data[131072];f=fopen(flash,"rb");if(!f||fread(data,1,sizeof(data),f)!=sizeof(data))return 6;fclose(f);if(!c->savedataRestore(c,data,sizeof(data),false))return 7;}
 c->rtc.override=RTC_FIXED;c->rtc.value=1789315200000LL;
 c->reset(c);frames(600,0);
 if(!strcmp(argv[4],"menu")){
  frames(1,8);frames(180,0);frames(1,A);frames(300,0);frames(1,A);frames(180,0);shot("continue-menu");frames(1,A);frames(300,0);shot("title-continue");at(R29,SAVE_X,SAVE_Y,"title-continue");
 }else if(!strcmp(argv[4],"read")){
  unsigned s=call("LoadGameSave",0);need(s==1,"load-status");call("MapProof_Resume",0);frames(240,0);shot("cold-reload");at(R29,SAVE_X,SAVE_Y,"cold-reload");
  need(call("FlagGet",HIDDEN_FLAG)==1,"potion-flag-survives-save");
 }else{
  call("MapProof_Boot",0);frames(240,0);observe("new-game");
  {static const unsigned char nm[]={0xCA,0xC6,0xBB,0xD3,0xBF,0xCC,0xFF,0xFF};unsigned sb2=c->busRead32(c,sym("gSaveBlock2Ptr"));for(int i=0;i<8;i++)c->busWrite8(c,sb2+i,nm[i]);}
  need(call("CalculatePlayerPartyCount",0)==0,"empty-party");
  // Cherrygrove -> Route 29 -> New Bark on foot, every step checked; then back to Cherrygrove.
  go(TOWN,START_X,START_Y);at(TOWN,START_X,START_Y,"start-cherrygrove");shot("cherrygrove-start");
  walk(ROUTE_OUT,sizeof(ROUTE_OUT)/sizeof(ROUTE_OUT[0]));
  walk(ROUTE_BACK,sizeof(ROUTE_BACK)/sizeof(ROUTE_BACK[0]));
  printf("{\"walked\":\"Cherrygrove-Route29-NewBark-and-back\",\"steps\":%d}\n",(int)(sizeof(ROUTE_OUT)/sizeof(ROUTE_OUT[0])+sizeof(ROUTE_BACK)/sizeof(ROUTE_BACK[0])));
  // A walking tour into every area: no warps between targets.
  go(R29,TOUR_X,TOUR_Y);at(R29,TOUR_X,TOUR_Y,"tour-start");
  walk(TOUR,sizeof(TOUR)/sizeof(TOUR[0]));
  // The hidden Potion, reached on foot by the tour: face it and search.
  go(R29,65,30);tap(RIGHT);{unsigned m,x,y;pos(&m,&x,&y);if(x!=65){step(LEFT);tap(RIGHT);}}at(R29,65,30,"facing-potion");
  need(call("FlagGet",HIDDEN_FLAG)==0,"potion-flag-clear");
  frames(1,A);frames(150,0);need(locked(),"potion-found");shot("potion-found");close_dialog();
  need(call("FlagGet",HIDDEN_FLAG)==1,"potion-flag-set");
  frames(1,A);frames(90,0);int again=locked();if(again)close_dialog();need(!again,"potion-only-once");
  printf("{\"hidden_potion\":\"found once\",\"flag\":%u}\n",HIDDEN_FLAG);
  ledge(30,12,16,1,0,"ledge_east-31-12");ledge(20,14,128,0,1,"ledge_south-20-15");ledge(28,14,128,0,1,"ledge_south-28-15");ledge(17,18,32,-1,0,"ledge_west-16-18");ledge(78,21,16,1,0,"ledge_east-79-21");ledge(19,19,128,0,1,"ledge_south-19-20");ledge(29,19,128,0,1,"ledge_south-29-20");ledge(53,19,128,0,1,"ledge_south-53-20");ledge(56,23,32,-1,0,"ledge_west-55-23");ledge(36,25,128,0,1,"ledge_south-36-26");ledge(58,25,128,0,1,"ledge_south-58-26");ledge(64,25,128,0,1,"ledge_south-64-26");ledge(74,25,128,0,1,"ledge_south-74-26");
  blocked(54,9,64,"gatehouse-door-shut");shot("gatehouse-door-shut");blocked(47,25,64,"cut-tree-47-24");shot("cut-tree-47-24");blocked(57,21,64,"cut-tree-57-20");shot("cut-tree-57-20");blocked(90,17,64,"sign-90-16");shot("sign-90-16");blocked(9,17,64,"sign-9-16");shot("sign-9-16");
  go(R29,GRASS_X,GRASS_Y);for(int i=0;i<6;i++){step(RIGHT);need(overworld()&&!locked(),"grass-no-battle");}shot("tall-grass");
  printf("{\"tall_grass_steps_without_battle\":6}\n");
  read_sign(WEST_SIGN_X,WEST_SIGN_Y,"sign-west");read_sign(EAST_SIGN_X,EAST_SIGN_Y,"sign-east");
  go(R29,SAVE_X,SAVE_Y);at(R29,SAVE_X,SAVE_Y,"save-spot");shot("save-spot");
  unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
 }
 c->deinit(c);return 0;
}
