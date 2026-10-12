# Collaboration workflow: Davis + Claude + Codex + Grok

How the four of us ship Pokemon Apocrypha faster without stepping on each
other. `AGENTS.md` is the short rulebook every agent reads first. This is the
longer version: the loop, the lanes, and what each recommended tool does or
does not do for a Gen 4 project.

## The one-paragraph version

The game is text. Map events are JSON, scripts are `.s`, dialogue is `.gmm`
XML, flags and vars are `#define`s, engine code is C. All of it lives in the
`apocrypha-ch1` branch of `Davisfox5/pokeheartgold`, mounted into this repo as
`disasm/pokeheartgold`. Any agent can clone that, edit it, run `make check`,
and open a PR. Davis is the only one who can turn text into a playable ROM
and the only one who can watch it run, so Davis's time goes to building,
playing from a checkpoint, visual map work, and decisions. Everything else is
fair game for agents in parallel.

## The loop

```
spec row (docs/CHAPTERn_SCENES_SPEC.md)            Davis writes or approves
      |
      v
agent branch  <agent>/<topic>                      Claude, Codex, or Grok
   edit zone_event JSON / scr_seq .s / .gmm / flags.h
   make check  (0 errors)
   draft PR against apocrypha-ch1 with the template filled in
      |
      v
Davis: merge -> _omni_native_build.sh (~30 s)      Mac only
       tools/cockpit.py from a checkpoint
       RAM readout: scene var, map id, player tile
      |
      v
status flip in the spec  (🔧 -> ✅ or ❌ + a line)  Davis or the rig
hub PR bumps the disasm/pokeheartgold submodule pointer
```

What makes it fast: agents never wait on a build to know whether a PR is
structurally valid, and Davis never reads a PR that fails `make check`.

## Lanes (who takes what)

| Lane | Owner | Tools |
|---|---|---|
| Design, lore, chapter specs | Davis | `DESIGN.md` (owner only), spec docs |
| Visual map layout, collision feel, 3D models, textures | Davis | Pokemon DS Map Studio, DSPRE, `tools/mapeditor/editor_app.py` (live, RAM-backed) |
| Scene scripts, triggers, NPC placement, warps | Agents | `zone_event/*.json`, `scr_seq_*.s`, `event_*.h` |
| Dialogue | Agents (Claude with `/df-writing`) | `msg_*.gmm` |
| Flags, vars, scene-var state machines | Agents (Claude with `/apoc-budget-check`) | `flags.h`, `vars.h` |
| Engine changes, new script commands | Agents, with a reason in the PR | `src/`, `asm/macros/script.inc` |
| Region ports (Hoenn, Sinnoh, Unova) | Agents | `tools/hoennconv/`, `tools/regionport/`, Porymap on `disasm/pokeemerald` for source-side fixes |
| Sprites and art insertion | Davis authors, agents insert | `scripts/insert_trainer.py`, `scripts/insert_ow.py`, `make build && make validate` |
| Build, play, verify, log | Davis + rig | `_omni_native_build.sh`, `tools/cockpit.py`, `tools/rig.py`, `docs/CH1_PLAYTHROUGH_LOG.md` |
| Merging | Davis | GitHub |

Parallelism rule: one map per open PR per agent. Two agents on the same
`scr_seq_NNNN_MAP.s` or `msg_NNNN_MAP.gmm` will conflict on message indexes
and object ids. If two scenes share a map, the second agent branches from the
first agent's branch and says so.

## Setup per participant

**Davis (Mac)**: already set up. The only new habit is `make check` before a
build, and `git submodule update --remote disasm/pokeheartgold` after merging
a game PR so the hub tracks it.

**Any agent with a shell (Claude Code, Codex, Grok Build)**:

```sh
git clone https://github.com/Davisfox5/pokemon-apocrypha
cd pokemon-apocrypha
git submodule update --init disasm/pokeheartgold     # the game, ~500 MB
make check                                            # should print 0 error(s)
```

