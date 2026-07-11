#!/usr/bin/env python3
"""mdlview.py - decode NSBMD building-model geometry for software preview.

Parses a BMD0 (model 0 only): shapes' Nitro display lists -> textured
triangles/quads in model space, material -> texture/palette binding via the
material section's pairing dictionaries, texture decode via
tools/hoennconv/nsbtx.py. Matrix commands are treated as identity (fine for
single-bone static props like bm_field buildings); upScale is applied.

Used by preview_render.py --donor to draw vanilla Gen-4 models in a town.
"""
import os
import struct
import sys

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)
sys.path.insert(0, os.path.join(_here, "..", "hoennconv"))

from nsbtx import Tex0                     # noqa: E402

# display-list parameter counts (words) per opcode
_PARAMS = {
    0x00: 0, 0x10: 1, 0x11: 0, 0x12: 1, 0x13: 1, 0x14: 1, 0x15: 0,
    0x16: 16, 0x17: 12, 0x18: 16, 0x19: 12, 0x1A: 9, 0x1B: 3, 0x1C: 3,
    0x20: 1, 0x21: 1, 0x22: 1, 0x23: 2, 0x24: 1, 0x25: 1, 0x26: 1,
    0x27: 1, 0x28: 1, 0x29: 1, 0x2A: 1, 0x2B: 1, 0x30: 1, 0x31: 1,
    0x32: 1, 0x33: 1, 0x34: 32, 0x40: 1, 0x41: 0,
}


def _s16(v):
    return v - 0x10000 if v & 0x8000 else v


def _s10(v):
    v &= 0x3FF
    return v - 0x400 if v & 0x200 else v


