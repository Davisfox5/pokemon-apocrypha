// Qualification-only backend test. Does not replace the game's current save path.
#include "global.h"
#include "test/test.h"
#include "pokemon.h"
#include "new_game.h"
#include "load_save.h"
#include "gba/flash_internal.h"
#include "agb_flash.h"
#include "apocrypha_store.inc.c"

static EWRAM_DATA struct ApsStore sPageStore = {0};
static bool FlashRead(void *ctx, uint32_t offset, void *dst, uint32_t n)
{
    (void)ctx;
    if(offset > FLASH_ROM_SIZE_1M || n > FLASH_ROM_SIZE_1M-offset) return false;
    u8 *p=dst;
    while(n) {
        u32 size=APS_SECTOR_SIZE-offset%APS_SECTOR_SIZE;
        if(size>n) size=n;
        ReadFlash(offset/APS_SECTOR_SIZE,offset%APS_SECTOR_SIZE,p,size);
        p+=size;offset+=size;n-=size;
    }
    return true;
}
static bool FlashErase(void *ctx, uint8_t sector) { (void)ctx; return sector<32 && EraseFlashSector(sector)==0; }
static bool FlashProgram(void *ctx, uint32_t offset, const void *src, uint32_t n)
{
    (void)ctx;
    if(offset>FLASH_ROM_SIZE_1M || n>FLASH_ROM_SIZE_1M-offset) return false;
    const u8 *p=src;
    if(offset%APS_SECTOR_SIZE==0 && n==APS_SECTOR_SIZE)
        return ProgramFlashSector(offset/APS_SECTOR_SIZE,(u8 *)p)==0;
    for(u32 i=0;i<n;++i)
        if(ProgramFlashByte((offset+i)/APS_SECTOR_SIZE,(offset+i)%APS_SECTOR_SIZE,p[i])) return false;
    return true;
}
static const struct ApsFlash sDevice = {NULL, FlashRead, FlashErase, FlashProgram};
static void ExpectedMon(u32 slot, u32 revision, struct BoxPokemon *out)
{
    struct Pokemon mon;
    bool changed = revision && (slot==0 || slot==899);
    CreateMonWithIVs(&mon, slot & 1 ? SPECIES_SYLVEON : SPECIES_BULBASAUR,
                    changed ? 90 : 10+slot%80, 0x12345678+slot,
                    OTID_STRUCT_PRESET(0x45670000+slot), slot%32);
    // Fully initialize name buffers: short species names otherwise leave unused
    // trailing bytes dependent on stack contents, making regenerated fixtures differ.
    u8 name[POKEMON_NAME_LENGTH+1];
    for(u32 i=0;i<POKEMON_NAME_LENGTH;++i) name[i]=0xBB+(slot+i)%26;
    name[POKEMON_NAME_LENGTH]=0xFF; // Engine string terminator.
    SetMonData(&mon,MON_DATA_NICKNAME,name);
    SetMonData(&mon,MON_DATA_OT_NAME,name);
    *out=mon.box;
}
static bool FillPage(void *ctx, uint8_t page, uint8_t *out)
{
    u32 revision=*(u32 *)ctx;
    u32 start=page*APS_SECTOR_SIZE,end=start+APS_SECTOR_SIZE;
    for(u32 i=0;i<APS_SECTOR_SIZE;++i) out[i]=(u8)(start+i+(page==22?revision:0));
    for(u32 slot=start/80;slot<900 && slot*80<end;++slot) {
        struct BoxPokemon mon;ExpectedMon(slot,revision,&mon);
        u32 first=slot*80>start?slot*80:start,last=(slot+1)*80<end?(slot+1)*80:end;
        memcpy(out+first-start,((u8 *)&mon)+first-slot*80,last-first);
    }
    return true;
}
TEST("Apocrypha page backend stores 900 actual Pokemon and commits PC boundaries on GBA flash")
{
    // The upstream runner owns timer 2; flash normally uses timer 2 as well.
    // Isolate flash on unused timer 3 in this headless test.
    IntrFunc oldTimer3 = gIntrTable[2];
    EXPECT_EQ(SetFlashTimerIntr(3, &gIntrTable[2]),0);
    Test_MgbaPrintf("storage start budget=%d",gTestRunnerState.timeoutSeconds);
    NewGameInitData();
    Test_MgbaPrintf("storage initialized budget=%d",gTestRunnerState.timeoutSeconds);
    EXPECT_EQ(gFlashMemoryPresent, TRUE);
    for(u32 i=0;i<32;++i) EXPECT_EQ(EraseFlashSector(i),0);
    Test_MgbaPrintf("storage erased budget=%d",gTestRunnerState.timeoutSeconds);
    u32 revision=0;
    u32 budget=gTestRunnerState.timeoutSeconds;
    EXPECT_EQ(ApsFormat(&sPageStore,sDevice,FillPage,&revision),APS_OK);
    Test_MgbaPrintf("aps format_seconds=%d",budget-gTestRunnerState.timeoutSeconds);
    Test_MgbaPrintf("storage before mount budget=%d",gTestRunnerState.timeoutSeconds);
    EXPECT_EQ(ApsMount(&sPageStore,sDevice),APS_OK);
    Test_MgbaPrintf("storage after mount budget=%d",gTestRunnerState.timeoutSeconds);
    EXPECT_EQ(sizeof(sPageStore)<=4300,TRUE);
    Test_MgbaPrintf("aps workspace_bytes=%d",sizeof(sPageStore));
    for(u32 slot=0;slot<900;++slot) {
        if(slot%300==0)Test_MgbaPrintf("storage verify slot=%d budget=%d",slot,gTestRunnerState.timeoutSeconds);
        struct BoxPokemon got,want;ExpectedMon(slot,revision,&want);
        EXPECT_EQ(ApsRead(&sPageStore,slot*80,&got,sizeof(got)),APS_OK);
        if(memcmp(&got,&want,sizeof(got))) {
            Test_MgbaPrintf("mismatch slot=%d",slot);
            for(u32 b=0;b<80;++b)if(((u8 *)&got)[b]!=((u8 *)&want)[b])Test_MgbaPrintf("byte %d got=%d want=%d",b,((u8 *)&got)[b],((u8 *)&want)[b]);
        }
        EXPECT_EQ(memcmp(&got,&want,sizeof(got)),0);
        EXPECT_EQ(GetBoxMonData(&got,MON_DATA_SPECIES),slot&1?SPECIES_SYLVEON:SPECIES_BULBASAUR);
    }
    revision=1; const u8 changed[]={0,17,22};
    budget=gTestRunnerState.timeoutSeconds;
    EXPECT_EQ(ApsCommit(&sPageStore,changed,3,FillPage,&revision),APS_OK);
    Test_MgbaPrintf("aps three_page_commit_seconds=%d",budget-gTestRunnerState.timeoutSeconds);
    memset(&sPageStore,0,sizeof(sPageStore));
    Test_MgbaPrintf("storage before mount budget=%d",gTestRunnerState.timeoutSeconds);
    EXPECT_EQ(ApsMount(&sPageStore,sDevice),APS_OK);
    Test_MgbaPrintf("storage after mount budget=%d",gTestRunnerState.timeoutSeconds);
    for(u32 slot=0;slot<900;++slot) {
        if(slot%300==0)Test_MgbaPrintf("storage verify slot=%d budget=%d",slot,gTestRunnerState.timeoutSeconds);
        struct BoxPokemon got,want;ExpectedMon(slot,revision,&want);
        EXPECT_EQ(ApsRead(&sPageStore,slot*80,&got,sizeof(got)),APS_OK);
        if(memcmp(&got,&want,sizeof(got))) {
            Test_MgbaPrintf("mismatch slot=%d",slot);
            for(u32 b=0;b<80;++b)if(((u8 *)&got)[b]!=((u8 *)&want)[b])Test_MgbaPrintf("byte %d got=%d want=%d",b,((u8 *)&got)[b],((u8 *)&want)[b]);
        }
        EXPECT_EQ(memcmp(&got,&want,sizeof(got)),0);
    }
    IntrFunc ignored;
    SetFlashTimerIntr(2,&ignored);
    gIntrTable[2]=oldTimer3;
}
