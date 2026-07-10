#!/usr/bin/env python3
"""narc.py - minimal Nitro NARC archive pack/unpack (byte-faithful).

NARC = 16-byte Nitro header + BTAF (member offset table) + BTNF (names,
flat/unused for these archives) + GMIF (member data, 4-byte aligned).

API:
  members = narc_read(path)          -> list[bytes]
  narc_write(path, members)          -> writes archive (flat BTNF, FF padding)
CLI:
  narc.py unpack <file.narc> <outdir>
  narc.py pack   <indir> <file.narc>     (members sorted numerically: 0.bin, 1.bin...)
  narc.py info   <file.narc>
"""
import os
import struct
import sys


def narc_read(path):
    with open(path, "rb") as f:
        b = f.read()
    assert b[0:4] == b"NARC", f"{path}: not a NARC"
    nblocks = struct.unpack_from("<H", b, 0x0E)[0]
    off = struct.unpack_from("<H", b, 0x0C)[0]  # header size (0x10)
    fatb_off = off
    assert b[fatb_off:fatb_off + 4] == b"BTAF"
    fatb_size = struct.unpack_from("<I", b, fatb_off + 4)[0]
    nfiles = struct.unpack_from("<I", b, fatb_off + 8)[0]
    entries = [struct.unpack_from("<II", b, fatb_off + 12 + i * 8) for i in range(nfiles)]
    fntb_off = fatb_off + fatb_size
    assert b[fntb_off:fntb_off + 4] == b"BTNF"
    fntb_size = struct.unpack_from("<I", b, fntb_off + 4)[0]
    fimg_off = fntb_off + fntb_size
    assert b[fimg_off:fimg_off + 4] == b"GMIF"
    data_base = fimg_off + 8
    return [b[data_base + s:data_base + e] for s, e in entries]


def narc_write(path, members):
    fat_entries = []
    data = bytearray()
    for m in members:
        start = len(data)
        data += m
        fat_entries.append((start, len(data)))
        while len(data) % 4:
            data.append(0xFF)
    fatb = b"BTAF" + struct.pack("<II", 12 + 8 * len(members), len(members))
    for s, e in fat_entries:
        fatb += struct.pack("<II", s, e)
    fntb = b"BTNF" + struct.pack("<I", 0x10) + struct.pack("<IHH", 4, 0, 1)
    fimg = b"GMIF" + struct.pack("<I", 8 + len(data)) + bytes(data)
    total = 0x10 + len(fatb) + len(fntb) + len(fimg)
    hdr = b"NARC" + struct.pack("<HHIHH", 0xFFFE, 0x0100, total, 0x10, 3)
    with open(path, "wb") as f:
        f.write(hdr + fatb + fntb + fimg)


def main():
    cmd = sys.argv[1]
    if cmd == "unpack":
        src, outdir = sys.argv[2], sys.argv[3]
        os.makedirs(outdir, exist_ok=True)
        ms = narc_read(src)
        for i, m in enumerate(ms):
            with open(os.path.join(outdir, f"{i}.bin"), "wb") as f:
                f.write(m)
        print(f"{len(ms)} members -> {outdir}")
    elif cmd == "pack":
        indir, dst = sys.argv[2], sys.argv[3]
        names = sorted(os.listdir(indir), key=lambda n: int(n.split(".")[0]))
        ms = []
        for n in names:
            with open(os.path.join(indir, n), "rb") as f:
                ms.append(f.read())
        narc_write(dst, ms)
        print(f"{len(ms)} members -> {dst}")
    elif cmd == "info":
        ms = narc_read(sys.argv[2])
        print(f"{sys.argv[2]}: {len(ms)} members")
        for i, m in enumerate(ms[:12]):
            print(f"  [{i}] {len(m)} bytes  head={m[:16].hex()}")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
