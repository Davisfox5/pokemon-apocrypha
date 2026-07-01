#!/usr/bin/env python3
"""Plain-English descriptions of zone_event entries for the map editor.

Turns raw event data into human sentences a newbie can read:
  * the ACTUAL DIALOGUE an NPC / sign speaks (scriptId -> script body -> msg text)
  * WHEN a hidden object appears (eventFlag -> which script clears it)
  * where a warp leads, what a trigger tile does, which way an NPC faces, etc.

Ground truth is the decomp source under disasm/pokeheartgold, so it stays correct
as the hack is edited:
  event_<MAP>.h    label -> script index
  scr_seq_*_<MAP>.s  script bodies (msg_* references, goto/call)
  msg_*_<MAP>.h    message text (as // comments above each #define)
  scr_seq_*.s      setflag/clearflag <FLAG> (story conditions)
"""
from __future__ import annotations

import functools
import re
from dataclasses import dataclass, field
from pathlib import Path

DECOMP = Path(__file__).resolve().parents[2] / "disasm" / "pokeheartgold"
SCR_DIR = DECOMP / "files" / "fielddata" / "script" / "scr_seq"
MSG_DIR = DECOMP / "files" / "msgdata" / "msg"

DIR_WORD = {0: "up", 1: "down", 2: "left", 3: "right"}

# Object idle-movement behaviour. These values index an engine action table with
# no named enum in the decomp, so anything not listed shows its raw id honestly
# rather than a guessed behaviour.
MOVE_WORD = {
    0: "stands still",
    1: "looks around in place",
    2: "wanders nearby",
    3: "wanders nearby",
    4: "wanders in a small area",
    5: "paces back and forth",
    6: "paces back and forth",
    7: "paces up and down",
    8: "paces up and down",
}


def movement_phrase(n) -> str:
    try:
        n = int(n)
    except (TypeError, ValueError):
        return "moves"
    w = MOVE_WORD.get(n)
    return w if w else f"moves (pattern {n})"


def facing_phrase(n) -> str:
    return f"faces {DIR_WORD.get(int(n), '?')}" if n is not None else ""


def humanize_sprite(sprite_id) -> str:
    """SPRITE_GSMIDDLEMAN1 -> 'Gsmiddleman 1'.  Not perfect, but readable."""
    s = str(sprite_id)
    s = re.sub(r"^SPRITE_", "", s)
    s = s.replace("_", " ").strip().title()
    s = re.sub(r"([A-Za-z])(\d)", r"\1 \2", s)   # split trailing digits
    return s or "Object"


def humanize_map(header) -> str:
    """MAP_CHERRYGROVE -> 'Cherrygrove'."""
    s = str(header)
    s = re.sub(r"^MAP_", "", s)
    return s.replace("_", " ").title() or "somewhere"


def humanize_var(var) -> str:
    s = str(var)
    s = re.sub(r"^VAR_(SCENE_)?", "", s)
    return s.replace("_", " ").title()


def clean_text(t: str) -> str:
    """Message text uses \\n (soft wrap) and \\r (page break); flatten to one line."""
    t = t.replace("\\n", " ").replace("\\r", " / ").replace("\\f", " / ")
    t = re.sub(r"\{[^}]*\}", "", t)              # drop {control codes}
    return re.sub(r"\s+", " ", t).strip()


# --------------------------------------------------------------------------- #
#  script / dialogue resolution
# --------------------------------------------------------------------------- #
def map_name_of(zone) -> str | None:
    """'fielddata/script/scr_seq/event_T21R0301.h' -> 'T21R0301'."""
    hdr = (getattr(zone, "data", {}) or {}).get("header", "")
    m = re.search(r"event_([A-Za-z0-9]+)\.h", str(hdr))
    return m.group(1) if m else None


@functools.lru_cache(maxsize=None)
def _header_syms(map_name: str) -> dict:
    p = SCR_DIR / f"event_{map_name}.h"
    if not p.exists():
        return {}
    return {m.group(1): int(m.group(2))
            for m in re.finditer(r"#define\s+(\w+)\s+(\d+)", p.read_text())}


@functools.lru_cache(maxsize=None)
def _script_file(map_name: str) -> Path | None:
    for p in sorted(SCR_DIR.glob(f"scr_seq_*_{map_name}.s")):
        if not p.name.endswith("_hdr.s"):
            return p
    return None


@functools.lru_cache(maxsize=None)
def _bodies(map_name: str) -> dict:
    """label -> [source lines] up to the next label."""
    p = _script_file(map_name)
    if not p:
        return {}
    out, cur = {}, None
    for ln in p.read_text().splitlines():
        m = re.match(r"^(\w+):", ln)
        if m:
            cur = m.group(1)
            out[cur] = []
        elif cur is not None:
            out[cur].append(ln.strip())
    return out


