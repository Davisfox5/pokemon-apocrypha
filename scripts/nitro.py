#!/usr/bin/env python3
"""nitro.py — minimal codec for HGSS trainer battle sprite NARC members.

Shared by extract_trainer.py / insert_trainer.py. Layout verified against
the vanilla NARCs (a/0/5/8 fronts, a/0/0/6 backs) and nitrogfx source
(disasm/pokeheartgold/tools/nitrogfx/gfx.c):

  Each trainer class is 5 consecutive NARC members:
    +0  NCGR  sprite tile data (plain tiled 4bpp — NOT scanned/encrypted;
              charHeader[0x14] == 0)
    +1  NCLR  palette (16 colors used; BGR555)
    +2  NCER  cell banks: one bank per frame, 6 OAMs each, char-name
              shift = blockSize field, per-bank char partitions (3200 B
              = one 80x80 frame) when >1 bank
    +3  NANR  animation timing (left untouched by these tools)
    +4  NCGR  aux tile data (200 tiles = 2 extra VRAM-streamed animation
              frames, same cell layout as the main NCGR)

  NCGR: pixel data at chunk+0x20, byte size at chunk+0x18 (nitrogfx
  ReadNtrImage). Low nibble = left pixel.
  NCLR: data size at chunk+0x10, data offset at chunk+0x14 (relative to
  chunk start + 0x10... verified empirically: data = file[16+off:]).
"""

import struct

MEMBERS_PER_CLASS = 5
TILE_BYTES = 32          # 8x8 @ 4bpp
FRAME_TILES = 100        # 80x80 sprite = 100 tiles
FRAME_BYTES = FRAME_TILES * TILE_BYTES

OAM_SIZES = {(0, 0): (8, 8), (0, 1): (16, 16), (0, 2): (32, 32), (0, 3): (64, 64),
             (1, 0): (16, 8), (1, 1): (32, 8), (1, 2): (32, 16), (1, 3): (64, 32),
             (2, 0): (8, 16), (2, 1): (8, 32), (2, 2): (16, 32), (2, 3): (32, 64)}


def _check(cond, msg):
    if not cond:
        raise ValueError(msg)


# ---------- NCLR ----------

def nclr_palette(b):
    """-> list of (r, g, b) 8-bit tuples (all entries stored in the file).

    nitrogfx ReadNtrPalette: color data at chunk+0x18, byte size at
    chunk+0x10.
    """
    _check(b[:4] == b"RLCN" and b[16:20] == b"TTLP", "not an NCLR")
    ds, = struct.unpack_from("<I", b, 16 + 0x10)
    raw = b[16 + 0x18:16 + 0x18 + ds]
    pal = []
    for i in range(0, len(raw), 2):
        v, = struct.unpack_from("<H", raw, i)
        r, g, bl = v & 31, (v >> 5) & 31, (v >> 10) & 31
        pal.append(((r << 3) | (r >> 2), (g << 3) | (g >> 2), (bl << 3) | (bl >> 2)))
    return pal


def nclr_replace(b, colors):
    """Return a new NCLR blob with its first len(colors) entries replaced."""
    _check(b[:4] == b"RLCN" and b[16:20] == b"TTLP", "not an NCLR")
    ds, = struct.unpack_from("<I", b, 16 + 0x10)
    _check(len(colors) * 2 <= ds, f"palette too long ({len(colors)} colors for {ds // 2} slots)")
    out = bytearray(b)
    for i, (r, g, bl) in enumerate(colors):
        v = (r >> 3) | ((g >> 3) << 5) | ((bl >> 3) << 10)
        struct.pack_into("<H", out, 16 + 0x18 + 2 * i, v)
    return bytes(out)


# ---------- NCGR ----------

def ncgr_tiles(b):
    """-> raw tile bytes (nitrogfx: data at chunk+0x20, size at chunk+0x18)."""
    _check(b[:4] == b"RGCN" and b[16:20] == b"RAHC", "not an NCGR")
    ds, = struct.unpack_from("<I", b, 16 + 0x18)
    return b[16 + 0x20:16 + 0x20 + ds]


def ncgr_replace(b, tiles):
    """Return a new NCGR blob with its tile data replaced (same size only)."""
    _check(b[:4] == b"RGCN" and b[16:20] == b"RAHC", "not an NCGR")
    ds, = struct.unpack_from("<I", b, 16 + 0x18)
    _check(len(tiles) == ds, f"tile data size mismatch: got {len(tiles)}, member holds {ds}")
    return b[:16 + 0x20] + bytes(tiles) + b[16 + 0x20 + ds:]


# ---------- NCER ----------

