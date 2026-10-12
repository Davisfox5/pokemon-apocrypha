CherrygroveCity_MapScripts::
    map_script MAP_SCRIPT_ON_TRANSITION, CherrygroveCity_PositionCast
    map_script MAP_SCRIPT_ON_FRAME_TABLE, CherrygroveCity_OnFrame
    .byte 0

CherrygroveCity_PositionCast:
    call_if_eq VAR_APOC_CHAPTER_STAGE, 0, CherrygroveCity_HideMurkrow
    call_if_ge VAR_APOC_CHAPTER_STAGE, 1, CherrygroveCity_HideBattleMons
    call_if_eq VAR_APOC_CHAPTER_STAGE, 4, CherrygroveCity_GoldWentHome
    call_if_eq VAR_APOC_CHAPTER_STAGE, 3, CherrygroveCity_CeremonyPosition
    call_if_eq VAR_APOC_CHAPTER_STAGE, 5, CherrygroveCity_ReturnPosition
    call_if_ge VAR_APOC_CHAPTER_STAGE, 6, CherrygroveCity_GoldAtHouse
    end
CherrygroveCity_HideMurkrow:
    setflag FLAG_APOC_MURKROW_HIDDEN
    clearflag FLAG_APOC_BATTLE_MONS_HIDDEN
    clearflag FLAG_APOC_GOLD_OUTSIDE_HIDDEN
    return
CherrygroveCity_HideBattleMons:
    setflag FLAG_APOC_BATTLE_MONS_HIDDEN
    return
CherrygroveCity_GoldWentHome:
    setflag FLAG_APOC_GOLD_OUTSIDE_HIDDEN
    return
CherrygroveCity_CeremonyPosition:
    setobjectxyperm LOCALID_CAST_KESTRA, 47, 19
    setobjectmovementtype LOCALID_CAST_KESTRA, MOVEMENT_TYPE_FACE_RIGHT
    setobjectxyperm LOCALID_CAST_GOLD, 49, 20
    setobjectmovementtype LOCALID_CAST_GOLD, MOVEMENT_TYPE_FACE_LEFT
    return
CherrygroveCity_ReturnPosition:
    clearflag FLAG_APOC_GOLD_OUTSIDE_HIDDEN
    clearflag FLAG_APOC_KESTRA_NORTH
    setobjectxyperm LOCALID_CAST_KESTRA, 76, 18
    setobjectmovementtype LOCALID_CAST_KESTRA, MOVEMENT_TYPE_FACE_RIGHT
    setobjectxyperm LOCALID_CAST_GOLD, 77, 18
    setobjectmovementtype LOCALID_CAST_GOLD, MOVEMENT_TYPE_FACE_RIGHT
    return
CherrygroveCity_GoldAtHouse:
    clearflag FLAG_APOC_GOLD_OUTSIDE_HIDDEN
    setobjectxyperm LOCALID_CAST_GOLD, 49, 20
    setobjectmovementtype LOCALID_CAST_GOLD, MOVEMENT_TYPE_FACE_LEFT
    return
CherrygroveCity_OnFrame:
    map_script_2 VAR_APOC_CHAPTER_STAGE, 0, CherrygroveCity_SilverDeparture
    map_script_2 VAR_APOC_CHAPTER_STAGE, 5, CherrygroveCity_GoldFarewellScene
    .2byte 0

