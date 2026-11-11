"""Render a Johto cave's HGSS floors from the game's own map data (Mt. Mortar's renderer, pointed at
the cave's area bank and matrices).

    python3 tools/gba/maps/<cave>/hgss_render.py PATH/TO/pokeheartgold OUT_DIR SIDE

Original designs and textures: Game Freak / Nintendo / Creatures (read-only derivation).
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import cave

HERE = Path(__file__).resolve().parent

def renderer():
    """mt_mortar/hgss_render.py, its area bank and floors set to the cave's."""
    sp = importlib.util.spec_from_file_location(f'{cave.TOOL}_hgss_render', HERE.parent / 'mt_mortar/hgss_render.py')
    R = importlib.util.module_from_spec(sp); sp.loader.exec_module(R)
    R.AREA_BANK = cave.AREA_BANK
    R.MAPS = {s: dict(header=f['header'], matrix=f['matrix'], zone=f['zone']) for s, f in cave.FLOORS.items()}
    R.MAP = next(iter(cave.FLOORS))
    return R

def main(phg, out, side):
    renderer().main(Path(phg), Path(out), side)
