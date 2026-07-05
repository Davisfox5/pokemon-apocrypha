#!/usr/bin/env python3
"""Child-proof NPC behavior editing: turn plain-English choices into the verified
engine recipes (see memory: hgss-npc-behavior-scripting).

Capabilities
  simple_behavior(...)   "always stands / wanders / paces"      -> JSON only
  behavior_switch(...)   "X until <story moment>, then Y"       -> two-object flag
                         swap: clone object, allocate spare flags, gate spawns,
                         inject guarded hide+swap blocks into the map's scripts
  add_walk(...)          "walk from their spot to a tile when a scene starts/ends"
                         -> .balign'd step table + apply_movement injection

All script injections are tagged `; [editor-behavior]` and guarded by flags so
they run exactly once. Generators refuse to run twice for the same object.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

DECOMP = Path(__file__).resolve().parents[2] / "disasm" / "pokeheartgold"
SCR_DIR = DECOMP / "files" / "fielddata" / "script" / "scr_seq"
FLAGS_H = DECOMP / "include" / "constants" / "flags.h"

MARK = "; [editor-behavior]"

# behavior name -> (movement, xRange, yRange) — ranges None = keep/upgrade existing
BEHAVIORS = {
    "stand":   (0, None, None),
    "wander":  (3, 3, 3),
    "pace_lr": (5, 1, 0),
    "pace_ud": (7, 0, 1),
}
BEHAVIOR_LABEL = {
    "stand": "stands still",
    "wander": "wanders around",
    "pace_lr": "paces left and right",
    "pace_ud": "paces up and down",
}


# --------------------------------------------------------------------------- #
#  map script plumbing
# --------------------------------------------------------------------------- #
def _map_files(map_name: str):
    hdr = next((p for p in SCR_DIR.glob(f"scr_seq_*_{map_name}_hdr.s")), None)
    scr = next((p for p in sorted(SCR_DIR.glob(f"scr_seq_*_{map_name}.s"))
                if not p.name.endswith("_hdr.s")), None)
    evh = SCR_DIR / f"event_{map_name}.h"
    return hdr, scr, evh


@dataclass
class Moment:
    var: str
    val: int
    macro: str          # _EV_scr_seq_<MAP>_NNN
    label: str          # scr_seq_<MAP>_NNN
    desc: str = ""      # plain-English snippet


def list_moments(map_name: str) -> list:
    """Story moments = the map's auto-run scene scripts, in scene order."""
    hdr, _, _ = _map_files(map_name)
    if not hdr:
        return []
    out = []
    for m in re.finditer(
            r"\.short\s+(VAR_\w+)\s*,\s*(\d+)\s*,\s*(_EV_scr_seq_(\w+?)_(\d+))\s*\+\s*1",
            hdr.read_text()):
        var, val, macro, mn, num = m.group(1), int(m.group(2)), m.group(3), m.group(4), m.group(5)
        out.append(Moment(var, val, macro, f"scr_seq_{mn}_{num}"))
    # plain-English labels from the dialogue each scene speaks
    try:
        import describe as D
        for mo in out:
            _, texts = D.script_dialogue(map_name, mo.macro + " + 1")
            if texts:
                snip = texts[0][:60] + ("…" if len(texts[0]) > 60 else "")
                mo.desc = f'the scene where someone says "{snip}"'
            else:
                mo.desc = f"story scene #{mo.val} on this map"
    except Exception:
        for mo in out:
            mo.desc = f"story scene #{mo.val}"
    return sorted(out, key=lambda m: m.val)


def entry_moment(map_name: str):
    ms = list_moments(map_name)
    return ms[0] if ms else None


# --------------------------------------------------------------------------- #
#  spare flag allocation (vacated pool, zero live references)
# --------------------------------------------------------------------------- #
def _flag_pool() -> list:
    """Vacated-candidate FLAG_ names in a stable order."""
    names = []
    for m in re.finditer(r"#define\s+(FLAG_HIDE_ROCKET_HIDEOUT\w*)\s+0x",
                         FLAGS_H.read_text()):
        names.append(m.group(1))
    return names


# The hack's story vacated the Rocket hideout, so references confined to its own
# maps (D35*) and their shared script bank (0149) don't count as "in use" — the
# precedent set when the hack reused B3F/B2F_MURKROW_1 for Kestra and Mom.
_EXEMPT = re.compile(r"(_D35|scr_seq_0149\.s)")


