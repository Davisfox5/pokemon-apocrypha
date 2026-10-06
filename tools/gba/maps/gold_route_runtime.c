// Script-level rescue test in a headless mGBA core. Starts from an ordinary
// saved field state; only the pre-rescue location/stage is set by fixture.
#define main unused_map_runtime_main
#include "runtime.c"
#undef main

static void tap(unsigned key) { frames(1, key); frames(36, 0); }

static int tour_actors(unsigned stop, const char *out)
{
    static const int positions[5][6] = {
        {49,11,50,11,51,11}, {59,11,60,11,61,11},
        {73,18,74,18,75,18}, {36,19,36,20,35,20},
        {47,20,48,20,49,20}
    };
    static const int faces[5][3] = {
        {4,4,3}, {4,4,3}, {4,4,3}, {1,3,4}, {4,4,3}
    };
    unsigned base=sym("gObjectEvents");
    int found[3]={0}, xx[3]={0}, yy[3]={0}, face[3]={0};
    for(int i=0;i<16;i++){
        unsigned a=base+i*0x24,flags=c->busRead8(c,a);
        if(!(flags&1)||c->busRead8(c,a+9)!=0||c->busRead8(c,a+10)!=80
           ||(c->busRead8(c,a+1)&32))continue;
        unsigned local=c->busRead8(c,a+8);
        int slot=(c->busRead8(c,a+2)&1)?0:local==7?1:local==5?2:-1;
        if(slot<0)continue;
        found[slot]++;xx[slot]=(short)c->busRead16(c,a+16)-7;
        yy[slot]=(short)c->busRead16(c,a+18)-7;
        face[slot]=c->busRead8(c,a+24)&15;
    }
    for(int j=0;j<3;j++)
        if(found[j]!=1||xx[j]!=positions[stop][j*2]||yy[j]!=positions[stop][j*2+1]||face[j]!=faces[stop][j]){
            static int sampled[5]={0};
            if(sampled[stop]++<3)printf("tour candidate %u player=%d,%d f%d Kestra=%d,%d f%d Gold=%d,%d f%d\n",
                stop,xx[0],yy[0],face[0],xx[1],yy[1],face[1],xx[2],yy[2],face[2]);
            return 0;
        }
    printf("tour stop %u player=%d,%d f%d Kestra=%d,%d f%d Gold=%d,%d f%d\n",
        stop,xx[0],yy[0],face[0],xx[1],yy[1],face[1],xx[2],yy[2],face[2]);
    fflush(stdout);
    char tag[40];sprintf(tag,"tour-stop-%u",stop);screenshot(out,tag);
    return 1;
}

