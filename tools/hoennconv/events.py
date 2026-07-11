#!/usr/bin/env python3
"""Convert pokeemerald map.json events -> HGSS zone_event JSON.

Target schema is the one jsonproc compiles in the HGSS decomp
(files/fielddata/eventdata/zone_event/*.json):
  objects: id, spriteId, movement, type, eventFlag, scriptId,
           facingDirection, param0..2, xRange, yRange, x, z, y
  warps:   x, z, header, anchor, y
  coords:  scriptId, x, z, w, h, y, val, var
  bgs:     scriptId, type, x, z, y, dir

Coordinates: HGSS overworld events use *matrix-global* tile coords (the whole
region is one matrix), so converted events are emitted in the stitched-canvas
frame. Interiors (own matrix each) stay in local coords.

Scripts do not auto-convert (Gen-3 bytecode vs Gen-4 scr_seq are different
VMs); scriptId keeps the Gen-3 label as a string so the intent is preserved
and grep-able, and the manifest lists every one as pending script authoring.
"""

from __future__ import annotations

# Gen-3 OBJ_EVENT_GFX_* -> HGSS SPRITE_* (include/constants/sprites.h).
# Deliberately archetype-level: named story NPCs get proper casting later.
SPRITE_MAP = {
    "OBJ_EVENT_GFX_BOY_1": "SPRITE_BOY1",
    "OBJ_EVENT_GFX_BOY_2": "SPRITE_BOY2",
    "OBJ_EVENT_GFX_BOY_3": "SPRITE_BOY3",
    "OBJ_EVENT_GFX_GIRL_1": "SPRITE_GIRL1",
    "OBJ_EVENT_GFX_GIRL_2": "SPRITE_GIRL2",
    "OBJ_EVENT_GFX_GIRL_3": "SPRITE_GIRL3",
    "OBJ_EVENT_GFX_LITTLE_BOY": "SPRITE_BABYBOY1",
    "OBJ_EVENT_GFX_LITTLE_GIRL": "SPRITE_BABYGIRL1",
    "OBJ_EVENT_GFX_MAN_1": "SPRITE_MAN1",
    "OBJ_EVENT_GFX_MAN_2": "SPRITE_MAN2",
    "OBJ_EVENT_GFX_MAN_3": "SPRITE_MAN3",
    "OBJ_EVENT_GFX_MAN_4": "SPRITE_MIDDLEMAN1",
    "OBJ_EVENT_GFX_MAN_5": "SPRITE_MIDDLEMAN1",
    "OBJ_EVENT_GFX_WOMAN_1": "SPRITE_WOMAN1",
    "OBJ_EVENT_GFX_WOMAN_2": "SPRITE_WOMAN2",
    "OBJ_EVENT_GFX_WOMAN_3": "SPRITE_WOMAN3",
    "OBJ_EVENT_GFX_WOMAN_4": "SPRITE_MIDDLEWOMAN1",
    "OBJ_EVENT_GFX_WOMAN_5": "SPRITE_MIDDLEWOMAN1",
    "OBJ_EVENT_GFX_OLD_MAN": "SPRITE_OLDMAN1",
    "OBJ_EVENT_GFX_OLD_WOMAN": "SPRITE_OLDWOMAN1",
    "OBJ_EVENT_GFX_FAT_MAN": "SPRITE_BIGMAN",
    "OBJ_EVENT_GFX_YOUNGSTER": "SPRITE_BOY2",
    "OBJ_EVENT_GFX_LASS": "SPRITE_GIRL2",
    "OBJ_EVENT_GFX_TWIN": "SPRITE_BABYGIRL1",
    "OBJ_EVENT_GFX_CAMPER": "SPRITE_BOY3",
    "OBJ_EVENT_GFX_PICNICKER": "SPRITE_GIRL3",
    "OBJ_EVENT_GFX_HIKER": "SPRITE_MOUNT",
    "OBJ_EVENT_GFX_FISHERMAN": "SPRITE_FISHING",
    "OBJ_EVENT_GFX_SAILOR": "SPRITE_SEAMAN",
    "OBJ_EVENT_GFX_SCIENTIST_1": "SPRITE_DOCTOR",
    "OBJ_EVENT_GFX_SCIENTIST_2": "SPRITE_DOCTOR",
    "OBJ_EVENT_GFX_ITEM_BALL": "SPRITE_MONSTARBALL",
    "OBJ_EVENT_GFX_CUTTABLE_TREE": "SPRITE_TREE",
    "OBJ_EVENT_GFX_BREAKABLE_ROCK": "SPRITE_BREAKROCK",
}
SPRITE_FALLBACK = "SPRITE_MAN1"

