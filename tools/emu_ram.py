#!/usr/bin/env python3
"""RAM introspection for the Apocrypha self-test rig (HGSS, py-desmume).

Reads live game state directly from memory so scene tests assert on ground truth
(scene var, current map, position) instead of guessing from pixels. Offsets were
derived by disassembling the save getters in build/heartgold.us/main.elf:

  SaveData*           = *(0x021D2308)                       (sSaveDataPtr, .bss)
  SaveArray_Get(sd,i) = sd + 0x10 + *(sd + i*16 + 0x2301C)
  VarsFlags block     = SaveArray block id 4  -> vars are u16[] at its start
  LocalFieldData block= SaveArray block id 5  -> currentPosition Location at +0
  Location            = { s32 mapId; s32 warpId; s32 x; s32 y(=worldZ); s32 dir }
  var(id)             = u16 @ varsBlock + 2*(id - 0x4000)
"""

SAVEPTR        = 0x021D2308
DESC_TABLE_OFF = 0x2301C
VARS_BLOCK_ID  = 4
LFD_BLOCK_ID   = 5
VAR_BASE       = 0x4000

# --- useful constants (from include/constants/{vars,maps}.h) ---
VAR_SCENE_CHERRYGROVE_CITY_OW = 0x4073
VAR_SCENE_PLAYERS_HOUSE_1F    = 0x4106
MAP_PLAYER_HOUSE_1F = 63
MAP_PLAYER_HOUSE_2F = 64
MAP_CHERRYGROVE     = 67


def _m(emu):
    return emu.emu.memory.unsigned


def savedata(emu):
    return _m(emu).read_long(SAVEPTR)


def _block(emu, block_id):
    m = _m(emu)
    sd = m.read_long(SAVEPTR)
    return sd + 0x10 + m.read_long(sd + block_id * 16 + DESC_TABLE_OFF)


def var(emu, vid):
    """Read a script variable (0x4000-based) as u16."""
    return _m(emu).read_short(_block(emu, VARS_BLOCK_ID) + 2 * (vid - VAR_BASE))


def loc(emu):
    """Current saved Location (map id reliable; x/z update on warp/map-load)."""
    m = _m(emu); lfd = _block(emu, LFD_BLOCK_ID)
    return {
        "mapId": m.read_long(lfd),
        "warpId": m.read_long(lfd + 4),
        "x": m.read_long(lfd + 8),
        "z": m.read_long(lfd + 0xC),
        "dir": m.read_long(lfd + 0x10),
    }


def snapshot(emu, vids=(VAR_SCENE_PLAYERS_HOUSE_1F, VAR_SCENE_CHERRYGROVE_CITY_OW)):
    s = loc(emu)
    s["vars"] = {hex(v): var(emu, v) for v in vids}
    return s


def set_var(emu, vid, value):
    """Write a script variable (u16). With per-frame scene re-eval, poking a scene
    var makes its gated scene fire immediately -> instant scene-jump for testing."""
    addr = _block(emu, VARS_BLOCK_ID) + 2 * (vid - VAR_BASE)
    emu.emu.memory.write_short(addr, value)
