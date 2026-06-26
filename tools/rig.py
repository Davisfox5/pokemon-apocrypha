#!/usr/bin/env python3
"""High-level self-test rig for Apocrypha (py-desmume + RAM oracle).

Provides reliable scene-driving primitives so I can verify a scene myself before
handing a build to the user:
  - advance_until_var: mash A (hold>=4 so presses register) until a scene var hits
    a target = the ground-truth "scene progressed" signal.
  - new_game_to_house_free: boot -> gender -> clear cold open -> player free.
  - checkpoint save/load: jump to a scene state in ~1s instead of replaying.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from emu_harness import Emu
import emu_ram as R

CKPT_DIR = os.path.join(os.path.dirname(__file__), "checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)


def advance_until_var(e, vid, target, cap=300, hold=5, after=16):
    """Press A until script var `vid` reaches `target`. Returns presses used, or -1."""
    for i in range(cap):
        if R.var(e, vid) >= target:
            return i
        e.press("A", hold=hold, after=after)
    return -1


def gender_select(e):
    """New game -> confirm gender (tap boy, tap YES)."""
    for _ in range(8):
        e.press("START", hold=4, after=40)
    e.press("A", hold=4, after=120)            # NEW GAME
    e.touch(57, 95, hold=5, after=20)          # boy sprite
    e.touch(195, 55, hold=5, after=30)         # YES


def new_game_to_house_free(e):
    """Boot a fresh game through the cold open to free-roam in the house.
    Returns presses used to clear the cold open (-1 if it never completed)."""
    e.wait(300)
    gender_select(e)
    return advance_until_var(e, R.VAR_SCENE_PLAYERS_HOUSE_1F, 1)


def ckpt_path(name):
    return os.path.join(CKPT_DIR, name + ".dsv")


def save_ckpt(e, name):
    e.savestate(ckpt_path(name)); return ckpt_path(name)


def load_ckpt(e, name):
    e.loadstate(ckpt_path(name))


if __name__ == "__main__":
    e = Emu()
    n = new_game_to_house_free(e)
    s = R.snapshot(e)
    print(f"cold open cleared in {n} presses; state={s}")
    if n >= 0:
        save_ckpt(e, "house_free")
        print("saved checkpoint: house_free.dsv  (map should be 63, HOUSE_1F var >=1)")
    else:
        e.shot("rig_coldopen_stuck")
        print("COLD OPEN DID NOT COMPLETE - see rig_coldopen_stuck.png")


def go_through_warp(e, direction, steps_to_tile=1):
    """Walk onto a warp tile then press again to walk THROUGH it (warps need the
    second press to trigger). Caller positions the player adjacent first."""
    for _ in range(steps_to_tile):
        e.press(direction, hold=16, after=14)   # step onto the warp tile
    e.press(direction, hold=20, after=40)        # walk through -> warp fires
    e.wait(120)
