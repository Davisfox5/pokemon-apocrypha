"""Headless mGBA checks for Route 46, and Route 45 across the seam.

    python3 tools/gba/maps/route46/runtime3.py ENGINE_CHECKOUT OUT_DIR

The harness is runtime_convert.py's (one fresh emulator process per phase: write, cold read,
title Continue; every capture dumps VRAM, BG palettes and registers, and the map layers rebuilt
from that dump must equal the decoded native maps pixel for pixel, the connected map drawn
beyond the seam, CherrygrovePrimary's animated sea counted apart). This route: views down the
whole of Route 46 (the Dark Cave mouth, the terraces and their stairs, the Rock Climb wall, the
tall grass, the road and the gate's roof); the seam walked from Route 45's west-edge stairs into
Route 46 and back on all three rows, with captures on both sides and part way through each
crossing step (just after the secondary tileset swaps); walk-behind under the route sign (BG1
must cover the player's cell) and in front of it (BG1 clear); the jump ledges, south and west,
one way; both straight flights; the Dark Cave mouth, the Rock Climb wall, the gate's roof, the
trees closing on it either side of its doorway, and a tree blocking a player on foot; both signs read; Route 45, Blackthorn and Cherrygrove
regression views; ordinary flash save, cold reload and Continue.
"""
from __future__ import annotations
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import runtime_convert as RC                         # noqa: E402

R, F, N = RC.ROUTE, RC.ROUTE45, RC.BLACKTHORN

RC.STEPS = [
    ('view', R, 20, 11, 'dark-cave-mouth'), ('view', R, 6, 11, 'north-woods'), ('view', R, 26, 11, 'east-lawn'),
    ('view', R, 20, 18, 'middle-road'), ('view', R, 8, 25, 'west-terrace'), ('view', R, 22, 24, 'rock-climb-wall'),
    ('view', R, 18, 31, 'middle-lawn'), ('view', R, 5, 34, 'west-stairs'), ('view', R, 18, 39, 'east-stairs'),
    ('view', R, 9, 46, 'tall-grass'), ('view', R, 19, 52, 'route-sign'), ('view', R, 18, 58, 'gate-road'),
    # The seam: Route 45's west-edge stairs west into Route 46 and back, captured on both sides and
    # part way through each crossing step.
    ('go', F, 2, 139), ('west', 2, None), ('at', F, 0, 139), ('shot', 'seam-route45-edge'),
    ('mid', 'west', 4, 'mid-crossing-west'), ('at', R, 31, 11), ('shot', 'seam-arrive-route46'),
    ('mid', 'east', 4, 'mid-crossing-east'), ('at', F, 0, 139), ('shot', 'seam-back-on-route45'),
    ('go', F, 1, 138), ('west', 2, None), ('at', R, 31, 10), ('east', 2, None), ('at', F, 1, 138),
    ('go', F, 1, 140), ('west', 2, None), ('at', R, 31, 12), ('east', 2, None), ('at', F, 1, 140),
    ('view', F, 4, 139, 'route45-west-stairs'),
    # Walk behind the route sign's board; in front of its post.
    ('go', R, 20, 48), ('south', 1, None), ('at', R, 20, 49), ('shot', 'behind-route-sign'), ('south', 1, None), ('at', R, 20, 49),
    ('go', R, 20, 52), ('north', 1, 'route-sign-front'), ('at', R, 20, 51),
    # Jump ledges, one way: south over (20, 21), west over (15, 25).
    ('go', R, 20, 20), ('south', 1, None), ('at', R, 20, 22), ('shot', 'ledge-jumped-south'), ('north', 1, None), ('at', R, 20, 22),
    ('go', R, 16, 25), ('west', 1, None), ('at', R, 14, 25), ('shot', 'ledge-jumped-west'), ('east', 1, None), ('at', R, 14, 25),
    # The two straight flights, down a south face.
    ('go', R, 5, 31), ('south', 2, 'west-stairs-descended'), ('at', R, 5, 33),
    ('go', R, 18, 36), ('south', 2, 'east-stairs-descended'), ('at', R, 18, 38),
    # Blocked on foot: the Dark Cave mouth (Dark Cave is not built), the Rock Climb wall (Gen 3 has
    # no Rock Climb), the gate's roof (its interior is not built) and the trees closing on it either side
    # of its doorway, a tree.
    ('go', R, 20, 10), ('north', 1, None), ('at', R, 20, 10),
    ('go', R, 23, 23), ('east', 1, None), ('at', R, 23, 23),
    ('go', R, 18, 61), ('south', 1, 'gate-roof'), ('at', R, 18, 61), ('west', 1, None), ('at', R, 18, 61),
    ('go', R, 19, 61), ('east', 1, None), ('at', R, 19, 61),
    ('go', R, 21, 52), ('east', 1, None), ('at', R, 21, 52),
    # Signs.
    ('sign', R, 20, 50, 'route-sign-read'), ('sign', R, 22, 10, 'dark-cave-sign-read'),
    ('view', F, 20, 140, 'regression-route45'), ('view', N, 25, 40, 'regression-blackthorn'), ('view', 0, 50, 17, 'regression-cherrygrove'),
]
RC.WALK_BEHIND = {'behind-route-sign': (20, 49)}
RC.IN_FRONT = ('route-sign-front',)

if __name__ == '__main__':
    RC.main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
