"""Violet's interiors, room by room: what each takes from HGSS and what it changes for its role.

Sprout Tower keeps HGSS's three floors as they are (the sages still train there; Elder Li on the top
floor). The university, the lecture hall and the five houses are labelled proposals for their new roles
(DESIGN.md: Violet is Johto's academic capital, the trainer school grown into a university, Falkner's old
gym a lecture hall and practice arena; the houses are campus homes, owner choice of November 3).
"""
from __future__ import annotations
import json
from pathlib import Path
import room as RM

# group: one private tileset pair for a building's rooms
GROUPS = {
    'university': dict(rooms=['VioletUniversity'], primary='violet_university', secondary='violet_university',
                       psym='VioletUniversityPrimary', ssym='VioletUniversity'),
    'lecture': dict(rooms=['VioletLectureHall'], primary='violet_lecture_hall', secondary='violet_lecture_hall',
                    psym='VioletLectureHallPrimary', ssym='VioletLectureHall'),
    'sage_house': dict(rooms=['VioletHouse1'], primary='violet_sage_house', secondary='violet_sage_house',
                       psym='VioletSageHousePrimary', ssym='VioletSageHouse'),
    'houses': dict(rooms=['VioletHouse2', 'VioletHouse3', 'VioletHouse4', 'VioletHouse5'],
                   primary='violet_houses', secondary='violet_houses', psym='VioletHousesPrimary', ssym='VioletHouses'),
    'sprout': dict(rooms=['SproutTower1F', 'SproutTower2F', 'SproutTower3F'], primary='violet_sprout_tower',
                   secondary='violet_sprout_tower', psym='VioletSproutTowerPrimary', ssym='VioletSproutTower'),
}

SPROUT_CROP = ((4, 3), (23, 26))         # HGSS cells x 4-26, y 3-28: the tower's floor and its back wall

def sprout(name, ladders, exit=None):
    def make():
        r = RM.from_hgss(name, *SPROUT_CROP)
        for p in r.hgss['props']:
            r.add(p)
        r.rect = (1, 0, 22, 26)          # x 5-25: the floor between the tower's side walls
        for c in ladders:
            r.behaviors[c] = 'ladder'
        if exit:
            r.behaviors[exit] = 'exit'
        r.notes.append('HGSS as it is: floor, walls, lanterns, railings, the swaying pillar, ladders, Bellsprout statues')
        return r
    return make

def L(x, y):                              # HGSS cell -> this map's cell
    return (x - SPROUT_CROP[0][0], y - SPROUT_CROP[0][1])

# --------------------------------------------------------------------------- the university (proposal)
# HGSS's Pokemon School is the lecture room, as it is: blackboard, the dean's desk, the students' desks,
# the bookshelf and cabinet, the tiled aisle. West of it the room runs on nine columns of its own floor and
# wall (HGSS columns 8-11, a window every fourth column) as the university library: tall stacks along the
# back wall, two free-standing stacks, a reading table (CHAPTER2_SCENES_SPEC 2.3b-c: lectures and the library).
UNI_COLS = [0, 1] + [8, 9, 10, 11, 8, 9, 10, 11, 8] + list(range(2, 17))

def university():
    r = RM.compose('school', UNI_COLS, list(range(0, 13)))
    lib = [(73, x, 4.0, {}) for x in (3.0, 5.0, 7.0, 9.0)]
    lib += [(72, 3.0, 7.5, {}), (72, 9.0, 7.5, {})]
    lib += [(94, 6.0, 7.5, {}), (53, 5.5, 8.5, {}), (53, 6.5, 8.5, {})]
    lib += [(94, 6.0, 10.5, {}), (53, 5.5, 11.5, {}), (53, 6.5, 11.5, {})]
    RM.finish(r, lib)
    r.rect = (1, 1, r.W - 1, 12)
    r.behaviors[(UNI_COLS.index(6, 2), 11)] = 'exit'
    for x in range(2, 10):
        if r.blocked[3, x]:
            r.behaviors[(x, 3)] = 'bookshelf'
    r.notes.append("HGSS's Pokemon School as the lecture room; a library wing of nine columns west of it (proposal)")
    return r