CherrygroveCity_SilverDeparture:
    goto_if_lt VAR_APOC_HOME_STAGE, 4, CherrygroveCity_NoChapterScene
    setflag FLAG_APOC_ROUTE_KESTRA_HIDDEN
    setflag FLAG_APOC_ROUTE_GOLD_HIDDEN
    setflag FLAG_APOC_ROUTE_RATTATA_HIDDEN
    lockall
    applymovement LOCALID_PLAYER, CherrygroveCity_PlayerApproachesBattle
    waitmovement 0
    msgbox CherrygroveCity_KestraRecognizes, MSGBOX_DEFAULT
    msgbox CherrygroveCity_SpectatorBoyReaction, MSGBOX_DEFAULT
    closemessage
    msgbox CherrygroveCity_GoldAttack, MSGBOX_DEFAULT
    applymovement LOCALID_BATTLE_TYPHLOSION, CherrygroveCity_TyphlosionAttacks
    playse SE_M_FLAMETHROWER
    waitmovement 0
    delay 18
    msgbox CherrygroveCity_SilverAttack, MSGBOX_DEFAULT
    applymovement LOCALID_BATTLE_ALAKAZAM, CherrygroveCity_AlakazamAttacks
    playse SE_M_PSYBEAM
    waitmovement 0
    delay 22
    msgbox CherrygroveCity_SpectatorManReaction, MSGBOX_DEFAULT
    closemessage
    fadescreen FADE_TO_WHITE
    setflag FLAG_APOC_BATTLE_MONS_HIDDEN
    removeobject LOCALID_BATTLE_TYPHLOSION
    removeobject LOCALID_BATTLE_ALAKAZAM
    fadescreen FADE_FROM_WHITE
    msgbox CherrygroveCity_KestraAfterBattle, MSGBOX_DEFAULT
    msgbox CherrygroveCity_SilverTeases, MSGBOX_DEFAULT
    msgbox CherrygroveCity_GoldOldDays, MSGBOX_DEFAULT
    msgbox CherrygroveCity_SilverLeague, MSGBOX_DEFAULT
    msgbox CherrygroveCity_GoldQuietTown, MSGBOX_DEFAULT
    msgbox CherrygroveCity_KestraHushed, MSGBOX_DEFAULT
    msgbox CherrygroveCity_SilverFarewell, MSGBOX_DEFAULT
    closemessage
    playse SE_TAILLOW_WING_FLAP
    clearflag FLAG_APOC_MURKROW_HIDDEN
    addobject LOCALID_CAST_MURKROW
    applymovement LOCALID_CAST_SILVER, CherrygroveCity_SilverFly
    applymovement LOCALID_CAST_MURKROW, CherrygroveCity_MurkrowFly
    waitmovement 0
    fadescreen FADE_TO_WHITE
    setflag FLAG_APOC_SILVER_DEPARTED
    removeobject LOCALID_CAST_SILVER
    setflag FLAG_APOC_MURKROW_HIDDEN
    removeobject LOCALID_CAST_MURKROW
    fadescreen FADE_FROM_WHITE
    msgbox CherrygroveCity_KestraFlyoff, MSGBOX_DEFAULT
    setvar VAR_APOC_CHAPTER_STAGE, 1
    call CherrygroveCity_FirstMeeting
    releaseall
    end
CherrygroveCity_NoChapterScene:
    end
CherrygroveCity_FaceRight:
    walk_in_place_fast_right
    step_end
CherrygroveCity_PlayerApproachesBattle:
    walk_fast_right
    walk_fast_right
    face_right
    step_end
CherrygroveCity_TyphlosionAttacks:
    jump_in_place_right
    step_end
CherrygroveCity_AlakazamAttacks:
    jump_in_place_left
    step_end
CherrygroveCity_SilverFly:
    jump_up
    walk_fast_up
    walk_fast_up
    step_end
CherrygroveCity_MurkrowFly:
    jump_up
    walk_fast_up
    walk_fast_up
    step_end
CherrygroveCity_KestraRecognizes:
    .string "KESTRA: No way. No way, no way--\pThat's Champion SILVER. Here.\nIn the flesh.$"
CherrygroveCity_GoldAttack:
    .string "GOLD: TYPHLOSION! Fire Blast,\nnow!$"
CherrygroveCity_SilverAttack:
    .string "SILVER: Alakazam. Psychic.\nEnd it.$"
CherrygroveCity_KestraAfterBattle:
    .string "KESTRA: Did you SEE that?!\pHe didn't even raise his voice.\nGOLD is the strongest Trainer\lever lived, and SILVER just--\pTook him apart.$"
CherrygroveCity_SilverTeases:
    .string "SILVER: ...And that's the match.\pYour TYPHLOSION still hits\nlike a freight train, old man.\pBut your reads have gone soft.\nRetirement's made you rusty.$"
CherrygroveCity_GoldOldDays:
    .string "GOLD: Hah! No sense denying it.\pFirst real battle I've had\nin years.\pFelt good. Like the old days.$"
CherrygroveCity_SilverLeague:
    .string "SILVER: You could have the old\ndays back any time you wanted.\pCome back to the League.\nThe circuit's grown dull\lwithout anyone worth fearing.$"
CherrygroveCity_GoldQuietTown:
    .string "GOLD: And upstage the Champion\nin front of the whole world?\pNot a chance. Besides,\neverything I need is right here.$"
CherrygroveCity_KestraHushed:
    .string "KESTRA: They're just... talking.\nLike it's nothing.\pTwo of the strongest people\nalive, right in front of us.$"
CherrygroveCity_SilverFarewell:
    .string "SILVER: ...Heh. Same old GOLD.\pTake care of yourself.\nI've got a region waiting on me.$"
CherrygroveCity_KestraFlyoff:
    .string "KESTRA: ...And he just flies\noff. Like the sky belongs to him.$"
CherrygroveCity_SpectatorBoyReaction:
    .string "BOY: That's GOLD's TYPHLOSION!\nCan you feel the heat from here?$"