def ncer_banks(b):
    """-> (banks, char_shift, partitions)

    banks: list of frames, each (oams, origin) where oams is a list of
    (x, y, w, h, char) OAM entries and origin = (minX, minY) from the
    bank's bounding box (animation frames shift their box — e.g. the
    backsprite throw slides right — so composition must anchor to it).
    partitions: per-bank (byte_offset, byte_size) into the NCGR tile data.
    """
    _check(b[:4] == b"RECN" and b[16:20] == b"KBEC", "not an NCER")
    base = 24
    nbanks, btype = struct.unpack_from("<HH", b, base)
    bankoff, blocksize, partoff = struct.unpack_from("<III", b, base + 4)
    entsize = 16 if btype == 1 else 8
    oambase = base + bankoff + nbanks * entsize
    banks = []
    for i in range(nbanks):
        o = base + bankoff + i * entsize
        ncells, _ = struct.unpack_from("<HH", b, o)
        oamoff, = struct.unpack_from("<I", b, o + 4)
        if btype == 1:
            _maxx, _maxy, minx, miny = struct.unpack_from("<hhhh", b, o + 8)
        else:
            minx = miny = -40  # no bounds stored; assume centered 80x80
        oams = []
        for c in range(ncells):
            a0, a1, a2 = struct.unpack_from("<HHH", b, oambase + oamoff + c * 6)
            y = a0 & 0xFF
            y -= 256 if y >= 128 else 0
            x = a1 & 0x1FF
            x -= 512 if x >= 256 else 0
            w, h = OAM_SIZES[((a0 >> 14) & 3, (a1 >> 14) & 3)]
            oams.append((x, y, w, h, a2 & 0x3FF))
        banks.append((oams, (minx, miny)))
    parts = [(0, None)] * nbanks
    if partoff:
        po = base + partoff
        parts = [struct.unpack_from("<II", b, po + 8 + 8 * i) for i in range(nbanks)]
    return banks, blocksize & 3, parts


# ---------- frame <-> tiles ----------

