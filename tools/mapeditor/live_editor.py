#!/usr/bin/env python3
"""Apocrypha Live Map Editor -- edit map events WHILE the ROM runs (HGSS).

One pygame window. You PLAY the ROM; press E to freeze into EDIT mode. The editor
resolves the map you're standing in (from live RAM) to its zone_event JSON source,
overlays the tile grid on the top screen, and draws every event -- objects/NPCs,
warps, triggers, bg-signs -- as a draggable handle at its tile. Drag one and:

  * for an NPC/object, its live LocalMapObject is poked in RAM -> it MOVES on screen
    the instant you resume (E) -- instant preview;
  * and the change is written into the in-memory zone_event dict, so pressing S
    saves it to the decomp source (persistent -- `make` recompiles it into the ROM).

So edits are BOTH live (immediate) and persistent (source of truth). Collision/tile
painting is a later phase; this is the event layer.

Run (inside .emu-venv, from repo root):
    source .emu-venv/bin/activate
    python tools/mapeditor/live_editor.py                 # fresh boot
    python tools/mapeditor/live_editor.py --state cur_cherrygrove.dsv

PLAY mode:  arrows=D-pad  Z/X=A/B  A/S=Y/X  Q/W=L/R  Enter=START  RShift=SELECT
            [ / ] = emu speed    E = freeze into EDIT    Esc = quit (saves state)
EDIT mode (emulation frozen):
    Click a handle to select it (nearest tile wins).
    Drag it, or nudge with arrow keys, to move it one tile at a time.
    Tab ...... cycle which event kinds are shown/pickable
    S ........ save all changed zone_event JSON files to the decomp source
    R ........ save + kick off a ROM rebuild (background); relaunch to load it
    E / Esc .. resume play (keeps your unsaved edits in memory)
"""
import os, sys, subprocess, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))   # tools/
sys.path.insert(0, os.path.dirname(__file__))                        # tools/mapeditor/

import pygame
from desmume.controls import keymask, Keys
from emu_harness import Emu
import emu_ram as R
from mapdata import ZoneEvents
from mapresolve import zone_event_path

# --- layout (mirrors cockpit.py) --------------------------------------------
SCALE = 2
DS_W, DS_H = 256, 384
SCREEN_SPLIT = 192                 # top screen rows 0..191
PANEL_W = 360
WIN_W = DS_W * SCALE + PANEL_W
WIN_H = DS_H * SCALE
FPS = 60

# player-anchored pixel<->tile projection (same calibration as cockpit.py)
PLAYER_PX_X, PLAYER_PX_Y, TILE_PX = 128, 88, 16

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BUILD_SCRIPT = os.path.join(_ROOT, "_omni_native_build.sh")
# fixed paths Claude reads on "check it": a text log + an annotated edit-mode shot
LOG_PATH = os.path.join(_ROOT, "_mapeditor.log")
SHOT_PATH = os.path.join(_ROOT, "_mapeditor.png")

KEYMAP = {
    pygame.K_UP: Keys.KEY_UP, pygame.K_DOWN: Keys.KEY_DOWN,
    pygame.K_LEFT: Keys.KEY_LEFT, pygame.K_RIGHT: Keys.KEY_RIGHT,
    pygame.K_z: Keys.KEY_A, pygame.K_x: Keys.KEY_B,
    pygame.K_a: Keys.KEY_Y, pygame.K_s: Keys.KEY_X,
    pygame.K_q: Keys.KEY_L, pygame.K_w: Keys.KEY_R,
    pygame.K_RETURN: Keys.KEY_START, pygame.K_RSHIFT: Keys.KEY_SELECT,
}

# event kinds: (json key, color, uses x/z fields). bgs use "dir"; coords have w/h.
KINDS = ["objects", "warps", "coords", "bgs"]
KIND_COLOR = {"objects": (90, 230, 120), "warps": (90, 170, 255),
              "coords": (255, 170, 70), "bgs": (210, 120, 240)}


