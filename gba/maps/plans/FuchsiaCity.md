# FuchsiaCity plan (HGSS `MAP_FUCHSIA`)

Gates: [MAP_CHECKLIST.md](../../../docs/MAP_CHECKLIST.md). Exterior only: the city map itself.
Interiors, gatehouse interiors and Pal Park are separate inventory rows and are not part of this map.

## G1 Reference

- HGSS constant / code: `MAP_FUCHSIA` / `MAP_T08`, header 56, area data bank 16 (map textures 16, buildings 15).
- Size: 64 x 64 cells, 2 x 2 matrix chunks of `map_matrix_0000_EVERYWHERE` from (37, 12).
- Decoded render: `tools/gba/maps/fuchsia_city/hgss_render.py PHG OUT` (the Route 32 renderer with Fuchsia's
  header and bank). Review copy: `hgss-vs-frlg.png` in the project files (`fuchsia-city/`).
- Registration: native = HGSS + (0, 0), whole map. Gate file: `gba/maps/gates/FuchsiaCity.json`.
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

Approved by owner: pending

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
| Rock / cliff faces | SW plateau behind the Gym row, south rims | FRLG | FuchsiaCity rock ridge (FRLG (4..28, 26..35)), face height to the Route 36 standard |
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

- Tileset pair: `gTileset_General_Frlg` + a new secondary `gTileset_FuchsiaCityApoc`, copied from
  `gTileset_FuchsiaCity` so FireRed's own maps stay untouched. The layout is FRLG-format (`isFrlg`).
- Expected budget: FRLG's primary as is (640 / 640 / 7). Secondary starts at FRLG Fuchsia's usage;
  new composites only where an HGSS footprint differs from FRLG's (houses, pen contents). Measured at G3.
- Seam ids with neighbours: none yet. Route 18 is not built; the west edge stays open ground under
  border trees and gets its connection when Route 18 is built.
- Warps: the door and gatehouse warps are placed on their visible doors. Their destinations are not
  built yet, so they are listed in `adapt_warps` until each map lands.

## G5 Self-review

Checked (coordinates) and fixed: (after G4)

## G6 Owner review log

- (pending)
