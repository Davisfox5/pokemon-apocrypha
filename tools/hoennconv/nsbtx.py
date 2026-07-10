#!/usr/bin/env python3
"""Read/edit the TEX0 (texture) block inside an NSBMD building model.

Scope: what the Hoenn retexture pass needs — enumerate textures/palettes,
decode them to RGBA for inspection, and mutate palette colors / texel bytes
*in place* (sizes never change, so the rest of the model is untouched).

Layout per apicula's nitro/tex.rs (offsets within the TEX0 block):
  0x00 "TEX0"        0x04 u32 section size
  0x0C u16 texDataLen>>3   0x0E u16 texInfoOff
  0x14 u32 texDataOff
  0x1C u16 cmpDataLen>>3   0x1E u16 cmpInfoOff
  0x24 u32 cmpDataOff      0x28 u32 cmpPalIdxOff
  0x30 u16 palDataLen>>3
  0x34 u32 palInfoOff      0x38 u32 palDataOff

3D-info dictionary (used for both textures and palettes):
  u8 dummy, u8 count, u16 size
  unknown block: u16 subSize, u16 const, count*u32
  data block:    u16 elemSize, u16 dataSize, count*elemSize bytes
  names:         count * 16 ASCII bytes

Texture data-block element (8 bytes): u32 params, u32 extra
  params bits: 0-15 dataOff>>3, 20-22 width=8<<n, 23-25 height=8<<n,
               26-28 format, 29 color0-transparent
Palette data-block element (4 bytes): u16 dataOff>>3, u16 flag

Texture formats: 1=A3I5, 2=pal4, 3=pal16, 4=pal256, 5=4x4-compressed,
6=A5I3, 7=direct16. Buildings use pal4/pal16/pal256.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Entry:
    name: str
    # textures
    params: int = 0
    fmt: int = 0
    width: int = 0
    height: int = 0
    color0: bool = False
    data_off: int = 0        # absolute offset of texel/palette data in blob
    # palettes
    pal_off: int = 0
    pal_ncolors: int = 0     # actual colors stored (span to next palette)


class Tex0:
    def __init__(self, blob: bytes):
        """blob = whole NSBMD file; finds and indexes its TEX0 block."""
        self.blob = bytearray(blob)
        self.base = blob.find(b"TEX0")
        if self.base < 0:
            raise ValueError("no TEX0 block (textures not embedded)")
        b = self.base
        (self.tex_len,) = struct.unpack_from("<H", blob, b + 0x0C)
        (self.tex_info_off,) = struct.unpack_from("<H", blob, b + 0x0E)
        (self.tex_data_off,) = struct.unpack_from("<I", blob, b + 0x14)
        (self.pal_len,) = struct.unpack_from("<H", blob, b + 0x30)
        (self.pal_info_off,) = struct.unpack_from("<I", blob, b + 0x34)
        (self.pal_data_off,) = struct.unpack_from("<I", blob, b + 0x38)
        self.textures = self._dict(b + self.tex_info_off, tex=True)
        self.palettes = self._dict(b + self.pal_info_off, tex=False)

    def _dict(self, off: int, tex: bool) -> list[Entry]:
        blob = self.blob
        count = blob[off + 1]
        # skip the "unknown block": 8-byte header (u16 subSize, u16 secSize,
        # u32 0x17F constant) + count u32 entries (verified by hexdump of
        # wk_hhouse: data block lands exactly at +4+8+4*count)
        p = off + 4 + 8 + 4 * count
        elem_size, data_size = struct.unpack_from("<HH", blob, p)
        p += 4
        entries = []
        data_start = p
        names_start = p + count * elem_size
        for i in range(count):
            e = Entry(name=bytes(
                blob[names_start + i * 16: names_start + i * 16 + 16]
            ).rstrip(b"\0").decode(errors="replace"))
            q = data_start + i * elem_size
            if tex:
                e.params, _ = struct.unpack_from("<II", blob, q)
                e.data_off = (self.base + self.tex_data_off
                              + ((e.params & 0xFFFF) << 3))
                e.width = 8 << ((e.params >> 20) & 7)
                e.height = 8 << ((e.params >> 23) & 7)
                e.fmt = (e.params >> 26) & 7
                e.color0 = bool(e.params & (1 << 29))
            else:
                off3, _ = struct.unpack_from("<HH", blob, q)
                e.pal_off = self.base + self.pal_data_off + (off3 << 3)
            entries.append(e)
        if not tex:
            # a palette's storage runs to the next palette (or block end);
            # formats may store fewer colors than their nominal maximum
            end = self.base + self.pal_data_off + (self.pal_len << 3)
            for e in entries:
                nxt = min([p.pal_off for p in entries if p.pal_off > e.pal_off]
                          or [end])
                e.pal_ncolors = (nxt - e.pal_off) // 2
        return entries

    # ---- palettes ------------------------------------------------------ #
    def palette_colors(self, pal: Entry, n: int) -> list[tuple[int, int, int]]:
        out = []
        for i in range(n):
            (v,) = struct.unpack_from("<H", self.blob, pal.pal_off + i * 2)
            out.append(((v & 31) * 255 // 31,
                        ((v >> 5) & 31) * 255 // 31,
                        ((v >> 10) & 31) * 255 // 31))
        return out

    def set_palette_colors(self, pal: Entry,
                           colors: list[tuple[int, int, int]]) -> None:
        for i, (r, g, b) in enumerate(colors):
            v = (r * 31 // 255) | ((g * 31 // 255) << 5) | ((b * 31 // 255) << 10)
            struct.pack_into("<H", self.blob, pal.pal_off + i * 2, v)

    def _pal_size(self, fmt: int) -> int:
        return {1: 32, 2: 4, 3: 16, 4: 256, 6: 32}.get(fmt, 0)

    def pal_for(self, tex: Entry) -> Entry | None:
        """Palette whose name matches the texture (vanilla convention:
        same name, or texture name + '_pl')."""
        for p in self.palettes:
            if p.name in (tex.name, tex.name + "_pl"):
                return p
        return self.palettes[0] if self.palettes else None

    # ---- texels -------------------------------------------------------- #
    def texel_indices(self, tex: Entry) -> list[int]:
        """Per-pixel palette indices (formats 2/3/4) or raw values."""
        blob, n = self.blob, tex.width * tex.height
        o = tex.data_off
        if tex.fmt == 2:      # 2bpp
            return [(blob[o + i // 4] >> ((i % 4) * 2)) & 3 for i in range(n)]
        if tex.fmt == 3:      # 4bpp
            return [(blob[o + i // 2] >> ((i % 2) * 4)) & 15 for i in range(n)]
        if tex.fmt == 4:      # 8bpp
            return [blob[o + i] for i in range(n)]
        if tex.fmt == 1:      # A3I5
            return [blob[o + i] & 31 for i in range(n)]
        if tex.fmt == 6:      # A5I3
            return [blob[o + i] & 7 for i in range(n)]
        raise ValueError(f"format {tex.fmt} not index-based")

    def set_texel_indices(self, tex: Entry, idx: list[int]) -> None:
        blob, n = self.blob, tex.width * tex.height
        o = tex.data_off
        if tex.fmt == 3:
            for i in range(0, n, 2):
                blob[o + i // 2] = (idx[i] & 15) | ((idx[i + 1] & 15) << 4)
        elif tex.fmt == 4:
            for i in range(n):
                blob[o + i] = idx[i] & 255
        elif tex.fmt == 2:
            for i in range(n):
                sh = (i % 4) * 2
                b = o + i // 4
                blob[b] = (blob[b] & ~(3 << sh)) | ((idx[i] & 3) << sh)
        else:
            raise ValueError(f"format {tex.fmt} not writable")

    # ---- inspection ----------------------------------------------------- #
    def render(self, tex: Entry):
        """RGBA PIL image of one texture."""
        from PIL import Image

        img = Image.new("RGBA", (tex.width, tex.height))
        px = img.load()
        pal = self.pal_for(tex)
        if tex.fmt == 7:      # direct
            for i in range(tex.width * tex.height):
                (v,) = struct.unpack_from("<H", self.blob, tex.data_off + i * 2)
                px[i % tex.width, i // tex.width] = (
                    (v & 31) * 255 // 31, ((v >> 5) & 31) * 255 // 31,
                    ((v >> 10) & 31) * 255 // 31, 255 if v & 0x8000 else 0)
            return img
        colors = self.palette_colors(
            pal, min(self._pal_size(tex.fmt), pal.pal_ncolors))
        idx = self.texel_indices(tex)
        alpha_bits = {1: (5, 3), 6: (3, 5)}.get(tex.fmt)
        for i, v in enumerate(idx):
            c = colors[v] if v < len(colors) else (255, 0, 255)
            a = 255
            if alpha_bits:
                shift, bits = alpha_bits
                raw = self.blob[tex.data_off + i] >> shift
                a = raw * 255 // ((1 << bits) - 1)
            elif tex.color0 and v == 0:
                a = 0
            px[i % tex.width, i // tex.width] = (*c, a)
        return img

    def bytes(self) -> bytes:
        return bytes(self.blob)
