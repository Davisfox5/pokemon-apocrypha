SandgemTown_MapScripts::
	.byte 0

SandgemTown_Visitor::
	lock
	faceplayer
	msgbox SandgemTown_VisitorText, MSGBOX_DEFAULT
	release
	end

SandgemTown_VisitorText::
	.string "The sea breeze is cool here.\nSANDGEM is a peaceful place to walk.$"
