#!/usr/bin/env python3
"""Chapter 1 / Scene 1 review driver.

Replays the game from a fresh boot through the house opening (O-1..O-3) and
Scene 1 (Silver in Cherrygrove), screenshotting every DISTINCT message box
(deduped by a hash of the box region) plus periodic field frames during
cutscene motion (auto-walks, camera pans, the Murkrow fly-off). Prints a
structured progress log + RAM assertions so the run can be audited.

Output PNGs + checkpoints go to OUT (passed as argv[1]).
"""
import os, sys, hashlib
sys.path.insert(0, os.path.dirname(__file__))
from emu_harness import Emu
import emu_ram as R
import rig

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

e = Emu()
shot_idx = 0

def save(tag):
    global shot_idx
    shot_idx += 1
    p = os.path.join(OUT, f"{shot_idx:03d}_{tag}.png")
    e.emu.screenshot().save(p)
    print("SHOT", p, flush=True)

def boxsig():
    # message box lives in the lower part of the TOP screen (y 144-190 of the
    # 256x384 stacked screenshot)
    img = e.emu.screenshot().convert('L').crop((8, 144, 248, 190)).resize((60, 12))
    return hashlib.md5(img.tobytes()).hexdigest()

def snapshot(label):
    l = R.loc(e)
    try:
        ow = R.var(e, R.VAR_SCENE_CHERRYGROVE_CITY_OW)
        hv = R.var(e, R.VAR_SCENE_PLAYERS_HOUSE_1F)
    except Exception:
        ow = hv = -1
    objs = R.objects(e)
    px = next((o for o in objs if o["id"] == 255), None)
    ppos = (px["x"], px["z"]) if px else (l["x"], l["z"])
    near = [f"spr{o['sprite']}@({o['x']},{o['z']}){o['dirname']}"
            for o in objs if o["id"] != 255
            and abs(o["x"] - ppos[0]) <= 14 and abs(o["z"] - ppos[1]) <= 14]
    print(f"STATE[{label}] map={l['mapId']} player={ppos} house={hv} cg_ow={ow} near={near}", flush=True)

def capture_until(var_id, target, prefix, cap=500, field_gap=110):
    """Mash A; screenshot every new stable message box + interval non-box frames."""
    seen = set()
    last_field = -10**9
    for i in range(cap):
        if R.var(e, var_id) >= target:
            print(f"DONE {prefix}: var reached {target} after {i} presses", flush=True)
            return True
        st = e.state()
        if st == 'box':
            sig = boxsig()
            # stabilize: wait for the text to finish rendering
            for _ in range(12):
                e.wait(10)
                s2 = boxsig()
                if s2 == sig:
                    break
                sig = s2
            if sig not in seen:
                seen.add(sig)
                save(f"{prefix}_box")
        else:
            if e.frame - last_field > field_gap:
                last_field = e.frame
                save(f"{prefix}_{st}")
        e.press('A', hold=5, after=16)
    print(f"FAIL {prefix}: var never reached {target} in {cap} presses", flush=True)
    return False

# ---------- O-1: cold open ----------
print("PHASE O-1 cold open", flush=True)
e.wait(300)
rig.gender_select(e)
ok = capture_until(R.VAR_SCENE_PLAYERS_HOUSE_1F, 1, "o1")
e.wait(40)
save("o1_end_free")
snapshot("after O-1")
if not ok:
    sys.exit(1)
e.savestate(os.path.join(OUT, "ck_after_o1.dsv"))

# ---------- O-2: upstairs PC (stairs are rig-hostile; try, then fall back) ----------
print("PHASE O-2 stairs attempt", flush=True)
# stairs live at (3,3) 1F wait, approach from below and walk UP into them
rig.nav_to(e, 3, 4, max_steps=40)
snapshot("at stairs approach")
up_ok = rig.go_through_warp(e, "UP")
print("STAIRS WARP FIRED:", up_ok, flush=True)
if up_ok:
    save("o2_upstairs")
    snapshot("2F")
    # PC location on 2F is unknown to the rig; just record we're here. Don't
    # wander — go back down so the run stays deterministic.
    rig.go_through_warp(e, "DOWN")
    save("o2_back_down")
if R.var(e, R.VAR_SCENE_PLAYERS_HOUSE_1F) < 2:
    print("O-2 NOT verifiable by rig; SETVAR house=2 to arm O-3", flush=True)
    R.set_var(e, R.VAR_SCENE_PLAYERS_HOUSE_1F, 2)
    e.wait(8)

# ---------- O-3: Pokégear hand-off (fires on HOUSE_1F==2 on 1F) ----------
print("PHASE O-3 pokegear hand-off", flush=True)
capture_until(R.VAR_SCENE_PLAYERS_HOUSE_1F, 4, "o3")
e.wait(40)
save("o3_end_free")
snapshot("after O-3")
e.savestate(os.path.join(OUT, "ck_after_o3.dsv"))

# ---------- exit house ----------
print("PHASE exit house", flush=True)
rig.nav_to(e, 4, 10, max_steps=60)
snapshot("beside door")
save("exit_beside_door")
rig.nav_to(e, 3, 10, max_steps=6)
door_ok = rig.go_through_warp(e, "DOWN")
print("DOOR WARP FIRED:", door_ok, flush=True)
e.wait(60)
snapshot("outside")
save("exit_outside")
if R.loc(e)["mapId"] != 67:
    print("FAIL: not on Cherrygrove map after door", flush=True)
    sys.exit(2)
e.savestate(os.path.join(OUT, "ck_pre_s1.dsv"))

# ---------- Scene 1: any step trips the 10x7 coord trigger ----------
print("PHASE Scene 1", flush=True)
e.press("DOWN", hold=16, after=10)
capture_until(R.VAR_SCENE_CHERRYGROVE_CITY_OW, 1, "s1", cap=600)
e.wait(60)
save("s1_end_free")
snapshot("after Scene 1")
e.savestate(os.path.join(OUT, "ck_post_s1.dsv"))
print("ALL PHASES COMPLETE", flush=True)
