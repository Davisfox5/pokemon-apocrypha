#!/usr/bin/env python3
"""High-level self-test rig for Apocrypha (py-desmume + RAM oracle).

Provides reliable scene-driving primitives so I can verify a scene myself before
handing a build to the user:
  - advance_until_var: mash A (hold>=4 so presses register) until a scene var hits
    a target = the ground-truth "scene progressed" signal.
  - new_game_to_house_free: boot -> gender -> clear cold open -> player free.
  - checkpoint save/load: jump to a scene state in ~1s instead of replaying.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from emu_harness import Emu
import emu_ram as R

CKPT_DIR = os.path.join(os.path.dirname(__file__), "checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)


def advance_until_var(e, vid, target, cap=300, hold=5, after=16):
    """Press A until script var `vid` reaches `target`. Returns presses used, or -1."""
    for i in range(cap):
        if R.var(e, vid) >= target:
            return i
        e.press("A", hold=hold, after=after)
    return -1


def gender_select(e):
    """New game -> confirm gender (tap boy, tap YES)."""
    for _ in range(8):
        e.press("START", hold=4, after=40)
    e.press("A", hold=4, after=120)            # NEW GAME
    e.touch(57, 95, hold=5, after=20)          # boy sprite
    e.touch(195, 55, hold=5, after=30)         # YES


def new_game_to_house_free(e):
    """Boot a fresh game through the cold open to free-roam in the house.
    Returns presses used to clear the cold open (-1 if it never completed)."""
    e.wait(300)
    gender_select(e)
    return advance_until_var(e, R.VAR_SCENE_PLAYERS_HOUSE_1F, 1)


def ckpt_path(name):
    return os.path.join(CKPT_DIR, name + ".dsv")


def save_ckpt(e, name):
    e.savestate(ckpt_path(name)); return ckpt_path(name)


def load_ckpt(e, name):
    e.loadstate(ckpt_path(name))


if __name__ == "__main__":
    e = Emu()
    n = new_game_to_house_free(e)
    s = R.snapshot(e)
    print(f"cold open cleared in {n} presses; state={s}")
    if n >= 0:
        save_ckpt(e, "house_free")
        print("saved checkpoint: house_free.dsv  (map should be 63, HOUSE_1F var >=1)")
    else:
        e.shot("rig_coldopen_stuck")
        print("COLD OPEN DID NOT COMPLETE - see rig_coldopen_stuck.png")


def go_through_warp(e, direction, timeout=140):
    """Step into a warp and WAIT for the map id to actually change (warps fire with
    a transition delay; some doors need a second walk-through press)."""
    start = R.loc(e)["mapId"]
    for attempt in range(2):
        e.press(direction, hold=18, after=4)
        for _ in range(timeout):
            if R.loc(e)["mapId"] != start:
                e.wait(22)
                return True
            e.wait(4)
    return False


def walk_to(e, key, n):
    for _ in range(n):
        e.press(key, hold=16, after=12)


# Cherrygrove (map 67) warp tiles — stepping on these warps you off-map, so the
# navigator must route AROUND them when heading for an overworld coord trigger.
CHERRYGROVE_WARPS = {(564,391),(555,391),(547,399),(558,401),(567,405)}

DIRS = {"UP":(0,-1),"DOWN":(0,1),"LEFT":(-1,0),"RIGHT":(1,0)}


def nav_to(e, tx, tz, max_steps=120, avoid=None, path=None):
    """Greedy walk toward (tx,tz): dominant axis first, perpendicular escape when
    blocked, never stepping onto an `avoid` tile (e.g. warps). Stops early if a
    scene fires (state box/black). Returns a reason string. If `path` is a list,
    each newly-entered tile is appended to it (for choreography path capture)."""
    avoid = set(avoid or ())
    recent = []  # anti-oscillation memory of last few tiles
    def _rec():
        if path is not None:
            t = (R.loc(e)["x"], R.loc(e)["z"])
            if not path or path[-1] != t: path.append(t)
    _rec()
    for _ in range(max_steps):
        _rec()
        if e.state() in ("box","black"):
            return "scene"
        l = R.loc(e); x,z = l["x"], l["z"]
        if (x,z) == (tx,tz):
            return "arrived"
        dx,dz = tx-x, tz-z
        ax = ["LEFT" if dx<0 else "RIGHT"] if dx else []
        az = ["UP" if dz<0 else "DOWN"] if dz else []
        prefs = (ax+az) if abs(dx)>=abs(dz) else (az+ax)
        for k in ("UP","LEFT","RIGHT","DOWN"):
            if k not in prefs: prefs.append(k)
        moved = False
        for k in prefs:
            ddx,ddz = DIRS[k]
            nxt = (x+ddx, z+ddz)
            if nxt in avoid: continue
            if nxt in recent[-3:]: continue          # don't immediately backtrack
            e.press(k, hold=16, after=10)
            if e.state() in ("box","black"): return "scene"
            now = (R.loc(e)["x"], R.loc(e)["z"])
            if now != (x,z):
                recent.append((x,z)); moved = True; break
        if not moved:
            # allow a backtrack step to escape a dead end
            for k in prefs:
                ddx,ddz = DIRS[k]
                if (x+ddx,z+ddz) in avoid: continue
                e.press(k, hold=16, after=10)
                if e.state() in ("box","black"): return "scene"
                if (R.loc(e)["x"],R.loc(e)["z"]) != (x,z):
                    moved = True; break
            if not moved:
                return "stuck@(%d,%d)" % (x,z)
    return "maxsteps@(%d,%d)" % (R.loc(e)["x"], R.loc(e)["z"])


def trigger_coord(e, tx, tz, settle=8):
    """Walk onto a coord-trigger tile and make sure the scene actually fires
    (coord scripts fire on a STEP, and nav can arrive a frame early). Oscillate
    on/off the tile until state goes box/black, never stepping onto a warp tile.
    Returns True if a scene fired."""
    nav_to(e, tx, tz, avoid=CHERRYGROVE_WARPS)
    for _ in range(settle):
        if e.state() in ("box","black"): return True
        e.wait(10)
    for k in ("DOWN","UP","LEFT","RIGHT","UP","DOWN"):
        l = R.loc(e); nxt = (l["x"]+DIRS[k][0], l["z"]+DIRS[k][1])
        if nxt in CHERRYGROVE_WARPS: continue
        e.press(k, hold=16, after=12)
        if e.state() in ("box","black"): return True
    return e.state() in ("box","black")