def allocate_flags(n: int) -> list:
    """First n pool flags with no live references (audit per the mom fix)."""
    got = []
    for name in _flag_pool():
        if len(got) >= n:
            break
        used = False
        for p in SCR_DIR.glob("*.s"):
            if _EXEMPT.search(p.name):
                continue
            if re.search(r"\b" + re.escape(name) + r"\b", p.read_text()):
                used = True
                break
        if not used:
            # also not used as any object's spawn gate (outside the vacated hideout)
            for p in (DECOMP / "files" / "fielddata" / "eventdata" / "zone_event").glob("*.json"):
                if _EXEMPT.search(p.name):
                    continue
                if name in p.read_text():
                    used = True
                    break
        if not used:
            got.append(name)
    if len(got) < n:
        raise RuntimeError(f"only {len(got)} spare flags free (need {n})")
    return got


# --------------------------------------------------------------------------- #
#  script surgery helpers
# --------------------------------------------------------------------------- #
def _next_marker_n(text: str) -> int:
    ns = [int(x) for x in re.findall(r"_edbh_(\d+)_", text)]
    return (max(ns) + 1) if ns else 1


def _section(text: str, label: str):
    """(start, end) character span of a script label's body (to next col-0 label)."""
    m = re.search(rf"^{re.escape(label)}:\s*$", text, re.M)
    if not m:
        raise RuntimeError(f"script label {label} not found")
    start = m.end()
    nxt = re.search(r"^\w+:\s*$", text[start:], re.M)
    end = start + (nxt.start() if nxt else len(text) - start)
    return start, end


def _insert_before_last_releaseall(text: str, label: str, block: str) -> str:
    """Insert just before the scene's terminal `releaseall`/`end` pair. Scenes may
    contain local continuation labels (e.g. _007_done:), so scan forward from the
    label for the first releaseall+end — every code path funnels through it,
    which is exactly the 'moment completed' semantics we want."""
    m = re.search(rf"^{re.escape(label)}:\s*$", text, re.M)
    if not m:
        raise RuntimeError(f"script label {label} not found")
    m2 = re.search(r"^\treleaseall[ \t]*\n\tend[ \t]*$", text[m.end():], re.M)
    if not m2:
        raise RuntimeError(f"{label}: no releaseall/end to anchor on")
    pos = m.end() + m2.start()
    return text[:pos] + block + text[pos:]


def _insert_after_lockall(text: str, label: str, block: str) -> str:
    s, e = _section(text, label)
    body = text[s:e]
    m = re.search(r"\tlockall\s*\n", body)
    pos = m.end() if m else 0
    return text[:s] + body[:pos] + block + body[pos:] + text[e:]


# --------------------------------------------------------------------------- #
#  generators
# --------------------------------------------------------------------------- #
def simple_behavior(ref: dict, behavior: str) -> str:
    mv, xr, yr = BEHAVIORS[behavior]
    ref["movement"] = mv
    if xr is not None:
        ref["xRange"] = max(int(ref.get("xRange", 0) or 0), xr) if xr else xr
    if yr is not None:
        ref["yRange"] = max(int(ref.get("yRange", 0) or 0), yr) if yr else yr
    return f'now always {BEHAVIOR_LABEL[behavior]}'


@dataclass
class Plan:
    """Everything a generator intends to write, for preview + apply."""
    summary: list = field(default_factory=list)
    json_path: Path = None
    json_data: dict = None
    writes: list = field(default_factory=list)   # (path, new_text)

    def apply(self):
        for p, t in self.writes:
            Path(p).write_text(t)
        if self.json_path is not None:
            Path(self.json_path).write_text(json.dumps(self.json_data, indent=2) + "\n")