Nothing else is required. No compiler, no SDK, no ROM, no Java, no wine.

**Agents without a shell (chat-only ChatGPT or Grok)**: paste them the
relevant spec section plus the current `scr_seq_NNNN_MAP.s`, `event_MAP.h`
and `.gmm` rows, and ask for a diff. Davis or a shell agent applies it on a
branch and runs `make check`. Give them `AGENTS.md` once per conversation.

## Hand-off between agents

A PR is the hand-off. The template asks for the four things the next agent
needs: maps touched, flags and vars claimed (with addresses), what is
unverified, and how to verify it (which var should reach which value, where
the player should end up). Claude can also run `/handoff` to write a longer
note; put it under `docs/handoffs/` if it needs to outlive the PR.

## Verification without guessing

The rig is the ground truth, not screenshots. `tools/emu_ram.py` reads scene
vars, map id and player tile straight from DeSmuME RAM. When Davis reports a
result, it should be in that shape ("`VAR_SCENE_CHERRYGROVE_CITY_OW` reached 2,
player at (553,402) on map 67"), and the agent's PR should have predicted
exactly that. Recorded paths (`tools/cockpit.py --record`) make a scene
replayable; commit them under `paths/` next to the scene they drive.

## Tool matrix: the Grok list against a Gen 4 project

| Recommended | Verdict | What we use instead or alongside |
|---|---|---|
| `pokeemerald-expansion` as the base | No. The game has been HGSS since day one, Chapter 1 is built and rig-verified, and Hoenn is being ported *into* HGSS. Switching engines restarts the project. | `pokeheartgold` decomp (`Davisfox5/pokeheartgold@apocrypha-ch1`). Same idea: full C source, text data files, `make`. |
| Porymap | Partly. Cannot open HGSS data. Can open `disasm/pokeemerald`, which is the source `tools/hoennconv` reads, so it is the right tool for fixing a Hoenn source map before conversion. | `tools/mapeditor/editor_app.py` for live HGSS event placement; PDSMS and DSPRE for geometry and NARC edits. |
| Poryscript | No. Compiles to Gen 3 script bytecode. | HGSS `scr_seq` macros in `asm/macros/script.inc`. Plain text, readable, every agent can write it. `tools/scrtool.py` disassembles vanilla scripts for reference. |
| Porytiles | No. Gen 3 metatiles. | `scripts/quantize.py`, `scripts/texture_prep.py`, `make build`, `make validate`; PDSMS for `.nsbtx`. |
| gbagfx + Tilemap Studio | No for the game. `nitrogfx` (in the decomp's `tools/`) is the Gen 4 counterpart. | `scripts/nitro.py` codec, `scripts/insert_trainer.py`, `scripts/insert_ow.py`. |
| porygon (MCP toolkit) | No. Built for `pokeemerald` map.bin and map.json. | `make check` plus the file table in `AGENTS.md` gives agents the same byte-safe, text-first entry points. |
| HexManiacAdvance, Advance Map | No. Gen 3 binary tools. | DSPRE Reloaded and SDSME are the Gen 4 binary editors, Davis-only, launched via `tools/launch_dspre.sh`. |
| DSPRE Reloaded + PDSMS (the Gen 4 row) | Yes, already in use. | Davis-only, GUI. Agents prepare the text side and hand off. |
| Git as the shared source of truth | Yes. | Two repos, PR-driven, CI runs `make check`. |
| Design docs for agent context | Yes, already the strongest part of this repo. | `DESIGN.md`, `ENGINEERING.md`, chapter specs, `AGENTS.md`. |

The one thing Grok's stack has that this one does not: a CI that produces a
playable build. The decomp's own `.github/workflows/build.yml` fetches the
compiler and SDK from pret's `workflows/assets` branch, so a GitHub Actions
build of the fork is possible. The open question is where the resulting ROM
may be stored. That is Davis's call and is tracked in the next-steps list in
the PR that added this file.
