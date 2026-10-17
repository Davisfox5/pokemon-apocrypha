# R02 complete rock-and-grass terrain tiles

- [Complete reusable tiles](review/shared-tiles.png)
- [Full native map](review/native-full.png)
- [Every corner, before and after](review/all-corners.png)
- [Map comparison](review/comparison.png)
- [Background gameplay](review/gameplay.png)

## Authoring contract

Use the 17 complete 16x16 masters in source/tiles and source/catalog.json. Each contains its own stone and appropriate grass cap; the catalog contains no independent grass slivers or corner-mask pieces. Place one master per wall cell. All 102 installed wall cells equal their corresponding complete PNG exactly. Native 8x8 palette/layer encoding is an implementation detail; authors do not assemble these terrain tiles from separate grass objects.

Grass caps use a compact 1–3px interlocking edge built into each tile. Uncapped rock tiles handle stacked stone joins. Faces retain their source texture beyond the cap. Destination objects such as trees remain separate. This terrain-specific combination follows the owner's explicit request and does not change the transparent-background rule for objects.

## Corner coverage

All eight turns were audited in source/corner-audit.json. Five convex turns use the same tiny three-pixel tip treatment. The previously omitted lower northwest stacked turn (14,4) is included; its backing is stone, so it does not introduce a false grass patch between rock tiers. Three concave turns retain their geometry as previously requested. The full before/after corner sheet shows both groups. No tree row moved; owner will identify the remaining row later.

## Evidence

Engine bc5612dd84 on codex/r02-cliff-review, draft PR12. Native build, actual Porymap/native equality, background stairs/route/barrier/gate approach and save/cold reload/title Continue pass. Static comparison confirms unchanged collision/elevation, decoded behaviors and stair artwork. 250 cells /1000 quadrants plus all eight turns and native gameplay inspected. Owner visual approval pending. No desktop emulator or production merge. Source assets and engine changes pushed separately; no ROMs or saves committed.

## Reproduce and reuse

r02_complete_tiles.py --engine ENGINE --install requires clean base b905f4cb70e59c8e4cf8272c43de5512f18590db. r02_review.py builds coordinate sheets. Existing r02_markup2_runtime.py validates unchanged movement on the resulting ROM; r02_publish.py gathers evidence. Use this complete-tile catalog for the next R02-family placement, superseding r02-shared-rims' separate-module authoring. Other maps are not migrated by this change.
