# Union Cave B2F — original HGSS reconstruction

Native source `de6922a964721aceb11147bcac6acadc477d4538`, branch
`codex/union-cave-1f`. [Shared cave review, checks and reproduction](../union-cave-1f/README.md).

- [Whole original / native map](evidence/comparison.png)
- [Actual native gameplay](evidence/gameplay-gallery.png)
- Original/native detail panels: [north](evidence/material-comparison-1.png),
  [middle](evidence/material-comparison-2.png), [south](evidence/material-comparison-3.png)
- [Numbered HGSS reference](evidence/numbered-hgss.png)
- [Native audit](evidence/audit.json), [packing](evidence/packing.json),
  [build identity](evidence/build.json)

Grid: 40×47, 16×16 native squares registered to the pictured HGSS scene.
Original reference, event records and registration are preserved under `source/`.
This is visual material interpretation plus the actual original warp topology,
not extracted DS collision. Native rock silhouettes, background/foreground layers,
base footprints and low shores remain separate editable data. Sprite/item pixels
are removed with local terrain repairs; campaign actors are not baked into art.

B2F's northwestern stair `(4,5)` returns to B1F's lower eastern bank `(29,46)`.
The lake, peninsulas, western gallery and separate southern lake follow the original
scene. Both northern low bank lips permit actual native Surf disembark; raised
plateau tops/faces remain rock barriers. Eight pixels of black void pad the original
744-pixel image to the native 752-pixel height. Original upper Alph transit rooms
outside this overview are not invented or rerouted here. Lapras/campaign actors
are not baked into the water image.

Porymap export matches native decoding with zero pixel differences. Layered
Porytiles RGB/alpha checks pass. Native stair travel, walking barriers, controlled
existing-engine Surf movement/disembark and ordinary save/cold reload/Continue are
verified. Campaign Surf activation/Strength rules and animated water are not
qualified by these map tests. No ROM/save/tool binaries are committed.
