# Hidden Grottoes

B2W2-style Hidden Grottoes, approved by Davis on 2026-11-20 as one of the ways to get Hidden
Ability Pokémon (see the HA decisions in GBA_MECHANICS_AUDIT.md "Hidden Abilities").

Game source lives on `Davisfox5/pokeemerald-expansion` (`apocrypha` branch). The grotto list,
the generator, the checker and the runtime test live here.

## How it plays

- A grotto entrance sits where two big trees of a forest wall meet. There is no gap: the trees
  stand as usual, and only the background showing between their sides is dark, deepest at the seam.
  Walking north into either of the two trunk-row cells at the seam leads to a clearing in dense woods.
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
- Walking back down the path leaves through the same entrance.

## Engine pieces (fork)

| File | What |
| --- | --- |
| `src/hidden_grotto.c`, `include/hidden_grotto.h` | Mechanic: refill counter, content roll, HA encounter, exit |
| `include/constants/hidden_grotto.h` | Capacity (64), refill chance, state values |
| `include/constants/hidden_grottoes.h`, `src/data/hidden_grottoes.h` | **Generated** grotto list |
| `data/scripts/hidden_grotto.inc` | Content and exit scripts |
| `data/maps/HiddenGrotto*`, `data/layouts/HiddenGrotto*` | The three interiors and the test woods |
| `data/tilesets/secondary/hidden_grotto` | **Generated** grotto art (pairs with `gTileset_CherrygrovePrimary`) |
| `include/global.h` | `SaveBlock3.hiddenGrottoes[64]` and `hiddenGrottoSteps` (65 bytes) |
| `src/field_control_avatar.c` | Step hook (`UpdateHiddenGrottoStepCounter`) |

Each grotto picks one of three interiors (`interior` in the JSON), and any number of grottoes can
share one. Every interior's warp points to `MAP_DYNAMIC`, so entering a grotto records the entrance
as the dynamic warp; the engine identifies the grotto from that warp (entrance map and tile) and
returns the player there on exit. No flags or vars are used besides `FLAG_TEMP_1`.

## Interiors and entrance art

Proposals modelled on B2W2's grottoes, drawn with Cherrygrove's tree (the Johto standard):

| Map | Look |
| --- | --- |
| `MAP_HIDDEN_GROTTO` | Round hollow: B2W2's clearing ringed by trees, content in the middle, flowers |
| `MAP_HIDDEN_GROTTO_BLOSSOM` | Spring version: pink trees ring the clearing, one stands behind the content |
| `MAP_HIDDEN_GROTTO_WINDING` | A path bends through the woods and opens into a small clearing |
| `MAP_HIDDEN_GROTTO_TEST_WOODS` | Test only: a forest wall with three entrances, one per interior |

All four are built by `tools/gba/grottoes/johto_art.py build ENGINE` from character grids in that
file. It copies the green and pink trees pixel for pixel out of CherrygroveCity
(`extract`, stamps in `gba/art/hidden-grottoes/`), uses CherrygrovePrimary's own grass and flower
metatiles, fills forest cells densely (a row of trees every two cells, alternate rows shifted one
cell, so each row's crowns hide the trunks behind), and packs only the tiles that
CherrygrovePrimary doesn't already have into the `hidden_grotto` secondary tileset (122 of 496
tiles, 60 metatiles, 2 palettes). `check ENGINE` fails if the engine files differ from a rebuild.
Previews: `gba/evidence/hidden-grottoes/layout-*.png`.

The entrance (`ENTRANCES` in the builder) changes only the background pixels between two trees'
sides in the six cells at their seam: tree pixels stay as they are, grass and shadow there turn to
the trees' own darkest browns, fading back to shadow toward the edges and the bottom. The two
trunk-row cells are `MB_NON_ANIMATED_DOOR` and passable. To put one on a finished map, that map's
builder applies the same change to its own tree cells.

Save use: one byte per grotto ID plus a step counter, appended to the end of SaveBlock3, so
existing saves load with every grotto unvisited. Grotto IDs index the save bytes, so an ID never
changes or gets reused once a grotto ships. The capacity is fixed at 64 so adding grottoes never
moves save data. The DexNav work adds about 936 bytes to SaveBlock3; together they stay under
the 1624-byte limit.

## Adding a grotto (map threads)

1. The map must be finished. Grottoes go on finished maps, never into an open map PR.
2. On the map, draw the entrance (see above) where two trees of a forest wall meet. Both
   trunk-row cells at the seam warp when stepped on (`MB_NON_ANIMATED_DOOR`). The player walks up
   into either from the south and steps back out on return.
3. Add an entry to `gba/grottoes/grottoes.json`: the next unused `index` (never reuse one),
   `id` (`GROTTO_<PLACE>`), `name`, `map`, entrance `x`/`y` (left cell) and `width` (2 for the
   two seam cells), `interior` (one of the three maps above), and its slots:
   - Pokémon: `{"species": "SPECIES_X", "level": [min, max], "gender": "any|male|female", "weight": n}`
   - Item: `{"item": "ITEM_X", "weight": n}`
4. `python3 tools/gba/grottoes/grottoes.py place ENGINE GROTTO_<PLACE>` adds the warps to the map.
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
ROM headless twice and writes `results.json` and frames. It walks into the entrance of the test
grotto (`GROTTO_TEST_WOODS_HOLLOW`, a `test_only` entrance in the test woods), checks the first
visit rolls content, forces every slot in turn (each Pokémon: sprite, battle, species, level
range, ability slot 2 equal to the species' Hidden Ability, not shiny, female when the slot says
so, grotto empty after running; each item: ball, pickup, empty), revisits empty, measures the
refill rate over 4000 simulated 256-step wraps, checks walking advances the counter, enters the
blossom (by its right-hand cell) and winding grottoes from their own entrances (each rolls its own
grotto and exits back to its own entrance), saves, and cold-reloads the save. Evidence: `gba/evidence/hidden-grottoes/`.
Porymap 6.3.1 renders all four maps identically to the builder's decode (`porymap-*.png`, 0
differing pixels).

## Open

- No real grottoes are placed yet; only the test entrance exists. Placement is coordinated with the
  HGSS map port thread, one finished map at a time.
- Grotto contents are per grotto in the JSON. B2W2's own grotto tables are not copied; each
  grotto's species, levels and weights still need choosing.
- The three interiors and the entrance are proposals for Davis to pick from or change. Other
  regions would get their own tree in the same builder.
- B2W2 also had hidden items in grottoes and gender-only slots tied to version. Neither is built.
