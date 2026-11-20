
#define main unused_map_qualification_main
#include "/home/user/pokemon-apocrypha/tools/gba/maps/runtime.c"
#undef main
#define RIGHT 16
#define VIOLET 43
#define VIOLET_NUM 43
#define EAST_NUM 33
#define WEST_NUM 45
#define LEFT 32
#define UP 64
#define DOWN 128
static const char *out;
static void shot(const char*t){screenshot(out,t);call("MapProof_ReadState",0);unsigned a=sym("gMapProofState");printf("{\"shot\":\"%s\",\"map\":%u,\"x\":%u,\"y\":%u}\n",t,c->busRead32(c,a+8),c->busRead32(c,a+12),c->busRead32(c,a+16));fflush(stdout);}
static void go(unsigned map,unsigned x,unsigned y){call("MapProof_Enter",map|(x<<8)|(y<<16));frames(360,0);}
static void need(int ok,const char*tag){if(!ok){fprintf(stderr,"FAILED %s (map %u at %u,%u)\n",tag,state[2],state[3],state[4]);shot(tag);exit(40);}}
static void at(unsigned map,unsigned x,unsigned y,const char*tag){observe(tag);need(state[2]==map&&state[3]==x&&state[4]==y,tag);}
static void pos(unsigned*m,unsigned*x,unsigned*y){call("MapProof_ReadState",0);unsigned a=sym("gMapProofState");*m=c->busRead32(c,a+8);*x=c->busRead32(c,a+12);*y=c->busRead32(c,a+16);}
static void step(unsigned key){unsigned m0,x0,y0,m1,x1,y1;pos(&m0,&x0,&y0);int moved=0;for(int t=0;t<32&&!moved;t++){frames(2,key);pos(&m1,&x1,&y1);moved=(m1!=m0||x1!=x0||y1!=y0);}frames(moved?40:8,0);frames(16,0);}
static void door(unsigned x,unsigned y,const char*name){char t[64];go(VIOLET,x,y+1);at(VIOLET_NUM,x,y+1,name);
 frames(2,UP);for(int i=0;i<24;i++){frames(4,i<8?UP:0);sprintf(t,"door-%s-%d",name,i);screenshot(out,t);}frames(300,0);observe(name);
 need(state[2]!=VIOLET_NUM,name);sprintf(t,"inside-%s",name);shot(t);
 step(DOWN);frames(300,0);observe(name);need(state[2]==VIOLET_NUM&&state[3]==x&&state[4]==y+1,name);sprintf(t,"out-%s",name);shot(t);
 printf("{\"door\":\"%s\",\"ok\":1}\n",name);fflush(stdout);}
static void walk(unsigned key,int n,const char*name){char t[64];for(int i=0;i<n;i++){step(key);sprintf(t,"%s-%d",name,i);shot(t);}}
int main(int argc,char**argv){
 if(argc!=4){fprintf(stderr,"runtime ROM SYMBOLS OUT\n");return 2;}
 out=argv[3];FILE*f=fopen(argv[2],"r");if(!f)return 3;while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;mCoreConfigInit(&c->config,"violet-city");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 c->rtc.override=RTC_FIXED;c->rtc.value=1789315200000LL;
 c->reset(c);frames(600,0);
 call("MapProof_Boot",0);frames(240,0);observe("new-game");
 // the east gate and back
 go(VIOLET,72,57);at(VIOLET_NUM,72,57,"east-front");shot("east-front");
 step(RIGHT);step(RIGHT);frames(240,0);observe("east-gate");need(state[2]==EAST_NUM,"into-east-gate");shot("east-gate-inside");
 go(VIOLET,72,58);at(VIOLET_NUM,72,58,"east-front-lower");
 step(RIGHT);step(RIGHT);frames(240,0);observe("east-gate-lower");need(state[2]==EAST_NUM,"into-east-gate-lower");
 // the gates' blocked cells: the east gate's roof, the tree seal above the west gate
 go(VIOLET,72,55);step(RIGHT);at(VIOLET_NUM,72,55,"east-gate-wall-blocks");
 go(VIOLET,7,25);step(LEFT);at(VIOLET_NUM,7,25,"west-gate-wall-blocks");
 // the west gate and back
 go(VIOLET,6,30);at(VIOLET_NUM,6,30,"west-front");shot("west-front");
 step(LEFT);step(LEFT);frames(240,0);observe("west-gate");need(state[2]==WEST_NUM,"into-west-gate");shot("west-gate-inside");
 // the north road, both bridges and the landing, south to the main street
 go(VIOLET,39,13);at(VIOLET_NUM,39,13,"north-road");shot("north-road");
 walk(DOWN,30,"south");
 observe("main-street");need(state[2]==VIOLET_NUM&&state[3]==39&&state[4]==43,"walked-south-to-the-main-street");
 printf("{\"walked\":\"north-road-to-main-street\"}\n");
 // the lake blocks on foot
 go(VIOLET,30,15);step(DOWN);at(VIOLET_NUM,30,15,"lake-blocks");shot("lake-blocks");
 // the hall: its door blocks from the spur, the lawn its old west wing gave back is open
 go(VIOLET,58,43);step(UP);at(VIOLET_NUM,58,43,"hall-blocks");shot("hall-front");
 go(VIOLET,54,33);step(RIGHT);step(RIGHT);at(VIOLET_NUM,56,33,"back-path-open");shot("back-path");
 go(VIOLET,47,40);step(RIGHT);step(RIGHT);at(VIOLET_NUM,49,40,"old-wing-open");shot("old-wing");
 // every door: it opens, the interior loads, walking out puts the player back below the door
 door(39,12,"SproutTower");
 door(57,42,"University");
 door(31,41,"LectureHall");
 door(21,40,"Mart");
 door(49,55,"PokemonCenter");
 door(11,26,"House1");
 door(10,37,"House2");
 door(26,55,"House3");
 door(36,60,"House4");
 door(56,63,"House5");
 c->deinit(c);return 0;
}
