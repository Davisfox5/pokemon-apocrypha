# KantoFuchsiaCity plan (HGSS `MAP_FUCHSIA`)

Gates: [MAP_CHECKLIST.md](../../../docs/MAP_CHECKLIST.md). Exterior only: the city map itself.
Interiors, gatehouse interiors and Pal Park are separate inventory rows and are not part of this map.

## G1 Reference

- HGSS constant / code: `MAP_FUCHSIA` / `MAP_T08`, header 56, area data bank 16 (map textures 16, buildings 15).
- Size: 64 x 64 cells, 2 x 2 matrix chunks of `map_matrix_0000_EVERYWHERE` from (37, 12).
- Decoded render: `tools/gba/maps/fuchsia_city/hgss_render.py PHG OUT` (the Route 32 renderer with Fuchsia's
  header and bank). Review copy: `hgss-vs-frlg.png` in the project files (`fuchsia-city/`).
- Registration: native = HGSS + (0, 0), whole map. Gate file: `gba/maps/gates/KantoFuchsiaCity.json`.
- Warps (HGSS event file `053_T08.json`, local cell = world - (1184, 384)):

| # | Cell | Destination | Inventory status |
| --- | --- | --- | --- |
| 0, 1 | (57, 38), (57, 39) | Route 15 Fuchsia gatehouse | not started |
| 2, 3 | (19, 61), (20, 61) | Route 19 Fuchsia gatehouse | not started |
| 4 | (13, 32) | Fuchsia Mart | not started |
| 5, 6 | (30, 19), (31, 19) | Pal Park entrance | optional scope (batch X) |
| 7 | (11, 55) | Fuchsia Gym | not started |
| 8 | (16, 55) | Southwest house | not started |
| 9 | (25, 55) | Pokémon Center 1F | not started |
| 10 | (38, 51) | Safari Zone warden's house | not started |

- Connections: Route 18 on the west edge (rows 41 to 44), not started. Route 15 and Route 19 are reached
  through their gatehouses (warps above), so they are not map connections.
- Buildings in the HGSS data: Pal Park hall (top centre), Mart (14, 32), Gym (12, 54), Center (26, 54),
  three houses (17, 54), (21, 54), (39, 50), (43, 50), Route 15 gatehouse exterior (61, 39), eleven
  Safari exhibit pens, five signs.
- Occluded or uncertain squares: rows 0 to 13, columns 28 to 33 are flagged walkable in HGSS but sit
  under the Pal Park hall and cannot be reached (rows 14 to 18 are blocked). They will be drawn as the
  building and trees and listed in `adapt_walk`. Nothing else is occluded.

## G2 Sourcing plan

Approved by owner: 2026-11-22 (Davis, "So are you doing it or what?" in reply to the plan card; taken as approval of the plan as written)

HGSS's Fuchsia is a remake of FireRed's, and the expansion checkout already carries FireRed's Fuchsia
art as native Gen 3 tiles (`gTileset_General_Frlg` + `gTileset_FuchsiaCity`, used by `FuchsiaCity_Frlg`,
Route 15 and Route 19). The proposal: HGSS's layout, square by square, drawn with FireRed's Fuchsia
art. FRLG cells below are `FuchsiaCity_Frlg` layout coordinates unless another map is named.

| Element | Where on the map | Source | Tileset and ids |
| --- | --- | --- | --- |
| Ground | everywhere open | FRLG | General_Frlg lawn (FRLG Fuchsia open ground) |
| Paths | HGSS dirt paths | FRLG | General_Frlg sand path and its edges, as FRLG Fuchsia's paths |
| Tall grass | none in HGSS Fuchsia | none | none |
| Trees | forest border and tree rows | FRLG | General_Frlg pine trees as FRLG Fuchsia's border |
| Rock / cliff faces | SW plateau behind the Gym row, south rims | FRLG | Levels counted from HGSS heights with the owner-accepted level method (`route32_native/levels.py`, contour audit zero breaks); drawn with `rock_frlg` (`route32_native/rock.py`), FRLG Fuchsia's rock, face height to the Route 36 standard; only protruding corners softened |
| Ledges | none in HGSS Fuchsia | none | none |
| Water / shore | pen ponds, fenced pond by the warden's house | FRLG | FuchsiaCity pond (FRLG (6..10, 6..9), (34..41, 23..26)) |
| Stairs | none in HGSS Fuchsia | none | none |
| Railings / fences | metal fences along paths and the pond | FRLG | General_Frlg metal fence as FRLG Fuchsia's |
| Bridges / docks | none | none | none |
| Safari exhibit pens | eleven pens north and west | FRLG | FuchsiaCity hedge pens (FRLG (5..11, 5..10) etc.); HGSS pen contents (pond, flower beds) from FRLG pond and flowers |
| Pal Park hall | top centre, doors (30..31, 19) | FRLG | FuchsiaCity Safari Zone building (FRLG (22..27, 0..5)) |
| Pokémon Center | (26, 54) | FRLG (proposed Kanto kit) | General_Frlg Center exterior |
| Mart | (14, 32) | FRLG (proposed Kanto kit) | General_Frlg Mart exterior |
| Route 15 gatehouse exterior | east edge (57..63, 36..40) | FRLG (proposed Kanto kit) | FuchsiaCity gate from `Route15_Frlg` (10..16, 8..13), mirrored side as needed |
| Gym | (12, 54) | FRLG | FuchsiaCity Gym exterior (FRLG (6..12, 28..32)) |
| Houses | SW house, warden's house, the two plain houses | FRLG | FuchsiaCity grey-roof houses (FRLG (13..22, 28..32), (32..37, 28..31)) cut to HGSS's footprints |
| Signs and props | five signs, flowers | FRLG | General_Frlg / FuchsiaCity signs and red flowers |

