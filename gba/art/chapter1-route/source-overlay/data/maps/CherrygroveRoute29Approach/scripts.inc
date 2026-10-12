CherrygroveRoute29Approach_MapScripts::
    map_script MAP_SCRIPT_ON_TRANSITION, CherrygroveRoute29Approach_PositionKestra
    .byte 0
CherrygroveRoute29Approach_PositionKestra:
    goto_if_ne VAR_APOC_CHAPTER_STAGE, 4, CherrygroveRoute29Approach_HideKestra
    goto_if_set FLAG_APOC_ROUTE29_KESTRA_HIDDEN, CherrygroveRoute29Approach_KestraPositioned
    clearflag FLAG_APOC_ROUTE29_KESTRA_HIDDEN
CherrygroveRoute29Approach_KestraPositioned:
    end
CherrygroveRoute29Approach_HideKestra:
    setflag FLAG_APOC_ROUTE29_KESTRA_HIDDEN
    end

CherrygroveRoute29Approach_FirstGrass::
    goto_if_set FLAG_APOC_ROUTE29_KESTRA_HIDDEN, CherrygroveRoute29Approach_EndGrass
    lockall
    getplayerxy VAR_0x8004, VAR_0x8005
    call_if_eq VAR_0x8005, 19, CherrygroveRoute29Approach_PlayerAligns
    applymovement LOCALID_PLAYER, CherrygroveRoute29Approach_PlayerFacesKestra
    applymovement LOCALID_ROUTE29_KESTRA, CherrygroveRoute29Approach_KestraApproaches
    waitmovement 0
    msgbox CherrygroveRoute29Approach_GrassText, MSGBOX_DEFAULT
    msgbox CherrygroveRoute29Approach_RaceText, MSGBOX_DEFAULT
    closemessage
    applymovement LOCALID_ROUTE29_KESTRA, CherrygroveRoute29Approach_KestraRuns
    waitmovement 0
    setflag FLAG_APOC_ROUTE29_KESTRA_HIDDEN
    removeobject LOCALID_ROUTE29_KESTRA
    releaseall
CherrygroveRoute29Approach_EndGrass:
    end
CherrygroveRoute29Approach_Kestra::
    msgbox CherrygroveRoute29Approach_GrassText, MSGBOX_NPC
    end
CherrygroveRoute29Approach_KestraApproaches:
    walk_fast_down
    walk_fast_left
    face_left
    step_end
CherrygroveRoute29Approach_PlayerAligns:
    applymovement LOCALID_PLAYER, CherrygroveRoute29Approach_PlayerStepsUp
    waitmovement 0
    return
CherrygroveRoute29Approach_PlayerStepsUp:
    walk_fast_up
    step_end
CherrygroveRoute29Approach_PlayerFacesKestra:
    face_right
    step_end
CherrygroveRoute29Approach_KestraRuns:
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
CherrygroveRoute29Approach_GrassText:
    .string "KESTRA: There it is. Tall\ngrass! GOLD warned us, right?\pI've waited my whole life\nfor this part. Let's see what\lyour starter can do!$"
CherrygroveRoute29Approach_RaceText:
    .string "KESTRA: First one to NEW\nBARK wins!\pLoser gets no bragging\nrights at all. See you there!$"