@functools.lru_cache(maxsize=None)
def _msg_texts(stem: str) -> dict:
    p = MSG_DIR / f"{stem}.h"
    if not p.exists():
        return {}
    out, pending = {}, None
    for ln in p.read_text().splitlines():
        s = ln.strip()
        if s.startswith("//"):
            pending = s[2:].strip()
        elif s.startswith("#define"):
            m = re.match(r"#define\s+(msg_\w+)\s+\d+", s)
            if m and pending is not None:
                out[m.group(1)] = pending
            pending = None
        elif s:
            pending = None
    return out


def _msg_text(sym: str) -> str | None:
    txt = _msg_texts(sym.rsplit("_", 1)[0]).get(sym)
    return clean_text(txt) if txt else None


def _eval_scriptid(map_name: str, script_id):
    """Resolve a scriptId (symbolic expr, int, or std_* name) to a runtime value."""
    if isinstance(script_id, int):
        return script_id
    s = str(script_id).strip()
    if not s or s == "0":
        return 0
    if s.startswith("std_"):
        return s
    syms = _header_syms(map_name)
    expr = re.sub(r"[A-Za-z_]\w*", lambda m: str(syms.get(m.group(0), "None")), s)
    try:
        v = eval(expr, {"__builtins__": {}}, {})   # noqa: S307 - digits/ops only
        return int(v) if v is not None else None
    except Exception:
        return None


def _collect_msgs(map_name: str, label: str, depth=0, seen=None) -> list:
    """Message symbols in a script body, following goto/call one-file-deep."""
    seen = seen if seen is not None else set()
    if label in seen or depth > 4:
        return []
    seen.add(label)
    bodies = _bodies(map_name)
    out = []
    for ln in bodies.get(label, []):
        out += re.findall(r"\bmsg_\w+", ln)
        for tgt in re.findall(r"\b(?:goto|call)(?:_if\w*)?\s+([A-Za-z_]\w*)", ln):
            if tgt in bodies:
                out += _collect_msgs(map_name, tgt, depth + 1, seen)
    # de-dup, preserve order
    seen_msg, uniq = set(), []
    for m in out:
        if m not in seen_msg:
            seen_msg.add(m)
            uniq.append(m)
    return uniq


def _script_label(map_name: str, script_id):
    """Resolve a scriptId to its body label, or a ('std'|None) sentinel."""
    v = _eval_scriptid(map_name, script_id)
    if v == 0 or v is None:
        return None
    if isinstance(v, str):
        return "std"
    label = f"scr_seq_{map_name}_{v - 1:03d}"
    return label if label in _bodies(map_name) else None


def dialogue_items(map_name: str, script_id) -> list:
    """Editable message list for a script: [{'sym','text','raw'}], following
    goto/call one file deep. Text is cleaned for display; raw keeps \\n / \\r."""
    import gmm
    label = _script_label(map_name, script_id)
    if not label or label == "std":
        return []
    out = []
    for sym in _collect_msgs(map_name, label):
        raw = gmm.get_text(sym)
        if raw is None:
            continue
        out.append({"sym": sym, "text": clean_text(raw), "raw": raw})
    return out


# script command -> friendly step phrase
_STEP_RULES = [
    (re.compile(r"\b\w*_?msg\b|\bmessage\b|\btalk\b"), "💬", None),   # handled specially
    (re.compile(r"\bapplymovement\b|\bmovement\b"),    "🚶", "a character moves"),
    (re.compile(r"\bsetflag\s+(FLAG_\w+)"),            "🔧", "turns ON a switch ({0})"),
    (re.compile(r"\bclearflag\s+(FLAG_\w+)"),          "🔧", "turns OFF a switch ({0})"),
    (re.compile(r"\bsetvar\s+(\w+)\s*,?\s*(\w+)?"),    "📌", "sets story progress ({0})"),
    (re.compile(r"\b(?:give|obtain)\w*item\w*"),       "🎁", "gives the player an item"),
    (re.compile(r"\bgive\w*pokemon\b|\bgivemon\b"),    "🎁", "gives the player a Pokémon"),
    (re.compile(r"\bwarp\w*\b|\bteleport\b"),          "➡", "sends the player somewhere"),
    (re.compile(r"\btrainer\w*battle\b|\bdotrainer\b"), "⚔", "starts a Trainer battle"),
    (re.compile(r"\bwild\w*battle\b|\bencounter\b"),   "⚔", "starts a wild battle"),
    (re.compile(r"\bplay\w*(se|sound|cry|fanfare)\b"), "🔊", "plays a sound"),
    (re.compile(r"\bwait\w*\b|\bdelay\b|\bpause\b"),   "⏳", "waits a moment"),
    (re.compile(r"\bfade\w*|\bscreen\w*\b"),           "🎬", "screen effect"),
]


