"""This cave's install step (johto_caves/cave_install.py; cave.py names the cave).

    python3 tools/gba/maps/dragons_den/install.py ENGINE
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / 'johto_caves')]
import cave_install                                    # noqa: E402

if __name__ == '__main__':
    cave_install.main(Path(sys.argv[1]).resolve())
