#!/usr/bin/env python3
"""Apocrypha Map Editor -- Dear PyGui rebuild (dark IDE).

A polished editor for the HGSS ROM hack, built on the same backend as the earlier
pygame tools (mapdata / mapresolve / emu_ram / py-desmume). Live game runs in a
pane; a stable world-tile canvas shows the map with draggable event icons; a
properties panel and toolbar give a real app feel.

Run (inside .emu-venv, from repo root):
    source .emu-venv/bin/activate
    python tools/mapeditor/editor_app.py --state cockpit_quick.dsv

Toolbar buttons + shortcuts:  G play/edit   S save   R build   F reveal   B map-bg
EDIT: drag an icon to move it (live poke + writes JSON).  PLAY (G): arrows/Z/X walk.
"""
import os, sys, math, copy, hashlib, subprocess, threading, traceback
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import dearpygui.dearpygui as dpg
from desmume.controls import keymask, Keys
from emu_harness import Emu, ROM as ROM_PATH
import emu_ram as R
from mapdata import ZoneEvents
from mapresolve import zone_event_path, flag_id, map_list
from live_editor import Handle, KINDS, KIND_COLOR, PLAYER_PX_X, PLAYER_PX_Y
import describe as D
import behavior as BW

DS_W, DS_H = 256, 384
CELL = 28                              # canvas px per world tile
CW, CH = 860, 760                      # canvas drawlist size
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# the real build script lives in the decomp submodule, not the repo root
BUILD_SCRIPT = os.path.join(ROOT, "disasm", "pokeheartgold", "_omni_native_build.sh")
BUILD_LOG = os.path.join(ROOT, "_mapeditor_build.log")
LOG_PATH = os.path.join(ROOT, "_mapeditor.log")
# Checkpoints: stale-build savestates freeze (they carry old overlay CODE in RAM --
# see tools/fresh_base.py), so we prefer, in order:
#   1. auto/last_session.dsv  -- where you left off last time (same-session ROM)
#   2. cur_house.dsv          -- regenerated fresh from the current ROM
CKPT_DIR = os.path.join(ROOT, "tools", "checkpoints")
AUTO_DIR = os.path.join(CKPT_DIR, "auto")
os.makedirs(AUTO_DIR, exist_ok=True)
SESSION_STATE = os.path.join(AUTO_DIR, "last_session.dsv")
FRESH_STATE = os.path.join(CKPT_DIR, "cur_house.dsv")
FRESH_SCRIPT = os.path.join(ROOT, "tools", "fresh_base.py")

def default_state():
    """Prefer a state SAVED AFTER the current ROM was built -- an older one carries
    the previous build's code in RAM and crashes (ARM undefined instruction)."""
    have = [p for p in (SESSION_STATE, FRESH_STATE) if os.path.exists(p)]
    try:
        rom_t = os.path.getmtime(ROM_PATH)
        for p in have:
            if os.path.getmtime(p) >= rom_t:
                return p
    except OSError:
        pass
    return have[0] if have else None

