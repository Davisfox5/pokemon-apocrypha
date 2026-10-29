"""HGSS's pier boards, cut from Route 32's own render (route30_catalog/hgss_render.py, read-only), for the
town's pier and boardwalk.

    python3 tools/gba/maps/cherrygrove_town/hgss_pier.py PATH/TO/pokeheartgold

Writes gba/art/cherrygrove-town/source/hgss/pier.png: one 32 px repeat of Route 32's north-south pier, all
48 px of it (an 8 px rail each side of 32 px of cross boards), and pier.json with its provenance.
Original texture: Game Freak / Nintendo / Creatures (read-only derivation).
"""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'route30_catalog')]
import hgss_render as H                              # noqa: E402

ROUTE_32, AREA_BANK = 36, 3                          # MAP_ROUTE_32 and its area data bank (src/data/map_headers.h)
PIER = (272, 74 * 16, 48, 32)                        # x, y, width, height in the render: cells 17-19, rows 74-75
OUT = HERE.parents[3] / 'gba/art/cherrygrove-town/source/hgss'

def main(phg):
    H.HEADER_ID, H.AREA_BANK = ROUTE_32, AREA_BANK
    full = np.array(H.render(phg)['full'].convert('RGB'))
    x, y, w, h = PIER
    tex = full[y:y + h, x:x + w]
    assert (np.abs(full[y + h:y + 2 * h, x:x + w].astype(int) - tex).max() <= 8), 'the pier does not repeat every 32 px there'
    OUT.mkdir(parents=True, exist_ok=True)
    Image.fromarray(tex).save(OUT / 'pier.png')
    rev = subprocess.run(['git', '-C', str(phg), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    (OUT / 'pier.json').write_text(json.dumps(dict(
        source='pret/pokeheartgold (Davisfox5 fork), MAP_ROUTE_32 rendered by tools/gba/maps/route30_catalog/hgss_render.py',
        revision=rev, render_box=dict(x=x, y=y, width=w, height=h),
        sha256=hashlib.sha256((OUT / 'pier.png').read_bytes()).hexdigest()), indent=1) + '\n')
    print('pier', tex.shape, len({tuple(c) for c in tex.reshape(-1, 3)}), 'colours')

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
