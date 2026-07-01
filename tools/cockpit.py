#!/usr/bin/env python3
"""Apocrypha Cockpit -- a live play + monitor + annotate front-end for the ROM.

One process. You PLAY the ROM in a real-time window; a side panel shows live RAM
ground truth (map / player tile / scene vars / nearby NPCs) sampled straight from
emu_ram.py; and at any moment you can PAUSE and ANNOTATE -- draw a box on a tile or
NPC, type a note, and the cockpit writes a "mark" (annotated PNG + a JSON/markdown
sidecar resolving what you circled to its engine entity) into the marks dir. Those
marks are the dialogue substrate: Claude reads them and we decide what to change.

Run (inside .emu-venv):
    source .emu-venv/bin/activate
    python tools/cockpit.py                 # fresh boot
    python tools/cockpit.py --state cur_cherrygrove.dsv   # seed from a checkpoint

Controls (PLAY mode):
    Arrow keys .......... D-pad
    Z / X ............... A / B
    A / S ............... Y / X
    Q / W ............... L / R
    Enter .............. START      RShift ... SELECT
    Mouse on bottom screen .. touch input
    `[` / `]` .......... emulation speed down / up   (turbo = hold Tab? no -- see below)
    Space .............. PAUSE + enter ANNOTATE mode
    F5 ................. quick savestate    F9 ... quick loadstate
    Esc ................ quit (auto-saves state)

Controls (ANNOTATE mode -- emulation frozen):
    Mouse drag ......... draw a box over the tile/NPC you mean
    Type ............... your note (Space types a space -- it does NOT resume)
    Enter .............. SAVE the mark (writes PNG + sidecar) and resume play
    Backspace .......... edit note
    Esc ................ cancel -- resume play without saving (does not quit app)
"""
import os, sys, json, time
sys.path.insert(0, os.path.dirname(__file__))

import pygame
from desmume.controls import keymask, Keys
from emu_harness import Emu
import emu_ram as R

# --- layout ------------------------------------------------------------------
SCALE   = 2                      # DS native 256x384 -> 512x768
DS_W, DS_H = 256, 384
SCREEN_SPLIT = 192               # top screen is rows 0..191, bottom 192..383
PANEL_W = 380
WIN_W   = DS_W * SCALE + PANEL_W
WIN_H   = DS_H * SCALE
FPS     = 60

MARKS_DIR = os.path.join(os.path.dirname(__file__), "..", "cockpit_marks")
MARKS_DIR = os.path.abspath(MARKS_DIR)
QUICK_STATE = os.path.join(os.path.dirname(__file__), "..", "cockpit_quick.dsv")
QUICK_STATE = os.path.abspath(QUICK_STATE)

# --- pixel -> tile projection (TUNABLE; calibrate by walking known tiles) -----
# HGSS centers the player near the upper-middle of the top screen. A tile is
# 16 native px. (player_px_x, player_px_y) is where the player sprite's tile
# sits on the top screen in native coords. Adjust these two if marks land off.
PLAYER_PX_X = 128   # calibrated against mark_001 (player tile vs Mom @ +1 north)
PLAYER_PX_Y = 88
TILE_PX     = 16

# keyboard -> DS key map
KEYMAP = {
    pygame.K_UP: Keys.KEY_UP, pygame.K_DOWN: Keys.KEY_DOWN,
    pygame.K_LEFT: Keys.KEY_LEFT, pygame.K_RIGHT: Keys.KEY_RIGHT,
    pygame.K_z: Keys.KEY_A, pygame.K_x: Keys.KEY_B,
    pygame.K_a: Keys.KEY_Y, pygame.K_s: Keys.KEY_X,
    pygame.K_q: Keys.KEY_L, pygame.K_w: Keys.KEY_R,
    pygame.K_RETURN: Keys.KEY_START, pygame.K_RSHIFT: Keys.KEY_SELECT,
}

# scene vars to watch on the panel + in the timeline (extend freely)
WATCH_VARS = [R.VAR_SCENE_CHERRYGROVE_CITY_OW, R.VAR_SCENE_PLAYERS_HOUSE_1F]


def fb_to_surface(emu):
    """Raw RGBX framebuffer -> pygame Surface (no PIL encode; fast).
    `emu` is the emu_harness.Emu wrapper; the DeSmuME core is emu.emu."""
    buf = emu.emu.display_buffer_as_rgbx()
    # py-desmume buffer is RGBX, row-major, 256x384 (top stacked over bottom)
    surf = pygame.image.frombuffer(bytes(buf), (DS_W, DS_H), "RGBX")
    return surf


