// Headless visual and script probe for the Chapter 1 New Bark draft.
#define main unused_map_runtime_main
#include "runtime.c"
#undef main

static void set_stage(unsigned stage)
{
    unsigned regs[16], cpsr = rd("cpsr"); char rn[8];
    for (int i=0;i<16;i++) { sprintf(rn,"r%d",i); regs[i]=rd(rn); }
    wr("cpsr",0x3f); wr("sp",0x03007c00); wr("r0",0x40FD); wr("r1",stage);
    wr("lr",0x09ffff01); wr("pc",sym("VarSet")&~1u);
    int done=0;
    for (int i=0;i<2000000;i++) if (rd("pc")>=0x09ffff00) { done=1; break; } else c->step(c);
    if (!done) exit(6);
    wr("cpsr",cpsr);
    for (int i=0;i<15;i++) { sprintf(rn,"r%d",i); wr(rn,regs[i]); }
    wr("pc",regs[15]-((cpsr&32)?2:4));
}

static int finish_script(void)
{
    for(int i=0;i<100;i++)
    {
        frames(1,1);frames(36,0);
        if((c->busRead32(c,sym("gMain")+4)&~1u)==sym("CB2_Overworld")
            && !call("ArePlayerFieldControlsLocked",0))return 1;
    }
    return 0;
}

