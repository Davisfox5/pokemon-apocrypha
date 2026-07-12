#!/usr/bin/env python3
"""hoenn_ground.py - authentic-art semantic ground renderer (v7).

v6 re-skinned Hoenn with vanilla Gen-4 donor textures; the owner verdict
(2026-07-11: littleroot_A_vs_B.png review + the v6 Slateport screenshots)
was that donor art reads as Johto — Hoenn keeps its own art. v7 ships the
Emerald art itself, at full 16px, on v6's rendering machinery:

- every unique ground metatile ART (16x16 RGB, brightness-lifted,
  content-hashed) becomes a 4bpp pltt16 texture. The NNS resdict format
  indexes entries with single bytes, so ONE texset holds at most 255
  names — the top ~230 arts by occurrence are kept (GBA tilemaps are
  repetitive; that's the bulk of all tiles) at a trivial ~32KB of VRAM
- per semantic class a BASE texture (that class's most common art)
  absorbs the long tail: unkept arts demote to their class base
- chunks bind up to 39 textures EACH (per-chunk material-name patching,
  39-slot template map_data_242): the chunk's class bases + its
  top-covering detail arts; a per-chunk vertex cap demotes the rarest
  details further until every 2x2 chunk window stays under the DS budget
- same-art runs merge into repeat-UV rects (period = 1 tile), which keeps
  vertices low without v5's supertile/atlas machinery
- trees are 32-tall wall quads over per-column 2-cell segments (bottom-up
  segmentation like preview_render.py, computed globally so chunk borders
  don't shift the phase), textured with the region's most common vertical
  tree-art pairs (16x32, opaque)
- palettes: exact-color quantize (dither NONE — the v5 fuzz lesson) +
  first-fit grouping into 16-color palettes, so palette VRAM stays a few
  KB like vanilla
"""
import sys
import os
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hoenn_texmap as tm                          # noqa: E402
import nsbmd                                       # noqa: E402
from PIL import Image                              # noqa: E402

FILL_CLASS = "sea"             # out-of-map tiles are open ocean
MAX_TEX = 254                  # NNS resdict hard cap: u8 node/entry indices
CHUNK_VERT_CAP = 1300          # any 2x2 chunk window <= 5200 (DS ~6144)
MAX_SLOTS = 39                 # chunk template material count
TREE_KEEP = 6                  # distinct tree-pair wall textures kept
TREE_WALL_H = 32.0             # 2 tiles tall, matches the 16x32 pair art


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


def _quant16(img, ncolors=16):
    """Exact-color 555 palette + index rows for a small RGB image.
    Returns (palette555 list, [[idx]]). dither=NONE always (v5 lesson)."""
    cs = img.getcolors(img.width * img.height)
    cset = {(r >> 3, g >> 3, b >> 3) for _, (r, g, b) in cs}
    if len(cset) > ncolors:
        img = img.quantize(colors=ncolors,
                           dither=Image.Dither.NONE).convert("RGB")
        cset = {(r >> 3, g >> 3, b >> 3)
                for _, (r, g, b) in img.getcolors(ncolors)}
    px = img.load()
    return sorted(cset), px


