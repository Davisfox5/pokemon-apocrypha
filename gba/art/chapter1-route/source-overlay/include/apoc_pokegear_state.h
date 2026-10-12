#ifndef GUARD_APOC_POKEGEAR_STATE_H
#define GUARD_APOC_POKEGEAR_STATE_H
#define APGEAR_CONTACTS 75
#define APGEAR_NOTES 100
#define APGEAR_HISTORY 16
#define APGEAR_REGISTERED 1
#define APGEAR_FAVORITE 2
#define APGEAR_MISSED 4
#define APGEAR_REMATCH 8
#define APGEAR_GIFT 16
struct ApocGearNote { u8 region, x, y, icon; };
struct ApocGearCall { u16 day; u8 contact, kind; };
struct ApocGearState {
    u32 magic, checksum;
    u16 version, passwordDay;
    u8 cards, historyCount, queue, callbackSteps;
    u8 contacts[APGEAR_CONTACTS], order[APGEAR_CONTACTS];
    struct ApocGearCall history[APGEAR_HISTORY];
    struct ApocGearNote notes[APGEAR_NOTES];
    u16 gifts[APGEAR_CONTACTS], rematchTrainers[APGEAR_CONTACTS];
    u8 passwordSolved, reserved[3];
};
#endif
