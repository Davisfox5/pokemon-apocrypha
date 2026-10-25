"""Headless mGBA checks for Route 42, and Mahogany Town across the seam.

    python3 tools/gba/maps/route42/runtime3.py ENGINE_CHECKOUT OUT_DIR

The harness is runtime_convert.py's (one fresh emulator process per phase: write, cold read,
title Continue; every capture dumps VRAM, BG palettes and registers, and the map layers rebuilt
from that dump must equal the decoded native maps pixel for pixel, the connected map drawn
beyond the seam). This route: views along Route 42, the parts reached by Surf included
(teleported to); the seam walked from Route 42 into Mahogany and back, with captures on both
sides and part way through each crossing step (just after the secondary tileset swaps), and on
the road's top and bottom rows; views on Mahogany's west road; walk-behind captures on both
route signs (BG1 must cover the player's cell) and in front of the east one (BG1 clear); the
stairs; a Mt. Mortar mouth, the Ecruteak gate's doorway, a tree and the pond's edge blocking a
player on foot; no way round the gate past the woods; all four signs read; Mahogany, Route 44
and Cherrygrove regression views; ordinary flash save, cold reload and Continue.
"""
from __future__ import annotations
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import runtime_convert as RC                         # noqa: E402

R, M = RC.ROUTE, RC.MAHOGANY

RC.STEPS = [
    ('view', R, 90, 13, 'seam-road'), ('view', R, 80, 13, 'east-road'), ('view', R, 80, 19, 'tall-grass'),
    ('view', R, 77, 12, 'east-cave-mouth'), ('view', R, 71, 13, 'stairs-top'), ('view', R, 68, 16, 'lower-lawn'),
    ('view', R, 45, 18, 'middle-lawn'), ('view', R, 48, 16, 'middle-cave-mouth'), ('view', R, 20, 12, 'west-cave-mouth'),
    ('view', R, 14, 14, 'west-road'), ('view', R, 8, 15, 'ecruteak-gate'), ('view', R, 15, 10, 'north-west-lawn'),
    ('view', R, 25, 13, 'west-pond-shore'),
    # The seam: Route 42 east into Mahogany and back, captured on both sides and part way through
    # each crossing step; then the road's top and bottom rows.
    ('go', R, 94, 13), ('east', 1, None), ('at', R, 95, 13), ('shot', 'seam-route42-edge'),
    ('mid', 'east', 4, 'mid-crossing-east'), ('at', M, 0, 13), ('shot', 'seam-arrive-mahogany'),
    ('mid', 'west', 4, 'mid-crossing-west'), ('at', R, 95, 13), ('shot', 'seam-back-on-route42'),
    ('go', R, 94, 10), ('east', 2, None), ('at', M, 0, 10), ('shot', 'seam-mahogany-row10'), ('west', 2, None), ('at', R, 94, 10),
    ('go', R, 94, 15), ('east', 2, None), ('at', M, 0, 15), ('west', 2, None), ('at', R, 94, 15),
    ('view', M, 3, 14, 'mahogany-west-road'), ('view', M, 0, 11, 'mahogany-west-edge'),
    # Walk behind: the top layer covers the player's cell, the sign's base stays solid.
    ('go', R, 86, 10), ('south', 1, None), ('at', R, 86, 11), ('shot', 'behind-east-route-sign'), ('south', 1, None), ('at', R, 86, 11),
    ('go', R, 11, 16), ('shot', 'behind-west-route-sign'), ('south', 1, None), ('at', R, 11, 16),
    ('go', R, 86, 13), ('north', 1, 'east-route-sign-front'), ('at', R, 86, 13),
    # The stairs down to the lower lawn and back.
    ('go', R, 72, 13), ('west', 3, 'stairs-descended'), ('at', R, 69, 13), ('east', 3, None), ('at', R, 72, 13),
    # Blocked on foot: a Mt. Mortar mouth, the gate's doorway (interiors not built), a tree, the pond.
    # The woods close on the gate: no way round it north or south of its east face.
    ('go', R, 77, 12), ('north', 1, None), ('at', R, 77, 12),
    ('go', R, 7, 15), ('west', 1, None), ('at', R, 7, 15),
    ('go', R, 7, 12), ('west', 1, None), ('at', R, 7, 12), ('go', R, 7, 13), ('west', 1, None), ('at', R, 7, 13),
    ('go', R, 7, 17), ('west', 1, None), ('at', R, 7, 17), ('south', 1, None), ('at', R, 7, 17),
    ('go', R, 41, 19), ('east', 1, None), ('at', R, 41, 19),
    ('go', R, 67, 13), ('west', 1, None), ('at', R, 67, 13),
    # Signs.
    ('sign', R, 86, 12, 'east-route-sign'), ('sign', R, 75, 12, 'east-mt-mortar-sign'),
    ('sign', R, 11, 17, 'west-route-sign'), ('sign', R, 16, 11, 'west-mt-mortar-sign'),
    ('view', M, 16, 16, 'regression-mahogany'), ('view', RC.ROUTE44, 10, 16, 'regression-route44'),
    ('view', 0, 50, 17, 'regression-cherrygrove'),
]
RC.WALK_BEHIND = {'behind-east-route-sign': (86, 11), 'behind-west-route-sign': (11, 16)}
RC.IN_FRONT = ('east-route-sign-front',)

if __name__ == '__main__':
    RC.main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
