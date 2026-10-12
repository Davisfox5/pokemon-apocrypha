# AGENTS.md

Instructions for every AI agent working on Pokemon Apocrypha: Claude Code,
Codex (ChatGPT), Grok Build, and anything else that reads this file. Davis is
the owner and the only person who can build and play the ROM. Read this whole
file before touching anything. `CLAUDE.md` adds Claude-specific skills on top
of it.

## What this project is

A Gen 4 (Nintendo DS) ROM hack of Pokemon HeartGold, built from the
`pokeheartgold` C decompilation. Five regions, 20 badges. It is **not** a Gen 3
/ `pokeemerald` project. Porymap, Poryscript, Porytiles and porygon operate on
`pokeemerald` trees and cannot open, edit, or build this game. The Gen 4
equivalents are listed below. See `docs/WORKFLOW.md` for the full tool matrix.

## The repositories

| Repo | Role | Where |
|---|---|---|
| `Davisfox5/pokemon-apocrypha` | The hub: design bible, chapter specs, asset pipeline, emulator rig, map editor, converters. Open PRs here for anything that is not game source. | this repo |
| `Davisfox5/pokeheartgold`, branch `apocrypha-ch1` | **The game.** Scripts, map events, text, flags, engine C. Mounted here as the submodule `disasm/pokeheartgold`. Open PRs against `apocrypha-ch1`. | `disasm/pokeheartgold/` |
| `pret/pokeemerald` (submodule `disasm/pokeemerald`) | Read-only Hoenn source data. `tools/hoennconv/` converts its maps into HGSS format. Porymap can open this tree. | `disasm/pokeemerald/` |
| `pret/pokeplatinum`, `pret/pokefirered` (submodules) | Reference only (Sinnoh port, Kanto assets). | `disasm/` |
| `Davisfox5/pokeemerald-expansion` | Not used by any pipeline. Ignore it unless Davis says otherwise. | |

Get the game source:

```sh
git submodule update --init disasm/pokeheartgold
```

The other three submodules are large and only needed for region-port work.

## Authority, in order

1. `DESIGN.md` is the world bible. **Never edit it.** If a task contradicts it,
   stop and say so. Changing the bible is Davis's call, in its own conversation.
2. `ENGINEERING.md` is the engine reality: verified limits, save layout, port
   status. Add verified findings there; do not relitigate design there.
3. `docs/CHAPTER*_SCENES_SPEC.md` is the per-scene desired end state, with a
   status marker per scene. It is downstream of the bible and can be wrong.
4. `docs/CHAPTER*_BUILD.md` is the implementation design for a chapter.
5. `docs/CH1_PLAYTHROUGH_LOG.md` records what the rig actually observed. Only a
   rig run or Davis updates it. Agents without a ROM do not mark anything
   verified.

## Where the game content lives (the Gen 4 answer to "map.json + scripts")

