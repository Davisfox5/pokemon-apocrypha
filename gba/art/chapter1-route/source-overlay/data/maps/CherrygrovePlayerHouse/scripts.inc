CherrygrovePlayerHouse_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, CherrygrovePlayerHouse_PositionMom
	map_script MAP_SCRIPT_ON_FRAME_TABLE, CherrygrovePlayerHouse_OnFrame
	.byte 0
CherrygrovePlayerHouse_PositionMom:
	call_if_eq VAR_APOC_HOME_STAGE, 0, CherrygrovePlayerHouse_MomWelcomePosition
	call_if_eq VAR_APOC_HOME_STAGE, 1, CherrygrovePlayerHouse_MomDoorPosition
	call_if_eq VAR_APOC_HOME_STAGE, 2, CherrygrovePlayerHouse_MomStairsPosition
	call_if_ge VAR_APOC_HOME_STAGE, 4, CherrygrovePlayerHouse_MomUnpackingPosition
	end
CherrygrovePlayerHouse_MomWelcomePosition:
	setobjectxyperm LOCALID_MOTHER, 5, 4
	setobjectmovementtype LOCALID_MOTHER, MOVEMENT_TYPE_FACE_LEFT
	return
CherrygrovePlayerHouse_MomDoorPosition:
	setobjectxyperm LOCALID_MOTHER, 2, 7
	setobjectmovementtype LOCALID_MOTHER, MOVEMENT_TYPE_FACE_UP
	return
CherrygrovePlayerHouse_MomStairsPosition:
	setobjectxyperm LOCALID_MOTHER, 3, 3
	setobjectmovementtype LOCALID_MOTHER, MOVEMENT_TYPE_FACE_UP
	return
CherrygrovePlayerHouse_MomUnpackingPosition:
	setobjectxyperm LOCALID_MOTHER, 3, 5
	setobjectmovementtype LOCALID_MOTHER, MOVEMENT_TYPE_FACE_DOWN
	return
CherrygrovePlayerHouse_OnFrame:
	map_script_2 VAR_APOC_HOME_STAGE, 0, CherrygrovePlayerHouse_Opening
	map_script_2 VAR_APOC_HOME_STAGE, 2, CherrygrovePlayerHouse_Handoff
	map_script_2 VAR_APOC_CHAPTER_STAGE, 6, CherrygrovePlayerHouse_FarewellAuto
	.2byte 0
CherrygrovePlayerHouse_FarewellAuto:
	lockall
	@ Mom steps out from the moving boxes; the player meets her directly below.
	applymovement LOCALID_PLAYER, CherrygrovePlayerHouse_FarewellPlayer
	applymovement LOCALID_MOTHER, CherrygrovePlayerHouse_FarewellMother
	waitmovement 0
	goto CherrygrovePlayerHouse_Farewell
CherrygrovePlayerHouse_FarewellPlayer:
	walk_fast_up
	face_up
	step_end
CherrygrovePlayerHouse_FarewellMother:
	walk_fast_left
	face_down
	step_end
CherrygrovePlayerHouse_Opening:
	lockall
	fadescreen FADE_TO_BLACK
	msgbox CherrygrovePlayerHouse_Cold, MSGBOX_DEFAULT
	closemessage
	applymovement LOCALID_PLAYER, CherrygrovePlayerHouse_FaceRight
	applymovement LOCALID_MOTHER, CherrygrovePlayerHouse_FaceLeft
	waitmovement 0
	fadescreen FADE_FROM_BLACK
	msgbox CherrygrovePlayerHouse_Welcome, MSGBOX_DEFAULT
	closemessage
	applymovement LOCALID_MOTHER, CherrygrovePlayerHouse_MomToDoor
	waitmovement 0
	setobjectxyperm LOCALID_MOTHER, 2, 7
	setobjectmovementtype LOCALID_MOTHER, MOVEMENT_TYPE_FACE_UP
	setvar VAR_APOC_HOME_STAGE, 1
	releaseall
	end
CherrygrovePlayerHouse_Handoff:
	lockall
	applymovement LOCALID_PLAYER, CherrygrovePlayerHouse_HandoffPlayer
	waitmovement 0
	applymovement LOCALID_MOTHER, CherrygrovePlayerHouse_FaceLeft
	waitmovement 0
	msgbox CherrygrovePlayerHouse_GearText, MSGBOX_DEFAULT
	setflag FLAG_APOC_POKEGEAR
	closemessage
	applymovement LOCALID_MOTHER, CherrygrovePlayerHouse_MomToBoxes
	waitmovement 0
	setobjectxyperm LOCALID_MOTHER, 3, 5
	setobjectmovementtype LOCALID_MOTHER, MOVEMENT_TYPE_FACE_DOWN
	setvar VAR_APOC_HOME_STAGE, 4
	releaseall
	end
