CherrygroveGoldHouse_MapScripts::
    map_script MAP_SCRIPT_ON_TRANSITION, CherrygroveGoldHouse_PositionGold
    .byte 0
CherrygroveGoldHouse_PositionGold:
    goto_if_eq VAR_APOC_CHAPTER_STAGE, 4, CherrygroveGoldHouse_GoldHome
    setflag FLAG_APOC_GOLD_HOUSE_HIDDEN
    end
CherrygroveGoldHouse_GoldHome:
    clearflag FLAG_APOC_GOLD_HOUSE_HIDDEN
    end

CherrygroveGoldHouse_Gold::
    lock
    faceplayer
    msgbox CherrygroveGoldHouse_GoldText, MSGBOX_DEFAULT
    release
    end
CherrygroveGoldHouse_Typhlosion::
    msgbox CherrygroveGoldHouse_TyphlosionText, MSGBOX_NPC
    end
CherrygroveGoldHouse_GoldText:
    .string "GOLD: TYPHLOSION, do the\nCHERI trees need more sun?\pI could move the pots... if\nI can find my squirt bottle.\pOh! Didn't see you there.\nHow's your new partner?$"
CherrygroveGoldHouse_TyphlosionText:
    .string "TYPHLOSION watches GOLD\nsort a box of BERRIES.$"
