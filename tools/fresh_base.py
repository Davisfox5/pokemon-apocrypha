#!/usr/bin/env python3
"""Generate a CURRENT-ROM clean free-roam checkpoint for CPP-style play.

Old checkpoints captured the previous build's field overlays in RAM; loaded under
the freshly-rebuilt ROM the field logic executes garbage (undefined-instruction /
frozen input). This boots the *current* ROM from a new game, clears the cold open
to in-house free-roam, and saves a fresh checkpoint whose RAM matches the ROM.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from emu_harness import Emu
import emu_ram as R
import rig

e = Emu()
n = rig.new_game_to_house_free(e)
s = R.snapshot(e)
print(f"cold open cleared in {n} presses; state={s}")
e.shot("fresh_base")
print("PNG:", os.path.join("/tmp/apoc_frames", "fresh_base.png"))
if n >= 0:
    p = rig.save_ckpt(e, "cur_house")
    print("saved checkpoint:", p)
else:
    print("COLD OPEN DID NOT COMPLETE")
