"""Dragon's Den, for the Johto cave kit (tools/gba/maps/johto_caves): HGSS zones D44R0101-0102.

The entrance off Blackthorn (a lit exit, a ladder down) and the den itself (a lake round the
shrine, the ladder up). The shrine's inside (D44R0103) is an interior and is not built: its door
stays solid, as the towns keep doors whose interiors do not exist yet.
"""
NAME = "Dragon's Den"
ART = 'dragons-den'                       # gba/art/<ART>
TOOL = 'dragons_den'                      # tools/gba/maps/<TOOL>
AREA_BANK = 86                            # HGSS map header areaDataBank (both floors)
FLOORS = {  # side: HGSS header, matrix, zone event file; native map name and id
    'entrance': dict(header='MAP_DRAGONS_DEN_ENTRANCE', matrix='map_matrix_0145_D44R0101.bin', zone='122_D44R0101',
                     name='DragonsDen_Entrance', id='MAP_DRAGONS_DEN_ENTRANCE'),
    'den': dict(header='MAP_DRAGONS_DEN', matrix='map_matrix_0146_D44R0102.bin', zone='239_D44R0102',
                name='DragonsDen', id='MAP_DRAGONS_DEN'),
}
# Textures (HGSS texture set 86): rock ramp, cave floor, the den's moss floor
ROCK_TEX = ('dwall_s', 'dcliff01', 'dallpeak_p')
FLOOR_TEX = 'droad01'
FLOOR2 = dict(tex='d17_rdr1', prefixes=('d17_rd',))   # the den's mossy floor: its cells take its own tones
# HGSS's own pixels kept where Gen 3 has no piece (as Route 45's cascades and Mt. Mortar's climbing holds):
# models (by their texture names) and ground materials
KEEP_MODELS = ('uzushio', 'd17_h02', 'd17_h01', 'board_cd')   # the whirlpool, the shrine on its deck, its door, its sign
KEEP_MATERIALS = ('d17_h04',)            # the wooden pier off the north stairs, the wreck in the lake
DECK_MATERIALS = ('d17_h02', 'd17_h03', 'd17_h04', 'd17_h05', 'd17_h06')
SEA_ROCKS = ('sea_rock', 'sea_rock_m')    # rocks standing in the lake: the routes' boulder in their own tones, on water
SMALL_ROCKS = ('d_rock01s',)              # small rocks on the floor: the routes' boulder in their own tones
EXTRA_CLASS = {'d17_rdr1': 1, 'd17_rdr2': 1, 'd17_rdn1': 1, 'd17_rdn2': 1, 'd17_rdbd': 1, 'd17_h04': 1,
               'sea_rock': 5, 'sea_rock_m': 5}
UNBUILT = {'MAP_DRAGONS_DEN_SHRINE'}      # warps to interiors not built: their cells stay solid, no warp
# The town and its mouth (native wiring only: another session's map)
TOWN = dict(map='BlackthornCity', id='MAP_BLACKTHORN_CITY', hgss='MAP_BLACKTHORN', cell=(32, 4), metatile=521,
            primary='cherrygrove', secondary='blackthorn_city', size=(64, 64), pair=('entrance', 0))
# Engine
BASE = 'f778375655'                       # claude/mt-mortar's head: Dragon's Den stacks on Mt. Mortar
GROUP = 'gMapGroup_Cherrygrove'
PRIMARY_SYM, SECONDARY_SYM, TILESET_DIR = 'DragonsDenPrimary', 'DragonsDen', 'dragons_den'
MAPSEC = dict(id='MAPSEC_DRAGONS_DEN', name="DRAGON'S DEN", x=4, y=3)
MUSIC = 'MUS_CAVE_OF_ORIGIN'
PROOF_LAST = 'MAP_MT_MORTAR_B1F'           # sMapProofMaps' last entry on BASE
BOULDERS = {}                             # HGSS's Strength boulders (SPRITE_ROCK objects): none here
SAVE = ('den', 28, 14)                    # where the harness saves
SURF = ('den', 28, 22)                    # a lake cell for the harness's surfing capture
COMMIT_PREFIX = "Dragon's Den"
