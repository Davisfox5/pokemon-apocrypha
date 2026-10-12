// Test-only engine entry points. Never included in the production source tree.
#include "global.h"
#include "main.h"
#include "overworld.h"
#include "field_screen_effect.h"
#include "field_player_avatar.h"
#include "event_data.h"
#include "regions.h"
#include "save.h"
#include "load_save.h"
#include "constants/map_groups.h"

EWRAM_DATA u32 gMapProofState[12] = {0};
const u16 sMapProofMaps[] = {MAP_PROOF_HOENN, MAP_PROOF_JOHTO, MAP_PROOF_KANTO, MAP_PROOF_SINNOH, MAP_PROOF_UNOVA};
void MapProof_Boot(void) { SetMainCallback2(CB2_NewGame); }
void MapProof_Enter(u32 region)
{
    u16 map = sMapProofMaps[region % 5];
    SetWarpDestination(MAP_GROUP(map), MAP_NUM(map), WARP_ID_NONE, 10, 11);
    DoWarp();
}
void MapProof_ReadState(void)
{
    s16 x,y;
    PlayerGetDestCoords(&x,&y);
    gMapProofState[0]=GetCurrentRegion();
    gMapProofState[1]=gSaveBlock1Ptr->location.mapGroup;
    gMapProofState[2]=gSaveBlock1Ptr->location.mapNum;
    gMapProofState[3]=x-7;
    gMapProofState[4]=y-7;
    gMapProofState[5]=gMapHeader.mapLayout->isFrlg;
    gMapProofState[6]=gMapHeader.mapLayout->width;
    gMapProofState[7]=gMapHeader.mapLayout->height;
    gMapProofState[8]=VarGet(VAR_TEMP_1);
    gMapProofState[9]=gMapHeader.regionMapSectionId;
}
void MapProof_Resume(void) { SetMainCallback2(CB2_ContinueSavedGame); }

void MapProof_Keep(void) { asm volatile ("" :: "r"(MapProof_Boot), "r"(MapProof_Enter), "r"(MapProof_ReadState), "r"(MapProof_Resume)); }
