# R02 second owner markup

- [Full route](review/native-full.png)
- [Markup versus native revision](review/markup-comparison.png)
- [Western detail](review/west-detail.png)
- [Background gameplay](review/gameplay.png)

## Changes

Red: southwest side shifts from x8 to x9; right-hand wall at x32 extends through y31. Green: old x8 wall restored to grass. Yellow: three inner joins repaired using contiguous side/front texture planes instead of rotated outer corners. The western gate keeps its installed building and stair artwork, with destination dirt continued beneath the stair apron.

Orange: marked northern trees move right one cell; the pair beside the upper wall moves left; two western forest rows move right; the three clearing trees move down; four southeastern rows move left. Each displacement is one native 16px tile. See source/tree-moves.json. Supporting forest adjustments keep the new walls clear: adjacent southwest rows realigned, two intersecting trees removed, and eastern rows continued beyond the boundary to keep it sealed. No replacement tree artwork or cropped in-map canopies.

## Evidence and limits

Engine 3f94e996f2 on codex/r02-cliff-review, draft PR12. Native build passed; actual offscreen Porymap export equals the native render. Background runtime passed both stair lanes/directions, wall shoulders, northern route after tree shifts, old-wall opening/new southwest barrier, gate apron approach, save/cold reload/title Continue. Both installed stair graphics remain byte-identical. Southern extension and eastern boundary collision verified in decoded map data; inaccessible forest wall cells were not claimed as walked tests.

547 affected cells; 42 collision changes. Zero tree/rock overlap, zero overlapping rebuilt trunk footprints, zero native pixel errors. 779 cells /3116 quadrants reviewed with assembled map and gameplay. Existing terrain levels and behavior retained. Tile bank stays at 1008 padded slots; only unreferenced native storage reclaimed. Owner visual approval pending. Isolated review checkout only, no production merge or desktop emulator.

## Reproduction

r02_markup2.py --engine ENGINE --install requires clean base c5ef879f46dd2cac5b4e9fd62494da752bcd7fb7. Build generated assets and native ROM with the pinned toolchain. r02_markup2_runtime.py runs background checks; r02_review.py generates coordinate sheets; r02_publish.py collects evidence. Supplied annotation preserved as source/owner-markup.jpg. No ROM or save committed.
