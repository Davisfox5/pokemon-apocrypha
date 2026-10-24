"""Headless mGBA checks for Lake of Rage, and Route 43 across the seam.

    python3 tools/gba/maps/lake_of_rage/runtime3.py ENGINE_CHECKOUT OUT_DIR

The harness is runtime_convert.py's (one fresh emulator process per phase: write, cold read,
title Continue; every capture dumps VRAM, BG palettes and registers, and the map layers rebuilt
from that dump must equal the decoded native maps pixel for pixel, the connected map drawn
beyond the seam). This route: views round the Lake's shores; the seam walked from Route 43 up
into the Lake and back down, with captures on both sides of it; walk-behind captures on tree
crowns, the guru's house and both signs (BG1 must cover the player's cell); in front of the
guru's house (BG1 clear); both ledges and the climb-back refusal; the house door, a tree and
the lake's edge blocking a player on foot; both signs read; a Route 43 view and a Cherrygrove
regression view; ordinary flash save, cold reload and Continue.
"""
from __future__ import annotations
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import runtime_convert as RC                         # noqa: E402

R, L = RC.ROUTE, RC.LAKE

RC.STEPS = [
    ('view', L, 48, 60, 'south-road'), ('view', L, 48, 52, 'lake-sign-shore'), ('view', L, 56, 59, 'guru-house'),
    ('view', L, 26, 54, 'south-west-lawn'), ('view', L, 22, 47, 'south-shore-west'), ('view', L, 45, 50, 'lake-outlet'),
    ('view', L, 66, 44, 'east-shore'), ('view', L, 72, 26, 'east-clearing'), ('view', L, 63, 47, 'south-east-shore'),
    ('view', L, 34, 62, 'west-seam-lawn'), ('view', L, 71, 40, 'east-woods-edge'),
    # The seam: Route 43 north into the Lake and back, captured on both sides.
    ('go', R, 16, 2), ('shot', 'seam-from-route43'), ('north', 3, None), ('at', L, 48, 63), ('shot', 'seam-arrive-lake'),
    ('north', 1, None), ('at', L, 48, 62), ('shot', 'seam-from-lake'),
    ('south', 2, None), ('at', R, 16, 0), ('shot', 'seam-back-on-route43'),
    ('go', R, 2, 1), ('north', 2, None), ('at', L, 34, 63), ('shot', 'west-seam-arrive-lake'),
    ('south', 1, None), ('at', R, 2, 0),
    # Walk behind: the top layer covers the player's cell, the object's base stays solid.
    ('go', L, 56, 52), ('shot', 'behind-guru-house'), ('south', 1, None), ('at', L, 56, 52),
    ('go', L, 48, 49), ('shot', 'behind-lake-sign'), ('south', 1, None), ('at', L, 48, 49),
    ('go', L, 54, 56), ('shot', 'behind-guru-sign'), ('south', 1, None), ('at', L, 54, 56),
    # Ledges: jump south, fail to climb back.
    ('go', L, 22, 48), ('south', 1, 'ledge-jump-north-run'), ('at', L, 22, 50), ('north', 1, None), ('at', L, 22, 50),
    ('go', L, 27, 50), ('south', 1, 'ledge-jump-south-run'), ('at', L, 27, 52), ('north', 1, None), ('at', L, 27, 52),
    # Blocked on foot: the guru's door (interior not built), a tree, the lake.
    ('go', L, 56, 58), ('north', 1, 'guru-house-front'), ('at', L, 56, 58),
    ('go', L, 44, 54), ('west', 1, None), ('at', L, 44, 54),
    ('go', L, 48, 47), ('north', 1, None), ('at', L, 48, 47),
    # Signs.
    ('sign', L, 48, 50, 'lake-sign'), ('sign', L, 54, 57, 'guru-sign'),
    ('view', R, 13, 58, 'route43-south-road'), ('view', 0, 50, 17, 'regression-cherrygrove'),
]
RC.WALK_BEHIND = {'behind-guru-house': (56, 52), 'behind-lake-sign': (48, 49), 'behind-guru-sign': (54, 56)}
RC.IN_FRONT = ('guru-house-front',)

if __name__ == '__main__':
    RC.main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
