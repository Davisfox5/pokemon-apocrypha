#!/usr/bin/env python3
"""Robust intro/navigation helpers for the Apocrypha autoplayer.

Key idea: distinguish game states *behaviorally*. In free-roam a D-pad press
scrolls the map (large top-screen delta); on a menu / gender-select / locked
cutscene it does not. This sidesteps the fact that the tan gender-select screen
and the house field both read as mid-brightness 'field' to a naive detector.
"""
import numpy as np


def top_gray(e):
    return np.asarray(e.emu.screenshot().convert("L"))[0:192, :].astype("int16")


def is_free_roam(e, thresh=11):
    """Probe: press DOWN briefly; if the top screen (map) moved a lot, we have
    walking control. Harmless on menus/cutscenes (no scroll)."""
    a = top_gray(e)
    e.press("DOWN", hold=12, after=6)
    b = top_gray(e)
    return float(np.abs(a - b).mean()) > thresh


def new_game_to_control(e, clear_cap=80):
    """Boot a fresh game, confirm gender (tap the boy sprite, then tap YES on the
    confirm dialog), clear the cold open, and return once the player has walking
    control in the house."""
    e.wait(300)
    for _ in range(8):
        e.press("START", hold=4, after=40)
    e.press("A", hold=4, after=150)               # NEW GAME -> gender select
    for _ in range(3):                            # tap boy, then tap YES (both touches)
        e.touch(57, 95, hold=5, after=18)         # boy sprite (bottom-left)
        e.touch(195, 55, hold=5, after=26)        # YES button (bottom-right)
    for _ in range(clear_cap):                    # clear the cold open until free-roam
        if is_free_roam(e):
            return True
        e.press("A", hold=3, after=16)
    return False


def walk(e, key, n):
    for _ in range(n):
        e.press(key, hold=16, after=16)


def advance_until_freeroam(e, cap=40, capture=None):
    """Press A through any dialogue/cutscene until walking control returns,
    optionally screenshotting each step. Returns frames captured."""
    shots = []
    for i in range(cap):
        if capture:
            shots.append(e.shot(f"{capture}_{i:02d}"))
        if is_free_roam(e):
            return shots
        e.press("A", hold=4, after=34)
    return shots