int main(int argc, char **argv)
{
    if (argc != 5 && argc != 6 && argc != 7) return 2;
    unsigned desiredChoice = argc >= 6 ? atoi(argv[5]) : 1;
    int recordTour = argc == 7;
    if (desiredChoice > 2) return 2;
    FILE *f = fopen(argv[2], "r");
    while (ns < 128 && fscanf(f, "%79s %x", names[ns], &addrs[ns]) == 2) ns++;
    fclose(f);
    unsigned char data[131072];
    f = fopen(argv[3], "rb");
    if (!f || fread(data, 1, sizeof(data), f) != sizeof(data)) return 3;
    fclose(f);
    struct mLogger log = {.log = quiet};
    mLogSetDefaultLogger(&log);
    c = mCoreFind(argv[1]);
    if (!c || !c->init(c)) return 4;
    mCoreConfigInit(&c->config, "apoc-gold-route");
    c->setVideoBuffer(c, pixels, 240);
    if (!mCoreLoadFile(c, argv[1]) || !c->savedataRestore(c, data, sizeof(data), false)) return 5;
    c->reset(c); frames(600, 0);
    for (int i = 0; i < 100; i++)
    {
        tap(1);
        if ((c->busRead32(c, sym("gMain") + 4) & ~1u) == sym("CB2_Overworld")
            && !call("ArePlayerFieldControlsLocked", 0)) break;
    }
    call("FlagSet", 0x25); // pre-place Gold hidden
    call("FlagClear", 0x24); // Kestra has run north
    // VarSet takes two args; set r1 before calling with the shared helper.
    unsigned regs[16], cpsr = rd("cpsr"); char rn[8];
    for (int i = 0; i < 16; i++) { sprintf(rn, "r%d", i); regs[i] = rd(rn); }
    wr("cpsr", 0x3f); wr("sp", 0x03007c00); wr("r0", 0x40FD); wr("r1", 2);
    wr("lr", 0x09ffff01); wr("pc", sym("VarSet") & ~1u);
    int done = 0;
    for (int i = 0; i < 2000000; i++) { if (rd("pc") >= 0x09ffff00) { done = 1; break; } c->step(c); }
    if (!done) return 6;
    wr("cpsr", cpsr);
    for (int i = 0; i < 15; i++) { sprintf(rn, "r%d", i); wr(rn, regs[i]); }
    wr("pc", regs[15] - ((cpsr & 32) ? 2 : 4));
    // Map index 10, position (44, 16), just south of Kestra.
    call("MapProof_Enter", 10 | 44 << 8 | 16 << 16);
    frames(180, 0); observe("route-rescue-ready"); screenshot(argv[4], "route-before");
    tap(64); tap(1);
    int sawBattle = 0, returnedCity = 0;
    for (int i = 0; i < 400; i++)
    {
        tap(1);
        if (i == 4 || i == 20 || i == 35 || i == 55)
        { char tag[32]; sprintf(tag, "route-%03d", i); screenshot(argv[4], tag); }
        if ((c->busRead32(c, sym("gMain") + 4) & ~1u) != sym("CB2_Overworld")) sawBattle = 1;
        if (sawBattle && (c->busRead32(c, sym("gMain") + 4) & ~1u) == sym("CB2_Overworld"))
        {
            call("MapProof_ReadState", 0);
            unsigned a = sym("gMapProofState");
            if (c->busRead32(c, a + 8) == 0 && call("VarGet", 0x40FD) == 3)
            { returnedCity = 1; screenshot(argv[4], "route-return-city"); break; }
        }
    }
    int gotStarter = 0;
    if (returnedCity)
    {
        for (int i = 0; i < 80 && call("ArePlayerFieldControlsLocked", 0); i++) frames(20, 0);
        printf("post-warp locked=%u\n", call("ArePlayerFieldControlsLocked", 0));
        observe("ceremony-arrival");
        tap(16); // face Gold at the outdoor ceremony pin
        observe("ceremony-face-gold");
        screenshot(argv[4], "ceremony-before");
        tap(1);
        int steeredChoice = 0;
        unsigned tourSeen=0;
        for (int i = 0; i < 400; i++)
        {
            if (!steeredChoice && (c->busRead32(c, sym("gMain") + 4) & ~1u) == sym("CB2_StarterChoose"))
            {
                if (desiredChoice == 0) tap(32);
                if (desiredChoice == 2) tap(16);
                steeredChoice = 1;
            }
            tap(1);
            if(recordTour){char frameName[48];sprintf(frameName,"tour-motion-%03d",i);screenshot(argv[4],frameName);}
            unsigned px=999,py=999,base=sym("gObjectEvents");
            for(int actor=0;actor<16;actor++){
                unsigned address=base+actor*0x24;
                if((c->busRead8(c,address)&1)&&(c->busRead8(c,address+2)&1)){
                    px=(short)c->busRead16(c,address+16)-7;
                    py=(short)c->busRead16(c,address+18)-7;
                    break;
                }
            }
            static const int tourX[5]={49,59,73,36,47},tourY[5]={11,11,18,19,20};
            for(unsigned stop=0;stop<5;stop++)
                if(!(tourSeen&(1u<<stop))&&px==(unsigned)tourX[stop]&&py==(unsigned)tourY[stop]){
                    if(tour_actors(stop,argv[4]))tourSeen|=1u<<stop;
                }
            if (i == 6 || i == 15 || i == 28 || i % 30 == 0)
            { char tag[32]; sprintf(tag, "ceremony-%03d", i); screenshot(argv[4], tag); }
            if ((c->busRead32(c, sym("gMain") + 4) & ~1u) == sym("CB2_Overworld")
                && call("VarGet", 0x40FD) == 4)
            { gotStarter = tourSeen==31; screenshot(argv[4], "ceremony-complete"); break; }
        }
    }
    if (gotStarter)
    {
        for (int i = 0; i < 30 && call("ArePlayerFieldControlsLocked", 0); i++) tap(1);
        unsigned gear = c->busRead32(c, sym("gSaveBlock3Ptr")) + 4;
        unsigned cards = c->busRead8(c, gear + 12);
        unsigned gold = c->busRead8(c, gear + 17);
        unsigned party = call("CalculatePlayerPartyCount", 0);
        unsigned shoes = call("FlagGet", 0x8C0);
        printf("card=%u gold_contact=%u party=%u shoes=%u player_choice=%u kestra_choice=%u\n",
            cards & 1, gold & 1, party, shoes,
            call("VarGet", 0x40FE), call("VarGet", 0x40FF));
        screenshot(argv[4], "ceremony-final-field");
        if (!(cards & 1) || !(gold & 1) || party != 1 || !shoes
            || call("VarGet", 0x40FE) != desiredChoice
            || call("VarGet", 0x40FF) != (call("VarGet", 0x40FE) + 1) % 3)
            gotStarter = 0;
    }
    printf("saw_battle=%d returned_city=%d got_starter=%d stage=%u\n", sawBattle, returnedCity, gotStarter, call("VarGet", 0x40FD));
    c->deinit(c);
    return sawBattle && returnedCity && gotStarter ? 0 : 7;
}
