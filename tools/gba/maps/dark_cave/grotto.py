"""The Dark Cave grotto: a new section reached only by Diving (owner direction, November 2026).

Creative proposal, built from scratch: a flooded chamber past the underwater path under the Route
45 side's lake. The player surfaces in its pool (the underwater path's water door warps onto the
deep water there), swims to the shore, climbs to a terrace and an upper chamber of quartz and moss
rock. Diving in the pool's deep water returns to the underwater path
in front of the door (the map's ON_RESUME setdivewarp, the Seafloor Cavern pattern). No items or
encounters are placed (campaign content).

The plan is a ledger like the HGSS-derived ones (assemble.ledger): digits are floor at that
level, ~ water (level 0, a tier under the shore), D deep water (the Dive spot), s stairs in a
face, L a south jump ledge, o HGSS's moss rock, p a rock formation one tier above its floor,
q quartz, # rock. Rock heights step up one tier per cell from the open ground round them, capped
three tiers up, as HGSS's rings do; beyond that is the void rock.
"""
from __future__ import annotations

W, H = 40, 30
ARRIVAL = (19, 21)                      # warp 0: the underwater door lands here, in the deep water
PLAN = [
    '########################################',  # 00
    '########################################',  # 01
    '##############33333333##################',  # 02
    '###########33333333333333###############',  # 03
    '#########333q3333333333333q#############',  # 04
    '########33333333333333333333############',  # 05
    '########p33333333333333333333o##########',  # 06
    '#########33333333333333333333###########',  # 07
    '##################ss####################',  # 08  face: the upper chamber over the terrace
    '#######2222222222222222222222222########',  # 09
    '#####2222222222222222222222222222#######',  # 10
    '####222o222222222222222222222222q#######',  # 11
    '####22222222222222222222222222222#######',  # 12
    '#####222222222222222222222222222########',  # 13
    '######22222222222222222222222222########',  # 14
    '######ss####################ss##########',  # 15  face: a flight down at each end
    '####11111111111111111111111111111#######',  # 16
    '###111o1111111111111111111111111111#####',  # 17
    '####11~~~~~~~~~~~~~~~~~~~~~~~~~~111#####',  # 18
    '#####~~~~~~~~~~~~~~~~~~~~~~~~~~~~~######',  # 19
    '#####~~~~~~~~~~~~~~~~~~~~~~~~~~~~~######',  # 20
    '######~~~~~~~~~~~~DD~~~~~~~~~~~~~~######',  # 21
    '######~~~~~~~~~~~~DD~~~~~~~~~~~~~#######',  # 22
    '#######~~~~~~~~~~~~~~~~~~~~~~~~~########',  # 23
    '########~~~~~~~~~~~~~~~~~~~~~~~#########',  # 24
    '##########~~~~~~~~~~~~~~~~~~~###########',  # 25
    '########################################',  # 26
    '########################################',  # 27
    '########################################',  # 28
    '########################################',  # 29
]
RING = 3

def ledger():
    """Cells in assemble.ledger's form."""
    assert len(PLAN) == H and all(len(r) == W for r in PLAN), 'plan size'
    FLOOR, WATER = 1, 7                                      # pack.CLASS numbers
    level = {}
    for y, row in enumerate(PLAN):
        for x, ch in enumerate(row):
            if ch.isdigit():
                level[(x, y)] = int(ch)
            elif ch in '~D':
                level[(x, y)] = 0
            elif ch in 'oq':                                 # stands on the floor beside it
                near = [int(PLAN[y + dy][x + dx]) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if PLAN[y + dy][x + dx].isdigit()]
                level[(x, y)] = max(near)
            elif ch == 'p':                                  # a knob one tier over the highest floor round it
                level[(x, y)] = max(int(PLAN[y + dy][x + dx]) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if PLAN[y + dy][x + dx].isdigit())
    # stairs and ledges: the face they cut, the upper floor's level
    for y, row in enumerate(PLAN):
        for x, ch in enumerate(row):
            if ch in 'sL':
                level[(x, y)] = max(int(PLAN[y - 1][x]), int(PLAN[y + 1][x]))
    open_ = {k: v for k, v in level.items() if PLAN[k[1]][k[0]] not in 'p'}
    top = max(level.values()) + RING + 1
    cells = []
    for y, row in enumerate(PLAN):
        out = []
        for x, ch in enumerate(row):
            c = dict(x=x, y=y, lab='.', floor='sand', material=FLOOR)
            if ch == '#':
                peak = min((v + max(abs(x - ox), abs(y - oy)) for (ox, oy), v in open_.items()
                            if max(abs(x - ox), abs(y - oy)) <= RING), default=None)
                if peak is None:
                    c.update(lab='T', ground=top, peak=top, level=top, void=True)
                else:
                    c.update(lab='T', ground=peak, peak=peak, level=peak, ring=True)
            else:
                v = level[(x, y)]
                c.update(ground=v, peak=v, level=v)
                if ch in '~D':
                    c.update(floor='water', material=WATER)
                    if ch == 'D':
                        c['deep'] = True
                elif ch == 's':
                    c['lab'] = 's'
                elif ch == 'L':
                    c['lab'] = 'L'
                elif ch == 'o':
                    c.update(boulder=True, moss=True)
                elif ch == 'q':
                    c.update(boulder=True, prop='quartz')
                elif ch == 'p':
                    c.update(lab='T', peak=v + 1, formation=True)
            out.append(c)
        cells.append(out)
    # a ledge stands on the floor below it (assemble.ledger's rule)
    for row in cells:
        for c in row:
            if c['lab'] == 'L':
                c['ground'] = cells[c['y'] + 1][c['x']]['ground']
    return cells