CherrygroveCity_SpectatorManReaction:
    .string "MAN: SILVER read that attack\nperfectly. What a finish...$"

CherrygroveCity_BattleSpectatorMan::
    msgbox CherrygroveCity_SpectatorManAfter, MSGBOX_NPC
    end
CherrygroveCity_SpectatorManAfter:
    .string "GOLD looked happy just to\nbattle his old friend again.$"

CherrygroveCity_Waterfront::
    msgbox CherrygroveCity_Waterfront_Text, MSGBOX_NPC
    end

CherrygroveCity_Waterfront_Text:
    .string "I come down here to watch the waves.\nThere is always something to see.$"

CherrygroveCity_Commuter::
    msgbox CherrygroveCity_Commuter_Text, MSGBOX_NPC
    end

CherrygroveCity_Commuter_Text:
    .string "Half the kids here ride to New Bark\nfor the labs now. Not Gold.\pHe came to Cherrygrove to get\naway from all that humming.$"

CherrygroveCity_TownSign::
    msgbox CherrygroveCity_TownSign_Text, MSGBOX_NPC
    end

CherrygroveCity_TownSign_Text:
    .string "CHERRYGROVE CITY\nWhere the cherry trees and the sea\plook after their own.$"

CherrygroveCity_NorthSign::
    msgbox CherrygroveCity_NorthSign_Text, MSGBOX_NPC
    end

CherrygroveCity_NorthSign_Text:
    .string "ROUTE 30\nNorth toward VIOLET CITY$"

CherrygroveCity_EastSign::
    msgbox CherrygroveCity_EastSign_Text, MSGBOX_NPC
    end

CherrygroveCity_EastSign_Text:
    .string "ROUTE 29\nEast toward NEW BARK TOWN$"

CherrygroveCity_GoldSign::
    msgbox CherrygroveCity_GoldSign_Text, MSGBOX_NPC
    end

CherrygroveCity_GoldSign_Text:
    .string "A quiet house and a worn battle yard.\nA man who has done enough.$"

CherrygroveCity_WaterfrontSign::
    msgbox CherrygroveCity_WaterfrontSign_Text, MSGBOX_NPC
    end

CherrygroveCity_WaterfrontSign_Text:
    .string "CHERRYGROVE WATERFRONT$"

CherrygroveCity_JohtoBoy::
    lock
    faceplayer
    msgbox CherrygroveCity_JohtoBoy_Text, MSGBOX_DEFAULT
    release
    end

CherrygroveCity_JohtoBoy_Text::
    .string "I saw the Champion battle\nGOLD right here!$"

CherrygroveCity_JohtoGirl::
    lock
    faceplayer
    msgbox CherrygroveCity_JohtoGirl_Text, MSGBOX_DEFAULT
    release
    end

CherrygroveCity_JohtoGirl_Text::
    .string "I like taking the long way home.$"

CherrygroveCity_CastGold::
    lock
    faceplayer
    goto_if_eq VAR_APOC_CHAPTER_STAGE, 5, CherrygroveCity_GoldFarewell
    goto_if_ge VAR_APOC_CHAPTER_STAGE, 4, CherrygroveCity_GoldAfterStarter
    goto_if_eq VAR_APOC_CHAPTER_STAGE, 3, CherrygroveCity_GoldStarter
    msgbox CherrygroveCity_GoldBeforeRescue, MSGBOX_DEFAULT
    release
    end

CherrygroveCity_GoldBeforeRescue:
    .string "GOLD: KESTRA went north? I'll\nkeep an eye on the route.$"

CherrygroveCity_GoldStarter:
    lockall
    msgbox CherrygroveCity_GoldTourStart, MSGBOX_DEFAULT
    closemessage
    call CherrygroveCity_TourWalk
    goto CherrygroveCity_GoldCeremony
