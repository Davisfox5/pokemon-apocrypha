@
@ DO NOT MODIFY THIS FILE! It is auto-generated from data/maps/CherrygroveCity/map.json
@

	.align 2

CherrygroveCity_ObjectEvents:
	object_event 1, OBJ_EVENT_GFX_JOHTO_WOMAN, 29, 20, 3, MOVEMENT_TYPE_WALK_UP_AND_DOWN, 0, 1, TRAINER_TYPE_NONE, 0, CherrygroveCity_Waterfront, 0
	object_event 2, OBJ_EVENT_GFX_JOHTO_MAN, 36, 8, 3, MOVEMENT_TYPE_WALK_LEFT_AND_RIGHT, 1, 0, TRAINER_TYPE_NONE, 0, CherrygroveCity_Commuter, 0
	object_event 3, OBJ_EVENT_GFX_JOHTO_BOY, 42, 24, 3, MOVEMENT_TYPE_WALK_LEFT_AND_RIGHT, 1, 0, TRAINER_TYPE_NONE, 0, CherrygroveCity_JohtoBoy, 0
	object_event 4, OBJ_EVENT_GFX_JOHTO_GIRL, 58, 20, 3, MOVEMENT_TYPE_WALK_LEFT_AND_RIGHT, 1, 0, TRAINER_TYPE_NONE, 0, CherrygroveCity_JohtoGirl, 0
	object_event 5, OBJ_EVENT_GFX_JOHTO_GOLD, 40, 18, 3, MOVEMENT_TYPE_WALK_SEQUENCE_UP_RIGHT_DOWN_LEFT, 1, 1, TRAINER_TYPE_NONE, 0, CherrygroveCity_CastGold, 0
	object_event 6, OBJ_EVENT_GFX_JOHTO_SILVER, 49, 24, 3, MOVEMENT_TYPE_WALK_SEQUENCE_UP_RIGHT_DOWN_LEFT, 1, 1, TRAINER_TYPE_NONE, 0, CherrygroveCity_CastSilver, 0
	object_event 7, OBJ_EVENT_GFX_JOHTO_KESTRA, 37, 22, 3, MOVEMENT_TYPE_WALK_LEFT_AND_RIGHT, 2, 0, TRAINER_TYPE_NONE, 0, CherrygroveCity_CastKestra, 0
	object_event 8, OBJ_EVENT_GFX_REGIONAL_HOENN, 48, 12, 3, MOVEMENT_TYPE_WALK_LEFT_AND_RIGHT, 1, 0, TRAINER_TYPE_NONE, 0, CherrygroveCity_CompareHoenn, 0
	object_event 9, OBJ_EVENT_GFX_REGIONAL_KANTO, 58, 18, 3, MOVEMENT_TYPE_WALK_SEQUENCE_UP_RIGHT_DOWN_LEFT, 1, 1, TRAINER_TYPE_NONE, 0, CherrygroveCity_CompareKanto, 0
	object_event 10, OBJ_EVENT_GFX_REGIONAL_JOHTO, 39, 12, 3, MOVEMENT_TYPE_WALK_SEQUENCE_UP_RIGHT_DOWN_LEFT, 1, 1, TRAINER_TYPE_NONE, 0, CherrygroveCity_CompareJohto, 0
	object_event 11, OBJ_EVENT_GFX_REGIONAL_SINNOH, 30, 22, 3, MOVEMENT_TYPE_WALK_SEQUENCE_UP_RIGHT_DOWN_LEFT, 1, 1, TRAINER_TYPE_NONE, 0, CherrygroveCity_CompareSinnoh, 0
	object_event 12, OBJ_EVENT_GFX_REGIONAL_UNOVA, 54, 29, 3, MOVEMENT_TYPE_WALK_LEFT_AND_RIGHT, 1, 0, TRAINER_TYPE_NONE, 0, CherrygroveCity_CompareUnova, 0

CherrygroveCity_MapWarps:
	warp_def 35, 17, 0, 0, MAP_CHERRYGROVE_PLAYER_HOUSE
	warp_def 46, 19, 0, 0, MAP_CHERRYGROVE_GOLD_HOUSE
	warp_def 56, 25, 0, 0, MAP_CHERRYGROVE_NEIGHBOR_HOUSE
	warp_def 34, 32, 0, 0, MAP_CHERRYGROVE_TRANSPLANT_HOUSE
	warp_def 43, 9, 0, 0, MAP_CHERRYGROVE_MART
	warp_def 53, 9, 0, 0, MAP_CHERRYGROVE_POKEMON_CENTER

CherrygroveCity_MapBGEvents:
	bg_sign_event 42, 15, 0, BG_EVENT_PLAYER_FACING_ANY, CherrygroveCity_TownSign

CherrygroveCity_MapEvents::
	map_events CherrygroveCity_ObjectEvents, CherrygroveCity_MapWarps, NULL, CherrygroveCity_MapBGEvents

