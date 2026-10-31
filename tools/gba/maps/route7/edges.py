"""HGSS's dirt road edge cells, cut from Route 30 (owner, 2026-10-31: the path edges Johto's routes
30, 32 and 36 already use, square corners, nothing drawn new).

    python3 tools/gba/maps/route7/edges.py PATH/TO/pokeheartgold

Renders HGSS's Route 30 (map header 34, area bank 2) with Olivine's renderer and cuts its straight
road01_r edge cells, two along each side (the edge repeats every 32 px, so a pair tiles), from
stretches with nothing else in them (no tree shadow, no grass tufts):

    n  grass to the north (cells (16, 45), (17, 45))
    s  grass to the south ((6, 50), (7, 50))
    w  grass to the west  ((3, 88), (3, 89))
    e  grass to the east  ((8, 6), (8, 7))

Writes gba/art/route7/source/art/road-edges.png: four rows (n, s, w, e) of two 16 x 16 cells, the
first for even world cells along the edge, the second for odd. compose.road_edges lays them.
"""
from __future__ import annotations
import sys, tempfile
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'olivine_elements'))
import hgss_render as R        # noqa: E402

ROOT = HERE.parents[3]
OUT = ROOT / 'gba/art/route7/source/art/road-edges.png'
HEADER_ID, AREA_BANK = 34, 2                 # MAP_ROUTE_30
CELLS = dict(n=[(16, 45), (17, 45)], s=[(6, 50), (7, 50)], w=[(3, 88), (3, 89)], e=[(8, 6), (8, 7)])
SIDES = 'nswe'

def main(phg):
    R.HEADER_ID, R.AREA_BANK = HEADER_ID, AREA_BANK
    with tempfile.TemporaryDirectory() as tmp:
        R.main(phg, Path(tmp))
        im = np.array(Image.open(Path(tmp) / 'hgss-ground.png').convert('RGB'))
    out = np.zeros((64, 32, 3), np.uint8)
    for i, side in enumerate(SIDES):
        for j, (x, y) in enumerate(CELLS[side]):
            out[i * 16:i * 16 + 16, j * 16:j * 16 + 16] = im[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
    Image.fromarray(out).save(OUT)
    print(OUT)

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
