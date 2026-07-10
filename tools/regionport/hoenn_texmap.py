#!/usr/bin/env python3
"""hoenn_texmap.py - semantic classification of Emerald metatiles for the
Gen-4 re-skin (regionport v6).

Every imported tile occurrence gets a semantic CLASS; hoenn_ground.py turns
classes into Gen-4 donor textures + geometry. Precedence:
  1. behavior (metatile attribute low byte, matched by MB_* NAME so the
     numeric values come from the pokeemerald header, never hardcoded)
  2. explicit (owner_tileset, metatile_id) overrides curated from the
     contact sheets (scratchpad emerald_sheets/)
  3. color heuristic on the rendered 16x16 (walkable: grass/sand/pave/dirt;
     blocked: layer-1 = canopy -> tree, else cliff/tree/sea_edge by hue)
"""
import os
import re

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
EM = os.path.join(ROOT, "disasm", "pokeemerald")

# ---- behavior name -> class -------------------------------------------------
# Classes: grass grass_dark tallgrass ashgrass flowers sand road_dirt
# road_pave peak ledge cliff tree fence rock sea pond river waterfall
# sea_edge bridge building blocked_misc
_BEHAVIOR_CLASS = {
    "MB_TALL_GRASS": "tallgrass",
    "MB_LONG_GRASS": "tallgrass",
    "MB_LONG_GRASS_SOUTH_EDGE": "tallgrass",
    "MB_SHORT_GRASS": "grass",
    "MB_ASHGRASS": "ashgrass",
    "MB_FOOTPRINTS": "sand",
    "MB_SAND": "sand",
    "MB_DEEP_SAND": "sand",
    "MB_POND_WATER": "pond",
    "MB_INTERIOR_DEEP_WATER": "pond",
    "MB_DEEP_WATER": "sea",
    "MB_SOOTOPOLIS_DEEP_WATER": "sea",
    "MB_OCEAN_WATER": "sea",
    "MB_NO_SURFACING": "sea",
    "MB_SHALLOW_WATER": "pond",
    "MB_WATERFALL": "waterfall",
    "MB_SPLASHING_WATER": "pond",
    "MB_MOUNTAIN_TOP": "peak",
    "MB_SEAWEED": "sea",
    "MB_SEAWEED_NO_SURFACING": "sea",
    "MB_UNDERWATER_BLOCKED_ABOVE": "sea",
    "MB_ICE": "pond",
    "MB_THIN_ICE": "pond",
    "MB_CRACKED_ICE": "pond",
    "MB_HOT_SPRINGS": "pond",
    "MB_PUDDLE": "grass",
    "MB_MUDDY_SLOPE": "road_dirt",
    "MB_BUMPY_SLOPE": "road_dirt",
    "MB_ISOLATED_VERTICAL_RAIL": "road_pave",
    "MB_ISOLATED_HORIZONTAL_RAIL": "road_pave",
    "MB_VERTICAL_RAIL": "road_pave",
    "MB_HORIZONTAL_RAIL": "road_pave",
    "MB_PACIFIDLOG_VERTICAL_LOG_TOP": "bridge",
    "MB_PACIFIDLOG_VERTICAL_LOG_BOTTOM": "bridge",
    "MB_PACIFIDLOG_HORIZONTAL_LOG_LEFT": "bridge",
    "MB_PACIFIDLOG_HORIZONTAL_LOG_RIGHT": "bridge",
    "MB_FORTREE_BRIDGE": "bridge",
}
_BEHAVIOR_PREFIX_CLASS = [
    ("MB_JUMP_", "ledge"),
    ("MB_EASTWARD_CURRENT", "sea"),
    ("MB_WESTWARD_CURRENT", "sea"),
    ("MB_NORTHWARD_CURRENT", "sea"),
    ("MB_SOUTHWARD_CURRENT", "sea"),
    ("MB_WALK_", "grass"),
    ("MB_SLIDE_", "road_pave"),
    ("MB_CRACKED_FLOOR", "road_dirt"),
    ("MB_BRIDGE_OVER_", "bridge"),
    ("MB_ROUTE120_", "bridge"),
    ("MB_UNUSED_FOOTPRINTS", "sand"),
    ("MB_DEEP_ASH", "ashgrass"),
    ("MB_STAIRS_OUTSIDE_", "cliff"),
    ("MB_SHOAL_", "sand"),
]

