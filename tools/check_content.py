#!/usr/bin/env python3
"""No-ROM content checks for Pokemon Apocrypha.

Runs against the game source in disasm/pokeheartgold (the Davisfox5/pokeheartgold
fork, branch apocrypha-ch1). Nothing here needs the compiler, the SDK, or a ROM,
so every collaborator (Davis, Claude, Codex, Grok) and CI can run it on any
change before Davis spends a build on it.

Checks:
  1. zone_event JSON parses, and every object/bg/coord scriptId and eventFlag
     names a symbol that exists (event_*.h for scripts, flags.h for flags,
     vars.h for coord vars). Object ids match the defines in the event header.
  2. flags.h / vars.h: no two names share an address, no address past
     NUM_FLAGS / NUM_VARS (the story-state budget), and a report of how many
     FLAG_APOC_* / VAR_APOC_* slots are in use.
  3. Script .s files: every `npc_msg msg_X` names a row that exists in the
     matching .gmm, every setflag/clearflag/checkflag names a defined flag,
     every setvar/compare/addvar names a defined var.
  4. .gmm message text: no straight apostrophe, straight double quote, or em
     dash (the HG charset rules in docs/CHAPTER1_BUILD.md).
  5. Nothing that must never be committed is present: *.nds, *.sav, SDK or
     compiler archives.

Usage:
    python3 tools/check_content.py            # whole tree
    python3 tools/check_content.py T21 R29    # only maps whose names contain these
Exit status is nonzero on any error. Warnings never fail the run.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECOMP = ROOT / "disasm" / "pokeheartgold"
ZONE_DIR = DECOMP / "files" / "fielddata" / "eventdata" / "zone_event"
SCR_DIR = DECOMP / "files" / "fielddata" / "script" / "scr_seq"
MSG_DIR = DECOMP / "files" / "msgdata" / "msg"
FLAGS_H = DECOMP / "include" / "constants" / "flags.h"
VARS_H = DECOMP / "include" / "constants" / "vars.h"
MAPS_H = DECOMP / "include" / "constants" / "maps.h"

DEFINE = re.compile(r"^#define\s+([A-Za-z_][A-Za-z0-9_]+)\s+(\(?)(0x[0-9A-Fa-f]+|\d+)\)?", re.M)
BAD_TEXT = {"'": "straight apostrophe (use U+2019)", '"': "straight double quote",
            "—": "em dash", "–": "en dash"}
FORBIDDEN_FILES = re.compile(r"\.(nds|srl|gba|sav|srm)$|NitroSDK[^/]*\.(7z|zip|rar)$|mwccarm/|license\.dat$", re.I)

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def defines(path: Path) -> dict[str, int]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return {m.group(1): int(m.group(3), 0) for m in DEFINE.finditer(text)}


# --------------------------------------------------------------------------- #
# 2. flag / var budget
# --------------------------------------------------------------------------- #
def check_budget() -> tuple[dict[str, int], dict[str, int]]:
    flags = defines(FLAGS_H)
    vars_ = defines(VARS_H)
    num_flags = flags.get("NUM_FLAGS", 2912)
    num_vars = vars_.get("NUM_VARS", 0x170)
    var_base = vars_.get("VAR_BASE", 0x4000)

    def dupes(table: dict[str, int], label: str, skip: set[str]) -> None:
        by_val: dict[int, list[str]] = defaultdict(list)
        for name, val in table.items():
            if name in skip or name.startswith(("NUM_", "TEMP_", "DAILY_", "MAP_TEMP_")):
                continue
            by_val[val].append(name)
        for val, names in sorted(by_val.items()):
            apoc = [n for n in names if "APOC" in n]
            if len(names) > 1 and apoc:
                err(f"{label}: {', '.join(names)} share address {val:#x} (one is Apocrypha's)")

    dupes(flags, "flags.h", {"FLAG_NOTHING", "FLAGS_END", "FLAG_BASE"})
    dupes(vars_, "vars.h", {"VARS_END", "VAR_BASE"})

    for name, val in flags.items():
        if name.startswith("FLAG_") and val >= num_flags and not name.endswith("_END") \
                and not name.startswith(("FLAG_TEMP_", "FLAG_DAILY_", "FLAG_MAP_TEMP_")):
            err(f"flags.h: {name} = {val:#x} is past NUM_FLAGS ({num_flags})")
    for name, val in vars_.items():
        if name.startswith("VAR_") and val >= var_base and val - var_base >= num_vars \
                and not name.startswith("VAR_SPECIAL") and not name.endswith("_END"):
            err(f"vars.h: {name} = {val:#x} is past NUM_VARS ({num_vars})")

    apoc_flags = sorted(n for n in flags if "APOC" in n)
    apoc_vars = sorted(n for n in vars_ if "APOC" in n)
    print(f"budget: {len(apoc_flags)} FLAG_APOC_* defined, {len(apoc_vars)} VAR_APOC_* defined "
          f"(limits NUM_FLAGS={num_flags}, NUM_VARS={num_vars}; run /apoc-budget-check for the full audit)")
    return flags, vars_


# --------------------------------------------------------------------------- #
# 1. zone_event JSON
# --------------------------------------------------------------------------- #
def event_header_symbols(header_rel: str) -> dict[str, int] | None:
    path = DECOMP / "files" / header_rel
    if not path.exists():
        return None
    return defines(path)


def script_id_ok(expr: str, syms: dict[str, int]) -> bool:
    """scriptId is an expression like `_EV_scr_seq_T21_012 + 1`, a bare std_*
    symbol, or an integer."""
    expr = expr.strip()
    if re.fullmatch(r"\d+", expr) or expr.startswith("std_"):
        return True
    m = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)\s*(\+\s*\d+)?", expr)
    if not m:
        return False
    name = m.group(1)
    return name in syms or name.startswith("std_") or name.startswith("scr_")


def check_zone_events(flags: dict[str, int], vars_: dict[str, int], only: list[str]) -> None:
    files = sorted(ZONE_DIR.glob("*.json"))
    if only:
        files = [f for f in files if any(o in f.name for o in only)]
    print(f"zone_event: checking {len(files)} files")
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            err(f"{f.name}: invalid JSON: {e}")
            continue
        syms = event_header_symbols(data.get("header", "")) or {}
        if not syms:
            warn(f"{f.name}: event header {data.get('header')!r} not found; scriptIds unchecked")
        ids_in_json = [o.get("id") for o in data.get("objects", [])]
        for kind in ("objects", "bgs", "coords"):
            for i, ev in enumerate(data.get(kind, [])):
                sid = str(ev.get("scriptId", "0"))
                if syms and not script_id_ok(sid, syms):
                    err(f"{f.name}: {kind}[{i}] scriptId {sid!r} not defined in {data['header']}")
                fl = ev.get("eventFlag")
                if fl is not None and not isinstance(fl, int) and fl not in flags:
                    err(f"{f.name}: {kind}[{i}] eventFlag {fl!r} not in flags.h")
                var = ev.get("var")
                if var is not None and not isinstance(var, int) and var not in vars_:
                    err(f"{f.name}: {kind}[{i}] var {var!r} not in vars.h")
        for i, oid in enumerate(ids_in_json):
            if isinstance(oid, int):
                continue
            if syms and oid not in syms:
                err(f"{f.name}: objects[{i}] id {oid!r} has no define in {data['header']}")
        seen = set()
        for oid in ids_in_json:
            if oid in seen:
                err(f"{f.name}: duplicate object id {oid!r}")
            seen.add(oid)


# --------------------------------------------------------------------------- #
# 3 + 4. scripts and messages
# --------------------------------------------------------------------------- #
GMM_ROW = re.compile(r'<row id="([^"]+)"')
GMM_TEXT = re.compile(r'<language name="English">(.*?)</language>', re.S)
SCR_CMD = re.compile(r"^\s*(npc_msg|setflag|clearflag|checkflag|setvar|compare|addvar|subvar|copyvar)\s+([^\s,;]+)", re.M)
SCR_LABEL_USE = re.compile(r"^\s*(?:goto|call|goto_if_eq|goto_if_ne|goto_if_lt|goto_if_gt|goto_if_le|goto_if_ge|goto_if_set|goto_if_unset|apply_movement\s+[^,]+,)\s*(\w+)", re.M)
SCR_LABEL_DEF = re.compile(r"^(\w+):", re.M)


def gmm_rows(path: Path) -> tuple[set[str], list[tuple[str, str]]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    ids = set(GMM_ROW.findall(text))
    texts = []
    for row in re.finditer(r'<row id="([^"]+)".*?</row>', text, re.S):
        m = GMM_TEXT.search(row.group(0))
        if m:
            texts.append((row.group(1), m.group(1)))
    return ids, texts


def check_scripts(flags: dict[str, int], vars_: dict[str, int], only: list[str]) -> None:
    msg_ids: set[str] = set()
    gmms = sorted(MSG_DIR.glob("*.gmm"))
    for g in gmms:
        ids, texts = gmm_rows(g)
        msg_ids |= ids
        if only and not any(o in g.name for o in only):
            continue
        for rid, txt in texts:
            for ch, why in BAD_TEXT.items():
                if ch in txt:
                    err(f"{g.name}: {rid} contains {why}")
    scripts = sorted(p for p in SCR_DIR.glob("scr_seq_*.s") if not p.name.endswith("_hdr.s"))
    if only:
        scripts = [s for s in scripts if any(o in s.name for o in only)]
    print(f"scripts: checking {len(scripts)} .s files against {len(gmms)} .gmm files")
    for s in scripts:
        text = s.read_text(encoding="utf-8", errors="replace")
        labels = set(SCR_LABEL_DEF.findall(text))
        for m in SCR_CMD.finditer(text):
            cmd, arg = m.group(1), m.group(2)
            if cmd == "npc_msg":
                if arg.startswith("msg_") and arg not in msg_ids:
                    err(f"{s.name}: npc_msg {arg} has no row in any .gmm")
            elif cmd in ("setflag", "clearflag", "checkflag"):
                if arg.startswith("FLAG_") and arg not in flags:
                    err(f"{s.name}: {cmd} {arg} not in flags.h")
            else:
                if arg.startswith("VAR_") and arg not in vars_:
                    err(f"{s.name}: {cmd} {arg} not in vars.h")
        for m in SCR_LABEL_USE.finditer(text):
            lbl = m.group(1)
            if lbl.startswith(("_", "scr_", "std_")) and lbl not in labels and not lbl.isdigit():
                # labels can live in sibling files or common.s; only flag Apocrypha-prefixed ones
                if lbl.startswith("_apoc"):
                    err(f"{s.name}: jumps to {lbl} but it is not defined in this file")


# --------------------------------------------------------------------------- #
# 5. forbidden files
# --------------------------------------------------------------------------- #
def check_forbidden() -> None:
    import subprocess
    for repo in (ROOT, DECOMP):
        try:
            out = subprocess.run(["git", "-C", str(repo), "ls-files"], capture_output=True, text=True, check=True).stdout
        except Exception:
            continue
        for line in out.splitlines():
            if FORBIDDEN_FILES.search(line):
                err(f"{repo.name}: tracked file must not be in the repo: {line}")


def main(argv: list[str]) -> int:
    only = [a for a in argv if not a.startswith("-")]
    if not DECOMP.exists() or not ZONE_DIR.exists():
        print("disasm/pokeheartgold is not checked out. Run:\n"
              "  git submodule update --init disasm/pokeheartgold")
        return 2
    flags, vars_ = check_budget()
    check_zone_events(flags, vars_, only)
    check_scripts(flags, vars_, only)
    check_forbidden()
    for w in warnings:
        print(f"warn: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
