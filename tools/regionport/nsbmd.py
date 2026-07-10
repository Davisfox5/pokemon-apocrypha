#!/usr/bin/env python3
"""nsbmd.py - generate HGSS-compatible map-chunk NSBMD models and NSBTX
texture sets by surgically reusing a real Platinum chunk as template.

Why a template: NNS name dictionaries embed patricia-tree bytes derived from
the entry names. Rather than reimplement the tree builder, we reuse the
8-texture template map_data_191 ('pc_room1'..'pc_room8') verbatim: its names,
tree bytes, materials, node and SBC. Only the shape display lists (geometry),
material texture dims, vertex counts, bbox and sizes are rewritten.

Model contract (fixed by the template):
  8 materials/shapes; texture k binds material k, shape k draws with it.
  Textures 'pc_room1'..'pc_room7': 16x16 repeating tiles (expanse layers).
  Texture 'pc_room8': the metatile atlas (detail quads).
  Vertices are fx16 4.12 in model units; the engine scales by posScale=64,
  so world = value*64/4096. One tile = 16 world units; chunks span +-256.

Name patching: NNS_G3dBindMdlTex iterates the MODEL's texture/palette name
dicts linearly (only the NSBTX-side dict is tree-walked), so the 16-byte name
slots in the template's material section can be patched per chunk without
rebuilding the model-side patricia tree. The NSBTX-side tree IS walked, so
build_btx_named() builds a real one (build_tree, verified against all 148
Platinum tileset dicts).
"""
import os
import struct

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
# Template must be an OUTDOOR chunk: indoor models (e.g. map_data_191) carry
# posScale=32 and other conventions that break the field renderer — outdoor
# chunks use posScale=64, which fx() below assumes. It must also have
# EIGHT palette-dict entries binding one material each: the earlier template
# (map_data_147) had only 7 — materials 3+4 shared one entry, so patching 8
# distinct palette names positionally shifted every binding after slot 3 and
# silently dropped the last name (washed-out Hoenn, v5 regression). 415 is a
# beach chunk with 8 materials/shapes/textures/palettes, one material per
# dict entry (permutation handled by tex_slot_of/pal_slot_of below).
TEMPLATE_PATH = os.path.join(
    ROOT, "disasm/pokeplatinum/res/field/maps/data/map_data_415.bin")
# Ground chunks use the largest clean outdoor model instead: 39 mats/shapes/
# textures/palettes, same SBC shell, posScale 64 — lifts the 8-texture-per-
# chunk ceiling for the Gen-4 re-skin (towns bind 15-25 terrain textures).
CHUNK_TEMPLATE_PATH = os.path.join(
    ROOT, "disasm/pokeplatinum/res/field/maps/data/map_data_242.bin")

NUM_TEX = 8
TEX_NAMES = [f"pc_room{i+1}" for i in range(NUM_TEX)]
PAL_NAMES = [f"pc_room{i+1}_pl" for i in range(NUM_TEX)]

# geometry command opcodes
G_NOP, G_TEXCOORD, G_NORMAL, G_VTX_16 = 0x00, 0x22, 0x21, 0x23
G_BEGIN, G_END = 0x40, 0x41
NORMAL_UP = 0x0007FC00  # +Y packed 10-bit, same as vanilla flat ground


