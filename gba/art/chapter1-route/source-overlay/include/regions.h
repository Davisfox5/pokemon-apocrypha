#ifndef GUARD_REGIONS_H
#define GUARD_REGIONS_H

#include "global.h"
#include "constants/regions.h"

enum KantoSubRegion GetKantoSubregion(u32 mapSecId);

static inline enum Region GetRegionForSectionId(u32 sectionId)
{
    switch (sectionId) {
    case MAPSEC_FLOCCESY_TOWN: return REGION_UNOVA;
    case MAPSEC_SANDGEM_TOWN: return REGION_SINNOH;
    case MAPSEC_CHERRYGROVE_CITY: return REGION_JOHTO;
    case MAPSEC_PROOF_HOENN: return REGION_HOENN;
    case MAPSEC_PROOF_JOHTO: return REGION_JOHTO;
    case MAPSEC_PROOF_KANTO: return REGION_KANTO;
    case MAPSEC_PROOF_SINNOH: return REGION_SINNOH;
    case MAPSEC_PROOF_UNOVA: return REGION_UNOVA;
    }
    if (sectionId >= KANTO_MAPSEC_START && sectionId < MAPSEC_SPECIAL_AREA)
        return REGION_KANTO;
    return REGION_HOENN;
}

static inline enum Region GetCurrentRegion(void)
{
    return GetRegionForSectionId(gMapHeader.regionMapSectionId);
}

#endif // GUARD_REGIONS_H
