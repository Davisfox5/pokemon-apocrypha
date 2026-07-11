#!/usr/bin/env python3
"""Byte-accurate NARC (Nitro Archive) reader/writer.

Layout verified against the vanilla HGSS land-data archive
(disasm/pokeheartgold/files/a/0/6/5) — parse+build round-trips the whole
19.5 MB file byte-identically (see verify.py).

  NARC header (16 bytes):
    "NARC"  u16 0xFFFE (BOM)  u16 0x0100 (version)  u32 fileSize
    u16 headerSize(0x10)      u16 chunkCount(3)
  BTAF chunk: "BTAF" u32 size  u32 fileCount  {u32 start, u32 end}[fileCount]
  BTNF chunk: "BTNF" u32 size  (flat archives: 8-byte dummy root entry)
  GMIF chunk: "GMIF" u32 size  member data (starts/ends relative to here+8)
"""

from __future__ import annotations

import struct
from pathlib import Path


def parse(data: bytes) -> list[bytes]:
    """NARC bytes -> list of member blobs."""
    if data[:4] != b"NARC":
        raise ValueError("not a NARC")
    off = 16
    if data[off:off + 4] != b"BTAF":
        raise ValueError("BTAF chunk missing")
    btaf_size, count = struct.unpack_from("<II", data, off + 4)
    fat = [struct.unpack_from("<II", data, off + 12 + 8 * i) for i in range(count)]
    off += btaf_size
    if data[off:off + 4] != b"BTNF":
        raise ValueError("BTNF chunk missing")
    off += struct.unpack_from("<I", data, off + 4)[0]
    if data[off:off + 4] != b"GMIF":
        raise ValueError("GMIF chunk missing")
    base = off + 8
    return [bytes(data[base + s:base + e]) for s, e in fat]


def build(members: list[bytes]) -> bytes:
    """List of member blobs -> flat (nameless) NARC, vanilla-compatible.

    Members are 4-byte aligned within GMIF, matching how the vanilla
    archives are packed (padding bytes are 0xFF, as knarc emits).
    """
    fat = []
    blob = bytearray()
    for m in members:
        start = len(blob)
        blob += m
        fat.append((start, len(blob)))
        while len(blob) % 4:
            blob.append(0xFF)
    btaf = b"BTAF" + struct.pack("<II", 12 + 8 * len(fat), len(fat))
    btaf += b"".join(struct.pack("<II", s, e) for s, e in fat)
    btnf = b"BTNF" + struct.pack("<I", 16) + struct.pack("<IHH", 4, 0, 1)
    gmif = b"GMIF" + struct.pack("<I", 8 + len(blob)) + bytes(blob)
    body = btaf + btnf + gmif
    hdr = b"NARC" + struct.pack("<HHIHH", 0xFFFE, 0x0100, 16 + len(body), 0x10, 3)
    return hdr + body


def load(path: str | Path) -> list[bytes]:
    return parse(Path(path).read_bytes())
