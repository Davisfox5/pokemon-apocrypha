"""Saffron's new building sprites from HGSS's own models (AGENTS.md, Buildings and props).

    python3 tools/gba/maps/saffron/sprites.py PATH/TO/pokeheartgold

The Magnet Train station is new to Saffron since FireRed's day (it came with the line to
Goldenrod in the Gold and Silver era). Its HGSS model (256, `ybc_ln*` textures) and door
(260) are rendered at C06's angle (`hgss_camera.view`), squeezed to HGSS's footprint
width (10.5 cells), in 14 colours of its own plus C06's outline, with one-pixel edge
shifts folded the way the Johto towns' buildings are. Writes
gba/art/saffron-kanto/source/sprites/station.png and origins.json (the door's pixel).
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OLIVINE = HERE.parent / 'olivine_elements'
sys.path[:0] = [str(OLIVINE)]
import hgss_render as R                 # noqa: E402
import hgss_camera as C                 # noqa: E402
import sprites as OS                    # noqa: E402  (palette fit, outline, tile folding)

R.HEADER_ID, R.AREA_BANK = 59, 12       # MAP_SAFFRON (MAP_T11), area data bank 12
ART = ROOT / 'gba/art/saffron-kanto'
OUT = ART / 'source/sprites'
STATION, STATION_DOOR = 256, 260        # HGSS's Saffron placements: (10.44, 2.0, 14.25) and (11.06, 2.0, 16.25)
DOOR_OFFSET = (0.625, 0.0, 2.0038)
STATION_WIDTH = 168                     # HGSS's footprint, 10.5 cells

def station(phg):
    _, _, models, _, _ = R.load(phg)
    rgba, to_px = C.view(models, [(STATION, (0, 0, 0)), (STATION_DOOR, DOOR_OFFSET)], STATION_WIDTH)
    pal = [tuple(v << 3 | v >> 2 for v in c) for c in OS.sprite_palette(rgba, 14)]
    img = OS.finish(rgba, pal)
    parts = {'station': img}
    OS.reuse_tiles(parts, ('station',))
    dx, dy = to_px(*DOOR_OFFSET)
    return parts['station'], rgba, (float(dx), float(dy))

def main(phg):
    OUT.mkdir(parents=True, exist_ok=True)
    img, raw, door = station(phg)
    Image.fromarray(img, 'RGBA').save(OUT / 'station.png')
    Image.fromarray(raw, 'RGBA').save(OUT / 'station-unquantized.png')
    (OUT / 'origins.json').write_text(json.dumps(dict(station=dict(door_px=[round(door[0], 2), round(door[1], 2)],
                                                                    size=[img.shape[1], img.shape[0]])), indent=1) + '\n')
    print('station', img.shape, 'door at', door, 'tiles', OS.unique_tiles(img),
          'colours', len({tuple(c) for c in img[img[..., 3] > 0][:, :3].tolist()}))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
