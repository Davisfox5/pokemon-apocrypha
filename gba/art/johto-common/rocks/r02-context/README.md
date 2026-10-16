# R02 contextual borders and complete rock faces

Replaces the rejected flattened-border candidate. Owner visual approval pending.

- [Original / previous / corrected](review/comparison.png)
- [Continuous upper wall](review/upper-wall.png)
- [Reusable mirrored pieces](review/mirrors.png)
- [Native gameplay](review/gameplay.png)
- [Full native map](review/native-full.png)

## Changes

Restore pre-smoothing native ground contour from `r02-joins` in the lower plateau. Select tall-grass masks from actual N/S/W/E grass neighbors, with destination ground underneath. Preserve irregular path edges; no global rounding or flattening. Context ledger: `source/contexts.json`.

Extend the west face through y5–25 and its upper corner; use the HGSS clean front-wall band across the north run. Apply the reflected side face to the east wall at x32, y16–25. Keep the existing east stair art and both stair movements. Trees retain their exact approved pixels. Transparent face, corner and stair-section masters and exact mirrors are in `source/catalog.json`; terrain is separate.

## Evidence

Engine `492da86574614f83e1c9e99c3d5de9686029b8e5` on `codex/r02-cliff-review`, draft PR12. Native build, actual Porymap pixel equality, both stair directions, grass entry/return, plateau traversal, ordinary save, cold reload and title Continue pass. No desktop emulator opened. No collision, elevation or behavior changes. 318 cells / 1272 quadrants inspected with assembled context; see `evidence/visual-review.json`.

916 tile slots, 488 primary metatiles; 100 tiles and 61 metatiles appended. Existing palette banks reused, no palette repack. This is the isolated review checkout, not a production merge. Visual approval remains with the owner.

## Reproduce

Run `tools/gba/maps/johto_common/r02_context.py --help` for preview/install from clean engine base `5b14c523c1a0688f3c291b485998bd91fd05dc86`. Runtime harness: `r02_context_runtime.py`; numbered cell sheets: `r02_review.py`; evidence collector: `r02_publish.py`. Source provenance follows `r02-joins` and original HGSS wall01_d; north front/corner is an adaptation of its clean band.
