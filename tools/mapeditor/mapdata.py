#!/usr/bin/env python3
"""Byte-accurate parse/serialize for HGSS map data (the-omni-hack / pokeheartgold).

Ground truth is the decomp loader, not guesswork:
  MapMatrix on-disk layout -- src/map_matrix.c : MapMatrix_MapMatrixData_Load()
    u8  width
    u8  height
    u8  has_headers
    u8  has_altitudes
    u8  name_length
    u8  name[name_length]                 (NOT null-terminated)
    u16 headers[width*height]   if has_headers      (little-endian, row-major)
    u8  altitudes[width*height] if has_altitudes
    u16 models[width*height]                        (little-endian, row-major)

  Arrays are indexed [y*width + x] (see the MI_CpuCopy8 width*height copies).

zone_event is already human-readable JSON on disk (jsonproc compiles it at build
time), so we round-trip it as JSON and let `make` recompile.
"""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass, field
from pathlib import Path


# --------------------------------------------------------------------------- #
#  Map matrix (zone composition grid: one cell == one 32x32 sub-map model)
# --------------------------------------------------------------------------- #
@dataclass
class MapMatrix:
    width: int
    height: int
    name: str
    models: list[int]                       # len == width*height, row-major
    headers: list[int] | None = None        # present iff has_headers
    altitudes: list[int] | None = None      # present iff has_altitudes

    # -- parse ------------------------------------------------------------- #
    @classmethod
    def parse(cls, data: bytes) -> "MapMatrix":
        mv = memoryview(data)
        width, height, has_headers, has_altitudes, name_len = mv[:5]
        off = 5
        name = bytes(mv[off:off + name_len]).decode("ascii")
        off += name_len
        n = width * height

        headers = None
        if has_headers:
            headers = list(struct.unpack_from(f"<{n}H", mv, off))
            off += n * 2

        altitudes = None
        if has_altitudes:
            altitudes = list(struct.unpack_from(f"<{n}B", mv, off))
            off += n

        models = list(struct.unpack_from(f"<{n}H", mv, off))
        off += n * 2

        if off != len(data):
            raise ValueError(f"trailing bytes: parsed {off} of {len(data)}")
        return cls(width, height, name, models, headers, altitudes)

    # -- serialize --------------------------------------------------------- #
    def serialize(self) -> bytes:
        n = self.width * self.height
        for label, arr in (("models", self.models),
                           ("headers", self.headers),
                           ("altitudes", self.altitudes)):
            if arr is not None and len(arr) != n:
                raise ValueError(f"{label} len {len(arr)} != width*height {n}")
        name_b = self.name.encode("ascii")
        out = bytearray()
        out += struct.pack("<BBBBB", self.width, self.height,
                           1 if self.headers is not None else 0,
                           1 if self.altitudes is not None else 0,
                           len(name_b))
        out += name_b
        if self.headers is not None:
            out += struct.pack(f"<{n}H", *self.headers)
        if self.altitudes is not None:
            out += struct.pack(f"<{n}B", *self.altitudes)
        out += struct.pack(f"<{n}H", *self.models)
        return bytes(out)

    @classmethod
    def load(cls, path: str | Path) -> "MapMatrix":
        return cls.parse(Path(path).read_bytes())

    def cell(self, x: int, y: int) -> int:
        return self.models[y * self.width + x]


# --------------------------------------------------------------------------- #
#  Zone events (objects / warps / triggers / bg) -- stored as JSON on disk
# --------------------------------------------------------------------------- #
@dataclass
class ZoneEvents:
    path: Path
    data: dict

    @classmethod
    def load(cls, path: str | Path) -> "ZoneEvents":
        p = Path(path)
        return cls(p, json.loads(p.read_text()))

    @property
    def objects(self) -> list[dict]:
        return self.data.setdefault("objects", [])

    @property
    def warps(self) -> list[dict]:
        return self.data.setdefault("warps", [])

    @property
    def coords(self) -> list[dict]:
        return self.data.setdefault("coords", [])

    @property
    def bgs(self) -> list[dict]:
        return self.data.setdefault("bgs", [])

    def save(self, indent: int = 2) -> None:
        # jsonproc parses standard JSON; keep 2-space indent + trailing newline
        # to match the repo's existing zone_event files for clean diffs.
        self.path.write_text(json.dumps(self.data, indent=indent) + "\n")
