"""Porymap round trip for Route 7: open, export, save, diff (Celadon's porymap.py).

    python3 tools/gba/maps/route7/porymap7.py ENGINE_CHECKOUT PORYMAP_BINARY

Route 7 streams its art with Celadon's (celadon_view.c), so Porymap shows the stand-in metatiles,
one flat colour per kind of cell (install6.KINDS with the route's): Porymap's export of the route
is compared with install7's stand-in decode (evidence/engine/standin.png). The gate room, Celadon
and Saffron (whose west gate changed) are opened and saved too.
Writes evidence/engine/porymap/{results.json,*.png}.
"""
from __future__ import annotations
import json, shutil, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'celadon_elements'))
import porymap as P            # noqa: E402

ROOT = HERE.parents[3]
REF = ROOT / 'gba/art/route7/evidence/engine'

if __name__ == '__main__':
    engine, binary = Path(sys.argv[1]).resolve(), str(Path(sys.argv[2]).resolve())
    stage = REF / 'porymap-reference'
    stage.mkdir(exist_ok=True)
    shutil.copy(REF / 'standin.png', stage / 'native.png')
    P.EV, P.CITY = stage, 'KantoRoute7'
    P.INTERIORS = ['KantoRoute7Gatehouse', 'KantoCeladonCity', 'KantoSaffronCity']
    P.main(engine, binary)
    out = REF / 'porymap'
    if out.exists():
        shutil.rmtree(out)
    shutil.move(str(stage / 'porymap'), str(out))
    shutil.rmtree(stage)
    r = json.loads((out / 'results.json').read_text())
    r['route7_files_changed'] = [f for f in r['files_changed_by_save'] if 'Route7' in f or 'route7' in f]
    (out / 'results.json').write_text(json.dumps(r, indent=2) + '\n')
    print('route 7 files changed by save:', r['route7_files_changed'], 'export vs stand-in:', r['city_export_vs_native'])
