# Forest and receiving-surface authoring record

Immutable input: native `116ea8011c958d10bf5d61daf2d879cca9e8a184`. Result: `8eb23f6774fd937f3018d413f1fab5b6dc8d05c8`. Do not replay an original map generator or this guarded authoring script over later owner changes.

`refine_forest.py` narrowly updates current native planes. `tree-rows.json` records each observed/inferred row and perimeter addition. `masters/olivine-tree.png` is an unscaled explicit silhouette from the [original HGSS overview](../hgss-reference.png), not a resized shared tree; `tree-provenance.json` records its donor and native palette. The local house master uses the existing residence palette with unchanged geometry.

`forest_understory.py` reconstructs complete receiving surfaces between visible reference anchors. `understory-reconstruction.json` records every affected course, shelf and donor. `receiving-surfaces.png` retains the finished ground before invisible-pixel packing; `rock-layer.png` and `wall-mask.png` retain stone independently of trees. `forest_textures.py` reuses same-facing glyphs with a source-tone and edge-join objective; no averaging or silhouette simplification. `texture-joins.json` records the measured changes.

`compile_planes.py` stages both City/Quay banks before mutating native source. `terrain_palettes.py` performs exact bank covering. Actual decoded pixels, Porymap, cell/collision checks, row/complete-root checks, gameplay and ordinary save/Continue are in [the review](../../evidence/forest-refinement/README.md). These authoring files do not establish owner visual acceptance.
