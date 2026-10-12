// Headless Gold rescue battle check. The special is invoked as a fixture while
// the ordinary map script/field choreography is qualified separately.
#define main unused_map_runtime_main
#include "runtime.c"
#undef main

int main(int argc, char **argv)
{
    if (argc != 5) return 2;
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
    mCoreConfigInit(&c->config, "apoc-gold-catch");
    c->setVideoBuffer(c, pixels, 240);
    if (!mCoreLoadFile(c, argv[1]) || !c->savedataRestore(c, data, sizeof(data), false)) return 5;
    c->reset(c);
    frames(600, 0);
    for (int i = 0; i < 100; i++)
    {
        frames(1, 1); frames(35, 0);
        if ((c->busRead32(c, sym("gMain") + 4) & ~1u) == sym("CB2_Overworld")
            && !call("ArePlayerFieldControlsLocked", 0)) break;
    }
    if ((c->busRead32(c, sym("gMain") + 4) & ~1u) != sym("CB2_Overworld")) return 6;
    call("ApocChapter_StartGoldCatch", 0);
    int sawBattle = 0, returned = 0;
    for (int i = 0; i < 300; i++)
    {
        frames(10, 1); frames(10, 0);
        if (i == 22 || i == 45 || i == 75)
        {
            char tag[32]; sprintf(tag, "catch-%03d", i);
            screenshot(argv[4], tag);
        }
        if ((c->busRead32(c, sym("gMain") + 4) & ~1u) != sym("CB2_Overworld")) sawBattle = 1;
        if (sawBattle && (c->busRead32(c, sym("gMain") + 4) & ~1u) == sym("CB2_Overworld"))
        {
            returned = 1;
            screenshot(argv[4], "catch-return");
            break;
        }
    }
    printf("saw_battle=%d returned=%d outcome=%u\n", sawBattle, returned,
           c->busRead8(c, sym("gBattleOutcome")));
    c->deinit(c);
    return sawBattle && returned ? 0 : 7;
}
