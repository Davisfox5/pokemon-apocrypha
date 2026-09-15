# Read only what the task needs

Startup: root AGENTS.md plus this index. Choose one route below; do not preload
all linked documents. Foundation choices are settled. Historical DS evidence is
optional, never part of routine startup.

| Task | First read | Expand only when needed |
| --- | --- | --- |
| Remote Claude/Grok setup / fresh clone | GBA_REMOTE_HANDOFF.md | Source presets, public baseline, Linux and macOS build commands |
| Resume current work / handoff | AGENT_HANDOFF.md | only its next-step references |
| Base setup, build, capacity | GBA_BASELINE.md | FOUNDATION_DECISIONS.md, pinned upstream install/config files |
| Maps beyond Hoenn / map feasibility | GBA_MAP_QUALIFICATION.md | `gba/evidence/map-qualification.json`; isolated tooling in `tools/gba/maps/` |
| Cherrygrove first town / playable map preview | CHERRYGROVE_GBA.md | `gba/evidence/cherrygrove/build.json`; `gba/maps/cherrygrove/town.json`; relevant Chapter 1 canon |
| Johto aesthetic / house, Center and tree tile samples | ../gba/art/johto-v3/README.md | Latest: single-crown trees, scenery transparency, HGSS geography; v2 preserves accepted buildings, v1 references and originals; runtime evidence and source patches |
| Johto NPC importer / walking town residents | ../gba/art/johto-npc-v1/README.md | Five HGSS sprite imports; three walking residents; dialogue, shop, palette and save verification; NPC patch applies after art v3 |
| Claude's independent Cherrygrove exterior / playable preview | ../gba/art/claude-cherrygrove/README.md | Original Gen 3 style Johto art, workbench-preset build, `gba/claude-cherrygrove.patch`, runtime and movement evidence |
| Fresh custom Cherrygrove / current visual preview | ../gba/art/johto-restart/README.md | Clean Emerald town baseline; approved custom houses/Center, new scenery and layout; twelve walkers; verified ROM/save and standalone source patch |
| Rejected HGSS Cherrygrove reconstruction / historical only | ../gba/art/johto-v4/README.md | Owner rejected repurposed art direction; preserve evidence, do not resume or build on this version |
| Five-region character scale / previous visual preview | ../gba/art/regional-scale-v1/README.md | Smaller custom cast; walking Hoenn, Kanto, Johto, Sinnoh and Unova samples; original vs reduced pixels; verified ROM/save and incremental patch |
| Custom Gold, Silver and Kestra / cleanup preview | ../gba/art/johto-cast-v1/README.md | Native cleanup, all three placed with residents; actual sprite-pixel direction checks; latest playable package and additive source patch |
| Battle rules, experience, evolution, conveniences | GBA_MECHANICS_AUDIT.md | FOUNDATION_DECISIONS.md; one relevant config/source file; machine inventory only for a specific lookup |
| Scope or mechanic exception | FOUNDATION_DECISIONS.md | relevant DESIGN.md gym or progression section |
| Map, tile, character production | AGENT_WORKFLOW.md | DESIGN.md regional identity and the specific location/character; artwork-library/README.md only for an asset lookup |
| Story or dialogue | target DESIGN.md section | matching CHAPTERn_SCENES_SPEC.md; dialogue is reusable, DS IDs/hooks are not |
| Trainer teams and encounters | current owner direction, then relevant chapter section | Existing BATTLES documents are provisional: owner said teams, placement and level curve are not designed; map feasibility comes first |
| TMs, move tutors, move distribution | MOVE_ECONOMY.md, then TUTOR_ROSTERS.md for the tutor lists | GBA_MECHANICS_AUDIT.md M04 section; `gba/evidence/m04-build.json`; `game/include/constants/tms_hms.h` for the built list |
| Breeding, egg moves, reward move gating | GBA_MECHANICS_AUDIT.md egg/breeding section | RESERVED_MOVE_POOL.md; `gba/evidence/egg-move-audit.json` and `reserved-move-pool.json`; `game/src/daycare.c` only for the special-move table |
| Items, rewards, services | relevant region ITEMS document and chapter section | related narrative gates and state identifiers |
| 30-box storage qualification | GBA_STORAGE_PROTOTYPE.md | GBA_STORAGE_QUALIFICATION.md, GBA_BASELINE.md, specific game/ save and storage files |
| Flags, saves, badges, travel | FOUNDATION_DECISIONS.md and AGENT_WORKFLOW.md | relevant active engine definitions once installed; historical ledger only to investigate a specific old failure |
| Old implementation or an asset decoder | ../archive/gen4/README.md | one indexed historical document or exact source file |
| Explicitly authorized DS fallback | ../archive/gen4/README.md | restoration procedure and source-tree manifest |

Paths in the table are relative to docs/ unless otherwise stated. Relevant region
files currently exist for JOHTO, KANTO, and HOENN. Chapter scene documents cover 1-8.
They retain story/data intent; their old engine assumptions do not define the GBA implementation.

## Bounded lookup examples (from repository root)

```sh
rg -n '^## |^### ' DESIGN.md
rg -n 'Kestra|KESTRA|Silver' DESIGN.md
rg -n '^## |^### ' docs/JOHTO_BATTLES.md
```

Then read the specific section with `sed -n 'START,ENDp' FILE`, using discovered
line numbers. Do not `cat` every markdown file, recursively dump disasm/, or
load contact sheets for unrelated regions. Search a named active directory first;
expand to a donor or archive only when the current task provides a reason.

Default `rg` searches exclude archived snapshots and `disasm/` via `.rgignore`.
This does not remove files from Git. To inspect historical code deliberately:

```sh
rg --no-ignore -n 'NUM_FLAGS' disasm/pokeheartgold/include/constants/flags.h
```

Use an exact file or narrowly scoped directory, not `rg --no-ignore` at root.

## Authority and status

1. Current owner instructions.
2. AGENTS.md for agent behavior; FOUNDATION_DECISIONS.md for approved technical scope.
3. DESIGN.md and relevant scene documents for narrative intent; recent owner corrections prevail.
4. Active task specifications and measured implementation records.
5. Archived documents: historical evidence only, including formerly authoritative language.

Approved means chosen; verified means tested. See GBA_BASELINE.md for which
checks actually exist. Do not turn a design target into a completion claim.