# --------------------------------------------------------------------------- the lecture hall (proposal)
# Falkner's gym, absorbed into the campus as a lecture hall and practice arena (DESIGN.md, Violet). HGSS's
# hall as it is: the drapery and crest at the back, the orange pillars, the glass floor panels and their
# rails, the wooden stage with its green mat, the statues at the door. The pit and the raised walkways in
# the middle become a stone practice court with white lines; a blackboard at the back of the stage and a
# lectern at its edge; two rows of desks each side face the stage (CHAPTER2_SCENES_SPEC 2.5).
def lecture_hall():
    import lecture_draft as LD
    r = RM.compose('gym', list(range(7, 24)), list(range(30)), keep=lambda k, p: p.model != 113)
    L = lambda x, y: (x - 7, y)
    LD.court(r, L)
    r.blocked[:] = False
    for y in range(r.H):
        for x in range(r.W):
            hx = x + 7
            if hx < 9 or hx > 21 or y < 4 or y > 28:
                r.blocked[y, x] = True
    for hx in (9, 10, 11, 19, 20, 21):
        for y in (17, 18):
            r.blocked[y, hx - 7] = True                      # the glass panels' rails
    for hx in (12, 18):                                       # the statues
        for y in (24, 25):
            r.blocked[y, hx - 7] = True
    seats = []
    for hx in (10.5, 20.5):
        for y in (12.5, 15.0):
            seats.append((91, hx - 7, y, {}))
            seats += [(53, hx - 7 + d, y + 1.0, {}) for d in (-1, 0, 1)]
    RM.finish(r, [(62, 15.5 - 7, 4.0, {}), (89, 15.5 - 7, 9.0, {})] + seats)
    r.rect = (0, 0, r.W, 29)
    r.behaviors[L(15, 28)] = 'exit'
    r.notes.append("HGSS's Violet Gym as a lecture hall and practice arena: the pit and walkways a stone court (proposal)")
    return r

# --------------------------------------------------------------------------- the houses (proposals)
# HGSS's Violet house (T22R0401, wood floor; its tatami twin T20R0301 for the sage), 11 x 9 cells: kitchen
# at the west, its window, the exit mat at (4, 8). Owner choice, November 3: campus homes.
HOUSE = (list(range(0, 11)), list(range(0, 10)))

def house(src, drop, extra, note):
    def make():
        r = RM.compose(src, *HOUSE, keep=lambda k, p: k not in drop)
        RM.finish(r, extra)
        r.rect = (0, 0, 11, 9)
        r.behaviors[(4, 8)] = 'exit'
        r.notes.append(note)
        return r
    return make

TABLE, CHAIRS, SHELF = [0], [1, 2, 3, 4], [8]
HOUSES = {
    # the retired sage's home, nearest the tower: tatami, a home shrine, a low table and cushions, a Bellsprout statue
    'VioletHouse1': house('house_unused', TABLE + CHAIRS + [7],          # the tatami twin lists its shelf 7th, its mat 8th
                          [(143, 8.5, 3.0, {}), (89, 6.5, 5.5, {}), (56, 5.5, 5.5, {}), (56, 7.5, 5.5, {}),
                           (64, 9.5, 7.5, {'kind': 1}), (114, 1.5, 7.5, {})],
                          "a retired sage's home: HGSS's tatami house, a home shrine, low table, cushions, a Bellsprout statue (proposal)"),
    # students' boarding house: two beds, a study desk with a PC, a poster
    'VioletHouse2': house('house_nw', TABLE + CHAIRS + SHELF,
                          [(17, 6.5, 4.0, {}), (17, 8.5, 4.0, {}), (91, 8.0, 6.5, {}), (53, 7.5, 7.5, {}), (53, 8.5, 7.5, {}), (139, 9.5, 2.6, {})],
                          "students' boarding house: two beds, a study desk, a poster (proposal)"),
    # a second boarding house: two beds, the bookshelf, a shared study table, a new student's boxes
    'VioletHouse3': house('house_nw', TABLE + CHAIRS,
                          [(17, 5.5, 4.0, {}), (17, 7.5, 4.0, {}), (91, 7.0, 6.5, {}), (53, 6.5, 7.5, {}), (53, 7.5, 7.5, {}),
                           (76, 9.5, 7.5, {})],
                          "students' boarding house: two beds, a study table, a new arrival's boxes (proposal)"),
    # a professor's home: a study of tall shelves and a desk with a PC beside the kitchen table
    'VioletHouse4': house('house_nw', CHAIRS[:2] + SHELF,
                          [(73, 9.0, 3.5, {}), (73, 7.0, 3.5, {}), (87, 9.0, 7.0, {'scale': (0.45, 0.45, 0.45)})],
                          "a professor's home with a study: tall shelves and a globe by the reading table (proposal)"),
    # the map-card kid's family home, with their gran: HGSS's house as it is, a town map, a clock and a TV
    'VioletHouse5': house('house_nw', [],
                          [(15, 6.8, 3.0, {}), (19, 9.0, 7.5, {})],
                          "the map-card kid's family home: HGSS's house, a town map on the wall and a TV (proposal)"),
}

