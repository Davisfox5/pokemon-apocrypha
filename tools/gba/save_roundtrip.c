// Qualification-only test, temporarily installed by build.py --qualification.
#include "global.h"
#include "test/test.h"
#include "new_game.h"
#include "load_save.h"
#include "save.h"
#include "pokemon.h"
#include "pokemon_storage_system.h"

static u32 StorageDigest(void)
{
    const u8 *bytes = (const u8 *)gPokemonStoragePtr;
    u32 hash = 2166136261u;
    for (u32 i = 0; i < sizeof(*gPokemonStoragePtr); ++i)
        hash = (hash ^ bytes[i]) * 16777619u;
    return hash;
}

TEST("Apocrypha baseline normal flash save reload retains party, PC boundaries and story state")
{
    NewGameInitData();
    EXPECT_EQ(gFlashMemoryPresent, TRUE);
    CreateRandomMon(&gParties[B_TRAINER_PLAYER][0], SPECIES_BULBASAUR, 15);
    gPartiesCount[B_TRAINER_PLAYER] = 1;
    SetBoxMonAt(0, 0, &gParties[B_TRAINER_PLAYER][0].box);
    CreateRandomMon(&gParties[B_TRAINER_PLAYER][0], SPECIES_SYLVEON, 25);
    SetBoxMonAt(TOTAL_BOXES_COUNT - 1, IN_BOX_COUNT - 1, &gParties[B_TRAINER_PLAYER][0].box);
    // Exercise every available slot with individually generated Pokemon.
    for (u32 box = 0; box < TOTAL_BOXES_COUNT; ++box)
        for (u32 slot = 0; slot < IN_BOX_COUNT; ++slot)
        {
            CreateRandomMon(&gParties[B_TRAINER_PLAYER][0],
                            box == 0 && slot == 0 ? SPECIES_BULBASAUR : SPECIES_SYLVEON, 25);
            SetBoxMonAt(box, slot, &gParties[B_TRAINER_PLAYER][0].box);
        }
    u32 storageDigest = StorageDigest();
    gSaveBlock1Ptr->vars[32] = 1234;
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);

    // Destroy the selected live state so the assertions require a flash reload.
    ZeroPlayerPartyMons();
    ResetPokemonStorageSystem();
    gSaveBlock1Ptr->vars[32] = 0;
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(gPartiesCount[B_TRAINER_PLAYER], 1);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_SPECIES), SPECIES_SYLVEON);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_LEVEL), 25);
    EXPECT_EQ(GetBoxMonData(GetBoxedMonPtr(0, 0), MON_DATA_SPECIES), SPECIES_BULBASAUR);
    EXPECT_EQ(GetBoxMonData(GetBoxedMonPtr(TOTAL_BOXES_COUNT - 1, IN_BOX_COUNT - 1), MON_DATA_SPECIES), SPECIES_SYLVEON);
    EXPECT_EQ(gSaveBlock1Ptr->vars[32], 1234);
    EXPECT_EQ(StorageDigest(), storageDigest);
}

TEST("Apocrypha roster profile retains Sylveon and canonical Fairy typing")
{
    EXPECT_EQ(gSpeciesInfo[SPECIES_SYLVEON].types[0], TYPE_FAIRY);
    EXPECT_EQ(gSpeciesInfo[SPECIES_CLEFAIRY].types[0], TYPE_FAIRY);
    EXPECT_EQ(gSpeciesInfo[SPECIES_GENESECT].baseHP, 71);
}
