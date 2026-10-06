#include "global.h"
#include "apoc_pokegear_services.h"
#include "event_data.h"
#include "rtc.h"
#include "item.h"
#include "battle_setup.h"
#include "constants/trainers.h"
#include "constants/opponents.h"
#include "constants/items.h"
#include "sound.h"
#include "naming_screen.h"
#include "field_screen_effect.h"
#include "overworld.h"
#include "constants/flags.h"
#include "constants/songs.h"
#define GEAR_MAGIC 0x41504731
#define GEAR_VERSION 1
static u32 Checksum(const struct ApocGearState *s)
{
    const u8 *p = (const u8 *)s;
    u32 hash = 2166136261u;
    unsigned i;
    for (i = 8; i < sizeof(*s); i++) hash = (hash ^ p[i]) * 16777619u;
    return hash;
}
void ApocGear_Seal(void)
{
    gSaveBlock3Ptr->apocGear.checksum = Checksum(&gSaveBlock3Ptr->apocGear);
}
void ApocGear_EnsureState(void)
{
    struct ApocGearState *s = &gSaveBlock3Ptr->apocGear;
    unsigned i;
    if (s->magic != GEAR_MAGIC || s->version != GEAR_VERSION || s->checksum != Checksum(s))
    {
        bool8 damaged = s->magic == GEAR_MAGIC;
        memset(s, 0, sizeof(*s));
        s->reserved[0] = damaged;
        s->magic = GEAR_MAGIC;
        s->version = GEAR_VERSION;
        s->queue = 255;
        s->passwordDay = 0xFFFF;
        for (i = 0; i < APGEAR_CONTACTS; i++) s->order[i] = i;
    }
    // Only an acquired gear registers Mom. No campaign contacts are fabricated.
    if (FlagGet(FLAG_APOC_POKEGEAR)) s->contacts[0] |= APGEAR_REGISTERED;
    ApocGear_Seal();
}
bool8 ApocGear_Register(u8 contact)
{
    if (contact >= APGEAR_CONTACTS) return FALSE;
    ApocGear_EnsureState();
    gSaveBlock3Ptr->apocGear.contacts[contact] |= APGEAR_REGISTERED;
    ApocGear_Seal();
    return TRUE;
}
bool8 ApocGear_QueueCall(u8 contact)
{
    ApocGear_EnsureState();
    if (contact >= APGEAR_CONTACTS || !(gSaveBlock3Ptr->apocGear.contacts[contact] & APGEAR_REGISTERED)) return FALSE;
    if (gSaveBlock3Ptr->apocGear.queue != 255)
        gSaveBlock3Ptr->apocGear.contacts[gSaveBlock3Ptr->apocGear.queue] |= APGEAR_MISSED;
    gSaveBlock3Ptr->apocGear.queue = contact;
    ApocGear_Seal();
    return TRUE;
}
void ApocGear_RecordCall(u8 contact, u8 kind)
{
    struct ApocGearState *s = &gSaveBlock3Ptr->apocGear;
    unsigned i;
    if (contact >= APGEAR_CONTACTS) return;
    for (i = APGEAR_HISTORY - 1; i; i--) s->history[i] = s->history[i-1];
    RtcCalcLocalTime();
    s->history[0].day = gLocalTime.days;
    s->history[0].contact = contact;
    s->history[0].kind = kind; // 0 outbound, 1 incoming, 2 missed
    if (s->historyCount < APGEAR_HISTORY) s->historyCount++;
    if (kind != 2) s->contacts[contact] &= ~APGEAR_MISSED;
    else s->contacts[contact] |= APGEAR_MISSED;
    if (s->queue == contact) s->queue = 255;
    ApocGear_Seal();
}
void ApocGear_FieldStep(void)
{
    struct ApocGearState *s = &gSaveBlock3Ptr->apocGear;
    if (!FlagGet(FLAG_APOC_POKEGEAR)) return;
    ApocGear_EnsureState();
    if (s->callbackSteps && !--s->callbackSteps)
    {
        ApocGear_Seal();
        ApocGear_QueueCall(0);
        PlaySE(SE_PC_LOGIN);
    }
    ApocGear_Seal();
}
void ApocGear_GiveMapCard(void)
{
    ApocGear_EnsureState();
    gSaveBlock3Ptr->apocGear.cards |= 1;
    ApocGear_Seal();
}
// Kestra asks for the player's name during their first meeting, after the cold open.
void ApocChapter_NamePlayer(void)
{
    DoNamingScreen(NAMING_SCREEN_PLAYER, gSaveBlock2Ptr->playerName,
                   gSaveBlock2Ptr->playerGender, 0, 0, CB2_ReturnToFieldContinueScript);
}
u8 ApocGear_GetNote(u8 region, u8 x, u8 y)
{
    ApocGear_EnsureState();
    unsigned i;
    for (i = 0; i < APGEAR_NOTES; i++)
    {
        struct ApocGearNote *n = &gSaveBlock3Ptr->apocGear.notes[i];
        if (n->icon && n->region == region && n->x == x && n->y == y) return n->icon;
    }
    return 0;
}
bool8 ApocGear_SetNote(u8 region, u8 x, u8 y, u8 icon)
{
    ApocGear_EnsureState();
    unsigned i, empty = APGEAR_NOTES;
    if (region < 1 || region > 5 || x > 207 || y > 127 || icon > 4) return FALSE;
    for (i = 0; i < APGEAR_NOTES; i++)
    {
        struct ApocGearNote *n = &gSaveBlock3Ptr->apocGear.notes[i];
        if (!n->icon) empty = i;
        if (n->icon && n->region == region && n->x == x && n->y == y) break;
    }
    if (i == APGEAR_NOTES) i = empty;
    if (i == APGEAR_NOTES) return FALSE;
    gSaveBlock3Ptr->apocGear.notes[i] = (struct ApocGearNote){region,x,y,icon};
    ApocGear_Seal();
    return TRUE;
}

