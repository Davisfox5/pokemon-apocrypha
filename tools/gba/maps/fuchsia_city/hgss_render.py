"""Render HGSS Fuchsia City (MAP_FUCHSIA, area bank 16) from the game's own map data, 1:1 at 16 px per tile.

Reuses the Route 32 renderer (tools/gba/maps/route32_native/hgss_render.py) with Fuchsia's
header id and area data bank. Nothing is replaced in the reference render.

    python3 tools/gba/maps/fuchsia_city/hgss_render.py PATH/TO/pokeheartgold OUT_DIR

Original designs and textures: Game Freak / Nintendo / Creatures (read-only derivation).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'route32_native'))
import hgss_render as base  # noqa: E402

base.AREA_BANK = 16
base.HEADER_ID = 56          # MAP_FUCHSIA (MAP_T08)


def main(phg, out):
    # Fuchsia has no stair material ('slope'), so the Route 32 stair mask is skipped.
    orig = base.render
    def render(phg):
        r = orig(phg)
        if 'slope' not in r['materials']:
            r['materials'] = r['materials'] + ['slope']
        return r
    base.render = render
    base.main(phg, out)

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
