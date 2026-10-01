FloccesyPokemonCenter_MapScripts::
    .byte 0

FloccesyPokemonCenter_Nurse::
    setvar VAR_0x800B, LOCALID_NURSE
    call Common_EventScript_PkmnCenterNurse
    waitmessage
    waitbuttonpress
    release
    end