def fb_to_surface(emu):
    buf = emu.emu.display_buffer_as_rgbx()
    return pygame.image.frombuffer(bytes(buf), (DS_W, DS_H), "RGBX")


def tile_to_native(tx, tz, player):
    """World tile -> top-screen native pixel (inverse of cockpit projection)."""
    return (PLAYER_PX_X + (tx - player[0]) * TILE_PX,
            PLAYER_PX_Y + (tz - player[1]) * TILE_PX)


def native_to_tile(nx, ny, player):
    return (player[0] + round((nx - PLAYER_PX_X) / TILE_PX),
            player[1] + round((ny - PLAYER_PX_Y) / TILE_PX))


class Handle:
    """A pickable event: a reference into a zone_event JSON list element."""
    __slots__ = ("kind", "ref", "idx", "lmo_addr", "live")

    def __init__(self, kind, ref, idx):
        self.kind, self.ref, self.idx = kind, ref, idx
        self.lmo_addr = 0            # bound live LocalMapObject (objects only)
        self.live = None            # live (x,z) from RAM, if the object is spawned

    @property
    def tile(self):
        return (int(self.ref.get("x", 0)), int(self.ref.get("z", 0)))

    def set_tile(self, tx, tz):
        self.ref["x"], self.ref["z"] = int(tx), int(tz)

    def label(self):
        r = self.ref
        if self.kind == "objects":
            return f"{r.get('id','obj')}  spr={r.get('spriteId','?')}  scr={r.get('scriptId','?')}"
        if self.kind == "warps":
            return f"warp -> {r.get('header','?')} anchor {r.get('anchor','?')}"
        if self.kind == "coords":
            return f"trigger {r.get('scriptId','?')} {r.get('w',1)}x{r.get('h',1)} var={r.get('var','?')}"
        return f"bg {r.get('scriptId','?')} type={r.get('type','?')}"