CherrygroveCity_GoldCeremony:
    msgbox CherrygroveCity_GoldTour, MSGBOX_DEFAULT
    msgbox CherrygroveCity_KestraInsists, MSGBOX_DEFAULT
    msgbox CherrygroveCity_GoldHesitates, MSGBOX_DEFAULT
    msgbox CherrygroveCity_KestraChampions, MSGBOX_DEFAULT
    msgbox CherrygroveCity_GoldRelents, MSGBOX_DEFAULT
    msgbox CherrygroveCity_KestraCheers, MSGBOX_DEFAULT
    msgbox CherrygroveCity_GoldWait, MSGBOX_DEFAULT
    closemessage
    applymovement LOCALID_CAST_GOLD, CherrygroveCity_GoldStepsInside
    waitmovement 0
    removeobject LOCALID_CAST_GOLD
    delay 60
    setobjectxyperm LOCALID_CAST_GOLD, 54, 19
    addobject LOCALID_CAST_GOLD
    applymovement LOCALID_CAST_GOLD, CherrygroveCity_GoldStepsOutside
    waitmovement 0
    msgbox CherrygroveCity_GoldPromise, MSGBOX_DEFAULT
    msgbox CherrygroveCity_KestraPickFirst, MSGBOX_DEFAULT
    closemessage
    special ApocChapter_ChooseStarter
    copyvar VAR_APOC_PLAYER_STARTER, VAR_RESULT
    copyvar VAR_STARTER_MON, VAR_RESULT
    goto_if_eq VAR_APOC_PLAYER_STARTER, 0, CherrygroveCity_GiveChikorita
    goto_if_eq VAR_APOC_PLAYER_STARTER, 1, CherrygroveCity_GiveCyndaquil
    goto CherrygroveCity_GiveTotodile
CherrygroveCity_GiveChikorita:
    setvar VAR_APOC_KESTRA_STARTER, 1
    givemon SPECIES_CHIKORITA, 5
    goto CherrygroveCity_StarterReceived
CherrygroveCity_GiveCyndaquil:
    setvar VAR_APOC_KESTRA_STARTER, 2
    givemon SPECIES_CYNDAQUIL, 5
    goto CherrygroveCity_StarterReceived
CherrygroveCity_GiveTotodile:
    setvar VAR_APOC_KESTRA_STARTER, 0
    givemon SPECIES_TOTODILE, 5
CherrygroveCity_StarterReceived:
    setflag FLAG_SYS_POKEMON_GET
    setflag FLAG_SYS_B_DASH
    setvar VAR_0x8004, 1
    special ApocGear_RegisterContactSpecial
    callnative ApocGear_GiveMapCard
    setvar VAR_APOC_CHAPTER_STAGE, 4
    msgbox CherrygroveCity_KestraCounter, MSGBOX_DEFAULT
    msgbox CherrygroveCity_GoldTools, MSGBOX_DEFAULT
    msgbox CherrygroveCity_KestraRace, MSGBOX_DEFAULT
    closemessage
    applymovement LOCALID_CAST_KESTRA, CherrygroveCity_KestraRunsEast
    waitmovement 0
    setflag FLAG_APOC_KESTRA_NORTH
    removeobject LOCALID_CAST_KESTRA
    msgbox CherrygroveCity_GoldElm, MSGBOX_DEFAULT
    closemessage
    applymovement LOCALID_CAST_GOLD, CherrygroveCity_GoldStepsInside
    waitmovement 0
    setflag FLAG_APOC_GOLD_OUTSIDE_HIDDEN
    removeobject LOCALID_CAST_GOLD
    releaseall
    end
CherrygroveCity_GoldAfterStarter:
    msgbox CherrygroveCity_GoldAfterStarterText, MSGBOX_DEFAULT
    release
    end
CherrygroveCity_GoldFarewellScene:
    lockall
    goto CherrygroveCity_GoldFarewell
CherrygroveCity_GoldFarewell:
    goto_if_set FLAG_APOC_GOLD_CATCH_DEMO, CherrygroveCity_GoldGiveBalls
    msgbox CherrygroveCity_GoldWelcomeBack, MSGBOX_DEFAULT
    msgbox CherrygroveCity_KestraDeparts, MSGBOX_DEFAULT
    closemessage
    applymovement LOCALID_CAST_KESTRA, CherrygroveCity_KestraRunsWest
    waitmovement 0
    setflag FLAG_APOC_KESTRA_NORTH
    setflag FLAG_APOC_KESTRA_DEPARTED
    removeobject LOCALID_CAST_KESTRA
    msgbox CherrygroveCity_GoldWatchingKestra, MSGBOX_DEFAULT
    msgbox CherrygroveCity_GoldCatchIntro, MSGBOX_DEFAULT
    closemessage
    special ApocChapter_StartPracticeCatch
    setflag FLAG_APOC_GOLD_CATCH_DEMO
    msgbox CherrygroveCity_GoldCatchLesson, MSGBOX_DEFAULT
    msgbox CherrygroveCity_GoldGift, MSGBOX_DEFAULT
CherrygroveCity_GoldGiveBalls:
    giveitem ITEM_POKE_BALL, 5
    goto_if_eq VAR_RESULT, FALSE, CherrygroveCity_GoldBagFull
    setvar VAR_APOC_CHAPTER_STAGE, 6
    msgbox CherrygroveCity_GoldLastAdvice, MSGBOX_DEFAULT
    msgbox CherrygroveCity_GoldDontRush, MSGBOX_DEFAULT
    closemessage
    fadescreen FADE_TO_BLACK
    removeobject LOCALID_CAST_GOLD
    setobjectxyperm LOCALID_CAST_GOLD, 49, 20
    addobject LOCALID_CAST_GOLD
    fadescreen FADE_FROM_BLACK
    releaseall
    end
