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

Second round, the owner's list ([before and after](evidence/round2-fixes.png)):

- **Mart**: the shared Johto Mart (`source/shared/poke-mart.png`, from `docs/GBA_SHARED_BUILDING_ART.md`'s
  hub copy, provenance in `source/shared/provenance.json`) at (49, 4), its door on the warp (51, 9). The old
  Mart and its flag sign are lawn again. The building's cells are blocked but its top row, walkable as the
  lawn there was, and the two cells the old Mart blocked east of it are walkable lawn; its door animation is cut from the installed art (`field_door.c`, the Mart's own entry).
- **Pokemon Center**: the cleaned shared Center prefab at (58, 4). The path notch under its door takes the
  town's straight path edges, and the old pond-rim strokes left in the lawn east of it are lawn again.
- **Paths**: the shore path's rims (x38-41, rows 17-20) and both door approaches use the town's own path and
  lawn pieces, chosen by neighbours and texture phase.
- **Shore**: the forest's sea strip (x38, rows 28-47) was a flat grey band with white dots. It takes the
  beach's own edge (sea, foam, sand rim, sand) over the animated sea, wobbling as the beach does, and turns
  out of the beach's diagonal at rows 27-28. The boulder on the strip keeps its own pixels.
- **Boardwalk**: the east-west walk (x27-37, rows 18-19) took the pier's plank cell unturned. It takes the
  same cell turned a quarter, planks across the walk as on the pier.
- **Boats**: the three boats lose their resampling speckle (532 pixels): a pixel unlike its neighbours takes
  their colour, and inside the hull a pixel takes its 3x3 majority. Outlines stay whole.
- **Flower bed**: the fenced bed east of the Center's path (x63-66, rows 12-14) gets its lawn rims back,
  copied from the nearest matching cell outside it, so its edges line up with the lawn around it.
- **Trees**: a leftover single forest column takes its tree half a cell over, so the lattice has no gap.

## Tilesets and banks

- Cherrygrove draws on its own copy of CherrygrovePrimary, `cherrygrove_town`, as Routes 30 and 31 have
  theirs. The copy keeps every id and tile the town's camera draws (its kept cells, its border, Route 29's
  window, Route 30's band, sea tiles 1-87) and frees the rest. Its sea animation is CherrygrovePrimary's,
  written to tiles 1-87 only (all the town draws of the 92). Crossing to Route 29 loads another primary;
  the engine redraws the view (PR #39).
- The two regional preview maps (dev warps from Sandgem and Floccesy) draw a frozen copy of Cherrygrove's
  secondary at the base revision, `cherrygrove_preview`, so the town's sheet takes the 12 slots only they used.
- Route 29 draws Cherrygrove's last 8 columns with CherrygrovePrimary. New cells there take primary ids no
  map draws, defined the same in both primaries, from tile slots free in both or secondary slots free in
  both Cherrygrove's and Route 29's sheets. Every other map on CherrygrovePrimary draws exactly as before.
- Cells Route 30 can see take the ids its pack gave them, from 596 (`../route30-catalog/source/pack/mirror-ids.json`).
- Banks: 0 lawn, 2 the Mart, 3 trees, 10 blossoms (both with the lawn's tones in three free slots), 5 rock,
  12 the pond.
- New tiles: 313 in Cherrygrove's sheet, 108 in the copy, 15 in both primaries, 16 shared with Route 29.
  Left: 1 copy slot, no secondary slots. The installer never reuses a tile the sea animation rewrites.
- **Folds**: the art needs more tiles than the sheets hold, so a new texture tile may take an existing one a
  few pixels away, as few as fit: 7 here (138 pixels over 37 metatiles, in the forests and plain ground).
  Edge and feature cells (shore, beach edges, paths, boats, pier, flowers, the Center's and Mart's lawn)
  fold only a ground texture's inner dither, to another tone of the same texture (7 cells moved); rims,
  foam, outlines and nails stay exact. The Center and Mart art, the doors and every cell Route 29 or Route
  30 also draws never fold. Any further art needs slots freed first.

## Checks

| Check | Result |
| --- | --- |
| Every town cell draws as composed (`town.py --install`) | 0 cells differ outside the folds; edge-cell folds are dither only |
| Collision, elevation and behaviour against the base town | unchanged except the Mart's footprint (43 cells, `install.json` `traversal_changed`) |
| Other maps on CherrygrovePrimary (Route 29, New Bark, Violet entrance, both previews) | 0 pixels differ |
| Route 29's window on the town, drawn with CherrygrovePrimary | identical to the town's own |
| Seams with Route 30 and Route 31 (`seams.py`) | clean in all four directions |
| Porymap 6.3.1 export vs native decode | 0 pixels differ (Cherrygrove, Route 29 approach, Route 30, Route 31) |
| Town runtime (`runtime.py`): seven doors in and out (the Mart's included), the walk to Route 29 and back, the pond | passes; frames match the decode outside sprites and the sign popup (`evidence/runtime-summary.json`, `evidence/runtime-doors.png`) |
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
