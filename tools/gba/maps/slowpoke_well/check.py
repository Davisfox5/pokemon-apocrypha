"""This cave's check step (johto_caves/cave_check.py; cave.py names the cave).

    python3 tools/gba/maps/slowpoke_well/check.py ENGINE
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / 'johto_caves')]
import cave_check                                    # noqa: E402

if __name__ == '__main__':
    cave_check.main(Path(sys.argv[1]).resolve())
