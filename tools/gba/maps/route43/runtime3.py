"""Headless mGBA checks for Route 43.

    python3 tools/gba/maps/route43/runtime3.py ENGINE_CHECKOUT OUT_DIR

The harness is runtime_convert.py's (one fresh emulator process per phase: write, cold read,
title Continue; every capture dumps VRAM, BG palettes and registers, and the map layers rebuilt
from that dump must equal the decoded native maps pixel for pixel).
This route: views down the whole route; walk-behind captures on tree crowns and signs that
check3.py lists (BG1 must cover the player's cell); the south ledge and the climb-back
refusal; tall grass underfoot; blocked woods, rock, ridge, gate body and pond edge; the three
signs; the toll gate in from the south and out to the north, and back in from the north and
out to the south; the Mahogany gatehouse from Route 43 down into Mahogany and back up; a
Cherrygrove regression view; ordinary flash save, cold reload and Continue.
"""
from __future__ import annotations
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import runtime_convert as RC                         # noqa: E402

R, G, MG, M = RC.ROUTE, RC.GATE, RC.MGATE, RC.MAHOGANY

RC.STEPS = [
    ('view', R, 16, 3, 'north-road'), ('view', R, 4, 7, 'north-west-grass'), ('view', R, 15, 12, 'upper-pond'),
    ('view', R, 23, 13, 'east-grass'), ('view', R, 15, 26, 'big-pond'), ('view', R, 27, 24, 'east-lawn'),
    ('view', R, 19, 40, 'ledge-lawn'), ('view', R, 12, 50, 'south-road-west'), ('view', R, 27, 52, 'south-road-east'),
    ('view', R, 13, 58, 'south-road'), ('view', R, 28, 30, 'east-ridge'),
    # Walk behind: the top layer covers the player's cell, the object's base stays solid.
    ('go', R, 20, 55), ('shot', 'behind-trees-south'), ('south', 1, None), ('at', R, 20, 55),
    ('go', R, 15, 19), ('shot', 'behind-tree-pond'), ('south', 1, None), ('at', R, 15, 19),
    ('go', R, 20, 49), ('shot', 'behind-trainer-tips'), ('south', 1, None), ('at', R, 20, 49),
    ('go', R, 15, 57), ('shot', 'behind-south-sign'), ('south', 1, None), ('at', R, 15, 57),
    ('go', R, 20, 2), ('shot', 'behind-north-sign'), ('south', 1, None), ('at', R, 20, 2),
    # Ledge: jump south, fail to climb back.
    ('go', R, 19, 44), ('south', 1, 'ledge-jump-south'), ('at', R, 19, 46), ('north', 1, None), ('at', R, 19, 46),
    # Tall grass: walk through it (no wild table on this map yet, so no battle starts).
    ('go', R, 15, 37), ('south', 3, 'tall-grass-walk'), ('at', R, 15, 40), ('north', 3, None), ('at', R, 15, 37),
    # Blocked: woods, rock, the east ridge, the gate body, the pond without Surf.
    ('go', R, 18, 44), ('west', 1, None), ('at', R, 18, 44),
    ('go', R, 10, 49), ('west', 1, None), ('at', R, 10, 49),
    ('go', R, 28, 50), ('east', 1, None), ('at', R, 28, 50),
    ('go', R, 24, 48), ('north', 1, None), ('at', R, 24, 48),
    ('go', R, 14, 30), ('west', 1, None), ('at', R, 14, 30),
    # Signs.
    ('sign', R, 20, 3, 'north-sign'), ('sign', R, 20, 50, 'trainer-tips'), ('sign', R, 15, 58, 'south-sign'),
    # Toll gate: in from the south door, out through the north doorway onto the arrow warp.
    ('view', R, 25, 48, 'toll-gate-front'), ('north', 1, None), ('wait', 400), ('map', G, 'toll-gate-entry'),
    ('shot', 'gatehouse-toll-interior'),
    ('go', G, 4, 2), ('north', 1, None), ('wait', 400), ('at', R, 25, 39), ('shot', 'toll-gate-north-exit'),
    ('north', 1, None), ('at', R, 25, 38),
    # Back in from the north (stand on the arrow, press south), out the south door.
    ('south', 1, None), ('at', R, 25, 39), ('south', 1, None), ('wait', 400), ('map', G, 'toll-gate-north-entry'),
    ('go', G, 4, 13), ('south', 1, None), ('wait', 400), ('at', R, 25, 48), ('shot', 'toll-gate-south-exit'),
    # Mahogany gatehouse: from Route 43 down into Mahogany, and back.
    ('go', R, 13, 60), ('south', 1, None), ('at', R, 13, 61), ('shot', 'mahogany-gate-back'),
    ('south', 1, None), ('wait', 400), ('map', MG, 'mahogany-gatehouse-entry'), ('shot', 'gatehouse-mahogany-interior'),
    ('go', MG, 4, 13), ('south', 1, None), ('wait', 400), ('at', M, 12, 6), ('shot', 'mahogany-gate-exit'),
    ('north', 1, None), ('wait', 400), ('map', MG, 'mahogany-gatehouse-return'),
    ('go', MG, 4, 2), ('north', 1, None), ('wait', 400), ('at', R, 12, 61), ('shot', 'route43-from-mahogany'),
    ('view', M, 13, 2, 'mahogany-north-seam'), ('view', 0, 50, 17, 'regression-cherrygrove'),
]
RC.WALK_BEHIND = {'behind-trees-south': (20, 55), 'behind-tree-pond': (15, 19), 'behind-trainer-tips': (20, 49),
                  'behind-south-sign': (15, 57), 'behind-north-sign': (20, 2)}
RC.IN_FRONT = ('toll-gate-front', 'toll-gate-south-exit', 'mahogany-gate-exit')

if __name__ == '__main__':
    RC.main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
