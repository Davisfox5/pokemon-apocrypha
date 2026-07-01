#!/usr/bin/env python3
"""cur_house -> door-exit Cherrygrove -> skip Scene 1 -> walk north into Route 30
-> walk up the path to the grass. Stops when a real dialogue box appears (the
catch firing, or a wild battle) -- ignores the headless 'black' bridge. Reports
whether the catch staged (rescue Kestra spr320 turns south) vs. a wild encounter."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from emu_harness import Emu
import emu_ram as R

SCRATCH = "/private/tmp/claude-501/-Users-davisfox-Documents-GitHub-the-omni-hack/3fdef984-9a20-4cf3-8daf-48eed0d89062/scratchpad"
CK = os.path.join(os.path.dirname(__file__), "checkpoints")
e = Emu(); e.wait(4)
e.loadstate(os.path.join(CK, "cur_house.dsv")); e.wait(4)

def st():
    l = R.loc(e)
    o = next((o for o in R.objects(e) if o["id"] == 255), None)
    return ((o["x"], o["z"]) if o else (l["x"], l["z"])), l["mapId"]

# door-exit
R.teleport(e, 3, 10); e.wait(8)
for _ in range(3):
    e.press("DOWN", hold=18, after=6)
    if R.loc(e)["mapId"] == 67:
        break
    e.wait(20)
R.set_var(e, 0x4073, 3); e.wait(4)

# greedy north until on Route 30 (map 34)
for _ in range(70):
    (px, pz), m = st()
    if m == 34:
        break
    e.press("UP", hold=16, after=10)
    (nx, nz), m = st()
    if m == 34 or (nx, nz) != (px, pz):
        continue
    e.press("LEFT" if nx > 550 else "RIGHT", hold=16, after=10)
print("entered R30 at", st())

# walk up the path toward the grass trigger; stop on a real box (catch/encounter),
# ignore the headless 'black' bridge. Steer toward x=551-552.
fired = None
for _ in range(90):
    (px, pz), m = st()
    if e.state() == "box":
        fired = (px, pz); break
    if pz <= 334:
        break
    e.press("UP", hold=16, after=10)
    (nx, nz), m = st()
    if e.state() == "box":
        fired = (nx, nz); break
    if (nx, nz) == (px, pz):  # blocked north -> sidestep toward the corridor
        e.press("LEFT" if nx > 551 else "RIGHT", hold=16, after=10)

e.wait(50)
(px, pz), m = st()
kes = [(o["x"], o["z"], o["dirname"]) for o in R.objects(e) if o["sprite"] == 320 and abs(o["z"] - 330) <= 4]
print("stopped at", (px, pz), "map", m, "| box@", fired, "| state", e.state())
print("rescue Kestra (spr320 near grass):", kes)
e.savestate(os.path.join(CK, "cur_r30.dsv"))
e.emu.screenshot().save(SCRATCH + "/play.png")
