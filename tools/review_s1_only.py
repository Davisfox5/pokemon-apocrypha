#!/usr/bin/env python3
"""Scene 1 capture, from ck_after_o3.dsv (inside house, HOUSE_1F==4).
Exits the house so the T21 event table loads fresh from the rebuilt ROM, then
observes exactly where the Scene-1 coord trigger fires and captures every beat."""
import os, sys, hashlib
sys.path.insert(0, os.path.dirname(__file__))
from emu_harness import Emu
import emu_ram as R
import rig

OUT = sys.argv[1]
e = Emu()
e.wait(4)
e.loadstate(os.path.join(OUT, "ck_after_o3.dsv"))
e.wait(120)

shot_idx = 100
def ppos():
    objs = R.objects(e)
    px = next((o for o in objs if o["id"] == 255), None)
    l = R.loc(e)
    return (px["x"], px["z"]) if px else (l["x"], l["z"])

def save(tag):
    global shot_idx
    shot_idx += 1
    p = os.path.join(OUT, f"{shot_idx:03d}_{tag}.png")
    e.emu.screenshot().save(p)
    print(f"SHOT {p} player={ppos()} cg_ow={R.var(e, R.VAR_SCENE_CHERRYGROVE_CITY_OW)}", flush=True)

def boxsig():
    img = e.emu.screenshot().convert('L').crop((8, 144, 248, 190)).resize((60, 12))
    return hashlib.md5(img.tobytes()).hexdigest()

def snapshot(label):
    l = R.loc(e)
    ow = R.var(e, R.VAR_SCENE_CHERRYGROVE_CITY_OW)
    objs = R.objects(e)
    p = ppos()
    near = [f"spr{o['sprite']}@({o['x']},{o['z']}){o['dirname']}"
            for o in objs if o["id"] != 255
            and abs(o["x"] - p[0]) <= 14 and abs(o["z"] - p[1]) <= 14]
    print(f"STATE[{label}] map={l['mapId']} player={p} cg_ow={ow} near={near}", flush=True)

# exit the house (door at (3,10) 1F; approach from (4,10) then DOWN)
snapshot("in house")
rig.nav_to(e, 4, 10, max_steps=60)
rig.nav_to(e, 3, 10, max_steps=6)
door_ok = rig.go_through_warp(e, "DOWN")
print("DOOR WARP FIRED:", door_ok, flush=True)
e.wait(90)
snapshot("outside door")
save("s1_at_door")

# does the trigger fire STANDING at the arrival tile? wait and watch
for i in range(6):
    e.wait(30)
    if e.state() != 'field' or R.var(e, R.VAR_SCENE_CHERRYGROVE_CITY_OW) >= 1:
        print(f"TRIGGER fired STANDING at door after {i*30} extra frames", flush=True)
        break
else:
    print("no standing fire at door; stepping DOWN", flush=True)
    for _ in range(4):
        e.press("DOWN", hold=16, after=14)
        e.wait(10)
        print(f"stepped: player={ppos()} state={e.state()}", flush=True)
        if e.state() != 'field':
            break

snapshot("trigger moment")
seen = set()
last_field = -10**9
for i in range(400):
    if R.var(e, R.VAR_SCENE_CHERRYGROVE_CITY_OW) >= 1:
        print(f"DONE: cg_ow==1 after {i} presses", flush=True)
        break
    st = e.state()
    if st == 'box':
        sig = boxsig()
        for _ in range(12):
            e.wait(10)
            s2 = boxsig()
            if s2 == sig:
                break
            sig = s2
        if sig not in seen:
            seen.add(sig)
            save("s1_box")
    else:
        if e.frame - last_field > 140:
            last_field = e.frame
            save(f"s1_{st}")
    e.press('A', hold=5, after=16)
else:
    print("FAIL: cg_ow never hit 1", flush=True)

e.wait(60)
save("s1_end_free")
snapshot("after S1")
e.savestate(os.path.join(OUT, "ck_post_s1.dsv"))
print("S1 CAPTURE COMPLETE", flush=True)