class Template:
    def __init__(self, path=TEMPLATE_PATH):
        with open(path, "rb") as f:
            raw = f.read()
        p, pr, mo, bd = struct.unpack_from("<4I", raw, 0)
        self.bmd = bytearray(raw[16 + p + pr:16 + p + pr + mo])
        b = self.bmd
        assert b[:4] == b"BMD0"
        self.mdl0 = struct.unpack_from("<I", b, 0x10)[0]
        nummdl = b[self.mdl0 + 9]
        entdata = self.mdl0 + 8 + 8 + (nummdl + 1) * 4 + 4
        self.m = self.mdl0 + struct.unpack_from("<I", b, entdata)[0]
        (self.msize, self.ofsSbc, self.ofsMat, self.ofsShp,
         self.ofsEvp) = struct.unpack_from("<5I", b, self.m)
        mat = self.m + self.ofsMat
        ofsTexDict, ofsPalDict = struct.unpack_from("<HH", b, mat)
        self.tex_tree = self._tree(mat + ofsTexDict)
        self.pal_tree = self._tree(mat + ofsPalDict)
        self.tex_name_offs = self._dict_name_offsets(mat + ofsTexDict)
        self.pal_name_offs = self._dict_name_offsets(mat + ofsPalDict)
        # dict slot -> bound material (texToMatList/palToMatList). Each slot
        # must bind exactly ONE material or per-material palette patching is
        # ambiguous; build_model writes names via the inverse permutation.
        def slot_mats(off):
            n = b[off + 1]
            ofs_entry = struct.unpack_from("<H", b, off + 6)[0]
            ep = off + ofs_entry
            unit = struct.unpack_from("<H", b, ep)[0]
            out = []
            for k in range(n):
                o, num, _bound = struct.unpack_from("<HBB", b, ep + 4 + k * unit)
                out.append(tuple(b[mat + o + i] for i in range(num)))
            return out
        tex_slots = slot_mats(mat + ofsTexDict)
        pal_slots = slot_mats(mat + ofsPalDict)
        assert all(len(s) == 1 for s in tex_slots), tex_slots
        assert all(len(s) == 1 for s in pal_slots), (
            "template palette dict must bind one material per entry", pal_slots)
        self.tex_slot_of = {s[0]: k for k, s in enumerate(tex_slots)}  # mat -> slot
        self.pal_slot_of = {s[0]: k for k, s in enumerate(pal_slots)}
        # material body offsets (relative to mat block)
        n = b[mat + 4 + 1]
        assert n == len(self.tex_name_offs) == len(self.pal_name_offs), (
            "template must have equal material/texture/palette counts", n)
        self.num = n
        enthdr = mat + 4 + 8 + (n + 1) * 4
        self.mat_offsets = [mat + struct.unpack_from("<I", b, enthdr + 4 + i * 4)[0]
                            for i in range(n)]
        # shape section: dict + n headers, then DLs
        shp = self.m + self.ofsShp
        sn = b[shp + 1]
        assert sn == n
        dsize = struct.unpack_from("<H", b, shp + 2)[0]
        self.shp_dict_size = dsize
        enthdr2 = shp + 8 + (sn + 1) * 4
        self.shp_body_offsets = [struct.unpack_from("<I", b, enthdr2 + 4 + i * 4)[0]
                                 for i in range(sn)]
        # Normalize to the proven render config regardless of template:
        # SBC identity MAT k -> SHP k pairing (147's artist-scrambled pairs
        # would draw shape DLs with the wrong materials), and vanilla OUTDOOR
        # materials — light0 enable + fog + white ambient + vertex-color
        # diffuse (map_data_147's own values). The light-enable bit is what
        # lets the arealight day/night system tint the map: the outdoor
        # loader strips material colors (NNS_G3dMdlUseGlb*) and drives
        # vertex color per-normal through the global light/ambient/emission,
        # so unlit materials render ~half-bright at noon and never tint.
        # Only deviation from vanilla: draw both faces (|0x40) so quad
        # winding can't blank tiles.
        sbc = self.m + self.ofsSbc
        shell = bytes((0x26, 0, 0, 0, 0, 0x02, 0, 0x01, 0x0B))
        assert bytes(b[sbc:sbc + 9]) == shell, b[sbc:sbc + 9].hex()
        for k in range(n):
            b[sbc + 9 + k * 4:sbc + 9 + k * 4 + 4] = bytes((0x04, k, 0x05, k))
        assert b[sbc + 9 + n * 4] == 0x2B
        for off in self.mat_offsets:
            struct.pack_into("<3I", b, off + 4, 0x7FFFE739, 0, 0x001F80C1)
        # prefix: everything up to end of last shape header
        self.shape_hdrs_end = shp + max(self.shp_body_offsets) + 16
        self.prefix = bytes(b[:self.shape_hdrs_end])

    def _tree(self, off):
        n = self.bmd[off + 1]
        return bytes(self.bmd[off + 8:off + 8 + (n + 1) * 4])

    def _dict_name_offsets(self, off):
        """Absolute offsets (within self.bmd/prefix) of the n 16-byte name slots."""
        n = self.bmd[off + 1]
        ofs_entry = struct.unpack_from("<H", self.bmd, off + 6)[0]
        ep = off + ofs_entry
        unit, ofs_name = struct.unpack_from("<HH", self.bmd, ep)
        return [ep + ofs_name + i * 16 for i in range(n)]


