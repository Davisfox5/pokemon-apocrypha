"""Render HGSS Blackthorn building models through the game's own field camera.

    python3 tools/gba/maps/blackthorn/hgss_camera.py PATH/TO/pokeheartgold OUT.png [MODEL_ID ...]

Blackthorn's map header uses camera type 0 (pokeheartgold src/data/map_headers.h); its
entry in FieldCamera_Create's table (asm/overlay_01_021EABA8.s, ov01_02206478) is
distance 0x29AEC1, pitch 0xDD62 (48.7 degrees down) and a 0x5C1 perspective, so narrow
that the view is close to orthographic. Each model is drawn with that pitch: screen y =
z sin(pitch) - y cos(pitch), at the game's own aspect (ground tiles 16 x 12 px). This is
the shape a player sees in game. Default models: 132 and 133, a Blackthorn house and its
door; 139 16 is the Gym and its door, 235 the standing stone.

The Gen 3 house and Gym sprites are drawn at C06's angle instead (view(), below), since the
owner-locked C06 Center is the accepted Gen 3 reference (Cianwood's
evidence/elements/c06-angle.png has the fit).
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

# C06's angle. Rendering HGSS's own Center model (40, door 15) this way reproduces the
# owner-locked C06 Center: orthographic at 38 degrees, 16 px per tile up the screen,
# squeezed across into its footprint (silhouette overlap 0.943; Cianwood,
# tools/gba/maps/cianwood_elements/hgss_camera.py --c06). Every building is fitted to its
# own footprint the same way.
C06_PITCH, C06_SCALE = 38.0, 16.0

def view(models, parts, width_px, pitch=C06_PITCH, sy=C06_SCALE, skip=('h_kage',), ground=0.1, retex=None):
    """Gen 3 view of HGSS models at C06's angle: orthographic at `pitch`, `sy` px per tile up
    the screen, squeezed across so the visible model is `width_px` wide. parts lists
    (model id, (x, y, z) offset in tiles). Textures are cutouts (alpha >= 200); the
    ground shadow quad (h_kage) and every face lying on the ground (all vertices below
    `ground`: painted shadows and floor mats) are left out. retex maps a texture name to a
    function that returns a replacement texture (marker renders). Returns RGBA and a
    function mapping model (x, y, z) to sprite pixels."""
    th = math.radians(pitch)
    s, c = math.sin(th), math.cos(th)
    items = []
    for mid, (ox, oy, oz) in parts:
        m = R.mdlview.Model(models[mid])
        mats = {}
        for matid, verts in m.faces():
            if matid not in mats:
                mat = R.Material(m, matid, m.tex)
                if mat.tex is not None:              # cutout: a soft shadow painted into a texture stays out
                    mat.tex = mat.tex.copy()
                    mat.tex[..., 3] = np.where(mat.tex[..., 3] >= 200, 255, 0)
                    if retex and mat.name in retex:
                        mat.tex = retex[mat.name](mat.tex)
                mats[matid] = mat
            mat = mats[matid]
            if mat.name in skip or mat.tex is None or max(v[0][1] + oy for v in verts) < ground:
                continue
            items.append(([(v[0][0] + ox, v[0][1] + oy, v[0][2] + oz) for v in verts], [v[1] for v in verts], mat))
    pts = np.array([p for w, _, _ in items for p in w])
    sx = width_px / (pts[:, 0].max() - pts[:, 0].min())
    x0, y0 = pts[:, 0].min() * sx, min((p[2] * s - p[1] * c) * sy for p in pts)
    to_px = lambda x, y, z: (x * sx - x0, (z * s - y * c) * sy - y0)
    W = int(round(width_px)); H = int(math.ceil(max((p[2] * s - p[1] * c) * sy for p in pts) - y0))
    cv = R.Canvas(W, H)
    for w, uv, mat in items:
        scr = [to_px(*p) for p in w]
        dep = [p[2] * c + p[1] * s for p in w]
        for a, b, d in ([(0, 1, 2)] if len(w) == 3 else [(0, 1, 2), (0, 2, 3)]):
            cv.tri([scr[a], scr[b], scr[d]], [uv[a], uv[b], uv[d]], [dep[a], dep[b], dep[d]], mat, 0)
    rgba = np.zeros((H, W, 4), np.uint8)
    rgba[..., :3] = np.clip(cv.rgb, 0, 255).astype(np.uint8)
    rgba[..., 3] = np.where(cv.mat >= 0, 255, 0)
    return rgba, to_px

def main(phg, out, mids):
    _, _, models, _, _ = R.load(phg)
    img = render(models, mids)
    img.resize((img.width * 4, img.height * 4), Image.Resampling.NEAREST).save(out)
    print('pitch %.2f deg, models %s, %dx%d px' % (math.degrees(PITCH), mids, img.width, img.height))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]), [int(v) for v in sys.argv[3:]] or [132, 133])
