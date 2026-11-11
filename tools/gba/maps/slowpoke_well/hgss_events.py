"""Record this cave's HGSS events (johto_caves/cave_events.py).

    python3 tools/gba/maps/<cave>/hgss_events.py PATH/TO/pokeheartgold OUT_DIR
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / 'johto_caves')]
import cave_events                                    # noqa: E402

if __name__ == '__main__':
    cave_events.main(Path(sys.argv[1]).resolve(), sys.argv[2])
