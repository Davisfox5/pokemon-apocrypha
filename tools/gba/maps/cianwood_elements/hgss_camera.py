"""Render HGSS Cianwood building models through the game's own field camera.

    python3 tools/gba/maps/cianwood_elements/hgss_camera.py PATH/TO/pokeheartgold OUT.png [MODEL_ID ...]

Cianwood's map header (MAP_CIANWOOD, pokeheartgold src/data/map_headers.h) uses camera
type 0, as Blackthorn's does; its entry in FieldCamera_Create's table
(asm/overlay_01_021EABA8.s, ov01_02206478) is distance 0x29AEC1, pitch 0xDD62 (48.7
degrees down) and a 0x5C1 perspective, so narrow that the view is close to orthographic.
Each model is drawn with that pitch: screen y = z sin(pitch) - y cos(pitch), at the game's
own aspect (ground tiles 16 x 12 px). This is the shape a player sees in game, used as the
reference for the Gen 3 sprites (sprites.py). Default models: 102 and 103, a Cianwood
house and its door; 104 116 the pharmacy, 105 116 the photo studio, 108 16 the Gym,
106 a herb rack, 90 the camera.
"""
from __future__ import annotations
import math, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hgss_render as R                     # noqa: E402

PITCH = math.radians((0x10000 - 0xDD62) / 65536 * 360)

def render(models, mids, px=16, pad=3, ground=(224, 200, 128)):
    ms = [R.mdlview.Model(models[m]) for m in mids]
    s, c = math.sin(PITCH), math.cos(PITCH)
    sy = lambda y, z: z * s - y * c
    pts = [v[0] for m in ms for _, f in m.faces() for v in f]
    x0, x1 = min(p[0] for p in pts) - pad, max(p[0] for p in pts) + pad
    y0 = min(sy(p[1], p[2]) for p in pts) - pad
    y1 = max(sy(p[1], p[2]) for p in pts) + pad
    cv = R.Canvas(int((x1 - x0) * px), int((y1 - y0) * px))
    cv.rgb[:] = ground
    for m in ms:
        mats, opaque, clear = {}, [], []
        for matid, verts in m.faces():
            mat = mats.setdefault(matid, R.Material(m, matid, m.tex))
            scr = [((v[0][0] - x0) * px, (sy(v[0][1], v[0][2]) - y0) * px) for v in verts]
            dep = [v[0][2] * c + v[0][1] * s for v in verts]
            uv = [v[1] for v in verts]
            tris = [(0, 1, 2)] if len(verts) == 3 else [(0, 1, 2), (0, 2, 3)]
            translucent = mat.alpha < 31 or (mat.tex is not None and ((mat.tex[:, :, 3] > 0) & (mat.tex[:, :, 3] < 255)).any())
            for a, b, d in tris:
                (clear if translucent else opaque).append(([scr[a], scr[b], scr[d]], [uv[a], uv[b], uv[d]], [dep[a], dep[b], dep[d]], mat))
        for p, uv, d, mat in opaque:
            cv.tri(p, uv, d, mat, 0)
        for p, uv, d, mat in clear:
            cv.tri(p, uv, d, mat, 0, blend=True)
    return Image.fromarray(np.clip(cv.rgb, 0, 255).astype(np.uint8))

def main(phg, out, mids):
    _, _, models, _, _ = R.load(phg)
    img = render(models, mids)
    img.resize((img.width * 4, img.height * 4), Image.Resampling.NEAREST).save(out)
    print('pitch %.2f deg, models %s, %dx%d px' % (math.degrees(PITCH), mids, img.width, img.height))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]), [int(v) for v in sys.argv[3:]] or [102, 103])