class LiveEditor:
    def __init__(self, state=None):
        self.e = Emu(); self.e.wait(8)
        self.seed = None
        if state and os.path.exists(state):
            self.e.loadstate(state); self.e.wait(8); self.seed = state

        pygame.init()
        pygame.display.set_caption("Apocrypha Live Map Editor")
        self.win = pygame.display.set_mode((WIN_W, WIN_H))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Menlo", 14)
        self.font_sm = pygame.font.SysFont("Menlo", 12)
        self.font_bold = pygame.font.SysFont("Menlo", 15, bold=True)

        self.mode = "play"          # "play" | "edit"
        self.running = True
        self.frame = 0
        self.speed = 1
        self.status = "ready"

        self.zones = {}             # map_id -> ZoneEvents (loaded on demand)
        self.dirty = set()          # map_ids with unsaved edits
        self.map_id = None
        self.player = (0, 0)
        self.handles = []
        self.selected = None
        self.dragging = False
        self.show = set(KINDS)      # which kinds are visible/pickable
        self.wysiwyg = True         # draw objects at LIVE sprite pos (L toggles)
        self._want_shot = False     # save an annotated PNG on the next draw
        try:                        # fresh log per launch
            open(LOG_PATH, "w").write(f"# live_editor session start (state={state})\n")
        except OSError:
            pass

    def _log(self, msg):
        try:
            with open(LOG_PATH, "a") as f:
                f.write(msg + "\n")
        except OSError:
            pass
        print(msg)

    # --- map / event loading -------------------------------------------------
    def _zone(self, map_id):
        if map_id not in self.zones:
            p = zone_event_path(map_id)
            self.zones[map_id] = ZoneEvents.load(p) if p else None
        return self.zones[map_id]

    def enter_edit(self):
        try:
            self.map_id = R.loc(self.e)["mapId"]
            entries = R.object_entries(self.e)
        except Exception as ex:
            self.status = f"RAM read failed: {ex}"; return
        px = next((o for o in entries if o["id"] == 255), None)
        self.player = (px["x"], px["z"]) if px else (0, 0)

        z = self._zone(self.map_id)
        self.handles = []
        if z is None:
            self.status = f"map {self.map_id}: no zone_event file"
        else:
            for kind in KINDS:
                for i, ref in enumerate(getattr(z, kind)):
                    self.handles.append(Handle(kind, ref, i))
            self._bind_live_objects(entries)
            self.status = (f"EDIT {os.path.basename(str(zone_event_path(self.map_id)))}"
                           f"  {len(self.handles)} events")
        self._debug_dump(entries)
        self.selected = None
        self.mode = "edit"
        self.e.emu.input.keypad_update(0)

    def _debug_dump(self, entries):
        """Log what the editor sees on freeze -- lets Claude calibrate remotely.
        Key signal: do live NPC (x,z) match the JSON object tiles? ([live] = bound)."""
        p = zone_event_path(self.map_id)
        self._log(f"\n--- EDIT map {self.map_id}  file {os.path.basename(str(p)) if p else '(none)'}"
                  f"  player {self.player} ---")
        npcs = [o for o in entries if o["id"] != 255]
        self._log(f"live objects ({len(npcs)} NPC + player): "
                  + ", ".join(f"id{o['id']}@({o['x']},{o['z']})" for o in npcs[:12]))
        objs = [h for h in self.handles if h.kind == "objects"]
        for h in objs:
            dt = self._draw_tile(h)
            nx, ny = tile_to_native(*dt, self.player)
            onscreen = 0 <= nx < DS_W and 0 <= ny < SCREEN_SPLIT
            live_s = (f"live{tuple(h.live)}" + ("!=auth" if h.live != h.tile else "")) if h.live else "no-live"
            self._log(f"  obj[{h.idx:>2}] {str(h.ref.get('id','?')):<28} auth{h.tile} "
                      f"{live_s:<18} px({nx:>4},{ny:>4}){'' if onscreen else ' offscr'}")
        bound = sum(1 for h in objs if h.lmo_addr)
        self._log(f"bound {bound}/{len(objs)} objects to live LMOs; "
                  f"warps={sum(h.kind=='warps' for h in self.handles)} "
                  f"coords={sum(h.kind=='coords' for h in self.handles)} "
                  f"bgs={sum(h.kind=='bgs' for h in self.handles)}")
        self._log(f"(screenshot -> {os.path.basename(SHOT_PATH)}; press P anytime for a fresh one)")
        self._want_shot = True

    def _bind_live_objects(self, entries):
        """Bind each object-handle to its live LMO by id == JSON array index (the
        HGSS object `id` constants are per-map sequential), so binding survives a
        script moving the NPC. Records the live tile for WYSIWYG drawing."""
        by_id = {o["id"]: o for o in entries if o["id"] != 255}
        for h in self.handles:
            if h.kind != "objects":
                continue
            o = by_id.get(h.idx)
            if o:
                h.lmo_addr = o["addr"]
                h.live = (o["x"], o["z"])

    def _draw_tile(self, h):
        """Where to draw/pick this handle: live sprite pos in WYSIWYG mode,
        else the authored source tile."""
        if self.wysiwyg and h.live is not None:
            return h.live
        return h.tile

    def _refresh_live(self):
        """Re-read player + live object tiles every frame while editing, so boxes
        track the running scene and RAM pokes show up immediately."""
        try:
            entries = R.object_entries(self.e)
        except Exception:
            return
        px = next((o for o in entries if o["id"] == 255), None)
        if px:
            self.player = (px["x"], px["z"])
        by_id = {o["id"]: o for o in entries if o["id"] != 255}
        for h in self.handles:
            if h.kind != "objects":
                continue
            o = by_id.get(h.idx)
            if o:
                h.lmo_addr, h.live = o["addr"], (o["x"], o["z"])
            else:
                h.lmo_addr, h.live = 0, None

    # --- editing ops ---------------------------------------------------------
    def move_selected(self, tx, tz):
        h = self.selected
        if not h:
            return
        if h.kind == "objects" and h.lmo_addr:
            R.move_object(self.e, h.lmo_addr, tx, tz)   # instant live preview
            h.live = (tx, tz)
        h.set_tile(tx, tz)                              # write authored source too
        self.dirty.add(self.map_id)

    def pick(self, nx, ny):
        tx, tz = native_to_tile(nx, ny, self.player)
        best, bestd = None, 99
        for h in self.handles:
            if h.kind not in self.show:
                continue
            hx, hz = self._draw_tile(h)
            d = abs(hx - tx) + abs(hz - tz)
            if d < bestd:
                best, bestd = h, d
        self.selected = best if bestd <= 1 else None

    def save_all(self):
        n = 0
        for mid in list(self.dirty):
            z = self.zones.get(mid)
            if z:
                z.save(); n += 1
        self.dirty.clear()
        self.status = f"saved {n} zone_event file(s) -> decomp source"
        self._log(self.status)

    def rebuild(self):
        self.save_all()
        if not os.path.exists(BUILD_SCRIPT):
            self.status = "saved; build script not found (build manually)"
            return
        subprocess.Popen(["bash", BUILD_SCRIPT],
                         cwd=os.path.dirname(BUILD_SCRIPT),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.status = "saved + build started (bg); relaunch --state to load ROM"

    # --- input ---------------------------------------------------------------
    def apply_keys(self):
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
                if ev.key == pygame.K_p:            # snapshot now (either mode)
                    self._want_shot = True
                    continue
                if self.mode == "play":
                    if ev.key == pygame.K_ESCAPE:
                        self.running = False
                    elif ev.key == pygame.K_e:
                        self.enter_edit()
                    elif ev.key == pygame.K_LEFTBRACKET:
                        self.speed = max(0, self.speed - 1)
                    elif ev.key == pygame.K_RIGHTBRACKET:
                        self.speed = min(8, self.speed + 1)
                else:  # edit mode
                    if ev.key in (pygame.K_e, pygame.K_ESCAPE):
                        self.mode = "play"; self.dragging = False
                    elif ev.key == pygame.K_TAB:
                        self._cycle_filter()
                    elif ev.key == pygame.K_l:
                        self.wysiwyg = not self.wysiwyg
                        self.status = f"WYSIWYG {'on (live sprite pos)' if self.wysiwyg else 'off (authored pos)'}"
                        self._want_shot = True
                    elif ev.key == pygame.K_s:
                        self.save_all()
                    elif ev.key == pygame.K_r:
                        self.rebuild()
                    elif self.selected and ev.key in (pygame.K_UP, pygame.K_DOWN,
                                                      pygame.K_LEFT, pygame.K_RIGHT):
                        tx, tz = self.selected.tile
                        tx += (ev.key == pygame.K_RIGHT) - (ev.key == pygame.K_LEFT)
                        tz += (ev.key == pygame.K_DOWN) - (ev.key == pygame.K_UP)
                        self.move_selected(tx, tz)
            elif ev.type == pygame.MOUSEBUTTONDOWN and self.mode == "edit":
                mx, my = ev.pos
                if mx < DS_W * SCALE and my < SCREEN_SPLIT * SCALE:
                    self.pick(mx / SCALE, my / SCALE)
                    self.dragging = self.selected is not None
            elif ev.type == pygame.MOUSEMOTION and self.dragging:
                mx, my = ev.pos
                tx, tz = native_to_tile(mx / SCALE, my / SCALE, self.player)
                self.move_selected(tx, tz)
            elif ev.type == pygame.MOUSEBUTTONUP:
                self.dragging = False

    def _cycle_filter(self):
        # cycle: all -> objects -> warps -> coords -> bgs -> all
        order = [set(KINDS)] + [{k} for k in KINDS]
        try:
            i = order.index(self.show)
        except ValueError:
            i = 0
        self.show = order[(i + 1) % len(order)]
        self.status = "show: " + ",".join(sorted(self.show))

    # --- rendering -----------------------------------------------------------
    def draw(self):
        frame = fb_to_surface(self.e)
        self.win.blit(pygame.transform.scale(frame, (DS_W * SCALE, DS_H * SCALE)), (0, 0))
        pygame.draw.line(self.win, (40, 40, 50), (0, SCREEN_SPLIT * SCALE),
                         (DS_W * SCALE, SCREEN_SPLIT * SCALE), 2)
        if self.mode == "edit":
            self._draw_grid()
            self._draw_handles()
        self._draw_panel()
        if self._want_shot:
            try:
                pygame.image.save(self.win, SHOT_PATH)
                self._log(f"shot saved -> {os.path.basename(SHOT_PATH)}")
            except Exception as ex:
                self._log(f"shot failed: {ex}")
            self._want_shot = False
        pygame.display.flip()

    def _draw_grid(self):
        ov = pygame.Surface((DS_W * SCALE, SCREEN_SPLIT * SCALE), pygame.SRCALPHA)
        # vertical/horizontal lines snapped to tile boundaries around the player
        ox = (PLAYER_PX_X % TILE_PX) * SCALE
        oy = (PLAYER_PX_Y % TILE_PX) * SCALE
        step = TILE_PX * SCALE
        for x in range(ox, DS_W * SCALE, step):
            pygame.draw.line(ov, (255, 255, 255, 30), (x, 0), (x, SCREEN_SPLIT * SCALE))
        for y in range(oy, SCREEN_SPLIT * SCALE, step):
            pygame.draw.line(ov, (255, 255, 255, 30), (0, y), (DS_W * SCALE, y))
        self.win.blit(ov, (0, 0))

    def _draw_handles(self):
        for h in self.handles:
            if h.kind not in self.show:
                continue
            tx, tz = self._draw_tile(h)
            nx, ny = tile_to_native(tx, tz, self.player)
            if not (-TILE_PX <= nx < DS_W and -TILE_PX <= ny < SCREEN_SPLIT):
                continue
            col = KIND_COLOR[h.kind]
            no_live = h.kind == "objects" and self.wysiwyg and h.live is None
            if no_live:                      # authored-only (NPC not spawned here)
                col = tuple(c // 2 for c in col)
            wx = int(h.ref.get("w", 1)) if h.kind == "coords" else 1
            wz = int(h.ref.get("h", 1)) if h.kind == "coords" else 1
            rx, ry = nx * SCALE, ny * SCALE
            rw, rh = wx * TILE_PX * SCALE, wz * TILE_PX * SCALE
            sel = h is self.selected
            fill = pygame.Surface((rw, rh), pygame.SRCALPHA)
            fill.fill((*col, 90 if sel else 45))       # translucent foot-tile
            self.win.blit(fill, (rx, ry))
            pygame.draw.rect(self.win, col, (rx, ry, rw, rh), 2 if sel else 1)
            if sel:
                pygame.draw.rect(self.win, (255, 255, 255), (rx - 2, ry - 2, rw + 4, rh + 4), 1)
                # crosshair marking the exact tile the sprite stands on
                cx, cy = rx + rw // 2, ry + rh // 2
                pygame.draw.line(self.win, (255, 255, 255), (cx - 5, cy), (cx + 5, cy))
                pygame.draw.line(self.win, (255, 255, 255), (cx, cy - 5), (cx, cy + 5))
            lbl = self._handle_label(h)
            if lbl:
                self.win.blit(self.font_sm.render(lbl, True, col), (rx, max(0, ry - 13)))

    def _handle_label(self, h):
        if h.kind == "objects":
            s = str(h.ref.get("id", "obj"))
            return s.split("_", 2)[-1] if s.count("_") >= 2 else s   # obj_R30_gsman1 -> gsman1
        if h.kind == "warps":
            return f">{h.ref.get('header','?')}"
        if h.kind == "coords":
            return "trig"
        return "bg"

    def _draw_panel(self):
        x0 = DS_W * SCALE
        pygame.draw.rect(self.win, (18, 20, 28), (x0, 0, PANEL_W, WIN_H))
        y = [10]
        def line(txt, color=(210, 220, 230), font=None, dy=18):
            self.win.blit((font or self.font).render(txt, True, color), (x0 + 12, y[0]))
            y[0] += dy
        mcol = (120, 230, 140) if self.mode == "play" else (255, 200, 90)
        line(f"[{self.mode.upper()}]  speed x{self.speed}  {self.clock.get_fps():4.1f}fps",
             mcol, self.font_bold, 24)
        if self.mode == "edit":
            line(f"map {self.map_id}   player {self.player}", (180, 220, 255))
            bound = sum(1 for h in self.handles if h.kind == "objects" and h.lmo_addr)
            nobj = sum(1 for h in self.handles if h.kind == "objects")
            line(f"WYSIWYG {'ON' if self.wysiwyg else 'off'} (L)  bound {bound}/{nobj}",
                 (120, 230, 140) if self.wysiwyg else (150, 160, 175), self.font_sm, 16)
            line(f"show: {','.join(sorted(self.show))}  (Tab)", (150, 160, 175), self.font_sm, 16)
            line(f"unsaved maps: {len(self.dirty)}",
                 (255, 180, 120) if self.dirty else (140, 150, 160), self.font_sm, 18)
            y[0] += 4
            for kind in KINDS:
                c = KIND_COLOR[kind]
                n = sum(1 for h in self.handles if h.kind == kind)
                line(f"  {kind}: {n}", c, self.font_sm, 15)
            y[0] += 6
            if self.selected:
                s = self.selected
                line("selected", (150, 160, 175), self.font_sm, 16)
                line("  " + s.label(), (230, 235, 240), self.font_sm, 15)
                line(f"  authored tile {s.tile}", (200, 210, 220), self.font_sm, 15)
                if s.lmo_addr:
                    moved = s.live != s.tile
                    line(f"  live tile {s.live}" + ("  (script-moved)" if moved else ""),
                         (255, 200, 120) if moved else (120, 230, 140), self.font_sm, 15)
                elif s.kind == "objects":
                    line("  not spawned here (source-only)", (150, 160, 170), self.font_sm, 15)
                line("  drag / arrows to move", (140, 150, 160), self.font_sm, 15)
            else:
                line("click a handle to select", (140, 150, 160), self.font_sm, 16)
        else:
            line("E = edit this map", (180, 220, 255))
            line("arrows/Z/X to play", (150, 160, 175), self.font_sm, 16)
        # footer status
        fy = WIN_H - 40
        pygame.draw.line(self.win, (50, 55, 65), (x0 + 8, fy - 8), (x0 + PANEL_W - 8, fy - 8))
        self.win.blit(self.font_sm.render(self.status[:46], True, (120, 200, 140)), (x0 + 12, fy))

    # --- main loop -----------------------------------------------------------
    def run(self):
        while self.running:
            self.events()
            if self.mode == "play":
                self.apply_keys()
                for _ in range(self.speed):
                    self.e.emu.cycle(False); self.frame += 1
            else:  # edit: keep the emulator LIVE but suppress player input, so
                   # RAM pokes render instantly and idle NPCs animate in place
                self.e.emu.input.keypad_update(0)
                self.e.emu.cycle(False); self.frame += 1
                self._refresh_live()
            self.draw()
            self.clock.tick(FPS)
        if self.seed:
            self.e.savestate(self.seed)
        pygame.quit()


def main():
    state = None
    args = sys.argv[1:]
    if "--state" in args:
        state = args[args.index("--state") + 1]
        if not os.path.isabs(state):
            state = os.path.abspath(state)
    LiveEditor(state).run()


if __name__ == "__main__":
    main()
