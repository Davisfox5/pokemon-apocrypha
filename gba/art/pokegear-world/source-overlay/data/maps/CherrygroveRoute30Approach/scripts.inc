CherrygroveRoute30Approach_MapScripts::
    .byte 0

CherrygroveRoute30Approach_Kestra::
    lockall
    faceplayer
    goto_if_ne VAR_APOC_CHAPTER_STAGE, 2, CherrygroveRoute30Approach_KestraWait
    msgbox CherrygroveRoute30Approach_KestraSearching, MSGBOX_DEFAULT
    msgbox CherrygroveRoute30Approach_RattataAppears, MSGBOX_DEFAULT
    clearflag FLAG_APOC_ROUTE_GOLD_HIDDEN
    addobject LOCALID_ROUTE_GOLD
    applymovement LOCALID_ROUTE_GOLD, CherrygroveRoute30Approach_GoldArrives
    waitmovement 0
    msgbox CherrygroveRoute30Approach_GoldWarning, MSGBOX_DEFAULT
    msgbox CherrygroveRoute30Approach_GoldThrow, MSGBOX_DEFAULT
    closemessage
    special ApocChapter_StartGoldCatch
    msgbox CherrygroveRoute30Approach_Caught, MSGBOX_DEFAULT
    msgbox CherrygroveRoute30Approach_GoldTour, MSGBOX_DEFAULT
    setvar VAR_APOC_CHAPTER_STAGE, 3
    setflag FLAG_APOC_ROUTE_KESTRA_HIDDEN
    setflag FLAG_APOC_ROUTE_GOLD_HIDDEN
    clearflag FLAG_APOC_KESTRA_NORTH
    fadescreen FADE_TO_BLACK
    removeobject LOCALID_ROUTE_GOLD
    removeobject LOCALID_ROUTE_KESTRA
    warp MAP_CHERRYGROVE_CITY, 48, 20
    waitstate
    releaseall
    end
CherrygroveRoute30Approach_KestraWait:
    msgbox CherrygroveRoute30Approach_KestraSearching, MSGBOX_DEFAULT
    releaseall
    end
CherrygroveRoute30Approach_Gold::
    end
CherrygroveRoute30Approach_GoldArrives:
    walk_down
    walk_in_place_fast_right
    step_end
CherrygroveRoute30Approach_KestraSearching:
    .string "KESTRA: This grass is perfect!\nWe're going to find a POKéMON.$"
CherrygroveRoute30Approach_RattataAppears:
    .string "A wild RATTATA bursts from the\ngrass! KESTRA has no POKéMON.$"
CherrygroveRoute30Approach_GoldWarning:
    .string "GOLD: Don't rush wild POKéMON\nwithout anything to protect you!$"
CherrygroveRoute30Approach_GoldThrow:
    .string "GOLD: Mine are back home...\nI hope this works!$"
CherrygroveRoute30Approach_Caught:
    .string "The RATTATA is caught.\nKESTRA is safe.$"
CherrygroveRoute30Approach_GoldTour:
    .string "GOLD: You two can't run into\ntall grass like that. Come on.\pI suppose I'll show you around.$"
