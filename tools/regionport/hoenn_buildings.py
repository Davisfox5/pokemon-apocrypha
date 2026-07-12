#!/usr/bin/env python3
"""hoenn_buildings.py - extract building footprints + art from Emerald maps.

For every map in the Hoenn stitch, finds enterable buildings (seeded from
warp_events door tiles), flood-filling over "structure" cells:
    collision != 0 AND (secondary-tileset metatile OR layer COVERED/SPLIT)
then growing the bbox upward over passable roof rows (secondary + COVERED/
SPLIT). Result per building: {map, type, doors, rect}; art = crop from the
rendered map. Buildings deduped by art content hash.

Standalone: `python hoenn_buildings.py` prints stats + writes a contact
sheet to build/hoenn_buildings.png + build/hoenn_buildings.json.
Imported by import_hoenn.py for footprint flattening + prop generation.
"""
import json
import os
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emeraldmap as em                    # noqa: E402
from PIL import Image                      # noqa: E402

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
EMER = os.path.join(ROOT, "disasm", "pokeemerald")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build")

LAYER_COVERED, LAYER_SPLIT = 1, 2

# GBA-era art reads noticeably darker than DS-native maps under the same
# arealight tint; lift everything baked from Emerald by a shared gain so
# Hoenn's ground and buildings match Johto/Sinnoh brightness.
HOENN_GAIN = 1.12
_GAIN_LUT = [min(255, round(i * HOENN_GAIN)) for i in range(256)]


def lift(c):
    return (_GAIN_LUT[c[0]], _GAIN_LUT[c[1]], _GAIN_LUT[c[2]])

TYPE_PATTERNS = [
    ("POKEMON_CENTER", "pokecenter"), ("MART", "mart"), ("GYM", "gym"),
    ("MUSEUM", "museum"), ("HARBOR", "harbor"), ("SHIPYARD", "shipyard"),
    ("BATTLE_TENT", "battletent"), ("FAN_CLUB", "fanclub"),
    ("CONTEST", "contest"), ("SCHOOL", "school"), ("LEAGUE", "league"),
    ("INSTITUTE", "institute"), ("STATION", "station"), ("CABLE_CAR", "cablecar"),
    ("FLOWER_SHOP", "flowershop"), ("DAY_CARE", "daycare"), ("HOUSE", "house"),
    ("COTTAGE", "house"), ("LAB", "lab"),
]


def infer_type(dest):
    for pat, t in TYPE_PATTERNS:
        if pat in dest:
            return t
    return "house"


