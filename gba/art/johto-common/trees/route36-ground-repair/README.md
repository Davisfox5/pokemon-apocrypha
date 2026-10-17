# Route 36 — residual tree backing correction

Engine `5b80e625d1`; supersedes the incomplete ground cleanup in route36-installation.
The source removal mask omitted backing baked into adjacent composite tiles.
Rebuilt grass throughout the full tree bounds, removed dithered backing, and
removed orphan backing at the northeast map edge and former tree cell (52,24).
Gate shoulders retain reviewed destination transitions; their dark backing is
removed without repainting the architecture.

22,335 pixels corrected in 786 cells. All 409 tree origins, silhouettes and trunks
retained. All 102 approved wall tiles and every non-repair pixel are unchanged.
Decoded per-cell collision/elevation/behavior is identical. Full-map audit finds
zero pixels of the obsolete dark backing color (64,136,104).

Reviewed all 64 unique changed tile pairs at 4x, with coordinates mapped to every
changed cell in evidence/tile-review.json. Inspected full map, the reported grove,
map-edge remnants and gate overlap. Before/after comparison is left/right.
Native decoded render equals actual Porymap output. Build and background movement,
stair, barrier, save/read/Continue checks are recorded in evidence; no desktop game.
Visual acceptance remains with the owner. This is the isolated review checkout,
not a production merge.

Reproduce from clean engine e739facc2a:

```
python tools/gba/maps/johto_common/r02_tree_ground.py --engine ENGINE --install
python tools/gba/maps/johto_common/r02_tree_review.py gba/art/johto-common/trees/route36-ground-repair
```
