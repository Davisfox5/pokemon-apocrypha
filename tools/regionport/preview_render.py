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
    if tex.mode != "RGBA":
        tex = tex.convert("RGBA")
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

    # ---- other 3-D-ified elements: trees + signs ------------------------- #
    def cell_art(tx, ty):
        return raw.crop((tx * 16, ty * 16, (tx + 1) * 16, (ty + 1) * 16))

    def greenish(im):
        g = t = 0
        for r, gr, bl, a in im.convert("RGBA").getdata():
            if a:
                t += 1
                if gr > r * 1.12 and gr > bl * 1.12:
                    g += 1
        return t and g / t > 0.5

    in_rect = set()
    for b in builds:
        x0, y0, x1, y1 = b["rect"]
        in_rect |= {(tx, ty) for tx in range(x0, x1 + 1)
                    for ty in range(y0, y1 + 1)}
    common = mb.common_ground()
    common_img = None
    for ty in range(m.h):
        for tx in range(m.w):
            c = mb.cell(tx, ty)
            if c and c["mt"] in common:
                common_img = Image.eval(cell_art(tx, ty),
                                        lambda v: min(255, round(v * hb.HOENN_GAIN)))
                break
        if common_img is not None:
            break

    objects = []      # (south_z, kind, payload)
    tree_cells = set()
    _tree_memo = {}

    def is_tree(tx, ty):
        if not (0 <= tx < m.w and 0 <= ty < m.h) or (tx, ty) in in_rect:
            return False
        if (tx, ty) not in _tree_memo:
            solid = (m.blocks[ty * m.w + tx] >> 10) & 3
            _tree_memo[(tx, ty)] = bool(solid) and greenish(cell_art(tx, ty))
        return _tree_memo[(tx, ty)]

    # segment each column's tree run into 2-cell canopies from the bottom up
    for tx in range(m.w):
        ty = m.h - 1
        while ty >= 0:
            if not is_tree(tx, ty) or (tx, ty) in tree_cells:
                ty -= 1
                continue
            top = ty
            while top - 1 >= 0 and is_tree(tx, top - 1):
                top -= 1
            yb = ty
            while yb >= top:
                hcells = 2 if yb - 1 >= top else 1
                tex = raw.crop((tx * 16, (yb - hcells + 1) * 16,
                                (tx + 1) * 16, (yb + 1) * 16))
                tex = Image.eval(tex,
                                 lambda v: min(255, round(v * hb.HOENN_GAIN)))
                for k in range(hcells):
                    tree_cells.add((tx, yb - k))
                objects.append(((yb + 1) * 16, "billboard",
                                (tex, tx * 16 + 8, (yb + 1) * 16,
                                 16, hcells * 16)))
                yb -= hcells
            ty = top - 1
    for ev in (mb.m.json.get("bg_events") or []):
        tx, ty = int(ev.get("x", -1)), int(ev.get("y", -1))
        if not (0 <= tx < m.w and 0 <= ty < m.h) or (tx, ty) in in_rect:
            continue
        tex = Image.eval(cell_art(tx, ty),
                         lambda v: min(255, round(v * hb.HOENN_GAIN)))
        objects.append(((ty + 1) * 16, "billboard",
                        (tex, tx * 16 + 8, (ty + 1) * 16, 16, 16)))
        tree_cells.add((tx, ty))
    # flatten billboarded cells in the ground
    if common_img is not None:
        for (tx, ty) in tree_cells:
            ground.paste(common_img, (tx * 16, ty * 16))

    # border apron: the GBA repeats border.bin (a 2x2-metatile block, the
    # forest ring for towns) outside the layout — render it around the map
    # so edges are enclosed instead of dropping into the void
    APRON = 6            # tiles each side (multiple of 2)
    border_img = None
    try:
        import struct as _st
        braw = open(os.path.join(hb.EMER,
                                 m.layout["border_filepath"]), "rb").read()
        bmts = _st.unpack("<4H", braw[:8])
        border_img = Image.new("RGBA", (32, 32))
        pals = m.palettes()
        for bi, mt in enumerate(bmts):
            mdef, _ = m.metatile_def(mt)
            if mdef is None:
                continue
            tile = Image.new("RGBA", (16, 16))
            tp = tile.load()
            for layer in range(2):
                for sub in range(4):
                    v = mdef[layer * 4 + sub]
                    tid, hf, vf, pal = (v & 0x3FF, v & 0x400, v & 0x800,
                                        (v >> 12) & 0xF)
                    rows = m.subtile_pixels(tid)
                    colors = pals[pal] if pal < len(pals) else []
                    for ry in range(8):
                        srow = rows[7 - ry] if vf else rows[ry]
                        for rx in range(8):
                            ci = srow[7 - rx] if hf else srow[rx]
                            if layer == 1 and ci == 0:
                                continue
                            if ci < len(colors):
                                tp[(sub % 2) * 8 + rx, (sub // 2) * 8 + ry] = (
                                    *colors[ci], 255)
            border_img.paste(tile, ((bi % 2) * 16, (bi // 2) * 16))
        border_img = Image.eval(border_img,
                                lambda v: min(255, round(v * hb.HOENN_GAIN)))
    except Exception:
        APRON = 0
    if APRON:
        big = Image.new("RGBA", (W + APRON * 32, H + APRON * 32))
        for by in range(0, big.height, 32):
            for bx in range(0, big.width, 32):
                big.paste(border_img, (bx, by))
        big.paste(ground, (APRON * 16, APRON * 16))
        ground = big
        A = APRON * 16
        # billboard the apron's inner ring so the enclosure reads as 3-D
        for bx in range(-A, W + A, 32):
            objects.append((0, "billboard",
                            (border_img, bx + 16, 0, 32, 32)))
            objects.append((H + A, "billboard",
                            (border_img, bx + 16, H + A, 32, 32)))
        for bz in range(32, H + A, 32):
            objects.append((bz, "billboard", (border_img, -A + 16, bz, 32, 32)))
            objects.append((bz, "billboard",
                            (border_img, W + A - 16, bz, 32, 32)))
    else:
        A = 0

    # re-blit ground (it changed) before drawing objects
    canvas = Image.new("RGBA", (OUT_W * SS, OUT_H * SS), (18, 18, 26, 255))
    paste_quad(canvas, ground,
               [(-A, 0, -A), (W + A, 0, -A), (W + A, 0, H + A), (-A, 0, H + A)],
               cam)

    for b in builds:
        objects.append(((b["rect"][3] + 1) * 16, "building", b))

    OV = 3            # roof overhang, art px
    for _z, kind, payload in sorted(objects, key=lambda o: o[0]):
        if kind == "billboard":
            tex, bx, bz, bw, bh = payload
            paste_quad(canvas, tex,
                       [(bx - bw / 2, bh, bz), (bx + bw / 2, bh, bz),
                        (bx + bw / 2, 0, bz), (bx - bw / 2, 0, bz)], cam)
            continue
        b = payload
        x0, y0, x1, y1 = b["rect"]
        img = b["img"]
        w, h = img.size
        cx = (x0 + x1 + 1) * 8
        zf = (y1 + 1) * 16
        zb = y0 * 16
        wall = min(hb.WALL_PX_SHORT if h <= 80 else hb.WALL_PX_TALL, h)
        roof_v = h - wall
        tilt = hb.ROOF_TILT if roof_v > 0 else 0
        hw = w / 2.0
        hwo = hw + OV

        # side strip: first mostly-opaque 8px column band of the wall rows,
        # alpha holes filled so no grass/transparent seam at the corner
        a = img.split()[3]
        sx0 = 0
        for x in range(0, max(1, w - 8)):
            col = [a.getpixel((x, y)) for y in range(roof_v, h)]
            if sum(1 for v in col if v > 128) >= len(col) * 0.9:
                sx0 = x
                break
        strip = img.crop((sx0, roof_v, sx0 + 8, h)).convert("RGBA")
        sp = strip.load()
        for y in range(strip.height):
            row = [sp[x, y] for x in range(8) if sp[x, y][3]]
            fillc = row[len(row) // 2] if row else (120, 120, 120, 255)
            for x in range(8):
                if not sp[x, y][3]:
                    sp[x, y] = fillc

        # true gabled shell (mirrors hoenn_buildings._gable_model): two roof
        # slopes meeting at a ridge + textured triangular gable ends
        ridge = 12 if roof_v >= 24 else 0
        rise = min(24, max(14, roof_v - ridge - 4)) if ridge else \
            hb.ROOF_TILT if roof_v else 0
        zr = zb + (zf - zb) * (1 - 0.35)     # ridge z, 35% from the back
        if not ridge:
            zr = zb - OV

        # back wall, then back slope (mostly hidden)
        paste_quad(canvas, strip,
                   [(cx + hw, wall, zb), (cx - hw, wall, zb),
                    (cx - hw, 0, zb), (cx + hw, 0, zb)], cam)
        if ridge:
            if hb.ridge_rows_uniform(img, ridge):
                back_tex = img.crop((0, 0, w, ridge)).transpose(
                    Image.FLIP_TOP_BOTTOM)
            else:
                back_tex = img.crop((0, ridge, w, min(2 * ridge, roof_v)))
            paste_quad(canvas, back_tex,
                       [(cx + hwo, wall + rise, zr), (cx - hwo, wall + rise, zr),
                        (cx - hwo, wall, zb - OV), (cx + hwo, wall, zb - OV)],
                       cam)
        # gable ends + side walls
        for sgn in (1, -1):
            x = cx + sgn * hw
            paste_quad(canvas, strip,
                       [(x, wall, zf), (x, wall, zb),
                        (x, 0, zb), (x, 0, zf)], cam)
            if ridge:
                tw, th2 = strip.width, strip.height
                paste_face(canvas, strip,
                           [((x, wall + rise, zr), (tw / 2, 0)),
                            ((x, wall, zb), (0, th2)),
                            ((x, wall, zf), (tw, th2))], cam)
        # front slope + front wall
        if roof_v > 0:
            roof_tex = img.crop((0, ridge, w, roof_v))
            paste_quad(canvas, roof_tex,
                       [(cx - hwo, wall + rise, zr), (cx + hwo, wall + rise, zr),
                        (cx + hwo, wall, zf + OV), (cx - hwo, wall, zf + OV)],
                       cam)
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
