# Route 36 — approved transparent trees

Owner approved the complete rock/grass tiles on 2026-10-17 and requested only the
approved backgroundless tree rollout. Engine `e739facc2a`, draft PR12.

## Changes

- Retained all 409 existing tree origins (402 cliff-pass placements plus seven
  rear gate trees). No movement, cropping or replacement tree design.
- Used approved T01 and its reviewed removal mask to remove 25,852 pixels of old
  grass-shadow backing. Destination grass/path now shows through native index-zero
  transparency; restored pixels occupy the lower layer.
- Preserved every other rendered pixel, all 102 approved wall cells, gates,
  paths/stairs and decoded per-cell collision/elevation/behavior.
- Reused replaced-only metatile IDs and unreferenced secondary graphics slots in
  the dedicated Route 36 banks. No new palette bank, tile slot or metatile slot.

## Evidence

`review/native-full.png`: native decoded map, pixel-identical to actual Porymap.
`review/*-comparison.png`: before left, after right, nearest-neighbor enlargement.
`review/tile-review-*.png`: 115 distinct before/after pairs covering 1,242 changed
cells; coordinate groups and inspected findings in `evidence/tile-review.json`.
Reviewed tree roots/crowns, grass/path gaps and rear/foreground gate overlaps.
`review/gameplay.png`: actual background mGBA captures. Build, both stair flights,
barriers, connection and ordinary save/read/title Continue passed. See runtime
and structure evidence for hashes and exact checks. Desktop emulator not opened.

Reproduce from engine bc5612dd84 in a clean isolated checkout:

```
python tools/gba/maps/johto_common/r02_transparent_trees.py --engine ENGINE --install
python tools/gba/maps/johto_common/r02_tree_review.py gba/art/johto-common/trees/route36-installation
```

This installs Route 36 in the review checkout only. Other maps and production
merge are outside this pass; latest tree appearance awaits owner review.
