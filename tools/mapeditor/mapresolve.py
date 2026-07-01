#!/usr/bin/env python3
"""Resolve a live RAM map id -> the zone_event JSON file that defines its events.

Chain (all from decomp source, so it stays correct across edits):
  RAM mapId (int)
    -> constants/maps.h : #define MAP_NAME  <id>
    -> src/data/map_headers.h : [MAP_NAME] = { .eventsBank = NARC_zone_event_NNN_* }
    -> files/fielddata/eventdata/zone_event/NNN_*.json
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

DECOMP = Path(__file__).resolve().parents[2] / "disasm" / "pokeheartgold"
MAPS_H = DECOMP / "include" / "constants" / "maps.h"
HEADERS_H = DECOMP / "src" / "data" / "map_headers.h"
ZONE_DIR = DECOMP / "files" / "fielddata" / "eventdata" / "zone_event"
FLAGS_H = DECOMP / "include" / "constants" / "flags.h"

_FLAGDEF = re.compile(r"#define\s+(FLAG_[A-Z0-9_]+)\s+(0x[0-9A-Fa-f]+|\d+)")

_DEF = re.compile(r"^#define\s+(MAP_[A-Z0-9_]+)\s+(\d+)", re.M)
_ENTRY = re.compile(r"\[(MAP_[A-Z0-9_]+)\]\s*=\s*\{", re.M)
_EVENTS = re.compile(r"\.eventsBank\s*=\s*NARC_zone_event_(\d+)_")


@lru_cache(maxsize=1)
def _map_name_to_id() -> dict[str, int]:
    return {m.group(1): int(m.group(2)) for m in _DEF.finditer(MAPS_H.read_text())}


@lru_cache(maxsize=1)
def _mapid_to_events_index() -> dict[int, int]:
    """Pair each [MAP_NAME] block with the first .eventsBank inside it."""
    text = HEADERS_H.read_text()
    names = _map_name_to_id()
    entries = list(_ENTRY.finditer(text))
    out: dict[int, int] = {}
    for i, m in enumerate(entries):
        name = m.group(1)
        end = entries[i + 1].start() if i + 1 < len(entries) else len(text)
        ev = _EVENTS.search(text, m.end(), end)
        if ev and name in names:
            out[names[name]] = int(ev.group(1))
    return out


@lru_cache(maxsize=1)
def _index_to_path() -> dict[int, Path]:
    out: dict[int, Path] = {}
    for p in ZONE_DIR.glob("*.json"):
        n = p.name.split("_", 1)[0]
        if n.isdigit():
            out[int(n)] = p
    return out


@lru_cache(maxsize=1)
def _flag_ids() -> dict[str, int]:
    return {m.group(1): int(m.group(2), 0) for m in _FLAGDEF.finditer(FLAGS_H.read_text())}


def flag_id(name: str) -> int | None:
    """Numeric id for a FLAG_* constant name (hex or decimal in flags.h)."""
    return _flag_ids().get(name)


@lru_cache(maxsize=1)
def map_list() -> list[tuple[int, str]]:
    """Sorted [(map_id, MAP_NAME)] for every map, first name wins on aliases."""
    id2name: dict[int, str] = {}
    for name, mid in _map_name_to_id().items():
        id2name.setdefault(mid, name)
    return sorted(id2name.items())


def zone_event_path(map_id: int) -> Path | None:
    """zone_event JSON Path for a live map id, or None if unmapped/dummy."""
    idx = _mapid_to_events_index().get(map_id)
    if idx is None:
        return None
    return _index_to_path().get(idx)


if __name__ == "__main__":
    import sys
    m2e = _mapid_to_events_index()
    print(f"maps.h defines: {len(_map_name_to_id())}")
    print(f"map_id -> events index pairs: {len(m2e)}")
    print(f"zone_event files: {len(_index_to_path())}")
    # spot-check the maps from our earlier hexdumps + a few overworld ones
    for mid in (int(a) for a in sys.argv[1:]) if len(sys.argv) > 1 else (0, 2, 4, 63, 67):
        p = zone_event_path(mid)
        print(f"  map {mid:>3} -> {p.name if p else '(none)'}")
