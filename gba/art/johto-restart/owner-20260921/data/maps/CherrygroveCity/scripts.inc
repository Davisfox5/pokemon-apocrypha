CherrygroveCity_MapScripts::
    .byte 0

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
    msgbox CherrygroveCity_CastGold_Text, MSGBOX_DEFAULT
    release
    end

CherrygroveCity_CastGold_Text::
    .string "GOLD$"

CherrygroveCity_CastSilver::
    lock
    faceplayer
    msgbox CherrygroveCity_CastSilver_Text, MSGBOX_DEFAULT
    release
    end

CherrygroveCity_CastSilver_Text::
    .string "SILVER$"

CherrygroveCity_CastKestra::
    lock
    faceplayer
    msgbox CherrygroveCity_CastKestra_Text, MSGBOX_DEFAULT
    release
    end

CherrygroveCity_CastKestra_Text::
    .string "KESTRA$"

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