CherrygroveCity_GoldBagFull:
    msgbox CherrygroveCity_GoldBagFullText, MSGBOX_DEFAULT
    releaseall
    end
CherrygroveCity_GoldTour:
    .string "GOLD: All right, uh... that's\nthe tour.\pYou should go play at home\nnow. Or something.$"
CherrygroveCity_GoldTourStart:
    .string "GOLD: Come on, you two.\nI said I'd show you around.\pTry to keep up, all right?$"
CherrygroveCity_TourCenter:
    .string "GOLD: POKéMON CENTER. They'll\nheal your team, no questions.\pYou'll be glad it's here after\na long stretch on the road.$"
CherrygroveCity_TourMart:
    .string "GOLD: The MART sells BALLS\nand other things you'll need.\pDon't wait until you're out of\nsupplies to come back.$"
CherrygroveCity_TourRoute29:
    .string "GOLD: That's ROUTE 29. It\nruns east to NEW BARK.\pProfessor ELM's institute is\nthere. I should call ahead.$"
CherrygroveCity_TourShore:
    .string "GOLD: And the sea. Some\nPOKéMON only live out there.\pKESTRA: You really did show\nus the whole town!$"
CherrygroveCity_GoldStepsInside:
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_up
    step_end
CherrygroveCity_GoldStepsOutside:
    walk_fast_down
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    face_left
    step_end
CherrygroveCity_TourWalk:
    @ Form a queue beside Gold's house, then walk without warping.
    applymovement LOCALID_CAST_GOLD, CherrygroveCity_TourGoldLineUp
    applymovement LOCALID_CAST_KESTRA, CherrygroveCity_TourKestraLineUp
    waitmovement 0
    applymovement LOCALID_CAST_GOLD, CherrygroveCity_TourMartGOLD
    applymovement LOCALID_CAST_KESTRA, CherrygroveCity_TourMartKESTRA
    applymovement LOCALID_PLAYER, CherrygroveCity_TourMartPLAYER
    waitmovement 0
    applymovement LOCALID_CAST_GOLD, CherrygroveCity_TourMartGOLDFace
    applymovement LOCALID_CAST_KESTRA, CherrygroveCity_TourMartKESTRAFace
    applymovement LOCALID_PLAYER, CherrygroveCity_TourMartPLAYERFace
    waitmovement 0
    msgbox CherrygroveCity_TourMart, MSGBOX_DEFAULT
    closemessage
    applymovement LOCALID_CAST_GOLD, CherrygroveCity_TourCenterGOLD
    applymovement LOCALID_CAST_KESTRA, CherrygroveCity_TourCenterKESTRA
    applymovement LOCALID_PLAYER, CherrygroveCity_TourCenterPLAYER
    waitmovement 0
    applymovement LOCALID_CAST_GOLD, CherrygroveCity_TourCenterGOLDFace
    applymovement LOCALID_CAST_KESTRA, CherrygroveCity_TourCenterKESTRAFace
    applymovement LOCALID_PLAYER, CherrygroveCity_TourCenterPLAYERFace
    waitmovement 0
    msgbox CherrygroveCity_TourCenter, MSGBOX_DEFAULT
    closemessage
    applymovement LOCALID_CAST_GOLD, CherrygroveCity_TourRoute29GOLD
    applymovement LOCALID_CAST_KESTRA, CherrygroveCity_TourRoute29KESTRA
    applymovement LOCALID_PLAYER, CherrygroveCity_TourRoute29PLAYER
    waitmovement 0
    applymovement LOCALID_CAST_GOLD, CherrygroveCity_TourRoute29GOLDFace
    applymovement LOCALID_CAST_KESTRA, CherrygroveCity_TourRoute29KESTRAFace
    applymovement LOCALID_PLAYER, CherrygroveCity_TourRoute29PLAYERFace
    waitmovement 0
    msgbox CherrygroveCity_TourRoute29, MSGBOX_DEFAULT
    closemessage
    applymovement LOCALID_CAST_GOLD, CherrygroveCity_TourShoreGOLD
    applymovement LOCALID_CAST_KESTRA, CherrygroveCity_TourShoreKESTRA
    applymovement LOCALID_PLAYER, CherrygroveCity_TourShorePLAYER
    waitmovement 0
    applymovement LOCALID_CAST_GOLD, CherrygroveCity_TourShoreGOLDFace
    applymovement LOCALID_CAST_KESTRA, CherrygroveCity_TourShoreKESTRAFace
    applymovement LOCALID_PLAYER, CherrygroveCity_TourShorePLAYERFace
    waitmovement 0
    msgbox CherrygroveCity_TourShore, MSGBOX_DEFAULT
    closemessage
    applymovement LOCALID_CAST_GOLD, CherrygroveCity_TourHouseGOLD
    applymovement LOCALID_CAST_KESTRA, CherrygroveCity_TourHouseKESTRA
    applymovement LOCALID_PLAYER, CherrygroveCity_TourHousePLAYER
    waitmovement 0
    applymovement LOCALID_CAST_GOLD, CherrygroveCity_TourHouseGOLDFace
    applymovement LOCALID_CAST_KESTRA, CherrygroveCity_TourHouseKESTRAFace
    applymovement LOCALID_PLAYER, CherrygroveCity_TourHousePLAYERFace
    waitmovement 0
    return