# ---- curated (owner_tileset, metatile_id) overrides -------------------------
# From scratchpad emerald_sheets/emerald_{walkable,blocked}.png (2026-07-10).
# Keys use the short tileset name the sheets show ('general', 'slateport'...).
KIND_CLASS = {
    # -- general, walkable --
    ("general", 0x001): "grass",
    ("general", 0x002): "grass",
    ("general", 0x004): "flowers",
    ("general", 0x00E): "grass_dark",
    ("general", 0x00F): "grass_dark",
    ("general", 0x01C): "grass",
    ("general", 0x01D): "grass",
    ("general", 0x00D): "grass",
    ("general", 0x05E): "road_pave",   # pale plaza tile
    ("general", 0x05F): "road_pave",
    ("general", 0x0AF): "road_pave",   # gray steps
    ("general", 0x0CF): "road_pave",   # gray stairs/step strip
    ("general", 0x0D4): "road_pave",
    ("general", 0x101): "road_pave",
    ("general", 0x108): "road_pave",
    ("general", 0x109): "road_pave",
    ("general", 0x0F6): "grass",
    ("general", 0x01B): "grass",
    # sand family (tan)
    ("general", 0x114): "sand", ("general", 0x118): "sand",
    ("general", 0x119): "sand", ("general", 0x11A): "sand",
    ("general", 0x11B): "sand", ("general", 0x120): "sand",
    ("general", 0x121): "sand", ("general", 0x122): "sand",
    ("general", 0x128): "sand", ("general", 0x129): "sand",
    ("general", 0x12A): "sand", ("general", 0x12B): "sand",
    # pale-green grass family (routes)
    ("general", 0x1CE): "grass", ("general", 0x1CF): "grass",
    ("general", 0x1D0): "grass", ("general", 0x1D1): "grass",
    ("general", 0x1D2): "grass", ("general", 0x1D8): "grass",
    ("general", 0x1D9): "grass", ("general", 0x1DA): "grass",
    ("general", 0x1E0): "grass", ("general", 0x1E1): "grass",
    ("general", 0x1E2): "grass",
    ("general", 0x01E): "grass",
    ("general", 0x010): "grass_dark",
    ("general", 0x011): "grass_dark",
    ("general", 0x012): "grass_dark",
    ("general", 0x013): "grass_dark",
    ("general", 0x01A): "grass_dark",
    # -- general, blocked --
    # tree canopies / hedges
    ("general", 0x0C6): "tree", ("general", 0x0C7): "tree",
    ("general", 0x0C8): "tree", ("general", 0x0C9): "tree",
    ("general", 0x0CA): "tree", ("general", 0x0CB): "tree",
    ("general", 0x1D4): "tree", ("general", 0x1D5): "tree",
    ("general", 0x1DC): "tree", ("general", 0x1DD): "tree",
    ("general", 0x1E4): "tree", ("general", 0x1E5): "tree",
    ("general", 0x016): "tree", ("general", 0x017): "tree",
    ("general", 0x01F): "tree",
    # cliff faces (brown rock)
    ("general", 0x06B): "cliff", ("general", 0x06D): "cliff",
    ("general", 0x070): "cliff", ("general", 0x071): "cliff",
    ("general", 0x073): "cliff", ("general", 0x074): "cliff",
    ("general", 0x075): "cliff", ("general", 0x079): "cliff",
    ("general", 0x07B): "cliff", ("general", 0x07C): "cliff",
    ("general", 0x07D): "cliff", ("general", 0x088): "cliff",
    ("general", 0x089): "cliff", ("general", 0x091): "cliff",
    ("general", 0x0A9): "cliff", ("general", 0x08A): "cliff",
    ("general", 0x175): "cliff", ("general", 0x176): "cliff",
    ("general", 0x17A): "cliff", ("general", 0x17C): "cliff",
    ("general", 0x17D): "cliff", ("general", 0x17E): "cliff",
    ("general", 0x182): "cliff", ("general", 0x184): "cliff",
    # water/land boundary strips
    ("general", 0x150): "sea_edge", ("general", 0x151): "sea_edge",
    ("general", 0x158): "sea_edge", ("general", 0x159): "sea_edge",
    # -- towns --
    ("rustboro", 0x2BB): "road_pave",
    ("rustboro", 0x2C3): "road_pave",
    ("rustboro", 0x2F9): "road_pave",
    ("rustboro", 0x300): "road_pave",
    ("rustboro", 0x302): "road_pave",
    ("rustboro", 0x309): "road_pave",
    ("rustboro", 0x207): "road_pave",
    ("rustboro", 0x212): "blocked_misc",
    ("rustboro", 0x221): "road_pave",
    ("rustboro", 0x225): "road_pave",
    ("rustboro", 0x206): "road_pave",
    ("slateport", 0x202): "road_pave",
    ("slateport", 0x209): "road_pave",
    ("slateport", 0x210): "road_pave",
    ("slateport", 0x211): "road_pave",
    ("slateport", 0x212): "road_pave",
    ("slateport", 0x219): "road_pave",
    ("slateport", 0x277): "road_pave",
    ("slateport", 0x285): "road_pave",
    ("slateport", 0x2C1): "road_pave",
    ("slateport", 0x2E9): "blocked_misc",   # market stall stripes
    ("slateport", 0x2F1): "road_pave",
    ("slateport", 0x33C): "road_pave",
    ("mauville", 0x2C1): "road_pave",
    ("mauville", 0x2A7): "road_pave",
    ("mauville", 0x222): "grass",
    ("mauville", 0x213): "flowers",
    ("mauville", 0x20C): "flowers",
    ("mauville", 0x215): "flowers",
    ("mauville", 0x21E): "flowers",
    ("mauville", 0x20A): "flowers",
    ("mauville", 0x291): "flowers",
    ("mauville", 0x284): "road_pave",
    ("fallarbor", 0x218): "ashgrass",
    ("fallarbor", 0x279): "road_dirt",
    ("fallarbor", 0x269): "blocked_misc",   # brick
    ("fallarbor", 0x243): "blocked_misc",
    ("fallarbor", 0x293): "bridge",
    ("lilycove", 0x22B): "grass",
    ("lilycove", 0x233): "grass",
    ("lilycove", 0x23B): "grass",
    ("lilycove", 0x232): "road_pave",
    ("lilycove", 0x234): "road_pave",
    ("lilycove", 0x251): "blocked_misc",    # stall stripes
    ("ever_grande", 0x23D): "road_pave",    # brick walk
    ("ever_grande", 0x23C): "road_pave",
    ("ever_grande", 0x23A): "road_pave",
    ("ever_grande", 0x23E): "road_pave",
    ("fortree", 0x261): "grass",
    ("fortree", 0x214): "bridge",
    ("fortree", 0x21C): "bridge",
    ("fortree", 0x26C): "grass",
    ("fortree", 0x259): "bridge",
    ("fortree", 0x276): "grass",
    ("fortree", 0x206): "tree",
    ("fortree", 0x23A): "tree",
    ("mossdeep", 0x2A5): "road_pave",
    ("mossdeep", 0x31A): "grass",
    ("mossdeep", 0x31B): "grass",
    ("mossdeep", 0x35F): "grass",
    ("mossdeep", 0x379): "grass",
    ("dewford", 0x219): "grass_dark",
    ("dewford", 0x23A): "blocked_misc",
    ("dewford", 0x243): "grass_dark",
    ("lavaridge", 0x27B): "cliff",
}

