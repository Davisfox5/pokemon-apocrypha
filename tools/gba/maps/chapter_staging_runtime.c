// Native visual/flag probe for Gold's house and the Route 29 first-grass scene.
#define main unused_map_runtime_main
#include "runtime.c"
#undef main

static void set_stage(unsigned stage)
{
    unsigned regs[16], cpsr=rd("cpsr"); char rn[8];
    for(int i=0;i<16;i++){sprintf(rn,"r%d",i);regs[i]=rd(rn);}
    wr("cpsr",0x3f);wr("sp",0x03007c00);wr("r0",0x40FD);wr("r1",stage);
    wr("lr",0x09ffff01);wr("pc",sym("VarSet")&~1u);
    int done=0;
    for(int i=0;i<2000000;i++)if(rd("pc")>=0x09ffff00){done=1;break;}else c->step(c);
    if(!done)exit(6);
    wr("cpsr",cpsr);for(int i=0;i<15;i++){sprintf(rn,"r%d",i);wr(rn,regs[i]);}
    wr("pc",regs[15]-((cpsr&32)?2:4));
}

static void tap(unsigned key){frames(1,key);frames(36,0);}

int main(int argc,char **argv)
{
    if(argc!=5)return 2;
    FILE*f=fopen(argv[2],"r");while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
    unsigned char data[131072];f=fopen(argv[3],"rb");if(!f||fread(data,1,sizeof(data),f)!=sizeof(data))return 3;fclose(f);
    struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);
    c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;mCoreConfigInit(&c->config,"apoc-ch1-staging");
    c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1])||!c->savedataRestore(c,data,sizeof(data),false))return 5;
    c->reset(c);frames(600,0);
    for(int i=0;i<100;i++){tap(1);if((c->busRead32(c,sym("gMain")+4)&~1u)==sym("CB2_Overworld")&&!call("ArePlayerFieldControlsLocked",0))break;}
    set_stage(4);
    printf("stage4=%u\n",call("VarGet",0x40FD));
    call("MapProof_Enter",2|4<<8|7<<16);frames(200,0);screenshot(argv[4],"gold-house-stage4");
    printf("house4_flag=%u\n",call("FlagGet",0x2B));
    call("FlagClear",0x2C);
    call("MapProof_Enter",9|7<<8|19<<16);frames(200,0);screenshot(argv[4],"route29-before");
    frames(18,16);frames(36,0); // right onto the first-grass trigger at (8,19)
    observe("route29-step");
    for(int i=0;i<100 && !call("FlagGet",0x2C);i++){
        tap(1);
        if(i==5||i==15){char tag[36];sprintf(tag,"route29-%d",i);screenshot(argv[4],tag);}
    }
    unsigned done=call("FlagGet",0x2C);screenshot(argv[4],"route29-after");
    set_stage(5);
    printf("stage5=%u\n",call("VarGet",0x40FD));
    call("MapProof_Enter",2|4<<8|7<<16);frames(200,0);screenshot(argv[4],"gold-house-stage5");
    printf("house5_flag=%u\n",call("FlagGet",0x2B));
    printf("route29_done=%u\n",done);c->deinit(c);return done?0:7;
}