class Model:
    def __init__(self, blob: bytes):
        self.blob = blob
        mdl0 = struct.unpack_from("<I", blob, 0x10)[0]
        nummdl = blob[mdl0 + 9]
        entdata = mdl0 + 8 + 8 + (nummdl + 1) * 4 + 4
        m = mdl0 + struct.unpack_from("<I", blob, entdata)[0]
        self.m = m
        (_, self.ofsSbc, self.ofsMat, self.ofsShp,
         _) = struct.unpack_from("<5I", blob, m)
        self.num_mat = blob[m + 0x18]
        self.num_shp = blob[m + 0x19]
        self.up_scale = struct.unpack_from("<i", blob, m + 0x1C)[0] / 65536.0

        # material -> texture/palette name via the pairing dicts
        mat = m + self.ofsMat
        ofsTexDict, ofsPalDict = struct.unpack_from("<HH", blob, mat)
        self.mat_tex = {}
        self.mat_pal = {}
        for off, out in ((mat + ofsTexDict, self.mat_tex),
                         (mat + ofsPalDict, self.mat_pal)):
            n = blob[off + 1]
            ofs_entry = struct.unpack_from("<H", blob, off + 6)[0]
            ep = off + ofs_entry
            unit, ofs_name = struct.unpack_from("<HH", blob, ep)
            for k in range(n):
                o, num, _b = struct.unpack_from("<HBB", blob, ep + 4 + k * unit)
                name = blob[ep + ofs_name + k * 16: ep + ofs_name + k * 16 + 16]
                name = name.rstrip(b"\0").decode(errors="replace")
                for i in range(num):
                    out[blob[mat + o + i]] = name

        # material bodies (for texImageParam wrap bits)
        n = blob[mat + 4 + 1]
        enthdr = mat + 4 + 8 + (n + 1) * 4
        self.mat_body = [mat + struct.unpack_from("<I", blob, enthdr + 4 + i * 4)[0]
                         for i in range(n)]

        # shapes -> display lists
        shp = m + self.ofsShp
        sn = blob[shp + 1]
        enthdr = shp + 8 + (sn + 1) * 4
        self.dls = []
        for i in range(sn):
            body = shp + struct.unpack_from("<I", blob, enthdr + 4 + i * 4)[0]
            _u0, _u1, _fl, ofs_dl, dl_size = struct.unpack_from("<HHIII", blob, body)
            self.dls.append(bytes(blob[body + ofs_dl: body + ofs_dl + dl_size]))

        # SBC: (material, shape) draw pairs
        self.pairs = []
        p = m + self.ofsSbc
        end = m + self.ofsMat
        cur_mat = 0
        while p < end:
            op = blob[p] & 0x1F
            if op == 0x04:
                cur_mat = blob[p + 1]; p += 2
            elif op == 0x05:
                self.pairs.append((cur_mat, blob[p + 1])); p += 2
            elif op == 0x06:
                p += 4 + (2 if blob[p + 3] & 0x08 else 0) \
                       + (1 if (blob[p] >> 5) & 1 else 0)
            elif op == 0x02:
                p += 3
            elif op == 0x03:
                p += 2
            elif op in (0x00, 0x0B):
                p += 1
            elif op == 0x01:
                break
            else:
                p += 1      # unknown: skip conservatively

        self.tex = Tex0(blob)
        self._teximg = {}

    def texture_image(self, mat_id):
        """RGBA PIL image for a material (None if untextured)."""
        name = self.mat_tex.get(mat_id)
        if name is None:
            return None
        if name not in self._teximg:
            e = next((t for t in self.tex.textures if t.name == name), None)
            self._teximg[name] = self.tex.render(e) if e else None
        return self._teximg[name]

    def tex_name(self, mat_id):
        return self.mat_tex.get(mat_id, "")

    def wrap_flags(self, mat_id):
        """(repeat_s, repeat_t, flip_s, flip_t) from the material's
        texImageParam (body +0x14)."""
        if mat_id >= len(self.mat_body):
            return (True, True, False, False)
        ti = struct.unpack_from("<I", self.blob, self.mat_body[mat_id] + 0x14)[0]
        return (bool(ti & 0x10000), bool(ti & 0x20000),
                bool(ti & 0x40000), bool(ti & 0x80000))

    # ---- geometry -------------------------------------------------------- #
    def faces(self):
        """[(mat_id, [((x,y,z),(s,t)), ...3 or 4 verts])] with upScale applied."""
        out = []
        for mat_id, shp_id in self.pairs:
            out += [(mat_id, f) for f in self._decode(self.dls[shp_id])]
        s = self.up_scale
        if s != 1.0:
            out = [(m, [((x * s, y * s, z * s), uv) for (x, y, z), uv in f])
                   for m, f in out]
        return out

    def _decode(self, dl):
        faces = []
        pos = (0.0, 0.0, 0.0)
        uv = (0.0, 0.0)
        mode = None
        verts = []

        def flush_vertex():
            verts.append((pos, uv))

        i = 0
        n = len(dl)
        while i + 4 <= n:
            ops = dl[i:i + 4]
            i += 4
            for op in ops:
                cnt = _PARAMS.get(op)
                if cnt is None:
                    return faces
                params = [struct.unpack_from("<I", dl, i + 4 * k)[0]
                          for k in range(cnt)] if i + 4 * cnt <= n else []
                i += 4 * cnt
                if op == 0x40:
                    mode = params[0] & 3
                    verts = []
                elif op == 0x41:
                    mode = None
                elif op == 0x22:
                    uv = (_s16(params[0] & 0xFFFF) / 16.0,
                          _s16(params[0] >> 16) / 16.0)
                elif op == 0x23:
                    x = _s16(params[0] & 0xFFFF) / 4096.0
                    y = _s16(params[0] >> 16) / 4096.0
                    z = _s16(params[1] & 0xFFFF) / 4096.0
                    pos = (x, y, z); flush_vertex()
                elif op == 0x24:
                    x = _s10(params[0]) / 64.0
                    y = _s10(params[0] >> 10) / 64.0
                    z = _s10(params[0] >> 20) / 64.0
                    pos = (x, y, z); flush_vertex()
                elif op == 0x25:
                    pos = (_s16(params[0] & 0xFFFF) / 4096.0,
                           _s16(params[0] >> 16) / 4096.0, pos[2]); flush_vertex()
                elif op == 0x26:
                    pos = (_s16(params[0] & 0xFFFF) / 4096.0, pos[1],
                           _s16(params[0] >> 16) / 4096.0); flush_vertex()
                elif op == 0x27:
                    pos = (pos[0], _s16(params[0] & 0xFFFF) / 4096.0,
                           _s16(params[0] >> 16) / 4096.0); flush_vertex()
                elif op == 0x28:
                    dx = _s10(params[0]) / 32768.0
                    dy = _s10(params[0] >> 10) / 32768.0
                    dz = _s10(params[0] >> 20) / 32768.0
                    pos = (pos[0] + dx, pos[1] + dy, pos[2] + dz); flush_vertex()

                # primitive assembly
                if mode is not None and verts:
                    if mode == 0 and len(verts) == 3:        # tris
                        faces.append(list(verts)); verts = []
                    elif mode == 1 and len(verts) == 4:      # quads
                        faces.append(list(verts)); verts = []
                    elif mode == 2 and len(verts) >= 3:      # tri strip
                        if len(verts) > 3:
                            a, b, c = verts[-3], verts[-2], verts[-1]
                            faces.append([a, b, c] if len(verts) % 2 else [b, a, c])
                        else:
                            faces.append(list(verts))
                    elif mode == 3 and len(verts) >= 4 and len(verts) % 2 == 0:
                        a, b, d, c = verts[-4], verts[-3], verts[-2], verts[-1]
                        faces.append([a, b, c, d])
        return faces


def load(path_or_blob) -> Model:
    if isinstance(path_or_blob, (bytes, bytearray)):
        return Model(bytes(path_or_blob))
    return Model(open(path_or_blob, "rb").read())
