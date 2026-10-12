NewBarkTown_MapScripts::
    map_script MAP_SCRIPT_ON_TRANSITION, NewBarkTown_PositionKestra
    map_script MAP_SCRIPT_ON_FRAME_TABLE, NewBarkTown_OnFrame
    .byte 0
NewBarkTown_PositionKestra:
    goto_if_ge VAR_APOC_CHAPTER_STAGE, 6, NewBarkTown_HideKestra
    goto_if_eq VAR_APOC_CHAPTER_STAGE, 5, NewBarkTown_KestraAtInstitute
    goto_if_ne VAR_APOC_CHAPTER_STAGE, 4, NewBarkTown_HideKestra
    goto_if_set FLAG_APOC_NEW_BARK_ARRIVAL_DONE, NewBarkTown_KestraAtInstitute
    clearflag FLAG_APOC_NEW_BARK_TOWN_KESTRA_HIDDEN
    setobjectxyperm LOCALID_NEW_BARK_TOWN_KESTRA, 4, 18
    end
NewBarkTown_KestraAtInstitute:
    clearflag FLAG_APOC_NEW_BARK_TOWN_KESTRA_HIDDEN
    setobjectxyperm LOCALID_NEW_BARK_TOWN_KESTRA, 27, 14
    setobjectmovementtype LOCALID_NEW_BARK_TOWN_KESTRA, MOVEMENT_TYPE_FACE_UP
    end
NewBarkTown_HideKestra:
    setflag FLAG_APOC_NEW_BARK_TOWN_KESTRA_HIDDEN
    end
NewBarkTown_OnFrame:
    map_script_2 VAR_APOC_CHAPTER_STAGE, 4, NewBarkTown_Arrival
    .2byte 0
NewBarkTown_Arrival:
    goto_if_set FLAG_APOC_NEW_BARK_ARRIVAL_DONE, NewBarkTown_ArrivalDone
    lockall
    applymovement LOCALID_PLAYER, NewBarkTown_WalkTogether
    applymovement LOCALID_NEW_BARK_TOWN_KESTRA, NewBarkTown_WalkTogether
    waitmovement 0
    applymovement LOCALID_PLAYER, NewBarkTown_FaceKestra
    applymovement LOCALID_NEW_BARK_TOWN_KESTRA, NewBarkTown_FacePlayer
    waitmovement 0
    msgbox NewBarkTown_ArrivalText, MSGBOX_DEFAULT
    closemessage
    applymovement LOCALID_NEW_BARK_TOWN_KESTRA, NewBarkTown_KestraRunsAhead
    waitmovement 0
    setflag FLAG_APOC_NEW_BARK_ARRIVAL_DONE
    setobjectxyperm LOCALID_NEW_BARK_TOWN_KESTRA, 27, 14
    setobjectmovementtype LOCALID_NEW_BARK_TOWN_KESTRA, MOVEMENT_TYPE_FACE_UP
    releaseall
NewBarkTown_ArrivalDone:
    end
NewBarkTown_WalkTogether:
    walk_fast_right
    walk_fast_right
    walk_fast_right
    step_end
NewBarkTown_FaceKestra:
    face_right
    step_end
NewBarkTown_FacePlayer:
    face_left
    step_end
NewBarkTown_KestraRunsAhead:
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    walk_fast_right
    step_end
NewBarkTown_ArrivalText:
    .string "KESTRA: We made it! ELM's\ninstitute is up ahead.\pCome on--GOLD said he\ncalled ahead for us!$"

NewBarkTown_Researcher::
    lock
    faceplayer
    msgbox NewBarkTown_ResearcherText, MSGBOX_DEFAULT
    release
    end
NewBarkTown_ResearcherText:
    .string "Grant review in an hour--\nI can't stop!\pHere for Professor ELM?\nEveryone is, lately.\pThe public wing is ahead.$"

NewBarkTown_Kestra::
    lock
    faceplayer
    goto_if_ge VAR_APOC_CHAPTER_STAGE, 5, NewBarkTown_KestraAfterElm
    msgbox NewBarkTown_KestraBeforeElmText, MSGBOX_DEFAULT
    release
    end
NewBarkTown_KestraAfterElm:
    msgbox NewBarkTown_KestraAfterElmText, MSGBOX_DEFAULT
    release
    end
NewBarkTown_KestraBeforeElmText:
    .string "KESTRA: ELM's institute!\pGOLD said he called ahead.\nCome on, let's go!$"
NewBarkTown_KestraAfterElmText:
    .string "KESTRA: Did you hear that?\nThe Champion started here!\pSame lab. Same professor.\nThat's going to be us.\pCome on--let's tell GOLD we're\nofficially Trainers!$"
