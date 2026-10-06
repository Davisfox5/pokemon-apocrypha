// Ordinary walking and button input from the post-handoff save to Chapter 1's
// northern departure. MapProof_ReadState observes position; it never warps.
#define main unused_map_runtime_main
#include "runtime.c"
#undef main

static void tap(unsigned key){frames(1,key);frames(28,0);}
static void pos(int *map,int *x,int *y)
{
    call("MapProof_ReadState",0);unsigned a=sym("gMapProofState");
    *map=c->busRead32(c,a+8);*x=c->busRead32(c,a+12);*y=c->busRead32(c,a+16);
}
static unsigned stage(void){return call("VarGet",0x40FD);}
static int locked(void){return call("ArePlayerFieldControlsLocked",0);}
static int actor(unsigned map,unsigned id,int *x,int *y,int *face)
{
    unsigned base=sym("gObjectEvents");
    for(int i=0;i<16;i++){
        unsigned a=base+i*0x24;
        if(!(c->busRead8(c,a)&1)||(c->busRead8(c,a+1)&32)
           ||c->busRead8(c,a+9)!=map||c->busRead8(c,a+10)!=80
           ||c->busRead8(c,a+8)!=id)continue;
        *x=(short)c->busRead16(c,a+16)-7;
        *y=(short)c->busRead16(c,a+18)-7;
        *face=c->busRead8(c,a+24)&15;
        return 1;
    }
    return 0;
}
static void require_actor(unsigned map,unsigned id,int x,int y,int face)
{
    int ax=0,ay=0,af=0;
    if(!actor(map,id,&ax,&ay,&af)||ax!=x||ay!=y||(face&&af!=face)){
        fprintf(stderr,"actor mismatch map=%u id=%u expected=%d,%d f%d got=%d,%d f%d\n",
            map,id,x,y,face,ax,ay,af);exit(70);
    }
}
static void require_absent(unsigned map,unsigned id)
{
    int x,y,face;if(actor(map,id,&x,&y,&face)){
        fprintf(stderr,"unexpected actor map=%u id=%u at=%d,%d\n",map,id,x,y);exit(71);
    }
}
static void drive(unsigned target)
{
    for(int i=0;i<700;i++){
        tap(1);
        if(stage()>=target && !locked())return;
    }
    fprintf(stderr,"dialogue timeout stage=%u target=%u\n",stage(),target);exit(40);
}
static void drive_flag(unsigned flag)
{
    for(int i=0;i<250;i++){
        tap(1);
        if(call("FlagGet",flag) && !locked())return;
    }
    fprintf(stderr,"flag timeout flag=%u stage=%u\n",flag,stage());exit(41);
}
static void logpoint(const char *name,const char *out)
{
    int m,x,y;pos(&m,&x,&y);
    printf("%s map=%d x=%d y=%d stage=%u locked=%d\n",name,m,x,y,stage(),locked());fflush(stdout);
    unsigned base=sym("gObjectEvents");
    for(int i=0;i<16;i++){
        unsigned a=base+i*0x24;
        if(!(c->busRead8(c,a)&1))continue;
        unsigned id=c->busRead8(c,a+8),player=c->busRead8(c,a+2)&1;
        int wanted=player||(m==0&&(id==5||id==6||id==7))
            ||(m==10&&(id==1||id==2||id==3))||(m==9&&id==1)
            ||(m==28&&id==2)||(m==29&&(id==1||id==3))||(m==1&&id==1);
        if(!wanted)continue;
        printf(" actor=%s%u at=%d,%d face=%u map=%u,%u gfx=%u invisible=%u\n",player?"player":"local",id,
            (short)c->busRead16(c,a+16)-7,(short)c->busRead16(c,a+18)-7,
            c->busRead8(c,a+24)&15,c->busRead8(c,a+10),c->busRead8(c,a+9),
            c->busRead16(c,a+4),!!(c->busRead8(c,a+1)&32));
    }
    screenshot(out,name);
}
static int load_map(const char *name,int *w,int *h,unsigned short *cells)
{
    char path[512];snprintf(path,sizeof(path),"tools/vendor/gba/opening-house-work/data/layouts/%s/map.bin",name);
    if(!strcmp(name,"CherrygroveCity")){*w=80;*h=48;}
    else if(!strcmp(name,"CherrygroveRoute29Approach")){*w=72;*h=48;}
    else if(!strcmp(name,"NewBarkTown")){*w=48;*h=36;}
    else if(!strcmp(name,"CherrygroveRoute30Approach")){*w=80;*h=18;}
    else return 0;
    FILE*f=fopen(path,"rb");if(!f)return 0;
    int ok=fread(cells,2,(*w)*(*h),f)==(size_t)((*w)*(*h));fclose(f);return ok;
}
static void walk_to(int expectedMap,int tx,int ty,const char *layout)
{
    unsigned short cells[4000];int w,h;if(!load_map(layout,&w,&h,cells))exit(51);
    for(int attempt=0;attempt<900;attempt++){
        int map,x,y;pos(&map,&x,&y);
        if(map!=expectedMap){fprintf(stderr,"map changed while walking: %d != %d\n",map,expectedMap);exit(52);}
        if(x==tx&&y==ty)return;
        if(locked()){fprintf(stderr,"locked during walk to %d,%d\n",tx,ty);exit(53);}
        int dist[4000],first[4000],queue[4000],head=0,tail=0;
        for(int i=0;i<w*h;i++){dist[i]=-1;first[i]=-1;}
        int start=y*w+x;dist[start]=0;queue[tail++]=start;
        // Active actors occupy one tile. Leave the destination accessible for a
        // controlled interaction with an NPC if explicitly requested.
        unsigned char occupied[4000]={0};unsigned base=sym("gObjectEvents");
        for(int i=0;i<16;i++){
            unsigned z=base+i*0x24;
            if(!(c->busRead8(c,z)&1)||(c->busRead8(c,z+2)&1))continue;
            int ox=(short)c->busRead16(c,z+16)-7,oy=(short)c->busRead16(c,z+18)-7;
            if(ox>=0&&ox<w&&oy>=0&&oy<h)occupied[oy*w+ox]=1;
        }
        static const int dx[4]={0,0,-1,1},dy[4]={-1,1,0,0};
        static const unsigned keys[4]={64,128,32,16};
        while(head<tail){int cur=queue[head++];if(cur==ty*w+tx)break;
            int cx=cur%w,cy=cur/w;
            for(int d=0;d<4;d++){
                int nx=cx+dx[d],ny=cy+dy[d];if(nx<0||ny<0||nx>=w||ny>=h)continue;
                int j=ny*w+nx;if(dist[j]>=0||occupied[j])continue;
                unsigned short v=cells[j];if(v&0xC00)continue;
                if((v>>12)!=3 && !(nx==tx&&ny==ty))continue;
                dist[j]=dist[cur]+1;first[j]=cur==start?d:first[cur];queue[tail++]=j;
            }
        }
        int target=ty*w+tx;if(dist[target]<0){fprintf(stderr,"no route map=%d from %d,%d to %d,%d\n",map,x,y,tx,ty);exit(54);}
        int d=first[target];if(d<0)exit(55);
        frames(8,keys[d]);frames(9,0);
        int nm,nx,ny;pos(&nm,&nx,&ny);
        if(nm!=map)return; // caller handles connection
        if(nx==x&&ny==y){frames(12,keys[d]);frames(9,0);}
    }
    fprintf(stderr,"walking timeout target=%d,%d\n",tx,ty);exit(56);
}
static void cross(int map,unsigned key)
{
    for(int i=0;i<10;i++){
        frames(12,key);frames(12,0);int m,x,y;pos(&m,&x,&y);if(m!=map)return;
    }
    fprintf(stderr,"connection did not cross from map %d\n",map);exit(57);
}

