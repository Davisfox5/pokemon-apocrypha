"""Headless mGBA checks for the third-draft Mahogany Town.

    python3 tools/gba/maps/mahogany/runtime3.py ENGINE_CHECKOUT OUT_DIR

The harness is runtime_convert.py's (one fresh emulator process per phase: write, cold
read, title Continue; every capture dumps VRAM, BG palettes and registers and the map
layers rebuilt from that dump must equal the decoded native map pixel for pixel). This
draft's route: views across the town, walk-behind captures on the cells check3.py lists
(BG1 must cover the player's cell), in-front captures at every building (BG1 must leave the
player clear), both ledge directions and the climb-back refusals, every blocked door and
barrier, both signs, the Center and its upper floor, Cherrygrove and back, ordinary flash
save, cold reload and Continue.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import runtime_convert as RC                         # noqa: E402

CITY, CENTER, UPSTAIRS = RC.CITY, RC.CENTER, RC.UPSTAIRS
NATIVE = HERE.parents[3] / 'gba/art/mahogany-town/evidence/pack3/native.png'

RC.STEPS = [
    ('view', CITY, 16, 16, 'town-centre'), ('view', CITY, 22, 24, 'center-approach'), ('view', CITY, 11, 24, 'gym-front'),
    ('view', CITY, 16, 15, 'shop-front'), ('view', CITY, 25, 15, 'east-house-front'), ('view', CITY, 13, 6, 'gate-front'),
    ('view', CITY, 3, 11, 'west-lawn'), ('view', CITY, 17, 9, 'north-road'), ('view', CITY, 30, 16, 'east-road'),
    ('view', CITY, 15, 26, 'south-road'), ('view', CITY, 5, 23, 'gym-lawn-west'), ('view', CITY, 18, 23, 'center-lawn'),
    ('view', CITY, 0, 13, 'west-edge'), ('view', CITY, 20, 8, 'north-woods-edge'), ('view', CITY, 24, 25, 'east-wall'),
    # Walk behind: the top layer covers the player's cell, the object's base stays solid.
    ('go', CITY, 22, 19), ('shot', 'behind-center'), ('south', 1, None), ('at', CITY, 22, 19),
    ('go', CITY, 11, 17), ('shot', 'behind-gym-roof'), ('south', 1, None), ('at', CITY, 11, 17),
    ('go', CITY, 17, 9), ('shot', 'behind-shop-roof'), ('south', 1, None), ('at', CITY, 17, 9),
    ('go', CITY, 4, 11), ('shot', 'behind-town-sign'), ('south', 1, None), ('at', CITY, 4, 11),
    ('go', CITY, 20, 11), ('shot', 'behind-antenna-tree'), ('south', 1, None), ('at', CITY, 20, 11),
    # Ledges: jump south and west, and fail to climb back.
    ('go', CITY, 10, 11), ('south', 1, 'ledge-jump-south'), ('at', CITY, 10, 13), ('north', 1, None), ('at', CITY, 10, 13),
    ('go', CITY, 7, 10), ('west', 1, 'ledge-jump-west'), ('at', CITY, 5, 10), ('east', 1, None), ('at', CITY, 5, 10),
    ('go', CITY, 5, 20), ('south', 1, 'ledge-jump-gym-lawn'), ('at', CITY, 5, 22), ('north', 1, None), ('at', CITY, 5, 22),
    # Blocked: the Center body, the unbuilt Gym, shop and house doors, the unbuilt gate, a tree, a wall, the mountain.
    ('go', CITY, 21, 24), ('north', 1, None), ('at', CITY, 21, 24),
    ('go', CITY, 11, 24), ('north', 1, None), ('at', CITY, 11, 24),
    ('go', CITY, 16, 15), ('north', 1, None), ('at', CITY, 16, 15),
    ('go', CITY, 25, 15), ('north', 1, None), ('at', CITY, 25, 15),
    ('go', CITY, 13, 6), ('north', 1, None), ('at', CITY, 13, 6),
    ('go', CITY, 16, 8), ('north', 1, None), ('at', CITY, 16, 8),
    ('go', CITY, 5, 10), ('north', 1, None), ('at', CITY, 5, 10),
    ('go', CITY, 3, 18), ('west', 1, None), ('at', CITY, 3, 18),
    ('go', CITY, 15, 26), ('south', 1, None), ('at', CITY, 15, 26),
    # Signs.
    ('sign', CITY, 4, 12, 'town-sign'), ('sign', CITY, 8, 24, 'gym-sign'),
    # Center: in, upstairs and back, out.
    ('go', CITY, 22, 24), ('north', 1, None), ('wait', 400), ('map', CENTER, 'center-entry'), ('shot', 'center-interior'),
    ('go', CENTER, 2, 6), ('west', 1, None), ('wait', 400), ('map', UPSTAIRS, 'center-upstairs'), ('shot', 'center-upstairs'),
    ('west', 1, None), ('wait', 400), ('map', CENTER, 'center-stair-return'),
    ('go', CENTER, 7, 7), ('south', 2, None), ('wait', 400), ('at', CITY, 22, 24), ('shot', 'center-exit'),
    ('view', 0, 50, 17, 'regression-cherrygrove'), ('view', CITY, 22, 25, 'return-to-mahogany'),
]
RC.WALK_BEHIND = {'behind-center': (22, 19), 'behind-gym-roof': (11, 17), 'behind-shop-roof': (17, 9), 'behind-town-sign': (4, 11),
                  'behind-antenna-tree': (20, 11)}
RC.IN_FRONT = ('center-approach', 'center-exit', 'gym-front', 'shop-front', 'east-house-front', 'gate-front')
RC.expected = lambda: RC.padded(np.array(Image.open(NATIVE).convert('RGB')).astype(np.int32) >> 3, RC.BORDER)

if __name__ == '__main__':
    RC.main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
