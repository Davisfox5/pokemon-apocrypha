#!/usr/bin/env python3
"""Verification gate for the Hoenn -> HGSS conversion. Run after any format
or mapping change:  python3 tools/hoennconv/verify.py

1. Format ground truth: parse + re-serialize every vanilla HGSS land-data
   member and the whole NARC byte-identically, and round-trip every vanilla
   map matrix. If these fail, our understanding of the DS formats is wrong
   and nothing downstream can be trusted.
2. Generated output: every emitted chunk re-parses, the matrix is
   self-consistent, and every zone_event JSON loads with in-range coords.
3. Behavior coverage: no Gen-3 behavior on the stitched overworld silently
   falls back to plain-passable unless it is on the reviewed KNOWN_PLAIN list.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "mapeditor"))

import behavior_map
import gba
import narc
import stitch
from hgss_map import MapChunk
from mapdata import MapMatrix

ROOT = Path(__file__).resolve().parents[2]
HG = ROOT / "disasm" / "pokeheartgold"
OUT = ROOT / "converted" / "hoenn"

# Gen-3 behaviors reviewed as "plain ground is the right conversion".
KNOWN_PLAIN = {
    "MB_NORMAL", "MB_MOUNTAIN_TOP", "MB_SHORT_GRASS", "MB_NO_RUNNING",
    "MB_BERRY_TREE_SOIL", "MB_REFLECTION_UNDER_BRIDGE", "MB_MUDDY_SLOPE",
    "MB_BRIDGE_OVER_POND_HIGH", "MB_BRIDGE_OVER_POND_MED",
    "MB_BRIDGE_OVER_POND_LOW",
    "MB_BRIDGE_OVER_POND_HIGH_EDGE_1", "MB_BRIDGE_OVER_POND_HIGH_EDGE_2",
    "MB_BRIDGE_OVER_POND_MED_EDGE_1", "MB_BRIDGE_OVER_POND_MED_EDGE_2",
    "MB_HORIZONTAL_RAIL", "MB_VERTICAL_RAIL",
    "MB_ISOLATED_HORIZONTAL_RAIL", "MB_ISOLATED_VERTICAL_RAIL",
    "MB_BIKE_BRIDGE_OVER_BARRIER",
    # secret bases are cut content for the hack's Hoenn (walls stay blocked
    # via grid collision; spots become plain scenery)
    "MB_SECRET_BASE_WALL", "MB_SECRET_BASE_SPOT_RED_CAVE",
    "MB_SECRET_BASE_SPOT_BROWN_CAVE", "MB_SECRET_BASE_SPOT_YELLOW_CAVE",
    "MB_SECRET_BASE_SPOT_BLUE_CAVE", "MB_SECRET_BASE_SPOT_SHRUB",
    "MB_SECRET_BASE_SPOT_TREE_LEFT", "MB_SECRET_BASE_SPOT_TREE_RIGHT",
    "MB_VASE", "MB_LONG_GRASS_SOUTH_EDGE", "MB_WATER_DOOR",
    "MB_STAIRS_OUTSIDE_ABANDONED_SHIP", "MB_SOUTH_ARROW_WARP",
}

fails = 0


def check(ok: bool, label: str) -> None:
    global fails
    print(("  ok   " if ok else "  FAIL ") + label)
    if not ok:
        fails += 1


def main() -> None:
    # -- 1. vanilla round-trips ------------------------------------------- #
    raw = (HG / "files/a/0/6/5").read_bytes()
    members = narc.parse(raw)
    check(narc.build(members) == raw, f"NARC container round-trip ({len(members)} members)")
    bad = sum(1 for m in members if MapChunk.parse(m).serialize() != m)
    check(bad == 0, "all vanilla land-data members round-trip")
    mm_dir = HG / "files/fielddata/mapmatrix/map_matrix"
    bad = 0
    n = 0
    for p in sorted(mm_dir.glob("*.bin")):
        n += 1
        if MapMatrix.load(p).serialize() != p.read_bytes():
            bad += 1
    check(bad == 0, f"all {n} vanilla map matrices round-trip")

    # -- 2. generated output ----------------------------------------------- #
    if not OUT.exists():
        print("  (converted/hoenn missing - run convert.py first)")
        sys.exit(1)
    matrix = MapMatrix.load(OUT / "matrix/hoenn_overworld.bin")
    chunk_files = sorted((OUT / "land_data").glob("chunk_*.bin"))
    for f in chunk_files:
        c = MapChunk.load(f)
        if c.serialize() != f.read_bytes():
            check(False, f"{f.name} round-trip")
            break
    else:
        check(True, f"all {len(chunk_files)} generated chunks re-parse")
    check(max(matrix.models) < len(chunk_files),
          "matrix model ids within generated chunk range")
    gen_narc = narc.parse((OUT / "land_data.narc").read_bytes())
    check(len(gen_narc) == len(chunk_files), "land_data.narc member count")

    manifest = json.loads((OUT / "manifest.json").read_text())
    W, H = manifest["canvas_metatiles"]
    bad = []
    for entry in manifest["maps"]:
        j = json.loads((OUT / entry["zone_event"]).read_text())
        for kind in ("objects", "warps", "coords", "bgs"):
            for e in j.get(kind, []):
                if not (0 <= e["x"] < W and 0 <= e["z"] < H):
                    bad.append((entry["gen3_id"], kind, e["x"], e["z"]))
    check(not bad, f"zone_event coords inside canvas ({bad[:3]})" if bad
          else "zone_event coords inside canvas")

    # -- 3. behavior coverage ----------------------------------------------- #
    placed = stitch.stitch()
    placed, _, _ = stitch.normalize(placed)
    behaviors = gba.behaviors()
    pairs: dict[tuple, gba.TilesetPair] = {}
    seen = Counter()
    for mid, p in placed.items():
        l = gba.load_layout(p.layout_id)
        key = (l.primary_tileset, l.secondary_tileset)
        pair = pairs.setdefault(key, gba.TilesetPair(*key))
        for cell in l.blockdata:
            seen[behaviors.get(pair.behavior(cell & gba.MAPGRID_METATILE_MASK), "?")] += 1
    unmapped = [n for n in seen
                if n not in behavior_map._TABLE
                and not n.startswith("MB_IMPASSABLE")
                and n not in KNOWN_PLAIN]
    check(not unmapped, "behavior coverage"
          + ("" if not unmapped else f" — unreviewed: {sorted(unmapped)}"))

    print(("PASS" if fails == 0 else f"{fails} FAILURES"))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
