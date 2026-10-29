# Cherrygrove City, cleaned up to AGENTS.md's native visual rules

2026-10-26, engine branch `claude/routes-30-31-catalog` (PR #39). The owner-approved town keeps its
layout, warps and every untouched cell's metatile id. What changed is the art of its elements, redrawn in
Johto's shared vocabulary and checked against HGSS Cherrygrove (rendered from pokeheartgold's own data).

![before and after](evidence/before-after.png)

## What changed

First round:

- **North edge**: the sea cliff is Johto rock (Mahogany's FRLG terraces in the HGSS ramp, `rock.py`) and
  turns north into Route 30's west wall; rock tops meeting same-height lawn take the soft grass fringe
  ([Route 30's README](../route30-catalog/README.md#cherrygroves-north-edge)).
- **Forests**: every woods block is the route's overlapping tree lattice (2x2 roots, the crown in the row
  above, crowns overlapping so no gap opens). Blossoms stay where the town had them. Crowns over a walkable
  cell draw above the player.
- **Islands**: the bay's two islands are Johto rock in the cliff's ramp, two terraces as HGSS's islands
  are (the upper plateau to the north-west, the lower ledge south and east), the sea animating under each
  rim. The grey boulders and the buoy line stay.
- **Pond**: Route 30's pond treatment (Route 43's method: HGSS freshwater texture, a rough mud and grass
  bank about two pixels inside the water cells). The old stone rim is lawn again. The pond is still
  surfable ocean water, as the owner's town has it.
- **Beach edges**: old tile reuse had left darker sand wedges (222, 206, 148) along the beach's diagonal
  lawn edges, 18 cells. They are beach sand again with the ground painter's beach and lawn rim.
- **Houses**: unchanged. They are the owner's accepted Cherrygrove architecture.

Owner revisions ([before and after](evidence/round3-fixes.png)):

- **Mart**: M01, the approved Johto Mart (`../johto-mart/`, `../johto-common/approved-buildings.json`), at
  (49, 4), its door on the warp (51, 9), pixel for pixel on the object layer. The old Mart and its flag sign
  are ground again. Its top row draws over the player and is walkable, its wall rows are solid, and the two
  cells the old sign blocked east of it are walkable lawn (as the owner's Oct 15 installation has it).
- **Pokemon Center**: C06, the approved Johto Center (`../johto-center/`), at (59, 5), door (61, 9), its top
  row walkable under the roof. Its 21 colours take banks 8 and 9 (the old Center's and old Mart's, free with
  them gone): the 12 its ground-edged tiles draw in one, the roof and sign tones in the other.
- **Doors**: the Mart (137) and Center (144) keep their door ids. Their open frames are cut from the
  installed art, each tile in the bank that draws it (`graphics/door_anims/johto_restart`, `field_door.c`).
- **Paths**: every dirt path takes Route 30's road ground (the painter's sand and its soft lawn rim) in
  place of the dashed grey rims and speckle, its corners rounded as HGSS's are (6 px). Only lawn and path
  pixels change: houses, signs, fences, flowers and shadows keep every pixel. The notches run up under the
  Mart's and Center's doors. The texture's darkest pebble tone is its next tone (no primary bank has it,
  and the town's path never drew it). The edges are straight: the painter's wobble made every corner and
  run unique, more tiles than the sheets hold.
- **Shore**: the forest's sea strip (x38, rows 28-47) was a flat grey band with white dots. It takes the
  beach's own edge (sea, foam, sand rim, sand) over the animated sea, wobbling as the beach does, and turns
  out of the beach's diagonal at rows 27-28. The boulder on the strip keeps its own pixels.
- **Dock**: the pier (x25-26, rows 15-22) and boardwalk (x27-37, rows 18-19) take HGSS Route 32's pier
  (`source/hgss/pier.png`, `tools/gba/maps/cherrygrove_town/hgss_pier.py`): an 8 px rail down each side and
  cross boards with their grain, the boardwalk turned a quarter, a beam across each end. No plank seams
  every three pixels, no nails. Six wood tones in bank 9.
- **Boats**: the fishing boat and the motorboat are redrawn clean on their own silhouettes in their own
  bank-11 colours (`boats.py`): outline, gunwale, flat deck with its hatch and crates, cabin, windows,
  door, transom or hull side. The large boat west of the pier is as the base town draws it.
- **Trees**: a leftover single forest column takes its tree half a cell over, so the lattice has no gap.

## Tilesets and banks

- Cherrygrove draws on its own copy of CherrygrovePrimary, `cherrygrove_town`, as Routes 30 and 31 have
  theirs. The copy keeps every id and tile the town's camera draws (its kept cells, its border, Route 29's
  window, Route 30's band, sea tiles 1-87) and frees the rest. Its sea animation is CherrygrovePrimary's,
  written to tiles 1-87 only (all the town draws of the 92). Crossing to Route 29 loads another primary;
  the engine redraws the view (PR #39).
- The two regional preview maps (dev warps from Sandgem and Floccesy) draw a frozen copy of Cherrygrove's
  secondary at the base revision, `cherrygrove_preview`, so the town's sheet takes the 12 slots only they used.
- The town's sheet stops at slot 495: tiles 1008-1023 are where `field_door.c` draws a door's frames.
- Route 29 draws Cherrygrove's last 8 columns with CherrygrovePrimary. New cells there take primary ids no
  map draws, defined the same in both primaries, from tile slots free in both or secondary slots free in
  both Cherrygrove's and Route 29's sheets. Every other map on CherrygrovePrimary draws exactly as before.
- Cells Route 30 can see take the ids its pack gave them, from 596 (`../route30-catalog/source/pack/mirror-ids.json`).
- Banks: 0 lawn and paths, 2 the Mart, 3 trees, 10 blossoms (both with the lawn's tones in three free
  slots), 5 rock, 8 and 9 the Center (9 with the wood), 11 the boats, 12 the pond.
- New tiles: 317 in Cherrygrove's sheet, 192 in the copy, 15 in both primaries, 26 shared with Route 29.
  Left: 23 copy slots, no secondary slots. The installer never reuses a tile the sea animation rewrites.
- **Folds**: a new texture tile may take an existing one a pixel away where the sheets run short (598 pixels
  over 113 metatiles). Edge and feature cells (paths, shore, beach edges, boats, dock, the buildings' lawn)
  fold only a ground texture's inner dither, to another tone of the same texture; rims, foam, outlines and
  art stay exact. The building art, the doors and every cell Route 29 or Route 30 also draws never fold.

## Checks

| Check | Result |
| --- | --- |
| Every town cell draws as composed (`town.py --install`) | 0 cells differ outside the folds; edge-cell folds are dither only |
| Collision, elevation and behaviour against the base town | unchanged except the Mart's and Center's footprints (67 cells, `install.json` `traversal_changed`) |
| Other maps on CherrygrovePrimary (Route 29, New Bark, Violet entrance, both previews) | 0 pixels differ |
| Route 29's window on the town, drawn with CherrygrovePrimary | identical to the town's own |
| Seams with Route 30 and Route 31 (`seams.py`) | clean in all four directions |
| Porymap 6.3.1 export vs native decode | 0 pixels differ (Cherrygrove, Route 29 approach, Route 30, Route 31) |
| Town runtime (`runtime.py`): seven doors in and out (the Mart's included), the walk to Route 29 and back, the pond | passes; every frame, after each door too, matches the decode outside the sprites and the sign popup (`evidence/runtime-summary.json`, `evidence/runtime-doors.png`) |
| Route 30 and Route 31 runtimes | pass |

## Limits

- The transplant house's warp (42, 32) sits inside the south forest, as it does in the base town.
- The tile budget is spent.
- Owner visual acceptance.

## Reproduce

```sh
python3 tools/gba/maps/cherrygrove_town/town.py ENGINE --preview   # draw the town (evidence/preview.png)
```

The install runs inside Route 30's pipeline ([its README](../route30-catalog/README.md#reproduce)):
`--render` and `--primary` before `pair_pack.py --install`, `--install` after it. Every run starts from
Cherrygrove at the engine's base revision (`base.py` BASE_REV). Treat the tools as provenance: once the owner
edits the town in Porymap, edit the native files and don't replay the generator over them.
