"""This cave's headless mGBA checks (johto_caves/cave_runtime.py; cave.py names the cave).

    python3 tools/gba/maps/slowpoke_well/runtime.py ENGINE OUT_DIR
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / 'johto_caves')]
import cave_runtime                                    # noqa: E402

if __name__ == '__main__':
    cave_runtime.main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