- Tileset pair: `gTileset_KantoFuchsia` (primary, `kanto_fuchsia`) + `gTileset_KantoFuchsiaCity` (secondary,
  `fuchsia_city_kanto`). Found at G3: the Emerald build does not compile FireRed's tilesets (they sit under
  `IS_FRLG`), so FireRed's General and Fuchsia art is re-split into an Emerald-format pair, pixel for pixel
  (`tools/gba/maps/fuchsia_city/pack.py`): same tiles, same palette banks, same metatiles and behaviours. The
  source art is unchanged and FireRed's own maps and tilesets are untouched. Animated flowers and water show
  their first frame (no FRLG animation callback in this pair).
- Expected budget: FRLG's primary as is (640 / 640 / 7). Secondary starts at FRLG Fuchsia's usage;
  new composites only where an HGSS footprint differs from FRLG's (houses, pen contents). Measured at G3.
- Seam ids with neighbours: none yet. Route 18 is not built; the west edge stays open ground under
  border trees and gets its connection when Route 18 is built.
- Warps: none yet. Every door and gate exit is drawn on HGSS's warp cell but stays solid until its interior
  or route exists (a warp needs a real destination to build; same rule as Saffron v3).

## G3 Build notes

- Generator: `tools/gba/maps/fuchsia_city/build.py` (cell-by-cell materials from the decoded HGSS ground and
  walkability), then `pack.py` (Emerald-format pair and layout). Engine map `KantoFuchsiaCity`, layout
  `LAYOUT_KANTO_FUCHSIA_CITY`, group `gMapGroup_KantoFuchsia`.
- Square-by-square sources: lawn, pale lawn, dirt paths, trees and fences autotiled from FRLG Fuchsia's own
  pieces on HGSS's cells; Mart, Gym, Center, houses, Pal Park hall, pens and ponds stamped from FRLG Fuchsia;
  the Route 15 gate from FRLG Route 15; the Route 19 gate's north door from FRLG Route 5's south gate.
- Signs: FRLG's signpost on HGSS's four sign cells. Two stand on dirt, so they are FRLG's sign (top layer)
  over that cell's own dirt (bottom layer); no art is pasted over anything. Sign text is not added yet
  (HGSS's text names Janine and Pal Park, which is story).
- Rock: one level, counted from HGSS's heights (plateau cells at height 2 over a floor at 1; the south
  hills the same), drawn with FRLG's mountain nine-slice and its low walls and ledge, the pieces `rock_frlg`
  uses. Fuchsia has one level and no stairs, so there is no terrace contour to audit beyond the single ring.
- Not reproduced: HGSS's six lamp posts (no FRLG piece), the hidden Nugget at (48, 29) (needs a new flag).
- Every walkability difference from HGSS is listed, with its cause, in the gate file.

## G5 Self-review

Gate (2026-11-22): PASS on build, glitch (0 black cells), budget (secondary 112/512 tiles, 63/512
metatiles), seams (no connections), warps (none), walk (0 of 4096 after adapt_walk), Porymap 6.3.1.
Headless run (tools/gba/maps/fuchsia_city/runtime.py): 107-step walk (30,20) to (56,39) with no
interruption; doors (30,20) hall, (25,56) center, (11,56) gym, (16,56) house, (38,52) warden, (13,33) Mart,
gates (56,39) and (19,60) refuse the player; pen (15,27) and pond fence (36,40) block. 32 frames compared
with the native render: 31 identical, east-pond (44,40) 99.94% (player reflection/shadow pixels).

Checked (coordinates) and fixed:

- Lawn base used tufted pieces 0xA/0xB (read hex as decimal); fixed to 0x10/0x11 everywhere.
- HGSS canopy/roof overhang rows (south edge of tree rows, building eaves) had been fenced; now walkable
  and listed in adapt_walk.
- East house pair (37-44, 48-51): second FRLG house source carried a shed piece; both use the warden house.
- Mart (11-14, 29-32): shifted one cell so its door sits on HGSS's (13,32).
- Plateau (6-29, 45-51): row 51 under the house roofs (15-22) uses the interior rock piece so the roofs
  sit on rock. Low walls (6, 52-59) and (29, 52-59) hang from the sw/se corners the way FireRed does
  (0x83 under 0x78, its only use in FRLG); the corner's rounded foot leaves a 2 px lawn notch, kept as FRLG draws it.
- Ledges (7-8, 13-16, 24-28 on row 59) end with FRLG's left/right end pieces.
- Signs (29,21), (36,51), (24,40), gym sign (9,57): on non-lawn ground they are composites (ground bottom
  layer, sign top layer); no background colour carried over.


## G6 Owner review log

- (pending)
