"""Slowpoke Well, for the Johto cave kit (tools/gba/maps/johto_caves): HGSS zones D26R0101-0103.

The well's bottom under Azalea (the ladder up, puddles, the hole into B1F), B1F (its maze of
terraces, the Strength boulder, the ladder down) and B2F (a lake round the ladder's island).
"""
NAME = 'Slowpoke Well'
ART = 'slowpoke-well'
TOOL = 'slowpoke_well'
AREA_BANK = 84
FLOORS = {
    'entrance': dict(header='MAP_SLOWPOKE_WELL_ENTRANCE', matrix='map_matrix_0045_D26R0101.bin', zone='111_D26R0101',
                     name='SlowpokeWell_Entrance', id='MAP_SLOWPOKE_WELL_ENTRANCE'),
    'b1f': dict(header='MAP_SLOWPOKE_WELL_B1F', matrix='map_matrix_0046_D26R0102.bin', zone='170_D26R0102',
                name='SlowpokeWell_B1F', id='MAP_SLOWPOKE_WELL_B1F'),
    'b2f': dict(header='MAP_SLOWPOKE_WELL_B2F', matrix='map_matrix_0106_D26R0103.bin', zone='174_D26R0103',
                name='SlowpokeWell_B2F', id='MAP_SLOWPOKE_WELL_B2F'),
}
ROCK_TEX = ('dwall_s', 'dcliff01', 'dallpeak_p')
FLOOR_TEX = 'droad01'
FLOOR2 = None
KEEP_MODELS = ()
KEEP_MATERIALS = ()
DECK_MATERIALS = ()
SEA_ROCKS = ()
# the well's own pieces: its round wall (yadonwall), the stone pillar beside the hole (yadon_hashi) and the stones on
# its floor (yadoishi) read as the cave's rock; its puddle (dpuddle_un) is HGSS 0x16, Gen 3 MB_PUDDLE
EXTRA_CLASS = {'yadonwall_d': 2, 'yadonwall_a': 2, 'yadon_hashi': 2, 'yadoishi_a': 5, 'yadoishi_b': 5, 'yadoishi_c': 5,
               'dpuddle_un': 7}
SMALL_ROCKS = ('d_rock01s', 'yadoishi_a', 'yadoishi_b', 'yadoishi_c')
UNBUILT = set()
TOWN = dict(map='JohtoAzaleaTown', id='MAP_JOHTO_AZALEA_TOWN', hgss='MAP_AZALEA', cell=(48, 14), metatile=208,
            primary='azalea', secondary='azalea', size=(64, 33), pair=('entrance', 0))
BASE = '4d8fbbfa03'                       # codex/azalea-town's head: the well hangs off Azalea
GROUP = 'gMapGroup_Cherrygrove'
PRIMARY_SYM, SECONDARY_SYM, TILESET_DIR = 'SlowpokeWellPrimary', 'SlowpokeWell', 'slowpoke_well'
MAPSEC = dict(id='MAPSEC_SLOWPOKE_WELL', name='SLOWPOKE WELL', x=1, y=8)
MUSIC = 'MUS_CAVE_OF_ORIGIN'
PROOF_LAST = 'MAP_JOHTO_AZALEA_TOWN'
BOULDERS = {'b1f': [(23, 3)]}             # HGSS's SPRITE_ROCK object on B1F: a Strength boulder
SAVE = ('entrance', 17, 7)
SURF = ('b2f', 5, 25)
COMMIT_PREFIX = 'Slowpoke Well'