class MapBuildings:
    def __init__(self, mid):
        self.m = em.MapData(mid)
        m = self.m
        # raw attrs for layer type (metatile_def masks them off)
        self._prim = em.load_tileset(m.layout["primary_tileset"])
        self._sec = em.load_tileset(m.layout["secondary_tileset"])

    def cell(self, x, y):
        m = self.m
        if not (0 <= x < m.w and 0 <= y < m.h):
            return None
        v = m.blocks[y * m.w + x]
        mt, coll = v & 0x3FF, (v >> 10) & 3
        if mt < em.NUM_METATILES_PRIMARY:
            attrs = self._prim[1]
            raw = attrs[mt] if mt < len(attrs) else 0
        else:
            attrs = self._sec[1]
            i = mt - em.NUM_METATILES_PRIMARY
            raw = attrs[i] if i < len(attrs) else 0
        layer = (raw >> 12) & 0xF
        return {"mt": mt, "coll": coll, "layer": layer,
                "sec": mt >= em.NUM_METATILES_PRIMARY}

    def is_structure(self, x, y):
        c = self.cell(x, y)
        return bool(c and c["coll"] and (c["sec"] or c["layer"] in (LAYER_COVERED, LAYER_SPLIT)))

    def is_roofish(self, x, y):
        c = self.cell(x, y)
        return bool(c and c["sec"] and c["layer"] in (LAYER_COVERED, LAYER_SPLIT))

    def is_body(self, x, y):
        """Building-body cell: impassable at elevation 0 (fences/cliffs sit
        at elevation 3, so this cleanly isolates structures)."""
        m = self.m
        if not (0 <= x < m.w and 0 <= y < m.h):
            return False
        v = m.blocks[y * m.w + x]
        return bool((v >> 10) & 3) and ((v >> 12) & 0xF) == 0

    def common_ground(self):
        if not hasattr(self, "_cg"):
            from collections import Counter
            m = self.m
            cnt = Counter()
            for v in m.blocks:
                if not ((v >> 10) & 3):
                    cnt[v & 0x3FF] += 1
            self._cg = {mt for mt, _ in cnt.most_common(30)}
        return self._cg

    def _is_ridge_cell(self, c):
        """Walk-behind roof-row cell: passable, MB_NORMAL, and with real
        top-layer art. (Common-ground membership was the old test; on small
        maps the ridge tiles themselves crack the top-30 list — Littleroot's
        houses kept a baked roof strip in the ground.)"""
        if c is None or c["coll"]:
            return False
        mt = c["mt"]
        if not hasattr(self, "_ridge_memo"):
            self._ridge_memo = {}
        v = self._ridge_memo.get(mt)
        if v is None:
            if mt < em.NUM_METATILES_PRIMARY:
                raw = self._prim[1][mt] if mt < len(self._prim[1]) else 0
            else:
                i = mt - em.NUM_METATILES_PRIMARY
                raw = self._sec[1][i] if i < len(self._sec[1]) else 0
            tl = _top_layer_tile(self, mt)
            v = (raw & 0xFF) == 0 and any(
                px is not None for row in tl for px in row)
            self._ridge_memo[mt] = v
        return v

    def extract(self):
        """[{type, doors:[(x,y)], rect, ground_rows}] — rectangle-grown from
        each warp door: up the door column over body cells, widened while
        whole columns of the band are body, then up to 3 roof-art rows."""
        m = self.m
        buildings = []
        for w in m.json.get("warp_events", []):
            x, y, dest = int(w["x"]), int(w["y"]), w["dest_map"]
            btype = infer_type(dest)
            # door row = bottom of the body; door tile itself is a body cell
            if not self.is_body(x, y):
                if self.is_body(x, y - 1):
                    y -= 1
                else:
                    continue
            y1 = y
            y0 = y
            while y0 > 0 and self.is_body(x, y0 - 1):
                y0 -= 1
            def col_solid(cx):
                return all(self.is_body(cx, cy) for cy in range(y0, y1 + 1))
            x0 = x1 = x
            while x0 > 0 and col_solid(x0 - 1):
                x0 -= 1
            while x1 < m.w - 1 and col_solid(x1 + 1):
                x1 += 1
            g0 = y0
            # roof-art rows: passable rows above whose tiles aren't ground
            ry = y0
            for _ in range(3):
                if ry == 0:
                    break
                row = [self.cell(cx, ry - 1) for cx in range(x0, x1 + 1)]
                odd = sum(1 for c in row if self._is_ridge_cell(c))
                if odd < (x1 - x0 + 1) * 0.7:
                    break
                ry -= 1
            merged = False
            for b in buildings:
                bx0, by0, bx1, by1 = b["rect"]
                if not (x1 < bx0 or bx1 < x0 or y1 < by0 or by1 < y0):
                    b["doors"].append((x, y1))
                    b["rect"] = (min(bx0, x0), min(by0, ry), max(bx1, x1), max(by1, y1))
                    b["ground_rows"] = (min(b["ground_rows"][0], g0),
                                        max(b["ground_rows"][1], y1))
                    merged = True
                    break
            if not merged:
                buildings.append({"type": btype, "doors": [(x, y1)],
                                  "rect": (x0, ry, x1, y1),
                                  "ground_rows": (g0, y1)})
        return buildings


def collect(map_ids):
    """{mid: [buildings]}, each building + 'art' PIL image."""
    out = OrderedDict()
    for mid in map_ids:
        try:
            mb = MapBuildings(mid)
        except Exception as e:
            print(f"  {mid}: skip ({e})")
            continue
        bs = mb.extract()
        if not bs:
            continue
        img = mb.m.render()
        for b in bs:
            x0, y0, x1, y1 = b["rect"]
            b["art"] = img.crop((x0 * 16, y0 * 16, (x1 + 1) * 16, (y1 + 1) * 16))
        out[mid] = bs
    return out


# ============================ generation ================================= #
# The parts below turn extracted buildings into HGSS prop assets. Flow
# (driven from import_hoenn.py):
#   prepare()      extract -> clamp -> mask -> dedupe -> select под budgets
#                  -> flatten surviving footprints in the stitched ckey grid
#   build_props()  fold-billboard BMD0 per distinct art + one NSBTX (pltt16,
#                  one 16-color palette per art) + build list + matshp/anim
#                  extensions (mirrors the Sinnoh prop-import pipeline)
#   inject_props() splice 48-byte MapPropFile entries into the generated
#                  land chunks (32 per chunk max, chunk-local fx32 coords)