All paths are inside `disasm/pokeheartgold/`. `MAP` is the map's short code,
for example `T21` (Cherrygrove City), `R29` (Route 29), `T20R0101` (Elm's Lab).

| You want to change | Edit | Notes |
|---|---|---|
| NPCs, signs, warps, coord triggers on a map | `files/fielddata/eventdata/zone_event/NNN_MAP.json` | Keys: `objects`, `bgs`, `warps`, `coords`. Positions are global world tiles `(x, z)`, z grows south. `jsonproc` compiles it at build time. |
| Object ids and script numbers for a map | `files/fielddata/script/scr_seq/event_MAP.h` | Every `objects[].id` in the JSON needs a `#define` here. Append new ids; do not renumber existing ones. |
| Event scripts (what happens when you talk, step, enter) | `files/fielddata/script/scr_seq/scr_seq_NNNN_MAP.s` | Assembly-style script language. Commands are macros in `asm/macros/script.inc`; Apocrypha-added commands are prefixed `apoc_`. `tools/scrtool.py` in the fork disassembles compiled scripts. |
| Map-load scripts and scene-var triggers | `files/fielddata/script/scr_seq/scr_seq_NNNN_MAP_hdr.s` | The `.short VAR, value, script` table runs a script on map load while `VAR == value`. |
| Dialogue and any on-screen text | `files/msgdata/msg/msg_NNNN_MAP.gmm` | XML rows `msg_NNNN_MAP_000XX`. Add rows at the end, keep `index` sequential. |
| Story flags | `include/constants/flags.h` | New ones are `FLAG_APOC_*`. Budget: `NUM_FLAGS 2912`. |
| Script vars | `include/constants/vars.h` | New ones are `VAR_APOC_*`. Budget: `NUM_VARS 368`. Scene vars gate everything. |
| Which script bank, text bank, matrix a map uses | `src/data/map_headers.h`, `include/constants/maps.h` | |
| Map layout (which 32x32 chunk models tile a zone) | `files/fielddata/mapmatrix/*.bin` | Binary. `tools/mapeditor/mapdata.py` in the hub parses and writes it. |
| 3D map geometry and textures | NARC binaries under `files/fielddata/` | Not text. Davis edits these in Pokemon DS Map Studio / DSPRE, or `tools/regionport/` generates them. |
| Wild encounters | `files/fielddata/encountdata/gs_enc_data.json` | |
| Trainer battle sprites, overworld sprites | `scripts/insert_trainer.py`, `scripts/insert_ow.py` in the hub | Scripted, round-trip verified. |
| Engine behaviour, new script commands | `src/*.c`, `include/*.h`, `asm/macros/script.inc` | C, MWCC/ARM9. Keep diffs minimal and explain them in the PR. |

## Engine rules that bite (learned the hard way, from `docs/CHAPTER1_SCENES_SPEC.md`)

- A coord or map-load script re-fires **every frame** while its gating var
  matches. Bump the var before the script ends.
- `hide_person` deletes the object **and sets** its `eventFlag`. To reveal it
  again: `clearflag` first, then `show_person`.
- To place a hidden actor: `move_person` before `show_person`. To move a live
  one: `move_person_facing`. Do not `move_person_facing` an object the same tick
  you showed it.
- Never `move_person_facing obj_player`. It lands on an unloaded chunk (black
  "Mystery Zone"). Move the player with `apply_movement`, camera focus
  (`scrcmd_102` / `scrcmd_103`), or a same-map `warp`.
- Every movement table label needs `.balign 4, 0` above it, or `wait_movement`
  hangs.
- A field `fade_screen` darkens the message box too. No readable text on a
  black screen from a field script.
- Scripts that `warp` and then `end` without `releaseall` leave a permanent
  black screen.

## Text rules

HG charset only. Curly apostrophe `’` (U+2019), never `'`. No `"`, no em or en
dashes. `\n` second line of the box, `\r` wait for button and clear, `\f`
scroll. Keep each box to two lines. Dialogue voice: Gen 4 in-game register,
one thought per box, no modern idiom. Claude runs `/df-writing` for this; other
agents follow `docs/CHAPTER1_BUILD.md` section 2 as the register sample.

## Story-state budget

Flags and vars are a fixed, nearly spent budget. Before a scene that needs a
new flag or var: reuse a vanilla one that is dead in Apocrypha if you can,
otherwise claim a free slot and leave a comment on the define saying which
scene owns it. Never give two names the same address. Claude runs
`/apoc-budget-check`; everyone runs `make check` (below), which fails on
collisions and out-of-range addresses.

## How to work

1. **Branch** off `main` (hub) or `apocrypha-ch1` (game) as `<agent>/<topic>`:
   `claude/...`, `codex/...`, `grok/...`. These prefixes are already in use.
2. **Edit text, not binaries.** JSON, `.s`, `.gmm`, `.h`, `.c`, `.md`, `.py`.
   If a change needs a NARC or model rebuilt, say so in the PR and stop there;
   Davis does the binary step.
3. **Run the checks** from the hub root before every PR:

   ```sh
   make check            # tools/check_content.py: JSON, script, text, flag/var, forbidden-file checks
   python3 tools/check_content.py T21 R29   # only the maps you touched
   ```

   Zero errors or the PR is not ready. CI runs the same script.
4. **Open a draft PR** and fill in the template (maps touched, flags/vars
   claimed, what is unverified). A game change and a hub change are two PRs;
   link them. After the game PR merges, a hub PR bumps the submodule pointer.
5. **Mark status honestly.** In the chapter spec use `🔧 implemented, unverified`
   until the rig or Davis has seen it run. Only a rig run turns it `✅`.
6. **Never commit** `*.nds`, `*.sav`, `*.dsv`, SDK or compiler archives,
   `license.dat`, or build output. A pre-commit hook and `make check` both
   refuse them.

## What agents cannot do here

- **Build the ROM.** Needs the MWCC compiler and Nitro SDK under wine on
  Davis's Mac (`disasm/pokeheartgold/_omni_native_build.sh`). About 30 s for
  a small script edit once set up.
- **Play it.** The py-desmume rig (`tools/cockpit.py`, `tools/rig.py`,
  `tools/path_replay.py`) needs the built ROM and a savestate. Davis runs it
  and pastes the result, or commits a recorded path.

So an agent's deliverable is a PR that passes `make check`, with a clear
"here is how to verify it" note: which scene var should change, which map id
and tile the player should land on. Davis builds, plays from a checkpoint,
and reports back with the rig's RAM readout, not a screenshot guess.

## Division of labour that works

| Who | Owns |
|---|---|
| Davis | Design decisions, visual map work (PDSMS, DSPRE, `tools/mapeditor`), building, playing, the playthrough log, merging. |
| Agents | Scripts, zone events, dialogue, flags/vars, chapter build docs, converters, rig scripts, engine C with a stated reason, documentation. |
| Claude specifically | `/apoc-lore-check` before any scene, `/apoc-budget-check` before new state, `/df-writing` for dialogue. |
