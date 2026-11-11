"""Render this cave's HGSS floors (johto_caves/cave_render.py; cave.py names them).

    python3 tools/gba/maps/<cave>/hgss_render.py PATH/TO/pokeheartgold OUT_DIR SIDE
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / 'johto_caves')]
import cave_render                                    # noqa: E402

if __name__ == '__main__':
    cave_render.main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), sys.argv[3])
