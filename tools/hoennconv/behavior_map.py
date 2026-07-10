#!/usr/bin/env python3
"""Gen-3 metatile behavior + collision  ->  Gen-4 (type byte, collision byte).

Gen-4 type values verified empirically against vanilla HGSS chunks
(tools/hoennconv/verify.py renders them against known maps):
  0x02 encounter grass        (Route 29 grass patches)
  0x15 surfable sea water     (Route 41 open sea)
  0x21 sand/beach             (Route 40 beach)
  0x10 still/pond water       (present on lake chunks)
  0x00 plain walkable ground

Values marked UNVERIFIED below follow the community (DSPRE) Gen-4 tables and
must be checked in-game once a Hoenn chunk boots: ledges 0x38-0x3B, ice 0x20,
waterfall 0x13, doors/warp panels 0x69/0x6D.

Collision byte: 0x00 passable, 0x80 blocked (the only two values community
tools emit; vanilla data carries extra low bits we don't reproduce).
"""

from __future__ import annotations

BLOCKED = 0x80
PASSABLE = 0x00

# Gen-4 type-byte constants
T_PLAIN = 0x00
T_GRASS = 0x02          # wild encounters
T_LONG_GRASS = 0x03
T_SEA = 0x15            # surfable, deep
T_POND = 0x10           # surfable, still
T_SAND = 0x21
T_ICE = 0x20            # UNVERIFIED
T_WATERFALL = 0x13      # UNVERIFIED
T_JUMP_E = 0x38         # UNVERIFIED (ledge hop east)
T_JUMP_W = 0x39         # UNVERIFIED
T_JUMP_N = 0x3A         # UNVERIFIED
T_JUMP_S = 0x3B         # UNVERIFIED
T_DOOR = 0x69           # UNVERIFIED (animated door warp)
T_STAIRS = 0x6D         # UNVERIFIED (non-animated warp: stairs/holes)

# MB_* name -> (gen4 type, force_collision or None)
# force_collision overrides the map.bin collision bits (e.g. water is
# "blocked" for walking in Gen 3 grids but must be surfable in Gen 4).
_TABLE: dict[str, tuple[int, int | None]] = {
    # grass
    "MB_TALL_GRASS": (T_GRASS, None),
    "MB_LONG_GRASS": (T_LONG_GRASS, None),
    "MB_UNUSED_05": (T_GRASS, None),
    "MB_SHORT_GRASS": (T_PLAIN, None),
    "MB_ASHGRASS": (T_GRASS, None),
    "MB_FOOTPRINTS": (T_SAND, None),
    # water
    "MB_POND_WATER": (T_POND, PASSABLE),
    "MB_SEMI_DEEP_WATER": (T_SEA, PASSABLE),
    "MB_DEEP_WATER": (T_SEA, PASSABLE),
    "MB_OCEAN_WATER": (T_SEA, PASSABLE),
    "MB_INTERIOR_DEEP_WATER": (T_SEA, PASSABLE),
    "MB_SOOTOPOLIS_DEEP_WATER": (T_SEA, PASSABLE),
    "MB_NO_SURFACING": (T_SEA, PASSABLE),
    "MB_WATERFALL": (T_WATERFALL, PASSABLE),
    "MB_SHALLOW_WATER": (T_PLAIN, None),
    "MB_PUDDLE": (T_PLAIN, None),
    "MB_HOT_SPRINGS": (T_PLAIN, None),
    # deep-water dive spots keep sea type; dive itself is future mechanics work
    "MB_SPLIT_WATER": (T_SEA, PASSABLE),
    # ocean currents: Gen 4 has no current mechanic, so they surf as open sea
    # (Route 132-134 becomes freely navigable; gameplay redesign tracked in
    # the manifest notes)
    "MB_EASTWARD_CURRENT": (T_SEA, PASSABLE),
    "MB_WESTWARD_CURRENT": (T_SEA, PASSABLE),
    "MB_NORTHWARD_CURRENT": (T_SEA, PASSABLE),
    "MB_SOUTHWARD_CURRENT": (T_SEA, PASSABLE),
    "MB_SEAWEED": (T_SEA, PASSABLE),
    "MB_SEAWEED_NO_SURFACING": (T_SEA, PASSABLE),
    # walkable specials that keep plain type but must stay passable
    "MB_PACIFIDLOG_VERTICAL_LOG_TOP": (T_PLAIN, PASSABLE),
    "MB_PACIFIDLOG_VERTICAL_LOG_BOTTOM": (T_PLAIN, PASSABLE),
    "MB_PACIFIDLOG_HORIZONTAL_LOG_LEFT": (T_PLAIN, PASSABLE),
    "MB_PACIFIDLOG_HORIZONTAL_LOG_RIGHT": (T_PLAIN, PASSABLE),
    "MB_FORTREE_BRIDGE": (T_PLAIN, PASSABLE),
    "MB_BRIDGE_OVER_OCEAN": (T_PLAIN, PASSABLE),
    # sand / ice
    "MB_SAND": (T_SAND, None),
    "MB_DEEP_SAND": (T_SAND, None),
    "MB_ICE": (T_ICE, None),
    "MB_THIN_ICE": (T_ICE, None),
    "MB_CRACKED_ICE": (T_ICE, None),
    # ledges: Gen 4 hop-over tiles are typed and blocked
    "MB_JUMP_EAST": (T_JUMP_E, BLOCKED),
    "MB_JUMP_WEST": (T_JUMP_W, BLOCKED),
    "MB_JUMP_NORTH": (T_JUMP_N, BLOCKED),
    "MB_JUMP_SOUTH": (T_JUMP_S, BLOCKED),
    "MB_JUMP_NORTHEAST": (T_JUMP_N, BLOCKED),
    "MB_JUMP_NORTHWEST": (T_JUMP_N, BLOCKED),
    "MB_JUMP_SOUTHEAST": (T_JUMP_S, BLOCKED),
    "MB_JUMP_SOUTHWEST": (T_JUMP_S, BLOCKED),
    # warp surfaces
    "MB_ANIMATED_DOOR": (T_DOOR, None),
    "MB_NON_ANIMATED_DOOR": (T_STAIRS, None),
    "MB_LADDER": (T_STAIRS, None),
    "MB_UP_ESCALATOR": (T_STAIRS, None),
    "MB_DOWN_ESCALATOR": (T_STAIRS, None),
    "MB_DEEP_SOUTH_WARP": (T_STAIRS, None),
}

# behaviors that are always solid regardless of grid collision
_FORCE_BLOCKED_PREFIXES = ("MB_IMPASSABLE",)


def convert(mb_name: str, gba_collision: int) -> tuple[int, int]:
    """(gen4_type, gen4_collision) for one Gen-3 cell."""
    t, forced = _TABLE.get(mb_name, (T_PLAIN, None))
    if any(mb_name.startswith(p) for p in _FORCE_BLOCKED_PREFIXES):
        return t, BLOCKED
    if forced is not None:
        return t, forced
    return t, (BLOCKED if gba_collision else PASSABLE)
