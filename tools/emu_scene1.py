#!/usr/bin/env python3
"""Walk out the house door into Cherrygrove to trigger Scene 1, then step through
its dialogue capturing each box (Kestra recognition, Gold/Silver battle, crowd,
fly-off, and the naming screen)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from emu_harness import Emu

e = Emu()
e.wait(300)
for _ in range(8):
    e.press("START", hold=4, after=40)
e.press("A", hold=4, after=120)      # NEW GAME
e.press("A", hold=4, after=30)       # gender
e.touch(128, 96, hold=4, after=30)
e.press("A", hold=4, after=120)
for _ in range(10):                  # clear the cold open -> control
    e.press("A", hold=4, after=45)
# exit via the front door (down to z10, left to the 3,10 warp)
e.press("DOWN", hold=12, after=20)
e.press("DOWN", hold=12, after=20)
e.press("LEFT", hold=12, after=20)
e.press("LEFT", hold=12, after=20)
e.wait(200)                          # warp + Scene 1 coord trigger + scene start
e.shot("s1_00_arrive")
# step Scene 1 dialogue
for i in range(22):
    e.press("A", hold=4, after=45)
    e.shot(f"s1_{i+1:02d}_f{e.frame:05d}")
e.savestate("/tmp/apoc_frames/scene1.dsv")
print("done frames:", e.frame)
sizes = {p: os.path.getsize('/tmp/apoc_frames/'+p) for p in os.listdir('/tmp/apoc_frames') if p.startswith('s1_')}
for k in sorted(sizes): print(sizes[k], k)
