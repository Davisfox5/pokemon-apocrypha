#!/usr/bin/env python3
"""Apocrypha Grid Map Editor -- a stable top-down grid you drag on precisely,
with the live ROM beside it reflecting every edit (HGSS).

Two panes:
  LEFT  = a clean, fixed-zoom tile grid in absolute world-tile space. Events
          (NPCs/objects, warps, triggers, bg-signs) are icons sitting on exact
          tiles. No smooth-scroll, no 2-tile-tall sprites to fight -- one icon,
          one tile. Drag an icon and it snaps to a cell.
  RIGHT = the live DeSmuME screen. The emulator keeps running (your input is
          suppressed in EDIT), so a drag pokes the NPC's LocalMapObject in RAM
          and you watch it move in the actual game. Drags also write the new tile
          back to the zone_event JSON source (persistent; `make` recompiles it).

Why a separate grid instead of drawing on the DS view: precise placement. The DS
camera scrolls sub-tile and sprites overlap; a fixed grid in world coordinates is
exact and can show a wider area than the DS camera (off-screen NPCs included).

Run (inside .emu-venv, from repo root):
    source .emu-venv/bin/activate
    python tools/mapeditor/grid_editor.py --state cockpit_quick.dsv

EDIT mode (default): mouse drags icons; arrows pan the grid (or nudge the
    selected icon one tile); C recenters on the player.
PLAY mode (press G to toggle): keyboard plays the ROM (arrows/Z/X...) so you can
    walk to another spot/map; the grid follows the player and auto-loads the new
    map. Press G again to return to EDIT.
    S save   R save+build   L live/authored   B mapbg   F reveal   P screenshot   Esc quit
"""
import os, sys, subprocess, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))   # tools/
sys.path.insert(0, os.path.dirname(__file__))                        # tools/mapeditor/

import pygame
from desmume.controls import keymask, Keys
from emu_harness import Emu
import emu_ram as R
from mapdata import ZoneEvents
from mapresolve import zone_event_path, flag_id
from live_editor import Handle, KINDS, KIND_COLOR, fb_to_surface, PLAYER_PX_X, PLAYER_PX_Y

# --- layout ------------------------------------------------------------------
GRID = 30                              # px per tile cell on the editor grid
VIEW_COLS, VIEW_ROWS = 20, 19
GRID_W, GRID_H = GRID * VIEW_COLS, GRID * VIEW_ROWS      # 600 x 570
DS_W, DS_H = 256, 384
DS_SCALE = 1.5                         # live DS pane magnification
DSPW, DSPH = int(DS_W * DS_SCALE), int(DS_H * DS_SCALE)  # 384 x 576
GAP = 10
PANEL_W = 300
WIN_W = GRID_W + GAP + DSPW + GAP + PANEL_W
WIN_H = max(GRID_H, DSPH) + 10
FPS = 60

DS_X = GRID_W + GAP                    # left edge of the live DS pane
PANEL_X = DS_X + DSPW + GAP

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BUILD_SCRIPT = os.path.join(_ROOT, "_omni_native_build.sh")
LOG_PATH = os.path.join(_ROOT, "_mapeditor.log")
SHOT_PATH = os.path.join(_ROOT, "_mapeditor.png")

KEYMAP = {                             # DRIVE mode: keyboard -> DS keys
    pygame.K_UP: Keys.KEY_UP, pygame.K_DOWN: Keys.KEY_DOWN,
    pygame.K_LEFT: Keys.KEY_LEFT, pygame.K_RIGHT: Keys.KEY_RIGHT,
    pygame.K_z: Keys.KEY_A, pygame.K_x: Keys.KEY_B,
    pygame.K_RETURN: Keys.KEY_START, pygame.K_RSHIFT: Keys.KEY_SELECT,
}


