#!/usr/bin/env python3
"""hoenn_ground.py - Gen-4 semantic ground renderer for the Hoenn import (v6).

Replaces the v1-v5 "GBA pixel quilt" (content-addressed pool + atlas of raw
Emerald tile images) with vanilla Gen-4 terrain art: every tile is classified
semantically (hoenn_texmap.py: behavior -> curated kinds -> hue fallback) and
drawn as merged rects UV-anchored into a SMALL fixed vocabulary of donor
textures pulled from vanilla HGSS/Platinum outdoor texsets (donorlib.py).

Ground is flat (elevation-driven cliff geometry is a later round). Trees are
real geometry: horizontal hedge runs become vertical quads textured with the
vanilla 64x64 canopy, one wall per even row of a tree blob. Sea is two-layer
(sea_un below, cutout sea_on above) like vanilla.

Every chunk binds the SAME texture list in the SAME material slots of the
39-slot chunk template (nsbmd.CHUNK_TEMPLATE_PATH) — unused slots get empty
display lists; there is no per-chunk pool assignment anymore.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import donorlib                                    # noqa: E402
import hoenn_texmap as tm                          # noqa: E402
import nsbmd                                       # noqa: E402
from PIL import Image                              # noqa: E402

# donor texsets to load, in preference order (first hit by name wins)
DONORS = [("hgss", 2), ("hgss", 7), ("hgss", 9), ("hgss", 18),
          ("plat", 6), ("plat", 19)]

# semantic class -> opaque ground texture (donor names; see donor_sheets/)
CLASS_GROUND = {
    "grass": "grass01gs",
    "grass_dark": "grass02",
    "tallgrass": "grass01gs",  # + egrass cutout decal
    "ashgrass": "grass01gs",
    "flowers": "grass01gs",    # + flower01 cutout decal
    "sand": "beach01",
    "road_dirt": "road01",
    "road_pave": "c1_g1",      # Platinum Jubilife plaza tile
    "peak": "allpeakgs",
    "ledge": "wall01_d",
    "cliff": "cliff01gs",
    "tree": "grass01gs",       # + hedge wall quads
    "rock": "cliff01gs",
    "sea": "sea_un",           # + sea_on cutout overlay
    "sea_edge": "sea_un",
    "pond": "pond_un",
    "river": "pond_un",
    "waterfall": "pond_un",
    "bridge": "bridge_c",
    "building": "c1_g1",
    "blocked_misc": "c1_g1",
}
# class -> cutout decal drawn just above its ground layer
OVERLAY = {"sea": "sea_on", "sea_edge": "sea_on",
           "pond": "pond_on", "river": "pond_on", "waterfall": "pond_on",
           "tallgrass": "egrass", "ashgrass": "egrass",
           "flowers": "flower01"}
WATER_CLASSES = {"sea", "sea_edge", "pond", "river", "waterfall"}
TREE_TEX = "tree01gs"
FILL_CLASS = "sea"             # out-of-map tiles are open ocean
WATER_UNDER_Y = -3.0           # water base sits below the cutout surface
DECAL_Y = 0.5                  # grass/flower decals float just off the ground

_lib = None


def _donor_pool():
    """Merged donor texture pool, preference-ordered. Each texture keeps its
    OWN set's palettes so association (donorlib.find_palette + overrides)
    resolves within the donor set the texture came from."""
    global _lib
    if _lib is None:
        texs = {}
        for kind, idx in DONORS:
            t, p = (donorlib.hgss_texset(idx) if kind == "hgss"
                    else donorlib.plat_texset(idx))
            for n, v in t.items():
                texs.setdefault(n, (v, kind, p))
        _lib = texs
    return _lib


class TexSet:
    """The fixed slot list + assembled NSBTX for the shared Hoenn area."""

    def __init__(self):
        texs = _donor_pool()
        want = sorted({t for t in CLASS_GROUND.values()}
                      | set(OVERLAY.values()) | {TREE_TEX})
        missing = [n for n in want if n not in texs]
        assert not missing, (
            f"donor textures missing: {missing}; available sample: "
            f"{sorted(texs)[:60]}")
        self.slots = want
        self.slot_of = {n: i for i, n in enumerate(want)}
        self.dims = {}
        entries, pal_entries, pal_seen = [], [], {}
        self.pal_of = {}
        for n in want:
            v, kind, set_pals = texs[n]
            self.dims[n] = (v["w"], v["h"])
            fmt, texels = v["fmt"], v["texels"]
            if fmt == 2:
                # pltt4 -> pltt16: vanilla marks 4-color palettes with a
                # dict-entry flag our writer doesn't emit (engine misreads
                # them as zebra garbage otherwise); expanding 2bpp->4bpp
                # sidesteps the flag semantics for pennies.
                t4 = bytearray(v["w"] * v["h"] // 2)
                for i, byte in enumerate(texels):
                    for k in range(4):
                        pos = i * 4 + k
                        t4[pos // 2] |= ((byte >> (2 * k)) & 3) << (4 * (pos & 1))
                fmt, texels = 3, bytes(t4)
            entries.append((n, v["w"], v["h"], texels, fmt, not v["c0t"]))
            pn = donorlib.find_palette(n, set_pals, source=kind)
            assert pn, f"no palette for donor texture {n}"
            self.pal_of[n] = pn
            if pn not in pal_seen:
                pal_seen[pn] = True
                pb = set_pals[pn]
                if len(pb) < 32:
                    pb = pb + b"\0" * (32 - len(pb))
                pal_entries.append((pn, pb))
        self.btx = nsbmd.build_btx_named(entries, pal_entries)

    def model_binding(self, num):
        """(tex_names, pal_names, tex_dims, repeat_slots) padded to num."""
        names = list(self.slots)
        pals = [self.pal_of[n] for n in names]
        dims = [self.dims[n] for n in names]
        while len(names) < num:
            names.append(self.slots[0])
            pals.append(self.pal_of[self.slots[0]])
            dims.append(self.dims[self.slots[0]])
        return names, pals, dims, set(range(len(self.slots)))


def classify_grid(mapdatas, ckey, GW, GH, avg_rgb_of):
    """Per-tile semantic class grid. avg_rgb_of(mid, mt) -> (r,g,b)."""
    cls_cache = {}
    sem = [[FILL_CLASS] * GW for _ in range(GH)]
    for z in range(GH):
        for x in range(GW):
            k = ckey[z][x]
            if k is None:
                continue
            c = cls_cache.get(k)
            if c is None:
                mid, mt = k
                m = mapdatas[mid]
                _, beh, layer, short = m.metatile_info(mt)
                c = tm.classify(short, mt, beh, _coll_of(m, mt), layer,
                                avg_rgb_of(mid, mt))
                cls_cache[k] = c
            sem[z][x] = c
    return sem


_coll_cache = {}


def _coll_of(m, mt):
    """Modal collision for a metatile on its own map (cheap, cached)."""
    k = (m.map_id, mt)
    v = _coll_cache.get(k)
    if v is None:
        ones = zero = 0
        for b in m.blocks:
            if (b & 0x3FF) == mt:
                if (b >> 10) & 3:
                    ones += 1
                else:
                    zero += 1
        v = 1 if ones > zero else 0
        _coll_cache[k] = v
    return v


def _anchored_quad(lx, lz, w, h, tw, th, y=0.0):
    """Ground rect with world-anchored UV into a repeating tw x th texture.
    Chunk size (32 tiles) is a multiple of every texture period (1/2/4
    tiles), so local parity == global parity."""
    px, pz = tw // 16, th // 16
    s0 = (lx % px) * 16 if px > 1 else 0
    t0 = (lz % pz) * 16 if pz > 1 else 0
    return _tile_quad_local(lx, lz, w, h, s0, t0, s0 + w * 16, t0 + h * 16, y=y)


def _tile_quad_local(lx, lz, w, h, s0, t0, s1, t1, y=0.0):
    x0, z0 = lx * 16 - 256, lz * 16 - 256
    x1, z1 = x0 + w * 16, z0 + h * 16
    return [((x0, y, z0), (s0, t0)), ((x1, y, z0), (s1, t0)),
            ((x1, y, z1), (s1, t1)), ((x0, y, z1), (s0, t1))]


def _wall_quad(lx, lz, run, height, s0, s1):
    """Vertical quad standing on the south edge of tile row lz, spanning
    run tiles wide and `height` world units tall."""
    x0 = lx * 16 - 256
    x1 = x0 + run * 16
    z = lz * 16 - 256 + 16
    return [((x0, height, z), (s0, 0)), ((x1, height, z), (s1, 0)),
            ((x1, 0, z), (s1, 64)), ((x0, 0, z), (s0, 64))]


def greedy_rects(cells):
    cells = set(cells)
    rects = []
    while cells:
        x, z = min(cells, key=lambda t: (t[1], t[0]))
        w = 1
        while (x + w, z) in cells:
            w += 1
        h = 1
        while all((x + i, z + h) in cells for i in range(w)):
            h += 1
        for i in range(w):
            for j in range(h):
                cells.discard((x + i, z + j))
        rects.append((x, z, w, h))
    return rects


def emit_chunk(ts, sem, cx, cy, GW, GH):
    """Build the 39 shape display lists for one chunk.
    Returns (shape_dls, nverts)."""
    tqs = {}     # slot -> [quads]

    def add(texname, quad):
        tqs.setdefault(ts.slot_of[texname], []).append(quad)

    grid = [[FILL_CLASS] * 32 for _ in range(32)]
    for lz in range(32):
        for lx in range(32):
            gx, gz = cx * 32 + lx, cy * 32 + lz
            if gx < GW and gz < GH:
                grid[lz][lx] = sem[gz][gx]

    # ground + overlay layers: merged rects per texture, world-anchored UVs.
    # Water ground sinks below the cutout surface layer; grass decals float
    # just above the ground so they never z-fight it.
    by_ground, by_over = {}, {}
    for lz in range(32):
        for lx in range(32):
            c = grid[lz][lx]
            by_ground.setdefault(CLASS_GROUND[c], []).append((lx, lz))
            o = OVERLAY.get(c)
            if o:
                by_over.setdefault((o, c in WATER_CLASSES), []).append((lx, lz))
    for g, cells in by_ground.items():
        tw, th = ts.dims[g]
        water = g in ("sea_un", "pond_un")
        for (x, z, w, h) in greedy_rects(cells):
            add(g, _anchored_quad(x, z, w, h, tw, th,
                                  y=WATER_UNDER_Y if water else 0.0))
    for (o, is_water), cells in by_over.items():
        tw, th = ts.dims[o]
        for (x, z, w, h) in greedy_rects(cells):
            add(o, _anchored_quad(x, z, w, h, tw, th,
                                  y=0.0 if is_water else DECAL_Y))

    # trees: hedge walls on even global rows, one run per row
    tw, thh = ts.dims[TREE_TEX]
    for lz in range(32):
        if (cy * 32 + lz) % 2:
            continue
        lx = 0
        while lx < 32:
            if grid[lz][lx] != "tree":
                lx += 1
                continue
            run = 1
            while lx + run < 32 and grid[lz][lx + run] == "tree":
                run += 1
            gx = cx * 32 + lx
            s0 = (gx % (tw // 16)) * 16
            add(TREE_TEX, _wall_quad(lx, lz, run, 64.0, s0, s0 + run * 16))
            lx += run
    shape_dls = []
    nverts = 0
    for k in range(39):
        quads = tqs.get(k, [])
        nverts += 4 * len(quads)
        shape_dls.append(nsbmd.quad_dl(quads))
    return shape_dls, nverts