def script_steps(map_name: str, script_id, _label=None, _seen=None, _depth=0) -> list:
    """Ordered plain-English steps of a script's sequence: [(icon, text)]."""
    label = _label or _script_label(map_name, script_id)
    if not label or label == "std" or _depth > 4:
        return []
    _seen = _seen if _seen is not None else set()
    if label in _seen:
        return []
    _seen.add(label)
    steps = []
    for ln in _bodies(map_name).get(label, []):
        ln = ln.strip()
        if not ln or ln.startswith((".", "@", "#", "/")):
            continue
        cmd = ln.split()[0] if ln.split() else ""
        if cmd in ("end", "return", "scrdef", "scrdef_end", "waitmsg"):
            continue
        # a message reference?
        msyms = re.findall(r"\bmsg_\w+", ln)
        if msyms:
            for s in msyms:
                t = _msg_text(s)
                steps.append(("💬", f'says: "{t}"' if t else "shows a message"))
            continue
        # follow goto/call
        tgt = re.match(r"(?:goto|call)(?:_if\w*)?\s+.*?([A-Za-z_]\w*)\s*$", ln)
        if tgt and tgt.group(1) in _bodies(map_name):
            steps += script_steps(map_name, None, tgt.group(1), _seen, _depth + 1)
            continue
        matched = False
        for rx, icon, tmpl in _STEP_RULES[1:]:
            m = rx.search(ln)
            if m:
                arg = m.group(1) if m.groups() else ""
                steps.append((icon, tmpl.format(humanize_var(arg) if arg else "")))
                matched = True
                break
        if not matched:
            steps.append(("•", cmd.replace("_", " ")))
    return steps


def script_dialogue(map_name: str, script_id) -> tuple[str, list]:
    """Return (kind, texts). kind in {'none','trainer','std','script'}; texts are
    the plain-English lines this script speaks (may be empty)."""
    v = _eval_scriptid(map_name, script_id)
    if v == 0 or v is None:
        return ("none", [])
    if isinstance(v, str):                       # std_* name
        if "trainer" in v:
            return ("trainer", [])
        return ("std", [])
    label = f"scr_seq_{map_name}_{v - 1:03d}"    # runtime id is 1-based over scrdef
    if label not in _bodies(map_name):
        return ("script", [])
    texts = []
    for sym in _collect_msgs(map_name, label):
        t = _msg_text(sym)
        if t:
            texts.append(t)
    return ("script", texts)


# --------------------------------------------------------------------------- #
#  flag story conditions
# --------------------------------------------------------------------------- #
@functools.lru_cache(maxsize=1)
def _flag_index() -> dict:
    """FLAG_* -> {'setflag': {maps}, 'clearflag': {maps}} across all scripts."""
    idx: dict = {}
    for p in SCR_DIR.glob("scr_seq_*.s"):
        if p.name.endswith("_hdr.s"):
            continue
        mapname = re.sub(r"^scr_seq_\d+_", "", p.stem)
        txt = p.read_text()
        for verb in ("setflag", "clearflag"):
            for m in re.finditer(rf"\b{verb}\s+(FLAG_\w+)", txt):
                d = idx.setdefault(m.group(1), {"setflag": set(), "clearflag": set()})
                d[verb].add(mapname)
    return idx


def flag_story(flag_name: str) -> str:
    """Plain-English 'when does this flag flip' for a FLAG_HIDE_* style gate."""
    name = str(flag_name)
    if not name or name == "FLAG_NOTHING":
        return ""
    info = _flag_index().get(name)
    if not info:
        return "always visible (no script changes this)"
    clears = sorted(info["clearflag"])
    if clears:
        where = ", ".join(humanize_map("MAP_" + c) if not c.startswith(("T", "R", "D", "C"))
                          else c for c in clears[:3])
        return f"appears after a story event (script area: {where})"
    sets = sorted(info["setflag"])
    if sets:
        return f"hidden by a story event (script area: {', '.join(sets[:3])})"
    return "controlled by the story"


# --------------------------------------------------------------------------- #
#  top-level per-event description
# --------------------------------------------------------------------------- #
@dataclass
class Desc:
    icon: str
    title: str
    lines: list = field(default_factory=list)


