"""Headless mGBA checks for Route 45, and Blackthorn City across the seam.

    python3 tools/gba/maps/route45/runtime3.py ENGINE_CHECKOUT OUT_DIR

The harness is runtime_convert.py's (one fresh emulator process per phase: write, cold read,
title Continue; every capture dumps VRAM, BG palettes and registers, and the map layers rebuilt
from that dump must equal the decoded native maps pixel for pixel, the connected map drawn
beyond the seam, CherrygrovePrimary's animated sea counted apart). This route: views down the
whole of Route 45 (its bridges, the three cascades, the pond and the woods at its foot); the
seam walked from Route 45 into Blackthorn and back, with captures on both sides and part way
through each crossing step (just after the secondary tileset swaps); a view on Blackthorn's
south shore; walk-behind under the route sign (BG1 must cover the player's cell) and in front of
it (BG1 clear); a jump ledge; a straight and a diagonal flight of stairs; the Dark Cave mouth
and a tree blocking a player on foot; a bridge walked end to end with the
river below it out of reach on foot, the Surf route's landing and shore walked to, and the road
beside the row 47 ledge ending at rock (owner review); both signs read; Blackthorn and Cherrygrove
regression views; ordinary flash save, cold reload and Continue.
"""
from __future__ import annotations
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import runtime_convert as RC                         # noqa: E402

R, N = RC.ROUTE, RC.BLACKTHORN

RC.STEPS = [
    ('view', R, 23, 2, 'seam-road'), ('view', R, 23, 8, 'route-sign'), ('view', R, 10, 7, 'dark-cave-mouth'),
    ('view', R, 18, 8, 'first-bridge'), ('view', R, 10, 17, 'second-bridge'), ('view', R, 5, 25, 'west-tall-grass'),
    ('view', R, 20, 21, 'east-tall-grass'), ('view', R, 11, 42, 'third-bridge'), ('view', R, 10, 56, 'first-cascade'),
    ('view', R, 13, 62, 'fourth-bridge'), ('view', R, 13, 85, 'fifth-bridge'), ('view', R, 16, 97, 'second-cascade'),
    ('view', R, 9, 110, 'island-road'), ('view', R, 14, 118, 'sixth-bridge'), ('view', R, 11, 124, 'third-cascade'),
    ('view', R, 26, 137, 'pond'), ('view', R, 14, 147, 'last-bridge'), ('view', R, 8, 148, 'south-woods'),
    ('view', R, 20, 147, 'river-mouth'),
    # The seam: Route 45 north into Blackthorn and back, captured on both sides and part way
    # through each crossing step.
    ('go', R, 23, 1), ('north', 1, None), ('at', R, 23, 0), ('shot', 'seam-route45-edge'),
    ('mid', 'north', 4, 'mid-crossing-north'), ('at', N, 23, 63), ('shot', 'seam-arrive-blackthorn'),
    ('mid', 'south', 4, 'mid-crossing-south'), ('at', R, 23, 0), ('shot', 'seam-back-on-route45'),
    ('go', R, 22, 1), ('north', 2, None), ('at', N, 22, 63), ('south', 2, None), ('at', R, 22, 1),
    ('go', R, 24, 1), ('north', 2, None), ('at', N, 24, 63), ('south', 2, None), ('at', R, 24, 1),
    ('view', N, 23, 60, 'blackthorn-south-bridge'),
    # Walk behind the route sign's board; in front of its post.
    ('go', R, 24, 5), ('south', 1, None), ('at', R, 24, 6), ('shot', 'behind-route-sign'), ('south', 1, None), ('at', R, 24, 6),
    ('go', R, 24, 9), ('north', 1, 'route-sign-front'), ('at', R, 24, 8),
    # A jump ledge, a straight flight down a south face, a diagonal flight down a west face.
    ('go', R, 16, 18), ('south', 1, None), ('at', R, 16, 20), ('shot', 'ledge-jumped'),
    ('go', R, 26, 22), ('south', 2, 'stairs-descended'), ('at', R, 26, 24),
    ('go', R, 20, 58), ('west', 2, 'diagonal-stairs-descended'), ('at', R, 18, 58), ('east', 2, None), ('at', R, 20, 58),
    # Blocked on foot: the Dark Cave mouth (Dark Cave's Route 45 side is not built), a tree.
    ('go', R, 10, 7), ('north', 1, None), ('at', R, 10, 7),
    ('go', R, 8, 148), ('south', 1, None), ('at', R, 8, 148),
    # Owner review (2026-10-26): a bridge walked end to end through its elevation steps (road 3,
    # end 0, deck 4 and 15), and no step from the deck onto the river; the Surf route's landing
    # below Blackthorn and its shore at the foot are walkable, the water beside them is not on
    # foot; the road beside the row 47 ledge's east end ends at rock.
    ('go', R, 8, 41), ('east', 3, None), ('at', R, 11, 41), ('north', 1, None), ('at', R, 11, 41), ('shot', 'on-third-bridge'),
    ('east', 3, None), ('at', R, 14, 41), ('west', 6, None), ('at', R, 8, 41),
    ('go', R, 22, 11), ('west', 2, None), ('at', R, 20, 11), ('shot', 'river-landing'), ('west', 1, None), ('at', R, 20, 11),
    ('go', R, 19, 148), ('south', 2, None), ('at', R, 19, 150), ('shot', 'river-shore'), ('south', 1, None), ('at', R, 19, 150),
    ('go', R, 23, 44), ('south', 2, None), ('at', R, 23, 46), ('shot', 'ledge-end-road'), ('south', 1, None), ('at', R, 23, 46),
    # Signs.
    ('sign', R, 24, 7, 'route-sign-read'), ('sign', R, 12, 7, 'dark-cave-sign-read'),
    ('view', N, 25, 40, 'regression-blackthorn'), ('view', 0, 50, 17, 'regression-cherrygrove'),
]
RC.WALK_BEHIND = {'behind-route-sign': (24, 6)}
RC.IN_FRONT = ('route-sign-front',)

if __name__ == '__main__':
    RC.main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
