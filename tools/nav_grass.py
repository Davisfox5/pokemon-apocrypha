#!/usr/bin/env python3
"""Walk the short Route-30 segment from just-north-of-the-bridge up into the
tall grass, letting the rig's greedy pathfinder stream chunks as it goes
(teleport alone leaves the far chunks unloaded -> black screen)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from emu_harness import Emu
import emu_ram as R
import rig

STATE = sys.argv[1]
TX, TZ = int(sys.argv[2]), int(sys.argv[3])

e = Emu()
e.wait(4)
e.loadstate(STATE)
e.wait(4)
# Drop onto a known-rendered, walkable tile north of the bridge, then walk.
R.teleport(e, 550, 355)
e.wait(20)
res = rig.nav_to(e, TX, TZ, max_steps=120)
l = R.loc(e)
px = next((o for o in R.objects(e) if o["id"] == 255), None)
xz = (px["x"], px["z"]) if px else (l["x"], l["z"])
print(f"nav={res} map={l['mapId']} player={xz}")
print("objs:", [(o["sprite"], o["x"], o["z"]) for o in R.objects(e) if o["id"] != 255])
e.savestate(STATE)
e.emu.screenshot().save(STATE[:-4] + ".png")
