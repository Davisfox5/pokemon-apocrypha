# DexNav on the Pokégear (November 20)

Owner approved DexNav on 2026-11-20 as an app on the one standard Silph handheld the
player gets at the start (the Pokégear in Johto). Wild Pokémon don't walk the overworld,
so hidden Pokémon show as rustling grass. Game source is on the fork
(`Davisfox5/pokeemerald-expansion`, branch `apocrypha`); this folder holds evidence.

## What changed in the game source

- **Pokégear moved onto `apocrypha`.** It only existed as `gba/pokegear-services.patch`
  (isolated build). The gear files (`src/apoc_pokegear*.c`, headers,
  `graphics/apoc_pokegear/`) are now in the production branch with a POKéGEAR start-menu
  entry, the field-step hook and its save record in SaveBlock3 (936 bytes, limit 1624).
  The opening-house maps and scenes in the old patch chain were not ported.
- **New game grants the gear** (`FLAG_APOC_POKEGEAR` in `NewGameInitData`). A later
  opening scene can move this into a scripted handoff.
- **DexNav app**, sixth tab between Phone and Style. Shows the registered species and
  search chain; A opens the expansion's DexNav screen; B returns to the gear. R in the
  field still searches the registered species. DexNav has no start-menu entry.
- **Tab bar** rebuilt for six apps with a new magnifier-and-sprout icon
  (`tools/gba/dexnav/rebuild_bar.py`, applied to `shell.bin` and `radio.bin`).
- **Grass rustle** (`src/apoc_grass_rustle.c`). Built at runtime from the metatile under
  the hidden Pokémon: its own tiles and palette, sheared left and right with transparent
  gaps so the still grass shows through. It matches any region's grass with no per-tileset
  art. Replaces Emerald's fixed shaking-grass sprites (`FLDEFF_SHAKING_GRASS`/`_LONG_GRASS`).
- **Upstream bug fixed.** `TryFindHiddenPokemon` bailed when no search was running
  (`== NULL` instead of `!= NULL`), so hidden Pokémon could never appear.
- **Hidden tables** for Route 29 and Route 30 (`hidden_mons` in `wild_encounters.json`),
  using species already on those routes. Hidden detection only runs on maps that have one.
  Other maps need their own table when their encounters are authored.

## Save IDs (stable, do not reuse)

| ID | Use |
| --- | --- |
| `FLAG_UNUSED_0x020` | `FLAG_APOC_POKEGEAR` (also DexNav detector mode) |
| `FLAG_UNUSED_0x021` | `FLAG_APOC_DEXNAV_SEARCHING` |
| `VAR_UNUSED_0x40F8`-`0x40FC` | Pokégear settings, tuning, presets, init marker |
| `VAR_UNUSED_0x40FD` | DexNav registered species |
| `VAR_UNUSED_0x40FE` | DexNav hidden-Pokémon step counter |

DexNav search levels stay off (`USE_DEXNAV_SEARCH_LEVELS`): one byte per species would not
fit SaveBlock3 next to the gear record.

## Evidence

`evidence/run.jsonl` from `tools/gba/dexnav/runtime.py` (headless mGBA, exit 0): new game
has the gear, every tab, DexNav screen opens and B returns to the gear, hidden Pokémon
detected on Route 29, 48 rustle frames. `gear-review.png`, `gear-dexnav-3x.png`,
`hidden-found-3x.png`, `rustle.gif`.

## Open

- The DexNav screen itself is the expansion's stock art; restyling it to the gear look is
  separate work.
- Rustle strength is a first pass for owner review.
