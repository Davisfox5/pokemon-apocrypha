// Compile with the target compiler: host sizeof() would give incorrect results.
#include "global.h"
#include "pokemon_storage_system.h"
#include "save.h"

struct ProposedThirtyBoxStorage
{
    u8 currentBox;
    struct BoxPokemon boxes[30][IN_BOX_COUNT];
    u8 boxNames[30][BOX_NAME_LENGTH + 1];
    u8 boxWallpapers[30];
    struct Pokemon fusions[MAX_FUSION_STORAGE];
};

const u32 apocryphaCapacity[] __attribute__((section(".apocrypha_capacity"), used)) = {
    sizeof(struct BoxPokemon), sizeof(struct Pokemon),
    sizeof(struct SaveBlock1), sizeof(struct SaveBlock2), sizeof(struct SaveBlock3),
    sizeof(struct PokemonStorage), TOTAL_BOXES_COUNT, IN_BOX_COUNT,
    SECTOR_DATA_SIZE, SAVE_BLOCK_3_CHUNK_SIZE, NUM_SECTORS_PER_SLOT, SECTORS_COUNT,
    SECTOR_ID_PKMN_STORAGE_END - SECTOR_ID_PKMN_STORAGE_START + 1,
    sizeof(struct ProposedThirtyBoxStorage), NUM_FLAG_BYTES, VARS_COUNT,
    NUM_BADGES, OBJECT_EVENTS_COUNT, NUM_SPECIES,
    offsetof(struct SaveBlock1, vars) + 32 * sizeof(u16),
};
