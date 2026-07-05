#!/usr/bin/env python3
"""RAM introspection for the Apocrypha self-test rig (HGSS, py-desmume).

Reads live game state directly from memory so scene tests assert on ground truth
(scene var, current map, position) instead of guessing from pixels. Offsets were
derived by disassembling the save getters in build/heartgold.us/main.elf:

  SaveData*           = *(sSaveDataPtr, .bss)   [auto-derived from main.elf]
  SaveArray_Get(sd,i) = sd + 0x10 + *(sd + i*16 + 0x2301C)
  VarsFlags block     = SaveArray block id 4  -> vars are u16[] at its start
  LocalFieldData block= SaveArray block id 5  -> currentPosition Location at +0
  Location            = { s32 mapId; s32 warpId; s32 x; s32 y(=worldZ); s32 dir }
  var(id)             = u16 @ varsBlock + 2*(id - 0x4000)
"""

# .bss addresses SHIFT whenever arm9 code changes size — a rebuilt ROM under the
# old constants reads garbage (mapId in the billions / objects()==[]). Re-derive
# from the freshly-linked main.elf at import; the literals are only a fallback
# for when the elf/nm is unavailable. (Last manual values: 2026-07-02 build.)
SAVEPTR        = 0x021D2328
FIELDSYS_PTR   = 0x021D4258

def _derive_bss_ptrs():
    global SAVEPTR, FIELDSYS_PTR
    import os, re, subprocess
    elf = os.path.join(os.path.dirname(__file__), "..", "disasm", "pokeheartgold",
                       "build", "heartgold.us", "main.elf")
    if not os.path.isfile(elf):
        return
    try:
        out = subprocess.run(["nm", elf], capture_output=True, text=True,
                             timeout=30).stdout
        m = re.search(r"^([0-9a-f]+) . sSaveDataPtr$", out, re.M)
        f = re.search(r"^([0-9a-f]+) . sFieldSysPtr$", out, re.M)
        if m and f:
            SAVEPTR = int(m.group(1), 16)
            FIELDSYS_PTR = int(f.group(1), 16)
    except Exception:
        pass

_derive_bss_ptrs()

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


# --- Story/event flags (same SaveVarsFlags block: u16 vars[0x170] then u8 flags[]) ---
# save_vars_flags.c: flag bit lives at flags[flagId/8], bit (flagId&7). NUM_VARS=0x170.
# An ObjectEvent spawns only if its eventFlag is CLEAR (map_object.c:257), so clearing a
# FLAG_HIDE_* reveals that NPC on the next map load.
FLAGS_OFF = 0x170 * 2
TEMP_FLAG_BASE = 0x4000