CherrygrovePlayerHouse_Mother::
	lock
	faceplayer
	goto_if_eq VAR_APOC_HOME_STAGE, 2, CherrygrovePlayerHouse_Handoff
	goto_if_eq VAR_APOC_HOME_STAGE, 1, CherrygrovePlayerHouse_Reminder
	goto_if_eq VAR_APOC_CHAPTER_STAGE, 6, CherrygrovePlayerHouse_Farewell
	goto_if_ge VAR_APOC_CHAPTER_STAGE, 7, CherrygrovePlayerHouse_SavingsVisit
	msgbox CherrygrovePlayerHouse_After, MSGBOX_DEFAULT
	release
	end
CherrygrovePlayerHouse_Farewell:
	msgbox CherrygrovePlayerHouse_FarewellText, MSGBOX_DEFAULT
	msgbox CherrygrovePlayerHouse_SaveOffer, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, YES, CherrygrovePlayerHouse_EnableSavings
	setvar VAR_APOC_MOM_SAVE_ENABLED, 0
	msgbox CherrygrovePlayerHouse_SaveNo, MSGBOX_DEFAULT
	goto CherrygrovePlayerHouse_FarewellDone
CherrygrovePlayerHouse_EnableSavings:
	setvar VAR_APOC_MOM_SAVE_ENABLED, 1
	msgbox CherrygrovePlayerHouse_SaveYes, MSGBOX_DEFAULT
CherrygrovePlayerHouse_FarewellDone:
	setvar VAR_APOC_CHAPTER_STAGE, 7
	msgbox CherrygrovePlayerHouse_FarewellEnd, MSGBOX_DEFAULT
	releaseall
	end
CherrygrovePlayerHouse_SavingsVisit:
	special ApocChapter_HasSavings
	goto_if_eq VAR_RESULT, TRUE, CherrygrovePlayerHouse_AskWithdraw
	goto CherrygrovePlayerHouse_AskSave
CherrygrovePlayerHouse_AskWithdraw:
	msgbox CherrygrovePlayerHouse_WithdrawOffer, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, YES, CherrygrovePlayerHouse_Withdraw
CherrygrovePlayerHouse_AskSave:
	msgbox CherrygrovePlayerHouse_SaveOffer, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, YES, CherrygrovePlayerHouse_EnableSavingsAgain
	setvar VAR_APOC_MOM_SAVE_ENABLED, 0
	goto CherrygrovePlayerHouse_SavingsDone
CherrygrovePlayerHouse_EnableSavingsAgain:
	setvar VAR_APOC_MOM_SAVE_ENABLED, 1
	goto CherrygrovePlayerHouse_SavingsDone
CherrygrovePlayerHouse_Withdraw:
	special ApocChapter_WithdrawSavings
	goto_if_eq VAR_RESULT, FALSE, CherrygrovePlayerHouse_WalletFull
	msgbox CherrygrovePlayerHouse_WithdrawDone, MSGBOX_DEFAULT
	goto CherrygrovePlayerHouse_AskSave
CherrygrovePlayerHouse_WalletFull:
	msgbox CherrygrovePlayerHouse_WalletFullText, MSGBOX_DEFAULT
CherrygrovePlayerHouse_SavingsDone:
	msgbox CherrygrovePlayerHouse_SavingsEnd, MSGBOX_DEFAULT
	release
	end
CherrygrovePlayerHouse_Reminder:
	msgbox CherrygrovePlayerHouse_Upstairs, MSGBOX_DEFAULT
	releaseall
	end
CherrygrovePlayerHouse_ExitGuard::
	lockall
	getplayerxy VAR_0x8004, VAR_0x8005
	call_if_eq VAR_0x8004, 3, CherrygrovePlayerHouse_AlignDoor
	applymovement LOCALID_PLAYER, CherrygrovePlayerHouse_FaceDown
	applymovement LOCALID_MOTHER, CherrygrovePlayerHouse_FaceUp
	waitmovement 0
	msgbox CherrygrovePlayerHouse_Upstairs, MSGBOX_DEFAULT
	closemessage
	applymovement LOCALID_PLAYER, CherrygrovePlayerHouse_Back
	waitmovement 0
	releaseall
	end