class TexSet:
    """Region art census -> NSBTX + per-cell texture resolution tables."""

    def __init__(self, mapdatas, ckey, sem, GW, GH, tile_image):
        # ---- census: art bytes per cell, occurrence counts, class votes --- #
        art = [[None] * GW for _ in range(GH)]
        counts = Counter()
        cls_votes = {}
        for z in range(GH):
            row_c, row_k, row_a = sem[z], ckey[z], art[z]
            for x in range(GW):
                k = row_k[x]
                if k is None:
                    continue
                a = tile_image(k[0], k[1])
                row_a[x] = a
                counts[a] += 1
                cls_votes.setdefault(a, Counter())[row_c[x]] += 1
        self.artgrid = art
        cls_of = {a: v.most_common(1)[0][0] for a, v in cls_votes.items()}

        # ---- bases: most common art per class (ground under trees=grass) - #
        base_art = {}
        for a, _ in counts.most_common():
            c = cls_of[a]
            if c != "tree" and c not in base_art:
                base_art[c] = a
        assert FILL_CLASS in base_art, "no sea art found for the fill class"
        if "grass" not in base_art:
            base_art["grass"] = base_art[FILL_CLASS]
        base_art["tree"] = base_art["grass"]

        # ---- tree wall segments (GLOBAL, so chunk borders keep phase) ----- #
        # per column: bottom-up 2-cell segmentation of vertical tree runs
        pair_counts = Counter()
        self.tree_segs = {}          # (cx, cy) -> [(gx, zbot, pairkey)]
        for x in range(GW):
            z = GH - 1
            while z >= 0:
                if sem[z][x] != "tree":
                    z -= 1
                    continue
                top = z
                while top - 1 >= 0 and sem[top - 1][x] == "tree":
                    top -= 1
                zb = z
                while zb >= top:
                    zt = max(top, zb - 1)
                    pk = (art[zt][x], art[zb][x])
                    pair_counts[pk] += 1
                    self.tree_segs.setdefault((x // 32, zb // 32), []) \
                        .append((x, zb, pk))
                    zb = zt - 1
                z = top - 1
        self.tree_pairs = [p for p, _ in pair_counts.most_common(TREE_KEEP)]

        # ---- selection: the resdict caps us at 254 names ------------------ #
        base_set = set(base_art.values())
        navail = MAX_TEX - len(base_set) - len(self.tree_pairs)
        details = [a for a, _ in counts.most_common()
                   if a not in base_set and cls_of[a] != "tree"][:navail]
        kept = list(dict.fromkeys(
            sorted(base_set, key=lambda a: -counts[a]) + details))
        self.name_of = {a: f"g{i:03x}" for i, a in enumerate(kept)}
        self.base_of = {c: self.name_of[a] for c, a in base_art.items()}
        self.base_names = set(self.base_of.values())
        covered = sum(counts[a] for a in kept)
        total = sum(counts.values())
        self.stats = (f"{len(kept)} ground arts "
                      f"({len(base_set)} bases) + {len(self.tree_pairs)} "
                      f"tree pairs; art coverage "
                      f"{100.0 * covered / total:.1f}% of {total} tiles")

        # ---- assemble textures + grouped palettes ------------------------- #
        entries = []       # (name, w, h, texels, fmt3, opaque0)
        imgs = []          # (name, w, h, img)
        for a in kept:
            imgs.append((self.name_of[a], 16, 16,
                         Image.frombytes("RGB", (16, 16), a)))
        self.tree_name = {}
        for i, (ta, tb) in enumerate(self.tree_pairs):
            im = Image.new("RGB", (16, 32))
            im.paste(Image.frombytes("RGB", (16, 16), ta), (0, 0))
            im.paste(Image.frombytes("RGB", (16, 16), tb), (0, 16))
            nm = f"tr{i:02d}"
            self.tree_name[(ta, tb)] = nm
            imgs.append((nm, 16, 32, im))
        self.tree_default = (self.tree_name[self.tree_pairs[0]]
                             if self.tree_pairs else None)

        quant = [(nm, w, h) + _quant16(im) for nm, w, h, im in imgs]
        groups, group_of = [], []
        for nm, w, h, cset, _ in quant:
            cs = set(cset)
            gi = next((j for j, g in enumerate(groups)
                       if len(g | cs) <= 16), None)
            if gi is None:
                gi = len(groups)
                groups.append(set())
            groups[gi] |= cs
            group_of.append(gi)
        gindex, palettes = [], []
        for gi, g in enumerate(groups):
            cl = sorted(g)
            gindex.append({c: k for k, c in enumerate(cl)})
            pb = bytearray(32)
            for k, (r, gg, b) in enumerate(cl):
                pb[k * 2] = (r | (gg << 5)) & 0xFF
                pb[k * 2 + 1] = ((gg >> 3) | (b << 2)) & 0xFF
            palettes.append((f"p{gi:02x}", bytes(pb)))
        self.pal_of, self.dims = {}, {}
        for i, (nm, w, h, cset, px) in enumerate(quant):
            idx = gindex[group_of[i]]
            t = bytearray(w * h // 2)
            for y in range(h):
                for x in range(w):
                    r, gg, b = px[x, y]
                    v = idx[(r >> 3, gg >> 3, b >> 3)]
                    t[(y * w + x) // 2] |= v << (4 * (x & 1))
            entries.append((nm, w, h, bytes(t), 3, True))
            self.pal_of[nm] = f"p{group_of[i]:02x}"
            self.dims[nm] = (w, h)
        self.npals = len(groups)
        self.btx = nsbmd.build_btx_named(entries, palettes)


def _rect_quad(lx, lz, w, h, y=0.0):
    """Ground rect; UV 0..w*16 x 0..h*16 over a repeating 16x16 texture."""
    x0, z0 = lx * 16 - 256, lz * 16 - 256
    x1, z1 = x0 + w * 16, z0 + h * 16
    return [((x0, y, z0), (0, 0)), ((x1, y, z0), (w * 16, 0)),
            ((x1, y, z1), (w * 16, h * 16)), ((x0, y, z1), (0, h * 16))]


def _wall_quad(lx, lz, run, height):
    """Vertical quad on the south edge of tile row lz, `run` tiles wide."""
    x0 = lx * 16 - 256
    x1 = x0 + run * 16
    z = lz * 16 - 256 + 16
    return [((x0, height, z), (0, 0)), ((x1, height, z), (run * 16, 0)),
            ((x1, 0, z), (run * 16, height)), ((x0, 0, z), (0, height))]


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
    """Build one chunk: (shape_dls[39], nverts, tex_names, pal_names,
    tex_dims, repeat_slots). Textures are bound PER CHUNK: the chunk's
    class bases + its most-covering detail arts, demoted as needed to fit
    39 slots and the vertex cap."""
    cls = [[FILL_CLASS] * 32 for _ in range(32)]
    akey = [[None] * 32 for _ in range(32)]
    for lz in range(32):
        for lx in range(32):
            gx, gz = cx * 32 + lx, cy * 32 + lz
            if gx < GW and gz < GH:
                cls[lz][lx] = sem[gz][gx]
                akey[lz][lx] = ts.artgrid[gz][gx]

    # tree walls for this chunk (precomputed globally): dominant kept pair
    segs = ts.tree_segs.get((cx, cy), [])
    tree_nm = None
    if segs:
        pc = Counter(pk for _, _, pk in segs)
        tree_nm = next((ts.tree_name[pk] for pk, _ in pc.most_common()
                        if pk in ts.tree_name), ts.tree_default)

    # wanted texture per cell + per-chunk detail coverage. Reserve the base
    # of EVERY class present (vertex-demotion can introduce a base slot the
    # initial pass never used).
    want = [[None] * 32 for _ in range(32)]
    cover = Counter()
    bases_needed = set()
    for lz in range(32):
        for lx in range(32):
            c = cls[lz][lx]
            a = akey[lz][lx]
            bases_needed.add(ts.base_of[c])
            nm = ts.name_of.get(a) if (a is not None and c != "tree") else None
            if nm is None:
                nm = ts.base_of[c]
            elif nm not in ts.base_names:
                cover[nm] += 1
            want[lz][lx] = nm

    def build(keep):
        tqs = {}
        for lz in range(32):
            by = {}
            for lx in range(32):
                nm = want[lz][lx]
                if nm not in keep and nm not in bases_needed:
                    nm = ts.base_of[cls[lz][lx]]
                by.setdefault(nm, []).append((lx, lz))
            for nm, cells in by.items():
                tqs.setdefault(nm, []).extend(cells)
        quads = {}
        nverts = 0
        for nm, cells in tqs.items():
            qs = [_rect_quad(x, z, w, h) for x, z, w, h in greedy_rects(cells)]
            quads[nm] = qs
            nverts += 4 * len(qs)
        if tree_nm and segs:
            runs = {}
            for gx, zb, _ in segs:
                runs.setdefault(zb, []).append(gx)
            ws = []
            for zb, xs in runs.items():
                xs.sort()
                i = 0
                while i < len(xs):
                    j = i
                    while j + 1 < len(xs) and xs[j + 1] == xs[j] + 1:
                        j += 1
                    ws.append(_wall_quad(xs[i] - cx * 32, zb - cy * 32,
                                         j - i + 1, TREE_WALL_H))
                    i = j + 1
            quads.setdefault(tree_nm, []).extend(ws)
            nverts += 4 * len(ws)
        return quads, nverts

    # slot fit: bases (+tree) always; details by coverage; then vertex cap
    nfixed = len(bases_needed) + (1 if tree_nm else 0)
    details = [nm for nm, _ in cover.most_common()][:max(0, MAX_SLOTS - nfixed)]
    keep = set(details)
    quads, nverts = build(keep)
    while nverts > CHUNK_VERT_CAP and details:
        keep.discard(details.pop())
        quads, nverts = build(keep)

    names = sorted(quads)
    assert len(names) <= MAX_SLOTS, (cx, cy, len(names))
    shape_dls = [nsbmd.quad_dl(quads[nm]) for nm in names]
    while len(names) < MAX_SLOTS:
        names.append(names[0])
        shape_dls.append(nsbmd.quad_dl([]))
    tex_names = names
    pal_names = [ts.pal_of[nm] for nm in names]
    tex_dims = [ts.dims[nm] for nm in names]
    return (shape_dls, nverts, tex_names, pal_names, tex_dims,
            set(range(MAX_SLOTS)))
