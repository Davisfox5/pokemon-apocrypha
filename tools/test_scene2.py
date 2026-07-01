#!/usr/bin/env python3
"""Drive Scene 2 (Cherrygrove first-meeting) on a fresh current-ROM save and snapshot
each beat: trigger staging, mid-dialogue/fly-off, and the face-to-face/naming, so the
positions, facings, and flow can be inspected for problems."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from emu_harness import Emu
import emu_ram as R
import rig
SCRATCH = "/private/tmp/claude-501/-Users-davisfox-Documents-GitHub-the-omni-hack/3fdef984-9a20-4cf3-8daf-48eed0d89062/scratchpad"

e = Emu()
rig.new_game_to_house_free(e)
R.set_var(e, R.VAR_SCENE_PLAYERS_HOUSE_1F, 4); e.wait(8)   # past the door gate
R.teleport(e, 3, 10); e.wait(8)
for _ in range(3):
    e.press("DOWN", hold=18, after=6)
    if R.loc(e)["mapId"] == 67:
        break
    e.wait(20)

def snap(tag):
    o = R.objects(e); px = next((x for x in o if x["id"] == 255), None)
    near = [(x["sprite"], x["x"], x["z"], x["dirname"]) for x in o if x["id"] != 255
            and px and abs(x["x"] - px["x"]) <= 14 and abs(x["z"] - px["z"]) <= 14]
    print(tag, "| player", (px["x"], px["z"], px["dirname"]) if px else "?",
          "| cg_ow", R.var(e, 0x4073), "| state", e.state())
    print("   near:", near)
    e.emu.screenshot().save(SCRATCH + f"/s2_{tag}.png")

print("entered Cherrygrove map", R.loc(e)["mapId"])
for _ in range(8):
    e.press("RIGHT", hold=16, after=10)   # walk toward the vantage -> trips Scene 2
snap("trigger")
for _ in range(60):
    e.press("A", hold=5, after=24)
snap("mid")
for _ in range(60):
    e.press("A", hold=5, after=24)
snap("end")