CherrygrovePlayerHouse_AlignDoor:
	applymovement LOCALID_PLAYER, CherrygrovePlayerHouse_StepLeft
	waitmovement 0
	return
CherrygrovePlayerHouse_StepLeft:
	walk_left
	step_end
CherrygrovePlayerHouse_MomToDoor:
	walk_left
	walk_left
	walk_left
	walk_down
	walk_down
	walk_down
	face_up
	step_end
CherrygrovePlayerHouse_HandoffPlayer:
	walk_down
	face_right
	step_end
CherrygrovePlayerHouse_MomToBoxes:
	walk_down
	walk_down
	face_down
	step_end
CherrygrovePlayerHouse_FaceRight:
	face_right
	step_end
CherrygrovePlayerHouse_FaceLeft:
	face_left
	step_end
CherrygrovePlayerHouse_FaceDown:
	face_down
	step_end
CherrygrovePlayerHouse_FaceUp:
	face_up
	step_end
CherrygrovePlayerHouse_Back:
	walk_up
	step_end
CherrygrovePlayerHouse_BoxOne::
	msgbox CherrygrovePlayerHouse_BoxText, MSGBOX_SIGN
	end
CherrygrovePlayerHouse_BoxTwo::
	msgbox CherrygrovePlayerHouse_BoxText, MSGBOX_SIGN
	end
CherrygrovePlayerHouse_Cold:
	.string "...\p......\pMOM: ...Honey. Hey--we're here.\nWake up, sleepyhead.\pMOM: We made it. Our new home!\pI still can't believe we\nactually did it.$"
CherrygrovePlayerHouse_Welcome:
	.string "MOM: All the way from Kalos...\nand now this is home.\pA whole new region. A fresh start,\nfor both of us.\pThe movers got everything here\nin one piece. More or less.\pGo on up and see your new room.\nI had your things set up first.\pYour PC should be ready. Get it\nsorted while I unpack down here.$"
CherrygrovePlayerHouse_Upstairs:
	.string "MOM: Go see your room upstairs.\nYour PC should be ready!$"
CherrygrovePlayerHouse_GearText:
	.string "MOM: There you are. Settling in?\pOh--this came for you.\nYour very own POKéGEAR.\pMap, phone, radio, clock--\nall in one.\pYou can open your BAG, check\nyour POKéGEAR, or SAVE here.\pCall me anytime. I mean it.$"
CherrygrovePlayerHouse_After:
	.string "MOM: I'll keep unpacking here.\nGo on, have a look around.\pCall me anytime, honey.$"
CherrygrovePlayerHouse_FarewellText:
	.string "MOM: So today's the day.\nMy little Trainer, off to see\lthe world.\pGOLD told me he set you\nstraight on the important things.\pOh--before you go. Let me do\nwhat mothers do.\pWhile you're away, I can look\nafter your money for you.\pEvery time you win a battle,\nI'll tuck a little aside.\pSafe and sound, waiting for\nwhen you come home.$"
CherrygrovePlayerHouse_SaveOffer:
	.string "MOM: Should I hold onto some\nof your prize money for you?$"
CherrygrovePlayerHouse_SaveYes:
	.string "MOM: Then it's settled. I'll\nkeep it safe for you.\pCall me anytime. I love\nhearing your voice.$"
CherrygrovePlayerHouse_SaveNo:
	.string "MOM: All right, all right.\nYou'll manage your own coin.\pJust don't spend it all on\nPOKé BALLS and vending machines!$"
CherrygrovePlayerHouse_FarewellEnd:
	.string "MOM: There's a whole world\nout there, and it's yours to walk.\pBe kind. Be brave. And every\nnow and then, come home.\pYour friend's probably halfway\nto VIOLET already. Go on!$"
CherrygrovePlayerHouse_WithdrawOffer:
	.string "MOM: I have some of your\nsavings. Take them now?$"
CherrygrovePlayerHouse_WithdrawDone:
	.string "MOM: Here you go. Spend it\non something useful!$"
CherrygrovePlayerHouse_WalletFullText:
	.string "MOM: Your wallet is full.\nI'll keep it safe for now.$"
CherrygrovePlayerHouse_SavingsEnd:
	.string "MOM: You know where to find me.\nTake care out there.$"
CherrygrovePlayerHouse_BoxText:
	.string "A moving box from Kalos.\nThere's still plenty to unpack.$"
