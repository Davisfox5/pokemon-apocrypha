"""HGSS Violet City's lake bank and landing, cut from its own render (route30_catalog/hgss_render.py,
read-only), for Violet's lake.

    python3 tools/gba/maps/violet_city/hgss_sources.py PATH/TO/pokeheartgold

Writes gba/art/violet-city-review/source/hgss/: lake-bank.png (the north bank, one 16 px repeat: its light
face, dark foot and first water row), landing.png (the central landing with 8 px of lake round it, from
the ground layer, so no bridge or lantern), sources.json (provenance).
Original textures: Game Freak / Nintendo / Creatures (read-only derivation).
"""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'route30_catalog')]
import hgss_render as H                              # noqa: E402

MAP_VIOLET, AREA_BANK = 73, 3                        # MAP_VIOLET and its area data bank (src/data/map_headers.h)
BANK = ('full', 400, 122, 16, 11)                    # layer, x, y, width, height
LANDING = ('ground', 488, 232, 208, 112)
OUT = HERE.parents[3] / 'gba/art/violet-city-review/source/hgss'

def main(phg):
    H.HEADER_ID, H.AREA_BANK = MAP_VIOLET, AREA_BANK
    r = H.render(phg)
    OUT.mkdir(parents=True, exist_ok=True)
    rev = subprocess.run(['git', '-C', str(phg), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    meta = dict(source='pret/pokeheartgold (Davisfox5 fork), MAP_VIOLET rendered by tools/gba/maps/route30_catalog/hgss_render.py',
                revision=rev, files={})
    for name, (layer, x, y, w, h) in (('lake-bank.png', BANK), ('landing.png', LANDING)):
        a = np.array(r[layer].convert('RGB'))[y:y + h, x:x + w]
        Image.fromarray(a).save(OUT / name)
        meta['files'][name] = dict(layer=layer, box=[x, y, w, h], sha256=hashlib.sha256((OUT / name).read_bytes()).hexdigest())
    (OUT / 'sources.json').write_text(json.dumps(meta, indent=1) + '\n')
    print(meta['files'])

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
