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
"""
import os
import struct

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
TEMPLATE_PATH = os.path.join(
    ROOT, "disasm/pokeplatinum/res/field/maps/data/map_data_191.bin")

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
        # material body offsets (relative to mat block)
        n = b[mat + 4 + 1]
        assert n == NUM_TEX
        enthdr = mat + 4 + 8 + (n + 1) * 4
        self.mat_offsets = [mat + struct.unpack_from("<I", b, enthdr + 4 + i * 4)[0]
                            for i in range(n)]
        # shape section: dict + 8 headers, then DLs
        shp = self.m + self.ofsShp
        sn = b[shp + 1]
        assert sn == NUM_TEX
        dsize = struct.unpack_from("<H", b, shp + 2)[0]
        self.shp_dict_size = dsize
        enthdr2 = shp + 8 + (sn + 1) * 4
        self.shp_body_offsets = [struct.unpack_from("<I", b, enthdr2 + 4 + i * 4)[0]
                                 for i in range(sn)]
        # prefix: everything up to end of last shape header
        self.shape_hdrs_end = shp + max(self.shp_body_offsets) + 16
        self.prefix = bytes(b[:self.shape_hdrs_end])

    def _tree(self, off):
        n = self.bmd[off + 1]
        return bytes(self.bmd[off + 8:off + 8 + (n + 1) * 4])


_template = None


def template():
    global _template
    if _template is None:
        _template = Template()
    return _template


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


def build_model(shape_dls, tex_dims):
    """shape_dls: 8 display-list byte blobs (shape k drawn with texture k).
    tex_dims: 8 (w,h) texture dimensions for material origW/origH.
    Returns a complete BMD0."""
    t = template()
    b = bytearray(t.prefix)
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
    struct.pack_into("<2I", b, t.m + 0x38, 0x80000, 0x2000)  # boxPosScale 128
    # material origW/origH + force double-sided (winding-order insurance)
    for k, (w, h) in enumerate(tex_dims):
        struct.pack_into("<2H", b, t.mat_offsets[k] + 32, w, h)
        pa = struct.unpack_from("<I", b, t.mat_offsets[k] + 0x0C)[0]
        struct.pack_into("<I", b, t.mat_offsets[k] + 0x0C, pa | 0xC0)
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
