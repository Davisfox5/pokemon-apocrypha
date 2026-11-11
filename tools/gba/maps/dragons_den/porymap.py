"""This cave's Porymap round trip (johto_caves/cave_porymap.py; cave.py names the cave).

    python3 tools/gba/maps/dragons_den/porymap.py ENGINE PORYMAP_BINARY
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / 'johto_caves')]
import cave_porymap                                    # noqa: E402

if __name__ == '__main__':
    cave_porymap.main(Path(sys.argv[1]).resolve(), str(Path(sys.argv[2]).resolve()))
