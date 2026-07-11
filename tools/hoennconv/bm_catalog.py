#!/usr/bin/env python3
"""Catalog the vanilla HGSS building models (bm_field.narc) for the
Hoenn retexture pass: model id -> NSBMD internal names + where vanilla
already places it (which chunks / how often).

The internal model/texture names (readable ASCII in the BMD0's name
dictionaries) are how you find candidates: e.g. every Johto house model is
named, and picking a visually-similar donor for a Hoenn building means
matching against these names plus the placement counts.

Writes converted/hoenn/buildings/bm_field_catalog.json.
"""

from __future__ import annotations

import json
import re
import struct
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import narc

ROOT = Path(__file__).resolve().parents[2]
HG = ROOT / "disasm" / "pokeheartgold"
OUT = ROOT / "converted" / "hoenn" / "buildings"

_NAME = re.compile(rb"[A-Za-z_][A-Za-z0-9_\-]{3,15}")


def nsbmd_names(blob: bytes) -> list[str]:
    """Readable names from a BMD0's dictionaries (model + texture names)."""
    names = []
    for m in _NAME.finditer(blob):
        s = m.group().decode()
        if s not in ("BMD0", "MDL0", "TEX0") and s not in names:
            names.append(s)
    return names[:12]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    models = narc.load(HG / "files/fielddata/build_model/bm_field.narc")

    # how often each model id appears across the vanilla overworld chunks
    placements = Counter()
    for member in narc.load(HG / "files/a/0/6/5"):
        perm, bldg, _, _ = struct.unpack_from("<4I", member, 0)
        _, bgs = struct.unpack_from("<HH", member, 16)
        off = 20 + bgs + perm
        for i in range(bldg // 48):
            placements[struct.unpack_from("<I", member, off + i * 48)[0]] += 1

    catalog = [{
        "id": i,
        "bytes": len(m),
        "names": nsbmd_names(m),
        "vanilla_placements": placements.get(i, 0),
    } for i, m in enumerate(models)]
    (OUT / "bm_field_catalog.json").write_text(json.dumps(catalog, indent=2) + "\n")
    named = sum(1 for c in catalog if c["names"])
    print(f"{len(catalog)} models, {named} with readable names, "
          f"{sum(placements.values())} total vanilla placements")


if __name__ == "__main__":
    main()