CherrygroveCity_TourGoldLineUp:
    walk_fast_up
    step_end
CherrygroveCity_TourKestraLineUp:
    walk_fast_right
    step_end
CherrygroveCity_TourMartGOLD:
    walk_fast_up
    walk_fast_up
    walk_fast_up
    walk_fast_up
    walk_fast_up
    walk_fast_up
    walk_fast_up
    walk_fast_up
    walk_fast_right
    walk_fast_right
    step_end
CherrygroveCity_TourMartGOLDFace:
    face_left
    step_end
CherrygroveCity_TourMartKESTRA:
    walk_fast_right
    walk_fast_up
    walk_fast_up
    walk_fast_up
    walk_fast_up
    walk_fast_up
    walk_fast_up
    walk_fast_up
    walk_fast_up
    walk_fast_right
    step_end
CherrygroveCity_TourMartKESTRAFace:
    face_right
    step_end
CherrygroveCity_TourMartPLAYER:
    walk_fast_up
    walk_fast_right
    walk_fast_up
    walk_fast_up
    walk_fast_up
    walk_fast_up
    walk_fast_up
    walk_fast_up
    walk_fast_up
    walk_fast_up
    step_end
CherrygroveCity_TourMartPLAYERFace:
    face_right
    step_end
CherrygroveCity_TourCenterGOLD:
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    step_end
CherrygroveCity_TourCenterGOLDFace:
    face_left
    step_end
CherrygroveCity_TourCenterKESTRA:
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    step_end
CherrygroveCity_TourCenterKESTRAFace:
    face_right
    step_end
CherrygroveCity_TourCenterPLAYER:
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    step_end
CherrygroveCity_TourCenterPLAYERFace:
    face_right
    step_end
CherrygroveCity_TourRoute29GOLD:
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_down
    walk_fast_down
    walk_fast_down
    walk_fast_down
    walk_fast_down
    walk_fast_down
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_down
    walk_fast_right
    walk_fast_right
    step_end
CherrygroveCity_TourRoute29GOLDFace:
    face_left
    step_end
CherrygroveCity_TourRoute29KESTRA:
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_down
    walk_fast_down
    walk_fast_down
    walk_fast_down
    walk_fast_down
    walk_fast_down
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_down
    walk_fast_right
    step_end
CherrygroveCity_TourRoute29KESTRAFace:
    face_right
    step_end
CherrygroveCity_TourRoute29PLAYER:
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_down
    walk_fast_down
    walk_fast_down
    walk_fast_down
    walk_fast_down
    walk_fast_down
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_down
    step_end
CherrygroveCity_TourRoute29PLAYERFace:
    face_right
    step_end
CherrygroveCity_TourShoreGOLD:
    walk_fast_down
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_down
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_up
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_down
    walk_fast_left
    step_end
CherrygroveCity_TourShoreGOLDFace:
    face_right
    step_end
CherrygroveCity_TourShoreKESTRA:
    walk_fast_right
    walk_fast_down
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_down
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_up
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_down
    step_end
CherrygroveCity_TourShoreKESTRAFace:
    face_left
    step_end
CherrygroveCity_TourShorePLAYER:
    walk_fast_right
    walk_fast_right
    walk_fast_down
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_down
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_up
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    walk_fast_left
    step_end
CherrygroveCity_TourShorePLAYERFace:
    face_down
    step_end
CherrygroveCity_TourHouseGOLD:
    walk_fast_down
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_up
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    step_end
CherrygroveCity_TourHouseGOLDFace:
    face_left
    step_end
CherrygroveCity_TourHouseKESTRA:
    walk_fast_left
    walk_fast_down
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_up
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    step_end
CherrygroveCity_TourHouseKESTRAFace:
    face_right
    step_end
