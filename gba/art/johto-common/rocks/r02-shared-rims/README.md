# R02 reusable grass-to-rock transitions

- [Reusable tiles and transparent edge modules](review/shared-tiles.png)
- [Full native map](review/native-full.png)
- [Before/after](review/comparison.png)
- [Wall close-up](review/wall-detail.png)
- [Native gameplay](review/gameplay.png)

## Shared set

Two explicit 16-pixel edge profiles, each one to two pixels wide, generate all four orientations by rotation/reflection. Source alpha remains transparent outside the edge itself. Original stone textures remain intact beyond that strip. The catalog includes paired front/side/rear/mirrored faces, a common outside-corner master, and its mirror. Destination terrain supplies the backing. Do not repaint separate edge patterns at individual map coordinates.

The shared outside-tip mask removes only three pixels (a two-pixel stepped radius). Four exposed convex tips use that same mask or its reflection. Concave geometry and the stacked rock-to-rock corner remain intact. The southwest return uses the reflected tip mask on its existing return geometry; it is not replaced by the mirrored side-facing master. Mirrored full faces/corners are reference modules for future receiving orientations.

All exposed grass-topped rock edges in this Route 36 family use the shared modules: 75 placements recorded in source/placements.json. Grass overlays are excluded from stacked rock-to-rock seams and the stair flights. Both longitudinal and transverse grass-topped faces are covered per the latest instruction. Trees, paths, buildings, inner-corner geometry and low-foot edges are retained. The earlier generated mockup was not imported.

## Native evidence

Engine b905f4cb70 on codex/r02-cliff-review, draft PR12. Build passed; actual offscreen Porymap/native pixel equality passed. Both stair lanes/directions, northern connection, southwest barriers, gate approach and ordinary save/cold reload/title Continue pass in background runtime. Static comparison confirms unchanged collision/elevation and decoded behavior everywhere, and identical installed stair pixels.

226 cells /904 quadrants reviewed with assembled native map and gameplay. No new palette; unreferenced storage reused only. Owner visual approval pending. No production merge or desktop emulator. This installs on Route 36 only; the modules are available for subsequent regional reuse, not a claim that other maps have been migrated.

## Reproduce

r02_shared_rims.py --engine ENGINE --install requires clean base 3f94e996f228fce092cdc732309636632dc5cae7. r02_review.py generates coordinate sheets. Use existing r02_markup2_runtime.py against the resulting ROM; movement is intentionally unchanged. r02_publish.py records engine/Porymap/runtime evidence. No ROMs or saves committed.
