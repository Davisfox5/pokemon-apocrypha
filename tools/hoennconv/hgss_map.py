#!/usr/bin/env python3
"""Parse/serialize one HGSS land-data member (a map "chunk": the unit the
map matrix composes into a region).

Ground truth: DSPRE MapFile.cs (HGSS branch) + byte-level verification against
all 676 members of the vanilla archive files/a/0/6/5 (round-trips identically,
see verify.py).

Member layout:
  u32 permissionsSize   (always 0x800: 32*32 cells * 2 bytes)
  u32 buildingsSize     (48 bytes per building entry)
  u32 modelSize         (NSBMD, "BMD0" magic)
  u32 bdhcSize          ("BDHC" magic terrain-height table)
  -- HGSS only: background-sound plates --
  u16 0x1234 signature
  u16 bgsSize           (bytes of plate data that follow; 0 is common)
  u8  bgs[bgsSize]
  -- sections, in header order --
  cell[32*32] permissions, row-major, 2 bytes each:
      u8 type       (terrain class: 0x02 encounter grass, 0x15 sea, 0x21 sand,
                     0x10 still water, 0x00 plain ... verified empirically
                     against Route 29 / Route 41 / Route 40 vanilla chunks)
      u8 collision  (0x00 passable, 0x80 blocked; vanilla data also carries
                     other low-bit values we preserve but do not emit)
  u8 buildings[buildingsSize]
  u8 model[modelSize]
  u8 bdhc[bdhcSize]
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

CHUNK_W = 32
CHUNK_H = 32
N_CELLS = CHUNK_W * CHUNK_H
BGS_SIGNATURE = 0x1234


@dataclass
class MapChunk:
    types: list[int]          # len 1024, row-major
    collisions: list[int]     # len 1024, row-major
    bgs: bytes = b""
    buildings: bytes = b""
    model: bytes = b""
    bdhc: bytes = b""

    @classmethod
    def parse(cls, data: bytes) -> "MapChunk":
        perm_sz, bldg_sz, model_sz, bdhc_sz = struct.unpack_from("<4I", data, 0)
        if perm_sz != N_CELLS * 2:
            raise ValueError(f"unexpected permissions size {perm_sz:#x}")
        sig, bgs_sz = struct.unpack_from("<HH", data, 16)
        if sig != BGS_SIGNATURE:
            raise ValueError(f"missing 0x1234 BGS signature (got {sig:#x})")
        off = 20
        bgs = bytes(data[off:off + bgs_sz]); off += bgs_sz
        cells = data[off:off + perm_sz]; off += perm_sz
        buildings = bytes(data[off:off + bldg_sz]); off += bldg_sz
        model = bytes(data[off:off + model_sz]); off += model_sz
        bdhc = bytes(data[off:off + bdhc_sz]); off += bdhc_sz
        if off != len(data):
            raise ValueError(f"trailing bytes: parsed {off} of {len(data)}")
        return cls(list(cells[0::2]), list(cells[1::2]), bgs, buildings, model, bdhc)

    def serialize(self) -> bytes:
        if len(self.types) != N_CELLS or len(self.collisions) != N_CELLS:
            raise ValueError("permission planes must be 32x32")
        cells = bytearray(N_CELLS * 2)
        cells[0::2] = bytes(self.types)
        cells[1::2] = bytes(self.collisions)
        out = struct.pack("<4I", len(cells), len(self.buildings),
                          len(self.model), len(self.bdhc))
        out += struct.pack("<HH", BGS_SIGNATURE, len(self.bgs)) + self.bgs
        return out + bytes(cells) + self.buildings + self.model + self.bdhc

    @classmethod
    def load(cls, path: str | Path) -> "MapChunk":
        return cls.parse(Path(path).read_bytes())

    # -- convenience ---------------------------------------------------- #
    def cell(self, x: int, y: int) -> tuple[int, int]:
        i = y * CHUNK_W + x
        return self.types[i], self.collisions[i]

    def set_cell(self, x: int, y: int, type_: int, collision: int) -> None:
        i = y * CHUNK_W + x
        self.types[i] = type_ & 0xFF
        self.collisions[i] = collision & 0xFF


def donor_flat_parts(vanilla_land_narc_members: list[bytes]) -> tuple[bytes, bytes]:
    """(model, bdhc) from the simplest vanilla chunk, for use as structural
    donors in generated chunks until real Hoenn models exist.

    We pick the member with the smallest model+bdhc — in vanilla HGSS that is
    a flat border chunk, which renders as plain ground at height 0.
    """
    best = min(vanilla_land_narc_members,
               key=lambda m: len(m))
    c = MapChunk.parse(best)
    return c.model, c.bdhc
