# R02 eastward ascent and tree placement correction

Owner rejected the prior pass: preview/map stair mismatch, trees drawn on vertical rock, right landing misalignment, and wrong ascent direction.

- [HGSS / previous / corrected](review/comparison.png)
- [Exact installed stair identity](review/installed-stair-proof.png)
- [Background gameplay](review/gameplay.png)
- [Full native map](review/native-full.png)

Both crossings rise east. Both installed 16×128 wall/stair sections are byte-identical RGBA to the same reviewed source. The opposite-facing mirror is retained only as a reusable reference. The right dirt landing is one row north of its low approach. Five complete T01 trees were moved off the stone face; no cropped trees, no tree/vertical-face intersection. Existing forest collision remains blocked; one stair collision opens and three right-stair behaviors now use native diagonal ascent. No scripts, events or warps changed.

Engine `6f68aaf57b3c2f117c341d13ba485d9f9ed4e9aa`. Build, actual Porymap/native equality, both lanes climbing east and descending west, shoulders/walls, raised landing exit, grass movement, ordinary save/cold reload/title Continue pass. No desktop emulator opened. 121 cells /484 quadrants and gameplay inspected; owner visual approval remains pending. This is isolated draft PR12, not a production merge.

Capacity: 995 tiles, 488 primary metatiles. Reused 33 unreferenced historical metatile IDs only after verifying the tileset belongs solely to Route36 and excluding all live map/border references. No live ID repacking or palette changes. Only 13 tile slots remain; future additions need deliberate unused-tile reclamation, not silent palette/art degradation.

Source: approved T01; HGSS wall/stair projection from `r02-joins`. Existing irregular path outside the receiving landing retained. Native reproduction: `r02_elevation.py --engine ENGINE --install` from clean `492da86574614f83e1c9e99c3d5de9686029b8e5`; `r02_elevation_runtime.py` validates the corrected directional movement. The helper's optional orphan-ID reuse is restricted to the explicit verified list supplied by this pass.
