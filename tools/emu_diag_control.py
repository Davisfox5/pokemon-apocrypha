#!/usr/bin/env python3
"""Diagnostic: reach player control after the cold open, then issue MOVEMENT
(not A) to confirm the player can walk the house (rules out a hang)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from emu_harness import Emu

e = Emu()
e.wait(300)
for _ in range(8):
    e.press("START", hold=4, after=40)
e.press("A", hold=4, after=120)      # NEW GAME
e.press("A", hold=4, after=30)       # gender confirm
e.touch(128, 96, hold=4, after=30)   # gender (touch fallback)
e.press("A", hold=4, after=120)
# advance through the ~6 cold-open boxes to reach control
for _ in range(10):
    e.press("A", hold=4, after=45)
e.shot("ctl_0_control")
# now MOVE (no A): walk down/left/up to prove free roam works
for i, key in enumerate(["DOWN","DOWN","LEFT","LEFT","UP","RIGHT"]):
    e.press(key, hold=10, after=20)
    e.shot(f"ctl_{i+1}_{key}")
print("done frames:", e.frame)
print("saved:", sorted(p for p in os.listdir("/tmp/apoc_frames") if p.startswith("ctl_")))