# icon color with alpha
def _rgba(kind, a=255, dim=False):
    c = KIND_COLOR[kind]
    if dim:
        c = tuple(x // 2 for x in c)
    return (c[0], c[1], c[2], a)

PLAY_KEYS = {
    dpg.mvKey_Up: Keys.KEY_UP, dpg.mvKey_Down: Keys.KEY_DOWN,
    dpg.mvKey_Left: Keys.KEY_LEFT, dpg.mvKey_Right: Keys.KEY_RIGHT,
    dpg.mvKey_Z: Keys.KEY_A, dpg.mvKey_X: Keys.KEY_B,
    dpg.mvKey_Return: Keys.KEY_START, dpg.mvKey_Shift: Keys.KEY_SELECT,
}

# plain-English names for the four event kinds (internal keys stay objects/warps/...)
KIND_LABEL = {
    "objects": "Characters",
    "warps": "Doors & exits",
    "coords": "Step triggers",
    "bgs": "Signs & items",
}

# field display order per event kind (widget type inferred from the value's type)
FIELD_ORDER = {
    "objects": ["id", "spriteId", "scriptId", "eventFlag", "movement", "type",
                "facingDirection", "xRange", "yRange", "param0", "param1", "param2",
                "x", "z", "y"],
    "warps": ["header", "anchor", "x", "z", "y"],
    "coords": ["scriptId", "var", "w", "h", "val", "x", "z", "y"],
    "bgs": ["scriptId", "type", "dir", "x", "z", "y"],
}


class MapEditor:
    def __init__(self, state=None):
        self.e = Emu(); self.e.wait(8)
        self.seed = None
        self.stale_state = False
        if state and os.path.exists(state):
            self.e.loadstate(state); self.e.wait(8); self.seed = state
            # A savestate older than the ROM carries the OLD build's code in RAM.
            # It may walk for a few steps and then hit an undefined instruction
            # (0x76767676) when the game loads anything that changed. Flag it so
            # run() can regenerate a fresh save instead of handing out a time bomb.
            try:
                self.stale_state = os.path.getmtime(state) < os.path.getmtime(ROM_PATH)
            except OSError:
                pass
        self.mode = "edit"                 # "edit" | "play"
        self.map_id = None
        self.player = (0, 0)
        self.pan = [0, 0]
        self.zones = {}
        self.dirty = set()
        self.handles = []
        self.selected = None
        self.dragging = False
        self.show = set(KINDS)
        self.show_bg = True
        self.frame = 0
        self.status = "ready"
        self.hover = None
        self.ctx_open = False
        self._prev_right = False
        self._ctx_tile = (0, 0)
        self.show_raw = False              # Properties panel: plain English vs raw fields
        self.pinned = set()                # lmo_addrs frozen for drag (unfrozen on Play)
        self._prev_left = False
        self.cw, self.ch = CW, CH          # live canvas size (follows the resizable pane)
        self.resizing = None               # active trigger-resize drag: (handle, ref)
        self.pending_text = {}             # msg sym -> edited dialogue, flushed on Save
        self.pick_dest = None              # callback armed by "click a tile" wizard steps
        self._wiz = {}                     # behavior/walk wizard state
        self.keys_down = set()             # Keys.* currently held (for play mode)
        # undo/redo -------------------------------------------------------------
        self.undo_stack = []               # entries: {op, label, ...}
        self.redo_stack = []
        self._drag_before = None           # ref snapshot at drag start
        self._resize_before = None
        self._typing_frame = -99           # last frame a text/number input was active
        # navigator / search ------------------------------------------------------
        self.browsing = False              # viewing a map the player is not on
        self.search_rows = None            # dialogue index rows (built by bg thread)
        self.search_status = "building dialogue index…"
        self._nav_map = {}                 # listbox label -> action payload
        # build / reload ----------------------------------------------------------
        self._build_proc = None
        self._fresh_proc = None

    def _log(self, msg):
        try:
            with open(LOG_PATH, "a") as f:
                f.write(msg + "\n")
        except OSError:
            pass

    # --- framebuffer ---------------------------------------------------------
    def _frame_floats(self):
        buf = np.frombuffer(bytes(self.e.emu.display_buffer_as_rgbx()), dtype=np.uint8)
        arr = buf.astype(np.float32) / 255.0
        arr[3::4] = 1.0
        return arr

    # --- world state ---------------------------------------------------------
    def _sync(self):
        try:
            entries = R.object_entries(self.e)
            mid = R.loc(self.e)["mapId"]
        except Exception:
            return None, None
        px = next((o for o in entries if o["id"] == 255), None)
        if px:
            self.player = (px["x"], px["z"])
        return entries, mid

    def _refresh_live(self):
        entries, mid = self._sync()
        if entries is None:
            return None
        if self.browsing:
            # viewing another map's files: live ids belong to the player's map,
            # so binding by index would attach the wrong sprites
            for h in self.handles:
                if h.kind == "objects":
                    h.lmo_addr, h.live = 0, None
            return mid
        by_id = {o["id"]: o for o in entries if o["id"] != 255}
        for h in self.handles:
            if h.kind != "objects":
                continue
            o = by_id.get(h.idx)
            h.lmo_addr, h.live = (o["addr"], (o["x"], o["z"])) if o else (0, None)
        return mid

    def _load_map(self, map_id):
        self.map_id = map_id
        if map_id not in self.zones:
            p = zone_event_path(map_id)
            self.zones[map_id] = ZoneEvents.load(p) if p else None
        self.selected = None
        self._rebuild_handles()
        self._rebuild_props()

    def _rebuild_handles(self):
        """(Re)build handles from current zone data + re-bind live objects. Call
        after add/delete/duplicate so idx and refs stay consistent."""
        z = self.zones.get(self.map_id)
        self.handles = []
        if z is not None:
            for kind in KINDS:
                for i, ref in enumerate(getattr(z, kind)):
                    self.handles.append(Handle(kind, ref, i))
        self._refresh_live()

    # --- add / delete / duplicate -------------------------------------------
    def _new_event(self, kind, tx, tz):
        if kind == "objects":
            return {"id": "obj_new", "spriteId": "SPRITE_NPC_NORMAL", "movement": 0,
                    "type": 0, "eventFlag": "FLAG_NOTHING", "scriptId": 0,
                    "facingDirection": 0, "param0": 0, "param1": 0, "param2": 0,
                    "xRange": 0, "yRange": 0, "x": tx, "z": tz, "y": 0}
        if kind == "warps":
            return {"x": tx, "z": tz, "header": "MAP_NOTHING", "anchor": 0, "y": 0}
        if kind == "coords":
            return {"scriptId": 0, "x": tx, "z": tz, "w": 1, "h": 1, "y": 0,
                    "val": 0, "var": "VAR_TEMP_x4000"}
        return {"scriptId": 0, "type": 0, "x": tx, "z": tz, "y": 0, "dir": 0}

    def add_event(self, kind, tx, tz):
        z = self.zones.get(self.map_id)
        if z is None:
            self.status = "this map has no events file"; return
        ref = self._new_event(kind, tx, tz)
        lst = getattr(z, kind)
        lst.append(ref)
        self.push_undo({"op": "add", "mid": self.map_id, "kind": kind, "ref": ref,
                        "idx": len(lst) - 1, "label": "add " + kind[:-1]})
        self.dirty.add(self.map_id)
        self._rebuild_handles()
        self.selected = next((h for h in reversed(self.handles) if h.ref is ref), None)
        self._rebuild_props()
        self.status = f"added {kind[:-1]} at ({tx},{tz}) - set its fields, then Save + Build"

    def delete_selected(self):
        h = self.selected
        if not h:
            return
        lst = getattr(self.zones[self.map_id], h.kind)
        if h.ref in lst:
            self.push_undo({"op": "del", "mid": self.map_id, "kind": h.kind, "ref": h.ref,
                            "idx": lst.index(h.ref), "label": "delete " + self._label(h)})
            lst.remove(h.ref)
        self.dirty.add(self.map_id)
        self.selected = None
        self._rebuild_handles()
        self._rebuild_props()
        self.status = "deleted (Cmd+Z undoes)"

    def duplicate_selected(self):
        h = self.selected
        if not h:
            return
        clone = copy.deepcopy(h.ref)
        clone["x"] = int(clone.get("x", 0)) + 1
        lst = getattr(self.zones[self.map_id], h.kind)
        lst.append(clone)
        self.push_undo({"op": "add", "mid": self.map_id, "kind": h.kind, "ref": clone,
                        "idx": len(lst) - 1, "label": "duplicate " + self._label(h)})
        self.dirty.add(self.map_id)
        self._rebuild_handles()
        self.selected = next((g for g in reversed(self.handles) if g.ref is clone), None)
        self._rebuild_props()
        self.status = "duplicated"

    # --- undo / redo ----------------------------------------------------------
    def push_undo(self, entry):
        entry.setdefault("frame", self.frame)
        self.undo_stack.append(entry)
        if len(self.undo_stack) > 300:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def _coalesce_or_push(self, ref, before, label):
        """Merge rapid edits to the same ref (typing in a field) into one entry."""
        top = self.undo_stack[-1] if self.undo_stack else None
        if (top and top["op"] == "mutate" and top["ref"] is ref
                and self.frame - top["frame"] < 90):
            top["after"] = copy.deepcopy(ref); top["frame"] = self.frame
        else:
            self.push_undo({"op": "mutate", "mid": self.map_id, "ref": ref,
                            "before": before, "after": copy.deepcopy(ref), "label": label})

    def _apply_entry(self, e, reverse):
        if e["op"] == "mutate":
            src = e["before"] if reverse else e["after"]
            e["ref"].clear(); e["ref"].update(copy.deepcopy(src))
            self.dirty.add(e["mid"])
        elif e["op"] in ("add", "del"):
            # add reversed = remove; del reversed = re-insert
            insert = (e["op"] == "add" and not reverse) or (e["op"] == "del" and reverse)
            z = self.zones.get(e["mid"])
            if z is None:
                return
            lst = getattr(z, e["kind"])
            if insert:
                if e["ref"] not in lst:
                    lst.insert(min(e["idx"], len(lst)), e["ref"])
            elif e["ref"] in lst:
                lst.remove(e["ref"])
            self.dirty.add(e["mid"])
        elif e["op"] == "text":
            self.pending_text[e["sym"]] = e["before"] if reverse else e["after"]
        self._rebuild_handles()
        # if the mutated ref is a live NPC, poke the game so it matches the undo
        if e["op"] == "mutate":
            for h in self.handles:
                if h.ref is e["ref"] and h.kind == "objects" and h.lmo_addr:
                    tx, tz = int(h.ref.get("x", 0)), int(h.ref.get("z", 0))
                    R.pin_object(self.e, h.lmo_addr, True); self.pinned.add(h.lmo_addr)
                    R.move_object(self.e, h.lmo_addr, tx, tz); h.live = (tx, tz)
        if self.selected is not None and all(h.ref is not self.selected.ref for h in self.handles):
            self.selected = None
        self._rebuild_props()

    def undo(self, *args):
        if not self.undo_stack:
            self.status = "nothing to undo"; return
        e = self.undo_stack.pop()
        self._apply_entry(e, reverse=True)
        self.redo_stack.append(e)
        self.status = "undid: " + e["label"]

    def redo(self, *args):
        if not self.redo_stack:
            self.status = "nothing to redo"; return
        e = self.redo_stack.pop()
        self._apply_entry(e, reverse=False)
        self.undo_stack.append(e)
        self.status = "redid: " + e["label"]

    # --- projection ----------------------------------------------------------
    def _center(self):
        return (self.player[0] + self.pan[0], self.player[1] + self.pan[1])

    def tile_to_canvas(self, tx, tz):
        cx, cz = self._center()
        return (int((tx - cx) * CELL + self.cw / 2), int((tz - cz) * CELL + self.ch / 2))

    def canvas_to_tile(self, mx, my):
        cx, cz = self._center()
        return (math.floor((mx - self.cw / 2) / CELL + cx),
                math.floor((my - self.ch / 2) / CELL + cz))

    def _fit_canvas(self):
        """Resize the drawlist to fill its (resizable) pane each frame."""
        try:
            w, h = dpg.get_item_rect_size("canvas_panel")
        except Exception:
            return
        w = max(200, int(w) - 4); h = max(200, int(h) - 4)
        if (w, h) != (self.cw, self.ch):
            self.cw, self.ch = w, h
            dpg.configure_item("canvas", width=w, height=h)

    def _tile_of(self, h):
        return h.live if h.live is not None else h.tile

    # --- editing -------------------------------------------------------------
    def _nearest(self, tile):
        tx, tz = tile
        best, bestd = None, 99
        for h in self.handles:
            if h.kind not in self.show:
                continue
            hx, hz = self._tile_of(h)
            if h.kind == "coords":
                w = int(h.ref.get("w", 1)); ht = int(h.ref.get("h", 1))
                if hx <= tx < hx + w and hz <= tz < hz + ht:
                    best, bestd = h, 0
                continue
            d = abs(hx - tx) + abs(hz - tz)
            if d < bestd:
                best, bestd = h, d
        return best if bestd <= 1 else None

    def pick(self, tile):
        self.selected = self._nearest(tile)
        self._rebuild_props()

    def _select(self, h):
        self.selected = h
        self._rebuild_props()

    def move_selected(self, tx, tz):
        h = self.selected
        if not h:
            return
        if h.kind == "objects" and h.lmo_addr:
            # freeze the NPC's movement AI first, so the poked tile STICKS instead
            # of the character wandering back to its patrol.
            if h.lmo_addr not in self.pinned:
                R.pin_object(self.e, h.lmo_addr, True); self.pinned.add(h.lmo_addr)
            R.move_object(self.e, h.lmo_addr, tx, tz)
            h.live = (tx, tz)
        h.set_tile(tx, tz)
        self.dirty.add(self.map_id)

    def _unpin_all(self):
        for addr in self.pinned:
            R.pin_object(self.e, addr, False)
        self.pinned.clear()

    def save_all(self, *args):
        n = 0
        for mid in list(self.dirty):
            z = self.zones.get(mid)
            if z:
                z.save(); n += 1
        self.dirty.clear()
        t = 0
        if self.pending_text:
            import gmm
            for sym, text in self.pending_text.items():
                if gmm.set_text(sym, text):
                    t += 1
            self.pending_text.clear()
        extra = f" + {t} dialogue edit(s)" if t else ""
        self.status = (f"saved {n} map file(s){extra}. "
                       + ("Build ROM to see dialogue/added items in game." if (t or n) else ""))

    def rebuild(self, *args):
        self.save_all()
        if not os.path.exists(BUILD_SCRIPT):
            self.status = f"build script not found: {BUILD_SCRIPT}"; return
        # already building?
        if getattr(self, "_build_proc", None) and self._build_proc.poll() is None:
            self.status = "build already running - see _mapeditor_build.log"; return
        logf = open(BUILD_LOG, "w")
        self._build_proc = subprocess.Popen(
            ["bash", BUILD_SCRIPT], cwd=os.path.dirname(BUILD_SCRIPT),
            stdout=logf, stderr=subprocess.STDOUT)
        self.status = ("building the ROM (~1-5 min)… keep working - it will "
                       "hot-swap into the game automatically when done")

    def _check_build(self):
        """When a build finishes, hot-swap the new ROM into the running game."""
        proc = getattr(self, "_build_proc", None)
        if proc is None or proc.poll() is None:
            return
        code = proc.returncode
        self._build_proc = None
        ok = code == 0
        if ok:
            try:
                ok = "MAKE EXIT=0" in open(BUILD_LOG).read()
            except OSError:
                pass
        if ok:
            self.hot_reload()
        else:
            self.status = f"BUILD FAILED - see _mapeditor_build.log"

    def toggle_mode(self, *args):
        self.mode = "play" if self.mode == "edit" else "edit"
        self.keys_down.clear()             # no stale held keys across a mode switch
        if self.mode == "play":
            self._unpin_all()              # let NPCs move normally while you play
            if self.browsing:              # can't play on a map the player isn't on
                self.browsing = False
                self.pan = [0, 0]
                _, mid = self._sync()
                if mid is not None:
                    self._load_map(mid)
        dpg.set_item_label("btn_mode", self._mode_label())
        self.status = ("playing - walk with arrow keys, Z/X to interact"
                       if self.mode == "play" else "editing - drag things to move them")

    def _mode_label(self):
        return "▶ Playing (G to edit)" if self.mode == "play" else "✎ Editing (G to play)"

    def toggle_bg(self, *args):
        self.show_bg = not self.show_bg

    def reveal_selected(self, *args):
        h = self.selected
        if not h or h.kind != "objects":
            self.status = "pick a character first, then Show/Hide"; return
        fname = str(h.ref.get("eventFlag", "FLAG_NOTHING"))
        if fname == "FLAG_NOTHING":
            self.status = "this character is always visible (no hide switch)"; return
        fid = flag_id(fname)
        cur = R.flag_check(self.e, fid) if fid else None
        if cur is None:
            self.status = "this character's visibility can't be toggled live"; return
        R.flag_write(self.e, fid, 0 if cur else 1)
        verb = "shown" if cur else "hidden"
        self.status = f"{verb} - walk out of this map and back in to see the change"

    # --- behavior / walk wizards ------------------------------------------------
    WIZ_BEH = [("stand", "Stands still"), ("wander", "Wanders around"),
               ("pace_lr", "Paces left and right"), ("pace_ud", "Paces up and down")]

    def _wiz_reset(self):
        if dpg.does_item_exist("wizwin"):
            dpg.delete_item("wizwin")
        self.pick_dest = None

    def _zone_and_map(self):
        z = self.zones.get(self.map_id)
        return z, (D.map_name_of(z) if z is not None else None)

    def open_behavior_wizard(self, h):
        self._wiz_reset()
        z, mn = self._zone_and_map()
        if not mn:
            self.status = "this map has no scripts to edit"; return
        moments = BW.list_moments(mn)
        name = D.humanize_sprite(h.ref.get("spriteId", "?"))
        self._wiz = {"h": h, "mn": mn, "moments": moments, "mode": "behavior"}
        labels = [l for _, l in self.WIZ_BEH]
        with dpg.window(tag="wizwin", label=f"How should {name} behave?", width=560,
                        pos=(160, 120), no_collapse=True, on_close=lambda *a: self._wiz_reset()):
            dpg.add_text("Right now they should…", color=(150, 160, 175))
            dpg.add_radio_button(labels, tag="wiz_now", default_value=labels[0],
                                 callback=self._wiz_preview)
            dpg.add_separator()
            dpg.add_text("For how long?", color=(150, 160, 175))
            when = ["Always"] + (["Until a story moment, then change…"] if moments else [])
            dpg.add_radio_button(when, tag="wiz_when", default_value="Always",
                                 callback=self._wiz_preview)
            if moments:
                dpg.add_combo([m.desc for m in moments], tag="wiz_moment", width=-1,
                              default_value=moments[-1].desc, label="",
                              callback=self._wiz_preview)
                dpg.add_text("…then they should:", color=(150, 160, 175), tag="wiz_then_lbl")
                dpg.add_radio_button(labels, tag="wiz_then", default_value=labels[1],
                                     callback=self._wiz_preview)
            dpg.add_separator()
            dpg.add_text("", tag="wiz_preview", wrap=520, color=(140, 210, 160))
            dpg.add_button(label="Apply", width=-1, callback=self._wiz_apply_behavior)
            dpg.add_text("Nothing changes in the game until you press Build ROM.",
                         color=(120, 135, 155), wrap=520)
        self._wiz_preview()

    def _beh_key(self, tag):
        val = dpg.get_value(tag)
        return next(k for k, l in self.WIZ_BEH if l == val)

    def _wiz_moment(self):
        d = dpg.get_value("wiz_moment") if dpg.does_item_exist("wiz_moment") else None
        return next((m for m in self._wiz.get("moments", []) if m.desc == d), None)

    def _wiz_preview(self, *args):
        if not dpg.does_item_exist("wiz_preview"):
            return
        h = self._wiz["h"]
        name = D.humanize_sprite(h.ref.get("spriteId", "?"))
        now = dpg.get_value("wiz_now")
        if dpg.get_value("wiz_when") == "Always" or not self._wiz["moments"]:
            txt = f"{name} will always: {now.lower()}, at ({h.ref.get('x')},{h.ref.get('z')})."
            show_then = False
        else:
            mo = self._wiz_moment()
            txt = (f"{name}: {now.lower()} at ({h.ref.get('x')},{h.ref.get('z')}) until "
                   f"{mo.desc if mo else '?'}.\nAfter that: "
                   f"{dpg.get_value('wiz_then').lower()}, forever.")
            show_then = True
        for t in ("wiz_moment", "wiz_then", "wiz_then_lbl"):
            if dpg.does_item_exist(t):
                dpg.configure_item(t, show=show_then)
        dpg.set_value("wiz_preview", txt)

    def _wiz_apply_behavior(self, *args):
        h = self._wiz["h"]; mn = self._wiz["mn"]
        z = self.zones.get(self.map_id)
        try:
            if dpg.get_value("wiz_when") == "Always" or not self._wiz["moments"]:
                note = BW.simple_behavior(h.ref, self._beh_key("wiz_now"))
                z.save(); self.dirty.discard(self.map_id)
                self.status = f"✓ {note}. Press Build ROM to make it real."
            else:
                if self.map_id in self.dirty:      # don't lose unsaved edits
                    z.save(); self.dirty.discard(self.map_id)
                plan = BW.behavior_switch(mn, z.path, str(h.ref.get("id")),
                                          self._beh_key("wiz_now"),
                                          self._beh_key("wiz_then"),
                                          self._wiz_moment())
                plan.apply()
                self.zones.pop(self.map_id, None)
                self._load_map(self.map_id)
                self.status = "✓ " + plan.summary[0] + "  Press Build ROM to make it real."
        except Exception as e:
            self.status = f"could not apply: {e}"
        self._wiz_reset()

    def open_walk_wizard(self, h):
        self._wiz_reset()
        z, mn = self._zone_and_map()
        if not mn:
            self.status = "this map has no scripts to edit"; return
        moments = BW.list_moments(mn)
        if not moments:
            self.status = "this map has no story scenes to attach a walk to"; return
        name = D.humanize_sprite(h.ref.get("spriteId", "?"))
        self._wiz = {"h": h, "mn": mn, "moments": moments, "mode": "walk", "dest": None}
        with dpg.window(tag="wizwin", label=f"Make {name} walk somewhere", width=560,
                        pos=(160, 120), no_collapse=True, on_close=lambda *a: self._wiz_reset()):
            dpg.add_text("During which scene?", color=(150, 160, 175))
            dpg.add_combo([m.desc for m in moments], tag="wiz_moment", width=-1,
                          default_value=moments[-1].desc)
            dpg.add_radio_button(["when the scene starts", "when the scene ends"],
                                 tag="wiz_walkwhen", default_value="when the scene starts",
                                 horizontal=True)
            dpg.add_separator()
            dpg.add_text("Now click the tile they should walk to, on the map.",
                         tag="wiz_dest_lbl", color=(255, 210, 130), wrap=520)
            dpg.add_combo(["(no turn)", "up", "down", "left", "right"], tag="wiz_face",
                          default_value="(no turn)", label="then face", width=160)
            dpg.add_button(label="Apply", width=-1, enabled=False, tag="wiz_walk_apply",
                           callback=self._wiz_apply_walk)
            dpg.add_text("Nothing changes in the game until you press Build ROM.",
                         color=(120, 135, 155), wrap=520)
        self.pick_dest = self._wiz_dest_picked
        self.status = "click the destination tile on the map"

    def _wiz_dest_picked(self, tile):
        h = self._wiz.get("h")
        if not h or not dpg.does_item_exist("wiz_dest_lbl"):
            return
        self._wiz["dest"] = tile
        sx, sz = int(h.ref.get("x", 0)), int(h.ref.get("z", 0))
        dpg.set_value("wiz_dest_lbl",
                      f"They will walk from ({sx},{sz}) to ({tile[0]},{tile[1]}).  "
                      "Click another tile to change it.")
        dpg.configure_item("wiz_walk_apply", enabled=True)
        self.status = "destination set - press Apply in the wizard"

    def _wiz_apply_walk(self, *args):
        h = self._wiz["h"]; mn = self._wiz["mn"]; dest = self._wiz.get("dest")
        if not dest:
            return
        face = dpg.get_value("wiz_face")
        try:
            plan = BW.add_walk(
                mn, str(h.ref.get("id")), self._wiz_moment(),
                "start" if "start" in dpg.get_value("wiz_walkwhen") else "end",
                (int(h.ref.get("x", 0)), int(h.ref.get("z", 0))), dest,
                face=None if face == "(no turn)" else face)
            plan.apply()
            self.status = "✓ " + plan.summary[0] + "  Press Build ROM to make it real."
        except Exception as e:
            self.status = f"could not add walk: {e}"
        self._wiz_reset()

    # --- play input ----------------------------------------------------------
    def _key_down(self, sender, app_data, user_data):
        if self._typing():
            return
        self.keys_down.add(user_data)

    def _key_up(self, sender, app_data, user_data):
        self.keys_down.discard(user_data)

    def apply_keys(self):
        mask = 0
        for gk in self.keys_down:
            mask |= keymask(gk)
        self.e.emu.input.keypad_update(mask)

    # --- hotkey guards ---------------------------------------------------------
    def _typing(self):
        return self.frame - self._typing_frame <= 2

    def _hot(self, fn):
        """Wrap a single-letter hotkey so it never fires while you're typing."""
        def cb(*args):
            if not self._typing():
                fn()
        return cb

    def _cmd_down(self):
        return any(dpg.is_key_down(k) for k in
                   (dpg.mvKey_LWin, dpg.mvKey_RWin, dpg.mvKey_LControl, dpg.mvKey_RControl))

    def _on_z_key(self, *args):
        """Z alone = game button (play mode); Cmd+Z = undo; Shift+Cmd+Z = redo."""
        if self._typing() or not self._cmd_down() or self.mode == "play":
            return
        if dpg.is_key_down(dpg.mvKey_LShift) or dpg.is_key_down(dpg.mvKey_RShift):
            self.redo()
        else:
            self.undo()

    # --- map navigator ----------------------------------------------------------
    def toggle_nav(self, *args):
        show = not dpg.is_item_shown("navwin")
        dpg.configure_item("navwin", show=show)
        if show:
            self._nav_refresh()
            dpg.focus_item("nav_filter")

    def _auto_ckpt(self, mid):
        return os.path.join(AUTO_DIR, f"map_{mid:03d}.dsv")

    def _save_auto_ckpt(self):
        """Snapshot the current map so the navigator can jump back here instantly."""
        if self.map_id is None or self.browsing:
            return
        try:
            self.e.savestate(self._auto_ckpt(self.map_id))
        except Exception:
            pass

    def _after_state_load(self):
        """Housekeeping after any loadstate: stale RAM handles must be dropped."""
        self.pinned.clear()
        self.keys_down.clear()
        self.browsing = False
        entries, mid = self._sync()
        if mid is not None:
            self._load_map(mid)

    def reset_game(self, *args):
        p = default_state()
        if not p:
            self.status = "no checkpoint available"; return
        self.e.loadstate(p); self.e.wait(4)
        self._after_state_load()
        self.status = "restarted from your last good spot"

    def goto_map(self, mid, focus_idx=None, focus_kind=None):
        if mid == self.map_id and not self.browsing:
            self.status = "you're already on this map"
        elif os.path.exists(self._auto_ckpt(mid)):
            self.e.loadstate(self._auto_ckpt(mid)); self.e.wait(4)
            self._after_state_load()
            self.status = f"jumped to {self._map_name()} (visited earlier this session)"
        else:
            # view-only: show the map's events from its files; the game stays put
            self.browsing = True
            self._load_map(mid)
            z = self.zones.get(mid)
            pts = [(int(r.get("x", 0)), int(r.get("z", 0)))
                   for k in KINDS for r in (getattr(z, k) if z else [])]
            if pts:
                cx = sum(p[0] for p in pts) // len(pts)
                cz = sum(p[1] for p in pts) // len(pts)
                self.pan = [cx - self.player[0], cz - self.player[1]]
            self.status = ("viewing this map from its files (view-only) - walk there "
                           "in Play mode once to enable instant jumping")
        # focus a specific event (from dialogue search)
        if focus_kind is not None and focus_idx is not None:
            for h in self.handles:
                if h.kind == focus_kind and h.idx == focus_idx:
                    self._select(h)
                    hx, hz = self._tile_of(h)
                    self.pan = [hx - self.player[0], hz - self.player[1]]
                    break

    def _nav_refresh(self, *args):
        needle = (dpg.get_value("nav_filter") or "").strip().lower()
        mode = dpg.get_value("nav_mode")
        self._nav_map = {}
        items = []
        if mode == "Maps":
            here = self.map_id
            for mid, name in map_list():
                label = f"{D.humanize_map(name)}   (map {mid})"
                if mid == here:
                    label = "▶ " + label
                if needle and needle not in label.lower():
                    continue
                if os.path.exists(self._auto_ckpt(mid)):
                    label += "   ●visited"
                self._nav_map[label] = ("map", mid, None, None)
                items.append(label)
                if len(items) >= 400:
                    break
            dpg.set_value("nav_status", f"{len(items)} maps")
        else:
            rows = self.search_rows
            if rows is None:
                dpg.set_value("nav_status", self.search_status)
            elif not needle:
                dpg.set_value("nav_status", f"{len(rows)} lines - type words to search")
            else:
                for r in rows:
                    if needle in r["text"].lower():
                        snip = r["text"][:70] + ("…" if len(r["text"]) > 70 else "")
                        label = f'{D.humanize_map(r["name"])} · "{snip}"'
                        n = 2
                        base = label
                        while label in self._nav_map:
                            label = f"{base} ({n})"; n += 1
                        self._nav_map[label] = ("map", r["mid"], r["idx"], r["kind"])
                        items.append(label)
                        if len(items) >= 200:
                            break
                dpg.set_value("nav_status", f"{len(items)} match(es)")
        dpg.configure_item("nav_list", items=items)

    def _nav_pick(self, sender, app_data, user_data=None):
        act = self._nav_map.get(app_data)
        if not act:
            return
        _, mid, idx, kind = act
        self.goto_map(mid, focus_idx=idx, focus_kind=kind)

    # --- dialogue search index (background thread) -------------------------------
    def _index_dialogue(self):
        try:
            rows = []
            maps = map_list()
            for i, (mid, name) in enumerate(maps):
                if i % 25 == 0:
                    self.search_status = f"building dialogue index… {i}/{len(maps)}"
                p = zone_event_path(mid)
                if not p:
                    continue
                try:
                    z = ZoneEvents.load(p)
                except Exception:
                    continue
                mn = D.map_name_of(z)
                if not mn:
                    continue
                for kind in ("objects", "coords", "bgs"):
                    for idx, ref in enumerate(getattr(z, kind)):
                        try:
                            items = D.dialogue_items(mn, ref.get("scriptId", 0))
                        except Exception:
                            items = []
                        for it in items:
                            rows.append({"mid": mid, "name": name, "kind": kind,
                                         "idx": idx, "text": it["text"]})
            self.search_rows = rows
            self.search_status = f"{len(rows)} dialogue lines indexed"
        except Exception:
            self.search_status = "index failed (see log)"
            self._log("INDEX ERROR:\n" + traceback.format_exc())

    # --- hot reload (new ROM into the running game) ------------------------------
    def _clear_source_caches(self):
        for fn in (D._header_syms, D._script_file, D._bodies, D._msg_texts, D._flag_index):
            try:
                fn.cache_clear()
            except Exception:
                pass
        self.zones = {}
        self.search_rows = None
        self.search_status = "re-indexing after build…"
        threading.Thread(target=self._index_dialogue, daemon=True).start()

    def _frozen(self):
        """True if the game no longer animates or responds (stale-code state)."""
        def hsh():
            return hashlib.md5(bytes(self.e.emu.display_buffer_as_rgbx())).hexdigest()
        self._sync(); p0, h0 = self.player, hsh()
        for k in (Keys.KEY_DOWN, Keys.KEY_UP):
            for _ in range(45):
                self.e.emu.input.keypad_update(keymask(k)); self.e.emu.cycle(False)
        self.e.emu.input.keypad_update(0)
        self._sync()
        return hsh() == h0 and self.player == p0

    def hot_reload(self):
        self.status = "swapping in the new ROM…"
        tmp = os.path.join(AUTO_DIR, "_hot_reload_tmp.dsv")
        try:
            self.e.savestate(tmp)
            self.e.emu.open(ROM_PATH); self.e.wait(8)
            self.e.loadstate(tmp); self.e.wait(6)
            if not self._frozen():
                self.e.loadstate(tmp); self.e.wait(4)   # undo the freeze-test steps
                self._clear_source_caches()
                self._after_state_load()
                self.status = "✓ new ROM live - your changes are now in the game"
                return
            # code changed -> old RAM can't run it; boot a fresh save in the background
            self.status = ("code changed: building a fresh save (1-3 min)… "
                           "game will restart at the player's house")
            logf = open(os.path.join(ROOT, "_mapeditor_fresh.log"), "w")
            self._fresh_proc = subprocess.Popen(
                [sys.executable, FRESH_SCRIPT], stdout=logf, stderr=subprocess.STDOUT)
        except Exception:
            self._log("HOT RELOAD ERROR:\n" + traceback.format_exc())
            self.status = "reload hiccup - use Restart spot, or relaunch the editor"

    def _check_fresh(self):
        proc = self._fresh_proc
        if proc is None or proc.poll() is None:
            return
        code = proc.returncode
        self._fresh_proc = None
        if code == 0 and os.path.exists(FRESH_STATE):
            try:
                self.e.loadstate(FRESH_STATE); self.e.wait(4)
                self.stale_state = False
                self._clear_source_caches()
                self._after_state_load()
                self._save_auto_ckpt()
                self.status = "✓ fresh save ready - you're at the house with the new ROM"
            except Exception:
                self.status = "fresh save made - use Restart spot to load it"
        else:
            self.status = f"fresh-save script failed (exit {code}) - see _mapeditor_fresh.log"

    # =====================================================================
    #  UI
    # =====================================================================
    def build_ui(self):
        dpg.create_context()
        self._load_font()
        self._theme()
        with dpg.texture_registry():
            dpg.add_raw_texture(DS_W, DS_H, self._frame_floats(),
                                format=dpg.mvFormat_Float_rgba, tag="ds")

        # focus tracker: while any text/number box is active, app hotkeys stay quiet
        with dpg.item_handler_registry(tag="typing_reg"):
            dpg.add_item_active_handler(
                callback=lambda *a: setattr(self, "_typing_frame", self.frame))

        with dpg.window(tag="main", no_scrollbar=True):
            # toolbar
            with dpg.group(horizontal=True):
                dpg.add_button(label=self._mode_label(), tag="btn_mode", callback=self.toggle_mode)
                dpg.add_button(label="Save", callback=self.save_all)
                dpg.add_button(label="Build ROM", callback=self.rebuild)
                dpg.add_button(label="Undo", callback=self.undo)
                dpg.add_button(label="Redo", callback=self.redo)
                dpg.add_button(label="Maps & Find", callback=self.toggle_nav)
                dpg.add_button(label="Restart spot", callback=self.reset_game)
                dpg.add_checkbox(label="Show map picture", default_value=True,
                                 callback=lambda s, a, u=None: setattr(self, "show_bg", a))
                dpg.add_spacer(width=16)
                dpg.add_text("", tag="map_label", color=(150, 200, 255))
            dpg.add_spacer(height=2)
            # resizable 3-pane split (drag the dividers)
            with dpg.table(header_row=False, resizable=True, borders_innerV=True,
                           borders_outerV=False, policy=dpg.mvTable_SizingStretchProp,
                           height=-1, tag="split"):
                dpg.add_table_column(init_width_or_weight=0.26)   # info
                dpg.add_table_column(init_width_or_weight=0.50)   # map
                dpg.add_table_column(init_width_or_weight=0.24)   # game
                with dpg.table_row():
                    # ---- info pane -------------------------------------------
                    with dpg.child_window(border=False, tag="left_panel"):
                        dpg.add_text("SHOW ON MAP", color=(130, 145, 165))
                        for k in KINDS:
                            dpg.add_checkbox(label=KIND_LABEL.get(k, k), default_value=True,
                                             tag=f"layer_{k}", callback=self._on_layer_toggle)
                        dpg.add_text("Right-click the map to add or edit things.",
                                     color=(120, 140, 160), wrap=0)
                        dpg.add_separator()
                        dpg.add_text("WHAT IS THIS?", color=(130, 145, 165))
                        with dpg.child_window(height=-1, tag="props_area", border=False):
                            dpg.add_text("Click anything on the map to see what it is,\n"
                                         "in plain English.", color=(140, 150, 160), wrap=0)
                    # ---- map pane --------------------------------------------
                    with dpg.child_window(border=False, tag="canvas_panel", no_scrollbar=True):
                        with dpg.drawlist(width=self.cw, height=self.ch, tag="canvas"):
                            dpg.add_draw_layer(tag="layer")
                    # ---- game pane -------------------------------------------
                    with dpg.child_window(border=False, tag="game_panel"):
                        dpg.add_text("THE GAME (live)", color=(130, 145, 165))
                        dpg.add_image("ds", width=DS_W, height=DS_H, tag="ds_img")
                        dpg.add_text("Press G to play: arrows walk, Z = A, X = B.",
                                     color=(120, 140, 160), wrap=0)
                        dpg.add_separator()
                        dpg.add_text("", tag="status_text", color=(120, 200, 140), wrap=0)
        dpg.set_primary_window("main", True)

        # floating right-click context menu (populated on open)
        with dpg.window(tag="ctxwin", show=False, no_title_bar=True, no_resize=True,
                        no_move=True, no_collapse=True, autosize=True, no_scrollbar=True):
            pass

        # Maps & Find window (toggled from the toolbar)
        with dpg.window(tag="navwin", label="Maps & Find", show=False, width=460,
                        height=560, pos=(120, 90), on_close=lambda *a: None):
            self._guard_input(dpg.add_input_text(
                tag="nav_filter", width=-1, callback=self._nav_refresh,
                hint="type a map name, or words someone says…"))
            with dpg.group(horizontal=True):
                dpg.add_radio_button(("Maps", "Dialogue"), tag="nav_mode", horizontal=True,
                                     default_value="Maps", callback=self._nav_refresh)
                dpg.add_text("", tag="nav_status", color=(140, 150, 165))
            dpg.add_listbox(tag="nav_list", items=[], num_items=17, width=-1,
                            callback=self._nav_pick)
            dpg.add_text("Click a map to jump there. Maps you've visited this session\n"
                         "jump instantly; others open in view-only mode.",
                         color=(120, 135, 155))

        with dpg.handler_registry():
            dpg.add_key_release_handler(dpg.mvKey_G, callback=self._hot(self.toggle_mode))
            dpg.add_key_release_handler(dpg.mvKey_S, callback=self._hot(self.save_all))
            dpg.add_key_release_handler(dpg.mvKey_R, callback=self._hot(self.rebuild))
            dpg.add_key_release_handler(dpg.mvKey_F, callback=self._hot(self.reveal_selected))
            dpg.add_key_release_handler(dpg.mvKey_B, callback=self._hot(self.toggle_bg))
            dpg.add_key_release_handler(dpg.mvKey_Z, callback=self._on_z_key)
            # play-mode movement: track held keys via down/up handlers (reliable),
            # then apply_keys() turns the held set into the emulator keypad each frame
            for dpgkey, gamekey in PLAY_KEYS.items():
                dpg.add_key_down_handler(dpgkey, user_data=gamekey, callback=self._key_down)
                dpg.add_key_release_handler(dpgkey, user_data=gamekey, callback=self._key_up)

        dpg.create_viewport(title="Apocrypha Map Editor", width=1560, height=940,
                            min_width=900, min_height=600)
        dpg.setup_dearpygui()
        dpg.show_viewport()

    def _load_font(self):
        path = next((p for p in (
            "/Library/Fonts/Arial Unicode.ttf",
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc") if os.path.exists(p)), None)
        if not path:
            return
        try:
            with dpg.font_registry():
                with dpg.font(path, 19) as f:
                    dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
                    # smart quotes / dashes / ellipsis + arrows/marks used in the UI
                    dpg.add_font_chars([0x2018, 0x2019, 0x201C, 0x201D, 0x2013,
                                        0x2014, 0x2026, 0x2192, 0x25CF, 0x25C6,
                                        0x25A0, 0x2605, 0x2022, 0x25B6, 0x270E])
            dpg.bind_font(f)
        except Exception:
            pass

    def _theme(self):
        with dpg.theme() as t:
            with dpg.theme_component(dpg.mvAll):
                c = dpg.add_theme_color
                c(dpg.mvThemeCol_WindowBg, (18, 20, 26))
                c(dpg.mvThemeCol_ChildBg, (24, 27, 34))
                c(dpg.mvThemeCol_Border, (44, 49, 60))
                c(dpg.mvThemeCol_Text, (222, 228, 236))
                c(dpg.mvThemeCol_TextDisabled, (120, 128, 140))
                c(dpg.mvThemeCol_Button, (46, 52, 66))
                c(dpg.mvThemeCol_ButtonHovered, (64, 120, 200))
                c(dpg.mvThemeCol_ButtonActive, (74, 140, 230))
                c(dpg.mvThemeCol_FrameBg, (32, 36, 46))
                c(dpg.mvThemeCol_FrameBgHovered, (44, 50, 64))
                c(dpg.mvThemeCol_FrameBgActive, (52, 60, 78))
                c(dpg.mvThemeCol_CheckMark, (90, 190, 255))
                c(dpg.mvThemeCol_Header, (46, 88, 150))
                c(dpg.mvThemeCol_HeaderHovered, (56, 104, 172))
                c(dpg.mvThemeCol_Separator, (44, 49, 60))
                c(dpg.mvThemeCol_TableBorderLight, (44, 49, 60))
                c(dpg.mvThemeCol_ScrollbarBg, (18, 20, 26))
                c(dpg.mvThemeCol_ScrollbarGrab, (52, 58, 72))
                c(dpg.mvThemeCol_TitleBgActive, (30, 60, 110))
                s = dpg.add_theme_style
                s(dpg.mvStyleVar_FrameRounding, 6)
                s(dpg.mvStyleVar_ChildRounding, 8)
                s(dpg.mvStyleVar_GrabRounding, 6)
                s(dpg.mvStyleVar_ScrollbarRounding, 6)
                s(dpg.mvStyleVar_WindowPadding, 14, 12)
                s(dpg.mvStyleVar_ItemSpacing, 9, 8)
                s(dpg.mvStyleVar_FramePadding, 10, 6)
                s(dpg.mvStyleVar_CellPadding, 8, 4)
                s(dpg.mvStyleVar_ScrollbarSize, 13)
        dpg.bind_theme(t)

    def _on_layer_toggle(self, sender, app_data, user_data=None):
        kind = dpg.get_item_alias(sender).replace("layer_", "")
        if app_data:
            self.show.add(kind)
        else:
            self.show.discard(kind)

    def _make_setter(self, ref, key, is_int):
        def cb(sender, app_data, user_data=None):
            before = copy.deepcopy(ref)
            ref[key] = int(app_data) if is_int else app_data
            self._coalesce_or_push(ref, before, f"edit {key}")
            self.dirty.add(self.map_id)
            h = self.selected
            if h and h.ref is ref and key in ("x", "z") and h.kind == "objects" and h.lmo_addr:
                nx, nz = int(ref.get("x", 0)), int(ref.get("z", 0))
                R.move_object(self.e, h.lmo_addr, nx, nz); h.live = (nx, nz)
        return cb

    def _guard_input(self, tag):
        """Mark a widget so its keystrokes never trigger app hotkeys."""
        try:
            dpg.bind_item_handler_registry(tag, "typing_reg")
        except Exception:
            pass
        return tag

    def _prop_field(self, parent, ref, key):
        val = ref.get(key, 0)
        is_int = isinstance(val, int) and not isinstance(val, bool)
        cb = self._make_setter(ref, key, is_int)
        if is_int:
            self._guard_input(dpg.add_input_int(label=key, default_value=int(val),
                              parent=parent, width=120, step=0, callback=cb))
        else:
            self._guard_input(dpg.add_input_text(label=key, default_value=str(val),
                              parent=parent, width=170, callback=cb))

    def _rebuild_props(self):
        if not dpg.does_item_exist("props_area"):
            return
        dpg.delete_item("props_area", children_only=True)
        P = "props_area"
        h = self.selected
        if h is None:
            dpg.add_text("Click anything on the map to see what it is,\n"
                         "in plain English.", parent=P, color=(140, 150, 160), wrap=0)
            return
        z = self.zones.get(self.map_id)
        desc = D.describe(z, h.kind, h.ref) if z is not None else None
        col = KIND_COLOR[h.kind]
        mn = D.map_name_of(z) if z is not None else None
        # headline
        title = f"{desc.icon}  {desc.title}" if desc else h.kind[:-1]
        dpg.add_text(title, parent=P, color=col, wrap=0)
        if desc:
            for ln in desc.lines:
                dpg.add_text(ln, parent=P, color=(200, 208, 218), wrap=0, bullet=True)
        # live status for characters
        if h.kind == "objects":
            self._live_note(P, h)
        # editable dialogue + story-step sequence
        if mn and h.kind in ("objects", "coords", "bgs"):
            self._dialogue_section(P, mn, h)
            self._steps_section(P, mn, h)
        # trigger size
        if h.kind == "coords":
            self._size_section(P, h)
        dpg.add_separator(parent=P)
        # plain actions
        dpg.add_text("ACTIONS", parent=P, color=(130, 145, 165))
        with dpg.group(horizontal=True, parent=P):
            if h.kind == "objects":
                dpg.add_button(label="Show / Hide", callback=self.reveal_selected)
            dpg.add_button(label="Duplicate", callback=lambda *a: self.duplicate_selected())
            dpg.add_button(label="Delete", callback=lambda *a: self.delete_selected())
        dpg.add_text("Tip: drag it on the map to move it.", parent=P,
                     color=(120, 140, 160), wrap=0)
        # raw values (folded away by default)
        dpg.add_separator(parent=P)
        dpg.add_checkbox(label="Show raw values (advanced)", default_value=self.show_raw,
                         parent=P, callback=self._toggle_raw)
        if self.show_raw:
            dpg.add_text("These are the exact game fields. Edit with care.",
                         parent=P, color=(150, 160, 170), wrap=0)
            for key in FIELD_ORDER.get(h.kind, []):
                self._prop_field(P, h.ref, key)

    # --- dialogue editing ----------------------------------------------------
    def _dialogue_section(self, P, mn, h):
        items = []
        try:
            items = D.dialogue_items(mn, h.ref.get("scriptId", 0))
        except Exception:
            pass
        if not items:
            return
        dpg.add_separator(parent=P)
        dpg.add_text("WHAT IT SAYS  (edit to change)", parent=P, color=(130, 145, 165))
        for it in items:
            with dpg.group(parent=P):
                shown = self.pending_text.get(it["sym"], it["raw"])
                self._guard_input(dpg.add_input_text(
                    default_value=shown, multiline=True, width=-1, height=64,
                    callback=self._make_dialogue_setter(it["sym"], it["raw"])))
        dpg.add_text("\\n = new line,  \\r = next text box.  Save + Build to apply.",
                     parent=P, color=(120, 135, 155), wrap=0)

    def _make_dialogue_setter(self, sym, original):
        def cb(sender, app_data, user_data=None):
            before = self.pending_text.get(sym, original)
            top = self.undo_stack[-1] if self.undo_stack else None
            if top and top["op"] == "text" and top["sym"] == sym and self.frame - top["frame"] < 90:
                top["after"] = app_data; top["frame"] = self.frame
            else:
                self.push_undo({"op": "text", "sym": sym, "before": before,
                                "after": app_data, "label": "edit dialogue"})
            self.pending_text[sym] = app_data
            self.status = "dialogue edited - Save, then Build ROM to hear it in game"
        return cb

    def _steps_section(self, P, mn, h):
        steps = []
        try:
            steps = D.script_steps(mn, h.ref.get("scriptId", 0))
        except Exception:
            pass
        if not steps:
            return
        with dpg.tree_node(label="Step-by-step (what happens)", parent=P, default_open=False):
            for _icon, text in steps[:30]:
                dpg.add_text(text, wrap=0, bullet=True, color=(190, 198, 210))

    def _size_section(self, P, h):
        dpg.add_separator(parent=P)
        dpg.add_text("TRIGGER SIZE", parent=P, color=(130, 145, 165))
        with dpg.group(horizontal=True, parent=P):
            self._guard_input(dpg.add_input_int(
                label="wide", default_value=int(h.ref.get("w", 1) or 1),
                width=110, step=1, min_value=1, min_clamped=True,
                callback=self._make_size_setter("w")))
            self._guard_input(dpg.add_input_int(
                label="tall", default_value=int(h.ref.get("h", 1) or 1),
                width=110, step=1, min_value=1, min_clamped=True,
                callback=self._make_size_setter("h")))
        dpg.add_text("Or drag the square handle at the trigger's corner on the map.",
                     parent=P, color=(120, 135, 155), wrap=0)

    def _make_size_setter(self, key):
        def cb(sender, app_data, user_data=None):
            if self.selected:
                before = copy.deepcopy(self.selected.ref)
                self.selected.ref[key] = max(1, int(app_data))
                self._coalesce_or_push(self.selected.ref, before, "resize trigger")
                self.dirty.add(self.map_id)
        return cb

    def _toggle_raw(self, sender, app_data, user_data=None):
        self.show_raw = bool(app_data)
        self._rebuild_props()

    def _live_note(self, P, h):
        if h.lmo_addr:
            moved = h.live is not None and tuple(h.live) != tuple(h.tile)
            if moved:
                dpg.add_text(f"● On screen now, moved to {tuple(h.live)} (frozen so it stays).",
                             parent=P, color=(255, 205, 120), wrap=0, bullet=True)
            else:
                dpg.add_text("● On screen in the game right now.",
                             parent=P, color=(120, 230, 140), wrap=0, bullet=True)
        else:
            dpg.add_text("● Not on screen right now (hidden by the story, or off-camera). "
                         "Use Show / Hide, then re-enter the map.",
                         parent=P, color=(180, 160, 120), wrap=0, bullet=True)

    # --- canvas rendering ----------------------------------------------------
    def _redraw_canvas(self):
        dpg.delete_item("layer", children_only=True)
        p = "layer"
        W, H = self.cw, self.ch
        dpg.draw_rectangle((0, 0), (W, H), fill=(20, 22, 28), color=(20, 22, 28), parent=p)
        # map background (live DS top screen), aligned to player anchor
        if self.show_bg and not self.browsing:
            scale = CELL / 16.0
            pgx, pgy = self.tile_to_canvas(*self.player)
            bx = pgx + CELL / 2 - PLAYER_PX_X * scale
            by = pgy + CELL / 2 - PLAYER_PX_Y * scale
            dpg.draw_image("ds", (bx, by), (bx + 256 * scale, by + 192 * scale),
                           uv_min=(0, 0), uv_max=(1, 0.5), parent=p)
            dpg.draw_rectangle((0, 0), (W, H), fill=(12, 14, 20, 90), color=(0, 0, 0, 0), parent=p)
        # grid lines
        cx, cz = self._center()
        ox = int((-(cx) * CELL + W / 2) % CELL)
        oy = int((-(cz) * CELL + H / 2) % CELL)
        for x in range(ox, int(W), CELL):
            dpg.draw_line((x, 0), (x, H), color=(255, 255, 255, 16), parent=p)
        for y in range(oy, int(H), CELL):
            dpg.draw_line((0, y), (W, y), color=(255, 255, 255, 16), parent=p)
        # player cell (hidden while viewing another map's files)
        if not self.browsing:
            pgx, pgy = self.tile_to_canvas(*self.player)
            dpg.draw_rectangle((pgx, pgy), (pgx + CELL, pgy + CELL), color=(150, 200, 255), thickness=2, parent=p)
            dpg.draw_text((pgx + 2, pgy - 15), "YOU", size=13, color=(190, 220, 255), parent=p)
        # events
        for h in self.handles:
            if h.kind not in self.show:
                continue
            self._draw_handle(h, p)
        # sprite-shape outlines: hover (subtle) then selection (bright)
        if self.hover is not None and self.hover is not self.selected and self.hover.kind in self.show:
            a, b = self._shape_bbox(self.hover)
            dpg.draw_rectangle(a, b, color=(255, 255, 255, 130), thickness=2, rounding=3, parent=p)
        if self.selected is not None:
            a, b = self._shape_bbox(self.selected)
            dpg.draw_rectangle(a, b, color=(255, 235, 120), thickness=3, rounding=3, parent=p)
            # resize handle for triggers (drag to reshape)
            if self.selected.kind == "coords":
                hx, hy = b
                dpg.draw_rectangle((hx - 9, hy - 9), (hx + 1, hy + 1),
                                   fill=(255, 235, 120), color=(30, 30, 30), parent=p)
        dpg.draw_rectangle((0, 0), (W - 1, H - 1), color=(52, 58, 72), parent=p)

    def _shape_bbox(self, h):
        """Canvas bounding box of the event's real footprint (NPC sprite ~1 tile
        wide x 2 tall standing on the bottom tile; triggers span w x h; else 1 tile)."""
        tx, tz = self._tile_of(h)
        gx, gy = self.tile_to_canvas(tx, tz)
        if h.kind == "objects":
            return (gx, gy - CELL), (gx + CELL, gy + CELL)
        if h.kind == "coords":
            w = int(h.ref.get("w", 1)); ht = int(h.ref.get("h", 1))
            return (gx, gy), (gx + w * CELL, gy + ht * CELL)
        return (gx, gy), (gx + CELL, gy + CELL)

    def _draw_handle(self, h, p):
        tx, tz = self._tile_of(h)
        gx, gy = self.tile_to_canvas(tx, tz)
        if gx < -CELL or gx > CW or gy < -CELL or gy > CH:
            return
        sel = h is self.selected
        dim = h.kind == "objects" and h.live is None
        col = _rgba(h.kind, dim=dim)
        cx_, cy_ = gx + CELL // 2, gy + CELL // 2
        if h.kind == "objects":
            dpg.draw_circle((cx_, cy_), CELL // 2 - 3, fill=col, color=col, parent=p)
        elif h.kind == "warps":
            dpg.draw_rectangle((gx + 4, gy + 4), (gx + CELL - 4, gy + CELL - 4), fill=col, color=col, parent=p)
        elif h.kind == "coords":
            w = int(h.ref.get("w", 1)); ht = int(h.ref.get("h", 1))
            dpg.draw_rectangle((gx, gy), (gx + w * CELL, gy + ht * CELL),
                               fill=_rgba(h.kind, 60), color=col, thickness=1, parent=p)
        else:
            dpg.draw_polygon([(cx_, gy + 4), (gx + CELL - 4, cy_), (cx_, gy + CELL - 4), (gx + 4, cy_)],
                             fill=col, color=col, parent=p)
        # label objects/warps + any selection
        if sel or h.kind in ("objects", "warps"):
            lbl = self._label(h)
            dpg.draw_text((gx, gy - 14), lbl, size=12, color=col, parent=p)

    def _label(self, h):
        if h.kind == "objects":
            return D.humanize_sprite(h.ref.get("spriteId", "?")).split(" ")[0][:14]
        if h.kind == "warps":
            return "→ " + D.humanize_map(h.ref.get("header", "?")).split(" ")[0][:12]
        if h.kind == "coords":
            return "trigger"
        return "sign" if int(h.ref.get("type", 0) or 0) != 2 else "hidden item"

    def _point_in_item(self, tag, pt):
        """True if screen point pt is inside a shown item's rectangle."""
        try:
            mn = dpg.get_item_rect_min(tag)
            sz = dpg.get_item_rect_size(tag)
        except Exception:
            return False
        return mn[0] <= pt[0] <= mn[0] + sz[0] and mn[1] <= pt[1] <= mn[1] + sz[1]

    def _resize_trigger(self, h, tile):
        ox, oz = self._tile_of(h)
        h.ref["w"] = max(1, tile[0] - ox + 1)
        h.ref["h"] = max(1, tile[1] - oz + 1)
        self.dirty.add(self.map_id)

    def _handle_mouse(self):
        left = dpg.is_mouse_button_down(dpg.mvMouseButton_Left)
        right = dpg.is_mouse_button_down(dpg.mvMouseButton_Right)
        left_edge = left and not self._prev_left
        right_edge = right and not self._prev_right
        editing = self.mode == "edit"
        # is_item_hovered("canvas") is False when the floating menu sits on top, so
        # clicks on the menu never touch the canvas (this is what makes Add work).
        on_canvas = dpg.is_item_hovered("canvas")
        mpos = dpg.get_drawing_mouse_pos()
        # a press on the canvas dismisses an open menu; a press on the menu doesn't
        if left_edge and self.ctx_open and on_canvas:
            self._hide_ctx()
        # begin a trigger resize if grabbing the selected trigger's corner handle
        if (left_edge and editing and on_canvas and self.selected
                and self.selected.kind == "coords"):
            _, corner = self._shape_bbox(self.selected)
            if abs(mpos[0] - corner[0]) <= 12 and abs(mpos[1] - corner[1]) <= 12:
                self.resizing = self.selected
        # wizard "click a destination tile" mode swallows the next canvas click
        if left_edge and editing and on_canvas and self.pick_dest is not None:
            self.pick_dest(self.canvas_to_tile(*mpos))
            self._prev_left = left
            return
        # left: resize / select / drag-move
        if left and editing and on_canvas:
            tile = self.canvas_to_tile(*mpos)
            if self.resizing is not None:
                if self._resize_before is None:
                    self._resize_before = copy.deepcopy(self.resizing.ref)
                self._resize_trigger(self.resizing, tile)
            elif not self.dragging:
                self.pick(tile); self.dragging = True
                self._drag_before = copy.deepcopy(self.selected.ref) if self.selected else None
            elif self.selected:
                self.move_selected(*tile)
        if not left:
            if self.dragging and self.selected and self._drag_before is not None \
                    and self._drag_before != self.selected.ref:
                self.push_undo({"op": "mutate", "mid": self.map_id, "ref": self.selected.ref,
                                "before": self._drag_before,
                                "after": copy.deepcopy(self.selected.ref),
                                "label": "move " + self._label(self.selected)})
            self.dragging = False
            self._drag_before = None
            if self.resizing is not None:
                if self._resize_before is not None and self._resize_before != self.resizing.ref:
                    self.push_undo({"op": "mutate", "mid": self.map_id, "ref": self.resizing.ref,
                                    "before": self._resize_before,
                                    "after": copy.deepcopy(self.resizing.ref),
                                    "label": "resize trigger"})
                self.resizing = None
                self._resize_before = None
                self._rebuild_props()          # refresh the size fields
        # hover shape highlight
        if editing and on_canvas and not self.dragging and self.resizing is None:
            self.hover = self._nearest(self.canvas_to_tile(*mpos))
        else:
            self.hover = None
        # right-click on canvas -> context menu
        if right_edge and editing and on_canvas:
            self._open_ctx(self.canvas_to_tile(*mpos))
        self._prev_left = left
        self._prev_right = right

    # --- right-click context menu -------------------------------------------
    def _hide_ctx(self):
        if self.ctx_open:
            dpg.configure_item("ctxwin", show=False)
            self.ctx_open = False

    def _open_ctx(self, tile):
        self._ctx_tile = tile
        target = self._nearest(tile)
        if target is not None:
            self._select(target)
        self._build_ctx(target, tile)
        mx, my = dpg.get_mouse_pos(local=False)
        dpg.configure_item("ctxwin", pos=(int(mx), int(my)), show=True)
        self.ctx_open = True

    def _build_ctx(self, target, tile):
        dpg.delete_item("ctxwin", children_only=True)
        P = "ctxwin"
        if target is not None:
            z = self.zones.get(self.map_id)
            de = D.describe(z, target.kind, target.ref) if z is not None else None
            head = (de.title if de else target.kind[:-1])
            dpg.add_text(head[:38], parent=P, color=KIND_COLOR[target.kind])
            dpg.add_button(label="Edit / see details", width=200, parent=P,
                           callback=lambda *a: (self._select(target), self._hide_ctx()))
            if target.kind == "objects":
                dpg.add_button(label="Change behavior…", width=200, parent=P,
                               callback=lambda *a: (self._select(target), self._hide_ctx(),
                                                    self.open_behavior_wizard(target)))
                dpg.add_button(label="Make them walk…", width=200, parent=P,
                               callback=lambda *a: (self._select(target), self._hide_ctx(),
                                                    self.open_walk_wizard(target)))
                dpg.add_button(label="Show / Hide", width=200, parent=P,
                               callback=lambda *a: (self._select(target),
                                                    self.reveal_selected(), self._hide_ctx()))
            dpg.add_button(label="Duplicate", width=200, parent=P,
                           callback=lambda *a: (self._select(target),
                                                self.duplicate_selected(), self._hide_ctx()))
            dpg.add_button(label="Delete", width=200, parent=P,
                           callback=lambda *a: (self._select(target),
                                                self.delete_selected(), self._hide_ctx()))
            dpg.add_separator(parent=P)
        tx, tz = tile
        if not self.browsing:
            dpg.add_button(label="Move player here", width=200, parent=P,
                           callback=lambda *a: (R.teleport(self.e, tx, tz),
                                                self._hide_ctx()))
            dpg.add_separator(parent=P)
        dpg.add_text(f"Add something here ({tx}, {tz}):", parent=P, color=(150, 160, 175))
        for kind, lbl in (("objects", "Character"), ("warps", "Door / exit"),
                          ("coords", "Step trigger"), ("bgs", "Sign")):
            dpg.add_button(label="+ " + lbl, width=200, parent=P,
                           callback=lambda s, a, u, k=kind: (self.add_event(k, tx, tz),
                                                             self._hide_ctx()))

    def _map_name(self):
        if not hasattr(self, "_id2name"):
            self._id2name = {mid: nm for mid, nm in map_list()}
        return D.humanize_map(self._id2name.get(self.map_id, ""))

    def _update_labels(self):
        nm = self._map_name() or "Unknown area"
        n = len(self.handles)
        parts = [f"{nm}  (map {self.map_id})", f"{n} thing(s)"]
        if self.browsing:
            parts.append("VIEW-ONLY (player elsewhere)")
        pend = len(self.dirty) + len(self.pending_text)
        if pend:
            parts.append(f"{pend} unsaved change(s)")
        if self.undo_stack:
            parts.append(f"undo: {self.undo_stack[-1]['label']}")
        dpg.set_value("map_label", "   •   ".join(parts))
        dpg.set_value("status_text", self.status)

    # --- main loop -----------------------------------------------------------
    def run(self, max_frames=None):
        self.build_ui()
        _, mid = self._sync()
        self._load_map(mid if mid is not None else 0)
        threading.Thread(target=self._index_dialogue, daemon=True).start()
        if self.stale_state and max_frames is None and os.path.exists(FRESH_SCRIPT):
            # loaded save predates the current ROM -> regenerate instead of crashing
            self.status = ("your save is older than the current ROM (it would crash) - "
                           "making a fresh one (1-3 min)… you can browse maps meanwhile")
            logf = open(os.path.join(ROOT, "_mapeditor_fresh.log"), "w")
            self._fresh_proc = subprocess.Popen(
                [sys.executable, FRESH_SCRIPT], stdout=logf, stderr=subprocess.STDOUT)
        else:
            self._save_auto_ckpt()
        pending, pend_n = None, 0
        while dpg.is_dearpygui_running():
            if max_frames is not None:
                if self.frame >= max_frames:
                    break
                # exercise the property panels (dialogue/steps/size) headlessly
                if self.frame == 2:
                    self.toggle_mode()          # enter play; exercise input path
                    self._selftest_p0 = self.player
                if 4 <= self.frame <= max_frames - 3:
                    self.keys_down = {Keys.KEY_DOWN}   # simulate walking
                if self.frame == max_frames - 2:
                    self.keys_down = set()
                    print(f"SELFTEST walk: player {getattr(self, '_selftest_p0', None)} "
                          f"-> {self.player}")
                if self.frame == 3:
                    o = next((h for h in self.handles if h.kind == "objects"), None)
                    if o:
                        self._select(o)
                if self.frame == 5 and self.selected:
                    # exercise undo/redo: move an NPC one tile, undo, redo, undo
                    before = copy.deepcopy(self.selected.ref)
                    self.move_selected(int(before.get("x", 0)) + 1, int(before.get("z", 0)))
                    self.push_undo({"op": "mutate", "mid": self.map_id,
                                    "ref": self.selected.ref, "before": before,
                                    "after": copy.deepcopy(self.selected.ref),
                                    "label": "selftest move"})
                    self.undo(); self.redo(); self.undo()
                    assert self.selected is None or \
                        self.selected.ref.get("x") == before.get("x"), "undo failed"
                    print("SELFTEST undo/redo OK")
                if self.frame == 7:
                    self.goto_map(60)          # browse the cardboard-box room files
                    print(f"SELFTEST browse: map={self.map_id} browsing={self.browsing} "
                          f"things={len(self.handles)}")
                    self.toggle_mode()         # play-mode entry must snap back to player
                    self.toggle_mode()
                    print(f"SELFTEST snapback: map={self.map_id} browsing={self.browsing}")
                if self.frame == max_frames // 2:
                    c = next((h for h in self.handles if h.kind == "coords"), None)
                    if c:
                        self._select(c)
            try:
                if self.mode == "play":
                    self.apply_keys()
                else:
                    self.e.emu.input.keypad_update(0)
                self.e.emu.cycle(False); self.frame += 1
                live = self._refresh_live()
                if (not self.browsing and live is not None
                        and 0 <= live < 600 and live != self.map_id):
                    pending, pend_n = (live, pend_n + 1) if live == pending else (live, 1)
                    if pend_n >= 6:
                        self.pan = [0, 0]; self._load_map(live)
                        self._save_auto_ckpt()          # this map is now instantly jumpable
                        pending, pend_n = None, 0
                else:
                    pending, pend_n = None, 0
                self._check_build()
                self._check_fresh()
                self._fit_canvas()
                self._handle_mouse()
                dpg.set_value("ds", self._frame_floats())
                self._redraw_canvas()
                self._update_labels()
                dpg.render_dearpygui_frame()
            except Exception:
                self._log("FRAME ERROR:\n" + traceback.format_exc())
        # Never overwrite curated checkpoints (that's what corrupted cockpit_quick.dsv).
        # Session continuity goes to its own auto file -- but only if the game is
        # actually healthy: saving a crashed game would poison every future launch.
        if max_frames is None:
            try:
                healthy = R.player_obj_addr(self.e) != 0 and not self.stale_state
                if healthy:
                    self.e.savestate(SESSION_STATE)
                elif os.path.exists(SESSION_STATE):
                    os.remove(SESSION_STATE)     # drop a suspect leftover instead
            except Exception:
                pass
        dpg.destroy_context()


def main():
    state = default_state()
    args = sys.argv[1:]
    if "--state" in args:
        state = args[args.index("--state") + 1]
        if not os.path.isabs(state):
            state = os.path.abspath(state)
    frames = None
    if "--selftest" in args:
        frames = int(args[args.index("--selftest") + 1])
    ed = MapEditor(state)
    ed.run(max_frames=frames)
    if frames is not None:
        print(f"SELFTEST OK: ran {ed.frame} frames, no crash. "
              f"map={ed.map_id}, things={len(ed.handles)}")


if __name__ == "__main__":
    main()
