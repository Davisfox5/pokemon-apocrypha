NewBarkInstitute_MapScripts::
    map_script MAP_SCRIPT_ON_FRAME_TABLE, NewBarkInstitute_OnFrame
    .byte 0
NewBarkInstitute_OnFrame:
    map_script_2 VAR_APOC_CHAPTER_STAGE, 4, NewBarkInstitute_ElmHandoff
    .2byte 0

NewBarkInstitute_ElmHandoff:
    lockall
    applymovement LOCALID_PLAYER, NewBarkInstitute_PlayerApproaches
    applymovement LOCALID_NEW_BARK_INSTITUTE_KESTRA, NewBarkInstitute_KestraJoins
    applymovement LOCALID_NEW_BARK_ELM, NewBarkInstitute_ElmFacesPlayer
    waitmovement 0
    msgbox NewBarkInstitute_ElmGreeting, MSGBOX_DEFAULT
    msgbox NewBarkInstitute_KestraGreeting, MSGBOX_DEFAULT
    msgbox NewBarkInstitute_ElmDex, MSGBOX_DEFAULT
    setflag FLAG_SYS_POKEDEX_GET
    special SetUnlockedPokedexFlags
    msgbox NewBarkInstitute_ElmReceived, MSGBOX_DEFAULT
    msgbox NewBarkInstitute_ElmOrientation, MSGBOX_DEFAULT
    msgbox NewBarkInstitute_ElmRemembers, MSGBOX_DEFAULT
    msgbox NewBarkInstitute_ElmSilver, MSGBOX_DEFAULT
    setvar VAR_0x8004, 2
    special ApocGear_RegisterContactSpecial
    setvar VAR_APOC_CHAPTER_STAGE, 5
    msgbox NewBarkInstitute_ElmFarewell, MSGBOX_DEFAULT
    releaseall
    end
NewBarkInstitute_ElmFacesPlayer:
    face_down
    step_end
NewBarkInstitute_PlayerApproaches:
    walk_fast_up
    walk_fast_up
    face_up
    step_end
NewBarkInstitute_KestraJoins:
    walk_fast_right
    face_right
    step_end

NewBarkInstitute_Elm::
    lock
    faceplayer
    goto_if_ge VAR_APOC_CHAPTER_STAGE, 5, NewBarkInstitute_ElmAfter
    msgbox NewBarkInstitute_ElmWait, MSGBOX_DEFAULT
    release
    end
NewBarkInstitute_ElmAfter:
    msgbox NewBarkInstitute_ElmAfterText, MSGBOX_DEFAULT
    release
    end
NewBarkInstitute_Aide::
    lock
    faceplayer
    msgbox NewBarkInstitute_AideText, MSGBOX_DEFAULT
    release
    end
NewBarkInstitute_Kestra::
    lock
    faceplayer
    msgbox NewBarkInstitute_KestraText, MSGBOX_DEFAULT
    release
    end

NewBarkInstitute_ElmGreeting:
    .string "ELM: Ah--you must be the two\nfrom CHERRYGROVE. Come in!\pGOLD rang ahead about you.\nSaid his neighbors had finally\lcaught the bug.\pHe was right to send you.$"
NewBarkInstitute_KestraGreeting:
    .string "KESTRA: GOLD gave us our first\nPOKéMON! Can we really get\la POKéDEX?$"
NewBarkInstitute_ElmRemembers:
    .string "ELM: The two of you remind me\nof someone. Two, actually.\pGOLD walked into this lab\nnot much older than you are.\pAnd the other one--well,\nyou know him as the Champion.$"
NewBarkInstitute_ElmDex:
    .string "ELM: A Trainer without a\nPOKéDEX walks with closed eyes.\pHere. One for each of you.\pIt records every POKéMON you\nmeet and every one you catch.\pThe more pages you fill, the\nmore you'll understand.$"
NewBarkInstitute_ElmReceived:
    .string "{PLAYER} received a POKéDEX\nfrom Professor ELM!$"
NewBarkInstitute_ElmOrientation:
    .string "ELM: Check it whenever you\nsee a POKéMON you don't know.\pIt fills its own pages. All\nyou have to do is go and look.$"
NewBarkInstitute_ElmSilver:
    .string "ELM: SILVER was a difficult\nboy back then. Sharp edges.\pBut people change. He turned\nthat fire into something the\lwhole world could lean on.\pChampion. Protector. Proof\nno one is only their worst day.\pI've never been prouder of\ntwo students.$"
NewBarkInstitute_ElmFarewell:
    .string "ELM: Go on, then. Your road's\nwaiting. Fill those pages!\pI've added my number to your\nPOKéGEAR. Safe travels.$"
NewBarkInstitute_ElmWait:
    .string "ELM: Just a moment. I have\nsomething for both of you.$"
NewBarkInstitute_ElmAfterText:
    .string "ELM: How is the POKéDEX\ntreating you?\pEvery entry helps the\ninstitute's fieldwork.$"
NewBarkInstitute_AideText:
    .string "The public wing is busy enough.\nThe research rooms are beyond\nthis door.$"
NewBarkInstitute_KestraText:
    .string "KESTRA: The Champion started\nright here. Same professor!\pThat's going to be us. Come\non--let's go tell GOLD!$"
