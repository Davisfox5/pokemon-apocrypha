"""Gen 3 conversion of HGSS's building models: drawn as pixel art, not shrunk.

A building's HGSS model is rendered orthographically at C06's 38 degree pitch (Olivine's
camera), unsqueezed, at SCALE px per model unit (C06 draws the Center at about 15), supersampled
SS times. Every sample keeps its face, its material and its texel. Then the picture is
drawn the way a Gen 3 artist draws a building:

    faces     each output pixel takes the face that covers most of its SS x SS block, and
              that face's texel nearest the block's centre, so edges stay one pixel sharp
              and no colour is a blend of two surfaces
    light     each face is lit by its orientation (Gen 3's top-left light: roofs and tops
              lightest, south fronts the base, east sides a step darker, west sides a step
              lighter), as whole steps on its material's ramp
    ramps     each material's texels are snapped to its own colours (k-means in 5-bit colour,
              eight), grouped into hue families; a lighting or crease step moves within the
              colour's own family, so a blue frame never turns yellow
    lines     where two faces meet, the lower face's edge pixel takes its ramp's darkest
              shade (a crease line); the silhouette takes C06's outline colour; a top edge
              facing the light takes one step lighter (a highlight)

Returns RGBA art and the model-to-pixel map (as hgss_camera.view does).
"""
from __future__ import annotations
import math
import numpy as np

import common as C

PITCH, SCALE, SS = 38.0, 19.0, 4
OUTLINE = (41, 41, 49)                       # C06's outline

def raster(models, parts, scale=SCALE, pitch=PITCH, skip=('h_kage',), retex=None, ground=0.1):
    """Supersampled render: per sample its face id, material uid, normal class, texel."""
    r = C.R()
    th = math.radians(pitch)
    s, c = math.sin(th), math.cos(th)
    faces = []
    for mid, (ox, oy, oz) in parts:
        m = r.mdlview.Model(models[mid])
        mats = {}
        for matid, verts in m.faces():
            if matid not in mats:
                mat = r.Material(m, matid, m.tex)
                if mat.tex is not None:
                    mat.tex = mat.tex.copy()
                    mat.tex[..., 3] = np.where(mat.tex[..., 3] >= 200, 255, 0)
                    if retex and mat.name in retex:
                        mat.tex = retex[mat.name](mat.tex)
                mats[matid] = mat
            mat = mats[matid]
            if mat.name in skip or mat.tex is None or max(v[0][1] + oy for v in verts) < ground:
                continue
            w = [(v[0][0] + ox, v[0][1] + oy, v[0][2] + oz) for v in verts]
            faces.append((w, [v[1] for v in verts], mat))
    pts = np.array([p for w, _, _ in faces for p in w])
    k = scale * SS
    x0 = pts[:, 0].min() * k
    y0 = min((p[2] * s - p[1] * c) * k for p in pts)
    to_px = lambda x, y, z: (x * k - x0, (z * s - y * c) * k - y0)
    W = int(math.ceil((pts[:, 0].max() * k - x0) / SS)) * SS
    H = int(math.ceil((max((p[2] * s - p[1] * c) * k for p in pts) - y0) / SS)) * SS
    cv = r.Canvas(W, H)
    normals = []
    for fi, (w, uv, mat) in enumerate(faces):
        a, b, d = np.array(w[0]), np.array(w[1]), np.array(w[2])
        n = np.cross(b - a, d - a)
        n = n / (np.linalg.norm(n) or 1)
        normals.append(n)
        scr = [to_px(*p) for p in w]
        dep = [p[2] * c + p[1] * s for p in w]
        for i0, i1, i2 in ([(0, 1, 2)] if len(w) == 3 else [(0, 1, 2), (0, 2, 3)]):
            cv.tri([scr[i0], scr[i1], scr[i2]], [uv[i0], uv[i1], uv[i2]], [dep[i0], dep[i1], dep[i2]], mat, fi)
    return cv, faces, np.array(normals), (lambda x, y, z: tuple(v / SS for v in to_px(x, y, z)))

def light_class(n):
    """Gen 3 lighting step for a face normal (model y up, z toward the viewer, x east):
    tops +1, west faces +1, south fronts 0, east faces -1, undersides -2."""
    nx, ny, nz = n
    if ny > 0.55:
        return 1
    if ny < -0.55:
        return -2
    if abs(nx) > abs(nz):
        return 1 if nx < 0 else -1
    return 0

