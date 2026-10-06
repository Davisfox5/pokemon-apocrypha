FloccesyTown_MapScripts::
	.byte 0

FloccesyTown_Visitor::
	lock
	faceplayer
	msgbox FloccesyTown_VisitorText, MSGBOX_DEFAULT
	release
	end

FloccesyTown_VisitorText::
	.string "The clock keeps time for us.\nWelcome to FLOCCESY TOWN!$"