import struct                                                    # noqa: E402
import nsbmd                                                     # noqa: E402
from narc import narc_read, narc_write                           # noqa: E402

HG = os.path.join(ROOT, "disasm", "pokeheartgold")

MAX_RECT_W, MAX_RECT_H = 14, 12   # tiles; bigger structures stay 2D
MAX_ARTS = 68                     # 550-slot model-file array: 480 used + head-room
TEXEL_BUDGET = 150_000            # 4bpp texel bytes. The v7 ground texset is
                                  # ~42K (254 authentic 16px arts); v5 shipped
                                  # 163K ground + 40K props without VRAM
                                  # corruption, so ~150K of props keeps the
                                  # total at that proven ~200K level and
                                  # promotes far more of the region's ~115
                                  # building instances from flat-baked ground
                                  # art to 3D fold-billboard props.
DOWNSCALE_PX = 128                # arts wider/taller than this use half-res
                                  # textures (world size unchanged)
BASE_MODELS = 480                 # vanilla 340 + sinnoh import 140
WALL_PX_SHORT, WALL_PX_TALL = 32, 48
ROOF_TILT = 16                    # world units of roof rise front->back
RIDGE_PX = 12                     # top art rows folded up as the ridge

NO_ANIM_MEMBER = bytes.fromhex("ffff000000000000" + "ff" * 16)


