"""This cave's assemble step (johto_caves/cave_assemble.py; cave.py names the cave).

    python3 tools/gba/maps/slowpoke_well/assemble.py PHG ENGINE
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / 'johto_caves')]
import cave_assemble                                    # noqa: E402

if __name__ == '__main__':
    cave_assemble.main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
