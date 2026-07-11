#!/usr/bin/env python3
"""preview_render.py - software-render a town with fold-billboard buildings.

Best-effort stand-in for an emulator screenshot: same scene the ROM builds —
Emerald ground (footprints flattened, HOENN_GAIN-lifted) plus the exact
fold-billboard geometry `hoenn_buildings._fold_model` generates (vertical
front wall, roof quad rising ROOF_TILT front->back, solid-color sides),
textured with the same `_mask_art` output, viewed from an HGSS-style tilted
camera. Painter's algorithm; perspective-correct textured quads via PIL's
PERSPECTIVE transform.

Differences from the ROM: ground here is raw lifted Emerald pixels (the v6
semantic re-skin swaps them for Gen-4 donor textures), no arealight tint,
no fog. Geometry and building art are pipeline-exact.

Usage: python3 preview_render.py [MAP_LITTLEROOT_TOWN] [out.png]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from PIL import Image

import emeraldmap as em
import hoenn_buildings as hb

SS = 2                      # supersample factor
OUT_W, OUT_H = 1024, 768


def find_coeffs(dst, src):
    """PIL PERSPECTIVE coeffs mapping dst quad -> src quad."""
    a = []
    for (dx, dy), (sx, sy) in zip(dst, src):
        a.append([dx, dy, 1, 0, 0, 0, -sx * dx, -sx * dy])
        a.append([0, 0, 0, dx, dy, 1, -sy * dx, -sy * dy])
    b = np.array([c for s in src for c in s], dtype=float)
    return np.linalg.solve(np.array(a, dtype=float), b)


class Camera:
    """Perspective camera looking at the town center, HGSS-style pitch."""

    def __init__(self, target, dist=520.0, pitch_deg=52.0, fov_deg=38.0,
                 w=OUT_W * SS, h=OUT_H * SS):
        import math
        p = math.radians(pitch_deg)
        self.eye = np.array([target[0],
                             target[1] + dist * math.sin(p),
                             target[2] + dist * math.cos(p)])
        self.target = np.array(target, dtype=float)
        fwd = self.target - self.eye
        self.f = fwd / np.linalg.norm(fwd)
        right = np.cross(self.f, np.array([0.0, 1.0, 0.0]))
        self.r = right / np.linalg.norm(right)
        self.u = np.cross(self.r, self.f)
        self.scale = (h / 2) / math.tan(math.radians(fov_deg) / 2)
        self.w, self.h = w, h

    def project(self, pt):
        v = np.array(pt, dtype=float) - self.eye
        x, y, z = v @ self.r, v @ self.u, v @ self.f
        if z < 1:
            z = 1
        return (self.w / 2 + x * self.scale / z,
                self.h / 2 - y * self.scale / z, z)


def paste_quad(canvas, tex, world_quad, cam):
    """Texture `tex` onto the projection of world_quad (tex corners map
    clockwise from top-left)."""
    proj = [cam.project(p) for p in world_quad]
    xs = [p[0] for p in proj]
    ys = [p[1] for p in proj]
    x0, y0 = int(max(0, min(xs) - 1)), int(max(0, min(ys) - 1))
    x1 = int(min(canvas.width, max(xs) + 1))
    y1 = int(min(canvas.height, max(ys) + 1))
    if x1 <= x0 or y1 <= y0:
        return
    dst = [(p[0] - x0, p[1] - y0) for p in proj]
    src = [(0, 0), (tex.width, 0), (tex.width, tex.height), (0, tex.height)]
    try:
        coeffs = find_coeffs(dst, src)
    except np.linalg.LinAlgError:
        return
    warped = tex.transform((x1 - x0, y1 - y0), Image.PERSPECTIVE, coeffs,
                           Image.NEAREST)
    canvas.alpha_composite(warped, (x0, y0))


def solid_quad(canvas, color, world_quad, cam):
    from PIL import ImageDraw
    proj = [cam.project(p)[:2] for p in world_quad]
    ImageDraw.Draw(canvas).polygon(proj, fill=color)


def paste_face(canvas, tex, face, cam, wrap=(True, True, False, False)):
    """Textured tri/quad with per-face UVs in texels (repeat/flip-aware)."""
    from PIL import Image, ImageDraw
    import math
    pts = [v[0] for v in face]
    uvs = [v[1] for v in face]
    us = [u for u, _ in uvs]
    vs = [v for _, v in uvs]
    rep_s, rep_t, flip_s, flip_t = wrap
    if 0 <= min(us) and max(us) <= tex.width and 0 <= min(vs) and max(vs) <= tex.height:
        tiled, u0, v0 = tex, 0, 0
    else:
        # cover [floor(min/w)..ceil(max/w)) whole tiles, mirroring when
        # the flip bit is set (DS mirrored-repeat)
        i0 = math.floor(min(us) / tex.width)
        i1 = math.ceil(max(us) / tex.width)
        j0 = math.floor(min(vs) / tex.height)
        j1 = math.ceil(max(vs) / tex.height)
        tiled = Image.new("RGBA", ((i1 - i0) * tex.width,
                                   (j1 - j0) * tex.height))
        for j in range(j0, j1):
            for i in range(i0, i1):
                t = tex
                if flip_s and i % 2:
                    t = t.transpose(Image.FLIP_LEFT_RIGHT)
                if flip_t and j % 2:
                    t = t.transpose(Image.FLIP_TOP_BOTTOM)
                if not rep_s and i != 0:
                    continue
                if not rep_t and j != 0:
                    continue
                tiled.alpha_composite(t, ((i - i0) * tex.width,
                                          (j - j0) * tex.height))
        u0, v0 = i0 * tex.width, j0 * tex.height
    src = [(u - u0, v - v0) for u, v in uvs]

    proj = [cam.project(p) for p in pts]
    xs = [p[0] for p in proj]
    ys = [p[1] for p in proj]
    x0, y0 = int(max(0, min(xs) - 1)), int(max(0, min(ys) - 1))
    x1 = int(min(canvas.width, max(xs) + 2))
    y1 = int(min(canvas.height, max(ys) + 2))
    if x1 <= x0 or y1 <= y0:
        return
    dst = [(p[0] - x0, p[1] - y0) for p in proj]
    try:
        if len(pts) == 4:
            coeffs = find_coeffs(dst, src)
            warped = tiled.transform((x1 - x0, y1 - y0), Image.PERSPECTIVE,
                                     coeffs, Image.NEAREST)
        else:
            a = np.array([[dst[i][0], dst[i][1], 1, 0, 0, 0] for i in range(3)] +
                         [[0, 0, 0, dst[i][0], dst[i][1], 1] for i in range(3)])
            b = np.array([src[i][0] for i in range(3)] +
                         [src[i][1] for i in range(3)])
            c = np.linalg.solve(a, b)
            warped = tiled.transform((x1 - x0, y1 - y0), Image.AFFINE,
                                     (c[0], c[1], c[2], c[3], c[4], c[5]),
                                     Image.NEAREST)
            mask = Image.new("L", warped.size, 0)
            ImageDraw.Draw(mask).polygon(dst, fill=255)
            warped.putalpha(Image.composite(
                warped.getchannel("A"), Image.new("L", warped.size, 0), mask))
    except np.linalg.LinAlgError:
        return
    canvas.alpha_composite(warped, (x0, y0))


DONOR_BY_TYPE = {"house": 20, "lab": 21, "pokecenter": 2, "mart": 1, "gym": 5}
MODEL_UNIT_PX = 16          # 1 model unit == 1 tile == 16 art px


def draw_donor(canvas, model, cx, cz, cam, scale=1.0):
    """Project a decoded vanilla model at ground position (cx, 0, cz)."""
    s = MODEL_UNIT_PX * scale
    faces = []
    for mat_id, f in model.faces():
        world = [((cx + x * s, y * s, cz + z * s), uv) for (x, y, z), uv in f]
        centroid = np.mean([p for p, _ in world], axis=0)
        depth = (centroid - cam.eye) @ cam.f
        faces.append((depth, mat_id, world))
    from PIL import ImageDraw
    for _d, mat_id, world in sorted(faces, key=lambda t: -t[0]):
        tex = model.texture_image(mat_id)
        if "kage" in model.tex_name(mat_id):
            # ground shadow: engine blends it; approximate at 35% black
            proj = [cam.project(v[0])[:2] for v in world]
            ov = canvas.copy()
            ImageDraw.Draw(ov).polygon(proj, fill=(0, 0, 0, 255))
            canvas.paste(Image.blend(canvas, ov, 0.35))
            continue
        if tex is None:
            solid_quad(canvas, (120, 120, 130, 255), [v[0] for v in world], cam)
        else:
            paste_face(canvas, tex, world, cam, model.wrap_flags(mat_id))


def render(mid="MAP_LITTLEROOT_TOWN", out_path=None, donor=False):
    mb = hb.MapBuildings(mid)
    m = mb.m
    ground = m.render().convert("RGBA")
    ground = Image.eval(ground, lambda v: min(255, round(v * hb.HOENN_GAIN)))

    raw = m.render()
    builds = []
    for b in mb.extract():
        x0, y0, x1, y1 = b["rect"]
        b["art"] = raw.crop((x0 * 16, y0 * 16, (x1 + 1) * 16, (y1 + 1) * 16))
        art = hb._mask_art(mb, b)
        art = Image.eval(art, lambda v: min(255, round(v * hb.HOENN_GAIN)))
        builds.append({"rect": b["rect"], "img": art, "type": b["type"]})
        # flatten footprint to the door-approach row (matches the importer)
        patch = ground.crop((x0 * 16, (y1 + 1) * 16,
                             (x1 + 1) * 16, (y1 + 2) * 16))
        for ty in range(y0, y1 + 1):
            ground.paste(patch, (x0 * 16, ty * 16))

    W, H = ground.size                    # world: 1 art px = 1 unit
    cam = Camera(target=(W / 2, 0, H / 2 + 20))
    canvas = Image.new("RGBA", (OUT_W * SS, OUT_H * SS), (18, 18, 26, 255))

    paste_quad(canvas, ground,
               [(0, 0, 0), (W, 0, 0), (W, 0, H), (0, 0, H)], cam)

    if donor:
        import mdlview
        from narc import narc_read
        bm = narc_read(os.path.join(
            hb.ROOT, "disasm/pokeheartgold/files/fielddata/build_model/"
            "bm_field.narc"))
        cache = {}
        for b in sorted(builds, key=lambda b: b["rect"][1]):
            x0, y0, x1, y1 = b["rect"]
            did = DONOR_BY_TYPE.get(b["type"], 20)
            if did not in cache:
                cache[did] = mdlview.Model(bm[did])
            mdl = cache[did]
            # scale the donor to the Hoenn footprint width (what a real
            # drop-in integration would tune via the matshp locator)
            xs = [v[0][0] for _, f in mdl.faces() for v in f]
            fit = ((x1 - x0 + 1) * 16) / ((max(xs) - min(xs)) * MODEL_UNIT_PX)
            cx = (x0 + x1 + 1) * 8
            cz = (y0 + y1 + 1) * 8
            draw_donor(canvas, mdl, cx, cz, cam, scale=fit)
        canvas = canvas.resize((OUT_W, OUT_H), Image.LANCZOS)
        out_path = out_path or os.path.join(hb.OUT, f"render_{mid}_donor.png")
        canvas.convert("RGB").save(out_path)
        print("wrote", out_path)
        return

    # painter's: farthest (smallest z back) first == north to south
    for b in sorted(builds, key=lambda b: b["rect"][1]):
        x0, y0, x1, y1 = b["rect"]
        img = b["img"]
        w, h = img.size
        cx = (x0 + x1 + 1) * 8            # center x in px
        zf = (y1 + 1) * 16                # south (front) edge
        zb = y0 * 16                      # north (back) edge
        wall = min(hb.WALL_PX_SHORT if h <= 80 else hb.WALL_PX_TALL, h)
        roof_v = h - wall
        tilt = hb.ROOF_TILT if roof_v > 0 else 0
        hw = w / 2.0
        side = img.crop((2, h - wall + 2, min(10, w), h - wall + 10)).resize((1, 1))
        scol = tuple(side.getpixel((0, 0)))

        # side + back solids (drawn first)
        for face in (
            [(cx + hw, wall, zf), (cx + hw, wall + tilt, zb),
             (cx + hw, 0, zb), (cx + hw, 0, zf)],
            [(cx - hw, wall + tilt, zb), (cx - hw, wall, zf),
             (cx - hw, 0, zf), (cx - hw, 0, zb)],
            [(cx + hw, wall + tilt, zb), (cx - hw, wall + tilt, zb),
             (cx - hw, 0, zb), (cx + hw, 0, zb)],
        ):
            solid_quad(canvas, scol, face, cam)
        if roof_v > 0:
            roof_tex = img.crop((0, 0, w, roof_v))
            paste_quad(canvas, roof_tex,
                       [(cx - hw, wall + tilt, zb), (cx + hw, wall + tilt, zb),
                        (cx + hw, wall, zf), (cx - hw, wall, zf)], cam)
        wall_tex = img.crop((0, roof_v, w, h))
        paste_quad(canvas, wall_tex,
                   [(cx - hw, wall, zf), (cx + hw, wall, zf),
                    (cx + hw, 0, zf), (cx - hw, 0, zf)], cam)

    canvas = canvas.resize((OUT_W, OUT_H), Image.LANCZOS)
    out_path = out_path or os.path.join(hb.OUT, f"render_{mid}.png")
    canvas.convert("RGB").save(out_path)
    print("wrote", out_path)


def _here_hc():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "hoennconv")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--donor"]
    render(*(args or ()), donor="--donor" in sys.argv)