_templates = {}


def template(path=TEMPLATE_PATH):
    if path not in _templates:
        _templates[path] = Template(path)
    return _templates[path]


def pack_dl(cmds):
    """cmds: list of (opcode, [u32 params]). Returns packed display list."""
    out = bytearray()
    for i in range(0, len(cmds), 4):
        group = list(cmds[i:i + 4])
        while len(group) < 4:
            group.append((G_NOP, []))
        out += bytes(op for op, _ in group)
        for _, params in group:
            for pv in params:
                out += struct.pack("<I", pv & 0xFFFFFFFF)
    while len(out) % 4:
        out.append(0)
    return bytes(out)


def fx(v):
    """world units -> fx16 4.12 model units (posScale 64)."""
    r = int(round(v * 4096 / 64)) & 0xFFFF
    return r


def quad_dl(quads):
    """quads: list of 4-vertex tuples [((wx,wy,wz),(s,t)), ...] with s,t in
    texels. Returns a display list drawing them (normal up, quads)."""
    if not quads:
        return pack_dl([(G_BEGIN, [1]), (G_END, [])])
    cmds = [(G_BEGIN, [1]), (G_NORMAL, [NORMAL_UP])]
    for q in quads:
        for (wx, wy, wz), (s, t) in q:
            st = (int(round(s * 16)) & 0xFFFF) | ((int(round(t * 16)) & 0xFFFF) << 16)
            cmds.append((G_TEXCOORD, [st]))
            cmds.append((G_VTX_16, [fx(wx) | (fx(wy) << 16), fx(wz)]))
    cmds.append((G_END, []))
    return pack_dl(cmds)


