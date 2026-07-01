#!/usr/bin/env python3
"""Minimal: does Mom wander from spawn (zone_event movement type)? Idle the field
with B-presses so the NPC AI ticks, and watch whether her tile changes."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from emu_harness import Emu
import emu_ram as R
import rig

e = Emu()
rig.new_game_to_house_free(e)   # var=1, free-roam in the house
print("Observing Mom at var=1 (should wander if movement type walks):")
last, moved = None, 0
for i in range(12):
    for _ in range(8):
        e.press("B", hold=2, after=4)   # idle ticks; B is a no-op in field free-roam
    m = next((o for o in R.objects(e) if o["sprite"] == 365), None)
    pos = (m["x"], m["z"], m["dirname"]) if m else None
    if last and pos and pos[:2] != last[:2]:
        moved += 1
    print(f"[{i}] Mom {pos}")
    last = pos
print("position changes:", moved, "->", "WANDERS" if moved else "STATIONARY")
