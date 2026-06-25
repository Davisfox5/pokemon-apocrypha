#!/usr/bin/env python3
"""Apocrypha scripted-playthrough harness for py-desmume (headless DeSmuME).

Drives the freshly-built ROM frame-by-frame, injecting controller input and
dumping screenshots so the build can be visually verified without a GUI.

Usage: run inside the .emu-venv. Import helpers or run a driver script that
calls boot() then press()/wait()/shot().
"""
import os
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask

ROM = "/Users/davisfox/Documents/GitHub/the-omni-hack/disasm/pokeheartgold/build/heartgold.us/pokeheartgold.us.nds"
OUT = "/tmp/apoc_frames"
os.makedirs(OUT, exist_ok=True)

KEY = {
    "A": Keys.KEY_A, "B": Keys.KEY_B, "X": Keys.KEY_X, "Y": Keys.KEY_Y,
    "L": Keys.KEY_L, "R": Keys.KEY_R, "START": Keys.KEY_START, "SELECT": Keys.KEY_SELECT,
    "UP": Keys.KEY_UP, "DOWN": Keys.KEY_DOWN, "LEFT": Keys.KEY_LEFT, "RIGHT": Keys.KEY_RIGHT,
}

class Emu:
    def __init__(self, rom=ROM):
        self.emu = DeSmuME()
        try: self.emu.volume_set(0)
        except Exception: pass
        self.emu.open(rom)
        self.frame = 0

    def wait(self, n):
        # cycle(False): do NOT poll the (uninitialized) joystick, which would
        # otherwise reset the keypad every frame and swallow scripted input.
        for _ in range(n):
            self.emu.cycle(False)
            self.frame += 1

    def press(self, key, hold=6, after=10):
        m = keymask(KEY[key])
        self.emu.input.keypad_add_key(m)
        self.wait(hold)
        self.emu.input.keypad_rm_key(m)
        self.wait(after)

    def touch(self, x, y, hold=6, after=8):
        self.emu.input.touch_set_pos(x, y)
        self.wait(hold)
        self.emu.input.touch_release()
        self.wait(after)

    def shot(self, name):
        p = os.path.join(OUT, name if name.endswith(".png") else name + ".png")
        self.emu.screenshot().save(p)
        return p

    def savestate(self, path):
        self.emu.savestate.save_file(path)

    def loadstate(self, path):
        self.emu.savestate.load_file(path)

    # --- screen-state aware helpers (for reliable scripted navigation) ---
    def state(self):
        img = self.emu.screenshot().convert('L')
        px = img.load()
        box = [px[x, y] for y in range(150, 186, 6) for x in range(24, 236, 24)]
        fld = [px[x, y] for y in range(16, 120, 12) for x in range(24, 236, 24)]
        bm = sum(box) / len(box); fm = sum(fld) / len(fld)
        if bm < 20 and fm < 20: return 'black'
        if bm > 195: return 'box'
        return 'field'

    def clear_dialog(self, cap=60):
        for _ in range(cap):
            if self.state() == 'field':
                return True
            self.press('A', hold=3, after=12)
        return False

    def step(self, key, n=1, hold=12, after=14):
        for _ in range(n):
            self.press(key, hold=hold, after=after)


if __name__ == "__main__":
    e = Emu()
    e.wait(300)
    # mash START/A through the health screen + logos + legendary intro, sampling frames
    checkpoints = [600, 1100, 1600, 2200, 2800, 3400]
    nxt = 0
    while e.frame < 3500:
        e.press("START", hold=4, after=8)
        e.press("A", hold=4, after=8)
        if nxt < len(checkpoints) and e.frame >= checkpoints[nxt]:
            e.shot(f"cal_{e.frame:05d}")
            nxt += 1
    e.shot(f"cal_{e.frame:05d}_end")
    print("frames:", e.frame)
    print("saved:", sorted(os.listdir(OUT)))
