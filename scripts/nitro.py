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


# ---------- class-level helpers ----------

def class_members(members, cls):
    n = len(members) // MEMBERS_PER_CLASS
    _check(0 <= cls < n, f"class {cls} out of range (NARC holds {n} classes)")
    i = cls * MEMBERS_PER_CLASS
    return members[i:i + MEMBERS_PER_CLASS]


def class_frame_count(members, cls):
    banks, _, _ = ncer_banks(class_members(members, cls)[2])
    return len(banks)