def _top_layer_tile(mb, mt):
    """Render ONLY the top layer of a metatile (color 0 transparent) — the
    exact pixels the GBA composites over the ground, i.e. clean roof art
    without the baked background."""
    m = mb.m
    mdef, _ = m.metatile_def(mt)
    out = [[None] * 16 for _ in range(16)]
    if mdef is None:
        return out
    pals = m.palettes()
    for sub in range(4):
        v = mdef[4 + sub]
        tid, hf, vf, pal = v & 0x3FF, v & 0x400, v & 0x800, (v >> 12) & 0xF
        rows = m.subtile_pixels(tid)
        colors = pals[pal] if pal < len(pals) else [(0, 0, 0)] * 16
        ox, oy = (sub % 2) * 8, (sub // 2) * 8
        for ry in range(8):
            srow = rows[7 - ry] if vf else rows[ry]
            for rx in range(8):
                ci = srow[7 - rx] if hf else srow[rx]
                if ci == 0:
                    continue
                out[oy + ry][ox + rx] = colors[ci] if ci < len(colors) else (0, 0, 0)
    return out


_tile_color_cache = {}


def _tile_colors(mb, mt):
    """Set of RGB colors a metatile renders (both layers)."""
    key = (id(mb), mt)
    if key not in _tile_color_cache:
        m = mb.m
        mdef, _ = m.metatile_def(mt)
        cols = set()
        if mdef is not None:
            pals = m.palettes()
            for sub in range(8):
                v = mdef[sub]
                tid, pal = v & 0x3FF, (v >> 12) & 0xF
                rows = m.subtile_pixels(tid)
                colors = pals[pal] if pal < len(pals) else []
                for row in rows:
                    for ci in row:
                        if ci and ci < len(colors):
                            cols.add(colors[ci])
        _tile_color_cache[key] = cols
    return _tile_color_cache[key]


def _mask_art(mb, b):
    """Crop art with non-building cells keyed out (alpha 0). Roof-art rows
    (above the collision body) are re-rendered from the metatiles' TOP layer
    only, so the ground behind the roof never bakes into the texture."""
    x0, y0, x1, y1 = b["rect"]
    g0 = b["ground_rows"][0]
    cg = mb.common_ground()
    art = b["art"].convert("RGBA")
    px = art.load()
    doors = set(b["doors"])
    for ty in range(y0, y1 + 1):
        for tx in range(x0, x1 + 1):
            c = mb.cell(tx, ty)
            if ty < g0:
                # roof overdraw row: top-layer pixels only
                keep_cell = c and c["mt"] not in cg and not c["coll"]
                top = _top_layer_tile(mb, c["mt"]) if keep_cell else None
                for dy in range(16):
                    for dx in range(16):
                        v = top[dy][dx] if top else None
                        px[(tx - x0) * 16 + dx, (ty - y0) * 16 + dy] = (
                            (v[0], v[1], v[2], 255) if v else (0, 0, 0, 0))
                continue
            keep = mb.is_body(tx, ty) or (tx, ty) in doors
            if not keep:
                for dy in range(16):
                    for dx in range(16):
                        px[(tx - x0) * 16 + dx, (ty - y0) * 16 + dy] = (0, 0, 0, 0)
    # Roof-edge cells in BODY rows (sloped corners, side eaves) are SPLIT
    # layer type: their roof pixels live in the top layer and the baked
    # grass in the bottom layer — re-render those cells top-layer-only,
    # exactly like the roof overdraw rows above the body.
    for ty in range(g0, y1 + 1):
        for tx in range(x0, x1 + 1):
            c = mb.cell(tx, ty)
            if not c or c["layer"] != LAYER_SPLIT:
                continue
            if not (mb.is_body(tx, ty) or (tx, ty) in doors):
                continue
            top = _top_layer_tile(mb, c["mt"])
            for dy in range(16):
                for dx in range(16):
                    v = top[dy][dx]
                    px[(tx - x0) * 16 + dx, (ty - y0) * 16 + dy] = (
                        (v[0], v[1], v[2], 255) if v else (0, 0, 0, 0))
    return art


def _ring_fill(mb, b):
    """Fill metatile for the flattened footprint: prefer the ground directly
    south of the building (the door-approach row — usually pavement), then
    the 1-cell ring."""
    from collections import Counter
    x0, y0, x1, y1 = b["rect"]
    south = Counter()
    for tx in range(x0, x1 + 1):
        for dy in (1, 2):
            c = mb.cell(tx, y1 + dy)
            if c and not c["coll"] and c["layer"] == 0:
                south[c["mt"]] += 1
    if south:
        return south.most_common(1)[0][0]
    cnt = Counter()
    for tx in range(x0 - 1, x1 + 2):
        for ty in (y0 - 1, y1 + 1):
            c = mb.cell(tx, ty)
            if c and not c["coll"] and c["layer"] == 0:
                cnt[c["mt"]] += 1
    for ty in range(y0, y1 + 1):
        for tx in (x0 - 1, x1 + 1):
            c = mb.cell(tx, ty)
            if c and not c["coll"] and c["layer"] == 0:
                cnt[c["mt"]] += 1
    return cnt.most_common(1)[0][0] if cnt else None


def prepare(origins, ckey):
    """Extract + select buildings; flatten surviving footprints in ckey.
    Returns {"arts": [art dicts], "instances": [instance dicts]}."""
    arts = OrderedDict()          # key -> art dict
    instances = []
    for mid, (gx, gy, w, h) in origins.items():
        try:
            mb = MapBuildings(mid)
        except Exception:
            continue
        for b in mb.extract():
            x0, y0, x1, y1 = b["rect"]
            bw, bh = x1 - x0 + 1, y1 - y0 + 1
            if bw < 2 or bh < 2 or bw > MAX_RECT_W or bh > MAX_RECT_H:
                continue
            img = mb.m.render()
            b["art"] = img.crop((x0 * 16, y0 * 16, (x1 + 1) * 16, (y1 + 1) * 16))
            masked = _mask_art(mb, b)
            # perceptual dedupe: same type+size+per-tile mean color = same
            # building (exact bytes differ across towns via baked background
            # corners around roof edges)
            thumb = masked.convert("RGB").resize(
                (max(1, masked.size[0] // 16), max(1, masked.size[1] // 16)),
                Image.BILINEAR)
            sig = bytes(v >> 4 for v in thumb.tobytes())
            key = (b["type"], masked.size, sig)
            if key not in arts:
                arts[key] = {"img": masked, "type": b["type"], "n": 0,
                             "id": len(arts)}
            arts[key]["n"] += 1
            gy0, gy1 = b["ground_rows"]
            instances.append({
                "map": mid, "art_key": key, "type": b["type"],
                "gx0": gx + x0, "gz0": gy + y0, "gx1": gx + x1, "gz1": gy + y1,
                "g_ground0": gy + gy0, "g_ground1": gy + gy1,
                "fill_mt": _ring_fill(mb, b),
            })
    # selection under budgets: most-instanced arts first
    ranked = sorted(arts.values(), key=lambda a: -a["n"])
    kept_orig, texels = set(), 0
    for a in ranked:
        w, h = a["img"].size
        if w > DOWNSCALE_PX or h > DOWNSCALE_PX:
            w, h = w // 2, h // 2
        pw, ph = 1 << (w - 1).bit_length(), 1 << (h - 1).bit_length()
        if pw - w < 8 and ph - h < 8:
            ph *= 2   # matches _quantize16's patch row
        cost = pw * ph // 2
        if len(kept_orig) >= MAX_ARTS or texels + cost > TEXEL_BUDGET:
            continue
        kept_orig.add(a["id"])
        texels += cost
    live_arts = [a for a in arts.values() if a["id"] in kept_orig]
    for i, a in enumerate(live_arts):
        a["id"] = i
        a["keep"] = True
    live = []
    for inst in instances:
        a = arts[inst["art_key"]]
        if a.get("keep"):
            inst["art_id"] = a["id"]
            live.append(inst)
    # flatten surviving footprints
    for inst in live:
        m = inst["map"]
        fill = inst["fill_mt"]
        if fill is None:
            continue
        for gz in range(inst["gz0"], inst["gz1"] + 1):
            for gx in range(inst["gx0"], inst["gx1"] + 1):
                if 0 <= gz < len(ckey) and 0 <= gx < len(ckey[0]) and ckey[gz][gx]:
                    ckey[gz][gx] = (m, fill)
    print(f"buildings: {len(instances)} found, {len(live)} kept "
          f"({len(live_arts)} models, {texels // 1024}K texels)")
    return {"arts": live_arts, "instances": live}


def _pack_normal(nx, ny, nz):
    def q(v):
        return int(max(-512, min(511, round(v * 511)))) & 0x3FF
    return q(nx) | (q(ny) << 10) | (q(nz) << 20)


def _faces_dl(faces):
    """faces: [(normal(3), [4 x ((x,y,z),(s,t))])] -> packed DL (quads)."""
    cmds = [(nsbmd.G_BEGIN, [1])]
    for normal, verts in faces:
        cmds.append((nsbmd.G_NORMAL, [_pack_normal(*normal)]))
        for (wx, wy, wz), (s, t) in verts:
            st = (int(round(s * 16)) & 0xFFFF) | ((int(round(t * 16)) & 0xFFFF) << 16)
            cmds.append((nsbmd.G_TEXCOORD, [st]))
            cmds.append((nsbmd.G_VTX_16,
                         [nsbmd.fx(wx) | (nsbmd.fx(wy) << 16), nsbmd.fx(wz)]))
    cmds.append((nsbmd.G_END, []))
    return nsbmd.pack_dl(cmds)


def _quantize16(img, wall_rows=0):
    """RGBA -> (4bpp texels padded to pow2, 32B BGR555 palette, pw, ph,
    patch_uv, strip). Color 0 = transparent. An 8x8 solid wall-color patch
    is placed in the padding for the back wall; when wall_rows is given, an
    8xwall_rows strip of the front wall's edge columns is baked below it
    for the side walls (strip = (x, y, w, h) in texels, or None)."""
    w, h = img.size
    rgb = img.convert("RGB")
    alpha = img.split()[3]
    apx = alpha.load()
    rpx = rgb.load()
    for y in range(h):
        for x in range(w):
            rpx[x, y] = lift(rpx[x, y])
    # wall color = average of bottom-row opaque pixels
    wall = [0, 0, 0]
    n = 0
    for x in range(w):
        if apx[x, h - 1]:
            c = rpx[x, h - 1]
            wall[0] += c[0]; wall[1] += c[1]; wall[2] += c[2]; n += 1
    wall = tuple(v // max(n, 1) for v in wall)
    # transparent pixels -> wall color so they don't waste palette slots
    for y in range(h):
        for x in range(w):
            if not apx[x, y]:
                rpx[x, y] = wall
    q = rgb.quantize(colors=15, dither=Image.Dither.NONE)
    qpx = q.load()
    pal = (q.getpalette() + [0] * 45)[:45]
    # nearest palette slot for the wall color
    best, bd = 0, 1 << 30
    for i in range(15):
        r, g, bl = pal[i * 3:i * 3 + 3]
        d = (r - wall[0]) ** 2 + (g - wall[1]) ** 2 + (bl - wall[2]) ** 2
        if d < bd:
            best, bd = i, d
    pw = 1 << max(3, (w - 1).bit_length())
    ph = 1 << max(3, (h - 1).bit_length())
    if pw - w < 8 and ph - h < 8:
        ph *= 2   # room for the patch
    idx = bytearray(pw * ph)   # 0 = transparent
    for y in range(h):
        for x in range(w):
            if apx[x, y]:
                idx[y * pw + x] = qpx[x, y] + 1
    # 8x8 patch location: right padding if any, else below the art
    if pw - w >= 8:
        px0, py0 = w, 0
    else:
        px0, py0 = 0, h
    for y in range(py0, py0 + 8):
        for x in range(px0, px0 + 8):
            idx[y * pw + x] = best + 1
    # side-wall strip: the first mostly-OPAQUE 8px column band of the wall
    # rows (edge columns can be transparent/keyed corners — sampling them
    # leaves a grass-colored seam between front and side), baked below the
    # patch so side faces show connected wall texture instead of flat color
    strip = None
    wall_r = wall_rows if wall_rows and wall_rows <= h else 0
    if wall_r and py0 + 8 + wall_r <= ph and px0 + 8 <= pw:
        sx0 = 0
        for x in range(0, max(1, w - 8)):
            if sum(1 for y in range(h - wall_r, h) if apx[x, y]) >= wall_r * 0.9:
                sx0 = x
                break
        sy = py0 + 8
        for y in range(wall_r):
            yy = h - wall_r + y
            src = best + 1
            for x in range(8):
                xx = min(sx0 + x, w - 1)
                if apx[xx, yy]:
                    src = qpx[xx, yy] + 1
                idx[(sy + y) * pw + (px0 + x)] = src
        strip = (px0, sy, 8, wall_r)
    texels = bytearray(pw * ph // 2)
    for i in range(0, pw * ph, 2):
        texels[i // 2] = idx[i] | (idx[i + 1] << 4)
    palbin = bytearray(32)
    for i in range(15):
        r, g, bl = pal[i * 3:i * 3 + 3]
        struct.pack_into("<H", palbin, (i + 1) * 2,
                         (r >> 3) | ((g >> 3) << 5) | ((bl >> 3) << 10))
    return bytes(texels), bytes(palbin), pw, ph, (px0 + 4, py0 + 4), strip


def _fold_model(art, name, ground_d_px):
    """Fold-billboard building model. Origin: ground center of footprint."""
    img = art["img"]
    w, h = img.size
    ts = 1   # texel scale: art px per texel
    if w > DOWNSCALE_PX or h > DOWNSCALE_PX:
        ts = 2
        # NEAREST, not BOX: box-averaging blends the (0,0,0) keyed-out pixels
        # into building edges as dark fringes
        img = img.resize((w // 2, h // 2), Image.NEAREST)
    wall = WALL_PX_SHORT if h <= 80 else WALL_PX_TALL
    wall = min(wall, h)
    texels, palbin, pw, ph, patch, strip = _quantize16(img, wall // ts)
    hw = w / 2.0
    hd = ground_d_px / 2.0
    roof_v = h - wall            # art rows used by the roof
    tilt = ROOF_TILT if roof_v > 0 else 0
    pu, pv = patch
    if strip:
        sx, sy, sw, sh = strip
        s_uv = [(sx, sy), (sx + sw, sy), (sx + sw, sy + sh), (sx, sy + sh)]
    else:
        s_uv = [(pu, pv)] * 4
    faces = []
    # front wall (south, +z)
    faces.append(((0, 0, 1), [
        ((-hw, wall, hd), (0, (h - wall) / ts)),
        ((hw, wall, hd), (w / ts, (h - wall) / ts)),
        ((hw, 0, hd), (w / ts, h / ts)),
        ((-hw, 0, hd), (0, h / ts)),
    ]))
    # roof overhangs the walls; the top art rows fold up as the ridge so the
    # far side of a gabled roof reads as a surface, not a cut line
    OV = 3
    hwo, hdo = hw + OV, hd + OV
    ridge = RIDGE_PX if roof_v >= 24 else 0
    if roof_v > 0:
        # main slope: front edge y=wall at z=+hdo, back y=wall+tilt at -hdo
        faces.append(((0, 0.97, 0.24), [
            ((-hwo, wall + tilt, -hdo), (0, ridge / ts)),
            ((hwo, wall + tilt, -hdo), (w / ts, ridge / ts)),
            ((hwo, wall, hdo), (w / ts, roof_v / ts)),
            ((-hwo, wall, hdo), (0, roof_v / ts)),
        ]))
    if ridge:
        rl = ridge / ts
        faces.append(((0, 0.6, -0.8), [
            ((-hwo, wall + tilt + ridge * 0.8, -hdo - ridge * 0.6), (0, 0)),
            ((hwo, wall + tilt + ridge * 0.8, -hdo - ridge * 0.6), (w / ts, 0)),
            ((hwo, wall + tilt, -hdo), (w / ts, rl)),
            ((-hwo, wall + tilt, -hdo), (0, rl)),
        ]))
    # sides: front wall's edge-column strip, top of strip at the eave line
    faces.append(((1, 0, 0), [
        ((hw, wall, hd), s_uv[0]), ((hw, wall + tilt, -hd), s_uv[1]),
        ((hw, 0, -hd), s_uv[2]), ((hw, 0, hd), s_uv[3]),
    ]))
    faces.append(((-1, 0, 0), [
        ((-hw, wall + tilt, -hd), s_uv[0]), ((-hw, wall, hd), s_uv[1]),
        ((-hw, 0, hd), s_uv[2]), ((-hw, 0, -hd), s_uv[3]),
    ]))
    # back wall (north, -z): strip too — flat color otherwise
    faces.append(((0, 0, -1), [
        ((hw, wall + tilt, -hd), s_uv[0]), ((-hw, wall + tilt, -hd), s_uv[1]),
        ((-hw, 0, -hd), s_uv[2]), ((hw, 0, -hd), s_uv[3]),
    ]))
    dl = _faces_dl(faces)
    empty = nsbmd.pack_dl([(nsbmd.G_BEGIN, [1]), (nsbmd.G_END, [])])
    model = nsbmd.build_model([dl] + [empty] * 7,
                              [(pw, ph)] * 8,
                              tex_names=[name] * 8,
                              pal_names=[name + "_p"] * 8,
                              wrap_repeat_slots=0)
    return model, (name, pw, ph, texels, 3), (name + "_p", palbin)


def build_props(binfo):
    """Returns (models bytes list, btx bytes, texel_total). Also extends
    bm_field/a040/matshp/a107 NARC files on disk (truncating to the
    post-Sinnoh baseline first, so re-runs are idempotent)."""
    models, textures, palettes = [], [], []
    for a in sorted(binfo["arts"], key=lambda a: a["id"]):
        name = f"hb{a['id']:02d}"
        # depth from the widest instance of this art (they share footprints)
        insts = [i for i in binfo["instances"] if i["art_id"] == a["id"]]
        d_px = max((i["g_ground1"] - i["g_ground0"] + 1) for i in insts) * 16
        model, tex, pal = _fold_model(a, name, d_px)
        models.append(model)
        textures.append(tex)
        palettes.append(pal)
    btx = nsbmd.build_btx_named(textures, palettes)

    bm_path = os.path.join(HG, "files/fielddata/build_model/bm_field.narc")
    a040_path = os.path.join(HG, "files/a/0/4/0")
    matshp_path = os.path.join(HG, "files/fielddata/build_model/bm_field_matshp.dat")
    anim_path = os.path.join(HG, "files/a/1/0/7")
    bm = narc_read(bm_path)[:BASE_MODELS]
    anim = narc_read(anim_path)[:BASE_MODELS]
    assert len(bm) == BASE_MODELS, "run import_sinnoh.py first"
    with open(matshp_path, "rb") as f:
        ms = f.read()
    loc_n, ids_n = struct.unpack_from("<HH", ms, 0)
    locs = [struct.unpack_from("<HH", ms, 4 + i * 4) for i in range(min(loc_n, BASE_MODELS))]
    ids_keep = 0
    for cnt, idx in locs:
        if cnt:
            ids_keep = max(ids_keep, idx + cnt)
    ids_blob = ms[4 + loc_n * 4:4 + loc_n * 4 + ids_n * 4][:ids_keep * 4]
    # each building gets ONE (mat0, shp0) pair — HGSS renders exactly the
    # locator's pairs (a count of 0 draws NOTHING, unlike Platinum's C which
    # falls back to a full-model draw)
    ids_blob = bytearray(ids_blob)
    for m in models:
        bm.append(m)
        anim.append(NO_ANIM_MEMBER)
        locs.append((1, len(ids_blob) // 4))
        ids_blob += struct.pack("<HH", 0, 0)
    new_ms = struct.pack("<HH", len(locs), len(ids_blob) // 4)
    new_ms += b"".join(struct.pack("<HH", c, i) for c, i in locs)
    new_ms += bytes(ids_blob)
    narc_write(bm_path, bm)
    narc_write(a040_path, bm)
    narc_write(anim_path, anim)
    with open(matshp_path, "wb") as f:
        f.write(new_ms)
    build_list = struct.pack("<H", len(models)) + b"".join(
        struct.pack("<H", BASE_MODELS + i) for i in range(len(models)))
    print(f"props: {len(models)} models (ids {BASE_MODELS}..{BASE_MODELS + len(models) - 1}), "
          f"btx {len(btx) // 1024}K")
    return build_list, btx


def inject_props(land, models_grid, binfo, CW, CH):
    """Splice MapPropFile entries into the generated land members."""
    per_chunk = {}
    for inst in binfo["instances"]:
        cxpx = (inst["gx0"] + inst["gx1"] + 1) * 16 / 2.0
        czpx = (inst["g_ground0"] + inst["g_ground1"] + 1) * 16 / 2.0
        cx, cy = int(cxpx // 512), int(czpx // 512)
        if not (0 <= cx < CW and 0 <= cy < CH) or models_grid[cy][cx] == 0xFFFF:
            continue
        lx = cxpx - (cx * 512 + 256)
        lz = czpx - (cy * 512 + 256)
        per_chunk.setdefault((cx, cy), []).append(
            (BASE_MODELS + inst["art_id"], lx, lz))
    placed = dropped = 0
    for (cx, cy), allprops in per_chunk.items():
        props = allprops[:32]
        dropped += max(0, len(allprops) - 32)
        mi = models_grid[cy][cx]
        b = land[mi]
        ps, prs, ms_, bs = struct.unpack_from("<4I", b, 0)
        assert prs == 0, "chunk already has props"
        blob = b"".join(
            struct.pack("<i3i3i3i2i", mid,
                        int(lx * 4096), 0, int(lz * 4096),
                        0, 0, 0,
                        4096, 4096, 4096, 0, 0)
            for mid, lx, lz in props)
        head = b[16:16 + 4 + ps]          # 0x1234 block + perms
        rest = b[16 + 4 + ps:]            # model + bdhc
        land[mi] = (struct.pack("<4I", ps, len(blob), ms_, bs)
                    + head + blob + rest)
        placed += len(props)
    print(f"props placed: {placed} ({dropped} dropped by 32/chunk cap)")


def main():
    _, _, origins = em.stitch(["MAP_LITTLEROOT_TOWN", "ALL"])
    allb = collect(list(origins))
    total = sum(len(v) for v in allb.values())
    # dedupe by art bytes
    arts = OrderedDict()
    for mid, bs in allb.items():
        for b in bs:
            key = (b["art"].size, b["art"].tobytes())
            arts.setdefault(key, {"type": b["type"], "n": 0, "img": b["art"],
                                  "id": len(arts)})
            arts[key]["n"] += 1
            b["art_id"] = arts[key]["id"]
    print(f"{total} buildings on {len(allb)} maps; {len(arts)} distinct arts")
    sizes = {}
    tex4 = tex8 = 0
    for a in arts.values():
        w, h = a["img"].size
        pw = 1 << (w - 1).bit_length()
        ph = 1 << (h - 1).bit_length()
        tex4 += pw * ph // 2
        tex8 += pw * ph
        sizes[(w // 16, h // 16)] = sizes.get((w // 16, h // 16), 0) + 1
    print("footprint sizes (tiles):", dict(sorted(sizes.items())))
    print(f"texture bytes if 4bpp: {tex4} ({tex4/1024:.0f}K), 8bpp: {tex8/1024:.0f}K")
    from collections import Counter
    print("types:", Counter(a["type"] for a in arts.values()))
    # contact sheet
    cols = 10
    cw = max(a["img"].size[0] for a in arts.values())
    ch = max(a["img"].size[1] for a in arts.values())
    rows = (len(arts) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cw, rows * ch), (30, 30, 30))
    for i, a in enumerate(arts.values()):
        sheet.paste(a["img"], ((i % cols) * cw, (i // cols) * ch))
    os.makedirs(OUT, exist_ok=True)
    sheet.save(os.path.join(OUT, "hoenn_buildings.png"))
    meta = {mid: [{k: v for k, v in b.items() if k != "art"} for b in bs]
            for mid, bs in allb.items()}
    with open(os.path.join(OUT, "hoenn_buildings.json"), "w") as f:
        json.dump(meta, f, indent=1)
    print("wrote build/hoenn_buildings.png + .json")


if __name__ == "__main__":
    main()
