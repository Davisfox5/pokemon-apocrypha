#!/usr/bin/env python3
"""Replay a path recorded by ``cockpit.py --record``.

The cockpit writes what you actually pressed while walking a scene by hand.
This module plays it back through the same ``Emu`` the rig uses, so
choreography can be walked once instead of hand-coded as press() calls.

    from emu_harness import Emu
    from path_replay import load, replay

    from emu_harness import KEY, Emu

    assert KEY_NAMES == frozenset(KEY), (
        "path_replay.KEY_NAMES has drifted from emu_harness.KEY"
    )

    e = Emu()
    e.wait(8)
    steps = load("paths/ch1_s2.json")
    replay(e, steps)

Or from the shell, inside .emu-venv:

    python tools/path_replay.py paths/ch1_s2.json --state cur_cherrygrove.dsv

A path is a list of steps:

    {"op": "press", "key": "A",  "hold": 6, "after": 10}
    {"op": "touch", "x": 57, "y": 95, "hold": 5, "after": 20}
    {"op": "note",  "text": "checkpoint @ frame 4210"}

``hold`` and ``after`` are emulated frames. ``note`` is a comment and is skipped.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

# Valid rig key names. Duplicated from emu_harness.KEY so this module (and its
# tests) import without desmume present; the assertion in replay() keeps the two
# from drifting.
KEY_NAMES = frozenset({
    "A", "B", "X", "Y", "L", "R", "START", "SELECT",
    "UP", "DOWN", "LEFT", "RIGHT",
})


def load(path):
    """Read a recorded path. Accepts the cockpit's wrapper or a bare step list."""
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data.get("steps", [])
    return data


def seed_state(path):
    """Return the savestate name the path was recorded from, or None.

    A path recorded from a checkpoint only replays correctly from that same
    checkpoint. Callers should honor this rather than replaying from a cold boot.
    """
    with open(path) as f:
        data = json.load(f)
    return data.get("seed_state") if isinstance(data, dict) else None


def replay(e, steps, verbose=False, on_step=None):
    """Play `steps` against emulator `e`. Returns the number of steps executed.

    `on_step(i, step)` runs before each step, which is where a caller hooks in a
    RAM assertion to find the exact step a scene diverges at.
    """
    done = 0
    for i, step in enumerate(steps):
        op = step.get("op")
        if on_step:
            on_step(i, step)
        if op == "note":
            if verbose:
                print(f"[{i}] note: {step.get('text', '')}")
            continue
        if op == "press":
            key = step.get("key")
            if key not in KEY_NAMES:
                raise ValueError(f"step {i}: unknown key {key!r}")
            e.press(key, hold=int(step.get("hold", 6)),
                    after=int(step.get("after", 10)))
        elif op == "touch":
            e.touch(int(step["x"]), int(step["y"]),
                    hold=int(step.get("hold", 6)),
                    after=int(step.get("after", 8)))
        else:
            raise ValueError(f"step {i}: unknown op {op!r}")
        done += 1
        if verbose:
            print(f"[{i}] {op} {step.get('key') or ''} "
                  f"hold={step.get('hold')} after={step.get('after')}")
    return done


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    path = args[0]
    state = None
    if "--state" in args:
        state = args[args.index("--state") + 1]
    verbose = "-v" in args or "--verbose" in args

    recorded_seed = seed_state(path)
    if recorded_seed and not state:
        print(f"warning: path was recorded from {recorded_seed}; "
              f"replaying from a cold boot will almost certainly desync. "
              f"Pass --state {recorded_seed}")

    from emu_harness import KEY, Emu

    assert KEY_NAMES == frozenset(KEY), (
        "path_replay.KEY_NAMES has drifted from emu_harness.KEY"
    )

    e = Emu()
    e.wait(8)
    if state:
        e.loadstate(state)
        e.wait(8)

    steps = load(path)
    n = replay(e, steps, verbose=verbose)
    print(f"replayed {n} step(s) from {path}; frame={e.frame}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
