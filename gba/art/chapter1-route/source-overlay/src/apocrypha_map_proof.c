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
const u16 sMapProofMaps[] = {MAP_CHERRYGROVE_CITY, MAP_CHERRYGROVE_PLAYER_HOUSE, MAP_CHERRYGROVE_GOLD_HOUSE, MAP_CHERRYGROVE_NEIGHBOR_HOUSE, MAP_CHERRYGROVE_TRANSPLANT_HOUSE, MAP_CHERRYGROVE_MART, MAP_CHERRYGROVE_POKEMON_CENTER, MAP_CHERRYGROVE_PLAYER_BEDROOM, MAP_CHERRYGROVE_CENTER_UPSTAIRS, MAP_CHERRYGROVE_ROUTE29_APPROACH, MAP_CHERRYGROVE_ROUTE30_APPROACH, MAP_CHERRYGROVE_HARBOR_HOUSE, MAP_CHERRYGROVE_GARDEN_HOUSE, MAP_SANDGEM_TOWN, MAP_SANDGEM_LAB, MAP_SANDGEM_POKEMON_CENTER, MAP_SANDGEM_MART, MAP_SANDGEM_HOUSE_WEST, MAP_SANDGEM_HOUSE_SOUTH, MAP_SANDGEM_CENTER_UPSTAIRS, MAP_FLOCCESY_TOWN, MAP_FLOCCESY_POKEMON_CENTER, MAP_FLOCCESY_HOUSE_WEST, MAP_FLOCCESY_HOUSE_EAST, MAP_FLOCCESY_LODGE, MAP_FLOCCESY_SHED_WEST, MAP_FLOCCESY_SHED_EAST, MAP_FLOCCESY_CENTER_UPSTAIRS, MAP_NEW_BARK_TOWN, MAP_NEW_BARK_INSTITUTE};
void MapProof_Boot(void) { SetMainCallback2(CB2_NewGame); }
void MapProof_Enter(u32 region)
{
    u16 map = sMapProofMaps[(region & 255) % ARRAY_COUNT(sMapProofMaps)];
    SetWarpDestination(MAP_GROUP(map), MAP_NUM(map), WARP_ID_NONE, (region >> 8) & 255, (region >> 16) & 255);
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
