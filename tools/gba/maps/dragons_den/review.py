"""This cave's review sheets (johto_caves/cave_review.py; cave.py names the cave).

    python3 tools/gba/maps/dragons_den/review.py ENGINE RUNTIME_DIR
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / 'johto_caves')]
import cave_review                                    # noqa: E402

if __name__ == '__main__':
    cave_review.main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