def build_model(shape_dls, tex_dims, tex_names=None, pal_names=None,
                wrap_repeat_slots=7, tmpl=None):
    """shape_dls: t.num display-list byte blobs (shape k drawn with texture k).
    tex_dims: t.num (w,h) texture dimensions for material origW/origH.
    tex_names/pal_names: optional t.num names to patch into the material dicts
    (binding iterates these linearly; the stale model-side tree is unused).
    wrap_repeat_slots: first N materials get repeat wrap, the rest clamp.
    wrap_repeat_slots may also be a set of material indices to repeat.
    tmpl: Template to surger (default 8-slot prop template; ground chunks
    pass template(CHUNK_TEMPLATE_PATH) = 39 slots).
    Returns a complete BMD0."""
    t = tmpl or template()
    assert len(shape_dls) == t.num and len(tex_dims) == t.num, (
        len(shape_dls), len(tex_dims), t.num)
    b = bytearray(t.prefix)
    # names are given PER MATERIAL k; write each into the dict slot that
    # actually binds material k (dict order is an arbitrary permutation)
    if tex_names is not None:
        for k, nm in enumerate(tex_names):
            off = t.tex_name_offs[t.tex_slot_of[k]]
            b[off:off + 16] = nm.encode().ljust(16, b"\0")
    if pal_names is not None:
        for k, nm in enumerate(pal_names):
            off = t.pal_name_offs[t.pal_slot_of[k]]
            b[off:off + 16] = nm.encode().ljust(16, b"\0")
    # append DLs after the shape headers; patch each shape header
    shp = t.m + t.ofsShp
    cursor = t.shape_hdrs_end - shp  # relative to shape section
    nverts = nquads = 0
    for k, dl in enumerate(shape_dls):
        body = shp + t.shp_body_offsets[k]
        ofs_dl = (shp + cursor) - body
        struct.pack_into("<HHIII", b, body, 0, 16, 0x5, ofs_dl, len(dl))
        b += dl
        cursor += len(dl)
        nquads += max(0, (len(dl) // 4 - 4) // 13)  # approx; fixed below
    # exact counts recomputed by caller are optional; count via DL parse:
    nquads = 0
    for dl in shape_dls:
        # each quad contributes 4 TEXCOORD+VTX pairs = 12 params + 8 cmds; count VTX_16 cmds
        i = 0
        nv = 0
        data = dl
        while i < len(data):
            ops = data[i:i + 4]
            i += 4
            for op in ops:
                if op == G_TEXCOORD:
                    i += 4
                elif op == G_NORMAL:
                    i += 4
                elif op == G_VTX_16:
                    i += 8
                    nv += 1
                elif op == G_BEGIN:
                    i += 4
        nverts += nv
        nquads += nv // 4
    model_size = (t.ofsShp + (t.shape_hdrs_end - shp)) + sum(len(d) for d in shape_dls)
    # pad model to 4
    while (len(b) - t.m) % 4:
        b.append(0)
    model_size = len(b) - t.m
    struct.pack_into("<I", b, t.m, model_size)          # model.size
    struct.pack_into("<I", b, t.m + 0x10, model_size)   # ofsEvpMtx (none)
    # info: numVertex/&c at m+0x24, bbox at m+0x2c
    struct.pack_into("<4H", b, t.m + 0x24, min(nverts, 0xFFFF), min(nquads, 0xFFFF), 0, min(nquads, 0xFFFF))
    struct.pack_into("<6H", b, t.m + 0x2C,
                     0xE000, 0xF800, 0xE000,   # box xyz: -2.0, -0.5, -2.0
                     0x4000, 0x1000, 0x4000)   # box whd:  4.0,  1.0,  4.0
    # boxPosScale 128 and its fx32 INVERSE 1/128 (0x20). Getting the inverse
    # wrong (e.g. 0x2000 = 0.5) breaks the renderer's per-chunk box test:
    # every chunk except the one the camera is inside gets frustum-culled.
    struct.pack_into("<2I", b, t.m + 0x38, 0x80000, 0x20)
    # material origW/origH (+0x20) and texImageParam (+0x14) wrap bits:
    # repeat without flip for the 7 tile slots, clamp for the atlas so any
    # epsilon overshoot samples the cell edge instead of a foreign cell
    for k, (w, h) in enumerate(tex_dims):
        struct.pack_into("<2H", b, t.mat_offsets[k] + 0x20, w, h)
        ti = struct.unpack_from("<I", b, t.mat_offsets[k] + 0x14)[0]
        rep = (k in wrap_repeat_slots) if isinstance(wrap_repeat_slots, (set, frozenset)) \
            else k < wrap_repeat_slots
        ti = (ti & ~0x000F0000) | (0x00030000 if rep else 0)
        struct.pack_into("<I", b, t.mat_offsets[k] + 0x14, ti)
    mdl0_size = len(b) - t.mdl0
    struct.pack_into("<I", b, t.mdl0 + 4, mdl0_size)
    struct.pack_into("<I", b, 0x08, len(b))             # BMD0 filesize
    return bytes(b)


def _log2(v):
    n = 0
    while (8 << n) < v:
        n += 1
    assert (8 << n) == v, v
    return n


def build_btx(textures, palette):
    """textures: 8 (w, h, texel_bytes 8bpp index data). palette: 512 bytes
    (256 x BGR555). All 8 palette names point at the same palette."""
    t = template()
    texdata = bytearray()
    tex_entries = []
    for w, h, texels in textures:
        assert len(texels) == w * h
        while len(texdata) % 8:
            texdata.append(0)
        ofs = len(texdata)
        texdata += texels
        w0 = ((ofs >> 3) & 0xFFFF) | (_log2(w) << 20) | (_log2(h) << 23) | (4 << 26)
        w1 = w | (h << 11) | 0x80000000
        tex_entries.append((w0, w1))
    while len(texdata) % 8:
        texdata.append(0)
    paldata = bytes(palette)
    assert len(paldata) == 512

    def mkdict(tree, entries, unit, names):
        n = len(names)
        size = 8 + len(tree) + 4 + n * unit + n * 16
        # header: rev, numEntries, sizeOfDict, dummy(8), ofsEntryHeader
        d = bytearray()
        d += struct.pack("<BBH", 0, n, size)
        d += struct.pack("<HH", 8, 8 + len(tree))
        d += tree
        d += struct.pack("<HH", unit, 4 + n * unit)
        for e in entries:
            if unit == 8:
                d += struct.pack("<2I", *e)
            else:
                d += struct.pack("<HH", *e)
        for nm in names:
            d += nm.encode().ljust(16, b"\0")
        return bytes(d)

    texdict = mkdict(t.tex_tree, tex_entries, 8, TEX_NAMES)
    paldict = mkdict(t.pal_tree, [(0, 0)] * NUM_TEX, 4, PAL_NAMES)

    HDR = 0x3C
    ofs_texdict = HDR
    ofs_paldict = ofs_texdict + len(texdict)
    ofs_texdata = ofs_paldict + len(paldict)
    ofs_paldata = ofs_texdata + len(texdata)
    total = ofs_paldata + len(paldata)
    tex0 = bytearray()
    tex0 += b"TEX0" + struct.pack("<I", total)
    tex0 += struct.pack("<I", 0)
    tex0 += struct.pack("<HH", len(texdata) >> 3, ofs_texdict)
    tex0 += struct.pack("<I", 0)
    tex0 += struct.pack("<I", ofs_texdata)
    tex0 += struct.pack("<I", 0)
    tex0 += struct.pack("<HH", 0, ofs_texdict)
    tex0 += struct.pack("<I", 0)
    tex0 += struct.pack("<I", ofs_paldata)
    tex0 += struct.pack("<I", ofs_paldata)
    tex0 += struct.pack("<I", 0)
    tex0 += struct.pack("<I", (len(paldata) >> 3) | 0x80000000)
    tex0 += struct.pack("<I", ofs_paldict)
    tex0 += struct.pack("<I", ofs_paldata)
    assert len(tex0) == HDR, len(tex0)
    tex0 += texdict + paldict + texdata + paldata
    out = bytearray()
    out += b"BTX0" + struct.pack("<HHIHH", 0xFEFF, 0x0001, 0x10 + len(tex0), 0x10, 1)
    out += struct.pack("<I", 0x14)
    out += tex0
    struct.pack_into("<I", out, 0x08, len(out))
    return bytes(out)


# ---- NNS resdict patricia tree (for NSBTX-side dicts, which ARE tree-walked) --
def _getbit(name, i):
    return (name[i >> 3] >> (i & 7)) & 1


def build_tree(names):
    """NNS G3D resdict patricia nodes for 16-byte names; node 0 = head = entry 0.
    Verified semantically against every dict in Platinum's 148 tileset files."""
    assert 1 <= len(names) <= 255
    names = [nm.encode().ljust(16, b"\0") if isinstance(nm, str) else bytes(nm).ljust(16, b"\0")
             for nm in names]
    assert len(set(names)) == len(names), "duplicate names"
    nodes = [[127, 0, 0, 0]]

    def search(x):
        prev_ref, cur = 128, 0
        while nodes[cur][0] < prev_ref:
            prev_ref = nodes[cur][0]
            cur = nodes[cur][2] if _getbit(x, nodes[cur][0]) else nodes[cur][1]
        return cur

    for ei in range(1, len(names)):
        x = names[ei]
        y = names[nodes[search(x)][3]]
        i = max(b for b in range(128) if _getbit(x, b) != _getbit(y, b))
        prev, cur, side = 0, 0, 1
        first = True
        while True:
            ref = nodes[cur][0]
            if (not first and ref >= nodes[prev][0]) or ref <= i:
                break
            first = False
            prev = cur
            side = 2 if _getbit(x, ref) else 1
            cur = nodes[cur][side]
        nn = len(nodes)
        node = [i, 0, 0, ei]
        if _getbit(x, i):
            node[2] = nn
            node[1] = cur
        else:
            node[1] = nn
            node[2] = cur
        nodes.append(node)
        nodes[prev][side] = nn
    # self-check: every name resolves through the same walk the engine does
    for ei, nm in enumerate(names):
        prev_ref, cur = 128, 0
        while nodes[cur][0] < prev_ref:
            prev_ref = nodes[cur][0]
            cur = nodes[cur][2] if _getbit(nm, nodes[cur][0]) else nodes[cur][1]
        assert nodes[cur][3] == ei, (ei, nm)
    tree = bytearray()
    for ref, l, r, idx in nodes:
        tree += bytes((ref, l, r, idx))
    while len(tree) < (len(names) + 1) * 4:   # convention: (n+1) node slots
        tree += bytes((127, 0, 0, 0))
    return bytes(tree)


def _mkdict(tree, entries, unit, names):
    n = len(names)
    size = 8 + len(tree) + 4 + n * unit + n * 16
    d = bytearray()
    d += struct.pack("<BBH", 0, n, size)
    d += struct.pack("<HH", 8, 8 + len(tree))
    d += tree
    d += struct.pack("<HH", unit, 4 + n * unit)
    for e in entries:
        if unit == 8:
            d += struct.pack("<2I", *e)
        else:
            d += struct.pack("<HH", *e)
    for nm in names:
        d += nm.encode().ljust(16, b"\0")
    return bytes(d)


_TEXEL_BYTES = {1: 1.0, 2: 0.25, 3: 0.5, 4: 1.0, 6: 1.0}  # per pixel


def build_btx_named(textures, palettes, pal_of=None):
    """Generalized NSBTX. textures: [(name, w, h, texels)] for 8bpp pltt256,
    or [(name, w, h, texels, fmt)] with fmt in {1 a3i5, 2 pltt4, 3 pltt16,
    4 pltt256, 6 a5i3}. fmt 3 draws color 0 transparent unless a 6th element
    is True (opaque ground tiles); for fmt 2/4 an EXPLICIT 6th element False
    requests color-0 transparency (donor cutouts), absent = opaque as before.
    palettes: [(name, BGR555 bytes)], any multiple of 8 bytes up to 512.
    All texture dims must be 8<<k. pal_of unused — palette selection happens
    at bind time by the model's palette names."""
    texdata = bytearray()
    tex_entries, tex_names = [], []
    for entry in textures:
        name, w, h, texels = entry[:4]
        fmt = entry[4] if len(entry) > 4 else 4
        opaque0 = entry[5] if len(entry) > 5 else False
        expected = int(w * h * _TEXEL_BYTES[fmt])
        assert len(texels) == expected, (name, w, h, fmt, len(texels))
        while len(texdata) % 8:
            texdata.append(0)
        ofs = len(texdata)
        texdata += texels
        w0 = ((ofs >> 3) & 0xFFFF) | (_log2(w) << 20) | (_log2(h) << 23) | (fmt << 26)
        if fmt == 3 and not opaque0:
            w0 |= 1 << 29   # color 0 transparent
        if fmt in (2, 4) and len(entry) > 5 and entry[5] is False:
            w0 |= 1 << 29
        w1 = w | (h << 11) | 0x80000000
        tex_entries.append((w0, w1))
        tex_names.append(name)
    while len(texdata) % 8:
        texdata.append(0)
    paldata = bytearray()
    pal_entries, pal_names = [], []
    for name, pal in palettes:
        assert len(pal) % 8 == 0 and 8 <= len(pal) <= 512, (name, len(pal))
        while len(paldata) % 8:
            paldata += b"\0"
        pal_entries.append((len(paldata) >> 3, 0))
        pal_names.append(name)
        paldata += pal
    paldata = bytes(paldata)

    texdict = _mkdict(build_tree(tex_names), tex_entries, 8, tex_names)
    paldict = _mkdict(build_tree(pal_names), pal_entries, 4, pal_names)

    HDR = 0x3C
    ofs_texdict = HDR
    ofs_paldict = ofs_texdict + len(texdict)
    ofs_texdata = ofs_paldict + len(paldict)
    ofs_paldata = ofs_texdata + len(texdata)
    total = ofs_paldata + len(paldata)
    tex0 = bytearray()
    tex0 += b"TEX0" + struct.pack("<I", total)
    tex0 += struct.pack("<I", 0)
    tex0 += struct.pack("<HH", len(texdata) >> 3, ofs_texdict)
    tex0 += struct.pack("<I", 0)
    tex0 += struct.pack("<I", ofs_texdata)
    tex0 += struct.pack("<I", 0)
    tex0 += struct.pack("<HH", 0, ofs_texdict)
    tex0 += struct.pack("<I", 0)
    tex0 += struct.pack("<I", ofs_paldata)
    tex0 += struct.pack("<I", ofs_paldata)
    tex0 += struct.pack("<I", 0)
    tex0 += struct.pack("<I", (len(paldata) >> 3) | 0x80000000)
    tex0 += struct.pack("<I", ofs_paldict)
    tex0 += struct.pack("<I", ofs_paldata)
    assert len(tex0) == HDR, len(tex0)
    tex0 += texdict + paldict + texdata + paldata
    out = bytearray()
    out += b"BTX0" + struct.pack("<HHIHH", 0xFEFF, 0x0001, 0x10 + len(tex0), 0x10, 1)
    out += struct.pack("<I", 0x14)
    out += tex0
    struct.pack_into("<I", out, 0x08, len(out))
    return bytes(out)