def behavior_switch(map_name: str, json_path: Path, obj_id_name: str,
                    before: str, after: str, moment: Moment) -> Plan:
    """X-until-moment-then-Y via the verified two-object flag swap."""
    hdr, scr, evh = _map_files(map_name)
    if not scr or not evh.exists():
        raise RuntimeError("this map has no editable scripts")
    data = json.loads(Path(json_path).read_text())
    objs = data.get("objects", [])
    src = next((o for o in objs if o.get("id") == obj_id_name), None)
    if src is None:
        raise RuntimeError(f"{obj_id_name} not in {json_path.name}")
    if any(o.get("id") == obj_id_name + "_after" for o in objs):
        raise RuntimeError("this character already has a story switch (remove it first)")
    scr_text = scr.read_text()
    if f"{MARK} {obj_id_name}:" in scr_text:
        raise RuntimeError("this character already has a story switch in the scripts")

    beat_flag, hide_flag = allocate_flags(2)
    ent = entry_moment(map_name)
    if ent is None:
        raise RuntimeError("this map has no scene table - story switching needs one")

    # --- JSON: retune original ("before" behavior + gate on beat flag), clone after-self
    plan = Plan(json_path=Path(json_path), json_data=data)
    simple_behavior(src, before)
    src["eventFlag"] = beat_flag
    clone = dict(src)
    clone["id"] = obj_id_name + "_after"
    simple_behavior(clone, after)
    clone["eventFlag"] = hide_flag
    objs.append(clone)
    new_index = len(objs) - 1

    # --- event header: define for the clone
    evh_text = evh.read_text()
    if f" {obj_id_name} " not in evh_text and f"{obj_id_name} " not in evh_text:
        raise RuntimeError(f"{obj_id_name} missing from {evh.name}")
    last_def = list(re.finditer(r"#define\s+obj_\w+\s+\d+\n", evh_text))[-1]
    evh_new = (evh_text[:last_def.end()]
               + f"#define {obj_id_name}_after {new_index}\n"
               + evh_text[last_def.end():])
    plan.writes.append((evh, evh_new))

    # --- scripts: hide clone at the entry scene; swap at the chosen moment
    n = _next_marker_n(scr_text)
    hide_block = (
        f"\t{MARK} {obj_id_name}: keep the after-version hidden until its moment\n"
        f"\tgoto_if_set {hide_flag}, _edbh_{n}_hid\n"
        f"\thide_person {obj_id_name}_after\n"
        f"_edbh_{n}_hid:\n")
    swap_block = (
        f"\t{MARK} {obj_id_name}: switch {BEHAVIOR_LABEL[before]} -> {BEHAVIOR_LABEL[after]}\n"
        f"\tgoto_if_set {beat_flag}, _edbh_{n}_done\n"
        f"\tsetflag {beat_flag}\n"
        f"\thide_person {obj_id_name}\n"
        f"\twait 8, VAR_SPECIAL_RESULT\n"
        f"\tclearflag {hide_flag}\n"
        f"\tshow_person {obj_id_name}_after\n"
        f"_edbh_{n}_done:\n")
    text = _insert_after_lockall(scr_text, ent.label, hide_block)
    text = _insert_before_last_releaseall(text, moment.label, swap_block)
    plan.writes.append((scr, text))

    plan.summary = [
        f"{BEHAVIOR_LABEL[before].capitalize()} at ({src.get('x')},{src.get('z')}) "
        f"until {moment.desc}.",
        f"After that: {BEHAVIOR_LABEL[after]} (from the same spot), forever.",
        f"(uses spare switches {beat_flag} + {hide_flag})",
    ]
    return plan


_STEP = {"up": 12, "down": 13, "left": 14, "right": 15}
_FACE = {"up": 0, "down": 1, "left": 2, "right": 3}


def add_walk(map_name: str, obj_id_name: str, moment: Moment, when: str,
             start_tile, dest_tile, face: str | None = None) -> Plan:
    """Walk a character between two fixed tiles when a scene starts or ends."""
    _, scr, _ = _map_files(map_name)
    if not scr:
        raise RuntimeError("this map has no editable scripts")
    text = scr.read_text()
    n = _next_marker_n(text)
    sx, sz = start_tile; dx, dz = dest_tile
    steps = []
    if dz != sz:
        steps.append((_STEP["up" if dz < sz else "down"], abs(dz - sz)))
    if dx != sx:
        steps.append((_STEP["left" if dx < sx else "right"], abs(dx - sx)))
    if face:
        steps.append((_FACE[face], 1))
    if not steps:
        raise RuntimeError("that walk goes nowhere")
    tbl = "".join(f"\tstep {a}, {b}\n" for a, b in steps)
    table = (f"\n\t.balign 4, 0\n"
             f"{MARK} walk for {obj_id_name} ({when} of {moment.label})\n"
             f"_edbh_{n}_walk:\n{tbl}\tstep_end\n\t.balign 4, 0\n")
    call = (f"\t{MARK} {obj_id_name} walks ({sx},{sz}) -> ({dx},{dz})\n"
            f"\tapply_movement {obj_id_name}, _edbh_{n}_walk\n"
            f"\twait_movement\n")
    if when == "start":
        text = _insert_after_lockall(text, moment.label, call)
    else:
        text = _insert_before_last_releaseall(text, moment.label, call)
    text = text.rstrip("\n") + "\n" + table
    plan = Plan()
    plan.writes.append((scr, text))
    plan.summary = [f"When {moment.desc} {'starts' if when=='start' else 'ends'}, "
                    f"{obj_id_name.split('_')[-1]} walks from ({sx},{sz}) to ({dx},{dz})"
                    + (f", then faces {face}." if face else ".")]
    return plan