def _dialogue_lines(kind: str, texts: list, speaker="Says") -> list:
    if kind == "trainer":
        return ['This is a Trainer — talk to them to battle.']
    if kind == "none":
        return []
    if kind == "std":
        return ['Runs a built-in game action (shop, healing, etc.).']
    if not texts:
        return ['Runs a script (no spoken text found).']
    out = []
    for t in texts[:3]:
        snip = t if len(t) <= 140 else t[:137] + "…"
        out.append(f'{speaker}: "{snip}"')
    if len(texts) > 3:
        out.append(f"…and {len(texts) - 3} more line(s).")
    return out


def describe_object(zone, obj: dict) -> Desc:
    mn = map_name_of(zone)
    sprite = humanize_sprite(obj.get("spriteId", "SPRITE_?"))
    kind, texts = script_dialogue(mn, obj.get("scriptId", 0)) if mn else ("none", [])
    typ = int(obj.get("type", 0) or 0)
    is_trainer = typ == 1 or kind == "trainer"
    role = ("a Trainer (battles you)" if is_trainer
            else "someone you can talk to" if (kind == "script" and texts)
            else "a decorative / background character" if kind == "none"
            else "an interactive character")
    d = Desc("●", f"{sprite} — {role}")
    move = movement_phrase(obj.get("movement", 0))
    face = facing_phrase(obj.get("facingDirection"))
    d.lines.append(f"At tile ({obj.get('x')}, {obj.get('z')}); {move}; {face}.")
    d.lines += _dialogue_lines("trainer" if is_trainer else kind, texts)
    flag = str(obj.get("eventFlag", "FLAG_NOTHING"))
    if flag and flag != "FLAG_NOTHING":
        d.lines.append(f"Visible? {flag_story(flag)}.")
    else:
        d.lines.append("Visible? Always on this map.")
    return d


def describe_warp(zone, w: dict) -> Desc:
    dest = humanize_map(w.get("header", "MAP_?"))
    d = Desc("→", f"Doorway / exit → {dest}")
    d.lines.append(f"At tile ({w.get('x')}, {w.get('z')}). Step here to travel to {dest}.")
    d.lines.append(f"Arrives at {dest}'s entry point #{w.get('anchor', 0)}.")
    return d


def describe_coord(zone, c: dict) -> Desc:
    mn = map_name_of(zone)
    kind, texts = script_dialogue(mn, c.get("scriptId", 0)) if mn else ("none", [])
    w = int(c.get("w", 1) or 1); h = int(c.get("h", 1) or 1)
    area = "1 tile" if (w, h) == (1, 1) else f"{w}×{h} tiles"
    d = Desc("◆", "Invisible step trigger")
    d.lines.append(f"Covers {area} starting at ({c.get('x')}, {c.get('z')}). "
                   "Fires when the player walks onto it.")
    d.lines += _dialogue_lines(kind, texts, speaker="Shows")
    var = str(c.get("var", "")); val = c.get("val", 0)
    if var and not (var.startswith("VAR_TEMP") and int(val or 0) == 0):
        d.lines.append(f"Only active when {humanize_var(var)} = {val}.")
    else:
        d.lines.append("Active whenever the player is on this map.")
    return d


def describe_bg(zone, b: dict) -> Desc:
    mn = map_name_of(zone)
    typ = int(b.get("type", 0) or 0)
    kind, texts = script_dialogue(mn, b.get("scriptId", 0)) if mn else ("none", [])
    if typ == 2:
        d = Desc("★", "Hidden item")
        d.lines.append(f"At tile ({b.get('x')}, {b.get('z')}). Found with an item check.")
        return d
    d = Desc("■", "Sign / readable spot")
    d.lines.append(f"At tile ({b.get('x')}, {b.get('z')}). Face it and press A to read.")
    d.lines += _dialogue_lines(kind, texts, speaker="Reads")
    return d


DESCRIBERS = {
    "objects": describe_object,
    "warps": describe_warp,
    "coords": describe_coord,
    "bgs": describe_bg,
}


def describe(zone, kind: str, ref: dict) -> Desc:
    try:
        return DESCRIBERS[kind](zone, ref)
    except Exception as e:                       # never let a bad parse break the UI
        return Desc("•", f"{kind[:-1]}", [f"(could not describe: {e})"])


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from mapdata import ZoneEvents
    from mapresolve import zone_event_path
    mid = int(sys.argv[1]) if len(sys.argv) > 1 else 67
    z = ZoneEvents.load(zone_event_path(mid))
    print(f"map {mid}  ({map_name_of(z)})")
    for kind in ("objects", "warps", "coords", "bgs"):
        for ref in getattr(z, kind):
            de = describe(z, kind, ref)
            print(f"\n{de.icon} {de.title}")
            for ln in de.lines:
                print(f"    {ln}")
