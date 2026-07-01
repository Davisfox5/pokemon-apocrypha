#!/usr/bin/env python3
"""Drive the come-downstairs + Mom scene (_006) by simulating arrival at the stairs
(3,3) and poking var=2, then watch player/Mom positions + facings through Mom's
monologue and exit -- to catch 'player faces a wall' / 'Mom vanishes'."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from emu_harness import Emu
import emu_ram as R
import rig
SCRATCH = "/private/tmp/claude-501/-Users-davisfox-Documents-GitHub-the-omni-hack/3fdef984-9a20-4cf3-8daf-48eed0d89062/scratchpad"

e = Emu()
rig.new_game_to_house_free(e)
R.teleport(e, 3, 3); e.wait(8)                              # simulate stairs arrival

def snap(tag):
    o = R.objects(e)
    dump = [(("PLAYER" if x["id"] == 255 else "MOM" if x["sprite"] == 365 else x["sprite"]),
             x["x"], x["z"], x["dirname"]) for x in o]
    print(tag, "| var", R.var(e, R.VAR_SCENE_PLAYERS_HOUSE_1F), "| state", e.state(), "|", dump)
    e.emu.screenshot().save(SCRATCH + f"/{tag}.png")

print("--- var=1 free-roam: does Mom wander from spawn (zone_event mv=3)? ---")
for i in range(5):
    e.wait(60)
    m = next((o for o in R.objects(e) if o["sprite"] == 365), None)
    print(f"v1[{i}] Mom", (m["x"], m["z"], m["dirname"]) if m else "?")
snap("s006_pre")                                            # Mom's start, before the scene
R.set_var(e, R.VAR_SCENE_PLAYERS_HOUSE_1F, 2); e.wait(50)   # -> come-down scene (_007) fires
snap("s006_start")                                          # staging: player + Mom face-to-face?
for _ in range(8):                                          # robustly clear msgs/fanfares
    e.clear_dialog(); e.wait(45)
snap("s006_after")                                          # scene complete: Mom back, var==4, free?
print("END | state", e.state(), "| var", R.var(e, R.VAR_SCENE_PLAYERS_HOUSE_1F),
      "| objs", [((("PLAYER" if x["id"] == 255 else "MOM")), x["x"], x["z"], x["dirname"])
                 for x in R.objects(e) if x["id"] == 255 or x["sprite"] == 365])
print("--- Mom should now wander (positions should change over time) ---")
for i in range(5):
    e.wait(60)
    m = next((o for o in R.objects(e) if o["sprite"] == 365), None)
    print(f"wander[{i}] Mom", (m["x"], m["z"], m["dirname"]) if m else "?")