CherrygroveCity_TourHousePLAYER:
    walk_fast_down
    walk_fast_left
    walk_fast_down
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_up
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    step_end
CherrygroveCity_TourHousePLAYERFace:
    face_right
    step_end
CherrygroveCity_KestraInsists:
    .string "KESTRA: Aren't you going to\ngive us our very first POKéMON\lnow?!$"
CherrygroveCity_GoldHesitates:
    .string "GOLD: Uh...$"
CherrygroveCity_KestraChampions:
    .string "KESTRA: Come onnnn! That's\nwhat Champions doooo, right?\pRight, {PLAYER}?!$"
CherrygroveCity_GoldRelents:
    .string "GOLD: Well, uh... I mean,\nI suppose so...$"
CherrygroveCity_KestraCheers:
    .string "KESTRA: Yaaaay! My HERO!$"
CherrygroveCity_GoldWait:
    .string "GOLD: Uh, OK. Wait right here.$"
CherrygroveCity_GoldPromise:
    .string "GOLD: OK, here we go.\pThese three POKéMON are very\nspecial to me.\pYou can each pick one, but\npromise to take good care of\lthem, OK?$"
CherrygroveCity_KestraPickFirst:
    .string "KESTRA: Yaaaay! {PLAYER},\nyou go first!$"
CherrygroveCity_KestraCounter:
    .string "KESTRA: Then I'm taking THIS\none!\pType advantage, right out of\nthe gate. Nothing personal.$"
CherrygroveCity_GoldTools:
    .string "GOLD: Before you go tearing\noff--here. You'll want these.\pRunning Shoes, so I don't have\nto watch you amble off.\pAnd a Map Card for your\nPOKéGEAR, so getting lost\lstops being an excuse.$"
CherrygroveCity_KestraRace:
    .string "KESTRA: First stop, Professor\nELM's lab in NEW BARK!\pLast one there is a SLOWPOKE!\nSmell ya later, {PLAYER}!$"
CherrygroveCity_GoldElm:
    .string "GOLD: I rang Professor ELM.\nHe'll fix you both up with a DEX.\pROUTE 29, straight east. You\nshould keep an eye on her...\pWelp. TYPHLOSION and I have\nsome gardening to do. Good luck.$"
CherrygroveCity_GoldAfterStarterText:
    .string "GOLD: Hm? Just talking things\nover with TYPHLOSION.\pThose CHERI trees need sun...\nWhere's my old squirt bottle?$"
CherrygroveCity_GoldWelcomeBack:
    .string "GOLD: There you two are.\nPOKéDEXES and everything.\pNow, before you set off,\nthere's a thing or two I want--$"
CherrygroveCity_KestraDeparts:
    .string "KESTRA: --VIOLET CITY! That's\nwhere the Gym is, right?\pAnd the school? No time to\nwaste. First Badge won't win\litself!\pSee you on the road, slowpoke!\nTry to keep up!$"
CherrygroveCity_GoldWatchingKestra:
    .string "GOLD: ...And there she goes.\pHalf a step ahead of her own\nbrain. Always was.\pBut you stuck around to hear\nthe rest. Come here a second.$"
CherrygroveCity_GoldCatchIntro:
    .string "GOLD: In a real battle, wear\nthe wild one down first.\pA tired POKéMON comes\nquietly. Don't knock it out!\pFor this practice, just\nthrow the BALL yourself.$"
CherrygroveCity_GoldCatchLesson:
    .string "GOLD: There you go. Your\nfirst throw! Hear that click?\pYou never quite stop chasing\nthat feeling. Trust me.$"
CherrygroveCity_GoldGift:
    .string "GOLD: Here. Take these to get\nyou started.\pThe Marts sell more, but a\ngood Trainer never lets their\lpack run empty.$"
CherrygroveCity_GoldLastAdvice:
    .string "GOLD: Head for VIOLET CITY.\nThere's a whole university now.\pTypes, items, battling--they'll\nteach you everything I'd fumble\ltrying to explain.$"
CherrygroveCity_GoldDontRush:
    .string "GOLD: But take it from someone\nwho's been there: don't rush.\pThe road goes fast enough on\nits own. Enjoy every step.\pNow go say goodbye to your\nmother before you leave.$"
CherrygroveCity_GoldBagFullText:
    .string "GOLD: Make room in your Bag,\nthen come back for the Balls.$"

CherrygroveCity_CastSilver::
    @ Silver leaves in the opening scene before control returns to the player.
    end
CherrygroveCity_Murkrow::
    end
CherrygroveCity_BattleMon::
    end

