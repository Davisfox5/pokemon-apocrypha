# Hidden Grottoes

B2W2-style Hidden Grottoes, approved by Davis on 2026-11-20 as one of the ways to get Hidden
Ability Pokémon (see the HA decisions in GBA_MECHANICS_AUDIT.md "Hidden Abilities").

Game source lives on `Davisfox5/pokeemerald-expansion` (`apocrypha` branch). The grotto list,
the generator, the checker and the runtime test live here.

## How it plays

- A grotto entrance is a hole on a route. Walking into it leads to a small clearing ringed by trees.
- The clearing holds one thing: a Pokémon (shown as its overworld sprite) or an item ball.
- Talking to the Pokémon starts a wild battle. It always has its Hidden Ability, is never shiny
  (as in B2W2), uses the slot's gender if one is set, and Synchronize and Cute Charm work as for
  other static encounters. The grotto empties as soon as the battle starts, whether the player
  catches it, beats it, runs or loses.
- Picking up the item empties the grotto. With a full bag pocket the item stays.
- Every 256 steps, each empty grotto has a 5% chance to refill (the B2W2 rule). A refill rolls a
  new slot from that grotto's table, weighted by each slot's `weight`.
- A grotto the player has never entered counts as full. Its content is rolled on the first visit.
- The clearing borrows the route's map section (name, region, met location), battle scene and
  music, so a Pokémon caught there is met on that route.
- Walking back down the path leaves through the same hole.

## Engine pieces (fork)

| File | What |
| --- | --- |
| `src/hidden_grotto.c`, `include/hidden_grotto.h` | Mechanic: refill counter, content roll, HA encounter, exit |
| `include/constants/hidden_grotto.h` | Capacity (64), refill chance, state values |
| `include/constants/hidden_grottoes.h`, `src/data/hidden_grottoes.h` | **Generated** grotto list |
| `data/scripts/hidden_grotto.inc` | Content and exit scripts |
| `data/maps/HiddenGrotto`, `data/layouts/HiddenGrotto` | The one shared interior (`MAP_HIDDEN_GROTTO`) |
| `include/global.h` | `SaveBlock3.hiddenGrottoes[64]` and `hiddenGrottoSteps` (65 bytes) |
| `src/field_control_avatar.c` | Step hook (`UpdateHiddenGrottoStepCounter`) |

One interior serves every grotto. Its warp points to `MAP_DYNAMIC`, so entering a grotto records
the entrance as the dynamic warp; the engine identifies the grotto from that warp (entrance map and
tile) and returns the player there on exit. No flags or vars are used besides `FLAG_TEMP_1`.

Save use: one byte per grotto ID plus a step counter, appended to the end of SaveBlock3, so
existing saves load with every grotto unvisited. Grotto IDs index the save bytes, so an ID never
changes or gets reused once a grotto ships. The capacity is fixed at 64 so adding grottoes never
moves save data. The DexNav work adds about 936 bytes to SaveBlock3; together they stay under
the 1624-byte limit.

## Adding a grotto (map threads)

1. The map must be finished. Grottoes go on finished maps, never into an open map PR.
2. On the map, draw the entrance in that region's tiles. The entrance metatile's behavior must
   warp when stepped on (`MB_NON_ANIMATED_DOOR` like a cave mouth, or `MB_ANIMATED_DOOR`).
   The player walks into it from the south and comes back out facing south.
3. Add an entry to `gba/grottoes/grottoes.json`: the next unused `index` (never reuse one),
   `id` (`GROTTO_<PLACE>`), `name`, `map`, entrance `x`/`y`, and its slots:
   - Pokémon: `{"species": "SPECIES_X", "level": [min, max], "gender": "any|male|female", "weight": n}`
   - Item: `{"item": "ITEM_X", "weight": n}`
4. `python3 tools/gba/grottoes/grottoes.py place ENGINE GROTTO_<PLACE>` adds the warp to the map.
5. `python3 tools/gba/grottoes/grottoes.py generate ENGINE` writes the two generated engine files.
6. `python3 tools/gba/grottoes/grottoes.py check ENGINE` must pass. It rejects species without a
   Hidden Ability (resolved by preprocessing the engine's species data, so roster and ability
   config apply), species or items that aren't built, reused indexes, and entrances without the
   warp or a warping metatile. It also fails if the generated files are stale.
7. Build the ROM, then commit the map, warp and generated files to the fork and the JSON to this
   repository, in the map's two PRs.

Keep Ability Patch and Ability Capsule out of grotto item tables unless Davis places them on purpose:
both are meant to be very rare.

## Test

`python3 tools/gba/grottoes/runtime.py ENGINE OUT` (GBA toolchain on PATH, libmgba-dev) runs the
ROM headless twice and writes `results.json` and frames. It enters the test grotto
(`GROTTO_MAP_PROOF_JOHTO`, a `test_only` entrance on the Johto map-proof field), checks the first
visit rolls content, forces every slot in turn (each Pokémon: sprite, battle, species, level
range, ability slot 2 equal to the species' Hidden Ability, not shiny, female when the slot says
so, grotto empty after running; each item: ball, pickup, empty), revisits empty, measures the
refill rate over 4000 simulated 256-step wraps, checks walking advances the counter, saves, and
cold-reloads the save. Evidence: `gba/evidence/hidden-grottoes/`.

`tools/gba/grottoes/interior.py ENGINE` regenerates the interior layout (stock Emerald trees and
flowers from General/Petalburg, no new tiles or palettes).

## Open

- No real grottoes are placed yet; only the test entrance exists. Placement is coordinated with the
  HGSS map port thread, one finished map at a time.
- Grotto contents are per grotto in the JSON. B2W2's own grotto tables are not copied; each
  grotto's species, levels and weights still need choosing.
- The interior uses Emerald's stock trees. A per-region interior (matching each region's kit) is
  a later art pass if wanted.
- B2W2 also had hidden items in grottoes and gender-only slots tied to version. Neither is built.