def project_pixel_to_tile(px_native_x, px_native_y, player_tile):
    """Top-screen native pixel -> world tile, using the player as the anchor."""
    dx = round((px_native_x - PLAYER_PX_X) / TILE_PX)
    dz = round((px_native_y - PLAYER_PX_Y) / TILE_PX)
    return (player_tile[0] + dx, player_tile[1] + dz)


class Cockpit:
    def __init__(self, state=None):
        self.e = Emu()
        self.e.wait(8)
        if state and os.path.exists(state):
            self.e.loadstate(state); self.e.wait(8)
            self.seed = state
        else:
            self.seed = None
        os.makedirs(MARKS_DIR, exist_ok=True)

        pygame.init()
        pygame.display.set_caption("Apocrypha Cockpit")
        self.win = pygame.display.set_mode((WIN_W, WIN_H))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Menlo", 14)
        self.font_sm = pygame.font.SysFont("Menlo", 12)
        self.font_bold = pygame.font.SysFont("Menlo", 15, bold=True)

        self.mode = "play"            # "play" | "annotate"
        self.frozen_snap = None       # RAM sampled at the instant of freeze (mark truth)
        self.running = True
        self.frame = 0
        self.speed = 1                # emulation cycles per rendered frame
        self.note = ""
        self.box = None               # (x0,y0,x1,y1) in window coords, top screen
        self.drag_start = None
        self.timeline = []            # recent (frame, text) events
        self.last_loc_key = None
        self.last_vars = {}
        self.mark_count = len(os.listdir(MARKS_DIR)) if os.path.isdir(MARKS_DIR) else 0
        self.status = "ready"

    # --- RAM sampling --------------------------------------------------------
    def sample(self):
        try:
            l = R.loc(self.e)
            objs = R.objects(self.e)
        except Exception as ex:
            return {"err": str(ex)}
        px = next((o for o in objs if o["id"] == 255), None)
        vars_now = {}
        for v in WATCH_VARS:
            try: vars_now[v] = R.var(self.e, v)
            except Exception: vars_now[v] = None
        snap = {"map": l["mapId"], "player": (px["x"], px["z"]) if px else (l["x"], l["z"]),
                "face": px["dirname"] if px else "?", "objs": objs, "vars": vars_now}
        # timeline: log map changes + watched-var flips
        key = (snap["map"],)
        if key != self.last_loc_key:
            if self.last_loc_key is not None:
                self.timeline.append((self.frame, f"map -> {snap['map']}"))
            self.last_loc_key = key
        for v, val in vars_now.items():
            if v in self.last_vars and self.last_vars[v] != val:
                self.timeline.append((self.frame, f"var {hex(v)}: {self.last_vars[v]}->{val}"))
        self.last_vars = dict(vars_now)
        self.timeline = self.timeline[-12:]
        return snap

    # --- input ---------------------------------------------------------------
    def apply_keys(self):
        pressed = pygame.key.get_pressed()
        mask = 0
        for pk, dk in KEYMAP.items():
            if pressed[pk]:
                mask |= keymask(dk)
        self.e.emu.input.keypad_update(mask)

    def handle_mouse_play(self):
        # touch on the bottom screen
        mx, my = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0] and mx < DS_W * SCALE and my >= SCREEN_SPLIT * SCALE:
            tx = mx // SCALE
            ty = (my // SCALE) - SCREEN_SPLIT
            if 0 <= tx < DS_W and 0 <= ty < SCREEN_SPLIT:
                self.e.emu.input.touch_set_pos(tx, ty)
        else:
            self.e.emu.input.touch_release()

    # --- annotate ------------------------------------------------------------
    def save_mark(self, snap):
        ts = int(time.time())
        idx = self.mark_count + 1
        base = f"mark_{idx:03d}_{ts}"
        png_path = os.path.join(MARKS_DIR, base + ".png")
        json_path = os.path.join(MARKS_DIR, base + ".json")
        md_path = os.path.join(MARKS_DIR, base + ".md")

        # render the frozen frame + box to a native-res surface and save
        frame = fb_to_surface(self.e)
        top = frame.subsurface((0, 0, DS_W, SCREEN_SPLIT)).copy()
        circled_tile = circled_obj = None
        if self.box:
            x0, y0, x1, y1 = self.box
            nx0, ny0 = x0 // SCALE, y0 // SCALE
            nx1, ny1 = x1 // SCALE, y1 // SCALE
            pygame.draw.rect(top, (255, 40, 40), (nx0, ny0, nx1 - nx0, ny1 - ny0), 1)
            cx, cy = (nx0 + nx1) // 2, (ny0 + ny1) // 2
            circled_tile = project_pixel_to_tile(cx, cy, snap["player"])
            # box-range match: project all four-corner extents to tiles, keep any NPC
            # whose tile falls inside the box (+1 tile margin), nearest-to-center wins.
            tA = project_pixel_to_tile(nx0, ny0, snap["player"])
            tB = project_pixel_to_tile(nx1, ny1, snap["player"])
            xlo, xhi = min(tA[0], tB[0]) - 1, max(tA[0], tB[0]) + 1
            zlo, zhi = min(tA[1], tB[1]) - 1, max(tA[1], tB[1]) + 1
            cand = [o for o in snap["objs"] if o["id"] != 255
                    and xlo <= o["x"] <= xhi and zlo <= o["z"] <= zhi]
            if cand:
                circled_obj = min(cand, key=lambda o:
                                  abs(o["x"] - circled_tile[0]) + abs(o["z"] - circled_tile[1]))
        pygame.image.save(top, png_path)

        data = {
            "mark": idx, "ts": ts, "note": self.note,
            "map": snap["map"], "player_tile": snap["player"], "player_face": snap["face"],
            "circled_tile": circled_tile,
            "circled_object": circled_obj,
            "scene_vars": {hex(k): v for k, v in snap["vars"].items()},
            "all_objects": [{"id": o["id"], "sprite": o["sprite"], "x": o["x"], "z": o["z"],
                             "face": o["dirname"]} for o in snap["objs"]],
            "recent_timeline": [{"frame": f, "event": t} for f, t in self.timeline],
            "png": os.path.relpath(png_path, os.path.dirname(MARKS_DIR)),
        }
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)
        with open(md_path, "w") as f:
            f.write(f"# Mark {idx}\n\n**Note:** {self.note or '(none)'}\n\n")
            f.write(f"- Map: `{snap['map']}`  player tile `{snap['player']}` facing `{snap['face']}`\n")
            if circled_tile:
                f.write(f"- Circled tile: `{circled_tile}`\n")
            if circled_obj:
                f.write(f"- Circled NPC: id `{circled_obj['id']}` sprite `{circled_obj['sprite']}` "
                        f"@ `({circled_obj['x']},{circled_obj['z']})` facing `{circled_obj['dirname']}`\n")
            f.write(f"- Scene vars: " + ", ".join(f"`{hex(k)}={v}`" for k, v in snap["vars"].items()) + "\n")
            f.write(f"\n![mark]({os.path.basename(png_path)})\n")

        self.mark_count = idx
        self.status = f"saved {base} -> cockpit_marks/"
        self.note = ""; self.box = None

    # --- rendering -----------------------------------------------------------
    def draw_panel(self, snap):
        x0 = DS_W * SCALE
        pygame.draw.rect(self.win, (18, 20, 28), (x0, 0, PANEL_W, WIN_H))
        y = 10
        def line(txt, color=(210, 220, 230), font=None, dy=18):
            nonlocal y
            self.win.blit((font or self.font).render(txt, True, color), (x0 + 12, y))
            y += dy

        mode_col = (120, 230, 140) if self.mode == "play" else (255, 200, 90)
        line(f"[{self.mode.upper()}]  speed x{self.speed}  {self.clock.get_fps():4.1f}fps",
             mode_col, self.font_bold, 24)
        if snap.get("err"):
            line("RAM: " + snap["err"][:36], (255, 120, 120)); return
        line(f"map  {snap['map']}", (180, 220, 255))
        line(f"tile {snap['player']}  facing {snap['face']}", (180, 220, 255))
        y += 6
        line("scene vars", (150, 160, 175), self.font_sm, 16)
        for v, val in snap["vars"].items():
            line(f"  {hex(v)} = {val}", (200, 210, 220), self.font_sm, 15)
        y += 6
        line(f"NPCs nearby", (150, 160, 175), self.font_sm, 16)
        px, pz = snap["player"]
        near = [o for o in snap["objs"] if o["id"] != 255
                and abs(o["x"] - px) <= 12 and abs(o["z"] - pz) <= 12]
        for o in near[:10]:
            line(f"  id{o['id']:>3} spr{o['sprite']:>3} ({o['x']},{o['z']}){o['dirname']}",
                 (200, 210, 220), self.font_sm, 15)
        if not near:
            line("  (none within 12)", (130, 140, 150), self.font_sm, 15)
        y += 8
        line("timeline", (150, 160, 175), self.font_sm, 16)
        for f, t in self.timeline[-6:]:
            line(f"  {f:>6} {t}", (190, 185, 160), self.font_sm, 15)

        # footer: annotate note + status
        fy = WIN_H - 70
        pygame.draw.line(self.win, (50, 55, 65), (x0 + 8, fy - 8), (x0 + PANEL_W - 8, fy - 8))
        self.win.blit(self.font_sm.render(f"marks: {self.mark_count}", True, (150, 160, 175)),
                      (x0 + 12, fy))
        if self.mode == "annotate":
            self.win.blit(self.font_sm.render("note> " + self.note + "_", True, (255, 220, 120)),
                          (x0 + 12, fy + 18))
        self.win.blit(self.font_sm.render(self.status[:44], True, (120, 200, 140)),
                      (x0 + 12, fy + 38))

    def draw(self, snap):
        frame = fb_to_surface(self.e)
        scaled = pygame.transform.scale(frame, (DS_W * SCALE, DS_H * SCALE))
        self.win.blit(scaled, (0, 0))
        # screen divider
        pygame.draw.line(self.win, (40, 40, 50), (0, SCREEN_SPLIT * SCALE),
                         (DS_W * SCALE, SCREEN_SPLIT * SCALE), 2)
        # live annotation box
        if self.box:
            x0, y0, x1, y1 = self.box
            pygame.draw.rect(self.win, (255, 40, 40), (x0, y0, x1 - x0, y1 - y0), 2)
        if self.mode == "annotate":
            ov = pygame.Surface((DS_W * SCALE, 22)); ov.set_alpha(140); ov.fill((0, 0, 0))
            self.win.blit(ov, (0, 0))
            self.win.blit(self.font_sm.render(
                "ANNOTATE  drag a box  -  type note (Space ok)  -  Enter=save  Esc=cancel",
                True, (255, 220, 120)), (6, 4))
        self.draw_panel(snap)
        pygame.display.flip()

    # --- event handling ------------------------------------------------------
    def events(self, snap):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False
            elif ev.type == pygame.KEYDOWN:
                if self.mode == "play":
                    if ev.key == pygame.K_ESCAPE:
                        self.running = False
                    elif ev.key == pygame.K_SPACE:
                        # sample RAM fresh at the freeze instant so the mark's engine
                        # data always matches the frozen frame (never a stale snap).
                        self.mode = "annotate"; self.frozen_snap = self.sample()
                        self.status = "annotating (frozen)"
                    elif ev.key == pygame.K_LEFTBRACKET:
                        self.speed = max(0, self.speed - 1)
                    elif ev.key == pygame.K_RIGHTBRACKET:
                        self.speed = min(8, self.speed + 1)
                    elif ev.key == pygame.K_F5:
                        self.e.savestate(QUICK_STATE); self.status = "quick-saved"
                    elif ev.key == pygame.K_F9 and os.path.exists(QUICK_STATE):
                        self.e.loadstate(QUICK_STATE); self.status = "quick-loaded"
                else:  # annotate -- Space types a space; Esc resumes; Enter saves+resumes
                    if ev.key == pygame.K_ESCAPE:
                        self.mode = "play"; self.box = None; self.note = ""
                        self.frozen_snap = None
                        self.e.emu.input.keypad_update(0)
                    elif ev.key == pygame.K_RETURN:
                        self.save_mark(self.frozen_snap or snap)
                        self.mode = "play"; self.frozen_snap = None
                        self.e.emu.input.keypad_update(0)
                    elif ev.key == pygame.K_BACKSPACE:
                        self.note = self.note[:-1]
                    elif ev.unicode and ev.unicode.isprintable():
                        self.note += ev.unicode
            elif ev.type == pygame.MOUSEBUTTONDOWN and self.mode == "annotate":
                mx, my = ev.pos
                if mx < DS_W * SCALE and my < SCREEN_SPLIT * SCALE:
                    self.drag_start = (mx, my); self.box = (mx, my, mx, my)
            elif ev.type == pygame.MOUSEMOTION and self.mode == "annotate" and self.drag_start:
                x0, y0 = self.drag_start
                self.box = (min(x0, ev.pos[0]), min(y0, ev.pos[1]),
                            max(x0, ev.pos[0]), max(y0, ev.pos[1]))
            elif ev.type == pygame.MOUSEBUTTONUP and self.mode == "annotate":
                self.drag_start = None

    # --- main loop -----------------------------------------------------------
    def run(self):
        snap = self.sample() or {}
        while self.running:
            self.events(snap)
            if self.mode == "play":
                self.apply_keys()
                self.handle_mouse_play()
                for _ in range(self.speed):
                    self.e.emu.cycle(False)
                    self.frame += 1
                if self.frame % 8 == 0:
                    snap = self.sample() or snap
            # in annotate mode show the freeze-instant sample, not a drifting one
            self.draw(self.frozen_snap if (self.mode == "annotate" and self.frozen_snap) else snap)
            self.clock.tick(FPS)
        # graceful exit: persist where you left off
        if self.seed:
            self.e.savestate(self.seed)
            self.status = f"saved -> {self.seed}"
        pygame.quit()


def main():
    state = None
    args = sys.argv[1:]
    if "--state" in args:
        state = args[args.index("--state") + 1]
        if not os.path.isabs(state):
            state = os.path.abspath(state)
    Cockpit(state).run()


if __name__ == "__main__":
    main()
