// Background emulator probe of the Gold/Silver/Murkrow outdoor scene.
#define main unused_map_runtime_main
#include "runtime.c"
#undef main
int main(int argc,char **argv)
{
    if(argc!=5)return 2;
    FILE *f=fopen(argv[2],"r");while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
    unsigned char data[131072];f=fopen(argv[3],"rb");if(!f||fread(data,1,sizeof(data),f)!=sizeof(data))return 3;fclose(f);
    struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);
    c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;mCoreConfigInit(&c->config,"apoc-opening-cast");
    c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1])||!c->savedataRestore(c,data,sizeof(data),false))return 5;
    c->reset(c);frames(600,0);
    for(int i=0;i<100;i++){frames(1,1);frames(36,0);if((c->busRead32(c,sym("gMain")+4)&~1u)==sym("CB2_Overworld")&&!call("ArePlayerFieldControlsLocked",0))break;}
    call("MapProof_Enter",0 | 43<<8 | 17<<16);frames(180,0);
    screenshot(argv[4],"silver-opening-start");
    for(int i=0;i<500;i++){
        frames(1,1);
        if(i>=28&&i<=32){
            for(int j=0;j<36;j+=4){frames(4,0);char name[48];sprintf(name,"flyoff-%02d-%02d",i,j);screenshot(argv[4],name);}
        }else frames(36,0);
        if(i==3||i==7||i==11||i==15||i==20||(i>=22&&i<=38&&i%2==0)){char name[40];sprintf(name,"silver-opening-%02d",i);screenshot(argv[4],name);}
        if(call("VarGet",0x40FD)==2&&!call("ArePlayerFieldControlsLocked",0))break;
    }
    unsigned stage=call("VarGet",0x40FD),silver=call("FlagGet",0x22),murkrow=call("FlagGet",0x27);
    observe("silver-departed");screenshot(argv[4],"silver-departed");
    printf("stage=%u silver_hidden=%u murkrow_hidden=%u\n",stage,silver,murkrow);
    c->deinit(c);return stage==2&&silver&&murkrow?0:6;
}
