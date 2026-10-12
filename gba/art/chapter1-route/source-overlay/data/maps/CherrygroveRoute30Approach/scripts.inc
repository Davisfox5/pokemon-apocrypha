CherrygroveRoute30Approach_MapScripts::
    map_script MAP_SCRIPT_ON_TRANSITION, CherrygroveRoute30Approach_PositionRescue
    .byte 0
CherrygroveRoute30Approach_PositionRescue:
    call_if_eq VAR_APOC_CHAPTER_STAGE, 2, CherrygroveRoute30Approach_HideRescueCast
    end
CherrygroveRoute30Approach_HideRescueCast:
    setflag FLAG_APOC_ROUTE_RATTATA_HIDDEN
    setflag FLAG_APOC_ROUTE_GOLD_HIDDEN
    return

CherrygroveRoute30Approach_Northbound::
    lockall
    goto_if_lt VAR_APOC_CHAPTER_STAGE, 7, CherrygroveRoute30Approach_NorthTooSoon
    goto_if_ge VAR_APOC_CHAPTER_STAGE, 8, CherrygroveRoute30Approach_NorthAfter
    msgbox CherrygroveRoute30Approach_DepartureText, MSGBOX_DEFAULT
    setvar VAR_APOC_CHAPTER_STAGE, 8
    releaseall
    end
CherrygroveRoute30Approach_NorthTooSoon:
    msgbox CherrygroveRoute30Approach_NorthTooSoonText, MSGBOX_DEFAULT
    releaseall
    end
CherrygroveRoute30Approach_NorthAfter:
    releaseall
    end
CherrygroveRoute30Approach_DepartureText:
    .string "The road bends north toward\nVIOLET CITY. Your journey begins.$"
CherrygroveRoute30Approach_NorthTooSoonText:
    .string "The north road can wait.\nThere's still someone to see\nin CHERRYGROVE.$"

CherrygroveRoute30Approach_Kestra::
    lockall
    goto_if_ne VAR_APOC_CHAPTER_STAGE, 2, CherrygroveRoute30Approach_KestraWait
    getplayerxy VAR_0x8004, VAR_0x8005
    call_if_eq VAR_0x8004, 43, CherrygroveRoute30Approach_PlayerAlignRight
    call_if_eq VAR_0x8004, 45, CherrygroveRoute30Approach_PlayerAlignLeft
    applymovement LOCALID_PLAYER, CherrygroveRoute30Approach_PlayerFacesKestra
    applymovement LOCALID_ROUTE_KESTRA, CherrygroveRoute30Approach_KestraFacesPlayer
    waitmovement 0
    msgbox CherrygroveRoute30Approach_KestraSearching, MSGBOX_DEFAULT
    applymovement LOCALID_ROUTE_KESTRA, CherrygroveRoute30Approach_KestraSpots
    waitmovement 0
    msgbox CherrygroveRoute30Approach_KestraSpotsText, MSGBOX_DEFAULT
    closemessage
    clearflag FLAG_APOC_ROUTE_RATTATA_HIDDEN
    addobject LOCALID_ROUTE_RATTATA
    playse SE_M_SCRATCH
    applymovement LOCALID_ROUTE_RATTATA, CherrygroveRoute30Approach_RattataApproaches
    waitmovement 0
    msgbox CherrygroveRoute30Approach_RattataAppears, MSGBOX_DEFAULT
    clearflag FLAG_APOC_ROUTE_GOLD_HIDDEN
    addobject LOCALID_ROUTE_GOLD
    applymovement LOCALID_ROUTE_GOLD, CherrygroveRoute30Approach_GoldArrives
    waitmovement 0
    msgbox CherrygroveRoute30Approach_GoldWarning, MSGBOX_DEFAULT
    msgbox CherrygroveRoute30Approach_GoldThrow, MSGBOX_DEFAULT
    closemessage
    special ApocChapter_StartGoldCatch
    setflag FLAG_APOC_ROUTE_RATTATA_HIDDEN
    removeobject LOCALID_ROUTE_RATTATA
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
CherrygroveRoute30Approach_Rattata::
    end
CherrygroveRoute30Approach_PlayerAlignRight:
    applymovement LOCALID_PLAYER, CherrygroveRoute30Approach_PlayerStepRight
    waitmovement 0
    return
CherrygroveRoute30Approach_PlayerAlignLeft:
    applymovement LOCALID_PLAYER, CherrygroveRoute30Approach_PlayerStepLeft
    waitmovement 0
    return
CherrygroveRoute30Approach_PlayerStepRight:
    walk_fast_right
    step_end
CherrygroveRoute30Approach_PlayerStepLeft:
    walk_fast_left
    step_end
CherrygroveRoute30Approach_PlayerFacesKestra:
    face_up
    step_end
CherrygroveRoute30Approach_KestraFacesPlayer:
    face_down
    step_end
CherrygroveRoute30Approach_KestraSpots:
    walk_in_place_fast_right
    step_end
CherrygroveRoute30Approach_RattataApproaches:
    walk_down
    walk_in_place_fast_left
    step_end
CherrygroveRoute30Approach_GoldArrives:
    walk_down
    walk_in_place_fast_right
    step_end
CherrygroveRoute30Approach_KestraSearching:
    .string "KESTRA: There you are, slowpoke!\pI've been searching around\nfor wild POKéMON. Quietly!\pSee? I'm being careful...\nfor once.$"
CherrygroveRoute30Approach_KestraSpotsText:
    .string "KESTRA: Wait--over there!\nThere's one! Let's get him!$"
CherrygroveRoute30Approach_RattataAppears:
    .string "KESTRA: Oh! That RATTATA\nspotted us first...$"
CherrygroveRoute30Approach_GoldWarning:
    .string "GOLD: Whoa--HOLD it, you two!\pYou don't go charging a wild\nPOKéMON with none of your own.\p...And now it's spotted you.\nOf course it has. Stand back.$"
CherrygroveRoute30Approach_GoldThrow:
    .string "GOLD: Mine are back home...\nI hope this works!$"
CherrygroveRoute30Approach_Caught:
    .string "GOLD: ...And--gotcha.\nHeh. Still got the touch.$"
CherrygroveRoute30Approach_GoldTour:
    .string "GOLD: Phew. That was close.\pYou kids can't run off into\ntall grass like that!\pWhat to do with you two...\n...All right. Come with me.\pGuess it's my job to show you\nthe ropes, now the old man's gone.$"