bool8 ApocGear_SetGift(u8 contact, u16 item)
{
    if (contact >= APGEAR_CONTACTS || item == ITEM_NONE || item >= ITEMS_COUNT) return FALSE;
    ApocGear_EnsureState();
    if (!(gSaveBlock3Ptr->apocGear.contacts[contact]&APGEAR_REGISTERED) || gSaveBlock3Ptr->apocGear.gifts[contact]) return FALSE;
    gSaveBlock3Ptr->apocGear.gifts[contact] = item;
    gSaveBlock3Ptr->apocGear.contacts[contact] |= APGEAR_GIFT;
    ApocGear_Seal(); return TRUE;
}
bool8 ApocGear_ClaimGift(u8 contact)
{
    ApocGear_EnsureState();
    if(contact >= APGEAR_CONTACTS) return FALSE;
    u16 item = gSaveBlock3Ptr->apocGear.gifts[contact];
    if(!item || !AddBagItem(item,1)) return FALSE;
    gSaveBlock3Ptr->apocGear.gifts[contact] = ITEM_NONE;
    gSaveBlock3Ptr->apocGear.contacts[contact] &= ~APGEAR_GIFT;
    ApocGear_Seal();return TRUE;
}
bool8 ApocGear_SetRematchContact(u8 contact, u16 trainer)
{
    if(contact >= APGEAR_CONTACTS || !trainer || trainer >= TRAINERS_COUNT) return FALSE;
    ApocGear_EnsureState();
    if (!(gSaveBlock3Ptr->apocGear.contacts[contact]&APGEAR_REGISTERED)) return FALSE;
    gSaveBlock3Ptr->apocGear.rematchTrainers[contact] = trainer;
    ApocGear_Seal();return TRUE;
}
bool8 ApocGear_RematchReady(u8 contact)
{
    ApocGear_EnsureState();
    if(contact >= APGEAR_CONTACTS || !gSaveBlock3Ptr->apocGear.rematchTrainers[contact]) return FALSE;
    u16 trainer = gSaveBlock3Ptr->apocGear.rematchTrainers[contact];
    for(unsigned i=0;i<REMATCH_TABLE_ENTRIES && i<MAX_REMATCH_ENTRIES;i++)
        if(gRematchTable[i].trainerIds[0]==trainer)
            return gSaveBlock1Ptr->trainerRematches[i]!=0;
    return FALSE;
}

// callnative adapters use script-local arguments and return VAR_RESULT.
void ApocGear_RegisterContactSpecial(void) { gSpecialVar_Result = ApocGear_Register(gSpecialVar_0x8004); }
void ApocGear_QueueCallSpecial(void) { gSpecialVar_Result = ApocGear_QueueCall(gSpecialVar_0x8004); }
void ApocGear_SetGiftSpecial(void) { gSpecialVar_Result = ApocGear_SetGift(gSpecialVar_0x8004,gSpecialVar_0x8005); }
void ApocGear_SetRematchContactSpecial(void) { gSpecialVar_Result = ApocGear_SetRematchContact(gSpecialVar_0x8004,gSpecialVar_0x8005); }
