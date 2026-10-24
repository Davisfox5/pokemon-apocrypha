"""Edit HGSS building models as faces before rendering them at C06's angle.

hgss_camera.view renders whole models. Saffron's new buildings are made from parts of
HGSS's own ones (the Dojo from the Fighting Dojo and the Gym, Silph's taller tower and its
lab wing from Silph Co.), so this works on faces: slice a model with axis planes (the
texture coordinates carried along, so a slice keeps its texture exactly), move and copy
slices, swap a face's texture, then render the lot at C06's angle with one horizontal
scale for every part.

    faces = load(models, 255)                      # HGSS model 255, its faces
    part = clip(faces, 'x', -3.3, 1.4)             # keep x in [-3.3, 1.4]
    rgba, to_px = render(part + other, 16)         # 16 px per model unit across
"""
from __future__ import annotations
import math, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import olivine                              # noqa: E402,F401  (puts olivine_elements on the path)
import hgss_render as R                     # noqa: E402
import hgss_camera as C                     # noqa: E402

AXIS = dict(x=0, y=1, z=2)

class Face:
    __slots__ = ('verts', 'uvs', 'mat')

    def __init__(self, verts, uvs, mat):
        self.verts, self.uvs, self.mat = [tuple(v) for v in verts], [tuple(u) for u in uvs], mat

def load(models, mid, offset=(0, 0, 0), skip=('h_kage',), retex=None):
    """A model's textured faces, offset; textures as cutouts (alpha >= 200), the way
    hgss_camera.view draws them. retex maps a texture name to a function of its texture."""
    m = R.mdlview.Model(models[mid])
    mats, out = {}, []
    ox, oy, oz = offset
    for matid, verts in m.faces():
        if matid not in mats:
            mat = R.Material(m, matid, m.tex)
            if mat.tex is not None:
                mat.tex = mat.tex.copy()
                mat.tex[..., 3] = np.where(mat.tex[..., 3] >= 200, 255, 0)
                if retex and mat.name in retex:
                    mat.tex = retex[mat.name](mat.tex)
            mats[matid] = mat
        mat = mats[matid]
        if mat.name in skip or mat.tex is None:
            continue
        out.append(Face([(v[0][0] + ox, v[0][1] + oy, v[0][2] + oz) for v in verts], [v[1] for v in verts], mat))
    return out

def _clip_poly(verts, uvs, a, value, keep_above):
    out_v, out_u = [], []
    n = len(verts)
    for i in range(n):
        p, q = verts[i], verts[(i + 1) % n]
        pu, qu = uvs[i], uvs[(i + 1) % n]
        pin = p[a] >= value if keep_above else p[a] <= value
        qin = q[a] >= value if keep_above else q[a] <= value
        if pin:
            out_v.append(p); out_u.append(pu)
        if pin != qin:
            t = (value - p[a]) / (q[a] - p[a])
            out_v.append(tuple(p[k] + t * (q[k] - p[k]) for k in range(3)))
            out_u.append(tuple(pu[k] + t * (qu[k] - pu[k]) for k in range(2)))
    return out_v, out_u

def clip(faces, axis, lo=-math.inf, hi=math.inf):
    """The parts of faces with lo <= coordinate <= hi on axis, cut exactly at the planes."""
    a = AXIS[axis]
    out = []
    for f in faces:
        v, u = f.verts, f.uvs
        if lo > -math.inf:
            v, u = _clip_poly(v, u, a, lo, True)
        if len(v) >= 3 and hi < math.inf:
            v, u = _clip_poly(v, u, a, hi, False)
        if len(v) >= 3:
            out.append(Face(v, u, f.mat))
    return out

def move(faces, dx=0.0, dy=0.0, dz=0.0):
    return [Face([(x + dx, y + dy, z + dz) for x, y, z in f.verts], f.uvs, f.mat) for f in faces]

def where(faces, test):
    """Faces whose vertices pass test(xyz array (n, 3)) -> bool."""
    return [f for f in faces if test(np.array(f.verts))]

def named(faces, *names):
    return [f for f in faces if f.mat.name in names]

def without(faces, *names):
    return [f for f in faces if f.mat.name not in names]

def retexture(faces, fn, *names):
    """Copies of the named faces' materials with fn applied to their textures."""
    cache, out = {}, []
    for f in faces:
        if f.mat.name not in names:
            out.append(f)
            continue
        if id(f.mat) not in cache:
            m = R.Material.__new__(R.Material)
            m.__dict__.update(f.mat.__dict__)
            m.tex = fn(f.mat.tex.copy())
            cache[id(f.mat)] = m
        out.append(Face(f.verts, f.uvs, cache[id(f.mat)]))
    return out

def extent(faces, axis):
    a = AXIS[axis]
    vals = [v[a] for f in faces for v in f.verts]
    return min(vals), max(vals)

def render(faces, sx, pitch=C.C06_PITCH, sy=C.C06_SCALE, ground=0.1, x_range=None, anchor=None):
    """Faces at C06's angle: orthographic at pitch, sy px per tile up the screen, sx px per
    model unit across. Faces lying on the ground (every vertex below `ground`) are left
    out, as hgss_camera.view leaves them. x_range fixes the sprite's left and right edge
    in model units (else the faces' own extent). anchor, a model point (x, y, z), lands on
    a whole pixel row, so two renders sharing parts draw them on the same pixel rows.
    Returns RGBA and model (x, y, z) -> px."""
    th = math.radians(pitch)
    s, c = math.sin(th), math.cos(th)
    items = [f for f in faces if max(v[1] for v in f.verts) >= ground]
    pts = np.array([p for f in items for p in f.verts])
    xl, xr = x_range if x_range else (pts[:, 0].min(), pts[:, 0].max())
    x0 = xl * sx
    y0 = min((p[2] * s - p[1] * c) * sy for p in pts)
    if anchor is not None:
        v = (anchor[2] * s - anchor[1] * c) * sy
        y0 = v - math.ceil(v - y0)
    to_px = lambda x, y, z: (x * sx - x0, (z * s - y * c) * sy - y0)
    W = int(round((xr - xl) * sx)); H = int(math.ceil(max((p[2] * s - p[1] * c) * sy for p in pts) - y0))
    cv = R.Canvas(W, H)
    for f in items:
        scr = [to_px(*p) for p in f.verts]
        dep = [p[2] * c + p[1] * s for p in f.verts]
        for k in range(1, len(f.verts) - 1):
            cv.tri([scr[0], scr[k], scr[k + 1]], [f.uvs[0], f.uvs[k], f.uvs[k + 1]], [dep[0], dep[k], dep[k + 1]], f.mat, 0)
    rgba = np.zeros((H, W, 4), np.uint8)
    rgba[..., :3] = np.clip(cv.rgb, 0, 255).astype(np.uint8)
    rgba[..., 3] = np.where(cv.mat >= 0, 255, 0)
    render.materials = np.where(cv.mat >= 0, np.array(R.MATERIAL_NAMES + [''], object)[cv.mat], '')
    return rgba, to_px

render.materials = None                         # the last render's texture name per pixel ('' where empty)