def flag_check(emu, fid):
    """1/0 for a regular story flag, or None for FLAG_NOTHING(0)/temp flags(>=0x4000)."""
    if not fid or fid >= TEMP_FLAG_BASE:
        return None
    a = _block(emu, VARS_BLOCK_ID) + FLAGS_OFF + (fid // 8)
    return (_m(emu).read_byte(a) >> (fid & 7)) & 1

def flag_write(emu, fid, value):
    """Set/clear a regular story flag. Returns False for non-persistent flag ids."""
    if not fid or fid >= TEMP_FLAG_BASE:
        return False
    a = _block(emu, VARS_BLOCK_ID) + FLAGS_OFF + (fid // 8)
    b = _m(emu).read_byte(a)
    b = (b | (1 << (fid & 7))) if value else (b & ~(1 << (fid & 7)))
    emu.emu.memory.write_byte(a, b & 0xFF)
    return True


# --- Live map-object oracle (the NPCs, not just the player) -------------------
# sFieldSysPtr(.bss) -> FieldSystem -> MapObjectManager -> objects[] (LocalMapObject)
# (FIELDSYS_PTR defined/derived above next to SAVEPTR)
FS_MAPOBJMAN    = 0x3C
MOM_COUNT       = 0x04
MOM_OBJECTS     = 0x124
LMO_SIZE        = 0x12C
LMO_FLAGS=0x00; LMO_ID=0x08; LMO_SPRITE=0x10; LMO_FACING=0x28; LMO_X=0x64; LMO_Z=0x6C
DIRNAME = {0:"N",1:"S",2:"W",3:"E"}

def objects(emu):
    """Every ACTIVE map object: {id, sprite, x, z, dir, dirname}. Ground truth for
    NPC placement/facing/existence (an object missing here = it despawned)."""
    m = _m(emu)
    fs = m.read_long(FIELDSYS_PTR)
    if not fs: return []
    man = m.read_long(fs + FS_MAPOBJMAN)
    if not man: return []
    count = m.read_long(man + MOM_COUNT)
    arr = m.read_long(man + MOM_OBJECTS)
    if not arr or count > 256: return []
    out = []
    for i in range(count):
        o = arr + i * LMO_SIZE
        if not (m.read_long(o + LMO_FLAGS) & 1):  # MAPOBJECTFLAG_ACTIVE
            continue
        d = m.read_long(o + LMO_FACING)
        out.append({"id": m.read_long(o + LMO_ID), "sprite": m.read_long(o + LMO_SPRITE),
                    "x": m.read_long(o + LMO_X), "z": m.read_long(o + LMO_Z),
                    "dir": d, "dirname": DIRNAME.get(d, str(d))})
    return out


def player_obj_addr(emu):
    m=_m(emu); fs=m.read_long(FIELDSYS_PTR); 
    if not fs: return 0
    man=m.read_long(fs+FS_MAPOBJMAN)
    if not man: return 0
    count=m.read_long(man+MOM_COUNT); arr=m.read_long(man+MOM_OBJECTS)
    for i in range(count):
        o=arr+i*LMO_SIZE
        if (m.read_long(o+LMO_FLAGS)&1) and m.read_long(o+LMO_ID)==255: return o
    return 0

def object_entries(emu):
    """Like objects() but each item also carries `addr` (its LocalMapObject base),
    so callers can WRITE the object (the live map editor drags NPCs this way)."""
    m = _m(emu)
    fs = m.read_long(FIELDSYS_PTR)
    if not fs: return []
    man = m.read_long(fs + FS_MAPOBJMAN)
    if not man: return []
    count = m.read_long(man + MOM_COUNT)
    arr = m.read_long(man + MOM_OBJECTS)
    if not arr or count > 256: return []
    out = []
    for i in range(count):
        o = arr + i * LMO_SIZE
        if not (m.read_long(o + LMO_FLAGS) & 1):
            continue
        d = m.read_long(o + LMO_FACING)
        out.append({"addr": o, "id": m.read_long(o + LMO_ID),
                    "sprite": m.read_long(o + LMO_SPRITE),
                    "x": m.read_long(o + LMO_X), "z": m.read_long(o + LMO_Z),
                    "dir": d, "dirname": DIRNAME.get(d, str(d))})
    return out


def move_object(emu, addr, tx, tz):
    """Hard-set any live map object (by its LMO addr) to tile (tx,tz): grid +
    previous + world position vector ((tile<<16)+0x8000). Generalized teleport."""
    if not addr:
        return False
    def w32(a, v):
        v &= 0xffffffff
        emu.emu.memory.write_short(a, v & 0xffff)
        emu.emu.memory.write_short(a + 2, (v >> 16) & 0xffff)
    wx = (tx << 16) + 0x8000; wz = (tz << 16) + 0x8000
    w32(addr + 0x64, tx); w32(addr + 0x6C, tz)   # current X/Z
    w32(addr + 0x58, tx); w32(addr + 0x60, tz)   # previous X/Z
    w32(addr + 0x70, wx); w32(addr + 0x78, wz)   # posVector X/Z
    return True


def teleport(emu, tx, tz):
    """Hard-set the live player object to tile (tx,tz). Reliable scene-jump."""
    return move_object(emu, player_obj_addr(emu), tx, tz)


# --- movement pin (live drag) -------------------------------------------------
# MAPOBJECTFLAG_MOVEMENT_PAUSED = bit6 of flags @ +0x00 (map_object.h). When set,
# the movement AI (sub_0205F12C -> ov01_021F92A0) skips all walking, so a poked
# tile position STICKS instead of the NPC wandering back. Lives in the low flags
# byte alongside ACTIVE(bit0), so a byte read/write is enough.
LMO_FLAG_PAUSED = 0x40

def pin_object(emu, addr, pinned=True):
    """Freeze/unfreeze a live map object's movement so a dragged tile sticks."""
    if not addr:
        return False
    m = _m(emu)
    b = m.read_byte(addr + LMO_FLAGS)
    b = (b | LMO_FLAG_PAUSED) if pinned else (b & ~LMO_FLAG_PAUSED)
    emu.emu.memory.write_byte(addr + LMO_FLAGS, b & 0xFF)
    return True

def is_pinned(emu, addr):
    return bool(addr) and bool(_m(emu).read_byte(addr + LMO_FLAGS) & LMO_FLAG_PAUSED)


# --- keep the .bss anchor pointers in sync with the CURRENT build ---
# SAVEPTR / FIELDSYS_PTR shift whenever C code is added/removed (they're .bss
# symbols). Stale values read garbage (map=0 / no objects) under a fresh ROM.
# Functions read these globals at call time, so overriding here is enough.
def _refresh_anchors():
    global SAVEPTR, FIELDSYS_PTR
    import subprocess, os.path
    elf = os.path.join(os.path.dirname(__file__), "..", "disasm", "pokeheartgold",
                       "build", "heartgold.us", "main.elf")
    if not os.path.exists(elf):
        return
    try:
        out = subprocess.run(["nm", elf], capture_output=True, text=True, timeout=60).stdout
    except Exception:
        return
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[2] == "sSaveDataPtr":
            SAVEPTR = int(parts[0], 16)
        elif len(parts) == 3 and parts[2] == "sFieldSysPtr":
            FIELDSYS_PTR = int(parts[0], 16)

_refresh_anchors()
