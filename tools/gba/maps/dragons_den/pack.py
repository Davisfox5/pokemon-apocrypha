"""This cave's pack step (johto_caves/cave_pack.py; cave.py names the cave).

    python3 tools/gba/maps/dragons_den/pack.py ENGINE
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / 'johto_caves')]
import cave_pack                                    # noqa: E402

if __name__ == '__main__':
    cave_pack.main(Path(sys.argv[1]).resolve())