class GridEditor:
    def __init__(self, state=None):
        self.e = Emu(); self.e.wait(8)
        self.seed = None
        if state and os.path.exists(state):
            self.e.loadstate(state); self.e.wait(8); self.seed = state

        pygame.init()
        pygame.key.set_repeat(250, 40)     # hold arrows to pan/nudge smoothly
        pygame.display.set_caption("Apocrypha Grid Map Editor")
        self.win = pygame.display.set_mode((WIN_W, WIN_H))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Menlo", 16)
        self.font_sm = pygame.font.SysFont("Menlo", 13)
        self.font_bold = pygame.font.SysFont("Menlo", 18, bold=True)

        self.mode = "edit"             # "edit" | "play"
        self.running = True
        self.frame = 0
        self.wysiwyg = True
        self.show = set(KINDS)
        self.show_bg = True            # live DS render as grid background (B toggles)
        self.status = "ready"

        self.zones = {}                # map_id -> ZoneEvents
        self.dirty = set()
        self.map_id = None
        self.player = (0, 0)
        self.handles = []
        self.selected = None
        self.dragging = False
        self.pan = [0, 0]              # tile offset added to player-centered view
        self._want_shot = False
        try:
            open(LOG_PATH, "w").write(f"# grid_editor session start (state={state})\n")
        except OSError:
            pass
        _, mid = self._sync_player()
        self._load_map(mid if mid is not None else 0)

    def _log(self, msg):
        try:
            with open(LOG_PATH, "a") as f:
                f.write(msg + "\n")
        except OSError:
            pass
        print(msg)

    # --- world state ---------------------------------------------------------
    def _sync_player(self):
        """Read player tile + live objects. Returns (entries, live_map_id) or
        (None, None) if RAM is transiently unreadable (e.g. mid map-transition).
        Does NOT commit self.map_id -- _load_map owns the loaded map."""
        try:
            entries = R.object_entries(self.e)
            mid = R.loc(self.e)["mapId"]
        except Exception as ex:
            self.status = f"RAM: {str(ex)[:22]}"
            return None, None
        px = next((o for o in entries if o["id"] == 255), None)
        if px:
            self.player = (px["x"], px["z"])
        return entries, mid

    def _load_map(self, map_id):
        self.map_id = map_id
        if map_id not in self.zones:
            p = zone_event_path(map_id)
            self.zones[map_id] = ZoneEvents.load(p) if p else None
        z = self.zones[map_id]
        self.handles = []
        if z is not None:
            for kind in KINDS:
                for i, ref in enumerate(getattr(z, kind)):
                    self.handles.append(Handle(kind, ref, i))
        self.selected = None
        self._refresh_live()
        p = zone_event_path(map_id)
        n = len(self.handles)
        self._log(f"\n--- MAP {map_id}  file {os.path.basename(str(p)) if p else '(none)'}"
                  f"  player {self.player}  events {n} ---")
        self.status = f"map {map_id}: {os.path.basename(str(p)) if p else 'no events'}  ({n})"

    def _refresh_live(self):
        """Rebind live objects; returns the live map id (or None if unreadable)."""
        entries, mid = self._sync_player()
        if entries is None:
            return None
        by_id = {o["id"]: o for o in entries if o["id"] != 255}
        for h in self.handles:
            if h.kind != "objects":
                continue
            o = by_id.get(h.idx)
            h.lmo_addr, h.live = (o["addr"], (o["x"], o["z"])) if o else (0, None)
        return mid

    def _tile_of(self, h):
        if self.wysiwyg and h.live is not None:
            return h.live
        return h.tile

    # --- grid <-> screen -----------------------------------------------------
    def _center(self):
        return (self.player[0] + self.pan[0], self.player[1] + self.pan[1])

    def tile_to_px(self, tx, tz):
        cx, cz = self._center()
        return (int((tx - cx) * GRID + GRID_W / 2),
                int((tz - cz) * GRID + GRID_H / 2))

    def px_to_tile(self, mx, my):
        # floor, not round: any pixel inside cell [gx, gx+GRID) maps to its tile
        cx, cz = self._center()
        return (math.floor((mx - GRID_W / 2) / GRID + cx),
                math.floor((my - GRID_H / 2) / GRID + cz))

    # --- editing -------------------------------------------------------------
    def move_selected(self, tx, tz):
        h = self.selected
        if not h:
            return
        if h.kind == "objects" and h.lmo_addr:
            R.move_object(self.e, h.lmo_addr, tx, tz)   # live: shows in DS pane
            h.live = (tx, tz)
        h.set_tile(tx, tz)                              # persistent: source JSON
        self.dirty.add(self.map_id)

    def pick(self, mx, my):
        tx, tz = self.px_to_tile(mx, my)
        best, bestd = None, 99
        for h in self.handles:
            if h.kind not in self.show:
                continue
            hx, hz = self._tile_of(h)
            if h.kind == "coords":       # triggers span w*h; hit-test the box
                w = int(h.ref.get("w", 1)); ht = int(h.ref.get("h", 1))
                if hx <= tx < hx + w and hz <= tz < hz + ht:
                    best, bestd = h, 0
                continue
            d = abs(hx - tx) + abs(hz - tz)
            if d < bestd:
                best, bestd = h, d
        self.selected = best if bestd <= 1 else None

    def toggle_gate(self):
        """Clear/set the selected object's FLAG_HIDE_* gate. Clearing reveals the
        NPC on the next map load (objects spawn only if the flag is clear)."""
        h = self.selected
        if not h or h.kind != "objects":
            self.status = "select an object first"; return
        fname = str(h.ref.get("eventFlag", "FLAG_NOTHING"))
        fid = flag_id(fname)
        if fname == "FLAG_NOTHING" or not fid:
            self.status = f"{fname}: not a hide-gate"; return
        cur = R.flag_check(self.e, fid)
        if cur is None:
            self.status = f"{fname}: temp flag, can't persist"; return
        R.flag_write(self.e, fid, 0 if cur else 1)
        self.status = (f"{'revealed' if cur else 'hid'} {fname.replace('FLAG_HIDE_','')}"
                       f" - re-enter map to spawn")

    def save_all(self):
        n = 0
        for mid in list(self.dirty):
            z = self.zones.get(mid)
            if z:
                z.save(); n += 1
        self.dirty.clear()
        self.status = f"saved {n} zone_event file(s) -> source"; self._log(self.status)

    def rebuild(self):
        self.save_all()
        if os.path.exists(BUILD_SCRIPT):
            subprocess.Popen(["bash", BUILD_SCRIPT], cwd=_ROOT,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.status = "saved + build started (bg); relaunch to load ROM"
        else:
            self.status = "saved; build script not found"
        self._log(self.status)

    # --- input ---------------------------------------------------------------
    def apply_drive_keys(self):
        pressed = pygame.key.get_pressed()
        mask = 0
        for pk, dk in KEYMAP.items():
            if pressed[pk]:
                mask |= keymask(dk)
        self.e.emu.input.keypad_update(mask)

    def events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.running = False
                elif ev.key == pygame.K_p:
                    self._want_shot = True
                elif ev.key == pygame.K_g:
                    self.mode = "play" if self.mode == "edit" else "edit"
                    self.status = f"{self.mode.upper()} mode (G toggles)"
                    self._log(f"[f{self.frame}] MODE -> {self.mode}  map={self.map_id} player={self.player}")
                elif ev.key == pygame.K_s:
                    self.save_all()
                elif ev.key == pygame.K_r:
                    self.rebuild()
                elif ev.key == pygame.K_l:
                    self.wysiwyg = not self.wysiwyg
                    self.status = f"WYSIWYG {'on' if self.wysiwyg else 'off'}"
                elif ev.key == pygame.K_c:
                    self.pan = [0, 0]
                elif ev.key == pygame.K_b:
                    self.show_bg = not self.show_bg
                    self.status = f"map bg {'on' if self.show_bg else 'off'}"
                elif ev.key == pygame.K_f:
                    self.toggle_gate()
                elif self.mode == "edit" and ev.key in (
                        pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                    dx = (ev.key == pygame.K_RIGHT) - (ev.key == pygame.K_LEFT)
                    dz = (ev.key == pygame.K_DOWN) - (ev.key == pygame.K_UP)
                    if self.selected:                    # nudge selection one tile
                        tx, tz = self._tile_of(self.selected)
                        self.move_selected(tx + dx, tz + dz)
                    else:                                # pan the grid one tile
                        self.pan[0] += dx; self.pan[1] += dz
            elif ev.type == pygame.MOUSEBUTTONDOWN and self.mode == "edit":
                mx, my = ev.pos
                if mx < GRID_W and my < GRID_H:
                    self.pick(mx, my)
                    self.dragging = self.selected is not None
            elif ev.type == pygame.MOUSEMOTION and self.dragging:
                mx, my = ev.pos
                if mx < GRID_W and my < GRID_H:
                    self.move_selected(*self.px_to_tile(mx, my))
            elif ev.type == pygame.MOUSEBUTTONUP:
                self.dragging = False

    # --- rendering -----------------------------------------------------------
    def draw(self):
        self.win.fill((12, 14, 20))
        self._draw_grid()
        self._draw_ds()
        self._draw_panel()
        if self._want_shot:
            try:
                pygame.image.save(self.win, SHOT_PATH); self._log(f"shot -> {os.path.basename(SHOT_PATH)}")
            except Exception as ex:
                self._log(f"shot failed: {ex}")
            self._want_shot = False
        pygame.display.flip()

    def _draw_bg(self):
        """Composite the live DS top screen under the grid, aligned so the DS
        player anchor (128,88) lands on the player's grid cell. Real map art
        (paths/water/buildings) as placement context -- approximate, no RE."""
        scale = GRID / 16.0            # 1 DS tile (16px) -> 1 grid cell
        top = fb_to_surface(self.e).subsurface((0, 0, DS_W, 192))
        scaled = pygame.transform.scale(top, (int(DS_W * scale), int(192 * scale)))
        pgx, pgy = self.tile_to_px(*self.player)
        bx = pgx + GRID / 2 - PLAYER_PX_X * scale
        by = pgy + GRID / 2 - PLAYER_PX_Y * scale
        prev = self.win.get_clip()
        self.win.set_clip((0, 0, GRID_W, GRID_H))
        self.win.blit(scaled, (bx, by))
        dim = pygame.Surface((GRID_W, GRID_H), pygame.SRCALPHA)  # mute so icons pop
        dim.fill((10, 12, 18, 70))
        self.win.blit(dim, (0, 0))
        self.win.set_clip(prev)

    def _draw_grid(self):
        pygame.draw.rect(self.win, (22, 26, 34), (0, 0, GRID_W, GRID_H))
        if self.show_bg:
            self._draw_bg()
        # grid lines
        cx, cz = self._center()
        ox = int((-(cx) * GRID + GRID_W / 2) % GRID)
        oy = int((-(cz) * GRID + GRID_H / 2) % GRID)
        for x in range(ox, GRID_W, GRID):
            pygame.draw.line(self.win, (36, 42, 52), (x, 0), (x, GRID_H))
        for y in range(oy, GRID_H, GRID):
            pygame.draw.line(self.win, (36, 42, 52), (0, y), (GRID_W, y))

        # player cell (outline only over the map bg so the sprite shows through)
        pgx, pgy = self.tile_to_px(*self.player)
        if not self.show_bg:
            pygame.draw.rect(self.win, (60, 90, 140), (pgx, pgy, GRID, GRID))
        pygame.draw.rect(self.win, (140, 190, 255), (pgx, pgy, GRID, GRID), 2)
        self.win.blit(self.font_sm.render("YOU", True, (200, 220, 255)), (pgx + 1, pgy + 4))

        # events
        for h in self.handles:
            if h.kind not in self.show:
                continue
            self._draw_handle(h)

        # clip anything drawn outside the pane
        pygame.draw.rect(self.win, (70, 80, 95), (0, 0, GRID_W, GRID_H), 1)

    def _draw_handle(self, h):
        tx, tz = self._tile_of(h)
        gx, gy = self.tile_to_px(tx, tz)
        if gx < -GRID or gx > GRID_W or gy < -GRID or gy > GRID_H:
            return
        col = KIND_COLOR[h.kind]
        sel = h is self.selected
        no_live = h.kind == "objects" and self.wysiwyg and h.live is None
        if no_live:
            col = tuple(c // 2 for c in col)
        cx_, cy_ = gx + GRID // 2, gy + GRID // 2
        if h.kind == "objects":
            pygame.draw.circle(self.win, col, (cx_, cy_), GRID // 2 - 2)
        elif h.kind == "warps":
            pygame.draw.rect(self.win, col, (gx + 3, gy + 3, GRID - 6, GRID - 6))
        elif h.kind == "coords":
            w = int(h.ref.get("w", 1)); ht = int(h.ref.get("h", 1))
            surf = pygame.Surface((w * GRID, ht * GRID), pygame.SRCALPHA)
            surf.fill((*col, 70))
            self.win.blit(surf, (gx, gy))
            pygame.draw.rect(self.win, col, (gx, gy, w * GRID, ht * GRID), 1)
        else:  # bg
            pygame.draw.polygon(self.win, col, [(cx_, gy + 3), (gx + GRID - 3, cy_),
                                                (cx_, gy + GRID - 3), (gx + 3, cy_)])
        if sel:
            pygame.draw.rect(self.win, (255, 255, 255), (gx - 1, gy - 1, GRID + 2, GRID + 2), 2)
        lbl = self._label(h)
        if lbl and (sel or h.kind in ("objects", "warps")):
            self.win.blit(self.font_sm.render(lbl, True, col), (gx, gy - 11))

    def _label(self, h):
        if h.kind == "objects":
            s = str(h.ref.get("id", "obj"))
            return s.split("_", 2)[-1] if s.count("_") >= 2 else s
        if h.kind == "warps":
            return f">{h.ref.get('header','?')}".replace("MAP_", "")[:14]
        if h.kind == "coords":
            return "trig"
        return "bg"

    def _draw_ds(self):
        frame = pygame.transform.scale(fb_to_surface(self.e), (DSPW, DSPH))
        self.win.blit(frame, (DS_X, 0))
        ymid = int(192 * DS_SCALE)
        pygame.draw.line(self.win, (40, 40, 50), (DS_X, ymid), (DS_X + DSPW, ymid), 1)
        pygame.draw.rect(self.win, (70, 80, 95), (DS_X, 0, DSPW, DSPH), 1)

    def _draw_panel(self):
        x = PANEL_X
        y = [8]
        def line(txt, color=(210, 220, 230), font=None, dy=17):
            self.win.blit((font or self.font).render(txt, True, color), (x, y[0])); y[0] += dy
        mcol = (255, 200, 90) if self.mode == "play" else (120, 230, 140)
        line(f"[{self.mode.upper()}]  {self.clock.get_fps():4.1f}fps", mcol, self.font_bold, 28)
        line(f"map {self.map_id}  you {self.player}", (180, 220, 255), self.font_sm, 19)
        bound = sum(1 for h in self.handles if h.kind == "objects" and h.lmo_addr)
        nobj = sum(1 for h in self.handles if h.kind == "objects")
        line(f"WYSIWYG {'on' if self.wysiwyg else 'off'}  bound {bound}/{nobj}",
             (150, 160, 175), self.font_sm, 19)
        line(f"unsaved: {len(self.dirty)} map(s)",
             (255, 180, 120) if self.dirty else (140, 150, 160), self.font_sm, 22)
        for kind in KINDS:
            c = KIND_COLOR[kind]
            n = sum(1 for h in self.handles if h.kind == kind)
            line(f"  {kind}: {n}", c, self.font_sm, 18)
        y[0] += 10
        if self.selected:
            s = self.selected
            line("selected", (150, 160, 175), self.font_sm, 19)
            line("  " + self._label(s), (235, 235, 240), self.font_sm, 18)
            line(f"  authored {s.tile}", (200, 210, 220), self.font_sm, 18)
            if s.lmo_addr:
                moved = s.live != s.tile
                line(f"  live {s.live}" + ("  moved" if moved else ""),
                     (255, 200, 120) if moved else (120, 230, 140), self.font_sm, 18)
            elif s.kind == "objects":
                line("  (not spawned here)", (150, 160, 170), self.font_sm, 18)
            if s.kind == "objects":
                fname = str(s.ref.get("eventFlag", "FLAG_NOTHING"))
                fid = flag_id(fname) if fname != "FLAG_NOTHING" else None
                st = R.flag_check(self.e, fid) if fid else None
                short = fname.replace("FLAG_HIDE_", "")
                if st is None:
                    line(f"  gate: {short[:20]}", (150, 160, 170), self.font_sm, 18)
                else:
                    line(f"  gate {short[:16]}={'HID' if st else 'shown'}  F toggles",
                         (255, 200, 120) if st else (120, 230, 140), self.font_sm, 18)
        else:
            line("click an icon to select", (140, 150, 160), self.font_sm, 19)
        # footer help + status
        fy = WIN_H - 72
        pygame.draw.line(self.win, (50, 55, 65), (x, fy - 8), (x + PANEL_W - 10, fy - 8))
        line2 = self.font_sm.render
        self.win.blit(line2("G = PLAY / EDIT toggle", True, (200, 200, 130)), (x, fy))
        self.win.blit(line2("drag move  F reveal  B mapbg", True, (130, 140, 155)), (x, fy + 18))
        self.win.blit(line2("S save  R build  P shot", True, (130, 140, 155)), (x, fy + 36))
        self.win.blit(line2(self.status[:38], True, (120, 200, 140)), (x, fy + 56))

    # --- main loop -----------------------------------------------------------
    def run(self):
        import traceback
        pending, pend_n = None, 0
        last_player = None
        while self.running:
            try:
                self.events()
                if self.mode == "play":
                    self.apply_drive_keys()
                else:
                    self.e.emu.input.keypad_update(0)
                self.e.emu.cycle(False); self.frame += 1
                live = self._refresh_live()
                # heartbeat: proves the loop + emulator are advancing (or not)
                if self.frame % 60 == 0:
                    moved = "" if self.player == last_player else " (moving)"
                    self._log(f"[f{self.frame}] hb {self.mode} fps={self.clock.get_fps():.0f} "
                              f"map={self.map_id} player={self.player} live={live}{moved}")
                    last_player = self.player
                # Debounced, range-checked map reload. A map transition briefly
                # reports unstable/garbage ids; only switch once the destination
                # id has held steady for several frames (avoids reloading -- and
                # reading RAM -- in the middle of the load).
                if live is not None and 0 <= live < 600 and live != self.map_id:
                    pending, pend_n = (live, pend_n + 1) if live == pending else (live, 1)
                    if pend_n >= 6:
                        self.pan = [0, 0]
                        self._load_map(live)
                        pending, pend_n = None, 0
                else:
                    pending, pend_n = None, 0
                self.draw()
            except Exception:
                self._log("FRAME ERROR:\n" + traceback.format_exc())
            self.clock.tick(FPS)
        if self.seed:
            try:
                self.e.savestate(self.seed)
            except Exception:
                pass
        pygame.quit()


def main():
    state = None
    args = sys.argv[1:]
    if "--state" in args:
        state = args[args.index("--state") + 1]
        if not os.path.isabs(state):
            state = os.path.abspath(state)
    GridEditor(state).run()


if __name__ == "__main__":
    main()
