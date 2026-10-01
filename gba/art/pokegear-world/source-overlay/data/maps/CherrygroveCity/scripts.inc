CherrygroveCity_MapScripts::
    map_script MAP_SCRIPT_ON_TRANSITION, CherrygroveCity_PositionCast
    map_script MAP_SCRIPT_ON_FRAME_TABLE, CherrygroveCity_OnFrame
    .byte 0

CherrygroveCity_PositionCast:
    call_if_eq VAR_APOC_CHAPTER_STAGE, 3, CherrygroveCity_CeremonyPosition
    end
CherrygroveCity_CeremonyPosition:
    setobjectxyperm LOCALID_CAST_KESTRA, 47, 19
    setobjectmovementtype LOCALID_CAST_KESTRA, MOVEMENT_TYPE_FACE_RIGHT
    setobjectxyperm LOCALID_CAST_GOLD, 49, 20
    setobjectmovementtype LOCALID_CAST_GOLD, MOVEMENT_TYPE_FACE_LEFT
    return

CherrygroveCity_OnFrame:
    map_script_2 VAR_APOC_CHAPTER_STAGE, 0, CherrygroveCity_SilverDeparture
    .2byte 0

CherrygroveCity_SilverDeparture:
    goto_if_lt VAR_APOC_HOME_STAGE, 4, CherrygroveCity_NoChapterScene
    setflag FLAG_APOC_ROUTE_KESTRA_HIDDEN
    setflag FLAG_APOC_ROUTE_GOLD_HIDDEN
    lockall
    applymovement LOCALID_PLAYER, CherrygroveCity_FaceRight
    waitmovement 0
    msgbox CherrygroveCity_BattleEnd, MSGBOX_DEFAULT
    msgbox CherrygroveCity_SilverFarewell, MSGBOX_DEFAULT
    msgbox CherrygroveCity_GoldReply, MSGBOX_DEFAULT
    msgbox CherrygroveCity_SilverLeaves, MSGBOX_DEFAULT
    setflag FLAG_APOC_SILVER_DEPARTED
    removeobject LOCALID_CAST_SILVER
    setvar VAR_APOC_CHAPTER_STAGE, 1
    releaseall
    end
CherrygroveCity_NoChapterScene:
    end
CherrygroveCity_FaceRight:
    walk_in_place_fast_right
    step_end
CherrygroveCity_BattleEnd:
    .string "The last exchange ends in a flash.\pSILVER wins. The crowd cheers!$"
CherrygroveCity_SilverFarewell:
    .string "SILVER: Still got it, GOLD. You're\ngetting a little rusty out here!$"
CherrygroveCity_GoldReply:
    .string "GOLD: Maybe. I like the quiet.\nGood seeing you, old friend.$"
CherrygroveCity_SilverLeaves:
    .string "SILVER waves to GOLD, then flies\naway. KESTRA can hardly speak.$"

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
    .string "The sea breeze feels nice today.$"

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
    goto_if_ge VAR_APOC_CHAPTER_STAGE, 4, CherrygroveCity_GoldAfterStarter
    goto_if_eq VAR_APOC_CHAPTER_STAGE, 3, CherrygroveCity_GoldStarter
    msgbox CherrygroveCity_GoldBeforeRescue, MSGBOX_DEFAULT
    release
    end

CherrygroveCity_GoldBeforeRescue:
    .string "GOLD: KESTRA went north? I'll\nkeep an eye on the route.$"

CherrygroveCity_GoldStarter:
    msgbox CherrygroveCity_GoldTour, MSGBOX_DEFAULT
    msgbox CherrygroveCity_KestraInsists, MSGBOX_DEFAULT
    msgbox CherrygroveCity_GoldPromise, MSGBOX_DEFAULT
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
    setflag FLAG_APOC_KESTRA_NORTH
    removeobject LOCALID_CAST_KESTRA
    msgbox CherrygroveCity_GoldTools, MSGBOX_DEFAULT
    msgbox CherrygroveCity_GoldElm, MSGBOX_DEFAULT
    release
    end
CherrygroveCity_GoldAfterStarter:
    msgbox CherrygroveCity_GoldAfterStarterText, MSGBOX_DEFAULT
    release
    end
CherrygroveCity_GoldTour:
    .string "GOLD: Let's see. The Mart is up\nthere; the Center is beside it.\pI never was much of a guide.$"
CherrygroveCity_KestraInsists:
    .string "KESTRA: Aren't Champions meant\nto give us our first POKéMON?$"
CherrygroveCity_GoldPromise:
    .string "GOLD: ...All right. These three\nare very special to me.\pPromise you'll care for yours.$"
CherrygroveCity_GoldTools:
    .string "GOLD: Running Shoes, and a Map\nCard for your new POKéGEAR.\pI've saved my number, too.$"
CherrygroveCity_GoldElm:
    .string "GOLD: Elm's institute in NEW BARK\ncan give you a POKéDEX.\pTake your time getting there.$"
CherrygroveCity_GoldAfterStarterText:
    .string "GOLD: Typhlosion and I have some\ngardening to get back to.$"

CherrygroveCity_CastSilver::
    @ Silver leaves in the opening scene before control returns to the player.
    end

CherrygroveCity_CastKestra::
    lock
    faceplayer
    goto_if_ge VAR_APOC_CHAPTER_STAGE, 2, CherrygroveCity_KestraRepeat
    msgbox CherrygroveCity_KestraHello, MSGBOX_DEFAULT
    msgbox CherrygroveCity_KestraNamePrompt, MSGBOX_DEFAULT
    closemessage
    special ApocChapter_NamePlayer
    msgbox CherrygroveCity_KestraNameReply, MSGBOX_DEFAULT
    setvar VAR_APOC_CHAPTER_STAGE, 2
    setflag FLAG_APOC_KESTRA_NORTH
    clearflag FLAG_APOC_ROUTE_KESTRA_HIDDEN
    removeobject LOCALID_CAST_KESTRA
    release
    end
CherrygroveCity_KestraRepeat:
    msgbox CherrygroveCity_KestraHello, MSGBOX_DEFAULT
    release
    end
CherrygroveCity_KestraHello:
    .string "KESTRA: Did you see that? GOLD\nand SILVER, right here!\pI'm KESTRA. You just moved in?$"
CherrygroveCity_KestraNamePrompt:
    .string "Wait, I don't know your name!\nWhat should I call you?$"
CherrygroveCity_KestraNameReply:
    .string "{PLAYER}! Nice to meet you.\pI'm going north to find a\nPOKéMON of my own. Come on!$"

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
