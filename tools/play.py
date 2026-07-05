#!/usr/bin/env python3
"""CPP-style visual driver for Apocrypha (py-desmume, HGSS).

Replicates the Claude-Plays-Pokemon loop. Each invocation:
  1. loads a persistent save-state from disk,
  2. applies the button presses I pass on the command line,
  3. saves the state back (so the next call continues where this one left off),
  4. writes a screenshot PNG (for my eyes) AND prints a structured RAM dump
     (map id / live player tile + facing / nearby objects) -- the same
     perception CPP got: a picture plus a dump of game data from the emulator.

py-desmume is a singleton per process, so every call is its own short-lived
process and the .dsv on disk is the persistent world.

Usage:
  python play.py STATE.dsv INIT SRC.dsv   # seed STATE from a checkpoint
  python play.py STATE.dsv LOOK           # no input; just screenshot + dump
  python play.py STATE.dsv UP UP A        # apply buttons in order
  python play.py STATE.dsv UP*5 RIGHT*2   # '*' repeats a button

Dpad = one walking tile each (hold 16 frames). A/B/START/etc = a tap.
PNG is written alongside STATE (STATE.png).
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from emu_harness import Emu
import emu_ram as R

BTN = {"A", "B", "X", "Y", "L", "R", "START", "SELECT"}
DPAD = {"UP", "DOWN", "LEFT", "RIGHT"}


def main():
    state = sys.argv[1]
    args = sys.argv[2:]
    e = Emu()
    e.wait(4)  # let the core spin up before loadstate

    if args and args[0].upper() == "INIT":
        e.loadstate(args[1])
        e.wait(8)
    else:
        if os.path.exists(state):
            e.loadstate(state)
            e.wait(2)
        seq = []
        for a in args:
            if a.upper() == "LOOK":
                continue
            if "*" in a:
                k, n = a.split("*")
                seq += [k] * int(n)
            else:
                seq.append(a)
        for k in seq:
            if k.upper().startswith("SETVAR:"):   # SETVAR:0x4073:3 -> poke a script var
                _, vid, val = k.split(":")
                R.set_var(e, int(vid, 0), int(val, 0))
                continue
            if k.upper().startswith("TOUCH:"):     # TOUCH:66,101 -> tap the bottom screen
                tx, ty = k.split(":")[1].split(",")
                e.touch(int(tx), int(ty), hold=6, after=12)
                continue
            if k.upper().startswith("TP:"):        # TP:550,330 -> hard-set player tile (same map)
                tx, tz = k.split(":")[1].split(",")
                R.teleport(e, int(tx), int(tz))
                e.wait(8)                          # let the camera re-center / map stream in
                continue
            k = k.upper()
            if k.isdigit():            # bare integer = wait that many frames
                e.wait(int(k))
            elif k in BTN:
                e.press(k, hold=6, after=12)
            elif k in DPAD:
                e.press(k, hold=16, after=10)
        e.wait(4)

    e.savestate(state)
    png = (state[:-4] if state.endswith(".dsv") else state) + ".png"
    e.emu.screenshot().save(png)

    l = R.loc(e)
    objs = R.objects(e)
    px = next((o for o in objs if o["id"] == 255), None)
    try:
        ow = R.var(e, R.VAR_SCENE_CHERRYGROVE_CITY_OW)
        hv = R.var(e, R.VAR_SCENE_PLAYERS_HOUSE_1F)
    except Exception:
        ow = hv = "?"
    if px:
        print(f"map={l['mapId']} player=({px['x']},{px['z']}) face={px['dirname']} cg_ow={ow} house={hv}")
        bx, bz = px["x"], px["z"]
    else:
        print(f"map={l['mapId']} player_loc=({l['x']},{l['z']}) dir={l['dir']} cg_ow={ow} [no live player obj]")
        bx, bz = l["x"], l["z"]
    near = [f"spr{o['sprite']}@({o['x']},{o['z']}){o['dirname']}"
            for o in objs if o["id"] != 255 and abs(o["x"] - bx) <= 12 and abs(o["z"] - bz) <= 12]
    print("near:", ", ".join(near) if near else "(none within 12)")
    print("PNG:", png)


if __name__ == "__main__":
    main()
