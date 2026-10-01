CherrygrovePlayerBedroom_MapScripts::
	.byte 0
CherrygrovePlayerBedroom_PC::
	lockall
	goto_if_set FLAG_APOC_PC_POTION, CherrygrovePlayerBedroom_PCMenu
	msgbox CherrygrovePlayerBedroom_PCText, MSGBOX_DEFAULT
	giveitem ITEM_POTION
	goto_if_eq VAR_RESULT, FALSE, CherrygrovePlayerBedroom_End
	setflag FLAG_APOC_PC_POTION
	setvar VAR_APOC_HOME_STAGE, 2
CherrygrovePlayerBedroom_PCMenu:
	closemessage
	special BedroomPC
	waitstate
CherrygrovePlayerBedroom_End:
	releaseall
	end
CherrygrovePlayerBedroom_PCText:
	.string "Your PC is ready to use.\pThere's a POTION tucked beside it,\nwith a note from MOM.$"
