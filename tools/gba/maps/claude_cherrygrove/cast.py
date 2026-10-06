"""Residents, visitors and the custom cast: positions, movement and dialogue.

Ambient only: no flags, no story triggers. Lore-checked against DESIGN.md
(Chapter 1, Characters, Inter-Regional Exchange). Silver is seen, not spoken
to: interacting with him gives narration. One thought per message box.
"""

SIGNS = dict(
    TownSign='CHERRYGROVE CITY\\nCity of fragrant flowers.',
    NorthSign='ROUTE 30\\nNorth to VIOLET CITY',
    EastSign='ROUTE 29\\nEast to NEW BARK TOWN',
    GoldSign="GOLD'S HOUSE",
    WaterfrontSign='CHERRYGROVE PIER\\nBoats moored here.',
    ParkSign='BLOSSOM PARK\\nPlease keep off the beds.',
    LookoutSign='SEASIDE LOOKOUT\\nMind the railing.',
)

def walk(gfx, id, x, y, move, rx=0, ry=0, text=None, script=None):
    return dict(gfx=gfx, id=id, pos=(x, y), move=move, range=(rx, ry), text=text, script=script)

SILVER_SCRIPT = '''LABEL::
    lock
    faceplayer
    msgbox LABEL_Text, MSGBOX_DEFAULT
    release
    end

LABEL_Text:
    .string "SILVER is deep in conversation\\nwith GOLD.\\pHe does not seem to notice you.$"
'''

NPCS = [
    # Custom cast.
    walk('OBJ_EVENT_GFX_JOHTO_GOLD', 'Gold', 45, 13, 'MOVEMENT_TYPE_WANDER_AROUND', 1, 1,
         'GOLD: SILVER came by to\\nvisit. We had a battle.\\pI lost. He says I have\\ngotten rusty.\\pThat is fine by me.\\nIt was a good battle.'),
    walk('OBJ_EVENT_GFX_JOHTO_SILVER', 'Silver', 44, 15, 'MOVEMENT_TYPE_WALK_SEQUENCE_UP_RIGHT_DOWN_LEFT', 1, 1, script=SILVER_SCRIPT),
    walk('OBJ_EVENT_GFX_JOHTO_KESTRA', 'Kestra', 53, 21, 'MOVEMENT_TYPE_WALK_LEFT_AND_RIGHT', 2, 0,
         'KESTRA: Did you see that?\\nThat was SILVER!\\pThe CHAMPION, right here\\nin CHERRYGROVE!\\pI want to battle like\\nthat someday.'),
    # Johto residents.
    walk('OBJ_EVENT_GFX_JOHTO_WOMAN', 'Woman', 30, 26, 'MOVEMENT_TYPE_WANDER_AROUND', 2, 1,
         'The boats hardly go out\\nthese days.\\pMy husband still mends the\\nnets every morning.'),
    walk('OBJ_EVENT_GFX_JOHTO_MAN', 'Man', 38, 9, 'MOVEMENT_TYPE_WANDER_AROUND', 2, 1,
         'GOLD moved here for the\\nquiet.\\pWe see to it that he\\ngets it.'),
    walk('OBJ_EVENT_GFX_JOHTO_BOY', 'Boy', 41, 21, 'MOVEMENT_TYPE_WANDER_AROUND', 2, 2,
         'The petals fall all\\nthrough spring.\\pMy mom says not to track\\nthem into the house.'),
    walk('OBJ_EVENT_GFX_JOHTO_GIRL', 'Girl', 22, 20, 'MOVEMENT_TYPE_WALK_UP_AND_DOWN', 0, 2,
         'I walk the beach when the\\ntide is out.\\pYou can find shells if\\nyou look.'),
    # Visitors from the other regions.
    walk('OBJ_EVENT_GFX_REGIONAL_HOENN', 'Hoenn', 23, 12, 'MOVEMENT_TYPE_WANDER_AROUND', 1, 2,
         'I came from HOENN to see\\nJOHTO.\\pThe sea is colder here.\\nThe sand is just as soft.'),
    walk('OBJ_EVENT_GFX_REGIONAL_KANTO', 'Kanto', 56, 13, 'MOVEMENT_TYPE_WALK_LEFT_AND_RIGHT', 2, 0,
         "I'm from KANTO. It's not so\\nfar from here.\\pThe towns are bigger there.\\nI like it quiet here."),
    walk('OBJ_EVENT_GFX_REGIONAL_JOHTO', 'Johto', 41, 9, 'MOVEMENT_TYPE_WALK_LEFT_AND_RIGHT', 3, 0,
         'The POKEMON CENTER is here\\nand the MART is next door.\\pIt is a small town. Nothing\\nis hard to find.'),
    walk('OBJ_EVENT_GFX_REGIONAL_SINNOH', 'Sinnoh', 16, 27, 'MOVEMENT_TYPE_FACE_LEFT', 0, 0,
         'Back home in SINNOH the sea\\nis grey and the wind bites.\\pI could stand on this pier\\nall day.'),
    walk('OBJ_EVENT_GFX_REGIONAL_UNOVA', 'Unova', 44, 25, 'MOVEMENT_TYPE_WANDER_AROUND', 2, 1,
         'UNOVA has parks too, but\\nnothing like this one.\\pAll these trees are pink!'),
]