int main(int argc,char **argv)
{
    if(argc!=5)return 2;
    FILE*f=fopen(argv[2],"r");while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
    unsigned char data[131072];f=fopen(argv[3],"rb");if(!f||fread(data,1,sizeof(data),f)!=sizeof(data))return 3;fclose(f);
    struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);
    if(!c||!c->init(c))return 4;mCoreConfigInit(&c->config,"apoc-ch1-continuous");c->setVideoBuffer(c,pixels,240);
    if(!mCoreLoadFile(c,argv[1])||!c->savedataRestore(c,data,sizeof(data),false))return 5;
    c->reset(c);frames(600,0);
    for(int i=0;i<100;i++){tap(1);if((c->busRead32(c,sym("gMain")+4)&~1u)==sym("CB2_Overworld")&&!locked())break;}
    logpoint("home-ready",argv[4]);
    frames(80,128);frames(180,0);
    frames(18,16);frames(180,0);
    frames(18,64);frames(18,0);frames(18,128);frames(180,0);
    frames(30,128);frames(180,0);
    logpoint("outside-home",argv[4]);
    require_actor(0,5,47,17,4);require_actor(0,6,51,17,3);
    drive(2);
    logpoint("silver-and-first-meeting",argv[4]);
    require_actor(0,5,47,17,4);require_absent(0,6);require_absent(0,7);
    walk_to(0,44,0,"CherrygroveCity");
    cross(0,64);
    logpoint("route30-entry",argv[4]);
    require_actor(10,1,44,15,0);require_absent(10,2);require_absent(10,3);
    walk_to(10,44,16,"CherrygroveRoute30Approach");
    drive(3);
    logpoint("rescue-return",argv[4]);
    require_actor(0,5,49,20,3);require_actor(0,7,47,19,4);
    frames(10,16);frames(12,0);tap(1);
    logpoint("gold-talk-attempt",argv[4]);
    drive(4);
    logpoint("starter-and-tour",argv[4]);
    require_absent(0,5);require_absent(0,7);
    walk_to(0,79,18,"CherrygroveCity");
    cross(0,16);
    logpoint("route29-entry",argv[4]);
    require_actor(9,1,10,17,3);
    walk_to(9,7,18,"CherrygroveRoute29Approach");
    frames(12,16);frames(20,0);
    drive_flag(0x2C);
    logpoint("route29-kestra",argv[4]);
    require_absent(9,1);
    walk_to(9,71,18,"CherrygroveRoute29Approach");
    cross(9,16);
    logpoint("new-bark-entry",argv[4]);
    drive_flag(0x2E);
    walk_to(28,27,11,"NewBarkTown");
    logpoint("elm-institute-entry",argv[4]);
    require_actor(28,2,27,14,2);
    drive(5);
    logpoint("elm-pokedex",argv[4]);
    require_actor(29,1,6,9,1);require_actor(29,3,5,10,4);
    frames(50,128);frames(240,0);
    logpoint("institute-exit",argv[4]);
    walk_to(28,0,18,"NewBarkTown");
    cross(28,32);
    logpoint("route29-return",argv[4]);
    walk_to(9,0,18,"CherrygroveRoute29Approach");
    cross(9,32);
    logpoint("gold-return-entry",argv[4]);
    require_actor(0,5,77,18,4);require_actor(0,7,76,18,4);
    drive(6);
    logpoint("gold-farewell-and-practice",argv[4]);
    walk_to(0,43,18,"CherrygroveCity");
    frames(30,64);frames(120,0);
    logpoint("home-farewell-entry",argv[4]);
    drive(7);
    logpoint("mom-goodbye",argv[4]);
    require_actor(1,1,2,5,1);
    frames(40,128);frames(120,0);
    logpoint("home-exit",argv[4]);
    walk_to(0,44,0,"CherrygroveCity");
    cross(0,64);
    logpoint("northbound-route",argv[4]);
    walk_to(10,44,12,"CherrygroveRoute30Approach");
    drive(8);
    logpoint("chapter1-departure",argv[4]);
    int finalMap,finalX,finalY;pos(&finalMap,&finalX,&finalY);
    unsigned gear=c->busRead32(c,sym("gSaveBlock3Ptr"))+4;
    unsigned cards=c->busRead8(c,gear+12);
    unsigned contacts=c->busRead8(c,gear+17);
    unsigned party=call("CalculatePlayerPartyCount",0);
    unsigned balls=call("CountTotalItemQuantityInBag",1);
    unsigned dex=call("FlagGet",0x861);
    printf("final party=%u balls=%u dex=%u map_card=%u gold_contact=%u stage=%u\n",
        party,balls,dex,cards&1,contacts&1,stage());
    if(finalMap!=10||finalX!=44||finalY!=12||stage()!=8||locked()
       ||party!=1||balls!=5||!dex||!(cards&1)||!(contacts&1))return 58;
    c->deinit(c);return 0;
}
