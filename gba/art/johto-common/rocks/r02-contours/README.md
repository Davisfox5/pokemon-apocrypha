# R02 owner-marked three-level contours

- [Full native route](review/native-full.png)
- [Owner markup versus revision](review/markup-comparison.png)
- [Background gameplay](review/gameplay.png)

The owner annotation supersedes the earlier request for a continuous northern right wall. Red courses are snapped to the native grid. The green run at x32, y0–15 is restored to grass. The yellow southwest run now uses the same rock family and palette as the other side faces.

Two stacked rises occupy the northwest. The upper rise turns east between the tree rows, then joins the right stair wall. The lower rise turns west and south around the southwest forest. Complete tree rows were repositioned at their normal pitch, with no tree pixels over rock and no overlapping rebuilt trunk footprints. The southwest rear rim uses a vertically mirrored face; its corners were inspected in the assembled map and native gameplay.

Three design heights are recorded in source/terrain-levels.npy. These represent visual terrain levels, not new GBA elevation-bit semantics. Both diagonal flights retain their existing native movement and rise east: lower to middle, then middle to upper. The restored northern grass connector is traversable again. The southwest bend blocks wall crossings while retaining the outside route.

## Validation

Engine commit c5ef879f46 on codex/r02-cliff-review, draft PR12. Native ROM build passed. Actual offscreen Porymap export equals the native render pixel for pixel. Background runtime checked both stair lanes in both directions, barriers, northern connection, southwest passage, save, cold reload and ordinary title Continue. 399 cells /1596 quadrants plus assembled screenshots inspected. Owner visual approval remains pending. No desktop emulator opened; production has not been merged.

239 affected cells; 101 collision changes; no behavior changes. Zero tree/rock overlap and zero overlapping rebuilt trunk footprints. Reused only proven unreferenced native slots: five tiles and fifteen metatiles; no new palettes or live-ID repacking. Bank remains 1008 padded tile slots /488 metatiles.

## Reproduce

Run tools/gba/maps/johto_common/r02_contours.py --engine ENGINE --install against clean base 768efc0592eb0d4761a2a8aaa13ad8ce177bf151. Build generated assets and ROM using the pinned ARM toolchain. r02_contours_runtime.py performs headless checks. r02_review.py generates cell sheets; r02_publish.py collects Porymap/runtime evidence. Source owner-markup.jpg preserves the supplied annotation. ROMs and saves are excluded.
