# Per-map checklist: G0 to G7

Owner-approved 2026-11-20. Every model and instance follows this, in order, for every HGSS map
(route, town, cave floor, interior). A map does not move to the next gate until the current one
passes. This is the order of work; [GBA_MAP_RECONSTRUCTION.md](GBA_MAP_RECONSTRUCTION.md) and the
cleanup rules in [AGENTS.md](../AGENTS.md) stay the standard each gate is held to.

The master list is [maps/HGSS_MAP_INVENTORY.csv](maps/HGSS_MAP_INVENTORY.csv): one row per HGSS map,
generated from pokeheartgold.

**Where things go.** Map files, tilesets and scripts: `Davisfox5/pokeemerald-expansion`, branched
from `apocrypha`. Plans, gate files, inventory, tools and review images: `Davisfox5/pokemon-apocrypha`.
Never the other way round (see the table at the top of AGENTS.md).

Statuses: `not started`, `sourcing plan`, `building`, `in review`,
`accepted`, `merged`. Update the row in the same commit that moves the map to a new gate.

## G0 Claim

1. Find the map's row. Run `python3 tools/gba/maps/inventory/build_inventory.py PHG --check`.
2. If the row already has a PR or branch, continue that branch. Never open a second PR for a map.
3. Work in batch order (the `batch` column) unless the owner asks for a specific map.
4. Set `status` to `sourcing plan`, fill `branch`, commit (in pokemon-apocrypha).

## G1 Reference

Write `gba/maps/plans/<MapName>.md` (copy [the template](maps/PLAN_TEMPLATE.md)) with:

- HGSS constant, size in cells, matrix cells, decoded render (route29/30 catalog `hgss_render.py` method).
- Every warp, connection and neighbour, with the neighbour's inventory status.
- Registration: native cell = HGSS tile + offset. Record it in `gba/maps/gates/<MapName>.json` now.
- Squares that are occluded or uncertain, and how they will be read.

## G2 Sourcing plan (owner approves before any drawing)

In the same plan file, a table with one line per element: ground, paths, tall grass, trees, rock and
cliff faces, ledges, water and shore, stairs (axis and direction), railings and fences, bridges,
buildings, doors, signs, and for interiors every wall, floor and furniture piece.

Each line names exactly one source:

- **Regional kit** (already approved; see below)
- **Accepted map** (name the map and its metatile ids)
- **Emerald** or **FRLG** native asset (name the tileset and ids)
- **Converted HGSS** texture (name the HGSS model/texture)
- **New art** (say why nothing above fits)

Also list the tileset pair, the expected tile and palette budget, and the seam ids shared with each
neighbour. Post the plan to the owner in one message. Do not draw until the owner approves it; then
record the approval date in the plan and set `status` to `building`.

A change of source after approval goes back to the owner before it is used.

## G3 Build

Build in the game source repository, **`Davisfox5/pokeemerald-expansion`**, on a branch from the
current `apocrypha` (which holds every merged neighbour). Map, layout, tileset and script changes
go there and only there. The plan, gate file, generator scripts and evidence go to a matching
branch in pokemon-apocrypha. Record both PRs in the inventory (`pr` and `hub_pr`). Follow GBA_MAP_RECONSTRUCTION.md steps 2 and 3
square by square. Use only the sources the plan lists. Never draw over existing content: see
"Never draw over what is already there" in AGENTS.md (owner rule, 2026-11-20).

## G4 Automated checks

```sh
python3 tools/gba/maps/map_gate.py ENGINE MapName --phg PHG --porymap PORYMAP_EXPORT_DIR --build --out OUT
```

Every check must say `pass`. `NOT RUN` is not a pass.

| Check | Fails when |
| --- | --- |
| build | the ROM does not build |
| glitch | a used metatile points at a missing tile or metatile, or a palette past 12. Cells drawing solid black are listed for G5 |
| budget | tiles, metatiles or palettes exceed the engine limits, or reserved door slots are used |
| seams | any cell visible across a connection draws differently in the two maps' tilesets |
| warps | a warp is not on a door, stair, ladder or arrow cell, leads nowhere, or its destination does not lead back |
| walk | walkable cells differ from decoded HGSS at the registered offset |
| porymap | the Porymap 6.3.1 export differs from the native render |

Deliberate differences go in `gba/maps/gates/<MapName>.json` (`adapt_walk`, `adapt_warps`,
`adapt_seams`), each explained in `notes`. Run the gate on every neighbour too, so both sides of each
seam are checked. Cloud setup for the build and the Porymap probe: see GBA_REMOTE_HANDOFF.md and the
`cloud-gba-verification-setup` project memory.

## G5 Self-review sheet

Before the owner sees anything, produce and inspect:

1. Whole map: HGSS reference beside native, same scale.
2. Coordinate-labelled crops of every edge seam, stair (first and last tread, both joins), railing,
   ledge end, door, building footprint, cliff corner and shoreline corner.
3. Headless gameplay frames crossing each connection and using each warp, both directions.
4. Every solid-black cell the gate listed, confirmed deliberate or fixed.
5. An old-vs-new diff of every changed cell: each changed pixel belongs to the element being
   changed (no tree, prop, shadow or neighbouring ground drawn over), and every patch edge
   (grass, water, path) is softened into its surroundings.

Fix what you find and rerun G4. Write the list of what was checked and fixed into the plan file.

## G6 Owner review

Post the review sheet in one message with the gate output. Set `status` to `in review`.
Owner changes go back to G3 (or G2 if a source changes) and through G4 and G5 again.
When the owner accepts, set `status` to `accepted` and fill `accepted` with the date.

## G7 Merge

Merge the accepted map's fork PR into pokeemerald-expansion's `apocrypha` and its pokemon-apocrypha
PR into `main`, together, right away so the next map builds on it. Close superseded
PRs for that map, set `status` to `merged`, clear `branch`, and run the inventory check with
`--engine` against the merged checkout.

## Regional kits

Each region has its own shared interiors and buildings (owner, 2026-11-20). Johto's Pokémon Center,
Mart, house interiors and gatehouses differ from Kanto's, and later regions get their own. The
`kit` column in the inventory names the kit a map uses (`johto-center`, `kanto-gatehouse`, ...).

- Build each region's kit once, before that region's first batch: exterior Center and Mart, Center
  1F/2F, Mart interior, gatehouse, a small set of house interiors, gym shell. Owner approves the kit.
- After approval, every map of that kind in that region uses the kit. Only the town-specific
  differences (size, furniture, NPC dressing) go through G2.
- Johto's kit starts from the approved Violet Center and the shared Johto Mart
  (`gba/art/johto-common/approved-buildings.json`).

## Batches

Finish and merge one batch before starting the next, so neighbours share tilesets and seams are
checked against merged maps. Order: A New Bark-Violet, B Route 32-Azalea, C Route 34-Goldenrod,
D Route 35-Ecruteak, E Route 38-Cianwood, F Route 42-Blackthorn, G League and Mt. Silver, then
Kanto K1 to K4. Batch X (Frontier, Pokéathlon, Safari Zone, Pal Park, Center Wi-Fi basements) is
optional scope until the owner says otherwise.