int main(int argc,char **argv)
{
    if (argc!=5) return 2;
    FILE *f=fopen(argv[2],"r");
    while(ns<128 && fscanf(f,"%79s %x",names[ns],&addrs[ns])==2) ns++;
    fclose(f);
    unsigned char data[131072];
    f=fopen(argv[3],"rb");
    if (!f || fread(data,1,sizeof(data),f)!=sizeof(data)) return 3;
    fclose(f);
    struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);
    c=mCoreFind(argv[1]);if(!c||!c->init(c)) return 4;
    mCoreConfigInit(&c->config,"apoc-new-bark");c->setVideoBuffer(c,pixels,240);
    if(!mCoreLoadFile(c,argv[1])||!c->savedataRestore(c,data,sizeof(data),false))return 5;
    c->reset(c);frames(600,0);
    for(int i=0;i<100;i++) {
        frames(1,1);frames(36,0);
        if((c->busRead32(c,sym("gMain")+4)&~1u)==sym("CB2_Overworld") && !call("ArePlayerFieldControlsLocked",0))break;
    }
    set_stage(4);
    call("MapProof_Enter",9 | 67<<8 | 18<<16);
    frames(180,0);observe("route-east-end");screenshot(argv[4],"route-east-end");
    frames(110,16);frames(100,0);observe("route-new-bark-crossing");
    screenshot(argv[4],"route-new-bark-crossing");
    if(!finish_script())return 26;
    call("MapProof_ReadState",0);
    if(c->busRead32(c,sym("gMapProofState")+8)!=28) return 8;
    call("MapProof_Enter",28 | 27<<8 | 14<<16);
    frames(180,0);observe("new-bark");screenshot(argv[4],"new-bark");
    frames(50,64);frames(180,0);observe("institute-entry");screenshot(argv[4],"institute-entry");
    for(int i=0;i<250;i++) {
        frames(1,1);frames(28,0);
        if (i==4||i==12||i==20) {char tag[40];sprintf(tag,"institute-%d",i);screenshot(argv[4],tag);}
        if(i%20==0) {char tag[40];sprintf(tag,"institute-dialogue-%03d",i);screenshot(argv[4],tag);}
        if(call("VarGet",0x40FD)==5)break;
    }
    observe("elm-complete");screenshot(argv[4],"elm-complete");
    unsigned stage=call("VarGet",0x40FD), dex=call("FlagGet",0x861);
    printf("stage=%u dex=%u\n",stage,dex);
    if(stage!=5||!dex)return 7;
    unsigned partyBeforePractice=call("CalculatePlayerPartyCount",0);
    unsigned ballsBeforePractice=call("CountTotalItemQuantityInBag",1);
    if(!finish_script())return 12;
    call("MapProof_Enter",28 | 27<<8 | 14<<16);
    frames(180,0);frames(50,64);frames(180,0);
    if(call("VarGet",0x40FD)!=5 || !call("FlagGet",0x861))return 20;
    if(!finish_script())return 21;
    frames(30,128);frames(150,0);observe("institute-exit");
    if(state[2]!=28)return 24;
    call("MapProof_Enter",28 | 2<<8 | 18<<16);
    frames(150,0);frames(50,32);frames(150,0);observe("route-westbound");
    if(state[2]!=9)return 25;
    call("MapProof_Enter",0 | 79<<8 | 18<<16);
    frames(180,0);observe("gold-return");screenshot(argv[4],"gold-return");
    for(int i=0;i<300 && call("VarGet",0x40FD)<6;i++) {
        frames(1,1);frames(32,0);
        if(i==4||i==16||i==40){char tag[40];sprintf(tag,"gold-%d",i);screenshot(argv[4],tag);}
        if(i%20==0){char tag[40];sprintf(tag,"gold-dialogue-%03d",i);screenshot(argv[4],tag);}
    }
    stage=call("VarGet",0x40FD);observe("gold-farewell");screenshot(argv[4],"gold-farewell");
    if(stage!=6)return 9;
    // The chapter stage advances before Gold's final advice. He must remain
    // next to the player while that dialogue is on screen, then leave.
    int goldNearby=0;unsigned objectBase=sym("gObjectEvents");
    for(int i=0;i<16;i++){
        unsigned a=objectBase+i*0x24;
        if((c->busRead8(c,a)&1)&&c->busRead8(c,a+8)==5
           &&c->busRead8(c,a+9)==0&&c->busRead8(c,a+10)==80
           &&(short)c->busRead16(c,a+16)-7==77
           &&(short)c->busRead16(c,a+18)-7==18
           &&!(c->busRead8(c,a+1)&32))goldNearby=1;
    }
    printf("gold_visible_during_advice=%d\n",goldNearby);
    if(!goldNearby)return 28;
    if(!finish_script())return 13;
    if(!call("FlagGet",0x26) || !call("FlagGet",0x28))return 22;
    unsigned partyAfterPractice=call("CalculatePlayerPartyCount",0);
    unsigned ballsAfterGift=call("CountTotalItemQuantityInBag",1);
    printf("practice_party_before=%u after=%u balls_before=%u after_gift=%u\n",
           partyBeforePractice,partyAfterPractice,ballsBeforePractice,ballsAfterGift);
    if(partyAfterPractice!=partyBeforePractice || ballsAfterGift!=ballsBeforePractice+5)return 27;
    call("MapProof_Enter",1 | 3<<8 | 6<<16);
    frames(180,0);observe("mom-return");screenshot(argv[4],"mom-return");
    for(int i=0;i<200 && call("VarGet",0x40FD)<7;i++){
        frames(1,1);frames(35,0);
        if(i%20==0){char tag[40];sprintf(tag,"mom-dialogue-%03d",i);screenshot(argv[4],tag);}
    }
    stage=call("VarGet",0x40FD);observe("mom-farewell");screenshot(argv[4],"mom-farewell");
    if(!finish_script())return 14;
    unsigned saveEnabled=call("VarGet",0x404E);
    unsigned netPrize=call("ApocChapter_DivertTrainerPrize",1000);
    unsigned saved=call("VarGet",0x40DB) | call("VarGet",0x40DC)<<16;
    printf("mom_stage=%u savings_enabled=%u prize_net=%u saved=%u\n",stage,saveEnabled,netPrize,saved);
    if(stage!=7||saveEnabled!=1||netPrize!=900||saved!=100)return 10;
    unsigned saveStatus=call("TrySavingData",0);
    void *flash=NULL;size_t flashSize=c->savedataClone(c,&flash);
    if(saveStatus!=1||flashSize!=131072)return 15;
    c->deinit(c);
    c=mCoreFind(argv[1]);if(!c||!c->init(c))return 16;
    mCoreConfigInit(&c->config,"apoc-new-bark-continue");c->setVideoBuffer(c,pixels,240);
    if(!mCoreLoadFile(c,argv[1])||!c->savedataRestore(c,flash,flashSize,false))return 17;
    free(flash);c->reset(c);frames(600,0);
    if(call("LoadGameSave",0)!=1)return 18;
    call("MapProof_Resume",0);frames(240,0);
    stage=call("VarGet",0x40FD);saved=call("VarGet",0x40DB)|call("VarGet",0x40DC)<<16;
    observe("cold-continue");screenshot(argv[4],"cold-continue");
    printf("cold_stage=%u cold_saved=%u cold_dex=%u\n",stage,saved,call("FlagGet",0x861));
    if(stage!=7||saved!=100||!call("FlagGet",0x861))return 19;
    call("ApocChapter_WithdrawSavings",0);
    saved=call("VarGet",0x40DB)|call("VarGet",0x40DC)<<16;
    if(saved!=0)return 23;
    printf("withdrawal_saved=%u\n",saved);
    call("MapProof_Enter",10 | 44<<8 | 13<<16);
    frames(180,0);frames(22,64);frames(100,0);
    for(int i=0;i<10 && call("VarGet",0x40FD)<8;i++){frames(1,1);frames(35,0);}
    stage=call("VarGet",0x40FD);observe("north-departure");screenshot(argv[4],"north-departure");
    c->deinit(c);
    return stage==8?0:11;
}
