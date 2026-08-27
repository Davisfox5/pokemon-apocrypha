---
name: apoc-budget-check
description: Audit Pokemon Apocrypha's story-state budget. Counts flag and var usage across scene specs and scripts against the HGSS engine limits (NUM_FLAGS 2912, NUM_VARS 368, national dex cap 493) and reports what is left. Use before adding a scene that needs new state, when a chapter spec adds flags or vars, when adding species, or when the user says "budget check".
allowed-tools: Read Grep Glob Bash(grep *) Bash(rg *)
---

# Apocrypha budget check

The Gen-4 engine ships fixed budgets. Apocrypha is a five-region, 20-badge,
five-thread game on an engine sized for Johto plus Kanto, so these are the
constraints most likely to end a plan, and they are cheap to check before
committing to a scene.

## The limits (from ENGINEERING.md, verified against source)

| Budget | Limit | Storage | Notes |
|---|---|---|---|
| Persistent flags | `NUM_FLAGS = 2912` | `u8 flags[364]` | Plus 64 temp, 64 map-temp, 192 daily. Vanilla HGSS already spends a large share. |
| Script vars | `NUM_VARS = 0x170 = 368` | `u16 vars[368]`, 736 bytes | Plus 32 temp vars and 14 special vars. |
| National dex | `493` (`SPECIES_ARCEUS`) | `caughtLanguages[ROUND_UP(493,4)]`, `NUM_DEX_FLAG_WORDS = CEILDIV(493+8,32)` | Save arrays are sized off this. Slots 494 to 507 hold `SPECIES_EGG`, `SPECIES_BAD_EGG`, and Rotom forms. |

Raising any of these means resizing the save block. That is designed work, not a
constant edit: see `engineering/m1-state-save-architecture.md` and
`engineering/m1-dex-expansion.md`.

## Procedure

1. Collect every flag and var identifier currently referenced. The naming
   conventions in this repo:

   ```bash
   grep -rhoE '\bFLAG_[A-Z0-9_]+' docs/ engineering/ tools/ --include='*.md' --include='*.py' | sort -u
   grep -rhoE '\bVAR_[A-Z0-9_]+' docs/ engineering/ tools/ --include='*.md' --include='*.py' | sort -u
   ```

   Scene specs also cite raw hex addresses (`VAR_SCENE_PLAYERS_HOUSE_1F = 0x4106`,
   `VAR_SCENE_CHERRYGROVE_CITY_OW = 0x4073`). Collect those too:

   ```bash
   grep -rhoE '0x4[0-9A-Fa-f]{3}' docs/*.md | sort -u
   ```

2. Separate Apocrypha's own state from vanilla's. Anything matching
   `FLAG_APOC_*` or `VAR_APOC_*` is new. Everything else is either vanilla HGSS
   state being reused or a scene var the base game already owns. Reusing a
   vanilla flag costs nothing; defining a new one costs a slot.

3. Count distinct new identifiers. Report:

   - New flags defined, and how many of `NUM_FLAGS` remain
   - New vars defined, and how many of `NUM_VARS` remain
   - Identifiers marked "reserved" in a spec but not yet used. These are
     committed budget: `FLAG_APOC_R29_INTRO_DONE` and
     `FLAG_APOC_MOM_GOODBYE_DONE` in `docs/CHAPTER1_SCENES_SPEC.md` are the
     pattern. Count them as spent.
   - Species count against 493 if any species were added

4. Flag anything worth a decision:

   - A scene defining more than two new persistent flags. Most beats can key off
     an existing scene var stage instead of a dedicated flag, and stages are
     free where flags are not.
   - A new var used only as a boolean. That is a flag, and it costs 16 bits
     instead of 1.
   - A flag that is set and never checked, or checked and never set. Usually a
     spec that drifted from the build.
   - Any reference at or past species 494. That is the sentinel range.

## Output

Report in this shape, and nothing else:

```
FLAGS   new: N of 2912   remaining: M   reserved-unused: K
VARS    new: N of 368    remaining: M   reserved-unused: K
DEX     highest species referenced: N of 493

Notes
- <one line per finding worth a decision>
```

If a budget is above 80 percent spent, say so on its own line and name the
migration doc that covers expanding it. Do not propose expanding it inline.

## What this skill does not do

- It does not check world consistency. That is `apoc-lore-check`.
- It does not edit specs or scripts. It reports.
- It does not count temp, map-temp, or daily flags, which are scoped and cheap.
  If a scene needs persistent state, say so explicitly; if temp state will do,
  that is the cheaper answer and worth saying.