# fallback hue buckets (avg RGB of the rendered metatile)
def _fallback_walkable(rgb):
    r, g, b = rgb
    mx = max(r, g, b)
    if g > r + 12 and g > b + 12:
        return "grass"
    if r > 150 and g > 120 and b < 120:
        return "sand"
    if mx > 140 and abs(r - g) < 24 and abs(g - b) < 24:
        return "road_pave"
    if r > g > b:
        return "road_dirt"
    if b > r and b > g:
        return "road_pave"
    return "grass"


def _fallback_blocked(rgb, layer):
    r, g, b = rgb
    if b > r + 20 and b > g:
        return "sea_edge"
    if g > r + 10 and g > b + 10:
        return "tree"
    if layer == 1:
        return "tree"          # drawn-over-player canopy
    if abs(r - g) < 20 and abs(g - b) < 20 and max(r, g, b) > 140:
        return "blocked_misc"  # pale = building-ish
    return "cliff"


_beh_values = None


def behavior_values():
    """{MB_* name: numeric value} parsed from the pokeemerald header."""
    global _beh_values
    if _beh_values is None:
        src = open(os.path.join(
            EM, "include/constants/metatile_behaviors.h")).read()
        _beh_values = {m.group(1): int(m.group(2), 0) for m in re.finditer(
            r"#define\s+(MB_\w+)\s+(0x[0-9A-Fa-f]+|\d+)", src)}
    return _beh_values


_beh_class = None


def class_of_behavior(beh):
    global _beh_class
    if _beh_class is None:
        _beh_class = {}
        for name, val in behavior_values().items():
            if name in _BEHAVIOR_CLASS:
                _beh_class[val] = _BEHAVIOR_CLASS[name]
            else:
                for pre, cls in _BEHAVIOR_PREFIX_CLASS:
                    if name.startswith(pre):
                        _beh_class[val] = cls
                        break
    return _beh_class.get(beh)


def classify(owner_ts, mt_id, beh, coll, layer, avg_rgb):
    """Semantic class for one metatile kind. owner_ts: short tileset name."""
    c = class_of_behavior(beh)
    if c is not None:
        return c
    c = KIND_CLASS.get((owner_ts, mt_id))
    if c is not None:
        return c
    if coll == 0:
        return _fallback_walkable(avg_rgb)
    return _fallback_blocked(avg_rgb, layer)
