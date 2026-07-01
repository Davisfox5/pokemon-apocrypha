#!/usr/bin/env python3
"""Screenshot the house from a few vantage points to see whether the custom
cardboard-box sprites (SPRITE_CARDBOARDBOX = 1050) render on the floor."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from emu_harness import Emu
import emu_ram as R
import rig
SC = "/private/tmp/claude-501/-Users-davisfox-Documents-GitHub-the-omni-hack/3fdef984-9a20-4cf3-8daf-48eed0d89062/scratchpad"

e = Emu()
rig.new_game_to_house_free(e)

def shot(tag, x=None, z=None):
    if x is not None:
        R.teleport(e, x, z); e.wait(12)
    e.emu.screenshot().save(SC + f"/box_{tag}.png")
    o = R.objects(e)
    ids = sorted({b["sprite"] for b in o})
    boxes = [(b["x"], b["z"]) for b in o if b["sprite"] == 1050]
    print(tag, "| player", [(p["x"], p["z"]) for p in o if p["id"] == 255],
          "| sprite ids present:", ids, "| boxes@", boxes)

shot("spawn")
shot("topleft", 3, 6)     # near box1 (1,4)
shot("left", 4, 8)        # near box2 (2,8)
shot("right", 6, 7)       # near box3 (8,5) / box4 (6,9)
