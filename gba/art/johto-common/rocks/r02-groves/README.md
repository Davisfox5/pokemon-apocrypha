# R02 aligned groves and complete northern wall

Owner rejected the previous individual tree shifts for creating compressed/overlapping crowns. They explicitly clarified that the **right-hand wall must continue to the northern map edge**.

- [HGSS versus full-height revision](review/north-to-south.png)
- [Previous versus corrected forest](review/comparison.png)
- [Full native route](review/native-full.png)
- [Background gameplay](review/gameplay.png)

## Layout

Rebuilt complete tree bands at two-cell horizontal pitch, using the unchanged approved T01 master. Removed conflicting extra placements instead of squeezing neighbors together. The changed 2x2 trunk footprints do not overlap. Crowns remain complete; no tree pixels cover either vertical rock face. Row placements are explicit in `source/tree-placements.json`. The bands follow the HGSS clearing/forest groups at native scale; they are not a claim of exact DS tree coordinates.

The right-hand wall now runs at x32 from y0 to y25, with the existing stair opening. Both installed stair sections remain exactly identical to the previously reviewed source, climbing east. **Traversal adaptation:** the continuous northern wall closes the old crossing near the northern clearing. The realigned west-side grove leaves a one-cell rim leading through tall grass to the existing eastern stairs. A headless walk verifies northern clearing → rim → grass → stairs → eastern clearing. No new warp or stair added.

## Evidence

Engine `768efc0592eb0d4761a2a8aaa13ad8ce177bf151` on draft PR12. Build, actual Porymap/native equality, both stair lanes/directions, wall barriers, northern route access and ordinary save/cold reload/title Continue pass. 408 cells /1632 quadrants and assembled native gameplay inspected. 20 collision cells adjusted for the wall and grove rim; behavior unchanged. No desktop emulator opened. Isolated review branch; owner visual approval pending.

Native bank remains at 1008 padded tile slots /488 metatiles. Reused 15 secondary tile slots proven unreferenced by all live map/border blocks, and unreferenced metatiles only. Dedicated tileset ownership verified; no live IDs repacked and no palette changes. Independent whole-map equality confirms unused-slot reclamation did not corrupt retained art. Untouched map pixels match exactly.

## Reproduce

`r02_groves.py --engine ENGINE --install` requires clean base `6f68aaf57b3c2f117c341d13ba485d9f9ed4e9aa`. `r02_groves_runtime.py` runs headless checks. `r02_review.py` generates coordinate sheets and `r02_publish.py` collects actual engine/Porymap evidence. No ROMs or saves are committed.
