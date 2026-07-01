#!/usr/bin/env python3
"""Re-verify the grass catch fires with VAR_SCENE_ROUTE_30_OW at its true gate-entry
value (0) -- i.e. the val:0 trigger fix. Hop-teleport up to the grass (streaming
collision), then step onto the trigger WITHOUT poking any var, and check the catch
staged (rescue Kestra turns south to face the player; player locked in a box)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from emu_harness import Emu
import emu_ram as R
SCRATCH = "/private/tmp/claude-501/-Users-davisfox-Documents-GitHub-the-omni-hack/3fdef984-9a20-4cf3-8daf-48eed0d89062/scratchpad"
e = Emu(); e.wait(4)
e.loadstate(os.path.join(os.path.dirname(__file__), "checkpoints/cur_r30.dsv")); e.wait(6)

def pos():
    o = next((o for o in R.objects(e) if o["id"] == 255), None)
    l = R.loc(e)
    return (o["x"], o["z"]) if o else (l["x"], l["z"])

# hop north past the bridge to the grass, each teleport loads local collision
for tz in (365, 353, 341):
    R.teleport(e, 552, tz); e.wait(16)
    e.press("UP", hold=14, after=8); e.press("DOWN", hold=14, after=8)
R.teleport(e, 552, 331); e.wait(16)   # adjacent SOUTH of rescue Kestra (552,330)
# face NORTH (toward Kestra) by writing the direction directly -- no step, no encounter roll
po = R.player_obj_addr(e)
for off in (0x28, 0x2C):
    e.emu.memory.write_short(po + off, 0); e.emu.memory.write_short(po + off + 2, 0)
e.wait(6)
print("pre-talk: pos", pos(), "facing", next((o["dirname"] for o in R.objects(e) if o["id"] == 255), "?"))

# TALK to Kestra (A is not a step -> no encounter)
e.press("A", hold=6, after=14)
e.wait(90)
ks = [(o["x"], o["z"], o["dirname"]) for o in R.objects(e) if o["sprite"] == 320 and abs(o["z"] - 330) <= 3]
print("post-step: pos", pos(), "| state", e.state(), "| CHERRY_OW", R.var(e, 0x4073))
print("rescue Kestra (spr320 near 552,330):", ks)
e.emu.screenshot().save(SCRATCH + "/play.png")