def downsample(cv):
    """Per output pixel: the face covering most of its block and that face's texel nearest
    the block's centre."""
    H, W = cv.h // SS, cv.w // SS
    own = cv.owner.reshape(H, SS, W, SS).transpose(0, 2, 1, 3).reshape(H, W, SS * SS)
    rgb = cv.rgb.reshape(H, SS, W, SS, 3).transpose(0, 2, 1, 3, 4).reshape(H, W, SS * SS, 3)
    face = np.full((H, W), -1, int)
    col = np.zeros((H, W, 3), np.float32)
    centre = np.array([(i // SS - (SS - 1) / 2) ** 2 + (i % SS - (SS - 1) / 2) ** 2 for i in range(SS * SS)])
    for y in range(H):
        for x in range(W):
            o = own[y, x]
            vals, cnt = np.unique(o, return_counts=True)
            if (vals >= 0).any():
                cnt = np.where(vals >= 0, cnt, 0)
                f = vals[np.argmax(cnt)]
                if cnt.max() * 2 < SS * SS and (o < 0).sum() * 2 > SS * SS:
                    continue                                   # mostly empty: background
                idx = np.nonzero(o == f)[0]
                i = idx[np.argmin(centre[idx])]
                face[y, x], col[y, x] = f, rgb[y, x, i]
    return face, col

def families(cent):
    """Group a material's colours into hue families (greys together), each ordered dark to
    light, so a lighting step stays inside a colour's own family."""
    import colorsys
    hsv = [colorsys.rgb_to_hsv(*(np.array(c) / 31.0)) for c in cent]
    fam = []
    for i, (h, s_, v) in enumerate(hsv):
        grey = s_ < 0.18
        for f in fam:
            j = f[0]
            hj, sj, vj = hsv[j]
            if grey and sj < 0.18 or (not grey and sj >= 0.18 and min(abs(h - hj), 1 - abs(h - hj)) < 0.07):
                f.append(i)
                break
        else:
            fam.append([i])
    lum = lambda c: 3 * c[0] + 4 * c[1] + 2 * c[2]
    return [sorted(f, key=lambda i: lum(cent[i])) for f in fam]

def ramps(face, col, faces, n=8):
    """Each material's colours (k-means in 5-bit colour) and their hue families."""
    import build as B
    out = {}
    uid = np.array([faces[f][2].uid if f >= 0 else -1 for f in face.ravel()]).reshape(face.shape)
    for u in np.unique(uid[uid >= 0]):
        px = (col[uid == u].astype(int) >> 3)
        uc, cnt = np.unique(px, axis=0, return_counts=True)
        k = min(n, len(uc))
        cent = sorted({tuple(int(v) for v in c) for c in B.kmeans_colors(uc, np.sqrt(cnt).astype(float), k)})
        fam = families(cent)
        where = {i: (fi, pos) for fi, f in enumerate(fam) for pos, i in enumerate(f)}
        out[int(u)] = (np.array(cent, int), fam, where)
    return uid, out

def step(ramp, i, d):
    """Colour i moved d steps lighter (d > 0) or darker within its family."""
    cent, fam, where = ramp
    fi, pos = where[i]
    f = fam[fi]
    return f[int(np.clip(pos + d, 0, len(f) - 1))]

def convert(models, parts, scale=SCALE, retex=None, skip=('h_kage',), n=8, light=True):
    cv, faces, normals, to_px = raster(models, parts, scale=scale, retex=retex, skip=skip)
    face, col = downsample(cv)
    uid, rp = ramps(face, col, faces, n)
    H, W = face.shape
    out = np.zeros((H, W, 4), np.uint8)
    lum = lambda c: 3 * c[..., 0] + 4 * c[..., 1] + 2 * c[..., 2]
    level = np.zeros((H, W), int)
    for y in range(H):
        for x in range(W):
            f = face[y, x]
            if f < 0:
                continue
            ramp = rp[int(uid[y, x])]
            c5 = col[y, x].astype(int) >> 3
            i = int(((ramp[0] - c5) ** 2 * [3, 4, 2]).sum(-1).argmin())
            if light:
                i = step(ramp, i, light_class(normals[f]))
            level[y, x] = i
            out[y, x, :3] = [(v << 3) | (v >> 2) for v in ramp[0][i]]
            out[y, x, 3] = 255
    # Crease lines: where a pixel's face differs from the face above or to its left and the
    # neighbour is nearer the viewer's light (a top or a west face), darken one step.
    for y in range(H):
        for x in range(W):
            f = face[y, x]
            if f < 0:
                continue
            ramp = rp[int(uid[y, x])]
            for dy, dx in ((-1, 0), (0, -1)):
                yy, xx = y + dy, x + dx
                if yy < 0 or xx < 0 or face[yy, xx] < 0 or face[yy, xx] == f:
                    continue
                if uid[yy, xx] == uid[y, x] and abs(float(np.dot(normals[f], normals[face[yy, xx]]))) > 0.98:
                    continue                                   # one surface split into triangles
                j = step(ramp, level[y, x], -1)
                out[y, x, :3] = [(v << 3) | (v >> 2) for v in ramp[0][j]]
    a = out[..., 3] > 0
    pad = np.pad(a, 1)
    edge = a & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    out[edge, :3] = OUTLINE
    return out, to_px