def compose_frame(bank, tiles, shift, part_off, canvas=80):
    """OAM cell bank + tile data -> flat list of palette indices (canvas^2)."""
    oams, (minx, miny) = bank
    out = [0] * (canvas * canvas)
    tilebase = part_off // TILE_BYTES
    for x, y, w, h, char in oams:
        tw = w // 8
        tstart = tilebase + (char << shift)
        for t in range(tw * (h // 8)):
            tile = tiles[(tstart + t) * TILE_BYTES:(tstart + t + 1) * TILE_BYTES]
            if len(tile) < TILE_BYTES:
                continue
            tx, ty = x - minx + (t % tw) * 8, y - miny + (t // tw) * 8
            for i in range(64):
                v = tile[i // 2] & 0xF if i % 2 == 0 else tile[i // 2] >> 4
                X, Y = tx + i % 8, ty + i // 8
                # DS OAM priority: the lowest-index OAM with an opaque texel
                # wins, so never overdraw an already-set pixel (a few vanilla
                # cells overlap, e.g. front class 102 banks 3-6)
                if 0 <= X < canvas and 0 <= Y < canvas and v and not out[Y * canvas + X]:
                    out[Y * canvas + X] = v
    return out


def decompose_frame(pixels, bank, shift, part_size, canvas=80, base=None):
    """Inverse of compose_frame: palette indices -> one partition's tile bytes.

    Bytes the cell layout never references are taken from `base` (the
    original partition bytes) when given, else left 0 — a few vanilla
    classes keep live data in tiles their static cell doesn't reference.
    """
    oams, (minx, miny) = bank
    out = bytearray(base[:part_size]) if base is not None else bytearray(part_size)
    if len(out) < part_size:
        out.extend(bytes(part_size - len(out)))
    for x, y, w, h, char in oams:
        tw = w // 8
        tstart = char << shift  # relative to this frame's partition
        for t in range(tw * (h // 8)):
            tx, ty = x - minx + (t % tw) * 8, y - miny + (t // tw) * 8
            for i in range(0, 64, 2):
                X, Y = tx + i % 8, ty + i // 8
                lo = pixels[Y * canvas + X] if 0 <= X < canvas and 0 <= Y < canvas else 0
                hi = pixels[Y * canvas + X + 1] if 0 <= X + 1 < canvas and 0 <= Y < canvas else 0
                off = (tstart + t) * TILE_BYTES + i // 2
                if off < part_size:
                    out[off] = (lo & 0xF) | ((hi & 0xF) << 4)
    return bytes(out)


# ---------- BTX0 (overworld mmodel textures) ----------
#
# HGSS overworld NPC sprites are billboarded textures: one BTX0 (NSBTX) file
# per model in files/data/mmodel/mmodel/ (mmodel_%08d.bin, packed by index
# into mmodel.narc). Layout verified empirically against vanilla members
# (e.g. 6 GIRL2, 118 GSGIRL2): a single TEX0 block whose header offsets at
# +0x0E/+0x34 point directly at NNS resource dicts. NPC walkers hold 16
# dict entries sharing 12 unique 512-byte 32x32 4bpp frames plus one
# 16-color palette.

def _btx_dict(b, base):
    """Parse an NNS G3D resource dict -> (entries, names)."""
    _check(b[base] == 0, f"resdict revision != 0 at {hex(base)}")
    count = b[base + 1]
    entbase = base + struct.unpack_from("<H", b, base + 6)[0]
    unit, nameofs = struct.unpack_from("<HH", b, entbase)
    ents = [b[entbase + 4 + i * unit: entbase + 4 + (i + 1) * unit] for i in range(count)]
    nb = entbase + nameofs
    names = [b[nb + i * 16: nb + i * 16 + 16].rstrip(b"\0").decode("ascii", "replace")
             for i in range(count)]
    return ents, names


def _btx_tex0(b):
    _check(b[:4] == b"BTX0", "not a BTX0")
    t, = struct.unpack_from("<I", b, 0x10)
    _check(b[t:t + 4] == b"TEX0", "BTX0 without TEX0 block")
    return t


def btx_frames(b):
    """-> (frames, tex_data_off): frames = [(name, offset, w, h, color0)]
    for every 4bpp-paletted (format 3) texture, in dict order. Offsets are
    relative to tex_data_off; several dict entries may share one offset."""
    t = _btx_tex0(b)
    texinfo = struct.unpack_from("<H", b, t + 0x0E)[0]
    texdata = struct.unpack_from("<I", b, t + 0x14)[0]
    ents, names = _btx_dict(b, t + texinfo)
    frames = []
    for ent, name in zip(ents, names):
        param, = struct.unpack_from("<I", ent)
        fmt = (param >> 26) & 7
        if fmt != 3:
            continue
        frames.append((name, (param & 0xFFFF) << 3,
                       8 << ((param >> 20) & 7), 8 << ((param >> 23) & 7),
                       (param >> 29) & 1))
    return frames, t + texdata


def btx_pixels(b, frame, tex_data_off):
    """-> flat list of palette indices for one frame from btx_frames."""
    _name, ofs, w, h, _c0 = frame
    raw = b[tex_data_off + ofs: tex_data_off + ofs + w * h // 2]
    out = []
    for byte in raw:
        out.append(byte & 0xF)
        out.append(byte >> 4)
    return out


def btx_palette(b, n=16):
    """-> first palette's first n colors as 8-bit (r, g, b) tuples."""
    t = _btx_tex0(b)
    palinfo = struct.unpack_from("<I", b, t + 0x34)[0]
    paldata = struct.unpack_from("<I", b, t + 0x38)[0]
    ents, _names = _btx_dict(b, t + palinfo)
    pofs = struct.unpack_from("<H", ents[0])[0] << 3
    pal = []
    for i in range(n):
        v, = struct.unpack_from("<H", b, t + paldata + pofs + 2 * i)
        r, g, bl = v & 31, (v >> 5) & 31, (v >> 10) & 31
        pal.append(((r << 3) | (r >> 2), (g << 3) | (g >> 2), (bl << 3) | (bl >> 2)))
    return pal


def btx_replace(b, frame_pixels, palette=None):
    """Return a new BTX0 blob with texture pixels (and optionally the first
    palette's colors) replaced in place. frame_pixels maps a frame's data
    offset (from btx_frames) -> flat list of palette indices."""
    t = _btx_tex0(b)
    out = bytearray(b)
    frames, texdata = btx_frames(b)
    sizes = {ofs: (w, h) for _n, ofs, w, h, _c in frames}
    for ofs, pixels in frame_pixels.items():
        _check(ofs in sizes, f"no texture at offset {hex(ofs)}")
        w, h = sizes[ofs]
        _check(len(pixels) == w * h, f"frame at {hex(ofs)}: expected {w * h} pixels, got {len(pixels)}")
        for i in range(0, len(pixels), 2):
            _check(pixels[i] < 16 and pixels[i + 1] < 16, "palette index out of range")
            out[texdata + ofs + i // 2] = pixels[i] | (pixels[i + 1] << 4)
    if palette is not None:
        palinfo = struct.unpack_from("<I", b, t + 0x34)[0]
        paldata = struct.unpack_from("<I", b, t + 0x38)[0]
        ents, _names = _btx_dict(b, t + palinfo)
        pofs = struct.unpack_from("<H", ents[0])[0] << 3
        palsize = struct.unpack_from("<H", b, t + 0x30)[0] << 3
        _check(len(palette) * 2 <= palsize, f"palette too long ({len(palette)} colors)")
        for i, (r, g, bl) in enumerate(palette):
            v = (r >> 3) | ((g >> 3) << 5) | ((bl >> 3) << 10)
            struct.pack_into("<H", out, t + paldata + pofs + 2 * i, v)
    return bytes(out)


# ---------- class-level helpers ----------

def class_members(members, cls):
    n = len(members) // MEMBERS_PER_CLASS
    _check(0 <= cls < n, f"class {cls} out of range (NARC holds {n} classes)")
    i = cls * MEMBERS_PER_CLASS
    return members[i:i + MEMBERS_PER_CLASS]


def class_frame_count(members, cls):
    banks, _, _ = ncer_banks(class_members(members, cls)[2])
    return len(banks)
