"""Restore appended inanimate fixtures in older Ecruteak saves, without a reset."""
from pathlib import Path
import sys
G=Path(sys.argv[1]);p=G/'src/event_object_movement.c';s=p.read_text();assert 'Ecruteak_EnsureHeritageObjects' not in s
s='#include "constants/map_groups.h"\n'+s+'''\n// Older Ecruteak previews cached an empty object-template list. Restore only
// the two appended inanimate fixtures on return to field; preserve all other
// objects, flags, party, inventory, player coordinates and save layout.
void Ecruteak_EnsureHeritageObjects(struct ScriptContext *ctx)
{
    u32 i;
    u8 objectEventId;
    const struct ObjectEventTemplate *template;
    (void)ctx;
    if (gSaveBlock1Ptr->location.mapGroup != MAP_GROUP(MAP_JOHTO_ECRUTEAK_CITY)
     || gSaveBlock1Ptr->location.mapNum != MAP_NUM(MAP_JOHTO_ECRUTEAK_CITY))
        return;
    for (i = 0; i < gMapHeader.events->objectEventCount; i++)
    {
        template = &gMapHeader.events->objectEvents[i];
        if (template->graphicsId < OBJ_EVENT_GFX_ECRUTEAK_FIRST
         || template->graphicsId >= OBJ_EVENT_GFX_ECRUTEAK_END)
            continue;
        if (gSaveBlock1Ptr->objectEventTemplates[i].localId != template->localId
         || gSaveBlock1Ptr->objectEventTemplates[i].graphicsId != template->graphicsId)
            gSaveBlock1Ptr->objectEventTemplates[i] = *template;
        if (TryGetObjectEventIdByLocalIdAndMap(template->localId,
                gSaveBlock1Ptr->location.mapNum, gSaveBlock1Ptr->location.mapGroup, &objectEventId))
            TrySpawnObjectEvent(template->localId,
                gSaveBlock1Ptr->location.mapNum, gSaveBlock1Ptr->location.mapGroup);
    }
}
''';p.write_text(s)
p=G/'data/maps/JohtoEcruteakCity/scripts.inc';s=p.read_text().replace('JohtoEcruteakCity_MapScripts::\n    .byte 0','JohtoEcruteakCity_MapScripts::\n    map_script MAP_SCRIPT_ON_RETURN_TO_FIELD, JohtoEcruteakCity_RefreshHeritage\n    .byte 0');s+='\nJohtoEcruteakCity_RefreshHeritage:\n    callnative Ecruteak_EnsureHeritageObjects\n    end\n';p.write_text(s)