CherrygroveCity_CastKestra::
    lock
    faceplayer
    goto_if_ge VAR_APOC_CHAPTER_STAGE, 2, CherrygroveCity_KestraRepeat
    call CherrygroveCity_FirstMeeting
    release
    end
CherrygroveCity_FirstMeeting:
    applymovement LOCALID_PLAYER, CherrygroveCity_PlayerMeetsKestra
    waitmovement 0
    applymovement LOCALID_CAST_KESTRA, CherrygroveCity_KestraFacesPlayer
    waitmovement 0
    msgbox CherrygroveCity_KestraHello, MSGBOX_DEFAULT
    msgbox CherrygroveCity_KestraNamePrompt, MSGBOX_DEFAULT
    closemessage
    special ApocChapter_NamePlayer
    msgbox CherrygroveCity_KestraNameReply, MSGBOX_DEFAULT
    msgbox CherrygroveCity_KestraDream, MSGBOX_DEFAULT
    msgbox CherrygroveCity_KestraRuns, MSGBOX_DEFAULT
    closemessage
    applymovement LOCALID_CAST_KESTRA, CherrygroveCity_KestraRunsNorth
    waitmovement 0
    setvar VAR_APOC_CHAPTER_STAGE, 2
    setflag FLAG_APOC_KESTRA_NORTH
    clearflag FLAG_APOC_ROUTE_KESTRA_HIDDEN
    removeobject LOCALID_CAST_KESTRA
    return
CherrygroveCity_KestraRepeat:
    msgbox CherrygroveCity_KestraHello, MSGBOX_DEFAULT
    release
    end
CherrygroveCity_KestraHello:
    .string "KESTRA: OK, OK--where are my\nmanners? I'm KESTRA.\pBorn here, raised here. I know\nevery cobble in this town.\pAnd you--nope. Don't know you.\nI'd remember a new face.$"
CherrygroveCity_KestraNamePrompt:
    .string "KESTRA: New face. So?\nWhat do I call you?$"
CherrygroveCity_KestraNameReply:
    .string "KESTRA: {PLAYER}.\p{PLAYER}! Ha--good name.\pI'll be hollering it across\nbattlefields, so that's lucky.$"
CherrygroveCity_KestraDream:
    .string "KESTRA: I've wanted ONE thing\nsince I could walk.\pTo be like him. Champion\nSILVER. The best there is.\pHe battled in MY town today.\nThat has GOT to be a sign.$"
CherrygroveCity_KestraRuns:
    .string "KESTRA: Standing still is for\npeople who've already made it.\pCome on, {PLAYER}. The whole\nregion's out THIS way.\pTry to keep up, partner!$"
CherrygroveCity_KestraRunsNorth:
    walk_fast_up
    walk_fast_up
    walk_fast_up
    step_end
CherrygroveCity_PlayerMeetsKestra:
    walk_fast_left
    walk_fast_down
    walk_fast_down
    walk_fast_down
    walk_fast_right
    face_up
    step_end
CherrygroveCity_KestraFacesPlayer:
    face_down
    step_end
CherrygroveCity_KestraRunsEast:
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    step_end
CherrygroveCity_KestraRunsWest:
    walk_fast_left
    walk_fast_left
    walk_fast_left
    step_end

CherrygroveCity_CompareHoenn::
    lock
    faceplayer
    msgbox CherrygroveCity_CompareHoenn_Text, MSGBOX_DEFAULT
    release
    end

CherrygroveCity_CompareHoenn_Text::
    .string "The sea breeze reminds me of HOENN.$"

CherrygroveCity_CompareKanto::
    lock
    faceplayer
    msgbox CherrygroveCity_CompareKanto_Text, MSGBOX_DEFAULT
    release
    end

CherrygroveCity_CompareKanto_Text::
    .string "I traveled here from KANTO.\nIt is a lovely place to take a break.$"

CherrygroveCity_CompareJohto::
    lock
    faceplayer
    msgbox CherrygroveCity_CompareJohto_Text, MSGBOX_DEFAULT
    release
    end

CherrygroveCity_CompareJohto_Text::
    .string "The flowers look beautiful today!$"

CherrygroveCity_CompareSinnoh::
    lock
    faceplayer
    msgbox CherrygroveCity_CompareSinnoh_Text, MSGBOX_DEFAULT
    release
    end

CherrygroveCity_CompareSinnoh_Text::
    .string "It is much warmer here than SINNOH.$"

CherrygroveCity_CompareUnova::
    lock
    faceplayer
    msgbox CherrygroveCity_CompareUnova_Text, MSGBOX_DEFAULT
    release
    end

CherrygroveCity_CompareUnova_Text::
    .string "I came all the way from UNOVA.\nThe quiet here is wonderful.$"
