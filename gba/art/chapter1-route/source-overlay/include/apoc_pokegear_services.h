#ifndef GUARD_APOC_POKEGEAR_SERVICES_H
#define GUARD_APOC_POKEGEAR_SERVICES_H
void ApocGear_EnsureState(void);
void ApocGear_Seal(void);
bool8 ApocGear_Register(u8 contact);
bool8 ApocGear_QueueCall(u8 contact);
void ApocGear_RecordCall(u8 contact, u8 kind);
void ApocGear_FieldStep(void);
void ApocGear_GiveMapCard(void);
bool8 ApocGear_SetGift(u8 contact, u16 item);
bool8 ApocGear_ClaimGift(u8 contact);
bool8 ApocGear_SetRematchContact(u8 contact, u16 trainer);
bool8 ApocGear_RematchReady(u8 contact);
bool8 ApocGear_SetNote(u8 region, u8 x, u8 y, u8 icon);
u8 ApocGear_GetNote(u8 region, u8 x, u8 y);
#endif