# MOVEMENT_TYPE_* family -> (hgss movement, facing, xRange, yRange)
# hgss movement values per the verified recipes in tools/mapeditor/behavior.py:
# 0 stand, 3 wander, 5 pace left/right, 7 pace up/down.
_FACING = {"UP": 0, "DOWN": 1, "LEFT": 2, "RIGHT": 3}


def _movement(g3: str, rx: int, ry: int) -> tuple[int, int, int, int]:
    if "WANDER" in g3:
        return 3, 1, max(rx, 1), max(ry, 1)
    if "WALK_LEFT_AND_RIGHT" in g3 or "PACE_LEFT_AND_RIGHT" in g3:
        return 5, 1, max(rx, 1), 0
    if "WALK_UP_AND_DOWN" in g3 or "PACE_UP_AND_DOWN" in g3:
        return 7, 1, 0, max(ry, 1)
    face = 1
    for k, v in _FACING.items():
        if g3.endswith("FACE_" + k) or g3.endswith(k):
            face = v
            break
    return 0, face, 0, 0


def convert_objects(map_tag: str, objs: list[dict], ox: int, oy: int,
                    notes: list[str]) -> list[dict]:
    out = []
    for o in objs:
        gfx = o.get("graphics_id", "")
        sprite = SPRITE_MAP.get(gfx)
        if sprite is None:
            sprite = SPRITE_FALLBACK
            notes.append(f"{map_tag}: {o.get('local_id')} gfx {gfx} -> fallback")
        mv, face, xr, yr = _movement(o.get("movement_type", ""),
                                     int(o.get("movement_range_x") or 0),
                                     int(o.get("movement_range_y") or 0))
        out.append({
            "id": f"obj_{map_tag}_{str(o.get('local_id', 'x')).removeprefix('LOCALID_').lower()}",
            "spriteId": sprite,
            "movement": mv,
            "type": 0,
            "eventFlag": o.get("flag", "0") if str(o.get("flag", "0")) != "0" else "FLAG_NOTHING",
            "scriptId": str(o.get("script") or 0),
            "facingDirection": face,
            "param0": 0, "param1": 0, "param2": 0,
            "xRange": xr, "yRange": yr,
            "x": ox + int(o["x"]), "z": oy + int(o["y"]), "y": 0,
        })
    return out


def convert_warps(warps: list[dict], ox: int, oy: int) -> list[dict]:
    return [{
        "x": ox + int(w["x"]), "z": oy + int(w["y"]),
        # dest map keeps its Gen-3 id as a placeholder header name; the real
        # MAP_HOENN_* header ids are assigned when headers are generated.
        "header": w["dest_map"],
        "anchor": int(str(w.get("dest_warp_id", 0)) or 0),
        "y": 0,
    } for w in warps]


def convert_coords(coords: list[dict], ox: int, oy: int) -> list[dict]:
    return [{
        "scriptId": str(c.get("script") or 0),
        "x": ox + int(c["x"]), "z": oy + int(c["y"]),
        "w": 1, "h": 1, "y": 0,
        "val": int(str(c.get("var_value", 0)) or 0),
        "var": c.get("var", "VAR_TEMP_x4000"),
    } for c in coords]


def convert_bgs(bgs: list[dict], ox: int, oy: int) -> list[dict]:
    out = []
    for b in bgs:
        hidden = b.get("type") == "hidden_item" or "item" in str(b.get("type", ""))
        out.append({
            "scriptId": (f"std_hiddenitem({b.get('item')})" if hidden
                         else str(b.get("script") or 0)),
            "type": 2 if hidden else 1,
            "x": ox + int(b["x"]), "z": oy + int(b["y"]), "y": 0,
            "dir": 4,
        })
    return out
