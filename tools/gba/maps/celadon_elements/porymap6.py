"""Porymap round trip for Celadon round 6: open, export, save, diff (round 3's porymap.py).

    python3 tools/gba/maps/celadon_elements/porymap6.py ENGINE_CHECKOUT PORYMAP_BINARY

The city streams its art (celadon_view.c), so Porymap shows its stand-in metatiles, one
flat colour per kind of cell (install6.KINDS): Porymap's export of the city is compared
with install6's stand-in decode (evidence/v6/engine/standin.png), the rooms as before.
Writes evidence/v6/engine/porymap/{results.json,*.png}.
"""
from __future__ import annotations
import shutil, sys
from pathlib import Path

import common as C
import porymap as P

if __name__ == '__main__':
    engine, binary = Path(sys.argv[1]).resolve(), str(Path(sys.argv[2]).resolve())
    ref = C.EV / 'v6' / 'engine'
    stage = ref / 'porymap-reference'
    stage.mkdir(exist_ok=True)
    shutil.copy(ref / 'standin.png', stage / 'native.png')
    P.EV = stage
    P.main(engine, binary)
    out = ref / 'porymap'
    if out.exists():
        shutil.rmtree(out)
    shutil.move(str(stage / 'porymap'), str(out))
    shutil.rmtree(stage)