ROOMS = {
    'VioletUniversity': university,
    'VioletLectureHall': lecture_hall,
    **HOUSES,
    'SproutTower1F': sprout('sprout1', [L(10, 15), L(10, 14), L(24, 9), L(24, 8), L(6, 16), L(6, 15)], L(15, 28)),
    'SproutTower2F': sprout('sprout2', [L(11, 14), L(24, 9), L(6, 16), L(15, 27)]),
    'SproutTower3F': sprout('sprout3', [L(15, 27)]),
}

def w(cell, dest, warp):
    return dict(x=cell[0], y=cell[1], elevation=0, dest_map=dest, dest_warp_id=str(warp))

# map: layout and its warps beyond the exit (HGSS's own order, so dest ids match HGSS's anchors)
MAPS = {
    'VioletUniversity': dict(layout='LAYOUT_VIOLET_UNIVERSITY', folder='VioletUniversity', exit=[(UNI_COLS.index(6, 2), 11)], warps=[]),
    'VioletLectureHall': dict(layout='LAYOUT_VIOLET_LECTURE_HALL', folder='VioletLectureHall', exit=[(8, 28)], warps=[]),
    **{n: dict(layout=f'LAYOUT_VIOLET_HOUSE_{n[-1]}', folder=n, exit=[(4, 8)], warps=[]) for n in HOUSES},
    'SproutTower1F': dict(layout='LAYOUT_SPROUT_TOWER_1F', folder='SproutTower1F', exit=[L(15, 28)],
                          warps=[w(L(10, 15), 'MAP_SPROUT_TOWER_2F', 0), w(L(24, 9), 'MAP_SPROUT_TOWER_2F', 1),
                                 w(L(6, 16), 'MAP_SPROUT_TOWER_2F', 2), w(L(6, 15), 'MAP_SPROUT_TOWER_2F', 2),
                                 w(L(10, 14), 'MAP_SPROUT_TOWER_2F', 0), w(L(24, 8), 'MAP_SPROUT_TOWER_2F', 1)]),
    'SproutTower2F': dict(layout='LAYOUT_SPROUT_TOWER_2F', folder='SproutTower2F', music_from='SproutTower1F',
                          warps=[w(L(11, 14), 'MAP_SPROUT_TOWER_1F', 1), w(L(24, 9), 'MAP_SPROUT_TOWER_1F', 2),
                                 w(L(6, 16), 'MAP_SPROUT_TOWER_1F', 3), w(L(15, 27), 'MAP_SPROUT_TOWER_3F', 0)]),
    'SproutTower3F': dict(layout='LAYOUT_SPROUT_TOWER_3F', folder='SproutTower3F', music_from='SproutTower1F',
                          warps=[w(L(15, 27), 'MAP_SPROUT_TOWER_2F', 3)]),
}

def install_maps(engine, names):
    """Each interior's map.json: its layout, its exit warps (kept from doors.py) and its own warps."""
    import doors as D
    for n in names:
        m = MAPS[n]
        p = engine / 'data/maps' / n / 'map.json'
        if p.exists():
            mj = json.loads(p.read_text())
        else:
            music = json.loads((engine / 'data/maps' / m.get('music_from', n) / 'map.json').read_text())['music'] if m.get('music_from') else 'MUS_LITTLEROOT'
            mj = D.interior_json(n, m['layout'], music, [])
            p.parent.mkdir(exist_ok=True)
            (p.parent / 'scripts.inc').write_text(D.scripts(n, None))
        mj['layout'] = m['layout']
        mj['id'] = m['layout'].replace('LAYOUT_', 'MAP_', 1)
        exits = [e for e in mj['warp_events'] if e['dest_map'] == 'MAP_VIOLET_CITY']
        if exits and m.get('exit'):
            dest = exits[0]['dest_warp_id']
            exits = [dict(x=x, y=y, elevation=0, dest_map='MAP_VIOLET_CITY', dest_warp_id=dest) for x, y in m['exit']]
        mj['warp_events'] = exits + m.get('warps', [])
        p.write_text(json.dumps(mj, indent=2) + '\n')
    # new maps join Violet's group and the script includes
    groups = json.loads((engine / 'data/maps/map_groups.json').read_text())
    grp = next(g for g in groups['group_order'] if 'VioletCity' in groups[g])
    es = (engine / 'data/event_scripts.s').read_text()
    for n in names:
        if n not in groups[grp]:
            groups[grp].append(n)
        inc = f'.include "data/maps/{n}/scripts.inc"'
        if inc not in es:
            es = es.replace('.include "data/maps/SproutTower1F/scripts.inc"\n', f'.include "data/maps/SproutTower1F/scripts.inc"\n{inc}\n', 1)
    (engine / 'data/maps/map_groups.json').write_text(json.dumps(groups, indent=2) + '\n')
    (engine / 'data/event_scripts.s').write_text(es)
