"""Headless mGBA checks for Route 44, and Mahogany Town across the seam.

    python3 tools/gba/maps/route44/runtime3.py ENGINE_CHECKOUT OUT_DIR

The harness is runtime_convert.py's (one fresh emulator process per phase: write, cold read,
title Continue; every capture dumps VRAM, BG palettes and registers, and the map layers rebuilt
from that dump must equal the decoded native maps pixel for pixel, the connected map drawn
beyond the seam). This route: views along Route 44; the seam walked from Route 44 into Mahogany
and back on all three road rows, with captures on both sides and part way through each
crossing step (just after the secondary tileset swaps); views on Mahogany's east road;
walk-behind captures on both signs (BG1 must cover the player's cell) and in front of the
route sign (BG1 clear); both Ice Path ledges and the climb-back refusals; the stairs; the Ice
Path mouth, a tree and the pond's edge blocking a player on foot; both signs read; a Mahogany
and a Cherrygrove regression view; ordinary flash save, cold reload and Continue.
"""
from __future__ import annotations
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import runtime_convert as RC                         # noqa: E402

R, M = RC.ROUTE, RC.MAHOGANY

RC.STEPS = [
    ('view', R, 4, 16, 'seam-road'), ('view', R, 12, 17, 'route-sign-road'), ('view', R, 10, 21, 'west-pond'),
    ('view', R, 15, 11, 'flower-lawn'), ('view', R, 23, 6, 'north-west-woods'), ('view', R, 30, 3, 'north-lawn'),
    ('view', R, 24, 25, 'bridge-west'), ('view', R, 32, 25, 'bridge'), ('view', R, 44, 25, 'south-road'),
    ('view', R, 65, 10, 'big-pond-east-shore'), ('view', R, 70, 22, 'east-road'), ('view', R, 78, 19, 'stairs-foot'),
    ('view', R, 80, 14, 'ice-path-ledge'), ('view', R, 88, 10, 'ice-path-mouth'),
    # The seam on each road row: Route 44 west into Mahogany and back, captured on both sides
    # and part way through each crossing step.
    ('go', R, 1, 16), ('west', 1, None), ('at', R, 0, 16), ('shot', 'seam-route44-edge'),
    ('mid', 'west', 4, 'mid-crossing-west'), ('at', M, 31, 16), ('shot', 'seam-arrive-mahogany'),
    ('mid', 'east', 4, 'mid-crossing-east'), ('at', R, 0, 16), ('shot', 'seam-back-on-route44'),
    ('go', R, 1, 15), ('west', 2, None), ('at', M, 31, 15), ('east', 2, None), ('at', R, 1, 15),
    ('go', R, 1, 17), ('west', 2, None), ('at', M, 31, 17), ('shot', 'seam-mahogany-row17'), ('east', 2, None), ('at', R, 1, 17),
    ('view', M, 27, 16, 'mahogany-east-road'), ('view', M, 31, 15, 'mahogany-east-edge'),
    # Walk behind: the top layer covers the player's cell, the sign's base stays solid.
    ('go', R, 8, 16), ('south', 1, None), ('at', R, 8, 17), ('shot', 'behind-route-sign'), ('south', 1, None), ('at', R, 8, 17),
    ('go', R, 90, 10), ('shot', 'behind-ice-path-sign'), ('south', 1, None), ('at', R, 90, 10),
    ('go', R, 8, 19), ('north', 1, 'route-sign-front'), ('at', R, 8, 19),
    # Ledges: jump south and west, fail to climb back.
    ('go', R, 88, 12), ('south', 1, 'ledge-jump-south'), ('at', R, 88, 14), ('north', 1, None), ('at', R, 88, 14),
    ('go', R, 87, 11), ('west', 1, 'ledge-jump-west'), ('at', R, 85, 11), ('east', 1, None), ('at', R, 85, 11),
    # The stairs up to the Ice Path ledge.
    ('go', R, 78, 19), ('north', 4, 'stairs-climbed'), ('at', R, 78, 15),
    # Blocked on foot: the Ice Path mouth (Ice Path not built), a tree, the pond.
    ('go', R, 89, 10), ('north', 1, None), ('at', R, 89, 10),
    ('go', R, 76, 12), ('east', 1, None), ('at', R, 76, 12),
    ('go', R, 6, 21), ('south', 1, None), ('at', R, 6, 21),
    # Signs.
    ('sign', R, 8, 18, 'route-sign'), ('sign', R, 90, 11, 'ice-path-sign'),
    ('view', M, 16, 16, 'regression-mahogany'), ('view', 0, 50, 17, 'regression-cherrygrove'),
]
RC.WALK_BEHIND = {'behind-route-sign': (8, 17), 'behind-ice-path-sign': (90, 10)}
RC.IN_FRONT = ('route-sign-front',)

if __name__ == '__main__':
    RC.main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
