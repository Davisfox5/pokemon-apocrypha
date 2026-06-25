#!/usr/bin/env python3
"""Controlled capture of the Apocrypha cold open: step the new-game flow one
dialogue box at a time so each beat (dots -> Mom wake -> our new home -> brighten
-> Kalos) can be screenshotted and verified."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from emu_harness import Emu

e = Emu()
e.wait(300)
# skip health/copyright/Nintendo+GF logos + legendary intro -> title -> main menu
for _ in range(8):
    e.press("START", hold=4, after=40)
# select NEW GAME (top option) and let it load
e.press("A", hold=4, after=120)
# gender select: confirm (A works per calibration); tap center as belt-and-suspenders
e.press("A", hold=4, after=30)
e.touch(128, 96, hold=4, after=30)
e.press("A", hold=4, after=120)
# now step through the cold open, capturing BEFORE each advance
for i in range(20):
    e.shot(f"co_{i:02d}_f{e.frame:05d}")
    e.press("A", hold=4, after=55)
e.savestate("/tmp/apoc_frames/after_coldopen.dsv")
print("done frames:", e.frame)
print("saved:", sorted(p for p in os.listdir("/tmp/apoc_frames") if p.startswith("co_")))
