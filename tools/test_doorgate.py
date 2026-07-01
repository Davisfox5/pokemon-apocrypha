#!/usr/bin/env python3
"""Test the house door gate: at var==1 (no Pokegear), stepping onto the door must
be blocked (Mom message, stay in the house, map stays 63) -- NOT warp out."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from emu_harness import Emu
import emu_ram as R
import rig
SCRATCH = "/private/tmp/claude-501/-Users-davisfox-Documents-GitHub-the-omni-hack/3fdef984-9a20-4cf3-8daf-48eed0d89062/scratchpad"

e = Emu()
rig.new_game_to_house_free(e)

def pos():
    o = next((o for o in R.objects(e) if o["id"] == 255), None)
    l = R.loc(e)
    return (o["x"], o["z"]) if o else (l["x"], l["z"])

print("1F free-roam at", pos(), "| house_var", R.var(e, R.VAR_SCENE_PLAYERS_HOUSE_1F))

# walk down to (4,10), then step LEFT onto the door (3,10)
for _ in range(3):
    if pos()[1] >= 10:
        break
    e.press("DOWN", hold=16, after=10)
e.press("LEFT", hold=16, after=10)
e.press("LEFT", hold=16, after=12)
print("stepped onto door:", pos(), "| map", R.loc(e)["mapId"], "| state", e.state())
e.emu.screenshot().save(SCRATCH + "/play.png")

if R.loc(e)["mapId"] != 63:
    print("RESULT: NOT blocked -- warped to map", R.loc(e)["mapId"]); sys.exit()
print("RESULT: BLOCKED (still in house). Clearing Mom's line...")
e.clear_dialog()
print("after gate:", pos(), "| var", R.var(e, R.VAR_SCENE_PLAYERS_HOUSE_1F), "| map", R.loc(e)["mapId"])

# --- UNLOCK: simulate getting the Pokegear (var leaves 1, disarming the gate) ---
R.set_var(e, R.VAR_SCENE_PLAYERS_HOUSE_1F, 4); e.wait(8)
for _ in range(5):
    if pos() == (3, 10):
        break
    e.press("LEFT" if pos()[0] > 3 else "RIGHT", hold=16, after=10)
e.press("DOWN", hold=18, after=6)
for _ in range(30):
    if R.loc(e)["mapId"] != 63:
        break
    e.wait(6)
print("UNLOCK exit -> map", R.loc(e)["mapId"], "pos", pos(),
      "(67 = Cherrygrove = door opened)")
